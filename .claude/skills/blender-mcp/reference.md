# Blender MCP: instalace, obnova a ladění rohů displejů

Referenční část skillu `blender-mcp` (načti jen při obnově instalace nebo při ladění displejů staršího AI receptu).

## Komunitní server `blender` (ahujasid, port 9876)

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

## Oficiální server `blender-lab` (Blender Lab, port 9877)

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

## Ladění rohů displejů v receptu AI lodi (starší cesta, `<Loď>_ai_build.json`)

### Ladění rohů displejů (podrobně WORKFLOW 3.2 bod 3)

Pohled z oka → mřížka, odečti rohy otvoru → `mcp_corners.py` s kandidátem, prohlédni zoom →
opakuj → rohy zapiš do receptu (`interior.displays.screens[].corners`, TL TR BR BL v m (u, v)) →
plný build (build_ai_ship + export + import_ship) → snímky `cockpit` ze zabalené hry.
Nový otvor bez plochy displeje: paprsky z oka přes pixely otvoru, rovina SVD, `u` = (0, −1, 0),
`v` = normála × `u`; flood fill zkosí spodní hranu o knoflíky – oprav ručně podle zoomu.

Pozn.: `mcp_grid`, `mcp_measure_openings` a `mcp_corners` berou jméno lodi jako první argument
(čtou `ArtSource/Ships/<Loď>/<Loď>_ai_build.json` a objekt `SM_Ship_<Loď>_Interior`).

Skripty pro ladění z oka nad AI receptem (čtou `ArtSource/Ships/<Loď>/<Loď>_ai_build.json` a objekt `SM_Ship_<Loď>_Interior`):

| Skript | Co dělá |
| --- | --- |
| `mcp_grid.py <Loď> out.png` | měřicí mřížka na rovině displeje (1 cm žlutá, 5 cm červená, osy zelené) |
| `mcp_measure_openings.py <Loď>` | paprsky z oka: najde otvor v rámečku a vypíše rohy (u, v) |
| `mcp_corners.py <Loď> '<json>' out.png` | posune plochy displejů na zadané rohy a vyfotí pohled z oka |
