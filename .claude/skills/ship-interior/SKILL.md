---
name: ship-interior
description: Walkable ship interiors in gamespace - the project's own interior kit (Tools/Kit/*: kit_build.py batches, kit_geo, kit_rules.json, kit_parts.json, import_kit.py, showroom on key U), kit rooms inside a ship (interior.kit_modules in <Ship>_hs.json, hs_interior.py, Tools/Assets/kit_rooms.py, kit_layout.py, hull_fit), the walkable ship (WalkSeat/WalkRamp sockets, SetInteriorWalk, F to stand up/sit/leave), interior lights (SHADOWED_SOCKETS, InteriorOnly, MegaLights), materials, grime cards, decals and labels, cockpit glass/hologram/control modules, space.Kit*/space.Walk/space.Where console commands, measure_look targets and interior traps. Reference files: kit-design.md (kit design language, grid, sections, budgets) and steadfast-legacy.md (the old Steadfast interior pipeline). Load when adding or changing interior rooms, kit parts, props, decals, lights or materials, walking inside a ship, or fixing holes, flicker, grey checkerboard or wrong colours inside a ship.
---

# Interiér lodi

Aktuální stav interiérů (co je hotové, otevřené body, další krok): `Docs/CURRENT.md`. Vizuální předání: skill
`visual-review`. Historie dávek kitu a kol kritika: `Docs/Archive/skills/ship-interior_2026-09-30.md`.

Referenční soubory tohoto skillu (čti podle úlohy):
- `kit-design.md` – designový jazyk kitu, mřížka, průřezy S/N/W/T/L, pivoty, sockety, jména, texely, rozpočty,
  kolize, seznam dílů. Čísla platí jen v `ArtSource/Kit/kit_rules.json`.
- `steadfast-legacy.md` – starý zkušební interiér Steadfastu (`build_steadfast_interior.py`, `import_interior.py`,
  `M_KitTrim`, tagy, `test_interior.py`), klávesa I.

## Pravidla autora (závazná)

- **Nic nového do 3D bez schváleného 2D návrhu.** Pro každou loď technický list ve tvaru RSI Ship Matrix
  (`ArtSource/Ships/<Loď>/<Loď>_spec.json`), popsaný řez a půdorysy palub, kde má **každá místnost a každý předmět
  účel** (`Design/<Loď>_layout.json`). Výkresy `python Tools/Design/draw_ship_design.py <layout.json>`.
- **Styl SC:** teplá/neutrální tmavá architektura, světelné lišty, tmavý základ, **studené hologramové UI**. Styl,
  ne kopie jednoho obrázku. Paleta podle výrobce je v `kit_rules.json` (`palettes`), popis v `kit-design.md` §4.
- **Žádná výplň:** bedny, sudy, rekvizity „pro detail“ působí levně. **Klávesnice u dveří = no-go** (i jako
  displejový modul). Procedurální pult z kvádrů = „levná low-poly hra“, no-go.
- Sedadla a funkční díly procedurálně; AI geometrie v lodi ne (Meshy sedadlo vyřazeno 25. 9. 2026).
- **Žádná jména ze Star Citizenu** (lodě, firmy, stanice); naše: Halcyon Freightworks, Kestrel Dynamics, Veyra.
- Assety zdarma (licence!) nebo po dílech, nikdy celá sestava jedním promptem, žádné placené balíky (skill
  `asset-sources`).
- Posuzuje se **z první osoby** (oko ~1,65 m), snímky 1920×1080 (cíl výkonu 1440p / 60 fps, CLAUDE.md). Stylový záměr kroku patří do briefu kritika.
- Optimalizace až na konci, když je vzhled hotový (autor 29. 9. 2026).

## Kit: stavba dílů

```bash
python Tools/Kit/kit_trim_sheet.py          # trim sheet 4096x2048 @ 1024 px/m -> ArtSource/Kit/Textures (+ trim_index.json)
python Tools/Kit/kit_screens.py             # atlas obrazovek displejů (T_Kit_Screens.png)
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup \
    --python Tools/Kit/kit_build.py -- <walls|batch2|batch3|batch4|...> [--only <díly>] [--sections W,N] [--no-render]
python Tools/Kit/kit_catalog.py <dávka>     # katalogový list Docs/Kit/catalog_batch<N>.png
```
```powershell
.\Tools\run_editor_python.ps1 Tools\Assets\import_kit.py           # /Game/Kit + ukázka v TestSpace
.\Tools\Shots.ps1 -Preset kit_showroom2 -Editor -Width 1920 -Height 1080
```

- **Soubory:** `Tools/Kit/kit_geo.py` (třída `Part`: geometrie po rolích materiálů, zkosené boxy a desky, lisovaný
  panel, trubky, UV podle os, UV1 = ID panelu, barva vrcholů `Col`, UCX, SOCKET_), `kit_walls.py`, `kit_batch2/3/4/4b.py`,
  `kit_liner.py` (obložení trupu), `kit_build.py` (stavba, decaly přes `hs_decals.Placer`, export FBX, manifest,
  rendery). `kit_build.jobs()` drží úlohy všech dávek; `--only` postaví vybrané díly.
- **Výstupy:** `ArtSource/Kit/Kit_*.blend`, `ArtSource/Kit/Export/SM_Kit_*.fbx`, `kit_manifest.json` (rozměry,
  trojúhelníky proti rozpočtu, materiály, sockety v UE cm s parametry světel, kolize, `colour_masks`,
  `service_labels`), rendery `Saved/KitCatalog/`.
- **Nový díl:** rodina v `kit_parts.json` (chybějící díl z pilotu jako `pilot_needs`), rozměry z `kit_rules.json`,
  rozpočet trojúhelníků, sockety `SOCKET_Snap_*`, `SOCKET_Light_n` (typ, role, cd, dosah), `SOCKET_Decal_n`.
- **Decaly dílů:** `label(p, item, bod, normála, xdir, ydir)`; `xdir × ydir` musí být normála plochy, jinak `KITBUILD`
  hlásí „mirrored frame“ (WORKFLOW 9.6 ct). Servisní štítek jen u hardwaru, který pojmenovává, nikdy stejný na
  sousedních modulech (`import_kit.check_layout_labels` shodí import, hlídá `test_kit_showroom.py`). Štítek leží celý
  na okraji prolisu nebo celý v prohlubni (9.6 cm).
- **Oděr a špína z geometrie:** `kit_geo` dává barvě rohů G = 0 plochám z bevelu (`Part.edge_faces`); `Col` je v doméně
  rohů, `kit_build.join()` převede bodovou barvu decalů na rohy, export `colors_type="LINEAR"`; `kit_build` spadne,
  když masky nepřežijí (9.6 cq, cr).
- **Karty špíny:** díl deklaruje `Part.grime(kind, at, normal, up, size, alpha, wear=False)`, `kit_build.decals`
  kartu položí paprskem (`hs_decals.Placer.card_at`); `up` míří ke zdroji špíny. Záměr „udržovaná pracovní loď“:
  špína jen ve spárách, u soklu, kolem poklopů a madel, vyšlapaná linie, stékání pod mřížkami. **Na tmavém grafitu
  je špína světlejší matný prach** (tmavá není vidět, 9.6 dl), karty mělké 0,18 / 0,1 m (hlubší dělají opar, dm).
- **Materiály kitu:** role `Kit_Primary/Structure/Accent/Signal/Rubber` na `M_Ship_Layered` se statickým přepínačem
  `SurfaceDetail` (lodě ho mají vypnutý); trim na vlastním masteru `M_Kit_Trim` (ne `M_Ship_PBR`, 9.6 dd), kovové
  pruhy trimu s drsností ≥ 0,5 (de). Společné hodnoty `import_kit.SURFACE`, role v `layered(..., **detail)`.
  Lak je dielektrikum (`PaintMetallic` 0,1); kov konstrukce bez odrazů Lumenu nad ~0,5 splývá s panely.
- **UE (`import_kit.py`):** díly do `/Game/Kit/Meshes` funkcemi `import_ship` (bez Nanite), staré meshe se před
  importem mažou (reimport držel staré sockety), `MI_Kit_<Výrobce>_<Role>` v `/Game/Kit/Materials`.
- **Ukázka kitu** v `TestSpace` (0, −500, 0) m: `import_kit.SHOWROOM` (`wall_runs`, `run_parts`, `placed`,
  `prov_spots`, `prov_boxes`), tag `KitShowroom`, přestavuje se při každém importu; import spadne, když délky modulů
  nesedí na běh. Klávesa **U** / `space.Showroom [annex|stairs]` prochází ukázka → přístavba → hala → zpět.

## Nábytek z kitu (dávka 6, `Tools/Kit/kit_furniture.py`, 30. 9. 2026)

- `kit_build.py -- furniture`: lůžko `Furniture_Bunk21L_A`, skříň `Locker10L_A`, hygienická buňka `Hygiene15L_A`,
  výdejník `Food16L_A`; rozpočet `tri_budget.Furniture` 15 000 (lůžko ~11 tis.). Recenze
  `Docs/Reviews/2026-09-30_cabin_furniture.md`.
- **Pivot „faced“:** na podlaze pod středem zadní hrany, čelo +X, šířka +Y. V lodi `run_parts`
  `[[x, y], [dx, dy], [díl]]`: yaw podle směru, +Y dílu je směr otočený o +90°.
- **U obložení trupu (průřez L):** zadní hrana `WALL_GAP` 0,1 m od líce, nic nad `top_at(x)` (zkosení minus žebra
  8 cm, WORKFLOW 9.6 er); kontrola Blenderem headless `Tools/Kit/kit_clash.py -- <Loď> Furniture_`.
- **Polštáře** jako výšková plocha `pad()` (`kit_geo.Part.mesh`, sdílené vrcholy): zaoblený okraj, vyboulená pole,
  švy jako prohlubně, knoflíky (9.6 eu); normála tkaniny `Tools/Kit/kit_fabric_normal.py` → `T_Kit_Fabric_N`,
  `import_kit.py` ji dá na `MI_Kit_Halcyon_Cushion`.
- **Dveře a zásuvky** v poli zapuštěném za plochým rámem: `front_plate(..., press=DEEP)`, `DEEP = (0.035, 0.012, 0.006)`
  (trojice `inset` v `kit_geo.box`, 9.6 et); kování na rám nebo na dno pole.
- Popisky nábytku jsou šablonové nápisy (`generate_interior_decals.stencil`) v setupu lodi; na lisovaném poli střed
  decalu na čelo (9.6 ew). Soft-key popisky tlačítek patří na stránku displeje (`kit_screens.py`).

## Místnosti z kitu v lodi

- Recept `interior.kit_modules` v `<Loď>_hs.json` popisuje místnosti v metrech layoutu (x dopředu, y na levobok,
  z od paluby): `rooms`, `wall_runs` (začátek, konec, normála líce, moduly), `run_parts` (portály, stropy, podlahy,
  přepážky `Bulkhead_Door*` s pivotem v rohu na líci), `stand_in_floor`, `width` (šířka kit místnosti, průřezy
  L41/L38 obložení trupu), `keep` (co zůstává lodní: `floor`, `objects`, `fittings`), `light_scale`,
  přepínač `enabled`.
- `hs_interior.py` v místnosti z kitu postaví jen přepážky, tmavou vrstvu nad stropem a náhrady; objekty layoutu
  a decaly interiéru tam přeskočí. Nápisy setupu s `legacy_room` platí jen pro místnosti bez kitu
  (`kit_layout.active_rooms`, `decal_active`). Starý kit v receptu (`interior.kit`) se staví vždy, když ho recept
  má (9.6 ei).
- UE: `Tools/Assets/kit_rooms.py` (volá `import_kit.py` i `import_ship.py`) vloží díly do `BP_Ship_<Loď>` pod Hull
  jako `InteriorMod_NN_<díl>` a světla ze socketů jako `Light_fix_kit_NN`. Sdílená matematika rozmístění
  `Tools/Kit/kit_layout.py`: ship space = layout + `assemble.offset`, y v UE zrcadlené, yaw v Blenderu opačně.
- **Po změně:** `kit_build.py -- <dávka>` → `import_kit.py` → přestavba lodi (`hs_build_ship`, `hs_assemble_ship`,
  **`gamespace_ship_export.py`**, 9.6 eq) → `import_ship.py` / `kit_rooms.py` → `test_ship_geometry.py <Loď>` (díry, plovoucí díly, `hull_in_rooms`,
  `walk_blocked`, nápisy) → presety `wayfarer_rooms` a `wayfarer_walk`.
- Řez trupem se skutečnými díly: `Tools/Kit/hull_fit_kit_rooms.py` (Blender, pak `--draw`) →
  `Docs/Kit/hull_fit_<loď>_kit_rooms.png`; nákladový prostor `Tools/Kit/hold_fit.py`; plán místnosti
  `Tools/Kit/cabin_plan.py`, `hold_grid_plan.py`.

## Světla interiéru v lodi

- Každé svítidlo, lišta a linka má své světlo s krátkým dosahem; světla u svítidel `hs_fixture_lights.py`
  (recept `interior.fixture_lights`, `fix_N`), světla kitu ze socketů dílů.
- **Stín jen hlavní světla** (`SHADOWED_SOCKETS`: lineární ve žlabech, bodovky stropních panelů); ostatní kontaktní
  stíny, prosvětlení stěn ×0,5 (`SOCKET_SCALE`). Díly kitu ve světelném kanálu 1, světla v 0 a 1.
- Bodovky, svatozáře stropu (`Light_Halo`), wash stěn, výklenky a stavová světla jen v režimu interiéru
  (`INTERIOR_ONLY_SOCKETS`, tag `InteriorOnly`, `ASpaceshipPawn::InteriorOnlyLights`); v letu nesvítí (9.6 dz).
- Režim osvětlení interiéru (`ASpacePlayerController::ApplyInteriorLighting`, `SetInteriorLighting`, pro snímky
  s volnou kamerou `space.InteriorLighting 1|0`): MegaLights (2 vzorky na pixel), odrazy Lumenu varianta c (do drsnosti 0,32, ½ rozlišení; od 6. 10.), interiérové
  meshe mimo stíny slunce (9.6 dr, ds). MegaLights se předehřívají na startu levelu (`-NoMegaLightsPrewarm` vypne).
- Široká místnost (průřezy L41/L38): bodovka 50°, 260 cd se stínem, svatozář 6 cd neutrální, bodovky na stěny
  60 cd / 70° skloněné 22°, žlábek 0,5 cd/m, wash dolů po stěně 5 cd/m; kajuta tlumená `light_scale` 0,6 (9.6 em).
- Vnitřní světla nesou `specular` (výchozí 0,25; plný dělal bílé body na skle). Světlo displeje na okolí patří
  před sklo ve výšce jeho středu (9.6 bz). Každé nové světlo s měřením výkonu.

## Průchozí loď

- Sockety trupu z receptu `assemble.sockets`: `WalkSeat` (za křeslem na podlaze kokpitu, `rotate_z_deg` 180) a
  `WalkRamp` (v nákladovém prostoru u rampy). Loď s oběma je průchozí (`HasWalkInterior`).
- F v lodi: `LeaveSeat` (přistálá nebo pod 1 m/s), jinak `ExitShip`. Pěšky v lodi: u křesla (170 cm od socketu
  `Cockpit`) sednout, u rampy (220 cm) ven jen po přistání. Zvenku F u průchozí lodi = dovnitř po rampě.
- `SetInteriorWalk(true)`: trup `ECC_Pawn` Ignore, meshe Interior / InteriorKit / InteriorMod_* QueryOnly a blokují
  Pawn + Visibility, s lodí jede `ASpaceGravityVolume`. Kolize místností zatím po polygonech (`CTF_USE_COMPLEX_AS_SIMPLE`
  z importu); pravidlo kitu „UCX boxy, nikdy complex-as-simple“ se zavede s optimalizací na konci.
- Kapsle v lodi 56 cm × 1,80 m (`SetShipCapsule`), mimo loď 84 cm × 1,92 m. Oko 1,65 m nad podlahou.
- Kontrola `walk_blocked` v `test_ship_geometry.py`: kapsle každými dveřmi layoutu a přes schody; zavřené dveře
  v `checks.walk_exempt`; blokovaný střed dveří je chyba, okraje varování `walk_tight`. Pak preset `wayfarer_walk`
  a log (`space.Where`, `WALK end`, `sits down`). Nástrahy 9.6 eb (ploška v průchodu), ec (hlava na schodech),
  ed (přistání ve scénáři), el (trup těsně za lícem).

## Hráč v interiéru

- **První osoba výchozí a v lodích jediná** (`APlayerCharacter::SetFirstPerson`): `FirstPersonCamera` 165 cm nad
  chodidly, 14 cm před obličejem, FOV 90°, ±80°, hlava skrytá. **V pěšky** přepíná první/třetí osobu (3P jen na
  testy; v lodi je V coupled/decoupled).
- Gravitace: `APlayerCharacter::UpdateGravity` se ptá `ASpaceGravityVolume` dřív než planety.

## Konzolové příkazy (zabalená hra i scénáře snímků, nic se neukládá)

| Příkaz | Co |
| --- | --- |
| `space.Interior` | do interiéru Steadfastu a zpět (= I) |
| `space.Showroom [annex\|stairs]` | ukázka kitu (= U) |
| `space.Walk <vpřed> <vpravo> <s> [yaw]` | chůze jako držené klávesy; log `WALK end at …` |
| `space.Interact` | co teď dělá F (vstát, sednout, ven po rampě, dovnitř) |
| `space.Where` | chodec v lodi: poloha v souřadnicích lodi (cm), podlaha, čeho se kapsle dotýká |
| `space.FlatSpot [°] [km]` | loď nad nejbližší rovné místo (přistání pro scénáře chůze) |
| `space.Door 1\|0\|-1` | dveře otevřít / zavřít / automaticky |
| `space.InteriorLighting 1\|0` | režim osvětlení interiéru pro volnou kameru |
| `space.Kit <Param> <hodnota> [část jména MI]` | skalár materiálů interiéru a kitu (`Lift`, `WearAmount`, `GrimeAmount`, `DecalOpacity`…) |
| `space.KitColor <Param> R G B [jméno]` | barva materiálů (`Gunmetal`, `PrimaryColor`…) |
| `space.KitLight Work\|Accent\|All\|Showroom <Vlastnost> <hodn.>` | světla (`Intensity`, `IntensityScale`, `Temperature`, `CastShadows`…) |
| `space.KitReset` | materiály, světla, slunce a sky light zpět – **první příkaz každé varianty** |
| `space.LightList` | výpis světel |

Kód: `Source/gamespace/SpaceInterior.*`, `SpaceInteriorTuning.cpp`, `SpacePlayerController.*`, `SpaceshipPawn.*`
(průchozí loď). Ladit nejdřív za běhu ve scénáři, hodnotu pak zapsat do skriptu nebo receptu (+ test).

## Snímky a měření

`.\Tools\Shots.ps1 -Preset <x> -Editor` během kroku, `-Package` na konci. Volná kamera: `"camera": "free"`,
`camera_location` / `camera_look_at` v metrech; v prostoru lodi `camera_local` / `look_local` (m, X dopředu,
Y doprava, Z nahoru). `console` příkazy platí do konce běhu → varianty začínej `space.KitReset`.

| Preset | Účel |
| --- | --- |
| `wayfarer_rooms` | všechny místnosti Wayfareru z výšky očí |
| `wayfarer_walk` | průchozí Wayfarer: přistání, vstát, schody, kajuta, chodba, náklad, ven, dovnitř, zpět do křesla |
| `wayfarer_kit_corridor`, `wayfarer_perf` | chodba z kitu před/po; výkon 3× interiér, 3× let (`perf_log.py`) |
| `kit_showroom2`, `kit_annex`, `kit_bays`, `kit_material` | ukázka kitu, přístavba, výklenky, materiál |
| `sc_look` | 1080p, auto expozice; `python Tools/Shots/measure_look.py <složka>` |
| `flicker_check` | 8× stejná kamera; `python Tools/Shots/measure_flicker.py <složka> <mapa.png>` |

**Cílové rozsahy SC (interiér, auto expozice):** průměr 0,13–0,23, p50 0,08–0,18, p90 0,32–0,53, p99 0,56–0,88,
**B/R 0,72–1,05** (teplé), detail 0,024–0,035. Blikání < 0,1 % pixelů. Výkon měř v zabalené hře ve 1080p (skill
`unreal-shots-and-look`).

## Kontrola geometrie lodi

Před každým předáním `python Tools/Tests/test_ship_geometry.py [Loď]` (Blender headless, ~15 s, `GEOTEST SUMMARY … PASS`;
běží i sám na konci `hs_assemble_ship.py`). `Tools/Blender/check_ship_geometry.py`: zrcadlené decaly, plovoucí díly,
průniky za obložení a ven z trupu, `hull_in_rooms`, placeholder materiály, díry z oka a z kamer presetu
`<loď>_interior.json`, `walk_blocked`. Díly kitu dosadí sám (`add_kit_rooms`). Výstup `Saved/GeoCheck/`
(`GEOCHECK_DEBUG=1` = barevný render po objektech). Výjimky `checks.floating_exempt`, `checks.walk_exempt`.
Díry zavírá tmavý plášť `Int_HullSkin` a obložení (9.6 bm–bo).

## Kokpit a sklo (hs pipeline)

- Sedadlo je procedurální `hs_cockpit.pilot_seat` (skořepina, polstrované panely se švy, rádius hran 2,8 cm).
- Ovládací moduly: `hs_cockpit.control_module(g, c, right, up, n, w, h, rows, tree=)`; ovladače `guarded`,
  `guarded_red`, `rotary`, `rocker`, `button`, `encoder`, `led_w`, `led_o`, `led_blink`. Každý ovladač včetně LED
  má štítek `ck_*` (knihovna decalů, `hs_cockpit.LABELS`, klade `hs_interior_decals`); neumístěné štítky vypíše
  stavba jako `INTDECALS {"labels_failed": …}` → rozšiř modul.
- Decaly interiéru jako mesh decaly: `interior.decals` → `hs_interior_decals.py` (`items` paprskem, `scatter`
  mřížkou paprsků: `axis: "x"` = mřížka y×z, `axis: "z"` = mřížka x×y, `grab_bars`), part `InteriorDecals`.
- **Vrstvení decalů na kokpitu** (7. 10. 2026, podle `Docs/Kit/etalon/decal_stack.md`): z generátoru se klade
  `hs_cockpit.stencil(item, at, n, right, up, scale, max_w)` (libovolná položka knihovny: `rivet_row_*`, `slot_s`,
  `seam_*`, `socket`, `access_panel`, `st_*`, `hazard_subtle`, `corner_mark`, `tri_warning`, `panel_*`, opotřebení
  `edge_scuff`, `scratches`, `streak_short`) a `hs_cockpit.grime(at, n, up, (w, h), kind, alpha)` (karty špíny
  `smear` / `rim` / `streaks` / `soot` přes `Placer.card_at`). Rámec musí být pravotočivý: `right × up = n`, jinak
  se položka zrcadlí. Nápisy čtené z křesla: `right` = −Y (pravá ruka pilota), `up` = +X (dopředu). Pořadí vrstev:
  podklad (tón ≥ 0,08, variace drsnosti) → vnoření tvarem → střední detail → informace → opotřebení. Malá karta
  špíny na členité ploše ztratí buňky a s nimi krytí: dávej alfa 0,85–1 a kartu na rovnou plochu.
- Odraz skla podle kamery: `MPC_ShipView.InsideView` (1 = kamera v obálce partů `Interior*`), nastavuje
  `ASpaceshipPawn::UpdateViewCollection`; `M_Ship_Glass` míchá hodnoty zvenku a `…Inside`, uvnitř se vypíná
  `r.Lumen.TranslucencyReflections.FrontLayer.Enable`. Loď s interiérem má `pawn.hide_canopy_in_cockpit: false`
  (9.6 ca–cb).
- Hologram lodi = vnější obálka `hs_cockpit._envelope(bm, voxels=160, smooth=30)`, kanopa patří do obálky;
  `M_Ship_Holo` jednostranný (9.6 cc).
- Výtka „text na displeji useknutý z oka“: nejdřív odsazení stránky v C++, pak ray cast z `SOCKET_Cockpit` na body
  skla a výpis zasaženého objektu (9.6 bw).

## Nástrahy (příznak → příčina → oprava)

- **Černé přesně vodorovné plochy s `M_Ship_PBR`, triplanár jinde špatně promítnutý** → `(float3x3)` přetypování
  struktury `FDFMatrix`/`FDFInverseMatrix`; používej `DFToFloat3x3(...)`. Normálová mapa v Custom node je BC5 bez
  modrého kanálu, z dopočítat. Hlídá `test_material_hlsl.py`. (9.6 dg, dh)
- **Šedá šachovnice v zabalené hře** (v editoru OK) → materiál se nezkompiloval: chybí usage flag
  (`used_with_nanite`, `used_with_static_mesh`, `used_with_instanced_static_meshes`) nebo sampler bez výchozí
  textury. Hledej „Failed to compile Material“ v `%APPDATA%\Unreal Engine\AutomationTool\Logs\…\Log.txt`. (9.3 f)
- **Zevnitř díra / chybí strop** → UE kreslí jednostranně; díl lícem dovnitř, obložení nebo tmavý plášť; kamery
  snímků patří dovnitř. (9.3 h, i, q)
- **Blikání jen v pohybu** → dvě plochy v jedné rovině; měř `flicker_check`, maž jen skutečné kopie. Díly kitu se
  nepotkávají v jedné rovině. (9.3 p)
- **Nový materiál nečekaně svítí oranžově** → jméno obsahuje `light`/`screen` (starý import, 9.3 aa).
- **Světla svítí modře** → `unreal.Color(255, 238, 214)` je BGRA; jen keyword `r=, g=, b=, a=`. (9.5 e)
- **Světlo za stěnou** nic nesvítí; po přesunu dovnitř měř znovu. (9.3 l)
- **Pomalý interiér** → stíny lokálních světel (22 světel = 15 ms z 18); stín jen hlavní světla, interiér je
  pixel-bound. Stínové mapy slunce v interiéru 3,2–3,8 ms. (9.3 r, 9.6 dr)
- **Statické světlo za běhu nereaguje na `SetIntensity`** → příkazy píšou vlastnosti + `MarkRenderStateDirty()`. (9.3 j)
- **C++ nenajde herce v buildu** → label je jen editor; používej tagy. (9.5 h)
- **Kolize zůstala** → `set_collision_enabled()` se s levelem neuloží; `set_collision_profile_name("NoCollision")`. (9.3 t)
- **Sklo/hologram rozbitý** → průsvitné/aditivní materiály nesmí na Nanite; vlastní mesh, import vypne
  `nanite_settings`. `StaticMeshEditorSubsystem` headless = `None`. (9.3 u, o)
- **Pin materiálu se nepřipojil** → `Power` má `Base`/`Exp`, `TextureSample` pin `UVs`;
  `connect_material_expressions` jen vrátí False → používej `link()`, který chybu ohlásí. (9.3 w)
- **Headless UE Python:** `unreal.Rotator` jen keywordy; `spawn_actor_from_object` padá →
  `spawn_actor_from_class(StaticMeshActor)` + `set_static_mesh`; `rerun_construction_scripts` není →
  `UFUNCTION(BlueprintCallable)`. (9.5)
- **Blender bmesh:** `faces.new()` má nulovou normálu do `bm.normal_update()`, nové vrcholy index −1 do
  `bm.verts.index_update()`. (9.3 s)
- **Nápis zrcadlený po přestavbě** → v setupu chybí `flip_u`/`flip_v`; hlídá `test_decal_orientation.py` a
  `test_ship_import.py`. (9.6 dy)
- **Text v AI obrázku:** pevná mřížka („exact 4 by 4 grid, one element centered in each cell, black background“),
  políčka se řežou výpočtem. (9.3 z)
- **Příkazy scénáře drž idempotentní** (přepínač běžel dvakrát). (9.3 m)
- Assety načítané podle cesty musí být v `DirectoriesToAlwaysCook` (`/Game/Environments`, `/Game/Kit` …). (9.3 b)
- **Malý díl kitu drahý na trojúhelníky** → rámečky difuzorů na obou stranách, bevely se 2 segmenty, zaslepené
  průběžné trubky → `bezel_face`, `segments=1`, `caps=False`. Rozpočet stropu = `Ceiling_base` 500 + 3500 na metr
  (autor 30. 9. 2026). (9.6 en)
- **Kit podlaha v místnosti L** jen 1 cm pod líc obložení; lodní podlahu vypne `"floor"` mimo `kit_modules.keep`,
  mezeru u přepážky `stand_in_floor`; decal na podlaze `max_depth_cm` 1,5. (9.6 ep, eo)
- **Polštář nebo kování „plave“** → lisované pole je 6 / 12 mm hluboké → polštář 7 mm do panelu, kování na rám.
  **Karta špíny visí** → paprsek trefil tlačítko nebo rám před panelem. (9.6 es, et, ev)
