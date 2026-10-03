# Wayfarer – boky revize G, 3. 10. 2026

Zadání autora 3. 10.: revize G schválená s úpravami (pás K panel + poklop na ~60 % desek nepravidelně, 5 větracích
skříní na bocích, ne nad sebou), pak přestavba, snímky, kritik `step` na Opusu, jedno ověřovací kolo povolené.
Výřezy výkresu: `2026-10-03_wayfarer_sides_revG/01–05_*.png`.

## Co se postavilo (data `Wayfarer_exterior_design.json`, model `exterior_model.py`)
- Střední vrstva boků: přídavný panel a poklop na deskách L, U, N; pod kořenem křídla v nižší výšce (`fallback_v`);
  pás K na 8 ze 14 desek (`share` 0,6 podle hashe ID, `irregular`); 5 větracích skříní K04, K09, L12, U13, L14.
- Čísla panelů D-R-PANEL-NUMBERS i na K, L, U, N, 7 cm (dřív 3,4 cm na R a S); znaky `pn_K/U/N` v atlasu.
- Šablony: 4 shluky na boku (RCS přídě, náklad, kolem jména); panelové linky a pokrytí vynechávají jméno a registraci.
- Kit: přídavný panel 20 mm nad svou deskou (`XK-DOUBLER.rise`; na 40mm deskách vystupoval o 2 mm).
- Rozpočet: HSBUDGET 453 565 (revize F) → 459 471 (strop 700 k).

## Nálezy cestou
- **„HE-0417“**: madlo a značka z pravidla doprovodů u poklopu D-H-40 vedly přes písmeno F; D-H-40 posunutý pod
  registraci (x 16,35, z 0,38). Panelová linka ani pokrytí to nebyly (dvě přestavby to vyloučily).
- **Výkres kreslil velké nápisy v poloviční velikosti**: `size` v setupu je poloviční rozměr (UE `DecalSize`), model
  výkresu ho bral jako celý. Opraveno (`exterior_model`, setup decaly), výkresy E-01 až E-08 překreslené.
- Stavba spadla na chybějícím `pn_K` (WORKFLOW 9.6 fq, test výkresu teď hlídá znaky z rozvrhu kitu) a generátor
  atlasu na Pillow v Pythonu 3.13 Blenderu (9.6 fp, náhrada `_PngImage`).

## Kritik (Opus, práh `step`): kolo 1 FAIL 6,4, ověřovací kolo PASS 6,5

| Kolo | Průměr | Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Styl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6,4 | 7 | 6 | 6 | 5 | 7 | 6 | 7 | 7 |
| ověření | 6,5 | 7 | 6 | 6 | 6 | 7 | 6 | 7 | 7 |

Listy a výstupy `2026-10-03_wayfarer_sides_revG/round1/`, `round2/` (`critic.md`). Snímky: editor
`shots:20261003_224712_wayfarer_exterior_review/`, zabalená hra `shots:20261003_225734_wayfarer_exterior_review/`.
Testy: `Test.ps1 -All` UE 22/22, Blender 1/1, offline 13/13 (výkresy interiéru překreslené: otisk `Wayfarer_lights.json`
se změnil s pásky v kanálu L/U); balení OK.

Reakce na body kola 1:
1. Střední vrstva jako čáry (musí) – **opraveno částečně**: panely 20 mm nad deskou se zkosením 10 mm, zblízka mají
   tloušťku; ze střední vzdálenosti pořád tenké. Malé poklopy zůstávají decaly (pravidlo rozpočtu autora 1. 10.).
2. Čísla a shluky (musí) – čísla **opravena** (7 cm, čitelná); shluky 8–9 položek, kritik je pořád vidí jako řídké.
3. Věnce nýtů – neopraveno, rozestup šroubů je data kitu (rozhodnutí stylu).
4. Lak bez variace a špíny – neopraveno (atlas špíny pro kanály v Známých problémech).
5. Černá příď – rozsah tmavé špičky podle výkresu; neopraveno.
6. Světelný pásek ve dne jasný – neopraveno; v ověření kritik hodnotí, že přepálený není.
7. Bílý srpek na listu 8 – neověřeno (okraj výřezu ve vesmíru).

Doporučení ověřovacího kola (otevřené): rozdíl tónu nebo drsnosti panelů proti desce, ve shluku jedna nosná položka
25–40 cm a výstražný prvek u nákladu, variace laku a špína ve spárách, RCS přídě s kovovým lemem hrdel.

## Srovnání se Star Citizen (`06_chase_SC_vs_Wayfarer.png`)
`starcitizenreference/` nemá žádný záběr exteriéru lodi (jen interiéry; obrázky Ship Matrix se nestahují), proto
Aegis Avenger z chase kamery ze hry (`2026-10-01_wayfarer_kit_pilot/refs/sc_avenger_chase.jpg`). Wayfarer zabírá
širší část obrazu (je větší než Avenger), povrch lodi je srovnatelně členitý; největší rozdíl je prostředí – SC má
mraky, nasvícený terén a hloubku, náš level plochou oblohu a šedý terén.
