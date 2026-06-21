#!/usr/bin/env python3
"""
edit_system_gui.py — Tkinter editor SYSTEM listu (levely, nodes, názvy soutěží…).

Stejný styl jako solve_flags_gui.py. Vlevo strom soutěží sezóny (hierarchie),
vpravo editovatelná pole (název, úroveň, typ, rodič, feeds_into / _loser, poznámka)
a tabulka vybrané soutěže jako kontext. Uložení rovnou do data/S*_FINAL.xlsx,
tlačítko „Zabalit do ZIP" + PRECTI_ME.txt.

Samostatný soubor (Python + openpyxl; tkinter je součást Pythonu).
Spuštění:  python edit_system_gui.py   (Windows: dvojklik na run_edit.bat)

== ZÁLOŽKA / ZÁKLAD ==  funkční v1 na opravy levelů/názvů/hierarchie; další pole
a hromadné akce doděláme, až k tomu dojdeme.
"""
import datetime
import glob
import os
import re
import zipfile
import collections
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import openpyxl

NON_DATA = {'META', 'CLUBS', 'SYSTEM', 'NOTES', 'TODO', 'CHANGES', 'README'}
LEVELS = ['', 'L10', 'L15', 'L20', 'L25', 'L30', 'L35', 'L40', 'L45',
          'L50', 'L55', 'L60', 'L70', 'L80', 'L90', 'L100']
TYPES = ['', 'league', 'group', 'final_group', 'playoff_round', 'playoff',
         'classification', 'qualification_group', 'qualification_series',
         'relegation_group', 'baraz', 'regional_championship', 'series',
         'final_series', 'region']
SYS_FIELDS = ['name', 'competition_type', 'level', 'parent_node_id',
              'feeds_into', 'feeds_into_loser', 'note']


def find_data_dir():
    here = os.path.abspath(os.path.dirname(__file__))
    for cand in (os.path.join(here, 'data'), here, os.getcwd()):
        if glob.glob(os.path.join(cand, 'S*_FINAL.xlsx')):
            return cand
    return None


def season_ids(data_dir):
    out = []
    for p in sorted(glob.glob(os.path.join(data_dir, 'S*_FINAL.xlsx'))):
        out.append(re.search(r'S(\d{4}_\d{2})', os.path.basename(p)).group(1))
    return out


def load_season(path):
    """Vrať (nodes, system_header_cols, standings). nodes mají i řádek v SYSTEM."""
    wb = openpyxl.load_workbook(path, data_only=True)
    sys_rows = list(wb['SYSTEM'].iter_rows(values_only=True))
    SH = {c: j for j, c in enumerate(sys_rows[0]) if c}
    nodes = {}
    order = []
    for i, r in enumerate(sys_rows[1:], start=2):
        nid = r[SH['node_id']] if 'node_id' in SH else None
        if not nid:
            continue
        nd = {'node_id': nid, '_row': i}
        for f in SYS_FIELDS:
            nd[f] = r[SH[f]] if f in SH else None
        nodes[nid] = nd
        order.append(nid)
    standings = collections.defaultdict(list)        # node_id -> [(pos, club, fate)]
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        rr = list(wb[sh].iter_rows(values_only=True))
        if not rr:
            continue
        H = {c: j for j, c in enumerate(rr[0]) if c}
        if 'node_id' not in H or 'row_type' not in H:
            continue
        for r in rr[1:]:
            if r[H['row_type']] != 'T':
                continue
            nid = r[H['node_id']]
            if nid:
                standings[nid].append((
                    r[H.get('pos', -1)] if 'pos' in H else '',
                    r[H.get('club_name', -1)] if 'club_name' in H else '',
                    r[H.get('season_fate', -1)] if 'season_fate' in H else ''))
    wb.close()
    return nodes, order, standings


class SystemEditor(tk.Toplevel):
    def __init__(self, master, data_dir):
        super().__init__(master)
        self.title('Almanach — editor soutěží (levely / nodes / názvy)')
        self.geometry('1240x800')
        self.data_dir = data_dir
        self.seasons = season_ids(data_dir)
        self.wbcache = {}
        self.nodes = {}
        self.order = []
        self.standings = {}
        self.cur = None
        self._build_ui()
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        if self.seasons:
            self.season_var.set(self.seasons[0])
            self.load_season(self.seasons[0])

    # -- UI --
    def _build_ui(self):
        top = ttk.Frame(self); top.pack(fill='x', padx=8, pady=6)
        ttk.Label(top, text='Sezóna:').pack(side='left')
        self.season_var = tk.StringVar()
        cb = ttk.Combobox(top, textvariable=self.season_var, values=self.seasons,
                          width=12, state='readonly'); cb.pack(side='left', padx=4)
        cb.bind('<<ComboboxSelected>>', lambda e: self.load_season(self.season_var.get()))
        ttk.Button(top, text='Zabalit do ZIP ▸', command=self.export_zip).pack(side='right')
        self.info = ttk.Label(top, text='', foreground='#555'); self.info.pack(side='right', padx=12)

        pan = ttk.Panedwindow(self, orient='horizontal'); pan.pack(fill='both', expand=True, padx=8, pady=4)
        left = ttk.Frame(pan); pan.add(left, weight=1)
        self.tree = ttk.Treeview(left, show='tree'); self.tree.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(left, command=self.tree.yview); sb.pack(side='right', fill='y')
        self.tree.config(yscrollcommand=sb.set)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        right = ttk.Frame(pan); pan.add(right, weight=2)
        form = ttk.LabelFrame(right, text='Úprava soutěže (node)'); form.pack(fill='x', pady=4)
        self.f = {}
        def row(lbl, widget, r):
            ttk.Label(form, text=lbl).grid(row=r, column=0, sticky='w', padx=6, pady=3)
            widget.grid(row=r, column=1, sticky='we', padx=6, pady=3)
        form.grid_columnconfigure(1, weight=1)
        self.f['name'] = ttk.Entry(form); row('Název:', self.f['name'], 0)
        self.f['level'] = ttk.Combobox(form, values=LEVELS, width=12); row('Úroveň:', self.f['level'], 1)
        self.f['competition_type'] = ttk.Combobox(form, values=TYPES); row('Typ:', self.f['competition_type'], 2)
        self.f['parent_node_id'] = ttk.Combobox(form); row('Rodič:', self.f['parent_node_id'], 3)
        self.f['feeds_into'] = ttk.Combobox(form); row('Postupuje do:', self.f['feeds_into'], 4)
        self.f['feeds_into_loser'] = ttk.Combobox(form); row('Sestup/poražení do:', self.f['feeds_into_loser'], 5)
        self.f['note'] = ttk.Entry(form); row('Poznámka:', self.f['note'], 6)
        self.idlbl = ttk.Label(form, text='', foreground='#999')
        self.idlbl.grid(row=7, column=1, sticky='w', padx=6)
        ttk.Button(form, text='Uložit do xlsx', command=self.save).grid(row=7, column=0, padx=6, pady=6, sticky='w')

        ttk.Label(right, text='Tabulka vybrané soutěže (kontext):',
                  font=('TkDefaultFont', 9, 'bold')).pack(anchor='w', pady=(8, 2))
        cols = ('pos', 'klub', 'osud')
        self.tbl = ttk.Treeview(right, columns=cols, show='headings', height=14)
        for c, w in zip(cols, (50, 360, 200)):
            self.tbl.heading(c, text=c.upper()); self.tbl.column(c, width=w, anchor='w')
        self.tbl.column('pos', anchor='center'); self.tbl.pack(fill='both', expand=True)

        self.status = ttk.Label(self, text='', relief='sunken', anchor='w'); self.status.pack(fill='x', side='bottom')

    # -- data --
    def load_season(self, sid):
        path = os.path.join(self.data_dir, f'S{sid}_FINAL.xlsx')
        self.nodes, self.order, self.standings = load_season(path)
        # combobox nabídky pro rodič/feeds = "název  [node_id]"
        opts = ['(žádný)'] + [f"{self.nodes[n]['name']}  [{n}]" for n in self.order]
        self.id_by_label = {f"{self.nodes[n]['name']}  [{n}]": n for n in self.order}
        for k in ('parent_node_id', 'feeds_into', 'feeds_into_loser'):
            self.f[k]['values'] = opts
        self.populate_tree()
        self.info.config(text=f'{len(self.nodes)} soutěží / fází')

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        kids = collections.defaultdict(list)
        roots = []
        ids = set(self.order)
        for n in self.order:
            p = self.nodes[n]['parent_node_id']
            if p in ids:
                kids[p].append(n)
            else:
                roots.append(n)
        self.iid_node = {}
        def ins(parent, nid):
            nd = self.nodes[nid]
            iid = self.tree.insert(parent, 'end',
                                   text=f"{nd['name'] or nid}   ({nd['level'] or '—'})", open=False)
            self.iid_node[iid] = nid
            for c in kids.get(nid, []):
                ins(iid, c)
        for r in roots:
            ins('', r)

    def on_select(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        nid = self.iid_node.get(sel[0])
        if not nid:
            return
        self.cur = nid
        nd = self.nodes[nid]
        self.f['name'].delete(0, 'end'); self.f['name'].insert(0, nd['name'] or '')
        self.f['level'].set(nd['level'] or '')
        self.f['competition_type'].set(nd['competition_type'] or '')
        self.f['note'].delete(0, 'end'); self.f['note'].insert(0, nd['note'] or '')
        for k in ('parent_node_id', 'feeds_into', 'feeds_into_loser'):
            v = nd[k]
            self.f[k].set(f"{self.nodes[v]['name']}  [{v}]" if v in self.nodes else '(žádný)')
        self.idlbl.config(text=f'node_id: {nid}')
        self.tbl.delete(*self.tbl.get_children())
        for k, (pos, club, fate) in enumerate(self.standings.get(nid, []), 1):
            self.tbl.insert('', 'end', values=(pos if pos not in (None, '') else k,
                                               club, fate if fate not in (None, '') else '—'))

    def _resolve(self, label):
        if label in ('', '(žádný)', None):
            return None
        if label in self.id_by_label:
            return self.id_by_label[label]
        m = re.search(r'\[([^\]]+)\]\s*$', str(label))
        return m.group(1) if m else (label if label in self.nodes else None)

    def _wb(self, sid):
        if sid not in self.wbcache:
            self.wbcache[sid] = openpyxl.load_workbook(
                os.path.join(self.data_dir, f'S{sid}_FINAL.xlsx'))
        return self.wbcache[sid]

    def save(self):
        if not self.cur:
            return
        sid = self.season_var.get()
        nd = self.nodes[self.cur]
        vals = {
            'name': self.f['name'].get().strip(),
            'level': self.f['level'].get().strip(),
            'competition_type': self.f['competition_type'].get().strip(),
            'note': self.f['note'].get().strip(),
            'parent_node_id': self._resolve(self.f['parent_node_id'].get()),
            'feeds_into': self._resolve(self.f['feeds_into'].get()),
            'feeds_into_loser': self._resolve(self.f['feeds_into_loser'].get()),
        }
        wb = self._wb(sid); ws = wb['SYSTEM']
        head = [c.value for c in ws[1]]
        for f, v in vals.items():
            if f in head:
                ws.cell(row=nd['_row'], column=head.index(f) + 1).value = (v or None)
                nd[f] = v
        wb.save(os.path.join(self.data_dir, f'S{sid}_FINAL.xlsx'))
        # promítni do stromu (název/level)
        for iid, n in self.iid_node.items():
            if n == self.cur:
                self.tree.item(iid, text=f"{vals['name'] or self.cur}   ({vals['level'] or '—'})")
                break
        self.status.config(text=f"Uloženo: {self.cur}  →  {vals['name']} ({vals['level']})")

    def export_zip(self):
        out = filedialog.asksaveasfilename(
            defaultextension='.zip',
            initialfile=f'almanach_system_{datetime.date.today()}.zip',
            filetypes=[('ZIP', '*.zip')])
        if not out:
            return
        readme = ('ALMANACH — sešity po úpravách SYSTEM (levely / nodes / názvy soutěží).\n'
                  f'Vytvořeno: {datetime.datetime.now():%Y-%m-%d %H:%M}\n')
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(glob.glob(os.path.join(self.data_dir, 'S*_FINAL.xlsx'))):
                z.write(p, os.path.join('data', os.path.basename(p)))
            z.writestr('PRECTI_ME.txt', readme)
        messagebox.showinfo('ZIP', f'Hotovo:\n{out}')

    def _on_close(self):
        for wb in self.wbcache.values():
            try:
                wb.close()
            except Exception:
                pass
        self.destroy()


def main():
    root = tk.Tk(); root.withdraw()
    data_dir = find_data_dir()
    if not data_dir:
        data_dir = filedialog.askdirectory(title='Vyber složku se sešity S*_FINAL.xlsx')
    if not data_dir or not glob.glob(os.path.join(data_dir, 'S*_FINAL.xlsx')):
        print('Nenašel jsem žádné S*_FINAL.xlsx.'); return
    app = SystemEditor(root, data_dir)
    app.protocol('WM_DELETE_WINDOW', lambda: (app._on_close(), root.destroy()))
    root.mainloop()


if __name__ == '__main__':
    main()
