import unittest

from virtual_tdi.flow import orifice_mdot_kg_per_s
from virtual_tdi.models import SimulationConfig
from virtual_tdi.thermo import GasModel


def _has_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


HAS_FLUIDS = _has_module("fluids")
HAS_COOLPROP = _has_module("CoolProp")


class TestBackendFallbacks(unittest.TestCase):
    @unittest.skipUnless(HAS_FLUIDS, "fluids not installed")
    def test_flow_backend_fluids_fallback(self):
        mdot = orifice_mdot_kg_per_s(
            p_up_pa=2.0e5,
            t_up_k=300.0,
            p_down_pa=1.0e5,
            gamma=1.35,
            r_j_per_kg_k=287.0,
            area_m2=1.0e-5,
            discharge_coeff=0.7,
            backend="fluids",
            strict=True,
        )
        self.assertGreaterEqual(mdot, 0.0)

    @unittest.skipUnless(HAS_COOLPROP, "CoolProp not installed")
    def test_thermo_backend_coolprop_fallback(self):
        cfg = SimulationConfig(rpm=1500.0, thermo_backend="coolprop", strict_backends=True)
        g = GasModel().gamma(600.0, cfg, pressure_pa=1.0e5)
        self.assertGreater(g, 1.0)

if __name__ == "__main__":
    unittest.main()
