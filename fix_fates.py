#!/usr/bin/env python3
"""
fix_fates.py — oprava season_fate s ohledem na fáze soutěží.

Problém: u víceFázových soutěží (základní část → play off / o udržení / kvalifikace)
byl postup/sestup chybně přiřazen ZÁKLADNÍ ČÁSTI podle konečného pořadí. Postup ale
přišel až z play off / kvalifikace; základní část znamená jen „postup do play off".

Tento skript přepíše season_fate tak, že:
  • v základní (největší) fázi dostane tým štítek, KAM šel:
        play off / o udržení / o umístění / kvalifikace / prolínací
        (odvozeno z feeds_into / feeds_into_loser a z členství v sesterských fázích),
  • v koncové skupině o udržení: poslední = sestup, ostatní = udržel se,
  • postup/sestup na jednofázových (jedna tabulka) soutěžích zůstává beze změny.

Slovník: postup, sestup, udržel se, setrval, zůstal  +  fázové štítky.

Soutěže, kde si skript není jistý (víc fází, ale chybí feeds i tabulky), VYPÍŠE
do reportu k ručnímu dořešení podle zdrojových PDF.

  python fix_fates.py --season 1986_87 --preview     # náhled jedné sezóny
  python fix_fates.py --preview                       # náhled všech + report
  python fix_fates.py --apply                         # zápis do xlsx
"""
import collections
import glob
import os
import re
import sys
import openpyxl

DATA = os.path.join(os.path.dirname(__file__), 'data')
NON_DATA = {'META', 'CLUBS', 'SYSTEM', 'NOTES', 'TODO', 'CHANGES', 'README'}


def lvl(v):
    m = re.search(r'(\d+)', str(v or ''))
    return int(m.group(1)) if m else None


PLAYOFF_T = {'playoff_round', 'playoff', 'final_group', 'final_series', 'series'}
RELEG_T = {'relegation_group', 'relegation_playoff', 'relegation_series'}
CLASS_T = {'classification'}
QUAL_T = {'qualification_group', 'qualification_series', 'qualification', 'baraz'}


def sibling_label(node):
    """Štítek cílové (sesterské) fáze podle typu/názvu."""
    t = str(node.get('competition_type') or '')
    nm = str(node.get('name') or '').lower()
    if t in PLAYOFF_T or any(w in nm for w in
            ('play off', 'playoff', 'play-off', 'finále', 'čtvrtfinále',
             'semifinále', 'předkolo')):
        return 'play off'
    if t in RELEG_T or 'udržení' in nm or 'záchran' in nm:
        return 'o udržení'
    if t in CLASS_T or 'o umístění' in nm or re.search(r'\bo \d+\.', nm):
        return 'o umístění'
    if t in QUAL_T or 'kvalif' in nm or 'baráž' in nm or 'prolín' in nm:
        return 'prolínací' if ('baráž' in nm or 'prolín' in nm) else 'kvalifikace'
    return None


def load_system(wb):
    ws = wb['SYSTEM']
    rows = list(ws.iter_rows(values_only=True))
    H = {c: j for j, c in enumerate(rows[0]) if c}
    nodes = {}
    for r in rows[1:]:
        nid = r[H['node_id']] if 'node_id' in H else None
        if not nid:
            continue
        nodes[nid] = {
            'node_id': nid,
            'name': r[H.get('name', -1)] if 'name' in H else '',
            'competition_type': r[H.get('competition_type', -1)] if 'competition_type' in H else '',
            'level': r[H.get('level', -1)] if 'level' in H else '',
            'parent': r[H.get('parent_node_id', -1)] if 'parent_node_id' in H else None,
            'feeds': r[H.get('feeds_into', -1)] if 'feeds_into' in H else None,
            'loser': r[H.get('feeds_into_loser', -1)] if 'feeds_into_loser' in H else None,
        }
    return nodes


def season_changes(path):
    """Vrať dict {(sheet, rowidx): new_fate} a report flagů pro jednu sezónu."""
    wb = openpyxl.load_workbook(path, data_only=True)
    nodes = load_system(wb)
    # membership + řádky podle node
    members = collections.defaultdict(set)      # node -> {club_id}
    rowsby = collections.defaultdict(list)       # node -> [(sheet, rowidx, pos, club_id, fate)]
    fate_col = {}
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        ws = wb[sh]
        rr = list(ws.iter_rows(values_only=True))
        if not rr:
            continue
        H = {c: j for j, c in enumerate(rr[0]) if c}
        if 'season_fate' not in H or 'node_id' not in H or 'row_type' not in H:
            continue
        fate_col[sh] = H['season_fate']
        for i, r in enumerate(rr[1:], start=2):
            if r[H['row_type']] != 'T':
                continue
            nid = r[H['node_id']]
            cid = r[H.get('club_id', -1)] if 'club_id' in H else None
            pos = r[H.get('pos', -1)] if 'pos' in H else None
            fate = r[H['season_fate']]
            if nid:
                members[nid].add(cid)
                rowsby[nid].append((sh, i, pos, cid, fate))
    wb.close()

    changes = {}
    flags = []
    # seskup fáze podle root (vrchol stromu)
    def root_of(nid):
        seen = set()
        while nid in nodes and nodes[nid]['parent'] in nodes and nodes[nid]['parent'] not in seen:
            seen.add(nid)
            nid = nodes[nid]['parent']
        return nid
    comps = collections.defaultdict(list)
    for nid in rowsby:
        comps[root_of(nid)].append(nid)

    for root, phase_ids in comps.items():
        tphases = [p for p in phase_ids if rowsby[p]]
        if len(tphases) < 2:
            continue  # jednofázová soutěž → neměníme
        # základní fáze = ta s nejvíc týmy
        base = max(tphases, key=lambda p: len(members[p]))
        base_lvl = lvl(nodes.get(base, {}).get('level'))
        siblings = [p for p in tphases if p != base]
        # feeds_into (vítěz) / feeds_into_loser (poražený) základní fáze — priorita
        bn = nodes.get(base, {})
        wlab = sibling_label(nodes[bn['feeds']]) if bn.get('feeds') in nodes else None
        llab = sibling_label(nodes[bn['loser']]) if bn.get('loser') in nodes else None
        lmem = members.get(bn.get('loser'), set())
        wmem = members.get(bn.get('feeds'), set())
        # fallback: členství v sesterských fázích (jen když chybí feeds)
        dest = {}
        if not (wlab or llab):
            for s in siblings:
                lab = sibling_label(nodes.get(s, {}))
                if not lab:
                    continue
                for cid in members[s]:
                    if cid in members[base] and cid not in dest:
                        dest[cid] = lab
        # přepiš základní fázi
        for (sh, i, pos, cid, fate) in rowsby[base]:
            new = None
            if wlab or llab:
                if llab and cid in lmem:
                    new = llab
                elif wlab and cid not in lmem and (not wmem or cid in wmem):
                    new = wlab
            else:
                new = dest.get(cid)
            if new and new != fate:
                changes[(sh, i)] = new
        # koncová skupina o udržení: poslední=sestup, ostatní=udržel se
        for s in tphases:
            sl = sibling_label(nodes.get(s, {}))
            if sl == 'o udržení':
                for (sh, i, pos, cid, fate) in rowsby[s]:
                    if fate == 'setrval':
                        changes[(sh, i)] = 'udržel se'
        # flag: základní fáze pořád nese postup/sestup, co skript nevyřešil
        unresolved = [r for r in rowsby[base]
                      if (sh_i := (r[0], r[1])) not in changes and r[4] in ('postup', 'sestup')]
        if unresolved and not dest and not (wlab or llab):
            flags.append((nodes.get(base, {}).get('name', base), len(unresolved)))
    return changes, flags


def main():
    apply = '--apply' in sys.argv
    one = None
    if '--season' in sys.argv:
        one = sys.argv[sys.argv.index('--season') + 1]
    paths = ([os.path.join(DATA, f'S{one}_FINAL.xlsx')] if one
             else sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx'))))
    total = 0
    by_label = collections.Counter()
    all_flags = []
    touched = 0
    for path in paths:
        sid = re.search(r'S(\d{4}_\d{2})', os.path.basename(path)).group(1)
        changes, flags = season_changes(path)
        total += len(changes)
        for v in changes.values():
            by_label[v] += 1
        for nm, k in flags:
            all_flags.append((sid, nm, k))
        if apply and changes:
            wb = openpyxl.load_workbook(path)
            for sh in wb.sheetnames:
                if sh in NON_DATA:
                    continue
                ws = wb[sh]
                head = [c.value for c in ws[1]]
                if 'season_fate' not in head:
                    continue
                col = head.index('season_fate') + 1
                for (csh, ri), val in changes.items():
                    if csh == sh:
                        ws.cell(row=ri, column=col).value = val
            wb.save(path); wb.close(); touched += 1
    print(f"{'ZAPSÁNO' if apply else 'PREVIEW'}: {total} změn season_fate"
          + (f' (upraveno {touched} souborů)' if apply else ''))
    print("  rozpad podle nového štítku:")
    for k, v in by_label.most_common():
        print(f"    {v:6}  {k}")
    if all_flags:
        print(f"\n  ⚑ k ručnímu dořešení (víc fází, chybí feeds i tabulky): {len(all_flags)} soutěží")
        for sid, nm, k in all_flags[:25]:
            print(f"    {sid}  {str(nm)[:40]:40} ({k} týmů s postup/sestup)")
        if not apply:
            os.makedirs('docs', exist_ok=True)
            import csv
            with open('docs/FATE_REVIEW.csv', 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['sezona', 'soutez', 'tymu_s_postup_sestup'])
                for sid, nm, k in all_flags:
                    w.writerow([sid, nm, k])
            print('  → seznam k revizi: docs/FATE_REVIEW.csv')


if __name__ == '__main__':
    main()
