#!/usr/bin/env python3
"""
print_seasons.py — Vyrenderuje pro každou sezónu print-friendly artefakty:

  print/html/{sid}.html   — single-page HTML (lze otevřít, vytisknout přímo)
  print/pdf/{sid}.pdf     — PDF přes weasyprint (A4, stránkováno)

XLSX = už existuje jako zdroj v data/, není třeba znovu generovat.

Použití:
  python3 print_seasons.py             # všechny sezóny
  python3 print_seasons.py S1966_67    # jen jedna
  python3 print_seasons.py --html-only # bez PDF (rychlejší)
"""
import sqlite3, os, html, sys
from collections import defaultdict

DBF = 'almanach.sqlite'
OUT = 'print'

CSS = """@page{size:A4;margin:14mm}
body{font:11px/1.35 -apple-system,Segoe UI,Roboto,sans-serif;color:#222;margin:0}
h1{font-size:18px;margin:0 0 8px;border-bottom:2px solid #333;padding-bottom:4px}
h2{font-size:13px;margin:14px 0 3px;color:#234;page-break-after:avoid}
h3{font-size:11px;margin:8px 0 2px;color:#555;font-weight:600;page-break-after:avoid}
table{border-collapse:collapse;width:100%;margin-bottom:6px;font-size:10px;page-break-inside:avoid}
th,td{padding:2px 6px;border:1px solid #bbb;text-align:left}
th{background:#e8e8ee;font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.fate{font-size:9px;color:#666;padding-left:4px}
.muted{color:#888;font-size:10px}
.summary{background:#f4f6f9;padding:6px 10px;margin:8px 0;border-left:3px solid #1f3a5f;font-size:10px}"""


def fate_short(f):
    if not f:
        return ''
    return {'postup': '↑', 'sestup': '↓', 'setrval': '=', 'zanik': '×',
            'slouceni': '⇄', 'reorganizace': '↻', 'setrval?': '=?'}.get(f, f)


def render_season(c, sid):
    label = c.execute("SELECT season_label FROM seasons WHERE season_id=?",
                      (sid,)).fetchone()[0]
    nodes = {n['node_id']: n for n in c.execute(
        "SELECT * FROM competitions WHERE season_id=?", (sid,))}
    rows = c.execute("""SELECT * FROM standings WHERE season_id=?
                        ORDER BY sheet, node_id, CAST(pos AS INTEGER), club_name""",
                     (sid,)).fetchall()
    by_sheet = defaultdict(list)
    for r in rows:
        by_sheet[r['sheet'] or '?'].append(r)

    # summary
    n_clubs = c.execute("SELECT COUNT(*) FROM clubs WHERE season_id=?", (sid,)).fetchone()[0]
    n_nodes = len(nodes)

    out = [f"<!doctype html><meta charset=utf-8><title>{label}</title><style>{CSS}</style>"]
    out.append(f"<h1>Sezóna {html.escape(str(label))}</h1>")
    out.append(f'<div class=summary>{n_clubs} klubů · {n_nodes} soutěží · '
               f'{sum(len(v) for v in by_sheet.values())} tabulkových řádků</div>')

    for sh in sorted(by_sheet):
        out.append(f"<h2>{html.escape(sh)}</h2>")
        cur_node = None
        for r in by_sheet[sh]:
            if r['node_id'] != cur_node:
                if cur_node is not None:
                    out.append("</table>")
                cur_node = r['node_id']
                nn = nodes.get(cur_node)
                nm = nn['name'] if nn else cur_node
                meta = ' · '.join(filter(None, [
                    nn['competition_type'] if nn else None,
                    nn['level'] if nn else None]))
                out.append(f"<h3>{html.escape(str(nm or ''))} "
                           f'<span class=muted>{html.escape(meta)}</span></h3>')
                out.append("<table><tr><th>#</th><th>Klub</th><th>GP</th>"
                           "<th>W</th><th>D</th><th>L</th><th>GF:GA</th>"
                           "<th>PTS</th><th></th></tr>")
            out.append(f"<tr><td>{r['pos'] or ''}</td>"
                       f"<td>{html.escape(str(r['club_name'] or ''))}</td>"
                       f"<td class=num>{r['GP'] or ''}</td>"
                       f"<td class=num>{r['W'] or ''}</td>"
                       f"<td class=num>{r['D'] or ''}</td>"
                       f"<td class=num>{r['L'] or ''}</td>"
                       f"<td class=num>{(r['GF'] or '')}:{(r['GA'] or '')}</td>"
                       f"<td class=num>{r['PTS'] or ''}</td>"
                       f"<td class=fate>{fate_short(r['season_fate'])}</td></tr>")
        if cur_node is not None:
            out.append("</table>")
    return label, '\n'.join(out)


def main():
    only = None
    html_only = False
    for arg in sys.argv[1:]:
        if arg == '--html-only':
            html_only = True
        elif arg.startswith('S'):
            only = arg
    if not os.path.exists(DBF):
        print(f"Chybí {DBF}. Spusť: python3 build_db.py")
        return
    for sub in ('html', 'pdf'):
        os.makedirs(f"{OUT}/{sub}", exist_ok=True)
    db = sqlite3.connect(DBF); db.row_factory = sqlite3.Row; c = db.cursor()
    seasons = c.execute("SELECT season_id FROM seasons ORDER BY season_id").fetchall()

    if not html_only:
        try:
            import weasyprint
        except ImportError:
            print("weasyprint není nainstalovaný — generuju jen HTML.")
            html_only = True

    n_html = n_pdf = 0
    for s in seasons:
        sid = s['season_id']
        if only and sid != only:
            continue
        label, htmlx = render_season(c, sid)
        with open(f"{OUT}/html/{sid}.html", 'w', encoding='utf-8') as fh:
            fh.write(htmlx)
        n_html += 1
        if not html_only:
            try:
                weasyprint.HTML(string=htmlx).write_pdf(f"{OUT}/pdf/{sid}.pdf")
                n_pdf += 1
            except Exception as e:
                print(f"  ! PDF {sid} selhal: {e}")
        if n_html % 10 == 0:
            print(f"  ... {n_html} HTML / {n_pdf} PDF")
    print(f"\n=== {OUT}/ ===")
    print(f"  HTML: {n_html} sezón v print/html/")
    if not html_only:
        print(f"  PDF:  {n_pdf} sezón v print/pdf/")
    print(f"  XLSX zdroje: data/ (už máš)")
    db.close()


if __name__ == '__main__':
    main()
