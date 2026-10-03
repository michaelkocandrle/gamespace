# Wayfarer – výkres interiéru I-08 (plán světel), 3. 10. 2026

List `ArtSource/Ships/Wayfarer/Design/Drawings/Wayfarer_I08_lights.png` (vektorově `Saved/Drawings/`), kreslí `Tools/Design/draw_interior_plans.py`, test
`Tools/Tests/test_interior_drawing.py`. Styl I-04 (schválen 1. 10.), jeden zdroj dat; list podle schváleného vzoru = jedno
kolo kritika.

## Kolo kritika (Opus, `"gate": "step"`; brief a zpráva v `2026-10-03_wayfarer_drawing_i08/`)

| Kolo | Verdikt | Skóre (čitelnost / úplnost / data / konvence / stavebnost / srozumitelnost) | Průměr |
|---|---|---|---|
| 1 | FAIL | 6 / 4 / 5 / 6 / 5 / 6 | 5,3 |

Po kole opraveny všechny body „musí“; další kolo až po schválení autorem (finální recenze).

## Reakce na výtky
Značka „i“ v kroužku u každého světla jen pěšky („i2“ ve skupině), velký černý roh u světel se stínem, světla v jednom bodě (bodovka a svatozář) jako jeden symbol s kroužky a počtem „2×“; světla z nastavení lodi doplněna do modelu interiéru (L-SET-PILOT 2,5 cd u oka pilota, L-SET-DISP-* 12 cd × podíl plochy obrazovky = 12 / 12 / 2,4 / 2,1 cd, ze setupu, hlaviček C++ a socketů trupu) – hra má 147 světel; tabulka druhů rozdělená podle druhu, typu a barvy (Bay pás / bodové, L-INT bodovky, barvy lodi slovy, „i“ jako „3 ze 4“); poznámka k výkonu s cílem autora (RTX 2060 6 GB, 1080p, za letu do 20 ms), posledním měřením (28. 9.: 16,7 / 20,4 ms) a postupem ověření. Mělo by: odkazy kokpitu po světlech (rozsah L-FIX-13…38 obsahuje L-FIX-15 z kajuty), svazky odkazů v TEC.

## Otázky pro autora
Hustota světel kokpitu 3,9 /m² nad pravidlem 2–3 (z toho 5 L-SET); měření celé lodi s kitem chybí. Dál „Kontrola dat“ na listu (body „[čeká na autora]“ a „[k opravě]“; oprava layoutu mění otisky E-01–E-08, tedy
hlavní session).
