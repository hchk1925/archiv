#!/usr/bin/env python3
"""
desktop.py — Almanach: desktopový korektor (Tkinter).

Okno jako normální program; čte a zapisuje přímo data/S*_FINAL.xlsx.
Sdílí backend s webovou verzí (app.py): načítání sezón, audit, PDF.

Spuštění:  python desktop.py
Potřebuje: tkinter (součást Pythonu na Windows/macOS) + openpyxl (+ reportlab pro PDF).
"""
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import app as core  # sdílený backend (Flask se neespouští, jen importuje)

VARIANTY = ['', 'OK – legitimní fáze', 'doplnit týmy', 'sloučit', 'smazat',
            'opravit (level/region/název)', 'neúplné – nech co je']
STAVY = ['ne', 'ANO', 'nedořešitelné']
NODE_RE = re.compile(r'NODE_S\d{4}_\d{2}_\d+')


# ─────────── čisté helpery (testovatelné bez GUI) ───────────
def node_of(todo_item):
    m = NODE_RE.search(str(todo_item.get('reference', '')))
    return m.group(0) if m else None


def resolved_set(d):
    out = set()
    for t in d['todo']:
        if str(t['done']).strip().upper() == 'ANO':
            nid = node_of(t)
            if nid:
                out.add(nid)
    return out


def node_todo_map(d):
    by = {}
    for t in d['todo']:
        nid = node_of(t)
        if nid:
            by.setdefault(nid, t)
    return by


def open_file(path):
    try:
        if sys.platform.startswith('win'):
            os.startfile(path)  # noqa
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.run(['open', path])
        else:
            import subprocess
            subprocess.run(['xdg-open', path])
    except Exception:
        pass


# ─────────── GUI ───────────
class AlmanachDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Almanach — korektor')
        self.geometry('1180x760')
        self.minsize(900, 560)
        self.seasons = core.list_season_ids()
        self.sid = None
        self.d = None
        self.item_map = {}        # tree iid -> ('node', nid) | ('todo', num)
        self.nodes = {}
        self.anote = {}
        self.ntodo = {}
        self.cur_num = None       # # aktuální audit položky (nebo None)
        self._build_ui()
        if self.seasons:
            self.season_var.set(self.seasons[0])
            self.load_sid(self.seasons[0])

    # -- stavba UI --
    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill='x', padx=8, pady=6)
        ttk.Label(top, text='Sezóna:').pack(side='left')
        self.season_var = tk.StringVar()
        cb = ttk.Combobox(top, textvariable=self.season_var, values=self.seasons,
                          width=12, state='readonly')
        cb.pack(side='left', padx=4)
        cb.bind('<<ComboboxSelected>>', self.on_season)
        ttk.Button(top, text='◀', width=3, command=lambda: self.step(-1)).pack(side='left')
        ttk.Button(top, text='▶', width=3, command=lambda: self.step(1)).pack(side='left')
        self.count_lbl = ttk.Label(top, text='')
        self.count_lbl.pack(side='left', padx=12)
        ttk.Button(top, text='PDF plný', command=lambda: self.export('full')).pack(side='right', padx=2)
        ttk.Button(top, text='PDF audit', command=lambda: self.export('audit')).pack(side='right', padx=2)

        pan = ttk.Panedwindow(self, orient='horizontal')
        pan.pack(fill='both', expand=True, padx=8, pady=4)

        left = ttk.Frame(pan)
        pan.add(left, weight=1)
        self.tree = ttk.Treeview(left, show='tree')
        self.tree.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(left, command=self.tree.yview)
        sb.pack(side='right', fill='y')
        self.tree.config(yscrollcommand=sb.set)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.tag_configure('gap', foreground='#b45309')
        self.tree.tag_configure('done', foreground='#1b7a32')

        right = ttk.Frame(pan)
        pan.add(right, weight=2)
        self.title_lbl = ttk.Label(right, text='', font=('TkDefaultFont', 13, 'bold'),
                                   wraplength=640, justify='left')
        self.title_lbl.pack(anchor='w', pady=(0, 2))
        self.comment = tk.Text(right, height=3, wrap='word', relief='flat',
                               background='#fff7e0', font=('TkDefaultFont', 10))
        self.comment.pack(fill='x', pady=3)
        self.comment.config(state='disabled')

        cols = ('pos', 'klub', 'GP', 'W', 'D', 'L', 'GFGA', 'PTS', 'fate')
        heads = ('#', 'Klub', 'GP', 'W', 'D', 'L', 'GF:GA', 'PTS', 'Fate')
        widths = (34, 280, 38, 32, 32, 32, 60, 38, 96)
        self.table = ttk.Treeview(right, columns=cols, show='headings', height=10)
        for c, h, w in zip(cols, heads, widths):
            self.table.heading(c, text=h)
            self.table.column(c, width=w, anchor='center')
        self.table.column('klub', anchor='w')
        self.table.pack(fill='both', expand=True, pady=3)

        self.form = ttk.LabelFrame(right, text='Řešení (zapíše se rovnou do xlsx)')
        self.form.pack(fill='x', pady=4)
        r1 = ttk.Frame(self.form)
        r1.pack(fill='x', padx=6, pady=3)
        ttk.Label(r1, text='Stav:').pack(side='left')
        self.stav = tk.StringVar(value='ne')
        ttk.Combobox(r1, textvariable=self.stav, values=STAVY, width=14,
                     state='readonly').pack(side='left', padx=(2, 12))
        ttk.Label(r1, text='Řešení:').pack(side='left')
        self.varianta = tk.StringVar(value='')
        ttk.Combobox(r1, textvariable=self.varianta, values=VARIANTY, width=28,
                     state='readonly').pack(side='left', padx=2)
        r2 = ttk.Frame(self.form)
        r2.pack(fill='x', padx=6, pady=3)
        ttk.Label(r2, text='Poznámka:').pack(side='left')
        self.pozn = ttk.Entry(r2)
        self.pozn.pack(side='left', fill='x', expand=True, padx=2)
        self.save_btn = ttk.Button(self.form, text='Uložit do xlsx', command=self.save)
        self.save_btn.pack(anchor='e', padx=6, pady=(0, 5))
        self._set_form_enabled(False)

        self.status = ttk.Label(self, text='', relief='sunken', anchor='w')
        self.status.pack(fill='x', side='bottom')

    # -- data --
    def load_sid(self, sid):
        self.sid = sid
        self.d = core.load_season(sid)
        self.nodes = {n['node_id']: n for n in self.d['system']}
        self.anote = core.audit_notes_by_node(self.d)
        self.ntodo = node_todo_map(self.d)
        self.populate_tree()
        op = sum(1 for t in self.d['todo']
                 if str(t['done']).strip().upper() != 'ANO')
        dn = sum(1 for t in self.d['todo']
                 if str(t['done']).strip().upper() == 'ANO')
        self.count_lbl.config(text=f'{self.d["label"]}  ·  {op} otevřených · {dn} vyřešených')
        self._clear_detail()

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.item_map = {}
        d = self.d
        resolved = resolved_set(d)
        nr = core.node_rows(d)
        for sh in sorted(d['standings'].keys()):
            trows = [r for r in d['standings'][sh] if r['row_type'] == 'T']
            if not trows:
                continue
            shid = self.tree.insert('', 'end', text=sh, open=False)
            seen = set()
            for r in trows:
                nid = r['node_id']
                if nid in seen:
                    continue
                seen.add(nid)
                nm = self.nodes.get(nid, {}).get('name') or nid or '?'
                gap = nid in self.anote
                done = nid in resolved
                mark = '✓ ' if done else ('⚑ ' if gap else '   ')
                tag = 'done' if done else ('gap' if gap else '')
                iid = self.tree.insert(shid, 'end', text=f'{mark}{nm}',
                                       tags=(tag,) if tag else ())
                self.item_map[iid] = ('node', nid)
        others = [t for t in d['todo'] if not node_of(t)]
        if others:
            oid = self.tree.insert('', 'end', text='▣ Ostatní položky (TODO)', open=False)
            for t in others:
                done = str(t['done']).strip().upper() == 'ANO'
                mark = '✓ ' if done else '• '
                txt = f'{mark}{t["typ"]}: {core.clean_popis(t["popis"])[:60]}'
                iid = self.tree.insert(oid, 'end', text=txt,
                                       tags=('done',) if done else ('gap',))
                self.item_map[iid] = ('todo', t['num'])

    # -- výběr / detail --
    def on_season(self, _evt=None):
        self.load_sid(self.season_var.get())

    def step(self, delta):
        if not self.sid:
            return
        i = self.seasons.index(self.sid) + delta
        if 0 <= i < len(self.seasons):
            self.season_var.set(self.seasons[i])
            self.load_sid(self.seasons[i])

    def on_select(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        kind_val = self.item_map.get(sel[0])
        if not kind_val:
            self._clear_detail()
            return
        kind, val = kind_val
        if kind == 'node':
            self.show_node(val)
        else:
            self.show_todo(val)

    def show_node(self, nid):
        nm = self.nodes.get(nid, {}).get('name') or nid
        self.title_lbl.config(text=nm)
        notes = self.anote.get(nid, [])
        done = nid in resolved_set(self.d)
        self._set_comment(('✓ vyřešeno — ' if done else '⚑ ') + ' | '.join(notes)
                          if notes else '(bez auditní poznámky)',
                          green=done, warn=bool(notes) and not done)
        # tabulka
        self.table.delete(*self.table.get_children())
        for r in core.node_rows(self.d).get(nid, []):
            self.table.insert('', 'end', values=(
                r['pos'] or '', r['club_name'] or '', r['GP'] or '', r['W'] or '',
                r['D'] or '', r['L'] or '', f'{r["GF"] or ""}:{r["GA"] or ""}',
                r['PTS'] or '', r['season_fate'] or ''))
        t = self.ntodo.get(nid)
        self._load_form(t)

    def show_todo(self, num):
        t = next((x for x in self.d['todo'] if str(x['num']) == str(num)), None)
        self.table.delete(*self.table.get_children())
        if not t:
            return
        self.title_lbl.config(text=f'{t["typ"]} · {t["reference"]}')
        done = str(t['done']).strip().upper() == 'ANO'
        self._set_comment(core.clean_popis(t['popis']), green=done, warn=not done)
        self._load_form(t)

    def _load_form(self, t):
        if not t:
            self.cur_num = None
            self.stav.set('ne')
            self.varianta.set('')
            self.pozn.delete(0, 'end')
            self._set_form_enabled(False)
            return
        self.cur_num = t['num']
        self.stav.set(str(t['done']).strip() or 'ne')
        pozn = t['poznamka'] or ''
        m = re.match(r'^\[([^\]]*)\]\s*(.*)$', pozn)
        if m and m.group(1) in VARIANTY:
            self.varianta.set(m.group(1))
            pozn = m.group(2)
        else:
            self.varianta.set('')
        self.pozn.delete(0, 'end')
        self.pozn.insert(0, pozn)
        self._set_form_enabled(True)

    def _set_comment(self, text, green=False, warn=False):
        self.comment.config(state='normal')
        self.comment.delete('1.0', 'end')
        self.comment.insert('1.0', text)
        self.comment.config(background='#e4f5e7' if green else
                            ('#fff7e0' if warn else '#f0f0f0'))
        self.comment.config(state='disabled')

    def _set_form_enabled(self, on):
        st = 'normal' if on else 'disabled'
        for w in self.form.winfo_children():
            for ch in (w.winfo_children() if w.winfo_children() else [w]):
                try:
                    ch.configure(state=st if not isinstance(ch, ttk.Combobox)
                                 else ('readonly' if on else 'disabled'))
                except tk.TclError:
                    pass
        try:
            self.save_btn.configure(state=st)
        except tk.TclError:
            pass

    def _clear_detail(self):
        self.title_lbl.config(text='— vyber soutěž vlevo —')
        self._set_comment('')
        self.table.delete(*self.table.get_children())
        self._load_form(None)

    # -- akce --
    def save(self):
        if self.cur_num is None:
            messagebox.showinfo('Almanach', 'Tato položka nemá co ukládat.')
            return
        core.save_todo_resolution(self.sid, self.cur_num, self.stav.get(),
                                  self.varianta.get(), self.pozn.get())
        self.status.config(text=f'Uloženo do data/S{self.sid}_FINAL.xlsx '
                                f'(#{self.cur_num}).')
        # obnov sezónu a vrať výběr
        sel = self.tree.selection()
        self.load_sid(self.sid)
        # zachovej rozbalení/označení přibližně: znovu označit stejné kind/val
        if sel:
            pass

    def export(self, kind):
        try:
            data = (core.build_full_pdf(self.d, self.sid) if kind == 'full'
                    else core.build_season_pdf(self.d, self.sid))
        except Exception as e:  # reportlab chybí apod.
            messagebox.showerror('PDF', f'PDF se nepodařilo vytvořit:\n{e}')
            return
        default = f'{"almanach" if kind == "full" else "audit"}_S{self.sid}.pdf'
        path = filedialog.asksaveasfilename(defaultextension='.pdf',
                                            initialfile=default,
                                            filetypes=[('PDF', '*.pdf')])
        if not path:
            return
        with open(path, 'wb') as f:
            f.write(data)
        self.status.config(text=f'PDF uloženo: {path}')
        open_file(path)


def main():
    AlmanachDesktop().mainloop()


if __name__ == '__main__':
    main()
