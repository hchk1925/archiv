#!/usr/bin/env python3
"""
app.py — Almanach: Viewer + Editor v jedné aplikaci.

Čte přímo z data/S*_FINAL.xlsx (XLSX je jediný zdroj pravdy).
Žádná SQLite, žádná instalace — `python3 app.py` a otevři localhost:5000.

Funkce:
  Viewer:
    /                          — seznam sezón + stats
    /s/<sid>                   — sezóna: pyramida + všechny tabulky
    /club/<chain_id>           — běh klubu napříč sezónami
    /comp/<comp_chain_id>      — běh soutěže napříč sezónami
    /search?q=...              — fulltext klubů
  Editor:
    /s/<sid>/edit/clubs        — formulář na CLUBS
    /s/<sid>/edit/standings    — formulář na T-řádky standings

Po uložení se z xlsx přečte ta sezóna znovu a chainy se přepočtou.
"""
import openpyxl, glob, os, re, sys
from collections import defaultdict
from flask import Flask, request, render_template_string, redirect, url_for, abort

DATA = 'data'
NON_DATA = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA', 'TODO'}
B_SUF = re.compile(r'\s+(B|II|III|IV)\s*$')
LEVEL_RE = re.compile(r'L(\d+)')
ORG_PFX = re.compile(
    r'^(TJ|HC|VTJ|ASD|ZTJ|DSO|DŠO|DSJ|ZSJ|Sokol|SK|AC|AFK|SKP|KLH|KS|BK|HO|RH|ČH|VSJ|PDA|DA|VŠ)\.?\s+', re.I)

app = Flask(__name__)
CACHE = {}                                  # sid -> {clubs, system, standings, notes, meta, label}
SEASON_ORDER = []                           # ['1949_50', ...]
CLUB_CHAIN = {}                             # (sid, cid) -> chain_id
CHAIN_HIST = defaultdict(list)              # chain_id -> [(sid, cid)] sorted
NODE_CHAIN = {}                             # (sid, node_id) -> comp_chain_id
COMP_HIST = defaultdict(list)               # comp_chain_id -> [(sid, node_id)]


# ─────────── Data loading ───────────
def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def cell(r, H, name):
    i = H.get(name)
    return r[i] if i is not None and i < len(r) else None


def lvl(v):
    if v is None: return None
    m = LEVEL_RE.search(str(v))
    return int(m.group(1)) if m else None


def core_name(name):
    if not name: return ''
    s = str(name).strip()
    s = re.sub(r'\s*\([^)]*\)\s*', ' ', s)
    prev = None
    while prev != s:
        prev = s; s = ORG_PFX.sub('', s).strip()
    s = B_SUF.sub('', s).strip()
    return re.sub(r'\s+', ' ', s).strip().lower()


def safe_id(s):
    return re.sub(r'[^A-Za-z0-9_]', '_', str(s))[:80]


def load_season(sid):
    """Načti jednu sezónu z xlsx do paměťové struktury."""
    path = os.path.join(DATA, f'S{sid}_FINAL.xlsx')
    if not os.path.exists(path):
        return None
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {'clubs': [], 'system': [], 'standings': defaultdict(list),
           'notes': [], 'meta': {}, 'label': sid.replace('_', '/')}
    # META
    if 'META' in wb.sheetnames:
        for r in wb['META'].iter_rows(values_only=True):
            if r and r[0]:
                out['meta'][str(r[0])] = r[1]
        if 'season_label' in out['meta'] and out['meta']['season_label']:
            out['label'] = out['meta']['season_label']
    # CLUBS
    ws = wb['CLUBS']; rr = list(ws.iter_rows(values_only=True))
    H = hidx(rr[0])
    for r in rr[1:]:
        if not r or cell(r, H, 'club_id') is None: continue
        out['clubs'].append({
            'club_id': cell(r, H, 'club_id'),
            'clean_name': cell(r, H, 'clean_name') or '',
            'raw_name': cell(r, H, 'raw_name') or '',
            'sheet': cell(r, H, 'sheet') or '',
            'level': cell(r, H, 'level') or '',
            'district': cell(r, H, 'district') or '',
            'prev_club_id': cell(r, H, 'prev_club_id'),
            'change_note': cell(r, H, 'change_note') or '',
            'city': cell(r, H, 'city') or '',
        })
    # SYSTEM
    if 'SYSTEM' in wb.sheetnames:
        rs = list(wb['SYSTEM'].iter_rows(values_only=True))
        SH = hidx(rs[0])
        for r in rs[1:]:
            if not r or cell(r, SH, 'node_id') is None: continue
            out['system'].append({
                'node_id': cell(r, SH, 'node_id'),
                'name': cell(r, SH, 'name') or '',
                'competition_type': cell(r, SH, 'competition_type') or '',
                'level': cell(r, SH, 'level') or '',
                'parent_node_id': cell(r, SH, 'parent_node_id'),
                'feeds_into': cell(r, SH, 'feeds_into'),
                'feeds_into_loser': cell(r, SH, 'feeds_into_loser'),
                'prev_node_id': cell(r, SH, 'prev_node_id'),
                'note': cell(r, SH, 'note') or '',
            })
    # NOTES
    if 'NOTES' in wb.sheetnames:
        rn = list(wb['NOTES'].iter_rows(values_only=True))
        if rn:
            NH = hidx(rn[0])
            for r in rn[1:]:
                if not r or all(x is None for x in r): continue
                out['notes'].append({
                    'node_id': cell(r, NH, 'node_id') or '',
                    'sheet': cell(r, NH, 'sheet') or '',
                    'note_text': cell(r, NH, 'note_text') or '',
                    'source_type': cell(r, NH, 'source_type') or '',
                })
    # standings (T) + registrations (R) per data sheet
    for sh in wb.sheetnames:
        if sh in NON_DATA: continue
        rs = list(wb[sh].iter_rows(values_only=True))
        if not rs: continue
        DH = hidx(rs[0])
        if 'club_id' not in DH or 'row_type' not in DH: continue
        for r in rs[1:]:
            if not r: continue
            rt = cell(r, DH, 'row_type')
            if rt not in ('T', 'R'): continue
            out['standings'][sh].append({
                'row_type': rt,
                'tr_id': cell(r, DH, 'tr_id'),
                'club_id': cell(r, DH, 'club_id'),
                'club_name': cell(r, DH, 'club_name') or '',
                'pos': cell(r, DH, 'pos'),
                'GP': cell(r, DH, 'GP'),
                'W': cell(r, DH, 'W'),
                'D': cell(r, DH, 'D'),
                'L': cell(r, DH, 'L'),
                'GF': cell(r, DH, 'GF'),
                'GA': cell(r, DH, 'GA'),
                'PTS': cell(r, DH, 'PTS'),
                'node_id': cell(r, DH, 'node_id'),
                'level': cell(r, DH, 'level'),
                'season_fate': cell(r, DH, 'season_fate'),
                'prev_club_id': cell(r, DH, 'prev_club_id'),
            })
    wb.close()
    return out


def load_all():
    global SEASON_ORDER
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    SEASON_ORDER = [re.search(r'S(\d{4}_\d{2})', os.path.basename(p)).group(1)
                    for p in files]
    print(f"Loading {len(SEASON_ORDER)} sezón…")
    for sid in SEASON_ORDER:
        CACHE[sid] = load_season(sid)
    compute_chains()
    print(f"  hotovo: {len(SEASON_ORDER)} sezón, "
          f"{len(CHAIN_HIST)} klub-řetězů, {len(COMP_HIST)} soutěž-řetězů")


def compute_chains():
    """Spočítej chain_id pro kluby (přes primary successor) + comp_chain_id."""
    global CLUB_CHAIN, CHAIN_HIST, NODE_CHAIN, COMP_HIST
    CLUB_CHAIN = {}; CHAIN_HIST.clear()
    NODE_CHAIN = {}; COMP_HIST.clear()

    # valid (sid, cid) set
    valid = set()
    info = {}
    for sid in SEASON_ORDER:
        if not CACHE.get(sid): continue
        for c in CACHE[sid]['clubs']:
            key = (sid, c['club_id'])
            valid.add(key)
            info[key] = {'name': c['clean_name'], 'prev': c['prev_club_id'],
                         'lvl': lvl(c['level']) or 9999}

    def prev_key(key):
        p = info[key]['prev']
        if not p: return None
        m = re.search(r'CLUB_(S\d{4}_\d{2})_', str(p))
        ps = m.group(1)[1:] if m else None        # strip leading S → '1949_50'
        return (ps, p) if ps and (ps, p) in valid else None

    children = defaultdict(list)
    for key in valid:
        pk = prev_key(key)
        if pk: children[pk].append(key)

    primary = {}
    for pk, kids in children.items():
        non_b = [k for k in kids if not B_SUF.search(info[k]['name'])]
        pool = non_b or kids
        pool.sort(key=lambda k: (info[k]['lvl'], k[1]))
        primary[pk] = pool[0]

    for sid in SEASON_ORDER:
        if not CACHE.get(sid): continue
        for c in CACHE[sid]['clubs']:
            key = (sid, c['club_id'])
            pk = prev_key(key)
            if pk and pk in CLUB_CHAIN and primary.get(pk) == key:
                cid = CLUB_CHAIN[pk]
            else:
                cid = f"CHAIN_{c['club_id']}"
            CLUB_CHAIN[key] = cid
            CHAIN_HIST[cid].append(key)

    # comp chains přes prev_node_id
    for sid in SEASON_ORDER:
        if not CACHE.get(sid): continue
        for n in CACHE[sid]['system']:
            key = (sid, n['node_id'])
            pn = n['prev_node_id']
            if pn:
                m = re.search(r'NODE_(S\d{4}_\d{2})_', str(pn))
                ps = m.group(1)[1:] if m else None
                pkey = (ps, pn) if ps else None
                if pkey and pkey in NODE_CHAIN:
                    NODE_CHAIN[key] = NODE_CHAIN[pkey]
                    COMP_HIST[NODE_CHAIN[key]].append(key)
                    continue
            ccid = f"COMP_{safe_id(sid)}_{safe_id(n['node_id'])}"
            NODE_CHAIN[key] = ccid
            COMP_HIST[ccid].append(key)


def reload_season(sid):
    CACHE[sid] = load_season(sid)
    compute_chains()


def get_club(sid, cid):
    if sid not in CACHE: return None
    for c in CACHE[sid]['clubs']:
        if c['club_id'] == cid: return c
    return None


def get_node(sid, nid):
    if sid not in CACHE: return None
    for n in CACHE[sid]['system']:
        if n['node_id'] == nid: return n
    return None


# ─────────── UI templates ───────────
LAYOUT = """<!doctype html>
<html><head>
<meta charset=utf-8>
<title>{{title}} · Almanach</title>
<style>
*{box-sizing:border-box}
body{font:14px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#222;background:#f6f7fa}
header{background:#1a3050;color:#fff;padding:10px 18px;display:flex;gap:16px;align-items:center;position:sticky;top:0;z-index:100}
header a.brand{font-size:16px;font-weight:600;color:#fff;text-decoration:none}
header a{color:#cfe0ff;text-decoration:none}
header a:hover{color:#fff}
header form{margin-left:auto;display:flex;gap:4px}
header input{padding:5px 9px;border:0;border-radius:3px;width:240px;font:inherit}
header button{padding:5px 10px;background:#2d4868;color:#fff;border:0;border-radius:3px;cursor:pointer}
main{max-width:1380px;margin:14px auto;padding:0 16px}
h2{margin:18px 0 6px;font-size:19px;color:#1a3050}
h3{margin:14px 0 4px;font-size:14px;color:#345;font-weight:600}
table{border-collapse:collapse;width:100%;background:#fff;margin:4px 0 10px;font-size:13px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
th,td{padding:4px 9px;border-bottom:1px solid #eaeaef;text-align:left;vertical-align:top}
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
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:5px}
.grid a{padding:7px;background:#fff;border:1px solid #dde2eb;border-radius:4px;text-align:center;font-size:13px}
.grid a:hover{background:#eef2f7;text-decoration:none}
.muted{color:#888;font-size:12px}
.stat-row{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 22px}
.stat{background:#fff;padding:10px 14px;border-radius:6px;box-shadow:0 1px 2px rgba(0,0,0,.04);min-width:140px}
.stat b{display:block;font-size:20px;color:#1a3050}
.stat span{color:#777;font-size:12px}
.nav-prev-next{display:flex;justify-content:space-between;margin:6px 0 16px;font-size:13px;gap:6px}
.nav-prev-next a{padding:5px 10px;background:#eef2f7;border-radius:4px;flex:1;text-align:center}
.nav-prev-next a:hover{background:#dde6f0}
.tab-bar{display:flex;gap:2px;margin:10px 0 0;border-bottom:2px solid #1a3050}
.tab-bar a{padding:6px 14px;background:#dde2eb;color:#234;border-radius:4px 4px 0 0;font-weight:600}
.tab-bar a.active{background:#1a3050;color:#fff}
.tab-bar a:hover{text-decoration:none}
.tab-body{background:#fff;padding:14px;border-radius:0 4px 4px 4px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
input[type=text],textarea,select{width:100%;padding:3px 6px;border:1px solid #ccc;border-radius:3px;font:inherit}
textarea{min-height:40px;font-size:12px;font-family:inherit}
input[type=number]{width:60px;padding:3px 5px;border:1px solid #ccc;border-radius:3px;font:inherit}
.save-bar{position:sticky;bottom:0;background:#fff;padding:10px 14px;margin:14px -14px -14px;border-top:1px solid #ddd;box-shadow:0 -2px 4px rgba(0,0,0,.04)}
.save-bar button{padding:8px 18px;background:#1a3050;color:#fff;border:0;border-radius:4px;cursor:pointer;font-weight:600;font-size:14px}
.save-bar button:hover{background:#2d4868}
.flash{background:#dcf3df;color:#1b5e20;padding:8px 14px;border-radius:4px;margin:8px 0}
.edit-link{float:right;font-size:12px;background:#1a3050;color:#fff;padding:3px 10px;border-radius:3px}
.edit-link:hover{background:#2d4868;color:#fff;text-decoration:none}
footer{padding:18px;color:#888;text-align:center;font-size:11px}
</style></head><body>
<header>
<a href="/" class=brand>🏒 Almanach</a>
{% if sid %}<span class=muted>· {{sid.replace('_','/')}}</span>{% endif %}
<form action="/search"><input name=q placeholder="hledat klub (3+)" value="{{request.args.get('q','')}}"><button>→</button></form>
</header>
<main>
{% if flash %}<div class=flash>{{flash}}</div>{% endif %}
{{body|safe}}
</main>
<footer>Čte z data/S*_FINAL.xlsx · spuštěno z app.py</footer>
</body></html>
"""


def render(title, body, sid=None, flash=None):
    return render_template_string(LAYOUT, title=title, body=body, sid=sid, flash=flash)


def fate_pill(f):
    if not f: return ''
    import html as h
    cls = {'postup': 'postup', 'sestup': 'sestup', 'zanik': 'zanik',
           'slouceni': 'slouceni', 'reorganizace': 'reorg'}.get(f, '')
    return f'<span class="pill {cls}">{h.escape(str(f))}</span>'


def esc(s):
    import html as h
    return h.escape(str(s or ''))


# ─────────── Routes ───────────
@app.route('/')
def index():
    body = '<h2>Přehled</h2><div class=stat-row>'
    for k, v in [
        ('sezón', len(SEASON_ORDER)),
        ('klubů', sum(len(CACHE[s]['clubs']) for s in SEASON_ORDER if CACHE.get(s))),
        ('řetězů klubů', len(CHAIN_HIST)),
        ('soutěží', sum(len(CACHE[s]['system']) for s in SEASON_ORDER if CACHE.get(s))),
        ('soutěž-řetězů', len(COMP_HIST)),
    ]:
        body += f'<div class=stat><b>{v}</b><span>{k}</span></div>'
    body += '</div><h2>Sezóny</h2><div class=grid>'
    for sid in SEASON_ORDER:
        label = CACHE[sid]['label'] if CACHE.get(sid) else sid
        body += f'<a href="/s/{sid}">{esc(label)}</a>'
    body += '</div>'
    # nejdelší klub-řetězy
    longest = sorted(CHAIN_HIST.items(), key=lambda x: -len(x[1]))[:12]
    body += '<h2>Nejdelší řetězy klubů</h2><table>'
    body += '<tr><th>Klub (poslední název)</th><th>Sezón</th><th>Rozsah</th></tr>'
    for ccid, hist in longest:
        last_sid, last_cid = hist[-1]; first_sid = hist[0][0]
        last = get_club(last_sid, last_cid)
        if not last: continue
        body += (f'<tr><td><a href="/club/{ccid}">{esc(last["clean_name"])}</a></td>'
                 f'<td class=num>{len(hist)}</td>'
                 f'<td>{first_sid.replace("_","/")}–{last_sid.replace("_","/")}</td></tr>')
    body += '</table>'
    return render('Přehled', body)


@app.route('/s/<sid>')
def season(sid):
    if sid not in CACHE or not CACHE[sid]: abort(404)
    d = CACHE[sid]
    i = SEASON_ORDER.index(sid)
    prev_a = (f'<a href="/s/{SEASON_ORDER[i-1]}">← {SEASON_ORDER[i-1].replace("_","/")}</a>'
              if i > 0 else '<span></span>')
    next_a = (f'<a href="/s/{SEASON_ORDER[i+1]}">{SEASON_ORDER[i+1].replace("_","/")} →</a>'
              if i + 1 < len(SEASON_ORDER) else '<span></span>')
    body = (f'<h2>Sezóna {esc(d["label"])} '
            f'<a href="/s/{sid}/edit/clubs" class=edit-link>✎ editovat</a></h2>'
            f'<div class=nav-prev-next>{prev_a}<a href="/">přehled</a>{next_a}</div>')
    # pyramida (top-level)
    body += '<h3>Pyramida soutěží</h3><table>'
    body += '<tr><th>Soutěž</th><th>Typ</th><th>Úroveň</th><th>feeds_into</th></tr>'
    for n in sorted([x for x in d['system'] if not x['parent_node_id']],
                    key=lambda x: (str(x['level']), x['node_id'])):
        ccid = NODE_CHAIN.get((sid, n['node_id']))
        comp_link = f'<a href="/comp/{ccid}">{esc(n["name"])}</a>' if ccid else esc(n['name'])
        body += (f'<tr><td>{comp_link}</td>'
                 f'<td>{esc(n["competition_type"])}</td>'
                 f'<td>{esc(n["level"])}</td>'
                 f'<td class=muted>{esc(n["feeds_into"] or "")}</td></tr>')
    body += '</table>'
    # tabulky podle sheet
    nodes = {n['node_id']: n for n in d['system']}
    for sh in sorted(d['standings'].keys()):
        body += f'<h3>{esc(sh)}</h3>'
        cur_node = None
        for r in d['standings'][sh]:
            if r['row_type'] != 'T': continue
            if r['node_id'] != cur_node:
                if cur_node is not None: body += '</table>'
                cur_node = r['node_id']
                nn = nodes.get(cur_node)
                nm = nn['name'] if nn else cur_node
                ccid = NODE_CHAIN.get((sid, cur_node))
                title = (f'<a href="/comp/{ccid}">{esc(nm)}</a>' if ccid else esc(nm))
                body += (f'<b>{title}</b>'
                         '<table><tr><th>#</th><th>Klub</th>'
                         '<th>GP</th><th>W</th><th>D</th><th>L</th>'
                         '<th>GF:GA</th><th>PTS</th><th>Fate</th></tr>')
            ch = CLUB_CHAIN.get((sid, r['club_id']))
            cl = (f'<a href="/club/{ch}">{esc(r["club_name"])}</a>' if ch
                  else esc(r['club_name']))
            body += (f'<tr><td>{r["pos"] or ""}</td><td>{cl}</td>'
                     f'<td class=num>{r["GP"] or ""}</td>'
                     f'<td class=num>{r["W"] or ""}</td>'
                     f'<td class=num>{r["D"] or ""}</td>'
                     f'<td class=num>{r["L"] or ""}</td>'
                     f'<td class=num>{(r["GF"] or "")}:{(r["GA"] or "")}</td>'
                     f'<td class=num>{r["PTS"] or ""}</td>'
                     f'<td>{fate_pill(r["season_fate"])}</td></tr>')
        if cur_node is not None: body += '</table>'
    return render(d['label'], body, sid)


@app.route('/club/<chain_id>')
def club_chain(chain_id):
    hist = CHAIN_HIST.get(chain_id)
    if not hist: abort(404)
    hist = sorted(hist)
    last_sid, last_cid = hist[-1]; first_sid = hist[0][0]
    last = get_club(last_sid, last_cid)
    body = (f'<h2>{esc(last["clean_name"])}</h2>'
            f'<p class=muted>{len(hist)} sezón · '
            f'{first_sid.replace("_","/")} – {last_sid.replace("_","/")} · '
            f'město: {esc(last["city"])}</p>')
    body += '<table><tr><th>Sezóna</th><th>Klub</th><th>Úroveň</th><th>Město</th><th>Fate</th><th>club_id</th></tr>'
    for sid, cid in hist:
        c = get_club(sid, cid)
        if not c: continue
        ft = ''
        for sh in CACHE[sid]['standings'].values():
            for r in sh:
                if r['club_id'] == cid and r['season_fate']:
                    ft = r['season_fate']; break
            if ft: break
        body += (f'<tr><td><a href="/s/{sid}">{sid.replace("_","/")}</a></td>'
                 f'<td>{esc(c["clean_name"])}</td>'
                 f'<td>{esc(c["level"])}</td>'
                 f'<td>{esc(c["city"])}</td>'
                 f'<td>{fate_pill(ft)}</td>'
                 f'<td class=muted>{cid}</td></tr>')
    body += '</table>'
    if last.get('change_note'):
        body += f'<h3>change_note (poslední)</h3><div style="background:#fff;padding:10px;border-radius:4px;font-size:12px">{esc(last["change_note"])}</div>'
    return render(last['clean_name'] or chain_id, body)


@app.route('/comp/<comp_chain_id>')
def comp_chain(comp_chain_id):
    items = COMP_HIST.get(comp_chain_id)
    if not items: abort(404)
    items = sorted(items)
    last_sid, last_nid = items[-1]; first_sid = items[0][0]
    last = get_node(last_sid, last_nid)
    body = (f'<h2>{esc(last["name"])}</h2>'
            f'<p class=muted>{len(items)} sezón · '
            f'{first_sid.replace("_","/")} – {last_sid.replace("_","/")} · '
            f'úroveň: {esc(last["level"])}</p>')
    body += '<table><tr><th>Sezóna</th><th>Název</th><th>Typ</th><th>Úroveň</th></tr>'
    for sid, nid in items:
        n = get_node(sid, nid)
        if not n: continue
        body += (f'<tr><td><a href="/s/{sid}">{sid.replace("_","/")}</a></td>'
                 f'<td>{esc(n["name"])}</td>'
                 f'<td>{esc(n["competition_type"])}</td>'
                 f'<td>{esc(n["level"])}</td></tr>')
    body += '</table>'
    return render(last['name'] or comp_chain_id, body)


@app.route('/search')
def search():
    q = (request.args.get('q') or '').strip().lower()
    if len(q) < 2:
        return render('Hledat', '<p>Zadej alespoň 2 znaky.</p>')
    hits = []
    seen_chains = set()
    for sid in SEASON_ORDER:
        if not CACHE.get(sid): continue
        for c in CACHE[sid]['clubs']:
            if q in c['clean_name'].lower():
                ch = CLUB_CHAIN.get((sid, c['club_id']))
                if ch and ch not in seen_chains:
                    seen_chains.add(ch)
                    hits.append((ch, c, sid))
                    if len(hits) > 400: break
        if len(hits) > 400: break
    body = f'<h2>Výsledky pro „{esc(q)}" ({len(hits)})</h2>'
    body += '<table><tr><th>Klub</th><th>Město</th><th>Sezóna</th></tr>'
    for ch, c, sid in hits[:300]:
        body += (f'<tr><td><a href="/club/{ch}">{esc(c["clean_name"])}</a></td>'
                 f'<td>{esc(c["city"])}</td>'
                 f'<td><a href="/s/{sid}">{sid.replace("_","/")}</a></td></tr>')
    body += '</table>'
    return render(f'Hledat „{q}"', body)


# ── Editor ──
@app.route('/s/<sid>/edit/clubs', methods=['GET', 'POST'])
def edit_clubs(sid):
    if sid not in CACHE: abort(404)
    path = os.path.join(DATA, f'S{sid}_FINAL.xlsx')
    if request.method == 'POST':
        wb = openpyxl.load_workbook(path)
        ws = wb['CLUBS']
        rows = list(ws.iter_rows())
        H = hidx([c.value for c in rows[0]])
        changes = 0
        for row in rows[1:]:
            cid = row[H['club_id']].value
            if not cid: continue
            for f in ('clean_name', 'city', 'prev_club_id', 'level',
                      'district', 'change_note'):
                if f not in H: continue
                new_v = request.form.get(f'{f}_{cid}')
                if new_v is None: continue
                new_v = new_v.strip() or None
                old_v = row[H[f]].value
                if (old_v or None) != new_v:
                    row[H[f]].value = new_v
                    changes += 1
        wb.save(path); wb.close()
        reload_season(sid)
        return redirect(url_for('edit_clubs', sid=sid, saved=changes))
    saved = request.args.get('saved')
    flash = f'Uloženo, {saved} změn.' if saved else None
    d = CACHE[sid]
    body = (f'<h2>Sezóna {esc(d["label"])} · editace CLUBS</h2>'
            f'<div class=tab-bar>'
            f'<a class=active>CLUBS ({len(d["clubs"])})</a>'
            f'<a href="/s/{sid}/edit/standings">Standings</a>'
            f'<a href="/s/{sid}">← zpět na pohled</a>'
            f'</div><div class=tab-body><form method=POST>'
            f'<table><tr><th>club_id</th><th>clean_name</th><th>city</th>'
            f'<th>level</th><th>prev_club_id</th><th>change_note</th></tr>')
    for c in d['clubs']:
        cid = c['club_id']
        body += f'<tr><td class=muted>{cid}</td>'
        for f in ('clean_name', 'city', 'level', 'prev_club_id'):
            body += f'<td><input name="{f}_{cid}" value="{esc(c[f])}"></td>'
        body += f'<td><textarea name="change_note_{cid}">{esc(c["change_note"])}</textarea></td></tr>'
    body += '</table><div class=save-bar><button>Uložit CLUBS</button></div></form></div>'
    return render(f'{sid} CLUBS edit', body, sid, flash)


@app.route('/s/<sid>/edit/standings', methods=['GET', 'POST'])
def edit_standings(sid):
    if sid not in CACHE: abort(404)
    path = os.path.join(DATA, f'S{sid}_FINAL.xlsx')
    if request.method == 'POST':
        wb = openpyxl.load_workbook(path)
        changes = 0
        for shn in wb.sheetnames:
            if shn in NON_DATA: continue
            ws = wb[shn]
            rows = list(ws.iter_rows())
            if not rows: continue
            SH = hidx([c.value for c in rows[0]])
            if 'tr_id' not in SH: continue
            for row in rows[1:]:
                tr_id = row[SH['tr_id']].value
                if not tr_id: continue
                for col in ('pos', 'club_name', 'GP', 'W', 'D', 'L', 'GF', 'GA',
                            'PTS', 'season_fate'):
                    if col not in SH: continue
                    new_v = request.form.get(f'{col}_{tr_id}')
                    if new_v is None: continue
                    new_v = new_v.strip() or None
                    if col in ('GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS') and new_v:
                        try: new_v = int(new_v)
                        except ValueError: pass
                    if (row[SH[col]].value or None) != new_v:
                        row[SH[col]].value = new_v
                        changes += 1
        wb.save(path); wb.close()
        reload_season(sid)
        return redirect(url_for('edit_standings', sid=sid, saved=changes))
    saved = request.args.get('saved')
    flash = f'Uloženo, {saved} změn.' if saved else None
    d = CACHE[sid]
    body = (f'<h2>Sezóna {esc(d["label"])} · editace Standings</h2>'
            f'<div class=tab-bar>'
            f'<a href="/s/{sid}/edit/clubs">CLUBS</a>'
            f'<a class=active>Standings</a>'
            f'<a href="/s/{sid}">← zpět na pohled</a>'
            f'</div><div class=tab-body><form method=POST>')
    for shn in sorted(d['standings'].keys()):
        rows = [r for r in d['standings'][shn] if r['row_type'] == 'T']
        if not rows: continue
        body += f'<h3>{esc(shn)}</h3><table><tr><th>tr_id</th><th>#</th><th>Klub</th>'
        for c in ('GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS'): body += f'<th>{c}</th>'
        body += '<th>Fate</th></tr>'
        for r in rows:
            tr = r['tr_id']
            if not tr: continue
            body += f'<tr><td class=muted>{tr}</td>'
            body += f'<td style="width:50px"><input name="pos_{tr}" value="{r["pos"] or ""}"></td>'
            body += f'<td><input name="club_name_{tr}" value="{esc(r["club_name"])}"></td>'
            for c in ('GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS'):
                body += f'<td><input type=number name="{c}_{tr}" value="{r[c] if r[c] is not None else ""}"></td>'
            body += f'<td><select name="season_fate_{tr}">'
            for o in ('', 'setrval', 'setrval?', 'postup', 'sestup', 'zanik',
                      'slouceni', 'reorganizace'):
                sel = ' selected' if (r['season_fate'] or '') == o else ''
                body += f'<option{sel}>{o}</option>'
            body += '</select></td></tr>'
        body += '</table>'
    body += '<div class=save-bar><button>Uložit Standings</button></div></form></div>'
    return render(f'{sid} Standings edit', body, sid, flash)


if __name__ == '__main__':
    load_all()
    print(f"\n  → otevři: http://localhost:5000\n")
    app.run(host='127.0.0.1', port=5000, debug=False)
