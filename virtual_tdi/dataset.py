from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .config_loader import create_geometry_from_config, load_yaml_config
from .edc_maps import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D
from .full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle
from .hydraulics import NozzleConfig, VP37HydraulicConfig, estimate_pilot_ratio
from .lift_table import ValveLiftTable
from .models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig
from .n146_map import N146VoltageMap2D
from .soi_map import SOIMap2D
from .valvetrain import ValveFlow, ValveTiming
from .vp37 import VP37LineModel, apply_hydraulic_delay
from .vp37_cam import VP37CamProfile


@dataclass(frozen=True)
class DatasetConfig:
    n: int = 1000
    seed: int = 1
    rpm_min: float = 1500.0
    rpm_max: float = 1500.0
    step_deg: float = 1.0
    cycles: int = 1
    ecu_mode: str = "off"  # off|report|limit
    use_soi_map: bool = False
    use_n146_map: bool = False
    use_boost_map: bool = False
    p_intake_bar_min: float = 1.0
    p_intake_bar_max: float = 1.8
    p_amb_bar: float = 1.0
    p_exhaust_bar: float = 1.15
    t_exhaust_k: float = 800.0
    t_intake_k: float = 300.0
    fuel_temp_min_c: float = 20.0
    fuel_temp_max_c: float = 90.0
    # Inputs sampling
    n146_mv_min: float = 1500.0
    n146_mv_max: float = 4500.0
    soi_offset_min: float = -3.0
    soi_offset_max: float = 3.0
    # Limit ranges when map missing
    iq_min: float = 2.0
    iq_max: float = 45.0
    # Fuel choices
    fuels: tuple[str, ...] = ("diesel", "svo")
    iq_basis: str = "mass"  # mass|volume
    nozzle_diameters_mm: tuple[float, ...] = (0.184, 0.205, 0.216, 0.230, 0.260)
    nozzle_flow_exp: float = 1.0
    pilot_model: str = "fixed"  # fixed|hydraulic
    pilot_fraction: float = 0.12
    nozzle_cd: float = 0.72
    nozzle_pilot_open_bar: float = 190.0
    nozzle_main_open_bar: float = 300.0
    nozzle_pilot_area_frac: float = 0.30
    plunger_diameter_mm: float = 10.0
    chamber_volume_mm3: float = 200.0
    line_volume_mm3: float = 400.0
    back_pressure_bar: float = 50.0
    thermo_backend: str = "simple"
    flow_backend: str = "simple"
    coolprop_fluid: str = "Air"
    ignition_delay_model: str = "arrhenius"
    ignition_delay_deg: float = 5.0
    strict_backends: bool = True
    integrator: str = "scipy"
    scipy_method: str = "Radau"
    scipy_rtol: float = 1.0e-7
    scipy_atol: float = 1.0e-9
    scipy_max_step_deg: float = 1.0
    # Hardware metadata (not yet used for physics; logged for ML)
    nozzle_holes: int = 5
    nozzle_diameter_mm: float = 0.184
    vp37_camplate: str = "DE110"
    cam_profile_file: str = "skok_tloczka_vp37_de110.csv"
    valvetrain_profile_file: str = "profil_krzywek_4cylindry.md"


def _resolve_map_path(path: Path | None, pattern: str) -> Path | None:
    if path is not None and path.exists():
        return path
    return next(Path(".").glob(pattern), None)


def generate_dataset(
    cfg: DatasetConfig,
    *,
    geom: EngineGeometry | None = None,
    out_csv: Path | None = None,
    # Optional explicit paths
    soi_map_path: Path | None = None,
    n146_map_path: Path | None = None,
    smoke_map_path: Path | None = None,
    egr_map_path: Path | None = None,
    boost_map_path: Path | None = None,
    valve_table_path: Path | None = None,
    vp37_cam_path: Path | None = None,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(int(cfg.seed))

    if geom is None:
        geom = create_geometry_from_config(load_yaml_config("engine_reference_sources.yaml"))

    valve_timing = ValveTiming()
    valve_flow = ValveFlow()

    valve_table = None
    vt = _resolve_map_path(valve_table_path, "profil_krzywek_4cylindry.md")
    if vt is not None:
        valve_table = ValveLiftTable.from_markdown(vt)

    cam = None
    cam_path = _resolve_map_path(vp37_cam_path, "skok_tloczka_vp37_de110.csv")
    if cam_path is not None:
        cam = VP37CamProfile.from_csv(cam_path)

    soi_map = None
    sp = _resolve_map_path(soi_map_path, "*SOI*Table 1.csv")
    if sp is not None:
        soi_map = SOIMap2D.from_csv(sp)

    n146_map = None
    npth = _resolve_map_path(n146_map_path, "*N146*Table 1.csv")
    if npth is not None:
        n146_map = N146VoltageMap2D.from_csv(npth)

    smoke_map = None
    smp = _resolve_map_path(smoke_map_path, "SmokeLimiter*.csv")
    if smp is not None:
        smoke_map = SmokeLimiterMap2D.from_csv(smp)

    egr_map = None
    egp = _resolve_map_path(egr_map_path, "Mapa_EGR*.csv")
    if egp is not None:
        egr_map = EGRMafTargetMap2D.from_csv(egp)

    boost_map = None
    bmp = _resolve_map_path(boost_map_path, "Mapa_BOOST*.csv")
    if bmp is not None:
        boost_map = BoostTargetMap2D.from_csv(bmp)

    def pick_fuel(name: str) -> Fuel:
        if name == "diesel":
            return Fuel.diesel()
        if name == "svo":
            return Fuel.svo_rapeseed()
        if name == "methanol":
            return Fuel.methanol()
        raise ValueError(f"Unknown fuel: {name}")

    rows: list[dict[str, Any]] = []
    for i in range(int(cfg.n)):
        rpm = float(rng.uniform(cfg.rpm_min, cfg.rpm_max))
        fuel_name = str(rng.choice(cfg.fuels))
        fuel = pick_fuel(fuel_name)
        fuel_temp_c = float(rng.uniform(cfg.fuel_temp_min_c, cfg.fuel_temp_max_c))
        # Simplified density correction (similar to user-provided coef)
        rho_corr = fuel.density_kg_per_m3 * (1.0 - (fuel_temp_c - 15.0) * 0.00083)
        rho_corr = max(600.0, rho_corr)
        nozzle_diam = float(rng.choice(cfg.nozzle_diameters_mm))

        soi_offset = float(rng.uniform(cfg.soi_offset_min, cfg.soi_offset_max))

        # Commanded IQ (mg/str)
        if cfg.use_n146_map and n146_map is not None:
            n146_mv = float(rng.uniform(cfg.n146_mv_min, cfg.n146_mv_max))
            iq_cmd = float(n146_map.iq_from_mv(rpm, n146_mv))
        else:
            n146_mv = None
            iq_cmd = float(rng.uniform(cfg.iq_min, cfg.iq_max))

        # ECU derivation: EGR->MAF, smoke limiter -> iq_eff, boost target
        maf = 850.0
        if egr_map is not None:
            maf = float(egr_map.maf_target(rpm, iq_cmd))
        iq_max_smoke = None
        if smoke_map is not None:
            iq_max_smoke = float(smoke_map.iq_max(rpm, maf))
        iq_eff_cmd = float(iq_cmd)
        if cfg.ecu_mode == "limit" and iq_max_smoke is not None:
            iq_eff_cmd = min(iq_eff_cmd, iq_max_smoke)
            if egr_map is not None:
                maf = float(egr_map.maf_target(rpm, iq_eff_cmd))
            iq_max_smoke = float(smoke_map.iq_max(rpm, maf)) if smoke_map is not None else None
            if iq_max_smoke is not None:
                iq_eff_cmd = min(iq_eff_cmd, iq_max_smoke)

        boost_target_mbar = None
        if boost_map is not None:
            boost_target_mbar = float(boost_map.map_target_mbar(rpm, iq_eff_cmd))

        # SOI (model convention)
        if cfg.use_soi_map and soi_map is not None:
            soi_main = float(soi_map.soi_deg_model_convention(rpm, iq_eff_cmd, offset_deg=soi_offset))
        else:
            soi_main = float(-6.0 + soi_offset)
        soi_pilot = float(soi_main - 6.0)

        # Mass vs volume basis for fuel quantity
        if cfg.iq_basis == "volume":
            rho_ref = Fuel.diesel().density_kg_per_m3
            iq_mass = iq_eff_cmd * (rho_corr / rho_ref)
        else:
            iq_mass = iq_eff_cmd

        # Duration from VP37
        duration_main = 42.0
        if cam is not None:
            duration_main = float(
                cam.duration_main_crank_deg(
                    iq_mg_per_stroke=iq_eff_cmd,
                    cylinder=1,
                    iq_max_mg=51.0,
                    delivery_start_frac=0.40,
                )
            )
        # Nozzle size influence (area scaling)
        base_d = 0.184
        area_ratio = (base_d**2) / (nozzle_diam**2)
        duration_main = duration_main * (area_ratio ** float(cfg.nozzle_flow_exp))

        pilot_fraction = float(cfg.pilot_fraction)
        if cfg.pilot_model == "hydraulic":
            if cam is None:
                raise ValueError("pilot_model=hydraulic requires vp37 cam profile.")
            nozzle = NozzleConfig(
                diameter_mm=float(nozzle_diam),
                holes=int(cfg.nozzle_holes),
                discharge_coeff=float(cfg.nozzle_cd),
                pilot_open_bar=float(cfg.nozzle_pilot_open_bar),
                main_open_bar=float(cfg.nozzle_main_open_bar),
                pilot_area_frac=float(cfg.nozzle_pilot_area_frac),
            )
            hyd = VP37HydraulicConfig(
                plunger_diameter_mm=float(cfg.plunger_diameter_mm),
                chamber_volume_mm3=float(cfg.chamber_volume_mm3),
                line_volume_mm3=float(cfg.line_volume_mm3),
                back_pressure_bar=float(cfg.back_pressure_bar),
            )
            pilot_fraction = estimate_pilot_ratio(
                cam,
                rpm=rpm,
                duration_main_deg=float(duration_main),
                fuel=fuel,
                nozzle=nozzle,
                hyd=hyd,
                cylinder=1,
            )

        schedule = InjectionSchedule(
            soi_pilot_deg=soi_pilot,
            soi_main_deg=soi_main,
            pilot_fraction=float(pilot_fraction),
            duration_pilot_deg=8.0,
            duration_main_deg=duration_main,
        )
        schedule = apply_hydraulic_delay(schedule, fuel=fuel, rpm=rpm, model=VP37LineModel(line_length_m=0.0))

        p_intake_bar = float(rng.uniform(cfg.p_intake_bar_min, cfg.p_intake_bar_max))
        if cfg.use_boost_map and boost_target_mbar is not None:
            p_intake_bar = boost_target_mbar / 1000.0 - float(cfg.p_amb_bar)
            p_intake_bar = max(0.01, p_intake_bar)

        boundaries = BoundaryConditions(
            intake_pressure_pa=p_intake_bar * 1e5,
            intake_temp_k=cfg.t_intake_k,
            exhaust_pressure_pa=cfg.p_exhaust_bar * 1e5,
            exhaust_temp_k=cfg.t_exhaust_k,
        )

        combustion_cfg = CombustionConfig(
            hrr_model="vp37_main" if cam is not None else "wiebe",
            ignition_delay_model=str(cfg.ignition_delay_model),
            fixed_ignition_delay_deg=float(cfg.ignition_delay_deg),
        )
        models = SimulationConfig(
            rpm=rpm,
            step_deg=cfg.step_deg,
            fuel_mg_per_cycle_per_cyl=iq_mass,
            combustion=combustion_cfg,
            thermo_backend=str(cfg.thermo_backend),
            flow_backend=str(cfg.flow_backend),
            coolprop_fluid=str(cfg.coolprop_fluid),
            strict_backends=bool(cfg.strict_backends),
            integrator=str(cfg.integrator),
            scipy_method=str(cfg.scipy_method),
            scipy_rtol=float(cfg.scipy_rtol),
            scipy_atol=float(cfg.scipy_atol),
            scipy_max_step_deg=float(cfg.scipy_max_step_deg),
        )
        sim_cfg = FullCycleConfig(
            rpm=rpm,
            step_deg=cfg.step_deg,
            cycles=max(1, int(cfg.cycles)),
            boundaries=boundaries,
            valve_timing=valve_timing,
            valve_flow=valve_flow,
            valve_lift_table=valve_table,
            cylinder=1,
            vp37_cam_profile=cam,
            vp37_iq_max_mg=51.0,
            vp37_delivery_start_frac=0.40,
            fuel_mg_per_cycle_per_cyl=iq_mass,
            models=models,
        )

        res = simulate_full_cycle(geom, fuel, schedule, sim_cfg)

        row: dict[str, Any] = {
            "idx": i,
            "rpm": rpm,
            "fuel": fuel_name,
            "fuel_temp_c": fuel_temp_c,
            "fuel_density_kg_m3": float(rho_corr),
            "iq_basis": cfg.iq_basis,
            "nozzle_diameter_mm": nozzle_diam,
            "nozzle_holes": int(cfg.nozzle_holes),
            "hw_vp37_camplate": str(cfg.vp37_camplate),
            "hw_vp37_cam_profile_file": str(cfg.cam_profile_file),
            "hw_valvetrain_profile_file": str(cfg.valvetrain_profile_file),
            "soi_offset_deg": soi_offset,
            "iq_cmd_mg_per_str": iq_cmd,
            "iq_eff_cmd_mg_per_str": iq_eff_cmd,
            "iq_eff_mg_per_str": iq_mass,
            "n146_mv": n146_mv,
            "maf_target_mg_per_str": maf,
            "smoke_iq_max_mg_per_str": iq_max_smoke,
            "boost_target_mbar_abs": boost_target_mbar,
            "p_intake_bar_used": p_intake_bar,
            "soi_main_deg_model": soi_main,
            "duration_main_deg": duration_main,
            "pilot_model": cfg.pilot_model,
            "pilot_fraction": pilot_fraction,
        }
        # Flatten selected metrics
        for k, v in res.metrics.items():
            row[f"out_{k}"] = v
        rows.append(row)

    if out_csv is not None:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        # Stable header order: common inputs then metrics
        keys = list(rows[0].keys()) if rows else []
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    return rows


def _make_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate synthetic dataset from the Virtual TDI simulator.")
    p.add_argument(
        "--engine-config",
        type=Path,
        default=Path("engine_reference_sources.yaml"),
        help="Path to engine configuration YAML file.",
    )
    p.add_argument("--n", type=int, default=2000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--rpm-min", type=float, default=1500.0)
    p.add_argument("--rpm-max", type=float, default=1500.0)
    p.add_argument("--step-deg", type=float, default=1.0)
    p.add_argument("--cycles", type=int, default=1)
    p.add_argument("--ecu", choices=["off", "report", "limit"], default="off")
    p.add_argument("--use-soi-map", action="store_true")
    p.add_argument("--use-n146-map", action="store_true")
    p.add_argument("--use-boost-map", action="store_true")
    p.add_argument("--p-intake-min", type=float, default=1.0, help="Physics mode: intake pressure min [bar abs]")
    p.add_argument("--p-intake-max", type=float, default=1.8, help="Physics mode: intake pressure max [bar abs]")
    p.add_argument("--p-amb-bar", type=float, default=1.0, help="Ambient pressure [bar abs]")
    p.add_argument("--fuel-temp-min", type=float, default=20.0)
    p.add_argument("--fuel-temp-max", type=float, default=90.0)
    p.add_argument("--iq-basis", choices=["mass", "volume"], default="mass")
    p.add_argument("--nozzles", type=str, default="0.184,0.205,0.216,0.230,0.260")
    p.add_argument("--nozzle-flow-exp", type=float, default=1.0, help="Duration scaling exponent vs area ratio.")
    p.add_argument("--pilot-model", choices=["fixed", "hydraulic"], default="fixed")
    p.add_argument("--pilot-frac", type=float, default=0.12, help="Pilot fraction for fixed model.")
    p.add_argument("--thermo-backend", choices=["simple", "coolprop"], default="coolprop")
    p.add_argument("--flow-backend", choices=["simple", "fluids"], default="fluids")
    p.add_argument("--coolprop-fluid", type=str, default="Air")
    p.add_argument("--ignition-delay", choices=["arrhenius", "fixed_deg"], default="arrhenius")
    p.add_argument("--ignition-delay-deg", type=float, default=5.0)
    strict_group = p.add_mutually_exclusive_group()
    strict_group.add_argument("--strict-backends", dest="strict_backends", action="store_true")
    strict_group.add_argument("--no-strict-backends", dest="strict_backends", action="store_false")
    p.set_defaults(strict_backends=True)
    p.add_argument("--integrator", choices=["rk4", "scipy"], default="scipy")
    p.add_argument("--scipy-method", type=str, default="Radau")
    p.add_argument("--scipy-rtol", type=float, default=1.0e-7)
    p.add_argument("--scipy-atol", type=float, default=1.0e-9)
    p.add_argument("--scipy-max-step-deg", type=float, default=1.0)
    p.add_argument("--out", type=Path, default=Path("data") / "synthetic.csv")
    p.add_argument("--n146-mv-min", type=float, default=1500.0)
    p.add_argument("--n146-mv-max", type=float, default=4500.0)
    p.add_argument("--soi-offset-min", type=float, default=-3.0)
    p.add_argument("--soi-offset-max", type=float, default=3.0)
    p.add_argument("--iq-min", type=float, default=2.0)
    p.add_argument("--iq-max", type=float, default=45.0)
    p.add_argument("--fuels", type=str, default="diesel,svo")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _make_argparser().parse_args(argv)
    cfg = DatasetConfig(
        n=int(args.n),
        seed=int(args.seed),
        rpm_min=float(args.rpm_min),
        rpm_max=float(args.rpm_max),
        step_deg=float(args.step_deg),
        cycles=int(args.cycles),
        ecu_mode=str(args.ecu),
        use_soi_map=bool(args.use_soi_map),
        use_n146_map=bool(args.use_n146_map),
        use_boost_map=bool(args.use_boost_map),
        p_intake_bar_min=float(args.p_intake_min),
        p_intake_bar_max=float(args.p_intake_max),
        p_amb_bar=float(args.p_amb_bar),
        fuel_temp_min_c=float(args.fuel_temp_min),
        fuel_temp_max_c=float(args.fuel_temp_max),
        n146_mv_min=float(args.n146_mv_min),
        n146_mv_max=float(args.n146_mv_max),
        soi_offset_min=float(args.soi_offset_min),
        soi_offset_max=float(args.soi_offset_max),
        iq_min=float(args.iq_min),
        iq_max=float(args.iq_max),
        fuels=tuple([s.strip() for s in str(args.fuels).split(",") if s.strip()]),
        iq_basis=str(args.iq_basis),
        nozzle_diameters_mm=tuple([float(s) for s in str(args.nozzles).split(",") if s.strip()]),
        nozzle_flow_exp=float(args.nozzle_flow_exp),
        pilot_model=str(args.pilot_model),
        pilot_fraction=float(args.pilot_frac),
        thermo_backend=str(args.thermo_backend),
        flow_backend=str(args.flow_backend),
        coolprop_fluid=str(args.coolprop_fluid),
        ignition_delay_model=str(args.ignition_delay),
        ignition_delay_deg=float(args.ignition_delay_deg),
        strict_backends=bool(args.strict_backends),
        integrator=str(args.integrator),
        scipy_method=str(args.scipy_method),
        scipy_rtol=float(args.scipy_rtol),
        scipy_atol=float(args.scipy_atol),
        scipy_max_step_deg=float(args.scipy_max_step_deg),
    )
    engine_config = load_yaml_config(args.engine_config)
    geom = create_geometry_from_config(engine_config)
    rows = generate_dataset(cfg, geom=geom, out_csv=args.out)
    print(f"Wrote {len(rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
