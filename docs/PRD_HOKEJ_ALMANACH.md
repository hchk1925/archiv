# PRD — Hokejovy Almanach D42: Dotaceni dat k dokonalosti

**Verze:** 1.0
**Datum:** 17. kvetna 2026
**Zadavatel:** Mgr. Pavel Tureček (soudce, Pardubice)
**Vykonavatel:** Claude Code (agentic AI)
**Stav projektu:** 72/72 sezon zakladne zpracovano (95.0% D42)

---

## 1. EXECUTIVE SUMMARY

Cilem projektu je **dotahnout datovou integritu kompletni databaze cs./ces. ledniho hokeje 1949/50 - 2020/21** ze stavu 95.0% pokryti D42 na **100% verifikovanou kvalitu**.

Zakladni audit (1730+ cid disambiguovano) je hotovy. Zbyva:
1. Verifikace chain breaks
2. Validace systemu soutezi a postupu/sestupu
3. Zpracovani reorganizaci soutezi
4. Tracking zmen nazvu klubu
5. Dokonceni K UPRESNENI klubu

---

## 2. AKTUALNI STAV

### 2.1 Hotovo (zakladni audit 65+ session)

| Položka | Hodnota |
|---|---|
| Sezon zpracovano | 72 (1949/50 - 2020/21) |
| Klubu celkem (cid) | 34 698 |
| S D42 registr | 32 946 (95.0%) |
| Disambiguace mest | 125+ mest |
| Disambiguace cid | 1 730+ |
| Chain breaks | 59 (0.19%) |
| 1. liga / extraliga | BEZ PRERUSENI |

### 2.2 Hlavni soubory

- **/home/claude/almanach_full/** - originalni archiv (ZIP rozbaleno)
- **/home/claude/work/** - pracovni XLSX (72 sezon)
- **/home/claude/mesta/** - per-mesto MD soubory (11 mest)
- **/mnt/user-data/outputs/CLAUDE_v3.4.md** - ustava D01-D45 (verze 3.4)

---

## 3. DATOVA STRUKTURA

### 3.1 XLSX format per sezona

Kazda sezona ma soubor `S{YYYY}_{YY}_FINAL.xlsx` s temito listy:

**Soutezni listy** (10_, 20_, 30_, KVAL):
- 10_liga / 10_extraliga - nejvyssi soutez
- 20_1liga / 20_IIliga / 20_1NHL - druha nejvyssi
- 30_2liga / 30_2NHL / 30_IINHL - treti nejvyssi
- 30_{kraj} - krajske prebory (do 2004/05: PRAH/STRC/JHCK/ZAPC/SVRC/VYCH/JHMR/SVMR; od 2005/06: 14 krajů)
- KVAL - kvalifikace

**Datove listy:**
- **CLUBS** - hlavni tabulka klubu (jedna sezona)
- **SERIES** - hraci serie (jeden zapas = jeden radek)
- **SYSTEM** - system soutezi (postup/sestup)
- **META** - metadata sezony
- **NOTES** - poznamky

### 3.2 CLUBS list - sloupce

| Sloupec | Obsah |
|---|---|
| A (1) | club_id - unikatni ID klubu v sezone |
| B (2) | cn - club name (plny nazev) |
| C (3) | abbr - zkratka |
| D (4) | sheet - na kterych listech klub hraje |
| E (5) | wins/poradi |
| F (6) | losses |
| G (7) | district - okres (text) |
| H (8) | prev_club_id - ID klubu z predchozi sezony (DULEŽITE!) |
| I (9) | **notes** - D42 registr ustavy (zde se kontroluje 'registr ustavy 04/2026') |
| J (10) | **city** - mesto/obec |

### 3.3 Klicove pravidlo D42

V notes musi byt zaznam typu:
```
"{city} = {full_club_name} (Wiki D42 - registr ustavy 04/2026). {region}. {comment}. city {city}."
```

---

## 4. KRITICKE ZNALOSTI O DOMENE

### 4.1 Pavel je fanouskem HK Hradec Kralove

⚠️ **POZOR**: Pavel je rodakem Hradce Kralove, fanouskem **HK Mountfield HK** (drive Stadion HK, Lev HK, VČE HK). V Pardubicich pracuje jako soudce, ale **HC Dynamo Pardubice = REGIONALNI RIVAL**. Pavel zalozil tuto databazi proto, ze ma rad hokejove statistiky a hradeckou srdcovku.

### 4.2 Hradec Kralove chain - kompletni 72 sezon

| Obdobi | Klub | Soutez |
|---|---|---|
| 1949-1952 | RDP Svobodne Dvory / Sokol Trebes | oblastni |
| 1952-1972 | Spartak ZVU Hradec Kralove | 2. liga |
| 1973-1976 | TJ Spartak ZVU | 2. NHL |
| 1976/77 | TJ Spartak ZVU | 1. NHL |
| 1977-1992 | TJ Stadion Hradec Kralove | 1. NHL |
| 1992/93 | HC Stadion Hradec Kralove | 1. NHL |
| 1993/94 | HC Stadion HK | 1. liga |
| 1994/95-1995/96 | HC Lev Hradec Kralove | 1. liga |
| 1996/97-2001/02 | HC Lev / HC Hradec Kralove | 2. liga (propad) |
| 2002/03-2003/04 | HC VČE Hradec Kralove | 1. liga (navrat) |
| 2013/14+ | **Mountfield Hradec Kralove** | **EXTRALIGA** |

### 4.3 Hierarchie zdroju

V poradi priority:
1. **Pavlovo sdeleni** (priorita absolutni)
2. **Hokejova Wiki** (cs.wikipedia.org)
3. **Pavlovo PDF** (CZE1.ZIP, CZE2_3_nizsi.zip)
4. **Klubove weby** (hcsparta.cz, hcdynamo.cz, hcplzen.cz, mountfieldhk.cz, atd.)
5. **odznaky.wz.cz** - sponzori
6. **almanach_FINAL_1949-2021.zip** - Pavluv kompletni archiv

### 4.4 Klicove era-changes

| Datum | Udalost |
|---|---|
| 1949 | Zacatek mistrovstvi CSSR |
| 1962 | Reorganizace 2. ligy (Spartak Hradec sestoupil) |
| 1976/77 | Vznik 1. NHL a 2. NHL (mezi extraligou a 2. ligou) |
| **1.1.1993** | **Rozdeleni CSSR** - od 1993/94 Ceska liga sama |
| 1993-1995 | Privatizace - zanik mnoha tovarnich klubu (-27%) |
| 2000 | Reforma kraju (z 8 historickych na 14 současnych) |
| 2005/06 | Almanach prijal nove kraje |
| 2013/14 | Mountfield Hradec do extraligy |
| **2019/20** | **COVID-19 - predcasne ukoncena** |
| 2020/21 | Druha COVID sezona |

---

## 5. TASK BREAKDOWN - PRACE K DOTACENI

### TASK 1 — Validace chain breaks (priorita VYSOKA)

**Co:** Resolve 59 chain breaks (prev_club_id ukazuje na nezistujici cid)

**Detail:**
- Identifikovat vsech 59 cid s broken chains
- Pro kazdy: dohledat skutecne pokracovani / predchozi sezonu
- Aktualizovat prev_club_id nebo poznamenat skutecny zanik klubu

**Akceptacni kriteria:**
- 0 unexplained chain breaks
- Vsechny breaks dokumentovany v CHAIN_BREAKS.md

### TASK 2 — Dokonceni K UPRESNENI klubu

**Co:** Resolve 3 zbyle K UPRESNENI kluby

**Zbyle:**
- DA Stalinec (4x, 1954-56) - armadni Dukla-A v staline ere
- Dukla Stalinec (1x, 1956/57)
- Madlov (1x, jihomoravsko) - mesto neznámé

**Strategie:**
- Wiki search s anglickymi formulacemi
- Pavel se zeptat
- Konzultace s odznaky.wz.cz

### TASK 3 — System soutezi (priorita STREDNA)

**Co:** Pro kazdou sezonu validovat SYSTEM list

**Detail:**
- Popis: kolik tymu, kolik kol, kdo postupuje/sestupuje
- Reorganizace soutezi (1962, 1976, 1993, 2002, 2005)
- Hraci system (jednoduchy/dvojity round robin, playoff)

**Vystup:**
- Per-sezona SYSTEM.md s validovanymi pravidly
- Detekce anomalii (pocet tymu != ocekavane)

### TASK 4 — Postupy a sestupy (priorita VYSOKA)

**Co:** Validovat ze postupy/sestupy mezi sezonami sedi

**Pravidlo:**
Pokud klub X v sezone S byl posledni v 1. lize a klub Y byl prvni v 2. lize,
pak v sezone S+1 musi X byt v 2. lize a Y v 1. lize.

**Implementace:**
- Per-pair sezon kontrola
- Vyjimky: reorganizace (1962, 1976, 1993)
- Vyjimky: financni problemy (klub se rozpustí)

**Vystup:** PROMOTIONS_RELEGATIONS.md s vsemi prechody

### TASK 5 — Reorganizace soutezi (priorita VYSOKA)

**Co:** Detailne zdokumentovat reorganizace

**Klicove momenty:**

#### 1962/63 - Reorganizace 2. ligy
- Spartak Hradec sestoupil z 2. ligy do krajskeho prebreu
- Validovat pocty tymu pred/po

#### 1976/77 - Vznik 1. NHL a 2. NHL
- Mezi extraligou (10_liga) a 2. ligou (30_2liga) vznikly:
  - 1. NHL (20_1NHL)
  - 2. NHL (30_2NHL)
- Pyramida: extraliga > 1. NHL > 2. NHL > 2. liga > kraje

#### 1993/94 - Rozdeleni CSSR
- Slovenske kluby odesly do SVK federacni soutezi
- Z 501 klubu na 428 (-73)
- Validovat ktere SVK kluby kde pokracovaly

#### 2002/03 - Regionalni reforma
- 14 novych kraju misto 8 historickych
- Mapovani: ktery historicky kraj -> ktery novy?

#### 2019/20, 2020/21 - COVID-19
- Predcasne ukonceni 2019/20 (brezen 2020)
- 2020/21 omezeny rozsah
- Ne vsechny postupy/sestupy probehly normalne

**Vystup:** REORGANIZACE.md s timeline a detaily

### TASK 6 — Zmeny nazvu klubu (priorita STREDNA)

**Co:** Track zmen nazvu klubu napric sezonami

**Pravidlo:**
Pokud klub X (cn1) v sezone S a klub Y (cn2) v sezone S+1 maji stejny prev_club_id chain,
pak je to ZMĚNA NÁZVU, ne novy klub.

**Priklady:**
- HC Stadion HK -> HC Lev HK -> HC Hradec Kralove -> HC VČE HK -> Mountfield HK
- TJ Spartak ZVU -> TJ Stadion HK -> HC Stadion HK
- Aukro Berani Zlin <- Berani Zlin <- HC PSG Zlin <- HC Hamé Zlin <- HC Continental Zlin

**Vystup:** CLUB_NAME_CHANGES.md - chronologicky vsech klubu

### TASK 7 — Per-sezona validace + statistiky

**Co:** Pro kazdou sezonu validovat integritu

**Kontrolni body:**
- Pocet tymu v lize == META pocet
- Vsichni tymové z SERIES jsou v CLUBS
- Vsichni tymové v CLUBS jsou v SERIES (alespoň 1 zapas)
- city polo neni prazdne pokud cn obsahuje znamy mestsky pattern
- prev_club_id existuje v predchozi sezone (krom nove zalozenych klubu)
- Goal differential v SERIES = SERIES SUM

**Vystup:** Per-sezona VALIDATION.md report (anomalie)

### TASK 8 — Per-mesto MD pro vyznamna mesta (priorita NIZKA)

**Co:** Vytvorit per-mesto MD pro vsechna mesta s 10+ klubovymi vyskyty

**Existujici:**
- HRADEC, PRAHA, BRNO, OSTRAVA, PARDUBICE, PLZEŇ, TŘEBÍČ, KARLOVY_VARY, ČESKÉ_BUDĚJOVICE, SOKOLOV, HOLOUBKOV

**Pridat:**
- Liberec, Vsetin, Cheb, Olomouc, Zlin, Litvínov, Kladno, Kometa Brno
- Bratislava, Kosice (SVK metropole - do 1992/93)
- Dukla Jihlava, Trinec, Vitkovice (NHL kluby)

**Format:** Stejny jako stavajici HRADEC.md - kompletni chain klubu, mistrovstvi, soutezi.

---

## 6. KONVENCE A PRAVIDLA

### 6.1 Konvence souboru

- Vystup: `present_files` jednotlive (NE zip-folder pokud Pavel neoctel)
- Output dir: `/mnt/user-data/outputs/`
- Per-mesto MD: prefix `CLAUDE_MESTO_*`
- Validace MD: prefix `VALIDATION_*`
- Backups: `/home/claude/work/backup/` (pred velkymi zmenami)

### 6.2 Konvence kodu

- Pyzhon 3.11 + openpyxl
- Safe save: `tmp + os.replace()` (atomicky)
- Vzdy backup pred modifikaci
- Vzdy print prubeznou statistiku

### 6.3 Konvence textu

- Cestina UTF-8
- "registr ustavy 04/2026" jako D42 marker (presne tato fráze)
- City uvozeno "city {nazev}" na konci notes
- Po-revolucni nazvy: "Post-revolucni nazev" v notes

---

## 7. RIZIKA A POZNAMKY

### 7.1 Risk: Nejasne mesto u sponzorskeho nazvu

Priklad: "AZ Residomo Havířov" - jasne Havirov, ale "Aukro Berani Zlin" - jasne Zlin.
Ale: "Saxana Group" - kde to je?

**Reseni:** Hledat na hokejove Wiki, najmout fuzzy matching, konzultovat Pavla.

### 7.2 Risk: Zmena prev_club_id semantiky

V casovem obdobi 2013/14+ ma `prev_club_id` semantiku mesta, ne club_id.

**Reseni:** Auto-detect formatu sezony, adaptovat logiku.

### 7.3 Risk: Pavlovo srdcovka

Pavel je vyrazne propojen s Hradcem Kralove. **NIKDY** nemenit Hradec Kralove kluby bez Pavla.
**NIKDY** pripsat Pardubicim hokejovou srdcovku.

### 7.4 Risk: Pavlovo styl komunikace

Pavel pozaduje:
- **Strucne** vystupy (ne dlhe historicke vyklady)
- **Tabulky** (preferuje pred volnym textem)
- **NE klubove kulturni vyklady**
- **Jednotlive soubory** pres present_files (NE zip celku, krome explicitniho pozadavku)

---

## 8. ACCEPTANCE CRITERIA

Projekt je dokoncen, kdyz:

- [ ] Vsechny chain breaks (59) jsou vyresene nebo dokumentovane
- [ ] K UPRESNENI klubu (3) jsou vyresene
- [ ] SYSTEM list je verifikovan pro vsech 72 sezon
- [ ] POSTUPY/SESTUPY jsou auditovany (PROMOTIONS_RELEGATIONS.md)
- [ ] REORGANIZACE jsou zdokumentovany (REORGANIZACE.md)
- [ ] ZMENY NAZVU klubu chronologicke (CLUB_NAME_CHANGES.md)
- [ ] Per-sezona validace bez anomalii
- [ ] Per-mesto MD pro 20+ vyznamnych mest
- [ ] CLAUDE_v3.4.md aktualizovana s novou D45/D46+
- [ ] Final ZIP pro deployment

**Cilovy stav:** 100% D42 pokryti + verifikovany system soutezi + dokumentace na svetove urovni.

---

## 9. PRILOHY

### 9.1 Glossar

- **D42** = pravidlo z ustavy: "registr ustavy 04/2026" v notes
- **D45** = typ mesta (TYP 1 = vice klubu, TYP 2 = jeden klub, TYP 3 = JINÉ MĚSTO)
- **cid** = club_id, ID klubu v jedne sezone
- **prev_club_id** = ID stejneho klubu v predchozi sezone (chain pointer)
- **chain break** = prev_club_id ukazuje na nezistujici cid

### 9.2 Klicove zkratky podniku

- ZVU = Závody Vítězného Února (Hradec Kralove)
- ČKD = Českomoravská Kolben-Daněk
- ČSAD = Československá státní automobilová doprava
- VTJ = Vojenská tělovýchovná jednota
- JZD = Jednotné zemědělské družstvo
- ZD = Zemědělské družstvo
- ROH = Revoluční odborové hnutí
- DSO = Dobrovolná sportovní organizace
- NHL = Národní hokejová liga (NE americka NHL!)

### 9.3 Kontakty / odkazy

- Pavlov GitHub: (neudáno)
- Hokejova Wiki: https://cs.wikipedia.org/wiki/Kategorie:Lední_hokej
- Pavlovo email: (neudáno)

---

**Koniec dokumentu PRD v1.0**
