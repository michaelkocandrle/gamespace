# Brief: technický výkres interiéru I-08 – Wayfarer, plán světel a výkon

Hodnotíš **technický výkres**, ne herní vzhled. List I-08 patří do sady výkresů interiéru lodi Wayfarer (dossier lodi,
bod 4). Styl sady autor schválil na vzorovém listu kajuty I-04 (1:20 na A0): rámeček, razítko, legenda, odkazové čáry
s ID, stavy prvků (postaveno černě, návrh modře s +). Výkres kreslí skript z týchž dat, ze kterých se loď staví; půdorys
je z postavené geometrie (díly kitu, interiér a trup lodi). Toto je dílčí kolo (ne finální předání).

## Co má list obsahovat

1. Všechna světla interiéru lodi na svém místě v půdorysu celé paluby (1:20): typ, barva, stín, „jen pěšky“.
2. Souhrn po místnostech: počet, za letu, jen při chůzi, se stínem, podlaha, hustota proti pravidlu kitu, součet cd.
3. Druhy světel: socket kitu nebo světlo lodi, počet, typ, barva, rozsah cd, stín, místnosti, účel.
4. Poznámka k výkonu (RTX 2060, 1080p) a ke kontrole světel v zabalené hře.
5. Srozumitelnost pro autora, který není herní vývojář.

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i08_r1\`: `00_celkovy_pohled.png`, `01_pudorys_zad.png`, `02_pudorys_pric.png`, `03_tabulky.png`, `04_legenda_poznamky.png`, `05_razitko.png` (00 = celý list zmenšený, ostatní výřezy 200 dpi).
Celý list: `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I08_lights.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – `interior` (kit_modules, kit.fittings, decals, lights)
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – místnosti, objekty, dveře
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_interior_design.json` – ID, účely, dveře, komponenty, decaly
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Wayfarer_setup.json` – promítané nápisy D-INT-*
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Export\Wayfarer_lights.json` – světla lodi; `C:\gamespace\gamespace-audit\ArtSource\Kit\Export\kit_manifest.json`
  – díly kitu, sockety světel, decaly dílů
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I08_lights.json` – ID nakreslená, popsaná a v tabulkách
Udělej namátkovou kontrolu aspoň deseti prvků.

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost. 2. Úplnost proti zadání (body výše). 3. Soulad s daty. 4. Konvence technického výkresu. 5. Stavebnost
a ověřitelnost (dá se podle listu stavba ověřit?). 6. Srozumitelnost pro autora.

Práh PASS (dílčí krok, `"gate": "step"`): průměr aspoň 6,5, žádná kategorie pod 6, žádná výtka „musí se opravit".

## Formát odpovědi (česky, Markdown)

```
# Verdikt: PASS | FAIL
První dojem: <jedna věta>
| Kategorie | Skóre | Proč |
...
Průměr: <x,x>
## Musí se opravit
1. <výřez, oblast> – <co> – <jak to má být>
## Mělo by se opravit
## Drobnosti
## Namátková kontrola dat (prvek, výkres, data, sedí/nesedí)
```
Buď konkrétní: každá výtka říká, na kterém výřezu a kde přesně.
