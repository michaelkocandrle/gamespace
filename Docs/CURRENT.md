# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (nad ním jen `CLAUDE.md`), **nejvýš 80 řádků** (autor 30. 9. 2026). Hotové do stavu,
splněné smaž; podrobnosti do commitu a recenzí (`Docs/Reviews/`), historie do 30. 9. v `Docs/HANDOFF.md` (archiv).

Stav k **1. 10. 2026 odpoledne**: úklid disku (snímky na D:, `Tools/Cleanup.ps1`, export a import jen změněných
meshů), každá session balí do své složky, hra z main zabalená v `C:\gamespace\Builds`; vzorový výkres exteriéru E-01.

## Stav

- **Hra:** zabalená Development hra (menu, pauza, nastavení); `TestSpace` s planetou Veyra (120 km), Keth a Orun.
- **Let podle SC** (master reference `starcitizenreference/`): SC-1a IFCS (coupled/decoupled, SCM/NAV, omezovač,
  G-Safe, ComStab, VJoy), SC-1b boost a afterburner, SC-1c letový HUD, SC-2a podvozek a precision, SC-2b VTOL,
  SC-3 značka dráhy letu, SC-4 quantum drive (cíl nosem, spool, kalibrace, tunel, příjezd). Ovládání: `README.md`.
  Tělesa pro quantum, radar a `FindNearest` drží `USpaceCelestialRegistrySubsystem`.
- **Postava:** první osoba (V pěšky = třetí jen pro testy); sférická gravitace planety i umělá v lodi.
- **Wayfarer** (Halcyon Freightworks, malá multirole, 1 pilot) – jediná létající loď:
  - exteriér v2.1 přesně podle výkresu (`hs_build_ship`; ploutve 1,3 m potvrzené autorem, výška lodi 4,9 m), mesh
    decaly se šablonami jen u hardwaru, livrej, RCS, podvozek; kokpit v2 (skleněné MFD, hologram lodi, moduly);
  - povrch trupu v3 = **koncept B + C** (autor 1. 10.); data návrhu `Design/Wayfarer_exterior_design.json`, každý
    prvek stavby i návrhu má ID (`Tools/Design/assign_exterior_ids.py`), výkresy z modelu `exterior_model.py`;
  - chase kamera 2800 cm; level: slunce 11 lx, obloha 0,55; průchozí interiér (F vstát / sednout / ven / dovnitř);
  - interiér z kitu: technická chodba s výklenky komponent, přepážky s dveřmi, nákladový prostor (mřížka 8 SCU,
    varianta B; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou a nábytkem z kitu.
- **Steadfast** (nákladní): 2D návrh v2 čeká na schválení; starý odmítnutý interiér v `TestSpace` (klávesa I).
- **Interiérový kit** (`ArtSource/Kit/kit_rules.json`, `kit_parts.json`): dávky 1–3, 4 zčásti, 6 (nábytek kajuty);
  ukázka v `TestSpace` (U). Strop 500 + 3500 trojúhelníků na metr (autor 30. 9.; převezme `kit_manifest.json`).
- **Flotila:** Ship Matrix a dossiery publikované (skill `ship-pipeline` 1b); Delver a Farsight jen jako spec.
- **Nástroje:** `Tools/Test.ps1`, `Tools/Build.ps1`, CI s offline testy při každém pushi (stav přes veřejné API
  GitHubu), kritik s prahem `"gate": "step"` / `"ship"`, zámek těžkých zdrojů `Tools/HeavyLock.ps1`, snímky
  v `D:\gamespace-shots` (`shots:` v recenzích), `Tools/Cleanup.ps1` na konci kroku.

## Paralelní práce

- **Rozdělení `ASpaceshipPawn` je sloučené do main** (1. 10. 2026; kroky 1–9, průběh na konci
  `Docs/Reviews/2026-09-30_spaceshippawn_split_plan.md`); autor hru z větve ručně otestoval.

## Čeká na rozhodnutí autora

- **Styl výkresů: vzorový list E-01** (`ArtSource/Ships/Wayfarer/Design/Drawings/Wayfarer_E01_starboard.png`,
  recenze `Docs/Reviews/2026-10-01_wayfarer_drawing_e01.md`). Po schválení zbytek bodů 3, 4 a 6 dossieru, teprve
  pak exteriérový kit a pilot z dat návrhu.
- **Disk:** Zen DDC přesune autor na D: (`setx UE-LocalDataCachePath D:\UnrealDDC`) a napíše; pak ověřit novou
  cestu a smazat starý Zen DDC. Starý lokální DDC (4,2 GB, `%LOCALAPPDATA%\UnrealEngine\Common\DerivedDataCache`)
  smaže autor (mazání mi oprávnění nepovolila). LFS sirotci (~17 GB) a worktree audit až po sloučení.
- Nábytek kajuty: posouzení ve hře (kritik po 3 kolech a ověření FAIL 7/6/6/7/7/8/8/7, levné body opravené).
- Steadfast: schválení 2D návrhu v2 (`ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`).
- Kanopa Wayfareru jako téma designu v2 (autor ho otevře sám). Paleta Kestrel Dynamics: u první lodi Kestrelu.

## Známé problémy

- Exteriér Wayfareru (kritik 30. 9. FAIL 4,4): detail, materiály, trysky, světla, záď, podvozek, křídla a zbraně
  čekají na nový povrch trupu. Loď na svahu leží trupem v terénu (přistání v `SpaceshipPawn`, po rozdělení).
- Interiér Wayfareru, otevřené body recenzí: kajuta (`2026-09-30_cabin_furniture.md`: panel a sedák výdejníku,
  žebrování gumových pruhů, čočka lampičky, potrubí ventilátoru buňky) a obložení (`2026-09-30_cabin_liner.md`:
  svítidlo A, třmeny a patky zábradlí, nouzové značení, rám kolem zadních dveří).
- **Odrazy kovu odložené na optimalizaci** (autor 30. 9.): odrazy Lumenu do drsnosti 0,32 za +1,3 ms.
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny; ohmatání madel; lišty stropu po segmentech.
- **Determinismus stavby, na později** (autor 1. 10.): export a import přeskočí meshe se stejným hashem geometrie,
  ale přestavba v Blenderu dá jiné hashe (~250 MB do LFS) a import pokaždé znovu uloží ~150 materiálů a textur.
- Výkres E-01 našel decaly a konektor, které z boku dopadají na gondolu, křídlo nebo zbraň; oprava je v návrhu.
- Hřebenový terén (`RidgedOctaves`) vypnutý: kamera po přistání pod zemí, díry u okraje Veyry; kameny bez kolize.
- Quantum tunel: stěny méně „mléčné“ než reference; TSR kreslí tmavé čáry podél jisker, ohony bývají tečkované.
- Displeje: render target bez mipmap (pod ~1600 px šířky písmo zrní); duchy čísel při afterburneru.
- Loď bez podvozku u země stojí na neviditelném kořenovém boxu (končí u patek); řeší se, jen když to bude vadit.
- Zvuky jsou procedurální zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc.
- Neověřeno autorem ve hře: časování quantum skoku, HUD SC-1c mimo 1080p, chůze interiérem Steadfastu. Shipping
  build nikdy nezkoušen; v PIE Escape ukončí hru (menu je F10); debug HUD je anglicky.
- `compileall` hlásí `SyntaxWarning: invalid escape sequence` v docstringách šesti skriptů `Tools/Assets`.

## Další kroky

1. **Wayfarer:** po schválení stylu E-01 výkresy exteriéru (6 pohledů, detaily, kóty, kit), interiéru a konceptů,
   pak kit a pilot; interiér: podlaha nákladového prostoru z kitu, otevřené body recenzí kajuty a obložení.
2. **Po dokončení druhé session:** sloučit větev s rozděleným `ASpaceshipPawn`, build, `.\Tools\Test.ps1 -All`,
   zabalit, vyfotit `cockpit` a `wayfarer_rooms`; pak loď na svahu (přistání v `SpaceshipPawn`).
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
