# Almanach — kompletní balíček

Rozbal a v terminálu vstup do téhle složky.

## Co tu najdeš

- `data/` — **65 sezónních Excelů** (zdroj pravdy) + dokumentace v CLAUDE_*.md
- `app.py` — **Viewer + Editor v jedné Flask appce**
- `print/html/` + `print/pdf/` — **65 sezón** jako HTML + PDF (předgenerované, otevři přímo)
- `viewer/` — **statický HTML viewer** (otevři `viewer/index.html` v prohlížeči, žádná instalace)
- `almanach.sqlite` + `export/*.csv` — konsolidovaná DB pro analýzu
- `*.py` — leštící nástroje (viz README.md)
- `README.md` — kompletní průvodce, co je k čemu

## Rychlý start

### Bez instalace (jen prohlížení)
1. Otevři `viewer/index.html` v prohlížeči → klikatelná navigace přes sezóny / kluby / soutěže
2. Nebo otevři jakýkoli `print/html/S*.html` / `print/pdf/S*.pdf` → samostatná sezóna

### S Pythonem (viewer + editor + edit zpět do xlsx)
```bash
pip install openpyxl pandas flask weasyprint
python3 app.py
```
Otevři `http://localhost:5000`. Klikáš jako na Wikipedii. Pro editaci klikni „✎ editovat" v hlavičce sezóny.

### Regenerace artefaktů (po úpravě xlsx)
```bash
python3 build_db.py            # → almanach.sqlite + export/*.csv
python3 health.py              # → HEALTH.md (kontrola stavu)
python3 print_seasons.py       # → print/html/ + print/pdf/
```

## Co je hotové

- 65 sezón 1949/50 – 2013/14
- prev_club_id (klub → minulá sezóna): **0 rozbitých**, 25 405 linků
- season_fate (postup/sestup/zánik/...): **0 nekonzistencí**, 97 % pokrytí
- pyramida soutěží: **595** feeds_into (postup) + **3 648** prev_node_id (návaznost soutěží)
- **9 676 klub-řetězů** napříč sezónami (Sparta Praha, Dynamo Pardubice 65 sezón, …)
- **3 882 soutěž-řetězů** (Extraliga 58 sezón, …)
- 65 sezón vyrenderováno do HTML + PDF
