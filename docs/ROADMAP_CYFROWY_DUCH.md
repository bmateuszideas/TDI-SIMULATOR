# Roadmap: dopasowanie projektu do manifestu "Cyfrowy Duch"

Ten dokument spisuje rozbieznosci i kolejnosc prac tak, aby projekt byl zgodny z manifestem.
Pelna kinetyka chemiczna (full-chem) nie jest wymagana na tym etapie.

## 1) Rozbieznosci vs manifest (stan obecny, main @ 6558cb8)
Zrobione (domkniete w PR #10-#23; walidacja 3/3 PASS + map-grid 12/12 - patrz docs/validation_report.md):
- Kolektory dynamiczne (0D, bilanse masy/energii, stan EGR) - gazowymiana z oryficzem 0D przez zawory, z przeplywami odwrotnymi.
- Hydraulika wtrysku: fala cisnienia 1D (lumped line) w przewodzie + dynamika iglicy (NeedleConfig); HRR z profilu hydraulicznego; wtrysk wielofazowy pilot/main.
- Wymiana ciepla: Woschni uproszczony z modelem scian (denko/tlok/tuleja, 3 powierzchnie); temperatury scian kalibrowane na punktach ALH (600/650/550 K, w YAML z source) i konfigurowalne z YAML/CLI.
- Opuznienie zaplonu Arrhenius z capem sanity (40 deg) + diagnostyka SOC/delay w metrykach.
- Turbo: mapy sprezarki/turbiny GT1749V + dynamika walka (J*domega/dt) + feedforward z fabrycznej mapy BOOST (Faza 2.A; `validate --map-grid` 12/12).
- Termika mieszanin: gamma(T,x) blend powietrze/spaliny; masa paliwa w bilansie ladunku zsynchronizowana z HRR (Faza 2.B).
- ECU: model percepcji czujnikow (opoznienia, filtry, szum, bias) + petle regulacji (governor PI, PID boost -> VNT z anti-windup) w transientze (Faza 2.C).
- Walidacja: zestaw referencyjny ALH 90 KM (`python -m virtual_tdi validate` -> 3/3 PASS) + siatka map ECU (12/12) + testy trendow IMEP/EGT/BSFC (Faza 1).
- Warsztat tunera: `python -m virtual_tdi compare` (warianty osprzetu/kalibracji w jednym punkcie pracy).

Nadal otwarte:
- Geometria/kinematyka: czesc danych to estymacje (oznaczone w docs/PARAMETRY_SILNIKA.md), nie wszystkie maja twarde zrodla pomiarowe.
- Kalibracja na prawdziwych danych pomiarowych (P-theta trace, EGT z hamowni) - kolejny poziom wiernosci (docs/validation_report.md §7).
- Mapa EGR: plik w repo uszkodzony (stala ~850) - walidacja MAF z mapy EGR wstrzymana do poprawnego zrzutu (docs/MAPY_ECU_KONWENCJE.md §4).
- Faza 3 (ML/DL): cel ML, przyspieszenie i wersjonowanie datasetow, baseline model (TODO.md).
- Dane i parametry: audyt "magicznych" wartosci bez jawnego zrodla (TODO.md, kryteria zgodnosci na koniec fazy).
- Full-chem: celowo poza zakresem na tym etapie.

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
- Profil VP37: `skok_tloczka_vp37_de110.csv`
- Dodatkowe zrodla: `docs/sources/specs_with_sources.md`

## 2) Priorytety (bez full-chem)
1. Twarde dane i zrodla:
   - Kompletny katalog parametrow, ich pochodzenie i jednostki.
   - Oznaczenie, co jest pomiarem, a co kalibracja.
2. Geometria i kinematyka:
   - Zastapienie domyslnych wartosci danymi pomiarowymi.
   - Testy regresyjne dla V(theta), dV/dtheta, lift table itp.
3. Gazowymiana i kolektory:
   - Wprowadzenie stanow kolektorow (masa/energia).
   - Straty cisnienia, temperatura w kolektorach, masa rezydualna.
4. Wymiana ciepla:
   - Model scian z bilansami energii, osobne powierzchnie (denko/tuleja/glowica).
   - Weryfikacja z EGT i trendami IMEP/BSFC.
5. Hydraulika i wtrysk:
   - Fale cisnienia w przewodzie, dynamika iglicy.
   - Wtrysk wielofazowy liczony z modelu hydraulicznego, nie tylko Wiebe.
6. Turbo:
   - Mapy sprezarki/turbiny lub model parametryczny z dynamika.
7. ECU (warstwa 3):
   - Model percepcji: opoznienia, filtry, bledy czujnikow.
   - Sterowanie jako petle regulacji (nie tylko mapy).

## 3) Kamienie milowe
M1: Zrodla danych + walidacja geometrii
- katalog parametrow z linkami do plikow zrodlowych
- testy geometrii i zaworow jako twarda walidacja

M2: Kolektory + masa rezydualna
- stany kolektorow i bilanse masy/energii
- spadki cisnienia i temperatura w kolektorach

M3: Wymiana ciepla "sciany"
- model scian i walidacja trendow termicznych

M4: Hydraulika wtrysku
- fala cisnienia + iglica
- wtrysk liczony z hydrauliki

M5: Turbo
- mapy lub model parametryczny + dynamika

M6: ECU "percepcja"
- czujniki, filtry, opoznienia, petle regulacji

## 4) Kryteria zgodnosci z manifestem
- Brak "magicznych" parametrow bez zrodla.
- Jawne rownania dla kazdego efektu.
- Model krokowy "kat po kacie" z pelnym bilansem masy/energii.
- Rozdzielenie warstw: geometria, fizyko-chemia (bez full-chem), inteligencja.
