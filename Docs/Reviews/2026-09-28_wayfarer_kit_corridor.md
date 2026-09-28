# Recenze: pilotní chodba Wayfareru z kitu (krok 7.1 zadání kitu, 28. 9. 2026)

Zadání autora (28. 9., po kroku „špína“, místo dávky 4):
1. Ověřit, že se průřezy kitu vejdou do trupu Wayfareru bez změny siluety, a ukázat řez trupem s průřezem uvnitř.
2. Postavit pilotní chodbu Wayfareru jen z dílů kitu přes layout. Srovnat ji ze stejných pozic se současnou chodbou
   a s referencí SC, změřit FPS a udělat kolo kritika. Chybějící díly zapsat jako obsah dalších dávek.

## Bod 1: průřezy kitu v trupu

- **Obálky průřezů** (26. 9., přepočítáno dnes na aktuálním trupu se stejnými čísly):
  [`Docs/Kit/hull_fit_wayfarer.png`](../Kit/hull_fit_wayfarer.png).
  - Nákladový prostor: N i W s rezervou +0,09 m.
  - Technická chodba: N +0,35 m, W +0,33 m.
  - Kajuta: N +0,28 m, W +0,23 m.
  - Kokpit: kit se nevejde (−0,69 / −0,93 m), dostane vlastní díly.
  - Místnost s profilem W se na mřížce vejde nejvýš 3,0 m (náklad), 3,3 m (chodba) a 3,0 m (kajuta).
- **Skutečné díly kitu v trupu** (nové): [`Docs/Kit/hull_fit_wayfarer_kit_rooms.png`](../Kit/hull_fit_wayfarer_kit_rooms.png),
  `Tools/Kit/hull_fit_kit_rooms.py`. Díly pilotní chodby jsou rozmístěné stejnou matematikou jako ve hře a řez je
  vede po 0,3 m.
  - Nejmenší mezera mezi dílem kitu a vnitřkem trupu je +0,29 m (horní roh portálu, x 8,35).
  - Kanál pod roštem má +0,39 m, ostatní stanice +0,52 m.
  - Nic netrčí a exteriér se nemění: výkres exteriéru vyšel po úpravě layoutu bitově stejný.
- Test geometrie lodi (`test_ship_geometry.py`) teď díly kitu do lodi dosadí sám. Průnik trupem: 0.

## Bod 2: co se postavilo

**Místnost:** technická chodba (layout x 8,2–10,34), mezi přepážkami 2,1 m. Průřez W je vycentrovaný.
- Portál A na zadním konci rámuje dveře z nákladového prostoru.
- Stěny 1,8 m:
  - levobok: mřížka 1,2 m (reaktor) a mřížka 0,6 m (chladič);
  - pravobok: poklop 1,2 m (generátor štítů) a mřížka 0,6 m (chladič).
- Strop: dva kabelové žlaby se světlem.
- Podlaha: deska 1,2 m a rošt nad kanálem před chladiči. Pod portálem je náhradní pás, deska 0,3 m pro W chybí.

**Úpravy layoutu** (klíče `_kit` v `Wayfarer_layout.json`, výkresy překreslené; čeká na schválení autorem):
- **Dveře z nákladového prostoru** posunuty z y 1,2 na y 0,5, šířka 1,0 m. Ve schváleném plánu ústily přímo na bok
  reaktoru (y 1,05–1,85 od x 8,35) a volných zbývalo 0,4 m. Teď jsou uvnitř průchodu mezi komponentami i průřezu W.
- **Přepážka ke kajutě** posunuta o 6 cm (10,40 → 10,34), aby 2,1 m sedělo na mřížku kitu 0,3 m.

**Pipeline:**
- **Recept:** `interior.kit_modules` v `Wayfarer_hs.json`.
- **Blender:** `hs_interior` v místnosti z kitu postaví jen přepážky, tmavou vrstvu nad stropem a náhradní podlahu.
  Objekty layoutu a decaly tam přeskočí.
- **UE:** `Tools/Assets/kit_rooms.py` vloží díly do `BP_Ship_Wayfarer` jako komponenty `InteriorMod_*` bez kolize
  a 12 světel `Light_fix_kit_*`, která pawn zapíná s kamerou uvnitř. Světla nemají stíny, stejně jako ostatní
  svítidla lodi.
- **Volání:** `kit_rooms.py` volá `import_kit.py` i `import_ship.py`.
- **Sdílená matematika:** `Tools/Kit/kit_layout.py`.
- **Oprava kitu nalezená testem geometrie lodi:** tmavé výklenky za otvory mřížek a poklopů visely 1cm deskou ve
  stěně a kolem zůstávala škvíra. Teď sahají až k zadní stěně modulu (`RECESS_BACK`).
- **Nápisy:**
  - projekce reaktoru, napětí a chladiče ze setupu lodi zrušené (mířily na staré objekty);
  - ENGINEERING přesunutý nalevo od posunutých dveří;
  - COCKPIT zmenšený, aby se vešel na svislou část stěny kitu.

## Srovnání ze stejných pozic

List [`2026-09-28_wayfarer_kit_corridor/compare_before_kit_sc.jpg`](2026-09-28_wayfarer_kit_corridor/compare_before_kit_sc.jpg):
současná chodba | chodba z kitu | reference SC (jiné lodě). Preset `wayfarer_kit_corridor`, před
`Saved/Shots/20260928_114357_…`, po `Saved/Shots/20260928_171009_…` (zabalená hra).

| Pohled | Jas před → po | Detail před → po | B/R po |
|---|---|---|---|
| dopředu ke kajutě | 0,14 → 0,26 | 0,017 → 0,028 | 0,75 |
| dozadu k nákladu | 0,10 → 0,23 | 0,015 → 0,034 | 0,74 |
| vstup z nákladu | 0,11 → 0,17 | 0,014 → 0,018 | 0,74 |
| stěna s reaktorem | 0,07 → 0,20 | 0,012 → 0,025 | 0,73 |

SC: jas 0,13–0,23, detail 0,024–0,035, B/R 0,72–1,05. Pohled dopředu zesvětluje osvětlená kajuta za dveřmi.

## Výkon (zabalená hra, 1920×1080, RTX 2060, výchozí kvalita)

| Pohled | Před | Po |
|---|---|---|
| Technická chodba (osvětlení interiéru, MegaLights) | 17,5 / 18,3 ms (55 FPS) | 19,0 / 19,6 ms (51 FPS) |
| Nákladový prostor (preset `wayfarer_interior`) | 18,0 / 19,2 ms | 19,4 / 20,2 ms |
| Ke dveřím technické chodby | 18,7 / 19,6 ms | 19,5 / 20,3 ms |
| Kajuta | 18,3 / 19,0 ms | 18,8 / 19,5 ms |
| Kokpit (pilot) | – | 16,0 / 16,7 ms (60 FPS) |

(GPU / snímek.) Světla kitu se stíny (jako v showroomu) stála 10–24 ms: 42 ms u dveří, 1676 draw callů místo 673,
protože loď se létá bez MegaLights a každé světlo kreslilo stínovou mapu. Proto jsou v lodi bez stínů a se zesílením
×1,1 místo ×2,0 (bez stínů byl jas 0,32).

## Kolo kritika – FAIL, 6/4/5/6/5/6/6/5 = 43

Výstup [round1/critic.md](2026-09-28_wayfarer_kit_corridor/round1/critic.md), snímky `Saved/Shots/20260928_164015_…`
(rychlá smyčka). Podle zadání 7.1 jedno kolo. Body „musí“ jsou chybějící díly kitu, ne chyby pilota.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Reaktor a chladič nejsou čitelné, za mřížkou jen černo | musí | Souhlas. Chybí díl: výklenek komponenty s viditelným jádrem, západkami, popiskem a světlem → nová rodina `Wall_ComponentBay` (dávka 4). |
| 2 | Prázdná pole mezi žebry: bez madel, skříněk, přípojek | musí | Zčásti souhlas. Stěny chodby jsou tu komponenty (bod 1). Madla (`Fitting_Handrail`, dávka 6) a žlaby vedené k reaktoru (`Cable_Run`/`Pipe_Run`, dávka 7) chybí. |
| 3 | Materiál jako jednolitý plast, bez špíny u mřížek | musí | Neopraveno: materiály jsou ze schválených kroků kitu. Bez stínů je světlo v lodi plošší a rozdíly laku a kovu se méně čtou. Prach u mřížek je na zmenšeném listu slabý (viz recenze kroku „špína“). Otevřené. |
| 4 | Přepálená skvrna na černé přepážce (list 03) | musí | Mimo kit: přepážka a světlo jsou ze starého nákladového prostoru. Zapsáno k `Bulkhead_Door` (dávka 4). |
| 5 | Světlo bez svítidel v pouzdrech a kuželů | musí | Souhlas, systémové: pouzdra svítidel jsou dávka 8. V lodi navíc bez stínů. |
| 6 | Napojení na okolní prostory (přepážky, dveře) | doporučeno | Podle briefu dávka 4 (`Bulkhead_Door` s dveřmi mimo osu). |
| 7 | Šipky cedulí míří od dveří | doporučeno | ENGINEERING opraveno (nalevo od dveří). COCKPIT se nalevo nevejde, dveře kajuty jsou u levoboku a místo zabírá žebro stěny. Zapsáno k `Fitting_Sign`: šipky pro obě strany dveří. |
| 8 | Malé popisky nečitelné | doporučeno | Popisky komponent patří k `Wall_ComponentBay`. |
| 9 | Podlaha bez roštů a spár | doporučeno | Opraveno: rošt nad kanálem před chladiči. |
| 10 | Strop jako plochá deska | doporučeno | Opraveno: dva kabelové žlaby po celé délce. |

Po opravách 9 a 10 a cedulí žádné další kolo (zadání 7.1: jedno kolo). Snímky po opravách jsem zkontroloval sám.

## Chybějící díly (zapsáno v `ArtSource/Kit/kit_parts.json`, klíč `pilot_needs` a nové rodiny v dávce 4)

- `Wall_ComponentBay` (nová, dávka 4): výklenky komponent S1 – reaktor (mřížové dveře, kolejnice, REACTOR S1 / HIGH
  VOLTAGE), chladič (žebrované jádro, vývod ke kořeni křídla), generátor štítů (poklop se západkami). Hloubka ~0,5 m.
- `Bulkhead_Door` (dávka 4): dveře mimo osu průřezu (parametr polohy), líc navazující na sokl, sklon a lištu stěn kitu,
  vejde se do portálu. Nahradí procedurální přepážky lodí.
- `Floor_Plate` 0,3 m pro W (dávka 3): 2,1 m mezi přepážkami nejde pokrýt deskami 0,6/1,2.
- `Fitting_Sign` (dávka 6): cedule na svislý pás stěny (pod 1,3 m v W), šipky pro obě strany dveří.
- `Stair_Flight` 1,15 m (vyvýšený kokpit) a `Stair_Ramp` 22°/1,6 m (rampa Wayfareru).
- `Wall_HullLiner` (nová, dávka 4, **otázka pro autora**): nákladový prostor potřebuje 8 SCU (2,5 m) + uličku
  1,25 m = 3,75 m, ale W místnost se tam vejde nejvýš 3,0 m. Buď tenké obložení podél trupu, nebo 6 SCU / užší ulička.
- Mimo díly: chození po lodi (kolize kitu v lodi, gravitace, vstup), dveře s křídly.

## Rozhodnutí autora a práce po nich (28. 9. 2026 večer)

**Vodorovné čáry v řezu trupem:** nejde o geometrii v chodbě. Každá stanice se kreslí do panelu ±2,46 m,
křídla sahají do y ±7,3 m a bez ořezu se jejich řez (s pody a šachtami podvozku) kreslil přes interiér sousedních
panelů. V datech řezu na x 9,85 není uvnitř chodby (|y| < 1,15 m, výška 0,3–2,0 m) ani jedna úsečka trupu, stěny trupu
jsou na y ±2,3 m. Oba výkresy mají ořez (`clip_y`) a jsou překreslené. Autor měl ale pravdu, že test „průnik“ tohle
nehlídal (jen díly interiéru mimo trup): nová kontrola `hull_in_rooms` hledá exteriér (trup, kanopa, podvozek)
ve volném prostoru každé místnosti kromě kokpitu. Wayfarer: 0; negativní test (místnosti záměrně za trupem) ji chytí.

**Nákladový prostor 8 SCU:** s tenkým obložením se vejde (viz dokument lodi, `Docs/Kit/hold_fit_wayfarer.png`).

**Layout:** posun dveří a přepážky schválen, zapsáno v layoutu, dokumentu lodi a dossieru. Snímek ze strany
nákladového prostoru (`hold_to_door`): dveře se s uličkou kryjí jen 0,35 m – návrh úpravy čeká na autora.

**Přepínač:** `interior.kit_modules.enabled` (recept lodi) je vypnutý: technická chodba je zase ze starého kitu
s reaktorem a chladiči (jejich projektované nápisy mají `legacy_room: "tech"`), `kit_rooms.py` nechá loď bez dílů
kitu. Zapnutí = `true`, přestavba lodi a import. Pravidlo v `Tools/Kit/kit_layout.active_rooms`.

**Cedule ENGINEERING:** nalevo od dveří, pod sklonem stěny, celá ve vstupním pohledu.

**Světlo a výkon chodby z kitu:**
- stíny jen hlavní světla (lineární ve žlabech), ostatní bez stínů s kontaktními stíny 0,05;
- prosvětlení stěn na poloviční sílu;
- díly kitu ve světelném kanálu 1 (slunce do chodby uvnitř trupu nedosvítí), světla kitu v kanálech 0 a 1;
- **hlavní úspora – C++:** stínové mapy slunce stály 3,2–3,8 ms, i když uvnitř trupu slunce nic nevidí. Kreslily se do
  nich interiérové meshe lodi (bez Nanite). V režimu osvětlení interiéru (MegaLights) je pawn lodi vyřadí ze stínů
  slunce (trup místnosti zastíní dál) a stínovaná světla kitu vrhají stín jen tehdy; v letu je všechno jako dřív.

| Zabalená hra, GPU | před | po |
|---|---|---|
| chodba z kitu, režim interiéru | 18,98 ms | **16,51 ms** |
| chodba z kitu, osvětlení jako v letu | 26,3 ms (všechna světla se stíny) | 19,7 ms |
| současná chodba, režim interiéru | 17,49 ms | **15,12 ms** |
| současná chodba, osvětlení jako v letu | – | 19,1 ms |
| pohledy do interiéru v letu (náklad, dveře, kajuta) | 18,0–18,7 ms (ráno) | 18,8–19,5 ms |
| kokpit | – | 16,1 ms (59–61 FPS) |

Cíl „chodba pod 16,6 ms“ je v režimu interiéru splněný těsně (16,51). Další páka, kterou jsem nezapnul: MegaLights
se 2 vzorky na pixel (−0,6 až −0,7 ms, víc šumu). Stěny chodby z kitu pod sklonem jsou se stínovanými stropními
světly tmavé (jas 0,08): přímé světlo tam přes převis nedosvítí – řeší svítidla v pouzdrech (dávka 8).
