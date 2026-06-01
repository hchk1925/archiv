"""
panels/link_clubs_dialog.py - Dialog pro spojeni klubu napric sezonami

Pavlovo upresneni 04/2026: Manualni linkovaci nastroj.
Workflow: vyber zdrojovy klub (sezona X) -> tlacitko "Spojit s predchozi/nasledujici sezonou"
-> dialog ukaze kandidaty v cilove sezone -> potvrdi se -> nastavi se prev_club_id.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox, QComboBox,
    QGroupBox, QFormLayout, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import re


class LinkClubsDialog(QDialog):
    """
    Modalni dialog: vyber kandidata v cilove sezone pro link.
    
    Args:
        almanach: Almanach instance
        source_season: Season instance (zdroj)
        source_cid: cid klubu, ktery linkujeme
        direction: 'prev' (zdroj -> najit predchudce v X-1) 
                   nebo 'next' (najit nastupce v X+1, kde nastavime prev=zdroj)
    """
    
    def __init__(self, parent, almanach, source_season, source_cid, direction='prev'):
        super().__init__(parent)
        self.almanach = almanach
        self.source_season = source_season
        self.source_cid = source_cid
        self.source_club = source_season.get_club(source_cid)
        self.direction = direction
        self.target_season = None
        self.target_cid = None
        
        self._init_target_season()
        self._setup_ui()
        self._load_candidates()
    
    def _init_target_season(self):
        """Najde cilovou sezonu (predchozi/nasledujici)."""
        all_seasons = sorted(self.almanach.get_all_seasons())
        try:
            idx = all_seasons.index(self.source_season.season_label)
        except ValueError:
            return
        
        if self.direction == 'prev' and idx > 0:
            target_label = all_seasons[idx - 1]
        elif self.direction == 'next' and idx < len(all_seasons) - 1:
            target_label = all_seasons[idx + 1]
        else:
            return
        
        self.target_season = self.almanach.get_season(target_label)
    
    def _setup_ui(self):
        self.setWindowTitle('🔗 Spojit kluby napříč sezónami')
        self.resize(900, 600)
        layout = QVBoxLayout(self)
        
        # Header info
        src_cn = self.source_club.get('clean_name', '?')
        src_sh = self.source_club.get('sheet', '?')
        src_city = self.source_club.get('city', '?')
        src_lv = self.source_club.get('level', '?')
        
        if self.direction == 'prev':
            arrow_text = f"  ← najít předchůdce v "
        else:
            arrow_text = f"  → najít nástupce v "
        
        if self.target_season:
            target_label = self.target_season.season_label
        else:
            target_label = "(žádná sezóna k dispozici)"
        
        info_box = QGroupBox('Zdrojový klub')
        info_layout = QFormLayout(info_box)
        info_layout.addRow('Sezóna:', QLabel(self.source_season.season_label))
        info_layout.addRow('Klub:', QLabel(f'<b>{src_cn}</b>'))
        info_layout.addRow('cid:', QLabel(self.source_cid))
        info_layout.addRow('Sheet:', QLabel(f'{src_sh} (lv={src_lv})'))
        info_layout.addRow('city:', QLabel(src_city or '(prázdné)'))
        layout.addWidget(info_box)
        
        # Direction info
        dir_label = QLabel(f'{arrow_text}<b>{target_label}</b>')
        f = QFont()
        f.setPointSize(12)
        dir_label.setFont(f)
        dir_label.setStyleSheet('padding:6px; background:#e8f4f8;')
        layout.addWidget(dir_label)
        
        if not self.target_season:
            layout.addWidget(QLabel('❌ Cílová sezóna neexistuje. Otevři vícesezónní adresář.'))
            close_btn = QPushButton('Zavřít')
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return
        
        # Filtr
        filter_box = QGroupBox('Filtry kandidátů')
        fl = QHBoxLayout(filter_box)
        
        fl.addWidget(QLabel('🔎 Hledat:'))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('část jména, města...')
        self.search_edit.textChanged.connect(self._load_candidates)
        fl.addWidget(self.search_edit, 2)
        
        # Default: predvyplnit jadro nazvu z source
        suggested_query = self._extract_core_name(src_cn, src_city)
        if suggested_query:
            self.search_edit.setText(suggested_query)
        
        self.same_city_check = QCheckBox('Stejné city')
        self.same_city_check.setChecked(bool(src_city))
        self.same_city_check.stateChanged.connect(self._load_candidates)
        fl.addWidget(self.same_city_check)
        
        self.same_sheet_check = QCheckBox('Podobný sheet')
        self.same_sheet_check.setChecked(False)
        self.same_sheet_check.stateChanged.connect(self._load_candidates)
        fl.addWidget(self.same_sheet_check)
        
        layout.addWidget(filter_box)
        
        # Tree kandidatu
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['cid', 'clean_name', 'sheet', 'level', 'city', 'prev'])
        self.tree.itemDoubleClicked.connect(self._confirm_link)
        for i in range(6):
            self.tree.header().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tree, 1)
        
        # Tlacitka
        btn_box = QHBoxLayout()
        self.btn_link = QPushButton('🔗 Spojit (nastaví prev_club_id)')
        self.btn_link.clicked.connect(self._confirm_link)
        self.btn_link.setStyleSheet('background:#90c890; font-weight:bold; padding:6px;')
        btn_box.addWidget(self.btn_link)
        
        cancel_btn = QPushButton('Zrušit')
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)
        
        layout.addLayout(btn_box)
        
        # Tip
        tip = QLabel(
            '💡 Dvojklik nebo tlačítko 🔗 spojí kluby. '
            f'Nastavení: <code>{self.source_cid}.prev_club_id</code> = '
            'cid vybraného klubu z cílové sezóny.' if self.direction == 'prev' else
            '💡 Dvojklik nebo tlačítko 🔗 spojí kluby. '
            f'Nastavení: <code>vybraný_klub.prev_club_id = {self.source_cid}</code>.'
        )
        tip.setStyleSheet('color:#666;font-style:italic;padding:4px;')
        tip.setWordWrap(True)
        layout.addWidget(tip)
    
    def _extract_core_name(self, clean_name, city):
        """Extrahuje jadro nazvu pro vyhledavani (D44 - identita = mesto + jadro nazvu)."""
        if not clean_name:
            return ''
        # Odstranit zname prefixy
        prefixes = ['TJ ', 'DSO ', 'DŠO ', 'Sokol ', 'Spartak ', 'Slavoj ', 
                    'Tatran ', 'Dynamo ', 'Slovan ', 'Baník ', 'Banik ',
                    'Lokomotiva ', 'Lokomotíva ', 'RH ', 'DA ', 'Jiskra ',
                    'Slavia ', 'Slávia ', 'Iskra ', 'Dukla ', 'VTJ ',
                    'ZSJ ', 'Sigma ', 'HC ', 'ASD ']
        core = clean_name
        for p in prefixes:
            if core.startswith(p):
                core = core[len(p):]
                break
        # Odstranit suffixy A/B/C/II
        core = re.sub(r'\s+(II|III|IV|V|VI|B|C|D)$', '', core).strip()
        # Pokud tam je city, vyber radej city (presnejsi pro identitu)
        if city and len(city) > 2 and city in core:
            return city
        # Jinak prvni vyznamne slovo
        return core
    
    def _load_candidates(self):
        """Naplni tree kandidaty z cilove sezony s aplikaci filtru."""
        if not self.target_season:
            return
        
        self.tree.clear()
        query = self.search_edit.text().strip().lower()
        same_city = self.same_city_check.isChecked()
        same_sheet = self.same_sheet_check.isChecked()
        
        src_city = (self.source_club.get('city') or '').strip().lower()
        src_sheet = (self.source_club.get('sheet') or '').strip()
        
        # Sber kandidatu
        candidates = []
        for cid, club in self.target_season.clubs.items():
            cn = (club.get('clean_name') or '').lower()
            city = (club.get('city') or '').lower()
            sh = (club.get('sheet') or '')
            
            # Filtr: query
            if query and query not in cn and query not in city:
                continue
            
            # Filtr: same city
            if same_city and src_city:
                if city != src_city:
                    continue
            
            # Filtr: similar sheet (top-level shoda - 30/40 + nazev)
            if same_sheet and src_sheet:
                # Pomer shody (nepresne)
                if not (sh == src_sheet or 
                        (sh and src_sheet and sh.split('_')[-1] == src_sheet.split('_')[-1])):
                    continue
            
            candidates.append((cid, club))
        
        # Razeni: nejprve presna shoda jadra, pak abecedne
        src_core = self._extract_core_name(
            self.source_club.get('clean_name', ''), 
            self.source_club.get('city', '')
        ).lower()
        
        def sort_key(item):
            cid, club = item
            cn = (club.get('clean_name') or '').lower()
            score = 0
            if src_core and src_core in cn:
                score = -10  # presna shoda nahoru
            return (score, cn)
        
        candidates.sort(key=sort_key)
        
        # Naplnit tree
        for cid, club in candidates[:200]:  # max 200
            item = QTreeWidgetItem([
                cid,
                str(club.get('clean_name') or ''),
                str(club.get('sheet') or ''),
                str(club.get('level') or ''),
                str(club.get('city') or ''),
                str(club.get('prev_club_id') or ''),
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, cid)
            self.tree.addTopLevelItem(item)
        
        n = self.tree.topLevelItemCount()
        self.btn_link.setText(f'🔗 Spojit ({n} kandidátů)')
    
    def _confirm_link(self):
        """Potvrdi link akci."""
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.warning(self, 'Vyber klub', 'Vyber kandidáta v seznamu.')
            return
        
        target_cid = items[0].data(0, Qt.ItemDataRole.UserRole)
        target_club = self.target_season.get_club(target_cid)
        if not target_club:
            QMessageBox.critical(self, 'Chyba', f'Klub {target_cid} nenalezen v cílové sezóně.')
            return
        
        # Potvrzeni
        if self.direction == 'prev':
            # Source.prev = target
            change_text = (f'{self.source_season.season_label} {self.source_cid} '
                           f'(<b>{self.source_club.get("clean_name")}</b>)\n'
                           f'  prev_club_id: <b>{target_cid}</b> '
                           f'({self.target_season.season_label} '
                           f'{target_club.get("clean_name")})')
        else:
            # Target.prev = source
            change_text = (f'{self.target_season.season_label} {target_cid} '
                           f'(<b>{target_club.get("clean_name")}</b>)\n'
                           f'  prev_club_id: <b>{self.source_cid}</b> '
                           f'({self.source_season.season_label} '
                           f'{self.source_club.get("clean_name")})')
        
        reply = QMessageBox.question(
            self, 'Potvrdit spojení',
            f'Spojit kluby?\n\n{change_text}',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Provedeni
        try:
            if self.direction == 'prev':
                self.source_season.update_club(self.source_cid, 'prev_club_id', target_cid)
            else:
                self.target_season.update_club(target_cid, 'prev_club_id', self.source_cid)
            
            self.target_cid = target_cid
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Chyba', f'Spojení selhalo: {e}')
