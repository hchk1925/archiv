#!/usr/bin/env python3
"""
add_prev_node_id.py — Doplnit sloupec prev_node_id do listu SYSTEM
ve všech 65 sezónách.

Pro každý competition node v sezóně N najde stejnou soutěž v N-1
podle (name normalizováno, level). Tím vznikne řetěz „I.liga 1949/50
→ 1950/51 → 1951/52 → … → Extraliga 2013/14" — návaznost soutěží
napříč sezónami (Wikipedia-style navigace).

Idempotentní: pokud sloupec už existuje, jen přepíše hodnoty.
"""
import openpyxl, glob, os, re, sys
from collections import defaultdict

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
NEW_COL = 'prev_node_id'


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def norm_name(s):
    if not s:
        return ''
    s = str(s).strip().lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\.', '', s)
    # sjednotit některé varianty zápisu (nepřepisuje obsah, jen pro match)
    s = s.replace('iliga', 'i.liga').replace('iiliga', 'ii.liga')
    return s


def season_of(p):
    m = re.search(r'S(\d{4})_(\d{2})', os.path.basename(p))
    return f"S{m.group(1)}_{m.group(2)}"


def load_system_index(path):
    """Vrať mapu (norm_name, level) → node_id pro danou sezónu."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['SYSTEM']
    rows = list(ws.iter_rows(values_only=True))
    H = hidx(rows[0])
    out = defaultdict(list)
    for r in rows[1:]:
        if not r or r[H['node_id']] is None:
            continue
        key = (norm_name(r[H['name']]), str(r[H['level']] or ''))
        out[key].append(r[H['node_id']])
    wb.close()
    return out


def ensure_column(ws, col_name):
    """Zajistí, že list má sloupec col_name. Vrátí jeho 0-based index."""
    headers = [c.value for c in next(ws.iter_rows(max_row=1))]
    if col_name in headers:
        return headers.index(col_name)
    new_idx = len(headers)
    ws.cell(row=1, column=new_idx + 1, value=col_name)
    return new_idx


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    seasons = [season_of(p) for p in files]
    s_by = dict(zip(seasons, files))
    # prev-season SYSTEM indices
    prev_idx = {seasons[0]: None}
    for i in range(1, len(seasons)):
        prev_idx[seasons[i]] = load_system_index(s_by[seasons[i - 1]])

    tot_linked = tot_ambig = tot_no = 0
    for path in files:
        sid = season_of(path)
        wb = openpyxl.load_workbook(path)
        if 'SYSTEM' not in wb.sheetnames:
            wb.close()
            continue
        ws = wb['SYSTEM']
        col = ensure_column(ws, NEW_COL)
        # přečti H znovu (po ensure_column)
        H = hidx([c.value for c in next(ws.iter_rows(max_row=1))])
        ni, nmi, lvi = H['node_id'], H['name'], H['level']
        pidx = prev_idx[sid]
        if pidx is None:
            wb.save(path); wb.close()
            continue
        linked = ambig = no = 0
        for row in list(ws.iter_rows())[1:]:
            if row[ni].value is None:
                continue
            key = (norm_name(row[nmi].value), str(row[lvi].value or ''))
            cands = pidx.get(key, [])
            if len(cands) == 1:
                row[col].value = cands[0]
                linked += 1
            elif len(cands) > 1:
                ambig += 1
                row[col].value = None             # nech prázdné, kolega rozhodne
            else:
                no += 1
                row[col].value = None
        wb.save(path)
        wb.close()
        tot_linked += linked; tot_ambig += ambig; tot_no += no
        if linked or ambig or no:
            print(f"  ✓ {sid}: linked={linked} ambig={ambig} new={no}")
    print(f"\n=== SOUHRN ===")
    print(f"  prev_node_id linků doplněno: {tot_linked}")
    print(f"  ambiguózních (víc kandidátů): {tot_ambig}")
    print(f"  nových soutěží (bez předchůdce): {tot_no}")


if __name__ == '__main__':
    main()
