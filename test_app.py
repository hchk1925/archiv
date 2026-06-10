#!/usr/bin/env python3
"""
test_app.py — smoke testy all-in-one nástroje (app.py).

Spusť:  python test_app.py
Ověří:  routy (viewer/audit/přehled), PDF plný + audit, write-back do xlsx
        (s automatickým obnovením), a export buildery (html/xlsx).
Nemění data natrvalo: po testu write-backu se sešit vrátí do původního stavu.
"""
import io
import os
import sys
import app

FAIL = []


def check(cond, msg):
    print(('  OK  ' if cond else ' FAIL ') + msg)
    if not cond:
        FAIL.append(msg)


def main():
    app.load_all()
    c = app.app.test_client()
    # vyber sezónu, která má torzo položky v TODO
    sid = next((s for s in app.SEASON_ORDER
                if app.CACHE[s] and app.CACHE[s]['todo']), None)
    check(sid is not None, 'nalezena sezóna s TODO položkami')
    print(f"\n— testovací sezóna: {sid} —\n")

    # 1. GET routy
    for path, must in [('/', 'Sezóny'),
                       (f'/s/{sid}', 'Pyramida'),
                       (f'/s/{sid}/audit', 'audit/save'),
                       ('/audit', 'otevřených'),
                       (f'/s/{sid}/edit/standings', 'Uložit')]:
        r = c.get(path)
        check(r.status_code == 200 and must in r.get_data(as_text=True),
              f'GET {path} → 200 & obsahuje „{must}"')

    # 2. inline komentář „co chybí" na sezónním pohledu
    sp = c.get(f'/s/{sid}').get_data(as_text=True)
    check('note-callout' in sp, 'sezónní pohled má inline callout „co chybí"')

    # 3. PDF plný + audit
    for url, magic in [(f'/s/{sid}/full.pdf', b'%PDF-'),
                       (f'/s/{sid}/audit.pdf', b'%PDF-')]:
        r = c.get(url)
        check(r.status_code == 200 and r.data[:5] == magic and len(r.data) > 1500,
              f'GET {url} → validní PDF ({len(r.data)} B)')

    # 4. write-back do xlsx (+ obnovení)
    path = os.path.join(app.DATA, f'S{sid}_FINAL.xlsx')
    backup = open(path, 'rb').read()
    try:
        t = app.CACHE[sid]['todo'][0]
        num = t['num']
        r = c.post(f'/s/{sid}/audit/save',
                   data={'num': str(num), 'done': 'ANO',
                         'varianta': 'doplnit týmy', 'poznamka': 'SMOKE-TEST'})
        check(r.status_code == 302, f'POST audit/save #{num} → 302 redirect')
        import openpyxl
        ws = openpyxl.load_workbook(path, read_only=True)['TODO']
        H = {cc.value: j for j, cc in enumerate(next(ws.iter_rows(max_row=1)), 0)}
        found = False
        for row in ws.iter_rows(min_row=2, values_only=True):
            if str(row[H['#']]) == str(num):
                found = (row[H['vyřešeno? (ANO/ne)']] == 'ANO'
                         and 'SMOKE-TEST' in str(row[H['poznámka kolegy']]))
                break
        check(found, 'write-back zapsal stav ANO + poznámku do TODO listu xlsx')
    finally:
        open(path, 'wb').write(backup)
        app.reload_season(sid)
    check(open(path, 'rb').read() == backup, 'sešit obnoven do původního stavu')

    # 5. export buildery
    pdf_full = app.build_full_pdf(app.CACHE[sid], sid)
    pdf_aud = app.build_season_pdf(app.CACHE[sid], sid)
    check(pdf_full[:5] == b'%PDF-' and len(pdf_full) > len(pdf_aud) // 2,
          'build_full_pdf → bytes PDF')
    check(pdf_aud[:5] == b'%PDF-', 'build_season_pdf → bytes PDF')

    print('\n' + ('VŠE OK' if not FAIL else f'SELHALO: {len(FAIL)} testů'))
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
