# Světla interiéru: hustota proti C2 a varianty výkonu (26. 9. 2026)

Zadání autora: porovnat hustotu světel s C2 na m² a na místnost, odvodit cílovou hustotu pro kit a změřit malá
světla bez stínů, MegaLights a emisivní povrchy přes Lumen. Cíl: hustota blízko C2 a cena nejvýš ~2 ms
v interiéru.

## 1. Hustota: C2 proti Wayfareru

Počty C2 jsou z outlineru v rozboru ([C2 8:04](https://www.youtube.com/watch?v=EOaiEeEjCGM&t=484)).
Plochy C2 jsou **odhad**, protože ve videu nejsou:
- nákladový prostor ~300 m² (696 SCU v 2–3 vrstvách plus uličky);
- můstek ~60 m² (šest stanovišť ve dvou řadách);
- horní paluba ~250 m².

| Prostor | Světel | Plocha | Na m² |
|---|---|---|---|
| C2 můstek | 74 | ~60 m² (odhad) | ~1,2 |
| C2 nákladový prostor | 160 | ~300 m² (odhad) | ~0,5 |
| C2 horní paluba (obytná) | 418 | ~250 m² (odhad) | ~1,7 |
| Wayfarer kokpit | 38 (13 + 25 u svítidel) | 13,4 m² | 2,8 |
| Wayfarer nákladový prostor | 48 (12 + 36) | 27,4 m² | 1,75 |
| Wayfarer technická chodba | 15 (3 + 12) | 8,4 m² | 1,8 |
| Wayfarer kajuta | 22 (7 + 15) | 18,2 m² | 1,2 |

Před světly u svítidel měl Wayfarer 0,4–1,0 světla na m². **Na m² je teď na úrovni C2 nebo nad ní.** Méně
světel na místnost je dáno jen tím, že naše místnosti jsou 4–10× menší. C2 působí hustěji ještě kvůli vysokým
prostorům a různým typům svítidel (prstence rámů, lišty podél podlahy, stropní pouzdra, kontrolky).

**Cílová hustota pro kit** (převzato do designového jazyka, `ship-interior`):
- **pravidlo:** každé svítidlo, lišta a linka má své světlo;
- obytné prostory a chodby 1,2–1,8 světla na m²;
- kokpit 2–3 na m² (desky, displeje, podsvícení nohou);
- velké nákladové prostory 0,5–1 na m²;
- kontrolky, LED a obruby tlačítek jsou jen emisivní, bez světla.

## 2. Varianty a jejich cena

Preset `Tools/Shots/light_variants.json`: ulička nákladového prostoru (chodba od rampy) a pohled pilota, 3 km,
den, 1080p, `stat gpu` (Queue Total, průměr). Konzolové příkazy `SpaceShipLightTuning.cpp`:
`space.FixLights`, `space.ShipLightShadows`, `space.ShipLightRadius`, `space.IntEmissive`; MegaLights přes
`r.MegaLights.EnableForProject` (engine ho čte každý snímek, hra ho přepne za běhu).

| Varianta | Chodba GPU | rozdíl | Kokpit GPU | rozdíl |
|---|---|---|---|---|
| a) jen světla místností (41) | 16,85 ms | – | 13,53 ms | – |
| b) + 88 světel u svítidel, bez stínů, dosah 1,6 m (současný stav) | 18,30 | **+1,45** | 14,74 | **+1,21** |
| c) b + stíny klasicky (virtual shadow maps) | 129,8 | +113 | 60,5 | +47 |
| d) b přes MegaLights, bez stínů | 18,32 | +1,47 | 14,87 | +1,34 |
| e) b přes MegaLights, **všechna světla se stíny (ray tracing)** | 19,00 | **+2,15** | 15,35 | **+1,82** |
| f) bez světel u svítidel, emise ×4 (světlo jen přes Lumen) | 16,69 | −0,16 | 13,73 | +0,20 |
| g) b s dvojnásobným dosahem (3,2 m) | 19,98 | +3,13 | 15,60 | +2,07 |

Dvojnásobná hustota (164 světel u svítidel, 205 celkem), stejná měření:

| Varianta | Chodba | Kokpit |
|---|---|---|
| b) bez stínů | +2,26 ms | +1,81 ms |
| e) MegaLights se stíny | +2,77 ms (min +2,0) | +2,0 ms (min +1,2) |

Samotný průchod MegaLights: chodba 2,43 → 2,65 ms, kokpit 1,92 → 2,04 ms. Klasická světla rostou lineárně
(`Lights` 2,26 → 2,94 ms).

## 3. Co z toho plyne

- **Klasické stíny pro desítky světel nejdou** (+47 až +113 ms).
- **Malá světla bez stínů** jsou nejlevnější do současné hustoty, cena ale roste s počtem i dosahem (dosah ×2 =
  +1,7 ms navíc). Stíny nemají, takže světlo prosvítá díly.
- **MegaLights** mají skoro pevnou cenu (průchod ~2 ms). Světla nahradí téměř zadarmo a stíny ze všech světel
  přidají jen ~0,6 ms. Nad ~2× současné hustoty vycházejí levněji než klasická světla. Omezení v UE 5.8:
  - funkce je označená jako **experimentální**;
  - potřebuje hardwarový ray tracing (RTX 2060 ho má, projekt má `r.RayTracing` zapnutý);
  - nepodporuje směrová světla (slunce zůstává klasicky);
  - kvalita stínů závisí na BVH, interiér bez Nanite je v pořádku;
  - stochastické vzorkování může v pohybu šumět. Snímky jsou statické, pohyb se musí ověřit ve hře.
  - V průměrech se objevily výkyvy (maxima až 20 ms), zřejmě při přepnutí za běhu. Trvale zapnuté by je mít
    nemělo, ověřit.
- **Emise přes Lumen** místnost prakticky nerozsvítí: tenké lišty jsou v povrchové cache Lumenu malé a světlo
  z nich je slabé a rozmazané. Stojí ~0,2 ms. Hodí se jen na kontrolky, LED a obruby, tam světlo není potřeba.

## 4. Návrh kombinace (ke schválení)

1. **Každé svítidlo a lišta dostane světlo** (dosah 1,5–2 m, specular 0,2) podle cílové hustoty výše.
2. **MegaLights zapnout, jen když je kamera uvnitř lodi** (stejný přepínač jako světla u svítidel), se stíny
   ray tracingem pro všechna světla interiéru. Odhad +1,8 až +2,2 ms při současné hustotě, do ~2,8 ms při
   dvojnásobné. Vzhled: stíny od žeber a konzolí, tmavší kouty, víc kontrastu (listy chodby a kokpitu).
3. **Záložní režim** (MegaLights vypnuté v nastavení grafiky nebo nepodporované): stejná světla bez stínů
   klasicky, +1,2 až +1,5 ms.
4. **Kontrolky, LED, obruby tlačítek a displeje jen emisivně**, bez skutečného světla.
5. **Rezerva na vyšší hustotu:** v interiéru stojí stíny slunce 3,1 ms (chodba) a odrazy Lumenu 2,6 ms, i když
   sem slunce svítí jen oknem. Omezení stínů slunce a kvality odrazů s kamerou uvnitř může uvolnit 1,5–3 ms.
   Změřím to v pilotu chodby z kitu, spolu s jemnou objemovou mlhou (MegaLights umí i objem).

Listy: `2026-09-26_interior_lighting_variants/` (vzhled a, b, e, f na chodbě a v kokpitu; výřezy `stat gpu`).
