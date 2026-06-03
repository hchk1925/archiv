#!/usr/bin/env python3
"""pdf_worklist.py — z reportu verify_vs_pdf udělá worklist 'k ověření' do
docs/PDF_VERIFY_WORKLIST.md (oblastní/KVAL/národní patra, neúplné rozpisy)."""
import re, datetime, subprocess, sys

rep = subprocess.run([sys.executable, 'verify_vs_pdf.py'],
                     capture_output=True, text=True).stdout.splitlines()
out = ['# PDF-diff worklist — řádky „k ověření"\n',
       f'_{datetime.datetime.now():%Y-%m-%d %H:%M} · z verify_vs_pdf.py_\n',
       'Řádky bez jednoznačné shody v DS PDF — typicky neúplný rozpis (tým odehrál '
       'méně zápasů než v PDF) nebo PDF řádek nemá. Nutno rozhodnout ručně. '
       'NEopravováno automaticky.\n']
cur = None
buf = []
sections = []
for l in rep:
    m = re.match(r'^=== (\d{4}_\d{2}) ===', l)
    if m:
        if cur and buf:
            sections.append((cur, buf))
        cur = m.group(1); buf = []
    elif 'k ověření' in l:
        mm = re.search(r'k ověření \[([^\]]+)\]: .([^\']+). GP(\d+) (\d+):(\d+)', l)
        if mm:
            buf.append(f'  - `{mm.group(1)}` {mm.group(2)} — GP{mm.group(3)} '
                       f'{mm.group(4)}:{mm.group(5)}')
if cur and buf:
    sections.append((cur, buf))
tot = sum(len(b) for _, b in sections)
out.insert(3, f'\n**Celkem k ověření: {tot}** (napříč {len(sections)} sezónami)\n')
for sid, b in sections:
    out.append(f'\n## {sid}  ({len(b)})\n')
    out.extend(b)
open('docs/PDF_VERIFY_WORKLIST.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(f'docs/PDF_VERIFY_WORKLIST.md — {tot} řádků, {len(sections)} sezón')
