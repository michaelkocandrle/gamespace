# Wayfarer kokpit: levné otevřené body (26. 9. 2026)

Zadání autora: zavřít levné otevřené body z recenze v2 (`2026-09-25_wayfarer_cockpit_v2.md`) bez kritika,
stačí snímky před a po. Listy: `2026-09-26_wayfarer_cockpit_cheap_fixes/` (vlevo před: zabalená hra
25. 9. večer, vpravo po: 26. 9. dopoledne).

| # | Bod | Co se změnilo | List |
|---|---|---|---|
| 1 | Zadní pohled bez sedadla před dveřmi | Kamera presetu (`cockpit_back_day`, `cockpit_back`) stojí vedle sedadla a dívá se dolů po schodech do dveří kabiny. Polohu jsem vybral z pěti kandidátů v Eevee náhledu. | `01_zadni_pohled.jpg` |
| 2 | Denní pohled pilota bez mlhy | `pilot_view_day` letí ve 300 m místo 3 km: terén v zorném poli je 2–5 km daleko, ne 15+ km v oparu. | `02_pohled_pilota_den.jpg` |
| 3 | Hologram z vlastního meshe vnějšího obalu | `hs_cockpit._envelope`: voxely (160 po délce lodi), zeď kolem ploch, flood fill zvenku, vnitřek plný, hranice = obálka. Vyhlazení Taubinem (30 kroků), decimace na 24k trojúhelníků. Materiál je jednostranný a má slabší skenovací linky (ScanDepth 0,12). Vnitřní plochy trupu, které prosvítaly, jsou pryč. | `03_hologram.jpg` |
| 4 | Loketní opěrky | Polstrované opěrky na grafitové skořepině se závěsem na boční rám (sklápí se při nástupu), 23 cm od konzolí. | `04_loketni_operky.jpg` |
| 5 | Popisky tří stavových LED | Popisek dostala každá LED: pody MAIN/BATT/FAULT a LINK/TRK/WARN, křídla TEMP/WARN a ARMED/HEAT/READY, konzole SEAL/PRESS/WARN (modul rozšířen na 18 cm). 13 nových štítků `ck_*`. | `05_popisky_led.jpg` |
| 6 | Odraz skla podle kamery | `MPC_ShipView.InsideView` nastavuje `ASpaceshipPawn::UpdateViewCollection`: 1, když je kamera hráče uvnitř interiéru lodi. Sklo má hodnoty zvenku (neprůhlednost 0,7, drsnost 0,03, specular 1) a zevnitř (0,15 / 0,06 / 0,5). Uvnitř je navíc vypnutý drahý ostrý odraz Lumenu (`FrontLayer`). Pilot sklo nově vidí (`hide_canopy_in_cockpit: false`), dosud bylo v kameře kokpitu skryté. | `06_sklo_zvenku.jpg`, `02_pohled_pilota_den.jpg` |

## Výkon skla

Sklo přes celý pohled pilota nejdřív stálo +3,1 ms GPU (57 FPS):
- ostrý odraz Lumenu na průsvitných plochách (`FrontLayer`) +1,9 ms;
- průsvitné osvětlení per-pixel všemi světly kabiny (Surface ForwardShading) +1,1 ms.

Po vypnutí `FrontLayer` uvnitř a přechodu na Surface TranslucencyVolume stojí +0,58 ms. Z toho průsvitnost
0,38 ms a průsvitné osvětlení 0,15 ms, v limitu 1 ms. `stat gpu` z oka pilota ve 3 km: 13,15 ms před,
13,73 ms po. Denní pohled pilota ve 300 m: 67 FPS.
