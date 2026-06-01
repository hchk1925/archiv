import json, re
with open('/tmp/s1988_data.json') as f: D=json.load(f)

def norm(n):
    n=re.sub(r'\s*\([^)]+\)','',n)
    return n.replace('HC ','').replace('TJ ','').strip().lower()

playoff_norm={norm(c) for c in D['playoff_clubs']}
udrzeni_norm={norm(c) for c in D['udrzeni_clubs']}

def fc(f): return {'postup':'f-up','sestup':'f-down','reorganizace':'f-reorg','setrval':''}.get(f,'')
def fl(f): return {'postup':'▲ postup','sestup':'▼ sestup','reorganizace':'◆ reorg.','setrval':''}.get(f,'')
def bdg(n): return {'M':'<span class="badge m">M</span>','N':'<span class="badge n">N</span>','S':'<span class="badge s">S</span>'}.get(n,'')
def is_releg(name): return any(x in name.lower() for x in ['udržení','záchran','o umístění'])

def dest(club):
    cn=norm(club)
    if cn in playoff_norm: return ('► play-off','d-po')
    if cn in udrzeni_norm: return ('► sk. o udržení','d-rel')
    return ('','')

def compute_terminal(blocks):
    t={}
    for bi,b in enumerate(blocks):
        for r in b['rows']: t[r['club']]=bi
    return t

def rtable(b, bi, terminal, show_dest=False):
    rows=''
    releg=is_releg(b['name'])
    for r in b['rows']:
        gf=r['gf'] if r['gf'] is not None else ''
        ga=r['ga'] if r['ga'] is not None else ''
        show_fate=(terminal.get(r['club'])==bi)
        fate=r['fate'] if show_fate else ''
        dcell=''
        if show_dest:
            dl,dcls=dest(r['club'])
            dcell=f'<td class="dest {dcls}">{dl}</td>'
        else:
            dcell='<td class="dest"></td>' if any('ákladní' in bb['name'] for bb in [b]) else ''
        rows+=f'''<tr class="{fc(fate)}"><td class="pos">{r['pos']}</td><td class="club">{r['club']} {bdg(r['note'])}</td><td class="num">{r['gp'] if r['gp'] is not None else ''}</td><td class="num">{r['w'] if r['w'] is not None else ''}</td><td class="num">{r['d'] if r['d'] is not None else ''}</td><td class="num">{r['l'] if r['l'] is not None else ''}</td><td class="num gd">{gf}:{ga}</td><td class="num pts">{r['body'] if r['body'] is not None else ''}</td>{dcell if show_dest else ''}<td class="fate">{fl(fate)}</td></tr>'''
    cls='block releg' if releg else 'block'
    tag='<span class="releg-tag">o udržení</span>' if releg else ''
    dhead='<th class="dest">Postupuje</th>' if show_dest else ''
    return f'''<div class="{cls}"><h3>{b['name']} {tag}</h3><table><thead><tr><th class="pos">#</th><th class="club">Klub</th><th class="num">Z</th><th class="num">V</th><th class="num">R</th><th class="num">P</th><th class="num gd">Skóre</th><th class="num pts">B</th>{dhead}<th class="fate">Osud</th></tr></thead><tbody>{rows}</tbody></table></div>'''

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

extra=D['extra']
term=compute_terminal(extra)
zc_html=''.join(rtable(b,bi,term,show_dest=('ákladní' in b['name'])) for bi,b in enumerate(extra))
po_html=po_bracket(D['po'],['Čtvrtfinále','Semifinále','Finále','O 3.místo','O 5.místo','O 5.-8.místo','O 7.místo','O 9.místo'])

html=f'''<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Sezóna 1988/89</title><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:#fbfbfa;color:#1a1a1a;line-height:1.45;padding:1.5rem 1rem 4rem;font-size:14px;}}
.wrap{{max-width:880px;margin:0 auto;}}
header{{border-bottom:2px solid #1a1a1a;padding-bottom:1rem;margin-bottom:1.5rem;}}
h1{{font-size:1.6rem;font-weight:700;}} .sub{{color:#555;font-size:0.85rem;margin-top:0.3rem;}}
.level{{margin-top:1.6rem;}}
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
.num{{text-align:center;width:32px;font-size:0.82rem;}} .gd{{width:62px;color:#555;}} .pts{{font-weight:700;width:34px;}}
.dest{{width:120px;font-size:0.68rem;font-weight:600;}}
.dest.d-po{{color:#2a5a8a;}} .dest.d-rel{{color:#b03030;}}
.fate{{width:70px;font-size:0.7rem;text-align:right;}}
tr.f-up{{background:#f0f7f0;}} tr.f-up .fate{{color:#2d7a32;font-weight:600;}}
tr.f-down{{background:#fbf0f0;}} tr.f-down .fate{{color:#b03030;font-weight:600;}}
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;padding:0.05rem 0.3rem;border-radius:2px;margin-left:0.2rem;}}
.badge.m{{background:#1a1a1a;color:#fff;}} .badge.n{{background:#2d7a32;color:#fff;}} .badge.s{{background:#b03030;color:#fff;}}
.po-wrap{{margin-top:1rem;background:#f4f6f8;border:1px solid #dde3e8;border-radius:4px;padding:0.8rem;}}
.po-head{{font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#2a4a6a;margin-bottom:0.7rem;}}
.po-bracket{{display:flex;gap:0.8rem;overflow-x:auto;padding-bottom:0.4rem;}}
.po-col{{min-width:170px;flex:1;}}
.po-phase{{font-size:0.66rem;text-transform:uppercase;color:#5a7088;font-weight:700;margin-bottom:0.4rem;text-align:center;}}
.po-series{{background:#fff;border:1px solid #d5dde4;border-radius:3px;margin-bottom:0.55rem;overflow:hidden;}}
.po-team{{display:flex;justify-content:space-between;padding:0.28rem 0.5rem;font-size:0.76rem;border-bottom:1px solid #eef1f4;}}
.po-team.po-win{{font-weight:700;background:#eaf5ea;}} .po-sc{{font-weight:700;margin-left:0.5rem;}}
.po-games{{font-size:0.62rem;color:#889;padding:0.2rem 0.5rem;background:#fafbfc;}}
.flow-note{{margin-top:0.7rem;font-size:0.72rem;color:#555;padding:0.5rem 0.7rem;background:#eef2f6;border-radius:3px;border-left:3px solid #2a5a8a;}}
.legend{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #ddd;font-size:0.72rem;color:#666;display:flex;flex-wrap:wrap;gap:0.8rem 1.5rem;}}
.legend b{{color:#1a1a1a;}} footer{{margin-top:1.5rem;font-size:0.7rem;color:#999;}}
</style></head><body><div class="wrap">
<header><h1>Lední hokej ČSSR — sezóna 1988/89</h1>
<div class="sub">I. liga 12 klubů · základní část → play-off (1.–8.) / skupina o udržení (9.–12.)</div></header>
<div class="level"><div class="level-head"><span class="lname">1. úroveň — I. liga</span><span class="lmeta">L10 · 12 klubů</span></div>
{zc_html}
<div class="flow-note">► <b>Návaznost:</b> týmy 1.–8. ze základní části postupují do <b style="color:#2a5a8a">play-off</b>, týmy 9.–12. do <b style="color:#b03030">skupiny o udržení</b>. Konečný osud (sestup) se rozhoduje až v těchto fázích.</div>
<div class="po-wrap"><div class="po-head">Play-off I. ligy → 🏆 Tesla Pardubice</div>{po_html}</div>
</div>
<div class="legend">
<span><b>Z</b> zápasy · <b>V</b> výhry · <b>R</b> remízy · <b>P</b> prohry · <b>B</b> body</span>
<span><b style="color:#2a5a8a">►</b> postup do fáze · <b style="color:#b03030">▮</b> skupina o udržení · <b style="color:#2a4a6a">⬛</b> play-off</span>
<span><b style="color:#2d7a32">▲</b> postup · <b style="color:#b03030">▼</b> sestup</span>
</div>
<footer>Data: Hokejový almanach (registr D42) · Mistr: Tesla Pardubice (4. titul)</footer>
</div></body></html>'''

with open('/mnt/user-data/outputs/sezona_1988_89.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"HTML 1988/89 ({len(html)} znaku)")
