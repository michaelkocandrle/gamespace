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
| 6 | v6 v testovacím úseku | 5,0 | neutrální světlo odkrylo „bílý čistý plast“: materiály 4, holé plochy, silueta, lučík, legendy |
| 7 | B podle 2D návrhu | 5,5 | skladba návrhu ~65 %, vzhled ~30 %; jednolitý lak, černé kaňky, nízká věž, nesvítí |
| 8 | B | 5,6 | opěrka a knipl opravené; světlé skvrny po plochách, věž, legendy |
| 9 | B | 5,9 | světlo a čitelnost 6; materiál a decaly 5 (rám bez vložek, oděr hran) |
| 10 | B | 5,9 | skladba ~75 %, vzhled ~47 %; zbývá materiál, bok věže, kryt, decaly |
| 11–14 | B | 6,0 → 6,4 | čitelné decaly (DecalTint), čelo věže grafit s logem, rám nekovový lak |
| 15–18 | B | **6,5 → 6,8 PASS** | tmavší lak, odřené hrany; pak autor opotřebení zrušil |
| 19–20 | B | 6,4 | pokusy o oděr (mramor) – autor 8. 10.: díly jsou nové z výroby, bez opotřebení |
| 21–23 | B nový | 6,5 → **6,6 PASS** | lak pod čirým lakem, leštěné kovové hrany, matný grafit vložek, výstražný pás, rýhovaný návlek, druhá vrstva šablon |

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

## Kolo 6: hodnocení jako terminál (neutrální světlo, úhly referencí)

Preset `Tools/Shots/kit_cockpit_console_studio.json` (konzole v testovacím úseku kitu, záběry jako `konzole_3`,
`kreslo_1`, `konzole_1`, `kreslo_2`). FBX zrcadlí osu y: strana pilota je v úseku na +y. Kritik 5,0 FAIL.

**Zjištění:** tmavé světlo kokpitu skrývalo hlavní vadu – materiály. V neutrálním světle je loketní jednotka
(`Kit_Shell`, albedo 0,46) skoro bílá a matná, tělo (`Kit_Console` 0,31) světlé a čisté, bez oděru a špíny.
Albeda rolí továrny jsme v kokpitu zvedali, aby nebyly černé – tím jsme kompenzovali světlo materiálem. Správně
je to obráceně: albeda podle SC (kritik: loketní jednotka ~0,45–0,50 sRGB, tělo ~0,30 sRGB, patka ~0,12 sRGB,
tj. lineárně ~0,18 / 0,07 / 0,014), clear coat, šum drsnosti, oděr na kontaktních hranách – a jas kokpitu
dorovnat světlem kokpitu (systémový krok 3).

**Další krok:** kalibrace albed a opotřebení rolí továrny v neutrálním světle úseku proti referencím (měřit
pixely SC vs. naše na stejném typu plochy), pak tvar (silueta, holé plochy, lučík) a emisivní legendy; kokpit
se pak dosvítí.

## Varianta B (kola 7–10)

Díl `SM_Kit_Cockpit_Console12W_B` podle 2D návrhu (`Docs/Kit/parts/KF-COCKPIT-CONSOLE/part.md`), hodnocený sám
v neutrálním světle (preset `kit_cockpit_console_b`), snímek stavu `Docs/Kit/parts/KF-COCKPIT-CONSOLE/variant_b_v1.jpg`.

**Systémové opravy materiálu kitu** (platí pro všechny díly, výchozí hodnoty beze změny): oděr hran v pásmu podle
role (`wear_band_m`; kokpit 0–1 m – konzole pod 0,9 m dřív neměla oděr vůbec), `FaceWear`/`FaceDirt` v `M_Kit_Base`,
měřítko grunge na roli, vlastní barva a drsnost odhaleného kovu (`bare_colour`, `bare_rough` – hladký kov zrcadlil
tmavou místnost jako černé kaňky), ostrá zkosení `Part.sharp_deg`, svítící role `Kit_GlowKey`, `Kit_GlowAmber`.

**Otevřené (kolo 10, „musí“):**
1. Materiál: velké plochy jako grafitové vložky (albedo 0,08–0,12) ve světlém rámu všude; oděr hran na rámu
   výraznější (dnes jen na zkoseních, světlý a úzký) – nejspíš maska zakřivení/šířky v `M_Kit_Base`.
2. Bok věže: zapuštěný panel se spárou, šrouby, zkosení v polovině, znak // HALCYON.
3. Kryt EMER: nic nad horní hranou věže, nápis EMER pod krytem (knihovna má jen `ck_emerg_o2`).
4. Decaly: oranžový znak // na nosníku i věži viditelně, štítek HF-3287, škrábance kolem ovladačů, kontrastní
   spodní nápisy (decal `maker` má šedou 0,42 – chce světlejší variantu).
5. Svit: bloom kláves (emise 15–25 s tmavým rámečkem), větší legendy kolébek.

## Kola 11–23 a rozhodnutí autora (8. 10. 2026)

- **Opotřebení zrušeno** (autor): díly lodí jsou nové z výroby – lesklé, matné, naleštěné; detail z vrstvení decalů a
  textur (paměť `brand-new-parts-no-wear`). Kola 15–19 hledala oděr hran; nástroje z toho zůstaly (role hrany
  `Part.edge_roles`, `WearSharpness`, `BareMetallic`, pásmo oděru role), ale B je nepoužívá k oděru.
- **Systémové nálezy:** decaly kitu šedly (barevný decal lodi bez `DecalTint` → `MI_Kit_Halcyon_DecalPaint` 1,5×);
  zkosení 12 mm na 5–9 cm blocích zabírala půl boku (6 mm); díly kokpitu se importují načisto (`FRESH_PARTS`).
- **Materiály B:** `Kit_Frame` lak pod čirým lakem s pomerančovou kůrou (`T_Kit_OrangePeel_N`), `Kit_FrameEdge`
  leštěný kov na zkoseních, `Kit_Inset` hluboký matný grafit se zrnem (`T_Kit_Grain_N`), `Kit_Grip` rýhovaný návlek
  (`T_Kit_Knurl_N`), generátor `Tools/Kit/kit_paint_normals.py`.
- **Otevřené (kolo 23, doporučeno):** podpanely na boku nosníku a šikmém boku věže, opěrka ve dvou segmentech s lemem
  a zrnem kůže, třetí vrstva mikro šablon, LED kolébek v rámečku; horní tmavé plochy čtou pod stropním světlem úseku
  šedě (světlo, ne materiál).
