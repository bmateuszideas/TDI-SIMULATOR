# Raport: ujemny IMEP i katalog modulow

## 1) Problem z ujemnym momentem (IMEP < 0) - diagnoza

### Objawy z logu
- `out_heavy/metrics.txt` pokazal **ujemny IMEP** i **ujemny moment** mimo dawki ~35.4 mg/suw oraz boostu z mapy.
- Metryki `soc_*` i `ign_delay_*` wskazaly **zaplonnienie przesuniete o ~180 deg**, czyli spalanie po GMP i na suwie wydechu.

### Przyczyna
- To nie jest realne przesuniecie pompy o 180 deg, tylko **zbyt duze opoznienie zaplonu z modelu**.
- Opoznienie zaplonu na poziomie ~180 deg przesuwa SOC na suw wydechu.

### Konsekwencja
- Spalanie nastepuje **po GMP**, wiec calka `P * dV` staje sie ujemna -> **ujemny IMEP**.
- To nie jest blad map ECU, tylko **blad modelu zaplonu**.

### Zmiany diagnostyczne / naprawcze (juz w kodzie)
- **Zapisywanie SOC i opoznienia zaplonu** w metrykach:
  - `soc_pilot_deg_model`, `soc_main_deg_model`
  - `ign_delay_pilot_deg`, `ign_delay_main_deg`
  - `ign_delay_*_source` - wskazuje, czy wynik pochodzi z Arrheniusa czy `fixed_deg`.
- **Korekty ECU i warunki w cylindrze**:
  - korekty SOI od temperatur paliwa/cieczy, EGR, offset zaplonu,
  - udzial spalin resztkowych (`residual_frac`), EGR (`egr_frac`),
  - korekta temperatury ladunku (`charge_temp_offset_k`),
  - temperatura scian (`wall_temp_k`).

### Wniosek praktyczny
- "Przesuniecie pompy o 180 deg" naprawia objaw (czas zaplonu), ale **nie naprawia przyczyny** (model zaplonu).
- Rzeczywista korekta to **kalibracja opoznienia zaplonu** (parametry Arrheniusa lub wartosc `fixed_deg` + warunki cylindra), a nie globalny obrot pompy.

## 2) Moduly `virtual_tdi/` - opis kazdego pliku

- `virtual_tdi/__init__.py` - opis pakietu i eksport glownych klas/funkcji (full cycle, maps, hydraulika, modele).
- `virtual_tdi/__main__.py` - wejscie modulu; uruchamia CLI lub generator datasetu.
- `virtual_tdi/cli.py` - glowne CLI:
  - wczytywanie map ECU (SOI, N146, boost, smoke, EGR),
  - budowa harmonogramu wtrysku i korekty ECU,
  - uruchomienie symulacji pelnego cyklu / zamknietego cyklu,
  - sweep SOI, wyjsciowe CSV, wrazliwosci (numdifftools),
  - sprzezenie z turbo.
- `virtual_tdi/combustion.py` - modele spalania:
  - Wiebe (pilot + main) i profil VP37,
  - wyznaczanie SOC na bazie opoznienia zaplonu (Arrhenius/fixed),
  - runtime do sledzenia SOC i opoznien.
- `virtual_tdi/controller.py` - solver monotoniczny (bisekcja) uzywany do znajdowania dawki dla targetu mocy.
- `virtual_tdi/coupled.py` - iteracyjne sprzezenie turbo z pelnym cyklem (zamkniecie obiegu).
- `virtual_tdi/dataset.py` - generator datasetow syntetycznych (monte-carlo) + CLI do produkcji CSV.
- `virtual_tdi/edc_maps.py` - parsery map EDC:
  - Smoke limiter, EGR MAF target, Boost target,
  - interpolacja biliniowa.
- `virtual_tdi/flow.py` - przeplyw przez oryficz:
  - tryb prosty (idealny gaz, choked/subsonic),
  - backend `fluids` dla subsonicznego przeplywu i ekspansywnosci.
- `virtual_tdi/full_cycle.py` - pelna symulacja 720 deg:
  - konfiguracja boundary conditions, valve timing, lift table,
  - integratory RK4 oraz SciPy (Radau),
  - spalanie, wymiana ciepla, przeplywy zaworowe,
  - metryki IMEP/torque/BSFC/rod force/SOC/ignition delay.
- `virtual_tdi/geometry.py` - kinematyka korbowodu:
  - polozenie tloka, dV/dtheta, objetosc cylindra, powierzchnie wymiany ciepla.
- `virtual_tdi/heat_transfer.py` - Woschni (uproszczony) dla h(theta).
- `virtual_tdi/hydraulics.py` - uproszczona hydraulika VP37:
  - geometria dyszy/plungera, model cisnienia,
  - estymacja udzialu pilota.
- `virtual_tdi/lift_table.py` - parser tabeli wzniosu zaworow z Markdown + interpolacja.
- `virtual_tdi/models.py` - definicje danych:
  - geometria silnika, paliwo, harmonogram wtrysku,
  - konfiguracje spalania i wymiany ciepla,
  - SimulationConfig (backendy + integratory).
- `virtual_tdi/n146_map.py` - mapa N146: interpolacja IQ<->mV (forward i inverse).
- `virtual_tdi/soi_map.py` - mapa SOI: interpolacja RPM x IQ -> SOI i konwersja znaku do konwencji modelu.
- `virtual_tdi/solver.py` - symulator "closed cycle" (bez wymiany gazow), RK4/SciPy.
- `virtual_tdi/thermo.py` - termodynamika:
  - gamma/cp/cv z prostego modelu lub CoolProp,
  - gestosc i cisnienie (EOS),
  - opoznienie zaplonu (Arrhenius).
- `virtual_tdi/turbo.py` - model turbo: konfiguracja sprawnosci i przyrost PR z mocy spalin.
- `virtual_tdi/valvetrain.py` - rozrzad i przeplyw:
  - krzywa wzniosu (sinus), efektywne pole kurtyny, timing.
- `virtual_tdi/vp37.py` - hydrauliczne opoznienie wtrysku (line delay) i korekta harmonogramu.
- `virtual_tdi/vp37_cam.py` - profil krzywki VP37:
  - wczytanie z CSV, ksztalt dawki i czas wtrysku.

## 3) Testy `tests/` - opis kazdego pliku

- `tests/test_backends.py` - sprawdza backendy (fluids, CoolProp) i podstawowe wywolania.
- `tests/test_controller.py` - bisekcja dla funkcji rosnacej i malejacej.
- `tests/test_dataset.py` - generacja malego datasetu (3 rekordy) i kluczowe kolumny wyjsciowe.
- `tests/test_edc_maps.py` - parsowanie i interpolacja map Smoke/EGR/Boost na znanych punktach.
- `tests/test_full_cycle_sanity.py` - pelny cykl w trybie uproszczonym; IMEP i Pmax > 0.
- `tests/test_full_cycle_vp37_hrr.py` - pelny cykl z HRR opartym o VP37 (cam + ksztalt dawki).
- `tests/test_geometry.py` - objetosc cylindra w TDC/BDC bez offsetu.
- `tests/test_hydraulics.py` - udzial pilota w granicach 0..1 oraz przypadek 0 deg.
- `tests/test_lift_table.py` - parsowanie tabeli wzniosu i interpolacja > 1 mm w znanym zakresie.
- `tests/test_n146_map.py` - poprawne wczytanie i inwersja mapy N146.
- `tests/test_soi_map.py` - wczytanie mapy SOI i poprawna konwencja znaku (BTDC -> ujemne).
- `tests/test_solver_sanity.py` - uruchomienie closed-cycle i metryki Pmax.
- `tests/test_turbo_coupled.py` - uruchomienie sprzezenia turbo i historia iteracji.
- `tests/test_valvetrain.py` - krzywa wzniosu ma 0 na brzegach i ~1 w srodku.
- `tests/test_vp37_cam.py` - czas wtrysku rosnie monotonicznie wraz z dawka.
