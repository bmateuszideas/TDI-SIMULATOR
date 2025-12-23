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

Jeśli chcesz generować dane stricte “z fizyki” (do ML/DL), uruchamiaj dataset bez map (`python -m virtual_tdi dataset ...` domyślnie nie używa map) albo w symulacji ustaw `--ecu off` i steruj wejściami jawnie.

## Szybki start

1) Zainstaluj zależności z `requirements.txt` w swoim środowisku.

GUI (prosty panel do uruchamiania symulacji):

`python -m virtual_tdi gui`

2) Pełny cykl 720° (gazowymiana + sprężanie + spalanie + rozprężanie + wydech):

`python -m virtual_tdi --mode full --rpm 1500 --fuel diesel --fuel-mg 20 --out out`

Dobór dawki paliwa pod zadaną moc (prosty “governor” dla CHP):

`python -m virtual_tdi --mode full --rpm 1500 --fuel diesel --target-brake-kw 10 --fuel-mg-min 2 --fuel-mg-max 40 --out out`

Sterowanie dawką przez napięcie N146 (jeśli masz mapę napięcie↔IQ w repo):

`python -m virtual_tdi --mode full --rpm 1500 --n146-mv 2500 --out out`

Tryb ECU (limity dymienia + EGR + target boost z map):

`python -m virtual_tdi --mode full --ecu limit --rpm 1500 --n146-mv 2500 --out out`

Użycie target boost jako warunku brzegowego dolotu (tymczasowo, bez dynamiki turbo):

`python -m virtual_tdi --mode full --ecu limit --use-boost-map --rpm 1500 --n146-mv 2500 --out out`

Turbo coupling (bilans mocy turbina→sprężarka, iteracyjne dopasowanie p_intake):

`python -m virtual_tdi --mode full --turbo --turbo-iters 5 --rpm 1500 --n146-mv 2500 --out out`

Generowanie danych syntetycznych (do ML/DL) z symulatora:

Fizyka-first (bez map ECU, boost losowany):

`python -m virtual_tdi dataset --n 5000 --rpm-min 1500 --rpm-max 1500 --ecu off --p-intake-min 1.0 --p-intake-max 1.8 --fuel-temp-min 20 --fuel-temp-max 90 --iq-basis volume --nozzles 0.184,0.205,0.216,0.230 --step-deg 1.0 --out data/synthetic.csv`

ECU-first (używa map jeśli są w repo):

`python -m virtual_tdi dataset --n 5000 --rpm-min 1500 --rpm-max 1500 --ecu limit --use-soi-map --use-n146-map --use-boost-map --fuel-temp-min 20 --fuel-temp-max 90 --iq-basis volume --nozzles 0.184,0.205 --step-deg 1.0 --out data/synthetic_ecu.csv`

Wiecej o datasetach ML (geometria per-probka `--mech sample`, obsluga bledow `--on-error`, metadane `--meta-out`): `docs/DATASET_ML.md`.

Sweep kąta wtrysku (SOI main):

`python -m virtual_tdi --mode full --rpm 1500 --fuel diesel --fuel-mg 20 --soi-main-sweep -14:-2:1 --out out`

Cykl zamknięty (tylko sprężanie/spalanie/rozprężanie):

`python -m virtual_tdi --mode closed --rpm 1500 --fuel diesel --fuel-mg 20 --out out`

Wyniki:
- `out/cycle.csv`
- `out/metrics.txt`
- `out/p_t.png`, `out/heat.png`, `out/pv.png` (oraz dla full: `out/mass.png`)

## Co jest zaimplementowane

- Geometria układu korbowego z desaxage (offset): `V(θ)` oraz `dV/dθ`.
- Termodynamika 0D z `γ(T)` i stratami ciepła (Woschni simplified).
- Spalanie Double‑Wiebe (pilot + main) z opóźnieniem zapłonu (model Arrhenius / stałe).
- Pełny cykl 720° z gazowymianą: przepływ ściśliwy przez zawory (model kryzy).
- Jeśli istnieje plik `profil_krzywek_4cylindry.md`, solver używa go jako tabeli wzniosu zaworów (zamiast sinusów).
- Uproszczony wpływ VP37/paliwa: opóźnienie hydrauliczne przewodu (`--line-m`) przesuwa SOI.
  - Przykład: `--line-m 0.4` (ok. 2–3° opóźnienia przy 1500 RPM, zależnie od paliwa).
- Jeśli istnieje `Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv`, a nie podasz `--soi-main`, SOI main jest brane z tej mapy (oś: RPM i IQ mg/suw).
- Jeśli istnieje `Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv`, w `metrics.txt` pojawia się `n146_mv_est`, a opcja `--n146-mv` pozwala wyznaczyć IQ z napięcia.
- Jeśli istnieje `skok_tloczka_vp37_de110.csv`, a `--duration-model` to `auto` (domyślnie), czas trwania wtrysku main jest wyliczany z profilu krzywki VP37 (funkcja IQ i cylindra), a w `metrics.txt` pojawia się `duration_main_deg`.
- Jeśli masz `skok_tloczka_vp37_de110.csv`, możesz też ustawić `--hrr-model vp37_main`, żeby kształt wydzielania ciepła main był oparty o kształt dm_fuel/dθ z VP37 (pilot nadal Wiebe). W `cycle.csv` pojawia się `dm_fuel_main_mg_per_deg`.
- Jeśli masz `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv` i `Mapa_EGR___interpolowana_mapa_MAF.csv`, tryb `--ecu limit` ogranicza IQ przez smoke limiter (na podstawie MAF target z mapy EGR) i zapisuje `maf_target_mg_per_stroke` oraz `smoke_iq_max_mg_per_stroke` w `metrics.txt`.
- Jeśli masz `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv`, w `metrics.txt` pojawia się `boost_target_mbar_abs` (oraz opcjonalnie `--use-boost-map` ustawia `p_intake` jako ciśnienie względem atmosfery: `boost_target_mbar_abs - p_amb`).
- Opcjonalne backendy fizyki: `--thermo-backend coolprop`, `--flow-backend fluids`.
- Opoznienie zaplonu: `--ignition-delay arrhenius|fixed_deg` (dla `fixed_deg` ustaw `--ignition-delay-deg`).

## Testy

`python -m unittest discover -s tests -p "test_*.py"`

## Co dalej (kolejne etapy)

- Kolektory i EGR jako stany dynamiczne (zamiast stałych warunków brzegowych).
- VP37 “głębiej”: tłoczek, fala ciśnienia, iglica/dysza, dwie fazy otwarcia.
- Turbo/boost: solver turbina–kompresor (mapy lub model parametryczny).
- Warstwa ECU (EDC15) i strojenie.
