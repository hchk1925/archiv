# Health report — hokejový almanach DB

_2026-05-31 08:12_

## Souhrn

- **Sezóny:** 65  (S1949_50 – S2013_14)
- **Klub-záznamů:** 32662
- **Unikátních řetězů klubů (chain_id):** 9676
- **Soutěžních uzlů:** 7390
- **Tabulkových řádků:** 23392

## Návaznost klubů (prev_club_id)

- S nastaveným prev: **25405** / 32662 (77.8 %)
- **Rozbitých linků:** 0 (odkaz na neexistující ID v předchozí sezóně)

## Řetězy klubů

- Řetězů celkem: **9676**, z toho jednosezónních: 4525
- Nejdelší řetěz: **65** sezón

| sezón | rozsah | klub (poslední název) |
|---|---|---|
| 65 | S1949_50–S2013_14 | HC Sparta Praha |
| 65 | S1949_50–S2013_14 | HC ČSOB Pojišťovna Pardubice |
| 61 | S1949_50–S2009_10 | HC Kopřivnice |
| 61 | S1953_54–S2013_14 | OLH Spartak Soběslav |
| 60 | S1954_55–S2013_14 | HC Verva Litvínov |
| 60 | S1954_55–S2013_14 | HC Lední Medvědi Pelhřimov |
| 59 | S1955_56–S2013_14 | HC Dukla Jihlava |
| 56 | S1949_50–S2004_05 | Sokol Semechnice |
| 56 | S1953_54–S2008_09 | HC ZVVZ Milevsko |
| 56 | S1953_54–S2008_09 | RI Okna Zlín |
| 56 | S1958_59–S2013_14 | HC Tambor Dvůr Králové nad Labem |
| 54 | S1960_61–S2013_14 | HC Žabonosy |

## Datová kvalita: větvení prev_club_id

- Předchůdců s **víc než 1 ne-B nástupcem** (možný chybný prev nebo split): **1584**

<details><summary>Top 20</summary>

- CLUB_S1965_66_0492 -> CLUB_S1966_67_0028 'TJ Spartak Královopolská strojírna Brno'; CLUB_S1966_67_0045 'TJ Spartak ZVÚ Hradec Králové'; CLUB_S1966_67_0064 'Spartak Praha Potrubi'; CLUB_S1966_67_0164 'Spartak Benátky'; CLUB_S1966_67_0270 'Spartak Kralovice'; CLUB_S1966_67_0425 'Spartak Pilníkov'; CLUB_S1966_67_0427 'Spartak Petříkovice'; CLUB_S1966_67_0440 'Spartak Žďár nad Sázavou'; CLUB_S1966_67_0481 'Spartak Zborovice'; CLUB_S1966_67_0538 'Spartak Bílovec'; CLUB_S1966_67_0559 'Spartak Milotice nad Bečvou'; CLUB_S1966_67_0607 'Spartak Dolné Hámre'; CLUB_S1966_67_0610 'Spartak Povážská Bystrica'
- CLUB_S1964_65_0493 -> CLUB_S1965_66_0043 'Spartak Motorlet'; CLUB_S1965_66_0188 'Spartak Sezimovo Ustí'; CLUB_S1965_66_0280 'Spartak Strašnice'; CLUB_S1965_66_0337 'Spartak Jiříkov'; CLUB_S1965_66_0376 'Spartak Žamberk'; CLUB_S1965_66_0484 'Spartak Brumov'; CLUB_S1965_66_0492 'Spartak'; CLUB_S1965_66_0566 'Spartak Příbor'; CLUB_S1965_66_0593 'Spartak Milotice'; CLUB_S1965_66_0620 'Spartak Horní Benešov (BRU)'; CLUB_S1965_66_0625 'Spartak Příbor (NJ)'
- CLUB_S1950_51_0632 -> CLUB_S1951_52_0206 'ČSSZ Liberec'; CLUB_S1951_52_0210 'RH Liberec'; CLUB_S1951_52_0226 'Sokol ČSSZ Liberec'; CLUB_S1951_52_0230 'Sokol LRI Liberec'; CLUB_S1951_52_0232 'VPS Liberec'; CLUB_S1951_52_0238 'Sokol Autorenova Liberec'
- CLUB_S1965_66_0014 -> CLUB_S1966_67_0334 'Textilana Liberec'; CLUB_S1966_67_0335 'Plastimat Liberec'; CLUB_S1966_67_0338 'ČSD Liberec'; CLUB_S1966_67_0339 'Pozemní stavby Liberec'; CLUB_S1966_67_0342 'Učitelé Liberec'; CLUB_S1966_67_0343 'Slévarna Liberec'
- CLUB_S2000_01_0011 -> CLUB_S2001_02_0012 'HC České Budějovice'; CLUB_S2001_02_0148 'Aspera České Budějovice'; CLUB_S2001_02_0151 'Sharks České Budějovice'; CLUB_S2001_02_0154 'Cheyennes České Budějovice'; CLUB_S2001_02_0159 'HoDO České Budějovice'
- CLUB_S1949_50_0086 -> CLUB_S1950_51_0103 'Sokol Voděrady – Luštěnice'; CLUB_S1950_51_0166 'Sokol Voděrady'; CLUB_S1950_51_0167 'Sokol Voděrady – Sokol Davle'; CLUB_S1950_51_0168 'Pivovar Velké Popovice – Sokol Voděrady'
- CLUB_S1951_52_0005 -> CLUB_S1952_53_0004 'DSO Dynamo Karlovy Vary'; CLUB_S1952_53_0158 'Doprava Karlovy Vary'; CLUB_S1952_53_0171 'JNV Karlovy Vary'; CLUB_S1952_53_0174 'Stavba Karlovy Vary'
- CLUB_S1951_52_0003 -> CLUB_S1952_53_0008 'DSO Slavoj České Budějovice'; CLUB_S1952_53_0099 'ZSJ Slavia České Budějovice'; CLUB_S1952_53_0100 'PDA I. České Budějovice'; CLUB_S1952_53_0104 'PDA II. České Budějovice'
- CLUB_S1954_55_0607 -> CLUB_S1955_56_0036 'Spartak Moravia Olomouc'; CLUB_S1955_56_0052 'DSO Spartak Moravia Olomouc'; CLUB_S1955_56_0630 'DA Olomouc'; CLUB_S1955_56_0652 'Dynamo Spoje Olomouc'
- CLUB_S1954_55_0472 -> CLUB_S1955_56_0530 'Motorpal Jihlava'; CLUB_S1955_56_0538 'Jiskra Jihlava'; CLUB_S1955_56_0553 'Tatran Jihlava'; CLUB_S1955_56_0583 'Motorpal Jihlava B(Jihlava město) – Jihlava okres)'
- CLUB_S1965_66_0529 -> CLUB_S1966_67_0514 'Sokol Studénka'; CLUB_S1966_67_0532 'Sokol Studénka pro příští sezonu dosazen do KP.'; CLUB_S1966_67_0537 'Tatra Studénka'; CLUB_S1966_67_0587 'Tatran Studénka (NJ)'
- CLUB_S1998_99_0035 -> CLUB_S1999_00_0043 'TJ Bohemians Praha "A"'; CLUB_S1999_00_0048 'TJ Bohemians Praha "B"'; CLUB_S1999_00_0051 'TJ Bohemians Praha A'; CLUB_S1999_00_0056 'TJ Bohemians Praha "B“'
- CLUB_S2009_10_0001 -> CLUB_S2010_11_0009 'HC Plzeň 1929'; CLUB_S2010_11_0145 'HC Plzeň 2000'; CLUB_S2010_11_0151 'HC ŽPK Plzeň'; CLUB_S2010_11_0165 'HC Panasonic Plzeň'
- CLUB_S1949_50_0018 -> CLUB_S1950_51_0008 'Slavia Pardubice'; CLUB_S1950_51_0666 'SNB Pardubice'; CLUB_S1950_51_0671 'Pardubice'
- CLUB_S1949_50_0063 -> CLUB_S1950_51_0022 'ZSJ Železničáři Louny'; CLUB_S1950_51_0911 'Veselí nad Moravou'; CLUB_S1950_51_0931 'Železničáři Bohumín'
- CLUB_S1949_50_0008 -> CLUB_S1950_51_0049 'ZSJ Zbrojovka Brno I-Židenice'; CLUB_S1950_51_0057 'ZSJ Zbrojovka Brno II-Židenice'; CLUB_S1950_51_0860 'Brno'
- CLUB_S1949_50_0054 -> CLUB_S1950_51_0060 'ZSJ Slavia Přerov'; CLUB_S1950_51_0913 'Sokol Přerov'; CLUB_S1950_51_0924 'Přerov'
- CLUB_S1949_50_0833 -> CLUB_S1950_51_0417 'Český Krumlov'; CLUB_S1950_51_0807 'Sokol Moravský Krumlov'; CLUB_S1950_51_0867 'Moravský Krumlov'
- CLUB_S1949_50_0729 -> CLUB_S1950_51_0755 'SK Jihlava'; CLUB_S1950_51_0758 'Modeta Jihlava'; CLUB_S1950_51_0769 'Jihlava'
- CLUB_S1949_50_0857 -> CLUB_S1950_51_0898 'Tatran Valašské Meziříčí'; CLUB_S1950_51_0909 'Valašské Klobouky'; CLUB_S1950_51_0910 'Valašské Meziříčí'

</details>

## Návaznost soutěží (season_fate)

- Pokrytí: **22714** / 23392 (97.1 %) tabulkových řádků
- **Nekonzistencí** (1 club_id = víc fate v sezóně): **0**
- KVAL kontaminace (fate kde má být prázdné, D30): **0**
- Rozložení fate: `setrval`=9967, `reorganizace`=5175, `postup`=2687, `setrval?`=2578, `sestup`=2057, `zanik`=243, `slouceni`=7

## Pyramida soutěží (SYSTEM)

- Uzlů s `feeds_into`: **595** / 7390
- Top-level kvalifikací **bez** feeds_into (mezera/TODO): **37**

## Integrita

- Standings řádků bez záznamu v CLUBS (orphan): **0**

## Po sezónách

| sezóna | klubů | prev % | rozbité | fate % | fate nekon. | feeds |
|---|---|---|---|---|---|---|
| 1949_50 | 925 | 0 | 0 | 99 | 0 | 21 |
