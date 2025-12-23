from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import exp
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .engine_model import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig
    from .injection import VP37CamProfile


R_AIR_J_PER_KG_K = 287.0
R_UNIVERSAL_J_PER_MOL_K = 8.314462618


@dataclass(frozen=True)
class GasModel:
    r_j_per_kg_k: float = R_AIR_J_PER_KG_K

    def gamma(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["gamma"]
        g = cfg.gamma_t0 - cfg.gamma_slope_per_k * temperature_k
        return max(cfg.gamma_min, min(cfg.gamma_max, g))

    def cp(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["cp"]
        g = self.gamma(temperature_k, cfg, pressure_pa=pressure_pa)
        return g * self.r_j_per_kg_k / max(1e-9, (g - 1.0))

    def cv(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["cv"]
        cp = self.cp(temperature_k, cfg, pressure_pa=pressure_pa)
        return max(1e-9, cp - self.r_j_per_kg_k)

    def density_from_pT(self, pressure_pa: float, temperature_k: float, cfg: SimulationConfig) -> float:
        p = float(max(1.0, pressure_pa))
        t = float(max(1.0, temperature_k))
        backend = cfg.thermo_backend

        if backend == "coolprop":
            cp_mod = _coolprop_module()
            if cp_mod is not None:
                try:
                    return float(cp_mod.PropsSI("Dmass", "T", t, "P", p, cfg.coolprop_fluid))
                except Exception:
                    if cfg.strict_backends:
                        raise RuntimeError("CoolProp backend failed to compute density.")

        return p / (max(1e-9, self.r_j_per_kg_k) * t)

    def pressure_from_rhoT(self, density_kg_per_m3: float, temperature_k: float, cfg: SimulationConfig) -> float:
        rho = float(max(1e-9, density_kg_per_m3))
        t = float(max(1.0, temperature_k))
        backend = cfg.thermo_backend

        if backend == "coolprop":
            cp_mod = _coolprop_module()
            if cp_mod is not None:
                try:
                    return float(cp_mod.PropsSI("P", "T", t, "Dmass", rho, cfg.coolprop_fluid))
                except Exception:
                    if cfg.strict_backends:
                        raise RuntimeError("CoolProp backend failed to compute pressure.")

        return rho * max(1e-9, self.r_j_per_kg_k) * t

    def temperature_from_prho(self, pressure_pa: float, density_kg_per_m3: float, cfg: SimulationConfig) -> float:
        p = float(max(1.0, pressure_pa))
        rho = float(max(1e-9, density_kg_per_m3))
        backend = cfg.thermo_backend

        if backend == "coolprop":
            cp_mod = _coolprop_module()
            if cp_mod is not None:
                try:
                    return float(cp_mod.PropsSI("T", "P", p, "Dmass", rho, cfg.coolprop_fluid))
                except Exception:
                    if cfg.strict_backends:
                        raise RuntimeError("CoolProp backend failed to compute temperature.")

        return p / (max(1e-9, self.r_j_per_kg_k) * rho)


@lru_cache(maxsize=2)
def _coolprop_module() -> Any | None:
    try:
        import CoolProp.CoolProp as cp  # type: ignore

        return cp
    except Exception:
        return None


def _real_gas_props(temperature_k: float, pressure_pa: float | None, cfg: SimulationConfig) -> dict[str, float] | None:
    p = float(pressure_pa) if pressure_pa is not None else 1.0e5
    t = float(max(1.0, temperature_k))
    backend = cfg.thermo_backend

    if backend == "coolprop":
        cp_mod = _coolprop_module()
        if cp_mod is None:
            if cfg.strict_backends:
                raise RuntimeError("CoolProp backend requested but module is not available.")
            return None
        try:
            cp = float(cp_mod.PropsSI("Cpmass", "T", t, "P", p, cfg.coolprop_fluid))
            cv = float(cp_mod.PropsSI("Cvmass", "T", t, "P", p, cfg.coolprop_fluid))
            if cp <= 0.0 or cv <= 0.0:
                return None
            gamma = cp / cv
            return {"cp": cp, "cv": cv, "gamma": gamma}
        except Exception:
            if cfg.strict_backends:
                raise RuntimeError("CoolProp backend failed to compute properties.")
            return None

    return None


def ignition_delay_seconds_arrhenius(p_pa: float, t_k: float, *, a: float, n: float, ea_j_per_mol: float) -> float:
    """Simple Arrhenius-like model from spec (tunable; not a calibrated correlation).

    Uses p in bar to avoid microscopic A values.
    """
    p_bar = max(1e-6, p_pa / 1.0e5)
    return a * (p_bar ** (-n)) * exp(ea_j_per_mol / (R_UNIVERSAL_J_PER_MOL_K * max(1.0, t_k)))


def omega_rad_per_s(rpm: float) -> float:
    return rpm * 2.0 * 3.141592653589793 / 60.0


from math import sqrt
from typing import Any



def orifice_mdot_kg_per_s(
    *,
    p1_pa: float | None = None,
    t1_k: float | None = None, # Assuming t1_k is the temperature associated with p1_pa and it's always the temperature of the gas flowing through the orifice
    p2_pa: float | None = None,
    p_up_pa: float | None = None,
    t_up_k: float | None = None,
    p_down_pa: float | None = None,
    gamma: float,
    r_j_per_kg_k: float,
    area_m2: float,
    discharge_coeff: float,
    backend: str = "simple",
    strict: bool = True,
) -> float:
    """Quasi-steady compressible orifice flow (ideal gas).

    Returns signed mass flow rate. Positive if flow is from 1 -> 2, negative if from 2 -> 1.
    """
    if p1_pa is None or p2_pa is None or t1_k is None:
        if p_up_pa is None or p_down_pa is None or t_up_k is None:
            raise TypeError("Provide p1_pa/t1_k/p2_pa or p_up_pa/t_up_k/p_down_pa.")
        p1_pa = float(p_up_pa)
        p2_pa = float(p_down_pa)
        t1_k = float(t_up_k)
    if area_m2 <= 0.0 or discharge_coeff <= 0.0:
        return 0.0

    # Determine actual upstream and downstream based on pressures
    if p1_pa >= p2_pa:
        p_up, t_up, p_down, flow_direction = p1_pa, t1_k, p2_pa, 1.0
    else:
        p_up, t_up, p_down, flow_direction = p2_pa, t1_k, p1_pa, -1.0

    p_up = max(1.0, p_up)
    p_down = max(1.0, p_down)
    t_up = max(1.0, t_up)
    g = max(1.01, gamma)
    r = max(1e-9, r_j_per_kg_k)

    pr = p_down / p_up
    pr_crit = (2.0 / (g + 1.0)) ** (g / (g - 1.0))

    a_eff = discharge_coeff * area_m2

    if backend == "fluids":
        mdot_unsigned = _fluids_orifice_mdot(
            p_up_pa=p_up,
            p_down_pa=p_down,
            t_up_k=t_up,
            gamma=g,
            r_j_per_kg_k=r,
            area_m2=a_eff,
            strict=strict,
        )
        if mdot_unsigned is not None:
            return flow_direction * mdot_unsigned
        # Fall back to the simple model if fluids couldn't compute.

    if pr <= pr_crit:
        # Choked
        term = (2.0 / (g + 1.0)) ** ((g + 1.0) / (2.0 * (g - 1.0)))
        mdot_unsigned = a_eff * p_up * sqrt(g / (r * t_up)) * term
    else:
        # Subsonic
        term = (2.0 * g / (r * t_up * (g - 1.0))) * (pr ** (2.0 / g) - pr ** ((g + 1.0) / g))
        if term <= 0.0:
            mdot_unsigned = 0.0
        else:
            mdot_unsigned = a_eff * p_up * sqrt(term)
    
    return flow_direction * mdot_unsigned


def _fluids_orifice_mdot(
    *,
    p_up_pa: float,
    p_down_pa: float,
    t_up_k: float,
    gamma: float,
    r_j_per_kg_k: float,
    area_m2: float,
    strict: bool,
) -> float | None:
    try:
        import inspect

        import fluids.compressible as comp  # type: ignore
    except Exception:
        if strict:
            raise RuntimeError("fluids backend requested but module is not available.")
        return None

    mw = R_UNIVERSAL_J_PER_MOL_K / max(1e-9, r_j_per_kg_k)  # kg/mol
    params = {
        "P0": p_up_pa,
        "P1": p_up_pa,
        "P2": p_down_pa,
        "P": p_down_pa,
        "T0": t_up_k,
        "T1": t_up_k,
        "A": area_m2,
        "A_t": area_m2,
        "k": gamma,
        "gamma": gamma,
        "MW": mw,
        "molar_mass": mw,
    }

    candidates = [
        "isentropic_mass_flow",
        "isentropic_mass_flow_rate",
        "mass_flow_rate_isentropic",
        "critical_flow",
    ]
    for name in candidates:
        fn: Any | None = getattr(comp, name, None)
        if fn is None:
            continue
        try:
            sig = inspect.signature(fn)
            call_kwargs = {k: v for k, v in params.items() if k in sig.parameters}
            if not call_kwargs:
                continue
            mdot = fn(**call_kwargs)
            if mdot is None:
                continue
            return float(mdot)
        except Exception:
            continue
    return None


from dataclasses import dataclass
from math import cos, pi, sin, sqrt



@dataclass(frozen=True)
class GeometryResult:
    theta_rad: float
    s_m: float
    ds_dtheta_m_per_rad: float
    volume_m3: float
    dvol_dtheta_m3_per_rad: float
    # Exposed surface areas for heat transfer
    area_head_m2: float
    area_piston_m2: float
    area_liner_m2: float

    @property
    def heat_transfer_area_m2(self) -> float:
        return self.area_head_m2 + self.area_piston_m2 + self.area_liner_m2


def piston_position_s_m(geom: EngineGeometry, theta_rad: float) -> float:
    # Spec implementation: s = r cosθ + sqrt(L^2 - (r sinθ - δ)^2)
    r = geom.crank_radius_m
    L = geom.rod_length_m
    delta = geom.offset_m
    u = r * sin(theta_rad) - delta
    return r * cos(theta_rad) + sqrt(max(0.0, L * L - u * u))


def piston_position_derivative_ds_dtheta(geom: EngineGeometry, theta_rad: float) -> float:
    r = geom.crank_radius_m
    L = geom.rod_length_m
    delta = geom.offset_m
    u = r * sin(theta_rad) - delta
    denom = sqrt(max(1e-30, L * L - u * u))
    # ds/dθ = -r sinθ - (u * r cosθ)/sqrt(L^2 - u^2)
    return -r * sin(theta_rad) - (u * r * cos(theta_rad)) / denom


def cylinder_volume_m3(geom: EngineGeometry, theta_rad: float) -> tuple[float, float, float]:
    """Returns (V, dV/dtheta, x_from_tdc).

    x_from_tdc is the current piston travel from TDC (0 at TDC, ~stroke at BDC).
    """
    s = piston_position_s_m(geom, theta_rad)
    ds_dtheta = piston_position_derivative_ds_dtheta(geom, theta_rad)
    s_tdc = piston_position_s_m(geom, 0.0)
    x_from_tdc = s_tdc - s
    area = geom.piston_area_m2
    V_c = geom.clearance_volume_m3_per_cyl
    V = V_c + area * x_from_tdc
    dV_dtheta = -area * ds_dtheta
    return V, dV_dtheta, x_from_tdc


def get_surface_areas(geom: EngineGeometry, x_from_tdc_m: float) -> tuple[float, float, float]:
    """Returns heat transfer surface areas for head, piston, and liner."""
    exposed_liner_height = max(0.0, min(geom.stroke_m, x_from_tdc_m))
    area_piston = geom.piston_area_m2
    area_head = area_piston  # Assume flat head
    area_liner = pi * geom.bore_m * exposed_liner_height
    return area_head, area_piston, area_liner


def geometry_at_theta(geom: EngineGeometry, theta_rad: float) -> GeometryResult:
    s = piston_position_s_m(geom, theta_rad)
    ds_dtheta = piston_position_derivative_ds_dtheta(geom, theta_rad)
    V, dV_dtheta, x_from_tdc = cylinder_volume_m3(geom, theta_rad)
    a_head, a_piston, a_liner = get_surface_areas(geom, x_from_tdc)
    return GeometryResult(
        theta_rad=theta_rad,
        s_m=s,
        ds_dtheta_m_per_rad=ds_dtheta,
        volume_m3=V,
        dvol_dtheta_m3_per_rad=dV_dtheta,
        area_head_m2=a_head,
        area_piston_m2=a_piston,
        area_liner_m2=a_liner,
    )


from math import pow

from .engine_model import HeatTransferConfig


def h_woschni_simplified_w_per_m2_k(
    *,
    bore_m: float,
    pressure_pa: float,
    temperature_k: float,
    mean_piston_speed_m_per_s: float,
    cfg: HeatTransferConfig,
) -> float:
    """
    Calculates the gas-side heat transfer coefficient using a simplified
    Woschni correlation.
    """
    # h = c * B^-0.2 * p_bar^0.8 * T^-0.55 * w^0.8
    p_bar = max(1e-6, pressure_pa / 1.0e5)
    w = max(0.1, cfg.w_mult * mean_piston_speed_m_per_s)
    return (
        cfg.woschni_c
        * pow(max(1e-6, bore_m), -0.2)
        * pow(p_bar, 0.8)
        * pow(max(1.0, temperature_k), -0.55)
        * pow(w, 0.8)
    )


def calculate_wall_heat_loss_j_per_rad(
    *,
    h_coeff: float,
    gas_temp_k: float,
    area_head_m2: float,
    area_piston_m2: float,
    area_liner_m2: float,
    cfg: HeatTransferConfig,
    omega_rad_per_s: float,
) -> float:
    """
    Calculates the total heat loss to the walls from all surfaces in J/rad
    for a multi-zone wall temperature model.
    """
    q_dot_head = h_coeff * area_head_m2 * (gas_temp_k - cfg.head_temp_k)
    q_dot_piston = h_coeff * area_piston_m2 * (gas_temp_k - cfg.piston_temp_k)
    q_dot_liner = h_coeff * area_liner_m2 * (gas_temp_k - cfg.liner_temp_k)

    q_dot_total_w = q_dot_head + q_dot_piston + q_dot_liner
    
    # Convert from J/s (Watts) to J/rad
    return q_dot_total_w / max(1e-9, omega_rad_per_s)



from dataclasses import dataclass
from math import pi, sin


@dataclass(frozen=True)
class ValveTiming:
    # Angles in degrees, referenced to 0 = TDC combustion.
    # Full 4-stroke cycle spans [-360, 360] deg.
    ivo_deg: float = -350.0
    ivc_deg: float = -150.0
    evo_deg: float = 140.0
    evc_deg: float = 350.0


@dataclass(frozen=True)
class ValveFlow:
    intake_valve_diameter_m: float = 35.95e-3
    exhaust_valve_diameter_m: float = 31.45e-3
    intake_max_lift_m: float = 8.5e-3
    exhaust_max_lift_m: float = 8.5e-3
    cd_intake: float = 0.70
    cd_exhaust: float = 0.72


def _cycle_angle_0_720(theta_deg: float) -> float:
    return (theta_deg + 360.0) % 720.0


def valve_lift_fraction(theta_deg: float, open_deg: float, close_deg: float) -> float:
    """Smooth normalized lift (0..1) between open and close over a 720° cycle.

    Uses a symmetric sin(pi * phi) profile where phi in [0,1].
    """
    t = _cycle_angle_0_720(theta_deg)
    o = _cycle_angle_0_720(open_deg)
    c = _cycle_angle_0_720(close_deg)

    duration = (c - o) % 720.0
    if duration <= 0.0:
        return 0.0
    inside = ((t - o) % 720.0) <= duration
    if not inside:
        return 0.0
    phi = ((t - o) % 720.0) / duration
    if phi <= 0.0 or phi >= 1.0:
        return 0.0
    return float(sin(pi * phi))


def effective_curtain_area_m2(valve_diameter_m: float, lift_m: float) -> float:
    # Curtain area ~ circumference * lift, capped by port area.
    curtain = pi * valve_diameter_m * max(0.0, lift_m)
    port = pi * (valve_diameter_m**2) / 4.0
    return min(curtain, port)


from dataclasses import dataclass
from math import pi, sqrt


@dataclass(frozen=True)
class NozzleConfig:
    diameter_mm: float = 0.184
    holes: int = 5
    discharge_coeff: float = 0.72
    pilot_open_bar: float = 190.0
    main_open_bar: float = 300.0
    pilot_area_frac: float = 0.30

    @property
    def area_m2(self) -> float:
        d = self.diameter_mm * 1e-3
        return (pi * (d**2) / 4.0) * self.holes


@dataclass(frozen=True)
class NeedleConfig:
    """Properties of the injector needle for dynamic simulation."""
    mass_kg: float = 0.005  # 5 grams
    seat_area_mm2: float = 0.5
    spring_k_n_per_m: float = 50000.0  # 50 N/mm
    damping_coeff_ns_per_m: float = 10.0
    max_lift_mm: float = 0.3

    @property
    def seat_area_m2(self) -> float:
        return self.seat_area_mm2 * 1e-6
    
    @property
    def max_lift_m(self) -> float:
        return self.max_lift_mm * 1e-3


@dataclass(frozen=True)
class VP37HydraulicConfig:
    plunger_diameter_mm: float = 10.0
    chamber_volume_mm3: float = 200.0
    line_volume_mm3: float = 400.0
    back_pressure_bar: float = 50.0

    @property
    def plunger_area_m2(self) -> float:
        d = self.plunger_diameter_mm * 1e-3
        return pi * (d**2) / 4.0

    @property
    def volume_eff_m3(self) -> float:
        return (self.chamber_volume_mm3 + self.line_volume_mm3) * 1e-9


def estimate_pilot_ratio(
    cam: VP37CamProfile,
    *,
    rpm: float,
    duration_main_deg: float,
    fuel: Fuel,
    nozzle: NozzleConfig,
    hyd: VP37HydraulicConfig,
    cylinder: int = 1,
) -> float:
    """Estimate pilot mass fraction from pressure trace in a simplified VP37 line model."""
    if duration_main_deg <= 0.0:
        return 0.0

    a_deg, s_mm = cam._rising_segment(cam._lobe_index_for_cylinder(cylinder))
    if a_deg.size < 2:
        return 0.0

    dur_pump_deg = max(0.0, duration_main_deg / 2.0)
    a_start = float(a_deg[0])
    a_end = min(float(a_deg[-1]), a_start + dur_pump_deg)
    if a_end <= a_start:
        return 0.0

    # Slice to injection window
    mask = (a_deg >= a_start) & (a_deg <= a_end)
    a_deg = a_deg[mask]
    s_mm = s_mm[mask]
    if a_deg.size < 2:
        return 0.0

    omega_pump = (rpm / 2.0) * 2.0 * pi / 60.0  # pump rad/s
    rho = max(1e-6, fuel.density_kg_per_m3)
    k = max(1e5, fuel.bulk_modulus_pa)
    v_eff = max(1e-12, hyd.volume_eff_m3)
    a_plunger = hyd.plunger_area_m2
    p_back = hyd.back_pressure_bar * 1e5
    p_open_pilot = p_back + nozzle.pilot_open_bar * 1e5
    p_open_main = p_back + nozzle.main_open_bar * 1e5

    p = p_back
    pilot_m = 0.0
    total_m = 0.0
    a_noz = nozzle.area_m2
    cd = nozzle.discharge_coeff

    for i in range(1, len(a_deg)):
        d_deg = float(a_deg[i] - a_deg[i - 1])
        if d_deg <= 0:
            continue
        dt = (d_deg * pi / 180.0) / max(1e-9, omega_pump)
        ds = (s_mm[i] - s_mm[i - 1]) * 1e-3
        v_plunger = ds / max(1e-12, dt)
        q_plunger = a_plunger * v_plunger

        m_dot = 0.0
        if p >= p_open_pilot:
            area_eff = a_noz * cd
            if p < p_open_main:
                area_eff *= max(1e-3, nozzle.pilot_area_frac)
            dp = max(0.0, p - p_back)
            m_dot = area_eff * sqrt(2.0 * rho * dp)
        q_out = m_dot / rho if m_dot > 0.0 else 0.0

        dp_dt = (k / v_eff) * (q_plunger - q_out)
        p = max(p_back, p + dp_dt * dt)

        if m_dot > 0.0:
            dm = m_dot * dt
            total_m += dm
            if p < p_open_main:
                pilot_m += dm

    if total_m <= 0.0:
        return 0.0
    return max(0.0, min(1.0, pilot_m / total_m))


from dataclasses import dataclass
from math import exp

import numpy as np



DEG2RAD = 3.141592653589793 / 180.0


@dataclass(frozen=True)
class CombustionScheduleRuntime:
    # Computed SOC (start of combustion) in radians once ignition delay is known.
    pilot_soc_rad: float | None = None
    main_soc_rad: float | None = None


def wiebe_dxb_dtheta(theta_rad: float, *, start_rad: float, duration_rad: float, a: float, m: float) -> float:
    if duration_rad <= 0:
        return 0.0
    y = (theta_rad - start_rad) / duration_rad
    if y <= 0.0 or y >= 1.0:
        return 0.0
    return (a * (m + 1.0) / duration_rad) * (y**m) * exp(-a * (y ** (m + 1.0)))


def heat_release_rate_wiebe_single(
    theta_rad: float,
    *,
    q_j: float,
    start_rad: float | None,
    duration_rad: float,
    a: float,
    m: float,
) -> float:
    if start_rad is None:
        return 0.0
    return q_j * wiebe_dxb_dtheta(theta_rad, start_rad=start_rad, duration_rad=duration_rad, a=a, m=m)


def mass_rate_shaped(
    theta_rad: float,
    *,
    start_rad: float | None,
    duration_rad: float,
    m_total_kg: float,
    u: np.ndarray,
    w: np.ndarray,
) -> float:
    """Shaped mass rate dm/dθ in kg/rad.

    u: 0..1, w: normalized such that ∫_0^1 w(u) du = 1.
    """
    if start_rad is None or duration_rad <= 0.0 or m_total_kg <= 0.0:
        return 0.0
    x = (theta_rad - start_rad) / duration_rad
    if x <= 0.0 or x >= 1.0:
        return 0.0
    wu = float(np.interp(float(x), u, w))
    return (m_total_kg / duration_rad) * wu


def heat_release_rate_from_shaped_fuel(
    theta_rad: float,
    *,
    start_rad: float | None,
    duration_rad: float,
    q_total_j: float,
    u: np.ndarray,
    w: np.ndarray,
) -> float:
    if start_rad is None or duration_rad <= 0.0 or q_total_j <= 0.0:
        return 0.0
    x = (theta_rad - start_rad) / duration_rad
    if x <= 0.0 or x >= 1.0:
        return 0.0
    wu = float(np.interp(float(x), u, w))
    return (q_total_j / duration_rad) * wu


def heat_release_rate_dq_dtheta(
    theta_rad: float,
    *,
    fuel: Fuel,
    q_total_j: float,
    schedule: InjectionSchedule,
    cfg: CombustionConfig,
    runtime: CombustionScheduleRuntime,
    injection_profile: tuple[np.ndarray, np.ndarray] | None = None,
) -> float:
    """
    Calculates the heat release rate dQ/d(theta) in J/rad based on the configured model.
    """
    if cfg.hrr_model == "hydraulic_profile":
        if injection_profile is None or runtime.main_soc_rad is None:
            return 0.0
        
        profile_theta_rad, profile_dmdtheta_kg_rad = injection_profile
        if profile_theta_rad.size == 0:
            return 0.0

        # Calculate ignition delay as a constant shift
        delay_rad = runtime.main_soc_rad - (schedule.soi_main_deg * DEG2RAD)

        # Look up the past injection rate that is now combusting
        source_theta = theta_rad - delay_rad
        
        dm_fuel_dtheta = float(np.interp(source_theta, profile_theta_rad, profile_dmdtheta_kg_rad, left=0.0, right=0.0))
        
        # dQ/d(theta) = dm_fuel/d(theta) * LHV
        return dm_fuel_dtheta * fuel.lhv_j_per_kg

    # Fallback to Wiebe models
    a = cfg.wiebe_a
    q_p = q_total_j * max(0.0, min(1.0, schedule.pilot_fraction))
    q_m = q_total_j - q_p

    dq = 0.0
    if runtime.pilot_soc_rad is not None:
        dq += q_p * wiebe_dxb_dtheta(
            theta_rad,
            start_rad=runtime.pilot_soc_rad,
            duration_rad=schedule.duration_pilot_deg * DEG2RAD,
            a=a,
            m=schedule.wiebe_m_pilot,
        )
    if runtime.main_soc_rad is not None:
        dq += q_m * wiebe_dxb_dtheta(
            theta_rad,
            start_rad=runtime.main_soc_rad,
            duration_rad=schedule.duration_main_deg * DEG2RAD,
            a=a,
            m=schedule.wiebe_m_main,
        )
    return dq
...


def maybe_arm_combustion(
    theta_deg: float,
    *,
    pressure_pa: float,
    temperature_k: float,
    fuel: Fuel,
    schedule: InjectionSchedule,
    sim_cfg: SimulationConfig,
    runtime: CombustionScheduleRuntime,
    air_mass_kg: float | None = None,
) -> CombustionScheduleRuntime:
    # Arm pilot/main SOC exactly once, when we pass SOI.
    def compute_soc(soi_deg: float) -> float:
        if sim_cfg.combustion.ignition_delay_model == "fixed_deg":
            delay_deg = sim_cfg.combustion.fixed_ignition_delay_deg
        else:
            tau_s = ignition_delay_seconds_arrhenius(
                pressure_pa,
                temperature_k,
                a=fuel.id_a,
                n=fuel.id_n,
                ea_j_per_mol=fuel.id_ea_j_per_mol,
            )
            delay_rad = tau_s * omega_rad_per_s(sim_cfg.rpm)
            delay_deg = delay_rad / DEG2RAD
        return (soi_deg + delay_deg) * DEG2RAD

    pilot_soc = runtime.pilot_soc_rad
    if pilot_soc is None and theta_deg >= schedule.soi_pilot_deg:
        pilot_soc = compute_soc(schedule.soi_pilot_deg)

    main_soc = runtime.main_soc_rad
    if main_soc is None and theta_deg >= schedule.soi_main_deg:
        main_soc = compute_soc(schedule.soi_main_deg)

    return CombustionScheduleRuntime(pilot_soc_rad=pilot_soc, main_soc_rad=main_soc)
