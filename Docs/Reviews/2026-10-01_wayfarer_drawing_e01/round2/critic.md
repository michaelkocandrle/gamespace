# Verdikt: FAIL

První dojem: Řemeslně velmi slušný list – čistá hierarchie čar, stavy prvků jasně odlišené, data sedí na centimetry – ale navržené desky překrývají postavené prvky na plášti a list to sám nehlásí, detail A má zkřížené odkazy a tabulky jsou na A0 pod čitelnou velikostí písma.

| Kategorie | Skóre | Proč |
| --- | --- | --- |
| 1. Čitelnost | 6 | Pohledy A/B a legenda jsou čitelné, ale v detailu A se kříží vějíře odkazových čar, v pohledu B končí odkazy různých prvků 1 cm od sebe (D-NAME-R / G-VT-02 ×, F-GRILLE-01 + / D-H-42 ×), tabulky a kontrola dat mají písmo ≈ 2 mm a několik buněk je useknutých „…". |
| 2. Úplnost proti zadání | 8 | Všechno ze zadání na listu je (desky, zóny se šrafami a legendou, F s ID, světla typ/barva/intenzita, decaly s knihovnou a sloupcem „čte", stavy, kóty, detail 1:20, řez 1:5, koncept, 8× RCS); chybí jen kontrola orientace decalů na levoboku (list je 1/1) a skutečné výšky pásů v metrech. |
| 3. Soulad s daty | 8 | 20 namátkově ověřených prvků sedí polohou, stavem i počtem, otisky dat v razítku souhlasí s E01.json; mínus za dvojí a protichůdný řádek D-H-55 v KONTROLE DAT, nehlášený G-HTL-01 za křídlem a useknuté důvody změn. |
| 4. Konvence technického výkresu | 7 | Rámeček se zónami, razítko, měřítka, úrovně, odkaz na detail i řez, konvence skrytých hran – vše je; kazí to křížení odkazů, kóta „4,90" bez popisu, úroveň „+3,30 hřbet" (je to špička ploutve), řez bez spojovacího prvku a skóre kritika v revizním řádku. |
| 5. Návrh povrchu (B + C) | 5 | Rozvržení pásů K/L/U/S, žeber na každé příčce, podélníků a materiálů odpovídá B + C a konstrukčně drží; ale desky 30/40 mm nad pláštěm (řez R1) pohřbí postavené světelné pásy, lišty G-SP a nově přesunutý konektor, oranžový pruh skončil v mezeře rámu a tmavé nápisy na gunmetal rámu. |
| 6. Srozumitelnost pro autora | 7 | Účely a důvody česky, legenda stavů, fotky konceptu, tabulka změn s důvody – autor pozná, co se staví a proč; brzdí ho useknuté důvody, abstraktní definice pásů zlomkem výšky průřezu a drobné písmo tabulek. |

Průměr: 6,8 (práh PASS nesplněn: kategorie 5 pod 6 a jedna výtka „musí se opravit")

## Musí se opravit

1. **Výřezy 02–03 (pohled A), 05–06 (pohled B), 08 (řez R1), 11 (KONTROLA DAT) – navržené desky překrývají postavené prvky na plášti a list to nehlásí.** Řez R1 sám ukazuje desku XK-PLATE 30 mm (XK-PLATE-H 40 mm) nad pláštěm P-HULL. Na plášti přitom sedí postavená geometrie, která není v `panels.cut`: L-HULL-RUN-LOW (z 0,35, x 7,2–16,6 → uvnitř pásu L, desky L06–L13), L-HULL-RUN-CANOPY (z 1,62, x 15,4–18,9 → pás U, U13–U15), G-SP-01/02 (z 0,3 → L04/L05) a F-CONN-01 v nové poloze z 0,75 (→ deska L11). KONTROLA DAT hlásí jen skrytí za křídlem/gondolou, průnik s navrženými deskami ne. – Jak to má být: každý postavený prvek „z boku" ležící v ploše desky P-S buď do `panels.cut` (výřez v desce s okrajem 40 mm jako u šachet) nebo v návrhu zvednout na líc desky; v pohledu A výřezy v deskách nakreslit; do KONTROLY DAT přidat automatický řádek „prvek × deska P-S-…" pro každý průnik.

## Mělo by se opravit

1. Výřez 07 (detail A) a 05 (pohled B) – křížení odkazových čar (vějíře z dolní řady u zadního krytu, z horní řady u x 3,3–4,3); v pohledu B končí odkaz D-NAME-R ~1 cm od konce odkazu G-VT-02 ×, konec D-H-42 × těsně pod koncem F-GRILLE-01 +. Odkazy se nesmí křížit, v hustých místech dvě řady nebo lomený odkaz; u překrytých prvků vést odkaz decalu na okraj jeho rámečku.
2. Výřezy 08–11 – písmo tabulek, legendy a kontroly dat ≈ 2 mm, pod ISO 3098 (2,5 mm); pod tabulkami je volné místo. Zvětšit na 2,5–3,5 mm.
3. Výřezy 09–10 – useknuté buňky „…" (F-RCS-01, F-CONN-01, F-GRILLE-01, D-H-55, D-H-58, D-LOGO-R). Zalamovat na libovolný počet řádků nebo zkrátit `why` v datech.
4. Výřezy 02–03 – oranžový pruh Z-B-03 po změně leží v mezeře rámu mezi pásy L a U (na gunmetal rámu pod lícem desek); v konceptech B i C vede pruh přes pláty. Položit na desky, nebo výslovně napsat, že je záměrně v rámu.
5. Výřezy 05–06 – tmavé servisní nápisy na tmavém rámu po změně P-HULL na gunmetal: D-H-59 (deska U07 vypadla kvůli F-GRILLE-01), D-H-58, D-H-29. Světlý inkoust (xstl_*) nebo posunout na desku; do KONTROLY DAT řádek „nápis × podklad".
6. Výřez 11 – KONTROLA DAT: D-H-55 dvakrát a protichůdně; chybí G-HTL-01 (dolní polovina za křídlem). Sloučit, doplnit.
7. Výřez 10 – kontrola orientace „na obou bocích": list je jen pravobok, D-*-L nikde. Malý proužek levoboku nebo odkaz na list E-02.

## Drobnosti

1. Výřezy 01 a 04 – úroveň „+3,30 hřbet" je špička ploutve (hřbet ≈ 2,9).
2. Výřez 03 – svislá kóta „4,90" bez popisu.
3. Výřez 08 – řez R1 bez šroubu; dokreslit šroub a přidat řez R2 plátem XK-PLATE-H.
4. Výřez 11 – revizní řádek nese výsledek kritika; „Kontroloval" bez data.
5. Výřez 08 – pásy jen zlomkem výšky průřezu; uvést i z na příčce 11,6.
6. Výřez 10 – D-HAZARDEXHAUST-R „x 0,1 z 1,2" neříká, že leží na gondole.
7. Výřez 05 – mezery mezi popisky horní řady menší než výška písma.

## Namátková kontrola dat
20 prvků (F-RCS-01/02/05/06/09/12/13, F-CONN-01, D-LOGO-R, D-H-29/55/58, F-GRILLE-01/02, G-VT-01/02/03, D-H-42, P-B-02…15, Z-B-03, G-HT-01, G-SN-02, R-B-01, detail A, světla, otisky dat, počty) – vše sedí polohou, stavem i počtem; F-CONN-01 a L-HULL-RUN-* sedí polohou, ale leží v ploše navržených desek (Musí 1).
