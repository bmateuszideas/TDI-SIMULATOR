from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .full_cycle import BoundaryConditions, FullCycleConfig, FullCycleResult, simulate_full_cycle
from .models import EngineGeometry, Fuel, InjectionSchedule
from .thermo import omega_rad_per_s
from .turbo import TurboConfig, compressor_pr_from_power


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
