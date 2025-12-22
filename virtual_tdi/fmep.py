from __future__ import annotations

from .models import SimulationConfig


def calculate_fmep_pa(
    *,
    rpm: float,
    pmax_pa: float,
    a_bar: float,
    b_bar_per_krpm: float,
    c_bar_per_bar: float,
) -> float:
    """Estimate friction mean effective pressure (FMEP) in Pa.

    Model: FMEP_bar = A + B * (rpm / 1000) + C * Pmax_bar
    """
    rpm_krpm = rpm / 1000.0
    pmax_bar = pmax_pa / 1.0e5
    fmep_bar = a_bar + b_bar_per_krpm * rpm_krpm + c_bar_per_bar * pmax_bar
    return max(0.0, fmep_bar) * 1.0e5


def calculate_fmep_from_config(cfg: SimulationConfig, pmax_pa: float) -> float:
    return calculate_fmep_pa(
        rpm=cfg.rpm,
        pmax_pa=pmax_pa,
        a_bar=cfg.fmep_a_bar,
        b_bar_per_krpm=cfg.fmep_b_bar_per_krpm,
        c_bar_per_bar=cfg.fmep_c_bar_per_bar,
    )
