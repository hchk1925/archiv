#!/usr/bin/env python3
"""
harmonize_schema.py — srovnání schématu listu SYSTEM napříč všemi sezónami.

Nově přidané sezóny z balíku D42 měly neúplnou hlavičku SYSTEM:
  - 1948/49: jen node_id..parent_node_id (chybí feeds_into, … , prev_node_id)
  - 2014/15–2020/21: chybí prev_node_id

Tento skript zajistí, že každý list SYSTEM má kanonických 12 sloupců (chybějící
doplní jako prázdné, na konec). Čtenáři pracují podle názvů sloupců, takže
pořadí nevadí; jde o konzistenci a o to, aby navazující skripty nepadaly.

Idempotentní.
"""
import openpyxl, glob, os, re, sys

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
CANON = ['node_id', 'name', 'competition_type', 'level', 'region',
         'parent_node_id', 'feeds_into', 'feeds_into_loser', 'scoring',
         'status', 'note', 'prev_node_id', 'entry', 'phase_order']


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    changed = 0
    for path in files:
        sid = re.search(r'S\d{4}_\d{2}', os.path.basename(path)).group(0)
        wb = openpyxl.load_workbook(path)
        if 'SYSTEM' not in wb.sheetnames:
            wb.close()
            continue
        ws = wb['SYSTEM']
        headers = [c.value for c in next(ws.iter_rows(max_row=1))]
        missing = [h for h in CANON if h not in headers]
        if missing:
            base = len(headers)
            for j, h in enumerate(missing):
                ws.cell(row=1, column=base + j + 1, value=h)
            wb.save(path)
            changed += 1
            print(f"  ✓ {sid}: doplněno {missing}")
        wb.close()
    print(f"\n=== SYSTEM schéma srovnáno: změněno {changed} sezón ===")


if __name__ == '__main__':
    main()
