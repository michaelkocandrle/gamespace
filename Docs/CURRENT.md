# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu pod `CLAUDE.md`, **nejvýš 80 řádků**; hotové do stavu, podrobnosti do recenzí a commitů.

Stav k **3. 10. 2026**: Wayfarer postavený podle výkresů **revize F** (kritik PASS 6,5); revize G schválena s úpravami
(krok 2 a 3 zadání 3. 10.); výkresy interiéru I-01–I-09 sloučené do main. **Cíl výkonu: 1440p / 60 fps s TSR nebo DLSS**
(RTX 5070 Ti, `CLAUDE.md`; staré 20 ms na RTX 2060 neplatí); nic se neměří ani neoptimalizuje do konce.

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
    varianta B; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou a nábytkem z kitu;
  - výkresy interiéru (`draw_interior_sheet.py`, `_deck.py`, `_plans.py`): **I-01 až I-04 schváleny jako vzor**, I-05 až
    I-09 jsou generovaná dokumentace bez dalších kol kritika (I-05 kokpit se kontroluje až u kokpitu z kitu).
- **Steadfast** (nákladní): 2D návrh v2 čeká na schválení; starý odmítnutý interiér v `TestSpace` (klávesa I).
- **Interiérový kit** (`ArtSource/Kit/kit_rules.json`, `kit_parts.json`): dávky 1–3, 4 zčásti, 6 (nábytek kajuty);
  ukázka v `TestSpace` (U). Strop 500 + 3500 trojúhelníků na metr (autor 30. 9.; převezme `kit_manifest.json`).
- **Flotila:** Ship Matrix a dossiery publikované (skill `ship-pipeline` 1b); Delver a Farsight jen jako spec.
- **Nástroje:** `Test.ps1`, `Build.ps1`, CI s offline testy (stav přes veřejné API GitHubu), kritik s prahem `step` /
  `ship`, zámek `HeavyLock.ps1`, snímky v `C:\gamespace-shots` (`shots:` v recenzích), `Cleanup.ps1` na konci kroku.

## Paralelní práce

- Větev `wayfarer-dossier-interior` (682ed1f) sloučená do main 3. 10. (výkresy I-01–I-09, oprava dveří hygieny v kitu:
  FBX v repozitáři, do UE se dostane `import_kit.py` při příští přestavbě). Druhá session teď nic nemá.

## Čeká na rozhodnutí autora

- Podpora života Wayfareru v2: posunutá k ose, z většiny pod lůžkem (list I-04, řez R1; po sloučení `import_kit.py`).
- **Na kokpit z kitu** (mimo rozsah 3. 10.): ~40 štítků ovladačů kokpitu v datech, hustota světel kokpitu 3,9/m²
  proti pravidlu 2–3, texty layoutu (ulička 1,25 vs 1,40; „0,35 m“), dveře DR-TEC-CAB do kajuty s odsazením 78–90 mm
  a přesun položek na stěně.
- Nábytek kajuty: posouzení ve hře (kritik po 3 kolech a ověření FAIL 7/6/6/7/7/8/8/7, levné body opravené).
- Steadfast: schválení 2D návrhu v2 (`Steadfast_Design.md`); kanopa Wayfareru (téma v2), paleta Kestrel Dynamics.

## Známé problémy

- Podvozek, křídla a zbraně Wayfareru zatím bez kitu. Loď na svahu leží trupem v terénu.
- `DebugEngageQuantum` po zadání cíle jménem znovu vybírá cíl podle nosu lodi (drobnost, autor 1. 10.).
- Interiér Wayfareru: otevřené body recenzí `2026-09-30_cabin_furniture.md` a `2026-09-30_cabin_liner.md`.
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

1. **Wayfarer – revize G s úpravami čeká na potvrzení** („G s úpravami potvrzeno“): pás K panel + poklop na 8/14 desek
   (výběr a uspořádání podle ID), 5 větracích skříní K04, K09, L12, U13, L14, popisky desek mimo panely; HSBUDGET
   453 565 → 459 621 (dočasná stavba; strop 700 k); znaky `pn_K/U/N` v atlasu decalů. Výřezy `2026-10-03_wayfarer_sides_revG/`
   04–05. Pak krok 3: přestavba, snímky chase a zblízka, kritik step (Opus), srovnání se `starcitizenreference/`.
2. **Loď na svahu:** přistání v `SpaceshipPawn` (odblokované); interiér: podlaha nákladu z kitu, body recenzí.
3. **Let podle SC:** zbytek HUD a MFD (SC-3), mapa systému a doplňování quantum paliva (SC-4), přetížení (SC-5),
   systémy lodi a power triangle (SC-6). Každou fázi potvrdit s autorem.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
