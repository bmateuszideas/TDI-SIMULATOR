import unittest

from virtual_tdi.injection import SOIMap2D


class TestSOIMap(unittest.TestCase):
    def test_parses_and_interpolates(self):
        m = SOIMap2D.from_csv("Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv")
        self.assertGreaterEqual(m.rpm_axis.size, 5)
        self.assertGreaterEqual(m.iq_axis_mg_per_str.size, 5)

        # Known grid point: 1491 rpm, 20 mg/suw -> 0.1° BTDC (approx), so model should return about -0.1°.
        soi = m.soi_deg_model_convention(1491.0, 20.0)
        self.assertAlmostEqual(soi, -0.1, places=2)

        # Interpolation should be finite
        soi2 = m.soi_deg_model_convention(1600.0, 18.0)
        self.assertTrue(abs(soi2) < 50.0)


if __name__ == "__main__":
    unittest.main()

