"""
panels/club_detail.py - Detail jednoho klubu (editace clean_name, city, level, prev_club_id, ...)
"""
from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QHBoxLayout, QVBoxLayout, QLabel, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ClubDetailPanel(QWidget):
    
    EDITABLE_FIELDS = [
        ('club_id', 'Club ID', 'readonly'),
        ('clean_name', 'Clean name (sjednocený)', 'text'),
        ('raw_name', 'Raw name (z almanachu)', 'text'),
        ('sheet', 'Sheet (kraj/soutěž)', 'text'),
        ('entry_note', 'Entry note', 'text'),
        ('level', 'Level', 'combo:L10,L20,L30,L40,L100,okresní,KVAL'),
        ('district', 'District', 'text'),
        ('prev_club_id', 'Prev club ID (předchůdce)', 'text'),
        ('city', 'City (město)', 'text'),
        ('change_note', 'Change note (poznámka)', 'multiline'),
    ]
    
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.season = None
        self.cid = None
        self.fields = {}
        self.read_only = True
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header s ID a indikátorem
        self.header = QLabel('Vyber klub ze stromu →')
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        self.header.setFont(f)
        layout.addWidget(self.header)
        
        # Form s editovatelnými poli
        form_box = QGroupBox('Údaje klubu')
        form_layout = QFormLayout(form_box)
        
        for key, label, kind in self.EDITABLE_FIELDS:
            if kind == 'readonly':
                w = QLineEdit()
                w.setReadOnly(True)
                w.setStyleSheet('background:#f0f0f0;')
            elif kind == 'text':
                w = QLineEdit()
                w.editingFinished.connect(lambda k=key: self._on_field_changed(k))
            elif kind == 'multiline':
                w = QTextEdit()
                w.setMaximumHeight(120)
                w.focusOutEvent = self._make_textedit_focusout(key, w)
            elif kind.startswith('combo:'):
                w = QComboBox()
                w.setEditable(True)
                opts = kind.split(':', 1)[1].split(',')
                w.addItems([''] + opts)
                w.currentTextChanged.connect(lambda v, k=key: self._on_combo_changed(k, v))
            else:
                w = QLineEdit()
            self.fields[key] = w
            form_layout.addRow(QLabel(label), w)
        
        layout.addWidget(form_box)
        
        # Akční tlačítka
        btn_box = QGroupBox('Akce')
        btn_layout = QHBoxLayout(btn_box)
        
        self.btn_save = QPushButton('💾 Uložit změny')
        self.btn_save.clicked.connect(self._save_changes)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_delete = QPushButton('🗑 Smazat klub')
        self.btn_delete.clicked.connect(self._delete_club)
        self.btn_delete.setStyleSheet('background:#ffcccc;')
        btn_layout.addWidget(self.btn_delete)
        
        self.btn_assign_b = QPushButton('🔗 Přiřadit jako B-tým k...')
        self.btn_assign_b.clicked.connect(self._assign_b_team)
        btn_layout.addWidget(self.btn_assign_b)
        
        self.btn_make_a = QPushButton('Označit jako A-tým')
        self.btn_make_a.clicked.connect(self._make_a_team)
        btn_layout.addWidget(self.btn_make_a)
        
        # NOVE: Spojit s predchozi/nasledujici sezonou (Pavlovo upresneni 04/2026)
        self.btn_link_prev = QPushButton('🔗 Spojit s předchozí sezónou')
        self.btn_link_prev.clicked.connect(lambda: self._link_clubs('prev'))
        self.btn_link_prev.setStyleSheet('background:#cce5ff;')
        btn_layout.addWidget(self.btn_link_prev)
        
        self.btn_link_next = QPushButton('🔗 Spojit s následující sezónou')
        self.btn_link_next.clicked.connect(lambda: self._link_clubs('next'))
        self.btn_link_next.setStyleSheet('background:#cce5ff;')
        btn_layout.addWidget(self.btn_link_next)
        
        btn_layout.addStretch()
        layout.addWidget(btn_box)
        
        layout.addStretch()
        self.set_read_only(True)
    
    def _make_textedit_focusout(self, key, w):
        """Helper pro QTextEdit focusOutEvent."""
        original = w.focusOutEvent
        def handler(event):
            self._on_field_changed(key)
            QWidget.focusOutEvent(w, event)
        return handler
    
    def show_club(self, season, cid):
        self.season = season
        self.cid = cid
        club = season.get_club(cid)
        if not club:
            self.header.setText(f'❌ Klub {cid} nenalezen')
            return
        cn = club.get('clean_name', '')
        sheet = club.get('sheet', '')
        self.header.setText(f'🏒 {cn}  ({cid}, {season.season_label}, {sheet})')
        
        for key, _, kind in self.EDITABLE_FIELDS:
            w = self.fields[key]
            value = club.get(key, '') or ''
            value = str(value) if value is not None else ''
            if kind == 'multiline':
                w.blockSignals(True)
                w.setPlainText(value)
                w.blockSignals(False)
            elif kind.startswith('combo:'):
                w.blockSignals(True)
                w.setCurrentText(value)
                w.blockSignals(False)
            else:
                w.blockSignals(True)
                w.setText(value)
                w.blockSignals(False)
    
    def _get_field_value(self, key):
        kind = next((k for f, _, k in self.EDITABLE_FIELDS if f == key), None)
        w = self.fields[key]
        if kind == 'multiline':
            return w.toPlainText()
        elif kind and kind.startswith('combo:'):
            return w.currentText()
        else:
            return w.text()
    
    def _on_field_changed(self, key):
        if self.read_only or not self.cid or not self.season:
            return
        new_val = self._get_field_value(key)
        old_val = self.season.get_club(self.cid).get(key) or ''
        if str(old_val) == str(new_val):
            return
        try:
            self.season.update_club(self.cid, key, new_val)
            self.main.statusBar().showMessage(f'✓ {key}: „{old_val}" → „{new_val}" (audit)')
        except Exception as e:
            QMessageBox.critical(self, 'Chyba', str(e))
    
    def _on_combo_changed(self, key, value):
        self._on_field_changed(key)
    
    def _save_changes(self):
        """Uloží do Excelu (volá save aktuální sezóny)."""
        if not self.season:
            return
        self.main.save_current()
    
    def _delete_club(self):
        if self.read_only or not self.cid or not self.season:
            return
        reply = QMessageBox.warning(
            self, 'Smazat klub',
            f'Opravdu smazat klub {self.cid}?\n\nT-řádky tohoto klubu zůstanou (manuálně zkontroluj).',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.season.delete_club(self.cid)
            self.main._refresh_tree()
            self.main.statusBar().showMessage(f'✓ Smazáno: {self.cid}')
            self.cid = None
            self.header.setText('Klub smazán')
        except Exception as e:
            QMessageBox.critical(self, 'Chyba', str(e))
    
    def _assign_b_team(self):
        QMessageBox.information(self, 'TODO', 
            'Funkce „Přiřadit jako B-tým" — vybrat A-tým ze stejné sezóny, '
            'doplnit suffix „B" a nastavit prev_club_id na A-tým.\n\n'
            'V plánu pro v1.1.')
    
    def _make_a_team(self):
        if not self.cid or not self.season:
            return
        cn = self.fields['clean_name'].text()
        # Odstranit suffix
        import re
        new_cn = re.sub(r'\s+(II|III|B|C)$', '', cn).strip()
        if new_cn != cn:
            self.fields['clean_name'].setText(new_cn)
            self._on_field_changed('clean_name')
            self.main.statusBar().showMessage(f'A-tým: suffix odstraněn („{cn}" → „{new_cn}")')
    
    def _link_clubs(self, direction):
        """Otevre LinkClubsDialog pro manualni linkovani klubu napric sezonami.
        
        direction: 'prev' = najit predchudce v sezone X-1 (nastavi self.prev_club_id)
                   'next' = najit nastupce v sezone X+1 (nastavi nastupce.prev_club_id = self)
        """
        if self.read_only:
            QMessageBox.information(self, 'Read-only', 
                'Editace je zamknuta. Zapni Edit mode (Editace -> Edit mode).')
            return
        if not self.cid or not self.season:
            return
        if not hasattr(self.main, 'almanach') or not self.main.almanach:
            QMessageBox.warning(self, 'Almanach', 'Otevri nejprve adresar s vice sezonami.')
            return
        
        from panels.link_clubs_dialog import LinkClubsDialog
        dialog = LinkClubsDialog(self, self.main.almanach, self.season, self.cid, direction)
        if dialog.exec():
            # Po uspesnem linknuti refresh detail panelu + tree + genealogie
            target_cid = dialog.target_cid
            target_label = dialog.target_season.season_label if dialog.target_season else '?'
            
            if direction == 'prev':
                # Refreshne aktualni klub (ma novy prev_club_id)
                self.show_club(self.season, self.cid)
                self.main.statusBar().showMessage(
                    f'✓ Spojeno: {self.cid}.prev_club_id = {target_cid} ({target_label})'
                )
            else:
                # Refresh ne nutny pro aktualni klub, jen status
                self.main.statusBar().showMessage(
                    f'✓ Spojeno: {target_cid}.prev_club_id = {self.cid} ({target_label})'
                )
            
            # Refresh genealogie
            if hasattr(self.main, 'genealogy_panel'):
                self.main.genealogy_panel.show_genealogy(
                    self.main.almanach, self.season.season_label, self.cid
                )
    
    def set_read_only(self, ro):
        self.read_only = ro
        for key, _, kind in self.EDITABLE_FIELDS:
            if kind == 'readonly':
                continue
            w = self.fields[key]
            if kind == 'multiline':
                w.setReadOnly(ro)
            elif kind.startswith('combo:'):
                w.setEnabled(not ro)
            else:
                w.setReadOnly(ro)
        self.btn_save.setEnabled(not ro)
        self.btn_delete.setEnabled(not ro)
        self.btn_assign_b.setEnabled(not ro)
        self.btn_make_a.setEnabled(not ro)
        self.btn_link_prev.setEnabled(not ro)
        self.btn_link_next.setEnabled(not ro)
