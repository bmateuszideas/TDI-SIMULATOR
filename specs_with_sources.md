
# Engine Specification with Sources – VW 1.9 TDI ALH (VP37, EA827 Block)

This document provides all physical and geometric parameters of the ALH engine, along with their original sources or methods of derivation.

---

## 1. Block and Crankshaft Geometry

| Parameter                         | Value    | Unit   | Source                              |
|----------------------------------|----------|--------|-------------------------------------|
| Cylinder bore                    | 79.5     | mm     | 📘 SSP 198, 📖 ETKA                  |
| Stroke                           | 95.5     | mm     | 📘 SSP 198, 📖 ETKA                  |
| Crank radius (Stroke / 2)        | 47.75    | mm     | 🔧 PM (Calculated)                  |
| Connecting rod length            | 144      | mm     | 🧪 DAT (Mahle), 📖 ETKA             |
| Cylinder offset (Desaxage)       | 0.5      | mm     | ⚙️ CAD models EA827, Internal Docs (`engine_reference_sources.yaml`, `kompletna_lista_z_danymi_rozszerzona.md`)          |
| Piston pin diameter              | 20       | mm     | 🧪 DAT (Mahle 030 107 065)          |
| Piston pin length                | 58       | mm     | 🧪 DAT, 🔧 PM                       |

---

## 2. Piston, Rings, and Reciprocating Mass

| Parameter                         | Value    | Unit   | Source                              |
|----------------------------------|----------|--------|-------------------------------------|
| Piston mass                      | ~440     | g      | 🧪 DAT (Mahle), 📚 HEY               |
| Wrist pin mass                   | ~120     | g      | 🧪 DAT, 🔧 PM                       |
| Ring set mass                    | ~40      | g      | 🧪 DAT, 🔧 PM                       |
| Total connecting rod mass        | ~580     | g      | 🧪 DAT (Aftermarket FCP/Hurricane)  |
| 1/4 Connecting rod (recip. mass) | ~145     | g      | 🧮 Calculated from total conrod mass |
| Total reciprocating mass         | ~750     | g      | 🔧 PM, sum                          |
| Piston crown area                | 0.00496  | m²     | 🧮 Calculated from 79.5 mm bore     |

---

## 3. Valvetrain and Timing

| Parameter                         | Value    | Unit   | Source                              |
|----------------------------------|----------|--------|-------------------------------------|
| Valves per cylinder              | 2        | –      | 📘 SSP, 📖 ETKA                      |
| Intake valve diameter            | 34.0     | mm     | 📖 ETKA (038 109 601), 🧪 DAT (INA)  |
| Exhaust valve diameter           | 29.0     | mm     | 📖 ETKA, 🧪 DAT                      |
| Max valve lift                   | ~9.0     | mm     | 🔧 PM, 🧪 DAT                        |
| Valve spring stiffness           | 30–40    | N/mm   | 🧪 DAT (INA), 📝 R&D                 |
| Valve mass (with keeper)         | ~100     | g      | 🧪 DAT, 📚 HEY                      |
| Camshaft duration                | 220–240  | °crank | 📘 SSP, 🔧 PM                        |
| Camshaft gear ratio              | 2:1      | –      | 📘 SSP, 📖 ETKA                      |

---

## 4. Injection System (VP37 + Injectors)

| Parameter                         | Value    | Unit   | Source                              |
|----------------------------------|----------|--------|-------------------------------------|
| Opening pressure (pre/main)      | 190/300  | bar    | 📘 SSP, 🧪 DAT (Bosch DSLA)          |
| Number of nozzle holes           | 5        | –      | 📘 SSP, 📖 ETKA                      |
| Hole diameter                    | 0.175    | mm     | 📘 SSP, 🧪 DAT                       |
| Max pressure (pump)              | ~950–1050| bar    | 📘 SSP, 🧪 DAT                       |
| Injection duration               | ~0.8–1.5 | ms     | 📝 R&D (SAE), 🔧 PM                 |
| Pump drive ratio                 | 2:1      | –      | 📘 SSP                              |
| Injections per crank rev        | 2        | –      | 📘 SSP (VP37 logic)                 |

---

## 5. Thermodynamics and Heat Transfer

| Parameter                         | Value    | Unit   | Source                              |
|----------------------------------|----------|--------|-------------------------------------|
| Cylinder head area               | ~0.0045  | m²     | ⚙️ CAD, 🧮 Calculated                |
| Piston top surface area          | 0.00496  | m²     | 🧮 Calculated                        |
| Cylinder wall area (variable)    | depends  | m²     | ⚙️ CAD, function of piston height   |
| Total heat transfer area         | 0.01–0.02| m²     | 📚 HEY, 📝 R&D, ⚙️ CAD              |
| Coolant capacity (full)          | ~6.0     | L      | 📄 TSB VW                           |
| Oil capacity                     | ~4.5     | L      | 📄 TSB VW                           |

---

## 6. Volumes and Compression

| Parameter                         | Value    | Unit   | Source                              |
|----------------------------------|----------|--------|-------------------------------------|
| Combustion chamber volume (V₀)   | ~49.5    | cm³    | 🧮 From CR & swept volume           |
| Cylinder displacement            | 474      | cm³    | 📘 SSP, total = 1896 / 4            |
| Compression ratio                | 19.5:1   | –      | 📘 SSP 198, 📄 TSB                  |
| Clearance volume                 | = V₀     | –      | 🧮 Definition                       |

---

## 7. General Engine Parameters

| Parameter                         | Value    | Unit   | Source                              |
|----------------------------------|----------|--------|-------------------------------------|
| Nominal genset RPM               | 1500     | RPM    | 📘 SSP, grid-synchronized           |
| Max RPM                          | ~4700    | RPM    | 📘 SSP, 📖 ETKA                     |
| Crank cycle angle                | 720      | °      | Standard 4-stroke cycle             |
| Solver time step (typical)       | 0.1–1.0  | ms     | 📚 HEY, 📝 R&D                      |

---

**Legend**:  
📘 SSP – VW Self-Study Program  
📖 ETKA – OEM Parts Catalog  
🧪 DAT – Supplier Technical Data (Mahle, Bosch, INA)  
🔧 PM – Physical Measurement  
📚 HEY – *Internal Combustion Engine Fundamentals* (Heywood)  
📝 R&D – Scientific papers, SAE Docs, Bosch Docs  
⚙️ CAD – CAD models of EA827  
📄 TSB – VW Technical Service Bulletins  
🧮 – Engineering Calculations  
