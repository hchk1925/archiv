# Almanach v2 — souhrn změn

**Provedeno:** 26. dubna 2026 · plošně přes 72 sezón

---

## Co bylo zapsáno do souborů (skutečné změny)

### 1. Nový list `PYRAMIDA` ve všech 72 sezónách

Zařazen hned za `SYSTEM`. Schéma:

| level | tier_name | competitions | sheets | node_count | note |
|---|---|---|---|---|---|
| L10 | Nejvyšší soutěž (1. úroveň) | I. liga | 10_liga | 2 | (volné) |
| L15 | Kvalifikace / baráž o L10 | … | KVAL | 1 | |
| L20 | 2. úroveň | 1.ČNHL | 20_INHL | 1 | |
| … | … | … | … | … | … |

`competitions` = unikátní kořeny `block_name` (před prvním '/'), max 10. `note` je prázdné — pro tvé ruční zápisy.

### 2. Opravy KVAL levelu (9 řádků celkem)

**Změna úrovně (2 řádky — jen tam, kde byl cíl jednoznačně v pyramidě dané sezóny):**

| Sezóna | řádek | starý | nový | block_name |
|---|---|---|---|---|
| 1973/74 | 17 | L15 | **L25** | II.NHL / Kvalifikace o 1. ČNHL |
| 1973/74 | 22 | L15 | **L45** | Divize / Kvalifikace |

T-řádky pod oběma H také dostaly nový level.

**Doplnění prázdného levelu (7 řádků):**

| Sezóna | řádek | doplněno | block_name |
|---|---|---|---|
| 1956/57 | 10, 11, 15, 16, 19 | L35 | Kvalifikace o oblastní soutěž / … |
| 1981/82 | 3 | L25 | Kvalifikace o I.ČNHL / skupina A |
| 1981/82 | 8 | L25 | Kvalifikace o I.ČNHL / skupina B |

---

## NEPROVEDENO — čeká na tvé schválení

Post-validační kontrola našla **45 dalších H-řádků**, kde současný level neodpovídá pravidlu **„cíl kvalifikace + 5"**. Klíčové vzory:

### A) Kvalifikace o **2. ČNHL** / **2. SNHL** — současný `L25`, navržený `L35`
2. ČNHL je **3. úroveň** (L30), takže kvalifikace o ni má být L35.

| Sezóna | block_name | aktuální | navržený |
|---|---|---|---|
| 1976/77 | Kvalifikace o 2. ČNHL | L25 | L35 |
| 1977/78 | Kvalifikace o 2. ČNHL | L25 | L35 |
| 1983/84 | Kvalifikace o 2. ČNHL / Kvalifikace o SNHL | L25 | L35 |
| 1984/85 | Kvalifikace o 2. ČNHL / Kvalifikace o 1. SNHL | L25 | L35 |
| 1985/86 | Kvalifikace o 2. ČNHL / Kvalifikace o 2. SNHL | L25 | L35 |
| 1986/87 | Kvalifikace o 2. ČNHL / Kvalifikace o 2. SNHL | L25 | L35 |
| 1989/90 | Kvalifikace o případný postup do 2. ČNHL (2×) | L25/L45 | L35 |
| 1990/91 | Kvalifikace o 2. ČNHL | L25 | L35 |
| 1991/92 | Kvalifikace o 2. ČNHL | L25 | L35 |
| 1992/93 | Kvalifikace o 2. ČNHL (2×) | L25 | L35 |

### B) Kvalifikace o **divizi** — současný `L35`, navržený `L45`
Divize je 4. úroveň (L40, od 73/74), takže kvalifikace = L45.

| Sezóna | block_name | aktuální | navržený |
|---|---|---|---|
| 1969/70 | Kvalifikace o divizi | L35 | L45 |
| 1970/71 | Kvalifikace o divizi | L35 | L45 |
| 1970/71 | Krajský přebor / o postup do kvalifikace o Divizi | L35 | L45 |
| 1971/72 | Kvalifikace o divizi | L35 | L45 |
| 1975/76 | Kvalifikace o divizi | L35 | L45 |
| 1956/57 | Krajský přebor MNV Praha / kvalifikace o Divizi (2×) | L35 | L45 |

### C) Kvalifikace o **postup do II. ligy** — současný `L35`, navržený `L25`
Toto je hlavní kategorie u **moderních sezón (2013/14+)**. II. liga = L20.

| Sezóna | aktuální | navržený | počet H |
|---|---|---|---|
| 2013/14, 2014/15 | L35 | L25 | 7 |
| 2015/16, 2016/17, 2017/18 | L35 | L25 | 3 |
| 2018/19, 2019/20, 2020/21 | L35 | L25 | 3 |
| 1987/88 | L35 | L25 | 1 |

### D) Ostatní (smíšené)
- 1956/57 „Oblastní soutěž / kvalifikace o II.ligu" — L25 → **L15** (pokud II.liga té doby = L10)
- 1957/58 „Kvalifikace o II.ligu" — L25 → **L15** (totéž)
- 1974/75 „Divize / kvalifikace o 2. ČNHL" — L15 → **L35**
- 1978/79, 1979/80, 1980/81 — kvalifikace o I./ČNHL na L15 → **L25**
- 1989/90 „II.NHL / Kvalifikace o případný postup do 1.ČNHL" — L35 → **L25**
- 1991/92 „I. SNHL / …" — L25 → **L15** (pokud cíl je nejvyšší)
- 1992/93 „I.NHL / Kvalifikace o 1. ČNHL" — L15 → **L25**
- 1992/93 „I.SNHL / Kvalifikace o přímý postup do FHL" — L25 → **L15** (FHL = Federální HL = nejvyšší)

---

## NEJASNÉ (26 případů, k tvé ruční kontrole)

Algoritmus nedokázal cíl kvalifikace identifikovat. Vyžaduje znalost kontextu:

- **1949/50–1953/54** „Kvalifikace o ligu" / „Mistrovství republiky / kvalifikace" / „kvalifikace o celostátní soutěž" — pyramida 50. let je specifická, nutno určit, co byl cíl (celostátní liga = L10)
- **1954/55, 1956/57** „Kvalifikace o postup do oblastní soutěže" / „Kvalifikace o oblastní soutěž" — co je oblastní soutěž v té době?
- **1955/56** „Oblastní soutěže / kvalifikace o postup do Celostátní soutěže" — Celostátní = L10
- **1967/68** „II.liga / kvalifikace o ligu (l15)" — anotace `(l15)` v block_name napovídá L15
- **1976/77** „I.NHL / I.SNHL / kvalifikace o L10" — explicitně `L10` v textu, takže KVAL = L15
- **1984/85** „I.liga / kvalifikace o ligu" — pravděpodobně L15
- **1993/94–1997/98** „Kvalifikace o 2.ligu" — pokud 2. liga = L20, KVAL = L25 (současné L25 by bylo správné)
- **2013/14** „Předkolo baráže" (3×) — co je cílem té baráže?

---

## Co dál

Doporučuji takto:
1. **Schválit hromadně kategorii A+B+C** — všechny řídí univerzální pravidlo „cíl + 5", odchylky jsou systémové.
2. **Procházet kategorii D + 26 nejasných po jednom** s tvým komentářem (knihy, archiv, Wikipedia).
3. Po opravě **refresh PYRAMIDA listu** (znovu se naplní z aktuálních dat).

Záloha původních souborů zachována (mám lokálně, mohu vrátit kdykoli).
