# 📖 ÚSTAVA FÁZÍ SOUTĚŽÍ — Hokejový almanach

**Verze:** 1.0
**Účel:** Manuál pro implementaci do Excelu tak, aby i mladý čtenář pochopil **flow soutěže** v dané sezóně — jak na sebe navazují fáze (základní část → play-off → o umístění → sestup).

---

## 1. PROČ TENTO DOKUMENT

Almanach obsahuje 72 sezón čs./českého hokeje. Každá sezóna má svou **strukturu soutěží** (úrovně) a každá soutěž má svůj **vnitřní průběh** (fáze). Aby čtenář pochopil, **jak se klub dostal k postupu nebo sestupu**, musí vidět celý tok:

```
Základní část → (rozdělení) → Play-off (o titul)  /  Skupina o udržení (o sestup)
```

Bez tohoto kontextu vznikají chyby ve výkladu — např. „klub sestoupil ze základní části", i když se ze základní části nesestupovalo.

---

## 2. TYPY FÁZÍ (competition_type) — slovník

V datech (SYSTEM list) má každý uzel soutěže pole `competition_type`. Toto jsou všechny typy napříč 72 sezónami:

| Typ | Česky | Co to je | Výskyt |
|---|---|---|---:|
| **league** | Soutěž (úroveň) | Celá soutěž jedné úrovně (I. liga, II. liga…) | 1497× |
| **group** | Skupina / fáze | Část soutěže: základní část, skupina A/B/C | 4841× |
| **playoff** | Play-off (zastřešení) | Nadřazený uzel celého play-off | 36× |
| **playoff_round** | Kolo play-off | Čtvrtfinále, semifinále, finále (série zápasů) | 330× |
| **final_group** | Finálová skupina | Závěrečná skupina o titul (ne série, ale tabulka) | 673× |
| **final_series** | Finálová série | Finále hrané na série zápasů | 2× |
| **classification** | O umístění | O 3., 5., 7. místo, o udržení (tabulka) | 339× |
| **relegation_group** | Skupina o udržení | Týmy bojující o záchranu / proti sestupu | 140× |
| **relegation_playoff** | Baráž o sestup | Play-off o udržení | 1× |
| **baraz** | Baráž | Souboj MEZI úrovněmi (postup/sestup) | 361× |
| **qualification_group** | Kvalifikační skupina | Kvalifikace o postup (tabulka) | 165× |
| **qualification_series** | Kvalifikační série | Kvalifikace hraná na série | 6× |
| **regional_championship** | Krajský přebor | Krajská/oblastní soutěž | 101× |
| **series** | Série | Obecná série zápasů | 6× |
| **region** | Region | Regionální zastřešující uzel | 6× |

---

## 3. FÁZE SOUTĚŽE — flow

### 3.1 Základní část (ZČ)
**`group` s názvem „Základní část"**

- Všechny týmy hrají každý s každým (často 2× nebo 4×).
- Výsledek = **pořadí**, které určuje nasazení do dalších fází.
- ⚠️ **Ze základní části se zpravidla NESESTUPUJE ani NEPOSTUPUJE přímo** — je to jen rozřazení.
- **Osud (postup/sestup) se zde NEZOBRAZUJE** (pokud následuje další fáze).

### 3.2 Play-off (PO)
**`playoff` → `playoff_round`**

Vyřazovací část o titul. Týmy z horní poloviny ZČ. Kola:
- **Předkolo** — někdy (týmy 7.–10. v moderní extralize)
- **Čtvrtfinále** — 8 týmů → 4 série
- **Semifinále** — 4 týmy → 2 série
- **Finále** — 2 týmy → 1 série → **MISTR** 🏆

Hraje se na **série zápasů** (na 2/3/4 vítězné). Vítěz série postupuje.

### 3.3 O umístění
**`classification`**

Týmy vyřazené v play-off hrají o konečné pořadí:
- **O 3. místo** (bronz) — poražení semifinalisté
- **O 5. místo**, **O 7. místo** — nižší pořadí
- ⚠️ Zde se většinou **nerozhoduje o sestupu**, jen o estetické pořadí.

### 3.4 Skupina o udržení / záchranu
**`relegation_group` nebo `classification` s názvem „o udržení"**

- Týmy z **dolní poloviny** ZČ (např. 9.–12.).
- Hrají mezi sebou o to, kdo **sestoupí**.
- ⚠️ **TADY se rozhoduje o sestupu** — osud „sestup" patří SEM, ne do ZČ.
- **Vizuálně vyznačit** (červený rámeček, tag „skupina o udržení").

### 3.5 Baráž / Kvalifikace MEZI úrovněmi
**`baraz` nebo `qualification_group`**

- Souboj týmů z **DVOU sousedních úrovní** (např. poslední z extraligy × první z 1. ligy).
- Rozhoduje, kdo bude příští sezónu v které úrovni.
- Zobrazit jako **spojnici ↕ mezi úrovněmi** v pyramidě.

---

### 3.6 Kódování TOKU fází (entry / phase_order / feeds_into)

Aby šel flow soutěže přečíst strojově, má každý uzel fáze v listu **SYSTEM** tato pole:

| Pole | Význam | Příklad |
|---|---|---|
| `phase_order` | pořadí fáze v rámci soutěže (1 = ZČ) | `1`, `2`, `3`, `4` |
| `entry` | **kdo do fáze vstupuje** (kritérium) | `1.–8. ZČ`, `9.–12. ZČ`, `poražení ČF` |
| `feeds_into` | kam jdou **vítězové / postupující** (node_id) | → Semifinále |
| `feeds_into_loser` | kam padají **poražení** (node_id) | → O 5.-8.místo |

Rozvětvení po základní části se zapíše dvěma cíli ze ZČ: `feeds_into` = horní větev
(play-off), `feeds_into_loser` = dolní větev (skupina o udržení). Vícecestné rozdělení
(např. 1.–6. → ČF, 7.–10. → předkolo, 11.–14. → play out) se popíše polem `entry`
na cílových fázích.

**Příklad — extraliga 1988/89** (`phase_flow.py S1988_89`):

```
[1] Základní část     ← 12 týmů        vítěz→ Čtvrtfinále · poražený→ Skupina o udržení
[2] Čtvrtfinále       ← 1.–8. ZČ       vítěz→ Semifinále  · poražený→ O 5.-8.místo
[2] Skupina o udržení ← 9.–12. ZČ      poražený→ O 9.místo
[3] Semifinále        ← vítězové ČF    vítěz→ Finále      · poražený→ O 3.místo
[3] O 5.-8.místo      ← poražení ČF    vítěz→ O 5.místo   · poražený→ O 7.místo
[4] Finále            ← vítězové SF    (terminální → MISTR)
```

Generuje/čte `phase_flow.py`. **Plošně vyplněno přes `phase_flow.py --auto`**: tok
fází odvozen ze struktury (názvy uzlů + typy + seskupení po soutěžích přes
`parent_node_id` + počty týmů v tabulkách → pozice „1.–8."/„9.–12.") pro **633
soutěží / 2200 uzlů** v 73 ze 74 sezón. Pole protékají i do `almanach.sqlite`
(`competitions.entry`, `competitions.phase_order`). Auto je heuristika — u
exotických formátů může být `entry`/tok přibližný, dá se přepsat ručně.

---

## 4. KLÍČOVÝ PRINCIP — osud jen u terminální fáze

> **Postup/sestup (`season_fate`) se zobrazuje POUZE u poslední (terminální) fáze, ve které k němu reálně došlo.**

### Proč
Klub má v datech `season_fate` na **každém** svém řádku (v každé fázi). Ale fakticky k postupu/sestupu došlo jen v JEDNÉ fázi — té poslední.

### Příklad: TJ Baník ČSA Karviná (I. ČNHL 1986/87)

| Fáze | Pořadí | season_fate v datech | Zobrazit osud? |
|---|---|---|---|
| Základní část | 9. | sestup | ❌ NE (následuje další fáze) |
| Skupina o udržení | 12. | sestup | ✅ ANO (zde reálně sestoupil) |

Karviná skončila 9. v ZČ → spadla do skupiny o udržení → tam skončila 12. → **sestup**.
Kdyby se „sestup" zobrazil u ZČ, čtenář by si myslel, že 9. místo = sestup, což je **nesmysl**.

### Implementace
```python
def compute_terminal(blocks):
    """Pro každý klub vrátí index posledního bloku, kde se objevuje."""
    terminal = {}
    for block_index, block in enumerate(blocks):
        for row in block['rows']:
            terminal[row['club']] = block_index
    return terminal

# Při zobrazení:
show_fate = (terminal[club] == current_block_index)
fate = row['season_fate'] if show_fate else ''
```

**Totéž platí pro postup:** mistr (Poldi SONP Kladno) má „postup" až u finále play-off, ne u základní části.

---

## 5. VIZUÁLNÍ KONVENCE (pro Excel i HTML)

| Prvek | Význam | Barva / značka |
|---|---|---|
| **Postup** ▲ | klub postupuje výš | zelený řádek `#f0f7f0` |
| **Sestup** ▼ | klub sestupuje níž | červený řádek `#fbf0f0` |
| **Reorganizace** ◆ | změna kvůli reformě soutěží | žlutý řádek `#fbf8ed` |
| **Setrval** | klub zůstává v úrovni | neutrální (bez značky) |
| **M** mistr | vítěz nejvyšší soutěže | černý badge |
| **N** nováček | nově postoupivší | zelený badge |
| **S** sestupující | označen už v ZČ jako ohrožený | červený badge |
| **Skupina o udržení** | fáze o sestup | červený levý rámeček + tag |
| **Play-off** | vyřazovací část | modrá zóna |
| **Baráž ↕** | mezi úrovněmi | žlutá zóna |

---

## 6. STRUKTURA DAT V EXCELU

### 6.1 Soutěžní listy (10_liga, 20_1NHL, 30_2NHL, KVAL…)
Pevné indexy sloupců (POZOR — parsovat podle indexů, ne relativně!):

| Index | Sloupec | Popis |
|---:|---|---|
| 0 | row_type | `H` = hlavička bloku, `T` = řádek tabulky |
| 1 | block_name | název fáze (jen u `H`) |
| 2 | pos | pořadí |
| 3 | club_name | název klubu |
| 4 | note | M/N/S badge |
| 5 | GP | zápasy |
| 6 | W | výhry |
| 7 | D | remízy |
| 8 | L | prohry |
| 9 | GF | vstřelené |
| 10 | : | oddělovač |
| 11 | GA | obdržené |
| 12 | PTS | body |
| 13 | comp_path | cesta fází (hierarchie) |
| 14 | node_id | odkaz na SYSTEM uzel |
| 15 | level | L10/L15/L20… |
| 16 | club_id | trvalé ID klubu |
| 17 | prev_club_id | ID klubu v minulé sezóně |
| 18 | dest_node_id | kam klub postoupil |
| 19 | dest_type | typ cíle |
| 20 | **season_fate** | setrval/postup/sestup/reorganizace |
| 21 | tr_id | ID řádku tabulky |
| 22 | district | okres |

### 6.2 SYSTEM list — uzly soutěží
`node_id, name, competition_type, level, region, parent_node_id`

Stromová hierarchie: I. liga → Základní část / Play-off → Čtvrtfinále…
`parent_node_id` propojuje fáze do stromu.

### 6.3 SERIES list — série play-off
`series_id, node_id, club_id, raw_name, clean_name, side, game_scores, series_score, dest_node_id, note`

- `side` 1/2 = domácí/host
- `game_scores` = „6:1, 1:6, 1:0" (jednotlivé zápasy)
- `series_score` = „3:2" (celkový výsledek série)

---

## 7. FLOW PŘÍKLAD — extraliga 1986/87

```
┌─────────────────────────────────────────────┐
│ ZÁKLADNÍ ČÁST (12 týmů, každý s každým)      │  ← jen pořadí, BEZ osudu
└──────────────┬──────────────────┬────────────┘
               │ 1.–8.            │ 9.–12.
               ▼                  ▼
        ┌─────────────┐    ┌──────────────────┐
        │  PLAY-OFF   │    │ SKUPINA O UDRŽENÍ│  ← červeně, ZDE sestup
        │ ČF→SF→Finále│    │   (o sestup)     │
        └──────┬──────┘    └────────┬─────────┘
               ▼                    ▼
          🏆 MISTR              ▼ SESTUP
        (zde postup/titul)   (zde se zobrazí "sestup")
```

---

## 8. PLÁN IMPLEMENTACE DO EXCELU

### Fáze A — Doplnit metadata fází
1. Do SYSTEM listu doplnit u každého uzlu **čitelný popis** (`phase_description`):
   - „Základní část — týmy hrají každý s každým o nasazení"
   - „Skupina o udržení — týmy 9.–12. bojují o záchranu"
2. Doplnit pole `is_terminal` (true/false) — zda je fáze terminální pro výpočet osudu.

### Fáze B — Vizuální značení
1. Skupiny o udržení obarvit červeně (relegation_group, classification „udržení").
2. Play-off zóny modře.
3. Baráž žlutě.

### Fáze C — Logika osudu
Implementovat `compute_terminal()` do generátoru přehledů — osud jen u terminální fáze.

### Fáze D — Flow diagram per sezóna
Pro každou soutěž vygenerovat **flow diagram** (jako bod 7) — vizuální tok fází.

### Fáze E — Čtenářský popis
Ke každé sezóně krátký textový popis: „Jak probíhala soutěž" (2–3 věty) pro laiky.

---

## 9. TERMINOLOGIE PRO MLADÉ ČTENÁŘE

| Termín | Vysvětlení |
|---|---|
| **Základní část** | Úvodní fáze, kde hrají všichni se všemi. Určí pořadí. |
| **Play-off** | Vyřazovací boje o titul. Kdo prohraje sérii, končí. |
| **Série** | Souboj dvou týmů na více zápasů (např. „na 3 výhry"). |
| **Čtvrtfinále/semifinále/finále** | Postupná kola play-off (8→4→2 týmy). |
| **O umístění** | Zápasy o konečné pořadí mezi vyřazenými týmy. |
| **Skupina o udržení** | Slabší týmy bojují, aby nesestoupily. |
| **Baráž** | Souboj o postup/sestup mezi dvěma úrovněmi soutěže. |
| **Kvalifikace** | Předkolo o právo hrát v určité soutěži. |
| **Postup ▲** | Klub jde do vyšší soutěže. |
| **Sestup ▼** | Klub padá do nižší soutěže. |
| **Reorganizace ◆** | Změna kvůli reformě systému soutěží. |

---

## 10. PRAVIDLA — shrnutí

1. **Osud jen u terminální fáze** — postup/sestup zobrazit pouze tam, kde k němu reálně došlo.
2. **Základní část = jen pořadí** — nikdy osud, pokud následuje další fáze.
3. **Skupina o udržení vždy vyznačit** — vizuálně oddělit (červeně).
4. **Play-off jako série** — zobrazit jednotlivé zápasy i celkový výsledek série.
5. **Baráž/kvalifikace mezi úrovněmi** — zobrazit jako spojnici v pyramidě.
6. **Pevné indexy při parsování** — sloupce mají fixní pozice (viz bod 6.1).
7. **Data se nemění** — tato pravidla jsou pro ZOBRAZENÍ, ne pro úpravu dat.

---

**Tento dokument je živá ústava — bude se doplňovat při implementaci.**

---

## 11. DODATEK — Osud v baráži / prolínací soutěži / kvalifikaci

### Klíčové pravidlo: osud závisí na PŮVODU týmu

V baráži/kvalifikaci/prolínací soutěži se potkávají týmy z **DVOU sousedních úrovní**. Osud (`season_fate`) se přiřazuje **podle toho, odkud tým přišel** a zda uspěl:

| Původ týmu | Výsledek v baráži | season_fate | Vysvětlení |
|---|---|---|---|
| **Z vyšší úrovně** | uspěl (udržel se) | `setrval` | zůstal ve vyšší soutěži |
| **Z vyšší úrovně** | neuspěl | **`sestup`** ▼ | spadl do nižší |
| **Z nižší úrovně** | uspěl (postoupil) | **`postup`** ▲ | šel výš |
| **Z nižší úrovně** | neuspěl | **NIC (prázdné!)** | ⚠️ **zůstal v nižší — NESESTOUPIL** |

### ⚠️ Nejčastější chyba
Tým z nižší soutěže, který v baráži **neuspěl**, se vrací do své původní (nižší) soutěže — **NESESTOUPIL**, protože nikdy nebyl výš. V jeho řádku **NESMÍ být žádný osud** (ani „sestup", ani nic jiného) — kolonka osud je **prázdná**.

### Příklad: prolínací soutěž o I. ligu
```
Tým A (z I. ligy, extraliga)  → neuspěl → ▼ SESTUP   (spadl z extraligy)
Tým B (z 1. NHL)              → uspěl   → ▲ POSTUP   (šel do extraligy)
Tým C (z 1. NHL)              → neuspěl → (prázdné)  ← zůstal v 1. NHL, NESESTOUPIL
Tým D (z extraligy)           → uspěl   → setrval    (udržel extraligu)
```

### Implementace
```python
def baraz_fate(origin_level, result, club_level_in_baraz):
    """
    origin_level: 'higher' | 'lower' (odkud tým přišel)
    result: 'success' | 'fail'
    """
    if origin_level == 'higher':
        return 'sestup' if result == 'fail' else 'setrval'
    else:  # z nižší úrovně
        return 'postup' if result == 'success' else ''  # NIC při neúspěchu!
```

Původ týmu (`origin_level`) se určí porovnáním:
- úrovně, ze které tým do baráže vstoupil (jeho domovská soutěž v dané sezóně),
- vůči úrovni, o kterou se v baráži hraje.

### Zobrazení
- Tým z nižší úrovně bez postupu → **prázdná kolonka osud**, řádek neutrální (bez barvy).
- Pouze reálné postupy (▲) a sestupy (▼) se barevně značí.

---

## 12. AKTUALIZOVANÁ PRAVIDLA — shrnutí (v2)

1. **Osud jen u terminální fáze** — postup/sestup jen tam, kde k němu reálně došlo.
2. **Základní část = jen návaznost** — NIKDY season_fate; místo toho „► play-off" / „► o udržení".
3. **Skupina o udržení vždy vyznačit** — vizuálně (červeně).
4. **Play-off jako série** — jednotlivé zápasy + výsledek série.
5. **Baráž/kvalifikace mezi úrovněmi** — spojnice v pyramidě.
6. **Osud v baráži dle původu** — tým z nižší soutěže bez postupu = NIC (nesestoupil).
7. **Pevné indexy při parsování** — sloupce mají fixní pozice.
8. **Data se nemění** — pravidla jsou pro ZOBRAZENÍ.
9. **Postup do fáze ≠ postup mezi úrovněmi** — „► play-off" (uvnitř soutěže) vs „▲ postup" (mezi úrovněmi) jsou různé věci, různě značené.

---

## 13. ZÁSADNÍ PRINCIP — osud z porovnání úrovní mezi sezónami

### Pravidlo
`season_fate` se **NEODVOZUJE z poznámky v datech** (ta může být chybná), ale z **porovnání úrovně, na které tým sezónu ZAČÍNÁ, s úrovní, na které hraje v NÁSLEDUJÍCÍ sezóně**:

```
level_start  = úroveň týmu na začátku sezóny S (jeho domovská soutěž, NE baráž)
level_next   = úroveň téhož týmu (přes prev_club_id chain) v sezóně S+1

POROVNÁNÍ:
  level_next  výš  než level_start  →  ▲ POSTUP
  level_next  níž  než level_start  →  ▼ SESTUP
  level_next  ==   level_start      →  setrval (žádný osud)
  proběhla REORGANIZACE             →  ◆ "jiná píseň" (nelze prostě porovnat)
```

### Proč je to robustní
- Nezáleží na tom, co je napsané v poli `season_fate` — osud je **fakt odvozený z reality** (kde tým reálně hrál příští rok).
- Automaticky řeší baráž: tým z nižší soutěže, který nepostoupil, má `level_next == level_start` → **setrval, bez osudu** (nesestoupil).
- Automaticky řeší rozšíření/redukci soutěže: viz Motor 1972/73.

### Klíč: „úroveň, na které tým ZAČÍNÁ"
Tým hraje v jedné sezóně více fází (základní část, play-off, baráž). Jeho **startovní úroveň** je úroveň jeho **domovské soutěže** = kde odehrál základní část:
- Tým v extralize (L10) může hrát i baráž (L15) — jeho start level je **L10**, ne L15.
- Tým v 1. lize (L20) může hrát baráž o extraligu (L15) — start level **L20**.

Baráž (L15/L25/L35) NENÍ startovní úroveň — je to mezičlánek.

### Příklad: Motor České Budějovice
```
1972/73: start level = L10 (extraliga, základní část, 10. místo)
         → baráž (prolínací soutěž), obhájil
1973/74: level = L10 (extraliga, 10. místo z 12)   ← přes prev_club_id

L10 → L10  =  SETRVAL (žádný osud)  ✓
```
Tým NESESTOUPIL, protože příští sezónu hrál opět extraligu. Rozšíření z 10 na 12 klubů je důvod, proč se z 10. místa nesestupovalo — ale to NEMUSÍME řešit zvlášť: porovnání úrovní to vyřeší samo.

### Příklad: tým z 1. ligy v baráži, který nepostoupil
```
1972/73: start level = L20 (1. liga)
         → baráž (prolínací soutěž), neuspěl
1973/74: level = L20 (1. liga, nebo její nástupce)  ← přes prev_club_id

L20 → L20  =  SETRVAL (žádný osud)  ✓  (nesestoupil — vrátil se domů)
```

### Reorganizace = „jiná píseň"
Když se mezi sezónami změní STRUKTURA soutěží (vznik/zánik úrovně, přečíslování), prosté porovnání úrovní selže — úroveň L20 v sezóně S nemusí odpovídat L20 v S+1.

Příklady reorganizací (NEPOROVNÁVAT prostě úrovně):
- **1953/54** — vznik celostátní 2. ligy
- **1960/61** — sjednocení 2. ligy
- **1973/74** — vznik 1. ČNHL a 2. ČNHL (přečíslování celé pyramidy)
- **1993/94** — rozdělení ČSSR (odešly slovenské kluby)

V těchto přechodech se osud určuje **ručně / z kontextu reformy**, ne porovnáním čísel úrovní. Označit jako ◆ reorganizace.

### Implementace
```python
def derive_fate(club_id, season, next_season, clubs_data, is_reorg_transition):
    if is_reorg_transition:
        return 'reorganizace'  # jiná píseň
    
    start_level = home_level(club_id, season)        # domovská soutěž (ZČ), ne baráž
    successor = find_successor(club_id, next_season) # přes prev_club_id
    if successor is None:
        return ''  # zánik / nenavázáno — neřešit zde
    next_level = home_level(successor, next_season)
    
    if next_level < start_level: return 'postup'   # nižší číslo = vyšší soutěž
    if next_level > start_level: return 'sestup'
    return 'setrval'  # žádný osud k zobrazení

def home_level(club_id, season):
    """Úroveň základní části (domovská soutěž), NE baráž (L15/L25/L35)."""
    levels = [r.level for r in rows_of(club_id, season)]
    # vyfiltrovat baráže (L_5) — vzít hlavní úroveň
    home = [L for L in levels if not is_baraz_level(L)]
    return min(home)  # nejvyšší soutěž (nejnižší číslo), kde tým hrál ZČ
```

---

## 14. PRAVIDLA — finální shrnutí (v3)

1. **Osud = porovnání úrovní mezi sezónami** (start vs. next), NE poznámka v datech.
2. **Startovní úroveň = domovská soutěž (ZČ)**, ne baráž (L15/L25/L35).
3. **Reorganizace = „jiná píseň"** — neporovnávat úrovně, určit z kontextu reformy (◆).
4. **Osud jen u terminální fáze** — zobrazit jen tam, kde k němu reálně došlo.
5. **Základní část = jen návaznost** (► play-off / ► o udržení), nikdy osud mezi úrovněmi.
6. **Baráž: výsledek se promítne do úrovně příští sezóny** — tým z nižší bez postupu = setrval = bez osudu.
7. **Skupina o udržení vždy vyznačit** (červeně).
8. **Play-off jako série** (zápasy + výsledek série).
9. **Baráž ≠ skupina o udržení** — baráž je mezi úrovněmi (žlutě), udržení je uvnitř soutěže (červeně).
10. **Pevné indexy při parsování**; **data se nemění** (pravidla pro zobrazení).

---

## 15. ZÁVISLOST — princip vyžaduje správný chain (prev_club_id)

Porovnání úrovní mezi sezónami stojí a padá na **správně navázaném `prev_club_id`** (klub v sezóně S+1 ukazuje na svůj záznam v sezóně S).

### Co se stane při chybném chainu
Pokud je `prev_club_id` špatně (ukazuje na jiný klub / chybí), porovnání úrovní dá nesmysl:
```
Dukla Jihlava  L10 → L20  (zdánlivý SESTUP)   ← ARTEFAKT špatného chainu
```
Dukla Jihlava ve skutečnosti zůstala v extralize — jen byl chain přerušen reorganizací 1973/74.

### Pravidla pro spolehlivý výpočet osudu
1. **Před výpočtem osudu ověř chain** — `prev_club_id` musí ukazovat na existující záznam téhož klubu.
2. **Při reorganizaci chain nespoléhej** — přečíslování úrovní láme porovnání → označ ◆ „jiná píseň".
3. **Nenavázaný klub** (žádný následovník v S+1) → osud prázdný (zánik / přestávka — neřeš zde, viz audit prostupnosti).
4. **Více záznamů klubu v S+1** (fáze soutěží 2013+) → porovnávej s domovskou úrovní (ZČ), ne s barážovým záznamem.

### Pořadí kroků v generátoru
```
1. Načti kluby sezóny S a S+1
2. Sestav chain: successor[club_id_S] = club_id_S+1 (přes prev_club_id)
3. Pro každý klub:
   a. start_level = home_level(S)         # ZČ, ne baráž
   b. je-li S→S+1 reorganizace → osud = ◆, KONEC
   c. successor? ne → osud = '', KONEC
   d. next_level = home_level(successor, S+1)
   e. porovnej → postup / sestup / setrval
4. Zobraz osud jen u terminální fáze (sekce 4)
```

### Vztah k auditu prostupnosti
Tento princip je **druhá strana** auditu chain breaks (viz PROSTUPNOST_AUDIT.md):
- Audit prostupnosti = zajišťuje, že chain je správný (prev_club_id navázán).
- Princip osudu = používá ten chain k odvození postupu/sestupu.

Čím lepší chain integrita (aktuálně 99,99 %), tím spolehlivější výpočet osudů.

---

**Konec ústavy fází soutěží — v3. Připraveno k postupné implementaci do Excelu i zobrazovací vrstvy.**
