from __future__ import annotations

import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk


class VirtualTdiGui:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Virtual TDI GUI")
        self.root.geometry("900x640")

        self.process: subprocess.Popen[str] | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()
        self._running = False

        self._build_form()
        self._build_output()
        self._poll_output()

    def _build_form(self) -> None:
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(side=tk.TOP, fill=tk.X)

        self.var_mode = tk.StringVar(value="full")
        self.var_rpm = tk.StringVar(value="1500")
        self.var_fuel = tk.StringVar(value="diesel")
        self.var_fuel_mg = tk.StringVar(value="20")
        self.var_cycles = tk.StringVar(value="5")
        self.var_step_deg = tk.StringVar(value="0.1")
        self.var_out = tk.StringVar(value="out")
        self.var_ecu = tk.StringVar(value="off")
        self.var_use_boost = tk.BooleanVar(value=False)
        self.var_turbo = tk.BooleanVar(value=False)
        self.var_flow_backend = tk.StringVar(value="simple")
        self.var_thermo_backend = tk.StringVar(value="simple")
        self.var_ignition = tk.StringVar(value="arrhenius")
        self.var_ign_delay = tk.StringVar(value="5.0")
        self.var_no_plot = tk.BooleanVar(value=True)
        self.var_strict = tk.BooleanVar(value=False)

        row = 0
        row = self._row(frm, row, "Mode", ttk.Combobox(frm, textvariable=self.var_mode, values=["full", "closed"], state="readonly"))
        row = self._row(frm, row, "RPM", ttk.Entry(frm, textvariable=self.var_rpm))
        row = self._row(frm, row, "Fuel", ttk.Combobox(frm, textvariable=self.var_fuel, values=["diesel", "svo", "methanol"], state="readonly"))
        row = self._row(frm, row, "Fuel mg", ttk.Entry(frm, textvariable=self.var_fuel_mg))
        row = self._row(frm, row, "Cycles", ttk.Entry(frm, textvariable=self.var_cycles))
        row = self._row(frm, row, "Step deg", ttk.Entry(frm, textvariable=self.var_step_deg))
        row = self._row(frm, row, "Out dir", ttk.Entry(frm, textvariable=self.var_out))
        row = self._row(frm, row, "ECU", ttk.Combobox(frm, textvariable=self.var_ecu, values=["off", "report", "limit"], state="readonly"))
        row = self._row(frm, row, "Flow backend", ttk.Combobox(frm, textvariable=self.var_flow_backend, values=["simple", "fluids"], state="readonly"))
        row = self._row(frm, row, "Thermo backend", ttk.Combobox(frm, textvariable=self.var_thermo_backend, values=["simple", "coolprop"], state="readonly"))
        row = self._row(frm, row, "Ignition", ttk.Combobox(frm, textvariable=self.var_ignition, values=["arrhenius", "fixed_deg"], state="readonly"))
        row = self._row(frm, row, "Fixed delay deg", ttk.Entry(frm, textvariable=self.var_ign_delay))

        opts = ttk.Frame(frm)
        opts.grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Checkbutton(opts, text="Use boost map", variable=self.var_use_boost).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(opts, text="Turbo", variable=self.var_turbo).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(opts, text="No plot", variable=self.var_no_plot).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(opts, text="Strict backends", variable=self.var_strict).pack(side=tk.LEFT)

        btns = ttk.Frame(frm)
        btns.grid(row=row + 1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.btn_run = ttk.Button(btns, text="Run", command=self.on_run)
        self.btn_run.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_stop = ttk.Button(btns, text="Stop", command=self.on_stop, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Clear output", command=self.on_clear).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(frm, mode="indeterminate")
        self.progress.grid(row=row + 2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _build_output(self) -> None:
        out = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        out.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.text = tk.Text(out, wrap="word", height=24)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(out, command=self.text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text["yscrollcommand"] = scroll.set

    def _row(self, parent: ttk.Frame, row: int, label: str, widget: ttk.Widget) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        widget.grid(row=row, column=1, sticky="ew", pady=2)
        parent.grid_columnconfigure(1, weight=1)
        return row + 1

    def _append(self, msg: str) -> None:
        self.text.insert(tk.END, msg)
        self.text.see(tk.END)

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

    def _build_cmd(self) -> list[str] | None:
        try:
            rpm = float(self.var_rpm.get())
            fuel_mg = float(self.var_fuel_mg.get())
            cycles = int(float(self.var_cycles.get()))
            step_deg = float(self.var_step_deg.get())
            ign_delay = float(self.var_ign_delay.get())
        except ValueError:
            self._append("Invalid numeric input.\n")
            return None
        if step_deg <= 0.0:
            self._append("Step deg must be > 0.\n")
            return None

        mode = self.var_mode.get()
        if mode not in {"full", "closed"}:
            self._append("Invalid mode.\n")
            return None

        flow_backend = self.var_flow_backend.get()
        if flow_backend == "fluids" and not self._fluids_backend_available():
            self._append("fluids backend missing mass-flow functions; falling back to simple.\n")
            flow_backend = "simple"

        cmd = [sys.executable, "-m", "virtual_tdi", "--mode", mode]
        cmd += ["--rpm", f"{rpm}"]
        cmd += ["--fuel", self.var_fuel.get()]
        cmd += ["--fuel-mg", f"{fuel_mg}"]
        cmd += ["--step-deg", f"{step_deg}"]
        cmd += ["--ecu", self.var_ecu.get()]
        cmd += ["--flow-backend", flow_backend]
        cmd += ["--thermo-backend", self.var_thermo_backend.get()]
        cmd += ["--ignition-delay", self.var_ignition.get()]
        if self.var_ignition.get() == "fixed_deg":
            cmd += ["--ignition-delay-deg", f"{ign_delay}"]
        if mode == "full":
            cmd += ["--cycles", f"{max(1, cycles)}"]
        if self.var_use_boost.get():
            cmd += ["--use-boost-map"]
        if self.var_turbo.get():
            cmd += ["--turbo"]
        if self.var_no_plot.get():
            cmd += ["--no-plot"]
        if not self.var_strict.get():
            cmd += ["--no-strict-backends"]
        out_dir = self.var_out.get().strip()
        if out_dir:
            cmd += ["--out", out_dir]
        return cmd

    @staticmethod
    def _fluids_backend_available() -> bool:
        try:
            import fluids.compressible as comp  # type: ignore
        except Exception:
            return False
        candidates = [
            "isentropic_mass_flow",
            "isentropic_mass_flow_rate",
            "mass_flow_rate_isentropic",
            "critical_flow",
        ]
        return any(getattr(comp, name, None) for name in candidates)

    def on_run(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self._append("Process already running.\n")
            return
        cmd = self._build_cmd()
        if not cmd:
            return
        self._set_running(True)
        self._append("Running:\n  " + " ".join(cmd) + "\n")
        thread = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        thread.start()

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
            self.output_queue.put(f"\nExit code: {code}\n")
        except Exception as exc:
            self.output_queue.put(f"Failed to run: {exc}\n")
        finally:
            self.output_queue.put("__GUI_DONE__")
            self.process = None

    def on_stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            self._append("No running process.\n")
            return
        self._append("Stopping process...\n")
        self.process.terminate()

    def on_clear(self) -> None:
        self.text.delete("1.0", tk.END)

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
    app = VirtualTdiGui()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
