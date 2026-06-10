Sem vlož Garamond ve formátu TTF (TrueType), např.:
  Garamond.ttf            (regular)
  Garamond-Bold.ttf       (bold)

App si font najde automaticky (preferuje cokoli s „garamond" v názvu).
Pořadí hledání:
  1) proměnná prostředí AUDIT_PDF_FONT (plná cesta k .ttf)
     volitelně AUDIT_PDF_FONT_BOLD
  2) tato složka fonts/
  3) systémové fonty (fc-match Garamond)
  4) fallback: serif (Liberation/DejaVu) — když Garamond není

Pozn.: reportlab umí jen .ttf (TrueType), NE .otf. Pokud máš Garamond jen
v .otf, převeď ho na .ttf (např. ve FontForge) nebo nastav jiný TTF.
