# Hokejový almanach — kompletní pipeline

## Co kde je

| Komponenta | Soubor / složka | Co to dělá |
|---|---|---|
| **Zdroj pravdy** | `data/S*_FINAL.xlsx` (74 sezón, 1947/48–2020/21) | Per-sezónní Excel sešity. Jeden soubor = jedna sezóna. |
| **Pravidla + registry** | `docs/` (64 MD) | Ústava fází soutěží, audity, registr měst/krajů, reporty. |
| **Originální PDF** | `sources/CZE1/`, `sources/CZE2_3_nizsi/` | Zdrojové tabulky soutěží (nejvyšší + nižší) pro re-extrakci poškozených listů. |
| **App** (Viewer + Editor) | `app.py` | Jedna Flask aplikace — čte přímo z xlsx, prohlíží i edituje. |
| **Printer** (HTML+PDF) | `print/html/`, `print/pdf/` (gen. přes `print_seasons.py`) | Per-sezónní tištěné výstupy. PDF A4, stránkováno. |
| **Konsolidovaná DB** | `almanach.sqlite` (gen. přes `build_db.py`) | Volitelně — pro analýzu/audit, ne pro app. |
| **Health report** | `HEALTH.md` (gen. přes `health.py`) | Kontrolní report stavu DB (pokrytí linků, mezery). |
| **TODO** v sešitech | list `TODO` v každém S*.xlsx | Per-sezónní seznam položek k verifikaci. |

```bash
python3 app.py
# → otevři http://localhost:5000
```

Funkce:
- `/` — přehled sezón + nejdelší řetězy klubů
- `/s/{sid}` — sezóna (pyramida + všechny tabulky, klikatelné kluby a soutěže)
- `/club/{chain_id}` — běh klubu napříč sezónami
- `/comp/{comp_chain_id}` — běh soutěže napříč sezónami
- `/search?q=` — fulltext klubů
- `/s/{sid}/edit/clubs` — editace CLUBS (clean_name, prev_club_id, city, level, change_note)
- `/s/{sid}/edit/standings` — editace tabulkových výsledků (pos, GP/W/D/L, GF/GA, PTS, season_fate)

Po uložení změny v UI se sezóna znovu načte z xlsx a chainy se přepočtou.

## Tištěné výstupy

```bash
python3 print_seasons.py                  # všechny sezóny → HTML + PDF
python3 print_seasons.py S1966_67         # jedna
python3 print_seasons.py --html-only      # bez PDF (rychlejší)
```

Výstup do `print/html/S{sid}.html` a `print/pdf/S{sid}.pdf`.

## Volitelné — analýza přes SQLite

```bash
python3 build_db.py        # postaví almanach.sqlite + export/*.csv
python3 health.py          # → HEALTH.md (kontrolní report)
```

App ani Printer SQLite nepoužívají — jsou jen pro audit.

## Datové leštící nástroje (postupně použité)

| Skript | Co dělá |
|---|---|
| `fix_continuity.py` | Fáze 0–3: pseudo-kluby odstranit, prev_club_id linky, fate konzistence, feeds_into pyramida |
| `fix_broken_prev_d42.py` | Druhé kolo D42 oprav rozbitých prev_club_id |
| `polish_almanach.py` | Sedmifázové leštění (orphan CLUBS, fate cross-ref, city očistit/opravit, hub prev, feeds_into, fate sjednotit) |
| `fix_d44_bridges.py` | D44 identity můstky přes organizační reformy (Sokol→ZSJ→DSO→TJ) |
| `fill_remaining_fate.py` | Doplnit zbylé prázdné season_fate |
| `add_prev_node_id.py` | Doplnit prev_node_id do SYSTEM (návaznost soutěží napříč sezónami) |
| `revert_phase_f_falsepositives.py` | Vrátit false-positives auto-city úprav |
| `apply_todo_sheets.py` | Refresh per-sezónního listu TODO ve všech sešitech (vč. flagů poškozených GA/GF) |
| `fix_new_seasons_chain.py` | Návaznost klubů u sezón přidaných z balíku D42 (2017/18 přemapování, 1948/49→1949/50) |
| `harmonize_schema.py` | Srovnání hlavičky listu SYSTEM na kanonických 12 sloupců napříč sezónami |
| `validate_almanach.py` | Era-aware audit (mistr z META/SERIES vs 1. ZČ, validace 2-1-0 vs 3-2-1-0, poškozené buňky) → `docs/DATA_QUALITY.md` |
| `fill_from_pdf.py` | Re-extrakce poškozených extraligových tabulek z `sources/CZE1/*.pdf` (GA/GF/W/D/L/PTS) s ověřením a pojistkami zarovnání |
| `verify_vs_pdf.py` | Křížová kontrola nejvyšší soutěže všech sezón proti PDF (pořadí pravdy PDF>xlsx); `--write` opraví V/R/P, PTS a překlepy GF:GA |
| `fix_missing_links.py` | Rozrod klubů: doplní chybějící prev_club_id u jednoznačných pokračování (přesné jméno, jediný volný ne-B předchůdce) |
| `build_1947_48.py` | Postaví S1947_48 z PDF (Státní liga 2 sk. + finále) a naváže chain dopředu na S1948_49 |
| `phase_flow.py` | Tok fází soutěže (entry/phase_order/feeds_into): `--auto` plošně odvodí a zapíše všechny sezóny, `S####` vypíše flow, `--apply` vzorové |
| `audit.py`, `detail.py` | Diagnostika (rychlý audit přes Excely) |

## Datový model (xlsx · per sezóna)

Každý sešit `S{rok}_FINAL.xlsx` obsahuje:

| List | Co obsahuje |
|---|---|
| `10_liga`, `20_*`, `30_*`, `40_*`, `KVAL` | Per-soutěžní tabulky (H/T/S/R řádky, kódy A–W) |
| `CLUBS` | Klub v sezóně: club_id, clean_name, prev_club_id, city, level, change_note |
| `SYSTEM` | Pyramida soutěží: node_id, name, level, parent_node_id, feeds_into, **prev_node_id** |
| `NOTES` | Volné poznámky k uzlům + [TBD] flagy |
| `SERIES` | Playoff série |
| `META` | Metadata sezóny (label, era, scoring) |
| `TODO` | Položky k ověření (generuje `apply_todo_sheets.py`) |

## Wikipedia-style navigace

- **Klub → běh sezónami:** chain_id (řetěz prev_club_id)
- **Sezóna → další sezóna:** šipky ← → v UI
- **Soutěž → minulá sezóna soutěže:** prev_node_id (SYSTEM)
- **Soutěž → vyšší/nižší tier:** parent_node_id, feeds_into
- **Klikni na klub** v jakékoli tabulce → jeho historie
- **Klikni na soutěž** v pyramidě → její historie

## Závislosti

```bash
pip install openpyxl pandas flask weasyprint
```

- `openpyxl` — čtení/zápis xlsx
- `flask` — webová app
- `pandas` — pro build_db.py
- `weasyprint` — PDF rendering (jen pro print_seasons.py)

## Generované artefakty (gitignorované)

- `almanach.sqlite`, `export/`
- `print/`
- `S*_ukazka.html` (ad-hoc náhledy)
- `HEALTH.md`

