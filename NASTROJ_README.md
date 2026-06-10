# Almanach — nástroj (korektor · viewer · builder · printer)

Vše v jednom souboru **`app.py`**. Zdroj pravdy jsou sešity v **`data/S*_FINAL.xlsx`**.

## 1. Co potřebuješ
- Python 3.9+ (testováno na 3.11)
- balíčky: `flask`, `openpyxl`, `reportlab` (pro PDF)

## 2. Instalace
```bash
# (volitelně) virtuální prostředí
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install flask openpyxl reportlab
```

## 3. Spuštění aplikace
```bash
python app.py
```
Otevři v prohlížeči: **http://localhost:5000**

- Seznam sezón → klikni na sezónu → **pyramida + všechny tabulky**.
- Pod tabulkami se žlutě/oranžově ukazují **komentáře „co chybí"**.
- Tlačítko **⚑ audit** → vyřeš položku (stav + řešení + poznámka) → **Uložit do xlsx**
  (zapíše se rovnou do příslušného sešitu — žádný mezikrok).
- **PDF plný** / **PDF audit** = tisk pro ruční práci (čekárna, gauč).

## 4. Tisk / export z příkazové řádky
```bash
python app.py pdf  all        # plná sezóna + audit → docs/audit_pdf/
python app.py html all        # totéž jako HTML     → docs/audit_html/
python app.py xlsx all        # audit worklist      → docs/Audit_export.xlsx
python app.py pdf  1948_49     # jen jedna sezóna
```

## 5. Přestavba databáze (po opravách)
Sešity jsou zdroj pravdy. Když chceš promítnout změny do `almanach.sqlite` + CSV:
```bash
python app.py build       # = python build_db.py
```

## 6. Garamond v PDF
Jsem nastavený na Garamond. Vlož svůj **Garamond.ttf** do složky `fonts/`
(viz `fonts/README.txt`), nebo nastav cestu:
```bash
# Linux/macOS
export AUDIT_PDF_FONT=/cesta/Garamond.ttf
export AUDIT_PDF_FONT_BOLD=/cesta/Garamond-Bold.ttf
# Windows (PowerShell)
$env:AUDIT_PDF_FONT="C:\Windows\Fonts\garamond.ttf"
```
Když Garamond nenajde, použije serif fallback (almanach se vytiskne tak jako tak).

## 7. Test, že vše šlape
```bash
python test_app.py        # projede routy, PDF, zápis do xlsx (a vrátí ho zpět)
```
Očekávaný výstup: `VŠE OK`.

## Soubory v balíku
- `app.py` — celý nástroj (web + CLI)
- `data/S*_FINAL.xlsx` — 74 sezón (zdroj pravdy, sem se zapisuje)
- `build_db.py` — konsolidace sešitů → `almanach.sqlite` + CSV
- `apply_torzo_gaps.py` — (re-runnable) zápis torz do TODO/NOTES listů
- `test_app.py` — smoke testy
- `requirements.txt`, `fonts/`, `run.sh`, `run.bat`
