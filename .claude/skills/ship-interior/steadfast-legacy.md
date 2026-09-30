# Starý interiér Steadfastu: pipeline a skripty

Referenční část skillu `ship-interior`. Zkušební interiér Steadfastu (strojovna | nákladový prostor | chodba |
dveře | kokpit) stojí v `TestSpace` 500 m stranou od lodi (klávesa I). Autor ho 24. 9. 2026 odmítl; nový
Steadfast se staví podle 2D návrhu v2. Skripty jsou pracovní pipeline a zdroj ověřených postupů, ne cílový vzhled.

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
