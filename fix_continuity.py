#!/usr/bin/env python3
"""
fix_continuity.py — Finalizace návazností v hokejovém almanachu.

Re-runnable. Zpracuje všechny S*_FINAL.xlsx ve --dir (default: data/).

Fáze:
  0. Odstranění parsing-error pseudo-klubů ('finále', skóre řádky, K MAZÁNÍ).
  1. Oprava prev_club_id (rozbité + chybějící) v CLUBS + sync do datových listů.
  2. Konzistence season_fate (D30 KVAL cleanup + řešení nekonzistencí cross-refem §8).
  3. SYSTEM feeds_into — můstky kvalifikace/baráž → cílová soutěž (postupy mezi soutěžemi).

Bezpečnost:
  - Nikdy nemění club_id / node_id / tr_id.
  - Phase 3 nikdy nepřepisuje existující feeds_into (jen doplňuje prázdné).
  - Nejisté případy → TODO_continuity.md (pravidlo D40), ne hádání.
  - Auto-linky značeny 'TBD:' v change_note (D19/D24) pro pozdější verifikaci.
"""
import openpyxl, glob, os, re, sys, argparse, datetime
from collections import defaultdict, Counter

NON_DATA = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA'}
ORG_PREFIX = re.compile(
    r'^(TJ|HC|VTJ|ASD|ZTJ|DSO|DŠO|DSJ|ZSJ|Sokol|SK|AC|AFK|SKP|KLH|KS|BK|HO|RH|ČH|VSJ|PDA|DA|VŠ|VŠS)\.?\s+',
    re.I)
SCORE_RE = re.compile(r'\d+\s*[:\-–]\s*\d+')
FLAG_RE = re.compile(r'PARSING ERROR|K MAZÁN|není klub|MAZÁN[ÍI]', re.I)
JUNK_NAMES = {'finále', 'finale', 'o udržení', 'o postup', 'baráž', 'play off',
              'playoff', 'semifinále', 'čtvrtfinále', 'finálová skupina',
              'kvalifikace', 'nadstavba', 'o 3. místo', 'o 5. místo'}
LEVEL_RE = re.compile(r'L(\d+)')

LOG = []
TODO = []


def log(msg):
    LOG.append(msg)


def todo(season, msg):
    TODO.append(f"[{season}] {msg}")


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def season_of(path):
    m = re.search(r'S(\d{4})_(\d{2})', os.path.basename(path))
    return f"{m.group(1)}_{m.group(2)}"


def norm_core(name):
    """Jádro názvu pro párování: bez org. prefixů, B/II suffixů, závorek, diakritiky-insensitive lower."""
    if name is None:
        return ''
    s = str(name).strip()
    s = re.sub(r'\s*\([^)]*\)\s*', ' ', s)          # odstranit závorkové anotace
    prev = None
    while prev != s:                                  # opakovaně strip org prefix
        prev = s
        s = ORG_PREFIX.sub('', s).strip()
    s = re.sub(r'\s+(B|II|III|IV|C)\s*$', '', s)      # B/II/.. suffix
    s = re.sub(r'[^\wÁ-ž ]', ' ', s, flags=re.U)
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s


def is_pseudo(clean_name, change_note):
    nm = str(clean_name or '').strip()
    nl = nm.lower()
    cn = str(change_note or '')
    if FLAG_RE.search(cn):
        return 'flagged'
    if nl in JUNK_NAMES:
        return 'junk_name'
    # čistý skóre/zápasový řádek bez delšího klubového jádra
    if SCORE_RE.search(nm):
        core = SCORE_RE.sub('', nm).strip(' -–:')
        if len(re.sub(r'[^A-Za-zÁ-ž]', '', core)) < 4:
            return 'score_pattern'
    return None


# ───────────────────────── Phase 0 ─────────────────────────
def phase0_remove_pseudo(wb, season):
    ws = wb['CLUBS']
    rows = list(ws.iter_rows(values_only=True))
    H = hidx(rows[0])
    ci, ni = H['club_id'], H['clean_name']
    cni = H.get('change_note')
    removed = {}
    del_idx = []
    for r_i, r in enumerate(rows[1:], start=2):
        if not r or r[ci] is None:
            continue
        reason = is_pseudo(r[ni], r[cni] if cni is not None else None)
        if reason:
            removed[r[ci]] = (str(r[ni]), reason)
            del_idx.append(r_i)
    if not removed:
        return set()
    for i in sorted(del_idx, reverse=True):
        ws.delete_rows(i, 1)
    # smazat odpovídající řádky v datových listech
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        dws = wb[sh]
        drows = list(dws.iter_rows(values_only=True))
        if not drows:
            continue
        DH = hidx(drows[0])
        if 'club_id' not in DH:
            continue
        dci = DH['club_id']
        dd = [i for i, rr in enumerate(drows[1:], start=2)
              if rr and rr[dci] in removed]
        for i in sorted(dd, reverse=True):
            dws.delete_rows(i, 1)
    for cid, (nm, why) in sorted(removed.items()):
        log(f"  P0 [{season}] removed pseudo {cid} '{nm}' ({why})")
    return set(removed.keys())


# ───────────────────────── model loaders ─────────────────────────
def read_clubs(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['CLUBS']
    rows = list(ws.iter_rows(values_only=True))
    H = hidx(rows[0])
    out = {}
    for r in rows[1:]:
        if not r or r[H['club_id']] is None:
            continue
        cid = r[H['club_id']]
        out[cid] = {
            'clean': r[H['clean_name']],
            'sheet': r[H.get('sheet', -1)] if 'sheet' in H else None,
            'level': r[H['level']] if 'level' in H else None,
            'city': r[H['city']] if 'city' in H else None,
            'prev': r[H['prev_club_id']] if 'prev_club_id' in H else None,
            'core': norm_core(r[H['clean_name']]),
        }
    wb.close()
    return out


# ───────────────────────── Phase 1 ─────────────────────────
def find_prev_candidate(club, prev_clubs):
    """Vrátí (cid, jistota) nebo (None, None). jistota: 'strong'|'weak'."""
    core = club['core']
    if not core:
        return None, None
    city = (club['city'] or '').strip().lower()
    by_core = [pid for pid, pc in prev_clubs.items() if pc['core'] == core]
    if not by_core:
        return None, None
    if len(by_core) == 1:
        pc = prev_clubs[by_core[0]]
        pcity = (pc['city'] or '').strip().lower()
        if city and pcity and city == pcity:
            return by_core[0], 'strong'
        if not city or not pcity:
            return by_core[0], 'strong'
        return by_core[0], 'weak'           # jméno sedí, město liší → D24 best-guess
    # víc kandidátů → rozhodni městem
    same_city = [pid for pid in by_core
                 if (prev_clubs[pid]['city'] or '').strip().lower() == city and city]
    if len(same_city) == 1:
        return same_city[0], 'strong'
    return None, None                        # ambiguózní → TODO


def phase1_prev_links(wb, season, prev_clubs, removed_prev):
    """Opraví CLUBS.prev_club_id, vrátí mapu cid->final_prev pro sync do dat. listů."""
    ws = wb['CLUBS']
    rows = list(ws.iter_rows())
    H = hidx([c.value for c in rows[0]])
    ci = H['club_id'] + 1
    ni = H['clean_name'] + 1
    pi = H['prev_club_id'] + 1
    cni = (H['change_note'] + 1) if 'change_note' in H else None
    cityi = (H['city'] + 1) if 'city' in H else None
    # postav model aktuální sezóny
    cur = {}
    for row in rows[1:]:
        cid = row[ci - 1].value
        if cid is None:
            continue
        cur[cid] = {
            'clean': row[ni - 1].value,
            'core': norm_core(row[ni - 1].value),
            'city': row[cityi - 1].value if cityi else None,
            'prev': row[pi - 1].value,
            'row': row,
        }
    prev_ids = set(prev_clubs.keys()) if prev_clubs is not None else set()
    final_prev = {}
    fixed = filled = cleared = ambiguous = 0
    for cid, c in cur.items():
        p = c['prev']
        final_prev[cid] = p
        if prev_clubs is None:                       # první sezóna
            continue
        broken = p is not None and p not in prev_ids
        missing = p is None
        if not broken and not missing:
            continue
        if broken and p in removed_prev:
            c['row'][pi - 1].value = None
            final_prev[cid] = None
            cleared += 1
            todo(season, f"{cid} '{c['clean']}' prev mířil na smazaný pseudo-klub {p} → vymazáno")
            continue
        cand, conf = find_prev_candidate(
            {'core': c['core'], 'city': c['city']}, prev_clubs)
        if cand is None:
            if broken:
                ambiguous += 1
                todo(season, f"{cid} '{c['clean']}' ROZBITÝ prev {p} (neexist.), "
                             f"bez jednoznačného kandidáta — ponecháno")
            continue
        c['row'][pi - 1].value = cand
        final_prev[cid] = cand
        tag = (f"TBD: auto-prev_club_id {('oprava' if broken else 'doplnění')} → {cand} "
               f"({conf}, jméno+město; verifikovat) [fix_continuity]")
        if cni is not None:
            old = c['row'][cni - 1].value
            c['row'][cni - 1].value = (str(old) + ' || ' + tag) if old else tag
        else:
            todo(season, f"{cid} '{c['clean']}' {tag} (sezóna bez change_note sloupce)")
        if broken:
            fixed += 1
        else:
            filled += 1
        if conf == 'weak':
            todo(season, f"{cid} '{c['clean']}' prev→{cand} jen dle jména "
                         f"(město liší) — ověřit (D24)")
    # sync do datových listů
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
        dci, dpi = DH['club_id'], DH['prev_club_id']
        for row in drows[1:]:
            cid = row[dci].value
            if cid in final_prev and final_prev[cid] != row[dpi].value:
                row[dpi].value = final_prev[cid]
    log(f"  P1 [{season}] prev: opraveno={fixed} doplněno={filled} "
        f"vymazáno(pseudo)={cleared} ambiguózní→TODO={ambiguous}")
    return fixed, filled, cleared, ambiguous


# ───────────────────────── Phase 2 ─────────────────────────
FATE_PREC = ['zanik', 'slouceni', 'reorganizace', 'postup', 'sestup',
             'setrval', 'setrval?']


def lvl_num(v):
    if v is None:
        return None
    m = LEVEL_RE.search(str(v))
    return int(m.group(1)) if m else None


def phase2_fate(wb, season, next_clubs):
    """D30 KVAL cleanup + řešení nekonzistencí (cross-ref §8, fallback precedence)."""
    # next-season cross-ref mapa: prev_cid -> min level v příští sezóně
    prev_to_min_next = {}
    if next_clubs:
        for ncid, nc in next_clubs.items():
            pp = nc['prev']
            if not pp:
                continue
            ln = lvl_num(nc['level'])
            if ln is None:
                continue
            if pp not in prev_to_min_next or ln < prev_to_min_next[pp]:
                prev_to_min_next[pp] = ln
    kval_cleared = 0
    cid_fate = defaultdict(lambda: defaultdict(list))   # cid -> fate -> [cells]
    cid_lvl = {}
    cid_name = {}
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        dws = wb[sh]
        drows = list(dws.iter_rows())
        if not drows:
            continue
        DH = hidx([c.value for c in drows[0]])
        if 'season_fate' not in DH or 'club_id' not in DH:
            continue
        sfi, dci = DH['season_fate'], DH['club_id']
        lvi = DH.get('level')
        is_kval = sh == 'KVAL' or sh.startswith('KVAL')
        for row in drows[1:]:
            cid = row[dci].value
            ft = row[sfi].value
            lvl = row[lvi].value if lvi is not None else None
            ln = lvl_num(lvl)
            if ft and (is_kval or ln in (15, 25, 35, 45)):
                row[sfi].value = None              # D30
                kval_cleared += 1
                continue
            if cid and ft:
                cid_fate[cid][str(ft).strip()].append(row[sfi])
                if cid not in cid_lvl or (ln is not None and
                                          (cid_lvl[cid] is None or ln < cid_lvl[cid])):
                    cid_lvl[cid] = ln
                cid_name[cid] = cid
    resolved = 0
    for cid, fm in cid_fate.items():
        if len(fm) <= 1:
            continue
        chosen = None
        # 1) cross-ref §8
        nxt = prev_to_min_next.get(cid)
        cur_lv = cid_lvl.get(cid)
        if nxt is not None and cur_lv is not None:
            if nxt < cur_lv:
                chosen = 'postup'
            elif nxt > cur_lv:
                chosen = 'sestup'
            else:
                chosen = 'setrval'
            if cur_lv == 15 and nxt == 20:
                chosen = 'setrval'
        # cross-ref hodnota musí být mezi reálně přítomnými, jinak fallback
        if chosen not in fm:
            chosen = None
        # 2) fallback precedence
        if chosen is None:
            if next_clubs and cid not in prev_to_min_next:
                if 'zanik' in fm:
                    chosen = 'zanik'
                elif 'slouceni' in fm:
                    chosen = 'slouceni'
            if chosen is None:
                for f in FATE_PREC:
                    if f in fm:
                        chosen = f
                        break
        for f, cells in fm.items():
            if f == chosen:
                continue
            for cell in cells:
                cell.value = chosen
        resolved += 1
        todo(season, f"{cid} fate nekonzist. {sorted(fm)} → '{chosen}' "
                     f"(cross-ref={'ano' if nxt is not None else 'ne'}) — ověřit")
    log(f"  P2 [{season}] KVAL fate vymazáno={kval_cleared} "
        f"nekonzistencí vyřešeno={resolved}")
    return kval_cleared, resolved


# ───────────────────────── Phase 3 ─────────────────────────
def phase3_feeds(wb, season):
    ws = wb['SYSTEM']
    rows = list(ws.iter_rows())
    H = hidx([c.value for c in rows[0]])
    ni, nmi, cti = H['node_id'], H['name'], H['competition_type']
    lvi, pari = H['level'], H['parent_node_id']
    fii, fli = H['feeds_into'], H['feeds_into_loser']
    nodes = []
    for row in rows[1:]:
        if row[ni].value is None:
            continue
        nodes.append({
            'id': row[ni].value, 'name': str(row[nmi].value or ''),
            'ct': str(row[cti].value or ''), 'lvl': lvl_num(row[lvi].value),
            'par': row[pari].value, 'fi': row[fii].value, 'fl': row[fli].value,
            'row': row, 'fii': fii, 'fli': fli,
        })
    # cílové ligové kotvy: competition_type 'league', parent None;
    # národní (bez 30_/40_ region prefixu) přednostně
    league_by_lvl = {}
    for n in nodes:
        if n['ct'] == 'league' and n['par'] is None and n['lvl'] is not None:
            national = not re.match(r'^\d0[_ ]', n['name'])
            key = n['lvl']
            cand = (0 if national else 1, n['id'])
            if key not in league_by_lvl or cand < league_by_lvl[key][0]:
                league_by_lvl[key] = (cand, n['id'])
    league_lvls = sorted(league_by_lvl.keys())
    added = 0
    for n in nodes:
        if n['fi']:
            continue                                  # nikdy nepřepisovat
        is_qual = (n['ct'] in ('baraz', 'qualification_group') or
                   re.match(r'^(Kvalifikace|Baráž|KVAL)\b', n['name'], re.I))
        if not is_qual or n['lvl'] is None:
            continue
        # Jen TOP-LEVEL kvalifikační kotvy (parent=None). Vnořené baráže
        # (parent=liga) mají v moderní éře nejednoznačné cíle kvůli názvosloví
        # („1.liga" = 2. úroveň po 2000) → D40: TODO, nehádat.
        if n['par'] is not None:
            todo(season, f"SYSTEM {n['id']} '{n['name'][:40]}' (L{n['lvl']}, "
                         f"parent={n['par']}) vnořená baráž — feeds_into "
                         f"ponecháno prázdné (ověřit cíl ručně)")
            continue
        # cílová liga = nejvyšší ligová úroveň striktně pod úrovní baráže
        target_lvls = [L for L in league_lvls if L < n['lvl']]
        if not target_lvls:
            todo(season, f"SYSTEM {n['id']} '{n['name'][:40]}' (L{n['lvl']}) "
                         f"baráž bez určitelné cílové ligy — feeds_into prázdné")
            continue
        tgt_lvl = max(target_lvls)
        tgt = league_by_lvl[tgt_lvl][1]
        n['row'][n['fii']].value = tgt
        added += 1
    log(f"  P3 [{season}] feeds_into doplněno (baráž→cílová liga)={added}")
    return added


# ───────────────────────── driver ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default='data')
    ap.add_argument('--only-season', default=None,
                    help='zpracuj jen tuto sezónu (např. 1955_56) pro test')
    args = ap.parse_args()
    files = sorted(glob.glob(os.path.join(args.dir, 'S*_FINAL.xlsx')))
    if not files:
        print('Žádné soubory.')
        return
    # pre-pass: modely CLUBS všech sezón (pro cross-ref) z aktuálního stavu na disku
    seasons = [season_of(f) for f in files]
    clubs_cache = {season_of(f): read_clubs(f) for f in files}

    tot = Counter()
    prev_clubs = None
    prev_removed = set()
    for i, path in enumerate(files):
        s = season_of(path)
        if args.only_season and s != args.only_season:
            prev_clubs = clubs_cache[s]
            prev_removed = set()
            continue
        wb = openpyxl.load_workbook(path)
        removed = phase0_remove_pseudo(wb, s)
        f, fl, cl, am = phase1_prev_links(wb, s, prev_clubs, prev_removed)
        next_clubs = clubs_cache[seasons[i + 1]] if i + 1 < len(files) else None
        kc, rs = phase2_fate(wb, s, next_clubs)
        fa = phase3_feeds(wb, s)
        wb.save(path)
        tot['pseudo'] += len(removed)
        tot['prev_fixed'] += f
        tot['prev_filled'] += fl
        tot['prev_cleared'] += cl
        tot['kval_fate'] += kc
        tot['fate_resolved'] += rs
        tot['feeds_added'] += fa
        prev_clubs = read_clubs(path)         # po úpravách (CLUBS aktuální)
        prev_removed = removed
        print(f"  ✓ {s}")

    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    with open('CHANGELOG_continuity.md', 'w', encoding='utf-8') as fh:
        fh.write(f"# Changelog – finalizace návazností\n\n_{stamp}_\n\n")
        fh.write("## Souhrn\n\n")
        for k, v in tot.items():
            fh.write(f"- **{k}**: {v}\n")
        fh.write("\n## Detail po sezónách\n\n```\n")
        fh.write('\n'.join(LOG))
        fh.write("\n```\n")
    with open('TODO_continuity.md', 'w', encoding='utf-8') as fh:
        fh.write(f"# TODO – položky k lidské verifikaci (D40)\n\n_{stamp}_\n\n")
        fh.write(f"Celkem: {len(TODO)}\n\n```\n")
        fh.write('\n'.join(TODO))
        fh.write("\n```\n")
    print("\n=== SOUHRN ===")
    for k, v in tot.items():
        print(f"  {k}: {v}")
    print(f"  TODO položek: {len(TODO)}")
    print("Viz CHANGELOG_continuity.md + TODO_continuity.md")


if __name__ == '__main__':
    main()
