from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import exp
from typing import Any

import numpy as np

from .models import SimulationConfig


R_AIR_J_PER_KG_K = 287.0
R_UNIVERSAL_J_PER_MOL_K = 8.314462618


_T_GRID_K = tuple(float(t) for t in np.arange(200.0, 3000.0 + 1.0, 25.0))
_LOG_P_GRID = tuple(float(x) for x in np.linspace(np.log(1.0e3), np.log(1.0e8), 60))
_T_MIN_K = float(_T_GRID_K[0])
_T_MAX_K = float(_T_GRID_K[-1])
_LOG_P_MIN = float(_LOG_P_GRID[0])
_LOG_P_MAX = float(_LOG_P_GRID[-1])
_T_STEP_K = float(_T_GRID_K[1]) - float(_T_GRID_K[0])
_LP_STEP = float(_LOG_P_GRID[1]) - float(_LOG_P_GRID[0])
_LOG_RHO_STEP = None


@dataclass(frozen=True)
class GasModel:
    r_j_per_kg_k: float = R_AIR_J_PER_KG_K
    # Exhaust products have a higher molar mass and cp than air; the mixture
    # gamma drops accordingly. cp offset from diesel exhaust gas tables
    # (Heywood Ch. 3: cp_exh ~ 1105-1150 J/kgK at 300-800 K vs 1005 air).
    cp_burned_offset_j_per_kg_k: float = 110.0

    def _burned_cp_offset(self, burned_fraction: float | None) -> float:
        if burned_fraction is None:
            return 0.0
        x = max(0.0, min(1.0, float(burned_fraction)))
        return self.cp_burned_offset_j_per_kg_k * x

    def gamma(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None,
              burned_fraction: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["gamma"]
        if cfg.gamma_slope_per_k != 0.0:
            # Legacy linear form (kept for backward compatibility of old configs)
            g = cfg.gamma_t0 - cfg.gamma_slope_per_k * temperature_k
        else:
            # Saturating exponential fit to air/exhaust tables (Heywood Ch. 2);
            # see models.SimulationConfig for the fitted points.
            import numpy as np
            g = cfg.gamma_inf + (cfg.gamma_t0 - cfg.gamma_inf) * float(
                np.exp(-max(1.0, temperature_k) / cfg.gamma_t_ref_k))
        g = max(cfg.gamma_min, min(cfg.gamma_max, g))
        if burned_fraction is not None and burned_fraction > 0.0:
            # Mixture correction: gamma_mix = cp_mix / (cp_mix - R) with
            # cp_mix = cp_air + x * cp_offset (TODO.md Faza 2.B.1).
            cp_air = g * self.r_j_per_kg_k / max(1e-9, (g - 1.0))
            cp_mix = cp_air + self._burned_cp_offset(burned_fraction)
            return cp_mix / max(1e-9, cp_mix - self.r_j_per_kg_k)
        return g

    def cp(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None,
           burned_fraction: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["cp"]
        g = self.gamma(temperature_k, cfg, pressure_pa=pressure_pa,
                       burned_fraction=burned_fraction)
        return g * self.r_j_per_kg_k / max(1e-9, (g - 1.0))

    def cv(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None,
           burned_fraction: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["cv"]
        cp = self.cp(temperature_k, cfg, pressure_pa=pressure_pa,
                     burned_fraction=burned_fraction)
        return max(1e-9, cp - self.r_j_per_kg_k)

    def density_from_pT(self, pressure_pa: float, temperature_k: float, cfg: SimulationConfig) -> float:
        p = float(max(1.0, pressure_pa))
        t = float(max(1.0, temperature_k))
        backend = cfg.thermo_backend

        if backend == "coolprop":
            cp_mod = _coolprop_module()
            if cp_mod is not None:
                try:
                    return float(cp_mod.PropsSI("Dmass", "T", t, "P", p, cfg.coolprop_fluid))
                except Exception:
                    if cfg.strict_backends:
                        raise RuntimeError("CoolProp backend failed to compute density.")

        return p / (max(1e-9, self.r_j_per_kg_k) * t)

    def pressure_from_rhoT(self, density_kg_per_m3: float, temperature_k: float, cfg: SimulationConfig) -> float:
        rho = float(max(1e-9, density_kg_per_m3))
        t = float(max(1.0, temperature_k))
        backend = cfg.thermo_backend

        if backend == "coolprop":
            tables = _coolprop_rho_t_tables(cfg.coolprop_fluid)
            if tables is not None:
                t_grid, rho_grid, p_tab = tables
                t_c = min(max(t, _T_MIN_K), _T_MAX_K)
                # rho grid is log-spaced
                lrho = float(np.log(max(1e-6, rho)))
                lrho_c = min(max(lrho, _LOG_RHO_MIN), _LOG_RHO_MAX)
                return _bilinear_lookup(t_grid, rho_grid, p_tab, t_c, lrho_c)
            if cfg.strict_backends:
                raise RuntimeError("CoolProp backend requested but module is not available.")

        return rho * max(1e-9, self.r_j_per_kg_k) * t

    def temperature_from_prho(self, pressure_pa: float, density_kg_per_m3: float, cfg: SimulationConfig) -> float:
        p = float(max(1.0, pressure_pa))
        rho = float(max(1e-9, density_kg_per_m3))
        backend = cfg.thermo_backend

        if backend == "coolprop":
            tables = _coolprop_rho_t_tables(cfg.coolprop_fluid)
            if tables is not None:
                t_grid, rho_grid, p_tab = tables
                lp = float(np.log(p))
                lp_c = min(max(lp, _LOG_P_MIN), _LOG_P_MAX)
                # Invert p_tab on the (T, log rho) grid: find T for given (log rho, log p).
                # p_tab varies strongly with T at fixed rho, so bisection over the T axis is robust.
                lo, hi = 0, t_grid.size - 1
                lrho = float(np.log(max(1e-6, rho)))
                lrho_c = min(max(lrho, _LOG_RHO_MIN), _LOG_RHO_MAX)
                for _ in range(40):
                    mid = (lo + hi) // 2
                    p_mid = _bilinear_lookup(t_grid, rho_grid, p_tab, float(t_grid[mid]), lrho_c)
                    if p_mid < p:
                        lo = mid
                    else:
                        hi = mid
                    if hi - lo <= 1:
                        break
                p_lo = _bilinear_lookup(t_grid, rho_grid, p_tab, float(t_grid[lo]), lrho_c)
                p_hi = _bilinear_lookup(t_grid, rho_grid, p_tab, float(t_grid[hi]), lrho_c)
                if p_hi <= p_lo:
                    return float(t_grid[lo])
                frac = (p - p_lo) / (p_hi - p_lo)
                return float(t_grid[lo] + frac * (t_grid[hi] - t_grid[lo]))
            if cfg.strict_backends:
                raise RuntimeError("CoolProp backend requested but module is not available.")

        return p / (max(1e-9, self.r_j_per_kg_k) * rho)





@lru_cache(maxsize=2)
def _coolprop_module() -> Any | None:
    try:
        import CoolProp.CoolProp as cp  # type: ignore

        return cp
    except Exception:
        return None


@lru_cache(maxsize=8)
def _coolprop_tables(
    fluid: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """Cpmass/Cvmass tabulated on a (T, log p) grid for fast bilinear lookup."""
    cp_mod = _coolprop_module()
    if cp_mod is None:
        return None
    t_grid = np.asarray(_T_GRID_K, dtype=float)
    lp_grid = np.asarray(_LOG_P_GRID, dtype=float)
    cp_tab = np.empty((t_grid.size, lp_grid.size), dtype=float)
    cv_tab = np.empty_like(cp_tab)
    for ti, t in enumerate(t_grid):
        for pi, lp in enumerate(lp_grid):
            p = float(np.exp(lp))
            try:
                cp_tab[ti, pi] = float(cp_mod.PropsSI("Cpmass", "T", float(t), "P", p, fluid))
                cv_tab[ti, pi] = float(cp_mod.PropsSI("Cvmass", "T", float(t), "P", p, fluid))
            except Exception:
                cp_tab[ti, pi] = -1.0
                cv_tab[ti, pi] = -1.0
    if np.any(cp_tab <= 0.0) or np.any(cv_tab <= 0.0):
        return None
    return t_grid, lp_grid, cp_tab, cv_tab


def _bilinear_lookup(t_grid: np.ndarray, y_grid: np.ndarray, tab: np.ndarray, t: float, y: float) -> float:
    """Bilinear interpolation on uniform grids; first axis spaced by _T_STEP_K,
    second axis uniform with step derived from the grid itself."""
    nt = t_grid.size
    ny = y_grid.size
    y_step = float(y_grid[1]) - float(y_grid[0])
    ti = int((t - float(t_grid[0])) / _T_STEP_K)
    if ti < 0:
        ti = 0
    elif ti > nt - 2:
        ti = nt - 2
    yi = int((y - float(y_grid[0])) / y_step)
    if yi < 0:
        yi = 0
    elif yi > ny - 2:
        yi = ny - 2
    t0 = float(t_grid[ti])
    y0 = float(y_grid[yi])
    ft = (t - t0) / _T_STEP_K
    fy = (y - y0) / y_step
    if ft < 0.0:
        ft = 0.0
    elif ft > 1.0:
        ft = 1.0
    if fy < 0.0:
        fy = 0.0
    elif fy > 1.0:
        fy = 1.0
    q00 = tab[ti, yi]
    q10 = tab[ti + 1, yi]
    q01 = tab[ti, yi + 1]
    q11 = tab[ti + 1, yi + 1]
    a = q00 + ft * (q10 - q00)
    b = q01 + ft * (q11 - q01)
    return a + fy * (b - a)


_LOG_RHO_GRID = tuple(float(x) for x in np.linspace(np.log(1e-4), np.log(5.0e2), 80))
_LOG_RHO_MIN = float(_LOG_RHO_GRID[0])
_LOG_RHO_MAX = float(_LOG_RHO_GRID[-1])
_LOG_RHO_STEP = float(_LOG_RHO_GRID[1]) - float(_LOG_RHO_GRID[0])


@lru_cache(maxsize=8)
def _coolprop_rho_t_tables(
    fluid: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Pressure tabulated on a (T, log rho) grid for fast p(rho, T) lookup."""
    cp_mod = _coolprop_module()
    if cp_mod is None:
        return None
    t_grid = np.asarray(_T_GRID_K, dtype=float)
    lrho_grid = np.asarray(_LOG_RHO_GRID, dtype=float)
    p_tab = np.empty((t_grid.size, lrho_grid.size), dtype=float)
    for ti, t in enumerate(t_grid):
        for ri, lrho in enumerate(lrho_grid):
            rho = float(np.exp(lrho))
            try:
                p_tab[ti, ri] = float(cp_mod.PropsSI("P", "T", float(t), "Dmass", rho, fluid))
            except Exception:
                p_tab[ti, ri] = -1.0
    if np.any(p_tab <= 0.0):
        return None
    return t_grid, lrho_grid, p_tab


def _real_gas_props(temperature_k: float, pressure_pa: float | None, cfg: SimulationConfig) -> dict[str, float] | None:
    p = float(pressure_pa) if pressure_pa is not None else 1.0e5
    t = float(max(1.0, temperature_k))
    backend = cfg.thermo_backend

    if backend == "coolprop":
        tables = _coolprop_tables(cfg.coolprop_fluid)
        if tables is None:
            if cfg.strict_backends:
                raise RuntimeError("CoolProp backend requested but module is not available.")
            return None
        t_grid, lp_grid, cp_tab, cv_tab = tables
        t_c = min(max(t, _T_MIN_K), _T_MAX_K)
        lp_c = min(max(float(np.log(max(1.0, p))), _LOG_P_MIN), _LOG_P_MAX)
        cp = _bilinear_lookup(t_grid, lp_grid, cp_tab, t_c, lp_c)
        cv = _bilinear_lookup(t_grid, lp_grid, cv_tab, t_c, lp_c)
        if cp <= 0.0 or cv <= 0.0:
            return None
        return {"cp": cp, "cv": cv, "gamma": cp / cv}

    return None


def ignition_delay_seconds_arrhenius(p_pa: float, t_k: float, *, a: float, n: float, ea_j_per_mol: float) -> float:
    """Simple Arrhenius-like model from spec (tunable; not a calibrated correlation).

    Uses p in bar to avoid microscopic A values.
    """
    p_bar = max(1e-6, p_pa / 1.0e5)
    return a * (p_bar ** (-n)) * exp(ea_j_per_mol / (R_UNIVERSAL_J_PER_MOL_K * max(1.0, t_k)))


def omega_rad_per_s(rpm: float) -> float:
    return rpm * 2.0 * 3.141592653589793 / 60.0
