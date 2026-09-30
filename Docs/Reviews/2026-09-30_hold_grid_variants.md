# Mřížka v nákladovém prostoru: varianty k rozhodnutí (30. 9. 2026)

Zadání autora: vysvětlit varianty mřížky se snímky a co na nich závisí (podlaha, rampa, prahy); rozhodne autor.

List `2026-09-30_hold_grid_variants/grid_variants.jpg` obsahuje řádky A, B, C a v každém tři pohledy:
shora (vše nad 2 m odříznuto), z technické chodby dveřmi a z uličky ke dveřím.

- Jde o hliněný render z herního blendu lodi i s díly kitu.
- Na mřížce stojí 8 kontejnerů po 1 SCU (1,25 m).
- Zelená plocha je volná podlaha před dveřmi do technické chodby, žlutě je obrys poklopu kvantového pohonu.
- Render dělá `Tools/Design/hold_grid_variants.py`.

## Problém

Dveře do technické chodby jsou na y 0–1,0 m. Blíž k levoboku jít nemůžou, protože za nimi stojí reaktor
(posunuté 28. 9.). Mřížka dnes končí 0,3 m před přepážkou. Z dveří se tak vystupuje přímo proti rohu kontejneru
a do uličky vede jen 0,35 m šířky dveří.

## Varianty

| | Mřížka (x od zádě) | Volno před dveřmi | Od rampy k mřížce | Přes poklop kvantového pohonu |
|---|---|---|---|---|
| **A** dnes | 2,9–7,9 | 0,30 m | 1,90 m | 0 |
| **B** o 0,25 m dozadu | 2,65–7,65 | 0,55 m | 1,65 m | 0 (2 cm od okraje) |
| **C** o 0,55 m dozadu | 2,35–7,35 | 0,85 m | 1,35 m | 0,28 m: první řada kontejnerů stojí na poklopu |

**Doporučení: B.** Před dveřmi je víc než půl metru volné podlahy. Kontejner přitažený paprskem od rampy má
pořád 1,65 m na položení a otočení. Poklop k pohonu zůstává volný.

Varianta C by uvolnila nejvíc místa. K pohonu by se ale šlo jen po vyložení první řady a mezi rampou a mřížkou
by zbylo jen 10 cm víc, než je hrana kontejneru.

Návrh z 28. 9. (mřížka i o 0,15 m k pravoboku, ulička 0,5–2,05 m) už neplatí. Od té doby přibyla žebra obložení
(8 cm do místnosti) a L-track s D-oky (~10 cm). Kontejner by s hranou na y −2,0 do nich narazil. Dnešní hrana
−1,85 je správná, jde tedy posouvat jen podélně.

## Co na poloze mřížky závisí

- **Podlaha:**
  - Mřížku (kolejnice a 15 úchytů) staví loď sama z obdélníku v `Wayfarer_layout.json`
    (`hs_interior.obj_cargo_grid`); stačí změnit `rect` a přestavět loď.
  - Desky podlahy (rastr 0,6 m) a poklop nádrže paliva v uličce se nemění.
  - Poklop kvantového pohonu (x 1,4–2,6) určuje, jak daleko dozadu mřížka smí, pokud má zůstat přístupný.
- **Rampa:**
  - Mezi horní hranou rampy (x 1,0) a mřížkou je místo na položení kontejneru z paprsku, to je sloupec
    „od rampy k mřížce“.
  - Hydraulika rampy (x 1,05–1,6 u pravoboku) a držák paprsku (u levoboku) zůstávají, mřížka k nim nedosáhne
    v žádné variantě.
- **Prahy:**
  - Práh dveří do technické chodby (přepážka x 8,2) se nemění, mění se jen volná plocha před ním.
  - Práh rampy (x 1,0) se nemění.
- **Nápisy:**
  - Šablona `GRID` na obložení pravoboku (`Int_Grid`, x 7,8) se posune s koncem mřížky.
  - Pruh uličky na podlaze (`Int_Lane`) zůstává.
- **Kit:** obložení s L-trackem (moduly C po 1,2 m) ani strop se nemění.

Po rozhodnutí posunu mřížku v layoutu a šablonu, přestavím loď a projdu geometrický test a snímky nákladového
prostoru.

## Rozhodnutí (autor 30. 9. 2026): varianta B – provedeno

- `Wayfarer_layout.json`: mřížka `rect` x 2,65–7,65 (dřív 2,9–7,9); šablona `Int_Grid` v setupu o 0,25 m dozadu
  (x 7,55).
- Loď přestavěná (`hs_build_ship`, `hs_assemble_ship`, export, `import_ship`), geometrický test PASS (včetně
  `walk_blocked`), `test_ship_import` PASS.
- Ve hře: `2026-09-30_hold_grid_variants/grid_B_in_game.jpg` (vlevo A, vpravo B; zabalená hra, preset
  `wayfarer_rooms`, snímek 09).
