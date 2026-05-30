# Hokejový almanach — kompletní pipeline

## Co kde je

| Komponenta | Soubor / složka | Co to dělá |
|---|---|---|
| **Zdroj pravdy** | `data/S*_FINAL.xlsx` (65 sezón) | Per-sezónní Excel sešity. Jeden soubor = jedna sezóna. |
| **Konsolidovaná databáze** | `almanach.sqlite` | Postavená z Excelů. Spojuje vše do queryovatelné SQL DB. |
| **Health report** | `HEALTH.md` | Kontrolní report stavu DB (pokrytí linků, konzistence, mezery). |
| **Viewer** (HTML) | `viewer/index.html` | Statický web. Otevři v prohlížeči. Navigace Wikipedia-style. |
| **Printer** (HTML+PDF) | `print/html/`, `print/pdf/` | Per-sezónní tištěné výstupy. PDF A4, stránkováno. |
| **Editor** (Flask) | `editor.py` | Lokální web editor. Spusť `python3 editor.py`, otevři localhost:5000. |
| **TODO** v sešitech | list `TODO` v každém S*.xlsx | Per-sezónní seznam položek k verifikaci. |

## Workflow

```bash
# 1. Z Excelů postavit/aktualizovat DB
python3 build_db.py

# 2. Kontrola stavu DB
python3 health.py                # → HEALTH.md

# 3. Vyrenderovat viewer
python3 build_viewer.py          # → viewer/

# 4. Vyrenderovat per-sezónní HTML + PDF
python3 print_seasons.py         # → print/html/ + print/pdf/
python3 print_seasons.py S1966_67           # jen jedna sezóna
python3 print_seasons.py --html-only        # bez PDF (rychlejší)

# 5. Editor (lokálně)
python3 editor.py                # otevři http://localhost:5000
```

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
| `apply_todo_sheets.py` | Refresh per-sezónního listu TODO ve všech sešitech |
| `audit.py`, `detail.py` | Diagnostika (rychlý audit přes Excely) |

## Datový model (`almanach.sqlite`)

| Tabulka | Klíč | Co obsahuje |
|---|---|---|
| `seasons` | season_id | Metadata sezóny (label, era, scoring system) |
| `clubs` | (season_id, club_id) | Klub v sezóně + `chain_id` (řetěz napříč sezónami) + prev_club_id |
| `competitions` | (season_id, node_id) | Soutěž + hierarchie (parent_node_id) + feeds_into + **prev_node_id** |
| `standings` | tr_id | T-řádky (tabulky) — výsledky klubů |
| `registrations` | — | R-řádky (registrovaný klub bez tabulky) |
| `series` | series_id | Playoff série |
| `notes` | — | Poznámky |

## Wikipedia-style navigace

- **Klub → běh sezónami:** `clubs.chain_id` (řetěz prev_club_id přes všechny sezóny)
- **Sezóna → další sezóna:** přes řazení `season_id`
- **Soutěž → minulá sezóna soutěže:** `competitions.prev_node_id`
- **Soutěž → vyšší/nižší tier:** `parent_node_id` (hierarchie), `feeds_into` (postup), `feeds_into_loser` (sestup, částečně)
- **Tabulkový řádek → klub → historie:** `standings.club_id` → `clubs.chain_id`
- **Vyhledávání klubu** přes `viewer/search.html`

## Generované artefakty (gitignorované)

- `almanach.sqlite` (regeneruj přes `build_db.py`)
- `export/*.csv` (regeneruj)
- `viewer/` (regeneruj přes `build_viewer.py`)
- `print/` (regeneruj přes `print_seasons.py`)
- `S*_ukazka.html` (ad-hoc náhledy)
- `HEALTH.md` (regeneruj přes `health.py`)
