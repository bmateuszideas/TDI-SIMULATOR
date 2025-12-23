import unittest

from virtual_tdi.engine_model import Fuel


class TestFuels(unittest.TestCase):
    def test_from_name_known(self) -> None:
        self.assertEqual(Fuel.from_name("diesel").name.lower(), "diesel")
        self.assertIn("SVO", Fuel.from_name("svo").name)
        self.assertIn("Biodiesel", Fuel.from_name("biodiesel").name)

    def test_custom_requires_params(self) -> None:
        with self.assertRaises(ValueError):
            Fuel.from_name("custom")

    def test_custom_builds(self) -> None:
        f = Fuel.from_name("custom", density_kgm3=900.0, bulk_modulus_bar=18000.0, lhv_mjkg=42.0)
        self.assertEqual(f.name, "Custom")
        self.assertAlmostEqual(f.density_kg_per_m3, 900.0, places=6)
        self.assertAlmostEqual(f.bulk_modulus_pa, 18000.0 * 1e5, places=3)
        self.assertAlmostEqual(f.lhv_j_per_kg, 42.0 * 1e6, places=3)

    def test_density_correction(self) -> None:
        f = Fuel.diesel()
        f2 = f.with_density_correction(80.0)
        self.assertLess(f2.density_kg_per_m3, f.density_kg_per_m3)

