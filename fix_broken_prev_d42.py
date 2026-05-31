#!/usr/bin/env python3
"""
fix_broken_prev_d42.py — Druhé kolo oprav rozbitých prev_club_id.

Pro zbylých ~20 rozbitých linků (D42 registr + city-token):
  - score-pattern řádky (parsing error) → odstranit (Phase 0 redux)
  - city/jméno-token shoda v předchozí sezóně → fix s 'TBD:' flagem
  - víc kandidátů / žádný → ponechat (řeší kolega)

Re-runnable. Po doběhnutí spusť apply_todo_sheets.py a build_db.py.
"""
import openpyxl, glob, os, re, sys
from collections import defaultdict

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
NON_DATA = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA', 'TODO'}
ORG_PREFIX = re.compile(
    r'^(TJ|HC|VTJ|ASD|ZTJ|DSO|DŠO|DSJ|ZSJ|Sokol|SK|AC|AFK|SKP|KLH|KS|BK|HO|RH|ČH|VSJ|PDA|DA|VŠ|VŠS)\.?\s+',
    re.I)
SCORE_RE = re.compile(r'\d+\s*[:\-–]\s*\d+')

# D42 nápověda: keyword v aktuálním názvu → keywordy v předchůdci
D42_HINTS = [
    (r'Sparta\s+ČKD|Sparta\s+Praha', ['Spartak Praha Sokolovo', 'Spartak Sokolovo']),
    (r'Bohemians', ['ČKD Praha', 'Bohemians']),
    (r'Baník Kladno|SONP Kladno|Poldi', ['SONP Kladno', 'Sokol SONP', 'Baník SONP', 'TJ SONP']),
    (r'BK Mladá Boleslav|Spartak.*Boleslav|Škoda Mladá Boleslav|AZNP', ['Mladá Boleslav', 'Spartak Mladá Boleslav', 'Škoda Mladá Boleslav']),
]


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def core(name):
    if not name:
        return ''
    s = str(name).strip()
    s = re.sub(r'\s*\([^)]*\)\s*', ' ', s)
    prev = None
    while prev != s:
        prev = s
        s = ORG_PREFIX.sub('', s).strip()
    s = re.sub(r'\s+(B|II|III|IV)\s*$', '', s)
    return re.sub(r'\s+', ' ', s).strip().lower()


def tokens(s):
    return set(re.findall(r"[A-Za-zÁ-ž]{3,}", str(s or '').lower()))


def city_norm(s):
    if not s:
        return ''
    s = re.sub(r'\s*\([^)]*\)\s*', '', str(s))      # bez disambig závorek
    return s.strip().lower()


def is_pseudo_score(name, city):
    nm = str(name or '')
    cy = str(city or '')
    return bool(SCORE_RE.search(nm) and SCORE_RE.search(cy))


def load_season_clubs(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['CLUBS']; rows = list(ws.iter_rows(values_only=True))
    H = hidx(rows[0])
    out = {}
    for r in rows[1:]:
        if not r or r[H['club_id']] is None:
            continue
        out[r[H['club_id']]] = {
            'clean': r[H['clean_name']], 'sheet': r[H.get('sheet', -1)] if 'sheet' in H else None,
            'city': r[H['city']] if 'city' in H else None,
        }
    wb.close()
    return out


def find_candidate(target, prev_clubs):
    tname = str(target['clean'] or '')
    tcore = core(tname)
    tcity = city_norm(target['city'])
    tsheet = target['sheet']
    ttok = tokens(tname) | tokens(target['city'])
    t_is_b = bool(re.search(r'\s+(B|II|III|IV)\s*$', tname))

    hint_set = []
    for pat, hints in D42_HINTS:
        if re.search(pat, tname, re.I):
            hint_set = [h.lower() for h in hints]
            break

    scored = []
    for pid, pc in prev_clubs.items():
        pname = str(pc['clean'] or '')
        pcity = city_norm(pc['city'])
        psheet = pc['sheet']
        pcore = core(pname)
        ptok = tokens(pname) | tokens(pc['city'])
        p_is_b = bool(re.search(r'\s+(B|II|III|IV)\s*$', pname))
        sc = 0
        if hint_set and any(h in pname.lower() for h in hint_set):
            sc += 5
        if tcore and pcore == tcore:
            sc += 4
        if tcity and tcity == pcity:
            sc += 3
        common = ttok & ptok - {'sokol', 'praha', 'klub', 'tj', 'hc'}
        sc += min(len(common), 3)
        if tsheet and psheet:
            if str(tsheet).split('_')[0] == str(psheet).split('_')[0]:
                sc += 1
        # B/A symetrie: B preferuje B, A preferuje A
        if t_is_b != p_is_b:
            sc -= 3
        if sc >= 3:
            scored.append((sc, pid, pname))
    scored.sort(reverse=True)
    if not scored:
        return None, None
    # tolerance ties: 1 bod stačí (B/A penalty už odstínilo většinu)
    if len(scored) == 1 or scored[0][0] - scored[1][0] >= 1:
        return scored[0][1], scored[0][2]
    return None, None


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    seasons = [re.search(r'S\d{4}_\d{2}', f).group(0) for f in files]
    s_by = dict(zip(seasons, files))
    clubs_cache = {s: load_season_clubs(p) for s, p in s_by.items()}
    # valid set
    valid = {(s, cid) for s, cls in clubs_cache.items() for cid in cls}

    # najít rozbité
    broken = []
    for sid, cls in clubs_cache.items():
        wb = openpyxl.load_workbook(s_by[sid], read_only=True, data_only=True)
        ws = wb['CLUBS']; rows = list(ws.iter_rows(values_only=True))
        H = hidx(rows[0])
        for r in rows[1:]:
            if not r or r[H['club_id']] is None:
                continue
            cid = r[H['club_id']]
            pcid = r[H['prev_club_id']]
            if not pcid:
                continue
            m = re.search(r'CLUB_(S\d{4}_\d{2})_', str(pcid))
            ps = m.group(1) if m else None
            if not ps or (ps, pcid) not in valid:
                broken.append((sid, cid, r[H['clean_name']],
                               r[H['city']] if 'city' in H else None,
                               r[H.get('sheet', -1)] if 'sheet' in H else None,
                               pcid, ps))
        wb.close()

    print(f"Rozbitých prev: {len(broken)}\n")
    by_season_changes = defaultdict(list)
    pseudo = []
    fixed = []
    skipped = []
    for sid, cid, nm, cty, sh, pcid, ps in broken:
        if is_pseudo_score(nm, cty):
            pseudo.append((sid, cid, nm))
            by_season_changes[sid].append(('PSEUDO', cid, None, None))
            continue
        if ps not in clubs_cache:
            skipped.append((sid, cid, nm, 'prev sezóna mimo rozsah'))
            continue
        cand, cand_name = find_candidate(
            {'clean': nm, 'city': cty, 'sheet': sh}, clubs_cache[ps])
        if cand:
            fixed.append((sid, cid, nm, cand, cand_name))
            by_season_changes[sid].append(('FIX', cid, cand, cand_name))
        else:
            # bez kandidáta: rozbitý pointer je horší než prázdný
            skipped.append((sid, cid, nm, 'bez kandidáta → vymazáno'))
            by_season_changes[sid].append(('CLEAR', cid, None, None))

    print(f"  → pseudo k odstranění: {len(pseudo)}")
    print(f"  → fix z D42/city: {len(fixed)}")
    print(f"  → ponecháno pro kolegu: {len(skipped)}\n")

    # APLIKACE
    for sid, changes in by_season_changes.items():
        path = s_by[sid]
        wb = openpyxl.load_workbook(path)
        ws = wb['CLUBS']
        rows = list(ws.iter_rows())
        H = hidx([c.value for c in rows[0]])
        ci, pi = H['club_id'], H['prev_club_id']
        cni = H.get('change_note')
        # mapy: cid -> action
        actions = {cid: (kind, target, tname) for kind, cid, target, tname in changes}
        # PSEUDO: smaž CLUBS řádek + data-sheet řádky
        to_del = []
        for r_i, row in enumerate(rows[1:], start=2):
            cid = row[ci].value
            if cid in actions:
                kind, tgt, tnm = actions[cid]
                if kind == 'PSEUDO':
                    to_del.append(r_i)
                elif kind == 'FIX':
                    row[pi].value = tgt
                    if cni is not None:
                        old = row[cni].value
                        tag = (f"TBD: auto-prev_club_id (D42/city) → {tgt} "
                               f"'{tnm}'; ověřit [fix_broken_prev_d42]")
                        row[cni].value = (str(old) + ' || ' + tag) if old else tag
                elif kind == 'CLEAR':
                    row[pi].value = None
                    if cni is not None:
                        old = row[cni].value
                        tag = ("TBD: prev_club_id vymazáno (mířil na neexist. ID, "
                               "žádný kandidát v předchozí sezóně) [fix_broken_prev_d42]")
                        row[cni].value = (str(old) + ' || ' + tag) if old else tag
        for i in sorted(to_del, reverse=True):
            ws.delete_rows(i, 1)
        # smaž data-sheet řádky pseudo + sync prev v data sheets
        pseudo_ids = {cid for cid, a in actions.items() if a[0] == 'PSEUDO'}
        fix_map = {cid: a[1] for cid, a in actions.items() if a[0] == 'FIX'}
        clear_ids = {cid for cid, a in actions.items() if a[0] == 'CLEAR'}
        for sh in wb.sheetnames:
            if sh in NON_DATA:
                continue
            dws = wb[sh]; drows = list(dws.iter_rows())
            if not drows:
                continue
            DH = hidx([c.value for c in drows[0]])
            if 'club_id' not in DH:
                continue
            dci = DH['club_id']
            dpi = DH.get('prev_club_id')
            ddel = []
            for r_i, row in enumerate(drows[1:], start=2):
                cid = row[dci].value
                if cid in pseudo_ids:
                    ddel.append(r_i)
                elif dpi is not None:
                    if cid in fix_map:
                        row[dpi].value = fix_map[cid]
                    elif cid in clear_ids:
                        row[dpi].value = None
            for i in sorted(ddel, reverse=True):
                dws.delete_rows(i, 1)
        wb.save(path)
        print(f"  ✓ {sid}: {len(changes)} změn")

    # log
    with open('CHANGELOG_d42.md', 'w', encoding='utf-8') as fh:
        fh.write("# D42 / 2. kolo oprav rozbitých prev_club_id\n\n")
        if pseudo:
            fh.write(f"## Odstraněno jako pseudo-klub ({len(pseudo)})\n\n")
            for sid, cid, nm in pseudo:
                fh.write(f"- `{sid}` {cid} '{nm}'\n")
        if fixed:
            fh.write(f"\n## Opraveno (TBD-flag) ({len(fixed)})\n\n")
            for sid, cid, nm, cand, cname in fixed:
                fh.write(f"- `{sid}` {cid} '{nm}' → {cand} '{cname}'\n")
        if skipped:
            fh.write(f"\n## Ponecháno kolegovi ({len(skipped)})\n\n")
            for sid, cid, nm, why in skipped:
                fh.write(f"- `{sid}` {cid} '{nm}' — {why}\n")
    print("\nViz CHANGELOG_d42.md")


if __name__ == '__main__':
    main()
