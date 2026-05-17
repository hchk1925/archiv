#!/usr/bin/env python3
"""
apply_todo_sheets.py — Rozdistribuuje TODO_continuity.md do sezónních sešitů.

Pro každou sezónu:
  - přidá/přepíše list 'TODO' s položkami JEN té sezóny (kolega-friendly:
    bold hlavička, autofiltr, zmrazený první řádek, sloupec na poznámku),
  - přidá paralelní '[TBD]' řádky do listu NOTES (konvence D19).

Re-runnable: list TODO se přestaví; staré '[TBD]'/source_type='TODO-auto'
řádky v NOTES se před doplněním odstraní (žádné duplikáty).

Zdroj workbooků se NEMĚNÍ formátem — pořád 1 sešit = 1 sezóna.
"""
import openpyxl, glob, os, re, sys
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from collections import defaultdict

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
TODO_MD = 'TODO_continuity.md'
AUTO_TAG = 'TODO-auto'                       # marker našich NOTES řádků
HDR = ['#', 'typ', 'reference', 'popis', 'vyřešeno? (ANO/ne)',
       'poznámka kolegy']


def categorize(msg):
    m = msg.lower()
    if 'fate nekonzist' in m or 'fate' in m and 'nekonzist' in m:
        return 'fate'
    if 'system' in m:
        return 'pyramida'
    if 'pseudo' in m or 'mazán' in m:
        return 'pseudo'
    if 'prev' in m:
        return 'prev_club_id'
    return 'jiné'


def ref_of(msg):
    m = re.search(r'(CLUB_S\d{4}_\d{2}_\d+|NODE_S\d{4}_\d{2}_\d+)', msg)
    return m.group(1) if m else ''


def parse_todo():
    by_season = defaultdict(list)
    for ln in open(TODO_MD, encoding='utf-8'):
        ln = ln.rstrip('\n')
        m = re.match(r'\[(\d{4}_\d{2})\]\s*(.*)', ln.strip())
        if not m:
            continue
        season, msg = m.group(1), m.group(2)
        by_season[season].append(msg)
    return by_season


def build_todo_sheet(wb, items):
    if 'TODO' in wb.sheetnames:
        del wb['TODO']
    ws = wb.create_sheet('TODO')            # na konec (pořadí ostatních beze změny)
    hf = Font(bold=True, color='FFFFFF')
    fill = PatternFill('solid', fgColor='305496')
    for j, h in enumerate(HDR, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.font = hf
        c.fill = fill
        c.alignment = Alignment(vertical='center')
    for i, (typ, ref, msg) in enumerate(items, start=1):
        ws.cell(row=i + 1, column=1, value=i)
        ws.cell(row=i + 1, column=2, value=typ)
        ws.cell(row=i + 1, column=3, value=ref)
        ws.cell(row=i + 1, column=4, value=msg)
        ws.cell(row=i + 1, column=5, value='')
        ws.cell(row=i + 1, column=6, value='')
    widths = [5, 14, 26, 88, 18, 40]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    for r in range(2, len(items) + 2):
        ws.cell(row=r, column=4).alignment = Alignment(wrap_text=True,
                                                       vertical='top')
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HDR))}{len(items)+1}"


def update_notes(wb, items, season):
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
    # odstraň naše předchozí auto řádky (idempotence) — odspoda
    for r_i in range(len(rows), 1, -1):
        r = rows[r_i - 1]
        if sti is not None and r[sti] == AUTO_TAG:
            ws.delete_rows(r_i, 1)
    # přidej nové [TBD] řádky
    added = 0
    for typ, ref, msg in items:
        rowvals = [None] * ncols
        if nti is not None:
            rowvals[nti] = f"[TBD] {typ}: {msg}"
        if sti is not None:
            rowvals[sti] = AUTO_TAG
        if 'node_id' in idx and ref.startswith('NODE_'):
            rowvals[idx['node_id']] = ref
        ws.append(rowvals)
        added += 1
    return added


def main():
    by_season = parse_todo()
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    tot_sheets = tot_items = tot_notes = 0
    for path in files:
        m = re.search(r'S(\d{4})_(\d{2})', os.path.basename(path))
        season = f"{m.group(1)}_{m.group(2)}"
        msgs = by_season.get(season, [])
        items = [(categorize(x), ref_of(x), x) for x in msgs]
        wb = openpyxl.load_workbook(path)
        build_todo_sheet(wb, items)
        n_notes = update_notes(wb, items, season)
        wb.save(path)
        tot_sheets += 1
        tot_items += len(items)
        tot_notes += n_notes
        print(f"  ✓ {season}: {len(items):>2} položek (TODO list + "
              f"{n_notes} [TBD] v NOTES)")
    print(f"\n=== HOTOVO ===")
    print(f"  Sešitů s listem TODO: {tot_sheets}")
    print(f"  TODO položek celkem:  {tot_items}")
    print(f"  [TBD] řádků v NOTES:  {tot_notes}")
    print(f"  Formát zachován: 1 sešit = 1 sezóna (list TODO na konci)")


if __name__ == '__main__':
    main()
