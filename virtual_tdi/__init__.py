"""Virtual 1.9 TDI ("cyfrowy duch") - white-box engine cycle simulator.

This package starts with a practical MVP: 0D closed-cylinder cycle (compression +
combustion + expansion) integrated in crank angle domain with RK4.
"""

from .coupled import CoupledResult, simulate_coupled_turbo
from .full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle
from .edc_maps import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D
from .hydraulics import NozzleConfig, VP37HydraulicConfig, estimate_pilot_ratio
from .lift_table import ValveLiftTable
from .models import EngineGeometry, EngineState, Fuel, InjectionSchedule, SimulationConfig
from .n146_map import N146VoltageMap2D
from .soi_map import SOIMap2D
from .solver import simulate_closed_cycle
from .valvetrain import ValveFlow, ValveTiming
from .vp37 import VP37LineModel, apply_hydraulic_delay
from .vp37_cam import VP37CamProfile
from .dataset import DatasetConfig, generate_dataset
from .turbo import TurboConfig

__all__ = [
    "BoundaryConditions",
    "BoostTargetMap2D",
    "CoupledResult",
    "EGRMafTargetMap2D",
    "EngineGeometry",
    "EngineState",
    "Fuel",
    "FullCycleConfig",
    "InjectionSchedule",
    "DatasetConfig",
    "NozzleConfig",
    "N146VoltageMap2D",
    "SmokeLimiterMap2D",
    "SimulationConfig",
    "SOIMap2D",
    "TurboConfig",
    "VP37HydraulicConfig",
    "estimate_pilot_ratio",
    "generate_dataset",
    "ValveFlow",
    "ValveLiftTable",
    "ValveTiming",
    "VP37CamProfile",
    "VP37LineModel",
    "apply_hydraulic_delay",
    "simulate_closed_cycle",
    "simulate_coupled_turbo",
    "simulate_full_cycle",
]
