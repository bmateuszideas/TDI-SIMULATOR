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
