from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from .core import build_case, run_case, run_injection_debug
from .core import create_geometry_from_config, load_yaml_config
from .injection import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D
from .physics import geometry_at_theta
from .injection import N146VoltageMap2D
from .injection import SOIMap2D


APP_STYLE = """
QWidget {
    background-color: #0b0f14;
    color: #00ff41;
    font-family: Consolas, "Courier New", monospace;
}
QFrame#panel {
    background-color: rgba(0, 0, 0, 220);
    border: 2px solid #00ff41;
    border-radius: 8px;
}
QFrame#header {
    background-color: rgba(0, 0, 0, 230);
    border: 2px solid #00ff41;
    border-radius: 8px;
}
QLabel#headerTitle {
    font-size: 18px;
    font-weight: 700;
    color: #00ff41;
    letter-spacing: 2px;
}
QLabel#headerSub {
    color: #00e6ff;
    font-size: 10px;
}
QFrame#statusBar {
    background-color: rgba(0, 0, 0, 200);
    border: 1px solid #00ff41;
    border-radius: 6px;
}
QFrame#statusItem {
    background-color: rgba(0, 255, 65, 12);
    border-radius: 4px;
    padding: 4px;
}
QLabel#panelHeader {
    color: #00e6ff;
    font-weight: 700;
    border-bottom: 1px solid #00ff41;
    padding-bottom: 6px;
}
QLabel#valueLabel {
    color: #00e6ff;
    font-weight: 700;
}
QLabel#smallLabel {
    color: #00ff41;
    font-size: 9px;
}
QFrame#thermalCard {
    background-color: rgba(0, 0, 0, 180);
    border: 1px solid #00ff41;
    border-radius: 6px;
    padding: 6px;
}
QFrame#thermalCard[state="warning"] {
    border-color: #ff9800;
}
QFrame#thermalCard[state="critical"] {
    border-color: #f44336;
}
QLabel#thermalStatus[state="warning"] {
    color: #ff9800;
}
QLabel#thermalStatus[state="critical"] {
    color: #f44336;
}
QLabel#thermalStatus[state="ok"] {
    color: #00ff41;
}
QFrame#resultCard {
    background-color: rgba(0, 0, 0, 200);
    border: 2px solid #00ff41;
    border-radius: 8px;
    padding: 8px;
}
QLabel#resultValue {
    color: #00e6ff;
    font-size: 18px;
    font-weight: 700;
}
QLabel#resultLabel {
    color: #00ff41;
    font-size: 9px;
}
QPushButton {
    background-color: #00ff41;
    color: #000;
    border: none;
    border-radius: 6px;
    padding: 6px;
    font-weight: 700;
}
QPushButton:hover {
    background-color: #00cc33;
}
QPushButton#secondary {
    background-color: rgba(0, 255, 65, 30);
    color: #00ff41;
    border: 1px solid #00ff41;
}
QProgressBar {
    border: 1px solid #00ff41;
    border-radius: 6px;
    background-color: rgba(0, 0, 0, 120);
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #00ff41, stop:0.5 #ff9800, stop:1 #f44336);
    border-radius: 6px;
}
QTableWidget {
    background-color: rgba(0, 0, 0, 120);
    gridline-color: #00ff41;
}
QHeaderView::section {
    background-color: rgba(0, 0, 0, 200);
    color: #00e6ff;
    border: 1px solid #00ff41;
}
"""


@dataclass
class ThermalState:
    rpm: int = 2500
    iq: float = 35.0
    boost: int = 1800
    intake_temp_c: int = 40
    ambient_temp_c: int = 20
    fuel_type: str = "diesel"
    soi_offset: float = 0.0
    pilot_mg: float = 1.2
    pilot_model: str = "hydraulic"
    egt_pre_turbo_c: int = 650
    cylinder_peak_k: int = 1850
    piston_temp_c: int = 320
    valve_temp_c: int = 780
    manifold_temp_c: int = 680
    turbine_temp_c: int = 720
    lambda_afr: float = 1.45
    power_hp: int = 65
    torque_nm: int = 185


class ThermalEstimator:
    LHV_MAP = {
        "diesel": 42.5,
        "svo": 37.8,
        "biodiesel": 37.3,
        "wvo": 38.2,
    }

    @staticmethod
    def estimate(state: ThermalState) -> ThermalState:
        lhv = ThermalEstimator.LHV_MAP.get(state.fuel_type, 42.5)
        base_lambda = 1.3 + (state.boost - 1000) * 0.0004
        lam = max(1.15, base_lambda - state.iq * 0.008)

        stoich_afr = 14.5
        afr = lam * stoich_afr
        combustion_temp = 1100 + (state.iq / lam) * 18 - (afr - 14.5) * 25

        rpm_factor = 1 + (state.rpm - 2000) * 0.00008
        timing_factor = 1 + (state.soi_offset * 0.018)

        egt = combustion_temp * 0.48 * rpm_factor * timing_factor * (lhv / 42.5)
        cyl_peak = combustion_temp + 450 + state.iq * 6.5 - (lam - 1.2) * 150

        piston_heat_load = state.iq * state.rpm * 0.0012
        oil_cooling_eff = 0.65
        piston = 160 + piston_heat_load * 3.2 * (1 - oil_cooling_eff * 0.5)
        valve = egt * 1.18 + 40 + (state.iq * 1.2)
        manifold = (valve * 0.7 + egt * 0.3) + 20
        turbine = egt * 1.06 + (state.boost - 1000) * 0.015

        cycles_per_sec = max(0.1, state.rpm / 120.0)
        fuel_kg_s = state.iq * 1e-6 * cycles_per_sec * 4.0
        fuel_power_kw = fuel_kg_s * lhv * 1000.0
        load_factor = float(np.clip(state.iq / 55.0, 0.0, 1.0))
        boost_factor = float(np.clip((state.boost - 1000.0) / 1000.0, 0.0, 1.0))
        rpm_factor = float(np.clip(abs(state.rpm - 2000.0) / 2200.0, 0.0, 1.0))
        eff = 0.18 + 0.14 * load_factor + 0.04 * boost_factor + 0.06 * (1.0 - rpm_factor)
        eff = float(np.clip(eff, 0.16, 0.38))
        power_kw = fuel_power_kw * eff
        power_hp = power_kw * 1.341
        torque_nm = (power_kw * 9549) / max(1.0, state.rpm)

        return ThermalState(
            rpm=state.rpm,
            iq=state.iq,
            boost=state.boost,
            intake_temp_c=state.intake_temp_c,
            ambient_temp_c=state.ambient_temp_c,
            fuel_type=state.fuel_type,
            soi_offset=state.soi_offset,
            pilot_mg=state.pilot_mg,
            pilot_model=state.pilot_model,
            egt_pre_turbo_c=int(round(egt)),
            cylinder_peak_k=int(round(cyl_peak)),
            piston_temp_c=int(round(piston)),
            valve_temp_c=int(round(valve)),
            manifold_temp_c=int(round(manifold)),
            turbine_temp_c=int(round(turbine)),
            lambda_afr=float(lam),
            power_hp=int(round(power_hp)),
            torque_nm=int(round(torque_nm)),
        )


class StatusItem(QtWidgets.QFrame):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.setObjectName("statusItem")
        self.dot = QtWidgets.QLabel(" ")
        self.dot.setFixedSize(10, 10)
        self.dot.setStyleSheet("border-radius: 5px; background: #00ff41;")
        self.text = QtWidgets.QLabel(label)
        self.text.setObjectName("smallLabel")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(self.dot)
        layout.addWidget(self.text)
        layout.addStretch(1)

    def set_status(self, color: str, text: str) -> None:
        self.dot.setStyleSheet(f"border-radius: 5px; background: {color};")
        self.text.setText(text)


class ThermalCard(QtWidgets.QFrame):
    def __init__(self, label: str, unit: str) -> None:
        super().__init__()
        self.setObjectName("thermalCard")
        self.value = QtWidgets.QLabel("--")
        self.value.setObjectName("valueLabel")
        self.label = QtWidgets.QLabel(f"{label} ({unit})")
        self.label.setObjectName("smallLabel")
        self.status = QtWidgets.QLabel("OK")
        self.status.setObjectName("thermalStatus")
        self.status.setProperty("state", "ok")
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.value)
        layout.addWidget(self.label)
        layout.addWidget(self.status)

    def set_value(self, value: str) -> None:
        self.value.setText(value)

    def set_status(self, state: str, text: str) -> None:
        self.setProperty("state", state)
        self.status.setProperty("state", state)
        self.status.setText(text)
        self.style().polish(self)
        self.status.style().polish(self.status)


class ResultCard(QtWidgets.QFrame):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.setObjectName("resultCard")
        self.value = QtWidgets.QLabel("--")
        self.value.setObjectName("resultValue")
        self.label = QtWidgets.QLabel(label)
        self.label.setObjectName("resultLabel")
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.value)
        layout.addWidget(self.label)

    def set_value(self, value: str) -> None:
        self.value.setText(value)


class SimulationWorker(QtCore.QObject):
    finished = QtCore.Signal(object, object, dict)
    failed = QtCore.Signal(str)

    def __init__(self, engine_config_path: Path, overrides: dict[str, Any]) -> None:
        super().__init__()
        self.engine_config_path = engine_config_path
        self.overrides = overrides

    @QtCore.Slot()
    def run(self) -> None:
        try:
            engine_config = load_yaml_config(self.engine_config_path)
            case = build_case(engine_config, self.overrides)
            result = run_case(case)
            metrics = dict(getattr(result, "metrics", {}))
            self.finished.emit(result, case, metrics)
        except Exception as exc:
            self.failed.emit(str(exc))


class ThermalDashboard(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("1.9 TDI ALH - Thermal Analysis Lab")
        self.resize(1500, 900)

        pg.setConfigOptions(antialias=False, useOpenGL=True, background=None, foreground="#00ff41")

        self.state = ThermalState()
        self.saved_configs: list[dict[str, Any]] = []
        self.data_log: list[dict[str, Any]] = []
        self.sim_thread: QtCore.QThread | None = None
        self.sim_worker: SimulationWorker | None = None
        self.engine_config_path = Path("engine_reference_sources.yaml")
        self.last_result: object | None = None
        self.last_case: object | None = None
        self.last_metrics: dict[str, Any] | None = None
        self.map_x_axis: np.ndarray | None = None
        self.map_y_axis: np.ndarray | None = None
        self.map_grid: np.ndarray | None = None
        self._map_hover_proxy: object | None = None

        container = QtWidgets.QWidget()
        container.setStyleSheet(APP_STYLE)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_status_bar())
        layout.addLayout(self._build_main_grid())
        layout.addWidget(self._build_predictions_panel())

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        self.setCentralWidget(scroll)

        self._init_timers()
        self._update_all(quick=True)

    def _build_header(self) -> QtWidgets.QFrame:
        header = QtWidgets.QFrame()
        header.setObjectName("header")
        v = QtWidgets.QVBoxLayout(header)
        title = QtWidgets.QLabel("1.9 TDI ALH PRO - THERMAL LAB")
        title.setObjectName("headerTitle")
        subtitle = QtWidgets.QLabel("THERMAL ANALYSIS | SAFETY MARGINS | PREDICTIVE MAINT")
        subtitle.setObjectName("headerSub")
        v.addWidget(title, alignment=QtCore.Qt.AlignCenter)
        v.addWidget(subtitle, alignment=QtCore.Qt.AlignCenter)
        return header

    def _build_status_bar(self) -> QtWidgets.QFrame:
        bar = QtWidgets.QFrame()
        bar.setObjectName("statusBar")
        grid = QtWidgets.QGridLayout(bar)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        self.status_engine = StatusItem("ENGINE: NOMINAL")
        self.status_egt = StatusItem("EGT: SAFE")
        self.status_coolant = StatusItem("COOLANT: OK")
        self.status_oil = StatusItem("OIL: OK")
        self.status_turbo = StatusItem("TURBO: NOMINAL")
        self.status_piston = StatusItem("PISTON: SAFE")
        self.status_logging = StatusItem("LOGGING: ACTIVE")

        items = [
            self.status_engine,
            self.status_egt,
            self.status_coolant,
            self.status_oil,
            self.status_turbo,
            self.status_piston,
            self.status_logging,
        ]
        for i, item in enumerate(items):
            grid.addWidget(item, i // 4, i % 4)
        return bar

    def _build_main_grid(self) -> QtWidgets.QHBoxLayout:
        grid = QtWidgets.QHBoxLayout()
        grid.setSpacing(10)

        grid.addWidget(self._build_left_panel(), 1)
        grid.addWidget(self._build_center_panel(), 2)
        grid.addWidget(self._build_right_panel(), 1)
        return grid

    def _build_left_panel(self) -> QtWidgets.QFrame:
        panel = self._panel("ENGINE PARAMETERS")
        layout = panel.layout()

        self.rpm_slider, self.rpm_value = self._add_slider(layout, "RPM", 800, 5500, 2500, unit="RPM")
        self.iq_slider, self.iq_value = self._add_slider(layout, "IQ (mg/stroke)", 50, 750, 350, scale=0.1, unit="mg")
        self.boost_slider, self.boost_value = self._add_slider(layout, "Boost (mbar)", 1000, 2800, 1800, unit="mbar")

        self.intake_spin = self._add_spin(layout, "Intake Temp (C)", 20, 80, 40)
        self.ambient_spin = self._add_spin(layout, "Ambient Temp (C)", -20, 50, 20)

        fuel_box = QtWidgets.QComboBox()
        fuel_box.addItems(["diesel", "svo", "biodiesel", "wvo"])
        fuel_box.currentTextChanged.connect(self._on_inputs_changed)
        self.fuel_box = fuel_box
        layout.addWidget(self._labeled_widget("Fuel Type", fuel_box))

        self.soi_spin = self._add_double_spin(layout, "SOI Offset (deg BTDC)", -15.0, 15.0, 0.0, 0.5)
        self.pilot_model_box = QtWidgets.QComboBox()
        self.pilot_model_box.addItem("Hydraulic (VP37)", "hydraulic")
        self.pilot_model_box.addItem("Fixed pilot mg", "fixed_mg")
        self.pilot_model_box.currentIndexChanged.connect(self._on_pilot_model_changed)
        layout.addWidget(self._labeled_widget("Pilot model", self.pilot_model_box))
        self.pilot_spin = self._add_double_spin(layout, "Pilot Dose (mg/stroke)", 0.0, 5.0, 1.2, 0.1)
        self._on_pilot_model_changed()

        preset_grid = QtWidgets.QGridLayout()
        presets = [
            ("ECO", "eco"),
            ("STAGE 1", "stage1"),
            ("STAGE 2", "stage2"),
            ("STAGE 3", "stage3"),
            ("EXTREME", "extreme"),
            ("TOWING", "towing"),
        ]
        for i, (label, key) in enumerate(presets):
            btn = QtWidgets.QPushButton(label)
            btn.setObjectName("secondary")
            btn.clicked.connect(lambda _=False, k=key: self._apply_preset(k))
            preset_grid.addWidget(btn, i // 3, i % 3)
        layout.addWidget(self._section("Quick Presets", preset_grid))

        self.use_backend = QtWidgets.QCheckBox("Use physics backend (full cycle)")
        self.use_backend.setChecked(False)
        self.use_backend.stateChanged.connect(self._on_inputs_changed)
        layout.addWidget(self.use_backend)

        run_btn = QtWidgets.QPushButton("RUN THERMAL SIM")
        run_btn.clicked.connect(self._run_simulation)
        layout.addWidget(run_btn)

        layout.addStretch(1)
        return panel

    def _build_center_panel(self) -> QtWidgets.QFrame:
        panel = self._panel("DASHBOARD TABS")
        layout = panel.layout()

        self.main_tabs = QtWidgets.QTabWidget()
        self.main_tabs.addTab(self._build_simulation_tab(), "Simulation")
        self.main_tabs.addTab(self._build_maps_tab(), "ECU Maps")
        self.main_tabs.addTab(self._build_geometry_tab(), "Geometry")
        self.main_tabs.addTab(self._build_results_tab(), "Results")
        self.main_tabs.addTab(self._build_data_tab(), "Data Export")
        layout.addWidget(self.main_tabs)

        return panel

    def _build_simulation_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._build_thermal_tab(), "Thermal")
        self.tabs.addTab(self._build_pressure_tab(), "P-CA")
        self.tabs.addTab(self._build_pv_tab(), "PV")
        self.tabs.addTab(self._build_rohr_tab(), "ROHR + Injection")
        self.tabs.addTab(self._build_hydraulics_tab(), "Hydraulics")
        layout.addWidget(self.tabs)

        return widget

    def _build_thermal_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.last_update = QtWidgets.QLabel("Updated: --:--:--")
        self.last_update.setObjectName("smallLabel")
        layout.addWidget(self.last_update, alignment=QtCore.Qt.AlignRight)

        self.egt_gauge = QtWidgets.QProgressBar()
        self.egt_gauge.setRange(400, 900)
        self.egt_gauge.setValue(self.state.egt_pre_turbo_c)
        layout.addWidget(self.egt_gauge)

        self.thermal_cards = {
            "cylinder": ThermalCard("Peak Cyl", "K"),
            "egt": ThermalCard("EGT Pre-Turbo", "C"),
            "piston": ThermalCard("Piston Crown", "C"),
            "valve": ThermalCard("Exhaust Valve", "C"),
            "manifold": ThermalCard("Exh Manifold", "C"),
            "turbine": ThermalCard("Turbine Inlet", "C"),
        }
        grid = QtWidgets.QGridLayout()
        keys = list(self.thermal_cards.keys())
        for i, key in enumerate(keys):
            grid.addWidget(self.thermal_cards[key], i // 2, i % 2)
        layout.addLayout(grid)

        self.temp_plot = pg.PlotWidget()
        self.temp_plot.setBackground((0, 0, 0))
        self.temp_plot.showGrid(x=True, y=True, alpha=0.3)
        self.temp_plot.setLabel("left", "Temperature (C)")
        self.temp_plot.setLabel("bottom", "Exhaust path")
        self.temp_plot.setYRange(300, 1000)
        self.temp_line = self.temp_plot.plot(pen=pg.mkPen("#00e6ff", width=2))
        self.temp_points = pg.ScatterPlotItem(size=8, brush=pg.mkBrush("#00ff41"))
        self.temp_plot.addItem(self.temp_points)
        ticks = [(0, "Cylinder"), (1, "Valve"), (2, "Manifold"), (3, "Turbine"), (4, "Post")]
        self.temp_plot.getAxis("bottom").setTicks([ticks])
        layout.addWidget(self.temp_plot)

        self.warning_container = QtWidgets.QVBoxLayout()
        warning_box = QtWidgets.QFrame()
        warning_box.setObjectName("panel")
        warning_layout = QtWidgets.QVBoxLayout(warning_box)
        warning_layout.addWidget(QtWidgets.QLabel("Warnings", objectName="panelHeader"))
        warning_layout.addLayout(self.warning_container)
        layout.addWidget(warning_box)

        return widget

    def _build_pressure_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.pressure_plot = pg.PlotWidget()
        self.pressure_plot.setBackground((0, 0, 0))
        self.pressure_plot.showGrid(x=True, y=True, alpha=0.3)
        self.pressure_plot.setLabel("bottom", "Crank angle (deg)")
        self.pressure_plot.setLabel("left", "Pressure (bar)")
        self.pressure_plot.addLegend()
        self.pressure_cyl = self.pressure_plot.plot(pen=pg.mkPen("#00e6ff", width=2), name="p_cyl")
        self.pressure_intake = self.pressure_plot.plot(
            pen=pg.mkPen("#00ff41", width=1, style=QtCore.Qt.DashLine), name="p_intake"
        )
        self.pressure_exhaust = self.pressure_plot.plot(
            pen=pg.mkPen("#ff9800", width=1, style=QtCore.Qt.DashLine), name="p_exhaust"
        )
        self.pressure_line_tdc = pg.InfiniteLine(pos=0.0, angle=90, pen=pg.mkPen("#00ff41", style=QtCore.Qt.DotLine))
        self.pressure_line_soi = pg.InfiniteLine(pos=0.0, angle=90, pen=pg.mkPen("#ff9800", style=QtCore.Qt.DotLine))
        self.pressure_line_peak = pg.InfiniteLine(pos=0.0, angle=90, pen=pg.mkPen("#f44336", style=QtCore.Qt.DotLine))
        self.pressure_plot.addItem(self.pressure_line_tdc)
        self.pressure_plot.addItem(self.pressure_line_soi)
        self.pressure_plot.addItem(self.pressure_line_peak)
        layout.addWidget(self.pressure_plot)
        return widget

    def _build_pv_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.pv_info = QtWidgets.QLabel("IMEP: -- | Wi: -- J/cyl")
        self.pv_info.setObjectName("smallLabel")
        layout.addWidget(self.pv_info)

        self.pv_plot = pg.PlotWidget()
        self.pv_plot.setBackground((0, 0, 0))
        self.pv_plot.showGrid(x=True, y=True, alpha=0.3)
        self.pv_plot.setLabel("bottom", "Volume (cm^3)")
        self.pv_plot.setLabel("left", "Pressure (bar)")
        self.pv_plot.setLogMode(x=True, y=True)
        self.pv_curve = self.pv_plot.plot(pen=pg.mkPen("#00e6ff", width=2))
        layout.addWidget(self.pv_plot)
        return widget

    def _build_rohr_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.rohr_plot = pg.PlotWidget()
        self.rohr_plot.setBackground((0, 0, 0))
        self.rohr_plot.showGrid(x=True, y=True, alpha=0.3)
        self.rohr_plot.setLabel("bottom", "Crank angle (deg)")
        self.rohr_plot.setLabel("left", "ROHR (J/deg)")
        self.rohr_curve = self.rohr_plot.plot(pen=pg.mkPen("#00e6ff", width=2))
        layout.addWidget(self.rohr_plot)

        self.inj_plot = pg.PlotWidget()
        self.inj_plot.setBackground((0, 0, 0))
        self.inj_plot.showGrid(x=True, y=True, alpha=0.3)
        self.inj_plot.setLabel("bottom", "Crank angle (deg)")
        self.inj_plot.setLabel("left", "Injection (mg/deg)")
        self.inj_curve = self.inj_plot.plot(pen=pg.mkPen("#00ff41", width=2))
        layout.addWidget(self.inj_plot)

        self.inj_status = QtWidgets.QLabel("Injection profile: --")
        self.inj_status.setObjectName("smallLabel")
        layout.addWidget(self.inj_status)
        return widget

    def _build_hydraulics_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.hyd_status = QtWidgets.QLabel("Hydraulics: not available")
        self.hyd_status.setObjectName("smallLabel")
        layout.addWidget(self.hyd_status)

        self.hyd_pressure_plot = pg.PlotWidget()
        self.hyd_pressure_plot.setBackground((0, 0, 0))
        self.hyd_pressure_plot.showGrid(x=True, y=True, alpha=0.3)
        self.hyd_pressure_plot.setLabel("bottom", "Theta (deg)")
        self.hyd_pressure_plot.setLabel("left", "Line pressure (bar)")
        self.hyd_pressure_curve = self.hyd_pressure_plot.plot(pen=pg.mkPen("#00e6ff", width=2))
        layout.addWidget(self.hyd_pressure_plot)

        self.hyd_needle_plot = pg.PlotWidget()
        self.hyd_needle_plot.setBackground((0, 0, 0))
        self.hyd_needle_plot.showGrid(x=True, y=True, alpha=0.3)
        self.hyd_needle_plot.setLabel("bottom", "Theta (deg)")
        self.hyd_needle_plot.setLabel("left", "Needle lift (mm)")
        self.hyd_needle_curve = self.hyd_needle_plot.plot(pen=pg.mkPen("#00ff41", width=2))
        layout.addWidget(self.hyd_needle_plot)

        self.hyd_mdot_plot = pg.PlotWidget()
        self.hyd_mdot_plot.setBackground((0, 0, 0))
        self.hyd_mdot_plot.showGrid(x=True, y=True, alpha=0.3)
        self.hyd_mdot_plot.setLabel("bottom", "Theta (deg)")
        self.hyd_mdot_plot.setLabel("left", "Fuel rate (mg/s)")
        self.hyd_mdot_curve = self.hyd_mdot_plot.plot(pen=pg.mkPen("#ff9800", width=2))
        layout.addWidget(self.hyd_mdot_plot)

        return widget

    def _build_maps_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        controls = QtWidgets.QHBoxLayout()
        self.map_select = QtWidgets.QComboBox()
        self.map_select.addItem("SOI Map (Start of Injection)", "soi")
        self.map_select.addItem("N146 Voltage Map", "n146")
        self.map_select.addItem("Smoke Limiter Map", "smoke")
        self.map_select.addItem("EGR MAF Target Map", "egr")
        self.map_select.addItem("Boost Target Map", "boost")
        self.map_select.currentIndexChanged.connect(self._on_map_selected)
        controls.addWidget(QtWidgets.QLabel("Select Map:", objectName="smallLabel"))
        controls.addWidget(self.map_select)
        reload_btn = QtWidgets.QPushButton("Reload Map")
        reload_btn.setObjectName("secondary")
        reload_btn.clicked.connect(self._on_map_selected)
        controls.addWidget(reload_btn)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.map_info = QtWidgets.QLabel("Map: --")
        self.map_info.setObjectName("smallLabel")
        layout.addWidget(self.map_info)

        self.map_cursor_label = QtWidgets.QLabel("Cursor: --")
        self.map_cursor_label.setObjectName("smallLabel")
        layout.addWidget(self.map_cursor_label)

        self.map_plot = pg.PlotWidget()
        self.map_plot.setBackground((0, 0, 0))
        self.map_plot.showGrid(x=True, y=True, alpha=0.3)
        self.map_plot.setLabel("bottom", "Axis X")
        self.map_plot.setLabel("left", "RPM")
        self.map_image = pg.ImageItem()
        self.map_plot.addItem(self.map_image)
        vb = self.map_plot.getViewBox()
        vb.invertY(False)
        self.map_vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#00ff41", style=QtCore.Qt.DotLine))
        self.map_hline = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#00ff41", style=QtCore.Qt.DotLine))
        self.map_plot.addItem(self.map_vline)
        self.map_plot.addItem(self.map_hline)
        layout.addWidget(self.map_plot)

        export_row = QtWidgets.QHBoxLayout()
        export_csv = QtWidgets.QPushButton("Export Map CSV")
        export_csv.setObjectName("secondary")
        export_csv.clicked.connect(self._export_map_csv)
        export_png = QtWidgets.QPushButton("Export Map PNG")
        export_png.setObjectName("secondary")
        export_png.clicked.connect(self._export_map_png)
        export_row.addWidget(export_csv)
        export_row.addWidget(export_png)
        export_row.addStretch(1)
        layout.addLayout(export_row)

        self.map_table = QtWidgets.QTableWidget(0, 0)
        self.map_table.setCornerButtonEnabled(False)
        self.map_table.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.map_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.map_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.map_table)

        self._map_hover_proxy = pg.SignalProxy(self.map_plot.scene().sigMouseMoved, rateLimit=60, slot=self._on_map_hover)
        self._on_map_selected()
        return widget

    def _build_geometry_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        form = QtWidgets.QFormLayout()
        self.geom_labels: dict[str, QtWidgets.QLabel] = {}
        for key in [
            "bore_mm",
            "stroke_mm",
            "rod_length_mm",
            "offset_mm",
            "compression_ratio",
            "swept_cm3",
            "clearance_cm3",
            "intake_valve_mm",
            "exhaust_valve_mm",
            "max_lift_mm",
        ]:
            lbl = QtWidgets.QLabel("--")
            lbl.setObjectName("valueLabel")
            self.geom_labels[key] = lbl
        form.addRow("Bore (mm)", self.geom_labels["bore_mm"])
        form.addRow("Stroke (mm)", self.geom_labels["stroke_mm"])
        form.addRow("Rod Length (mm)", self.geom_labels["rod_length_mm"])
        form.addRow("Offset (mm)", self.geom_labels["offset_mm"])
        form.addRow("Compression Ratio", self.geom_labels["compression_ratio"])
        form.addRow("Swept Volume (cm3)", self.geom_labels["swept_cm3"])
        form.addRow("Clearance Volume (cm3)", self.geom_labels["clearance_cm3"])
        form.addRow("Intake Valve Dia (mm)", self.geom_labels["intake_valve_mm"])
        form.addRow("Exhaust Valve Dia (mm)", self.geom_labels["exhaust_valve_mm"])
        form.addRow("Max Lift (mm)", self.geom_labels["max_lift_mm"])
        layout.addLayout(form)

        self.geom_plot = pg.PlotWidget()
        self.geom_plot.setBackground((0, 0, 0))
        self.geom_plot.showGrid(x=True, y=True, alpha=0.3)
        self.geom_plot.setLabel("bottom", "Crank angle (deg)")
        self.geom_plot.setLabel("left", "Volume (cm3)")
        self.geom_curve = self.geom_plot.plot(pen=pg.mkPen("#00e6ff", width=2))
        layout.addWidget(self.geom_plot)

        self._refresh_geometry_tab()
        return widget

    def _build_results_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.results_info = QtWidgets.QLabel("No physics results yet.")
        self.results_info.setObjectName("smallLabel")
        layout.addWidget(self.results_info)

        self.results_table = QtWidgets.QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.results_table)
        return widget

    def _build_data_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.data_status = QtWidgets.QLabel("No physics results to export.")
        self.data_status.setObjectName("smallLabel")
        layout.addWidget(self.data_status)

        btn_csv = QtWidgets.QPushButton("Export Results CSV")
        btn_csv.setObjectName("secondary")
        btn_csv.clicked.connect(self._export_results_csv)
        btn_json = QtWidgets.QPushButton("Export Results JSON")
        btn_json.setObjectName("secondary")
        btn_json.clicked.connect(self._export_results_json)
        btn_cfg = QtWidgets.QPushButton("Export Config")
        btn_cfg.setObjectName("secondary")
        btn_cfg.clicked.connect(self._export_engine_config)

        layout.addWidget(btn_csv)
        layout.addWidget(btn_json)
        layout.addWidget(btn_cfg)
        layout.addStretch(1)
        return widget

    def _build_right_panel(self) -> QtWidgets.QFrame:
        panel = self._panel("THERMAL STRESS ANALYSIS")
        layout = panel.layout()

        res_grid = QtWidgets.QGridLayout()
        self.result_power = ResultCard("Power (HP)")
        self.result_torque = ResultCard("Torque (Nm)")
        self.result_lambda = ResultCard("Lambda")
        self.result_nox = ResultCard("NOx (ppm est)")
        res_grid.addWidget(self.result_power, 0, 0)
        res_grid.addWidget(self.result_torque, 0, 1)
        res_grid.addWidget(self.result_lambda, 1, 0)
        res_grid.addWidget(self.result_nox, 1, 1)
        layout.addLayout(res_grid)

        layout.addWidget(QtWidgets.QLabel("Component Safety Margins", objectName="panelHeader"))
        self.safety_table = QtWidgets.QTableWidget(4, 4)
        self.safety_table.setHorizontalHeaderLabels(["Component", "Current", "Limit", "Margin"])
        self.safety_table.verticalHeader().setVisible(False)
        self.safety_table.horizontalHeader().setStretchLastSection(True)
        self.safety_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.safety_table)

        tool_box = QtWidgets.QFrame()
        tool_layout = QtWidgets.QVBoxLayout(tool_box)
        tool_layout.addWidget(QtWidgets.QLabel("Advanced Tools", objectName="panelHeader"))
        btn_save = QtWidgets.QPushButton("SAVE CONFIG")
        btn_save.setObjectName("secondary")
        btn_save.clicked.connect(self._save_config)
        btn_compare = QtWidgets.QPushButton("COMPARE")
        btn_compare.setObjectName("secondary")
        btn_compare.clicked.connect(self._compare_configs)
        btn_predict = QtWidgets.QPushButton("PREDICT MAINT")
        btn_predict.setObjectName("secondary")
        btn_predict.clicked.connect(self._show_predictions)
        btn_export_log = QtWidgets.QPushButton("EXPORT LOG")
        btn_export_log.setObjectName("secondary")
        btn_export_log.clicked.connect(self._export_log)
        tool_layout.addWidget(btn_save)
        tool_layout.addWidget(btn_compare)
        tool_layout.addWidget(btn_predict)
        tool_layout.addWidget(btn_export_log)
        layout.addWidget(tool_box)

        btn_snapshot = QtWidgets.QPushButton("EXPORT SNAPSHOT")
        btn_snapshot.setObjectName("secondary")
        btn_snapshot.clicked.connect(self._export_snapshot)
        layout.addWidget(btn_snapshot)

        layout.addStretch(1)
        return panel

    def _build_predictions_panel(self) -> QtWidgets.QFrame:
        panel = QtWidgets.QFrame()
        panel.setObjectName("panel")
        panel.setVisible(False)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.addWidget(QtWidgets.QLabel("Predictive Maintenance Analysis", objectName="panelHeader"))
        self.predictions_list = QtWidgets.QVBoxLayout()
        layout.addLayout(self.predictions_list)
        self.predictions_panel = panel
        return panel

    def _panel(self, title: str) -> QtWidgets.QFrame:
        panel = QtWidgets.QFrame()
        panel.setObjectName("panel")
        layout = QtWidgets.QVBoxLayout(panel)
        header = QtWidgets.QLabel(title)
        header.setObjectName("panelHeader")
        layout.addWidget(header)
        return panel

    def _section(self, title: str, inner_layout: QtWidgets.QLayout) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("panel")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.addWidget(QtWidgets.QLabel(title, objectName="panelHeader"))
        layout.addLayout(inner_layout)
        return frame

    def _labeled_widget(self, label: str, widget: QtWidgets.QWidget) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        layout = QtWidgets.QVBoxLayout(frame)
        layout.addWidget(QtWidgets.QLabel(label, objectName="smallLabel"))
        layout.addWidget(widget)
        return frame

    def _add_slider(
        self,
        layout: QtWidgets.QVBoxLayout,
        label: str,
        min_v: int,
        max_v: int,
        value: int,
        *,
        scale: float = 1.0,
        unit: str = "",
    ) -> tuple[QtWidgets.QSlider, QtWidgets.QLabel]:
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(value)
        slider.valueChanged.connect(self._on_inputs_changed)
        value_label = QtWidgets.QLabel()
        value_label.setObjectName("valueLabel")
        frame = QtWidgets.QFrame()
        v = QtWidgets.QVBoxLayout(frame)
        v.addWidget(QtWidgets.QLabel(label, objectName="smallLabel"))
        v.addWidget(slider)
        v.addWidget(value_label)
        layout.addWidget(frame)
        self._update_slider_label(value_label, slider.value(), scale, unit)
        slider.valueChanged.connect(lambda val: self._update_slider_label(value_label, val, scale, unit))
        slider.setProperty("scale", scale)
        slider.setProperty("unit", unit)
        return slider, value_label

    def _update_slider_label(self, label: QtWidgets.QLabel, value: int, scale: float, unit: str) -> None:
        display = value * scale
        if abs(scale - 1.0) > 1e-6:
            label.setText(f"{display:.1f} {unit}".strip())
        else:
            label.setText(f"{int(display)} {unit}".strip())

    def _add_spin(self, layout: QtWidgets.QVBoxLayout, label: str, min_v: int, max_v: int, value: int) -> QtWidgets.QSpinBox:
        spin = QtWidgets.QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(value)
        spin.valueChanged.connect(self._on_inputs_changed)
        layout.addWidget(self._labeled_widget(label, spin))
        return spin

    def _add_double_spin(
        self,
        layout: QtWidgets.QVBoxLayout,
        label: str,
        min_v: float,
        max_v: float,
        value: float,
        step: float,
    ) -> QtWidgets.QDoubleSpinBox:
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(min_v, max_v)
        spin.setSingleStep(step)
        spin.setValue(value)
        spin.valueChanged.connect(self._on_inputs_changed)
        layout.addWidget(self._labeled_widget(label, spin))
        return spin

    def _on_inputs_changed(self) -> None:
        self._update_all(quick=True)

    def _apply_preset(self, preset: str) -> None:
        presets = {
            "eco": dict(rpm=1800, iq=25.0, boost=1400, soi=2.0, pilot=10),
            "stage1": dict(rpm=2500, iq=45.0, boost=1900, soi=0.0, pilot=1.2),
            "stage2": dict(rpm=2800, iq=55.0, boost=2200, soi=-1.0, pilot=1.3),
            "stage3": dict(rpm=3200, iq=65.0, boost=2400, soi=-2.0, pilot=1.4),
            "extreme": dict(rpm=3500, iq=75.0, boost=2600, soi=-3.0, pilot=1.5),
            "towing": dict(rpm=2200, iq=52.0, boost=2000, soi=1.0, pilot=1.3),
        }
        p = presets.get(preset)
        if not p:
            return
        self.rpm_slider.setValue(p["rpm"])
        self.iq_slider.setValue(int(p["iq"] * 10))
        self.boost_slider.setValue(p["boost"])
        self.soi_spin.setValue(p["soi"])
        self.pilot_spin.setValue(p["pilot"])

    def _update_all(self, *, quick: bool) -> None:
        state = self._read_inputs()
        estimated = ThermalEstimator.estimate(state)
        self.state = estimated

        if quick:
            self._update_ui_from_state(self.state)
            return

        self._update_ui_from_state(self.state)

    def _read_inputs(self) -> ThermalState:
        rpm = int(self.rpm_slider.value())
        iq = float(self.iq_slider.value()) * 0.1
        boost = int(self.boost_slider.value())
        intake = int(self.intake_spin.value())
        ambient = int(self.ambient_spin.value())
        fuel = str(self.fuel_box.currentText())
        soi = float(self.soi_spin.value())
        pilot = float(self.pilot_spin.value())
        pilot_model = str(self.pilot_model_box.currentData() or "hydraulic")
        return ThermalState(
            rpm=rpm,
            iq=iq,
            boost=boost,
            intake_temp_c=intake,
            ambient_temp_c=ambient,
            fuel_type=fuel,
            soi_offset=soi,
            pilot_mg=pilot,
            pilot_model=pilot_model,
        )

    def _update_ui_from_state(self, state: ThermalState) -> None:
        self.egt_gauge.setValue(int(state.egt_pre_turbo_c))
        self._update_last_time()

        self.thermal_cards["cylinder"].set_value(str(state.cylinder_peak_k))
        self.thermal_cards["egt"].set_value(str(state.egt_pre_turbo_c))
        self.thermal_cards["piston"].set_value(str(state.piston_temp_c))
        self.thermal_cards["valve"].set_value(str(state.valve_temp_c))
        self.thermal_cards["manifold"].set_value(str(state.manifold_temp_c))
        self.thermal_cards["turbine"].set_value(str(state.turbine_temp_c))

        self.result_power.set_value(str(state.power_hp))
        self.result_torque.set_value(str(state.torque_nm))

        lambda_val = state.lambda_afr
        nox_val = self._estimate_nox(state)
        if self.use_backend.isChecked() and self.last_metrics:
            lambda_val = float(self.last_metrics.get("lambda_est", lambda_val))
            nox_val = int(round(float(self.last_metrics.get("nox_ppm_est", nox_val))))

        self.result_lambda.set_value(f"{lambda_val:.2f}")
        self.result_nox.set_value(str(nox_val))

        self._update_statuses(state)
        self._update_safety_table(state)
        self._update_warnings(state)
        self._update_temp_path(state)

    def _update_statuses(self, state: ThermalState) -> None:
        egt = state.egt_pre_turbo_c
        piston = state.piston_temp_c
        valve = state.valve_temp_c
        turbo = state.turbine_temp_c

        if egt > 850:
            self.status_egt.set_status("#f44336", "EGT: DANGER")
            self.thermal_cards["egt"].set_status("critical", "SHUTDOWN")
        elif egt > 750:
            self.status_egt.set_status("#f44336", "EGT: CRITICAL")
            self.thermal_cards["egt"].set_status("critical", "CRITICAL")
        elif egt > 700:
            self.status_egt.set_status("#ff9800", "EGT: HIGH")
            self.thermal_cards["egt"].set_status("warning", "HIGH")
        elif egt > 650:
            self.status_egt.set_status("#ff9800", "EGT: ELEVATED")
            self.thermal_cards["egt"].set_status("ok", "ELEVATED")
        else:
            self.status_egt.set_status("#00ff41", "EGT: SAFE")
            self.thermal_cards["egt"].set_status("ok", "NOMINAL")

        if piston > 400:
            self.status_piston.set_status("#f44336", "PISTON: MELT RISK")
            self.thermal_cards["piston"].set_status("critical", "MELT")
        elif piston > 350:
            self.status_piston.set_status("#ff9800", "PISTON: HOT")
            self.thermal_cards["piston"].set_status("warning", "HOT")
        else:
            self.status_piston.set_status("#00ff41", "PISTON: SAFE")
            self.thermal_cards["piston"].set_status("ok", "OK")

        if valve > 850:
            self.thermal_cards["valve"].set_status("critical", "LIMIT")
        elif valve > 800:
            self.thermal_cards["valve"].set_status("warning", "HIGH")
        else:
            self.thermal_cards["valve"].set_status("ok", "OK")

        if turbo > 850:
            self.status_turbo.set_status("#f44336", "TURBO: CRITICAL")
        elif turbo > 750:
            self.status_turbo.set_status("#ff9800", "TURBO: ELEVATED")
        else:
            self.status_turbo.set_status("#00ff41", "TURBO: NOMINAL")

        self.status_engine.set_status("#00ff41", "ENGINE: NOMINAL")
        self.status_coolant.set_status("#00ff41", "COOLANT: OK")
        self.status_oil.set_status("#00ff41", "OIL: OK")
        self.status_logging.set_status("#00ff41", "LOGGING: ACTIVE")

    def _update_safety_table(self, state: ThermalState) -> None:
        rows = [
            ("Piston Crown", f"{state.piston_temp_c} C", "400 C", 400 - state.piston_temp_c),
            ("Exhaust Valve", f"{state.valve_temp_c} C", "850 C", 850 - state.valve_temp_c),
            ("EGT Pre-Turbo", f"{state.egt_pre_turbo_c} C", "750 C", 750 - state.egt_pre_turbo_c),
            ("Turbine Housing", f"{state.turbine_temp_c} C", "900 C", 900 - state.turbine_temp_c),
        ]
        self.safety_table.setRowCount(len(rows))
        for i, (comp, curr, lim, margin) in enumerate(rows):
            self.safety_table.setItem(i, 0, QtWidgets.QTableWidgetItem(comp))
            self.safety_table.setItem(i, 1, QtWidgets.QTableWidgetItem(curr))
            self.safety_table.setItem(i, 2, QtWidgets.QTableWidgetItem(lim))
            margin_text = f"{margin:+d} C"
            item = QtWidgets.QTableWidgetItem(margin_text)
            if margin < 0:
                item.setForeground(QtGui.QColor("#f44336"))
            else:
                item.setForeground(QtGui.QColor("#00ff41"))
            self.safety_table.setItem(i, 3, item)

    def _update_warnings(self, state: ThermalState) -> None:
        while self.warning_container.count():
            item = self.warning_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        warnings = []
        if state.egt_pre_turbo_c > 850:
            warnings.append(("CRITICAL", "EGT > 850C - SHUTDOWN REQUIRED"))
        if state.piston_temp_c > 400:
            warnings.append(("CRITICAL", "Piston temp exceeds limit"))
        if state.valve_temp_c > 850:
            warnings.append(("CRITICAL", "Valve temp exceeds limit"))
        if state.iq > 60:
            warnings.append(("ADVISORY", "High fuel quantity - monitor EGT"))
        if state.boost > 2400:
            warnings.append(("ADVISORY", "High boost - verify turbo safety"))

        if not warnings:
            label = QtWidgets.QLabel("No active warnings.")
            label.setObjectName("smallLabel")
            self.warning_container.addWidget(label)
            return

        for severity, msg in warnings:
            label = QtWidgets.QLabel(f"{severity}: {msg}")
            if severity == "CRITICAL":
                label.setStyleSheet("color: #f44336;")
            else:
                label.setStyleSheet("color: #ff9800;")
            self.warning_container.addWidget(label)

    def _update_temp_path(self, state: ThermalState) -> None:
        temps = [
            float(state.cylinder_peak_k - 273.15),
            float(state.valve_temp_c),
            float(state.manifold_temp_c),
            float(state.turbine_temp_c),
            float(state.egt_pre_turbo_c * 0.68),
        ]
        x = np.arange(len(temps))
        self.temp_line.setData(x, temps)
        self.temp_points.setData(x, temps, symbol="o")

    def _estimate_nox(self, state: ThermalState) -> int:
        peak_k = max(1400.0, float(state.cylinder_peak_k))
        egt_c = max(200.0, float(state.egt_pre_turbo_c))
        lambda_air = max(0.9, float(state.lambda_afr))

        temp_factor = np.clip((peak_k - 1500.0) / 400.0, 0.0, 1.6)
        egt_factor = np.clip((egt_c - 450.0) / 400.0, 0.0, 1.4)
        lambda_factor = np.clip((lambda_air - 1.0) / 0.6, 0.0, 1.2)

        nox = 50.0 + 1200.0 * (temp_factor ** 1.6) + 500.0 * (egt_factor ** 1.4)
        nox *= 0.7 + 0.6 * lambda_factor
        return int(np.clip(round(nox), 20, 3000))

    def _update_last_time(self) -> None:
        now = datetime.now()
        self.last_update.setText(f"Updated: {now:%H:%M:%S}")

    def _init_timers(self) -> None:
        self.log_timer = QtCore.QTimer(self)
        self.log_timer.setInterval(5000)
        self.log_timer.timeout.connect(self._log_data)
        self.log_timer.start()

    def _log_data(self) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "rpm": self.state.rpm,
            "iq": self.state.iq,
            "boost": self.state.boost,
            "egt": self.state.egt_pre_turbo_c,
            "piston_temp": self.state.piston_temp_c,
            "valve_temp": self.state.valve_temp_c,
            "power_hp": self.state.power_hp,
            "torque_nm": self.state.torque_nm,
            "lambda": self.state.lambda_afr,
        }
        self.data_log.append(entry)

    def _update_physics_plots(self, result: object, case: object, metrics: dict) -> None:
        theta = np.asarray(getattr(result, "theta_deg", []), dtype=float)
        pressure_pa = np.asarray(getattr(result, "pressure_pa", []), dtype=float)
        pressure_bar = pressure_pa / 1e5 if pressure_pa.size else np.array([])

        self.pressure_cyl.setData(theta, pressure_bar)
        p_intake = getattr(result, "p_intake_pa", None)
        p_exhaust = getattr(result, "p_exhaust_pa", None)
        if p_intake is not None:
            self.pressure_intake.setData(theta, np.asarray(p_intake) / 1e5)
        else:
            self.pressure_intake.setData([], [])
        if p_exhaust is not None:
            self.pressure_exhaust.setData(theta, np.asarray(p_exhaust) / 1e5)
        else:
            self.pressure_exhaust.setData([], [])

        soi = None
        if case is not None and getattr(case, "schedule", None) is not None:
            soi = float(getattr(case.schedule, "soi_main_deg", 0.0))
        self.pressure_line_tdc.setValue(0.0)
        self.pressure_line_soi.setValue(float(soi) if soi is not None else 0.0)
        if pressure_bar.size:
            peak_idx = int(np.argmax(pressure_bar))
            peak_theta = float(theta[peak_idx]) if theta.size else 0.0
            self.pressure_line_peak.setValue(peak_theta)

        volume_m3 = np.asarray(getattr(result, "volume_m3", []), dtype=float)
        volume_cm3 = volume_m3 * 1e6 if volume_m3.size else np.array([])
        if volume_cm3.size and pressure_bar.size:
            mask = (volume_cm3 > 0.0) & (pressure_bar > 0.0)
            self.pv_curve.setData(volume_cm3[mask], pressure_bar[mask])
        else:
            self.pv_curve.setData([], [])

        imep_bar = metrics.get("imep_bar")
        wi_text = "IMEP: -- | Wi: -- J/cyl"
        if imep_bar is not None and case is not None and getattr(case, "geom", None) is not None:
            wi_j = float(imep_bar) * 1e5 * float(case.geom.swept_volume_m3_per_cyl)
            wi_text = f"IMEP: {float(imep_bar):.2f} bar | Wi: {wi_j:.1f} J/cyl"
        self.pv_info.setText(wi_text)

        dq_comb = getattr(result, "dq_comb_j_per_deg", None)
        if dq_comb is not None:
            self.rohr_curve.setData(theta, np.asarray(dq_comb, dtype=float))
        else:
            self.rohr_curve.setData([], [])

        dm_main = getattr(result, "dm_fuel_main_mg_per_deg", None)
        if dm_main is not None and len(dm_main) > 0:
            self.inj_curve.setData(theta, np.asarray(dm_main, dtype=float))
            self.inj_status.setText("Injection profile: OK")
        else:
            self.inj_curve.setData([], [])
            self.inj_status.setText("Injection profile: not available")

        try:
            engine_config = load_yaml_config(self.engine_config_path)
            overrides = self._build_overrides()
            inj = run_injection_debug(engine_config, overrides)
            theta_h = np.asarray(inj["theta_deg"], dtype=float)
            self.hyd_pressure_curve.setData(theta_h, np.asarray(inj["line_pressure_pa"]) / 1e5)
            self.hyd_needle_curve.setData(theta_h, np.asarray(inj["needle_lift_m"]) * 1e3)
            self.hyd_mdot_curve.setData(theta_h, np.asarray(inj["mdot_fuel_kg_s"]) * 1e6)
            self.hyd_status.setText("Hydraulics: OK")
        except Exception as exc:
            self.hyd_pressure_curve.setData([], [])
            self.hyd_needle_curve.setData([], [])
            self.hyd_mdot_curve.setData([], [])
            self.hyd_status.setText(f"Hydraulics: unavailable ({exc})")

    @staticmethod
    def _resolve_map_path(pattern: str) -> Path | None:
        for p in Path(".").glob(pattern):
            return p
        return None

    def _on_map_selected(self) -> None:
        map_id = self.map_select.currentData()
        if map_id is None:
            return
        self._load_map(map_id)

    def _load_map(self, map_id: str) -> None:
        try:
            if map_id == "soi":
                path = self._resolve_map_path("*SOI*Table 1.csv")
                if path is None:
                    raise FileNotFoundError("SOI map not found")
                m = SOIMap2D.from_csv(path)
                x_axis = m.iq_axis_mg_per_str
                y_axis = m.rpm_axis
                grid = m.soi_deg_btdc_positive
                x_label = "IQ (mg/str)"
                value_label = "SOI (deg BTDC)"
            elif map_id == "n146":
                path = self._resolve_map_path("*N146*Table 1.csv")
                if path is None:
                    raise FileNotFoundError("N146 map not found")
                m = N146VoltageMap2D.from_csv(path)
                x_axis = m.iq_axis_mg_per_str
                y_axis = m.rpm_axis
                grid = m.voltage_mv
                x_label = "IQ (mg/str)"
                value_label = "Voltage (mV)"
            elif map_id == "smoke":
                path = self._resolve_map_path("SmokeLimiter*.csv")
                if path is None:
                    raise FileNotFoundError("Smoke limiter map not found")
                m = SmokeLimiterMap2D.from_csv(path)
                x_axis = m.maf_axis_mg_per_str
                y_axis = m.rpm_axis
                grid = m.iq_max_mg_per_str
                x_label = "MAF (mg/str)"
                value_label = "IQ max (mg/str)"
            elif map_id == "egr":
                path = self._resolve_map_path("Mapa_EGR*.csv")
                if path is None:
                    raise FileNotFoundError("EGR map not found")
                m = EGRMafTargetMap2D.from_csv(path)
                x_axis = m.iq_axis_mg_per_str
                y_axis = m.rpm_axis
                grid = m.maf_target_mg_per_str
                x_label = "IQ (mg/str)"
                value_label = "MAF target (mg/str)"
            elif map_id == "boost":
                path = self._resolve_map_path("Mapa_BOOST*.csv")
                if path is None:
                    raise FileNotFoundError("Boost map not found")
                m = BoostTargetMap2D.from_csv(path)
                x_axis = m.iq_axis_mg_per_str
                y_axis = m.rpm_axis
                grid = m.map_mbar_abs
                x_label = "IQ (mg/str)"
                value_label = "MAP target (mbar)"
            else:
                return
        except Exception as exc:
            self.map_info.setText(f"Map load failed: {exc}")
            self.map_image.setImage(np.zeros((1, 1)))
            self.map_table.setRowCount(0)
            return

        self.map_info.setText(f"{value_label} | {path}")
        self.map_x_axis = np.asarray(x_axis, dtype=float)
        self.map_y_axis = np.asarray(y_axis, dtype=float)
        self.map_grid = np.asarray(grid, dtype=float)
        self._update_map_view(x_axis, y_axis, grid, x_label)
        self._update_map_table(x_axis, y_axis, grid)

    def _update_map_view(self, x_axis: np.ndarray, y_axis: np.ndarray, grid: np.ndarray, x_label: str) -> None:
        grid_arr = np.asarray(grid, dtype=float)
        if grid_arr.size == 0:
            self.map_image.setImage(np.zeros((1, 1)))
            return
        self.map_image.setImage(grid_arr, autoLevels=True)
        x0 = float(x_axis[0])
        y0 = float(y_axis[0])
        width = float(x_axis[-1] - x_axis[0]) if len(x_axis) > 1 else 1.0
        height = float(y_axis[-1] - y_axis[0]) if len(y_axis) > 1 else 1.0
        self.map_image.setRect(QtCore.QRectF(x0, y0, width, height))
        self.map_plot.setLabel("bottom", x_label)
        self.map_plot.setLabel("left", "RPM")
        self.map_plot.setXRange(float(x_axis[0]), float(x_axis[-1]))
        self.map_plot.setYRange(float(y_axis[0]), float(y_axis[-1]))

    def _update_map_table(self, x_axis: np.ndarray, y_axis: np.ndarray, grid: np.ndarray) -> None:
        x_vals = np.asarray(x_axis, dtype=float)
        y_vals = np.asarray(y_axis, dtype=float)
        grid_arr = np.asarray(grid, dtype=float)
        self.map_table.setRowCount(len(y_vals))
        self.map_table.setColumnCount(len(x_vals))
        self.map_table.setHorizontalHeaderLabels([f"{x:.2f}" for x in x_vals])
        self.map_table.setVerticalHeaderLabels([f"{rpm:.0f}" for rpm in y_vals])
        for i, rpm in enumerate(y_vals):
            for j, x in enumerate(x_vals):
                value = grid_arr[i, j]
                self.map_table.setItem(i, j, QtWidgets.QTableWidgetItem(f"{value:.2f}"))
        self.map_table.resizeColumnsToContents()
        self.map_table.resizeRowsToContents()

    def _on_map_hover(self, event: object) -> None:
        if self.map_x_axis is None or self.map_y_axis is None or self.map_grid is None:
            return
        pos = event[0] if isinstance(event, (list, tuple)) else event
        if pos is None:
            return
        vb = self.map_plot.getViewBox()
        if not vb.sceneBoundingRect().contains(pos):
            return
        mouse = vb.mapSceneToView(pos)
        x_val = float(mouse.x())
        y_val = float(mouse.y())

        x_axis = self.map_x_axis
        y_axis = self.map_y_axis
        grid = self.map_grid
        if x_val < x_axis[0] or x_val > x_axis[-1] or y_val < y_axis[0] or y_val > y_axis[-1]:
            return

        xi = int(np.searchsorted(x_axis, x_val, side="right") - 1)
        yi = int(np.searchsorted(y_axis, y_val, side="right") - 1)
        xi = int(np.clip(xi, 0, len(x_axis) - 2))
        yi = int(np.clip(yi, 0, len(y_axis) - 2))

        x0 = float(x_axis[xi])
        x1 = float(x_axis[xi + 1])
        y0 = float(y_axis[yi])
        y1 = float(y_axis[yi + 1])
        q00 = float(grid[yi, xi])
        q10 = float(grid[yi, xi + 1])
        q01 = float(grid[yi + 1, xi])
        q11 = float(grid[yi + 1, xi + 1])
        tx = 0.0 if x1 == x0 else (x_val - x0) / (x1 - x0)
        ty = 0.0 if y1 == y0 else (y_val - y0) / (y1 - y0)
        a = q00 * (1.0 - tx) + q10 * tx
        b = q01 * (1.0 - tx) + q11 * tx
        value = a * (1.0 - ty) + b * ty

        self.map_vline.setValue(x_val)
        self.map_hline.setValue(y_val)
        self.map_cursor_label.setText(f"Cursor: RPM {y_val:.0f} | X {x_val:.2f} | Value {value:.2f}")

    def _export_map_csv(self) -> None:
        if self.map_x_axis is None or self.map_y_axis is None or self.map_grid is None:
            QtWidgets.QMessageBox.information(self, "Export", "No map data loaded.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Map CSV", "map.csv", "CSV Files (*.csv)")
        if not path:
            return
        x_axis = self.map_x_axis
        y_axis = self.map_y_axis
        grid = self.map_grid
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = ["RPM"] + [f"{x:.2f}" for x in x_axis]
            writer.writerow(header)
            for i, rpm in enumerate(y_axis):
                row = [f"{rpm:.0f}"] + [f"{v:.3f}" for v in grid[i, :]]
                writer.writerow(row)
        QtWidgets.QMessageBox.information(self, "Export", f"Saved map CSV to {path}")

    def _export_map_png(self) -> None:
        if self.map_x_axis is None or self.map_y_axis is None or self.map_grid is None:
            QtWidgets.QMessageBox.information(self, "Export", "No map data loaded.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Map PNG", "map.png", "PNG Files (*.png)")
        if not path:
            return
        pixmap = self.map_plot.grab()
        pixmap.save(path, "PNG")
        QtWidgets.QMessageBox.information(self, "Export", f"Saved map PNG to {path}")

    def _refresh_geometry_tab(self) -> None:
        try:
            cfg = load_yaml_config(self.engine_config_path)
            geom = create_geometry_from_config(cfg)
            valvetrain = cfg.get("parameters", {}).get("valvetrain", {})
        except Exception as exc:
            for lbl in self.geom_labels.values():
                lbl.setText("--")
            self.geom_curve.setData([], [])
            return

        cr = geom.compression_ratio
        if cr is None:
            cv = geom.clearance_volume_m3_per_cyl
            vs = geom.swept_volume_m3_per_cyl
            cr = (vs + cv) / max(1e-12, cv)

        self.geom_labels["bore_mm"].setText(f"{geom.bore_m * 1e3:.2f}")
        self.geom_labels["stroke_mm"].setText(f"{geom.stroke_m * 1e3:.2f}")
        self.geom_labels["rod_length_mm"].setText(f"{geom.rod_length_m * 1e3:.2f}")
        self.geom_labels["offset_mm"].setText(f"{geom.offset_m * 1e3:.2f}")
        self.geom_labels["compression_ratio"].setText(f"{float(cr):.2f}")
        self.geom_labels["swept_cm3"].setText(f"{geom.swept_volume_m3_per_cyl * 1e6:.2f}")
        self.geom_labels["clearance_cm3"].setText(f"{geom.clearance_volume_m3_per_cyl * 1e6:.2f}")
        self.geom_labels["intake_valve_mm"].setText(str(valvetrain.get("intake_valve_diameter", {}).get("value", "--")))
        self.geom_labels["exhaust_valve_mm"].setText(str(valvetrain.get("exhaust_valve_diameter", {}).get("value", "--")))
        self.geom_labels["max_lift_mm"].setText(str(valvetrain.get("max_valve_lift", {}).get("value", "--")))

        theta_deg = np.linspace(0.0, 360.0, 361)
        vols = []
        for deg in theta_deg:
            res = geometry_at_theta(geom, np.deg2rad(deg))
            vols.append(res.volume_m3 * 1e6)
        self.geom_curve.setData(theta_deg, np.asarray(vols))

    def _update_results_table(self) -> None:
        metrics = self.last_metrics or {}
        if not metrics:
            self.results_info.setText("No physics results yet.")
            self.results_table.setRowCount(0)
            return
        self.results_info.setText("Results from last physics run.")
        items = sorted(metrics.items())
        self.results_table.setRowCount(len(items))
        for i, (k, v) in enumerate(items):
            self.results_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(k)))
            if isinstance(v, (int, float, np.floating, np.integer)):
                text = f"{float(v):.4g}"
            else:
                text = str(v)
            self.results_table.setItem(i, 1, QtWidgets.QTableWidgetItem(text))

    def _update_data_status(self) -> None:
        if self.last_result is None:
            self.data_status.setText("No physics results to export.")
            return
        self.data_status.setText("Results available for export.")

    def _export_results_csv(self) -> None:
        if self.last_result is None:
            QtWidgets.QMessageBox.information(self, "Export", "No physics results to export.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Results CSV", "results.csv", "CSV Files (*.csv)")
        if not path:
            return
        result = self.last_result
        theta = np.asarray(getattr(result, "theta_deg", []), dtype=float)
        columns = {
            "theta_deg": theta,
            "pressure_bar": np.asarray(getattr(result, "pressure_pa", []), dtype=float) / 1e5,
            "temperature_k": np.asarray(getattr(result, "temperature_k", []), dtype=float),
            "volume_cm3": np.asarray(getattr(result, "volume_m3", []), dtype=float) * 1e6,
            "p_intake_bar": np.asarray(getattr(result, "p_intake_pa", []), dtype=float) / 1e5,
            "p_exhaust_bar": np.asarray(getattr(result, "p_exhaust_pa", []), dtype=float) / 1e5,
            "dq_comb_j_per_deg": np.asarray(getattr(result, "dq_comb_j_per_deg", []), dtype=float),
            "dm_fuel_main_mg_per_deg": np.asarray(getattr(result, "dm_fuel_main_mg_per_deg", []), dtype=float),
        }
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns.keys())
            for i in range(len(theta)):
                row = [col[i] if len(col) > i else "" for col in columns.values()]
                writer.writerow(row)
        QtWidgets.QMessageBox.information(self, "Export", f"Saved results to {path}")

    def _export_results_json(self) -> None:
        if self.last_result is None:
            QtWidgets.QMessageBox.information(self, "Export", "No physics results to export.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Results JSON", "results.json", "JSON Files (*.json)")
        if not path:
            return
        result = self.last_result
        payload = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.last_metrics or {},
            "state": asdict(self.state),
            "series": {
                "theta_deg": np.asarray(getattr(result, "theta_deg", []), dtype=float).tolist(),
                "pressure_bar": (np.asarray(getattr(result, "pressure_pa", []), dtype=float) / 1e5).tolist(),
                "temperature_k": np.asarray(getattr(result, "temperature_k", []), dtype=float).tolist(),
                "volume_cm3": (np.asarray(getattr(result, "volume_m3", []), dtype=float) * 1e6).tolist(),
            },
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QtWidgets.QMessageBox.information(self, "Export", f"Saved results to {path}")

    def _export_engine_config(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Engine Config",
            "engine_reference_sources.yaml",
            "YAML Files (*.yaml *.yml)",
        )
        if not path:
            return
        src = Path(self.engine_config_path)
        if not src.exists():
            QtWidgets.QMessageBox.warning(self, "Export", "Engine config not found.")
            return
        Path(path).write_text(src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        QtWidgets.QMessageBox.information(self, "Export", f"Saved config to {path}")

    def _run_simulation(self) -> None:
        if not self.use_backend.isChecked():
            self._update_all(quick=True)
            return
        if self.sim_thread is not None:
            return
        overrides = self._build_overrides()
        self.sim_thread = QtCore.QThread()
        self.sim_worker = SimulationWorker(self.engine_config_path, overrides)
        self.sim_worker.moveToThread(self.sim_thread)
        self.sim_thread.started.connect(self.sim_worker.run)
        self.sim_worker.finished.connect(self._on_sim_finished)
        self.sim_worker.failed.connect(self._on_sim_failed)
        self.sim_worker.finished.connect(self._cleanup_thread)
        self.sim_worker.failed.connect(self._cleanup_thread)
        self.sim_thread.start()

    def _build_overrides(self) -> dict[str, Any]:
        state = self._read_inputs()
        overrides = {
            "mode": "full",
            "rpm": float(state.rpm),
            "fuel_mg": float(state.iq),
            "boost_mbar_abs": float(state.boost),
            "t_intake_k": float(state.intake_temp_c) + 273.15,
            "fuel": state.fuel_type,
            "soi_offset_deg": float(state.soi_offset),
        }
        if state.pilot_model == "fixed_mg":
            overrides["pilot_model"] = "fixed"
            overrides["pilot_mg"] = float(state.pilot_mg)
        else:
            overrides["pilot_model"] = "hydraulic"
        return overrides

    def _on_pilot_model_changed(self) -> None:
        mode = str(self.pilot_model_box.currentData() or "hydraulic")
        self.pilot_spin.setEnabled(mode == "fixed_mg")

    def _on_sim_finished(self, result: object, case: object, metrics: dict) -> None:
        state = self._read_inputs()
        estimated = ThermalEstimator.estimate(state)
        try:
            peak_k = float(np.max(result.temperature_k))
            egt_c = float(np.max(result.t_exhaust_k) - 273.15)
            estimated.cylinder_peak_k = int(round(peak_k))
            estimated.egt_pre_turbo_c = int(round(egt_c))
        except Exception:
            pass
        if "brake_power_kw_est" in metrics:
            estimated.power_hp = int(round(float(metrics["brake_power_kw_est"]) * 1.341))
        if "brake_torque_nm_est" in metrics:
            estimated.torque_nm = int(round(float(metrics["brake_torque_nm_est"])))

        self.state = estimated
        self.last_result = result
        self.last_case = case
        self.last_metrics = metrics
        self._update_ui_from_state(self.state)
        self._update_physics_plots(result, case, metrics)
        self._update_results_table()
        self._update_data_status()

    def _on_sim_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, "Simulation failed", message)

    def _cleanup_thread(self) -> None:
        if self.sim_thread is None:
            return
        self.sim_thread.quit()
        self.sim_thread.wait()
        self.sim_thread = None
        self.sim_worker = None

    def _save_config(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(self, "Save configuration", "Name:")
        if not ok or not name:
            return
        self.saved_configs.append({"name": name, "timestamp": datetime.now().isoformat(), "params": asdict(self.state)})
        QtWidgets.QMessageBox.information(self, "Saved", f"Configuration saved: {name}")

    def _compare_configs(self) -> None:
        if len(self.saved_configs) < 2:
            QtWidgets.QMessageBox.information(self, "Compare", "Save at least 2 configurations.")
            return
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Configuration Comparison")
        layout = QtWidgets.QVBoxLayout(dialog)
        table = QtWidgets.QTableWidget()
        params = ["rpm", "iq", "boost", "egt_pre_turbo_c", "piston_temp_c", "valve_temp_c", "power_hp", "torque_nm", "lambda_afr"]
        labels = ["RPM", "IQ", "Boost", "EGT", "Piston", "Valve", "Power", "Torque", "Lambda"]
        table.setRowCount(len(params))
        table.setColumnCount(len(self.saved_configs) + 1)
        headers = ["Parameter"] + [c["name"][:15] for c in self.saved_configs]
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        for i, (p, label) in enumerate(zip(params, labels)):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(label))
            for j, cfg in enumerate(self.saved_configs, start=1):
                val = cfg["params"].get(p, "")
                if isinstance(val, float):
                    text = f"{val:.2f}"
                else:
                    text = str(val)
                table.setItem(i, j, QtWidgets.QTableWidgetItem(text))
        layout.addWidget(table)
        dialog.resize(700, 400)
        dialog.exec()

    def _export_log(self) -> None:
        if not self.data_log:
            QtWidgets.QMessageBox.information(self, "Export", "No log data collected yet.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Log", "thermal_log.csv", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.data_log[0].keys()))
            writer.writeheader()
            writer.writerows(self.data_log)
        QtWidgets.QMessageBox.information(self, "Export", f"Saved log to {path}")

    def _export_snapshot(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Snapshot", "thermal_snapshot.json", "JSON Files (*.json)")
        if not path:
            return
        payload = {
            "timestamp": datetime.now().isoformat(),
            "state": asdict(self.state),
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QtWidgets.QMessageBox.information(self, "Export", f"Saved snapshot to {path}")

    def _show_predictions(self) -> None:
        while self.predictions_list.count():
            item = self.predictions_list.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        predictions = self._predict_maintenance(self.state)
        for pred in predictions:
            label = QtWidgets.QLabel(
                f"{pred['title']}\n{pred['message']}\nInspection: {pred['interval']} | Cost: {pred['cost']}"
            )
            label.setWordWrap(True)
            label.setStyleSheet("color: #00e6ff; padding: 6px;")
            self.predictions_list.addWidget(label)
        self.predictions_panel.setVisible(True)

    def _predict_maintenance(self, state: ThermalState) -> list[dict[str, str]]:
        preds = []
        if state.egt_pre_turbo_c > 780:
            preds.append(
                {
                    "title": "Turbo thermal stress",
                    "message": "High EGT suggests turbine heat fatigue risk.",
                    "interval": "Inspect in 20h",
                    "cost": "$120",
                }
            )
        if state.piston_temp_c > 360:
            preds.append(
                {
                    "title": "Piston temperature elevated",
                    "message": "Consider oil cooling inspection and ring wear check.",
                    "interval": "Inspect in 50h",
                    "cost": "$220",
                }
            )
        if state.valve_temp_c > 820:
            preds.append(
                {
                    "title": "Exhaust valve stress",
                    "message": "Valve seat inspection recommended.",
                    "interval": "Inspect in 30h",
                    "cost": "$180",
                }
            )
        if not preds:
            preds.append(
                {
                    "title": "No critical alerts",
                    "message": "Thermal profile within safe margins.",
                    "interval": "Routine 100h",
                    "cost": "$0",
                }
            )
        return preds


def pyside_main() -> int:
    app = QtWidgets.QApplication([])
    app.setStyleSheet(APP_STYLE)
    win = ThermalDashboard()
    win.show()
    return app.exec()


from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

try:
    from . import core as app_api
    from .core import create_geometry_from_config
    from .engine_model import Fuel
except ImportError:  # pragma: no cover
    # Allows running via: `streamlit run virtual_tdi/gui.py`
    from virtual_tdi import core as app_api
    from virtual_tdi.core import create_geometry_from_config
    from virtual_tdi.engine_model import Fuel


def _import_streamlit():
    try:
        import streamlit as st  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "Streamlit is not installed. Install it (e.g. `pip install streamlit`) and run:\n"
            "  streamlit run virtual_tdi/gui.py"
        ) from exc
    return st


def _plotly_figures(result) -> dict[str, Any]:
    import plotly.graph_objects as go

    theta = np.asarray(result.theta_deg)
    p_bar = np.asarray(result.pressure_pa) / 1e5
    t_k = np.asarray(result.temperature_k)
    v = np.asarray(result.volume_m3)
    dq = np.asarray(result.dq_comb_j_per_deg)
    dm = np.asarray(result.dm_fuel_main_mg_per_deg)

    figs: dict[str, Any] = {}

    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(x=theta, y=p_bar, name="P_cyl [bar]"))
    fig_p.update_layout(xaxis_title="Crank angle [deg]", yaxis_title="Pressure [bar]", height=360, margin=dict(l=10, r=10, t=30, b=10))
    figs["p_theta"] = fig_p

    fig_pv = go.Figure()
    fig_pv.add_trace(go.Scatter(x=v, y=np.asarray(result.pressure_pa), name="PV", mode="lines"))
    fig_pv.update_layout(
        xaxis_title="Volume [m3]",
        yaxis_title="Pressure [Pa]",
        xaxis_type="log",
        yaxis_type="log",
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    figs["pv"] = fig_pv

    fig_heat = go.Figure()
    fig_heat.add_trace(go.Scatter(x=theta, y=dq, name="dQ_comb/dθ [J/deg]"))
    fig_heat.add_trace(go.Scatter(x=theta, y=dm, name="dm_fuel_main [mg/deg]", yaxis="y2"))
    fig_heat.update_layout(
        xaxis_title="Crank angle [deg]",
        yaxis_title="dQ [J/deg]",
        yaxis2=dict(title="dm [mg/deg]", overlaying="y", side="right"),
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    figs["heat"] = fig_heat

    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(x=theta, y=t_k, name="T_cyl [K]"))
    fig_t.update_layout(xaxis_title="Crank angle [deg]", yaxis_title="Temperature [K]", height=360, margin=dict(l=10, r=10, t=30, b=10))
    figs["t_theta"] = fig_t

    return figs


def _get_value(cfg: dict[str, Any], *keys: str, default=None):
    cur: Any = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    if isinstance(cur, dict) and "value" in cur:
        return cur["value"]
    return cur


def _set_value(cfg: dict[str, Any], value: Any, *keys: str) -> None:
    cur: Any = cfg
    for k in keys[:-1]:
        cur = cur[k]
    leaf = cur[keys[-1]]
    if isinstance(leaf, dict) and "value" in leaf:
        leaf["value"] = value
    else:
        cur[keys[-1]] = value


def _write_rows_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def render() -> None:  # pragma: no cover (UI)
    st = _import_streamlit()

    st.set_page_config(page_title="Virtual TDI - Engineering Dashboard", layout="wide")
    st.title("Virtual TDI - Engineering Dashboard (MVP)")

    if "engine_config_path" not in st.session_state:
        st.session_state.engine_config_path = "engine_reference_sources.yaml"
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
        st.session_state.last_metrics = None

    col_l, col_c, col_r = st.columns([0.32, 0.46, 0.22], gap="large")

    with col_l:
        st.subheader("Input / Config")

        engine_cfg_path = st.text_input("Engine config YAML", st.session_state.engine_config_path)
        st.session_state.engine_config_path = engine_cfg_path

        tabs = st.tabs(["Single", "Config (YAML)", "Sweep"])

        with tabs[0]:
            mode = st.selectbox("Mode", ["full", "closed"], index=0)
            rpm = st.number_input("RPM", min_value=500.0, max_value=6000.0, value=1500.0, step=50.0)

            st.markdown("### Fuel")
            fuel = st.selectbox(
                "Fuel type",
                [
                    "diesel",
                    "svo",
                    "biodiesel",
                    "margarine",
                    "lard",
                    "wvo",
                    "heating_oil",
                    "used_engine_oil",
                    "transformer_oil",
                    "methanol",
                    "custom",
                ],
                index=0,
            )
            fuel_mg = st.number_input("Fuel mg (per cyl per cycle)", min_value=0.0, max_value=120.0, value=20.0, step=0.5)
            fuel_temp_c = st.number_input("Fuel temp [°C] (density corr only)", min_value=-20.0, max_value=150.0, value=15.0, step=1.0)

            custom_density = custom_bulk = custom_lhv = custom_afr = None
            if fuel == "custom":
                custom_density = st.number_input("Custom density ρ [kg/m3]", min_value=600.0, max_value=1200.0, value=900.0, step=5.0)
                custom_bulk = st.number_input("Custom bulk modulus K [bar]", min_value=5000.0, max_value=30000.0, value=18000.0, step=250.0)
                custom_lhv = st.number_input("Custom LHV [MJ/kg]", min_value=10.0, max_value=60.0, value=42.0, step=0.5)
                custom_afr = st.number_input("Custom stoich AFR [-]", min_value=4.0, max_value=20.0, value=14.5, step=0.1)

            st.markdown("### Boundary conditions")
            p_intake_bar = st.number_input("p_intake [bar abs]", min_value=0.7, max_value=3.5, value=1.0, step=0.05)
            t_intake_k = st.number_input("t_intake [K]", min_value=200.0, max_value=400.0, value=300.0, step=5.0)
            p_exhaust_bar = st.number_input("p_exhaust [bar abs]", min_value=0.8, max_value=4.0, value=1.15, step=0.05)
            t_exhaust_k = st.number_input("t_exhaust [K]", min_value=300.0, max_value=1300.0, value=800.0, step=10.0)

            st.markdown("### Numerics")
            step_deg = st.number_input("Step [deg]", min_value=0.02, max_value=5.0, value=0.1, step=0.05)
            integrator = st.selectbox("Integrator", ["rk4", "scipy"], index=0)
            thermo_backend = st.selectbox("Thermo backend", ["simple", "coolprop"], index=0)
            flow_backend = st.selectbox("Flow backend", ["simple", "fluids"], index=0)

            st.markdown("### Thermal BC (walls)")
            wall_head_k = st.number_input("Wall head [K]", min_value=250.0, max_value=800.0, value=500.0, step=10.0)
            wall_piston_k = st.number_input("Wall piston [K]", min_value=250.0, max_value=900.0, value=550.0, step=10.0)
            wall_liner_k = st.number_input("Wall liner [K]", min_value=250.0, max_value=700.0, value=450.0, step=10.0)

            st.markdown("### Combustion")
            hrr_model = st.selectbox("HRR model", ["auto", "wiebe", "vp37_main", "hydraulic_profile"], index=0)
            ignition_delay = st.selectbox("Ignition delay", ["arrhenius", "fixed_deg"], index=0)
            ignition_delay_deg = st.number_input("Fixed ignition delay [deg]", min_value=0.0, max_value=60.0, value=5.0, step=0.5)

            # Quick fuel physics preview (ρ/K/LHV)
            try:
                fuel_obj = Fuel.from_name(
                    fuel,
                    density_kgm3=custom_density,
                    bulk_modulus_bar=custom_bulk,
                    lhv_mjkg=custom_lhv,
                    stoich_air_fuel=custom_afr,
                )
                fuel_obj = fuel_obj.with_density_correction(float(fuel_temp_c))
                c_ms = float((fuel_obj.bulk_modulus_pa / max(1e-9, fuel_obj.density_kg_per_m3)) ** 0.5)
                e_cycle_j = (float(fuel_mg) * 1e-6) * float(fuel_obj.lhv_j_per_kg)
                st.caption(f"ρ={fuel_obj.density_kg_per_m3:.1f} kg/m3, K={fuel_obj.bulk_modulus_pa/1e5:.0f} bar, LHV={fuel_obj.lhv_j_per_kg/1e6:.1f} MJ/kg")
                st.caption(f"c≈sqrt(K/ρ)={c_ms:.0f} m/s; energy/cycle≈{e_cycle_j:.0f} J per cyl")
            except Exception as exc:
                st.warning(f"Fuel config invalid: {exc}")

            run = st.button("RUN_SINGLE", type="primary", use_container_width=True)
            reset = st.button("RESET", use_container_width=True)
            if reset:
                st.session_state.last_result = None
                st.session_state.last_metrics = None

            if run:
                try:
                    engine_cfg = app_api.load_engine_config(engine_cfg_path)
                except Exception as exc:
                    st.error(f"Failed to load engine config: {exc}")
                    return

                overrides = {
                    "mode": mode,
                    "rpm": rpm,
                    "fuel": fuel,
                    "fuel_mg": fuel_mg,
                    "fuel_temp_c": fuel_temp_c,
                    "p_intake_bar": p_intake_bar,
                    "t_intake_k": t_intake_k,
                    "p_exhaust_bar": p_exhaust_bar,
                    "t_exhaust_k": t_exhaust_k,
                    "step_deg": step_deg,
                    "integrator": integrator,
                    "thermo_backend": thermo_backend,
                    "flow_backend": flow_backend,
                    "hrr_model": hrr_model,
                    "ignition_delay": ignition_delay,
                    "ignition_delay_deg": ignition_delay_deg,
                    "wall_head_k": wall_head_k,
                    "wall_piston_k": wall_piston_k,
                    "wall_liner_k": wall_liner_k,
                    "strict_backends": False,
                    "ecu": "off",
                }
                if fuel == "custom":
                    overrides.update(
                        {
                            "fuel_density_kgm3": custom_density,
                            "fuel_bulk_modulus_bar": custom_bulk,
                            "fuel_lhv_mjkg": custom_lhv,
                            "fuel_stoich_afr": custom_afr,
                        }
                    )

                with st.spinner("Running simulation..."):
                    try:
                        case = app_api.build_case(engine_cfg, overrides)
                        result = app_api.run_case(case)
                    except Exception as exc:
                        st.error(f"Simulation failed: {exc}")
                        return

                st.session_state.last_result = result
                st.session_state.last_metrics = dict(getattr(result, "metrics", {}))
                if hrr_model == "hydraulic_profile":
                    try:
                        st.session_state.last_inj = app_api.run_injection_debug(engine_cfg, overrides)
                    except Exception:
                        st.session_state.last_inj = None
                else:
                    st.session_state.last_inj = None

        with tabs[1]:
            st.markdown("### Edit engine_reference_sources.yaml (selected fields)")
            try:
                engine_cfg = app_api.load_engine_config(engine_cfg_path)
            except Exception as exc:
                st.error(f"Failed to load engine config: {exc}")
                engine_cfg = None

            if engine_cfg is not None:
                crank = engine_cfg["parameters"]["cranktrain"]
                ch = engine_cfg["parameters"]["combustion_chamber"]

                bore = st.number_input("Bore [mm]", min_value=70.0, max_value=90.0, value=float(crank["bore"]["value"]), step=0.1)
                stroke = st.number_input("Stroke [mm]", min_value=80.0, max_value=110.0, value=float(crank["stroke"]["value"]), step=0.1)
                rod = st.number_input("Rod length [mm]", min_value=130.0, max_value=170.0, value=float(crank["rod_length"]["value"]), step=0.1)
                offset = st.number_input("Cylinder offset [mm]", min_value=-2.0, max_value=2.0, value=float(crank["cylinder_offset"]["value"]), step=0.1)

                bowl = st.number_input("Bowl volume [cm3]", min_value=0.0, max_value=60.0, value=float(ch["bowl_volume"]["value"]), step=0.05)
                head_recess = st.number_input("Head recess [cm3]", min_value=0.0, max_value=10.0, value=float(ch["head_recess_volume"]["value"]), step=0.05)
                gasket = st.number_input("Gasket thickness [mm]", min_value=0.0, max_value=3.0, value=float(ch["gasket_thickness"]["value"]), step=0.01)
                protrusion = st.number_input("Piston protrusion [mm]", min_value=0.0, max_value=2.0, value=float(ch["piston_protrusion"]["value"]), step=0.01)

                if st.button("Apply to in-memory config", use_container_width=True):
                    _set_value(engine_cfg, float(bore), "parameters", "cranktrain", "bore")
                    _set_value(engine_cfg, float(stroke), "parameters", "cranktrain", "stroke")
                    _set_value(engine_cfg, float(rod), "parameters", "cranktrain", "rod_length")
                    _set_value(engine_cfg, float(offset), "parameters", "cranktrain", "cylinder_offset")
                    _set_value(engine_cfg, float(bowl), "parameters", "combustion_chamber", "bowl_volume")
                    _set_value(engine_cfg, float(head_recess), "parameters", "combustion_chamber", "head_recess_volume")
                    _set_value(engine_cfg, float(gasket), "parameters", "combustion_chamber", "gasket_thickness")
                    _set_value(engine_cfg, float(protrusion), "parameters", "combustion_chamber", "piston_protrusion")
                    st.session_state._engine_cfg_inmem = engine_cfg
                    st.success("Updated in-memory config.")

                inmem = st.session_state.get("_engine_cfg_inmem", None) or engine_cfg
                geom = create_geometry_from_config(inmem)
                vs = geom.swept_volume_m3_per_cyl * 1e6
                vc = geom.clearance_volume_m3_per_cyl * 1e6
                cr = (vs + vc) / max(1e-9, vc)
                st.caption(f"Derived: Vs={vs:.2f} cm3, Vc={vc:.2f} cm3, CR={cr:.3f}")

                save = st.button("BTN_SAVE (overwrite YAML)", type="primary", use_container_width=True)
                reload_cfg = st.button("BTN_LOAD (reload from disk)", use_container_width=True)
                if reload_cfg:
                    st.session_state.pop("_engine_cfg_inmem", None)
                    st.info("Reloaded (next render reads from disk).")
                if save:
                    app_api.save_engine_config(inmem, Path(engine_cfg_path))
                    st.success("Saved YAML.")

        with tabs[2]:
            st.markdown("### Sweep RPM x IQ (batch)")
            rpm_start = st.number_input("RPM start", value=1000.0, step=50.0)
            rpm_stop = st.number_input("RPM stop", value=4500.0, step=50.0)
            rpm_step = st.number_input("RPM step", value=250.0, step=50.0)
            iq_start = st.number_input("IQ start [mg]", value=5.0, step=1.0)
            iq_stop = st.number_input("IQ stop [mg]", value=50.0, step=1.0)
            iq_step = st.number_input("IQ step [mg]", value=5.0, step=1.0)
            out_csv = st.text_input("Output CSV", "data/sweep_rpm_iq.csv")
            run_sweep = st.button("BTN_RUN_SWEEP (RPM x IQ)", use_container_width=True)

            st.markdown("### Sweep SOI main")
            soi_start = st.number_input("SOI start [deg]", value=-14.0, step=1.0)
            soi_stop = st.number_input("SOI stop [deg]", value=-2.0, step=1.0)
            soi_step = st.number_input("SOI step [deg]", value=1.0, step=0.5)
            out_soi_csv = st.text_input("Output SOI sweep CSV", "data/sweep_soi.csv")
            run_soi = st.button("BTN_RUN_SWEEP (SOI)", use_container_width=True)

            if run_sweep or run_soi:
                try:
                    engine_cfg = app_api.load_engine_config(engine_cfg_path)
                except Exception as exc:
                    st.error(f"Failed to load engine config: {exc}")
                    return

            if run_sweep:
                if rpm_step <= 0 or iq_step <= 0:
                    st.error("Steps must be > 0.")
                else:
                    rpm_vals = np.arange(rpm_start, rpm_stop + rpm_step * 0.5, rpm_step, dtype=float)
                    iq_vals = np.arange(iq_start, iq_stop + iq_step * 0.5, iq_step, dtype=float)
                    with st.spinner("Running sweep..."):
                        rows = app_api.run_sweep(
                            app_api.SweepConfig(
                                engine_config=engine_cfg,
                                mode="full",
                                rpm_values=rpm_vals,
                                iq_values_mg=iq_vals,
                                overrides={
                                    "fuel": fuel,
                                    "fuel_temp_c": fuel_temp_c,
                                    "step_deg": step_deg,
                                    "integrator": integrator,
                                    "thermo_backend": thermo_backend,
                                    "flow_backend": flow_backend,
                                    "hrr_model": hrr_model,
                                    "ignition_delay": ignition_delay,
                                    "ignition_delay_deg": ignition_delay_deg,
                                    "p_intake_bar": p_intake_bar,
                                    "t_intake_k": t_intake_k,
                                    "p_exhaust_bar": p_exhaust_bar,
                                    "t_exhaust_k": t_exhaust_k,
                                    "wall_head_k": wall_head_k,
                                    "wall_piston_k": wall_piston_k,
                                    "wall_liner_k": wall_liner_k,
                                },
                            )
                        )
                    _write_rows_csv(Path(out_csv), rows)
                    st.success(f"Wrote {out_csv} ({len(rows)} rows)")

            if run_soi:
                if soi_step == 0:
                    st.error("SOI step must be non-zero.")
                else:
                    soi_vals = np.arange(soi_start, soi_stop + soi_step * 0.5, soi_step, dtype=float)
                    rows: list[dict[str, Any]] = []
                    with st.spinner("Running SOI sweep..."):
                        for soi in soi_vals:
                            case = app_api.build_case(
                                engine_cfg,
                                {
                                    "mode": "full",
                                    "rpm": rpm,
                                    "fuel": fuel,
                                    "fuel_mg": fuel_mg,
                                    "fuel_temp_c": fuel_temp_c,
                                    "soi_main": float(soi),
                                    "p_intake_bar": p_intake_bar,
                                    "t_intake_k": t_intake_k,
                                    "p_exhaust_bar": p_exhaust_bar,
                                    "t_exhaust_k": t_exhaust_k,
                                    "step_deg": step_deg,
                                    "integrator": integrator,
                                    "thermo_backend": thermo_backend,
                                    "flow_backend": flow_backend,
                                    "hrr_model": hrr_model,
                                    "ignition_delay": ignition_delay,
                                    "ignition_delay_deg": ignition_delay_deg,
                                    "wall_head_k": wall_head_k,
                                    "wall_piston_k": wall_piston_k,
                                    "wall_liner_k": wall_liner_k,
                                },
                            )
                            res = app_api.run_case(case)
                            metrics = dict(getattr(res, "metrics", {}))
                            row = {"rpm": float(rpm), "fuel_mg": float(fuel_mg), "soi_main_deg": float(soi)}
                            row.update({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
                            rows.append(row)
                    _write_rows_csv(Path(out_soi_csv), rows)
                    st.success(f"Wrote {out_soi_csv} ({len(rows)} rows)")

    with col_r:
        st.subheader("Controls / KPI")
        metrics = st.session_state.last_metrics or {}
        if metrics:
            for k in [
                "brake_power_kw_est",
                "brake_torque_nm_est",
                "bsfc_g_per_kwh_est",
                "peak_pressure_bar",
                "imep_bar",
                "soi_main_deg_model",
                "ign_delay_main_deg",
            ]:
                if k in metrics:
                    st.metric(k, f"{metrics[k]:.3f}" if isinstance(metrics[k], (int, float)) else str(metrics[k]))
            if "imep_bar" in metrics and isinstance(metrics["imep_bar"], (int, float)) and float(metrics["imep_bar"]) < 0.0:
                st.error("IMEP < 0: możliwy problem z zapłonem / opóźnieniem zapłonu / SOI.")
        else:
            st.info("Run a case to see metrics.")

        if metrics:
            with st.expander("All metrics"):
                st.json(metrics)

    with col_c:
        st.subheader("Visuals")
        result = st.session_state.last_result
        if result is None:
            st.info("Run a case to see plots.")
        else:
            figs = _plotly_figures(result)
            tabs = st.tabs(["P-θ", "PV", "Heat/Injection", "T-θ", "Hydraulics"])
            with tabs[0]:
                st.plotly_chart(figs["p_theta"], use_container_width=True)
            with tabs[1]:
                st.plotly_chart(figs["pv"], use_container_width=True)
            with tabs[2]:
                st.plotly_chart(figs["heat"], use_container_width=True)
            with tabs[3]:
                st.plotly_chart(figs["t_theta"], use_container_width=True)
            with tabs[4]:
                inj = st.session_state.get("last_inj", None)
                if inj is None:
                    st.info("Select HRR model = hydraulic_profile and run to see injection hydraulics.")
                else:
                    import plotly.graph_objects as go

                    theta = np.asarray(inj["theta_deg"])
                    lift_mm = np.asarray(inj["needle_lift_m"]) * 1e3
                    p_bar = np.asarray(inj["line_pressure_pa"]) / 1e5
                    mdot = np.asarray(inj["mdot_fuel_kg_s"])

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=theta, y=lift_mm, name="Needle lift [mm]"))
                    fig.add_trace(go.Scatter(x=theta, y=p_bar, name="Line pressure [bar]", yaxis="y2"))
                    fig.add_trace(go.Scatter(x=theta, y=mdot, name="m_dot [kg/s]", yaxis="y3"))
                    fig.update_layout(
                        xaxis_title="Crank angle [deg] (approx)",
                        yaxis=dict(title="Lift [mm]"),
                        yaxis2=dict(title="Pressure [bar]", overlaying="y", side="right"),
                        yaxis3=dict(title="m_dot [kg/s]", anchor="free", overlaying="y", side="right", position=1.0),
                        height=420,
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with st.expander("Case config (debug)"):
                st.json(asdict(app_api.build_case(app_api.load_engine_config(st.session_state.engine_config_path), {"mode": mode, "rpm": rpm, "fuel": fuel, "fuel_mg": fuel_mg, "step_deg": step_deg}).models))


if __name__ == "__main__":  # pragma: no cover
    render()


import sys
from pathlib import Path


def streamlit_main(argv: list[str] | None = None) -> int:  # pragma: no cover
    try:
        from streamlit.web import cli as stcli  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "Streamlit is not installed. Install it (e.g. `pip install streamlit`) and run:\n"
            "  streamlit run virtual_tdi/gui.py"
        ) from exc

    script = Path(__file__)
    args = argv or []
    sys.argv = ["streamlit", "run", str(script), *args]
    return int(stcli.main() or 0)




def main() -> int:
    return pyside_main()
