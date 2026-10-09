# Diagnostyka TDI (VAG) — kanon logów VCDS

Źródło: procedura diagnostyczna TDI (VAG) dostarczona przez właściciela repo
(forumowy standard logowania VAG-Com / VCDS). Ten dokument jest kanonem
interpretacji logów diagnostycznych i mostem między językiem diagnostów
a modelem (`virtual_tdi/vcds_logs.py`).

## Procedura logowania (skrót)

- Odczyt błędów: Engine-01 → 02-Fault Codes.
- **Logi statyczne** (biega jałowy, temp. płynu ≥ 80°C): bloki 000, 001, 003,
  004, 007, 013, 014, 018, 023 (Meas. Blocks 08); Basic Settings 04: 000, 003
  (EGR cykluje, ~50 s), 004 (pompa przestawia się cyklicznie; start gdy obie
  wartości na LATE; NIE dla PD), 011 (kierownice VTG cyklicznie, ~50 s).
- **Logi dynamiczne** (III bieg, temp. ≥ 80°C, dwie osoby!): bloki 000, 001,
  003, 004, 008, 010, 011; start przy 1500 rpm, stop przy 4200 rpm.

## Semantyka bloków (kanon diagnostyczny)

| Grupa | Pola | Znaczenie / kryterium sprawności |
|---|---|---|
| 000 poz. 3 | MAF (surowa, 0-255) | przy pełnym obciążeniu = 255 |
| 003 | RPM / MAF żądana / MAF rzeczywista / EGR duty | żądana == rzeczywista; idle ~230-310 mg/R przy EGR aktywnym |
| 007 | temp. paliwa / oleju / dolotu / płynu (G62) | zimny: wszystkie ≈ temp. otoczenia; rozgrzany: G62 vs G2 (grupa 003 w Instruments) rozróżnia termostat vs czujnik |
| 008 | RPM / IQ życzenie / IQ limit momentu / IQ limit dymienia | sprawność: życzenie ≥ dymienie > moment; **IQ via MAF najniższa ⇒ G70 (przepływomierz) źle mierzy** |
| 010 | MAF / atm (f96) / ciśnienie doładowania / przepustnica | poz. 4 = 100% (pedał do oporu); MAF wg wymaganego dla silnika |
| 011 | RPM / ciśnienie dolotu żądane / rzeczywiste / N75 duty | żądane == rzeczywiste; **rzeczywiste > żądane = przeładowanie (notlauf, DTC 00575)**; < żądane = turbina/dynamika spalin/podciśnienie |

## Kluczowe zależności diagnostyczne (właściciel)

1. **G70 (MAF) jest fundamentem**: zanim ocenisz turbinę/EGR, potwierdź, że
   MAF mierzy poprawnie — bo smoke limiter (IQ via MAF, grupa 008 poz. 4)
   tnie dawkę wg MAF; zły MAF = zaniżona moc bez usterki mechanicznej.
2. **Hierarchia pętli**: ECU zwiększa N75 → boost rośnie → MAF rośnie →
   limity (moment/dymienie) przycinają IQ. Przeładowanie = N75/kierownice
   VTG wadliwe; niedoładowanie = turbina (szczelinowanie), wydech (katalizator),
   podciśnienie.
3. **EGR**: grupa 003 statyczna — MAF żądana == rzeczywista przy duty ~40-43%.
   Basic Settings: OFF (zamknięty) MAF ≥ 400 mg/R; ON (otwarty) ~180 mg/R.
   Niedomknięty = spaliny w dolocie (twarda praca); nieotwarty = za mało
   recyrkulacji (tylko emisje/głośność, dynamika OK).
4. **mg/R vs mg/suw**: w logach VCDS "mg/R" (na obrót wału). Dla 4-suwnego
   silnika suw = 2 obroty, więc mg/suw = 2 × mg/R w wartościach średnich;
   w mapach ECU konwencja to mg/suw (patrz MAPY_ECU_KONWENCJE.md).

## Interpretacja logów zdrowego vs zdegradowanego silnika

- **Mapy ECU = stan idealny (zdrowy silnik)** — kanon walidacji modelu.
- **Logi = stan rzeczywisty** — często z auta z usterką (ludzie logują, gdy
  coś nie gra). Dlatego logi są materiałem **diagnostycznym** (fault-injection:
  który wariant usterki w modelu odtwarza wzorzec z loga), a nie referencją
  kalibracji.
- Wyjątek: log z potwierdzonego zdrowego auta = dodatkowa walidacja
  (wartości powinny pokrywać się z mapami — patrz logi przykładowe:
  grupa 011 dynamiczna, żądane ≈ rzeczywiste w zakresie 2100-2230 mbar).

## Most do symulatora (`vcds_logs.py`)

- `parse_group003/008/010/011(text)` — parser tabel logów VCDS.
- `to_operating_points(rows)` — ekstrakcja punktów pracy (RPM, IQ, boost
  żądany/rzeczywisty, MAF) do porównania z modelem.
- Diagnostyczne reguły powyżej zaimplementowane jako klasyfikator
  `classify(rows)`: zwraca hipotezy usterek (przeładowanie / niedoładowanie /
  EGR niedomknięty / EGR nieotwarty / MAF podejrzany) wg kryteriów z tabel.
