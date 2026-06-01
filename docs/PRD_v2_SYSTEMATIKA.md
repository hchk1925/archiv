# PRD v2 — Hokejovy Almanach D42: Systematika soutezi

**Verze:** 2.0 *(navrh na predelani struktury)*
**Datum:** 22. kvetna 2026
**Zadavatel:** Pavel Tureček
**Pozadavek Pavla:** *"vsechny sezony predelat tak, aby byla jasna systematika soutezi… mame sice levely, ale je to takovy zmatek"*

## 🎯 EXECUTIVE SUMMARY

Pavlovo zjisteni: aktualni struktura almanachu *(L10, L20, L30 atd)* je nekonzistentni napic 72 sezonami a chybi explicitni faze soutezi *(zakladni cast, predkolo, ctvrtfinale...)*.

**Cíl:** Predelat strukturu vsech 72 sezon tak, aby kazda sezona mela **konzistentni format jako Wikipedia** — hlavicku, konecnou tabulku, playoff bracket, statistiky.

## 📋 TASK BREAKDOWN

### TASK A — Datova struktura upgrade *(nutne)*

#### A1: Pridat sloupce do CLUBS list
- **L_TYP** *(X/1/2/K/O/Q)* - konsolidovany typ soutezi
- **FAZE** *(ZC/PK/CF/SF/F/O3/PO/BAR)* - faze v soutezi
- **PORADI** *(1-14 atd)* - poradi v tabulce ZC

#### A2: Rozsirit L-cisla
```
EXTRALIGA (10):
  L10 = Zakladni cast (FAZE=ZC)
  L11 = Predkolo (FAZE=PK)        ⭐ NOVE
  L12 = Ctvrtfinale (FAZE=CF)      ⭐ NOVE
  L13 = Semifinale (FAZE=SF)       ⭐ NOVE
  L14 = O 3. misto (FAZE=O3)       ⭐ NOVE
  L15 = Finale (FAZE=F)
  L16 = Playout (FAZE=PO)          ⭐ NOVE
  L17 = Baraz (FAZE=BAR)           ⭐ NOVE

1. LIGA (20):
  L20 = ZC, L21 = PK, L22 = CF, L23 = SF, L24 = O3, L25 = F, L26 = PO

2. LIGA (30):
  L30 = ZC (vychod/zapad), L31 = SF, L32 = F

KRAJSKE PREBORY (40):
  L40 = ZC, L41 = F
```

### TASK B — META list rozsireni *(per sezona)*

Per sezona META list ma obsahovat:
```python
{
  "season_num": "21. rocnik samostatne ČHE",
  "sponsor": "Tipsport",
  "datum_zacatek": "2013-09-13",
  "datum_konec": "2014-04-30",
  "pocet_klubu_extra": 14,
  "pocet_klubu_1liga": 16,
  "pocet_zapasov_zc": 52,
  "system_bodovani": "3-2-1-0",
  "mistr_cid": "CLUB_S2013_14_0009",
  "vicemistr_cid": "CLUB_S2013_14_0006",
  "treti_cid": "CLUB_S2013_14_0001",
  "vitez_zc_cid": "CLUB_S2013_14_0001",
  "novacek_cid": "CLUB_S2013_14_0005",
  "sestup_extra_cid": "CLUB_S2013_14_0014",
  "top_strelec": "Petr Ton",
  "top_strelec_cid": "CLUB_S2013_14_0001",
  "top_strelec_branek": 35,
  "top_scorer": "Petr Ton",
  "top_scorer_bodu": 67,
  "top_assist": "Jaroslav Hlinka",
  "top_assist_asistenci": 45
}
```

### TASK C — Per-sezona MD reportu

Pro kazdou sezonu *(72 sezon!)* vygenerovat **SEASON_REPORT_YYYY_YY.md**:

**Struktura:**
```
# SEZONA YYYY/YY — [Nazev soutezi]

## Hlavicka
- Cislo rocniku, sponzor, ucastnici, datum

## Hlavni vysledky
- Mistr, vicemistr, 3. misto, novacek, sestup

## Konecna tabulka ZC
- Po. Klub GP W OTW OTL L GF GA Body

## Playoff bracket
- Predkolo → CF → SF → F (+ O 3. misto)

## Statistiky
- Top strelec, top scorer

## Klicove udalosti
- Mileniky sezony

## Referencni Wiki
```

### TASK D — Faze playoff rekonstrukce

#### Stare sezony (pre-2013):
SERIES list ma zapasy ale ne faze. Pojdu zrekonstruovat z:
1. Datum zapasu *(kvetnove zapasy = playoff)*
2. Wiki potvrzeni
3. Pavlovy PDF data

#### 2013-2020:
Almanach uz castecne ma L10/L15. Pojdu rozsirit na L11-L17.

### TASK E — Validace per sezona

Per sezona kontrolovat:
- Pocet klubu v ZC == META.pocet_klubu_extra
- Vsech klubu v ZC ma PORADI
- Mistr je v F a vyhrall
- Bracket je konzistentni *(8 v CF, 4 v SF, 2 v F)*

## 🎯 IMPLEMENTACE — POSTUP

### Faze 1: Demo na 2013/14 *(HOTOVO)*
- ✅ SEASON_REPORT_2013_14.md vytvoreno *(jako template)*
- ✅ SYSTEM_SOUTEZI.md vytvoreno *(definice L-cisel a faze)*

### Faze 2: Klicove sezony *(priorita)*

Vytvorit per-sezona MD pro tyto klicove sezony jako vzor pro Claude Code:
1. **1949/50** - prvni ČSSR mistrovstvi *(LTC Praha)*
2. **1962/63** - reorganizace 2. ligy
3. **1976/77** - vznik 1. NHL a 2. NHL ⭐
4. **1992/93** - posledni federalni sezona
5. **1993/94** - prvni samostatny ČSE
6. **1996/97** - stabilizace 14 klubu
7. **2013/14** - Mountfield HK do extraligy ⭐
8. **2019/20** - COVID-19 *(predcasne ukonceni)*

### Faze 3: Pre-1993 SVK kluby
Pro federalni sezony 1949-1993 priznat:
- Cesky klub vs Slovensky klub *(SVK marker)*
- Mistrovstvi spolecne CSSR ligy
- Po 1993 oddelene Ceska/Slovenska liga

### Faze 4: Batch generace 72 MD
Pro vsech 72 sezon vygenerovat SEASON_REPORT_YYYY_YY.md.

**Estimate:** 8 hodin prace pro Claude Code, plnou validaci, plnou Wikipedii pripravenu.

## 📁 SOUBORY K VYTVORENI

| Soubor | Status |
|---|---|
| SYSTEM_SOUTEZI.md | ✅ HOTOVO |
| SEASON_REPORT_2013_14.md | ✅ HOTOVO *(demo)* |
| SEASON_REPORT_1949_50.md | 🔴 TO-DO |
| SEASON_REPORT_1976_77.md | 🔴 TO-DO |
| SEASON_REPORT_1992_93.md | 🔴 TO-DO |
| SEASON_REPORT_TEMPLATE.md | 🔴 TO-DO |
| ... *(72 sezon)* | 🔴 TO-DO |
| Update CLUBS list | 🔴 TO-DO |
| Update META list | 🔴 TO-DO |

## 💡 KLICOVE PRINCIPY

1. **Konzistence** - kazda sezona ma stejny format
2. **Wiki vzor** - struktura jako Wikipedia stranky pro CHE
3. **Faze soutezi** - L10/L11/L12... pro extraligu, atd.
4. **Per-sezona MD** - jednoduche cteni pro Pavla
5. **Vse v cestine** *(UTF-8)*

## 🔧 PYTHON SKRIPT - generator MD report

```python
def generate_season_report(sezona):
    """Generuje SEASON_REPORT_YYYY_YY.md ze sezony"""
    
    # 1. Nacti META
    meta = load_meta(sezona)
    
    # 2. Nacti tabulku ZC (poradi 1-14)
    zc_table = load_zc_table(sezona, level='X')
    
    # 3. Nacti playoff bracket
    playoff = load_playoff_bracket(sezona)
    
    # 4. Nacti statistiky
    stats = load_stats(sezona)
    
    # 5. Generuj MD
    md = render_md_template(meta, zc_table, playoff, stats)
    
    return md
```

---

**Status:** PRD v2.0 navrzeno. Pavel se rozhodne ktere klice sezony zacit jako prvni.
