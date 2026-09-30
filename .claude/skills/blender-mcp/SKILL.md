---
name: blender-mcp
description: Blender 5.2 in the gamespace project - running the headless builders in Tools/Blender/*.py and Tools/Kit/*.py (hs_build_ship.py, hs_assemble_ship.py, gamespace_ship_export.py, kit_build.py, check_ship_geometry.py...) with MSYS_NO_PATHCONV=1 from Git Bash, and the live Blender MCP servers blender-lab (:9877, official) and blender (:9876, community) for inspection (execute_blender_code, screenshots, Tools/Blender/mcp/*.py, ops_context.py for operators, eye view). Reference file reference.md covers installation/recovery and display-corner tuning of the older AI recipe. Load it whenever you run or edit a Blender script, drive Blender through MCP, use bpy/bmesh, or hit a Blender pipeline trap.
---

# Blender v gamespace: headless buildery a živý Blender MCP

Pravda je vždy **skript + recept v gitu**, nikdy ručně upravený `.blend` ani živé úpravy v GUI.
Autor v Blenderu neklikává – všechno jde přes `blender -b --python …`. **MCP slouží k prohlížení a ladění
(pohled z oka, screenshot, dotaz na scénu); stavba je vždy headless skriptem.**

## Cesty a spouštění

- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
  (Git Bash: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"`).
- **Z Git Bash vždy `MSYS_NO_PATHCONV=1`**, jinak MSYS přepíše `/c/...` i Blenderovské `//Export`
  a skript tiše pracuje se špatnou cestou.
- Argumenty skriptu jdou za `--`. Výstup skriptů hledej podle prefixu v printu (např. `HSASSEMBLE`,
  `GEOTEST`, `KITBUILD`, `HOLES <n>`).
- Delší Python piš nástrojem Write do scratchpadu a spouštěj soubor (heredoc + apostrofy se rozbijí);
  v cestách uvnitř Python řetězců `r"..."` (jinak `\U` = unicode escape).
- Běžící GUI Blender **drží .blend** – před headless buildem, který ho ukládá, GUI zavři.

```bash
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
# loď z výkresu (skill ship-pipeline 3b2), z kořene repozitáře
MSYS_NO_PATHCONV=1 "$B" -b --factory-startup --python Tools/Blender/hs_build_ship.py -- ArtSource/Ships/<Loď>/HardSurface/<Loď>_hs.json
MSYS_NO_PATHCONV=1 "$B" -b ArtSource/Ships/<Loď>/HardSurface/<Loď>_HS.blend --python Tools/Blender/hs_assemble_ship.py -- ArtSource/Ships/<Loď>/HardSurface/<Loď>_hs.json
# export FBX + manifest (z adresáře lodi kvůli //Export)
cd ArtSource/Ships/<Loď>
MSYS_NO_PATHCONV=1 "$B" -b <Loď>_HS_Game.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"
```

Výstup exportu: `ArtSource/Ships/<Loď>/Export/<Loď>_manifest.json` + FBX na díl. Import do Unrealu je
`Tools/Assets/import_ship.py` přes `Tools\run_editor_python.ps1` nástrojem PowerShell (skill `ship-pipeline` 6).

## Skripty v `Tools/Blender/`

| Skript | Spuštění / účel |
| --- | --- |
| `hs_build_ship.py`, `hs_assemble_ship.py` | loď z výkresu: díly z obrysů, detail, decaly, vrstvy, světla → `<Loď>_HS_Game.blend`; na konci `test_ship_geometry.py` (skill `ship-pipeline` 3b2) |
| `hs_interior.py`, `hs_cockpit.py`, `hs_interior_decals.py`, `hs_fixture_lights.py` | interiér a kokpit v receptu lodi (skill `ship-interior`) |
| `gamespace_ship_export.py` | `-b Ship.blend --python … -- --out "//Export" [--validate-only] [--force]`. Bez Blenderu: `python Tools/Blender/gamespace_ship_export.py --check-manifest <manifest.json>`. Konvence `SM_Ship_<Loď>[_<Díl>][_LOD<n>]`, `UCX_<Mesh>_<NN>`, `SOCKET_<Jméno>`; zbytek (HIGH_, světla, kamery) se ignoruje. |
| `check_ship_geometry.py` | kontrola geometrie lodi (volá `python Tools/Tests/test_ship_geometry.py`) |
| `silhouette_compare.py` | masky a IoU siluety proti výkresu / konceptu (skill `ship-pipeline` 3b) |
| `cockpit_view_survey.py` | `-b <Loď>.blend --python … -- <X> <Y> <Z> <FOV>` (oko v UE cm): % volného výhledu. Blender m = UE cm / 100, Y zrcadlené. |
| `eye_view_metrics.py` | metriky pohledu z oka (výhled, deska, sloupky) proti cílům kokpitu |
| `find_interior_holes.py` | díry v interiéru paprsky, na konci `HOLES <n>` (0 = zavřeno) |
| `build_ai_ship.py`, `fit_ship_interior.py`, `bake_ship_ao.py`, `split_ship_gear.py` | starší AI recept lodi (`ship-pipeline/legacy-ai-model.md`) |
| `build_steadfast_interior.py`, `recolour_kit.py` | starý interiér Steadfastu z kitu Quaternius (`ship-interior/steadfast-legacy.md`) |
| `tests/test_ship_export_core.py`, `tests/test_silhouette_compare.py` | čistý Python, spouští `Tools/Test.ps1` |

Kit interiéru má vlastní skripty v `Tools/Kit/` (skill `ship-interior`). Souřadnice: Blender je pravotočivý Z-up
v metrech, loď nosem do +X; Unreal levotočivý Z-up v cm, Y zrcadlené.

## Živý Blender přes MCP: dva servery naráz

Oba běží v jednom Blenderu s GUI, každý na svém portu (instalace a obnova: `reference.md`):

| | `blender-lab` (oficiální, blender.org/lab) | `blender` (komunitní ahujasid) |
| --- | --- | --- |
| Port addonu | **9877** | 9876 |
| Protokol socketu | JSON `{"type":"execute","code","strict_json"}` + NUL → `Tools/Blender/mcp/lab_socket.py` | JSON `{"type","params"}` → `Tools/Blender/mcp/mcp_socket.py` |
| Na co | **výchozí** pro práci se scénou a dokumentaci: strukturovaný výsledek (`result`), `get_objects_summary`, `get_python_api_docs` / `search_api_docs` / `search_manual_docs`, screenshot okna nebo oblasti, souhrny .blend; žádná telemetrie | čistý screenshot viewportu (`get_viewport_screenshot`, max 1000 px), importy Poly Haven / Sketchfab / Poly Pizza; každé volání chce `user_prompt`; nutné `DISABLE_TELEMETRY=true` |

- `blender-lab` je scope local pro `C:\gamespace` i `C:\gamespace\gamespace`; `blender` jen pro `C:\gamespace`.
- **Online přístup** v Blenderu je zapnutý (24. 9. 2026); bez něj port 9877 neposlouchá.
- Nástroje `*_for_cli` z `blender-lab` v Claude Code na Windows vyprší po 120 s → místo nich headless skripty.
- Splash screen po startu zakryje scénu na screenshotu z `blender-lab` → spouštěj Blender rovnou s .blend.

### Použití

1. Blender **s GUI** na pozadí (socket běží jen s GUI; v `-b` se addon jen zaregistruje):
   ```bash
   MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" ArtSource/Ships/<Loď>/<Loď>_HS_Game.blend
   ```
   (spusť na pozadí, `run_in_background`).
2. Na začátku stav addonu a scény (`get_objects_summary` nebo `get_addon_status()` + `get_scene_info()`).
3. Když MCP nástroje v session nejsou, mluv se socketem přímo skripty v `Tools/Blender/mcp/`
   (spouštěj obyčejným `python`):

| Skript | Co dělá |
| --- | --- |
| `mcp_socket.py`, `lab_socket.py` | poslání kódu na port 9876 / 9877 |
| `mcp_eye_view.py out.png [--headless --displays on\|off --look clay\|material --ship X]` | kamera `EyeCam` v oku podle `SOCKET_Cockpit` z manifestu a FOV/sklonu ze setupu (= kamera kokpitu ve hře), backface culling jako v UE; `--headless` clay render `<Loď>_HS_Game.blend` 1920×1080 bez živého Blenderu |
| `ops_context.py` | operátory s kontextem okna (níže) |

4. Po skončení Blender **zavři** (drží .blend, build receptu pak selže na zápisu).

### Kód v `execute_blender_code`

- Uzly shaderu hledej **podle typu**, ne jména (lokalizace UI):
  `next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")`.
- Enum hodnoty nehardcoduj, čti je z `bl_rna.properties[...].enum_items`.
  `scene.render.engine` přiřazuj v `try/except TypeError`.
- Barvu materiálu nastavuj na vstupech uzlu, `material.diffuse_color` je jen viewport.
- Objekty vytvářej `bpy.data.objects.new(...)` + `collection.objects.link(...)`.

## Operátory – helper `Tools/Blender/mcp/ops_context.py`

Operátory padaly na `poll() failed, context is incorrect` jen kvůli chybějícímu kontextu okna. Helper najde okno,
oblast `VIEW_3D` a její region a operátor spustí v `bpy.context.temp_override(...)`:

```python
import sys; sys.path.insert(0, r"<kořen repozitáře>\Tools\Blender\mcp")
from ops_context import run_op, edit_mode, OpsContextError
run_op("object.join", active=hull, selected=[hull, fin])
run_op("object.modifier_apply", active=ob, selected=[ob], modifier="Bevel")
with edit_mode(panel):
    run_op("mesh.select_all", active=panel, action="SELECT")
    run_op("mesh.bevel", active=panel, offset=0.02, segments=3, profile=0.7, affect="EDGES")
```

- Test `Tools/Blender/mcp/test_ops_context.py` (headless `-b --factory-startup`, přes MCP
  `exec(open("<cesta s />").read())`; `\t` v cestě by byl tabulátor). Ověřeno 24. 9. 2026: join, modifier_apply,
  bevel s profilem, boolean EXACT, inset projdou headless i živě; `knife_project` jen živě.
- **Headless past:** `blender -b` má okno ze startup souboru, ale nikdy se nevykreslí. Operátory promítající
  z pohledu (`knife_project`, `view3d.*`, `transform.*`) pak **tiše nic neudělají**; helper je v `-b` odmítne.
- `knife_project` potřebuje řezací objekt s okrajovými nebo drátovými hranami (plocha, křivka).
- **bmesh zůstává alternativou** pro čistě geometrické operace bez kontextu (`bmesh.ops.bevel`,
  `inset_region`, `bisect_plane`, `create_grid`…). Po vytvoření ploch `normal_update()`, u nových prvků
  `index_update()`.

## Nástrahy (příznak → příčina → řešení)

**Prostředí**
- Cesty v Blenderu nesedí / `//Export` skončí jinde → Git Bash přepisuje cesty →
  `MSYS_NO_PATHCONV=1` (WORKFLOW 9.1 d).
- `uvx`/nástroj z wingetu „neexistuje“ → PATH se projeví až po restartu terminálu → plná cesta (9.1 e).
- Addon po zkopírování nevidět → chybí `bpy.ops.preferences.addon_refresh()` (9.1 f).
- MCP nic nevrací / connection refused → Blender běží v `-b` nebo neběží → spusť s GUI.
- Build receptu selže na zápisu .blend → otevřený GUI Blender ho drží → zavři ho.

**Snímky z živého Blenderu**
- Snímek ukazuje stav před změnou → `get_viewport_screenshot` fotí před překreslením →
  nejdřív `bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP")`.
- `get_viewport_screenshot` chce **absolutní** cestu k souboru.
- Díl ~10 cm je na screenshotu tři pixely → renderuj kamerou do souboru (Workbench,
  `bpy.ops.render.render(write_still=True)`) a soubor si přečti. Nový díl vždy ze tří stran (9.3 x).
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
- Po odebrání hodnoty ze `<Loď>_setup.json` zůstane v Blueprintu stará (9.3 c) – to je strana Unrealu.
- Interiér nesmí mít Nanite (`no_nanite_parts`), sklo/hologramy jako vlastní mesh bez Nanite (9.2 a, 9.3 u).
- Nástrahy displejů staršího AI receptu (rám otočený dvakrát, `corners`, `grow_m`, `cut_depth_m`): `reference.md`
  a WORKFLOW 9.6 a–c.

## Kam dál

- Loď z výkresu: skill `ship-pipeline`; interiér a kit: skill `ship-interior`.
- Úplný seznam nástrah: WORKFLOW kap. 9.
