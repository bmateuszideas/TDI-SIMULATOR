import unittest
from pathlib import Path
import numpy as np

from virtual_tdi.config_loader import create_geometry_from_config, load_yaml_config, create_manifold_configs_from_config
from virtual_tdi.full_cycle import FullCycleConfig, simulate_full_cycle
from virtual_tdi.models import (
    CombustionConfig,
    EngineGeometry,
    Fuel,
    InjectionSchedule,
    SimulationConfig,
    ManifoldConfig,
)
from virtual_tdi.valvetrain import ValveFlow, ValveTiming
from virtual_tdi.lift_table import ValveLiftTable

class TestFullCycleDynamicManifolds(unittest.TestCase):

    def setUp(self):
        """Set up a basic configuration for the full cycle simulation."""
        self.engine_config = load_yaml_config("engine_reference_sources.yaml")
        self.geom = create_geometry_from_config(self.engine_config)
        self.fuel = Fuel.diesel()
        
        self.schedule = InjectionSchedule(
            soi_pilot_deg=-10.0, soi_main_deg=-2.0, pilot_fraction=0.1,
            duration_pilot_deg=5.0, duration_main_deg=20.0,
        )

        manifold_configs = create_manifold_configs_from_config(self.engine_config)
        self.intake_manifold_config = ManifoldConfig(
            volume_m3=manifold_configs['intake'].volume_m3,
            initial_temp_k=300.0, initial_pressure_pa=1.0e5,
        )
        self.exhaust_manifold_config = ManifoldConfig(
            volume_m3=manifold_configs['exhaust'].volume_m3,
            initial_temp_k=500.0, initial_pressure_pa=1.1e5,
        )
        
        self.valve_table = ValveLiftTable.from_markdown("profil_krzywek_4cylindry.md")
        models = SimulationConfig(rpm=1500.0, integrator='rk4')

        self.cfg = FullCycleConfig(
            rpm=1500.0, cycles=4, # Use a few more cycles for temperatures to stabilize
            intake_manifold_config=self.intake_manifold_config,
            exhaust_manifold_config=self.exhaust_manifold_config,
            p_ambient_pa=1.0e5, t_ambient_k=300.0,
            valve_lift_table=self.valve_table, models=models,
        )

    def test_simulation_runs_and_produces_plausible_results(self):
        """
        Test that the simulation with dynamic manifolds (mass and energy)
        runs without crashing and that the results are physically plausible.
        """
        result = simulate_full_cycle(self.geom, self.fuel, self.schedule, self.cfg)

        self.assertIsNotNone(result)
        self.assertEqual(len(result.theta_deg), len(result.p_intake_pa))
        self.assertEqual(len(result.theta_deg), len(result.t_intake_k))
        self.assertEqual(len(result.theta_deg), len(result.p_exhaust_pa))
        self.assertEqual(len(result.theta_deg), len(result.t_exhaust_k))

        # Check for NaNs or Infs in key results
        for arr_name in ["pressure_pa", "temperature_k", "p_intake_pa", "t_intake_k", "p_exhaust_pa", "t_exhaust_k"]:
            arr = getattr(result, arr_name)
            self.assertFalse(np.any(np.isnan(arr)), f"{arr_name} contains NaN values")
            self.assertFalse(np.any(np.isinf(arr)), f"{arr_name} contains Inf values")

        # Basic plausibility checks
        self.assertGreater(result.metrics["peak_pressure_bar"], 30.0)
        self.assertGreater(result.metrics["m_air_in_kg_per_cyl"], 1e-4)

        # Mean intake pressure should be around ambient pressure
        mean_intake_bar = result.metrics["p_intake_mean_bar"]
        self.assertAlmostEqual(mean_intake_bar, 1.0, delta=0.1, msg="Intake pressure should settle near ambient")

        # Mean exhaust pressure should be slightly above ambient
        mean_exhaust_bar = result.metrics["p_exhaust_mean_bar"]
        self.assertGreater(mean_exhaust_bar, 1.0, msg="Exhaust pressure should be above ambient")

        # Mean intake temperature should be close to ambient
        mean_intake_temp_k = result.metrics["t_intake_mean_k"]
        self.assertAlmostEqual(mean_intake_temp_k, self.cfg.t_ambient_k, delta=20, msg="Intake temp should settle near ambient")
        
        # Mean exhaust temperature should be significantly higher than ambient
        mean_exhaust_temp_k = result.metrics["t_exhaust_mean_k"]
        self.assertGreater(mean_exhaust_temp_k, 500.0, msg="Exhaust temp should be high")

    def test_intake_egr_fraction_increases_with_overlap_backflow(self):
        valve_timing = ValveTiming(ivo_deg=-20.0, ivc_deg=200.0, evo_deg=-200.0, evc_deg=20.0)
        intake_config = ManifoldConfig(
            volume_m3=self.intake_manifold_config.volume_m3,
            initial_temp_k=300.0,
            initial_pressure_pa=0.8e5,
            initial_egr_fraction=0.0,
        )
        exhaust_config = ManifoldConfig(
            volume_m3=self.exhaust_manifold_config.volume_m3,
            initial_temp_k=800.0,
            initial_pressure_pa=1.6e5,
            initial_egr_fraction=1.0,
        )
        models = SimulationConfig(rpm=1200.0, integrator="rk4")
        cfg = FullCycleConfig(
            rpm=1200.0,
            cycles=2,
            step_deg=1.0,
            intake_manifold_config=intake_config,
            exhaust_manifold_config=exhaust_config,
            p_ambient_pa=0.8e5,
            t_ambient_k=300.0,
            valve_timing=valve_timing,
            models=models,
        )

        result = simulate_full_cycle(self.geom, self.fuel, self.schedule, cfg)

        self.assertGreater(np.max(result.egr_intake_frac), intake_config.initial_egr_fraction)
        self.assertTrue(np.all((result.egr_intake_frac >= 0.0) & (result.egr_intake_frac <= 1.0)))
        self.assertTrue(np.all((result.egr_exhaust_frac >= 0.0) & (result.egr_exhaust_frac <= 1.0)))
        self.assertTrue(np.all((result.egr_cylinder_frac >= 0.0) & (result.egr_cylinder_frac <= 1.0)))


if __name__ == "__main__":
    unittest.main()
