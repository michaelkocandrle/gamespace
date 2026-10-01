# Wayfarer: levné opravy exteriéru, menší ploutve a koncepty povrchu (1. 10. 2026)

Zadání autora po výchozí recenzi (`2026-09-30_wayfarer_exterior.md`), bez kola kritika:

1. zrcadlené nápisy na pravoboku opravit a test decalů rozšířit i na decaly ze setupu;
2. šablonové nápisy výraznější a rozmístěné podle pravidel (u hardwaru, ne náhodně);
3. výchozí vzdálenost chase kamery;
4. denní světlo levelu: ostřejší stíny a odlesky na trupu, změřit výkon;
5. ploutve zmenšit jako změnu designu;
6. koncepty nového povrchu trupu (Higgsfield image-to-image), nic nestavět před výběrem.

Kamera ani světlo nesahají do `SpaceshipPawn` (kamera je v setupu lodi, světlo v `build_space_scene.py`).

## 1. Nápisy na pravoboku

- Nebyly zrcadlené, ale **otočené o 180°** (čtou se pozpátku a vzhůru nohama, což vypadá jako zrcadlo). Decaly ze
  setupu `Name_R`, `Reg_R`, `Logo_R` a `HazardExhaust_R` měly rotaci `[0, 90, -90]`; levobok má `[0, -90, 90]`.
  Oprava: roll +90 (`[0, 90, 90]`). Postižené byly čtyři decaly, ne dva.
- Test decalů ze setupu existoval (`test_decal_orientation.py`, pravidla 1 a 2: strana diváka a zrcadlení), otočení
  nehlídal. Nové **pravidlo 3**: text na stěně (osa X do 60° od vodorovné) musí mít „nahoru“ (−Y komponenty, s
  `flip_v` +Y) nahoru v prostoru lodi. Na stavu před opravou hlásí právě tyto čtyři decaly, všechny interiérové
  nápisy (autorem ověřené) procházejí. Test běží offline i v CI (93 kontrol).
- Doklad: [01_starboard_markings.jpg](2026-10-01_wayfarer_cheap_fixes/01_starboard_markings.jpg).

## 2. Šablonové nápisy u hardwaru

- Knihovna decalů: nová dávka 16 šablon `xst_*` (tmavý inkoust 0,07 pro bílý lak) a `xstl_*` (světlý 0,84 pro tmavý
  hřbet), písmo 3,4 cm místo 2 cm a šedé 0,42. Staré položky (`st_*`) používá kit interiéru, proto zůstaly.
  `decal_library.py pack`: `append` je název dávky a dávky se balí za sebou, takže nová dávka nemůže posunout UV
  hotových meshů. Ověřeno: 117 starých položek má stejné `uv`, trim beze změny.
- Recept `Wayfarer_hs.json`: z pravidel `coverage` (mřížka po celé ploše) a `clusters` zmizely všechny textové
  šablony; zůstaly jen značky bez textu. Nápisy mají pevná místa u hardwaru: výstraha u trysky, sání, servisní šachta
  gondoly, hlavní a příďový podvozek, rampa, hydraulika rampy, plnění QT paliva, zemnicí bod, externí napájení,
  přístupový panel, střešní poklop, rám kabiny. Průduchy dostávají „VENT - KEEP CLEAR“ přes
  `greeble_companions.vent_stencil` (tmavý na boku, světlý na hřbetu). NO STEP tmavý na křídle, světlý na hřbetu.
- Měřítko: nápisy 1,5×, NO STEP 2× (písmo 5 cm, NO STEP 14 cm).
- Doklady: [05_stencils_nose.jpg](2026-10-01_wayfarer_cheap_fixes/05_stencils_nose.jpg),
  [06_stencils_wing.jpg](2026-10-01_wayfarer_cheap_fixes/06_stencils_wing.jpg),
  [08_stencils_beside_hardware.jpg](2026-10-01_wayfarer_cheap_fixes/08_stencils_beside_hardware.jpg).
- Co zůstává: nápisy jsou čitelné zblízka, z chase kamery ne (u SC také ne). Pořád jsou to decaly na hladkém trupu;
  k hardwaru, který by opravdu vystupoval, patří až nový povrch trupu.

## 3. Chase kamera

- `Wayfarer_setup.json` `components.camera_boom`: délka ramene 1750 → **2800 cm** (1,3 × délka lodi), výška 420 →
  520 cm. Ploutve a gondoly byly 9 m od kamery a vyplnily celý okraj obrazu; teď je vidět celá loď na ~35–40 %
  šířky jako v SC. Kolečko myši dál zoomuje (`CameraZoom` × toto rameno).
- Doklady: [02_chase_camera_rear.jpg](2026-10-01_wayfarer_cheap_fixes/02_chase_camera_rear.jpg),
  [03_chase_camera_front_left.jpg](2026-10-01_wayfarer_cheap_fixes/03_chase_camera_front_left.jpg).

## 4. Denní světlo

- Varianty přes konzoli (`Tools/Shots/wayfarer_day_light.json`, směr slunce × strana lodi; síla slunce, obloha,
  úhel zdroje, kontaktní stíny; rozlišení stínových map).
- Zjištění: stíny slunce jsou ostré už dnes, protože scalability epic dává `r.Shadow.Virtual.ResolutionLodBiasDirectional
  -1.5` a úhel zdroje se na stínu křídla neprojeví. Plochý dojem má hlavně příčinu v tom, že výchozí pohledy
  (chase zezadu, levobok zepředu) vidí stranu odvrácenou od slunce, kterou svítí jen obloha. Osvětlený pravobok má
  kontrast jako SC. Zbytek dělá lak bez variace drsnosti, což patří k povrchu trupu, ne ke světlu.
- Nové hodnoty v `build_space_scene.py`: slunce 8 → **11 lx**, obloha 0,7 → **0,55**, úhel 0,5° → **0,25°**,
  kontaktní stíny 0,08 → **0,12 m**. Obloha níž nešla: podle poznámky ve skriptu je pod ~0,45 stinná strana lodi ve
  vesmíru černá.
- Účinek (výřezy trupu, stejný záběr): osvětlený bok p90 0,65 → 0,70, p50 0,52 → 0,57; stinný bok a kontrast skoro
  beze změny. Doklad: [07_day_light_ab.jpg](2026-10-01_wayfarer_cheap_fixes/07_day_light_ab.jpg).
- Výkon: zabalená hra, 1920 × 1080, preset `wayfarer_cheap_fixes` 3× (staré hodnoty přes konzoli proti novým v levelu),
  `perf_log.py`. GPU minima stejná (+0,01 až +0,11 ms), průměry +0,3 až +0,5 ms při rozptylu nového světla až 1,7 ms
  (jeden běh s výkyvem; starý 0,3–0,7 ms). Síla světla ani úhel zdroje nic nestojí; rozdíl je v šumu měření.

  | záběr | GPU staré (ms) | GPU nové (ms) |
  |---|---|---|
  | levobok 3/4 zepředu | 14,33 (min 14,06) | 14,60 (min 14,17) |
  | pravobok 3/4 zepředu | 14,36 (min 14,13) | 14,71 (min 14,15) |
  | křídlo | 14,84 (min 14,64) | 15,24 (min 14,66) |
  | chase zezadu | 12,33 (min 12,19) | 12,74 (min 12,26) |
  | chase zepředu zleva | 13,17 (min 13,06) | 13,65 (min 13,13) |

## 5. Ploutve (design v2.1)

- Výkres `Wayfarer_layout.json`: ploutev 2,0 → **1,3 m** vysoká (vršek v rovině hřbetu 3,3 m), základna 3,3 → 2,6 m,
  horní tětiva 0,8 m, sklon ven stejný. Výška lodi 5,6 → **4,9 m** (spec, `Wayfarer_Design.md` kap. 6).
- Recept: kolizní boxy ploutví, značka na špičce, pokrytí decaly a karta špíny na ploutvi posunuté na novou ploutev.
- Přestavba `hs_build_ship` + `hs_assemble_ship` (test geometrie PASS, bounds z 2,80 → 2,13 m), export, import.
- Doklad: [04_fins_rear.jpg](2026-10-01_wayfarer_cheap_fixes/04_fins_rear.jpg).

## 6. Koncepty povrchu trupu

- Vstup: dva čisté záběry ve hře (3/4 zepředu zleva, 3/4 zezadu zleva) v `ArtSource/Ships/Wayfarer/Concept/surface_v3/
  input_current.jpg`; model GPT Image 2.5, high, 2k; 4 × ~3 kredity. Zadání a čtyři směry v `prompt.txt`.
- A čistý aerospace, B vrstvený utilitární, C průmyslový tahoun, D robustní průzkumník; všechny drží siluetu, livrej
  a jméno, přidávají panely s tloušťkou, zapuštěné poklopy, materiálové zóny, RCS, obrysová světla, rám a písty
  rampy, držáky zbraní a trysky s prstenci. Pozor: AI přidala i věci mimo výkres (D antény a kupoli na hřbetu,
  A překlep „IF-0417“); stavba jde z výkresu, koncept je jen reference stylu.
- List vedle sebe: [09_surface_concepts.jpg](2026-10-01_wayfarer_cheap_fixes/09_surface_concepts.jpg). Čeká na výběr autora.

## Testy, balení, snímky

- `.\Tools\Test.ps1 -All`: offline 6/6 (147 kontrol, z toho 93 decalů), Blender 1/1 (test geometrie lodi), UE 22/22
  (1398 kontrol, `test_ship_import` 333). Po přestavbě i `hs_assemble_ship` GEOTEST PASS.
- Balení 1,4 min; finální snímky ze zabalené hry: `Saved/Shots/20261001_014523_wayfarer_exterior_review` (31) a 3×
  `wayfarer_cheap_fixes`. Všechny prohlédnuté; snímky před a po výše jsou z `-Editor` (shoda se zabalenou hrou).
- Zbývá z recenze 30. 9.: trysky, záď a rampa, podvozek, křídla, zbraně, materiály a světla lodi, tedy systémové body
  pro nový povrch trupu (koncept A–D). Kolo kritika se nedělalo (zadání autora: levné opravy bez kritika).
