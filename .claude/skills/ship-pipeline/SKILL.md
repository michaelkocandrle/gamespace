---
name: ship-pipeline
description: How a ship goes from idea to Unreal in gamespace - Ship Matrix reference set (fetch_ship_matrix.py), the mandatory 2D design stage (ArtSource/Ships/<Ship>/Design, <Ship>_layout.json with exterior outlines, draw_ship_design.py, <Ship>_spec.json in RSI Ship Matrix shape, author approval), the design dossier and fleet Ship Matrix page (build_ship_matrix.py, published as an Artifact), technical drawings drawn from the build data with IDs (assign_exterior_ids.py, <Ship>_exterior_design.json, exterior_model.py, draw_exterior_sheet.py, test_exterior_drawing.py; interior sheets from the built FBX: fbx_mesh.py, mesh_draw.py, interior_model.py, assign_interior_ids.py, <Ship>_interior_design.json, draw_interior_sheet.py, test_interior_drawing.py), consistent concept views via Higgsfield as style reference, the exterior built exactly from the drawing (hs_build_ship.py, hs_assemble_ship.py, <Ship>_hs.json), silhouette_compare.py, detail layers (decal library, mesh decals, livery, wings, gear, lights), Blender export (gamespace_ship_export.py, manifest) and Unreal import (import_ship.py, <Ship>_setup.json). Reference file legacy-ai-model.md covers the older AI-model recipe (build_ai_ship.py). Load when designing a new ship, building or changing a ship exterior, touching sockets/UCX collision/pivot/LODs/ship materials/naming/decals, or running the ship export/import scripts.
---

# Loď: od nápadu do Unrealu

Vzor celého návrhu (reference, spec, layout s exteriérem, koncepty, dossier, hs recept): **`ArtSource/Ships/Wayfarer/`**.
Autor není herní vývojář: **všechno skriptem / receptem**, nic ručním klikáním v Blenderu ani editoru.
Interiér lodi: skill `ship-interior`; vizuální předání: skill `visual-review`. `Docs/Ships/ShipPipeline.md` popisuje
starší AI cestu a ruční kroky (dnes je dělá recept); starší AI recept je v `legacy-ai-model.md` tohoto skillu.
Historie měření a rozborů: `Docs/Archive/skills/ship-pipeline_2026-09-30.md`.

Blender z Git Bash vždy s `MSYS_NO_PATHCONV=1` (jinak se `//Export` přepíše na `/Export`):
```bash
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
MSYS_NO_PATHCONV=1 "$BL" -b ...
```
UE skripty a testy spouštěj **nástrojem PowerShell** (`.\Tools\run_editor_python.ps1 ...`), přes bash se
rozbije `$PSScriptRoot`.

## 0. Pořadí fází (nepřeskakovat)

1. **Reference ze Ship Matrix** (1a) → **spec** → **2D návrh** (layout s exteriérem, výkresy, kontrola siluet) →
   **koncepty** jako reference stylu (2a) → **dossier + Ship Matrix** (1b) → schválení autorem.
   **Dokud autor neschválí, nic se nestaví ve 3D.**
2. **Exteriér přesně z výkresu** (3b2): `hs_build_ship.py` → `hs_assemble_ship.py` → `<Loď>_HS_Game.blend`
   (test geometrie běží na konci sám). AI geometrie lodi ne (od 24. 9. 2026); AI jen jako reference stylu.
3. Vrstvy detailu (3b3): decaly, trim, livrej, křídla, podvozek, světla; silueta proti maskám výkresu (3b).
4. `gamespace_ship_export.py` → FBX + `<Loď>_manifest.json` (5).
5. `import_ship.py` + `<Loď>_setup.json` → `BP_Ship_<Loď>`; pak `build_main_menu.py` (6).
6. Testy + snímky (7), vizuální kritik (skill `visual-review`), dossier a Ship Matrix znovu (1b).

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
totéž co `<Loď>_setup.json` (build config). Existují: `Wayfarer_spec.json`, `Steadfast_spec.json`, `Delver_spec.json`, `Farsight_spec.json`.

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
  studené UI jen tam, kde se pracuje. Paleta interiéru podle výrobce: `ArtSource/Kit/kit_rules.json`
  (`palettes`, skill `ship-interior`); oranžová Halcyon Freightworks `0.85, 0.34, 0.06`.
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

## 1c. Technické výkresy z dat (dossier body 3, 4, 6; autor 1. 10. 2026)

Jeden zdroj dat: výkres obsahuje jen to, co je v datech, a data jen to, co je ve výkresu; každý díl kitu,
decal, světlo a funkční prvek nese ve výkresu stejné ID jako v datech.
```bash
python Tools/Design/assign_exterior_ids.py <Loď> [--check]   # doplní "id" do receptu a setupu (stávající nemění)
python Tools/Design/exterior_model.py <Loď>                  # model výkresu: prvky, stavy, co je vidět z boku
python Tools/Design/draw_exterior_sheet.py <Loď> [--dpi 200] [--sheets E-03 E-05]   # listy E-01..E-07 -> Design/Drawings
python Tools/Tests/test_exterior_drawing.py                  # výkres = data (i v Test.ps1 a CI)
```
- **Postavené** prvky jsou v datech stavby (`<Loď>_hs.json`, `<Loď>_setup.json`) s `"id"` (builder ho ignoruje);
  **nepostavené** v `Design/<Loď>_exterior_design.json`: `proposed` prvky, `changes` (`change` s `set`, `remove`),
  materiálové zóny `MZ-*` se šrafou, exteriérový kit `XK-*`, desky boků (pásy × pole mezi příčkami → `P-S-<pás><pole>`),
  český účel postavených prvků `purpose` (v datech stavby je jen anglický `_what`; test hlídá, že žádný nechybí).
  Exteriérový kit se pak staví z týchž dat návrhu.
- Stavy na výkresu: postaveno černě, návrh modře (+), změna modře (Δ, stará poloha červeně čárkovaně), odstranit
  červeně (×). Skryté za bližším dílem čárkovaně (model počítá viditelnost dílů z boku a hloubku z pohledu shora).
- Model hlásí, kam prvek „z boku“ opravdu dopadne (nejbližší díl, WORKFLOW 9.6 fb), co je skryté, výřezy v deskách
  a podklad nápisů – „Kontrola dat“ na listu; desky musí vyříznout místo pro díly na plášti (WORKFLOW 9.6 fe).
- **Listy exteriéru** (styl E-01 schválen 1. 10. 2026): E-01 pravobok (A desky a materiály, B prvky, detail A gondola),
  E-02 tabulky, E-03 shora, E-04 zespodu, E-05 zezadu 1:20 a zepředu 1:30, E-06 levobok (A a B zrcadlově, kontrola
  nápisů levé strany), E-07 detaily (příď s kabinou, rampa s rámem a písty, gondola shora), E-08 detaily (hlavní
  podvozek s částmi podle `hs_gear.leg`, držák zbraně s řezem). Skladba listů E-03 až E-08:
  `Tools/Design/draw_exterior_views.py`. Detail má přinést, co pohled 1:30 neumí (části, kóty, řez), jinak nepatří
  na list (kritik pohledů 1. 10. 2026).
- **Pohledy** počítá `Tools/Design/exterior_views.py` z týchž dat jako pravobok (`Element.geo[view]`;
  `Model.use_view(view)` přepne `e.sb`, `m.solids`, `m.canopy`, takže kreslič kreslí každý pohled stejným kódem):
  tělesa z horních a čelních obrysů layoutu s pořadím zakrývání (`ORDER`); prvky boku trupu, které leží na horním
  nebo spodním zkosení, se do půdorysu promítnou přes poloviční šířku trupu v dané výšce; prvky z hřbetu a břicha
  (x, y), z gondol (x, úhel), ze zadní stěny (paprsky podél x) a návrhu se kladou přímo z dat. Levobok se ukládá
  v souřadnicích pravoboku a zrcadlí ho rám (`Frame(flip=True)`). Směr čtení nápisů na hřbetu a břiše podle
  `hs_decals._frame` (od bližšího boku), šipka u každé kopie.
- **Sklo kabiny z boku** je jen tam, kde je trup uvnitř obou obrysů kabiny (boční i horní, jako
  `hs_build_ship.split_canopy`): kde je trup širší než horní obrys, končí sklo výš na rameni (ověřeno na postavené
  kabině 1. 10. 2026; samotný boční obrys kreslil sklo o 35 cm níž).
- Výkresy E-01 až E-08 autor schválil 1. 10. 2026 (revize C: hřbet R v primárním laku, rám rampy); kit a pilot
  se staví podle nich.

### Výkresy interiéru (bod 4) a koncepty (bod 6) – druhá session (1. 10. 2026)

- **Styl listů** = schválené E-01 až E-08: A0 na šířku 1189 × 841 mm, PNG 200 dpi do `Design/Drawings/<Loď>_<list>.png`,
  vektorové PDF do `Saved/Drawings/`, ke každému listu postranní JSON (ID nakreslená a popsaná po pohledech, tabulky,
  otisky dat). Stavebnice v `Tools/Design/draw_exterior_sheet.py`: `Sheet` (písmo Bahnschrift se záložními Segoe UI
  a Segoe UI Symbol), `Frame` (měřítko, výřez, `flip`), `Drawer` (`place_labels`: popisky v řadách nad a pod
  pohledem se sběrnicí odkazů; `panel_labels`; stavové barvy `STATUS_COL` / `STATUS_MARK`), `frame_and_zones`,
  `title_block`, `legend`, `table`, `wrap`, `dim_h` / `dim_v`; detaily a kóty v `draw_exterior_views.py`
  (`detail_window`, `dim_chain`, `dim_vert`, `balloon_column`). Popisky česky, kód anglicky.
- **Jeden zdroj dat a test:** výkres kreslí jen to, co je v datech, a každý prvek nese ID z dat. Vzor testu
  `Tools/Tests/test_exterior_drawing.py` (otisky dat v JSON listu, nakreslené = model po pohledech, každé nakreslené
  ID popsané, český účel u každého postaveného prvku, kontroly konfliktů). ID doplňuje `Tools/Design/assign_exterior_ids.py`
  (`json_ids.py`) jen v exteriérových blocích receptu a setupu; ID interiéru jsou v datech návrhu interiéru (níže).
- **Co z interiéru je v datech:** `Design/<Loď>_layout.json` – `decks` (výška podlahy, světlá výška, obrys),
  `rooms` (id, název, obdélník nebo polygon, `purpose` česky), `objects` (místnost, obdélník, z, `below` pod podlahou,
  `purpose` česky, poznámky `_kit`, `_liner`), `doors` (poloha, osa, šířka); recept `HardSurface/<Loď>_hs.json`
  blok `interior` (`height_m`, `wall_inset_m`, `sill_z`, `lights` po místnostech, `seat`, `kit_modules` a `kit`
  po místnostech, `cockpit`, `decals` s položkami a rozsevem, `fixture_lights`); stavitel `Tools/Blender/hs_interior.py`
  (+ `hs_interior_kit.py`, `hs_interior_decals.py`, `hs_cockpit.py`, `hs_fixture_lights.py`); interiérový kit
  `ArtSource/Kit/kit_rules.json` a `kit_parts.json` (rastr 0,3 m); světla po stavbě
  `Export/<Loď>_lights.json` (int_*, fix_*); recenze interiéru `Docs/Reviews/2026-09-2*_kit_*`,
  `2026-09-30_cabin_*.md`, `2026-09-30_hold_grid_variants.md`.
- **Koncepty:** zvolený koncept povrchu `concept` v datech návrhu (B + C, obrázky `Concept/surface_v3/`, `prompt.txt`),
  starší koncepty a ořezy `Concept/*.png`, siluety `Design/guides/<Loď>_mask_*.png` a `Tools/Blender/silhouette_compare.py`
  (IoU); obrázky ze Ship Matrix do generátoru nikdy (skill `asset-sources`).
- **Interiér (bod 4)** kreslí postavené díly, ne obdélníky z layoutu (styl I-04 schválen 1. 10.):
  ```bash
  python Tools/Design/assign_interior_ids.py <Loď> [--check]   # ID do Design/<Loď>_interior_design.json "ids"
  python Tools/Design/interior_model.py <Loď>                  # prvky po místnostech, kontrola dat
  python Tools/Design/draw_interior_sheet.py <Loď> [--sheets I-04]   # list místnosti -> Design/Drawings (~1 min)
  python Tools/Tests/test_interior_drawing.py                  # výkres = data (i v Test.ps1 a CI, bez FBX)
  ```
  - Geometrie z FBX v LFS: `fbx_mesh.py` čte binární FBX v čistém Pythonu (meshe v prostoru Blenderu bez kořenové
    konverze, materiál a UV po trojúhelnících, sockety), díly kitu se kladou jako v `kit_layout.layout_parts`,
    interiér a trup lodi = ship space minus `assemble.offset`. `mesh_draw.py` kreslí pravoúhlé pohledy malířovým
    algoritmem (výplň = odstín materiálu, hrany ohybů, obrysy) a řez rovinou (tlustá čára).
  - **ID interiéru nejsou v receptu ani v layoutu**, ale v `Design/<Loď>_interior_design.json` `ids`, navázaná na
    data stavby ověřitelným klíčem (jméno objektu / dveří, `[id, díl]` souběžně s `kit_modules`, `[položka, id]` u
    decalů): zápis do receptu by zneplatnil otisky všech listů exteriéru (WORKFLOW 9.6 fh). Otisky interiéru
    (`interior_model._digests`) berou jen interiérovou část každého souboru; FBX jen informativně (šum stavby).
  - Schéma ID: `<MÍSTNOST>-W-<L|R><n>` stěny od zádi, `-B-<A|F>` přepážky, `-C-<n>` strop, `-FL-<n>` podlaha,
    `-U-` nábytek (= ID objektu layoutu, který díl staví), `-M-` komponenta, `-O-` vybavení, `DR-<z>-<do>` dveře;
    světlo a decal dílu = ID dílu + `/` + socket nebo položka knihovny. Kódy místností v `rooms` dat návrhu.
  - Co který pohled listu místnosti kreslí, určuje `interior_model.sheet_views` (pravidlo pro kreslič i test).
    Řez rovinou bere vrchol v rovině jako „za řezem“ (švy panelů trupu leží na stanicích, WORKFLOW 9.6 fg).
  - List místnosti (vzor I-04 kajuta, 1:20): půdorys v řezu 1,2 m s mřížkou kitu 0,3 m (od začátku běhu stěn a od
    osy), strop zespodu ve směru půdorysu, rozvinuté stěny 1–4 ze středu místnosti, příčný řez s kapslí 0,56 × 1,80
    a zónami nad stropem a pod podlahou, klíčový plán, legenda, tabulky (díly kitu, účel dílů, nábytek / dveře /
    komponenty, světla po socketech, decaly), souhrn světel a výkon, kontrola dat (layout × díl, komponenta mimo
    trup, poznámky `review_notes`).

## 2. Koncepty jako reference stylu

- **Exteriér lodi se staví z výkresu**, koncepty z AI (Higgsfield) slouží jen jako reference stylu, barev a detailu
  a jako obrázky do dossieru. Snímky ze SC do AI generátorů posílat smíš (skill `asset-sources`), výstup nesmí nést
  jména a loga SC.
- **Interiér a komplexní kompozice** (kokpit, pulty, přístroje) nikdy jedním promptem; funkční detail procedurálně.
- Koncept: **2–4 konzistentní pohledy téže lodi: bok, zepředu, shora, 3/4.** Neutrální pozadí, rovnoměrné světlo,
  bez motion bluru a dramatických stínů, celá loď v záběru.

## 2a. Konzistentní pohledy přes Higgsfield MCP (ověřeno 24. 9. 2026)

Závěry z měření (tabulka a test: archiv skillu):
- **Bez vodítka si model domyslí půdorys** a „zepředu“ kreslí seshora šikmo. Hezký obrázek neznamená správný tvar –
  vždy měř.
- **List všech pohledů v jednom obrázku nepoužívej**: pohledy mají každý jiné měřítko a půdorys neodpovídá boku.
- **Vodicí silueta jako druhá reference** je hlavní páka. **Výchozí volba: Nano Banana Pro + vodítko** (IoU 0,90–0,98,
  uzávěr 0,3 %). Vodítko vzniká z našeho 2D návrhu (obrys paluby z `<Loď>_layout.json`, profil z řezu), ne z AI.
- Pohled **zepředu je nejslabší**; plovoucí špičky nebo díly navíc → přegenerovat. **Každý pohled si před použitím
  prohlédni** (Read na PNG), číslo nestačí.
- Podlahu a stín i přes „no floor“ → před měřením `remove_background`. **Světlý trup na světle šedém pozadí** rozbije
  vyříznutí siluety → generuj na kontrastním pozadí.
- Model rád „zjednoduší“ půdorys (Wayfarer: gondoly přilepené k trupu) → třetí reference (pohled zepředu) a slovní
  popis rozestupu, nebo prompt „Fill the dark silhouette in the first image with the starship from the second image“.

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
6. Koncepty jdou do dossieru (`dossier.json`, `check_views`) a jako reference stylu pro stavbu z výkresu (3b2).

## 3b. Měřitelná shoda siluety (`Tools/Blender/silhouette_compare.py`)

Při modelování optimalizuj **číslo**, ne dojem z obrázku.

```bash
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
# 1) masky modelu (Workbench, ortho, headless); --collection / --objects, volitelně výřez
MSYS_NO_PATHCONV=1 "$B" -b Ship.blend --python Tools/Blender/silhouette_compare.py -- render \
    --collection HS_<Loď>_Nacelle_UL --out Saved/Silhouette/nacelle --prefix hs
# reference jako výřez AI modelu (box + válec kolem osy, bez pylonu)
MSYS_NO_PATHCONV=1 "$B" -b ArtSource/Ships/<Loď>/<Loď>_AI.blend --python Tools/Blender/silhouette_compare.py -- render \
    --objects SM_Ship_<Loď> --crop-box=-6.8,3.0,0.4,0.35,6.0,3.4 --crop-cylinder=4.551,1.892,1.24 \
    --out Saved/Silhouette/nacelle --prefix meshy
# 2) porovnání: render proti renderu (světové souřadnice) nebo proti konceptům (bbox)
python Tools/Blender/silhouette_compare.py compare --model Saved/Silhouette/nacelle/hs --ref-model Saved/Silhouette/nacelle/meshy --out Saved/Silhouette/nacelle
python Tools/Blender/silhouette_compare.py compare --model DIR/model --ref front=Concept/front.png --ref side=Concept/side_a.png --ref top=Concept/top.png --out DIR
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
- **Test:** `python Tools/Blender/tests/test_silhouette_compare.py` (i v `Tools/Test.ps1`; render krychle
  v Blenderu jen s `-Blender`).
- **Cíle:** hard-surface díl proti AI objemu ≥ 0,88 na pohled. Nižší číslo znamená špatnou osu nebo
  poloměr, ne detail. Proti konceptu je cíl ≥ 0,9 a `aspect_model` do 3 % od `aspect_ref`.

## 3b2. Exteriér přesně podle výkresu (Wayfarer v2, výchozí cesta od 24. 9. 2026)

**AI image-to-3D nedává přesný hard-surface** (Wayfarer v1: roztavené plochy, rozeklané hrany, lak na tom nesedí;
autor: „tohle není dost dobré“). Exteriér se proto staví přímo z obrysů schváleného výkresu. AI slouží jen jako
reference stylu.

```bash
MSYS_NO_PATHCONV=1 "$BL" -b --factory-startup --python-exit-code 1 --python Tools/Blender/hs_build_ship.py -- ArtSource/Ships/<Loď>/HardSurface/<Loď>_hs.json
MSYS_NO_PATHCONV=1 "$BL" -b ArtSource/Ships/<Loď>/HardSurface/<Loď>_HS.blend --python-exit-code 1 --python Tools/Blender/hs_assemble_ship.py -- ArtSource/Ships/<Loď>/HardSurface/<Loď>_hs.json
# pak gamespace_ship_export.py na <Loď>_HS_Game.blend a import_ship.py jako obvykle
```
- **Výkres:** každý obrys v `exterior` má `part`, který ho spojuje přes pohledy. Díl chybějící v pohledu si ho může
  půjčit (`borrow`).
- **Stavba dílů:**
  - `loft: true` (trup): řez = obrys zepředu natažený na šířku shora a výšku z boku;
  - ostatní díly: průnik vytažených obrysů (boolean EXACT);
  - `revolve`: recept `hs_build_part` (poloměry z boku výkresu), obě strany zrcadlově;
    tryska motoru `exhaust.nozzle` → `hs_build_part.build_nozzle` (zvon, prstence, žebra, hrdlo, středové těleso na
    táhlech, jádro `_NozzleCore` ve slotu Emissive = síla podle tahu); výkres E-05 detail G (`nozzle_detail`); gondola
    v rozpočtu přes `refine` (řady), `panel_bevel_segments`, `sub_segments`;
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

## 3b2b. Exteriérový kit ze schválených výkresů (autor 1. 10. 2026)

Kit se staví z modelu výkresu, ne ručně: co je na výkresu, to je na lodi.
```bash
python Tools/Design/exterior_kit_layout.py <Loď> [--region pilot]   # -> Design/<Loď>_exterior_kit.json (generované)
# recept: "exterior_kit": {"layout": "ArtSource/Ships/<Loď>/Design/<Loď>_exterior_kit.json"}; pak stavba jako v 3b2
```
- **Rozvrh** (`exterior_kit_layout.py`): desky a rám jako obrysy v rovině pohledu (SB x, z pro boční pásy, zrcadlené
  na levobok; TOP x, y pro hřbet; AFT y, z pro zadní stěnu) s výřezy, tloušťkou z kitu (XK-PLATE 30 mm, XK-PLATE-H
  40 mm, rám 15–20 mm), body šroubů a filtrem normál ploch; díly (XK-RCS, XK-STROBE, XK-LANDLIGHT, XK-PISTON) s polohou.
  Oblast `pilot` = hřbet, ramena, záď, gondoly; `ship` = celý trup (všechny pásy, celý rám; 3. 10. 2026). Dno kanálu na
  bocích jen kolem desek a rámu (`skin_near_side` → `skin.near_side`), jinde lak. Pás může mít `merge` [[a, b]] (jedna
  dlouhá deska, žebra ji obejdou: deska pod jménem lodi) a `sub.skip` (pole bez panelu a poklopu, např. pod registrací). Test výkresu hlídá, že rozvrh je z aktuálních dat a staví přesně
  postavené pásy (`panels.built_bands`).
- **Stavba** (`Tools/Blender/hs_exterior_kit.py`, z `hs_build_ship` po vrstvě detailu, před světly, greeblemi
  a decaly): plochy trupu pod obrysem se přesně ořežou (bisect rovinami hran obrysu ve směru pohledu), zkopírují,
  vytáhnou ven o tloušťku a zkosí; každá deska je vlastní objekt (vlastní tón panelu přes `part_obj` → UV1); plášť
  pod deskami a rámem dostane slot `Channel` (dno kanálu: tmavší a hrubší než gunmetal rám, se špínou); záblesková
  světla mají slot `Strobe` (hra ho bliká 0,06 s, mezi záblesky je tma), proto má pouzdro i stálé poziční světlo
  (`PosWhite`, `LightRed`, `LightGreen`); pracovní světlo rampy přidá reflektor do `hs_lights`.
- **Hierarchie povrchu** (kritik pilotu, kolo 1: „kachlíkovaná střecha“, „rám je plochá výplň“): rám má profil T
  (kit `cap_w`/`cap_h` = stojina, `bolt_pitch` = řady šroubů po obou stranách stojiny; `profile()` v rozvrhu), páteř
  je široká (XK-SPINE 280 mm proti žebrům 80 mm), na deskách hřbetu jsou přídavné panely XK-DOUBLER a malé poklopy
  XK-HATCH v rovině desky se spárou (`panels.roof.sub`; `Views.roof_subs` je umístí 70 mm od hran a výřezů, posune
  po poli, jinak vynechá; ID `P-S-R<strana><pole>-D / -H`). Šrouby desek se rozkládají rovnoměrně
  (`em.bolt_columns`, stejně výkres i rozvrh).
- **Střední vrstva** (kritik pilotu, kolo 2): rozvody XK-CONDUIT (`F-CONDUIT`, `on: roof`) leží v servisním kanálu
  mezi páteří a deskami (`roof.spine_gap` 0,34 = půl páteře 0,14 + kanál 0,2 m): trubky podle `pipes` (y od osy,
  Ø, materiál), spodek `lift` nad pláštěm (nad žebry), objímky po `clamp_pitch` mimo žebra, na koncích úseku do pláště
  s přírubou; úseky = půdorys rozvodů minus výřezy (`exterior_views.conduit_runs`). Rozvody nevyřezávají desky ani
  páteř (`roof_hardware` je vynechá). Větrací skříně XK-VENTBOX: na hřbetu místo čtvercového panelu v `sub.vent_bays`
  (ID `-V`), na zádi `F-VENT-AFT` (`on: aft`); staví se jako tři desky (skříň s otvorem, tmavé dno, lamely;
  `vent_entries` v rozvrhu). Hřeben páteře z holého kovu (`cap_material` v kitu → `cap.material` v rozvrhu).
- **Rameno a záď jako desky na rámu** (krok c pilotu, 2. 10. 2026): boční pás může mít `sub` jako hřbet
  (`exterior_model.side_subs`: pás výšek v sekce, panel + poklop, mimo roh s číslem desky; poklop na šikmém rameni
  jako decal paprskem `ray` jako čísla); rozvody po rameni `on: shoulder` (`pipes` s výškou v, `lift` nad pláštěm přes
  desky, `hs_exterior_kit.conduit_side`), rozvody desky nevyřezávají. Zadní stěna = `panels.aft` (obrys půlky stěny
  v pohledu AFT, `cells`, `clear` – decaly, které desky obejdou) + rám `kind: aft` s `members` (`Views.aft_layout`);
  dno kanálu na zádi jen na svislé stěně (`skin_z_max`: na zkosení jsou velké trojúhelníky a plocha přiřazená podle
  středu trčí nad desky). Sekundární lak má vlastní clear coat (`SecondaryClearCoatRoughness` v `M_Ship_Layered`):
  zrcadlící šedé desky četly jako okna.
- **Čísla desek** (pravidlo D-R-PANEL-NUMBERS, `exterior_kit_layout.panel_numbers` → klíč `decals` rozvrhu →
  `hs_decals.build` → `Placer.text`): text složený z jednoznakových položek `pn_<znak>` v jednom rámu (položka na
  číslo se do atlasu 2 m nevešla: „decal sheet full“). Ramena: dolní zadní roh, paprsek šikmo dolů dovnitř (`ray`,
  rameno je skloněné ~45°, `side` by decal zahodil na kontrole normály); hřbet: u zadní hrany mezi pásem panelů
  a poklopů, posune se dopředu mimo výřezy, jinak vynechá.
- **Rozpočet trojúhelníků trupu** (autor 1. 10. 2026, schváleno; `Docs/Reviews/2026-10-01_wayfarer_triangle_budget.md`):
  trup `SM_Ship_<Loď>` ≤ 700 k (varování nad 700 k, chyba nad 1 M = limit exportéru); rozpočet po částech
  v `<Loď>_hs.json` → `budget` (`parts`: jméno, `max`, regulární výrazy jmen zdrojových objektů, první shoda vyhrává,
  zbytek `other` z rezervy). `hs_assemble_ship` vypíše `HSBUDGET` a zapíše `Export/<Loď>_budget.json`,
  `Tools/Tests/test_triangle_budget.py` ho porovná. **Geometrie jen pro velkou a střední vrstvu** (plášť, desky, rám,
  rozvody, skříně, RCS, hydraulika, trysky, podvozek, zbraně); **šrouby, západky, malé poklopy pod 0,4 m, mřížky
  pod 0,3 m a panelové spáry jsou decaly** s normálou a AO z atlasu. Plochy zkopírované z trupu (desky, rám, desky
  detailu) i loft trupu se před solidify a zkosením slučují v rovině (`dissolve_limit` 1°, odděleně podle materiálu;
  `hs_exterior_kit.dissolve_planar`, `hs_build_ship.finish(dissolve=)`); zkosení 1 segment se zpevněnými normálami
  (`harden_normals` + weighted normals), 2 segmenty jen u křivek viditelných z chase kamery (prstence gondol, ústí
  trysek); válce podle průměru 8 / 12 / 16 stěn (pod 50 mm, do 150 mm, nad; `hs_exterior_kit.seg_for`,
  `hs_build_part.cyl`). Spáry loftu pod rámem kitu se nestaví (`hs_exterior_kit.frame_cover` → `loft(covered=)`).
  Hlavní žrout nebyly šrouby (4 %), ale modifikátory na hustých kopiích ploch trupu (rám 16 k → 176 k).
- **Drobný detail kitu jako decaly** (recept `exterior_kit.decal_detail.scope`: seznam ID nebo `"all"`): rozvrh
  označí šrouby `bolts_as: decal` (`bolt_kit`, `bolt_kit_frame` – typ info s vlastní kovovou barvou, strukturní brával
  barvu desky) a poklop XK-HATCH nestaví (deska bez díry, `hatch_small` × 1,3 + dvě `latch_kit`); stavba předá body
  šroubů přes `hs_kit_decals`, `hs_decals` je položí jako rovné čtverce (kontrola hran by je na 25mm pásnici zahodila).
  Decaly kitu (`kit_*`) nedostávají doprovody pravidla „companions“; `kit_check` → `Export/<Loď>_decals.json`,
  `test_kit_decals.py`. Data a výkresy beze změny; poklop jako decal se v testu výkresu počítá jako postavený.
- **Záď z kitu:** rám rampy XK-RAMPFRAME (50 mm, šrouby, styčníky `ramp_gussets`), nášlapné lišty a pryžový práh
  XK-TREAD na dveřích (stojí na desce P-B-07: tloušťka = deska + lišta), pant XK-HINGE, písty XK-PISTON s vidlicovými
  držáky a hadicí (patka na stěně, hlava na čele rámu).
- **Zrcadlové páry** (_L / _R) mají jednu identitu panelu (`hs_assemble_ship`): jinak mohla jedna kopie vyjít jako
  holý kov a symetrické desky četly jako dva materiály.
- **Uplatnění návrhu:** co kit postaví, se odebere z receptu (desky P-B, bloky RCS, které nahrazuje), změny se
  zapíšou do receptu (`"kit"` u funkčního prvku, `"paint2"` u materiálu skříně ploutve, tmavý inkoust nápisů)
  a z `changes` návrhu zmizí; postavené prvky návrhu mají `"status": "built"`. Funkční prvek s klíčem `"kit"`
  `hs_functional` přeskočí.
- **Náhled v Blenderu** (Eevee) ukáže decaly a karty špíny jako bílé plochy (bez textur a průhlednosti): klín
  přes hřbet v náhledu není geometrie. Rozhoduje snímek z Unrealu.
- Livery A (grafitové sedlo nad `TopZ`) je od 1. 10. 2026 vypnutá (`TopZ` 9999): hřbet v primárním laku.

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
  Novou položku stačí přidat do receptu a postavit znovu. **Hotové meshe (loď, kit, interiér) nesou UV atlasu**:
  nové položky vždy s `"append": "<název dávky>"`; `pack` balí dávky v pořadí prvního výskytu za všechno staré,
  takže se žádná stará položka nepohne (ověř diffem indexu: `uv` starých položek beze změny).
- Šablonové nápisy exteriéru (autor 1. 10. 2026): jen u hardwaru, který jmenují (tryska, sání, podvozek, poklop,
  průduch), ne náhodně po ploše (`coverage` a `clusters` bez textu). Položky `xst_*` tmavé pro bílý lak, `xstl_*`
  světlé pro tmavý hřbet, písmo 3,4 cm; průduchy dostávají nápis přes `greeble_companions.vent_stencil`.
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


**Z rozborů lodí SC** (Markom3D, Pisces, 100i, Mustang, Titan; tabulky v archivu skillu):
- Trup bez decalů je skoro hladký; panelové linky, žaluzie, logo a velká čísla jsou decaly na rovném laku.
- Rozdíl ve „feelu“ dělá hlavně **hodnotová stavba a lesk** (30–60 % plochy tmavé, lesklý lak s clear coatem,
  sousední desky se liší tónem a leskem), až potom počet detailů. Livrej a clear coat mají největší efekt.
- Lak bez opotřebení hran; špinavý dojem dělá drsnost, ne barva. `EdgeWear` 0,15, `ClearCoatRoughVariation` 0,12.
- **Karty špíny** `decals.grime` (`Placer.card`, atlas `generate_grime_textures.py`, master `meshdecal_grime`, buňka
  8 cm, měkký okraj přes vertex colour, `up` = odkud špína jde) nad motory, přes křídla a svislé plochy.

**Cílová čísla kokpitu z oka** (medián 5 referencí SC, 1920×1080, `Tools/Blender/eye_view_metrics.py`; oko musí sedět
v pásu skla):

| Veličina | Cíl |
| --- | --- |
| Výhled ven (% plochy) | 62 (53–71) |
| Horní hrana desky (% výšky od spodu) | 35 (30–40) |
| Nejširší sloupek v poli (% šířky) | 0,7 (≤ 2 přijatelné) |
| Sloupek v pásu ±15° kolem pohledu | žádný |

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
cd ArtSource/Ships/<Loď>      # z kořene repozitáře (i ve worktree), kvůli //Export
MSYS_NO_PATHCONV=1 "$BL" -b <Loď>_HS_Game.blend --python-exit-code 1 --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export" --validate-only
MSYS_NO_PATHCONV=1 "$BL" -b <Loď>_HS_Game.blend --python-exit-code 1 --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"
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
- **Po každém `hs_assemble_ship.py` export znovu**, i když se měnil jen interiér: assemble FBX nepřepíše a
  `import_ship.py` by dovezl minulý export (stará podlaha a krabice přes nové díly, WORKFLOW 9.6 eq). Kontrola: čas
  FBX v `Export/`.
- **FBX jen při změně geometrie** (autor 1. 10. 2026; dřív každá přestavba ~250 MB do LFS): exportér spočítá otisk
  souboru (pozice 0,1 mm, UV, normály rohů, materiály, sockety; nezávislý na pořadí trojúhelníků,
  `geometry_digest`) a soubor se stejným otiskem jako v minulém manifestu (`files[].geometry_hash`) nezapíše
  (`EXPORT SKIPPED` ve výpisu). `--all-files` zapíše vše, `--record-hashes` jen doplní otisky do manifestu
  (FBX na disku jsou z tohoto `.blend`). Import přeskočí mesh se stejným otiskem jako při minulém importu
  (`imported_hashes` v `<Loď>_import_report.json`, `kept_unchanged`); `GAMESPACE_SHIP_FORCE_IMPORT=1` importuje vše.
- Hodnoty pawnu z geometrie počítá jen `suggest_pawn_settings()` v exportéru → manifest
  `suggested_pawn_settings` → import. Nepřepočítávat ručně.

## 6. Import do Unrealu (ShipPipeline L2–L3, WORKFLOW 2.2)

```powershell
$env:GAMESPACE_SHIP_MANIFEST = (Resolve-Path "ArtSource\Ships\<Loď>\Export\<Loď>_manifest.json").Path
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py
.\Tools\run_editor_python.ps1 Tools\Assets\build_main_menu.py
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py   # uklidí, co držela úvodní obrazovka
```
Proměnné: `GAMESPACE_SHIP_DRY_RUN=1`, `GAMESPACE_SHIP_APPLY_PLANET=0`, `GAMESPACE_SHIP_SET_GAME_MODE=0`,
`GAMESPACE_SHIP_FORCE_IMPORT=1` (importovat i meshe s nezměněným otiskem).
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
- Chase kamera: manifest navrhuje ~1,8 × délka, v praxi ~1,3 × délka (Wayfarer 2800 cm, SocketOffset.Z 520;
  autor 1. 10. 2026). Při 0,8 × zabíraly ploutve a gondoly celý okraj obrazu, SC ukazuje celou loď na ~40 % šířky.

Textury v UE: `_BC` sRGB on; `_N` Normalmap + **Flip Green on** (Blender/glTF = OpenGL); `_ORM` a `_AO`
Masks, sRGB off. Rozměry mocnina dvou, trup 4096², malé díly 1–2K.

## 7. Testy a snímky

```powershell
.\Tools\Test.ps1                                   # offline (plán importu, export core, decaly, HLSL)
.\Tools\Test.ps1 -UE -Filter *ship_import*
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_displays.py
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_frame.py
python Tools/Tests/test_ship_geometry.py <Loď>     # Blender headless, běží i na konci hs_assemble_ship.py
.\Tools\Shots.ps1 -Preset ship_views -Editor
.\Tools\Shots.ps1 -Preset cockpit -Editor
```
Loď pod testem: `Tools/Tests/ship_under_test.py` (`SHIP = "Wayfarer"`), úvodní obrazovka: `MENU_SHIP` v
`build_main_menu.py` (po přidání dílu ji postav znovu). Kontroly kokpitu a free looku se bez dílu Interior a socketů
Display_ přeskočí.
Po každém kroku lodi doplň `dossier.json` (u modelu klíč `model`: `renders`, `shots`, `known`), ulož rendery do
`ArtSource/Ships/<Loď>/Renders/` (i `silhouette_compare render` masky `model_*.png`), snímky do `Docs/Shots/<Loď>/`
a znovu publikuj Ship Matrix (1b). Když autor najde vizuální chybu, přidej do testu kontrolu, která by ji chytila.
Předání vizuální práce: skill `visual-review`.

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
