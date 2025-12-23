# CR vs Vc report (ALH/1.9 TDI)

Inputs (reference):
- bore = 79.5 mm
- stroke = 95.5 mm
- gasket_thickness = 1.63 mm (compressed)
- piston_protrusion = 1.05 mm (above deck)
- head_recess_volume = 0.8 cm3
- piston_bowl_volume reference = 24.5 cm3

Formula used:
- Vd = (pi/4) * bore^2 * stroke
- clearance_thickness = max(0, gasket_thickness - piston_protrusion)
- Vc = bowl_volume + head_recess_volume + (pi/4 * bore^2 * clearance_thickness)
- CR = (Vd + Vc) / Vc

Computed results:
- Vd = 474.054 cm3
- clearance_thickness = 0.58 mm
- With bowl_volume = 24.5 cm3 -> Vc = 28.179 cm3 -> CR = 17.823 (delta -1.677 vs 19.5)
- For CR = 19.5 -> Vc_target = 25.625 cm3 -> bowl_volume_required = 21.945 cm3 (delta -2.555 cm3 vs 24.5)

Action taken:
- bowl_volume in engine_reference_sources.yaml set to 21.95 cm3 to match CR 19.5 with given gasket/protrusion/head recess.

What-if gasket variants (compressed thickness scenarios)
- Inputs held constant: piston_protrusion = 1.05 mm, head_recess = 0.8 cm3, bowl = 21.95 cm3
- Table shows how gasket thickness shifts Vc and CR (example deltas ±0.10 mm around 2-hole baseline):

| Gasket thickness (mm) | Clearance (mm) | Vc (cm3) | CR |
|---|---|---|---|
| 1.53 | 0.48 | 25.133 | 19.862 |
| 1.63 (baseline) | 0.58 | 25.629 | 19.497 |
| 1.73 | 0.68 | 26.125 | 19.145 |

Interpretacja:
- ~±0.10 mm w grubości uszczelki przesuwa CR o ok. ±0.36 punktu przy stałej misce 21.95 cm3 i protrusion 1.05 mm.
