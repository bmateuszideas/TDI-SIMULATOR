import unittest

from virtual_tdi.dataset import DatasetConfig, generate_dataset


class TestDataset(unittest.TestCase):
    def test_generate_small_dataset(self):
        cfg = DatasetConfig(
            n=3,
            seed=1,
            rpm_min=1500.0,
            rpm_max=1500.0,
            step_deg=5.0,
            cycles=1,
            ecu_mode="off",
            thermo_backend="simple",
            flow_backend="simple",
            ignition_delay_model="arrhenius",
            strict_backends=False,
            integrator="rk4",
        )
        rows = generate_dataset(cfg, out_csv=None)
        self.assertEqual(len(rows), 3)
        self.assertIn("out_peak_pressure_pa", rows[0])
        self.assertIn("iq_eff_mg_per_str", rows[0])
        self.assertIn("nozzle_diameter_mm", rows[0])


if __name__ == "__main__":
    unittest.main()
