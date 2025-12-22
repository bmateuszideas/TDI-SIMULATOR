from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np


_FLOAT_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _parse_float_any(s: str) -> float:
    m = _FLOAT_RE.search(s)
    if not m:
        raise ValueError(f"Cannot parse float from: {s!r}")
    return float(m.group(0).replace(",", "."))


@dataclass(frozen=True)
class N146VoltageMap2D:
    """N146 quantity adjuster voltage map: RPM x IQ(mg/str) -> mV."""

    rpm_axis: np.ndarray  # (Nrpm,) ascending
    iq_axis_mg_per_str: np.ndarray  # (Niq,) ascending
    voltage_mv: np.ndarray  # (Nrpm, Niq)

    @staticmethod
    def from_csv(path: str | Path) -> "N146VoltageMap2D":
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if not text:
            raise ValueError(f"Empty CSV: {p}")

        import csv

        rows = list(csv.reader(text, delimiter=",", quotechar='"'))
        if len(rows) < 2:
            raise ValueError(f"Not enough rows in CSV: {p}")

        header = rows[0]
        if len(header) < 3:
            raise ValueError(f"Invalid header in CSV: {p}")

        iq_cols = header[1:]
        iq_axis = np.array([_parse_float_any(h) for h in iq_cols], dtype=float)

        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if not r:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            cells = r[1 : 1 + len(iq_axis)]
            if len(cells) != len(iq_axis):
                continue
            row_vals = []
            ok = True
            for c in cells:
                try:
                    row_vals.append(_parse_float_any(c))
                except ValueError:
                    ok = False
                    break
            if not ok:
                continue
            rpm_vals.append(rpm)
            grid.append(row_vals)

        if len(rpm_vals) < 2:
            raise ValueError(f"Parsed too few RPM rows from {p}")

        rpm_axis = np.array(rpm_vals, dtype=float)
        voltage = np.array(grid, dtype=float)

        r_order = np.argsort(rpm_axis)
        rpm_axis = rpm_axis[r_order]
        voltage = voltage[r_order, :]

        q_order = np.argsort(iq_axis)
        iq_axis = iq_axis[q_order]
        voltage = voltage[:, q_order]

        return N146VoltageMap2D(rpm_axis=rpm_axis, iq_axis_mg_per_str=iq_axis, voltage_mv=voltage)

    def mv(self, rpm: float, iq_mg_per_str: float) -> float:
        return float(self._bilinear(rpm, iq_mg_per_str))

    def iq_from_mv(self, rpm: float, mv: float) -> float:
        """Invert map at given RPM assuming monotone increasing mv vs IQ."""
        v_row = self._row_at_rpm(float(rpm))
        iq = self.iq_axis_mg_per_str
        # Ensure monotonic for interp; if not, sort by voltage.
        order = np.argsort(v_row)
        v_sorted = v_row[order]
        iq_sorted = iq[order]
        mv_c = float(np.clip(mv, float(v_sorted[0]), float(v_sorted[-1])))
        return float(np.interp(mv_c, v_sorted, iq_sorted))

    def _row_at_rpm(self, rpm: float) -> np.ndarray:
        x = float(np.clip(rpm, float(self.rpm_axis[0]), float(self.rpm_axis[-1])))
        xi = np.searchsorted(self.rpm_axis, x, side="right") - 1
        xi = int(np.clip(xi, 0, len(self.rpm_axis) - 2))
        x0 = float(self.rpm_axis[xi])
        x1 = float(self.rpm_axis[xi + 1])
        t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
        return (1.0 - t) * self.voltage_mv[xi, :] + t * self.voltage_mv[xi + 1, :]

    def _bilinear(self, rpm: float, iq: float) -> float:
        x = float(np.clip(rpm, float(self.rpm_axis[0]), float(self.rpm_axis[-1])))
        y = float(np.clip(iq, float(self.iq_axis_mg_per_str[0]), float(self.iq_axis_mg_per_str[-1])))

        xi = np.searchsorted(self.rpm_axis, x, side="right") - 1
        yi = np.searchsorted(self.iq_axis_mg_per_str, y, side="right") - 1
        xi = int(np.clip(xi, 0, len(self.rpm_axis) - 2))
        yi = int(np.clip(yi, 0, len(self.iq_axis_mg_per_str) - 2))

        x0 = float(self.rpm_axis[xi])
        x1 = float(self.rpm_axis[xi + 1])
        y0 = float(self.iq_axis_mg_per_str[yi])
        y1 = float(self.iq_axis_mg_per_str[yi + 1])

        q00 = float(self.voltage_mv[xi, yi])
        q10 = float(self.voltage_mv[xi + 1, yi])
        q01 = float(self.voltage_mv[xi, yi + 1])
        q11 = float(self.voltage_mv[xi + 1, yi + 1])

        tx = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
        ty = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)

        a = q00 * (1.0 - tx) + q10 * tx
        b = q01 * (1.0 - tx) + q11 * tx
        return a * (1.0 - ty) + b * ty

