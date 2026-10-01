# Wayfarer – rozpočet trojúhelníků exteriéru (návrh ke schválení), 1. 10. 2026

**Zadání (autor 1. 10.):** pilot kitu pokrývá jen část lodi a trup už narazil na limit exportéru 1 M trojúhelníků.
Navrhnout rozpočet po částech lodi, drobný detail přesunout z geometrie do decalů a normálových map jako SC
(šrouby, malé poklopy, mřížky, panelové spáry); geometrie jen pro střední vrstvu (desky, rozvody, skříně, rám,
trysky). Spočítat úsporu, navrhnout pravidlo do skillu `ship-pipeline`. **Nic nepřestavovat do schválení.**

## Měření (postavený pilot, `Wayfarer_HS.blend`, jen v paměti, nic neuloženo)

Sloupce: dnes; zkosení 1 segment místo 2; bez zkosení; plochy zdroje sloučené v rovině (`dissolve_limit` 1°)
a zkosení 1 segment. Exteriér celkem 1 007 924 (export trupu 991 k + díly, které jdou do jiných meshů).

| Část | dnes | zkosení 1 seg. | bez zkosení | sloučení 1° + zkosení 1 seg. |
|---|---:|---:|---:|---:|
| plášť trupu (loft) | 210 937 | 161 063 | 117 099 | 27 228 |
| rám kitu (žebra, podélníky, páteř) | 189 212 | 111 792 | 53 204 | 41 940 |
| gondoly | 151 328 | 112 832 | 80 048 | 44 712 |
| křídla a ploutve | 68 600 | 56 136 | 44 748 | 13 694 |
| díly kitu (RCS, písty, rozvody, lampy) | 67 864 | 35 976 | 15 360 | 32 444 |
| pouzdra a pásy světel | 65 320 | 26 632 | 7 272 | 26 632 |
| desky ramen S | 49 216 | 34 344 | 21 424 | 4 076 |
| desky detailu (recept P-B) | 42 592 | 31 540 | 22 128 | 4 458 |
| šrouby kitu (1316 ks) | 36 848 | 36 848 | 36 848 | 36 848 |
| desky hřbetu R | 35 788 | 25 660 | 17 100 | 3 700 |
| funkční díly | 26 120 | 15 864 | 7 432 | 15 864 |
| panely, poklopy, skříně na R | 18 280 | 11 296 | 6 104 | 2 880 |
| podvozek (vlastní mesh) | 16 660 | 16 660 | 16 660 | 16 534 |
| záď z kitu (rám rampy, skříně) | 10 176 | 4 440 | 1 356 | 4 080 |
| ostatní (zbraně, greeble, zapuštění, sklo, západky) | 18 983 | 12 223 | 7 143 | 8 260 |
| **celkem** | **1 007 924** | **693 306** | **453 926** | **283 350** |

**Co z toho plyne:** šrouby nejsou hlavní problém (3,7 %). Trojúhelníky dělají **modifikátory na hustých plochách**:
desky a rám jsou kopie ploch trupu a loft trupu je jemně dělený i tam, kde je rovný (rám má v základu 16 tisíc
trojúhelníků, po solidify a zkosení ve 2 segmentech 176 tisíc, tj. 11×). Rovné oblasti se dají sloučit beze změny
tvaru; zakřivené plochy (gondoly, oblé rohy trupu) při 1° zůstávají.

## Návrh

### A. Geometrie jen pro střední a velkou vrstvu
- **Geometrie:** plášť, desky (jako vystouplé desky se zkosením), rám T, páteř, rozvody, skříně, bloky RCS, písty,
  pant, lampy, **trysky**, podvozek, zbraně.
- **Do decalů s normálou a AO (atlas, jako SC):** šrouby desek a rámu (řady `bolt_row_*`, nová položka „šroub
  rámu“ pro rozteč 250 mm), západky poklopů, **malé poklopy XK-HATCH** (dnes díra v desce + deska; decal `hatch`
  s normálou spáry a západkami), malé mřížky, panelové spáry na plochách, kde nejsou desky kitu (trim).
- **Panelové spáry trupu** (`seams` loftu) pod žebry kitu zrušit: žebro je zakrývá a `fill_grooves` je stejně
  zvedá (dnes geometrie, kterou nikdo nevidí).

### B. Stavba levněji beze změny vzhledu
1. **Sloučit rovné plochy** zdroje (`dissolve_limit` 1°, oddělit podle materiálu) u loftu trupu, desek a rámu
   před solidify a zkosením.
2. **Zkosení 1 segment** se „zpevněnými normálami“ (bevel `harden_normals` + weighted normals) místo 2 segmentů:
   hrana chytí světlo stejně, polovina trojúhelníků. Zaoblení ve 2 segmentech jen tam, kde je hrana z chase
   kamery vidět jako křivka (prstence gondol, ústí trysek).
3. Válce dílů podle velikosti: Ø pod 50 mm 8 stěn, do 150 mm 12, nad 16 (dnes 10–20 bez ohledu na velikost).

### C. Úspora (pilot, stejný rozsah)
| Krok | Exteriér | Úspora |
|---|---:|---:|
| dnes | 1 008 k | – |
| B1 + B2 (sloučení, zkosení 1 seg.) | 283 k | −72 % |
| + šrouby, západky, malé poklopy do decalů (A) | ~ 240 k | −76 % |

Decaly mají vlastní mesh bez Nanite (dnes 862 decalů); 1316 šroubů jako ~170 řad je zhruba +7 k trojúhelníků
v meshi decalů (čtverce na mřížce 6 cm).

### D. Rozpočet celé lodi (trup `SM_Ship_Wayfarer`, exportér: chyba nad 1 M)

Odhad celé lodi = pilot po krocích B a A, kit (desky, rám) na všech pásech K, L, U, S, R, zádi a břiše
(asi 2,5× rám a 4× desky pilotu) a nové trysky.

| Část | Rozpočet | Odhad po úpravě |
|---|---:|---:|
| plášť trupu (loft) | 50 k | 27 k |
| desky kitu (všechny pásy, záď, břicho, panely, skříně) | 80 k | ~ 45 k |
| rám kitu (žebra, podélníky, páteř) | 120 k | ~ 105 k |
| střední vrstva (rozvody, skříně, RCS, písty, pant, lampy) | 60 k | ~ 35 k |
| gondoly bez trysek | 60 k | 45 k |
| **trysky** (2 ×: kužel s hrdlem, středové těleso, žebra, táhla, prstence) | 80 k | – (nové) |
| křídla, ploutve, zbraně | 40 k | 16 k |
| světla (pouzdra, pásy) | 30 k | 27 k |
| funkční díly, desky detailu, zapuštění, greeble | 40 k | 30 k |
| **rezerva** (další krok kitu, antény, poškození) | 140 k | – |
| **celkem trup** | **700 k** | ~ 410 k + trysky |

Podvozek, kabina, interiér, decaly a hologram jsou vlastní meshe se svými stropy (interiér 404 k, podvozek 17 k).

### E. Pravidlo do skillu `ship-pipeline` (3b2b) – návrh
> **Rozpočet trojúhelníků trupu** (autor 1. 10. 2026, Wayfarer): trup ≤ 700 k (exportér: chyba nad 1 M,
> varování nad 700 k), rozpočet po částech v `<Loď>_hs.json` → `budget`; `hs_assemble_ship` vypíše
> skutečnost po částech (`HSBUDGET`) a test ji porovná s rozpočtem. **Geometrie jen pro velkou a střední vrstvu**
> (plášť, desky, rám, rozvody, skříně, RCS, hydraulika, trysky, podvozek, zbraně); **šrouby, západky, malé poklopy
> pod 0,4 m, mřížky pod 0,3 m a panelové spáry jsou decaly** s normálou a AO z atlasu. Plochy zkopírované z trupu
> se před solidify a zkosením slučují v rovině (1°); zkosení 1 segment se zpevněnými normálami, 2 segmenty jen
> u křivek viditelných z chase kamery; válce podle průměru 8 / 12 / 16 stěn. Spáry loftu pod rámem kitu se nestaví.

## Rizika
- Sloučené rovné plochy se triangulují na dlouhé tenké trojúhelníky; na Nanite a s plochým stínováním je to
  v pořádku, ale na oblých přechodech může vzniknout stínovací chyba. Ověření: snímky z editoru po přestavbě
  (bod 2) a srovnání s dnešní sadou `shots:20261001_211213_wayfarer_kit_pilot/`.
- Šrouby jako decal ztratí siluetu z ostrého úhlu (SC to tak má; z chase kamery nerozlišitelné). Kritik v kole 1
  chtěl šrouby výraznější – decal musí mít silnou normálu a AO.
- Malé poklopy jako decal: poklop už nebude díra s tmavou spárou do kanálu (méně „oken“, což pomůže i bodu 4).
