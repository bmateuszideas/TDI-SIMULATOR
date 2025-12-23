# TODO: Inżynierskie GUI (Dashboard R&D) + paliwa alternatywne

Źródła wymagań:
- `Untitled.md` – FRS: układ 3‑panelowy, lista wejść/wyjść, batch/sweep, wymagania techniczne.
- `A weź zrob liste tych wszystkich z parametrami (1).md` – lista paliw + parametry (ρ, K, LHV) oraz notatki o wpływie na model.

Cel:
- Zbudować **inżynierski dashboard** do szybkich eksperymentów (R&D), który:
  - ustawia parametry (hardware + warunki brzegowe + numeryka),
  - uruchamia symulację (full/closed),
  - pokazuje metryki i wykresy interaktywne,
  - robi sweep/batch i zapisuje wyniki,
  - obsługuje **paliwa alternatywne** (predefiniowane + “Custom”).

---

## 0) Decyzje startowe (1x)

1) Wybrać technologię GUI (rekomendacja: **Streamlit MVP**, potem ewentualnie **PySide6 Pro**):
- **Streamlit MVP (szybko, najmniej kodu UI)**:
  - wykresy: Plotly,
  - plusy: szybki prototyp, łatwe interakcje,
  - minusy: “web‑desktop” (lokalnie w przeglądarce).
- **PySide6 Pro (desktop “jak z labu”)**:
  - wykresy: PyQtGraph (bardzo szybkie) albo Plotly w WebView,
  - plusy: prawdziwy desktop, splittery, docki,
  - minusy: więcej kodu i pracy z wątkami.

2) Ustalić politykę zapisu konfiguracji:
- Minimalnie: UI trzyma override w pamięci i zapisuje do **osobnego pliku preset** (np. `configs/presets/*.yaml`).
- Jeśli wymagane “edytuj `engine_reference_sources.yaml` w locie”: dodać przycisk “Save to YAML (nadpisz)” + potwierdzenie + walidacja schema.

3) Ustalić spójne nazwy wejść:
- CLI ma dziś m.in. `--fuel-mg`, `--p-intake-bar`, `--soi-main`, `--soi-map`.
- FRS używa nazw `--iq`, `--boost` (mbar), `--soi offset`.
- TODO: dopisać aliasy w CLI albo mapować w UI (zalecane: **aliasy w CLI**).

---

## 1) Backend API dla GUI (bez subprocess) – MUST HAVE

FRS wymaga: “GUI importuje backend, nie odpala subprocess”.

### 1.1. Dodać moduł API (np. `virtual_tdi/app_api.py`) (DONE)

**Zadanie**
- Wyciągnąć z `virtual_tdi/cli.py` logikę “zbuduj konfigurację → uruchom solver → zwróć wyniki” do funkcji bez argparse.

**Proponowane API**
- `load_engine_config(path: Path) -> dict`
- `save_engine_config(config: dict, path: Path) -> None` (opcjonalnie)
- `build_case(config_yaml: dict, overrides: dict) -> CaseConfig`
- `run_case(case: CaseConfig) -> CaseResult`
- `run_sweep(sweep: SweepConfig) -> SweepResult`

**CaseResult powinien zawierać**
- tablice do wykresów: `theta_deg`, `pressure_pa`, `temp_k`, `volume_m3`, `p_intake_pa`, `p_exhaust_pa`, `mdot_in`, `mdot_ex`, `dq_comb`, `dq_wall`, `dm_fuel_main_mg_per_deg`, `lift_i`, `lift_e`, itd. (co już istnieje w wynikach full cycle).
- `metrics: dict[str, float]` (już jest).
- opcjonalnie (debug) gdy `hrr_model == hydraulic_profile`:
  - `needle_lift_m`, `line_pressure_pa`, `mdot_fuel_kg_s`, `inj_theta_deg` (żeby UI narysowało hydraulikę i “Needle Lift Max”).

**Akceptacja**
- GUI potrafi uruchomić symulację *bez* subprocess.
- CLI dalej działa (CLI tylko “opakowuje” API).

### 1.2. Aliasowanie nazw wejść (FRS ↔ CLI) (DONE)

**Zadanie**
- Dodać aliasy w `virtual_tdi/cli.py`:
  - `--iq` jako alias `--fuel-mg`,
  - `--boost-mbar-abs` jako alias `--p-intake-bar` (przeliczenie),
  - `--soi-offset-deg` (dodaje offset do SOI z mapy lub do `--soi-main`).

**Akceptacja**
- UI może używać nazw z FRS bez ręcznych przeliczeń w UI.

---

## 2) Model stanu UI (UI State) - MUST HAVE (DONE)

### 2.1. Zdefiniować strukturę stanu (DONE)

**Zadanie**
- Stworzyć `UiState` (dataclass), który przechowuje:
  - `engine_config_path`,
  - “Hardware” (geometria, komora, wtrysk, zawory),
  - “Operating point” (rpm, iq, boost, soi offset),
  - “Numerics” (step_deg, integrator, backends),
  - “Thermal BC” (wall temps, ambient),
  - “Files” (mapy, cam profile, valve table).

**Ważne**
- `engine_reference_sources.yaml` ma strukturę `...: {value, unit, source}` – UI edytuje **tylko `.value`**, a `unit/source` zachowuje.

### 2.2. Walidacje wejść (UI‑side) (DONE)

**Zadanie**
- Zakresy jak w FRS (np. bore 70–90 mm, step_deg > 0, rpm 800–5500, itd.).
- Walidacja spójności:
  - CR wyliczany vs. Vc → wyświetlać na żywo (np. “CR computed: 19.50”).
  - gdy `hrr_model in {vp37_main, hydraulic_profile}` a brak pliku cam → blokada + komunikat.

---

## 3) Inżynierskie GUI – implementacja (Streamlit MVP)

### 3.1. Nowy entry‑point (DONE)

**Zadanie**
- Dodać moduł np. `virtual_tdi/dashboard_streamlit.py`.
- Dodać w `virtual_tdi/__main__.py` komendę: `python -m virtual_tdi dashboard`.

**Uruchomienie**
- `python -m virtual_tdi dashboard` (wrapper) albo `streamlit run virtual_tdi/dashboard_streamlit.py`.

### 3.2. Layout 3‑panelowy (FRS) (DONE)

**Zadanie**
- Lewy panel (`st.sidebar`): Hardware + Numerics + Save/Load.
- Centrum: wykresy (Plotly), zakładki: `P-θ`, `PV`, `ROHR+Needle`, `Heat`, `Massflow`.
- Prawy panel: druga kolumna: telemetria + log/status + przyciski Run/Stop/Reset.

### 3.3. “Run single” i telemetria (DONE)

**Zadanie**
- `RUN_SINGLE`:
  - zbudować `CaseConfig`,
  - uruchomić `run_case`,
  - odświeżyć wykresy i KPI.
- KPI zgodnie z FRS (mapowanie z `result.metrics`):
  - moc/torque/BSFC, Pmax, IMEP,
  - SOI actual + ignition delay,
  - (gdy hydraulic_profile) `needle_lift_max`.

### 3.4. Obsługa IMEP < 0 (alert) (DONE)

**Zadanie**
- Jeśli `imep_bar < 0`: czerwony alert + sugestie (np. zmień ignition delay na fixed / przesuń SOI / parametry Arrheniusa).

---

## 4) Batch / Sweep (wg FRS) – MUST HAVE (DONE)

### 4.1. Sweep 2D (RPM x IQ) (DONE)

**Zadanie**
- UI: start/stop/step dla RPM i IQ + nazwa pliku.
- Backend: pętla po siatce, zapis CSV (np. `data/grid_rpm_iq.csv`) + metryki w kolumnach.
- Progres: pasek + ETA.

### 4.2. Sweep SOI (main) (DONE)

**Zadanie**
- UI: start/stop/step (deg) + opcja “add to map” / “export CSV”.
- Backend: użyć istniejącej ścieżki CLI `--soi-main-sweep` albo przenieść ją do API.

---

## 5) Paliwa alternatywne – MUST HAVE (z listy użytkownika)

Model paliwa w kodzie: `virtual_tdi/models.py:Fuel` wymaga co najmniej:
- `density_kg_per_m3` (ρ),
- `bulk_modulus_pa` (K),
- `lhv_j_per_kg` (LHV),
- (opcjonalnie) `stoich_air_fuel`, parametry ignition delay (Arrhenius).

### 5.0. Tabela wejściowa paliw (z Twojej listy)

Uwaga praktyczna (wg notatki): parametry dla margaryny/smalcu dotyczą stanu **ciekłego ~70–80°C**; lepkości nie modelujemy jeszcze, więc to tylko “fizyka falowa + energia”.

| Fuel (nazwa w GUI) | density ρ (kg/m3) | bulk modulus K (bar) | LHV (MJ/kg) | Uwagi |
|---|---:|---:|---:|---|
| Diesel (ON) – baza | 840 | 16000 | 43.0 | mapy ECU są “skalibrowane” pod diesel |
| SVO (rapeseed) | 920 | 19000 | 37.6 | gęstszy i “twardszy” |
| Biodiesel (B100/FAME) | 880 | 17500 | 38.0 | pomiędzy diesel i SVO |
| Margaryna (roztopiona) | 915 | ~18500 | 39.5 | podobna do SVO po roztopieniu |
| Smalec (ciekły) | 890 | ~17000 | 39.8 | wysoka kaloryczność |
| WVO (zużyta frytura) | 930+ | 19500 | 36.5 | “brudny olej”; przyjąć np. 930 lub 940 |
| Olej opałowy | 850 | 16000 | 42.5 | blisko diesel |
| Olej silnikowy (zużyty) | 900 | 18000 | 44.0 | wysoka energia, ale lepkość “killer” (poza modelem) |
| Olej transformatorowy | 870 | 17000 | 45.0 | bardzo energetyczny |

Konwersje do backendu:
- `bulk_modulus_pa = bulk_modulus_bar * 1e5`
- `lhv_j_per_kg = lhv_mj_per_kg * 1e6`

### 5.1. Dodać predefiniowane paliwa do `Fuel` (DONE)

**Zadanie**
- Dodać metody fabryczne (nazwy robocze; możesz zmienić):
  - `Fuel.biodiesel_b100_fame()`
  - `Fuel.margarine_melted()`
  - `Fuel.lard_liquid()`
  - `Fuel.wvo_used_frying_oil()`
  - `Fuel.heating_oil()`
  - `Fuel.used_engine_oil()`
  - `Fuel.transformer_oil()`
- Konwersje z tabeli:
  - `bulk_modulus_pa = bulk_modulus_bar * 1e5`
  - `lhv_j_per_kg = lhv_mj_per_kg * 1e6`
- Parametry ignition delay (jeśli brak danych): startowo kopiować z `diesel()` albo `svo_rapeseed()` + oznaczyć jako “placeholder”.

**Akceptacja**
- `virtual_tdi/cli.py` i `virtual_tdi/dataset.py` widzą nowe paliwa w `--fuel` / `--fuels`.

### 5.2. Tryb “Custom fuel” (zgodnie z FRS) (DONE)

**Zadanie**
- Dodać `--fuel custom` + flagi:
  - `--fuel-density-kgm3`
  - `--fuel-bulk-modulus-bar`
  - `--fuel-lhv-mjkg`
  - opcjonalnie: `--fuel-stoich-afr`, `--id-a`, `--id-n`, `--id-ea`.
- W GUI: gdy `Fuel=Custom`, odblokować pola edycji tych wartości.

### 5.3. UI: pokazywać “co to robi” (ρ/K/LHV) (DONE)

**Zadanie**
- W panelu paliwa wyświetlać:
  - `c = sqrt(K/ρ)` (prędkość fali),
  - energię na cykl: `m_fuel * LHV`,
  - ostrzeżenie: lepkość nie jest modelowana (ważne dla margaryny/smalcu/WVO).

### 5.4. Fuel temperature (FRS: IN_07) – spójne z `dataset.py` (DONE)

W generatorze datasetu jest już prosta korekta gęstości:
- `rho_corr = rho * (1 - (T_c - 15) * 0.00083)` (z clampem np. `>= 600`).

**Zadanie**
- Dodać `--fuel-temp-c` do CLI i do `SimulationConfig`.
- Stosować korektę `rho_corr` w miejscach, gdzie liczy się hydraulika/wtrysk (co najmniej w `vp37.py`, `hydraulics.py`, `injection.py`), tak żeby GUI mogło pokazać wpływ temperatury paliwa.

---

## 6) Wykresy (FRS) – MUST HAVE minimum set (DONE)

1) `P(θ)` – cylinder pressure vs crank angle (0–720).
2) `PV` – pętla indykatorowa (log‑log lub linear) + liczba “work per cycle”.
3) `ROHR + dm_fuel/dθ` (albo `dq_comb/dθ`) – analiza spalania.
4) Gdy `hydraulic_profile`: `needle lift` + `line pressure` (debug hydrauliki).

---

## 7) Spójność z aktualnym repo (gap list)

1) Obecne `virtual_tdi/gui.py` odpala subprocess → zostawić jako “proste GUI”, ale dodać nowe “engineering GUI” wg tego TODO.
2) FRS mówi o `Compression Ratio` jako wejściu – w aktualnym modelu CR wynika z geometrii Vc; w GUI lepiej:
   - pokazywać CR wyliczony,
   - pozwolić edytować składniki Vc (bowl/head/gasket/protrusion).
3) FRS ma `Boost Pressure` i `SOI Offset` – dziś to jest rozproszone w `--p-intake-bar`, `--use-boost-map`, `--soi-main`/mapy → dodać aliasy/ustandaryzować.

