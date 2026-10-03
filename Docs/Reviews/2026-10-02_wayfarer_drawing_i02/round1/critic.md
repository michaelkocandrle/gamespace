# Verdikt: FAIL
První dojem: Přehledný, čistě kreslený dvoulist ve stylu I-04: díly kitu, objekty a dveře sedí na data na centimetr, ale list tiše vynechává šest nápisů na obložení a hasicí přístroj a navíc počítá dva vnější reflektory trupu jako světla nákladu.

| Kategorie | Skóre | Proč |
|---|---|---|
| Čitelnost | 7 | Hierarchie čar je jasná, výplně šedé a štítky mimo pohledy; nejmenší štítky 1,8 mm, na 06 dole souběžné odkazy asi 2 mm od sebe. |
| Úplnost proti zadání | 6 | Body 1–8 mají pohled nebo tabulku; chybí směr otevírání rampy, označené poklopy v podlaze, ID vybavení v pohledech stěn, hasicí přístroj a 6 z 11 nápisů D-INT. |
| Soulad s daty | 4 | Stěny, strop, přepážka, objekty, dveře i nakreslené decaly sedí; nesedí počty (světel 42, ne 44; nápisů 35, ne 29), hasicí přístroj bez ID, plocha 27,4 m² z obdélníku layoutu místo postavených 4,10 m, velikosti decalů z kitu knihovní. |
| Konvence technického výkresu | 7 | Rámeček, razítko, měřítka, výškové úrovně, R1, pohledy 1–4, legenda, odkazy 1/2 ↔ 2/2 v pořádku; osa půdorysu v jiné soustavě než tabulky a titulek řezu, chybí vnitřní kóty průchodů a zápis revize B. |
| Stavebnost a průchodnost | 6 | Mřížka, moduly a kapsle v uličce 1,40 m ověřitelné; nádrž prochází trupem bez řešení, nástup ke dveřím (0,54 m před mřížkou) neověřený, poklopy nezakreslené. |
| Srozumitelnost pro autora | 6 | Skoro všechno má český účel; L-FLOOD a hasicí přístroj bez účelu, třída ID „O“ nevysvětlená, „+5,4“ na ose proti „x 6,40“ v titulku řezu mate. |

Průměr: 6,0

## Musí se opravit
1. 04, 06, 11 – chybí šest postavených promítaných nápisů nákladu (D-INT-SEC02, SEC03, SEC04, FIRE na levoboku, D-INT-HOLD a D-INT-GRID na pravoboku, y ±2,025): model bere místnost z obdélníku layoutu ±1,90 a zahodí, co je za ním; obložení je na ±2,05. Brát příslušnost podle postaveného prostoru.
2. 02, 11, 12 – mezi světly nákladu dva vnější reflektory L-FLOOD-L/R (z 2,59 nad stropem, osvětlení gondol); vyřadit, pak 42 světel, hustotu z postavené podlahy 7,19 × 4,10 = 29,5 m².
3. 01, 03, 04, 05 – hasicí přístroj nakreslený bez ID a účelu (data: interior.kit.fittings, keep); dát ID, účel, řádek v tabulce, popsat v PLAN a EL-L.
4. 08, 03 – nádrž HLD-M-QFUEL zčásti mimo trup bez řešení; navrhnout posun (jako CAB-M-LIFESUP) se starou polohou červeně a novou modře, do té doby kolizi vyznačit.

## Mělo by se opravit
5. 01 – osa v souřadnicích mřížky (+0,0 … +7,2), titulek řezu a tabulky v souřadnicích layoutu; popsat „+0,0 = x 1,00“ a k R1 připsat x.
6. 04, 06, 07 – tažný paprsek a hydraulika rampy v pohledech stěn bez odkazu.
7. 01 – u rampy chybí směr otevírání.
8. 01, 12 – poklopy k pohonu a nádrži nepopsané; věta „jen podlahová deska kitu“ neplatí (podlaha nákladu je lodní).
9. 02 – pás bez stropního panelu (x 1,00 … 1,60, nadpraží rampy) a bílé obdélníky v pásu trupu nepopsané.
10. 01, 03 – před DR-HLD-TEC zbývá mezi mřížkou a přepážkou 0,54 m (< kapsle 0,56), dveře se s uličkou kryjí jen 0,35 m; okótovat a ověřit kapslí.
11. 10 – účel Bulkhead_Door00L41_C „dveře 0,5 m vpravo“ odporuje výkresu i datům (vlevo, k levoboku).
12. 11 – velikosti decalů z kitu jsou knihovní, ne osazené (maker ×0,22, hazard_subtle ×0,3, st_inspect ×0,6).
13. 04 – štítek výrobce HLD-W-L1/maker leží za držákem tažného paprsku.
14. 09, 08 – legenda: skryté pod podlahou černě čárkovaně vs. návrh modře; poznámka 3 bez třídy „O“ a D-INT.
15. 13, 14 – revize B bez záznamu; list 2/2 má měřítko 1:20 a stejný podtitul jako 1/2.

## Drobnosti
Písmo 1,8 mm (štítky socketů, díly pod ID, „+1,2“, „osa“); souběžné odkazy na 06 dole; „+2,30“, „+1,70“ přes čáry trupu na 05 a 07, kóta „nad stropem“ přes „+2,30 strop“ na 03; tmavý trojúhelník v otvoru dveří na 05; titulek tabulky dílů kitu bez podlahy a nevysvětlený sloupec „tr.“; „zrcadleně k půdorysu“ proti poznámce 5; chybí řádek účelu místnosti; čelní pohledy bez značky levobok/pravobok.

## Namátková kontrola dat
Sedí: HLD-W-L1…L6, HLD-W-R1…R6, HLD-C-1…C-6, HLD-C-2 světla, HLD-B-F a jeho světla (text „vpravo“ ne), HLD-O-GRID, HLD-M-QDRIVE/QFUEL (kolize), HLD-O-TRACTOR/RAMPHYD, DR-HLD-TEC, DR-RAMP (bez směru), D-INT-EXIT, CAUTIONLOAD, ENGINEERING, LANE, RAMPHAZARD, Cove/Wash, řez R1 (osa mate).
Nesedí: D-INT-SEC02/03/04, FIRE, HOLD, GRID (chybí); L-FLOOD-L/R (nejsou světla nákladu); hasicí přístroj (bez ID); plocha pro hustotu (27,4 místo 29,5 m²).
