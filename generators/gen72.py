import json, re
with open('/tmp/s1972_full.json') as f: D=json.load(f)

def fc(f): return {'postup':'f-up','sestup':'f-down','reorganizace':'f-reorg'}.get(f,'')
def fl(f): return {'postup':'▲ postup','sestup':'▼ sestup','reorganizace':'◆ reorg.'}.get(f,'')
def bdg(n): return {'M':'<span class="badge m">M</span>','N':'<span class="badge n">N</span>','S':'<span class="badge s">S</span>'}.get(n,'')
def is_releg(name): return any(x in name.lower() for x in ['udržení','záchran'])
def is_basic(name): return 'ákladní' in name.lower()
def is_baraz(name): return any(x in name.lower() for x in ['prolínací','kvalifikace','baráž'])

def compute_terminal(blocks):
    t={}
    for bi,b in enumerate(blocks):
        for r in b['rows']: t[r['club']]=bi
    return t

def clean_fate(fate, baraz):
    """V barázi: jen postup/sestup; setrval a nejistoty → skryt (NIC)."""
    f=(fate or '').replace('?','').strip()
    if baraz:
        # tým z nižší co neuspěl = setrval = NIC; jen reálné postupy/sestupy
        return f if f in ('postup','sestup') else ''
    return f

def short_name(name):
    parts=[p for p in name.split(' / ') if p.strip()]
    return parts[-1] if parts else name

def rtable(b, bi, terminal):
    rows=''; releg=is_releg(b['name']); basic=is_basic(b['name']); baraz=is_baraz(b['name'])
    disp_name=short_name(b['name'])
    for r in b['rows']:
        gf=r['gf'] if r['gf'] is not None else ''
        ga=r['ga'] if r['ga'] is not None else ''
        if basic:
            fate=''  # zakl.cast s navaznosti = bez osudu (ale 72/73 nema oddelenou ZC)
        else:
            raw = r['fate'] if terminal.get(r['club'])==bi else ''
            fate = clean_fate(raw, baraz)
        rows+=f'''<tr class="{fc(fate)}"><td class="pos">{r['pos']}</td><td class="club">{r['club']} {bdg(r['note'])}</td><td class="num">{r['gp'] if r['gp'] is not None else ''}</td><td class="num">{r['w'] if r['w'] is not None else ''}</td><td class="num">{r['d'] if r['d'] is not None else ''}</td><td class="num">{r['l'] if r['l'] is not None else ''}</td><td class="num gd">{gf}:{ga}</td><td class="num pts">{r['body'] if r['body'] is not None else ''}</td><td class="fate">{fl(fate)}</td></tr>'''
    if baraz: releg=False  # baraz ma prednost (nazev z hierarchie muze obsahovat 'udrzeni')
    cls='block baraz' if baraz else ('block releg' if releg else 'block')
    tag=''
    if releg: tag='<span class="releg-tag">o udržení</span>'
    elif baraz: tag='<span class="baraz-tag">baráž ↕</span>'
    return f'''<div class="{cls}"><h3>{disp_name} {tag}</h3><table><thead><tr><th class="pos">#</th><th class="club">Klub</th><th class="num">Z</th><th class="num">V</th><th class="num">R</th><th class="num">P</th><th class="num gd">Skóre</th><th class="num pts">B</th><th class="fate">Osud</th></tr></thead><tbody>{rows}</tbody></table></div>'''

def render_level(blocks):
    term=compute_terminal(blocks)
    return ''.join(rtable(b,bi,term) for bi,b in enumerate(blocks))

meta=D['meta']
extra=render_level(D['extra'])
# II.liga - oddelit prolínací do baraz zony
ii_main=[b for b in D['iiliga'] if not is_baraz(b['name'])]
ii_baraz=[b for b in D['iiliga'] if is_baraz(b['name'])]
iiliga=render_level(ii_main)
iiliga_baraz=render_level(ii_baraz) if ii_baraz else ''
divize=render_level(D['divize'])
# KVAL - rozdelit
kval_cnhl=[b for b in D['kval'] if 'ČNHL' in b['name']]
kval_div=[b for b in D['kval'] if 'divizi' in b['name'].lower()]
cnhl_h=render_level(kval_cnhl)
divkval_h=render_level(kval_div)

def short(name):
    p=name.split(' / ')
    return p[-1] if p[-1] else (p[-2] if len(p)>1 else name)

html=f'''<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Sezóna 1972/73</title><style>
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
.releg-tag{{font-size:0.62rem;background:#b03030;color:#fff;padding:0.1rem 0.4rem;border-radius:2px;margin-left:0.4rem;text-transform:uppercase;vertical-align:middle;}}
.baraz-tag{{font-size:0.62rem;background:#c89a3c;color:#fff;padding:0.1rem 0.4rem;border-radius:2px;margin-left:0.4rem;text-transform:uppercase;vertical-align:middle;}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;}}
th,td{{padding:0.3rem 0.4rem;text-align:left;}}
thead th{{font-size:0.66rem;text-transform:uppercase;letter-spacing:0.05em;color:#999;border-bottom:1px solid #ccc;}}
tbody tr{{border-bottom:1px solid #eee;}} tbody tr:hover{{background:#f0f0ee;}}
.pos{{width:26px;text-align:center;color:#999;font-size:0.8rem;}} .club{{font-weight:500;}}
.num{{text-align:center;width:34px;font-size:0.82rem;}} .gd{{width:62px;color:#555;}} .pts{{font-weight:700;width:34px;}}
.fate{{width:70px;font-size:0.7rem;text-align:right;}}
tr.f-up{{background:#f0f7f0;}} tr.f-up .fate{{color:#2d7a32;font-weight:600;}}
tr.f-down{{background:#fbf0f0;}} tr.f-down .fate{{color:#b03030;font-weight:600;}}
tr.f-reorg{{background:#fbf8ed;}} tr.f-reorg .fate{{color:#9a7d1a;}}
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;padding:0.05rem 0.3rem;border-radius:2px;margin-left:0.2rem;}}
.badge.m{{background:#1a1a1a;color:#fff;}} .badge.n{{background:#2d7a32;color:#fff;}} .badge.s{{background:#b03030;color:#fff;}}
.kval-zone{{margin:1.4rem 0;padding:0.6rem 0.8rem;background:#fdfaf3;border-left:3px solid #c89a3c;border-radius:0 3px 3px 0;}}
.kval-zone-head{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#9a7d1a;font-weight:700;margin-bottom:0.3rem;}}
.kval-zone-head::before{{content:'↕ ';}}
.flow-note{{margin-top:0.7rem;font-size:0.72rem;color:#555;padding:0.5rem 0.7rem;background:#eef2f6;border-radius:3px;border-left:3px solid #5a7088;}}
.legend{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #ddd;font-size:0.72rem;color:#666;display:flex;flex-wrap:wrap;gap:0.8rem 1.5rem;}}
.legend b{{color:#1a1a1a;}} footer{{margin-top:1.5rem;font-size:0.7rem;color:#999;}}
</style></head><body><div class="wrap">
<header><h1>Lední hokej ČSSR — sezóna 1972/73</h1>
<div class="sub">{meta.get('era_note','')}</div>
<div class="meta-grid">
<div><span class="k">Mistr</span><span class="v">Tesla Pardubice</span></div>
<div><span class="k">Bodování</span><span class="v">{meta.get('scoring_system','')}</span></div>
<div><span class="k">Systém</span><span class="v">bez play-off (vítěz ZČ = mistr)</span></div>
<div><span class="k">Klubů celkem</span><span class="v">{meta.get('total_clubs','')}</span></div>
</div></header>

<div class="level"><div class="level-head"><span class="lname">1. úroveň — I. liga</span><span class="lmeta">L10 · 10 klubů · jednofázová (každý s každým)</span></div>
{extra}
</div>

<div class="kval-zone"><div class="kval-zone-head">Prolínací soutěž o I. ligu · L15 (baráž extraliga × 1. liga)</div>
{iiliga_baraz}
<div class="flow-note" style="border-color:#c89a3c;background:#fdfaf3;">► Týmy z <b>I. ligy</b> (extraligy) brání příslušnost, týmy z <b>1. ligy</b> útočí na postup. Tým z nižší soutěže, který nepostoupí, <b>zůstává</b> (nesestoupil — bez osudu).</div>
</div>

<div class="level"><div class="level-head"><span class="lname">2. úroveň — II. liga</span><span class="lmeta">L20 · skupiny A / B / 1.SNHL</span></div>
{iiliga}
</div>

<div class="kval-zone"><div class="kval-zone-head">Kvalifikace o postup do nové ČNHL · L25 (přechod na systém 1973/74)</div>{cnhl_h}</div>

<div class="level"><div class="level-head"><span class="lname">3. úroveň — Divize</span><span class="lmeta">L30 · 8 skupin</span></div>
{divize}
</div>

<div class="kval-zone"><div class="kval-zone-head">Kvalifikace o divizi · (baráž divize × kraj)</div>{divkval_h}</div>

<div class="legend">
<span><b>Z</b> zápasy · <b>V</b> výhry · <b>R</b> remízy · <b>P</b> prohry · <b>B</b> body (2-1-0)</span>
<span><span class="badge m">M</span> mistr · <span class="badge n">N</span> nováček · <span class="badge s">S</span> sestup</span>
<span><b style="color:#2d7a32">▲</b> postup · <b style="color:#b03030">▼</b> sestup · <b style="color:#9a7d1a">◆</b> reorg.</span>
<span><b style="color:#c89a3c">↕</b> baráž/kvalifikace — tým z nižší bez postupu = bez osudu</span>
</div>
<footer>Data: Hokejový almanach (registr D42) · {meta.get('note','')}</footer>
</div></body></html>'''

with open('/mnt/user-data/outputs/sezona_1972_73.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"HTML 72/73 ({len(html)} znaku)")

# Validace baraz
print("\n=== Prolínací soutěž — osud po opravě ===")
for b in ii_baraz:
    term=compute_terminal(ii_baraz)
    for bi2,bb in enumerate(ii_baraz):
        if bb is b:
            for r in b['rows']:
                raw=r['fate'] if term.get(r['club'])==bi2 else ''
                cleaned=clean_fate(raw, True)
                print(f"  {r['club'][:28]:<28} data='{r['fate']}' → zobrazeno='{cleaned or '(nic)'}'")
