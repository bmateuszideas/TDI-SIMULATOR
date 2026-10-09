# Konwencje map ECU (kanon odczytu plików CSV)

Dokument opisuje znaczenie osi i danych każdej mapy kalibracyjnej sterownika
1.9 TDI (ALH, VP37, EDC). Źródło ustaleń: opis właściciela repo (który odczytał
mapy z ECU tego silnika) — niniejszy dokument jest kanonem interpretacji
dla parserów w `virtual_tdi/edc_maps.py`, `soi_map.py`, `n146_map.py`.

Wspólna konwencja plików:
- Nagłówek (pierwszy wiersz) = **oś IQ (mg/suw)** (lub MAF — patrz SmokeLimiter).
- Pierwsza kolumna = **oś RPM**.
- Komórki = wartość mapy dla (RPM, IQ).
- Pliki "interpolowane" = oryginalne mapy ECU przeinterpolowane na siatkę
  regularną.

## 1. SOI — "Mapa Kąta Początku Wtrysku (SOI)... Table 1.csv"

- Osie: RPM (0–5355, pierwsza kolumna) × IQ (0–40 mg/suw, nagłówek).
- Dane: **kąt początku wtrysku w stopniach obrotu wału przed TDC (BTDC)**
  — wartości dodatnie = przed TDC.
- Ostatnia kolumna "Źródło" = metadane (ignorowana przez parser).
- Logika: przy obrotach X i dawce Y mg/suw wtrysk musi nastąpić Z° BTDC,
  aby zapewnić optymalne okno czasowe wtrysku (czas = kąt/ω: wyższe RPM →
  więcej wyprzedzenia dla tej samej dawki).
- Konwersja w modelu: BTDC dodatnie w pliku → ujemne w konwencji modelu
  (`soi_deg_model_convention`).

## 2. N146 — "Mapa napięcia pompy N146... Table 1.csv"

- Osie: RPM (0–4494) × IQ (0–51 mg/stroke).
- Dane: **napięcie w mV** dla nastawnika (elektrozaworu) dawki paliwa VP37.
- Logika: przy obrotach X, dla uzyskania Z mg/suw paliwa, nastawnik musi
  otrzymać od ECU napięcie z komórki (mV).
- Interpretacja fizyczna (quasi-mapa czasu trwania): napięcie steruje czasem
  otwarcia tłoczka; przy wyższych RPM ten sam czas odpowiada mniejszemu kątowi
  — dlatego w pliku mV maleją z RPM przy stałej dawce, a rosną z dawką.
- Offset przy 0 rpm (~1387 mV dla 0.4 mg) = fizyka zaworu (minimalny prąd).

## 3. SmokeLimiter — "SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv"

- Osie: MAF (300–853 mg/suw powietrza, nagłówek) × RPM (861–5355, pierwsza
  kolumna).
- Dane: **maksymalna dawka paliwa (mg/suw)** dla danego (RPM, MAF).
- Logika: przy obrotach X i dostępnej masie powietrza Y mg/suw możesz wtrysnąć
  maksymalnie Z mg paliwa, aby utrzymać założoną przez producenta lambdę
  (spalić paliwo bez generowania dymu/sadzy).
- Użycie przez ECU: dwustopniowe — najpierw wyznacza dostępny MAF (pomiar /
  cel z mapy EGR), potem tnie IQ do min(zadane, limit z mapy).
- Górna granica MAF ~850 mg/suw = pełny przepływ przy zamkniętym EGR.

## 4. EGR→MAF — "Mapa_EGR___interpolowana_mapa_MAF.csv"

- Zamierzona logika (wg właściciela): przy obrotach X i dawce Y mg/suw
  **reguluj zaworem EGR tak, aby faktyczna masa powietrza (MAF) = Z mg/suw**
  (zadany MAF dla zamkniętej pętli EGR, nie pozycja zaworu).
- EGR działa tylko przy małych obciążeniach w określonych partiach obrotów;
  przy dużych obciążeniach mapa ma pełny przepływ (850 mg/suw = EGR zamknięty).
- **UWAGA: plik w repo jest uszkodzony** — niemal w całości wypełniony stałą
  850.0, ostatni wiersz pocięty. Nie należy na nim opierać walidacji;
  parser `EGRMafTargetMap2D` zwraca z niego w praktyce stałą ~850 (pełny
  przepływ). Do poprawienia, gdy dostępny będzie poprawny zrzut.

## 5. BOOST — "Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv"

- Osie: RPM (21–4746, pierwsza kolumna) × IQ (0–45 mg/suw, nagłówek).
- Dane: **bezwzględne ciśnienie w kolektorze dolotowym (mbar abs)**, tj.
  ~1000 mbar atmosfery + nadciśnienie ze sprężarki. Odczyt: 1298 mbar =
  298 mbar doładowania; 1950 mbar = 950 mbar doładowania.
- Logika: przy obrotach X i dawce Y mg/suw potrzebujesz Z mbar ciśnienia
  dolotu (zadana wartość dla regulacji VNT).
- Naprawy pliku (udokumentowane, na podstawie potwierdzenia właściciela):
  - nagłówek miał o dwa zera za dużo w kolumnach ≥ 20 (błąd rzędu wielkości
    z OCR/eksportu): `2000→20, 2500→25, ..., 4000→40`,
  - ostatnia kolumna `8500` to błąd OCR — poprawnie **45 mg/suw**.

## Konsekwencje dla modelu

1. Łańcuch ECU w symulatorze: SOI (kąt) + N146 (mV↔IQ) + SmokeLimiter
   (MAF→max IQ) + BOOST (cel ciśnienia dolotu) — zgodny z opisaną logiką.
2. Mapa BOOST jako zadana wartość dla pętli boost (docelowo: `BoostPidConfig`
   z profilem z mapy zamiast płaskiego targetu — TODO.md).
3. EGR: do czasu uzyskania poprawnego pliku model zakłada pełny przepływ
   (EGR zamknięty) w punktach pełnego obciążenia — zgodne z fizyką (przy
   pełnym obciążeniu EGR i tak jest zamknięte).
