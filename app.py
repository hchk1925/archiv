#!/usr/bin/env python3
"""
app.py — Almanach: vše v jednom (korektor · viewer · builder · printer).

Čte/zapisuje přímo do data/S*_FINAL.xlsx (XLSX je jediný zdroj pravdy).

  python app.py            web: viewer + korektor + audit (localhost:5000)
  python app.py build      xlsx → almanach.sqlite + CSV
  python app.py pdf  all   audit worklist → docs/audit_pdf/   (Garamond)
  python app.py html all   audit worklist → docs/audit_html/
  python app.py xlsx all   audit worklist → docs/Audit_export.xlsx

Web:
  Viewer:   /  ·  /s/<sid>  ·  /club/<chain>  ·  /comp/<chain>  ·  /search
  Korektor: /s/<sid>/edit/clubs  ·  /s/<sid>/edit/standings
  Audit:    /audit  ·  /s/<sid>/audit  (komentář „co chybí" + řešení → xlsx)
            /s/<sid>/audit.pdf  (tisk pro ruční zpracování)

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
           'notes': [], 'todo': [], 'meta': {}, 'label': sid.replace('_', '/')}
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
    # TODO (audit worklist)
    if 'TODO' in wb.sheetnames:
        rt = list(wb['TODO'].iter_rows(values_only=True))
        if rt:
            TH = hidx(rt[0])
            for r in rt[1:]:
                if not r or all(x is None for x in r): continue
                popis = cell(r, TH, 'popis')
                if popis is None: continue
                out['todo'].append({
                    'num': cell(r, TH, '#'),
                    'typ': cell(r, TH, 'typ') or '',
                    'reference': cell(r, TH, 'reference') or '',
                    'popis': popis or '',
                    'done': cell(r, TH, 'vyřešeno? (ANO/ne)') or '',
                    'poznamka': cell(r, TH, 'poznámka kolegy') or '',
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


def list_season_ids():
    """Seřazený seznam sezón ('1947_48', …) ze složky data/ (bez načítání)."""
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    return [re.search(r'S(\d{4}_\d{2})', os.path.basename(p)).group(1)
            for p in files]


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
.note-callout{background:#fff7e0;border-left:4px solid #f0a500;padding:6px 10px;margin:0 0 8px;font-size:12.5px;border-radius:0 4px 4px 0}
.note-callout.torzo{background:#ffe9d6;border-left-color:#d97706}
.note-callout.done{background:#e4f5e7;border-left-color:#3a9d4f}
.note-callout.done .tag{color:#1b7a32}
.note-callout .tag{display:inline-block;font-weight:700;color:#b45309;margin-right:6px;text-transform:uppercase;font-size:11px;letter-spacing:.04em}
.audit-link{background:#d97706;color:#fff;padding:3px 10px;border-radius:3px;font-size:12px;margin-left:6px}
.audit-link:hover{background:#b45309;color:#fff;text-decoration:none}
.audit-item{background:#fff;border:1px solid #e2d2bd;border-left:4px solid #d97706;border-radius:4px;padding:10px 12px;margin:8px 0}
.audit-item.done{border-left-color:#3a9d4f;opacity:.72}
.audit-item h4{margin:0 0 3px;font-size:13.5px;color:#234}
.audit-item .ref{color:#666;font-size:12px}
.audit-item form{display:flex;gap:8px;align-items:flex-end;margin-top:7px;flex-wrap:wrap}
.audit-item .fcol{display:flex;flex-direction:column;gap:2px}
.audit-item label{font-size:11px;color:#777}
.audit-item select{width:150px}.audit-item textarea{min-width:280px;min-height:30px}
.audit-item button{padding:6px 14px;background:#d97706;color:#fff;border:0;border-radius:4px;cursor:pointer;font-weight:600}
.audit-item button:hover{background:#b45309}
.badge-open{background:#d97706;color:#fff;border-radius:10px;padding:1px 8px;font-size:11px}
.print-link{background:#444;color:#fff;padding:3px 10px;border-radius:3px;font-size:12px;margin-left:6px}
.print-link:hover{background:#222;color:#fff;text-decoration:none}
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
    # audit poznámky podle node_id (co chybí)
    audit_by_node = defaultdict(list)
    for nt in d['notes']:
        txt = nt['note_text']
        if nt['node_id'] and (nt['source_type'] == 'TODO-auto'
                              or str(txt).startswith('[TBD]')):
            audit_by_node[nt['node_id']].append(txt)
    # uzly už vyřešené v auditu (TODO vyřešeno=ANO) → callout zezelená
    resolved_nodes = set()
    for t in d['todo']:
        if str(t['done']).strip().upper() == 'ANO':
            m = re.search(r'NODE_S\d{4}_\d{2}_\d+', str(t['reference']))
            if m:
                resolved_nodes.add(m.group(0))
    n_open = sum(1 for t in d['todo']
                 if str(t['done']).strip().upper() != 'ANO')
    audit_btn = (f'<a href="/s/{sid}/audit" class=audit-link>⚑ audit'
                 + (f' <span class=badge-open>{n_open}</span>' if n_open else '')
                 + '</a>')
    body = (f'<h2>Sezóna {esc(d["label"])} '
            f'<a href="/s/{sid}/edit/clubs" class=edit-link>✎ editovat</a>{audit_btn}'
            f'<a href="/s/{sid}/full.pdf" class=print-link>🖶 PDF plný</a>'
            f'<a href="/s/{sid}/audit.pdf" class=print-link>🖶 PDF audit</a></h2>'
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
                body += f'<b>{title}</b>'
                done = cur_node in resolved_nodes
                for txt in audit_by_node.get(cur_node, []):
                    t = str(txt).replace('[TBD] ', '').replace('  [torzo-audit]', '')
                    is_torzo = 'torzo' in t[:12].lower()
                    tag, rest = (t.split(':', 1) + [''])[:2] if ':' in t else ('chybí', t)
                    if done:
                        cls = ' done'; tag = '✓ vyřešeno'
                    else:
                        cls = ' torzo' if is_torzo else ''
                    body += (f'<div class="note-callout{cls}">'
                             f'<span class=tag>{esc(tag.strip())}</span>'
                             f'{esc(rest.strip() or t)}</div>')
                body += ('<table><tr><th>#</th><th>Klub</th>'
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


# ─────────── Audit ───────────
VARIANTY = ['', 'OK – legitimní fáze', 'doplnit týmy', 'sloučit', 'smazat',
            'opravit (level/region/název)', 'neúplné – nech co je']
TODO_HDR = ['#', 'typ', 'reference', 'popis', 'vyřešeno? (ANO/ne)',
            'poznámka kolegy']


def node_rows(d):
    """node_id -> [T-řádky] napříč listy."""
    by = defaultdict(list)
    for sh, rows in d['standings'].items():
        for r in rows:
            if r['row_type'] == 'T' and r['node_id']:
                by[r['node_id']].append(r)
    return by


def clean_popis(txt):
    return (str(txt).replace('[TBD] ', '')
            .replace('  [torzo-audit]', '').replace('[torzo-audit]', '').strip())


@app.route('/s/<sid>/audit')
def audit(sid):
    if sid not in CACHE or not CACHE[sid]: abort(404)
    d = CACHE[sid]
    i = SEASON_ORDER.index(sid)
    prev_a = (f'<a href="/s/{SEASON_ORDER[i-1]}/audit">← {SEASON_ORDER[i-1].replace("_","/")}</a>'
              if i > 0 else '<span></span>')
    next_a = (f'<a href="/s/{SEASON_ORDER[i+1]}/audit">{SEASON_ORDER[i+1].replace("_","/")} →</a>'
              if i + 1 < len(SEASON_ORDER) else '<span></span>')
    nrows = node_rows(d)
    items = d['todo']
    op = [t for t in items if str(t['done']).strip().upper() != 'ANO']
    dn = [t for t in items if str(t['done']).strip().upper() == 'ANO']
    flash = ('Uloženo.' if request.args.get('saved') else None)
    body = (f'<h2>Audit · {esc(d["label"])} '
            f'<a href="/s/{sid}" class=edit-link>← pohled</a>'
            f'<a href="/s/{sid}/audit.pdf" class=print-link>🖶 PDF</a></h2>'
            f'<div class=nav-prev-next>{prev_a}<a href="/audit">přehled auditů</a>{next_a}</div>'
            f'<p class=muted>{len(op)} otevřených · {len(dn)} vyřešených</p>')

    def render_item(t, done=False):
        num = t['num']
        ref = esc(t['reference'])
        popis = esc(clean_popis(t['popis']))
        typ = esc(t['typ'])
        # mini-tabulka pro torzo (kontext)
        mini = ''
        nid = None
        m = re.search(r'NODE_S\d{4}_\d{2}_\d+', str(t['reference']))
        if m: nid = m.group(0)
        if nid and nrows.get(nid):
            mini = '<table style="margin:5px 0;max-width:520px"><tr><th>#</th><th>Klub</th><th>GP</th><th>W</th><th>D</th><th>L</th><th>GF:GA</th><th>PTS</th></tr>'
            for r in nrows[nid]:
                mini += (f'<tr><td>{r["pos"] or ""}</td><td>{esc(r["club_name"])}</td>'
                         f'<td class=num>{r["GP"] or ""}</td><td class=num>{r["W"] or ""}</td>'
                         f'<td class=num>{r["D"] or ""}</td><td class=num>{r["L"] or ""}</td>'
                         f'<td class=num>{(r["GF"] or "")}:{(r["GA"] or "")}</td>'
                         f'<td class=num>{r["PTS"] or ""}</td></tr>')
            mini += '</table>'
        sel_done = str(t['done']).strip()
        opts_stav = [('ne', 'Otevřeno'), ('ANO', 'Vyřešeno'),
                     ('nedořešitelné', 'Nedořešitelné')]
        stav_html = ''.join(
            f'<option value="{v}"{" selected" if sel_done==v or (not sel_done and v=="ne") else ""}>{lbl}</option>'
            for v, lbl in opts_stav)
        var_html = ''.join(f'<option{" selected" if o and o in (t["poznamka"] or "") else ""}>{esc(o)}</option>'
                           for o in VARIANTY)
        pozn_clean = re.sub(r'^\[[^\]]*\]\s*', '', t['poznamka'] or '')
        return (f'<div class="audit-item{" done" if done else ""}">'
                f'<h4><span class=pill>{typ}</span> #{num} &nbsp; {popis}</h4>'
                f'<div class=ref>{ref}</div>{mini}'
                f'<form method=POST action="/s/{sid}/audit/save">'
                f'<input type=hidden name=num value="{num}">'
                f'<div class=fcol><label>stav</label><select name=done>{stav_html}</select></div>'
                f'<div class=fcol><label>řešení (typ)</label><select name=varianta>{var_html}</select></div>'
                f'<div class=fcol style="flex:1"><label>poznámka kolegy</label>'
                f'<textarea name=poznamka>{esc(pozn_clean)}</textarea></div>'
                f'<button>Uložit do xlsx</button></form></div>')

    if op:
        body += '<h3>Otevřené položky</h3>'
        for t in op: body += render_item(t)
    if dn:
        body += '<h3 style="margin-top:18px">Vyřešené</h3>'
        for t in dn: body += render_item(t, done=True)
    if not items:
        body += '<p class=muted>Žádné položky v TODO listu této sezóny.</p>'
    return render(f'Audit {sid}', body, sid, flash)


def save_todo_resolution(sid, num, done='ne', varianta='', poznamka=''):
    """Zapiš řešení audit položky do TODO listu sešitu (sdílí web i desktop).
    Vrací sloučenou poznámku. Nezávislé na Flasku."""
    num = str(num)
    combined = (f'[{varianta.strip()}] ' if varianta.strip() else '') + poznamka.strip()
    path = os.path.join(DATA, f'S{sid}_FINAL.xlsx')
    wb = openpyxl.load_workbook(path)
    ws = wb['TODO']
    H = {c.value: j for j, c in enumerate(ws[1], 1) if c.value}
    cnum = H.get('#'); cdone = H.get('vyřešeno? (ANO/ne)')
    cpoz = H.get('poznámka kolegy')
    for row in ws.iter_rows(min_row=2):
        if cnum and str(row[cnum - 1].value) == num:
            if cdone: row[cdone - 1].value = done
            if cpoz: row[cpoz - 1].value = combined or None
            break
    wb.save(path); wb.close()
    return combined


def save_system_layout(sid, changes):
    """Zapiš změny org-chartu (nadřazenost + úroveň) do SYSTEM listu.
    changes: {node_id: {'parent_node_id': hodnota|None, 'level': hodnota}}.
    Vrací počet změněných uzlů. Nezávislé na Flasku (sdílí desktop)."""
    if not changes:
        return 0
    path = os.path.join(DATA, f'S{sid}_FINAL.xlsx')
    wb = openpyxl.load_workbook(path)
    ws = wb['SYSTEM']
    H = {c.value: j for j, c in enumerate(ws[1], 1) if c.value}
    cid = H.get('node_id'); cpar = H.get('parent_node_id'); clev = H.get('level')
    n = 0
    for row in ws.iter_rows(min_row=2):
        if not cid:
            break
        nid = row[cid - 1].value
        if nid in changes:
            ch = changes[nid]
            if 'parent_node_id' in ch and cpar:
                row[cpar - 1].value = ch['parent_node_id'] or None
            if 'level' in ch and clev:
                row[clev - 1].value = ch['level'] or None
            n += 1
    wb.save(path); wb.close()
    return n


@app.route('/s/<sid>/audit/save', methods=['POST'])
def audit_save(sid):
    if sid not in CACHE: abort(404)
    save_todo_resolution(sid, request.form.get('num', ''),
                         request.form.get('done', 'ne'),
                         request.form.get('varianta', ''),
                         request.form.get('poznamka', ''))
    reload_season(sid)
    return redirect(url_for('audit', sid=sid, saved=1))


@app.route('/audit')
def audit_overview():
    body = '<h2>Přehled auditů</h2><table><tr><th>Sezóna</th><th>Otevřené</th><th>Vyřešené</th><th></th></tr>'
    tot_o = tot_d = 0
    for sid in SEASON_ORDER:
        d = CACHE.get(sid)
        if not d: continue
        op = sum(1 for t in d['todo'] if str(t['done']).strip().upper() != 'ANO')
        dn = sum(1 for t in d['todo'] if str(t['done']).strip().upper() == 'ANO')
        tot_o += op; tot_d += dn
        if not (op or dn): continue
        bo = f'<span class=badge-open>{op}</span>' if op else '0'
        body += (f'<tr><td><a href="/s/{sid}/audit">{esc(d["label"])}</a></td>'
                 f'<td class=num>{bo}</td><td class=num>{dn}</td>'
                 f'<td><a href="/s/{sid}/audit.pdf">PDF</a></td></tr>')
    body += '</table>'
    body = (f'<div class=stat-row><div class=stat><b>{tot_o}</b><span>otevřených</span></div>'
            f'<div class=stat><b>{tot_d}</b><span>vyřešených</span></div></div>') + body
    return render('Přehled auditů', body)


# ─────────── PDF export ───────────
# Preferuj Garamond (uživatel je zvyklý); fallback na serif.
PDF_FONT = None          # název regular fontu po registraci
PDF_FONT_BOLD = None     # název bold fontu
FONT_DIRS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'),
    os.path.expanduser('~/.fonts'), os.path.expanduser('~/.local/share/fonts'),
    os.path.expanduser('~/Library/Fonts'), '/Library/Fonts',
    '/usr/share/fonts', '/usr/local/share/fonts', 'C:\\Windows\\Fonts']


def _scan_fonts(needles, exclude=()):
    """Najdi .ttf, jehož jméno obsahuje všechny 'needles' a žádný 'exclude'."""
    for d in FONT_DIRS:
        if not d or not os.path.isdir(d): continue
        for root, _, files in os.walk(d):
            for f in files:
                low = f.lower()
                if not low.endswith('.ttf'): continue
                if all(n in low for n in needles) and not any(x in low for x in exclude):
                    return os.path.join(root, f)
    return None


def _fc_match(query):
    import subprocess
    try:
        out = subprocess.run(['fc-match', '-f', '%{file}', query],
                             capture_output=True, text=True, timeout=5)
        p = out.stdout.strip()
        return p if p.lower().endswith('.ttf') and 'garamond' in p.lower() else None
    except Exception:
        return None


def _resolve_fonts():
    """(regular_path, bold_path, label). Garamond > serif fallback."""
    env = os.environ.get('AUDIT_PDF_FONT')
    if env and os.path.exists(env):
        return env, os.environ.get('AUDIT_PDF_FONT_BOLD', env), 'Garamond (env)'
    reg = (_scan_fonts(['garamond'], exclude=['bold', 'italic', 'oblique'])
           or _fc_match('Garamond'))
    if reg:
        bold = (_scan_fonts(['garamond', 'bold'], exclude=['italic'])
                or _fc_match('Garamond:bold') or reg)
        return reg, bold, 'Garamond'
    # fallback: serif
    for base, rname, bname in [
        ('/usr/share/fonts/truetype/liberation', 'LiberationSerif-Regular.ttf',
         'LiberationSerif-Bold.ttf'),
        ('/usr/share/fonts/truetype/dejavu', 'DejaVuSerif.ttf',
         'DejaVuSerif-Bold.ttf')]:
        r = os.path.join(base, rname)
        if os.path.exists(r):
            b = os.path.join(base, bname)
            return r, (b if os.path.exists(b) else r), 'serif (fallback)'
    return None, None, 'none'


def _ensure_font():
    global PDF_FONT, PDF_FONT_BOLD
    if PDF_FONT: return PDF_FONT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    reg, bold, label = _resolve_fonts()
    if not reg:
        raise RuntimeError('Nenalezen žádný TTF font pro PDF.')
    pdfmetrics.registerFont(TTFont('AuditSerif', reg))
    pdfmetrics.registerFont(TTFont('AuditSerif-Bold', bold))
    PDF_FONT, PDF_FONT_BOLD = 'AuditSerif', 'AuditSerif-Bold'
    print(f"  PDF font: {label}  ({os.path.basename(reg)})")
    return PDF_FONT


def build_season_pdf(d, sid):
    """Tiskový audit-worklist sezóny → bytes (jen otevřené položky)."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    _ensure_font()
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle('H1', parent=ss['Title'], fontName=PDF_FONT_BOLD, fontSize=16)
    H2 = ParagraphStyle('H2', parent=ss['Heading3'], fontName=PDF_FONT_BOLD, fontSize=11,
                        spaceBefore=8, spaceAfter=2)
    P = ParagraphStyle('P', parent=ss['Normal'], fontName=PDF_FONT, fontSize=9.5, leading=12)
    Pm = ParagraphStyle('Pm', parent=P, textColor=colors.HexColor('#666'), fontSize=8.5)
    box = ParagraphStyle('box', parent=P, fontName=PDF_FONT,
                         backColor=colors.HexColor('#fff3df'), borderPadding=4,
                         leftIndent=2, spaceBefore=2, spaceAfter=2)
    nrows = node_rows(d)
    op = [t for t in d['todo'] if str(t['done']).strip().upper() != 'ANO']
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=12 * mm,
                            title=f'Audit {d["label"]}')
    el = [Paragraph(f'Audit — sezóna {esc(d["label"])}', H1),
          Paragraph(f'{len(op)} otevřených položek · k ručnímu zpracování', Pm),
          Spacer(1, 6)]
    checks = '☐ OK   ☐ doplnit týmy   ☐ sloučit   ☐ smazat   ☐ opravit   ☐ neúplné→Todo'
    for t in op:
        el.append(Paragraph(f'<b>#{t["num"]} · {esc(t["typ"])}</b> — {esc(t["reference"])}', H2))
        el.append(Paragraph(esc(clean_popis(t['popis'])), box))
        nid = None
        m = re.search(r'NODE_S\d{4}_\d{2}_\d+', str(t['reference']))
        if m: nid = m.group(0)
        if nid and nrows.get(nid):
            data = [['#', 'Klub', 'GP', 'W', 'D', 'L', 'GF:GA', 'PTS']]
            for r in nrows[nid]:
                data.append([r['pos'] or '', r['club_name'] or '',
                             r['GP'] or '', r['W'] or '', r['D'] or '', r['L'] or '',
                             f'{r["GF"] or ""}:{r["GA"] or ""}', r['PTS'] or ''])
            tb = Table(data, colWidths=[8 * mm, 70 * mm, 11 * mm, 9 * mm, 9 * mm,
                                        9 * mm, 18 * mm, 11 * mm])
            tb.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), PDF_FONT, 8),
                ('FONT', (0, 0), (-1, 0), PDF_FONT_BOLD, 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef2f7')),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT')]))
            el.append(tb)
        el.append(Paragraph(checks, P))
        el.append(Paragraph('poznámka: ' + '.' * 78, Pm))
        el.append(Spacer(1, 6))
    if not op:
        el.append(Paragraph('Žádné otevřené položky — sezóna OK.', P))
    doc.build(el)
    return buf.getvalue()


def audit_notes_by_node(d):
    """node_id -> [čisté audit komentáře 'co chybí']."""
    by = defaultdict(list)
    for nt in d['notes']:
        txt = nt['note_text']
        if nt['node_id'] and (nt['source_type'] == 'TODO-auto'
                              or str(txt).startswith('[TBD]')):
            by[nt['node_id']].append(clean_popis(txt))
    return by


def build_full_pdf(d, sid):
    """Plná sezóna: pyramida + všechny tabulky + komentáře a zaškrtávátka."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, KeepTogether)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    _ensure_font()
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle('H1', parent=ss['Title'], fontName=PDF_FONT_BOLD, fontSize=16)
    H2 = ParagraphStyle('H2', parent=ss['Heading2'], fontName=PDF_FONT_BOLD, fontSize=12,
                        spaceBefore=10, spaceAfter=3, textColor=colors.HexColor('#1a3050'))
    H3 = ParagraphStyle('H3', parent=ss['Heading3'], fontName=PDF_FONT_BOLD, fontSize=10,
                        spaceBefore=6, spaceAfter=1)
    P = ParagraphStyle('P', parent=ss['Normal'], fontName=PDF_FONT, fontSize=9, leading=11)
    Pm = ParagraphStyle('Pm', parent=P, textColor=colors.HexColor('#666'), fontSize=8)
    box = ParagraphStyle('box', parent=P, fontName=PDF_FONT,
                         backColor=colors.HexColor('#fff3df'), borderPadding=3,
                         borderColor=colors.HexColor('#d97706'), borderWidth=0.5,
                         leftIndent=2, spaceBefore=1, spaceAfter=1)
    donebox = ParagraphStyle('donebox', parent=box,
                             backColor=colors.HexColor('#e4f5e7'),
                             borderColor=colors.HexColor('#3a9d4f'))
    anotes = audit_notes_by_node(d)
    resolved = set()
    for t in d['todo']:
        if str(t['done']).strip().upper() == 'ANO':
            m = re.search(r'NODE_S\d{4}_\d{2}_\d+', str(t['reference']))
            if m: resolved.add(m.group(0))
    nodes = {n['node_id']: n for n in d['system']}
    checks = '☐ OK  ☐ doplnit týmy  ☐ sloučit  ☐ smazat  ☐ opravit  ☐ neúplné→Todo  ____________'
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=13 * mm, bottomMargin=11 * mm,
                            title=f'Almanach {d["label"]}')
    n_gap = sum(len(v) for v in anotes.values())
    el = [Paragraph(f'Almanach — sezóna {esc(d["label"])}', H1),
          Paragraph(f'Plný přehled k revizi · {len(d["system"])} soutěží · '
                    f'{n_gap} míst s poznámkou „co chybí"', Pm), Spacer(1, 5)]

    def mk_table(rows, head, widths, aligns_right_from=2):
        data = [head]
        data += rows
        tb = Table(data, colWidths=widths, repeatRows=1)
        tb.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), PDF_FONT, 8),
            ('FONT', (0, 0), (-1, 0), PDF_FONT_BOLD, 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef2f7')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
            ('ALIGN', (aligns_right_from, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5)]))
        return tb

    # pyramida
    top = sorted([x for x in d['system'] if not x['parent_node_id']],
                 key=lambda x: (str(x['level']), x['node_id']))
    if top:
        el.append(Paragraph('Pyramida soutěží', H2))
        rows = [[esc(n['name']), esc(n['competition_type']), esc(n['level']),
                 esc(n['feeds_into'] or '')] for n in top]
        el.append(mk_table(rows, ['Soutěž', 'Typ', 'Úroveň', 'feeds_into'],
                           [78 * mm, 34 * mm, 20 * mm, 50 * mm], aligns_right_from=99))

    # tabulky po listech
    for sh in sorted(d['standings'].keys()):
        trows = [r for r in d['standings'][sh] if r['row_type'] == 'T']
        if not trows: continue
        el.append(Paragraph(esc(sh), H2))
        # seskup po node_id v pořadí výskytu
        order, groups = [], defaultdict(list)
        for r in trows:
            nid = r['node_id']
            if nid not in groups: order.append(nid)
            groups[nid].append(r)
        for nid in order:
            nn = nodes.get(nid)
            nm = nn['name'] if nn else (nid or '')
            is_done = nid in resolved
            block = [Paragraph(esc(nm), H3)]
            for c in anotes.get(nid, []):
                if is_done:
                    block.append(Paragraph('✓ vyřešeno — ' + esc(c), donebox))
                else:
                    block.append(Paragraph('⚑ ' + esc(c), box))
            rows = [[r['pos'] or '', esc(r['club_name'] or ''),
                     r['GP'] or '', r['W'] or '', r['D'] or '', r['L'] or '',
                     f'{r["GF"] or ""}:{r["GA"] or ""}', r['PTS'] or '',
                     esc(r['season_fate'] or '')] for r in groups[nid]]
            block.append(mk_table(
                rows, ['#', 'Klub', 'GP', 'W', 'D', 'L', 'GF:GA', 'PTS', 'Fate'],
                [7 * mm, 62 * mm, 10 * mm, 8 * mm, 8 * mm, 8 * mm, 16 * mm, 10 * mm, 22 * mm]))
            if anotes.get(nid) and not is_done:
                block.append(Paragraph(checks, P))
            block.append(Spacer(1, 4))
            el.append(KeepTogether(block))
    doc.build(el)
    return buf.getvalue()


_SK_RE = re.compile(
    r'(Sloven|Západoslov|Východoslov|St[řr]edoslov|Bratislav|Košic|Nitran|'
    r'Prešov|Žilin|Banskobystr|Trnav|Trenč|SNHL)', re.I)


def _pdf_region(name):
    return 'SK' if _SK_RE.search(str(name or '')) else 'CZ'


def _pdf_core(name):
    s = str(name or '')
    s = re.sub(r',?\s*\d+\.\s*úroveň(\s*\([^)]*\))?', '', s, flags=re.I)
    s = re.sub(r',?\s*(skupina|Skupina|sk\.)\s*[^,]*', '', s, flags=re.I)
    s = re.sub(r',?\s*(semifinále|čtvrtfinále|finále|základní (část|skupina)|'
               r'finálová skupina|o udržení|o umístění|play\-?off|nadstavba|'
               r'červená|modrá|O \d)[^,]*', '', s, flags=re.I)
    s = re.sub(r'\s+', ' ', s).strip().strip(',').strip(' -–').strip()
    return s or str(name or '')


def _pdf_tier_name(level, names):
    cores = []
    for n in names:
        c = _pdf_core(n)
        if c and c not in cores:
            cores.append(c)
    low = ' '.join(names).lower()
    if sum('kvalifik' in c.lower() for c in cores) >= max(1, (len(cores) + 1) // 2):
        return 'Kvalifikace o postup'
    leagues = [c for c in cores if re.search(r'(ČNHL|SNHL|CHL|liga|extraliga)', c, re.I)]
    if leagues:
        seen = []
        for c in leagues:
            if c not in seen:
                seen.append(c)
        return ' / '.join(seen[:3])
    m = re.search(r'(\d+)\.\s*úroveň', low)
    if m:
        return f'Krajské soutěže ({m.group(1)}. úroveň)'
    if re.search(r'přebor|kraj|třída', low):
        return 'Krajské soutěže'
    return cores[0] if cores else (str(level) or '—')


def build_orgchart_pdf(d, sid):
    """Org chart sezóny jako pyramida: úrovně shora dolů, ČECHY | SLOVENSKO,
    názvy úrovní odvozené z obsahu. Soutěže sloučené (×N skupin)."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    _ensure_font()
    import collections as _c
    import io
    buf = io.BytesIO()
    W, H = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    c.setTitle(f'Org chart {d["label"]}')
    M = 12 * mm
    GUT = 50 * mm                      # levý sloupec s názvem úrovně
    CONTENT_X = M + GUT
    CZ_W = 130 * mm
    DIV_X = CONTENT_X + CZ_W
    SK_X = DIV_X + 4 * mm
    SK_W = W - M - SK_X
    BW, BH, GAP = 41 * mm, 11 * mm, 3 * mm
    PAL = [(colors.HexColor('#e3edff'), colors.HexColor('#8fb0e6')),
           (colors.HexColor('#dcf4e8'), colors.HexColor('#74c19c')),
           (colors.HexColor('#fdecc9'), colors.HexColor('#e0b76e')),
           (colors.HexColor('#ece0f7'), colors.HexColor('#b194d6')),
           (colors.HexColor('#fde0e2'), colors.HexColor('#e0939a')),
           (colors.HexColor('#ddf0f3'), colors.HexColor('#83bdc7')),
           (colors.HexColor('#eef1d6'), colors.HexColor('#bcc47e'))]

    # hlavní soutěže: vrchol vždy; vnitřní kola/fáze (Playoff, Finále…) ven,
    # ale podsoutěže (I.ČNHL, II.SNHL…) necháme. Sloučení do jádra pak řeší _pdf_core.
    phase = re.compile(
        r'^(Play\-?off|Playoff|Finále|Semifinále|Čtvrtfinále|Předkolo|Baráž|'
        r'Nadstavba|Základní část|Skupina o udržení|O\s+\d.*m[ií]sto|O umístění|'
        r'O postup|Finálová skupina|kolo\b)', re.I)
    node_ids = {n['node_id'] for n in d['system']}
    tops = [n for n in d['system']
            if n['parent_node_id'] not in node_ids
            or not phase.match(str(n['name']).strip())]
    levels = sorted({n['level'] for n in tops}, key=lambda l: (lvl(l) or 9999))
    by = _c.defaultdict(lambda: _c.defaultdict(lambda: _c.defaultdict(int)))
    names_at = _c.defaultdict(list)
    for n in tops:
        reg = _pdf_region(n['name'])
        by[n['level']][reg][_pdf_core(n['name'])] += 1
        names_at[n['level']].append(str(n['name']))

    def header():
        c.setFillColor(colors.HexColor('#1a3050'))
        c.setFont(PDF_FONT_BOLD, 15)
        c.drawString(M, H - M + 1, f'Org chart soutěží — sezóna {d["label"]}')
        c.setFont(PDF_FONT, 8.5)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(M, H - M - 11, 'Pyramida úrovní shora (nejvyšší) dolů · '
                                    'hlavní soutěže (vnitřní kola sloučena) · ČR/SK auto z názvu')
        c.setFont(PDF_FONT_BOLD, 9)
        c.setFillColor(colors.HexColor('#1a3050'))
        c.drawString(CONTENT_X + 2, H - M - 26, 'ČECHY / celostátní')
        c.drawString(SK_X + 2, H - M - 26, 'SLOVENSKO')

    def boxes_height(groups, width):
        per = max(1, int((width + GAP) // (BW + GAP)))
        rows = max(1, -(-len(groups) // per)) if groups else 1
        return rows * (BH + GAP)

    def draw_boxes(groups, x0, width, fill, edge):
        if not groups:
            c.setFillColor(colors.HexColor('#bbbbbb')); c.setFont(PDF_FONT, 8)
            c.drawString(x0 + 2, cur_y - BH + 3, '—')
            return
        per = max(1, int((width + GAP) // (BW + GAP)))
        for i, (core_nm, cnt) in enumerate(sorted(groups.items())):
            col, row = i % per, i // per
            bx = x0 + col * (BW + GAP)
            byy = cur_y - row * (BH + GAP) - BH
            c.setFillColor(fill); c.setStrokeColor(edge); c.setLineWidth(1)
            c.roundRect(bx, byy, BW, BH, 4, stroke=1, fill=1)
            label = core_nm if len(core_nm) <= 33 else core_nm[:31] + '…'
            c.setFillColor(colors.HexColor('#15314e')); c.setFont(PDF_FONT, 7.4)
            c.drawString(bx + 3, byy + BH / 2 - 2.4, label)

    header()
    cur_y = H - M - 34
    for ti, lev in enumerate(levels):
        cz = by[lev]['CZ']; sk = by[lev]['SK']
        th = max(boxes_height(cz, CZ_W), boxes_height(sk, SK_W)) + 4 * mm
        if cur_y - th < M:
            c.showPage(); header(); cur_y = H - M - 34
        fill, edge = PAL[ti % len(PAL)]
        # pruh úrovně (levý sloupec)
        c.setFillColor(edge)
        c.roundRect(M, cur_y - th + 3, GUT - 4 * mm, th - 4, 5, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont(PDF_FONT_BOLD, 8.6)
        tname = _pdf_tier_name(lev, names_at[lev])
        ty = cur_y - 6
        for line in _wrap_words(tname, 26):
            c.drawString(M + 4, ty, line); ty -= 10
        c.setFont(PDF_FONT, 7); c.drawString(M + 4, cur_y - th + 8, str(lev))
        # boxy
        draw_boxes(cz, CONTENT_X, CZ_W, fill, edge)
        draw_boxes(sk, SK_X, SK_W, fill, edge)
        # dělící čára CZ|SK
        c.setStrokeColor(colors.HexColor('#cfd6e0')); c.setLineWidth(0.8)
        c.line(DIV_X + 2, cur_y - th + 4, DIV_X + 2, cur_y)
        c.setStrokeColor(colors.HexColor('#e6e9ee'))
        c.line(M, cur_y - th + 2, W - M, cur_y - th + 2)
        cur_y -= th + 2 * mm
    c.showPage(); c.save()
    return buf.getvalue()


def _wrap_words(text, width):
    out, line = [], ''
    for w in str(text).split():
        if len(line) + len(w) + 1 > width and line:
            out.append(line); line = w
        else:
            line = (line + ' ' + w).strip()
    if line:
        out.append(line)
    return out[:3]


@app.route('/s/<sid>/orgchart.pdf')
def orgchart_pdf(sid):
    if sid not in CACHE or not CACHE[sid]: abort(404)
    from flask import Response
    pdf = build_orgchart_pdf(CACHE[sid], sid)
    return Response(pdf, mimetype='application/pdf',
                    headers={'Content-Disposition':
                             f'inline; filename=orgchart_{sid}.pdf'})


@app.route('/s/<sid>/full.pdf')
def full_pdf(sid):
    if sid not in CACHE or not CACHE[sid]: abort(404)
    from flask import Response
    pdf = build_full_pdf(CACHE[sid], sid)
    return Response(pdf, mimetype='application/pdf',
                    headers={'Content-Disposition':
                             f'inline; filename=almanach_{sid}.pdf'})


@app.route('/s/<sid>/audit.pdf')
def audit_pdf(sid):
    if sid not in CACHE or not CACHE[sid]: abort(404)
    from flask import Response
    pdf = build_season_pdf(CACHE[sid], sid)
    return Response(pdf, mimetype='application/pdf',
                    headers={'Content-Disposition':
                             f'inline; filename=audit_{sid}.pdf'})


# ─────────── All-in-one CLI (serve / build / print) ───────────
def cli_build():
    """Konsolidace xlsx → almanach.sqlite + CSV (volá build_db.py)."""
    import subprocess
    print("Builder: data/S*_FINAL.xlsx → almanach.sqlite …")
    r = subprocess.run([sys.executable, 'build_db.py'])
    sys.exit(r.returncode)


def _seasons_arg(arg):
    if not arg or arg == 'all':
        return list(SEASON_ORDER)
    arg = arg.replace('/', '_').lstrip('S')
    return [arg] if arg in SEASON_ORDER else []


def cli_pdf(arg):
    outdir = 'docs/audit_pdf'
    os.makedirs(outdir, exist_ok=True)
    seasons = _seasons_arg(arg)
    for sid in seasons:
        d = CACHE.get(sid)
        if not d: continue
        with open(os.path.join(outdir, f'almanach_S{sid}.pdf'), 'wb') as f:
            f.write(build_full_pdf(d, sid))
        with open(os.path.join(outdir, f'audit_S{sid}.pdf'), 'wb') as f:
            f.write(build_season_pdf(d, sid))
    print(f"PDF: {len(seasons)} sezón (plný + audit) → {outdir}/")


def cli_html(arg):
    outdir = 'docs/audit_html'
    os.makedirs(outdir, exist_ok=True)
    c = app.test_client()
    seasons = _seasons_arg(arg)
    for sid in seasons:
        full = c.get(f'/s/{sid}').get_data(as_text=True)
        with open(os.path.join(outdir, f'sezona_S{sid}.html'), 'w') as f:
            f.write(full)
        au = c.get(f'/s/{sid}/audit').get_data(as_text=True)
        with open(os.path.join(outdir, f'audit_S{sid}.html'), 'w') as f:
            f.write(au)
    print(f"HTML: {len(seasons)} sezón (plný + audit) → {outdir}/")


def cli_xlsx(arg):
    """Audit worklist → docs/Audit_export.xlsx (listy per sezóna)."""
    import openpyxl as ox
    from openpyxl.styles import Font, PatternFill, Alignment
    wb = ox.Workbook(); wb.remove(wb.active)
    hf = Font(bold=True, color='FFFFFF'); fl = PatternFill('solid', fgColor='305496')
    seasons = _seasons_arg(arg)
    for sid in seasons:
        d = CACHE.get(sid)
        if not d or not d['todo']: continue
        ws = wb.create_sheet(sid.replace('_', '-')[:31])
        ws.append(['#', 'typ', 'reference', 'co chybí / popis', 'stav', 'poznámka'])
        for c0 in ws[1]: c0.font = hf; c0.fill = fl
        for t in d['todo']:
            ws.append([t['num'], t['typ'], t['reference'],
                       clean_popis(t['popis']), t['done'] or 'ne', t['poznamka']])
        for col, w in zip('ABCDEF', [5, 14, 40, 55, 10, 30]):
            ws.column_dimensions[col].width = w
        for r in ws.iter_rows(min_row=2):
            for c0 in r: c0.alignment = Alignment(wrap_text=True, vertical='top')
        ws.freeze_panes = 'A2'
    out = 'docs/Audit_export.xlsx'
    wb.save(out)
    print(f"XLSX: {len(wb.sheetnames)} listů → {out}")


def cli_serve():
    print(f"\n  → otevři: http://localhost:5000   "
          f"(viewer · korektor · audit · PDF)\n")
    app.run(host='127.0.0.1', port=5000, debug=False)


HELP = """Almanach — vše v jednom (korektor · viewer · builder · printer)

  python app.py [serve]        spustí web (viewer + korektor + audit)   [výchozí]
  python app.py build          xlsx → almanach.sqlite + CSV
  python app.py pdf  [sid|all] audit worklist → docs/audit_pdf/*.pdf  (Garamond)
  python app.py html [sid|all] audit worklist → docs/audit_html/*.html
  python app.py xlsx [sid|all] audit worklist → docs/Audit_export.xlsx

  sid např. 1948_49.  PDF font: Garamond (env AUDIT_PDF_FONT, fonts/, fc-match),
  jinak serif fallback."""

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'serve'
    if cmd in ('-h', '--help', 'help'):
        print(HELP); sys.exit(0)
    if cmd == 'build':
        cli_build()
    load_all()
    arg = sys.argv[2] if len(sys.argv) > 2 else 'all'
    if cmd == 'serve':
        cli_serve()
    elif cmd == 'pdf':
        cli_pdf(arg)
    elif cmd == 'html':
        cli_html(arg)
    elif cmd == 'xlsx':
        cli_xlsx(arg)
    else:
        print(f"Neznámý příkaz '{cmd}'.\n"); print(HELP); sys.exit(1)
