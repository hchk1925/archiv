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
    # stávající kluby: norm name -> (club_id, club_name)
    existing = {}
    existing_hasstats = {}
    for r in rows[1:]:
        if r[H['row_type']] == 'T':
            k = norm(r[H['club_name']])
            existing[k] = (r[H['club_id']], r[H['club_name']])
            existing_hasstats[k] = any(r[H[c]] is not None
                                       for c in ['GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS'])

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
    m = re.match(r'.*?(S\d{4}_\d{2})', season_f) or re.search(r'(S\d{4}_\d{2})', rows[1][H['node_id']] or '')
    season_id = re.search(r'S\d{4}_\d{2}', str(rows[1][H['node_id']])).group(0)
    club_n = maxid(f'CLUB_{season_id}_')
    tr_n = maxid(f'TR_{season_id}_')

    # parse kolega
    tridy = parse_zupa(load_sheet(coll_f, coll_sheet))
    # kolega: full block label -> list teams
    coll_blocks = []   # (block_label, level, teams)
    for t in tridy:
        groups = ([('', t['_implicit'])] if t['_implicit']['teams'] else []) + \
                 [(g['label'], g) for g in t['groups'] if g['teams']]
        for glabel, g in groups:
            full = f"{t['label']} / {glabel}".strip() if glabel else t['label']
            coll_blocks.append((full, t['level'], g['teams']))

    # plán
    new_clubs = []
    add_cnt = keep_cnt = 0
    out_rows = [STD_HEADER]
    unmatched_blocks = []
    downgrades = []

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

    # projdi kolegovy bloky v jeho pořadí; namapuj na náš node
    comp_for_block = {}
    for full, level, teams in coll_blocks:
        bk = blockkey(full)
        if bk in bk_map:
            bn, nid, lvl = bk_map[bk]
        else:
            unmatched_blocks.append(full)
            continue
        out_rows.append(['H', bn, None, None, None, None, None, None, None, None,
                         None, None, None, None, nid, lvl, None, None, None, None,
                         None, None, None])
        for tm in teams:
            cid, isnew = club_for(tm['name'], tm['note'], lvl)
            if isnew: add_cnt += 1
            else: keep_cnt += 1
            tm_hasstats = any(tm[c] is not None
                              for c in ['GP', 'W', 'D', 'L', 'GF', 'GA', 'PTS'])
            if existing_hasstats.get(norm(tm['name'])) and not tm_hasstats:
                downgrades.append(tm['name'])
            tr_n += 1
            fate = tm['status'] if tm['status'] else None
            out_rows.append(['T', None, tm['rank'], tm['name'], tm['note'],
                             tm['GP'], tm['W'], tm['D'], tm['L'], tm['GF'], ':',
                             tm['GA'], tm['PTS'], bn, nid, lvl, cid, None, None,
                             None, fate, f"TR_{season_id}_{tr_n:05d}", None])

    print(f"== {kraj} ← {coll_sheet} ==")
    print(f"  bloků kolega: {len(coll_blocks)}, namapováno: {len(coll_blocks)-len(unmatched_blocks)}")
    if unmatched_blocks:
        print(f"  !! NENAMAPOVANÉ bloky (chybí uzel): {unmatched_blocks}")
    # pojistka: naše týmy, které v kolegově podkladu nejsou → ztratily by se
    coll_names = set()
    for full, level, teams in coll_blocks:
        for tm in teams:
            coll_names.add(norm(tm['name']))
    lost = [existing[k][1] for k in existing if k not in coll_names]

    print(f"  týmů celkem: {add_cnt+keep_cnt}  (zachováno {keep_cnt}, NOVÝCH {add_cnt})")
    print(f"  nové kluby: {[c[1] for c in new_clubs]}")
    if downgrades:
        print(f"  !! DOWNGRADE (kolega bez čísel, my máme): {downgrades}")
    if lost:
        print(f"  !! ZTRÁTA našich týmů (u kolegy nejsou): {lost}")

    if not do_write:
        print("\n(dry-run — přidej --write)")
        return
    if unmatched_blocks:
        print("\n!! Nepíšu — nejdřív domapovat bloky."); return
    if downgrades:
        print("\n!! Nepíšu — hrozí ztráta našich statistik. Vyřeš ručně."); return
    if lost:
        print("\n!! Nepíšu — naše týmy by zmizely. Vyřeš ručně."); return

    shutil.copy(season_f, season_f + '.bak')
    # přepiš list
    idx = wb.sheetnames.index(kraj)
    del wb[kraj]
    nws = wb.create_sheet(kraj, idx)
    for row in out_rows:
        nws.append(row)
    # CLUBS
    cws = wb['CLUBS']
    for cid, name, note, level in new_clubs:
        cws.append([cid, re.sub(r'\s*\((N|S|M)\)\s*$', '', name).strip(), name, kraj,
                    note, level, None, None,
                    'Doplněno z kolegova úplného podkladu (kraj rebuild).', None])
    wb.save(season_f)
    print(f"\n✓ {season_f} přepsán list {kraj}; +{add_cnt} klubů (záloha {season_f}.bak)")


if __name__ == '__main__':
    main()
