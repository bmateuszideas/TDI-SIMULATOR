# I/O Contract

This document describes the simulator outputs exposed via the CLI (`metrics.txt` + CSV) and the dataset generator.
All metric values use SI units unless stated otherwise.

## Full-cycle metrics (`virtual_tdi.full_cycle`)

| Metric key | Unit | Description |
| --- | --- | --- |
| `peak_pressure_pa` | Pa | Peak cylinder pressure over the cycle. |
| `peak_temp_k` | K | Peak cylinder temperature over the cycle. |
| `imep_pa` | Pa | Indicated mean effective pressure. |
| `indicated_torque_nm` | N·m | Indicated torque (per engine). |
| `brake_torque_nm_est` | N·m | Estimated brake torque. |
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

## Closed-cycle metrics (`virtual_tdi.solver`)

| Metric key | Unit | Description |
| --- | --- | --- |
| `mass_kg_per_cyl` | kg | Cylinder mass at start angle. |
| `q_total_j_per_cyl` | J | Total chemical energy input from fuel. |
| `peak_pressure_pa` | Pa | Peak cylinder pressure over the simulated window. |
| `peak_temp_k` | K | Peak cylinder temperature over the simulated window. |
| `wi_j_per_cyl` | J | Indicated work over the simulated window. |
| `imep_pa` | Pa | Indicated mean effective pressure. |
| `indicated_torque_nm` | N·m | Indicated torque (per engine). |
| `brake_torque_nm_est` | N·m | Estimated brake torque. |

## Time-series CSV outputs (`cycle.csv`)

The CLI exports cycle data with columns named after their SI units (e.g., `pressure_pa`, `temperature_k`,
`p_intake_pa`, `p_exhaust_pa`, `dq_comb_j_per_deg`). These headers are written verbatim to the CSV.

## Dataset outputs (`virtual_tdi.dataset`)

The dataset generator prefixes simulator metrics with `out_` (for example, `out_peak_pressure_pa`).
CSV headers are identical to the row field names.
