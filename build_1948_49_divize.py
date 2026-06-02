#!/usr/bin/env python3
"""
build_1948_49_divize.py — doplní VŠECHNY divize 1948/49 z PDF (in-place, idempotent).

Struktura (z DS PDF): krajské skupiny A/B → krajská finále → celostátní play-off
(Semifinálové skupiny A/B → Finálová skupina). Vítěz divize: ZSJ GZ Královo Pole.
Slovenská oblastná liga má nekompletní tabulky (autor to označuje).

Středočeská divize + nejvyšší soutěž už řeší enrich_1948_49.py; tento skript přidává
Západočeskou, Východočeskou, Moravskoslezskou, Slovenskou + play-off + finále + notes.
Vše ověřeno: suma GF=GA, body=2·V+R (kromě nekompletních SVK — označeno).
"""
import openpyxl, re
from openpyxl.utils import get_column_letter

PATH = 'data/S1948_49_FINAL.xlsx'
S = 'S1948_49'
HDR10 = ['row_type', 'block_name', 'pos', 'club_name', 'note', 'GP', 'W', 'D', 'L',
         'GF', ':', 'GA', 'PTS', 'comp_path', 'node_id', 'level', 'club_id',
         'prev_club_id', 'dest_node_id', 'dest_type', 'season_fate', 'tr_id', 'district']

# raw_name, GP,W,D,L,GF,GA,PTS, city
ZAPC_A = [('JTO Sokol Holoubkov',5,4,1,0,35,15,9,'Holoubkov'),
          ('JTO Sokol Čechie Horní Litvínov',5,4,0,1,26,19,8,'Horní Litvínov'),
          ('JTO Sokol Čechie Louny',5,3,0,2,28,18,6,'Louny'),
          ('JTO Sokol Viktoria Osek (u Rokycan)',5,2,0,3,21,24,4,'Osek'),
          ('JTO Sokol Volduchy',5,1,0,4,18,37,2,'Volduchy'),
          ('JTO Sokol Ústí nad Labem',5,0,1,4,12,27,1,'Ústí nad Labem')]
ZAPC_B = [('JTO Sokol II Meteor České Budějovice',6,6,0,0,52,20,12,'České Budějovice'),
          ('JTO Sokol Tábor',6,4,1,1,39,19,9,'Tábor'),
          ('JTO Sokol Felbabka',6,3,2,1,34,29,8,'Felbabka'),
          ('JTO Sokol Horymír Neumětely',6,2,1,3,36,40,5,'Neumětely'),
          ('JTO Sokol Blatná',6,2,0,4,32,45,4,'Blatná'),
          ('JTO Sokol Písek',6,1,1,4,19,40,3,'Písek'),
          ('JTO Sokol Rožmitál pod Třemšínem',6,0,1,5,16,35,1,'Rožmitál pod Třemšínem')]
VYCH_A = [('JTO Sokol I Pardubice',5,4,1,0,38,15,9,'Pardubice'),
          ('JTO Sokol Havlíčkův Brod',5,3,1,1,29,29,7,'Havlíčkův Brod'),
          ('ZSJ Dekva Třebíč',5,3,0,2,40,27,6,'Třebíč'),
          ('JTO Sokol Svítkov',5,2,0,3,37,26,4,'Pardubice'),
          ('JTO Sokol Choltice',5,1,0,4,17,40,2,'Choltice'),
          ('JTO Sokol Okříšky',5,1,0,4,18,42,2,'Okříšky')]
VYCH_B = [('JTO Sokol Mladá Boleslav',5,4,1,0,28,7,9,'Mladá Boleslav'),
          ('JTO Sokol Meteor Svobodné Dvory',5,3,1,1,31,22,7,'Svobodné Dvory'),
          ('ZSJ VČE Slavia Hradec Králové',5,2,1,2,12,14,5,'Hradec Králové'),
          ('JTO Sokol Sparta Kopidlno',5,1,2,2,13,23,4,'Kopidlno'),
          ('JTO Sokol Stadion Jaroměř',5,2,0,3,9,16,4,'Jaroměř'),
          ('JTO Sokol Dolní Bousov',5,0,1,4,12,23,1,'Dolní Bousov')]
SVMR_A = [('ZSJ Vítkovické železárny',5,4,1,0,44,12,9,'Ostrava'),
          ('JTO Sokol Ostravská Slavia',5,4,0,1,30,14,8,'Ostrava'),
          ('ZSJ Železničáři Vsetín',5,3,0,2,40,25,6,'Vsetín'),
          ('JTO Sokol Přerov',5,2,1,2,25,26,5,'Přerov'),
          ('JTO Sokol II Sparta Prostějov',5,1,0,4,30,34,2,'Prostějov'),
          ('JTO Sokol Čechie VII Ostrava',5,0,0,5,4,62,0,'Ostrava')]
SVMR_B = [('ZSJ GZ Královo Pole',5,5,0,0,79,10,10,'Brno'),
          ('JTO Sokol Harnach Žižka Brno',5,3,0,2,42,17,6,'Brno'),
          ('JTO Sokol Staroměstský',5,3,0,2,37,30,6,'Staré Město'),
          ('ZSJ Dyas Viktoria Uherský Ostroh',5,3,0,2,25,22,6,'Uherský Ostroh'),
          ('JTO Sokol Černá Hora',5,1,0,4,24,59,2,'Černá Hora'),
          ('JTO Sokol Slovácká Slavia Uherské Hradiště',5,0,0,5,7,76,0,'Uherské Hradiště')]
SVK_Z = [('JTO Sokol Banská Bystrica',2,2,0,0,15,5,4,'Banská Bystrica'),
         ('ZSJ Železničiari Zvolen',6,5,0,1,35,22,10,'Zvolen'),
         ('ZJ Sokol VŠ Bratislava',5,2,0,3,19,20,4,'Bratislava'),
         ('ZJ Sokol SNB Bratislava',5,1,0,4,11,19,2,'Bratislava'),
         ('JTO Sokol Trenčín',4,1,0,3,12,26,2,'Trenčín')]
SVK_V = [('JTO Sokol Tatry Poprad',6,6,0,0,84,20,12,'Poprad'),
         ('JTO Sokol Sparta Prešov',5,2,1,2,34,40,5,'Prešov'),
         ('JTO Sokol Jednota Košice',6,2,1,3,36,51,5,'Košice'),
         ('ZSJ Baťa Liptovský Mikuláš',4,2,0,2,25,21,4,'Liptovský Mikuláš'),
         ('JTO Sokol Spišská Nová Ves',5,0,0,5,20,67,0,'Spišská Nová Ves')]
# play-off (reuse existing club_id dle clean_name): (clean_name, GP,W,D,L,GF,GA,PTS, note)
SF_A = [('Sokol II Meteor České Budějovice',3,3,0,0,13,10,6,''),
        ('Sokol I Pardubice',3,2,0,1,15,9,4,''),
        ('Sokol Hostivař',3,1,0,2,15,15,2,''),
        ('Sokol Černošice',3,0,0,3,10,19,0,'')]
SF_B = [('ZSJ GZ Královo Pole',2,2,0,0,25,1,4,''),
        ('ZSJ Vítkovické železárny',2,1,0,1,4,7,2,''),
        ('Sokol Tatry Poprad',2,0,0,2,3,24,0,'')]
FINAL = [('ZSJ GZ Královo Pole',3,2,0,1,13,7,4,'M-divize'),
         ('ZSJ Vítkovické železárny',3,2,0,1,14,10,4,''),
         ('Sokol II Meteor České Budějovice',3,2,0,1,11,10,4,''),
         ('Sokol I Pardubice',3,0,0,3,4,15,0,'')]

NOTES = [
    'Divize 1948/49: krajské skupiny A/B → krajská finále → celostátní play-off (Semifinálové skupiny A/B → Finálová skupina). VÍTĚZ DIVIZE: ZSJ GZ Královo Pole.',
    'Krajská finále: Západočeská — Meteor ČB (5:5, 2:1 nad Holoubkovem); Východočeská — Pardubice (8:0, 3:2 nad Ml. Boleslaví); Slovenská — Tatry Poprad (6:4, 4:2 nad B. Bystricí).',
    'Slovenská oblastná liga — tabulky NEKOMPLETNÍ (nestejný počet zápasů, část výsledků neznámá); pořadí dle PDF.',
    'Kvalifikace o divizi: vítězové župních I. tříd (Vokovice-Veleslavín, Čimice/Uhříněves, Stará Boleslav/Kyje aj.); postupující též Unhošť, Lokomotiva Nymburk, Viktoria Plzeň, Opava, Slovena Žilina, Kovosmalt Petržalka ad.',
    'Po sezóně: sloučení I. ČLTK + ZMP Praha, Ostravská Slavia + Sokol Mariánské Hory, Harnach Žižka Brno + Žabovřesky (soutěž přenechal Zbrojovce Brno-Židenice II.).',
    'Reorganizace po ročníku: zánikem župních mistrovství vznikly krajské soutěže.',
]


def clean(raw):
    return re.sub(r'^JTO ', '', raw)


def main():
    wb = openpyxl.load_workbook(PATH)
    sy = wb['SYSTEM']
    cl = wb['CLUBS']
    se = wb['SERIES']
    no = wb['NOTES']
    have_sheets = set(wb.sheetnames)
    have_nodes = {sy.cell(r, 1).value for r in range(2, sy.max_row + 1)}
    name2cid = {}
    Hc = {c.value: i for i, c in enumerate(cl[1])}
    for r in range(2, cl.max_row + 1):
        name2cid[cl.cell(r, Hc['clean_name'] + 1).value] = cl.cell(r, 1).value
    # nejvyšší volné club_id / node
    nums = [int(m.group(1)) for v in name2cid.values()
            if (m := re.search(r'_(\d+)$', str(v)))]
    cidx = max(nums) + 1
    nnums = [int(m.group(1)) for v in have_nodes if v and (m := re.search(r'_(\d+)$', str(v)))]
    nidx = max(nnums) + 1

    def node():
        nonlocal nidx
        n = f'NODE_{S}_{nidx:04d}'; nidx += 1; return n
    tr = [200]

    def add_sheet(sheet, region, blocks, level='L20'):
        """blocks = [(block_name, comp_type, teams, reuse_clubid)]; vrátí div_node."""
        nonlocal cidx
        if sheet in wb.sheetnames:
            return None
        ws = wb.create_sheet(sheet)
        ws.append(HDR10)
        for j, wdt in enumerate([6,34,5,30,5,4,4,4,4,5,3,5,5,34,20,6,20,20,18,12,12,18,16], 1):
            ws.column_dimensions[get_column_letter(j)].width = wdt
        for (bname, ctype, teams, reuse, nd) in blocks:
            ws.append(['H', bname, '', '', '', '', '', '', '', '', '', '', '', '',
                       nd, level, '', '', '', '', '', '', ''])
            for i, t in enumerate(teams, 1):
                if reuse:
                    cleannm = t[0]; cid = name2cid.get(cleannm, '')
                    gp,w,d,l,gf,ga,pts,nt = t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8]
                    dispname = cleannm
                else:
                    raw = t[0]; cleannm = clean(raw)
                    gp,w,d,l,gf,ga,pts = t[1],t[2],t[3],t[4],t[5],t[6],t[7]
                    city = t[8]; nt = ''
                    cid = f'CLUB_{S}_{cidx:04d}'; cidx += 1
                    cl.append([cid, cleannm, raw, sheet, '', level, '', '',
                               'Divize 1948/49 (PDF). prev_club_id zatím prázdný.', city])
                    name2cid[cleannm] = cid
                    dispname = cleannm
                tr[0] += 1
                ws.append(['T','',i,dispname,nt,gp,w,d,l,gf,':',ga,pts,bname,nd,level,
                           cid,'','','','',f'TR_{S}_{tr[0]:05d}',''])
        return ws

    def add_node(name, ctype, level, region, parent=''):
        n = node()
        sy.append([n, name, ctype, level, region, parent, '', '', '2-1-0', '', '', '', '', ''])
        return n

    # ── krajské divize ──
    for sheet, region, label, A, B in [
        ('30ZAPC', 'REG_ZPC', 'Západočeská', ZAPC_A, ZAPC_B),
        ('30VYCH', 'REG_VYC', 'Východočeská', VYCH_A, VYCH_B),
        ('30SVMR', 'REG_SVM', 'Moravskoslezská', SVMR_A, SVMR_B),
        ('30SVK', 'REG_SVK', 'Slovenská oblastná liga', SVK_Z, SVK_V)]:
        if sheet in wb.sheetnames:
            continue
        ndiv = add_node(f'30_{label} divize', 'league', 'L20', region)
        na = add_node(f'30_{label} {"Skupina A" if region!="REG_SVK" else "Skupina západ"}', 'group', 'L20', region, ndiv)
        nb = add_node(f'30_{label} {"Skupina B" if region!="REG_SVK" else "Skupina východ"}', 'group', 'L20', region, ndiv)
        ga = 'Skupina A' if region != 'REG_SVK' else 'Skupina západ'
        gb = 'Skupina B' if region != 'REG_SVK' else 'Skupina východ'
        add_sheet(sheet, region, [
            (f'{label} divize / {ga}', 'group', A, False, na),
            (f'{label} divize / {gb}', 'group', B, False, nb)])
        print(f"  ✔ {sheet} ({label}) A+B")

    # ── celostátní play-off divize ──
    if '30DIV' not in wb.sheetnames:
        npo = add_node('Divize / celostátní play-off', 'playoff', 'L20', 'REG_CS')
        nsfa = add_node('Divize / Semifinálová skupina A', 'final_group', 'L20', 'REG_CS', npo)
        nsfb = add_node('Divize / Semifinálová skupina B', 'final_group', 'L20', 'REG_CS', npo)
        nfin = add_node('Divize / Finálová skupina', 'final_group', 'L20', 'REG_CS', npo)
        add_sheet('30DIV', 'REG_CS', [
            ('Divize play-off / Semifinálová skupina A', 'final_group', SF_A, True, nsfa),
            ('Divize play-off / Semifinálová skupina B', 'final_group', SF_B, True, nsfb),
            ('Divize play-off / Finálová skupina', 'final_group', FINAL, True, nfin)])
        print("  ✔ 30DIV (Semifinálové A/B + Finálová skupina) — vítěz Královo Pole")

    # ── krajská finále → SERIES ──
    if se.max_row < 2 or all('divize' not in str(se.cell(r, 10).value or '').lower()
                             for r in range(2, se.max_row + 1)):
        fin_series = [
            ('Finále západočeské divize', 'Sokol II Meteor České Budějovice', 'Sokol Holoubkov', '5:5, 2:1', '1:0 (na zápasy)', 'mistr záp. divize'),
            ('Finále východočeské divize', 'Sokol I Pardubice', 'Sokol Mladá Boleslav', '8:0, 3:2', '2:0', 'mistr vých. divize'),
            ('Finále slovenské divize', 'Sokol Tatry Poprad', 'Sokol Banská Bystrica', '6:4, 4:2', '2:0', 'mistr slov. divize'),
        ]
        for k, (lbl, a, b, gs, ss, nt) in enumerate(fin_series, 1):
            sid = f'SER_{S}_01{k:02d}'
            se.append([sid, '', name2cid.get(a, ''), a, a, '1', gs, ss, '', f'{lbl}: {nt}'])
            se.append([sid, '', name2cid.get(b, ''), b, b, '2', gs, '', '', ''])
        print("  ✔ krajská finále → SERIES (3)")

    # ── NOTES ──
    existing = {no.cell(r, 1).value for r in range(2, no.max_row + 1)}
    for t in NOTES:
        if t not in existing:
            no.append([t])

    # META
    me = wb['META']
    mk = {me.cell(r, 1).value: r for r in range(2, me.max_row + 1)}
    def setm(k, v):
        if k in mk: me.cell(mk[k], 2).value = v
        else: me.append([k, v])
    setm('mistr_divize', 'ZSJ GZ Královo Pole')
    setm('status', 'Nejvyšší soutěž + kompletní divize (4 kraje + Slovensko) + celostátní '
                   'play-off divize. Slovenské tabulky nekompletní. Župní I. třídy jen poznámky.')
    wb.save(PATH)
    print(f"=== {PATH}: divize 1948/49 hotovy ===")


if __name__ == '__main__':
    main()
