---
name: blender-mcp
description: Blender 5.2 in the gamespace project - running the headless builders in Tools/Blender/*.py (build_ai_ship.py, gamespace_ship_export.py, bake_ship_ao.py, fit_ship_interior.py, build_steadfast_interior.py...) with MSYS_NO_PATHCONV=1 from Git Bash, and the live Blender MCP on localhost:9876 (execute_blender_code, get_viewport_screenshot, Tools/Blender/mcp/mcp_socket.py, eye view, display corners). Load it whenever you run or edit a Blender script, drive Blender through MCP, use bpy/bmesh, or hit a Blender pipeline trap.
---

# Blender v gamespace: headless buildery a živý Blender MCP

Pravda je vždy **skript + recept v gitu**, nikdy ručně upravený `.blend` ani živé úpravy v GUI.
Autor v Blenderu neklikává – všechno jde přes `blender -b --python …` nebo přes MCP.

## Cesty a spouštění

- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
  (Git Bash: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"`).
- **Z Git Bash vždy `MSYS_NO_PATHCONV=1`**, jinak MSYS přepíše `/c/...` i Blenderovské `//Export`
  a skript tiše pracuje se špatnou cestou.
- Argumenty skriptu jdou za `--`. Výstup skriptů hledej podle prefixu v printu (např. `MCPINSTALL`,
  `HOLES <n>`).
- Delší Python piš nástrojem Write do scratchpadu a spouštěj soubor (heredoc + apostrofy se rozbijí);
  v cestách uvnitř Python řetězců `r"..."` (jinak `\U` = unicode escape).
- Běžící GUI Blender **drží .blend** – před headless buildem, který ho ukládá, GUI zavři.

```bash
cd /c/gamespace/gamespace
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
# AI loď -> herní .blend podle receptu (--no-save jen vyzkouší)
MSYS_NO_PATHCONV=1 "$B" -b --python Tools/Blender/build_ai_ship.py -- ArtSource/Ships/Vanguard/Vanguard_ai_build.json
# export FBX + manifest (z adresáře lodi kvůli //Export)
cd ArtSource/Ships/Vanguard
MSYS_NO_PATHCONV=1 "$B" -b Vanguard_Meshy.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"
```

Výstup exportu: `ArtSource/Ships/Vanguard/Export/Vanguard_manifest.json` + FBX na díl. Import do
Unrealu je `Tools/Assets/import_ship.py` (přes `Tools\run_editor_python.ps1`, nástrojem PowerShell,
podrobně WORKFLOW 2.2) – to už není Blender.

## Skripty v `Tools/Blender/`

| Skript | Spuštění / účel |
| --- | --- |
| `build_ai_ship.py` | `-b --python … -- <Loď>_ai_build.json [--no-save]`. Recept: import → orient → split → decimate → UV + rebake → interior (fit, decimate 150k, rebake 4K, uv_focus, displays) → canopy_clear → canopy_frame → lining → sockets. Podrobně WORKFLOW 2.1, ShipPipeline 2B. |
| `gamespace_ship_export.py` | `-b Ship.blend --python … -- --out "//Export" [--validate-only] [--force]`. Bez Blenderu: `python Tools/Blender/gamespace_ship_export.py --check-manifest <manifest.json>`. Konvence `SM_Ship_<Loď>[_<Díl>][_LOD<n>]`, `UCX_<Mesh>_<NN>`, `SOCKET_<Jméno>`; zbytek (HIGH_, světla, kamery) se ignoruje. |
| `bake_ship_ao.py` | `-b ArtSource/Ships/<Loď>/<Loď>_Meshy.blend --python … -- <Loď>` → `Textures/T_Ship_<Loď>_AO.png` (ORM okluzi nemá, R kanál = maska displejů). |
| `fit_ship_interior.py` | `-b <Loď>_Meshy.blend --python … -- <recept>`: najde měřítko/polohu AI kokpitu v kabině a oko. Výsledek ručně do receptu (`interior.placement`, `sockets.Cockpit`) a `<Loď>_setup.json`. |
| `cockpit_view_survey.py` | `-b Vanguard.blend --python … -- 520 0 110 88` (oko X Y Z v UE cm, FOV). Paprsky: % volného výhledu. Blender m = UE cm / 100, Y zrcadlené. |
| `split_ship_gear.py` | Jednorázově oddělí podvozek do `SM_Ship_<Loď>_Gear` a uloží .blend (`--dry-run`). |
| `build_steadfast_interior.py` | `-b --python …`: interiér Steadfastu z `CargoBay_Shell.glb` + Quaternius kitu (`ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip`, mimo git) → GLB místností + `Interior_layout.json` v `ArtSource/Ships/Steadfast/Interior/`. |
| `find_interior_holes.py` | `-b --python …`: díry v interiéru paprsky, na konci `HOLES <n>` (0 = zavřeno). |
| `recolour_kit.py` | Přebarví kit do palety (gunmetal + oranžový akcent). `blender <soubor.blend> --python …` nebo přes MCP `exec(open(r"…").read())`. Idempotentní (značka `recoloured`). |
| `tests/test_ship_export_core.py` | Čistý Python bez Blenderu: `python Tools/Blender/tests/test_ship_export_core.py`. |

Souřadnice: Blender je pravotočivý Z-up v metrech, loď nosem do +X; Unreal levotočivý Z-up v cm,
Y zrcadlené.

## Živý Blender MCP (současný: komunitní ahujasid/blender-mcp)

K čemu: dívat se modelu z oka pilota a ladit (rohy displejů, rám, světla, kitbash díly) bez stovek
headless renderů. Server na `localhost:9876` spouští libovolný Python ve scéně (jen lokálně).

### Stav instalace (hotovo, jen pro obnovu – podrobně WORKFLOW 3.1)

- Server v Claude Code se jmenuje `blender`, stdio, scope **local pro `C:\gamespace`** (session
  otevřená jinde ho nedostane), příkaz = plná cesta k `uvx.exe`
  (`C:/Users/micha/AppData/Local/Microsoft/WinGet/Packages/astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe/uvx.exe`) + `blender-mcp`:
  ```
  claude mcp add blender -e DISABLE_TELEMETRY=true -- <plná cesta>\uvx.exe blender-mcp
  ```
  **`DISABLE_TELEMETRY=true` je povinné** – balík jinak posílá autorovi balíku data o použití
  vč. screenshotů a stavu scény.
- `uvx blender-mcp` bez verze stahuje nejnovější balík; nástroje se tím mění (dnes navíc
  `get_addon_status`, `bpy_api_lookup`, `describe_node_type`, `disable_telemetry`…). Když se
  addon a server rozejdou, přeinstaluj addon.
- Addon do Blenderu: `blender -b --python Tools/Blender/mcp/install_blender_mcp_addon.py`
  (vezme `bundled/addon.py` z uv cache, `addon_refresh`, zapne `blender_mcp_addon`, vypne
  `telemetry_consent`, uloží prefs). Předtím musí jednou proběhnout `uvx blender-mcp`.
- Nástroje MCP serveru se načtou jen při startu session; po změně registrace restart Claude Code.

### Použití

1. Blender **s GUI** na pozadí (socket běží jen s GUI; v `-b` se addon jen zaregistruje):
   ```bash
   cd /c/gamespace/gamespace && MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" ArtSource/Ships/Vanguard/Vanguard_Meshy.blend
   ```
   (spusť na pozadí, `run_in_background`).
2. Na začátku `get_addon_status()` (verze Blenderu) a `get_scene_info()`.
3. Nástroje `blender`: `execute_blender_code`, `get_viewport_screenshot`, `get_object_info`…
   Některé chtějí argument `user_prompt`.
4. Když MCP nástroje v session nejsou, mluv se socketem přímo skripty v `Tools/Blender/mcp/`
   (spouštěj obyčejným `python`):

| Skript | Co dělá |
| --- | --- |
| `mcp_socket.py` | `send(type, params)`; CLI `python mcp_socket.py execute_code '{"code": "..."}'` |
| `mcp_eye_view.py out.png` | kamera `EyeCam` v oku Vanguardu (1,74 / 0 / 1,89 m, FOV 88°), backface culling jako v UE, screenshot |
| `mcp_grid.py out.png` | měřicí mřížka na rovině displeje (1 cm žlutá, 5 cm červená, osy zelené) |
| `mcp_measure_openings.py` | paprsky z oka: najde otvor v rámečku a vypíše rohy (u, v) |
| `mcp_corners.py '<json>' out.png` | posune plochy displejů na zadané rohy a vyfotí pohled z oka |

Pozn.: `mcp_*` skripty mají natvrdo Vanguard (`Vanguard_ai_build.json`, `SM_Ship_Vanguard_Interior`).

5. Po skončení Blender **zavři** (drží .blend, build receptu pak selže na zápisu).

### Ladění rohů displejů (podrobně WORKFLOW 3.2 bod 3)

Pohled z oka → mřížka, odečti rohy otvoru → `mcp_corners.py` s kandidátem, prohlédni zoom →
opakuj → rohy zapiš do receptu (`interior.displays.screens[].corners`, TL TR BR BL v m (u, v)) →
plný build (build_ai_ship + export + import_ship) → snímky `cockpit` ze zabalené hry.
Nový otvor bez plochy displeje: paprsky z oka přes pixely otvoru, rovina SVD, `u` = (0, −1, 0),
`v` = normála × `u`; flood fill zkosí spodní hranu o knoflíky – oprav ručně podle zoomu.

### Kód v `execute_blender_code`

- Uzly shaderu hledej **podle typu**, ne jména (lokalizace UI):
  `next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")`.
- Enum hodnoty nehardcoduj, čti je z `bl_rna.properties[...].enum_items`.
  `scene.render.engine` přiřazuj v `try/except TypeError`.
- Barvu materiálu nastavuj na vstupech uzlu, `material.diffuse_color` je jen viewport.
- Objekty vytvářej `bpy.data.objects.new(...)` + `collection.objects.link(...)`.

## Operátory vs. bmesh (platné pravidlo do kroku 3)

- **Přes MCP zatím nepoužívej `bpy.ops`** pro práci s geometrií: `bpy.ops.object.join` a spol.
  padají na `poll() failed, context is incorrect` (chybí kontext viewportu). Geometrii skládej
  přes `bmesh`, objekty přes `bpy.data.objects.new`.
- Výjimky, které fungují: `bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP")`,
  `bpy.ops.render.render(write_still=True)`; v headless skriptech (`-b`) jsou operátory běžně
  použité (import, bake, `preferences.addon_refresh`).
- Toto pravidlo se po kroku 3 mění, viz sekce „Operátory přes MCP“.

## Oficiální Blender MCP (Blender Lab)

TODO: doplní krok 2

## Operátory přes MCP

TODO: doplní krok 3

## Nástrahy (příznak → příčina → řešení)

**Prostředí**
- Cesty v Blenderu nesedí / `//Export` skončí jinde → Git Bash přepisuje cesty →
  `MSYS_NO_PATHCONV=1` (WORKFLOW 9.1 d).
- `uvx`/nástroj z wingetu „neexistuje“ → PATH se projeví až po restartu terminálu → plná cesta
  (9.1 e).
- Addon po zkopírování nevidět → chybí `bpy.ops.preferences.addon_refresh()` (9.1 f).
- MCP nic nevrací / connection refused → Blender běží v `-b` nebo neběží → spusť s GUI.
- Build receptu selže na zápisu .blend → otevřený GUI Blender ho drží → zavři ho.

**Snímky z živého Blenderu**
- Snímek ukazuje stav před změnou → `get_viewport_screenshot` fotí před překreslením →
  nejdřív `bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP")`.
- `get_viewport_screenshot` chce **absolutní** cestu k souboru.
- Díl ~10 cm je na screenshotu tři pixely a nastavení `region_3d` se neprojeví → renderuj kamerou
  do souboru (Workbench, `bpy.ops.render.render(write_still=True)`) a soubor si přečti.
  Nový díl vždy ze tří stran, než ho zapojíš (9.3 x).
- Snímek z kamery otočený o 90° → `to_track_quat("Z", "Y")` → správně `to_track_quat("-Z", "Y")`.
- Měření z oka nesedí → oko je navržené pro 16:9 a FOV 88°, jiný FOV dává jiná čísla (9.6 e).
- Zevnitř vidět ven, i když v Blenderu je stěna → Unreal kreslí jednostranně → v Blenderu zapni
  `use_backface_culling` (dělá `mcp_eye_view.py`); díry hledej paprsky (`find_interior_holes.py`),
  rub = zásah s `normal.dot(směr) > 0` (9.3 h, q).

**bmesh**
- Otočení ploch „k místnosti“ podle normály nic nedělá → `bm.faces.new()` má nulovou normálu →
  `bm.normal_update()` (9.3 s).
- Mapování podle indexu vrcholu se rozsype → nové vrcholy mají `index` −1 →
  `bm.verts.index_update()` (totéž `faces`/`edges`).
- Po úpravě `bm.to_mesh(me); me.update(); bm.free()`.

**Pipeline lodí (9.6)**
- Rám displeje otočený dvakrát → rotace v placement matici i v osách `u`/`v` → `add_displays`
  dostává matici bez rotace.
- Otvory rámečků AI modelu nejsou obdélníky → `corners`, ne `rect`, a ladění z oka.
- Trup zevnitř průhledný (jednostranný) → krok `lining`; u oka blízko křídla je vidět hrubá geometrie.
- Světlý proužek AI skla v rozích displeje → `grow_m` 0,0045 (displej o ~5 mm pod hranu rámečku);
  malé displeje ve sloupku `cut_depth_m` 6 mm, jinak řez utrhne knoflíky.
- Známá neopravená vada: pravý displej Vanguardu má vlevo dole zubatou hranu z AI textury.
- Po odebrání hodnoty ze `<Loď>_setup.json` zůstane v Blueprintu stará (9.3 c) – to je strana Unrealu.
- Interiér nesmí mít Nanite (`no_nanite_parts: ["Interior"]`), sklo/hologramy jako vlastní mesh
  bez Nanite (9.2 a, 9.3 u).

## Kam dál

- Recept a displeje: WORKFLOW 2.1; import do UE: WORKFLOW 2.2; celý postup lodi: `Docs/Ships/ShipPipeline.md` (2B).
- Modulární díly / kitbash místo jednoho promptu: `Docs/AssetPipeline_Modular.md`.
- Úplný seznam nástrah: WORKFLOW kap. 9.
