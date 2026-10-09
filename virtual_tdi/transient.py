from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Any

import numpy as np

from .full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle
from .models import EngineGeometry, Fuel, InjectionSchedule
from .thermo import omega_rad_per_s


RPM2RAD_S = 2.0 * np.pi / 60.0
RAD_S2RPM = 60.0 / (2.0 * np.pi)


@dataclass(frozen=True)
class GovernorConfig:
    """PI speed governor acting on fuel quantity (IQ)."""

    kp_mg_per_rpm: float = 0.10
    ki_mg_per_rpm_s: float = 0.06
    iq_min_mg: float = 0.0
    iq_max_mg: float = 55.0
    anti_windup: bool = True


@dataclass(frozen=True)
class TurboLagConfig:
    """First-order lag of intake manifold pressure behind its steady target."""

    tau_s: float = 0.8
    p_boost_target_bar_abs: float = 1.0


@dataclass(frozen=True)
class TransientConfig:
    """Mean-Value Engine Model (MVEM) transient simulation config."""

    t_start_s: float = 0.0
    t_end_s: float = 20.0
    dt_s: float = 0.05
    rpm_start: float = 900.0
    rpm_target: Callable[[float], float] | None = None
    load_torque_nm_fn: Callable[[float], float] | None = None
    inertia_kg_m2: float = 0.35
    governor: GovernorConfig = field(default_factory=GovernorConfig)
    turbo_lag: TurboLagConfig = field(default_factory=TurboLagConfig)
    p_intake_start_bar_abs: float = 1.0
    t_intake_k: float = 300.0
    p_exhaust_bar_abs: float = 1.15
    t_exhaust_k: float = 800.0
    cycles_per_point: int = 2
    fuel_mg_start: float = 5.0
    dq_drop_rate_s: float = 20.0


@dataclass
class TransientSample:
    t_s: float
    rpm: float
    load_torque_nm: float
    fuel_mg: float
    brake_torque_nm: float
    brake_power_kw: float
    p_intake_bar_abs: float
    iq_integral: float
    imep_bar: float
    peak_pressure_bar: float
    metrics: dict[str, Any]


@dataclass
class TransientResult:
    samples: list[TransientSample]
    cycle_history: list[dict[str, Any]]


def _make_full_cycle_cfg(
    *,
    cfg: TransientConfig,
    rpm: float,
    p_intake_bar_abs: float,
    fuel_mg: float,
    models: Any,
    valve_timing: Any,
    valve_flow: Any,
    valve_lift_table: Any,
    step_deg: float,
    cam: Any = None,
) -> FullCycleConfig:
    boundaries = BoundaryConditions(
        intake_pressure_pa=p_intake_bar_abs * 1.0e5,
        intake_temp_k=cfg.t_intake_k,
        exhaust_pressure_pa=cfg.p_exhaust_bar_abs * 1.0e5,
        exhaust_temp_k=cfg.t_exhaust_k,
    )
    return FullCycleConfig(
        rpm=rpm,
        step_deg=step_deg,
        cycles=cfg.cycles_per_point,
        fuel_mg_per_cycle_per_cyl=fuel_mg,
        boundaries=boundaries,
        valve_timing=valve_timing,
        valve_flow=valve_flow,
        valve_lift_table=valve_lift_table,
        cylinder=1,
        vp37_cam_profile=cam,
        models=models,
    )


def run_transient(
    geom: EngineGeometry,
    fuel: Fuel,
    schedule_builder: Callable[[float], InjectionSchedule],
    cfg: TransientConfig,
    *,
    models: Any,
    valve_timing: Any,
    valve_flow: Any,
    valve_lift_table: Any = None,
    step_deg: float = 0.5,
    cam: Any = None,
    progress: Callable[[int, int], None] | None = None,
) -> TransientResult:
    """Run a time-based MVEM transient.

    At each time step:
    1. Governor computes IQ from rpm error (PI with anti-windup).
    2. Full 720-degree cycle is simulated at current rpm/IQ/intake pressure.
    3. Shaft speed integrates brake torque minus load torque.
    4. Intake pressure follows a first-order turbo lag toward the boost target.
    """
    n_steps = int(round((cfg.t_end_s - cfg.t_start_s) / cfg.dt_s)) + 1
    rpm = float(cfg.rpm_start)
    iq = float(cfg.fuel_mg_start)
    iq_integral = 0.0
    iq_prev = iq
    p_intake_bar = float(cfg.p_intake_start_bar_abs)
    samples: list[TransientSample] = []
    cycle_history: list[dict[str, Any]] = []

    gov = cfg.governor
    load_fn = cfg.load_torque_nm_fn if cfg.load_torque_nm_fn is not None else (lambda t: 0.0)
    rpm_target_fn = cfg.rpm_target if cfg.rpm_target is not None else (lambda t: cfg.rpm_start)

    for k in range(n_steps):
        t = cfg.t_start_s + k * cfg.dt_s
        rpm_target = float(rpm_target_fn(t))
        err = rpm_target - rpm
        iq_integral += err * cfg.dt_s
        iq_p = gov.kp_mg_per_rpm * err
        iq_i = gov.ki_mg_per_rpm_s * iq_integral
        iq_raw = iq_p + iq_i
        if gov.anti_windup:
            if iq_raw > gov.iq_max_mg and err > 0.0:
                iq_integral -= err * cfg.dt_s
                iq_raw = gov.iq_max_mg
            elif iq_raw < gov.iq_min_mg and err < 0.0:
                iq_integral -= err * cfg.dt_s
                iq_raw = gov.iq_min_mg
        iq = float(np.clip(iq_raw, gov.iq_min_mg, gov.iq_max_mg))
        # Slew-rate limit on fuel quantity change [mg/s] to avoid bang-bang actuation.
        if cfg.dq_drop_rate_s > 0.0:
            max_delta = cfg.dq_drop_rate_s * cfg.dt_s
            iq = float(np.clip(iq, iq_prev - max_delta, iq_prev + max_delta))
            iq = float(np.clip(iq, gov.iq_min_mg, gov.iq_max_mg))

        rpm_cycle = max(100.0, rpm)
        models_at_rpm = replace(models, rpm=rpm_cycle)
        schedule = schedule_builder(iq)
        full_cfg = _make_full_cycle_cfg(
            cfg=cfg,
            rpm=rpm_cycle,
            models=models_at_rpm,
            p_intake_bar_abs=p_intake_bar,
            fuel_mg=iq,
            valve_timing=valve_timing,
            valve_flow=valve_flow,
            valve_lift_table=valve_lift_table,
            step_deg=step_deg,
            cam=cam,
        )
        res = simulate_full_cycle(geom, fuel, schedule, full_cfg)
        brake_torque_nm = float(res.metrics.get("brake_torque_nm_est", 0.0))
        load_torque_nm = float(load_fn(t))

        omega = rpm * RPM2RAD_S
        domega = (brake_torque_nm - load_torque_nm) / max(1e-9, cfg.inertia_kg_m2)
        rpm_next = rpm + domega * RAD_S2RPM * cfg.dt_s
        rpm_next = max(0.0, rpm_next)

        # Turbo lag: intake pressure moves toward boost target with time constant tau.
        p_target_bar = float(cfg.turbo_lag.p_boost_target_bar_abs)
        p_intake_bar = p_intake_bar + (cfg.dt_s / max(1e-9, cfg.turbo_lag.tau_s)) * (p_target_bar - p_intake_bar)

        samples.append(
            TransientSample(
                t_s=t,
                rpm=rpm,
                load_torque_nm=load_torque_nm,
                fuel_mg=iq,
                brake_torque_nm=brake_torque_nm,
                brake_power_kw=brake_torque_nm * omega / 1000.0,
                p_intake_bar_abs=p_intake_bar,
                iq_integral=iq_integral,
                imep_bar=float(res.metrics.get("imep_bar", 0.0)),
                peak_pressure_bar=float(res.metrics.get("peak_pressure_pa", 0.0)) / 1.0e5,
                metrics=res.metrics,
            )
        )
        cycle_history.append(
            {
                "t_s": t,
                "rpm": rpm,
                "fuel_mg": iq,
                "p_intake_bar": p_intake_bar,
                "brake_torque_nm": brake_torque_nm,
                "load_torque_nm": load_torque_nm,
            }
        )
        if progress is not None:
            progress(k + 1, n_steps)
        rpm = rpm_next
        iq_prev = iq

    return TransientResult(samples=samples, cycle_history=cycle_history)

