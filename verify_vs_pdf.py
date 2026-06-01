#!/usr/bin/env python3
"""
verify_vs_pdf.py — křížová kontrola nejvyšší soutěže (10_liga) proti originálním
PDF (sources/CZE1/CZ-YYYY-YY.pdf). Pořadí pravdy: PDF > xlsx.

Join přes (GP, GF, GA) — nezávislý na jménech (PDF layout je rozházený).
Hlásí:
  A) xlsx řádek bez shody v PDF (možná chyba GF/GA nebo řádek mimo nejvyšší PDF)
  B) shoda na skóre, ale liší se V/R/P (jen éra <2000, kde platí 2-1-0)

Report-only (default). S --write opraví V/R/P u jednoznačných shod typu B
(stejné GP+GF+GA, V+R+P=GP po opravě).
"""
import openpyxl, glob, os, re, sys
from pdfminer.high_level import extract_text

PDF_DIR = 'sources/CZE1'
WRITE = '--write' in sys.argv
ROW_FLEX = re.compile(r'(?<!\d)(\d{1,2})\s+((?:\d{1,3}\s+){2,6}?)(\d{1,3}):(\d{1,3})(?!\d)')


def derive_wdl(outs):
    n = len(outs)
    if n == 3:                      # V R P
        return outs[0], outs[1], outs[2]
    if n == 4:                      # V VP PP P (bez remíz)
        return outs[0] + outs[1], 0, outs[2] + outs[3]
    if n == 5:                      # V VP R PP P
        return outs[0] + outs[1], outs[2], outs[3] + outs[4]
    if n == 6:                      # V VP VN PN PP P (nájezdová éra, bez remíz)
        return outs[0] + outs[1] + outs[2], 0, outs[3] + outs[4] + outs[5]
    return None


def parse_pdf(sid):
    yr = sid[1:].replace('_', '-')
    path = os.path.join(PDF_DIR, f'CZ-{yr}.pdf')
    if not os.path.exists(path):
        return None
    txt = extract_text(path)
    rows = []
    for line in txt.splitlines():
        m = ROW_FLEX.search(line)          # max 1 tabulkový řádek na řádek textu
        if not m:
            continue
        outs = [int(x) for x in m.group(2).split()]
        wdl = derive_wdl(outs)
        rows.append({'gp': int(m.group(1)), 'outs': outs, 'wdl': wdl,
                     'gf': int(m.group(3)), 'ga': int(m.group(4)), 'used': False})
    return rows


def hcol(ws, name):
    for j, c in enumerate(next(ws.iter_rows(max_row=1)), 1):
        if c.value == name:
            return j
    return None


def main():
    files = sorted(glob.glob('data/S*_FINAL.xlsx'))
    tot_nomatch = tot_wdl = tot_fixed = 0
    report = []
    for path in files:
        sid = re.search(r'S\d{4}_\d{2}', os.path.basename(path)).group(0)
        pdf = parse_pdf(sid)
        if pdf is None:
            continue
        yr = int(sid[1:5])
        wb = openpyxl.load_workbook(path)
        ws = wb['10_liga']
        cRT, cGP = hcol(ws, 'row_type'), hcol(ws, 'GP')
        cW, cD, cL = hcol(ws, 'W'), hcol(ws, 'D'), hcol(ws, 'L')
        cGF, cGA, cPTS = hcol(ws, 'GF'), hcol(ws, 'GA'), hcol(ws, 'PTS')
        # bloky s možným přenosem bodů (o udržení/umístění/prolínací/baráž/nadstavba)
        carry_re = re.compile(r'udržen|umíst|prolín|baráž|nadstavb|playoff|play-off', re.I)
        nomatch, wdldiff, gafix, fixed = [], [], [], 0
        unmatched = []
        blk = ''
        for row in ws.iter_rows():
            if row[cRT - 1].value == 'H' and row[1].value:
                blk = str(row[1].value)
            if row[cRT - 1].value != 'T':
                continue
            gp, gf, ga = row[cGP-1].value, row[cGF-1].value, row[cGA-1].value
            nm = row[3].value
            if not all(isinstance(x, int) for x in (gp, gf, ga)):
                continue
            cand = next((r for r in pdf if not r['used'] and r['gp'] == gp
                         and r['gf'] == gf and r['ga'] == ga), None)
            if cand is None:
                nomatch.append((nm, gp, gf, ga))
                unmatched.append((row, nm, gp))
                continue
            cand['used'] = True
            if yr < 2000 and cand['wdl'] is not None:
                w, d, l = cand['wdl']
                xw, xd, xl = row[cW-1].value, row[cD-1].value, row[cL-1].value
                if (xw, xd, xl) != (w, d, l):
                    wdldiff.append((nm, (xw, xd, xl), (w, d, l)))
                    if WRITE and w + d + l == gp:
                        row[cW-1].value, row[cD-1].value, row[cL-1].value = w, d, l
                        row[cPTS-1].value = 2 * w + d   # 2-1-0: PTS odvozené z V/R
                        fixed += 1
                # PTS=2·V+R v ne-přenosových blocích (ZČ/finále)
                cw, cd = row[cW-1].value, row[cD-1].value
                if (isinstance(cw, int) and isinstance(cd, int)
                        and not carry_re.search(blk)
                        and row[cPTS-1].value != 2 * cw + cd):
                    wdldiff.append((nm + ' [PTS]', row[cPTS-1].value, 2 * cw + cd))
                    if WRITE:
                        row[cPTS-1].value = 2 * cw + cd
                        fixed += 1
        # PASS 2 (<2000): no-match řádky napáruj přes ověřené V/R/P a převezmi
        # GF:GA z PDF (drobné překlepy ve skóre; PDF = pravda nad xlsx).
        still_nomatch = []
        for row, nm, gp in unmatched:
            done = False
            if yr < 2000:
                wdl = (row[cW-1].value, row[cD-1].value, row[cL-1].value)
                cands = [r for r in pdf if not r['used'] and r['gp'] == gp
                         and r['wdl'] == wdl]
                if len(cands) == 1:
                    p = cands[0]; p['used'] = True
                    oldgf, oldga = row[cGF-1].value, row[cGA-1].value
                    gafix.append((nm, f"{oldgf}:{oldga}", f"{p['gf']}:{p['ga']}"))
                    if WRITE:
                        row[cGF-1].value, row[cGA-1].value = p['gf'], p['ga']
                        fixed += 1
                    done = True
            if not done:
                still_nomatch.append((nm, gp, row[cGF-1].value, row[cGA-1].value))
        nomatch = still_nomatch
        if WRITE and fixed:
            wb.save(path)
        wb.close()
        tot_nomatch += len(nomatch); tot_wdl += len(wdldiff) + len(gafix); tot_fixed += fixed
        if nomatch or wdldiff or gafix:
            report.append((sid, nomatch, wdldiff, gafix, fixed))

    for sid, nomatch, wdldiff, gafix, fixed in report:
        print(f"\n=== {sid[1:]} ===")
        for nm, gp, gf, ga in nomatch:
            print(f"   ✗ bez shody v PDF (k ověření): '{nm}' GP{gp} {gf}:{ga}")
        for nm, old, new in wdldiff:
            print(f"   ~ V/R/P '{nm}': xlsx{old} -> PDF{new} {'✔' if WRITE else ''}")
        for nm, old, new in gafix:
            print(f"   ~ GF:GA '{nm}': xlsx {old} -> PDF {new} {'✔' if WRITE else ''}")
    print(f"\n=== SOUHRN === bez shody: {tot_nomatch} | opraveno V/R/P+PTS+GF/GA: "
          f"{tot_wdl} | zapsáno: {tot_fixed}  (WRITE={WRITE})")


if __name__ == '__main__':
    main()
