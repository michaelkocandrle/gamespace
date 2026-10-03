# Verdikt: FAIL
První dojem: Úhledný list ve stylu I-04 se silným řezem R1 a úplnou tabulkou světel, jako dokumentace kokpitu ale neúplný: decaly nejsou zakreslené nikde, schody nemají jediný údaj ani profil a přístup k avionice se z listu ověřit nedá.

| Kategorie | Skóre | Proč |
|---|---|---|
| Čitelnost | 6 | Čisté nadpisy, čáry a tabulky; v pohledech 1 a 3 se štítky světel překrývají (L-FIX-14 nečitelné). |
| Úplnost proti zadání | 5 | Decaly v žádném pohledu, schody bez ID, rozměrů a profilu, sklo a rámy kabiny nepopsané. |
| Soulad s daty | 6 | Objekty a 38 světel sedí; decaly bez polohy, pět pravidel rozsevu chybí, stav avioniky „postaveno“ proti „nemodeluje se“, legenda a razítko popisují jinou konvenci. |
| Konvence technického výkresu | 6 | Schody bez výstupní čáry a stupňů, bodovky bez směru, legenda s nepoužitými značkami, bez skla. |
| Stavebnost a průchodnost | 5 | Řez R1 ověřuje průchod 1,20 a výšku 2,07, ale přístup (profil schodů, podesta 0,35, výška v otvoru) ani přístup k avionice za deskou ověřit nejde. |
| Srozumitelnost pro autora | 6 | Účely světel obecné, zkratky L-FIX / L-INT / D-I nevysvětlené, razítko „postaveno z kitu“. |

Průměr: 5,7

## Musí se opravit
1. Decaly D-I-01 … D-I-10 nejsou zakreslené (data: interior.decals.items, paprsek z bodu), tabulka bez polohy a stavu;
   chybí pět pravidel rozsevu v kokpitu (scatter 0, 1, 4, 5, 6).
2. Schody (jediný přístup) bez ID a řádku v rozpisu, bez výstupní čáry, stupňů, profilu; podesta 0,35 m mezi schody
   a opěradlem nezakótovaná; výška v otvoru DR-CAB-CPT neověřena; L-FIX-15 (1. stupeň) chybí bez vysvětlení.
3. Avionika: stav „postaveno“ proti „nemodeluje se“, poklop nezakreslen; poklop (x 18,80 … 19,30) leží za koncovou
   stěnou prostoru pro nohy (x 18,62) pod přístrojovou deskou – přístup „deskou před křeslem“ z dat neplatí; střet v1
   s břichem v R1 není vidět.
4. Překrývající se štítky světel v pohledech 1 a 3 (L-FIX-14/25, L-FIX-13/24).

## Mělo by se opravit
1. Legenda a poznámky: vysvětlit L-FIX, L-INT, D-I; vypustit nepoužité značky, doplnit sklo. 2. Razítko „postaveno
z kitu“. 3. Oko pilota jen jako úroveň: bod v půdorysu a pohledu 1, paprsek přes hranu desky s úhlem (≈ 8°), rozlišit
oko stojící kapsle a sedícího pilota. 4. Hlavní prvky v pohledech bez ID. 5. Kabina zespodu: popsat sklo a rámy,
u L-INT uvést, na čem jsou, šipky směru. 6. Účely světel konkrétně. 7. Text „páky HOSAS v loketních opěrkách“ proti
konzolím. 8. Přesahy postavené geometrie (opěradlo +2,65, křídla desky od x 17,3) v kontrole dat.

## Drobnosti
„Stín vrhá 0 (hlavní světla: )“; plocha 11,0 včetně otvoru schodiště; dvě různé „teplé bílé“; sloupec „osazeno“ →
„rozměr“; „K-01_K-05“.

## Namátková kontrola dat
20 prvků: sedí 15 (CPT-U-SEAT obálka, konzole, deska, DR-CAB-CPT, madla, oko jen výška, R1, L-FIX-16…19, L-FIX-23, 28,
L-INT-7/8, 4/6, 2/12, počet světel, D-INT v kajutě); zčásti L-FIX-14 (štítek), AVIONICS (stav); nesedí D-I-07 … 10
(chybí), rozsev.
