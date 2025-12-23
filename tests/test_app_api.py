import unittest
from pathlib import Path

from virtual_tdi import core as app_api


class TestAppApi(unittest.TestCase):
    def test_build_and_run_closed_cycle(self) -> None:
        engine_cfg = app_api.load_engine_config(Path("engine_reference_sources.yaml"))
        case = app_api.build_case(
            engine_cfg,
            {
                "mode": "closed",
                "rpm": 1500.0,
                "fuel": "diesel",
                "fuel_mg": 10.0,
                "step_deg": 2.0,
                "integrator": "rk4",
                "thermo_backend": "simple",
                "flow_backend": "simple",
                "strict_backends": False,
            },
        )
        res = app_api.run_case(case)
        self.assertTrue(hasattr(res, "metrics"))
        self.assertIn("peak_pressure_bar", res.metrics)
