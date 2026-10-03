# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu (nad ním jen `CLAUDE.md`), **nejvýš 80 řádků** (autor 30. 9. 2026). Hotové do stavu,
splněné smaž; podrobnosti do commitu a recenzí (`Docs/Reviews/`), historie do 30. 9. v `Docs/HANDOFF.md` (archiv).

Stav k **2. 10. 2026 večer**: pilot kitu Wayfareru **hotový** (krok d, kritik PASS 6,6); noc opravena stínem planety (3. 10.);
výkresy v **revizi E** čekají na schválení (schválená D). Nový PC autora.

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
    větrací skříně (hřbet pole 08/12, záď), čísla desek ze znaků `pn_*`; krok c: desky S s panely, poklopy a rozvody,
    světlejší matnější sekundární lak, záď jako desky P-S-A na rámu FR-AFT; **rozpočet trojúhelníků** schválen (trup
    ≤ 700 k, `budget` v receptu, `HSBUDGET`, test; skill `ship-pipeline` 3b2b): po kroku d 350 k (dřív 987 k);
    krok d: trysky (`build_nozzle`, E-05 detail G: límec, zvon s prstenci a žebry, hrdlo, středové těleso na táhlech,
    oranžové jádro podle tahu), gondoly 140 k → 59 k;
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

- **Revize E výkresů** E-01 až E-08 (krok d, detail G trysky na E-05): schválení.
- Nábytek kajuty: posouzení ve hře (kritik po 3 kolech a ověření FAIL 7/6/6/7/7/8/8/7, levné body opravené).
- Steadfast: schválení 2D návrhu v2 (`Steadfast_Design.md`). Kanopa Wayfareru jako téma designu v2 (autor otevře
  sám); paleta Kestrel Dynamics u první lodi Kestrelu.

## Známé problémy

- Exteriér Wayfareru mimo pilot (podvozek, křídla, zbraně) čeká na kit celé lodi. Loď na svahu leží trupem v terénu.
- `DebugEngageQuantum` po zadání cíle jménem znovu vybírá cíl podle nosu lodi (drobnost, autor 1. 10.).
- Interiér Wayfareru: otevřené body recenzí `2026-09-30_cabin_furniture.md` a `2026-09-30_cabin_liner.md`.
- PC autora: RAM s EXPO 6000 padala (BSOD, chyby v testu paměti); od 3. 10. běží na 4800 bez chyb (WORKFLOW 9.6 fm).
- **Odrazy kovu odložené na optimalizaci** (autor 30. 9.): odrazy Lumenu do drsnosti 0,32 za +1,3 ms.
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny, špína v kanálech dlouhou úzkou buňku (krok c); ohmatání
  madel; lišty stropu po segmentech. Rozvody S na zadním konci (x 3–4) dělají ohyb přes pole bez desky.
- **Determinismus stavby na později** (WORKFLOW 9.6 ff): šum ±40 trojúhelníků, 3 FBX, import ukládá ~150 assetů;
  náhodné decaly už na pořadí stavby nezávisí (9.6 fl, test v `test_kit_decals.py`).
- Hřebenový terén vypnutý (kamera po přistání pod zemí); kameny bez kolize. Quantum tunel méně „mléčný“, TSR
  čáry podél jisker; displeje bez mipmap (pod ~1600 px písmo zrní), duchy čísel.
- Loď bez podvozku u země stojí na neviditelném kořenovém boxu (řeší se, až bude vadit). Zvuky jsou procedurální
  zástupci; jas oblohy je odhad; obloha v atmosféře nerozlišuje den a noc (soumrak a noc jen v presetu snímků).
- Neověřeno autorem: časování quantum skoku, HUD SC-1c mimo 1080p, chůze Steadfastem; Shipping build nezkoušen; v PIE
  Escape ukončí hru (menu F10); debug HUD anglicky; `compileall` SyntaxWarning v šesti skriptech `Tools/Assets`.

## Další kroky

1. **Wayfarer – kit na celou loď** (autor 2. 10.: rovnou po opravě noci). Otevřené body kritika kola 4 (`…_kit_pilot.md`, krok d):
   jádro trysky bledé v zabalené hře, tepelný límec, variace laku, černé výřezy hřbetu, šablony. Paralelní session
   I-01–I-09 (bez Unrealu / Blenderu / balení) smí běžet.
2. **Loď na svahu:** přistání v `SpaceshipPawn` (odblokované); interiér: podlaha nákladu z kitu, body recenzí.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
