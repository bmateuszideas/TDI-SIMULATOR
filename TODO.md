# TODO — plan rozwoju projektu (na bazie review ×2, stan: `16021de`, main)

> Struktura: Faza 0 (higiena + rozbieżności) → Faza 1 (walidacja i kalibracja)
> → Faza 2 (fizyka domykająca) → Faza 3 (ML/DL).
> To jest jedyne źródło planu — po wykonaniu pozycji odhacz `x` i dopisz commit/PR.
>
> Legenda: `[ ]` do zrobienia, `[x]` zrobione. Każda pozycja ma kryterium ukończenia (AC).

---

## FAZA 0 — Higiena i rozbieżności (tanie, 1–2 dni, zamyka review)

### 0.A Konflikty danych źródłowych ("source of truth")

- [x] **0.A.1 Ujednolicić średnice zaworów (D1)**
  - Kanon: `engine_reference_sources.yaml` (ssący 35.95 mm, wydechowy 31.45 mm, wznios 8.5 mm).
  - Poprawić `docs/sources/specs_with_sources.md` §3 (dziś: 34.0/29.0 mm, ~9.0 mm — sprzeczne z kanonem).
  - Sprawdzić, czy `docs/PARAMETRY_SILNIKA.md` jest zgodny (dziś: tak).
  - AC: `grep -rn "34.0\|29.0" docs/ docs/sources/specs_with_sources.md` nie zwraca średnic zaworów; testy geometrii zielone.

- [x] **0.A.2 Rozstrzygnąć masy posuwiste (D2)**
  - Przyjąć 745 g (YAML: 440+120+40+145) jako kanon.
  - `reciprocating_mass_kg=0.73` w `virtual_tdi/full_cycle.py:58` → 0.745 ALBO usunąć parametr jako martwy.
  - Decyzja: zostawić parametr (plan: siły inercyjne w przyszłości) czy usunąć (YAGNI)?
    → zostawiamy + komentarz w YAML, usuwamy z `coupled.py` przenoszenie, jeśli nieużywane.
  - AC: jedna wartość masy w YAML/kodzie; `grep -rn "0.73\|750 g"` czysty.

- [x] **0.A.3 Przenieść temperatury ścian do YAML (D3)**
  - Dziś hardcoded: `models.py:152-154` (head 500 K, piston 550 K, liner 450 K).
  - Dodać do `engine_reference_sources.yaml` (sekcja heat transfer) + obsługa w `config_loader.py`.
  - Dodać CLI/GUI parametry (np. `--wall-temp-head-k` itd.) — spójne z resztą kontraktu parametrów.
  - AC: zmiana temperatury możliwa z YAML/CLI bez edycji kodu; test jednostkowy na odczyt z config.

### 0.B Dokumentacja nieaktualna

- [x] **0.B.1 Odświeżyć `docs/ROADMAP_CYFROWY_DUCH.md` §1 (R1/D4)**
  - Przenieść do "zrobione": kolektory dynamiczne, fala 1D w przewodzie, dynamika iglicy, model ścian (3 powierzchnie), model opóźnienia zapłonu z cap.
  - Zostawić jako otwarte: turbo (mapy+dynamika), mieszaniny spalin, percepcja ECU, walidacja na danych referencyjnych.
  - AC: ROADMAP §1 zgodny z CHECKLIST (żadnej pozycji zaznaczonej [x] w checklist opisanej jako "brak" w roadmap).

- [x] **0.B.2 Docstring `virtual_tdi/__init__.py` (D6)**
  - Zamienić "starts with a practical MVP: 0D closed-cylinder cycle" na opis stanu faktycznego
    (pełny cykl 720°, kolektory, VP37 hydraulika, ECU maps, transient, dataset, GUI).
  - AC: docstring odzwierciedla 4 tryby pracy.

- [x] **0.B.3 Uporządkować dokumenty w root repo (R5)**
  - Przenieść do `docs/sources/`: `docs/sources/kompletna_lista_z_danymi_SCALONA.md`,
    `docs/sources/kompletna_lista_z_danymi_rozszerzona.md`, `docs/sources/kompletna_lista_z_danymi_rozszerzona_pelna.md`,
    `docs/sources/uzupelniona_lista_z_danymi_i_zrodlami.md`, `docs/sources/specs_with_sources.md`,
    `docs/sources/SPECYFIKACJA MATEMATYCZNA SOLVERA_ 1.9 TDI COGENERATION ENGINE.md`,
    `docs/sources/tabela_danych_pochodnych_i_bezposrednich.md`.
  - `docs/history/RAPORT_IMEP_I_KATALOG.md` → `docs/history/` (już ma nagłówek "historyczny").
  - Zaktualizować wszystkie ścieżki w README/docs (linki do przeniesionych plików).
  - AC: `git mv` + wszystkie linki działają (grep po starych ścieżkach czysty); testy i CI zielone.

### 0.C Konflikty konfiguracji / kodu

- [x] **0.C.1 Związać defaulty `DatasetConfig` z CLI dataseta (D8)**
  - Dziś: dataclass (`dataset.py:66,72`) = `simple`/`scipy`; CLI defaults = `coolprop`/`rk4`.
  - Rozstrzygnięcie: jedna para defaultów (rekomendacja: `simple`/`rk4` — szybkość i determinizm
    generatora; coolprop do analiz pojedynczych cykli).
  - AC: dataclass i CLI mają identyczne defaulty; test porównujący oba źródła defaultów.

- [x] **0.C.2 Zaudytować oś IQ w `Mapa_BOOST*.csv` (R2)**
  - Kod ostrzega: wartości > 60 mg/suw (np. 85.0) niefizyczne.
  - Zweryfikować jednostki pliku (może to mg/stroke × inna baza, może złą kolumna).
  - Jeśli CSV błędne → poprawić; jeśli poprawne → udokumentować zakres w
    `docs/BASELINE_MAPY_ECU_I_OSPRZET.md` i wyciszyć/uszczegółowić warning.
  - AC: brak UserWarning przy smoke run `--use-boost-map` ALBO wyjaśnienie w docs.

- [x] **0.C.3 Zdefiniować politykę pinningów zależności (D10)**
  - `requirements.txt` (`==`) vs `pyproject.toml` (`>=`) — świadoma decyzja:
    app (requirements) pinnie, biblioteka (pyproject) zakresowo.
  - Zapisać politykę w `docs/WORKFLOW.md` §Dependencies.
  - AC: docs opisują politykę; requirements i pyproject zgodne z polityką.

- [x] **0.C.4 Drobiazgi README (D10)**
  - Literówka "Opoznienie zaplonu" (sekcja spalania?), powtórzona numeracja "2)".
  - AC: README czytany bez błędów numeracji.

### 0.D Higiena repo i procesu

- [ ] **0.D.1 Scalić PR #12 (Dependabot: lightgbm 4.5.0→4.6.0)** — tylko `requirements-ml.txt`, niskie ryzyko.
  - AC: PR scalony, CI zielone.

- [ ] **0.D.2 Usunąć nieaktualne gałęzie**
  - `CODEX-LOCAL*` (2 szt.), `vibe/gui-rozbudowa` (scalona przez #10).
  - AC: `git branch -r` bez nieaktualnych gałęzi (po konsultacji z właścicielem — usunięcie na GitHub).

- [ ] **0.D.3 Tag `v0.2.0` zgodnie z `docs/WORKFLOW.md`**
  - `pyproject.toml` deklaruje v0.2.0, a w repo nie ma ani jednego taga.
  - AC: tag `v0.2.0` na commicie po Fazie 0; (opcjonalnie GitHub Release z changelogiem).

- [x] **0.D.4 Opcjonalnie: `requirements-dev.txt`** (AGENTS.md o nim wspomina, nie istnieje).
  - AC: plik istnieje z dev-toolingiem (np. lint) LUB usunąć wzmiankę z AGENTS.md.

---

## FAZA 1 — Walidacja i kalibracja (fundament wizji, najwyższa wartość)

> Cel: przejść z "model spójny wewnętrznie" na "model wiadomo-jakie-błądzi".
> Do tej pory nie istnieje ŻADEN test "czy wynik zgadza się z rzeczywistością".

### 1.A Zestaw walidacyjny

- [x] **1.A.1 Zebrać punkty referencyjne ALH 90 KM**
  - 3–5 punktów: np. 1500 / 3000 / 4000 rpm, pełne obciążenie + 1 punkt częściowego.
  - Źródła: VW SSP 198, dane hamowniane ALH 90 KM, Heywood (trendy BSFC/EGT), ewentualne
    publikacje o 1.9 TDI CHP (jest `SPECYFIKACJA...COGENERATION`).
  - Dla każdego punktu: zakres docelowy IMEP / peak-P / EGT / BSFC / λ.
  - AC: `validation/reference_points.yaml` z 3–5 punktami + źródła każdej wartości.

- [x] **1.A.2 Moduł `virtual_tdi/validation.py` (lub pakiet `validation/`)**
  - Runner: dla punktu referencyjnego uruchamia full cycle, porównuje metryki z zakresami,
    raportuje pass/fail + odchyłki.
  - CLI: `python -m virtual_tdi validate --reference validation/reference_points.yaml`.
  - AC: polecenie działa, raport czytelny (tabela: metryka / sym / ref / delta / status).

### 1.B Kalibracja (parametry stroić tak, aby minimizować błąd na punktach 1.A)

- [x] **1.B.1 Skalibrować FMEP (A/B/C)** — B=0.12 bar/krpm, C=0.02 bar/bar (Heywood/Millington-Hartles); test transientu bounds poszerzony
  - Dziś A=1 bar flat, B=C=0 → systematyczny błąd momentu hamowniczego przy małych dawkach.
  - Źródło wyjściowe: empiryczne zależności FMEP od RPM/peak-P (Heywood rozdz. 13, Millington–Hartles).
  - AC: B/C ≠ 0 z uzasadnieniem źródłowym; brake torque w punktach referencyjnych w zakresie.

- [ ] **1.B.2 Skalibrować wymianę ciepła**
  - `w_mult` (dziś 6) + temperatury ścian (po 0.A.3 już konfigurowalne).
  - Cel: EGT i peak-P w zakresach referencyjnych.
  - AC: test regresji trendów EGT/peak-P na punktach 1.A (z tolerancją ±X%, X ustalić po zebraniu danych).

- [x] **1.B.3 Dodać BSFC do metryk** — dodane (poprawiona jednostka: g/kWh), IO_CONTRACT zaktualizowany
  - `brake_power_kw_est` już jest → brakuje `bsfc_g_per_kwh`.
  - Dodać do `full_cycle` metrics + `annotate_metrics` + `docs/IO_CONTRACT.md`.
  - AC: `bsfc_g_per_kwh` w metrics.txt; IO_CONTRACT zaktualizowany; test jednostkowy.

- [x] **1.B.4 Zbadać nadmierny IMEP** — wnioski w docs/validation_report.md; główna przyczyna porażek full-load: turbo coupling (p_intake 0.94 vs 1.8 bar) → Faza 2.A
  - Dziś: IMEP 8.6 bar @ 20 mg NA (1500 rpm) — realnie ALH ~5–6 bar.
  - Podejrzani: `w_mult`, FMEP, masa paliwa nie w ładunku (~4%, udokumentowane w README), γ powietrza.
  - Po 1.B.1–1.B.2 powtórzyć porównanie; jeśli błąd > 15% — wykonać analizę wrażliwości i udokumentować.
  - AC: wpis w `docs/validation_report.md` (lub podobnym) z wyjaśnieniem głównych przyczyn odchyłki.

### 1.C Testy walidacyjne jako regression gates

- [x] **1.C.1 Testy trendów IMEP/EGT/BSFC (domyka pola CHECKLISTY)**
  - Nie sztywnych wartości (model kalibrowany), a zakresy/trendy: monotoniczność IMEP vs dawka,
    EGT rośnie z obciążeniem, BSFC z minimum w środku zakresu obciążeń.
  - AC: testy w `tests/test_validation_trends.py`; zielone w CI; CHECKLISTA odhaczona.

- [x] **1.C.2 Odhaczyć w CHECKLIST odpowiadające pola**
  - "Testy trendów IMEP/EGT/BSFC po zmianach" + "Zestawy porównawcze: P-theta, IMEP, EGT, BSFC".
  - AC: CHECKLISTA zgodna ze stanem faktycznym.

---

## FAZA 2 — Fizyka domykająca (kolejność wg wpływu na realizm)

> Tożsamość projektu (decyzja planistyczna, przyjęta): **(A) wirtualny warsztat co-what-if
> jako cel nadrzędny; (B) fabryka datasetów ML jako produkt uboczny** — bo dataset
> dziedziczy każdą słabość fizyki (nieskalibrowane FMEP/walls → zaraża `out_` kolumny).

### 2.A Turbo (M5 — największa dziura dzisiejszego modelu)

- [x] **2.A.1 Mapy sprężarki/turbiny zamiast stałych sprawności** — turbo_map_gt1749v.yaml + virtual_tdi/turbo_map.py (bilinear, clipping); `--turbo` podpięte do CLI (było martwą flagą!); fix krytyczny: coupling nie przekazywał fuel_mg do iteracji
  - Źródło map: publikowane mapy K03 (ALH ma K03) — GT-Power/producent/literatura.
  - Format: klasa 2D podobna do `edc_maps.py` (interpolacja + clipping do choke/surge).
  - AC: `--turbo` używa map; test na 2–3 znanych punktach map (PR/eff na krawędziach zakresu).

- [x] **2.A.2 Dynamika wałka turbo**
  - Bilans momentu bezwładności: `dω/dt = (P_t − P_c)/(J·ω)`.
  - Zastąpić iteracyjną relaksację (`turbo-iters`) prawdziwą dynamiką w trybie transient
    (dziś: lag 1. rzędu na p_intake — lepsze, ale nie sprzężone z masą wałka).
  - AC: test odpowiedzi skokowej (spool-up time rzędu sekund, nie natychmiastowe PR).

### 2.B Termika mieszanin

- [x] **2.B.1 γ(T, x) blend powietrze/spaliny** — GasModel z burned_fraction (cp offset +110 J/kgK wg Heywood Ch. 3); cylinder: EGR+burnt, wydech: x=1
  - Dziś: CoolProp backend = czyste "Air" — nie mieszanina spalin.
  - Krok 1: liniowy/cp-mixing model γ jako funkcja T i ułamka spalin x.
  - AC: test własności (γ mieszaniny między γ_powietrze a γ_spaliny, poprawny trend z T).

- [x] **2.B.2 Masa paliwa w bilansie ładunku** — dm_fuel/dθ = dQ/LHV zsynchronizowane z HRR; governor PI re-strojenie (kp 0.10→0.05, ki 0.06→0.03)
  - Dodać masę wtryskniętego paliwa do masy ładunku w Momencie wtrysku (full_cycle).
  - AC: bilans masy zamyka się z paliwem; README sekcja "znane ograniczenia" odchudzona; test.

- [ ] **2.B.3 (Opcja, droższe) CoolProp z mieszaniną** — tylko jeśli 2.B.1 niewystarczające.

### 2.C Percepcja ECU (M6)

- [x] **2.C.1 Model czujników: opóźnienia, filtry (1 rzędu), szum/bias** — virtual_tdi/perception.py (SensorModel: lag+delay+bias+noise; PerceptionLayer rpm/MAP/EGT); podpięte do governor pętli (perception.enabled)
  - Dziś: mapy ECU czytają prawdziwe wartości bez opóźnień.
  - Parametry: delay EGT (rzędu sekund), delay MAP, szum MAF — z źródłami lub explicit assumptions.
  - AC: klasa `SensorModel` + test (przepływ sygnału, opóźnienie widoczne w śladzie).

- [x] **2.C.2 Pętle regulacji zamiast statycznych map** — BoostPidConfig (PID na boost error → ER VNT, anti-windup) w transient; fix bisekcji PR poza gridem mapy
  - PID na boost i IQ sprzężone z fizycznym rdzeniem (po 2.A — bez turbo dynamiki nie ma sensu).
  - AC: test transient z pętlą boost closed-loop stabilny (bez oscylacji PR).

---

## FAZA 3 — ML/DL (dopiero po Fazie 1; dane muszą być najpierw wiarygodne)

- [ ] **3.1 Zdefiniować cel ML** — surrogate IMEP/BSFC? silnik sugestii kalibracyjnych
  (manifest §9)? klasyfikacja wariantu osprzętu po sygnale? — decyzja przed jakąkolwiek pracą.
- [ ] **3.2 Przyspieszyć generator datasetów** — multiprocessing / backend `simple` jako
  default (dziś: 5000 próbek ≈ 1.5 h na coolprop). Benchmark przed/po w docs.
- [ ] **3.3 Wersjonowanie datasetów** — schemat nazewnictwa + hash konfiguracji generatora
  w metadanych pliku wyjściowego.
- [ ] **3.4 Baseline model** — po 3.1: prosty model (np. gradient boosting na `hw_*` + rpm + IQ)
  z walidacją train/test; `requirements-ml.txt` już czeka.
- [ ] **3.5 Promocja (B) do pełnoprawnego produktu** — dopiero gdy Faza 1 potwierdzi,
  że błąd systematyczny fizyki < akceptowalny dla celu ML.

---

## Walidacja map-driven (obszar roboczy ECU)

- [x] Siatka punktow z map ECU (RPM x IQ, limit SmokeLimitera jako gorna dawka)
- [x] Feedforward z fabrycznej mapy BOOST jako sufit couplingu turbo (`boost_ceiling_pa`)
- [x] `python -m virtual_tdi validate --map-grid` — 12/12 PASS (odchyly -2 do -14%)
- [ ] (gdy poprawny plik EGR) walidacja MAF z mapy EGR na tej samej siatce

## Kryteria zgodności z manifestem (check na koniec każdej fazy)

- Brak "magicznych" parametrów bez źródła → po Fazie 0: audit `grep` stałych liczbowych
  w `virtual_tdi/` vs YAML/docs.
- Jawne równania dla każdego efektu → każda nowa fizyka = równanie w docstring + test.
- Model krokowy "kąt po kącie" z pełnym bilansem masy/energii → testy sanity już są; utrzymać.
- Rozdzielenie warstw: geometria / fizyko-chemia (bez full-chem) / inteligencja — utrzymać architekturę.

---

## Zrobione przed tym planem (kontekst, nie do odhaczania)

- Pełny cykl 720° z dynamicznymi kolektorami, fala 1D VP37, dynamika iglicy, model ścian,
  cap na opóźnienie zapłonu, governor PI transient, mapy ECU z walidacją, GUI, CI 96 testów,
  fixy fizyki z PR #11/#13 (Woschni 40×, blow-up delay, masa wtrysku, zgodność backendów).
