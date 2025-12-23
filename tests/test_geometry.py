import math
import unittest

from virtual_tdi.core import create_geometry_from_config, load_yaml_config
from virtual_tdi.physics import cylinder_volume_m3, piston_position_derivative_ds_dtheta
from virtual_tdi.engine_model import EngineGeometry


class TestGeometry(unittest.TestCase):
    def setUp(self):
        """Load engine geometry from the master config file."""
        config = load_yaml_config("engine_reference_sources.yaml")
        self.geom: EngineGeometry = create_geometry_from_config(config)
        self.assertIsNotNone(self.geom)

    def test_volume_at_theta_zero_and_pi(self):
        """
        Tests if the volume at theta=0 and theta=pi matches the geometry
        definition, as the implementation uses theta=0 as the reference for TDC.
        """
        # Volume at theta=0 should be exactly the clearance volume by definition in the code
        v_at_zero, _, _ = cylinder_volume_m3(self.geom, 0.0)
        self.assertAlmostEqual(v_at_zero, self.geom.clearance_volume_m3_per_cyl, places=12)

        # Volume at theta=pi (approx. BDC)
        v_at_pi, _, _ = cylinder_volume_m3(self.geom, math.pi)
        # This should be close to the total volume, but not exact due to the offset
        expected_v_at_pi = self.geom.clearance_volume_m3_per_cyl + self.geom.swept_volume_m3_per_cyl
        # Allow a small tolerance because of the offset's effect
        self.assertAlmostEqual(v_at_pi, expected_v_at_pi, places=5)

    def test_derivative_at_true_dead_centers(self):
        """
        The derivative of volume (dV/dtheta) must be zero at the true
        top and bottom dead centers, where piston velocity is zero.
        These points are NOT at 0 and pi radians when there is an offset.
        """
        delta = self.geom.offset_m
        r = self.geom.crank_radius_m
        L = self.geom.rod_length_m

        self.assertTrue(r > 0)
        self.assertTrue(L > 0)
        self.assertTrue(delta >= 0)

        def find_root(fn, a, b):
            fa, fb = fn(a), fn(b)
            if fa == 0.0:
                return a
            if fb == 0.0:
                return b
            if fa * fb > 0.0:
                raise AssertionError("Root not bracketed for ds/dtheta.")
            lo, hi = a, b
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                fm = fn(mid)
                if fa * fm <= 0.0:
                    hi, fb = mid, fm
                else:
                    lo, fa = mid, fm
            return 0.5 * (lo + hi)

        ds_dtheta = lambda th: piston_position_derivative_ds_dtheta(self.geom, th)
        theta_tdc = find_root(ds_dtheta, -math.pi / 2.0, math.pi / 2.0)
        _, dV_dtheta_tdc, _ = cylinder_volume_m3(self.geom, theta_tdc)
        self.assertAlmostEqual(dV_dtheta_tdc, 0.0, places=6, msg="dV/dtheta should be 0 at true TDC")

        theta_bdc = find_root(ds_dtheta, math.pi / 2.0, 3.0 * math.pi / 2.0)
        _, dV_dtheta_bdc, _ = cylinder_volume_m3(self.geom, theta_bdc)
        self.assertAlmostEqual(dV_dtheta_bdc, 0.0, places=6, msg="dV/dtheta should be 0 at true BDC")

    def test_volume_and_derivative_at_intermediate_points(self):
        """
        Validates the volume and its derivative at 90 degrees, where the piston
        is near max speed.
        """
        theta = math.pi / 2.0  # 90 degrees
        V, dV_dtheta, _ = cylinder_volume_m3(self.geom, theta)

        # Manually calculate expected values for validation
        r = self.geom.crank_radius_m
        L = self.geom.rod_length_m
        delta = self.geom.offset_m

        s_tdc_ref = r + L  # Simplified position at theta=0 without offset for reference
        
        # Exact position calculation from geometry.py
        u_90 = r * math.sin(theta) - delta
        s_90 = r * math.cos(theta) + math.sqrt(L**2 - u_90**2)
        
        s_0 = r * math.cos(0) + math.sqrt(L**2 - (r * math.sin(0) - delta)**2)

        x_from_tdc_90 = s_0 - s_90
        expected_V = self.geom.clearance_volume_m3_per_cyl + self.geom.piston_area_m2 * x_from_tdc_90
        
        denom_90 = math.sqrt(L**2 - u_90**2)
        ds_dtheta_90 = -r * math.sin(theta) - (u_90 * r * math.cos(theta)) / denom_90
        expected_dV_dtheta = -self.geom.piston_area_m2 * ds_dtheta_90

        self.assertAlmostEqual(V, expected_V, places=12)
        self.assertAlmostEqual(dV_dtheta, expected_dV_dtheta, places=12)
        # The derivative should be strongly positive (volume increasing)
        self.assertGreater(dV_dtheta, 0)


if __name__ == "__main__":
    unittest.main()
