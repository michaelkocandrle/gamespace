# Verdikt: FAIL
První dojem: Hutný výkres celé paluby, na kterém polohy a ID sedí na centimetry, ale v kokpitu si sám odporuje (schod 0,35 m proti podlaze +1,15 a světlá výška 2,30 m pod sklem, kde je ≈ 1,95 m) a v půdorysu je místo schodiště bílá díra.

| Kategorie | Skóre | Proč |
|---|---|---|
| Čitelnost | 6 | Hierarchie funguje (tučné názvy místností v bílých polích, ID v pásech, silný obrys trupu), ale čtení brzdí šedá podlaha s hustou sítí spár a mřížky, drobné šedé texty asi 1,5 mm na A0, křížení obrysů ze dvou rovin řezu v kokpitu a asi deset stejně šedých vzorků materiálů. |
| Úplnost proti zadání | 6 | Půdorys s ID, řez, čtyři tabulky, vazba na I-02 až I-05 i kontrola dat na listu jsou. V půdorysu ale chybí schodiště do kokpitu, u 49 ID dílů kitu chybí modul a účel, u rampy směr otevírání a řez má jen dvě výškové úrovně. |
| Soulad s daty | 6 | V 17 z 19 namátkových kontrol polohy sedí s layoutem a kitem na centimetry. Tabulka místností ale u kokpitu uvádí schod 0,35 m a světlou výšku 2,30 m, kdežto postaveno je +1,15 a ≈ 1,95 m, a stav komponent TEC „návrh“ odporuje geometrii nakreslené v řezu. |
| Konvence technického výkresu | 6 | Rámeček, razítko, měřítko, značky řezu A, stavy prvků a podélné řetězy kót odpovídají stylu I-04. Chybí příčné kóty, výškové úrovně kokpitu a trupu, zlomové čáry u ořezaného trupu, černá čárkovaná čára v legendě a revize B v seznamu revizí. |
| Stavebnost a průchodnost | 5 | Mřížka kitu s počátky a posuny po místnostech je vzorná. ID ale nemají typ modulu, v půdorysu chybí schodiště a obdélníky komponent TEC kolidují s přepážkou a líci stěn, aniž by to kontrola dat hlásila; podle listu tedy palubu nejde postavit ani ověřit. |
| Srozumitelnost pro autora | 5 | České názvy a účely místností pomáhají. Kódy ID ale nemají klíč, kontrola dat nemá závěry, tabulky mluví žargonem a list si sám odporuje v kokpitu (0,35 proti +1,15) i u reaktoru (nakreslený, ale „nepostaveno“). |

Průměr: 5,7 (práh dílčího kroku: průměr aspoň 6,5 a žádná kategorie pod 6. Pod 6 jsou stavebnost a srozumitelnost a k tomu je 5 bodů „musí se opravit“.)

## Musí se opravit
1. **Výřez 03, za přepážkou CAB-B-F (x ≈ 15,2–16,0, y ±0,45)** – Schodiště do kokpitu v půdorysu chybí: bílý prázdný obdélník, vykreslený jen nejvyšší stupeň; řez ukazuje 6 stupňů z ±0,00 na +1,15. – Nakreslit všechny stupně (pod rovinou řezu plně, nad ní čárkovaně se zlomovou čarou), šipku „nahoru“ s počtem a výškou stupňů, šířku mezi madly a kóty začátku a konce schodiště.
2. **Výřez 09, tabulka MÍSTNOSTI, řádek CPT, „účel“** – „Podlaha o schod výš (0,35 m)“, ale řez i layout (`floor_z` 1,15) mají +1,15 (hs `_raise`: 0.35 → 1.15). Kontrola dat to nehlásí. – Opravit účel v datech; kontrola dat má porovnat výšky v textech účelu s `floor_z` a s geometrií.
3. **Výřez 09, řádek CPT, „sv. výška“ („2,30 od +1,15“)** – strop by byl na +3,45, nad vrcholem trupu; podle řezu je pod sklem nejvýš ≈ 1,95 m (za schody) a u křesla ≈ 1,75 m. – Uvést světlou výšku z postavené geometrie a okótovat ji v řezu.
4. **Výřez 02 (modré obdélníky TEC-M-*), výřez 05, výřez 10** – Stav: „návrh, zatím nepostaveno“, ale řez kreslí reaktor a chladič jako postavenou geometrii modulů TEC-W-L1/L2. Polohy: obdélníky z layoutu nesedí na postavené výklenky (TEC-M-POWER zasahuje 0,19 m do přepážky TEC-B-A a 0,15 m přes líc stěny do chodby, TEC-M-SHIELD obdobně, chladiče 0,14–0,19 m před svým modulem). Kontrola dat nic nehlásí. – Rozlišit „model ve výklenku postaven“ od „samostatná komponenta – návrh“; do kontroly dat přidat kolize obdélníků layoutu s přepážkami, líci a výklenky v mm.
5. **Pásy ID (výřezy 01–06), výřez 10** – 49 ID dílů kitu bez modulu, délky a účelu. – Doplnit tabulku dílů kitu (ID, místnost, modul, délka, stav, český účel) nebo psát variantu pod ID v pásech.

## Mělo by se opravit
1. Výřezy 01, 03, 04, 06 – rámy pohledů ořezávají trup bez zlomové čáry (příď za x ≈ 19,8, záď před x ≈ 0,4). – Zlomové čáry s poznámkou, kam trup pokračuje.
2. Výřezy 04, 06 – řez nemá výškové značky podlahy kokpitu, dna podpodlahového prostoru a trupu ani vrcholu trupu; chybí svislé kóty schodiště a světlé výšky dveří. – Doplnit.
3. Výřez 07 legenda, výřez 01 (HLD-O-TRACTOR), výřez 03 (konzole) – černě čárkované obdélníky v legendě nejsou; čárkovaně jsou i prvky nad podlahou. – Rozlišit v legendě: černě čárkovaně pod podlahou, modře čárkovaně návrh, čerchovaně obrys z layoutu.
4. Výřezy 01, 04 – u DR-RAMP chybí směr otevírání. – Otevřenou rampu čárkovaně pod 22° v řezu, obrys v půdorysu.
5. Výřezy 01–03 – jen podélné řetězy kót; chybí příčné (šířky mezi líci, poloha a šířka dveří, ulička, schody).
6. Výřez 03, kokpit – kříží se obrysy ze dvou rovin řezu; poznámka drobná. – Lomená řezová čára, odlišit obrys z druhé roviny.
7. Výřez 09 – plocha z obdélníku layoutu, šířka z líců (HLD 27,4 místo 29,5; TEC 8,1 místo ≈ 4,3). – Stejný základ, v hlavičce z čeho.
8. Výřez 07 – chybí klíč ke kódům ID.
9. Výřez 08 – body kontroly dat bez závěru (záměr / k opravě / čeká na autora).
10. Výřezy 01–03 – šedá podlaha se spárami a mřížkou tvoří hustou síť, drobné texty ≈ 1,5 mm. – Zesvětlit podlahu, mřížku tenčeji, čáry po 1,2 m výrazněji, texty aspoň 2 mm.
11. Výřez 07 – 21 vzorků materiálů, asi deset stejně šedých; vzorky světel a decalu na list nepatří.
12. Výřezy 04, 06 – odkazy v řezu končí ve středu kvádru (mřížka ve vzduchu, křeslo pod podlahou). – Na viditelnou hranu.
13. Výřez 04 – bílý rám nad stropem nákladu (x ≈ 4,5–5,5) bez popisu.
14. Výřez 11 – revize B v razítku, v seznamu jen A.

## Drobnosti
1. Překryvy: HLD-O-GRID přes „HLD-W-R4“, poznámka pod podlahou protnutá obdélníkem QDRIVE, „CPT“ na čáře skla.
2. LIFESUP: chybí šipka k nové poloze, popisek v1 malý.
3. DR-HLD-TEC: křídlo na líci HLD-B-F místo v kapse TEC-B-A.
4. Náhradní pásy podlahy pod portály (`stand_in_floor`) neoznačené.
5. Řez nemá pás ID podlah (servisní kanál pod TEC-FL-2).
6. Poslední úsek „líce přepážek“ (4,21) končí na konci obdélníku kokpitu, ne na líci.
7. Tabulka mluví žargonem („interior.kit_modules“), sloupec účel dlouhý ≈ 19 cm.
8. Šedé řádky seznamu listů nevysvětlené.
9. Obdélníky místností z layoutu nezakreslené.

## Namátková kontrola dat
19 prvků: 17 sedí (HLD-O-RAMPHYD, HLD-O-TRACTOR, HLD-M-QDRIVE, HLD-M-QFUEL, HLD-O-GRID, HLD-W-L1…L6, HLD-C-1,
TEC-W-L1/L2, DR-HLD-TEC, DR-TEC-CAB, DR-CAB-HYG, CAB-U-LOCKER, CAB-M-LIFESUP, CPT-O-GRAB-01, CPT-M-AVIONICS, řetězy kót);
nesedí TEC-M-POWER (proti postaveným dílům a stavu) a místnost CPT (schod 0,35 a výška 2,30 proti +1,15 a ≈ 1,95);
CPT-U-SEAT: v půdorysu sedí, odkaz v řezu míří pod podlahu.
