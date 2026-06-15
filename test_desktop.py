#!/usr/bin/env python3
"""
test_desktop.py — headless smoke test desktopové appky (Tkinter).

Spusť pod virtuálním displejem:
    xvfb-run -a python3 test_desktop.py
Ověří: čisté helpery, sestavení okna, naplnění stromu, zobrazení tabulky +
komentáře u torza a zápis řešení do xlsx (s automatickým obnovením sešitu).
"""
import os
import sys

FAIL = []


def check(cond, msg):
    print(('  OK  ' if cond else ' FAIL ') + msg)
    if not cond:
        FAIL.append(msg)


def main():
    import desktop
    import app as core
    # v headless nesmí naskočit modální dialog (čekal by na klik)
    desktop.messagebox.showinfo = lambda *a, **k: None
    desktop.messagebox.showerror = lambda *a, **k: None
    desktop.messagebox.showwarning = lambda *a, **k: None

    # 1) čisté helpery bez GUI
    sid = next(s for s in core.list_season_ids()
               if core.load_season(s)['todo'])
    d = core.load_season(sid)
    check(isinstance(desktop.resolved_set(d), set), 'resolved_set vrací set')
    nt = desktop.node_todo_map(d)
    check(all(k.startswith('NODE_') for k in nt), 'node_todo_map klíčuje podle NODE_')

    # 2) sestavení okna
    win = desktop.AlmanachDesktop()
    win.update()
    check(len(win.item_map) > 0, 'strom naplněn položkami')

    # 3) vyber sezónu s torzem a najdi uzel s mezerou
    torzo_sid = next(s for s in core.list_season_ids()
                     if core.audit_notes_by_node(core.load_season(s)))
    win.season_var.set(torzo_sid)
    win.load_sid(torzo_sid)
    win.update()
    gap_node = next(iter(core.audit_notes_by_node(win.d)))
    win.show_node(gap_node)
    win.update()
    check(len(win.table.get_children()) > 0, 'tabulka týmů se zobrazila')
    txt = win.comment.get('1.0', 'end').strip()
    check('⚑' in txt or 'chybí' in txt or 'máme jen' in txt,
          'komentář „co chybí" se zobrazil u torza')
    check(win.cur_num is not None, 'u torza je předvyplněný formulář řešení')

    # 4) zápis řešení do xlsx + obnovení
    path = os.path.join(core.DATA, f'S{torzo_sid}_FINAL.xlsx')
    backup = open(path, 'rb').read()
    try:
        win.stav.set('ANO')
        win.varianta.set('doplnit týmy')
        win.pozn.delete(0, 'end')
        win.pozn.insert(0, 'DESKTOP-TEST')
        num = win.cur_num
        win.save()
        import openpyxl
        ws = openpyxl.load_workbook(path, read_only=True)['TODO']
        H = {c.value: j for j, c in enumerate(next(ws.iter_rows(max_row=1)), 0)}
        ok = False
        for row in ws.iter_rows(min_row=2, values_only=True):
            if str(row[H['#']]) == str(num):
                ok = (row[H['vyřešeno? (ANO/ne)']] == 'ANO'
                      and 'DESKTOP-TEST' in str(row[H['poznámka kolegy']]))
                break
        check(ok, 'Uložit do xlsx zapsalo stav + poznámku')
    finally:
        open(path, 'wb').write(backup)
    check(open(path, 'rb').read() == backup, 'sešit obnoven do původního stavu')

    # 5) PDF export builder (bez dialogu)
    pdf = core.build_full_pdf(win.d, torzo_sid)
    check(pdf[:5] == b'%PDF-', 'build_full_pdf z desktopu → PDF')

    # 6) ORG CHART — sestavení, re-parent, zápis do SYSTEM listu
    osid = next(s for s in core.list_season_ids()
                if any(n['parent_node_id'] for n in core.load_season(s)['system']))
    od = core.load_season(osid)
    oc = desktop.OrgChart(win, osid, od)
    oc.update()
    check(len(oc.item_node) > 0, 'org chart: boxy vykresleny')
    check(len(oc.bands) > 0, 'org chart: patra (úrovně) sestavena')
    # vyber uzel s rodičem a přepni ho pod jiný kořenový uzel
    child = next(n['node_id'] for n in od['system']
                 if n['parent_node_id'] in oc.nodes)
    newpar = next(n['node_id'] for n in od['system']
                  if not n['parent_node_id'] and n['node_id'] != oc.model[child]['parent']
                  and child not in oc._descendants(n['node_id']))
    oc.apply_change(child, newpar, oc.model[newpar]['level'])
    check(oc.model[child]['parent'] == newpar, 'org chart: re-parent v modelu')
    check(child in oc._changes(), 'org chart: změna zaevidována')
    # cyklus se nesmí povolit
    kid = next((k for k in oc._descendants(newpar)), None)
    if kid:
        oc.apply_change(newpar, kid, oc.model[newpar]['level'])
        check(oc.model[newpar]['parent'] != kid, 'org chart: cyklus zakázán')
    # zápis do xlsx + obnovení
    opath = os.path.join(core.DATA, f'S{osid}_FINAL.xlsx')
    obackup = open(opath, 'rb').read()
    try:
        oc.apply_change(child, newpar, oc.model[newpar]['level'])
        oc.save()
        import openpyxl
        ws = openpyxl.load_workbook(opath, read_only=True)['SYSTEM']
        H = {c.value: j for j, c in enumerate(next(ws.iter_rows(max_row=1)), 0)}
        got = None
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[H['node_id']] == child:
                got = row[H['parent_node_id']]
                break
        check(got == newpar, 'org chart: nadřazenost zapsána do SYSTEM listu')
    finally:
        open(opath, 'wb').write(obackup)
    check(open(opath, 'rb').read() == obackup, 'org chart: sešit obnoven')
    oc.destroy()

    win.destroy()
    print('\n' + ('VŠE OK' if not FAIL else f'SELHALO: {len(FAIL)}'))
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
