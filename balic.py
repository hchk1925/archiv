#!/usr/bin/env python3
"""
balic.py — „Balič": z vybraných složek vyrobí JEDEN .exe pro kolegu.

Jak to funguje:
  • Dej tento soubor do složky, kde máš solve_flags_gui.py a podsložky s daty
    (např. data, CZE1, CZE2+3+nizsi, jarda-puvodni).
  • Spusť:  python balic.py
  • Zaškrtni složky, které se mají přibalit (data je nutná — jsou v ní sešity).
  • Klikni „Vytvořit .exe pro kolegu". Vznikne  dist/Almanach.exe.
  • Kolegovi pošleš JEN ten jeden Almanach.exe.

Když kolega .exe spustí, vedle něj se SAM rozbalí přibalené složky (data + ostatní)
a rovnou se otevře Almanach. Žádný Python, žádný zip, žádný .bat.

(Potřebuje PyInstaller; když chybí, Balič nabídne instalaci.)
"""
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

SKIP_DIRS = {'build', 'dist', '__pycache__', '.git', '.idea', '.vscode'}


def base_dir():
    return os.path.abspath(os.path.dirname(__file__)) if not getattr(sys, 'frozen', False) \
        else os.path.dirname(sys.executable)


def list_folders(base):
    out = []
    for n in sorted(os.listdir(base)):
        p = os.path.join(base, n)
        if os.path.isdir(p) and n not in SKIP_DIRS and not n.startswith('.'):
            out.append(n)
    return out


def list_apps(base):
    return [n for n in sorted(os.listdir(base))
            if n.endswith('.py') and n not in ('balic.py',)]


def build_cmd(app, name, folders, console=False, sep=None):
    sep = sep or os.pathsep
    cmd = [sys.executable, '-m', 'PyInstaller', '--onefile',
           '--console' if console else '--windowed',
           '--noconfirm', '--clean', '--name', name]
    for f in folders:
        cmd += ['--add-data', f'{f}{sep}_payload/{os.path.basename(f)}']
    cmd += [app]
    return cmd


class Balic(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title('Balič — vytvoř .exe pro kolegu')
        self.geometry('820x620')
        self.base = base_dir()
        self.vars = {}
        self._build()

    def _build(self):
        top = ttk.Frame(self); top.pack(fill='x', padx=10, pady=8)
        ttk.Label(top, text='Balič — zabalí vybrané složky do jednoho .exe pro kolegu.',
                  font=('TkDefaultFont', 12, 'bold')).pack(anchor='w')
        ttk.Label(top, foreground='#555', text=f'Pracovní složka: {self.base}').pack(anchor='w')

        row = ttk.Frame(self); row.pack(fill='x', padx=10)
        ttk.Label(row, text='Program (.py):').pack(side='left')
        self.app_var = tk.StringVar()
        apps = list_apps(self.base)
        default_app = next((a for a in ('Almanach.py', 'solve_flags_gui.py') if a in apps),
                           apps[0] if apps else '')
        self.app_var.set(default_app)
        ttk.Combobox(row, textvariable=self.app_var, values=apps, width=30,
                     state='readonly').pack(side='left', padx=4)
        ttk.Label(row, text='   Název programu:').pack(side='left')
        self.name_var = tk.StringVar(value='Almanach')
        ttk.Entry(row, textvariable=self.name_var, width=18).pack(side='left', padx=4)

        box = ttk.LabelFrame(self, text='Složky k přibalení (zaškrtni)')
        box.pack(fill='both', expand=False, padx=10, pady=8)
        for f in list_folders(self.base):
            v = tk.BooleanVar(value=(f == 'data'))
            self.vars[f] = v
            has_xlsx = bool([x for x in os.listdir(os.path.join(self.base, f))
                             if x.endswith('.xlsx')]) if os.path.isdir(os.path.join(self.base, f)) else False
            txt = f + ('   (obsahuje xlsx — sešity)' if has_xlsx else '')
            ttk.Checkbutton(box, text=txt, variable=v).pack(anchor='w', padx=8, pady=1)
        if not self.vars:
            ttk.Label(box, text='(žádné podsložky — dej balic.py vedle složky data/)',
                      foreground='#a00').pack(anchor='w', padx=8)

        bar = ttk.Frame(self); bar.pack(fill='x', padx=10)
        self.build_btn = ttk.Button(bar, text='▶ Vytvořit .exe pro kolegu', command=self.build)
        self.build_btn.pack(side='left')
        ttk.Button(bar, text='Otevřít složku dist', command=self.open_dist).pack(side='left', padx=8)
        self.console_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text='Zobrazit konzoli (pro ladění – verze pro mě)',
                        variable=self.console_var).pack(side='left', padx=12)

        self.log = tk.Text(self, height=14, wrap='word', bg='#111', fg='#cfc',
                           font=('Courier', 9))
        self.log.pack(fill='both', expand=True, padx=10, pady=8)
        self._log('Připraveno. Zaškrtni složky a klikni „Vytvořit .exe pro kolegu".\n'
                  'Pozn.: build chvíli trvá (i pár minut). Hotový .exe bude v dist\\.\n')

    def _log(self, s):
        self.log.insert('end', s); self.log.see('end'); self.log.update_idletasks()

    def open_dist(self):
        d = os.path.join(self.base, 'dist')
        if os.path.isdir(d):
            if sys.platform.startswith('win'):
                os.startfile(d)  # noqa
            else:
                subprocess.run(['xdg-open', d])
        else:
            messagebox.showinfo('dist', 'Složka dist zatím neexistuje (nejdřív vytvoř .exe).')

    def _check_pyinstaller(self):
        try:
            import PyInstaller  # noqa
            return True
        except Exception:
            if messagebox.askyesno('PyInstaller', 'Chybí PyInstaller. Nainstalovat teď?'):
                self._log('Instaluji PyInstaller…\n')
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', 'openpyxl'])
                try:
                    import PyInstaller  # noqa
                    return True
                except Exception:
                    self._log('Instalace se nezdařila.\n')
            return False

    def build(self):
        app = self.app_var.get().strip()
        name = (self.name_var.get().strip() or 'Almanach')
        folders = [f for f, v in self.vars.items() if v.get()]
        if not app or not os.path.exists(os.path.join(self.base, app)):
            messagebox.showerror('Balič', 'Vyber platný program (.py).'); return
        if not any(os.path.isdir(os.path.join(self.base, f))
                   and any(x.endswith('.xlsx') for x in os.listdir(os.path.join(self.base, f)))
                   for f in folders):
            if not messagebox.askyesno('Balič', 'Žádná zaškrtnutá složka neobsahuje xlsx. '
                                                'Opravdu pokračovat?'):
                return
        if not self._check_pyinstaller():
            return
        self.build_btn.config(state='disabled')
        cmd = build_cmd(app, name, folders, console=self.console_var.get())
        self._log('\n$ ' + ' '.join(cmd) + '\n\n')
        threading.Thread(target=self._run, args=(cmd, name), daemon=True).start()

    def _run(self, cmd, name):
        try:
            p = subprocess.Popen(cmd, cwd=self.base, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in p.stdout:
                self.after(0, self._log, line)
            p.wait()
            exe = os.path.join(self.base, 'dist',
                               name + ('.exe' if sys.platform.startswith('win') else ''))
            if p.returncode == 0 and os.path.exists(exe):
                self.after(0, self._done_ok, exe)
            else:
                self.after(0, self._log, f'\n[!] Build skončil s kódem {p.returncode}.\n')
        except Exception as e:
            self.after(0, self._log, f'\n[!] Chyba: {e}\n')
        finally:
            self.after(0, lambda: self.build_btn.config(state='normal'))

    def _done_ok(self, exe):
        self._log(f'\n✔ HOTOVO:  {exe}\n   Pošli kolegovi JEN tento jeden soubor.\n')
        messagebox.showinfo('Hotovo', f'.exe je hotové:\n{exe}\n\n'
                                      'Pošli kolegovi jen tento jeden soubor. Po spuštění\n'
                                      'se mu data sama rozbalí vedle .exe.')


def main():
    root = tk.Tk(); root.withdraw()
    app = Balic(root)
    app.protocol('WM_DELETE_WINDOW', root.destroy)
    root.mainloop()


if __name__ == '__main__':
    main()
