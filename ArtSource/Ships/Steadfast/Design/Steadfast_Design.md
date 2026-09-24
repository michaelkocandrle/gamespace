# Steadfast – návrh lodi v2 (ke schválení)

Stav: **návrh 24. 9. 2026, čeká na schválení autorem.** Dokud není schválený, nic z něj se nestaví ve 3D.

Zdroje, ze kterých se všechno kreslí:

- rozvržení: `Steadfast_layout.json` (místnosti, objekty, dveře; souřadnice v metrech);
- specifikace: `../Steadfast_spec.json` (ve tvaru RSI Ship Matrix);
- výkresy: `Steadfast_deck_upper.png`, `Steadfast_deck_lower.png`, `Steadfast_cutaway.png`. Kreslí je `python Tools/Design/draw_ship_design.py ArtSource/Ships/Steadfast/Design/Steadfast_layout.json`.

## 1. Vize

Halcyon Freightworks Steadfast je poctivá pracovní loď pro malou posádku na dlouhé trasy na okraj zmapovaného prostoru. Tři lidé na ní žijí týdny: nahoře mají domov, dole náklad a stroje. Loď je navržená tak, aby se dostala zpátky i bez stanice. Má proto velké nádrže, ošetřovnu, zbrojnici s EVA výstrojí, náhradní díly a strojovnu přístupnou za letu.

Loď se nemá tvářit jako luxusní jachta ani jako vojenský stroj. Má působit jako dobře udržovaný nákladní vůz budoucnosti: poctivý materiál, jasné značení a všechno na svém místě.

## 2. Parametry (Ship Matrix)

| | |
|---|---|
| Výrobce / role | Halcyon Freightworks · transport · Freight / Exploration · medium |
| Rozměry | délka 30 m · šířka 22 m (s motorovými gondolami; tlakový trup 6,4 m) · výška 9,5 m (s podvozkem) |
| Hmotnost / náklad | 185 t · 42 SCU |
| Posádka | 1–3 · 3 lůžka · stanoviště: pilot, druhý pilot / navigátor, senzory a komunikace s drapáky, inženýr (pult ve strojovně) |
| Let | SCM 140 m/s · AB 240 m/s · pitch 55 / yaw 40 / roll 75 °/s · zrychlení: vpřed 45, vzad 30, do stran 25, nahoru 30, dolů 25 m/s² (zrychlení je návrh; rychlosti a rotace už hra používá) |
| Avionika | radar S2 · počítač S2 (přední technická místnost) |
| Pohon | 2× nádrž vodíku · quantum drive S2 · nádrž quantum paliva 4,5 SCU · 2× hlavní motor TR4 v gondolách · 12× manévrovací TR2 |
| Moduly | reaktor S2 (prochází oběma palubami) · 2× chladič S2 · 2× generátor štítů S2 · podpora života S2 |
| Zbraně | 2× S3 v přídi (pilot) · dálková věž 2× S2 na hřbetě (ovládá ji stanoviště senzorů) · 4× raketa S2 |
| Vybavení | 2× nákladní drapák pod břichem · dokovací límec na levém boku |

## 3. Uspořádání

Loď má dvě paluby nad sebou v tlakovém trupu širokém 6,4 m. Hlavní motory sedí ve dvou bočních gondolách, proto zadní stěna trupu nese jen jejich přívody a strojovna zůstává průchozí.

- **Dolní paluba** (podlaha 0 m, světlá výška 3,0 m): náklad a technika.
  - Na zádi je dolní patro strojovny.
  - Uprostřed je nákladový prostor s rampou v břiše.
  - Na přídi je přední technická místnost a přechodová komora.
- **Horní paluba** (podlaha 3,3 m, světlá výška 2,4 m): obytná část a řízení.
  - Na zádi je horní patro strojovny.
  - Uprostřed vede hlavní chodba a z ní se vstupuje do kajut a služeb.
  - Na přídi je předsíň můstku a kokpit.
- **Propojení palub:**
  - U přídě vede schodiště z přední technické místnosti do předsíně můstku.
  - Na zádi vede žebřík vedle reaktoru.
  - Obě paluby tak tvoří okruh a nikde se nejde slepou uličkou dvakrát.

Každá místnost a každý objekt i s účelem jsou ve výkresech a v `Steadfast_layout.json`: horní paluba má 24 objektů, dolní 16. Nic tam není jen pro vyplnění místa.

### Pohyb posádky

- **Nástup ze země:** rampa v břiše → nákladový prostor (ulička podél pravé stěny) → přední technická místnost → schodiště → předsíň → kokpit. Je to asi 25 m chůze, stejně jako v SC, kde člověk loď při nástupu prochází.
- **Nástup ze stanice / z jiné lodi:** dokovací límec → přechodová komora → přední technická místnost → schodiště.
- **Život na palubě:** z hlavní chodby jsou všechny dveře na dva kroky. Kajuty jsou na levém boku, kuchyňka, koupelna a zbrojnice na pravém. Na konci chodby jsou tlakové dveře do strojovny.
- **Opravy:** pult inženýra má výhled na reaktor, žebříkem se slézá dolů k nádržím a chladičům a dveřmi mezi chladiči se jde přímo do nákladu.

## 4. Designový jazyk interiéru

Styl je SC, ale vlastní („vibe, ne kopie“).

- **Architektura:** teplá / neutrální.
  - Panely z tmavého kovu s viditelným členěním a spárami.
  - Tmavá podlaha s kovovou mřížkou v technických prostorech.
  - V obytné části je podlaha plná, s pryžovým povrchem.
  - Hrany a rohy jsou zkosené; žádné holé krabice.
- **Světlo:**
  - Světelné pásy ve stropě a u podlahy; pracovní světla 5200 K.
  - V kajutách a jídelně teplejší (≈ 3500 K) a tlumené.
  - Ve strojovně a nákladu studené a pracovní.
  - V kokpitu tma, aby vynikly obrazovky a hologramy.
- **UI:** studené holografické obrazovky (tyrkys / modrá) jen tam, kde se s něčím pracuje:
  - v kokpitu, u pultu inženýra, u panelu rampy, u komory, u terminálu kapitána a na ošetřovně.
  - Žádné samostatné svítící terminály u dveří. Dveře se otevírají samy nebo z malého podsvíceného pole přímo v rámu.
- **Značení:** šablonové nápisy a výstražné pruhy (decaly, které fungují) – čísla místností, šipky únikových cest, „CARGO“, výstrahy u rampy a u reaktoru.
- **Každý objekt patří lodi:**
  - Sedadla a konzole mají kabely a úchyty do podlahy.
  - Náklad je ukotvený v mřížce.
  - Skříňky mají svůj obsah (skafandry, léky, díly).

## 5. Co se tím mění proti dnešnímu 3D interiéru

Dnešní interiér je jednopodlažní zkušební průchod (strojovna → náklad → chodba → kokpit) z kitu a procedurálních tvarů. Autor ho 24. 9. odmítl: keypad, levný pult, nízké stěny bez detailu, objekty bez účelu. Po schválení tohoto návrhu se interiér postaví znovu podle `Steadfast_layout.json`:

- po místnostech;
- nejdřív kokpit a předsíň, protože v nich hráč začíná;
- detailní objekty z Meshy / Scenario po kusech.

Z dnešní verze zůstává to, co autor schválil:

- decaly;
- světelné pásy a osvětlení;
- hologramy (doladit);
- Meshy sedadla.

## 6. Otevřené otázky pro autora

1. Náklad 42 SCU (dvě vrstvy, ulička 1,9 m) – stačí, nebo spíš víc nákladu a užší ulička (až 56 SCU)?
2. Dálková věž na hřbetě a stanoviště senzorů v kokpitu – ano, nebo loď bez věže (čistý hauler)?
3. Ošetřovna vs. druhá kajuta – má loď mít ošetřovnu, nebo radši větší kajutu posádky?
4. Vstup rampou v břiše (jako Freelancer) vs. zadní rampou (jako Cutlass / C1) – zadní rampa by znamenala přesunout strojovnu nahoru a doprostřed.
