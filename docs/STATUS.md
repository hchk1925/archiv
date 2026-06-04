# STAV ALMANACHU — přehled (pro pokračování ruční prací)

_Generuje se ručně; stav k poslednímu commitu. Zdraví ověř kdykoli: `python3 build_db.py && python3 health.py`._

## Rozsah
**74 sezón 1947/48 – 2020/21.** Zdroj pravdy: `data/S*_FINAL.xlsx` (per sezóna).
Originální podklady: `sources/CZE1/` (nejvyšší soutěž) + `sources/CZE2_3_nizsi/` (nižší).

## Co je HOTOVÉ a ověřené ✅

| Vrstva | Stav | Jak ověřeno |
|---|---|---|
| **Mistři** (celá historie) | M badge na skutečném mistrovi (play-off vítěz), `seasons.champion` v DB | PDF + web (sporné dohledané) |
| Nejvyšší soutěž | standings srovnané | `verify_vs_pdf.py` (exact diff) |
| 1./2. liga, divize | standings srovnané | `verify_vs_pdf.py` |
| Oblastní soutěž + KVAL | standings srovnané (exact) | `verify_vs_pdf.py` |
| Rané sezóny 1947/48–1952/53 | postaveny/ověřeny z PDF vč. play-off fází | PDF |
| Chainy klubů | navázané, **0 rozbitých** | `health.py` |
| Tok fází soutěží | `entry`/`phase_order`/`feeds_into` u 633 soutěží | `phase_flow.py --auto` |

**Integrita:** 0 rozbitých chainů · 0 nekonzistencí fate · 0 orphanů · éra 2-1-0 V+R+P≠GP=0 · poškozené buňky=0.

## Co zbývá na RUČNÍ průchod (s papíry) ✋

1. **Krajské soutěže** (listy 30*/20*/Z* regionální) — DS PDF je nepokrývá, 95 % OK.
   Worklist: **`docs/KRAJSKE_CHECK.md`** (1065 skupin s nálezem; krajský přebor / I. třída nejvýš).
   - **1948/49 župní** (listy `Z*`, 15 žup, I.–III. třída, ~560 týmů) doplněny ze surového
     XLS kolegy jako **základ úplnosti** — mnohde neúplné, hodnoty k ruční verifikaci
     (archivy/dobový tisk). Finále/kvalifikace a prázdné sekce evidovány v `NOTES`.
2. **Oblastní/KVAL „k ověření"** — kde data mají neúplný rozpis vs PDF (tým odehrál méně zápasů).
   Worklist: **`docs/PDF_VERIFY_WORKLIST.md`** (303 řádků po sezónách; část jsou false-positives = správně postavené play-off bloky).
3. **Drobnosti k rozhodnutí:** 18× `season_fate = "setrval?"` (nejistota ve zdroji), 10 víceznačných chybějících chainů, `season_fate` u kvalifikací.

> ⚠️ **Co NEautomatizovat:** doplňování „k ověření" řádků párováním jmen z PDF se prokázalo jako nespolehlivé (prokládaný layout → posun o řádek → poškození). Tahle vrstva se musí číst okem.

## Jak pracovat

```bash
python3 app.py            # prohlížeč/editor na http://localhost:5000
python3 build_db.py       # konsolidovaná almanach.sqlite + export/*.csv
python3 health.py         # kontrolní report (HEALTH.md)
python3 validate_almanach.py   # era-aware audit → docs/DATA_QUALITY.md
python3 verify_vs_pdf.py [--write]  # diff standings proti PDF (národní + oblastní/KVAL)
python3 phase_flow.py S####    # tok fází dané sezóny
```

Závislosti se instalují samy přes SessionStart hook (`.claude/hooks/session-start.sh`),
jinak: `pip install -r requirements.txt`.

## Klíčová dokumentace
- `docs/CLAUDE_FAZE_SOUTEZI.md` — ústava fází soutěží (vč. §3.6 kódování toku).
- `docs/MASTER_REPORT.md` — stav všech sezón + provedené opravy.
- `docs/DATA_QUALITY.md` — era-aware audit (mistři, validace, poškozené buňky).
- `docs/KRAJSKE_CHECK.md`, `docs/PDF_VERIFY_WORKLIST.md` — worklisty k ruční kontrole.
