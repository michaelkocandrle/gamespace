# Brief: kolo 2 – technický výkres interiéru I-02 – Wayfarer, nákladový prostor

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

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i02_r2\`:
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

## Kolo 1 a co se změnilo (ověř každý bod: opraveno / zčásti / neopraveno, a kde to vidíš)

Kolo 1: FAIL 7 / 6 / 4 / 7 / 6 / 6 (průměr 6,0).
Ohodnoť list znovu celý (všechny kategorie) a k tomu ověř body níže.

Musí se opravit:
1. Šest promítaných nápisů na obložení (D-INT-SEC02, SEC03, SEC04, FIRE, HOLD, GRID): místnost se teď bere podle
   postaveného prostoru (líce obložení ±2,05), nápisy jsou v pohledech 1 a 3 a v tabulce (35 + 12 karet špíny).
2. Reflektory L-FLOOD-L/R nad stropem kitu vyřazené (patří na výkresy exteriéru): 42 světel; hustota z postavené podlahy
   (7,19 × 4,10 = 29,5 m²).
3. Hasicí přístroj: HLD-O-FIRE-01 (vybavení lodi z interior.kit.fittings, „keep“) s účelem, v půdorysu, v pohledu 1
   a v tabulce; ostatní vybavení z téhož seznamu se v nákladu nestaví (kit) a na list nepatří.
4. Nádrž HLD-M-QFUEL: návrh v2 (o 0,10 m k ose, y 0,70 … 1,60) modře čárkovaně se šipkou v půdorysu i v řezu, v kontrole
   dat s důvodem jako „čeká na autora“. Layout se neměnil (rozhoduje autor; layout čtou i exteriérové listy).
Mělo by se opravit: 5 osa mřížky „+0,0 = x 1,00“, u R1 „x 6,40“; 6 tažný paprsek a hydraulika rampy s odkazem v pohledech
stěn (objekty u stěny); 7 rampa v půdorysu: šipka a „závěs, sklápí se ven a dolů (22°)“; 8 poklopy: stav komponent pod
podlahou „postaven poklop v podlaze nad ní, jednotka se nemodeluje“, věta o podlaze opravená (podlaha lodi z desek
0,6 m s poklopy); 9 pás bez stropního panelu na x 1,00 … 1,60 popsaný (bílá místa v pásu trupu ne – tmavá vrstva lodi
nad kitem, popsaná na I-01); 10 před DR-HLD-TEC kóta 0,54 a kapsle Ø 0,56 s výsledkem, v kontrole dat i krytí dveří
s uličkou; 11 účel Bulkhead_Door00L41_C „vlevo, k levoboku“; 12 velikost decalů osazená (z postavené geometrie, sloupec
„osazeno“); 13 štítek za tažným paprskem hlásí kontrola dat (decal za objektem); 14 legenda rozlišuje černě čárkovanou
obálku (postaveno) a modrý návrh, poznámka 3 zná „O“ a „D-INT“; 15 revize A, list 2/2 bez měřítka a s vlastním
podtitulem.
Drobnosti: písmo štítků aspoň 2,0 mm; titulek stropu „orientace jako půdorys“; řádek účelu místnosti pod titulkem
půdorysu; čelní pohledy mají šipky levobok / pravobok; sloupec „trojúh.“ pojmenovaný. Neopraveno: souběžné odkazy na
06 dole, překryvy úrovní s čarami trupu, tmavý trojúhelník v otvoru dveří na 05.

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
