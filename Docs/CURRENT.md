# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (nad ním jen `CLAUDE.md`), **nejvýš 80 řádků** (autor 30. 9. 2026). Na konci
kroku hotové přesuň do stavu a splněné kroky smaž; podrobnosti patří do commitu a recenze v `Docs/Reviews/`,
historie do 30. 9. 2026 je v `Docs/HANDOFF.md` (archiv).

Stav k **30. 9. 2026 večer**, `main` po `7452fe1`: větev auditu sloučená, `.\Tools\Test.ps1 -All` zelený
(offline 6/6, Blender 1/1, UE 22/22), první běh CI zelený, hra zabalená.

## Stav

- **Hra:** zabalená Development hra s úvodní obrazovkou, pauzou a nastavením; `TestSpace` s planetou Veyra
  (poloměr 120 km, atmosféra, fotoskenovaný povrch, kameny), kulisy Keth a Orun.
- **Let podle SC** (master reference `starcitizenreference/`): SC-1a IFCS (coupled/decoupled, SCM/NAV, omezovač,
  G-Safe, ComStab, VJoy), SC-1b boost a afterburner, SC-1c letový HUD, SC-2a podvozek a precision, SC-2b VTOL,
  SC-3 značka dráhy letu, SC-4 quantum drive (cíl nosem, spool, kalibrace, tunel, příjezd). Ovládání: `README.md`.
  Tělesa pro quantum, radar a `FindNearest` drží `USpaceCelestialRegistrySubsystem`.
- **Postava:** první osoba výchozí a v lodích jediná (V pěšky přepne na třetí jen kvůli testům); sférická
  gravitace planety i umělá v lodi.
- **Wayfarer** (Halcyon Freightworks, malá multirole, 1 pilot) – jediná létající loď:
  - exteriér v2 přesně podle schváleného výkresu (`hs_build_ship`), vrstvy detailu podle SC (mesh decaly, livrej,
    clear coat, RCS, podvozek), kokpit v2 (skleněné MFD, hologram lodi, ovládací moduly);
  - průchozí interiér: F v přistálé lodi = vstát za křeslem, u křesla sednout, u rampy ven; zvenku F dovnitř;
  - interiér z kitu: technická chodba s výklenky komponent, přepážky s dveřmi, nákladový prostor (mřížka 8 SCU,
    varianta B; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou a nábytkem z kitu.
- **Steadfast** (nákladní, Halcyon Freightworks): 2D návrh v2 čeká na schválení. Starý zkušební interiér stojí
  v `TestSpace` 500 m stranou (klávesa I), autor ho odmítl.
- **Interiérový kit** (`ArtSource/Kit/kit_rules.json`, `kit_parts.json`): dávky 1–3 schválené, dávka 4 zčásti
  (výklenky, přepážky `Bulkhead_Door`, obložení `Wall_HullLiner`, stropy a podlaha průřezu L), dávka 6 nábytek
  kajuty. Ukázka v `TestSpace` (klávesa U). Strop 500 + 3500 trojúhelníků na metr (autor 30. 9.;
  `kit_manifest.json` ho převezme při příští stavbě dávky).
- **Flotila:** Ship Matrix a dossiery publikované (odkazy ve skillu `ship-pipeline` 1b); Delver a Farsight jen
  jako spec.
- **Nástroje:** `Tools/Test.ps1` (UE test selže i na chybě enginu v logu), `Tools/Build.ps1`, engine přes
  `GAMESPACE_UE_ROOT`; CI pouští offline testy při každém pushi (stav přes veřejné API GitHubu, `gh` na stroji
  není). Kritik má práh podle typu kroku (`"gate": "step"` / `"ship"`). Zámek těžkých zdrojů `Tools/HeavyLock.ps1`.

## Paralelní práce

- **Druhá session rozděluje `ASpaceshipPawn`** ve worktree `C:\gamespace\gamespace-audit` podle
  `Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md`. Hlavní session do `SpaceshipPawn.h/.cpp` a souvisejících
  souborů nesahá; větev sloučí a pustí `.\Tools\Test.ps1 -All`, až druhá session skončí.

## Čeká na rozhodnutí autora

- Nábytek kajuty: posouzení ve hře (kritik po 3 kolech a ověřovacím kole FAIL 7/6/6/7/7/8/8/7; levné body
  opravené potom se snímky před a po).
- Steadfast: schválení 2D návrhu v2 (`ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`).
- Kanopa Wayfareru jako téma designu v2 (autor ho otevře sám). Paleta Kestrel Dynamics: u první lodi Kestrelu.

## Známé problémy

- Interiér Wayfareru, otevřené body recenzí: kajuta (`2026-09-30_cabin_furniture.md`: panel a sedák výdejníku,
  žebrování gumových pruhů, čočka lampičky, potrubí ventilátoru buňky) a obložení (`2026-09-30_cabin_liner.md`:
  svítidlo A, třmeny a patky zábradlí, nouzové značení, rám kolem zadních dveří).
- **Odrazy kovu odložené na optimalizaci** (autor 30. 9.): jediná účinná varianta jsou odrazy Lumenu do drsnosti
  0,32 za +1,3 ms (`2026-09-30_interior_reflections.md`).
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny; ohmatání madel; lišty stropu po segmentech.
- Stavba lodi není deterministická, export vždy přepíše všechna FBX (WORKFLOW 9.6 cw).
- Hřebenový terén (`RidgedOctaves`) je vypnutý: kamera po přistání pod zemí, díry u okraje Veyry (podezření na
  odhad výšky v dlaždici, neověřeno). Kameny na Veyře nemají kolizi.
- Quantum tunel: stěny méně „mléčné“ než reference; TSR kreslí tmavé čáry podél rychlých jisker a ohony jisker
  bývají tečkované.
- Displeje: render target bez mipmap (pod ~1600 px šířky písmo zrní); krátké duchy čísel při afterburneru.
- Loď bez podvozku u země stojí na neviditelném kořenovém boxu (končí u patek); řeší se, jen když to bude vadit.
- Zvuky jsou procedurální zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc.
- Neověřeno autorem ve hře: časování quantum skoku, HUD SC-1c mimo 1080p, chůze interiérem Steadfastu.
- Shipping build nikdy nezkoušen. V PIE Escape ukončí hru (menu je F10). Debug HUD je anglicky.
- `compileall` hlásí `SyntaxWarning: invalid escape sequence` v docstringách šesti skriptů `Tools/Assets`.

## Další kroky

1. **Wayfarer, interiér z kitu:** podlaha nákladového prostoru z kitu (dnes `keep.hold` drží lodní podlahu),
   otevřené body recenzí kajuty a obložení; nábytek dalších místností jen podle schváleného layoutu.
2. **Po dokončení druhé session:** sloučit větev s rozděleným `ASpaceshipPawn`, build, `.\Tools\Test.ps1 -All`,
   zabalit, vyfotit `cockpit` a `wayfarer_rooms`.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
