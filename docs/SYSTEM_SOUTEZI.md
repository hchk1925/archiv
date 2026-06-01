# SYSTEMATIKA SOUTEZI — Levely a baraz

## ⚠️ KLICOVA OPRAVA (Pavlovo upresnit)

**L-cisla = ÚROVNĚ soutezi** *(level 1 = extraliga, level 2 = 1. liga, atd)*  
**Baraz/kvalifikace = MEZI úrovněmi** *(L15 = baraz L10↔L20)*

## 📋 Spravna semantika L-cisel

| Level | Vyznam | Pocet klubu *(typicky)* |
|---|---|---:|
| **L10** | Extraliga *(top)* | 14 |
| **L15** | **Baraz/kvalifikace mezi L10 a L20** | 4 *(2 z L10 + 2 z L20)* |
| **L20** | 1. liga / 1. NHL | 14-20 |
| **L25** | **Baraz/kvalifikace mezi L20 a L30** | 3-5 |
| **L30** | 2. liga / 2. NHL | 24-32 |
| **L35** | **Baraz/kvalifikace mezi L30 a L40** | 0-8 |
| **L40** | Krajsky prebor *(3. nejnizsi soutez)* | 156-207 |

## 📊 Realne pocty 2013-2020

| Sezona | L10 | L15 | L20 | L25 | L30 | L35 | L40 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2013/14 | 18* | 4 | 20 | 5 | 29 | 8 | 199 |
| 2014/15 | 18* | 4 | 18 | 3 | 28 | 3 | 195 |
| 2015/16 | 18* | 4 | 18 | 3 | 30 | 7 | 195 |
| 2016/17 | 18* | 4 | 18 | 3 | 32 | 6 | 207 |
| 2017/18 | 18* | 4 | 14 | 3 | 31 | 0 | 188 |
| 2018/19 | 18* | 4 | 15 | 0 | 28 | 0 | 190 |
| **2019/20** | 14 | **0** | 32 | **0** | 26 | **0** | 177 |
| **2020/21** | 14 | **0** | 18 | **0** | 24 | **0** | 156 |

*L10 = 18 znamena: 14 unique kluby extraligy + 4 zaznamy v baraz (klub se objevuje 2x)*

### COVID-19 sezony 2019/20+2020/21
- **L15/L25/L35 = 0** *(baraz se nehrall)*
- **L10 = 14** *(jen zakladni cast, bez baraze)*
- Sezony predcasne ukoncene / omezene

## 🔧 Sprava classify() funkce

```python
def classify(sheet, level):
    sheet_s = sheet or ''
    level_s = level or ''
    
    # EXTRALIGA = L10 + jeji baraz L15
    if '10_liga' in sheet_s or 'extraliga' in sheet_s.lower():
        return 'X'
    if level_s in ('L10', 'L15'):
        return 'X'  # L15 = baraz extraliga vs 1.liga
    
    # 1. LIGA = L20 + jeji baraz L25
    if level_s in ('L20', 'L25'):
        return '1'  # L25 = baraz 1.liga vs 2.liga
    if any(x in sheet_s for x in ['20_celost', '20_oblastni', '20_IIliga', '20_1liga', '20_1NHL']):
        return '1'
    
    # 2. LIGA = L30 + jeji baraz L35
    if level_s in ('L30', 'L35'):
        return '2'  # L35 = baraz 2.liga vs kraj
    if any(x in sheet_s for x in ['30_2liga', '30_2NHL', '30_IINHL']):
        return '2'
    
    # KRAJSKE PREBORY = L40
    if level_s == 'L40':
        return 'K'
    
    # Krajske prebory podle nazvu (pre-2013)
    KRAJ_NAMES = ['Brněnský', 'Gottwaldovský', 'Jihlavský', 'Praha', ...]
    if any(name in sheet_s for name in KRAJ_NAMES):
        return 'K'
    
    if 'KVAL' in sheet_s: return 'Q'
    return '?'
```

## 📋 Specifika starsich sezon (pre-2013)

V starsich sezonach almanach nepouzival L-cisla, ale prefixy sheet:
- `10_liga` = extraliga
- `20_celost` / `20_IIliga` / `20_1NHL` = 1. liga
- `30_2liga` / `30_2NHL` = 2. liga
- `30_*kraj*` / `40_*kraj*` = krajske prebory
- `KVAL` = kvalifikace = **baraz mezi urovnemi**

V techto sezonach se baraz vyskytuje:
- Mezi extraligou a 1. ligou
- Mezi 1. ligou a 2. ligou
- Mezi 2. ligou a kraj prebory

## 💡 Implikace pro analyzu

### Pri pocitani klubu v lize:
**Pocitat UNIKE klubu**, nepocitat baraz duplicitne:
- Extraliga 2013/14 = **14 klubu** *(ne 18!)* — 4 baraze jsou duplicity
- Klub muze mit zaznam v L10 *(zakladni cast)* + L15 *(baraz)* = jeden klub

### Postupy/sestupy:
- **L15 = klub bojuje o postup/sestup** mezi extraligou a 1. ligou
- Kdo L15 vyhrall → zustal v extralize / postoupil
- Kdo L15 prohrall → sestoupil / zustal v 1. lize

---

**Verze 2.0** *(opraveno dle Pavlovo upresnit)*
**Predchozi pochopeni (chybne):** L15 = play-off, L25 = play-off… → BYLO ŠPATNĚ.
