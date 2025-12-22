import unittest

from virtual_tdi.coupled import simulate_coupled_turbo
from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig
from virtual_tdi.models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig
from virtual_tdi.turbo import TurboConfig


class TestTurboCoupled(unittest.TestCase):
    def test_runs(self):
        geom = EngineGeometry(
            bore_m=79.5e-3,
            stroke_m=95.5e-3,
            rod_length_m=144e-3,
            crank_radius_m=95.5e-3 / 2.0,
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
            duration_main_deg=25.0,
        )
        cfg = FullCycleConfig(
            rpm=1500.0,
            step_deg=2.0,
            cycles=1,
            boundaries=BoundaryConditions(intake_pressure_pa=1.0e5, intake_temp_k=300.0, exhaust_pressure_pa=1.15e5, exhaust_temp_k=800.0),
            fuel_mg_per_cycle_per_cyl=15.0,
            models=SimulationConfig(
                rpm=1500.0,
                step_deg=2.0,
                fuel_mg_per_cycle_per_cyl=15.0,
                combustion=CombustionConfig(hrr_model="wiebe"),
                thermo_backend="simple",
                flow_backend="simple",
                strict_backends=False,
            ),
        )
        turbo_cfg = TurboConfig(p_amb_pa=1.0e5, t_amb_k=300.0, pr_max=2.0)
        res = simulate_coupled_turbo(geom, fuel, schedule, cfg, turbo_cfg, iterations=2)
        self.assertGreater(res.result.metrics["peak_pressure_pa"], 1.0e5)
        self.assertTrue(len(res.history) >= 1)


if __name__ == "__main__":
    unittest.main()
