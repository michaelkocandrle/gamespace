# KF-COCKPIT-CONSOLE – levá konzole kokpitu jako díl továrny (7. 10. 2026)

Pilot nového postupu pro kokpit (autor 7. 10.: díly působí plasticky, „symplicitní pocit“). Konzole už není
vytažený `rr_slab` s jednotným zkosením v `hs_interior.py`, ale díl továrny `SM_Kit_Cockpit_Console12W_A`
(`Tools/Kit/kit_cockpit.py`) se sdílenými materiály továrny, dosazený v lodi přes `interior.kit_modules.run_parts`.
Rychlá smyčka ~4 min bez přestavby lodi: `kit_build factory --only` → `import_kit.py` → `Shots cockpit_audit -Editor`.

Brána `step` (průměr ≥ 6,5, žádná kategorie pod 6). Hodnotí se jen levá konzole v kokpitu.

| Kolo | Verze | Průměr | Hlavní výtky |
| --- | --- | --- | --- |
| 1 | v1–v2 | – | knipl a ovládací blok ne podle SC (autor) |
| 2 | v3 | 4,8 | plochá deska s kniplem; chybí zvednutá loketní jednotka, moduly, oranžové akcenty, legendy malé |
| 3 | v4 | 5,3 | silueta kvádru, tělo téměř černé, legendy nečitelné, C-lučík jako dráty |
| 4 | v5 | 5,5 | silueta pořád kvádr, legendy, opotřebení laku není vidět, prázdné desky, slabé podsvícení |
| 5 | v6 | 5,6 | stavový pás opravený; dál silueta, opotřebení, holé plochy modulů, legendy kláves, logo, ploché světlo |

## Co se změnilo

- **v4:** deska z rámovaných modulů ve spárách se šrouby (mřížka sání se žaluzií, stavový pás, 2×2 klávesy),
  loketní jednotka nad deskou na dvou konzolách, perforovaná opěrka zápěstí, oranžové šrafování základny kniplu,
  oranžový rámeček kolem červené klávesy a pás madla, světlá hlava kniplu, švy krytů na loketní jednotce.
- **v5:** nová role továrny `Kit_Console` (středně šedý lak sRGB ~0,31, `kit_materials.json`) pro tělo, moduly
  a klín čela – panelová šeď 0,19 v tlumeném kokpitu četla jako černá; mezera pod loketní jednotkou 4,5 cm;
  C-lučík jeden plochý pás na čepech; legendy stavového pásu nad proužky; kryt klávesy s bočnicemi a pantem.

- **v6:** loketní jednotka se zkosenými konci, vybrání v modulech se světlým ošoupáním hrany, větší legendy
  a stavové proužky, logo na vnitřním boku podstavce.

## Proč skóre stagnuje (po kole 5)

Kola 3–5 přidávají po 0,1–0,5 a kritik opakuje tytéž výtky: ploché světlo bez měkkého stínu, opotřebení laku
z masky továrny není v tlumeném kokpitu vidět, legendy decalů štítků jsou šedé (sdílený decal materiál lodi).
To nejsou vady jednoho dílu, ale systému (paměť `critic-systemic-not-local`). Další krok proto systémově:
1. světlo nad konzolemi (malé bodové světlo s měkkým stínem v kokpitu, `Wayfarer_setup.json`);
2. opotřebení `Kit_Console`/`Kit_Shell`: silnější a nepravidelná maska oděru, tmavší spáry a šrouby;
3. emisivní legendy kláves (podsvícené písmo, ne šedý decal);
4. pak silueta (kapsy v boku, podříznutí, patka) a teprve potom pravá konzole jako zrcadlo.

## Otevřené výtky (kolo 4–5) a reakce

1. Silueta kvádru (musí): zkosené čelo 25–30°, podříznutý vnitřní bok, kapsy v boku, odsazená patka – další krok.
2. Legendy (musí): decaly štítků jdou přes sdílený decal materiál lodi a čtou se šedě; potřeba světlejší
   varianta legend nebo emisivní legendy na klávesách – další krok.
3. Opotřebení laku (musí): oděr hran a špína ve spárách z masky továrny nejsou v kokpitu vidět – zesílit pro
   `Kit_Console`, přidat karty špíny do spár modulů.
4. Prázdné desky (musí): lem a vybrání modulů, logo Halcyon na boku loketní jednotky, ID panelů, šrafy.
5. Podsvícení kláves a proužků silnější (doporučeno).
6. C-lučík s plochou stranou a viditelnými čepy (doporučeno).

Listy a review.json: `2026-10-07_kf_cockpit_console_r2` … `_r4`.
