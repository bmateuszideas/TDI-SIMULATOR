import unittest
import warnings

from virtual_tdi.combustion import maybe_arm_combustion, CombustionScheduleRuntime
from virtual_tdi.models import Fuel, InjectionSchedule, SimulationConfig
from virtual_tdi.thermo import ignition_delay_seconds_arrhenius, omega_rad_per_s
import numpy as np


class TestIgnitionDelay(unittest.TestCase):
    """Regression guards for the Arrhenius ignition-delay blow-up (review 1.2).

    At low charge temperatures the uncalibrated Arrhenius correlation gives
    physically impossible delays (168 deg at 30 bar / 600 K -> SOC on the
    exhaust stroke, negative IMEP). The sanity cap must clamp this and flag it.
    """

    def test_arrhenius_delay_magnitudes(self):
        rpm = 1500.0
        cases = [
            (60e5, 800.0, 4.6),   # healthy main-injection conditions
            (35e5, 650.0, 59.0),  # cold pilot: uncapped blow-up territory
            (30e5, 600.0, 168.0),
        ]
        for p, t, expected in cases:
            tau = ignition_delay_seconds_arrhenius(
                p, t, a=5.0e-6, n=1.0, ea_j_per_mol=5.8e4
            )
            deg = tau * omega_rad_per_s(rpm) * 180.0 / np.pi
            self.assertAlmostEqual(deg, expected, delta=expected * 0.05)

    def test_cap_clamps_and_flags(self):
        cfg = SimulationConfig(rpm=1500.0)
        schedule = InjectionSchedule(
            soi_pilot_deg=-12.0,
            soi_main_deg=-6.0,
            pilot_fraction=0.12,
            duration_pilot_deg=8.0,
            duration_main_deg=42.0,
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            runtime = maybe_arm_combustion(
                -6.0,
                pressure_pa=30e5,
                temperature_k=600.0,
                fuel=Fuel.diesel(),
                schedule=schedule,
                sim_cfg=cfg,
                runtime=CombustionScheduleRuntime(),
            )
            self.assertTrue(runtime.ign_delay_main_capped)
            self.assertLessEqual(runtime.ign_delay_main_deg, 40.0)
            self.assertTrue(any("cap" in str(x.message) for x in w))

    def test_soc_main_within_sanity_window_at_typical_conditions(self):
        cfg = SimulationConfig(rpm=1500.0)
        schedule = InjectionSchedule(
            soi_pilot_deg=-12.0,
            soi_main_deg=-6.0,
            pilot_fraction=0.12,
            duration_pilot_deg=8.0,
            duration_main_deg=42.0,
        )
        runtime = maybe_arm_combustion(
            -6.0,
            pressure_pa=60e5,
            temperature_k=800.0,
            fuel=Fuel.diesel(),
            schedule=schedule,
            sim_cfg=cfg,
            runtime=CombustionScheduleRuntime(),
        )
        soc_main_deg = runtime.main_soc_rad * 180.0 / np.pi
        self.assertLess(soc_main_deg, 10.0)
        self.assertFalse(runtime.ign_delay_main_capped)


if __name__ == "__main__":
    unittest.main()
