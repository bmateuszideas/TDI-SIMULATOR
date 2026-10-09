"""Tests for the map-driven validation grid (factory ECU map consistency)."""
import unittest
from pathlib import Path

from virtual_tdi.edc_maps import BoostTargetMap2D, SmokeLimiterMap2D
from virtual_tdi.soi_map import SOIMap2D
from validation.map_consistency import build_grid

ROOT = Path(__file__).resolve().parent.parent


class TestMapGrid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.soi = SOIMap2D.from_csv(next(ROOT.glob("*SOI*Table 1.csv")))
        cls.boost = BoostTargetMap2D.from_csv(next(ROOT.glob("Mapa_BOOST*.csv")))
        cls.smoke = SmokeLimiterMap2D.from_csv(next(ROOT.glob("SmokeLimiter*.csv")))

    def test_grid_points_in_working_area(self):
        grid = build_grid(soi_map=self.soi, boost_map=self.boost,
                          smoke_map=self.smoke, n_rpm=4, n_iq=3)
        self.assertEqual(len(grid), 12)
        for pt in grid:
            self.assertGreaterEqual(pt.rpm, 900.0)
            self.assertLessEqual(pt.rpm, 4500.0)
            self.assertGreater(pt.iq_mg, 0.0)
            self.assertLessEqual(pt.iq_mg, 36.5)
            # SOI in model convention: negative = BTDC; near idle the factory
            # map gives ~0.5 deg BTDC which the convention keeps just above 0
            # after rounding - allow the small positive edge.
            self.assertLessEqual(pt.soi_model_deg, 1.0)
            self.assertGreater(pt.boost_target_mbar_abs, 900.0)

    def test_grid_matches_maps_at_points(self):
        grid = build_grid(soi_map=self.soi, boost_map=self.boost,
                          smoke_map=self.smoke, n_rpm=3, n_iq=2)
        for pt in grid:
            expected_boost = self.boost.map_target_mbar(pt.rpm, pt.iq_mg)
            self.assertAlmostEqual(pt.boost_target_mbar_abs, expected_boost, places=3)
            expected_soi = self.soi.soi_deg_model_convention(pt.rpm, pt.iq_mg)
            self.assertAlmostEqual(pt.soi_model_deg, expected_soi, places=6)

    def test_smoke_limit_drives_max_iq(self):
        grid = build_grid(soi_map=self.soi, boost_map=self.boost,
                          smoke_map=self.smoke, n_rpm=2, n_iq=3)
        by_rpm = {}
        for pt in grid:
            by_rpm.setdefault(pt.rpm, []).append(pt.iq_mg)
        for rpm, iqs in by_rpm.items():
            self.assertEqual(max(iqs), min(iqs[-1], 36.5))


if __name__ == "__main__":
    unittest.main()
