"""Tests for ECU perception (Faza 2.C.1) and turbo shaft dynamics (Faza 2.A.3)."""
import unittest

from virtual_tdi.perception import PerceptionConfig, PerceptionLayer, SensorConfig, SensorModel


class TestSensorModel(unittest.TestCase):
    def test_lag_converges_to_true_value(self):
        s = SensorModel(SensorConfig(name="t", tau_s=0.05), dt_s=0.01)
        vals = [s.step(100.0) for _ in range(200)]
        self.assertGreater(vals[-1], 99.0)
        self.assertLess(vals[0], 20.0)  # starts near zero: lag visible

    def test_delay_holds_initial_value(self):
        s = SensorModel(SensorConfig(name="t", delay_s=0.05), dt_s=0.01)
        out = [s.step(100.0) for _ in range(10)]
        # first ~5 steps still held at the initial state (delay line)
        self.assertLess(out[0], 50.0)
        self.assertGreater(out[-1], 50.0)

    def test_bias_applied(self):
        s = SensorModel(SensorConfig(name="t", tau_s=1e-9, bias=5.0), dt_s=0.01)
        v = s.step(10.0)
        self.assertAlmostEqual(v, 15.0, places=3)

    def test_noise_is_random_but_bounded_in_mean(self):
        s = SensorModel(SensorConfig(name="t", tau_s=1e-9, noise_std=1.0), dt_s=0.01, seed=42)
        samples = [s.step(0.0) for _ in range(500)]
        mean = sum(samples) / len(samples)
        self.assertLess(abs(mean), 0.2)

    def test_perception_layer(self):
        pl = PerceptionLayer(PerceptionConfig(enabled=True), dt_s=0.01, seed=0)
        rpm_p, map_p, egt_p = pl.perceive(rpm=1500.0, map_kpa=100.0, egt_k=800.0)
        self.assertIsInstance(rpm_p, float)
        self.assertIsInstance(map_p, float)
        self.assertIsInstance(egt_p, float)


class TestShaftDynamics(unittest.TestCase):
    def test_shaft_does_not_race_and_stays_bounded(self):
        from virtual_tdi.turbo_map import TurboMapModel, shaft_dynamics_step
        tm = TurboMapModel.from_yaml()
        shaft = 60000.0
        for _ in range(200):
            shaft, pr = shaft_dynamics_step(
                tm, shaft_rpm=shaft, p_intake_pa=1.0e5, p_exhaust_pa=1.2e5,
                t_exhaust_k=800.0, m_air_kg_s=0.04, m_exhaust_kg_s=0.042,
                dt_s=0.05,
            )
            self.assertLessEqual(shaft, 280000.0)
            self.assertGreaterEqual(shaft, 10000.0)
            self.assertGreaterEqual(pr, 1.0)
            self.assertLessEqual(pr, 4.5)

    def test_high_inertia_spools_slower(self):
        from virtual_tdi.turbo_map import TurboMapModel, shaft_dynamics_step
        tm = TurboMapModel.from_yaml()

        def spool(inertia):
            shaft = 60000.0
            for _ in range(20):
                shaft, _ = shaft_dynamics_step(
                    tm, shaft_rpm=shaft, p_intake_pa=1.0e5, p_exhaust_pa=1.2e5,
                    t_exhaust_k=800.0, m_air_kg_s=0.04, m_exhaust_kg_s=0.042,
                    dt_s=0.05, inertia_kg_m2=inertia,
                )
            return shaft

        fast = spool(2.0e-5)
        slow = spool(2.0e-3)
        self.assertGreater(fast, slow)


if __name__ == "__main__":
    unittest.main()
