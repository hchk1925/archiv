#!/usr/bin/env python3
"""
polish_almanach.py — Leštící passy nad sezónními sešity.

A. Doplnění chybějících CLUBS řádků pro orphan standings.
B. Doplnění chybějícího season_fate §8 cross-refem.
C. Oprava city: odstranit z 'city' org. prefix/firmu, pokud city
   obsahuje slovo z clean_name a název města je rozpoznatelné.
D. Vyčištění hub prev_club_id: kde >=4 ne-B nástupců, ponech jen
   primárního (max overlap s názvem předchůdce), ostatním vymaž.
E. Doplnění top-level kvalifikací feeds_into (vč. ne-NODE id jako 'L15').

Re-runnable. Po doběhnutí: build_db.py + health.py.
"""
import openpyxl, glob, os, re, sys
from collections import defaultdict

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
NON_DATA = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA', 'TODO'}
ORG_PREFIX = re.compile(
    r'^(TJ|HC|VTJ|ASD|ZTJ|DSO|DŠO|DSJ|ZSJ|Sokol|SK|AC|AFK|SKP|KLH|KS|BK|HO|RH|ČH|VSJ|PDA|DA|VŠ|VŠS)\.?\s+',
    re.I)
LEVEL_RE = re.compile(r'L(\d+)')
B_SUF = re.compile(r'\s+(B|II|III|IV)\s*$')


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def lvl(v):
    if v is None:
        return None
    m = LEVEL_RE.search(str(v))
    return int(m.group(1)) if m else None


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


def season_of(p):
    m = re.search(r'S(\d{4})_(\d{2})', os.path.basename(p))
    return f"S{m.group(1)}_{m.group(2)}"


def load_clubs_dict(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['CLUBS']
    rr = list(ws.iter_rows(values_only=True))
    H = hidx(rr[0])
    out = {}
    for r in rr[1:]:
        if not r or r[H['club_id']] is None:
            continue
        out[r[H['club_id']]] = {
            'clean': r[H['clean_name']],
            'sheet': r[H.get('sheet', -1)] if 'sheet' in H else None,
            'level': r[H.get('level', -1)] if 'level' in H else None,
            'city': r[H['city']] if 'city' in H else None,
            'prev': r[H['prev_club_id']] if 'prev_club_id' in H else None,
        }
    wb.close()
    return out


# ─────────── Phase A: orphan standings → doplnit do CLUBS ───────────
def phase_a(path, season):
    wb = openpyxl.load_workbook(path)
    if 'CLUBS' not in wb.sheetnames:
        wb.close()
        return 0
    ws = wb['CLUBS']
    rows = list(ws.iter_rows(values_only=True))
    H = hidx(rows[0])
    have = set(r[H['club_id']] for r in rows[1:] if r and r[H['club_id']])
    added = 0
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        dws = wb[sh]
        drows = list(dws.iter_rows(values_only=True))
        if not drows:
            continue
        DH = hidx(drows[0])
        if 'club_id' not in DH or 'club_name' not in DH:
            continue
        for r in drows[1:]:
            if not r:
                continue
            cid = r[DH['club_id']]
            if not cid or cid in have:
                continue
            new_row = [None] * len(rows[0])
            new_row[H['club_id']] = cid
            new_row[H['clean_name']] = r[DH['club_name']]
            new_row[H.get('raw_name', H['clean_name'])] = r[DH['club_name']]
            new_row[H['sheet']] = sh
            if 'level' in H and 'level' in DH:
                new_row[H['level']] = r[DH['level']]
            if 'prev_club_id' in H and 'prev_club_id' in DH:
                new_row[H['prev_club_id']] = r[DH['prev_club_id']]
            if 'change_note' in H:
                new_row[H['change_note']] = (
                    'TBD: doplněno z standings (orphan) [polish_almanach]')
            ws.append(new_row)
            have.add(cid)
            added += 1
    if added:
        wb.save(path)
    wb.close()
    return added


# ─────────── Phase B: season_fate doplnit §8 cross-refem ───────────
def phase_b(path, season, next_clubs):
    if not next_clubs:
        return 0
    # next_clubs už načtená dict ve formátu z load_clubs_dict
    prev_to_min_next = {}
    for ncid, nc in next_clubs.items():
        pp = nc['prev']
        if not pp:
            continue
        ln = lvl(nc['level'])
        if ln is None:
            continue
        if pp not in prev_to_min_next or ln < prev_to_min_next[pp]:
            prev_to_min_next[pp] = ln
    wb = openpyxl.load_workbook(path)
    filled = 0
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        is_kval = sh == 'KVAL' or sh.startswith('KVAL')
        dws = wb[sh]
        drows = list(dws.iter_rows())
        if not drows:
            continue
        DH = hidx([c.value for c in drows[0]])
        if 'club_id' not in DH or 'season_fate' not in DH:
            continue
        sfi, dci = DH['season_fate'], DH['club_id']
        lvi = DH.get('level')
        rti = DH.get('row_type')
        for row in drows[1:]:
            if rti is not None and row[rti].value != 'T':
                continue                            # fate jen pro T-řádky
            if row[sfi].value:
                continue
            cid = row[dci].value
            if not cid:
                continue
            ln = lvl(row[lvi].value) if lvi is not None else None
            if is_kval or ln in (15, 25, 35, 45):
                continue                            # D30
            nxt = prev_to_min_next.get(cid)
            if nxt is None:
                row[sfi].value = 'zanik'
            else:
                if ln is None:
                    continue
                if nxt < ln:
                    row[sfi].value = 'postup'
                elif nxt > ln:
                    row[sfi].value = 'sestup'
                else:
                    row[sfi].value = 'setrval'
                if ln == 15 and nxt == 20:
                    row[sfi].value = 'setrval'
            filled += 1
    if filled:
        wb.save(path)
    wb.close()
    return filled


# ─────────── Phase C: city cleanup ───────────
KNOWN_CITIES = set()                                   # naplní main


def phase_c(path, season):
    wb = openpyxl.load_workbook(path)
    if 'CLUBS' not in wb.sheetnames:
        return 0
    ws = wb['CLUBS']
    rows = list(ws.iter_rows())
    H = hidx([c.value for c in rows[0]])
    if 'city' not in H:
        wb.close()
        return 0
    cityi = H['city']
    cni = H.get('change_note')
    fixed = 0
    for row in rows[1:]:
        cy = str(row[cityi].value or '').strip()
        if not cy:
            continue
        # zachovat jednoslovné nebo "X-Y" / "X (Y)" / "X u Y" / "X nad Y" tvary
        if re.search(r'[\-(]|^\S+\s+(u|nad|pod|na|v|za)\s+\S+$', cy, re.I):
            continue
        words = cy.split()
        if len(words) <= 2:
            continue                                    # 1-2 slova nech být
        # hledej nejdelší známé město jako koncovou sekvenci slov
        best = None
        for n in range(min(len(words), 4), 0, -1):
            cand = ' '.join(words[-n:])
            if cand in KNOWN_CITIES:
                best = cand
                break
        if best and best != cy:
            row[cityi].value = best
            if cni is not None:
                old = row[cni].value
                tag = f"TBD: city '{cy}' → '{best}' (oříznut firemní prefix) [polish_almanach]"
                row[cni].value = (str(old) + ' || ' + tag) if old else tag
            fixed += 1
    if fixed:
        wb.save(path)
    wb.close()
    return fixed


# ─────────── Phase D: hub prev cleanup ───────────
def phase_d_global(season_paths):
    """Globální passa: najdi všechny prev_club_id s >=4 ne-B nástupci a
    ponech jen primárního (max name-overlap s předchůdcem); ostatním
    vymaž prev_club_id (s TBD)."""
    # postav cache CLUBS všech sezón
    by_season = {}
    for p in season_paths:
        by_season[season_of(p)] = load_clubs_dict(p)
    # děti per prev
    children = defaultdict(list)
    for sid, cls in by_season.items():
        for cid, c in cls.items():
            pp = c['prev']
            if not pp:
                continue
            if B_SUF.search(str(c['clean'] or '')):
                continue                              # B-týmy ignorovat
            children[pp].append((sid, cid))
    hubs = [(pp, kids) for pp, kids in children.items() if len(kids) >= 4]
    # najdi předchůdce a jeho jméno
    cleared = 0
    by_season_cleanups = defaultdict(set)             # season → cids to clear
    for pp, kids in hubs:
        # najdi předchůdce
        pm = re.search(r'CLUB_(S\d{4}_\d{2})_', str(pp))
        if not pm:
            continue
        ps = pm.group(1)
        if ps not in by_season:
            continue
        pred = by_season[ps].get(pp)
        if not pred:
            continue
        pred_tok = tokens(pred['clean']) - {'sokol', 'klub', 'tj', 'hc'}
        if not pred_tok:
            continue
        # ohodnoť nástupce
        scored = []
        for sid, cid in kids:
            kt = tokens(by_season[sid][cid]['clean']) - {'sokol', 'klub', 'tj', 'hc'}
            scored.append((len(kt & pred_tok), sid, cid))
        scored.sort(reverse=True)
        keep_sid, keep_cid = scored[0][1], scored[0][2]
        for sc, sid, cid in scored:
            if (sid, cid) == (keep_sid, keep_cid):
                continue
            if sc == scored[0][0] and sc >= 1:
                # tie na primárního: nechej víc kandidátů, ať to dořeší kolega
                continue
            by_season_cleanups[sid].add(cid)
    # aplikuj
    for sid, cids in by_season_cleanups.items():
        path = next(p for p in season_paths if season_of(p) == sid)
        wb = openpyxl.load_workbook(path)
        ws = wb['CLUBS']
        rows = list(ws.iter_rows())
        H = hidx([c.value for c in rows[0]])
        pi = H['prev_club_id']
        cni = H.get('change_note')
        ci = H['club_id']
        for row in rows[1:]:
            if row[ci].value in cids:
                row[pi].value = None
                if cni is not None:
                    old = row[cni].value
                    tag = ("TBD: prev_club_id vymazáno (hub-link, "
                           "nejisté pokračování) [polish_almanach]")
                    row[cni].value = (str(old) + ' || ' + tag) if old else tag
                cleared += 1
        # sync do dat. listů
        for sh in wb.sheetnames:
            if sh in NON_DATA:
                continue
            dws = wb[sh]
            drows = list(dws.iter_rows())
            if not drows:
                continue
            DH = hidx([c.value for c in drows[0]])
            if 'club_id' not in DH or 'prev_club_id' not in DH:
                continue
            for row in drows[1:]:
                if row[DH['club_id']].value in cids:
                    row[DH['prev_club_id']].value = None
        wb.save(path)
        wb.close()
    return cleared


# ─────────── Phase G: sjednocení fate pro stejný cid v rámci sezóny ───────────
FATE_PREC = ['zanik', 'slouceni', 'reorganizace', 'postup', 'sestup',
             'setrval', 'setrval?']


def phase_g(path, season):
    wb = openpyxl.load_workbook(path)
    cid_fate = defaultdict(lambda: defaultdict(list))
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        if sh == 'KVAL' or sh.startswith('KVAL'):
            continue
        dws = wb[sh]
        drows = list(dws.iter_rows())
        if not drows:
            continue
        DH = hidx([c.value for c in drows[0]])
        if 'club_id' not in DH or 'season_fate' not in DH:
            continue
        for row in drows[1:]:
            cid = row[DH['club_id']].value
            ft = row[DH['season_fate']].value
            if cid and ft:
                cid_fate[cid][str(ft).strip()].append(row[DH['season_fate']])
    unified = 0
    for cid, fm in cid_fate.items():
        if len(fm) <= 1:
            continue
        for f in FATE_PREC:
            if f in fm:
                chosen = f
                break
        else:
            chosen = next(iter(fm))
        for f, cells in fm.items():
            if f == chosen:
                continue
            for cc in cells:
                cc.value = chosen
        unified += 1
    if unified:
        wb.save(path)
    wb.close()
    return unified


# ─────────── Phase F: oprava city dle clean_name (2+ slovné město) ───────────
def phase_f(path, season, multi_cities):
    wb = openpyxl.load_workbook(path)
    if 'CLUBS' not in wb.sheetnames:
        return 0
    ws = wb['CLUBS']
    rows = list(ws.iter_rows())
    H = hidx([c.value for c in rows[0]])
    if 'city' not in H or 'clean_name' not in H:
        wb.close()
        return 0
    cityi, ni = H['city'], H['clean_name']
    cni = H.get('change_note')
    # seřaď známá vícevýrazová města podle délky (sestup), ať berou nejdelší
    cands = sorted(multi_cities, key=lambda x: -len(x))
    fixed = 0
    for row in rows[1:]:
        nm = str(row[ni].value or '')
        cy = str(row[cityi].value or '').strip()
        if not nm:
            continue
        match = None
        for cand in cands:
            if cand in nm:
                match = cand
                break
        if not match:
            continue
        if cy == match:
            continue
        # nepřepisuj pokud aktuální city je „X-Y" / „X (Y)" varianta téhož základu
        base = match.split()[-1]
        if cy and base in cy:
            continue
        row[cityi].value = match
        if cni is not None:
            old = row[cni].value
            tag = (f"TBD: city '{cy or '(prázdné)'}' → '{match}' "
                   f"(odvozeno z názvu klubu) [polish_almanach]")
            row[cni].value = (str(old) + ' || ' + tag) if old else tag
        fixed += 1
    if fixed:
        wb.save(path)
    wb.close()
    return fixed


# ─────────── Phase E: feeds_into pro top-level kvalifikace ───────────
def phase_e(path, season):
    wb = openpyxl.load_workbook(path)
    if 'SYSTEM' not in wb.sheetnames:
        wb.close()
        return 0
    ws = wb['SYSTEM']
    rows = list(ws.iter_rows())
    H = hidx([c.value for c in rows[0]])
    ni = H['node_id']; nmi = H['name']; cti = H['competition_type']
    lvi = H['level']; pari = H['parent_node_id']; fii = H['feeds_into']
    nodes = []
    for r in rows[1:]:
        if r[ni].value is None:
            continue
        # úroveň: z level sloupce nebo z node_id (např. "L15")
        ln = lvl(r[lvi].value)
        if ln is None:
            ln = lvl(r[ni].value)
        nodes.append({
            'id': r[ni].value, 'name': str(r[nmi].value or ''),
            'ct': str(r[cti].value or ''), 'lvl': ln,
            'par': r[pari].value, 'fi': r[fii].value, 'row': r,
        })
    league_by_lvl = {}
    for n in nodes:
        if n['ct'] == 'league' and n['par'] is None and n['lvl'] is not None:
            nat = not re.match(r'^\d0[_ ]', n['name'])
            k = (0 if nat else 1, n['id'])
            if n['lvl'] not in league_by_lvl or k < league_by_lvl[n['lvl']][0]:
                league_by_lvl[n['lvl']] = (k, n['id'])
    lvls = sorted(league_by_lvl.keys())
    added = 0
    for n in nodes:
        if n['fi']:
            continue
        is_q = (n['ct'] in ('baraz', 'qualification_group') or
                re.match(r'^(Kvalifikace|Baráž|KVAL)\b', n['name'], re.I) or
                str(n['id']).startswith('L'))           # L15/L25 node ids
        if not is_q or n['lvl'] is None:
            continue
        if n['par'] is not None:
            continue
        below = [L for L in lvls if L < n['lvl']]
        if not below:
            continue
        tgt = league_by_lvl[max(below)][1]
        n['row'][fii].value = tgt
        added += 1
    if added:
        wb.save(path)
    wb.close()
    return added


def main():
    global KNOWN_CITIES
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    seasons = [season_of(p) for p in files]
    s_by = dict(zip(seasons, files))
    # postav KNOWN_CITIES (město použito 5+×)
    city_freq = defaultdict(int)
    for p in files:
        for c in load_clubs_dict(p).values():
            cy = str(c['city'] or '').strip()
            if cy:
                city_freq[cy] += 1
    # KNOWN_CITIES: jen "čisté" tvary (≤2 slova, nebo X-Y / X (Y) / X u Y),
    # výskyt 5+×. Akumulátorům/Spartakům dveře zavřeny i kdyby se opakovali.
    candidates = {c for c, n in city_freq.items() if n >= 5}
    KNOWN_CITIES = set()
    for c in candidates:
        if re.search(r'\d', c):
            continue
        w = c.split()
        if len(w) <= 2:
            KNOWN_CITIES.add(c)
        elif re.search(r'[\-(]', c):
            KNOWN_CITIES.add(c)
        elif re.match(r'^\S+\s+(u|nad|pod|na|v|za)\s+\S+(\s+\S+)?$', c, re.I):
            KNOWN_CITIES.add(c)
    print(f"  známých měst (5+ výskytů): {len(KNOWN_CITIES)}")
    # next-season clubs cache (pro Phase B)
    next_cache = {}
    for i, s in enumerate(seasons[:-1]):
        next_cache[s] = load_clubs_dict(s_by[seasons[i + 1]])
    next_cache[seasons[-1]] = None

    multi_cities = {c for c in KNOWN_CITIES if len(c.split()) >= 2
                    and not re.search(r'[\-(]', c)}
    print(f"  vícevýrazových měst (pro Phase F): {len(multi_cities)}")
    totA = totB = totC = totE = totF = totG = 0
    for p in files:
        s = season_of(p)
        a = phase_a(p, s)
        b = phase_b(p, s, next_cache[s])
        cf = phase_c(p, s)
        e = phase_e(p, s)
        f = phase_f(p, s, multi_cities)
        g = phase_g(p, s)
        totA += a; totB += b; totC += cf; totE += e; totF += f; totG += g
        if a + b + cf + e + f + g:
            print(f"  ✓ {s}: A={a} B={b} C={cf} E={e} F={f} G={g}")
    totD = phase_d_global(files)
    print(f"\n=== SOUHRN ===")
    print(f"  A. orphan CLUBS doplněno:        {totA}")
    print(f"  B. fate cross-refem doplněno:    {totB}")
    print(f"  C. city očištěno (firemní prefix):{totC}")
    print(f"  D. hub prev_club_id vymazáno:    {totD}")
    print(f"  E. feeds_into doplněno:          {totE}")
    print(f"  F. city opraveno dle názvu klubu:{totF}")
    print(f"  G. fate sjednoceno (cid):        {totG}")


if __name__ == '__main__':
    main()
