import pytest
from pathlib import Path
from virtual_tdi.core import (
    load_yaml_config,
    create_geometry_from_config,
    create_manifold_configs_from_config,
    create_intercooler_config_from_config,
    create_valve_flow_from_config,
)
from virtual_tdi.engine_model import EngineGeometry, ManifoldConfig, IntercoolerConfig
from virtual_tdi.physics import ValveFlow


# Path to the reference YAML file (adjust if needed)
REFERENCE_YAML_PATH = Path(__file__).parent.parent / "engine_reference_sources.yaml"

@pytest.fixture(scope="module")
def engine_config():
    """Loads the engine reference config once for all tests."""
    return load_yaml_config(REFERENCE_YAML_PATH)

def test_config_file_exists():
    """Ensures the engine_reference_sources.yaml file exists."""
    assert REFERENCE_YAML_PATH.exists(), f"Reference YAML file not found at {REFERENCE_YAML_PATH}"

def test_load_yaml_config_valid():
    """Tests if the YAML config can be loaded successfully."""
    config = load_yaml_config(REFERENCE_YAML_PATH)
    assert isinstance(config, dict)
    assert "engine" in config
    assert "parameters" in config

def test_create_geometry_from_config_valid(engine_config):
    """Tests if EngineGeometry can be created successfully from the config."""
    geometry = create_geometry_from_config(engine_config)
    assert isinstance(geometry, EngineGeometry)
    # Check a few key fields for correct type and non-zero value
    assert isinstance(geometry.bore_m, float) and geometry.bore_m > 0
    assert isinstance(geometry.bowl_volume_m3, float)
    assert isinstance(geometry.cylinders, int) and geometry.cylinders > 0

def test_create_manifold_configs_from_config_valid(engine_config):
    """Tests if ManifoldConfig objects can be created successfully."""
    manifolds = create_manifold_configs_from_config(engine_config)
    assert isinstance(manifolds, dict)
    assert "intake" in manifolds and isinstance(manifolds["intake"], ManifoldConfig)
    assert "exhaust" in manifolds and isinstance(manifolds["exhaust"], ManifoldConfig)
    assert manifolds["intake"].volume_m3 > 0
    assert manifolds["exhaust"].volume_m3 > 0

def test_create_intercooler_config_from_config_valid(engine_config):
    """Tests if IntercoolerConfig can be created successfully."""
    intercooler = create_intercooler_config_from_config(engine_config)
    assert isinstance(intercooler, IntercoolerConfig)
    assert intercooler.mass_al_kg > 0
    assert intercooler.h_ambient_w_per_m2_k_base >= 0

def test_create_valve_flow_from_config_valid(engine_config):
    """Tests if ValveFlow can be created successfully."""
    valve_flow = create_valve_flow_from_config(engine_config)
    assert isinstance(valve_flow, ValveFlow)
    assert valve_flow.intake_valve_diameter_m > 0
    assert valve_flow.exhaust_max_lift_m >= 0

# Test for missing/invalid parameters (example)
def test_create_geometry_missing_key_raises_error():
    """Tests that a KeyError is raised for missing geometry parameters."""
    invalid_config = load_yaml_config(REFERENCE_YAML_PATH)
    # Temporarily remove a required key
    del invalid_config["parameters"]["cranktrain"]["bore"]
    with pytest.raises(ValueError, match="Invalid or missing key in engine config for geometry"):
        create_geometry_from_config(invalid_config)

# TODO: Add more tests for:
# - Invalid data types (e.g., string for a float value)
# - Missing top-level sections (e.g., 'cranktrain' or 'valvetrain')
# - Correct unit conversions (e.g., checking values after conversion)
# - Loading of other config types as they are implemented (FrictionModel, CompressorMap, VntMap, etc.)
# - Test for parameter ranges (e.g., efficiency between 0 and 1)
