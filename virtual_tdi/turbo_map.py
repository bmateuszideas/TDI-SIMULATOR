"""Turbocharger map model (TODO.md Faza 2.A).

Loads a compressor + turbine map (see validation/turbo_map_gt1749v.yaml)
and provides bilinear interpolation over speed lines and pressure ratio
grids, with clipping to the mapped envelope. Replaces fixed efficiency
assumptions in the quasi-steady power balance used by coupled.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAP_PATH = ROOT / "validation" / "turbo_map_gt1749v.yaml"


@dataclass(frozen=True)
class TurboMapModel:
    speed_rpm: np.ndarray            # (n_speed,)
    pr_grid: np.ndarray             # (n_pr,)
    mass_kg_s: np.ndarray           # (n_speed, n_pr) corrected mass flow
    eff_map: np.ndarray             # (n_speed, n_pr) isentropic efficiency
    t_er_grid: np.ndarray           # (n_er,) turbine expansion ratios
    t_eff: np.ndarray               # (n_er,) turbine efficiency
    t_mdot_factor: float

    @staticmethod
    def from_yaml(path: str | Path = DEFAULT_MAP_PATH) -> "TurboMapModel":
        p = Path(path)
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        speed = np.asarray(data["speed_rpm"], dtype=float)
        mass = np.asarray(data["corrected_mass_kg_s"]["values"], dtype=float)
        pr = np.asarray(data["corrected_mass_kg_s"]["pr_grid"], dtype=float)
        eff = np.asarray(data["efficiency"]["values"], dtype=float)
        tgrid = np.asarray(data["turbine"]["er_grid"], dtype=float)
        teff = np.asarray(data["turbine"]["efficiency"], dtype=float)
        tmf = float(data["turbine"]["mass_flow_factor_kg_s_per_er"])
        if mass.shape != (len(speed), len(pr)) or eff.shape != (len(speed), len(pr)):
            raise ValueError(f"Turbo map shape mismatch in {p}: {mass.shape}/{eff.shape}")
        return TurboMapModel(
            speed_rpm=speed, pr_grid=pr, mass_kg_s=mass, eff_map=eff,
            t_er_grid=tgrid, t_eff=teff, t_mdot_factor=tmf,
        )

    def _bilinear(self, grid_x: np.ndarray, grid_y: np.ndarray, values: np.ndarray,
                  x: float, y: float) -> float:
        """Bilinear interpolation with clipping to the mapped envelope."""
        x_c = float(np.clip(x, grid_x[0], grid_x[-1]))
        y_c = float(np.clip(y, grid_y[0], grid_y[-1]))
        i = int(np.searchsorted(grid_x, x_c))
        i = max(1, min(i, len(grid_x) - 1))
        j = int(np.searchsorted(grid_y, y_c))
        j = max(1, min(j, len(grid_y) - 1))
        x0, x1 = grid_x[i - 1], grid_x[i]
        y0, y1 = grid_y[j - 1], grid_y[j]
        tx = 0.0 if x1 == x0 else (x_c - x0) / (x1 - x0)
        ty = 0.0 if y1 == y0 else (y_c - y0) / (y1 - y0)
        v00 = values[i - 1, j - 1]
        v01 = values[i - 1, j]
        v10 = values[i, j - 1]
        v11 = values[i, j]
        return float((1 - tx) * (1 - ty) * v00 + (1 - tx) * ty * v01
                     + tx * (1 - ty) * v10 + tx * ty * v11)

    def compressor_efficiency(self, speed_rpm: float, pr: float) -> float:
        return self._bilinear(self.speed_rpm, self.pr_grid, self.eff_map,
                              speed_rpm, pr)

    def compressor_mass_kg_s(self, speed_rpm: float, pr: float) -> float:
        """Corrected mass flow through the compressor at (speed, PR)."""
        return self._bilinear(self.speed_rpm, self.pr_grid, self.mass_kg_s,
                              speed_rpm, pr)

    def turbine_efficiency(self, er: float) -> float:
        er_c = float(np.clip(er, self.t_er_grid[0], self.t_er_grid[-1]))
        return float(np.interp(er_c, self.t_er_grid, self.t_eff))

    def turbine_mass_kg_s(self, er: float, speed_rpm: float) -> float:
        """Swallowed mass flow; scales weakly with shaft speed."""
        er_c = max(1.0, float(er))
        speed_factor = 0.8 + 0.2 * float(np.clip(speed_rpm, 0.0, 210000.0)) / 210000.0
        return self.t_mdot_factor * er_c * speed_factor

    def compressor_power_w(self, speed_rpm: float, pr: float, m_air_kg_s: float,
                           t_in_k: float = 300.0, cp_j_per_kg_k: float = 1005.0,
                           gamma: float = 1.4) -> float:
        """Shaft power absorbed by the compressor (W), efficiency from the map."""
        eff = max(0.1, self.compressor_efficiency(speed_rpm, pr))
        g = max(1.05, gamma)
        temp = (g - 1.0) / g
        work_isentropic = m_air_kg_s * cp_j_per_kg_k * t_in_k * (pr ** temp - 1.0)
        return float(work_isentropic / eff)

    def turbine_power_w(self, er: float, speed_rpm: float, t_turbine_in_k: float,
                       p_out_pa: float = 1.0e5, cp_j_per_kg_k: float = 1100.0,
                       gamma: float = 1.33,
                       mdot_exhaust_kg_s: float | None = None) -> float:
        """Shaft power delivered by the turbine (W), efficiency from the map.

        If mdot_exhaust_kg_s is given (mass conservation: exhaust out of the
        engine flows through the turbine), it overrides the swallowing factor;
        the factor stays as fallback for map-only evaluation.
        """
        eff = max(0.1, self.turbine_efficiency(er))
        mdot = (mdot_exhaust_kg_s if mdot_exhaust_kg_s is not None
                else self.turbine_mass_kg_s(er, speed_rpm))
        g = max(1.05, gamma)
        temp = (g - 1.0) / g
        work_isentropic = (mdot * cp_j_per_kg_k * t_turbine_in_k
                           * (1.0 - er ** (-temp)))
        return float(work_isentropic * eff)
