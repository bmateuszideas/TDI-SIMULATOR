"""Map-driven validation grid (TODO.md: walidacja na obszarze roboczym ECU).

Points are generated from the factory ECU maps themselves:
- RPM x IQ grid sampled inside the maps' working area,
- for each point the ECU maps give SOI, boost target and (via SmokeLimiter)
  the max IQ; the simulator runs the full cycle with ECU settings and the
  resulting intake pressure / air mass are compared against the factory
  BOOST map and the MAF axis conventions (docs/MAPY_ECU_KONWENCJE.md).

This validates gas exchange + turbo coupling across the whole ECU operating
area using factory data instead of a handful of literature points.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from virtual_tdi.edc_maps import BoostTargetMap2D, SmokeLimiterMap2D
from virtual_tdi.soi_map import SOIMap2D

ROOT_LIKE = "."


@dataclass(frozen=True)
class MapGridPoint:
    rpm: float
    iq_mg: float
    soi_model_deg: float          # model convention (negative = BTDC)
    boost_target_mbar_abs: float  # from factory BOOST map
    smoke_iq_max_mg: float        # from factory SmokeLimiter at full airflow


def build_grid(
    *,
    soi_map: SOIMap2D,
    boost_map: BoostTargetMap2D,
    smoke_map: SmokeLimiterMap2D,
    n_rpm: int = 4,
    n_iq: int = 3,
) -> list[MapGridPoint]:
    """Sample a grid inside the maps' common working area."""
    rpm_lo = max(900.0, float(np.min(soi_map.rpm_axis)), float(np.min(boost_map.rpm_axis)))
    rpm_hi = min(4500.0, float(np.max(soi_map.rpm_axis)), float(np.max(boost_map.rpm_axis)))
    rpm_vals = np.linspace(rpm_lo, rpm_hi, n_rpm)
    points: list[MapGridPoint] = []
    for rpm in rpm_vals:
        # IQ column from the smoke limiter's full-airflow limit at this rpm
        # (850 mg/stroke = EGR closed, full charge) -> max physical dose.
        smoke_max = float(smoke_map.iq_max(float(rpm), 850.0))
        iq_vals = [smoke_max * f for f in (0.4, 0.7, 1.0)][:n_iq]
        for iq in iq_vals:
            iq = min(iq, 36.5)
            soi = soi_map.soi_deg_model_convention(float(rpm), float(iq))
            boost = boost_map.map_target_mbar(float(rpm), float(iq))
            points.append(MapGridPoint(
                rpm=float(rpm), iq_mg=float(iq),
                soi_model_deg=float(soi),
                boost_target_mbar_abs=float(boost),
                smoke_iq_max_mg=smoke_max,
            ))
    return points
