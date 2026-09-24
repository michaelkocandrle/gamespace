---
name: unreal-shots-and-look
description: Visual verification and look tuning of the packaged Unreal game - Tools/Shots.ps1 screenshot presets (Tools/Shots/*.json, shot fields, -Package/-Keep/-Width 1920 -Height 1080), contact sheets, measure_look.py / measure_flicker.py, live console tuning (space.Post, space.Sun, space.Sky, space.ShipMat, space.Kit*, space.KitLight), scene light/grade/exposure, performance measurement (perf_* presets, stat unit, Unreal Insights) and UE 5.8 rendering traps (Nanite+TSR smear, translucency sorting, TSR ghosting, Custom node, auto exposure). Load whenever you change anything visible, need screenshots, tune lighting/materials/post process, or measure FPS.
---

# Snímky, vzhled scény a výkon (UE 5.8)

Zdroj pravdy: `Docs/WORKFLOW.md` kap. 6 (Shots), 6.1 (ladění za běhu), 7.3, 9.2 (nástrahy
vykreslování + Insights), 11 (vzhled scény); `Docs/HANDOFF.md` kapitola o snímcích (~ř. 1370)
a body 35, 42, 64, 65, 72.

## Základní pravidla

- **Vzhled se posuzuje jen v zabalené hře** (`C:\gamespace\Builds\Gamespace\Windows\gamespace.exe`).
  Uncooked `-game` kreslí nové materiály šedě; PIE/editor se nespouští.
- **Každý snímek si sám prohlédni** (Read na PNG) a porovnej s referencí (`starcitizenreference/`,
  `Docs/UI/`, `ArtSource/Reference/Mood/`). Autorovi napiš, co na snímcích je, a odděl, co musí
  posoudit sám (pocit, plynulost, jas na jeho monitoru, čitelnost za pohybu).
- Autor hraje **1920 × 1080 na RTX 2060 6 GB**. Výchozí `Shots.ps1` je 1600 × 900 → FPS o ~40 %
  lepší a písmo RT jinak ostré. Na výkon, jas a čitelnost vždy `-Width 1920 -Height 1080`.
- Hra během snímků převezme popředí okna. Když hra běží, balení se zasekne / nakopíruje starý exe –
  hru nikdy neukončuj sám, požádej autora. Předem se neptej, jestli běží: balení pusť a zkontroluj čas exe.

## Tools/Shots.ps1

```powershell
.\Tools\Shots.ps1 -Preset cockpit                     # vyfotí existující balíček (~20–60 s)
.\Tools\Shots.ps1 -Preset cockpit -Package            # nejdřív Tools\Package.ps1 (~5 min); nutné po změně C++ nebo Content
.\Tools\Shots.ps1 -Preset sc_look -Width 1920 -Height 1080
.\Tools\Shots.ps1 -Preset hud -Keep                   # kopie i do Docs\Shots\<preset>\<čas>\ (jde do gitu)
.\Tools\Shots.ps1 -List C:\cesta\muj.json             # scénář mimo Tools\Shots (třeba ve scratchpadu)
.\Tools\Shots.ps1 -Last                               # vypíše nejnovější sadu
# -TimeoutSeconds 180 je výchozí; u dlouhých scénářů (flicker_check 33 snímků) zvednout
```

- Výstup: `Saved\Shots\<yyyyMMdd_HHmmss>_<preset>\NN_<name>.png` (NN = pořadí). `Saved\` není v gitu.
- Konec výpisu `RESULT: OK - N picture(s)`; bez snímků `RESULT: FAILED` → `Saved\Logs\gamespace.log`, hledej `SHOTS`.
- `WARNING: ... changed after the last package` = snímky ukazují starý build → `-Package`.
- **Scénář JSON se čte z disku za běhu** – změna scénáře ani konzolových hodnot nepotřebuje balení.
- Za běhu hry (`~`): `space.Shot nazev` (do `Saved\Shots\manual`), `space.Shots <cesta.json>`.
- Ruční spuštění (např. pro trace): `gamespace.exe /Game/Maps/TestSpace -windowed -ResX=1920 -ResY=1080
  -nosplash -unattended -ShotList="<json>" -ShotOut="<složka>"`.
- Runner: `Source/gamespace/SpaceShotRunner.cpp/.h` – autoritativní seznam polí.

### Pole snímku (`{"_comment": "...", "shots": [ {...}, ... ]}`)

| skupina | pole |
| --- | --- |
| kamera | `camera`: `cockpit` / `chase` / `free` / `pawn` (kamera postavy); `chase_yaw`, `chase_pitch` (>0 zespodu), `chase_zoom`; free: `camera_location`, `camera_look_at` [m, svět], `fov`, `exposure` (připíchne auto expozici; nákladový prostor ~2,0) |
| poloha | `altitude_m`, `facing`: `horizon` / `planet` / `away` / `body:<jméno>` (např. `body:Orun`) |
| let | `speed_ms` nebo `drift` [vpřed, vpravo, nahoru] m/s, `boost`, `afterburner`, `stick`, `mode` (`SCM`/`NAV`), `limiter`, `coupled`, `gsafe`, `comstab`, `precision`, `gear`, `lower_gear` (krátký `settle` chytí půlku vysouvání) |
| quantum | `quantum`, `quantum_progress`, `quantum_ready` |
| kokpit | `cockpit_eye`, `hide_hull`, `hide_canopy`, `cockpit_light` [key, fill], `display_light`, `interior_tint` |
| ostatní | `name`, `hud` (0 nic, 1 letový HUD, 2 + krátký text, 3 + plný text), `settle` [s], `console` [příkazy] |

- `console` **platí do konce běhu** – další snímky nastavení dědí, A/B pak vyjde falešně. Buď stav po
  vrstvách (poslední snímek = vše dohromady, vzor `look_final`), nebo každá varianta začne resetem
  (`space.KitReset`; u lodi znovu vypsat všechny parametry, vzor `hull_tune`, `plastic_diag`).
- **První snímek zahoď** (loď se nestihne ustálit) – dej tam `warmup` / `z_warmup`.
- Nízká `altitude_m` + `gear` + pár s `settle` loď opravdu posadí. Po velkém přesunu se staví terén:
  `settle` ≥ 2 s, po skoku z 20 km na zem až 12 s (`rocks_look`).
- S `chase_yaw` je nahoře nápis FREE LOOK – to je v pořádku.

## Prohlížení a měření snímků

```bash
python Tools/Shots/sheet.py <složka> <out.png> [sloupců=2] [šířka=800]   # kontaktní list s názvy souborů
python Tools/Shots/measure_look.py <složka>          # LOOK: mean, p10/50/90/99 jasu, sytost, B/R, detail (1. snímek přeskočí)
python Tools/Shots/measure_flicker.py <složka> <mapa.png>   # FLICKER: % pixelů měnících se >8 % mezi stejnými snímky
```

- Listy a výřezy ukládej do scratchpadu, ne do repa. Malé prvky vyřízni a zvětši; v 1600 × 900:
  levý MFD ~495–710 × 640–825, pravý ~893–1105 × 640–825, střední sloupek ~745–855 × 630–880 px.
- Cílové rozsahy SC pro interiér (hlavička `measure_look.py`): mean 0,13–0,23, p50 0,08–0,18,
  p90 0,32–0,53, p99 0,56–0,88, B/R 0,72–1,05 (teplé < 1 < studené), detail 0,024–0,035.
  Letový kokpit SC nad planetou: mean 0,13–0,19 (náš po bodu 72: 0,10–0,19, ve vesmíru 0,05).
- Rozdíl variant měř (průměrná odchylka jasu, % změněných pixelů), ať nehádáš, jestli je změna vidět.
- Při 400 m/s nejsou dva snímky stejně zarámované → absolutní ostrost (Laplace) skáče o desítky %.
  Statické věci měř ve stoje, pohyblivé 2× za nastavení (rozdíl dvojice = chyba měření), raději
  poměrem (směrovost rozmazání) než absolutním číslem (WORKFLOW 11.4).
- `measure_flicker.py` maskuje FPS počítadlo od x = 1350 → počítá s šířkou 1600 px.

## Ladění za běhu (konzole, nic se neukládá)

Varianta přes recept + balení stojí ~4 min, přes konzoli v jednom běhu ~20–30 s. Hotová čísla pak
přepiš do receptu (po restartu hry je vše zpět podle úrovně).

| příkaz | účel |
| --- | --- |
| `space.PostList <část>` / `space.Post <Nastavení> <hodnoty...>` | post process přes reflexi; barvy po složkách (`space.Post ColorGain 1 1 1.04 1`) |
| `space.PostDump` | přepsané hodnoty jako řádky `POST_SETTINGS` pro `build_space_scene.py` |
| `space.Sun <Vlastnost> <h>` / `space.SunDir <pitch> <yaw>` | směrové světlo (`Intensity`, `ContactShadowLength`, `LightSourceAngle`, `SpecularScale`) |
| `space.Sky <Vlastnost> <h>` / `space.LightList sun\|sky <část>` | sky light (`Intensity`, `CubemapResolution`) |
| `space.ShipMat <Param> <h>` / `space.ShipMatColor <Param> r g b` | materiály lodi (`DetailNormalStrength`, `DetailTileCm`, `PanelStrength`, `BaseColorTint`…) |
| `space.Kit <Param> <h> [filtr]` / `space.KitColor` | materiály interiéru (`Lift`, `MetallicScale`, `RoughnessFloor`, `Gunmetal`, `WearAmount`, `WearEverywhere`, `GrimeAmount`); filtr `MI_T_` = trim sheety |
| `space.KitLight Work\|Accent\|All <Vlastnost> <h>` | světla interiéru (`Intensity` v lm, `UseTemperature True`, `Temperature`, `LightColor R G B`, `OuterConeAngle`) |
| `space.KitReset` | interiér + slunce + sky zpět na úroveň – první příkaz každé varianty |
| `space.Interior`, `space.Walk <vpřed> <vpravo> <s> [°]`, `space.Door 1\|0\|-1` | interiér Steadfastu, chůze (log `WALK end at …`), dveře |
| `space.CockpitPitch`, `space.DashboardFocus 1`, `space.MfdPage <L> <R>`, `space.Hud 0-3` | kokpit a HUD |
| `space.Atmo`, `space.SkyParam`, `space.Dust` / `DustList`, `space.Tunnel` / `TunnelList`, `space.Sparks`, `space.Vtol` | atmosféra, materiál oblohy, prach, quantum tunel, jiskry, VTOL |
| `space.CockpitKeepWindow`, `space.HudLineBatch` (1/0) | A/B přepínače výkonu displejů a HUD (9.2 g) |

Kód: `Source/gamespace/SpacePostTuning.cpp`, `Source/gamespace/SpaceInteriorTuning.cpp`.

## Smyčka vzhledu scény (WORKFLOW 11.2)

1. Scénář `Tools/Shots/<x>.json`, každá varianta s `console` (vzory `look_sun`, `look_fill`,
   `look_final`, `interior_tune`).
2. `.\Tools\Shots.ps1 -Preset <x>` bez `-Package`, pokud se neměnil C++ ani obsah.
3. Kontaktní list + měření; variantu vyber podle obrázků, ne odhadem.
4. Přepsat: scéna → `Tools/Assets/build_space_scene.py` (`SKY_LIGHT_INTENSITY`, `SUN_CONTACT_SHADOW_M`,
   `SUN_SOURCE_ANGLE_DEG`, `POST_SETTINGS`); loď → `ArtSource/Ships/<Loď>/<Loď>_setup.json`.
5. `.\Tools\run_editor_python.ps1 Tools\Assets\build_space_scene.py` (+ `import_ship.py` při změně
   materiálu lodi), test `Tools\Tests\test_scene_look.py` (úroveň proti receptu), balení, snímky.

### Platné hodnoty a zjištění

- Loď v kosmu je silueta, když nic nesvítí do stínu: **sky light 0,7**, `base_color_tint` 3,2
  (sky pod 0,5 = černý trup, nad ~1,1 planeta ztrácí terminátor). Směr slunce nepomáhá.
- Contact shadows 0,08 m a slunce 0,5° jsou zadarmo. Grade: ColorContrast 1,08, ColorGain 1 1 1,04,
  ColorSaturation 1,06, Bloom 0,45, FilmGrain 0,2, Vignette 0,35.
- **Zakázané:** chromatická aberace (`scene_fringe_intensity` = barevné lemy v kokpitu) a vyvážení bílé
  (`white_temp` 6200 zmodrá interiér); hlídá `test_scene_look.py`.
- Film grain, motion blur i TSR stopy změřeny jako neškodné (`look_artifacts`). „Pruhování“ trupu je
  mikrodetail materiálu (`DetailNormalStrength`, `PanelStrength`), ne artefakt.
- Expozice: vesmír pevně EV100 3; `CockpitExposureBias` −0,7 EV (displeje jsou emisivní, kompenzace
  `emissive_strength` 2,9 ve `Vanguard_setup.json`), `QuantumExposureBias` −0,8 (`SpaceshipPawn.h`).
  Kokpit key 1,5 / fill 0,8 (`cockpit_light` ve snímku).
- Interiér podle SC: gunmetal 0,33/0,33/0,34, pracovní světla 5200 K, teplé světelné lišty
  (`MI_KitStrip`, emise 14).
- `r.Tonemapper.Sharpen=0.6` v `Config/DefaultEngine.ini` vrací hranu po TSR.
- Lumen kvalita 2 (reflections, final gather) nic nepřidá a stojí ~1 FPS; GI je jediná drahá skupina.

## Výkon

- Presety `perf_quality` (filmová vs epická po skupinách, TSR 75 %), `perf_interior` (stíny a dosah
  světel přes `space.KitLight`), `look_groups` (cena každé škálovací skupiny). Vždy `-Width 1920 -Height 1080`.
- Čti `stat unit` ve snímku (do `console` prvního snímku); dál `stat Slate`, `stat SpaceCockpit`,
  `stat SpaceHud` (Line batches).
- **Nejdřív zkontroluj RenderRes** ve `stat unit`: hra kdysi běžela na 50 % a vše bylo měkké. Pod 50 % nikdy.
- Aktuální výchozí (HANDOFF 64): **epická, vykreslení 75 %, TSR** (`USpaceUserSettings` verze 4).
  Referenční čísla 1080p: filmová 100 % = 49 FPS interiér / 70 let; epická + TSR 75 % = 70–78 / 90–98.
  Interiér je vázaný na pixely (rozlišení 6 ms, skupiny o stupeň níž 0–1 ms); stíny 22 lokálních
  světel byly většina snímku.
- FPS hned po přesunu lodi nic neříká (terén, herní vlákno 20–30 ms): `settle` ≥ 2 s, A/B ve **stejném
  balíčku** přes `console`, každá varianta v samostatném spuštění hry (průměry `stat` se přelévají).

### Unreal Insights bez GUI

```powershell
& C:\gamespace\Builds\Gamespace\Windows\gamespace.exe /Game/Maps/TestSpace -windowed -ResX=1920 -ResY=1080 -nosplash -unattended `
  -ShotList="<scénář.json>" -ShotOut="<složka>" -trace=cpu,frame -statnamedevents -tracefile="<soubor>.utrace"
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealInsights.exe" -OpenTraceFile="<soubor>.utrace" -NoUI -AutoQuit `
  -ExecOnAnalysisCompleteCmd="TimingInsights.ExportTimerStatistics <soubor>.csv"
```

Na konec procesu čekej (`Start-Process -PassThru`, `WaitForExit`). CSV `Name, Count, Incl, Excl, I.Avg…`
je v sekundách, řaď podle `Excl`.

## Nástrahy vykreslování (příznak → příčina → řešení; podrobně WORKFLOW 9.2)

- **Kokpit a displeje se v rychlém letu rozmazávají a trhají** → Nanite dává špatné motion vectors
  meshi připojenému ke kameře (TSR) → `no_nanite_parts: ["Interior"]`, `MotionBlurAmount 0` na
  kokpitové kameře. Ověř `display_sharpness`.
- **Duchy čísel na displejích (dvě desítky přes sebe)** → TSR prolíná měnící se čísla → opaque + pixel
  animation, stav 5 Hz, kvantování. Translucent, responsive AA ani „after motion blur“ nepomohly.
  Zbytek při afterburneru / tvrdém brzdění zůstává.
- **Blikání / hitch RT displejů** → přestavba RT při FOV kicku → měřítko jen ze šířky okna, práh 0,099.
- **Písmo na displejích zrní pod ~1600 px** → RT nemá mipmapy; čitelnost posuzuj v 1080p.
- **Pád FPS po přidání kreslených čar (herní vlákno +6–17 ms)** → Slate dávkuje čáry kvadraticky →
  jedna tloušťka a vrstva, `GlowLines` jen výjimečně, do RT kresli přes trvalé okno
  (`FWidgetRenderer::DrawWindow`), nikdy `DrawWidget` každý snímek.
- **Loď černá / objekt plochý šedý v buildu** → materiál spadl na default: uzly Transform z Pythonu dají
  nulu, Custom uzel s `Tex.Sample(...)` neprojde v RT hit shaderu → převody v HLSL,
  `Texture2DSample(Tex, TexSampler, uv)`, co jde uzly, nedávej do Custom. Chyba je vidět jen v cook
  logu (`Failed to compile Material`, `%APPDATA%\Unreal Engine\AutomationTool\Logs\...\Cook-*.txt`)
  → po každé změně materiálu snímek.
- **Efekt u vzdáleného tělesa zmizí** → vstupy Custom uzlu jsou float, ne LWC → rozdíl pozic uzlem
  `Subtract` mimo Custom nebo `LocalPosition` s `local_origin=INSTANCE`.
- **Materiál zůstal translucent** → `_fresh_material` znovu použije asset → blend mode a klíčové
  vlastnosti vždy nastav explicitně.
- **Průhledná vrstva nezakryje hvězdy** → translucent jen dobarví → neprůhledné + maska s modrým šumem
  (`MaterialExpressionScalarBlueNoise`, `opacity_mask_clip_value` 0,5).
- **Tmavé „duchy“ za mlhou přes celý obraz** → TSR bez velocity → `enable_responsive_aa` +
  `output_translucent_velocity`.
- **Černé kostičkované čáry přes průsvitné věci** → krycí vrstva kolem kamery se řadí poslední → vyšší
  `TranslucentSortPriority` věcem navrch (záporná priorita řadí před všechno ve scéně).
- **Tenká rychlá čára vyjde tečkovaná** → TSR → plocha natočená ke kameře, šířka ~3 px roste se vzdáleností.
- **Ostrá rovná hrana přes obraz** → neprůhledná „obloha“ na válci → dej ji na kouli.
- **Tmavá scéna vyjde sytě modrá** → auto expozice ji vytáhne → připíchni (`AutoExposureMin/MaxBrightness`
  + `AutoExposureBias`), teprve pak lad emise (měřítko se posune ~6×).
- **Černý pruh na obzoru** → `bottom_radius` SkyAtmosphere nad terénem → pod nejnižší terén. S vlastní
  kopulí `IsSky` přidej `SkyAtmosphereViewLuminance`; v záchytu sky lightu nic nedá → výplň dodat jinak.
- **Bílý klín jen v rychlosti** → poloha kamery v Ticku pawnu je z minulého snímku → přičti
  `LinearVelocity * DeltaSeconds`.
- **Loď vyjede ze záběru v rychlém letu z boku** → `CameraLagMaxDistance = 0` znamená „bez stropu“ →
  vypni `bEnableCameraLag`.
- **Obraz měkký** → RenderRes nebo škálovací skupiny na Medium (HANDOFF 35, 42) → zkontroluj `stat unit`
  dřív, než začneš podezírat model nebo materiál.
- Poly Haven `dimensions` jsou v mm.

## Presety (`Tools/Shots/*.json`)

| preset | obsah |
| --- | --- |
| `cockpit` | oko pilota, displeje, rám + chase – po každé změně lodi nebo kamery |
| `cockpit_light`, `cockpit_tune`, `cockpit_view_tune` | světla kokpitu; oko a tint; výchozí výška pohledu |
| `cockpit_look` | expozice letového kokpitu: `space.Post AutoExposureBias` 0 / −0,5 / −1 / −1,5 |
| `cockpit_centre` | střední sloupek (radar, self status) ve stavech |
| `cockpit_readability` | čitelnost MFD z křesla, `DashboardFocus` |
| `display_sharpness` | ostrost displejů v rychlém letu (Nanite / TSR) |
| `mfd_pages` | stránky MFD ve stavech, které je naplní |
| `hud`, `velocity_vector`, `vtol`, `landing` | HUD ve stavech; značka dráhy (`drift`); VTOL (`space.Vtol`); podvozek a přistání |
| `ship`, `ship_views`, `ship_dark` | loď zvenku; 13 pohledů na nový model; maják jako rim light |
| `hull_detail`, `hull_now`, `hull_tune` | mikrodetail zblízka; trup bez ladění; 6 variant `space.ShipMat` |
| `hull_zones`, `hull_panels`, `hull_scorch`, `hull_decals` | AO / kavita / odřený lak; panelové spáry; spálený plech; nápisy (šmouhy = otočený decal) |
| `plastic_diag`, `plastic_mat` | příčiny „plastového“ vzhledu; kovovost trupu |
| `look_sun`, `look_fill`, `look_tune`, `look_final` | silueta v kosmu: slunce, výplň, post po vrstvách, výsledná volba |
| `look_sharp`, `look_groups`, `look_artifacts` | proč měkký obraz; cena škálovacích skupin; grain / blur / TSR stopy |
| `space_look`, `dust_tune` | přehled prostředí; rychlostní čáry (`space.Dust`) |
| `atmo_tune`, `atmo_tune2`–`4`, `terrain_atmo`, `terrain_look`, `rocks_look` | atmosféra Veyry (`space.Atmo`); opar nad pouští; terén ve 3 měřítkách; kameny (settle 12 s) |
| `quantum`, `quantum_final`, `quantum_look`, `quantum_light`, `quantum_ramp` | quantum drive: HUD, skok, úhly, světlo, první sekundy |
| `tunnel_tune`, `tunnel_variants`, `tunnel_haze`, `sparks_flow` | tunel (`space.Tunnel`), jiskry (`space.Sparks`), stěny, dosah plamene |
| `playtest_fixes` | opravy z playtestu SC-1c / SC-4 bez konzole |
| `steadfast_interior` | interiér Steadfastu: nákladový prostor, chodba, strojovna; free kamera, pevná expozice |
| `interior_tune`, `ceiling_tune`, `accent_tune` | materiály a světla interiéru (`space.Kit*`, začíná `KitReset`); strop; oranžové akcenty |
| `sc_look`, `sc_tune` | interiér s auto expozicí proti SC (`measure_look.py`, 1080p); barevné varianty SC vzhledu |
| `wear_check`, `wear_tune` | opotřebení zblízka; `WearAmount / WearEverywhere / GrimeAmount` |
| `flicker_check` | každý pohled 8× stejnou kamerou → `measure_flicker.py` |
| `perf_quality`, `perf_interior` | výkon v 1080p (kvalita, TSR 75 %); stíny a dosah světel interiéru |
| `interior_walk` | chůze postavy (`camera: pawn`, `space.Walk`), výsledek i v logu |

Nový preset: zkopíruj nejbližší, napiš `_comment` (co, proč, `Run: Tools/Shots.ps1 -Preset <x> ...`)
a první snímek udělej jako warmup. Přidej ho i do tabulky presetů ve WORKFLOW kap. 6.
