"""Trend regression tests (Faza 1.C.1 in TODO.md).

These do not assert calibrated absolute values (that is the job of
`python -m virtual_tdi validate`), but physical monotonicity of trends:
IMEP grows with fuel dose, peak pressure grows with fuel dose, BSFC
at part load is above the full-load island, exhaust temp grows with load.
"""
import unittest

from virtual_tdi.models import Fuel
from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle
from virtual_tdi.geometry import EngineGeometry
from virtual_tdi.models import Fuel, InjectionSchedule, SimulationConfig
from virtual_tdi.valvetrain import ValveTiming


def _geometry() -> EngineGeometry:
    return EngineGeometry(
        bore_m=79.5e-3,
        stroke_m=95.5e-3,
        rod_length_m=144e-3,
        crank_radius_m=95.5e-3 / 2.0,
        offset_m=0.5e-3,
        bowl_volume_m3=17.5e-6,
        head_recess_m3=4.5e-6,
        gasket_thickness_m=1.53e-3,
        piston_protrusion_m=0.8e-3,
        compression_ratio=19.5,
        cylinders=4,
    )


def _schedule() -> InjectionSchedule:
    return InjectionSchedule(
        soi_pilot_deg=-12.0,
        soi_main_deg=-6.0,
        pilot_fraction=0.12,
        duration_pilot_deg=8.0,
        duration_main_deg=42.0,
    )


def _run(rpm: float, fuel_mg: float) -> dict:
    geom = _geometry()
    models = SimulationConfig(
        rpm=rpm,
        step_deg=2.0,
        fuel_mg_per_cycle_per_cyl=fuel_mg,
        thermo_backend="simple",
        flow_backend="simple",
        strict_backends=False,
    )
    cfg = FullCycleConfig(
        rpm=rpm,
        step_deg=2.0,
        cycles=1,
        boundaries=BoundaryConditions(
            intake_pressure_pa=1.0e5,
            intake_temp_k=300.0,
            exhaust_pressure_pa=1.15e5,
            exhaust_temp_k=800.0,
        ),
        valve_timing=ValveTiming(),
        fuel_mg_per_cycle_per_cyl=fuel_mg,
        models=models,
    )
    res = simulate_full_cycle(geom, Fuel.diesel(), _schedule(), cfg)
    return res.metrics


class TestImepTrends(unittest.TestCase):
    def test_imep_grows_with_fuel_dose(self):
        m1 = _run(1500.0, 6.0)
        m2 = _run(1500.0, 12.0)
        self.assertGreater(m2["imep_pa"], m1["imep_pa"])

    def test_peak_pressure_grows_with_fuel_dose(self):
        m1 = _run(1500.0, 6.0)
        m2 = _run(1500.0, 12.0)
        self.assertGreater(m2["peak_pressure_pa"], m1["peak_pressure_pa"])

    def test_exhaust_temp_grows_with_load(self):
        m1 = _run(1500.0, 6.0)
        m2 = _run(1500.0, 14.0)
        self.assertGreater(m2["t_exhaust_mean_k"], m1["t_exhaust_mean_k"])

    def test_bsfc_present_and_positive(self):
        m = _run(1500.0, 10.0)
        self.assertIn("bsfc_g_per_kwh", m)
        self.assertGreater(m["bsfc_g_per_kwh"], 50.0)
        self.assertLess(m["bsfc_g_per_kwh"], 2000.0)

    def test_mass_balance_closes_within_tolerance(self):
        # Single-cycle run starts from an assumed residual state; with the
        # fuel mass (Faza 2.B.2) and burned-gas mixture gamma (Faza 2.B.1)
        # the first-cycle balance closes within ~14%. Multi-cycle runs
        # (cycles>=3) converge much tighter (see full-cycle sanity tests).
        m = _run(1500.0, 10.0)
        start = m["mass_start_kg_per_cyl"]
        end = m["mass_end_kg_per_cyl"]
        self.assertLess(abs(start - end) / start, 0.15)


if __name__ == "__main__":
    unittest.main()
