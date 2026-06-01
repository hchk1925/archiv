# CLAUDE.md — Hokejový almanach DB
### Onboarding pro agenta · Duben 2026 · Verze 3.3

> **Pracovní jazyk:** česky (odpovědi, komentáře k datům).  
> **Kód / identifikátory:** anglicky (sloupce, klíče, Python).

> **Update v3.3 (04/2026):** Přidána pravidla D37–D43 (D42=registr identit, D43=disambig formáty) z práce na 53/54 a 54/55. Audit duplicit napříč 6 sezónami (29 sloučení). Dokončen audit sezón 53/54 (98%) a 54/55 (97%).

---

## 1. Co je tento projekt

**Hokejový almanach** — strojově čitelná historická DB výsledků čs./čes./slov. ledního hokeje.

- Jeden Excel workbook = jedna sezóna: `S{RRRR}_{RR}_FINAL.xlsx`
- Každý klub sledovatelný řetězem `prev_club_id` přes všechny sezóny
- Pokrývá ligu, kvalifikace i krajské soutěže

**Aktuální rozsah:** 72 sezón **1949/50 – 2020/21** — všechny dokončeny (`season_fate` + `city`).

**Plán:** Rozšiřování **pozpátku** před 1949/50 (1948/49, 1947/48 …) — fragmentovaná struktura, nutno komunikovat detail po detailu.

**Editor:** `OSAlmanach.py` (Python/Tkinter) — viz kap. 9.

---

## 2. Stav zpracování

| Oblast | Stav |
|--------|------|
| `season_fate` L10–L35 | ✅ 100 % (72 sezón) |
| `city` v CLUBS | ✅ 100 % (72 sezón) |
| `NOTES` listy | ✅ přítomny ve všech sezónách |
| `KVAL` level L15/L25 | ✅ opraveno retroaktivně |
| **Audit 49/50** | ✅ duplicita Sokol Mšec sloučena (04/2026) |
| **Audit 51/52** | ✅ duplicita ONV Český Těšín sloučena (04/2026) |
| **Audit 52/53** | ✅ duplicita ZPS Gottwaldov sloučena (04/2026) |
| **Audit 53/54** | ✅ kompletní (A,B,C,F,G,H ~98%, 8 v TODO) (04/2026) |
| **Audit 54/55** | ✅ kompletní (A,B,C,F,G,H ~97%, 6 v TODO) (04/2026) |
| Sezóny před 1949/50 | ❌ čekají (nový chat) |
| `dest_node_id/dest_type` | ⚠️ záměrně prázdné (low priority) |
| `SERIES` detaily | ⚠️ částečně (playoff série) |

---

## 3. Struktura adresáře

```
almanach/
  S1949_50_FINAL.xlsx   ← 1949/50
  S1950_51_FINAL.xlsx
  …
  S2020_21_FINAL.xlsx   ← 2020/21
OSAlmanach.py           ← editor (může být ve stejném adresáři jako xlsx)
HOKEJ_ALMANACH_TECHNICKY_REPORT.md  ← podrobná tech. zpráva
CLAUDE.md               ← tento soubor
```

Soubory s příponou `-opravene.xlsx` jsou pracovní varianty, ne primární výstup.

---

## 4. Layout datového listu (23 sloupců A–W)

### Levá část — pro laika (A–M)

| Sl. | Název | H | T | S | R |
|-----|-------|---|---|---|---|
| A | `row_type` | `H` | `T` | `S` | `R` |
| B | `block_name` | nadpis | — | — | — |
| C | `pos` | — | pořadí | — | — |
| D | `club_name` | — | název klubu | popis série | název klubu |
| E | `note` | — | N/S/M | — | — |
| F–M | GP,W,D,L,GF,:,GA,PTS | — | statistiky | — | — |

### Pravá část — kódy (N–W)

| Sl. | Název | Popis |
|-----|-------|-------|
| N | `comp_path` | „I. liga / Základní část" |
| O | `node_id` | `NODE_S1990_91_0001` |
| P | `level` | L10, L20, L30… |
| Q | `club_id` | `CLUB_S1990_91_0007` |
| R | `prev_club_id` | Odkaz do předchozí sezóny |
| S | `dest_node_id` | Cílový node v téže sezóně |
| T | `dest_type` | playoff / kvalifikace / zachrana / finale |
| U | `season_fate` | Osud klubu po sezóně |
| V | `tr_id` | `TR_S1990_91_00042` |
| W | `district` | Okres (jen R-řádky) |

### Typy řádků

| Typ | Povinné | Prázdné |
|-----|---------|---------|
| **H** — záhlaví bloku | B, O, P | C–M, Q–W |
| **T** — klub v tabulce | C–M, O–V | — |
| **S** — série (playoff) | D, O, Q | C, F–M |
| **R** — registrovaný klub bez tabulky | D, O, P, Q, R, W | F–M, S–V |

---

## 5. Pomocné listy

### CLUBS

`club_id | clean_name | raw_name | sheet | level | entry_note | prev_club_id | change_note | city`

- `level` = nejvyšší soutěž kde klub v sezóně hraje jako **primární** (ne baráž/KVAL)
- `city` = historické sídlo (viz §8)
- `prev_club_id` = odkaz na CLUBS **předchozí sezóny**

### META

`key | value` — `season_id`, `season_label`, `era_note`, `scoring_system`, `source`, `total_nodes`, `total_clubs`, `prev_season`, `prev_club_matched`, `note`

### SYSTEM

Hierarchie uzlů: `node_id | name | competition_type | level | region | parent_node_id | feeds_into | feeds_into_loser | scoring | status | note`

### SERIES

Playoff série: `series_id | node_id | club_id | raw_name | clean_name | side | game_scores | series_score | dest_node_id | note`

### NOTES

`node_id | sheet | note_text | source_type | fake_club_ids`  
`source_type`: `T`, `H`, `DS-PDF`, `manual`

### Pořadí listů v workbooku

```
Republikové (10_liga, 20_…, 30_…, 40_…, KVAL)
Regionální CZ (30PRAH, 30STRC, …)
Regionální SVK (30ZASL, 30STSL, 30VYSL)   ← jen do 92/93
────────────────────────────────────────
NOTES → SYSTEM → SERIES → CLUBS → META
```

---

## 6. Identifikátory

```
NODE_S{RRRR}_{RR}_{NNNN}    ← soutěžní uzel      (4 číslice)
CLUB_S{RRRR}_{RR}_{NNNN}    ← klub v sezóně      (4 číslice)
TR_S{RRRR}_{RR}_{NNNNN}     ← T-řádek            (5 číslic)
```

**Pravidla:** po přidělení **neměnné**. Přejmenování klubu mění `clean_name`, ne `club_id`. Unikátní v rámci sezóny.

---

## 7. Úrovně soutěží (level)

| level | Soutěž |
|-------|--------|
| L10 | I. liga / Extraliga |
| L15 | Baráž / Kvalifikace o L10 |
| L20 | II. liga / I. ČNHL / I. SNHL / 1. liga |
| L25 | Baráž / Kvalifikace o L20 |
| L30 | II. ČNHL / II. SNHL / Krajský přebor / 2. liga |
| L35 | Kvalifikace o L30 |
| L40 | Divize (od 73/74) / nižší krajské |
| L45 | Kvalifikace o L40 |
| L50+ | Nižší oblastní, okresy |

> ⚠️ **SNHL = L20.** „Kvalifikace o SNHL" = **L25** (ne L15!).  
> L15 je výhradně pro kvalifikaci s cílem L10 (I. liga).

---

## 8. season_fate — pravidla

### Hodnoty

| hodnota | popis |
|---------|-------|
| `setrval` | Ověřeno — hraje stejnou soutěž příští sezónu |
| `setrval?` | Pravděpodobně setrval, neověřeno (L40+, nebo příší workbook chybí) |
| `postup` | Postoupil do vyšší soutěže |
| `sestup` | Sestoupil do nižší soutěže |
| `zanik` | Klub zanikl, nemá pokračovatele |
| `slouceni` | Zanikl jako entita, ale pokračuje přes B tým nebo fúzi |
| `reorganizace` | Přečíslování bez pohybu; odchod do jiné národní federace |

### Algoritmus (standardní cross-ref)

```python
# Zpětná mapa z CLUBS příší sezóny:
prev_to_min_next = {prev_cid: min(level) for prev_cid → cid_next}

next_lv = prev_to_min_next.get(club_id)
clubs_lv = clubs_lv_map[club_id]   # z CLUBS aktuální sezóny

if next_lv is None:        fate = "zanik"
elif next_lv < clubs_lv:   fate = "postup"
elif next_lv > clubs_lv:   fate = "sestup"
else:                      fate = "setrval"

# Výjimka baráž (clubs_lv=L15 = barážní blok):
if clubs_lv == 15 and next_lv == 20:
    fate = "setrval"   # klub se vrátil do 1. ligy, žádný pohyb
```

### Klíčová pravidla

1. **Jeden `club_id` = jedna `fate`** napříč všemi listy sezóny.
2. **KVAL fate:** pouze `postup` nebo `setrval` (sestup v KVAL neexistuje).
3. **Baráž setrval:** klub z L10 prošel baráží a zůstal v L10 → `setrval`.
4. **False reorganizace:** `lv_from>=30 AND lv_to>=30 AND |lv_to-lv_from|>5` → `reorganizace`.
5. **SK kluby po 92/93:** odchod do SK soutěže → `reorganizace`.
6. **COVID 19/20:** krajské soutěže nedohrány → krajské = `setrval` (ne sestup).
7. **Mistr ≠ vítěz ZC** od 93/94 (playoff éra) — dokumentuj obojí odděleně v NOTES.
8. **slouceni:** klub ukončil vyšší entitu, ale pokračuje přes B tým v krajském (kontinuita přes B entitu).

### Konzistence fate

```python
# Validace: každý club_id má max. 1 fate hodnotu
for cid, fates in cid_fate_dict.items():
    assert len(set(fates)) <= 1
```

---

## 9. KVAL list — pravidla

Všechny republikové kvalifikace na jeden list `KVAL`. **Neexistuje `KVAL_SNHL`** (zrušen, obsah sloučen).

### Level H-řádků (cílová soutěž + 5)

| Cíl vítěze | Level | Příklad block_name |
|-----------|-------|--------------------|
| I. liga (L10) | **L15** | „Baráž o I. ligu" |
| I. ČNHL / SNHL (L20) | **L25** | „Kvalifikace o SNHL" |
| II. ČNHL / SNHL (L30) | **L35** | „Kvalifikace o II. ČNHL" |
| Divize (L40) | **L45** | „Kvalifikace o divizi" |

Sub-skupiny (A/B/C): `level = NaN` — T-řádky dědí level nejbližšího H.

### Kaskádový bug

Pokud `block_name` H-řádku obsahuje vzor `\d:\d` (výsledek série) → chyba pipeline. Opravit dle `node_id` a kontextu.

---

## 10. city — pravidla

Historické sídlo klubu v době sezóny.

1. **Bez suffixu B** — `"Kladno"` i pro `"SONP Kladno B"`
2. **Bez organizačních prefixů** — `"Železný Brod"` (ne `"ŽS Železný Brod"`)
3. **Bez regionálních anotací** — `(VYS)`, `(OLO)` apod. ignorovat
4. **Dukla L10** → vždy `city="Jihlava"`; Dukla L20 v 50. letech → `city="Olomouc"`
5. **Historický název** — Gottwald → Zlín platí od 1990/91

---

## 11. Krajské kódy a éry

### Éra 14 krajů ČSR (1949/50–1959/60)
`PHAM, PHAV, JHCK, PLZN, KVRY, USTE, LIBE, PARD, HRAD, JIHL, BRNO, GOTT, OLOM, OSTR`  
Slovensko: `BRAT, NITR, BANS, ZILI, KOSI, PRES`

### Éra 7 krajů ČSR (1960/61–2001/02)
`PRAH, STRC, JHCK, ZAPC, SVRC, VYCH, JHMR, SVMR, CEMO (od 70/71)`  
Slovensko: `ZASL, STSL, VYSL`

### Éra 14 krajů ČR (2002/03+) — přibývání

| Sezóna | Nové kódy |
|--------|-----------|
| 93/94 | PRAH, STRC, JHCK, ZAPC, SVRC, VYCH, JHMR, SVMR |
| 02/03 | JMVY, KVRY, LIBE, PLZN, ZLIN, USTE |
| 03/04 | VYSO, OLOM, MSKR |
| 05/06 | HRAD, JMZL, PARD, LBUS |
| 07/08 | USKV |
| 18/19 | 30_Plzeňský-KV |

> Regionální anotace v závorce v `club_name` (např. `(VYS)`) se při extrakci `city` ignoruje. Klub hrající mimo svůj geografický region je validní.

**Dynamický prefix:** KP na L20 → prefix 20 (20PHAM). KP na L30 → prefix 30 (30PRAH). KP na L40 → prefix 40.

---

## 12. Co agent NESMÍ dělat

1. Přepisovat `node_id`, `club_id`, `tr_id` bez explicitního potvrzení
2. Vytvořit list `KVAL_SNHL` — byl zrušen, neexistuje
3. Nastavit `season_fate=sestup` v KVAL listu
4. Nastavit KVAL blok o SNHL/I.ČNHL na L15 (správně L25)
5. Mazat listy (i prázdné NOTES/SERIES jsou záměrné)
6. Mergeovat `club_id` bez potvrzení
7. Přidávat sloupce mimo A–W v datových listech
8. Označit `setrval?` jako chybu — je validní hodnota

---

## 13. Typická pracovní sada pro novou sezónu

```python
# 1. Načti CLUBS příští sezóny → prev_to_min_next
# 2. Oprav KVAL level H-řádků (L15→L25 kde block_name obsahuje "II.ligy" nebo "SNHL")
# 3. Doplň season_fate cross-refem (viz §8)
# 4. Oprav false sestupy v krajských → reorganizace
# 5. Konzistuj fate napříč listy (jeden club_id = jedna fate)
# 6. Hledej chybějící prev_club_id linky (nástupci bez linku)
# 7. Doplň city do CLUBS
# 8. Přidej NOTES (mistr, klíčové události)
# 9. Ulož
```

**Chybějící linky:** pokud klub v příší sezóně nemá `prev_club_id` a odpovídá jménem → oprav link v CLUBS příší sezóny.

**Zanik vs. slouceni:** bez nástupce = `zanik`. B tým přebral identitu = `slouceni` + dokumentuj `change_note`.

---

## 14. Editor OSAlmanach.py

Spuštění: `python OSAlmanach.py [cesta]`  
Auto-detekce adresáře: nejprve `./almanach/`, pak stejný adresář jako skript.  
Závislosti: `pip install openpyxl pandas`

### Klávesové zkratky

| Klávesa | Akce |
|---------|------|
| `Ctrl+S` | Uložit aktuální sezónu |
| `Ctrl+K` | Otevřít KlubEditor (průřez historií) |
| `Ctrl+F` | Hledání |
| `Ctrl+G` | Přejít na sezónu |
| `Delete` | Smazat vybraný řádek (s potvrzením) |
| Pravé tlačítko | Kontextové menu (edit / detail / smazat) |
| Double-click | Inline edit buňky |

### KlubEditor (Ctrl+K)

Otevře průřez historií klubu přes **všechny sezóny** (sleduje prev_club_id řetěz dozadu i dopředu):

- Horní tabulka: Sezóna | Název | Úr. | Fate | Město | club_id | prev_club_id
- Aktuální sezóna tučně modře
- Double-click na sezónu → naviguj hlavní okno
- Dolní tabulka: výskyty ve vybrané sezóně
- Hromadné fate / city pro celou sezónu jedním klikem

### Dirty state

- Neuložená sezóna = `●` v navigátoru
- Přechod na jinou sezónu / zavření → dialog Uložit/Zahodit/Zrušit
- Změny se pamatují při přepínání listů téže sezóny

---

## 15. Plán: sezóny před 1949/50

Zpracování půjde **pozpátku**: 1948/49, 1947/48 …

**Proč pozpátku:** 1949/50 je kotva (existující `prev_club_id` chain). Napojujeme se na ni.

**Specifika pre-1949:**
- Soutěžní struktura výrazně fragmentovaná (Čechy ≠ Morava ≠ Slovensko)
- Válečné přerušení, reorganizace, neúplné prameny
- Různé systémy v různých regionech souběžně
- Výrazně vyšší míra nejistoty → `setrval?` liberálněji
- Každá sezóna = **samostatná komunikace**, detail po detailu

**Krajské kódy pre-1949:** pravděpodobně župní dělení (jiné než poválečné krajské). Nutno konzultovat před zpracováním.

**Otevřené otázky pro pre-1949:**
- Jaký je přesný žánrový/župní systém kódů?
- Existuje L10 kontinuálně, nebo jsou mezery?
- Jaký formát zdrojů (tisk, rukopisy, sekundární literatura)?

---

## 16. Rozhodovací log (Decision Log)

| # | Rozhodnutí |
|---|-----------|
| D01 | `KVAL_SNHL` → sloučeno do `KVAL` |
| D02 | KVAL SNHL level = L25 (ne L15) |
| D03 | False přečíslování krajských → `reorganizace` |
| D04 | `city`: bez suffix B, bez org. prefixů, bez (VYS)(OLO) anotací |
| D05 | `setrval→postup`: 37 oprav cross-check (retroaktivně) |
| D06 | Konzistence fate: jeden `club_id` = jedna `fate` v sezóně |
| D07 | KVAL level L15→L25 opraveno retroaktivně ve všech sezónách |
| D08 | Kaskádový block_name bug (S-řádky) opraveno |
| D09 | Mistr ≠ vítěz ZC od 93/94 |
| D10 | Baráž setrval: `clubs_lv=15 AND next=20 → setrval` |
| D11 | Tábor 09/10: `zanik→slouceni` (B tým přebral identitu) |
| D12 | COVID 19/20: krajské soutěže = `setrval` (nedohrána sezóna) |
| D13 | Regionální anotace v závorce ignorovat při extrakci `city` |
| D14 | Dukla L10 → `city="Jihlava"` vždy |
| D15 | SK kluby po 92/93 → `reorganizace` |
| D16 | `clubs_lv` = nejvyšší primární soutěž (ne baráž/KVAL) |
| D17 | Přejmenování: mění `clean_name`, ne `club_id`; dokumentuj `change_note` |
| **D18** | **Identity transitions** (přejmenování / fúze / přesun pod jinou organizaci): řešit JEN s 100% jistotou z primárního zdroje (wiki, PDF, dobový tisk, kniha). Bez doložení nesahat na `clean_name`/`raw_name`. TBD-flag. |
| **D19** | **TBD-flag konvence:** prefix `TBD:` v `change_note` (případně `TBD-IDENTITY:` pro identity transitions); paralelní `[TBD]` v NOTES. Pavel filtruje. |
| **D20** | **B-tým vlastní `club_id`:** B-tým má vždy vlastní řádek v CLUBS (vlastní identita), nepřepojuje se na A-tým. |
| **D21** | **B-tým name pravidlo (STRIKTNĚ, bez výjimky):** B-tým má **vždy** stejný kořen jako A-tým + suffix B. Použít **složitější verzi** názvu pro oba (A i B). Platí pro **všechny kluby napříč všemi sezónami**, i když almanach má B-tým s historickou stopou (např. SONP Kladno B vs A-tým Baník Kladno → B přepsat na „Baník Kladno B"). Příklady viz § 18. |
| **D22** | **„Sokol" povinné označení té doby (1949–1953):** Sokol byl povinný prefix sokolských klubů. Při zachování `clean_name` z almanachu (např. „Sokol Spojocel Chomutov II") jde o vývoj klubu — nepřejmenovávat na pozdější verzi, jen flag v `change_note`. **Výjimka:** B-týmy přejmenovat dle pravidla D21. |
| **D23** | **City u velkých měst (Praha, Brno, Ostrava, Karviná, …):** Pokud klub nese v názvu městskou část (Hulváky, Fryštát, Košíře, Vítkovice, …), `city` = **město** (ne městská část). Městská část zůstává v `clean_name`. |
| **D24** | **Smart fix `prev_club_id`:** Pokud broken link (prev → neexistující ID) nebo zjevně chybný prev, ale existuje evidentní kandidát se stejným `clean_name` + regionem v předchozí sezóně, mlčky propojit + TBD-flag pro pozdější verifikaci. |
| **D25** | **Default `fate` při nejistotě = `setrval?`** (s otazníkem; aplikuje se hromadně na konci auditu). |
| **D26** | **City disambiguator:** Stačí blízkost většího známého sídla (formát: „Obec (OkresnĚkyMěsto)", např. „Lány (Kladno)"). Velká nezaměnitelná města (Praha, Brno) bez disambiguatoru. **Default při pochybnosti = dát disambiguator** pro orientaci. |
| **D27** | **Identitní pravidlo katalogu:** **2 různé kluby = 2 různá `club_id`, vždy.** Při sdílení ID nutný split (vznik nového ID v hierarchii). |
| **D28** | **Éra Spartak/Dynamo/Jiskra/Baník/Slavoj — pomalý nástup od 1951/52, plný rozjezd později:** V 51/52 dominuje ještě **ZSJ-éra** (Závodní sokolská jednota), socialistická přejmenování Sokol → Spartak/Dynamo/Jiskra/Baník/Slavoj jsou zatím **výjimečná** (jednotlivé kluby). Plný plošný přechod přijde pravděpodobně v 52/53 a později. **Stále platí D18** (verifikace primárním zdrojem) — TBD-IDENTITY flag pro pozdější verifikaci. |
| **D29** | **B-tým bez A-týmu = audit selhal:** Pokud najdeme B-tým, **musí v té samé sezóně existovat A-tým**. Pokud A-tým chybí, je to chyba (kolega v nižších soutěžích občas není precizní v názvech). Postup: dohledat A-tým podle prev_club_id, kontextu skupiny, nebo identity transition; přejmenovat B-tým dle D21. Bez identifikace A-týmu nelze klub auditovat. |
| **D30** | **KVAL fate je nezávislé:** Klub má v sezóně `fate` jen ze základní soutěže (L10/L20/L30/...). KVAL/MS (L15/L25/L35) reprezentuje účast v baráži, **fate v KVAL listě má být prázdné**. Při auditu inkonzistencí fate plošně čistit fate v KVAL u klubů s prev/cid v 20_*/30_*/atd. |
| **D31** | **Identity transition NEPROPAGOVAT zpět:** Když identifikujeme řetězec přejmenování (např. Sokol Hutě → Baník Chomutov ZJF), v každé sezóně **clean_name = autentický název té sezóny** (nikdy přepisovat starou sezónu na novější název!). Genealogii zaznamenat **jen do `change_note`** jako informativní propojení (např. „Pokračování v 52/53: Baník Chomutov ZJF"). Excel sezóna je pravda; Wiki = jen genealogie identit. |
| **D32** | **clean_name = dobový název, city = moderní orientace.** Pro Gottwaldov platí: clean_name zachovává „Gottwaldov" (autentický název 1949-1989), city = „Zlín" (moderní orientace pro vyhledávání). Pro Otrokovice a další samostatná města zůstává city podle skutečnosti (Otrokovice ≠ Zlín). |
| **D33** | **PDA / DA = Posádkový dům armády / Dům armády** (vojenský klub). Většina měst měla jednu vojenskou posádku → jeden PDA/DA klub. **DA = novější forma PDA** (od ~54/55). **České Budějovice** mají v 52/53 dvě posádky → **PDA I. České Budějovice** (CLUB_S1952_53_0100) a **PDA II. České Budějovice** (CLUB_S1952_53_0104) jsou **DVA NEZÁVISLÉ KLUBY**, ne A+B! Pozor: římské „I." / „II." u PDA neznamená A/B, ale různé posádky. **Lokalita PDA/DA klubu (DŮLEŽITÉ — Pavlovo pravidlo 04/2026):** (a) Pokud almanach uvádí město v názvu *(např. „PDA Hradec Králové", „DA Stráž", „PDA Čáslav")* → city = město. (b) Pokud sheet je velkoměstský *(PHA_mesto)* → city = velkoměsto *(odlišení od stejných klubů jinde)*. (c) Pokud almanach má jen abstraktní přízvisko/přezdívku/bojový pomník *(Jaslo, Stalingrad, Sokolovo, Tankista, Úder, Blesk, Čapajev, Pravda, Jiskra, Vysočina, Sněžka, Radbuza, Ostrožan, Psohlavci, Disk, Šohaj, Blaník, Turbina, Gardista, Útok, Oděsa)* **bez města v almanachu** → **city VŽDY prázdné** *(nezeptávat se Pavla, je to defaultní pravidlo)*. (d) Stejně pojmenovaný PDA/DA klub v jiném městě = jiný klub *(DA Jiskra Praha ≠ DA Jiskra Olomouc — různé cid)*. |
| **D34** | **Známá fate hodnoty:** `setrval`, `sestup`, `postup`, `nehraje`, `reorganizace`. „reorganizace" se objevuje od 53/54 (velká reorganizace ČS hokeje 1954) — klub byl přesunut do nové soutěže/struktury bez klasického postupu/sestupu. KVAL fate musí být **vždy prázdné** (D30). |
| **D35** | **53/54: ponecháváme almanachové názvy klubů** (ne striktní sjednocení A+B dle D21). Almanach 53/54 má TJ prefix selektivně u některých klubů (např. „TJ Spartak Motorlet" vs „Spartak Tatra Smíchov B" bez TJ) — to je autentický záznam a zachováváme. D21 striktní pravidlo je pozastaveno pro 53/54+. **Pravidlo o organizační formě** *(Pavlovo upresneni 04/2026)*: Pokud se klub liší **jen prefixem organizační formy** *(TJ / DSO / DŠO / DSJ / Sokol / žádný)* → **je to TENTÝŽ klub** *(jen měnila se org. forma, např. 1948 Sokol → 1949 ZSJ → 1952 DSO → 1956 TJ)*. To znamená: prev_club_id ve formě „TJ X" → „DSO X" je legitimní, identita klubu zůstává. |
| **D36** | **Výjimka pro okresní úroveň:** Na nejnižší úrovni (okresní/L40) může A-tým a B-tým téhož klubu hrát **ve stejné soutěži** (stejný level, stejná skupina). Není to chyba — je to organizační realita okresního hokeje. (Příklad: 53/54 0208 Lokomotiva Plzeň + 0205 Lokomotiva Plzeň B, oba okresní.) |
| **D37** | **Ostravské části — city formát „Ostrava-X".** Pro části/čtvrti Ostravy se používá **city = „Ostrava-X"** (s pomlčkou), nikoli jen „Ostrava" nebo jen „X". Příklady: Ostrava-Poruba, Ostrava-Hrušov, Ostrava-Mariánské Hory, Ostrava-Polanka, Ostrava-Pustkovec, **Ostrava-Vítkovice, Ostrava-Hulváky, Ostrava-Svinov, Ostrava-Kunčice, Ostrava-Přívoz, Ostrava-Radvanice, Ostrava-Michálkovice** (přidáno 04/2026). Samostatné obce u Ostravy *(Klímkovice, Horní Lhota, Vratimov)* zůstávají s vlastním city. **Bohumín** má obdobu D37 — pro části Bohumína (Pudlov, Záblatí, Skřečoň, Vrbice, Starý Bohumín, Nový Bohumín) → city **„Bohumín-X"** (Pavlovo upresneni 04/2026 — Pudlov pro 56/57 0608). **Pozor:** Vítkovice **klub** (Baník Vítkovice) je samostatný od Baníku Ostrava — jiný klub s jiným cid, ale **stejné city Ostrava-Vítkovice**. |
| **D38** | **Doly = pojmenování klubu, ne lokality.** Kluby s prefixem „Horník" *(důl)* nebo „Baník" *(uhelný revír)* mají v názvu jméno dolu (Pionýr, Kamčatka, Stalingrad, 1. máj, Sovinec, ČSA, Mír, Zápotocký, ...). Pokud almanach uvádí město → city = město *(např. Horník Sovinec Karviná → city Karviná)*. Pokud almanach jméno města neuvádí → **city zůstává prázdné** *(důl je pojmenování, ne lokalita)*. Stejná logika jako PDA bez města *(D33)*. |
| **D39** | **Pravidlo o duplicitách:** Když má sezóna 2+ záznamy se stejným `clean_name` + `sheet`, rozlišit dle úrovně: **(a) okresní / L40** → klub může figurovat **jen 1× v sezóně**, jakákoli duplicita = chyba parsu/kolegy = sloučit *(zachovat nižší cid, T/R-řádky převést)*. **(b) Krajský přebor / L20 / L10** → soutěž má fáze *(skupina A/B → finále → o udržení)*; klub má **1 cid** ale v T/R figuruje vícekrát *(různé fáze, stejný klub)*. Nikdy nedávat 2 cid pro stejný klub v jedné sezóně. |
| **D40** | **Pravidlo o nejistotě:** Pokud si Claude ani po Pavlově vysvětlení není jist *(klub, lokalita, prev, identita, suffix...)*, **automaticky vložit do TODO** s krátkým popisem co je nejasné. Nikdy nehádat = riziko zanesení chyby do dat. Lepší 50 položek v TODO které Pavel později vyřeší, než 5 chybných údajů v CLUBS. |
| **D42** | **Slovenské ekvivalenty českých prefixů** *(SVK kluby)*: **ČH = Červená Hviezda** *(slovenský ekvivalent Rudé Hvězdy / RH)*, **TJ = Telovýchovná jednota** *(stejné jako CZ)*, **Sokol = Sokol** *(stejné)*, **Dom armády = Dům armády / DA** *(slovenský zápis, vojenský klub)*. Slovenské zkratky/názvy se ponechávají autenticky *(neprepisují se na české)*. |
| **D41** | **NIKDY nepřesouvat kluby mezi sheets!** Sheet (kraj) = autentický záznam almanachu = svatý. Geografické nesoulady jsou legitimní: (a) hranice krajů byly v 50. letech jiné než dnes, (b) v hokeji bylo časté, že klub hrál v geograficky jiném kraji s ohledem na lepší dopravní dostupnost. Pokud klub leží v jiném kraji než je sheet, **city zůstává správné** *(město, kde klub sídlí)* a sheet zůstává **původní** *(kde klub administrativně hrál)*. Příklad: Spartak Šluknov v 30_Liberecký sheet, city = „Šluknov" (Šluknov leží v Ústeckém kraji, ale klub hrál v Libereckém — autentický záznam 54/55). **DŮLEŽITÝ DŮSLEDEK PRO CITY (Pavlovo upresneni 04/2026):** Sheet **vylučuje** určitá města jako city. Pokud sheet=30_Brněnský / 40_Brněnský → city **NIKDY** Praha, Bratislava, Ostrava (jiné kraje). Pokud kolega zapsal city z jiného kraje, je to **CHYBA** — sheet je autoritativní. Při nejasnosti, zda je město X čtvrť Brna nebo Prahy, sheet rozhoduje *(„Vinohrady" v sheet=30_Brněnský = Brno-Vinohrady, ne Praha-Vinohrady; „Kovosmalt" v 30_Brněnský = brněnský Kovosmalt, ne bratislavský)*. |
| **D42** | **Registr identit hlavních klubů (Wiki D18)** *(Pavlovo upresneni 04/2026 - Brno)*. Některé hlavní kluby mají dlouhé genealogie přejmenování. Když Claude potká **jakoukoli variantu** názvu spojenou s hlavním klubem, ví že **jde o tentýž klub** napříč sezónami a v change_note musí cite Wiki D18. **REGISTR PRO BRNO:** **(a) Královo Pole = HC Brno** (1910-1993): SK Královo Pole → Sokol KP → ZSJ GZ Královo Pole → DSO/TJ Spartak KP → KPS Brno → Ingstav Brno → Lokomotiva Ingstav → HC Brno/Boby. Patterns v almanachu: „Královo Pole", „GZ Královo Pole", „Spartak Královo Pole", „KPS Brno", „Ingstav". **(b) Zbrojovka Brno-Židenice** (1910-1964, zaniklý): SK Židenice → fúze 1948 s SK Horácká Slavia Třebíč → Sokol Zbrojovka Brno-Židenice → ZJS/ZJŠ Zbrojovka Spartak Brno (ZJS=ZJŠ=Závody Jana Švermy). Patterns: „Zbrojovka Brno", „Sokol Zbrojovka", „ZJS Zbrojovka", „ZJŠ", „Spartak Brno ZJŠ". **(c) Rudá hvězda Brno** (1953-dnes): TJ RH Brno → TJ ZKL → TJ Zetor → HC Zetor → HC Královopolská → HC Kometa. Patterns: „Rudá hvězda Brno", „RH Brno". **REGISTR PRO PRAHU** (Pavlovo upresneni 04/2026): **(d) Sparta Praha = HC Sparta Praha** (1903-dnes): AC Sparta → Sokol Sparta Bubeneč → ZSJ Bratrství Sparta → ZSJ Sparta ČKD-Sokolovo → TJ Spartak Praha Sokolovo (1952-65) → TJ Sparta ČKD → HC Sparta Praha. Patterns: „Sparta Praha", „Bratrství Sparta", „Sparta ČKD", „Spartak Sokolovo", „Spartak Praha Sokolovo". **(e) Slavia Praha = HC Slavia Praha** (1900-dnes): SK Slavia → Sokol Slavia → ZSJ Dynamo Slavia → DSO/TJ Dynamo Praha (1953-65) → fúze 1964 s Tatra Smíchov → TJ Slavia Praha → TJ Slavia IPS → HC Slavia Praha. Patterns: „Slavia Praha", „Dynamo Slavia Praha", „Dynamo Praha". **POZOR:** „Dynamo Praha 7 Doprava" je JINÝ klub (závodní klub Dopravního podniku, nesmí se míchat se Slavií!). **(f) LTC Praha → Tatra Smíchov** (1904-1964, zaniklý fúzí se Slavií): LTC Praha → ZSJ Zdar LTC → ZSJ OD Praha → fúze 1951 s SK Smíchov → Tatra Smíchov → fúze 1964 s Dynamem (Slavia) ⇒ ZÁNIK. Patterns: „LTC Praha", „Zdar LTC", „OD Praha", „Tatra Smíchov". **(g) I. ČLTK Praha → Spartak Motorlet** (1923-dnes): I. ČLTK → Sokol ZMP → ZSJ ZMP → ZSJ Sokol Šverma Jinonice → DSO/TJ Spartak Motorlet → TJ ČLTK Motorlet → TJ DP I. ČLTK → I. ČLTK Praha. Patterns: „ZMP Praha", „Šverma Jinonice", „Spartak Motorlet", „ČLTK". **POZOR:** Pro budoucí sezóny (57/58+) tato pravidla aplikovat AUTOMATICKY (city = Praha/Brno, prev z předchozí sezóny, change_note s Wiki D42 odkazem). Tento registr lze rozšiřovat o další hlavní kluby (Plzeň, Ostrava, Kladno) kdy budou Wiki rešerše dostupné. |
| **D43** | **Formáty disambig pro city** *(Pavlovo upresneni 04/2026)*. Pro přehlednost a odlišení obcí stejného jména se používají 3 formáty disambig (volba dle kontextu): **(a) „Obec (okres)"** - okresní disambig pro malé obce s mnoha homonymy *(Brumovice (Břeclav) vs Brumovice (Opava), Bílovice (Brno) vs Bílovice nad Svitavou, Rudka (Brno))*. **(b) „Obec u Města"** - prepoziční disambig kde jde o známou tvar lokality *(Rosice u Brna, Sedlec u Benešova, Jindřichov u Šumperka, Příbram na Moravě, Bílovice nad Svitavou)*. **(c) „Brno-X" / „Ostrava-X" / „Bohumín-X"** *(D37 obdoba)* - pro části/čtvrti města *(Brno-Šlapanice, Brno-Bosonohy, Ostrava-Vítkovice)*. Volba mezi (a)/(b)/(c) podle: pokud je obec **dnes součást většího města** → (c); pokud je **samostatná, ale je jich víc** → (a) okresní disambig; pokud má **tradiční prepoziční tvar** → (b). |


---

## 17. Vědomostní báze měst — Sokol-jednoty I/II/III/…

Postupně budovaná báze měst, kde existovalo víc samostatných Sokol-jednot. Při auditu suffixovaných klubů („Sokol [město] II/III/…") nejdřív konzultovat tuto tabulku.

| Město | Jednoty | Hokej hrály |
|---|---|---|
| **Plzeň** | I, II, III, IV, V | min. **V** *(2021 1949/50, 50/51)* |
| **Pardubice** | I, II, III | **I** *(20_oblastni)*, **III** *(Studánka, ve čtvrti Studánka — krajský přebor)* |
| **Praha** | mnoho (jednoty po čtvrtích) | různé — **Smíchov II**, Praha III, ZMP II, atd. *(I-jednota Smíchov hokej neprovozovala)* |
| **Smíchov (Praha)** | I, II | **II** *(I hokej neprovozovala — potvrzeno)* |
| **Turnov** | I, II | **II** *(samostatná jednota)* |
| **Jaroměř** | I, II | **I** *(přejmenování ze „Stadion Jaroměř")*, **II** *(samostatná)* |

**Pravidla:**
- Pokud město v tabulce: `clean_name` Sokol [město] II = samostatná jednota; ponechat v původní formě.
- Pokud město NENÍ v tabulce: postupovat case-by-case s Pavlem; nově potvrzená města přidat zde.

---

## 18. B-tým konvence (D21 podrobně)

**Pravidlo:** B-tým má stejný kořen jako A-tým + suffix B. Pokud se A a B v almanachu liší formou jména (kratší vs. delší, s/bez „Sokol" prefixu), použít **ten složitější** pro oba.

**Příklady (50/51 audit):**

| B-tým (50/51 cid) | Před auditem | A-tým | Po auditu |
|---|---|---|---|
| 0213 | Sokol Bratrství Sparta II | ZSJ Sparta ČKD-Sokolovo Praha (0025) | **ZSJ Sparta ČKD-Sokolovo Praha B** |
| 0227 | Sokol Instalační závody II | ZSJ Instalační závody Praha (0035) | **ZSJ Instalační závody Praha B** |
| 0345 | Sokol Meopta Košíře II | Meopta Košíře (0126) | **Meopta Košíře B** *(A bez Sokol → B taky bez)* |
| 0518 | Sokol Spojocel Chomutov II | ZSJ Spojené ocelárny Chomutov (0017) | **ZSJ Spojené ocelárny Chomutov B** |
| 0647 | Perla Česká Třebová B | Sokol Perla Česká Třebová (0639) | **Sokol Perla Česká Třebová B** |

**Rozhodovací strom:**
1. Najít A-tým ve stejné sezóně (vyšší level, podobný kořen).
2. Pokud existuje → B-tým přejmenovat dle A-tým + B (použít delší/složitější verzi z obou).
3. Pokud A-tým neexistuje, ale jméno má suffix II/III: → pravděpodobně samostatná Sokol-jednota *(nebo TBD)*.
4. T-řádky v sezónním listu vždy aktualizovat spolu s `clean_name` v CLUBS.

**Důležité:** B-tým si **ZACHOVÁVÁ vlastní `club_id`** (pravidlo D20) — nepřepojuje se na A-tým. Vztah B↔A je dokumentován pouze v `change_note` a NOTES.

---

*Aktualizováno: duben 2026 (v3.1). Podrobnosti viz `HOKEJ_ALMANACH_TECHNICKY_REPORT.md`.*
