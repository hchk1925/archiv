#!/usr/bin/env python3
"""
fix_club_notes_in_block_name.py — Oprava parser-artefaktu, kdy se poznámka
o klubu (např. "HC Mladá Boleslav B po skončení soutěže ukončila činnost")
dostala do block_name H-řádku jako kdyby to byla další soutěž.

Co dělá pro každý nalezený H-řádek:
  1) Rozparsuje block_name (oddělovač " / ")
  2) Najde segment popisující osud klubu (klubové jméno + sloveso)
  3) Vytáhne ho a uloží:
     - do listu NOTES sezóny (s odkazem na node_id)
     - do change_note odpovídajícího klubu v CLUBS (TBD flag)
  4) Zbylé segmenty složí zpět do block_name
  5) Pokud nezbude smysluplný heading → H-řádek smaže
"""
import openpyxl, glob, re, os, sys
from collections import defaultdict

DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
NON = {'NOTES', 'SYSTEM', 'SERIES', 'CLUBS', 'META', 'PYRAMIDA', 'TODO'}

# slovesa/fráze indikující osud klubu (case insensitive)
FATE_VERBS = [
    r'po skončení', r'ukončil[aoy]?\s+(činnost|hraní|soutěž)',
    r'zanikl[aoy]?', r'nevstoupil[aoy]?', r'neúčast', r'stáhl[aoy]?\s+se',
    r'vyřazen[aoy]?', r'diskval', r'odstoupil[aoy]?', r'nedohrá[la]',
    r'odhlášen[aoy]?', r'nepostoupil[aoy]?', r'kontumace',
]
VERB_RE = re.compile('|'.join(FATE_VERBS), re.I)

# segment je "noteful" pokud obsahuje sloveso AND nezačíná čistě konkurenčním
# klíčovým slovem
COMP_WORDS = re.compile(r'^(skupin\w*|finále|finál\w*|kvalifikace|baráž|'
                        r'\w+\.?\s*třída|\w+\.?\s*liga|krajský přebor|'
                        r'krajská soutěž|městská soutěž|obvodní|nadstavba|'
                        r'finálová\s+\w+|II\.?\s*třída|I\.?\s*[AB]?\s*třída|'
                        r'okresní\s+\w+|playoff|play\s*off|čtvrtfinále|'
                        r'semifinále)\s*$', re.I)


def hidx(row0):
    return {h: i for i, h in enumerate(row0) if h is not None}


def is_note_segment(s):
    s = s.strip()
    if not s:
        return False
    if COMP_WORDS.match(s):
        return False
    return bool(VERB_RE.search(s))


def extract_club_name(note_segment):
    """Z 'HC Mladá Boleslav B po skončení soutěže ukončila činnost'
    vrátí 'HC Mladá Boleslav B'."""
    s = note_segment.strip()
    # odstranit " — " a všechno za, nebo VERB_RE match a všechno za
    s = re.sub(r'\s+[—–-]\s+.*$', '', s)
    m = VERB_RE.search(s)
    if m:
        s = s[:m.start()].strip()
    # odstranit závěrečné "B", "II" suffixy už NE — to je část jména
    return s


ORG_PFX = re.compile(
    r'^(TJ|HC|VTJ|ASD|ZTJ|DSO|DŠO|DSJ|ZSJ|Sokol|SK|AC|AFK|SKP|KLH|KS|BK|HO|RH|ČH|VSJ|PDA|DA|VŠ)\.?\s+',
    re.I)


def _normalize_name(s):
    s = re.sub(r'\s+', ' ', str(s or '').strip().lower())
    s = s.replace('"', '').replace('„', '').replace('"', '')
    # odstranit org. prefixy (i opakovaně: "TJ HC X" → "X")
    prev = None
    while prev != s:
        prev = s
        s = ORG_PFX.sub('', s).strip()
    return s


def _has_b_suffix(s):
    return bool(re.search(r'\b(b|ii|iii|iv)\b\s*$', s.strip()))


def find_club_id(clubs_idx, sheet, club_name):
    """Najdi club_id; respektuje B/II/III suffix (A-tým ≠ B-tým)."""
    target = _normalize_name(club_name)
    target_is_b = _has_b_suffix(target)
    # přesná shoda
    for cid, info in clubs_idx.items():
        if _normalize_name(info['clean_name']) == target:
            return cid
    # kandidáti: clean_name obsahuje target jako celý outřez (slovní hranice)
    matches = []
    for cid, info in clubs_idx.items():
        nm = _normalize_name(info['clean_name'])
        nm_is_b = _has_b_suffix(nm)
        # B-target sedí JEN s B-kandidátem; A-target jen s A-kandidátem
        if target_is_b != nm_is_b:
            continue
        if target in nm or nm in target:
            matches.append(cid)
    if len(matches) == 1:
        return matches[0]
    # filtr dle sheet
    if sheet:
        same = [c for c in matches if clubs_idx[c].get('sheet') == sheet]
        if len(same) == 1:
            return same[0]
    # poslední tie-break: nejkratší rozdíl délky
    if matches:
        matches.sort(key=lambda c: abs(len(_normalize_name(clubs_idx[c]['clean_name'])) - len(target)))
        return matches[0]
    return None


def process_workbook(path, season):
    wb = openpyxl.load_workbook(path)
    if 'CLUBS' not in wb.sheetnames:
        wb.close(); return 0, 0, 0
    # CLUBS index
    ws = wb['CLUBS']
    rows_clubs = list(ws.iter_rows())
    CH = hidx([c.value for c in rows_clubs[0]])
    clubs_idx = {}
    for row in rows_clubs[1:]:
        cid = row[CH['club_id']].value
        if not cid: continue
        clubs_idx[cid] = {
            'clean_name': row[CH['clean_name']].value,
            'sheet': row[CH.get('sheet', -1)].value if 'sheet' in CH else None,
            'row': row,
        }
    cni = CH.get('change_note')

    # NOTES helper
    notes_ws = wb['NOTES'] if 'NOTES' in wb.sheetnames else None
    if notes_ws:
        notes_rows = list(notes_ws.iter_rows(values_only=True))
        NH = hidx(notes_rows[0]) if notes_rows else {}

    notes_added = 0
    extracted = 0
    rows_removed = 0
    pending_notes = []                 # (node_id, sheet, text)

    for shn in wb.sheetnames:
        if shn in NON: continue
        sws = wb[shn]
        srows = list(sws.iter_rows())
        if not srows: continue
        SH = hidx([c.value for c in srows[0]])
        if 'row_type' not in SH or 'block_name' not in SH: continue
        rti, bni = SH['row_type'], SH['block_name']
        nidi = SH.get('node_id')
        to_delete = []
        for r_idx, row in enumerate(srows[1:], start=2):
            if row[rti].value != 'H': continue
            bn = str(row[bni].value or '')
            if not VERB_RE.search(bn): continue
            # split podle " / "
            segs = [s.strip() for s in re.split(r'\s*/\s*', bn) if s.strip()]
            kept = []
            for seg in segs:
                if is_note_segment(seg):
                    # vytáhni jako poznámku
                    club_name = extract_club_name(seg)
                    cid = find_club_id(clubs_idx, shn, club_name) if club_name else None
                    node_id = row[nidi].value if nidi is not None else None
                    pending_notes.append((node_id, shn, seg, cid, club_name))
                    extracted += 1
                else:
                    kept.append(seg)
            new_bn = ' / '.join(kept)
            if new_bn != bn:
                if not kept:
                    # nezbylo nic → smaž H-řádek
                    to_delete.append(r_idx)
                else:
                    row[bni].value = new_bn
        for i in sorted(to_delete, reverse=True):
            sws.delete_rows(i, 1)
            rows_removed += 1

    # Zapis poznámky do NOTES + change_note
    if pending_notes and notes_ws:
        # rozšiř NOTES schema na 5 sloupců pokud nemá
        notes_rows = list(notes_ws.iter_rows(values_only=True))
        hdr = list(notes_rows[0]) if notes_rows else ['node_id', 'sheet', 'note_text', 'source_type']
        idx = hidx(hdr)
        ncols = len(hdr)
        for node_id, sh, seg, cid, club_name in pending_notes:
            row_vals = [None] * ncols
            if 'node_id' in idx: row_vals[idx['node_id']] = node_id
            if 'sheet' in idx: row_vals[idx['sheet']] = sh
            if 'note_text' in idx:
                row_vals[idx['note_text']] = (
                    f"[club-fate] {seg}" + (f" (club_id: {cid})" if cid else ''))
            if 'source_type' in idx: row_vals[idx['source_type']] = 'club-note-extracted'
            notes_ws.append(row_vals)
            notes_added += 1
            # do CLUBS.change_note
            if cid and cni is not None:
                old = clubs_idx[cid]['row'][cni].value
                tag = f"TBD: extrahováno z block_name: '{seg}' [fix_club_notes_in_block_name]"
                clubs_idx[cid]['row'][cni].value = (str(old) + ' || ' + tag) if old else tag

    if pending_notes or rows_removed:
        wb.save(path)
    wb.close()
    return extracted, notes_added, rows_removed


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'S*_FINAL.xlsx')))
    tot_ext = tot_notes = tot_rem = 0
    for path in files:
        sid = re.search(r'S(\d{4}_\d{2})', path).group(1)
        ext, notes, rem = process_workbook(path, sid)
        if ext or rem:
            print(f"  ✓ {sid}: extrahováno={ext} NOTES={notes} H-řádků smazáno={rem}")
        tot_ext += ext; tot_notes += notes; tot_rem += rem
    print(f"\n=== SOUHRN ===")
    print(f"  Extrahovaných poznámek o klubech: {tot_ext}")
    print(f"  Přidáno do listu NOTES:           {tot_notes}")
    print(f"  Smazaných H-řádků (prázdných):    {tot_rem}")


if __name__ == '__main__':
    main()
