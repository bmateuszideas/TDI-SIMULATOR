# Roadmap: dopasowanie projektu do manifestu "Cyfrowy Duch"

Ten dokument spisuje rozbieznosci i kolejnosc prac tak, aby projekt byl zgodny z manifestem.
Pelna kinetyka chemiczna (full-chem) nie jest wymagana na tym etapie.

## 1) Rozbieznosci vs manifest (stan obecny)
- Geometria/kinematyka: czesc danych ma wartosci domyslne, nie wszystkie maja twarde zrodla pomiarowe.
- Gazowymiana: przeplyw przez zawory jako oryficz 0D, brak modeli kolektorow i fal cisnienia.
- Termodynamika: idealny gaz + opcjonalny CoolProp, ale bez mieszanin spalin/paliwa.
- Wymiana ciepla: korelacja Woschni (uproszczona, empiryczna).
- Hydraulika wtrysku: uproszczone modele VP37 i przewodu, brak dynamiki iglicy i fal cisnienia.
- Turbo: prosty bilans mocy bez map sprzezarki/turbiny i bez dynamiki.
- ECU: mapy i proste reguly, brak modelu percepcji (czujniki, opoznienia, filtry).
- Dane i parametry: czesc "magicznych" wartosci bez jawnego zrodla.

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
- Dodatkowe zrodla: `specs_with_sources.md`

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
