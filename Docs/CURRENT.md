# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (nad ním jen `CLAUDE.md`), **nejvýš 80 řádků** (autor 30. 9. 2026). Hotové do stavu,
splněné smaž; podrobnosti do commitu a recenzí (`Docs/Reviews/`), historie do 30. 9. v `Docs/HANDOFF.md` (archiv).

Stav k **1. 10. 2026 v noci**: levné opravy exteriéru Wayfareru, menší ploutve (design v2.1), nové denní světlo;
`.\Tools\Test.ps1 -All` zelený, hra zabalená (`Docs/Reviews/2026-10-01_wayfarer_cheap_fixes.md`).

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
  - exteriér v2.1 přesně podle výkresu (`hs_build_ship`; ploutve 1,3 m, výška lodi 4,9 m), mesh decaly se šablonami
    jen u hardwaru, livrej, clear coat, RCS, podvozek; kokpit v2 (skleněné MFD, hologram lodi, ovládací moduly);
  - chase kamera 2800 cm (1,3 × délka); level: slunce 11 lx, obloha 0,55, zdroj 0,25°;
  - průchozí interiér: F v přistálé lodi = vstát za křeslem, u křesla sednout, u rampy ven; zvenku F dovnitř;
  - interiér z kitu: technická chodba s výklenky komponent, přepážky s dveřmi, nákladový prostor (mřížka 8 SCU,
    varianta B; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou a nábytkem z kitu.
- **Steadfast** (nákladní, Halcyon Freightworks): 2D návrh v2 čeká na schválení. Starý zkušební interiér stojí
  v `TestSpace` 500 m stranou (klávesa I), autor ho odmítl.
- **Interiérový kit** (`ArtSource/Kit/kit_rules.json`, `kit_parts.json`): dávky 1–3, 4 zčásti, 6 (nábytek kajuty);
  ukázka v `TestSpace` (U). Strop 500 + 3500 trojúhelníků na metr (autor 30. 9.; převezme `kit_manifest.json`).
- **Flotila:** Ship Matrix a dossiery publikované (skill `ship-pipeline` 1b); Delver a Farsight jen jako spec.
- **Nástroje:** `Tools/Test.ps1`, `Tools/Build.ps1`, CI s offline testy při každém pushi (stav přes veřejné API
  GitHubu), kritik s prahem `"gate": "step"` / `"ship"`, zámek těžkých zdrojů `Tools/HeavyLock.ps1`.

## Paralelní práce

- **Druhá session rozděluje `ASpaceshipPawn`** ve worktree `C:\gamespace\gamespace-audit` podle
  `Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md`. Hlavní session do `SpaceshipPawn.h/.cpp` a souvisejících
  souborů nesahá; větev sloučí a pustí `.\Tools\Test.ps1 -All`, až druhá session skončí.

## Čeká na rozhodnutí autora

- **Povrch trupu Wayfareru: výběr konceptu A–D** (`ArtSource/Ships/Wayfarer/Concept/surface_v3/concepts_sheet.jpg`).
  Po výběru: návrh exteriérového kitu (díly, pravidla, materiálové zóny, i pro další lodě) a pilot na jedné části.
- **Úklid disku, návrh ke schválení** (1. 10.): osiřelé LFS objekty mimo remote 17,2 GB, staré sady `Saved/Shots`
  16,8 GB, Zen DDC 41 GB na disk D (`UE-LocalDataCachePath`), videa referencí 3,2 GB.
- Nábytek kajuty: posouzení ve hře (kritik po 3 kolech a ověření FAIL 7/6/6/7/7/8/8/7, levné body opravené).
- Steadfast: schválení 2D návrhu v2 (`ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`).
- Kanopa Wayfareru jako téma designu v2 (autor ho otevře sám). Paleta Kestrel Dynamics: u první lodi Kestrelu.

## Známé problémy

- Exteriér Wayfareru (kritik 30. 9. FAIL 4,4): detail, materiály, trysky, světla, záď, podvozek, křídla a zbraně
  čekají na nový povrch trupu. Loď na svahu leží trupem v terénu (přistání v `SpaceshipPawn`, po rozdělení).
- Interiér Wayfareru, otevřené body recenzí: kajuta (`2026-09-30_cabin_furniture.md`: panel a sedák výdejníku,
  žebrování gumových pruhů, čočka lampičky, potrubí ventilátoru buňky) a obložení (`2026-09-30_cabin_liner.md`:
  svítidlo A, třmeny a patky zábradlí, nouzové značení, rám kolem zadních dveří).
- **Odrazy kovu odložené na optimalizaci** (autor 30. 9.): jediná účinná varianta jsou odrazy Lumenu do drsnosti
  0,32 za +1,3 ms (`2026-09-30_interior_reflections.md`).
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny; ohmatání madel; lišty stropu po segmentech.
- Stavba lodi není deterministická, export vždy přepíše všechna FBX (WORKFLOW 9.6 cw): ~250 MB do LFS na přestavbu.
- Hřebenový terén (`RidgedOctaves`) je vypnutý: kamera po přistání pod zemí, díry u okraje Veyry (podezření na
  odhad výšky v dlaždici, neověřeno). Kameny na Veyře nemají kolizi.
- Quantum tunel: stěny méně „mléčné“ než reference; TSR kreslí tmavé čáry podél rychlých jisker a ohony jisker
  bývají tečkované.
- Displeje: render target bez mipmap (pod ~1600 px šířky písmo zrní); duchy čísel při afterburneru.
- Loď bez podvozku u země stojí na neviditelném kořenovém boxu (končí u patek); řeší se, jen když to bude vadit.
- Zvuky jsou procedurální zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc.
- Neověřeno autorem ve hře: časování quantum skoku, HUD SC-1c mimo 1080p, chůze interiérem Steadfastu. Shipping
  build nikdy nezkoušen; v PIE Escape ukončí hru (menu je F10); debug HUD je anglicky.
- `compileall` hlásí `SyntaxWarning: invalid escape sequence` v docstringách šesti skriptů `Tools/Assets`.

## Další kroky

1. **Wayfarer, exteriér:** po výběru konceptu exteriérový kit a pilot; interiér: podlaha nákladového prostoru z kitu,
   otevřené body recenzí kajuty a obložení; nábytek dalších místností jen podle schváleného layoutu.
2. **Po dokončení druhé session:** sloučit větev s rozděleným `ASpaceshipPawn`, build, `.\Tools\Test.ps1 -All`,
   zabalit, vyfotit `cockpit` a `wayfarer_rooms`; pak loď na svahu (přistání v `SpaceshipPawn`).
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
