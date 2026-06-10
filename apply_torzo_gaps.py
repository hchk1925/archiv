#!/usr/bin/env python3
"""
apply_torzo_gaps.py — Zapíše „torza" (soutěžní uzly s ≤2 týmy) jako otevřené
položky do sešitů i do DB, konzistentně a re-runnable.

Pro každou sezónu:
  - list TODO  → řádky typ='torzo' (oranžové), marker [torzo-audit]
  - list NOTES → [TBD] torzo: ... (source_type='TODO-auto', node_id), marker
                 (pokud má NOTES jen sloupec 'note', povýší se na plné schéma)

Idempotentní: staré [torzo-audit] řádky se před zápisem odstraní.
Po úpravě sešitů spusť `python build_db.py`, aby se torzo poznámky promítly
do tabulky notes v almanach.sqlite.

Zdroj torz: almanach.sqlite (odvozeno ze standings).
"""
import sqlite3, glob, os, re, sys
from collections import defaultdict
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
DB = 'almanach.sqlite'
MARK = '[torzo-audit]'
FILL = PatternFill('solid', fgColor='FFE0B2')      # světle oranžová
TYPFONT = Font(bold=True, color='B45309')
PLACE = '(žádné otevřené položky'
NOTES_SCHEMA = ['note_text', 'node_id', 'sheet', 'source_type', 'fake_club_ids']

REG = {'STC': 'Středočeský kraj', 'PHA': 'Praha', 'JHC': 'Jihočeský kraj',
       'PLZ': 'Plzeňský kraj', 'PLK': 'Plzeňský kraj', 'KVK': 'Karlovarský kraj',
       'UST': 'Ústecký kraj', 'ULK': 'Ústecký kraj', 'LBK': 'Liberecký kraj',
       'HKK': 'Královéhradecký kraj', 'PAK': 'Pardubický kraj', 'VYS': 'Vysočina',
       'JHM': 'Jihomoravský kraj', 'BRN': 'Brněnsko', 'ZLK': 'Zlínský kraj',
       'OLK': 'Olomoucký kraj', 'MSK': 'Moravskoslezský kraj', 'OST': 'Ostravsko',
       'SVC': 'severní Čechy', 'VYC': 'východní Čechy', 'SVM': 'jihozápadní Morava',
       'ZPC': 'západní Čechy', 'CS': 'celostátní'}


def faze(name):
    n = (name or '').lower()
    return any(k in n for k in ['finále', 'final', 'kval', 'play', 'baráž',
                                'o postup', 'o udržení'])


def co_chybi(name, n, teams):
    tl = [t.strip() for t in teams.split(' / ')] if teams else []
    if faze(name):
        return f"máme jen účastníky ({', '.join(tl) or '?'}), chybí výsledek / odveta"
    if n == 1:
        return f"máme jen 1 tým ({tl[0] if tl else '?'}), chybí zbytek týmů i celá tabulka"
    return f"máme jen 2 týmy ({', '.join(tl)}), chybí zbytek týmů a tabulka"


def torzo_by_season():
    con = sqlite3.connect(DB)
    q = '''SELECT s.season_id, s.node_id, c.name, c.level, c.region, COUNT(*) n,
                  GROUP_CONCAT(s.club_name, ' / ')
           FROM standings s
           LEFT JOIN competitions c
             ON c.season_id=s.season_id AND c.node_id=s.node_id
           GROUP BY s.season_id, s.node_id
           HAVING n<=2
           ORDER BY s.season_id, c.level, s.node_id'''
    by = defaultdict(list)
    for sid, node, name, lvl, reg, n, teams in con.execute(q):
        by[sid].append((node, name, lvl, reg, n, teams))
    return by


def ref_text(name, reg, node):
    rg = REG.get((reg or '').replace('REG_', ''), '')
    return f"{name or '— bez názvu —'}" + (f" ({rg})" if rg else '') + f" · {node}"


def update_todo(ws, items):
    """Přepíše [torzo-audit] řádky v TODO listu, zachová ostatní."""
    keep = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(v is None for v in row):
            continue
        popis = str(row[3] or '')
        if MARK in popis or popis.startswith(PLACE):
            continue
        keep.append(list(row))
    nextnum = 0
    for kr in keep:
        try:
            nextnum = max(nextnum, int(kr[0]) if kr[0] else 0)
        except (TypeError, ValueError):
            pass
    if ws.max_row >= 2:
        ws.delete_rows(2, ws.max_row - 1)
    for kr in keep:
        ws.append(kr)
    for node, name, lvl, reg, n, teams in items:
        nextnum += 1
        ws.append([nextnum, 'torzo', ref_text(name, reg, node),
                   f"{co_chybi(name, n, teams)}  {MARK}", 'ne', None])
        r = ws.max_row
        for col in range(1, 7):
            ws.cell(r, col).fill = FILL
        ws.cell(r, 2).font = TYPFONT
        ws.cell(r, 4).alignment = Alignment(wrap_text=True, vertical='top')
    if not keep and not items:
        ws.append([None, None, None, '(žádné otevřené položky — sezóna OK)',
                   None, None])


def ensure_rich_notes(ws):
    """Vrátí header-index; pokud má NOTES jen 'note', povýší na plné schéma."""
    hdr = [c.value for c in ws[1]]
    if 'note_text' in hdr and 'source_type' in hdr:
        return {h: i for i, h in enumerate(hdr) if h is not None}
    # plain ('note',) → note_text + doplňkové sloupce; data zůstávají ve sl. A
    for j, name in enumerate(NOTES_SCHEMA, start=1):
        ws.cell(1, j, name)
    hdr = [c.value for c in ws[1]]
    return {h: i for i, h in enumerate(hdr) if h is not None}


def update_notes(ws, items):
    H = ensure_rich_notes(ws)
    ncols = ws.max_column
    nti, sti = H.get('note_text'), H.get('source_type')
    ndi = H.get('node_id')
    # smaž staré torzo poznámky
    for ri in range(ws.max_row, 1, -1):
        v = ws.cell(ri, (nti or 0) + 1).value
        if v and MARK in str(v):
            ws.delete_rows(ri, 1)
    for node, name, lvl, reg, n, teams in items:
        vals = [None] * ncols
        if nti is not None:
            vals[nti] = f"[TBD] torzo: {co_chybi(name, n, teams)}  {MARK}"
        if sti is not None:
            vals[sti] = 'TODO-auto'
        if ndi is not None:
            vals[ndi] = node
        ws.append(vals)


def main():
    by = torzo_by_season()
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    tot = 0
    for path in files:
        m = re.search(r'S(\d{4})_(\d{2})', os.path.basename(path))
        sid = f"S{m.group(1)}_{m.group(2)}"
        items = by.get(sid, [])
        wb = openpyxl.load_workbook(path)
        if 'TODO' in wb.sheetnames:
            update_todo(wb['TODO'], items)
        if 'NOTES' in wb.sheetnames:
            update_notes(wb['NOTES'], items)
        wb.save(path)
        if items:
            tot += len(items)
            print(f"  ✓ {sid}: {len(items):>2} torz → TODO + NOTES")
    print(f"\n=== Hotovo. Vloženo torzo položek: {tot} ===")
    print("Spusť `python build_db.py` pro promítnutí do almanach.sqlite.")


if __name__ == '__main__':
    main()
