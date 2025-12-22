from __future__ import annotations

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

