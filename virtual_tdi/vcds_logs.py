"""VCDS diagnostic log parsing and fault classification.

Bridge between the tuner's diagnostic language (VAG-Com/VCDS measuring
blocks, docs/DIAGNOSTYKA_VCDS.md) and the simulator: parses group tables,
extracts operating points for model comparison, and classifies common faults
(overboost/underboost, EGR stuck, MAF underread) per the canonical criteria.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VcdsRow:
    time_s: float
    rpm: float
    fields: dict[str, float | str] = field(default_factory=dict)


def _parse_number(token: str) -> float | None:
    try:
        return float(token.replace(",", ".").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def parse_group(text: str, *, group: int) -> list[VcdsRow]:
    """Parse a VCDS group table (rows: TIME STAMP + numeric columns)."""
    rows: list[VcdsRow] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Column separators: pipe or runs of whitespace (NOT commas - comma is
        # the decimal separator in European VCDS logs, e.g. "1285,2").
        cells = re.split(r"\s*\|\s*|\s{2,}|\t", line)
        cells = [c.strip() for c in cells if c.strip() not in ("", "|")]
        if len(cells) < 2:
            continue
        t = _parse_number(cells[0])
        if t is None:
            continue
        values: list[float | None] = []
        for c in cells[1:]:
            v = _parse_number(c)
            values.append(v)
        # numeric rows only (skip OFF/ON markers handled as strings)
        if all(v is None for v in values):
            continue
        fields: dict[str, float | str] = {}
        for idx, (c, v) in enumerate(zip(cells[1:], values), start=1):
            key = f"p{idx}"
            fields[key] = v if v is not None else c
        rpm = fields.get("p1") if group != 0 else None
        rows.append(VcdsRow(time_s=t, rpm=float(rpm) if isinstance(rpm, (int, float)) else 0.0,
                            fields=fields))
    return rows


@dataclass(frozen=True)
class OperatingPoint:
    rpm: float
    boost_spec_mbar: float | None = None
    boost_actual_mbar: float | None = None
    maf_spec_mg_r: float | None = None
    maf_actual_mg_r: float | None = None
    iq_requested_mg_r: float | None = None
    iq_torque_limit_mg_r: float | None = None
    iq_smoke_limit_mg_r: float | None = None
    n75_duty_pct: float | None = None
    egr_duty_pct: float | None = None


def to_operating_points(rows_003: list[VcdsRow] | None = None,
                        rows_008: list[VcdsRow] | None = None,
                        rows_010: list[VcdsRow] | None = None,
                        rows_011: list[VcdsRow] | None = None) -> list[OperatingPoint]:
    """Merge per-group rows (keyed by RPM proximity) into operating points."""
    by_rpm_003 = {round(r.rpm): r for r in (rows_003 or [])}
    by_rpm_008 = {round(r.rpm): r for r in (rows_008 or [])}
    by_rpm_010 = {round(r.rpm): r for r in (rows_010 or [])}
    rpms = sorted({r.rpm for r in (rows_011 or [])} |
                  {r.rpm for r in (rows_003 or [])} |
                  {r.rpm for r in (rows_008 or [])} |
                  {r.rpm for r in (rows_010 or [])})
    points: list[OperatingPoint] = []
    for rpm in rpms:
        key = round(rpm)
        g3 = by_rpm_003.get(key)
        g8 = by_rpm_008.get(key)
        g10 = by_rpm_010.get(key)
        g11 = next((r for r in (rows_011 or []) if abs(r.rpm - rpm) < 30.0), None)
        points.append(OperatingPoint(
            rpm=float(rpm),
            maf_spec_mg_r=_f(g3, "p2") if g3 else None,
            maf_actual_mg_r=_f(g3, "p3") if g3 else None,
            egr_duty_pct=_f(g3, "p4") if g3 else None,
            iq_requested_mg_r=_f(g8, "p2") if g8 else None,
            iq_torque_limit_mg_r=_f(g8, "p3") if g8 else None,
            iq_smoke_limit_mg_r=_f(g8, "p4") if g8 else None,
            boost_spec_mbar=_f(g11, "p2") if g11 else None,
            boost_actual_mbar=_f(g11, "p3") if g11 else None,
            n75_duty_pct=_f(g11, "p4") if g11 else None,
        ))
    return points


def _f(row: VcdsRow, key: str) -> float | None:
    v = row.fields.get(key)
    return float(v) if isinstance(v, (int, float)) else None


@dataclass(frozen=True)
class FaultHypothesis:
    name: str
    evidence: str
    severity: str  # "info" | "suspect" | "fault"


def classify(points: list[OperatingPoint]) -> list[FaultHypothesis]:
    """Classify common faults per the canonical diagnostic rules
    (docs/DIAGNOSTYKA_VCDS.md)."""
    out: list[FaultHypothesis] = []

    # Rule: overboost (actual >> spec) -> notlauf risk, N75/vanes fault.
    over = [p for p in points
            if p.boost_actual_mbar and p.boost_spec_mbar
            and p.boost_actual_mbar > p.boost_spec_mbar * 1.05]
    if over:
        worst = max(over, key=lambda p: p.boost_actual_mbar - p.boost_spec_mbar)
        out.append(FaultHypothesis(
            "overboost", f"{len(over)} pts actual>spec (worst +{worst.boost_actual_mbar - worst.boost_spec_mbar:.0f} mbar @ {worst.rpm:.0f} rpm); N75/VTG vanes suspect (notlauf/DTC 00575 risk)", "fault"))

    # Rule: underboost (actual << spec) -> turbo wear / exhaust restriction / vacuum.
    under = [p for p in points
             if p.boost_actual_mbar and p.boost_spec_mbar
             and p.boost_actual_mbar < p.boost_spec_mbar * 0.92]
    if under:
        worst = min(under, key=lambda p: p.boost_actual_mbar / p.boost_spec_mbar)
        out.append(FaultHypothesis(
            "underboost", f"{len(under)} pts actual<spec (worst {100*(worst.boost_actual_mbar/worst.boost_spec_mbar-1):.1f}% @ {worst.rpm:.0f} rpm); turbo wear/exhaust restriction/vacuum suspect", "fault"))

    # Rule: MAF actual vs spec (group 003) mismatch at steady state.
    maf_bad = [p for p in points
               if p.maf_actual_mg_r and p.maf_spec_mg_r
               and p.rpm > 1200.0
               and abs(p.maf_actual_mg_r - p.maf_spec_mg_r) > 0.1 * p.maf_spec_mg_r + 20.0]
    if maf_bad:
        out.append(FaultHypothesis(
            "maf_mismatch", f"{len(maf_bad)} pts MAF actual != spec (>10%+20); EGR position or G70 sensor suspect", "suspect"))

    # Rule: smoke limit lowest IQ (group 008) -> G70 underreads (engine derated by MAF).
    smoke_min = [p for p in points
                 if p.iq_smoke_limit_mg_r is not None
                 and p.iq_torque_limit_mg_r is not None
                 and p.iq_smoke_limit_mg_r < p.iq_torque_limit_mg_r - 0.5]
    if smoke_min:
        out.append(FaultHypothesis(
            "maf_underread", f"{len(smoke_min)} pts smoke limit < torque limit: engine derated by MAF (G70 underread or EGR stuck open)", "fault"))

    # Rule: healthy baseline.
    if not out:
        out.append(FaultHypothesis(
            "healthy", "boost spec==actual, MAF spec==actual, limits ordered; matches factory maps", "info"))
    return out
