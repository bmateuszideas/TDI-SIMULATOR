# Produkt: Virtual TDI — cyfrowy bliźniak 1.9 TDI (ALH)

Ten dokument definiuje **cel produktu** (po przeglądzie i przeprojektowaniu).
Zastępuje rozproszone opisy w `README.md`, `TODO.md` i manifeście
`CYFROWY_DUCH_FUNDAMENTALNE_ZALOZENIA.md` jedną, spójną definicją.

## Cel produktu (jedno zdanie)

> **Virtual TDI to white-box cyfrowy bliźniak silnika VW 1.9 TDI ALH (pompa VP37):
> wirtualny warsztat tunera i diagnosty, którego rdzeń fizyczny jest walidowany
> na fabrycznych mapach ECU i punktach referencyjnych ALH, a którego drugim
> produktem jest fabryka danych "z fizyki" (physics-first) dla ML/DL.**

Manifestowe uzasadnienie ("cyfrowy duch"): żadnych czarnych skrzynek — każdy efekt
ma jawne równanie, każdy parametr ma źródło (`engine_reference_sources.yaml`,
`docs/PARAMETRY_SILNIKA.md`).

## Dla kogo (persony)

| Persona | Potrzeba | Powierzchnia produktu |
|---|---|---|
| Tuner / mechanik | "co się stanie po założeniu końcówek 0.205?" bez rozkręcania silnika | `compare`, `gui`, flagi fault-injection |
| Diagnosta (VCDS) | odtworzenie wzorca usterki z loga w modelu | `vcds_logs.py` (`classify`), fault-injection (`--boost-leak-frac`, `--maf-underread-frac`, `--egr-fraction`) |
| Inżynier kogeneracji (CHP @ 1500 rpm) | wiarygodna prognoza pracy w stałym punkcie, test paliw alternatywnych | `simulate` (full/transient), `validate`, `--fuel svo/methanol` |
| Badacz ML/DL | wiarygodne dane treningowe "z fizyki", nie z map | `dataset` (physics-first, `--ecu off`) |
| Recenzent / student | sprawdzenie, że model "wie, jakie błędy robi" | `validate` (3 punkty ALH + siatka map), `docs/validation_report.md` |

## Powierzchnie produktu (CLI)

```
python -m virtual_tdi --mode full ...     # symulacja: cykl 720°, closed, transient (MVEM)
python -m virtual_tdi gui                 # panel Tk: wszystkie parametry, presety, JSON
python -m virtual_tdi compare ...         # warsztat what-if: warianty osprzętu/kalibracji
python -m virtual_tdi validate            # walidacja: punkty ALH 90 KM (3/3 PASS), --map-grid (12/12)
python -m virtual_tdi dataset ...         # generator danych syntetycznych (physics-first lub ECU-first)
```

Każda powierzchnia ma osobny kontrakt I/O: `docs/IO_CONTRACT.md`.

## Rdzeń fizyczny (co modeluje)

- Geometria układu korbowego z desaxage: `V(θ)`, `dV/dθ` (`geometry.py`).
- Termodynamika 0D z `γ(T, x)` (blend powietrze/spaliny) i stratami ciepła
  (Woschni uproszczony, 3 powierzchnie ścian) — `thermo.py`, `heat_transfer.py`.
- Spalanie Double-Wiebe (pilot + main) z opóźnieniem zapłonu (Arrhenius z capem)
  lub HRR z profilu hydraulicznego VP37 — `combustion.py`.
- Pełny cykl 720° z dynamicznymi kolektorami i gazowymianą przez zawory
  (model kryzy, przepływy odwrotne, EGR) — `full_cycle.py`, `flow.py`.
- Wtrysk: profil krzywki VP37 DE110, hydraulika linii (opóźnienie SOI),
  dynamika iglicy, dwufazowość pilot/main — `vp37_cam.py`, `vp37.py`,
  `hydraulics.py`, `injection.py`.
- Turbo: mapy sprężarki/turbiny GT1749V + dynamika wałka (bilans momentu
  bezwładności) + feedforward z fabrycznej mapy BOOST — `turbo_map.py`,
  `coupled.py`, `turbo.py`.
- Warstwa ECU: fabryczne mapy SOI / N146 / SmokeLimiter / EGR / BOOST
  (`edc_maps.py`, `soi_map.py`, `n146_map.py`), percepcja czujników
  (opóźnienia, filtry, szum, bias — `perception.py`), governor PI + PID boost
  w transientze (`transient.py`, `controller.py`).
- Masa wtryskiwanego paliwa wchodzi do bilansu masy ładunku (zsynchronizowane z HRR).

## Metryki sukcesu (stan aktualny, main @ `6558cb8`)

- **Testy:** 137 testów jednostkowych zielonych (`python -m unittest discover -s tests`).
- **Walidacja vs rzeczywistość:** `python -m virtual_tdi validate` → 3/3 PASS
  (ALH 90 KM: peak-torque, rated-power, part-load; tolerancje 10–25%),
  `validate --map-grid` → 12/12 PASS na siatce z fabrycznych map ECU.
  Raport i znane odchyłki: `docs/validation_report.md`.
- **CI:** GitHub Actions (Python 3.12): testy + bramki jakości
  (`--help`, import, smoke run) — `.github/workflows/ci.yml`.

## Poza zakresem (non-goals)

- Pełna kinetyka chemiczna (full-chem) — celowo wyłączona (manifest §1 roadmapy).
- Symulacja w czasie rzeczywistym / HIL.
- Inne silniki niż baseline ALH — ale konfiguracja jest w YAML, więc rozszerzenie
  to kwestia danych, nie kodu.
- Trenowanie modeli ML w tym repo — repo dostarcza tylko dane (`dataset`);
  narzędzia ML są opcjonalne (`requirements-ml.txt`).
- Kalibracja na prawdziwych logach P-θ / EGT z hamowni — czeka na dane
  (kolejny poziom wierności, patrz `docs/validation_report.md` §7).

## Wersjonowanie i wydania

Semver (`pyproject.toml`), wydania tagowane z `main` zgodnie z `docs/WORKFLOW.md`.
Bieżąca wersja: `python -m virtual_tdi --version`.
