# Review kodu i dokumentacji — raport końcowy

Zakres: pełny przegląd repo na `main` @ `6558cb8` (kod `virtual_tdi/`, `tests/`,
`validation/`, dokumentacja root + `docs/`, CI, konfiguracja pakietu).

## Metoda (co zostało empirycznie zweryfikowane)

- `python -m unittest discover -s tests -p "test_*.py"` → **137 testów, OK** (54 s).
- Bramki CI z `.github/workflows/ci.yml`: `python -m virtual_tdi --help`,
  `python -c "import virtual_tdi"`, smoke run
  `--mode full --rpm 1500 --fuel diesel --fuel-mg 20 --no-plot` → OK.
- `python -m virtual_tdi validate` → **3/3 PASS** (ALH 90 KM).
- `python -m virtual_tdi compare --rpm 1900 --fuel-mg 36 --variant stock
  --variant nozzles_0.205:nozzle-diameter=0.205` → tabela metryk OK.
- Inspekcja kodu: warstwy, kontrakt I/O (`docs/IO_CONTRACT.md` vs `full_cycle.py`/
  `solver.py`/`transient.py`/`dataset.py`), spójność dokumentów między sobą.

## Ustalenia — kod

| # | Severity | Lokalizacja | Ustalenie | Status |
|---|---|---|---|---|
| C1 | medium | `virtual_tdi/__main__.py:10-22`, `cli.py:_make_argparser` | Subkomendy `dataset`/`compare`/`validate`/`gui` były niewidoczne w `--help` (dyspatch przez `sys.argv[1]`); brak `--version`. Produkt nie był "odkrywalny" z CLI. | **Naprawione**: epilog z listą subkomend + `--version` (`__init__.__version__`, fallback 0.2.0 = `pyproject.toml`); testy w `tests/test_cli_regression.py` |
| C2 | low | `virtual_tdi/__init__.py` | Brak `__version__` mimo wersji w `pyproject.toml` (0.2.0) i braku tagów w repo (TODO 0.D.3). | **Naprawione** (częściowo): `__version__`; tagowanie zostaje procesem wg `docs/WORKFLOW.md` (wymaga decyzji właściciela) |
| C3 | low | root repo | `app-debug.apk` (18 KB, Android debug build) — obcy artefakt binarny w repo Pythonowego symulatora. | **Otwarty** (nie usuwam cudzych plików bez zgody): zalecane usunięcie lub przeniesienie poza repo |
| C4 | info | `virtual_tdi/full_cycle.py:58` | `reciprocating_mass_kg=0.745` zgodne z kanonem YAML (TODO 0.A.2 zamknięte). | OK |
| C5 | info | `virtual_tdi/` | Podział `vp37.py` (linia) / `vp37_cam.py` (krzywka) / `hydraulics.py` (dysza+iglica) jest warstwowy, nie duplikacją — opisany w `docs/ARCHITECTURE.md`. | OK |

## Ustalenia — dokumentacja

| # | Severity | Lokalizacja | Ustalenie | Status |
|---|---|---|---|---|
| D1 | high | `docs/ROADMAP_CYFROWY_DUCH.md` §1 | Sekcja "Nadal otwarte" wymieniała jako otwarte: mapy turbo + dynamikę wałka, masę paliwa w ładunku, percepcję ECU, pętle regulacji, zestaw walidacyjny — wszystko to jest zaimplementowane i zwalidowane (`validation_report.md` §6–§10, `validate` 3/3 PASS, map-grid 12/12). Roadmapa przeczyła CHECKLIŚCIE i raportowi. | **Naprawione**: §1 zaktualizowany do stanu faktycznego |
| D2 | high | `docs/CHECKLIST_CYFROWY_DUCH.md` | Niezaznaczone pozycje faktycznie zrobione (percepcja, pętle regulacji, dynamika turbo w `coupled.py`, testy trendów — jednocześnie zaznaczone niżej w tym samym pliku, jawne zakresy map, źródła zaworów); wewnętrzna sprzeczność. | **Naprawione**: checkboxy zgodne ze stanem faktycznym |
| D3 | medium | `README.md` | README był listą ficzerów, bez definicji celu produktu i person; dokumenty wymienione tylko 3 z 8+. | **Naprawione**: README przepisany product-first, wszystkie komendy zweryfikowane; nowe `docs/PRODUCT.md` + `docs/ARCHITECTURE.md` |
| D4 | medium | `TODO.md` | Nagłówek odnosił się do starego stanu (`16021de`, "CI 96 testów" — jest 137); pozycja 1.B.2 (kalibracja ścian) była nieodfajkowana mimo że jest zrobiona i udokumentowana (`validation_report.md` §7, YAML 600/650/550 K z `source`). | **Naprawione**: nagłówek + 1.B.2 |
| D5 | low | `docs/PARAMETRY_SILNIKA.md:18`, `engine_reference_sources.yaml:43` | Źródło "kompletna_lista_z_danymi.md" wskazywało nieistniejący plik (rzeczywisty: `docs/sources/kompletna_lista_z_danymi_SCALONA.md`). | **Naprawione** |
| D6 | info | `docs/validation_report.md` | Sekcje §2–§5 to historia stanów pośrednich (FAIL full-load przed Fazą 2.A) — oznaczone jako takie, aktualny stan w §7–§10 (3/3 PASS). | OK (kontekst historyczny) |

## Ustalenia — proces/konfiguracja

| # | Severity | Lokalizacja | Ustalenie | Status |
|---|---|---|---|---|
| P1 | info | `pyproject.toml` vs `requirements.txt` | Polityka pinów (app: `==`, biblioteka: `>=`) udokumentowana w `docs/WORKFLOW.md` §5 — zgodna. | OK |
| P2 | info | `docs/WORKFLOW.md` §6, `.gitignore` | Artefakty runów (`out/`, `*.png`) nie są commitowane — OK. | OK |
| P3 | low | TODO 0.D.1–0.D.3 | Otwarte pozycje procesowe: merge PR #12 (Dependabot, `requirements-ml.txt`), czyszczenie starych branchy, tag `v0.2.0` — decyzje właściciela, poza zakresem tego PR. | Otwarte (świadomie) |

## Wnioski projektowe (re-design celu produktu)

1. Cel produktu sformułowano ponownie jako definicję w `docs/PRODUCT.md`:
   cyfrowy bliźniak ALH = wirtualny warsztat tunera/diagnosty + walidowany rdzeń
   fizyczny + fabryka danych physics-first dla ML. Cztery powierzchnie CLI
   (`simulate`/`gui`, `compare`, `validate`, `dataset`) odpowiadają personom.
2. Dokumentacja przepisana product-first: nowy `README.md`, `docs/PRODUCT.md`,
   `docs/ARCHITECTURE.md` (mapa modułów per warstwa); stale dokumenty
   (ROADMAP/CHECKLIST/TODO) doprowadzone do zgodności z kodem.
3. Kod: minimalne, bezpieczne zmiany UX produktu (`--version`, widoczne
   subkomendy w `--help`) + testy regresyjne; 137/137 testów zielonych,
   bramki CI zielone. Żadnych zmian w fizyce — model był już walidowany (3/3).

## Co celowo NIE było zmieniane

- Fizyka i kalibracja (walidowana; zmiany wymagałyby nowych danych pomiarowych).
- `app-debug.apk` i otwarte pozycje procesowe TODO (0.D.1–0.D.3) — własność właściciela.
- `docs/sources/` i `docs/history/` — surowe źródła danych, archiwum (bez zmian treści).
