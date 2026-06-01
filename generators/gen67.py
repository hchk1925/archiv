import json, re
with open('/tmp/s1967.json') as f: D=json.load(f)

def fc(f): return {'postup':'f-up','sestup':'f-down','reorganizace':'f-reorg'}.get(f,'')
def fl(f): return {'postup':'▲ postup','sestup':'▼ sestup','reorganizace':'◆ reorg.'}.get(f,'')
def bdg(n): return {'M':'<span class="badge m">M</span>','N':'<span class="badge n">N</span>','S':'<span class="badge s">S</span>'}.get(n,'')
def is_releg(n): return any(x in n.lower() for x in ['udržení','záchran'])
def is_baraz(n): return any(x in n.lower() for x in ['kvalifikace','baráž','prolínací'])
def short(n):
    p=[x for x in n.split(' / ') if x.strip()]
    return p[-1] if p else n
def compute_terminal(blocks):
    t={}
    for bi,b in enumerate(blocks):
        for r in b['rows']: t[r['club']]=bi
    return t
def clean_fate(f,baraz):
    f=(f or '').replace('?','').strip()
    if baraz: return f if f in ('postup','sestup') else ''
    return f

def rtable(b,bi,term,compact=False):
    rows=''; releg=is_releg(b['name']); baraz=is_baraz(b['name'])
    if baraz: releg=False
    for r in b['rows']:
        gf=r['gf'] if r['gf'] is not None else ''
        ga=r['ga'] if r['ga'] is not None else ''
        raw=r['fate'] if term.get(r['club'])==bi else ''
        fate=clean_fate(raw,baraz)
        rows+=f'''<tr class="{fc(fate)}"><td class="pos">{r['pos']}</td><td class="club">{r['club']} {bdg(r['note'])}</td><td class="num">{r['gp'] if r['gp'] is not None else ''}</td><td class="num">{r['w'] if r['w'] is not None else ''}</td><td class="num">{r['d'] if r['d'] is not None else ''}</td><td class="num">{r['l'] if r['l'] is not None else ''}</td><td class="num gd">{gf}:{ga}</td><td class="num pts">{r['body'] if r['body'] is not None else ''}</td><td class="fate">{fl(fate)}</td></tr>'''
    cls='block'+(' releg' if releg else '')+(' baraz' if baraz else '')
    tag=''
    if releg: tag='<span class="releg-tag">o udržení</span>'
    elif baraz: tag='<span class="baraz-tag">baráž ↕</span>'
    return f'''<div class="{cls}"><h3>{short(b['name'])} {tag}</h3><table><thead><tr><th class="pos">#</th><th class="club">Klub</th><th class="num">Z</th><th class="num">V</th><th class="num">R</th><th class="num">P</th><th class="num gd">Skóre</th><th class="num pts">B</th><th class="fate">Osud</th></tr></thead><tbody>{rows}</tbody></table></div>'''

def render(blocks):
    t=compute_terminal(blocks)
    return ''.join(rtable(b,bi,t) for bi,b in enumerate(blocks))

extra=render(D['extra'])
ii=render(D['iiliga'])
# KVAL - rozdelit: kval o ligu (L15 baraz) + kval o 2.ligu
kval_liga=[b for b in D['kval'] if 'ligu (l15)' in b['name'].lower() or 'o ligu' in b['name'].lower()]
kval_2liga=[b for b in D['kval'] if b not in kval_liga]
baraz_liga=render(kval_liga) if kval_liga else ''
kval_2=render(kval_2liga) if kval_2liga else ''

# Kraje - hlavni blok kazdeho kraje (prvni "Krajský přebor" nebo prvni blok)
kraje_html=''
for kraj,blocks in D['kraje'].items():
    if not blocks: continue
    # vzit jen prvni blok s radky (hlavni krajsky prebor)
    main=blocks[0]
    t=compute_terminal(blocks)
    kraje_html+=f'<div class="kraj-box"><div class="kraj-name">{kraj}</div>{rtable(main,0,t)}</div>'

html=f'''<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Sezóna 1967/68</title><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:#fbfbfa;color:#1a1a1a;line-height:1.45;padding:1.5rem 1rem 4rem;font-size:14px;}}
.wrap{{max-width:880px;margin:0 auto;}}
header{{border-bottom:2px solid #1a1a1a;padding-bottom:1rem;margin-bottom:1.2rem;}}
h1{{font-size:1.6rem;font-weight:700;}} .sub{{color:#555;font-size:0.85rem;margin-top:0.3rem;}}
.meta-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0.4rem 1.5rem;margin-top:0.9rem;font-size:0.8rem;}}
.meta-grid div{{display:flex;justify-content:space-between;border-bottom:1px dotted #ccc;padding:0.15rem 0;}}
.meta-grid .k{{color:#777;}} .meta-grid .v{{font-weight:600;}}
.level{{margin-top:1.8rem;}}
.level-head{{display:flex;align-items:baseline;gap:0.6rem;background:#1a1a1a;color:#fff;padding:0.5rem 0.8rem;border-radius:3px 3px 0 0;}}
.level-head .lname{{font-size:1.05rem;font-weight:700;}} .level-head .lmeta{{font-size:0.72rem;color:#bbb;margin-left:auto;}}
.block{{margin-top:1rem;}} .block h3{{font-size:0.82rem;font-weight:600;color:#444;padding:0.4rem 0.2rem;border-bottom:1px solid #ddd;}}
.block.releg h3{{color:#b03030;}} .block.releg{{background:#fdf6f6;border-left:3px solid #b03030;border-radius:0 3px 3px 0;padding:0.2rem 0.6rem 0.5rem;}}
.releg-tag{{font-size:0.6rem;background:#b03030;color:#fff;padding:0.1rem 0.4rem;border-radius:2px;margin-left:0.4rem;text-transform:uppercase;vertical-align:middle;}}
.baraz-tag{{font-size:0.6rem;background:#c89a3c;color:#fff;padding:0.1rem 0.4rem;border-radius:2px;margin-left:0.4rem;text-transform:uppercase;vertical-align:middle;}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;}}
th,td{{padding:0.3rem 0.4rem;text-align:left;}}
thead th{{font-size:0.64rem;text-transform:uppercase;letter-spacing:0.04em;color:#999;border-bottom:1px solid #ccc;}}
tbody tr{{border-bottom:1px solid #eee;}} tbody tr:hover{{background:#f0f0ee;}}
.pos{{width:24px;text-align:center;color:#999;font-size:0.8rem;}} .club{{font-weight:500;}}
.num{{text-align:center;width:32px;font-size:0.8rem;}} .gd{{width:60px;color:#555;}} .pts{{font-weight:700;width:32px;}}
.fate{{width:66px;font-size:0.68rem;text-align:right;}}
tr.f-up{{background:#f0f7f0;}} tr.f-up .fate{{color:#2d7a32;font-weight:600;}}
tr.f-down{{background:#fbf0f0;}} tr.f-down .fate{{color:#b03030;font-weight:600;}}
.badge{{display:inline-block;font-size:0.58rem;font-weight:700;padding:0.05rem 0.28rem;border-radius:2px;margin-left:0.2rem;}}
.badge.m{{background:#1a1a1a;color:#fff;}} .badge.n{{background:#2d7a32;color:#fff;}} .badge.s{{background:#b03030;color:#fff;}}
.kval-zone{{margin:1.4rem 0;padding:0.6rem 0.8rem;background:#fdfaf3;border-left:3px solid #c89a3c;border-radius:0 3px 3px 0;}}
.kval-zone-head{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#9a7d1a;font-weight:700;margin-bottom:0.3rem;}}
.kval-zone-head::before{{content:'↕ ';}}
.kraje-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:1rem;margin-top:1rem;}}
.kraj-box{{border:1px solid #e5e5e2;border-radius:4px;padding:0.5rem 0.7rem;background:#fff;}}
.kraj-name{{font-size:0.8rem;font-weight:700;color:#2a4a3a;margin-bottom:0.2rem;}}
.kraj-box table{{font-size:0.78rem;}} .kraj-box .gd{{width:54px;}}
.legend{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #ddd;font-size:0.72rem;color:#666;display:flex;flex-wrap:wrap;gap:0.8rem 1.5rem;}}
.legend b{{color:#1a1a1a;}} footer{{margin-top:1.5rem;font-size:0.7rem;color:#999;}}
</style></head><body><div class="wrap">
<header><h1>Lední hokej ČSSR — sezóna 1967/68</h1>
<div class="sub">Liga 10 týmů · II. liga 4×8 + kvalifikace · bez play-off (vítěz ZČ = mistr)</div>
<div class="meta-grid">
<div><span class="k">Mistr</span><span class="v">Dukla Jihlava</span></div>
<div><span class="k">Bodování</span><span class="v">2-1-0</span></div>
<div><span class="k">Klubů celkem</span><span class="v">653</span></div>
<div><span class="k">Krajů</span><span class="v">11</span></div>
</div></header>

<div class="level"><div class="level-head"><span class="lname">1. úroveň — I. liga</span><span class="lmeta">L10 · 10 klubů</span></div>
{extra}
</div>

<div class="kval-zone"><div class="kval-zone-head">Kvalifikace o I. ligu · L15 (baráž)</div>
{baraz_liga}
<div style="font-size:0.72rem;color:#7a6418;padding:0.3rem 0;">Motor České Budějovice a VŽKG Ostrava postoupily do I. ligy. Týmy z II. ligy, které nepostoupily, zůstávají (bez osudu).</div>
</div>

<div class="level"><div class="level-head"><span class="lname">2. úroveň — II. liga</span><span class="lmeta">L20 · 4 skupiny A–D (4×8)</span></div>
{ii}
</div>

<div class="kval-zone"><div class="kval-zone-head">Kvalifikace o postup do II. ligy (mezi II. ligou a kraji)</div>{kval_2}</div>

<div class="level"><div class="level-head"><span class="lname">3. úroveň — Krajské přebory</span><span class="lmeta">L40 · 11 krajů</span></div>
<div class="kraje-grid">{kraje_html}</div>
</div>

<div class="legend">
<span><b>Z</b> zápasy · <b>V</b> výhry · <b>R</b> remízy · <b>P</b> prohry · <b>B</b> body (2-1-0)</span>
<span><span class="badge m">M</span> mistr · <span class="badge n">N</span> nováček · <span class="badge s">S</span> sestup</span>
<span><b style="color:#2d7a32">▲</b> postup · <b style="color:#b03030">▼</b> sestup · <b style="color:#c89a3c">↕</b> baráž (z nižší bez postupu = bez osudu)</span>
</div>
<footer>Data: Hokejový almanach (registr D42) · Mistr: Dukla Jihlava · Sestup: VTŽ Chomutov</footer>
</div></body></html>'''

with open('/mnt/user-data/outputs/sezona_1967_68.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"HTML 67/68 ({len(html)} znaku)")
