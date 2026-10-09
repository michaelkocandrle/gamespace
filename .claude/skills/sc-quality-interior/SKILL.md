---
name: sc-quality-interior
description: How the Wayfarer cockpit reached the author's "good enough" SC level (9. 10. 2026) and how to repeat it fast on any interior, room, console or ship part - the method (author's screenshot -> AI-edited concept -> choice -> build to it, compare from the concept's angle), the shape language (lofted forms through stations, satin panel paint, graphite fields, light lines, lit recesses), the detail layers (panel trim v2 with per-panel tone, logical mesh decals, services on the lining, interior scatter), the light plan, the MFD v5 style, the walk map, the pipeline commands and every trap met on the way. Load before building or improving any interior surface, console, seat, wall, floor or cockpit part to SC quality, or when the author says "plastic", "uniform", "boxes", "not detailed", "no purpose", "cannot walk".
---

# Úroveň SC v interiéru: jak jsme ji dosáhli v kokpitu Wayfareru

Autor 9. 10. 2026 kokpit prohlásil za „good enough“. Tento skill popisuje **postup**, který funguje, a **chyby**,
které stály nejvíc času. Další místnosti a lodě se dělají stejně. Historie je v commitech 8.–9. 10. 2026 a v
recenzích `Docs/Reviews/2026-10-08_cockpit_v3_r1..r3`, `2026-10-09_cockpit_v4_r4`.

## 1. Co nefungovalo (neopakovat)

- **Iterace po malých krocích s kritikem** (r1–r4 skóre 5,4 → 6,0): přidávání drobností na krabice nezvedne dojem.
  Kritik i autor hodnotí **celek**: tvar, vrstvy, světlo. Viz paměť `critic-systemic-not-local`.
- **Krabice z `p.box` s malým zkosením** = „plastic vibe“. Velké hmoty musí být tvarované (loft) a mít texturu panelů.
- **Jednolitý bílý lak** bez variace = nevěrohodné. Variace se dělá v textuře (tón po panelech), ne v geometrii.
- **Prvky bez účelu** (tmavé obdélníky, svítící pruhy „jen tak“) autor okamžitě odhalí. Každý prvek musí mít funkci:
  mřížka sání vzduchu, rozvodná krabice, madlo, servisní poklop, číslo panelu u panelu.
- **Náhodný rozptyl decalů** působí nelogicky (čísla panelů na podlaze se opakovala). Decaly klást podle logiky.
- **Výklad pochvaly**: „ten materiál je skvělý“ ≠ „ten prvek dej všude“ (paměť `clarify-praise-before-replicating`).

## 2. Postup, který funguje (pořadí kroků)

1. **Koncept z autorova screenshotu.** Screenshot hry → Scenario `model_openai-gpt-image-2-5-sunburst`
   (`referenceImages`: upload přes `upload_asset` + curl PUT, 2 varianty, `quality: high`). Prompt: co zachovat
   (kamera, okolí) a co **přesně** přepracovat (tvar, ovládání, světla, materiál). Varianty uložit do
   `ArtSource/Ships/<Loď>/Concept/...`, autor vybere přes `AskUserQuestion` s doporučením.
   - Pro 2D UI (MFD) místo AI: **PIL maketa ve skutečném rozlišení s herními fonty** (`Tools/Design/mfd_layout_mock.py`).
2. **Stavba podle konceptu** (kap. 3–6).
3. **Srovnání ze stejného úhlu**: v presetu snímků je záběr z úhlu konceptu (`Tools/Shots/cockpit_v3.json`
   `concept_view`), skládat koncept nad hru do jednoho listu (PIL) a dorovnávat rozdíly, dokud nesedí.
4. **Průchodnost** změřit (`cockpit_walk_map.py`, kap. 8), ne odhadovat.
5. **Kritik** jedno kolo s párem „koncept vs. hra“ (`visual-review`), výtky brát jako seznam, pak předat autorovi.

## 3. Tvarový jazyk (díly kitu, `Tools/Kit/kit_cockpit_v3.py`)

- **Loft přes stanice** místo krabic. `STATIONS = [(x, hloubka od obložení, výška vnitřní horní hrany), ...]`,
  `_section(x)` vrací průřez (zapuštěný sokl 5 cm, zkosení, čelo, zkosení 25 mm, šikmá horní plocha 11° k uličce),
  `_skin(p, role, rings, centres)` potáhne prstence a **otočí každou plochu od středu** (centroid test; ruční
  pořadí vrcholů vyšlo obráceně → tmavý render). Hloubka nikdy nepřekročí průchod (ulička ≥ 0,53 m).
- **Napojení do sousedního tvaru** (konzole → křídlo desky): poslední stanice stoupá k hornímu okraji křídla.
- **Ploché pole na šikmé ploše**: `top_pt(x, s)` / `top_frame(x, s)` (bod a rám na povrchu), `_top_patch(...)`
  (deska sledující povrch, šířka může být funkce x), `_face_patch(...)` na čele. Ovládání klást do rámů z povrchu.
- **Materiály dílů**: `Kit_PanelPaint` (lesklý lak s trimem, velké plochy), `Kit_PanelSatin` (stejný lak saténový –
  svislé plochy v zrcadlovém laku odrážely tmavý kokpit a četly šedě), `Kit_Inset` (grafitová pole),
  `Kit_Lip` (saténové rámy a lemy), `Kit_GlowStrip` / `Kit_GlowFoot` / `Kit_GlowWindow` (linky, skrytá LED,
  prosvícené difuzory). Role v `kit_geo.ROLES` a `ArtSource/Kit/kit_materials.json` (+ `limits`).
- **Konstrukce s logikou**: vzpěra = sloupek 60×35 mm pod lakovaným krytem + noha do příruby se 4 šrouby (ne
  „háky“ z trubek); skořepina kolem opěradla změřená z modelu křesla (`seat_profile3.py` ve scratchpadu:
  x a poloviční šířka po výškách).

## 4. Vrstvy detailu (to, co dělá „SC level“)

1. **Textura panelů v2** (`Tools/Kit/kit_panel_detail.py`, 0,8 m dlaždice, normal + cavity):
   rekurzivní dělení na ~40 panelů 8 druhů (zapuštěný, žaluzie, perforace, poklop se šrouby, štítek s vyrytými
   „řádky textu“, dvojitý stupeň, nýty, hladký), spáry, šrouby v rozích, řady spojovacích prvků, vlasové linky.
   **Tón po panelech zapečený do cavity** (lak ±5 %, 14 % šedý sekundární lak, 6 % grafit): master násobí base
   color cavity mapou (`DetailCavityMap`, `DetailCavityStrength`) → variace na všech plochách bez kódu.
   Měřítko podle dílu: stěny `detail_tile_cm` 120 / síla 0,6, konzole 60 / 0,6, cavity 0,7.
2. **Mesh decaly z knihovny** (`ArtSource/Ships/Shared/Decals/decal_library_index.json`; strukturní = jen normál+AO,
   info = barva) na dílech kitu přes `kit_batch2.label(p, item, at, normal, xdir, ydir, scale)`:
   - **Logicky**: číslo panelu u každého otvoru vlevo nahoře, `st_vent` u mřížky, řada šroubů na spoji rámů.
   - Výplň jen drobné strukturní kusy (`DRESS_FILL`: nýty, spáry, šrouby, štěrbiny, zásuvky, servisní světla).
   - **Stejný kus ne blíž než 30 cm** (výkresy I-07 slévají kopie bližší 25 cm → test výkresů padá).
   - **Každý nový kus potřebuje český účel** v `<Loď>_interior_design.json` (`"pn_2": ...` slovník), jinak
     `test_interior_drawing` FAIL.
3. **Rozvody na obložení** (`hs_interior.py`, blok `services`): ray-cast na skutečný povrch obložení (BVH z `lb`),
   dvě chráničky na sponách u každého žebra, rozvodná krabice se šroubovaným víkem, vlnitá ohebná chránička
   do konzole (odkud konzole bere proud), kulová tryska vzduchu s potrubím u hlavy pilota. Účel je vidět.
4. **Rozptyl decalů interiéru** (`interior.decals.scatter` v `<Loď>_hs.json`): stěny a deska hustě
   (step 0,15–0,16, prob 0,85–0,95); podlaha jen rohové značky, nýty, šrouby, pár nápisů (prob 0,45). Nové
   pravidlo = nové ID `D-I-R-SCATTER-nn` v návrhových datech. JSON upravovat **řádkově** (přepis `json.dump`
   rozbije formát celého souboru → obří diff).

## 5. Světlo

- Linky místo plošného jasu: světelné linky na žebrech, v rámu skla, po vnitřní hraně konzole (bez přerušení do
  desky), skrytá LED pod převisem soklu, prosvícené mřížky. Plošný „wash“ ztlumit (`frame_wash_cd` 1,5).
- Svislá čela ve stínu: bodová světla nad uličkou mířená na čela (`console_face_cd` 90).
- Expozice kokpitu a emise displejů: skill `cockpit-displays` (při změně biasu přepočítat emisi).

## 6. MFD v5 (skill `cockpit-displays` má detaily)

Bílé písmo Saira (žádné zúžené), azurové čáry, jantar jen pro příznaky; rychlost a G v kruzích jako radar
(`USpaceHudGauge.bRing`), tenké čárové ukazatele (`bThin`), záložky podtržené, tabulky bez rámečků a vlajek.
Holo pole za obrazem (`M_Ship_HoloField`, průsvitné, ne aditivní = mléčné) a paprsek projektoru.

## 7. Pipeline a příkazy (PowerShell)

```powershell
$bl = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
# díly kitu kokpitu: VŽDY všechny najednou (jinak assemble hlásí „kit parts not in blend“)
.\Tools\HeavyLock.ps1 run -Task "kit" -Exec "& '$bl' -b --factory-startup --python-exit-code 1 --python Tools/Kit/kit_build.py -- factory --only SM_Kit_Cockpit_Console12W_A,SM_Kit_Cockpit_Console12W_B,SM_Kit_Cockpit_Console12W_BR,SM_Kit_Cockpit_SeatArm07W_L,SM_Kit_Cockpit_SeatArm07W_R,SM_Kit_Cockpit_ConsoleWall18W_L,SM_Kit_Cockpit_ConsoleWall18W_R,SM_Kit_Cockpit_SeatBack07W_A --no-render"
.\Tools\run_editor_python.ps1 Tools\Assets\import_kit.py
# loď: hs_build_ship -> hs_assemble_ship (GEOTEST) -> export (z ArtSource/Ships/<Loď>) -> import_ship (GAMESPACE_SHIP_MANIFEST)
# výkresy: draw_interior_deck, draw_interior_sheet --sheets I-02 I-03 I-04 I-05 I-06, draw_interior_plans,
#          draw_exterior_sheet, exterior_kit_layout --region ship; pak .\Tools\Test.ps1
.\Tools\Shots.ps1 -Preset cockpit_v3 -Editor          # srovnávací záběry (concept_view, konzole z uličky)
```

Celá přestavba trvá ~15 min: pouštět na pozadí (`run_in_background`) a čekat `until grep` smyčkou.

## 8. Kontroly

- **GEOTEST** (`check_ship_geometry.py`): floating (dílek musí něčeho dotýkat: LED pod převis, ne 2 cm pod něj),
  penetrating, holes (`Saved/GeoCheck/holes_*.png`), walk_blocked (hrany do výšky kroku 0,45 m nad chodidly
  jsou schody, ne překážky).
- **Mapa průchodnosti** (`Tools/Blender/cockpit_walk_map.py` na `<Loď>_HS_Game.blend`): kapsle hry po 3 cm,
  flood fill, ASCII mapa `o` dosažené / `.` odříznuté / `#` blokované. Tak se našlo, že obejití křesla blokoval
  konec schodiště (31 cm místo 50) → strmější lodní schody (5 × 0,23 m, stupnice 0,165), zábradlí končí na schodu.

## 9. Nástrahy (příznak → příčina → řešení)

- Plocha loftu tmavá / černá → obrácené pořadí vrcholů → `_skin` s centroid testem, nebo `[f[::-1] for f in faces]`.
- Svislá čela šedá a zrcadlí podlahu → zrcadlový lak (clear coat 1,0, rough 0,04) → saténová role + světla na čela.
- Snížení „ploutve“ desky (`outer_lift_scale` < 1) → škvíra do oblohy u parapetu (holes) → ponechat 1,0, plochu
  zapracovat vložkou a linkou.
- Prvek uvnitř jiného (světelný pás uvnitř tmavé vložky) → nevidět → odsazení o 2–3 mm před povrch.
- Stejné decaly blízko sebe → výkres I-07 je sloučí → test FAIL → rozestup 30 cm.
- Python v PowerShell `-c` s uvozovkami se rozpadne → úpravy souborů přes bash heredoc / skript ve scratchpadu.
- Počítač usne → běh na pozadí stojí; po probuzení pokračuje (zkontrolovat čas spuštění UE procesu).
