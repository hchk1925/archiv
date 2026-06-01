#!/usr/bin/env python3
"""
apply_todo_sheets.py — Refresh per-season listů TODO v sešitech.

Pro každou sezónu sestaví aktuální seznam TBD/otevřených položek
PŘÍMO ZE SEŠITU (CLUBS change_note s 'TBD:', rozbité prev, pyramidové
mezery, fate nekonzistence) a zapíše:
  - list 'TODO' (přepsán)
  - paralelní '[TBD]' řádky v NOTES (source_type='TODO-auto', re-runnable)

Re-runnable. Nemá vstupní .md — vždy odráží aktuální stav.
"""
import openpyxl, glob, os, re, sys
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from collections import defaultdict

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
AUTO_TAG = 'TODO-auto'
NON_DATA = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA', 'TODO'}
HDR = ['#', 'typ', 'reference', 'popis', 'vyřešeno? (ANO/ne)',
       'poznámka kolegy']
TBD_RE = re.compile(r'TBD[:\-][^|]*', re.I)
LEVEL_RE = re.compile(r'L(\d+)')


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def lvl(v):
    if v is None:
        return None
    m = LEVEL_RE.search(str(v))
    return int(m.group(1)) if m else None


def collect_items(wb):
    items = []                      # (typ, ref, popis)
    # 1. CLUBS s 'TBD:' v change_note
    ws = wb['CLUBS']
    rows = list(ws.iter_rows(values_only=True))
    H = hidx(rows[0])
    valid_cids = set()
    for r in rows[1:]:
        if not r or r[H['club_id']] is None:
            continue
        valid_cids.add(r[H['club_id']])
    for r in rows[1:]:
        if not r or r[H['club_id']] is None:
            continue
        cid = r[H['club_id']]
        cn = r[H.get('change_note')] if 'change_note' in H else None
        if cn:
            for m in TBD_RE.finditer(str(cn)):
                items.append(('prev_club_id / identita', cid, m.group(0).strip()))
    # 2. rozbité prev (post-fix by mělo být 0, ale jistota)
    for r in rows[1:]:
        if not r or r[H['club_id']] is None:
            continue
        cid = r[H['club_id']]
        pcid = r[H['prev_club_id']]
        if not pcid:
            continue
        # validní jen pokud existuje v některé předchozí sezóně (mimo aktuální);
        # zde stačí ověřit, že nejde o aktuální sezónu — cross-season validaci
        # provádí audit; tady jen flag „prev mimo katalog"
        if not re.match(r'CLUB_S\d{4}_\d{2}_\d+', str(pcid)):
            items.append(('prev_club_id', cid,
                          f"podivný tvar prev_club_id: {pcid}"))
    # 3. SYSTEM — top-level kvalifikace bez feeds_into
    if 'SYSTEM' in wb.sheetnames:
        ws = wb['SYSTEM']
        rr = list(ws.iter_rows(values_only=True))
        SH = hidx(rr[0])
        for r in rr[1:]:
            if not r or r[SH['node_id']] is None:
                continue
            nm = str(r[SH['name']] or '')
            ct = str(r[SH['competition_type']] or '')
            par = r[SH['parent_node_id']]
            fi = r[SH['feeds_into']]
            is_q = (ct in ('baraz', 'qualification_group') or
                    re.match(r'^(Kvalifikace|Baráž|KVAL)\b', nm, re.I))
            if is_q and par is None and not fi:
                items.append(('pyramida (feeds_into)', r[SH['node_id']],
                              f"top-level kvalifikace bez feeds_into: '{nm}'"))
    # 4. fate nekonzistence (per club_id ve standings)
    fates = defaultdict(set)
    cnames = {}
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        dws = wb[sh]
        rr = list(dws.iter_rows(values_only=True))
        if not rr:
            continue
        DH = hidx(rr[0])
        if 'club_id' not in DH or 'season_fate' not in DH:
            continue
        for r in rr[1:]:
            if not r:
                continue
            cid = r[DH['club_id']]
            ft = r[DH['season_fate']]
            if cid and ft:
                fates[cid].add(str(ft).strip())
                cnames[cid] = r[DH.get('club_name', 3)] if 'club_name' in DH else ''
    for cid, fs in fates.items():
        if len(fs) > 1:
            items.append(('fate', cid,
                          f"nekonzistentní fate {sorted(fs)} — sjednotit"))
    # 5. poškozené tabulkové buňky v extralize (L10): GA chybí / GF=0
    #    (re-extrakce ze zdroje — viz docs/DATA_QUALITY.md)
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        dws = wb[sh]
        rr = list(dws.iter_rows(values_only=True))
        if not rr:
            continue
        DH = hidx(rr[0])
        if 'row_type' not in DH or 'GA' not in DH:
            continue
        for r in rr[1:]:
            if not r or r[DH['row_type']] != 'T':
                continue
            if lvl(r[DH.get('level')] if 'level' in DH else None) != 10:
                continue
            nm = r[DH.get('club_name', 3)]
            ga = r[DH['GA']]
            gf = r[DH['GF']] if 'GF' in DH else None
            if ga is None or str(ga).strip() == ':':
                items.append(('tabulka (re-extrakce)', nm,
                              'chybí obdržené branky (GA) — doplnit ze zdroje'))
            if gf == 0 or (gf is not None and str(gf).strip() == ':'):
                items.append(('tabulka (re-extrakce)', nm,
                              'vstřelené branky (GF) = 0/chybí — ověřit ze zdroje'))
    return items


def build_todo_sheet(wb, items):
    if 'TODO' in wb.sheetnames:
        del wb['TODO']
    ws = wb.create_sheet('TODO')
    hf = Font(bold=True, color='FFFFFF')
    fill = PatternFill('solid', fgColor='305496')
    for j, h in enumerate(HDR, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.font = hf
        c.fill = fill
        c.alignment = Alignment(vertical='center')
    if not items:
        ws.cell(row=2, column=4, value='(žádné otevřené položky — sezóna OK)')
    for i, (typ, ref, msg) in enumerate(items, start=1):
        ws.cell(row=i + 1, column=1, value=i)
        ws.cell(row=i + 1, column=2, value=typ)
        ws.cell(row=i + 1, column=3, value=ref)
        ws.cell(row=i + 1, column=4, value=msg)
    widths = [5, 22, 26, 88, 18, 40]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    for r in range(2, max(2, len(items) + 2)):
        ws.cell(row=r, column=4).alignment = Alignment(wrap_text=True,
                                                       vertical='top')
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HDR))}{max(2,len(items)+1)}"


def update_notes(wb, items):
    if 'NOTES' not in wb.sheetnames:
        return 0
    ws = wb['NOTES']
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return 0
    hdr = list(rows[0])
    idx = {h: i for i, h in enumerate(hdr) if h is not None}
    sti = idx.get('source_type')
    nti = idx.get('note_text')
    ncols = len(hdr)
    for r_i in range(len(rows), 1, -1):
        r = rows[r_i - 1]
        if sti is not None and r[sti] == AUTO_TAG:
            ws.delete_rows(r_i, 1)
    added = 0
    for typ, ref, msg in items:
        rowvals = [None] * ncols
        if nti is not None:
            rowvals[nti] = f"[TBD] {typ}: {msg}"
        if sti is not None:
            rowvals[sti] = AUTO_TAG
        if 'node_id' in idx and str(ref).startswith('NODE_'):
            rowvals[idx['node_id']] = ref
        ws.append(rowvals)
        added += 1
    return added


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    tot = 0
    for path in files:
        m = re.search(r'S(\d{4})_(\d{2})', os.path.basename(path))
        season = f"{m.group(1)}_{m.group(2)}"
        wb = openpyxl.load_workbook(path)
        items = collect_items(wb)
        build_todo_sheet(wb, items)
        n = update_notes(wb, items)
        wb.save(path)
        tot += len(items)
        print(f"  ✓ {season}: {len(items):>3} pol. v TODO + {n} [TBD] NOTES")
    print(f"\n=== Refresh hotov. Celkem otevřených položek: {tot} ===")


if __name__ == '__main__':
    main()
