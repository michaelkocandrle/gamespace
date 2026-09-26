# Gamespace – pracovní postup a nástrahy

> **Vstupním bodem je od 24. 9. 2026 `CLAUDE.md` v kořeni repozitáře** (krátký přehled, pravidla, příkazy) a skills v `.claude/skills/` (načítají se podle úkolu). Tento dokument nečti celý, hledej v něm grepem; zůstává jako historie a úplný seznam.


Stav k **19. 9. 2026**. Doplňuje `Docs/HANDOFF.md`: HANDOFF říká **co** projekt je a v jakém je
stavu, tento dokument **jak** se na něm pracuje krok za krokem a **na čem jsme se už spálili**.
Nová session: nejdřív HANDOFF (hlavně kapitola 2, pravidla), potom tento dokument celý.

Obsah:
1. Jeden krok práce od zadání po odpověď autorovi
2. Loď z AI modelu: Blender → Unreal
3. Blender MCP: ladění v živém viewportu
4. C++ build, Live Coding, unity build
5. Headless testy
6. Balení hry a snímky (Shots)
7. Kokpit: displeje, HUD, světla (jak to je postavené a proč)
8. Git a commit
9. Nástrahy – úplný seznam
10. Kam dál (priority)

---

## 1. Jeden krok práce od zadání po odpověď autorovi

1. **Přečti zadání a referenci.** Vizuální cíl je 1:1 Star Citizen
   (`starcitizenreference/`, autorovy screenshoty). Autor chce přesnou kopii, ne přibližnou.
   Odchylku, kterou nejde odstranit, pojmenuj v odpovědi.
2. **Rozděl práci na malé kroky.** Každý krok má být hotový, otestovaný a commitnutý.
3. **Změna** jde přes skript nebo kód. Nikdy ne klikáním v editoru. Úpravy assetů dělají Python
   skripty v `Tools/Assets`, ladění lodi recepty JSON v `ArtSource/Ships/<Loď>/`.
4. **Build** editoru (kapitola 4). Po změně C++ je vždy potřeba plný build, editor nesmí běžet.
5. **Headless testy** (kapitola 5). Spusť ty, kterých se změna týká, a po větší změně všechny.
6. **Zabalení a snímky:** `.\Tools\Shots.ps1 -Preset <x> -Package`. Každý snímek si **sám
   prohlédni** (nástroj Read na PNG) a porovnej s referencí. Nečekej, že to autor udělá za tebe.
7. **Commit a push** (kapitola 8).
8. **Odpověď autorovi (česky).** Musí obsahovat:
   - co se změnilo a proč;
   - které testy prošly;
   - které snímky jsi zkontroloval a co na nich je;
   - že je zabalená hra připravená v `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe`;
   - **přesný testovací scénář** (klávesy, kam letět, na co se dívat);
   - co musí posoudit jen autor (pocit, jas, čitelnost na jeho monitoru);
   - jestli stačí Live Coding, nebo je nutný restart editoru;
   - rizika.

Autor hraje zabalenou hru z `C:\gamespace\Builds`. **Když hra běží, balení se zasekne nebo
nakopíruje starý exe.** Hru nikdy neukončuj sám. Požádej autora, ať ji zavře.

---

### 1.1 Reference z videa (21. 9. 2026)

Když jde o pohyb, průběh nebo HUD (quantum skok, přistání, efekty), jeden screenshot nestačí.
`python Tools/Reference/fetch_video.py <url> <název> [--every 2] [--from 3:40 --to 5:10]` stáhne video
z YouTube v nejlepší kvalitě do 4K (yt-dlp, `pip install yt-dlp`), vypíše skutečné rozlišení, nařeže
snímky pojmenované časem (`tHH_MM_SS.jpg`) a složí přehledové listy po 12. Postup: projít listy,
zajímavé časy otevřít v plném rozlišení nebo vyříznout výřez HUD, poznatky zapsat do
`starcitizenreference/` (vlastními slovy, časy jako odkazy). Video a snímky jsou cizí záznam:
leží jen v `ArtSource/Reference/Video/` (v `.gitignore`).

## 2. Loď z AI modelu: Blender → Unreal

Podrobně je to v `Docs/Ships/ShipPipeline.md`. Tady je jen pořadí a místa, kde se chybuje.

> **Než se cokoliv nového pošle do Meshy/Tripo, přečti `Docs/AssetPipeline_Modular.md`.**
> Jednoduchý tvar (trup, tělo) jde generovat vcelku jako doteď. Komplexní kompozice (kokpit
> interiér a cokoliv podobného) se má rozložit na díly a poskládat přes Blender MCP, ne
> generovat jedním promptem — to je přesně to, co se pokazilo u kokpitu.

### 2.1 Recept → .blend

Recept je `ArtSource/Ships/<Ship>/<Ship>_ai_build.json`. `Tools/Blender/build_ai_ship.py` ho
provádí v tomto pořadí:

1. `import` (FBX/GLB z Meshy)
2. `orient` (osa X dopředu, metry)
3. `split` (díly podle ostrovů a obdélníků: trup, canopy, podvozek…)
4. `decimate`
5. UV + `rebake` (textura AI modelu se převypéká na nové UV)
6. `interior`:
   - `fit` (umístění kokpitu do trupu, oko `eye_behind`);
   - `decimate` 150k;
   - `rebake` 4K;
   - `uv_focus` (víc texelů kolem oka);
   - `displays`
7. `canopy_clear`
8. `canopy_frame` (tmavý kovový rám, slot `M_Ship_<Loď>_CanopyFrame`)
9. `lining` (vnitřní obložení, aby trup nebyl zevnitř průhledný)
10. `sockets` (Cockpit, Exit, Display_*, …)

```bash
cd /c/gamespace/gamespace
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python Tools/Blender/build_ai_ship.py -- ArtSource/Ships/<Ship>/<Ship>_ai_build.json
cd ArtSource/Ships/<Ship>
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b <Ship>.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"
```

`--no-save` recept jen vyzkouší. Výstup exportu je
`Export/<Ship>_manifest.json` a FBX pro každý díl.

**Displeje v receptu** (`interior.displays.screens[]`):
- `centre`, `u`, `v` (osy roviny displeje v souřadnicích modelu kokpitu);
- `corners`: čtyři rohy TL, TR, BR, BL v metrech (u, v). Otvory rámečků nejsou obdélníky, proto
  rohy, ne `rect`;
- `texture_rect` [x0, y0, x1, y1]: kde displej leží na plátně hry (pixely od levého horního rohu, přesně
  jako `USpaceCockpitDisplays::ScreenRect`); celé plátno je `texture_size` [1330, 490]. Bez nich dostane
  displej i jednu n-tinu šířky textury (starý způsob);
- `grow_m` (0,0045, ~5 mm ve hře): displej sahá o tolik dál než řez, pod vyvýšenou hranu rámečku. Přesně
  na obrys otvoru v některých rozích prosvítal světlý proužek AI skla (autorovy detaily 19. 9. 2026).
  Řez zůstává na obrysu, aby rámeček neztratil vnitřní hranu. Porovnáno 0 / 5 / 8 mm v Blenderu z oka
  s fialovými displeji – pozor, `get_viewport_screenshot` fotí před překreslením, vynuť
  `bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP")`;
- `cut_depth_m` u displeje přebije společnou hloubku řezu. Malé displeje ve sloupku mají 6 mm, aby
  zůstaly knoflíky na rámečku (se 2 cm by je řez utrhl).

Skript vyřízne plochu uvnitř čtyřúhelníku (`inside_quad`), dá jí slot `*_Screens` a UV podle
`texture_rect`. Na střed displeje dá socket `Display_<name>`. Rohy se ladí v Blender MCP
(kapitola 3). Sada displejů na první stíhačce (odstraněna 24. 9. 2026): `left` a `right` (MFD 29 × 25 cm),
`centre_top` (radar, 11 × 13,5 cm) a `centre_bottom` (self status, 11 × 12 cm) ve středním sloupku. Test
`test_cockpit_displays.py` (loď z `Tools/Tests/ship_under_test.py`, bez modelu SKIP) hlídá, že `texture_rect` v receptu = `ScreenRect` v kódu a že poměr stran
obdélníku odpovídá sklu.

### 2.2 .blend → Unreal

```powershell
$env:GAMESPACE_SHIP_MANIFEST = "C:\gamespace\gamespace\ArtSource\Ships\<Ship>\Export\<Ship>_manifest.json"
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py
.\Tools\run_editor_python.ps1 Tools\Assets\build_main_menu.py
```

- Nastavení lodi (pawn, komponenty, materiály, světla, kamera) je v
  `ArtSource/Ships/<Ship>/<Ship>_setup.json`. Po odebrání hodnoty z něj zůstane v Blueprintu
  stará hodnota (nástraha 9.3c).
- `no_nanite_parts: ["Interior"]`: interiér **nesmí** mít Nanite (nástraha 9.2a).
- Materiály staví `Tools/Assets/ship_materials.py`. Displeje používají master `M_Ship_Screen`
  (unlit, opaque, pixel animation, parametr `EmissiveStrength`).
- `build_main_menu.py` po importu obnoví úvodní scénu s lodí; loď se zobrazí, až bude nastavená v
  `MENU_SHIP` (teď žádná, kamera krouží kolem prázdného `MenuOrbitCenter`).

---

## 3. Blender MCP: ladění v živém viewportu

K čemu to je: vidět model z oka pilota a ladit ho (rohy displejů, rám, světla) bez stovek
headless renderů. Nainstalováno 19. 9. 2026.

### 3.1 Instalace (už je hotová, jen pro případ obnovy)

- `uv` přes winget (`astral-sh.uv`). **PATH se projeví až po restartu terminálu**, proto se
  v konfiguraci používá plná cesta k `uvx.exe`.
- Server pro Claude Code (scope local pro `C:\gamespace`):
  ```
  claude mcp add blender -e DISABLE_TELEMETRY=true -- <plná cesta>\uvx.exe blender-mcp
  ```
  **`DISABLE_TELEMETRY=true` je nutné.** Balík jinak posílá autorovi balíku data o použití
  (včetně screenshotů a stavu scény).
- Addon do Blenderu: `Tools/Blender/mcp/install_blender_mcp_addon.py` (bere `bundled/addon.py`
  z uv cache, zapne addon a vypne `telemetry_consent`).

### 3.1b Scenario MCP (UltraShape a spol., 23. 9. 2026)

3D modely se do Scenaria přes REST nahrávají vícedílným uploadem (`POST /v1/uploads` → `PUT` na
presigned URL → dokončovací volání), a to poslední volání není ve veřejné dokumentaci (všechno pod
`docs.scenario.com` vrací bez přihlášení 404). Proto se používá jejich vlastní MCP server, který
upload řeší sám:

```
claude mcp add --transport http scenario https://mcp.scenario.com/mcp --header "Authorization: Basic <base64 klíč:secret>"
```

- Autentizace je HTTP Basic, tedy `API key:API secret` v Base64 (samotný klíč nestačí).
- Hlavička se uloží do `.claude.json` v domovském adresáři k tomuhle projektu — **ne do repozitáře**;
  klíče leží v `C:/gamespace/secrets/` (mimo git).
- **Nástroje serveru se načtou až při startu session**, po přidání je potřeba session restartovat.
- `claude mcp list` ověří spojení (`✓ Connected`).

UltraShape 1.0 (`model_ultrashape-1-0`, capability `3d23d`) chce **obojí**: `image` (referenční
obrázek) i `model` (hrubý mesh), k tomu `numInferenceSteps` (1–50, výchozí 50),
`octreeResolution` (128–1024, výchozí 1024) a `seed`.

Nástrahy (23. 9. 2026):
- **UltraShape není v plánu `cu-basic`.** `model_run` vrací 403 `ModelAccessRestrictedError`,
  vyžaduje plán `cu-pro-q3-25`. Blokuje to i `dry_run`, cenu tedy nezjistíš dřív než po upgradu.
- MCP server je registrovaný s rozsahem *local* pro `C:\gamespace\gamespace`. Session spuštěná
  v `C:\gamespace` jeho nástroje vůbec nedostane. Buď startuj session v adresáři repa, nebo mluv
  se serverem napřímo přes JSON-RPC (`initialize` → `notifications/initialized` → `tools/call`,
  hlavička `Mcp-Session-Id`, Basic auth ze `scenario.key`).
- Upload přes MCP: `upload_asset` (s `file_size`, bez `data`) vrací `parts[].upload_url`.
  Na každou URL udělej `PUT` se syrovými bajty (bez `x-amz-checksum-*` hlaviček) a zavolej
  `upload_asset_complete` s `upload_id`. Takhle prošly PNG i GLB pro test SwitchPanel: obrázek
  `asset_rmnHbeqKqDFkHQGpGqtpGEeL`, mesh `asset_ep4gbRYJxXJqvkDhuGmGkMpr`. Po upgradu je stačí
  znovu použít.

### 3.2 Použití

1. Spusť Blender **s GUI** na pozadí. Socket na `localhost:9876` běží jen s GUI; v `-b` se addon jen
   zaregistruje.
   ```bash
   cd /c/gamespace/gamespace && MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" ArtSource/Ships/<Ship>/<Ship>.blend
   ```
2. Buď MCP nástroje `blender` (`get_viewport_screenshot`, `execute_blender_code`…; mnoho jich
   vyžaduje argument `user_prompt`), nebo pomocné skripty v `Tools/Blender/mcp/`, které mluví přímo
   se socketem (fungují, i když MCP nástroje nejsou v session načtené):

| Skript | Co dělá |
| --- | --- |
| `mcp_socket.py` | `send(type, params)`; z příkazové řádky `python mcp_socket.py execute_code '{"code": "..."}'` |
| `mcp_eye_view.py out.png [--headless --displays on\|off --look clay\|material --ship X]` | kamera `EyeCam` v oku podle `SOCKET_Cockpit` z manifestu a FOV/sklonu ze setupu (= kamera kokpitu ve hře), backface culling jako v UE; živě přes MCP screenshot, `--headless` clay render `<Loď>_HS_Game.blend` 1920×1080 bez živého Blenderu (předloha pro koncepty) |
| `mcp_grid.py <Ship> out.png` | měřicí mřížka na rovině displeje (1 cm žlutá, 5 cm červená, osy zelené) |
| `mcp_measure_openings.py <Ship>` | paprsky z oka: najde otvor v rámečku a vypíše jeho rohy (u, v) |
| `mcp_corners.py <Ship> '<json>' out.png` | posune plochy displejů na zadané rohy a vyfotí pohled z oka (displeje, které v JSON nejsou, nechá být) |

3. **Postup ladění rohů:**
   - pohled z oka;
   - mřížka, odečti rohy otvoru;
   - `mcp_corners.py` s kandidátem, prohlédni zoom;
   - uprav, opakuj;
   - hotové rohy zapiš do receptu;
   - plný build (2.1, 2.2);
   - snímky `cockpit` z hry.

   Živé úpravy v GUI Blenderu se **neukládají**, pravda je vždy recept.

   **Nový otvor, který ještě nemá plochu displeje** (tak se měřil střední sloupek, 19. 9. 2026):
   - pohled z oka, odečti pixely otvoru;
   - paprsky z oka přes ty pixely → body skla v souřadnicích modelu kokpitu (`placement` matice
     inverzně), rovina proložená SVD: střed a normála. Osy: `u` = (0, −1, 0) (doprava z pohledu pilota),
     `v` = normála × `u`;
   - flood fill jako `mcp_measure_openings.py` (stačí mu podstrčit seznam displejů);
   - obrys kandidátních rohů jako tenké emisivní čáry, kamera **v oku** jen natočená na otvor
     s úzkým FOV (perspektiva se nezmění, jen zoom). Pozor: kamera potřebuje
     `to_track_quat("-Z", "Y")`, s `"Z"` je snímek otočený o 90°;
   - flood fill se zastaví o knoflíky na rámečku a spodní hranu „zkosí“ – skutečná hrana skla je
     vodorovná, oprav ji ručně podle zoomu;
   - `get_viewport_screenshot` chce **absolutní** cestu k souboru.
4. Po skončení Blender zavři. Když ho necháš běžet, drží .blend a build receptu může selhat na zápisu.

---

## 4. C++ build, Live Coding, unity build

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" gamespaceEditor Win64 Development -Project="C:\gamespace\gamespace\gamespace.uproject" -WaitMutex -FromMsBuild
```

- **Editor musí být zavřený.** Headless skripty editor spouštějí a samy zavírají.
- **Live Coding** stačí jen na změny těl funkcí. Nové soubory, `UPROPERTY`, `UFUNCTION` nebo
  změny hlaviček vyžadují restart editoru a plný build. Autorovi to vždy napiš.
- **Herní target se kompiluje jinak než editor** (jiné seskupení unity build). Chyba se může
  ukázat až při `Package.ps1`. Viz nástraha 9.4a.
- Nový modul v `gamespace.Build.cs` (naposledy `RenderCore`) je povolený. Smart App Control je
  vypnutý.

---

## 5. Headless testy

Spouštěj **nástrojem PowerShell** (přes bash se rozbije `$PSScriptRoot`):

```powershell
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_displays.py
```

| Test | Pokrývá |
| --- | --- |
| `test_cockpit_displays.py` | displeje v kokpitu: slot, render target, velikost, světla, stav |
| `test_cockpit_frame.py` | pozice oka, deska 7–13° pod horizontem, ≥ 1,2 m od oka |
| `test_flight_hud_sc1c.py` | rozložení HUD podle SC, barvy, režimy space.Hud |
| `test_ship_import.py` | import lodi, díly, sockety, materiály |
| `test_landing_sc2.py`, `test_landing_l5.py` | podvozek, přistání |
| `test_ifcs_sc1.py`, `test_boost_afterburner_sc1b.py`, `test_flight_modes.py`, `test_free_look.py` | let |
| `test_character_l6.py`, `test_planet_l3.py`, `test_menu_settings.py` | postava, planeta, menu |
| `test_interior.py` | interiér Steadfastu: usage flagy, výchozí textury samplerů, parametry `M_KitTrim`, tagy, světla |

Testovaná loď je jmenovaná na jednom místě: `Tools/Tests/ship_under_test.py` (`SHIP = None`, dokud není
importovaná nová loď). Testy, které potřebují model (displeje, rám kokpitu, sockety podvozku, import),
do té doby vypíšou SKIP „no ship model yet"; letové testy běží na nativním `ASpaceshipPawn` (kvádr).

Testy mimo UE (obyčejný Python):
- `Tools/Assets/tests/test_import_ship_plan.py`;
- `Tools/Blender/tests/test_ship_export_core.py`.

Test musí hlídat to, co autor viděl rozbité. Když se opraví vizuální chyba, přidej do testu
kontrolu, která by ji zachytila (příklad: `no_nanite_parts` v `test_import_ship_plan.py`).

---

## 6. Balení hry a snímky (Shots)

```powershell
.\Tools\Package.ps1                              # ~5 min, kontroluje 12 klíčových assetů včetně písma
.\Tools\Shots.ps1 -Preset cockpit -Package       # zabalí a vyfotí
.\Tools\Shots.ps1 -Preset cockpit -Keep          # snímky i do Docs\Shots\ (jdou do gitu)
```

Presety (`Tools/Shots/*.json`):

| Preset | Obsah |
| --- | --- |
| `cockpit` | pohled z oka, displeje, rám |
| `cockpit_light` | varianty světel kokpitu |
| `display_sharpness` | ostrost displejů při rychlém letu |
| `cockpit_centre` | střední sloupek (radar, self status): vesmír, horizont, afterburner, vysouvání podvozku, přistání. Obrazovky jsou malé, vyřízni a zvětši oblast ~745–855 × 630–880 px |
| `hull_detail` | trup zblízka: detailní vrstva materiálu (srovnání se `detail_normal_strength` 0) |
| `mfd_pages` | stránky MFD ve stavech, které je naplní. Vyřízni levý MFD ~495–710 × 640–825 a pravý ~893–1105 × 640–825 px |
| `look_sun`, `look_fill` | proč je loď v kosmu silueta: směr slunce, výplň sky lightu, lak trupu |
| `look_tune`, `look_final` | post process po vrstvách a výsledná volba proti úrovni tak, jak je |
| `hull_zones` | okluze, kavita a odřený lak na trupu (`space.ShipMat`) |
| `hull_decals` | kam dosedly nápisy; šmouhy místo textu znamenají špatně otočený decal |
| `hull_panels` | panelové spáry: velikost listu a síla (`space.ShipMat`) |
| `hull_scorch` | spálený plech u trysek: síla a dosah (`space.ShipMat`) |
| `vtol` | SC-2b: odznak VTOL, visení na zvedacích tryskách (`space.Vtol`) |
| `velocity_vector` | SC-3: značka dráhy letu (pole `drift` ve scénáři) |
| `dust_tune`, `space_look` | rychlostní čáry (`space.Dust`) a prohlídka prostředí |
| `quantum`, `quantum_look`, `tunnel_tune` | SC-4: HUD quantum drivu a skok (pole `quantum`, `quantum_progress`, `quantum_ready`, `facing: body:<jméno>`), ladění tunelu (`space.Tunnel`) |
| `look_sharp`, `look_groups` | proč je obraz měkký a co která škálovací skupina stojí |
| `look_artifacts` | film grain, motion blur a stopy za pohybem – změřeno, žádný z nich obraz nekazí |
| `hud` | HUD ve všech situacích |
| `landing` | přistání, podvozek |
| `ship_views`, `ship` | loď zvenku |
| `steadfast_interior` | interiér Steadfastu: nákladový prostor (a–e), průchod a chodba (f–g), strojovna (h–j); volná kamera, pevná expozice |
| `interior_tune` | varianty materiálu a světel interiéru (`space.Kit*`), každá začíná `space.KitReset`; celek a detail stěny |
| `ceiling_tune` | světla nákladového prostoru se stropem: jas a kužel bodovek, oranžové akcenty; celek a pohled na strop |
| `accent_tune` | jas oranžových akcentů v celém interiéru (prostor, strop, chodba, strojovna) |
| `flicker_check` | blikání: každý pohled 8× za sebou stejnou kamerou; vyhodnocení = podíl pixelů, které se mezi snímky mění (`python Tools/Shots/measure_flicker.py <složka> <mapa.png>`) |
| `sc_look` | interiér s automatickou expozicí ve 1080p proti SC referencím; čísla `python Tools/Shots/measure_look.py <složka>` (rozsahy SC v hlavičce skriptu) |
| `sc_tune` | varianty barvy SC vzhledu (kov, teplota světel, barva lišt, akcenty) přes `space.Kit*` |
| `wear_check` | opotřebení zblízka (stěna, bedna, rám dveří, podlaha) bez něj a s výchozím nastavením |
| `wear_tune` | opotřebení a špína materiálu (`space.Kit WearAmount / WearEverywhere / GrimeAmount`) |
| `cockpit_look` | expozice v letovém kokpitu: `space.Post AutoExposureBias` 0 / −0,5 / −1 / −1,5 nad planetou, ve vesmíru, dolů |
| `perf_quality` | cena kvality ve 1080p: filmová proti epické po skupinách a TSR 75 %, v letovém kokpitu i interiéru (spouštět s `-Width 1920 -Height 1080` – autor hraje ve 1080p, výchozích 1600 × 900 dává o ~40 % lepší čísla) |
| `perf_interior` | výkon interiéru: `stat unit` a varianty stínů / dosahu světel přes `space.KitLight` |
| `interior_walk` | chůze interiérem v zabalené hře: `space.Interior`, `space.Walk`, kamera postavy (`"camera": "pawn"`); výsledek je i v logu hry (`WALK end at …`) |

Pole jednoho snímku:
- základ: `camera`, `altitude_m`, `facing`, `speed_ms` (nebo `drift` [vpřed, vpravo, nahoru] v m/s,
  když loď má lítat jinam, než kam míří), `boost`, `afterburner`, `stick`, `mode`, `settle`;
- kokpit: `cockpit_eye`, `hide_hull`, `hide_canopy`, `cockpit_light` [key, fill], `display_light`, `interior_tint`;
- ostatní: `console` (konzolové příkazy, **zůstanou nastavené i pro další snímky**), `gear`, `precision`, `chase_*`, `hud` (0–3).

Kontrola: snímky si otevři, porovnej s referencí a z více snímků slož jeden list
(PIL ve scratchpadu), aby šlo porovnat varianty vedle sebe.

Hra během snímků krátce převezme popředí. Když autor zrovna hraje, nejdřív se domluv.

---

## 7. Kokpit: displeje, HUD, světla

### 6.1 Ladění vzhledu za běhu (šetří hodiny)

Každá varianta materiálu přes recept a balení stojí ~4 minuty. Proto se parametry lodi dají měnit
**v běžící zabalené hře** a jeden balíček pak pokryje desítky variant (~20 s na jednu):

```
space.ShipMat DetailNormalStrength 1.2      # skalár na všech materiálech lodi
space.ShipMat DetailTileCm 12
space.ShipMatColor BaseColorTint 3.4 3.4 3.4
space.CockpitPitch -3                        # sklon pohledu v kokpitu
space.DashboardFocus 1                       # přiblížení na displeje
space.MfdPage 1 2                            # stránky MFD
```

Ve scénáři snímků je dej do pole `console` (platí i pro další snímky, viz nástraha 9.2h) – vzor je
`Tools/Shots/hull_tune.json`: jeden běh, šest variant vedle sebe. Příkaz dělá dynamické instance
materiálu, takže **nic neukládá**: co vypadá dobře, přepiš do `<Loď>_setup.json` a jednou přeimportuj.

### 7.1 Displeje (MFD)

- `UCockpitDisplayComponent` (`Source/gamespace/CockpitDisplayComponent.*`) kreslí widget
  `USpaceCockpitDisplays` (podtřída `USpaceFlightHud`, stejné názvy widgetů a stejné
  `ApplyState`) přes `FWidgetRenderer` do render targetu. RT jde do MID slotu `*_Screens`.
- **Velikost RT** odpovídá velikosti displeje na obrazovce:
  - `ScreenShareAt88` 0,155 × šířka okna × `Oversample` 1,25;
  - měřítko se počítá **jen ze šířky okna**, ne z FOV, a RT se přestaví až při změně měřítka > 0,099
    (nástraha 9.2c).
- **Stav** (čísla) se aktualizuje `StateRateHz` 5×/s (setup), **kreslí se** `UpdateRateHz` 60×/s.
  Během změny se čísla kvantují (rychlost na desítky, G na 0,5). Přesná jsou, jen když hodnota stojí
  (`Steady`/`SteadyState`, prahy 0,5 m/s a 0,05 G za aktualizaci). Proč: TSR jinak míchá dva snímky
  čísel a vznikají „duchy“.
- **Světla:** Rect lighty na socketech `Display_*` (8 cd, barva 0,4/0,75/1). Displeje tak
  prosvětlují kokpit jako v SC. Malé displeje ve sloupku svítí úměrně ploše (velikost i cd podle
  `ScreenRect`).
- **Plátno** 1330 × 490: vlevo FLIGHT 0–560, vpravo STATUS 560–1120, sloupek 1120–1330 (radar 0–259,
  self status 259–490). Stejná hustota pixelů na centimetr skla na všech displejích.
- **Střední sloupek:** RADAR (`USpaceHudRadar`, dosah `RadarRangeM` 5 km, kontakty z
  `USpaceCockpitDisplays::MakeRadarContacts` 5×/s: pawny a static meshe s kolizí v dosahu, tělesa jen jako
  směr na okraji a jen do 60° nad/pod křídly) a SELF STATUS (`USpaceHudShipStatus`: obrysy kolizních hullů
  shora, motory ze socketů `Engine_*` podle tahu, podvozek ze `Gear_*`). Vypínač `space.CockpitCentre 0`.
- **Měření:** `stat SpaceCockpit` (stav a kreslení displejů), `stat SpaceHud` (kreslené prvky).
- **Čitelnost:** z oka je MFD na 1080p ~0,4 své velikosti v návrhu (560 px → ~230 px). Písmo pod 26 se z křesla
  nečte; `test_cockpit_displays.py` hlídá minimum. Obsah přidávej jen s tímhle rozpočtem, detail patří do
  přiblížení (Z, `ASpaceshipPawn::SetDashboardFocus`, `space.DashboardFocus`). Text se nezalamuje ani
  neořezává: přetečení poznáš jen na snímku (hodnota přes záložku stránky).
- **Stránky MFD** (`F1` levý, `F2` pravý, s Alt zpět; `[` `]` pro US klávesnici): vlevo FLIGHT / THRUSTERS / NAVIGATION, vpravo STATUS /
  CONTACTS / SELF STATUS, `UWidgetSwitcher` (kreslí se jen zobrazená). Stránku drží
  `UCockpitDisplayComponent` (`CyclePage`, `SetPage`), ve snímcích `console: ["space.MfdPage 1 2"]`.
  Novou stránku přidej do `PageTitles` a do pole stránek v `Screen(...)` v `BuildTree`; jen se skutečnými
  daty. Skryté řádky seznamů skrývej i s jejich linkou (řádek a linka v jednom boxu).

### 7.2 HUD

- `USpaceFlightHud` (`SpaceFlightHud.*`):
  - rozložení změřené z SC při 1080p od středu;
  - paleta ledově azurová, písmo Rajdhani Medium se slabým azurovým obrysem;
  - kreslené prvky: `USpaceHudSymbol`, `USpaceHudTape`, `USpaceHudLadder`, `USpaceHudGauge`, `USpaceHudLamp`.
- `space.Hud`: 0 vypnuto, 1 jen letový HUD (výchozí), 2 + kompaktní text, 3 + plný debug. H cykluje.
- **Písmo:** TTF v `Content/UI/Fonts`, staguje se přes `DirectoriesToAlwaysStageAsUFS Path="UI/Fonts"`.
  - Vlastní písmo: první `.ttf`/`.otf` v `Content/UI/Fonts/Custom/` (v `.gitignore`). Sem si autor
    může dát vlastní font.
  - Písmo ze hry SC **nevytahujeme ani nestahujeme z neoficiálních zdrojů**.

### 7.3 Světla a expozice

- Kokpit má key a fill světlo (setup: key 1,5, fill 0,8, source radius 12, offset [80, 0, −10],
  radius 250). Laď je přes `cockpit_light` ve snímcích nebo `DebugSetCockpitLighting`.
- Expozice ve vesmíru je pevná (EV100 3). Starý kokpitový bodovka 12 cd dělala celý kokpit šedým
  (nástraha 9.3e).
- Tint interiéru (`base_color_tint` 0,6) ztmaví AI texturu na SC tón.

---

## 8. Git a commit

- **Před commitem `git status`.**
- **Nikdy nepřidávej** autorův soubor `Docs/UI/Screenshot 2026-09-21 150400.png`. Vždy:
  ```bash
  git add -A -- . ':!Docs/UI/Screenshot 2026-09-21 150400.png'
  ```
- Zprávy commitů jsou anglicky, krátký nadpis a konec:
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Každý krok se commitne a pushne (`git push origin main`).
- Po větším kroku aktualizuj `Docs/HANDOFF.md`:
  - kapitola 5, bod v seznamu hotového;
  - kapitola 11, známé problémy;
  - kapitola 13, commity.
- Po změně systému aktualizuj i `README.md`.

---

## 9. Nástrahy – úplný seznam

Každá nás stála aspoň hodinu. Formát: **příznak → příčina → řešení**.

### 9.1 Prostředí a nástroje

- a) **Balení visí nebo zabalí starý exe.** Příčina: autor má spuštěnou hru z `Builds`, nebo zůstal
  viset spadlý proces hry. Řešení: požádej autora, ať hru zavře. Proces sám neukončuj. Po zabalení
  zkontroluj čas `gamespace.exe`.
- b) **`run_editor_python.ps1` z bashe nefunguje** (`$PSScriptRoot`). Spouštěj nástrojem PowerShell.
- c) **Bash heredoc a apostrofy.** Delší Python patch skripty piš nástrojem Write do scratchpadu
  a spouštěj je. Pozor i na `\U` v cestách uvnitř normálních Python řetězců (unicode escape), používej
  `r"..."`.
- d) **Blender z Git Bash** mění cesty `/c/...` a `//Export`. Vždy `MSYS_NO_PATHCONV=1`.
- e) **winget nainstaluje nástroj, ale PATH ho nevidí** do restartu terminálu. Používej plnou cestu.
- f) **Blender MCP:**
  - addon se našel až po `addon_refresh`;
  - telemetrie je ve výchozím stavu zapnutá, vypínej ji v serveru (env) i v addonu;
  - socket jen s GUI;
  - nástroje chtějí argument `user_prompt`;
  - běžící GUI Blender drží .blend.
- g) **Klávesy a rozložení klávesnice.** Autor má **českou klávesnici** (rozložení 0405): `[`, `]`, `;`, `'`
  a podobné nejsou samostatné klávesy (vpravo od P je „ú“) a Unreal klávesu hledá podle znaku. Nové
  klávesy vybírej z písmen, čísel, F-kláves, čárky a tečky. **F1–F5, F9, F11, PgUp/PgDn a `;`** mají
  v Development buildu (ten autor hraje) ladicí příkazy enginu (`DebugExecBindings` v `BaseInput.ini`:
  F1 drátový model, F2 unlit…); klávesu pro hru z nich uvolni řádkem `-DebugExecBindings=(…)` v
  `Config/DefaultInput.ini` (přesná kopie řádku z enginu), jako u F1/F2 pro stránky MFD.

### 9.2 Vykreslování (UE 5.8)

- **Materiál z Pythonu:** uzly `Transform` (world→local, local→tangent) daly v `M_Ship_PBR` nulový vektor a
  **loď byla černá**. Převody prostorů dělej v HLSL uvnitř `MaterialExpressionCustom`
  (`GetPrimitiveData(Parameters).WorldToLocal`, `Parameters.TangentToWorld`), vstupy uzlu připojuj jménem
  (`unreal.CustomInput` se plní přes `set_editor_property`, struktury neberou keyword argumenty).
  Shadery se v commandletu nekompilují, chybu uvidíš až po zabalení – proto po každé změně materiálu
  snímek. Detail, který drsnost i snižuje, dělá na kovu lesklé fleky: opotřebení ji má jen zvyšovat.

- **Poloha kamery v Ticku pawnu je z minulého snímku.** `PlayerCameraManager` se aktualizuje až po
  pawnu. Co se staví kolem kamery (prach, tunel), je při 1,2 km/s o 20 m pozadu; přičti
  `LinearVelocity * DeltaSeconds`. Příznak: bílý klín přes obraz, který se v jiném snímku nezopakuje
  jinde, jen v rychlosti (21. 9. 2026).
- **Co jde postavit uzly, nedávej do Custom uzlu.** Custom uzel s `LocalPosition` se v editoru
  postavil, cook log mlčel, a v zabalené hře se objekt kreslil výchozím šedým materiálem. Plochý
  šedý povrch tam, kde má být efekt, znamená „materiál spadl na default“ – zkus ho přepsat bez
  Custom uzlu, než budeš hledat chybu v HLSL.
- **Tmavá scéna s automatickou expozicí není tmavá.** Skoro černý tunel si oko vytáhne na sytě modrou.
  Když má něco zůstat tmavé, připíchni expozici (`AutoExposureMin/MaxBrightness` + `AutoExposureBias`
  přes `PostProcessSettings` kamery) a teprve pak lad' jas všeho svítícího – měřítko se posune ~6x.
- **Operátory přes MCP spouštěj přes `Tools/Blender/mcp/ops_context.py`** (`run_op`, `edit_mode`;
  skill `blender-mcp`). Dřív padaly na `poll() failed, context is incorrect` kvůli chybějícímu
  kontextu okna; helper dá `temp_override(window, area, region, …)`. Headless (`-b`) projekční
  operátory (`knife_project`, `view3d.*`) tiše nic neudělají, proto je helper odmítne. bmesh zůstává
  alternativou pro čistě geometrické operace. Na prohlédnutí malých dílů nestačí `get_viewport_screenshot` – renderuj
  kamerou do souboru a ten si přečti.
- **Konzolové příkazy ve snímkovém běhu platí do konce běhu.** Druhá varianta zdědí nastavení první,
  takže „A/B“ porovnání vyjde falešně. Každý snímek musí začít návratem na výchozí hodnoty a první
  snímek zahoď (loď se do něj nestihne natočit).
- **Průhledný materiál svět nezakryje, jen dobarví.** Ať má krytí jakékoliv, hvězdy a planety pod ním
  budou vidět. Když má něco zakrýt svět (mlha v tunelu), musí být neprůhledné – a řídnutí se dělá
  maskou s modrým šumem (`MaterialExpressionScalarBlueNoise`, práh `opacity_mask_clip_value` 0,5).
  `MaterialExpressionDitherTemporalAA` v Pythonu neexistuje.
- **Vstupy Custom uzlu jsou `float`, ne LWC.** Odečítat v něm dvě světové pozice (`WorldPosition` minus
  `ObjectPositionWS`) znamená u vzdáleného tělesa chybu v decimetrech a efekt zmizí. Rozdíl počítej
  uzlem `Subtract` mimo Custom, nebo měř v prostoru instance (`MaterialExpressionLocalPosition`
  s `local_origin=INSTANCE`, u kvádru -50..50 cm).
- **Tvar natažené kostky se neměří 3D vzdáleností od osy.** Pixel je vždycky na povrchu, takže je od
  osy aspoň půl šířky daleko a tvar vyjde nula. Ber `min(|y|, |z|)` v prostoru instance.
- **Tenká rychlá čára v TSR vyjde tečkovaná.** Kresli ji jako **plošku natočenou ke kameře**
  (`Plane` v ISM, rotace `MakeFromXZ(směr, k_kameře)`) a nech šířku růst se vzdáleností (~3 px).
  `enable_responsive_aa` to sice taky spraví, ale na světlém pozadí za to zaplatíš černými šmouhami
  tam, kde TSR nemá historii.
- **Neprůhledná „obloha“ kolem kamery patří na kouli, ne na válec.** Silueta válce udělá přes obraz
  ostrou rovnou hranu. Když barvu počítáš jen ze směru pohledu, na tvaru nezáleží – a koule nemá švy.
- **Custom uzel s texturami: `Texture2DSample(Tex, TexSampler, uv)`, nikdy `Tex.Sample(...)`.** Ray tracing
  hit shadery nemají derivace, `.Sample` v nich neprojde a celý materiál se v buildu nahradí výchozím
  šedým. V editoru ani v headless buildu materiálu chyba vidět není – jen v cook logu
  („Failed to compile Material“, `%APPDATA%\Unreal Engine\AutomationTool\Logs\...\Cook-*.txt`).
- **Rozměry z Poly Haven API (`dimensions`) jsou v milimetrech**, ne v centimetrech.
- **SkyAtmosphere a obloha s `IsSky`:** s vlastní kopulí oblohy se atmosféra nekreslí sama, materiál
  kopule ji musí přidat uzlem `SkyAtmosphereViewLuminance`. V záchytu sky lightu ten uzel ale nedává
  nic – výplň z oblohy pak chybí a stíny jsou černé; něco jiného (u nás malovaný přechod) musí
  do záchytu světlo dodat.
- **Virtuální zem SkyAtmosphere** (`bottom_radius`) musí být pod nejnižším terénem, jinak má obzor
  černý pruh (paprsky nad skutečným obzorem narazí na tmavou zem atmosféry).
- **`CameraLagMaxDistance = 0` není „bez zpoždění“, ale „bez stropu“.** Chceš-li zpoždění pryč,
  vypni `bEnableCameraLag`. A zpoždění i s rozumným stropem jde podél dráhy letu: při rychlém letu
  a pohledu z boku vystrčí loď ze záběru (quantum, 21. 9. 2026).
- **Průsvitná vrstva přes celý obraz (mlha) a TSR:** bez vlastního pohybu nemá TSR čím odmítnout
  starou historii a objekty za ní nechávají tmavé „duchy“. Takové materiály: `enable_responsive_aa`
  a `output_translucent_velocity`.
- **Plně krycí průsvitná vrstva kolem kamery** (mlha tunelu) má střed v kameře, takže se při řazení
  podle vzdálenosti vykreslí jako poslední a přemaže ostatní průsvitné věci (vypadá to jako černé
  kostičkované čáry). Věci, které mají být před ní, potřebují vyšší `TranslucentSortPriority`.
- **Záporná `TranslucentSortPriority`** řadí objekt před *všechny* průsvitné věci ve scéně, ne jen
  před ty, se kterými ho chceš seřadit. Zvedni prioritu těm, které mají být navrchu.
- **Efekt kolem kamery z válce:** kamera uvnitř otevřeného válce ve směru letu dostane úběžník
  zadarmo z perspektivy (`USpaceSpeedTunnelComponent`). Materiál oboustranný, aditivní; rozměry
  z bounds meshe, takže na pivotu válce nezáleží.
- a) **Nanite + TSR na meshi připojeném ke kameře.** Příznak: kokpit a displeje se při rychlém
  letu rozmazávají a „trhají“. Příčina: Nanite dává špatné motion vectory pro mesh, který se hýbe
  s kamerou. S `r.Nanite 0` byl obraz ostrý. Řešení: `no_nanite_parts: ["Interior"]` (interiér bez
  Nanite) a `MotionBlurAmount 0` na kokpitové kameře.
- b) **Duchy čísel na displejích.** Čísla, která se mění každý snímek, TSR prolíná (dvě desítky
  přes sebe). Nepomohlo:
  - translucent materiál + responsive AA: zdvojené řádky, protože nemá velocity;
  - „after motion blur“: rozmazané;
  - TSR cvary.

  Pomohlo: opaque + pixel animation, stav 5 Hz a kvantování během změny (7.1). **Zbývá:** při
  afterburneru nebo tvrdém brzdění se na okamžik prolnou dvě desítky.
- c) **RT se neustále přestavoval** (blikání, hitch) kvůli FOV kicku při boostu. Měřítko teď
  bereme jen ze šířky okna a práh je 0,099.
- d) **`_fresh_material` znovu použije existující asset** a nechá mu staré vlastnosti (materiál
  zůstal translucent). Blend mode a další klíčové vlastnosti vždy nastav explicitně.
- e) **Uncooked `-game`** kreslí nové materiály šedě. Vzhled posuzuj jen v zabalené hře (Shots).
- f) RT nemá mipmapy. Na menším rozlišení než ~1600 px může písmo na displejích zrnit.
- g) **Kreslení čar ve Slate je kvadratické s počtem dávek** (19. 9. 2026). Příznak: po přidání radaru
  a siluety lodi spadl kokpit z ~64 na ~31 FPS, herní vlákno +6 až 17 ms, GPU beze změny. Příčina
  (Unreal Insights: `Slate::AddLineElements` 6,5 ms na volání): každá změna **tloušťky** vyhlazené čáry
  (jiné parametry shaderu) nebo **vrstvy** začne novou dávku a každá dávka rezervuje sdílené pole vrcholů
  přesně o svou velikost – celé pole se zkopíruje. `GlowLines` kreslí čáru třikrát různou tloušťkou, tedy
  tři dávky na čáru. Řešení: v kreslených widgetech **jedna tloušťka a jedna vrstva pro všechny čáry**,
  stejné čáry kreslit za sebou, záři (`GlowLines`) jen na pár krátkých prvků. Barva dávku nerozbíjí (je ve
  vrcholech). **Upřesnění (19. 9. 2026 večer):** kopírování pole je drahé jen tam, kde se seznam prvků
  **nerecykluje**. Slate drží seznam prvků (a kapacitu polí) pro každé okno; `FWidgetRenderer::DrawWidget`
  ale pro každé kreslení vytváří **nové** `SVirtualWindow`, takže displeje začínaly pokaždé s prázdným
  polem a každá dávka ho realokovala (~50 µs na dávku; ve viewportu, kde se seznam recykluje, ~2 µs).
  Řešení: `UCockpitDisplayComponent` drží jedno okno (`DrawWindow`) a kreslí přes
  `FWidgetRenderer::DrawWindow` – „Display draw“ 5,6 → 1,9 ms na vykreslení, `AddLineElements` 2,75 →
  0,62 ms. Pro každý další widget kreslený do render targetu platí totéž: **nikdy `DrawWidget` v každém
  snímku, vždy trvalé okno.** Navíc všechny čáry kreslených prvků (`SpaceHudStyle::PaintLine`) čekají ve
  frontě a kořen (`USpaceFlightHud::NativePaint`) je vydá seřazené podle vrstvy a tloušťky – dávek čar je
  polovina (HUD 132 → 63). Přepínače pro A/B: `space.CockpitKeepWindow`, `space.HudLineBatch` (obojí 1),
  počet dávek ukazuje `stat SpaceHud` (Line batches).
- i) **Ostrost obrazu hlídej přes `stat unit` → RenderRes.** Hra běžela půl roku na 50 % rozlišení
  (`sg.ResolutionQuality` v `GameUserSettings.ini`, auto-detekce enginu) a všechno bylo měkké. Nové
  nastavení je 100 % a stará konfigurace se jednou převede (`USpaceUserSettings::MigrateSettings`).
  Když se posuzuje ostrost čehokoli, nejdřív zkontroluj RenderRes ve snímku.
- h) **FPS ve snímcích hned po přesunu lodi nic neříká.** První snímek scénáře a snímky po velkém přesunu
  (jiná výška, přistání) mají herní vlákno 20–30 ms, protože se staví terén. Na výkon se dívej se
  `settle` ≥ 2 s a srovnávej A/B ve **stejném balíčku** (konzolový přepínač v poli `console`), každou
  variantu v samostatném spuštění hry – průměry `stat` se jinak mezi snímky přelévají.

### Profilování zabalené hry (Unreal Insights bez GUI, k nástrahám 9.2g a 9.2h)

```powershell
# trace (hra se scénářem snímků, pak se sama ukončí)
& C:\gamespace\Builds\Gamespace\Windows\gamespace.exe /Game/Maps/TestSpace -windowed -ResX=1600 -ResY=900 -nosplash -unattended `
  -ShotList="<scénář.json>" -ShotOut="<složka>" -trace=cpu,frame -statnamedevents -tracefile="<soubor>.utrace"
# export statistik časovačů do CSV (čekat na konec procesu: Start-Process ... -PassThru, WaitForExit)
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealInsights.exe" -OpenTraceFile="<soubor>.utrace" -NoUI -AutoQuit `
  -ExecOnAnalysisCompleteCmd="TimingInsights.ExportTimerStatistics <soubor>.csv"
```

CSV má sloupce `Name, Count, Incl, Excl, I.Avg…` v sekundách; seřaď podle `Excl`. Rychlejší orientace bez
trace: pole `console` ve scénáři s `stat unit`, `stat Slate`, `stat SpaceCockpit` – statistiky jsou vidět ve
snímku.

### 9.3 Obsah a cookování

- a) **Písmo v buildu chybělo.** Špatná cesta ve `DirectoriesToAlwaysStageAsUFS`: je relativní
  ke `Content`, tedy `UI/Fonts`. `Package.ps1` teď písmo kontroluje.
- b) **Assety načítané podle cesty** (zvuky, input) v buildu chyběly. Cooker je nevidí, proto se
  přidávají do `DirectoriesToAlwaysCook`. Nový adresář tam přidej a doplň kontrolu do `Package.ps1`.
- c) **Blueprint override zůstává.** Po odebrání hodnoty ze `_setup.json` ji v BP nastav
  explicitně.
- d) **Ručně dělané `IA_*` a `IMC_*` assety nikdy znovu nevytvářej.** Mění se jen skripty
  `add_*_input.py`, které je doplňují.
- e) **Příliš silné světlo v kokpitu** (stará bodovka 12 cd) dělalo celý kokpit šedým a plochým.
  Tmavý SC vzhled dělají slabé světlo, displeje jako zdroje a tint interiéru.
- f) **Šedá šachovnice přes celý interiér = materiál se v zabalené hře nezkompiloval.** Engine v
  takovém případě tiše nasadí `WorldGridMaterial` a v editoru je přitom všechno v pořádku. Dvě
  příčiny, obě v `M_KitTrim` (23. 9. 2026):
  1. **Chybí usage flag.** Naimportovaný mesh má zapnutý Nanite, materiál dělaný skriptem ne
     (`used_with_nanite`). Editor si flag doplní, až materiál na mesh přetáhneš myší; skript si ho
     musí nastavit sám (`used_with_nanite`, `used_with_static_mesh`, `used_with_instanced_static_meshes`).
  2. **Nepřipojený texturní parametr.** Sampler bez textury spadne na engine `DefaultTexture`, což je
     sRGB Color - pro sampler typu Normal nebo Linear Color je to **chyba kompilace**
     („Sampler type is Normal, should be Color"). Každému samplerovi nastav výchozí texturu
     odpovídajícího typu.
  Kde se to pozná: cook log `%APPDATA%\Unreal Engine\AutomationTool\Logs\...\Log.txt`, hledej
  „Failed to compile Material" - hlásí i konkrétní uzel. Log zabalené hry říká jen následek
  („missing usage flag", „Invalid shader map ID").

- g) **Barva materiálu nestačí, když světlo má opačný odstín** (23. 9. 2026, `interior_tune`).
  Modřejší gunmetal pod teplými světly (255, 238, 214) posunul B/R stěny jen 0,95 → 1,05, teplota
  světel 7000 K sama 0,95 → 1,06, obojí dohromady 1,26. Když má být povrch „studený“, lad' nejdřív
  světlo. A nižší metallic povrch zesvětlí, nezbarví – kov s bílým base colour je prostě stříbrný.
- h) **Díl z kitu lícem špatným směrem je z druhé strany neviditelný.** Unreal kreslí jednostranně
  (i když glTF kitu hlásí `doubleSided`), takže podlahová deska použitá jako strop nebo stěnový
  panel otočený ven zevnitř „neexistuje“ a prostor je otevřený do vesmíru (23. 9. 2026, nákladový
  prostor). Blender to v běžném náhledu neukáže. Kontrola: paprsky ze středu místnosti ven a
  u zásahu `normal.dot(směr) > 0` = rub (`build_steadfast_interior.py`, bod 60 v HANDOFF). Oprava: díl lícem
  dovnitř, nebo obložení za stěnou.
- i) **Kamera snímků za stěnou vidí dovnitř** – ze stejného důvodu (rub stěny je průhledný). Snímek
  pak vypadá v pořádku, ale ukazuje místnost „bez čtvrté stěny“. Kamery interiéru patří dovnitř.
- j) **Statické světlo za běhu nejde měnit setterem.** `SetIntensity`/`SetLightColor` světlo s
  mobilitou Static ve hře odmítnou (i s `r.AllowStaticLighting=False`). Ladicí příkazy proto píšou
  přímo do vlastností a volají `MarkRenderStateDirty()` (`SpaceInteriorTuning.cpp`, `SpacePostTuning.cpp`).
- k) **Průchod do cizího kitbashe má za stěnou další stěnu.** Otvor vyříznutý jen v rovině stěny
  ukázal v rámu dveří panel – shell měl 1 m za ní ještě vnější stěnu na konci přečnívající podlahy.
  A řez podle polohy bez kontroly normály smazal i podlahu v průchodu. Před řezem si vypiš plochy
  v celém objemu průchodu po materiálu a normále (bod 61 v HANDOFF) a mazej jen svislé.
- l) **Světlo za stěnou interiér nesvítí, jen se tak tváří.** Oranžová světla nákladového prostoru
  stála 40 cm za stěnou; když se přesunula dovnitř, stejných 200 lm najednou oteplilo celou
  místnost. Po přesunu světla měř znovu.

- m) **Konzolové příkazy snímku běžely dvakrát.** Runner nastavoval další snímek hned po uložení
  předchozího a znovu v jeho prvním snímku. U nastavení to nevadilo, přepínač (`space.Interior`)
  hráče poslal dovnitř a hned zpátky. Opraveno v `SpaceShotRunner.cpp`; příkazy scénáře ať jsou i tak
  pokud možno idempotentní.
- n) **Rám dveří z kitu má průchod jen 70 % výšky.** `Door_Frame_Square` je 5 m, ale průchod 3,5 m;
  po zmenšení na palubu 2,4 m zbyl průchod 1,4 m a postava by neprošla. Než díl použiješ jako
  průchod, změř jeho otvor (vrcholy, ne bounding box). Rámy jsou teď procedurální.
- o) **Headless Python v UE:** `StaticMeshEditorSubsystem` tam není (vrací `None`) – Nanite se vypne
  `mesh.set_editor_property("nanite_settings", …)`, což mesh přestaví samo. `rerun_construction_scripts`
  v Pythonu neexistuje – co má C++ herec přepočítat, vystav jako `UFUNCTION(BlueprintCallable)`
  (`ASpaceSlidingDoor::LayoutLeaves`). `get_relative_location` není; `get_editor_property("relative_location")`.

- p) **Blikání bez zjevné příčiny = dvě plochy v jedné rovině.** Kitbash může mít díl dvakrát (bedna
  na podlaze a stejná napůl zapuštěná) nebo stěnu přesně na místě cizí stěny. Na snímku to nepoznáš,
  jen v pohybu. Najdi to měřením (`flicker_check`: stejná kamera 8×, co se mění, bliká) a v geometrii
  (plochy se stejnou rovinou z různých kusů, které se překrývají). Mazat jen skutečné kopie (stejný
  obrys) – „každý díl, který se s jiným překrývá“ smazal i podlahu, protože dlaždice se překrývají.
- q) **Díry se hledají paprsky, ne očima.** `find_interior_holes.py`: z mřížky bodů ve všech směrech,
  rub plochy se prochází (Unreal ho nekreslí), únik = díra. Body uvnitř rekvizit (sloup, pult) dávají
  falešné úniky – vyřazuj body blíž než 30 cm ke geometrii. Škvíry v rozích, kde se panely jen
  dotýkají hranou, zavírá tmavý plášť za stěnami.
- r) **Stíny lokálních světel jsou drahé.** 22 stínovaných světel byla většina snímku (15 ms ze 18).
  Doplňková světla (akcenty, displeje) bez stínů, pracovním světlům dosah jen na vlastní místnost.
- s) **Blender bmesh: `faces.new()` má nulovou normálu**, dokud nezavoláš `bm.normal_update()`.
  Otočení ploch „k místnosti“ podle normály bez toho nic neudělá. Stejně tak nové vrcholy mají
  `index` −1 až do `bm.verts.index_update()` – mapování obrázku podle indexu vrcholu se jinak rozsype.
- t) **`set_collision_enabled()` v editorovém skriptu se neuloží** s levelem (herec v testu měl kolizi
  dál). Uloží se kolizní profil: `set_collision_profile_name("NoCollision")`.
- u) **Průsvitné a aditivní materiály nesmí na Nanite mesh** – sklo i hologramy jsou vlastní GLB,
  import jim Nanite vypne (`nanite_settings`).
- w) **Piny uzlů materiálu v Pythonu mají vlastní jména:** `Power` má `Base`/`Exp`, ne `A`/`B`;
  `TextureSample` bere souřadnice na pinu `UVs`, ne `Coordinates`. `connect_material_expressions`
  při špatném jménu jen vrátí False – skript musí chybu ohlásit (`link()` v `import_interior.py`).
- x) **Meshy a „celá sestava“:** zadání „pult do kokpitu“ vrátilo celý kokpit s oblouky a sedadly; ani
  „samostatný blok, nic jiného“ nedalo nízký pult, ale skříň. Samostatné předměty (sedadlo, boční panel,
  skříň) umí dobře, přesný tvar na míru ne. Každý díl si prohlédni ze tří stran (render v Blenderu) dřív,
  než ho zapojíš; co nesedí, použij jinde nebo zahoď.
- y) **Opotřebení podle normálové mapy funguje jen na kitu.** Procedurální díly mají v materiálu kitu
  UV na náhodném místě atlasu, takže „hrana“ z normálové mapy padne doprostřed plochy. Proto slabé
  opotřebení a nic mimo hrany.
- z) **Text v obrázku z AI:** GPT Image 2.5 (Scenario) napsal všech 16 nápisů atlasu přesně. Zadávej
  pevnou mřížku („exact 4 by 4 grid, one element centered in each cell, black background“) – políčka
  se pak dají vyříznout výpočtem bez ručního ořezu.
- aa) **Jména materiálů ze stavitele rozhodují o vzhledu v Unrealu.** `import_interior.py` přiřazuje podle
  jména: „black“ → tmavý plast, „lamp“ → svítidlo, „light“/„screen“ → oranžově svítící pás, „glass“,
  „m_holo_“, „white“, „strip“. Nový materiál pojmenuj tak, aby nechtěně nepadl do svítící skupiny.
- v) **Žádná jména ze Star Citizenu** v obsahu (stanice, lodě, firmy) – vzhled ano, cizí značky ne.

### 9.4 C++ a UHT

- a) **Unity build, kolize jmen.** `ModeColor` v `SpaceFlightHud.cpp` a `SpaceDebugHUD.cpp` spadl
  jen v herním targetu. Statické pomocné funkce a konstanty v .cpp pojmenovávej jedinečně
  (proto `MasterModeColor`).
- b) **`Points.Add(Points[0])` padá.** TArray se při realokaci přesune a reference neplatí.
  Nejdřív prvek zkopíruj do lokální proměnné.
- c) **C4458: lokální proměnná `Slot` zastiňuje člen** `UWidget::Slot`. Ve widgetech `Slot`
  nepoužívej jako název proměnné.
- d) **UHT: parametr `UFUNCTION` se nesmí jmenovat jako vlastnost třídy.** Přejmenuj parametr.
- e) Nativní třídy: CDO hodnoty se nekopírují do instancí, assety načítej v konstruktoru.
- f) Pohyb pawnu sweepuje jen root komponentu (`HullCollision`).

### 9.5 Python v UE

- a) `unreal.Rotator(a, b, c)` je poziční **roll, pitch, yaw**. Používej keyword argumenty.
- b) Struct wrappery neberou keyword argumenty v konstruktoru.
- c) Commandlet:
  - traces a sweepy nezasáhnou;
  - animace potřebují `++GFrameCounter`;
  - shadery se nekompilují.
- d) Vlastnosti jen `Config` bez `BlueprintReadOnly` nebo `Edit` nejsou z Pythonu vidět.
- e) **`unreal.Color(255, 238, 214)` je modrá.** FColor má pořadí **B, G, R, A**, takže poziční
  argumenty barvu prohodí - světla v nákladovém prostoru svítila modře. Používej keyword argumenty
  (`unreal.Color(r=255, g=238, b=214, a=255)`).
- f) `spawn_actor_from_object` v headless editoru padá (EXCEPTION_ACCESS_VIOLATION). Stabilní cesta
  je `spawn_actor_from_class(StaticMeshActor)` a `set_static_mesh` dodatečně.
- g) `asset_import_data` z Interchange nemá `source_data`; starší skripty na ní spadnou.
- h) **Jméno herce (label) v zabalené hře neexistuje.** `set_actor_label` je jen editor; C++ v buildu
  herce podle něj nenajde. Co má hra najít (konzolové příkazy, logika), dostane **tag**
  (`set_editor_property("tags", [unreal.Name(...)])`) – tak to dělá `import_interior.py`.

### 9.6 Blender pipeline

- a) **Rám displeje se otočil dvakrát.** Rotace byla v placement matici i v osách `u`/`v`.
  `add_displays` dostává matici bez rotace.
- b) **Otvory rámečků AI modelu nejsou obdélníky** (lichoběžníky, zkosené rohy). Proto `corners`
  místo `rect` a ladění z oka (kapitola 3).
- c) **Jednostranný trup.** Zevnitř je průhledný, proto `lining`. U oka blízko křídla je vidět
  hrubá geometrie.
- d) **Pravý displej má vlevo dole zubatou hranu** rámečku z AI textury. Neopravené.
- e) Oko je navržené pro 16:9 a FOV 88°. Měření z jiného FOV nesedí.
- f) **Render z `blender -b` zmizel.** Relativní `scene.render.filepath` (`Saved/...`) Blender bere
  vůči .blend, ne vůči aktuálnímu adresáři. Ve skriptech dělej `os.path.abspath` výstupní složky.
- g) **IoU siluety bylo nesmyslně nízké, i když díl seděl.** Výřez AI modelu obsahoval kousky
  pylonu, normalizace podle bboxu tím zvětšila a posunula masku. Dva rendery ve stejných
  souřadnicích porovnávej ve světovém prostoru (`silhouette_compare.py --align world`, výchozí)
  a díl vyřízni i válcem (`--crop-cylinder yc,zc,r`).
- h) **Poloměr změřený jako maximální vzdálenost vrcholů od osy je o ~5 % větší**, protože započítá
  výstupky a greebly AI modelu. Měř z masky (střed a rovný okraj), ne z extrémů vrcholů.
- i) **Rovný díl kitu na zakřiveném plášti odstává na krajích** (průhyb = šířka² / (8 · r); víko
  0,7 m na r 1,12 m ≈ 5 cm). Velké díly je třeba ohnout podle povrchu.
- j) **Python z heredocu přes nástroj Bash dostane jiná zpětná lomítka.** Nástroj mění `\\` na `\`
  i v uvozovaném `<<'EOF'`: `'\\n'` se stane skutečným koncem řádku, `split('\\')` neuzavřeným
  řetězcem. Python, ve kterém jsou zpětná lomítka, zapiš nástrojem Write do scratchpadu a spusť soubor.
- k) **AI pohledy „téže lodi“ mají jiný půdorys a zepředu jsou šikmo seshora.** Obrázkový model
  z jednoho hero obrázku tvar domýšlí (GPT Image 2.5: křídla o třetinu kratší a šípová dopředu).
  Vodicí silueta jako druhá reference a kontrola `silhouette_compare.py views` (ship-pipeline 2a).
- l) **Maska konceptu zabrala polovinu obrázku.** Model nakreslil podlahu a stín i přes „no floor“.
  Před měřením Higgsfield `remove_background` (alfa). A pozor, aby hero render patřil ke stejné
  verzi modelu, se kterou se měří.
- m) **Světlý trup na světle šedém pozadí: děravá maska, IoU koncepce shora jen 0,56.** Vyříznutí siluety podle
  mediánu okraje nerozliší lomenou bílou od šedé. Generuj na kontrastním pozadí (tmavé pro světlý trup),
  nebo měř verzi po `remove_background` (`*_cut.png`).
- n) **Na renderu lodi velké šedé plochy přes křídla.** Renderovaly se kolizní obálky UCX. `render_ship_views.py`
  je skrývá (`hide_render`); vlastní render skripty musí taky.
- o) **Po vyříznutí dílu recept běžel 10 min a trup dostal obří ploché trojúhelníky.** `holes_fill` na AI meshi
  s otevřenými hranami spojil okraje křídel a gondol. Díl s `"fill_holes": false`.
- p) **UCX „Not convex“, i když je obálka konvexní.** Titěrné plošky (0,0003 m²) z téměř shodných extrémů mají
  nepřesnou normálu. `kdop_hull` teď slučuje extrémy do 10 cm a zahazuje vrcholy nejkratších hran.
- q) **Test podvozku: sockety 2,5 cm nad spodkem boxu.** Box je vycentrovaný na aktéra, trup posunutý k pivotu
  (`Hull_RelativeLocation_cm`). V prostoru meshe je spodek boxu −extent − posun.
- r) **AI loď ve hře rozmazaná, flekatá a „špinavá“, i s 4K texturou.** UV atlas využíval 0,4 % textury, protože
  mesh byl polévka rozpojených trojúhelníků a margin na každý ostrůvek sežral místo. Svařit (`weld_m`),
  unwrap bez marginu a `pack_islands`, pak měřit využití atlasu. Pak čistý lak (`repaint_ship.py`), ne AI barvu.
- s) **Oranžové pruhy jako roztřepené „plamínky“.** Zóny se zařazovaly po celých trojúhelnících. Tenké pruhy
  vyřezávat po texelech z AI kresby (medián 5 px, práh).
- t) **Blender nemá Pillow ani SciPy.** Jeho Python má ale stejnou verzi jako systémový (3.13):
  `repaint_ship._borrow()` přidá systémové site-packages.
- u) **AI image-to-3D loď po přebarvení pořád „roztavená“.** Geometrie je z AI, lak ji nespraví. Stavět exteriér
  z obrysů výkresu (`hs_build_ship.py`).
- v) **Díl postavený průnikem obrysů je uříznutý** (Wayfarer: ploutev končila ve 3,25 m místo 4,0 m). Obrysy
  výkresu si odporovaly: šikmá ploutev byla shora nakreslená užší, než je. Opravit výkres, ne model.
- w) **Sklo kabiny pruhované.** Trup kopíruje horní hranu obrysu kabiny přesně a test bodu v polygonu na hraně
  kolísá. Testovat jen proti spodní hraně a trup předtím rozříznout podél čáry (`cut_polyline`).
- x) **Detaily kitu ve hře chybí.** `new_from_object` zahodí instance z geometry nodes. Do instanceru přidat
  Realize Instances (`hs_assemble_ship.py` to dělá).
- y) **Díl kitu (poklop) na střeše stojí šikmo.** Jediný paprsek trefil stěnu panelové drážky. `place_greebles`
  bere průměr normál 7 paprsků přes stopu dílu; díly nedávat na spáru.
- z) **Deska vybraná podle středů plošek má schodovité okraje.** Plošky trupu na hraně oblasti prošly jen zčásti.
  `hs_detail._cut_region` plošky nejdřív rozřízne rovinami hranic oblasti (`bisect_plane`).
- aa) **Žlab na hřebeni střechy snížil siluetu z boku.** Trubky v něm musí sahat až k povrchu. Silueta se měří po
  každé změně tvaru (`silhouette_compare.py`, nesmí klesnout).
- ab) **Decal nebo pás visí ve vzduchu přes hranu střechy.** Bod mřížky minul povrch nebo skočil na jinou plochu.
  `hs_decals.py` takový decal vynechá a vypíše, pás rozdělí na souvislé běhy.
- ac) **Tmavé mřížky mají na tmavém krytu světlý rámeček.** Mip bleed přímé alfy: v menších mipech se průhledná
  (světlá) barva mísí do okraje. V atlasu rozšířit barvu do průhledných texelů (`dilate_colour`).
- ad) **Vertex colour opotřebení zalije celou plochu.** Hodnota ve vrcholu se interpoluje přes každou plošku, které
  se dotýká. Hranu značit jen u vrcholů obklopených malými ploškami (prostřední řada zkosení).
- ae) **Vertex colours se neimportují, i když je FBX má.** Legacy FBX reimport existujícího assetu bere volbu
  z uložených import dat assetu (IGNORE). `import_ship.py` ji nastaví i tam. `has_vertex_colors()` u Nanite meshe
  v commandletu vrací False, ověřuje se volba importu, nebo snímek.
- af) **Pravá gondola má spáry jinde než levá.** Rotační díl pro pravou stranu dostal stejnou fázi panelů. Fáze
  pro zrcadlo je `(180 − fáze) mod rozteč`.
- ag) **Volná kamera snímku je „nakloněná“.** Nad kulatou planetou není osa Z světa „nahoru“ lodi. Kamera
  v prostoru lodi (`camera_local`) bere up vektor lodi.
- ah) **Kolem každého decalu je vidět obdélník.** Plochá stopa decalu přepisuje drsnost laku (0,32 proti 0,45).
  Alfa strukturních decalů jen na prvcích (`decal_library.feature_alpha`).
- ai) **Výklenek vyříznutý do zadní stěny je černá díra, skrz kterou je vidět terén.** Konec loftu je jeden
  n-úhelník a inset a extrude na něm nevytvoří uzavřené stěny. Na zadní stěnu jen desky (výběr podle obálky plochy,
  `_box_touches`) a mřížky jako decaly.
- aj) **Deska na n-úhelníku nevznikla („no faces“).** Předvýběr podle středu plochy minul n-úhelník, jehož střed
  leží jinde. Vybírat podle překryvu obálky.
- ak) **Štítek visí přes schod okraje desky.** Kontrola normál ho nepozná, protože obě plochy mají stejný směr.
  `laid_grid` odmítne i výškový skok přes 12 mm mezi sousedními body.
- al) **Doprovodné decaly (štítek, madlo u poklopu) se nevytvořily.** Kruhový test překryvu je u protáhlých
  decalů příliš přísný. Test orientovaných obdélníků (SAT) a doprovodné decaly bez testu.
- am) **Čísla panelů na svazích a střeše jsou vzhůru nohama.** Rám decalu: na bocích a svazích „nahoru“ po
  povrchu, na střeše a břiše podle bližší strany lodi.
- an) **Příkaz bash uvnitř PowerShellu se tiše nespustil** (uvozovky), import pak vzal staré FBX. Build v Blenderu
  pouštět nástrojem Bash, import a balení nástrojem PowerShell.
- ao) **Tvarovaná křídla o třetinu tenčí, silueta zepředu klesla.** Profil NACA normalizovaný číslem 0,15014.
  Správná závorka v 30 % tětivy je 0,10003.
- ap) **Křídla se nepřestavěla („shaped: []“).** Bmesh vytvořený z ploch nemá normály, a osy desky vyšly nulové.
  Po stavbě zavolat `bm.normal_update()`.
- aq) **Silueta shora klesla o spáry mezi díly křídla.** Pod díly patří tmavé jádro bez spár.
- ar) **„Noc“ se ztlumeným sluncem je pořád den.** `space.SunDir 25 45` dá slunce pod horizont, `space.Sun Intensity 0`
  a `space.Sky Intensity 0.03`. Obloha levelu přesto zůstává světlá (skybox nesleduje slunce).
- as) **Chromová náběžná hrana ploutve je flekatá.** Leštěný kov 0,28 odráží šum Lumenu. Náběžné hrany tmavým
  materiálem.
- at) **`MaterialProperty.MP_CUSTOM_DATA0` neexistuje** (clear coat z Pythonu). Materiál s `use_material_attributes`
  a uzlem MakeMaterialAttributes (piny ClearCoat, ClearCoatRoughness).
- au) **Livrej B a C vypadaly jako zebra.** Zóny livreje sdílely barvu se sekundárním lakem desek. Vlastní
  `LiveryColor`.
- av) **Pryžová těsnění jako hrubá černá mřížka.** Při laku 0,7 a těsnění 0,1 je poměr 7×, na snímku černá. Těsnění 0,28.
- aw) **Sklo na kopuli v hlavním Nanite meshi.** Průsvitný materiál Nanite nekreslí. Funkční díly jen neprůhlednými
  materiály.
- ax) **Nové funkční díly ubraly siluetu** (anténa 0,6 m, objímky zbraní). Trysky zapustit, antény ≤ 0,3 m,
  objímky ≤ 1,15 × hlaveň.
- ay) **Pilotní pohled nahoře černý, sklo kabiny zakryté.** Interiér se stavěl před oddělením kabiny z trupu,
  obložení nad parapetem zkopírovalo i plochy budoucího skla. Blok `interior` v `hs_build_ship.py` běží až po
  rozdělení kabiny.
- az) **Interiér přesvícený do bíla** (průměr snímku 0,75, cíl SC 0,13–0,23). Automatická expozice
  místnost s bodovkami 110 cd neztmaví. Bodovky 20 cd, tmavé albedo (≤ 0,13), měřit `measure_look.py`.
  B/R pod 0,72 = příliš oranžové světlo, (1, 0,93, 0,86) dává 0,79.
- ba) **Testy kokpitu padaly po přidání interiéru.** Kontroly předpokládaly Vanguard: part `Interior` jen
  s kokpitem, 4 motory, slot `CanopyFrame`. Měřit vůči partu `Screens`, počet motorů brát z manifestu
  (`SOCKET_Engine*`), `Display_` sockety hledat na všech meshích lodi.
- bb) **Interiér z procedurálních boxů vypadá jako „prázdný byt nebo kancelář“** (autor o Wayfareru v1).
  Příčina: stavěl jsem místnosti rovnou z půdorysu stejným postupem jako trup (`hs_*`, boxy) a
  `Docs/AssetPipeline_Modular.md` jsem nepřečetl. Postup pro interiéry v něm je: modulární kit (Quaternius,
  CC0) jako nosná konstrukce, procedurální přesný detail navíc. Ze skillu ship-interior jsem si vzal jen
  „kit Quaternius je dočasný, low-poly stěny jsou vidět“ a kit jsem vyřadil úplně. Z exteriéru jsem nepřenesl
  nic: vrstvy, decaly ani variaci panelů. Řešení: před interiérem přečíst AssetPipeline_Modular.md a udělat
  rozbor referencí interiéru; kit jako strukturu a trim textury, procedurálně jen přesné díly, decaly
  interiéru a světlo s kontrastem (`hs_interior_kit.py`).
- bc) **Díly kitu mezi sebou prosvítaly oblohou.** Trup zevnitř UE nekreslí a mezery mezi díly kitu šly až
  ven. Za kit dát uzavřený tmavý plášť (stěny a strop, `shell()`).
- bd) **Stěny z kitu v UE černé**, i když v Eevee byly vidět. Reflektory svítily jen kolmo dolů a světelná rýha
  je pro Lumen malá. Do každé rýhy přidat bodové světlo (12 cd), stěny pak čtou.
- be) **Decaly v interiéru zrcadlené nebo vzhůru nohama.** Decal promítá podél −X a text se orientuje podle
  roll. Ověřené rotace `[pitch, yaw, roll]`: pravobok (vnitřní stěna čelem k +Y UE) `[0,-90,90]` + `flip_u`,
  levobok `[0,90,90]` bez flipu, přepážka čelem dozadu `[0,180,-90]` + `flip_v`, čelem dopředu `[0,0,-90]` +
  `flip_v`, podlaha `[90,0,0]` (U podél lodi). Velikost u stěn `[hloubka, půl výšky, půl šířky]`.
- bf) **Díly kitu ztratily vzhled po assemble.** Assemble dělá smart UV unwrap všem partům; trim sheet potřebuje
  původní UV. Kit a jeho procedurální díly s kubickým UV jdou do partu `InteriorKit`, který se nerozbaluje
  (jméno objektu `_IntKit_`).
- bg) **Kit objekty spojené joinem mají rozbitá UV**, když se UV vrstva nejmenuje stejně. Nové bmeshe v kit
  materiálu musí mít vrstvu `UVMap` (jako glTF import), `hs_interior_kit._uv_layer`.

- bh) **Pod nohama pilota prosvítal terén.** Podlaha kokpitu byla jedna plocha, `finish()` přepočítá normály
  a samotnou plochu otočil dolů (UE ji nekreslí). Podlahu stavět jako uzavřenou desku (`extrude_face_region`).
  Totéž platí pro každou otevřenou plochu v bmeshi, který jde přes `recalc_face_normals`: deska kokpitu se
  proto dělá `solidify`.
- bi) **Moduly MFD seděly nízko a byly uříznuté.** Vlastní pravidlo testu „displeje ≥ 12° pod okem“ bylo přísnější
  než HUD (končí ~5° pod okem). Hranice podle skutečného HUD: 8°.
- bj) **Rám kabiny tmavý proti obloze i přes světlý lak.** Expozice kokpitu −0,7 EV (z Vanguardu) a slabé světlo na
  rámu. −0,2 EV, emise displejů o 2^0,5 níž, bodová světla na rám z ramen a od sloupků.
- bk) **Pruhované stínování obložení kabiny.** Obložení kopíruje fasety trupu s hladkými normálami přes ostré
  hrany a některé plochy měly obrácenou orientaci. Normály ke středu kokpitu + `set_sharp_from_angle(25°)`.
- bl) **Oranžová linka přeškrtla horní okraj displejů.** Linka 3 cm pod hranou desky vedla i přes pole MFD, kde je
  nad sklem jen 2 cm. Na polích displejů linku vynechat.
- bm) **Tenké proužky oblohy podél okrajů skla a ve spárách interiéru.** Příčiny byly tři:
  - pásek ostění byl solidifikovaný a `hp.finish()` ho spojil do nemanifoldního pruhu s přepočtenými normálami;
  - plochy obložení se otáčely „ke středu kokpitu“, což na strmých plochách u skla selhalo;
  - trup má na střeše střídavě obrácené normály.

  Oprava:
  - ostění postav oboustranně jako samostatné plochy bez spojování;
  - plochu obložení otoč, když trup leží blíž ve směru normály než proti ní;
  - zbytek interiéru dostal tmavý vnitřní plášť 5 cm pod trupem (`Int_HullSkin`);
  - oblasti obložení a pláště vybírej podle vrcholů, ne podle středů ploch, a nech je překrývat.

  Hledání: `GEOCHECK_DEBUG=1` přidá k masce děr i render s náhodnou barvou po objektech. Paprsek přes bílý pixel ukáže, co zasáhne (rub = obrácená plocha).
- bn) **Díl „trčí z trupu“, i když výška sedí na ose.** Trup se ke stranám snižuje. Výška stropu nebo parapetu
  změřená jen na ose (y = 0) nebo v jedné výšce pustí rohy ven. Měř přes celou šířku dílu a v horní i dolní výšce;
  parapet konči u obložení (3 cm pod trupem), ne za ním.
- bp) **Málo výhledu z kokpitu, i když je sklo velké.** Spodní hrana skla ležela 1–1,3 m nad okem pilota a pilot koukal do obložení. Nejdřív změř výšku oka proti pásu skla (`eye_view_metrics.py`, případně rozmítnutí výšky oka). Oko patří do pásu skla: zvedni kokpit, exteriér nech. Díly exteriéru, které leží na skle (trysky RCS), jsou zevnitř velké tmavé bloky.
- bq) **Posunutá tmavá kopie textu na displeji, jen ve dne.** Vypadala jako duch TSR nebo odraz. Byl to stín: maskovaný materiál displeje vrhá stín podle masky a slunce kreslí písmena na desku za sklem. Komponenta displejů má `cast_shadow` false. Rozliš podle svícení: jen ve dne = stín, i v noci = TSR nebo odraz.
- br) **Štítek ovladače chybí (`INTDECALS labels_failed … edge`).** Placer klade decal jen na rovnou přední plochu. Příčiny:
  - modul zapadl do vyboulené nebo zalomené fascie → `hs_cockpit.seat()` ho postaví nad nejvyšší bod pod obrysem;
  - na vodorovné desce Placer natočil štítek podle světa přes ovladač → štítky modulu nesou rámeček modulu (`frame`);
  - paprsky `lay` z 12 cm trefily jinou geometrii nebo rub → štítky kladou z 2 cm a rubové plochy se přeskakují;
  - dlouhé slovo (QUANTUM) přesahuje buňku → měřítko se zmenší na `max_w`.
- bs) **Nový objekt v interiéru má v herním blendu nesmyslné vrcholy (loď „6·10¹² m“ v exportu).** Příčiny:
  - `hs_build_ship.finish()` přidá Bevel a WeightedNormal každému objektu bez modifikátoru;
  - assemble všechny modifikátory aplikuje a Bevel na hustém meshi s degenerovanými plochami vyrobí smetí.

  Hologram proto nese modifikátor Decimate: `finish()` ho vynechá a assemble decimaci aplikuje. Mesh z cizích dílů ber vyhodnocený (`evaluated_get().to_mesh()`), protože greeble jsou bodová mračna s instancerem. Nepoužívej `meshes.new_from_object` s následným mazáním.
- bt) **Nový podagent „not found“ (`Agent type 'visual-critic' not found`).** Claude Code sleduje jen složky agentů, které existovaly při startu session. První soubor v nové `.claude/agents/` se proto načte až po restartu. Do té doby spouštěj read-only agenta (Explore) s doslovným textem zadání a zapiš to do recenze.
- bu) **V noci je obloha pořád světlá, i když slunce zapadlo.** Namalovaný gradient `ASkyDome` na slunce nereagoval, jen `SkyBrightness` z prostředí. Oprava v `SkyDome.cpp`: jas × `Lerp(NightSkyFloor 0,02, 1, Day)`, kde `Day` = `SmoothStep(-0,12, 0,08, výška slunce)` × poměr intenzity slunce k výchozí.
- bv) **Metrika „nejširší sloupek“ hlásila 2,3 %, i když na obraze žádný sloupek nebyl.** Počítala i zářez v linii parapetu. `eye_view_metrics.py` teď bere jen svislé členy: sloupek je tmavý běh, nad kterým loď pokračuje aspoň 8 % výšky obrazu.
- bw) **Nadpisy středových displejů useknuté z oka pilota.** Tři různé příčiny, každou našel teprve ray cast z oka na horní hranu skla:
  - při šířce 11 cm zašly vnější hrany za vnitřní hrany MFD podů (zpět na 9 cm);
  - clona nad sklem (`glass_panel`, `visor`) předsahovala k oku;
  - horní přední hrana těla sloupku ležela o 2 cm blíž k oku než horní hrana skla (hlava posunuta na `ped_x − 0,13`).

  Když je text na displeji v zabalené hře useknutý, nejdřív vylouči texturu (odsazení stránky v `SpaceFlightHud.cpp`), pak střílej paprsky z `SOCKET_Cockpit` na body skla (0,7–0,99 výšky) a vypiš zasažený objekt, materiál a normálu.
- bx) **`stat gpu` se v zabalené hře neukáže.** Chce `r.GPUStatsEnabled 1` před `stat gpu`. `space.KitReset` nevrací slunce, proto měření výkonu patří před noční snímek.
- by) **`import_ship.py` hlásí „manifest has errors“, i když kontrola manifestu prošla.** Relativní `GAMESPACE_SHIP_MANIFEST` se v commandletu vyhodnotí vůči `Engine\Binaries\Win64`. Dávej vždy absolutní cestu.
- bz) **Modré skvrny u spodního okraje pohledu pilota.** Bodová světla desky (světlo displejů na okolí) seděla 12 cm pod MFD u kolenního panelu a vypálila hot spot. Světlo displeje patří před sklo ve výšce jeho středu (~20 cm), ne k nejbližšímu povrchu.
- ca) **Pilot nevidí sklo kanopy, i když lodi s interiérem svítí odlesky na skle ve snímcích z volné kamery.** `ASpaceshipPawn::bHideCanopyInCockpit` je výchozí `true` (pro lodě bez interiéru, kde skořepina sedí 13 cm od oka). Loď s interiérem ho vypíná v setupu (`pawn.hide_canopy_in_cockpit: false`).
- cb) **Sklo přes celý pohled pilota stálo 3 ms GPU (73 → 57 FPS).** Ostrý odraz Lumenu na průsvitných plochách (`r.Lumen.TranslucencyReflections.FrontLayer.Enable`) +1,9 ms, osvětlení Surface ForwardShading všemi světly kabiny +1,1 ms. Oprava:
  - `UpdateViewCollection` vypíná `FrontLayer`, když je kamera uvnitř lodi;
  - `M_Ship_Glass` je Surface TranslucencyVolume.

  Výsledek +0,58 ms. Průsvitný materiál, který může zaplnit obrazovku, vždy změř `stat gpu` (WORKFLOW bx).
- cc) **Hologram jako „rozmazaná modrá hmota“.** Decimovaná kopie celého exteriéru nesla všechny vnitřní plochy (rub trupu, spodky greeble), aditivní materiál je sečetl přes sebe. Hologram je teď vnější obálka z voxelů (`hs_cockpit._envelope`). Nástrahy:
  - `bmesh.ops.smooth_laplacian_vert(preserve_volume=True)` voxelové schody nevyhladil;
  - prosté průměrování (`smooth_vert` 0,5) smrsklo ploutev;
  - funguje Taubin (střídavě 0,5 a −0,53).

  Hloubka skenovacích linek na hladké obálce kreslí vlnité vrstevnice, proto ScanDepth 0,12.
- bo) **Kontrola geometrie před každým předáním:** `python Tools/Tests/test_ship_geometry.py` (Blender headless na
  `<Loď>_HS_Game.blend`, ~15 s): zrcadlené decaly, plovoucí díly, průniky, placeholdery, díry viditelné hráči.
  Musí projít (autor 25. 9. 2026).


---

## 10. Kam dál (priority k 19. 9. 2026)

Menší kroky, podle pořadí:

1. ~~Třetí displej ve středním sloupku~~ – hotovo 19. 9. 2026: RADAR nahoře, SELF STATUS dole
   (HANDOFF kapitola 5, bod 31).
2. ~~Přepínání stránek MFD~~ – hotovo 19. 9. 2026 (F1 / F2, HANDOFF kapitola 5, bod 32). Navazuje:
   přepínání myší jako v SC (režim interakce, klik na tlačítko displeje) a stránky zbraní, štítů a
   energie, až budou systémy.
3. ~~Detail lodi zblízka~~ – hotovo 20. 9. 2026 (detailní vrstva materiálu, trup 1 mil. trojúhelníků,
   HANDOFF bod 33). Navazuje: decaly a nápisy, lepší zdrojové modely z Meshy/Higgsfield.
4. ~~Hrany trupu (zkosení, vážené normály)~~ – změřeno 20. 9. 2026 a **zahozeno**: trup z Meshy má
   92 % hran pod 36° (organický sken, ne rovné panely), takže ostrejší úhel i 2mm bevel změnily jen 1 %
   pixelů. Hrany budou dávat smysl až u modelů s rovnými panely.
5. ~~Světlo a post scény~~ – hotovo 20. 9. 2026 (kapitola 11, HANDOFF bod 36).
6. ~~Okluze a kavita na trupu~~ – hotovo 20. 9. 2026 (HANDOFF bod 38): v pečených texturách žádná
   okluze nebyla, `Tools/Blender/bake_ship_ao.py` ji dopeče.
7. ~~Nápisy a výstražné pruhy~~ – hotovo 20. 9. 2026 (HANDOFF bod 39): decaly ze seznamu v setupu lodi.
   Navazuje: víc nápisů a další místa (zatím jich je sedm).
8. ~~Panelové spáry~~ – hotovo 20. 9. 2026 (HANDOFF bod 40): dlaždicový list triplanárně v prostoru lodi.
9. ~~První zóna materiálu~~ – hotovo 20. 9. 2026 (HANDOFF bod 41): spálený plech u trysek z polohy
   v prostoru lodi. Navazuje: další zóny (gondoly proti trupu, břicho po vstupu do atmosféry)
   a nakonec druhá sada UV, až bude třeba zóny kreslit ručně a ne odvozovat z tvaru.
10. ~~Hra běžela na Medium~~ – hotovo 20. 9. 2026 (HANDOFF bod 42): výchozí předvolba je Cinematic
    kromě global illumination, plus doostření po tonemapperu. **Než začneš hledat rozmazanost
    v modelu nebo materiálu, změř nastavení** – dvakrát za den to bylo ono (rozlišení 50 %, pak Medium).
11. **Odlesky a špína na skle canopy** (jemný fresnel, škrábance).
12. **Silnější záře displejů na rámu** a okolní desce.
13. Doladit zbývající „duchy“ čísel při afterburneru (9.2b).
14. **ambientCG.com** (sesterská stránka k Poly Havenu, stejná CC0 licence, volné API bez
    klíče, 2000+ materiálů) – zvážit `fetch_ambientcg.py` podle vzoru `fetch_polyhaven.py`
    pro variaci materiálu trupu (viz plastic_diag/plastic_mat) a pro interiér (kůže sedadel,
    guma, opotřebený kov na panelech). Nalezeno autorem 23. 9. 2026, zatím nezapojeno.

Velké celky:
- tělo pilota v sedadle;
- lepší model kokpitu (sedadlo, boční stěny);
- chybějící systémy SC HUD (palivo, zbraně, protiopatření);
- ~~SC-2b VTOL a zpětná vazba při visení~~ – hotovo 20. 9. 2026 (HANDOFF bod 43). Další v letové
  roadmapě je SC-3 (zbytek HUD a MFD) nebo SC-4 (quantum travel místo cruise).
- SC-4 quantum drive je hotový (HANDOFF bod 47). Z videa zbývá: **mapa systému (F2)** s výběrem
  cíle, **modré jiskry z hran trupu** ve skoku (zvenku), **modrá záře pod přídí** z kokpitu,
  doplňování quantum paliva.

---

## 11. Vzhled scény: světlo, grade a rychlá smyčka

Nejdražší část „vypadat jako SC“ není textura ani počet trojúhelníků, ale **světlo**. Proto se ladí
v běžící zabalené hře a teprve hotová čísla se přepíšou do receptu. Jeden průchod trvá **~30 s**
(bez balení), ne ~4 minuty.

### 11.1 Konzolové příkazy (`Source/gamespace/SpacePostTuning.cpp`)

Všechno jde přes reflexi, takže žádný seznam vlastností se neudržuje ručně:

| příkaz | co dělá |
| --- | --- |
| `space.PostList <část jména>` | vypíše nastavení post processu a hodnoty v této úrovni (`[x]` = úroveň je přepisuje) |
| `space.Post <Nastavení> <hodnota...>` | přepíše jedno nastavení; barvy a vektory se píšou po složkách (`space.Post ColorGain 1 1 1.04 1`) |
| `space.PostDump` | vypíše všechny přepsané hodnoty **rovnou jako řádky pro `POST_SETTINGS`** v `Tools/Assets/build_space_scene.py` |
| `space.Sun <Vlastnost> <hodnota>` | vlastnost směrového světla (`Intensity`, `ContactShadowLength`, `LightSourceAngle`, `SpecularScale`) |
| `space.SunDir <pitch> <yaw>` | kam slunce svítí, ve stupních |
| `space.Sky <Vlastnost> <hodnota>` | vlastnost sky lightu (`Intensity`, `CubemapResolution`) |
| `space.LightList sun\|sky <část jména>` | co ty dva příkazy berou |
| `space.ShipMat` / `space.ShipMatColor` | materiály lodi (bod 34 v HANDOFF) |
| `space.Kit <Param> <hodnota> [část jména]` / `space.KitColor` | materiály interiéru (`Lift`, `MetallicScale`, `RoughnessFloor`, `Gunmetal`…); filtr `MI_T_` = jen trim sheety (`Source/gamespace/SpaceInteriorTuning.cpp`) |
| `space.KitLight Work\|Accent\|All <Vlastnost> <hodnota>` | světla interiéru (`Intensity` v lm, `UseTemperature True`, `Temperature`, `LightColor R G B`, u bodovek `OuterConeAngle`) |
| `space.KitReset` | interiér, slunce a sky light zpátky na hodnoty z úrovně – první příkaz každé varianty |
| `space.Interior` | do interiéru Steadfastu a zpátky (ve hře klávesa I) |
| `space.Walk <dopředu> <doprava> <s> [směr°]` | postava jde, jako by držela klávesy; do logu píše, kde skončila (kolize) |
| `space.Door 1\|0\|-1` | posuvné dveře otevřít / zavřít / zpět na automatiku |

Nic z toho se neukládá. Po restartu hry je zpátky to, co je v úrovni.

### 11.2 Postup

1. Napsat scénář do `Tools/Shots/<něco>.json`, kde každý snímek má `console` s tím, co mění.
   **Nastavení zůstávají i pro další snímky**, takže se stavějí po vrstvách a poslední snímek je
   všechno dohromady (vzory: `look_sun`, `look_fill`, `look_final`).
2. `.\Tools\Shots.ps1 -Preset <něco>` – bez `-Package`, pokud se neměnilo C++ ani obsah.
3. Snímky složit vedle sebe (PIL v scratchpadu) a **podívat se na ně**; rozdíl se dá i změřit
   (průměrná odchylka jasu, kolik procent pixelů se změnilo) – ušetří to hádání, jestli je změna vidět.
4. Co sedí, přepsat do `Tools/Assets/build_space_scene.py` (`SKY_LIGHT_INTENSITY`,
   `SUN_CONTACT_SHADOW_M`, `SUN_SOURCE_ANGLE_DEG`, `POST_SETTINGS`) a materiály do
   `<Loď>_setup.json`. `space.PostDump` vypíše řádky `POST_SETTINGS` k vložení.
5. `.\Tools\run_editor_python.ps1 Tools\Assets\build_space_scene.py` (a `import_ship.py`, když se
   měnil materiál lodi), pak `Tools\Tests\test_scene_look.py` – ten porovnává **úroveň proti receptu**,
   takže chytí zapomenutý krok 5.

### 11.3 Co se z toho zatím ví (20. 9. 2026)

- **Loď byla v kosmu silueta, protože jí nic nesvítilo do stínu.** Sky light měl intenzitu 0.35 a
  směr slunce s tím skoro nehnul (`look_sun`: čtyři úhly slunce, žádný nepomohl, jas sky lightu ano).
- **Sky light 0.7 + `base_color_tint` 3.2.** Pod 0.5 je trup černý, nad ~1.1 ztrácí planeta terminátor;
  lak 2.2 mizel v siluetě, 4.5 je křídový (`look_fill`).
- **Chromatická aberace a vyvážení bílé jsou zakázané.** `scene_fringe_intensity` kreslí barevné
  lemy po hranách desky v kokpitu, `white_temp` 6200 zmodrá celý interiér (`look_final`, srovnání
  s `cockpit`). Test `test_scene_look.py` hlídá, že je úroveň nepřepisuje.
- **Lumen na kvalitu 2 (reflections, final gather) nic nepřidal** a stál ~1 FPS, takže v receptu není.
- Contact shadows (0.08 m) a širší slunce (0.5°) stojí nula a hrají do detailu panelů.
- Celkově: 80 → 88 FPS (změna vzhledu výkon nezhoršila).

### 11.4 Co bylo podezřelé a měření ho vyvrátilo (20. 9. 2026)

Po tom, co se předvolba zvedla na Cinematic (HANDOFF bod 42), zůstaly tři podezřelí. `Tools/Shots/look_artifacts.json` je změřil a **ani jeden obraz nekazí**:

- **Film grain 0.2** (přidaný tímhle projektem): šum v ploché obloze **3,90 s ním proti 3,80 bez něj**,   tedy 2,5 % – a opakované měření se shoduje na 0,006. Zbylých 3,8 je šum scény samotné, ne grain.
- **Motion blur** (výchozí 0.5, na Cinematic běží v plné kvalitě): při 400 m/s je poměr svislých a   vodorovných hran v terénu **0,47 se zapnutým i vypnutým** rozmazáním. Kdyby rozmazával, poměr spadne –   chase kamera ale letí s lodí, takže v záběru se skoro nic nehne.
- **Stopy za pohybem (TSR)**: silueta lodi proti obloze je při 5× zvětšení čistá, bez schodů i bez teček.

Jemné „pruhování“ na hladkých plochách trupu je **mikrodetailní vrstva materiálu**, ne chyba: `DetailNormalStrength 0` ubere 17 % vysokých frekvencí, `PanelStrength 0` dalších 7 %. Je to povrch, ne artefakt.

**Jak měřit, aby to něco znamenalo:** při 400 m/s není žádných dvou snímků stejně zarámováno, takže absolutní „ostrost“ (Laplace) skáče o desítky procent podle toho, kde zrovna loď je. Proto: statické věci měř ve stoje, kde jsou snímky totožné, pohyblivé dvakrát za nastavení (rozdíl dvojice je chyba měření) a raději **poměrem** (směrovostí rozmazání) než absolutním číslem.
