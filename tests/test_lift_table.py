import unittest
import numpy as np

from virtual_tdi.injection import ValveLiftTable


class TestLiftTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load the valve lift table once for all tests."""
        cls.table = ValveLiftTable.from_markdown("profil_krzywek_4cylindry.md")
        if cls.table is None:
            raise AssertionError("Valve lift table failed to load.")
        if cls.table.theta_deg_0_720.size < 100:
            raise AssertionError("Valve lift table has too few samples.")

    def test_max_lift_matches_profile_data(self):
        """
        Verify that the maximum lift from the interpolated function matches the
        maximum value present in the source data file for each valve.
        """
        for cyl in [1, 2, 3, 4]:
            # Check intake valve max lift
            max_lift_in_data_in = np.max(self.table.intake_lift_mm[cyl])
            # Find the angle of max lift to test the interpolation at that exact point
            angle_of_max_in = self.table.theta_deg_0_720[np.argmax(self.table.intake_lift_mm[cyl])]
            interpolated_max_in = self.table.lift_m(angle_of_max_in, cylinder=cyl, valve="intake")
            self.assertAlmostEqual(
                interpolated_max_in * 1000,
                max_lift_in_data_in,
                places=3,
                msg=f"Cyl {cyl} intake max lift mismatch",
            )

            # Check exhaust valve max lift
            max_lift_in_data_ex = np.max(self.table.exhaust_lift_mm[cyl])
            angle_of_max_ex = self.table.theta_deg_0_720[np.argmax(self.table.exhaust_lift_mm[cyl])]
            interpolated_max_ex = self.table.lift_m(angle_of_max_ex, cylinder=cyl, valve="exhaust")
            self.assertAlmostEqual(
                interpolated_max_ex * 1000,
                max_lift_in_data_ex,
                places=3,
                msg=f"Cyl {cyl} exhaust max lift mismatch",
            )

    def test_interpolation_mid_point(self):
        """
        Tests the linear interpolation between two known points from the table.
        """
        # Using Cylinder 4 intake valve data around 72 degrees
        # From the file: at 72.0 deg, lift is 8.223 mm. At 75.6 deg, lift is 8.444 mm.
        angle1 = 72.0
        lift1_mm = 8.223
        angle2 = 75.6
        lift2_mm = 8.444

        # Mid-point angle
        mid_angle = (angle1 + angle2) / 2.0
        # Expected lift is the average of the two points for linear interpolation
        expected_mid_lift_mm = (lift1_mm + lift2_mm) / 2.0

        interpolated_lift = self.table.lift_m(mid_angle, cylinder=4, valve="intake")
        self.assertAlmostEqual(interpolated_lift * 1000, expected_mid_lift_mm, places=3)

    def test_periodicity(self):
        """
        Lift at angle `theta` should be the same as `theta + 720`, `theta - 720`, etc.
        """
        for angle in [30.0, 180.0, 450.0]:
            lift1 = self.table.lift_m(angle, cylinder=1, valve="intake")
            lift2 = self.table.lift_m(angle + 720.0, cylinder=1, valve="intake")
            lift3 = self.table.lift_m(angle - 720.0, cylinder=1, valve="intake")
            self.assertAlmostEqual(lift1, lift2, places=6)
            self.assertAlmostEqual(lift1, lift3, places=6)

    def test_valve_timing_open_close(self):
        """
        Verifies that the valve lift is zero just before opening and just after closing.
        """
        # For Cylinder 1, the intake valve starts lifting just after 335.0 deg
        self.assertAlmostEqual(self.table.lift_m(335.0, cylinder=1, valve="intake"), 0.0, places=6)
        self.assertGreater(self.table.lift_m(338.6, cylinder=1, valve="intake"), 0.0)

        # And it closes around 572.7 deg
        self.assertGreater(self.table.lift_m(572.7, cylinder=1, valve="intake"), 0.0)
        # The next point in the file (576.3) is 0, so interpolation should be 0 just after.
        self.assertAlmostEqual(self.table.lift_m(577.0, cylinder=1, valve="intake"), 0.0, places=6)

        # For Cylinder 1, the exhaust valve starts lifting just after 158.5 deg
        self.assertAlmostEqual(self.table.lift_m(158.0, cylinder=1, valve="exhaust"), 0.0, delta=2e-5)
        self.assertGreater(self.table.lift_m(158.5, cylinder=1, valve="exhaust"), 0.0)
        
        # And it closes around 360.2 deg
        self.assertGreater(self.table.lift_m(360.2, cylinder=1, valve="exhaust"), 0.0)
        self.assertAlmostEqual(self.table.lift_m(361.0, cylinder=1, valve="exhaust"), 0.0, delta=5e-4)


if __name__ == "__main__":
    unittest.main()
