# Checklist: zgodnosc z manifestem "Cyfrowy Duch"

Ten plik sluzy jako lista kontrolna dopasowania kodu do manifestu.
Full-chem nie jest wymagany. Stan zsynchronizowany z kodem (main @ 6558cb8,
walidacja 3/3 PASS + map-grid 12/12 - patrz docs/validation_report.md i docs/REVIEW.md).

## Warstwa 1: geometria i kinematyka
- [x] `virtual_tdi/geometry.py`: dane bazowe z `engine_reference_sources.yaml`
- [x] `virtual_tdi/valvetrain.py`: parametry zaworow zrodlowe (docs/PARAMETRY_SILNIKA.md §3) + testy zakresow
- [x] `virtual_tdi/lift_table.py`: walidacja profilu z `profil_krzywek*.md` (tests/test_lift_table.py)
- [x] `virtual_tdi/vp37_cam.py`: walidacja profilu z `skok_tloczka_vp37_de110.csv`
- [x] Testy regresyjne V(theta), dV/dtheta, lift i kinematyki

## Warstwa 2: fizyka (bez full-chem)
- [x] `virtual_tdi/thermo.py`: gamma(T,x) blend powietrze/spaliny + spis ograniczen (Faza 2.B.1, validation_report §7)
- [x] `virtual_tdi/full_cycle.py`: bilans masy/energii z uwzglednieniem kolektorow i masy paliwa w ladunku (Faza 2.B.2)
- [x] `virtual_tdi/flow.py`: przeplyw kryza dwukierunkowy przez zawory, kolektory 0D
- [x] `virtual_tdi/heat_transfer.py`: model scian (denko/tuleja/glowica), temperatury z YAML/CLI, skalibrowane (1.B.2)
- [x] Testy trendow IMEP/EGT/BSFC po zmianach (tests/test_validation_trends.py)

## Warstwa 2b: hydraulika i wtrysk
- [x] `virtual_tdi/injection.py` (nie hydraulics.py): fala cisnienia w przewodzie (1D lumped line)
- [x] dynamika iglicy: zaimplementowana w `virtual_tdi/injection.py` (NeedleConfig + solve_injection_hydraulics); wielofazowosc (pilot/main area)
- [x] `virtual_tdi/combustion.py`: zaplon zasilany profilem wtrysku z hydrauliki

## Warstwa 3: inteligencja (ECU)
- [x] `virtual_tdi/edc_maps.py`: jawne zakresy i zrodla map (docs/MAPY_ECU_KONWENCJE.md, docs/BASELINE_MAPY_ECU_I_OSPRZET.md)
- [x] `virtual_tdi/n146_map.py`, `virtual_tdi/soi_map.py`: walidacje map
- [x] Model percepcji: opoznienia, filtry, bledy czujnikow (`virtual_tdi/perception.py`, Faza 2.C.1)
- [x] Sterowanie jako petle regulacji: governor PI + PID boost -> VNT (`transient.py`, `controller.py`, Faza 2.C.2)

## Turbo
- [x] `virtual_tdi/turbo.py` + `virtual_tdi/turbo_map.py`: mapy sprezarki/turbiny GT1749V (Faza 2.A.1)
- [x] `virtual_tdi/coupled.py` + `turbo_map.shaft_dynamics_step`: dynamika walka turbo (Faza 2.A.2/2.A.3)

## Dane i zrodla
- [x] `engine_reference_sources.yaml`: pelny katalog parametrow (kazdy z `source`)
- [x] `docs/BASELINE_MAPY_ECU_I_OSPRZET.md`: opis map i osprzetu
- [x] Mapy ECU: `Mapa*SOI*Table 1.csv`, `Mapa*N146*Table 1.csv`, `SmokeLimiter*.csv`, `Mapa_EGR*.csv`, `Mapa_BOOST*.csv`
- [x] Profile: `profil_krzywek*.md`, `skok_tloczka_vp37_de110.csv`
- [x] `docs/sources/specs_with_sources.md`: uzupelnione parametry i zrodla (0.A.1)

## Walidacja i testy
- [x] Zestawy porownawcze: P-theta, IMEP, EGT, BSFC (validation/reference_points.yaml + `python -m virtual_tdi validate` -> 3/3 PASS)
- [x] Testy regresyjne dla modeli (kolektory, sciany, hydraulika, percepcja, turbo: tests/test_full_cycle_*, test_hydraulics, test_perception_turbo_dynamics, test_turbo_*)
- [x] Testy trendow IMEP/EGT/BSFC (tests/test_validation_trends.py)
- [ ] Walidacja MAF z mapy EGR na siatce map (plik EGR w repo uszkodzony - docs/MAPY_ECU_KONWENCJE.md §4; czeka na poprawny zrzut)
