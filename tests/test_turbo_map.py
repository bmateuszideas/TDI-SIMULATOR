import unittest
from pathlib import Path

from virtual_tdi.turbo_map import TurboMapModel

ROOT = Path(__file__).resolve().parent.parent


class TestTurboMapModel(unittest.TestCase):
    def setUp(self):
        self.tm = TurboMapModel.from_yaml(ROOT / "validation" / "turbo_map_gt1749v.yaml")

    def test_loads_map_shape(self):
        self.assertEqual(self.tm.speed_rpm.shape, (6,))
        self.assertEqual(self.tm.mass_kg_s.shape, (6, 6))
        self.assertEqual(self.tm.eff_map.shape, (6, 6))

    def test_compressor_efficiency_in_physical_range(self):
        for N in (60000, 120000, 180000, 210000):
            for pr in (1.2, 1.8, 2.6):
                eff = self.tm.compressor_efficiency(N, pr)
                self.assertGreaterEqual(eff, 0.3)
                self.assertLessEqual(eff, 0.85)

    def test_interpolation_clips_outside_envelope(self):
        # Outside the mapped envelope the value clips to the boundary, no NaN.
        eff = self.tm.compressor_efficiency(300000, 5.0)
        self.assertFalse(eff != eff)
        eff2 = self.tm.compressor_efficiency(10000, 1.05)
        self.assertGreater(eff2, 0.0)

    def test_compressor_mass_flow_grows_with_speed_and_falls_with_pr(self):
        m_low = self.tm.compressor_mass_kg_s(90000, 1.5)
        m_high = self.tm.compressor_mass_kg_s(210000, 1.5)
        self.assertGreater(m_high, m_low)
        m_low_pr = self.tm.compressor_mass_kg_s(150000, 1.2)
        m_high_pr = self.tm.compressor_mass_kg_s(150000, 3.0)
        self.assertGreater(m_low_pr, m_high_pr)

    def test_turbine_efficiency_interpolates(self):
        e1 = self.tm.turbine_efficiency(1.3)
        e2 = self.tm.turbine_efficiency(1.8)
        self.assertAlmostEqual(e1, 0.66, places=6)
        self.assertAlmostEqual(e2, 0.72, places=6)

    def test_powers_positive_and_mass_consistent(self):
        # 0.05 kg/s at PR 1.8, 100k rpm
        p_comp = self.tm.compressor_power_w(100000, 1.8, 0.05)
        self.assertGreater(p_comp, 1000.0)
        self.assertLess(p_comp, 20000.0)
        p_turb = self.tm.turbine_power_w(1.8, 100000, 800.0,
                                         mdot_exhaust_kg_s=0.052)
        self.assertGreater(p_turb, 1000.0)
        # explicit exhaust mass flow overrides swallowing factor
        p_fallback = self.tm.turbine_power_w(1.8, 100000, 800.0)
        self.assertGreater(abs(p_fallback - p_turb), 1.0)

    def test_invalid_map_shape_raises(self):
        import tempfile
        import yaml
        data = yaml.safe_load((ROOT / "validation" / "turbo_map_gt1749v.yaml").read_text())
        data["corrected_mass_kg_s"]["values"] = [[0.1, 0.2]]  # wrong shape
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(data, f)
            path = f.name
        with self.assertRaises(ValueError):
            TurboMapModel.from_yaml(path)


if __name__ == "__main__":
    unittest.main()
