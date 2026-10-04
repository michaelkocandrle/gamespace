# Recenze: napájení lodi a studený start (krok 2a podle autorova záznamu), 4. 10. 2026

Listy: `Docs/Reviews/2026-10-04_ship_power/` (brief, 4 listy; listy s rámy z autorova záznamu SC zůstávají lokálně).
Práh `step`. Reference: autorův záznam SC 4.x (`sc_own_04` t00_03_36, t00_02_33, t00_02_36; `sc_own_03` t00_05_48).
Snímky kola 1 `shots:20261004_171644_ship_power`, kola 2 `shots:20261004_172544_ship_power`, balená hra `shots:20261004_173417_ship_power`.

## Kolo 1 – FAIL, průměr 6,8

Skóre: silueta 7, hierarchie 7, materiály 6, decaly 6, světlo 6, čitelnost 7, geometrie 7, styl 8.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Vypnutá loď svítí pásy parapetu a modrým bodem | musí | opraveno: světla trupu (`_Light*`, `_PosWhite`), světla kitu (`_Glow*`) a skleněné linky na 3 %, hologram skrytý |
| 2 | Vypnuté MFD šedomodré, ne černé sklo | doporučeno | neopraveno: je to deska `IntScreenBack` za průhledným sklem; patří k materiálu obrazovek, viz kolo 2 |
| 3 | Popisek najetí v šedém rámečku | doporučeno | opraveno: azurový text 15 px, slabý podklad bez obrysu |
| 4 | NAPÁJENÍ chybí v režimu interakce | doporučeno | opraveno: první řádek i v režimu interakce |
| 5 | OK mimo řádek, slabé čekání | doporučeno | neplatné zčásti (perspektiva natočených panelů); čekání jantarové, hotové zelené OK |
| 6 | Prázdná spodní třetina náběhu | doporučeno | opraveno: řádek SHIP OS 2.4 pod lištou (běžící procenta duchovala pod TSR, proto pevný text) |
| 7 | Malé displeje nečitelné | doporučeno | opraveno: jen BOOT a lišta |
| 8 | LED panelů se nemění | doporučeno | neplatné: pohotovostní LED jako v desce Pisces |

## Kolo 2 – PASS, průměr 6,9

Skóre: silueta 7, hierarchie 7, materiály 6, decaly 7, světlo 7, čitelnost 7, geometrie 7, styl 7.

| # | Výtka | Závažnost | Reakce |
|---|---|---|---|
| 1 | Vypnuté MFD nejsou černé lesklé sklo | doporučeno | odloženo: ztmavit `IntScreenBack` podle napájení (parametr materiálu); s kokpitem z kitu |
| 2 | Drobná modrá skvrna u základny hologramu | doporučeno | odloženo: zdroj (materiál emitoru) nedohledán, není mezi zhasínanými materiály |
| 3 | Slabé čekající značky | doporučeno | opraveno bez kola: „WAIT“ jasně jantarově, stejná velikost jako OK |
| 4 | Pozadí náběhu modrošedé | doporučeno | odloženo s bodem 1 |
