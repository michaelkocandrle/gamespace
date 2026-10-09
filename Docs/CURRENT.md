# Aktuální stav projektu

Jediný zdroj **aktuálního** stavu pod `CLAUDE.md`, **nejvýš 80 řádků**; hotové do stavu, podrobnosti do recenzí a commitů.

Stav k **3. 10. 2026**: Wayfarer postavený podle výkresů **revize G** (kritik po ověřovacím kole PASS 6,5); povrch trupu
je pro teď uzavřený; výkresy interiéru I-01–I-09 sloučené do main. **Cíl výkonu: 1440p / 60 fps s TSR**
(AMD RX 9070, `CLAUDE.md`; staré 20 ms na RTX 2060 neplatí); nic se neměří ani neoptimalizuje do konce.

## Stav

- **Hra:** zabalená Development hra (menu, pauza, nastavení); `TestSpace` s planetou Veyra (120 km), Keth a Orun.
- **Let podle SC** (master reference `starcitizenreference/`): SC-1a IFCS (coupled/decoupled, SCM/NAV, omezovač,
  G-Safe, ComStab, VJoy), SC-1b boost a afterburner, SC-1c letový HUD, SC-2a podvozek a precision, SC-2b VTOL,
  SC-3 značka dráhy letu, SC-4 quantum drive (cíl nosem, spool, kalibrace, tunel, příjezd). Ovládání: `README.md`.
  **Přistání na svahu** (3. 10.): loď stojí na třech patkách (rovina pod patkami, `TripodRest`), pohyb sweepuje vlastní
  kolizi trupu (UCX) místo kořenového boxu, `Obstructed` = trup by se dotkl terénu; `landing_slope`, README „On a slope“.
- **Menu a nastavení ve stylu SC 4.10** (4. 10., kritik PASS 7,4 / 7,5): karta HRÁT, záložky, ~35 položek, KLÁVESY.
- **Interakce podle SC** (4. 10., krok 1 z autorova záznamu, kritik PASS 6,5): ťuknout F = výzva u předmětu, podržet F =
  režim interakce (kurzor, MFD klikací), seznam kláves vpravo dole, hlášení a tipy (`README` „Interaction“).
- **Napájení lodi** (4. 10., kroky 2a/2b, kritik PASS 6,9): U nebo knoflík PWR, vypnuto = bez tahu a tmavý kokpit, náběh
  2,5 s; MFD CONFIGURATION s klikacími přepínači; vstávání za letu (loď zabrzdí); Alt+U = showroom (`README` „Ship power“).
- **Postava:** první osoba (V pěšky = třetí jen pro testy); sférická gravitace planety i umělá v lodi.
- **Wayfarer** (Halcyon Freightworks, malá multirole, 1 pilot) – jediná létající loď:
  - exteriér v2.1 přesně podle výkresu (`hs_build_ship`; ploutve 1,3 m potvrzené autorem, výška lodi 4,9 m), mesh
    decaly se šablonami jen u hardwaru, livrej, RCS, podvozek; kokpit v2 (skleněné MFD, hologram lodi, moduly);
  - povrch trupu v3 = **koncept B + C** (autor 1. 10.); data návrhu `Design/Wayfarer_exterior_design.json`, každý
    prvek stavby i návrhu má ID (`Tools/Design/assign_exterior_ids.py`), výkresy z modelu `exterior_model.py`;
  - pilot kitu trupu (desky, rám T, páteř, rozvody, poklopy, trysky `build_nozzle`); **rozpočet trojúhelníků** trup
    ≤ 700 k (`budget`, `HSBUDGET`, test; skill `ship-pipeline` 3b2b), dnes ~350 k;
  - chase kamera 2800 cm; level: slunce 11 lx, obloha 0,55; průchozí interiér (F vstát / sednout / ven / dovnitř);
  - interiér z kitu: technická chodba s výklenky komponent, přepážky s dveřmi, nákladový prostor (mřížka 8 SCU,
    varianta B; podlaha zatím lodní) a kajuta z obložení trupu s kit podlahou a nábytkem z kitu;
  - výkresy interiéru (`draw_interior_sheet.py`, `_deck.py`, `_plans.py`): **I-01 až I-04 schváleny jako vzor**, I-05 až
    I-09 jsou generovaná dokumentace bez dalších kol kritika (I-05 kokpit se kontroluje až u kokpitu z kitu).
- **Steadfast** (nákladní): 2D návrh v2 čeká na schválení; starý odmítnutý interiér v `TestSpace` (klávesa I).
- **Interiérový kit** (`ArtSource/Kit/kit_rules.json`, `kit_parts.json`): dávky 1–3, 4 zčásti, 6 (nábytek kajuty);
  ukázka v `TestSpace` (U). Strop 500 + 3500 trojúhelníků na metr (autor 30. 9.; převezme `kit_manifest.json`).
- **Továrna dílů** (6. 10.): `Docs/Kit/` soupis `catalog_draft.md`, etalon SC `etalon/etalon.md`, workflow
  `FACTORY_WORKFLOW.md` **v0.2**; **pilot 1 `KF-PORTAL-01`**: list rev. F, **krok 7–8 hotové** (výkon ~1 ms; kritik FAIL 5,2 po 3 kolech), STOP před krokem 9.
- **Flotila:** Ship Matrix a dossiery publikované (skill `ship-pipeline` 1b); Delver a Farsight jen jako spec.
- **Nástroje:** `Test.ps1`, `Build.ps1`, CI s offline testy (stav přes veřejné API GitHubu), kritik s prahem `step` /
  `ship` / `part`, zámek `HeavyLock.ps1`, snímky v `C:\gamespace-shots` (`shots:` v recenzích), `Cleanup.ps1` na konci kroku.

## Čeká na rozhodnutí autora

- **Továrna:** vrstvy decalů v2 (`Docs/Kit/etalon/decal_stack.md`), portál rev. G, úsek průchozí (kolize po členech);
  **inženýrský terminál** (F) a **servisní stěna rev. 2** (7. 10., PASS 6,75, `2026-10-07_kit_bay_service.md`): širší díl kvůli čtvercovým skříňkám?
- **Autor 5. 10. – věrná kopie SC podle referencí** (pak vlastní styl); pořadí v Dalších krocích, bod 0.
- **Kokpit v2** (4. 10.): C-01 schválen výchozími volbami (D průmyslový, zakouřené hologramy, HOTAS, krémové obložení –
  autor může změnit); hotové holoprojektory MFD (CK-HP-L/R) a vnitřní rám kanopy (CK-CF); dál HOTAS, konzole a ovladače, materiály, střed.
- Podpora života Wayfareru v2 pod lůžkem (I-04, R1); nábytek kajuty ve hře (FAIL 7/6/6/7/7/8/8/7); Steadfast v2, Kestrel.

## Známé problémy

- Podvozek, křídla a zbraně Wayfareru bez kitu; nohy bez odpružení (jeden mesh). Klesání (C) u země dopadá ~10 m/s.
  Snímek 11 `wayfarer_exterior_review` staví loď do svahu 32° (trup v terénu), chce `space.FlatSpot`. `DebugEngageQuantum`
  po zadání cíle jménem znovu vybírá cíl podle nosu lodi (drobnost, autor 1. 10.).
- Interiér Wayfareru: otevřené body recenzí `2026-09-30_cabin_furniture.md` a `2026-09-30_cabin_liner.md`.
- **Odrazy kovu:** varianta c zapnutá v celé hře (autor 6. 10.; interiér Lumen do drsnosti 0,32, ½ rozlišení; RX 9070 +0,6–1,4 ms).
- Kit: vyšlapaná linie potřebuje směrovou buňku atlasu špíny, špína v kanálech dlouhou úzkou buňku (krok c); ohmatání
  madel; lišty stropu po segmentech. Rozvody S na zadním konci (x 3–4) dělají ohyb přes pole bez desky.
- **Determinismus stavby na později** (WORKFLOW 9.6 ff): šum ±40 trojúhelníků, 3 FBX, import ukládá ~150 assetů; shluky
  decalů trupu občas mezi dvěma přestavbami poskočí (`test_kit_decals`; 7. 10. jednou, další přestavba prošla).
- Hřebenový terén vypnutý; kameny bez kolize; zvuky lodi z ElevenLabs (boost/quantum/UI procedurální); quantum tunel, TSR jiskry, displeje bez mipmap, duchy čísel.
- Neověřeno autorem: quantum skok, HUD SC-1c mimo 1080p, chůze Steadfastem; Shipping nezkoušen; PIE Escape končí hru.

## Další kroky

0. **Autor 9. 10. – pořadí:** (1) kokpit **good enough** (9. 10.; postup ve skillu `sc-quality-interior`); (2) **zvuky znovu**: 9. 10. 11 zvuků podle autorova výběru na
   sound boardu (`sound_candidates.py`, `sound_board.py`), klik v interakci = SW_ButtonPress – čeká na poslech ve hře; (3) exteriér Wayfareru doladit;
   (4) drobnosti interiéru zbytku lodi, dveře, přenesení centrální MFD obrazovky, animace.
   Kokpit 9. 10.: v4 konzole (koncept B), MFD v5 všude, trim v2 s tóny, mesh decaly, rozvody, skořepina křesla,
   strmější schody (průchod za křeslem; `Tools/Blender/cockpit_walk_map.py`); kritik r4 6,0 (`…_cockpit_v4_r4.md`).
   c) detail všech předmětů na úroveň SC (hasičák, skafandr, dveře, nic z prostých tvarů) a celá loď (stěny, podlaha,
      strop, profily) ve stylu stropu chodby (paměť `sc-level-detail-everywhere`); rampa: plán a rozhodnutí A/B
      čeká na autora (`2026-10-06_ramp_plan.md`).
1. Povrch trupu zmrazený (revize G, PASS 6,5); přistání na svahu čeká na vyzkoušení autorem (pak odpružení nohou).
3. Podle SC (`OwnCapture_Gameplay_Notes.md`): dál visor pěšky, systémy lodi, stanice.
4. **Optimalizace až na konci**, až bude vzhled hotový (autor 29. 9.); pak i odrazy kovu (varianta c).
