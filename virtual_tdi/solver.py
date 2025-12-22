from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any

import numpy as np

trapezoid = getattr(np, "trapezoid", np.trapz)

from .combustion import CombustionScheduleRuntime, heat_release_rate_dq_dtheta, maybe_arm_combustion
from .geometry import geometry_at_theta
from .heat_transfer import h_woschni_simplified_w_per_m2_k
from .models import EngineGeometry, Fuel, InjectionSchedule, SimulationConfig
from .thermo import GasModel, omega_rad_per_s


DEG2RAD = pi / 180.0


def _mean_wall_temp_k(cfg: SimulationConfig) -> float:
    ht = cfg.heat_transfer
    return (ht.head_temp_k + ht.piston_temp_k + ht.liner_temp_k) / 3.0


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
        qdot_wall_w = h * geom_res.heat_transfer_area_m2 * (T - _mean_wall_temp_k(cfg))
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
        qdot_wall_w = h * geom_res.heat_transfer_area_m2 * (temperature[i] - _mean_wall_temp_k(cfg))
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
        "peak_pressure_pa": float(np.max(pressure)),
        "peak_temp_k": float(np.max(temperature)),
        "wi_j_per_cyl": wi_j,
        "imep_pa": imep_pa,
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
        qdot_wall_w = h * geo.heat_transfer_area_m2 * (T - _mean_wall_temp_k(cfg))
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
        qdot_wall_w = h * geo.heat_transfer_area_m2 * (float(T_grid[i]) - _mean_wall_temp_k(cfg))
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
        "peak_pressure_pa": float(np.max(pressure)),
        "peak_temp_k": float(np.max(T_grid)),
        "wi_j_per_cyl": wi_j,
        "imep_pa": imep_pa,
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
