from __future__ import annotations

from math import pi
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
        bore_m = float(crank_params["bore"]["value"]) * 1e-3
        stroke_m = float(crank_params["stroke"]["value"]) * 1e-3
        bowl_volume_m3 = float(comp_params["bowl_volume"]["value"]) * 1e-6
        head_recess_m3 = float(comp_params["head_recess_volume"]["value"]) * 1e-6
        gasket_thickness_m = float(comp_params["gasket_thickness"]["value"]) * 1e-3
        piston_protrusion_m = float(comp_params["piston_protrusion"]["value"]) * 1e-3
        piston_area_m2 = pi * (bore_m**2) / 4.0
        clearance_volume_m3 = (
            bowl_volume_m3 + head_recess_m3 + piston_area_m2 * (gasket_thickness_m - piston_protrusion_m)
        )
        if clearance_volume_m3 <= 0.0:
            raise ValueError("Computed clearance volume must be positive.")
        swept_volume_m3 = piston_area_m2 * stroke_m
        compression_ratio = (swept_volume_m3 + clearance_volume_m3) / clearance_volume_m3
        compression_ratio_ref = float(str(comp_params["compression_ratio"]["value"]).split(":")[0])
        if compression_ratio_ref > 0.0:
            rel_error = abs(compression_ratio - compression_ratio_ref) / compression_ratio_ref
            if rel_error > 0.01:
                raise ValueError(
                    "Compression ratio mismatch: computed "
                    f"{compression_ratio:.3f} vs reference {compression_ratio_ref:.3f}."
                )
        return EngineGeometry(
            bore_m=bore_m,
            stroke_m=stroke_m,
            rod_length_m=float(crank_params["rod_length"]["value"]) * 1e-3,
            crank_radius_m=float(crank_params["crank_radius"]["value"]) * 1e-3,
            offset_m=float(crank_params["cylinder_offset"]["value"]) * 1e-3,
            bowl_volume_m3=bowl_volume_m3,
            head_recess_m3=head_recess_m3,
            gasket_thickness_m=gasket_thickness_m,
            piston_protrusion_m=piston_protrusion_m,
            compression_ratio=compression_ratio,
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
