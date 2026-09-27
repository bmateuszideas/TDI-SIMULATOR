import unittest

import numpy as np

from virtual_tdi.cli import _fmt_value


class TestFmtValue(unittest.TestCase):
    def test_regular_float_three_decimals(self):
        self.assertEqual(_fmt_value(1234.5678), "1234.568")

    def test_small_values_use_scientific(self):
        self.assertEqual(_fmt_value(1.125624e-05), "1.125624e-05")

    def test_zero_stays_zero(self):
        self.assertEqual(_fmt_value(0.0), "0.000")

    def test_numpy_float(self):
        self.assertEqual(_fmt_value(np.float64(9.5)), "9.500")

    def test_string_passthrough(self):
        self.assertEqual(_fmt_value("hello"), "hello")


if __name__ == "__main__":
    unittest.main()
