import unittest

from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle
from virtual_tdi.models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig
from virtual_tdi.vp37_cam import VP37CamProfile


class TestFullCycleVP37HRR(unittest.TestCase):
    def test_runs_with_vp37_main_hrr(self):
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
            duration_main_deg=25.0,
        )
        cam = VP37CamProfile.from_csv("skok_tloczka_vp37_de110.csv")
        models = SimulationConfig(
            rpm=1500.0,
            step_deg=2.0,
            fuel_mg_per_cycle_per_cyl=20.0,
            combustion=CombustionConfig(hrr_model="vp37_main"),
            thermo_backend="simple",
            flow_backend="simple",
            strict_backends=False,
        )
        cfg = FullCycleConfig(
            rpm=1500.0,
            step_deg=2.0,
            cycles=1,
            boundaries=BoundaryConditions(intake_pressure_pa=1.0e5, intake_temp_k=300.0, exhaust_pressure_pa=1.15e5, exhaust_temp_k=800.0),
            fuel_mg_per_cycle_per_cyl=20.0,
            models=models,
            vp37_cam_profile=cam,
        )
        res = simulate_full_cycle(geom, fuel, schedule, cfg)
        self.assertGreater(res.metrics["peak_pressure_bar"], 1.0)
        self.assertTrue(hasattr(res, "dm_fuel_main_mg_per_deg"))


if __name__ == "__main__":
    unittest.main()
