# Brief: technický výkres interiéru I-02 – Wayfarer, nákladový prostor

Hodnotíš **technický výkres**, ne herní vzhled. List I-02 patří do sady výkresů interiéru lodi Wayfarer (dossier lodi,
bod 4). Styl sady autor schválil na vzorovém listu kajuty I-04 (1:20 na A0, detaily 1:5 / 1:10 tam, kde se 1:20
slévá): stejný rámeček, razítko, legenda, kóty, odkazové čáry s ID a stavy prvků (postaveno černě, návrh modře s +);
výkres kreslí skript z týchž dat, ze kterých se loď staví, pohledy jsou z postavené geometrie (díly interiérového kitu,
interiér a trup lodi), ID, účely a návrhy z dat. Toto je dílčí kolo (ne finální předání).

Náklad je dlouhý 7,2 m: jeho čtyři stěny v 1:20 by zabraly 1,2 m papíru, proto je místnost na dvou listech: 1/2 (A0)
pohledy, legenda, klíčový plán, poznámky a kontrola dat; 2/2 (A1) tabulky a souhrn světel. Podlaha nákladu je zatím
lodní (ne z kitu) a zadní stěnu tvoří rampa – záměr, ne chyba.

## Co má list podle zadání autora obsahovat (bod 4 dossieru, pro jednu místnost)

1. Půdorys v mřížce kitu 0,3 m: každý díl kitu jako obrys s ID, podlahové desky, mřížky, poklopy, dveře se směrem
   otevírání, nábytek a objekty (nákladová mřížka 8 SCU, hydraulika rampy, tažný paprsek), komponenty pod podlahou.
2. Rozvinuté pohledy stěn místnosti (obě strany i čela): moduly s ID, výbava, decaly, světla.
3. Plán stropu: stropní díly, svítidla, žlaby, potrubí, poklopy.
4. Průřez: výšky, průchodnost s kapslí postavy (ulička vedle nákladu), co je pod podlahou a nad stropem.
5. Nápisy a decaly s ID z knihovny.
6. Světla: typ, barva, intenzita, stíny, počet na místnost, poznámka k výkonu.
7. Rozpisy: dveře, nábytek a vybavení (ID kitu, účel), komponenty (výklenek, přístup, výměna).
8. Účel každého objektu (autor není herní vývojář: má z listu pochopit, co je postaveno, co je jen návrh a proč).
Klávesnice ani ovládací panel u dveří nejsou záměrně (záměr projektu); chybějící panel nevytýkej.

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i02_r1\`:
`00_celkovy_pohled_1.png`, `00_celkovy_pohled_2.png` (oba listy zmenšené) a výřezy v plném rozlišení (200 dpi):
`01_pudorys`, `02_strop`, `03_rez`, `04`–`07` rozvinuté stěny 1–4, `08_klicovy_plan_poznamky_kontrola`, `09_legenda`,
`10_tabulky_kit_nabytek`, `11_tabulky_svetla_decaly`, `12_souhrn_svetel`, `13_razitko_1`, `14_razitko_2`.
Celé listy: `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I02_hold_1.png` a `_2.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – blok `interior.kit_modules`:
  běhy stěn (začátek, konec, normála líce, moduly) a díly v řadě (začátek, směr, díly); metry layoutu, x od zádi,
  y k levoboku, z od paluby
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – místnosti, objekty s účely, dveře
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_interior_design.json` – ID (`ids`), české
  účely dílů kitu, dveřní křídla (postavené / návrh), komponenty, účely decalů
- `C:\gamespace\gamespace-audit\ArtSource\Kit\Export\kit_manifest.json` – rozměry dílů, sockety světel s parametry
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Wayfarer_setup.json` – promítané decaly D-INT-* (Unreal cm)
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Export\Wayfarer_lights.json` – vlastní světla lodi (L-FLOOD-*)
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I02_hold.json` – ID nakreslená a
  popsaná v jednotlivých pohledech a v tabulkách
Udělej namátkovou kontrolu aspoň deseti prvků (ID, poloha na výkresu proti souřadnicím v datech, stav, účel).

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost: velikost a hierarchie písma, tloušťky čar (řez / obrys / hrana), výplně, překryvy, odkazové čáry
   (při tisku A0 i na monitoru se zoomem).
2. Úplnost proti zadání listu (body 1–8 výše).
3. Soulad s daty: ID, polohy, stavy, počty světel a decalů, tabulky.
4. Konvence technického výkresu: rámeček, razítko, měřítko, kóty, výškové úrovně, značky řezu a pohledů, legenda,
   skryté a navržené prvky, návaznost listů 1/2 a 2/2.
5. Stavebnost a průchodnost: dá se podle listu interiér postavit a ověřit (mřížka kitu, moduly, průchod s kapslí,
   co je pod podlahou a nad stropem, komponenty a jejich přístup)?
6. Srozumitelnost pro autora, který není herní vývojář.

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
