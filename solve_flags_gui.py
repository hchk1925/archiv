#!/usr/bin/env python3
"""
solve_flags_gui.py — Tkinter appka na dořešení oflagovaných osudů (postup/sestup
u víceFázových soutěží, které automat neuměl rozhodnout).

Samostatný soubor (potřebuje jen Python + openpyxl; tkinter je součást Pythonu).
Dej tento soubor do složky, kde máš sešity S*_FINAL.xlsx (nebo do složky, která má
podsložku data/), a spusť:

    python solve_flags_gui.py        (na Windows dvojklik na run_solve.bat)

Co umí:
  • projíždíš flagy jeden po druhém, vidíš tabulku + další fáze soutěže (kontext),
  • u sporného týmu ťukneš variantu (tlačítko) / napíšeš vlastní / Přeskočíš,
  • PRŮBĚŽNĚ se to zapisuje do xlsx a stav se ukládá (solve_progress.json),
  • můžeš kdykoliv zavřít a vrátit se — naváže tam, kde jsi skončil,
  • tlačítko „Zabalit do ZIP" vytvoří zip se všemi sešity + vysvětlujícím textem.
"""
import datetime
import glob
import json
import os
import re
import sys
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import collections
import openpyxl

NON_DATA = {'META', 'CLUBS', 'SYSTEM', 'NOTES', 'TODO', 'CHANGES', 'README'}
PLAYOFF_T = {'playoff_round', 'playoff', 'final_group', 'final_series', 'series'}
RELEG_T = {'relegation_group', 'relegation_playoff', 'relegation_series'}
CLASS_T = {'classification'}
QUAL_T = {'qualification_group', 'qualification_series', 'qualification', 'baraz'}


def _lvl(v):
    m = re.search(r'(\d+)', str(v or ''))
    return int(m.group(1)) if m else None


def _poskey(p):
    m = re.match(r'\d+', str(p) if p is not None else '')
    return int(m.group()) if m else 999


def _sibling_label(node):
    t = str(node.get('competition_type') or '')
    nm = str(node.get('name') or '').lower()
    if t in PLAYOFF_T or any(w in nm for w in
            ('play off', 'playoff', 'play-off', 'finále', 'čtvrtfinále',
             'semifinále', 'předkolo')):
        return 'play off'
    if t in RELEG_T or 'udržení' in nm or 'záchran' in nm:
        return 'o udržení'
    if t in CLASS_T or 'o umístění' in nm or re.search(r'\bo \d+\.', nm):
        return 'o umístění'
    if t in QUAL_T or 'kvalif' in nm or 'baráž' in nm or 'prolín' in nm:
        return 'prolínací' if ('baráž' in nm or 'prolín' in nm) else 'kvalifikace'
    return None


def _load_system(wb):
    ws = wb['SYSTEM']
    rows = list(ws.iter_rows(values_only=True))
    H = {c: j for j, c in enumerate(rows[0]) if c}
    nodes = {}
    for r in rows[1:]:
        nid = r[H['node_id']] if 'node_id' in H else None
        if not nid:
            continue
        nodes[nid] = {
            'node_id': nid,
            'name': r[H.get('name', -1)] if 'name' in H else '',
            'competition_type': r[H.get('competition_type', -1)] if 'competition_type' in H else '',
            'level': r[H.get('level', -1)] if 'level' in H else '',
            'parent': r[H.get('parent_node_id', -1)] if 'parent_node_id' in H else None,
            'feeds': r[H.get('feeds_into', -1)] if 'feeds_into' in H else None,
            'loser': r[H.get('feeds_into_loser', -1)] if 'feeds_into_loser' in H else None,
        }
    return nodes


def analyze(path):
    """Oflagované soutěže (víc fází, postup/sestup nešel auto-rozhodnout) + kontext."""
    wb = openpyxl.load_workbook(path, data_only=True)
    nodes = _load_system(wb)
    members = collections.defaultdict(set)
    rowsby = collections.defaultdict(list)
    for sh in wb.sheetnames:
        if sh in NON_DATA:
            continue
        rr = list(wb[sh].iter_rows(values_only=True))
        if not rr:
            continue
        H = {c: j for j, c in enumerate(rr[0]) if c}
        if 'season_fate' not in H or 'node_id' not in H or 'row_type' not in H:
            continue
        for i, r in enumerate(rr[1:], start=2):
            if r[H['row_type']] != 'T':
                continue
            nid = r[H['node_id']]
            if not nid:
                continue
            cid = r[H.get('club_id', -1)] if 'club_id' in H else None
            pos = r[H.get('pos', -1)] if 'pos' in H else None
            club = r[H.get('club_name', -1)] if 'club_name' in H else ''
            members[nid].add(cid)
            rowsby[nid].append((sh, i, pos, cid, club, r[H['season_fate']]))
    wb.close()

    def root_of(nid):
        seen = set()
        while nid in nodes and nodes[nid]['parent'] in nodes and nodes[nid]['parent'] not in seen:
            seen.add(nid); nid = nodes[nid]['parent']
        return nid
    comps = collections.defaultdict(list)
    for nid in rowsby:
        comps[root_of(nid)].append(nid)

    items = []
    for root, phase_ids in comps.items():
        tphases = [p for p in phase_ids if rowsby[p]]
        if len(tphases) < 2:
            continue
        base = max(tphases, key=lambda p: len(members[p]))
        bn = nodes.get(base, {})
        wlab = _sibling_label(nodes[bn['feeds']]) if bn.get('feeds') in nodes else None
        llab = _sibling_label(nodes[bn['loser']]) if bn.get('loser') in nodes else None
        if wlab or llab:
            continue
        dest = {}
        for s in [p for p in tphases if p != base]:
            lab = _sibling_label(nodes.get(s, {}))
            if lab:
                for cid in members[s]:
                    if cid in members[base]:
                        dest.setdefault(cid, lab)
        if dest:
            continue
        unresolved = [r for r in rowsby[base] if r[5] in ('postup', 'sestup')]
        if not unresolved:
            continue
        ordered = sorted(tphases, key=lambda p: (_lvl(nodes.get(p, {}).get('level')) or 0,
                                                 str(nodes.get(p, {}).get('name', ''))))
        phases = [{'name': nodes.get(p, {}).get('name', p),
                   'type': nodes.get(p, {}).get('competition_type', ''),
                   'rows': sorted(rowsby[p], key=lambda v: _poskey(v[2]))}
                  for p in ([base] + [p for p in ordered if p != base])]
        items.append({'comp': bn.get('name', base), 'level': bn.get('level', ''),
                      'base': sorted(rowsby[base], key=lambda v: _poskey(v[2])),
                      'unresolved': unresolved, 'phases': phases})
    return items


VARIANTS = [('play off', 'play off'), ('o udržení', 'o udržení'),
            ('o umístění', 'o umístění'), ('kvalifikace', 'kvalifikace'),
            ('prolínací', 'prolínací'), ('postup (přímý)', 'postup'),
            ('sestup (přímý)', 'sestup'), ('udržel se', 'udržel se'),
            ('setrval', 'setrval'), ('zůstal', 'zůstal')]
SKIP = '__skip__'


def find_data_dir():
    here = os.path.abspath(os.path.dirname(__file__))
    for cand in (os.path.join(here, 'data'), here, os.getcwd()):
        if glob.glob(os.path.join(cand, 'S*_FINAL.xlsx')):
            return cand
    return None


def build_queue(data_dir):
    items = []
    for path in sorted(glob.glob(os.path.join(data_dir, 'S*_FINAL.xlsx'))):
        sid = re.search(r'S(\d{4}_\d{2})', os.path.basename(path)).group(1)
        for fl in analyze(path):
            for (sh, row, pos, cid, club, fate) in fl['unresolved']:
                items.append({
                    'sid': sid, 'path': path, 'sheet': sh, 'row': row,
                    'pos': pos, 'club': club, 'fate': fate,
                    'comp': fl['comp'], 'level': fl['level'],
                    'base': fl['base'], 'phases': fl['phases'],
                    'key': f'{sid}|{sh}|{row}'})
    return items


class FlagSolver(tk.Tk):
    def __init__(self, data_dir):
        super().__init__()
        self.title('Almanach — dořešení osudů (flagy)')
        self.geometry('1180x780')
        self.data_dir = data_dir
        self.prog_path = os.path.join(data_dir, 'solve_progress.json')
        self.progress = self._load_progress()
        self.queue = build_queue(data_dir)
        self.wbcache = {}
        self.idx = 0
        self._build_ui()
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self._goto_first_pending()
        self.show()

    # -- stav --
    def _load_progress(self):
        try:
            return json.load(open(self.prog_path, encoding='utf-8'))
        except Exception:
            return {}
    def _save_progress(self):
        try:
            json.dump(self.progress, open(self.prog_path, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=0)
        except Exception:
            pass
    def _done_count(self):
        return sum(1 for v in self.progress.values() if v and v != SKIP)

    def _wb(self, path):
        if path not in self.wbcache:
            self.wbcache[path] = openpyxl.load_workbook(path)
        return self.wbcache[path]
    def _fatecol(self, wb, sheet):
        head = [c.value for c in wb[sheet][1]]
        return head.index('season_fate') + 1 if 'season_fate' in head else None

    # -- UI --
    def _build_ui(self):
        top = ttk.Frame(self); top.pack(fill='x', padx=8, pady=6)
        ttk.Label(top, text=f'Složka: {self.data_dir}', foreground='#555').pack(side='left')
        ttk.Button(top, text='Zabalit do ZIP ▸', command=self.export_zip).pack(side='right')
        self.count_lbl = ttk.Label(top, text='', font=('TkDefaultFont', 10, 'bold'))
        self.count_lbl.pack(side='right', padx=12)

        self.pbar = ttk.Progressbar(self, mode='determinate')
        self.pbar.pack(fill='x', padx=8)

        mid = ttk.Frame(self); mid.pack(fill='both', expand=True, padx=8, pady=6)
        self.title_lbl = ttk.Label(mid, text='', font=('TkDefaultFont', 13, 'bold'),
                                   wraplength=1100, justify='left')
        self.title_lbl.pack(anchor='w')

        # kompletní tabulky všech fází soutěže (fáze → týmy)
        tf = ttk.Frame(mid); tf.pack(fill='both', expand=True, pady=4)
        cols = ('pos', 'klub', 'osud')
        self.tbl = ttk.Treeview(tf, columns=cols, show='tree headings', height=15)
        self.tbl.heading('#0', text='FÁZE / SKUPINA'); self.tbl.column('#0', width=240)
        for c, w in zip(cols, (50, 330, 200)):
            self.tbl.heading(c, text=c.upper()); self.tbl.column(c, width=w, anchor='w')
        self.tbl.column('pos', anchor='center')
        ysb = ttk.Scrollbar(tf, command=self.tbl.yview); ysb.pack(side='right', fill='y')
        self.tbl.configure(yscrollcommand=ysb.set)
        self.tbl.pack(side='left', fill='both', expand=True)
        self.tbl.tag_configure('q', background='#fff6da')          # sporný (postup/sestup)
        self.tbl.tag_configure('cur', background='#ffe0a3')         # právě řešený tým
        self.tbl.tag_configure('phase', font=('TkDefaultFont', 9, 'bold'),
                               foreground='#1a3050')

        self.team_lbl = ttk.Label(mid, text='', font=('TkDefaultFont', 12, 'bold'),
                                  foreground='#b07d10')
        self.team_lbl.pack(anchor='w')

        bf = ttk.Frame(mid); bf.pack(anchor='w', pady=6)
        self._keys = '1234567890'
        for i, (label, val) in enumerate(VARIANTS):
            ttk.Button(bf, text=f'{self._keys[i]}  {label}', width=20,
                       command=lambda v=val: self.choose(v)).grid(
                           row=i // 5, column=i % 5, padx=3, pady=3, sticky='w')

        cf = ttk.Frame(mid); cf.pack(anchor='w', pady=4)
        ttk.Label(cf, text='Vlastní text:').pack(side='left')
        self.custom = ttk.Entry(cf, width=40); self.custom.pack(side='left', padx=4)
        self.custom.bind('<Return>', lambda e: self._choose_custom())
        ttk.Button(cf, text='Uložit vlastní', command=self._choose_custom).pack(side='left')
        ttk.Button(cf, text='Přeskočit (s)', command=self.skip).pack(side='left', padx=12)

        nav = ttk.Frame(mid); nav.pack(anchor='w', pady=6)
        ttk.Button(nav, text='◀ předchozí', command=lambda: self.move(-1)).pack(side='left')
        ttk.Button(nav, text='další ▶', command=lambda: self.move(1)).pack(side='left', padx=6)
        ttk.Label(nav, text='   (klávesy: 1–0 = varianta, s = přeskočit, ←/→ = listovat)',
                  foreground='#888').pack(side='left')
        self.bind('<Key>', self._key)
        self.status = ttk.Label(self, text='', relief='sunken', anchor='w')
        self.status.pack(fill='x', side='bottom')

    def _key(self, e):
        if self.focus_get() is self.custom:
            return
        ch = (e.char or '').lower()
        if ch in self._keys:
            self.choose(VARIANTS[self._keys.index(ch)][1])
        elif ch == 's':
            self.skip()
        elif e.keysym == 'Right':
            self.move(1)
        elif e.keysym == 'Left':
            self.move(-1)

    # -- navigace/zobrazení --
    def _goto_first_pending(self):
        for i, it in enumerate(self.queue):
            st = self.progress.get(it['key'])
            if not st or st == SKIP:
                self.idx = i; return
        self.idx = 0

    def show(self):
        n = len(self.queue)
        done = self._done_count()
        self.pbar['maximum'] = max(1, n); self.pbar['value'] = done
        self.count_lbl.config(text=f'{done} / {n} vyřešeno')
        if not self.queue:
            self.title_lbl.config(text='Žádné flagy — vše vyřešeno 🎉')
            return
        it = self.queue[self.idx]
        self.title_lbl.config(
            text=f"[{self.idx+1}/{n}]  {it['sid'].replace('_','/')}  ·  {it['comp']}  ({it['level']})")
        self.tbl.delete(*self.tbl.get_children())
        for ph in it['phases']:
            pid = self.tbl.insert('', 'end', text=f"{ph['name']}  [{ph['type']}]",
                                  open=True, tags=('phase',))
            for k, (sh, row, pos, cid, club, fate) in enumerate(ph['rows'], 1):
                dpos = pos if pos not in (None, '') else k
                key = f"{it['sid']}|{sh}|{row}"
                done = self.progress.get(key)
                mark = (' ✔ ' + done) if (done and done != SKIP) else (
                    '  ⟵ ?' if fate in ('postup', 'sestup') else '')
                tag = 'cur' if (sh == it['sheet'] and row == it['row']) else (
                    'q' if fate in ('postup', 'sestup') else '')
                self.tbl.insert(pid, 'end', values=(dpos, club, f'{fate or "—"}{mark}'),
                                tags=(tag,) if tag else ())
        st = self.progress.get(it['key'])
        stx = '' if not st else (f'  — už vyřešeno: {st}' if st != SKIP else '  — přeskočeno')
        pre = f"{it['pos']}. " if it['pos'] not in (None, '') else ''
        self.team_lbl.config(text=f"→  {pre}{it['club']}   (teď: {it['fate']}){stx}")
        self.custom.delete(0, 'end')

    def move(self, d):
        if self.queue:
            self.idx = (self.idx + d) % len(self.queue)
            self.show()

    def choose(self, val):
        it = self.queue[self.idx]
        wb = self._wb(it['path']); col = self._fatecol(wb, it['sheet'])
        if col:
            wb[it['sheet']].cell(row=it['row'], column=col).value = val
            wb.save(it['path'])
        self.progress[it['key']] = val
        self._save_progress()
        self.status.config(text=f"Zapsáno: {it['club']} → {val}")
        self._advance()

    def _choose_custom(self):
        v = self.custom.get().strip()
        if v:
            self.choose(v)

    def skip(self):
        it = self.queue[self.idx]
        self.progress[it['key']] = SKIP
        self._save_progress()
        self.status.config(text=f"Přeskočeno: {it['club']}")
        self._advance()

    def _advance(self):
        nxt = None
        for off in range(1, len(self.queue) + 1):
            j = (self.idx + off) % len(self.queue)
            st = self.progress.get(self.queue[j]['key'])
            if not st or st == SKIP:
                nxt = j; break
        if nxt is None:
            self.show()
            messagebox.showinfo('Hotovo', 'Všechny flagy vyřešené! Můžeš zabalit do ZIP.')
        else:
            self.idx = nxt; self.show()

    # -- export / zavření --
    def export_zip(self):
        for wb in self.wbcache.values():
            pass
        out = filedialog.asksaveasfilename(
            defaultextension='.zip',
            initialfile=f'almanach_opraveno_{datetime.date.today()}.zip',
            filetypes=[('ZIP', '*.zip')])
        if not out:
            return
        done = self._done_count()
        skipped = sum(1 for v in self.progress.values() if v == SKIP)
        readme = (
            'ALMANACH — opravené sešity\n'
            f'Vytvořeno: {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n'
            'Co je opravené (season_fate):\n'
            '• U víceFázových soutěží už postup/sestup NEvisí na základní části.\n'
            '  Základní část nese štítek, KAM tým šel: play off / o udržení /\n'
            '  o umístění / kvalifikace / prolínací.\n'
            '• Skupina o udržení: poslední = sestup, ostatní = udržel se.\n'
            '• Jednofázové soutěže (přímý postup) beze změny.\n\n'
            f'Ruční dořešení flagů (tato appka): {done} rozhodnutí'
            + (f', {skipped} přeskočeno (zatím nevyřešeno)' if skipped else '') + '.\n\n'
            'Slovník osudů: postup, sestup, udržel se, setrval, zůstal\n'
            '  + fázové štítky: play off, o udržení, o umístění, kvalifikace, prolínací.\n')
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(glob.glob(os.path.join(self.data_dir, 'S*_FINAL.xlsx'))):
                z.write(p, os.path.join('data', os.path.basename(p)))
            z.writestr('PRECTI_ME.txt', readme)
        messagebox.showinfo('ZIP', f'Hotovo:\n{out}\n\n{done} rozhodnutí, {skipped} přeskočeno.')

    def _on_close(self):
        self._save_progress()
        for wb in self.wbcache.values():
            try:
                wb.close()
            except Exception:
                pass
        self.destroy()


def main():
    data_dir = find_data_dir()
    root_probe = tk.Tk(); root_probe.withdraw()
    if not data_dir:
        data_dir = filedialog.askdirectory(title='Vyber složku se sešity S*_FINAL.xlsx')
    root_probe.destroy()
    if not data_dir or not glob.glob(os.path.join(data_dir, 'S*_FINAL.xlsx')):
        print('Nenašel jsem žádné S*_FINAL.xlsx.'); return
    FlagSolver(data_dir).mainloop()


if __name__ == '__main__':
    main()
