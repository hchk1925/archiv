#!/usr/bin/env python3
"""
editor.py — Lokální webový editor almanachu (Flask).

Spuštění:
  python3 editor.py
  → otevři http://localhost:5000 v prohlížeči

Co umí:
  - List sezón → klubů v sezóně
  - Editovat CLUBS: clean_name, prev_club_id, city, change_note
  - Editovat T-řádky standings: pos, GP/W/D/L/GF/GA/PTS, season_fate
  - Editovat NOTES (přidat poznámku k uzlu/sezóně)
  - Uložit → píše zpět do data/S{sid}_FINAL.xlsx
  - Hledat klub napříč sezónami (chain navigace)

Žádné login, žádné konflikty — single-user lokální nástroj.
"""
import openpyxl, glob, os, re, json
from flask import Flask, request, render_template_string, redirect, url_for, jsonify

DATA = 'data'
NON_DATA = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA', 'TODO'}

app = Flask(__name__)

# ── helpers ──
SEASONS = None


def discover_seasons():
    global SEASONS
    SEASONS = sorted([os.path.basename(p).replace('_FINAL.xlsx', '')[1:]
                      for p in glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx'))])
    return SEASONS


def sid_to_path(sid):
    return os.path.join(DATA, f'S{sid}_FINAL.xlsx')


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def load_sheet(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        wb.close(); return [], {}
    ws = wb[sheet]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        wb.close(); return [], {}
    H = hidx(rows[0])
    wb.close()
    return rows, H


# ── routes ──
PAGE = """<!doctype html><meta charset=utf-8><title>{{title}} – Editor</title>
<style>
*{box-sizing:border-box}
body{font:14px/1.4 -apple-system,Segoe UI,sans-serif;margin:0;color:#222;background:#f6f7fa}
header{background:#1a3050;color:#fff;padding:10px 18px;display:flex;gap:14px;align-items:center}
header a{color:#cfe0ff;text-decoration:none}
header form{margin-left:auto}
header input{padding:5px 8px;border:0;border-radius:3px;width:240px}
main{max-width:1400px;margin:14px auto;padding:0 16px}
h2{margin:14px 0 6px;font-size:18px;color:#1a3050}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:4px}
.grid a{display:block;text-align:center;padding:6px;background:#fff;border:1px solid #ddd;border-radius:4px;text-decoration:none;color:#1a3050}
.grid a:hover{background:#eef2f7}
table{border-collapse:collapse;width:100%;background:#fff;margin:6px 0;font-size:13px}
th,td{padding:4px 7px;border:1px solid #ddd;text-align:left;vertical-align:top}
th{background:#e8ecf3;font-weight:600}
input[type=text],textarea,select{width:100%;padding:3px 5px;border:1px solid #ccc;border-radius:3px;font:inherit}
textarea{min-height:38px;font-size:12px}
input[type=number]{width:60px;padding:3px 5px;border:1px solid #ccc;border-radius:3px}
button{padding:6px 14px;background:#1a3050;color:#fff;border:0;border-radius:4px;cursor:pointer;font-weight:600}
button:hover{background:#2d4868}
.btn-sec{background:#888}
.muted{color:#888;font-size:12px}
.flash{background:#dcf3df;color:#1b5e20;padding:8px 12px;border-radius:4px;margin:8px 0}
.tab-bar{display:flex;gap:2px;margin:8px 0 0}
.tab-bar a{padding:6px 14px;background:#dde2eb;text-decoration:none;color:#234;border-radius:4px 4px 0 0}
.tab-bar a.active{background:#fff;font-weight:600}
.tab-body{background:#fff;padding:12px;border-radius:0 4px 4px 4px}
</style>
<header>
  <a href="/" style="font-size:16px;font-weight:600;color:#fff">🏒 Editor almanachu</a>
  {% if sid %}<span class=muted>· sezóna {{sid}}</span>{% endif %}
  <form action="/search">
    <input name="q" placeholder="hledat klub (3+ znaky)" value="{{request.args.get('q','')}}">
  </form>
</header>
<main>
{% if flash %}<div class=flash>{{flash}}</div>{% endif %}
{{body|safe}}
</main>
"""


def render(title, body, sid=None, flash=None):
    return render_template_string(PAGE, title=title, body=body, sid=sid, flash=flash)


@app.route('/')
def index():
    seasons = discover_seasons()
    grid = '<div class=grid>'
    for s in seasons:
        grid += f'<a href="/s/{s}">{s.replace("_","/")}</a>'
    grid += '</div>'
    body = f'<h2>Sezóny ({len(seasons)})</h2>{grid}'
    return render('Sezóny', body)


@app.route('/s/<sid>')
def season(sid):
    path = sid_to_path(sid)
    if not os.path.exists(path):
        return f'sezóna {sid} neexistuje', 404
    rows, H = load_sheet(path, 'CLUBS')
    # tab navigation
    tab = request.args.get('tab', 'clubs')
    seasons = discover_seasons()
    idx = seasons.index(sid)
    prev = seasons[idx - 1] if idx > 0 else None
    nxt = seasons[idx + 1] if idx + 1 < len(seasons) else None
    nav = (f'<p>{"<a href=/s/"+prev+">← "+prev+"</a>" if prev else "—"} · '
           f'<a href="/">přehled</a> · '
           f'{"<a href=/s/"+nxt+">"+nxt+" →</a>" if nxt else "—"}</p>')

    tabs = ('<div class=tab-bar>'
            f'<a href="?tab=clubs" class="{ "active" if tab=="clubs" else ""}">CLUBS ({len(rows)-1})</a>'
            f'<a href="?tab=standings" class="{ "active" if tab=="standings" else ""}">Standings</a>'
            f'<a href="?tab=notes" class="{ "active" if tab=="notes" else ""}">NOTES</a>'
            '</div><div class=tab-body>')

    if tab == 'clubs':
        body = nav + f'<h2>{sid} · CLUBS</h2>' + tabs
        body += f'<form method=POST action="/s/{sid}/clubs">'
        body += '<table><tr><th>club_id</th><th>clean_name</th><th>city</th><th>prev_club_id</th><th>level</th><th>change_note</th></tr>'
        for r in rows[1:]:
            if not r or r[H['club_id']] is None:
                continue
            cid = r[H['club_id']]
            body += f'<tr><td class=muted>{cid}<input type=hidden name="cid_{cid}" value="{cid}"></td>'
            for f in ['clean_name', 'city', 'prev_club_id', 'level']:
                v = r[H.get(f, -1)] if f in H else ''
                body += f'<td><input type=text name="{f}_{cid}" value="{(v or "")}"></td>'
            v = r[H.get('change_note', -1)] if 'change_note' in H else ''
            body += f'<td><textarea name="change_note_{cid}">{(v or "")}</textarea></td></tr>'
        body += '</table><br><button>Uložit CLUBS</button></form></div>'
        return render(f'{sid} CLUBS', body, sid)

    if tab == 'standings':
        # list všech sheet-data
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        body = nav + f'<h2>{sid} · Standings</h2>' + tabs
        body += f'<form method=POST action="/s/{sid}/standings">'
        for sh in wb.sheetnames:
            if sh in NON_DATA:
                continue
            srows = list(wb[sh].iter_rows(values_only=True))
            if not srows:
                continue
            SH = hidx(srows[0])
            if 'club_id' not in SH or 'pos' not in SH:
                continue
            body += f'<h3>{sh}</h3><table><tr><th>tr_id</th><th>#</th><th>Klub</th>'
            for col in ('GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS', 'season_fate'):
                body += f'<th>{col}</th>'
            body += '</tr>'
            for r in srows[1:]:
                if not r:
                    continue
                rt = r[SH.get('row_type', -1)] if 'row_type' in SH else None
                if rt != 'T':
                    continue
                tr_id = r[SH.get('tr_id', -1)] if 'tr_id' in SH else None
                if not tr_id:
                    continue
                body += f'<tr><td class=muted>{tr_id}</td>'
                for col in ('pos', 'club_name'):
                    v = r[SH.get(col, -1)] if col in SH else ''
                    body += f'<td><input type=text name="{col}_{tr_id}" value="{(v or "")}"></td>'
                for col in ('GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS'):
                    v = r[SH.get(col, -1)] if col in SH else ''
                    body += f'<td><input type=number name="{col}_{tr_id}" value="{(v or "")}"></td>'
                v = r[SH.get('season_fate', -1)] if 'season_fate' in SH else ''
                body += f'<td><select name="season_fate_{tr_id}">'
                for o in ['', 'setrval', 'setrval?', 'postup', 'sestup',
                          'zanik', 'slouceni', 'reorganizace']:
                    sel = ' selected' if (v or '') == o else ''
                    body += f'<option{sel}>{o}</option>'
                body += '</select></td></tr>'
            body += '</table>'
        wb.close()
        body += '<br><button>Uložit Standings</button></form></div>'
        return render(f'{sid} Standings', body, sid)

    if tab == 'notes':
        nrows, NH = load_sheet(path, 'NOTES')
        body = nav + f'<h2>{sid} · NOTES</h2>' + tabs
        body += '<table><tr><th>node_id</th><th>sheet</th><th>note_text</th><th>source_type</th></tr>'
        for r in nrows[1:]:
            if not r or all(x is None for x in r):
                continue
            body += '<tr>'
            for col in ('node_id', 'sheet', 'note_text', 'source_type'):
                v = r[NH.get(col, -1)] if col in NH else ''
                body += f'<td>{(v or "")}</td>'
            body += '</tr>'
        body += '</table><p class=muted>(Editace NOTES zatím jen přes Excel.)</p></div>'
        return render(f'{sid} NOTES', body, sid)


@app.route('/s/<sid>/clubs', methods=['POST'])
def save_clubs(sid):
    path = sid_to_path(sid)
    wb = openpyxl.load_workbook(path)
    ws = wb['CLUBS']
    rows = list(ws.iter_rows())
    H = hidx([c.value for c in rows[0]])
    changes = 0
    for row in rows[1:]:
        cid = row[H['club_id']].value
        if not cid:
            continue
        for f in ['clean_name', 'city', 'prev_club_id', 'level', 'change_note']:
            if f not in H:
                continue
            new_v = request.form.get(f'{f}_{cid}')
            if new_v is None:
                continue
            new_v = new_v or None
            if (row[H[f]].value or None) != new_v:
                row[H[f]].value = new_v
                changes += 1
    wb.save(path); wb.close()
    return redirect(url_for('season', sid=sid, _anchor=f'saved-{changes}') + '?tab=clubs')


@app.route('/s/<sid>/standings', methods=['POST'])
def save_standings(sid):
    path = sid_to_path(sid)
    wb = openpyxl.load_workbook(path)
    changes = 0
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        ws = wb[sh]
        rows = list(ws.iter_rows())
        if not rows:
            continue
        SH = hidx([c.value for c in rows[0]])
        if 'tr_id' not in SH:
            continue
        for row in rows[1:]:
            tr_id = row[SH['tr_id']].value
            if not tr_id:
                continue
            for col in ('pos', 'club_name', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS', 'season_fate'):
                if col not in SH:
                    continue
                new_v = request.form.get(f'{col}_{tr_id}')
                if new_v is None:
                    continue
                new_v = new_v or None
                if col in ('GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS') and new_v:
                    try:
                        new_v = int(new_v)
                    except ValueError:
                        pass
                if (row[SH[col]].value or None) != new_v:
                    row[SH[col]].value = new_v
                    changes += 1
    wb.save(path); wb.close()
    return redirect(url_for('season', sid=sid) + '?tab=standings')


@app.route('/search')
def search():
    q = (request.args.get('q') or '').strip().lower()
    if len(q) < 2:
        return render('Hledat', '<p>Zadej alespoň 2 znaky.</p>')
    hits = []
    for sid in discover_seasons():
        rows, H = load_sheet(sid_to_path(sid), 'CLUBS')
        for r in rows[1:]:
            if not r or r[H['club_id']] is None:
                continue
            nm = str(r[H['clean_name']] or '')
            if q in nm.lower():
                hits.append((sid, r[H['club_id']], nm,
                             r[H.get('city', -1)] if 'city' in H else ''))
        if len(hits) > 400:
            break
    body = f'<h2>Výsledky pro „{q}" ({len(hits)})</h2><table>'
    body += '<tr><th>Sezóna</th><th>Klub</th><th>Město</th><th></th></tr>'
    for sid, cid, nm, city in hits[:300]:
        body += (f'<tr><td><a href="/s/{sid}">{sid}</a></td>'
                 f'<td>{nm}</td><td>{city or ""}</td>'
                 f'<td class=muted>{cid}</td></tr>')
    body += '</table>'
    return render(f'Hledat „{q}"', body)


if __name__ == '__main__':
    discover_seasons()
    print(f"=== Editor almanachu ===")
    print(f"  {len(SEASONS)} sezón nalezeno v {DATA}/")
    print(f"  Otevři: http://localhost:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
