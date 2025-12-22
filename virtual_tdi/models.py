from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Literal, Optional


@dataclass(frozen=True)
class EngineGeometry:
    bore_m: float
    stroke_m: float
    rod_length_m: float
    crank_radius_m: float
    offset_m: float
    compression_ratio: float
    cylinders: int = 4

    @property
    def piston_area_m2(self) -> float:
        return pi * (self.bore_m**2) / 4.0

    @property
    def swept_volume_m3_per_cyl(self) -> float:
        return self.piston_area_m2 * self.stroke_m

    @property
    def clearance_volume_m3_per_cyl(self) -> float:
        # CR = (Vs + Vc) / Vc
        return self.swept_volume_m3_per_cyl / (self.compression_ratio - 1.0)


@dataclass(frozen=True)
class ManifoldConfig:
    """Static properties of a manifold."""

    volume_m3: float
    # Initial state guesses
    initial_temp_k: float = 300.0
    initial_pressure_pa: float = 1.0e5
    initial_egr_fraction: float = 0.0


@dataclass
class ManifoldState:
    """Dynamic state of a manifold as a 0D control volume."""

    mass_kg: float
    temperature_k: float
    egr_fraction: float

    @classmethod
    def from_config(cls, cfg: ManifoldConfig) -> "ManifoldState":
        from .thermo import R_AIR_J_PER_KG_K  # Local import to avoid cycle

        # Initial mass from ideal gas law
        rho = cfg.initial_pressure_pa / (max(1e-9, R_AIR_J_PER_KG_K) * max(1.0, cfg.initial_temp_k))
        mass = rho * cfg.volume_m3
        egr_fraction = max(0.0, min(1.0, cfg.initial_egr_fraction))
        return cls(mass_kg=mass, temperature_k=cfg.initial_temp_k, egr_fraction=egr_fraction)


@dataclass(frozen=True)
class Fuel:
    name: str
    lhv_j_per_kg: float
    cetane_number: float
    density_kg_per_m3: float
    bulk_modulus_pa: float
    stoich_air_fuel: float

    # Arrhenius-like ignition delay parameters (tunable; units described in docs).
    id_a: float = 5.0e-6
    id_n: float = 1.0
    id_ea_j_per_mol: float = 6.2e4

    @staticmethod
    def diesel() -> "Fuel":
        return Fuel(
            name="Diesel",
            lhv_j_per_kg=42.5e6,
            cetane_number=51.0,
            density_kg_per_m3=830.0,
            bulk_modulus_pa=1.6e9,
            stoich_air_fuel=14.5,
            id_a=5.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=5.8e4,
        )

    @staticmethod
    def svo_rapeseed() -> "Fuel":
        return Fuel(
            name="SVO (rapeseed)",
            lhv_j_per_kg=37.0e6,
            cetane_number=45.0,
            density_kg_per_m3=920.0,
            bulk_modulus_pa=1.95e9,
            stoich_air_fuel=13.8,
            id_a=7.0e-6,
            id_n=1.0,
            id_ea_j_per_mol=6.2e4,
        )

    @staticmethod
    def methanol() -> "Fuel":
        return Fuel(
            name="Methanol",
            lhv_j_per_kg=20.0e6,
            cetane_number=5.0,
            density_kg_per_m3=790.0,
            bulk_modulus_pa=1.2e9,
            stoich_air_fuel=6.45,
            id_a=2.0e-5,
            id_n=1.0,
            id_ea_j_per_mol=6.5e4,
        )


@dataclass(frozen=True)
class InjectionSchedule:
    # Angles in degrees, relative to TDC combustion (0 deg == TDC).
    soi_pilot_deg: float
    soi_main_deg: float
    pilot_fraction: float  # 0..1 of total fuel energy
    duration_pilot_deg: float
    duration_main_deg: float
    wiebe_m_pilot: float = 2.0
    wiebe_m_main: float = 2.0


@dataclass(frozen=True)
class HeatTransferConfig:
    model: Literal["woschni_simplified"] = "woschni_simplified"
    # Wall temperatures for multi-zone model
    head_temp_k: float = 500.0
    piston_temp_k: float = 550.0
    liner_temp_k: float = 450.0
    # Woschni simplified constants: h = c * B^-0.2 * p_bar^0.8 * T^-0.55 * w^0.8
    woschni_c: float = 3.26
    # Gas velocity proxy: w = w_mult * mean_piston_speed
    w_mult: float = 6.0


@dataclass(frozen=True)
class CombustionConfig:
    eta_comb: float = 0.98
    wiebe_a: float = 6.9
    # Heat release rate model:
    # - wiebe: classic double-Wiebe (pilot+main)
    # - vp37_main: pilot Wiebe, main shaped by VP37 dm_fuel/dθ and shifted by ignition delay
    # - hydraulic_profile: HRR shape is taken from a pre-computed injection rate profile
    hrr_model: Literal["wiebe", "vp37_main", "hydraulic_profile"] = "wiebe"
    # Ignition delay model choice
    ignition_delay_model: Literal["arrhenius", "fixed_deg"] = "arrhenius"
    fixed_ignition_delay_deg: float = 5.0


@dataclass(frozen=True)
class SimulationConfig:
    rpm: float
    theta_start_deg: float = -180.0
    theta_end_deg: float = 180.0
    step_deg: float = 0.1
    intake_pressure_pa: float = 1.0e5
    intake_temp_k: float = 300.0
    # Total fuel per cylinder per cycle (4-stroke) in mg.
    fuel_mg_per_cycle_per_cyl: float = 20.0
    # Gamma model (per spec): gamma(T) = 1.38 - 0.0001*T
    gamma_t0: float = 1.38
    gamma_slope_per_k: float = 1.0e-4
    gamma_min: float = 1.10
    gamma_max: float = 1.40
    combustion: CombustionConfig = CombustionConfig()
    heat_transfer: HeatTransferConfig = HeatTransferConfig()
    thermo_backend: Literal["simple", "coolprop"] = "simple"
    flow_backend: Literal["simple", "fluids"] = "simple"
    coolprop_fluid: str = "Air"
    strict_backends: bool = True
    integrator: Literal["rk4", "scipy"] = "scipy"
    scipy_method: str = "Radau"
    scipy_rtol: float = 1.0e-7
    scipy_atol: float = 1.0e-9
    scipy_max_step_deg: float = 1.0
    # Simple friction loss model for reporting (not fed back into cylinder dynamics).
    fmep_pa: float = 1.0e5  # ~1 bar


@dataclass
class EngineState:
    # Core state integrated in theta domain:
    pressure_pa: float
    # Cached / derived (computed from ideal gas law at each step):
    temperature_k: float
    # Event state for combustion scheduling:
    pilot_soc_deg: Optional[float] = None
    main_soc_deg: Optional[float] = None
