---
name: ship-pipeline
description: How a ship goes from idea to Unreal in gamespace - the mandatory 2D design stage (ArtSource/Ships/<Ship>/Design, <Ship>_layout.json, draw_ship_design.py, <Ship>_spec.json in RSI Ship Matrix shape, author approval), concept views for Higgsfield/Meshy, the AI-model recipe (<Ship>_ai_build.json, build_ai_ship.py), Blender export (gamespace_ship_export.py, manifest) and Unreal import (import_ship.py, <Ship>_setup.json). Load when designing a new ship, generating or processing a ship model, touching sockets/UCX collision/pivot/LODs/ship materials/naming, or running the ship export/import scripts.
---

# Loď: od nápadu do Unrealu

Podrobný zdroj: `Docs/Ships/ShipPipeline.md` (kap. 0–5, hlavně 2A a 2B), `Docs/WORKFLOW.md` kap. 2
a nástrahy 9.6, `Docs/AssetPipeline_Modular.md` (kdy generovat vcelku, kdy po dílech).
Vzor 2D návrhu: `ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`.
Autor není herní vývojář: **všechno skriptem / receptem**, nic ručním klikáním v Blenderu ani editoru.
Kapitoly C–D, G–I v ShipPipeline popisují ruční kliky v Blenderu; dnes je dělá recept (2B).

Blender z Git Bash vždy s `MSYS_NO_PATHCONV=1` (jinak se `//Export` přepíše na `/Export`):
```bash
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
MSYS_NO_PATHCONV=1 "$BL" -b ...
```
UE skripty a testy spouštěj **nástrojem PowerShell** (`.\Tools\run_editor_python.ps1 ...`), přes bash se
rozbije `$PSScriptRoot`.

## 0. Pořadí fází (nepřeskakovat)

1. **2D návrh** → schválení autorem. **Dokud autor neschválí, nic se nestaví ve 3D.**
2. Koncept (pohledy) → AI model (Meshy / Higgsfield) nebo kitbash/stažený model.
3. Recept `<Loď>_ai_build.json` → `build_ai_ship.py` → `<Loď>_Meshy.blend`.
4. `gamespace_ship_export.py` → FBX + `<Loď>_manifest.json`.
5. `import_ship.py` + `<Loď>_setup.json` → `BP_Ship_<Loď>`; pak `build_main_menu.py`.
6. Testy + `Tools\Shots.ps1` (snímky si sám prohlédni).

## 1. 2D návrh (povinný první krok každé lodi)

Adresář `ArtSource/Ships/<Loď>/Design/`:

| Soubor | Co |
| --- | --- |
| `<Loď>_layout.json` | **jediný zdroj pravdy**: `decks` (floor_z, clear_height, outline), `rooms` (id, deck, name, rect, purpose), `objects` (room, name, rect, purpose), `doors` (deck, at, axis, width, name). Metry, x dopředu od zádě, y na levobok. |
| `<Loď>_Design.md` | vize, parametry, uspořádání, pohyb posádky, designový jazyk, **otevřené otázky pro autora**; stav „čeká na schválení“ |
| `<Loď>_deck_upper.png`, `_deck_lower.png`, `_cutaway.png` | výkresy v měřítku, generované – nikdy ručně |

Specifikace je **o úroveň výš**: `ArtSource/Ships/<Loď>/<Loď>_spec.json` ve tvaru RSI Ship Matrix
(`identity`, `dimensions`, `crew`, `flight`, `components`, `weapons`, `_status`). Kód ho nečte; není to
totéž co `<Loď>_setup.json` (build config). Existují: `Steadfast_spec.json`, `Delver_spec.json`,
`Farsight_spec.json`.

Výkresy:
```bash
python Tools/Design/draw_ship_design.py ArtSource/Ships/Steadfast/Design/Steadfast_layout.json
```
(Pillow, písmo Bahnschrift, 62 px/m; místnosti tónované podle zóny command/crew/service/cargo/engineering,
objekty očíslované s legendou účelu.) Nové typy místností přidej do `ROOM_ZONE` ve skriptu.

Pravidla návrhu (autor 24. 9. 2026):
- Každá místnost a **každý objekt má účel** (`purpose`). Žádné vatové propy (bedny, sudy „pro detail“),
  **klávesnice u dveří = no-go**, žádné krabicové procedurální pulty.
- Vzor anotovaných řezů a půdorysů: `Docs/UI/reference_tvorba_lodi/*.jpg`.
- Styl SC, ale vlastní („vibe, ne kopie“), nestylizovat podle jednoho dvou obrázků. Teplá architektura,
  studené UI jen tam, kde se pracuje. Paleta: gunmetal `0.35, 0.42, 0.55` (se studeným světlem 7000 K),
  oranžová `0.85, 0.34, 0.06` (AssetPipeline_Modular, sekce Paleta).
- V lodích je hráč v první osobě → interiér navrhuj na průchod (okruh palub, žádné slepé uličky
  dvakrát, nástup ze země i ze stanice).
- Ship Matrix pole: délka/šířka/výška, hmotnost, SCU, posádka a stanoviště, SCM/AB, pitch/yaw/roll,
  zrychlení po osách, komponenty (avionika, pohon, moduly), zbraně/utility.

## 2. Koncept → AI model (ShipPipeline 2A, 2B; AssetPipeline_Modular)

Kdy co:
- **Exteriér lodi** (jedna dominantní silueta) → generovat vcelku: hero obrázek → multi-view → Meshy
  (nebo Higgsfield multi-image to 3D).
- **Interiér / komplexní kompozice** (kokpit, pulty, přístroje) → **nikdy jedním promptem**. AI jen hrubá
  obálka; funkční detail (tlačítka, přepínače, rámy displejů, panely) **procedurálně v Blenderu** (bmesh);
  sesadit přes Blender MCP (WORKFLOW kap. 3).
- Třetí rovnocenná cesta: stažený model s komerční licencí (Quaternius CC0 první; Sketchfab CC-BY →
  autor do `Docs/Credits.md`). **Licenci zkontroluj před stažením**; „personal/non-commercial/editorial“ ne.
- AI je dobrá na panelové díly, selhává na tenkých protáhlých (kabely, trubky, madla) → procedurálně.

Koncept pro AI (2A): **2–4 konzistentní pohledy téže lodi: bok, zepředu, shora, 3/4.** Neutrální
pozadí, rovnoměrné světlo, bez motion bluru a dramatických stínů, celá loď v záběru. Z jednoho obrázku si
AI záda a spodek vymyslí. Postup a ověření viz 2a.

## 2a. Konzistentní pohledy přes Higgsfield MCP (ověřeno 24. 9. 2026)

Test na procedurálním modelu první stíhačky (17,58 × 12,96 × 4,36 m), aby šel každý pohled změřit proti
skutečnému modelu. Testovací soubory, prompty a listy rozdílů byly smazány spolu s lodí (24. 9. 2026);
historie je v gitu, commit `2919d8a`. Naměřené výsledky platí dál:

| Varianta (IoU proti modelu) | bok | zepředu | shora | uzávěr | rozpětí/výška proti spec |
| --- | --- | --- | --- | --- | --- |
| GPT Image 2.5, jen hero obrázek | 0,79 | 0,29 | 0,65 | 24 % | −37 % / +4 % |
| GPT Image 2.5, list 2 × 2 v jednom obrázku | 0,22 | 0,56 | 0,58 | 138 % | nepoužitelné |
| Nano Banana Pro, jen hero (zepředu po `remove_background`) | 0,82 | 0,73 | 0,76 | 15 % | −4 % / +9 % |
| GPT Image 2.5 + vodicí silueta | 0,89 | 0,54 | 0,92 | 17 % | −3 % / +5 % |
| **Nano Banana Pro + vodicí silueta** | **0,97** | **0,90** | **0,98** | **0,3 %** | **0,1 % / 0,4 %** |

Co z toho plyne:
- **Bez vodítka si model domyslí půdorys** (GPT udělal křídla dopředu šípová a o třetinu kratší) a „zepředu“
  kreslí seshora šikmo. Hezký obrázek neznamená správný tvar – vždy měř.
- **List všech pohledů v jednom obrázku nepoužívej**: pohledy mají každý jiné měřítko, přetékají přes
  buňky a půdorys neodpovídá boku.
- **Vodicí silueta jako druhá reference** („The second image is the exact orthographic … silhouette of this
  ship … must match exactly“) je hlavní páka. **Výchozí volba: Nano Banana Pro + vodítko** – siluetu
  drží téměř přesně a přitom kreslí skutečný povrch a barvy z hero obrázku. U nové lodi vodítko vzniká
  z našeho 2D návrhu (obrys paluby z `<Loď>_layout.json`, profil z řezu), ne z AI.
- Pohled **zepředu je nejslabší** (tenká křídla = malý posun rozhodí IoU). Nano Banana v něm nakreslil
  navíc dvě plovoucí špičky ploutví nad lodí – měření je jako odtržené skvrny zahodí, ale obrázek
  do multi-image to 3D takhle nesmí → přegenerovat, nebo poslat jen bok + shora + 3/4.
  **Každý pohled si před použitím prohlédni** (Read na PNG), číslo nestačí.
- Modely někdy kreslí podlahu a stín i přes „no floor“ → před měřením `remove_background` (Higgsfield,
  výstup s alfou, `extract_reference_mask` alfu použije).

Postup pro novou loď (vše přes MCP a skripty, nic ručně):
1. Hero obrázek (3/4) schválený autorem → `mcp__higgsfield__media_upload` + `curl -X PUT` + `media_confirm`.
2. Vodítka: `python Tools/Blender/silhouette_compare.py guide --mask side=<profil.png> --mask top=<půdorys.png>
   --mask front=<čelo.png> --out ArtSource/Ships/<Loď>/Concept/guides` (tmavá silueta na světle šedé, 16:9;
   z hotového modelu `--model <render prefix>`). Nahrát stejně jako hero.
3. `generate_image_batch`, model `nano_banana_pro` (`resolution: 2k`, `aspect_ratio: 16:9`, 2 kredity;
   v odpovědi se hlásí jako `nano_banana_2`), `medias`: hero + vodítko, obojí role `image_references`.
   Do promptu „no floor, no shadow“. Záloha `gpt_image_2_5` (`quality: high`, 2,75 kreditu).
   Fronta bývá 5–15 min → `jobs_wait` opakovaně.
4. Stáhnout `result_url` curlem do `ArtSource/Ships/<Loď>/Concept/` (surové, needitovat), prompt
   a nastavení do `prompt.txt`.
5. Kontrola konzistence (bez modelu):
   ```bash
   python Tools/Blender/silhouette_compare.py views --ref front=f.png --ref side=s.png --ref top=t.png \
       --dims <délka,šířka,výška ze spec> --out Saved/Concept/<Loď>
   ```
   Každý pohled ukazuje dva ze tří rozměrů, takže bok + shora předpovídají poměr stran zepředu
   (`closure_error_pct`); dál symetrie zepředu a shora a odchylka od rozměrů ze `_spec.json`.
   **Přijmout:** rozměry proti spec ≤ 5 %, symetrie ≥ 0,9, uzávěr ≤ 10 % (vyšší = jeden pohled má jinou
   výšku, obvykle zepředu → přegenerovat ten). Masky si prohlédni (`views_masks.png`).
6. Teprve pak multi-image to 3D (níže).

Generování:
- **Higgsfield** multi-image to 3D: Topology triangle, 200–300 tis. tris, **PBR maps zapnout** (jinak
  zapečené světlo), rigging ne. GLB do `ArtSource/Ships/<Loď>/Higgsfield/` a **nikdy needitovat**.
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
# okluze (R kanál ORM je emisní maska obrazovek, AO má vlastní mapu), ~30 s
MSYS_NO_PATHCONV=1 "$BL" -b ArtSource/Ships/<Loď>/<Loď>_Meshy.blend --python Tools/Blender/bake_ship_ao.py -- <Loď>
```
AO se v setupu přidá jako `"ao"` mezi textury (`cavity_strength`, `ao_strength`, maska `wear_amount`).

Pravidla čísel:
- Délka: malá stíhačka 12–16 m, Steadfast 30 m. AI modely chodí 1–2 m
  a s náhodnou orientací (Meshy: příď −X).
- Trup s Nanite může mít ~1 mil. tris (Nanite si vybere; cena = velikost FBX a čas pečení).
- 4K na 14m loď ≈ 3 mm/px → detail zblízka dělá **detailní vrstva materiálu** `M_Ship_PBR`
  (`detail_*` v setupu, `Tools/Assets/generate_detail_textures.py`), ne větší textura.
- Kolize: trup rozděl, kde se zužuje; každý motor, kabina a noha podvozku zvlášť.
- Díry v trupu po vyříznutí podvozku se zacelí samy; pahýly nad řezem zůstávají jako úchyty.

Kontrola po buildu: porovnej v Blenderu s originálem ze stejných úhlů (kabina zblízka, spodek, 3/4) –
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

## 3b. Měřitelná shoda siluety (`Tools/Blender/silhouette_compare.py`)

Při modelování optimalizuj **číslo**, ne dojem z obrázku.

```bash
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
# 1) masky modelu (Workbench, ortho, headless); --collection / --objects, volitelně výřez
MSYS_NO_PATHCONV=1 "$B" -b Ship.blend --python Tools/Blender/silhouette_compare.py -- render \
    --collection HS_<Loď>_Nacelle_UL --out Saved/Silhouette/nacelle --prefix hs
# reference jako výřez AI modelu (box + válec kolem osy, bez pylonu)
MSYS_NO_PATHCONV=1 "$B" -b ArtSource/Ships/<Loď>/<Loď>_Meshy.blend --python Tools/Blender/silhouette_compare.py -- render \
    --objects SM_Ship_<Loď> --crop-box=-6.8,3.0,0.4,0.35,6.0,3.4 --crop-cylinder=4.551,1.892,1.24 \
    --out Saved/Silhouette/nacelle --prefix meshy
# 2) porovnání: render proti renderu (světové souřadnice) nebo proti konceptům (bbox)
python Tools/Blender/silhouette_compare.py compare --model Saved/Silhouette/nacelle/hs --ref-model Saved/Silhouette/nacelle/meshy --out Saved/Silhouette/nacelle
python Tools/Blender/silhouette_compare.py compare --model DIR/model --ref front=Concept/front.png --ref side=Concept/side.png --ref top=Concept/top.png --out DIR
# 3) všechno najednou
python Tools/Blender/silhouette_compare.py run --blend Ship.blend --collection X --ref side=... --out DIR
```

- **Pohledy:**
  - front = na nos z +X, levobok vpravo;
  - side = ze pravoboku (−Y), nos vpravo;
  - top = shora, nos vpravo.
  - Koncept otočený opačně se porovná zrcadlově (`mirrored`).
- **Výstup:** `silhouette.json` (IoU, poměr stran bboxu modelu/reference, `extra_pct` / `missing_pct`
  po pohledech, `mean_iou`), dále `diff_<pohled>.png` a `diff_sheet.png`. Šedá = obojí, červená =
  model má navíc, tyrkys = modelu chybí.
- **Koncept:** silueta se vyřízne z neutrálního pozadí (medián okraje, práh `--threshold` 30) nebo
  z alfy. Otvory se vyplní, skvrny se odstraní rekonstrukcí, takže tenké špičky zůstanou.
- **Render proti renderu** se porovnává ve světových souřadnicích (`--align world`). Normalizace
  podle bboxu by kvůli jedné zbloudilé části posunula celou masku (WORKFLOW 9.6 g).
- **`views`** (konzistence konceptů mezi sebou, bez modelu) a **`guide`** (vodicí siluety pro obrázkový
  model) popisuje sekce 2a. Koncepty nad 1400 px se před vyříznutím zmenší; odtržené skvrny pod 2 %
  největšího kusu se zahodí.
- **Test:** `python Tools/Blender/tests/test_silhouette_compare.py`, 20 kontrol včetně renderu
  krychle v Blenderu.
- **Cíle:** hard-surface díl proti AI objemu ≥ 0,88 na pohled. Nižší číslo znamená špatnou osu nebo
  poloměr, ne detail. Proti konceptu je cíl ≥ 0,9 a `aspect_model` do 3 % od `aspect_ref`.

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

## 4. Pojmenování a sockety (ShipPipeline kap. 1)

| Co | Vzor |
| --- | --- |
| Hlavní mesh / díl | `SM_Ship_<Loď>`, `SM_Ship_<Loď>_<Díl>` (`_Gear`, `_Interior`, `_Lining`, `_Canopy`) |
| LOD (jen bez Nanite) | `SM_Ship_<Loď>[_<Díl>]_LOD<n>`, každý LOD vlastní FBX |
| Kolize | `UCX_<mesh>_NN` (konvexní), `UBX_`/`USP_`/`UCP_` |
| Socket | `SOCKET_<Jméno>` (Empty, rodič = mesh; import prefix zahodí, kód bere oba tvary) |
| Materiálový slot (Blender) | `M_Ship_<Loď>_<Slot>` → v UE `MI_Ship_<Loď>_<Slot>` |
| Textury UE | `T_Ship_<Loď>_<Slot>_BC/_N/_ORM/_E/_M/_AO` |
| Reference v .blend | `HIGH_*` (export ignoruje) |
| Blueprint | `BP_Ship_<Loď>` (potomek `ASpaceshipPawn`) |

Jméno lodi: jedno slovo s velkým písmenem, bez mezer a podtržítek. Blenderové `.001` = chyba exportu.

Sockety, se kterými počítá kód:
- `Cockpit` (X dopředu; skutečné oko ale bere `<Loď>_setup.json` → `cockpit_camera.relative_location`).
- `Engine_L/R/…` nebo `EngineMain`: osa X **dozadu ven z trysky** (v receptu `rotate_z_deg: 180`).
- `CameraTarget` (volitelně), `Exit` (mimo UCX s rezervou na kapsli postavy r 42 cm, výška 1,92 m;
  ideálně ~80 cm), `Gear_Nose/L/R` (`bottom_of` dílu podvozku = spodek patky), `Display_<jméno>`.

Adresáře: zdroje `ArtSource/Ships/<Loď>/` (Concept, Higgsfield, Meshy, Textures, Export, Design,
Interior, Kitbash; `.blend/.glb/.fbx/.png` přes Git LFS, `*.blend1` ignorované), Unreal
`Content/Ships/<Loď>/{Meshes,Materials,Textures,Blueprints,VFX,Audio}`, sdílené
`Content/Ships/Shared/Materials`.

## 5. Export z Blenderu (ShipPipeline K, L1)

```bash
cd /c/gamespace/gamespace/ArtSource/Ships/<Loď>
MSYS_NO_PATHCONV=1 "$BL" -b <Loď>_Meshy.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export" --validate-only
MSYS_NO_PATHCONV=1 "$BL" -b <Loď>_Meshy.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"
# bez Blenderu i Unrealu:
python Tools/Blender/gamespace_ship_export.py --check-manifest ArtSource/Ships/<Loď>/Export/<Loď>_manifest.json
python Tools/Assets/import_ship.py ArtSource/Ships/<Loď>/Export/<Loď>_manifest.json   # jen vypíše plán
```
- Validace: ERROR musí být 0. Hlídá jednotky, jména, aplikované transformace, zrcadlení, tris, UV,
  sloty, non-manifold, konvexnost/vrcholy UCX (≤ 32), LODy, rodiče socketů, nos +X, měřítko 4–80 m,
  pivot, UCX vyčnívající > 5 % délky.
- Pivot = **střed obálky kolizí** v počátku (Center on collision); loď se otáčí kolem počátku a root box
  pawnu je v něm vycentrovaný.
- Exportní nastavení je napevno ve skriptu (Face smoothing, Triangulate, Forward −Z, Up Y, …).
- Staré FBX dílů, které nový model nemá, smaž z `Export/`.
- Hodnoty pawnu z geometrie počítá jen `suggest_pawn_settings()` v exportéru → manifest
  `suggested_pawn_settings` → import. Nepřepočítávat ručně.

## 6. Import do Unrealu (ShipPipeline L2–L3, WORKFLOW 2.2)

```powershell
$env:GAMESPACE_SHIP_MANIFEST = "C:\gamespace\gamespace\ArtSource\Ships\<Loď>\Export\<Loď>_manifest.json"
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py
.\Tools\run_editor_python.ps1 Tools\Assets\build_main_menu.py
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py   # uklidí, co držela úvodní obrazovka
```
Proměnné: `GAMESPACE_SHIP_DRY_RUN=1`, `GAMESPACE_SHIP_APPLY_PLANET=0`, `GAMESPACE_SHIP_SET_GAME_MODE=0`.
Import: kontrola manifestu → FBX (Nanite kromě skla a `no_nanite_parts`) → ověří velikost, osy, hully,
sloty, sockety (měřítko 100 → 1) → `BP_Ship_<Loď>` → `<Loď>_import_report.json`. Při změně slotů smaže
starý mesh a importuje načisto, uklidí osiřelé assety.

`ArtSource/Ships/<Loď>/<Loď>_setup.json` (vyhrává nad manifestem, klíče `_*` = poznámky):
- `materials`: instance → `master` z `hull` | `pbr` | `glass` | `screen` | `decal`
  (`Tools/Assets/ship_materials.py`: `M_Ship_Hull`, `M_Ship_PBR`, `M_Ship_Glass`, `M_Ship_Screen`,
  `M_Ship_Decal`), `slots`, volitelně `meshes`, `textures`, barvy/roughness/emise/opacity, `detail_*`.
  **Každý slot musí mít materiál** (hlídá `test_import_ship_plan.py`).
- `pawn` (snake_case vlastnosti `ASpaceshipPawn`), `components` (`camera_boom.target_arm_length`, …,
  vektory `[x, y, z]`), `no_nanite_parts` (např. `["Interior"]`), `decals`.
- Geometrie → přepočítat jen kameru, oko, `gear_stow_travel_cm` (nejdelší noha pod břichem),
  `gear_extension_cm` 0 když patky leží na spodku kolizního boxu. Letové hodnoty nesahat.
- Chase kamera: manifest navrhuje ~1,8 × délka, v praxi ~0,8 × délka (SocketOffset.Z ~300–400).

Textury v UE: `_BC` sRGB on; `_N` Normalmap + **Flip Green on** (Blender/glTF = OpenGL); `_ORM` a `_AO`
Masks, sRGB off. Rozměry mocnina dvou, trup 4096², malé díly 1–2K.

## 7. Testy a snímky

```powershell
.\Tools\run_editor_python.ps1 Tools\Tests\test_ship_import.py
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_displays.py
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_frame.py
.\Tools\Shots.ps1 -Preset ship_views -Package
.\Tools\Shots.ps1 -Preset cockpit
.\Tools\Shots.ps1 -Preset landing
```
Mimo UE: `python Tools/Assets/tests/test_import_ship_plan.py`, `python Tools/Blender/tests/test_ship_export_core.py`.
Když autor najde vizuální chybu, přidej do testu kontrolu, která by ji chytila.

## 8. Checklist modelu

- [ ] 2D návrh schválený autorem; spec v Ship Matrix tvaru
- [ ] Reálná velikost, Unit Scale 1.0, nos +X, vršek +Z, transformace aplikované, bez záporného měřítka
- [ ] Pivot = střed obálky UCX; spodek root boxu = nejnižší bod, na kterém loď stojí
- [ ] Sklo samostatný díl bez Nanite; interiér bez Nanite
- [ ] Jedna UV mapa bez překryvů, žádný prázdný slot, textury bez zapečeného světla
- [ ] 3–8 konvexních UCX (≤ 32 vrcholů), nevyčnívají, pod křídly volno pro chůzi postavy
- [ ] Sockety Cockpit / Engine_* / Exit / Gear_* se správnými osami
- [ ] Validate 0 ERROR, manifest check OK, testy zelené, snímky prohlédnuté

## 9. Nástrahy (příznak → příčina → oprava)

- Loď v UE stokrát menší → FBX bez převodu jednotek → import zkusí Convert Scene Unit; ověř Approx Size
  = `expected_ue_size_cm`.
- `//Export` zapsáno do `/Export` → Git Bash přepis cest → `MSYS_NO_PATHCONV=1`.
- Fleky / trojúhelníky přes půl textury po decimaci → AI UV atlas z tisíců ostrůvků → nové UV + rebake
  (recept to dělá), normála zapečená z originálu.
- Zevnitř kabiny je vidět skrz loď → trup je jednostranný → `lining`, `canopy_clear`, oko těsně nad
  předním okrajem kabiny (WORKFLOW 9.6 c).
- Rám displeje otočený dvakrát → rotace v placement matici i v `u`/`v` → `add_displays` bez rotace (9.6 a).
- Světlý proužek AI skla kolem displeje → řez přesně na obrysu → `grow_m` 0,0045.
- Kokpit/displeje se při rychlém pohybu rozmazávají → Nanite + TSR na meshi u kamery → `no_nanite_parts`
  (WORKFLOW 9.2 a).
- Hodnota odebraná ze `_setup.json` v BP zůstává → Blueprint override → nastav ji explicitně (9.3 c).
- Podvozek/ploutve zajíždějí do terénu → vizuál pod spodkem root boxu → spodek boxu = patky.
- Loď se při otáčení „kývá“ → pivot mimo střed boxu → Center on collision / recept.
- Chase kamera se lepí do vlastní lodi → boom sweepuje kanálem Camera a mesh ho blokuje → kolizní
  nastavení `Hull` neměnit bez kontroly boomu (ShipPipeline 5, „Další pasti“). Root `HullCollision`
  (box přes celou loď) ignoruje pawny; postava naráží do UCX hullů meshe.
- `bpy.ops.object.join` přes MCP: `poll() failed` → chybí kontext viewportu → bmesh / `bpy.data`
  (nebo helper s `temp_override`, pokud už existuje v `Tools/Blender/mcp/`).
- AI kusy technických prvků vypadají „organicky“ → AI nemá strojovou přesnost → procedurálně.
- Licence AI výstupů (Higgsfield, Meshy, Tripo) a stažených modelů ověř před vydáním hry.
