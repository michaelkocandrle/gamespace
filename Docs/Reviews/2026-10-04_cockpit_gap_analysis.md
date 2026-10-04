# Kokpit Wayfareru proti SC: rozbor rozdílů a plán (4. 10. 2026)

Podnět autora (4. 10.): „ten level designu a grafiky tam pořád nemáme… řadu věcí máme pořád plasticky simplificitně
řešenou, cockpit zejména“; k MFD: „mají být daleko víc holografic vibe… high tech advanced, tyhle displeje působí
plasticky, působí to jako palubní displej, palubní počítač“.

Srovnání: naše `shots:20261004_172544_ship_power/05_power_on.png`, `/02_power_off.png`,
`shots:20261004_181921_mfd_config/06_config_zoom.png` proti autorovu záznamu SC (`sc_own_04` t00_02_36, t00_08_06,
`sc_own_03` t00_05_48; Aurora a Pisces). Rozbor udělal podagent (Opus), bez úprav.

## Největší rozdíly (podle dopadu)

1. **Materiály jsou ploché barvy.** Sloty kokpitu (`int_console`, `int_frame`, `int_dark` … v `Wayfarer_hs.json`) jsou
   konstanty: barva, drsnost, metallic. Chybí trim sheet, normal detail, AO a curvature, otěr hran, šmouhy, variace
   drsnosti v dílu. Výsledek je sametový černý plast.
2. **Tvary jsou měkké zaoblené desky.** Skoro vše je `rr_slab` / `rr_ring` v `Tools/Blender/hs_cockpit.py`. Chybí
   tvrdé zkosení s úzkým odleskem, vrstvení (rám, výplň, krytka), inset a výřezy.
3. **Chybí mikrodetail:** spáry panelů, šrouby, mřížky, drážky, panty, kabely, hadice.
4. **Rám kanopy:** SC má tlusté vzpěry s hloubkou, lemy a těsnění, takže kokpit sedí v kleci. U nás je jen tenká
   hrana skla (téma „kanopa v2“ čeká na autora).
5. **Světlo:** u nás rovnoměrně tmavé, bez spotů na ovladačích a bez kontaktních stínů. Kovy nic neodrážejí
   (odrazy Lumenu jsou odložené).
6. **Popisky:** SC je má drobné a husté (loga, varování, šablony, čísla panelů, legendy kláves). Naše jsou málo početné
   a měřítkem velké.
7. **Ovladače a sedadlo:** naše ovladače jsou miniaturní ploché desky (14,5 mm), čtou se jako nálepky. Nejsou vidět
   HOTAS ani ruce.
8. **MFD** plavou v kapotě bez nosné konstrukce. Navíc jsou jako obsah „palubní počítač“ (plné panely, štítky
   s rámečky), ne holografie (autor).

**Systémové** (oprava jednou pomůže všemu):

- PBR master s trim sheetem, otěrem hran (curvature/AO z bake) a grime;
- normal detail (spáry, šrouby, mřížky);
- knihovna mikrodecalů s pravidlem hustoty;
- chamfer a inset v geometrických helperech;
- pravidla světel kokpitu a odrazy (reflection capture).

**Lokální:** rám kanopy, ramena MFD, velikost a hloubka ovladačů, HOTAS a ruce, měřítko nápisů, kabely.

## Plán

| Krok | Obsah | Rozsah |
|---|---|---|
| H | **Holografické MFD** (autor 4. 10.) | střední |
| 1 | **2D návrh kokpitu v2** | střední |
| 2 | **Materiálový základ** | velký |
| 3 | **Geometrická knihovna** | střední |
| 4 | **Stavba Wayfareru** | střední |
| 5 | **Světlo a odrazy** | malý až střední |

Obsah kroků:

- **H – holografické MFD:**
  - obsah bez plných panelů a rámečků;
  - tenké světelné linky, záře (bloom přes emisi), jemné řádkování a lehký paralaxní odstup vrstev;
  - průhledné sklo s promítnutým obrazem místo „monitoru“;
  - přepínače jako světelné pilulky;
  - stejný jazyk mají už popisky najetí (holografický popisek z 2b).
- **1 – 2D návrh kokpitu v2:**
  - řez, půdorys a pohled pilota: rámy kanopy, ramena MFD, spáry, šrouby, kabelové trasy;
  - měřené cíle: tloušťka rámu, hustota decalů a šroubů na m², rozsah drsnosti;
  - styl podle snímků SC, AI jen jako stylová reference.
- **2 – materiálový základ:**
  - master materiál s trim sheetem (CC0), otěrem hran z bake curvature/AO, grime a variací drsnosti;
  - sloty v `*_hs.json` ze skalárů na sady;
  - bake v Blender headless.
- **3 – geometrická knihovna** v `hs_cockpit.py`: `chamfer_slab`, `inset_panel`, `bolt_row`, `grille`, `cable_run`,
  `strut`; pody, kapota a ovladače jako vrstvené dílce, větší a hlubší ovladače.
- **4 – stavba Wayfareru:**
  - vnitřní rám kanopy z výkresu, ramena MFD, kabely, drobné štítky podle hustoty, HOTAS v zorném poli;
  - navazuje na „kokpit z kitu“ v `Docs/CURRENT.md`.
- **5 – světlo a odrazy:** key/rim, spoty na ovladače, kontaktní stíny, reflection capture, stavy vypnuto/zapnuto;
  na závěr kritik s checklistem kokpitu.

Kroky 2 a 3 jsou jádro „plastového“ dojmu. Bez nich bude každá lokální oprava pořád vypadat jako plast.
