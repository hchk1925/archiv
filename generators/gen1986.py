import json
with open('/tmp/s1986_data.json') as f: D = json.load(f)

def fc(f): return {'postup':'f-up','sestup':'f-down','reorganizace':'f-reorg','setrval':''}.get(f,'')
def fl(f): return {'postup':'▲ postup','sestup':'▼ sestup','reorganizace':'◆ reorg.','setrval':''}.get(f,'')
def bdg(n): return {'M':'<span class="badge m">M</span>','N':'<span class="badge n">N</span>','S':'<span class="badge s">S</span>'}.get(n,'')

# Detekce typu bloku
def is_relegation(name):
    n=name.lower()
    return any(x in n for x in ['udržení','záchran','o umístění','o 7','o 9','o 11'])
def is_basic(name):
    n=name.lower()
    return 'základní' in n or name.endswith('skupina A') or name.endswith('skupina B') or name.endswith('skupina C')

# KLICOVA LOGIKA: pro kazdou uroven najit terminalni blok kazdeho klubu
# fate zobrazit JEN u terminalniho (posledniho) bloku daneho klubu
def compute_terminal(blocks):
    """Vrati dict: club_name -> index posledniho bloku kde se klub objevi"""
    terminal = {}
    for bi, b in enumerate(blocks):
        for r in b['rows']:
            terminal[r['club']] = bi
    return terminal

def rtable_smart(b, bi, terminal):
    rows=''
    relegation = is_relegation(b['name'])
    for r in b['rows']:
        gf=r['gf'] if r['gf'] is not None else ''
        ga=r['ga'] if r['ga'] is not None else ''
        # fate zobrazit JEN pokud tento blok je terminalni pro klub
        show_fate = (terminal.get(r['club']) == bi)
        fate = r['fate'] if show_fate else ''
        rows+=f'''<tr class="{fc(fate)}"><td class="pos">{r['pos']}</td><td class="club">{r['club']} {bdg(r['note'])}</td><td class="num">{r['gp'] if r['gp'] is not None else ''}</td><td class="num">{r['w'] if r['w'] is not None else ''}</td><td class="num">{r['d'] if r['d'] is not None else ''}</td><td class="num">{r['l'] if r['l'] is not None else ''}</td><td class="num gd">{gf}:{ga}</td><td class="num pts">{r['body'] if r['body'] is not None else ''}</td><td class="fate">{fl(fate)}</td></tr>'''
    cls = 'block releg' if relegation else 'block'
    tag = '<span class="releg-tag">skupina o udržení</span>' if relegation else ''
    return f'''<div class="{cls}"><h3>{b['name']} {tag}</h3><table><thead><tr><th class="pos">#</th><th class="club">Klub</th><th class="num">Z</th><th class="num">V</th><th class="num">R</th><th class="num">P</th><th class="num gd">Skóre</th><th class="num pts">B</th><th class="fate">Osud</th></tr></thead><tbody>{rows}</tbody></table></div>'''

def render_level(blocks):
    terminal = compute_terminal(blocks)
    return ''.join(rtable_smart(b, bi, terminal) for bi, b in enumerate(blocks))

def po_bracket(series, phases):
    html='<div class="po-bracket">'
    for phase in phases:
        ph=[s for s in series if phase.lower() in s['node'].lower()]
        if not ph: continue
        html+=f'<div class="po-col"><div class="po-phase">{phase}</div>'
        for s in ph:
            t1,t2=s['t1'],s['t2']
            try:
                a,b=map(int,t1['sscore'].split(':')); w1=a>b
            except: w1=False
            html+=f'''<div class="po-series">
<div class="po-team {'po-win' if w1 else ''}">{t1['name']}<span class="po-sc">{t1['sscore'].split(':')[0] if ':' in str(t1['sscore']) else ''}</span></div>
<div class="po-team {'po-win' if not w1 else ''}">{t2['name']}<span class="po-sc">{t1['sscore'].split(':')[1] if ':' in str(t1['sscore']) else ''}</span></div>
<div class="po-games">{t1['games']}</div></div>'''
        html+='</div>'
    html+='</div>'
    return html

meta=D['meta']
extra_zc=render_level(D['extraliga'])
po_extra=po_bracket(D['po_extra'], ['Čtvrtfinále','Semifinále','Finále','O 3.místo','O 5.místo','O 7.místo'])
nhl1=render_level(D['nhl1'])
po_nhl1=po_bracket(D['po_nhl1'], ['čtvrtfinále','semifinále','finále','O 3.místo'])
nhl2=render_level(D['nhl2'])
kval=''.join(rtable_smart(b, bi, compute_terminal(D['kval'])) for bi,b in enumerate(D['kval']))

html=f'''<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Sezóna 1986/87</title><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:#fbfbfa;color:#1a1a1a;line-height:1.45;padding:1.5rem 1rem 4rem;font-size:14px;}}
.wrap{{max-width:880px;margin:0 auto;}}
header{{border-bottom:2px solid #1a1a1a;padding-bottom:1rem;margin-bottom:1.5rem;}}
h1{{font-size:1.6rem;font-weight:700;}} .sub{{color:#555;font-size:0.85rem;margin-top:0.3rem;}}
.meta-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0.4rem 1.5rem;margin-top:0.9rem;font-size:0.8rem;}}
.meta-grid div{{display:flex;justify-content:space-between;border-bottom:1px dotted #ccc;padding:0.15rem 0;}}
.meta-grid .k{{color:#777;}} .meta-grid .v{{font-weight:600;}}
.level{{margin-top:1.6rem;}}
.level-head{{display:flex;align-items:baseline;gap:0.6rem;background:#1a1a1a;color:#fff;padding:0.5rem 0.8rem;border-radius:3px 3px 0 0;}}
.level-head .lname{{font-size:1.05rem;font-weight:700;}} .level-head .lmeta{{font-size:0.72rem;color:#bbb;margin-left:auto;}}
.block,.kval-block{{margin-top:1rem;}} .block h3{{font-size:0.85rem;font-weight:600;color:#444;padding:0.4rem 0.2rem;border-bottom:1px solid #ddd;}}
.block.releg h3{{color:#b03030;border-bottom-color:#e0b0b0;}}
.releg-tag{{font-size:0.62rem;background:#b03030;color:#fff;padding:0.1rem 0.4rem;border-radius:2px;margin-left:0.4rem;text-transform:uppercase;letter-spacing:0.05em;vertical-align:middle;}}
.block.releg{{background:#fdf6f6;border-left:3px solid #b03030;border-radius:0 3px 3px 0;padding:0.2rem 0.6rem 0.5rem;}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;}}
th,td{{padding:0.3rem 0.4rem;text-align:left;}}
thead th{{font-size:0.66rem;text-transform:uppercase;letter-spacing:0.05em;color:#999;border-bottom:1px solid #ccc;}}
tbody tr{{border-bottom:1px solid #eee;}} tbody tr:hover{{background:#f0f0ee;}}
.pos{{width:28px;text-align:center;color:#999;font-size:0.8rem;}} .club{{font-weight:500;}}
.num{{text-align:center;width:34px;font-size:0.82rem;}} .gd{{width:64px;color:#555;}} .pts{{font-weight:700;width:36px;}}
.fate{{width:72px;font-size:0.7rem;text-align:right;}}
tr.f-up{{background:#f0f7f0;}} tr.f-up .fate{{color:#2d7a32;font-weight:600;}}
tr.f-down{{background:#fbf0f0;}} tr.f-down .fate{{color:#b03030;font-weight:600;}}
tr.f-reorg{{background:#fbf8ed;}} tr.f-reorg .fate{{color:#9a7d1a;}}
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;padding:0.05rem 0.3rem;border-radius:2px;margin-left:0.2rem;}}
.badge.m{{background:#1a1a1a;color:#fff;}} .badge.n{{background:#2d7a32;color:#fff;}} .badge.s{{background:#b03030;color:#fff;}}
.po-wrap{{margin-top:1rem;background:#f4f6f8;border:1px solid #dde3e8;border-radius:4px;padding:0.8rem;}}
.po-head{{font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#2a4a6a;margin-bottom:0.7rem;}}
.po-bracket{{display:flex;gap:0.8rem;overflow-x:auto;padding-bottom:0.4rem;}}
.po-col{{min-width:175px;flex:1;}}
.po-phase{{font-size:0.66rem;text-transform:uppercase;letter-spacing:0.06em;color:#5a7088;font-weight:700;margin-bottom:0.4rem;text-align:center;}}
.po-series{{background:#fff;border:1px solid #d5dde4;border-radius:3px;margin-bottom:0.55rem;overflow:hidden;}}
.po-team{{display:flex;justify-content:space-between;align-items:center;padding:0.28rem 0.5rem;font-size:0.76rem;border-bottom:1px solid #eef1f4;}}
.po-team.po-win{{font-weight:700;background:#eaf5ea;}}
.po-sc{{font-weight:700;margin-left:0.5rem;}}
.po-games{{font-size:0.62rem;color:#889;padding:0.2rem 0.5rem;background:#fafbfc;}}
.kval-zone{{margin:0.8rem 0;padding:0.6rem 0.8rem;background:#fdfaf3;border-left:3px solid #c89a3c;border-radius:0 3px 3px 0;}}
.kval-zone-head{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#9a7d1a;font-weight:700;margin-bottom:0.5rem;}}
.kval-zone-head::before{{content:'↕ ';}}
.note-principle{{margin-top:0.6rem;font-size:0.7rem;color:#777;font-style:italic;padding:0.4rem 0.6rem;background:#f6f6f4;border-radius:3px;}}
.legend{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #ddd;font-size:0.72rem;color:#666;display:flex;flex-wrap:wrap;gap:0.8rem 1.5rem;}}
.legend b{{color:#1a1a1a;}} footer{{margin-top:1.5rem;font-size:0.7rem;color:#999;}}
</style></head><body><div class="wrap">
<header><h1>Lední hokej ČSSR — sezóna 1986/87</h1>
<div class="sub">{meta.get('era_note','')}</div>
<div class="meta-grid">
<div><span class="k">Mistr</span><span class="v">Tesla Pardubice</span></div>
<div><span class="k">Bodování ZČ</span><span class="v">{meta.get('scoring_system','')}</span></div>
<div><span class="k">Klubů celkem</span><span class="v">{meta.get('total_clubs','')}</span></div>
<div><span class="k">Předchozí sezóna</span><span class="v">1985/86</span></div>
</div></header>

<div class="level"><div class="level-head"><span class="lname">1. úroveň — I. liga</span><span class="lmeta">L10 · 12 klubů</span></div>
{extra_zc}
<div class="po-wrap"><div class="po-head">Play-off I. ligy</div>{po_extra}</div>
</div>

<div class="kval-zone"><div class="kval-zone-head">Baráž o I. ligu · L15</div>
<div style="font-size:0.78rem;color:#7a6418;padding:0.3rem 0;">Kvalifikace o 1. CHL: TJ Plastika Nitra – TJ Poldi SONP Kladno 0:3</div>
</div>

<div class="level"><div class="level-head"><span class="lname">2. úroveň — I. ČNHL + I. SNHL</span><span class="lmeta">L20 · ZČ + play-off + sk. o udržení</span></div>
{nhl1}
<div class="po-wrap"><div class="po-head">Play-off I. ČNHL</div>{po_nhl1}</div>
</div>

<div class="kval-zone"><div class="kval-zone-head">Kvalifikace o 2. ČNHL / 2. SNHL · L35</div>{kval}</div>

<div class="level"><div class="level-head"><span class="lname">3. úroveň — II. ČNHL + II. SNHL</span><span class="lmeta">L30 · skupiny + finále</span></div>
{nhl2}
</div>

<div class="note-principle">Princip zobrazení: <b>postup/sestup</b> je vyznačen pouze u <b>terminální fáze</b>, ve které k němu reálně došlo — nikoli u základní části. Týmy na 9.–12. místě postupují do <b>skupiny o udržení</b>, sestup se rozhoduje až tam.</div>

<div class="legend">
<span><b>Z</b> zápasy · <b>V</b> výhry · <b>R</b> remízy · <b>P</b> prohry · <b>B</b> body (2-1-0)</span>
<span><span class="badge m">M</span> mistr · <span class="badge n">N</span> nováček</span>
<span><b style="color:#2d7a32">▲</b> postup · <b style="color:#b03030">▼</b> sestup · <b style="color:#9a7d1a">◆</b> reorg.</span>
<span><b style="color:#b03030">▮</b> skupina o udržení · <b style="color:#2a4a6a">⬛</b> play-off · <b style="color:#9a7d1a">↕</b> baráž</span>
</div>
<footer>Data: Hokejový almanach (registr D42) · {meta.get('note','')}</footer>
</div></body></html>'''

with open('/mnt/user-data/outputs/sezona_1986_87.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"HTML opraveno ({len(html)} znaku)")

# Validace - Karviná
terminal_nhl1 = compute_terminal(D['nhl1'])
print(f"\nKarviná terminalni blok: index {terminal_nhl1.get('TJ Baník ČSA Karviná')}")
for bi, b in enumerate(D['nhl1']):
    for r in b['rows']:
        if 'Karviná' in r['club']:
            show = terminal_nhl1.get(r['club']) == bi
            print(f"  Blok {bi} [{b['name'][:35]}]: Karviná fate={r['fate']} → ZOBRAZIT={show}")
