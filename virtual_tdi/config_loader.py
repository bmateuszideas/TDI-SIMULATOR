from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import EngineGeometry, ManifoldConfig
from .valvetrain import ValveFlow


def load_yaml_config(path: str | Path) -> dict:
    """Loads a YAML file and returns its content as a dictionary."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Configuration file not found at: {p}")
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_geometry_from_config(config: dict[str, Any]) -> EngineGeometry:
    """Creates an EngineGeometry object from a loaded YAML config dictionary."""
    try:
        crank_params = config["parameters"]["cranktrain"]
        comp_params = config["parameters"]["combustion_chamber"]
        return EngineGeometry(
            bore_m=float(crank_params["bore"]["value"]) * 1e-3,
            stroke_m=float(crank_params["stroke"]["value"]) * 1e-3,
            rod_length_m=float(crank_params["rod_length"]["value"]) * 1e-3,
            crank_radius_m=float(crank_params["crank_radius"]["value"]) * 1e-3,
            offset_m=float(crank_params["cylinder_offset"]["value"]) * 1e-3,
            compression_ratio=float(str(comp_params["compression_ratio"]["value"]).split(":")[0]),
            cylinders=int(comp_params["total_cylinders"]["value"]),
        )
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid or missing key in engine config for geometry: {e}") from e


def create_manifold_configs_from_config(config: dict[str, Any]) -> dict[str, ManifoldConfig]:
    """Creates ManifoldConfig objects from a loaded YAML config dictionary."""
    try:
        params = config["parameters"]
        manifold_params = params.get("manifolds")
        if manifold_params is None:
            manifold_params = (
                params.get("masses", {})
                .get("total_reciprocating_mass_per_cyl", {})
                .get("manifolds")
            )
        if manifold_params is None:
            raise KeyError("manifolds")
        intake_vol_l = float(manifold_params["intake_volume"]["value"])
        exhaust_vol_l = float(manifold_params["exhaust_volume"]["value"])

        return {
            "intake": ManifoldConfig(volume_m3=intake_vol_l * 1e-3),
            "exhaust": ManifoldConfig(volume_m3=exhaust_vol_l * 1e-3),
        }
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid or missing key in engine config for manifolds: {e}") from e


def create_valve_flow_from_config(config: dict[str, Any]) -> ValveFlow:
    """Creates a ValveFlow object from a loaded YAML config dictionary."""
    try:
        valve_params = config["parameters"]["valvetrain"]
        max_lift_m = float(valve_params["max_valve_lift"]["value"]) * 1e-3
        return ValveFlow(
            intake_valve_diameter_m=float(valve_params["intake_valve_diameter"]["value"]) * 1e-3,
            exhaust_valve_diameter_m=float(valve_params["exhaust_valve_diameter"]["value"]) * 1e-3,
            intake_max_lift_m=max_lift_m,
            exhaust_max_lift_m=max_lift_m,
        )
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid or missing key in engine config for valvetrain: {e}") from e
