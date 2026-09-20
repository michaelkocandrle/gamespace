# Gamespace – pracovní postup a nástrahy

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

## 2. Loď z AI modelu: Blender → Unreal

Podrobně je to v `Docs/Ships/ShipPipeline.md`. Tady je jen pořadí a místa, kde se chybuje.

### 2.1 Recept → .blend

Recept je `ArtSource/Ships/Vanguard/Vanguard_ai_build.json`. `Tools/Blender/build_ai_ship.py` ho
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
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python Tools/Blender/build_ai_ship.py -- ArtSource/Ships/Vanguard/Vanguard_ai_build.json
cd ArtSource/Ships/Vanguard
MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b Vanguard_Meshy.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"
```

`--no-save` recept jen vyzkouší. Výstup exportu je
`Export/Vanguard_manifest.json` a FBX pro každý díl.

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
(kapitola 3). Displeje ve Vanguardu (19. 9. 2026): `left` a `right` (MFD 29 × 25 cm), `centre_top`
(radar, 11 × 13,5 cm) a `centre_bottom` (self status, 11 × 12 cm) ve středním sloupku. Test
`test_cockpit_displays.py` hlídá, že `texture_rect` v receptu = `ScreenRect` v kódu a že poměr stran
obdélníku odpovídá sklu.

### 2.2 .blend → Unreal

```powershell
$env:GAMESPACE_SHIP_MANIFEST = "C:\gamespace\gamespace\ArtSource\Ships\Vanguard\Export\Vanguard_manifest.json"
.\Tools\run_editor_python.ps1 Tools\Assets\import_ship.py
.\Tools\run_editor_python.ps1 Tools\Assets\build_main_menu.py
```

- Nastavení lodi (pawn, komponenty, materiály, světla, kamera) je v
  `ArtSource/Ships/Vanguard/Vanguard_setup.json`. Po odebrání hodnoty z něj zůstane v Blueprintu
  stará hodnota (nástraha 9.3c).
- `no_nanite_parts: ["Interior"]`: interiér **nesmí** mít Nanite (nástraha 9.2a).
- Materiály staví `Tools/Assets/ship_materials.py`. Displeje používají master `M_Ship_Screen`
  (unlit, opaque, pixel animation, parametr `EmissiveStrength`).
- `build_main_menu.py` po importu obnoví úvodní scénu s lodí.

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

### 3.2 Použití

1. Spusť Blender **s GUI** na pozadí. Socket na `localhost:9876` běží jen s GUI; v `-b` se addon jen
   zaregistruje.
   ```bash
   cd /c/gamespace/gamespace && MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" ArtSource/Ships/Vanguard/Vanguard_Meshy.blend
   ```
2. Buď MCP nástroje `blender` (`get_viewport_screenshot`, `execute_blender_code`…; mnoho jich
   vyžaduje argument `user_prompt`), nebo pomocné skripty v `Tools/Blender/mcp/`, které mluví přímo
   se socketem (fungují, i když MCP nástroje nejsou v session načtené):

| Skript | Co dělá |
| --- | --- |
| `mcp_socket.py` | `send(type, params)`; z příkazové řádky `python mcp_socket.py execute_code '{"code": "..."}'` |
| `mcp_eye_view.py out.png` | kamera v oku (1,74 / 0 / 1,89 m, FOV 88°), backface culling jako v UE, screenshot |
| `mcp_grid.py out.png` | měřicí mřížka na rovině displeje (1 cm žlutá, 5 cm červená, osy zelené) |
| `mcp_measure_openings.py` | paprsky z oka: najde otvor v rámečku a vypíše jeho rohy (u, v) |
| `mcp_corners.py '<json>' out.png` | posune plochy displejů na zadané rohy a vyfotí pohled z oka (displeje, které v JSON nejsou, nechá být) |

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
| `test_ship_import.py` | import Meshy Vanguardu, díly, sockety, materiály |
| `test_landing_sc2.py`, `test_landing_l5.py` | podvozek, přistání |
| `test_ifcs_sc1.py`, `test_boost_afterburner_sc1b.py`, `test_flight_modes.py`, `test_free_look.py` | let |
| `test_character_l6.py`, `test_planet_l3.py`, `test_menu_settings.py` | postava, planeta, menu |

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
| `cockpit_tune` | ladění (tint, světla) |
| `display_sharpness` | ostrost displejů při rychlém letu |
| `cockpit_centre` | střední sloupek (radar, self status): vesmír, horizont, afterburner, vysouvání podvozku, přistání. Obrazovky jsou malé, vyřízni a zvětši oblast ~745–855 × 630–880 px |
| `cockpit_readability` | čitelnost z křesla, přiblížení Z, srovnání se starým okem |
| `hull_detail` | trup zblízka: detailní vrstva materiálu (srovnání se `detail_normal_strength` 0) |
| `mfd_pages` | stránky MFD ve stavech, které je naplní. Vyřízni levý MFD ~495–710 × 640–825 a pravý ~893–1105 × 640–825 px |
| `look_sun`, `look_fill` | proč je loď v kosmu silueta: směr slunce, výplň sky lightu, lak trupu |
| `look_tune`, `look_final` | post process po vrstvách a výsledná volba proti úrovni tak, jak je |
| `hud` | HUD ve všech situacích |
| `landing` | přistání, podvozek |
| `ship_views`, `ship` | loď zvenku |

Pole jednoho snímku:
- základ: `camera`, `altitude_m`, `facing`, `speed_ms`, `boost`, `afterburner`, `stick`, `mode`, `settle`;
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
- **Nikdy nepřidávej** autorovu složku
  `ArtSource/Ships/Vanguard/Export/Meshy_AI_Sci_Fi_Transport_Ship_0918125120_texture_fbx/`. Vždy:
  ```bash
  git add -A -- . ':!ArtSource/Ships/Vanguard/Export/Meshy_AI_Sci_Fi_Transport_Ship_0918125120_texture_fbx'
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

### 9.6 Blender pipeline

- a) **Rám displeje se otočil dvakrát.** Rotace byla v placement matici i v osách `u`/`v`.
  `add_displays` dostává matici bez rotace.
- b) **Otvory rámečků AI modelu nejsou obdélníky** (lichoběžníky, zkosené rohy). Proto `corners`
  místo `rect` a ladění z oka (kapitola 3).
- c) **Jednostranný trup.** Zevnitř je průhledný, proto `lining`. U oka blízko křídla je vidět
  hrubá geometrie.
- d) **Pravý displej má vlevo dole zubatou hranu** rámečku z AI textury. Neopravené.
- e) Oko je navržené pro 16:9 a FOV 88°. Měření z jiného FOV nesedí.

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
5. ~~Světlo a post scény~~ – hotovo 20. 9. 2026 (kapitola 11, HANDOFF bod 36). Navazuje: zóny materiálu,
   dlaždicové PBR a decaly (panelové spáry, nápisy) – to je teď největší rozdíl proti SC.
6. **Odlesky a špína na skle canopy** (jemný fresnel, škrábance).
7. **Silnější záře displejů na rámu** a okolní desce.
8. Doladit zbývající „duchy“ čísel při afterburneru (9.2b).

Velké celky:
- tělo pilota v sedadle;
- lepší model kokpitu (sedadlo, boční stěny);
- chybějící systémy SC HUD (palivo, zbraně, protiopatření);
- SC-2b VTOL a zpětná vazba při visení (HANDOFF kap. 10 a 11).

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
