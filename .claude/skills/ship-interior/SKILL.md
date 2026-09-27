---
name: ship-interior
description: Building and tuning walkable ship interiors (the Steadfast interior) - Tools/Blender/build_steadfast_interior.py (rooms, MESHY_PROPS, DECALS, Interior_layout.json), Tools/Assets/import_interior.py (M_KitTrim, M_KitHolo/Glass/Leather, M_Decal, lights, ASpaceSlidingDoor, ASpaceGravityVolume), space.Kit*/space.Interior/space.Walk/space.Door, test_interior.py, shot presets steadfast_interior/interior_walk/sc_look/flicker_check/wear_*, find_interior_holes.py, first-person player. Load when adding or changing interior rooms, props, decals, lights, materials, doors, or when fixing holes, flicker, grey checkerboard or wrong colours inside a ship.
---

# Interiér lodi (Steadfast)

Stav k 24. 9. 2026: interiér Steadfastu (strojovna | nákladový prostor | chodba | dveře | kokpit)
je průchozí, stojí v `TestSpace` 500 m stranou od lodi, bez vnějšího trupu. **Autor ho ohodnotil
jako nedostatečný a nový Steadfast se staví podle 2D návrhu** (HANDOFF bod 73–75). Stávající
skripty jsou pracovní pipeline a zdroj ověřených postupů, ne cílový vzhled.

**Wayfarer (25. 9. 2026): interiér uvnitř létajícího trupu**, jiná cesta než Steadfast:
- `Tools/Blender/hs_interior.py` volá `hs_build_ship.py` po rozdělení kabiny. Recept `interior` v
  `ArtSource/Ships/Wayfarer/HardSurface/Wayfarer_hs.json` (`height_m`, `sill_z`, `lights`, `seat`).
  Místnosti a předměty bere z `Design/Wayfarer_layout.json`; předmět se pozná podle klíčového slova
  v českém názvu (`Hydraulika`, `Reaktor`, `Lůžko`, `Přístrojová`, `křeslo`…). Neznámý se přeskočí.
- Výstup: part `Interior` (bez Nanite a kolize) a `Screens` (canvas 1330×490, 4 obdélníky `RECTS`), sockety
  `Display_*`, světla do `Wayfarer_lights.json`. Materiály `MI_Ship_Wayfarer_Int*` jsou na vrstveném masteru.
- Snímky `Tools/Shots/wayfarer_interior.json` (`camera_local` / `look_local` v prostoru lodi, m).
- Cíl jasu jako výše (průměr 0,13–0,23, B/R 0,72–1,05). Bodovky 20 cd na 2,3 m vysokou místnost.
- **v2 (pilot chodby a kokpitu, 25. 9. 2026): kit jako nosná vrstva** (`Tools/Blender/hs_interior_kit.py`,
  recept `interior.kit`): `rooms` (které místnosti), `walls` (dvojice stěna + horní díl na modul, levobok a
  pravobok), `floor`, `ceiling`, `chamfer_deg`, `cove_m`, `spot_cd`, `cove_cd`, `portal_w/d`, `fittings`
  (extinguisher, handrail, vent, junction, conduit). Měřítko kitu se počítá z výšky: stěna 3 + skloněný
  horní díl 2 kit m končí rýhu pod stropem (0,47 u 2,3 m). Kit se čte přímo ze zipu.
- Procedurální díly v kit materiálu: `kit_box` / `kit_obox` (kubické UV), `tbox` v hs_interior.
- Materiály kitu: `kit_trim01/02/02b/03`, `kit_cables`, `kit_padded(_grey)` → MI na `M_Ship_PBR` s texturami
  z `ArtSource/Ships/Shared/Kit/` (`tone_kit_textures.py`), tón přes `base_color_tint`.
- Decaly interiéru: `generate_interior_decals.py` → `D_Int_*`, v setupu `Int_*` (rotace viz WORKFLOW 9.6 be).
- Iterace: `hs_interior_preview.py` (Eevee ze stejných kamer, `world=`, `light=`, `exposure=`); Eevee bez GI
  stěny podsvítí jinak než Lumen, konečné posouzení jen ze zabalené hry.
- **Kokpit Wayfareru (koncept A, 25. 9. 2026):** recept `interior.cockpit` (`style: wrap`, `pod_x/y/z`,
  `screen_w`, `side_margin`, `top_margin`, `wing`, `centre_x`, `centre_top_z`, `fascia_*`, `seam_x`,
  `pinstripe_inset_m`, `frame_wash_cd`) → `Tools/Blender/hs_cockpit.py` (`build_wrap`: deska, křídla, sloupek
  s radarem, pod deskou). Náhled z oka: `hs_interior_preview.py ... eye=1`. Cíl: `Concept/Cockpit/cockpit_target_*.png`.
- **Decaly interiéru jako mesh decaly:** `interior.decals` → `hs_interior_decals.py` (Placer z `hs_decals`,
  položky knihovny, `items` paprskem, `scatter` mřížkou paprsků ke stěnám, `grab_bars`), part `InteriorDecals`.

## Pravidla autora (závazná)

- **Nic nového do 3D bez schváleného 2D návrhu.** Pro každou loď: technický list ve tvaru RSI Ship
  Matrix (`ArtSource/Ships/<Ship>/<Ship>_spec.json`, kód ho nečte), popsaný řez a půdorysy palub, kde má
  **každá místnost a každý předmět účel**. Zdroj pravdy Steadfastu:
  `ArtSource/Ships/Steadfast/Design/Steadfast_layout.json` + `Steadfast_Design.md`; výkresy kreslí
  `python Tools/Design/draw_ship_design.py <layout.json>`. Vzory řezů: `Docs/UI/reference_tvorba_lodi/`.
- **Styl SC:** teplá/neutrální tmavá architektura, světelné lišty, tmavý základ, **studené
  hologramové UI**. (Starší „modrá ocel“ z bodu 59 je překonaná.) Styl, ne kopie jednoho obrázku.
- **Žádná výplň:** bedny, sudy, rekvizity „pro detail“ působí levně. **Klávesnice u dveří
  (`Prop_AccessPoint`) = no-go.** Procedurální pult z kvádrů = „levná low-poly hra“, no-go.
  Low-poly stěny kitu jsou vidět - kit Quaternius je jen dočasný.
- Co autor schválil: šablonové decaly, osvětlení lištami, hologramy (doladit), sedadla z Meshy.
- **Žádná jména ze Star Citizenu** (lodě, firmy, stanice) - naše: Halcyon Freightworks, Veyra.
- Assety: zdarma (licence!), nebo po dílech z Meshy/Scenario, nikdy celá sestava jedním promptem,
  žádné placené balíky. Viz `Docs/AssetSources_Free.md`, `Docs/AssetPipeline_Modular.md`.
- Posuzuje se **z první osoby** (oko ~1,65 m), 1920×1080, RTX 2060.

## Pipeline: Blender → Unreal → test → balení → snímky

```
# 1) Blender headless (Git Bash): postaví GLB místností + Interior_layout.json
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b \
    --python Tools/Blender/build_steadfast_interior.py
# 1b) kontrola děr (musí skončit HOLES 0, falešné úniky z bodů uvnitř pultu ignorovat)
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b \
    --python Tools/Blender/find_interior_holes.py
```
```powershell
# 2) import do UE (PowerShell, editor zavřený) - přehratelné kdykoliv znovu
.\Tools\run_editor_python.ps1 Tools\Assets\import_interior.py
# 3) test
.\Tools\run_editor_python.ps1 Tools\Tests\test_interior.py      # INTERIORTEST PASS/FAIL
.\Tools\run_editor_python.ps1 Tools\Tests\test_character_l6.py  # první osoba
# 4) balení + snímky
.\Tools\Shots.ps1 -Preset steadfast_interior -Package
.\Tools\Shots.ps1 -Preset sc_look -Width 1920 -Height 1080
python Tools/Shots/measure_look.py <složka snímků>
```
Změna jen v C++ (`SpaceInterior*.cpp`, `PlayerCharacter`) → build editoru, pak balení.

### `Tools/Blender/build_steadfast_interior.py`
- Vstupy: `ArtSource/Ships/Steadfast/Interior/CargoBay_Shell.glb` (původní kitbash prostoru) a díly
  vybalené ze `ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip` (CC0, mimo git, návod
  v README vedle). Mapa dílů: `PARTS`.
- Výstup do `ArtSource/Ships/Steadfast/Interior/`: `CargoBay/Corridor/EngineRoom/Cockpit.glb`
  (místnost = jeden mesh), `CockpitGlass.glb`, `CockpitScreens.glb`, `DoorLeaf.glb`,
  `Interior_layout.json` (světla, akcenty, dveře, `SPAWN`, `GRAVITY_BOX`, `props`, `decals`).
- Souřadnice Blenderu v m, Z nahoru, **+X = směr letu**; Unreal má X a Z stejné, **Y zrcadlené**.
  Rozvržení: strojovna x −7..−1 | nákl. prostor 0..8 | chodba 9..17 (šířka 2 m) | kokpit 17..22,4.
  Přepážky 1 m (podlaha shellu přečnívá). Strop všude `HEIGHT` 2,4 m.
- Konstanty: průchod `OPEN_WIDTH` 1,3 × `OPEN_HEIGHT` 2,1 m, rám `DOOR_HEIGHT` 2,25 + nadpraží,
  obložení `LINER_OFFSET` 0,05 m za stěnou, tmavý plášť `hull()` `HULL_GAP` 0,25 m vně.
- Pomůcky: `box`, `prism`, `quad`, `floor`, `ceiling`, `wall(…, gaps=)`, `doorway`, `lamps`,
  `strip` / `ceiling_strips` (světelné lišty), `cylinder`, `pipe_run` (objímky + závěsy á 1 m),
  `cable` / `cable_bundle` (prověšené po parabole), `grating` (rošt nad tmavou šachtou), `beam`,
  `mfd`, `screen_quad`, `radar_disc`, `console`, `toggle`, `knob`, `front_console`,
  `duplicate_islands` (maže zdvojené/zapuštěné díly), `open_shell` (průchody do shellu).
- **`MESHY_PROPS`**: `{"mesh", "at": bod podlahy pod středem, "yaw": kam míří čelo (° Blender, +X=0),
  "width": šířka po škálování (m)}`. Díly leží v `ArtSource/Ships/Steadfast/Kitbash/Meshy/*.glb`
  (PilotSeat, SideConsole, EquipmentRack).
- **`DECALS`**: `{"cell": 0–15 v atlasu 4×4, "at": bod na povrchu, "normal": kam míří povrch,
  "size": m}`. Buňky: 0 žluté pruhy, 1 CARGO BAY, 2 ENGINE ROOM, 3 COCKPIT, 4–6 DECK A-01..03,
  7 šipka (vpravo), 8 výstražný trojúhelník, 9 CAUTION HIGH VOLTAGE, 10 NO STEP, 11 HALCYON
  FREIGHTWORKS, 12 FIRE SUPPRESSION, 13 AIRLOCK, 14 „07“, 15 oranžové pruhy. Atlas:
  `ArtSource/Ships/Steadfast/Interior/Decals/DecalAtlas_raw.png` (Scenario, GPT Image 2.5).
- **Jména materiálů rozhodují o vzhledu v UE** (viz níže) - pojmenovávej podle toho.

### `Tools/Assets/import_interior.py`
- Importuje do `/Game/Environments/Steadfast` (props `/Props`, povrchy `/Surfaces`, decaly
  `/Decals`), staví herce v `/Game/Maps/TestSpace` na `PLACE_AT` = (0, 50000, 0) cm, uloží level.
  `to_unreal(p)` = PLACE_AT + (x, −y, z)·100.
- **`prune()` na konci maže z `/Game/Environments/Steadfast` vše, co není v seznamu `kept`**
  (glTF import tahá kopie textur, 84 MB do LFS). Nový asset v tom balíku přidej do `kept`, jinak zmizí.
- **`M_KitTrim`** (`build_master`): textura kitu odbarvená → `Lift` 0,8 → tint `Gunmetal`
  (0,33, 0,33, 0,34); ORM → `MetallicScale` 0,4, `RoughnessScale` 0,68, `RoughnessFloor` 0,32;
  emise kitu → oranžové akcenty. Vrstvy z ambientCG (`ArtSource/Textures/ambientCG/`: PaintedMetal004
  a 013, MetalPlates006, Leather033A, Rubber004), triplanárně ve světových souřadnicích:
  `WearAmount` 0,2 jen na hranách (`WearEverywhere` 0, holý kov 0,30 / drsnost 0,45),
  `GrimeAmount` 0,5, `FloorPlates` 0,65 na plochách nahoru.
- Instance: `MI_<trim sheet>` na sloty podle jména, `MI_KitDark`, `MI_KitGlow` (oranž. emise 14),
  `MI_KitLamp` (teplá bílá 20), `MI_KitScreen`, `MI_KitWhite`, `MI_KitStrip` (lišty (1, 0,8, 0,58), 14).
  `M_KitGlass` (průsvitné, oboustranné), `M_KitLeather` (sedadla), `M_KitHolo` + `MI_Holo_<stránka>`
  (aditivní, unlit, oboustranné: obrázek × modrý tint × `HOLO_STRENGTH` 5 × řádky 240; černá =
  průhledná). Obsah obrazovek kreslí `python Tools/Assets/draw_holo_screens.py` →
  `ArtSource/Ships/Steadfast/Interior/Screens/`.
- **Mapování slotů podle jména (pořadí):** `m_black_seat*` → kůže; `black` → tmavý plast; `lamp` →
  svítidlo; `glass` → sklo; `m_holo_<Stránka>` → hologram; `white`; `strip` → lišta; `m_screen*` →
  displej; **`light` nebo `screen` kdekoliv → oranžově svítící pás**.
- Světla (`place_lights`): pracovní = bodovky pod svítidly dolů, 1150 lm, 5200 K, kužel 25/80°,
  dosah 450 cm, stíny; akcenty 100 lm bez stínů; světla displejů modrá bez stínů.
- `place_interior_actors`: `ASpaceSlidingDoor` (křídla `DoorLeaf`, otevře se do 2,6 m, 0,55 s,
  `LayoutLeaves()` jako `UFUNCTION`), `ASpaceGravityVolume` (box, 981 cm/s², dolů = −Z boxu), spawn.
- `place_props`: jednotné měřítko podle `width`, postaví na podlahu, `MESHY_FRONT_YAW` −90°
  (Meshy míří do −Y). Kolize podle polygonů.
- `place_decals`: `M_Decal` (deferred, translucent), `MI_Decal_NN` s `CellU = cell % 4`,
  `CellV = cell // 4`; neprůhlednost z jasu, barva ×0,7; hloubka 12 cm. Stěna **roll +90°**
  (−90° = vzhůru nohama), podlaha pitch −90°.
- Kolize: všechny místnosti a sklo `CTF_USE_COMPLEX_AS_SIMPLE`; `CockpitScreens` bez kolize a stínu.
- **Tagy** (herce v buildu hledá C++ podle tagu, ne labelu): `SpaceInterior`,
  `SpaceInteriorLight_Work`, `SpaceInteriorLight_Accent`, `SpaceInteriorGlass`, `SpaceInteriorDoor`,
  `SpaceInteriorSpawn`, `SpaceInteriorScreens`, `SpaceInteriorProp`, `SpaceInteriorDecal`.

### Test `Tools/Tests/test_interior.py`
Hlídá usage flagy `M_KitTrim` (Nanite, static mesh, instanced), výchozí textury všech samplerů,
parametry a jejich výchozí hodnoty podle konstant skriptu (čte je přes `ast`), tagy, světla.
**Nová konstanta/tag/parametr → doplň do `WANTED` a kontrol.** Nikdy neukládá.

## Hráč v interiéru

- Vstup: klávesa **I** (kdekoliv v TestSpace), tlačítko v menu pauzy, `space.Interior`
  (`ASpacePlayerController::ToggleInterior`, start na tagu `SpaceInteriorSpawn`, zpět do lodi).
- **První osoba výchozí a v lodích jediná** (`APlayerCharacter::SetFirstPerson`,
  `Source/gamespace/PlayerCharacter.cpp`): `FirstPersonCamera` 165 cm nad chodidly, 14 cm před
  obličejem, FOV 90°, ±80°, hlava skrytá (`HideBoneByName("head")`). **V pěšky** přepíná první/třetí
  osobu (3P jen na testy; v lodi je V coupled/decoupled).
- Gravitace: `APlayerCharacter::UpdateGravity` se ptá `ASpaceGravityVolume` dřív než planety.
- Další krok podle autora: usednutí do pilotního křesla s animací (Mixamo) a plynulý přechod do kamery kokpitu.

## Konzolové příkazy (zabalená hra i scénáře snímků, nic se neukládá)

| Příkaz | Co |
| --- | --- |
| `space.Interior` | do interiéru a zpět (= I) |
| `space.Walk <vpřed> <vpravo> <s> [yaw]` | chůze jako držené klávesy; log `WALK end at …` |
| `space.Door 1\|0\|-1` | všechny dveře otevřít / zavřít / automaticky |
| `space.Kit <Param> <hodnota> [část jména mat.]` | skalár materiálů: `Lift`, `MetallicScale`, `RoughnessScale`, `RoughnessFloor`, `AccentStrength`, `WearAmount`, `WearEverywhere`, `GrimeAmount`, `FloorPlates`; filtr `MI_T_` = jen trim sheety |
| `space.KitColor <Param> R G B [jméno]` | `Gunmetal`, `Accent` |
| `space.KitLight Work\|Accent\|All <Vlastnost> <hodn.>` | `Intensity` (lm), `Temperature`, `UseTemperature True`, `LightColor R G B`, `AttenuationRadius`, `OuterConeAngle` |
| `space.KitReset` | materiály, světla, slunce a sky light zpět - **první příkaz každé varianty** |
| `space.LightList` | výpis světel (sun/shadow…), `SpacePostTuning.cpp` |

Kód: `Source/gamespace/SpaceInterior.cpp/.h`, `SpaceInteriorTuning.cpp`, `SpacePlayerController.*`.
Ladit nejdřív za běhu přes `space.Kit*` ve scénáři, hodnotu pak zapsat do konstant
`import_interior.py` (+ test), přehrát import, zabalit.

## Snímky a měření

`.\Tools\Shots.ps1 -Preset <x>` (snímky v `Saved\Shots\<stamp>_<preset>\`). Volná kamera interiéru:
`"camera": "free"`, `camera_location` / `camera_look_at` v **metrech** (interiér na Y = 500, Y
zrcadlené proti Blenderu), `fov`, `exposure` (pevná 2,0 pro srovnání materiálů; `sc_look` je
s automatickou expozicí). `"camera": "pawn"` = kamera postavy. `console` příkazy zůstávají pro
další snímky → varianty začínej `space.KitReset`.

| Preset | Účel |
| --- | --- |
| `steadfast_interior` | přehled všech místností, pevná expozice |
| `interior_walk` | `space.Interior` + `space.Walk` z první osoby; kontrola kolizí v logu |
| `sc_look` | 1080p, auto expozice; `python Tools/Shots/measure_look.py <složka>` |
| `sc_tune`, `interior_tune`, `ceiling_tune`, `accent_tune` | varianty barvy/světel přes `space.Kit*` |
| `wear_check`, `wear_tune` | opotřebení zblízka / síla wear+grime |
| `flicker_check` | 8× stejná kamera; `python Tools/Shots/measure_flicker.py <složka> <mapa.png>` |
| `perf_interior`, `perf_quality` | `stat unit`, stíny/dosah světel; vždy `-Width 1920 -Height 1080` |

**Cílové rozsahy SC (interiér, auto expozice):** průměr 0,13–0,23, p50 0,08–0,18, p90 0,32–0,53,
p99 0,56–0,88, **B/R 0,72–1,05** (teplé), detail 0,024–0,035. Dosaženo: prostor/chodba/strojovna
B/R 0,70–0,77, p99 0,72–0,96. Blikání < 0,1 % pixelů. Interiér ~70 FPS ve 1080p (epická, TSR 75 %).
Snímky porovnávej listem vedle sebe (PIL ve scratchpadu) proti `ArtSource/Reference/Mood/sc_cockpit_*.webp`.

## Kontrola geometrie (Wayfarer a další lodě z hs pipeline)

Před každým předáním: `python Tools/Tests/test_ship_geometry.py` (Blender headless, ~15 s, `GEOTEST SUMMARY … PASS`).
Kontrolu dělá `Tools/Blender/check_ship_geometry.py`: zrcadlené decaly (mesh i promítané), plovoucí díly, průniky
za obložení/ven z trupu, placeholder materiály, díry z oka a z kamer presetu `<loď>_interior.json`. Výstup je v
`Saved/GeoCheck/` (`geocheck.json`, masky `holes_*.png`; s `GEOCHECK_DEBUG=1` i barevný render po objektech).
Výjimky pro plovoucí díly: recept `checks.floating_exempt`. Díry se zavírají tmavým pláštěm `Int_HullSkin` (5 cm
pod trupem) a obložením kokpitu; nástrahy WORKFLOW 9 bm–bo.

## Vizuální kritik před předáním (autor 25. 9. 2026)

Každé předání interiéru nebo kokpitu projde podagentem `visual-critic` (postup a checklisty
`interior` / `cockpit`: skill `ship-pipeline` 7b). Listy skládá `Tools/Review/make_compare_sheet.py`
(pohled z oka a zezadu, zblízka ovladače; den, noc, vesmír). Kritik dostane jen `brief.md` a listy.
Nejvýš 3 kola, každá výtka s reakcí, recenze v `Docs/Reviews/`. Kontrola geometrie
(`test_ship_geometry.py`) se dělá navíc, ne místo kritika.

## Pilotní sedadlo, rozptyl decalů, světla (hs pipeline, kokpit v2)

- Sedadlo je procedurální `hs_cockpit.pilot_seat` (Meshy vyřazené jako AI geometrie, autor 25. 9. 2026): skořepina,
  polstrované panely se švy (poloměr hran 2,8 cm; kulaté polštáře působí jako hračka), boční vedení, opěrka hlavy
  na sloupcích, popruhy přes horní hranu do štěrbin a do přezky.
- Rozptyl decalů `interior.decals.scatter`: `axis: "x"` = mřížka y×z, paprsky podél x od `from_x` (čela, stěny);
  `axis: "z"` = mřížka x×y (rozsah `y`), paprsky dolů od `from_z` (desky shora).
- Vnitřní světla nesou `specular` (výchozí 0,25): plný specular dělal na lesklém skle kanopy bílé body.
- Světlo displeje na okolí patří před sklo ve výšce jeho středu, ne k nejbližšímu povrchu (hot spot, WORKFLOW bz).
- Výtka „text na displeji useknutý z oka“: nejdřív odsazení stránky v C++, pak ray cast z `SOCKET_Cockpit` na body
  skla a výpis zasaženého objektu (WORKFLOW bw).

## Interiérový kit: designový jazyk (návrh ke schválení autorem, 26. 9. 2026)

Vlastní modulární kit pro interiéry Wayfareru, Steadfastu a dalších lodí (zadání autora 26. 9. 2026: kroky
1–7, každý díl jednou vyladit a schválit, pak opakovat). Úroveň a přístup SC, design vlastní, bez kopií dílů.
Quaternius už nosná vrstva není. **Do schválení tohoto oddílu se nic nestaví.**

Podklady:
- moodboard `ArtSource/Reference/Mood/kit_moodboard.jpg` (lokálně, obsahuje snímek z cizího videa);
- reference `starcitizenreference/Screenshot 2026-09-25 0213*.png` a `ShipDetailing_VideoNotes.md`;
- schválená chodba a kokpit v2, exteriér Wayfareru (recept `Wayfarer_hs.json`).

### 1. Tvarosloví
- **Průřez chodby: lichoběžník s osmiúhelníkovým stropem.**
  - Svislá stěna do výšky 1,3 m.
  - Nad ní zkosení 35° dovnitř, jako dnešní chodba Wayfareru (`kit.chamfer_deg`). Končí u stropu ve vybrání
    se světelnou lištou (`cove_m` 0,12).
  - Plochý strop, uprostřed kabelový žlab.
  - U podlahy sokl 0,10 m se zkosením 45° a modrou lištou.
- **Zalomená stěna:** panel se v horní třetině láme o 10–15° dovnitř. Dlouhá stěna tak není jedna rovina.
- **Rytmus:**
  - portál (rám) po 1,2 m: dva stěnové moduly 0,6 m, nebo jeden modul 1,2 m;
  - rám je o 8–12 cm hlubší než panely, šířka lícové plochy 14 cm (`portal_w`), na vnitřní hraně svítící
    prstenec.
- **Panelové poměry:** 1 : 2 a 2 : 3 (0,6 × 1,2, 0,6 × 0,9, 0,4 × 0,6). Zakázané jsou čtverce přes 0,8 m a
  souvislé plochy přes 1,2 m bez spáry.
- **Tři vrstvy, vždy nad sebou:**
  1. konstrukce (žebra, nosníky, příhrady 60–120 mm hluboké);
  2. panely předsazené 20–40 mm před konstrukcí se stínovou spárou kolem;
  3. výbava na panelech (skříňky, displeje, madla, trubky 5–30 cm).

  Panel vždy přesahuje díl pod sebou. Díly se nepotkávají v jedné rovině (blikání, WORKFLOW 9.3 p).
- **Úhly:** hlavní zkosení 35°, vedlejší 45°. Rohy panelů zaoblené nebo sražené, žádná ostrá pravoúhlá hrana
  delší než 2 cm.

### 2. Velikosti
| Prvek | Hodnota |
|---|---|
| Zkosení velkých dílů (> 1 m: žebra, portály, desky) | 12–20 mm, 2 segmenty |
| Zkosení středních dílů (0,2–1 m: skříňky, konzole, poklopy) | 6–10 mm |
| Zkosení malých dílů (< 0,2 m: ovladače, západky, šrouby) | 2–4 mm |
| Trup exteriéru, pro srovnání | 25 mm |
| Nosná žebra a rámy | 60–120 mm |
| Stěnové panely | 20–30 mm |
| Kryty a poklopy | 10–15 mm |
| Lišty a obruby | 5–8 mm |
| Stínová spára mezi panely (tmavý materiál) | šířka 6–10 mm, hloubka 10–20 mm |
| Dělicí drážka v panelu | šířka 3–4 mm, hloubka 2–3 mm |
| Větrací štěrbiny | 8 mm, rozteč 20 mm |
| Šrouby | Ø 8–12 mm, v řadách po 60–100 mm |
| Výška stropu | chodba 2,3 m, kajuta 2,3–2,4 m, servisní průlez 1,9 m |

### 3. Hierarchie detailu a shlukování
- **Velký:** portály, žebra, stěnové moduly, žlaby, desky. Určuje rytmus prostoru po 1,2 m.
- **Střední (0,2–0,6 m):** skříňky, displeje, konzole, trubky, mřížky, poklopy, madla, svítidla.
- **Malý (1–5 cm):** šrouby, štítky, kontrolky, západky, kabelové vývodky, popisky.
- **Shluky:** 60–70 % středního a malého detailu leží do ~1 m od funkčního místa. Funkční místa: dveře,
  konzole, lůžko, technika, žebřík, hasicí přístroj. Mezi shluky jsou klidné panely jen se spárou, jedním
  štítkem a zrnem materiálu. Rytmus klid – shluk – klid; nikdy rovnoměrný detail po celé stěně.
- Každý panel nad 0,5 m má aspoň spáru nebo jeden decal, jako na exteriéru. Klidná plocha nesmí být holá,
  kritik holé plochy vytýká.

### 4. Paleta a materiály
Barvy jsou lineární, sdílený master kitu s variací po panelech a zrnem v lesku.

| Materiál | Kde | Hodnoty |
|---|---|---|
| **Grafit** (lakovaný kov) | architektura: panely, konzole, desky | 0,05–0,07; drsnost 0,45–0,55; zrno 45 cm; `RoughVariation` 0,35 |
| **Gunmetal** (broušený/satinový kov) | konstrukce, rámy, madla, zábradlí, podlahové lišty | 0,33/0,33/0,34; metallic 1; drsnost 0,30–0,40 |
| **Krémová** (akcent) | lemy dveří, lůžko, výstupky, obložení rámu skla | nejvýš 10–15 % plochy prostoru |
| **Oranžová Halcyon Freightworks** (signální) | madla, záchytné body, výstražné pruhy, linky, poklopy | 0,85/0,34/0,06; nejvýš 3–5 % plochy |
| Guma | stupně, protiskluzové pásy, madla, soklové lišty | tmavá, drsnost 0,8–0,9 |
| Látka, kůže | sedadla, lůžka, polstry | švy z trim sheetu |
| Plast | kryty elektroniky, displejové rámy | drsnost 0,5 |
| Karbon | jen luxusní výbava (jiný výrobce) | – |
| Studené UI | displeje, hologramy, modré lišty u podlahy | modrá 0,45/0,72/1,0 |

- Variace mezi panely jako na exteriéru: tón ±7 %, drsnost ±0,12, 8 % panelů kovových.
- Opotřebení jen v drsnosti, bez otřených hran (rozbor SC).
- **Výrobce jako parametr:** instance palety podle výrobce.
  - Halcyon Freightworks: grafit, krémová, oranžová.
  - Kestrel Dynamics: návrh světlý šedobílý lak, tmavé gunmetal rámy, modrý akcent. Ke schválení s kitem.

### 5. Decaly a trim sheet
- **Hustota jako na podlaze a dveřích C2:**
  - dveře a rámy: číslo sekce, značky, čáry, kroužky, štítek otevírání;
  - podlaha: čáry podél stěn, pruhy u prahů, nápisy sekcí, protiskluzová pole. V nákladovém prostoru decaly
    zabírají až 50 % podlahy.
- **Typy:** strukturní (normála, drsnost, AO: spáry, šrouby, mřížky, poklopy) a informační (barva: nápisy,
  čísla, výstrahy), jak je dnes v knihovně. Dlouhé čáry jsou natažený úsek atlasu.
- **Ovládací panely:**
  - tištěný zaoblený rámeček skupiny s názvem v přerušené horní hraně;
  - oblouky stupnic kolem voličů, popisek pod každým ovladačem, emisní verze štítků;
  - jedno velké podsvícené tlačítko hlavní funkce.
- **Trim sheet kitu** (vlastní, procedurální, 4096 px, 512 px/m):
  - obruby panelů, stínové spáry, řady šroubů, švy čalounění, rámečky, lemy, protiskluzové pruhy;
  - díly kitu mapují hrany a lišty na trim sheet a velké plochy na sdílený master (triplanární zrno).
- **Písmo:** Rajdhani a Share Tech Mono. Servisní nápisy 2 cm, orientační 8–15 cm, čísla sekcí 25–40 cm.

### 6. Světla
Podle rozboru C2 a měření `Docs/Reviews/2026-09-26_interior_lighting_variants.md`.
- **Každé svítidlo, lišta a linka má své světlo:** dosah 1,5–2 m, specular 0,2, bez klasických stínů. Světlo
  je vždy v pouzdře: liniové ve zkosení a v soklu, bodové v kruhovém stropním pouzdře, nikdy holá žárovka.
- **Hustota:**
  - obytné prostory a chodby 1,2–1,8 světla na m²;
  - kokpit 2–3 na m²;
  - velké nákladové prostory 0,5–1 na m².

  Kontrolky, LED a obruby tlačítek jsou jen emisivní.
- **Barevný nádech:**
  - pracovní světla teplá bílá 4000–5200 K;
  - orientační lišty u podlahy studená modrá;
  - akcenty slabě oranžové;
  - nouzová světla červená.

  Kontrast: kužele ze stropních pouzder, tmavé kouty a mezery mezi ostrůvky světla.
- **Stíny:** návrh je MegaLights s ray-traced stíny, zapnuté jen s kamerou uvnitř lodi (+1,8 až +2,2 ms).
  Záložní režim bez stínů (+1,2 až +1,5 ms). Klasické stíny pro desítky světel nejdou (+47 až +113 ms).
- **Jemná objemová mlha:** nízká hustota, jen aby byly vidět kužele. Cena se změří v pilotu chodby.

## Interiérový kit: mřížka a technická pravidla (krok 2, 26. 9. 2026)

Strojově čitelně je vše v `ArtSource/Kit/kit_rules.json`. Čtou ho stavební skripty dílů (krok 4), kontroly kitu
(krok 5) a manifest (krok 6), takže čísla se mění jen tam. Výkres průřezů, rytmu a pivotů
`Docs/Kit/kit_sections.png` kreslí z pravidel `python Tools/Kit/draw_kit_sections.py`.

- **Mřížka:**
  - půdorys 0,3 m, moduly 0,3 / 0,6 / 0,9 / 1,2 m;
  - rozteč portálů 1,2 m (portál 0,3 + stěny 0,9) nebo 2,4 m (portál 0,3 + stěny 2,1). Obě smí střídat, aby rytmus
    chodby nebyl jednotvárný (autor 26. 9. 2026);
  - svisle 0,1 m;
  - výplně 0,1 a 0,2 m jen tam, kde trup vnutí šířku mimo mřížku (Wayfarer: nákladový prostor 3,8 m = 3,6 +
    2 × 0,1);
  - díly se skládají bez mezer: každý modul nese na svých okrajích polovinu stínové spáry (4 mm) nad tmavým
    těsněním, takže spoj nikde neprosvítá.
- **Standardní průřezy** (světlá šířka mezi líci panelů u podlahy / strop):

| Průřez | Šířka | Strop | Svislá stěna do | Sklon 3:4 | Strop mezi vybráními | Portál před líc |
|---|---|---|---|---|---|---|
| S servisní průlez | 0,9 | 2,1 | 1,9 | 0,2 (odsazení 0,15) | 0,6 | 0 (lícuje) |
| N úzká chodba | 1,2 | 2,3 | 1,7 | 0,4 (0,3) | 0,6 | 0,08 |
| W široká chodba, místnost | 2,4 | 2,3 | 1,3 | 0,8 (0,6) | 1,2 | 0,10 |
| T vysoká místnost, náklad | podle místnosti | 2,7 | 1,7 | 0,8 (0,6) | podle místnosti | 0,10 |

- **Profil stěny:**
  - sokl do 0,1 m se zkosením 45° a lištou u podlahy;
  - svislá část;
  - sklon 3 : 4 (36,9°, návrhových „~35°“ na mřížce);
  - vybrání 0,12 m se světelnou lištou;
  - strop s kabelovým žlabem.
- **Zóny od líce panelu** (líc = hranice místnosti z layoutu):
  - konstrukce za lícem do 0,2 m, pak obložení trupu;
  - panel 20–30 mm, předsazený 20–40 mm;
  - podlahová deska 50 mm nad konstrukcí 0,15 m;
  - strop s konstrukcí 0,25 m.
- **Průchodnost:** kapsle postavy má poloměr 0,42 m a výšku 1,92 m (`PlayerCharacter.cpp`). Světlá šířka všude
  i v portálu ≥ 0,9 m, světlá výška ≥ 2,0 m. Proto portály v průlezu S nevystupují.
  - Ověření v celé výšce kapsle po 1 cm (hlava a ramena, kde se stěna sklání): `python Tools/Kit/check_kit_clearance.py`.
  - Nejmenší boční rezerva je všude ve výšce boků (0,42 m, kde je kapsle nejširší). Ve výšce ramen a hlavy je
    rezerva větší, protože se kapsle zužuje rychleji než stěna.

| Průřez | Mezi portály: bok / hlava | V portálu: bok / hlava |
|---|---|---|
| S | 0,03 / 0,18 m | 0,03 / 0,18 m |
| N | 0,18 / 0,38 m | 0,10 / 0,30 m |
| W | 0,53 / 0,38 m | 0,43 / 0,28 m |
| T (3,6 m) | 1,38 / 0,78 m | 1,28 / 0,68 m |

  - **Výbava v chodbě N** smí vystoupit nejvýš 0,15 m od líce, pokud je jen na jedné straně (světlá šířka musí
    zůstat 0,9 m); na obou stranách nejvýš 0,15 m dohromady. Skříňky 0,2 m hluboké jen v průřezech W a T.
  - **Kamera třetí osoby** (klávesa V pěšky): rameno 3,8 m, posun (0; 0,55; 0,65) m, sonda 0,12 m, kolize zapnutá.
    V chodbě N skončí 2,75 m za postavou při vodorovném pohledu, 1,3 m při pohledu 30° dolů (narazí na sklon
    stropu). Nikdy nevleze do hlavy a zůstane v profilu. Kolize kitu proto musí blokovat kanál Camera. Ve hře se
    ověří v pilotu chodby, dnešní interiér Wayfareru kolizi nemá.
- **Kit v trupu Wayfareru** (`Tools/Kit/hull_fit_sections.py`, řezy po 0,1 m, obálka = líc + konstrukce 0,2 m
  + podlaha 0,2 m + strop 0,25 m, 5 cm od trupu, silueta se nemění; výkres `Docs/Kit/hull_fit_wayfarer.png`):
  - N a W se vejdou do nákladu, techniky i kajuty (rezerva 0,09–0,35 m, nejtěsněji u rampy x = 1,1 m).
  - Místnost na celou šířku layoutu (3,8 m) se se zónou konstrukce 0,2 m nevejde. Nejširší místnost na mřížce:
    náklad 3,0 m, technika 3,3 m, kajuta 3,0 m.
  - Pro náklad je to otázka návrhu: 8 SCU ve 2 řadách a ulička 1,25 m potřebují 3,75 m. Rozhodne se v pilotu
    (tenčí konstrukce 0,1 m jen v nákladu, jiné uspořádání SCU).
  - Kokpit je nízký prostor pod kanopou (podlaha 1,15 m, nad ní ~1,7 m do trupu). Průřezy chodeb v něm neplatí;
    dostane vlastní díly (deska s displejovým pásem, rám skla) v kroku 7.2.
- **Pivoty** (+X dopředu, +Y vlevo, +Z nahoru, měřítko 1, aplikované transformace):
  - průběžné díly (podlaha, strop, portál, trubky, kabely, vzduchotechnika, schody): začátek modulu na ose
    průřezu, z = 0, +X po směru chodby;
  - stěny, dveře, přepážky: dolní roh na lícové rovině, líc míří na +X, šířka po +Y (0 až W);
  - rohy: vnitřní roh průsečíku lícových rovin;
  - výbava, konzole, deska, sklo, světla: střed montážní plochy, čelo na +X.
- **Sockety:**
  - `SOCKET_Snap_Start/End/Left/Right/Top/Bottom`, vždy na mřížce;
  - `SOCKET_Light_n`: X = směr světla, parametry (typ, role teplá/studená/signální/nouzová, cd, dosah, kužel,
    stín MegaLights) v manifestu kitu;
  - `SOCKET_Decal_n`: X = normála, Y = nahoru decalu; tagy číslo sekce, výstraha, štítek, šipka, servis;
  - `SOCKET_Mount_n`: úchyt výbavy.
- **Jména:**
  - `SM_Kit_<Kategorie>_<Díl><velikost v dm><průřez>_<Varianta>`, např. `SM_Kit_Wall_Grille06W_B`. Kategorie:
    Wall, Corner, Portal, Ceiling, Floor, Stair, Door, Bulkhead, Console, Dash, Glass, Fitting, Furniture,
    Pipe, Cable, Duct, Light.
  - `MI_Kit_<Výrobce>_<Role>`, `T_Kit_<Jméno>_<BC|N|ORM|M|H|E>`.
  - Sloty materiálů dílu se jmenují podle role: `Kit_Primary` (grafit), `Kit_Structure` (gunmetal),
    `Kit_Accent`, `Kit_Signal`, `Kit_Rubber`, `Kit_Fabric`, `Kit_Plastic`, `Kit_Trim`, `Kit_Seal`,
    `Kit_GlowWarm`, `Kit_GlowCool`, `Kit_GlowSignal`, `Kit_Screen`, `Kit_Glass`.
- **Paleta podle výrobce:** loď v setupu zvolí `kit_maker` (Halcyon / Kestrel) a import přiřadí sloty rolí
  k `MI_Kit_<Výrobce>_<Role>`. Barvy rolí jsou v `kit_rules.json` (`palettes`). Kit tak slouží více lodím bez
  kopií dílů.
- **Hustota texelů:**
  - trim sheet 1024 px/m (±25 %) pro hrany, lemy, spáry a obruby (autor 26. 9. 2026: 512 byl zblízka měkký). List
    4096 × 2048: pruhy se opakují po 4 m, výšky pruhů celkem 2 m. Paměť 16,8 MB, s mipmapami 22,4 MB (BC1 barva,
    BC5 normála, BC1 ORM), jeden list pro všechny lodě. Hra teď využívá ~3,2 z 5 GB VRAM;
  - velké plochy triplanárně ve světě 1024 px/m, bez UV;
  - decaly 2048 px/m;
  - zrno 45 cm.
- **Rozpočty trojúhelníků** (LOD0, bez Nanite). Dnešní interiér Wayfareru má ~300 tisíc trojúhelníků na
  67 m² (~4,5 tisíce na m²).
  - stěna 5 000 na metr, roh 4 000, portál 8 000, strop 3 500 na metr, podlaha 1 500 na metr;
  - schod 600, dveře 10 000, přepážka 8 000;
  - konzole 15 000, palubní deska 60 000, sklo 500;
  - drobná výbava 3 000, nábytek 15 000;
  - trubky 500 na metr, kabely 1 000 na metr, vzduchotechnika 800 na metr, pouzdro světla 600;
  - místnost nejvýš 10 000 na m², interiér lodi nejvýš 1 milion;
  - LOD1 (50 %, velikost na obrazovce 0,25) jen pro konzole, nábytek a výbavu.
- **Kolize:** jednoduché UCX boxy po modulech, nikdy complex-as-simple.
  - stěna, podlaha, strop: jeden box každý;
  - portál: boxy vystupujícího rámu;
  - schody: šikmý box;
  - dveře: rám a pohyblivý box křídla;
  - konzole: jeden box, nábytek 1–3 boxy;
  - drobná výbava bez kolize, pokud se po ní nešplhá.
- **Nanite:** interiér zůstává bez Nanite, znovu ověřeno 26. 9. 2026 (`Docs/Reviews/2026-09-26_kit_nanite_check.md`):
  - s Nanite zmizely tenké díly (rámy, moduly, obruby);
  - stíny MegaLights chtějí přesnou geometrii;
  - interiér letí s kamerou (WORKFLOW 9.2 a).

## Interiérový kit: seznam dílů (krok 3, 26. 9. 2026)

Strojově čitelně je seznam v `ArtSource/Kit/kit_parts.json`: rodiny dílů, varianty, délky modulů, průřezy,
dávka a stav (planned / built / approved). Seznam odpovídá zadání autora: 47 rodin, 78 variant před násobením
délkami a průřezy. Stavba po dávkách, další dávka až po schválení předchozí:

1. **Stěnové moduly a materiály kitu:**
   - plný, s mřížkou, se skříňkou, s průchodem trubek, se servisním poklopem, s displejem (každý A–C);
   - master a instance podle výrobce, trim sheet.
2. **Rohy, přechody, portály, strop:**
   - vnitřní a vnější roh, přechod N–W, konec chodby, zúžení do průlezu;
   - portál se svítícím prstencem;
   - stropní žlab, stropní panely se světlem a ventilací.
3. **Podlaha, schody, rampa:** desky s lištami, rošty, poklopy, schody, rampa.
4. **Zárubně, dveře, přepážky:** posuvné dveře s animovatelným křídlem.
5. **Konzole, deska, sklo:**
   - konzole stojící, nástěnná a rohová;
   - palubní deska s displejovým pásem zapuštěným pod linií pohledu a ovládacími moduly z kokpitu v2;
   - skleněné panely 0,2 / 0,32 / 0,5 m.
6. **Výbava a nábytek:**
   - madla, zábradlí, žebříky, hasicí přístroj, lékárnička, cedule;
   - skříňky, boxy, lůžko, sedadla (procedurální sedadlo z kokpitu v2).
7. **Infrastruktura:** trubky, kabely, vzduchotechnika, parametricky podle délky a průměru.
8. **Pouzdra svítidel:** liniové, bodové, nouzové, kontrolky (jen emise) s přednastavenými světly.

Pravidla pro všechny díly:
- materiál, decaly, světla a sockety podle designového jazyka, žádné holé šedé díly;
- průřez N: výbava nejvýš 0,15 m od líce;
- zákaz klávesnic u dveří platí i pro displejové moduly.

## Interiérový kit: stavba dílů a ukázka v enginu (krok 4, dávka 1, 27. 9. 2026)

Pipeline (vše skriptem, rychlá smyčka bez balení, dokud se ladí tvar v Blenderu):
```bash
python Tools/Kit/kit_trim_sheet.py          # trim sheet 4096x2048 @ 1024 px/m -> ArtSource/Kit/Textures (+ trim_index.json)
python Tools/Kit/kit_screens.py             # atlas obrazovek displejů (T_Kit_Screens.png, M_Ship_Screen)
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup     --python Tools/Kit/kit_build.py -- walls [--sections W,N] [--no-render]
python Tools/Kit/kit_catalog.py 1           # katalogový list Docs/Kit/catalog_batch1.png
```
```powershell
.\Tools\run_editor_python.ps1 Tools\Assets\import_kit.py           # /Game/Kit + ukázková chodba v TestSpace
.\Tools\Shots.ps1 -Preset kit_showroom -Package -Width 1920 -Height 1080
```
- **Soubory:**
  - `Tools/Kit/kit_geo.py`: třída `Part`. Geometrie po rolích materiálů, zkosené boxy a desky, lisovaný panel
    (`inset`), trubky, UV (trim pruhy podle lokálních os, atlas obrazovek, metry), UV1 = náhodné ID panelu,
    barva vrcholů `Col` pro vrstvený master, UCX a SOCKET_.
  - `Tools/Kit/kit_walls.py`: stěnové moduly (plášť + 6 typů × A–C).
  - `Tools/Kit/kit_build.py`: stavba, decaly přes `hs_decals.Placer`, export FBX, manifest, rendery.
- **Výstupy:**
  - `ArtSource/Kit/Kit_Walls.blend`;
  - `ArtSource/Kit/Export/SM_Kit_*.fbx`;
  - `kit_manifest.json` (rozměry, trojúhelníky proti rozpočtu, materiály, sockety v UE cm s parametry světel, kolize);
  - rendery `Saved/KitCatalog/`.
- **Plášť stěny** (každý modul):
  - tmavá výplň za panely (vidět ve spárách);
  - zapuštěný sokl s modrou lištou a gumovou hranou;
  - spodní panel v sekundárním tónu s kartáčovaným kopacím plechem;
  - lisovaný hlavní panel;
  - oranžová signální linka ve žlábku pod šroubovanou madlovou lištou (trim `rail_bolted`);
  - sklon ze dvou lisovaných panelů se šroubovanou přírubou;
  - vybrání s okrajem, římsou, čelem a teplou lištou;
  - poloviční kryty spojů na koncích modulu (sousedé z nich složí jeden kryt);
  - konstrukční rám na každém spoji (`Wall.ribs`): polovina 6,5 cm na každém konci modulu, dohromady 13 cm s plochým
    lícem 9 cm, 8,5 cm před panely, zkosení k panelům, čisté koleno mezi svislou částí a sklonem, šrouby po 0,3 m.
    (Dvě zaoblené poloviny po 3 cm četl kritik jako „svislé trubky“ a spoje jako „tenké spáry“.) Výbava musí
    nechat 6,5 cm u konců modulu volné (skříňky 0,46 m, displej 0,4 m, poklop A 0,38 m);
  - otevřený kabelový žlab pod vybráním (deska 4 cm od sklonu na žebírkách, lem, 3 černé kabely a krémový);
  - hlavní panel rozdělený v 0,86 m (`Wall.split`), horní deska 12 mm vpředu (stínová spára, přesah); vlastní
    `main_split` to vypne (skříňky, Plain B/C, kanál trubek);
  - na horním sklonu kabelové kanály (`Wall.conduits`): vzor podle jména dílu (žádný 20 %, jeden, dvojice, dvojice se
    zanořením do panelu přes průchodku), 1–3 příchytky na volných místech (třmen nebo pásek). Stejné kanály na každém
    modulu dělaly rastr (ověřovací kolo);
  - konzole vybrání nad každým spojem (schová konce lišt; samostatné koncovky četl kritik jako „schody“);
  - rámy bez zkosení: zkosení 5 mm rozdělí hrany profilu pod 40° a hladké stínování udělá z rámu kulatý sloup;
  - lišty jako svítidla: kovový profil s lemy, koncovky a difuzor (u podlahy, nahoře ve vybrání i pod hranou vybrání);
  - světla: jedno lineární (rect) světlo na lištu a modul (`Wall.strip_light`, socket `type="rect"` s `width_cm`,
    `height_cm`, `dir_ue`): sokl studené 0,25 cd/m, dosah 0,7 m; vybrání nahoru teplé 0,8 cd/m, 1,1 m; pod hranou
    vybrání dolů-ven teplé 1,1 cd/m, 2,4 m (osvětluje sklon a protější stěnu). Body po 0,6 m pálily skvrny;
  - `Snap_Start/End`, dvě UCX (stěna, sklon s vybráním).
- **Výbava podle kola 1 kritika (27. 9. 2026):**
  - skříňky mají korpus s ohybem hran, zvýšený rám, dveře 12 mm v rámu přes tmavou spáru, panty, větrací štěrbiny;
    stohované se liší (páka západky vs. zapuštěné madlo a zámek), bedna má rychlouzávěry a boční madla;
  - poklop má zvýšený rám, 4 rychlouzávěry Ø 28 mm, panty, výstražný pás jen nad rámem;
  - trubky vycházejí ze stěny a vracejí se do ní obloukem s průchodkou uvnitř modulu, nikdy nekončí
    na hranici modulu (trasy přes víc modulů = mosty v dávce 7);
  - displej má krycí sklo a klávesy v tmavých jamkách;
  - štítky (`kit_rules.decal_rules`): servisní štítek (`st_*`, `label_*`) jen u hardwaru, který pojmenovává (poklop A
    SERVICE ACCESS, poklop B INSPECT, poklop C systémy, mřížka VENT hned u mřížky, dublovací plech TORQUE, trubky
    svůj systém); plná stěna nenese žádný. Nikdy stejný štítek na sousedních modulech layoutu: kontroluje
    `import_kit.check_layout_labels` (import spadne) a `test_kit_showroom.py`; manifest má `service_labels` dílu.
    Čísla panelů jsou čísla dílu (stejný díl = stejné číslo). Štítek leží celý na okraji prolisu nebo celý
    v prohlubni (WORKFLOW cm);
  - oděr hran: `kit_geo` dává barvě rohů G = 0 plochám z bevelu (`Part.edge_faces`), master pak ošoupe jen zkosení
    (EdgeWear lak 0,3, konstrukce 0,5). Maska po vrcholech nejde: skoro každý vrchol dílu leží na hraně.
    Barva `Col` je v doméně rohů; `kit_build.join()` převede bodovou `Col` decalů taky na rohy
    (`to_corner_colour`), jinak by masky dílu přepsala a UE by bílou barvu zahodil (WORKFLOW cq). Export
    `colors_type="LINEAR"`. `kit_build` spadne, když masky nepřežijí (`colour_masks` v manifestu);
  - gumové těsnění 6 mm uvnitř rámu poklopů a mřížek (`_gasket`).
- **UE (`Tools/Assets/import_kit.py`):**
  - Díly jdou do `/Game/Kit/Meshes` přes funkce `import_ship` (FBX, velikost, sloty, kolize, sockety), bez Nanite, kolize simple-as-complex.
  - Staré meshe se před importem mažou (reimport držel staré sockety).
  - `MI_Kit_Halcyon_<Role>` v `/Game/Kit/Materials` na masterech lodí:
    - layered pro Primary, Structure a Accent: Primary 0,1/0,095/0,088, **PaintMetallic 0,1** (lak je dielektrikum,
      při 0,45 ztratil půl difuzního světla a stěny zčernaly), grunge 0,3, variace drsnosti 0,28, špína 0,35 (vertex R
      klesá u podlahy ve spodních 0,5 m); Structure 80 % palety (0,26), metallic 0,4, drsnost 0,36 (čistý kov 1,0
      zrcadlil tmavou místnost a rám zmizel); Accent 70 % palety, drsnost 0,56; Signal 80 % palety, drsnost 0,5;
      bez oděru hran (SC lak ho nemá); teplá světla (255, 228, 200), `Kit_GlowWarm` 1/0,9/0,78 (B/R 0,58 → 0,72);
    - hull pro Signal, Rubber, Seal, Plastic a svítivé materiály;
    - pbr pro Trim;
    - screen pro displeje;
    - decaly zatím přes instance Wayfareru (sdílený atlas).
  - **Ukázka:** `TestSpace` na (0, −500, 0) m, chodba W 8,4 m, světlo u každého socketu, tmavý box proti slunci.
    Podlaha, strop, konce a stropní světla jsou provizorní (drsný `MI_Kit_Halcyon_ProvFloor`, bodovky 45 cd / 90° na
    0,22/0,5/0,78 délky, výplň 8 cd 80 cm pod stropem, WORKFLOW cn). Tag `KitShowroom`, přestavuje se při každém běhu.
- **Výkon ukázky:** GPU 15,8–17 ms ve 1080p (~59–63 FPS), z toho `Lights` 3,4–3,9 ms (60 lineárních světel + displej
  + 6 provizorních). Body místo lineárních světel stály 2,7 ms, ale pálily skvrny a stěny nechaly černé.
- **Procházení ukázky:** klávesa **U** nebo `space.Showroom` (`ASpacePlayerController::ToggleInteriorAt`, tag
  `KitShowroomSpawn`), zpět stejně. Import staví gravitační objem (tag `KitShowroom`) a startovní bod; tmavý box
  proti slunci je bez kolize (hráč by v něm uvízl).
- **Ladění ukázky za běhu:** `space.KitLight Showroom <Vlastnost> <hodnota>` (i rect světla, např. `CastShadows 1`),
  `space.KitColor PrimaryColor r g b Structure` (materiály ukázky), `space.KitReset`.
- **MegaLights** (`kit_megalights.json`, `kit_megalights_perf.json`, list `Docs/Kit/megalights_compare.png`): bez stínů
  +0,1 ms a stejný obraz, s ray-traced stíny ze všech 67 světel +1,0 ms a kontaktní stíny. VRAM +0,1 GB. První
  zapnutí stínů za běhu dá záškub 140 ms. Rozhodnutí autora čeká (doplněk ve studii světel 26. 9.).
- **Test:** `Tools/Tests/test_kit_showroom.py` (barvy vrcholů přes export z UE, štítky sousedů, gravitace, start,
  kolize boxu).
- **Měření vzhledu** (`measure_look.py`, auto expozice): chodba průměr 0,21, p90 0,35, B/R 0,71, detail 0,025 = v rozsahu
  SC. Kolo 2 (lak metallic 0,45, body, úzké bodovky) mělo 0,14 / 0,27 / 0,58 / 0,024 a stěny 0,06–0,10.

## Interiérový kit, dávka 2: portály, strop, koncové stěny, rohy, přechod (27. 9. 2026)

`Tools/Kit/kit_batch2.py`, stavba `kit_build.py -- batch2` (výstup `ArtSource/Kit/Kit_Batch2.blend`, katalog
`python Tools/Kit/kit_catalog.py 2` → `Docs/Kit/catalog_batch2.png`). `kit_build.jobs()` drží seznam úloh všech
dávek (díl, rozpočet, pohledy renderů); `--only <jména>` postaví vybrané díly.

- **Pivoty:** portál, strop a přechod na ose chodby na začátku modulu (+X podél chodby); koncová stěna a zúžení
  jako stěna (líc +X, šířka podél +Y); roh v bodě, kde se potkají roviny líců.
- **`Section`:** rozměry průřezu z `kit_rules`, `inner(d)` = vnitřní obrys odsazený o d (noha, sklon 3:4, strop;
  vybrání leží uvnitř odsazené čáry sklonu). `ceil_half` = polovina stropu mezi čely vybrání + 2 cm.
- **Portál (0,3 m):**
  - tmavý límec 3,5 cm od stěn přes celou hloubku;
  - rám vystupuje o `portal_protrusion`, zkosené hrany (nesou oděr), šrouby na obou lících, styčníky
    v kolenech, patky se šrouby;
  - každý rám nese jedno číslo na levé noze (tmavá destička 0,98–1,14 m, svislé čelo nohy končí u zlomu 1,27 m;
    F02/G08/H19, v N C21) a socket `SOCKET_Decal_Section` pro číslování přes rozvržení (dávka 6);
  - A: světelný prstenec jen přes zkosení a hlavu, difuzor v drážce mezi lemy s krytkami, lineární světlo pod hlavou;
  - B: šrafovaný výstražný pás 0,3–0,9 m na obou nohách;
  - C: těžší rám s vnitřním žebrem, hlavou prochází kanál a trubka stropního pole B (příruby se šrouby na obou lících).
  Vnější obdélník (0,2 m do stěny, 0,25 m nad strop) je skrytý, na katalogu vypadá jako deska.
- **Strop:**
  - panely: tmavá výplň, tři lisované pásy, poloviční příčné nosníky na koncích (rytmus rámů přes strop).
    A = zapuštěná čtvercová bodovka (lem, tmavá šachta, čočka, dvě lamely; spot 35 cd, 0,6 m 22 cd, 0,3 m je výplň),
    B = vyústění vzduchu jako mřížka z lamel (perforovaná plocha zdálky četla jako černá díra), C = zapuštěné lineární
    svítidlo s příčnými lamelami po 8 cm;
  - otevřené pole: dno 20 cm nad stropem v tmavé primární barvě (ne černé), příčné nosníky, studený servisní pásek,
    zavěšené lineární svítidlo s lemy a lamelami; A = žlab se svazky kabelů, B = kanál a potrubí s barevným kódem;
  - teplé svítící plochy (`Kit_GlowWarm`) mají emisi 7: při 14 byly difuzory ořezaná bílá deska, čitelnost dělají
    lamely, ne nižší emise;
  - světla ve stropě nejvýš ~1,8 m od sebe, jinak vzniknou tmavá místa.
- **Koncová stěna:** obrys průřezu včetně vybrání, tři pole mezi rámy až ke stropu, sokl, kopací panel a lišta
  pokračují ze stěn, hlavový nosník. B má okno pod lištou: rám ve dvou stupních s těsněním, sklo, ostění 14 cm,
  za ním zavřená roleta z tmavých lamel, v nadpraží tlumené neutrální světlo, stavová LED; tmavá zadní deska 20 cm
  za lícem (v 7 cm zakryla ostění). Výhled ven v ukázce není (kritik ho chce, otevřené pro autora).
  Zúžení W→S = koncová stěna s obrysem průlezu S, rámem, výstražným pásem, SERVICE ACCESS a 0,6 m průlezu.
- **Přechod N→W (0,6 m):** obě stěny rozevřené pod 45° v půdorysu, profil lofovaný mezi průřezy (`Part.quads`),
  lišta sleduje klesající zlom, lem a pás vybrání ve stálé výšce 2,1 m, šroubované žebro uprostřed každé šikmé stěny.
  Kritik chce víc (těžký rám portálu N, funkční shluk, sloupek na zlomu) – otevřené.
- **Rohy:**
  - vnitřní roh nepotřebuje poloviny stěn: dva stěnové moduly začínající v rohu se svými sklony protnou do
    úžlabí samy (viditelný je nižší sklon). Díl jen zakryje spoj: A sloupek se zkosenou hranou do místnosti, patkou
    a gumovým chráničem 0,15–1,0 m + nosník v úžlabí + konzole vybrání, B zkosený panel 45° pod zlomem;
  - vnější roh vyplní kvadrant nad zlomem: dvě trojúhelníkové plochy v rovinách sklonů (nároží), nárazník
    přes svislou hranu, gumový nárazník 0,15–1,05 m s výstražným šrafováním na obou čelech, hřebenový nosník,
    vybrání otočené kolem rohu.
- **Decaly dílů:** `label(p, item, bod, normála, xdir, ydir)` – `xdir × ydir` musí být normála plochy, jinak
  `KITBUILD` hlásí „mirrored frame“ (dřív decal tiše ležel rubem, WORKFLOW ct).
- **Trim kitu** (`MI_Kit_*_Trim` na `M_Ship_PBR`): detailní normála a panelové spáry trupu vypnuté (WORKFLOW cu).
- **Ukázka:** `import_kit.SHOWROOM`:
  - `wall_runs` (start, konec, normála, moduly), `run_parts`, `placed`;
  - `place_part` otáčí sockety světel s dílem;
  - stěnový modul má yaw = atan2(normála) a běží podél (sin, −cos) svého yaw;
  - import spadne, když délky modulů nesedí na běh.
  Chodba W 0–9,6 m s portály A/B/C po 2,4 m, zatáčka do L (vnější roh 9,6/1,2, vnitřní 12/−1,2), rameno,
  přechod, pahýl N a koncová stěna N. Provizorní je podlaha a strop nad křižovatkou a přechodem.
  Preset `kit_showroom2.json`.
- **Světla ukázky:** soklová lineární světla zrušená (41 modulů = ~1 ms, podlahu skoro nerozsvítí; s MegaLights se
  mohou vrátit). Provizorní bodovky `prov_spots` = `((x, y), cd[, kužel])`, jen v otevřené části stropu (nad hranou
  zkosení se stíní, WORKFLOW cv). 99 světel, chodba GPU 17,6 ms (52 FPS), křižovatka 16,7 ms (57 FPS).
- **Ladění za běhu bez balení:** `space.Kit <Param> <hodnota> <část jména MI>` a `space.KitLight Showroom …` na
  zabalené hře (presety `kit_rail_noise.json`, `kit_glow_strength.json`); teprve výsledek zapsat do `import_kit.py`.
- **Kritik dávky 2:** 37 → 41 → 44, FAIL; otevřené: okno, kužely/stíny (MegaLights), přechod W→N, materiál kitu,
  displeje a značení. Recenze `Docs/Reviews/2026-09-27_kit_batch2.md`. Autor dávku schválil 27. 9.
- **Po schválení (27. 9.):**
  - **Přístavba ukázky:** uzavřené L jižně od chodby (y −3,6…−8,4). End24W_A → 2,4 m W → zatáčka se zkoseným
    vnitřním rohem B (7,2/−3,6) a vnějším rohem (4,8/−6,0) → 2,4 m ramene → zúžení do průlezu. Vlastní start
    `KitShowroomAnnexSpawn`: klávesa U vede ukázka → přístavba → zpět, `space.Showroom annex`. Preset `kit_annex.json`.
  - **Okno End24W_B:** roleta napůl vytažená (4 ze 7 lamel, spodní lišta, vodicí lišty po stranách), zadní deska
    s otvorem (`_end_base(hole=)`), ostění až k desce. V ukázce je za oknem karta `KitShowroom_WindowStars`
    s `M_Kit_WindowStars`. HLSL hvězd, mlhovin a Mléčné dráhy je z `build_space_scene.py` (čteno přes `ast`, ten
    skript při importu spouští `main()`). Materiál hledá hvězdy podle směru pohledu, takže karta 1,3 m za zdí
    působí jako nekonečno bez paralaxy. Materiál oblohy samotný se nepoužil, protože je `is_sky`.
  - **`Portal_Ring03N_B`:** těžký rám na změně W→N. Rám hluboký 26 cm, stupňovitý límec na obou lících, prstenec
    z A, výstražný pás na hlavici ze strany W, průchod 1,0 m.
  - **MegaLights C:** `SpacePlayerController` nastaví `r.MegaLights.EnableForProject` 1 při vstupu do libovolného
    interiéru a 0 při návratu. Všechna světla ukázky mají `cast_shadows` v levelu (stíny se nepřepínají za běhu:
    první zapnutí dělalo záškub 140 ms). Snímky s volnou kamerou musí MegaLights zapnout samy
    (`kit_showroom2.json` v rozcvičení).
  - **Výkon (C, 1080p, TSR 75 %):** chodba 18,1 ms GPU, křižovatka 18,0 ms (~52–57 FPS). Profil a návrh:
    `Docs/Reviews/2026-09-27_interior_perf_profile.md`. Odrazy Lumenu stojí 2,3–2,8 ms (jejich vypnutí je hlavní
    návrh), stíny 1,1 ms, rozlišení 67 % ušetří 1,6–2,5 ms. Postproces, průsvitnost, práh drsnosti a sběr sond
    nic nedají. Návrh čeká na autora; nová světla přidávat až po něm.

## Poznatky z rozboru interiérů SC (Markom3D, 26. 9. 2026)

Podrobně s časy: `starcitizenreference/ShipDetailing_VideoNotes.md`.
- **Světla:** C2 má ~790 světel, můstek 74, nákladový prostor 160. To je zhruba 1 světlo na m², světlo u
  každého svítidla, lišty i prstence rámů. U nás 35 na celou loď.
  - Cíl: každé svítidlo a svítící lišta své světlo s krátkým dosahem a bez stínu, stíny jen 2–3 hlavní.
  - Akcent u podlahy a pod deskou.
  - Měřit `stat gpu`.
- **Decaly v interiéru:** husté u dveří (značky, čáry, kroužky), na podlaze čáry, pruhy u prahů a nápisy sekcí.
  Na podlaze nákladového prostoru C2 zabírají decaly přes polovinu plochy. Dlouhé čáry dělá natažený kus atlasu.
- **Panely ovladačů:** tištěné zaoblené rámečky skupin s názvem v přerušené horní hraně, oblouky stupnic,
  popisek pod každým ovladačem. Knoflíky jsou jednoduché, jedno velké podsvícené tlačítko, emisní nápisy.
- **Materiály:** plochý lak s variací lesku (skvrny se ukážou v odlesku), žádné otřené hrany. Švy sedadla
  jsou decaly nebo trim sheet.
- Horní plocha desky C2 je velká a čistá: hustotu soustřeď do shluků u funkčních míst.
- **Zavedeno: světla u svítidel** (`Tools/Blender/hs_fixture_lights.py`, recept `interior.fixture_lights`):
  - každý ostrov svítícího materiálu dostane světla po 0,9 m (dosah 1,6 m, bez stínu), odsazená na otevřenou stranu;
  - jména `fix_N`, pawn je zapíná jen s kamerou uvnitř (WORKFLOW cf);
  - Wayfarer 88 světel, kokpit +1,1 ms GPU.
- Zrno interiéru: `GrungeTileCm` 45 a `RoughVariation` 0,35 na vrstveném masteru. Velikost skvrn trupu
  (180 cm) na plochách kokpitu nebyla vidět.

## Sklo kanopy a hologram (26. 9. 2026)

- Odraz skla podle kamery: `MPC_ShipView.InsideView` (1 = kamera hráče v obálce partů `Interior*` lodi, jinak 0)
  nastavuje `ASpaceshipPawn::UpdateViewCollection`. `M_Ship_Glass` míchá `Opacity/Roughness/Specular` (zvenku) a
  `…Inside`. Wayfarer: zvenku 0,7 / 0,03 / 1, zevnitř 0,15 / 0,06 / 0,5.
  - Uvnitř se navíc vypíná `r.Lumen.TranslucencyReflections.FrontLayer.Enable`.
  - Sklo je Surface TranslucencyVolume.
  - Loď s interiérem musí mít `pawn.hide_canopy_in_cockpit: false` (WORKFLOW ca–cb).
- Hologram lodi je vnější obálka: `hs_cockpit._envelope(bm, voxels=160, smooth=30)`, kanopa patří do obálky (jinak
  flood fill vteče do kabiny). Materiál `M_Ship_Holo` je jednostranný (WORKFLOW cc).

## Ovládací moduly kokpitu (hs pipeline)

`hs_cockpit.control_module(g, c, right, up, n, w, h, rows, tree=)` staví pouzdro se šrouby a ovladači v řádcích.
- Druhy ovladačů: `guarded`, `guarded_red`, `rotary`, `rocker`, `button`, `encoder`, `led_w`, `led_o`, `led_blink`.
- Každý ovladač včetně LED má štítek (nepopsaná LED působí jako placeholder). Štítek u okraje modulu padá na
  `edge`, když modul nemá dost místa: rozšiř modul (konzole 18 cm pro tři LED).
- Štítky: položky `ck_*` z knihovny decalů jdou do `hs_cockpit.LABELS` a klade je `hs_interior_decals` (rámeček modulu, dosah 2 cm, šířka ≤ buňka).
- `tree` = plocha, na kterou se modul usadí (`seat`).
- Nový štítek: položka `ck_*` v `ArtSource/Ships/Shared/Decals/decal_library.json` a přestavba atlasu `decal_library.py` (~9 min).
- Neumístěné štítky vypisuje stavba jako `INTDECALS {"labels_failed": …}`.

## Nástrahy (příznak → příčina → oprava)

- **Šedá šachovnice v zabalené hře** (v editoru OK) → `M_KitTrim` se nezkompiloval: chybí usage
  flag (`used_with_nanite`, `used_with_static_mesh`, `used_with_instanced_static_meshes`) nebo
  sampler bez výchozí textury (sRGB `DefaultTexture` na Normal/Linear sampleru = chyba kompilace).
  Hledej „Failed to compile Material“ v `%APPDATA%\Unreal Engine\AutomationTool\Logs\…\Log.txt`. (W 9.3 f)
- **Zevnitř díra / chybí strop / kamera vidí „bez čtvrté stěny“** → UE kreslí jednostranně
  (i když glTF hlásí doubleSided); díl lícem ven. Kontrola `find_interior_holes.py` (rub = únik,
  body < 30 cm od geometrie vyřaď), oprava díl lícem dovnitř / obložení / tmavý plášť. Kamery snímků
  patří dovnitř. (W 9.3 h, i, q)
- **Blikání jen v pohybu** → dvě plochy v jedné rovině (zdvojený díl, stěna na cizí stěně). Měř
  `flicker_check`, maž jen skutečné kopie se stejným obrysem, ne „vše, co se překrývá“ (dlaždice). (W 9.3 p)
- **Průchod ukazuje za rámem panel / zmizela podlaha** → za stěnou kitbashe je další stěna; řez
  podle polohy smazal i vodorovné plochy. Vypiš plochy v objemu průchodu (materiál, normála), maž
  jen svislé. (W 9.3 k)
- **Rám dveří z kitu neprůchozí** → `Door_Frame_Square` má průchod 70 % výšky; měř otvor z vrcholů.
  Rámy jsou procedurální. (W 9.3 n)
- **Nový materiál nečekaně svítí oranžově** → jméno obsahuje `light`/`screen` (první kabel
  „cable_light“). (W 9.3 aa)
- **Modrý povrch se nezbarví** → světlo má opačný odstín; laď nejdřív teplotu světel. Nižší
  metallic zesvětlí, nezbarví. (W 9.3 g)
- **Světla svítí modře** → `unreal.Color(255, 238, 214)` je BGRA; jen keyword `r=, g=, b=, a=`. (W 9.5 e)
- **Světlo za stěnou** nic nesvítí; po přesunu dovnitř měř znovu (200 lm pak přehřálo místnost). (W 9.3 l)
- **Pomalý interiér** → stíny lokálních světel (22 světel = 15 ms z 18). Akcenty a displeje bez
  stínů, pracovním dosah jen na místnost. Interiér je pixel-bound. (W 9.3 r)
- **Statické světlo za běhu nereaguje na `SetIntensity`** → příkazy píšou vlastnosti přímo
  + `MarkRenderStateDirty()`. (W 9.3 j)
- **C++ nenajde herce v buildu** → label je jen editor; používej tagy. (W 9.5 h)
- **Kolize zůstala** → `set_collision_enabled()` se s levelem neuloží; `set_collision_profile_name("NoCollision")`. (W 9.3 t)
- **Sklo/hologram rozbitý** → průsvitné/aditivní materiály nesmí na Nanite; vlastní GLB, import vypne
  `nanite_settings`. `StaticMeshEditorSubsystem` headless = `None`. (W 9.3 u, o)
- **Pin materiálu se nepřipojil** → `Power` má `Base`/`Exp`, `TextureSample` pin `UVs`;
  `connect_material_expressions` jen vrátí False → používej `link()`, který chybu ohlásí. (W 9.3 w)
- **Headless UE Python:** `unreal.Rotator` jen keywordy (poziční = roll, pitch, yaw);
  `spawn_actor_from_object` padá → `spawn_actor_from_class(StaticMeshActor)` + `set_static_mesh`;
  `rerun_construction_scripts` není → `UFUNCTION(BlueprintCallable)`; `get_editor_property("relative_location")`. (W 9.5)
- **Blender bmesh:** `faces.new()` má nulovou normálu do `bm.normal_update()`, nové vrcholy index −1
  do `bm.verts.index_update()`. (W 9.3 s)
- **Opotřebení uprostřed ploch** → procedurální díly mají UV na náhodném místě atlasu kitu; wear jen
  slabě a na hranách. (W 9.3 y)
- **Meshy vrátí celou sestavu** místo dílu → samostatné předměty (sedadlo, panel, skříň) umí, pult na
  míru ne. Každý díl prohlédni ze 3 stran v Blenderu před zapojením. Generování:
  `python Tools/Assets/meshy_generate.py --spec ArtSource/Ships/Steadfast/Kitbash/meshy_parts.json
  --out ArtSource/Ships/Steadfast/Kitbash/Meshy --refine` (10 kreditů/díl, klíč
  `C:\gamespace\secrets\meshy.key` → `MESHY_API_KEY`, nikdy do repa). (W 9.3 x)
- **Text v AI obrázku:** zadávej pevnou mřížku („exact 4 by 4 grid, one element centered in each
  cell, black background“), políčka se pak řežou výpočtem. (W 9.3 z)
- **Scénář přepínač běžel dvakrát** (opraveno v `SpaceShotRunner.cpp`) - příkazy scénáře drž idempotentní. (W 9.3 m)
- Assety načítané podle cesty musí být v `DirectoriesToAlwaysCook` (`/Game/Environments` už je). (W 9.3 b)

Podrobnosti a historie: HANDOFF body 58–75, WORKFLOW 9.3 f–aa a 9.5.
