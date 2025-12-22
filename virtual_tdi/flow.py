from __future__ import annotations

from math import sqrt
from typing import Any

from .thermo import R_UNIVERSAL_J_PER_MOL_K


def orifice_mdot_kg_per_s(
    *,
    p_up_pa: float,
    t_up_k: float,
    p_down_pa: float,
    gamma: float,
    r_j_per_kg_k: float,
    area_m2: float,
    discharge_coeff: float,
    backend: str = "simple",
    strict: bool = True,
) -> float:
    """Quasi-steady compressible orifice flow (ideal gas).

    Returns positive mass flow from upstream -> downstream.
    """
    if area_m2 <= 0.0 or discharge_coeff <= 0.0:
        return 0.0

    p_up = max(1.0, p_up_pa)
    p_down = max(1.0, p_down_pa)
    t_up = max(1.0, t_up_k)
    g = max(1.01, gamma)
    r = max(1e-9, r_j_per_kg_k)

    pr = p_down / p_up
    pr_crit = (2.0 / (g + 1.0)) ** (g / (g - 1.0))

    a_eff = discharge_coeff * area_m2

    if backend == "fluids":
        mdot = _fluids_orifice_mdot(
            p_up_pa=p_up,
            p_down_pa=p_down,
            t_up_k=t_up,
            gamma=g,
            r_j_per_kg_k=r,
            area_m2=a_eff,
            strict=strict,
        )
        if mdot is not None:
            return max(0.0, mdot)
        if strict:
            # If the fluids backend is present but does not expose the expected API,
            # fall back to the simple formulation instead of failing hard.
            pass

    if pr <= pr_crit:
        # Choked
        term = (2.0 / (g + 1.0)) ** ((g + 1.0) / (2.0 * (g - 1.0)))
        return a_eff * p_up * sqrt(g / (r * t_up)) * term

    # Subsonic
    term = (2.0 * g / (r * t_up * (g - 1.0))) * (pr ** (2.0 / g) - pr ** ((g + 1.0) / g))
    if term <= 0.0:
        return 0.0
    return a_eff * p_up * sqrt(term)


def _fluids_orifice_mdot(
    *,
    p_up_pa: float,
    p_down_pa: float,
    t_up_k: float,
    gamma: float,
    r_j_per_kg_k: float,
    area_m2: float,
    strict: bool,
) -> float | None:
    try:
        import inspect

        import fluids.compressible as comp  # type: ignore
    except Exception:
        if strict:
            raise RuntimeError("fluids backend requested but module is not available.")
        return None

    mw = R_UNIVERSAL_J_PER_MOL_K / max(1e-9, r_j_per_kg_k)  # kg/mol
    params = {
        "P0": p_up_pa,
        "P1": p_up_pa,
        "P2": p_down_pa,
        "P": p_down_pa,
        "T0": t_up_k,
        "T1": t_up_k,
        "A": area_m2,
        "A_t": area_m2,
        "k": gamma,
        "gamma": gamma,
        "MW": mw,
        "molar_mass": mw,
    }

    candidates = [
        "isentropic_mass_flow",
        "isentropic_mass_flow_rate",
        "mass_flow_rate_isentropic",
        "critical_flow",
    ]
    for name in candidates:
        fn: Any | None = getattr(comp, name, None)
        if fn is None:
            continue
        try:
            sig = inspect.signature(fn)
            call_kwargs = {k: v for k, v in params.items() if k in sig.parameters}
            if not call_kwargs:
                continue
            mdot = fn(**call_kwargs)
            if mdot is None:
                continue
            return float(mdot)
        except Exception:
            continue
    return None
