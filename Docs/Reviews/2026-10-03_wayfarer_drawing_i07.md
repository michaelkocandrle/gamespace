# Wayfarer – výkres interiéru I-07 (plán decalů a nápisů), 3. 10. 2026

List `ArtSource/Ships/Wayfarer/Design/Drawings/Wayfarer_I07_decals.png` (vektorově `Saved/Drawings/`), kreslí `Tools/Design/draw_interior_plans.py`, test
`Tools/Tests/test_interior_drawing.py`. Styl I-04 (schválen 1. 10.), jeden zdroj dat; list podle schváleného vzoru = jedno
kolo kritika.

## Kolo kritika (Opus, `"gate": "step"`; brief a zpráva v `2026-10-03_wayfarer_drawing_i07/`)

| Kolo | Verdikt | Skóre (čitelnost / úplnost / data / konvence / stavebnost / srozumitelnost) | Průměr |
|---|---|---|---|
| 1 | FAIL | 6 / 5 / 6 / 6 / 5 / 6 | 5,7 |

Po kole opraveny všechny body „musí“; další kolo až po schválení autorem (finální recenze).

## Reakce na výtky
Decaly D-I v bodě dopadu paprsku (ne v počátku), druhy knihovny česky, tabulka pravidel rozsevu, rozlišení promítaného nápisu a decalu dílu. Nevyřešeno: asi 40 štítků ovladačů kokpitu klade stavba kokpitu (hs_cockpit, hs_interior_decals) mimo data interiéru – na listu jako otevřený bod; do dat interiéru je převede hlavní session (hs_* tato session nemění).

## Otázky pro autora
Převést štítky ovladačů kokpitu do dat interiéru (hlavní session). Dál „Kontrola dat“ na listu (body „[čeká na autora]“ a „[k opravě]“; oprava layoutu mění otisky E-01–E-08, tedy
hlavní session).
