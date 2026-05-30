#!/usr/bin/env python3
"""
build_viewer.py — Statický HTML viewer almanachu (Wikipedia-style navigace).

Generuje viewer/:
  index.html                  — všechny sezóny + globální stats + odkazy
  season/{sid}.html           — jedna stránka na sezónu (všechny tabulky, pyramida)
  chain/{chain_id}.html       — historie klubu napříč sezónami
  comp/{comp_chain_id}.html   — historie soutěže napříč sezónami
  search.html                 — vyhledávač klubů (vanilla JS)
  style.css

Otevři viewer/index.html v prohlížeči — žádná instalace.
"""
import sqlite3, os, html, json, re, sys
from collections import defaultdict

DBF = sys.argv[1] if len(sys.argv) > 1 else 'almanach.sqlite'
OUT = 'viewer'

CSS = """*{box-sizing:border-box}
body{font:14px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#222;background:#f7f7f9}
header{background:#1f3a5f;color:#fff;padding:12px 22px;display:flex;align-items:center;gap:18px}
header h1{margin:0;font-size:17px;font-weight:600}
header nav a{color:#cfe0ff;text-decoration:none;margin-right:14px;font-size:14px}
header nav a:hover{color:#fff}
main{max-width:1320px;margin:18px auto;padding:0 18px}
h2{margin:22px 0 6px;font-size:18px;color:#1f3a5f}
h3{margin:14px 0 4px;font-size:14px;color:#345;font-weight:600}
table{border-collapse:collapse;width:100%;background:#fff;margin-bottom:10px;font-size:13px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
th,td{padding:5px 9px;border-bottom:1px solid #eaeaef;text-align:left;vertical-align:top}
th{background:#eef2f7;font-weight:600;color:#234}
tr:hover td{background:#fafafa}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;background:#e7ecf3;color:#345}
.pill.postup{background:#dcf3df;color:#1b5e20}
.pill.sestup{background:#fde0e0;color:#a92020}
.pill.zanik{background:#222;color:#fff}
.pill.slouceni{background:#fff3cd;color:#7c5a00}
.pill.reorg{background:#e1d6f3;color:#4a2a7a}
a{color:#1f3a5f;text-decoration:none}
a:hover{text-decoration:underline}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:6px}
.grid a{padding:8px 10px;background:#fff;border:1px solid #e6e8ee;border-radius:6px;display:block;text-align:center}
.grid a:hover{background:#eef2f7;text-decoration:none}
.muted{color:#888;font-size:12px}
.stat-row{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 22px}
.stat{background:#fff;padding:10px 14px;border-radius:6px;box-shadow:0 1px 2px rgba(0,0,0,.04);min-width:150px}
.stat b{display:block;font-size:20px;color:#1f3a5f}
.stat span{color:#777;font-size:12px}
.nav-prev-next{display:flex;justify-content:space-between;margin:8px 0 18px;font-size:13px}
.nav-prev-next a{padding:4px 10px;background:#eef2f7;border-radius:4px}
footer{padding:24px;color:#888;text-align:center;font-size:12px}
"""

JS_SEARCH = """let D=[];fetch('search_index.json').then(r=>r.json()).then(d=>D=d);
function s(q){const o=document.getElementById('r');if(!q||q.length<2){o.innerHTML='';return}
q=q.toLowerCase();o.innerHTML=D.filter(x=>x.n.toLowerCase().includes(q)).slice(0,300)
.map(x=>`<tr><td><a href="chain/${x.c}.html">${x.n}</a></td><td>${x.city||''}</td>
<td>${x.span}</td><td class=num>${x.ns}</td></tr>`).join('');}"""


def page(title, body, depth=0):
    rel = '../' * depth
    return (f"<!doctype html><meta charset=utf-8><title>{html.escape(str(title or ''))} – Almanach</title>"
            f"<link rel=stylesheet href='{rel}style.css'>"
            f"<header><h1>🏒 Hokejový almanach</h1><nav>"
            f"<a href='{rel}index.html'>Sezóny</a>"
            f"<a href='{rel}search.html'>Hledat klub</a>"
            f"</nav></header><main>{body}</main>"
            f"<footer>Generováno z almanach.sqlite</footer>")


def fate_pill(f):
    if not f:
        return ''
    cls = {'postup': 'postup', 'sestup': 'sestup', 'zanik': 'zanik',
           'slouceni': 'slouceni', 'reorganizace': 'reorg'}.get(f, '')
    return f'<span class="pill {cls}">{html.escape(f)}</span>'


def main():
    if not os.path.exists(DBF):
        print(f"Chybí {DBF}. Spusť: python3 build_db.py")
        return
    for sub in ('season', 'chain', 'comp'):
        os.makedirs(f"{OUT}/{sub}", exist_ok=True)
    db = sqlite3.connect(DBF); db.row_factory = sqlite3.Row; c = db.cursor()
    with open(f"{OUT}/style.css", 'w', encoding='utf-8') as fh:
        fh.write(CSS)

    seasons = c.execute("SELECT season_id, season_label FROM seasons "
                        "ORDER BY season_id").fetchall()
    sid_to_label = {s['season_id']: (s['season_label'] or s['season_id']) for s in seasons}

    # comp chain: spočítej competition_chain_id z prev_node_id
    def safe_id(s):
        return re.sub(r'[^A-Za-z0-9_]', '_', str(s))[:80]

    comp_chain = {}                         # (sid, node_id) -> comp_chain_id
    for sid, label in [(s['season_id'], s['season_label']) for s in seasons]:
        for n in c.execute("SELECT node_id, prev_node_id FROM competitions "
                           "WHERE season_id=?", (sid,)):
            if n['prev_node_id']:
                m = re.search(r'NODE_(S\d{4}_\d{2})_', str(n['prev_node_id']))
                if m and (m.group(1), n['prev_node_id']) in comp_chain:
                    comp_chain[(sid, n['node_id'])] = comp_chain[(m.group(1), n['prev_node_id'])]
                    continue
            comp_chain[(sid, n['node_id'])] = f"COMP_{safe_id(sid)}_{safe_id(n['node_id'])}"

    # ── index ──
    body = '<h2>Přehled</h2><div class="stat-row">'
    for k, v in [
        ('sezón', c.execute("SELECT COUNT(*) FROM seasons").fetchone()[0]),
        ('klubů', c.execute("SELECT COUNT(*) FROM clubs").fetchone()[0]),
        ('řetězů klubů', c.execute("SELECT COUNT(DISTINCT chain_id) FROM clubs").fetchone()[0]),
        ('soutěží', c.execute("SELECT COUNT(*) FROM competitions").fetchone()[0]),
        ('tabulkových řádků', c.execute("SELECT COUNT(*) FROM standings").fetchone()[0]),
    ]:
        body += f'<div class="stat"><b>{v}</b><span>{k}</span></div>'
    body += '</div><h2>Sezóny</h2><div class="grid">'
    for s in seasons:
        body += f'<a href="season/{s["season_id"]}.html">{s["season_label"]}</a>'
    body += '</div><h2>TOP 12 nejdelších řetězů klubů</h2><table>'
    body += '<tr><th>Klub</th><th>Sezón</th><th>Rozsah</th></tr>'
    for r in c.execute("""SELECT chain_id, COUNT(DISTINCT season_id) ns,
        MIN(season_id) s0, MAX(season_id) s1,
        (SELECT clean_name FROM clubs c2 WHERE c2.chain_id=c1.chain_id
         ORDER BY season_id DESC LIMIT 1) nm
        FROM clubs c1 GROUP BY chain_id ORDER BY ns DESC LIMIT 12"""):
        body += (f'<tr><td><a href="chain/{r["chain_id"]}.html">'
                 f'{html.escape(r["nm"] or "")}</a></td>'
                 f'<td class=num>{r["ns"]}</td>'
                 f'<td>{sid_to_label[r["s0"]]} – {sid_to_label[r["s1"]]}</td></tr>')
    body += '</table>'
    with open(f"{OUT}/index.html", 'w', encoding='utf-8') as fh:
        fh.write(page('Přehled', body, 0))

    # ── per-season ──
    for i, s in enumerate(seasons):
        sid = s['season_id']; label = s['season_label']
        prev_link = (f'<a href="{seasons[i-1]["season_id"]}.html">← {seasons[i-1]["season_label"]}</a>'
                     if i > 0 else '<span></span>')
        next_link = (f'<a href="{seasons[i+1]["season_id"]}.html">{seasons[i+1]["season_label"]} →</a>'
                     if i + 1 < len(seasons) else '<span></span>')
        body = f'<h2>{label} <span class=muted>({sid})</span></h2>'
        body += f'<div class="nav-prev-next">{prev_link}{next_link}</div>'
        # pyramida (top-level)
        body += '<h3>Pyramida soutěží</h3><table>'
        body += '<tr><th>Soutěž</th><th>Typ</th><th>Úroveň</th><th>→ příští sezóna</th></tr>'
        for n in c.execute("""SELECT * FROM competitions WHERE season_id=?
                              AND parent_node_id IS NULL ORDER BY level, node_id""", (sid,)):
            ch = comp_chain.get((sid, n['node_id']))
            body += (f'<tr><td><a href="../comp/{ch}.html">{html.escape(n["name"] or "")}</a></td>'
                     f'<td>{n["competition_type"] or ""}</td>'
                     f'<td>{n["level"] or ""}</td>'
                     f'<td class=muted>{n["feeds_into"] or ""}</td></tr>')
        body += '</table>'
        # tabulky
        rows = c.execute("""SELECT s.*, cl.chain_id FROM standings s
                            LEFT JOIN clubs cl ON cl.season_id=s.season_id AND cl.club_id=s.club_id
                            WHERE s.season_id=? ORDER BY s.sheet, s.node_id,
                            CAST(s.pos AS INTEGER), s.club_name""", (sid,)).fetchall()
        nodes = {n['node_id']: n for n in c.execute(
            "SELECT * FROM competitions WHERE season_id=?", (sid,))}
        by_sheet = defaultdict(list)
        for r in rows:
            by_sheet[r['sheet'] or '?'].append(r)
        for sh in sorted(by_sheet):
            body += f'<h3>{html.escape(sh)}</h3>'
            cur_node = None
            for r in by_sheet[sh]:
                if r['node_id'] != cur_node:
                    if cur_node is not None:
                        body += '</table>'
                    cur_node = r['node_id']
                    nn = nodes.get(cur_node)
                    nm = nn['name'] if nn else cur_node
                    body += (f'<b>{html.escape(nm or "")}</b>'
                             '<table><tr><th>#</th><th>Klub</th>'
                             '<th>GP</th><th>W</th><th>D</th><th>L</th>'
                             '<th>GF:GA</th><th>PTS</th><th>Fate</th></tr>')
                ch = r['chain_id']
                club_link = (f'<a href="../chain/{ch}.html">{html.escape(r["club_name"] or "")}</a>'
                             if ch else html.escape(r['club_name'] or ''))
                body += (f'<tr><td>{r["pos"] or ""}</td><td>{club_link}</td>'
                         f'<td class=num>{r["GP"] or ""}</td>'
                         f'<td class=num>{r["W"] or ""}</td>'
                         f'<td class=num>{r["D"] or ""}</td>'
                         f'<td class=num>{r["L"] or ""}</td>'
                         f'<td class=num>{(r["GF"] or "")}:{(r["GA"] or "")}</td>'
                         f'<td class=num>{r["PTS"] or ""}</td>'
                         f'<td>{fate_pill(r["season_fate"])}</td></tr>')
            if cur_node is not None:
                body += '</table>'
        with open(f"{OUT}/season/{sid}.html", 'w', encoding='utf-8') as fh:
            fh.write(page(label, body, 1))

    # ── per-chain (kluby napříč sezónami) ──
    search_idx = []
    for ch in c.execute("SELECT DISTINCT chain_id FROM clubs").fetchall():
        cid = ch['chain_id']
        hist = c.execute("""SELECT season_id, club_id, clean_name, level, city, prev_club_id
                            FROM clubs WHERE chain_id=? ORDER BY season_id""", (cid,)).fetchall()
        if not hist:
            continue
        last = hist[-1]; first = hist[0]
        body = (f'<h2>{html.escape(last["clean_name"] or "")}</h2>'
                f'<p class=muted>{len(hist)} sezón · '
                f'{sid_to_label[first["season_id"]]} – {sid_to_label[last["season_id"]]} · '
                f'město: {html.escape(last["city"] or "?")}</p>')
        body += '<table><tr><th>Sezóna</th><th>Klub</th><th>Úroveň</th><th>Město</th><th>Fate</th></tr>'
        for h in hist:
            ft = c.execute("""SELECT season_fate FROM standings
                              WHERE season_id=? AND club_id=?
                              AND season_fate IS NOT NULL AND season_fate<>''
                              LIMIT 1""", (h['season_id'], h['club_id'])).fetchone()
            ftv = ft['season_fate'] if ft else ''
            body += (f'<tr><td><a href="../season/{h["season_id"]}.html">'
                     f'{sid_to_label[h["season_id"]]}</a></td>'
                     f'<td>{html.escape(h["clean_name"] or "")}</td>'
                     f'<td>{h["level"] or ""}</td>'
                     f'<td>{html.escape(h["city"] or "")}</td>'
                     f'<td>{fate_pill(ftv)}</td></tr>')
        body += '</table>'
        with open(f"{OUT}/chain/{cid}.html", 'w', encoding='utf-8') as fh:
            fh.write(page(last['clean_name'] or cid, body, 1))
        search_idx.append({
            'c': cid, 'n': last['clean_name'] or cid,
            'city': last['city'] or '',
            'span': f"{sid_to_label[first['season_id']]}–{sid_to_label[last['season_id']]}",
            'ns': len(hist),
        })

    # ── per-comp-chain (soutěže napříč sezónami) ──
    chain_seasons = defaultdict(list)
    for (sid, nid), ccid in comp_chain.items():
        chain_seasons[ccid].append((sid, nid))
    for ccid, items in chain_seasons.items():
        items.sort()
        first_sid, first_nid = items[0]
        first_node = c.execute("SELECT * FROM competitions WHERE season_id=? AND node_id=?",
                               (first_sid, first_nid)).fetchone()
        last_sid, last_nid = items[-1]
        last_node = c.execute("SELECT * FROM competitions WHERE season_id=? AND node_id=?",
                              (last_sid, last_nid)).fetchone()
        body = (f'<h2>{html.escape(last_node["name"] or "")}</h2>'
                f'<p class=muted>{len(items)} sezón · '
                f'{sid_to_label[first_sid]} – {sid_to_label[last_sid]} · '
                f'úroveň: {last_node["level"] or ""}</p>')
        body += '<table><tr><th>Sezóna</th><th>Název soutěže</th><th>Typ</th><th>Úroveň</th></tr>'
        for sid, nid in items:
            n = c.execute("SELECT * FROM competitions WHERE season_id=? AND node_id=?",
                          (sid, nid)).fetchone()
            body += (f'<tr><td><a href="../season/{sid}.html">{sid_to_label[sid]}</a></td>'
                     f'<td>{html.escape(n["name"] or "")}</td>'
                     f'<td>{n["competition_type"] or ""}</td>'
                     f'<td>{n["level"] or ""}</td></tr>')
        body += '</table>'
        with open(f"{OUT}/comp/{ccid}.html", 'w', encoding='utf-8') as fh:
            fh.write(page(last_node['name'] or ccid, body, 1))

    # ── search ──
    with open(f"{OUT}/search_index.json", 'w', encoding='utf-8') as fh:
        json.dump(search_idx, fh, ensure_ascii=False)
    body = ('<h2>Hledat klub</h2>'
            '<input id=q type=search placeholder="3+ znaky..." oninput="s(this.value)" autofocus '
            'style="width:100%;padding:9px;font-size:15px;border:1px solid #ccc;border-radius:5px;margin-bottom:10px">'
            '<table><tr><th>Klub</th><th>Město</th><th>Rozsah</th><th>Sezón</th></tr>'
            '<tbody id=r></tbody></table>'
            f'<script>{JS_SEARCH}</script>')
    with open(f"{OUT}/search.html", 'w', encoding='utf-8') as fh:
        fh.write(page('Hledat', body, 0))

    db.close()
    print(f"=== Viewer hotov: {OUT}/index.html ===")
    print(f"  {len(seasons)} sezón, {len(search_idx)} klub-řetězů, "
          f"{len(chain_seasons)} soutěž-řetězů")


if __name__ == '__main__':
    main()
