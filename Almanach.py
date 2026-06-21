#!/usr/bin/env python3
"""
Almanach.py — HLAVNÍ ROZCESTNÍK. Spusť tohle jediné a vyber, co chceš dělat.

Z jednoho okna:
  • dořešit flagy (osudy týmů, neúplné tabulky),
  • opravit názvy klubů (překlepy),
  • editovat soutěže (úrovně / názvy / hierarchii),
  • vytvořit balíček / .exe pro kolegu.

Spuštění (ze zdroje):  python Almanach.py
Jako .exe: data se sama rozbalí do složky vedle programu a tohle okno se otevře.
"""
import glob
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import solve_flags_gui as flags
import edit_system_gui as sysed
try:
    import kosilka
except Exception:
    kosilka = None
try:
    import viewer
except Exception:
    viewer = None
try:
    import balic
except Exception:
    balic = None


class Hub(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Almanach — nástroje')
        self.geometry('580x560')
        flags.extract_payload()                       # jako .exe: rozbal data vedle sebe
        self.data_dir = flags.find_data_dir()
        self._build()

    def _build(self):
        ttk.Label(self, text='ALMANACH', font=('TkDefaultFont', 22, 'bold')).pack(pady=(18, 0))
        ttk.Label(self, text='Vyber, co chceš dělat:', foreground='#555').pack(pady=(0, 6))
        self.dd = ttk.Label(self, text='', foreground='#777')
        self.dd.pack(pady=2)
        self._refresh_dd()

        frm = ttk.Frame(self); frm.pack(pady=12)

        def big(txt, cmd):
            ttk.Button(frm, text=txt, width=48, command=cmd).pack(pady=6, ipady=4)

        big('📋   Košilky soutěží — osud + návaznost (x-1 ↔ x+1)', self.open_kosilka)
        big('🧩   Dořešit flagy (osudy týmů, neúplné tabulky)', self.open_flags)
        big('🏷   Opravit názvy klubů (překlepy)', self.open_clubs)
        big('📄   Prohlížeč sezón (zobrazit tabulky v PDF)', self.open_viewer)
        big('🗂   Editor soutěží (úrovně / názvy / hierarchie)', self.open_sys)
        big('♻   Přegenerovat košilky z dat', self.regen_kosilka)
        if not getattr(sys, 'frozen', False) and balic is not None:
            big('📦   Vytvořit balíček / .exe pro kolegu', self.open_balic)
        ttk.Separator(frm, orient='horizontal').pack(fill='x', pady=8)
        big('📁   Změnit složku s daty', self.choose_dir)
        big('❓   Nápověda', self.help)

        ttk.Label(self, foreground='#999',
                  text='Tip: každý nástroj se otevře v samostatném okně. '
                       'Toto rozcestník nech otevřené.').pack(side='bottom', pady=8)

    def _refresh_dd(self):
        self.dd.config(text=('Data: ' + self.data_dir) if self.data_dir
                       else 'Data: — nenalezeno, klikni „Změnit složku s daty"')

    def _need_data(self):
        if not self.data_dir:
            self.choose_dir()
        return bool(self.data_dir)

    def choose_dir(self):
        d = filedialog.askdirectory(title='Vyber složku se sešity S*_FINAL.xlsx')
        if not d:
            return
        if glob.glob(os.path.join(d, 'S*_FINAL.xlsx')):
            self.data_dir = d
        elif glob.glob(os.path.join(d, 'data', 'S*_FINAL.xlsx')):
            self.data_dir = os.path.join(d, 'data')
        else:
            messagebox.showerror('Data', 'V té složce nejsou žádné S*_FINAL.xlsx.')
            return
        self._refresh_dd()

    def open_flags(self):
        if self._need_data():
            flags.FlagSolver(self, self.data_dir)

    def open_clubs(self):
        if self._need_data():
            flags.ClubEditor(self, self.data_dir)

    def open_kosilka(self):
        if self._need_data():
            flags.KosilkaEditor(self, self.data_dir)

    def regen_kosilka(self):
        if kosilka is None:
            messagebox.showinfo('Košilky', 'Modul kosilka.py není k dispozici.')
            return
        if not self._need_data():
            return
        if not messagebox.askyesno('Přegenerovat košilky',
                                   'Přepočítá KOŠILKY (osud + návaznost) ve VŠECH sezónách '
                                   'z aktuálních dat.\n\nRuční úpravy osudu/cíle v košilce se '
                                   'mohou přepsat odvozenými hodnotami. Pokračovat?'):
            return
        try:
            kosilka.build_all(self.data_dir)
            messagebox.showinfo('Košilky', 'Hotovo — košilky přegenerovány ve všech sezónách.')
        except Exception as e:
            messagebox.showerror('Košilky', f'Nepodařilo se přegenerovat:\n{e}')

    def open_viewer(self):
        if viewer is None:
            messagebox.showinfo('Prohlížeč', 'Prohlížeč není k dispozici.')
            return
        if self._need_data():
            viewer.Viewer(self, self.data_dir)

    def open_sys(self):
        if self._need_data():
            sysed.SystemEditor(self, self.data_dir)

    def open_balic(self):
        balic.Balic(self)

    def help(self):
        messagebox.showinfo('Nápověda', (
            'JAK NA TO:\n\n'
            '1) „Košilky soutěží" — HLAVNÍ nástroj. Pro každou soutěž vidíš\n'
            '   všechny týmy, jejich OSUD (setrval / postup / sestup / zánik /\n'
            '   reorganizace) a NÁVAZNOST x-1 ↔ x+1. Nahoře je seznam a pořadí\n'
            '   fází soutěže. Klikneš na buňku Osud / ← předch. / násl. → a změníš.\n'
            '2) „Dořešit flagy" — situace, kde si počítač nebyl jistý.\n'
            '3) „Opravit názvy klubů" — najdeš klub, opravíš překlep, uložíš.\n'
            '4) „Editor soutěží" — měníš úrovně, názvy, nadřazenost (pokročilé).\n'
            '5) „Přegenerovat košilky" — přepočítá košilky z dat (po větších\n'
            '   úpravách). Ruční osudy se mohou přepsat odvozenými.\n'
            '6) „Vytvořit balíček pro kolegu" — udělá jeden .exe pro kolegu.\n\n'
            'Vše se ukládá průběžně. Můžeš kdykoliv zavřít a vrátit se.'))


def main():
    Hub().mainloop()


if __name__ == '__main__':
    main()
