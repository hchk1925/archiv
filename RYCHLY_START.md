# Almanach — kompletní balíček

Rozbal a v terminálu vstup do téhle složky.

## Co tu najdeš

- `data/` — **65 sezónních Excelů** (zdroj pravdy) + dokumentace v CLAUDE_*.md
- `app.py` — **Viewer + Editor** (Python Flask, čte přímo z xlsx)
- `print/html/` + `print/pdf/` — **65 sezón** jako HTML + PDF (předgenerované, otevři přímo)
- `almanach.sqlite` + `export/*.csv` — konsolidovaná DB pro analýzu
- `*.py` — leštící nástroje (viz README.md)
- `README.md` — kompletní průvodce

## Rychlý start

### Viewer + Editor (hlavní nástroj)
```bash
pip install openpyxl pandas flask weasyprint
python3 app.py
```
Otevři `http://localhost:5000` v prohlížeči. Klikáš jako na Wikipedii:
- **Sezóny** → tabulky všech soutěží, klikatelné kluby
- **Klub** → běh všemi sezónami (Sparta Praha, Dynamo Pardubice 65 sezón, …)
- **Soutěž** → její historie napříč sezónami (Extraliga 58 sezón)
- **Hledat klub** — fulltext přes 9 676 řetězů
- **Editace** — klikni „✎ editovat" v hlavičce sezóny → uloží zpět do xlsx

### Bez Pythonu (jen tištěné výstupy)
Otevři jakýkoli `print/html/S{rok}.html` v prohlížeči nebo `print/pdf/S{rok}.pdf`.
Tabulky všech soutěží té sezóny.

### Regenerace artefaktů (po úpravě xlsx)
```bash
python3 build_db.py            # → almanach.sqlite + export/*.csv
python3 health.py              # → HEALTH.md (kontrola stavu)
python3 print_seasons.py       # → print/html/ + print/pdf/
```

## Co je hotové

- 65 sezón 1949/50 – 2013/14
- prev_club_id (klub → minulá sezóna): **0 rozbitých**, 25 405 linků
- season_fate: **0 nekonzistencí**, 97 % pokrytí
- pyramida soutěží: **595** feeds_into + **3 648** prev_node_id
- **9 676 klub-řetězů** napříč sezónami
- **3 882 soutěž-řetězů**
- 65 sezón vyrenderováno do HTML + PDF
