# DANE TECHNICZNO-FIZYCZNE (SCALONE) - VW 1.9 TDI (ALH/1Z/AHU)

_Wygenerowano: 2025-12-23 02:59:03_

Cel: **jeden** plik jako wspolna baza danych techniczno-fizycznych dla symulatora.

## 1) Zrodla prawdy / priorytet danych

- `engine_reference_sources.yaml` jest **kanonicznym** zrodlem liczb i jednostek uzywanych przez kod.
- Pliki wejsciowe profili i map (uzywane przez kod):
  - `profil_krzywek_4cylindry.md` -> `virtual_tdi/lift_table.py` (valve lift)
  - `skok_tloczka_vp37_de110.csv` -> `virtual_tdi/vp37_cam.py` (profil VP37)
  - Mapy ECU `.csv` (SOI/N146/Smoke/EGR/Boost) -> `virtual_tdi/*_map.py`, `virtual_tdi/edc_maps.py`

## 2) Geometria silnika (z `engine_reference_sources.yaml`)

- Srednica cylindra (bore): `79.5` mm
- Skok tloka (stroke): `95.5` mm
- Dlugosc korbowodu (rod): `144.0` mm
- Offset cylindra/desaxage: `0.5` mm

W kodzie (patrz `virtual_tdi/geometry.py`) pozycja tloka i objetosc cylindra sa liczone z uwzglednieniem offsetu (desaxage).

## 3) Komora spalania / CR / Vc

Definicje (spojne z dokumentacja w repo i implementacja):

- Pole tloka: `A = pi * (bore/2)^2`
- "Clearance thickness" nad tlokiem: `t_clearance = max(0, gasket_thickness - piston_protrusion)`
- Obj?tosc szczelinowa: `Vc = bowl_volume + head_recess_volume + A * t_clearance`
- Stopien sprezenia: `CR = (Vs + Vc) / Vc`, gdzie `Vs = A * stroke`

Wartosci wejsciowe (z `engine_reference_sources.yaml`):
- `bowl_volume`: `21.95` cm3
- `head_recess_volume`: `0.8` cm3
- `gasket_thickness`: `1.63` mm
- `piston_protrusion`: `1.05` mm

Wartosci pochodne (wyliczone z powyzszego):
- `A_piston`: `0.00496391` m2
- `Vs` (na cylinder): `474.05` cm3
- `t_clearance`: `0.58` mm
- `Vc`: `25.63` cm3
- `CR` (z powyzszego Vc): `19.497`

Uwaga o rozbieznosciach: w starszych notatkach w root pojawialy sie przyblizone Vc/CR; traktuj je jako archiwum (przeniesione do `SMIETNIK/`).

## 4) Rozrzad (profile zaworow)

- `profil_krzywek_4cylindry.md` jest **uzywany przez kod** (parser + interpolacja w `virtual_tdi/lift_table.py`).
- `profil_krzywek_walek.md` (w tym repo: `profil_krzywek_wałek.md`) **nie jest wykryty jako uzywany przez kod**; zostaje jako material referencyjny.

W praktyce kod zamienia tabele lift(?) na funkcje przez interpolacje (to jest ta "geometryczna funkcja" w sensie obliczeniowym).

## 5) Pompa VP37 (profil krzywki / skok tloczka)

- `skok_tloczka_vp37_de110.csv` jest **uzywany przez kod**: `virtual_tdi/vp37_cam.py` wczytuje skok tloczka jako funkcje kata pompy i buduje z tego ksztalt wtrysku / czas trwania wtrysku.

## 6) Mapy ECU (dane sterownika)

Pliki `.csv` w root sa traktowane jako dane warstwy ECU (referencja/limity), a nie jako "fizyka":
- SOI: `Mapa K?ta Pocz?tku Wtrysku (SOI) dla silnika 1.9 TDI - Table 1.csv` -> `virtual_tdi/soi_map.py`
- N146: `Mapa napi?cia pompy N146 - VW Golf IV ALH 90hp - Table 1.csv` -> `virtual_tdi/n146_map.py`
- Smoke limiter: `SmokeLimiter___interpolowana_mapa_maksymalnego_IQ.csv` -> `virtual_tdi/edc_maps.py`
- EGR MAF target: `Mapa_EGR___interpolowana_mapa_MAF.csv` -> `virtual_tdi/edc_maps.py`
- Boost target: `Mapa_BOOST___interpolowana_mapa_ci_nienia_do_adowania.csv` -> `virtual_tdi/edc_maps.py`

## 7) Co zostalo scalone i przeniesione do `SMIETNIK/`

Ten plik zast?puje rozproszone listy/tabele z root (dane + pochodne). Oryginalne pliki trafiaja do `SMIETNIK/` jako archiwum.

### Pliki przeniesione do `SMIETNIK/`

- `SMIETNIK/kompletna_lista_z_danymi_SCALONA.md`
- `SMIETNIK/kompletna_lista_z_danymi_rozszerzona.md`
- `SMIETNIK/kompletna_lista_z_danymi_rozszerzona_pelna.md`
- `SMIETNIK/uzupelniona_lista_z_danymi_i_zrodlami.md`
- `SMIETNIK/specs_with_sources.md`
- `SMIETNIK/tabela_danych_pochodnych_i_bezposrednich.md`
- `SMIETNIK/RAPORT_IMEP_I_KATALOG.md`
- `SMIETNIK/output.png`
- `SMIETNIK/NA PODSTAWIE LISTY PODAJ WSZYSTKIE DANE KTORE MO½....md`
