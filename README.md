# Virtual TDI — cyfrowy bliźniak 1.9 TDI (ALH)

White-box symulator 0D silnika **VW 1.9 TDI ALH (pompa VP37)** — "cyfrowy duch":
żadnych czarnych skrzynek, każdy efekt ma jawne równanie, każdy parametr ma źródło.

**Cel produktu** (pełna definicja w [docs/PRODUCT.md](docs/PRODUCT.md)): wirtualny
warsztat tunera i diagnosty, którego rdzeń fizyczny jest walidowany na fabrycznych
mapach ECU i punktach referencyjnych ALH 90 KM, a którego drugim produktem jest
fabryka danych "z fizyki" dla ML/DL.

Stan: 137 testów zielonych · walidacja 3/3 punktów ALH + 12/12 siatki map ECU · CI green (Python 3.12).

## Szybki start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m virtual_tdi --version
python -m virtual_tdi --help                 # wszystkie flagi symulacji + lista subkomend
```

Pierwsza symulacja (pełny cykl 720°: gazowymiana + sprężanie + spalanie + rozprężanie + wydech):

```bash
python -m virtual_tdi --mode full --rpm 1500 --fuel diesel --fuel-mg 20 --out out
# wyniki: out/cycle.csv, out/metrics.txt, out/p_t.png, out/heat.png, out/pv.png, out/mass.png
```

## Cztery zastosowania

### 1. Warsztat tunera — "co jeśli" (`compare`, GUI, fault-injection)

Porównanie wariantów osprzętu/kalibracji w jednym punkcie pracy:

```bash
python -m virtual_tdi compare --rpm 1900 --fuel-mg 36 \
  --variant stock \
  --variant nozzles_0.205:nozzle-diameter=0.205 \
  --variant timing_plus2:soi-offset=-2.0
```

Tabela: torque / moc / IMEP / peak-P / BSFC / EGT / czas wtrysku / wałek turbo per wariant.
Uwaga: przy stałej dawce zmiana końcówki zmienia szybkość/fazowanie wtrysku (ścieżka
hydrauliczna), nie masę paliwa — łącz z `fuel-mg`/`boost-bar`, by badać granice wariantu.

Fault-injection (diagnostyka): `--boost-leak-frac 0.1`, `--maf-underread-frac 0.2`,
`--egr-fraction 0.3` — fizyczna reakcja modelu na usterkę; klasyfikator wzorców
z logów VCDS: `virtual_tdi/vcds_logs.py` (kanon: [docs/DIAGNOSTYKA_VCDS.md](docs/DIAGNOSTYKA_VCDS.md)).

GUI (panel Tk, presety, zapis/odczyt konfiguracji JSON):

```bash
python -m virtual_tdi gui
```

### 2. Walidacja — "czy model wie, jakie błędy robi" (`validate`)

```bash
python -m virtual_tdi validate            # 3 punkty referencyjne ALH 90 KM → 3/3 PASS
python -m virtual_tdi validate --map-grid # siatka 12 punktów z fabrycznych map ECU → 12/12 PASS
```

Raport z analizą odchyłek: [docs/validation_report.md](docs/validation_report.md);
punkty referencyjne: `validation/reference_points.yaml`.

### 3. Symulacja pracy w czasie (`--mode transient`, MVEM)

Governor PI steruje dawką, wał ma bezwładność, turbo ma dynamikę wałka
(bilans momentu `J·dω/dt` z map GT1749V); w każdym kroku liczony pełny cykl 720°:

```bash
python -m virtual_tdi --mode transient --rpm 1500 --rpm-start 1450 --rpm-target 1500 \
  --load-torque-nm 80 --load-step-s 3 --transient-end-s 8 --transient-dt-s 0.1 --out out
# wyniki: out/transient.csv + out/transient.png (rpm / IQ / momenty / ciśnienie dolotu)
```

Krok czasowy nie większy niż ~0.1 s (jawny Euler na bezwładności wału 0.35 kg·m²).

Cykl zamknięty (tylko sprężanie/spalanie/rozprężanie):

```bash
python -m virtual_tdi --mode closed --rpm 1500 --fuel diesel --fuel-mg 20 --out out
```

### 4. Fabryka danych dla ML/DL (`dataset`)

```bash
# fizyka-first (bez map ECU, boost losowany) — domyślnie:
python -m virtual_tdi dataset --n 5000 --rpm-min 1500 --rpm-max 1500 --ecu off \
  --p-intake-min 1.0 --p-intake-max 1.8 --nozzles 0.184,0.205,0.216,0.230 --out data/synthetic.csv

# ECU-first (mapy z repo):
python -m virtual_tdi dataset --n 5000 --rpm-min 1500 --rpm-max 1500 --ecu limit \
  --use-soi-map --use-n146-map --use-boost-map --out data/synthetic_ecu.csv
```

## Mapy ECU a fizyka (ważne)

Mapy ECU w repo (SOI / N146 / SmokeLimiter / EGR / BOOST) to **warstwa sterownika
i referencja**, nie "silnik" symulatora. Są skalibrowane pod konkretny osprzęt:
końcówka `0.184 × 5`, pompa VP37 `DE110`, rozrząd z `profil_krzywek_4cylindry.md`
(patrz [docs/BASELINE_MAPY_ECU_I_OSPRZET.md](docs/BASELINE_MAPY_ECU_I_OSPRZET.md)).
Przy podmianie końcówek te mapy nie są już "tym samym ECU" — traktuj wariant
osprzętu jako cechę w danych ML. Do danych strict "z fizyki" używaj `dataset`
bez map (`--ecu off`, domyślnie) lub `--ecu off` w symulacji.
Kanon osi/jednostek map: [docs/MAPY_ECU_KONWENCJE.md](docs/MAPY_ECU_KONWENCJE.md)
("mg/suw" = na cylinder na suw; hierarchia SmokeLimiter > EGR).

## Dokumentacja

- [docs/PRODUCT.md](docs/PRODUCT.md) — cel produktu, persony, powierzchnie, non-goals, metryki sukcesu
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — mapa modułów per warstwa, przepływ danych
- [docs/IO_CONTRACT.md](docs/IO_CONTRACT.md) — kontrakt wejść/wyjść (metryki, CSV, dataset)
- [docs/WORKFLOW.md](docs/WORKFLOW.md) — dev → CI → release, polityka pinów zależności
- [docs/validation_report.md](docs/validation_report.md) — raport walidacji i znane odchyłki
- [docs/PARAMETRY_SILNIKA.md](docs/PARAMETRY_SILNIKA.md) — katalog parametrów z źródłami
- [docs/DIAGNOSTYKA_VCDS.md](docs/DIAGNOSTYKA_VCDS.md) — kanon logów VCDS i klasyfikator usterek
- [docs/ROADMAP_CYFROWY_DUCH.md](docs/ROADMAP_CYFROWY_DUCH.md), [docs/CHECKLIST_CYFROWY_DUCH.md](docs/CHECKLIST_CYFROWY_DUCH.md), [TODO.md](TODO.md) — roadmapa i plan
- [docs/REVIEW.md](docs/REVIEW.md) — pełny przegląd kodu i dokumentacji
- `docs/sources/` — surowe listy danych i źródła; `docs/history/` — raporty historyczne
- `CYFROWY_DUCH_FUNDAMENTALNE_ZALOZENIA.md` — manifest filozofii projektu

## Co jest zaimplementowane (rdzeń fizyczny)

- Geometria układu korbowego z desaxage: `V(θ)`, `dV/dθ`.
- Termodynamika 0D z `γ(T, x)` (blend powietrze/spaliny) i stratami ciepła
  (Woschni uproszczony, 3 powierzchnie ścian; temperatury z YAML/CLI).
- Spalanie Double-Wiebe (pilot + main) z opóźnieniem zapłonu (Arrhenius z capem)
  lub HRR z profilu VP37 (`--hrr-model vp37_main|hydraulic_profile|wiebe`).
- Pełny cykl 720° z gazowymianą: przepływ przez zawory (model kryzy, przepływy
  odwrotne), dynamiczne kolektory, EGR; masa paliwa w bilansie ładunku.
- Wtrysk: profil krzywki VP37 DE110 (`skok_tloczka_vp37_de110.csv`), opóźnienie
  hydrauliczne linii (`--line-m`), dynamika iglicy, pilot+main.
- Mapy ECU wykrywane względem CWD (uruchamiaj z root repo lub podaj ścieżki
  `--soi-map/--n146-map/--smoke-map/--egr-map/--boost-map/--vp37-cam/--valve-table`);
  SOI main domyślnie z mapy SOI; `--n146-mv` wyznacza IQ z napięcia N146.
- Turbo: mapy GT1749V (`validation/turbo_map_gt1749v.yaml`), dynamika wałka,
  feedforward z mapy BOOST (`--turbo`, `--use-boost-map`, `--ecu limit`).
- Percepcja ECU (opóźnienia/filtry/szum czujników) w pętli transient.
- Backendy: `--thermo-backend coolprop` (tablicowany, ~1 s/cykl) / `simple`;
  `--flow-backend fluids|simple`; `--integrator rk4|scipy`.

## Testy i CI

```bash
python -m unittest discover -s tests -p "test_*.py" -v   # 137 testów
```

CI (GitHub Actions, Python 3.12): testy + bramki jakości (`--help`, import, smoke run)
— `.github/workflows/ci.yml`. Wydania tagowane z `main` ([docs/WORKFLOW.md](docs/WORKFLOW.md)).

## Struktura repo

```
virtual_tdi/    kod pakietu (patrz docs/ARCHITECTURE.md — warstwy 1-4)
tests/          137 testów unittest
validation/     punkty referencyjne ALH + mapa turbo GT1749V + check spójności map
docs/           dokumentacja produktu (patrz wyżej)
*.csv, *.md     mapy ECU, profil VP37, profil rozrządu (dane źródłowe w root)
engine_reference_sources.yaml   źródło prawdy parametrów fizycznych (z source per parametr)
```
