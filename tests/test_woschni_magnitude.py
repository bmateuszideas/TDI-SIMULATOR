import unittest

from virtual_tdi.heat_transfer import h_woschni_simplified_w_per_m2_k
from virtual_tdi.models import HeatTransferConfig


class TestWoschniMagnitude(unittest.TestCase):
    """Magnitude guard for the Woschni correlation (review 1.1).

    The constant must be consistent with the pressure units used in
    heat_transfer.py (pressure in bar): c = 127.93 per the repo's own
    SPECYFIKACJA MATEMATYCZNA (section 5). A previous regression used c = 3.26
    (a kPa-formulation constant) with p in bar, understating wall heat losses
    by ~40x and inflating IMEP.
    """

    def test_h_magnitude_at_combustion_point(self):
        cfg = HeatTransferConfig()
        h = h_woschni_simplified_w_per_m2_k(
            bore_m=79.5e-3,
            pressure_pa=60.0e5,
            temperature_k=1500.0,
            mean_piston_speed_m_per_s=4.77,
            cfg=cfg,
        )
        # Classic Woschni at 60 bar / 1500 K gives h ~ O(1000) W/m^2K.
        self.assertGreater(h, 300.0)
        self.assertLess(h, 5000.0)

    def test_h_scales_with_pressure(self):
        cfg = HeatTransferConfig()
        kwargs = dict(
            bore_m=79.5e-3,
            temperature_k=1500.0,
            mean_piston_speed_m_per_s=4.77,
        )
        h_low = h_woschni_simplified_w_per_m2_k(pressure_pa=10.0e5, cfg=cfg, **kwargs)
        h_high = h_woschni_simplified_w_per_m2_k(pressure_pa=100.0e5, cfg=cfg, **kwargs)
        self.assertGreater(h_high, h_low)

    def test_default_constant_matches_spec(self):
        # SPECYFIKACJA MATEMATYCZNA: h = 127.93 * D^-0.2 * P[bar]^0.8 * ...
        self.assertAlmostEqual(HeatTransferConfig().woschni_c, 127.93, places=2)


if __name__ == "__main__":
    unittest.main()
