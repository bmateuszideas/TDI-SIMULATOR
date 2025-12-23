from __future__ import annotations

from typing import Any

import numpy as np

from .engine_model import Fuel


def estimate_lambda(m_air_in_kg: float, fuel_mg_per_cycle: float, fuel: Fuel) -> float:
    fuel_kg = max(0.0, float(fuel_mg_per_cycle)) * 1e-6
    if fuel_kg <= 0.0:
        return float("inf")
    return float(m_air_in_kg) / max(1e-12, fuel_kg * float(fuel.stoich_air_fuel))


def estimate_emissions(
    *,
    rpm: float,
    fuel_mg_per_cycle: float,
    m_air_in_kg_per_cyl: float,
    peak_temp_k: float,
    egt_k: float,
    fuel: Fuel,
    dual_fuel_lpg_frac: float = 0.0,
) -> dict[str, Any]:
    lambda_air = estimate_lambda(m_air_in_kg_per_cyl, fuel_mg_per_cycle, fuel)
    peak_k = max(1200.0, float(peak_temp_k))
    egt_k = max(300.0, float(egt_k))

    temp_factor = np.clip((peak_k - 1500.0) / 600.0, 0.0, 1.5)
    egt_factor = np.clip((egt_k - 650.0) / 350.0, 0.0, 1.5)
    lambda_factor = np.clip((lambda_air - 1.0) / 0.6, 0.0, 1.5)

    nox_ppm = 60.0 + 520.0 * (temp_factor**1.6) + 180.0 * (egt_factor**1.2)
    nox_ppm *= 0.7 + 0.6 * lambda_factor

    rich_factor = np.clip((1.3 - lambda_air) / 0.4, 0.0, 1.5)
    cool_factor = np.clip((2000.0 - peak_k) / 600.0, 0.0, 1.5)
    co_ppm = 120.0 + 900.0 * (rich_factor**1.2) + 400.0 * (cool_factor**1.2)

    dual = float(np.clip(dual_fuel_lpg_frac, 0.0, 0.6))
    if dual > 0.0:
        nox_red = np.interp(fuel_mg_per_cycle, [5.0, 20.0, 40.0], [0.0, 0.07, 0.24]) * (dual / 0.30)
        nox_ppm *= max(0.2, 1.0 - nox_red)
        co_mult = np.interp(fuel_mg_per_cycle, [5.0, 20.0, 40.0], [3.8, 6.8, 18.0])
        co_ppm *= 1.0 + (co_mult - 1.0) * (dual / 0.30)

    co2_pct = 2.5 + 5.0 * (1.4 / max(0.8, min(lambda_air, 2.5)))

    return {
        "lambda_est": float(lambda_air),
        "nox_ppm_est": float(np.clip(nox_ppm, 20.0, 3000.0)),
        "co_ppm_est": float(np.clip(co_ppm, 50.0, 20000.0)),
        "co2_pct_est": float(np.clip(co2_pct, 2.0, 12.0)),
        "dual_fuel_lpg_frac": float(dual),
        "rpm": float(rpm),
    }
