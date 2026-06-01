# AUDIT DATOVÉ KVALITY — Hokejový almanach (72 sezón)

**Verze:** 1.0 · cíl: technická a datová dokonalost

## 1. Souhrn validace tabulek (V+R+P=Z)

| Úroveň | Řádků | Chyb | % | Poznámka |
|---|---:|---:|---:|---|
| Extraliga | 1151 | 455 | 40% | většina = moderní formát + 4 poškozené listy |
| 1. liga | 1989 | 421 | 21% | rozdělené skupiny + moderní formát |
| 2. liga/divize | 1939 | 642 | 33% | regionální + moderní formát |
| Kvalifikace | 582 | 7 | 1% | ✓ čisté |
| Kraj/okres | 17775 | 1157 | 7% | drobné chyby ze zdrojových PDF |

⚠️ Vysoké % NENÍ vždy chyba — viz klasifikace níže.

## 2. Klasifikace extraligových listů (72 sezón)

| Kategorie | Počet | Stav |
|---|---:|---|
| **OK** ✓ | 44 | V+R+P=Z platí (éra 2-1-0) |
| **Moderní formát** | 19 | 3-2-1-0 (V/VP/PP/P) — V+R+P≠Z je očekávané |
| **⚠️ Ke kontrole** | 5 | GF=0 nebo posun (1991–1995) |
| **POŠKOZENÝ** | 4 | GA chybí (1980/81, 1981/82, 2000/01, 2001/02) |

## 3. POŠKOZENÉ listy — nutná re-extrakce ze zdroje

Tyto listy mají **neúplná data** (chybí sloupec branek), které **nelze dopočítat** z tabulky:

| Sezóna | Problém | Co chybí |
|---|---|---|
| **1980/81** | GA = `:` | obdržené branky; hodnoty posunuté |
| **1981/82** | GA = `:` | obdržené branky |
| **2000/01** | GA = `:` | obdržené branky (GF=149 OK) |
| **2001/02** | GA = `:` | obdržené branky |

**Akce:** re-extrahovat skóre ze zdrojových PDF (Pavel má originály).

## 4. KE KONTROLE — GF=0 (1991–1995)

Rozdělené ligy + nadstavba; vstřelené branky (GF) chybí:

| Sezóna | GF=0 řádků | Formát |
|---|---:|---|
| 1991/92 | 5 | Skupina Západ/Východ + nadstavba |
| 1992/93 | 7 | poslední federální |
| 1993/94 | 4 | rozdělení ČSSR |
| 1994/95 | 4 | samostatná ČR |
| 1995/96 | (posun) | 18 klubů |

**Akce:** ověřit GF ze zdroje pro tyto sezóny.

## 5. MODERNÍ formát (2002/03+) — JINÁ validační pravidla

Od sezóny 2002/03 se používá bodování **3-2-1-0**:
- V (výhra) = 3 body
- VP (výhra v prodloužení/nájezdech) = 2 body
- PP (prohra v prodloužení) = 1 bod
- P (prohra) = 0 bodů

Tabulka má **5 výsledkových sloupců** (V/VP/PP/P), ne 3 (V/R/P). Proto **V+R+P≠Z neplatí** — je nutné počítat V+VP+PP+P=Z.

⚠️ Validace musí rozlišovat éru:
```python
def validate_row(row, season_year):
    if season_year >= 2002:
        # 3-2-1-0: V + VP + PP + P = GP
        return row.v + row.vp + row.pp + row.p == row.gp
    else:
        # 2-1-0: V + R + P = GP
        return row.w + row.d + row.l == row.gp
```

⚠️ **POZOR:** aktuální parsing čte jen 3 sloupce (W/D/L) i pro moderní éru → moderní data jsou parsována nesprávně. Pro moderní sezóny je třeba rozšířit parser o sloupce VP/PP.

## 6. ČISTÉ sezóny (44) — éra 2-1-0

Sezóny 1949/50–1979/80 (kromě 1980/81), 1982/83–1990/91, 1996/97–1999/00:
- V+R+P=Z platí ✓
- body=2V+R ✓
- GF:GA kompletní ✓

Tyto jsou referenční datová kvalita.

## 7. Velké odchylky (Δ≥10) — překlepy ve zdroji

192 řádků s velkou odchylkou V+R+P vs Z. Příklady (kraj/okres):
- 1968/69 Sokol Černá Hora: V+R+P=102, Z=13 (Δ89) — překlep
- 1963/64 Baník Orlová: V+R+P=81, Z=10 (Δ71)
- 1954/55 Sokol Těšetice: V+R+P=40, Z=10 (Δ30)

**Akce:** opravit zjevné překlepy (krajské/okresní úrovně, nízká priorita).

## 8. PLÁN technické dokonalosti

### Priorita 1 — Poškozené extraligové listy (4)
Re-extrahovat 1980/81, 1981/82, 2000/01, 2001/02 ze zdroje.

### Priorita 2 — Moderní formát parser (19 sezón)
Rozšířit parser o sloupce VP/PP pro éru 2002+. Validace dle éry.

### Priorita 3 — GF=0 sezóny (5)
Doplnit vstřelené branky 1991–1995 ze zdroje.

### Priorita 4 — Překlepy kraj/okres (192)
Opravit zjevné překlepy (Δ≥10).

### Priorita 5 — Chain integrita
Udržet 99,99 % (viz PROSTUPNOST_AUDIT.md) — základ pro výpočet osudů.

## 9. Validační pravidla (k zabudování)

```python
RULES = {
    'vrp_equals_gp': 'V+R+P=GP (éra 2-1-0) / V+VP+PP+P=GP (3-2-1-0)',
    'points_formula': 'body=2V+R (2-1-0) / body=3V+2VP+PP (3-2-1-0)',
    'ga_not_colon': 'GA musí být číslo, ne ":"',
    'gf_not_zero': 'GF=0 jen výjimečně (prázdná tabulka)',
    'pos_sequential': 'pořadí 1..N bez mezer',
    'chain_valid': 'prev_club_id ukazuje na existující záznam',
}
```

---

**Závěr:** Z 72 extraligových sezón je 44 datově čistých, 19 v moderním formátu (vyžaduje parser update), 5 ke kontrole, 4 poškozené (re-extrakce). Nižší soutěže mají ~7 % drobných chyb ze zdrojových PDF.
