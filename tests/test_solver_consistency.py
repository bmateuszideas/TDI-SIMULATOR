import unittest

from virtual_tdi.models import (
    CombustionConfig,
    EngineGeometry,
    Fuel,
    InjectionSchedule,
    SimulationConfig,
)
from virtual_tdi.solver import simulate_closed_cycle


def _geom() -> EngineGeometry:
    return EngineGeometry(
        bore_m=79.5e-3,
        stroke_m=95.5e-3,
        rod_length_m=144e-3,
        crank_radius_m=95.5e-3 / 2.0,
        offset_m=0.5e-3,
        compression_ratio=19.5,
    )


def _config(integrator: str) -> SimulationConfig:
    return SimulationConfig(
        rpm=1500.0,
        step_deg=1.0,
        fuel_mg_per_cycle_per_cyl=20.0,
        combustion=CombustionConfig(hrr_model="wiebe"),
        thermo_backend="simple",
        flow_backend="simple",
        strict_backends=False,
        integrator=integrator,
        intake_pressure_pa=1.0e5,
        intake_temp_k=320.0,
    )


class TestSolverIntegratorConsistency(unittest.TestCase):
    """N-11: rk4 and scipy paths must start from the same initial mass.

    The rk4 path used to compute the initial cylinder mass from the ideal-gas
    law regardless of the thermo backend, while the scipy path used the
    backend's density - making results diverge for coolprop and being
    needlessly different even for simple.
    """

    def test_initial_mass_and_imep_consistent_across_integrators(self):
        schedule = InjectionSchedule(
            soi_pilot_deg=-12.0,
            soi_main_deg=-6.0,
            pilot_fraction=0.12,
            duration_pilot_deg=8.0,
            duration_main_deg=42.0,
        )
        res_rk4 = simulate_closed_cycle(_geom(), Fuel.diesel(), schedule, _config("rk4"))
        res_scipy = simulate_closed_cycle(_geom(), Fuel.diesel(), schedule, _config("scipy"))
        self.assertAlmostEqual(
            res_rk4.metrics["mass_kg_per_cyl"],
            res_scipy.metrics["mass_kg_per_cyl"],
            delta=res_scipy.metrics["mass_kg_per_cyl"] * 1e-6,
            msg="initial mass differs between integrators",
        )
        # IMEP within 5% - different integration accuracy is expected,
        # but the initial state must not be the source of divergence.
        imep_rk4 = res_rk4.metrics["imep_pa"]
        imep_scipy = res_scipy.metrics["imep_pa"]
        self.assertGreater(imep_rk4, 0.0)
        self.assertGreater(imep_scipy, 0.0)
        self.assertAlmostEqual(imep_rk4, imep_scipy, delta=imep_scipy * 0.05)


if __name__ == "__main__":
    unittest.main()
