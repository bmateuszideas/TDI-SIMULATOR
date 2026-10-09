# Bazowa konfiguracja (mapy ECU i osprzęt)

Ten projekt używa kilku map ECU (SOI, N146, SmokeLimiter, EGR, Boost). Te mapy są “fabryczne”, ale **nie są uniwersalne** – zakładają konkretną konfigurację hardware.

## Mapy w repo

- `Mapa Kąta Początku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv`
  - Oś: `RPM × IQ (mg/suw)` → SOI (stopnie BTDC w pliku; w modelu konwertowane na konwencję: BTDC = wartości ujemne).
- `Mapa napięcia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv`
  - Oś: `RPM × IQ (mg/suw)` → `N146 (mV)`.
- `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv`
  - Oś: `RPM × MAF (mg/suw)` → `max IQ (mg/suw)`.
- `Mapa_EGR___interpolowana_mapa_MAF.csv`
  - Oś: `RPM × IQ (mg/suw)` → `MAF target (mg/suw)`.
- `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv`
  - Oś: `RPM × IQ (mg/suw)` → `MAP target (mbar abs)`.

## Bazowa konfiguracja, dla której mapy są sensowne

- Wtryskiwacze: końcówka `0.184 × 5` (ALH 90hp).
- Pompa VP37: krzywka/tarcza `DE110`:
  - profil skoku tłoczka: `skok_tloczka_vp37_de110.csv`
- Rozrząd / wznios zaworów:
  - tabela wzniosu: `profil_krzywek_4cylindry.md`

## Dlaczego to ważne (ML/DL i “co-jeśli”)

W praktyce “IQ (mg/suw)” w ECU i mapach jest wielkością zależną od kalibracji osprzętu (m.in. końcówki wtryskiwacza, hydrauliki i geometrii wtrysku). Jeśli podmienisz np. końcówkę na `0.205`, to:

- te same mapy SOI/N146/SmokeLimiter/EGR/Boost nie muszą już odzwierciedlać realnej pracy silnika,
- różnica w sprzęcie powinna być **jawnie oznaczona** w danych syntetycznych jako wariant konfiguracji,
- najlepsza praktyka dla ML: trenować modele na danych z wielu konfiguracji, gdzie konfiguracja jest cechą wejściową (np. `nozzle_diameter_mm`, `holes`, `vp37_cam_profile`).

W tym repo można podmieniać pliki map przez flagi CLI (`--soi-map`, `--n146-map`, `--smoke-map`, `--egr-map`, `--boost-map`) i generować osobne datasety dla różnych zestawów map/konfiguracji.

## Uwaga: mapy to warstwa ECU, nie fizyka

Mapy w repo są przede wszystkim:
- punktem odniesienia do konstrukcji/kalibracji modelu fizycznego,
- warstwą “sterownika” (Inteligencja), którą można włączyć/wyłączyć.

Do generowania danych syntetycznych “fizyka-first” użyj generatora dataset bez map (`python -m virtual_tdi dataset ...` domyślnie nie używa map ECU), albo w symulacji ustaw `--ecu off` i podawaj wejścia jawnie.

## Audyt mapy BOOST (Faza 0 / TODO.md 0.C.2)

Audyt osi `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv`:

- Konwencja pliku: nagłówek = oś IQ (mg/suw, z heurystyką ×100 dla wartości ≥ 200,
  tj. `2000`→20 mg), pierwsza kolumna = oś RPM. To zgodne z konwencją parsera
  (`BoostTargetMap2D.from_csv`).
- Zakres osi RPM w pliku: ~1000–5000 (wartości interpolowane, np. 4746, 3507, 2499).
- Zakres osi IQ w pliku: 0–40 mg/suw — fizyczny dla ALH — **plus jedna kolumna
  `8500` (→85 mg/suw)**, która jest niefizyczna dla tego silnika (max IQ SmokeLimitera
  to ~36.5 mg). Prawdopodobny błąd źródła (może miało być `4500`→45 mg albo `850`→8.5 mg).
- Dodatkowo ostatni wiersz ma RPM `21` — ewidentna anomalia danych źródłowych.

Decyzja: pliku źródłowego **nie modyfikujemy** (to dane referencyjne); parser
ostrzega (`UserWarning`) przy wartościach osi IQ > 60 mg/suw i jest to świadomy
safety-net. Punkty z anomalous axis leżą poza obszarem roboczym map (IQ ≤ ~36.5,
RPM 900–5000), więc nie wpływają na wyniki w normalnym użyciu.
Jeśli pojawi się oryginalne źródło mapy, kolumnę `8500` i wiersz `21` należy
poprawić u źródła.
