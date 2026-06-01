# PYRAMIDA ZOBRAZENI — Mapovani L-cislo → uroven soutezi

## 🎯 Cíl

Data zustavaji beze zmeny. Tato reference rika, **jak pri ZOBRAZENI vykreslit spravnou pyramidu** per sezona.

## ⚠️ Klicove pravidlo

**L-cislo NENI primo uroven pyramidy!** Spravna uroven se odvodi z **kombinace L-cislo + sheet name**:
- `L20` muze byt: krajsky prebor *(1951/52)*, 1. liga *(1953+)*, 1.NHL *(1976+)*
- `L15` muze byt: baraz *(vetsinou)* NEBO 2. liga *(1956/57 — sheet 20_celost)*

## 🔧 Zobrazovaci funkce

```python
def pyramid_position(sezona_year, level, sheet):
    """
    Vrati (uroven, nazev_souteze, je_baraz) pro zobrazeni pyramidy.
    uroven: 1 (top) az 6 (najnizsi)
    je_baraz: True pokud jde o kvalifikaci/baraz mezi urovnemi
    """
    sheet_s = sheet or ''
    
    # === BARAZ (KVAL sheet nebo L_5 ktery odkazuje na vyssi soutez) ===
    if 'KVAL' in sheet_s:
        return (None, 'Kvalifikace/baraz', True)
    
    # === UROVEN 1: EXTRALIGA ===
    if '10_liga' in sheet_s or 'extraliga' in sheet_s.lower():
        return (1, 'Extraliga', False)
    
    # === UROVEN 2: druha nejvyssi (1.liga / 1.NHL / oblastni) ===
    if '20_1NHL' in sheet_s:
        return (2, '1. NHL', False)
    if '20_1liga' in sheet_s or '20_IIliga' in sheet_s:
        return (2, '1. liga', False)
    if '20_celost' in sheet_s:
        return (2, '2. liga (celostatni)', False)
    if '20_oblastni' in sheet_s:
        return (2, 'Oblastni soutez', False)
    
    # === UROVEN 3: treti (2.liga / 2.NHL) ===
    if '30_2NHL' in sheet_s:
        return (3, '2. NHL', False)
    if '30_2liga' in sheet_s:
        return (3, '2. liga', False)
    if '30_oblastni' in sheet_s:
        return (3, 'Oblastni soutez', False)
    if '40_Divize' in sheet_s:
        return (3, 'Divize', False)
    
    # === KRAJSKE/OKRESNI - uroven podle L-cisla a kraje ===
    # Kdyz je sheet '20_{kraj}' (1951/52), je to krajsky prebor na 2. urovni
    if sheet_s.startswith('20_') and any(k in sheet_s for k in KRAJ_NAMES):
        return (2, f'Krajsky prebor ({extract_kraj(sheet_s)})', False)
    # Kdyz '30_{kraj}', krajsky prebor na 3.-4. urovni dle sezony
    if sheet_s.startswith('30_') and any(k in sheet_s for k in KRAJ_NAMES):
        # uroven zavisi na tom, zda existuje celostatni 2.liga v sezone
        return (4, f'Krajsky prebor ({extract_kraj(sheet_s)})', False)
    if sheet_s.startswith('40_'):
        return (4, f'Krajsky prebor', False)
    if level == 'okresní' or 'okres' in sheet_s.lower():
        return (5, 'Okresni prebor', False)
    
    return (None, sheet_s, False)
```

## 📊 Pyramida per epoche *(pro zobrazeni)*

### Epocha 1949-1952: 4-5 urovni *(bez celostatni 2.ligy)*
```
1. Extraliga          (10_liga)         L10
2. Oblastni soutez    (20_oblastni)     L20    [1949-50]
   NEBO krajske       (20_kraj)         L20    [1951-52]
3. Krajske prebory    (30_kraj)         L30
4. Okresni            (30_kraj)         L40-L50
```

### Epocha 1953-1959: 5-6 urovni *(vznik celostatni 2.ligy)*
```
1. Extraliga          (10_liga)         L10
2. 2. liga celostatni (20_celost)       L20
3. Oblastni/Krajske   (30_oblastni)     L30
4. Krajske prebory    (40_kraj)         L40
5. Okresni            (40_kraj)         L50
6. Najnizsi           (40_PHA_mesto)    L60    [1956-59]
```

### Epocha 1960-1972: 4-5 urovni *(sjednocena 2.liga)*
```
1. Extraliga          (10_liga)         L10
2. 2. liga            (20_IIliga)       L20
3. Krajske prebory    (30_kraj)         L30
4. Okresni            (30_kraj)         L40
+ Baraz extra/2.liga  (KVAL)            L15
```

### Epocha 1973-1992: 5-6 urovni *(1.NHL + 2.NHL)*
```
1. Extraliga          (10_liga)         L10
2. 1. NHL             (20_1NHL)         L20
3. 2. NHL             (30_2NHL)         L30    [od 1976/77]
4. Divize             (40_Divize)       L40
5. Krajske prebory    (30_kraj)         L50
6. Okresni            (30_kraj)         L60
+ Baraz               (KVAL)            L15/L25
```

### Epocha 1993-2012: 4 urovne *(samostatna CR)*
```
1. Extraliga          (10_liga)         L10
2. 1. liga            (20_1liga)        L20
3. 2. liga            (30_2liga)        L30
4. Krajske prebory    (30_kraj)         L40
+ Baraz (nepravidelne)(KVAL)            L15/L25
```

### Epocha 2013-2018: 4 urovne + plny baraz
```
1. Extraliga          (10_liga)         L10
   Baraz extra/1.liga (10_liga/KVAL)    L15
2. 1. liga            (20_1liga)        L20
   Baraz 1./2.liga    (20_1liga)        L25
3. 2. liga            (30_2liga)        L30
   Baraz 2.liga/kraj  (KVAL)            L35
4. Krajske prebory    (30_kraj)         L40
```

### Epocha 2019-2021: 4 urovne *(COVID, bez baraz)*
```
1. Extraliga          (10_liga)         L10
2. 1. liga            (20_1liga)        L20
3. 2. liga            (30_2liga)        L30
4. Krajske prebory    (30_kraj)         L40
```

## 💡 Zobrazovaci logika *(shrnuti)*

| Krok | Akce |
|---|---|
| 1 | Precist L-cislo + sheet name z CLUBS |
| 2 | Detekce baraz: pokud `KVAL` v sheet → je baraz mezi urovnemi |
| 3 | Detekce urovni: dle prefixu sheet *(10_=extra, 20_celost=2.liga, 20_1NHL=1.NHL, 30_kraj=kraj)* |
| 4 | Krajske prebory: uroven dle epochy *(2. uroven 1951/52, jinak 3.-4.)* |
| 5 | Render pyramidu: serad podle urovni 1-6 |

## 🎯 Pro aplikaci

Pri zobrazeni sezony:
1. Nacti vsech klubu
2. Pro kazdy urci `pyramid_position(year, level, sheet)`
3. Seskup podle urovni
4. Zobraz pyramidu: Extraliga nahore → krajske dole
5. Baraz zobraz jako **spojnici mezi urovnemi**

---

**Verze 1.0** — zobrazovaci reference *(data se nemeni)*
**Pavlovo upresnit:** *"pri zobrazeni mit spravne pyramidu"*
