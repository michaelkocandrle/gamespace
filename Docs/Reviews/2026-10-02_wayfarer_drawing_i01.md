# Wayfarer – výkres interiéru I-01 (hlavní paluba), 2.–3. 10. 2026

List `ArtSource/Ships/Wayfarer/Design/Drawings/Wayfarer_I01_deck.png` (vektorově `Saved/Drawings/`), kreslí `Tools/Design/draw_interior_deck.py`, test
`Tools/Tests/test_interior_drawing.py`. Styl I-04 (schválen 1. 10.), jeden zdroj dat.

## Kola kritika (Opus, `"gate": "step"`; briefy a zprávy v `2026-10-02_wayfarer_drawing_i01/`)

| Kolo | Verdikt | Skóre (čitelnost / úplnost / data / konvence / stavebnost / srozumitelnost) | Průměr |
|---|---|---|---|
| 1 | FAIL | 6 / 6 / 6 / 6 / 5 / 5 | 5,7 |
| 2 | FAIL (2 body „musí“) | 7 / 7 / 7 / 7 / 6 / 7 | 6,8 |

| 3 | FAIL (1 bod „musí“) | 7 / 7 / 6 / 7 / 7 / 7 | 6,8 |

Kolo 3 (3. 10., po sloučení main) bylo poslední povolené. Bod „musí“ (komponenty pod podlahou proti trupu: spodní hrana AVIONICS z −0,20 mimo trup, chybějící QFUEL, návrhy v2) je opraven: kontrola trupu paprskem dolů (kanopa nemá střechu), obě komponenty v kontrole, návrhy v2 modře na listu. Finální kolo až po schválení autorem.

## Reakce na výtky
Kolo 1: schodiště do kokpitu, rozpor účelu kokpitu (0,35 m v layoutu proti +1,15), světlá výška kokpitu z geometrie, komponenty TEC postavené ve výklencích kitu, díly kitu pod ID. Kolo 2: světlá výška měřená nad celou pochozí plochou (2,05 pod žebrem kabiny, WORKFLOW 9 fm), díly pod ID stropů a přepážek, tabulka dílů s ID a nábytkem, stropy z geometrie, řezová čára, zlomové čáry. Kolo 3: kontrola komponent proti trupu (hlavní smyčka trupu + paprsek), návrhy v2 QFUEL a AVIONICS, světla kokpitu z nastavení lodi (L-SET, přibyla 3. 10. s I-08) v počtech místností. Podrobný seznam reakcí po bodech je v briefech dalších kol.

## Otázky pro autora
Viz „Kontrola dat“ na listu (body „[čeká na autora]“ a „[k opravě]“: layout podle kitu – mění otisky E-01–E-08, tedy
hlavní session).
