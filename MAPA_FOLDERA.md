# MAPA FOLDERA: 1.9TDI-WIRTUALNY_KLON

_Wygenerowano: 2025-12-23 03:07:10_

To jest automatyczna mapa folderu: drzewo + opis kazdego pliku (osobno), a dla skryptow Python: zaleznosci, API i wybrane wzory (linie z kodu).

## 1) Drzewo katalogu (bez cache/pyc)

```text
.continue/
  agents/
    new-config-1.yaml
    new-config.yaml
  prompts/
    new-prompt.md
  rules/
    cyfrowy-duch-rules.md
    use-detailed-physics.md
    use-named-exports.md
.history-memo/
  2025-12-22.md
1.9TDI-WIRTUALNY_KLON.code-workspace
CYFROWY_DUCH_FUNDAMENTALNE_ZALOZENIA.md
DANE_TECHNICZNO_FIZYCZNE.md
GEMINI.md
MAPA_FOLDERA.md
Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv
Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv
Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv
Mapa_EGR___interpolowana_mapa_MAF.csv
README.md
SMIETNIK/
  NA PODSTAWIE LISTY PODAJ WSZYSTKIE DANE KTORE MOŻ....md
  RAPORT_IMEP_I_KATALOG.md
  kompletna_lista_z_danymi_SCALONA.md
  kompletna_lista_z_danymi_rozszerzona.md
  kompletna_lista_z_danymi_rozszerzona_pelna.md
  output.png
  specs_with_sources.md
  tabela_danych_pochodnych_i_bezposrednich.md
  uzupelniona_lista_z_danymi_i_zrodlami.md
SPECYFIKACJA MATEMATYCZNA SOLVERA_ 1.9 TDI COGENERATION ENGINE.md
SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv
data/
  synthetic.csv
docs/
  BASELINE_MAPY_ECU_I_OSPRZET.md
  CHECKLIST_CYFROWY_DUCH.md
  PARAMETRY_SILNIKA.md
  RAPORT_CR_VC.md
  ROADMAP_CYFROWY_DUCH.md
engine_reference_sources.yaml
profil_krzywek_4cylindry.md
profil_krzywek_wałek.md
requirements.txt
skok_tloczka_vp37_de110.csv
src/
  main.py
tests/
  test_backends.py
  test_config_loader.py
  test_controller.py
  test_dataset.py
  test_dataset_config.py
  test_edc_maps.py
  test_full_cycle_dynamic_manifolds.py
  test_full_cycle_sanity.py
  test_full_cycle_vp37_hrr.py
  test_geometry.py
  test_hydraulics.py
  test_lift_table.py
  test_n146_map.py
  test_soi_map.py
  test_solver_sanity.py
  test_turbo_coupled.py
  test_valvetrain.py
  test_vp37_cam.py
virtual_tdi/
  __init__.py
  __main__.py
  cli.py
  combustion.py
  config_loader.py
  controller.py
  coupled.py
  dataset.py
  edc_maps.py
  flow.py
  full_cycle.py
  geometry.py
  gui.py
  heat_transfer.py
  hydraulics.py
  injection.py
  lift_table.py
  models.py
  n146_map.py
  soi_map.py
  solver.py
  thermo.py
  turbo.py
  valvetrain.py
  vp37.py
  vp37_cam.py
```

## 2) Root - szybka klasyfikacja

- `1.9TDI-WIRTUALNY_KLON.code-workspace` -> `IDE`
- `CYFROWY_DUCH_FUNDAMENTALNE_ZALOZENIA.md` -> `DOC`
- `DANE_TECHNICZNO_FIZYCZNE.md` -> `DOC`
- `GEMINI.md` -> `DOC`
- `MAPA_FOLDERA.md` -> `DOC`
- `Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv` -> `DATA`
- `Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv` -> `DATA`
- `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv` -> `DATA`
- `Mapa_EGR___interpolowana_mapa_MAF.csv` -> `DATA`
- `README.md` -> `DOC`
- `SPECYFIKACJA MATEMATYCZNA SOLVERA_ 1.9 TDI COGENERATION ENGINE.md` -> `DOC`
- `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv` -> `DATA`
- `engine_reference_sources.yaml` -> `DATA`
- `profil_krzywek_4cylindry.md` -> `DATA`
- `profil_krzywek_wałek.md` -> `DATA`
- `requirements.txt` -> `DOC`
- `skok_tloczka_vp37_de110.csv` -> `DATA`

---

# 3) OPIS PLIKOW (KAZDY PLIK OSOBNO)

## 1.9TDI-WIRTUALNY_KLON.code-workspace

- Typ: `IDE`; rozmiar: `101` B

## CYFROWY_DUCH_FUNDAMENTALNE_ZALOZENIA.md

- Typ: `DOC`; rozmiar: `3958` B
- Linie pliku: `98`
- Poczatkowe linie (head):
```text
﻿## "CYFROWY DUCH" SILNIKA – FUNDAMENTALNE ZAŁOŻENIA

### 1. Cel nadrzędny
Stworzyć cyfrowego bliźniaka fizycznego silnika 1.9 TDI, który:
- nie jest uproszczeniem – ma tę samą złożoność co rzeczywisty silnik,
- ucieleśnia prawa fizyki zamiast je przybliżać,
- pozwala na inżynierską zabawę w "co jeśli" bez rozkręcania silnika.

### 2. Filozofia projektowa
- żadnych "czarnych skrzynek" – każdy efekt ma swoje równania,
- żadnych stałych "magicznych" – wszystkie parametry mierzalne,
- fizyka ponad szybkością obliczeń – wolimy dokładność niż szybkość.

### 3. Trzy warstwy modelu
**Warstwa 1: Geometria i kinematyka**
- Silnik jako maszyna geometryczna.
- Krzywki, tłoki, korbowody opisane równaniami.
- Klucz: dokładne dane pomiarowe (nie przybliżenia).

**Warstwa 2: Fizyko-chemia**
- Silnik jako przetwornik energii chemicznej.
- Pełna kinetyka reakcji, gazy rzeczywiste, wymiana ciepła.
- Klucz: brak założeń o "idealności".

**Warstwa 3: Inteligencja**
```

## DANE_TECHNICZNO_FIZYCZNE.md

- Typ: `DOC`; rozmiar: `3912` B
- Linie pliku: `83`
- Poczatkowe linie (head):
```text
﻿# DANE TECHNICZNO-FIZYCZNE (SCALONE) - VW 1.9 TDI (ALH/1Z/AHU)

_Wygenerowano: 2025-12-23 02:59:03_

Cel: **jeden** plik jako wspolna baza danych techniczno-fizycznych dla symulatora.

## 1) Zrodla prawdy / priorytet danych

- `engine_reference_sources.yaml` jest **kanonicznym** zrodlem liczb i jednostek uzywanych przez kod.
- Pliki wejsciowe profili i map (uzywane przez kod):
  - `profil_krzywek_4cylindry.md` -> `virtual_tdi/lift_table.py` (valve lift)
  - `skok_tloczka_vp37_de110.csv` -> `virtual_tdi/vp37_cam.py` (profil VP37)
  - Mapy ECU `.csv` (SOI/N146/Smoke/EGR/Boost) -> `virtual_tdi/*_map.py`, `virtual_tdi/edc_maps.py`

## 2) Geometria silnika (z `engine_reference_sources.yaml`)

- Srednica cylindra (bore): `79.5` mm
- Skok tloka (stroke): `95.5` mm
- Dlugosc korbowodu (rod): `144.0` mm
- Offset cylindra/desaxage: `0.5` mm

W kodzie (patrz `virtual_tdi/geometry.py`) pozycja tloka i objetosc cylindra sa liczone z uwzglednieniem offsetu (desaxage).

## 3) Komora spalania / CR / Vc

```

## GEMINI.md

- Typ: `DOC`; rozmiar: `4656` B
- Linie pliku: `82`
- Poczatkowe linie (head):
```text
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
```

## MAPA_FOLDERA.md

- Typ: `DOC`; rozmiar: `93309` B
- Linie pliku: (pomijam head, bo to plik autogenerowany)

## Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv

- Typ: `DATA`; rozmiar: `2072` B
- Separator: `,`; wiersze: `17`
- Naglowek + pierwsze wiersze:
```text
RPM (Obroty silnika)/IQ(MG/SUW),0,00 IQ,3,00 IQ,6,00 IQ,9,60 IQ,12,00 IQ,16,00 IQ,20,00 IQ,24,00 IQ,26,00 IQ,28,00 IQ,32,00 IQ,36,00 IQ,40,00 IQ,Źródło
5355,11,4°,12,4°,13,5°,14,0°,14,5°,14,5°,14,5°,14,5°,14,6°,15,1°,15,6°,15,6°,15,6°,1
4494,8,5°,9,4°,10,4°,10,8°,11,6°,12,4°,13,1°,13,6°,14,6°,15,1°,15,6°,15,6°,15,6°,1
3990,6,4°,7,3°,8,2°,8,4°,9,2°,10,1°,10,9°,11,6°,12,2°,15,1°,15,6°,15,6°,15,6°,1
3738,2,4°,3,2°,4,3°,4,5°,5,2°,6,0°,6,5°,7,5°,8,4°,13,8°,14,4°,14,4°,14,4°,1
3234,0,4°,0,8°,1,3°,1,6°,2,0°,3,1°,4,0°,4,6°,5,8°,9,5°,12,0°,12,0°,12,0°,1
2982,-0,6°,0,0°,0,0°,0,0°,0,3°,1,5°,2,7°,3,2°,4,3°,7,7°,10,8°,10,8°,10,8°,1
2730,-0,6°,-0,6°,-0,6°,-0,6°,-0,3°,0,8°,1,5°,2,2°,3,2°,6,3°,9,6°,9,6°,9,6°,1
```

## Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv

- Typ: `DATA`; rozmiar: `2799` B
- Separator: `,`; wiersze: `17`
- Naglowek + pierwsze wiersze:
```text
Engine speed (rpm)vsIQ(mg/suw)-mVolts,IQ 0,00 mg/stroke,IQ 0,40 mg/stroke,IQ 2,00 mg/stroke,IQ 4,00 mg/stroke,IQ 6,00 mg/stroke,IQ 8,00 mg/stroke,IQ 10,00 mg/stroke,IQ 12,00 mg/stroke,IQ 15,00 mg/stroke,IQ 20,00 mg/stroke,IQ 25,00 mg/stroke,IQ 30,00 mg/stroke,IQ 35,00 mg/stroke,IQ 40,00 mg/stroke,IQ 51,00 mg/stroke
4494,0,00,1067,16,1271,06,1420,02,1549,45,1719,17,1919,41,2100,12,2330,89,2909,65,3490,84,3929,18,4293,04,4539,68,4686,20
3990,0,00,1096,46,1280,83,1429,79,1559,22,1719,17,1909,65,2100,12,2310,13,2851,04,3341,88,3761,90,4122,10,4389,50,4617,83
3507,0,00,1130,65,1300,37,1439,56,1568,99,1728,94,1909,65,2080,59,2280,83,2771,67,3172,16,3560,44,3930,40,4192,92,4484,74
3003,0,00,1169,72,1329,67,1460,32,1570,21,1750,92,1909,65,2080,59,2261,29,2692,31,3021,98,3411,48,3722,83,3980,46,4269,84
2499,0,00,1179,49,1350,43,1490,84,1599,51,1750,92,1909,65,2061,05,2241,76,2593,41,2892,55,3241,76,3522,59,3750,92,4004,88
1995,0,00,1203,91,1390,72,1521,37,1631,26,1781,44,1920,64,2041,51,2201,47,2501,83,2741,15,3051,28,3290,60,3501,83,3760,68
1743,0,00,1249,08,1429,79,1560,44,1680,10,1800,98,1940,17,2061,05,2200,24,2451,77,2670,33,2969,48,3172,16,3378,51,3628,82
```

## Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv

- Typ: `DATA`; rozmiar: `1078` B
- Separator: `,`; wiersze: `16`
- Naglowek + pierwsze wiersze:
```text
RPM,0.0,10.0,15.0,2000.0,2500.0,3000.0,3500.0,4000.0,8500.0
4746,1198.0,1256.0,1316.0,1404.0,1492.0,1590.0,1669.0,1500.0,1500.0
4994,1149.0,1219.0,1278.0,1384.0,1482.0,1600.0,1708.0,1718.0,1806.0
4242,1100.0,1190.0,1259.0,1355.0,1473.0,1589.0,1708.0,1835.0,1914.0
3990,1090.0,1160.0,1240.0,1335.0,1454.0,1580.0,1698.0,1950.0,1950.0
3507,1070.0,1130.0,1200.0,1296.0,1416.0,1552.0,1698.0,1950.0,1950.0
3003,1050.0,1091.0,1160.0,1247.0,1376.0,1532.0,1689.0,1950.0,1950.0
2499,1021.0,1061.0,1120.0,1218.0,1328.0,1502.0,1680.0,1950.0,1950.0
```

## Mapa_EGR___interpolowana_mapa_MAF.csv

- Typ: `DATA`; rozmiar: `1339` B
- Separator: `,`; wiersze: `17`
- Naglowek + pierwsze wiersze:
```text
RPM,0.0,3.0,7.4,10.0,12.4,15.0,17.4,20.0,22.4,25.0,29.0,33.0,51.0
5355,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0
3612,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0,850.0
3423,330.0,364.8,404.8,445.5,474.8,520.0,50.0,600.0,650.0,704.8,765.6,802.0,850.0
2499,276.7,309.8,344.8,384.8,424.8,454.8,494.8,534.8,594.8,644.8,700.0,748.0,850.0
2247,266.7,294.8,324.8,359.8,394.8,424.8,464.8,509.8,569.8,614.8,670.0,747.0,850.0
1995,256.7,289.8,314.8,349.8,384.8,414.8,449.8,94.8,544.8,578.8,639.6,718.0,850.0
1743,256.7,284.8,304.8,349.8,384.8,414.8,454.8,99.8,544.8,584.8,650.0,719.0,880.0
```

## README.md

- Typ: `DOC`; rozmiar: `6468` B
- Linie pliku: `112`
- Poczatkowe linie (head):
```text
# 1.9TDI-WIRTUALNY_KLON

Repo zawiera implementację "cyfrowego ducha" 1.9 TDI jako białoskrzynkowy symulator 0D.

## Dokumenty
- `docs/ROADMAP_CYFROWY_DUCH.md`
- `docs/CHECKLIST_CYFROWY_DUCH.md`
- `docs/BASELINE_MAPY_ECU_I_OSPRZET.md`

## Bazowa kalibracja map (ważne)

Wszystkie fabryczne mapy ECU, które są w repo (SOI / N146 / SmokeLimiter / EGR / BOOST) należy traktować jako **skalibrowane pod konkretną konfigurację osprzętu**:

- Wtryskiwacze: końcówka `0.184 x 5` (średnica otworka × liczba otworów).
- Pompa VP37: krzywka/tarcza `DE110` (profil w `skok_tloczka_vp37_de110.csv`).
- Wałek rozrządu / wznios zaworów: profil z `profil_krzywek_4cylindry.md`.

Jeśli podmieniasz końcówki (np. `0.205`) lub inne elementy, **te mapy nie są już “tym samym ECU”** w sensie kalibracji. To jest bardzo dobra informacja dla ML/DL: traktuj wariant osprzętu jako cechę/klasę i ucz model na danych z różnych konfiguracji (lub używaj odpowiednich map dla danej konfiguracji).

## Mapy ECU a fizyka (ważne)

Mapy ECU w repo są **referencją/warstwą sterownika**, a nie “silnikiem” symulatora. Symulator ma być modelem fizycznym; mapy:
- pomagają odwzorować zachowanie seryjnego ECU (warstwa “Inteligencja”),
- mogą służyć jako ograniczenia (np. smoke limiter) lub cele regulatorów,
- nie powinny zastępować mechaniki/termo/chemii.
```

## SPECYFIKACJA MATEMATYCZNA SOLVERA_ 1.9 TDI COGENERATION ENGINE.md

- Typ: `DOC`; rozmiar: `11540` B
- Linie pliku: `172`
- Poczatkowe linie (head):
```text
# **SPECYFIKACJA MATEMATYCZNA SOLVERA: 1.9 TDI COGENERATION ENGINE**

Typ dokumentu: Algorytmy Fizyczne & Równania Konstytutywne  
Zastosowanie: Symulacja czasu rzeczywistego (Real-Time Physics) dla układu kogeneracyjnego (CHP)

## **1\. KINEMATYKA UKŁADU KORBOWEGO (SOLVER GEOMETRII)**

**Cel:** Wyznaczenie dokładnej objętości cylindra $V(\\theta)$ i jej pochodnej $dV/d\\theta$ w każdym kroku czasowym. Jest to fundament dla równań termodynamiki.

### **Równanie Ruchu Tłoka (Z uwzględnieniem Desaxage)**

W silnikach VW (blok EA827) oś sworznia tłoka jest przesunięta względem osi cylindra (offset/desaxage $\\delta$). Uproszczony wzór sinus-cosinus jest tutaj **niewystarczający**.

**Wzór implementacyjny:**

$$s(\\theta) \= r \\cos(\\theta) \+ \\sqrt{L^2 \- (r \\sin(\\theta) \- \\delta)^2}$$  
Gdzie:

* $s(\\theta)$: Chwilowe położenie tłoka (od osi wału).  
* $r$: Promień wykorbienia (47.75 mm).  
* $L$: Długość korbowodu (144.0 mm).  
* $\\delta$: Przesunięcie osi (Offset, typowo \~0.5-1.0 mm w TDI).  
* $\\theta$: Kąt obrotu wału (0 \= GMP spalania).

### **Chwilowa Objętość Cylindra**
```

## SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv

- Typ: `DATA`; rozmiar: `1062` B
- Separator: `,`; wiersze: `15`
- Naglowek + pierwsze wiersze:
```text
RPM,300.0,350.0,400.0,450.0,503.3,550.0,600.0,650.0,750.0,850.0,851.0,852.0,853.0
5355,7.2,8.8,11.2,13.4,15.5,17.3,19.0,20.2,21.8,25.0,25.0,25.0,25.0
4242,10.2,12.0,13.6,16.0,17.3,20.0,23.2,25.0,28.0,34.0,34.0,34.0,34.0
3759,10.4,13.2,15.6,18.4,22.0,25.6,28.6,31.4,34.0,36.0,36.5,36.5,36.5
3507,10.2,12.4,15.0,18.0,22.8,25.8,28.8,32.0,34.9,36.5,36.5,36.5,36.5
3255,10.2,13.0,16.0,19.4,23.2,26.0,29.0,32.4,35.4,37.5,37.5,37.5,37.5
2751,11.2,14.0,18.0,21.0,24.0,27.0,30.0,33.2,36.3,37.5,37.5,37.5,37.5
2491,11.3,15.2,19.0,23.0,26.0,29.0,32.0,35.2,37.5,38.0,38.0,38.0,38.0
```

## engine_reference_sources.yaml

- Typ: `DATA`; rozmiar: `7932` B

## profil_krzywek_4cylindry.md

- Typ: `DATA`; rozmiar: `15163` B
- Linie pliku: `204`
- Poczatkowe linie (head):
```text
# Profil wzniosu zaworów dla 4 cylindrów (cykl 4-suwowy, 720° CK)

| Kąt Wału [°CK] | Dolotowy_Cyl1 | Wydechowy_Cyl1 | Dolotowy_Cyl3 | Wydechowy_Cyl3 | Dolotowy_Cyl4 | Wydechowy_Cyl4 | Dolotowy_Cyl2 | Wydechowy_Cyl2 |
|----------------|------------------|------------------|------------------|------------------|------------------|------------------|------------------|------------------|
| 0.0 | 0.000 | 0.000 | 1.735 | 0.000 | 0.943 | 0.344 | 0.000 | 0.959 |
| 3.6 | 0.000 | 0.000 | 1.413 | 0.000 | 1.218 | 0.198 | 0.000 | 1.238 |
| 7.2 | 0.000 | 0.000 | 1.119 | 0.000 | 1.523 | 0.092 | 0.000 | 1.544 |
| 10.8 | 0.000 | 0.000 | 0.854 | 0.000 | 1.854 | 0.026 | 0.000 | 1.876 |
| 14.4 | 0.000 | 0.000 | 0.622 | 0.000 | 2.208 | 0.000 | 0.000 | 2.229 |
| 18.0 | 0.000 | 0.000 | 0.424 | 0.000 | 2.583 | 0.000 | 0.000 | 2.600 |
| 21.6 | 0.000 | 0.000 | 0.263 | 0.000 | 2.975 | 0.000 | 0.000 | 2.984 |
| 25.2 | 0.000 | 0.000 | 0.139 | 0.000 | 3.380 | 0.000 | 0.000 | 3.378 |
| 28.8 | 0.000 | 0.000 | 0.054 | 0.000 | 3.795 | 0.000 | 0.000 | 3.778 |
| 32.4 | 0.000 | 0.000 | 0.008 | 0.000 | 4.217 | 0.000 | 0.000 | 4.179 |
| 36.0 | 0.000 | 0.000 | 0.000 | 0.000 | 4.641 | 0.000 | 0.000 | 4.577 |
| 39.6 | 0.000 | 0.000 | 0.000 | 0.000 | 5.064 | 0.000 | 0.000 | 4.968 |
| 43.2 | 0.000 | 0.000 | 0.000 | 0.000 | 5.482 | 0.000 | 0.000 | 5.347 |
| 46.8 | 0.000 | 0.000 | 0.000 | 0.000 | 5.891 | 0.000 | 0.000 | 5.711 |
| 50.4 | 0.000 | 0.000 | 0.000 | 0.000 | 6.288 | 0.000 | 0.000 | 6.057 |
| 54.0 | 0.000 | 0.000 | 0.000 | 0.000 | 6.669 | 0.000 | 0.000 | 6.379 |
| 57.6 | 0.000 | 0.000 | 0.000 | 0.000 | 7.030 | 0.000 | 0.000 | 6.675 |
| 61.2 | 0.000 | 0.000 | 0.000 | 0.000 | 7.369 | 0.000 | 0.000 | 6.942 |
| 64.8 | 0.000 | 0.000 | 0.000 | 0.000 | 7.683 | 0.000 | 0.000 | 7.176 |
| 68.4 | 0.000 | 0.000 | 0.000 | 0.000 | 7.968 | 0.000 | 0.000 | 7.376 |
| 72.0 | 0.000 | 0.000 | 0.000 | 0.000 | 8.223 | 0.000 | 0.000 | 7.539 |
```

## profil_krzywek_wałek.md

- Typ: `DATA`; rozmiar: `5345` B
- Linie pliku: `204`
- Poczatkowe linie (head):
```text
# Profil wzniosu zaworów (Krzywki) – 0–720° CK

| Kąt Wału [°CK] | Wznios Dolot [mm] | Wznios Wydech [mm] |
|----------------|-------------------|--------------------|
| 0.0 | 0.000 | 0.000 |
| 3.6 | 0.000 | 0.000 |
| 7.2 | 0.000 | 0.000 |
| 10.8 | 0.000 | 0.000 |
| 14.4 | 0.000 | 0.000 |
| 18.0 | 0.000 | 0.000 |
| 21.6 | 0.000 | 0.000 |
| 25.2 | 0.000 | 0.000 |
| 28.8 | 0.000 | 0.000 |
| 32.4 | 0.000 | 0.000 |
| 36.0 | 0.000 | 0.000 |
| 39.6 | 0.000 | 0.000 |
| 43.2 | 0.000 | 0.000 |
| 46.8 | 0.000 | 0.000 |
| 50.4 | 0.000 | 0.000 |
| 54.0 | 0.000 | 0.000 |
| 57.6 | 0.000 | 0.000 |
| 61.2 | 0.000 | 0.000 |
| 64.8 | 0.000 | 0.000 |
| 68.4 | 0.000 | 0.000 |
| 72.0 | 0.000 | 0.000 |
```

## requirements.txt

- Typ: `DOC`; rozmiar: `356` B

## skok_tloczka_vp37_de110.csv

- Typ: `DATA`; rozmiar: `128113` B
- Separator: `,`; wiersze: `3601`
- Naglowek + pierwsze wiersze:
```text
Kat_obrotu_pompy_deg,Skok_tloczka_mm
0.0,0.0
0.1000277854959711,0.00798709083789927
0.2000555709919422,0.015974126902747018
0.3000833564879133,0.023961053421867336
0.4001111419838844,0.031947815623335554
0.5001389274798556,0.03993435873635384
0.6001667129758266,0.047920627991626795
```

## .continue/agents/new-config-1.yaml

- Typ: `DATA`; rozmiar: `636` B

## .continue/agents/new-config.yaml

- Typ: `DATA`; rozmiar: `636` B

## .continue/prompts/new-prompt.md

- Typ: `DOC`; rozmiar: `179` B
- Linie pliku: `7`
- Poczatkowe linie (head):
```text
---
name: New prompt
description: odpowiadaj po polsku
invokable: true
---

Please write a thorough suite of unit tests for this code, making sure to cover all relevant edge cases
```

## .continue/rules/cyfrowy-duch-rules.md

- Typ: `DOC`; rozmiar: `315` B
- Linie pliku: `12`
- Poczatkowe linie (head):
```text
---
globs: |-
  **/*.py
  **/*.md
  **/*.txt
description: Ensure that all aspects of the engine, including geometry,
  kinematics, physics, and intelligence, are accurately represented in the
  model.
alwaysApply: true
---

Create a detailed model of a physical engine (1.9 TDI) with high accuracy and completeness.
```

## .continue/rules/use-detailed-physics.md

- Typ: `DOC`; rozmiar: `240` B
- Linie pliku: `8`
- Poczatkowe linie (head):
```text
---
globs: "**/*.py"
description: Apply this rule when developing a detailed physics-based simulation
  to ensure accuracy and realism.
alwaysApply: true
---

Ensure that the model uses detailed physical equations and principles throughout.
```

## .continue/rules/use-named-exports.md

- Typ: `DOC`; rozmiar: `246` B
- Linie pliku: `8`
- Poczatkowe linie (head):
```text
---
globs: "**/*.js"
description: Ensure that all prop types are explicitly declared for better type
  safety and code maintainability in React components.
alwaysApply: false
---

Always use named exports when declaring React component properties
```

## .history-memo/2025-12-22.md

- Typ: `DOC`; rozmiar: `882` B
- Linie pliku: `64`
- Poczatkowe linie (head):
```text

# [21:06:19] - MAGUS Council → gemini

siema

Open files:
c:\Users\tucyk\.gemini\settings.json

# [21:06:47] - MAGUS Council → gemini

siema

Open files:
c:\Users\tucyk\.gemini\settings.json

# [21:07:14] - MAGUS Council → gemini

siema

# [21:06:19] - MAGUS Council → gemini

siema

Open files:
c:\Users\tucyk\.gemini\settings.json
```

## SMIETNIK/NA PODSTAWIE LISTY PODAJ WSZYSTKIE DANE KTORE MOŻ....md

- Typ: `DOC`; rozmiar: `5270` B
- Linie pliku: `113`
- Poczatkowe linie (head):
```text
# **BAZA DANYCH KONSTRUKCYJNYCH: 1.9 TDI (EA188 / VP37)**

## **🔧 1\. Układ tłokowo-korbowy**

* **Średnica cylindra (ø cylindra):** 79.50 mm (Nominał)  
* **Skok tłoka:** 95.50 mm  
* **Liczba cylindrów:** 4  
* **Rozstaw cylindrów (center-to-center):** 88.00 mm  
* **Średnica tłoka (ø):** 79.45 mm (Nominał dla cylindra 79.50)  
* **Wysokość tłoka (od osi sworznia do denka):** 45.80 mm (tzw. wysokość kompresyjna)  
* **Kształt denka tłoka:** Wklęsły, komora wirowa typu "Omega"  
* **Liczba pierścieni tłokowych:** 3 (1. Uszczelniający, 2\. Uszczelniająco-zgarniający, 3\. Zgarniający)  
* **Średnica sworznia tłokowego:** 26.00 mm  
* **Długość korbowodu (center-to-center):** 144.00 mm  
* **Masa korbowodu i tłoka:**  
* **Offset osi tłoka względem osi cylindra (Desaxage):** 0.5 mm

## **🔩 2\. Wał korbowy**

* **Średnica czopów głównych:** 54.00 mm  
* **Średnica czopów korbowodowych:** 47.80 mm  
* **Rozstaw czopów (kąt zapłonu):** 180° (Kolejność 1-3-4-2)  
* **Długość i kształt ramion:**  
* **Masa wału korbowego:**  
* **Promień wykorbienia (throw radius):** 47.75 mm  
```

## SMIETNIK/RAPORT_IMEP_I_KATALOG.md

- Typ: `DOC`; rozmiar: `5923` B
- Linie pliku: `102`
- Poczatkowe linie (head):
```text
# Raport: ujemny IMEP i katalog modulow

## 1) Problem z ujemnym momentem (IMEP < 0) - diagnoza

### Objawy z logu
- `out_heavy/metrics.txt` pokazal **ujemny IMEP** i **ujemny moment** mimo dawki ~35.4 mg/suw oraz boostu z mapy.
- Metryki `soc_*` i `ign_delay_*` wskazaly **zaplonnienie przesuniete o ~180 deg**, czyli spalanie po GMP i na suwie wydechu.

### Przyczyna
- To nie jest realne przesuniecie pompy o 180 deg, tylko **zbyt duze opoznienie zaplonu z modelu**.
- Opoznienie zaplonu na poziomie ~180 deg przesuwa SOC na suw wydechu.

### Konsekwencja
- Spalanie nastepuje **po GMP**, wiec calka `P * dV` staje sie ujemna -> **ujemny IMEP**.
- To nie jest blad map ECU, tylko **blad modelu zaplonu**.

### Zmiany diagnostyczne / naprawcze (juz w kodzie)
- **Zapisywanie SOC i opoznienia zaplonu** w metrykach:
  - `soc_pilot_deg_model`, `soc_main_deg_model`
  - `ign_delay_pilot_deg`, `ign_delay_main_deg`
  - `ign_delay_*_source` - wskazuje, czy wynik pochodzi z Arrheniusa czy `fixed_deg`.
- **Korekty ECU i warunki w cylindrze**:
  - korekty SOI od temperatur paliwa/cieczy, EGR, offset zaplonu,
  - udzial spalin resztkowych (`residual_frac`), EGR (`egr_frac`),
  - korekta temperatury ladunku (`charge_temp_offset_k`),
```

## SMIETNIK/kompletna_lista_z_danymi_SCALONA.md

- Typ: `DOC`; rozmiar: `7360` B
- Linie pliku: `155`
- Poczatkowe linie (head):
```text
﻿# 🔗 Scalona Lista: Dane Rozszerzone + Dane Producentów i Obliczenia

## 🧩 Sekcja 1: Dane Rozszerzone (źródłowe + podstawowe)

# **BAZA DANYCH KONSTRUKCYJNYCH: 1.9 TDI (EA188 / VP37)**

## **🔧 1\. Układ tłokowo-korbowy**

* **Średnica cylindra (ø cylindra):** 79.50 mm (Nominał)  
* **Skok tłoka:** 95.50 mm  
* **Liczba cylindrów:** 4  
* **Rozstaw cylindrów (center-to-center):** 88.00 mm  
* **Średnica tłoka (ø):** 79.45 mm (Nominał dla cylindra 79.50)  
* **Wysokość tłoka (od osi sworznia do denka):** 45.80 mm (tzw. wysokość kompresyjna)  
* **Kształt denka tłoka:** Wklęsły, komora wirowa typu "Omega"  
* **Liczba pierścieni tłokowych:** 3 (1. Uszczelniający, 2\. Uszczelniająco-zgarniający, 3\. Zgarniający)  
* **Średnica sworznia tłokowego:** 26.00 mm  
* **Długość korbowodu (center-to-center):** 144.00 mm  
* **Masa korbowodu i tłoka:**  
* **Offset osi tłoka względem osi cylindra (Desaxage):** 0.5 mm

## **🔩 2\. Wał korbowy**

* **Średnica czopów głównych:** 54.00 mm  
* **Średnica czopów korbowodowych:** 47.80 mm  
```

## SMIETNIK/kompletna_lista_z_danymi_rozszerzona.md

- Typ: `DOC`; rozmiar: `5955` B
- Linie pliku: `127`
- Poczatkowe linie (head):
```text
﻿# **BAZA DANYCH KONSTRUKCYJNYCH: 1.9 TDI (EA188 / VP37)**

## **🔧 1\. Układ tłokowo-korbowy**

* **Średnica cylindra (ø cylindra):** 79.50 mm (Nominał)  
* **Skok tłoka:** 95.50 mm  
* **Liczba cylindrów:** 4  
* **Rozstaw cylindrów (center-to-center):** 88.00 mm  
* **Średnica tłoka (ø):** 79.45 mm (Nominał dla cylindra 79.50)  
* **Wysokość tłoka (od osi sworznia do denka):** 45.80 mm (tzw. wysokość kompresyjna)  
* **Kształt denka tłoka:** Wklęsły, komora wirowa typu "Omega"  
* **Liczba pierścieni tłokowych:** 3 (1. Uszczelniający, 2\. Uszczelniająco-zgarniający, 3\. Zgarniający)  
* **Średnica sworznia tłokowego:** 26.00 mm  
* **Długość korbowodu (center-to-center):** 144.00 mm  
* **Masa korbowodu i tłoka:**  
* **Offset osi tłoka względem osi cylindra (Desaxage):** 0.5 mm

## **🔩 2\. Wał korbowy**

* **Średnica czopów głównych:** 54.00 mm  
* **Średnica czopów korbowodowych:** 47.80 mm  
* **Rozstaw czopów (kąt zapłonu):** 180° (Kolejność 1-3-4-2)  
* **Długość i kształt ramion:**  
* **Masa wału korbowego:**  
* **Promień wykorbienia (throw radius):** 47.75 mm  
```

## SMIETNIK/kompletna_lista_z_danymi_rozszerzona_pelna.md

- Typ: `DOC`; rozmiar: `1221` B
- Linie pliku: `24`
- Poczatkowe linie (head):
```text

## 🧮 Dane pochodne + dane producentów

| Parametr | Wartość | Pochodzenie |
|----------|---------|-------------|
| Powierzchnia denka tłoka | 0.004964 m² | 🧮 wyliczenie z bore |
| Objętość cylindra | 474.05 cm³ | 🧮 πr²·h |
| Objętość komory spalania (V₀) | 25.62 cm³ | 🧮 z CR |
| Objętość martwa | 25.62 cm³ | 🧮 = V₀ |
| Powierzchnia głowicy nad tłokiem | 0.004964 m² | 🧮 wyliczenie z bore |
| Średnia prędkość tłoka | 4.78 m/s | 🧮 2×stroke×RPM/60 |
| Czas trwania 1 obrotu wału | 0.0400 s | 🧮 60 / RPM |
| Maks. przyspieszenie tłoka | 1178.18 m/s² | 🧮 ω²×r |
| Maks. siła bezwładności tłoka | 518.40 N | 🧮 m×a |
| Masa tłoka | 440 g | 🧪DAT: Mahle 030 107 065 |
| Masa sworznia | 120 g | 🧪DAT: Mahle 030 107 065 |
| Masa pierścieni | 40 g | 🧪DAT: Mahle 030 107 065 |
| Długość korbowodu | 144 mm | 🧪DAT: Mahle TDI |
| Średnica sworznia tłoka | 20 mm | 🧪DAT: Mahle 030 107 065 |
| Długość sworznia | 58 mm | 🧪DAT: Mahle 030 107 065 |
| Masa zaworu | 100 g | 🧪DAT: INA 030 109 611 |
| Skok zaworu max | 9 mm | 🧪DAT: INA 030 109 611 |
| Sztywność sprężyn zaworowych | 30–40 N/mm | 🧪DAT: INA 030 109 623 |
```

## SMIETNIK/output.png

- Typ: `GENERATED`; rozmiar: `346051` B

## SMIETNIK/specs_with_sources.md

- Typ: `DOC`; rozmiar: `6649` B
- Linie pliku: `110`
- Poczatkowe linie (head):
```text

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
```

## SMIETNIK/tabela_danych_pochodnych_i_bezposrednich.md

- Typ: `DOC`; rozmiar: `584` B
- Linie pliku: `11`
- Poczatkowe linie (head):
```text
### 📊 Tabela pełna – dane bezpośrednie i pochodne (obliczalne)

| Parametr | Wartość | Źródło |
|---|---|---|
| Powierzchnia denka tłoka (A_piston) | 0.00496 m² | 🧮 calculated from bore |
| Objętość cylindra (V_s) | 474.05 cm³ | 🧮 V = πr²h |
| Objętość komory spalania (V₀) | 25.62 cm³ | 🧮 V₀ = V / (CR - 1) |
| Objętość martwa | 25.62 cm³ | 🧮 equal to V₀ |
| Powierzchnia tulei odsłoniętej | 0.02385 m² | 🧮 π·d·h (bore, stroke) |
| Powierzchnia całkowita wymiany ciepła | 0.02882 m² | 🧮 A_piston + A_liner (uproszczone) |
```

## SMIETNIK/uzupelniona_lista_z_danymi_i_zrodlami.md

- Typ: `DOC`; rozmiar: `5270` B
- Linie pliku: `113`
- Poczatkowe linie (head):
```text
# **BAZA DANYCH KONSTRUKCYJNYCH: 1.9 TDI (EA188 / VP37)**

## **🔧 1\. Układ tłokowo-korbowy**

* **Średnica cylindra (ø cylindra):** 79.50 mm (Nominał)  
* **Skok tłoka:** 95.50 mm  
* **Liczba cylindrów:** 4  
* **Rozstaw cylindrów (center-to-center):** 88.00 mm  
* **Średnica tłoka (ø):** 79.45 mm (Nominał dla cylindra 79.50)  
* **Wysokość tłoka (od osi sworznia do denka):** 45.80 mm (tzw. wysokość kompresyjna)  
* **Kształt denka tłoka:** Wklęsły, komora wirowa typu "Omega"  
* **Liczba pierścieni tłokowych:** 3 (1. Uszczelniający, 2\. Uszczelniająco-zgarniający, 3\. Zgarniający)  
* **Średnica sworznia tłokowego:** 26.00 mm  
* **Długość korbowodu (center-to-center):** 144.00 mm  
* **Masa korbowodu i tłoka:**  
* **Offset osi tłoka względem osi cylindra (Desaxage):** 0.5 mm

## **🔩 2\. Wał korbowy**

* **Średnica czopów głównych:** 54.00 mm  
* **Średnica czopów korbowodowych:** 47.80 mm  
* **Rozstaw czopów (kąt zapłonu):** 180° (Kolejność 1-3-4-2)  
* **Długość i kształt ramion:**  
* **Masa wału korbowego:**  
* **Promień wykorbienia (throw radius):** 47.75 mm  
```

## data/synthetic.csv

- Typ: `DATA`; rozmiar: `2983351` B
- Separator: `,`; wiersze: `5001`
- Naglowek + pierwsze wiersze:
```text
idx,rpm,fuel,hw_nozzle_holes,hw_nozzle_diameter_mm,hw_vp37_camplate,hw_vp37_cam_profile_file,hw_valvetrain_profile_file,soi_offset_deg,iq_cmd_mg_per_str,iq_eff_mg_per_str,n146_mv,maf_target_mg_per_str,smoke_iq_max_mg_per_str,boost_target_mbar_abs,p_intake_bar_used,soi_main_deg_model,duration_main_deg,out_peak_pressure_bar,out_peak_temp_k,out_imep_bar,out_indicated_torque_nm,out_brake_torque_nm_est,out_brake_power_kw_est,out_mass_start_kg_per_cyl,out_mass_end_kg_per_cyl,out_fuel_energy_in_j_per_cyl,out_q_comb_j_per_cyl,out_q_wall_j_per_cyl,out_q_exhaust_out_j_per_cyl_est,out_torque_ind_mean_nm_per_cyl,out_torque_ind_pp_nm_per_cyl,out_torque_ind_ripple_rms_nm_per_cyl,out_rod_force_max_comp_n_est,out_rod_force_max_tens_n_est,out_bsfc_g_per_kwh_est
0,1500.0,svo,5,0.184,DE110,skok_tloczka_vp37_de110.csv,profil_krzywek_4cylindry.md,-2.135042323682198,42.79192622690149,42.79192622690149,,797.1947253930662,37.03571428571428,1724.6287494127325,1.2494651616083883,-8.135042323682198,54.71323224492421,63.92649562420481,1924.8929239651911,12.52299925818043,188.96701047186676,173.87741359686675,27.31260025905553,3.718577025463235e-05,1.3875103193070308e-05,1583.301270395355,1532.4991513120947,6.808347464355627,1403.1397640913406,47.17915559286335,1040.126252587715,192.96970612552866,30587.470461267632,536.9478077516466,282.0144053581452
1,1500.0,svo,5,0.184,DE110,skok_tloczka_vp37_de110.csv,profil_krzywek_4cylindry.md,1.9662155629226508,19.595562863873933,19.595562863873933,,499.5048498455161,28.821878579033037,1116.1921834077364,1.4396749501384476,-4.033784437077349,20.681974219610822,73.65843890971666,1349.0665159923456,8.056438752950918,121.56841303015707,106.47881615515708,16.725653329798984,4.2846670385177854e-05,2.5633617357965388e-05,725.0358259633355,689.3589560939524,3.0420570284829616,623.6848348946979,30.35193035229914,1127.5864300238582,181.03258943003033,35418.32218941202,479.69146945647435,210.8857122617224
2,1500.0,svo,5,0.184,DE110,skok_tloczka_vp37_de110.csv,profil_krzywek_4cylindry.md,0.2288598793156691,16.178463809460965,16.178463809460965,,450.4000421757037,26.979296677726747,1074.9673241012829,1.6307429627427235,-5.771140120684331,16.803417133745292,84.16332213378584,1218.255570358703,7.063886822454169,106.59120452145811,91.50160764645811,14.373038918688422,4.8533112422958087e-05,3.275157545149495e-05,598.6031609500557,592.7919133374767,2.364771928171629,557.8814725780635,26.61255237192638,1218.2975987511502,188.00573528869467,40681.05300527208,454.87009174232924,202.61014404660864
3,1500.0,svo,5,0.184,DE110,skok_tloczka_vp37_de110.csv,profil_krzywek_4cylindry.md,-0.27901266311609074,7.763792981628084,7.763792981628084,,307.43565488911696,20.376964560631706,1002.2772783207724,1.3224903891577033,-6.279012663116091,7.800556957411523,67.66276517543204,1036.9958687544258,3.524611687773284,53.18496950941222,38.09537263441222,5.984007140201753,3.9359099626173624e-05,2.8274531760075793e-05,287.2603403202391,288.0379073035401,1.1805896603765622,369.5884061677377,13.278606839476192,875.4840551321582,135.71349802627682,32442.12206463546,495.92121563555634,233.53627493264293
4,1500.0,svo,5,0.184,DE110,skok_tloczka_vp37_de110.csv,profil_krzywek_4cylindry.md,1.502188035780316,14.057576593399716,14.057576593399716,,412.6691449219952,25.92702124104687,1049.743840930061,1.3881527795453081,-4.497811964219684,14.46762644332977,71.02233508144295,1242.222571323236,6.024724066534375,90.9106574471144,75.8210605721144,11.909944344037067,4.1313301022377695e-05,2.6586323101746725e-05,520.1303339557895,526.7538460637659,2.162238827436702,492.94521443662643,22.697607605127292,1050.1487345719318,161.47011565576773,34109.78325111566,478.63566555781995,212.45806980440025
5,1500.0,diesel,5,0.184,DE110,skok_tloczka_vp37_de110.csv,profil_krzywek_4cylindry.md,2.76994316198272,33.16596745326194,33.16596745326194,,735.2677239493186,36.986255930401285,1502.2652904465126,1.4329814844379474,-3.23005683801728,38.1663769190397,104.15056140677333,1762.9502017298812,14.450343708884997,218.049861272267,202.96026439726697,31.8809237800548,4.264746380832088e-05,2.117691909881945e-05,1409.5536167636326,1406.5479577952426,6.421190652497855,1074.598074199273,54.440514018352296,1284.7127113972822,231.88924839816892,50568.29313827998,498.21826106638946,187.2553688460557
6,1500.0,svo,5,0.184,DE110,skok_tloczka_vp37_de110.csv,profil_krzywek_4cylindry.md,2.819552479296796,24.190949178558785,24.190949178558785,,575.9940049232491,33.523926009680665,1194.323233142381,1.0926924899766162,-3.180447520703204,26.16781627703667,55.88399340455376,1661.2018141079338,8.668160180494269,130.79904277158576,115.70944589658578,18.175597258982975,3.252000387023822e-05,1.2156567855798227e-05,895.065119606675,871.439624081913,4.094736595384368,720.6811419730702,32.65654810919583,922.458058892461,159.11374746728956,26595.24253652764,599.2032209501076,239.57236673411148
```

## docs/BASELINE_MAPY_ECU_I_OSPRZET.md

- Typ: `DOC`; rozmiar: `2464` B
- Linie pliku: `43`
- Poczatkowe linie (head):
```text
# Bazowa konfiguracja (mapy ECU i osprzęt)

Ten projekt używa kilku map ECU (SOI, N146, SmokeLimiter, EGR, Boost). Te mapy są “fabryczne”, ale **nie są uniwersalne** – zakładają konkretną konfigurację hardware.

## Mapy w repo

- `Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv`
  - Oś: `RPM × IQ (mg/suw)` → SOI (stopnie BTDC w pliku; w modelu konwertowane na konwencję: BTDC = wartości ujemne).
- `Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv`
  - Oś: `RPM × IQ (mg/suw)` → `N146 (mV)`.
- `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv`
  - Oś: `RPM × MAF (mg/suw)` → `max IQ (mg/suw)`.
- `Mapa_EGR___interpolowana_mapa_MAF.csv`
  - Oś: `RPM × IQ (mg/suw)` → `MAF target (mg/suw)`.
- `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv`
  - Oś: `RPM × IQ (mg/suw)` → `MAP target (mbar abs)`.

## Bazowa konfiguracja, dla której mapy są sensowne

- Wtryskiwacze: końcówka `0.184 × 5` (ALH 90hp).
- Pompa VP37: krzywka/tarcza `DE110`:
  - profil skoku tłoczka: `skok_tloczka_vp37_de110.csv`
- Rozrząd / wznios zaworów:
  - tabela wzniosu: `profil_krzywek_4cylindry.md`

```

## docs/CHECKLIST_CYFROWY_DUCH.md

- Typ: `DOC`; rozmiar: `2230` B
- Linie pliku: `45`
- Poczatkowe linie (head):
```text
# Checklist: zgodnosc z manifestem "Cyfrowy Duch"

Ten plik sluzy jako lista kontrolna dopasowania kodu do manifestu.
Full-chem nie jest wymagany.

## Warstwa 1: geometria i kinematyka
- [ ] `virtual_tdi/geometry.py`: dane bazowe z `engine_reference_sources.yaml`
- [ ] `virtual_tdi/valvetrain.py`: parametry zaworow zrodlowe + testy zakresow
- [ ] `virtual_tdi/lift_table.py`: walidacja profilu z `profil_krzywek*.md`
- [ ] `virtual_tdi/vp37_cam.py`: walidacja profilu z `skok_tloczka_vp37_de110.csv`
- [ ] Testy regresyjne V(theta), dV/dtheta, lift i kinematyki

## Warstwa 2: fizyka (bez full-chem)
- [ ] `virtual_tdi/thermo.py`: spis ograniczen modelu i plan mieszanin
- [ ] `virtual_tdi/full_cycle.py`: bilans masy/energii z uwzglednieniem kolektorow
- [ ] `virtual_tdi/flow.py`: przeplyw z korektami strat, zrodla parametrow
- [ ] `virtual_tdi/heat_transfer.py`: model scian (denko/tuleja/glowica)
- [ ] Testy trendow IMEP/EGT/BSFC po zmianach

## Warstwa 2b: hydraulika i wtrysk
- [ ] `virtual_tdi/hydraulics.py`: fala cisnienia w przewodzie
- [ ] `virtual_tdi/vp37.py`: dynamika iglicy i wielofazowy wtrysk
- [ ] `virtual_tdi/combustion.py`: zaplon zasilany profilem wtrysku z hydrauliki

## Warstwa 3: inteligencja (ECU)
```

## docs/PARAMETRY_SILNIKA.md

- Typ: `DOC`; rozmiar: `5633` B
- Linie pliku: `100`
- Poczatkowe linie (head):
```text
# Katalog Parametrów Fizycznych i Geometrycznych Silnika 1.9 TDI

Ten dokument stanowi centralne repozytorium dla wszystkich kluczowych parametrów silnika wykorzystywanych w symulatorze "Wirtualny Klon". Jego celem jest spełnienie pierwszego kamienia milowego (M1) z roadmapy projektu: **stworzenie kompletnego katalogu parametrów, ich pochodzenia i jednostek**.

Każdy parametr musi mieć jawnie określone źródło, aby uniknąć "magicznych" wartości i zapewnić zgodność z manifestem "Cyfrowego Ducha".

## 1. Układ Korbowo-Tłokowy (Cranktrain)

Podstawowe wymiary definiujące kinematykę i objętość roboczą silnika.

| Parametr | Wartość | Jednostka | Źródło / Opis |
|---|---|---|---|
| Oznaczenie silnika bazowego | VW 1.9 TDI (ALH/EA827) | - | VW SSP 198 |
| Średnica cylindra (bore) | 79.5 | mm | VW SSP 198, ETKA |
| Skok tłoka (stroke) | 95.5 | mm | VW SSP 198, ETKA |
| Długość korbowodu | 144.0 | mm | ETKA, Mahle Datasheet |
| Promień wykorbienia | 47.75 | mm | 🧮 Obliczone (`stroke / 2`) |
| Odsadzenie osi cylindra (desaxage) | 0.5 | mm | CAD models EA827, `SMIETNIK/kompletna_lista_z_danymi_SCALONA.md` |
| Rozstaw cylindrów | 88.0 | mm | `SMIETNIK/kompletna_lista_z_danymi_rozszerzona.md` |
| Wysokość kompresyjna tłoka | 45.80 | mm | `SMIETNIK/kompletna_lista_z_danymi_rozszerzona.md` |
| Średnica sworznia tłokowego | 26.00 | mm | `SMIETNIK/kompletna_lista_z_danymi_rozszerzona.md` |

## 2. Komora Spalania i Stopień Sprężania

Parametry definiujące objętość termodynamiczną.
```

## docs/RAPORT_CR_VC.md

- Typ: `DOC`; rozmiar: `1445` B
- Linie pliku: `38`
- Poczatkowe linie (head):
```text
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

```

## docs/ROADMAP_CYFROWY_DUCH.md

- Typ: `DOC`; rozmiar: `3231` B
- Linie pliku: `78`
- Poczatkowe linie (head):
```text
# Roadmap: dopasowanie projektu do manifestu "Cyfrowy Duch"

Ten dokument spisuje rozbieznosci i kolejnosc prac tak, aby projekt byl zgodny z manifestem.
Pelna kinetyka chemiczna (full-chem) nie jest wymagana na tym etapie.

## 1) Rozbieznosci vs manifest (stan obecny)
- Geometria/kinematyka: czesc danych ma wartosci domyslne, nie wszystkie maja twarde zrodla pomiarowe.
- Gazowymiana: przeplyw przez zawory jako oryficz 0D, brak modeli kolektorow i fal cisnienia.
- Termodynamika: idealny gaz + opcjonalny CoolProp, ale bez mieszanin spalin/paliwa.
- Wymiana ciepla: korelacja Woschni (uproszczona, empiryczna).
- Hydraulika wtrysku: uproszczone modele VP37 i przewodu, brak dynamiki iglicy i fal cisnienia.
- Turbo: prosty bilans mocy bez map sprzezarki/turbiny i bez dynamiki.
- ECU: mapy i proste reguly, brak modelu percepcji (czujniki, opoznienia, filtry).
- Dane i parametry: czesc "magicznych" wartosci bez jawnego zrodla.

## 1.1) Zrodla danych w repo (start)
- `engine_reference_sources.yaml` (parametry bazowe + zrodla)
- `docs/BASELINE_MAPY_ECU_I_OSPRZET.md` (mapy ECU i ich zakres)
- Mapy ECU (wzorce nazw):
  - `Mapa*SOI*Table 1.csv`
  - `Mapa*N146*Table 1.csv`
  - `SmokeLimiter*.csv`
  - `Mapa_EGR*.csv`
  - `Mapa_BOOST*.csv`
- Profil rozrzadu: `profil_krzywek*.md`
```

## src/main.py

- Typ: `CODE`; rozmiar: `0` B
- Linie pliku: `1`

## tests/test_backends.py

- Typ: `CODE`; rozmiar: `1225` B
- Linie pliku: `44`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.flow import orifice_mdot_kg_per_s`
  - `from virtual_tdi.models import SimulationConfig`
  - `from virtual_tdi.thermo import GasModel`
- API (definicje top-level):
  - `def _has_module()`
  - `class TestBackendFallbacks` (metody: test_flow_backend_fluids_fallback, test_thermo_backend_coolprop_fallback)
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L27:             gamma=1.35,
L39:         g = GasModel().gamma(600.0, cfg, pressure_pa=1.0e5)
```

## tests/test_config_loader.py

- Typ: `CODE`; rozmiar: `3702` B
- Linie pliku: `80`
- Zaleznosci (importy):
  - `pytest`
  - `from pathlib import Path`
  - `from virtual_tdi.config_loader import load_yaml_config, create_geometry_from_config, create_manifold_configs_from_config, create_intercooler_config_from_config, create_valve_flow_from_config`
  - `from virtual_tdi.models import EngineGeometry, ManifoldConfig, IntercoolerConfig`
  - `from virtual_tdi.valvetrain import ValveFlow`
- API (definicje top-level):
  - `def engine_config()` - Loads the engine reference config once for all tests.
  - `def test_config_file_exists()` - Ensures the engine_reference_sources.yaml file exists.
  - `def test_load_yaml_config_valid()` - Tests if the YAML config can be loaded successfully.
  - `def test_create_geometry_from_config_valid()` - Tests if EngineGeometry can be created successfully from the config.
  - `def test_create_manifold_configs_from_config_valid()` - Tests if ManifoldConfig objects can be created successfully.
  - `def test_create_intercooler_config_from_config_valid()` - Tests if IntercoolerConfig can be created successfully.
  - `def test_create_valve_flow_from_config_valid()` - Tests if ValveFlow can be created successfully.
  - `def test_create_geometry_missing_key_raises_error()` - Tests that a KeyError is raised for missing geometry parameters.
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `Ensures the engine_reference_sources.yaml`
  - `engine_reference_sources.yaml`

## tests/test_controller.py

- Typ: `CODE`; rozmiar: `638` B
- Linie pliku: `21`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.controller import solve_monotone_bisect`
- API (definicje top-level):
  - `class TestController` (metody: test_bisect_increasing, test_bisect_decreasing)

## tests/test_dataset.py

- Typ: `CODE`; rozmiar: `855` B
- Linie pliku: `31`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.dataset import DatasetConfig, generate_dataset`
- API (definicje top-level):
  - `class TestDataset` (metody: test_generate_small_dataset)
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L20:             integrator="rk4",
```

## tests/test_dataset_config.py

- Typ: `CODE`; rozmiar: `2397` B
- Linie pliku: `74`
- Zaleznosci (importy):
  - `unittest`
  - `from pathlib import Path`
  - `yaml`
  - `os`
  - `csv`
  - `from virtual_tdi.dataset import main`
- API (definicje top-level):
  - `class TestDatasetConfig` (metody: setUp, tearDown, test_dataset_generation_with_custom_config)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `test_engine_config.yaml`
  - `test_output.csv`

## tests/test_edc_maps.py

- Typ: `CODE`; rozmiar: `1102` B
- Linie pliku: `27`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.edc_maps import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D`
- API (definicje top-level):
  - `class TestEDCMaps` (metody: test_smoke_limiter, test_egr_maf_target, test_boost_target)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv`
  - `Mapa_EGR___interpolowana_mapa_MAF.csv`
  - `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv`

## tests/test_full_cycle_dynamic_manifolds.py

- Typ: `CODE`; rozmiar: `4302` B
- Linie pliku: `94`
- Zaleznosci (importy):
  - `unittest`
  - `from pathlib import Path`
  - `numpy`
  - `from virtual_tdi.config_loader import create_geometry_from_config, load_yaml_config, create_manifold_configs_from_config`
  - `from virtual_tdi.full_cycle import FullCycleConfig, simulate_full_cycle`
  - `from virtual_tdi.models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig, ManifoldConfig`
  - `from virtual_tdi.valvetrain import ValveFlow, ValveTiming`
  - `from virtual_tdi.lift_table import ValveLiftTable`
- API (definicje top-level):
  - `class TestFullCycleDynamicManifolds` (metody: setUp, test_simulation_runs_and_produces_plausible_results)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `engine_reference_sources.yaml`
  - `profil_krzywek_4cylindry.md`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L42:         models = SimulationConfig(rpm=1500.0, integrator='rk4', step_deg=1.0)
```

## tests/test_full_cycle_sanity.py

- Typ: `CODE`; rozmiar: `1791` B
- Linie pliku: `54`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle`
  - `from virtual_tdi.models import EngineGeometry, Fuel, InjectionSchedule, SimulationConfig`
  - `from virtual_tdi.valvetrain import ValveTiming`
- API (definicje top-level):
  - `class TestFullCycleSanity` (metody: test_runs_and_positive_imep)

## tests/test_full_cycle_vp37_hrr.py

- Typ: `CODE`; rozmiar: `1888` B
- Linie pliku: `55`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle`
  - `from virtual_tdi.models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig`
  - `from virtual_tdi.vp37_cam import VP37CamProfile`
- API (definicje top-level):
  - `class TestFullCycleVP37HRR` (metody: test_runs_with_vp37_main_hrr)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `skok_tloczka_vp37_de110.csv`

## tests/test_geometry.py

- Typ: `CODE`; rozmiar: `4553` B
- Linie pliku: `109`
- Zaleznosci (importy):
  - `math`
  - `unittest`
  - `from virtual_tdi.config_loader import create_geometry_from_config, load_yaml_config`
  - `from virtual_tdi.geometry import cylinder_volume_m3, piston_position_derivative_ds_dtheta`
  - `from virtual_tdi.models import EngineGeometry`
- API (definicje top-level):
  - `class TestGeometry` (metody: setUp, test_volume_at_theta_zero_and_pi, test_derivative_at_true_dead_centers, test_volume_and_derivative_at_intermediate_points)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `engine_reference_sources.yaml`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L18:         Tests if the volume at theta=0 and theta=pi matches the geometry
L26:         v_at_pi, _, _ = cylinder_volume_m3(self.geom, math.pi)
L36:         These points are NOT at 0 and pi radians when there is an offset.
L65:         theta_tdc = find_root(ds_dtheta, -math.pi / 2.0, math.pi / 2.0)
L69:         theta_bdc = find_root(ds_dtheta, math.pi / 2.0, 3.0 * math.pi / 2.0)
L78:         theta = math.pi / 2.0  # 90 degrees
L89:         u_90 = r * math.sin(theta) - delta
L90:         s_90 = r * math.cos(theta) + math.sqrt(L**2 - u_90**2)
L92:         s_0 = r * math.cos(0) + math.sqrt(L**2 - (r * math.sin(0) - delta)**2)
L97:         denom_90 = math.sqrt(L**2 - u_90**2)
L98:         ds_dtheta_90 = -r * math.sin(theta) - (u_90 * r * math.cos(theta)) / denom_90
```

## tests/test_hydraulics.py

- Typ: `CODE`; rozmiar: `1385` B
- Linie pliku: `47`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.hydraulics import NozzleConfig, VP37HydraulicConfig, estimate_pilot_ratio`
  - `from virtual_tdi.models import Fuel`
  - `from virtual_tdi.vp37_cam import VP37CamProfile`
- API (definicje top-level):
  - `class TestHydraulics` (metody: test_pilot_ratio_bounds, test_pilot_ratio_zero_duration)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `skok_tloczka_vp37_de110.csv`

## tests/test_lift_table.py

- Typ: `CODE`; rozmiar: `4566` B
- Linie pliku: `100`
- Zaleznosci (importy):
  - `unittest`
  - `numpy`
  - `from virtual_tdi.lift_table import ValveLiftTable`
- API (definicje top-level):
  - `class TestLiftTable` (metody: setUpClass, test_max_lift_matches_profile_data, test_interpolation_mid_point, test_periodicity, test_valve_timing_open_close)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `profil_krzywek_4cylindry.md`

## tests/test_n146_map.py

- Typ: `CODE`; rozmiar: `877` B
- Linie pliku: `26`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.n146_map import N146VoltageMap2D`
- API (definicje top-level):
  - `class TestN146Map` (metody: test_parse_and_forward, test_inverse)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv`

## tests/test_soi_map.py

- Typ: `CODE`; rozmiar: `764` B
- Linie pliku: `24`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.soi_map import SOIMap2D`
- API (definicje top-level):
  - `class TestSOIMap` (metody: test_parses_and_interpolates)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv`

## tests/test_solver_sanity.py

- Typ: `CODE`; rozmiar: `1288` B
- Linie pliku: `43`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.models import EngineGeometry, Fuel, InjectionSchedule, SimulationConfig`
  - `from virtual_tdi.solver import simulate_closed_cycle`
- API (definicje top-level):
  - `class TestSolverSanity` (metody: test_runs_and_outputs_metrics)

## tests/test_turbo_coupled.py

- Typ: `CODE`; rozmiar: `1843` B
- Linie pliku: `52`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.coupled import simulate_coupled_turbo`
  - `from virtual_tdi.full_cycle import BoundaryConditions, FullCycleConfig`
  - `from virtual_tdi.models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig`
  - `from virtual_tdi.turbo import TurboConfig`
- API (definicje top-level):
  - `class TestTurboCoupled` (metody: test_runs)
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L38:                 combustion=CombustionConfig(hrr_model="wiebe"),
```

## tests/test_valvetrain.py

- Typ: `CODE`; rozmiar: `560` B
- Linie pliku: `18`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.valvetrain import valve_lift_fraction`
- API (definicje top-level):
  - `class TestValveTrain` (metody: test_lift_fraction_basic)

## tests/test_vp37_cam.py

- Typ: `CODE`; rozmiar: `763` B
- Linie pliku: `21`
- Zaleznosci (importy):
  - `unittest`
  - `from virtual_tdi.vp37_cam import VP37CamProfile`
- API (definicje top-level):
  - `class TestVP37Cam` (metody: test_duration_monotone)
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `skok_tloczka_vp37_de110.csv`

## virtual_tdi/__init__.py

- Typ: `CODE`; rozmiar: `1644` B
- Opis modulu (docstring): Virtual 1.9 TDI ("cyfrowy duch") - white-box engine cycle simulator.
- Linie pliku: `52`
- Zaleznosci (importy):
  - `from coupled import CoupledResult, simulate_coupled_turbo`
  - `from full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle`
  - `from edc_maps import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D`
  - `from hydraulics import NozzleConfig, VP37HydraulicConfig, estimate_pilot_ratio`
  - `from lift_table import ValveLiftTable`
  - `from models import EngineGeometry, EngineState, Fuel, InjectionSchedule, SimulationConfig`
  - `from n146_map import N146VoltageMap2D`
  - `from soi_map import SOIMap2D`
  - `from solver import simulate_closed_cycle`
  - `from valvetrain import ValveFlow, ValveTiming`
  - `from vp37 import VP37LineModel, apply_hydraulic_delay`
  - `from vp37_cam import VP37CamProfile`
  - `from dataset import DatasetConfig, generate_dataset`
  - `from turbo import TurboConfig`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: combustion + expansion) integrated in crank angle domain with RK4.
```

## virtual_tdi/__main__.py

- Typ: `CODE`; rozmiar: `394` B
- Linie pliku: `14`
- Zaleznosci (importy):
  - `sys`
  - `from cli import main`
  - `from dataset import main`
  - `from gui import main`

## virtual_tdi/cli.py

- Typ: `CODE`; rozmiar: `31634` B
- Linie pliku: `675`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `argparse`
  - `csv`
  - `sys`
  - `from pathlib import Path`
  - `numpy`
  - `from config_loader import create_geometry_from_config, load_yaml_config, create_manifold_configs_from_config, create_valve_flow_from_config`
  - `from controller import solve_monotone_bisect`
  - `from coupled import simulate_coupled_turbo`
  - `from edc_maps import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D`
  - `from full_cycle import FullCycleConfig, simulate_full_cycle`
  - `from hydraulics import NozzleConfig, VP37HydraulicConfig, NeedleConfig, estimate_pilot_ratio`
  - `from injection import InjectionLineConfig, solve_injection_hydraulics`
  - `from lift_table import ValveLiftTable`
  - `from models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig, ManifoldConfig`
  - `from n146_map import N146VoltageMap2D`
  - `from soi_map import SOIMap2D`
  - `from solver import simulate_closed_cycle`
  - `from turbo import TurboConfig`
  - `from valvetrain import ValveFlow, ValveTiming`
  - `from vp37 import VP37LineModel, apply_hydraulic_delay`
  - `from vp37_cam import VP37CamProfile`
- Uzywany przez (reverse-import):
  - `virtual_tdi/__main__.py`
- API (definicje top-level):
  - `def load_geometry_from_yaml()` - Helper to load the YAML config and create an EngineGeometry instance.
  - `def _default_schedule()`
  - `def _make_argparser()`
  - `def _fmt_value()`
  - `def _write_csv()`
  - `def _plot()`
  - `def main()`
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `_fmt_value(result.md`
  - `inj_res.md`
  - `writes soi_sweep.csv`
  - `Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv`
  - `Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv`
  - `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv`
  - `Mapa_EGR___interpolowana_mapa_MAF.csv`
  - `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv`
  - `Table 1.csv`
  - `cycle.csv`
  - `engine_reference_sources.yaml`
  - `heat.png`
  - `mass.png`
  - `p_t.png`
  - `profil_krzywek_4cylindry.md`
  - `pv.png`
  - `skok_tloczka_vp37_de110.csv`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L175:         choices=["auto", "wiebe", "vp37_main", "hydraulic_profile"],
L189:         help="Thermo properties backend for cp/cv/gamma.",
L195:         help="Flow model backend for orifice mass flow.",
L209:     p.add_argument("--integrator", choices=["rk4", "scipy"], default="rk4") # Changed default to rk4
L285:                     "heat_transfer_area_m2", "gamma",
L298:                         _fmt_value(result.gamma[i]),
L577:             if hrr_model == "auto": hrr_model = "vp37_main" if cam else "wiebe"
L606:                 omega_crank = args.rpm * 2.0 * pi / 60.0
L608:                 soi_main_rad = schedule.soi_main_deg * (pi/180.0)
```

## virtual_tdi/combustion.py

- Typ: `CODE`; rozmiar: `5414` B
- Linie pliku: `179`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import exp`
  - `numpy`
  - `from models import CombustionConfig, Fuel, InjectionSchedule, SimulationConfig`
  - `from thermo import ignition_delay_seconds_arrhenius, omega_rad_per_s`
- Uzywany przez (reverse-import):
  - `virtual_tdi/full_cycle.py`
  - `virtual_tdi/solver.py`
- API (definicje top-level):
  - `class CombustionScheduleRuntime`
  - `def wiebe_dxb_dtheta()`
  - `def heat_release_rate_wiebe_single()`
  - `def mass_rate_shaped()` - Shaped mass rate dm/dθ in kg/rad.
  - `def heat_release_rate_from_shaped_fuel()`
  - `def heat_release_rate_dq_dtheta()` - Calculates the heat release rate dQ/d(theta) in J/rad based on the configured model.
  - `def maybe_arm_combustion()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import exp
L28:     return (a * (m + 1.0) / duration_rad) * (y**m) * exp(-a * (y ** (m + 1.0)))
L63:     wu = float(np.interp(float(x), u, w))
L81:     wu = float(np.interp(float(x), u, w))
L112:         dm_fuel_dtheta = float(np.interp(source_theta, profile_theta_rad, profile_dmdtheta_kg_rad, left=0.0, right=0.0))
```

## virtual_tdi/config_loader.py

- Typ: `CODE`; rozmiar: `6873` B
- Linie pliku: `147`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from pathlib import Path`
  - `from typing import Any`
  - `from math import pi`
  - `yaml`
  - `from models import EngineGeometry, ManifoldConfig, IntercoolerConfig, N146ActuatorConfig`
  - `from valvetrain import ValveFlow`
- Uzywany przez (reverse-import):
  - `tests/test_config_loader.py`
  - `tests/test_full_cycle_dynamic_manifolds.py`
  - `tests/test_geometry.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
- API (definicje top-level):
  - `def load_yaml_config()` - Loads a YAML file and returns its content as a dictionary.
  - `def _get_param_value()`
  - `def _parse_compression_ratio()`
  - `def create_geometry_from_config()` - Creates an EngineGeometry object from a loaded YAML config dictionary.
  - `def create_manifold_configs_from_config()` - Creates ManifoldConfig objects from a loaded YAML config dictionary.
  - `def create_intercooler_config_from_config()` - Creates an IntercoolerConfig object from a loaded YAML config dictionary.
  - `def create_n146_actuator_config_from_config()` - Creates an N146ActuatorConfig object from a loaded YAML config dictionary.
  - `def create_valve_flow_from_config()` - Creates a ValveFlow object from a loaded YAML config dictionary.
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L5: from math import pi
L61:                 area_mm2 = (pi / 4.0) * (bore_mm ** 2)
```

## virtual_tdi/controller.py

- Typ: `CODE`; rozmiar: `1538` B
- Linie pliku: `61`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
- Uzywany przez (reverse-import):
  - `tests/test_controller.py`
  - `virtual_tdi/cli.py`
- API (definicje top-level):
  - `class SolveResult`
  - `def solve_monotone_bisect()` - Bisection for monotone function f(x) approximating f(x)=target.

## virtual_tdi/coupled.py

- Typ: `CODE`; rozmiar: `3915` B
- Linie pliku: `104`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from typing import Any`
  - `from full_cycle import BoundaryConditions, FullCycleConfig, FullCycleResult, simulate_full_cycle`
  - `from models import EngineGeometry, Fuel, InjectionSchedule`
  - `from thermo import omega_rad_per_s`
  - `from turbo import TurboConfig, compressor_pr_from_power`
- Uzywany przez (reverse-import):
  - `tests/test_turbo_coupled.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
- API (definicje top-level):
  - `class CoupledResult`
  - `def simulate_coupled_turbo()` - Iterate cycles to converge intake pressure from turbo power balance.

## virtual_tdi/dataset.py

- Typ: `CODE`; rozmiar: `18961` B
- Linie pliku: `462`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `argparse`
  - `csv`
  - `from dataclasses import dataclass`
  - `from pathlib import Path`
  - `from typing import Any`
  - `numpy`
  - `from config_loader import create_geometry_from_config, load_yaml_config`
  - `from edc_maps import BoostTargetMap2D, EGRMafTargetMap2D, SmokeLimiterMap2D`
  - `from full_cycle import BoundaryConditions, FullCycleConfig, simulate_full_cycle`
  - `from hydraulics import NozzleConfig, VP37HydraulicConfig, estimate_pilot_ratio`
  - `from lift_table import ValveLiftTable`
  - `from models import CombustionConfig, EngineGeometry, Fuel, InjectionSchedule, SimulationConfig`
  - `from n146_map import N146VoltageMap2D`
  - `from soi_map import SOIMap2D`
  - `from valvetrain import ValveFlow, ValveTiming`
  - `from vp37 import VP37LineModel, apply_hydraulic_delay`
  - `from vp37_cam import VP37CamProfile`
- Uzywany przez (reverse-import):
  - `tests/test_dataset.py`
  - `tests/test_dataset_config.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/__main__.py`
- API (definicje top-level):
  - `class DatasetConfig`
  - `def _resolve_map_path()`
  - `def generate_dataset()`
  - `def _make_argparser()`
  - `def main()`
- Pliki/dane wspominane w kodzie (heurystyka po rozszerzeniach):
  - `Table 1.csv`
  - `engine_reference_sources.yaml`
  - `profil_krzywek_4cylindry.md`
  - `skok_tloczka_vp37_de110.csv`
  - `synthetic.csv`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L225:         area_ratio = (base_d**2) / (nozzle_diam**2)
L226:         duration_main = duration_main * (area_ratio ** float(cfg.nozzle_flow_exp))
L278:             hrr_model="vp37_main" if cam is not None else "wiebe",
L383:     p.add_argument("--nozzle-flow-exp", type=float, default=1.0, help="Duration scaling exponent vs area ratio.")
L395:     p.add_argument("--integrator", choices=["rk4", "scipy"], default="scipy")
```

## virtual_tdi/edc_maps.py

- Typ: `CODE`; rozmiar: `7389` B
- Linie pliku: `221`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from pathlib import Path`
  - `re`
  - `numpy`
- Uzywany przez (reverse-import):
  - `tests/test_edc_maps.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
- API (definicje top-level):
  - `def _parse_float_any()`
  - `def _read_csv_rows()`
  - `class SmokeLimiterMap2D` (metody: from_csv, iq_max) - Smoke limiter: RPM x MAF(mg/str) -> max IQ (mg/str).
  - `class EGRMafTargetMap2D` (metody: from_csv, maf_target) - EGR MAF target: RPM x IQ(mg/str) -> target MAF (mg/str).
  - `class BoostTargetMap2D` (metody: from_csv, map_target_mbar) - Boost target: RPM x IQ(mg/str) -> MAP target (mbar abs).
  - `def _bilinear()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L158:         iq_axis = np.array([v / 100.0 if v >= 200.0 else v for v in raw_axis], dtype=float)
L197: def _bilinear(x_axis: np.ndarray, y_axis: np.ndarray, grid: np.ndarray, x: float, y: float) -> float:
L198:     x_c = float(np.clip(x, float(x_axis[0]), float(x_axis[-1])))
L199:     y_c = float(np.clip(y, float(y_axis[0]), float(y_axis[-1])))
L201:     xi = int(np.clip(np.searchsorted(x_axis, x_c, side="right") - 1, 0, len(x_axis) - 2))
L202:     yi = int(np.clip(np.searchsorted(y_axis, y_c, side="right") - 1, 0, len(y_axis) - 2))
```

## virtual_tdi/flow.py

- Typ: `CODE`; rozmiar: `4020` B
- Linie pliku: `140`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from math import sqrt`
  - `from typing import Any`
  - `from thermo import R_UNIVERSAL_J_PER_MOL_K`
- Uzywany przez (reverse-import):
  - `tests/test_backends.py`
  - `virtual_tdi/full_cycle.py`
- API (definicje top-level):
  - `def orifice_mdot_kg_per_s()` - Quasi-steady compressible orifice flow (ideal gas).
  - `def _fluids_orifice_mdot()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L3: from math import sqrt
L12:     t1_k: float | None = None, # Assuming t1_k is the temperature associated with p1_pa and it's always the temperature of the gas flowing through the orifice
L17:     gamma: float,
L24:     """Quasi-steady compressible orifice flow (ideal gas).
L46:     g = max(1.01, gamma)
L50:     pr_crit = (2.0 / (g + 1.0)) ** (g / (g - 1.0))
L59:             gamma=g,
L70:         term = (2.0 / (g + 1.0)) ** ((g + 1.0) / (2.0 * (g - 1.0)))
L71:         mdot_unsigned = a_eff * p_up * sqrt(g / (r * t_up)) * term
L74:         term = (2.0 * g / (r * t_up * (g - 1.0))) * (pr ** (2.0 / g) - pr ** ((g + 1.0) / g))
L78:             mdot_unsigned = a_eff * p_up * sqrt(term)
L88:     gamma: float,
L112:         "k": gamma,
L113:         "gamma": gamma,
L133:             mdot = fn(**call_kwargs)
```

## virtual_tdi/full_cycle.py

- Typ: `CODE`; rozmiar: `20937` B
- Linie pliku: `428`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import pi`
  - `from typing import Any`
  - `numpy`
  - `from combustion import CombustionScheduleRuntime, heat_release_rate_dq_dtheta, heat_release_rate_from_shaped_fuel, heat_release_rate_wiebe_single, maybe_arm_combustion`
  - `from flow import orifice_mdot_kg_per_s`
  - `from geometry import geometry_at_theta`
  - `from heat_transfer import h_woschni_simplified_w_per_m2_k, calculate_wall_heat_loss_j_per_rad`
  - `from models import EngineGeometry, Fuel, SimulationConfig, ManifoldConfig, ManifoldState, IntercoolerConfig`
  - `from thermo import GasModel, omega_rad_per_s`
  - `from valvetrain import ValveFlow, ValveTiming, effective_curtain_area_m2, valve_lift_fraction`
  - `from lift_table import ValveLiftTable`
  - `from vp37_cam import VP37CamProfile`
- Uzywany przez (reverse-import):
  - `tests/test_full_cycle_dynamic_manifolds.py`
  - `tests/test_full_cycle_sanity.py`
  - `tests/test_full_cycle_vp37_hrr.py`
  - `tests/test_turbo_coupled.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/coupled.py`
  - `virtual_tdi/dataset.py`
- API (definicje top-level):
  - `class BoundaryConditions`
  - `class FullCycleConfig` (metody: __post_init__)
  - `class FullCycleResult`
  - `def _rk4_step()`
  - `def simulate_full_cycle()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import pi
L28: DEG2RAD = pi / 180.0
L131: def _rk4_step(theta_rad: float, state: np.ndarray, *, step_rad: float, deriv) -> np.ndarray:
L149:     theta_deg = np.arange(cfg.theta_start_deg, cfg.theta_end_deg + cfg.step_deg / 2.0, cfg.step_deg, dtype=float)
L219:                 dm_dtheta = (m_main_kg / dur_main_rad) * float(np.interp(float((theta_r - soi_main_rad) / dur_main_rad), main_u, main_w, left=0.0, right=0.0))
L244:             gas.gamma(t_c, cfg.models, pressure_pa=p_c),
L249:             gas.gamma(t_i, cfg.models, pressure_pa=p_i),
L254:             gas.gamma(t_e, cfg.models, pressure_pa=p_e),
L259:             gas.gamma(cfg.t_ambient_k, cfg.models, pressure_pa=cfg.p_ambient_pa),
L266:         mdot_i_c = orifice_mdot_kg_per_s(p1_pa=p_i, t1_k=t_i, p2_pa=p_c, gamma=g_i, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=a_i, discharge_coeff=cfg.valve_flow.cd_intake, backend=cfg.models.flow_backend)
L267:         mdot_c_e = orifice_mdot_kg_per_s(p1_pa=p_c, t1_k=t_c, p2_pa=p_e, gamma=g_c, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=a_e, discharge_coeff=cfg.valve_flow.cd_exhaust, backend=cfg.models.flow_backend)
L269:         mdot_amb_i = orifice_mdot_kg_per_s(p1_pa=cfg.p_ambient_pa, t1_k=cfg.t_ambient_k, p2_pa=p_i, gamma=g_amb, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=cfg.manifold_throttle_coeff, discharge_coeff=0.8)
L270:         mdot_e_amb = orifice_mdot_kg_per_s(p1_pa=p_e, t1_k=t_e, p2_pa=cfg.p_ambient_pa, gamma=g_e, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=cfg.manifold_throttle_coeff, discharge_coeff=0.8)
L274:         mdot_egr = orifice_mdot_kg_per_s(p1_pa=p_e, t1_k=t_e, p2_pa=p_i, gamma=g_e, r_j_per_kg_k=gas.r_j_per_kg_k, area_m2=area_egr, discharge_coeff=cfg.egr_discharge_coeff, backend=cfg.models.flow_backend)
L379:     wi_j = float(trapezoid(results["pressure"] * np.gradient(volume, theta_rad), theta_rad))
L382:     indicated_torque_nm = (imep_pa * geom.swept_volume_m3_per_cyl * geom.cylinders) / (4.0 * pi)
L383:     brake_torque_nm = max(0.0, (imep_pa - fmep_pa) * geom.swept_volume_m3_per_cyl * geom.cylinders / (4.0 * pi))
L389:         "peak_pressure_bar": np.max(results["pressure"]) / 1.0e5,
L397:         "m_air_in_kg_per_cyl": np.sum(np.clip(results["mdot_in"], 0.0, None) * dt),
L398:         "m_exhaust_out_kg_per_cyl": np.sum(np.clip(-results["mdot_ex"], 0.0, None) * dt),
L399:         "p_intake_mean_bar": np.mean(results["p_intake"])/1e5,
L401:         "p_exhaust_mean_bar": np.mean(results["p_exhaust"])/1e5,
```

## virtual_tdi/geometry.py

- Typ: `CODE`; rozmiar: `2894` B
- Linie pliku: `85`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import cos, pi, sin, sqrt`
  - `from models import EngineGeometry`
- Uzywany przez (reverse-import):
  - `tests/test_geometry.py`
  - `virtual_tdi/full_cycle.py`
  - `virtual_tdi/solver.py`
- API (definicje top-level):
  - `class GeometryResult` (metody: heat_transfer_area_m2)
  - `def piston_position_s_m()`
  - `def piston_position_derivative_ds_dtheta()`
  - `def cylinder_volume_m3()` - Returns (V, dV/dtheta, x_from_tdc).
  - `def get_surface_areas()` - Returns heat transfer surface areas for head, piston, and liner.
  - `def geometry_at_theta()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import cos, pi, sin, sqrt
L31:     u = r * sin(theta_rad) - delta
L32:     return r * cos(theta_rad) + sqrt(max(0.0, L * L - u * u))
L39:     u = r * sin(theta_rad) - delta
L40:     denom = sqrt(max(1e-30, L * L - u * u))
L42:     return -r * sin(theta_rad) - (u * r * cos(theta_rad)) / denom
L66:     area_liner = pi * geom.bore_m * exposed_liner_height
```

## virtual_tdi/gui.py

- Typ: `CODE`; rozmiar: `9970` B
- Linie pliku: `242`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `queue`
  - `subprocess`
  - `sys`
  - `threading`
  - `tkinter`
  - `from tkinter import ttk`
- Uzywany przez (reverse-import):
  - `virtual_tdi/__main__.py`
- API (definicje top-level):
  - `class VirtualTdiGui` (metody: __init__, _build_form, _build_output, _row, _append, _poll_output, _build_cmd, _fluids_backend_available, on_run, _run_process, on_stop, on_clear, _set_running, run)
  - `def main()`

## virtual_tdi/heat_transfer.py

- Typ: `CODE`; rozmiar: `1494` B
- Linie pliku: `55`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from math import pow`
  - `from models import HeatTransferConfig`
- Uzywany przez (reverse-import):
  - `virtual_tdi/full_cycle.py`
  - `virtual_tdi/solver.py`
- API (definicje top-level):
  - `def h_woschni_simplified_w_per_m2_k()` - Calculates the gas-side heat transfer coefficient using a simplified
  - `def calculate_wall_heat_loss_j_per_rad()` - Calculates the total heat loss to the walls from all surfaces in J/rad
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L18:     Woschni correlation.
```

## virtual_tdi/hydraulics.py

- Typ: `CODE`; rozmiar: `3740` B
- Linie pliku: `136`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import pi, sqrt`
  - `from models import Fuel`
  - `from vp37_cam import VP37CamProfile`
- Uzywany przez (reverse-import):
  - `tests/test_hydraulics.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
  - `virtual_tdi/injection.py`
- API (definicje top-level):
  - `class NozzleConfig` (metody: area_m2)
  - `class NeedleConfig` (metody: seat_area_m2, max_lift_m) - Properties of the injector needle for dynamic simulation.
  - `class VP37HydraulicConfig` (metody: plunger_area_m2, volume_eff_m3)
  - `def estimate_pilot_ratio()` - Estimate pilot mass fraction from pressure trace in a simplified VP37 line model.
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import pi, sqrt
L22:         return (pi * (d**2) / 4.0) * self.holes
L53:         return pi * (d**2) / 4.0
L91:     omega_pump = (rpm / 2.0) * 2.0 * pi / 60.0  # pump rad/s
L110:         dt = (d_deg * pi / 180.0) / max(1e-9, omega_pump)
L121:             m_dot = area_eff * sqrt(2.0 * rho * dp)
```

## virtual_tdi/injection.py

- Typ: `CODE`; rozmiar: `5106` B
- Linie pliku: `129`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `numpy`
  - `from math import pi, sqrt`
  - `from models import Fuel`
  - `from hydraulics import NozzleConfig, VP37HydraulicConfig, NeedleConfig`
  - `from vp37_cam import VP37CamProfile`
- Uzywany przez (reverse-import):
  - `virtual_tdi/cli.py`
- API (definicje top-level):
  - `class InjectionLineConfig`
  - `class InjectionResult` - High-resolution result of a single injection event simulation.
  - `def solve_injection_hydraulics()` - Solves the 1D injection hydraulics including a lumped-parameter line model
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import pi, sqrt
L55:     omega_pump = (rpm / 2.0) * 2.0 * pi / 60.0
L56:     total_time = (a_deg[-1] - a_deg[0]) * pi / 180.0 / omega_pump
L61:     L_seg, A_line, V_seg = line.length_m / line.segments, pi * (line.diameter_mm*1e-3)**2 / 4.0, (pi * (line.diameter_mm*1e-3)**2 / 4.0) * (line.length_m / line.segments)
L66:     state = np.zeros(2 * N + 2)
L70:     pump_angle_rad = np.interp(time_s, (time_s[0], time_s[-1]), (a_deg[0]*pi/180.0, a_deg[-1]*pi/180.0))
L71:     plunger_pos_m = np.interp(pump_angle_rad, a_deg*pi/180.0, s_mm*1e-3)
L102:         m_dot_noz = area_eff * sqrt(2.0 * rho * dp_nozzle)
```

## virtual_tdi/lift_table.py

- Typ: `CODE`; rozmiar: `4169` B
- Linie pliku: `113`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from pathlib import Path`
  - `numpy`
- Uzywany przez (reverse-import):
  - `tests/test_full_cycle_dynamic_manifolds.py`
  - `tests/test_lift_table.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
  - `virtual_tdi/full_cycle.py`
- API (definicje top-level):
  - `class ValveLiftTable` (metody: from_markdown, lift_m) - Valve lift table for a 4-stroke 720° crank cycle.
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L20:     intake_lift_mm: dict[int, np.ndarray]  # cyl -> (N,)
L21:     exhaust_lift_mm: dict[int, np.ndarray]  # cyl -> (N,)
L84:         def ordered(values: list[float]) -> np.ndarray:
L108:         x_ext = np.concatenate([x, x[:1] + 720.0])
L110:         mm = float(np.interp(t, x_ext, y_ext))
```

## virtual_tdi/models.py

- Typ: `CODE`; rozmiar: `10027` B
- Linie pliku: `290`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `numpy`
  - `from scipy.interpolate import LinearNDInterpolator`
  - `from dataclasses import dataclass`
  - `from math import pi`
  - `from typing import Literal, Optional, Any`
  - `from scipy.interpolate import interp1d`
- Uzywany przez (reverse-import):
  - `tests/test_backends.py`
  - `tests/test_config_loader.py`
  - `tests/test_full_cycle_dynamic_manifolds.py`
  - `tests/test_full_cycle_sanity.py`
  - `tests/test_full_cycle_vp37_hrr.py`
  - `tests/test_geometry.py`
  - `tests/test_hydraulics.py`
  - `tests/test_solver_sanity.py`
  - `tests/test_turbo_coupled.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/combustion.py`
  - `virtual_tdi/config_loader.py`
  - `virtual_tdi/coupled.py`
  - `virtual_tdi/dataset.py`
  - `virtual_tdi/full_cycle.py`
  - `virtual_tdi/geometry.py`
  - `virtual_tdi/heat_transfer.py`
  - `virtual_tdi/hydraulics.py`
  - `virtual_tdi/injection.py`
  - `virtual_tdi/solver.py`
  - `virtual_tdi/thermo.py`
  - `virtual_tdi/turbo.py`
  - `virtual_tdi/vp37.py`
- API (definicje top-level):
  - `class EngineGeometry` (metody: piston_area_m2, swept_volume_m3_per_cyl, clearance_volume_m3_per_cyl)
  - `class FrictionModel` - Parameters for the Chen-Flynn friction model.
  - `class CompressorMap` (metody: from_csv, get_efficiency, get_turbo_rpm) - Interpolated compressor map data.
  - `class VntMap` (metody: from_csv, get_effective_area) - Interpolated VNT effective area map data.
  - `class ManifoldConfig` - Static properties of a manifold.
  - `class IntercoolerConfig` - Static properties of an intercooler.
  - `class N146ActuatorConfig` - Parameters for the N146 dosing plunger actuator model.
  - `class ManifoldState` (metody: from_config) - Dynamic state of a manifold as a 0D control volume.
  - `class Fuel` (metody: diesel, svo_rapeseed, methanol)
  - `class InjectionSchedule`
  - `class HeatTransferConfig` (metody: wall_temp_k)
  - `class CombustionConfig`
  - `class SimulationConfig`
  - `class EngineState`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L7: from math import pi
L27:         return pi * (self.bore_m ** 2) / 4.0
L245:     hrr_model: Literal["wiebe", "vp37_main", "hydraulic_profile"] = "wiebe"
L272:     integrator: Literal["rk4", "scipy"] = "scipy"
```

## virtual_tdi/n146_map.py

- Typ: `CODE`; rozmiar: `4759` B
- Linie pliku: `138`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from pathlib import Path`
  - `re`
  - `numpy`
- Uzywany przez (reverse-import):
  - `tests/test_n146_map.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
- API (definicje top-level):
  - `def _parse_float_any()`
  - `class N146VoltageMap2D` (metody: from_csv, mv, iq_from_mv, _row_at_rpm, _bilinear) - N146 quantity adjuster voltage map: RPM x IQ(mg/str) -> mV.
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L100:         mv_c = float(np.clip(mv, float(v_sorted[0]), float(v_sorted[-1])))
L101:         return float(np.interp(mv_c, v_sorted, iq_sorted))
L103:     def _row_at_rpm(self, rpm: float) -> np.ndarray:
L104:         x = float(np.clip(rpm, float(self.rpm_axis[0]), float(self.rpm_axis[-1])))
L105:         xi = np.searchsorted(self.rpm_axis, x, side="right") - 1
L106:         xi = int(np.clip(xi, 0, len(self.rpm_axis) - 2))
L113:         x = float(np.clip(rpm, float(self.rpm_axis[0]), float(self.rpm_axis[-1])))
L114:         y = float(np.clip(iq, float(self.iq_axis_mg_per_str[0]), float(self.iq_axis_mg_per_str[-1])))
L116:         xi = np.searchsorted(self.rpm_axis, x, side="right") - 1
L117:         yi = np.searchsorted(self.iq_axis_mg_per_str, y, side="right") - 1
L118:         xi = int(np.clip(xi, 0, len(self.rpm_axis) - 2))
L119:         yi = int(np.clip(yi, 0, len(self.iq_axis_mg_per_str) - 2))
```

## virtual_tdi/soi_map.py

- Typ: `CODE`; rozmiar: `4248` B
- Linie pliku: `127`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from pathlib import Path`
  - `re`
  - `numpy`
- Uzywany przez (reverse-import):
  - `tests/test_soi_map.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
- API (definicje top-level):
  - `def _parse_float_any()`
  - `class SOIMap2D` (metody: from_csv, soi_deg_model_convention, _bilinear) - SOI map: RPM x IQ(mg/str) -> SOI(deg).
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L102:         x = float(np.clip(rpm, float(self.rpm_axis[0]), float(self.rpm_axis[-1])))
L103:         y = float(np.clip(iq, float(self.iq_axis_mg_per_str[0]), float(self.iq_axis_mg_per_str[-1])))
L105:         xi = np.searchsorted(self.rpm_axis, x, side="right") - 1
L106:         yi = np.searchsorted(self.iq_axis_mg_per_str, y, side="right") - 1
L107:         xi = int(np.clip(xi, 0, len(self.rpm_axis) - 2))
L108:         yi = int(np.clip(yi, 0, len(self.iq_axis_mg_per_str) - 2))
```

## virtual_tdi/solver.py

- Typ: `CODE`; rozmiar: `13675` B
- Linie pliku: `387`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import pi`
  - `from typing import Any`
  - `numpy`
  - `from combustion import CombustionScheduleRuntime, heat_release_rate_dq_dtheta, maybe_arm_combustion`
  - `from geometry import geometry_at_theta`
  - `from heat_transfer import h_woschni_simplified_w_per_m2_k`
  - `from models import EngineGeometry, Fuel, InjectionSchedule, SimulationConfig`
  - `from thermo import GasModel, omega_rad_per_s`
- Uzywany przez (reverse-import):
  - `tests/test_solver_sanity.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
- API (definicje top-level):
  - `class SimulationResult`
  - `def _rk4_step_pressure()`
  - `def simulate_closed_cycle()`
  - `def simulate_closed_cycle_scipy()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import pi
L18: DEG2RAD = pi / 180.0
L30:     gamma: np.ndarray
L60:     theta_deg = np.arange(cfg.theta_start_deg, cfg.theta_end_deg + cfg.step_deg / 2.0, cfg.step_deg, dtype=float)
L76:     gamma = np.zeros_like(theta_rad)
L86:         g = gas.gamma(T, cfg, pressure_pa=p_pa)
L133:         gamma[i] = gas.gamma(temperature[i], cfg, pressure_pa=pressure[i])
L169:     gamma[0] = gas.gamma(temperature[0], cfg, pressure_pa=pressure[0])
L173:     dV = np.gradient(volume, theta_rad)  # m3/rad
L177:     indicated_torque_nm = imep_pa * vd_total / (4.0 * pi)  # 4-stroke
L178:     brake_torque_nm = max(0.0, (imep_pa - cfg.fmep_pa) * vd_total / (4.0 * pi))
L183:         "peak_pressure_bar": float(np.max(pressure) / 1.0e5),
L199:         gamma=gamma,
L211:         from scipy.integrate import solve_ivp
L219:     theta_deg = np.arange(cfg.theta_start_deg, cfg.theta_end_deg + cfg.step_deg / 2.0, cfg.step_deg, dtype=float)
L250:     def rhs(theta_r: float, y: np.ndarray, rt: CombustionScheduleRuntime) -> np.ndarray:
L256:         g = gas.gamma(T, cfg, pressure_pa=P)
L293:         sol = solve_ivp(
L331:     gamma = np.zeros_like(theta_rad)
L339:         gamma[i] = gas.gamma(float(T_grid[i]), cfg, pressure_pa=P)
L362:     indicated_torque_nm = imep_pa * vd_total / (4.0 * pi)
L363:     brake_torque_nm = max(0.0, (imep_pa - cfg.fmep_pa) * vd_total / (4.0 * pi))
L368:         "peak_pressure_bar": float(np.max(pressure) / 1.0e5),
L384:         gamma=gamma,
```

## virtual_tdi/thermo.py

- Typ: `CODE`; rozmiar: `5185` B
- Linie pliku: `136`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from functools import lru_cache`
  - `from math import exp`
  - `from typing import Any`
  - `from models import SimulationConfig`
- Uzywany przez (reverse-import):
  - `tests/test_backends.py`
  - `virtual_tdi/combustion.py`
  - `virtual_tdi/coupled.py`
  - `virtual_tdi/flow.py`
  - `virtual_tdi/full_cycle.py`
  - `virtual_tdi/solver.py`
  - `virtual_tdi/vp37.py`
- API (definicje top-level):
  - `class GasModel` (metody: gamma, cp, cv, density_from_pT, pressure_from_rhoT, temperature_from_prho)
  - `def _coolprop_module()`
  - `def _real_gas_props()`
  - `def ignition_delay_seconds_arrhenius()` - Simple Arrhenius-like model from spec (tunable; not a calibrated correlation).
  - `def omega_rad_per_s()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L5: from math import exp
L19:     def gamma(self, temperature_k: float, cfg: SimulationConfig, *, pressure_pa: float | None = None) -> float:
L22:             return props["gamma"]
L30:         g = self.gamma(temperature_k, cfg, pressure_pa=pressure_pa)
L115:             gamma = cp / cv
L116:             return {"cp": cp, "cv": cv, "gamma": gamma}
L131:     return a * (p_bar ** (-n)) * exp(ea_j_per_mol / (R_UNIVERSAL_J_PER_MOL_K * max(1.0, t_k)))
```

## virtual_tdi/turbo.py

- Typ: `CODE`; rozmiar: `2515` B
- Linie pliku: `80`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import pow`
  - `from typing import Optional`
  - `from models import CompressorMap, VntMap`
- Uzywany przez (reverse-import):
  - `tests/test_turbo_coupled.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/coupled.py`
- API (definicje top-level):
  - `class TurboConfig`
  - `def get_compressor_efficiency()`
  - `def get_compressor_turbo_rpm()`
  - `def get_vnt_effective_area()`
  - `def compressor_pr_from_power()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L19:     gamma: float = 1.35
L75:     g = max(1.1, cfg.gamma)
```

## virtual_tdi/valvetrain.py

- Typ: `CODE`; rozmiar: `1628` B
- Linie pliku: `57`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import pi, sin`
- Uzywany przez (reverse-import):
  - `tests/test_config_loader.py`
  - `tests/test_full_cycle_dynamic_manifolds.py`
  - `tests/test_full_cycle_sanity.py`
  - `tests/test_valvetrain.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/config_loader.py`
  - `virtual_tdi/dataset.py`
  - `virtual_tdi/full_cycle.py`
- API (definicje top-level):
  - `class ValveTiming`
  - `class ValveFlow`
  - `def _cycle_angle_0_720()`
  - `def valve_lift_fraction()` - Smooth normalized lift (0..1) between open and close over a 720° cycle.
  - `def effective_curtain_area_m2()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import pi, sin
L34:     Uses a symmetric sin(pi * phi) profile where phi in [0,1].
L49:     return float(sin(pi * phi))
L54:     curtain = pi * valve_diameter_m * max(0.0, lift_m)
L55:     port = pi * (valve_diameter_m**2) / 4.0
```

## virtual_tdi/vp37.py

- Typ: `CODE`; rozmiar: `1124` B
- Linie pliku: `32`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from math import sqrt`
  - `from models import Fuel, InjectionSchedule`
  - `from thermo import omega_rad_per_s`
- Uzywany przez (reverse-import):
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
- API (definicje top-level):
  - `class VP37LineModel`
  - `def apply_hydraulic_delay()`
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L4: from math import sqrt
L19:     c = sqrt(max(1.0, fuel.bulk_modulus_pa) / max(1e-9, fuel.density_kg_per_m3))
```

## virtual_tdi/vp37_cam.py

- Typ: `CODE`; rozmiar: `8198` B
- Linie pliku: `223`
- Zaleznosci (importy):
  - `from __future__ import annotations`
  - `from dataclasses import dataclass`
  - `from pathlib import Path`
  - `numpy`
- Uzywany przez (reverse-import):
  - `tests/test_full_cycle_vp37_hrr.py`
  - `tests/test_hydraulics.py`
  - `tests/test_vp37_cam.py`
  - `virtual_tdi/__init__.py`
  - `virtual_tdi/cli.py`
  - `virtual_tdi/dataset.py`
  - `virtual_tdi/full_cycle.py`
  - `virtual_tdi/hydraulics.py`
  - `virtual_tdi/injection.py`
- API (definicje top-level):
  - `class VP37CamProfile` (metody: from_csv, _lobe_index_for_cylinder, _rising_segment, duration_main_crank_deg, rate_shape_u_w) - VP37 cam-plate plunger stroke profile.
- Wybrane linie/wzory (doslownie z kodu; z numerami linii):
```text
L70:             idx = np.argsort(stroke_mm)[-4:]
L82:     def _rising_segment(self, lobe_idx: int) -> tuple[np.ndarray, np.ndarray]:
L93:         ang_ext = np.concatenate([ang, ang[1:] + 360.0])
L97:         peak_idx = int(np.argmin(np.abs(ang_ext - peak)))
L152:         s_norm = np.clip(s / peak, 0.0, 1.0)
L159:         a_start = float(np.interp(start_frac, s_sorted, a_sorted))
L160:         a_end = float(np.interp(end_frac, s_sorted, a_sorted))
L174:     ) -> tuple[np.ndarray, np.ndarray]:
L191:         s_norm = np.clip(s / peak, 0.0, 1.0)
L215:         w_grid = np.interp(u_grid, u_raw, ds_da)
```
