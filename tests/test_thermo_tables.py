import unittest

from virtual_tdi.models import SimulationConfig
from virtual_tdi.thermo import GasModel, _coolprop_tables, _coolprop_rho_t_tables


class TestThermoCoolPropTables(unittest.TestCase):
    def setUp(self):
        try:
            import CoolProp  # noqa: F401
        except Exception:
            raise unittest.SkipTest("CoolProp not installed")
        self.cfg = SimulationConfig(rpm=1500.0, thermo_backend="coolprop")
        self.gas = GasModel()

    def test_tables_build(self):
        self.assertIsNotNone(_coolprop_tables("Air"))
        self.assertIsNotNone(_coolprop_rho_t_tables("Air"))

    def test_gamma_close_to_coolprop(self):
        import CoolProp.CoolProp as cp

        for t, p in [(300.0, 1.0e5), (800.0, 30.0e5), (1500.0, 80.0e5)]:
            exact = cp.PropsSI("Cpmass", "T", t, "P", p, "Air") / cp.PropsSI(
                "Cvmass", "T", t, "P", p, "Air"
            )
            approx = self.gas.gamma(t, self.cfg, pressure_pa=p)
            self.assertLess(abs(approx - exact) / exact, 0.02, msg=f"T={t} P={p}")

    def test_pressure_from_rhoT_close(self):
        import CoolProp.CoolProp as cp

        for rho, t in [(1.2, 300.0), (20.0, 600.0)]:
            exact = cp.PropsSI("P", "T", t, "Dmass", rho, "Air")
            approx = self.gas.pressure_from_rhoT(rho, t, self.cfg)
            self.assertLess(abs(approx - exact) / exact, 0.02, msg=f"rho={rho} T={t}")

    def test_lookup_far_outside_grid_is_clamped(self):
        g = self.gas.gamma(100.0, self.cfg, pressure_pa=1.0)
        self.assertGreater(g, 1.0)
        self.assertLess(g, 2.0)


if __name__ == "__main__":
    unittest.main()
