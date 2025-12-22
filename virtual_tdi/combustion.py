from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np

from .models import CombustionConfig, Fuel, InjectionSchedule, SimulationConfig
from .thermo import ignition_delay_seconds_arrhenius, omega_rad_per_s


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
