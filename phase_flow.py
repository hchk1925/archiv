#!/usr/bin/env python3
"""
phase_flow.py — fáze jedné soutěže a jejich TOK (kdo odkud kam).

Model (SYSTEM list):
  - uzly fází existují (group/playoff_round/final_group/classification…) a visí
    pod soutěží přes parent_node_id;
  - NOVĚ se vyplňuje:
      entry        — kdo do fáze vstupuje ("1.–8. ZČ", "poražení ČF", "9.–12. ZČ")
      phase_order  — pořadí fáze v rámci soutěže (1=ZČ, 2=ČF, …)
      feeds_into       — kam jdou VÍTĚZOVÉ / postupující (node_id)
      feeds_into_loser — kam padají PORAŽENÍ (node_id)

Použití:
  python3 phase_flow.py S1988_89          # vypíše tok fází sezóny (read-only)
  python3 phase_flow.py --apply           # zapíše tok pro vzorové sezóny (DEMO)
"""
import openpyxl, sys, re

DATA = 'data'

# DEMO specifikace toku fází (dle reálné struktury sezóny).
# Klíč = název uzlu; hodnota = (phase_order, entry, feeds_into_name, feeds_loser_name)
DEMO = {
    'S1988_89': {
        'Základní část':       (1, '12 týmů, čtyřkolově', 'Čtvrtfinále', 'Skupina o udržení'),
        'Čtvrtfinále':         (2, '1.–8. ZČ',            'Semifinále',  'O 5.-8.místo'),
        'Semifinále':          (3, 'vítězové ČF',         'Finále',      'O 3.místo'),
        'Finále':              (4, 'vítězové SF',         '',            ''),
        'O 3.místo':           (4, 'poražení SF',         '',            ''),
        'O 5.-8.místo':        (3, 'poražení ČF',         'O 5.místo',   'O 7.místo'),
        'O 5.místo':           (4, 'vítězové sk. 5.–8.',  '',            ''),
        'O 7.místo':           (4, 'poražení sk. 5.–8.',  '',            ''),
        'Skupina o udržení':   (2, '9.–12. ZČ',           '',            'O 9.místo'),
        'O 9.místo':           (3, 'sk. o udržení',       '',            ''),
    },
    'S2013_14': {
        'Předkolo':    (1, '7.–10. ZČ',                'Čtvrtfinále', 'Play Out'),
        'Čtvrtfinále': (2, '1.–6. ZČ + 2 z předkola',  'Semifinále',  ''),
        'Semifinále':  (3, 'vítězové ČF',              'Finále',      ''),
        'Finále':      (4, 'vítězové SF',              '',            ''),
        'Play Out':    (1, '11.–14. ZČ + poražení předkola', '',      ''),
    },
}


def load(path):
    wb = openpyxl.load_workbook(path)
    ws = wb['SYSTEM']
    hdr = [c.value for c in ws[1]]
    idx = {h: i for i, h in enumerate(hdr)}
    return wb, ws, idx


def name2id(ws, idx):
    out = {}
    for r in range(2, ws.max_row + 1):
        nid = ws.cell(r, idx['node_id'] + 1).value
        nm = ws.cell(r, idx['name'] + 1).value
        if nid and nm and nm not in out:
            out[nm] = nid
    return out


def apply_demo(sid, scope_level='L10'):
    """Zapíše tok fází jen pro uzly dané úrovně (vzor = nejvyšší soutěž L10)
    a jen pro názvy, které jsou na té úrovni jednoznačné (jinak by stejné názvy
    fází v nižších soutěžích kolidovaly)."""
    path = f'{DATA}/{sid}_FINAL.xlsx'
    wb, ws, idx = load(path)
    for col in ('entry', 'phase_order', 'feeds_into', 'feeds_into_loser'):
        if col not in idx:
            raise SystemExit(f"{sid}: chybí sloupec {col} — spusť harmonize_schema.py")
    # node_id jen z uzlů cílové úrovně + počet názvů (kvůli jednoznačnosti)
    nid, cnt = {}, {}
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, idx['level'] + 1).value != scope_level:
            continue
        nm = ws.cell(r, idx['name'] + 1).value
        cnt[nm] = cnt.get(nm, 0) + 1
        nid.setdefault(nm, ws.cell(r, idx['node_id'] + 1).value)
    spec = DEMO[sid]
    n, skipped = 0, []
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, idx['level'] + 1).value != scope_level:
            continue
        nm = ws.cell(r, idx['name'] + 1).value
        if nm not in spec:
            continue
        if cnt.get(nm, 0) != 1:
            skipped.append(nm)
            continue
        order, entry, fi, fl = spec[nm]
        ws.cell(r, idx['phase_order'] + 1).value = order
        ws.cell(r, idx['entry'] + 1).value = entry
        ws.cell(r, idx['feeds_into'] + 1).value = nid.get(fi, '') if (fi and cnt.get(fi) == 1) else ''
        ws.cell(r, idx['feeds_into_loser'] + 1).value = nid.get(fl, '') if (fl and cnt.get(fl) == 1) else ''
        n += 1
    wb.save(path)
    msg = f"  ✔ {sid}: tok fází zapsán u {n} uzlů ({scope_level})"
    if skipped:
        msg += f"  ⚠ přeskočeno (nejednoznačný název): {sorted(set(skipped))}"
    print(msg)


def report(sid):
    path = f'{DATA}/{sid}_FINAL.xlsx'
    wb, ws, idx = load(path)
    id2nm = {}
    nodes = []
    for r in range(2, ws.max_row + 1):
        nid = ws.cell(r, idx['node_id'] + 1).value
        if not nid:
            continue
        nm = ws.cell(r, idx['name'] + 1).value
        id2nm[nid] = nm
        nodes.append({'id': nid, 'name': nm,
                      'lvl': ws.cell(r, idx['level'] + 1).value,
                      'order': ws.cell(r, idx.get('phase_order', -1) + 1).value if 'phase_order' in idx else None,
                      'entry': ws.cell(r, idx.get('entry', -1) + 1).value if 'entry' in idx else None,
                      'fi': ws.cell(r, idx['feeds_into'] + 1).value,
                      'fl': ws.cell(r, idx['feeds_into_loser'] + 1).value})
    wb.close()
    flow = [n for n in nodes if n['order'] not in (None, '')]
    if not flow:
        print(f"{sid}: žádné fáze s vyplněným tokem (phase_order). "
              f"Použij phase_flow.py --apply nebo doplň ručně.")
        return
    print(f"\n=== {sid[1:]} — tok fází soutěže ===")
    for n in sorted(flow, key=lambda x: (x['order'], x['name'])):
        arrow = []
        if n['fi']:
            arrow.append(f"vítěz→ {id2nm.get(n['fi'], n['fi'])}")
        if n['fl']:
            arrow.append(f"poražený→ {id2nm.get(n['fl'], n['fl'])}")
        tail = '   ' + ' · '.join(arrow) if arrow else '   (terminální)'
        print(f"  [{n['order']}] {n['name']:20} ← {n['entry'] or '?':28}{tail}")


def main():
    if '--apply' in sys.argv:
        for sid in DEMO:
            apply_demo(sid)
            report(sid)
        return
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        print("Použití: phase_flow.py S1988_89   |   phase_flow.py --apply")
        return
    for sid in args:
        report(sid)


if __name__ == '__main__':
    main()
