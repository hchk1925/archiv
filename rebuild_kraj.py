#!/usr/bin/env python3
"""
rebuild_kraj.py — přestaví jeden krajský list per-sezónního xlsx z kolegova
syrového .xls (úplná data se statistikami), přičemž ZACHOVÁ stávající club_id
(párování podle jména → nerozbije chainy) a node strukturu. Chybějící týmy
doplní jako nové kluby/řádky.

Použití:
    python3 rebuild_kraj.py <sezona.xlsx> <kraj_list> <kolega.xls> <kolega_list> [--write]
Bez --write jen ukáže plán (kolik se přidá/zachová).
"""
import sys, re, shutil
import xlrd, openpyxl
from build_1948_49_zupni import parse_zupa

STD_HEADER = ['row_type','block_name','pos','club_name','note','GP','W','D','L',
              'GF',':','GA','PTS','comp_path','node_id','level','club_id',
              'prev_club_id','dest_node_id','dest_type','season_fate','tr_id','district']


def norm(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    s = re.sub(r'\s*\((N|S|M)\)\s*$', '', s)
    return s.lower()


class XlsxSheet:
    """Adaptér openpyxl listu na rozhraní xlrd (nrows/ncols/cell_value)."""
    def __init__(self, ws):
        self._rows = list(ws.iter_rows(values_only=True))
        self.nrows = len(self._rows)
        self.ncols = max((len(r) for r in self._rows), default=0)

    def cell_value(self, r, c):
        row = self._rows[r]
        return row[c] if c < len(row) and row[c] is not None else ''


def load_sheet(path, sheet):
    if path.lower().endswith('.xlsx'):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        return XlsxSheet(wb[sheet])
    return xlrd.open_workbook(path).sheet_by_name(sheet)


def blockkey(label):
    return re.sub(r'\s+', ' ', str(label)).strip().lower()


def main():
    if len(sys.argv) < 5:
        print(__doc__); sys.exit(1)
    season_f, kraj, coll_f, coll_sheet = sys.argv[1:5]
    do_write = '--write' in sys.argv

    wb = openpyxl.load_workbook(season_f)
    ws = wb[kraj]
    rows = list(ws.iter_rows(values_only=True))
    H = {str(v): i for i, v in enumerate(rows[0])}

    # stávající bloky v pořadí: blockkey -> (block_name, node_id, level)
    blocks = []           # zachované pořadí
    bk_map = {}
    sid_pref = None
    for r in rows[1:]:
        if r[H['row_type']] == 'H':
            bn = r[H['block_name']]; nid = r[H['node_id']]; lvl = r[H['level']]
            bk_map[blockkey(bn)] = (bn, nid, lvl)
            blocks.append(blockkey(bn))
    # stávající kluby: norm name -> (club_id, club_name) + plné statistiky pro merge
    existing = {}
    existing_full = {}
    for r in rows[1:]:
        if r[H['row_type']] == 'T':
            k = norm(r[H['club_name']])
            existing[k] = (r[H['club_id']], r[H['club_name']])
            existing_full[k] = {c: r[H[c]] for c in
                                ['pos', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS', 'note', 'season_fate']}

    def has_stats_dict(d, keys=('GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS')):
        return any(d.get(c) is not None for c in keys)

    # max ids v sezoně
    def maxid(prefix):
        mx = 0
        for sn in wb.sheetnames:
            for row in wb[sn].iter_rows(values_only=True):
                for v in row:
                    if isinstance(v, str):
                        for g in re.findall(prefix + r'(\d+)', v):
                            mx = max(mx, int(g))
        return mx
    season_id = re.search(r'S\d{4}_\d{2}', str(rows[1][H['node_id']])).group(0)
    club_n = maxid(f'CLUB_{season_id}_')
    tr_n = maxid(f'TR_{season_id}_')
    node_n = maxid(f'NODE_{season_id}_')

    # ── SYSTEM: mapy uzlů ──
    sys_ws = wb['SYSTEM']
    SH = {str(v): i for i, v in enumerate(next(sys_ws.iter_rows(values_only=True)))}
    sys_info = {}     # node_id -> (name, level, region)
    for r in list(sys_ws.iter_rows(values_only=True))[1:]:
        if r[SH['node_id']]:
            sys_info[r[SH['node_id']]] = (r[SH['name']], r[SH['level']], r[SH['region']])
    # region tohoto kraje + úrovňové kontejnery "{prefix} L30/L40/L50"
    region = None
    for bk, (bn, nid, lvl) in bk_map.items():
        if nid in sys_info and sys_info[nid][2]:
            region = sys_info[nid][2]; break
    container_by_level = {}   # level -> node_id
    prefix = None
    for nid, (nm, lvl, reg) in sys_info.items():
        mm = re.match(r'(.+) L(30|40|50)$', str(nm or ''))
        if mm and reg == region:
            container_by_level[f'L{mm.group(2)}'] = nid
            prefix = mm.group(1)
    if prefix is None:
        prefix = kraj

    new_sys = []     # (node_id, name, type, level, parent)

    def mint_node(name, ctype, level, parent):
        nonlocal node_n
        node_n += 1
        nid = f"NODE_{season_id}_{node_n:04d}"
        new_sys.append((nid, name, ctype, level, parent))
        sys_info[nid] = (name, level, region)
        return nid

    def resolve_container(tlabel, level):
        bk = blockkey(tlabel)
        if bk in bk_map:
            _, nid, lvl = bk_map[bk]
            return nid, lvl
        if level in container_by_level:
            return container_by_level[level], level
        nid = mint_node(f"{prefix} {tlabel}", 'league', level, None)
        container_by_level[level] = nid
        return nid, level

    def resolve_group(full, container_nid, level):
        bk = blockkey(full)
        if bk in bk_map:
            _, nid, lvl = bk_map[bk]
            return nid, lvl
        return mint_node(full, 'group', level, container_nid), level

    tridy = parse_zupa(load_sheet(coll_f, coll_sheet))
    new_clubs = []
    add_cnt = keep_cnt = 0
    out_rows = [STD_HEADER]
    merged = []

    def club_for(name, note, level):
        nonlocal club_n
        k = norm(name)
        if k in existing:
            return existing[k][0], False
        club_n += 1
        cid = f"CLUB_{season_id}_{club_n:04d}"
        new_clubs.append((cid, name, note, level))
        existing[k] = (cid, name)
        return cid, True

    def emit_H(label, nid, lvl):
        out_rows.append(['H', label, None, None, None, None, None, None, None,
                         None, None, None, None, None, nid, lvl, None, None, None,
                         None, None, None, None])

    def emit_team(tm, label, nid, lvl):
        nonlocal add_cnt, keep_cnt, tr_n
        cid, isnew = club_for(tm['name'], tm['note'], lvl)
        if isnew: add_cnt += 1
        else: keep_cnt += 1
        ex = existing_full.get(norm(tm['name']), {})
        tm_has = any(tm[c] is not None for c in ['GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS'])
        # MERGE: kolega bez čísel a my máme → ponech naše statistiky
        if not tm_has and has_stats_dict(ex):
            pos = tm['rank'] if tm['rank'] is not None else ex.get('pos')
            GP, W, D, L = ex['GP'], ex['W'], ex['D'], ex['L']
            GF, GA, PTS = ex['GF'], ex['GA'], ex['PTS']
            merged.append(tm['name'])
        else:
            pos = tm['rank']
            GP, W, D, L = tm['GP'], tm['W'], tm['D'], tm['L']
            GF, GA, PTS = tm['GF'], tm['GA'], tm['PTS']
        tr_n += 1
        fate = tm['status'] if tm['status'] else None
        out_rows.append(['T', None, pos, tm['name'], tm['note'], GP, W, D, L, GF,
                         ':', GA, PTS, label, nid, lvl, cid, None, None, None,
                         fate, f"TR_{season_id}_{tr_n:05d}", None])

    # projdi kolegovy třídy v pořadí
    for t in tridy:
        cont_nid, cont_lvl = resolve_container(t['label'], t['level'])
        has_direct = bool(t['_implicit']['teams'])
        named = [g for g in t['groups'] if g['teams']]
        if has_direct:
            emit_H(t['label'], cont_nid, t['level'])
            for tm in t['_implicit']['teams']:
                emit_team(tm, t['label'], cont_nid, t['level'])
        if named:
            if not has_direct:
                emit_H(t['label'], cont_nid, t['level'])   # holý kontejner
            for g in named:
                full = f"{t['label']} / {g['label']}"
                gnid, glvl = resolve_group(full, cont_nid, t['level'])
                emit_H(full, gnid, t['level'])
                for tm in g['teams']:
                    emit_team(tm, full, gnid, t['level'])

    # pojistka: naše týmy, které v kolegově podkladu nejsou → ztratily by se
    coll_names = set()
    for t in tridy:
        for g in [t['_implicit']] + t['groups']:
            for tm in g['teams']:
                coll_names.add(norm(tm['name']))
    lost = [existing[k][1] for k in existing if k not in coll_names]

    print(f"== {kraj} ← {coll_sheet} ==")
    print(f"  týmů celkem: {add_cnt+keep_cnt}  (zachováno {keep_cnt}, NOVÝCH {add_cnt})")
    print(f"  nové kluby: {[c[1] for c in new_clubs]}")
    if new_sys:
        print(f"  nové uzly: {[(s[1], s[3]) for s in new_sys]}")
    if merged:
        print(f"  merge (kolega bez čísel → naše čísla zachována): {merged}")
    if lost:
        print(f"  !! ZTRÁTA našich týmů (u kolegy nejsou): {lost}")

    if not do_write:
        print("\n(dry-run — přidej --write)")
        return
    if lost:
        print("\n!! Nepíšu — naše týmy by zmizely. Vyřeš ručně."); return

    shutil.copy(season_f, season_f + '.bak')
    # přepiš list
    idx = wb.sheetnames.index(kraj)
    del wb[kraj]
    nws = wb.create_sheet(kraj, idx)
    for row in out_rows:
        nws.append(row)
    # SYSTEM: nové uzly
    for nid, name, ctype, level, parent in new_sys:
        sys_ws.append([nid, name, ctype, level, region, parent, None, None,
                       '2-1-0', None, 'Doplněno (kraj rebuild z kolegova podkladu).',
                       None, None, None])
    # CLUBS
    cws = wb['CLUBS']
    for cid, name, note, level in new_clubs:
        cws.append([cid, re.sub(r'\s*\((N|S|M)\)\s*$', '', name).strip(), name, kraj,
                    note, level, None, None,
                    'Doplněno z kolegova úplného podkladu (kraj rebuild).', None])
    wb.save(season_f)
    print(f"\n✓ {season_f} přepsán list {kraj}; +{add_cnt} klubů, +{len(new_sys)} uzlů "
          f"(záloha {season_f}.bak)")


if __name__ == '__main__':
    main()
