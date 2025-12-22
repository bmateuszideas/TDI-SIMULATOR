from __future__ import annotations

from dataclasses import dataclass, field
from math import pi
from typing import Any

import numpy as np

trapezoid = getattr(np, "trapezoid", np.trapz)

from .combustion import (
    CombustionScheduleRuntime,
    heat_release_rate_dq_dtheta,
    heat_release_rate_from_shaped_fuel,
    heat_release_rate_wiebe_single,
    maybe_arm_combustion,
)
from .flow import orifice_mdot_kg_per_s
from .geometry import geometry_at_theta
from .heat_transfer import h_woschni_simplified_w_per_m2_k, calculate_wall_heat_loss_j_per_rad
from .models import EngineGeometry, Fuel, SimulationConfig, ManifoldConfig, ManifoldState
from .thermo import GasModel, omega_rad_per_s
from .valvetrain import ValveFlow, ValveTiming, effective_curtain_area_m2, valve_lift_fraction
from .lift_table import ValveLiftTable
from .vp37_cam import VP37CamProfile


DEG2RAD = pi / 180.0


@dataclass(frozen=True)
class BoundaryConditions:
    intake_pressure_pa: float = 1.0e5
    intake_temp_k: float = 300.0
    exhaust_pressure_pa: float = 1.1e5
    exhaust_temp_k: float = 800.0


@dataclass(frozen=True)
class FullCycleConfig:
    rpm: float
    step_deg: float = 0.1
    cycles: int = 3
    theta_start_deg: float = -360.0
    theta_end_deg: float = 360.0
    fuel_mg_per_cycle_per_cyl: float = 20.0
    boundaries: BoundaryConditions | None = None
    intake_manifold_config: ManifoldConfig | None = None
    exhaust_manifold_config: ManifoldConfig | None = None
    p_ambient_pa: float = 1.0e5
    t_ambient_k: float = 300.0
    manifold_throttle_coeff: float = 1e-4
    valve_timing: ValveTiming = field(default_factory=ValveTiming)
    valve_flow: ValveFlow = field(default_factory=ValveFlow)
    valve_lift_table: ValveLiftTable | None = None
    cylinder: int = 1
    tdc_offset_deg: dict[int, float] = None
    vp37_cam_profile: VP37CamProfile | None = None
    vp37_iq_max_mg: float = 51.0
    vp37_delivery_start_frac: float = 0.40
    reciprocating_mass_kg: float = 0.73
    injection_profile: tuple[np.ndarray, np.ndarray] | None = None
    models: SimulationConfig = field(default_factory=lambda: SimulationConfig(rpm=1500.0))
    m_min_kg: float = 1.0e-7
    t_min_k: float = 200.0
    t_max_k: float = 4500.0

    def __post_init__(self) -> None:
        boundaries = self.boundaries
        if boundaries is None:
            boundaries = BoundaryConditions(
                intake_pressure_pa=self.p_ambient_pa,
                intake_temp_k=self.t_ambient_k,
                exhaust_pressure_pa=self.p_ambient_pa,
                exhaust_temp_k=self.t_ambient_k,
            )
            object.__setattr__(self, "boundaries", boundaries)

        if self.intake_manifold_config is None:
            object.__setattr__(
                self,
                "intake_manifold_config",
                ManifoldConfig(
                    volume_m3=2e-3,
                    initial_temp_k=boundaries.intake_temp_k,
                    initial_pressure_pa=boundaries.intake_pressure_pa,
                ),
            )

        if self.exhaust_manifold_config is None:
            object.__setattr__(
                self,
                "exhaust_manifold_config",
                ManifoldConfig(
                    volume_m3=1.5e-3,
                    initial_temp_k=boundaries.exhaust_temp_k,
                    initial_pressure_pa=boundaries.exhaust_pressure_pa,
                ),
            )

        if self.p_ambient_pa == 1.0e5 and self.t_ambient_k == 300.0:
            object.__setattr__(self, "p_ambient_pa", boundaries.intake_pressure_pa)
            object.__setattr__(self, "t_ambient_k", boundaries.intake_temp_k)

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

    geom0 = geometry_at_theta(geom, theta_rad[0])
    rho0 = gas.density_from_pT(
        cfg.intake_manifold_config.initial_pressure_pa,
        intake_state.temperature_k,
        cfg.models,
    )
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

    def run_one_cycle(init_state: np.ndarray):
        results = {k: np.zeros_like(theta_rad) for k in ["pressure", "temp", "mass", "p_intake", "t_intake", "p_exhaust", "t_exhaust", "mdot_in", "mdot_ex", "lift_i", "lift_e", "dq_comb", "dq_wall", "torque", "dm_fuel_main_mg_per_deg"]}
        state, runtime = init_state.copy(), CombustionScheduleRuntime()
        
        for i, (theta_d, theta_r) in enumerate(zip(theta_deg, theta_rad)):
            m_c, t_c, m_i, t_i, m_e, t_e = state
            
            geo = geometry_at_theta(geom, theta_r)
            rho_c = m_c / max(1e-12, geo.volume_m3)
            p_c = max(1.0, gas.pressure_from_rhoT(rho_c, t_c, cfg.models))
            p_i = gas.pressure_from_rhoT(m_i / cfg.intake_manifold_config.volume_m3, t_i, cfg.models)
            p_e = gas.pressure_from_rhoT(m_e / cfg.exhaust_manifold_config.volume_m3, t_e, cfg.models)

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

            state_derivs, mdot_in, mdot_ex, dq_comb, dq_wall = _deriv_func(theta_r, state, runtime)
            results["mdot_in"][i], results["mdot_ex"][i] = mdot_in, mdot_ex
            results["dq_comb"][i], results["dq_wall"][i] = dq_comb * DEG2RAD, dq_wall * DEG2RAD
            results["torque"][i] = p_c * geo.dvol_dtheta_m3_per_rad

            if i < len(theta_rad) - 1:
                state = _rk4_step(
                    theta_r,
                    state,
                    step_rad=step_rad,
                    deriv=lambda t, s: _deriv_func(t, s, runtime)[0],
                )
                state[1::2] = np.clip(state[1::2], cfg.t_min_k, cfg.t_max_k) # Clip temperatures

        return results, state

    def _deriv_func(theta_r, state_vec, rt):
        m_c, t_c, m_i, t_i, m_e, t_e = state_vec
        geo = geometry_at_theta(geom, theta_r)
        
        rho_c = m_c / max(1e-12, geo.volume_m3)
        p_c = max(1.0, gas.pressure_from_rhoT(rho_c, t_c, cfg.models))
        p_i = gas.pressure_from_rhoT(m_i / cfg.intake_manifold_config.volume_m3, t_i, cfg.models)
        p_e = gas.pressure_from_rhoT(m_e / cfg.exhaust_manifold_config.volume_m3, t_e, cfg.models)
        
        g_c = gas.gamma(t_c, cfg.models, pressure_pa=p_c)
        cp_c = gas.cp(t_c, cfg.models, pressure_pa=p_c)
        cv_c = gas.cv(t_c, cfg.models, pressure_pa=p_c)
        g_i = gas.gamma(t_i, cfg.models, pressure_pa=p_i)
        cp_i = gas.cp(t_i, cfg.models, pressure_pa=p_i)
        cv_i = gas.cv(t_i, cfg.models, pressure_pa=p_i)
        g_e = gas.gamma(t_e, cfg.models, pressure_pa=p_e)
        cp_e = gas.cp(t_e, cfg.models, pressure_pa=p_e)
        cv_e = gas.cv(t_e, cfg.models, pressure_pa=p_e)
        g_amb = gas.gamma(cfg.t_ambient_k, cfg.models, pressure_pa=cfg.p_ambient_pa)
        cp_amb = gas.cp(cfg.t_ambient_k, cfg.models, pressure_pa=cfg.p_ambient_pa)

        li_m, le_m = lift_m(theta_r / DEG2RAD, "intake"), lift_m(theta_r / DEG2RAD, "exhaust")
        a_i, a_e = effective_curtain_area_m2(cfg.valve_flow.intake_valve_diameter_m, li_m), effective_curtain_area_m2(cfg.valve_flow.exhaust_valve_diameter_m, le_m)
        
        if p_i > p_c:
            mdot_i_c = orifice_mdot_kg_per_s(
                p_up_pa=p_i,
                t_up_k=t_i,
                p_down_pa=p_c,
                gamma=g_i,
                r_j_per_kg_k=gas.r_j_per_kg_k,
                area_m2=a_i,
                discharge_coeff=cfg.valve_flow.cd_intake,
                backend=cfg.models.flow_backend,
            )
        else:
            mdot_i_c = -orifice_mdot_kg_per_s(
                p_up_pa=p_c,
                t_up_k=t_c,
                p_down_pa=p_i,
                gamma=g_c,
                r_j_per_kg_k=gas.r_j_per_kg_k,
                area_m2=a_i,
                discharge_coeff=cfg.valve_flow.cd_intake,
                backend=cfg.models.flow_backend,
            )

        if p_c > p_e:
            mdot_c_e = orifice_mdot_kg_per_s(
                p_up_pa=p_c,
                t_up_k=t_c,
                p_down_pa=p_e,
                gamma=g_c,
                r_j_per_kg_k=gas.r_j_per_kg_k,
                area_m2=a_e,
                discharge_coeff=cfg.valve_flow.cd_exhaust,
                backend=cfg.models.flow_backend,
            )
        else:
            mdot_c_e = -orifice_mdot_kg_per_s(
                p_up_pa=p_e,
                t_up_k=t_e,
                p_down_pa=p_c,
                gamma=g_e,
                r_j_per_kg_k=gas.r_j_per_kg_k,
                area_m2=a_e,
                discharge_coeff=cfg.valve_flow.cd_exhaust,
                backend=cfg.models.flow_backend,
            )

        mdot_amb_i = (
            orifice_mdot_kg_per_s(
                p_up_pa=cfg.p_ambient_pa,
                t_up_k=cfg.t_ambient_k,
                p_down_pa=p_i,
                gamma=g_amb,
                r_j_per_kg_k=gas.r_j_per_kg_k,
                area_m2=cfg.manifold_throttle_coeff,
                discharge_coeff=0.8,
            )
            if cfg.p_ambient_pa > p_i
            else 0.0
        )
        mdot_e_amb = (
            orifice_mdot_kg_per_s(
                p_up_pa=p_e,
                t_up_k=t_e,
                p_down_pa=cfg.p_ambient_pa,
                gamma=g_e,
                r_j_per_kg_k=gas.r_j_per_kg_k,
                area_m2=cfg.manifold_throttle_coeff,
                discharge_coeff=0.8,
            )
            if p_e > cfg.p_ambient_pa
            else 0.0
        )
        
        dm_cyl_dtheta, dm_intake_dtheta, dm_exhaust_dtheta = (mdot_i_c - mdot_c_e)/omega, (mdot_amb_i - mdot_i_c)/omega, (mdot_c_e - mdot_e_amb)/omega
        
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
        
        h_amb_i = cp_amb * cfg.t_ambient_k
        h_i_c = cp_i * t_i
        dT_intake_dtheta = ((mdot_amb_i*h_amb_i - mdot_i_c*h_i_c)/omega - cv_i*t_i*dm_intake_dtheta) / max(cfg.m_min_kg*cv_i, m_i*cv_i)
        
        h_c_e = cp_c * t_c
        h_e_amb = cp_e * t_e
        dT_exhaust_dtheta = ((mdot_c_e*h_c_e - mdot_e_amb*h_e_amb)/omega - cv_e*t_e*dm_exhaust_dtheta) / max(cfg.m_min_kg*cv_e, m_e*cv_e)
        
        state_derivs = np.array(
            [
                dm_cyl_dtheta,
                dT_cyl_dtheta,
                dm_intake_dtheta,
                dT_intake_dtheta,
                dm_exhaust_dtheta,
                dT_exhaust_dtheta,
            ]
        )
        return state_derivs, mdot_i_c, -mdot_c_e, dq_c, dq_w

    state = np.array([m0_cyl, t0_cyl, intake_state.mass_kg, intake_state.temperature_k, exhaust_state.mass_kg, exhaust_state.temperature_k])
    
    for _ in range(max(1, cfg.cycles)):
        results, state = run_one_cycle(state)

    volume = np.array([geometry_at_theta(geom, tr).volume_m3 for tr in theta_rad])
    wi_j = float(trapezoid(results["pressure"] * np.gradient(volume, theta_rad), theta_rad))
    imep_pa = wi_j / geom.swept_volume_m3_per_cyl
    indicated_torque_nm = (imep_pa * geom.swept_volume_m3_per_cyl * geom.cylinders) / (4.0 * pi)
    brake_torque_nm = max(0.0, (imep_pa - cfg.models.fmep_pa) * geom.swept_volume_m3_per_cyl * geom.cylinders / (4.0 * pi))
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
