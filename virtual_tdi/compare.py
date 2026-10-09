"""Tuner what-if comparison (TODO.md Faza 2.C, project goal A).

Runs the same operating point across hardware/calibration variants and
prints a side-by-side metric table - the "what happens if I fit different
nozzles / more boost / other timing" workflow.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

METRICS_OF_INTEREST = [
    "brake_torque_nm_est", "brake_power_kw_est", "imep_bar",
    "peak_pressure_pa", "bsfc_g_per_kwh", "t_exhaust_mean_k",
    "p_intake_mean_pa", "duration_main_deg", "turbo_shaft_rpm",
]


def run_variant(name: str, extra_args: list[str], out_dir: Path,
                base_cmd: list[str]) -> dict[str, float | None]:
    cmd = base_cmd + extra_args + ["--out", str(out_dir), "--no-plot"]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[{name}] CLI failed: {proc.stderr.strip()[-300:]}", file=sys.stderr)
        return {m: None for m in METRICS_OF_INTEREST}
    metrics: dict[str, float | None] = {}
    metrics_path = out_dir / "metrics.txt"
    text = metrics_path.read_text(encoding="utf-8") if metrics_path.exists() else ""
    for line in text.splitlines():
        key, _, value = line.partition(":")
        try:
            metrics[key.strip()] = float(value)
        except ValueError:
            continue
    return {m: metrics.get(m) for m in METRICS_OF_INTEREST}


def main(argv: list[str] | None = None) -> int:
    import tempfile

    parser = argparse.ArgumentParser(
        description="Compare hardware/calibration variants at one operating point "
                    "(tuner what-if workflow, TODO.md project goal A)")
    parser.add_argument("--rpm", type=float, default=1900.0)
    parser.add_argument("--fuel-mg", type=float, default=36.0)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--turbo", action="store_true", default=True)
    parser.add_argument("--no-turbo", dest="turbo", action="store_false")
    parser.add_argument("--turbo-iters", type=int, default=12)
    parser.add_argument(
        "--variant", action="append", required=True,
        metavar="NAME[:nozzle-diameter=0.205|soi-offset=-2|boost-bar=1.8|fuel-mg=30]",
        help="Variant spec: name[:key=value|key=value...]. "
             "Supported keys: nozzle-diameter, nozzle-holes, soi-offset, "
             "boost-bar (p-intake), fuel-mg. NOTE: at a fixed commanded IQ the "
             "nozzle changes injection rate/phasing (hydraulic path), not the "
             "total fuel mass - differences vs stock are physically small by "
             "design; combine with fuel-mg/boost-bar to explore limits.")
    parser.add_argument("--workdir", type=Path, default=None)
    args = parser.parse_args(argv)

    workdir = args.workdir if args.workdir else Path(tempfile.gettempdir()) / "tdi_compare"
    workdir.mkdir(parents=True, exist_ok=True)

    base_cmd = [
        sys.executable, "-m", "virtual_tdi", "--mode", "full",
        "--rpm", str(args.rpm), "--fuel", "diesel",
        "--cycles", str(args.cycles),
        "--thermo-backend", "simple", "--integrator", "rk4",
        # Physical injection path so nozzle variants actually change physics
        # (default wiebe/vp37_main ignores --nozzle-diameter-mm).
        "--hrr-model", "hydraulic_profile", "--duration-model", "auto",
    ]
    if args.turbo:
        base_cmd += ["--turbo", "--turbo-iters", str(args.turbo_iters),
                     "--turbo-relax", "0.6", "--turbo-pr-max", "2.0"]

    results: dict[str, dict] = {}
    for spec in args.variant:
        name, _, kv_str = spec.partition(":")
        extra: list[str] = []
        if kv_str:
            for kv in kv_str.split("|"):
                key, _, value = kv.partition("=")
                if not value:
                    print(f"Invalid variant spec: {spec}", file=sys.stderr)
                    return 2
                if key == "nozzle-diameter":
                    extra += ["--nozzle-diameter-mm", value]
                elif key == "nozzle-holes":
                    extra += ["--nozzle-holes", value]
                elif key == "soi-offset":
                    extra += ["--soi-offset-deg", value]
                elif key == "boost-bar":
                    extra += ["--p-intake-bar", value]
                elif key == "fuel-mg":
                    extra += ["--fuel-mg", value]
                else:
                    print(f"Unknown variant key: {key}", file=sys.stderr)
                    return 2
        results[name] = run_variant(name, extra, workdir / name, base_cmd)

    header = ["variant"] + METRICS_OF_INTEREST
    columns = ["variant"] + METRICS_OF_INTEREST
    widths = []
    for col in columns:
        cell_lens = [len(col)]
        for r in results.values():
            v = r.get(col) if col != "variant" else None
            cell_lens.append(len("n/a" if v is None else f"{v:.2f}"))
        widths.append(max(8, max(cell_lens)))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*header))
    for name, metrics in results.items():
        row = [name] + [
            "n/a" if metrics.get(m) is None else f"{metrics[m]:.2f}"
            for m in METRICS_OF_INTEREST
        ]
        print(fmt.format(*row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
