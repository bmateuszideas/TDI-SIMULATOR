import unittest

from virtual_tdi.physics import NozzleConfig, VP37HydraulicConfig, estimate_pilot_ratio
from virtual_tdi.engine_model import Fuel
from virtual_tdi.injection import VP37CamProfile


class TestHydraulics(unittest.TestCase):
    def test_pilot_ratio_bounds(self):
        cam = VP37CamProfile.from_csv("skok_tloczka_vp37_de110.csv")
        fuel = Fuel.diesel()
        duration = cam.duration_main_crank_deg(
            iq_mg_per_stroke=20.0,
            cylinder=1,
            iq_max_mg=51.0,
            delivery_start_frac=0.40,
        )
        ratio = estimate_pilot_ratio(
            cam,
            rpm=1500.0,
            duration_main_deg=duration,
            fuel=fuel,
            nozzle=NozzleConfig(),
            hyd=VP37HydraulicConfig(),
            cylinder=1,
        )
        self.assertGreaterEqual(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)
        self.assertGreater(ratio, 0.0)

    def test_pilot_ratio_zero_duration(self):
        cam = VP37CamProfile.from_csv("skok_tloczka_vp37_de110.csv")
        ratio = estimate_pilot_ratio(
            cam,
            rpm=1500.0,
            duration_main_deg=0.0,
            fuel=Fuel.diesel(),
            nozzle=NozzleConfig(),
            hyd=VP37HydraulicConfig(),
            cylinder=1,
        )
        self.assertEqual(ratio, 0.0)


if __name__ == "__main__":
    unittest.main()
