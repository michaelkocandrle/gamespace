# Zdroje zdarma dostupných assetů pro SC vzhled (průzkum 23. 9. 2026)

Autor: žádné placené balíky; kvalitní zdarma assety ano (licence ověřit **před** stažením), Meshy AI
a Scenario.com po jednotlivých dílech, ne „vygenerovat všechno najednou“. Povolené licence: CC0,
CC-BY (s uvedením autora v `Docs/Credits.md`), bezplatné licence pro komerční použití. Zakázané:
non-commercial, editorial, jen osobní použití, zákaz šíření ve hře.

## 1. PBR materiály (největší skok za nejmenší práci)

| Zdroj | Licence | Stažení | Materiály pro SC vzhled |
| --- | --- | --- | --- |
| [ambientCG](https://ambientcg.com) | CC0 1.0 (hry výslovně povolené) | API bez přihlášení: `https://ambientcg.com/api/v2/full_json?q=…&type=Material&include=downloadData`, 1K–8K | `PaintedMetal004/006/013/016` (lakované panely s opotřebením), `MetalPlates006/008/017B`, `MetalWalkway014`, `MetalWalkway010`, `Grate001/002` (rošty), `Leather033A`, `Leather037`, `Fabric061` (sedadla), `Rubber004`, `Metal032`, `Metal049A` |
| [Poly Haven](https://polyhaven.com) | CC0 | API bez klíče (`https://api.polyhaven.com`, poslat vlastní User-Agent), až 8K/16K; Blender MCP má `download_polyhaven_asset` | `blue_metal_plate`, `metal_plate`, `rusty_painted_metal`, `painted_metal_shutter`, `metal_grate_rusty`, `rusty_metal_grid`, `brown_leather`, `leather_white` |

## 2. Nápisy, šablony, panelové detaily (decaly)

- **Yughues – Free Decals Materials #01 Redux** ([OpenGameArt](https://opengameart.org/content/free-decals-01-sci-fi)),
  CC-BY 4.0/3.0 (uvést autora): sci-fi panely, mřížky, ventilátory, průduchy i s normálami.
- **Stencil Painted Decal Pack** ([itch.io](https://strideh.itch.io/stencil-painted-decal-pack)): nápisy,
  čísla, výstražné pruhy, šipky; komerčně s uvedením autora, **nesmí se dávat do AI** (Meshy/Scenario).
  Stahuje se s přihlášením na itch – stáhne autor.
- Vlastní nápisy a štítky: Scenario (texty v generovaných obrázcích jsou nespolehlivé, písmo dodat ručně).

## 3. Modely

- **Infiltrator Demo** (Epic, [Fab](https://www.fab.com/listings/d813ecef-8346-4d8c-9484-169da72a80aa)) –
  zdarma, licence „jen pro projekty v Unreal Engine“ (to jsme). AAA industriální sci-fi interiér (637 meshů,
  900 textur), projekt z UE 4.9 – nutná migrace. Nejblíž SC ze všeho zdarma. Stahuje autor (účet Fab).
- **Fab – Limited-Time Free**: tři assety každé dva týdny, zůstanou navždy (Fab Standard License dovoluje
  hru s nimi šířit). Stojí za pravidelnou kontrolu.
- **Sketchfab** (CC-BY, stahování vyžaduje účet – stahuje autor): „A Sci-Fi Cockpit Concept“ (758k trojúhelníků,
  nejblíž vzhledem, těžký), „Sci-Fi Modular Asset Pack PBR“ (TVdot), „Sci-fi seat“ (Turtle_Flipper), dvě sci-fi
  chodby. U každého zkontrolovat odznak licence na stránce.
- **NASA 3D Resources** ([GitHub](https://github.com/nasa/NASA-3D-Resources)) – bez autorských práv (bez log NASA),
  díly ISS/Orion na detaily.
- Megascans už zdarma nejsou (jen do konce 2024).

## 4. AI

- **Meshy 7**: samostatné rekvizity (sedadlo, konzole, bedny, spojky potrubí), PBR mapy, ostřejší hrany než
  Meshy 6. Slabé na přesnost a symetrii („lehce roztavené“), nevyrobí modulární díly na mřížku – zdi,
  rámy a podlahy dělat v Blenderu. Na placeném plánu patří výstup autorovi.
- **Scenario**: bezešvé textury + mapy, **obsah hologramových obrazovek a HUD**, štítky a loga; PBR mapy
  odvozené z barvy – na realistický kov horší než ambientCG.

## Pořadí použití

1. ambientCG skriptem (~15 materiálů) → jeden master materiál (lak + opotřebení hran + špína) → přetexturovat kit.
2. Poly Haven jako detailní varianty a zdroj špíny.
3. Vrstva decalů (Yughues, šablony, vlastní štítky).
4. Infiltrator Demo – potrubí, kabely, lišty a průmyslové rekvizity místo nejslabších dílů kitu.
5. Meshy 7 na hlavní rekvizity (sedadlo, pulty) přebarvené materiály z bodu 1; Scenario na obsah obrazovek.
