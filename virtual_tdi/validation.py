"""Validation runner: compares simulator output against ALH reference points.

Points are defined in validation/reference_points.yaml (Faza 1 in TODO.md).
Each point runs the full-cycle CLI in a subprocess (so the whole pipeline,
including ECU maps and turbo coupling, is exercised) and the resulting
metrics are compared against reference ranges with tolerances.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REFERENCE = ROOT / "validation" / "reference_points.yaml"

METRIC_ALIASES = {
    "brake_torque_nm": "brake_torque_nm_est",
    "brake_power_kw": "brake_power_kw_est",
    "bsfc_g_per_kwh": "bsfc_g_per_kwh",
    "imep_bar": "imep_bar",
    "peak_pressure_pa": "peak_pressure_pa",
    "egt_k": "t_exhaust_mean_k",
}


def load_reference_points(path: str | Path = DEFAULT_REFERENCE) -> list[dict]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    points = data.get("points") or []
    if not points:
        raise ValueError(f"No points found in reference file: {p}")
    return points


def _read_metrics(out_dir: Path) -> dict[str, float]:
    metrics: dict[str, float] = {}
    metrics_path = out_dir / "metrics.txt"
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.txt not found in {out_dir}")
    for line in metrics_path.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        try:
            metrics[key.strip()] = float(value.strip())
        except ValueError:
            continue
    return metrics


def run_point(point: dict, *, workdir: Path, verbose: bool = False) -> dict:
    """Runs one reference point through the CLI subprocess and returns a result row."""
    name = point.get("name") or f"rpm{point.get('rpm')}"
    out_dir = workdir / name
    cmd = [
        sys.executable, "-m", "virtual_tdi",
        "--mode", "full",
        "--rpm", str(point["rpm"]),
        "--fuel", "diesel",
        "--fuel-mg", str(point["fuel_mg_per_cycle_per_cyl"]),
        "--out", str(out_dir),
        "--no-plot",
        "--thermo-backend", "simple",
        "--integrator", "rk4",
        # Multi-cycle: the first cycle charges the dynamic manifolds from the
        # assumed initial state; steady-state metrics need >= 2 cycles.
        "--cycles", str(int(point.get("cycles", 2))),
    ]
    if point.get("soi_offset_deg") is not None:
        cmd += ["--soi-offset-deg", str(point["soi_offset_deg"])]
    if point.get("turbo"):
        cmd += ["--turbo", "--turbo-iters", str(int(point.get("turbo_iters", 12))),
                "--turbo-relax", "0.6", "--turbo-pr-max", "2.0"]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Point {name}: CLI failed: {proc.stderr.strip()[-400:]}")

    metrics = _read_metrics(out_dir)
    checks = []
    for metric, spec in (point.get("expect") or {}).items():
        key = METRIC_ALIASES.get(metric, metric)
        simulated = metrics.get(key)
        ref = float(spec["ref"])
        tol = float(spec["tol_pct"]) / 100.0
        if simulated is None:
            checks.append({"metric": metric, "ref": ref, "sim": None,
                           "delta_pct": None, "status": "MISSING"})
            continue
        delta_pct = (simulated - ref) / ref * 100.0 if ref else 0.0
        status = "PASS" if abs(simulated - ref) <= abs(ref) * tol else "FAIL"
        checks.append({"metric": metric, "ref": ref, "sim": simulated,
                        "delta_pct": delta_pct, "status": status})
    passed = all(c["status"] == "PASS" for c in checks)
    row = {"name": name, "rpm": point["rpm"], "checks": checks, "passed": passed,
           "known_gap": point.get("known_gap")}
    if verbose:
        print(f"[{name}] rpm={point['rpm']} -> {'PASS' if passed else 'FAIL'}")
        for c in checks:
            sim = "n/a" if c["sim"] is None else f"{c['sim']:.3f}"
            print(f"    {c['metric']:<18} ref={c['ref']:<12.4g} sim={sim:<12} "
                  f"delta={c['delta_pct'] if c['delta_pct'] is not None else 'n/a'}% [{c['status']}]")
    return row


def run_validation(reference_path: str | Path = DEFAULT_REFERENCE,
                   workdir: str | Path | None = None,
                   verbose: bool = True) -> list[dict]:
    points = load_reference_points(reference_path)
    workdir = Path(workdir) if workdir else Path(tempfile.gettempdir()) / "tdi_validation"
    workdir.mkdir(parents=True, exist_ok=True)
    rows = [run_point(p, workdir=workdir, verbose=verbose) for p in points]
    n_pass = sum(1 for r in rows if r["passed"])
    if verbose:
        print(f"\nValidation summary: {n_pass}/{len(rows)} points passed.")
    return rows


def run_map_grid_validation(*, n_rpm: int = 4, n_iq: int = 3,
                            workdir: Path | None = None,
                            verbose: bool = True) -> list[dict]:
    """Map-grid validation: compare model intake pressure against the factory
    BOOST map across the ECU working area (docs/MAPY_ECU_KONWENCJE.md)."""
    import subprocess
    import tempfile

    from virtual_tdi.edc_maps import BoostTargetMap2D, SmokeLimiterMap2D
    from virtual_tdi.soi_map import SOIMap2D
    from validation.map_consistency import build_grid

    soi_map = SOIMap2D.from_csv(next(Path(".").glob("*SOI*Table 1.csv")))
    boost_map = BoostTargetMap2D.from_csv(next(Path(".").glob("Mapa_BOOST*.csv")))
    smoke_map = SmokeLimiterMap2D.from_csv(next(Path(".").glob("SmokeLimiter*.csv")))
    grid = build_grid(soi_map=soi_map, boost_map=boost_map, smoke_map=smoke_map,
                      n_rpm=n_rpm, n_iq=n_iq)

    workdir = Path(workdir) if workdir else Path(tempfile.gettempdir()) / "tdi_mapgrid"
    workdir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for pt in grid:
        out_dir = workdir / f"r{int(pt.rpm)}_iq{pt.iq_mg:.0f}"
        cmd = [
            sys.executable, "-m", "virtual_tdi", "--mode", "full",
            "--rpm", str(pt.rpm), "--fuel", "diesel",
            "--fuel-mg", str(pt.iq_mg),
            "--soi-main", str(pt.soi_model_deg),
            "--turbo", "--turbo-iters", "12", "--turbo-relax", "0.6",
            "--turbo-pr-max", "2.0",
            "--cycles", "2",
            "--thermo-backend", "simple", "--integrator", "rk4",
            "--out", str(out_dir), "--no-plot",
        ]
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if proc.returncode != 0:
            if verbose:
                print(f"[{pt.rpm:.0f} rpm, {pt.iq_mg:.1f} mg] CLI FAILED: {proc.stderr.strip()[-200:]}")
            rows.append({"rpm": pt.rpm, "iq": pt.iq_mg, "p_sim_mbar": None,
                         "p_ref_mbar": pt.boost_target_mbar_abs, "delta_pct": None,
                         "status": "ERROR"})
            continue
        metrics = _read_metrics(out_dir)
        p_sim_mbar = metrics.get("p_intake_mean_pa", 0.0) / 100.0
        delta_pct = (p_sim_mbar - pt.boost_target_mbar_abs) / pt.boost_target_mbar_abs * 100.0
        status = "PASS" if abs(delta_pct) <= 15.0 else "FAIL"
        rows.append({"rpm": pt.rpm, "iq": pt.iq_mg, "p_sim_mbar": p_sim_mbar,
                     "p_ref_mbar": pt.boost_target_mbar_abs, "delta_pct": delta_pct,
                     "status": status})
        if verbose:
            print(f"[{pt.rpm:.0f} rpm, {pt.iq_mg:5.1f} mg] "
                  f"boost sim={p_sim_mbar:7.1f} mbar, map={pt.boost_target_mbar_abs:7.1f} mbar, "
                  f"delta={delta_pct:+6.1f}% [{status}]")
    n_pass = sum(1 for r in rows if r["status"] == "PASS")
    if verbose:
        print(f"\nMap-grid validation: {n_pass}/{len(rows)} points within 15% of the factory BOOST map.")
    return rows


def main(argv: list[str] | None = None) -> int:
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="Validate simulator against ALH reference points")
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE,
                        help="Path to reference_points.yaml")
    parser.add_argument("--workdir", type=Path, default=None,
                        help="Directory for run outputs (default: tempdir)")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-point output")
    parser.add_argument("--map-grid", action="store_true",
                        help="Run the map-driven grid validation (factory BOOST map "
                             "as reference across the ECU working area)")
    parser.add_argument("--grid-rpm", type=int, default=4, help="Map grid: RPM sample count")
    parser.add_argument("--grid-iq", type=int, default=3, help="Map grid: IQ sample count")
    args = parser.parse_args(argv)

    if args.map_grid:
        workdir = args.workdir if args.workdir else Path(tempfile.gettempdir()) / "tdi_mapgrid"
        rows = run_map_grid_validation(n_rpm=args.grid_rpm, n_iq=args.grid_iq,
                                       workdir=workdir, verbose=not args.quiet)
        return 0 if all(r["status"] == "PASS" for r in rows) else 1

    workdir = args.workdir if args.workdir else Path(tempfile.gettempdir()) / "tdi_validation"
    rows = run_validation(args.reference, workdir=workdir, verbose=not args.quiet)
    return 0 if all(r["passed"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
