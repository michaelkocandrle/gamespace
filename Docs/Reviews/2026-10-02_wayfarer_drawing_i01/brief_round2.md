# Brief: kolo 2 – technický výkres interiéru I-01 – Wayfarer, hlavní paluba (celá loď)

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

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i01_r2\`:
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

## Kolo 1 a co se změnilo (ověř každý bod: opraveno / zčásti / neopraveno, a kde to vidíš)

Kolo 1: FAIL 6 / 6 / 6 / 6 / 5 / 5 (průměr 5,7). Ohodnoť list znovu celý (všechny kategorie) a k tomu ověř:

Musí se opravit:
1. Schodiště do kokpitu v půdorysu: všechny stupně, šipka „nahoru 6 × 0,192“, šířka mezi bočnicemi a délka letu kótami;
   v řezu svislá kóta 6 × 0,192 = 1,15.
2. Účel kokpitu v layoutu („0,35 m“): **text v layoutu nezměněn** – layout čte i sada exteriérových výkresů E-01 až E-08
   a ty mění jen hlavní session; rozpor teď hlásí kontrola dat jako „[k opravě]“ s odkazem na data stavby (cockpit._raise).
3. Světlá výška kokpitu: z postavené geometrie (nejnižší plocha v ose za schody), v tabulce i jako kóta v řezu.
4. Komponenty TEC: model teď bere jako jejich polohu postavený výklenek modulu kitu (Wall_ComponentBay, SOCKET_Component),
   stav „postaveno“; rozdíl layoutu proti výklenku je v kontrole dat v mm jako „[k opravě] … kit platí, layout opravit“.
5. Díly kitu: pod každým ID v pásech a u desek podlahy je šedě díl kitu; tabulka DÍLY KITU (díl, počet, český účel).

Mělo by se opravit: 1 zlomové čáry a poznámky, kam trup pokračuje; 2 výškové značky trupu nad a pod každou
místností, podlaha kokpitu, kóty schodiště, otvoru DR-TEC-CAB (2,05) a světlé výšky; 3 legenda rozlišuje černě
čárkovanou obálku z layoutu, modře návrh, červeně dřívější polohu, čerchovaně obrys místnosti z layoutu; 4 rampa dole
(22°) v řezu z dat layoutu (v půdorysu ne: za zádí už není místo v rámu, poznámka a řez); 5 příčné řetězy kót
u zadního konce každé místnosti z kitu (líce a dveře); 6 lomený řez u kokpitu: silná čerchovaná čára a větší popisek;
7 délka, šířka a plocha místností z líců postavených dílů (kokpit z obrysu layoutu), sloupec „základ“; 8 klíč ID
v poznámce 3; 9 každý bod kontroly dat má závěr [záměr] / [k opravě] / [čeká na autora]; 10 výplně o 40 % světlejší,
vedlejší čáry mřížky tenčí, hlavní po 1,2 m silnější, drobné texty aspoň 2,1 mm; 11 legenda bez vzorků materiálů,
světel a decalů; 12 odkazy v řezu na patu prvku (mřížka na podlaze, sedák křesla); 13 tmavá vrstva nad stropem
nákladu popsaná; 14 revize A (první vydání).
Drobnosti: náhradní pásy podlahy pod portály popsané; obrysy místností z layoutu zakreslené; řetěz líců popsaný
(„konce: závěs rampy, špička kokpitu“); „šedě = zatím nenakresleno“ u seznamu listů; tabulka bez žargonu.
Neopraveno vědomě: drobnost 3 (křídlo DR-HLD-TEC se kreslí v rovině otvoru z layoutu, x 8,20), drobnost 5 (pás ID
podlah v řezu – podlahy jsou v půdorysu), drobnost 1 částečně (odsazení překryvů dělá rozmístění popisků samo).

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

## Formát odpovědi (česky, Markdown; za tabulkou kategorií přidej sekci „## Ověření bodů kola 1“)

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
