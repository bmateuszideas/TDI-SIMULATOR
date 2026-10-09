import unittest

from virtual_tdi.cli import _make_argparser


def _args(cmd):
    return _make_argparser().parse_args(cmd)


class TestCliRegression(unittest.TestCase):
    """Regression guards for CLI paths that previously crashed (N-01, N-02).

    These tests only verify that argument combinations parse and that the
    affected code paths import/construct their dependencies without
    placeholder (`...`) arguments or missing names. Full runs are covered
    by the integration smoke commands documented in README.
    """

    def test_parser_accepts_pilot_model_hydraulic(self):
        args = _args(["--mode", "full", "--pilot-model", "hydraulic", "--fuel-mg", "20"])
        self.assertEqual(args.pilot_model, "hydraulic")
        self.assertGreaterEqual(float(args.nozzle_diameter_mm), 0.0)
        self.assertGreaterEqual(float(args.plunger_diameter_mm), 0.0)

    def test_parser_accepts_hrr_model_hydraulic_profile(self):
        args = _args(["--mode", "full", "--hrr-model", "hydraulic_profile", "--fuel-mg", "20"])
        self.assertEqual(args.hrr_model, "hydraulic_profile")

    def test_math_pi_imported_in_cli(self):
        import virtual_tdi.cli as cli_mod
        self.assertTrue(hasattr(cli_mod, "pi"))

    def test_no_placeholder_ellipsis_calls_in_cli_source(self):
        import inspect
        import virtual_tdi.cli as cli_mod
        src = inspect.getsource(cli_mod)
        self.assertNotIn("NozzleConfig(...)", src)
        self.assertNotIn("VP37HydraulicConfig(...)", src)
        self.assertNotIn("estimate_pilot_ratio(...)", src)


if __name__ == "__main__":
    unittest.main()
