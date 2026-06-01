#!/usr/bin/env python3
"""
validate_almanach.py — era-aware audit datové kvality nad almanach.sqlite.

Spusť po build_db.py. Vypíše souhrn a zapíše docs/DATA_QUALITY.md.

Co kontroluje:
  1. Mistr extraligy per sezóna: META 'Mistr:' → (fallback) vítěz finále SERIES
     → (fallback) M-badge / 1. místo ZČ. Porovná s 1. místem základní části
     a označí sezóny, kde se mistr ≠ 1. ZČ (typicky moderní play-off éra).
  2. Validace tabulek dle éry:
       - éra 2-1-0 (<2002): V+R+P=GP a PTS=2·V+R
       - éra 3-2-1-0 (≥2002): W/D/L jsou ve zdroji ztrátové (5 sloupců V/VP/PP/P
         uložené do 3), proto se V+R+P=GP nevaliduje — jen se eviduje.
  3. Poškozené buňky extraligy: chybějící GA, GF=0/NULL — přesný seznam pro
     re-extrakci ze zdroje.
"""
import sqlite3, re, os, datetime

DBF = 'almanach.sqlite'
OUT = 'docs/DATA_QUALITY.md'
MODERN_FROM = 2002          # od této sezóny bodování 3-2-1-0


def year_of(sid):
    return int(sid[1:5])


def main():
    db = sqlite3.connect(DBF)
    seasons = [r[0] for r in db.execute(
        "SELECT season_id FROM seasons ORDER BY season_id")]

    champ_rows = []          # (sid, champion, source, first_zc, mismatch)
    broken = []              # (sid, pos, name, problem)
    era_stats = {'2-1-0': {'rows': 0, 'bad_wdl': 0, 'bad_pts': 0},
                 '3-2-1-0': {'rows': 0, 'lossy': 0}}

    for sid in seasons:
        note = db.execute("SELECT note FROM seasons WHERE season_id=?",
                          (sid,)).fetchone()[0] or ''
        ext = db.execute(
            "SELECT pos, club_name, GP, W, D, L, GF, GA, PTS, club_id "
            "FROM standings WHERE season_id=? AND sheet='10_liga' "
            "AND pos IS NOT NULL", (sid,)).fetchall()
        # seřaď dle pozice (číselně, kde to jde)
        def posnum(p):
            try: return int(str(p).strip())
            except Exception: return 9999
        ext_sorted = sorted(ext, key=lambda r: posnum(r[0]))

        # ── mistr ── (konec věty = '. ' následované velkým písmenem, nebo konec;
        #    nezalomí se na tečce uvnitř závorek typu '(1. playoff)')
        m = re.search(r'Mistr:\s*(.+?)(?:\.\s+[A-ZČŠŘŽÁÉ]|\.?$)', note)
        champion, source = (None, None)
        if m:
            champion, source = m.group(1).strip(), 'META'
        else:
            fin = final_winner(db, sid)
            if fin:
                champion, source = fin, 'SERIES'
            elif ext_sorted:
                # M-badge v poznámce řádku? jinak 1. místo
                champion, source = ext_sorted[0][1], '1.ZČ'
        first_zc = ext_sorted[0][1] if ext_sorted else None
        mism = bool(champion and first_zc and
                    norm(champion) != norm(first_zc))
        champ_rows.append((sid, champion, source, first_zc, mism))

        # ── validace tabulek (extraliga) ──
        modern = year_of(sid) >= MODERN_FROM
        for pos, name, gp, w, d, l, gf, ga, pts, cid in ext_sorted:
            if ga is None:
                broken.append((sid, pos, name, 'GA chybí'))
            if gf == 0:
                broken.append((sid, pos, name, 'GF=0'))
            elif gf is None:
                broken.append((sid, pos, name, 'GF chybí'))
            if modern:
                era_stats['3-2-1-0']['rows'] += 1
                if None not in (gp, w, d, l) and w + d + l != gp:
                    era_stats['3-2-1-0']['lossy'] += 1
            else:
                era_stats['2-1-0']['rows'] += 1
                if None not in (gp, w, d, l) and w + d + l != gp:
                    era_stats['2-1-0']['bad_wdl'] += 1
                if None not in (pts, w, d) and pts != 2 * w + d:
                    era_stats['2-1-0']['bad_pts'] += 1

    db.close()
    write_report(champ_rows, broken, era_stats, seasons)


def norm(s):
    s = str(s or '').lower()
    s = re.sub(r'\(.*?\)', '', s)       # zahoď anotace v závorkách ((C), (1. playoff)…)
    s = re.sub(r'\s+', '', s)
    return s


def final_winner(db, sid):
    """Zkus odvodit vítěze z poslední série SERIES (nejvyšší úroveň/finále)."""
    rows = db.execute(
        "SELECT series_id, clean_name, side, series_score, note "
        "FROM series WHERE season_id=? AND series_score IS NOT NULL", (sid,)).fetchall()
    if not rows:
        return None
    # finále = série, jejíž node/název obsahuje 'finále' nebo nejvyšší série
    best = None
    for sidx, name, side, score, note in rows:
        if not score or ':' not in str(score):
            continue
        try:
            a, b = [int(x) for x in str(score).split(':')[:2]]
        except Exception:
            continue
        # vítěz série = ten, kdo má víc; vrať jen u série označené jako finále
        if note and 'finále' in str(note).lower() and a > b:
            best = name
    return best


def write_report(champ_rows, broken, era, seasons):
    os.makedirs('docs', exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    L = [f"# Audit datové kvality — era-aware\n\n_{stamp} · generuje "
         f"`validate_almanach.py` z `almanach.sqlite`_\n"]

    L.append("## 1. Mistři extraligy a srovnání s 1. místem základní části\n")
    L.append("Mistr je primárně z META (`Mistr:`). Sloupec **≠ZČ** značí, že "
             "mistr není tým z 1. místa základní části — v play-off éře normální.\n")
    L.append("| Sezóna | Mistr | Zdroj | 1. ZČ | ≠ZČ |")
    L.append("|---|---|---|---|:--:|")
    nmis = 0
    for sid, champ, src, fz, mis in champ_rows:
        if mis:
            nmis += 1
        L.append(f"| {sid[1:]} | {champ or '—'} | {src or '—'} | "
                 f"{fz or '—'} | {'⚠' if mis else ''} |")
    L.append(f"\n_Mistr ≠ 1. ZČ u **{nmis}** sezón (play-off rozhodlo jinak)._\n")
    zc_po = [sid[1:] for sid, ch, src, fz, mis in champ_rows
             if src == '1.ZČ' and year_of(sid) >= 1985]
    if zc_po:
        L.append(f"> ⚠ **K potvrzení:** u sezón {', '.join(zc_po)} chybí v META "
                 f"explicitní `Mistr:`, mistr je odvozen z 1. místa ZČ — v "
                 f"play-off éře (≥1985/86) je nutné ověřit vítěze play-off.\n")

    L.append("## 2. Validace tabulek dle éry (extraliga)\n")
    e = era['2-1-0']
    L.append(f"**Éra 2-1-0 (<{MODERN_FROM}):** {e['rows']} řádků · "
             f"V+R+P≠GP: **{e['bad_wdl']}** · PTS≠2·V+R: **{e['bad_pts']}**")
    m = era['3-2-1-0']
    L.append(f"\n**Éra 3-2-1-0 (≥{MODERN_FROM}):** {m['rows']} řádků · "
             f"W/D/L nesedí na GP (ztrátový zdroj — 5 sl. → 3): **{m['lossy']}** "
             f"(očekávané, ne chyba)\n")

    L.append("## 3. Poškozené buňky extraligy (re-extrakce ze zdroje)\n")
    if broken:
        bys = {}
        for sid, pos, name, prob in broken:
            bys.setdefault(sid, []).append((pos, name, prob))
        L.append("| Sezóna | Řádků | Problém |")
        L.append("|---|---|---|")
        for sid in sorted(bys):
            probs = bys[sid]
            kinds = sorted({p[2] for p in probs})
            L.append(f"| {sid[1:]} | {len(probs)} | {', '.join(kinds)} |")
        L.append("")
    else:
        L.append("Žádné. ✓\n")

    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write("\n".join(L) + "\n")

    print(f"=== Audit → {OUT} ===")
    print(f"  Mistr ≠ 1.ZČ: {nmis} sezón")
    print(f"  2-1-0: {e['rows']} ř., V+R+P≠GP={e['bad_wdl']}, PTS≠2V+R={e['bad_pts']}")
    print(f"  3-2-1-0: {m['rows']} ř., ztrátových W/D/L={m['lossy']}")
    print(f"  poškozených buněk: {len(broken)}")
    if broken:
        bys = {}
        for sid, pos, name, prob in broken:
            bys.setdefault(sid, set()).add(prob)
        for sid in sorted(bys):
            print(f"    {sid[1:]}: {', '.join(sorted(bys[sid]))}")


if __name__ == '__main__':
    main()
