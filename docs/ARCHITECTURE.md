# Architektura: Virtual TDI

Mapa kodu według warstw manifestu "cyfrowy duch" (`CYFROWY_DUCH_FUNDAMENTALNE_ZALOZENIA.md`).
Cel produktu: `docs/PRODUCT.md`. Kontrakt I/O: `docs/IO_CONTRACT.md`.

## Przepływ danych (od źródeł do wyników)

```
engine_reference_sources.yaml ─┐
Mapa*.csv (SOI/N146/EGR/BOOST) ─┼─► config_loader.py / edc_maps.py / soi_map.py / n146_map.py
skok_tloczka_vp37_de110.csv ────┤        │
profil_krzywek_4cylindry.md ────┘        ▼
                              models.py (dataclasses: EngineGeometry, SimulationConfig, ...)
                                        │
        ┌───────────────┬───────────────┼────────────────┬───────────────┐
        ▼               ▼               ▼                ▼               ▼
   geometry.py    solver.py      full_cycle.py     coupled.py     transient.py
   valvetrain.py  (closed 360°)  (720° + manifolds) (turbo maps  (MVEM, governor,
   lift_table.py                  + gas exchange)    + shaft dyn)  PID boost, perception)
   vp37_cam.py                                             │
        └───────────────┬───────────────┘                ▼
                        ▼                          dataset.py / compare.py / validation.py / cli.py / gui.py
                  thermo.py, combustion.py, flow.py,        │
                  heat_transfer.py, fmep.py,                 ▼
                  hydraulics.py, injection.py, vp37.py   out/: cycle.csv, metrics.txt,
                                                        transient.csv, *.png, dataset CSV
```

Zasada: **warstwy nie mieszają się w dół** — warstwa 3 (ECU) czyta stan fizyki
przez percepcję, nigdy nie odwrotnie; mapy ECU są referencją/ograniczeniem,
nie zastępują fizyki (patrz README "Mapy ECU a fizyka").

## Warstwy i moduły

### Warstwa 0 — dane źródłowe (źródło prawdy)
- `engine_reference_sources.yaml` — wszystkie parametry fizyczne z polem `source`;
  ładowane przez `config_loader.py` (geometria, kolektory, zawory, wymiana ciepła).
- Mapy ECU (CSV w root): SOI, N146, SmokeLimiter, EGR→MAF, BOOST — kanon osi/jednostek:
  `docs/MAPY_ECU_KONWENCJE.md`; zakres i konfiguracja sprzętowa: `docs/BASELINE_MAPY_ECU_I_OSPRZET.md`.
- Profile: `skok_tloczka_vp37_de110.csv` (krzywka VP37), `profil_krzywek_4cylindry.md`
  (wznios zaworów). Katalog parametrów z źródłami: `docs/PARAMETRY_SILNIKA.md`.

### Warstwa 1 — geometria i kinematyka
- `geometry.py` — `V(θ)`, `dV/dθ` z desaxage; `models.py:EngineGeometry`.
- `valvetrain.py` — `ValveTiming`, `ValveFlow`, powierzchnia kurtyny zaworu.
- `lift_table.py` — tabela wzniosu z profilu rozrządu (zamiast sinusów).
- `vp37_cam.py` — profil skoku tłoczka VP37 → czas trwania wtrysku.

### Warstwa 2 — fizyko-chemia (bez full-chem)
- `thermo.py` — `GasModel` z `γ(T, x)` (blend powietrze/spaliny, EGR, burned fraction);
  backend `simple` (pure Python) lub `coolprop` (tablicowany lookup, ~1 s/cykl).
- `combustion.py` — Double-Wiebe (pilot+main), opóźnienie zapłonu Arrhenius z capem,
  HRR z profilu hydraulicznego (`vp37_main`, `hydraulic_profile`).
- `flow.py` — przepływ kryzą przez zawory (dwukierunkowy), kolektory 0D.
- `heat_transfer.py` — Woschni uproszczony, 3 powierzchnie ścian (głowica/tłok/tuleja),
  temperatury z YAML/CLI.
- `fmep.py` — FMEP = A + B·krpm + C·peak-P/bar (kalibrowane wg Heywood Ch. 13).
- `hydraulics.py`, `injection.py`, `vp37.py` — dysza/iglica (NeedleConfig),
  linia wysokiego ciśnienia (opóźnienie SOI), wielofazowość.
- `solver.py` — cykl zamknięty (sprężanie/spalanie/rozprężanie), RK4 lub SciPy.
- `full_cycle.py` — pełne 720°: gazowymiana, bilanse masy/energii kolektorów,
  masa paliwa w ładunku, EGR; metryki → `metrics.txt`.
- `turbo.py`, `turbo_map.py`, `coupled.py` — mapy GT1749V (sprężarka/turbina),
  `shaft_dynamics_step` (J·dω/dt), coupling mocy + feedforward z mapy BOOST.

### Warstwa 3 — inteligencja (ECU)
- `edc_maps.py`, `soi_map.py`, `n146_map.py` — parsery map 2D (bilinear + clipping).
- `perception.py` — `SensorModel` (lag 1. rzędu + delay + bias + szum z seedem),
  `PerceptionLayer` dla rpm/MAP/EGT.
- `controller.py` — bisekcja monotoniczna (solve target-kW), `BoostPidConfig`
  (PID na błąd boost → VNT, anti-windup).
- `transient.py` — MVEM: governor PI → IQ, bezwładność wału, dynamika turbo,
  w każdym kroku pełny cykl 720°.
- `vcds_logs.py` — parser logów VCDS (grupy 003/008/010/011) + klasyfikator usterek;
  kanon: `docs/DIAGNOSTYKA_VCDS.md`.

### Warstwa 4 — powierzchnie produktu
- `cli.py` / `__main__.py` — `simulate` (domyślnie, flagi) + subkomendy
  `dataset`, `compare`, `validate`, `gui` (dysponowane w `__main__.py`).
- `dataset.py` — generator Monte Carlo (physics-first domyślnie, `--ecu limit` opcjonalnie).
- `compare.py` — tabela metryk dla wariantów (nozzle/SOI/boost/fuel) w jednym punkcie.
- `validation.py` — runner walidacji: `validation/reference_points.yaml`
  (punkty ALH) + `--map-grid` (siatka z map ECU).
- `gui.py` — panel Tk (tryby, presety, zapis/odczyt JSON).

## Konwencje

- Jednostki SI wszędzie w kodzie; `bar`/`mbar` tylko jawnie oznaczone w metrykach
  (patrz `docs/IO_CONTRACT.md`). "mg/suw" = masa na cylinder na suw.
- Kąty wału w stopniach, TDC = 0, BTDC = ujemne (konwersja z map: dodatnie BTDC
  w pliku → ujemne w modelu).
- Determinizm: seedowany RNG w `dataset`/`perception`; testy nie losują bez seed.
- Zależności: core = numpy/scipy/pyyaml/coolprop/fluids/matplotlib (piny w
  `requirements.txt`); ML osobno (`requirements-ml.txt`). Polityka pinów:
  `docs/WORKFLOW.md` §5.

## Testy i jakość

- `tests/` — 137 testów unittest (geometria, termodynamika, spalanie, hydraulika,
  mapy, percepcja, transient, walidacja trendów, regresje CLI).
- Bramki CI (`.github/workflows/ci.yml`): testy + `python -m virtual_tdi --help`
  + `import virtual_tdi` + smoke run `--mode full ... --no-plot`.
- Lokalnie: `python -m unittest discover -s tests -p "test_*.py" -v`
  (patrz `AGENTS.md`).
