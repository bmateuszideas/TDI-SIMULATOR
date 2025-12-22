
import unittest
from pathlib import Path
import yaml
import os
import csv

from virtual_tdi.dataset import main as dataset_main

class TestDatasetConfig(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("test_temp_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.config_path = self.test_dir / "test_engine_config.yaml"
        self.output_csv_path = self.test_dir / "test_output.csv"
        
        config_data = {
            "parameters": {
                "cranktrain": {
                    "bore": {"value": 80.0, "unit": "mm"},
                    "stroke": {"value": 96.0, "unit": "mm"},
                    "rod_length": {"value": 145.0, "unit": "mm"},
                    "crank_radius": {"value": 48.0, "unit": "mm"},
                    "cylinder_offset": {"value": 0.6, "unit": "mm"}
                },
                "combustion_chamber": {
                    "compression_ratio": {"value": "20.0:1"},
                    "bowl_volume": {"value": 17.0, "unit": "cm3"},
                    "head_recess_volume": {"value": 4.4, "unit": "cm3"},
                    "gasket_thickness": {"value": 1.5, "unit": "mm"},
                    "piston_protrusion": {"value": 0.7, "unit": "mm"},
                    "total_cylinders": {"value": 4}
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def tearDown(self):
        if self.config_path.exists():
            self.config_path.unlink()
        if self.output_csv_path.exists():
            self.output_csv_path.unlink()
        if self.test_dir.exists():
            os.rmdir(self.test_dir)

    def test_dataset_generation_with_custom_config(self):
        # Prepare arguments for the dataset main function
        args = [
            "--engine-config", str(self.config_path),
            "--out", str(self.output_csv_path),
            "--n", "1",
            "--rpm-min", "1000",
            "--rpm-max", "1000",
        ]
        
        # Run the dataset generation
        return_code = dataset_main(args)
        
        # Check that the process completed successfully
        self.assertEqual(return_code, 0)
        
        # Check if the output CSV was created
        self.assertTrue(self.output_csv_path.exists())
        
        # Check the content of the CSV
        with open(self.output_csv_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertIn("out_peak_pressure_pa", header)
            data = next(reader)
            self.assertEqual(len(data), len(header))

if __name__ == "__main__":
    unittest.main()
