from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from .models import Fuel, InjectionSchedule
from .thermo import omega_rad_per_s


@dataclass(frozen=True)
class VP37LineModel:
    # Very simplified: hydraulic delay = line_length / c, where c = sqrt(K/rho).
    line_length_m: float = 0.40


def apply_hydraulic_delay(schedule: InjectionSchedule, *, fuel: Fuel, rpm: float, model: VP37LineModel) -> InjectionSchedule:
    if model.line_length_m <= 0.0:
        return schedule
    c = sqrt(max(1.0, fuel.bulk_modulus_pa) / max(1e-9, fuel.density_kg_per_m3))
    tau_s = model.line_length_m / max(1e-9, c)
    delay_deg = (omega_rad_per_s(rpm) * tau_s) * (180.0 / 3.141592653589793)
    return InjectionSchedule(
        soi_pilot_deg=schedule.soi_pilot_deg + delay_deg,
        soi_main_deg=schedule.soi_main_deg + delay_deg,
        pilot_fraction=schedule.pilot_fraction,
        duration_pilot_deg=schedule.duration_pilot_deg,
        duration_main_deg=schedule.duration_main_deg,
        wiebe_m_pilot=schedule.wiebe_m_pilot,
        wiebe_m_main=schedule.wiebe_m_main,
    )

