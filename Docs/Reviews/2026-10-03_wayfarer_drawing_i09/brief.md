# Brief: technický výkres interiéru I-09 – Wayfarer, rozpisy dveří, nábytku, komponent a objektů

Hodnotíš **technický výkres**, ne herní vzhled. List I-09 patří do sady výkresů interiéru lodi Wayfarer (dossier lodi,
bod 4). Styl sady autor schválil na vzorovém listu kajuty I-04 (1:20 na A0): rámeček, razítko, legenda, odkazové čáry
s ID, stavy prvků (postaveno černě, návrh modře s +). Výkres kreslí skript z týchž dat, ze kterých se loď staví; půdorys
je z postavené geometrie (díly kitu, interiér a trup lodi). Toto je dílčí kolo (ne finální předání).

## Co má list obsahovat

1. Rozpis všech dveří: ID, mezi místnostmi, šířka, provedení, stav křídla (postaveno / návrh / bez křídla), pohyb,
   ovládání (záměrně bez klávesnic), účel, list.
2. Rozpis nábytku: ID, díl kitu nebo stavba lodi, umístění, účel, list.
3. Rozpis komponent lodi: stav, kde jsou postavené, výklenek nebo místo, přístup, výměna, poznámky a návrhy.
4. Rozpis objektů a vybavení lodi (layout, vybavení interior.kit.fittings, madla).
5. Srozumitelnost pro autora, který není herní vývojář.

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i09_r1\`: `00_celkovy_pohled.png`, `01_dvere_nabytek.png`, `02_komponenty.png`, `03_objekty.png`, `04_razitko.png` (00 = celý list zmenšený, ostatní výřezy 200 dpi).
Celý list: `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I09_schedules.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – `interior` (kit_modules, kit.fittings, decals, lights)
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – místnosti, objekty, dveře
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_interior_design.json` – ID, účely, dveře, komponenty, decaly
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Wayfarer_setup.json` – promítané nápisy D-INT-*
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Export\Wayfarer_lights.json` – světla lodi; `C:\gamespace\gamespace-audit\ArtSource\Kit\Export\kit_manifest.json`
  – díly kitu, sockety světel, decaly dílů
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I09_schedules.json` – ID nakreslená, popsaná a v tabulkách
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
