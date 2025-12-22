import unittest

from virtual_tdi.fmep import calculate_fmep_pa
from virtual_tdi.models import EngineGeometry, Fuel, InjectionSchedule, SimulationConfig
from virtual_tdi.solver import simulate_closed_cycle


class TestSolverSanity(unittest.TestCase):
    def test_runs_and_outputs_metrics(self):
        bore = 79.5e-3
        stroke = 95.5e-3
        geom = EngineGeometry(
            bore_m=bore,
            stroke_m=stroke,
            rod_length_m=144e-3,
            crank_radius_m=stroke / 2.0,
            offset_m=0.5e-3,
            bowl_volume_m3=17.5e-6,
            head_recess_m3=4.5e-6,
            gasket_thickness_m=1.53e-3,
            piston_protrusion_m=0.8e-3,
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
        cfg = SimulationConfig(
            rpm=1500.0,
            step_deg=1.0,
            fuel_mg_per_cycle_per_cyl=10.0,
            thermo_backend="simple",
            flow_backend="simple",
            strict_backends=False,
        )
        result = simulate_closed_cycle(geom, fuel, schedule, cfg)
        self.assertIn("peak_pressure_bar", result.metrics)
        self.assertGreater(result.metrics["peak_pressure_bar"], 1.0)

    def test_fmep_trend_with_rpm(self):
        imep_bar = 6.0
        pmax_bar = 80.0
        a_bar = 0.6
        b_bar_per_krpm = 0.4
        c_bar_per_bar = 0.01

        fmep_low = calculate_fmep_pa(
            rpm=1500.0,
            pmax_pa=pmax_bar * 1e5,
            a_bar=a_bar,
            b_bar_per_krpm=b_bar_per_krpm,
            c_bar_per_bar=c_bar_per_bar,
        )
        fmep_high = calculate_fmep_pa(
            rpm=3000.0,
            pmax_pa=pmax_bar * 1e5,
            a_bar=a_bar,
            b_bar_per_krpm=b_bar_per_krpm,
            c_bar_per_bar=c_bar_per_bar,
        )
        self.assertGreaterEqual(fmep_low, 0.0)
        self.assertGreaterEqual(fmep_high, 0.0)

        bmep_low = imep_bar - fmep_low / 1e5
        bmep_high = imep_bar - fmep_high / 1e5
        self.assertGreater(bmep_low, bmep_high)


if __name__ == "__main__":
    unittest.main()
