# Audit datové kvality — era-aware

_2026-06-03 14:12 · generuje `validate_almanach.py` z `almanach.sqlite`_

## 1. Mistři extraligy a srovnání s 1. místem základní části

Mistr je primárně z META (`Mistr:`). Sloupec **≠ZČ** značí, že mistr není tým z 1. místa základní části — v play-off éře normální.

| Sezóna | Mistr | Zdroj | 1. ZČ | ≠ZČ |
|---|---|---|---|:--:|
| 1947_48 | LTC Praha | M-badge | I. ČLTK Praha | ⚠ |
| 1948_49 | LTC Praha | M-badge | LTC Praha |  |
| 1949_50 | ATK Praha | M-badge | ATK Praha |  |
| 1950_51 | SKP České Budějovice | M-badge | SKP České Budějovice |  |
| 1951_52 | Vítkovické Železárny | M-badge | Sokol Hutě Chomutov | ⚠ |
| 1952_53 | Spartak Praha Sokolovo | M-badge | Spartak Praha Sokolovo |  |
| 1953_54 | TJ Spartak Praha Sokolovo | M-badge | TJ Spartak Praha Sokolovo |  |
| 1954_55 | Rudá hvězda Brno | M-badge | Rudá hvězda Brno |  |
| 1955_56 | Rudá hvězda Brno | M-badge | Rudá hvězda Brno |  |
| 1956_57 | Rudá hvězda Brno | M-badge | Rudá hvězda Brno |  |
| 1957_58 | Rudá hvězda Brno | M-badge | Rudá hvězda Brno |  |
| 1958_59 | Rudá hvězda Brno | M-badge | SONP Kladno | ⚠ |
| 1959_60 | SONP Kladno | M-badge | Rudá hvězda Brno | ⚠ |
| 1960_61 | Rudá hvězda Brno | M-badge | Rudá hvězda Brno |  |
| 1961_62 | Rudá hvězda Brno | M-badge | Slovan Bratislava | ⚠ |
| 1962_63 | ZKL Brno | M-badge | ZKL Brno |  |
| 1963_64 | ZKL Brno | M-badge | ZKL Brno |  |
| 1964_65 | ZKL Brno | M-badge | ZKL Brno |  |
| 1965_66 | ZKL Brno | M-badge | ZKL Brno |  |
| 1966_67 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1967_68 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1968_69 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1969_70 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1970_71 | Dukla Jihlava | M-badge | ZKL Brno | ⚠ |
| 1971_72 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1972_73 | Tesla Pardubice | M-badge | Tesla Pardubice |  |
| 1973_74 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1974_75 | SONP Kladno | M-badge | SONP Kladno |  |
| 1975_76 | SONP Kladno | M-badge | SONP Kladno |  |
| 1976_77 | Poldi SONP Kladno | M-badge | Poldi SONP Kladno |  |
| 1977_78 | Poldi SONP Kladno | M-badge | Poldi SONP Kladno |  |
| 1978_79 | Slovan CHZJD Bratislava | M-badge | Slovan CHZJD Bratislava |  |
| 1979_80 | TJ Poldi SONP Kladno | M-badge | TJ Poldi SONP Kladno |  |
| 1980_81 | TJ Vítkovice | M-badge | TJ Vítkovice |  |
| 1981_82 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1982_83 | HC Dukla Jihlava | M-badge | HC Dukla Jihlava |  |
| 1983_84 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1984_85 | Dukla Jihlava | M-badge | Dukla Jihlava |  |
| 1985_86 | VSŽ Košice | M-badge | VSŽ Košice |  |
| 1986_87 | Tesla Pardubice | M-badge | Tesla Pardubice |  |
| 1987_88 | VSŽ Košice | M-badge | Motor České Budějovice | ⚠ |
| 1988_89 | Tesla Pardubice | M-badge | Tesla Pardubice |  |
| 1989_90 | HC Dukla Jihlava | M-badge | HC Dukla Jihlava |  |
| 1990_91 | HC Dukla Jihlava | M-badge | HC Dukla Jihlava |  |
| 1991_92 | HC Dukla Trenčín | M-badge | HC Škoda Plzeň | ⚠ |
| 1992_93 | HC Sparta Praha | M-badge | HC Chemopetrol Litvínov | ⚠ |
| 1993_94 | HC Olomouc | M-badge | HC Zbrojovka Vsetín | ⚠ |
| 1994_95 | HC Dadák Vsetín | M-badge | HC Dadák Vsetín |  |
| 1995_96 | HC Petra Vsetín (C) | M-badge | HC Slezan Opava | ⚠ |
| 1996_97 | HC Petra Vsetín | M-badge | HC Petra Vsetín |  |
| 1997_98 | HC Petra Vsetín (C) | M-badge | HC Petra Vsetín (C) |  |
| 1998_99 | HC Slovnaft Vsetín (C) | M-badge | HC Slovnaft Vsetín (C) |  |
| 1999_00 | HC Sparta Praha (C) | M-badge | HC Sparta Praha (C) |  |
| 2000_01 | HC Slovnaft Vsetín | M-badge | HC Slovnaft Vsetín |  |
| 2001_02 | HC Sparta Praha (C) | M-badge | HC Sparta Praha (C) |  |
| 2002_03 | HC Slavia Praha (C) | M-badge | HC ČSOB Pojišťovna Pardubice | ⚠ |
| 2003_04 | HC Hamé Zlín (C) | M-badge | HC Moeller Pardubice | ⚠ |
| 2004_05 | HC Moeller Pardubice (C) | M-badge | HC Hamé Zlín | ⚠ |
| 2005_06 | HC Sparta Praha (C) | M-badge | Bílí Tygři Liberec | ⚠ |
| 2006_07 | HC Sparta Praha (C) | M-badge | Bílí Tygři Liberec | ⚠ |
| 2007_08 | HC Slavia Praha (C) | M-badge | HC České Budějovice | ⚠ |
| 2008_09 | HC Energie Karlovy Vary | M-badge | HC Slavia Praha | ⚠ |
| 2009_10 | HC Eaton Pardubice (C) | M-badge | HC Plzeň 1929 | ⚠ |
| 2010_11 | HC Oceláři Třinec (C) | M-badge | HC Oceláři Třinec (C) |  |
| 2011_12 | HC ČSOB Pojišťovna Pardubice | M-badge | HC Sparta Praha | ⚠ |
| 2012_13 | HC Škoda Plzeň (C) | M-badge | Piráti Chomutov | ⚠ |
| 2013_14 | PSG Zlín | M-badge | HC Sparta Praha | ⚠ |
| 2014_15 | HC Verva Litvínov | M-badge | HC Oceláři Třinec | ⚠ |
| 2015_16 | Bílí Tygři Liberec | M-badge | Bílí Tygři Liberec |  |
| 2016_17 | HC Kometa Brno | M-badge | Bílí Tygři Liberec | ⚠ |
| 2017_18 | HC Kometa Brno | M-badge | HC Škoda Plzeň | ⚠ |
| 2018_19 | HC Oceláři Třinec | M-badge | Bílí Tygři Liberec | ⚠ |
| 2019_20 | Bílí Tygři Liberec | 1.ZČ | Bílí Tygři Liberec |  |
| 2020_21 | HC Oceláři Třinec | M-badge | HC Sparta Praha | ⚠ |

_Mistr ≠ 1. ZČ u **27** sezón (play-off rozhodlo jinak)._

> ⚠ **K potvrzení:** u sezón 2019_20 chybí v META explicitní `Mistr:`, mistr je odvozen z 1. místa ZČ — v play-off éře (≥1985/86) je nutné ověřit vítěze play-off.

## 2. Validace tabulek dle éry (extraliga)

**Éra 2-1-0 (<2002):** 829 řádků · V+R+P≠GP: **0** · PTS≠2·V+R: **3**

**Éra 3-2-1-0 (≥2002):** 342 řádků · W/D/L nesedí na GP (ztrátový zdroj — 5 sl. → 3): **334** (očekávané, ne chyba)

## 3. Poškozené buňky extraligy (re-extrakce ze zdroje)

Po doplnění z originálních PDF (`fill_from_pdf.py`): **žádné**. ✓

## 4. Reziduální anomálie 2-1-0 éry (k ověření)

| Sezóna | Poz. | Klub | Detail |
|---|---|---|---|
| 1988_89 | 9 | TJ Vítkovice | PTS=11≠2·V+R=8 (možný přenos bodů/penalizace) |
| 1988_89 | 10 | TJ Gottwaldov | PTS=9≠2·V+R=7 (možný přenos bodů/penalizace) |
| 1988_89 | 12 | Poldi SONP Kladno | PTS=4≠2·V+R=3 (možný přenos bodů/penalizace) |

_Pozn.: u skupin o udržení / prolínacích (1988/89) je PTS>2·V+R korektní — body se přenášejí ze základní části. Zbytek jsou drobné ±1 odchylky v základní části k ověření z PDF._

