from __future__ import annotations

from math import pow

from .models import HeatTransferConfig


def h_woschni_simplified_w_per_m2_k(
    *,
    bore_m: float,
    pressure_pa: float,
    temperature_k: float,
    mean_piston_speed_m_per_s: float,
    cfg: HeatTransferConfig,
) -> float:
    """
    Calculates the gas-side heat transfer coefficient using a simplified
    Woschni correlation.
    """
    # h = c * B^-0.2 * p_bar^0.8 * T^-0.55 * w^0.8
    p_bar = max(1e-6, pressure_pa / 1.0e5)
    w = max(0.1, cfg.w_mult * mean_piston_speed_m_per_s)
    return (
        cfg.woschni_c
        * pow(max(1e-6, bore_m), -0.2)
        * pow(p_bar, 0.8)
        * pow(max(1.0, temperature_k), -0.55)
        * pow(w, 0.8)
    )


def calculate_wall_heat_loss_j_per_rad(
    *,
    h_coeff: float,
    gas_temp_k: float,
    area_head_m2: float,
    area_piston_m2: float,
    area_liner_m2: float,
    cfg: HeatTransferConfig,
    omega_rad_per_s: float,
) -> float:
    """
    Calculates the total heat loss to the walls from all surfaces in J/rad
    for a multi-zone wall temperature model.
    """
    q_dot_head = h_coeff * area_head_m2 * (gas_temp_k - cfg.head_temp_k)
    q_dot_piston = h_coeff * area_piston_m2 * (gas_temp_k - cfg.piston_temp_k)
    q_dot_liner = h_coeff * area_liner_m2 * (gas_temp_k - cfg.liner_temp_k)

    q_dot_total_w = q_dot_head + q_dot_piston + q_dot_liner
    
    # Convert from J/s (Watts) to J/rad
    return q_dot_total_w / max(1e-9, omega_rad_per_s)

