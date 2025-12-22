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


def _read_csv_rows(path: Path) -> list[list[str]]:
    import csv

    return list(csv.reader(path.read_text(encoding="utf-8", errors="replace").splitlines(), delimiter=",", quotechar='"'))


@dataclass(frozen=True)
class SmokeLimiterMap2D:
    """Smoke limiter: RPM x MAF(mg/str) -> max IQ (mg/str)."""

    rpm_axis: np.ndarray
    maf_axis_mg_per_str: np.ndarray
    iq_max_mg_per_str: np.ndarray  # shape (Nrpm, Nmaf)

    @staticmethod
    def from_csv(path: str | Path) -> "SmokeLimiterMap2D":
        p = Path(path)
        rows = _read_csv_rows(p)
        if len(rows) < 2:
            raise ValueError(f"Not enough rows in CSV: {p}")
        header = rows[0]
        if len(header) < 3:
            raise ValueError(f"Invalid header in CSV: {p}")

        maf_axis = np.array([_parse_float_any(h) for h in header[1:]], dtype=float)
        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if len(r) < 2:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            cells = r[1 : 1 + len(maf_axis)]
            if len(cells) != len(maf_axis):
                continue
            try:
                vals = [float(c.replace(",", ".")) for c in cells]
            except ValueError:
                continue
            rpm_vals.append(rpm)
            grid.append(vals)

        rpm_axis = np.asarray(rpm_vals, dtype=float)
        iq_max = np.asarray(grid, dtype=float)
        if rpm_axis.size < 2:
            raise ValueError(f"Parsed too few rows from {p}")

        r_order = np.argsort(rpm_axis)
        rpm_axis = rpm_axis[r_order]
        iq_max = iq_max[r_order, :]

        m_order = np.argsort(maf_axis)
        maf_axis = maf_axis[m_order]
        iq_max = iq_max[:, m_order]
        return SmokeLimiterMap2D(rpm_axis=rpm_axis, maf_axis_mg_per_str=maf_axis, iq_max_mg_per_str=iq_max)

    def iq_max(self, rpm: float, maf_mg_per_str: float) -> float:
        return float(_bilinear(self.rpm_axis, self.maf_axis_mg_per_str, self.iq_max_mg_per_str, rpm, maf_mg_per_str))


@dataclass(frozen=True)
class EGRMafTargetMap2D:
    """EGR MAF target: RPM x IQ(mg/str) -> target MAF (mg/str)."""

    rpm_axis: np.ndarray
    iq_axis_mg_per_str: np.ndarray
    maf_target_mg_per_str: np.ndarray  # shape (Nrpm, Niq)

    @staticmethod
    def from_csv(path: str | Path) -> "EGRMafTargetMap2D":
        p = Path(path)
        rows = _read_csv_rows(p)
        if len(rows) < 2:
            raise ValueError(f"Not enough rows in CSV: {p}")
        header = rows[0]
        if len(header) < 3:
            raise ValueError(f"Invalid header in CSV: {p}")

        iq_axis = np.array([_parse_float_any(h) for h in header[1:]], dtype=float)
        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if len(r) < 2:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            cells = r[1 : 1 + len(iq_axis)]
            if len(cells) != len(iq_axis):
                continue
            try:
                vals = [float(c.replace(",", ".")) for c in cells]
            except ValueError:
                continue
            rpm_vals.append(rpm)
            grid.append(vals)

        rpm_axis = np.asarray(rpm_vals, dtype=float)
        maf = np.asarray(grid, dtype=float)
        if rpm_axis.size < 2:
            raise ValueError(f"Parsed too few rows from {p}")

        r_order = np.argsort(rpm_axis)
        rpm_axis = rpm_axis[r_order]
        maf = maf[r_order, :]

        q_order = np.argsort(iq_axis)
        iq_axis = iq_axis[q_order]
        maf = maf[:, q_order]
        return EGRMafTargetMap2D(rpm_axis=rpm_axis, iq_axis_mg_per_str=iq_axis, maf_target_mg_per_str=maf)

    def maf_target(self, rpm: float, iq_mg_per_str: float) -> float:
        return float(_bilinear(self.rpm_axis, self.iq_axis_mg_per_str, self.maf_target_mg_per_str, rpm, iq_mg_per_str))


@dataclass(frozen=True)
class BoostTargetMap2D:
    """Boost target: RPM x IQ(mg/str) -> MAP target (mbar abs)."""

    rpm_axis: np.ndarray
    iq_axis_mg_per_str: np.ndarray
    map_mbar_abs: np.ndarray

    @staticmethod
    def from_csv(path: str | Path) -> "BoostTargetMap2D":
        p = Path(path)
        rows = _read_csv_rows(p)
        if len(rows) < 2:
            raise ValueError(f"Not enough rows in CSV: {p}")
        header = rows[0]
        if len(header) < 3:
            raise ValueError(f"Invalid header in CSV: {p}")

        raw_axis = np.array([_parse_float_any(h) for h in header[1:]], dtype=float)
        # Heuristic: some sources encode IQ as 2000..4000 meaning 20.00..40.00.
        iq_axis = np.array([v / 100.0 if v >= 200.0 else v for v in raw_axis], dtype=float)

        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if len(r) < 2:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            cells = r[1 : 1 + len(iq_axis)]
            if len(cells) != len(iq_axis):
                continue
            try:
                vals = [float(c.replace(",", ".")) for c in cells]
            except ValueError:
                continue
            rpm_vals.append(rpm)
            grid.append(vals)

        rpm_axis = np.asarray(rpm_vals, dtype=float)
        mp = np.asarray(grid, dtype=float)
        if rpm_axis.size < 2:
            raise ValueError(f"Parsed too few rows from {p}")

        r_order = np.argsort(rpm_axis)
        rpm_axis = rpm_axis[r_order]
        mp = mp[r_order, :]

        q_order = np.argsort(iq_axis)
        iq_axis = iq_axis[q_order]
        mp = mp[:, q_order]
        return BoostTargetMap2D(rpm_axis=rpm_axis, iq_axis_mg_per_str=iq_axis, map_mbar_abs=mp)

    def map_target_mbar(self, rpm: float, iq_mg_per_str: float) -> float:
        return float(_bilinear(self.rpm_axis, self.iq_axis_mg_per_str, self.map_mbar_abs, rpm, iq_mg_per_str))


def _bilinear(x_axis: np.ndarray, y_axis: np.ndarray, grid: np.ndarray, x: float, y: float) -> float:
    x_c = float(np.clip(x, float(x_axis[0]), float(x_axis[-1])))
    y_c = float(np.clip(y, float(y_axis[0]), float(y_axis[-1])))

    xi = int(np.clip(np.searchsorted(x_axis, x_c, side="right") - 1, 0, len(x_axis) - 2))
    yi = int(np.clip(np.searchsorted(y_axis, y_c, side="right") - 1, 0, len(y_axis) - 2))

    x0 = float(x_axis[xi])
    x1 = float(x_axis[xi + 1])
    y0 = float(y_axis[yi])
    y1 = float(y_axis[yi + 1])

    q00 = float(grid[xi, yi])
    q10 = float(grid[xi + 1, yi])
    q01 = float(grid[xi, yi + 1])
    q11 = float(grid[xi + 1, yi + 1])

    tx = 0.0 if x1 == x0 else (x_c - x0) / (x1 - x0)
    ty = 0.0 if y1 == y0 else (y_c - y0) / (y1 - y0)

    a = q00 * (1.0 - tx) + q10 * tx
    b = q01 * (1.0 - tx) + q11 * tx
    return a * (1.0 - ty) + b * ty

