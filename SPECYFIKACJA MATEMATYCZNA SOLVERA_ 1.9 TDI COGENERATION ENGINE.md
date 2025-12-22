# **SPECYFIKACJA MATEMATYCZNA SOLVERA: 1.9 TDI COGENERATION ENGINE**

Typ dokumentu: Algorytmy Fizyczne & Równania Konstytutywne  
Zastosowanie: Symulacja czasu rzeczywistego (Real-Time Physics) dla układu kogeneracyjnego (CHP)

## **1\. KINEMATYKA UKŁADU KORBOWEGO (SOLVER GEOMETRII)**

**Cel:** Wyznaczenie dokładnej objętości cylindra $V(\\theta)$ i jej pochodnej $dV/d\\theta$ w każdym kroku czasowym. Jest to fundament dla równań termodynamiki.

### **Równanie Ruchu Tłoka (Z uwzględnieniem Desaxage)**

W silnikach VW (blok EA827) oś sworznia tłoka jest przesunięta względem osi cylindra (offset/desaxage $\\delta$). Uproszczony wzór sinus-cosinus jest tutaj **niewystarczający**.

**Wzór implementacyjny:**

$$s(\\theta) \= r \\cos(\\theta) \+ \\sqrt{L^2 \- (r \\sin(\\theta) \- \\delta)^2}$$  
Gdzie:

* $s(\\theta)$: Chwilowe położenie tłoka (od osi wału).  
* $r$: Promień wykorbienia (47.75 mm).  
* $L$: Długość korbowodu (144.0 mm).  
* $\\delta$: Przesunięcie osi (Offset, typowo \~0.5-1.0 mm w TDI).  
* $\\theta$: Kąt obrotu wału (0 \= GMP spalania).

### **Chwilowa Objętość Cylindra**

$$V(\\theta) \= V\_c \+ \\frac{\\pi B^2}{4} \\cdot (s\_{max} \- s(\\theta))$$  
Klucz dla Tunera:  
Zmiana uszczelki głowicy (1, 2, 3 karby) zmienia parametr $V\_c$ (Clearance Volume).

* Obliczenie $V\_c$: $V\_{omega\\\_bowl} \+ V\_{gasket} \+ V\_{deck\\\_height}$.

## **2\. TERMODYNAMIKA KOMORY SPALANIA (SOLVER 0D)**

**Cel:** Obliczenie ciśnienia w cylindrze $P(\\theta)$. Zamiast map, stosujemy **I Zasadę Termodynamiki** w formie różniczkowej dla układu otwartego.

### **Główne Równanie Solvera (Rate of Pressure Rise)**

To równanie musi być rozwiązywane w pętli (np. metodą Rungego-Kutty 4\. rzędu):

$$\\frac{dP}{d\\theta} \= \\frac{\\gamma \- 1}{V} \\left( \\frac{dQ\_{comb}}{d\\theta} \- \\frac{dQ\_{wall}}{d\\theta} \\right) \- \\frac{\\gamma P}{V} \\frac{dV}{d\\theta} \+ \\frac{dm\_{in}}{d\\theta} \\dots$$  
Gdzie:

1. $\\frac{dQ\_{comb}}{d\\theta}$: Szybkość wydzielania ciepła ze spalania (patrz sekcja 3).  
2. $\\frac{dQ\_{wall}}{d\\theta}$: Strata ciepła do ścianek (patrz sekcja 5 \- kluczowe dla CHP\!).  
3. $\\frac{dV}{d\\theta}$: Zmiana objętości (z kinematyki).  
4. $\\gamma$ **(Kappa)**: Wykładnik adiabaty. **UWAGA:** Nie może być stały (1.4). Musi być funkcją temperatury $T$:$$\\gamma(T) \= 1.38 \- 0.0001 \\cdot T$$  
   (Dla spalin Diesla wartość ta spada w wysokich temperaturach).

## **3\. SPALANIE I WTRYSK (MODELOWANIE PALIW)**

**Cel:** Symulacja spalania różnych paliw (ON vs Rzepak) i wtrysku dwufazowego (Pilot/Main).

### **Kinetyka Uwalniania Ciepła (Double Wiebe Function)**

Standardowa funkcja Wiebe nie oddaje charakterystyki TDI (miękka praca na wolnych obrotach, twarda pod obciążeniem). Stosujemy model **Podwójnego Wiebe** (Pilot \+ Main).

$$\\frac{dQ\_{comb}}{d\\theta} \= 6.9 \\frac{Q\_{pilot}}{\\Delta \\theta\_p} (m\_p+1) y\_p^{m\_p} e^{-6.9 y\_p^{m\_p+1}} \+ 6.9 \\frac{Q\_{main}}{\\Delta \\theta\_m} (m\_m+1) y\_m^{m\_m} e^{-6.9 y\_m^{m\_m+1}}$$  
Gdzie $y \= \\frac{\\theta \- \\theta\_{start}}{\\Delta \\theta}$.

Implementacja Paliw (SVO/LPG/Metanol):  
Parametr $Q$ (Całkowita energia) zależy od paliwa:  
$$Q\_{total} \= m\_{fuel} \\cdot LHV\_{fuel} \\cdot \\eta\_{comb}$$

* Dla Rzepaku (SVO): $LHV \\approx 37 MJ/kg$ (Mniejsza energia \-\> Solver musi wydłużyć $\\Delta \\theta\_m$ by utrzymać moc).  
* Dla Metanolu: $LHV \\approx 20 MJ/kg$ (Drastyczny spadek mocy bez korekty dawki).

### **Opóźnienie Zapłonu (Ignition Delay) \- Model Arrheniusa**

To równanie decyduje, kiedy *naprawdę* zaczyna się spalanie względem momentu wtrysku.

$$\\tau\_{id} \= A \\cdot P^{-n} \\cdot \\exp\\left(\\frac{E\_a}{R \\cdot T}\\right)$$

* $A, n, E\_a$: Stałe zależne od **Liczby Cetanowej (CN)** paliwa.  
* **Wniosek:** Rzepak ma wyższą lepkość, ale często niższą liczbę cetanową i gorsze parowanie $\\rightarrow$ Model wyliczy większe $\\tau\_{id}$. Silnik wirtualny pokaże, że trzeba przyspieszyć kąt wtrysku (SOI), aby trafić w GMP.

## **4\. HYDRAULIKA VP37 (EFEKT PALIWOWY)**

**Cel:** Obliczenie rzeczywistego kąta wtrysku i ciśnienia w zależności od rodzaju paliwa.

### **Prędkość Fali Dźwiękowej w Paliwie**

Kluczowe dla zrozumienia, dlaczego na Biodieslu silnik pracuje twardziej.

$$c \= \\sqrt{\\frac{K}{\\rho}}$$

* $K$: Moduł ściśliwości (Bulk Modulus).  
* $\\rho$: Gęstość paliwa.

**Przykład obliczeniowy dla Solvera:**

1. **Diesel:** $K=16000$ bar, $\\rho=830$ kg/m³ $\\rightarrow$ $c \\approx 1390$ m/s.  
2. **SVO (Rzepak):** $K=19500$ bar, $\\rho=920$ kg/m³ $\\rightarrow$ $c \\approx 1455$ m/s.

**Opóźnienie Hydrauliczne Przewodu (Line Delay):**

$$\\Delta t\_{hyd} \= \\frac{L\_{przewodu}}{c}$$  
Wyższa prędkość $c$ w rzepaku oznacza, że fala dociera do wtryskiwacza **szybciej**.

* **Efekt w modelu:** Przy tym samym ustawieniu pompy, rzeczywisty kąt wtrysku dla SVO przesuwa się w stronę "Wczesny" (Advance). Model samoczynnie pokaże wzrost Pmax.

## **5\. WYMIANA CIEPŁA (DLA KOGENERACJI CHP)**

**Cel:** Precyzyjne obliczenie, ile mocy idzie w wał (prąd), a ile w wodę i spaliny (ciepło). To najważniejsza sekcja dla Twojego projektu.

### **Korelacja Woschni'ego**

Standard przemysłowy do obliczania współczynnika przejmowania ciepła $h\_g$ wewnątrz cylindra.

$$h\_g \= 127.93 \\cdot D^{-0.2} \\cdot P^{0.8} \\cdot T^{-0.55} \\cdot (w)^{0.8}$$  
Gdzie $w$ (uśredniona prędkość gazu) to suma prędkości tłoka i zawirowania wywołanego spalaniem:

$$w \= C\_1 \\cdot \\bar{v}\_{piston} \+ C\_2 \\frac{V\_d T\_r}{P\_r V\_r} (P \- P\_{motored})$$

* $Q\_{wall} \= h\_g \\cdot A(\\theta) \\cdot (T\_{gas} \- T\_{wall})$  
* **Dla Tunera:** Zwiększenie doładowania podnosi $P$ (ciśnienie), co drastycznie zwiększa $h\_g$.  
* **Dla Kogeneracji:** Większe $h\_g$ to więcej ciepła w płaszczu wodnym (Wymiennik I), ale mniej entalpii w spalinach (Wymiennik II \- kocioł). Model pozwoli zbalansować te wartości, np. poprzez zmianę $C\_2$ (zależnego od kształtu komory wirowej w tłoku).

## **6\. TURBOSPRĘŻARKA (WASTEGATE & CUSTOM MAP)**

**Cel:** Symulacja hybrydowej turbiny Twojego wspólnika.

### **Bilans Mocy Turbosprężarki**

Solver musi iteracyjnie znaleźć punkt równowagi, gdzie moc turbiny \= moc kompresora.

$$P\_{turb} \= \\dot{m}\_{exh} \\cdot c\_p \\cdot T\_{in\\\_turb} \\cdot \\eta\_{turb} \\cdot \\left\[ 1 \- \\left(\\frac{P\_{out}}{P\_{in}}\\right)^{\\frac{\\gamma-1}{\\gamma}} \\right\]$$

### **Modelowanie Wastegate (WG)**

WG traktujemy jako zwężkę o zmiennym przekroju (Variable Orifice), która upuszcza część spalin obok wirnika.

$$\\dot{m}\_{WG} \= C\_d \\cdot A\_{WG}(lift) \\cdot \\frac{P\_{in}}{\\sqrt{R T\_{in}}} \\cdot \\Psi(PR)$$

* **Scenariusz Rzepakowy:** SVO spala się wolniej $\\rightarrow$ wyższe $T\_{in\\\_turb}$ (EGT) $\\rightarrow$ większa energia spalin.  
* **Reakcja Solvera:** Model wyliczy, że dla tej samej mocy kompresora, WG musi się otworzyć szerzej niż na Dieslu, aby nie przeładować układu. Jeśli WG jest za mały (seryjny port), model pokaże **Boost Creep** (niekontrolowany wzrost doładowania).

## **PODSUMOWANIE DLA PROGRAMISTY (ARCHITEKTURA PĘTLI GŁÓWNEJ)**

Aby zbudować model typu "White Box", kod symulacji nie może opierać się na prostych zależnościach wejście-wyjście. Musi on realizować **cykliczną pętlę numeryczną (Time-Marching Loop)**, która dla każdego kroku czasowego (np. $\\Delta t \= 10 \\mu s$ lub $\\Delta \\theta \= 0.1^\\circ$) aktualizuje stan układu termodynamicznego. Poniżej przedstawiono algorytm wykonawczy klasy EngineCycle:

1. **KROK 1: Aktualizacja Stanu Geometrycznego i Kinetycznego (Geometry Solver Update)**  
   * Pobierz aktualny kąt wału $\\theta\_{current}$.  
   * Wylicz chwilową objętość cylindra $V(\\theta)$ używając wzoru z Sekcji 1 (uwzględniając desaxage).  
   * Wylicz pochodną objętości $dV/d\\theta$ (niezbędną do członu pracy w równaniu energii).  
   * **Kluczowe dla CHP:** Wylicz chwilową powierzchnię wymiany ciepła $A(\\theta) \= A\_{glowicy} \+ A\_{tłoka} \+ A\_{tulei}(\\theta)$, co jest niezbędne dla modelu Woschni (Sekcja 5\) do precyzyjnego bilansu strat cieplnych do płaszcza wodnego.  
2. **KROK 2: Inicjalizacja Parametrów Paliwa (Fuel Physics Injection)**  
   * Pobierz właściwości aktywnego paliwa z obiektu FuelMatrix (Diesel, SVO, LPG, Metanol).  
   * Zaktualizuj lokalne zmienne: Wartość Opałową ($LHV$), Gęstość ($\\rho$) oraz Moduł Ściśliwości ($K$).  
   * *Zastosowanie:* Wartość $K$ wpłynie na obliczenie opóźnienia hydraulicznego w Kroku 3, a $LHV$ przeskaluje energię dostępną w Kroku 4\.  
3. **KROK 3: Hydraulika i Fazy Wtrysku (Injection & Spray Dynamics)**  
   * Sprawdź stan logiczny wtryskiwacza (zamknięty/pilot/główny).  
   * Oblicz ciśnienie w przewodzie $P\_{line}(t)$ uwzględniając dynamikę pompy VP37 i prędkość fali dźwiękowej $c \= \\sqrt{K/\\rho}$.  
   * Wyznacz rzeczywisty moment otwarcia iglicy (SOI) uwzględniając opóźnienie hydrauliczne (Line Delay).  
   * Jeśli iglica otwarta: Oblicz masowy wydatek paliwa $\\dot{m}\_{fuel}$ w oparciu o różnicę ciśnień $(P\_{line} \- P\_{cyl})$ i efektywny przekrój dyszy $A\_{eff}$ (zależny od wzniosu $h\_1/h\_2$).  
4. **KROK 4: Kinetyka Chemiczna i Uwalnianie Ciepła (Combustion Solver)**  
   * Oblicz opóźnienie zapłonu $\\tau\_{id}$ (model Arrheniusa z Sekcji 3\) dla wtryśniętej dawki.  
   * Jeśli czas \> $\\tau\_{id}$, uruchom funkcję spalania (Double Wiebe).  
   * Wyznacz $dQ\_{comb}$ (ilość ciepła uwolnionego w tym kroku).  
   * *Dual Fuel Check:* W przypadku LPG/DME, dodaj ciepło ze spalania paliwa gazowego, monitorując ryzyko spalania stukowego (Knock Index) poprzez analizę drugiej pochodnej ciśnienia $d^2P/d\\theta^2$.  
5. **KROK 5: Bilans Energii i Rozwiązanie Równania Stanu (Thermodynamic Integration)**  
   * Oblicz temperaturę gazu $T\_{gas}$ z równania gazu doskonałego dla poprzedniego kroku.  
   * Wyznacz współczynnik przejmowania ciepła $h\_g$ (model Woschni) i oblicz stratę energii do ścianek: $dQ\_{wall} \= h\_g \\cdot A(\\theta) \\cdot (T\_{gas} \- T\_{wall})$.  
   * **Rozwiąż główne równanie różniczkowe ciśnienia** (Sekcja 2\) metodą Rungego-Kutty (RK4), sumując zyski z $dQ\_{comb}$ i odejmując straty $dQ\_{wall}$ oraz pracę objętościową $P \\cdot dV$.  
   * Zapisz nowe ciśnienie $P\_{cyl}$ dla bieżącego kąta $\\theta$.  
6. **KROK 6: Mechanika Wału i Sprzężenie Zwrotne Turbo (Output & Feedback)**  
   * Przelicz ciśnienie $P\_{cyl}$ na siłę działającą na tłok i moment obrotowy na wale ($T\_{ind}$).  
   * Odejmij straty tarcia (FMEP) zależne od lepkości oleju i prędkości obrotowej.  
   * Oblicz entalpię spalin wyrzucanych do kolektora wydechowego.   
   * **Turbo Solver:** Sprawdź bilans mocy turbiny i kompresora (Sekcja 6). Jeśli moc turbiny jest za mała/duża, zaktualizuj ciśnienie doładowania ($P\_{boost}$) dla *kolejnego* cyklu silnika (iteracyjne dążenie do równowagi).

Taki zestaw wzorów i ustrukturyzowana pętla gwarantują, że "Duch" silnika będzie reagował fizycznie (deterministycznie), a nie "na sztywno". Zmiana dowolnego parametru wejściowego (np. średnicy dyszy w Kroku 3\) automatycznie i naturalnie wpłynie na wynik końcowy (Pmax w Kroku 5 i Moment w Kroku 6\) bez konieczności ręcznego strojenia map wynikowych. 