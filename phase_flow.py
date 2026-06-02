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


# ── AUTO inference toku fází ze struktury (názvy + typy + parent + počty týmů) ──
NON_DATA = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA', 'TODO', 'NOTES1'}
# pořadí fáze pro řazení/zobrazení
ORDER = {'ZC': 1, 'PREDKOLO': 2, 'UDRZENI': 2, 'PLAYOUT': 2, 'OF': 2, 'CF': 3,
         'SF': 4, 'O58': 4, 'OUMIST': 4, 'FINALE': 5, 'O3': 5, 'O5': 5, 'O7': 5,
         'O9': 5, 'O11': 5}
INTRA = set(ORDER)                      # role, které auto vyplňuje (baráž/kval NE)


def classify(name):
    s = (name or '').lower()
    if '/' in s:
        s = s.split('/')[-1].strip()
    if 'základní' in s or s in ('zč', 'zc', 'základní část'):
        return 'ZC'
    if 'předkolo' in s:
        return 'PREDKOLO'
    if 'osmifin' in s or '1/8' in s:
        return 'OF'
    if 'čtvrtfin' in s or '1/4' in s:
        return 'CF'
    if 'semifin' in s:
        return 'SF'
    if 'play out' in s or 'play-out' in s or 'playout' in s:
        return 'PLAYOUT'
    if 'udržen' in s or 'záchran' in s:
        return 'UDRZENI'
    if '5.-8' in s or '5.–8' in s or '5.-8.' in s:
        return 'O58'
    if 'o 3' in s or '3. míst' in s or '3.míst' in s:
        return 'O3'
    if 'o 5' in s or '5. míst' in s or '5.míst' in s:
        return 'O5'
    if 'o 7' in s or '7. míst' in s or '7.míst' in s:
        return 'O7'
    if 'o 9' in s or '9. míst' in s or '9.míst' in s:
        return 'O9'
    if 'o 11' in s or '11. míst' in s:
        return 'O11'
    if 'o umíst' in s:
        return 'OUMIST'
    if 'finále' in s or 'final' in s:
        return 'FINALE'
    return None


def read_counts(path):
    """node_id → počet T-řádků (velikost tabulky fáze)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    cnt = {}
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        ws = wb[sh]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        H = {h: i for i, h in enumerate(rows[0])}
        if 'row_type' not in H or 'node_id' not in H:
            continue
        for r in rows[1:]:
            if r and r[H['row_type']] == 'T' and r[H['node_id']]:
                cnt[r[H['node_id']]] = cnt.get(r[H['node_id']], 0) + 1
    wb.close()
    return cnt


def auto_season(sid):
    path = f'{DATA}/{sid}_FINAL.xlsx'
    wb, ws, idx = load(path)
    for col in ('entry', 'phase_order', 'feeds_into', 'feeds_into_loser'):
        if col not in idx:
            raise SystemExit(f"{sid}: chybí {col} — spusť harmonize_schema.py")
    cnt = read_counts(path)
    # načti uzly
    nodes = {}
    parent = {}
    for r in range(2, ws.max_row + 1):
        nid = ws.cell(r, idx['node_id'] + 1).value
        if not nid:
            continue
        nodes[nid] = {'row': r, 'name': ws.cell(r, idx['name'] + 1).value,
                      'type': ws.cell(r, idx['competition_type'] + 1).value,
                      'role': classify(ws.cell(r, idx['name'] + 1).value),
                      'n': cnt.get(nid, 0)}
        parent[nid] = ws.cell(r, idx['parent_node_id'] + 1).value or None

    def root(nid, seen=None):
        seen = seen or set()
        while parent.get(nid) and parent[nid] in nodes and parent[nid] not in seen:
            seen.add(nid)
            nid = parent[nid]
        return nid

    # seskup uzly po soutěžích (root)
    groups = {}
    for nid in nodes:
        groups.setdefault(root(nid), []).append(nid)

    wired = 0
    for rt, members in groups.items():
        roles = {}
        for nid in members:
            rl = nodes[nid]['role']
            if rl in INTRA:
                roles.setdefault(rl, []).append(nid)
        # má soutěž vůbec víc fází (play-off / o udržení / skupina o umístění)?
        flow_roles = {'PREDKOLO', 'OF', 'CF', 'SF', 'FINALE', 'O58', 'UDRZENI',
                      'PLAYOUT', 'O3', 'O5', 'O7', 'O9', 'O11', 'OUMIST'}
        if not (roles.keys() & flow_roles):
            continue
        # ZČ: buď uzel role ZC, nebo kořenová soutěž (drží tabulku ZČ)
        if 'ZC' not in roles and nodes[rt]['n'] > 0 and nodes[rt]['role'] is None:
            roles['ZC'] = [rt]
            nodes[rt]['role'] = 'ZC'

        def first(*rls):
            for rl in rls:
                if roles.get(rl):
                    return roles[rl][0]
            return ''

        N = max((nodes[x]['n'] for x in roles.get('ZC', [])), default=0)
        R = sum(nodes[x]['n'] for x in roles.get('UDRZENI', []))
        po_top = first('PREDKOLO', 'CF', 'SF', 'FINALE')
        releg = first('UDRZENI', 'PLAYOUT')
        has_pre = bool(roles.get('PREDKOLO'))

        def setc(nid, order, entry, fi='', fl=''):
            nodes[nid]['_w'] = (order, entry, fi, fl)

        for rl, ids in roles.items():
            for nid in ids:
                if rl == 'ZC':
                    e = f"{N} týmů" if N else 'účastníci soutěže'
                    setc(nid, 1, e, po_top, releg)
                elif rl == 'PREDKOLO':
                    setc(nid, 2, 'střed tabulky ZČ', first('CF', 'SF'), first('PLAYOUT', 'UDRZENI'))
                elif rl == 'OF':
                    setc(nid, 2, 'horní část ZČ', first('CF', 'SF'), first('O58'))
                elif rl == 'CF':
                    if has_pre:
                        e = 'horní ZČ + postupující z předkola'
                    elif N and R:
                        e = f"1.–{N - R}. ZČ"
                    else:
                        e = 'horní polovina ZČ'
                    setc(nid, 3, e, first('SF', 'FINALE'), first('O58'))
                elif rl == 'SF':
                    setc(nid, 4, 'vítězové ČF', first('FINALE'), first('O3', 'OUMIST'))
                elif rl == 'FINALE':
                    setc(nid, 5, 'vítězové SF', '', '')
                elif rl == 'O3':
                    setc(nid, 5, 'poražení SF', '', '')
                elif rl == 'O58':
                    setc(nid, 4, 'poražení ČF', first('O5'), first('O7'))
                elif rl == 'O5':
                    setc(nid, 5, 'sk. o 5.–8. (horní)', '', '')
                elif rl == 'O7':
                    setc(nid, 5, 'sk. o 5.–8. (dolní)', '', '')
                elif rl == 'O9':
                    setc(nid, 5, 'o 9. místo', '', '')
                elif rl == 'O11':
                    setc(nid, 5, 'o 11. místo', '', '')
                elif rl == 'OUMIST':
                    setc(nid, 4, 'poražení play-off', '', '')
                elif rl == 'UDRZENI':
                    e = f"{N - R + 1}.–{N}. ZČ" if (N and R) else 'dolní část ZČ'
                    setc(nid, 2, e, '', '')
                elif rl == 'PLAYOUT':
                    setc(nid, 2, 'dolní část ZČ', '', '')
        wired += 1

    # zápis
    n_nodes = 0
    for nid, nd in nodes.items():
        if '_w' in nd:
            order, entry, fi, fl = nd['_w']
            ws.cell(nd['row'], idx['phase_order'] + 1).value = order
            ws.cell(nd['row'], idx['entry'] + 1).value = entry
            ws.cell(nd['row'], idx['feeds_into'] + 1).value = fi
            ws.cell(nd['row'], idx['feeds_into_loser'] + 1).value = fl
            n_nodes += 1
    wb.save(path)
    return wired, n_nodes


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
    import glob
    if '--auto' in sys.argv:
        files = sorted(glob.glob(f'{DATA}/S*_FINAL.xlsx'))
        tc = tn = 0
        for p in files:
            sid = re.search(r'S\d{4}_\d{2}', p).group(0)
            w, nn = auto_season(sid)
            tc += w; tn += nn
            if w:
                print(f"  {sid[1:]}: {w} soutěží, {nn} uzlů fází")
        print(f"\n=== AUTO hotovo: {tc} soutěží s tokem fází, {tn} uzlů ===")
        return
    if '--apply' in sys.argv:
        for sid in DEMO:
            apply_demo(sid)
            report(sid)
        return
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        print("Použití: phase_flow.py S1988_89  |  --auto (všechny)  |  --apply (demo)")
        return
    for sid in args:
        report(sid)


if __name__ == '__main__':
    main()
