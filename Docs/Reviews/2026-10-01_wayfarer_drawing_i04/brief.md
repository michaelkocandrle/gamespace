# Brief: vzorový technický výkres interiéru I-04 – Wayfarer, kajuta

Hodnotíš **technický výkres**, ne herní vzhled. Je to vzorový list, podle kterého autor schválí styl všech dalších
výkresů interiéru lodi Wayfarer (dossier lodi, bod 4). Styl exteriérových listů E-01 až E-08 autor schválil;
interiér má mít stejný jazyk (rámeček, razítko, měřítko, legenda, kóty, odkazové čáry s ID, stavy prvků) a stejný
princip: výkres kreslí skript z týchž dat, ze kterých se loď staví, a každá část nese ID, které je v datech.
Pohledy jsou kreslené z postavené geometrie (díly interiérového kitu a interiér lodi), ID, účely a návrhy z dat.

## Co má list podle zadání autora obsahovat (bod 4 dossieru, pro jednu místnost)

1. Půdorys v mřížce kitu 0,3 m: každý díl kitu jako obrys s ID, podlahové desky, mřížky, poklopy, dveře se směrem
   otevírání, nábytek.
2. Rozvinuté pohledy stěn místnosti (obě strany i čela): moduly s ID, výbava, decaly, světla.
3. Plán stropu: stropní díly, svítidla, žlaby, potrubí, poklopy.
4. Průřez: výšky, průchodnost s kapslí postavy, co je pod podlahou a nad stropem.
5. Nápisy a decaly s ID z knihovny.
6. Světla: typ, barva, intenzita, stíny, počet na místnost, poznámka k výkonu.
7. Rozpisy: dveře, nábytek a vybavení (ID kitu, účel), komponenty (výklenek, přístup, výměna).
8. Účel každého objektu (autor nebývá herní vývojář: má z listu pochopit, co je postaveno, co je jen návrh a proč).
Stavy prvků: postaveno černě, návrh modře (+). Klávesnice ani ovládací panel u dveří nejsou záměrně (záměr
projektu); stav dveří ukazuje světlo a značení – chybějící panel nevytýkej.

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace\ad2ac10f-4bac-4b92-ac91-90ddac002bd2\scratchpad\i04_review_r1\`:
`00_celkovy_pohled.png` (celý list A0 zmenšený) a výřezy v plném rozlišení (200 dpi): `01_pudorys`, `02_strop`,
`03_rez`, `04`–`07` rozvinuté stěny 1–4, `08_legenda_klicovy_plan`, `09_poznamky`, `10_tabulky_kit_nabytek`,
`11_tabulky_svetla_decaly`, `12_souhrn_svetel_kontrola_dat`, `13_razitko`.
Celý list: `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I04_cabin.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – blok `interior.kit_modules`:
  běhy stěn (začátek, konec, normála líce, moduly) a díly v řadě (začátek, směr, díly); metry layoutu, x od zádi,
  y k levoboku, z od paluby
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – místnosti, objekty s účely, dveře
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_interior_design.json` – ID (`ids`), české
  účely dílů kitu, dveřní křídla (postavené / návrh), komponenty, účely decalů
- `C:\gamespace\gamespace-audit\ArtSource\Kit\Export\kit_manifest.json` – rozměry dílů, sockety světel s parametry
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Wayfarer_setup.json` – promítané decaly D-INT-* (Unreal cm)
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I04_cabin.json` – ID nakreslená a
  popsaná v jednotlivých pohledech a v tabulkách
Udělej namátkovou kontrolu aspoň deseti prvků (ID, poloha na výkresu proti souřadnicím v datech, stav, účel).

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost: velikost a hierarchie písma, tloušťky čar (řez / obrys / hrana), výplně, překryvy, odkazové čáry
   (při tisku A0 i na monitoru se zoomem).
2. Úplnost proti zadání listu (body 1–8 výše).
3. Soulad s daty: ID, polohy, stavy, počty světel a decalů, tabulky.
4. Konvence technického výkresu: rámeček, razítko, měřítko, kóty, výškové úrovně, značky řezu a pohledů, legenda,
   skryté a navržené prvky.
5. Stavebnost a průchodnost: dá se podle listu interiér postavit a ověřit (mřížka kitu, moduly, průchod s kapslí,
   co je pod podlahou a nad stropem, komponenty a jejich přístup)?
6. Srozumitelnost pro autora, který není herní vývojář: pozná z listu, co je postaveno, co je návrh a k čemu slouží?

Práh PASS (dílčí krok): průměr aspoň 6,5, žádná kategorie pod 6, žádná výtka „musí se opravit".

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
