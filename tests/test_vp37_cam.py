import unittest

from virtual_tdi.injection import VP37CamProfile


class TestVP37Cam(unittest.TestCase):
    def test_duration_monotone(self):
        cam = VP37CamProfile.from_csv("skok_tloczka_vp37_de110.csv")
        d10 = cam.duration_main_crank_deg(iq_mg_per_stroke=10.0, cylinder=1, iq_max_mg=51.0, delivery_start_frac=0.4)
        d20 = cam.duration_main_crank_deg(iq_mg_per_stroke=20.0, cylinder=1, iq_max_mg=51.0, delivery_start_frac=0.4)
        d50 = cam.duration_main_crank_deg(iq_mg_per_stroke=50.0, cylinder=1, iq_max_mg=51.0, delivery_start_frac=0.4)
        self.assertGreater(d20, d10)
        self.assertGreater(d50, d20)
        self.assertGreater(d10, 0.0)
        self.assertLess(d50, 200.0)


if __name__ == "__main__":
    unittest.main()

