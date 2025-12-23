from __future__ import annotations

import numpy as np
from scipy.interpolate import LinearNDInterpolator

from dataclasses import dataclass, replace
from math import pi
from typing import Literal, Optional, Any


@dataclass(frozen=True)
class EngineGeometry:
    bore_m: float
    stroke_m: float
    rod_length_m: float
    crank_radius_m: float
    offset_m: float
    cylinders: int = 4
    bowl_volume_m3: float = 0.0  # Volume of the bowl in the piston
    gasket_thickness_m: float = 0.0  # Thickness of the head gasket
    piston_protrusion_m: float = 0.0  # Piston protrusion above deck at TDC
    head_recess_m3: float = 0.0  # Volume of valve recesses/squish in the head
    compression_ratio: float | None = None

    @property
    def piston_area_m2(self) -> float:
        return pi * (self.bore_m ** 2) / 4.0

    @property
    def swept_volume_m3_per_cyl(self) -> float:
        return self.piston_area_m2 * self.stroke_m

    @property
    def clearance_volume_m3_per_cyl(self) -> float:
        clearance_m = max(0.0, self.gasket_thickness_m - self.piston_protrusion_m)
        vc_geom = self.bowl_volume_m3 + self.head_recess_m3 + self.piston_area_m2 * clearance_m
        if vc_geom <= 0.0 and self.compression_ratio is not None and self.compression_ratio > 1.0:
            return self.swept_volume_m3_per_cyl / (self.compression_ratio - 1.0)
        return vc_geom


@dataclass(frozen=True)
class FrictionModel:
    """Parameters for the Chen-Flynn friction model."""
    a_pa: float = 80000.0  # Constant friction coefficient (Pa)
    b_pa_per_mpa: float = 0.05  # Coefficient for P_max (Pa/MPa)
    c_pa_per_rpm: float = 0.005  # Coefficient for RPM (Pa/RPM)


@dataclass(frozen=True)
class CompressorMap:
    """Interpolated compressor map data."""
    efficiency_interp: Any # LinearNDInterpolator
    turbo_rpm_interp: Any # LinearNDInterpolator

    @classmethod
    def from_csv(cls, file_path: str) -> "CompressorMap":
        # Load CSV, prepare data for interpolation
        # Assume CSV has columns: 'mass_flow_corrected', 'pressure_ratio', 'efficiency', 'turbo_rpm_corrected'
        data = np.loadtxt(file_path, delimiter=',', skiprows=1) # Assuming header row
        points = data[:, :2] # mass_flow_corrected, pressure_ratio
        efficiency_values = data[:, 2]
        turbo_rpm_values = data[:, 3]

        efficiency_interp = LinearNDInterpolator(points, efficiency_values)
        turbo_rpm_interp = LinearNDInterpolator(points, turbo_rpm_values)

        return cls(efficiency_interp=efficiency_interp, turbo_rpm_interp=turbo_rpm_interp)

    def get_efficiency(self, mass_flow: float, pressure_ratio: float) -> float:
        return float(self.efficiency_interp((mass_flow, pressure_ratio)))

    def get_turbo_rpm(self, mass_flow: float, pressure_ratio: float) -> float:
        return float(self.turbo_rpm_interp((mass_flow, pressure_ratio)))


from scipy.interpolate import interp1d

@dataclass(frozen=True)
class VntMap:
    """Interpolated VNT effective area map data."""
    effective_area_interp: Any # interp1d

    @classmethod
    def from_csv(cls, file_path: str) -> "VntMap":
        # Load CSV, prepare data for interpolation
        # Assume CSV has columns: 'vnt_angle_deg', 'effective_area_m2'
        data = np.loadtxt(file_path, delimiter=',', skiprows=1) # Assuming header row
        vnt_angles = data[:, 0]
        effective_areas = data[:, 1]

        effective_area_interp = interp1d(vnt_angles, effective_areas, kind='linear', fill_value="extrapolate")

        return cls(effective_area_interp=effective_area_interp)

    def get_effective_area(self, vnt_angle_deg: float) -> float:
        return float(self.effective_area_interp(vnt_angle_deg))


@dataclass(frozen=True)
class ManifoldConfig:
    """Static properties of a manifold."""

    volume_m3: float
    # Initial state guesses
    initial_temp_k: float = 300.0
    initial_pressure_pa: float = 1.0e5


@dataclass(frozen=True)
class IntercoolerConfig:
    """Static properties of an intercooler."""
    mass_al_kg: float = 1.5 # Mass of the intercooler core (aluminium)
    cp_al_j_per_kg_k: float = 900.0 # Specific heat capacity of aluminium
    area_ext_m2: float = 0.5 # External surface area for ambient heat transfer
    h_ambient_w_per_m2_k_base: float = 10.0 # Base convective heat transfer coefficient to ambient (for 0 vehicle speed)
    h_ambient_w_per_m2_k_factor_v: float = 2.0 # Factor for vehicle speed influence on h_ambient
    h_ic_air_w_per_m2_k: float = 100.0 # Heat transfer coefficient between air and intercooler core
    area_ic_air_m2: float = 0.2 # Effective heat transfer area between air and intercooler core


@dataclass(frozen=True)
class N146ActuatorConfig:
    """Parameters for the N146 dosing plunger actuator model."""
    plunger_mass_kg: float = 0.005
    spring_constant_n_per_m: float = 500.0
    damping_coefficient_ns_per_m: float = 0.05
    force_coefficient_n_per_v: float = 0.1 # N/V
    max_travel_m: float = 2.0e-3 # 2.0 mm
    initial_voltage_v: float = 5.0


@dataclass
class ManifoldState:
    """Dynamic state of a manifold as a 0D control volume."""

    mass_kg: float
    temperature_k: float
    exhaust_gas_fraction: float = 0.0 # From 0.0 (fresh air) to 1.0 (pure exhaust)

    @classmethod
    def from_config(cls, cfg: ManifoldConfig) -> "ManifoldState":
        from .physics import R_AIR_J_PER_KG_K

        # Initial mass from ideal gas law
        rho = cfg.initial_pressure_pa / (max(1e-9, R_AIR_J_PER_KG_K) * max(1.0, cfg.initial_temp_k))
        mass = rho * cfg.volume_m3
        return cls(mass_kg=mass, temperature_k=cfg.initial_temp_k, exhaust_gas_fraction=0.0)


@dataclass(frozen=True)
class Fuel:
    name: str
    lhv_j_per_kg: float
    cetane_number: float
    density_kg_per_m3: float
    bulk_modulus_pa: float
    stoich_air_fuel: float

    # Arrhenius-like ignition delay parameters (tunable; units described in docs).
    id_a: float = 5.0e-6
    id_n: float = 1.0
    id_ea_j_per_mol: float = 6.2e4

    @staticmethod
    def diesel() -> "Fuel":
        return Fuel(
            name="Diesel",
            lhv_j_per_kg=42.5e6,
            cetane_number=51.0,
            density_kg_per_m3=830.0,
            bulk_modulus_pa=1.6e9,
            stoich_air_fuel=14.5,
            id_a=5.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=5.8e4,
        )

    @staticmethod
    def svo_rapeseed() -> "Fuel":
        return Fuel(
            name="SVO (rapeseed)",
            lhv_j_per_kg=37.0e6,
            cetane_number=45.0,
            density_kg_per_m3=920.0,
            bulk_modulus_pa=1.95e9,
            stoich_air_fuel=13.8,
            id_a=7.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=6.2e4,
        )

    @staticmethod
    def methanol() -> "Fuel":
        return Fuel(
            name="Methanol",
            lhv_j_per_kg=20.0e6,
            cetane_number=5.0,
            density_kg_per_m3=790.0,
            bulk_modulus_pa=1.2e9,
            stoich_air_fuel=6.45,
            id_a=2.0e-5,
            id_n=1.0,
            id_ea_j_per_mol=6.5e4,
        )

    @staticmethod
    def biodiesel_b100_fame() -> "Fuel":
        return Fuel(
            name="Biodiesel (B100/FAME)",
            lhv_j_per_kg=38.0e6,
            cetane_number=50.0,
            density_kg_per_m3=880.0,
            bulk_modulus_pa=1.75e9,
            stoich_air_fuel=12.6,
            id_a=7.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=6.0e4,
        )

    @staticmethod
    def margarine_melted() -> "Fuel":
        return Fuel(
            name="Margarine (melted)",
            lhv_j_per_kg=39.5e6,
            cetane_number=45.0,
            density_kg_per_m3=915.0,
            bulk_modulus_pa=1.85e9,
            stoich_air_fuel=13.8,
            id_a=7.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=6.2e4,
        )

    @staticmethod
    def lard_liquid() -> "Fuel":
        return Fuel(
            name="Lard (liquid)",
            lhv_j_per_kg=39.8e6,
            cetane_number=45.0,
            density_kg_per_m3=890.0,
            bulk_modulus_pa=1.70e9,
            stoich_air_fuel=13.8,
            id_a=7.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=6.2e4,
        )

    @staticmethod
    def wvo_used_frying_oil() -> "Fuel":
        return Fuel(
            name="WVO (used frying oil)",
            lhv_j_per_kg=36.5e6,
            cetane_number=40.0,
            density_kg_per_m3=930.0,
            bulk_modulus_pa=1.95e9,
            stoich_air_fuel=13.8,
            id_a=8.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=6.4e4,
        )

    @staticmethod
    def heating_oil() -> "Fuel":
        return Fuel(
            name="Heating oil",
            lhv_j_per_kg=42.5e6,
            cetane_number=48.0,
            density_kg_per_m3=850.0,
            bulk_modulus_pa=1.60e9,
            stoich_air_fuel=14.5,
            id_a=5.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=5.9e4,
        )

    @staticmethod
    def used_engine_oil() -> "Fuel":
        return Fuel(
            name="Used engine oil",
            lhv_j_per_kg=44.0e6,
            cetane_number=35.0,
            density_kg_per_m3=900.0,
            bulk_modulus_pa=1.80e9,
            stoich_air_fuel=14.0,
            id_a=1.0e-5,
            id_n=1.0,
            id_ea_j_per_mol=6.6e4,
        )

    @staticmethod
    def transformer_oil() -> "Fuel":
        return Fuel(
            name="Transformer oil",
            lhv_j_per_kg=45.0e6,
            cetane_number=45.0,
            density_kg_per_m3=870.0,
            bulk_modulus_pa=1.70e9,
            stoich_air_fuel=14.5,
            id_a=7.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=6.2e4,
        )

    @staticmethod
    def custom(
        *,
        name: str = "Custom",
        density_kg_per_m3: float,
        bulk_modulus_pa: float,
        lhv_j_per_kg: float,
        stoich_air_fuel: float = 14.5,
        cetane_number: float = 45.0,
        id_a: float = 7.0e-6,
        id_n: float = 1.0,
        id_ea_j_per_mol: float = 6.2e4,
    ) -> "Fuel":
        return Fuel(
            name=name,
            lhv_j_per_kg=float(lhv_j_per_kg),
            cetane_number=float(cetane_number),
            density_kg_per_m3=float(density_kg_per_m3),
            bulk_modulus_pa=float(bulk_modulus_pa),
            stoich_air_fuel=float(stoich_air_fuel),
            id_a=float(id_a),
            id_n=float(id_n),
            id_ea_j_per_mol=float(id_ea_j_per_mol),
        )

    def with_density_correction(
        self,
        fuel_temp_c: float,
        *,
        ref_temp_c: float = 15.0,
        coeff_per_c: float = 0.00083,
        min_density_kg_per_m3: float = 600.0,
    ) -> "Fuel":
        rho_corr = float(self.density_kg_per_m3) * (1.0 - (float(fuel_temp_c) - ref_temp_c) * coeff_per_c)
        rho_corr = max(float(min_density_kg_per_m3), rho_corr)
        return replace(self, density_kg_per_m3=rho_corr)

    @staticmethod
    def from_name(
        name: str,
        *,
        density_kgm3: float | None = None,
        bulk_modulus_bar: float | None = None,
        lhv_mjkg: float | None = None,
        stoich_air_fuel: float | None = None,
        id_a: float | None = None,
        id_n: float | None = None,
        id_ea_j_per_mol: float | None = None,
    ) -> "Fuel":
        key = str(name).strip().lower()
        if key == "diesel":
            return Fuel.diesel()
        if key == "svo":
            return Fuel.svo_rapeseed()
        if key == "methanol":
            return Fuel.methanol()
        if key in {"biodiesel", "b100", "fame", "biodiesel_b100_fame"}:
            return Fuel.biodiesel_b100_fame()
        if key in {"margarine", "margaryna", "margarine_melted"}:
            return Fuel.margarine_melted()
        if key in {"lard", "smalec", "lard_liquid"}:
            return Fuel.lard_liquid()
        if key in {"wvo", "used_frying_oil", "wvo_used_frying_oil"}:
            return Fuel.wvo_used_frying_oil()
        if key in {"heating_oil", "oil_heating", "olej_opalowy"}:
            return Fuel.heating_oil()
        if key in {"used_engine_oil", "engine_oil", "olej_silnikowy"}:
            return Fuel.used_engine_oil()
        if key in {"transformer_oil", "olej_transformatorowy"}:
            return Fuel.transformer_oil()
        if key == "custom":
            if density_kgm3 is None or bulk_modulus_bar is None or lhv_mjkg is None:
                raise ValueError("custom fuel requires density_kgm3, bulk_modulus_bar, lhv_mjkg")
            return Fuel.custom(
                density_kg_per_m3=float(density_kgm3),
                bulk_modulus_pa=float(bulk_modulus_bar) * 1e5,
                lhv_j_per_kg=float(lhv_mjkg) * 1e6,
                stoich_air_fuel=float(stoich_air_fuel) if stoich_air_fuel is not None else 14.5,
                id_a=float(id_a) if id_a is not None else 7.0e-6,
                id_n=float(id_n) if id_n is not None else 1.0,
                id_ea_j_per_mol=float(id_ea_j_per_mol) if id_ea_j_per_mol is not None else 6.2e4,
            )
        raise ValueError(f"Unknown fuel name: {name}")


@dataclass(frozen=True)
class InjectionSchedule:
    # Angles in degrees, relative to TDC combustion (0 deg == TDC).
    soi_pilot_deg: float
    soi_main_deg: float
    pilot_fraction: float  # 0..1 of total fuel energy
    duration_pilot_deg: float
    duration_main_deg: float
    wiebe_m_pilot: float = 2.0
    wiebe_m_main: float = 2.0


@dataclass(frozen=True)
class HeatTransferConfig:
    model: Literal["woschni_simplified"] = "woschni_simplified"
    # Wall temperatures for multi-zone model
    head_temp_k: float = 500.0
    piston_temp_k: float = 550.0
    liner_temp_k: float = 450.0
    # Woschni simplified constants: h = c * B^-0.2 * p_bar^0.8 * T^-0.55 * w^0.8
    woschni_c: float = 3.26
    # Gas velocity proxy: w = w_mult * mean_piston_speed
    w_mult: float = 6.0

    @property
    def wall_temp_k(self) -> float:
        return (self.head_temp_k + self.piston_temp_k + self.liner_temp_k) / 3.0


@dataclass(frozen=True)
class CombustionConfig:
    eta_comb: float = 0.98
    wiebe_a: float = 6.9
    # Heat release rate model:
    # - wiebe: classic double-Wiebe (pilot+main)
    # - vp37_main: pilot Wiebe, main shaped by VP37 dm_fuel/dθ and shifted by ignition delay
    # - hydraulic_profile: HRR shape is taken from a pre-computed injection rate profile
    hrr_model: Literal["wiebe", "vp37_main", "hydraulic_profile"] = "wiebe"
    # Ignition delay model choice
    ignition_delay_model: Literal["arrhenius", "fixed_deg"] = "arrhenius"
    fixed_ignition_delay_deg: float = 5.0


@dataclass(frozen=True)
class SimulationConfig:
    rpm: float
    theta_start_deg: float = -180.0
    theta_end_deg: float = 180.0
    step_deg: float = 0.1
    intake_pressure_pa: float = 1.0e5
    intake_temp_k: float = 300.0
    # Total fuel per cylinder per cycle (4-stroke) in mg.
    fuel_mg_per_cycle_per_cyl: float = 20.0
    # Gamma model (per spec): gamma(T) = 1.38 - 0.0001*T
    gamma_t0: float = 1.38
    gamma_slope_per_k: float = 1.0e-4
    gamma_min: float = 1.10
    gamma_max: float = 1.40
    combustion: CombustionConfig = CombustionConfig()
    heat_transfer: HeatTransferConfig = HeatTransferConfig()
    thermo_backend: Literal["simple", "coolprop"] = "coolprop"
    flow_backend: Literal["simple", "fluids"] = "fluids"
    coolprop_fluid: str = "Air"
    strict_backends: bool = True
    integrator: Literal["rk4", "scipy"] = "scipy"
    scipy_method: str = "Radau"
    scipy_rtol: float = 1.0e-7
    scipy_atol: float = 1.0e-9
    scipy_max_step_deg: float = 1.0
    friction_model: FrictionModel = FrictionModel()
    fmep_pa: float = 0.0


@dataclass
class EngineState:
    # Core state integrated in theta domain:
    pressure_pa: float
    # Cached / derived (computed from ideal gas law at each step):
    temperature_k: float
    # Event state for combustion scheduling:
    pilot_soc_deg: Optional[float] = None
    main_soc_deg: Optional[float] = None


from dataclasses import dataclass
from math import pi
from typing import Any

import numpy as np

trapezoid = getattr(np, "trapezoid", np.trapz)

from .physics import CombustionScheduleRuntime, heat_release_rate_dq_dtheta, maybe_arm_combustion
from .physics import geometry_at_theta
from .physics import h_woschni_simplified_w_per_m2_k
from .physics import GasModel, omega_rad_per_s


DEG2RAD = pi / 180.0


@dataclass(frozen=True)
class SimulationResult:
    theta_deg: np.ndarray
    volume_m3: np.ndarray
    pressure_pa: np.ndarray
    temperature_k: np.ndarray
    dq_comb_j_per_deg: np.ndarray
    dq_wall_j_per_deg: np.ndarray
    heat_transfer_area_m2: np.ndarray
    gamma: np.ndarray
    metrics: dict[str, Any]


def _rk4_step_pressure(
    theta_rad: float,
    pressure_pa: float,
    *,
    step_rad: float,
    deriv,
) -> float:
    k1 = deriv(theta_rad, pressure_pa)
    k2 = deriv(theta_rad + 0.5 * step_rad, pressure_pa + 0.5 * step_rad * k1)
    k3 = deriv(theta_rad + 0.5 * step_rad, pressure_pa + 0.5 * step_rad * k2)
    k4 = deriv(theta_rad + step_rad, pressure_pa + step_rad * k3)
    return pressure_pa + (step_rad / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def simulate_closed_cycle(
    geom: EngineGeometry,
    fuel: Fuel,
    schedule: InjectionSchedule,
    cfg: SimulationConfig,
) -> SimulationResult:
    if cfg.integrator == "scipy":
        return simulate_closed_cycle_scipy(geom, fuel, schedule, cfg)
    gas = GasModel()
    omega = omega_rad_per_s(cfg.rpm)
    mean_piston_speed = 2.0 * geom.stroke_m * cfg.rpm / 60.0

    theta_deg = np.arange(cfg.theta_start_deg, cfg.theta_end_deg + cfg.step_deg / 2.0, cfg.step_deg, dtype=float)
    theta_rad = theta_deg * DEG2RAD

    geom0 = geometry_at_theta(geom, theta_rad[0])
    V0 = geom0.volume_m3
    # Initial mass from intake state at start angle.
    mass_kg = cfg.intake_pressure_pa * V0 / (gas.r_j_per_kg_k * cfg.intake_temp_k)

    q_total_j = (cfg.fuel_mg_per_cycle_per_cyl * 1e-6) * fuel.lhv_j_per_kg * cfg.combustion.eta_comb

    pressure = np.zeros_like(theta_rad)
    temperature = np.zeros_like(theta_rad)
    dq_comb = np.zeros_like(theta_rad)
    dq_wall = np.zeros_like(theta_rad)
    volume = np.zeros_like(theta_rad)
    a_ht = np.zeros_like(theta_rad)
    gamma = np.zeros_like(theta_rad)

    pressure[0] = cfg.intake_pressure_pa
    temperature[0] = cfg.intake_temp_k
    runtime = CombustionScheduleRuntime()

    def deriv(theta_r: float, p_pa: float) -> float:
        geom_res = geometry_at_theta(geom, theta_r)
        V = geom_res.volume_m3
        T = max(1.0, p_pa * V / (mass_kg * gas.r_j_per_kg_k))
        g = gas.gamma(T, cfg, pressure_pa=p_pa)

        dq_comb_dtheta = heat_release_rate_dq_dtheta(
            theta_r,
            fuel=fuel,
            q_total_j=q_total_j,
            schedule=schedule,
            cfg=cfg.combustion,
            runtime=runtime,
        )

        if cfg.heat_transfer.model != "woschni_simplified":
            raise ValueError(f"Unsupported heat transfer model: {cfg.heat_transfer.model}")
        h = h_woschni_simplified_w_per_m2_k(
            bore_m=geom.bore_m,
            pressure_pa=p_pa,
            temperature_k=T,
            mean_piston_speed_m_per_s=mean_piston_speed,
            cfg=cfg.heat_transfer,
        )
        qdot_wall_w = h * geom_res.heat_transfer_area_m2 * (T - cfg.heat_transfer.wall_temp_k)
        dq_wall_dtheta = qdot_wall_w / max(1e-9, omega)  # J/rad

        return ((g - 1.0) / V) * (dq_comb_dtheta - dq_wall_dtheta) - (g * p_pa / V) * geom_res.dvol_dtheta_m3_per_rad

    for i in range(1, len(theta_rad)):
        # Arm combustion start angles at step boundaries (keeps RK4 derivative pure).
        geom_prev = geometry_at_theta(geom, theta_rad[i - 1])
        temp_prev = max(1.0, pressure[i - 1] * geom_prev.volume_m3 / (mass_kg * gas.r_j_per_kg_k))
        runtime = maybe_arm_combustion(
            theta_deg[i - 1],
            pressure_pa=pressure[i - 1],
            temperature_k=temp_prev,
            fuel=fuel,
            schedule=schedule,
            sim_cfg=cfg,
            runtime=runtime,
            air_mass_kg=mass_kg,
        )

        p_next = _rk4_step_pressure(theta_rad[i - 1], pressure[i - 1], step_rad=cfg.step_deg * DEG2RAD, deriv=deriv)
        pressure[i] = max(1e3, p_next)

        geom_res = geometry_at_theta(geom, theta_rad[i])
        volume[i] = geom_res.volume_m3
        a_ht[i] = geom_res.heat_transfer_area_m2
        temperature[i] = max(1.0, pressure[i] * volume[i] / (mass_kg * gas.r_j_per_kg_k))
        gamma[i] = gas.gamma(temperature[i], cfg, pressure_pa=pressure[i])

        runtime = maybe_arm_combustion(
            theta_deg[i],
            pressure_pa=pressure[i],
            temperature_k=temperature[i],
            fuel=fuel,
            schedule=schedule,
            sim_cfg=cfg,
            runtime=runtime,
            air_mass_kg=mass_kg,
        )

        # Store energy rates per degree for reporting (more human-friendly).
        dq_comb[i] = heat_release_rate_dq_dtheta(
            theta_rad[i],
            fuel=fuel,
            q_total_j=q_total_j,
            schedule=schedule,
            cfg=cfg.combustion,
            runtime=runtime,
        ) * DEG2RAD

        h = h_woschni_simplified_w_per_m2_k(
            bore_m=geom.bore_m,
            pressure_pa=pressure[i],
            temperature_k=temperature[i],
            mean_piston_speed_m_per_s=mean_piston_speed,
            cfg=cfg.heat_transfer,
        )
        qdot_wall_w = h * geom_res.heat_transfer_area_m2 * (temperature[i] - cfg.heat_transfer.wall_temp_k)
        dq_wall[i] = (qdot_wall_w / max(1e-9, omega)) * DEG2RAD

    # Fill volume[0] and gamma[0]
    volume[0] = geom0.volume_m3
    a_ht[0] = geom0.heat_transfer_area_m2
    gamma[0] = gas.gamma(temperature[0], cfg, pressure_pa=pressure[0])

    # Metrics
    # Indicated work over the simulated window: Wi = ∫ P dV
    dV = np.gradient(volume, theta_rad)  # m3/rad
    wi_j = float(trapezoid(pressure * dV, theta_rad))
    imep_pa = wi_j / geom.swept_volume_m3_per_cyl
    vd_total = geom.swept_volume_m3_per_cyl * geom.cylinders
    indicated_torque_nm = imep_pa * vd_total / (4.0 * pi)  # 4-stroke
    brake_torque_nm = max(0.0, (imep_pa - cfg.fmep_pa) * vd_total / (4.0 * pi))

    metrics = {
        "mass_kg_per_cyl": mass_kg,
        "q_total_j_per_cyl": q_total_j,
        "peak_pressure_bar": float(np.max(pressure) / 1.0e5),
        "peak_temp_k": float(np.max(temperature)),
        "wi_j_per_cyl": wi_j,
        "imep_bar": imep_pa / 1.0e5,
        "indicated_torque_nm": indicated_torque_nm,
        "brake_torque_nm_est": brake_torque_nm,
    }

    return SimulationResult(
        theta_deg=theta_deg,
        volume_m3=volume,
        pressure_pa=pressure,
        temperature_k=temperature,
        dq_comb_j_per_deg=dq_comb,
        dq_wall_j_per_deg=dq_wall,
        heat_transfer_area_m2=a_ht,
        gamma=gamma,
        metrics=metrics,
    )


def simulate_closed_cycle_scipy(
    geom: EngineGeometry,
    fuel: Fuel,
    schedule: InjectionSchedule,
    cfg: SimulationConfig,
) -> SimulationResult:
    try:
        from scipy.integrate import solve_ivp
    except Exception as e:
        raise RuntimeError("SciPy is required for integrator='scipy'.") from e

    gas = GasModel()
    omega = omega_rad_per_s(cfg.rpm)
    mean_piston_speed = 2.0 * geom.stroke_m * cfg.rpm / 60.0

    theta_deg = np.arange(cfg.theta_start_deg, cfg.theta_end_deg + cfg.step_deg / 2.0, cfg.step_deg, dtype=float)
    theta_rad = theta_deg * DEG2RAD

    geom0 = geometry_at_theta(geom, theta_rad[0])
    rho0 = gas.density_from_pT(cfg.intake_pressure_pa, cfg.intake_temp_k, cfg)
    mass_kg = rho0 * geom0.volume_m3

    q_total_j = (cfg.fuel_mg_per_cycle_per_cyl * 1e-6) * fuel.lhv_j_per_kg * cfg.combustion.eta_comb

    # Initialize runtime at start (handles SOI before start).
    runtime = CombustionScheduleRuntime()
    runtime = maybe_arm_combustion(
        theta_deg[0],
        pressure_pa=cfg.intake_pressure_pa,
        temperature_k=cfg.intake_temp_k,
        fuel=fuel,
        schedule=schedule,
        sim_cfg=cfg,
        runtime=runtime,
        air_mass_kg=mass_kg,
    )

    # Segment boundaries at SOI angles within range.
    soi_list = []
    for soi in (schedule.soi_pilot_deg, schedule.soi_main_deg):
        if cfg.theta_start_deg < soi < cfg.theta_end_deg:
            soi_list.append(soi)
    soi_list = sorted(set(soi_list))

    T_grid = np.zeros_like(theta_rad)

    def rhs(theta_r: float, y: np.ndarray, rt: CombustionScheduleRuntime) -> np.ndarray:
        T = float(max(1.0, y[0]))
        geo = geometry_at_theta(geom, theta_r)
        V = geo.volume_m3
        rho = mass_kg / max(1e-12, V)
        P = gas.pressure_from_rhoT(rho, T, cfg)
        g = gas.gamma(T, cfg, pressure_pa=P)
        cv = gas.cv(T, cfg, pressure_pa=P)

        dq_comb_dtheta = heat_release_rate_dq_dtheta(
            theta_r,
            fuel=fuel,
            q_total_j=q_total_j,
            schedule=schedule,
            cfg=cfg.combustion,
            runtime=rt,
        )

        h = h_woschni_simplified_w_per_m2_k(
            bore_m=geom.bore_m,
            pressure_pa=P,
            temperature_k=T,
            mean_piston_speed_m_per_s=mean_piston_speed,
            cfg=cfg.heat_transfer,
        )
        qdot_wall_w = h * geo.heat_transfer_area_m2 * (T - cfg.heat_transfer.wall_temp_k)
        dq_wall_dtheta = qdot_wall_w / max(1e-9, omega)

        dT_dtheta = (dq_comb_dtheta - dq_wall_dtheta - P * geo.dvol_dtheta_m3_per_rad) / max(1e-9, mass_kg * cv)
        return np.array([dT_dtheta], dtype=float)

    theta_start = float(theta_rad[0])
    theta_end = float(theta_rad[-1])
    seg_points = [theta_start] + [s * DEG2RAD for s in soi_list] + [theta_end]

    T0 = float(cfg.intake_temp_k)
    for i in range(len(seg_points) - 1):
        a = seg_points[i]
        b = seg_points[i + 1]
        if b < a + 1e-12:
            continue
        mask = (theta_rad >= a - 1e-12) & (theta_rad <= b + 1e-12)
        t_eval = theta_rad[mask]
        sol = solve_ivp(
            lambda tr, y: rhs(tr, y, runtime),
            (a, b),
            np.array([T0], dtype=float),
            t_eval=t_eval,
            method=str(cfg.scipy_method),
            rtol=float(cfg.scipy_rtol),
            atol=float(cfg.scipy_atol),
            max_step=max(1e-9, float(cfg.scipy_max_step_deg) * DEG2RAD),
        )
        if not sol.success:
            raise RuntimeError(f"SciPy solver failed: {sol.message}")
        T_grid[mask] = sol.y[0]
        T0 = float(sol.y[0][-1])

        # Update runtime at segment boundary if it is an SOI point.
        if i < len(seg_points) - 2:
            theta_deg_event = float(b / DEG2RAD)
            geo = geometry_at_theta(geom, b)
            rho = mass_kg / max(1e-12, geo.volume_m3)
            P = gas.pressure_from_rhoT(rho, T0, cfg)
            runtime = maybe_arm_combustion(
                theta_deg_event,
                pressure_pa=P,
                temperature_k=T0,
                fuel=fuel,
                schedule=schedule,
                sim_cfg=cfg,
                runtime=runtime,
                air_mass_kg=mass_kg,
            )

    # Post-process outputs on grid
    volume = np.zeros_like(theta_rad)
    pressure = np.zeros_like(theta_rad)
    dq_comb = np.zeros_like(theta_rad)
    dq_wall = np.zeros_like(theta_rad)
    a_ht = np.zeros_like(theta_rad)
    gamma = np.zeros_like(theta_rad)
    for i, tr in enumerate(theta_rad):
        geo = geometry_at_theta(geom, tr)
        volume[i] = geo.volume_m3
        a_ht[i] = geo.heat_transfer_area_m2
        rho = mass_kg / max(1e-12, geo.volume_m3)
        P = gas.pressure_from_rhoT(rho, float(T_grid[i]), cfg)
        pressure[i] = P
        gamma[i] = gas.gamma(float(T_grid[i]), cfg, pressure_pa=P)
        dq_comb[i] = heat_release_rate_dq_dtheta(
            tr,
            fuel=fuel,
            q_total_j=q_total_j,
            schedule=schedule,
            cfg=cfg.combustion,
            runtime=runtime,
        ) * DEG2RAD
        h = h_woschni_simplified_w_per_m2_k(
            bore_m=geom.bore_m,
            pressure_pa=P,
            temperature_k=float(T_grid[i]),
            mean_piston_speed_m_per_s=mean_piston_speed,
            cfg=cfg.heat_transfer,
        )
        qdot_wall_w = h * geo.heat_transfer_area_m2 * (float(T_grid[i]) - cfg.heat_transfer.wall_temp_k)
        dq_wall[i] = (qdot_wall_w / max(1e-9, omega)) * DEG2RAD

    dV = np.gradient(volume, theta_rad)
    wi_j = float(trapezoid(pressure * dV, theta_rad))
    imep_pa = wi_j / geom.swept_volume_m3_per_cyl
    vd_total = geom.swept_volume_m3_per_cyl * geom.cylinders
    indicated_torque_nm = imep_pa * vd_total / (4.0 * pi)
    brake_torque_nm = max(0.0, (imep_pa - cfg.fmep_pa) * vd_total / (4.0 * pi))

    metrics = {
        "mass_kg_per_cyl": mass_kg,
        "q_total_j_per_cyl": q_total_j,
        "peak_pressure_bar": float(np.max(pressure) / 1.0e5),
        "peak_temp_k": float(np.max(T_grid)),
        "wi_j_per_cyl": wi_j,
        "imep_bar": imep_pa / 1.0e5,
        "indicated_torque_nm": indicated_torque_nm,
        "brake_torque_nm_est": brake_torque_nm,
    }

    return SimulationResult(
        theta_deg=theta_deg,
        volume_m3=volume,
        pressure_pa=pressure,
        temperature_k=T_grid,
        dq_comb_j_per_deg=dq_comb,
        dq_wall_j_per_deg=dq_wall,
        heat_transfer_area_m2=a_ht,
        gamma=gamma,
        metrics=metrics,
    )


from dataclasses import dataclass
from math import pi
from typing import Any

import numpy as np

trapezoid = getattr(np, "trapezoid", np.trapz)

from .physics import (
    CombustionScheduleRuntime,
    heat_release_rate_dq_dtheta,
    heat_release_rate_from_shaped_fuel,
    heat_release_rate_wiebe_single,
    maybe_arm_combustion,
)
from .emissions import estimate_emissions
from .physics import orifice_mdot_kg_per_s
from .physics import geometry_at_theta
from .physics import h_woschni_simplified_w_per_m2_k, calculate_wall_heat_loss_j_per_rad
from .physics import GasModel, omega_rad_per_s
from .physics import ValveFlow, ValveTiming, effective_curtain_area_m2, valve_lift_fraction
from .injection import ValveLiftTable
from .injection import VP37CamProfile


DEG2RAD = pi / 180.0


@dataclass(frozen=True)
class BoundaryConditions:
    intake_pressure_pa: float = 1.0e5
    intake_temp_k: float = 300.0
    exhaust_pressure_pa: float = 1.15e5
    exhaust_temp_k: float = 800.0


@dataclass(frozen=True)
class FullCycleConfig:
    rpm: float
    step_deg: float = 0.1
    cycles: int = 3
    theta_start_deg: float = -360.0
    theta_end_deg: float = 360.0
    fuel_mg_per_cycle_per_cyl: float = 20.0
    intake_manifold_config: ManifoldConfig = ManifoldConfig(volume_m3=2e-3)
    exhaust_manifold_config: ManifoldConfig = ManifoldConfig(volume_m3=1.5e-3)
    boundaries: BoundaryConditions | None = None
    p_ambient_pa: float = 1.0e5
    t_ambient_k: float = 300.0
    # External connections for manifold mass exchange. These default to ambient,
    # but should be set to compressor outlet / exhaust tailpipe conditions.
    p_intake_supply_pa: float | None = None
    t_intake_supply_k: float | None = None
    p_exhaust_sink_pa: float | None = None
    t_exhaust_sink_k: float | None = None
    # Effective throttle / exhaust restriction area (m^2). Used for ambient<->manifold exchange.
    # NOTE: If too small, manifolds become "thermal capacitors" and temperatures can diverge.
    manifold_throttle_coeff: float = 6e-4
    valve_timing: ValveTiming = ValveTiming()
    valve_flow: ValveFlow = ValveFlow()
    valve_lift_table: ValveLiftTable | None = None
    cylinder: int = 1
    tdc_offset_deg: dict[int, float] = None
    vp37_cam_profile: VP37CamProfile | None = None
    vp37_iq_max_mg: float = 51.0
    vp37_delivery_start_frac: float = 0.40
    reciprocating_mass_kg: float = 0.73
    injection_profile: tuple[np.ndarray, np.ndarray] | None = None
    models: SimulationConfig = SimulationConfig(rpm=1500.0)
    m_min_kg: float = 1.0e-7
    t_min_k: float = 200.0
    t_max_k: float = 4500.0
    p_max_prev_pa: float = 0.0
    vehicle_speed_kmh: float = 0.0
    intercooler_config: IntercoolerConfig = IntercoolerConfig()
    egr_valve_max_area_m2: float = 0.0001 # Max effective area of the EGR valve
    egr_valve_pos_fraction: float = 0.0 # EGR valve position from 0.0 (closed) to 1.0 (open)
    egr_discharge_coeff: float = 0.8 # Discharge coefficient for the EGR valve
    dual_fuel_lpg_frac: float = 0.0
    # Simple manifold heat loss model (W/K) to prevent unrealistically high manifold temperatures.
    intake_heat_loss_w_per_k: float = 60.0
    exhaust_heat_loss_w_per_k: float = 220.0

    def __post_init__(self) -> None:
        if self.p_intake_supply_pa is None:
            object.__setattr__(self, "p_intake_supply_pa", float(self.p_ambient_pa))
        if self.t_intake_supply_k is None:
            object.__setattr__(self, "t_intake_supply_k", float(self.t_ambient_k))
        if self.p_exhaust_sink_pa is None:
            object.__setattr__(self, "p_exhaust_sink_pa", float(self.p_ambient_pa))
        if self.t_exhaust_sink_k is None:
            object.__setattr__(self, "t_exhaust_sink_k", float(self.t_ambient_k))
        if self.boundaries is None:
            object.__setattr__(
                self,
                "boundaries",
                BoundaryConditions(
                    intake_pressure_pa=self.intake_manifold_config.initial_pressure_pa,
                    intake_temp_k=self.intake_manifold_config.initial_temp_k,
                    exhaust_pressure_pa=self.exhaust_manifold_config.initial_pressure_pa,
                    exhaust_temp_k=self.exhaust_manifold_config.initial_temp_k,
                ),
            )
        else:
            object.__setattr__(
                self,
                "intake_manifold_config",
                ManifoldConfig(
                    volume_m3=self.intake_manifold_config.volume_m3,
                    initial_temp_k=self.boundaries.intake_temp_k,
                    initial_pressure_pa=self.boundaries.intake_pressure_pa,
                ),
            )
            object.__setattr__(
                self,
                "exhaust_manifold_config",
                ManifoldConfig(
                    volume_m3=self.exhaust_manifold_config.volume_m3,
                    initial_temp_k=self.boundaries.exhaust_temp_k,
                    initial_pressure_pa=self.boundaries.exhaust_pressure_pa,
                ),
            )
        if self.tdc_offset_deg is None:
            object.__setattr__(self, "tdc_offset_deg", {1: 0.0, 3: 180.0, 4: 360.0, 2: 540.0})


@dataclass(frozen=True)
class FullCycleResult:
    theta_deg: np.ndarray
    volume_m3: np.ndarray
    pressure_pa: np.ndarray
    temperature_k: np.ndarray
    mass_kg: np.ndarray
    p_intake_pa: np.ndarray
    t_intake_k: np.ndarray
    p_exhaust_pa: np.ndarray
    t_exhaust_k: np.ndarray
    mdot_intake_kg_s: np.ndarray
    mdot_exhaust_kg_s: np.ndarray
    intake_lift_frac: np.ndarray
    exhaust_lift_frac: np.ndarray
    dq_comb_j_per_deg: np.ndarray
    dq_wall_j_per_deg: np.ndarray
    dm_fuel_main_mg_per_deg: np.ndarray
    torque_indicated_nm_per_cyl: np.ndarray
    metrics: dict[str, Any]


def _rk4_step(theta_rad: float, state: np.ndarray, *, step_rad: float, deriv) -> np.ndarray:
    k1 = deriv(theta_rad, state)
    k2 = deriv(theta_rad + 0.5 * step_rad, state + 0.5 * step_rad * k1)
    k3 = deriv(theta_rad + 0.5 * step_rad, state + 0.5 * step_rad * k2)
    k4 = deriv(theta_rad + step_rad, state + step_rad * k3)
    return state + (step_rad / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def simulate_full_cycle(
    geom: EngineGeometry,
    fuel: Fuel,
    schedule,
    cfg: FullCycleConfig,
) -> FullCycleResult:
    gas = GasModel()
    omega = omega_rad_per_s(cfg.rpm)
    mean_piston_speed = 2.0 * geom.stroke_m * cfg.rpm / 60.0

    theta_deg = np.arange(cfg.theta_start_deg, cfg.theta_end_deg + cfg.step_deg / 2.0, cfg.step_deg, dtype=float)
    theta_rad = theta_deg * DEG2RAD
    step_rad = cfg.step_deg * DEG2RAD

    q_total_j = (cfg.fuel_mg_per_cycle_per_cyl * 1e-6) * fuel.lhv_j_per_kg * cfg.models.combustion.eta_comb
    m_fuel_total_kg = (cfg.fuel_mg_per_cycle_per_cyl * 1e-6)

    intake_state = ManifoldState.from_config(cfg.intake_manifold_config)
    exhaust_state = ManifoldState.from_config(cfg.exhaust_manifold_config)
    exhaust_state.exhaust_gas_fraction = 1.0 # Assuming exhaust manifold is initially full of exhaust gases

    geom0 = geometry_at_theta(geom, theta_rad[0])
    rho0 = intake_state.mass_kg / cfg.intake_manifold_config.volume_m3
    m0_cyl = rho0 * geom0.volume_m3
    t0_cyl = intake_state.temperature_k

    cyl = cfg.cylinder
    if cyl not in (1, 2, 3, 4): raise ValueError("cfg.cylinder must be 1..4")
    tdc_offset = float(cfg.tdc_offset_deg.get(cyl, 0.0))

    def lift_m(theta_local_deg: float, valve: str) -> float:
        if cfg.valve_lift_table is not None:
            return cfg.valve_lift_table.lift_m(theta_local_deg + tdc_offset, cylinder=cyl, valve=valve)
        frac = valve_lift_fraction(theta_local_deg, cfg.valve_timing.ivo_deg, cfg.valve_timing.ivc_deg) if valve == "intake" else valve_lift_fraction(theta_local_deg, cfg.valve_timing.evo_deg, cfg.valve_timing.evc_deg)
        max_lift = cfg.valve_flow.intake_max_lift_m if valve == "intake" else cfg.valve_flow.exhaust_max_lift_m
        return max_lift * frac

    main_u, main_w = None, None
    if cfg.vp37_cam_profile:
        main_u, main_w = cfg.vp37_cam_profile.rate_shape_u_w(
            iq_mg_per_stroke=cfg.fuel_mg_per_cycle_per_cyl, cylinder=cyl,
            iq_max_mg=cfg.vp37_iq_max_mg, delivery_start_frac=cfg.vp37_delivery_start_frac, samples=250,
        )

    def run_one_cycle(init_state: np.ndarray, p_max_prev_pa: float):
        results = {k: np.zeros_like(theta_rad) for k in ["pressure", "temp", "mass", "p_intake", "t_intake", "p_exhaust", "t_exhaust", "mdot_in", "mdot_ex", "lift_i", "lift_e", "dq_comb", "dq_wall", "torque", "dm_fuel_main_mg_per_deg"]}
        state, runtime = init_state.copy(), CombustionScheduleRuntime()
        current_p_max_pa = 0.0
        
        for i, (theta_d, theta_r) in enumerate(zip(theta_deg, theta_rad)):
            m_c, t_c, m_i, t_i, f_i, m_e, t_e, f_e, t_ic = state
            
            geo = geometry_at_theta(geom, theta_r)
            rho_c = m_c / max(1e-12, geo.volume_m3)
            p_c = max(1.0, gas.pressure_from_rhoT(rho_c, t_c, cfg.models))
            p_i = gas.pressure_from_rhoT(m_i / cfg.intake_manifold_config.volume_m3, t_i, cfg.models)
            p_e = gas.pressure_from_rhoT(m_e / cfg.exhaust_manifold_config.volume_m3, t_e, cfg.models)

            current_p_max_pa = max(current_p_max_pa, p_c)

            for k, v in [("pressure",p_c), ("temp",t_c), ("mass",m_c), ("p_intake",p_i), ("t_intake",t_i), ("p_exhaust",p_e), ("t_exhaust",t_e)]: results[k][i] = v
            
            li_m, le_m = lift_m(theta_d, "intake"), lift_m(theta_d, "exhaust")
            results["lift_i"][i], results["lift_e"][i] = li_m / max(1e-9, cfg.valve_flow.intake_max_lift_m), le_m / max(1e-9, cfg.valve_flow.exhaust_max_lift_m)
            
            runtime = maybe_arm_combustion(
                theta_d,
                pressure_pa=p_c,
                temperature_k=t_c,
                fuel=fuel,
                schedule=schedule,
                sim_cfg=cfg.models,
                runtime=runtime,
                air_mass_kg=m_c,
            )

            dur_main_rad, soi_main_rad = schedule.duration_main_deg*DEG2RAD, schedule.soi_main_deg*DEG2RAD
            m_main_kg = m_fuel_total_kg * (1.0 - max(0.0, min(1.0, schedule.pilot_fraction)))
            dm_dtheta = 0.0
            if main_u is not None and main_w is not None and dur_main_rad > 0:
                dm_dtheta = (m_main_kg / dur_main_rad) * float(np.interp(float((theta_r - soi_main_rad) / dur_main_rad), main_u, main_w, left=0.0, right=0.0))
                if (theta_r - soi_main_rad) <= 0.0 or (theta_r - soi_main_rad) >= dur_main_rad: dm_dtheta = 0.0
            results["dm_fuel_main_mg_per_deg"][i] = (dm_dtheta * DEG2RAD) * 1e6

            derivs, mdot_in, mdot_ex, dq_c, dq_w = _eval(theta_r, state, runtime)
            results["mdot_in"][i], results["mdot_ex"][i] = mdot_in, mdot_ex
            results["dq_comb"][i], results["dq_wall"][i] = dq_c * DEG2RAD, dq_w * DEG2RAD
            results["torque"][i] = p_c * geo.dvol_dtheta_m3_per_rad

            if i < len(theta_rad) - 1:
                state = _rk4_step(theta_r, state, step_rad=step_rad, deriv=lambda t, s: _eval(t, s, runtime)[0])
                state[[1, 3, 6, 8]] = np.clip(state[[1, 3, 6, 8]], cfg.t_min_k, cfg.t_max_k) # Clip temperatures

        return results, state, current_p_max_pa

    def _eval(theta_r, state_vec, rt):
        m_c, t_c, m_i, t_i, f_i, m_e, t_e, f_e, t_ic = state_vec
        geo = geometry_at_theta(geom, theta_r)
        
        rho_c = m_c / max(1e-12, geo.volume_m3)
        p_c = max(1.0, gas.pressure_from_rhoT(rho_c, t_c, cfg.models))
        p_i = gas.pressure_from_rhoT(m_i / cfg.intake_manifold_config.volume_m3, t_i, cfg.models)
        p_e = gas.pressure_from_rhoT(m_e / cfg.exhaust_manifold_config.volume_m3, t_e, cfg.models)
        
        g_c, cp_c, cv_c = (
            gas.gamma(t_c, cfg.models, pressure_pa=p_c),
            gas.cp(t_c, cfg.models, pressure_pa=p_c),
            gas.cv(t_c, cfg.models, pressure_pa=p_c),
        )
        g_i, cp_i, cv_i = (
            gas.gamma(t_i, cfg.models, pressure_pa=p_i),
            gas.cp(t_i, cfg.models, pressure_pa=p_i),
            gas.cv(t_i, cfg.models, pressure_pa=p_i),
        )
        g_e, cp_e, cv_e = (
            gas.gamma(t_e, cfg.models, pressure_pa=p_e),
            gas.cp(t_e, cfg.models, pressure_pa=p_e),
            gas.cv(t_e, cfg.models, pressure_pa=p_e),
        )
        p_sup = float(cfg.p_intake_supply_pa)
        t_sup = float(cfg.t_intake_supply_k)
        p_sink = float(cfg.p_exhaust_sink_pa)
        t_sink = float(cfg.t_exhaust_sink_k)
        g_sup, cp_sup = (
            gas.gamma(t_sup, cfg.models, pressure_pa=p_sup),
            gas.cp(t_sup, cfg.models, pressure_pa=p_sup),
        )
        g_sink, cp_sink = (
            gas.gamma(t_sink, cfg.models, pressure_pa=p_sink),
            gas.cp(t_sink, cfg.models, pressure_pa=p_sink),
        )

        li_m, le_m = lift_m(theta_r / DEG2RAD, "intake"), lift_m(theta_r / DEG2RAD, "exhaust")
        a_i, a_e = effective_curtain_area_m2(cfg.valve_flow.intake_valve_diameter_m, li_m), effective_curtain_area_m2(cfg.valve_flow.exhaust_valve_diameter_m, le_m)
        
        mdot_i_c = orifice_mdot_kg_per_s(p1_pa=p_i, t1_k=t_i, p2_pa=p_c, gamma=g_i, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=a_i, discharge_coeff=cfg.valve_flow.cd_intake, backend=cfg.models.flow_backend)
        mdot_c_e = orifice_mdot_kg_per_s(p1_pa=p_c, t1_k=t_c, p2_pa=p_e, gamma=g_c, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=a_e, discharge_coeff=cfg.valve_flow.cd_exhaust, backend=cfg.models.flow_backend)
        
        mdot_sup_i = orifice_mdot_kg_per_s(
            p1_pa=p_sup,
            t1_k=t_sup,
            p2_pa=p_i,
            gamma=g_sup,
            r_j_per_kg_k=gas.r_j_per_kg_k,
            area_m2=cfg.manifold_throttle_coeff,
            discharge_coeff=0.8,
        )
        mdot_e_sink = orifice_mdot_kg_per_s(
            p1_pa=p_e,
            t1_k=t_e,
            p2_pa=p_sink,
            gamma=g_e,
            r_j_per_kg_k=gas.r_j_per_kg_k,
            area_m2=cfg.manifold_throttle_coeff,
            discharge_coeff=0.8,
        )
        
        # EGR flow
        area_egr = cfg.egr_valve_max_area_m2 * cfg.egr_valve_pos_fraction
        mdot_egr = orifice_mdot_kg_per_s(p1_pa=p_e, t1_k=t_e, p2_pa=p_i, gamma=g_e, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=area_egr, discharge_coeff=cfg.egr_discharge_coeff, backend=cfg.models.flow_backend)

        dm_cyl_dtheta = (mdot_i_c - mdot_c_e)/omega
        dm_intake_dtheta = (mdot_sup_i - mdot_i_c + mdot_egr)/omega
        dm_exhaust_dtheta = (mdot_c_e - mdot_e_sink - mdot_egr)/omega
        
        # Calculate derivatives for exhaust gas fractions
        mdot_in_i_from_ambient = max(0.0, mdot_sup_i)
        mdot_in_i_from_cylinder = max(0.0, -mdot_i_c)
        mdot_in_i_from_egr = max(0.0, mdot_egr) # EGR flow from exhaust to intake
        f_in_ambient = 0.0 # Ambient air is fresh air
        f_in_cylinder = 1.0 # Assuming gas from cylinder into intake is pure exhaust during backflow
        f_in_egr = f_e # EGR flow brings exhaust gas from exhaust manifold
        
        df_intake_dtheta = ( (mdot_in_i_from_ambient * (f_in_ambient - f_i)) + (mdot_in_i_from_cylinder * (f_in_cylinder - f_i)) + (mdot_in_i_from_egr * (f_in_egr - f_i)) ) / (max(cfg.m_min_kg, m_i) * omega)

        mdot_in_e_from_cylinder = max(0.0, mdot_c_e)
        mdot_out_e_to_egr = max(0.0, -mdot_egr) # Flow from exhaust to EGR to intake
        f_in_cylinder_exhaust = 1.0 # Assuming gas from cylinder into exhaust is pure exhaust
        
        df_exhaust_dtheta = ( (mdot_in_e_from_cylinder * (f_in_cylinder_exhaust - f_e)) - (mdot_out_e_to_egr * (f_e - f_e)) ) / (max(cfg.m_min_kg, m_e) * omega)
        # Note: (f_e - f_e) is 0, so mdot_out_e_to_egr does not directly affect df_exhaust_dtheta for current approach.
        # It's already accounted for in dm_exhaust_dtheta.
        
        dq_c = heat_release_rate_dq_dtheta(
            theta_r,
            fuel=fuel,
            q_total_j=q_total_j,
            schedule=schedule,
            cfg=cfg.models.combustion,
            runtime=rt,
            injection_profile=cfg.injection_profile
        )
        
        htc = h_woschni_simplified_w_per_m2_k(
            bore_m=geom.bore_m,
            pressure_pa=p_c,
            temperature_k=t_c,
            mean_piston_speed_m_per_s=mean_piston_speed,
            cfg=cfg.models.heat_transfer
        )
        dq_w = calculate_wall_heat_loss_j_per_rad(
            h_coeff=htc,
            gas_temp_k=t_c,
            area_head_m2=geo.area_head_m2,
            area_piston_m2=geo.area_piston_m2,
            area_liner_m2=geo.area_liner_m2,
            cfg=cfg.models.heat_transfer,
            omega_rad_per_s=omega,
        )
        
        h_i_c_flow = cp_i*t_i if mdot_i_c > 0 else cp_c*t_c
        h_c_e_flow = cp_c*t_c if mdot_c_e > 0 else cp_e*t_e
        dH_flow = (mdot_i_c * h_i_c_flow - mdot_c_e * h_c_e_flow) / omega
        
        dT_cyl_dtheta = (dq_c - dq_w - p_c*geo.dvol_dtheta_m3_per_rad + dH_flow - cv_c*t_c*dm_cyl_dtheta) / max(cfg.m_min_kg*cv_c, m_c*cv_c)
        
        h_amb_i = cp_sup * t_sup
        h_i_c = cp_i * t_i
        # Enthalpy flow from EGR to intake manifold
        h_egr_to_intake_flow = cp_e * t_e if mdot_egr > 0 else cp_i * t_i
        
        q_intake_loss_w = cfg.intake_heat_loss_w_per_k * max(0.0, (t_i - cfg.t_ambient_k))
        dT_intake_dtheta = (
            ((mdot_sup_i * h_amb_i - mdot_i_c * h_i_c + mdot_egr * h_egr_to_intake_flow) / omega)
            - (q_intake_loss_w / omega)
            - cv_i * t_i * dm_intake_dtheta
        ) / max(cfg.m_min_kg * cv_i, m_i * cv_i)
        
        h_c_e = cp_c * t_c
        h_e_sink = (cp_e * t_e) if mdot_e_sink > 0 else (cp_sink * t_sink)
        # Enthalpy flow from exhaust manifold to EGR
        h_egr_from_exhaust_flow = cp_e * t_e if mdot_egr > 0 else cp_i * t_i
        
        q_exhaust_loss_w = cfg.exhaust_heat_loss_w_per_k * max(0.0, (t_e - cfg.t_ambient_k))
        dT_exhaust_dtheta = (
            ((mdot_c_e * h_c_e - mdot_e_sink * h_e_sink - mdot_egr * h_egr_from_exhaust_flow) / omega)
            - (q_exhaust_loss_w / omega)
            - cv_e * t_e * dm_exhaust_dtheta
        ) / max(cfg.m_min_kg * cv_e, m_e * cv_e)
        
        # Intercooler core heat soak model
        h_ambient_ic = cfg.intercooler_config.h_ambient_w_per_m2_k_base + cfg.intercooler_config.h_ambient_w_per_m2_k_factor_v * cfg.vehicle_speed_kmh
        q_ambient_ic_w = h_ambient_ic * cfg.intercooler_config.area_ext_m2 * (t_ic - cfg.t_ambient_k)
        
        # Simplified Q_air_in for intercooler core (interaction with intake manifold air)
        # Assuming heat transfer is proportional to temperature difference between intake air and intercooler core
        q_air_in_ic_w = cfg.intercooler_config.h_ic_air_w_per_m2_k * cfg.intercooler_config.area_ic_air_m2 * (t_i - t_ic)
        
        dt_ic_dt = (q_air_in_ic_w - q_ambient_ic_w) / (cfg.intercooler_config.mass_al_kg * cfg.intercooler_config.cp_al_j_per_kg_k)
        dt_ic_dtheta = dt_ic_dt / omega
        
        derivs = np.array(
            [
                dm_cyl_dtheta,
                dT_cyl_dtheta,
                dm_intake_dtheta,
                dT_intake_dtheta,
                df_intake_dtheta,
                dm_exhaust_dtheta,
                dT_exhaust_dtheta,
                df_exhaust_dtheta,
                dt_ic_dtheta,
            ]
        )
        return derivs, mdot_i_c, -mdot_c_e, dq_c, dq_w

    state = np.array([m0_cyl, t0_cyl, intake_state.mass_kg, intake_state.temperature_k, intake_state.exhaust_gas_fraction, exhaust_state.mass_kg, exhaust_state.temperature_k, exhaust_state.exhaust_gas_fraction, intake_state.temperature_k])
    p_max_prev_pa = cfg.p_max_prev_pa
    
    for _ in range(max(1, cfg.cycles)):
        results, state, current_p_max_pa = run_one_cycle(state, p_max_prev_pa)
        p_max_prev_pa = current_p_max_pa

    volume = np.array([geometry_at_theta(geom, tr).volume_m3 for tr in theta_rad])
    wi_j = float(trapezoid(results["pressure"] * np.gradient(volume, theta_rad), theta_rad))
    imep_pa = wi_j / geom.swept_volume_m3_per_cyl
    fmep_pa = cfg.models.friction_model.a_pa + cfg.models.friction_model.b_pa_per_mpa * (p_max_prev_pa * 1e-6) + cfg.models.friction_model.c_pa_per_rpm * cfg.rpm
    indicated_torque_nm = (imep_pa * geom.swept_volume_m3_per_cyl * geom.cylinders) / (4.0 * pi)
    brake_torque_nm = max(0.0, (imep_pa - fmep_pa) * geom.swept_volume_m3_per_cyl * geom.cylinders / (4.0 * pi))
    power_w = brake_torque_nm * omega
    
    dt = (cfg.step_deg * DEG2RAD) / max(1e-9, omega)
    
    metrics = {
        "peak_pressure_bar": np.max(results["pressure"]) / 1.0e5,
        "peak_temp_k": np.max(results["temp"]),
        "imep_bar": imep_pa / 1.0e5,
        "indicated_torque_nm": indicated_torque_nm,
        "brake_torque_nm_est": brake_torque_nm,
        "brake_power_kw_est": power_w / 1000.0,
        "mass_start_kg_per_cyl": results["mass"][0],
        "mass_end_kg_per_cyl": results["mass"][-1],
        "m_air_in_kg_per_cyl": np.sum(np.clip(results["mdot_in"], 0.0, None) * dt),
        "m_exhaust_out_kg_per_cyl": np.sum(np.clip(-results["mdot_ex"], 0.0, None) * dt),
        "p_intake_mean_bar": np.mean(results["p_intake"])/1e5,
        "t_intake_mean_k": np.mean(results["t_intake"]),
        "p_exhaust_mean_bar": np.mean(results["p_exhaust"])/1e5,
        "t_exhaust_mean_k": np.mean(results["t_exhaust"]),
        "fuel_energy_in_j_per_cyl": (m_fuel_total_kg * fuel.lhv_j_per_kg),
        "q_comb_j_per_cyl": float(trapezoid(results["dq_comb"] / DEG2RAD, theta_rad)),
        "q_wall_j_per_cyl": float(trapezoid(results["dq_wall"] / DEG2RAD, theta_rad)),
    }
    emissions = estimate_emissions(
        rpm=cfg.rpm,
        fuel_mg_per_cycle=cfg.fuel_mg_per_cycle_per_cyl,
        m_air_in_kg_per_cyl=metrics["m_air_in_kg_per_cyl"],
        peak_temp_k=metrics["peak_temp_k"],
        egt_k=float(np.max(results["t_exhaust"])),
        fuel=fuel,
        dual_fuel_lpg_frac=cfg.dual_fuel_lpg_frac,
    )
    metrics.update(emissions)

    return FullCycleResult(
        theta_deg=theta_deg,
        volume_m3=volume,
        pressure_pa=results["pressure"],
        temperature_k=results["temp"],
        mass_kg=results["mass"],
        p_intake_pa=results["p_intake"],
        t_intake_k=results["t_intake"],
        p_exhaust_pa=results["p_exhaust"],
        t_exhaust_k=results["t_exhaust"],
        mdot_intake_kg_s=results["mdot_in"],
        mdot_exhaust_kg_s=results["mdot_ex"],
        intake_lift_frac=results["lift_i"],
        exhaust_lift_frac=results["lift_e"],
        dq_comb_j_per_deg=results["dq_comb"],
        dq_wall_j_per_deg=results["dq_wall"],
        dm_fuel_main_mg_per_deg=results["dm_fuel_main_mg_per_deg"],
        torque_indicated_nm_per_cyl=results["torque"],
        metrics=metrics,
    )
