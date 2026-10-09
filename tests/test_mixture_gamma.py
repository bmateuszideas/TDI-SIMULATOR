"""Tests for the burned-gas mixture gamma(T,x) model (TODO.md Faza 2.B.1)."""
import unittest

from virtual_tdi.models import SimulationConfig
from virtual_tdi.thermo import GasModel


class TestMixtureGamma(unittest.TestCase):
    def setUp(self):
        self.gas = GasModel()
        self.cfg = SimulationConfig(rpm=1500.0, thermo_backend="simple")

    def test_gamma_unburned_unchanged(self):
        g_air = self.gas.gamma(300.0, self.cfg)
        g_x0 = self.gas.gamma(300.0, self.cfg, burned_fraction=0.0)
        self.assertAlmostEqual(g_air, g_x0, places=12)

    def test_gamma_falls_with_burned_fraction(self):
        g0 = self.gas.gamma(800.0, self.cfg, burned_fraction=0.0)
        g1 = self.gas.gamma(800.0, self.cfg, burned_fraction=1.0)
        self.assertGreater(g0, g1)
        # Between endpoints, monotone
        g05 = self.gas.gamma(800.0, self.cfg, burned_fraction=0.5)
        self.assertGreater(g0, g05)
        self.assertGreater(g05, g1)

    def test_cp_rises_with_burned_fraction(self):
        cp0 = self.gas.cp(800.0, self.cfg, burned_fraction=0.0)
        cp1 = self.gas.cp(800.0, self.cfg, burned_fraction=1.0)
        self.assertGreater(cp1, cp0)
        self.assertAlmostEqual(cp1 - cp0, 110.0, delta=25.0)

    def test_cv_consistency(self):
        for x in (0.0, 0.5, 1.0):
            cp = self.gas.cp(1000.0, self.cfg, burned_fraction=x)
            cv = self.gas.cv(1000.0, self.cfg, burned_fraction=x)
            g = self.gas.gamma(1000.0, self.cfg, burned_fraction=x)
            self.assertAlmostEqual(cp / cv, g, places=9)

    def test_fraction_clipped(self):
        g_over = self.gas.gamma(500.0, self.cfg, burned_fraction=5.0)
        g_one = self.gas.gamma(500.0, self.cfg, burned_fraction=1.0)
        self.assertAlmostEqual(g_over, g_one, places=12)
        g_neg = self.gas.gamma(500.0, self.cfg, burned_fraction=-0.5)
        g_zero = self.gas.gamma(500.0, self.cfg, burned_fraction=0.0)
        self.assertAlmostEqual(g_neg, g_zero, places=12)


if __name__ == "__main__":
    unittest.main()
