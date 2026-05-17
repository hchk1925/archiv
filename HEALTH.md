# Health report — hokejový almanach DB

_2026-05-17 13:48_

## Souhrn

- **Sezóny:** 65  (S1949_50 – S2013_14)
- **Klub-záznamů:** 32686
- **Unikátních řetězů klubů (chain_id):** 9713
- **Soutěžních uzlů:** 7390
- **Tabulkových řádků:** 23442

## Návaznost klubů (prev_club_id)

- S nastaveným prev: **25503** / 32686 (78.0 %)
- **Rozbitých linků:** 20 (odkaz na neexistující ID v předchozí sezóně)

<details><summary>Rozbité linky</summary>

- `S1950_51` CLUB_S1950_51_0207 'Sokol Poříčí nad Sázavou' -> CLUB_S1949_50_0937
- `S1954_55` CLUB_S1954_55_0238 'Plzeň B – Líně 4:3' -> CLUB_S1953_54_0185
- `S1954_55` CLUB_S1954_55_0420 'DA Motor Pardubice' -> CLUB_S1953_54_0019
- `S1955_56` CLUB_S1955_56_0012 'Baník Kladno' -> CLUB_S1954_55_0041
- `S1956_57` CLUB_S1956_57_0048 'TJ Sokol Okříšky' -> CLUB_S1955_56_0529
- `S1957_58` CLUB_S1957_58_0057 'Sokol Prštice' -> CLUB_S1956_57_0060
- `S1960_61` CLUB_S1960_61_0577 'Sokol Hnojice' -> CLUB_S1959_60_0593
- `S1963_64` CLUB_S1963_64_0639 'Sokol Bohuňovice' -> CLUB_S1962_63_0672
- `S1964_65` CLUB_S1964_65_0002 'Sparta ČKD Praha' -> CLUB_S1963_64_0062
- `S1964_65` CLUB_S1964_65_0041 'TJ Gottwaldov B' -> CLUB_S1963_64_0546
- `S1964_65` CLUB_S1964_65_0056 'Bohemians ČKD Praha' -> CLUB_S1963_64_0062
- `S1964_65` CLUB_S1964_65_0093 'Sparta Podluhy' -> CLUB_S1963_64_0085
- `S1964_65` CLUB_S1964_65_0508 'Slatina B' -> CLUB_S1963_64_0762
- `S1973_74` CLUB_S1973_74_0064 'TJ Spartak Lada Soběslav' -> CLUB_S1972_73_0117
- `S1976_77` CLUB_S1976_77_0073 'TJ Slavoj Český Krumlov' -> CLUB_S1975_76_0103
- `S1983_84` CLUB_S1983_84_0031 'VTJ Topoľčany' -> CLUB_S1982_83_0051
- `S1984_85` CLUB_S1984_85_0321 'Lázně Bělohrad' -> CLUB_S1983_84_0280
- `S2010_11` CLUB_S2010_11_0233 'HC Šternberk (OLO)' -> CLUB_S2009_10_0185
- `S2010_11` CLUB_S2010_11_0241 'HC Grewis Plumov (OLO)' -> CLUB_S2009_10_0185
- `S2013_14` CLUB_S2013_14_0019 'BK Mladá Boleslav' -> CLUB_S2012_13_0017

</details>

## Řetězy klubů

- Řetězů celkem: **9713**, z toho jednosezónních: 4550
- Nejdelší řetěz: **65** sezón

| sezón | rozsah | klub (poslední název) |
|---|---|---|
| 65 | S1949_50–S2013_14 | HC ČSOB Pojišťovna Pardubice |
| 61 | S1949_50–S2009_10 | HC Kopřivnice |
| 60 | S1954_55–S2013_14 | HC Verva Litvínov |
| 60 | S1954_55–S2013_14 | HC Lední Medvědi Pelhřimov |
| 59 | S1955_56–S2013_14 | HC Dukla Jihlava |
| 56 | S1949_50–S2004_05 | Sokol Semechnice |
| 56 | S1953_54–S2008_09 | HC ZVVZ Milevsko |
| 56 | S1953_54–S2008_09 | RI Okna Zlín |
| 56 | S1958_59–S2013_14 | HC Tambor Dvůr Králové nad Labem |
| 54 | S1960_61–S2013_14 | HC Žabonosy |
| 53 | S1949_50–S2001_02 | SHC Vajgar Jindřichův Hradec |
| 53 | S1961_62–S2013_14 | HC Klášterec nad Ohří |

## Datová kvalita: větvení prev_club_id

- Předchůdců s **víc než 1 ne-B nástupcem** (možný chybný prev nebo split): **1620**

<details><summary>Top 20</summary>

- CLUB_S1965_66_0492 -> CLUB_S1966_67_0028 'TJ Spartak Královopolská strojírna Brno'; CLUB_S1966_67_0045 'TJ Spartak ZVÚ Hradec Králové'; CLUB_S1966_67_0064 'Spartak Praha Potrubi'; CLUB_S1966_67_0164 'Spartak Benátky'; CLUB_S1966_67_0270 'Spartak Kralovice'; CLUB_S1966_67_0425 'Spartak Pilníkov'; CLUB_S1966_67_0427 'Spartak Petříkovice'; CLUB_S1966_67_0440 'Spartak Žďár nad Sázavou'; CLUB_S1966_67_0481 'Spartak Zborovice'; CLUB_S1966_67_0538 'Spartak Bílovec'; CLUB_S1966_67_0559 'Spartak Milotice nad Bečvou'; CLUB_S1966_67_0607 'Spartak Dolné Hámre'; CLUB_S1966_67_0610 'Spartak Povážská Bystrica'
- CLUB_S1964_65_0493 -> CLUB_S1965_66_0043 'Spartak Motorlet'; CLUB_S1965_66_0188 'Spartak Sezimovo Ustí'; CLUB_S1965_66_0280 'Spartak Strašnice'; CLUB_S1965_66_0337 'Spartak Jiříkov'; CLUB_S1965_66_0376 'Spartak Žamberk'; CLUB_S1965_66_0484 'Spartak Brumov'; CLUB_S1965_66_0492 'Spartak'; CLUB_S1965_66_0566 'Spartak Příbor'; CLUB_S1965_66_0593 'Spartak Milotice'; CLUB_S1965_66_0620 'Spartak Horní Benešov (BRU)'; CLUB_S1965_66_0625 'Spartak Příbor (NJ)'
- CLUB_S1950_51_0632 -> CLUB_S1951_52_0206 'ČSSZ Liberec'; CLUB_S1951_52_0210 'RH Liberec'; CLUB_S1951_52_0226 'Sokol ČSSZ Liberec'; CLUB_S1951_52_0230 'Sokol LRI Liberec'; CLUB_S1951_52_0232 'VPS Liberec'; CLUB_S1951_52_0238 'Sokol Autorenova Liberec'
- CLUB_S1965_66_0014 -> CLUB_S1966_67_0334 'Textilana Liberec'; CLUB_S1966_67_0335 'Plastimat Liberec'; CLUB_S1966_67_0338 'ČSD Liberec'; CLUB_S1966_67_0339 'Pozemní stavby Liberec'; CLUB_S1966_67_0342 'Učitelé Liberec'; CLUB_S1966_67_0343 'Slévarna Liberec'
- CLUB_S1984_85_0264 -> CLUB_S1985_86_0266 'Nářadí Česká Lípa'; CLUB_S1985_86_0268 'PS STAZ Česká Lípa'; CLUB_S1985_86_0273 'Akuma Česká Lípa'; CLUB_S1985_86_0276 'ČSAD Česká Lípa'; CLUB_S1985_86_0278 'ŽOS Česká Lípa'; CLUB_S1985_86_0280 'OÚNZ Česká Lípa'
- CLUB_S1952_53_0008 -> CLUB_S1953_54_0014 'DSO Slavoj České Budějovice'; CLUB_S1953_54_0132 'DSO Slavoj České Budějovice "B"'; CLUB_S1953_54_0134 'DSO Dynamo České Budějovice'; CLUB_S1953_54_0137 'PDA České Budějovice'; CLUB_S1953_54_0142 'RH České Budějovice'
- CLUB_S1966_67_0013 -> CLUB_S1967_68_0011 'TJ Motor České Budějovice'; CLUB_S1967_68_0028 'TJ Slezan OSP Opava'; CLUB_S1967_68_0043 'Motor České Budějovice'; CLUB_S1967_68_0206 'Dukla České Budějovice'; CLUB_S1967_68_0212 'Stadion České Budějovice'
- CLUB_S1972_73_0018 -> CLUB_S1973_74_0017 'TJ Slovan NV Ústí nad Labem'; CLUB_S1973_74_0369 'Spoje Ústí nad Labem'; CLUB_S1973_74_0372 'Chemička Ústí nad Labem'; CLUB_S1973_74_0374 'SČA Ústí nad Labem'; CLUB_S1973_74_0375 'KPÚ Ústí nad Labem'
- CLUB_S2000_01_0003 -> CLUB_S2001_02_0003 'HC IPB Pojišťovna Pardubice'; CLUB_S2001_02_0265 'HC Panteři Pardubice'; CLUB_S2001_02_0266 'HC Pardubice'; CLUB_S2001_02_0268 'HC AMAT Pardubice'; CLUB_S2001_02_0277 'HC Severka Pardubice'
- CLUB_S2000_01_0011 -> CLUB_S2001_02_0012 'HC České Budějovice'; CLUB_S2001_02_0148 'Aspera České Budějovice'; CLUB_S2001_02_0151 'Sharks České Budějovice'; CLUB_S2001_02_0154 'Cheyennes České Budějovice'; CLUB_S2001_02_0159 'HoDO České Budějovice'
- CLUB_S1949_50_0086 -> CLUB_S1950_51_0103 'Sokol Voděrady – Luštěnice'; CLUB_S1950_51_0166 'Sokol Voděrady'; CLUB_S1950_51_0167 'Sokol Voděrady – Sokol Davle'; CLUB_S1950_51_0168 'Pivovar Velké Popovice – Sokol Voděrady'
- CLUB_S1951_52_0005 -> CLUB_S1952_53_0004 'DSO Dynamo Karlovy Vary'; CLUB_S1952_53_0158 'Doprava Karlovy Vary'; CLUB_S1952_53_0171 'JNV Karlovy Vary'; CLUB_S1952_53_0174 'Stavba Karlovy Vary'
- CLUB_S1951_52_0003 -> CLUB_S1952_53_0008 'DSO Slavoj České Budějovice'; CLUB_S1952_53_0099 'ZSJ Slavia České Budějovice'; CLUB_S1952_53_0100 'PDA I. České Budějovice'; CLUB_S1952_53_0104 'PDA II. České Budějovice'
- CLUB_S1952_53_0153 -> CLUB_S1953_54_0181 'Sokol Bezdružice'; CLUB_S1953_54_0188 'Bezdružice – H. Týn 1:5'; CLUB_S1953_54_0193 'Plzeň b – Bezdružice 18:2'; CLUB_S1953_54_0199 'H. Bříza – Bezdružice 5:0'
- CLUB_S1953_54_0168 -> CLUB_S1954_55_0225 'Tatran Horažďovice'; CLUB_S1954_55_0244 'Spartak Blatná – Tatran Horažďovice 17:6'; CLUB_S1954_55_0245 'Lokomotiva Plzeň – Tatran Horažďovice 12:6'; CLUB_S1954_55_0246 'Sokol Žákavá – Tatran Horažďovice'
- CLUB_S1953_54_0410 -> CLUB_S1954_55_0472 'Spartak Jihlava'; CLUB_S1954_55_0474 'RH Jihlava'; CLUB_S1954_55_0480 'Jiskra Modeta Jihlava'; CLUB_S1954_55_0493 'Spartak Mokov Jihlava'
- CLUB_S1954_55_0607 -> CLUB_S1955_56_0036 'Spartak Moravia Olomouc'; CLUB_S1955_56_0052 'DSO Spartak Moravia Olomouc'; CLUB_S1955_56_0630 'DA Olomouc'; CLUB_S1955_56_0652 'Dynamo Spoje Olomouc'
- CLUB_S1954_55_0472 -> CLUB_S1955_56_0530 'Motorpal Jihlava'; CLUB_S1955_56_0538 'Jiskra Jihlava'; CLUB_S1955_56_0553 'Tatran Jihlava'; CLUB_S1955_56_0583 'Motorpal Jihlava B(Jihlava město) – Jihlava okres)'
- CLUB_S1958_59_0380 -> CLUB_S1959_60_0347 'Dukla Liberec'; CLUB_S1959_60_0348 'Slávia Liberec'; CLUB_S1959_60_0362 'Dukla Liberec'; CLUB_S1959_60_0364 'Slávia Liberec'
- CLUB_S1960_61_0567 -> CLUB_S1961_62_0592 'Baník Karviná 1.máj'; CLUB_S1961_62_0594 'Baník Karviná ČSA'; CLUB_S1961_62_0597 'RH Karviná'; CLUB_S1961_62_0600 'Spartak Karviná A'

</details>

## Návaznost soutěží (season_fate)

- Pokrytí: **22490** / 23442 (95.9 %) tabulkových řádků
- **Nekonzistencí** (1 club_id = víc fate v sezóně): **0**
- KVAL kontaminace (fate kde má být prázdné, D30): **0**
- Rozložení fate: `setrval`=9961, `reorganizace`=5175, `postup`=2683, `setrval?`=2585, `sestup`=2054, `zanik`=25, `slouceni`=7

## Pyramida soutěží (SYSTEM)

- Uzlů s `feeds_into`: **474** / 7390
- Top-level kvalifikací **bez** feeds_into (mezera/TODO): **68**

## Integrita

- Standings řádků bez záznamu v CLUBS (orphan): **2**

## Po sezónách

| sezóna | klubů | prev % | rozbité | fate % | fate nekon. | feeds |
|---|---|---|---|---|---|---|
| 1949_50 | 927 | 0 | 0 | 94 | 0 | 16 |
