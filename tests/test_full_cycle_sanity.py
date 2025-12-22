import unittest

from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle
from virtual_tdi.models import EngineGeometry, Fuel, InjectionSchedule, SimulationConfig
from virtual_tdi.valvetrain import ValveTiming


class TestFullCycleSanity(unittest.TestCase):
    def test_default_config_has_boundaries_and_valve_flow(self):
        cfg = FullCycleConfig(rpm=1500.0)
        self.assertIsNotNone(cfg.boundaries)
        self.assertGreater(cfg.valve_flow.intake_valve_diameter_m, 0.0)
        self.assertGreater(cfg.valve_flow.exhaust_valve_diameter_m, 0.0)

    def test_runs_and_positive_imep(self):
        bore = 79.5e-3
        stroke = 95.5e-3
        geom = EngineGeometry(
            bore_m=bore,
            stroke_m=stroke,
            rod_length_m=144e-3,
            crank_radius_m=stroke / 2.0,
            offset_m=0.5e-3,
            compression_ratio=19.5,
            cylinders=4,
        )
        fuel = Fuel.diesel()
        schedule = InjectionSchedule(
            soi_pilot_deg=-12.0,
            soi_main_deg=-6.0,
            pilot_fraction=0.12,
            duration_pilot_deg=8.0,
            duration_main_deg=42.0,
        )
        models = SimulationConfig(
            rpm=1500.0,
            step_deg=2.0,
            fuel_mg_per_cycle_per_cyl=15.0,
            thermo_backend="simple",
            flow_backend="simple",
            strict_backends=False,
        )
        cfg = FullCycleConfig(
            rpm=1500.0,
            step_deg=2.0,
            cycles=1,
            boundaries=BoundaryConditions(intake_pressure_pa=1.0e5, intake_temp_k=300.0, exhaust_pressure_pa=1.15e5, exhaust_temp_k=800.0),
            valve_timing=ValveTiming(),
            fuel_mg_per_cycle_per_cyl=15.0,
            models=models,
        )
        result = simulate_full_cycle(geom, fuel, schedule, cfg)
        self.assertIn("imep_pa", result.metrics)
        self.assertGreater(result.metrics["peak_pressure_pa"], 1.0e5)
        self.assertGreater(result.metrics["imep_pa"], 1.0e4)


if __name__ == "__main__":
    unittest.main()
