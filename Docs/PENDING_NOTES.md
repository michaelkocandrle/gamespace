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

## Nástroje

- `space.Kit <Parametr> <hodnota> <část jména>` s filtrem jména mění i materiály dílů lodí, tedy kit místností,
  které `kit_rooms.py` staví do blueprintu lodi. Příklad: `space.Kit PaintMetallic 0.9 _Structure` (30. 9. 2026).
  Bez filtru zůstává jen u herců interiéru a ukázky kitu.
- Preset `wayfarer_reflection_options.json` porovná dnešní odrazy, kov 0,9 bez odrazů a kov s odrazy Lumenu
  do drsnosti 0,32. Časy jsou v řádcích `SHOTS perf` v logu.
