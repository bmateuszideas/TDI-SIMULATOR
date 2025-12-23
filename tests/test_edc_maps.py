import unittest

from virtual_tdi.injection import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D


class TestEDCMaps(unittest.TestCase):
    def test_smoke_limiter(self):
        m = SmokeLimiterMap2D.from_csv("SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv")
        self.assertAlmostEqual(m.iq_max(1491.0, 300.0), 20.0, places=1)
        self.assertAlmostEqual(m.iq_max(5355.0, 300.0), 7.2, places=1)

    def test_egr_maf_target(self):
        m = EGRMafTargetMap2D.from_csv("Mapa_EGR___interpolowana_mapa_MAF.csv")
        self.assertAlmostEqual(m.maf_target(1491.0, 0.0), 246.7, places=1)
        self.assertAlmostEqual(m.maf_target(5355.0, 10.0), 850.0, places=1)

    def test_boost_target(self):
        m = BoostTargetMap2D.from_csv("Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv")
        # Columns include 2500.0 which is interpreted as 25.0 mg/str.
        self.assertAlmostEqual(m.map_target_mbar(1491.0, 25.0), 1207.0, places=1)
        self.assertAlmostEqual(m.map_target_mbar(1491.0, 20.0), 1120.0, places=1)


if __name__ == "__main__":
    unittest.main()

