import openpyxl
wb=openpyxl.load_workbook('work/S1948_49_FINAL.xlsx',data_only=True,read_only=True)
def bdg(n): return {'M':'<span class="badge m">M</span>'}.get(n,'')
def fl(f): return {'postup':'▲ postup','sestup':'▼ sestup'}.get(f,'')
def fc(f): return {'postup':'f-up','sestup':'f-down'}.get(f,'')

extra=''
for r in wb['10_liga'].iter_rows(values_only=True):
    if r and r[0]=='T':
        extra+=f'''<tr class="{fc(r[20])}"><td class="pos">{r[2]}</td><td class="club">{r[3]} {bdg(r[4])}</td><td class="num">{r[5]}</td><td class="num">{r[6]}</td><td class="num">{r[7]}</td><td class="num">{r[8]}</td><td class="num gd">{r[9]}:{r[11]}</td><td class="num pts">{r[12]}</td><td class="fate">{fl(r[20])}</td></tr>'''

kval=''
for r in wb['KVAL'].iter_rows(values_only=True):
    if r and r[0]=='T':
        f='postup' if r[2] in ('1','2') else ''
        kval+=f'''<tr class="{fc(f)}"><td class="pos">{r[2]}</td><td class="club">{r[3]}</td><td class="num">{r[5]}</td><td class="num">{r[6]}</td><td class="num">{r[7]}</td><td class="num">{r[8]}</td><td class="num pts">{r[12]}</td><td class="fate">{fl(f)}</td></tr>'''
wb.close()

html=f'''<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Sezóna 1948/49</title><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,"Segoe UI",system-ui,sans-serif;background:#fbfbfa;color:#1a1a1a;line-height:1.45;padding:1.5rem 1rem 4rem;font-size:14px;}}
.wrap{{max-width:760px;margin:0 auto;}}
header{{border-bottom:2px solid #1a1a1a;padding-bottom:1rem;margin-bottom:1.2rem;}}
h1{{font-size:1.6rem;font-weight:700;}} .sub{{color:#555;font-size:0.85rem;margin-top:0.3rem;}}
.meta-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0.4rem 1.5rem;margin-top:0.9rem;font-size:0.8rem;}}
.meta-grid div{{display:flex;justify-content:space-between;border-bottom:1px dotted #ccc;padding:0.15rem 0;}}
.meta-grid .k{{color:#777;}} .meta-grid .v{{font-weight:600;}}
.level{{margin-top:1.8rem;}}
.level-head{{display:flex;align-items:baseline;gap:0.6rem;background:#1a1a1a;color:#fff;padding:0.5rem 0.8rem;border-radius:3px 3px 0 0;}}
.level-head .lname{{font-size:1.05rem;font-weight:700;}} .level-head .lmeta{{font-size:0.72rem;color:#bbb;margin-left:auto;}}
.block{{margin-top:1rem;}} .block h3{{font-size:0.82rem;font-weight:600;color:#444;padding:0.4rem 0.2rem;border-bottom:1px solid #ddd;}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;}}
th,td{{padding:0.32rem 0.4rem;text-align:left;}}
thead th{{font-size:0.66rem;text-transform:uppercase;letter-spacing:0.05em;color:#999;border-bottom:1px solid #ccc;}}
tbody tr{{border-bottom:1px solid #eee;}} tbody tr:hover{{background:#f0f0ee;}}
.pos{{width:28px;text-align:center;color:#999;font-size:0.8rem;}} .club{{font-weight:500;}}
.num{{text-align:center;width:36px;font-size:0.82rem;}} .gd{{width:64px;color:#555;}} .pts{{font-weight:700;width:38px;}}
.fate{{width:72px;font-size:0.7rem;text-align:right;}}
tr.f-up{{background:#f0f7f0;}} tr.f-up .fate{{color:#2d7a32;font-weight:600;}}
tr.f-down{{background:#fbf0f0;}} tr.f-down .fate{{color:#b03030;font-weight:600;}}
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;padding:0.05rem 0.3rem;border-radius:2px;margin-left:0.2rem;background:#1a1a1a;color:#fff;}}
.kval-zone{{margin:1.4rem 0;padding:0.6rem 0.8rem;background:#fdfaf3;border-left:3px solid #c89a3c;border-radius:0 3px 3px 0;}}
.kval-zone-head{{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;color:#9a7d1a;font-weight:700;margin-bottom:0.3rem;}}
.kval-zone-head::before{{content:'↕ ';}}
.data-warn{{margin-top:0.7rem;font-size:0.72rem;color:#7a5a00;padding:0.5rem 0.7rem;background:#fdf6e3;border-radius:3px;border-left:3px solid #d4a017;}}
.chain-note{{margin-top:0.7rem;font-size:0.72rem;color:#2a5a3a;padding:0.5rem 0.7rem;background:#eef6f0;border-radius:3px;border-left:3px solid #2d7a32;}}
.legend{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #ddd;font-size:0.72rem;color:#666;display:flex;flex-wrap:wrap;gap:0.8rem 1.5rem;}}
.legend b{{color:#1a1a1a;}} footer{{margin-top:1.5rem;font-size:0.7rem;color:#999;}}
</style></head><body><div class="wrap">
<header><h1>Lední hokej ČSR — sezóna 1948/49</h1>
<div class="sub">Státní liga (6. ročník) · 8 týmů jednokolově · poslední 2 sestup · <b>nově přidaná sezóna</b></div>
<div class="meta-grid">
<div><span class="k">Mistr</span><span class="v">LTC Praha</span></div>
<div><span class="k">Bodování</span><span class="v">2-1-0</span></div>
<div><span class="k">Zdroj</span><span class="v">Wikipedia (en)</span></div>
<div><span class="k">Stav</span><span class="v">republiková úroveň</span></div>
</div></header>

<div class="level"><div class="level-head"><span class="lname">1. úroveň — Státní liga</span><span class="lmeta">L10 · 8 týmů</span></div>
<div class="block"><h3>Konečná tabulka</h3>
<table><thead><tr><th class="pos">#</th><th class="club">Klub</th><th class="num">Z</th><th class="num">V</th><th class="num">R</th><th class="num">P</th><th class="num gd">Skóre</th><th class="num pts">B</th><th class="fate">Osud</th></tr></thead>
<tbody>{extra}</tbody></table></div>
<div class="chain-note">► <b>Návaznost (chain):</b> mistr LTC Praha → v 1949/50 jako „Zdar LTC Praha"; ATK Praha → mistr 1949/50; ŠK Bratislava → NV Bratislava (přejmenování po únoru 1948). Posledních 8 klubů navázáno na S1949_50 přes prev_club_id.</div>
</div>

<div class="kval-zone"><div class="kval-zone-head">Kvalifikace o ligu · L15 (finálová skupina)</div>
<div class="block"><table><thead><tr><th class="pos">#</th><th class="club">Klub</th><th class="num">Z</th><th class="num">V</th><th class="num">R</th><th class="num">P</th><th class="num pts">B</th><th class="fate">Osud</th></tr></thead>
<tbody>{kval}</tbody></table></div>
<div class="data-warn">⚠ <b>Datová poznámka:</b> u kvalifikace Wiki uvádí jen body a gólový rozdíl; Z/V/R/P dopočteno z bodů (2-1-0), skóre GF:GA chybí. Královo Pole a Vítkovické železárny postoupily do I. ligy 1949/50.</div>
</div>

<div class="legend">
<span><b>Z</b> zápasy · <b>V</b> výhry · <b>R</b> remízy · <b>P</b> prohry · <b>B</b> body (2-1-0)</span>
<span><span class="badge">M</span> mistr · <b style="color:#2d7a32">▲</b> postup · <b style="color:#b03030">▼</b> sestup · <b style="color:#c89a3c">↕</b> kvalifikace</span>
</div>
<footer>Data: Hokejový almanach (registr D42) · 1948/49 nově přidána z Wikipedie · regiony čekají na podklady</footer>
</div></body></html>'''
with open('/mnt/user-data/outputs/sezona_1948_49.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"HTML 1948/49 ({len(html)} znaku)")
