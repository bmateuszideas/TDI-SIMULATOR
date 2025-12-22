from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolveResult:
    value: float
    iterations: int
    converged: bool


def solve_monotone_bisect(
    *,
    f,
    target: float,
    x_lo: float,
    x_hi: float,
    tol: float,
    max_iter: int = 30,
) -> SolveResult:
    """Bisection for monotone function f(x) approximating f(x)=target.

    Assumes f(x_lo) <= target <= f(x_hi) or the reverse (handles decreasing too).
    """
    f_lo = float(f(x_lo))
    f_hi = float(f(x_hi))

    if f_lo == target:
        return SolveResult(value=x_lo, iterations=0, converged=True)
    if f_hi == target:
        return SolveResult(value=x_hi, iterations=0, converged=True)

    increasing = f_hi > f_lo
    if increasing:
        bracket_ok = f_lo <= target <= f_hi
    else:
        bracket_ok = f_hi <= target <= f_lo
    if not bracket_ok:
        return SolveResult(value=x_lo, iterations=0, converged=False)

    lo, hi = x_lo, x_hi
    for it in range(1, max_iter + 1):
        mid = 0.5 * (lo + hi)
        f_mid = float(f(mid))
        err = f_mid - target
        if abs(err) <= tol:
            return SolveResult(value=mid, iterations=it, converged=True)
        if increasing:
            if f_mid < target:
                lo = mid
            else:
                hi = mid
        else:
            if f_mid > target:
                lo = mid
            else:
                hi = mid
    return SolveResult(value=0.5 * (lo + hi), iterations=max_iter, converged=False)

