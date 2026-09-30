# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (hierarchie v `CLAUDE.md`: nad ním jen CLAUDE.md). Krátký: stav, rozhodnutí
autora, známé problémy, další kroky. Na konci každého kroku ho uprav: hotové přesuň do stavu, splněné kroky smaž,
podrobnosti patří do commitu a recenze v `Docs/Reviews/`. Historie do 30. 9. 2026: `Docs/HANDOFF.md` (archiv).

Stav k **30. 9. 2026 večer**, `main` po `7452fe1`: větev auditu sloučená, `.\Tools\Test.ps1 -All` zelený
(offline 6/6, Blender 1/1, UE 22/22), první běh CI zelený, hra zabalená.

## Stav

- **Hra:** zabalená Development hra s úvodní obrazovkou, pauzou a nastavením; `TestSpace` s planetou Veyra
  (poloměr 120 km, atmosféra, fotoskenovaný povrch, kameny), kulisy Keth a Orun.
- **Let podle SC** (master reference `starcitizenreference/`): SC-1a IFCS (coupled/decoupled, SCM/NAV, omezovač,
  G-Safe, ComStab, VJoy), SC-1b boost a afterburner, SC-1c letový HUD, SC-2a podvozek a precision, SC-2b VTOL,
  SC-3 značka dráhy letu, SC-4 quantum drive (cíl nosem, spool, kalibrace, tunel, příjezd). Ovládání: `README.md`.
  Tělesa pro quantum, radar a `FindNearest` drží `USpaceCelestialRegistrySubsystem` (radar v kokpitu ověřen
  v zabalené hře 30. 9.).
- **Postava:** první osoba výchozí a v lodích jediná (V pěšky přepne na třetí jen kvůli testům); sférická
  gravitace planety i umělá v lodi.
- **Wayfarer** (Halcyon Freightworks, malá multirole, 1 pilot) – jediná létající loď:
  - exteriér v2 přesně podle schváleného výkresu (`hs_build_ship`), vrstvy detailu podle SC (mesh decaly, livrej,
    clear coat, RCS, podvozek), kokpit v2 (skleněné MFD, hologram lodi, ovládací moduly);
  - **průchozí interiér** (29. 9.): F v přistálé lodi = vstát za křeslem, u křesla sednout, u rampy ven; zvenku F
    dovnitř po rampě;
  - **interiér z kitu** (29.–30. 9.): technická chodba s výklenky komponent, přepážky s dveřmi, nákladový prostor
    (mřížka 8 SCU ve variantě B, x 2,65–7,65; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou
    a **nábytkem z kitu** (lůžko, skříň na skafandr, hygienická buňka, výdejník; recenze
    `Docs/Reviews/2026-09-30_cabin_furniture.md`).
- **Steadfast** (nákladní, Halcyon Freightworks): 2D návrh v2 čeká na schválení autorem. Starý zkušební interiér
  stojí v `TestSpace` 500 m stranou (klávesa I), autor ho odmítl.
- **Interiérový kit** (vlastní, pravidla `ArtSource/Kit/kit_rules.json`, díly `kit_parts.json`): dávky 1–3
  hotové a schválené, dávka 4 zčásti (výklenky komponent, přepážky `Bulkhead_Door`, obložení `Wall_HullLiner`,
  stropy a podlaha průřezu L), dávka 6 nábytek kajuty (`Tools/Kit/kit_furniture.py`). Ukázka v `TestSpace`
  (klávesa U). Rozpočet stropu 500 + 3500 trojúhelníků na metr (autor 30. 9.; `kit_manifest.json` ho převezme
  při příští stavbě dávky).
- **Flotila:** Ship Matrix a dossiery publikované (odkazy ve skillu `ship-pipeline` 1b); Delver a Farsight jen
  jako spec. Vanguard a první stíhačka odstraněny 24. 9.
- **Nástroje:** `Tools/Test.ps1` (jednotný běh testů; UE test selže i na exit kódu editoru, tedy na chybě enginu
  v logu), `Tools/Build.ps1`, engine přes `GAMESPACE_UE_ROOT` (`Tools/UERoot.ps1`), GitHub Actions spouští při
  každém pushi offline testy (`.github/workflows/offline-tests.yml`, stav přes veřejné API
  `api.github.com/repos/michaelkocandrle/gamespace/actions/runs`, `gh` na stroji není). Vizuální kritik má práh
  podle typu kroku (`"gate": "step"` / `"ship"`, CLAUDE.md, skill `visual-review`).

## Paralelní práce

- **Druhá session rozděluje `ASpaceshipPawn`** podle `Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md`
  (autor ji spustil po zelených testech 30. 9.). Hlavní session do `SpaceshipPawn.h/.cpp` nesahá; větev sloučí
  a pustí `.\Tools\Test.ps1 -All`, až druhá session skončí.

## Čeká na rozhodnutí autora

- Nábytek kajuty: posouzení ve hře. Kritik po 3 kolech a ověřovacím kole FAIL (7/6/6/7/7/8/8/7, body 2 a 5
  částečně); levné body po něm opravené se snímky před a po, bez dalšího kola.
- Steadfast: schválení 2D návrhu v2 (`ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`).
- Kanopa Wayfareru jako téma designu v2 (autor ho otevře sám).
- Paleta Kestrel Dynamics: rozhodne se u první lodi Kestrelu.

## Známé problémy

- Interiér Wayfareru, otevřené body recenzí:
  - kajuta (`2026-09-30_cabin_furniture.md`): otěr a tmavé štítky na krémovém panelu výdejníku, sedák výdejníku
    světlejší než matrace (stejný materiál, jiné světlo), žebrování gumových pruhů jen zblízka, svítící čočka
    lampičky z uličky nevidět, potrubí ventilátoru buňky schované za stropními rozvody;
  - obložení (`2026-09-30_cabin_liner.md`): svítidlo A, třmeny a patky zábradlí, nouzové značení, rám kolem
    zadních dveří.
- **Odrazy kovu odložené na optimalizaci** (autor 30. 9.): reflection captures s Lumen GI nic nedělají, samotné
  SSR kov nezmění (rámy míří na stěny mimo záběr); jediná účinná varianta jsou odrazy Lumenu do drsnosti 0,32
  za +1,3 ms (`2026-09-30_interior_reflections.md`).
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny; ohmatání madel; lišty stropu po segmentech.
- Stavba lodi není deterministická: dvě stavby z téhož receptu se liší o pár trojúhelníků, export tak vždy
  přepíše všechna FBX (WORKFLOW 9.6 cw).
- Hřebenový terén (`RidgedOctaves`) je vypnutý: kamera po přistání pod zemí, díry u okraje Veyry. Podezření na
  odhad výšky v dlaždici, neověřeno.
- Kameny na Veyře nemají kolizi.
- Quantum tunel: stěny méně „mléčné“ než reference; TSR kreslí tmavé čáry podél rychlých jisker a ohony jisker
  bývají tečkované.
- Displeje: render target bez mipmap (pod ~1600 px šířky písmo zrní); krátké duchy čísel při afterburneru.
- Loď bez podvozku u země stojí na neviditelném kořenovém boxu (končí u patek); řeší se, jen když to bude vadit.
- Zvuky jsou procedurální zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc.
- Neověřeno autorem ve hře: časování quantum skoku, vzhled HUD SC-1c na jiném rozlišení než 1080p, chůze
  interiérem Steadfastu.
- Shipping build nikdy nezkoušen. V PIE Escape ukončí hru (menu je F10). Debug HUD je anglicky.
- `compileall` hlásí `SyntaxWarning: invalid escape sequence` v docstringách šesti skriptů `Tools/Assets`
  (oprava `r"""`, zatím jen varování).

## Další kroky

1. **Wayfarer, interiér z kitu:** podlaha nákladového prostoru z kitu (dnes `keep.hold` drží lodní podlahu),
   otevřené body recenzí kajuty a obložení; nábytek dalších místností jen podle schváleného layoutu.
2. **Po dokončení druhé session:** sloučit větev s rozděleným `ASpaceshipPawn`, build, `.\Tools\Test.ps1 -All`,
   zabalit, vyfotit `cockpit` a `wayfarer_rooms`.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
