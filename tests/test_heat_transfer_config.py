import unittest

from virtual_tdi.config_loader import (
    create_heat_transfer_config_from_config,
    load_yaml_config,
)
from virtual_tdi.models import HeatTransferConfig


class TestHeatTransferConfigFromYaml(unittest.TestCase):
    def setUp(self):
        self.config = load_yaml_config("engine_reference_sources.yaml")

    def test_reads_wall_temperatures_from_yaml(self):
        ht = create_heat_transfer_config_from_config(self.config)
        self.assertEqual(ht.head_temp_k, 500.0)
        self.assertEqual(ht.piston_temp_k, 550.0)
        self.assertEqual(ht.liner_temp_k, 450.0)

    def test_missing_section_falls_back_to_defaults(self):
        stripped = {"parameters": {}}
        ht = create_heat_transfer_config_from_config(stripped)
        self.assertEqual(ht, HeatTransferConfig())

    def test_invalid_section_raises_value_error(self):
        with self.assertRaises(ValueError):
            create_heat_transfer_config_from_config({"parameters": {"heat_transfer": {"head_wall_temp": {}}}})


if __name__ == "__main__":
    unittest.main()
