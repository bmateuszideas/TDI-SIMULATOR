import unittest

from virtual_tdi.physics import valve_lift_fraction


class TestValveTrain(unittest.TestCase):
    def test_lift_fraction_basic(self):
        # Intake open from -350 to -150: mid-point should be near 1, ends 0.
        self.assertAlmostEqual(valve_lift_fraction(-350.0, -350.0, -150.0), 0.0, places=6)
        self.assertAlmostEqual(valve_lift_fraction(-150.0, -350.0, -150.0), 0.0, places=6)
        mid = valve_lift_fraction(-250.0, -350.0, -150.0)
        self.assertGreater(mid, 0.90)


if __name__ == "__main__":
    unittest.main()

