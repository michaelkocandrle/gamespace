# Brief: kolo 3 – technický výkres interiéru I-01 – Wayfarer, hlavní paluba (celá loď)

Hodnotíš **technický výkres**, ne herní vzhled. List I-01 patří do sady výkresů interiéru lodi Wayfarer (dossier lodi,
bod 4). Styl sady autor schválil na vzorovém listu místnosti I-04 (kajuta): stejný rámeček, razítko, měřítko 1:20
na A0, legenda, kóty, odkazové čáry s ID, stavy prvků (postaveno černě, návrh modře s +, dřívější poloha červeně
čárkovaně). Výkres kreslí skript z týchž dat, ze kterých se loď staví; pohledy jsou z postavené geometrie (díly
interiérového kitu a interiér a trup lodi), ID, účely a návrhy z dat. Toto je dílčí kolo (ne finální předání).

## Co má list I-01 obsahovat (zadání autora: „Půdorys paluby v mřížce kitu 0,3 m (celá loď)“)

1. Půdorys celé hlavní paluby v mřížce kitu 0,3 m: každý díl kitu (stěny, přepážky, podlahy) s ID, nábytek,
   dveře se směrem otevírání, komponenty a objekty z layoutu (pod podlahou čárkovaně), hranice a názvy místností.
2. Vazba na listy místností (I-02 náklad, I-03 technická chodba, I-04 kajuta, I-05 kokpit): kde je co podrobně.
3. Podélný řez (výšky paluby, stropu, schod do kokpitu, co je pod podlahou a nad stropem, přepážky a dveře).
4. Tabulky: místnosti (rozměry, plocha, výška, stavba z kitu nebo lodí, účel), dveře, prvky s ID, mřížka kitu.
5. Kontrola dat: rozpory mezi layoutem a postavenými díly.
6. Srozumitelnost pro autora, který není herní vývojář.
Světla a decaly na tento list záměrně nepatří (jsou na listech místností a na I-07, I-08). Klávesnice ani ovládací
panel u dveří nejsou záměrně (záměr projektu); chybějící panel nevytýkej.

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i01_r3\`:
`00_celkovy_pohled.png` (celý list A0 zmenšený) a výřezy v plném rozlišení (200 dpi): `01`–`03` půdorys (záď, střed,
příď), `04`–`06` řez A (záď, střed, příď), `07_legenda_poznamky_dily` (legenda, poznámky, tabulka dílů kitu), `08_kontrola_dat`,
`09_tabulky_mistnosti_dvere`, `10_tabulka_prvky`, `12_tabulka_mrizka`, `11_razitko`.
Celý list: `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I01_deck.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – blok `interior.kit_modules`:
  běhy stěn `wall_runs` (začátek, konec, normála líce, moduly) a díly v řadě `run_parts`; metry layoutu, x od zádi,
  y k levoboku, z od paluby
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – místnosti, objekty s účely, dveře
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_interior_design.json` – ID (`ids`), české
  účely dílů kitu, dveřní křídla (postavené / návrh), komponenty
- `C:\gamespace\gamespace-audit\ArtSource\Kit\Export\kit_manifest.json` – rozměry dílů
- `C:\gamespace\gamespace-audit\ArtSource\Kit\kit_rules.json` – mřížka (`grid`)
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I01_deck.json` – ID nakreslená a
  popsaná v pohledech PLAN a LSEC a v tabulkách
Udělej namátkovou kontrolu aspoň deseti prvků (ID, poloha na výkresu proti souřadnicím v datech, stav, účel).

## Kolo 2 a co se změnilo (ověř každý bod: opraveno / zčásti / neopraveno, a kde to vidíš)

Kolo 2: FAIL 7 / 7 / 7 / 7 / 6 / 7 (průměr 6,8; dva body „musí“).
Ohodnoť list znovu celý (všechny kategorie) a k tomu ověř body níže.

Musí se opravit (kolo 2):
1. Světlá výška kokpitu: měří se nad celou pochozí plochou za schody (x 16,24 … 16,55, pás y ±0,30) ze všech dílů
   včetně trupu, kabiny a jejích žeber; nejníž je žebro kabiny na +3,20 v x 16,32 → 2,05. V řezu y 0,30 se žebro kreslí
   níž, protože jde dál k boku za rovinou řezu – v pásu nad hlavou je +3,20 (ověřeno řezy geometrie). Kóta a tabulka
   uvádějí místo měření; nad kokpitem je značka vrcholu kabiny.
2. Díly kitu: šedý díl pod ID stropů v pásu nad řezem, za ID přepážek a nábytku v odkazech; tabulka DÍLY KITU má
   sloupec ID a řádky nábytku z kitu (počty sedí s tabulkou MÍSTNOSTI).
Mělo by se opravit (kolo 2): 1 účel HLD-B-F „vlevo, k levoboku“; 2 nad každou místností značka stropu z geometrie,
+2,30 popsané „strop v layoutu“; 3 odkaz mřížky na úchyt u podlahy, odkaz křesla na sedák; 4 rovina řezu a lom
dlouhou čerchovanou čarou se silnými konci; 5 zlomové čáry a poznámky i v řezu.
Drobnosti: pata rampy popsaná (x −3,00, z −1,60, za rámem); účel CPT v tabulce označený „[k opravě]“; šířka CPT
z obrysu (3,50); zelená kóta v legendě; schodiště se stupněm 0,18 a sklonem; podlaha nákladu „z kitu, podlaha lodi“;
přibyl hasicí přístroj HLD-O-FIRE-01 (vybavení lodi, interior.kit.fittings). Neopraveno: šipka u LIFESUP, výška otvoru
DR-HLD-TEC (v datech není), ulička 1,40 proti „1,25“ v účelu.

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost: velikost a hierarchie písma, tloušťky čar (řez / obrys / hrana), výplně, překryvy, odkazové čáry
   (při tisku A0 i na monitoru se zoomem).
2. Úplnost proti zadání listu (body 1–6 výše).
3. Soulad s daty: ID, polohy, stavy, tabulky.
4. Konvence technického výkresu: rámeček, razítko, měřítko, kóty, výškové úrovně, značky řezu, legenda, skryté
   a navržené prvky.
5. Stavebnost a průchodnost: dá se podle listu paluba postavit a ověřit (mřížka kitu, moduly, návaznost místností,
   dveře, co je pod podlahou)?
6. Srozumitelnost pro autora, který není herní vývojář.

Práh PASS (dílčí krok, `"gate": "step"`): průměr aspoň 6,5, žádná kategorie pod 6, žádná výtka „musí se opravit".

## Formát odpovědi (česky, Markdown; za tabulkou kategorií přidej sekci „## Ověření bodů kola 2“)

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
