from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import exp
from typing import Any

from .models import SimulationConfig


R_AIR_J_PER_KG_K = 287.0
R_UNIVERSAL_J_PER_MOL_K = 8.314462618


@dataclass(frozen=True)
class GasModel:
    r_j_per_kg_k: float = R_AIR_J_PER_KG_K

    def gamma(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["gamma"]
        g = cfg.gamma_t0 - cfg.gamma_slope_per_k * temperature_k
        return max(cfg.gamma_min, min(cfg.gamma_max, g))

    def cp(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["cp"]
        g = self.gamma(temperature_k, cfg, pressure_pa=pressure_pa)
        return g * self.r_j_per_kg_k / max(1e-9, (g - 1.0))

    def cv(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None) -> float:
        props = _real_gas_props(temperature_k, pressure_pa, cfg)
        if props is not None:
            return props["cv"]
        cp = self.cp(temperature_k, cfg, pressure_pa=pressure_pa)
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
            cp_mod = _coolprop_module()
            if cp_mod is not None:
                try:
                    return float(cp_mod.PropsSI("P", "T", t, "Dmass", rho, cfg.coolprop_fluid))
                except Exception:
                    if cfg.strict_backends:
                        raise RuntimeError("CoolProp backend failed to compute pressure.")

        return rho * max(1e-9, self.r_j_per_kg_k) * t

    def temperature_from_prho(self, pressure_pa: float, density_kg_per_m3: float, cfg: SimulationConfig) -> float:
        p = float(max(1.0, pressure_pa))
        rho = float(max(1e-9, density_kg_per_m3))
        backend = cfg.thermo_backend

        if backend == "coolprop":
            cp_mod = _coolprop_module()
            if cp_mod is not None:
                try:
                    return float(cp_mod.PropsSI("T", "P", p, "Dmass", rho, cfg.coolprop_fluid))
                except Exception:
                    if cfg.strict_backends:
                        raise RuntimeError("CoolProp backend failed to compute temperature.")

        return p / (max(1e-9, self.r_j_per_kg_k) * rho)


@lru_cache(maxsize=2)
def _coolprop_module() -> Any | None:
    try:
        import CoolProp.CoolProp as cp  # type: ignore

        return cp
    except Exception:
        return None


def _real_gas_props(temperature_k: float, pressure_pa: float | None, cfg: SimulationConfig) -> dict[str, float] | None:
    p = float(pressure_pa) if pressure_pa is not None else 1.0e5
    t = float(max(1.0, temperature_k))
    backend = cfg.thermo_backend

    if backend == "coolprop":
        cp_mod = _coolprop_module()
        if cp_mod is None:
            if cfg.strict_backends:
                raise RuntimeError("CoolProp backend requested but module is not available.")
            return None
        try:
            cp = float(cp_mod.PropsSI("Cpmass", "T", t, "P", p, cfg.coolprop_fluid))
            cv = float(cp_mod.PropsSI("Cvmass", "T", t, "P", p, cfg.coolprop_fluid))
            if cp <= 0.0 or cv <= 0.0:
                return None
            gamma = cp / cv
            return {"cp": cp, "cv": cv, "gamma": gamma}
        except Exception:
            if cfg.strict_backends:
                raise RuntimeError("CoolProp backend failed to compute properties.")
            return None

    return None


def ignition_delay_seconds_arrhenius(p_pa: float, t_k: float, *, a: float, n: float, ea_j_per_mol: float) -> float:
    """Simple Arrhenius-like model from spec (tunable; not a calibrated correlation).

    Uses p in bar to avoid microscopic A values.
    """
    p_bar = max(1e-6, p_pa / 1.0e5)
    return a * (p_bar ** (-n)) * exp(ea_j_per_mol / (R_UNIVERSAL_J_PER_MOL_K * max(1.0, t_k)))


def omega_rad_per_s(rpm: float) -> float:
    return rpm * 2.0 * 3.141592653589793 / 60.0
