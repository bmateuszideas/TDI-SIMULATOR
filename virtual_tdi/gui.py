"""Tkinter GUI for the Virtual TDI simulator.

All argument-construction logic lives in pure, headless-testable functions
(``SETTING_SPECS``, ``SETTINGS_DEFAULTS``, ``build_cli_args``,
``parse_soi_sweep``, ``settings_to_json``, ``settings_from_json``).
The Tk widgets only read/write a plain ``dict`` of setting values, so the
core behaviour is unit-testable without a display.
"""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

from virtual_tdi.cli import _make_argparser

CLI_PARSER = _make_argparser()
_CLI_ACTIONS = {a.dest: a for a in CLI_PARSER._actions if a.dest not in ("help",)}
_CLI_DEFAULTS = {dest: a.default for dest, a in _CLI_ACTIONS.items()}

FILE_FIELDS = (
    "engine_config",
    "n146_map",
    "soi_map",
    "smoke_map",
    "egr_map",
    "boost_map",
    "vp37_cam",
    "valve_table",
)

_FILE_EXTENSIONS = {
    "engine_config": ("Pliki YAML", "*.yaml"),
    "n146_map": ("Pliki CSV", "*.csv"),
    "soi_map": ("Pliki CSV", "*.csv"),
    "smoke_map": ("Pliki CSV", "*.csv"),
    "egr_map": ("Pliki CSV", "*.csv"),
    "boost_map": ("Pliki CSV", "*.csv"),
    "vp37_cam": ("Pliki CSV", "*.csv"),
    "valve_table": ("Pliki Markdown", "*.md"),
}


def _cli_default(name: str):
    default = _CLI_DEFAULTS[name]
    if isinstance(default, Path):
        return str(default)
    return default


def _as_float(value, error: str = "not a number") -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(error)


def _spec(name: str, label: str, modes: str = "full", choices=None) -> dict:
    return {"name": name, "label": label, "modes": modes, "choices": choices}


SETTING_SPECS: dict[str, list[dict]] = {
    "Silnik / punkt pracy": [
        _spec("engine_config", "Engine-config YAML"),
        _spec("rpm", "Prędkość [obr/min]"),
        _spec("fuel", "Paliwo", choices=["diesel", "svo", "methanol"]),
        _spec("cyl", "Cylinder (full)"),
        _spec("step_deg", "Krok rozwiązania [deg]"),
        _spec("cycles", "Liczba cykli (full)"),
        _spec("p_amb_bar", "Ciśnienie otoczenia [bar]"),
        _spec("fmep_a_bar", "FMEP A [bar]"),
        _spec("fmep_b_bar_per_krpm", "FMEP B [bar/krpm]"),
        _spec("fmep_c_bar_per_bar", "FMEP C [bar/bar]"),
        _spec("fmep_bar", "FMEP stały [bar] (deprecated)"),
        _spec("target_brake_kw", "Moc docelowa [kW] (full, dobór dawki)"),
        _spec("fuel_mg_min", "Dobór dawki: min [mg]"),
        _spec("fuel_mg_max", "Dobór dawki: max [mg]"),
        _spec("target_tol_kw", "Dobór dawki: tolerancja [kW]"),
        _spec("n146_mv", "N146 napięcie [mV] (IQ z mapy)"),
        _spec("soi_main_sweep", "Sweep SOI [start:end:step] (full)"),
    ],
    "Dawka / wtrysk / VP37": [
        _spec("fuel_mg", "Dawka paliwa [mg/cyl/cykl]"),
        _spec("soi_main", "SOI main [deg] (puste = mapa)"),
        _spec("soi_pilot", "SOI pilot [deg] (puste = auto)"),
        _spec("soi_offset_deg", "Offset SOI [deg]"),
        _spec("pilot_lead_deg", "Pilot lead [deg]"),
        _spec("duration_model", "Model czasu wtrysku", choices=["auto", "fixed", "vp37"]),
        _spec("pilot_model", "Model pilota", choices=["fixed", "hydraulic"]),
        _spec("hrr_model", "Model HRR", choices=["auto", "wiebe", "vp37_main", "hydraulic_profile"]),
        _spec("soi_map", "Mapa SOI (CSV)"),
        _spec("n146_map", "Mapa N146 (CSV)"),
        _spec("vp37_cam", "Profil krzywki VP37 (CSV)"),
        _spec("vp37_iq_max", "VP37 IQ max [mg/stroke]"),
        _spec("vp37_start_frac", "VP37 start ułamek [0..1]"),
        _spec("nozzle_diameter_mm", "Dysza Ø otworu [mm]"),
        _spec("nozzle_holes", "Dysza: liczba otworów"),
        _spec("nozzle_cd", "Dysza: Cd"),
        _spec("nozzle_pilot_open_bar", "Otwarcie pilota [bar]"),
        _spec("nozzle_main_open_bar", "Otwarcie main [bar]"),
        _spec("nozzle_pilot_area_frac", "Ułamek pola pilota [0..1]"),
        _spec("plunger_diameter_mm", "Tłoczek VP37 Ø [mm]"),
        _spec("chamber_volume_mm3", "Komora VP37 [mm³]"),
        _spec("line_volume_mm3", "Objętość linii [mm³]"),
        _spec("back_pressure_bar", "Ciśnienie tłoczenia [bar]"),
        _spec("line_m", "Linia: długość [m] (opóźnienie)"),
        _spec("line_length_m", "Linia 1D: długość [m]"),
        _spec("line_diameter_mm", "Linia 1D: Ø [mm]"),
        _spec("line_segments", "Linia 1D: segmenty"),
        _spec("needle_mass_kg", "Iglica: masa [kg]"),
        _spec("needle_spring_k", "Iglica: sprężyna [N/m]"),
        _spec("needle_damping_c", "Iglica: tłumienie [Ns/m]"),
    ],
    "Zawory / manifolds": [
        _spec("ivo", "IVO [deg]"),
        _spec("ivc", "IVC [deg]"),
        _spec("evo", "EVO [deg]"),
        _spec("evc", "EVC [deg]"),
        _spec("valve_table", "Profil zaworów (Markdown)"),
        _spec("p_intake_bar", "P intake [bar abs]"),
        _spec("t_intake_k", "T intake [K]"),
        _spec("p_exhaust_bar", "P exhaust [bar abs]"),
        _spec("t_exhaust_k", "T exhaust [K]"),
    ],
    "Turbo / ECU / EGR": [
        _spec("turbo", "Sprzężenie turbo"),
        _spec("turbo_iters", "Iteracje turbo"),
        _spec("turbo_eta_t", "Sprawność turbiny ηt"),
        _spec("turbo_eta_c", "Sprawność sprężarki ηc"),
        _spec("turbo_eta_mech", "Sprawność wału ηmech"),
        _spec("turbo_pr_max", "Maksymalne PR"),
        _spec("turbo_relax", "Relaksacja P intake"),
        _spec("use_boost_map", "Użyj mapy boost"),
        _spec("ecu", "ECU", choices=["off", "report", "limit"]),
        _spec("smoke_map", "Mapa smoke limiter (CSV)"),
        _spec("egr_map", "Mapa EGR (CSV)"),
        _spec("boost_map", "Mapa boost (CSV)"),
    ],
    "Transient": [
        _spec("transient_end_s", "Czas symulacji [s]", modes="full,closed,transient"),
        _spec("transient_dt_s", "Krok czasu [s]", modes="full,closed,transient"),
        _spec("rpm_start", "RPM start", modes="full,closed,transient"),
        _spec("rpm_target", "RPM target", modes="full,closed,transient"),
        _spec("load_torque_nm", "Moment obciążenia [Nm]", modes="full,closed,transient"),
        _spec("load_step_s", "Load step [s]", modes="full,closed,transient"),
        _spec("inertia_kg_m2", "Bezwładność [kg·m²]", modes="full,closed,transient"),
        _spec("gov_kp", "Governor Kp [mg/rpm]", modes="full,closed,transient"),
        _spec("gov_ki", "Governor Ki [mg/rpm/s]", modes="full,closed,transient"),
        _spec("turbo_tau_s", "Turbo τ [s]", modes="full,closed,transient"),
        _spec("boost_target_bar", "Boost target [bar abs]", modes="full,closed,transient"),
    ],
    "Backendy / integrator": [
        _spec("thermo_backend", "Thermo backend", choices=["simple", "coolprop"], modes="full,closed,transient"),
        _spec("flow_backend", "Flow backend", choices=["simple", "fluids"], modes="full,closed,transient"),
        _spec("coolprop_fluid", "CoolProp fluid", modes="full,closed,transient"),
        _spec("strict_backends", "Strict backends", modes="full,closed,transient"),
        _spec("ignition_delay", "Model opóźnienia zapłonu", choices=["arrhenius", "fixed_deg"], modes="full,closed,transient"),
        _spec("ignition_delay_deg", "Opóźnienie zapłonu [deg]", modes="full,closed,transient"),
        _spec("integrator", "Integrator", choices=["rk4", "scipy"], modes="full,closed,transient"),
        _spec("scipy_method", "SciPy: metoda", modes="full,closed,transient"),
        _spec("scipy_rtol", "SciPy: rtol", modes="full,closed,transient"),
        _spec("scipy_atol", "SciPy: atol", modes="full,closed,transient"),
        _spec("scipy_max_step_deg", "SciPy: max step [deg]", modes="full,closed,transient"),
    ],
    "Wyjście": [
        _spec("out", "Katalog wyjściowy", modes="full,closed,transient"),
        _spec("no_plot", "Bez wykresów", modes="full,closed,transient"),
    ],
}

_SPEC_BY_NAME: dict[str, dict] = {}
for _specs in SETTING_SPECS.values():
    for _s in _specs:
        _SPEC_BY_NAME[_s["name"]] = _s

_DEFAULTS_CACHE: dict[str, object] | None = None


def SETTINGS_DEFAULTS() -> dict[str, object]:
    global _DEFAULTS_CACHE
    if _DEFAULTS_CACHE is None:
        _DEFAULTS_CACHE = {}
        for name, default in _CLI_DEFAULTS.items():
            if isinstance(default, Path):
                _DEFAULTS_CACHE[name] = str(default)
            else:
                _DEFAULTS_CACHE[name] = default
        _DEFAULTS_CACHE["mode"] = "full"
    return dict(_DEFAULTS_CACHE)


def parse_soi_sweep(value) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    parts = text.split(":")
    if len(parts) != 3:
        raise ValueError("Sweep SOI musi mieć format start:end:step")
    start, end, step = (_as_float(p.strip()) for p in parts)
    if step == 0.0:
        raise ValueError("Krok sweep nie może być 0")
    if step > 0.0 and start >= end:
        raise ValueError("Dla dodatniego kroku start musi być < end")
    if step < 0.0 and start <= end:
        raise ValueError("Dla ujemnego kroku start musi być > end")
    return text


def _optional_float(settings: dict, name: str, label: str) -> float | None:
    raw = settings.get(name)
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None
    return _as_float(text, f"{label} musi być liczbą")


def build_cli_args(settings: dict) -> list[str]:
    """Pure function: dict of GUI setting values -> CLI argument list.

    Mirrors the argparse defaults so that a value equal to the CLI default is
    simply omitted (keeps commands short); values differing from defaults are
    always passed explicitly with CLI casting applied.
    """
    settings = {str(k): v for k, v in settings.items()}
    mode = str(settings.get("mode") or "full")
    if mode not in {"full", "closed", "transient"}:
        raise ValueError(f"Nieznany tryb: {mode}")

    sweep = parse_soi_sweep(settings.get("soi_main_sweep"))
    n146_mv = _optional_float(settings, "n146_mv", "N146 mV")
    target_brake_kw = _optional_float(settings, "target_brake_kw", "Moc docelowa")

    if n146_mv is not None and sweep is not None:
        raise ValueError("N146 mV i sweep SOI wykluczają się wzajemnie")
    if target_brake_kw is not None and sweep is not None:
        raise ValueError("Moc docelowa i sweep SOI wykluczają się wzajemnie")
    if target_brake_kw is not None and mode != "full":
        raise ValueError("Moc docelowa działa tylko w trybie full")
    if sweep is not None and mode != "full":
        raise ValueError("Sweep SOI działa tylko w trybie full")
    if n146_mv is not None and mode != "full":
        raise ValueError("N146 mV działa tylko w trybie full")

    cmd: list[str] = ["--mode", mode]

    for name, action in _CLI_ACTIONS.items():
        if name in {"soi_main_sweep", "n146_mv", "target_brake_kw", "mode"}:
            continue
        default = _CLI_DEFAULTS[name]
        raw = settings.get(name)

        if isinstance(default, bool) or default is True or default is False:
            enabled = bool(raw)
            if enabled != bool(default):
                if name == "strict_backends":
                    cmd.append("--no-strict-backends" if not enabled else "--strict-backends")
                else:
                    cmd.append("--" + name.replace("_", "-"))
            continue

        text = "" if raw is None else str(raw).strip()
        if text == "":
            if default is None or isinstance(default, Path):
                continue
            raise ValueError(f"Pole '{name}' jest wymagane")
        if default is None:
            value = text
        elif isinstance(default, bool):
            continue
        elif isinstance(default, int):
            try:
                value = str(int(float(text)))
            except ValueError:
                raise ValueError(f"Nieprawidłowa wartość dla '{name}': '{text}'")
        elif isinstance(default, float):
            value = str(_as_float(text, f"Nieprawidłowa wartość dla '{name}'"))
        else:
            value = text

        if default is not None and value == str(_cli_default(name)):
            continue
        cmd += ["--" + name.replace("_", "-"), value]

    if target_brake_kw is not None:
        cmd += ["--target-brake-kw", repr(target_brake_kw)]
    if n146_mv is not None:
        cmd += ["--n146-mv", repr(n146_mv)]
    if sweep is not None:
        cmd += ["--soi-main-sweep", sweep]

    return cmd


def settings_to_json(settings: dict) -> str:
    return json.dumps({str(k): v for k, v in settings.items()}, indent=2, ensure_ascii=False, sort_keys=True)


def settings_from_json(text: str) -> dict:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Konfiguracja musi być obiektem JSON")
    result = SETTINGS_DEFAULTS()
    for name, value in data.items():
        if name in result:
            result[name] = value
    return result


def _tk_available() -> bool:
    try:
        import tkinter  # noqa: F401
    except Exception:
        return False
    try:
        import tkinter.ttk  # noqa: F401
    except Exception:
        return False
    return True


class VirtualTdiGui:
    PRESETS: dict[str, dict[str, object]] = {
        "Domyślny (pełny cykl)": {},
        "CHP 10 kW @1500": {
            "target_brake_kw": "10",
            "fuel_mg_min": "2",
            "fuel_mg_max": "40",
            "out": "out_chp",
        },
        "Zamknięty cykl": {"mode": "closed", "fuel_mg": "15"},
        "Transient 800\u21921500 pod obciążeniem": {
            "mode": "transient",
            "rpm": "1500",
            "rpm_start": "800",
            "rpm_target": "1500",
            "load_torque_nm": "60",
            "load_step_s": "3",
            "inertia_kg_m2": "0.35",
        },
    }

    def __init__(self, root=None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        self._ttk = ttk
        self.root = tk.Tk() if root is None else root
        self.root.title("Virtual TDI \u2014 symulator silnika 1.9 TDI")
        self.root.geometry("1180x820")

        self.settings: dict[str, object] = SETTINGS_DEFAULTS()
        self.entries: dict[str, object] = {}
        self.combos: dict[str, object] = {}
        self.check_vars: dict[str, object] = {}
        self.mode_widgets: dict[str, list] = {"full": [], "closed": [], "transient": []}
        self._row_cache: dict[str, list] = {}

        self.process = None
        self.output_queue = queue.Queue()
        self._running = False

        self._build_form()
        self._build_output()
        self._poll_output()

        self.apply_settings_to_widgets(self.settings)

    # ------------------------------------------------------------------ form

    def _build_form(self) -> None:
        tk, ttk = self._tk, self._ttk

        header = ttk.Frame(self.root, padding=(10, 8, 10, 0))
        header.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(header, text="Preset:").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar(value=next(iter(self.PRESETS.keys())))
        preset_combo = ttk.Combobox(
            header,
            textvariable=self.preset_var,
            values=list(self.PRESETS.keys()),
            state="readonly",
            width=26,
        )
        preset_combo.pack(side=tk.LEFT, padx=(6, 12))
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset)

        ttk.Button(header, text="Wczytaj konfiguracj\u0119\u2026", command=self.on_load_settings).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(header, text="Zapisz konfiguracj\u0119\u2026", command=self.on_save_settings).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(header, text="Przywr\u00f3\u0107 domy\u015blne", command=self.on_defaults).pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=8)

        for tab_name, specs in SETTING_SPECS.items():
            tab = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(tab, text=tab_name)
            canvas = tk.Canvas(tab, highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
            inner = ttk.Frame(canvas)
            inner.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")),
            )
            canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.bind(
                "<Configure>",
                lambda e, c=canvas, w=canvas_window: c.itemconfigure(w, width=e.width),
            )

            def on_mousewheel(event, c=canvas):
                try:
                    if event.num == 4 or event.delta > 0:
                        c.yview_scroll(-1, "units")
                    elif event.num == 5 or event.delta < 0:
                        c.yview_scroll(1, "units")
                except Exception:
                    pass

            canvas.bind_all("<MouseWheel>", lambda e, c=canvas: on_mousewheel(e, c))
            canvas.bind_all("<Button-4>", lambda e, c=canvas: on_mousewheel(e, c))
            canvas.bind_all("<Button-5>", lambda e, c=canvas: on_mousewheel(e, c))
            canvas.bind("<Enter>", lambda e, c=canvas: c.focus_set())
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            inner.grid_columnconfigure(1, weight=1)

            for row, spec in enumerate(specs):
                self._build_setting_row(inner, row, spec)

        mode_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.insert(0, mode_tab, text="Tryb pracy")
        mode_tab.grid_columnconfigure(1, weight=1)

        self.mode_var = tk.StringVar(value=str(self.settings.get("mode") or "full"))
        mode_combo = ttk.Combobox(
            mode_tab,
            textvariable=self.mode_var,
            values=["full", "closed", "transient"],
            state="readonly",
        )
        ttk.Label(mode_tab, text="Tryb symulacji").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        mode_combo.grid(row=0, column=1, sticky="ew", pady=2)
        self.combos["mode"] = mode_combo
        mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)

        ttk.Label(
            mode_tab,
            text=(
                "full \u2014 pe\u0142ny cykl 720\u00b0 (gazowymiana + spalanie),\n"
                "closed \u2014 zamkni\u0119ty cykl (bez gazowymiany),\n"
                "transient \u2014 symulacja nieustalona (MVEM, governor PI + turbo lag)."
            ),
            justify=tk.LEFT,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.notebook.select(0)

        body = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        body.pack(side=tk.TOP, fill=tk.X)
        runbar = ttk.Frame(body)
        runbar.pack(side=tk.TOP, fill=tk.X)
        runbar.grid_columnconfigure(0, weight=1)
        self.btn_run = ttk.Button(runbar, text="Uruchom symulacj\u0119", command=self.on_run)
        self.btn_run.grid(row=0, column=0, sticky="ew", ipady=4)
        self.btn_stop = ttk.Button(runbar, text="Stop", command=self.on_stop, state="disabled")
        self.btn_stop.grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=4)
        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))

    def _build_setting_row(self, parent, row: int, spec: dict) -> None:
        tk, ttk = self._tk, self._ttk
        name = spec["name"]
        modes = {m.strip() for m in spec["modes"].split(",") if m.strip()}
        label = ttk.Label(parent, text=spec["label"])
        label.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)

        default = _CLI_DEFAULTS[name]
        if isinstance(default, bool) or default is True or default is False:
            var = tk.BooleanVar(value=bool(default))
            widget = ttk.Checkbutton(parent, variable=var)
            widget.var = var
            self.check_vars[name] = var
        elif spec["choices"]:
            var = tk.StringVar(value=str(_cli_default(name)))
            widget = ttk.Combobox(parent, textvariable=var, values=list(spec["choices"]), state="readonly")
            widget.var = var
            self.combos[name] = widget
        else:
            widget = ttk.Entry(parent)
            if name in FILE_FIELDS:
                frame = ttk.Frame(parent)
                widget.grid(row=0, column=0, sticky="ew")
                browse = ttk.Button(frame, text="\u2026", width=3, command=lambda n=name: self._browse_file(n))
                browse.grid(row=0, column=1, padx=(4, 0))
                widget = frame
                inner_entry = frame.grid_slaves(row=0, column=0)[0]
                self.entries[name] = inner_entry
            else:
                self.entries[name] = widget

        widget.grid(row=row, column=1, sticky="ew", pady=2)

        for mode in ("full", "closed", "transient"):
            if mode in modes:
                self.mode_widgets[mode].append((label, widget))

    def _browse_file(self, name: str) -> None:
        from tkinter import filedialog

        extensions = _FILE_EXTENSIONS.get(name)
        filetypes = [extensions, ("Wszystkie pliki", "*.*")] if extensions else [("Wszystkie pliki", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            entry = self.entries.get(name)
            if entry is not None:
                entry.delete(0, "end")
                entry.insert(0, str(path))

    def _build_output(self) -> None:
        tk, ttk = self._tk, self._ttk
        out = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        out.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.text = tk.Text(out, wrap="word", height=14)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(out, command=self.text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text["yscrollcommand"] = scroll.set

    # ------------------------------------------------------------- settings IO

    def apply_settings_to_widgets(self, settings: dict) -> None:
        self.settings = dict(settings)
        mode = str(settings.get("mode") or "full")
        if "mode" in self.combos:
            self.mode_var.set(mode)

        for name, entry in self.entries.items():
            value = settings.get(name)
            text = "" if value is None else str(value)
            entry.delete(0, "end")
            entry.insert(0, text)

        for name, combo in self.combos.items():
            if name == "mode":
                continue
            combo.set(str(settings.get(name)))

        for name, var in self.check_vars.items():
            var.set(bool(settings.get(name)))

        self._apply_mode_visibility(mode)

    def _read_widgets_to_settings(self) -> dict:
        settings = SETTINGS_DEFAULTS()
        settings["mode"] = self.mode_var.get()
        for name, entry in self.entries.items():
            settings[name] = entry.get()
        for name, combo in self.combos.items():
            if name == "mode":
                continue
            settings[name] = combo.get()
        for name, var in self.check_vars.items():
            settings[name] = bool(var.get())
        self.settings = settings
        return settings

    def _apply_mode_visibility(self, mode: str) -> None:
        active = set(self.mode_widgets.get(mode, []))
        for mode_name, widgets in self.mode_widgets.items():
            state = "normal" if mode_name == mode else "disabled"
            for label, widget in widgets:
                try:
                    if isinstance(widget, self._ttk.Frame):
                        for child in widget.grid_slaves():
                            child.configure(state=state)
                    else:
                        widget.configure(state=state)
                    label.configure(foreground="#000000" if state == "normal" else "#a0a0a0")
                except Exception:
                    pass

    # ---------------------------------------------------------------- actions

    def _on_mode_change(self, event=None) -> None:
        self._apply_mode_visibility(self.mode_var.get())

    def _on_preset(self, event=None) -> None:
        name = self.preset_var.get()
        preset = self.PRESETS.get(name, {})
        settings = SETTINGS_DEFAULTS()
        settings.update(dict(preset))
        self.apply_settings_to_widgets(settings)

    def on_defaults(self) -> None:
        self.apply_settings_to_widgets(SETTINGS_DEFAULTS())
        self._append("Przywr\u00f3cono ustawienia domy\u015blne.\n")

    def on_load_settings(self) -> None:
        from tkinter import filedialog, messagebox

        path = filedialog.askopenfilename(
            filetypes=[("Pliki JSON", "*.json"), ("Wszystkie pliki", "*.*")]
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            settings = settings_from_json(data)
        except Exception as exc:
            messagebox.showerror("B\u0142\u0105d wczytywania", f"Nie uda\u0142o si\u0119 wczyta\u0107 konfiguracji:\n{exc}")
            return
        self.apply_settings_to_widgets(settings)
        self._append(f"Wczytano konfiguracj\u0119: {path}\n")

    def on_save_settings(self) -> None:
        from tkinter import filedialog, messagebox

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Pliki JSON", "*.json"), ("Wszystkie pliki", "*.*")],
        )
        if not path:
            return
        try:
            settings = self._read_widgets_to_settings()
            Path(path).write_text(settings_to_json(settings), encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("B\u0142\u0105d zapisu", f"Nie uda\u0142o si\u0119 zapisa\u0107 konfiguracji:\n{exc}")
            return
        self._append(f"Zapisano konfiguracj\u0119: {path}\n")

    def _build_cmd(self) -> list[str] | None:
        try:
            settings = self._read_widgets_to_settings()
            return [sys.executable, "-m", "virtual_tdi"] + build_cli_args(settings)
        except ValueError as exc:
            self._append(f"B\u0142\u0105d ustawie\u0144: {exc}\n")
            return None

    def on_run(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self._append("Symulacja ju\u017c trwa.\n")
            return
        cmd = self._build_cmd()
        if not cmd:
            return
        self._set_running(True)
        self._append("Uruchamiam:\n  " + " ".join(cmd) + "\n\n")
        threading.Thread(target=self._run_process, args=(cmd,), daemon=True).start()

    def _run_process(self, cmd: list[str]) -> None:
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self.output_queue.put(line)
            code = self.process.wait()
            self.output_queue.put(f"\nKod wyj\u015bcia: {code}\n")
        except Exception as exc:
            self.output_queue.put(f"Nie uda\u0142o si\u0119 uruchomi\u0107: {exc}\n")
        finally:
            self.output_queue.put("__GUI_DONE__")
            self.process = None

    def on_stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            self._append("Brak uruchomionej symulacji.\n")
            return
        self._append("Zatrzymuj\u0119 symulacj\u0119...\n")
        self.process.terminate()

    def on_clear(self) -> None:
        self.text.delete("1.0", "end")

    def _append(self, msg: str) -> None:
        self.text.insert("end", msg)
        self.text.see("end")

    def _poll_output(self) -> None:
        try:
            while True:
                msg = self.output_queue.get_nowait()
                if msg == "__GUI_DONE__":
                    self._set_running(False)
                    continue
                self._append(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_output)

    def _set_running(self, running: bool) -> None:
        if self._running == running:
            return
        self._running = running
        if running:
            self.progress.start(10)
            self.btn_run.configure(state="disabled")
            self.btn_stop.configure(state="normal")
        else:
            self.progress.stop()
            self.progress.configure(value=0)
            self.btn_run.configure(state="normal")
            self.btn_stop.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    try:
        import tkinter as tk
    except Exception as exc:
        print(f"GUI niedost\u0119pne: {exc}", file=sys.stderr)
        return 2
    app = VirtualTdiGui(root=tk.Tk())
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
