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

## Warsztat tunera (co-jeśli)

Porównanie wariantów osprzętu/kalibracji na jednym punkcie pracy —
odpowiedź na pytania typu "co się stanie po założeniu końcówek 0.205":

```
python -m virtual_tdi compare --rpm 1900 --fuel-mg 36 \
  --variant stock \
  --variant nozzles_0.205:nozzle-diameter=0.205 \
  --variant timing_plus2:soi-offset=-2.0
```

Wypisuje tabelę: torque / moc / IMEP / peak-P / BSFC / EGT / czas trwania
wtrysku / wałek turbo dla każdego wariantu. Uwaga: przy stałej komendowanej
dawce zmiana końcówki zmienia szybkość/fazowanie wtrysku (ścieżka
hydrauliczna), nie masę paliwa — różnice vs stock są fizycznie małe; łącz
z `fuel-mg`/`boost-bar`, by badać granice wariantu.

## Walidacja

Porównanie symulacji z punktami referencyjnymi ALH 90 KM (patrz
`docs/validation_report.md` i TODO.md Faza 1):

```
python -m virtual_tdi validate
```

## Quickstart

1) Zainstaluj zależności z `requirements.txt` w swoim środowisku.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Opcjonalne narzędzia ML/DL i kalibracji (nieużywane przez rdzeń symulatora) są w `requirements-ml.txt`.

2) Sprawdź CLI:

```
python -m virtual_tdi --help
```

## Run

3) GUI (pełny panel z zakładkami dla wszystkich parametrów CLI — tryby full/closed/transient,
presety, zapis/wczytywanie konfiguracji JSON, podgląd wyjścia na żywo):

`python -m virtual_tdi gui`

Konfiguracje GUI zapisywane są jako JSON i można je wczytać ponownie w GUI
(lub przekazać ręcznie przez CLI — GUI pokazuje pełne polecenie w logu przed uruchomieniem).

4) Pełny cykl 720° (gazowymiana + sprężanie + spalanie + rozprężanie + wydech):

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
- - `--hrr-model`: `auto` (domyślna — wybiera `vp37_main`, gdy w CWD jest `skok_tloczka_vp37_de110.csv`, w przeciwnym razie `wiebe`), `wiebe`, `vp37_main`, `hydraulic_profile` (profil wtrysku z modelu 1D iglicy/linii; pilot spala się jako Wiebe, profil main normalizowany do zadanej dawki).
- Jeśli masz `skok_tloczka_vp37_de110.csv`, możesz też ustawić `--hrr-model vp37_main`, żeby kształt wydzielania ciepła main był oparty o kształt dm_fuel/dθ z VP37 (pilot nadal Wiebe). W `cycle.csv` pojawia się `dm_fuel_main_mg_per_deg`.
- Jeśli masz `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv` i `Mapa_EGR___interpolowana_mapa_MAF.csv`, tryb `--ecu limit` ogranicza IQ przez smoke limiter (na podstawie MAF target z mapy EGR) i zapisuje `maf_target_mg_per_stroke` oraz `smoke_iq_max_mg_per_stroke` w `metrics.txt`.
- Jeśli masz `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv`, w `metrics.txt` pojawia się `boost_target_mbar_abs` (oraz opcjonalnie `--use-boost-map` ustawia `p_intake` jako ciśnienie absolutne: `boost_target_mbar_abs / 1000` bar abs — mapy boost traktujemy jako ciśnienie absolutne, spójnie w CLI i datasecie).
- Backendy fizyki: `--thermo-backend coolprop` (domyślny — CoolProp musi być zainstalowany przy `--strict-backends`, patrz quickstart), `--flow-backend fluids` (domyślnie `simple`).
- Mapy ECU, profil VP37 i profil zaworów są wykrywane względem katalogu bieżącego (CWD) — uruchamiaj z root repo albo podaj ścieżki przez `--soi-map/--n146-map/--vp37-cam/--valve-table`.
- ~~Ograniczenie modelu: masa paliwa nie jest doliczana do masy ładunku~~ — **naprawione** (Faza 2.B.2): spalone paliwo wchodzi do bilansu masy ładunku zsynchronizowane z HRR; termika mieszaniny γ(T,x) z ułamkiem spalin (Faza 2.B.1).
- Opóźnienie zapłonu: `--ignition-delay arrhenius|fixed_deg` (dla `fixed_deg` ustaw `--ignition-delay-deg`).

## Tests

`python -m unittest discover -s tests -p "test_*.py" -v`

## CI

CI działa na GitHub Actions (Python 3.12) i uruchamia testy z katalogu `tests`.

## Tryb transient (MVEM)

Symulacja pracy silnika w czasie: governor PI steruje dawką (IQ), wał korbowy ma bezwładność, dolot podąża za celem boost z opóźnieniem turbo (stała czasowa 1. rzędu). W każdym kroku czasowym liczony jest pełny cykl 720°.

`python -m virtual_tdi --mode transient --rpm 1500 --rpm-start 1450 --rpm-target 1500 --load-torque-nm 80 --load-step-s 3 --transient-end-s 8 --transient-dt-s 0.1 --out out`

Uwaga: kroku czasowego transient nie należy powiększać powyżej ~0.1 s — jawny Euler całkowania wałka korbowego (inercja 0.35 kg·m²) traci wtedy stabilność. Dawka paliwa jest ograniczona szybkością zmiany `dq_drop_rate_s` (mg/s), co modeluje bezwładność pompy VP37.

Wyniki:
- `out/transient.csv` (rpm, IQ, moment hamowniczy, obciążenie, moc, p_intake, IMEP, peak pressure w czasie)
- `out/transient.png` (4 panele: rpm / IQ / momenty / ciśnienie dolotu)

Parametry strojenia: `--gov-kp`, `--gov-ki`, `--inertia-kg-m2`, `--turbo-tau-s`, `--boost-target-bar`.

## Wydajność (backend CoolProp)

Własności CoolProp (cp, cv, gamma, p(rho,T)) są tablicowane na siatce (T, log p) i (T, log rho) przy pierwszym użyciu (budowa ~3 s), potem lookup bilinearny w czystym Pythonie. Pełny cykl 720° z backendem coolprop: ~1 s (wcześniej ~70 s), błąd interpolacji < 0.5%.

## Co dalej (kolejne etapy)
- Turbo/boost: mapy sprężarki/turbiny + dynamika wałka turbo (obecnie: bilans mocy lub lag 1. rzędu).
- Warstwa ECU (EDC15): percepcja (czujniki, filtry, opóźnienia) i strojenie.
- Kalibracja governorów transient na dane pomiarowe.

- VP37 “głębiej”: tłoczek, fala ciśnienia, iglica/dysza, dwie fazy otwarcia.
