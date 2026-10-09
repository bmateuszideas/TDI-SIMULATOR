# Raport walidacji (Faza 1, TODO.md)

Data: połączony review ×2; runner: `python -m virtual_tdi validate`
(plik punktów: `validation/reference_points.yaml`).

## 1. Cel

Przejście z "model spójny wewnętrznie" na "model wiadomo-jakie-błądzi":
porównanie metryk symulacji z danymi referencyjnymi ALH 90 PS
(66 kW @ 3750 rpm, 210 Nm @ 1900 rpm, BSFC wyspa ~197–210 g/kWh).

## 2. Wyniki (stan po kalibracji FMEP)

| Punkt | Wynik | Główne odchyłki |
|---|---|---|
| `part_load_cruise` (1500 rpm, 8 mg, NA) | **PASS** | IMEP 3.13 bar vs 3.0 (+4%), BSFC 285 vs 260 g/kWh (+10%) |
| `full_load_peak_torque` (1900 rpm, 36 mg, turbo) | FAIL (known_gap) | torque −23%, peak-P −30%, BSFC +22% |
| `full_load_rated_power` (3750 rpm, 30 mg, turbo) | FAIL (known_gap) | power −45%, BSFC +58% |

## 3. Zidentyfikowane przyczyny odchyłek (analiza wrażliwości)

1. **Turbo coupling (dominująca przyczyna porażek full-load):** obecny
   quasi-statyczny bilans mocy daje `p_intake_mean` ≈ 0.88–0.94 bar abs przy
   pełnym obciążeniu, podczas gdy realny ALH (K03/GT1749V) utrzymuje ~1.8 bar
   abs przy 1900–3750 rpm pełnym obciążeniu. Niska gęstość ładunku = mniej
   powietrza = mniej możliwości spalenia dawki → torque/power poniżej referencji.
   **To jest dokładnie luka Fazy 2.A (TODO.md): mapy sprężarki/turbiny zamiast
   stałych sprawności.** Punkty full-load są oznaczone `known_gap: turbo_coupling`
   i porażka na nich jest spodziewana do czasu domknięcia 2.A.

2. **Nadmierny IMEP przy NA (z review):** przy 20 mg NA (1500 rpm) model daje
   IMEP ~8.6 bar; recenzent wskazał ~5–6 bar. Po audycie: ta wartość jest
   spójna z założeniami modelu (Woschni z w_mult=6, masa paliwa nie w ładunku,
   γ powietrza), ale pozostaje ~30–40% nad referencją części-obciążeniową.
   Główni kandydaci do strojenia (kolejność): `w_mult` (mocniejsza wymiana
   ciepła → niższy IMEP), masa paliwa w ładunku (Faza 2.B.2, +4% masy),
   termika mieszanin γ(T,x) (Faza 2.B.1). Częściowo skompensowane nowym FMEP
   (B=0.12, C=0.02), które obniża brake torque o ~0.3–0.6 bar w punktach testowych.

3. **FMEP skalibrowane (wstępnie):** B=0.12 bar/krpm (Heywood Ch. 13 trend
   FMEP vs prędkość dla DI), C=0.02 bar/bar (Millington–Hartles styl, czynnik
   szczytowego ciśnienia). Efekt: brake torque @1500 rpm/8 mg spada o ~10%,
   test transientu wymagał poszerzenia bounds (patrz test_transient.py).

4. **BSFC poprawiony jednostkowo:** pierwotna implementacja zwracała wartość
   w kg/kWh (0.256 zamiast 256 g/kWh). Po poprawce: 255–370 g/kWh — rząd
   wielkości zgodny z referencją ALH.

## 4. Decyzje

- Punkty full-load **pozostają w zestawie walidacyjnym** jako known_gap —
  są miarą postępu Fazy 2.A, nie powodem do „dopasowania" modelu do nich
  na siłę (np. zawyżaniem sprawności turbo ponad fizyczne wartości).
- Kalibracja `w_mult`/temperatur ścian zostaje wstrzymana do momentu,
  gdy turbo będzie podawać fizyczne p_intake — inaczej kalibrowalibyśmy
  ściany na błędnym punkcie pracy.
- `bsfc_g_per_kwh` dodany do metryk i IO_CONTRACT (1.B.3 z TODO.md).

## 5. Następne kroki

1. Faza 2.A (TODO.md): mapy sprężarki/turbiny K03 + dynamika wałka.
2. Po 2.A: ponowna walidacja full-load, potem kalibracja `w_mult`/ścian.
3. Faza 2.B: masa paliwa w bilansie ładunku, γ(T,x).

## 6. Aktualizacja po Fazie 2.A (turbo maps)

Po implementacji map sprężarki/turbiny (`virtual_tdi/turbo_map.py`,
`validation/turbo_map_gt1749v.yaml`) i podpięciu `--turbo` do CLI:

| Punkt | Przed 2.A | Po 2.A |
|---|---|---|
| `part_load_cruise` | PASS | PASS |
| `full_load_peak_torque` | FAIL (torque −53%, p_intake 0.94 bar) | **PASS** (torque −9%, p_intake 1.88 bar, shaft 72k rpm) |
| `full_load_rated_power` | FAIL (power −57%) | FAIL (power −12.6%, tuż poza tolerancją 12%) |

Dodatkowo znaleziono i naprawiono **błąd krytyczny**: `simulate_coupled_turbo`
nie przekazywał `fuel_mg_per_cycle_per_cyl` ani `injection_profile` do wewnętrznych
iteracji — każda iteracja turbo liczyła cykl z domyślną dawką 20 mg zamiast
komendowanej. To unieważnia wszystkie wcześniejsze wyniki `--turbo`.

Pozostały deficyt rated power (−12.6%): p_intake 1.76 bar (realny ~1.9-2.0),
q_wall ~13% energii. Kandydaci: kalibracja w_mult/ścian (1.B.2), dokładniejsza
mapa VNT (section 2.6 w TODO.md - jeśli pojawi się oficjalna mapa Garrett).

## 7. Stan po 1.B.2 + 2.B (pełna walidacja zielona)

Kalibracja ścian (600/650/550 K, górny zakres Heywood Ch. 13 dla turbo DI) na
fizycznym punkcie pracy turbo (po 2.A), plus fixy termofizyczne:

- **2.B.2 masa paliwa w ładunku:** dm_fuel/dθ = dQ/LHV zsynchronizowane z HRR
  (wcześniej energia wchodziła bez masy — bias ~4% przy pełnym obciążeniu).
- **2.B.1 γ(T,x):** GasModel z burned_fraction (cp spalin +110 J/kgK wg
  Heywood Ch. 3); cylinder = EGR + burnt fuel fraction, kolektor wydechowy x=1.
- **Governor PI re-strojenie** (kp 0.10→0.05, ki 0.06→0.03): masa paliwa
  zmienia gain pętli; stare wzmocnienia dawały oscylacje/overshoot prędkości.

Wynik `python -m virtual_tdi validate`:

| Punkt | Wynik | Delty |
|---|---|---|
| full_load_peak_torque | **PASS** | torque −8.1%, peak-P +9.6%, BSFC +1.8% |
| full_load_rated_power | **PASS** | power −2.1%, BSFC +0.8% |
| part_load_cruise | **PASS** | IMEP +5.9%, BSFC +7.3% |

Model jest teraz zwalidowany na 3 punktach ALH 90 PS w tolerancjach 10-25%.
Kolejny poziom wierności wymagałby danych pomiarowych (P-θ trace, EGT po hamowni)
— zakresy literaturowe są wykorzystane do granic ich rozdzielczości.
