# Audit datové kvality — era-aware

_2026-06-02 10:28 · generuje `validate_almanach.py` z `almanach.sqlite`_

## 1. Mistři extraligy a srovnání s 1. místem základní části

Mistr je primárně z META (`Mistr:`). Sloupec **≠ZČ** značí, že mistr není tým z 1. místa základní části — v play-off éře normální.

| Sezóna | Mistr | Zdroj | 1. ZČ | ≠ZČ |
|---|---|---|---|:--:|
| 1948_49 | LTC Praha | 1.ZČ | LTC Praha |  |
| 1949_50 | ATK Praha | 1.ZČ | ATK Praha |  |
| 1950_51 | SKP České Budějovice | 1.ZČ | SKP České Budějovice |  |
| 1951_52 | Sokol Hutě Chomutov | 1.ZČ | Sokol Hutě Chomutov |  |
| 1952_53 | Spartak Praha Sokolovo | 1.ZČ | Spartak Praha Sokolovo |  |
| 1953_54 | TJ Spartak Praha Sokolovo | 1.ZČ | TJ Spartak Praha Sokolovo |  |
| 1954_55 | Rudá hvězda Brno | 1.ZČ | Rudá hvězda Brno |  |
| 1955_56 | Rudá hvězda Brno | 1.ZČ | Rudá hvězda Brno |  |
| 1956_57 | Rudá hvězda Brno | 1.ZČ | Rudá hvězda Brno |  |
| 1957_58 | Rudá hvězda Brno | 1.ZČ | Rudá hvězda Brno |  |
| 1958_59 | SONP Kladno | META | SONP Kladno |  |
| 1959_60 | Rudá hvězda Brno | 1.ZČ | Rudá hvězda Brno |  |
| 1960_61 | Rudá hvězda Brno | 1.ZČ | Rudá hvězda Brno |  |
| 1961_62 | Slovan Bratislava | 1.ZČ | Slovan Bratislava |  |
| 1962_63 | ZKL Brno | 1.ZČ | ZKL Brno |  |
| 1963_64 | ZKL Brno | META | ZKL Brno |  |
| 1964_65 | ZKL Brno | META | ZKL Brno |  |
| 1965_66 | ZKL Brno | META | ZKL Brno |  |
| 1966_67 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1967_68 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1968_69 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1969_70 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1970_71 | Dukla Jihlava | META | ZKL Brno | ⚠ |
| 1971_72 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1972_73 | Tesla Pardubice (1. playoff) | META | Tesla Pardubice |  |
| 1973_74 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1974_75 | SONP Kladno | 1.ZČ | SONP Kladno |  |
| 1975_76 | SONP Kladno | 1.ZČ | SONP Kladno |  |
| 1976_77 | TJ Spartak BEZ Bratislava | SERIES | Poldi SONP Kladno | ⚠ |
| 1977_78 | Poldi SONP Kladno | META | Poldi SONP Kladno |  |
| 1978_79 | Slovan Bratislava | META | Slovan CHZJD Bratislava | ⚠ |
| 1979_80 | TJ Poldi SONP Kladno | 1.ZČ | TJ Poldi SONP Kladno |  |
| 1980_81 | TJ Vítkovice | 1.ZČ | TJ Vítkovice |  |
| 1981_82 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1982_83 | Dukla Jihlava | META | HC Dukla Jihlava | ⚠ |
| 1983_84 | Dukla Jihlava | 1.ZČ | Dukla Jihlava |  |
| 1984_85 | Dukla Jihlava | META | Dukla Jihlava |  |
| 1985_86 | VSŽ Košice | META | VSŽ Košice |  |
| 1986_87 | Tesla Pardubice | 1.ZČ | Tesla Pardubice |  |
| 1987_88 | VSŽ Košice | META | Motor České Budějovice | ⚠ |
| 1988_89 | Tesla Pardubice | META | Tesla Pardubice |  |
| 1989_90 | HC Dukla Jihlava | 1.ZČ | HC Dukla Jihlava |  |
| 1990_91 | Dukla Jihlava | META | HC Dukla Jihlava | ⚠ |
| 1991_92 | Dukla Trenčín | META | HC Škoda Plzeň | ⚠ |
| 1992_93 | HC Chemopetrol Litvínov | 1.ZČ | HC Chemopetrol Litvínov |  |
| 1993_94 | HC Olomouc. 1. česká sezóna | META | HC Zbrojovka Vsetín | ⚠ |
| 1994_95 | HC Dadák Vsetín | META | HC Dadák Vsetín |  |
| 1995_96 | HC Petra Vsetín | META | HC Slezan Opava | ⚠ |
| 1996_97 | HC Petra Vsetín. 3. titul v řadě | META | HC Petra Vsetín | ⚠ |
| 1997_98 | HC Petra Vsetín. 4. titul | META | HC Petra Vsetín (C) | ⚠ |
| 1998_99 | HC Slovnaft Vsetín. 5. titul | META | HC Slovnaft Vsetín (C) | ⚠ |
| 1999_00 | HC Sparta Praha | META | HC Sparta Praha (C) |  |
| 2000_01 | HC Slovnaft Vsetín. 6. titul | META | HC Slovnaft Vsetín | ⚠ |
| 2001_02 | HC Sparta Praha | META | HC Sparta Praha (C) |  |
| 2002_03 | HC Slavia Praha | META | HC ČSOB Pojišťovna Pardubice | ⚠ |
| 2003_04 | HC Hamé Zlín | META | HC Moeller Pardubice | ⚠ |
| 2004_05 | HC Moeller Pardubice | META | HC Hamé Zlín | ⚠ |
| 2005_06 | HC Sparta Praha | META | Bílí Tygři Liberec | ⚠ |
| 2006_07 | HC Sparta Praha | META | Bílí Tygři Liberec | ⚠ |
| 2007_08 | HC Slavia Praha. 1.liga 2 skupiny. ÚLK+KVK sloučeny | META | HC České Budějovice | ⚠ |
| 2008_09 | Energie Karlovy Vary | META | HC Slavia Praha | ⚠ |
| 2009_10 | HC Eaton Pardubice | META | HC Plzeň 1929 | ⚠ |
| 2010_11 | HC Oceláři Třinec | META | HC Oceláři Třinec (C) |  |
| 2011_12 | HC ČSOB Pojišťovna Pardubice | META | HC Sparta Praha | ⚠ |
| 2012_13 | HC Škoda Plzeň. Ústecký a KV + Karlovarský zvlášť | META | Piráti Chomutov | ⚠ |
| 2013_14 | PSG Zlín | META | HC Sparta Praha | ⚠ |
| 2014_15 | HC Verva Litvínov | META | HC Oceláři Třinec | ⚠ |
| 2015_16 | Bílí Tygři Liberec. 1.liga=WSM liga. Ústecký zpět | META | Bílí Tygři Liberec | ⚠ |
| 2016_17 | HC Kometa Brno | META | Bílí Tygři Liberec | ⚠ |
| 2017_18 | HC Kometa Brno. 1.liga=WSM liga | META | HC Škoda Plzeň | ⚠ |
| 2018_19 | HC Oceláři Třinec. 1.liga=Chance liga | META | Bílí Tygři Liberec | ⚠ |
| 2019_20 | Bílí Tygři Liberec | 1.ZČ | Bílí Tygři Liberec |  |
| 2020_21 | HC Oceláři Třinec | META | HC Sparta Praha | ⚠ |

_Mistr ≠ 1. ZČ u **30** sezón (play-off rozhodlo jinak)._

> ⚠ **K potvrzení:** u sezón 1986_87, 1989_90, 1992_93, 2019_20 chybí v META explicitní `Mistr:`, mistr je odvozen z 1. místa ZČ — v play-off éře (≥1985/86) je nutné ověřit vítěze play-off.

## 2. Validace tabulek dle éry (extraliga)

**Éra 2-1-0 (<2002):** 817 řádků · V+R+P≠GP: **0** · PTS≠2·V+R: **3**

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

