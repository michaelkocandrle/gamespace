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
