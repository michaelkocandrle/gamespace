# Kokpit – detail 2: vrstvení decalů, opotřebení, křeslo, světlo – 7. 10. 2026

Navazuje na `2026-10-07_cockpit_consoles.md` (PASS 6,5). Autor 7. 10.: „přidávej detaily, vrstvy decalů, nauč se
vrstvení decalů a textur přes sebe“. Postup podle rozboru etalonu `Docs/Kit/etalon/decal_stack.md`; know-how ve skillu
`ship-interior` (Kokpit a sklo – vrstvení decalů). Práh `step`.

## Co se změnilo

- **Nástroje vrstvení v generátoru kokpitu:** `hs_cockpit.stencil(...)` klade libovolnou položku knihovny decalů
  (pravotočivý rámec), `hs_cockpit.grime(..., wear=)` karty špíny přes `Placer.card_at`; interiérové decaly mají nový
  slot **`DecalWear`** (světlé ošoupání – stejný master jako špína, tint 8 / 8,8 / 10, drsnost × 0,35).
- **Stack konzolí:** tón těla 0,082 (dřív 0,05), kryty 0,2; nýty pod hranou, řada slotů, zásuvka a štítek, servisní
  kryt se zapuštěnými šrouby a šablonou SERVICE, číslo panelu, výstražný trojúhelník, `st_torque`, tón-v-tónu šrafy;
  opotřebení: tmavé lemy a šmouhy + světlé ošoupání u ovladačů, pod předloktím, u paty čel, na loketních opěrkách.
  Nápisy na hlavách konzolí čtené z křesla (C22 se dřív četl obráceně).
- **Křeslo:** popruhy z teple šedé tkaniny s vazbou (`int_webbing`), zřetelná perforace (dlaždice 4 cm), centrální
  otočný zámek se 4 jazýčky a vroubkováním, bederní pásy, ovládací destičky na loketních opěrkách, páky sklonu
  s oranžovou koncovkou, boční kovový rám s odlehčovacími otvory a šrouby.
- **HOTAS:** tlačítka s límcem místo svítících teček, spoušť s lučíkem, opěrka dlaně (knipl), posuvník (plyn).
- **Světlo (systémová příčina stagnace):** kokpitové světlo teple neutrální 1,0 / 0,93 / 0,84 (setup
  `pawn.cockpit_light_color`, dřív studené 0,85 / 0,92 / 1), záře displejů 12 → 7 cd, lišta na čele konzolí 0,55.
  `import_ship` nově nastaví barvu (`*_color`) jako LinearColor.

## Kola kritika

| Kolo | Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Styl | Průměr | Verdikt |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 7 | 6 | 5 | 6 | 6 | 7 | 7 | 6 | 6,25 | FAIL |
| 2 | 6 | 6 | 5 | 6 | 6 | 7 | 7 | 6 | 6,1 | FAIL |
| 3 | 6 | 6 | 5 | 7 | 6 | 7 | 7 | 6 | 6,25 | FAIL |
| ověř. | 6 | 7 | 6 | 7 | 6 | 7 | 7 | 7 | 6,6 | **PASS** |

Kolo 1 „musí“: špína neviditelná → zjištěno, že tmavá špína na tmavém grafitu nemá kontrast; zavedena světlá vrstva
`DecalWear`. HOTAS placeholdery → tlačítka s límcem, spoušť, opěrka. Zámek postroje → byl mimo záběr; záběr sedáku
rozšířen, zámek dopracován. Kolo 2 „musí“: opotřebení, materiály bez variace, křeslo (perforace, popruhy, opěrky),
rám křesla → vše výše. Kolo 3 „musí“: materiály křesla a čitelnost opotřebení → teplé světlo, tóny krytů, tint wear.
Ověřovací kolo: bod 2 splněn, bod 1 částečně (bez „musí“).

Neopraveno / další krok (doporučení ověřovacího kola): popruhy ještě teplejší a světlejší proti rámu, perforace
čitelná z 1–2 m, zbytek modrého nádechu na křesle, silueta křesla (zúžená hlavová opěrka, boční vedení), špína ve
spárách (AO / křivost), popisky na destičkách opěrek, slabší azurová záře rámečků MFD. Zaoblení hran těl konzolí.

Finální snímky ze zabalené hry: `shots:20261007_112723_cockpit_audit`, `shots:20261007_112830_mfd_pages`.
