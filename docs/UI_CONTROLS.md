# Kontrolki GUI w `virtual_tdi/gui.py`

Ten dokument w języku polskim opisuje wszystkie widoczne elementy interfejsu PySide6, aby było jasne, jakie dane trafiają do backendu (`core/engine_model/physics`).

## Nagłówek i pasek statusu
- **Nagłówek** – baner „1.9 TDI ALH PRO - THERMAL LAB” z podtytułem przypomina cel aplikacji.  
- **Status bar** – pod nim kilka `StatusItem`, które pokazują instancyjne stany (np. BOOST, TURBO, TEMP, FUEL, ERROR) bazując na `self.state`. Kolory od sygnalizacji alertów po stan bezpieczny.

## Panel po lewej („ENGINE PARAMETERS”)
Kontrolki po lewej przekładają się bezpośrednio na `core.build_case()` / `run_case()`:
1. **Suwak RPM** – zakres 800‑5500 obr/min; wartość prezentowana obok.  
2. **Suwak IQ** – 50‑750 mg/suw, przeliczane przez `scale=0.1`. To strzał główny dawki paliwa.  
3. **Suwak Boostu** – 1000‑2800 mbar (ciśnienie doładowania).  
4. **Spinboxy temperatur** – osobne dla temperatury dolotu i otoczenia (C).  
5. **Menu paliwa** – `diesel`, `svo`, `biodiesel`, `wvo` – zmienia obiekt `Fuel` w backendzie.  
6. **Offset SOI** – `QDoubleSpinBox` ±15° BTDC dla korekcji kąta początku wtrysku.  
7. **Model pilota** – przełącznik pomiędzy hydrauliką VP37 a stałą masą pilota.  
8. **Dawka pilota** – edytowalna (0‑5 mg/suw) przy modelu `fixed_mg`.  
9. **Presety** – przyciski „ECO”, „STAGE 1‑3”, „EXTREME”, „TOWING” ładują gotowe zestawy RPM/IQ/Boost.  
10. **Checkbox „Use physics backend”** – wybór pomiędzy szybką estymacją JS a symulacją `simulate_full_cycle()`.  
11. **RUN THERMAL SIM** – startuje wątek i wysyła aktualne ustawienia do backendu.

## Panel środkowy („DASHBOARD TABS”)
`QTabWidget` z pięcioma zakładkami:

### Zakładka „Simulation”
- **Thermal** – mierniki `ThermalCard` dla temperatur tłoka, zaworów, turbiny itp., pasek postępu EGT oraz wykres temperatury wzdłuż toru spalinowego. Z prawej lista ostrzeżeń generowanych przez `core.check_warnings()`.  
- **P-CA** – wykres ciśnienia cylindrowego vs kąt wału z krzywymi cylindryczną, dolotową, wylotową oraz markerami TDC/SOI/max.  
- **PV** – log/log pętla indykatorowa; dodatkowy label z IMEP/Work.  
- **ROHR + Injection** – dwa wykresy: ROHR i profil wtrysku (mg/deg), plus status hydrauli.  
- **Hydraulics** – przy włączonym profilu hydraulik pokazuje ciśnienie linii, lift iglicy, masowy przepływ paliwa dla lepszego debugowania VP37.

### Zakładka „ECU Maps”
- **Selektor mapy** – lista map (`soi`, `n146`, `smoke`, `egr`, `boost`) i przycisk „Reload”.  
- **Etykiety mapy i kursora** – `map_info`/`map_cursor_label`.  
- **Podgląd mapy** – `pg.ImageItem` na siatce z liniami crosshair (silnik/dwa osie).  
- **Eksport** – przyciski do CSV i PNG.  
- **Tabela mapy** – `QTableWidget` odzwierciedlający wartości siatki.  
- **Hover** – `SignalProxy` podsłuchuje ruch kursora i aktualizuje etykietę.

### Zakładki geometryczne i wynikowe
- **Geometry** – tabelka CR, Vc, Vd, przerysowany wykres objętości (wdłuż kąta).  
- **Results** – „metykowe” tabelki (np. IMEP, BSFC, Lambda, NOx) + label informujący o aktualności danych.  
- **Data Export** – przyciski eksportu wyników/JSON, zapisu konfiguracji/wyeksportowania logów.

## Panel po prawej („THERMAL STRESS ANALYSIS”)
- **Kafelki wynikowe** – power (HP), torque (Nm), lambda, NOx (ppm).  
- **Tabela marginesów bezpieczeństwa** – komponenty (tłok, zawory, turbo) pokazane z wartością, limitem i marginem.  
- **Narzędzia** – przyciski `SAVE CONFIG`, `COMPARE`, `PREDICT MAINT`, `EXPORT LOG`.  
- **Export snapshot** – przycisk do zapisu stanu GUI i wyników po obliczeniach.

## Panel predictive maintenance
Dolna część zawiera listę wpisów generowanych przez `_show_predictions()` – symulowany AI mock wskazuje przeglądy, koszty i przedział czasowy.

## Notatki końcowe
- Wszelkie suwaki/spinnery wywołują `_on_inputs_changed()` i trafiają do `_run_simulation()` → finalnie do `core.build_case()`/`run_case()`.  
- Przycisk `SAVE CONFIG`/`COMPARE` odnosi się do `self.saved_configs`, które operują na `CaseConfig`.  
- Map export i selectors podtrzymują workflow „mapy + hover + eksport” zgodnie z `Mapowanie_plik_w (1).csv`.

## Dlaczego frontend liczy ~2000 linii, a backend ~100?
1. **Interfejs musi opisać wiele widoków** – każda zakładka z wykresami, tabelkami, warningami i eksportami zajmuje kilkadziesiąt linii, bo PySide6 wymaga jawnego tworzenia widgetów i layoutów.  
2. **Zarządzanie zdarzeniami i formatowaniem** – obsługa sygnałów, crosshair’ów, tabel, eksportów, presetów i menu paliw to kaskada kodu, która w backendzie sprowadza się do prostych struktur danych i symulacji.  
3. **Backend robi „tylko” liczby** – logiczna część (symulacje, hydraulika, physics) jest skondensowana w modułach `engine_model`, `physics`, `injection`; jeden wywołanie funkcji generuje dane dla wielu widoków.  
4. **Rozdział odpowiedzialności** – GUI musi opisać każdy komponent wizualny osobno, co naturalnie mnoży linie; backend natomiast operuje na tabelach, funkcjach numerycznych i konfiguracjach.  

Ten przewodnik tłumaczy więc, dlaczego warstwa wizualna jest rozbudowana i co dokładnie przekazuje do modelu; wystarczy wskazać dane wejściowe oraz wyniki, a backend powinien je zinterpretować bez dodatkowych zmian komunikacyjnych.

## Tabela powiązań frontend → backend
Poniżej zbiorcza tabela pokazuje, którędy każda kluczowa kontrolka przesyła dane do `core` i `engine_model`, aby nie było żadnych „osamotnionych” elementów GUI.

| Kontrolka / panel | Przekazywana wartość | Jak backend wykorzystuje tę wartość |
| --- | --- | --- |
| RPM slider | `rpm` w ramach `overrides` (`_run_simulation` → `core.build_case().overrides["rpm"]`) | `SimulationConfig.rpm` – wpływa na omega w solverze i prędkość tłoka, pomaga ustalić kroki w `simulate_full_cycle`. |
| IQ slider | `fuel_mg` (mg/suw) | `SimulationConfig.fuel_mg_per_cycle_per_cyl` → determinuje energię paliwa i masę w cylindrze w `simulate_closed_cycle`. |
| Boost slider | `p_intake_bar` | `SimulationConfig.intake_pressure_pa`, używany w masie dolotu i obwodach EGR. |
| Temperatura dolotu/otoczenia | `t_intake_k`, `t_ambient_k` | Warunki brzegowe dla `physics.GasModel` (gęstość, cp/cv) i dla obwodów cieplnych (HeatTransferConfig). |
| Fuel selector / pola custom | `fuel` + ewentualne `fuel_density_kgm3`, `fuel_bulk_modulus_bar`, `fuel_lhv_mjkg` | `core.create_fuel()` wybiera odpowiedni `Fuel`; wartości trafiają do `engine_model` i `physics` (nawet `estimate_pilot_ratio`). |
| SOI offset | `soi_offset_deg` | Wstawiane do `InjectionSchedule.soi_main_deg`, zmieniające pozycję AR w symulacji. |
| Pilot model (combo + spin) | `pilot_model` (`hydraulic`/`fixed_mg`) oraz `pilot_mg` | `CaseConfig.schedule` w `core.build_schedule()` ustawia tryb wtrysku: hydrauliczny odwołuje się do `estimate_pilot_ratio`, fixed modyfikuje `InjectionSchedule.pilot_mg`. |
| Presety (ECO, Stage, Extreme, Towing) | Gotowe zestawy `rpm/iq/boost/soi` | Presety uzupełniają `overrides` zanim `core.run_case()` zbuduje `CaseConfig`. Backend widzi tylko wartości, nie nazwę presetu. |
| Checkbox „Use physics backend” | `use_backend` | Decyduje, czy `_run_simulation()` wykona lekki estimator (JS-dokładność) czy `core.run_case()` z `simulate_full_cycle`. |
| RUN THERMAL SIM | uruchamia `_run_simulation()` | Warstwa UI przekazuje zebrane dane do `core`, a backend zwraca `SimulationResult`, który trafia z powrotem do wykresów/metryk. |
| Map selector (SOI, N146, Smoke, EGR, Boost) | `map_kind`, paths | `core` ładuje odpowiadające mapy (`SOIMap2D`, `N146VoltageMap2D`, etc.) i zwraca dane (np. `soi_deg`); GUI odświeża tabelę/obraz. |
| Eksport map | aktualna `map_grid` | GUI zapisuje macierz przez helpery `core._export_map_csv/png`, backend nie liczy nowych danych. |
| Wyniki (thermals, table) | `SimulationResult.metrics`, `CaseConfig` | Wykresy/kolorowe karty i tabeli odczytują gotowe metryki (p_cyl, Pmax, NOx, λ) zwracane przez `core.run_case()`. |
| Predictive tools (save/compare/export) | `self.saved_configs`, `self.data_log` | Zapisywane `CaseConfig`/metrik w backendzie mogą być później odtworzone lub porównane w `core`. |

Każdy wiersz tej tabeli potwierdza, że żaden element UI nie został „zostawiony sam w polu walki” – wszystkie są twardo spięte z backendowymi strukturami.
