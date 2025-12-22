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
