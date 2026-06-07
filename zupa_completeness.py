#!/usr/bin/env python3
"""
zupa_completeness.py — pro župní éru (1947/48, 1948/49) založí SHEET NA KAŽDOU
ŽUPU (40{KÓD}) a doplní kluby z kolegova indexu 'clbs' jako základ úplnosti
(jen názvy + pořadí + příznak, BEZ statistik). Župní I.třída = level L40
(pod divizí). Nemíchá se do krajových/divizních sheetů.

    python3 zupa_completeness.py <sezona.xlsx> <kolega.xlsx> [--write]
"""
import sys, re, shutil
import openpyxl

# (klíčové slovo v názvu župy) -> kód sheetu (sheet = 'Z'+kód). Kódy + regiony
# přesně dle zavedené konvence ze sezony 1948/49 (sheety ZSTRC, ZKLAD, …).
ZUPA_CODE = [
    ('středočesk', 'STRC'), ('středolabsk', 'SLAB'), ('kladensk', 'KLAD'),
    ('podbrdsk', 'PODB'), ('západočesk', 'ZAPC'), ('šumavsk', 'SUMA'),
    ('krušnohorsk', 'KRUS'), ('severočesk', 'SEVC'), ('východočesk', 'VYCH'),
    ('orlick', 'ORLI'), ('západomoravsk', 'ZAPM'), ('horáck', 'HORA'),
    ('hanáck', 'HANA'), ('slováck', 'SLOV'), ('slezsk', 'SLEZ'),
]
REGION = {
    'STRC': 'REG_STC', 'SLAB': 'REG_STC', 'KLAD': 'REG_STC', 'PODB': 'REG_STC',
    'SUMA': 'REG_JHC', 'KRUS': 'REG_SVC', 'SEVC': 'REG_SVC', 'ZAPC': 'REG_ZPC',
    'VYCH': 'REG_VYC', 'ORLI': 'REG_VYC', 'HORA': 'REG_VYS', 'ZAPM': 'REG_SVM',
    'SLOV': 'REG_SVM', 'HANA': 'REG_SVM', 'SLEZ': 'REG_SVM',
}
SKIP = ('liga', 'divize', 'svk', 'slovens')
STD_HEADER = ['row_type','block_name','pos','club_name','note','GP','W','D','L',
              'GF',':','GA','PTS','comp_path','node_id','level','club_id',
              'prev_club_id','dest_node_id','dest_type','season_fate','tr_id','district']
LEVEL = 'L30'

def zupa_code(lst):
    s = str(lst or '').lower()
    if any(k in s for k in SKIP):
        return None
    for kw, code in ZUPA_CODE:
        if kw in s:
            return code
    return None

def norm(s):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    s = re.sub(r'\s*[\(\[](N|S|M)[\)\]]\s*$', '', s)
    return s.lower()

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    season_f, coll_f = sys.argv[1], sys.argv[2]
    do_write = '--write' in sys.argv

    cwb = openpyxl.load_workbook(coll_f, read_only=True, data_only=True)
    crows = list(cwb['clbs'].iter_rows(values_only=True))
    ch = {str(v): i for i, v in enumerate(crows[0])}
    def cc(r, name): return r[ch[name]] if name in ch else None
    cwb.close()

    wb = openpyxl.load_workbook(season_f)
    season_id = re.search(r'S(\d{4}_\d{2})', season_f).group(0)

    have = set()
    for sn in wb.sheetnames:
        rows = list(wb[sn].iter_rows(values_only=True))
        if not rows: continue
        h = {str(v): i for i, v in enumerate(rows[0])}
        if 'club_name' not in h: continue
        for r in rows[1:]:
            if r and r[h.get('row_type', 0)] == 'T' and r[h['club_name']]:
                have.add(norm(r[h['club_name']]))

    def maxid(prefix):
        mx = 0
        for sn in wb.sheetnames:
            for row in wb[sn].iter_rows(values_only=True):
                for v in row:
                    if isinstance(v, str):
                        for g in re.findall(prefix + r'(\d+)', v):
                            mx = max(mx, int(g))
        return mx
    club_n = maxid(f'CLUB_{season_id}_'); tr_n = maxid(f'TR_{season_id}_')
    node_n = maxid(f'NODE_{season_id}_')

    from collections import OrderedDict
    groups = OrderedDict()
    for r in crows[1:]:
        lst = str(cc(r, 'List (oblast)') or '').strip()
        if zupa_code(lst) is None:
            continue
        sou = str(cc(r, 'Soutěž') or '').strip()
        sk = cc(r, 'Skupina/část'); sk = str(sk).strip() if sk is not None else ''
        groups.setdefault((lst, sou, sk), []).append(r)

    new_clubs = []; new_sys = []; sheet_adds = OrderedDict(); report = []
    def mint(name, region):
        nonlocal node_n
        node_n += 1; nid = f"NODE_{season_id}_{node_n:04d}"
        new_sys.append((nid, name, region)); return nid

    for (lst, sou, sk), rws in groups.items():
        code = zupa_code(lst); sheet = f"Z{code}"
        todo = [r for r in rws if norm(cc(r, 'Klub')) not in have]
        if not todo: continue
        label = f"{lst} župa {sou}".strip() + (f" / {sk}" if sk else "")
        node = mint(label, REGION.get(code))
        out = sheet_adds.setdefault(sheet, [])
        out.append(['H', label, None, None, None, None, None, None, None, None,
                    None, None, None, None, node, LEVEL, None, None, None, None,
                    None, None, None])
        for r in todo:
            nm = str(cc(r, 'Klub')).strip()
            pori = cc(r, 'Pořadí')
            flag = cc(r, 'Příznak []') or cc(r, 'Anotace ()')
            note = flag if str(flag) in ('N', 'S', 'M') else None
            club_n += 1; cid = f"CLUB_{season_id}_{club_n:04d}"
            new_clubs.append((cid, nm, note, sheet))
            tr_n += 1
            out.append(['T', None, pori, nm, note, None, None, None, None, None,
                        ':', None, None, label, node, LEVEL, cid, None, None, None,
                        None, f"TR_{season_id}_{tr_n:05d}", None])
            have.add(norm(nm))
        report.append((sheet, label, len(todo)))

    print(f"== {season_id}: župní úplnost z clbs (sheet na župu, jen názvy) ==")
    for sheet, label, n in report:
        print(f"  {sheet:8s} {label}: {n}")
    total = sum(n for _, _, n in report)
    print(f"  CELKEM +{total} klubů, +{len(new_sys)} uzlů, "
          f"{len(sheet_adds)} žup-sheetů")
    if not do_write:
        print("\n(dry-run — přidej --write)"); return

    shutil.copy(season_f, season_f + '.bak')
    for sheet, out in sheet_adds.items():
        if sheet not in wb.sheetnames:
            ws = wb.create_sheet(title=sheet); ws.append(STD_HEADER)
        else:
            ws = wb[sheet]
        for row in out:
            ws.append(row)
    sys_ws = wb['SYSTEM']
    syshdr = [str(c.value) for c in next(sys_ws.iter_rows())]
    si = {n: i for i, n in enumerate(syshdr)}
    for nid, name, region in new_sys:
        rowv = [None] * len(syshdr)
        rowv[si['node_id']] = nid; rowv[si['name']] = name
        rowv[si['competition_type']] = 'league'; rowv[si['level']] = LEVEL
        rowv[si['region']] = region
        rowv[si['note']] = 'Župní soutěž – základ úplnosti z clbs (jen názvy).'
        sys_ws.append(rowv)
    cws = wb['CLUBS']
    chdr = [str(c.value) for c in next(cws.iter_rows())]
    desc = 'Župní soutěž – základ úplnosti z clbs (jen názvy, bez statistik).'
    for cid, name, note, sheet in new_clubs:
        clean = re.sub(r'\s*[\(\[](N|S|M)[\)\]]\s*$', '', name).strip()
        vals = {'club_id': cid, 'raw_name': name, 'clean_name': clean,
                'sheet': sheet, 'entry_note': note, 'level': LEVEL,
                'district': None, 'prev_club_id': None, 'change_note': desc, 'city': None}
        cws.append([vals.get(col) for col in chdr])
    wb.save(season_f)
    print(f"\n✓ {season_f}: +{total} klubů, +{len(new_sys)} uzlů, "
          f"{len(sheet_adds)} žup-sheetů (záloha {season_f}.bak)")

if __name__ == '__main__':
    main()
