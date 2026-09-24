---
name: cockpit-displays
description: Cockpit MFD displays, flight HUD and cockpit lighting/exposure in the gamespace UE 5.8 project - UCockpitDisplayComponent / USpaceCockpitDisplays render targets, MFD pages (F1/F2, space.MfdPage, CyclePage), centre column radar and self status, USpaceFlightHud (space.Hud, fonts in Content/UI/Fonts), cockpit key/fill lights, CockpitExposureBias, display readability (font >= 26). Load when changing or debugging anything drawn on cockpit screens or the HUD, cockpit lights/exposure, TSR ghosting/blur on displays, or when running test_cockpit_displays.py, test_cockpit_frame.py, test_flight_hud_sc1c.py or the Shots presets cockpit*, mfd_pages, hud, display_sharpness.
---

# Kokpit: displeje (MFD), letový HUD, světla a expozice

Týká se letového kokpitu s **živými displeji** (kód je obecný; první stíhačka, na které vznikl, byla
24. 9. 2026 odstraněna a nová loď je ve 2D návrhu, takže teď žádná loď živé displeje nemá). Kokpit
Steadfastu má zatím jen **statické**
hologramové obrazovky (`Tools/Assets/draw_holo_screens.py` → `ArtSource/Ships/Steadfast/Interior/Screens/`,
mesh `CockpitScreens.glb`, materiál `M_KitHolo`, HANDOFF bod 66); živá data přijdou, až Steadfast poletí.
Podrobná historie: HANDOFF body 23–33, 32b, 72; postup WORKFLOW kap. 7, nástrahy 9.2 a)–i), 9.3 a).

## Soubory

| Co | Kde |
| --- | --- |
| Komponenta displejů (RT, stránky, světla displejů) | `Source/gamespace/CockpitDisplayComponent.{h,cpp}` |
| HUD + widget displejů (`USpaceFlightHud`, podtřída `USpaceCockpitDisplays`) | `Source/gamespace/SpaceFlightHud.{h,cpp}` |
| Textový debug HUD, cvar `space.Hud` | `Source/gamespace/SpaceDebugHUD.cpp` |
| Kokpitová kamera, světla, expozice, přiblížení | `Source/gamespace/SpaceshipPawn.{h,cpp}` |
| Hodnoty lodi (světla, `cockpit_displays`, emissive obrazovek) | `ArtSource/Ships/<Loď>/<Loď>_setup.json` |
| Písma | `Content/UI/Fonts/` (Rajdhani-Medium/SemiBold, ShareTechMono-Regular + OFL licence), `Custom/` |
| Vstup MFD | `Content/Input/IA_MfdLeft`, `IA_MfdRight`; přidává `Tools/Assets/add_mfd_input.py` |
| Testy | `Tools/Tests/test_cockpit_displays.py`, `test_cockpit_frame.py` (loď z `Tools/Tests/ship_under_test.py`; bez modelu SKIP), `test_flight_hud_sc1c.py`, `test_flight_hud_sc3.py` (značka dráhy letu) |
| Snímky | `Tools/Shots/cockpit*.json`, `mfd_pages.json`, `hud.json`, `display_sharpness.json` |
| Reference SC | `Docs/UI/` (hlavně `Screenshot 2026-09-17 201854.png`), `ArtSource/Reference/Mood/sc_cockpit_*.webp` (lokálně) |

## Jak displeje fungují

- `UCockpitDisplayComponent` kreslí widget `USpaceCockpitDisplays` přes `FWidgetRenderer` do **render
  targetu**, ten jde jako `ScreenTexture` do MID slotu `*_Screens` (`MI_Ship_<Loď>_Screens`, unlit,
  opaque, pixel animation). V editoru jsou obrazovky černé – obsah vznikne až za běhu.
- `USpaceCockpitDisplays` je podtřída `USpaceFlightHud`: **stejné názvy widgetů a stejné `ApplyState`**.
  Nový údaj tedy obvykle = stav v `FSpaceFlightHudState` (make_state) + widget v `BuildTree`.
- **Plátno 1330 × 490 px:** vlevo FLIGHT 0–560, vpravo STATUS 560–1120, střední sloupek 1120–1330
  (radar 0–259, self status 259–490). Každý displej má v receptu `texture_rect`/`texture_size`, stejná
  hustota pixelů na cm skla všude. Otvory v rámu jsou v receptu jako `corners` (ne `rect`), plocha
  sahá ~5 mm pod rámeček (`grow_m`), řez AI skla 6 mm (`cut_depth_m`).
- **Velikost RT = velikost displeje na obrazovce:** `ScreenShareAt88` 0,155 × šířka okna × `Oversample` 1,25.
  Měřítko jen ze **šířky okna** (ne z FOV), přestavba jen při změně měřítka > 0,099 (9.2 c).
- **Dvě frekvence:** stav (čísla) `StateRateHz` – v setupu `cockpit_displays.state_rate_hz` **5**
  (C++ default je 12, platí setup); kreslení `UpdateRateHz` 60. Během změny se čísla kvantují
  (rychlost po 10 m/s, G po 0,5), přesná až v klidu (`USpaceCockpitDisplays::Steady` / `SteadyState`,
  prahy 0,5 m/s a 0,05 G za aktualizaci). Důvod: TSR prolíná čísla měněná každý snímek (9.2 b).
- **Trvalé okno:** kreslí se přes `FWidgetRenderer::DrawWindow` do jednoho `DrawWindow`, nikdy
  `DrawWidget` každý snímek (9.2 g). Platí pro **každý** další widget kreslený do RT.
- **Světla displejů:** Rect lighty na socketech `Display_*` (3 cm před sklem), 8 cd
  (`display_light_intensity_cd`), barva 0,4/0,75/1, dosah `DisplayLightRadiusCm` 160. Malé displeje
  svítí úměrně ploše (`ScreenRect`). Nestínují.
- Kreslí se jen v pohledu z kokpitu. Displeje svítí i s vypnutým HUD (jsou součást lodi).

## Stránky MFD

- Vlevo **FLIGHT → THRUSTERS → NAVIGATION**, vpravo **STATUS → CONTACTS → SELF STATUS**, `UWidgetSwitcher`
  (kreslí se jen zobrazená; po zrychlení FLIGHT/STATUS ~1,0 ms, ostatní 0,6–1,0 ms za snímek).
- Klávesy: **F1** levý, **F2** pravý, **Alt+F1/F2** zpět (Shift = boost, proto ne Shift). `[` `]` jen pro US
  klávesnici – na české klávesnici autora nejsou samostatné klávesy. Enginové debug bindy F1/F2
  (wireframe/unlit) odebírá `Config/DefaultInput.ini` (`-DebugExecBindings`).
- Kód: `UCockpitDisplayComponent::CyclePage(Display, Direction)`, `SetPage(Display, Page)`,
  `USpaceCockpitDisplays::PageTitles`, `SetPages`. Konzole `space.MfdPage <levý 0-2> <pravý 0-2>`.
- **Nová stránka:** titulek do `PageTitles`, widgety do pole stránek v `Screen(...)` v `BuildTree`.
  **Jen se skutečnými daty** – zbraně, štíty, energie, chlazení hra nemá a nic se nepředstírá
  (proto chybí i tlačítka PWR/WPN/THR/SHLD/COOL; přijdou se SC-6).
- Skryté řádky seznamů skrývej **i s jejich linkou** (řádek a linka v jednom boxu).

## Střední sloupek (RADAR, SELF STATUS)

- RADAR `USpaceHudRadar`: shora, nos nahoru, dosah `RadarRangeM` 5 km (kruhy po třetinách), výseč FOV 88°.
  Kontakty z `USpaceCockpitDisplays::MakeRadarContacts` 5×/s (pawny a static meshe s kolizí v dosahu,
  max 24); tělesa jen jako písmeno na okraji a jen do 60° nad/pod rovinou křídel.
- SELF STATUS `USpaceHudShipStatus`: obrys z kolizních hullů lodi (obecné pro každou loď), motory ze
  socketů `Engine_*` podle tahu, podvozek z `Gear_*` (jantarově při pohybu), dole GEAR, tah %, LANDED.
- Vypnout: `space.CockpitCentre 0`. Snímky `-Preset cockpit_centre`; obrazovky jsou malé, vyřízni a zvětši
  oblast ~745–855 × 630–880 px (1600 × 900).

## Čitelnost (rozpočet písma)

- Z oka (~1,3–1,5 m od desky) je MFD na 1080p ~0,4 své velikosti v návrhu (560 px → ~230 px).
- **Minimum písma 26** na MFD, **21** na malých displejích sloupku (RadarRange, RadarHeading, ShipGear,
  ShipThrust), vše ≥ 16. Velká čísla: rychlost ≥ 96, G ≥ 56, režim ≥ 60. Hlídá `test_cockpit_displays.py`.
- Obsah přidávej jen s tímto rozpočtem; detail patří do přiblížení: držet **Z** nebo prostřední tlačítko
  myši (`ASpaceshipPawn::SetDashboardFocus`, konzole `space.DashboardFocus 1/0`) – hlava 15 cm k desce,
  ~19° dolů, FOV ~44°, letový HUD se schová. Poloha ze socketů `Display_*`.
- **Text se nezalamuje ani neořezává.** Přetečení (hodnota přes záložku stránky) uvidíš jen na snímku.
- RT nemá mipmapy: pod ~1600 px šířky okna může písmo zrnit (9.2 f).

## Letový HUD

- `USpaceFlightHud` celý v C++ (bez widget Blueprintu). Rozložení změřené z SC při 1080p od středu,
  paleta ledově azurová, Rajdhani Medium se slabým azurovým obrysem. Kreslené prvky `USpaceHudSymbol`,
  `USpaceHudTape`, `USpaceHudLadder`, `USpaceHudGauge`, `USpaceHudLamp` (+ radar/ship status pro displeje).
- `space.Hud`: 0 vypnuto, **1 jen letový HUD (výchozí)**, 2 + kompaktní text, 3 + plný debug text.
  Klávesa **H** cykluje, menu nastavení to ukládá. Ve snímku pole `"hud": 0–3`.
- HUD v kokpitu i zvenku stejný (záměr, jako SC hledí); podrobnosti nesou MFD.
- Značka dráhy letu (SC-3) se počítá v `USpaceFlightHud::ApplyView` z ohniskové délky, v jednotkách 1080p
  plátna; test `test_flight_hud_sc3.py`.
- **Čáry:** všechny přes `SpaceHudStyle::PaintLine` do fronty, kořen (`NativePaint`) je vydá seřazené
  podle vrstvy a tloušťky. V kreslených widgetech **jedna tloušťka a jedna vrstva** pro všechny čáry,
  `GlowLines` (3 dávky na čáru) jen na pár krátkých prvků. Barva dávku nerozbíjí.

### Písmo

- TTF v `Content/UI/Fonts`, staguje `Config/DefaultGame.ini`:
  `+DirectoriesToAlwaysStageAsUFS=(Path="UI/Fonts")` – cesta **relativní ke Content** (s `Content/UI/Fonts`
  se nestagovalo nic a HUD v balíčku padal na Roboto, 9.3 a). `Tools/Package.ps1` písmo v buildu kontroluje.
- Vlastní písmo: první `.ttf`/`.otf` (podle jména) v `Content/UI/Fonts/Custom/` (v `.gitignore`) použije HUD
  i displeje (`CustomFont()` v `SpaceFlightHud.cpp`); pak znovu zabalit.
- **Písmo ze Star Citizen nevytahujeme ani nestahujeme z neoficiálních zdrojů.** Jména v UI naše (Veyra,
  Keth, Orun, Halcyon), ne ze SC.

## Světla a expozice kokpitu

- Key + fill (setup první stíhačky, dobrý výchozí bod): `cockpit_light_intensity_cd` 1,5, offset [80, 0, −10], radius 250 cm,
  source radius 12 cm; `cockpit_fill_intensity_cd` 0,8, offset [−15, 0, 12]. Bez stínů, pod střechou
  canopy. Posouvají se s okem (`cockpit_eye` ve snímcích).
  - 12 / 5 cd = plošně šedá deska; bez světel černá (slunce dovnitř nesvítí). Většinu světla dávají displeje.
- Ladění: pole snímku `cockpit_light` [key, fill], `display_light`, `interior_tint`; v kódu
  `ASpaceshipPawn::DebugSetCockpitLighting(Key, Fill, Display, InteriorTint)`. Preset `cockpit_light`.
- Interiér kokpitu `base_color_tint` 0,6 (tmavý jako v SC). Hodnoty trupu (`space.ShipMat`) interiér nedědí.
- **Expozice:** kokpitová kamera má vlastní `ASpaceshipPawn::CockpitExposureBias` = **−0,7 EV** (ve skoku
  quantum se prolíná na `QuantumExposureBias` −0,8 a expozice se připíchne). Cíl proti SC: střední jas
  kokpitu nad planetou ~0,10–0,19, ve vesmíru ~0,05 (tmavý kokpit, jasné displeje).
  - Displeje jsou emisivní a s expozicí tmavnou → `MI_Ship_<Loď>_Screens.emissive_strength`
    **2,9 = 1,8 × 2^0,7**. Změníš-li bias, přepočítej emissive stejně (jinak tmavé / kvetoucí písmo;
    efektivní jas nad ~3 = bílé písmo kvete a rozmazává se).
  - Sklo displejů (`ESpaceHudSymbol::MfdGlass`) tmavé, obsah jasný.
  - Za běhu: `space.Post AutoExposureBias <EV>` (preset `cockpit_look`: 0 / −0,5 / −1 / −1,5),
    vlastnost lodi `space.Ship CockpitExposureBias <EV>` (neukládá se; co sedí, zapiš do kódu/setupu).

## Testy a snímky

Testy vždy **nástrojem PowerShell** (bash rozbije `$PSScriptRoot`), commandlet nic nekreslí:

```powershell
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_displays.py   # slot, RT, velikost, světla, stav, písmo >= 26
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_frame.py      # oko, deska pod horizontem, vzdálenost
.\Tools\run_editor_python.ps1 Tools\Tests\test_flight_hud_sc1c.py    # strom HUD, make_state/apply_state, space.Hud
```

Vzhled jen v **zabalené** hře (uncooked `-game` kreslí nové materiály šedě, 9.2 e):

```powershell
.\Tools\Shots.ps1 -Preset cockpit -Package      # zabalí (~5 min) a vyfotí
.\Tools\Shots.ps1 -Preset mfd_pages             # levý MFD ~495–710 × 640–825, pravý ~893–1105 × 640–825 px
.\Tools\Shots.ps1 -Preset cockpit_look -Width 1920 -Height 1080   # expozice; autor hraje 1080p
```

Presety: `cockpit` (oko, displeje, rám), `cockpit_light`, `cockpit_centre`, `cockpit_look`,
`mfd_pages`, `hud` (HUD ve všech situacích), `display_sharpness` (displeje za rychlého letu).
Pole snímku pro kokpit: `cockpit_eye`, `hide_hull`, `hide_canopy`, `cockpit_light`, `display_light`,
`interior_tint`, `hud`, `console` (např. `["space.MfdPage 1 2"]`).
Výřezy si zvětši a slož do jednoho listu (PIL ve scratchpadu) proti referenci z `Docs/UI/`.

Měření: `stat SpaceCockpit` (stav a kreslení displejů), `stat SpaceHud` (prvky, „Line batches“), `stat unit`
(zkontroluj RenderRes – ostrost bez 100 % rozlišení nehodnoť, 9.2 i). A/B přepínače
`space.CockpitKeepWindow 0/1`, `space.HudLineBatch 0/1`. Profilování přes Unreal Insights bez GUI:
WORKFLOW 9.2, odstavec „Profilování zabalené hry“.

Další konzole: `space.CockpitPitch <°>` (sklon pohledu, setup `cockpit_view_pitch_deg` 0),
`space.CameraShake <násobitel>`, `space.CockpitCentre 0/1`.

## Nástrahy (příznak → příčina → řešení)

- **Kokpit a displeje se za rychlého letu rozmazávají a „trhají“** → Nanite dává meshi letícímu s kamerou
  špatné motion vectory, TSR míchá z nesprávného místa → interiér bez Nanite (`no_nanite_parts` v setupu,
  hlídá `test_import_ship_plan.py`), kokpitová kamera `MotionBlurAmount 0`. Ověření `display_sharpness`.
- **Duchy čísel (dvě desítky přes sebe)** → TSR prolíná číslo měněné každý snímek → opaque + pixel
  animation, stav 5 Hz, kvantování během změny. Nepomohlo: translucent + responsive AA (zdvojené řádky),
  průhlednost po TSR (rozmazané), TSR cvary, mipmapy RT. Zbývá krátce při afterburneru / tvrdém brzdění.
- **Blikání displejů a hitch při boostu** → RT se přestavoval kvůli FOV kicku → měřítko jen ze šířky okna,
  práh 0,099.
- **Po přidání kreslených prvků spadne kokpit z ~64 na ~31 FPS, herní vlákno +6–17 ms, GPU beze změny** →
  Slate `AddLineElements`: každá změna tloušťky/vrstvy = nová dávka, a nové okno při každém kreslení =
  realokace pole → trvalé okno + jedna tloušťka/vrstva + fronta čar (9.2 g).
- **HUD v balíčku v Roboto** → špatná cesta stage fontů → `Path="UI/Fonts"` (9.3 a).
- **Kokpit šedý / vybledlý** → příliš silná key/fill světla (12 cd) nebo expozice → světla ze setupu, bias −0,7.
- **Displeje vybledlé od oblohy** → lit sklo odráželo denní oblohu → obrazovky unlit.
- **Materiál zůstal translucent po reimportu** → `_fresh_material` znovu použije asset se starými
  vlastnostmi → blend mode vždy nastav explicitně (9.2 d).
- **F1/F2 přepne wireframe/unlit místo stránky** (Development build) → enginové debug bindy → odebrat v
  `DefaultInput.ini` (už je).
- **Konzole v poli `console` platí do konce běhu** → A/B zdědí nastavení → každý snímek začni návratem na
  výchozí hodnoty, první snímek zahoď; FPS hodnoť se `settle` ≥ 2 s (9.2 h).
- **Kolize jmen v unity buildu** (`ModeColor` v HUDu vs `SpaceDebugHUD.cpp`) → konstanty v souborech
  pojmenovávej jedinečně.

## Pravidla

- Na displeje ani HUD nic nepředstírat: jen data, která hra opravdu má.
- AI malované ciferníky nejdou přečíst – obsah obrazovek vždy kreslit (živě v RT, nebo skriptem).
- Po vizuální opravě přidej do testu kontrolu, která by chybu zachytila.
- Hotovo = test zelený + snímek zabalené hry zkontrolovaný proti referenci.
