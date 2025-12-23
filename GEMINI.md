# Project: 1.9TDI-WIRTUALNY_KLON

## Project Overview

This repository contains a white-box 0D simulator, referred to as the "digital ghost" of a 1.9 TDI engine. It is a Python-based project designed to simulate the thermodynamic and mechanical behavior of the engine, offering various levels of fidelity and control. The simulator can operate in a "physics-first" mode (without ECU maps) or an "ECU-first" mode (incorporating ECU maps for control and limits).

**Key Features:**

*   **Engine Geometry:** Implements crank mechanism geometry with desaxage.
*   **Thermodynamics:** 0D thermodynamics with variable specific heat ratio (`γ(T)`) and heat losses (Woschni simplified).
*   **Combustion:** Double-Wiebe model for pilot and main injection, with ignition delay (Arrhenius or fixed).
*   **Full 720° Cycle:** Includes gas exchange, compressible flow through valves (orifice model).
*   **Valve Train:** Uses valve lift tables (e.g., `profil_krzywek_4cylindry.md`) if available.
*   **VP37 Injection Pump:** Simplified model for hydraulic delay and injection duration based on cam profiles (e.g., `skok_tloczka_vp37_de110.csv`).
*   **ECU Emulation:** Can integrate factory ECU maps for Start of Injection (SOI), N146 pump voltage, Smoke Limiter, EGR target MAF, and Boost pressure. These maps act as a reference layer, not replacing the physical model.
*   **Turbo Coupling:** Supports iterative turbocharger power balance.
*   **Physics Backends:** Optional integration with `CoolProp` for thermodynamics and `fluids` for flow models.
*   **Data Generation:** Capable of generating synthetic data for machine learning/deep learning applications.

## Building and Running

The project requires Python and its dependencies.

1.  **Install Dependencies:**
    Install the required Python packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the GUI (optional):**
    A simple graphical interface is available for running simulations:
    ```bash
    python -m virtual_tdi gui
    ```

3.  **Run Simulations via CLI:**
    The primary way to run simulations is through the command-line interface. The main script is `virtual_tdi/cli.py`.

    **Examples:**

    *   **Full 720° Cycle Simulation:**
        ```bash
        python -m virtual_tdi --mode full --rpm 1500 --fuel diesel --fuel-mg 20 --out out
        ```
    *   **Solve for Target Brake Power:**
        ```bash
        python -m virtual_tdi --mode full --rpm 1500 --fuel diesel --target-brake-kw 10 --fuel-mg-min 2 --fuel-mg-max 40 --out out
        ```
    *   **Control Fuel Quantity via N146 Voltage (using map):**
        ```bash
        python -m virtual_tdi --mode full --rpm 1500 --n146-mv 2500 --out out
        ```
    *   **ECU Mode (with smoke/EGR limits):**
        ```bash
        python -m virtual_tdi --mode full --ecu limit --rpm 1500 --n146-mv 2500 --out out
        ```
    *   **Generate Synthetic Data (Physics-first):**
        ```bash
        python -m virtual_tdi dataset --n 5000 --rpm-min 1500 --rpm-max 1500 --ecu off --p-intake-min 1.0 --p-intake-max 1.8 --fuel-temp-min 20 --fuel-temp-max 90 --iq-basis volume --nozzles 0.184,0.205,0.216,0.230 --step-deg 1.0 --out data/synthetic.csv
        ```

    **Output:**
    Simulation results are saved to the specified output directory (`--out`), typically containing:
    *   `cycle.csv`: Detailed cycle data (e.g., crank angle, pressure, temperature, volume, mass).
    *   `metrics.txt`: Summary metrics from the simulation.
    *   Plot images: `p_t.png` (pressure/temperature vs. crank angle), `heat.png` (heat release rates), `pv.png` (PV diagram), `mass.png` (cylinder mass vs. crank angle for full cycle).

## Development Conventions

*   **Modular Structure:** The core logic is organized into Python modules within the `virtual_tdi` directory (e.g., `solver.py`, `full_cycle.py`, `geometry.py`, `thermo.py`, `combustion.py`).
*   **Configuration:** Engine and simulation parameters are primarily loaded from `engine_reference_sources.yaml`. ECU maps are provided as `.csv` files.
*   **Physics vs. ECU:** The simulator aims to be a physical model. ECU maps are treated as a control or reference layer, not a replacement for underlying physics. This distinction is crucial for generating physics-based data.
*   **Optional Backends:** The project supports optional "heavy" backends (CoolProp, Fluids) for more accurate physical properties. If these are enabled (`--strict-backends`) but missing, the CLI will prompt the user.

## Testing

Unit tests are available in the `tests/` directory. To run them:

```bash
python -m unittest discover -s tests -p "test_*.py"
```
