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
class SOIMap2D:
    """SOI map: RPM x IQ(mg/str) -> SOI(deg).

    CSV format expected like:
    RPM (..)/IQ(MG/SUW), "0,00 IQ", "3,00 IQ", ... , źródło
    1491, "-1,5°", ..., "9,6°", 1
    """

    rpm_axis: np.ndarray  # (Nrpm,) ascending
    iq_axis_mg_per_str: np.ndarray  # (Niq,) ascending
    soi_deg_btdc_positive: np.ndarray  # (Nrpm, Niq)

    @staticmethod
    def from_csv(path: str | Path) -> "SOIMap2D":
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

        # Header: first column is RPM, last column is source. Middle are IQ columns.
        iq_cols = header[1:-1]
        iq_axis = np.array([_parse_float_any(h) for h in iq_cols], dtype=float)

        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if not r or len(r) < 3:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            soi_cells = r[1 : 1 + len(iq_axis)]
            if len(soi_cells) != len(iq_axis):
                continue
            soi_row = []
            ok = True
            for cell in soi_cells:
                try:
                    soi_row.append(_parse_float_any(cell))
                except ValueError:
                    ok = False
                    break
            if not ok:
                continue
            rpm_vals.append(rpm)
            grid.append(soi_row)

        if len(rpm_vals) < 2:
            raise ValueError(f"Parsed too few RPM rows from {p}")

        rpm_axis = np.array(rpm_vals, dtype=float)
        soi = np.array(grid, dtype=float)

        # Sort ascending by rpm for interpolation
        order = np.argsort(rpm_axis)
        rpm_axis = rpm_axis[order]
        soi = soi[order, :]

        iq_order = np.argsort(iq_axis)
        iq_axis = iq_axis[iq_order]
        soi = soi[:, iq_order]

        return SOIMap2D(rpm_axis=rpm_axis, iq_axis_mg_per_str=iq_axis, soi_deg_btdc_positive=soi)

    def soi_deg_model_convention(self, rpm: float, iq_mg_per_str: float, *, offset_deg: float = 0.0) -> float:
        """Return SOI in model convention (negative = BTDC, positive = ATDC)."""
        soi_btdc = float(self._bilinear(rpm, iq_mg_per_str))
        return (-soi_btdc) + float(offset_deg)

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

        q00 = float(self.soi_deg_btdc_positive[xi, yi])
        q10 = float(self.soi_deg_btdc_positive[xi + 1, yi])
        q01 = float(self.soi_deg_btdc_positive[xi, yi + 1])
        q11 = float(self.soi_deg_btdc_positive[xi + 1, yi + 1])

        tx = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
        ty = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)

        a = q00 * (1.0 - tx) + q10 * tx
        b = q01 * (1.0 - tx) + q11 * tx
        return a * (1.0 - ty) + b * ty

