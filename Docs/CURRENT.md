# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (nad ním jen `CLAUDE.md`), **nejvýš 80 řádků** (autor 30. 9. 2026). Hotové do stavu,
splněné smaž; podrobnosti do commitu a recenzí (`Docs/Reviews/`), historie do 30. 9. v `Docs/HANDOFF.md` (archiv).

Stav k **1. 10. 2026 noc**: výkresy Wayfareru E-01 až E-08 schválené (revize C); revize D čeká na schválení s pilotem
kitu, který po 3 kolech kritika skončil FAIL 6,4 (5,4 → 5,9 → 6,4; recenze 2026-10-01_wayfarer_kit_pilot).

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
  - pilot kitu (hřbet, ramena, záď, gondoly): desky, rám T, páteř s kovovým hřebenem, rozvody v kanálu u páteře,
    větrací skříně (hřbet pole 08/12, záď), čísla desek ze znaků `pn_*`; trup 991 k trojúhelníků (limit 1 M);
  - chase kamera 2800 cm; level: slunce 11 lx, obloha 0,55; průchozí interiér (F vstát / sednout / ven / dovnitř);
  - interiér z kitu: technická chodba s výklenky komponent, přepážky s dveřmi, nákladový prostor (mřížka 8 SCU,
    varianta B; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou a nábytkem z kitu.
- **Steadfast** (nákladní): 2D návrh v2 čeká na schválení; starý odmítnutý interiér v `TestSpace` (klávesa I).
- **Interiérový kit** (`ArtSource/Kit/kit_rules.json`, `kit_parts.json`): dávky 1–3, 4 zčásti, 6 (nábytek kajuty);
  ukázka v `TestSpace` (U). Strop 500 + 3500 trojúhelníků na metr (autor 30. 9.; převezme `kit_manifest.json`).
- **Flotila:** Ship Matrix a dossiery publikované (skill `ship-pipeline` 1b); Delver a Farsight jen jako spec.
- **Nástroje:** `Tools/Test.ps1`, `Tools/Build.ps1`, CI s offline testy při každém pushi (stav přes veřejné API
  GitHubu), kritik s prahem `"gate": "step"` / `"ship"`, zámek `Tools/HeavyLock.ps1` (`CLAUDE.md`), snímky
  v `D:\gamespace-shots` (`shots:` v recenzích), `Tools/Cleanup.ps1` na konci kroku, Zen DDC v `D:\UnrealDDC`.

## Paralelní práce

- **Druhá session** (worktree `gamespace-audit`, větev `wayfarer-dossier-interior`): výkresy interiéru (bod 4, styl
  I-04 schválen 1. 10.) a koncepty (bod 6); `exterior_*.py` mění jen hlavní session. 0e7e4d4 sloučen do main 1. 10.;
  5894e97 (dveře hygieny, I-04 R1) jen ve větvi. Konflikt v `Drawings/*`: kterákoli strana, pak překreslit.
- **Hlavní session:** exteriérový kit. Druhá session balí do `Builds_<jméno>`; slučuje hlavní session.

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
- Loď bez podvozku u země stojí na neviditelném kořenovém boxu (řeší se, až bude vadit). Zvuky jsou procedurální
  zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc (soumrak a noc jen v presetu snímků).
- `compileall` hlásí `SyntaxWarning: invalid escape sequence` v docstringách šesti skriptů `Tools/Assets`.
- Neověřeno autorem ve hře: časování quantum skoku, HUD SC-1c mimo 1080p, chůze interiérem Steadfastu. Shipping
  build nikdy nezkoušen; v PIE Escape ukončí hru (menu je F10); debug HUD je anglicky.

## Další kroky

1. **Wayfarer – kit dál** (pilot FAIL 6,4 po 3 kolech, otevřené body v recenzi `2026-10-01_wayfarer_kit_pilot.md`,
   kolo 3): **musí** desky ramen S nečíst jako okna (světlejší a drsnější sekundární lak, panely / poklopy na S) a
   záď jako desky na rámu (pás AFT v rozvrhu); dále noc (trup se neztmaví ani s oblohou 0,03 – zjistit zdroj),
   přepálené červené světlo, tmavé výřezy na hřbetu, karty špíny v kanálech; **trysky jako krémové disky** (vnitřek
   s žebry a emisivním jádrem) v kroku gondol. Pak kit na celou loď. Druhá session: 4, 6.
2. **Loď na svahu:** přistání v `SpaceshipPawn` (odblokované); interiér: podlaha nákladu z kitu, body recenzí.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
