# Dataset ML (Virtual 1.9 TDI)

Ten repo ma wbudowany generator danych syntetycznych do uczenia ML/DL: `python -m virtual_tdi dataset ...`.

## Co dostajesz w CSV

- Każdy wiersz to 1 punkt pracy (pełny cykl 720° lub zadana liczba cykli).
- Kolumny wejściowe (`rpm`, `p_intake_bar_used`, `fuel*`, `soi*`, `iq*`, `nozzle*`, itp.) + **geometria** (`geom_*`).
- Etykiety/wyjścia są spłaszczone jako `out_*` i pochodzą z `res.metrics` symulatora (np. `out_peak_pressure_bar`).
- `ok=1` oznacza poprawną symulację; przy `--on-error record` błędy lądują w wierszu z `ok=0` + `error_type`/`error_msg`.

## Tryby (sterowanie wejściami)

- **Fizyka-first (bez map ECU)**: `--ecu off` i losowane/ustawiane zakresy (IQ, boost, SOI offset).
- **ECU-first**: `--use-soi-map`, `--use-n146-map`, `--use-boost-map` oraz `--ecu report|limit` – generator korzysta z map z repo (jeśli istnieją).

## Mechaniczne “what-if” (geometria per-wiersz)

Włącz: `--mech sample` i podaj zakresy `--*-min/--*-max`. Wtedy każdy wiersz ma osobną geometrię, a w CSV pojawią się kolumny `geom_*`.

Przykład (konserwatywne rozrzuty):

`python -m virtual_tdi dataset --n 2000 --rpm-min 1500 --rpm-max 1500 --ecu off --p-intake-min 1.0 --p-intake-max 1.8 --fuels diesel,svo,wvo --mech sample --gasket-mm-min 1.45 --gasket-mm-max 1.75 --protrusion-mm-min 0.95 --protrusion-mm-max 1.15 --bowl-cm3-min 20.0 --bowl-cm3-max 26.0 --out data/chp_mech.csv`

## Metadane / reprodukowalność

Opcjonalnie zapisuj JSON obok CSV (schema + hash plików wejściowych + config generatora):

`python -m virtual_tdi dataset --n 5000 --rpm-min 1500 --rpm-max 1500 --ecu off --out data/chp.csv --meta-out data/chp.meta.json`

## Tipy pod dataset dla kogeneratora (CHP)

- Zacznij od stałej prędkości: `--rpm-min 1500 --rpm-max 1500`.
- Zwiększ szybkość kosztem dokładności: `--step-deg 5.0` (lub większe), `--cycles 1`.
- Jeśli losujesz szerokie zakresy (paliwa/mechanika), użyj `--on-error record` albo `--on-error skip`.

