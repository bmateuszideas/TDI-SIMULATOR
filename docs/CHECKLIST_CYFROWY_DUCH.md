# Checklist: zgodnosc z manifestem "Cyfrowy Duch"

Ten plik sluzy jako lista kontrolna dopasowania kodu do manifestu.
Full-chem nie jest wymagany.

## Warstwa 1: geometria i kinematyka
- [x] `virtual_tdi/geometry.py`: dane bazowe z `engine_reference_sources.yaml`
- [ ] `virtual_tdi/valvetrain.py`: parametry zaworow zrodlowe + testy zakresow
- [ ] `virtual_tdi/lift_table.py`: walidacja profilu z `profil_krzywek*.md`
- [x] `virtual_tdi/vp37_cam.py`: walidacja profilu z `skok_tloczka_vp37_de110.csv`
- [x] Testy regresyjne V(theta), dV/dtheta, lift i kinematyki

## Warstwa 2: fizyka (bez full-chem)
- [ ] `virtual_tdi/thermo.py`: spis ograniczen modelu i plan mieszanin
- [x] `virtual_tdi/full_cycle.py`: bilans masy/energii z uwzglednieniem kolektorow
- [ ] `virtual_tdi/flow.py`: przeplyw z korektami strat, zrodla parametrow
- [x] `virtual_tdi/heat_transfer.py`: model scian (denko/tuleja/glowica)
- [ ] Testy trendow IMEP/EGT/BSFC po zmianach

## Warstwa 2b: hydraulika i wtrysk
- [x] `virtual_tdi/injection.py` (nie hydraulics.py): fala cisnienia w przewodzie (1D lumped line)
- [x] dynamika iglicy: zaimplementowana w `virtual_tdi/injection.py` (NeedleConfig + solve_injection_hydraulics); wielofazowosc (pilot/main area) czesciowo
- [x] `virtual_tdi/combustion.py`: zaplon zasilany profilem wtrysku z hydrauliki

## Warstwa 3: inteligencja (ECU)
- [ ] `virtual_tdi/edc_maps.py`: jawne zakresy i zrodla map
- [x] `virtual_tdi/n146_map.py`, `virtual_tdi/soi_map.py`: walidacje map
- [ ] Model percepcji: opoznienia, filtry, bledy czujnikow
- [ ] Sterowanie jako petle regulacji (nie tylko mapy)

## Turbo
- [x] `virtual_tdi/turbo.py`: mapy sprezarki/turbiny lub model parametryczny
- [ ] `virtual_tdi/coupled.py`: dynamika turbo zamiast jednego bilansu

## Dane i zrodla
- [x] `engine_reference_sources.yaml`: pelny katalog parametrow
- [x] `docs/BASELINE_MAPY_ECU_I_OSPRZET.md`: opis map i osprzetu
- [x] Mapy ECU: `Mapa*SOI*Table 1.csv`, `Mapa*N146*Table 1.csv`, `SmokeLimiter*.csv`, `Mapa_EGR*.csv`, `Mapa_BOOST*.csv`
- [x] Profile: `profil_krzywek*.md`, `skok_tloczka_vp37_de110.csv`
- [ ] `specs_with_sources.md`: uzupelnione parametry i zrodla

## Walidacja i testy
- [ ] Zestawy porownawcze: P-theta, IMEP, EGT, BSFC
- [ ] Testy regresyjne dla nowych modeli (kolektory, sciany, hydraulika)
