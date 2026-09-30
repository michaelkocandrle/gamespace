# Starší cesta: AI model lodi → recept → .blend

Referenční část skillu `ship-pipeline`. **Od 24. 9. 2026 se exteriér lodi staví přesně z výkresu** (`hs_build_ship`,
skill 3b2); AI image-to-3D nedává přesný hard-surface a slouží jen jako reference stylu. Tento postup platí jen pro
údržbu starších receptů (`<Loď>_ai_build.json`, `build_ai_ship.py`, `fit_ship_interior.py`) a pro AI objem jako
měřítko siluety. Ukázkové cesty (`<Loď>_Meshy.blend`, `nacelle.json`) patřily odstraněnému Vanguardu.

## Generování AI modelu (dříve oddíl 2a)

Generování:
- **Higgsfield** multi-image to 3D (MCP `generate_3d`, model `multi_image_to_3d`, 30 kreditů, fronta ~25 min):
  `medias` = job id schválených pohledů (bok, 3/4, shora, zepředu), `should_texture` + `enable_pbr` true,
  `topology` triangle, `target_polycount` 300000, `symmetry_mode` on, `texture_prompt` s paletou.
  GLB do `ArtSource/Ships/<Loď>/Higgsfield/` a **nikdy needitovat**. Textury pro recept:
  `blender -b --python Tools/Blender/glb_textures.py -- <glb> <out_dir>` (base_color, normal, roughness,
  metallic), v receptu `source_model` (GLB) a `textures`. Wayfarer: nos na −X → `rotate_z_deg` 180.
  Kontrola hned po stažení: `render_ship_views.py` (textury, 6 úhlů) + `silhouette_compare.py` proti maskám výkresu.
- **Meshy**: surový export (FBX + PBR textury) do `ArtSource/Ships/<Loď>/Meshy/<stažení>/`, needitovat.
  Díly skriptem: `python Tools/Assets/meshy_generate.py [--dry-run|--refine|--hi] [--spec X.json --out DIR]`,
  klíč jen z `MESHY_API_KEY`. `--hi` = `geometry_resolution 4k`, ~30k tris (25 kreditů, preview 20).
- **Scenario** (`Tools/Assets/scenario_mcp.py`): Polygen retopologie (`model_tencent-smarttopology`,
  113 CU, ~20 min, progress skáče 10 % → hotovo, sleduj `updatedAt`), UV, dělení na díly, textury.
  Tripo 3.1 na šedém clay renderu selhal; UltraShape je za tarifem Pro.
- Hyper3D Rodin přes Blender MCP: zkušební klíč vyčerpaný (`API_INSUFFICIENT_FUNDS`).

## 3. Recept AI model → .blend (ShipPipeline 2B, WORKFLOW 2.1)

Nic ručně: přestavbu popisuje `ArtSource/Ships/<Loď>/<Loď>_ai_build.json` (první
recept zůstal jen v gitové historii) a `Tools/Blender/build_ai_ship.py` ji z originálu zopakuje (~3 min).
Souřadnice v receptu: metry v Blenderu **po otočení**, +X příď, +Y levý bok, +Z nahoru.

Klíče receptu: `ship`, `source_fbx`, `textures` (base_color, normal, roughness, metallic), `out_blend`,
`orient` (`rotate_z_deg`, `length_m`), `parts` (např. `Gear.regions` – boxy pod úrovní břicha),
`decimate` (cíl + `importance` pravidla, faktor držet ~1), `rebake` (4K BC a N, 2K ORM),
`emissive` (středy trysek y,z, poloměr, x), `canopy_clear`, `canopy_frame`, `lining`,
`collision` (boxy → konvexní `UCX_`, max 26 vrcholů), `sockets`, `interior` (`fit`, `displays`,
`placement`).

```bash
cd /c/gamespace/gamespace
# měření: prázdné parts/collision/sockets a --no-save vypíše rozměry po otočení
MSYS_NO_PATHCONV=1 "$BL" -b --python Tools/Blender/build_ai_ship.py -- ArtSource/Ships/<Loď>/<Loď>_ai_build.json --no-save
MSYS_NO_PATHCONV=1 "$BL" -b --python Tools/Blender/build_ai_ship.py -- ArtSource/Ships/<Loď>/<Loď>_ai_build.json
# čistý lak místo špinavé AI barvy (blok "repaint" v receptu; čte *_BC_AI.png, píše mapy pro hru), ~1 min
MSYS_NO_PATHCONV=1 "$BL" -b ArtSource/Ships/<Loď>/<Loď>_AI.blend --python Tools/Blender/repaint_ship.py -- ArtSource/Ships/<Loď>/<Loď>_ai_build.json
# okluze (R kanál ORM je emisní maska obrazovek, AO má vlastní mapu), ~30 s
MSYS_NO_PATHCONV=1 "$BL" -b ArtSource/Ships/<Loď>/<Loď>_Meshy.blend --python Tools/Blender/bake_ship_ao.py -- <Loď>
```
AO se v setupu přidá jako `"ao"` mezi textury (`cavity_strength`, `ao_strength`, maska `wear_amount`).

**Kvalita povrchu AI lodi (Wayfarer 1.1, autor: „vypadá rozbitě a špinavě“):**
- `"weld_m": 0.0005` v receptu: AI mesh bývá polévka rozpojených trojúhelníků. Bez svaření vznikne ostrůvek na
  každý trojúhelník a atlas využije 0,4 % textury. Build vypisuje `UV atlas uses N %`; **cíl ≥ 40 %**.
- Unwrap: `smart_project` s nulovým marginem a pak `pack_islands` ADD `uv_margin` (0,0005).
- Barva: AI textura se nepoužívá přímo. `repaint_ship.py` dělá zóny laku podle bloku `repaint` (`zones` s barvou
  sRGB, roughness a metallic; `glass_boxes`, `engine_boxes`, `accent_exclude_boxes`, `speck_area_m2`,
  `detail_strength` 0,3). Rebake píše `T_Ship_<Loď>_BC_AI/ORM_AI`, repaint `T_Ship_<Loď>_BC/ORM`.
- Materiál s vymodelovanými panely: `panel_strength` 0, `wear_amount` ≤ 0,05, `detail_rough_variation` ~0,04.
- Kontrola: `render_ship_views.py --swap T_Ship_<Loď>_BC_AI.png=<nová BC>` a snímky `ship_views` ze hry, vždy
  zblízka (`10_close_three_quarter`).

Pravidla čísel:
- Délka: malá stíhačka 12–16 m, Steadfast 30 m. AI modely chodí 1–2 m
  a s náhodnou orientací (Meshy: příď −X).
- Trup s Nanite může mít ~1 mil. tris (Nanite si vybere; cena = velikost FBX a čas pečení).
- 4K na 14m loď ≈ 3 mm/px → detail zblízka dělá **detailní vrstva materiálu** `M_Ship_PBR`
  (`detail_*` v setupu, `Tools/Assets/generate_detail_textures.py`), ne větší textura.
- Kolize: trup rozděl, kde se zužuje; každý motor, kabina a noha podvozku zvlášť.
- Díry v trupu po vyříznutí podvozku se zacelí samy; pahýly nad řezem zůstávají jako úchyty. U AI meshe
  s otevřenými hranami (Wayfarer) zacelování natáhlo obří plochy přes křídla a trvalo 10 min → u dílu
  `"fill_holes": false`.
- Visící díly (pootevřená rampa) oddělit jako vlastní díl (`parts.Ramp`), jinak test podvozku vidí trup pod břichem.
- Patky na spodku kolizního boxu: kolizní region kolem noh až k patkám (vrcholy dílu Gear se počítají) →
  `gear_extension_cm` 0.
- Kolize: k-DOP bere extrémy ≥ 10 cm od sebe a při selhání kontroly konvexnosti zahodí konec nejkratší hrany
  (sliver plošky s nepřesnou normálou).

Kontrola po buildu: `MSYS_NO_PATHCONV=1 "$BL" -b <Loď>_AI.blend --python Tools/Blender/render_ship_views.py -- --out DIR`
(EEVEE, 6 úhlů, UCX skryté) a porovnej s originálem ze stejných úhlů (kabina zblízka, spodek, 3/4) –
render přes kameru do souboru, ne `get_viewport_screenshot` (fotí před překreslením; vynuť
`bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP")`). Fleky na kovu = normály/UV; rozmazané = malé textury.

Kokpit a interiér (2B kroky 6 a 10):
- `Tools/Blender/cockpit_view_survey.py -- X Y Z FOV` (UE cm) nebo `sweep:X0:X1:Z0:Z1`; počítá s tím,
  že UE nekreslí odvrácené stěny.
- `Tools/Blender/fit_ship_interior.py -- <recept>` na hotovém `<Loď>_Meshy.blend` vypíše usazení a oko →
  `interior.placement`, `sockets.Cockpit`, oko do setupu (`components.cockpit_camera.relative_location`,
  cm, **Y s opačným znaménkem**), postav znovu.
- Rámování oka: `fit.dash_below_eye_deg` [7, 13], displeje ~15–24° pod okem, první stíhačka
  měla `eye_behind_stick_m` 0,65. Oko navržené pro 16:9 a FOV 88°.
- Displeje (`interior.displays.screens[]`): `centre`, `u`, `v`, `corners` TL/TR/BR/BL (otvory nejsou
  obdélníky), `texture_rect` = `USpaceCockpitDisplays::ScreenRect` (plátno `texture_size` [1330, 490]),
  `grow_m` 0,0045, `cut_depth_m` (malé 6 mm). Slot `M_Ship_<Loď>_Screens`, socket `Display_<jméno>`.
  Podrobně WORKFLOW 2.1; hlídá `test_cockpit_displays.py`.

## 3c. Exteriér hard-surface (AssetPipeline_Modular „Exteriér: hard-surface“)

- AI trup je jen **objemová reference**. Loď se staví po dílech z JSON receptů v
  `ArtSource/Ships/<Loď>/HardSurface/`.
- **Rotační díly** staví `Tools/Blender/hs_build_part.py`:
  - panely se skutečnými spárami, prstence, sání a tryska;
  - bevel s harden normals a weighted normals;
  - kit `HS_Kit` a GN `HS_KitInstancer`.
  ```bash
  MSYS_NO_PATHCONV=1 "$B" -b --factory-startup --python Tools/Blender/hs_build_part.py -- ArtSource/Ships/<Loď>/HardSurface/nacelle.json
  MSYS_NO_PATHCONV=1 "$B" -b ArtSource/Ships/<Loď>/HardSurface/<Loď>_Nacelle_HS.blend --python Tools/Blender/hs_render_views.py -- --collection HS_<Loď>_Nacelle_UL --out Saved/HardSurface/hs --prefix hs
  ```
- **Smyčka:**
  1. změř osu a profil z masek AI objemu;
  2. uprav recept;
  3. build;
  4. `silhouette_compare`;
  5. `hs_render_views` a list vedle sebe s Meshy výřezem;
  6. prohlédni detail zblízka.
- **Pilot gondoly:** IoU 0,854 → 0,894 jen úpravou osy a poloměrů v receptu.
  - Otevřené: ohnout velké díly kitu podle povrchu, pylon, UV a materiály, import do UE.
  - Celou loď nepřestavovat bez rozhodnutí autora.
