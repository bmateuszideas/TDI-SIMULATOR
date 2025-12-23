from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

trapezoid = getattr(np, "trapezoid", np.trapz)


@dataclass(frozen=True)
class VP37CamProfile:
    """VP37 cam-plate plunger stroke profile.

    The input CSV (e.g. DE110) is expected to cover pump angle 0..360 deg and
    contain 4 lobes (4 injection events) per revolution.
    """

    pump_angle_deg: np.ndarray  # (N,) in [0,360]
    stroke_mm: np.ndarray  # (N,)
    peak_angles_deg: np.ndarray  # (4,) peak positions for lobes

    @staticmethod
    def from_csv(path: str | Path) -> "VP37CamProfile":
        import csv

        p = Path(path)
        rows = list(csv.reader(p.read_text(encoding="utf-8", errors="replace").splitlines()))
        if len(rows) < 10:
            raise ValueError(f"Too few rows in cam CSV: {p}")

        header = rows[0]
        if len(header) < 2:
            raise ValueError(f"Invalid cam CSV header: {p}")

        ang = []
        stroke = []
        for r in rows[1:]:
            if len(r) < 2:
                continue
            try:
                a = float(r[0].replace(",", "."))
                s = float(r[1].replace(",", "."))
            except ValueError:
                continue
            ang.append(a)
            stroke.append(s)

        pump_angle = np.asarray(ang, dtype=float)
        stroke_mm = np.asarray(stroke, dtype=float)
        if pump_angle.size < 100:
            raise ValueError(f"Parsed too few samples from cam CSV: {p}")

        # Sort by angle for interpolation.
        order = np.argsort(pump_angle)
        pump_angle = pump_angle[order]
        stroke_mm = stroke_mm[order]

        # Peak detection (simple local maxima).
        peaks = []
        for i in range(1, len(stroke_mm) - 1):
            if stroke_mm[i] > stroke_mm[i - 1] and stroke_mm[i] > stroke_mm[i + 1] and stroke_mm[i] > 0.01:
                peaks.append(pump_angle[i])
        peaks = np.asarray(peaks, dtype=float)
        if peaks.size != 4:
            # Keep up to 4 strongest peaks.
            if peaks.size < 1:
                raise ValueError(f"Could not find cam lobes in {p}")
            # approximate by taking top 4 by stroke magnitude
            idx = np.argsort(stroke_mm)[-4:]
            peaks = np.sort(pump_angle[idx])

        return VP37CamProfile(pump_angle_deg=pump_angle, stroke_mm=stroke_mm, peak_angles_deg=np.sort(peaks))

    def _lobe_index_for_cylinder(self, cylinder: int) -> int:
        # Map firing order 1-3-4-2 to lobe order 0-1-2-3.
        order = {1: 0, 3: 1, 4: 2, 2: 3}
        if cylinder not in order:
            raise ValueError("cylinder must be 1..4")
        return order[cylinder]

    def _rising_segment(self, lobe_idx: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (angle_deg, stroke_mm) for the rising part of a given lobe."""
        peaks = self.peak_angles_deg
        if peaks.size < 4:
            raise ValueError("Cam profile must have 4 lobes.")

        peak = float(peaks[lobe_idx])

        # Work on extended domain to handle wrap-around cleanly.
        ang = self.pump_angle_deg
        st = self.stroke_mm
        ang_ext = np.concatenate([ang, ang[1:] + 360.0])
        st_ext = np.concatenate([st, st[1:]])

        # Find the peak index in extended array closest to peak (first revolution).
        peak_idx = int(np.argmin(np.abs(ang_ext - peak)))

        # Previous peak angle in extended domain.
        prev_peak = float(peaks[(lobe_idx - 1) % 4])
        if lobe_idx == 0:
            prev_peak = prev_peak - 360.0
        # Segment where valley is expected: between prev_peak and peak.
        seg_mask = (ang_ext >= prev_peak) & (ang_ext <= peak)
        seg_idx = np.where(seg_mask)[0]
        if seg_idx.size < 5:
            raise ValueError("Not enough samples for lobe segmentation.")

        # Valley index (minimum stroke) within segment.
        valley_local = int(seg_idx[np.argmin(st_ext[seg_idx])])

        # Rising segment: from valley to peak (monotonic-ish).
        start = valley_local
        end = peak_idx
        if end <= start:
            end = start + 1
        a = ang_ext[start : end + 1]
        s = st_ext[start : end + 1]

        # Ensure strictly increasing in stroke for interpolation by sorting by stroke.
        # (We keep angle monotonic too, but use stroke-based interp later.)
        return a, s

    def duration_main_crank_deg(
        self,
        *,
        iq_mg_per_stroke: float,
        cylinder: int = 1,
        iq_max_mg: float = 51.0,
        delivery_start_frac: float = 0.40,
    ) -> float:
        """Estimate main injection duration (EOI-SOI) in crank degrees from cam stroke.

        Uses the rising part of the cam lobe; assumes injected quantity scales with
        effective stroke fraction used. delivery_start_frac trims off early stroke
        where pressure is typically too low for injection.
        """
        iq = float(max(0.0, iq_mg_per_stroke))
        iq_max = float(max(1e-9, iq_max_mg))
        frac = min(1.0, iq / iq_max)
        start_frac = float(np.clip(delivery_start_frac, 0.0, 0.95))
        end_frac = start_frac + frac * (1.0 - start_frac)

        lobe_idx = self._lobe_index_for_cylinder(cylinder)
        a, s = self._rising_segment(lobe_idx)
        peak = float(np.max(s))
        if peak <= 1e-6:
            return 0.0

        # Normalize and invert stroke->angle by interpolation on rising segment.
        # stroke is non-decreasing overall on rising part.
        s_norm = np.clip(s / peak, 0.0, 1.0)

        # Ensure increasing x for np.interp (sort by s_norm).
        order = np.argsort(s_norm)
        s_sorted = s_norm[order]
        a_sorted = a[order]

        a_start = float(np.interp(start_frac, s_sorted, a_sorted))
        a_end = float(np.interp(end_frac, s_sorted, a_sorted))
        dur_pump_deg = max(0.0, a_end - a_start)

        # Pump rotates at 1/2 crank speed: 1 pump deg == 2 crank deg.
        return 2.0 * dur_pump_deg

    def rate_shape_u_w(
        self,
        *,
        iq_mg_per_stroke: float,
        cylinder: int = 1,
        iq_max_mg: float = 51.0,
        delivery_start_frac: float = 0.40,
        samples: int = 200,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return (u, w) curve for shaped rate, u in [0,1], ∫w du = 1."""
        iq = float(max(0.0, iq_mg_per_stroke))
        iq_max = float(max(1e-9, iq_max_mg))
        frac = min(1.0, iq / iq_max)
        start_frac = float(np.clip(delivery_start_frac, 0.0, 0.95))
        end_frac = start_frac + frac * (1.0 - start_frac)

        lobe_idx = self._lobe_index_for_cylinder(cylinder)
        a, s = self._rising_segment(lobe_idx)
        peak = float(np.max(s))
        if peak <= 1e-6:
            u = np.linspace(0.0, 1.0, max(2, int(samples)), dtype=float)
            w = np.ones_like(u)
            w /= float(trapezoid(w, u))
            return u, w

        s_norm = np.clip(s / peak, 0.0, 1.0)
        # Select the portion between start_frac and end_frac
        mask = (s_norm >= start_frac) & (s_norm <= end_frac)
        if np.count_nonzero(mask) < 5:
            # Fall back to entire rising segment
            mask = s_norm >= start_frac

        a_sel = a[mask]
        s_sel = s[mask]
        if a_sel.size < 5:
            u = np.linspace(0.0, 1.0, max(2, int(samples)), dtype=float)
            w = np.ones_like(u)
            w /= float(trapezoid(w, u))
            return u, w

        # Weight by ds/da (stroke rate); ensure positive.
        ds_da = np.gradient(s_sel, a_sel)
        ds_da = np.clip(ds_da, 0.0, None)
        if float(np.max(ds_da)) <= 0.0:
            ds_da = np.ones_like(ds_da)

        # Map to normalized progress u and resample to uniform u grid.
        u_raw = (a_sel - float(a_sel[0])) / max(1e-9, float(a_sel[-1] - a_sel[0]))
        u_grid = np.linspace(0.0, 1.0, max(10, int(samples)), dtype=float)
        w_grid = np.interp(u_grid, u_raw, ds_da)

        area = float(trapezoid(w_grid, u_grid))
        if area <= 0.0:
            w_grid = np.ones_like(u_grid)
            area = float(trapezoid(w_grid, u_grid))
        w_grid /= area
        return u_grid, w_grid


from dataclasses import dataclass
from math import sqrt

from .engine_model import Fuel, InjectionSchedule
from .physics import omega_rad_per_s


@dataclass(frozen=True)
class VP37LineModel:
    # Very simplified: hydraulic delay = line_length / c, where c = sqrt(K/rho).
    line_length_m: float = 0.40


def apply_hydraulic_delay(schedule: InjectionSchedule, *, fuel: Fuel, rpm: float, model: VP37LineModel) -> InjectionSchedule:
    if model.line_length_m <= 0.0:
        return schedule
    c = sqrt(max(1.0, fuel.bulk_modulus_pa) / max(1e-9, fuel.density_kg_per_m3))
    tau_s = model.line_length_m / max(1e-9, c)
    delay_deg = (omega_rad_per_s(rpm) * tau_s) * (180.0 / 3.141592653589793)
    return InjectionSchedule(
        soi_pilot_deg=schedule.soi_pilot_deg + delay_deg,
        soi_main_deg=schedule.soi_main_deg + delay_deg,
        pilot_fraction=schedule.pilot_fraction,
        duration_pilot_deg=schedule.duration_pilot_deg,
        duration_main_deg=schedule.duration_main_deg,
        wiebe_m_pilot=schedule.wiebe_m_pilot,
        wiebe_m_main=schedule.wiebe_m_main,
    )



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

    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not text:
        return []
    first = text[0]
    delimiter = ";" if first.count(";") > first.count(",") else ","
    return list(csv.reader(text, delimiter=delimiter, quotechar='"'))


def _numeric_header_axis(header: list[str]) -> tuple[list[int], np.ndarray]:
    indices: list[int] = []
    values: list[float] = []
    for i, cell in enumerate(header[1:], start=1):
        try:
            values.append(_parse_float_any(cell))
            indices.append(i)
        except ValueError:
            continue
    return indices, np.array(values, dtype=float)


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
        rows = _read_csv_rows(p)
        if not rows:
            raise ValueError(f"Empty CSV: {p}")
        if len(rows) < 2:
            raise ValueError(f"Not enough rows in CSV: {p}")

        header = rows[0]
        if len(header) < 3:
            raise ValueError(f"Invalid header in CSV: {p}")

        col_idx, iq_axis = _numeric_header_axis(header)
        if iq_axis.size < 2:
            raise ValueError(f"Invalid header in CSV: {p}")

        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if not r or len(r) < 3:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            soi_row = []
            ok = True
            for idx in col_idx:
                if idx >= len(r):
                    ok = False
                    break
                try:
                    soi_row.append(_parse_float_any(r[idx]))
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

    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not text:
        return []
    first = text[0]
    delimiter = ";" if first.count(";") > first.count(",") else ","
    return list(csv.reader(text, delimiter=delimiter, quotechar='"'))


def _numeric_header_axis(header: list[str]) -> tuple[list[int], np.ndarray]:
    indices: list[int] = []
    values: list[float] = []
    for i, cell in enumerate(header[1:], start=1):
        try:
            values.append(_parse_float_any(cell))
            indices.append(i)
        except ValueError:
            continue
    return indices, np.array(values, dtype=float)


@dataclass(frozen=True)
class N146VoltageMap2D:
    """N146 quantity adjuster voltage map: RPM x IQ(mg/str) -> mV."""

    rpm_axis: np.ndarray  # (Nrpm,) ascending
    iq_axis_mg_per_str: np.ndarray  # (Niq,) ascending
    voltage_mv: np.ndarray  # (Nrpm, Niq)

    @staticmethod
    def from_csv(path: str | Path) -> "N146VoltageMap2D":
        p = Path(path)
        rows = _read_csv_rows(p)
        if not rows:
            raise ValueError(f"Empty CSV: {p}")
        if len(rows) < 2:
            raise ValueError(f"Not enough rows in CSV: {p}")

        header = rows[0]
        if len(header) < 3:
            raise ValueError(f"Invalid header in CSV: {p}")

        col_idx, iq_axis = _numeric_header_axis(header)
        if iq_axis.size < 2:
            raise ValueError(f"Invalid header in CSV: {p}")

        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if not r:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            row_vals = []
            ok = True
            for idx in col_idx:
                if idx >= len(r):
                    ok = False
                    break
                try:
                    row_vals.append(_parse_float_any(r[idx]))
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


from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class ValveLiftTable:
    """Valve lift table for a 4-stroke 720° crank cycle.

    Source file is expected to be a Markdown table with columns like:
    - Kąt Wału [°CK]
    - Dolotowy_Cyl1, Wydechowy_Cyl1, ... for cylinders 1..4
    Units: lift values in mm.
    """

    theta_deg_0_720: np.ndarray  # shape (N,)
    intake_lift_mm: dict[int, np.ndarray]  # cyl -> (N,)
    exhaust_lift_mm: dict[int, np.ndarray]  # cyl -> (N,)

    @staticmethod
    def from_markdown(path: str | Path) -> "ValveLiftTable":
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="replace").splitlines()

        header_idx = None
        for i, line in enumerate(text):
            if "|" in line and "K" in line and "Wa" in line and "Dolotowy" in line and "Wydechowy" in line:
                header_idx = i
                break
        if header_idx is None or header_idx + 2 >= len(text):
            raise ValueError(f"Could not find Markdown table header in {p}")

        headers = [h.strip() for h in text[header_idx].strip().strip("|").split("|")]
        # Consume separator row at header_idx+1
        data_lines = []
        for line in text[header_idx + 2 :]:
            if not line.strip().startswith("|"):
                break
            data_lines.append(line)

        if not data_lines:
            raise ValueError(f"No table rows found in {p}")

        def col(name: str) -> int:
            try:
                return headers.index(name)
            except ValueError as e:
                raise ValueError(f"Missing column '{name}' in {p}") from e

        angle_col = col(headers[0])

        intake: dict[int, list[float]] = {1: [], 2: [], 3: [], 4: []}
        exhaust: dict[int, list[float]] = {1: [], 2: [], 3: [], 4: []}
        theta: list[float] = []

        intake_cols = {c: col(f"Dolotowy_Cyl{c}") for c in (1, 2, 3, 4)}
        exhaust_cols = {c: col(f"Wydechowy_Cyl{c}") for c in (1, 2, 3, 4)}

        for line in data_lines:
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) != len(headers):
                continue
            try:
                theta_val = float(parts[angle_col].replace(",", "."))
            except ValueError:
                continue
            theta.append(theta_val)
            for c in (1, 2, 3, 4):
                intake[c].append(float(parts[intake_cols[c]].replace(",", ".")))
                exhaust[c].append(float(parts[exhaust_cols[c]].replace(",", ".")))

        theta_arr = np.asarray(theta, dtype=float)
        if theta_arr.ndim != 1 or theta_arr.size < 10:
            raise ValueError(f"Parsed too few rows from {p}")

        # Normalize to [0, 720) with monotonic increasing for interpolation
        theta_norm = np.mod(theta_arr, 720.0)
        order = np.argsort(theta_norm)
        theta_norm = theta_norm[order]

        def ordered(values: list[float]) -> np.ndarray:
            v = np.asarray(values, dtype=float)
            return v[order]

        return ValveLiftTable(
            theta_deg_0_720=theta_norm,
            intake_lift_mm={c: ordered(intake[c]) for c in (1, 2, 3, 4)},
            exhaust_lift_mm={c: ordered(exhaust[c]) for c in (1, 2, 3, 4)},
        )

    def lift_m(self, theta_deg: float, *, cylinder: int, valve: str) -> float:
        """Interpolated lift in meters for given global crank angle."""
        if cylinder not in (1, 2, 3, 4):
            raise ValueError("cylinder must be 1..4")
        t = float(np.mod(theta_deg, 720.0))
        if valve == "intake":
            y = self.intake_lift_mm[cylinder]
        elif valve == "exhaust":
            y = self.exhaust_lift_mm[cylinder]
        else:
            raise ValueError("valve must be 'intake' or 'exhaust'")

        x = self.theta_deg_0_720
        # Periodic interpolation: extend with endpoint + 720.
        x_ext = np.concatenate([x, x[:1] + 720.0])
        y_ext = np.concatenate([y, y[:1]])
        mm = float(np.interp(t, x_ext, y_ext))
        return mm * 1e-3



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

    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not text:
        return []
    first = text[0]
    delimiter = ";" if first.count(";") > first.count(",") else ","
    return list(csv.reader(text, delimiter=delimiter, quotechar='"'))


def _numeric_header_axis(header: list[str]) -> tuple[list[int], np.ndarray]:
    indices: list[int] = []
    values: list[float] = []
    for i, cell in enumerate(header[1:], start=1):
        try:
            values.append(_parse_float_any(cell))
            indices.append(i)
        except ValueError:
            continue
    return indices, np.array(values, dtype=float)


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

        col_idx, maf_axis = _numeric_header_axis(header)
        if maf_axis.size < 2:
            raise ValueError(f"Invalid header in CSV: {p}")
        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if len(r) < 2:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            vals: list[float] = []
            ok = True
            for idx in col_idx:
                if idx >= len(r):
                    ok = False
                    break
                try:
                    vals.append(_parse_float_any(r[idx]))
                except ValueError:
                    ok = False
                    break
            if not ok or len(vals) != len(maf_axis):
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

        col_idx, iq_axis = _numeric_header_axis(header)
        if iq_axis.size < 2:
            raise ValueError(f"Invalid header in CSV: {p}")
        rpm_vals: list[float] = []
        grid: list[list[float]] = []
        for r in rows[1:]:
            if len(r) < 2:
                continue
            try:
                rpm = _parse_float_any(r[0])
            except ValueError:
                continue
            vals: list[float] = []
            ok = True
            for idx in col_idx:
                if idx >= len(r):
                    ok = False
                    break
                try:
                    vals.append(_parse_float_any(r[idx]))
                except ValueError:
                    ok = False
                    break
            if not ok or len(vals) != len(iq_axis):
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

        col_idx, raw_axis = _numeric_header_axis(header)
        if raw_axis.size < 2:
            raise ValueError(f"Invalid header in CSV: {p}")
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
            vals: list[float] = []
            ok = True
            for idx in col_idx:
                if idx >= len(r):
                    ok = False
                    break
                try:
                    vals.append(_parse_float_any(r[idx]))
                except ValueError:
                    ok = False
                    break
            if not ok or len(vals) != len(iq_axis):
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

from dataclasses import dataclass
import numpy as np
from math import pi, sqrt

from .engine_model import Fuel
from .physics import NozzleConfig, VP37HydraulicConfig, NeedleConfig

@dataclass
class InjectionLineConfig:
    length_m: float = 0.4
    diameter_mm: float = 1.5
    segments: int = 5 # Increased segments for better wave representation

@dataclass
class InjectionResult:
    """High-resolution result of a single injection event simulation."""
    time_s: np.ndarray
    line_pressure_pa: np.ndarray # Pressure at the injector
    needle_lift_m: np.ndarray
    mdot_fuel_kg_s: np.ndarray

def solve_injection_hydraulics(
    cam: VP37CamProfile,
    *,
    rpm: float,
    iq_mg: float,
    fuel: Fuel,
    nozzle: NozzleConfig,
    needle: NeedleConfig,
    hyd: VP37HydraulicConfig,
    line: InjectionLineConfig,
    p_cylinder_pa: float,
    cylinder: int = 1,
) -> InjectionResult:
    """
    Solves the 1D injection hydraulics including a lumped-parameter line model
    and dynamic needle lift.
    """
    duration_main_deg = cam.duration_main_crank_deg(
        iq_mg_per_stroke=iq_mg, cylinder=cylinder, iq_max_mg=51.0, delivery_start_frac=0.4
    )
    if duration_main_deg <= 0.0: return InjectionResult(np.array([]), np.array([]), np.array([]), np.array([]))

    a_deg, s_mm = cam._rising_segment(cam._lobe_index_for_cylinder(cylinder))
    if a_deg.size < 2: return InjectionResult(np.array([]), np.array([]), np.array([]), np.array([]))

    dur_pump_deg = max(0.0, duration_main_deg / 2.0)
    a_start, a_end = float(a_deg[0]), min(float(a_deg[-1]), float(a_deg[0]) + dur_pump_deg)
    mask = (a_deg >= a_start) & (a_deg <= a_end)
    a_deg, s_mm = a_deg[mask], s_mm[mask]
    if a_deg.size < 2: return InjectionResult(np.array([]), np.array([]), np.array([]), np.array([]))

    omega_pump = (rpm / 2.0) * 2.0 * pi / 60.0
    total_time = (a_deg[-1] - a_deg[0]) * pi / 180.0 / omega_pump
    dt = 5e-8 # Smaller time step for stability with needle dynamics
    n_steps = int(total_time / dt)
    time_s = np.linspace(0, total_time, n_steps)

    L_seg, A_line, V_seg = line.length_m / line.segments, pi * (line.diameter_mm*1e-3)**2 / 4.0, (pi * (line.diameter_mm*1e-3)**2 / 4.0) * (line.length_m / line.segments)
    rho, K = fuel.density_kg_per_m3, fuel.bulk_modulus_pa
    
    # State: [p_1, q_1, ... p_N, q_N, x_needle, v_needle]
    N = line.segments
    state = np.zeros(2 * N + 2)
    p_back = p_cylinder_pa
    state[::2] = p_back 

    pump_angle_rad = np.interp(time_s, (time_s[0], time_s[-1]), (a_deg[0]*pi/180.0, a_deg[-1]*pi/180.0))
    plunger_pos_m = np.interp(pump_angle_rad, a_deg*pi/180.0, s_mm*1e-3)
    plunger_vel_ms = np.gradient(plunger_pos_m, dt)
    q_plunger = hyd.plunger_area_m2 * plunger_vel_ms

    results = {k: np.zeros_like(time_s) for k in ["line_pressure_pa", "needle_lift_m", "mdot_fuel_kg_s"]}
    
    # Spring preload force from opening pressure
    f_preload_pilot = nozzle.pilot_open_bar * 1e5 * needle.seat_area_m2
    
    for i in range(n_steps - 1):
        deriv = np.zeros_like(state)
        p_injector, x_needle, v_needle = state[-4], state[-2], state[-1]
        
        # Needle dynamics
        f_pressure = p_injector * needle.seat_area_m2
        f_spring = f_preload_pilot + needle.spring_k_n_per_m * x_needle
        f_damping = needle.damping_coeff_ns_per_m * v_needle
        f_net = f_pressure - f_spring - f_damping
        
        a_needle = f_net / needle.mass_kg if x_needle >= 0 else 0
        v_new = v_needle + a_needle * dt
        x_new = x_needle + v_new * dt
        
        if x_new < 0: x_new, v_new = 0, 0 # Needle hits seat
        if x_new > needle.max_lift_m: x_new, v_new = needle.max_lift_m, 0 # Needle hits stop

        deriv[-2], deriv[-1] = v_new - v_needle, a_needle
        
        # Nozzle flow
        area_eff = nozzle.area_m2 * nozzle.discharge_coeff * (x_new / needle.max_lift_m)
        dp_nozzle = max(0.0, p_injector - p_back)
        m_dot_noz = area_eff * sqrt(2.0 * rho * dp_nozzle)
        q_nozzle = m_dot_noz / rho
        
        results["mdot_fuel_kg_s"][i] = m_dot_noz
        results["line_pressure_pa"][i] = p_injector
        results["needle_lift_m"][i] = x_new

        # Line dynamics (mass and momentum)
        for j in range(N):
            p_idx, q_idx = 2*j, 2*j+1
            q_in = q_plunger[i] if j == 0 else state[q_idx-2]
            q_out = q_nozzle if j == N - 1 else state[q_idx]
            deriv[p_idx] = (K / V_seg) * (q_in - q_out)
            
            if j < N - 1:
                p_in, p_out = state[p_idx], state[p_idx+2]
                deriv[q_idx] = (A_line / (rho * L_seg)) * (p_in - p_out)

        state += deriv * dt
        state[-2], state[-1] = x_new, v_new # Update needle state separately
        state[::2] = np.maximum(p_back, state[::2])

    results["line_pressure_pa"][-1] = state[-4]
    results["needle_lift_m"][-1] = state[-2]
    
    return InjectionResult(time_s, results["line_pressure_pa"], results["needle_lift_m"], results["mdot_fuel_kg_s"])
