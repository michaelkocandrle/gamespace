# Archiv skillu `ship-interior` (přesunuto 30. 9. 2026)

Doslovně přesunuté oddíly z `.claude/skills/ship-interior/SKILL.md` (commit 44c26cc): stav a historie jednotlivých
kroků, výsledky kol kritika, měření a popisy postavených dílů. Pravidla, postupy a nástrahy zůstaly ve skillu
(zkráceně), stabilní pravidla kitu v `.claude/skills/ship-interior/kit-design.md`. Archiv není zdroj aktuálního
stavu (hierarchie v `CLAUDE.md`).

## Úvod skillu: stav k 24.–25. 9. 2026, Wayfarer v1/v2 (hs_interior)

Stav k 24. 9. 2026: interiér Steadfastu (strojovna | nákladový prostor | chodba | dveře | kokpit)
je průchozí, stojí v `TestSpace` 500 m stranou od lodi, bez vnějšího trupu. **Autor ho ohodnotil
jako nedostatečný a nový Steadfast se staví podle 2D návrhu** (HANDOFF bod 73–75). Stávající
skripty jsou pracovní pipeline a zdroj ověřených postupů, ne cílový vzhled.

**Wayfarer (25. 9. 2026): interiér uvnitř létajícího trupu**, jiná cesta než Steadfast:
- `Tools/Blender/hs_interior.py` volá `hs_build_ship.py` po rozdělení kabiny. Recept `interior` v
  `ArtSource/Ships/Wayfarer/HardSurface/Wayfarer_hs.json` (`height_m`, `sill_z`, `lights`, `seat`).
  Místnosti a předměty bere z `Design/Wayfarer_layout.json`; předmět se pozná podle klíčového slova
  v českém názvu (`Hydraulika`, `Reaktor`, `Lůžko`, `Přístrojová`, `křeslo`…). Neznámý se přeskočí.
- Výstup: part `Interior` (bez Nanite a kolize) a `Screens` (canvas 1330×490, 4 obdélníky `RECTS`), sockety
  `Display_*`, světla do `Wayfarer_lights.json`. Materiály `MI_Ship_Wayfarer_Int*` jsou na vrstveném masteru.
- Snímky `Tools/Shots/wayfarer_interior.json` (`camera_local` / `look_local` v prostoru lodi, m).
- Cíl jasu jako výše (průměr 0,13–0,23, B/R 0,72–1,05). Bodovky 20 cd na 2,3 m vysokou místnost.
- **v2 (pilot chodby a kokpitu, 25. 9. 2026): kit jako nosná vrstva** (`Tools/Blender/hs_interior_kit.py`,
  recept `interior.kit`): `rooms` (které místnosti), `walls` (dvojice stěna + horní díl na modul, levobok a
  pravobok), `floor`, `ceiling`, `chamfer_deg`, `cove_m`, `spot_cd`, `cove_cd`, `portal_w/d`, `fittings`
  (extinguisher, handrail, vent, junction, conduit). Měřítko kitu se počítá z výšky: stěna 3 + skloněný
  horní díl 2 kit m končí rýhu pod stropem (0,47 u 2,3 m). Kit se čte přímo ze zipu.
- Procedurální díly v kit materiálu: `kit_box` / `kit_obox` (kubické UV), `tbox` v hs_interior.
- Materiály kitu: `kit_trim01/02/02b/03`, `kit_cables`, `kit_padded(_grey)` → MI na `M_Ship_PBR` s texturami
  z `ArtSource/Ships/Shared/Kit/` (`tone_kit_textures.py`), tón přes `base_color_tint`.
- Decaly interiéru: `generate_interior_decals.py` → `D_Int_*`, v setupu `Int_*` (rotace viz WORKFLOW 9.6 be).
- Iterace: `hs_interior_preview.py` (Eevee ze stejných kamer, `world=`, `light=`, `exposure=`); Eevee bez GI
  stěny podsvítí jinak než Lumen, konečné posouzení jen ze zabalené hry.
- **Kokpit Wayfareru (koncept A, 25. 9. 2026):** recept `interior.cockpit` (`style: wrap`, `pod_x/y/z`,
  `screen_w`, `side_margin`, `top_margin`, `wing`, `centre_x`, `centre_top_z`, `fascia_*`, `seam_x`,
  `pinstripe_inset_m`, `frame_wash_cd`) → `Tools/Blender/hs_cockpit.py` (`build_wrap`: deska, křídla, sloupek
  s radarem, pod deskou). Náhled z oka: `hs_interior_preview.py ... eye=1`. Cíl: `Concept/Cockpit/cockpit_target_*.png`.
- **Decaly interiéru jako mesh decaly:** `interior.decals` → `hs_interior_decals.py` (Placer z `hs_decals`,
  položky knihovny, `items` paprskem, `scatter` mřížkou paprsků ke stěnám, `grab_bars`), part `InteriorDecals`.

## Kajuta Wayfareru z kitu (30. 9. 2026, z oddílu „Průchozí loď“)

- Kajuta Wayfareru z kitu (30. 9. 2026, varianta B): obložení na ±1,9 m, čela `Bulkhead_Door00L38_A` (vzadu) a `_F`
  (vpředu, průchod až ke stropu nad schody – nadpraží ve 2,05 m bralo hlavu), poslední modul u kokpitu `06L_D`
  (plochý sokl: trup je tam u podlahy 4,5 cm za lícem, WORKFLOW el). Světla místnosti tlumí
  `kit_modules.light_scale` (kajuta 0,6, WORKFLOW em). Nábytek zůstává lodní (`keep`), posunutý před žebra a pod
  zkosení; hygienická buňka má boky podle profilu obložení (`obj_hygiene(liner=)`).

## Dosažené hodnoty měření (z oddílu „Snímky a měření“)

**Cílové rozsahy SC (interiér, auto expozice):** průměr 0,13–0,23, p50 0,08–0,18, p90 0,32–0,53,
p99 0,56–0,88, **B/R 0,72–1,05** (teplé), detail 0,024–0,035. Dosaženo: prostor/chodba/strojovna
B/R 0,70–0,77, p99 0,72–0,96. Blikání < 0,1 % pixelů. Interiér ~70 FPS ve 1080p (epická, TSR 75 %).
Snímky porovnávej listem vedle sebe (PIL ve scratchpadu) proti `ArtSource/Reference/Mood/sc_cockpit_*.webp`.

## Stavba kitu po dávkách, materiál, špína, místnosti v lodi, výklenky (27.–29. 9. 2026)

## Interiérový kit: stavba dílů a ukázka v enginu (krok 4, dávka 1, 27. 9. 2026)

Pipeline (vše skriptem, rychlá smyčka bez balení, dokud se ladí tvar v Blenderu):
```bash
python Tools/Kit/kit_trim_sheet.py          # trim sheet 4096x2048 @ 1024 px/m -> ArtSource/Kit/Textures (+ trim_index.json)
python Tools/Kit/kit_screens.py             # atlas obrazovek displejů (T_Kit_Screens.png, M_Ship_Screen)
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup     --python Tools/Kit/kit_build.py -- walls [--sections W,N] [--no-render]
python Tools/Kit/kit_catalog.py 1           # katalogový list Docs/Kit/catalog_batch1.png
```
```powershell
.\Tools\run_editor_python.ps1 Tools\Assets\import_kit.py           # /Game/Kit + ukázková chodba v TestSpace
.\Tools\Shots.ps1 -Preset kit_showroom -Package -Width 1920 -Height 1080
```
- **Soubory:**
  - `Tools/Kit/kit_geo.py`: třída `Part`. Geometrie po rolích materiálů, zkosené boxy a desky, lisovaný panel
    (`inset`), trubky, UV (trim pruhy podle lokálních os, atlas obrazovek, metry), UV1 = náhodné ID panelu,
    barva vrcholů `Col` pro vrstvený master, UCX a SOCKET_.
  - `Tools/Kit/kit_walls.py`: stěnové moduly (plášť + 6 typů × A–C).
  - `Tools/Kit/kit_build.py`: stavba, decaly přes `hs_decals.Placer`, export FBX, manifest, rendery.
- **Výstupy:**
  - `ArtSource/Kit/Kit_Walls.blend`;
  - `ArtSource/Kit/Export/SM_Kit_*.fbx`;
  - `kit_manifest.json` (rozměry, trojúhelníky proti rozpočtu, materiály, sockety v UE cm s parametry světel, kolize);
  - rendery `Saved/KitCatalog/`.
- **Plášť stěny** (každý modul):
  - tmavá výplň za panely (vidět ve spárách);
  - zapuštěný sokl s modrou lištou a gumovou hranou;
  - spodní panel v sekundárním tónu s kartáčovaným kopacím plechem;
  - lisovaný hlavní panel;
  - oranžová signální linka ve žlábku pod šroubovanou madlovou lištou (trim `rail_bolted`);
  - sklon ze dvou lisovaných panelů se šroubovanou přírubou;
  - vybrání s okrajem, římsou, čelem a teplou lištou;
  - poloviční kryty spojů na koncích modulu (sousedé z nich složí jeden kryt);
  - konstrukční rám na každém spoji (`Wall.ribs`): polovina 6,5 cm na každém konci modulu, dohromady 13 cm s plochým
    lícem 9 cm, 8,5 cm před panely, zkosení k panelům, čisté koleno mezi svislou částí a sklonem, šrouby po 0,3 m.
    (Dvě zaoblené poloviny po 3 cm četl kritik jako „svislé trubky“ a spoje jako „tenké spáry“.) Výbava musí
    nechat 6,5 cm u konců modulu volné (skříňky 0,46 m, displej 0,4 m, poklop A 0,38 m);
  - otevřený kabelový žlab pod vybráním (deska 4 cm od sklonu na žebírkách, lem, 3 černé kabely a krémový);
  - hlavní panel rozdělený v 0,86 m (`Wall.split`), horní deska 12 mm vpředu (stínová spára, přesah); vlastní
    `main_split` to vypne (skříňky, Plain B/C, kanál trubek);
  - na horním sklonu kabelové kanály (`Wall.conduits`): vzor podle jména dílu (žádný 20 %, jeden, dvojice, dvojice se
    zanořením do panelu přes průchodku), 1–3 příchytky na volných místech (třmen nebo pásek). Stejné kanály na každém
    modulu dělaly rastr (ověřovací kolo);
  - konzole vybrání nad každým spojem (schová konce lišt; samostatné koncovky četl kritik jako „schody“);
  - rámy bez zkosení: zkosení 5 mm rozdělí hrany profilu pod 40° a hladké stínování udělá z rámu kulatý sloup;
  - lišty jako svítidla: kovový profil s lemy, koncovky a difuzor (u podlahy, nahoře ve vybrání i pod hranou vybrání);
  - světla: jedno lineární (rect) světlo na lištu a modul (`Wall.strip_light`, socket `type="rect"` s `width_cm`,
    `height_cm`, `dir_ue`): sokl studené 0,25 cd/m, dosah 0,7 m; vybrání nahoru teplé 0,8 cd/m, 1,1 m; pod hranou
    vybrání dolů-ven teplé 1,1 cd/m, 2,4 m (osvětluje sklon a protější stěnu). Body po 0,6 m pálily skvrny;
  - `Snap_Start/End`, dvě UCX (stěna, sklon s vybráním).
- **Výbava podle kola 1 kritika (27. 9. 2026):**
  - skříňky mají korpus s ohybem hran, zvýšený rám, dveře 12 mm v rámu přes tmavou spáru, panty, větrací štěrbiny;
    stohované se liší (páka západky vs. zapuštěné madlo a zámek), bedna má rychlouzávěry a boční madla;
  - poklop má zvýšený rám, 4 rychlouzávěry Ø 28 mm, panty, výstražný pás jen nad rámem;
  - trubky vycházejí ze stěny a vracejí se do ní obloukem s průchodkou uvnitř modulu, nikdy nekončí
    na hranici modulu (trasy přes víc modulů = mosty v dávce 7);
  - displej má krycí sklo a klávesy v tmavých jamkách;
  - štítky (`kit_rules.decal_rules`): servisní štítek (`st_*`, `label_*`) jen u hardwaru, který pojmenovává (poklop A
    SERVICE ACCESS, poklop B INSPECT, poklop C systémy, mřížka VENT hned u mřížky, dublovací plech TORQUE, trubky
    svůj systém); plná stěna nenese žádný. Nikdy stejný štítek na sousedních modulech layoutu: kontroluje
    `import_kit.check_layout_labels` (import spadne) a `test_kit_showroom.py`; manifest má `service_labels` dílu.
    Čísla panelů jsou čísla dílu (stejný díl = stejné číslo). Štítek leží celý na okraji prolisu nebo celý
    v prohlubni (WORKFLOW cm);
  - oděr hran: `kit_geo` dává barvě rohů G = 0 plochám z bevelu (`Part.edge_faces`), master pak ošoupe jen zkosení
    (EdgeWear lak 0,3, konstrukce 0,5). Maska po vrcholech nejde: skoro každý vrchol dílu leží na hraně.
    Barva `Col` je v doméně rohů; `kit_build.join()` převede bodovou `Col` decalů taky na rohy
    (`to_corner_colour`), jinak by masky dílu přepsala a UE by bílou barvu zahodil (WORKFLOW cq). Export
    `colors_type="LINEAR"`. `kit_build` spadne, když masky nepřežijí (`colour_masks` v manifestu);
  - gumové těsnění 6 mm uvnitř rámu poklopů a mřížek (`_gasket`).
- **UE (`Tools/Assets/import_kit.py`):**
  - Díly jdou do `/Game/Kit/Meshes` přes funkce `import_ship` (FBX, velikost, sloty, kolize, sockety), bez Nanite, kolize simple-as-complex.
  - Staré meshe se před importem mažou (reimport držel staré sockety).
  - `MI_Kit_Halcyon_<Role>` v `/Game/Kit/Materials` na masterech lodí:
    - layered pro Primary, Structure a Accent: Primary 0,1/0,095/0,088, **PaintMetallic 0,1** (lak je dielektrikum,
      při 0,45 ztratil půl difuzního světla a stěny zčernaly), grunge 0,3, variace drsnosti 0,28, špína 0,35 (vertex R
      klesá u podlahy ve spodních 0,5 m); Structure 80 % palety (0,26), metallic 0,4, drsnost 0,36 (čistý kov 1,0
      zrcadlil tmavou místnost a rám zmizel); Accent 70 % palety, drsnost 0,56; Signal 80 % palety, drsnost 0,5;
      bez oděru hran (SC lak ho nemá); teplá světla (255, 228, 200), `Kit_GlowWarm` 1/0,9/0,78 (B/R 0,58 → 0,72);
    - hull pro Signal, Rubber, Seal, Plastic a svítivé materiály;
    - pbr pro Trim;
    - screen pro displeje;
    - decaly zatím přes instance Wayfareru (sdílený atlas).
  - **Ukázka:** `TestSpace` na (0, −500, 0) m, chodba W 8,4 m, světlo u každého socketu, tmavý box proti slunci.
    Podlaha, strop, konce a stropní světla jsou provizorní (drsný `MI_Kit_Halcyon_ProvFloor`, bodovky 45 cd / 90° na
    0,22/0,5/0,78 délky, výplň 8 cd 80 cm pod stropem, WORKFLOW cn). Tag `KitShowroom`, přestavuje se při každém běhu.
- **Výkon ukázky:** GPU 15,8–17 ms ve 1080p (~59–63 FPS), z toho `Lights` 3,4–3,9 ms (60 lineárních světel + displej
  + 6 provizorních). Body místo lineárních světel stály 2,7 ms, ale pálily skvrny a stěny nechaly černé.
- **Procházení ukázky:** klávesa **U** nebo `space.Showroom` (`ASpacePlayerController::ToggleInteriorAt`, tag
  `KitShowroomSpawn`), zpět stejně. Import staví gravitační objem (tag `KitShowroom`) a startovní bod; tmavý box
  proti slunci je bez kolize (hráč by v něm uvízl).
- **Ladění ukázky za běhu:** `space.KitLight Showroom <Vlastnost> <hodnota>` (i rect světla, např. `CastShadows 1`),
  `space.KitColor PrimaryColor r g b Structure` (materiály ukázky), `space.KitReset`.
- **MegaLights** (`kit_megalights.json`, `kit_megalights_perf.json`, list `Docs/Kit/megalights_compare.png`): bez stínů
  +0,1 ms a stejný obraz, s ray-traced stíny ze všech 67 světel +1,0 ms a kontaktní stíny. VRAM +0,1 GB. První
  zapnutí stínů za běhu dá záškub 140 ms. Rozhodnutí autora čeká (doplněk ve studii světel 26. 9.).
- **Test:** `Tools/Tests/test_kit_showroom.py` (barvy vrcholů přes export z UE, štítky sousedů, gravitace, start,
  kolize boxu).
- **Měření vzhledu** (`measure_look.py`, auto expozice): chodba průměr 0,21, p90 0,35, B/R 0,71, detail 0,025 = v rozsahu
  SC. Kolo 2 (lak metallic 0,45, body, úzké bodovky) mělo 0,14 / 0,27 / 0,58 / 0,024 a stěny 0,06–0,10.

## Interiérový kit, dávka 2: portály, strop, koncové stěny, rohy, přechod (27. 9. 2026)

`Tools/Kit/kit_batch2.py`, stavba `kit_build.py -- batch2` (výstup `ArtSource/Kit/Kit_Batch2.blend`, katalog
`python Tools/Kit/kit_catalog.py 2` → `Docs/Kit/catalog_batch2.png`). `kit_build.jobs()` drží seznam úloh všech
dávek (díl, rozpočet, pohledy renderů); `--only <jména>` postaví vybrané díly.

- **Pivoty:** portál, strop a přechod na ose chodby na začátku modulu (+X podél chodby); koncová stěna a zúžení
  jako stěna (líc +X, šířka podél +Y); roh v bodě, kde se potkají roviny líců.
- **`Section`:** rozměry průřezu z `kit_rules`, `inner(d)` = vnitřní obrys odsazený o d (noha, sklon 3:4, strop;
  vybrání leží uvnitř odsazené čáry sklonu). `ceil_half` = polovina stropu mezi čely vybrání + 2 cm.
- **Portál (0,3 m):**
  - tmavý límec 3,5 cm od stěn přes celou hloubku;
  - rám vystupuje o `portal_protrusion`, zkosené hrany (nesou oděr), šrouby na obou lících, styčníky
    v kolenech, patky se šrouby;
  - každý rám nese jedno číslo na levé noze (tmavá destička 0,98–1,14 m, svislé čelo nohy končí u zlomu 1,27 m;
    F02/G08/H19, v N C21) a socket `SOCKET_Decal_Section` pro číslování přes rozvržení (dávka 6);
  - A: světelný prstenec jen přes zkosení a hlavu, difuzor v drážce mezi lemy s krytkami, lineární světlo pod hlavou;
  - B: šrafovaný výstražný pás 0,3–0,9 m na obou nohách;
  - C: těžší rám s vnitřním žebrem, hlavou prochází kanál a trubka stropního pole B (příruby se šrouby na obou lících).
  Vnější obdélník (0,2 m do stěny, 0,25 m nad strop) je skrytý, na katalogu vypadá jako deska.
- **Strop:**
  - panely: tmavá výplň, tři lisované pásy, poloviční příčné nosníky na koncích (rytmus rámů přes strop).
    A = zapuštěná čtvercová bodovka (lem, tmavá šachta, čočka, dvě lamely; spot 35 cd, 0,6 m 22 cd, 0,3 m je výplň),
    B = vyústění vzduchu jako mřížka z lamel (perforovaná plocha zdálky četla jako černá díra), C = zapuštěné lineární
    svítidlo s příčnými lamelami po 8 cm;
  - otevřené pole: dno 20 cm nad stropem v tmavé primární barvě (ne černé), příčné nosníky, studený servisní pásek,
    zavěšené lineární svítidlo s lemy a lamelami; A = žlab se svazky kabelů, B = kanál a potrubí s barevným kódem;
  - teplé svítící plochy (`Kit_GlowWarm`) mají emisi 7: při 14 byly difuzory ořezaná bílá deska, čitelnost dělají
    lamely, ne nižší emise;
  - světla ve stropě nejvýš ~1,8 m od sebe, jinak vzniknou tmavá místa.
- **Koncová stěna:** obrys průřezu včetně vybrání, tři pole mezi rámy až ke stropu, sokl, kopací panel a lišta
  pokračují ze stěn, hlavový nosník. B má okno pod lištou: rám ve dvou stupních s těsněním, sklo, ostění 14 cm,
  za ním zavřená roleta z tmavých lamel, v nadpraží tlumené neutrální světlo, stavová LED; tmavá zadní deska 20 cm
  za lícem (v 7 cm zakryla ostění). Výhled ven v ukázce není (kritik ho chce, otevřené pro autora).
  Zúžení W→S = koncová stěna s obrysem průlezu S, rámem, výstražným pásem, SERVICE ACCESS a 0,6 m průlezu.
- **Přechod N→W (0,6 m):** obě stěny rozevřené pod 45° v půdorysu, profil lofovaný mezi průřezy (`Part.quads`),
  lišta sleduje klesající zlom, lem a pás vybrání ve stálé výšce 2,1 m, šroubované žebro uprostřed každé šikmé stěny.
  Kritik chce víc (těžký rám portálu N, funkční shluk, sloupek na zlomu) – otevřené.
- **Rohy:**
  - vnitřní roh nepotřebuje poloviny stěn: dva stěnové moduly začínající v rohu se svými sklony protnou do
    úžlabí samy (viditelný je nižší sklon). Díl jen zakryje spoj: A sloupek se zkosenou hranou do místnosti, patkou
    a gumovým chráničem 0,15–1,0 m + nosník v úžlabí + konzole vybrání, B zkosený panel 45° pod zlomem;
  - vnější roh vyplní kvadrant nad zlomem: dvě trojúhelníkové plochy v rovinách sklonů (nároží), nárazník
    přes svislou hranu, gumový nárazník 0,15–1,05 m s výstražným šrafováním na obou čelech, hřebenový nosník,
    vybrání otočené kolem rohu.
- **Decaly dílů:** `label(p, item, bod, normála, xdir, ydir)` – `xdir × ydir` musí být normála plochy, jinak
  `KITBUILD` hlásí „mirrored frame“ (dřív decal tiše ležel rubem, WORKFLOW ct).
- **Trim kitu** (`MI_Kit_*_Trim` na `M_Ship_PBR`): detailní normála a panelové spáry trupu vypnuté (WORKFLOW cu).
- **Ukázka:** `import_kit.SHOWROOM`:
  - `wall_runs` (start, konec, normála, moduly), `run_parts`, `placed`;
  - `place_part` otáčí sockety světel s dílem;
  - stěnový modul má yaw = atan2(normála) a běží podél (sin, −cos) svého yaw;
  - import spadne, když délky modulů nesedí na běh.
  Chodba W 0–9,6 m s portály A/B/C po 2,4 m, zatáčka do L (vnější roh 9,6/1,2, vnitřní 12/−1,2), rameno,
  přechod, pahýl N a koncová stěna N. Provizorní je podlaha a strop nad křižovatkou a přechodem.
  Preset `kit_showroom2.json`.
- **Světla ukázky:** soklová lineární světla zrušená (41 modulů = ~1 ms, podlahu skoro nerozsvítí; s MegaLights se
  mohou vrátit). Provizorní bodovky `prov_spots` = `((x, y), cd[, kužel])`, jen v otevřené části stropu (nad hranou
  zkosení se stíní, WORKFLOW cv). 99 světel, chodba GPU 17,6 ms (52 FPS), křižovatka 16,7 ms (57 FPS).
- **Ladění za běhu bez balení:** `space.Kit <Param> <hodnota> <část jména MI>` a `space.KitLight Showroom …` na
  zabalené hře (presety `kit_rail_noise.json`, `kit_glow_strength.json`); teprve výsledek zapsat do `import_kit.py`.
- **Kritik dávky 2:** 37 → 41 → 44, FAIL; otevřené: okno, kužely/stíny (MegaLights), přechod W→N, materiál kitu,
  displeje a značení. Recenze `Docs/Reviews/2026-09-27_kit_batch2.md`. Autor dávku schválil 27. 9.
- **Po schválení (27. 9.):**
  - **Přístavba ukázky:** uzavřené L jižně od chodby (y −3,6…−8,4). End24W_A → 2,4 m W → zatáčka se zkoseným
    vnitřním rohem B (7,2/−3,6) a vnějším rohem (4,8/−6,0) → 2,4 m ramene → zúžení do průlezu. Vlastní start
    `KitShowroomAnnexSpawn`: klávesa U vede ukázka → přístavba → zpět, `space.Showroom annex`. Preset `kit_annex.json`.
  - **Okno End24W_B:** roleta napůl vytažená (4 ze 7 lamel, spodní lišta, vodicí lišty po stranách), zadní deska
    s otvorem (`_end_base(hole=)`), ostění až k desce. V ukázce je za oknem karta `KitShowroom_WindowStars`
    s `M_Kit_WindowStars`. HLSL hvězd, mlhovin a Mléčné dráhy je z `build_space_scene.py` (čteno přes `ast`, ten
    skript při importu spouští `main()`). Materiál hledá hvězdy podle směru pohledu, takže karta 1,3 m za zdí
    působí jako nekonečno bez paralaxy. Materiál oblohy samotný se nepoužil, protože je `is_sky`.
  - **`Portal_Ring03N_B`:** těžký rám na změně W→N. Rám hluboký 26 cm, stupňovitý límec na obou lících, prstenec
    z A, výstražný pás na hlavici ze strany W, průchod 1,0 m.
  - **MegaLights C:** `SpacePlayerController` nastaví `r.MegaLights.EnableForProject` 1 při vstupu do libovolného
    interiéru a 0 při návratu. Všechna světla ukázky mají `cast_shadows` v levelu (stíny se nepřepínají za běhu:
    první zapnutí dělalo záškub 140 ms). Snímky s volnou kamerou musí MegaLights zapnout samy
    (`kit_showroom2.json` v rozcvičení).
  - **Osvětlení interiéru (rozhodnutí autora 27. 9.):** při chůzi interiérem MegaLights C a vypnuté odrazy
    Lumenu (snížené odrazy ušetřily jen ~1 ms). Stav nastavuje `ASpacePlayerController::ApplyInteriorLighting`,
    pro snímky s volnou kamerou `space.InteriorLighting 1|0`. Předehřátí na prvních 30 snímků levelu
    (`-NoMegaLightsPrewarm` ho vypne pro měření). Po vstupu log `INTERIOR ENTRY … longest frame` (`kit_entry_hitch.json`).
  - **Jas:** `import_kit.KIT_LIGHT_SCALE` 1,8 (chodba 0,19). `space.KitLight <skupina> IntensityScale x` násobí hodnoty
    levelu za běhu.
  - **Výkon (1080p, TSR 75 %):** chodba 16,6 ms na snímek (60 FPS), křižovatka 16,1 ms (62 FPS), bez rezervy. Další
    světla přidávat s měřením. Profil: `Docs/Reviews/2026-09-27_interior_perf_profile.md`.
  - **Zúžení do průlezu:** zadní deska rozdělená kolem otvoru, pás u podlahy průlezu (WORKFLOW dc).

## Interiérový kit, dávka 3: podlahy, poklop, schodiště, rampa (27. 9. 2026)

`Tools/Kit/kit_batch3.py`, stavba `kit_build.py -- batch3` (`ArtSource/Kit/Kit_Batch3.blend`), katalog
`python Tools/Kit/kit_catalog.py 3`.
- **Pivot „run“:** začátek modulu na ose chodby ve výšce podlahy, pochozí plocha z = 0. Deska je široká jako průřez
  plus 0,1 m na každou stranu pod vybrání soklu.
- **Deska:**
  - tmavý podklad pod vším (spáry nekoukají do prázdna);
  - lemy u stěn se šrouby;
  - chodník uprostřed (ve W dvě desky);
  - A: protiskluzové pásy 8 cm po 11 cm (`antislip_tread`, slzičkový plech 25 mm);
  - B: středová čára (Signal, 2,4 cm) a krémové čáry okrajů chodníku, bez šraf podél stěn.
- **Mřížka:**
  - kanál 20 cm s dnem v barvě konstrukce;
  - trubka chladiva (Accent) se signálními pásky, vodní vedení, svazek kabelů, podpěry po 0,6 m;
  - světlo `Light_Channel_0` 1,8 cd/m;
  - ploché pruty 6 mm po 4,5 cm, příčky po 0,3 m, zvýšený rám.
- **Poklop:**
  - rám v primární barvě s gumovým těsněním;
  - kapsa s madlem a dnem, dvě čtvrtotáčkové západky, panty s kloubem, šrouby.
- **Schodiště (`Stair_Flight`, velikost = výška):**
  - stupně 0,2 × 0,25 m;
  - nos stupně v barvě konstrukce se světelným páskem a slabým světlem `Light_Step_i`;
  - uzavřené schodnice se šrouby;
  - madlo v oranžové výrobce s objímkami v ohybech, sloupky s patkami a konzolami;
  - výstražný lem na horní hraně;
  - kolize jako rampa (38,7°), chůze ověřena `space.Walk`.
- **Rampa (`Stair_Ramp`, velikost = vodorovná délka, výška 0,8 m):** tři desky s protiskluzovými pásy, příčná žebra
  s gumou, žluté výstražné okraje, obrubníky, odvodňovací mřížka u paty.
- **Trim kitu má vlastní master `M_Kit_Trim`** (WORKFLOW dd), ne `M_Ship_PBR`. Kovové pruhy mají drsnost ≥ 0,5 (de).
- **Ukázka:**
  - chodby na podlahách z kitu;
  - hala se schodištěm a rampou na x 14–20 m, start `KitShowroomStairsSpawn`, U: ukázka → přístavba → hala → zpět;
  - run parts mohou mít výšku `(x, y, z)`;
  - provizorní boxy `prov_boxes`.
- **Kritik dávky 3:** 41 → 44 → 44, FAIL. Otevřené body: kanál pod mřížkou, madlo poklopu, materiál kitu, světlo.
- **Po schválení (27. 9.):**
  - trubka chladiva v tmavé primární barvě;
  - světlo kanálu 0,6 cd/m z horní hrany boční stěny kanálu, šikmo dolů (nic neleží 5 cm pod pruhem);
  - madlo poklopu: kapsa prořízlá ve víku, světlé dno, oranžová tyč na čepech;
  - hrany schodů v roli `Kit_GlowNeutral` (neutrální bílá, emise 2,5) se světlem `neutral` 0,22 cd na stupeň pod sebou.

## Interiérový kit: materiál (krok „materiál kitu“, 27. 9. 2026)

Všechny vrstvené role kitu (`Kit_Primary`, `Kit_Structure`, `Kit_Accent`, `Kit_Signal`, `Kit_Rubber`) jedou na
`M_Ship_Layered` se statickým přepínačem **`SurfaceDetail`**. Lodě ho mají vypnutý, jejich vzhled se nemění
(hlídá `test_kit_showroom.py`). S přepínačem přibude:
- **mikrotextura `T_Ship_Micro`** (`generate_detail_textures.py`: R broušení, G mikroškrábance, B jemný šum drsnosti)
  na UV0 v metrech, `MicroTileCm` 60. `Brushed` (tón a drsnost v pruzích, konstrukce 0,7 na dlaždici 15 cm), `ScratchAmount` (škrábanec
  = holý kov), `MicroRough`;
- **detailní normála** trupu (`DetailNormalStrength` 0,05, `DetailTileCm` 25);
- **variace po deskách:** `PanelShift` posune grunge podle UV1, `PanelDirtVar` některé desky ušpiní víc;
- **oděr:** `FloorWear` (hrany u podlahy podle okluze), `TopWear` (plochy nahoru, madla a čára na podlaze).

Společné hodnoty jsou v `import_kit.SURFACE` (`GrungeTileCm` 120: se 45 cm vypadal kit po opravě projekce jako
tepaný plech), role si je přepíšou v `layered(..., **detail)`.
Role (27.–28. 9.):
- lak: drsnost 0,42, grunge 80 cm (±0,2), šedý prach 0,15 ve spárách a u soklu;
- konstrukce: ×0,75 palety, kov 0,5 (kov 0,7 bez odrazů Lumenu ztratil difuzní světlo a splynul s panely);
- oranžová: práškový lak 0,5, `TopWear` 1,0, grunge 30 cm;
- guma 0,05 / 0,75.
Světla kitu ×2,0 a emise difuzorů 3,5. Kritik po třech kolech: materiály 4/10, jemná variace se z 1,6 m nečte a zesílená
se čte jako skvrny. Další systémový krok jsou karty špíny podél spár a soklu.

Geometrie (`kit_geo`):
- **špína ve spárách:** čelní plocha každého panelu primárního laku a konstrukce, který má aspoň 15 cm, dostane
  vnitřní lem 4 cm; obvod a boky mají okluzi 0,35 → master tam dá špínu rozbitou grungem;
- **u soklu:** okluze klesá k podlaze jen na svislých plochách, nejvíc v pásu 12 cm, podlahy samy zůstávají čisté;
- **UV0 podél prvku:** u krabic vede U po nejdelší ose (`member`), u trubek po ose (`tube`), broušení tak jde podél
  nosníku či sloupku.
Měření: preset `kit_material` (jas `b_*`, detaily `c_*`/`d_*`, výkon `p_*`), recenze
`Docs/Reviews/2026-09-27_kit_material.md`.

### Špína kartami (krok „špína“, 28. 9. 2026, recenze `Docs/Reviews/2026-09-28_kit_grime.md`)

Stylový záměr autora: **„udržovaná pracovní loď“**. Panely a plochy desek téměř čisté, špína jen tam, kde vzniká:
- ve spárách;
- podél soklu;
- kolem poklopů a madel;
- vyšlapaná linie uprostřed podlahy;
- stékání pod mřížkami.

Žádné skvrny uprostřed desek. Záměr patří do briefu kritika („NEPOŽADUJ víc špíny“).
- Díl deklaruje kartu `Part.grime(kind, at, normal, up, size, alpha, wear=False)`. `kit_build.decals` najde
  povrch paprskem a položí kartu přes `hs_decals.Placer.card_at`. `up` míří ke zdroji špíny (hrana, spára).
- Buňky atlasu 2×2 (`generate_grime_textures.py`) a jejich pokrytí po hloubce karty:
  - `soot`: hustý jen nahoře, 0,68 ve 2 %, 0,35 ve 20 %, 0,16 ve 30 %, 0 v 50 %; na pásy u hran;
  - `rim`: 1cm pás a kapky, na malé kartě zmizí vedle spáry;
  - `streaks`: řídké stružky 0,1–0,15;
  - `smear`: skvrnitý 0,1–0,37, čte se jako skvrna.
- **Na tmavém grafitu musí být špína světlejší matný prach, ne tmavá vrstva.** Ani čistě černá karta jas
  desky (hlavně odlesk) skoro nezmění (A/B `kit_grime_ab.json`). `MI_Kit_Halcyon_DecalGrime` má tint
  (5,0; 5,9; 7,1), teplá šedá; plné ×5 na hnědém atlasu působilo jako rez.
- Viditelný pás je zhruba 35 % hloubky karty, protože světlý prach ukáže i doběh buňky soot. Hloubky: stěna/sokl
  0,18 m, spáry, rámy a nášlapy 0,1 m. Karty 0,3 m dělaly opar uprostřed desky.
- Vyšlapaná linie a stopa u madla: `MI_Kit_Halcyon_DecalWear` (slot `DecalWear`, 7. slot kitu; lodě mají 6,
  `SHIP_SLOTS`), tint (5,5; 6,4; 7,8), drsnost 0,35. Buňka smear je beztvará; směrový pás potřebuje vlastní buňku (otevřené).
- Svítidla: rámeček 6 mm kolem difuzoru (`BEZEL_ROLES`), emise `Kit_GlowWarm` 1,1.

### Místnosti lodi z kitu (pilotní chodba Wayfareru, 28. 9. 2026)

Recenze `Docs/Reviews/2026-09-28_wayfarer_kit_corridor.md`.
- Recept lodi `interior.kit_modules` (`<Loď>_hs.json`) popisuje místnosti v metrech layoutu (x dopředu, y na levobok,
  z od paluby) stejně jako `import_kit.SHOWROOM`:
  - `rooms`;
  - `wall_runs` (začátek, konec, normála líce, moduly);
  - `run_parts` (portály, stropy, podlahy);
  - `stand_in_floor` (náhrada chybějící desky 0,3 m).
- `hs_interior` v místnosti z kitu postaví jen přepážky, tmavou vrstvu nad stropem a náhrady. Objekty layoutu a decaly
  interiéru tam přeskočí.
- UE: `Tools/Assets/kit_rooms.py` vloží díly do `BP_Ship_<Loď>` pod Hull:
  - komponenty `InteriorMod_NN_<díl>` bez kolize;
  - světla ze socketů `Light_fix_kit_NN`, která pawn zapíná s kamerou uvnitř jako ostatní svítidla. Jsou **bez stínů**
    a se zesílením `SHIP_LIGHT_SCALE` ×1,1: loď se létá bez MegaLights a 11 světel se stíny stálo 10–24 ms
    (1676 draw callů). Showroom má ×2,0 a stíny.
- `kit_rooms.py` volá `import_kit.py` i `import_ship.py`. `remove_stale` světla `Light_fix_kit_*` nechává.
- Sdílená matematika rozmístění je `Tools/Kit/kit_layout.py`: ship space = layout + `assemble.offset`, y v UE
  zrcadlené, yaw v Blenderu opačně.
- Test geometrie lodi díly kitu dosadí sám (`add_kit_rooms`): díry, plovoucí díly a průnik trupem se kontrolují
  i s nimi.
- Řez trupem se skutečnými díly: `Tools/Kit/hull_fit_kit_rooms.py` (Blender, pak `--draw`) →
  `Docs/Kit/hull_fit_<loď>_kit_rooms.png`. Wayfarer: nejmenší mezera 0,29 m (portál), jinak 0,52 m.
- Snímky ze stejných pozic před a po: preset `wayfarer_kit_corridor` (pozice v metrech layoutu převedené na
  `camera_local`).
- Chybějící díly zapisuj do `ArtSource/Kit/kit_parts.json` jako `pilot_needs` u rodiny, nové rodiny do dávky.
- **Přepínač** `interior.kit_modules.enabled` (Wayfarer: vypnuto do dávky 4): vypnuté místnosti staví `hs_interior`
  po staru, nápisy ze setupu s `legacy_room` platí jen pro ně (`kit_layout.active_rooms`, `decal_active`). Po změně
  přestavět loď a importovat.
- **Světla v lodi (autor 28. 9.):** stín jen hlavní světla (`SHADOWED_SOCKETS`, lineární ve žlabech), ostatní
  kontaktní stíny 0,05, prosvětlení stěn ×0,5 (`SOCKET_SCALE`). Díly kitu ve světelném kanálu 1, světla v 0 a 1.
  Pawn lodi v režimu osvětlení interiéru vyřadí `Interior`/`InteriorKit`/`InteriorDecals` ze stínů slunce a
  zapne stín stínovaným `Light_fix_*`; v letu je vypne (WORKFLOW dr, ds).
- Nákladový prostor: `Tools/Kit/hold_fit.py` (kontejnery a ulička proti trupu s tenkým obložením).

### Výklenky komponent (dávka 4, 28. 9. 2026)

`Tools/Kit/kit_batch4.py`, stavba `kit_build.py -- batch4` (`ArtSource/Kit/Kit_Batch4.blend`), katalog
`python Tools/Kit/kit_catalog.py 4`, detailní rendery z výšky očí `Tools/Kit/render_kit_closeup.py`, snímky
`kit_bays.json` (přístavba ukázky) a `wayfarer_kit_corridor.json` (`tech_reactor`, `tech_shield`).
Reference: `starcitizenreference/ComponentBays_VideoNotes.md` (SC ukazuje komponentu celou, výklenek s otevřenými
dveřmi, kolébka se žlutými úchyty, pruh na parapetu).
- Výklenek = stěnový modul (`Wall`) s otvorem přes sokl i hlavní panel (`_bay_shell`): těžký rám s těsněním,
  obložená nika `BAY_DEPTH` (0,55 / 0,45 m) až za konstrukci stěny, žebra na zadní stěně, `backing_hole` v tmavém
  podkladu pláště, parapet v kovu konstrukce, špína na hraně parapetu.
- A reaktor: otevřené posuvné dveře (kolejnice pod hlavou, hrana křídla v kapse), kolébka s oranžovými úchyty nahoře
  i dole, kolejnice na výstražném pruhu, krémový plášť s rádiusy 3 cm, stavová obrazovka `reactor`, nosná madla,
  žebra nahoře, kabely a HV vedení do hlavy, chladivo do boku, svislé přípojky v levé mezeře.
- B chladič: žebrovaný blok před čelem pláště (žebra 3 mm po 12 mm na tmavé desce), výdech z vrchu ohnutý do zadní
  stěny (směr kořen křídla), úchyty, spojky chladiva, obrazovka `cooler`.
- C generátor štítů: poklop bez zkosení kolem okénka + zkosený lem, 4 západky, panty, madlo, sání dole, okénko se
  sklem a září emitoru (`Kit_GlowCool`) posunutou pod střed kvůli paralaxe (WORKFLOW dx), obrazovka `shield`.
- Štítky `plate_reactor/cooler/shield`, `warn_hv`, `maker_veyra`, `st_rails` jsou v knihovně decalů s `append`
  (WORKFLOW dt); obrazovky komponent v `kit_screens.py` (oblasti `reactor`, `cooler`, `shield`).
- Světlo výklenku `SOCKET_Light_Bay_0` (rect, neutrální, dosah 0,55 m, bez stínu v lodi), světlo emitoru (bod, 0,35 m),
  socket `SOCKET_Component` (slot, velikost) pro budoucí komponenty jako samostatné předměty. Rozpočet: stěna +
  `Fitting` (3 000).
- Úpravy 29. 9. (autor): pásy v ostění a na zadní stěně niky v roli `Kit_GlowDim` (teplá, emise 0,35; `Kit_GlowWarm`
  1,1 je pro lišty stěn a na malém svítidle zblízka přepaluje), západky poklopu s oranžovým křidélkem v tmavé misce,
  destička pod servisním štítkem. Světla výklenků a emitoru mají `interior_only` (v letu nesvítí, WORKFLOW dz).
- Výkon chodby Wayfareru z kitu s výklenky: 15,81 ms interiér / 19,49 ms let (zabalená hra, 3 × 3 měření,
  `wayfarer_perf.json`); MegaLights v interiérech na 2 vzorcích na pixel.

## Poznatky z rozboru interiérů SC (Markom3D, 26. 9. 2026)

Podrobně s časy: `starcitizenreference/ShipDetailing_VideoNotes.md`.
- **Světla:** C2 má ~790 světel, můstek 74, nákladový prostor 160. To je zhruba 1 světlo na m², světlo u
  každého svítidla, lišty i prstence rámů. U nás 35 na celou loď.
  - Cíl: každé svítidlo a svítící lišta své světlo s krátkým dosahem a bez stínu, stíny jen 2–3 hlavní.
  - Akcent u podlahy a pod deskou.
  - Měřit `stat gpu`.
- **Decaly v interiéru:** husté u dveří (značky, čáry, kroužky), na podlaze čáry, pruhy u prahů a nápisy sekcí.
  Na podlaze nákladového prostoru C2 zabírají decaly přes polovinu plochy. Dlouhé čáry dělá natažený kus atlasu.
- **Panely ovladačů:** tištěné zaoblené rámečky skupin s názvem v přerušené horní hraně, oblouky stupnic,
  popisek pod každým ovladačem. Knoflíky jsou jednoduché, jedno velké podsvícené tlačítko, emisní nápisy.
- **Materiály:** plochý lak s variací lesku (skvrny se ukážou v odlesku), žádné otřené hrany. Švy sedadla
  jsou decaly nebo trim sheet.
- Horní plocha desky C2 je velká a čistá: hustotu soustřeď do shluků u funkčních míst.
- **Zavedeno: světla u svítidel** (`Tools/Blender/hs_fixture_lights.py`, recept `interior.fixture_lights`):
  - každý ostrov svítícího materiálu dostane světla po 0,9 m (dosah 1,6 m, bez stínu), odsazená na otevřenou stranu;
  - jména `fix_N`, pawn je zapíná jen s kamerou uvnitř (WORKFLOW cf);
  - Wayfarer 88 světel, kokpit +1,1 ms GPU.
- Zrno interiéru: `GrungeTileCm` 45 a `RoughVariation` 0,35 na vrstveném masteru. Velikost skvrn trupu
  (180 cm) na plochách kokpitu nebyla vidět.
