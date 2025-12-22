import unittest

from virtual_tdi.n146_map import N146VoltageMap2D


class TestN146Map(unittest.TestCase):
    def test_parse_and_forward(self):
        m = N146VoltageMap2D.from_csv("Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv")
        self.assertGreater(m.rpm_axis.size, 5)
        self.assertGreater(m.iq_axis_mg_per_str.size, 5)
        # Known grid point: 1491 rpm, 0 mg -> 0 mV
        self.assertAlmostEqual(m.mv(1491.0, 0.0), 0.0, places=2)
        # Forward should be positive for higher IQ
        self.assertGreater(m.mv(1491.0, 20.0), 1000.0)

    def test_inverse(self):
        m = N146VoltageMap2D.from_csv("Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv")
        mv = m.mv(1491.0, 20.0)
        iq = m.iq_from_mv(1491.0, mv)
        self.assertAlmostEqual(iq, 20.0, places=1)


if __name__ == "__main__":
    unittest.main()

