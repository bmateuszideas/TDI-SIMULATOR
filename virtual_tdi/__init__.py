"""Virtual 1.9 TDI ("cyfrowy duch") - white-box engine cycle simulator.

This package starts with a practical MVP: 0D closed-cylinder cycle (compression +
combustion + expansion) integrated in crank angle domain with RK4.
"""

from .turbo import CoupledResult, TurboConfig, simulate_coupled_turbo
from .engine_model import (
    BoundaryConditions,
    FullCycleConfig,
    EngineGeometry,
    EngineState,
    Fuel,
    InjectionSchedule,
    SimulationConfig,
    simulate_full_cycle,
    simulate_closed_cycle,
)
from .injection import (
    BoostTargetMap2D,
    EGRMafTargetMap2D,
    SmokeLimiterMap2D,
    ValveLiftTable,
    N146VoltageMap2D,
    SOIMap2D,
    VP37LineModel,
    apply_hydraulic_delay,
    VP37CamProfile,
)
from .physics import NozzleConfig, VP37HydraulicConfig, estimate_pilot_ratio, ValveFlow, ValveTiming
from .core import DatasetConfig, generate_dataset

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
