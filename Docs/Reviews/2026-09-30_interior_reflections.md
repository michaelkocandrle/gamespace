# Odrazy v interiéru: levná varianta (30. 9. 2026)

Zadání autora: než se odrazy odloží na konec, změřit levnou variantu. Reflection captures v místnostech
interiéru, případně s odrazy v prostoru obrazovky (SSR), místo odrazů Lumenu. Cíl: broušený kov, lak a guma
rozeznatelné z běžné vzdálenosti, výkon aspoň 60 FPS, srovnání před a po.

## Výsledek

**Reflection captures v našem nastavení nefungují a fungovat nemůžou.** Hra osvětluje nepřímé světlo Lumenem
(Lumen GI) a UE 5.8 pak skládá lesk jen z Lumenova hrubého odrazu (screen probes) a SSR. Průchod
s reflection captures a oblohou se pro takový pohled vůbec nespustí:

- `IndirectLightRendering.cpp`, `RenderDeferredReflectionsAndSkyLighting`: pohled s Lumen GI se přeskočí
  („Specular was already composited in FDiffuseIndirectCompositePS“);
- `DiffuseIndirectComposite.usf`: při `bLumenReflectionInputIsSSR` je výsledek `lerp(RoughReflections, SSR,
  SSR.a)` a capture v něm nejsou.

Ověřeno na snímcích:

- s capture a bez nich;
- s MegaLights zapnutými a vypnutými během snímání capture;
- s `r.ReflectionEnvironmentLightmapMixing 0` i bez něj.

Všechny varianty jsou shodné na úrovni šumu, výřezy jsou v `captures_2x2_hold.jpg` a `captures_mixing.jpg`.
Capture by pomohly jen tehdy, kdyby se v interiéru vypnulo Lumen GI. Tím by ale zmizelo odražené světlo, na
kterém stojí schválený vzhled interiéru, takže tuhle variantu nedoporučuju.

Cestou jsem našel dvě další překážky:

1. Zabalená hra zpracovává runtime capture jen ve snímcích, kdy je v enginové frontě nějaká capture.
   Jedna capture přitom potřebuje ~7 snímků (stínový snímek a pak stěny krychle po jedné). Bez „pumpy“
   v C++ se tak nikdy nedokončí.
2. Bez statického světla by „lightmap mixing“ i tak vynuloval odraz capture na povrchu s drsností ≥ 0,3.

Kód pro capture jsem proto vrátil. V repozitáři zůstalo jen rozšíření `space.Kit` na díly lodí (s filtrem
jména) a srovnávací preset `Tools/Shots/wayfarer_reflection_options.json`.

## Co s kovem tedy jde

Kov kitu (`Kit_Structure`) má dnes metallic 0,5 a drsnost 0,36. Je to kompromis: bez odrazů Lumenu kov ztrácí
difuzní světlo a tmavne (kola kritika 27.–29. 9.). Změřil jsem proto tři varianty:

| Varianta | Vzhled (`options_close.jpg`, `options_wide.jpg`) | GPU navíc proti dnešku |
|---|---|---|
| a) dnes: SSR + hrubý odraz Lumenu, kov 0,5 / 0,36 | rámy světle šedé, čitelné proti laku, ale spíš jako světlá barva než kov | 0 |
| b) kov 0,9 / 0,30 bez odrazů Lumenu | rámy ztmavnou do tmavě šedé, působí jako tmavý lak | +0,2–0,9 ms (šum) |
| c) kov 0,9 / 0,30 + odrazy Lumenu jen do drsnosti 0,32, ½ rozlišení | rámy odrážejí osvětlené panely a čtou se jako broušený kov | **+1,3 ms** (c proti b) |
| d) dnešní materiály + tytéž odrazy | skoro jako a | +2,0 ms |

Měřeno v rychlé smyčce (`Shots.ps1 -Editor`, 1920×1080), GPU ms, průměr druhé poloviny ustálení snímku:

| Záběr | a | b | c | d |
|---|---|---|---|---|
| kajuta zblízka | 13,47 | 13,64 | 15,44 | 15,71 |
| nákladový prostor zblízka | 13,80 | 13,96 | 15,31 | 15,60 |
| strojovna k zádi | 15,20 | 16,10 | 16,73 | 17,09 |
| nákladový prostor, celá stěna | 14,09 | 14,35 | 15,61 | 16,08 |

- Zabalená hra má dnes v kajutě a nákladovém prostoru ~59–63 FPS (16–17 ms na snímek).
- Varianta c by ji stáhla na ~55–58 FPS, takže cíl 60 FPS nesplní. Stejný závěr jako 27. 9.
  (`2026-09-27_interior_perf_profile.md`), jen teď s materiálem, který by odrazy opravdu využil.

## Doporučení

- Nechat dnešní stav (a): SSR, bez odrazů Lumenu, kov jako kompromis 0,5 / 0,36. Nic nestojí a lak, kov
  a guma se od sebe liší barvou a drsností.
- Variantu c (skutečný kov + odrazy Lumenu do 0,32) zapnout ve fázi optimalizace, pokud se jinde uvolní
  ~1,5 ms, například nižším rozlišením TSR nebo úsporou v MegaLights.
- Přepnutí je malé: `SetInteriorLighting` nechá `r.Lumen.Reflections.Allow 1` s `MaxRoughnessToTrace 0.32`
  a `DownsampleFactor 2` a `import_kit.py` nastaví `Kit_Structure` na 0,9 / 0,30.

## Poznámky ke snímkům

- Loď ve výšce 3 000 m se mezi snímky nepatrně posune, a tím i kamera (`camera_local`). Rozdíl dvou snímků
  proto dělají hlavně hrany. Porovnávat je potřeba očima nebo po výřezech, ne průměrným rozdílem pixelů.
- `ShowFlag.ReflectionOverride 1` se ve snímkovači (`-Editor`, `-game`) neprojevil a obraz zůstal normálně
  osvětlený. Pro diagnostiku odrazů je spolehlivější dočasně nastavit materiál na kov přes `space.Kit`.
