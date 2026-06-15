#!/usr/bin/env python3
"""
desktop.py — Almanach: desktopový korektor (Tkinter).

Okno jako normální program; čte a zapisuje přímo data/S*_FINAL.xlsx.
Sdílí backend s webovou verzí (app.py): načítání sezón, audit, PDF.

Spuštění:  python desktop.py
Potřebuje: tkinter (součást Pythonu na Windows/macOS) + openpyxl (+ reportlab pro PDF).
"""
import collections
import os
import re
import sys
import tkinter as tk
from math import ceil
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
        self.after(80, lambda: self.pan.sashpos(0, 470))

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
        ttk.Button(top, text='Org chart ✎', command=self.open_orgchart).pack(side='right', padx=10)

        self.pan = ttk.Panedwindow(self, orient='horizontal')
        self.pan.pack(fill='both', expand=True, padx=8, pady=4)

        left = ttk.Frame(self.pan)
        self.pan.add(left, weight=1)
        self.tree = ttk.Treeview(left, show='tree')
        self.tree.column('#0', width=440, minwidth=240, stretch=True)
        xsb = ttk.Scrollbar(left, orient='horizontal', command=self.tree.xview)
        xsb.pack(side='bottom', fill='x')
        sb = ttk.Scrollbar(left, command=self.tree.yview)
        sb.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.config(yscrollcommand=sb.set, xscrollcommand=xsb.set)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.tag_configure('gap', foreground='#b45309')
        self.tree.tag_configure('done', foreground='#1b7a32')

        right = ttk.Frame(self.pan)
        self.pan.add(right, weight=2)
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
        # Strom = org-chart hierarchie (parent_node_id) s plnými názvy.
        # Žádné kódy listů — jen čitelné názvy soutěží.
        self.tree.delete(*self.tree.get_children())
        self.item_map = {}
        d = self.d
        resolved = resolved_set(d)
        ids = {n['node_id'] for n in d['system']}
        children = {}
        roots = []
        for n in d['system']:
            p = n['parent_node_id']
            if p and p in ids:
                children.setdefault(p, []).append(n)
            else:
                roots.append(n)   # bez rodiče (nebo rodič mimo sezónu) = vršek

        def keyf(n):
            return (core.lvl(n['level']) or 9999, str(n['name']))

        def insert(parent_iid, n):
            nid = n['node_id']
            gap = nid in self.anote
            done = nid in resolved
            mark = '✓ ' if done else ('⚑ ' if gap else '')
            tag = 'done' if done else ('gap' if gap else '')
            iid = self.tree.insert(parent_iid, 'end',
                                   text=f'{mark}{n["name"] or nid}',
                                   tags=(tag,) if tag else (), open=False)
            self.item_map[iid] = ('node', nid)
            for c in sorted(children.get(nid, []), key=keyf):
                insert(iid, c)

        for n in sorted(roots, key=keyf):
            insert('', n)
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

    def open_orgchart(self):
        if self.d:
            OrgChart(self, self.sid, self.d, on_saved=self.reload_current)

    def reload_current(self):
        if self.sid:
            self.load_sid(self.sid)
            self.status.config(text=f'Org chart uložen do data/S{self.sid}_FINAL.xlsx.')


LANE_LABEL = {
    'L10': 'Nejvyšší soutěž', 'L15': 'Kvalifikace',
    'L20': '2. úroveň (oblastní)', 'L30': '3. úroveň (krajský přebor)',
    'L40': '4. úroveň', 'L50': '5. úroveň',
}


def lane_label(lev):
    if lev in LANE_LABEL:
        return LANE_LABEL[lev]
    n = core.lvl(lev)
    return f'{n // 10}. úroveň' if n else '(bez úrovně)'


class OrgChart(tk.Toplevel):
    """Org chart sezóny: patra dle úrovní, přetahováním se mění úroveň (svisle)
    a nadřazenost (puštění na jinou soutěž). Uloží se do SYSTEM listu xlsx."""
    BOXW, BOXH, GAPX, GAPY, HEADER, COLS, PAD = 190, 46, 18, 16, 30, 7, 16
    # jemné barvy pater (fill, okraj) — cyklicky podle úrovně
    PALETTE = [('#e3edff', '#8fb0e6'), ('#dcf4e8', '#74c19c'),
               ('#fdecc9', '#e0b76e'), ('#ece0f7', '#b194d6'),
               ('#fde0e2', '#e0939a'), ('#ddf0f3', '#83bdc7'),
               ('#eef1d6', '#bcc47e')]
    BAND_BG = ('#f6f8fc', '#eef2f8')

    def __init__(self, master, sid, d, on_saved=None):
        super().__init__(master)
        self.title(f'Org chart — {d["label"]}')
        self.geometry('1240x760')
        self.sid = sid
        self.on_saved = on_saved
        self.nodes = {n['node_id']: dict(n) for n in d['system']}
        self.model = {nid: {'parent': (n['parent_node_id']
                                       if n['parent_node_id'] in self.nodes else None),
                            'level': n['level']}
                      for nid, n in self.nodes.items()}
        self.orig = {nid: dict(v) for nid, v in self.model.items()}
        self.item_node = {}     # canvas item id -> nid (boxy = drag)
        self.toggle_node = {}   # canvas item id -> nid (▸/▾ = sbalit)
        self.box = {}           # nid -> (x, y)
        self.bands = []         # [(level, y0, y1)]
        self.drag = None
        self.tier_item = {}     # canvas item id -> level (pruh patra = sbalit)
        # výchozí stav: rodiče sbalené + regionální patra (úroveň ≥ 30) sbalená
        # do jednoho „chlívku", ať to není přeplácané
        kids = self._children()
        self.collapsed = {nid for nid in self.nodes if kids.get(nid)}
        # rozbalené necháme jen vrchní patra (liga/kvalifikace/oblastní, úroveň < 30);
        # regiony a „bez úrovně" jsou sbalené do chlívku
        self.tier_collapsed = {lev for lev in {v['level'] for v in self.model.values()}
                               if not (core.lvl(lev) and core.lvl(lev) < 30)}
        self._build()
        self.relayout()

    # -- UI --
    def _build(self):
        bar = ttk.Frame(self)
        bar.pack(fill='x')
        ttk.Label(bar, foreground='#555',
                  text='Táhni soutěž:  svisle = změna úrovně (patro)  ·  '
                       'puštění na jinou soutěž = nadřazenost.').pack(side='left', padx=6, pady=4)
        self.save_btn = ttk.Button(bar, text='Uložit do xlsx', command=self.save)
        self.save_btn.pack(side='right', padx=4)
        ttk.Button(bar, text='Vrátit změny', command=self.reset).pack(side='right')
        self.info = ttk.Label(bar, text='')
        self.info.pack(side='right', padx=10)
        wrap = ttk.Frame(self)
        wrap.pack(fill='both', expand=True)
        self.cv = tk.Canvas(wrap, background='#fbfbfd', highlightthickness=0)
        ysb = ttk.Scrollbar(wrap, orient='vertical', command=self.cv.yview)
        xsb = ttk.Scrollbar(self, orient='horizontal', command=self.cv.xview)
        self.cv.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        xsb.pack(side='bottom', fill='x')
        ysb.pack(side='right', fill='y')
        self.cv.pack(side='left', fill='both', expand=True)
        self.cv.tag_bind('box', '<ButtonPress-1>', self._press)
        self.cv.tag_bind('box', '<B1-Motion>', self._motion)
        self.cv.tag_bind('box', '<ButtonRelease-1>', self._release)
        self.cv.tag_bind('tier', '<ButtonPress-1>', self._toggle_tier)
        self.cv.tag_bind('toggle', '<ButtonPress-1>', self._toggle_node)

    # -- model helpers --
    def _children(self):
        kids = collections.defaultdict(list)
        for nid, v in self.model.items():
            if v['parent']:
                kids[v['parent']].append(nid)
        return kids

    def _root_of(self, nid):
        seen = set()
        while True:
            p = self.model[nid]['parent']
            if not p or p not in self.model or p in seen:
                return nid
            seen.add(nid)
            nid = p

    def _descendants(self, nid):
        kids = self._children()
        out, stack = set(), [nid]
        while stack:
            for c in kids[stack.pop()]:
                if c not in out:
                    out.add(c)
                    stack.append(c)
        return out

    def _levels(self):
        return sorted({v['level'] for v in self.model.values()},
                      key=lambda l: (core.lvl(l) or 9999))

    def _visible(self, nid):
        """Uzel je vidět, pokud žádný jeho předek není sbalený."""
        p = self.model[nid]['parent']
        while p and p in self.model:
            if p in self.collapsed:
                return False
            p = self.model[p]['parent']
        return True

    def _round_rect(self, x1, y1, x2, y2, r=9, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.cv.create_polygon(pts, smooth=True, **kw)

    # -- kreslení --
    def relayout(self):
        self.cv.delete('all')
        self.item_node = {}
        self.toggle_node = {}
        self.tier_item = {}
        self.box = {}
        self.bands = []
        kids = self._children()
        per = collections.defaultdict(list)
        for nid, v in self.model.items():
            per[v['level']].append(nid)
        rootname = lambda n: str(self.nodes[self._root_of(n)]['name'])
        W = self.PAD + self.COLS * (self.BOXW + self.GAPX) + 30
        nodecol = {}
        plan = []          # (nid, x, y, fill, edge, has_kids, collapsed)
        y = self.PAD
        for ti, lev in enumerate(self._levels()):
            fill, edge = self.PALETTE[ti % len(self.PALETTE)]
            ids = per[lev]
            tcol = lev in self.tier_collapsed
            vis = ([] if tcol else
                   [n for n in sorted(ids, key=lambda n: (rootname(n), str(self.nodes[n]['name'])))
                    if self._visible(n)])
            rows = ceil(len(vis) / self.COLS) if vis else 0
            body_h = rows * (self.BOXH + self.GAPY) if vis else 0
            self._draw_tier_header(lev, len(ids), tcol, edge, y, W)
            if body_h:
                self.cv.create_rectangle(0, y + self.HEADER - 6, W,
                                         y + self.HEADER + body_h + 4,
                                         fill=self.BAND_BG[ti % 2], outline='', tags='bandbg')
            top = y + self.HEADER
            for i, nid in enumerate(vis):
                col, row = i % self.COLS, i // self.COLS
                bx = self.PAD + col * (self.BOXW + self.GAPX)
                by = top + row * (self.BOXH + self.GAPY)
                self.box[nid] = (bx, by)
                nodecol[nid] = (fill, edge)
                plan.append((nid, bx, by, fill, edge, bool(kids.get(nid)),
                             nid in self.collapsed))
            band_h = self.HEADER + (body_h + 12 if body_h else 4)
            self.bands.append((lev, y, y + band_h))
            y += band_h + 6
        self._draw_links()
        for args in plan:
            self._draw_box(*args)
        self.cv.configure(scrollregion=(0, 0, W + 10, y + 20))
        self._refresh_info()

    def _draw_tier_header(self, lev, count, collapsed, edge, y, W):
        tri = '▸' if collapsed else '▾'
        hint = '  — klikni pro rozbalení' if collapsed and count > 1 else ''
        bar = self._round_rect(self.PAD, y, W - 18, y + self.HEADER - 8, r=8,
                               fill=edge, outline='', tags=('tier', f'tier_{lev}'))
        t = self.cv.create_text(self.PAD + 12, y + (self.HEADER - 8) / 2, anchor='w',
                                text=f'{tri}  {lane_label(lev)}   ({count}){hint}',
                                fill='white', font=('TkDefaultFont', 10, 'bold'),
                                tags=('tier', f'tier_{lev}'))
        self.tier_item[bar] = lev
        self.tier_item[t] = lev

    def _draw_box(self, nid, x, y, fill, edge, has_kids, collapsed):
        changed = self.model[nid] != self.orig.get(nid)
        f = '#fbd38d' if changed else fill
        e = '#d97706' if changed else edge
        rect = self._round_rect(x, y, x + self.BOXW, y + self.BOXH, r=9,
                                fill=f, outline=e, width=1.5, tags=('box', f'g_{nid}'))
        nm = str(self.nodes[nid]['name']).strip() or '(bez názvu)'
        if len(nm) > 54:
            nm = nm[:52] + '…'
        offx = 24 if has_kids else 11
        txt = self.cv.create_text(x + offx, y + self.BOXH / 2, anchor='w', text=nm,
                                  width=self.BOXW - offx - 8, font=('TkDefaultFont', 8),
                                  tags=('box', f'g_{nid}'))
        self.item_node[rect] = nid
        self.item_node[txt] = nid
        if has_kids:
            tri = self.cv.create_text(x + 12, y + self.BOXH / 2, anchor='w',
                                      text=('▸' if collapsed else '▾'),
                                      font=('TkDefaultFont', 9, 'bold'), fill=e,
                                      tags=('toggle',))
            self.toggle_node[tri] = nid

    def _draw_links(self):
        for nid, v in self.model.items():
            p = v['parent']
            if p and p in self.box and nid in self.box:
                px, py = self.box[p]
                cx, cy = self.box[nid]
                x1, y1 = px + self.BOXW / 2, py + self.BOXH
                x2, y2 = cx + self.BOXW / 2, cy
                my = (y1 + y2) / 2 if y2 > y1 else y1 + 12
                self.cv.create_line(x1, y1, x1, my, x2, my, x2, y2,
                                    fill='#aab4c2', width=1.2, tags='link')
        self.cv.tag_lower('link')
        self.cv.tag_lower('bandbg')

    def _toggle_tier(self, e):
        cur = self.cv.find_withtag('current')
        lev = self.tier_item.get(cur[0]) if cur else None
        if lev is None:
            return
        self.tier_collapsed ^= {lev}
        self.relayout()

    def _toggle_node(self, e):
        cur = self.cv.find_withtag('current')
        nid = self.toggle_node.get(cur[0]) if cur else None
        if nid is None:
            return
        self.collapsed ^= {nid}
        self.relayout()

    # -- drag --
    def _press(self, e):
        cur = self.cv.find_withtag('current')
        if not cur:
            return
        nid = self.item_node.get(cur[0])
        if nid is None:
            return
        self.drag = {'nid': nid, 'x': self.cv.canvasx(e.x), 'y': self.cv.canvasy(e.y)}
        self.cv.tag_raise(f'g_{nid}')

    def _motion(self, e):
        if not self.drag:
            return
        cx, cy = self.cv.canvasx(e.x), self.cv.canvasy(e.y)
        self.cv.move(f'g_{self.drag["nid"]}', cx - self.drag['x'], cy - self.drag['y'])
        self.drag['x'], self.drag['y'] = cx, cy
        self._highlight(cx, cy)

    def _highlight(self, cx, cy):
        self.cv.delete('hl')
        tgt = self._target_at(cx, cy, self.drag['nid'])
        if tgt and tgt in self.box:
            x, y = self.box[tgt]
            self.cv.create_rectangle(x - 2, y - 2, x + self.BOXW + 2, y + self.BOXH + 2,
                                     outline='#1b7a32', width=2, tags='hl')

    def _band_at(self, cy):
        for lev, y0, y1 in self.bands:
            if y0 <= cy < y1:
                return lev
        return self.bands[-1][0] if self.bands and cy >= self.bands[-1][2] else (
               self.bands[0][0] if self.bands else None)

    def _target_at(self, cx, cy, nid):
        skip = self._descendants(nid) | {nid}
        for item in reversed(self.cv.find_overlapping(cx - 1, cy - 1, cx + 1, cy + 1)):
            t = self.item_node.get(item)
            if t and t not in skip:
                return t
        return None

    def _release(self, e):
        if not self.drag:
            return
        nid = self.drag['nid']
        cx, cy = self.cv.canvasx(e.x), self.cv.canvasy(e.y)
        self.cv.delete('hl')
        new_parent = self._target_at(cx, cy, nid)
        new_level = (self.model[new_parent]['level'] if new_parent
                     else self._band_at(cy)) or self.model[nid]['level']
        self.drag = None
        self.apply_change(nid, new_parent, new_level)

    def apply_change(self, nid, new_parent, new_level):
        """Změní nadřazenost/úroveň uzlu (testovatelné bez myši)."""
        if new_parent in (self._descendants(nid) | {nid}):
            new_parent = self.model[nid]['parent']     # zákaz cyklu
        self.model[nid]['parent'] = new_parent
        self.model[nid]['level'] = new_level
        self.relayout()

    # -- akce --
    def _changes(self):
        return {nid: v for nid, v in self.model.items() if v != self.orig.get(nid)}

    def _refresh_info(self):
        n = len(self._changes())
        self.info.config(text=(f'{n} změn k uložení' if n else 'beze změn'))

    def reset(self):
        self.model = {nid: dict(v) for nid, v in self.orig.items()}
        self.relayout()

    def save(self):
        ch = self._changes()
        if not ch:
            messagebox.showinfo('Org chart', 'Žádné změny k uložení.')
            return
        payload = {nid: {'parent_node_id': v['parent'], 'level': v['level']}
                   for nid, v in ch.items()}
        n = core.save_system_layout(self.sid, payload)
        self.orig = {nid: dict(v) for nid, v in self.model.items()}
        self.relayout()
        messagebox.showinfo('Org chart', f'Uloženo {n} změn do xlsx.')
        if self.on_saved:
            self.on_saved()


def main():
    AlmanachDesktop().mainloop()


if __name__ == '__main__':
    main()
