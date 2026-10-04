# Recenze: MFD CONFIGURATION a popisek najetí (krok 2b), 4. 10. 2026

Listy: `Docs/Reviews/2026-10-04_mfd_config/` (brief, 3 listy; listy s rámy z autorova záznamu SC zůstávají lokálně).
Práh `step`. Reference: autorův záznam SC 4.x (`sc_own_04` t00_08_06, t00_08_12). Snímky kola 1
`shots:20261004_181921_mfd_config`, kola 2 `shots:20261004_183400_mfd_config`, kola 3 `shots:20261004_183833_mfd_config`, balená hra `shots:20261004_184549_mfd_config`.

## Kolo 1 – FAIL, průměr 6,4

Skóre: silueta 7, hierarchie 6, materiály 7, decaly 7, světlo 7, čitelnost 5, geometrie 5, styl 7.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Přepínače nesedí na řádky | musí | řádek je jeden pevný box (značka, popisek, přepínač); zbytek je perspektiva natočeného panelu |
| 2 | Ladicí kroužky nad přepínači | musí | opraveno: kroužek jen u prvku pod kurzorem |
| 3 | Chybí linky mezi řádky | musí | opraveno (v kole 3 silnější) |
| 4 | VTOL na spodní liště | musí | opraveno v kole 3 (řádky 46 px) |
| 5 | OFF skoro není vidět | doporučeno | opraveno: jantarový obrys a text |
| 6 | Přepínač není posuvník | doporučeno | odloženo do holografických MFD |
| 7 | Popisek mimo displej s vodicí čarou | doporučeno | opraveno: bez čáry; holografický popisek (autor 4. 10.), vypínatelný v nastavení |
| 8 | Slabý nadpis FLIGHT | doporučeno | opraveno zčásti: plné písmo s linkou |

## Kolo 2 – FAIL, průměr 6,3

Skóre: silueta 7, hierarchie 6, materiály 6, decaly 6, světlo 6, čitelnost 6, geometrie 6, styl 7.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Přiřazení přepínačů k řádkům z pohledu pilota nejasné | musí | opraveno: podsvícený pruh u každého druhého řádku přes celou šířku, silnější linky |
| 2 | Popisek najetí přes nadpis stránky | musí | opraveno: popisek nad horním rámem displeje (`FSpaceHotspot::LabelWorldLocation`) |
| 3 | VTOL doléhá na lištu | musí | opraveno: řádky 52 → 46 px |
| 4 | Linky z pohledu pilota nevidět | doporučeno | opraveno: tloušťka 3 px |
| 5 | Přepínač není posuvník | doporučeno | odloženo do holografických MFD |
| 6 | Nadpis FLIGHT, najetí jen kroužkem | doporučeno | odloženo do holografických MFD |

## Kolo 3 – PASS, průměr 6,9

Skóre: silueta 7, hierarchie 6, materiály 7, decaly 7, světlo 7, čitelnost 7, geometrie 7, styl 7.

Doporučení (žádné „musí“) jdou do kroku H (holografické MFD, `2026-10-04_cockpit_gap_analysis.md`):

1. OFF se opticky čte ve výšce PRECISION MODE: přepínač blíž k popisku, nebo stejně vysoký jako pruh.
2. Najetí: podsvítit přepínač nebo celý řádek, kroužek vycentrovat.
3. FLIGHT jako záložka (FLIGHT / GUNNERY / HUD v SC).
4. ON slabší než OFF: ON jasně azurově.
5. Popisek najetí se dotýká hologramu lodi nad levým MFD.
