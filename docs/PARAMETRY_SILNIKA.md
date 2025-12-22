# Katalog Parametrów Fizycznych i Geometrycznych Silnika 1.9 TDI

Ten dokument stanowi centralne repozytorium dla wszystkich kluczowych parametrów silnika wykorzystywanych w symulatorze "Wirtualny Klon". Jego celem jest spełnienie pierwszego kamienia milowego (M1) z roadmapy projektu: **stworzenie kompletnego katalogu parametrów, ich pochodzenia i jednostek**.

Każdy parametr musi mieć jawnie określone źródło, aby uniknąć "magicznych" wartości i zapewnić zgodność z manifestem "Cyfrowego Ducha".

## 1. Układ Korbowo-Tłokowy (Cranktrain)

Podstawowe wymiary definiujące kinematykę i objętość roboczą silnika.

| Parametr | Wartość | Jednostka | Źródło / Opis |
|---|---|---|---|
| Oznaczenie silnika bazowego | VW 1.9 TDI (ALH/EA827) | - | VW SSP 198 |
| Średnica cylindra (bore) | 79.5 | mm | VW SSP 198, ETKA |
| Skok tłoka (stroke) | 95.5 | mm | VW SSP 198, ETKA |
| Długość korbowodu | 144.0 | mm | ETKA, Mahle Datasheet |
| Promień wykorbienia | 47.75 | mm | 🧮 Obliczone (`stroke / 2`) |
| Odsadzenie osi cylindra (desaxage) | 0.5 | mm | CAD models EA827, `kompletna_lista_z_danymi.md` |
| Rozstaw cylindrów | 88.0 | mm | `kompletna_lista_z_danymi_rozszerzona.md` |
| Wysokość kompresyjna tłoka | 45.80 | mm | `kompletna_lista_z_danymi_rozszerzona.md` |
| Średnica sworznia tłokowego | 26.00 | mm | `kompletna_lista_z_danymi_rozszerzona.md` |

## 2. Komora Spalania i Stopień Sprężania

Parametry definiujące objętość termodynamiczną.

| Parametr | Wartość | Jednostka | Źródło / Opis |
|---|---|---|---|
| Stopień sprężania (CR) | 19.5:1 | - | VW SSP 198 |
| Liczba cylindrów | 4 | - | VW SSP 198 |
| Objętość skokowa cylindra (Vd) | 474.14 | cm³ | 🧮 Obliczone z `bore` i `stroke` |
| Objętość komory spalania (Vc) | ~25.62 | cm³ | 🧮 Obliczone z `Vd` i `CR`. Wartość przybliżona, zależy od uszczelki. |

## 3. Układ Rozrządu (Valvetrain)

Parametry definiujące charakterystykę "oddychania" silnika.

| Parametr | Wartość | Jednostka | Źródło / Opis |
|---|---|---|---|
| Liczba zaworów na cylinder | 2 | - | VW SSP 198 |
| Średnica grzybka zaworu ssącego | 35.95 | mm | `kompletna_lista_z_danymi_rozszerzona.md` |
| Średnica grzybka zaworu wydechowego | 31.45 | mm | `kompletna_lista_z_danymi_rozszerzona.md` |
| Maksymalny wznios zaworów | 8.5 | mm | `kompletna_lista_z_danymi_rozszerzona.md` (dla wałka ALH) |
| Profil wzniosu | Tabela danych | deg -> mm | `profil_krzywek_4cylindry.md` |
| Średnica trzonka zaworu | 7.97 | mm | `kompletna_lista_z_danymi_rozszerzona.md` |

## 4. Układ Wtryskowy (Injection System)

Charakterystyka układu zasilania paliwem dla bazowej konfiguracji ALH (90KM).

| Parametr | Wartość | Jednostka | Źródło / Opis |
|---|---|---|---|
| Typ pompy | Bosch VP37 | - | VW SSP 211 |
| Średnica tłoczka pompy | 10.0 | mm | `kompletna_lista_z_danymi_rozszerzona.md` (skrzynia manualna) |
| Profil tarczy krzywkowej | Tabela danych | deg -> mm | `skok_tloczka_vp37_de110.csv` (dla pompy DE110) |
| Liczba otworów wtryskiwacza | 5 | - | VW SSP 211 |
| Średnica otworu wtryskiwacza | 0.184 | mm | `kompletna_lista_z_danymi_rozszerzona.md` (dla ALH 90KM) |
| Ciśnienie otwarcia (pilot) | 190 | bar | VW SSP 211, Bosch Datasheet |
| Ciśnienie otwarcia (main) | 300 | bar | VW SSP 211, Bosch Datasheet |

## 5. Masy Tłokowo-Korbowe

Masy używane w obliczeniach bezwładności i obciążeń.

| Parametr | Wartość | Jednostka | Źródło / Opis |
|---|---|---|---|
| Masa tłoka | 440 | g | `kompletna_lista_z_danymi_rozszerzona_pelna.md` (Mahle) |
| Masa sworznia | 120 | g | `kompletna_lista_z_danymi_rozszerzona_pelna.md` (Mahle) |
| Masa pierścieni (komplet) | 40 | g | `kompletna_lista_z_danymi_rozszerzona_pelna.md` (Mahle) |
| Masa całkowita korbowodu | ~580 | g | **Estymacja** na podst. danych części aftermarket (FCP/Hurricane) |
| Masa części posuwistej korbowodu | ~145 | g | **Estymacja** (`~1/4` masy całkowitej), standard inżynierski |
| **Całkowita masa posuwista / cyl.** | **~750** | **g** | 🧮 **Obliczone** (suma powyższych) |

## 6. Kolektory (Manifolds)

Objętości kontrolne dla gazowymiany.

| Parametr | Wartość | Jednostka | Źródło / Opis |
|---|---|---|---|
| Objętość kolektora ssącego | 2.0 | L | **Estymacja początkowa** |
| Objętość kolektora wydechowego | 1.5 | L | **Estymacja początkowa** |

---

Dokument będzie rozwijany wraz z postępem prac nad kolejnymi kamieniami milowymi. Parametry oznaczone jako **Estymacja** są głównymi kandydatami do weryfikacji pomiarowej lub zastąpienia twardymi danymi katalogowymi.
