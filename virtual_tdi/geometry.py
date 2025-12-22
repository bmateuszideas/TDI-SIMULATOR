from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt

from .models import EngineGeometry


@dataclass(frozen=True)
class GeometryResult:
    theta_rad: float
    s_m: float
    ds_dtheta_m_per_rad: float
    volume_m3: float
    dvol_dtheta_m3_per_rad: float
    # Exposed surface areas for heat transfer
    area_head_m2: float
    area_piston_m2: float
    area_liner_m2: float
    heat_transfer_area_m2: float


def piston_position_s_m(geom: EngineGeometry, theta_rad: float) -> float:
    # Spec implementation: s = r cosθ + sqrt(L^2 - (r sinθ - δ)^2)
    r = geom.crank_radius_m
    L = geom.rod_length_m
    delta = geom.offset_m
    u = r * sin(theta_rad) - delta
    return r * cos(theta_rad) + sqrt(max(0.0, L * L - u * u))


def piston_position_derivative_ds_dtheta(geom: EngineGeometry, theta_rad: float) -> float:
    r = geom.crank_radius_m
    L = geom.rod_length_m
    delta = geom.offset_m
    u = r * sin(theta_rad) - delta
    denom = sqrt(max(1e-30, L * L - u * u))
    # ds/dθ = -r sinθ - (u * r cosθ)/sqrt(L^2 - u^2)
    return -r * sin(theta_rad) - (u * r * cos(theta_rad)) / denom


def cylinder_volume_m3(geom: EngineGeometry, theta_rad: float) -> tuple[float, float, float]:
    """Returns (V, dV/dtheta, x_from_tdc).

    x_from_tdc is the current piston travel from TDC (0 at TDC, ~stroke at BDC).
    """
    s = piston_position_s_m(geom, theta_rad)
    ds_dtheta = piston_position_derivative_ds_dtheta(geom, theta_rad)
    s_tdc = piston_position_s_m(geom, 0.0)
    x_from_tdc = s_tdc - s
    area = geom.piston_area_m2
    V = geom.clearance_volume_m3_per_cyl + area * x_from_tdc
    dV_dtheta = -area * ds_dtheta
    return V, dV_dtheta, x_from_tdc


def get_surface_areas(geom: EngineGeometry, x_from_tdc_m: float) -> tuple[float, float, float]:
    """Returns heat transfer surface areas for head, piston, and liner."""
    exposed_liner_height = max(0.0, min(geom.stroke_m, x_from_tdc_m))
    area_piston = geom.piston_area_m2
    area_head = area_piston  # Assume flat head
    area_liner = pi * geom.bore_m * exposed_liner_height
    return area_head, area_piston, area_liner


def geometry_at_theta(geom: EngineGeometry, theta_rad: float) -> GeometryResult:
    s = piston_position_s_m(geom, theta_rad)
    ds_dtheta = piston_position_derivative_ds_dtheta(geom, theta_rad)
    V, dV_dtheta, x_from_tdc = cylinder_volume_m3(geom, theta_rad)
    a_head, a_piston, a_liner = get_surface_areas(geom, x_from_tdc)
    heat_transfer_area = a_head + a_piston + a_liner
    return GeometryResult(
        theta_rad=theta_rad,
        s_m=s,
        ds_dtheta_m_per_rad=ds_dtheta,
        volume_m3=V,
        dvol_dtheta_m3_per_rad=dV_dtheta,
        area_head_m2=a_head,
        area_piston_m2=a_piston,
        area_liner_m2=a_liner,
        heat_transfer_area_m2=heat_transfer_area,
    )
