import json, re
with open('/tmp/s1988_full.json') as f: D=json.load(f)

def norm(n): return re.sub(r'\s*\([^)]+\)','',n).replace('HC ','').replace('TJ ','').replace('ASD ','').replace('VTJ ','').strip().lower()
def fc(f): return {'postup':'f-up','sestup':'f-down','reorganizace':'f-reorg'}.get(f,'')
def fl(f): return {'postup':'▲ postup','sestup':'▼ sestup','reorganizace':'◆ reorg.'}.get(f,'')
def bdg(n): return {'M':'<span class="badge m">M</span>','N':'<span class="badge n">N</span>','S':'<span class="badge s">S</span>'}.get(n,'')
def is_releg(name): return any(x in name.lower() for x in ['udržení','záchran','o 9','o 11'])
def is_basic(name): return 'ákladní' in name.lower() or name in ('I.NHL','I.SNHL','I.ČNHL','II.ČNHL','II.SNHL') or re.match(r'^I+\.[ČS]?NHL$', name)

def compute_terminal(blocks):
    t={}
    for bi,b in enumerate(blocks):
        for r in b['rows']: t[r['club']]=bi
    return t

def build_dest(blocks, po_series):
    """Vrati funkci club->navaznost. Postup do play-off / o udrzeni."""
    po_clubs=set()
    for s in po_series:
        if any(x in s['node'].lower() for x in ['čtvrtfinále','předkolo']):
            po_clubs.add(norm(s['t1']['name'])); po_clubs.add(norm(s['t2']['name']))
    rel_clubs=set()
    for b in blocks:
        if is_releg(b['name']):
            for r in b['rows']: rel_clubs.add(norm(r['club']))
    def resolve(club):
        cn=norm(club)
        if cn in po_clubs: return ('► play-off','d-po')
        if cn in rel_clubs: return ('► o udržení','d-rel')
        return ('','')
    return resolve

def rtable(b, bi, terminal, resolve=None):
    rows=''; releg=is_releg(b['name']); basic=is_basic(b['name'])
    show_dest = basic and resolve is not None
    for r in b['rows']:
        gf=r['gf'] if r['gf'] is not None else ''
        ga=r['ga'] if r['ga'] is not None else ''
        # KLICOVE: v zakl.casti NIKDY season_fate - jen navaznost
        if basic:
            fate=''
        else:
            fate=r['fate'] if terminal.get(r['club'])==bi else ''
        dcell=''
        if show_dest:
            dl,dcls=resolve(r['club'])
            dcell=f'<td class="dest {dcls}">{dl}</td>'
        rows+=f'''<tr class="{fc(fate)}"><td class="pos">{r['pos']}</td><td class="club">{r['club']} {bdg(r['note'])}</td><td class="num">{r['gp'] if r['gp'] is not None else ''}</td><td class="num">{r['w'] if r['w'] is not None else ''}</td><td class="num">{r['d'] if r['d'] is not None else ''}</td><td class="num">{r['l'] if r['l'] is not None else ''}</td><td class="num gd">{gf}:{ga}</td><td class="num pts">{r['body'] if r['body'] is not None else ''}</td>{dcell}<td class="fate">{fl(fate)}</td></tr>'''
    cls='block releg' if releg else 'block'
    tag='<span class="releg-tag">o udržení</span>' if releg else ''
    dhead='<th class="dest">Postupuje</th>' if show_dest else ''
    return f'''<div class="{cls}"><h3>{b['name']} {tag}</h3><table><thead><tr><th class="pos">#</th><th class="club">Klub</th><th class="num">Z</th><th class="num">V</th><th class="num">R</th><th class="num">P</th><th class="num gd">Skóre</th><th class="num pts">B</th>{dhead}<th class="fate">Osud</th></tr></thead><tbody>{rows}</tbody></table></div>'''

def render_level(blocks, po_series=None):
    term=compute_terminal(blocks)
    resolve=build_dest(blocks, po_series or [])
    return ''.join(rtable(b,bi,term,resolve) for bi,b in enumerate(blocks))

def po_bracket(series, phases):
    html='<div class="po-bracket">'
    for ph in phases:
        pser=[s for s in series if ph.lower() in s['node'].lower()]
        if not pser: continue
        html+=f'<div class="po-col"><div class="po-phase">{ph}</div>'
        for s in pser:
            t1,t2=s['t1'],s['t2']
            try: a,b=map(int,t1['sscore'].split(':')); w1=a>b
            except: w1=False
            html+=f'''<div class="po-series"><div class="po-team {'po-win' if w1 else ''}">{t1['name']}<span class="po-sc">{t1['sscore'].split(':')[0] if ':' in str(t1['sscore']) else ''}</span></div><div class="po-team {'po-win' if not w1 else ''}">{t2['name']}<span class="po-sc">{t1['sscore'].split(':')[1] if ':' in str(t1['sscore']) else ''}</span></div><div class="po-games">{t1['games']}</div></div>'''
        html+='</div>'
    return html+'</div>'

extra=render_level(D['extra'], D['po_extra'])
po_e=po_bracket(D['po_extra'],['Čtvrtfinále','Semifinále','Finále','O 3.místo','O 5.místo','O 5.-8.místo','O 7.místo','O 9.místo'])
nhl1=render_level(D['nhl1'], D['po_nhl1'])
po_n1=po_bracket(D['po_nhl1'],['čtvrtfinále','semifinále','finále','O 3.místo'])
nhl2=render_level(D['nhl2'], D['po_nhl2'])
kval=''.join(rtable(b,bi,compute_terminal(D['kval'])) for bi,b in enumerate(D['kval']))
kraje_rows=''.join(f'<tr><td class="club">{k}</td><td class="num pts">{v}</td></tr>' for k,v in sorted(D['kraje'].items(),key=lambda x:-x[1]))
kraje_total=sum(D['kraje'].values())

html=f'''<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Sezóna 1988/89</title><style>
*{{margin:0;padding:0;box-sizing:border-box;}} html{{scroll-behavior:smooth;}}
body{{font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:#fbfbfa;color:#1a1a1a;line-height:1.45;padding:1.5rem 1rem 4rem;font-size:14px;}}
.wrap{{max-width:900px;margin:0 auto;}}
header{{border-bottom:2px solid #1a1a1a;padding-bottom:1rem;margin-bottom:1.2rem;}}
h1{{font-size:1.6rem;font-weight:700;}} .sub{{color:#555;font-size:0.85rem;margin-top:0.3rem;}}
.level{{margin-top:2rem;}}
.level-head{{display:flex;align-items:baseline;gap:0.6rem;background:#1a1a1a;color:#fff;padding:0.5rem 0.8rem;border-radius:3px 3px 0 0;}}
.level-head .lname{{font-size:1.05rem;font-weight:700;}} .level-head .lmeta{{font-size:0.72rem;color:#bbb;margin-left:auto;}}
.block{{margin-top:1rem;}} .block h3{{font-size:0.85rem;font-weight:600;color:#444;padding:0.4rem 0.2rem;border-bottom:1px solid #ddd;}}
.block.releg h3{{color:#b03030;border-bottom-color:#e0b0b0;}}
.releg-tag{{font-size:0.62rem;background:#b03030;color:#fff;padding:0.1rem 0.4rem;border-radius:2px;margin-left:0.4rem;text-transform:uppercase;vertical-align:middle;}}
.block.releg{{background:#fdf6f6;border-left:3px solid #b03030;border-radius:0 3px 3px 0;padding:0.2rem 0.6rem 0.5rem;}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;}}
th,td{{padding:0.3rem 0.4rem;text-align:left;}}
thead th{{font-size:0.66rem;text-transform:uppercase;letter-spacing:0.05em;color:#999;border-bottom:1px solid #ccc;}}
tbody tr{{border-bottom:1px solid #eee;}} tbody tr:hover{{background:#f0f0ee;}}
.pos{{width:26px;text-align:center;color:#999;font-size:0.8rem;}} .club{{font-weight:500;}}
.num{{text-align:center;width:32px;font-size:0.82rem;}} .gd{{width:60px;color:#555;}} .pts{{font-weight:700;width:34px;}}
.dest{{width:108px;font-size:0.68rem;font-weight:600;}} .dest.d-po{{color:#2a5a8a;}} .dest.d-rel{{color:#b03030;}}
.fate{{width:68px;font-size:0.7rem;text-align:right;}}
tr.f-up{{background:#f0f7f0;}} tr.f-up .fate{{color:#2d7a32;font-weight:600;}}
tr.f-down{{background:#fbf0f0;}} tr.f-down .fate{{color:#b03030;font-weight:600;}}
tr.f-reorg{{background:#fbf8ed;}} tr.f-reorg .fate{{color:#9a7d1a;}}
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;padding:0.05rem 0.3rem;border-radius:2px;margin-left:0.2rem;}}
.badge.m{{background:#1a1a1a;color:#fff;}} .badge.n{{background:#2d7a32;color:#fff;}} .badge.s{{background:#b03030;color:#fff;}}
.po-wrap{{margin-top:1rem;background:#f4f6f8;border:1px solid #dde3e8;border-radius:4px;padding:0.8rem;}}
.po-head{{font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#2a4a6a;margin-bottom:0.7rem;}}
.po-bracket{{display:flex;gap:0.8rem;overflow-x:auto;padding-bottom:0.4rem;}}
.po-col{{min-width:165px;flex:1;}}
.po-phase{{font-size:0.64rem;text-transform:uppercase;color:#5a7088;font-weight:700;margin-bottom:0.4rem;text-align:center;}}
.po-series{{background:#fff;border:1px solid #d5dde4;border-radius:3px;margin-bottom:0.5rem;overflow:hidden;}}
.po-team{{display:flex;justify-content:space-between;padding:0.26rem 0.5rem;font-size:0.74rem;border-bottom:1px solid #eef1f4;}}
.po-team.po-win{{font-weight:700;background:#eaf5ea;}} .po-sc{{font-weight:700;margin-left:0.5rem;}}
.po-games{{font-size:0.6rem;color:#889;padding:0.18rem 0.5rem;background:#fafbfc;}}
.flow-note{{margin-top:0.7rem;font-size:0.72rem;color:#555;padding:0.5rem 0.7rem;background:#eef2f6;border-radius:3px;border-left:3px solid #2a5a8a;}}
.kval-zone{{margin:1.5rem 0;padding:0.6rem 0.8rem;background:#fdfaf3;border-left:3px solid #c89a3c;border-radius:0 3px 3px 0;}}
.kval-zone-head{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#9a7d1a;font-weight:700;margin-bottom:0.5rem;}}
.kraj-table{{max-width:340px;}}
.legend{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #ddd;font-size:0.72rem;color:#666;display:flex;flex-wrap:wrap;gap:0.8rem 1.5rem;}}
.legend b{{color:#1a1a1a;}} footer{{margin-top:1.5rem;font-size:0.7rem;color:#999;}}
</style></head><body><div class="wrap">
<header><h1>Lední hokej ČSSR — sezóna 1988/89</h1>
<div class="sub">Všechny soutěže · základní část → play-off / skupina o udržení</div></header>

<div class="level"><div class="level-head"><span class="lname">1. úroveň — I. liga</span><span class="lmeta">L10 · 12 klubů</span></div>
{extra}
<div class="flow-note">► <b>Návaznost:</b> 1.–8. ze ZČ → <b style="color:#2a5a8a">play-off</b> (o titul), 9.–12. → <b style="color:#b03030">skupina o udržení</b>. Osud (postup/sestup) se rozhoduje až v cílové fázi.</div>
<div class="po-wrap"><div class="po-head">Play-off → 🏆 Tesla Pardubice</div>{po_e}</div>
</div>

<div class="level"><div class="level-head"><span class="lname">2. úroveň — I. ČNHL + I. SNHL</span><span class="lmeta">L20 · 22 klubů</span></div>
{nhl1}
<div class="po-wrap"><div class="po-head">Play-off I. ČNHL</div>{po_n1}</div>
</div>

<div class="kval-zone"><div class="kval-zone-head">Kvalifikace o 2. ČNHL / 2. SNHL · L35</div>{kval}</div>

<div class="level"><div class="level-head"><span class="lname">3. úroveň — II. ČNHL + II. SNHL</span><span class="lmeta">L30 · 43 klubů</span></div>
{nhl2}
</div>

<div class="level"><div class="level-head"><span class="lname">4. úroveň — Krajské přebory</span><span class="lmeta">L40 · {kraje_total} klubů · 11 krajů</span></div>
<table class="kraj-table"><thead><tr><th class="club">Kraj</th><th class="num pts">Klubů</th></tr></thead><tbody>{kraje_rows}</tbody></table>
</div>

<div class="legend">
<span><b>Z</b> zápasy · <b>V</b> výhry · <b>R</b> remízy · <b>P</b> prohry · <b>B</b> body</span>
<span><b style="color:#2a5a8a">►</b> postup do fáze (uvnitř soutěže) · <b style="color:#2a4a6a">⬛</b> play-off · <b style="color:#9a7d1a">↕</b> baráž</span>
<span><b style="color:#2d7a32">▲</b> postup (mezi úrovněmi) · <b style="color:#b03030">▼</b> sestup · <b style="color:#9a7d1a">◆</b> reorg.</span>
</div>
<footer>Data: Hokejový almanach (registr D42) · Mistr: Tesla Pardubice</footer>
</div></body></html>'''

with open('/mnt/user-data/outputs/sezona_1988_89.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"HTML opraveno ({len(html)} znaku)")

# Validace NHL1 zakl.cast
print("\n=== NHL1 zakl.cast - fate skryt, navaznost zobrazena ===")
resolve=build_dest(D['nhl1'], D['po_nhl1'])
for b in D['nhl1']:
    if is_basic(b['name']):
        for r in b['rows'][:6]:
            dl,_=resolve(r['club'])
            print(f"  {r['pos']}. {r['club'][:28]:<28} fate_data={r['fate']:<8} → zobrazeno: navaznost='{dl}', osud=SKRYT")
