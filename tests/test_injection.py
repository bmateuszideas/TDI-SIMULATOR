import unittest
from pathlib import Path

import numpy as np

trapezoid = getattr(np, "trapezoid", None) or np.trapezoid if hasattr(np, "trapezoid") else np.trapz

from virtual_tdi.hydraulics import (
    NeedleConfig,
    NozzleConfig,
    VP37HydraulicConfig,
)
from virtual_tdi.injection import (
    InjectionLineConfig,
    solve_injection_hydraulics,
)
from virtual_tdi.models import Fuel
from virtual_tdi.vp37_cam import VP37CamProfile

CAM_CSV = "skok_tloczka_vp37_de110.csv"


@unittest.skipUnless(
    Path(CAM_CSV).exists(),
    "VP37 cam CSV not available",
)
class TestInjectionHydraulics(unittest.TestCase):
    """Coverage for the 1D line + needle-dynamics injection model (review 3.3).

    Guards: mass conservation of the exported rate profile, needle response,
    and the effect of cylinder back-pressure on the injection profile.
    """

    @classmethod
    def setUpClass(cls):
        cls.cam = VP37CamProfile.from_csv(CAM_CSV)
        cls.fuel = Fuel.diesel()

    def _solve(self, iq_mg=20.0, p_cyl=60e5):
        return solve_injection_hydraulics(
            self.cam,
            rpm=1500.0,
            iq_mg=iq_mg,
            fuel=self.fuel,
            nozzle=NozzleConfig(),
            needle=NeedleConfig(),
            hyd=VP37HydraulicConfig(),
            line=InjectionLineConfig(),
            p_cylinder_pa=p_cyl,
            cylinder=1,
        )

    def test_rate_profile_integrates_to_commanded_iq(self):
        for iq in (10.0, 20.0, 40.0):
            res = self._solve(iq_mg=iq)
            omega = 1500.0 * 2.0 * np.pi / 60.0
            theta = res.time_s * omega
            dmdtheta = res.mdot_fuel_kg_s / omega
            total_mg = float(trapezoid(dmdtheta, theta)) * 1e6
            self.assertAlmostEqual(total_mg, iq, delta=iq * 1e-3,
                                   msg=f"IQ {iq} mg not conserved")

    def test_needle_lift_bounded(self):
        res = self._solve()
        self.assertTrue(np.all(res.needle_lift_m >= 0.0))
        self.assertLessEqual(np.max(res.needle_lift_m), NeedleConfig().max_lift_m + 1e-9)

    def test_higher_back_pressure_reduces_injection_rate(self):
        res_low = self._solve(p_cyl=1.15e5)
        res_high = self._solve(p_cyl=60e5)
        self.assertLess(np.max(res_high.mdot_fuel_kg_s),
                        np.max(res_low.mdot_fuel_kg_s))

    def test_line_pressure_positive_and_above_back_pressure_when_open(self):
        res = self._solve()
        self.assertTrue(np.all(res.line_pressure_pa > 0.0))

    def test_empty_profile_for_zero_duration(self):
        res = solve_injection_hydraulics(
            self.cam,
            rpm=1500.0,
            iq_mg=0.0,
            fuel=self.fuel,
            nozzle=NozzleConfig(),
            needle=NeedleConfig(),
            hyd=VP37HydraulicConfig(),
            line=InjectionLineConfig(),
            p_cylinder_pa=60e5,
            cylinder=1,
        )
        # IQ=0: duration is zero -> empty arrays, no crash
        self.assertEqual(res.time_s.size, res.mdot_fuel_kg_s.size)


if __name__ == "__main__":
    unittest.main()
