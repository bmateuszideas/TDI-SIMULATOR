from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np

from .config_loader import (
    create_geometry_from_config,
    load_yaml_config,
    create_manifold_configs_from_config,
    create_valve_flow_from_config,
)
from .controller import solve_monotone_bisect
from .coupled import simulate_coupled_turbo
from .edc_maps import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D
from .full_cycle import FullCycleConfig, simulate_full_cycle
from .hydraulics import NozzleConfig, VP37HydraulicConfig, NeedleConfig, estimate_pilot_ratio
from .injection import InjectionLineConfig, solve_injection_hydraulics
from .lift_table import ValveLiftTable
from .models import (
    CombustionConfig,
    EngineGeometry,
    Fuel,
    InjectionSchedule,
    SimulationConfig,
    ManifoldConfig,
)
from .n146_map import N146VoltageMap2D
from .soi_map import SOIMap2D
from .solver import simulate_closed_cycle
from .turbo import TurboConfig
from .valvetrain import ValveFlow, ValveTiming
from .vp37 import VP37LineModel, apply_hydraulic_delay
from .vp37_cam import VP37CamProfile


def load_geometry_from_yaml(path: str | Path) -> EngineGeometry:
    """Helper to load the YAML config and create an EngineGeometry instance."""
    config = load_yaml_config(path)
    return create_geometry_from_config(config)


def _default_schedule() -> InjectionSchedule:
    return InjectionSchedule(
        soi_pilot_deg=-12.0,
        soi_main_deg=-6.0,
        pilot_fraction=0.12,
        duration_pilot_deg=8.0,
        duration_main_deg=42.0,
        wiebe_m_pilot=2.0,
        wiebe_m_main=2.0,
    )


def _validate_args(args: Any) -> None:
    """Validate CLI arguments for safety and correctness (F-002).
    
    Raises:
        SystemExit: If any argument value is invalid.
    """
    if args.rpm <= 0:
        raise SystemExit("Error: --rpm must be > 0")
    
    if args.fuel_mg < 0:
        raise SystemExit("Error: --fuel-mg must be >= 0")
    
    if args.fuel_mg_min < 0:
        raise SystemExit("Error: --fuel-mg-min must be >= 0")
    
    if args.fuel_mg_max < 0:
        raise SystemExit("Error: --fuel-mg-max must be >= 0")
    
    if args.fuel_mg_min > args.fuel_mg_max:
        raise SystemExit("Error: --fuel-mg-min must be <= --fuel-mg-max")
