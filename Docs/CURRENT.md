# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (hierarchie v `CLAUDE.md`: nad ním jen CLAUDE.md). Krátký: stav, rozhodnutí
autora, známé problémy, další kroky. Na konci každého kroku ho uprav: hotové přesuň do stavu, splněné kroky smaž,
podrobnosti patří do commitu a recenze v `Docs/Reviews/`. Historie do 30. 9. 2026: `Docs/HANDOFF.md` (archiv).

Stav k **30. 9. 2026**.

## Stav

- **Hra:** zabalená Development hra s úvodní obrazovkou, pauzou a nastavením; `TestSpace` s planetou Veyra
  (poloměr 120 km, atmosféra, fotoskenovaný povrch, kameny), kulisy Keth a Orun.
- **Let podle SC** (master reference `starcitizenreference/`): SC-1a IFCS (coupled/decoupled, SCM/NAV, omezovač,
  G-Safe, ComStab, VJoy), SC-1b boost a afterburner, SC-1c letový HUD, SC-2a podvozek a precision, SC-2b VTOL,
  SC-3 značka dráhy letu, SC-4 quantum drive (cíl nosem, spool, kalibrace, tunel, příjezd). Ovládání: `README.md`.
- **Postava:** první osoba výchozí a v lodích jediná (V pěšky přepne na třetí jen kvůli testům); sférická
  gravitace planety i umělá v lodi.
- **Wayfarer** (Halcyon Freightworks, malá multirole, 1 pilot) – jediná létající loď:
  - exteriér v2 přesně podle schváleného výkresu (`hs_build_ship`), vrstvy detailu podle SC (mesh decaly, livrej,
    clear coat, RCS, podvozek), kokpit v2 (skleněné MFD, hologram lodi, ovládací moduly);
  - **průchozí interiér** (29. 9.): F v přistálé lodi = vstát za křeslem, u křesla sednout, u rampy ven; zvenku F
    dovnitř po rampě;
  - **přestavba interiéru z kitu, krok A** (29.–30. 9.): technická chodba s výklenky komponent, přepážky
    s dveřmi, nákladový prostor a kajuta z obložení trupu (varianta B). Nábytek a podlahy jsou zatím lodní.
- **Steadfast** (nákladní, Halcyon Freightworks): 2D návrh v2 čeká na schválení autorem. Starý zkušební interiér
  stojí v `TestSpace` 500 m stranou (klávesa I), autor ho odmítl.
- **Interiérový kit** (vlastní, pravidla `ArtSource/Kit/kit_rules.json`, díly `kit_parts.json`): dávky 1–3
  hotové a schválené, dávka 4 zčásti (výklenky komponent, přepážky `Bulkhead_Door`, obložení `Wall_HullLiner`).
  Ukázka v `TestSpace` (klávesa U).
- **Flotila:** Ship Matrix a dossiery publikované (odkazy ve skillu `ship-pipeline` 1b); Delver a Farsight jen
  jako spec. Vanguard a první stíhačka odstraněny 24. 9.
- **Nástroje:** `Tools/Test.ps1` (jednotný běh testů), `Tools/Build.ps1`, engine přes `GAMESPACE_UE_ROOT`
  (`Tools/UERoot.ps1`).

## Čeká na rozhodnutí autora

- Steadfast: schválení 2D návrhu v2 (`ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`).
- Wayfarer: posun mřížky nákladového prostoru (`Docs/Kit/hold_grid_plan_wayfarer.png`).
- Kanopa Wayfareru jako téma designu v2 (autor ho otevře sám).
- Plán rozdělení `ASpaceshipPawn` (`Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md`).
- Paleta Kestrel Dynamics: rozhodne se u první lodi Kestrelu.

## Známé problémy

- Interiér Wayfareru, otevřené body poslední recenze (`Docs/Reviews/2026-09-30_cabin_liner.md`): povrchová
  odezva materiálů (odrazy Lumenu jsou v interiéru kvůli výkonu vypnuté), svítidlo A, třmeny a patky zábradlí,
  nouzové značení, rám kolem zadních dveří.
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny; ohmatání madel; lišty stropu po segmentech.
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

1. **Wayfarer, přestavba interiéru:** nábytek kajuty a nákladového prostoru z kitu (dávka 6), pak podlahy;
   otevřené body recenze kajuty.
2. **Po auditu v1** (`Docs/Reviews/2026-09-30_audit_v1_response.md`): hlavní session zbuilduje a otestuje registr
   těles (`USpaceCelestialRegistrySubsystem`); po schválení plánu postupně rozdělit `ASpaceshipPawn`.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.).
