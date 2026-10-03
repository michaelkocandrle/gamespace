# Brief: kolo 2 – technický výkres interiéru I-03 – Wayfarer, technická chodba s komponentami

Hodnotíš **technický výkres**, ne herní vzhled. List I-03 patří do sady výkresů interiéru lodi Wayfarer (dossier lodi,
bod 4). Styl sady autor schválil na vzorovém listu kajuty I-04 (1:20 na A0, detaily 1:5 / 1:10 tam, kde se 1:20
slévá): stejný rámeček, razítko, legenda, kóty, odkazové čáry s ID a stavy prvků (postaveno černě, návrh modře s +);
výkres kreslí skript z týchž dat, ze kterých se loď staví, pohledy jsou z postavené geometrie (díly interiérového kitu,
interiér a trup lodi), ID, účely a návrhy z dat. Toto je dílčí kolo (ne finální předání).

Komponenty lodi (reaktor, dva chladiče, generátor štítů) jsou ve hře postavené jako součást stěnových modulů
s výklenky (díly kitu Wall_ComponentBay*); obdélníky komponent v layoutu se od postavených výklenků liší a list to hlásí
v kontrole dat jako otázku pro autora – kit platí před layoutem (rozhodnutí autora 1. 10. 2026).

## Co má list podle zadání autora obsahovat (bod 4 dossieru, pro jednu místnost)

1. Půdorys v mřížce kitu 0,3 m: každý díl kitu jako obrys s ID, podlahové desky, mřížky, poklopy, dveře se směrem
   otevírání, komponenty ve výklenkách stěn.
2. Rozvinuté pohledy stěn místnosti (obě strany i čela): moduly s ID, výbava, decaly, světla.
3. Plán stropu: stropní díly, svítidla, žlaby, potrubí, poklopy.
4. Průřez: výšky, průchodnost s kapslí postavy, co je pod podlahou a nad stropem.
5. Nápisy a decaly s ID z knihovny.
6. Světla: typ, barva, intenzita, stíny, počet na místnost, poznámka k výkonu.
7. Rozpisy: dveře, nábytek a vybavení (ID kitu, účel), komponenty (výklenek, přístup, výměna); detaily výklenků.
8. Účel každého objektu (autor není herní vývojář: má z listu pochopit, co je postaveno, co je jen návrh a proč).
Klávesnice ani ovládací panel u dveří nejsou záměrně (záměr projektu); chybějící panel nevytýkej.

## Listy k prohlédnutí (otevři každý nástrojem Read)

Složka `C:\Users\micha\AppData\Local\Temp\claude\C--gamespace-gamespace-audit\75d27abd-209d-454f-8ee9-7b2970d127cc\scratchpad\i03_r2\`:
`00_celkovy_pohled.png` (celý list A0 zmenšený) a výřezy v plném rozlišení (200 dpi): `01_pudorys`, `02_strop`,
`03_rez`, `04_detaily_vyklenku`, `05`–`08` rozvinuté stěny 1–4, `09_legenda_klicovy_plan`, `10_poznamky`,
`11_tabulky_kit_nabytek`, `12_tabulky_svetla_decaly`, `13_souhrn_svetel_kontrola_dat`, `14_razitko`.
Celý list: `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I03_tech.png`.

## Data ke kontrole souladu (čti, nic neměň)

- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\HardSurface\Wayfarer_hs.json` – blok `interior.kit_modules`:
  běhy stěn (začátek, konec, normála líce, moduly) a díly v řadě (začátek, směr, díly); metry layoutu, x od zádi,
  y k levoboku, z od paluby
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_layout.json` – místnosti, objekty s účely, dveře
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Wayfarer_interior_design.json` – ID (`ids`), české
  účely dílů kitu, dveřní křídla (postavené / návrh), komponenty, účely decalů
- `C:\gamespace\gamespace-audit\ArtSource\Kit\Export\kit_manifest.json` – rozměry dílů, sockety světel s parametry
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Wayfarer_setup.json` – promítané decaly D-INT-* (Unreal cm)
- `C:\gamespace\gamespace-audit\Tools\Kit\kit_batch4.py` – výklenky komponent (BAY_DEPTH, SILL, HEAD, otvor)
- `C:\gamespace\gamespace-audit\ArtSource\Ships\Wayfarer\Design\Drawings\Wayfarer_I03_tech.json` – ID nakreslená a
  popsaná v jednotlivých pohledech a v tabulkách
Udělej namátkovou kontrolu aspoň deseti prvků (ID, poloha na výkresu proti souřadnicím v datech, stav, účel).

## Kolo 1 a co se změnilo (ověř každý bod: opraveno / zčásti / neopraveno, a kde to vidíš)

Kolo 1: FAIL 5 / 6 / 5 / 6 / 5 / 6 (průměr 5,5).
Ohodnoť list znovu celý (všechny kategorie) a k tomu ověř body níže.

Musí se opravit:
1. Křídla DR-TEC-CAB proti zkosení: kontrola dat to teď počítá z profilu stěny (od jaké výšky a o kolik křídlo zasahuje)
   a hlásí světla a nápisy na dráze křídla; návrh k rozhodnutí autora: křídla na straně kajuty (obložení L, líce ±1,90,
   zkosení od +1,70) nebo užší křídla. Křídla schválil autor 1. 10. na straně chodby – rozhodne znovu on.
2. Výškové úrovně z profilu průřezu stěn (kit_rules W): +1,30 lišta, začátek zkosení; +2,10 konec zkosení, římsa;
   +2,30 strop – v pohledech stěn i v řezu.
3. Přístup ke komponentám podle postaveného dílu: posuvné křídlo výklenku otevřené v kapse (účely dílů a komponent
   v datech návrhu opravené).
4. Hustota světel z postavené podlahy mezi líci (1,79 × 2,40 = 4,3 m²), s poznámkou, že kit nemá pravidlo pro
   technické prostory.
5. Detaily výklenků přesunuté do druhé řady vpravo od stěn (nedotýkají se legendy); přibyl detail C (chladič).
Mělo by se opravit: 1 křídlo DR-HLD-TEC v kapse přepážky TEC-B-A (x 8,39) v datech návrhu i na výkresu, v pohledu 4
čárkovaně; 2 v řezu šířka ve výšce 1,80 mezi zkoseními a světlá výška v ose pod rovným stropem; 3 servisní kanál pod
roštem TEC-FL-2 popsaný; 4 světla stěn (Cove, Wash) jsou v pohledech stěn – řečeno v poznámce 5 (výšky v plánu stropu
nepřibyly); 5 detail C chladiče; 6 obálky vysunutých komponent (výměna do chodby) čárkovaně v půdorysu (oblouk poklopu
generátoru ne); 7 svazky odkazů: neopraveno; 8 odkazy stěn v řezu na řezané stěně modulu; 9 štítky Door / Reveal nad
dveřmi rozložené; 10 Bay = „světlo výklenku (svítí na komponentu)“; 11 řezové značky detailů A, B, C v půdorysu;
12 souhrn světel bez žargonu, sloupec „trojúh.“.
Drobnosti: revize A; velikost decalů osazená; štítky světel 2,0 mm; osa mřížky „+0,0 = x 8,54“; hloubka výklenku
světlá i s obložením; legenda s černě čárkovanou obálkou. Neopraveno: barva mřížky, kóta 1,79 proti modulům.

## Kategorie (skóre 1–10, jedna věta proč)

1. Čitelnost: velikost a hierarchie písma, tloušťky čar (řez / obrys / hrana), výplně, překryvy, odkazové čáry
   (při tisku A0 i na monitoru se zoomem).
2. Úplnost proti zadání listu (body 1–8 výše).
3. Soulad s daty: ID, polohy, stavy, počty světel a decalů, tabulky.
4. Konvence technického výkresu: rámeček, razítko, měřítko, kóty, výškové úrovně, značky řezu a pohledů, legenda,
   skryté a navržené prvky.
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
