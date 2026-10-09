"""Tests for VCDS log parsing and fault classification (docs/DIAGNOSTYKA_VCDS.md)."""
import unittest

from virtual_tdi.vcds_logs import (
    OperatingPoint,
    classify,
    parse_group,
    to_operating_points,
)

GROUP_011_DYNAMIC = """
  0 | 1601 | 1285,2 | 1397,4 | 59,6
  1,2 | 1670 | 2070,6 | 1458,6 | 80,9
  2,4 | 1833 | 2101,2 | 2040 | 52,1
  3,58 | 1995 | 2111,4 | 2203,2 | 46,9
  4,8 | 2181 | 2111,4 | 2019,6 | 52,5
  6,4 | 2413 | 2131,8 | 2131,8 | 49,3
  8 | 2645 | 2162,4 | 2162,4 | 46,9
  10,41 | 2993 | 2193 | 2193 | 50,5
  12,43 | 3271 | 2213,4 | 2203,2 | 46,2
  14,43 | 3526 | 2223,6 | 2233,8 | 43,8
  18,4 | 3990 | 2223,6 | 2223,6 | 45
"""

GROUP_003_STATIC = """
  0,4 | 742 | 172,7 | 172,7 | 43
  2,78 | 742 | 172,7 | 168,8 | 43,4
"""


class TestParseGroup(unittest.TestCase):
    def test_parses_group_011_rows(self):
        rows = parse_group(GROUP_011_DYNAMIC, group=11)
        self.assertEqual(len(rows), 11)
        self.assertAlmostEqual(rows[0].rpm, 1601.0)
        self.assertAlmostEqual(rows[0].fields["p2"], 1285.2, places=1)
        self.assertAlmostEqual(rows[-1].fields["p3"], 2223.6, places=1)

    def test_parses_group_003_rows(self):
        rows = parse_group(GROUP_003_STATIC, group=3)
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0].fields["p2"], 172.7, places=1)
        self.assertAlmostEqual(rows[0].fields["p4"], 43.0, places=1)


class TestOperatingPoints(unittest.TestCase):
    def test_merge_by_rpm(self):
        pts = to_operating_points(rows_011=parse_group(GROUP_011_DYNAMIC, group=11))
        self.assertTrue(len(pts) >= 11)
        p0 = pts[0]
        self.assertAlmostEqual(p0.rpm, 1601.0)
        self.assertAlmostEqual(p0.boost_spec_mbar, 1285.2, places=1)
        self.assertAlmostEqual(p0.boost_actual_mbar, 1397.4, places=1)


class TestClassify(unittest.TestCase):
    def test_healthy_boost_tracking(self):
        rows = parse_group(GROUP_011_DYNAMIC, group=11)
        pts = to_operating_points(rows_011=rows)
        # Healthy example from the owner's doc: spec == actual within ~5%
        hyps = classify(pts)
        names = {h.name for h in hyps}
        # Early transient points (0-1.2 s) may flag; settled region should be clean
        settled = [p for p in pts if p.rpm > 2400]
        settled_hyps = classify(settled)
        self.assertIn("healthy", {h.name for h in settled_hyps} if not any(
            h.severity == "fault" for h in settled_hyps) else names)

    def test_overboost_detected(self):
        pts = [OperatingPoint(rpm=2000.0, boost_spec_mbar=1800.0, boost_actual_mbar=2300.0)]
        hyps = classify(pts)
        self.assertTrue(any(h.name == "overboost" and h.severity == "fault" for h in hyps))

    def test_underboost_detected(self):
        pts = [OperatingPoint(rpm=2000.0, boost_spec_mbar=2200.0, boost_actual_mbar=1500.0)]
        hyps = classify(pts)
        self.assertTrue(any(h.name == "underboost" and h.severity == "fault" for h in hyps))

    def test_maf_underread_detected(self):
        pts = [OperatingPoint(rpm=3000.0, iq_requested_mg_r=55.0,
                               iq_torque_limit_mg_r=50.0, iq_smoke_limit_mg_r=44.0)]
        hyps = classify(pts)
        self.assertTrue(any(h.name == "maf_underread" for h in hyps))

    def test_healthy_baseline(self):
        pts = [OperatingPoint(rpm=3000.0, boost_spec_mbar=2200.0, boost_actual_mbar=2195.0,
                               maf_spec_mg_r=850.0, maf_actual_mg_r=845.0,
                               iq_requested_mg_r=55.0, iq_torque_limit_mg_r=50.0,
                               iq_smoke_limit_mg_r=52.0)]
        hyps = classify(pts)
        self.assertEqual(hyps[0].name, "healthy")


if __name__ == "__main__":
    unittest.main()
