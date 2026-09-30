# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (nad ním jen `CLAUDE.md`). **Strop 80 řádků** (hlídá `test_docs_limits.py`):
stav, rozhodnutí autora, známé problémy, další kroky. Po kroku uprav, splněné smaž; podrobnosti patří do commitu
a recenze v `Docs/Reviews/`, architektura do `Docs/ARCHITECTURE.md`. Historie do 30. 9. 2026: `Docs/HANDOFF.md`.

Stav k **30. 9. 2026 večer**, `main` po `7452fe1`: větev auditu sloučená, `.\Tools\Test.ps1 -All` zelený
(offline 6/6, Blender 1/1, UE 22/22), první běh CI zelený, hra zabalená.

## Stav

- **Hra:** zabalená Development hra (úvodní obrazovka, pauza, nastavení); `TestSpace` s planetou Veyra (120 km,
  atmosféra, fotoskenovaný povrch, kameny), kulisy Keth a Orun. Ovládání: `README.md`.
- **Let podle SC** (`starcitizenreference/`): SC-1a IFCS, SC-1b boost a afterburner, SC-1c HUD, SC-2a podvozek
  a precision, SC-2b VTOL, SC-3 značka dráhy letu, SC-4 quantum drive. Radar v kokpitu ověřen po zavedení
  registru těles v zabalené hře 30. 9.
- **Postava:** první osoba výchozí a v lodích jediná (V pěšky přepne na třetí jen kvůli testům); sférická
  gravitace planety i umělá v lodi.
- **Wayfarer** (Halcyon Freightworks, malá multirole, 1 pilot) – jediná létající loď:
  - exteriér v2 přesně podle výkresu, vrstvy detailu podle SC, kokpit v2 (skleněné MFD, hologram, moduly);
  - **průchozí interiér** (29. 9.): F v přistálé lodi vstát za křeslem, u křesla sednout, u rampy ven, zvenku dovnitř;
  - **interiér z kitu** (29.–30. 9.): technická chodba s výklenky, přepážky s dveřmi, nákladový prostor (mřížka
    8 SCU varianta B, x 2,65–7,65; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou a **nábytkem
    z kitu** (lůžko, skříň na skafandr, hygienická buňka, výdejník; `Docs/Reviews/2026-09-30_cabin_furniture.md`).
- **Steadfast:** 2D návrh v2 čeká na schválení; starý zkušební interiér 500 m stranou v `TestSpace` (I), odmítnutý.
- **Interiérový kit** (`ArtSource/Kit/kit_rules.json`, `kit_parts.json`): dávky 1–3 schválené, dávka 4 zčásti
  (výklenky, `Bulkhead_Door`, `Wall_HullLiner`, stropy a podlaha průřezu L), dávka 6 nábytek kajuty
  (`Tools/Kit/kit_furniture.py`); ukázka v `TestSpace` (U). Rozpočet stropu 500 + 3500 trojúhelníků na metr
  (autor 30. 9.; `kit_manifest.json` ho převezme při příští stavbě dávky).
- **Flotila:** Ship Matrix a dossiery publikované (skill `ship-pipeline` 1b); Delver a Farsight jen spec.
- **Nástroje:** `Tools/Test.ps1` (UE test selže i na chybě enginu v logu), `Tools/Build.ps1`, `GAMESPACE_UE_ROOT`,
  CI s offline testy při každém pushi, zámek těžkých zdrojů `Tools/HeavyLock.ps1`, práh kritika podle typu kroku.

## Paralelní práce

- **Druhá session rozděluje `ASpaceshipPawn`** (větev `pawn-split`) podle
  `Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md`. Hlavní session do `SpaceshipPawn.h/.cpp` nesahá; větev
  sloučí a pustí `.\Tools\Test.ps1 -All`. Těžké zdroje jen pod zámkem `C:\gamespace-locks\heavy.lock`.

## Čeká na rozhodnutí autora

- Nábytek kajuty: posouzení ve hře (kritik 3 kola + ověřovací FAIL 7/6/6/7/7/8/8/7, levné body opravené).
- Steadfast: schválení 2D návrhu v2 (`ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`).
- Kanopa Wayfareru jako téma designu v2 (autor ho otevře sám). Paleta Kestrel: u první lodi Kestrelu.

## Známé problémy

- Otevřené body recenzí interiéru Wayfareru:
  - kajuta (`2026-09-30_cabin_furniture.md`): otěr a tmavé štítky na panelu výdejníku, sedák výdejníku světlejší
    než matrace, žebrování gumových pruhů jen zblízka, čočka lampičky z uličky nevidět, potrubí ventilátoru buňky
    schované za stropními rozvody;
  - obložení (`2026-09-30_cabin_liner.md`): svítidlo A, třmeny a patky zábradlí, nouzové značení, rám zadních dveří.
- **Odrazy kovu odložené na optimalizaci** (autor 30. 9.): jediná účinná varianta jsou odrazy Lumenu do drsnosti
  0,32 za +1,3 ms (`2026-09-30_interior_reflections.md`).
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny; ohmatání madel; lišty stropu po segmentech.
- Stavba lodi není deterministická (pár trojúhelníků), export vždy přepíše všechna FBX (WORKFLOW 9.6 cw).
- Hřebenový terén (`RidgedOctaves`) vypnutý (kamera pod zemí, díry u okraje Veyry; neověřené podezření na odhad
  výšky v dlaždici). Kameny na Veyře nemají kolizi.
- Quantum tunel: stěny méně „mléčné“ než reference; TSR tmavé čáry podél rychlých jisker, tečkované ohony.
- Displeje: render target bez mipmap (pod ~1600 px písmo zrní); krátké duchy čísel při afterburneru.
- Loď bez podvozku stojí na neviditelném kořenovém boxu (končí u patek); řeší se, až to bude vadit.
- Zvuky jsou procedurální zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc.
- Neověřeno autorem ve hře: časování quantum skoku, HUD SC-1c mimo 1080p, chůze interiérem Steadfastu.
- Shipping build nezkoušen. V PIE Escape ukončí hru (menu F10). Debug HUD je anglicky.
- `compileall`: `SyntaxWarning: invalid escape sequence` v docstringách šesti skriptů `Tools/Assets` (oprava `r"""`).

## Další kroky

1. **Wayfarer, interiér z kitu:** podlaha nákladového prostoru z kitu (dnes `keep.hold`), otevřené body recenzí
   kajuty a obložení; nábytek dalších místností jen podle schváleného layoutu.
2. **Po dokončení druhé session:** sloučit `pawn-split`, build, `.\Tools\Test.ps1 -All`, zabalit, vyfotit `cockpit`
   a `wayfarer_rooms`; autor vyzkouší kroky Prezentace a Vstup podle předávky.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a quantum palivo (SC-4), přetížení (SC-5), systémy lodi
   (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu.
