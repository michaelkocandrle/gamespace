# Továrna dílů – soupis, poučení a mezery (návrh, 6. 10. 2026)

Jen analýza, nic se nestavělo. **Úroveň 1** = architektura (stěny, podlahy, stropy, rámy/portály, dveře, oblouky,
trubky, vzduchovody), **úroveň 2** = detailní předměty. Zdroje: `ArtSource/Kit/kit_parts.json`, `kit_rules.json`,
`ArtSource/Kit/Export/kit_manifest.json` (86 meshů), `Tools/Blender/hs_*.py`, recenze v `Docs/Reviews/`.
Skóre = průměr posledního kola kritika (práh `step` 6,5). Průřezy: N úzká 1,2 m, W široká 2,4 m, S průlez,
T vysoká, L38/L41 obložení trupu na šířku 3,8 / 4,1 m (kajuta / sklad Wayfareru).

## 1. Soupis dílů

**Kit** (`Tools/Kit/<skript>.py`, `build_part()`; umístění v lodi jen daty `interior.kit_modules` v `<Loď>_hs.json`
přes `kit_layout.py` → jiná loď bez změny kódu, pokud jí sedí průřez).

| ID (rodina) | Úr. | Kat. | Zdroj | Stav | Skóre / recenze | Jiná loď | Postavené varianty |
|---|---|---|---|---|---|---|---|
| Wall_Plain, _Grille, _Locker, _Pipes, _Hatch, _Display | 1 | stěna | `kit_walls.py` | schválený (autor 27. 9.) | FAIL 6,4 `kit_batch1_walls` | ano pro W; N jen Plain12N A/C | W 0,3/0,6/1,2 m × A–C (14 meshů) |
| Corner_Inner/Outer, Wall_Transition, _End, _Narrow | 1 | roh/uzel | `kit_batch2.py` | schválený 27. 9. | FAIL 5,5 `kit_batch2` (přechod W→N otevřený) | ano W; N jen End12N | 8 meshů |
| Portal_Ring | 1 | rám/portál | `kit_batch2.py` | schválený 27. 9. | FAIL 5,5 `kit_batch2` | ano W, N | 03W A–C, 03N A/B (S, T nepostavené) |
| Ceiling_Tray, Ceiling_Panel | 1 | strop | `kit_batch2.py`, L: `kit_batch4b.py` | schválený (W, N); L pilot | FAIL 5,5 `kit_batch2`; L: 6,0 `hold_liner` | W/N ano; L38/L41 částečně (šířka místnosti = nový záznam v `kit_rules` + přestavba) | 14 meshů |
| Floor_Plate, _Grille, _Hatch | 1 | podlaha | `kit_batch3.py`; L38 `kit_batch4b.py` | schválený 27. 9. | FAIL 5,5 `kit_batch3` | ano W, N; chybí 0,3 m W | 11 meshů |
| Stair_Flight, Stair_Ramp | 1 | schody/rampa | `kit_batch3.py` | schválený, nepoužitý | FAIL 5,5 `kit_batch3` | ne pro Wayfarer (výška 0,8 m vs. 1,15 m; rampa 2,9 m vs. 1,6 m / 22°) | Flight08N, Ramp29W |
| Bulkhead_Door | 1 | přepážka s otvorem | `kit_batch4b.py` | pilot (chodba, sklad, kajuta) | 5,4 `wayfarer_kit_corridor` (1 kolo) | částečně: L-varianty na míru místnostem Wayfareru | 03W A/B (mimo osu), 00W A, 00L41 C, 00L38 A/F |
| Wall_ComponentBay | 1/2 | výklenek komponenty | `kit_batch4.py` | pilot | FAIL 5,6 `kit_bays` | ano (W) | 12W A reaktor, 06W B chladič, 12W C štít |
| Wall_HullLiner | 1 | obložení trupu | `kit_liner.py` | pilot | FAIL 6,0 `hold_liner`; FAIL 6,5 `cabin_liner` (detail 5) | ano: L je bez šířky | 12L A/B/C/E/S, 06L A/C/D |
| Furniture_Bunk/Locker/Hygiene/Food | 2 | nábytek | `kit_furniture.py` `bunk()` … | pilot (kajuta) | FAIL 6,1 `cabin_furniture` (+ levné opravy) | ano, L-místnost | 21L, 10L, 15L, 16L, po 1 variantě |
| Mat_Master, Mat_Trim; Door_Sliding, Door_Frame, Bulkhead_Plain; batch 5, zbytek 6, 7, 8 | 1–2 | – | `kit_parts.json` | jen návrh (`planned`) | – | – | – |

**Jen ve Wayfareru** (Blender `Tools/Blender/hs_cockpit.py`, `hs_interior.py`, `hs_interior_kit.py`, `hs_canopy_frame.py`;
parametry v `Wayfarer_hs.json` `interior.cockpit`, `kit.fittings`; C++ najde ovladače jen podle socketů
`Display_*`, `Control_pwr`, `Control_eng`, `Control_door<n>*`, takže runtime přejde na jinou loď). Kokpit
celkem FAIL 6,17 `2026-10-06_cockpit_critic.md` (holo 6,0; layout 6,5; křeslo 6,5; konzole+klávesy+střed 5,5;
dveře+hasičák 6,5; soudržnost 6,0). * = ID navržené tímto soupisem.

| ID | Úr. | Kat. | Zdroj | Stav | Skóre | Jiná loď | Varianty |
|---|---|---|---|---|---|---|---|
| CK-HP-L/R holoprojektory MFD | 2 | displej | `hs_cockpit.holo_projector()` z `dash()` | jen Wayfarer | 6,0 (holo) | částečně: rozměry z JSON `holo_mfd`, poloha = pody Wayfareru | holo / sklo (`glass_panel()`), šířky, okraje |
| MFD-V3* obsah stránek | 2 | UI | C++ `USpaceCockpitDisplays`, `UCockpitDisplayComponent` | hotové 5. 10. | 6,0 | ano (slot `*_Screens`) | 7 stránek, klikací šipky, náběh, kouř |
| CK-HP-C středové displeje | 2 | displej | `hs_cockpit.dash()`/`pedestal()` | jen Wayfarer | 5,5 (malé, zrnité) | částečně (souřadnice v JSON) | – |
| CK-HOLO* hologram lodi | 2 | displej | `hs_cockpit.build_hologram()`, C++ `UShipPresentationComponent` | jen Wayfarer | v kokpitu | ano (z exteriéru libovolné lodi) | délka, svit, voxely |
| CK-CF vnitřní rám kanopy | 1 | rám | `hs_canopy_frame.build()` | jen Wayfarer | v kokpitu | ano (táhne se po hraně skla) | krytí, hloubka, zkosení, rozteč šroubů |
| CK-DS palubní deska | 1–2 | deska | `hs_cockpit.dash()`, `cowl()`, `build_wrap()` | jen Wayfarer | v kokpitu | částečně (souřadnice Wayfareru v JSON) | wrap / pods / plochá |
| CK-SC-L/R boční konzole | 2 | konzole | `hs_interior.obj_console()` | jen Wayfarer | 5,5 | částečně: pevné odsazení a popisky v kódu | – |
| CK-MOD* ovládací moduly (klávesy) | 2 | ovladač | `hs_cockpit.control_module()` | jen Wayfarer | 5,5 | ano (řádky (druh, popisek)) | 7 druhů: klávesa, kolébka, krytý spínač, otočný, enkodér, LED |
| CK-WP* křídlové panely | 2 | ovladač | `hs_cockpit.wing_panels()` | jen Wayfarer | 5,5 | částečně: sady tlačítek v kódu | – |
| CK-PWR*, CK-ENG* | 2 | ovladač | `hs_cockpit` + `SpaceshipPawn` | hotové | PWR PASS 6,9 `ship_power` | C++ ano, geometrie částečně | – |
| CK-HT HOTAS | 2 | ovladač | `hotas_stick()`, `hotas_throttle()` | jen Wayfarer | v kokpitu | ano funkce, umístění z odsazení konzole | – |
| CK-SEAT* pilotní křeslo v3 | 2 | sedadlo | `hs_cockpit.pilot_seat_v3()` | jen Wayfarer | 6,5 | ano (z obdélníku layoutu) | v1 box, Meshy GLB (Steadfast) |
| CK-CB* kabely pod deskou, pedály | 1 | rozvody | `hs_cockpit.underdash()` | jen Wayfarer | – | částečně (pevné kotvy) | – |
| CK-LT* světla kokpitu | – | světlo | `build_wrap()`, `cockpit_detail()` | jen Wayfarer | – | **ne** (souřadnice Wayfareru v kódu) | – |
| DOOR-SL* posuvné dveře | 1 | dveře | `hs_interior.build_door()`, C++ `UShipBoardingComponent` | hotové 5. 10. | **PASS 7,1** `2026-10-05_doors` | ano (z otvoru v layoutu) | 1 / 2 křídla, auto-zavření |
| DOOR-PNL* holo panel dveří | 2 | ovladač | C++ `USpaceDoorPanel` (widget), socket `Control_door<n>_panel` | hotové 5. 10. | 6,5 | ano | zavřeno/otevřeno, hover |
| FX-EXT* hasicí přístroj | 2 | výbava | `hs_interior_kit.extinguisher()` | jen Wayfarer | 6,5 | ano (JSON `fittings`) | – |
| staré zástupné bloky (lůžko, skříň, reaktor…) | 2 | – | `hs_interior.obj_*` | nahrazené kitem | – | ano, nízký detail | – |

Mimo rozsah: exteriérový kit trupu (desky, rám T, páteř; `2026-10-01_wayfarer_kit_pilot` PASS 6,6,
`2026-10-03_wayfarer_ship_kit` FAIL 6,0). **Žádný díl úrovně 1 ani 2 nemá PASS kritika kromě dveří a PWR.**

## 2. Poučení (seřazeno podle ztraceného času)

| # | Problém (recenze) | Pravidlo příště |
|---|---|---|
| 1 | Materiály 4–5 ve všech krocích, ladily se po dílech (`kit_material`, všechny kit_*, `cockpit_gap_analysis`) | Materiálový základ (trim, otěr z bake, drsnost) postav před koly na dílech; kategorie 2 kola ≤ 5 = stop lokálních oprav, systémový krok. |
| 2 | Kokpit ~10 dní bez 2D návrhu a knihovny tvarů (`cockpit*`, `cheap_fixes`, `detail_pass`) | Každý předmět mimo kit začíná 2D listem s měřenými cíli a sdílenými funkcemi (zkosení, vložený panel, šroub). |
| 3 | Holo MFD se ladilo obsahem, vada byla v geometrii (`holo_mfd`, `cockpit_critic`) | Dojem závislý na tvaru ověř nejdřív hrubou geometrií a jedním snímkem, pak obsah. |
| 4 | Světelný ping-pong, protichůdné výtky (`hold_liner`, `kit_batch3`, `cabin_liner`) | Světelný plán na typ místnosti; před kolem `measure_look.py`; výtku proti minulé nejdřív změř. |
| 5 | Špína tmavá na tmavém, 3 kola naslepo (`kit_grime`) | Před kolem na decal/efekt A/B snímek (vyp / černá / bílá). |
| 6 | Kritik hodnotil provizorní prvky ukázky (batch1–3, `kit_bays`) | Brief vyjmenuje provizorní a schválené prvky, výřezy jen na předmět kroku. |
| 7 | Rampa schválená, ale kinematicky nemožná (`ramp_plan`, odhad 6–8 dní) | Pohyblivý díl ve 2D v obou polohách: průchod postavy 1,8 m, dosednutí, kolize s trupem. |
| 8 | Chyby layoutu až při stavbě: dveře proti reaktoru, 8 SCU do W, zúžení u rampy (`wayfarer_kit_corridor`, `hold_grid_variants`) | Ve 2D 0,5 m volno za každými dveřmi a řez trupem v několika výškách po celé místnosti. |
| 9 | Díly kitu nepasovaly do lodi: 0,3 m podlaha, schody 1,15 m, rampa 22°, dveře mimo osu (`pilot_needs`) | Rozměrové řady kitu odvoď z výkresů cílových lodí dřív, než se dávka staví. |
| 10 | Kov ztmavil stěny, lekce se opakovala (`kit_batch1`, `hold_liner`) | Lak metallic ≤ 0,1, konstrukce ≤ 0,5; kontrast tónem a drsností; hodnoty jako test. |
| 11 | Kritik špatně četl prvky (L-track, žebra, páka plynu) (`hold_liner`, `kit_bays`, `cockpit_v2`) | Brief: poloha + detailní výřez ke každému klíčovému prvku; opakovanou neplatnou výtku jen odkázat. |
| 12 | Stíny světel kitu v lodi 10–42 ms (`wayfarer_kit_corridor`, `kit_bays`) | Novou sadu světel hned změřit v lodi (interiér i let, 3 běhy); světla kitu bez stínů jako výchozí. |
| 13 | Přechod W→N FAIL po všech kolech (`kit_batch2`) | Uzly navrhuj jako samostatný díl s těžkým rámem a shlukem výbavy, ne stěnu s dírou. |
| 14 | Čalounění jako vinyl, 3 kola (`cabin_furniture`) | Měkké plochy vždy `pad()` (výšková plocha, švy jako prohlubně), nikdy box s bevelem. |
| 15 | Výklenky komponent: detail schovaný, „cela“ (`kit_bays`) | Z výšky oka spočítej, co je vidět; funkční prvek na líc. |
| 16 | Obsah za mřížkou nečitelný 5 kol (`kit_batch3`, `kit_material`) | Obsah za mřížkou/sklem snímek z oka hned při stavbě; nejasnost autorovi po 1. kole. |
| 17 | Černé vodorovné plochy s `M_Ship_PBR` (`kit_batch3`, 9.6 dd) | Chyba nereagující na parametry: nejdřív test „stejná plocha, jiný master“. |
| 18 | Blender spadl tiše s kódem 0 (9.6 fg) | Vždy `--python-exit-code 1` a kontrola času `_HS_Game.blend` a FBX. |
| 19 | Přestavba se neprojevila ve hře, dvojí podlaha (9.6 eq) | Po `hs_assemble_ship` vždy export a kontrola času FBX. |
| 20 | Nedeterministická stavba přečíslovala světla a listy (9.6 cw, ff) | Každé pořadí ve stavbě řadit, otisky ze seřazených dat. |
| 21 | Useknuté texty displejů, 3 příčiny (`cockpit_v2`) | Výtka na čitelnost z oka = hned ray cast, nehádat. |
| 22 | Balení mezi koly kritika ~12 min/kolo, snímky ve střední kvalitě (`cockpit_v2`, `kit_material`) | Kola z `-Editor` s vynucenou kvalitou (kontrola v logu); balit jednou na konci. |
| 23 | Zrcadlené decaly, regrese (`kit_batch2`, `kit_bays`) | Každý nový nebo obnovený nápis test orientace + snímek. |
| 24 | Nová položka atlasu posunula UV starých; `--only` smazal díly z blendu (9.6 dt, ez, fj) | Atlas jen `append`; do commitu vždy celá dávka. |
| 25 | Změna sdíleného masteru tiše změnila Wayfarer (9.6 di) | Po změně masteru snímky před/po u všech lodí. |
| 26 | Tabule materiálů na izolovaných vzorcích snímaných kolmo v tmavé místnosti (autor ji 6. 10. neschválil: lak jako papír, lem bez odrazů, nic k porovnání se SC; `2026-10-06_kit_material_board`) | Materiály posuzuj jen v kontextu (zkušební úsek) a ze stejných úhlů a se stejným světlem jako kotevní záběry SC (workflow v0.2 kap. 3). |

Opakující se vzorec: **11 interiérových recenzí (kit 1–3, materiál, špína, výklenky, sklad, kajuta 2×, holo MFD,
kokpit) skončilo po 3 kolech FAIL s otevřenými body**; PASS jen dveře (2 kola), napájení a kolo 4 pilotu trupu. Příčina je systémová (materiál, světlo, 2D návrh předmětu), ne díl.

## 3. Mezery (žádný postavený díl)

**Úroveň 1:** průřezy **T** (vše) a **S** (kromě portálu); N jen zčásti (chybí Grille/Locker/Pipes/Hatch/Display,
rohy, Tray); podlaha 0,3 m; **zárubeň** (Door_Frame) a **posuvné dveře v kitu** (dnes jen `build_door()` lodi);
plná přepážka (Bulkhead_Plain); **oblouky** (ani v plánu); **trubky, kabely, vzduchovody** (Pipe/Cable/Duct_Run
jen plán); pouzdra svítidel (batch 8); žebřík, zábradlí, madla; poklop ve stropě; rám okna; rampa a schody
na míru lodi (parametrické); materiály Mat_Master/Mat_Trim jako díl.
**Úroveň 2:** konzole kitu (Console_Standing/Wall/Corner, Dash_Band, Glass_Panel), kokpitové předměty jako
sdílené díly (MFD, konzole, křeslo, HOTAS jsou funkce kódu Wayfareru, ne katalog); **centrální displej lodi**
mimo kokpit (stěnová/stolní obrazovka); **čtečka dlaně**; **stůl**, židle a lavice (Furniture_Seat); **kuchyňské
vybavení** (spotřebiče, nádobí; Furniture_Food je jeden blok); bedny (Furniture_Box); lékárnička; cedule;
skafandr jako samostatný předmět (dnes jen silueta ve skříňce); hasicí přístroj jako díl kitu.
