"""Headless tests for the GUI's pure argument-construction logic."""

import json
import unittest

from virtual_tdi.cli import _make_argparser
from virtual_tdi.gui import (
    SETTING_SPECS,
    SETTINGS_DEFAULTS,
    adjust_settings_for_backends,
    backend_availability,
    build_cli_args,
    parse_soi_sweep,
    settings_from_json,
    settings_to_json,
)

CLI_PARSER = _make_argparser()


def _settings(**overrides):
    s = SETTINGS_DEFAULTS()
    s.update(overrides)
    return s


class SoiSweepTest(unittest.TestCase):
    def test_empty_returns_none(self):
        self.assertIsNone(parse_soi_sweep(None))
        self.assertIsNone(parse_soi_sweep(""))
        self.assertIsNone(parse_soi_sweep("   "))

    def test_valid_sweep(self):
        self.assertEqual(parse_soi_sweep("-10:2:0.5"), "-10:2:0.5")

    def test_bad_format_raises(self):
        with self.assertRaises(ValueError):
            parse_soi_sweep("1:2")
        with self.assertRaises(ValueError):
            parse_soi_sweep("1:2:3:4")

    def test_zero_step_raises(self):
        with self.assertRaises(ValueError):
            parse_soi_sweep("0:10:0")

    def test_wrong_direction_raises(self):
        with self.assertRaises(ValueError):
            parse_soi_sweep("10:0:1")
        with self.assertRaises(ValueError):
            parse_soi_sweep("0:10:-1")


class BuildCliArgsTest(unittest.TestCase):
    def test_defaults_produce_minimal_command(self):
        cmd = build_cli_args(SETTINGS_DEFAULTS())
        self.assertEqual(cmd, ["--mode", "full"])

    def test_override_is_passed(self):
        cmd = build_cli_args(_settings(rpm="2000", fuel_mg="25.5"))
        self.assertIn("--rpm", cmd)
        self.assertEqual(cmd[cmd.index("--rpm") + 1], "2000.0")
        self.assertIn("--fuel-mg", cmd)
        self.assertEqual(cmd[cmd.index("--fuel-mg") + 1], "25.5")

    def test_mode_closed(self):
        cmd = build_cli_args(_settings(mode="closed"))
        self.assertEqual(cmd[:2], ["--mode", "closed"])

    def test_mode_transient(self):
        cmd = build_cli_args(
            _settings(mode="transient", rpm_start="800", rpm_target="1500", load_torque_nm="60")
        )
        self.assertEqual(cmd[:2], ["--mode", "transient"])
        self.assertIn("--rpm-start", cmd)
        self.assertIn("--load-torque-nm", cmd)

    def test_optional_path_defaults_are_omitted(self):
        cmd = build_cli_args(SETTINGS_DEFAULTS())
        self.assertNotIn("--soi-map", cmd)
        self.assertNotIn("--n146-map", cmd)

    def test_empty_optional_none_fields_are_omitted(self):
        cmd = build_cli_args(_settings(soi_main=""))
        self.assertNotIn("--soi-main", cmd)

    def test_none_default_field_value_is_passed(self):
        cmd = build_cli_args(_settings(soi_main="-5.5"))
        self.assertIn("--soi-main", cmd)
        self.assertEqual(cmd[cmd.index("--soi-main") + 1], "-5.5")

    def test_flag_true_is_passed(self):
        cmd = build_cli_args(_settings(turbo=True, use_boost_map=True, no_plot=True))
        self.assertIn("--turbo", cmd)
        self.assertIn("--use-boost-map", cmd)
        self.assertIn("--no-plot", cmd)

    def test_flag_false_is_omitted(self):
        cmd = build_cli_args(_settings(turbo=False))
        self.assertNotIn("--turbo", cmd)

    def test_bool_default_true_omitted_when_default(self):
        cmd = build_cli_args(SETTINGS_DEFAULTS())
        self.assertNotIn("--strict-backends", cmd)
        cmd = build_cli_args(_settings(strict_backends=False))
        self.assertIn("--no-strict-backends", cmd)

    def test_target_brake_kw(self):
        cmd = build_cli_args(_settings(target_brake_kw="10"))
        self.assertIn("--target-brake-kw", cmd)
        self.assertEqual(cmd[cmd.index("--target-brake-kw") + 1], "10.0")

    def test_target_brake_kw_not_full_raises(self):
        with self.assertRaises(ValueError):
            build_cli_args(_settings(mode="closed", target_brake_kw="10"))

    def test_n146_mv(self):
        cmd = build_cli_args(_settings(n146_mv="1200"))
        self.assertIn("--n146-mv", cmd)
        self.assertEqual(cmd[cmd.index("--n146-mv") + 1], "1200.0")

    def test_sweep_is_passed(self):
        cmd = build_cli_args(_settings(soi_main_sweep="-10:5:1"))
        self.assertIn("--soi-main-sweep", cmd)
        self.assertEqual(cmd[cmd.index("--soi-main-sweep") + 1], "-10:5:1")

    def test_n146_and_sweep_conflict(self):
        with self.assertRaises(ValueError):
            build_cli_args(_settings(n146_mv="1200", soi_main_sweep="-10:5:1"))

    def test_required_field_empty_raises(self):
        bad = SETTINGS_DEFAULTS()
        bad["rpm"] = ""
        with self.assertRaises(ValueError):
            build_cli_args(bad)

    def test_int_cast(self):
        cmd = build_cli_args(_settings(cycles="7", nozzle_holes="6"))
        self.assertEqual(cmd[cmd.index("--cycles") + 1], "7")
        self.assertEqual(cmd[cmd.index("--nozzle-holes") + 1], "6")

    def test_bad_number_raises(self):
        with self.assertRaises(ValueError):
            build_cli_args(_settings(rpm="abc"))

    def test_transcient_settings_in_full_mode_still_ok(self):
        cmd = build_cli_args(_settings(load_torque_nm="60"))
        self.assertIn("--load-torque-nm", cmd)

    def test_result_parses_through_cli_argparser(self):
        args = CLI_PARSER.parse_args(build_cli_args(_settings(rpm="1800", turbo=True)))
        self.assertEqual(args.rpm, 1800.0)
        self.assertTrue(args.turbo)
        self.assertEqual(args.mode, "full")

    def test_transient_result_parses_through_cli_argparser(self):
        cmd = build_cli_args(
            _settings(mode="transient", rpm="1500", rpm_start="800", rpm_target="1500", load_torque_nm="60", turbo_tau_s="0.9")
        )
        args = CLI_PARSER.parse_args(cmd)
        self.assertEqual(args.mode, "transient")
        self.assertEqual(args.rpm_start, 800.0)
        self.assertEqual(args.rpm_target, 1500.0)
        self.assertEqual(args.load_torque_nm, 60.0)
        self.assertEqual(args.turbo_tau_s, 0.9)

    def test_result_defaults_match_cli_defaults(self):
        args = CLI_PARSER.parse_args(build_cli_args(SETTINGS_DEFAULTS()))
        for name, value in vars(args).items():
            if name in ("soi_main_sweep", "n146_mv", "target_brake_kw"):
                continue
            expected = SETTINGS_DEFAULTS().get(name)
            if expected is None or isinstance(expected, str):
                continue
            if name in ("engine_config", "n146_map", "soi_map", "valve_table", "smoke_map", "egr_map", "boost_map", "vp37_cam", "out"):
                continue
            self.assertEqual(value, expected, f"mismatch for {name}")


class SettingsJsonTest(unittest.TestCase):
    def test_roundtrip(self):
        settings = _settings(rpm="2000", turbo=True, mode="transient", load_torque_nm="60")
        text = settings_to_json(settings)
        loaded = settings_from_json(text)
        self.assertEqual(loaded["rpm"], "2000")
        self.assertTrue(loaded["turbo"])
        self.assertEqual(loaded["mode"], "transient")
        self.assertEqual(loaded["load_torque_nm"], "60")

    def test_unknown_keys_ignored(self):
        loaded = settings_from_json(json.dumps({"rpm": "1234", "nieznane": "x"}))
        self.assertEqual(loaded["rpm"], "1234")
        self.assertNotIn("nieznane", loaded)

    def test_from_json_fills_defaults(self):
        loaded = settings_from_json(json.dumps({}))
        self.assertEqual(loaded["rpm"], SETTINGS_DEFAULTS()["rpm"])
        self.assertEqual(loaded["mode"], "full")


class BackendFallbackTest(unittest.TestCase):
    def test_all_installed_keeps_settings(self):
        settings, notes = adjust_settings_for_backends(
            SETTINGS_DEFAULTS(), {"fluids": True, "coolprop": True}
        )
        self.assertEqual(notes, [])
        self.assertEqual(settings["thermo_backend"], "coolprop")
        self.assertEqual(settings["flow_backend"], "fluids")

    def test_missing_fluids_downgrades_flow_backend(self):
        settings, notes = adjust_settings_for_backends(
            SETTINGS_DEFAULTS(), {"fluids": False, "coolprop": True}
        )
        self.assertEqual(settings["flow_backend"], "simple")
        self.assertTrue(any("fluids" in n for n in notes))
        self.assertFalse(settings["strict_backends"])

    def test_missing_coolprop_downgrades_thermo_backend(self):
        settings, notes = adjust_settings_for_backends(
            SETTINGS_DEFAULTS(), {"fluids": True, "coolprop": False}
        )
        self.assertEqual(settings["thermo_backend"], "simple")
        self.assertTrue(any("CoolProp" in n for n in notes))
        self.assertFalse(settings["strict_backends"])

    def test_explicit_simple_backends_need_no_strict_change(self):
        settings = SETTINGS_DEFAULTS()
        settings["thermo_backend"] = "simple"
        settings["flow_backend"] = "simple"
        settings["strict_backends"] = False
        adjusted, notes = adjust_settings_for_backends(
            settings, {"fluids": False, "coolprop": False}
        )
        self.assertEqual(notes, [])

    def test_adjusted_settings_build_valid_command(self):
        settings, _ = adjust_settings_for_backends(
            SETTINGS_DEFAULTS(), {"fluids": False, "coolprop": False}
        )
        cmd = build_cli_args(settings)
        args = CLI_PARSER.parse_args(cmd)
        self.assertEqual(args.flow_backend, "simple")
        self.assertEqual(args.thermo_backend, "simple")
        self.assertFalse(args.strict_backends)

    def test_backend_availability_returns_both_keys(self):
        availability = backend_availability()
        self.assertIn("fluids", availability)
        self.assertIn("coolprop", availability)


class SpecCoverageTest(unittest.TestCase):
    def test_every_cli_argument_has_a_spec(self):
        spec_names = {
            spec["name"]
            for specs in SETTING_SPECS.values()
            for spec in specs
        }
        spec_names.add("mode")
        for action in CLI_PARSER._actions:
            if action.dest in ("help",):
                continue
            self.assertIn(
                action.dest,
                spec_names,
                f"CLI argument '{action.dest}' has no GUI field",
            )

    def test_spec_names_exist_in_cli(self):
        spec_names = {
            spec["name"]
            for specs in SETTING_SPECS.values()
            for spec in specs
        }
        cli_dests = {a.dest for a in CLI_PARSER._actions if a.dest != "help"}
        self.assertTrue(spec_names <= cli_dests)

    def test_gui_importable_headless(self):
        import virtual_tdi.gui as gui_mod

        self.assertTrue(callable(gui_mod.build_cli_args))


if __name__ == "__main__":
    unittest.main()
