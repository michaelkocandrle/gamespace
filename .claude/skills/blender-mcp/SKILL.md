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
MSYS_NO_PATHCONV=1 "$B" -b --python Tools/Blender/build_ai_ship.py -- ArtSource/Ships/<Loď>/<Loď>_ai_build.json
# export FBX + manifest (z adresáře lodi kvůli //Export)
cd ArtSource/Ships/<Loď>
MSYS_NO_PATHCONV=1 "$B" -b <Loď>.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"
```

Výstup exportu: `ArtSource/Ships/<Loď>/Export/<Loď>_manifest.json` + FBX na díl. Import do
Unrealu je `Tools/Assets/import_ship.py` (přes `Tools\run_editor_python.ps1`, nástrojem PowerShell,
podrobně WORKFLOW 2.2) – to už není Blender.

## Skripty v `Tools/Blender/`

| Skript | Spuštění / účel |
| --- | --- |
| `build_ai_ship.py` | `-b --python … -- <Loď>_ai_build.json [--no-save]`. Recept: import → orient → split → decimate → UV + rebake → interior (fit, decimate 150k, rebake 4K, uv_focus, displays) → canopy_clear → canopy_frame → lining → sockets. Podrobně WORKFLOW 2.1, ShipPipeline 2B. |
| `gamespace_ship_export.py` | `-b Ship.blend --python … -- --out "//Export" [--validate-only] [--force]`. Bez Blenderu: `python Tools/Blender/gamespace_ship_export.py --check-manifest <manifest.json>`. Konvence `SM_Ship_<Loď>[_<Díl>][_LOD<n>]`, `UCX_<Mesh>_<NN>`, `SOCKET_<Jméno>`; zbytek (HIGH_, světla, kamery) se ignoruje. |
| `bake_ship_ao.py` | `-b ArtSource/Ships/<Loď>/<Loď>_Meshy.blend --python … -- <Loď>` → `Textures/T_Ship_<Loď>_AO.png` (ORM okluzi nemá, R kanál = maska displejů). |
| `fit_ship_interior.py` | `-b <Loď>_Meshy.blend --python … -- <recept>`: najde měřítko/polohu AI kokpitu v kabině a oko. Výsledek ručně do receptu (`interior.placement`, `sockets.Cockpit`) a `<Loď>_setup.json`. |
| `cockpit_view_survey.py` | `-b <Loď>.blend --python … -- <X> <Y> <Z> <FOV>` (oko X Y Z v UE cm, FOV). Paprsky: % volného výhledu. Blender m = UE cm / 100, Y zrcadlené. |
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
   cd /c/gamespace/gamespace && MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" ArtSource/Ships/<Loď>/<Loď>.blend
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
| `mcp_eye_view.py out.png` | kamera `EyeCam` v oku (poloha je ve skriptu, uprav pro danou loď; FOV 88°), backface culling jako v UE, screenshot |
| `mcp_grid.py <Loď> out.png` | měřicí mřížka na rovině displeje (1 cm žlutá, 5 cm červená, osy zelené) |
| `mcp_measure_openings.py <Loď>` | paprsky z oka: najde otvor v rámečku a vypíše rohy (u, v) |
| `mcp_corners.py <Loď> '<json>' out.png` | posune plochy displejů na zadané rohy a vyfotí pohled z oka |

Pozn.: `mcp_grid`, `mcp_measure_openings` a `mcp_corners` berou jméno lodi jako první argument
(čtou `ArtSource/Ships/<Loď>/<Loď>_ai_build.json` a objekt `SM_Ship_<Loď>_Interior`).

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

## Oficiální Blender MCP (Blender Lab) – `blender-lab`, port 9877

Od 24. 9. 2026 běží **oba servery naráz** v jednom Blenderu, každý na svém portu:

| | `blender` (komunitní ahujasid) | `blender-lab` (oficiální, blender.org/lab) |
| --- | --- | --- |
| Port addonu | 9876 | **9877** (přenastaveno, výchozí je také 9876) |
| Addon v Blenderu | `blender_mcp_addon` (scripts/addons) | rozšíření `bl_ext.user_default.mcp` (extensions/user_default/mcp), v1.0.3 |
| Server v Claude Code | `uvx.exe blender-mcp` (PyPI), `DISABLE_TELEMETRY=true` | `uvx.exe --from git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp blender-mcp`, env `BLENDER_MCP_PORT=9877`, `BLENDER_PATH=<blender.exe>` |
| Protokol socketu | JSON `{"type","params"}` → `Tools/Blender/mcp/mcp_socket.py` | JSON `{"type":"execute","code","strict_json"}` + NUL → `Tools/Blender/mcp/lab_socket.py` |
| Silné stránky | screenshot viewportu, Poly Haven / Sketchfab / Hyper3D / Hunyuan importy | dokumentace bpy API a manuálu (`get_python_api_docs`), screenshot okna nebo oblasti, souhrny .blend, `*_for_cli` nástroje v Blenderu na pozadí bez GUI, žádná telemetrie |

`blender-lab` je scope **local** pro `C:\gamespace` i `C:\gamespace\gamespace`; `blender` jen pro `C:\gamespace`.

- **Online přístup:** oficiální addon startuje jen s povoleným online přístupem.
  - Buď Blender spusť s `--online-mode` (platí jen pro to spuštění),
  - nebo autor jednou zapne *Preferences → System → Network → Allow Online Access* (**zapnuto 24. 9. 2026**, takže obyčejné spuštění Blenderu stačí).
  - Bez toho port 9877 neposlouchá a v preferencích addonu je chyba „online access“.
- **Instalace (hotovo, pro obnovu):**
  - Addon: `blender --command extension install-file -r user_default --enable mcp-1.0.3.zip`. Zip je z `https://projects.blender.org/lab/blender_mcp/releases`.
  - Pak v `-b` nastav `prefs.port = 9877`, `use_autostart = True` a `bpy.ops.wm.save_userpref()`.
  - Server: `claude mcp add blender-lab -s local -e BLENDER_MCP_PORT=9877 -e "BLENDER_PATH=..." -- <uvx.exe> --from "git+...@v1.0.3#subdirectory=mcp" blender-mcp`.
- **Pozor:** **neinstaluj oficiální server jako `uv tool install blender-mcp`.**
  - Obě implementace mají spustitelný soubor `blender-mcp`.
  - `uvx blender-mcp` (komunitní) by pak spouštěl nainstalovaný tool, tedy oficiální server.
- **Přepínání:** nic přepínat není potřeba, oba běží naráz.
  - Když by jeden překážel: `claude mcp remove <jméno> -s local` a potom restart Claude Code.
  - Addon se vypíná v Preferences, nebo `addon_utils.disable(...)` a `save_userpref`.
- **Srovnání:** viz tabulka níže.

### Srovnání na stejné úloze (24. 9. 2026, Blender 5.2.2, oba servery v jednom GUI Blenderu)

Úloha: panel 1,2 × 0,1 × 0,8 m, `mesh.bevel` s profilem přes `ops_context`, pak výpis scény,
screenshot a dokumentace `bpy.ops.mesh.bevel`.

| Krok | `blender-lab` (oficiální) | `blender` (komunitní) |
| --- | --- | --- |
| `execute_blender_code` | OK: 98 ploch, 3,6 ms. Vrací proměnnou `result` (dict jako JSON), stdout zvlášť. | OK: 98 ploch, 3,1 ms. Vrací jen text ze `print`. Každé volání chce `user_prompt`. |
| Scéna | `get_objects_summary`: strom kolekcí, výběr, viditelnost, aktivní objekt, režim. | `get_scene_info`: plochý seznam s polohou objektů. |
| Screenshot | `get_screenshot_of_area_as_image`: skutečné pixely okna v plném rozlišení, i s UI a překryvy. **Splash screen po startu zakryl scénu**, Blender proto spouštěj rovnou s .blend souborem; s otevřeným souborem se splash nezobrazí. | `get_viewport_screenshot`: čistý snímek viewportu (max 1000 px) bez splash a bez panelů. |
| Dokumentace API | `get_python_api_docs` / `search_api_docs` / `search_manual_docs`: offline RST dokumentace i manuál, s popisem a fulltextem. | `bpy_api_lookup`: živá introspekce RNA běžícího Blenderu, JSON s rozsahy a defaulty. Přesná pro danou verzi, bez manuálu. |
| Práce bez GUI | `*_for_cli` nástroje: **v Claude Code na Windows vyprší po 120 s** (i na 1MB souboru). Stejný `run_blender_cli` spuštěný ručně doběhne za 6 s, chyba je v běhu pod MCP. Místo nich používej naše headless skripty (`blender -b --python …`). | nemá |
| Navíc | `jump_to_*` (přepnutí záložky, fokus na objekt), `render_viewport_to_path`, `render_thumbnail_to_path`, souhrny .blend (chybějící soubory, knihovny). | Poly Haven, Sketchfab, Poly Pizza, Hyper3D, Hunyuan3D importy. |
| Soukromí | žádná telemetrie | nutné `DISABLE_TELEMETRY=true` |

**Doporučení:**
- Na práci se scénou a na dokumentaci je výchozí `blender-lab`: strukturovaný výsledek, dokumentace i manuál, žádná telemetrie.
- `blender` zůstává na čisté screenshoty viewportu a na importy z Poly Haven / Sketchfab.
- Obojí běží naráz, takže se volí podle úlohy.

## Operátory přes MCP – helper `Tools/Blender/mcp/ops_context.py`

Staré pravidlo „přes MCP žádné operátory“ už neplatí. Operátory padaly na
`poll() failed, context is incorrect` jen kvůli chybějícímu kontextu okna. Helper najde okno, oblast
`VIEW_3D` a její region a operátor spustí v `bpy.context.temp_override(window, area, region,
active_object, selected_objects…)`:

```python
import sys; sys.path.insert(0, r"C:\gamespace\gamespace\Tools\Blender\mcp")
from ops_context import run_op, edit_mode, OpsContextError
run_op("object.join", active=hull, selected=[hull, fin])
run_op("object.modifier_apply", active=ob, selected=[ob], modifier="Bevel")
with edit_mode(panel):
    run_op("mesh.select_all", active=panel, action="SELECT")
    run_op("mesh.bevel", active=panel, offset=0.02, segments=3, profile=0.7, affect="EDGES")
```

Test: `Tools/Blender/mcp/test_ops_context.py`. Headless se spouští
`blender -b --factory-startup --python …`, přes MCP `exec(open("C:/gamespace/…/test_ops_context.py").read())`
(cestu piš s `/`; `\t` v cestě by byl tabulátor). Výsledek 24. 9. 2026, Blender 5.2:

| Operátor | Headless `-b` | Živý Blender přes 9876 i 9877 |
| --- | --- | --- |
| `object.join` | OK | OK |
| `object.modifier_apply` (bevel) | OK | OK |
| `mesh.bevel` s profilem | OK | OK |
| boolean EXACT (modifier + apply) | OK | OK |
| `mesh.inset` (individual) | OK | OK |
| `mesh.knife_project` | **SKIP** – helper vrátí `OpsContextError` | OK (pohled shora ortho, `rv3d.update()`) |

- V Blenderu 5.2 prošel přes oba servery i holý `bpy.ops.object.join()` bez helperu. Helper přesto
  používej: nastaví i výběr a aktivní objekt, vrací čitelnou chybu a funguje stejně headless.
- **Headless past:** `blender -b` má okno a oblasti ze startup souboru, ale nikdy se nevykreslí.
  Operátory promítající z pohledu (`knife_project`, `view3d.*`, `transform.*`) pak **tiše nic
  neudělají**. Helper je proto v `-b` odmítne (`bpy.app.background`).
- `knife_project` potřebuje řezací objekt s **okrajovými nebo drátovými hranami** (plocha, křivka).
  Uzavřená krychle nestačí: „No other selected objects have wire or boundary edges“.
- **bmesh zůstává alternativou** pro čistě geometrické operace bez kontextu (`bmesh.ops.bevel`,
  `inset_region`, `bisect_plane`, `create_grid`…). Je rychlejší ve smyčkách a funguje všude.
  Po vytvoření ploch zavolej `normal_update()`, u nových prvků `index_update()`.

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
- Po odebrání hodnoty ze `<Loď>_setup.json` zůstane v Blueprintu stará (9.3 c) – to je strana Unrealu.
- Interiér nesmí mít Nanite (`no_nanite_parts: ["Interior"]`), sklo/hologramy jako vlastní mesh
  bez Nanite (9.2 a, 9.3 u).

## Kam dál

- Recept a displeje: WORKFLOW 2.1; import do UE: WORKFLOW 2.2; celý postup lodi: `Docs/Ships/ShipPipeline.md` (2B).
- Modulární díly / kitbash místo jednoho promptu: `Docs/AssetPipeline_Modular.md`.
- Úplný seznam nástrah: WORKFLOW kap. 9.
