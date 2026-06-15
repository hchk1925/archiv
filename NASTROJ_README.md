# Almanach — nástroj (korektor · viewer · builder · printer)

Zdroj pravdy jsou sešity v **`data/S*_FINAL.xlsx`**. Dvě podoby téhož:
- **`desktop.py`** — desktopová appka (okno, bez prohlížeče) — **doporučená**
- **`app.py`** — webová verze (běží v prohlížeči) — bonus

Obě sdílí stejný backend a zapisují do stejných Excelů.

## 1. Co potřebuješ
- Python 3.9+ (na Windows/macOS má `tkinter` v sobě)
- balíčky: `flask`, `openpyxl`, `reportlab`

## 2. Spuštění — DESKTOP (doporučeno)
```
Windows:      dvojklik na run_desktop.bat
macOS/Linux:  ./run_desktop.sh
```
(Při prvním běhu se doinstalují knihovny.) Otevře se okno:
- vlevo **strom soutěží** (torzo = ⚑, vyřešené = ✓),
- vpravo **tabulka týmů** a žlutý **komentář „co chybí"**,
- dole **Řešení** (stav + typ + poznámka) → **Uložit do xlsx** zapíše rovnou do sešitu,
- nahoře **PDF plný / PDF audit** pro tisk.

Ručně: `pip install flask openpyxl reportlab` a `python desktop.py`.

## 3. Spuštění — WEB (bonus)
```
python app.py        →  http://localhost:5000
```
Stejné funkce v prohlížeči (sezóna → tabulky + komentáře → ⚑ audit → uložit).

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
- `desktop.py` — desktopová appka (Tkinter) — **doporučená**
- `app.py` — webová verze (Flask) + CLI printer/builder
- `data/S*_FINAL.xlsx` — 74 sezón (zdroj pravdy, sem se zapisuje)
- `build_db.py` — konsolidace sešitů → `almanach.sqlite` + CSV
- `apply_torzo_gaps.py` — (re-runnable) zápis torz do TODO/NOTES listů
- `test_app.py`, `test_desktop.py` — smoke testy
- `requirements.txt`, `fonts/`
- `run_desktop.bat` / `run_desktop.sh` — spuštění desktopu
- `run.bat` / `run.sh` — spuštění webu
