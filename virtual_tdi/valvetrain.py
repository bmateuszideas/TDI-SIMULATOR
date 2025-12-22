from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin


@dataclass(frozen=True)
class ValveTiming:
    # Angles in degrees, referenced to 0 = TDC combustion.
    # Full 4-stroke cycle spans [-360, 360] deg.
    ivo_deg: float = -350.0
    ivc_deg: float = -150.0
    evo_deg: float = 140.0
    evc_deg: float = 350.0


@dataclass(frozen=True)
class ValveFlow:
    intake_valve_diameter_m: float = 35.95e-3
    exhaust_valve_diameter_m: float = 31.45e-3
    intake_max_lift_m: float = 8.5e-3
    exhaust_max_lift_m: float = 8.5e-3
    cd_intake: float = 0.70
    cd_exhaust: float = 0.72


def _cycle_angle_0_720(theta_deg: float) -> float:
    return (theta_deg + 360.0) % 720.0


def valve_lift_fraction(theta_deg: float, open_deg: float, close_deg: float) -> float:
    """Smooth normalized lift (0..1) between open and close over a 720° cycle.

    Uses a symmetric sin(pi * phi) profile where phi in [0,1].
    """
    t = _cycle_angle_0_720(theta_deg)
    o = _cycle_angle_0_720(open_deg)
    c = _cycle_angle_0_720(close_deg)

    duration = (c - o) % 720.0
    if duration <= 0.0:
        return 0.0
    inside = ((t - o) % 720.0) <= duration
    if not inside:
        return 0.0
    phi = ((t - o) % 720.0) / duration
    if phi <= 0.0 or phi >= 1.0:
        return 0.0
    return float(sin(pi * phi))


def effective_curtain_area_m2(valve_diameter_m: float, lift_m: float) -> float:
    # Curtain area ~ circumference * lift, capped by port area.
    curtain = pi * valve_diameter_m * max(0.0, lift_m)
    port = pi * (valve_diameter_m**2) / 4.0
    return min(curtain, port)
