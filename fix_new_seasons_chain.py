#!/usr/bin/env python3
"""
fix_new_seasons_chain.py — návaznost klubů u sezón nově přidaných z balíku D42.

Řeší dvě díry, které vznikly sloučením nových sezón (1948/49, 2014/15–2020/21)
s původní repo linií:

1) 2017/18 — prev_club_id systematicky ukazoval na sezónu 2015/16 (přeskočený
   rok) místo na bezprostředně předchozí 2016/17. Přemapujeme přes mapu
   nástupců: 2015/16_id -> 2016/17_id (dle prev_club_id v 2016/17), s fallbackem
   na shodu clean_name v 2016/17.

2) 1949/50 — chyběly linky na první sezónu 1948/49. Doplníme 8 extraligových
   linků (club_id i názvy se shodují s kurátorovanou verzí balíku).

Re-runnable: druhý běh už nic nezmění.
"""
import openpyxl, sys

DATA = 'data'


def load_clubs_rows(path):
    """Vrať (workbook, worksheet, idx_map, list[(row_idx, club_id, clean_name, prev)])."""
    wb = openpyxl.load_workbook(f'{DATA}/{path}')
    ws = wb['CLUBS']
    hdr = [c.value for c in ws[1]]
    idx = {h: i for i, h in enumerate(hdr)}
    ci, ni, pi = idx['club_id'], idx['clean_name'], idx['prev_club_id']
    rows = []
    for ri in range(2, ws.max_row + 1):
        cid = ws.cell(ri, ci + 1).value
        if cid is None:
            continue
        rows.append((ri, cid, str(ws.cell(ri, ni + 1).value or ''),
                     ws.cell(ri, pi + 1).value))
    return wb, ws, pi + 1, rows


def read_clubs(path):
    wb = openpyxl.load_workbook(f'{DATA}/{path}', read_only=True, data_only=True)
    ws = wb['CLUBS']
    rows = list(ws.iter_rows(values_only=True))
    idx = {h: i for i, h in enumerate(rows[0])}
    out = []
    for r in rows[1:]:
        if not r or r[idx['club_id']] is None:
            continue
        out.append((r[idx['club_id']], str(r[idx['clean_name']] or ''),
                    r[idx['prev_club_id']]))
    wb.close()
    return out


def fix_2017_18():
    c16 = read_clubs('S2016_17_FINAL.xlsx')
    succ = {}                       # 2015/16 id -> 2016/17 id (přes prev v 2016/17)
    by_name16 = {}
    for cid, nm, prev in c16:
        if prev:
            succ[prev] = cid
        by_name16.setdefault(nm.casefold(), cid)
    wb, ws, pcol, rows = load_clubs_rows('S2017_18_FINAL.xlsx')
    fixed = 0
    leftover = []
    for ri, cid, nm, prev in rows:
        if prev and str(prev).startswith('CLUB_S2015_16_'):
            tgt = succ.get(prev) or by_name16.get(nm.casefold())
            if tgt:
                ws.cell(ri, pcol).value = tgt
                fixed += 1
            else:
                leftover.append((cid, nm, prev))
    if fixed:
        wb.save(f'{DATA}/S2017_18_FINAL.xlsx')
    print(f"2017/18: přemapováno {fixed} prev_club_id (2015/16 -> 2016/17)")
    for cid, nm, prev in leftover:
        print(f"   ⚠ nepřemapováno: {cid} '{nm}' prev={prev}")
    return fixed


# 1949/50 extraliga -> 1948/49 (kurátorováno v balíku D42; club_id se shodují)
LINKS_1949 = {
    'CLUB_S1949_50_0001': 'CLUB_S1948_49_0003',  # ATK Praha
    'CLUB_S1949_50_0002': 'CLUB_S1948_49_0010',  # Vítkovické Železárny
    'CLUB_S1949_50_0003': 'CLUB_S1948_49_0001',  # Zdar LTC Praha <- LTC Praha
    'CLUB_S1949_50_0004': 'CLUB_S1948_49_0004',  # Stadion České Budějovice
    'CLUB_S1949_50_0005': 'CLUB_S1948_49_0009',  # GZ Královo Pole
    'CLUB_S1949_50_0006': 'CLUB_S1948_49_0002',  # NV Bratislava <- ŠK Bratislava
    'CLUB_S1949_50_0007': 'CLUB_S1948_49_0006',  # Bratrství Sparta Praha <- AC Sparta Bubeneč
    'CLUB_S1949_50_0008': 'CLUB_S1948_49_0005',  # Zbrojovka Brno <- Sokol Zbrojovka Židenice
}


def fix_1949_50():
    valid48 = {cid for cid, _, _ in read_clubs('S1948_49_FINAL.xlsx')}
    wb, ws, pcol, rows = load_clubs_rows('S1949_50_FINAL.xlsx')
    added = 0
    for ri, cid, nm, prev in rows:
        tgt = LINKS_1949.get(cid)
        if tgt and tgt in valid48 and not prev:
            ws.cell(ri, pcol).value = tgt
            added += 1
    if added:
        wb.save(f'{DATA}/S1949_50_FINAL.xlsx')
    print(f"1949/50: doplněno {added} linků na 1948/49")
    return added


if __name__ == '__main__':
    fix_2017_18()
    fix_1949_50()
