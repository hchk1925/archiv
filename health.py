#!/usr/bin/env python3
"""
health.py — Report zdraví konsolidované databáze (almanach.sqlite).

Spusť po build_db.py. Vypíše souhrn do konzole a zapíše HEALTH.md.
Slouží k průběžné kontrole při přidávání dalších sezón.
"""
import sqlite3, re, os, datetime, sys

DBF = sys.argv[1] if len(sys.argv) > 1 else 'almanach.sqlite'
OUT = 'HEALTH.md'


def main():
    if not os.path.exists(DBF):
        print(f"Chybí {DBF}. Spusť nejdřív: python3 build_db.py")
        return
    db = sqlite3.connect(DBF)
    c = db.cursor()

    def one(sql, a=()):
        return c.execute(sql, a).fetchone()[0]

    L = []                                   # markdown řádky

    def p(s=''):
        L.append(s)

    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    p(f"# Health report — hokejový almanach DB\n\n_{stamp}_\n")

    n_seasons = one("SELECT COUNT(*) FROM seasons")
    s_min = one("SELECT MIN(season_id) FROM seasons")
    s_max = one("SELECT MAX(season_id) FROM seasons")
    n_clubs = one("SELECT COUNT(*) FROM clubs")
    n_chain = one("SELECT COUNT(DISTINCT chain_id) FROM clubs")
    n_nodes = one("SELECT COUNT(*) FROM competitions")
    n_std = one("SELECT COUNT(*) FROM standings")

    p("## Souhrn\n")
    p(f"- **Sezóny:** {n_seasons}  ({s_min} – {s_max})")
    p(f"- **Klub-záznamů:** {n_clubs}")
    p(f"- **Unikátních řetězů klubů (chain_id):** {n_chain}")
    p(f"- **Soutěžních uzlů:** {n_nodes}")
    p(f"- **Tabulkových řádků:** {n_std}")

    # ── prev_club_id integrita ──
    valid = set(c.execute("SELECT season_id, club_id FROM clubs").fetchall())
    broken = []
    have_prev = 0
    for sid, cid, pcid in c.execute(
            "SELECT season_id, club_id, prev_club_id FROM clubs "
            "WHERE prev_club_id IS NOT NULL"):
        have_prev += 1
        m = re.search(r'CLUB_(S\d{4}_\d{2})_', str(pcid))
        ps = m.group(1) if m else None
        if not ps or (ps, pcid) not in valid:
            broken.append((sid, cid, pcid))
    p("\n## Návaznost klubů (prev_club_id)\n")
    p(f"- S nastaveným prev: **{have_prev}** / {n_clubs} "
      f"({100*have_prev/n_clubs:.1f} %)")
    p(f"- **Rozbitých linků:** {len(broken)} "
      f"(odkaz na neexistující ID v předchozí sezóně)")
    if broken:
        p("\n<details><summary>Rozbité linky</summary>\n")
        for sid, cid, pcid in broken:
            nm = one("SELECT clean_name FROM clubs WHERE season_id=? AND club_id=?",
                     (sid, cid))
            p(f"- `{sid}` {cid} '{nm}' -> {pcid}")
        p("\n</details>")

    # ── řetězy ──
    rows = c.execute("""SELECT chain_id, COUNT(DISTINCT season_id) ns,
        MIN(season_id), MAX(season_id) FROM clubs GROUP BY chain_id""").fetchall()
    singm = sum(1 for _, ns, *_ in rows if ns == 1)
    maxlen = max(ns for _, ns, *_ in rows)
    p("\n## Řetězy klubů\n")
    p(f"- Řetězů celkem: **{n_chain}**, z toho jednosezónních: {singm}")
    p(f"- Nejdelší řetěz: **{maxlen}** sezón")
    top = c.execute("""SELECT chain_id, COUNT(DISTINCT season_id) ns,
        MIN(season_id), MAX(season_id),
        (SELECT clean_name FROM clubs c2 WHERE c2.chain_id=c1.chain_id
         ORDER BY season_id DESC LIMIT 1)
        FROM clubs c1 GROUP BY chain_id ORDER BY ns DESC LIMIT 12""").fetchall()
    p("\n| sezón | rozsah | klub (poslední název) |")
    p("|---|---|---|")
    for ch, ns, s0, s1, nm in top:
        p(f"| {ns} | {s0}–{s1} | {nm} |")

    # ── větvení prev (datová kvalita: možný chybný prev) ──
    succ = {}
    for sid, cid, pcid, cn in c.execute(
            "SELECT season_id, club_id, prev_club_id, clean_name FROM clubs "
            "WHERE prev_club_id IS NOT NULL"):
        succ.setdefault(pcid, []).append((sid, cid, str(cn or '')))
    bsre = re.compile(r'(\bB\b|\bII+\b|\bIII\b|\bIV\b|\sC)\s*$')
    branchy = []
    for pcid, kids in succ.items():
        non_b = [k for k in kids if not bsre.search(k[2])]
        if len(non_b) > 1:
            branchy.append((pcid, non_b))
    p("\n## Datová kvalita: větvení prev_club_id\n")
    p(f"- Předchůdců s **víc než 1 ne-B nástupcem** (možný chybný prev "
      f"nebo split): **{len(branchy)}**")
    if branchy:
        p("\n<details><summary>Top 20</summary>\n")
        for pcid, kids in sorted(branchy, key=lambda x: -len(x[1]))[:20]:
            ks = "; ".join(f"{k[1]} '{k[2]}'" for k in kids)
            p(f"- {pcid} -> {ks}")
        p("\n</details>")

    # ── season_fate ──
    tot_fate = one("SELECT COUNT(*) FROM standings")
    set_fate = one("SELECT COUNT(*) FROM standings WHERE season_fate IS NOT NULL "
                   "AND season_fate <> ''")
    inconsist = c.execute("""SELECT season_id, club_id FROM standings
        WHERE season_fate IS NOT NULL AND season_fate<>''
        GROUP BY season_id, club_id
        HAVING COUNT(DISTINCT season_fate)>1""").fetchall()
    kval_bad = one("""SELECT COUNT(*) FROM standings
        WHERE season_fate IS NOT NULL AND season_fate<>''
        AND (sheet='KVAL' OR sheet LIKE 'KVAL%'
             OR level IN ('L15','L25','L35','L45'))""")
    fates = c.execute("""SELECT season_fate, COUNT(*) FROM standings
        WHERE season_fate IS NOT NULL AND season_fate<>''
        GROUP BY season_fate ORDER BY 2 DESC""").fetchall()
    p("\n## Návaznost soutěží (season_fate)\n")
    p(f"- Pokrytí: **{set_fate}** / {tot_fate} "
      f"({100*set_fate/tot_fate:.1f} %) tabulkových řádků")
    p(f"- **Nekonzistencí** (1 club_id = víc fate v sezóně): "
      f"**{len(inconsist)}**")
    p(f"- KVAL kontaminace (fate kde má být prázdné, D30): **{kval_bad}**")
    p("- Rozložení fate: " + ", ".join(f"`{f}`={n}" for f, n in fates))

    # ── pyramida ──
    feeds = one("SELECT COUNT(*) FROM competitions WHERE feeds_into IS NOT NULL")
    qual_no_feed = one("""SELECT COUNT(*) FROM competitions
        WHERE feeds_into IS NULL AND parent_node_id IS NULL
        AND (competition_type IN ('baraz','qualification_group')
             OR name LIKE 'Kvalifikace%' OR name LIKE 'Baráž%'
             OR name LIKE 'KVAL%')""")
    p("\n## Pyramida soutěží (SYSTEM)\n")
    p(f"- Uzlů s `feeds_into`: **{feeds}** / {n_nodes}")
    p(f"- Top-level kvalifikací **bez** feeds_into (mezera/TODO): "
      f"**{qual_no_feed}**")

    # ── orphan standings ──
    orph = one("""SELECT COUNT(*) FROM standings s
        WHERE NOT EXISTS(SELECT 1 FROM clubs c
        WHERE c.season_id=s.season_id AND c.club_id=s.club_id)""")
    p("\n## Integrita\n")
    p(f"- Standings řádků bez záznamu v CLUBS (orphan): **{orph}**")

    # ── per-season tabulka ──
    p("\n## Po sezónách\n")
    p("| sezóna | klubů | prev % | rozbité | fate % | fate nekon. | feeds |")
    p("|---|---|---|---|---|---|---|")
    for sid, in c.execute("SELECT season_id FROM seasons ORDER BY season_id"):
        nc = one("SELECT COUNT(*) FROM clubs WHERE season_id=?", (sid,))
        npv = one("SELECT COUNT(*) FROM clubs WHERE season_id=? "
                  "AND prev_club_id IS NOT NULL", (sid,))
        nbr = sum(1 for s, cc, pp in broken if s == sid)
        tf = one("SELECT COUNT(*) FROM standings WHERE season_id=?", (sid,))
        sf = one("SELECT COUNT(*) FROM standings WHERE season_id=? "
                 "AND season_fate IS NOT NULL AND season_fate<>''", (sid,))
        inc = sum(1 for s, cc in inconsist if s == sid)
        fe = one("SELECT COUNT(*) FROM competitions WHERE season_id=? "
                 "AND feeds_into IS NOT NULL", (sid,))
        pvp = f"{100*npv/nc:.0f}" if nc else "0"
        fap = f"{100*sf/tf:.0f}" if tf else "0"
        p(f"| {sid[1:]} | {nc} | {pvp} | {nbr} | {fap} | {inc} | {fe} |")

    db.close()
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write("\n".join(L) + "\n")

    print(f"=== Health report → {OUT} ===")
    print(f"  Sezóny: {n_seasons} ({s_min}–{s_max})")
    print(f"  Klubů: {n_clubs} | řetězů: {n_chain} | nejdelší: {maxlen} sezón")
    print(f"  prev: {have_prev} set, {len(broken)} rozbitých")
    print(f"  fate: {set_fate}/{tot_fate} ({100*set_fate/tot_fate:.1f}%), "
          f"{len(inconsist)} nekonzistencí, {kval_bad} KVAL kontaminace")
    print(f"  pyramida: {feeds}/{n_nodes} feeds_into, "
          f"{qual_no_feed} kvalifikací bez feeds")
    print(f"  větvení prev (DQ): {len(branchy)} | orphan standings: {orph}")


if __name__ == '__main__':
    main()
