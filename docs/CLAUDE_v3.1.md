# CLAUDE.md — Hokejový almanach DB
### Onboarding pro agenta · Duben 2026 · Verze 3.4

> **Pracovní jazyk:** česky (odpovědi, komentáře k datům). 
> **Kód / identifikátory:** anglicky (sloupce, klíče, Python).

> **Update v3.3 (04/2026):** Přidána pravidla D37–D44 (D42=registr identit, D43=disambig formáty, D44=identita klubu) z práce na 53/54 a 54/55. Audit duplicit napříč 6 sezónami (29 sloučení). Dokončen audit sezón 53/54 (98%) a 54/55 (97%).

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
 S1949_50_FINAL.xlsx ← 1949/50
 S1950_51_FINAL.xlsx
 …
 S2020_21_FINAL.xlsx ← 2020/21
OSAlmanach.py ← editor (může být ve stejném adresáři jako xlsx)
HOKEJ_ALMANACH_TECHNICKY_REPORT.md ← podrobná tech. zpráva
CLAUDE.md ← tento soubor
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
Regionální SVK (30ZASL, 30STSL, 30VYSL) ← jen do 92/93
────────────────────────────────────────
NOTES → SYSTEM → SERIES → CLUBS → META
```

---

## 6. Identifikátory

```
NODE_S{RRRR}_{RR}_{NNNN} ← soutěžní uzel (4 číslice)
CLUB_S{RRRR}_{RR}_{NNNN} ← klub v sezóně (4 číslice)
TR_S{RRRR}_{RR}_{NNNNN} ← T-řádek (5 číslic)
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
clubs_lv = clubs_lv_map[club_id] # z CLUBS aktuální sezóny

if next_lv is None: fate = "zanik"
elif next_lv < clubs_lv: fate = "postup"
elif next_lv > clubs_lv: fate = "sestup"
else: fate = "setrval"

# Výjimka baráž (clubs_lv=L15 = barážní blok):
if clubs_lv == 15 and next_lv == 20:
 fate = "setrval" # klub se vrátil do 1. ligy, žádný pohyb
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
6. ovat `club_id` bez potvrzení
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
| **D42** | **Registr identit hlavních klubů (Wiki D18)** *(Pavlovo upresneni 04/2026 - Brno)*. Některé hlavní kluby mají dlouhé genealogie přejmenování. Když Claude potká **jakoukoli variantu** názvu spojenou s hlavním klubem, ví že **jde o tentýž klub** napříč sezónami a v change_note musí cite Wiki D18. **REGISTR PRO BRNO:** **(a) Královo Pole = HC Brno** (1910-1993): SK Královo Pole → Sokol KP → ZSJ GZ Královo Pole → DSO/TJ Spartak KP → KPS Brno → Ingstav Brno → Lokomotiva Ingstav → HC Brno/Boby. Patterns v almanachu: „Královo Pole", „GZ Královo Pole", „Spartak Královo Pole", „KPS Brno", „Ingstav". **(b) Zbrojovka Brno-Židenice** (1910-1964, zaniklý): SK Židenice → fúze 1948 s SK Horácká Slavia Třebíč → Sokol Zbrojovka Brno-Židenice → ZJS/ZJŠ Zbrojovka Spartak Brno (ZJS=ZJŠ=Závody Jana Švermy). Patterns: „Zbrojovka Brno", „Sokol Zbrojovka", „ZJS Zbrojovka", „ZJŠ", „Spartak Brno ZJŠ". **(c) Rudá hvězda Brno** (1953-dnes): TJ RH Brno → TJ ZKL → TJ Zetor → HC Zetor → HC Královopolská → HC Kometa. Patterns: „Rudá hvězda Brno", „RH Brno". **REGISTR PRO PRAHU** (Pavlovo upresneni 04/2026): **(d) Sparta Praha = HC Sparta Praha** (1903-dnes): AC Sparta → Sokol Sparta Bubeneč → ZSJ Bratrství Sparta → ZSJ Sparta ČKD-Sokolovo → TJ Spartak Praha Sokolovo (1952-65) → TJ Sparta ČKD → HC Sparta Praha. Patterns: „Sparta Praha", „Bratrství Sparta", „Sparta ČKD", „Spartak Sokolovo", „Spartak Praha Sokolovo". **(e) Slavia Praha = HC Slavia Praha** (1900-dnes): SK Slavia → Sokol Slavia → ZSJ Dynamo Slavia → DSO/TJ Dynamo Praha (1953-65) → fúze 1964 s Tatra Smíchov → TJ Slavia Praha → TJ Slavia IPS → HC Slavia Praha. Patterns: „Slavia Praha", „Dynamo Slavia Praha", „Dynamo Praha". **POZOR:** „Dynamo Praha 7 Doprava" je JINÝ klub (závodní klub Dopravního podniku, nesmí se míchat se Slavií!). **(f) LTC Praha → Tatra Smíchov** (1904-1964, zaniklý fúzí se Slavií): LTC Praha → ZSJ Zdar LTC → ZSJ OD Praha → fúze 1951 s SK Smíchov → Tatra Smíchov → fúze 1964 s Dynamem (Slavia) ⇒ ZÁNIK. Patterns: „LTC Praha", „Zdar LTC", „OD Praha", „Tatra Smíchov". **(g) I. ČLTK Praha → Spartak Motorlet** (1923-dnes): I. ČLTK → Sokol ZMP → ZSJ ZMP → ZSJ Sokol Šverma Jinonice → DSO/TJ Spartak Motorlet → TJ ČLTK Motorlet → TJ DP I. ČLTK → I. ČLTK Praha. Patterns: „ZMP Praha", „Šverma Jinonice", „Spartak Motorlet", „ČLTK". **REGISTR PRO LIBEREC** (Pavlovo upresneni 04/2026): **(h) Liberec = Bili Tygri Liberec** (1934-dnes, OPRAVA z 04/2026 - puvodne 1956 chybne!): Rapid Horni Ruzodol (1934, KOREN klubu) -> Sokol/Jiskra Kolora Liberec (1950-1955) -> Lokomotiva Liberec (12/1955, slouceni Jiskra Kolora + Slovan KNV + Slovan Severoceske tiskarny) -> TJ Stadion Liberec (6/1961) -> HC Stadion PS Liberec (1974/76) -> HC Stadion Liberec -> Bili Tygri Liberec (21.8.2000). Patterns: Sokol Rapid Liberec, Kolora Liberec, Sokol/Jiskra Kolora Liberec, Lokomotiva Liberec, Stadion Liberec, Bili Tygri Liberec. POZOR pro Liberec: linie Slavia/Tatran/Slavoj Liberec (1945-1957) je SAMOSTATNY chain (zanikl 1957 sloucenim do Lokomotivy). **REGISTR PRO PARDUBICE** (Pavlovo upresneni 04/2026): **(i) Pardubice = HC Dynamo Pardubice** (1923-dnes): LTC Pardubice (1923) -> fuze 1949 s Rapid Pardubice => Sokol Pardubice I (slouceni 9 klubu: AFK, Kampa Klub, Rapid, LTC, SK, ČVK atd.) -> Slavia/Slávie Pardubice (1950) -> ZTJ Dynamo Pardubice ROH (1952) -> DTO Dynamo Pardubice (1957) -> Tesla Pardubice (1960) -> HC Pardubice (1991) -> HC Pojišťovna IB / IPB / ČSOB / Moeller / Eaton / ... -> HC Dynamo Pardubice (2015-dnes). Patterns: Sokol Pardubice I, Slavia Pardubice, Slávie Pardubice, Dynamo Pardubice, Tesla Pardubice, HC Pardubice. POZOR pro Pardubice: klub vznikl 1923 jako LTC Pardubice. Tesla Pardubice = NE jiný klub Tesla, ale tentyz Dynamo prejmenovany. AFK Pardubice (49/50) přešlo do TJ Tesla = stejny chain. **(j) AFK Svítkov / Jiskra Ramo Pardubice** (1932-?, samostatny klub od Dynama): SK Svítkov (1910, zanikl 1921) -> AFK Svítkov (1921, hokej od 1932/33) -> SAFK Svítkov (1944/45) -> AFK Svítkov (1945/46) -> Sokol Svítkov (1948-50) -> ZSJ Ramo Pardubice (1950, přesun do Pardubic - Svítkov už součást Pardubic) -> Ramo Pardubice (1951-53) -> Jiskra Ramo Pardubice (1953/54+, oficiální název). Svítkov = obec u Pardubic, dnes městská část. RAMO = patrně závod (k vyjasneni). POZN: i když almanach v některých sezónách píše jen "Ramo Pardubice", identita = "Jiskra Ramo" (od 1953/54 prefix Jiskra je oficiální). NE Dynamo chain. Patterns: AFK Svítkov, Sokol Svítkov, ZSJ Ramo, Ramo Pardubice, Jiskra Ramo Pardubice. **(k) VCHZ Pardubice = Východočeské chemické závody** (1925-?, Pavlovo upresneni 04/2026): Genealogie z fotbalu (sedi i pro hokej): SK Explosia Semtín (1925) -> DSO Synthesia Semtín Pardubice (1948) -> TJ Chemik Semtín Pardubice (1950) -> TJ Jiskra Semtín Pardubice (1953) -> TJ VCHZ Pardubice (1958, slouceni s Jiskra Rybitví). VCHZ = Východočeské chemické závody, továrna v Semtíně/Rybitví (dnes Synthesia Semtín). Pred 1958 dva proudy: linie Semtín (Jiskra Semtín 1953-58) a linie Rybitví (Sokol Rybitví 1948-53 -> Jiskra Rybitví 1953-58), sloučeny 1958 do VCHZ. Závodní klub - NE Dynamo Pardubice chain. Patterns: SK Explosia, Synthesia Semtín, Chemik Semtín, Jiskra Semtín, Sokol Rybitví, Jiskra Rybitví, TJ VCH Pardubice, VCHZ Pardubice. **(l) RH Pardubice = Rudá hvězda Pardubice**: klub MV/silových složek. NEZAMĚŇOVAT s SNB Pardubice (50/51 0666 - jiný klub). NE Dynamo chain. Patterns: RH Pardubice, Rudá hvězda Pardubice. **Plus VSJ Pardubice** (49/50 0023) = Vojenská sokolská jednota = vojensky klub, NE Dynamo chain. **Plus Studánka Pardubice** = klub ze čtvrti Studánka. 

**REGISTR PRO HRADEC KRÁLOVÉ** (Pavlovo upresneni 04/2026): **(n) Spartak Hradec Králové = HC Stadion HK / Mountfield HK** (1949-dnes): ZSJ Škoda Hradec Králové (1949, pobocka Skodovych zavodu Plzeň v HK) -> ZSJ RD Hradec Kralové (1950, RD = Rozvodne podniky) -> Spartak ZVÚ Hradec Králové (1952, ZVÚ = Závody vítězného února (po únoru 1948)) -> Spartak Hradec Králové (1953-) -> ... -> HC Stadion HK / Mountfield HK. Patterns: ZSJ Škoda Hradec Králové, ZSJ RD HK, ZSJ RDP Svobodné Dvory, Spartak ZVÚ HK, Spartak Hradec Králové. Cástri HK (od 1942/49): Kukleny, Plácky, Svobodné Dvory, Třebeš, Nový Hradec - dnes čtvrti HK. KLÍČOVÉ: od 1952 nadvláda Spartak HK nad hokejem v HK (predtim roztrišteny). 
POZOR pro HK: 
- Spartak Hradec u Opavy = JINÝ klub (Hradec u Opavy = obec ve Slezsku, sheet Ostravský)
- Brano Hradec Podolí = JINÝ klub (Slezsko)
- Jindřichův Hradec = JINÉ město (Jihočeský sheet) - BVK Vajgar/Slovan JH = jiný chain
- ZSJ Škoda Hradec Králové = pobocka Skodovych zavodu Plzeň, ALE samostatný hradecky klub (D44 - identita = lokalita), NE plzensky chain
Plus rozne mestske casti HK (Třebeš, Plácky, Svobodné Dvory, Nový Hradec, Kukleny) mely vlastni mensí kluby v 50. letech - po sjednoceni Sokol/DSO/TJ casti splynuly do hlavniho Spartak HK chain. 

**HK VEDLEJSI CHAINS** (Pavlovo upresneni 04/2026 - po sjednoceni 1948 casti Třebeš/Plácky/Svobodné Dvory/Nový Hradec NESPLYNULY uplne do Spartak HK, ale ponechaly si vlastni TJ identitu - jsou to **samostatne kluby**): 
**(o) SK Petrof / Sokol Nový Hradec Králové** (1933-): SK Petrof Nový HK (klavírka v HK) -> Sokol Nový HK (1948-) -> Tatran Nový Hradec (1956-57) -> Sokol Nový Hradec (1957-60, sestup posledni vyskyt). Nový Hradec = dnes čtvrť HK od 1942. 
**(p) SK Meteor / Slavoj Svobodné Dvory** (1934-1968+): SK Meteor (1934-48) -> Sokol Meteor -> ZSJ RDP Svobodné Dvory (1949, RDP = Rolnicky druzstevni podnik) -> RD/RDP Svobodné Dvory -> Slavoj Svobodné Dvory (1958-69, stabilni). 
**(q) Sparta Třebeš / Sokol Sparta HK** (1939-1955): Sparta HK (Třebeš, 1939) -> SK Sparta HK -> Sokol Sparta HK -> Sokol Třebeš -> 1955-56 zanik. NE soucasti Spartak HK chain! 
**(r) DTJ Plácky / Polaban / Dynamo Plácky** (1940-1962): DTJ Plácky -> Polaban Plácky -> Polaban HK -> Dynamo Plácky (1955-62 mladez). 3 ruzne entity, navazuji. 
**(s) Sokol VČE / ZSJ ERZ / Slavia HK** (1940-1950): SK Slavia HK (1940-45) -> BK Hockey Slavia HK (1945-46, slouceni s BK) -> Sokol VČE HK (1948-49, VČE = Východočeské elektrárny) -> ZSJ ERZ HK (1949-50, ERZ = Elektrarensky zavod) -> po 1949-50 mizí. 
**(t) Bruslařský klub Hradec Králové (BK)** (1925-1945): BK HK -> BK hockey HK -> BK Hockey Slavia HK (1945-46 slouceni se Slavií = konec BK, prechod hracu do Slavie HK). Do almanachu 49/50+ pravdepodobne nezanechalo stopy. 
Vsechny vedlejsi chains: city = Hradec Králové, NE Spartak HK chain. 

**REGISTR PRO JIHLAVU** (Pavlovo upresneni 04/2026): **(u) Dukla Jihlava = HC Dukla Jihlava** (1956-dnes): Dukla Olomouc (1956, ASD = Armádní sportovní družstvo) -> presun do Jihlavy 1956/57 -> Dukla Jihlava (1957) -> HC Dukla Jihlava (1994) -> fuze s SK Jihlava (2000) -> HC Dukla Jihlava. Vojenský armádní klub. 
**(v) SK Jihlava / Modeta Jihlava** (1929-2000, civilni klub, NEJSTARSI v Jihlavě): SK Jihlava (1929) -> Sokol Modeta (1948) -> ZSJ Modeta (1949) -> DSO Jiskra Modeta (1953) -> TJ Tatran Jihlava (1956) -> TJ Dynamo Jihlava (1958) -> TJ Modeta (1973) -> SK Jihlava (1990) -> fuze s Duklou (2000) -> zánik. Modeta = oděvnický závod v Jihlavě. Patterns: SK Jihlava, Modeta Jihlava, Jiskra Modeta Jihlava, Tatran Jihlava, Dynamo Jihlava. 
**(w) Spartak Jihlava** (treti klub, bez další dokumentace): samostatný chain, NE napojen na SK Jihlava ani Dukla. Patterns: Spartak Jihlava, Motorpal Jihlava (Motorpal = závod, vyroba dieselovych komponentu). 
Vsechny tri chains: city = Jihlava. 

**REGISTR PRO LIBEREC - ROZSIRENO** (Pavlovo upresneni 04/2026 - 6 chains): **(x) VTJ Dukla Liberec** (1959-1978): hraci-vojaci od 1959, oficialne 20.12.1960, pozdeji becko Dukly Jihlava. Konec 7/1978 presun do Pisku. Vojensky klub. 
**(y) Slavia / Tatran / Slavoj Liberec** (1945-1957, zanikla): SK Slavia (1945) -> Sokol Zdar Slavia (1949) -> Sokol OD/ČSSZ (1950-51) -> Tatran (1953, slouceni ČSSZ + Piana Ruprechtice + Libena) -> Slavoj (12/1955) -> 1957 sloucena do Lokomotivy = chain konci. Plus Slavia VŠS Liberec (akademicky tym, k overeni). 
**(z) Sokol SNB / Rudá hvězda Liberec** (1945-): AFK Stráž bezpečnosti (1945) -> Sokol SNB (1948) -> Sokol Rudá hvězda / RH Liberec (po 1952). Bezpecnostni slozky, NEZAMĚŇOVAT s VTJ Dukla Liberec (armadni). 
**(aa) SK Doubí / Sokol Doubí / Nisan Doubí** (1937-): mestska cast Liberec-Doubí. 
**(bb) SK Železničáři / ZSJ ČSAD Liberec** (1947-): SK Železničáři Liberec (1947/48) -> Sokol Železničáři -> ZSJ SAD/ČSAD Liberec (1949). 
POZOR pro Liberec: PDA Liberec (52/53-55/56) je predchudce VTJ Dukla (vojenska policie). Vsechny chains: city = Liberec. 

**REGISTR PRO KLADNO** (Pavlovo upresneni 04/2026): **(cc) Kladno = Rytíři Kladno** (1924-dnes): HOSK Kladno (1924, Hokejovy odbor SK Kladno) -> TJ Sokol Kladno (1948) -> TJ Sokol SONP Kladno (1949, SONP = Spojené ocelárny narodni podnik) -> DSO Baník Kladno SONP (1953) -> TJ SONP Kladno (1958) -> TJ Poldi SONP Kladno (1977) -> TJ Poldi Kladno (1989) -> HC Kladno / Poldi / Velvana / Vagnerplast / Rabat / GEUS OKNA -> Rytíři Kladno (2011-dnes). Patterns: Sokol SONP Kladno, ZSJ SONP Kladno, SONP Kladno, Baník Kladno, Baník SONP Kladno, Poldi Kladno. 
**(dd) Kablo Kladno** (1949-): Závodní klub Kabelovny Kladno (Kablo = Kabelovna n.p.). Pattern: Kablo Kladno, Spartak KABLO Kladno. 
**(ee) Lokomotiva Kladno** (1955-): Klub železničářů. 
**(ff) VSJ Kladno** (49/50): Vojenská sokolská jednota (jako VSJ Pardubice/Liberec). 
Vsechny Kladno chains: city = Kladno. POZN: dalsi mensi kluby v Kladne (Pošta atd.) se budou resit ad hoc. 

**HIERARCHIE ZDROJŮ pro D42** (Pavlovo upresneni 04/2026): 
**1. PRIORITA: Hokejová Wiki** (HC Energie KV, HC Dukla Jihlava, HC Oceláři Třinec, HC Dynamo Pardubice, ROBE Vsetín atd.) - autoritativni primarni zdroj pro hokejovou genealogii. 
**2. PRIORITA: Pavlova sdělení** - upresnujici a opravujici informace od Pavla. 
**3. odznaky.wz.cz/katalog/** = pouze **pre-vypomoc** (orientacni pomucka pro objeveni dalsich klubu nebo prvni podled na genealogii pred Wiki/Pavlem). NIKDY NE jako autoritativni zdroj o hokeji - je to fotbalova stranka, prechody se v hokeji a fotbale často LIŠÍ. 
Format URL: http://odznaky.wz.cz/katalog/[pismeno]/[mesto].htm. **Použití**: pre-vypomoc pred Wiki rešerší, ne za ní. Konecna identita = Wiki + Pavel. 

**OBECNÉ ZKRATKY PODNIKŮ** (Pavlovo upresneni 04/2026): 
- **ČSSZ** = Československé stavební závody (sídlilo ve více městech, zkratka pro vícero klubů zaroven - např. Pisek, Liberec) 
- **AZNP** = Automobilové závody narodni podnik (Skoda Mlada Boleslav) 
- **MEZ** = Moravské elektrotechnické závody (Vsetin, predecessor Zbrojovky) 
- **VTŽ** = Válcovny trub a železárny (Chomutov) 
- **VTGK** = Válcovny trub Gustava Klimenta (Chomutov, predchudce VTŽ) 
- **ZGK** = Závody Gustava Klimenta (Třebíč-Borovina) - PODNIKOVE ZKRATKY po G.Klimentovi se vyskytuji napric republikou (VTGK Chomutov, ZGK Třebíč atd., POTVRZENO Pavlem) 
- **SUKNO** = textilni podnik v Humpolci (Humpolec proslulý vyrobou suken/laken) 
- **Agrostroj** = zemedelske stroje (Pelhřimov) 
- **ŽĎAS / ZĎASS** = Žďárské strojírny a slévárny (Žďár nad Sázavou) 
- **Motorpal** = vstrikovaci systemy (Telč) 
- **Fezko** = autopotahy/textil (Strakonice) 
- **ČZ** = Česke závody motocyklove (Strakonice, motocykly CZ) 
- **Tokos** = paralelni podnik Žďár nad Sázavou 
- **TŽ** = Třinecké železárny (Trinec) 
- **SONP** = Spojené ocelárny narodni podnik (Kladno, Poldi) 
- **CHZ** = Chemické závody Československo-Sovětského přátelství (Litvinov) 
- **ZJF** = Závody Julia Fučíka (Chomutov) 
- **VŘSR** = Velke rijnove socialisticke revoluce (Trinec) 
- **Kosmos** = podnik (Čáslav, POTVRZENO Pavlem - patronat 49/50-52/53) 
- **ZSJ** = Závodní sokolská jednota (po 1948-49) 
- **DSO** = Dobrovolná sportovní organizace (od 1953) 
- **TJ** = Tělovýchovná jednota (od pozdejsich let) 
- **LVA** = Lékařská vojenská akademie (POTVRZENO Pavlem - mela hokejovy klub v HK 49/50) 

**REGISTR PRO KARLOVY VARY** (Pavlovo upresneni 04/2026): **(gg) Karlovy Vary = HC Energie Karlovy Vary** (1932-dnes): SK Slavia Karlovy Vary (1932) -> RKV Sokol Slavia (1951) -> RKV Dynamo (1953) -> DSO Dynamo (1956) -> TJ Slavia (1965) -> TJ Slavia PS (1974) -> HC Slavia / Becherovka -> HC Energie Karlovy Vary (2002-dnes). Patterns: Slavia KV, Dynamo KV. 
**(hh) VSJ / Krušnohor / PDA / DA / VTJ Karlovy Vary** (1949-): vojenský klub - rozšířená genealogie z odznaky.wz.cz: VSJ KV (49/50) -> Krušnohor Karlovy Vary (*1951) -> PDA Karlovy Vary (1953) -> Dům armády KV (1954-56) -> Dukla Karlovy Vary (1965, přechod RH Ostrov) -> VTJ Karlovy Vary (1976+). V hokeji 49/50-55/56 v almanachu, po 1956 mizi (presun nebo prejmenovani na Dukla). Patterns: VSJ KV, Krušnohor KV, PDA KV, DA / Dum armády KV, Dukla KV, VTJ KV. 
**(ii) RH Karlovy Vary** (1951-1956+): Rudá hvězda - bezpecnostni slozky. 
**(jj) Lokomotiva Karlovy Vary** (1953-1958+): zeleznicari. 
Vsechny KV chains: city = Karlovy Vary. 

**REGISTR PRO MLADA BOLESLAV** (Pavlovo upresneni 04/2026): **(kk) Mladá Boleslav = BK Mladá Boleslav** (1924+ predvalecny klub, dnes opet BK): BK Mladá Boleslav (predvalecne) -> AZNP MB (1949, AZNP = Automobilove zavody n.p. = Skoda automobilka) -> ZSJ AZNP MB (1950) -> Spartak Mladá Boleslav AZNP / Spartak AZNP MB (1953+) -> ... -> TJ Škoda Mladá Boleslav -> BK Mladá Boleslav (dnes). Patterns: AZNP Mladá Boleslav, Spartak Mladá Boleslav, Spartak AZNP MB. city Mladá Boleslav. POZOR: 'Škoda Mladá Boleslav' = AUTOMOBILKA (Skoda AUTO, AZNP), naprosto JINÁ firma od Škodových závodů Plzeň (těžké strojírenství)! 
**(ll) Stará Boleslav** (1949-): JINÉ MĚSTO od Mladá Boleslav! Stará Boleslav = dnes součást Brandýs nad Labem-Stará Boleslav (Praha-vychod). Genealogie: Sokol Stará Boleslav (1948-) -> SK Stará Boleslav (1952) -> Slavoj Stará Boleslav (1953+). Samostatný klub - NE Mlada Boleslav chain. city Stará Boleslav. 

**REGISTR PRO VSETÍN** (Pavlovo upresneni 04/2026): **(mm) Vsetín = VHK ROBE Vsetín** (1904-dnes): SK Vsetín (1904) -> BK Vsetín (1906) -> Sokol Vsetín (1933) -> Dynamo Vsetín (1949) -> Zbrojovka MEZ Vsetín (1951, MEZ = Moravské elektrotechnické závody) -> Spartak Vsetín / Spartak Zbrojovka Vsetín (1953-67) -> TJ Zbrojovka Vsetín (1968) -> HC Dadák / Petra / Slovnaft / HC Vsetín -> VHK Vsetín (2008) -> VHK ROBE Vsetín (2016-dnes). Patterns: Dynamo Vsetín, Zbrojovka MEZ Vsetín, Zbrojovka Vsetín, Spartak Vsetín, Spartak Zbrojovka Vsetín, Spartak Z Vsetín. MEZ = Moravske elektrotechnicke zavody (predecessor Zbrojovky Vsetin). 
**(nn) RH Vsetín** (1955-): Rudá hvězda - bezpečnostní složky. 
**(oo) Sokol Ústí u Vsetína** (53/54): SAMOSTATNÁ OBEC u Vsetína (district Vsetín), NE Vsetín chain. city Ústí u Vsetína. 
**(pp) PZ 19 Vsetín** (56/57): Pohraniční stráž 19 - vojenský klub. 
Vsechny chains krome (oo): city = Vsetín. 

**REGISTR PRO TŘINEC** (Pavlovo upresneni 04/2026): **(qq) Třinec = HC Oceláři Třinec** (1929-dnes): SK Třinec (1929) -> KS Zaolzie (1938-39, polske obdobi po Mnichove, Zaolzie = uzemi za Olzou) -> SK Železárny Třinec (1939) -> TJ TŽ VŘSR Třinec (1950, VŘSR = Velké říjnové socialistické revoluce, TŽ = Třinecké železárny) -> TJ TŽ Třinec (1988) -> HC Železárny Třinec (1994) -> HC Oceláři Třinec (1999-dnes). Patterns: Železárny Molotova Třinec, Sokol Železárny VMM Třinec, Baník Třinec, TŽ Třinec. POZN: Almanach v 50/51-52/53 uvadi 'Molotov/VMM' misto 'VŘSR' (Wiki) - varianta nazvu. 
**(rr) Baník Třinec-Konská** (53/54+): Konská = mestska cast Třince (D37 obdoba). 
**(ss) OUPZ Třinec III** (55/56): OUPZ = vojensky/zavodni klub, k overeni. 
Vsechny Třinec chains: city = Třinec. 

**REGISTR PRO CHOMUTOV** (Pavlovo upresneni 04/2026, hokej.cz history): **(tt) Chomutov = Piráti Chomutov** (1945-dnes): ČSK Chomutov (1945) -> ZJS Spojené ocelárny / Spojocel (1949-51) -> Sokol Hutě (1951-53, postup do 1.ligy) -> TJ Baník Chomutov ZJF (1953-58, ZJF = Závody Julia Fučíka) -> Baník VTŽ Chomutov (1958-60) -> VTŽ Chomutov (1960-91, VTŽ = Válcovny trub a železárny) -> KLH VT VTJ (1991-96) -> KLH Chomutov (1996-2011) -> Piráti Chomutov (2011-dnes). Patterns: ČSK Chomutov, Spojocel Chomutov, ZJS Spojené ocelárny, Sokol Hutě Chomutov, Baník Chomutov ZJF, Baník Chomutov, VTŽ Chomutov, KLH Chomutov, Piráti. POZN: 24.11.1956 leteckâ havárie u Eglisau (Švýcarsko) - 3 hráči TJ Baník Chomutov ZJF zahynuli. 
**(uu) ČSD Chomutov** (49/50-): klub železničářů. 
**(vv) Baník Chomutov VTGK** (53/54-55/56): VTGK = **Válcovny trub Gustava Klimenta** (POTVRZENO Pavlem 04/2026, název chomutovské továrny PŘED prejmenovanim na VTŽ - Válcovny trub a železárny cca 1958). VTGK chain je samostatny od hlavniho Piráti (stejna tovarna, ale ruzny zavodni klub). 
**(ww) VSJ Chomutov** (49/50): Vojenská sokolská jednota. 
**(xx) Sokolský kroužek Prům.školy** (52/53): školní kroužek. 
Vsechny Chomutov chains: city = Chomutov. POZOR: VTŽ Chomutov je Severočeský kraj, NE Třinec (Slezsko). VTŽ = Válcovny trub a železárny, NE Třinecké železárny. 

**REGISTR PRO LITVÍNOV** (Pavlovo upresneni 04/2026, hokej.cz history): **(yy) Litvínov = HC VERVA Litvínov** (1945-dnes): SK Stalinovy závody Horní Litvínov (8.11.1945) -> Sokol Stalinovy závody (1949) -> Jiskra Stalinovy závody / Jiskra SZ Litvínov (1953-54) -> TJ CHZ Litvínov (1962, CHZ = Chemické závody Československo-Sovětského přátelství) -> HC CHZ (1990) -> HC Chemopetrol (1991-2007) -> HC Litvínov (2007) -> HC Benzina (2009) -> HC VERVA Litvínov (2011-dnes). Patterns: Stalinovy závody Litvínov, Jiskra SZ Litvínov, Jiskra Litvínov, CHZ Litvínov, Chemopetrol Litvínov, Verva Litvínov. SZ = Stalinovy závody. POZN: 1958/59 postup do 1.ligy (1.misto v 2.lize). 
**(zz) Korda Litvínov** (1945-1955, starsi paralelni oddil): Korda Litvínov -> ZSJ Korda (1950) -> Jiskra Korda Litvínov (1954-55). 1955/56 splynul s hlavnim Jiskra Litvínov chain. Korda = PODNIK (potvrzeno Pavlem 04/2026, jako Škoda/Zbrojovka - patron klubu). 
Vsechny Litvínov chains: city = Litvínov. 

**REGISTR PRO ÚSTÍ NAD LABEM** (Pavlovo upresneni 04/2026, hokej.cz history): **Ústí nad Labem = HC Slovan Ústí nad Labem** (1946-dnes): Sokol Ústí nL (1946) -> LTC Ústí nL (1946-48) -> ZSJ Armaturka (1949-1959) -> TJ Chemička (1959-1963, prevzala) -> 1963 zanik TJ Chemička, NOVY klub TJ Slovan Ústí nL (1963, z TJ Slovan Narodni vybory) -> ... -> HC Slovan Ústí nL -> HC Slovan Ústečtí Lvi (2002-13) -> HC Slovan Ústí nL (2014-dnes). POZN: 1963 formálně zánik + nový subjekt, ale hokej.cz vede jako jeden chain. DSO reforma 1953: Armaturka -> Spartak (almanach autenticky D41 - Wiki neuvadi presny prubeh prejmenovani). Patterns: Arma Ústí nL, Armaturka Ústí nL, Slovan Ústí nL, Spartak Ústí nL, Chemička Ústí nL. 
**Plus drobnosti v Ústí**: Jiskra Chemička Ústí nL (53/54-58/59, paralelni chemicky podnik), RH Ústí nL (56/57+, bezpecnostni slozky), ZM Ústí nL (49/50-51/52, ZM = Železná mostárna? K upresneni). Plus 52/53 'Chemik' a 'Chemostav' Ústí nL = patrne varianty hlavniho chain (chemicky patronat pred TJ Chemička 1959). Plus 49/50 'Sokol Ústí na Labem' = patrne LTC ÚnL z 1946-48. 
**Predmestske obce Ústí nL** (samostatne v 50. letech, dnes mestske casti): 
- **Trmice** (50/51-): Sokol Trmice -> Dynamo Trmice -> Spartak Trmice. Plus Elektrárna Trmice (50/51). city = Trmice (autenticky stav 50. let, dnes by bylo Ústí nad Labem-Trmice). 
- **Neštěmice** (50/51-): Tonaso Neštěmice (Tovarna na sodu) -> Jiskra Neštěmice. city = Neštěmice (dnes mestska cast). 
**Joint zaznamy 49/50**: 'Sociakol Děčín – Arma Ústí n.L.' + 'Benzina Roudnice - Sociakol Děčín/Arma Ústí n.L.' = turnajove/kvalifikacni zaznamy mezi vice mesty. 
Vsechny Ústí chains: city = Ústí nad Labem. POZOR: 'Velká Buková' (49/50-50/51, sheet Praha) je JINÉ MĚSTO (Velká Buková = obec u Rakovníka), NE Ústí! Sezimovo Ústí (49/50+, Jihočeský) je tez JINÉ MĚSTO (u Tabora). 

**REGISTR PRO PÍSEK** (Pavlovo upresneni 04/2026, hokej.cz history): **Písek = IHC Králové Písek** (1927-dnes): prvni hokej v Pisku 1927 -> ČASK Písek (1942, slouceni SK + ČAFK + TC Orinoko, mistr jihoceske zupy) -> ZSJ ČSSZ Písek (1949-, ČSSZ = Československé stavební závody (POTVRZENO Pavlem 04/2026, sídlilo ve více městech - zkratka pro vícero klubů)) -> Spartak Písek (1953/54, DSO reforma) -> TJ Spartak Písek -> JITEX Písek (60. leta?, textilni podnik) -> 1990 fuze s VTJ Písek = VTJ JITEX Písek -> HC JITEX -> IHC Písek -> IHC Králové Písek (2020-dnes). Patterns: ZSJ ČSSZ Písek, Spartak Písek, TJ Spartak Písek. 
**Plus Dukla Písek** (57/58-): vojensky klub, dle hokej.cz pozdeji 'Dukla Jihlava B' a nakonec VTJ Písek. 1990 fuze s JITEX = IHC. 
**Plus drobnosti** v Pisku: 52/53 Poz.stavby Písek (Pozemni stavby), 59/60 Sokol Písek B. 
Vsechny Pisek chains: city = Písek. POZOR: 'Moravský Písek' (53/54-59/60, Gottwaldovský) = JINÉ MĚSTO (obec u Strážnice na jižní Moravě, okres Hodonín), NE Písek! Slavoj Moravský Písek je samostatny klub - city Moravský Písek. 

**REGISTR PRO TÁBOR** (Pavlovo upresneni 04/2026, hokej.cz history): **Tábor = HC Tábor** (1921-dnes): DSK Tábor (1921, Dělnický sportovní klub) -> ČSSZ Tábor (1949) -> ZSJ ČSSZ Tábor -> DSO Tatran Tábor (1953/54, almanach D41 - Wiki uvadi 1956) -> TJ Tatran -> TJ Vodní stavby Tábor (1960) -> 1993 fuze s VTJ Tábor = HC VS VTJ Tábor -> HC Tábor (1994-dnes). Patterns: ČSSZ Tábor, Tatran Tábor, Vodní stavby Tábor. 
**Vojensky chain Tábor** (1952-1958, pak prerusen, obnoven 1970 VTJ): PDA Tábor (1952-53) -> DA Otava (1954-56, Dum armady Otava - reka u Tabora) -> Dukla Tábor (DA Otava) (1956-57) -> Dukla Tábor (1957-58) -> konec po 57/58. POZN: VTJ Tábor obnoven 1970, 1987-89 byl ASD Dukla Jihlava B (presun z Pisku!), 1993 fuze s civilnim Vodni stavby = HC VS VTJ Tábor (Pavlovo: 'pak chvíli společná a pak vojáci konec'). 
**Plus drobnost**: Lokomotiva Tábor (54/55, zeleznicari). 
Vsechny Tabor chains: city = Tábor. 

**REGISTR PRO MILEVSKO + SOBĚSLAV + VIMPERK** (Pavlovo upresneni 04/2026, hokej.cz): 
**Milevsko = HC Milevsko 1934** (1934-dnes): SK Milevsko (1934) -> Sokol -> Sokol ČSSZ (1949) -> DSO Tatran (1953-56) -> Spartak Milevsko (1956+) -> TJ ZVVZ (1970, ZVVZ = Závody na výrobu vzduchotechnických zařízení) -> HC ZVVZ (1994) -> HC Milevsko 2010 -> HC Milevsko 1934 (2021-dnes). 
**Soběslav = OLH Spartak Soběslav** (1929-dnes): zalozeni 1929 -> Lada Soběslav -> ZSJ Lada -> DSO Spartak (1953/54) -> Spartak -> OLH Spartak Soběslav. Lada = lokalni patronat (k upresneni). 
**Vimperk = HC Vimperk** (1950-dnes): Slavoj OPK Vimperk (1950, zalozeni) -> TJ Jiskra Vimperk (1955) -> TJ Šumavan Vimperk (1962) -> HC Vimperk (1992-dnes). 
Vsechny 3 chains: city = Milevsko / Soběslav / Vimperk. 

**REGISTR PRO BENEŠOV + VLAŠIM + ČÁSLAV** (Pavlovo upresneni 04/2026, hokej.cz): 
**Benešov u Prahy = HC Lev Benešov** (1929-dnes, Stredocesky kraj, blizko Konopiste): zalozeni 1929 -> Sokol Benešov (49/50-) -> Slavoj Benešov (52/53+, DSO) -> Lokomotiva Benešov (59/60+) -> ... -> TJ ČSAD Benešov -> VHS HC Benešov (2007) -> 2007 fuze s SKLH = VHS HC Vodní Lvi -> HC Vodní Lvi Benešov -> HC Lev Benešov (dnes). 
**Vlašim = HC Rytíři Vlašim** (1953-dnes): Sokol Vlašim (49/50) -> Sokol Zbrojovka Vlašim (50/51, ZSJ podniku) -> 1953 zalozeni TJ Spartak Vlašim (Wiki - almanach D41 zachycuje Spartak uz 52/53) -> ... -> HC Rytíři Vlašim (2013-dnes). 
**Čáslav = HC Čáslav** (1929/2016): Kosmos Čáslav (49/50-, podnik) -> Slavoj Čáslav (53/54+, DSO) -> ... -> 2004 zanik -> 2016 obnova HC Čáslav (po otevreni zimniho stadionu). Pred 2016 jen okresni souteze na prirodnim lede. Plus vojensky/letecky chain: PDA -> DA -> Dukla Čáslav + Letci Čáslav (Caslav vojenske letiste). 
**POZOR DISAMBIG MUSI BÝT JEDNOZNACNE** (Pavlovo upresneni 04/2026): 
- **Benešov u Prahy** = nase hlavni Benesov (Stredocesky kraj, okres Benesov, blizko zamku Konopiste, dnes HC Lev Benesov). **'u Prahy' patri JEN do `city`, NE do `clean_name`** - klubove nazvy zustavaji autenticke z almanachu (Sokol Benešov, Slavoj Benešov, Lokomotiva Benešov atd. - bez 'u Prahy'). city = 'Benešov u Prahy'. 
- **Horní Benešov** + **Dolní Benešov** (Ostravsky/Moravskoslezsky) = JINÁ MĚSTA (Brano = Brany podnik HB, MSA = Moravskoslezska armaturka DB). Benar Benešov (52/53, Ústecký) = patrne Benešov nad Ploučnicí (Decinsky okres). Sokol Popovice u Benešova = vesnice u Stredoceskeho Benesova. 
Vsechny chains: city dle skutecne lokality. 

**REGISTR PRO TŘEBÍČ** (Pavlovo 04/2026, Wiki + hokej.cz + Pavlovo PDF dusledne): 
**Třebíč mela az do 1.1.1956 PARALELNI 3 hlavni kluby**: 
**Chain A = DSK** (1926-): DSK Třebíč (25.12.1926, 1937/38 v 1.lize 'moravsky Davos') -> JTO Sokol DSK (1948) -> ZSJ MEZ Třebíč (1950, MEZ pobočka) -> MEZ -> Spartak Třebíč (1953/54, DSO) -> 1.1.1956 SLOUČENÍ s Horáckou Slavií = DSO Spartak -> TJ Spartak (1956+) -> 57/58 postup do 2.ligy -> 58/59-59/60 ve 2.lize. 
**Chain B = ZGK Borovina** (Borovina je ctvrt Třebíče): Borovina Třebíč (49/50) -> ZSJ ZGK Třebíč-Borovina (50/51, ZGK = Závody Gustava Klimenta) -> Sokol KZ Borovina -> Jiskra Borovina ZGK -> Jiskra Borovina (53/54-55/56) -> Jiskra Třebíč (56/57+ mestsky). NEZAHRNUTA do slouceni 1.1.1956. 
**Chain C = Horácká Slavia** (1928-): Horácká Slavia Třebíč (19.2.1928 na Radostine) -> 1939-42 a 1946-48 v 1.lize -> 1948 prechod kadru do Brno Zbrojovka -> roztristenost -> Sokol II -> INVAZ -> GZ (Gottwaldovy závody) -> Tatran Třebíč (1953/54) -> 1.1.1956 SLOUČENÍ s DSK = Spartak Třebíč. 
**Pavlovo:** DSK + Horácká Slavia DUSLEDNE - dva paralelni hlavni kluby do 1.1.1956. ZGK/Klimentovy zavody jsou treti chain (ctvrt Borovina). Plus Stareč (vesnice u Třebíče). 
Vsechny Trebic chains: city = Třebíč. 

**REGISTR PRO PELHŘIMOV + HUMPOLEC + PACOV** (Pavlovo 04/2026, Wiki + hokej.cz): 
**Pelhřimov = HC Lední Medvědi Pelhřimov** (1932-dnes): 22.11.1932 zalozeni HC Pelhřimov (H.C.P.) na schuzi v hotelu Slavie - studentska SOKH na Narodnim kluzisti. Genealogie: HC Pelhřimov -> Sokol Pelhřimov (1949) -> Agrostroj Pelhřimov (1952, podnik) -> Spartak Pelhřimov (1953/54, DSO) -> TJ Spartak (1962, znovuzalozeno) -> HC Spartak -> HC Lední Medvědi (2013-dnes). 58/59 postup do L30 oblastni. 
**Humpolec = TJ Jiskra Humpolec** (1949-dnes): Sokol Humpolec (1949) -> Sokol Sukno Humpolec (1952, podnik SUKNO - textilni v Humpolci, mesto proslulé vyrobou suken) -> Jiskra Humpolec (1953/54, DSO) -> TJ Jiskra Humpolec (dnes). 
**Pacov = SK Pacov** (1950-): Pacov -> Slavoj Pacov (1951 DSO) -> Sokol Pacov -> Slavoj. Drobny vesnicky/mestsky klub. 
Vsechny chains: city = Pelhřimov / Humpolec / Pacov (NE 'Sukno Humpolec' nebo 'Agrostroj Pelhřimov' - to jsou podniky, ne mesta - kolega kolisal, sjednoceno). 

**REGISTR PRO VYSOČINU + STRAKONICE** (Pavlovo 04/2026, Wiki + hokej.cz): 
**Moravské Budějovice** = HC Žihadla MB (formálně 2005-): AFK MB -> Baník MB (52/53). V 50. letech jen okresni uroven, ZS az 2005. 
**Žďár nad Sázavou** = SKLH Žďár: Sokol -> ZĎASS/ŽĎAS (52/53+) -> Tokos -> Tatran -> Spartak (1956+). NE Žďár nad Orlicí (Královéhradecký - JINÉ MĚSTO). 
**Velké Meziříčí** = HHK VM: Sokol -> Spartak (56/57+). NE České ani Valašské Meziříčí. 
**Telč** = SK Telč: Sokol -> Motorpal (52/53, vstrikovaci systemy) -> Spartak (53/54+). 
**Polná, Třešť, Kamenice nad Lipou**: drobne okresni kluby. 
**Strakonice** = Spartak ČZ Strakonice (Jihocesky): Strakonice -> Fezko (autopotahy) -> ČZ (motocykly) -> DSO Spartak/Jiskra (53/54+) -> Spartak ČZ (57/58+). 
**POZOR DISAMBIG**: Žďár nad Orlicí, České Meziříčí (Královéhradecký) + Valašské Meziříčí (Zlinsky) jsou JINÁ MĚSTA. 
Vsechny chains: city dle skutecne lokality.

**REGISTR PRO PROSTĚJOV** (Pavlovo upresneni 04/2026, Wiki screenshot): **Prostějov = LHK Jestřábi Prostějov / IHC Prostějov** (1913-dnes): 1913 SK Prostějov -> 1945 ČSSZ Prostějov (ČSSZ = Československé stavební závody, POTVRZENO) -> 1953 DSO Tatran Prostějov -> Slovan Prostějov (1956) -> 1959 TJ Železárny Prostějov -> 1969 TJ Prostějov -> HKC -> BSH -> 1989 IHC Prostějov -> LHK Jestřábi Prostějov (dnes). Patterns: ZSJ ČSSZ, ČSSZ, Tatran Prostějov, Slovan Prostějov, Železárny Prostějov, IHC. **KLICOVE Pavlovo upresneni:** Klub NIKDY NEZANIKL (', hokej se porad hral'). 61/62 sestup z 2.ligy - kolega zapsal jen 'Prostějov' bez prefixu (patri do hlavni Železárny chain). Plus paralelni Agrostroj Prostějov chain (1950+, podnik zemedelskych stroju, jako Agrostroj Pelhřimov - stejny podnik). Vsechny Prostejov chains: city Prostějov.

**REGISTR PRO PŘEROV** (Pavlovo upresneni 04/2026, Wiki screenshot): **Přerov = HC Zubr Přerov** (1928-dnes): 1928 SK Přerov -> Sokol Přerov / Slavia Přerov (1948-52) -> 1953 TJ Spartak Meopta Přerov (Meopta = opticky podnik) -> 1975 TJ Meochema Přerov -> 1995 HC Přerov -> 2000 HC Minor 2000 -> 2006 HC Zubr Přerov (dnes). Patterns: Sokol Přerov, ZSJ Slavia Přerov, Sokol Slavia, Meopta Přerov, Spartak Meopta, TJ Meopta. 
**Přerovské strojírny** (paralelni podnikovy chain 52/53+): Přerovské strojírny (strojirensky podnik) -> Spartak Přerovské strojírny (1953+). NE hlavni Meopta chain. 
**Dukla Přerov** (vojaci 1959+): VTJ Dukla. 
**Sokol Přerov nad Labem** = DISAMBIG, JINE MESTO (Polabí, okres Nymburk, Stredocesky kraj). NE Severomoravsky Meopta chain! 
Hlavni + strojirny + Dukla: city Přerov. Sokol Přerov nad Labem: city Přerov nad Labem.

**REGISTR PRO DĚČÍN** (Pavlovo upresneni 04/2026, Wiki): **HC Děčín** (1945-dnes): HO SK Podmokly-Děčín (1945, zalozeni) -> Sociakol Děčín (1948-50) -> Kovostroj Děčín (1950+, podnik kovoobrabeci stroje) -> Spartak Děčín (1953+ DSO) -> Banik Děčín (1955+) -> ... -> HC Děčín (1999-dnes). lize. Patterns: Sociakol Děčín, Kovostroj Děčín, Spartak Děčín, Banik Děčín. POZN: 49/50 jointni zaznamy 'Sociakol Děčín – Arma Ústí nL Labem' a 'Benzina Roudnice - Sociakol Děčín/Arma Ústí nad Labem' = sdileny tym tří mest. Železničáři Děčín 49/50 -> ČSD Dynamo Děčín 50/51 (samostatna železničářská linie). Vsechny Děčín chains: city Děčín.

**REGISTR PRO TEPLICE** (Pavlovo upresneni 04/2026, Wiki + FK Teplice paralel): **HC Stadion Teplice** (1945-2007) -> **HC Teplice Huskies** (2019-dnes). DUE ERA mesta - mezi 2007-2019 hokej zanikl (neprovozuschopny ZS, zbytky Bilina 2010). Genealogie podle paralelni FK Teplice: 1945 zalozeni -> 1948 Sokol -> 1949 Technomat (podnik OD) -> 1951 Vodotechna -> 1952 Ingstav -> 1953 Tatran (DSO) -> 1960 Slovan -> 1966 Sklo Union -> ... -> 2007 zanik -> 2019 Huskies (novy ZS). Patterns: Technomat, Vodotechna, Tatran Teplice, Slovan Teplice. Mestske casti: Retenice (od 1963), Trnovany, Sobedruhy. Sklarny Retenice = sklarna 1890. **POZOR**: 'Slavoj Teplice nL Metuji' (59/60-61/62) = JINE MESTO Královéhradecky kraj (okres Náchod, Adrspasske skaly), city Teplice nad Metují. Vsechny Teplice chains (Severocesko): city Teplice.

**REGISTR PRO CHEB** (Pavlovo upresneni 04/2026, Wiki + retromuseum.cz): **MULTI-CHAIN MESTO** - v 50.letech 4-5 paralelnich klubu, dnesni HC Stadion Cheb (1978-dnes) je NOVY KLUB (bez primeho nasledníka 50.let). **RH Cheb** (1951-1996): klub 5. brigady Pohranicni straze (DSO Ministerstva vnitra). VSJ Sokolovo (1951) -> RH (1952+) -> VTJ Dukla Hranicar (1966-72, MO) -> RH zpet -> 1990 SK policie Union -> FC Union -> 1996 zanik. **TJ Lokomotiva Cheb** (oficialne 1960): zeleznicarsky, hokej od 50.let (1957 prirodni led v Gottwaldovych sadech, dnes Hradcany). **Spartak Cheb / Eska**: stadion Esky -> 1952 Spartak Eska Cheb -> 1963 soucast RH. **DA Hvezda Cheb + Slavoj Cheb**: drobne. Patterns: RH Cheb, Spartak Cheb, Lokomotiva Cheb, DA Hvezda Cheb, Slavoj Cheb. **POZOR**: Tatran Luby u Chebu = JINE MESTO (Luby = drive Schönbach, slavne housle). Vsechny Cheb chains: city Cheb.

**REGISTR PRO ŽATEC** (Pavlovo upresneni 04/2026, Wiki + FK Slavoj Žatec): **MENSI HOKEJOVY KLUB** - Žatec je predevsim chmelarske mesto (Žatecký chmel = EU chranene oznaceni puvodu). Hokej hraje jen 49/50-55/56, pak chybi. Genealogie: Sokol Žatec (1949) -> Sokol Chmel Lučan Žatec (1950, Patterns: Sokol Žatec, Sokol Chmel Lučan, MKP Žatec, Slavoj Žatec, Banik Žatec. POZN: VTJ Žatec (vojensky) pozdeji 1991 fuze s FK Teplice. Dnes Žatec nema samostatny hokej (fanouši jezdi do Loun/Mostu). city Žatec. 

**REGISTR PRO JINDŘICHŮV HRADEC** (Pavlovo upresneni 04/2026, hokej.cz history): **Jindřichův Hradec = HC Vajgar / TJ Slovan / HC Střelci** (1929-dnes): 
1928 bandy hokej na rybniku Vajgar -> 1929 zalozeni VBK Vajgar JH (Veslařsko-bruslařský klub) -> po valce nucene slouceni s mistnim Slovanem -> Jitolen JH (52/53) -> DSO Slovan JH (1953/54) -> TJ Slovan JH (1950-2006, dlouhe obdobi pod Slovanem) -> 1989/90 osamostatneni HC Vajgar JH -> 2014 HC Střelci JH (mladez) -> 2017-2020 KLH Vajgar -> 2020 zanik Vajgar, vse pod HC Střelci. Pavlovo: 'Slovan a pak Vajgar' POTVRZENO - almanach 50. let zachycuje Slovan, Vajgar nazev se vrátil 1989/90. 
**Plus drobnosti**: Nežárka JH (53/54, ricka Nežárka u JH), Jiskra JH (55/56-, paralelni). 
**POZOR DISAMBIG**: Hradec u Opavy / Hradec Podolí (sheet Ostravsky/Slezsky) = JINÉ MĚSTO (Slezsko, okres Opava, dnes Hradec nad Moravicí), Brano = Brany podnik. BVK 49/50 v almanachu = typo kolegy (spravne VBK). 

**REGISTR PRO HAVLÍČKŮV BROD** (Pavlovo upresneni 04/2026, hokej.cz, bkhb.cz): 
**KLÍČOVÉ: mesto Havlíčkův Brod do 1945 = Německý Brod** (prejmenovani 1945 po Karlu Havlíčkovi Borovskem). 
**Havlíčkův Brod = BK Havlíčkův Brod** (1928-dnes): BK Německý Brod (1928) -> 1932 mistr Vychodoceske zupy -> 1945 prejmenovani na BK Havlíčkův Brod ('N' -> 'H' na hrudi) -> 1947/48 jedina sezona v 1. lize CSR (zazitek se LTC Praha, SK Bratislava) -> Sokol PZ Havlíčkův Brod (PZ = Pletařské závody, POTVRZENO bkhb.cz) -> 1953/54 prejmenovani na Jiskra Havlíčkův Brod (zalozeni 2. ligy) -> ... -> LHK Jiskra HB -> BK Havlíčkův Brod (2015-dnes). Patterns: BK HB, Pletařské závody HB, Jiskra HB. city Havlíčkův Brod. 
**Plus drobnosti**: SK Železničáři HB (49/50, zeleznicari), Vojensky chain (PDA 53/54 -> Dukla 57/58, pak konec), Slovan HB (58/59-, B-tym hlavniho Jiskra). 
**HBH Holešák Havlíčkův Brod** = JINY KLUB (1984-1998, samostatny): TJ JZD Okrouhlička (1984, vesnice 12km od HB) -> 1992 vstup podnikatel Jiří Holešák -> HBH Holešák HB (1992-98) -> 1998 zanik (presun do Chotebore). Pavlovo 'cca 1990' = priblizne, skutecne 1992. 
Vsechny HB chains: city = Havlíčkův Brod. 

**REGISTR PRO BENEŠOV + VLAŠIM + ČÁSLAV** (Pavlovo upresneni 04/2026, hokej.cz): 
**Benešov = HC Lev Benešov** (1929-dnes): Sokol Benešov + VSJ -> Slavoj Benešov (1952/53, DSO) -> Lokomotiva Benešov (59/60+) -> ... -> TJ ČSAD Benešov (Tělovýchovná jednota Československé státní automobilové dopravy) -> VHS HC -> 2007 fuze se SKLH Benešov = VHS HC Vodní Lvi -> 2009 HC Vodní Lvi -> HC Lev Benešov. 
**Vlašim = HC Rytíři Vlašim** (1949-dnes, Wiki uvadi 1953): Sokol Vlašim (49/50) -> Sokol Zbrojovka Vlašim (50/51, podnikovy patronat - Zbrojovka Vlasim = vojenska tovarna) -> Spartak Vlašim (1953, DSO reforma - Wiki uvadi jako zalozeni) -> ... -> HC Vlašim -> HC Rytíři Vlašim (2013-dnes). POZN: klub existoval pred 1953 Wiki zalozenim - almanach kolegy autenticky D41. 
**Čáslav = Slavoj Čáslav** (civilni, do 2004): Kosmos Čáslav (49/50-52/53, podnik POTVRZENO Pavlem) -> Slavoj Čáslav (1953/54, DSO) -> ... -> 2004 zanik. HC Čáslav = nove zalozeny klub az 2016 po otevreni zimniho stadionu (Wiki). Plus VOJENSKY chain Čáslav: PDA Čáslav (54/55) -> DA (55/56) -> Letci Čáslav (56/57, letecka specifikace - Caslav ma vojenske letiste) -> Dukla Čáslav (57/58). 
**Disambig**: Horní Benešov + Dolní Benešov (Ostravsky sheet) = JINÉ MĚSTO! (obce ve Slezsku, Brano Horní Benešov = strojirensky podnik). Benar Benešov (52/53 Ústecký) = patrne Benešov nad Ploučnicí (Děčín okres) - JINÉ město. Vsechny chains: city = Benešov / Vlašim / Čáslav / Horní Benešov / Benešov nad Ploučnicí. 

**REGISTR PRO MOST** (Pavlovo upresneni 04/2026, hokej.cz history): **(aab) Most = HC Most / Baník Most** (1946-2017, zanikla v Most): HO Uhlomost (1946, Hokejovy oddil Uhlomost = uhlí + Most) -> Sokol Uhlomost (1948) -> Uhlomost (1952) -> TJ Baník Most (1953+, SHD = Severočeské hnědouhelné doly, po 1980 oficialne Banik SHD Most) -> ... -> HC Most (1991-2017). POZN: 2017 sestup z 1.ligy + presun do Slaneho -> v Most vznikl novy klub Mostečtí lvi (sezona 2017/18+, NE pokracovani HC Most). Patterns: Uhlomost, Sokol Uhlomost, Baník Most, Baník SHD Most. 
POZOR: 'Sokol Neuměřice – Kamenný Most' (49/50) je JINÉ MÍSTO (Neuměřice = obec u Slaneho ve Středocesku, Kamenný Most = mestska cast Neuměřic), NE mestsky klub Most v Most! city Neuměřice. POZOR: 'VTŽ Chomutov' (58/59-59/60) = JINÝ klub v Chomutově (Severočeský), NE Třinec! VTŽ Chomutov = Válcovny trub a železárny (POTVRZENO Wiki/hokej.cz - Pavlovo upresneni 04/2026, NE Třinecké železárny ani Vítkovické). Chomutov je Severočeský kraj. 

**REGISTR PRO PLZEŇ** (Pavlovo upresneni 04/2026): **(m) Plzeň = HC Škoda Plzeň** (1929-dnes): Hokejový odbor SK Viktoria Plzeň (1929) -> Sokol Plzeň IV (1948) -> ZSJ Škodovy závody (1949) -> ZSJ Leninovy závody / ZVIL (1952) -> Spartak Plzeň LZ / Spartak ZVIL (1953) -> TJ Škoda Plzeň (1965) -> HC Škoda Plzeň (1991) -> HC Interconnex / ZKZ / Keramika / Lasselsberger / HC Plzeň 1929 / HC Škoda Plzeň (2012-dnes). Patterns: Škoda Viktoria Plzeň, Sokol Plzeň IV, ZSJ Škoda Plzeň, Spartak Plzeň, Spartak LZ Plzeň, Spartak ZVIL Plzeň, Škoda Plzeň. ZVIL = Závody V.I. Lenina = Leninovy závody (zkratka). 

**KLÍČOVÉ PRAVIDLO PRO ŠKODA - 2 RŮZNÉ FIRMY** (Pavlovo upresneni 04/2026): Název „Škoda" v sportovních klubech je NEJEDNOZNAČNÝ - existují dve naprosto ruzne firemni Skody, plus vice pobocek prvni Skody:
- **(1) Škodovy závody (těžké strojírenství)** = výroba lokomotiv, naftových motorů, zbraní, energetického zařízení. Sídlo **Plzeň** (Leninovy závody 1952-, ZVIL = Závody V.I. Lenina). Pobočky: **Hradec Králové** (samostatný klub - např. ZSJ Škoda HK je vlastni hradecky chain), **Praha** (samostatná pobočka), plus **menší pobočky** v jiných městech. Každá pobočka = SAMOSTATNÝ KLUB s vlastní identitou.
- **(2) ŠKODA Mladá Boleslav (automobily)** = AZNP, dnes ŠKODA AUTO. NAPROSTO JINÁ firma od Škodových závodů - žádný vztah ke strojírnám v Plzni! Klub: TJ Škoda Mladá Boleslav → BK Mladá Boleslav.
**Důsledek pro audit:** Při potkávání „Škoda X" / „ZSJ Škoda Y" / „Spartak Škoda Z" - identita se URČUJE PODLE LOKALITY (D44), nikoli podle jména „Škoda". Sheet (D41) rozhoduje. „Škoda Plzeň" ≠ „Škoda Hradec Králové" ≠ „Škoda Mladá Boleslav" = TŘI různé kluby (různé firmy/pobočky, různá města). **POZOR:** Pro budoucí sezóny (57/58+) tato pravidla aplikovat AUTOMATICKY (city = Praha/Brno, prev z předchozí sezóny, change_note s Wiki D42 odkazem). Tento registr lze rozšiřovat o další hlavní kluby (Plzeň, Ostrava, Kladno) kdy budou Wiki rešerše dostupné. |
| **D43** | **Formáty disambig pro city** *(Pavlovo upresneni 04/2026)*. Pro přehlednost a odlišení obcí stejného jména se používají 3 formáty disambig (volba dle kontextu): **(a) „Obec (okres)"** - okresní disambig pro malé obce s mnoha homonymy *(Brumovice (Břeclav) vs Brumovice (Opava), Bílovice (Brno) vs Bílovice nad Svitavou, Rudka (Brno))*. **(b) „Obec u Města"** - prepoziční disambig kde jde o známou tvar lokality *(Rosice u Brna, Sedlec u Benešova, Jindřichov u Šumperka, Příbram na Moravě, Bílovice nad Svitavou)*. **(c) „Brno-X" / „Ostrava-X" / „Bohumín-X"** *(D37 obdoba)* - pro části/čtvrti města *(Brno-Šlapanice, Brno-Bosonohy, Ostrava-Vítkovice)*. Volba mezi (a)/(b)/(c) podle: pokud je obec **dnes součást většího města** → (c); pokud je **samostatná, ale je jich víc** → (a) okresní disambig; pokud má **tradiční prepoziční tvar** → (b). |
| **D44** | **Identita klubu = (město, jádro názvu)** *(klíčové Pavlovo pravidlo 04/2026)*. **Identita klubu je definována lokalitou a jádrem názvu, NIKOLI organizační formou (zkratkou).** Dobové prefixy jsou jen organizační zkratky odrážející tehdejší státní/sportovní reformy a NEJSOU součástí identity: **Sokol** *(po válce 1948 unifikace)*, **ZSJ** *(Závodní sokolská jednota, 1949-50)*, **DSO** *(Dobrovolná sportovní organizace, od 1953)*, **DŠO** *(slovenský ekvivalent)*, **DSJ**, **TJ** *(Tělovýchovná jednota, od 1957)*, **HC** *(Hockey Club, od 1990)*, **VTJ** *(Vojenská tělovýchovná jednota)*, **ASD** *(Armádní sportovní družstvo)*. **Jádro identity** = (a) **lokalita** *(město, čtvrť)* + (b) **jádro názvu** *(Sparta, Slavia, Spartak, Jiskra, Tatra, Dukla)* nebo (c) **podnik/závod** *(Škoda, Zbrojovka, ČKD, Motorlet, Tatra Smíchov, Mosilana)*. Rozhodovací postup: (1) Pokud klub má **stejnou lokalitu + stejné jádro/podnik** → **TENTÝŽ KLUB** napříč různými prefixy. (2) Pokud klub má **různou lokalitu nebo různé jádro/podnik** → **JINÝ KLUB**, ač má podobný prefix. **Příklady:** „ZSJ Bratrství Sparta Praha" = „Spartak Praha Sokolovo" = „TJ Sparta ČKD" = „HC Sparta Praha" *(stejná Sparta + Praha)*. „Spartak Tatra Smíchov" = „Tatra Smíchov" *(stejný podnik Tatra Smíchov + Praha)*. „Spartak Smíchov Škoda" ≠ Tatra Smíchov *(jiný podnik Škoda)*. „Tatra Smíchov" ≠ „Spartak Tatra Kolín" *(stejný podnik Tatra, ale jiná lokalita Smíchov vs Kolín)*. **Důsledek:** Při auditu identity NEPODLÉHAT zkratkám — DSO/ZSJ/TJ se vždy mění při reformách, ale klub zůstává. |

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

## D45 - 3 typy kontinuity klubu (Pavlovo upresneni 04/2026)

Pri formulovani genealogie klubu napric desetiletimi rozlisujeme 3 typy:

**TYP 1: Primá genealogická kontinuita** - klub funguje nepretrzite, jen meni jmena/podniky pres reformy (DSO 1953, krajska 1960). Priklad: HC Děčín (1945-dnes pod ruznymi jmeny), HC ZUBR Přerov (1928-dnes), HC Kometa Brno (1953-dnes), HC Sparta Praha (1903-dnes), HC Roudnice nad Labem (1931-dnes).

**TYP 2: Kontinuita mesta jako nositele hokejove tradice** - hokejova tradice mesta je nepreruena, ale klub se preformuluje (zanik a obnova pravniho subjektu). Dnesni klub je - navazuje na hokejovou identitu mesta, fanoušky, ZS, lokalitu. Pisem se 'NOSITEL HOKEJOVE TRADICE V MESTE' s vysvetlenim kontinuity. Priklady: HC Vlci Jablonec (1996, navazuje na 50.leta), HC Teplice Huskies (2019, po pauze 2007-2019), Mostečtí Lvi (2017, po odchodu HC Most), HC Berounšti Medvedi (1996, navazuje na Cesky lev/Lokomotiva 1933+), HC Stadion Litoměřice (2007, po Dukla 1991), HC Česká Lípa (1989, navazuje na 50.leta), HC Stadion Cheb (1978, navazuje na chebsky hokej 50.let).

**TYP 3: Diskontinuita / jine mesto** - skutecne nezavisle kluby. Priklad: Mostek (Královéhradecky) NENÍ Most (Severocesko); Frydlant (Liberecko) NENÍ Frydlant nL Ostravici (Severomoravsko/Frydek-Mistek); Teplice nL Metuji (Královéhradecky) NENÍ lazenske Teplice (Severocesko); Přerov nL Labem (Stredocesky) NENÍ moravsky Přerov.

**FORMULACE V NOTES:** 
- Typ 1: 'KONTINUITA klubu' 
- Typ 2: 'NOSITEL HOKEJOVE TRADICE V MESTE' s upresnenim 'formalne novy pravni subjekt YYYY, ale kontinuita s hokejovou tradici mesta...' 
- Typ 3: 'JINE MESTO! city XXXX. NE [hlavni mesto] chain.'
