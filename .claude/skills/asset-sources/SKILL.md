---
name: asset-sources
description: Where gamespace 3D assets, materials, decals and references come from and the rules for using them - free assets with licence check and Docs/Credits.md, no paid packs, Meshy AI (meshy_generate.py, Kitbash/*.json specs), Scenario MCP (scenario_mcp.py, GPT Image atlases, Polygen retopology, UltraShape), ambientCG/Poly Haven/Quaternius/Sketchfab, Higgsfield, API keys in C:\gamespace\secrets, SC art direction, and the YouTube video reference workflow (fetch_video.py, starcitizenreference/). Load before downloading or generating any asset, texture, decal or concept image, or when choosing between AI, a free kit and procedural geometry.
---

# Zdroje assetů, licence a art direction

Podrobnosti: `Docs/AssetSources_Free.md` (průzkum zdrojů), `Docs/AssetPipeline_Modular.md`
(kdy generovat vcelku, kdy po dílech; srovnání Meshy/Scenario/procedurálně), `Docs/Credits.md`,
WORKFLOW 1.1 (video reference), 3.1b (Scenario MCP), 9.3 x/z/v (nástrahy AI obsahu),
`Docs/Ships/ShipPipeline.md` kap. 2A/2B/4 (Higgsfield a AI model lodi).

## Pravidla (od autora, platí vždy)

1. **Žádné placené balíky.** Zdarma kvalitní assety ano, AI přes autorova předplatná (Meshy,
   Scenario), jinak procedurálně. Nic nekupovat, žádné upgrady tarifu bez autorova souhlasu
   (UltraShape chce Scenario Pro od 45 $/měs. – zatím zamítnuto, Meshy 4k stačí).
2. **Licence kontroluj PŘED stažením.** Povolené: CC0, CC-BY (s kreditem), bezplatné komerční
   licence (Fab Standard License; „jen pro projekty v UE“ je OK – jsme UE). Zakázané:
   non-commercial, editorial only, personal use only, zákaz šíření ve hře – i když se to tváří
   jako „free“.
3. **Každý použitý cizí nebo AI asset = řádek v `Docs/Credits.md`** (CC-BY do tabulky „Ve hře“
   s autorem a zdrojem; CC0 a AI výstupy do tabulky „CC0“ kvůli dohledatelnosti). Zapiš ve stejném
   commitu, kterým asset přibude.
4. **AI po dílech, nikdy „vygeneruj všechno najednou“.** Jednoduchý tvar (trup, sedadlo, jeden
   prop) vcelku; komplexní kompozici (kokpit, místnost s přístroji) rozlož: obálka z AI, přesný
   technický detail procedurálně v Blenderu, složit přes Blender MCP (`AssetPipeline_Modular.md`).
5. **Klíče jen v `C:\gamespace\secrets\`** (`meshy.key`, `scenario.key`), nikdy v repu, logu,
   commitu ani v URL. MCP hlavičky leží v uživatelském `~/.claude.json`, ne v repu.
6. **Žádná jména ze Star Citizenu** (stanice, lodě, firmy, loga) v obsahu ani ve výstupech –
   vzhled ano, značky ne. Naše jména: Halcyon Freightworks, Kestrel Dynamics, Veyra, Steadfast,
   Farsight, Delver (WORKFLOW 9.3 v).
7. **Žádné výplňové rekvizity.** Každý předmět v lodi musí mít účel z 2D návrhu lodi
   (`ArtSource/Ships/<Loď>/Design/`, `<Loď>_layout.json`). Klávesnice u dveří (`Prop_AccessPoint`)
   a procedurální „krabicové“ pulty jsou no-go. Nová loď: nejdřív 2D návrh + spec ve tvaru RSI Ship
   Matrix, 3D až po autorově schválení (HANDOFF bod 73, 75).
8. Cizí materiál s klauzulí „nesmí do AI“ (Stencil Painted Decal Pack, modely Vattalus z Fab/CGTrader)
   **nikdy neposílej do Meshy/Scenario/Higgsfield**. **Snímky ze Star Citizenu** (autorovy screenshoty,
   `starcitizenreference/`) **do AI generátorů jako stylovou referenci posílat smíš** – autor 25. 9. 2026:
   „samozřejmě že se smí posílat snímky ze SC do AI generátoru“. Výstup nesmí nést jména a loga SC (pravidlo 6).

## Art direction: styl SC (platí od 23. 9. 2026)

- **Teplá/neutrální architektura osvětlená světelnými lištami, tmavý základ, studené hologramové UI.**
  Nahrazuje starší „modrou ocel“ (gunmetal `0.35/0.42/0.55`, HANDOFF bod 59) – ta čísla jsou zastaralá.
- Aktuální paleta interiéru (HANDOFF bod 65): neutrální tmavý kov **0,33/0,33/0,34**, pracovní
  světla **5200 K**, svítidla a lišty teplá bílá (`MI_KitStrip`, emise 14). Oranžová akcentů
  `0.85, 0.34, 0.06` (Halcyon Freightworks).
- Cílová čísla proti SC (`python Tools/Shots/measure_look.py`, preset `sc_look`, 1920×1080):
  střední jas 0,08–0,26, p99 0,56–0,88, **B/R 0,72–1,05** (teplé), jemný detail 0,024–0,035.
- Opotřebení skoro jen na hranách, lakované panely v SC jsou téměř čisté (`WearAmount` 0,2,
  `WearEverywhere` 0, HANDOFF 68).
- Reference nálady (lokálně, ne v gitu): `ArtSource/Reference/Mood/sc_cockpit_*.webp`; řezy a
  půdorysy lodí `Docs/UI/reference_tvorba_lodi/`. Každý SC obrázek je jeden koncept jedné lodi –
  nestylizovat podle jednoho dvou obrázků.
- Postup u každého assetu: **zdarma zdroj → AI díl (Meshy/Scenario) → procedurálně**, pak změřit
  proti SC referenci (snímek přes Shots + `measure_look.py`), ne od oka.
- Co u autora prošlo: decaly (šablonové nápisy), osvětlení lištami, hologramy, sedadla z Meshy.
  Co ne: low-poly stěny kitu, procedurální přední pult, klávesnice u dveří.

## Pořadí zdrojů podle typu věci

| Potřebuju | Nejdřív | Pak |
| --- | --- | --- |
| PBR materiál (lak, plechy, rošt, kůže, guma) | ambientCG (CC0) | Poly Haven (CC0) |
| Modulární stěny/chodby | Quaternius MegaKit (CC0, `ArtSource/ThirdParty/Quaternius/`) + `recolour_kit.py` | Infiltrator Demo (Fab, stahuje autor) |
| Hero prop (sedadlo, skříň, boční panel) | Meshy text-to-3D `--refine` | Sketchfab CC-BY (stahuje autor) |
| Malý přesný technický díl (tlačítko, rám, mřížka, kabel, trubka) | procedurálně v Blenderu (bmesh) | – AI tady selhává |
| Nápisy, šablony, štítky, výstrahy | Scenario GPT Image (atlas v mřížce) nebo `Tools/Assets/generate_decals.py` | Yughues decals (CC-BY) |
| Obsah obrazovek/HUD | `Tools/Assets/draw_holo_screens.py` (naše písma) | Scenario |
| Trup lodi | Higgsfield multi-image nebo Meshy, pak `build_ai_ship.py` | – |
| Průmyslové fotoskeny (sudy, ventily) | Poly Haven modely (`fetch_polyhaven.py --models`) | – |

## Materiály: ambientCG a Poly Haven

- ambientCG API bez klíče:
  `https://ambientcg.com/api/v2/full_json?q=<dotaz>&type=Material&include=downloadData` (1K–8K).
  Staženo v `ArtSource/Textures/ambientCG/` (2K: PaintedMetal004, PaintedMetal013, MetalPlates006,
  Leather033A, Rubber004). Importuje `Tools/Assets/import_interior.py` (`SURFACES`,
  `/Game/Environments/Steadfast/Surfaces`); `M_KitTrim` z nich vrství opotřebení, špínu a podlahové
  desky triplanárně (UV kitu nevadí). Kandidáti na další: PaintedMetal006/016, MetalPlates008/017B,
  MetalWalkway010/014, Grate001/002, Leather037, Fabric061, Metal032, Metal049A.
  Samostatný `fetch_ambientcg.py` zatím **neexistuje** – když ho píšeš, vzor je `fetch_polyhaven.py`.
- Poly Haven: `python Tools/Assets/fetch_polyhaven.py [asset ...]` / `--models [asset ...]`
  → `ArtSource/Textures/PolyHaven/<asset>/` (2K diffuse, normal GL, ARM, `means.json`). API bez klíče,
  posílat vlastní User-Agent. Blender MCP má i `download_polyhaven_asset`.
- Nový materiál skriptem (WORKFLOW 9.3 f): šedá šachovnice v zabalené hře = chybí usage flagy
  (`used_with_nanite`, `used_with_static_mesh`, `used_with_instanced_static_meshes`) nebo sampler
  Normal/Linear bez výchozí textury správného typu. Hledej „Failed to compile Material“ v cook logu.
- Ladění vrstev za běhu: `space.Kit WearAmount / WearEverywhere / GrimeAmount / FloorPlates`.

## Meshy AI (text-to-3D)

```
# PowerShell: klíč jen do proměnné prostředí, ze souboru mimo repo
$env:MESHY_API_KEY = (Get-Content C:\gamespace\secrets\meshy.key -Raw).Trim()
python Tools/Assets/meshy_generate.py --spec <parts.json> --out <složka> --dry-run   # jen vypíše prompty, nic nevolá
python Tools/Assets/meshy_generate.py --spec <parts.json> --out <složka> <Díl>       # jeden díl ze spec
python Tools/Assets/meshy_generate.py --spec ArtSource/Ships/Steadfast/Kitbash/meshy_parts.json --out ArtSource/Ships/Steadfast/Kitbash/Meshy --refine
```

- Skript čte **jen `MESHY_API_KEY`**; soubor `meshy.key` sám neotevře.
- Spec JSON: `style` (přidá se ke každému promptu) + `parts[]` s `name`, `prompt`, `size_cm`,
  volitelně `target_polycount`. `--spec` a `--out` jsou povinné (výchozí spec není), cesty jsou
  relativně ke kořeni repa. Vzor: `ArtSource/Ships/Steadfast/Kitbash/meshy_parts.json` → výstup
  `ArtSource/Ships/Steadfast/Kitbash/Meshy/`. Výstup GLB + `meshy_report.json`.
- Přepínače: `--refine` (PBR textury 2K, druhý běh), `--hi` (`geometry_resolution` 4k,
  30 000 tris – rovná deska, ostré šrouby, čitelné přepínače; 25 kreditů místo 20), `--dry-run`.
- Ceny: preview ~20 kreditů/díl (~1 min); Steadfast díly s refine 10 kreditů/díl (HANDOFF 68).
- **Umí:** samostatné předměty – sedadlo (`PilotSeat` výborné), boční panel, skříň, panelové díly
  s ovladači. **Neumí:** přesný tvar na míru, symetrii, modulární díly na mřížku, tenké protáhlé věci
  (kabely → „chobotnice“). Zadání „pult do kokpitu“ vrátí celou kabinu (WORKFLOW 9.3 x).
- Meshy vrací normalizovaný model: měřítko srovnává import podle `size_cm`; Meshy kouká do −Y
  → v UE otočení −90° (`place_props` v `import_interior.py`, `MESHY_PROPS` ve staviteli).
- Každý díl si **před zapojením prohlédni ze tří stran** (render kamerou do souboru v Blenderu;
  `get_viewport_screenshot` je u malých dílů k ničemu). Co nesedí, zahoď nebo použij jinde.
- Meshy Retexture (prompt) mění jen materiál existující geometrie – vhodné na restylizaci
  staženého kitu.
- Na placeném plánu výstup patří autorovi → do Credits jako „vygenerováno, Meshy AI“.

## Scenario (MCP server + `scenario_mcp.py`)

- Registrace (hotová, scope *local* pro `C:\gamespace\gamespace` – session spuštěná v
  `C:\gamespace` nástroje `mcp__scenario__*` nedostane):
  `claude mcp add --transport http scenario https://mcp.scenario.com/mcp --header "Authorization: Basic <base64 klíč:secret>"`
  Auth = Basic `API key:API secret` v Base64 (samotný klíč nestačí). Nástroje se načtou až po
  restartu session; `claude mcp list` → `✓ Connected`.
- CLI klient (funguje i bez MCP nástrojů v session):
  ```
  python Tools/Assets/scenario_mcp.py tools
  python Tools/Assets/scenario_mcp.py upload <soubor> [kind]           # -> asset id
  python Tools/Assets/scenario_mcp.py run <modelId> '<json args>'      # čeká a stáhne
  python Tools/Assets/scenario_mcp.py get <assetId> <výstupní soubor>
  ```
  Klíč čte z `C:/gamespace/secrets/scenario.key` (jeden řádek `klíč:secret`). Upload jde přes MCP
  (dokončovací krok vícedílného uploadu není v REST dokumentaci), běhy přes REST
  `POST /v1/generate/custom/<modelId>`, `GET /v1/jobs/<id>`.
- Upload přes MCP nástroje ručně: `upload_asset` (s `file_size`, bez `data`) → `PUT` syrových bajtů
  na každé `parts[].upload_url` (**bez** `x-amz-checksum-*` hlaviček) → `upload_asset_complete`
  s `upload_id`.
- Tarif `cu-basic`: `accessRestrictions` 0 = dostupné, 50 = Pro. Užitečné modely:
  - `model_tencent-smarttopology` (Hunyuan Polygen 1.5) – AI retopologie, drží ostré hrany líp než
    decimace (28 624 → 3 131 tris, 113 CU, ~20 min; `progress` visí na 10 %, živost poznáš z `updatedAt`);
  - `model_tencent-uv-unwrapping` (auto UV do 30k ploch), `model_hunyuan-3d-part` (dělení na díly),
    `model_tripo-v3-0-texturing` (PBR na hotový mesh);
  - `model_tripo-v3-1-image-to-3d` – na šedém clay renderu **selhal** (díry, přepálená textura, 75 CU);
    případně znovu jen s barevným konceptem a vypnutým `smartLowPoly`;
  - `model_ultrashape-1-0` (`3d23d`, chce `image` **i** `model`, `octreeResolution` 128–1024) – jen Pro,
    `model_run` i `dry_run` vrací 403 `ModelAccessRestrictedError`. Vstupy už nahrané
    (`asset_rmnHbeqKqDFkHQGpGqtpGEeL` obrázek, `asset_ep4gbRYJxXJqvkDhuGmGkMpr` mesh).
  - **GPT Image 2.5** – text v obrázku píše přesně (atlas 16 nápisů, 12 CU). Zadávej pevnou mřížku:
    „exact 4 by 4 grid, one element centered in each cell, black background“ → políčka se vyříznou
    výpočtem. Výsledek: `ArtSource/Ships/Steadfast/Interior/Decals/`, v UE `M_Decal` + `MI_Decal_NN`
    (`CellU`/`CellV`), rozmístění `DECALS` → `Interior_layout.json` → `place_decals`. Decal na stěně
    roll +90° (−90° = vzhůru nohama), na podlaze pitch −90° (HANDOFF 69).
- Dělba práce: geometrii generovat v Meshy (4k), Scenario na kroky za tím (retopologie, UV, díly,
  textury) a na 2D obsah (nápisy, obrazovky, bezešvé textury). PBR mapy ze Scenaria jsou odvozené
  z barvy – na realistický kov je lepší ambientCG.

## Higgsfield (koncept lodi → 3D)

- `ShipPipeline.md` kap. 2A/2B: **2–4 konzistentní pohledy** (bok, zepředu, shora, 3/4),
  neutrální pozadí, rovnoměrné světlo, celá loď v záběru, bez motion blur a dramatických stínů.
  Z jednoho obrázku si AI záda a spodek vymyslí.
- Multi-image to 3D: topology triangle 200–300 tis. (`HIGH_`), **PBR mapy zapnout** (jinak zapečené
  světlo), volitelně druhý běh quad ~30 tis. Rigging ne.
- Surový GLB do `ArtSource/Ships/<Loď>/Higgsfield/` a **nikdy needitovat**. Koncepty + `prompt.txt` do `ArtSource/Ships/<Loď>/Concept/`
  (složka zatím neexistuje, vytvoř ji).
- Dál `Tools/Blender/build_ai_ship.py` s receptem `<Loď>_ai_build.json` (WORKFLOW 2.1, ShipPipeline 2B).
- Licenci výstupů Higgsfieldu pro komerční použití ověř, než loď půjde do vydané hry; zapiš do Credits.
- Higgsfield MCP (`claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp`) je zapojený
  (tarif plus, ~1000 kreditů; GPT Image 2.5 high 2k = 2,75 kr., Nano Banana Pro 2k = 2 kr.). Generování
  a ověření konzistentních pohledů lodi: skill `ship-pipeline` sekce 2a (vodicí silueta jako druhá
  reference, `silhouette_compare.py views`). Nahrávání: `media_upload` → `curl -X PUT` → `media_confirm`.

## Hotové modely zdarma

- **Quaternius** Modular Sci-Fi MegaKit (CC0, 190 modelů, `ArtSource/ThirdParty/Quaternius/README.md`):
  akcent je jen v emisivní mapě → `Tools/Blender/recolour_kit.py` z ní dělá svítící pásy.
  Pozor: `recolour_kit.py` tónuje do staré modré oceli – před dalším použitím sjednoť s paletou výše.
  Kit je na blízký pohled hráče low-poly (HANDOFF 73).
- **Sketchfab** (většinou CC-BY, stahování s účtem → stahuje autor): 71 kandidátů s licencí,
  autorem a počtem ploch v `ArtSource/Ships/Steadfast/Kitbash/free_asset_survey.json`. U každého
  zkontroluj odznak licence na stránce. Blender MCP má `search_sketchfab_models`.
- **Fab** Limited-Time Free (3 assety / 2 týdny, zůstanou navždy) a **Infiltrator Demo** (UE 4.9,
  nutná migrace) – stahuje autor přes svůj účet.
- **NASA 3D Resources** (bez autorských práv, bez log NASA) na detaily.
- Megascans už zdarma nejsou. Hyper3D Rodin přes Blender MCP: zkušební klíč vyčerpaný
  (`API_INSUFFICIENT_FUNDS`); Hunyuan3D v Blender MCP vypnutý, chce vlastní klíč.
- Stahování s přihlášením (itch, Fab, Sketchfab) dělá autor – napiš mu přesný odkaz a kam soubor
  uložit.

## Vložení cizí geometrie – nástrahy (WORKFLOW 9.3)

- **k)** Průchod v cizím kitu má za stěnou další stěnu; před řezem vypiš plochy v objemu po
  materiálu a normále, mazej jen svislé.
- **n)** Rám dveří z kitu má průchod jen ~70 % výšky – měř otvor z vrcholů, ne bounding box.
- **p)** Blikání = dvě plochy v jedné rovině (díl v kitu dvakrát); najdi `flicker_check`, maž jen
  skutečné kopie se stejným obrysem (ne „všechno, co se překrývá“ – dlaždice podlahy se překrývají).
- **u)** Průsvitné/aditivní materiály nesmí na Nanite mesh – sklo a hologramy jako vlastní GLB.
- **y)** Opotřebení podle normálové mapy funguje jen na kitu, ne na procedurálních dílech.
- **aa)** Jméno materiálu rozhoduje o vzhledu v UE (`import_interior.py`: „black“, „lamp“,
  „light“/„screen“ = svítící pás, „glass“, „m_holo_“, „white“, „strip“) – pojmenuj nový materiál tak,
  aby nechtěně nesvítil.

## Video reference (WORKFLOW 1.1) a `starcitizenreference/`

- `starcitizenreference/` je **hlavní designová reference** (letový systém, prostředí, planety,
  quantum, plán knihovny `Gamespace_ReferenceLibrary_Plan.md`). Vizuální cíl je 1:1 SC; odchylku,
  kterou nejde odstranit, pojmenuj v odpovědi autorovi.
- Každá nová funkce/vzhled začíná referenčním videem (když URL chybí, řekni si o ni autorovi,
  nebo použij existující poznámky):
  ```
  python Tools/Reference/fetch_video.py <url> <název> [--every 2] [--from 3:40 --to 5:10]
  ```
  yt-dlp (`pip install yt-dlp`) stáhne nejlepší kvalitu do 4K, vypíše skutečné rozlišení (ffprobe –
  YouTube někdy potichu pošle nižší), nařeže snímky `tHH_MM_SS.jpg` a složí přehledové listy 4×3.
  Potřebuje ffmpeg/ffprobe na PATH. Opakované spuštění stahování přeskočí.
- Postup: projít listy → zajímavé časy v plném rozlišení / výřez HUD → poznatky **vlastními slovy**
  s časy jako odkazy do `starcitizenreference/<Téma>_VideoNotes.md`.
- Video a snímky jsou cizí záznam: jen v `ArtSource/Reference/Video/` (v `.gitignore`), nikdy do
  commitu. Jako stylová reference pro AI koncepty poslat smíš (pravidlo 8).
