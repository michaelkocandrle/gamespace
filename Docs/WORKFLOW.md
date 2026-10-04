# Gamespace – pracovní postup a nástrahy

> **Místo v hierarchii (`CLAUDE.md`):** pod CLAUDE.md, `Docs/CURRENT.md` a skilly. Pravidla a brány kroku jsou
> v `CLAUDE.md`, aktuální stav v `Docs/CURRENT.md`, postupy podle domény ve skillech. Tento dokument drží
> podrobné postupy a hlavně **úplný seznam nástrah** (kap. 9). Nečti ho celý, hledej v něm grepem. Při rozporu
> se skillem nebo CLAUDE.md platí vyšší a tady se to opraví.

Obsah:
1. Jeden krok práce (odkaz na CLAUDE.md), reference z videa
2. Loď z AI modelu: Blender → Unreal (starší cesta)
3. Blender MCP: ladění v živém viewportu
4. C++ build, Live Coding, unity build
5. Testy
6. Balení hry a snímky (Shots), 6.1 ladění vzhledu za běhu
7. Kokpit: displeje, HUD, světla (jak to je postavené a proč)
8. Git a commit (odkaz na CLAUDE.md)
9. Nástrahy – úplný seznam
10. Kam dál (přesunuto do `Docs/CURRENT.md`)
11. Vzhled scény: světlo, grade a rychlá smyčka

---

## 1. Jeden krok práce od zadání po odpověď autorovi

Brány jednoho kroku (reference, malé kroky, build, testy, snímky `-Editor` během kroku a `-Package` na konci,
vizuální kritik, dokumentace, commit, odpověď autorovi) jsou jen v `CLAUDE.md`. Úpravy assetů dělají Python
skripty v `Tools/Assets`, ladění lodi recepty JSON v `ArtSource/Ships/<Loď>/`. Neptej se, jestli autorovi běží
hra: `Package.ps1` ji sám ukončí; po balení zkontroluj čas `gamespace.exe`.

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

> **Starší cesta.** Od 24. 9. 2026 se exteriér lodi staví přesně z výkresu (`hs_build_ship`, skill
> `ship-pipeline` 3b2), AI slouží jen jako reference stylu. Kapitola platí pro údržbu starších receptů;
> kapitola 2.2 (import do UE) platí dál.

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
# z kořene repozitáře
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
$env:GAMESPACE_SHIP_MANIFEST = (Resolve-Path "ArtSource\Ships\<Ship>\Export\<Ship>_manifest.json").Path
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py
.\Tools\run_editor_python.ps1 Tools\Assets\build_main_menu.py
```

- Nastavení lodi (pawn, komponenty, materiály, světla, kamera) je v
  `ArtSource/Ships/<Ship>/<Ship>_setup.json`. Po odebrání hodnoty z něj zůstane v Blueprintu
  stará hodnota (nástraha 9.3c).
- `no_nanite_parts: ["Interior"]`: interiér **nesmí** mít Nanite (nástraha 9.2a).
- Materiály staví `Tools/Assets/ship_materials.py`. Displeje používají master `M_Ship_Screen`
  (unlit, opaque, pixel animation, parametr `EmissiveStrength`).
- `build_main_menu.py` po importu obnoví úvodní scénu s lodí z `MENU_SHIP` (dnes `"Wayfarer"`).

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
   MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend   # z kořene repozitáře
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
.\Tools\Build.ps1      # Build.bat gamespaceEditor Win64 Development; engine z Tools/UERoot.ps1 (GAMESPACE_UE_ROOT)
```

- **Editor musí být zavřený.** Headless skripty editor spouštějí a samy zavírají.
- **Live Coding** stačí jen na změny těl funkcí. Nové soubory, `UPROPERTY`, `UFUNCTION` nebo
  změny hlaviček vyžadují restart editoru a plný build. Autorovi to vždy napiš.
- **Herní target se kompiluje jinak než editor** (jiné seskupení unity build). Chyba se může
  ukázat až při `Package.ps1`. Viz nástraha 9.4a.
- Nový modul v `gamespace.Build.cs` (naposledy `RenderCore`) je povolený. Smart App Control je
  vypnutý.

---

## 5. Testy

Spouštěj **nástrojem PowerShell** (přes bash se rozbije `$PSScriptRoot`):

```powershell
.\Tools\Test.ps1                                          # offline testy + compileall, jednotný souhrn
.\Tools\Test.ps1 -UE -Filter *cockpit*                    # + testy v UE podle masky; -All = všechno
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_displays.py
```

Seznam testů, co pokrývají a loď pod testem (`Tools/Tests/ship_under_test.py`, `SHIP = "Wayfarer"`): skill
`unreal-scripting` kap. 3. Offline část (`Tools/Test.ps1` bez `-UE`) běží při každém pushi v GitHub Actions
(`.github/workflows/offline-tests.yml`, Linux, pwsh); build UE a testy v UE tam nejsou.

Test musí hlídat to, co autor viděl rozbité. Když se opraví vizuální chyba, přidej do testu
kontrolu, která by ji zachytila (příklad: `no_nanite_parts` v `test_import_ship_plan.py`).

---

## 6. Balení hry a snímky (Shots)

```powershell
.\Tools\Shots.ps1 -Preset cockpit -Editor        # během kroku: nezabalený projekt, čeká na shadery (~2 min)
.\Tools\Package.ps1                              # na konci kroku, ~5 min, kontroluje 12 klíčových assetů včetně písma
.\Tools\Shots.ps1 -Preset cockpit -Package       # zabalí a vyfotí
.\Tools\Shots.ps1 -Preset cockpit -Keep          # snímky i do Docs\Shots\ (jdou do gitu)
```

Presety (`Tools/Shots/*.json`; úplný seznam jsou soubory s `_comment`, tady starší a obecné; interiér Wayfareru
a kit: skill `ship-interior`):

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

Hra během snímků krátce převezme popředí okna.

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

Ve scénáři snímků je dej do pole `console` (platí i pro další snímky, viz nástraha 9.6 cy) – vzor je
`Tools/Shots/hull_tune.json`: jeden běh, šest variant vedle sebe. Příkaz dělá dynamické instance
materiálu, takže **nic neukládá**: co vypadá dobře, přepiš do `<Loď>_setup.json` a jednou přeimportuj.

---

## 7. Kokpit: displeje, HUD, světla

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

Pravidla gitu (`git status`, `git add` s výjimkou autorova souboru, podpis commitu, push, zákaz force push)
jsou jen v `CLAUDE.md`. Po kroku uprav `Docs/CURRENT.md` (stav, známé problémy, další kroky), po změně systému
i `README.md`. `Docs/HANDOFF.md` je od 30. 9. 2026 archiv a nedoplňuje se.

---

## 9. Nástrahy – úplný seznam

Každá nás stála aspoň hodinu. Formát: **příznak → příčina → řešení**.

### 9.1 Prostředí a nástroje

- a) **Balení visí nebo zabalí starý exe.** Příčina: spuštěná hra z `Builds` nebo zaseknutý proces drží
  soubory. Řešení: `Package.ps1` od 22. 9. 2026 každý proces `gamespace` sám ukončí (i puštěnou hru), předem
  se neptej. Po zabalení zkontroluj čas `gamespace.exe`; když se balení přesto zasekne, napiš autorovi.
- b) **`run_editor_python.ps1` z bashe nefunguje** (`$PSScriptRoot`). Spouštěj nástrojem PowerShell.
- c) **Bash heredoc a apostrofy.** Delší Python patch skripty piš nástrojem Write do scratchpadu
  a spouštěj je. Pozor i na `\U` v cestách uvnitř normálních Python řetězců (unicode escape), používej
  `r"..."`.
- d) **Blender z Git Bash** mění cesty `/c/...` a `//Export`. Vždy `MSYS_NO_PATHCONV=1`.
- d2) **Nástroj Bash v relaci Claude Code slučuje dvojité zpětné lomítko na jedno** v příkazech a heredocích.
  Regex v `Shots.ps1` se tak rozbil (a Python pak hlásí `SyntaxWarning: invalid escape sequence`). Patche se zpětnými
  lomítky piš nástrojem Write do souboru a spouštěj ho, nebo použij Edit (28. 9. 2026).
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
- h) **Druhá session čekala 8 h na zámek těžkých zdrojů** (1. 10. 2026). Příčina: session zámek vzala a skončila
  bez `release`, zámek neměl ani obnovení, ani vypršení. Řešení: `Tools/HeavyLock.ps1` (heartbeat každých 5 min
  skrytým hlídačem, 20 min bez obnovení = opuštěný, hooky `Stop`/`StopFailure`/`SessionEnd` volají `release-idle`;
  pravidla v `CLAUDE.md`). Nástrahy při psaní: ve Windows PowerShell 5.1 je `$PSScriptRoot` ve výchozí hodnotě
  parametru pod `-File` prázdný (počítej v těle skriptu); funkce, která něco vypíše do výstupu a vrátí `$false`,
  vrací pole, a to je pravdivé (zprávy přes `Write-Host`); `--` v argumentech `-File` rozbije vázání parametrů
  (příkaz předávej jako `-Exec "<příkaz>"`). Proces nástroje Bash/PowerShell v relaci žije jen po dobu volání:
  hlídače neváž na něj, ale na proces skutečné operace (skripty volají `beat -OwnerPid $PID` samy).

- fd) **Výkres z matplotlibu se kreslil 3 minuty** (1. 10. 2026): šířka textu přes `TextPath(...).get_extents()`
  počítá extrémy Bézierových křivek (164 s na list A0). Šířku ber z metrik písma
  `TextToPath().get_text_width_height_descent(s, prop, ismath=False)` (list za 16 s). Bahnschrift je jeden
  proměnný soubor, matplotlib z něj tučné nevybere: tučné = obrys `patheffects.withStroke`. Nemá znaky ↑ ✓ ✗ −
  (U+2212): `draw_exterior_sheet.py` má záložní písma Segoe UI a Segoe UI Symbol (✓, →); jinak piš slova.
- fi) **Český text v souboru po úpravě PowerShellem rozbitý** (1. 10. 2026). Windows PowerShell 5.1
  `(Get-Content f -Raw) -replace ... | Set-Content` čte UTF-8 bez BOM jako ANSI a zapíše znaky dvakrát zakódované
  (`lÃ­c`). Zdroják upravuj nástrojem Edit nebo pythonovým skriptem ze souboru; `python - @"..."@` v PowerShellu
  visí (here-string je argument, python čeká na stdin). Oprava rozbitého souboru: zpětně zakódovat do cp1252.

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
- e) **Nezabalený projekt (`-game`) kreslil nové materiály šedě**: shadery se ještě překládaly. Od 28. 9. 2026
  snímkovač v rychlé smyčce `Shots.ps1 -Editor` drží každý snímek, dokud běží překlad shaderů a assetů
  (`SHOTS waiting for …`); proti zabalené hře je rozdíl na úrovni šumu. Během kroku se proto vzhled posuzuje
  z `-Editor`, finální snímky, předání a čísla výkonu ze zabalené hry. PIE ani okno editoru se nespouští.
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

- j) **Reflection captures v interiéru nic nedělají, obraz s nimi i bez nich je shodný** (30. 9. 2026).
  Příčina: hra používá Lumen GI a UE 5.8 pak skládá lesk jen z Lumenova hrubého odrazu a SSR
  (`DiffuseIndirectComposite.usf`, `bLumenReflectionInputIsSSR`); průchod s capture a oblohou
  (`RenderDeferredReflectionsAndSkyLighting`) pohled s Lumen GI přeskočí. Řešení: capture nepoužívat, dokud interiér
  běží s Lumen GI. Kov bez odrazů Lumenu zůstává kompromis (metallic ~0,5, drsnost ≥ 0,36).
  Recenze `Docs/Reviews/2026-09-30_interior_reflections.md`.
- k) **Runtime reflection capture se v zabalené hře nikdy nedokončí** (30. 9. 2026, platí jen bez Lumen GI).
  Příčina: `UGameEngine::Tick` aktualizuje capture jen ve snímcích, kdy je v enginové frontě nějaká capture
  (`HasReflectionCapturesToUpdate`). Runtime capture kreslí jednu stěnu krychle za snímek
  (`r.ReflectionCapture.Runtime.Timeslice 1`) a před ní stínový snímek, `RefreshCapture()` jen nastaví příznak.
  Řešení: ~8 snímků na capture volat každý snímek `MarkDirtyForRecaptureOrUpload()` („pumpa“). `bFastRender` funguje
  jen s `r.ReflectionCapture.Runtime.Budget > 0`.
- l) **Odraz capture a oblohy na drsném povrchu je nulový** (30. 9. 2026, bez statického světla a bez Lumen GI).
  Příčina: „lightmap mixing“ násobí odraz poměrem `IndirectIrradiance / AverageBrightness` (`ComputeMixingWeight`)
  a bez lightmap je `IndirectIrradiance` nula; od drsnosti 0,3 naplno. Řešení: `r.ReflectionEnvironmentLightmapMixing 0`.
- m) **`ShowFlag.ReflectionOverride 1` se ve snímkovači neprojeví** (`Shots.ps1 -Editor`, 30. 9. 2026). Řešení: pro
  diagnostiku odrazů dočasně materiál na kov, např. `space.Kit PaintMetallic 0.9 _Structure` a
  `space.Kit PrimaryRoughness 0.3 _Structure`.
- n) **Snímky A/B se liší hlavně na hranách** (30. 9. 2026). Příčina: loď ve výšce (`altitude_m`) se mezi snímky
  nepatrně posune a s ní i `camera_local`. Řešení: porovnávat očima nebo po výřezech, ne průměrným rozdílem pixelů.

### Profilování zabalené hry (Unreal Insights bez GUI, k nástrahám 9.2g a 9.2h)

```powershell
# trace (hra se scénářem snímků, pak se sama ukončí)
& C:\gamespace\Builds\Gamespace\Windows\gamespace.exe /Game/Maps/TestSpace -windowed -ResX=1600 -ResY=900 -nosplash -unattended `
  -ShotList="<scénář.json>" -ShotOut="<složka>" -trace=cpu,frame -statnamedevents -tracefile="<soubor>.utrace"
# export statistik časovačů do CSV (čekat na konec procesu: Start-Process ... -PassThru, WaitForExit)
& "$(.\Tools\UERoot.ps1)\Engine\Binaries\Win64\UnrealInsights.exe" -OpenTraceFile="<soubor>.utrace" -NoUI -AutoQuit `
  -ExecOnAnalysisCompleteCmd="TimingInsights.ExportTimerStatistics <soubor>.csv"
```

CSV má sloupce `Name, Count, Incl, Excl, I.Avg…` v sekundách; seřaď podle `Excl`. Rychlejší orientace bez
trace: pole `console` ve scénáři s `stat unit`, `stat Slate`, `stat SpaceCockpit` – statistiky jsou vidět ve
snímku.

- ex) **„Soumrak“ `space.SunDir -52 120` je dnes noc a strana lodi na slunci ve vesmíru se mění** (30. 9. 2026).
  **Příčina (1. 10. 2026):** `SpaceShotRunner` staví loď nad Veyru tam, kde stojí PlayerStart, a střed planety je
  140 km ve směru +X. Lokální „nahoru“ lodi je tedy světové **−X**, dopředu světové −Z a doleva světové **−Y**
  (ověřeno presetem `wayfarer_sun_calib`; první odhad +Y dal slunce na opačnou stranu); pitch a yaw `space.SunDir`
  jsou světové. Výška slunce nad obzorem = asin(cos(pitch) · cos(yaw)): `-39 45` je 33° (den, slunce vlevo vzadu),
  `-52 102` je −7° (pod obzorem, noc). Řešení: slunce e stupňů nad obzorem a a stupňů od přídě k levoboku je
  `space.SunDir asin(cos e · cos a) atan2(cos e · sin a, sin e)`. Soumrak 6° zezadu zleva = `-44.7 81.5`, noc −10° =
  `-44.1 104`, vesmír 30° zezadu zleva = `-37.8 50.8` (preset `wayfarer_kit_pilot`).
- fa) **Denní trup působí ploše, i když jsou stíny ostré** (1. 10. 2026). Výchozí pohledy (chase zezadu, levobok zepředu)
  vidí stranu odvrácenou od slunce `-39 45`, kterou svítí jen obloha; osvětlený pravobok má kontrast jako SC. Stíny
  slunce ostřejší být nemůžou: scalability epic už dává `r.Shadow.Virtual.ResolutionLodBiasDirectional -1.5` a úhel
  zdroje pod 0,5° se na stínu křídla neprojeví. Poměr slunce a oblohy (11 / 0,55) pomůže jen o pár procent jasu;
  zbytek je lak bez variace drsnosti (povrch trupu, ne světlo).

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
- g) **UE testy v novém worktree padají bez `SUMMARY`, v logu přetečení zásobníku v `MigrateSettings`.** Bez
  `GameUserSettings.ini` chybí enginová `Version`, takže `ApplyNonResolutionSettings` → `ValidateSettings` →
  `LoadSettings` a naše migrace se volaly dokola (stejně by dopadla hra na novém počítači). Opraveno pojistkou
  `bMigrating` (1. 10. 2026). Kód, který v `LoadSettings` nebo migraci volá `Apply*Settings`, počítej s tím, že
  se `LoadSettings` může vrátit zpátky do něj.
- h) **Komponenta lodi bez `BeginPlay` a ticku.** Headless testy spawnují pawn bez `BeginPlay` a `Tick`, takže
  logika v komponentách (`Ship*Component`) se volá z pawnu; `TickComponent` ani `BeginPlay` komponenty by
  v testech neproběhly. Pravidla dělení pawnu: `Docs/ARCHITECTURE.md` kap. 2.

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
- i) **UE test hlásí všechny kontroly OK, a přesto ho `Test.ps1` označí FAIL (`exit 1`)** (30. 9. 2026). Příčina:
  commandlet skončí kódem 1, když během běhu padne chyba enginu v logu (souhrn „Warning/Error Summary“ v logu
  editoru), a `run_editor_python.ps1` jeho kód předá dál. Dvě časté chyby: `LevelEditorSubsystem.new_level("/Temp/X")`
  mapu zároveň uloží do `Saved/X.umap`, takže další běh zaloguje „already an asset at the destination“; a
  `EditorAssetLibrary.load_asset` na neexistující asset zaloguje „LoadAsset failed“. Řešení: prázdný svět jen
  v paměti `unreal.EditorLoadingAndSavingUtils.new_blank_map(False)`; před načtením `does_asset_exist`.
  Chybějící asset, kvůli kterému se kontroly nespustí, vypiš jako SKIP s důvodem, ne tiše.
- fc) **Import uložil znovu i meshe, které nepřeimportoval** (1. 10. 2026). `import_ship.py` meshe se stejným hashem
  geometrie nechá (`kept`), ale `ship_materials.apply` jim nastavil materiály a uložil je s `only_if_is_dirty=False`:
  stejná velikost, jiné bajty, nový objekt v LFS. Řešení: materiál slotu nastavit jen, když se liší cesta, a mesh
  uložit jen po změně. Materiály, textury, Blueprint a mapa se zatím ukládají při každém importu znovu (~150
  souborů se stejným obsahem): po ověřovacím importu je vrať `git checkout -- Content`, pokud se data nezměnila.

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
- cd) **Karta špíny na gondole vystřihla schody.** Ploché buňky 15 cm se na zakřivení (r 0,6 m) propadly ~5 mm pod povrch, víc než odsazení decalu, a depth test je uprostřed zahodil. Buňky 8 cm (průhyb 1,3 mm). Obecně: mesh decal na křivce musí mít buňku menší než √(8 · r · odsazení).
- ce) **`ReferenceError: BMesh data of type BMVert has been removed` po přidání vrstvy.** Nová custom-data vrstva v bmeshi (`verts.layers.float_color.new`) zneplatní Python reference na už existující vrcholy. Vrstvu vytvoř před prvním vrcholem (v `Placer.__init__`).
- cf) **Světla interiéru bez stínů svítí přes trup ven a zvenku stojí až 12 ms.** Světla u svítidel (`fix_*`) proto pawn zapíná, jen když je kamera uvnitř (`UpdateViewCollection`). Test „uvnitř“: přes kamery pawnu jen kokpit (chase kamera visí v obálce interiéru nad trupem), přes jinou kameru obálka partů `Interior*`. Jedno FPS ze snímku po teleportu může být výkyv streamování: ověř `stat gpu`, než začneš optimalizovat.
- cg) **Varianta „bez světel“ měla stejnou cenu jako „se světly“.** Ladicí příkaz překlápěl uložený stav (`bFixtureLightsOn = !bFixtureLightsOn`), aby vynutil přepnutí. Když se stav a požadavek shodly, nepřepnulo se nic. Vynucení dělej příznakem „dirty“, ne překlápěním stavu. Každou měřenou variantu ověř i vzhledem (světelné ostrůvky na snímku).
- ch) **`stat gpu` ve snímcích chyběl, i když ho zapínal první snímek presetu.** Stav statistik mezi snímky není spolehlivý (`stat` přepíná). Měřicí snímek pošle `stat none`, `stat unit`, `stat gpu` (a jednou předem `r.GPUStatsEnabled 1`), viz `Tools/Shots/light_variants.json`.
- ci) **Klávesa I vede do interiéru Steadfastu, ne Wayfareru.** `ToggleInterior` hledá herce s tagem `SpaceInteriorSpawn` (Steadfast v `TestSpace`). Wayfarer se od 29. 9. 2026 prochází jinak: v přistálé lodi F = vstát z křesla (`ASpaceshipPawn::LeaveSeat`), preset `wayfarer_walk` (HANDOFF „Průchozí Wayfarer“, nástrahy eb–ed).
- cj) **Sockety kitu v UE s příponami `.001`, `.019`.** Jména objektů jsou v jednom `.blend` globální: SOCKET_Light_Cove_0 druhého dílu Blender přejmenoval a UE příponu převzalo. `kit_build.py` po exportu dílu jeho sockety přejmenuje (`__<díl>`) a před exportem kontroluje, že v názvu tečka není. Starý mesh v UE je potřeba smazat, reimport ponechal staré sockety.
- ck) **Import dílu padá na „material slots … manifest says …“.** FBX export vynechá sloty, které žádná plocha nepoužívá (díl bez strukturních decalů), ale manifest je vypsal. `kit_build.drop_unused_slots` sloty před exportem pročistí.
- cl) **Kitová ukázka byla skoro černá.** Grafit s albedem 0,06 bez kovu a jen lišty ve vybrání (svítí do stropu) a u podlahy. Paleta se kalibruje podle schválené chodby (stěny 0,085, panely 0,13, metallic 0,1–0,4 → `Kit_Primary` 0,1/0,095/0,088, metallic 0,3). Ukázka potřebuje světla místnosti jako skutečný interiér (strop přijde v dávce 2, do té doby provizorní).
- cm) **Decal kitu se tiše nepoloží („edge/overlap“ v `KITBUILD`).** `hs_decals.Placer` pokládá mřížku bodů po 6 cm a zahodí decal, když bod padne na zkosení (normála > 30°) nebo když je mezi sousedy schod > 12 mm. Kitový štítek přes hranu prolisu, přes žebro, pod přesahem lišty ve vybrání nebo na nástavbě (skříňka, trubky, poklop) tak zmizí. Štítek patří celý na okraj prolisu nebo celý do prohlubně; `Wall.shell_decals(kick_u=False)` vypne soklový štítek tam, kde spodní panel zakrývá výbava. Seznam vynechaných decalů je ve výstupu `KITBUILD`, kontroluj ho po každé stavbě.
- cn) **Provizorní strop ukázky dělal přepálený kříž.** Kovový materiál panelů (metallic 0,45) na rovině stropu zrcadlil provizorní světla a výplňové světlo 30 cm pod stropem do něj vypálilo horký bod. Provizorní roviny (podlaha, strop, konce) mají vlastní drsný nekovový `MI_Kit_Halcyon_ProvFloor` a výplňové světlo visí 80 cm pod stropem. Kritik hodnotí i provizorní věci, i když to brief říká.
- co) **Oprava „materiál jako plast“ udělala černé stěny.** Na výtku kritika jsem lakovaným panelům zvedl `PaintMetallic` na 0,45 a konstrukci dal čistý kov (1,0). Kov nemá difuzní složku: lak ztratil skoro půl světla, rám zrcadlil tmavou místnost a splynul se spárami. Kritik pak v kole 2 hlásil „žádná žebra“ a „černou spodní stěnu“ se stejným skóre. Lak je dielektrikum (metallic ≤ 0,1), plastový dojem dělá jednotná drsnost a chybějící detail, ne málo kovu. **Před každým kolem kritika pusť `measure_look.py`**: průměr, p90 a B/R mimo rozsah SC znamenají systémovou chybu světla nebo materiálu, kterou kritik popíše jako desítku lokálních výtek.
- cp) **Rám kitu se zkosením vypadal jako kulatý sloup.** Profil rámu má hrany 90°, 51° a 39°. Zkosení s jedním segmentem je rozpůlí a hrany 25° a 20° jsou pod prahem `set_sharp_from_angle(40°)`, takže se stínují hladce. Hladký profil pak kritik četl jako „svislé trubky“. Hranatý díl buď bez zkosení, nebo se zkosením se dvěma segmenty jen tam, kde je hrana 90°.
- cq) **Masky kitu (oděr, špína) v UE chyběly, celé bílé.** Díl nese `Col` v doméně rohů, mesh decalů z `hs_decals` v doméně bodů pod stejným jménem. `bmesh.from_mesh` obou meshů v `kit_build.join()` nechal jen bodovou vrstvu decalů, díl dostal bílou, a UE bílé barvy vrcholů při importu zahodí. Oprava: `to_corner_colour` převede vrstvu decalů na rohy před spojením, `kit_build` spadne, když masky nepřežijí. Obecně: dva meshe se stejně pojmenovaným atributem v různých doménách se spojením rozbijí potichu.
- cr) **`has_vertex_colors()` v headless commandletu lže.** `EditorStaticMeshLibrary.has_vertex_colors` vrací False i pro trup Wayfareru, jehož masky fungují (`StaticMeshEditorSubsystem` je headless `None`). Spolehlivě: exportovat mesh z UE do FBX (`AssetExportTask` + `StaticMeshExporterFBX`) a hledat `LayerElementColor`; UE ho zapíše jen při barvách (`test_kit_showroom.py`).
- cs) **MegaLights: jména proměnných a záškub.** V UE 5.8 se zapíná `r.MegaLights.EnableForProject` (jde i za běhu v zabalené hře), vypínač škálovatelnosti je `r.MegaLights.Allowed`. `r.MegaLights.Allow` a `r.MegaLights.Enable` z dokumentace Epicu neexistují a konzole je tiše ignoruje. První zapnutí stínů světlům za běhu dalo jeden snímek 140 ms, měř ustálený stav (`kit_megalights_perf.json`, 8 s).
- ct) **Decal kitu se postavil, ale ve hře nebyl vidět (levý výstražný pás rámu B, štítek chladiva).** `hs_decals.grid` otáčel novou plochu decalu podle `f.normal`, která je do `normal_update()` nulová (9.3 s), takže se neotočila nikdy a směr líce určilo pořadí vrcholů z rámce. Rámec s `x × y = −n` (zrcadlený) dal plochu rubem k divákovi a UE ji ořízl. Oprava: `normal_update()` před kontrolou a `kit_build` zrcadlený rámec hlásí v `KITBUILD` jako chybu („mirrored frame“). Pravidlo pro `label(..., normal, xdir, ydir)`: `xdir × ydir` musí být normála plochy (na protějších stranách se znaménko `ydir` otočí). Na lodích `Placer.place_at` zrcadlený rámec srovná sám (otočí x), jinak by se decal po opravě normály četl zrcadlově (Wayfarer `streak_drip`, `mirrored_decals` v `test_ship_geometry.py`). Po každé změně v `hs_decals` pusť i `test_ship_geometry.py`.
- cu) **Lišty kitu měly černou „trávu“ a tmavé svislé pruhy.** Trim kitu je na `M_Ship_PBR`, který přidává detailní normálu trupu (tile 30 cm, síla 0,7) a panelové spáry trupu. Pod světlem vybrání skoro souběžným s plochou dělala detailní normála vysokofrekvenční stíny, spáry pruhy přes lištu. Na `MI_Kit_*_Trim` jsou vypnuté (`detail_normal_strength`, `panel_strength`, `panel_seam_darken` 0). Příčinu jsem nejdřív hádal (zdrsnění kvůli Lumenu, nepomohlo); rychlejší je přepínat parametry za běhu `space.Kit <Param> <hodnota> <jméno MI>` na zabalené hře (preset `kit_rail_noise.json`, bez balení).
- cv) **Provizorní světlo nad zatáčkou nic nerozsvítilo.** Stálo nad horní hranou zkosení (0,6 m od stěny v průřezu W), tedy v kapse vybrání, a stínilo se samo. Světla ukázky patří do otevřené části stropu mezi hranami zkosení (`prov_spots` bere i kužel: `((x, y), cd, kužel)`).
- cw) **Dvě stavby lodi ze stejného receptu nejsou totožné.** `hs_build_ship.py` na Wayfareru dal trup 303 646 a pak 303 648 ploch, jiné pořadí jmen světel svítidel (`fix_*` v `Wayfarer_lights.json`) a jedno světlo posunuté o 0,2 mm. Rozdíl se pak propíše do decalů (paprsky padnou na jiné plochy). Dopad změny v kódu decalů proto měř na **stejném** `<Loď>_HS.blend`: `hs_assemble_ship` pusť dvakrát, se starou a novou verzí funkce (monkeypatch ve wrapperu, výstup mimo repo), a porovnej plochy podle polohy a normály (`Docs/Reviews/2026-09-27_hs_decals_wayfarer_check.md`). Od 1. 10. 2026
  exportér zapíše jen FBX se změněným otiskem geometrie a import přeskočí nezměněné meshe (skill `ship-pipeline` 5);
  přestavba samotného trupu ale kvůli nedeterminismu pořád změní jeho otisk (oprava stavby čeká v CURRENT.md).
  Pořadí světel svítidel opraveno 2. 10. 2026: `hs_fixture_lights` je řadí (síla, materiál, místo); dřív se po přestavbě
  přečíslovala `fix_*` a s nimi ID `L-FIX-*` na listu I-04 (`test_interior_drawing` hlásil prvky jen ve výkresu / jen v datech).
- fm) **Po pádu počítače byla loď ve hře černá krabice bez gondol** (3. 10. 2026). Modrá obrazovka MEMORY_MANAGEMENT
  (nestabilní RAM s EXPO 6000; Windows Memory Diagnostic našel chyby, bez EXPO čistý) přerušila import a nechala
  `SM_Ship_Wayfarer.uasset` a `_Decals.uasset` rozepsané; další import je nepřepsal (log: „Unable to load package … end of
  package tag is not valid“). Řešení: poškozené `.uasset` vrátit z gitu (`git checkout --`), import s
  `GAMESPACE_SHIP_FORCE_IMPORT=1`; kontrola všech balíčků = značka `C1 83 2A 9E` na začátku i konci souboru. Výstupy
  z doby nestabilní paměti přestavět (Blender, export, C++, balení načisto bez `Saved/Cooked`).
- cx) **Volná kamera snímků viděla postavu hráče.** Po `space.Showroom` stojí postava na startu. Snímky s `"camera": "free"` pak mají v záběru její ramena nebo celou postavu. Preset, který ověřuje vstup (`"camera": "pawn"`), má postavu hned poslat zpět (`space.Showroom annex` znovu) a teprve pak fotit volnou kamerou (`kit_annex.json`).
- cy) **Překryv `stat unit` / `stat gpu` zůstal na dalších snímcích.** Konzolové příkazy platí pro zbytek presetu. Snímek po měření výkonu musí mít `stat none`. Opačně: `stat gpu` zapnutý v rozcvičovacím snímku se do dalších snímků nemusí propsat. Seznam průchodů fotit se `stat none`, `stat unit`, `stat gpu` přímo v měřeném snímku (jako `l_perf_corridor`).
- cz) **S MegaLights C (RT stíny) ukázka ztmavla.** Světla bez stínů prosvítala geometrií, se stíny už ne. Průměr chodby klesl z 0,20 na 0,13, p90 z 0,42 na 0,25. Po zapnutí stínů přeměř `measure_look.py` a jas případně doplň intenzitou svítidel; s MegaLights to výkon skoro nemění.
- da) **Snímky s volnou kamerou měly 25 ms místo 16.** Předehřátí MegaLights po 30 snímcích vypnulo osvětlení interiéru a přepsalo `space.InteriorLighting 1` z rozcvičení presetu (obojí nastavuje proměnné s prioritou Code, platí pozdější zápis). Scéna se pak kreslila bez MegaLights a se 138 stínovými mapami. Konec předehřátí teď vrací žádaný stav: chůze interiérem nebo příkaz. Obecně: dvě místa, která nastavují stejnou proměnnou se stejnou prioritou, musí sdílet jeden „žádaný stav“. Po každé změně zapínání MegaLights zkontroluj `stat unit` na snímku výkonu.
- db) **`space.KitLight … IntensityScale` za běhu podhodnotil účinek.** Násobek 2,0 za běhu dal jas chodby 0,20, stejný násobek z importu výrazně víc. Za běhu totiž snímky jely s MegaLights přes konzoli (správně), ale import se měřil s chybou da. Násobky jasu ověřuj až v buildu se správným stavem osvětlení a kalibruj podle `measure_look.py`.
- dc) **Otvor v koncové stěně byl černý obdélník.** Zadní černá deska koncové stěny ležela 7 cm za lícem přes celý obrys, takže zakryla průlez za otvorem. Navíc `_upper_side` pro pravou stranu zrcadlil vstup špatně a horní panel přejel přes celý střed (nad otvorem průlezu a přes prostřední panel koncových stěn, dvě plochy v jedné rovině). Kdykoliv díl dostane otvor, prořízni i zadní desku (`_end_base(hole=)`, v zúžení tři díly kolem otvoru) a zkontroluj render zepředu.
- dd) **Vodorovné plochy trimu kitu byly černé a na materiál nereagovaly.** Protiskluzové pásy, pás u okraje desky, vyústění vzduchu: černé i s kovem 0, zeleným odstínem a drsností ×2, zatímco lišty na stěnách a šikmá rampa se stejným trimem fungovaly. Vyloučeno: textury v UE (export), UV v meshi (`get_static_mesh_description`), sloty, normály v FBX, tangenty FBX i UE, přepočet normál v sestavení. Rozhodl test se stejnými plochami ve vrstveném masteru: osvětlené. Příčinou byl master trupu `M_Ship_PBR` na plochách s normálou přesně (0, 0, ±1), kořen je v dg. Kit má dál vlastní jednoduchý `M_Kit_Trim` (`import_kit.build_trim_master`). Rychlý test příčiny: stejné plochy s jiným masterem v jednom sestavení.
- de) **Bez odrazů Lumenu jsou hladké kovy černé.** Interiéry běží s vypnutými odrazy (rozhodnutí autora). Kov s drsností pod ~0,45 pak nemá co odrážet a vykreslí se černě: protiskluzový pás (kov 1, drsnost 0,45), kopací plech, hlavy šroubů. `kit_trim_sheet.py` odmítne pruh s kovem > 0,5 a drsností < 0,5; kitové materiály mají drsnost konstrukce 0,46 a holého kovu 0,52.
- df) **V zabalené hře nefungují `viewmode` ani `ShowFlag.VisualizeBuffer`.** Snímky se nezmění. GBuffer se tak nedá prohlédnout; diagnostika přes parametry materiálu za běhu (`space.Kit`, `space.KitColor`) a přes varianty v jednom sestavení.
- dg) **Přetypování matice primitiva v HLSL: `(float3x3)GetPrimitiveData(Parameters).WorldToLocal` dává nesmysl.** V UE 5.8 jsou `LocalToWorld` a `WorldToLocal` struktury `FDFMatrix` / `FDFInverseMatrix` (`{float4x4 M; float3 …}`), ne matice. HLSL strukturu při přetypování zploští a vezme prvních devět čísel za sebou (M00 M01 M02, M03 M10 M11, M12 M13 M20), ne levý horní blok 3×3. U neotočeného dílu tak vyjde třetí řádek nulový. Normála (0, 0, 1) se změní na nulový vektor, `normalize` z něj udělá NaN a plocha je černá (dd, vodorovné plochy s `M_Ship_PBR`). U otočených dílů to NaN nedá, jen špatně promítne triplanární vrstvy (grunge na stěnách do boku se natáhl do svislých šmouh). Hledání půlením: sondy s variantami masteru na vodorovných deskách (`Tools/Assets/probe_pbr_flat.py`, preset `probe_pbr_flat`). Rozhodla deska se silou spár 0, která zůstala černá: NaN × 0 = NaN. RGB výstup vrstvy prošel přes `clamp`, který NaN na GPU převede na číslo, alfa (hloubka spáry) ne. Oprava: `DFToFloat3x3(…)` (engine sám bere `.M`), normály se do lokálního prostoru převádí transpozicí `LocalToWorld` a zpět `WorldToLocal` zleva, každá normalizovaná zvlášť. Degenerovaná transformace dostane záložní osu (0, 0, 1) místo `normalize` nulového vektoru. Hlídá `Tools/Tests/test_material_hlsl.py`. Vektorový součin se svislou osou v kódu nebyl (autorova hypotéza), mechanismus byl ale stejný: nulový vektor → NaN → černá.
- dh) **Normálová mapa čtená v Custom node nemá modrý kanál.** `TC_Normalmap` je BC5 (jen R a G), surový `Texture2DSample(...).rgb * 2 - 1` dá z = −1 a detail se ohne do plochy. Master trupu tak detailní normálu do 27. 9. vůbec neukázal (jen konstantní posun). Z se musí dopočítat: `z = sqrt(saturate(1 - dot(xy, xy)))`. Po opravě začala detailní normála poprvé působit: interiérový kit Wayfareru se sílou 0,25 vypadal jako tepaný plech, snížena na 0,06. Hlídá `test_material_hlsl.py`.
- di) **Oprava sdíleného masteru mění vzhled všech lodí, i když parametry zůstanou.** Po opravě dg/dh se změnil interiér Wayfareru (šikmá stěna nákladového prostoru přišla o lesk, stěny technické místnosti tepaný vzhled), trup zvenku ne. Postup: snímky „před“ ze starého buildu (`hull_decals`, `wayfarer_interior`), oprava, snímky „po“, rozdíl po snímcích (průměrná odchylka, podíl změněných pixelů). Když rozdíl působí jinak než šum, najdi instanci (kterým masterem jede) a dolaď její parametry v `<Loď>_setup.json`. Ladění bez nového importu meshů: `Tools/Assets/apply_ship_materials.py` (`GAMESPACE_MATS` omezí instance, jinak se znovu uloží všechny). Pozor, import kitu (`import_kit.py`) přestaví sdílené mastery a znovu uloží i meshe Wayfareru: před commitem je vrať, pokud se loď neimportovala.
- dj) **Snímky braly kvalitu grafiky z autorova menu.** Autor si 27. 9. večer přepnul grafiku na „střední“. `GameUserSettings.ini` zabaleného buildu (`Builds\Gamespace\Windows\gamespace\Saved\Config\Windows`) pak platil i pro `Shots.ps1`. Jedna sada měření vyšla o 5 ms rychlejší (VRAM 2,24 místo 3,11 GB) a kritik hodnotil snímky ve střední kvalitě. Poznáš to v logu hry: druhá sada `Set CVar` hned na startu (např. `r.MegaLights.NumSamplesPerPixel:2`). `Shots.ps1` teď autorův soubor na dobu běhu odloží, nastaví výchozí kvalitu hry (`USpaceUserSettings`: epická, GI vysoká, TSR 75 %) a po běhu ho vrátí; `-PlayerSettings` snímá s autorovým nastavením. Autorův soubor se nikdy nepřepisuje natrvalo.
- dk) **Přerušený `import_kit.py` nechá level bez ukázky.** Konec relace uprostřed importu smazal herce ukázky z `TestSpace` a tři meshe kitu. Snímky pak ukázaly terén planety místo chodby. Balení přitom prošlo, protože klíčové assety existovaly. Odhalí to `test_kit_showroom.py` (0 dílů, chybějící meshe). Oprava: import pustit znovu celý. Po každém importu kitu pusť test kitu dřív, než se balí.
- dl) **Tmavá špína na tmavém laku není vidět.** Tři kola kritik hlásil „špína ve spárách se nečte“, i když karty
  ležely celé (vrcholy s plnou alfou). A/B `Tools/Shots/kit_grime_ab.json` (`space.Kit DecalOpacity 0 DecalGrime`,
  `space.KitColor DecalTint 0 0 0 DecalGrime`) ukázal, že ani čistě černý odstín jas grafitu (albedo 0,07–0,1)
  skoro nezmění: desku dělá hlavně odlesk. Řešení: nános jako světlejší matný prach (tint ×5 na atlasu). Nejdřív
  A/B vypnuto/černá/bílá, pak ladit sílu; nezvětšovat karty naslepo.
- dm) **Světlý prach ukáže doběh karty jako opar.** Buňka `soot` má ve 30 % hloubky ještě 0,16 krytí. S tmavou
  špínou to nevadilo, se světlým prachem karta 0,3–0,35 m udělala opar uprostřed desky a nejhustší pás ležel pod lištou
  stěny. Viditelný pás ≈ 35 % hloubky: 0,18 m u stěny, 0,1 m ve spárách. Zdrojová hrana karty (`up`) patří do
  viditelného rohu.
- dn) **`bpy.data.libraries.load` přepíše seznam jmen objekty.** `data_to.objects = names` a po načtení je v `names`
  místo jmen načtený objekt, takže slovník podle jmen zůstal prázdný („kit parts not in ArtSource/Kit/*.blend“).
  Předávej kopii: `data_to.objects = list(names)` (28. 9. 2026).
- do) **Místnost z kitu v lodi:** blend lodi má v místnosti jen přepážky a náhrady, díly kitu vkládá až UE
  (`kit_rooms.py`, komponenty `InteriorMod_*`, světla `Light_fix_kit_*`). Test geometrie proto díly sám dosadí
  (`check_ship_geometry.add_kit_rooms`, sdílená matematika `Tools/Kit/kit_layout.py`), jinak hlásí díry v celé
  místnosti. Když místnost přijde o strop, sousední tmavá vrstva nad stropem visí volně: místnost z kitu si ji nechává.
  Tmavé výklenky za otvory dílů kitu musí sahat až k zadní stěně modulu (`RECESS_BACK`), jinak visí ve stěně
  a kolem je škvíra.
- dp) **Schválený půdorys měl dveře přímo proti objektu.** Dveře z nákladového prostoru Wayfareru (y 0,65–1,75)
  ústily na bok reaktoru (y 1,05–1,85 od x 8,35), takže volných zbylo 0,4 m. Odhalila to až pilotní chodba z kitu.
  Při návrhu kontroluj u každých dveří volný průchod do hloubky 0,5 m za nimi. Každá ruční úprava layoutu dostane
  klíč `_kit` s důvodem.
- dq) **Řez trupem kreslil cizí křídla přes interiér.** Každá stanice má panel ±2,5 m, křídla sahají do ±7,3 m;
  bez ořezu se kreslila do sousedních panelů a vypadala jako nosník přes chodbu. Kreslení řezů ořezává (`clip_y`).
  Před závěrem „geometrie v místnosti“ ověř data řezu, ne obrázek. Test průniku hlídá jen díly interiéru mimo trup;
  trup uvnitř místností hlídá `hull_in_rooms` (negativní test: místnosti rozšířené za trup musí selhat).
- dr) **Stínové mapy slunce v interiéru lodi stály 3,2–3,8 ms.** Uvnitř trupu slunce nic nevidí, ale virtuální
  stínové mapy kreslily interiérové meshe (bez Nanite) do stránek pro každý viditelný pixel. Sonda `space.Sun
  CastShadows False` (14,8 ms místo 18,5) a pak interiér bez vrhání stínu (16,7 ms, obraz stejný) to prokázaly.
  Oprava: v režimu osvětlení interiéru pawn lodi vypne `CastShadow` interiérových meshů (trup místnosti zastíní) a
  díly kitu jsou ve světelném kanálu 1 (slunce jen 0). Měření začínej `stat gpu` a sondami, ne úpravou světel.
- dt) **Nová položka knihovny decalů posune UV všech starých.** `decal_library.py` balí položky do polic podle výšky;
  jedna nová zařazená mezi staré posunula všechny za ní a hotové lodě a díly kitu (UV decalů zapečené v meshi) by
  ukazovaly cizí nápisy. Nové položky mají v receptu `"append"` a balí se až za staré. Po přestavbě atlasu porovnej UV
  starých položek v `decal_library_index.json` a pixely jejich obdélníků (dávka 4: 0 změn UV, 3 pixely zaokrouhlením).
  Atlas do UE dostane `import_ship.py` (textury `/Game/Ships/Wayfarer/Textures/T_Decals_*`).
- du) **První běh `Shots.ps1 -Editor` po reimportu velké textury ukázal rozmazané nápisy.** Atlas 4096 px se v nezabalené
  hře teprve kompiloval do DDC a snímky dostaly nízké mipy; druhý běh byl ostrý. Po reimportu textur ber první běh
  jako rozehřátí a rozmazaný detail ověř druhým během, než začneš hledat chybu v UV.
- dv) **Detail uvnitř plného kvádru není vidět.** Žebra chladiče ležela uvnitř plného kvádru „dutiny“ a pak za čelem
  plného pláště komponenty; na renderu byla černá nebo krémová plocha. Vybrání je jen zadní deska (a boky), ne kvádr,
  a detail za čelem pláště potřebuje otvor v plášti nebo musí stát před ním (chladič: žebrovaný blok před čelem).
- dw) **Paprsek štítku z 8 cm trefil mříž dveří před komponentou.** `Wall.label` střílí decal z 8 cm před plochou;
  na čele komponenty za mříží dveří zasáhl tyč. Štítky na komponentách v nikách: `_casing_label` z 3 cm a `label=True`
  (dosah 2 cm).
- dx) **Věc za okénkem je z výšky očí vidět níž, než leží.** Emitor 13 cm za průhledem na jeho středu ukazoval jen
  horní okraj prstence (oko 1,65 m, 1,3 m od stěny, okénko ve 0,75 m). Posun ≈ hloubka × (oko − okénko) / vzdálenost;
  věc za okénkem posuň o tolik níž nebo blíž ke sklu.
- dy) **Obnovený nápis v setupu byl zrcadlený.** Instance `MI_Ship_<Loď>_Decal_<jméno>` nese `DecalFlipU`, ale
  `build_decal_instances` ho nastaví jen, když ho položka setupu má. Staré instance měly převrácení uložené z dřívějška;
  po smazání a obnovení (nápisy technické chodby Wayfareru, `legacy_room`) vznikly s výchozí 0 a text byl zrcadlený.
  Položka setupu musí mít `flip_u` / `flip_v` vždy výslovně. Test geometrie to nechytí (hlídá jen mesh decaly).
  Hlídá `Tools/Tests/test_decal_orientation.py` (osa X nápisu k divákovi a právě jedno převrácení; symetrické pruhy
  `"symmetric": true`) a `test_ship_import.py` (instance mají převrácení jako setup). Test našel další čtyři nápisy,
  které četly správně jen díky starým instancím (sekce 02–04, FIRE SUPPRESSION).
- dz) **V letovém osvětlení stojí každé světlo kitu plnou cenu.** Bez MegaLights se neosvětlená obdélníková světla
  platí plochou na obrazovce; chodba z kitu byla v letu o 1 ms dražší než stará (20,35 proti 19,15 ms). Světla, která
  v letu nejsou potřeba (výklenky, prosvětlení stěn, kanál v podlaze), nesou tag `InteriorOnly` (`kit_rooms.py`,
  `INTERIOR_ONLY_SOCKETS` nebo parametr socketu `interior_only`) a pawn je zapne jen v režimu interiéru (19,49 ms).
- ea) **Opakovaná měření výkonu bez čtení snímků.** Snímkovač zapisuje `SHOTS perf <jméno> gpu_ms=.. frame_ms=..`
  (průměr druhé poloviny ustálení); preset `wayfarer_perf.json` měří 3× interiér a 3× let, `python
  Tools/Shots/perf_log.py <log…>` spojí běhy a vypíše průměr a rozptyl. Rozptyl mezi běhy 0,2–0,8 ms, proto se cíl
  dokládá aspoň 3 běhy.
- eb) **Chodec v lodi stojí a nejde dál, i když je před ním volno.** Snímky ukázaly stále stejné místo. Příčinou byla
  3 cm vysoká svislá ploška: zadní hrana desky podlahy kokpitu. Po vyříznutí otvoru pro schody zůstala celá přes
  průchod ve výšce 1,12 m a z dálky nebyla vidět. Test geometrie ani díry ji nenašly, protože kolize po polygonech
  vidí i plochu bez tloušťky.
  - Diagnóza: `space.Where` vypíše polohu v souřadnicích lodi a to, čeho se kapsle právě dotýká. Tah „ahead“ ukazuje
    až další překážku. Zdroj pak najdi výpisem ploch meshe v objemu průchodu v Blenderu (sonda podle materiálu a
    rozsahu).
  - Hlídá to kontrola `walk_blocked` v `check_ship_geometry.py`: kapsle každými dveřmi layoutu i přes schody.
- ec) **Výchozí kapsle postavy (84 cm × 1,92 m) neprojde strmými schody u dveří.** Schody Wayfareru (47°) začínají hned
  za dveřmi do kokpitu. Kapsle na horních stupních sahá hlavou až k pólu nad dveřmi. Pomohla štíhlejší kapsle v lodi
  (56 cm × 1,80 m, `APlayerCharacter::SetShipCapsule`), dveře až ke stropu, schody o 6 cm dál od stěny a žebro nad
  dveřmi zkrácené. Rezervu počítej s „vznášením“ kapsle 2,4 cm nad podlahou a s tím, že na hraně schodu stojí výš,
  než je střed stupně. Kontrola `walk_blocked` s kapslí o 15 cm vyšší selže; nová loď musí projít s rezervou.
- ed) **Loď v místě snímků nepřistane (`TooSteep`).** Snímkovač staví loď nad svah 32°, přistání dovolí nejvýš 25°.
  `space.FlatSpot [max °] [km]` ji přesune nad nejbližší rovné místo (sklon pod stopou 1,5 m i 8 m), pak snímek s
  `altitude_m` 3,2 a `settle` 10 přistane. Pozor, konzolové příkazy snímku běží před umístěním lodi: loď tehdy ještě
  může mířit nosem kolmo k povrchu a tečné směry z nosu vyjdou nulové (všech 20 000 vzorků pak padlo do jednoho bodu).
- ee) **Import kitu spadne na „kit part … not imported“.** `import_kit.py` importuje `import_ship` a ten při importu
  modulu spustí celý import lodi, včetně místností z kitu. Díly nové dávky ale ještě nejsou naimportované.
  `kit_rooms.py` proto chybějící díl jen ohlásí (`KITROOMS … skipped`) a na konci importu kitu staví místnosti znovu.
  Varování z první stavby jsou v pořádku, z té poslední ne.
- ef) **Zevnitř na stěně prosvítá zrcadlově logo z trupu.** Vnější nápis měl projekční hloubku ±60 cm. Obložení trupu je
  jen 15 cm od trupu, takže ho box zasáhl. Vnější nápisy drž nejvýš ±30 cm: na trup dosáhnou, na obložení ne.
- eg) **Obložení / strop kitu „prochází trupem“ u rampy.** Trup Wayfareru se nad 2 m zužuje a u rampy se nahoře zavírá.
  Obdélník místnosti ze stropu 2,3 m tam nestačí. Před návrhem průřezu změř šířku trupu v několika výškách po celé délce
  místnosti (skript na řezy jako `hold_fit.py`), ne jen v jednom místě. Kontrola `penetrating` vrhá paprsek k ose lodi
  ve výšce oka a hlásí rohy, které jsou za trupem.
- eh) **Projekční nápis „marks nothing“, i když podlaha je pod ním.** Kontrola vrhá jediný paprsek ze středu nápisu a
  ten padl do 5mm spáry mezi dlaždicemi (x 4,6 = spára rastru 0,6 m od x 1,0). Nápis posuň mimo spáru. U podlahy
  s deskami 3 cm dosáhne 4cm box na jejich spodní stranu („reads mirrored“), hloubku dej 2 cm.
- ei) **Po převedení poslední místnosti na nový kit zmizelo i něco mimo ni.** Starý kit (`interior.kit`, Quaternius)
  se v `hs_interior.py` vytvářel jen tehdy, když měl nějakou místnost. Pod stejnou podmínkou ale stavěl i zadní stěnu
  kokpitu (štít nad stropem kajuty, nosník) a detaily kokpitu. Z kokpitu se pak koukalo do tmy nad stropem kajuty a
  z manifestu zmizel `InteriorKit` (test menu a importu to hlásí jako „earlier model left“). Kit se teď staví vždy,
  když ho recept má. Po takové změně projdi i sousední místnosti a snímek z výšky očí v kokpitu.
- ej) **Po `kit_build.py -- <dávka> --only <díly>` geometrická kontrola lodi hlásí „kit parts not in ArtSource/Kit/*.blend“.**
  Stavba ukládá `.blend` dávky jen s díly, které právě postavila; `--only` tak z něj vyhodí všechny ostatní
  (`check_ship_geometry.py` bere díly z těchto souborů). Po změně jednoho dílu stav celou dávku (je deterministická),
  pak vrať FBX dílů, které se nezměnily (`git checkout -- ArtSource/Kit/Export/<díl>.fbx`, FBX nese čas vytvoření).
- ek) **Široký strop z kitu je černý, i když žlábek u stěny svítí naplno.** Světlo žlábku leží 8 cm pod stropem a strop
  zasáhne pod úhlem skoro rovnoběžně - střed stropu 3,6 m širokého nedosvítí žádnou silou (×2,5 jen přepálilo okraj
  do bíla). Stropní svítidla přitom svítí jen dolů. Řešení: u každého svítidla stropu slabé bodové světlo 35 cm pod
  stropem (`halo` v `kit_batch2.py`, socket `Light_Halo`, jen v interiéru): strop kolem svítidel čitelný, mezi nimi
  tmavší. Kaluže na podlaze dá až úzký silný kužel (50°, 260 cd; 100° a 35 cd byly neviditelné).
  Úzké kužely ale končí na podlaze a po ztlumení žlábku zčernají spodní půlky stěn (kritik: „černé plochy bez
  tvaru“). Stěny potřebují vlastní světlo: bodovky v postranním pásu stropu skloněné ke stěně (`scallop`, kaluž ve
  výšce lišty) a wash obložení mířený dolů po vlastní stěně (zkosí přes hrany panelů). Rect světlo s několika cd
  na 1 m vzdálenosti dá jen jednotky luxů – wash 1 cd/m stěnu nerozsvítí, potřebuje ~5 cd/m.
- el) **Geometrická kontrola hlásí „penetrating“ na soklu obložení u podlahy, i když místnost prošla hull_in_rooms.**
  Zapuštěný sokl obložení sahá 11 cm za líc (drážka, guma, výplň pod podlahou) a trup se u podlahy zužuje dřív než
  ve výšce pasu – ve Wayfareru u přepážky kokpitu (x 15,2) je u podlahy jen 4,5 cm od líce k trupu. Kontrola hlásí
  střed ostrůvku (střed modulu), ne místo průniku: změř trup vodorovnými paprsky po x a výškách 0–0,2 m. Řešení:
  poslední modul `Wall_HullLiner06L_D` (plochý sokl, guma na líci, za lícem nejvýš 3 cm).
- em) **Menší místnost je pod stejným světelným plánem přesvícená.** Kajuta 4,8 m pod světly skladu: p50 0,28 (SC
  0,08–0,18), světlejší lodní podlaha. Světla místnosti ztlumí `kit_modules.light_scale` ([x0, x1, faktor, místnost],
  `kit_rooms.py` násobí světla dílů podle polohy); kajuta 0,6.
- en) **Malý díl kitu stojí nečekaně mnoho trojúhelníků** (30. 9. 2026). Difuzor 4×4 cm `Kit_Glow*` stojí 108
  trojúhelníků (`_bezel` dává rámeček na obě velké strany), box s bevelem a 2 segmenty 108, s 1 segmentem 44, a
  zaslepené konce průběžných trubek a kabelů. Řešení: `bezel_face=-1/1` u difuzoru, jehož druhá strana leží na dílu;
  `segments=1` u bevelů ≤ 3 mm; `caps=False` u průběžných vedení; šrouby jako šestihran. Rozpad po voláních: obalit
  `Part.box/slab/tube` a účtovat přírůstek volajícímu (`slab` volá `box`, vnořené řádky se počítají dvakrát).
- eo) **Geometrický test hlásí u decalu na kit podlaze „box reaches the wall's other side“** (30. 9. 2026). Pruhy jsou
  zapuštěné 1 mm do desky (paprsek ze středu decalu narazí na jejich spodní stěnu) a deska je silná jen 2 cm (box
  decalu hluboký 3 cm dosáhne na její spodek). Řešení: `mirrored_projected` ignoruje odvrácené plochy do 8 mm za
  povrchem; decal na podlaze `"max_depth_cm": 1.5`.
- ep) **Kit podlaha v místnosti s obložením trupu (průřez L)** jde jen 1 cm pod líc obložení, ne 10 cm jako u stěn W:
  obložení má ve výklenku soklu vlastní práh a u přepážky kokpitu Wayfareru je trup jen 4,5 cm za lícem. Místnost
  přestane držet lodní podlahu odebráním `"floor"` z `kit_modules.keep`; mezeru mezi přepážkou a prvním modulem zakryje
  `stand_in_floor` (30. 9. 2026).
- eq) **Po přestavbě lodi se ve hře nic nezměnilo, stará geometrie zůstala** (30. 9. 2026). Kajuta měla kit podlahu
  i starou lodní a obě blikaly přes sebe; výdejník měl před sebou starou krabici. Příčina: `hs_assemble_ship.py`
  zapíše `<Loď>_HS_Game.blend`, ale FBX v `Export/` nepřepíše, takže `import_ship.py` importuje minulý export.
  Řešení: po assemble vždy `gamespace_ship_export.py -- --out "//Export"` (z `ArtSource/Ships/<Loď>`), pak
  `import_ship.py`. Kontrola: čas FBX v `Export/`.
- er) **Nábytek u obložení trupu narazí do žeber na zkosení** (30. 9. 2026). Obnažená žebra stojí na každém spoji
  modulů 8 cm od panelů i nahoru po zkosení, takže volno je jen po čáru o `FRAME_OUT / 0,6` níž než rovina zkosení
  (0,1 m od líce 1,68 m, ne 1,83 m; `kit_furniture.top_at`). Geometrický test to nevidí (díly kitu spojí do jednoho
  meshe): `Tools/Kit/kit_clash.py -- <Loď> [prefix]` postaví díly jako samostatné objekty a vypíše dvojice, které se
  protínají (dno na podlaze a konzole v obložení jsou záměr). Totéž kabelový žlab na zkosení (0,27–0,34 m od líce,
  od 1,99 m) a nosníky stropních rozvodů (od 2,09 m).
- es) **Polštář opřený o lisovaný panel „plave“** (geometrický test, 30. 9. 2026). Střed lisovaného panelu je 6 mm
  zapuštěný a zaoblené hrany polštáře mezeru zvětší nad toleranci 6 mm. Řešení: polštář 7 mm do panelu.
- et) **Kování na hlubokém lisovaném poli plave** (geometrický test, 30. 9. 2026): LED na okraji dvířek stála 1 cm nad
  plochou. Příčina: `kit_geo.box(inset=(okraj, hloubka))` je jeden `inset_region` s hloubkou, celý okraj je šikmina.
  Řešení: trojice `inset=(okraj, hloubka, schod)` dá plochý rám, strmý schod a rovné pole
  (`kit_furniture.DEEP = (0.035, 0.012, 0.006)`); kování na rám nebo na dno pole (`x - hloubka`), ne přes hranu.
- eu) **Čalounění z boxů s bevelem vypadá jako vinyl, i s normálou tkaniny** (kritik nábytku, 30. 9. 2026). Švy jako
  tmavé proužky na rovné ploše působí nakresleně. Řešení: polštář jako výšková plocha se sdílenými vrcholy
  (`kit_geo.Part.mesh`, `kit_furniture.pad`): zaoblený okraj, vyboulená pole mezi švy, šev jako prohlubeň, důlek
  s knoflíkem. `Part.quads` dělá každou plochu zvlášť (hranaté stínování). Matrace 2,1 m ~7,5 tis. trojúhelníků.
- ev) **Karta špíny visí před plochou** (30. 9. 2026). `Part.grime(at, normal)` položí kartu na první zásah paprsku;
  míří-li na tlačítko nebo rám 1–2 cm před panelem, karta visí ve vzduchu. Řešení: `at` na místo, kde paprsek trefí
  panel samotný.
- ew) **Decal na lisovaném poli zmizí** (30. 9. 2026). Pole je 12 mm za čelem dveří a decal s `max_depth_cm` 1,5 se
  středem 5 mm před čelem na něj nedosáhne. Řešení: střed decalu na čelo (≤ 15 mm od dna pole, pozor na zadní stranu
  desky); popisek celý uvnitř pole nebo celý na rámu.
- ey) **Nápis na pravoboku vzhůru nohama, i když test decalů prošel** (recenze exteriéru 30. 9. 2026). WAYFARER, HF-0417,
  logo a výstraha u trysky měly v `Wayfarer_setup.json` rotaci `[0, 90, -90]` místo `[0, 90, 90]`: text se četl
  pozpátku a vzhůru nohama, což vypadá jako zrcadlení, ale je to otočení o 180°. Test hlídal jen zrcadlení (počet
  flipů). Řešení: `test_decal_orientation.py` pravidlo 3, text na stěně musí mít „nahoru“ (−Y komponenty, s `flip_v`
  +Y) nahoru v prostoru lodi. Pravobok = levobok s opačným yaw a **stejným** roll.
- ez) **Druhá dávka nových položek atlasu by posunula první** (1. 10. 2026). `pack` řadil všechny položky s `append`
  dohromady podle výšky, takže vyšší nová položka by předběhla `st_rails` z dávky kitu a posunula UV hotových meshů.
  Řešení: `append` je název dávky a dávky se balí v pořadí prvního výskytu; po přestavbě porovnej `uv` starých
  položek v `decal_library_index.json` (má být beze změny).
- ds) **Stínovaná obdélníková světla bez MegaLights jsou drahá.** Dvě stínovaná světla kitu v chodbě bez MegaLights
  (osvětlení jako v letu): stínové mapy 7,3 ms a světla 5,5 ms (26 ms celkem). V lodi mají stín jen v režimu interiéru
  (MegaLights je trasuje), v letu ne; počet světel pod MegaLights cenu skoro nemění (8 i 12 světel: 3,5 ms).
- bo) **Kontrola geometrie před každým předáním:** od 27. 9. 2026 ji spouští sám `hs_assemble_ship.py` jako poslední krok každé přestavby lodi (při FAIL skončí Blender kódem 1, řádek `HSASSEMBLE GEOTEST FAIL`); ručně `python Tools/Tests/test_ship_geometry.py` (Blender headless na
  `<Loď>_HS_Game.blend`, ~15 s): zrcadlené decaly, plovoucí díly, průniky, placeholdery, díry viditelné hráči.
  Musí projít (autor 25. 9. 2026).
- fb) **Šablona „z boku“ dopadla metr od svého poklopu** (1. 10. 2026). Decaly, funkční díly a světla s `"on": "side"`
  hledá paprsek z boku lodi proti celé lodi (`hs_decals`, `hs_functional`, `hs_lights`), takže trefí **nejbližší** díl:
  HYDRAULICS (x 1,9, z 0,72) dopadl na gondolu, slot ve výšce 0,9 na zbraň, konektor na hranu křídla. Kit poklopy
  (`greebles`) se kladou jen na trup, a tak jejich šablony skončily jinde než ony. Řešení: kam co dopadne, ukazuje
  model výkresu (`Tools/Design/exterior_model.py`, `landing`; na listu E-01 „Kontrola dat“); prvek mezi gondolou
  a trupem polož paprskem `"on": "ray"` z mezery (`at` mezi trupem a gondolou, `dir` k trupu).
- fe) **Navržené desky by zakryly postavené prvky na plášti** (1. 10. 2026, kritik výkresu E-01 kolo 2). Desky
  koncept B + C stojí 30–40 mm nad pláštěm; světelné pásy, kryty kabelů, konektor a čočka světlometu ležely v ploše
  desek. Řešení v datech návrhu: `panels.cut_hardware` vyřízne v deskách místo pro každý díl na boku trupu
  (okraj `cut_margin`), světelné pásy jdou na rám (`"on": "frame"`: podélník, těsnění kabiny). Hlídá to
  `test_exterior_drawing.py` (žádný díl pod deskou bez výřezu, žádný nápis na podkladu stejného tónu).
- ff) **Přestavba přepsala i FBX, jejichž geometrie se nezměnila** (1. 10. 2026). Kabina, podvozek, hologram,
  obrazovky a kit měly ve dvou stavbách z týchž dat bit po bitu stejné meshe, ale jiný otisk souboru. Příčina:
  otisk obsahoval `repr()` nastavení exportu a `object_types` je množina řetězců; její pořadí se řídí náhodným
  hashem řetězců každého procesu (`PYTHONHASHSEED`), takže otisk vyšel náhodně jedním ze dvou způsobů. Řešení:
  `settings_key()` píše množiny seřazené, stejně jako otisky v manifestech
  (`test_file_digest_ignores_the_string_hash_seed`). Skutečný šum stavby zůstává jen v trupu, decalech
  a interiéru (±40 trojúhelníků mezi běhy). Ověřené porovnáním staveb A/B1/B2/C (recept s klíči `id` a bez nich).
  Vyřešeno 2. 10. 2026 (fl): náhodná pravidla decalů už nezávisí na pořadí stavby – změna kitu nebo jiného pravidla
  nepřelosuje decaly jinde. Nevyřešeno: šum ±40 trojúhelníků trupu a interiéru (paprsky decalů pak mohou padnout
  na jinou plochu – poloha se pohne o zlomek milimetru, ne decal na jiné místo), 3 FBX při každé přestavbě.
- fg) **Přestavba „prošla“, ale export vynechal všechny FBX jako nezměněné** (1. 10. 2026, kit pilot kolo 2). Výjimka
  v `--python` skriptu Blender neukončí chybou: `hs_assemble_ship.py` spadl v `kdop_hull` (po 12 pokusech o kolizi
  bez tenkých stěn použil uvolněný bmesh; spustily to nové díly kitu na zádi), Blender skončil kódem 0, game blend
  zůstal z minulé stavby a export ho správně poznal jako nezměněný. Řešení: Blender v dávce vždy s
  `--python-exit-code 1` (výjimka pak vrátí 1) a po stavbě zkontroluj čas `<Loď>_HS_Game.blend`; `kdop_hull` po
  vyčerpání pokusů použije kvádr oblasti.
- fh) **Řez trupem na výkresu interiéru neměl břicho** (1. 10. 2026, list I-04). Řez v x 12,50 vrátil jen střechu:
  panely břicha mají švy přesně na stanici 12,50 a řez s přísným znaménkem (`d <= 0 < d`) vynechal každý trojúhelník,
  který rovinu jen „ťukne“ vrcholem. Řešení v `mesh_draw._slice`: vrchol v rovině patří za řez (`d >= 0`), hrana se
  bere při `da < 0 <= db`. Výšky trupu na ose interpoluj podél úseček řezu (koncové body dlouhého panelu leží až na
  krajích). Taky: výběr trojúhelníků trupu podle středu v boxu kolem místnosti zahodil dlouhé panely břicha –
  pro řez ber celý mesh.
- fj) **ID interiéru v receptu by zneplatnila všechny listy exteriéru** (1. 10. 2026). Otisky dat na listech E-01–E-08
  jsou otisky celých souborů (recept, layout, setup); jakýkoli zápis do nich (i klíč `"id"`, který stavba ignoruje)
  žádá překreslit 8 listů (~20 MB PNG v LFS) a v paralelní práci dělá binární konflikty. Řešení: ID interiéru jsou
  v `Design/<Loď>_interior_design.json` navázaná na data stavby klíčem, který test ověřuje, a otisky interiéru se
  počítají jen z interiérové části dat (`interior_model._digests`).
- fj) **`kit_build.py -- <dávka> --only <díl>` uložil `Kit_<Dávka>.blend` jen s tím dílem** (1. 10. 2026, oprava dveří
  hygienické buňky). Skript na konci ukládá celou scénu jako blend dávky, a `--only` staví jen vybrané díly, takže
  z archivu zmizí ostatní (lůžko, skříň, výdejník; `kit_layout.kit_blends` a `kit_clash.py` hledají díly v blendech).
  `--only` stačí na rychlou kontrolu; do commitu přestav celou dávku. FBX dílů, jejichž geometrie se nezměnila, se
  liší jen časovým razítkem: porovnej je (`fbx_mesh.read`) a nezměněné vrať, ať v LFS nevznikají kopie. Jméno pro
  `--only` je celé jméno meshe (`SM_Kit_Furniture_Hygiene15L_A`), krátké jméno nepostaví nic („parts": 0).
- fk) **Po sloučení rovných ploch uletěla deska o 15–420 m / dno kanálu zčernalo** (1. 10. 2026, rozpočet trojúhelníků
  krok a). Solidify s `use_even_offset` na sloučených (nekonvexních, degenerovaných) n-úhelnících vymrštil vrchol
  desky detailu P-B: export zastavil jen první případ („Ship is 424.94 m across“), druhý (−16 m) chytil až
  `test_landing_sc2` (spodek trupu pod podvozkem). Řešení: `hs_build_part.planar_merge` (rozpuštění degenerovaných
  ploch, triangulace) a u desek detailu solidify bez rovnoměrné tloušťky. Sloučená velká plocha má málo vrcholů
  a AO pečené do vrcholů (`hs_layers`) se přes ni roztáhne: dno kanálu (slot Channel) se na plášti neslučuje
  (`parts.hull.merge_keep_slots`). Příčina ulétlých desek: rovnoměrná tloušťka dělí posun vrcholu sinem úhlu mezi
  sousedními plochami a na sloučených n-úhelnících s téměř nulovými úhly (protáhlé trojúhelníky po triangulaci) jde
  dělitel k nule. Od 1. 10. hlídá meze dílů přímo `hs_assemble_ship` (`HSASSEMBLE BOUNDS FAIL`, chyba sestavení).
- fl) **Po změně kitu se přesunula špína na dveřích rampy** (2. 10. 2026, krok b rozpočtu trojúhelníků). Vedle nápisu
  RAMP – STAND CLEAR přibyla stékající šmouha, ačkoli se mřížky ani pravidlo nezměnily. Příčina: náhodná pravidla
  decalů (`clusters`, `companions` – šmouhy pod mřížkami, štítky, `coverage`, `panel_lines`) brala čísla z jednoho
  sdíleného generátoru v pořadí stavby. Šrouby a poklopy kitu jako decaly přidaly rámy a pokusy, proud se posunul
  a každé další losování dopadlo jinak. Řešení: každé losování má vlastní generátor ze `seed` + pravidla + **klíče
  prvku** (`hs_decals._rng`: shluk a číslo pokusu, rodičovský decal doprovodu podle polohy, buňka mřížky coverage,
  pole panelové čáry), ne z pořadí. Stavba zapíše polohy náhodných decalů podle klíče do `Export/<Loď>_decals.json`
  (`random`, s předchozí stavbou v `random_prev`) a `test_kit_decals.py` ověří, že stejný prvek leží po dvou
  přestavbách za sebou na stejném místě (1 cm: šum sítě trupu z ff posune zásah paprsku o 1–8 mm, přelosovaný decal
  skočí o decimetry nebo změní položku). Po změně `seed` nebo pravidel test přeskočí (otisk vstupů
  `rules_hash`) – pak přestavět dvakrát. Oprava sama jednorázově přelosovala všechny náhodné decaly.
- fn) **Na výkresu nákladu chybělo šest nápisů a hasicí přístroj, světel bylo o dvě víc** (2. 10. 2026, kritik I-02).
  Model výkresu bral místnost bodu z obdélníku layoutu (y ±1,90), ale obložení nákladu z kitu je na ±2,05: nápisy na
  něm (y ±2,025) vypadly, a vnější reflektory gondol nad stropem (z 2,59) prošly filtrem výšky jako světla nákladu.
  Řešení: `interior_model._room_spaces` (místnost = obdélník rozšířený k lícům stěn kitu), světla exportu nad stropem
  kit místnosti jdou na exteriér; vybavení lodi z `interior.kit.fittings` má vlastní ID. Kit platí před layoutem.
- fo) **Světlá výška pod žebrem kabiny vyšla víc, než je** (2. 10. 2026, I-01: 2,08 místo 2,05). Řez rovinou x vrací úsečky s konci na
  hranách trojúhelníků; spodní plocha žebra přes celou šířku dala úsečku s konci daleko mimo pás y ±0,3, takže filtr
  koncových bodů ji vynechal. Úsečky se před hledáním minima ořezávají na pás (`DeckSheet.clear_height`). Pozor i na
  odečet z výkresu: v podélném řezu se žebro kreslí níž, než je nad hlavou, protože jde dál k boku za rovinou řezu.
- fp) **Knihovna decalů spadla na `ImportError: cannot import name '_imaging'`** (3. 10. 2026). Blender 5.2.2 má Python
  3.13, systémový Pillow je pro 3.12 a `borrow("PIL")` ho přidá do cesty. `decal_library.py` pak PNG zapíše a čte
  vlastní náhradou z numpy a zlib (`_PngImage`, `pil_image()`); výsledek je pixelově stejný (ověřeno na trim sheetu).
- fq) **Stavba lodi spadla v `hs_decals` na `KeyError: 'pn_K'`** (3. 10. 2026, revize G). Čísla desek se skládají ze
  znaků `pn_<znak>`, knihovna měla jen R, L, P, S a číslice. Nové znaky se přidávají jako nová dávka `append`
  (stávající položky atlasu se neposunou); test výkresu teď hlídá i znaky čísel z rozvrhu kitu.
- fr) **Loď na svahu stála na vzduchu nebo ležela trupem v terénu** (3. 10. 2026). Kořenový box Wayfareru je celá loď
  (21,5 × 14,7 m) až dolů k patkám, takže na svahu jeho rohy narazily na zem dřív než patky nebo trup. Pohyb lodi
  teď sweepuje vlastní kolizi trupu (UCX, `SweepHullParts` přes `ComponentSweepMulti`), přistání stojí na třech
  patkách (`TripodRest`, paprsky pod sockety `Gear_*`). Komponentový dotaz bere odezvy té komponenty, proto trup
  blokuje i `WorldStatic` a `WorldDynamic`; co se počítá, filtruje `BlocksShip` (jen to, co blokoval box: ne postavy,
  jinak pilot v kokpitu „zablokoval“ přistání).
- fs) **Přistání na rovném svahu odmítnuté jako `Obstructed`** (3. 10. 2026). Kontrola světlé výšky trupu počítala
  i kolizní blok podvozku (UCX_09, 5,3 m široký kvádr v úrovni patek), který se každého hrbolku mezi patkami dotkne.
  Tvary, které sahají do 50 cm nad patky, jsou podvozek a kontrola je vynechá (`HullClearOfGround`).
- ft) **Python v UE: bool UFUNCTION s výstupními parametry** nevrací `(ok, out1, …)`, ale jen výstupy, nebo `None`,
  když funkce vrátila false (`compute_tripod_rest`). `unreal.Rotator` nemá `rotate_vector`; otáčej přes
  `get_forward_vector` / `get_right_vector` / `get_up_vector`.
- fu) **`fetch_video.py` spadl na `FileNotFoundError`** (4. 10. 2026, nový PC). Chyběly ffmpeg a ffprobe, yt-dlp je jen
  jako modul (`python -m yt_dlp`, skript ho tak volá). Nainstalováno `winget install Gyan.FFmpeg`; aliasy ve
  `WinGet\Links` Git Bash nenajde, přidej na PATH složku `...\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*\bin`.
  Snímky z cizího videa nejdou do gitu ani ve srovnávacích listech kritika (`.gitignore` u recenze).
- fv) **Hra spadla na `Assertion failed: Addr < GetData() || Addr >= ...` (Array.h)** (4. 10. 2026, menu). `Line.Add(Line[0])`
  předá referenci do vlastního pole; když `Add` pole zvětší, reference míří do uvolněné paměti. Prvek si nejdřív zkopíruj.
- fw) **Nastavení „Ostření“ nemělo vliv** (4. 10. 2026). `r.Tonemapper.Sharpen` byl v `[SystemSettings]` v
  `DefaultEngine.ini`; ta priorita přebíjí `ECVF_SetByGameSetting`. Co má ovládat menu, nesmí být v ini.
- fx) **VÝCHOZÍ v menu vracelo hráčovy uložené hodnoty** (4. 10. 2026). `GetDefault<USpaceUserSettings>()` (CDO) se načítá
  z `GameUserSettings.ini`, takže drží uložené hodnoty, ne výchozí. Výchozí hodnoty jsou v `SetGameDefaults()` (v kódu).
- fy) **UE test prošel všemi body, ale `Test.ps1` hlásil exit 1** (4. 10. 2026). `LevelEditorSubsystem.new_level("/Temp/x")`
  zaloguje `Error`, když level v `/Temp` už existuje, a commandlet pak vrátí 1. V testech `load_level` existující mapy.
  Herní subsystém v testu: `unreal.new_object(Třída, outer=unreal.new_object(unreal.GameInstance))`.
- fz) **Hologram MFD pořád četl jako monitor** (4. 10. 2026). Displej byl skleněný panel v zapuštěném rámu s deskou za
  sklem; materiál obrazovky klíčuje obsah podle jasu, takže všechno tmavé ukáže desku, a slabé plné výplně (záře,
  pruhy, viněta) klíčování zesílí na plné bloky. Řešení: geometrie (pod bez otvoru, emitor, obraz nad ním bez desky,
  `hs_cockpit.holo_projector`); záře kreslit jen podél obrysů. Snížený pod nechal škvíru u bočního obložení
  (GEOTEST holes): vnější hrana podu zůstává ve staré výšce jako svislý schod (`pod_outer_low`).
- ga) **`HeavyLock.ps1 run -Exec "bash …"` nenašel bash** (4. 10. 2026). PowerShell nemá Git Bash v PATH: v `-Exec`
  plná cesta `& '<git>\bin\bash.exe' skript.sh` (`(Get-Command git).Source` vrátí `cmd\git.exe`, bash je v `bin\bash.exe`).


---

## 10. Kam dál

Přesunuto do `Docs/CURRENT.md` (Další kroky). Původní seznam priorit k 19. 9. 2026:
`Docs/Archive/workflow-kap10_2026-09-19.md`.

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
