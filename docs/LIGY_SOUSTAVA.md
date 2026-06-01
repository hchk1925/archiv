# LIGY SOUSTAVA — Promenlivost klasifikace 1949-2021

⚠️ **KLICOVE UPOZORNENI:** Almanach 72 sezon **opakovane menil oznaceni urovni soutezi** napic obdobi. Konkretne **krajske prebory** kolisaly mezi **L20**, **L30** a **L40** podle toho, jak byla pyramida v dane sezone strukturovana.

## Toto zpusobilo problemy v moji puvodni statistice:
- ❌ Klasifikovat klub `20_Brněnský` v 1951/52 jako "L20 = 1. liga" → CHYBA, ve skutecnosti to byl krajsky prebor
- ❌ Klasifikovat `40_Plzeňský` v 1956/57 jako "L40 = 4. liga" → CHYBA, ve skutecnosti to byl krajsky prebor

## Sprava klasifikace - dle prefixu sheet name:

| Prefix sheet | Vyznam |
|---|---|
| `10_liga`, `10_extraliga` | **Extraliga** (top) |
| `20_celost`, `20_oblastni`, `20_IIliga`, `20_1liga`, `20_1NHL` | **1. liga / 1. NHL** (2. nejvyssi) |
| `30_2liga`, `30_2NHL`, `30_IINHL` | **2. liga / 2. NHL** (3. nejvyssi) |
| `20_*Brněnský*`, `30_*Brněnský*`, `40_*Brněnský*` + dalsi kraje | **Krajsky prebor** |
| `KVAL` | **Kvalifikace** |

## Časova promenlivost krajskych preboru

| Obdobi | Krajske prebory | Komentar |
|---|---|---|
| 1949/50, 1950/51 | `30_Brněnský` atd. | L30 |
| **1951/52, 1952/53** | `20_Brněnský` atd. | ⚠️ posunute na L20 (bez celostatni 2. ligy) |
| 1953/54, 1954/55 | `30_*` | navrat na L30, zavedeno `20_celost` jako 1.liga |
| **1955-1959** | `40_*` | ⚠️ na L40 (zavedeno `30_oblastni` jako 2. liga) |
| 1960/61+ | `30_Jihomoravsky` atd. | stabilni od reformy 1960 |
| 2005/06+ | `30_Hradecký`, `30_Vysočina` atd. | po reformě kraju (8→14) |

## Sprava pyramida historicky

### Era 1 (1949/50-1952/53): EXTRALIGA + KRAJSKE PREBORY
- Top: extraliga (10_liga)
- 2. uroven: krajske prebory (30_ v 1949-1950, **20_ v 1951-1952**)

### Era 2 (1953/54-1954/55): VZNIK CELOSTATNI 2. LIGY
- Top: extraliga
- 2. uroven: 2. liga celostatni (`20_celost`)
- 3. uroven: krajske prebory (`30_*`)

### Era 3 (1955/56-1959/60): TRIVRSTVA s OBLASTNI
- Top: extraliga
- 2. uroven: 2. liga celostatni (`20_celost`)
- 3. uroven: **oblastni soutez** (`30_oblastni`, `30_PHA_mesto/venkov`)
- 4. uroven: krajske prebory (`40_*`)

### Era 4 (1960/61-1972/73): REFORMA - sjednoceni
- Top: extraliga (12, pak 10 klubu)
- 2. uroven: 2. liga (`20_IIliga`)
- 3. uroven: krajske prebory (`30_*` se sjednocujicim nazvem)

### Era 5 (1973/74-1992/93): EXTRA + 1.NHL + 2.NHL
- Top: extraliga
- 2. uroven: 1. NHL (`20_1liga`)
- 3. uroven: 2. NHL (`30_2liga` po 1976/77)
- 4. uroven: krajske prebory (`30_*`)

⚠️ **POZOR:** V 1973-1975 jeste neexistovala 2.NHL (vznikla az 1976/77!). Klube z teto urovne byly oznaceny jako "30_2liga" jeste pred existenci 2.NHL.

### Era 6 (1993/94-2004/05): PO ROZDELENI CSSR
- Top: extraliga (14 klubu)
- 2. uroven: 1. liga
- 3. uroven: 2. liga
- 4. uroven: krajske prebory (`30_*` s 8 historickymi kraji)

### Era 7 (2005/06-2020/21): NOVE KRAJE
- Top: extraliga
- 2. uroven: 1. liga
- 3. uroven: 2. liga
- 4. uroven: 14 novych krajskych preboru (`30_Hradecký`, `30_Vysočina`, `30_Liberecký`, atd.)

## Spravna klasifikace dle prefixu (Pavlovo upresnit)

```python
def classify(sheet, level, year):
    sheet_s = sheet or ''
    
    # 1. Top liga - jasne
    if '10_liga' in sheet_s or 'extraliga' in sheet_s.lower():
        return 'X'
    
    # 2. KRAJSKE PREBORY - dle nazvu kraje v sheet
    KRAJ_NAMES = ['Brněnský', 'Gottwaldovský', 'Jihlavský', 'Jihočeský', 'Karlovarský',
                  'Královéhradecký', 'Hradecký', 'Liberecký', 'Olomoucký', 'Ostravský',
                  'Pardubický', 'Plzeňský', 'Praha', 'Ústecký', 'PHA_mesto', 'PHA_venkov',
                  'Středočeský', 'Severočeský', 'Vysočina', 'Severomoravský', 'Jihomoravský',
                  'Východočeský', 'Západočeský', 'oblastni', 'Slezský',
                  'Banskobystrický', 'Bratislavský', 'Košický', 'Nitranský', 'Prešovský',
                  'Žilinský', 'SVK']
    if any(name in sheet_s for name in KRAJ_NAMES):
        return 'K'  # Krajsky prebor
    
    # 3. Celostatni druha liga
    if any(x in sheet_s for x in ['20_celost', '20_oblastni', '20_IIliga', 
                                   '20_1liga', '20_1NHL']):
        return '1'  # 1. liga / 1. NHL
    
    # 4. Treti urroven (celostatni)
    if any(x in sheet_s for x in ['30_2liga', '30_2NHL', '30_IINHL']):
        return '2'  # 2. liga / 2. NHL
    
    # Fallback dle L-cisla pro novy format (2013+)
    if level == 'L10': return 'X'
    if level == 'L20': return '1'
    if level == 'L30': return '2'
    
    if 'KVAL' in sheet_s: return 'Q'
    if level == 'okresní': return 'O'
    return '?'
```

## Implikace pro D45 a per-mesto analyzu

V mojich predchozich vystupech (CLUB_NAME_CHANGES.md, PROMOTIONS_RELEGATIONS.md) jsem **chybne klasifikoval krajske prebory jako 1. ligu** v sezonach:
- 1951/52, 1952/53 (kraj = L20)
- 1955-1959 (kraj = L40, ale pouzival jsem "v 30_ je 2. liga")

**Tyto vystupy nutno regenerovat** s opravenou klasifikaci.

## Akcni body pro Claude Code (PRD update)

1. Pridat `classify(sheet, level, year)` funkci do per-sezona auditu
2. Regenerovat **CLUB_NAME_CHANGES.md** s opravenou klasifikaci
3. Regenerovat **PROMOTIONS_RELEGATIONS.md** dle nove klasifikace
4. Pridat sloupec `L_TYP` (X/1/2/K/O/Q) do CLUBS pro stalou referenci
5. Aktualizovat **PRD_HOKEJ_ALMANACH.md** s touto sekcí

---

**Doplneno na zaklade Pavlovo upresnit (kvet 2026):** *"system soutezi bohuzel varioval krajske prebory byly nekdy L20, jindy L30 atd."*

---

## 🆕 DODATEK — Faze soutezi v 2013/14+

V sezonach **od 2013/14** almanach modeluje **vice fazi v ramci jedne soutezi** pomoci L-cisel:

| Level | Faze | Komentar |
|---|---|---|
| **L10** | Extraliga - zakladni cast | hlavni faze |
| **L15** | Extraliga - play-off / 2.kolo | faze 2 |
| **L20** | 1. liga - zakladni cast | hlavni faze |
| **L25** | 1. liga - play-off / baraz | faze 2 |
| **L30** | 2. liga - zakladni cast | hlavni faze |
| **L35** | 2. liga - play-off | faze 2 |
| **L40** | krajske prebory | regionalne |

⚠️ **Implikace pro analyzu:** Klub v extralige se v 2013/14+ muze objevit **3× v CLUBS listu**:
1. Zaznam pro L10 (zakl.cast)
2. Zaznam pro L15 (play-off)
3. Pripadny dalsi zaznam pro reorganizaci

To znamena ze pri **pocitani klubu v extralige** je nutne **deduplikovat dle cn** v ramci sezony.

V COVID sezonach **2019/20, 2020/21** play-off se nehrall → jen L10/L20/L30/L40.

### Aktualizovana classify() funkce:

```python
def classify(sheet, level):
    sheet_s = sheet or ''
    level_s = level or ''
    
    # Top liga - oboje L10 (zakl.cast) a L15 (play-off)
    if '10_liga' in sheet_s or level_s in ('L10', 'L15'):
        return 'X'
    
    # 1. liga - L20 + L25
    if level_s in ('L20', 'L25'):
        return '1'
    
    # 2. liga - L30 + L35
    if level_s in ('L30', 'L35'):
        return '2'
    
    # ... atd.
```
