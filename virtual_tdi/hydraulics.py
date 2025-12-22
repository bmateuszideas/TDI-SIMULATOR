from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

from .models import Fuel
from .vp37_cam import VP37CamProfile


@dataclass(frozen=True)
class NozzleConfig:
    diameter_mm: float = 0.184
    holes: int = 5
    discharge_coeff: float = 0.72
    pilot_open_bar: float = 190.0
    main_open_bar: float = 300.0
    pilot_area_frac: float = 0.30

    @property
    def area_m2(self) -> float:
        d = self.diameter_mm * 1e-3
        return (pi * (d**2) / 4.0) * self.holes


@dataclass(frozen=True)
class NeedleConfig:
    """Properties of the injector needle for dynamic simulation."""
    mass_kg: float = 0.005  # 5 grams
    seat_area_mm2: float = 0.5
    spring_k_n_per_m: float = 50000.0  # 50 N/mm
    damping_coeff_ns_per_m: float = 10.0
    max_lift_mm: float = 0.3

    @property
    def seat_area_m2(self) -> float:
        return self.seat_area_mm2 * 1e-6
    
    @property
    def max_lift_m(self) -> float:
        return self.max_lift_mm * 1e-3


@dataclass(frozen=True)
class VP37HydraulicConfig:
    plunger_diameter_mm: float = 10.0
    chamber_volume_mm3: float = 200.0
    line_volume_mm3: float = 400.0
    back_pressure_bar: float = 50.0

    @property
    def plunger_area_m2(self) -> float:
        d = self.plunger_diameter_mm * 1e-3
        return pi * (d**2) / 4.0

    @property
    def volume_eff_m3(self) -> float:
        return (self.chamber_volume_mm3 + self.line_volume_mm3) * 1e-9


def estimate_pilot_ratio(
    cam: VP37CamProfile,
    *,
    rpm: float,
    duration_main_deg: float,
    fuel: Fuel,
    nozzle: NozzleConfig,
    hyd: VP37HydraulicConfig,
    cylinder: int = 1,
) -> float:
    """Estimate pilot mass fraction from pressure trace in a simplified VP37 line model."""
    if duration_main_deg <= 0.0:
        return 0.0

    a_deg, s_mm = cam._rising_segment(cam._lobe_index_for_cylinder(cylinder))
    if a_deg.size < 2:
        return 0.0

    dur_pump_deg = max(0.0, duration_main_deg / 2.0)
    a_start = float(a_deg[0])
    a_end = min(float(a_deg[-1]), a_start + dur_pump_deg)
    if a_end <= a_start:
        return 0.0

    # Slice to injection window
    mask = (a_deg >= a_start) & (a_deg <= a_end)
    a_deg = a_deg[mask]
    s_mm = s_mm[mask]
    if a_deg.size < 2:
        return 0.0

    omega_pump = (rpm / 2.0) * 2.0 * pi / 60.0  # pump rad/s
    rho = max(1e-6, fuel.density_kg_per_m3)
    k = max(1e5, fuel.bulk_modulus_pa)
    v_eff = max(1e-12, hyd.volume_eff_m3)
    a_plunger = hyd.plunger_area_m2
    p_back = hyd.back_pressure_bar * 1e5
    p_open_pilot = p_back + nozzle.pilot_open_bar * 1e5
    p_open_main = p_back + nozzle.main_open_bar * 1e5

    p = p_back
    pilot_m = 0.0
    total_m = 0.0
    a_noz = nozzle.area_m2
    cd = nozzle.discharge_coeff

    for i in range(1, len(a_deg)):
        d_deg = float(a_deg[i] - a_deg[i - 1])
        if d_deg <= 0:
            continue
        dt = (d_deg * pi / 180.0) / max(1e-9, omega_pump)
        ds = (s_mm[i] - s_mm[i - 1]) * 1e-3
        v_plunger = ds / max(1e-12, dt)
        q_plunger = a_plunger * v_plunger

        m_dot = 0.0
        if p >= p_open_pilot:
            area_eff = a_noz * cd
            if p < p_open_main:
                area_eff *= max(1e-3, nozzle.pilot_area_frac)
            dp = max(0.0, p - p_back)
            m_dot = area_eff * sqrt(2.0 * rho * dp)
        q_out = m_dot / rho if m_dot > 0.0 else 0.0

        dp_dt = (k / v_eff) * (q_plunger - q_out)
        p = max(p_back, p + dp_dt * dt)

        if m_dot > 0.0:
            dm = m_dot * dt
            total_m += dm
            if p < p_open_main:
                pilot_m += dm

    if total_m <= 0.0:
        return 0.0
    return max(0.0, min(1.0, pilot_m / total_m))
