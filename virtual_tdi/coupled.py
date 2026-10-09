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


def simulate_coupled_turbo_map(
    geom: EngineGeometry,
    fuel: Fuel,
    schedule: InjectionSchedule,
    cfg_full: FullCycleConfig,
    turbo_cfg: TurboConfig,
    turbo_map: "TurboMapModel",
    iterations: int = 8,
) -> CoupledResult:
    """Turbo coupling using compressor/turbine maps (TODO.md Faza 2.A).

    Differences vs simulate_coupled_turbo (fixed efficiencies):
    - compressor/turbine efficiencies come from the map at (speed, PR/ER),
    - the balance solves for shaft speed: P_turbine(speed, ER) = P_comp(speed, PR),
    - exhaust backpressure feeds the turbine inlet (p_turbine_in = p_exhaust),
      so a higher boost also raises pumping work - the physical coupling the
      fixed-efficiency balance missed.
    """
    from .turbo_map import TurboMapModel  # noqa: F401  (type hint only)

    boundaries = cfg_full.boundaries
    p_intake = float(boundaries.intake_pressure_pa)
    shaft_rpm = 90000.0
    args_pr_max_holder = [max(1.05, turbo_cfg.pr_max)]
    history: list[dict[str, Any]] = []

    from .models import ManifoldConfig

    def build_cfg(p_in: float, p_exh: float) -> FullCycleConfig:
        intake_manifold = cfg_full.intake_manifold_config
        exhaust_manifold = cfg_full.exhaust_manifold_config
        if intake_manifold is not None:
            intake_manifold = ManifoldConfig(
                volume_m3=intake_manifold.volume_m3,
                initial_temp_k=intake_manifold.initial_temp_k,
                initial_pressure_pa=p_in,
                initial_egr_fraction=intake_manifold.initial_egr_fraction,
            )
        if exhaust_manifold is not None:
            exhaust_manifold = ManifoldConfig(
                volume_m3=exhaust_manifold.volume_m3,
                initial_temp_k=exhaust_manifold.initial_temp_k,
                initial_pressure_pa=p_exh,
                initial_egr_fraction=exhaust_manifold.initial_egr_fraction,
            )
        return FullCycleConfig(
            rpm=cfg_full.rpm,
            step_deg=cfg_full.step_deg,
            cycles=cfg_full.cycles,
            boundaries=BoundaryConditions(
                intake_pressure_pa=p_in,
                intake_temp_k=boundaries.intake_temp_k,
                exhaust_pressure_pa=p_exh,
                exhaust_temp_k=boundaries.exhaust_temp_k,
            ),
            intake_manifold_config=intake_manifold,
            exhaust_manifold_config=exhaust_manifold,
            valve_timing=cfg_full.valve_timing,
            valve_flow=cfg_full.valve_flow,
            valve_lift_table=cfg_full.valve_lift_table,
            cylinder=cfg_full.cylinder,
            tdc_offset_deg=cfg_full.tdc_offset_deg,
            vp37_cam_profile=cfg_full.vp37_cam_profile,
            vp37_iq_max_mg=cfg_full.vp37_iq_max_mg,
            vp37_delivery_start_frac=cfg_full.vp37_delivery_start_frac,
            fuel_mg_per_cycle_per_cyl=cfg_full.fuel_mg_per_cycle_per_cyl,
            injection_profile=cfg_full.injection_profile,
            reciprocating_mass_kg=cfg_full.reciprocating_mass_kg,
            models=cfg_full.models,
        )

    for i in range(max(1, int(iterations))):
        # Exhaust manifold pressure upstream of the turbine rises with boost
        # (physical coupling): a VNT at full load runs ER close to the boost PR
        # (closed vanes); engineering estimate, TODO.md Faza 2.A.
        pr_now = max(1.0, p_intake / turbo_cfg.p_amb_pa)
        p_exhaust = turbo_cfg.p_amb_pa * (1.0 + 1.5 * min(pr_now - 1.0, 1.2))
        res = simulate_full_cycle(geom, fuel, schedule, build_cfg(p_intake, p_exhaust))
        cycles_per_s = omega_rad_per_s(cfg_full.rpm) / (4.0 * 3.141592653589793)
        m_air_kg_s = float(res.metrics.get("m_air_in_kg_per_cyl", 0.0)) * cycles_per_s * geom.cylinders
        pr = max(1.0, p_intake / turbo_cfg.p_amb_pa)
        er = max(1.0, p_exhaust / turbo_cfg.p_amb_pa)
        t_exh = max(400.0, float(res.metrics.get("t_exhaust_mean_k", 800.0)))

        m_exhaust_kg_s = (float(res.metrics.get("m_exhaust_out_kg_per_cyl", 0.0))
                          * cycles_per_s * geom.cylinders
                          + m_air_kg_s * 0.0)  # exhaust already includes air+fuel out
        # Shaft speed from mass conservation: find the speed line whose
        # swallowed flow at the current PR matches the engine air flow.
        # (The compressor operates on its map; surge/choke are implicitly
        # handled by clipping in the interpolation.)
        shaft_new = shaft_rpm
        lo, hi = 20000.0, 260000.0
        for _ in range(24):
            mid = 0.5 * (lo + hi)
            m_map = turbo_map.compressor_mass_kg_s(mid, pr)
            if m_map > m_air_kg_s:
                hi = mid
            else:
                lo = mid
        shaft_new = 0.5 * (lo + hi)
        shaft_rpm = (1.0 - 0.3) * shaft_rpm + 0.3 * shaft_new

        p_comp_w = turbo_map.compressor_power_w(shaft_rpm, pr, m_air_kg_s,
                                                t_in_k=boundaries.intake_temp_k)
        p_turb_w = turbo_map.turbine_power_w(er, shaft_rpm, t_exh,
                                             p_out_pa=turbo_cfg.p_amb_pa,
                                             mdot_exhaust_kg_s=max(m_exhaust_kg_s, 0.002))
        # Boost direction: excess turbine power raises PR, deficit lowers it.
        # Steady state is where P_turb == P_comp at the mass-consistent speed.
        if p_comp_w > 1.0:
            excess = (p_turb_w - p_comp_w) / max(p_comp_w, 1.0)
            pr_target = pr * (1.0 + max(-0.15, min(0.15, 0.25 * excess)))
        else:
            pr_target = pr * 1.02
        pr_target = max(1.0, min(float(args_pr_max_holder[0]), pr_target))
        p_target = pr_target * turbo_cfg.p_amb_pa
        p_intake = (1.0 - turbo_cfg.relax) * p_intake + turbo_cfg.relax * p_target

        history.append({
            "iter": i,
            "p_intake_pa": p_intake,
            "p_exhaust_pa": p_exhaust,
            "pr_comp": pr,
            "er_turb": er,
            "shaft_rpm": shaft_rpm,
            "m_air_kg_s": m_air_kg_s,
            "power_comp_w": p_comp_w,
            "power_turb_w": p_turb_w,
        })

    pr_now = max(1.0, p_intake / turbo_cfg.p_amb_pa)
    p_exhaust = turbo_cfg.p_amb_pa * (1.0 + 1.5 * min(pr_now - 1.0, 1.2))
    final_res = simulate_full_cycle(geom, fuel, schedule, build_cfg(p_intake, p_exhaust))
    return CoupledResult(result=final_res, history=history)
