#!/usr/bin/env python3
"""
revert_phase_f_falsepositives.py — Vrátí Phase F city auto-přepisy
v případech, kdy původní change_note explicitně dokumentoval jiné city.

Pravidlo: pokud change_note obsahuje „city <X>" PŘED značkou
„|| TBD: city '<X>' → '<Y>' (odvozeno z názvu klubu)" a Y ≠ X,
je auto-přepis chybný (curátor X potvrdil dříve). Vrátit na X.
"""
import openpyxl, glob, os, re, sys
DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'

TBD_RE = re.compile(
    r"\|\|\s*TBD:\s*city\s*'([^']*)'\s*→\s*'([^']*)'\s*\(odvozeno z názvu klubu\)\s*\[polish_almanach\]")
CITY_DOC_RE = re.compile(r"\bcity\s+([A-ZÁ-Ž][\wÁ-ž\s\-]+?)(?=[\.\|]|$)", re.I)


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    reverted = kept = 0
    examples = []
    for path in files:
        wb = openpyxl.load_workbook(path)
        if 'CLUBS' not in wb.sheetnames:
            wb.close(); continue
        ws = wb['CLUBS']
        rows = list(ws.iter_rows())
        H = hidx([c.value for c in rows[0]])
        if 'city' not in H or 'change_note' not in H:
            wb.close(); continue
        cityi, cni, ni = H['city'], H['change_note'], H['clean_name']
        changed = False
        for row in rows[1:]:
            cn = row[cni].value
            if not cn or 'odvozeno z názvu klubu' not in str(cn):
                continue
            text = str(cn)
            m = TBD_RE.search(text)
            if not m:
                continue
            old_city, new_city = m.group(1), m.group(2)
            # text PŘED značkou
            before = text[:m.start()]
            # zachyceno-li „city <X>" před značkou
            doc_cities = [g.strip() for g in CITY_DOC_RE.findall(before)]
            doc_cities = [d for d in doc_cities if d.lower() not in
                          ('na', 'do', 'po', '')]
            if not doc_cities:
                kept += 1
                continue
            documented = doc_cities[-1]                # poslední zdokumentované
            if documented.lower() == new_city.lower():
                kept += 1
                continue
            # documented je 1+ slovo, podobné old_city (curátor potvrdil X);
            # vrátit city na X a odstranit TBD značku z change_note
            row[cityi].value = documented
            new_cn = (text[:m.start()].rstrip()
                      + (text[m.end():] if m.end() < len(text) else ''))
            new_cn = re.sub(r'\s*\|\|\s*$', '', new_cn).strip()
            row[cni].value = new_cn or None
            reverted += 1
            if len(examples) < 8:
                examples.append((row[H['club_id']].value,
                                 row[ni].value, old_city, new_city, documented))
            changed = True
        if changed:
            wb.save(path)
        wb.close()
    print(f"=== Phase F revert ===")
    print(f"  Vráceno (curátor měl city zdokumentované): {reverted}")
    print(f"  Ponecháno (žádná předchozí dokumentace): {kept}")
    print(f"\nUkázky vrácených:")
    for cid, nm, ocy, ncy, doc in examples:
        print(f"  {cid} '{nm}': {ncy} → vráceno na '{doc}' (Phase F měl '{ocy}'→'{ncy}')")


if __name__ == '__main__':
    main()
