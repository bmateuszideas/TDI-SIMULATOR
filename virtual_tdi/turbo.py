from __future__ import annotations

from dataclasses import dataclass
from math import pow


@dataclass(frozen=True)
class TurboConfig:
    eta_turbine: float = 0.70
    eta_comp: float = 0.70
    eta_mech: float = 0.95
    pr_min: float = 1.0
    pr_max: float = 2.4
    p_amb_pa: float = 1.0e5
    t_amb_k: float = 300.0
    gamma: float = 1.35
    cp_j_per_kg_k: float = 1005.0
    relax: float = 0.5


def compressor_pr_from_power(
    *,
    m_air_kg_s: float,
    t_in_k: float,
    power_turb_w: float,
    cfg: TurboConfig,
) -> float:
    if m_air_kg_s <= 1e-9 or power_turb_w <= 0.0:
        return cfg.pr_min

    power_shaft = power_turb_w * cfg.eta_turbine * cfg.eta_mech
    t_in = max(1.0, t_in_k)
    cp = max(1.0, cfg.cp_j_per_kg_k)
    g = max(1.1, cfg.gamma)
    # power_comp = m_air * cp * T_in / eta_c * (PR^((g-1)/g) - 1)
    term = (power_shaft * cfg.eta_comp) / max(1e-9, m_air_kg_s * cp * t_in)
    pr = pow(1.0 + max(0.0, term), g / (g - 1.0))
    return max(cfg.pr_min, min(cfg.pr_max, pr))
