import unittest

from virtual_tdi.controller import solve_monotone_bisect


class TestController(unittest.TestCase):
    def test_bisect_increasing(self):
        res = solve_monotone_bisect(f=lambda x: 2.0 * x, target=10.0, x_lo=0.0, x_hi=10.0, tol=1e-6)
        self.assertTrue(res.converged)
        self.assertAlmostEqual(res.value, 5.0, places=4)

    def test_bisect_decreasing(self):
        res = solve_monotone_bisect(f=lambda x: 10.0 - x, target=3.0, x_lo=0.0, x_hi=10.0, tol=1e-6)
        self.assertTrue(res.converged)
        self.assertAlmostEqual(res.value, 7.0, places=4)


if __name__ == "__main__":
    unittest.main()

