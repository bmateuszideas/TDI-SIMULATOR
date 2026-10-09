# I/O Contract

This document describes the simulator outputs exposed via the CLI (`metrics.txt` + CSV) and the dataset generator.

All metric values use SI units unless stated otherwise. For convenience several
pressure metrics are additionally exported in `bar` (suffix `_bar`); these are
derived from the SI value and are listed explicitly below.

## Full-cycle metrics (`virtual_tdi.full_cycle`)

| Metric key | Unit | Description |
| --- | --- | --- |
| `peak_pressure_pa` | Pa | Peak cylinder pressure over the cycle. |
| `peak_temp_k` | K | Peak cylinder temperature over the cycle. |
| `imep_pa` | Pa | Indicated mean effective pressure. |
| `imep_bar` | bar | IMEP in bar (`imep_pa / 1e5`). |
| `indicated_torque_nm` | N·m | Indicated torque (per engine). |
| `brake_torque_nm_est` | N·m | Estimated brake torque (can be negative at zero/low fuel). |
| `brake_power_kw_est` | kW | Estimated brake power. |
| `mass_start_kg_per_cyl` | kg | Cylinder mass at cycle start. |
| `mass_end_kg_per_cyl` | kg | Cylinder mass at cycle end. |
| `m_air_in_kg_per_cyl` | kg | Total intake air mass over the cycle. |
| `m_exhaust_out_kg_per_cyl` | kg | Total exhaust mass out over the cycle. |
| `p_intake_mean_pa` | Pa | Mean intake manifold pressure. |
| `t_intake_mean_k` | K | Mean intake manifold temperature. |
| `p_exhaust_mean_pa` | Pa | Mean exhaust manifold pressure. |
| `t_exhaust_mean_k` | K | Mean exhaust manifold temperature. |
| `fuel_energy_in_j_per_cyl` | J | Fuel chemical energy input. |
| `q_comb_j_per_cyl` | J | Integrated combustion heat release. |
| `q_wall_j_per_cyl` | J | Integrated wall heat loss. |
| `exhaust_power_kw_est` | kW | Exhaust enthalpy power available to a turbine (per engine). |
| `iq_cmd_mg_per_stroke` | mg | Commanded fuel quantity per stroke. |
| `iq_mg_per_stroke` | mg | Fuel quantity per stroke after ECU limiting. |
| `iq_eff_mg_per_stroke` | mg | Effective fuel quantity entering the cylinder model. |
| `soi_main_deg_model` | deg | Main start of injection used by the model (after map/offset/delay). |
| `soi_pilot_deg_model` | deg | Pilot start of injection used by the model. |
| `duration_main_deg` | deg | Main injection duration (VP37 cam model when available). |
| `pilot_fraction` | - | Fuel mass fraction injected in the pilot shot. |
| `n146_mv_est` | mV | Estimated N146 pump voltage for the given IQ (if map present). |
| `maf_target_mg_per_stroke` | mg/stroke | MAF target from the EGR map (if present). |
| `smoke_iq_max_mg_per_stroke` | mg/stroke | Smoke-limiter maximum IQ (if map present). |
| `boost_target_mbar_abs` | mbar | Boost pressure target from the boost map (if present). |

## Closed-cycle metrics (`virtual_tdi.solver`)

| Metric key | Unit | Description |
| --- | --- | --- |
| `mass_kg_per_cyl` | kg | Cylinder mass at start angle. |
| `q_total_j_per_cyl` | J | Total chemical energy input from fuel. |
| `peak_pressure_pa` | Pa | Peak cylinder pressure over the simulated window. |
| `peak_pressure_bar` | bar | Peak pressure in bar (`peak_pressure_pa / 1e5`). |
| `peak_temp_k` | K | Peak cylinder temperature over the simulated window. |
| `wi_j_per_cyl` | J | Indicated work over the simulated window. |
| `imep_pa` | Pa | Indicated mean effective pressure. |
| `indicated_torque_nm` | N·m | Indicated torque (per engine). |
| `brake_torque_nm_est` | N·m | Estimated brake torque (can be negative at zero/low fuel). |

## Transient outputs (`out/transient.csv`)

| Column | Unit | Description |
| --- | --- | --- |
| `t_s` | s | Time since simulation start. |
| `rpm` | rpm | Shaft speed (mean-value model). |
| `fuel_mg_per_stroke` | mg/stroke | Governor-commanded fuel quantity. |
| `brake_torque_nm` | N·m | Estimated brake torque at the current operating point. |
| `load_torque_nm` | N·m | Applied load torque. |
| `brake_power_kw` | kW | Brake power. |
| `p_intake_bar_abs` | bar | Intake manifold pressure (abs) with first-order turbo lag. |
| `imep_bar` | bar | IMEP at the current operating point. |
| `peak_pressure_bar` | bar | Peak cylinder pressure at the current operating point. |

## Time-series CSV outputs (`cycle.csv`)

The CLI exports cycle data with columns named after their SI units (e.g., `pressure_pa`, `temperature_k`,
`p_intake_pa`, `p_exhaust_pa`, `dq_comb_j_per_deg`). These headers are written verbatim to the CSV.

## Dataset outputs (`virtual_tdi.dataset`)

The dataset generator prefixes simulator metrics with `out_` (for example, `out_peak_pressure_pa`).
CSV headers are identical to the row field names.
