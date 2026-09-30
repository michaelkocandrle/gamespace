# Archiv skillu `blender-mcp` (přesunuto 30. 9. 2026)

Doslovně přesunuté výsledky srovnání a testů z `.claude/skills/blender-mcp/SKILL.md` (commit 44c26cc).
Doporučení z nich zůstala ve skillu.

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

## Test operátorů přes `ops_context.py` (24. 9. 2026)

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
