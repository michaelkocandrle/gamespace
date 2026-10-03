# Verdikt: FAIL
První dojem: List působí profesionálně a je hutný (půdorys, strop, řez, čtyři rozvinuté stěny, dva detaily 1:10, rozpisy), ale proti datům neobstojí: úroveň zkosení je ve všech pohledech špatně, navržená křídla dveří ke kajutě se do profilu nevejdou, popis přístupu ke komponentám neodpovídá postavenému dílu a rámeček detailu B jede přes legendu.

| Kategorie | Skóre | Proč |
|---|---|---|
| Čitelnost | 5 | Hierarchie jasná, ale rámeček detailu B přejíždí legendu i klíčový plán, odkazy ve svazcích, štítek TEC-B-A/Door_0 není vidět, štítky světel asi 1,3 mm. |
| Úplnost proti zadání | 6 | Všech osm bodů je; chybí detail výklenku chladiče, výšky a kóty a světla Cove/Wash v plánu stropu, servisní kanál pod roštem TEC-FL-2, křídlo DR-HLD-TEC v pohledu 4. |
| Soulad s daty | 5 | Moduly, výklenky, světla a počty sedí; nesedí „+1,70 zkosení“, plocha 8,1 m², přístup k reaktoru a chladičům, účel „světlo výdejníku“, odkazy TEC-W-L1/R1 v řezu, poloha křídla DR-HLD-TEC. |
| Konvence technického výkresu | 6 | Rámeček, razítko, měřítka, značky, legenda jsou; chybí odkaz na detaily A/B, výšky v plánu stropu, revize B; kóta světlé výšky přes zkosený panel; legenda nezná černé čárkované obrysy. |
| Stavebnost a průchodnost | 5 | Výklenky postavitelné; navržená křídla DR-TEC-CAB narážejí do zkosení, stavového světla a nápisu; průchod okótovaný jen u podlahy; prostor pod roštem chybí. |
| Srozumitelnost pro autora | 6 | Účely a stavy pomáhají; list tvrdí mřížová dvířka na pantech a „výdejník“, které nejsou; souhrn světel mluví žargonem. |

Průměr: 5,5

## Musí se opravit
1. 06 – navržená křídla DR-TEC-CAB (0,5 × 2,05 m, otevřená y ±0,50 … ±1,00) zasahují do zkosení bočních stěn (u y ±1,0 už ve výšce asi 1,57 m), levé přejíždí TEC-B-F/Status_0 a zakryje D-INT-COCKPIT; zapsat do kontroly dat jako otázku pro autora a navrhnout postavitelné řešení.
2. 05–08 – „+1,70 zkosení“ je pro průřez W špatně: zkosení +1,30 … +2,10 (kit_rules W); kreslit +1,30, +2,10, +2,30 i v řezu.
3. 04, 11 – „mřížová dvířka na pantech“ / „za mřížkou“ nejsou postavené: kit_batch4 staví otevřené posuvné křídlo v kapse (mříž odstraněna 28. 9.); popsat podle postaveného dílu.
4. 13 – hustota světel z obdélníku layoutu (8,1 m²) místo postavené podlahy 1,79 × 2,40 = 4,30 m² (asi 4,7 /m²), pravidlo pro obytné místnosti; přepsat.
5. 09, 04 – rámeček detailu B přechází přes legendu a klíčový plán.

## Mělo by se opravit
1. 01, 08 – křídlo DR-HLD-TEC na x 8,20 místo v kapse TEC-B-A, v pohledu 4 chybí, v datech chybí jeho poloha.
2. 03 – průchod okótovaný jen u podlahy (ve 1,80 m jen ≈ 1,65), dveřní otvor proti kapsli neokótovaný, světlá výška přes zkosený panel.
3. 01, 13 – servisní kanál pod roštem TEC-FL-2 nikde v řezu ani kótě.
4. 02 – plán stropu bez výšek, bez Cove/Wash, nepopsané pásy a plochy; titulek „zrcadleně“ proti poznámce 5.
5. 04 – chybí detail výklenku chladiče.
6. 01, 04 – chybí oblouk otevření poklopu generátoru a obálka vysunutého reaktoru.
7. 01, 05 – odkazy 1–3 mm od sebe.
8. 03 – odkazy TEC-W-L1/R1 končí za zadní stěnou výklenku.
9. 08 – Door_0 a Reveal_0 na stejném místě, štítek Door chybí.
10. 12 – Bay_0 „světlo výdejníku“ → „světlo výklenku“.
11. 01, 03 – chybí řezové značky detailů A/B.
12. 13, 11 – žargon (MegaLights, pixel-bound, kit_rooms.py, CLAUDE.md, „tr.“, „layout“).

## Drobnosti
Revize B bez záznamu; velikosti decalů knihovní místo osazených; rámeček rivet_row_8 pod pásem Wash; štítky světel 1,3 mm; osa x relativně a y absolutně, mřížka v barvě návrhu; kóta 1,79 proti modulům 1,2 + 0,6; hloubka výklenku vnější (0,58/0,48) vs. světlá (0,55/0,45); legenda bez černých čárkovaných obrysů.

## Namátková kontrola dat
Sedí: TEC-W-L1, TEC-W-R2, TEC-B-A + DR-HLD-TEC, TEC-B-F + DR-TEC-CAB, TEC-C-1/C-2 Linear, TEC-FL-2/Channel_0, výklenky POWER/SHIELD/COOLER, kontrola dat POWER/SHIELD, světla L1, Emitter_0, Status_0 (v dráze křídla), D-INT-COCKPIT, plate_reactor, počty, kapsle.
Nesedí: úroveň zkosení, hustota světel, přístup k reaktoru, účel Bay_0, odkaz TEC-W-L1 v R1, TEC-B-A/Door_0 v pohledu; křídla DR-TEC-CAB: data sedí, návrh nepostavitelný.
