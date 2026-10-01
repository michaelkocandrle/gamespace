# Ověření: 14 z 15 opraveno

| Bod | Stav | Kde / poznámka |
|---|---|---|
| M1 Stav DR-TEC-CAB v tabulce | opraveno | List 09, tabulka NÁBYTEK, DVEŘE, KOMPONENTY, řádek DR-TEC-CAB: stav „otvor postaven, křídlo návrh“ (modře) je celý, zalomený na dva řádky. |
| M2 Křídla DR-TEC-CAB modře čárkovaně v zasunuté poloze, strana líce | opraveno | List 01 (půdorys), levý okraj u přepážky CAB-B-A: dvě tenké modré čárkované obdélníky (tloušťka ~3 cm) za lícem na straně chodby, u y 0,5…1,0 a −1,0…−0,5, plus modré šipky od středu otvoru k oběma stranám. List 07 (pohled 4): dva modré čárkované obdélníky 0,5 × 2,05 m po obou stranách otvoru, štítek „DR-TEC-CAB křídlo + (návrh, po líci ze strany chodby)“. Strana je řečena i v tabulce na listu 09. V půdorysu samotném je strana jen graficky, bez textu. |
| M3 Kótovací řady v půdorysu, v řezu šířka místnosti a trupu | opraveno | List 01: nahoře 4,79 „líc přepážek“ a řada 2,30 / 2,10 / 0,39, dole 0,32 / 0,95 / 1,46 / 0,17 / 1,60 / 0,29 = 4,79 (sedí s daty), vlevo i vpravo 1,40 / 1,00 / 1,40 = 3,80 „líc obložení“, dveře buňky 0,80. List 03: „3,80 mezi líci obložení“, „4,67 trup vně (bez křídel a gondol)“, výšky +3,11 / +2,30 / ±0,00 / −0,63, světlá výška 2,30, průchod 1,66. |
| M4 D-INT-SEC06 popis podle polohy z dat | opraveno | List 10: „číslo úseku lodi 06 na obložení u přední přepážky (CAB-W-L5, 0,2 m za koncem lůžka)“; list 04: decal na CAB-W-L5; list 11, KONTROLA DAT: rozpor s komentářem setupu uveden, rozhodnutí na autorovi. |
| M5 Vzorec intenzity s ×0,5 pro Wash | opraveno | List 11: „cd dílu × Wash ×0,5 (kit_rooms) × zóna místnosti ×0,6 × Wash ×0,6 navíc × hra ×1,1 (např. Wash 12L: 6 × 0,5 × 0,6 × 0,6 × 1,1 = 1,19 cd)“ – příklad sedí s tabulkou. Základní cd dílů kitu na listu nejsou, dopočítat lze jen přes uvedený příklad. |
| M6 Sloupec umístění v rozpisu nábytku | opraveno | List 09: sloupec „umístění (m)“, např. CAB-U-BUNK „x 13,75, y 1,80, na podlaze, čelem k pravoboku (střed zadní hrany)“; sedí s `run_parts`. |
| M7 „před stěnou“ v pohledech 2 a 4 | opraveno | List 05 a 07: šedé štítky „… (před stěnou)“. |
| M8 Strop: žebřík, potrubí, žebra, římsa pojmenované | opraveno | List 02: štítky žebříku, římsy, potrubí a žebra. Viz ale nová chyba 2. |
| D1 Odkaz CAB-M-LIFESUP neprotíná „pod podlahou“ | opraveno | List 01 a 03. |
| D2 Pohled 3: štítek CAB-W-R1 nepřeškrtnutý | **neopraveno** | List 06: svislé odkazy D-INT-SUIT a CAB-U-LOCKER/ck_lock jdou přes pravou část štítku „CAB-W-R1“ i podtitulek. Oprava: odkazy vést vpravo od štítku, nebo štítek posunout. |
| D3 Řádky L-FIX-15 a karty špíny neuříznuté | opraveno | List 10. Součty sedí (42 světel, 28 decalů, 43 karet). |
| D4 Prázdný prostor pod podlahou v řezu vysvětlen | opraveno | List 03 a 11. |
| D5 Legenda: výplň trupu / tmavé vrstvy, „cd“, „MegaLights“ | opraveno | List 08; MegaLights vysvětluje až souhrn na listu 11, v legendě samotné není. |
| D6 Výškové úrovně u každého pohledu | opraveno | Listy 04–07. |
| D7 Mřížka kitu 0,3 m viditelná | opraveno | List 01; na výřezu rozeznatelná, na celkovém náhledu zaniká. |

## Nové chyby z oprav

1. **Kóty přeškrtnuté odkazy štítků nábytku** – list 01, dolní řada: 0,95, 1,46 a 1,60 leží na svislých odkazech CAB-U-LOCKER, CAB-U-HYGIENE a CAB-U-GALLEY; nahoře 2,10 a CAB-U-BUNK. Doporučeno: posunout text kóty nebo odkazy vést k okraji prvku.
2. **Odkazy stropu splývají v jednu čáru** – list 02: „kabelový žebřík“ (shora) a „dvojice potrubí“ (zdola) na stejném x; v řezu (list 03) CAB-C-2 a CAB-FL-2 rovněž. Doporučeno: odsadit.
3. **Štítek křídel v jednotném čísle** – list 07: „DR-TEC-CAB křídlo“ popisuje dvě křídla. Drobnost.
4. **Hmoty před stěnou nejsou rozlišitelné** – list 05 vpravo (výdejník před buňkou), list 07 vlevo (skříň před buňkou). Doporučeno: silnější obrys nebo světlejší výplň.
5. **Skryté decaly kresleny plně** – list 04: štítky CAB-W-L3/maker a CAB-W-L4/maker plnou výplní přes polici lůžka. Drobnost.

## Skóre kategorií po opravách (1–10)

- **Čitelnost: 7** – kóty a popisy úplné, ale nové kóty leží na odkazech, odkazy ve stropu a řezu splývají, CAB-W-R1 přeškrtnutý.
- **Úplnost: 9** – chybí jen základní cd dílů pro plné dopočítání tabulky světel.
- **Soulad s daty: 8** – polohy sedí s daty, rozpory v kontrole dat; šířka trupu 4,67 je z modelu, layout má 4,60.
- **Konvence: 7** – kóty se kříží s odkazy a skryté decaly jsou kresleny plně.
- **Stavebnost: 8** – hmoty před stěnou v pohledech 2 a 4 nejde z výkresu odečíst.
- **Srozumitelnost: 8** – MegaLights jen v souhrnu, ne v legendě.
