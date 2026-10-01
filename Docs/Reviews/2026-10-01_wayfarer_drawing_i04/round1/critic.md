# Verdikt: PASS

První dojem: Vypadá jako skutečný stavební list z kanceláře – jeden jazyk s exteriérovými listy (rámeček, razítko, legenda, klíčový plán, odkazové čáry s ID), a hlavně kreslený z dat, takže polohy a ID sedí; co chybí, jsou kóty a pár dotažení v tabulkách.

| Kategorie | Skóre | Proč |
|---|---|---|
| Čitelnost | 7 | Hierarchie písma a čar je jasná (řez tlustě, obrys za řezem tence, návrh modře), ID štítky čitelné; sráží to oříznuté buňky tabulek („otvor postaven, …“), několik křížících se odkazových čar a mřížka 0,3 m na monitoru skoro neviditelná. |
| Úplnost proti zadání | 8 | Všech 8 bodů zadání na listu je (půdorys, 4 rozvinuté stěny, strop, řez s kapslí, decaly, světla s výkonem, rozpisy, účely); chybí jen nakreslená navržená křídla DR-TEC-CAB v pohledu 4, polohy nábytku v jeho rozpisu a popis žlabů/potrubí ve stropním plánu. |
| Soulad s daty | 7 | 17 namátkových kontrol poloh a počtů sedí na centimetry; nesedí popis D-INT-SEC06 („nad lůžkem“, ve skutečnosti 0,2 m za jeho koncem na CAB-W-L5), vzorec intenzity v souhrnu nereprodukuje hodnoty Wash v tabulce a stav DR-TEC-CAB je v tabulce uříznutý. |
| Konvence technického výkresu | 6 | Rámeček, razítko, měřítko, značky řezu a pohledů, legenda, klíčový plán a stavy prvků jsou vzorné; ale v půdorysu ani v řezu není jediná kóta (jen stupnice mřížky), výškové úrovně jsou jen u stěny 1 a legenda nevysvětluje výplň trupu v řezu. |
| Stavebnost a průchodnost | 7 | Mřížka, běhy modulů s x-rozsahy, průchod 1,66 m s kapslí, světlá výška, přístup komponenty i kolize podpory života s trupem jsou doložené; nábytek má polohy jen v drobném textu kontroly dat (bez z a orientace), navržená křídla DR-TEC-CAB nemají řečeno, po které straně líce jedou, a „konstrukce pod podlahou“ je v řezu prázdná. |
| Srozumitelnost pro autora | 8 | České účely u každého dílu, barevné stavy s legendou, klíčový plán a seznam listů – autor pozná, co stojí a co je návrh; nevysvětlený zůstává žargon („cd“, „MegaLights“, „int.“) a uříznutý stav dveří. |

Průměr: 7,2 (práh dílčí krok: ≥ 6,5, žádná kategorie pod 6, žádné „musí se opravit“ – splněno)

## Musí se opravit
Žádné.

## Mělo by se opravit
1. **10_tabulky_kit_nabytek, řádek DR-TEC-CAB, sloupec „stav“** – text je uříznutý na „otvor postaven, …“; skript má „otvor postaven, křídlo návrh“. Stav prvku je jádro zadání (bod 8) – rozšířit sloupec nebo zalomit, aby se celý stav vešel.
2. **01_pudorys (levý okraj, x 10,34) a 07_steny_4 (otvor dveří)** – navržená dvě křídla DR-TEC-CAB nejsou nakreslená: v půdorysu je jen modrá čára v otvoru a šipka ↑↓ 0,14 m před lícem, v pohledu 4 nic. Doplnit modře čárkovaně obě křídla 0,5 m v zasunuté poloze a napsat, po které straně líce (kajuta/chodba) jedou – líc 3 cm + přepážka 4 cm kapsu neunese.
3. **01_pudorys + 03_rez** – chybějí kóty: délka 4,80 (líc 10,40 … 15,19), šířka 3,80 mezi líci obložení, šířky dveří 1,00 / 0,80, polohy nábytku od přepážky; v řezu šířka místnosti a trupu. Stupnice mřížky +0,0 … +4,8 je souřadnice, ne kóta. Jako vzor pro I-01 … I-09 to má mít aspoň jednu obvodovou kótovací řadu v půdorysu a jednu v řezu.
4. **11_tabulky_svetla_decaly, řádek D-INT-SEC06 + 04_steny_1 (vpravo, modul CAB-W-L5)** – účel říká „číslo úseku 06 na obložení nad lůžkem“, ale data (setup x 474 cm → layout x 14,99) i výkres ho mají v posledním modulu 0,6 m, 0,2 m za koncem lůžka (lůžko končí 14,80). Komentář v setupu („x 13,09“) je zastaralý. Buď opravit text účelu, nebo posunout decal nad lůžko – teď si autor bude hledat nápis na špatném místě.
5. **12_souhrn_svetel, řádek „Intenzita = …“** – vzorec „cd dílu × 0,6 × (stěny ×0,6) × 1,1“ dává pro Wash 12L 6 × 0,6 × 0,6 × 1,1 = 2,38 cd, tabulka má 1,19 (kit_rooms.py přidává globálně ×0,5 pro Wash). Doplnit „osvětlení stěn ×0,5 (kit_rooms) ×0,6 (zóna)“, jinak autor tabulku z hodnot kitu nedopočítá.
6. **10_tabulky_kit_nabytek, tabulka NÁBYTEK, DVEŘE, KOMPONENTY** – nemá sloupec umístění (x, y, z, orientace); polohy jsou jen v drobném textu KONTROLA DAT. Díly kitu umístění mají – nábytek má mít totéž (např. „střed zadní hrany x 13,75, y 1,80, hlava k zádi“).
7. **05_steny_2 a 07_steny_4** – velké šedé hmoty před přepážkou (vpravo buňka CAB-U-HYGIENE 2,3 m, vlevo konec lůžka; v pohledu 4 skříň + buňka vlevo a lůžko vpravo) nejsou označené a mají stejný tón jako stěna – autor je může číst jako součást přepážky. Buď je označit ID s poznámkou „před stěnou“, nebo kreslit světlejším obrysem.
8. **02_strop** – kromě ID panelů a světel není nic popsané: podélný „žebřík“ nahoře (y ≈ 1,0 m od levoboku, celá délka) a pás s oranžovými políčky dole nemají název; zadání (bod 3) chce žlaby, potrubí, poklopy pojmenované. Doplnit odkazové štítky (kabelový žlab obložení / římsa / žebro trupu) nebo to, co je nad stropem, ze stropního plánu vynechat.
9. **00_celkovy_pohled (rozhodnutí autora)** – list A0 v 1:20 má pravou dolní pětinu prázdnou a půdorys místnosti 4,8 m zabírá jen 240 mm; detail obložení (římsa 2,1–2,3 m na 04_steny_1) se slévá do pruhu čar. Pro listy jedné místnosti zvážit 1:10 na A0 nebo 1:20 na A1 – tenhle list určuje styl pro I-02 … I-05.

## Drobnosti
1. **01_pudorys (1205, 555)** – odkazová čára CAB-M-LIFESUP protíná text „pod podlahou“; posunout popisek vedle čáry.
2. **06_steny_3 (1690, 312)** – štítek „CAB-W-R1“ je přeškrtnutý odkazy D-INT-SUIT a CAB-U-LOCKER/ck_lock; **(940, 220)** se kříží odkazy D-INT-HYGIENE a CAB-U-HYGIENE/st_vent.
3. **11_tabulky_svetla_decaly** – řádek L-FIX-15 uříznutý („pás neb…“); řádek „karty špíny (43)“ uříznutý za CAB-W-L3, takže moduly L4, L5 a R1–R5 na listu chybějí a číslo 43 z listu nejde ověřit – zalomit na druhý řádek.
4. **03_rez** – pod podlahou je bílá plocha, zatímco text POD PODLAHOU A NAD STROPEM slibuje „konstrukci podlahy kitu a lodi“; napsat „nemodelováno – jen trup“ nebo konstrukci nakreslit.
5. **08_legenda** – chybí položka pro výplň trupu v řezu (tmavá vrstva nad stropem, světle šedý trup kolem místnosti) a vysvětlivka „cd = svítivost (kandela)“; „MegaLights“ v souhrnu světel je žargon bez vysvětlení.
6. **05/06/07** – výškové úrovně (+2,30, +1,70, +1,30, ±0,00) jsou jen u stěny 1; u pohledů 2 a 4 není odečitatelná výška otvoru dveří. Stačí značky ±0,00 a +2,30 u každého pohledu nebo kóta výšky otvoru.
7. **01_pudorys** – mřížka kitu 0,3 m (světle modrá tečkovaná) je na monitoru prakticky neviditelná; o stupeň tmavší nebo tenčí plnou čarou.

## Namátková kontrola dat (prvek, výkres, data, sedí/nesedí)

| Prvek | Výkres | Data | Sedí |
|---|---|---|---|
| CAB-W-L1 (Wall_HullLiner12L_E) | 01: první modul levoboku, odkaz do x ≈ 11,0; 04: mřížka sání v dolní desce; tabulka x 10,39 … 11,59, líc y 1,90 | hs wall_runs 10,39 → first part 12L_E, líc 1,9; účel „zpětné sání podpory života“ | sedí |
| CAB-U-BUNK (Furniture_Bunk21L_A) | 01: x 12,71 … 14,78, u levoboku; 04: výklenek s policemi, Berth ×2, Reading u zadního konce | run_parts střed 13,75, délka 2,10 → 12,70 … 14,80; sockets Berth ±0,575 (13,18 / 14,33 – na výkresu 13,14 / 14,32), Reading −0,91 (hlava k zádi) | sedí |
| CAB-U-HYGIENE + DR-CAB-HYG | 01: x 11,67 … 13,14, dveře kolem x 12,4, šipka zasouvání k přídi; 06: buňka s posuvným křídlem, D-INT-HYGIENE vlevo od dveří pod mřížkou | střed 12,4, dims 1,061 × 1,465 → 11,67 … 13,13; layout dveře at 12,4, šířka 0,8; design „zasouvá se k přídi“; D-INT-HYGIENE layout x 12,98 | sedí |
| CAB-U-LOCKER | 01: x 10,74 … 11,68 u pravoboku; 06: D-INT-SUIT na dvířkách (x ≈ 10,91), ck_lock, st_inspect | střed 11,195, dims 0,609 × 0,95 → 10,72 … 11,67; D-INT-SUIT layout x 10,91; manifest decal_items ck_lock, st_inspect, grime | sedí |
| CAB-U-GALLEY | 01: x 13,31 … 14,91; 06: skříňka ~0,84 … 1,83 se sedátkem pod ní, D-INT-GALLEY v levých horních dvířkách (x ≈ 14,48), Bay, Seat | střed 14,1, dims 0,683 × 1,6 × 1,65 → 13,30 … 14,90; D-INT-GALLEY layout x 14,48; sockets Bay, Seat | sedí |
| CAB-M-LIFESUP (návrh) | 01: modrý čárkovaný obdélník x 12,91 … 14,52, y 1,08 … 1,73; 03: modře pod podlahou na levoboku, roh přes čáru trupu; tabulka modře „návrh“ | layout rect 12,9 … 14,5, 1,1 … 1,75, z −0,55 … −0,05, below; design CAB-M-LIFESUP built_as „nepostavena“; kontrola „leží zčásti mimo trup“ | sedí |
| D-INT-SEC05 | 04: čtverec v horní hlavní desce CAB-W-L1, x ≈ 10,70, z ≈ 1,1 | setup (45, −187,5, −8) + offset → layout x 10,70, y 1,88, z 1,12 | sedí |
| D-INT-SEC06 | 04: vpravo v CAB-W-L5, x ≈ 14,99 (za koncem lůžka); tabulka „nad lůžkem“ | setup (474, …) → layout x 14,99; lůžko končí 14,80; komentář v setupu „x 13,09“ zastaralý | poloha sedí, popis účelu nesedí |
| D-INT-COCKPITSTAIRS / D-INT-QUARTERS | 05: nápis vlevo od otvoru (levobok při pohledu k přídi); 07: nápis vpravo od dveří (levobok při pohledu k zádi), oba ~1,5 m vysoko, 80 × 20 cm | setup → layout x 15,19 / 10,40, y +1,20 / +1,25 (levobok), z 1,50; size 10 × 40 half-extents = 20 × 80 cm | sedí |
| D-INT-STAIRHAZARD | 01: fialový pruh před otvorem do kokpitu x ≈ 15,03 … 15,16 | setup x 483 → layout 15,08 ± 0,07 („x 15,01–15,15“) | sedí |
| CAB-C-1 / CAB-C-3 světla | 02: Down uprostřed panelu, Scallop ±1,28 m od osy, Halo kroužek; CAB-C-2/4 Linear + Halo | manifest 12L38_A: Down (60, 0), Scallop (60, ±128), Halo; 12L38_C: Linear + Halo; run_parts A-C-A-C od 10,39 | sedí |
| Počty světel a režimy | SVĚTLA (42); stín 4 (Down, Linear); „i“ 22 | 10 Cove + 10 Wash + Door + 2 Status + 2 Down + 4 Halo + 4 Scallop + 2 Linear + 2 Berth + Reading + Bay + Seat + Suit + L-FIX-15 = 42; kit_rooms.py SHADOWED_SOCKETS = Linear, Down; INTERIOR_ONLY = Wash, Down, Halo, Scallop (+ Status interior_only v manifestu) = 22 | sedí |
| Intenzity (cd) | Down 171,6; Halo 2,31; Berth 0,59; Suit 1,98; Wash 12L 1,19 | 260 × 0,6 × 1,1 = 171,6; 3,5 × 0,66 = 2,31; 0,9 × 0,66 = 0,59; 3 × 0,66 = 1,98; Wash 6 × 0,5 × 0,6 × 0,6 × 1,1 = 1,19 | hodnoty sedí, vzorec na listu ×0,5 neuvádí |
| Decaly (28 + 43) | tabulka 28 řádků + karty špíny | 9 D-INT + 6 na přepážkách + 1 + 1 + 2 + 2 + 1 + 6 maker = 28; grime 4 × 7 + 1 + 2 + 1 + 1 + 5 + 5 = 43 (manifest decal_items) | sedí |
| CAB-B-A / CAB-B-F | tabulka „líc x 10,40“ / „líc x 15,19“; 07: Door světlo nad dveřmi + Status; 05: jen Status, otvor až ke stropu | run_parts 10,4 / 15,19; manifest 00L38_A sockets Door + Status, 00L38_F jen Status | sedí |
| Řez R1 | 03: „x 12,50“, popsáno CAB-W-L2, CAB-W-R2, CAB-FL-2, CAB-C-2; 01: značka R1 v x ≈ 12,51; průchod 1,66 (líc lůžka 0,92 ↔ líc buňky −0,74) | json section_x 12,5; moduly 11,59 … 12,79; 0,92 + 0,74 = 1,66 | sedí |
| DR-TEC-CAB stav | 01: modrá čára + šipka ↑↓; tabulka modře „otvor postaven, …“ | design leaf „proposed“, dvoukřídlé 2 × 0,5; skript „otvor postaven, křídlo návrh“ | stav sedí, text uříznutý |
