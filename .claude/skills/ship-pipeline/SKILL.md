---
name: ship-pipeline
description: How a ship goes from idea to Unreal in gamespace - Ship Matrix reference set (fetch_ship_matrix.py), the mandatory 2D design stage (ArtSource/Ships/<Ship>/Design, <Ship>_layout.json with exterior outlines, draw_ship_design.py, <Ship>_spec.json in RSI Ship Matrix shape, author approval), the design dossier and fleet Ship Matrix page (build_ship_matrix.py, published as an Artifact), concept views for Higgsfield/Meshy, the AI-model recipe (<Ship>_ai_build.json, build_ai_ship.py), Blender export (gamespace_ship_export.py, manifest) and Unreal import (import_ship.py, <Ship>_setup.json). Load when designing a new ship, generating or processing a ship model, touching sockets/UCX collision/pivot/LODs/ship materials/naming, or running the ship export/import scripts.
---

# Loď: od nápadu do Unrealu

Podrobný zdroj: `Docs/Ships/ShipPipeline.md` (kap. 0–5, hlavně 2A a 2B), `Docs/WORKFLOW.md` kap. 2
a nástrahy 9.6, `Docs/AssetPipeline_Modular.md` (kdy generovat vcelku, kdy po dílech).
Vzor celého návrhu (reference, spec, layout s exteriérem, koncepty, dossier): **`ArtSource/Ships/Wayfarer/`**
(schválen 24. 9. 2026). Starší vzor jen interiéru: `ArtSource/Ships/Steadfast/Design/`.
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

1. **Reference ze Ship Matrix** (1a) → **spec** → **2D návrh** (layout, výkresy, kontrola siluet) →
   **koncepty** (2a) → **dossier + Ship Matrix** (1b) → schválení autorem.
   **Dokud autor neschválí, nic se nestaví ve 3D.**
2. AI model (Meshy / Higgsfield) nebo kitbash/stažený model; silueta modelu se měří proti maskám z výkresu.
3. Recept `<Loď>_ai_build.json` → `build_ai_ship.py` → `<Loď>_Meshy.blend`.
4. `gamespace_ship_export.py` → FBX + `<Loď>_manifest.json`.
5. `import_ship.py` + `<Loď>_setup.json` → `BP_Ship_<Loď>`; pak `build_main_menu.py`.
6. Testy + `Tools\Shots.ps1` (snímky si sám prohlédni).

## 1a. Reference ze Ship Matrix (první krok každé lodi)

Autor chce každou loď „naplno inspirovanou“ referencemi z RSI Ship Matrix (24. 9. 2026).

```bash
python Tools/Design/fetch_ship_matrix.py --class small_multirole \
    --ships "Avenger Titan" "Mustang Alpha" "Aurora Mk I MR" 100i Cutter "C8X Pisces Expedition" Nomad Syulen
```
- Stáhne celou matici (`https://robertsspaceindustries.com/ship-matrix/index`, 255 lodí, s komponentami)
  do `starcitizenreference/ship_matrix/ship_matrix_index.json`. `--offline` použije uloženou.
- Pro třídu zapíše `<class>.md` a `<class>.json` (tabulka, medián, komponenty) a `<class>/<loď>.jpg`.
- Jména musí přesně sedět; při překlepu skript vypíše podobná.
- Vyber 6–10 lodí `flight-ready` té role; spec nové lodi má `_reference` (set, ships, median) a každou
  odchylku od mediánu vysvětli v `<Loď>_Design.md`.
- **Obrázky CIG jen ke studiu: nikdy do Higgsfieldu, Meshy ani Scenaria, nikdy do hry.**
- Jméno lodi zkontroluj proti jménům v matici (žádná shoda s lodí SC).

## 1. 2D návrh (povinný každé lodi)

Adresář `ArtSource/Ships/<Loď>/Design/`:

| Soubor | Co |
| --- | --- |
| `<Loď>_layout.json` | **jediný zdroj pravdy**: `decks` (floor_z, clear_height, outline), `rooms` (id, deck, name, rect, purpose), `objects` (room, name, rect, purpose), `doors` (deck, at, axis, width, name). Metry, x dopředu od zádě, y na levobok. |
| `<Loď>_Design.md` | vize, parametry, uspořádání, pohyb posádky, designový jazyk, **otevřené otázky pro autora**; stav „čeká na schválení“ |
| `<Loď>_deck_upper.png`, `_deck_lower.png`, `_cutaway.png` | výkresy v měřítku, generované – nikdy ručně |
| `<Loď>_exterior.png`, `guides/<Loď>_mask_*.png` | jen s blokem `exterior` v layoutu: exteriér ve třech pohledech s kótami a masky siluet (vodítka pro AI, měřítko pro 3D) |

**Obecný formát layoutu (vzor `Wayfarer_layout.json`):** `ship`, `sheet` (`subtitle`, `plan_extent`,
`cutaway_extent`, `ground_z`), libovolné `decks` (`title`), místnost má `zone`
(command/crew/service/cargo/engineering) a volitelně `floor_z`, objekt volitelně `z` [od, do] (kreslí se
do řezu) a `below: true` (pod podlahou, čárkovaně). `exterior`: `side` (x, z; ze pravoboku), `top` (x, y;
levobok nahoře), `front` (y, z; levobok vpravo) = seznam dílů `{name, kind, poly | circle, mirror, label,
label_at}` kreslených v pořadí; `kind` hull | wing | engine | fin | glass | gear | weapon | nozzle.
`cutaway`: `lines` (rampa, schod) a `labels`. Kreslí `Tools/Design/ship_sheets.py`, rozměry vypíše
řádek `SHIP_SHEETS` a **musí se rovnat specu**. Bez bloku `exterior` se kreslí starým způsobem (Steadfast).
Pak kontrola výkresu: `silhouette_compare.py views` na maskách (uzávěr ~0 %, symetrie ≥ 0,98).
JSON měň skriptem (Write do scratchpadu, pak Python); pole čísel drž na jednom řádku.

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
- Průchody pro postavu: dveře ≥ 1,0 m, uličky ≥ 1,0 m (kapsle 0,84 m); pilotní křeslo s přístupem zezadu.

## 1b. Dossier a Ship Matrix flotily (povinné u každé lodi, autor 24. 9. 2026)

Autor chce u každé lodi vidět celý postup specifikace a návrhu, jako na RSI Ship Matrix: „přesně takhle
si to představuju a chci to takhle ke každé lodi“.

```bash
python Tools/Design/build_ship_matrix.py                 # celá flotila -> Saved/Dossier/ShipMatrix.html
python Tools/Design/build_ship_matrix.py --ship <Loď>    # jedna loď    -> Saved/Dossier/<Loď>.html
```
- Stránka **Ship Matrix**: karty všech lodí (obrázek, výrobce, role, rozměry, posádka, SCU, SCM, stav),
  filtr velikosti, tabulka s řazením; klik na loď otevře její dossier (hash `#<Loď>`).
- **Dossier** lodi se skládá sám z dat, sekce jen když data existují: stav pipeline (9 kroků se zjistí
  ze souborů), reference ze Ship Matrix, spec proti mediánu, komponenty a zbraně, exteriér, paluby a řez
  s místnostmi a objekty, kontrola siluet výkresu, koncepty s měřením proti výkresu (počítá se při každém
  sestavení), otázky nebo rozhodnutí autora.
- Vstup navíc jen `ArtSource/Ships/<Loď>/Concept/dossier.json`: `status`, `card`, `concepts` (soubor
  a popisek), `check_views` (front/side/top koncepty k měření, u světlého trupu verze `*_cut.png` po
  `remove_background`), `concepts_note`, `questions` → po schválení `decided` a `decisions` [[otázka, odpověď]].
- Stav „schváleno“ bere z `_status` specu (obsahuje `approved`).
- **Publikace:** Artifact vždy do stejných adres (`url` parametr z jiné konverzace):
  - Ship Matrix: https://claude.ai/artifact/VvqHBqFf3xesWcBznpcmHU (`Saved/Dossier/ShipMatrix.html`)
  - dossier Wayfarer: https://claude.ai/artifact/Busq7MdkvGSXMp7RsgP7Ga
  Novou loď nebo nový krok vždy zapiš a Ship Matrix publikuj znovu; autorovi dej odkaz.

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
- **Světlý trup na světle šedém pozadí** rozbije vyříznutí siluety (díry, falešné IoU 0,56). Generuj na
  pozadí kontrastním k trupu (světlý trup → „plain uniform dark charcoal background“), jinak `remove_background`.
- Model rád „zjednoduší“ půdorys (Wayfarer: gondoly přilepené k trupu, rozpětí −20 %). Pomohla třetí
  reference (pohled zepředu, kde gondoly stojí zvlášť) a slovní popis rozestupu; nebo prompt „Fill the dark
  silhouette in the first image with the starship from the second image“ (vodítko jako první reference).

Postup pro novou loď (vše přes MCP a skripty, nic ručně; ověřeno na Wayfareru 24. 9. 2026):
1. Vodítka z masek výkresu: `python Tools/Blender/silhouette_compare.py guide --mask side=Design/guides/<Loď>_mask_side.png
   --mask top=... --mask front=... --out ArtSource/Ships/<Loď>/Design/guides` (tmavá silueta na světle šedé, 16:9).
   Nahrát: `mcp__higgsfield__media_upload` (files[]) → `curl -X PUT` každé → `media_confirm`.
2. **Stylový vzor:** bok jen z vodítka a stylového textu ve 2 variantách (styl značky, barvy, opotřebení);
   vybrat tu, co drží siluetu (Wayfarer: A 0,83 vs. B 0,79). Pak shora, zepředu a 3/4 s referencemi
   *job id vybraného boku* + vodítko daného pohledu („Keep the first image's exact paint …“). Hero jen
   z vodítek bez stylového vzoru tvarově ujede → jen na náladu.
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

## 3b2. Exteriér přesně podle výkresu (Wayfarer v2, výchozí cesta od 24. 9. 2026)

**AI image-to-3D nedává přesný hard-surface** (Wayfarer v1: roztavené plochy, rozeklané hrany, lak na tom nesedí;
autor: „tohle není dost dobré“). Exteriér se proto staví přímo z obrysů schváleného výkresu. AI slouží jen jako
reference stylu.

```bash
MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup --python Tools/Blender/hs_build_ship.py -- ArtSource/Ships/<Loď>/HardSurface/<Loď>_hs.json
MSYS_NO_PATHCONV=1 "$BL" -b ArtSource/Ships/<Loď>/HardSurface/<Loď>_HS.blend --python Tools/Blender/hs_assemble_ship.py -- ArtSource/Ships/<Loď>/HardSurface/<Loď>_hs.json
# pak gamespace_ship_export.py na <Loď>_HS_Game.blend a import_ship.py jako obvykle
```
- **Výkres:** každý obrys v `exterior` má `part`, který ho spojuje přes pohledy. Díl chybějící v pohledu si ho může
  půjčit (`borrow`).
- **Stavba dílů:**
  - `loft: true` (trup): řez = obrys zepředu natažený na šířku shora a výšku z boku;
  - ostatní díly: průnik vytažených obrysů (boolean EXACT);
  - `revolve`: recept `hs_build_part` (poloměry z boku výkresu), obě strany zrcadlově;
  - `cylinders`: válce.
- **Detail:**
  - `seams` na loftu jsou skutečné drážky (`x` stanice přepážek, `around` [strana, výška 0–1], `width`, `depth`);
  - `zones` jsou přesné řezy (`view` x/z nebo polyline side/top) plus materiál podle středu plošky;
  - `canopy_frame`: vzpěry, páteř, zapuštění skla;
  - `greebles`: díly kitu na paprsku k trupu, každý s `_what` (účel), barva laku.
- **Kontrola:** `silhouette_compare.py` proti `guides/<Loď>_mask_*` má být ≥ 0,95. Když díl nesedí, bývá chyba ve
  výkresu (Wayfarer: ploutev shora užší, než je vykloněná), a opravuje se výkres.
- **Assemble:** `groups` (Canopy, Gear), `offset` (layout → střed), `collision` a `sockets` v souřadnicích layoutu,
  `greeble_material`. Instance kitu se před převodem realizují, jinak se detaily neexportují.
- **Materiály v setupu:** slot na zónu, master `hull` s barvou (lineární), sklo `glass`, emise `_Emissive`.

## 3b3. Vrstvy detailu podle SC: decaly, trim sheet, mesh decaly v UE (autor 24. 9. 2026)

Rozbor lodi ze SC (Argo MOLE): mesh není hustý. Detail dělají mesh decaly, vrstvené materiály (kolem 12),
střední vrstva tvaru (desky s tloušťkou, zapuštěná místa, odhalená mechanika), zkosené hrany a světla.
Pořadí prací: knihovna decalů → trim sheet → mesh decaly v UE → tvar → materiál → světla. Vše nejdřív jako
pilot na jedné části.

**Knihovna decalů a trim sheet** (`Tools/Blender/decal_library.py`, recept
`ArtSource/Ships/Shared/Decals/decal_library.json`):
```bash
MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup --python Tools/Blender/decal_library.py -- ArtSource/Ships/Shared/Decals/decal_library.json
```
- Každá položka je skutečná geometrie v buňce mřížky 4 × 4 (buňka 0,5 m, atlas 2048 px, tedy ~1 mm/px):
  deska stopy se zapuštěnými místy (boolean) a díly na ní (`box`, `cyl`, `hex`, `bar`, `bar_y`, `repeat`/`step`).
- Ortografická kamera vyrenderuje průchody jako emisní přepsání materiálu do float EXR, takže hodnoty jsou přesné.
  Výsledné mapy:
  - `T_Decals_N` / `T_Trim_N`: normála OpenGL, v UE se převrací zelená;
  - `_H`: výška, 0,5 = povrch, ±3 cm;
  - `_AO`: okluze;
  - `_BC`: sRGB barva, A = krytí barvy (jen `paint_color`);
  - `_M`: R alfa, G drsnost, B kov.
- `decal_library_index.json` obsahuje UV obdélník, rozměr v metrech a účel každé položky, u trimu V rozsah pruhu.
  Novou položku stačí přidat do receptu a postavit znovu.
- Trim sheet: pruhy dlaždicované po U každé 2 m (lem, žebrování, šrouby, lišta, pás s výstupky, stupeň, mřížka,
  dvojitá spára).

**Mesh decaly v UE 5.8** (ověřeno `Tools/Tests/probe_mesh_decals.py`):
- Projekt má `r.DBuffer = 1`. Mastery `M_Ship_MeshDecal` a `M_Ship_MeshDecalPaint` jsou v doméně Deferred Decal,
  translucent. Engine z připojených pinů odvodí, co decal zapisuje:
  - `meshdecal` (normála + drsnost + kov) nechá lak trupu;
  - `meshdecal_paint` přidá barvu (štítky, pruhy).
  - Hull master přijímá barvu, normálu i drsnost (`MDR_COLOR_NORMAL_ROUGHNESS`).
- DBuffer nemá kanál AO. AO decalu jde jen do barvy u `meshdecal_paint`, u ostatních ho nese normála a drsnost.
- Nanite neumí materiál v doméně decal. Decaly jsou proto **vlastní díl bez Nanite** (`SM_Ship_<Loď>_Decals`,
  `no_nanite_parts`), stejně jako sklo. Zobrazit se mají i na Nanite trupu (DBuffer se aplikuje v base passu),
  pilot to musí potvrdit snímkem.
- Proti z-fightingu: čtverce decalů 2 mm nad povrchem (`r.MeshDecals.DepthBias` je 0).
- Textury v setupu: klíče `decal_normal`, `decal_m`, `decal_bc` (import nastaví normálovou mapu nebo masky).
  Parametry `decal_normal_strength`, `decal_opacity`, `decal_roughness_scale`.
- **Ověřeno ve hře (24. 9. 2026, pilot Wayfarer):** mesh decaly se kreslí i na Nanite trupu a na Nanite
  gondolách (šrouby, poklopy, štítky, madla). Díl `Decals` má `cast_shadow` a distance field vypnuté
  (`import_ship.py`).
- **Barva přes dva čtverce:** DBuffer decal má jedno krytí pro všechno, co zapisuje. Každá položka
  s vlastní barvou má proto normal-only čtverec a nad ním (0,8 mm) paint čtverec s krytím
  M.R × BC.A. BC.A je 1 jen tam, kde má díl vlastní barvu (průchod `own`), barva je vynásobená AO.
- **Pozor na mip bleed:** při přímé alfě se v menších mipech průhledná barva mísí do okraje.
  Tmavé mřížky tak měly na tmavém krytu světlý rámeček. `decal_library.py` proto rozšiřuje barvu
  do průhledných texelů (`dilate_colour`, 64 px).

**Rozmístění na lodi** (`Tools/Blender/hs_decals.py`, blok `decals` v `<Loď>_hs.json`, volá
`hs_assemble_ship.py` po spojení a posunu):
- `items`: položka z indexu, `on` = `pod` (x, deg), `side` (x, z), `top`/`bottom` (x, y) nebo `ray` (at, dir).
  Dále `rot`, `scale`, `mirror` a `along` {step, count}.
- `trim`: pás `strip` jako `pod_ring` (x, rozsah úhlů), `pod_line`, `top_cross`/`bottom_cross`.
- Každý bod mřížky (6 cm) se paprskem položí zpět na trup a zvedne o 2 mm, takže sleduje zakřivení.
- Decal, který by přečníval hranu (bod mine povrch nebo má normálu odchýlenou o víc než 30°), se
  vynechá a vypíše (`HSDECALS skipped`). Pás se na nespojitosti rozdělí; jinak visel přes okraj
  střechy do vzduchu.
- Osa x decalu jde po lodi a z venku doprava, takže atlas se čte správně na obou bocích a není
  zrcadlený.
- Rychlý náhled bez UE: Eevee render herního `.blend` s atlasy na slotech Decal / DecalPaint / Trim /
  TrimPaint. Normal-only čtverce v něm vypadají světlejší, protože Eevee neumí „ponechat barvu trupu“.

**Knihovna v2 a typy decalů** (autor 24. 9. 2026, závazné):
- Atlas 4096 px s pevnou hustotou 2048 px/m (0,5 mm na texel). Položky se automaticky rozmístí podle stopy
  (`pack`), takže všechny jsou stejně ostré. Recept: `decal_library.json` (`size_px`, `px_per_m`, položky s `type`
  a `tags`). Plná přestavba trvá asi 10 min, `-- refine` jen přepočítá alfu.
- **Strukturní** decaly (spáry, štěrbiny, nýty, šrouby, zapuštěné panely, mřížky, poklopy, zásuvky) **nemají
  zapečenou barvu**. Nesou normálu, drsnost a AO a barvu berou z podkladu:
  - kreslí se normal-only čtvercem (`meshdecal`, slot Decal) a nad ním čtvercem s AO (`meshdecal_ao`, slot
    DecalAO);
  - AO čtverec píše jen černou barvu s krytím (1 − AO), takže DBuffer lak pod sebou ztmaví.
- **Informační** decaly (nápisy, registrace, čísla panelů, štítky, šipky, výstražné pruhy, madla) mají vlastní
  barvu (`meshdecal_paint`, M.R × BC.A).
- **Opotřebení** (stékání, škrábance, oděry) je procedurální s měkkou alfou a používá se střídmě.
- Alfa strukturních decalů pokrývá jen skutečné prvky (`feature_alpha`: odchylka normály nebo výšky, 5 texelů
  od okraje stopy nic). Plochá stopa jinak přepisovala drsnost laku a kreslila obdélník kolem každého decalu.
- Text jde z fontů projektu (`Content/UI/Fonts`: Rajdhani, Share Tech Mono) jako vystouplá geometrie. Díly
  typu `poly` (šipky), `rivet`, `ring` a `corner_screws` dávají položkám vnitřní strukturu.

**Rozmístění podle pravidel** (`hs_decals.py`, `decals.rules`, `seed`; vše se znovu vygeneruje):
- `hull_seams`: prstence nýtů po spárách trupu a podélné linie. `pod_gaps`: spáry gondol z receptu gondoly;
  `avoid` vynechá šachtu.
- `plate_edges`: nýty podél okrajů desek. `panel_marks`: číslo na každém panelu gondoly a vyjmenované značky
  trupu.
- `clusters`: shluky kolem motorů, šachty, sání, rampy a podvozku. `companions`: štítek a madlo u každého
  poklopu, stékání pod mřížkou (`streak_chance`).
- Hero položky (`items`) se kladou první. Kontrolují se tak:
  - překryv orientovaných obdélníků (SAT);
  - hrany (bod mimo povrch, normála nad 30°, schod přes 12 mm mezi sousedními body);
  - pás se na nespojitosti nebo převisu přeruší.
- Text a šipky jsou na bocích a svazích vždy nahoru; na střeše a břiše se čtou z bližší strany lodi.
- Assemble vypíše počty podle dílů, pravidel a typů (`HSASSEMBLE ... "decals"`).

**Hustota podle referencí SC** (rozbor Pisces, 100i, Mustang a Titan, 24. 9. 2026):
- Hustotu dělají **tenké panelové linky** po 0,3–0,8 m se zalomením 45°, ne nýty. Pravidlo `panel_lines` (pásy
  pro boky, střechu, břicho a křídla, gondoly po panelech); pásy se nesmí křížit.
- Značení je **tón v tónu**: šedá na bílé a na tmavé. Výstražné pruhy na laku jsou šedé (`hazard_subtle`,
  `tri_warning`), žluté jen u podvozku a rampy.
- Porty a senzory mají šipky ‹‹ ●  ›› (`chevrons_port`); drobné červené značky (`red_marker`, `red_dot`) u poklopů.
- Malé servisní nápisy mají písmo 2 cm (`st_*`, Share Tech Mono).
- Aspoň jeden decal na každém panelu nad 0,5 m (`coverage`, mřížka s jitterem); u servisních míst shluky.
- Celá loď: kolem 800 decalů a 650 m pásů. Decaly se plynule stmívají mezi 60 a 90 m
  (`DecalFadeStartCm` / `EndCm`); díl Decals se přestane kreslit v 95 m. Menu (24 m), chase kamera a přistání
  jsou v plném rozsahu (preset `decal_fade`).

**„Feel“ SC: rozbor referencí** (Docs/UI screenshoty Titan, Guardian, Hornet, Cutlass, Spirit; ship matrix Pisces,
100i, Mustang, Aurora; porovnáno se stejných vzdáleností, 24. 9. 2026):

| Kategorie | SC má | Wayfarer měl (před) | Chybělo / co jsme udělali |
| --- | --- | --- | --- |
| Hodnotová stavba (zdálky) | 30–60 % plochy tmavé: grafitové zóny, tmavý podvozek mezi bílými deskami; loď se čte i jako silueta dvou tónů | ~95 % bílé, tmavý jen nos a záď | **nejdůležitější** – livrej (analytické zóny, 3 varianty) |
| Povrch (zblízka) | lesklý lak s clear coatem, odráží oblohu a okolí; sousední desky se liší tónem a leskem | matný lak, všechny desky stejné | clear coat 1 / 0,05; variace po panelu (UV1), 8 % kovových a 5 % karbonových panelů |
| Spáry | tmavé pryžové/stínové spáry 0,5–1 cm, rámují každý panel | světlé drážky splývaly s lakem | těsnění v drážkách (materiál Seal) |
| Velké značení | jméno / registrace přes část boku, logo výrobce, velké výstražné zóny u trysek a rampy (1 až 4 m) | jen malé nápisy (≤ 0,6 m) | promítané decaly WAYFARER, HF-0417, logo Halcyon, EXHAUST / RAMP |
| Manévrovací trysky | 12–30 bloků na malé lodi, na přídi, bocích, zádi, spodku i hřbetu | žádné | 26 bloků RCS (`hs_functional.py`) |
| Antény, senzory | 2–5 na loď (lopatka, bič, kopule) | 1 senzorový kit | 2 lopatky, bič, 2 kopule |
| Mechanika zvenku | závěsy klapek, písty, objímky zbraní, přípojky | kryty klapek, holé hlavně | závěsy, objímky zbraní, přípojky |
| Malé decaly | 0,5–2 / m² na klidných plochách, 5–10 / m² u servisních míst | ~0,8 / m² | beze změny (hustota už odpovídá) |
| Světla | pozice, obrys, reflektory, pásy; často modrobílé emisní lišty | pozice, obrys, reflektor, šachta | (další krok: emisní lišty podél trupu) |
| Siluetové vrstvy | hluboké převisy, negativní prostor mezi deskami | hladký loft s deskami 2–3 cm | (omezeno výkresem; siluetu nesmíme měnit) |

Závěr: rozdíl ve „feelu“ dělá hlavně **hodnotová stavba a lesk**, až potom počet detailů. Livrej a clear coat
mají největší efekt ze všech vzdáleností.

**„Feel“ SC uvnitř: rozbor referencí interiérů** (21 autorových snímků `starcitizenreference/Screenshot
2026-09-25 02*.png`: Argo, MISC, RSI, Origin, Drake, Crusader, obytné moduly i chodby; 25. 9. 2026). Autor
na jejich kvalitu míří. Wayfarer v1 (hs_interior.py, boxy z půdorysu) autor odmítl: „prázdný byt nebo kancelář“.

| Kategorie | SC má | Wayfarer v1 měl | Chybí / co s tím |
| --- | --- | --- | --- |
| Tvar prostoru | průřez lichoběžník nebo osmiúhelník, zkosené horní rohy, strop 2,1–2,4 m, portály (rámy) každých 1–2 m lámou délku | pravoúhlý box 3,8 × 2,3 m, rovný strop | zkosení nahoře, portál na každém modulu kitu |
| Konstrukce | odhalená žebra a nosníky, příhradový strop (Drake), kabelové svazky ve žlabech (žluté u MISC), potrubí s objímkami, vzduchotechnika | tenká žebra zapuštěná ve stěně | stropní žlab s kabely a trubkami, žebra přes celý profil |
| Vrstvy stěny | 3 roviny: nosná konstrukce, panely s přesahem 2–8 cm, výbava na panelech; panely 0,6–1,2 m, dělené spárou | jedna rovina, velké plochy | díly kitu (trim sheet s normálovou mapou), přesahy, lišty |
| Vybavení | skříňky se západkami, madla, hasicí přístroj, výdejník, obrazovka na rameni, lavice s čalouněním, žebřík; **ve shlucích** u dveří, konzolí, lůžka, techniky, mezi nimi klid | kvádry předmětů z půdorysu | výbava podle funkce místa, shluky, klidné plochy mezi |
| Materiály | lakovaný kov ve 2–3 tónech, holý kov na hranách, prošívané čalounění (Argo, Drake), gumová a děrovaná protiskluzová podlaha, karbon (RSI), barevný akcent výrobce (Argo oranž, RSI modrá, Drake žlutá) | jednolité plochy jednoho materiálu | trim textury kitu přetónované do palety, oranžový akcent Halcyonu, guma, čalounění |
| Decaly | velká čísla sekcí a dveří (01, 02), logo výrobce na stěně, výstražné pruhy u prahů a rampy, šipky, štítky CAUTION, čáry na podlaze | žádné | promítané decaly interiéru: místnosti, sekce, nouzové značky, šipky, pruhy |
| Světlo | kontrast: svítidla v pouzdrech (lišty ve zkosení, kruhová stropní), kužele a tmavé kouty, akcentová a orientační světla u podlahy, displeje a kontrolky; teplé 3000–4000 K proti studeným displejům | rovnoměrně svítící strop, bodovky bez pouzder | světla v pouzdrech kitu, směrová, tmavá místa mezi nimi, akcent u podlahy |
| Hustota detailu | 3 úrovně: velké (portály, panely), střední (skříňky, madla, ventilace 0,2–0,5 m), malé (šrouby, kontrolky, štítky 1–5 cm) | jen velké | všechny tři úrovně, malé hlavně u funkčních míst |

Závěr: interiér SC stojí na **konstrukci a vrstvách** (profil, portály, žlaby, panely s hloubkou) a
**kontrastním světle**. Předměty jsou až třetí vrstva. Postup: modulární kit (Quaternius, CC0) jako nosná
vrstva, procedurální přesný detail a decaly navíc (`Docs/AssetPipeline_Modular.md`).

**Kabina (kokpit) SC: rozbor a cílová čísla** (25. 9. 2026). Hlavní reference `cockpit_reference_holo.png`
v repozitáři není; náhradou autorových 5 snímků kokpitů SC `starcitizenreference/cockpit_reference_1..5.png`
(1, 2, 4 lehká stíhačka ve vesmíru / ve dne / v noci, 3 luxusní kabina, 5 těžký rám). Cíl = medián.

| Kategorie | SC má | Wayfarer má (po konceptu A) | Chybí |
| --- | --- | --- | --- |
| Displeje | tenké skleněné panely, průhledné, svítí jen obsah, tenký technický rám s podsvíceným okrajem, na držácích; často jeden široký panel pod linií pohledu (3, 5) | dva MFD v tlustých chromových rámečcích, neprůhledné tmavé pozadí | sklo, průhlednost, edge light, držáky, široký centrální panel |
| Fyzické ovladače | moduly (pods) s pouzdrem, rámem, šrouby a štítkem; páčky s kryty, voliče s drážkováním, kolébky, řady podsvícených tlačítek (12–18 mm), popisky u všeho | kulaté tečky a holé válce, pár kláves | skutečné tvary se zkosením, moduly, popisky |
| Kontrolky | desítky LED v řadách, oranžové a bílé, některé blikají | pár emisivních teček | řady LED, blikání |
| Palubní deska | nízká (horní hrana 23–47 % výšky obrazu od spodu, medián 35 %), mělká, dva moduly po stranách a střed otevřený dolů | horní hrana 39,8 % | mírně snížit a zúžit |
| Rám skla | skoro bezrámová kabina (1–4): jen tenký rám nahoře (0,4–0,7 % šířky), nic v pásu ±15° kolem pohledu; těžký rám (5) má sloupky 3,5 % | středový kříž nahoře, plné boční stěny, výhled 24,5 % | tenký rám, bez kříže, větší skla (cíl výhledu medián 62 %, rozsah 45–75 %) |
| Hologram lodi | vlastní loď jako modrý aditivní hologram vlevo nahoře (1, 2, 3) mimo pohled | drátěné kroužky radaru | hologram z meshe lodi |
| Světlo | tmavá kabina, světlo hlavně z displejů, hologramů a kontrolek, tlumené akcenty | světlá krémová kabina, výplňová světla | tmavší základ, ostrůvky světla |
| Barvy materiálů | tmavý grafit / gunmetal kolem displejů, světlé jen akcenty (3 bílá luxusní výjimka) | krémový rám kolem displejů | tmavé kolem displejů, krém jako akcent |

Změřeno (1920×1080, `Tools/Blender/eye_view_metrics.py`, reference odečtené z mřížky):

| Veličina | Ref 1 | Ref 2 | Ref 3 | Ref 4 | Ref 5 | **Medián (cíl ±15 %)** | Wayfarer před | Wayfarer po kroku 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Výhled ven (% plochy) | 62 | 51 | 75 | 62 | 45 | **62 (53–71)** | 24,5 | 60,8 |
| Horní hrana desky (% od spodu) | 38 | 47 | 23 | 35 | 28 | **35 (30–40)** | 39,8 | 35,3 |
| Nejširší sloupek v poli (% šířky) | 0,4 | 0,7 | 0,5 | 2 | 3,5 | **0,7** (≤ 2 přijatelné) | 42,1 (plné boční stěny) | 2,3 |
| Sloupek v pásu ±15° | ne | ne | ne | ne | ne | **ne** | ne | ne |

Krok 2 (25. 9. 2026): sklo začínalo 1–1,3 m nad okem, takže víc skla nepomohlo. **Oko musí sedět v pásu skla.**
Kokpit se proto zvedl o 0,8 m: podlaha 1,15, oko 2,45, schody z kabiny. Dál:
- zrušená podélná páteř a přední vzpěra (ležela v horizontu), vzpěry 6 cm;
- horní trysky RCS ze skla na nos;
- deska o 5 cm níž.

Exteriér a silueta zůstaly stejné. Měření `eye_view_metrics.py` čte oko ze `SOCKET_Cockpit` otevřeného blendu.

**Livrej a lak** (`M_Ship_Layered`, setup Paint): zóny v prostoru lodi (cm) – `TopZ/TopSlope` sedlo, `BotZ/BotSlope`
spodek, `TailX`, `NoseX`, pruh `StripeZ/StripeSlope/StripeW/StripeX0/X1` v `AccentColor`, zóny v `LiveryColor`;
`LiveryAmount` 1 jen v primárním laku. Varianty v `_livery_variants` setupu; přepnutí za běhu
`space.ShipMat <param> <hodnota>` (presety `livery_sun` / `livery_dusk`). Variace panelů: UV1 z
`hs_layers.panel_ids` (trup po polích spár, ostatní díly po objektech), `PanelTone`, `PanelRough`, `MetalShare`,
`CarbonShare`. Clear coat přes MakeMaterialAttributes (Python enum nemá piny CustomData).

**Křídla a ploutve** (`Tools/Blender/hs_wings.py`, blok `wings`): desku z obrysů přestaví na tvarovaný profil
uvnitř ní.
- Řezy po rozpětí mají přesný interval tětivy (bisekce paprskem), takže obrys výkresu zůstane.
- Profil NACA má maximum rovné tloušťce desky v 30 % tětivy. Pozor na normalizaci: závorka je 0,10003.
- Díly jsou oddělené skutečnou spárou: náběžná hrana, box, klapka nebo směrovka (sekundární lak) nad tmavým
  jádrem bez spár (silueta zůstává zavřená), kryty mechanismu klapek. Decaly na nich pravidly
  `coverage` / `panel_lines` s rozsahem y křídla.

**Podvozek** (`Tools/Blender/hs_gear.py`, blok `gear`): noha v obálce výkresu.
- Úchyt a olejopneumatický tlumič s lesklým pístem a objímkou.
- Nůžkové vzpěry, šikmá vzpěra, hydraulika.
- Kryt nohy s výstražným pruhem vyplní obálku v bočním pohledu.
- Kloub a patka s pryžovou podrážkou a žebry.
- Výsledek je jeden objekt pod původním jménem (skupina Gear, kterou pawn zvedá a spouští).

**Vrstva tvaru** (`Tools/Blender/hs_detail.py`, blok `detail`, volá `hs_build_ship.py` po zónách):
- `hull_plates`: oblast (`x`, `z` / `abs_y`, `normal_z`, `centre`) se rozřízne rovinami hranic, zkopíruje, dostane
  Solidify ven (`t`) a zkosení. `secondary` znamená sekundární lak.
- `hull_recesses`: inset + stěny + tmavé dno a výplň (`louvers` nebo `pipes`). Trubky v žlabu na hřebeni sahají
  k povrchu, jinak klesne silueta.
- `pod`: `plates` (úhly: 0 ven, 90 nahoru; pozor na ploutev na hřbetu), `bay` (panel i substruktura pryč, uzavřená
  vana s potrubím, aktuátorem a objímkami), `pipe_run`. Levá strana se staví a zrcadlí.
- Po každé změně `silhouette_compare.py` proti maskám výkresu; hodnoty nesmí klesnout.

**Vrstvený materiál** (`M_Ship_Layered`, klíč `layered`; masky peče `Tools/Blender/hs_layers.py`, blok `layers`):
- Vertex colour: R = AO (24 kosinových paprsků, 0,5 m), G = 1 − konvexní hrana (jen vrcholy s ploškami do
  `edge_max_face_m2`), B = 1 − sekundární lak (atribut plošky `paint2` z `hs_detail.py`), A = míra vrstev
  (`region_x` = pilot).
- Instance nastavují libovolný parametr: `vectors` / `scalars` v setupu (PrimaryColor, SecondaryColor,
  BareMetalColor, DirtColor, EdgeWear, DirtAmount, GrungeAmount, …).

**Světla** (`Tools/Blender/hs_lights.py`, blok `lights`):
- `lenses`: tmavé pouzdro a emisní čočka paprskem na povrch, `mirror_color` (červená vlevo, zelená vpravo),
  volitelně `light` (point nebo spot s `aim`).
- `strips`: pás po gondole, `r` = pevný poloměr, například dno šachty.
- `points`: samotná světla.
- Skutečná světla: scéna → `Export/<Loď>_lights.json` → `import_ship.py` → komponenty `Light_*` bez stínů.
- Ladění podle snímků: polohové světlo 3 cd (křídlo je 30 cm od něj), čočky mají emisi 25 až 30.

**Detail ve hře zblízka:** preset `Tools/Shots/pilot_views.json` používá volnou kameru v prostoru lodi
(`camera_local` / `look_local` v metrech; X dopředu, Y doprava, Z nahoru; up vektor bere z lodi).
Převod ze souřadnic layoutu: x − offset_x, −y, z − offset_z.

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
Loď pod testem: `Tools/Tests/ship_under_test.py` (`SHIP`), úvodní obrazovka: `MENU_SHIP` v `build_main_menu.py`
(po přidání dílu ji postav znovu). Kontroly kokpitu a free looku se bez dílu Interior a socketů Display_ přeskočí.
Po každém kroku lodi doplň `dossier.json` (u modelu klíč `model`: `renders`, `shots`, `known`), ulož rendery do
`ArtSource/Ships/<Loď>/Renders/` (i `silhouette_compare render` masky `model_*.png`), snímky do `Docs/Shots/<Loď>/`
a znovu publikuj Ship Matrix (1b).
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
