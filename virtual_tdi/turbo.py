from __future__ import annotations

from dataclasses import dataclass
from math import pow
from typing import Optional

from .engine_model import CompressorMap, VntMap


@dataclass(frozen=True)
class TurboConfig:
    eta_turbine: float = 0.70
    eta_comp: float = 0.70
    eta_mech: float = 0.95
    pr_min: float = 1.0
    pr_max: float = 2.4
    p_amb_pa: float = 1.0e5
    t_amb_k: float = 300.0
    gamma: float = 1.35
    cp_j_per_kg_k: float = 1005.0
    relax: float = 0.5
    vnt_angle_deg: float = 0.0
    compressor_map: CompressorMap | None = None
    vnt_map: VntMap | None = None


def get_compressor_efficiency(
    mass_flow_kg_s: float,
    pressure_ratio: float,
    cfg: TurboConfig,
) -> float:
    if cfg.compressor_map is not None:
        # Clamp inputs to reasonable ranges for interpolation
        mass_flow_kg_s = max(0.01, mass_flow_kg_s) # Example clamp, adjust as needed
        pressure_ratio = max(cfg.pr_min, pressure_ratio)
        return float(cfg.compressor_map.get_efficiency(mass_flow_kg_s, pressure_ratio))
    return cfg.eta_comp # Fallback to fixed efficiency


def get_compressor_turbo_rpm(
    mass_flow_kg_s: float,
    pressure_ratio: float,
    cfg: TurboConfig,
) -> float:
    if cfg.compressor_map is not None:
        # Clamp inputs to reasonable ranges for interpolation
        mass_flow_kg_s = max(0.01, mass_flow_kg_s) # Example clamp, adjust as needed
        pressure_ratio = max(cfg.pr_min, pressure_ratio)
        return float(cfg.compressor_map.get_turbo_rpm(mass_flow_kg_s, pressure_ratio))
    return 0.0 # No fallback RPM if no map, or use a default such as engine RPM * ratio


def get_vnt_effective_area(
    vnt_angle_deg: float,
    cfg: TurboConfig,
) -> float:
    if cfg.vnt_map is not None:
        return cfg.vnt_map.get_effective_area(vnt_angle_deg)
    return 1.0e-4 # Default effective area if no VNT map is provided (example value)


def compressor_pr_from_power(
    *,
    m_air_kg_s: float,
    t_in_k: float,
    power_turb_w: float,
    cfg: TurboConfig,
) -> float:
    if m_air_kg_s <= 1e-9 or power_turb_w <= 0.0:
        return cfg.pr_min

    power_shaft = power_turb_w * cfg.eta_turbine * cfg.eta_mech
    t_in = max(1.0, t_in_k)
    cp = max(1.0, cfg.cp_j_per_kg_k)
    g = max(1.1, cfg.gamma)
    # power_comp = m_air * cp * T_in / eta_c * (PR^((g-1)/g) - 1)
    term = (power_shaft * cfg.eta_comp) / max(1e-9, m_air_kg_s * cp * t_in)
    pr = pow(1.0 + max(0.0, term), g / (g - 1.0))
    return max(cfg.pr_min, min(cfg.pr_max, pr))


from dataclasses import dataclass
from typing import Any

from .engine_model import BoundaryConditions, FullCycleConfig, FullCycleResult, simulate_full_cycle
from .engine_model import EngineGeometry, Fuel, InjectionSchedule
from .physics import omega_rad_per_s


@dataclass(frozen=True)
class CoupledResult:
    result: FullCycleResult
    history: list[dict[str, Any]]


def simulate_coupled_turbo(
    geom: EngineGeometry,
    fuel: Fuel,
    schedule: InjectionSchedule,
    cfg_full: FullCycleConfig,
    turbo_cfg: TurboConfig,
    iterations: int = 5,
) -> CoupledResult:
    """Iterate cycles to converge intake pressure from turbo power balance."""
    boundaries = cfg_full.boundaries
    p_intake = float(boundaries.intake_pressure_pa)
    history: list[dict[str, Any]] = []

    for i in range(max(1, int(iterations))):
        step_cfg = FullCycleConfig(
            rpm=cfg_full.rpm,
            step_deg=cfg_full.step_deg,
            cycles=cfg_full.cycles,
            boundaries=BoundaryConditions(
                intake_pressure_pa=p_intake,
                intake_temp_k=boundaries.intake_temp_k,
                exhaust_pressure_pa=boundaries.exhaust_pressure_pa,
                exhaust_temp_k=boundaries.exhaust_temp_k,
            ),
            valve_timing=cfg_full.valve_timing,
            valve_flow=cfg_full.valve_flow,
            valve_lift_table=cfg_full.valve_lift_table,
            cylinder=cfg_full.cylinder,
            tdc_offset_deg=cfg_full.tdc_offset_deg,
            vp37_cam_profile=cfg_full.vp37_cam_profile,
            vp37_iq_max_mg=cfg_full.vp37_iq_max_mg,
            vp37_delivery_start_frac=cfg_full.vp37_delivery_start_frac,
            reciprocating_mass_kg=cfg_full.reciprocating_mass_kg,
            models=cfg_full.models,
        )

        res = simulate_full_cycle(geom, fuel, schedule, step_cfg)

        # Compute air mass flow rate from per-cycle intake mass.
        cycles_per_s = omega_rad_per_s(cfg_full.rpm) / (4.0 * 3.141592653589793)
        m_air_kg_s = float(res.metrics.get("m_air_in_kg_per_cyl", 0.0)) * cycles_per_s * geom.cylinders
        power_exh_w = float(res.metrics.get("exhaust_power_kw_est", 0.0)) * 1000.0
        pr = compressor_pr_from_power(
            m_air_kg_s=m_air_kg_s,
            t_in_k=boundaries.intake_temp_k,
            power_turb_w=power_exh_w,
            cfg=turbo_cfg,
        )

        p_target = pr * turbo_cfg.p_amb_pa
        p_intake = (1.0 - turbo_cfg.relax) * p_intake + turbo_cfg.relax * p_target

        history.append(
            {
                "iter": i,
                "p_intake_pa": p_intake,
                "pr_comp": pr,
                "m_air_kg_s": m_air_kg_s,
                "power_exhaust_w": power_exh_w,
            }
        )

    # Recompute once at converged p_intake for final result
    final_cfg = FullCycleConfig(
        rpm=cfg_full.rpm,
        step_deg=cfg_full.step_deg,
        cycles=cfg_full.cycles,
        boundaries=BoundaryConditions(
            intake_pressure_pa=p_intake,
            intake_temp_k=boundaries.intake_temp_k,
            exhaust_pressure_pa=boundaries.exhaust_pressure_pa,
            exhaust_temp_k=boundaries.exhaust_temp_k,
        ),
        valve_timing=cfg_full.valve_timing,
        valve_flow=cfg_full.valve_flow,
        valve_lift_table=cfg_full.valve_lift_table,
        cylinder=cfg_full.cylinder,
        tdc_offset_deg=cfg_full.tdc_offset_deg,
        vp37_cam_profile=cfg_full.vp37_cam_profile,
        vp37_iq_max_mg=cfg_full.vp37_iq_max_mg,
        vp37_delivery_start_frac=cfg_full.vp37_delivery_start_frac,
        reciprocating_mass_kg=cfg_full.reciprocating_mass_kg,
        models=cfg_full.models,
    )
    final_res = simulate_full_cycle(geom, fuel, schedule, final_cfg)
    return CoupledResult(result=final_res, history=history)
