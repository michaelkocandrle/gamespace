# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (nad ním jen `CLAUDE.md`), **nejvýš 80 řádků** (autor 30. 9. 2026). Hotové do stavu,
splněné smaž; podrobnosti do commitu a recenzí (`Docs/Reviews/`), historie do 30. 9. v `Docs/HANDOFF.md` (archiv).

Stav k **1. 10. 2026 večer**: výkresy exteriéru Wayfareru E-01 až E-08 schválené (revize C: hřbet R v primárním
laku); hlavní session staví exteriérový kit a pilota, druhá session výkresy interiéru a koncepty.

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
  GitHubu), kritik s prahem `"gate": "step"` / `"ship"`, zámek těžkých zdrojů `Tools/HeavyLock.ps1` (heartbeat
  5 min, 20 min bez obnovení = volný, hooky Stop/StopFailure/SessionEnd ho uvolní; `CLAUDE.md`), snímky
  v `D:\gamespace-shots` (`shots:` v recenzích), `Tools/Cleanup.ps1` na konci kroku, Zen DDC v `D:\UnrealDDC`.

## Paralelní práce

- **Druhá session** (worktree `gamespace-audit`, větev `wayfarer-dossier-interior`): výkresy interiéru (bod 4, styl
  I-04 schválen 1. 10.) a koncepty (bod 6); ID interiéru v `Design/Wayfarer_interior_design.json`, model
  `interior_model.py`, listy `draw_interior_sheet.py`, test `test_interior_drawing.py`, skill `ship-pipeline` 1c.
  `exterior_*.py` mění jen hlavní session. **Datový commit druhé session** (autor 1. 10.: layout kajuty podle kitu,
  podpora života posunutá, komentář D-INT-SEC06 v setupu; E-01–E-08 a paluba překreslené): při konfliktu v
  `Drawings/Wayfarer_E0*` nebo `Design/*.png` vzít kteroukoli stranu a po sloučení překreslit (`draw_exterior_sheet.py`).
- **Hlavní session:** exteriérový kit a pilot (hřbet, záď s gondolami), kritik s dílčím prahem.
- Druhá session balí do `Builds_<jméno>` (`BuildDir.ps1`); slučuje hlavní session.

## Čeká na rozhodnutí autora

- Nábytek kajuty: posouzení ve hře (kritik po 3 kolech a ověření FAIL 7/6/6/7/7/8/8/7, levné body opravené).
- Steadfast: schválení 2D návrhu v2 (`ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`).
- Kanopa Wayfareru jako téma designu v2 (autor ho otevře sám). Paleta Kestrel Dynamics: u první lodi Kestrelu.

## Známé problémy

- Exteriér Wayfareru (kritik 30. 9. FAIL 4,4): detail, materiály, trysky, světla, záď, podvozek, křídla a zbraně
  čekají na nový povrch trupu. Loď na svahu leží trupem v terénu (odblokované rozdělením pawnu).
- `DebugEngageQuantum` po zadání cíle jménem znovu vybírá cíl podle nosu lodi (drobnost, autor 1. 10.).
- Interiér Wayfareru, otevřené body recenzí: kajuta (`2026-09-30_cabin_furniture.md`: panel a sedák výdejníku,
  žebrování gumových pruhů, čočka lampičky, potrubí ventilátoru buňky) a obložení (`2026-09-30_cabin_liner.md`:
  svítidlo A, třmeny a patky zábradlí, nouzové značení, rám kolem zadních dveří).
- **Odrazy kovu odložené na optimalizaci** (autor 30. 9.): odrazy Lumenu do drsnosti 0,32 za +1,3 ms.
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny; ohmatání madel; lišty stropu po segmentech.
- **Determinismus stavby, na později** (autor 1. 10.): otisk souboru opraven (množina v nastavení exportu, WORKFLOW
  9.6 ff), šum zůstává v trupu, decalech a interiéru (±40 trojúhelníků mezi běhy; 3 FBX při každé přestavbě) a import
  pokaždé znovu uloží ~150 materiálů a textur. Klíče `id` v receptu a setupu stavbu nemění (ověřeno 1. 10.).
- Hřebenový terén (`RidgedOctaves`) vypnutý: kamera po přistání pod zemí, díry u okraje Veyry; kameny bez kolize.
- Quantum tunel: stěny méně „mléčné“ než reference; TSR kreslí tmavé čáry podél jisker, ohony bývají tečkované.
- Displeje: render target bez mipmap (pod ~1600 px šířky písmo zrní); duchy čísel při afterburneru.
- Loď bez podvozku u země stojí na neviditelném kořenovém boxu (končí u patek); řeší se, jen když to bude vadit.
- Zvuky jsou procedurální zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc.
- Neověřeno autorem ve hře: časování quantum skoku, HUD SC-1c mimo 1080p, chůze interiérem Steadfastu. Shipping
  build nikdy nezkoušen; v PIE Escape ukončí hru (menu je F10); debug HUD je anglicky.
- `compileall` hlásí `SyntaxWarning: invalid escape sequence` v docstringách šesti skriptů `Tools/Assets`.

## Další kroky

1. **Wayfarer:** exteriérový kit (díly XK-*) a pilot na hřbetu a zádi s gondolami podle výkresů E-01 až E-08,
   kritik s dílčím prahem; pak kit na celou loď. Druhá session: body 4 a 6 dossieru (viz Paralelní práce).
2. **Loď na svahu:** přistání v `SpaceshipPawn` (odblokované); interiér: podlaha nákladu z kitu, body recenzí.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
