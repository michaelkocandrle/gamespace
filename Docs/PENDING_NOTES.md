# Dočasné poznatky (čekají na novou strukturu dokumentace)

Druhá session (větev `audit-v1-followup`) přestavuje CLAUDE.md, skilly, HANDOFF a WORKFLOW. Do té doby se nové
poznatky a nástrahy píšou sem. Po sloučení se přenesou do nové struktury podle její hierarchie a tento soubor
zmizí.

## Nástrahy (formát příznak → příčina → řešení)

- **Reflection captures v interiéru nic nedělají, obraz s nimi i bez nich je shodný** (30. 9. 2026).
  Příčina: hra používá Lumen GI a UE 5.8 pak skládá lesk jen z Lumenova hrubého odrazu a SSR
  (`DiffuseIndirectComposite.usf`, `bLumenReflectionInputIsSSR`). Průchod s capture a oblohou
  (`RenderDeferredReflectionsAndSkyLighting`) pohled s Lumen GI přeskočí. Řešení: capture nepoužívat, dokud
  interiér běží s Lumen GI. Kov bez odrazů Lumenu zůstává kompromis (metallic ~0,5, drsnost ≥ 0,36).
  Recenze: `Docs/Reviews/2026-09-30_interior_reflections.md`.
- **Runtime reflection capture se v zabalené hře nikdy nedokončí** (30. 9. 2026, platí jen bez Lumen GI).
  Příčina: `UGameEngine::Tick` volá aktualizaci capture jen ve snímcích, kdy je v enginové frontě nějaká
  capture (`HasReflectionCapturesToUpdate`). Runtime capture přitom kreslí jednu stěnu krychle za snímek
  (`r.ReflectionCapture.Runtime.Timeslice 1`) a před ní stínový snímek, a `RefreshCapture()` jen nastaví
  příznak. Řešení: po dobu ~8 snímků na capture volat každý snímek `MarkDirtyForRecaptureOrUpload()` na
  některou z capture („pumpa“). Rychlé vykreslení (`bFastRender`) funguje jen s `r.ReflectionCapture.Runtime.Budget > 0`.
- **Odraz capture a oblohy na drsném povrchu je nulový** (30. 9. 2026, bez statického světla a bez Lumen GI).
  Příčina: „lightmap mixing“ násobí odraz poměrem `IndirectIrradiance / AverageBrightness`
  (`ComputeMixingWeight`) a bez lightmap je `IndirectIrradiance` nula; od drsnosti 0,3 to platí naplno.
  Řešení: `r.ReflectionEnvironmentLightmapMixing 0`.
- **`ShowFlag.ReflectionOverride 1` se ve snímkovači neprojeví** (`Shots.ps1 -Editor`, 30. 9. 2026), obraz
  zůstane normálně osvětlený. Řešení: pro diagnostiku odrazů dočasně nastavit materiál na kov, třeba
  `space.Kit PaintMetallic 0.9 _Structure` a `space.Kit PrimaryRoughness 0.3 _Structure`.
- **Snímky A/B se liší hlavně na hranách** (30. 9. 2026). Příčina: loď ve výšce (`altitude_m`) se mezi
  snímky nepatrně posune a s ní i `camera_local`. Řešení: porovnávat očima nebo po výřezech, ne průměrným
  rozdílem pixelů.

- **Malý díl kitu stojí nečekaně mnoho trojúhelníků** (30. 9. 2026). Příčiny:
  - 4×4 cm difuzor `Kit_Glow*` stojí 108 trojúhelníků, protože `_bezel` dává tmavý rámeček na obě velké
    strany (8 boxů);
  - box s bevelem a 2 segmenty stojí 108 trojúhelníků, s 1 segmentem 44;
  - zaslepené konce trubek a kabelů, které pokračují do dalšího modulu.

  Řešení:
  - `bezel_face=-1/1` u difuzoru, jehož druhá strana leží na dílu;
  - `segments=1` u bevelů ≤ 3 mm (z očí jsou to ~2 px);
  - `caps=False` u průběžných vedení;
  - šrouby jako šestihran.

  Rozpad trojúhelníků po voláních: obalit `kit_geo.Part.box/slab/tube` a účtovat přírůstek volajícímu
  (pozor, `slab` volá `box`, takže vnořené řádky se počítají dvakrát).

- **Geometrický test hlásí u decalu na kit podlaze „box reaches the wall's other side“** (30. 9. 2026).
  Příčiny:
  - protiskluzové pruhy jsou zapuštěné 1 mm do desky, takže paprsek ze středu decalu narazí na jejich spodní
    stěnu;
  - kit deska je silná jen 2 cm, takže box decalu hluboký 3 cm dosáhne na její spodní stranu.

  Řešení:
  - `mirrored_projected` ignoruje odvrácené plochy do 8 mm za povrchem;
  - decal na podlaze dostane `"max_depth_cm": 1.5`.
- **Kit podlaha v místnosti s obložením trupu (průřez L)** jde jen 1 cm pod líc obložení, ne 10 cm jako u stěn W.
  Obložení má ve výklenku soklu vlastní práh a u přepážky kokpitu Wayfareru je trup jen 4,5 cm za lícem.
  Místnost přestane držet lodní podlahu odebráním `"floor"` z `kit_modules.keep`. Mezeru mezi přepážkou a prvním
  modulem zakryje `stand_in_floor`.

- **Po přestavbě lodi se ve hře nic nezměnilo, stará geometrie zůstala** (30. 9. 2026). Kajuta měla novou kit
  podlahu i starou lodní a obě blikaly přes sebe v zubatých skvrnách; výdejník měl před sebou starou krabici.
  Příčina: `hs_assemble_ship.py` zapíše `<Loď>_HS_Game.blend`, ale FBX v `ArtSource/Ships/<Loď>/Export/` nepřepíše,
  a `import_ship.py` tak importuje FBX z minulého exportu. Řešení: po assemble vždy
  `blender -b <Loď>_HS_Game.blend --python ../../../Tools/Blender/gamespace_ship_export.py -- --out "//Export"`
  (z `ArtSource/Ships/<Loď>`) a teprve potom `import_ship.py`. Kontrola: čas FBX v `Export/`.
- **Nábytek u obložení trupu narazí do žeber na zkosení** (30. 9. 2026). Obnažená žebra obložení na každém spoji
  modulů stojí 8 cm od panelů i nahoru po zkosení. Pod zkosením je proto volno jen po čáru o `FRAME_OUT / 0,6` níž
  než rovina zkosení; 0,1 m od líce je to 1,68 m, ne 1,83 m. Geometrický test lodi to nevidí (díly kitu spojí do
  jednoho meshe); `Tools/Kit/kit_clash.py -- <Loď> [prefix]` postaví díly kitu jako samostatné objekty a vypíše
  dvojice, které se protínají (dno na podlaze a konzole v obložení jsou záměrné). Totéž pro kabelový žlab na
  zkosení (0,27–0,34 m od líce, od 1,99 m) a nosníky stropních rozvodů (od 2,09 m).
- **Polštář opřený o lisovaný panel „plave“** (geometrický test, 30. 9. 2026). Střed lisovaného panelu je 6 mm
  zapuštěný a zaoblené hrany polštáře mezeru zvětší nad toleranci 6 mm. Řešení: polštář 7 mm do panelu.

## Nástroje

- `space.Kit <Parametr> <hodnota> <část jména>` s filtrem jména mění i materiály dílů lodí, tedy kit místností,
  které `kit_rooms.py` staví do blueprintu lodi. Příklad: `space.Kit PaintMetallic 0.9 _Structure` (30. 9. 2026).
  Bez filtru zůstává jen u herců interiéru a ukázky kitu.
- Preset `wayfarer_reflection_options.json` porovná dnešní odrazy, kov 0,9 bez odrazů a kov s odrazy Lumenu
  do drsnosti 0,32. Časy jsou v řádcích `SHOTS perf` v logu.
