import unittest

import numpy as np

from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle
from virtual_tdi.models import EngineGeometry, Fuel, HeatTransferConfig, InjectionSchedule, SimulationConfig
from virtual_tdi.valvetrain import ValveTiming


class TestFullCycleHeatTransfer(unittest.TestCase):
    def test_head_temp_trends_and_component_sums(self):
        bore = 79.5e-3
        stroke = 95.5e-3
        geom = EngineGeometry(
            bore_m=bore,
            stroke_m=stroke,
            rod_length_m=144e-3,
            crank_radius_m=stroke / 2.0,
            offset_m=0.5e-3,
            compression_ratio=19.5,
            cylinders=4,
        )
        fuel = Fuel.diesel()
        schedule = InjectionSchedule(
            soi_pilot_deg=-12.0,
            soi_main_deg=-6.0,
            pilot_fraction=0.12,
            duration_pilot_deg=8.0,
            duration_main_deg=42.0,
        )
        models_cool = SimulationConfig(
            rpm=1500.0,
            step_deg=2.0,
            fuel_mg_per_cycle_per_cyl=15.0,
            thermo_backend="simple",
            flow_backend="simple",
            strict_backends=False,
            heat_transfer=HeatTransferConfig(head_temp_k=500.0),
        )
        models_hot = SimulationConfig(
            rpm=1500.0,
            step_deg=2.0,
            fuel_mg_per_cycle_per_cyl=15.0,
            thermo_backend="simple",
            flow_backend="simple",
            strict_backends=False,
            heat_transfer=HeatTransferConfig(head_temp_k=900.0),
        )
        base_cfg = dict(
            rpm=1500.0,
            step_deg=2.0,
            cycles=2,
            boundaries=BoundaryConditions(
                intake_pressure_pa=1.0e5,
                intake_temp_k=300.0,
                exhaust_pressure_pa=1.15e5,
                exhaust_temp_k=900.0,
            ),
            valve_timing=ValveTiming(),
            fuel_mg_per_cycle_per_cyl=15.0,
        )
        cfg_cool = FullCycleConfig(models=models_cool, **base_cfg)
        cfg_hot = FullCycleConfig(models=models_hot, **base_cfg)

        result_cool = simulate_full_cycle(geom, fuel, schedule, cfg_cool)
        result_hot = simulate_full_cycle(geom, fuel, schedule, cfg_hot)

        self.assertTrue(
            np.allclose(
                result_cool.dq_wall_j_per_deg,
                result_cool.dq_head_j_per_deg
                + result_cool.dq_piston_j_per_deg
                + result_cool.dq_liner_j_per_deg,
            )
        )

        trapezoid = getattr(np, "trapezoid", np.trapz)
        q_head_cool = float(trapezoid(result_cool.dq_head_j_per_deg, result_cool.theta_deg))
        q_head_hot = float(trapezoid(result_hot.dq_head_j_per_deg, result_hot.theta_deg))
        self.assertLess(q_head_hot, q_head_cool)

        self.assertGreater(
            result_hot.metrics["t_exhaust_mean_k"] - result_cool.metrics["t_exhaust_mean_k"], 0.02
        )
        self.assertGreater(result_hot.metrics["imep_bar"], result_cool.metrics["imep_bar"])


if __name__ == "__main__":
    unittest.main()
