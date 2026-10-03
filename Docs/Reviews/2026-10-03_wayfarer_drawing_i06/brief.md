# Brief: technický výkres interiéru I-06 – Wayfarer, průřezy s kapslí postavy

Hodnotíš **technický výkres**, ne herní vzhled. List I-06 patří do sady výkresů interiéru lodi Wayfarer (dossier lodi,
bod 4). Styl sady autor schválil na vzorovém listu kajuty I-04 (1:20 na A0): rámeček, razítko, legenda, kóty, odkazové
čáry s ID, stavy prvků (postaveno černě, návrh modře s +). Výkres kreslí skript z týchž dat, ze kterých se loď staví;
řezy jsou z postavené geometrie. Každý řez na tomto listu je týž řez R1 jako na listu dané místnosti (I-02 až I-05),
jen u rampy je řez navíc a dívá se k zádi na otvor rampy. Toto je dílčí kolo (ne finální předání).

## Co má list obsahovat (zadání autora: „Průřezy s kapslí postavy (rampa, náklad, chodba, kajuta, kokpit)“)

1. Pět příčných řezů v 1:20 s kapslí postavy ve hře (0,56 × 1,80 m, oko 1,65 m) na pochozí ploše.
2. V každém řezu: průchod u podlahy (mezi stěnami, nábytkem a obálkami objektů), šířka ve výšce 1,80 m tam, kde se
   stěny zkosují, světlá výška, výškové úrovně, co je pod podlahou (komponenty z layoutu) a nad stropem, šířka trupu.
3. Tabulka průchodnosti: hodnoty z řezů a závěr „projde / neprojde“ pro kapsli.
4. ID prvků, které řez protíná (stěny, strop, podlaha, nábytek, komponenty, objekty), s odkazem.
5. Srozumitelnost pro autora, který není herní vývojář: má z listu poznat, kudy postava projde a kde je těsno.

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i06_r1\`:
`00_celkovy_pohled.png` a výřezy v plném rozlišení (200 dpi): `01_rampa`, `02_naklad`, `03_chodba`, `04_kajuta`,
`05_kokpit`, `06_pruchodnost`, `07_legenda`, `08_razitko`.
Celý list: `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I06_sections.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – `interior.kit_modules` (běhy
  stěn, díly v řadě), `interior.kit.fittings`
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – místnosti, objekty (z), dveře
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_interior_design.json` – ID, komponenty, návrhy
- `C:\gamespace\gamespace-audit\ArtSource\Kit\kit_rules.json` – profily průřezů (`sections`: vertical_to, slope_rise,
  ceiling; zkosení 3:4)
- `C:\gamespace\gamespace-audit\ArtSource\Kit\Export\kit_manifest.json` – rozměry dílů
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I06_sections.json` – ID nakreslená
  a popsaná v jednotlivých řezech
Udělej namátkovou kontrolu aspoň deseti hodnot (průchody, výšky, ID, polohy proti datům).

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost. 2. Úplnost proti zadání (body 1–5). 3. Soulad s daty. 4. Konvence technického výkresu (kóty, výškové
úrovně, značky, legenda, razítko). 5. Stavebnost a průchodnost (dá se podle listu ověřit, že postava loď projde?).
6. Srozumitelnost pro autora.

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
