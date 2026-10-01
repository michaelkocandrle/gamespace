# Recenze: nábytek kajuty z kitu (Wayfarer), 30. 9. 2026

Autor zadal nábytek kajuty jako díly kitu. Postup je stejný jako u dávek kitu: katalog, showroom, kritik. Díly jsou
lůžko s policemi a lampičkou, skříň na skafandr a zbraň, hygienická buňka a výdejník jídla a vody (`kit_parts.json`
dávka 6, `Tools/Kit/kit_furniture.py`). Posuzuje se z první osoby (oko 1,65 m), snímky z rychlé smyčky
(`Shots.ps1 -Preset wayfarer_cabin_furniture -Editor`, 1920×1080). Stylový záměr je „udržovaná pracovní loď“.

- Zadání a páry: `2026-09-30_cabin_furniture/review_round1.json` až `review_round3.json`, `review_verify.json`
- Listy a brief: `round1/`, `round2/`, `round3/`, `verify/`
- Výstupy kritika: `round1/critic.md`, `round2/critic.md`, `round3/critic.md`, `verify/critic.md`
- Důkazy: `2026-09-30_cabin_furniture/evidence/`
- Finální snímky ze zabalené hry: `shots:20260930_210830_wayfarer_cabin_furniture` (1920×1080, 60–65 FPS
  v kajutě)

## Co nábytek dostal (konečný stav)

- **Lůžko** `Furniture_Bunk21L_A` (11,3 tis. trojúhelníků z 15 tis.):
  - bočnice s oranžovou hranou po celém profilu;
  - matrace ze tří polštářů, polštář, opěrky. Polštáře jsou měkké plochy (nový `kit_geo.Part.mesh`, pomocník
    `pad`): zaoblené hrany, vyboulená pole, švy jako prohlubně, knoflíky v důlcích, lemovka, polštář s promáčknutím;
  - deka se záhybem, přesahem a lemem;
  - dvě police na konzolách, s přepážkami a zábradlím na hranatých sloupcích;
  - lampička (15 cd, kužel 75°) s vypínačem, pod policí dvě krátká svítidla v pouzdrech;
  - v podstavci nasávání podpory života se štítkem LIFE SUPPORT.
- **Skříň** `Furniture_Locker10L_A`:
  - dveře skafandru s oknem a spodním polem zapuštěným 12 mm v plochém rámu, s větracími štěrbinami;
  - za oknem skafandr (helma, hledí, oranžový krční kroužek, ramena, hrudní modul, opasek, hadice) pod bodovým
    světlem;
  - průběžné panty po celé výšce obou dveří;
  - dveře zbraně se zámkem a oranžovou pákou na čepu;
  - šuplík na boty se zapuštěným polem, štěrbinami a oranžovým úchopem;
  - šablonový nápis SUIT · ARMS.
- **Hygienická buňka** `Furniture_Hygiene15L_A`:
  - boky podle zkosení obložení, rozdělené spárami, se soklovou lištou;
  - na boku servisní poklop filtru odsávání;
  - posuvné dveře ze tří polí (12 mm nad tělem dveří, mezery 2 cm) se šrafovaným pruhem na hraně posuvu, horní
    vedení a práh s drážkou;
  - nad dveřmi světlo obsazenosti v pouzdru, vedle displej obsazenosti a mřížka;
  - na střeše ventilátor s potrubím do stropu.
- **Výdejník** `Furniture_Food16L_A`:
  - chlazená skříňka s panty a štěrbinami, zásuvka na příděly;
  - pult vysunutý 10 cm s oblou gumovou hranou;
  - výdejní box v krémovém panelu ze tří polí se šrouby;
  - displej s popisky tlačítek (WATER · CHILL · RATION);
  - horní dvířka s panty a západkami;
  - pod ním sklopné sedátko se závěsem, konzolami a oranžovou pojistkou.
- **Podlaha kajuty** `Floor_Plate12L38_A`: protiskluzové pruhy z tmavé žebrované gumy (pruh trim sheetu
  `rubber_ribbed`), 6 cm široké.
- Kontroly:
  - `test_ship_geometry.py Wayfarer` PASS;
  - `kit_clash.py -- Wayfarer Furniture_` hlásí jen dotyky s podlahou a konzoly výdejníku zapuštěné do obložení
    (obojí záměr).

## Kolo 1 – FAIL

Skóre: silueta 5, detail 4, materiály 4, decaly 7, světlo 5, čitelnost 8, geometrie 7, soulad 6.
Plný výstup: `round1/critic.md`.

1. **Plastové čalounění (musí se opravit) – opraveno.** Tón ztmaven do šedé khaki, drsnost 0,92 bez lesku. Přibyly
   švy a knoflíky prošití. Kolo 2 ho dál četlo jako vinyl, pokračovalo se v kolech 2 a 3.
2. **Světlá jednolitá podlaha (musí se opravit) – opraveno.** Pruhy v uličce jsou 20 cm od sebe místo 11 cm (ulička
   četla jako jedna světlá deska). Tmavá guma přibyla v kole 2, žebrování v kole 3.
3. **Hladké dveře buňky (musí se opravit) – opraveno.** Dveře dostaly dvě stínové spáry, oranžový pruh na hraně, madlo
   na podložce, horní vedení a drážku v prahu. V kole 3 dveře ze tří polí, viz tam.
4. **Přepálené světlo ve výdejním boxu (musí se opravit) – opraveno.** Zdroj je tlumený teplý pruh schovaný pod
   stříškou boxu. Bodové světlo má 0,6 cd a svítí na trysku a mřížku.
5. **Krabicový výdejník (musí se opravit) – opraveno.**
   - Box je zapuštěný do krémového panelu s oranžovým rámem a šrouby, s odkapávací mřížkou.
   - Dvířka mají západky a jsou rozdělená sloupkem.
   - V kole 2 přibylo vlastní pouzdro výdejníku 5 cm před dvířky.
6. **Lampička nesvítí (musí se opravit) – opraveno.** Lampička má patku, rameno, kulatou hlavu se svítící čočkou
   a bodové světlo na polštář.
7. **Skříň bez hloubky (doporučeno) – opraveno.**
   - Rám je 2,6 cm hluboký a dveře sedí 1,6 cm za ním.
   - Páka zbraní má podložku, tělo a čep, zámek je modul s vložkou.
   - Šuplík má zapuštěný úchop.
   - Prázdné okno opravilo kolo 2.
8. **Černé mezery nad nábytkem (doporučeno) – neopraveno.**
   - Nad buňkou a skříní je vrstva stropních rozvodů: nosné profily, trubky na závěsech, kabelový žlab. Kryt nebo
     svítidlo bez účelu by bylo výplní. Důkaz: `evidence/r1_08_above_hygiene_cell_ceiling_services.jpg`.
   - Mezera mezi buňkou a skříní je 5 mm, aby se díly nedotýkaly (`kit_clash.py`).
9. **Nečitelná deka (doporučeno) – opraveno.** Deka má přehyb (válec), konec přes hranu matrace a lem.
10. **Sedátko jako polička (doporučeno) – částečně.** Kolo 2 opakovalo, že chybí závěs. Závěs, klouby a konzoly
    přibyly v kole 2.
11. **Tlačítka bez popisků (doporučeno) – částečně.** V kole 1 dostala podsvícené tečky, popisky na displeji až
    v kole 3.
12. **Nesouhlasná čísla 05 / 06 (doporučeno) – opraveno.** Decal sekce 06 je posunutý z výklenku lůžka.
13. **Madla skříňky u hlavy lůžka a tmavý kvádr (doporučeno) – neopraveno.**
    - Jde o schválený modul obložení `Wall_HullLiner12L_S`: nástěnná skříňka s madly a rozvodná skříňka se svodem
      kabelů.
    - Autor ho schválil v minulém kroku (recenze `2026-09-30_cabin_liner.md`, kolo 2, bod 6).
    - Důkaz: `evidence/r1_13_liner_locker_and_junction_box.jpg`.
14. **Mléčně hnědá buňka (doporučeno) – opraveno.** Buňka je v sekundárním grafitu, rámy a sloupky v konstrukčním kovu.
15. **Ploché světlo (doporučeno) – opraveno.** Pod policí je teplý pás (obdélníkové světlo po délce lišty). Svítí
    lampička a box výdejníku, strop kajuty zůstal podle schváleného obložení.

## Kolo 2 – FAIL

Skóre: silueta 5, detail 5, materiály 4, decaly 6, světlo 6, čitelnost 7, geometrie 5, soulad 6.
Plný výstup: `round2/critic.md`.

1. **Okno skříně je černá díra (musí se opravit) – opraveno.** Uvnitř je skafandr na držáku a nahoře tlumený pruh se
   světlem. Kolo 3 četlo obsah jako neurčitý tvar, dál viz kolo 3.
2. **Čalounění je plast (musí se opravit) – opraveno.**
   - Normálová mapa tkaniny `T_Kit_Fabric_N` (`Tools/Kit/kit_fabric_normal.py`, plátnová vazba s vlákny, dlaždice
     2 cm).
   - Lemovka na hranách matrace a polštáře, švy na opěrkách.
   - Deka má převis a lem.
3. **Nábytek jsou ploché desky (musí se opravit) – opraveno.**
   - Výdejník je vlastní pouzdro 5 cm před dvířky se silným oranžovým rámem. Pult je 4 cm deska s gumovou hranou.
   - Zásuvky mají zapuštěné úchopy s oranžovým vnitřkem a gumové nárazníky.
   - Panty mají 11 mm.
   - Rám dveří buňky je hlubší.
4. **Lampička je bílý válec (musí se opravit) – opraveno.** Hlava je grafitová, čočka v oranžovém prstenci, kloub
   u patky. Světlo míří na polštář: 60 cd přepálilo polštář, zůstalo 30 cd.
5. **Sedátko visí bez závěsu (musí se opravit) – opraveno.** Sedátko má lištu závěsu na zadní desce, klouby, dvě
   trojúhelníkové konzoly a gumovou hranu. Nad ním je tlumený pruh pod výdejníkem se světlem.
6. **Jeden matný materiál (musí se opravit) – opraveno.** Rozlišitelné rodiny materiálů:
   - lakovaný panel (primární a sekundární grafit);
   - konstrukční kov na bocích výdejníku, rámech, pultu a sloupcích (světlejší, `import_kit` ×1,25 / drsnost 0,42);
   - guma na hranách a nárazníkách;
   - látka.
7. **Světlé pruhy podlahy (doporučeno) – opraveno.** Pruhy jsou z tmavé gumy.
8. **Malé štítky (doporučeno) – částečně.**
   - Štítky jsou větší (14 × 7 cm). V kole 3 přešly na šablonový nápis, viz tam.
   - Výstražné štítky u sedátka a trysky nepřidávám: pitná voda ani sedátko ve 45 cm nejsou riziko, štítek by byl
     ozdobou bez účelu.
9. **Štítek LIFE SUPPORT na holé stěně (doporučeno) – opraveno.** Štítek je na podstavci lůžka vedle mřížky nasávání.
10. **Přepal pod policí (doporučeno) – opraveno.** Zdroj je obdélníkové světlo po celé délce difuzoru v pouzdře
    (2,5 cd).
11. **Potrubí ventilátoru nečitelné (doporučeno) – opraveno.** Potrubí je z kovu s tmavými objímkami. Kolo 3 ho
    zmínilo znovu, viz tam.
12. **Šuplík na boty bez madla (doporučeno) – opraveno.** Šuplík má zapuštěný úchop s oranžovým vnitřkem po šířce.

## Kolo 3 – FAIL (poslední počítané)

Skóre: silueta 6, detail 5, materiály 5, decaly 6, světlo 6, čitelnost 7, geometrie 7, soulad 7.
Plný výstup: `round3/critic.md`.

1. **Hladké krabice bez vrstvení (musí se opravit) – opraveno.**
   - Dveře skříně (spodní pole dveří skafandru), šuplík na boty a dvířka výdejníku mají vnitřní pole zapuštěné
     12 mm za plochým rámem se strmým schodem. Ve `kit_geo.box` je nově trojice `inset=(okraj, hloubka, schod)`.
     Dvojice měla šikmý okraj přes celou šířku a kování na něm plavalo: geometrická kontrola našla chladicí LED
     1 cm nad plochou.
   - Panty na chlazené skříňce a horních dvířkách, západka u dveří skafandru, tlačné západky na horních dvířkách.
   - Větrací štěrbiny na dveřích skafandru, chlazené skříňce a šuplíku.
   - Boky buňky mají spáry, soklovou lištu a servisní poklop.
2. **Čalounění jako hladký vinyl (musí se opravit) – opraveno.** Polštáře matrace, opěrky, polštář a sedátko jsou
   měkké plochy místo krabic se zaoblením:
   - každé pole mezi švy je vyboulené;
   - švy jsou prohlubně, na křížení je důlek s knoflíkem;
   - polštář je promáčknutý;
   - `pad` v `kit_furniture.py`, sdílené vrcholy, hladké stínování.
3. **Přepálená skvrna na polštáři, rovnoměrný pás (musí se opravit) – opraveno.** Lampička má 15 cd s kuželem 75°.
   Pod policí jsou dvě svítidla 0,65 m v pouzdrech po 0,9 cd místo jednoho pásu 1,8 m s 2,5 cd.
4. **Krémový panel, pult, sedátko v díře (musí se opravit) – opraveno.**
   - Panel má tři pole se spárou a šrouby v rohách a štítek servisního pole. Otěr je jen kolem tlačítek a pod boxem.
   - Pult je vysunutý na 10 cm, s gumovou oblou hranou.
   - Zadní deska sedátka je ve světlejším sekundárním grafitu. Světlo sedátka je před ním: osvětlí opěrku a desku,
     sedák dostane světlo jen šikmo. Sedátko má oranžovou pojistku sklopení.
5. **Dveře buňky jako jedna deska (musí se opravit) – opraveno.**
   - Tři pole s 12 mm mezerami na těle dveří.
   - Šrafovaný pruh na hraně posuvu (pruh `hazard` trim sheetu).
   - Horní vedení 3 cm s drážkou, práh s drážkou před dveřmi.
   - Světlo obsazenosti v pouzdru na nadpraží (studené, sedí k VACANT na displeji).
6. **Nečitelné drobné texty, štítky jako samolepky (doporučeno) – opraveno.**
   - SUIT · ARMS, HYGIENE a GALLEY jsou šablonové nápisy jako označení místností: název, linka, jeden řádek
     poloviční výšky (`generate_interior_decals.stencil`).
   - HYGIENE je menší (20 × 10 cm). Při 28 cm přesahoval na rohový sloupek: nápis „H|YGIENE“, list 06.
   - Tlačítka výdejníku mají popisky na spodním okraji displeje (WATER, CHILL, RATION se šipkami nad tlačítky).
7. **Neurčitý obsah okna skříně (doporučeno) – opraveno.**
   - Okno sahá výš, helma byla nad jeho horní hranou.
   - Skafandr je ve světlé skořepině: kulová helma, tmavé hledí, oranžový krční kroužek, ramena, paže, hrudní modul.
   - Nad skafandrem je bodové světlo 3 cd.
8. **Holé police (doporučeno) – opraveno.**
   - Tři trojúhelníkové konzoly do zadní desky; ta nově začíná v 1,12 m, aby na ní seděly i konzoly spodní police.
   - Dvě přepážky dělí každou polici na tři části.
   - Zábradlí je silnější, na hranatých sloupcích.
9. **Oranžová tyč končí ve vzduchu (doporučeno) – opraveno.** Byl to oranžový pruh na čele bočnice, končil tam, kde se
   bočnice lomí dozadu. Teď běží po čele, po šikmině a po sloupku výklenku.
10. **Nečitelné potrubí ventilátoru (doporučeno) – neopraveno.**
    - Potrubí vede ze střechy buňky do stropu (0,53 m od zadní hrany).
    - Z uličky ho zakrývá hrana střechy buňky (2,05 m) a nosné profily stropních rozvodů ve 2,09 m (kolem 0,75–1,0 m
      od zadní hrany; ventilátor se od nich musel odsunout, `kit_clash.py`). Posunout ho blíž k uličce nejde.
    - Z první osoby buňka nekončí „víkem bez napojení“: nad ní hned začínají stropní rozvody (důkaz k bodu 8
      z kola 1).
    - Důkaz, že potrubí existuje (záběr nad výdejníkem, ne z očí): `evidence/r3_10_fan_and_duct_over_cell.jpg`.
11. **Plochá podlaha (doporučeno) – opraveno.**
    - Pruhy jsou z trim sheetu `rubber_ribbed`: tmavá guma s žebry napříč, normála, matná, 6 cm široká.
    - Lem u nábytku tvoří jeho zapuštěný sokl se studeným proužkem (lůžko, skříň) a kopací plechy buňky.
      Šrouby v rozích desek podlaha má.
12. **Tmavá hmota u pravého okraje listu 01 (doporučeno) – opraveno.** Je to zadní bok hygienické buňky. Dostal spáry,
    soklovou lištu a v úrovni očí servisní poklop filtru odsávání: rám, víko, šrouby, oranžový úchop, štítek.
13. **Jiné čalounění sedátka (doporučeno) – opraveno.**
    - Sedátko má od začátku stejný materiál `Kit_Cushion` jako lůžko.
    - Krémově ho dělalo světlo 1,2 cd 20 cm nad ním. Teď je 0,35 cd před ním.
    - Sedák má stejná vyboulená pole a šev jako matrace.

## Ověřovací kolo (body 1–9, 11–13 z kola 3) – FAIL (body 2 a 5 částečně)

Skóre: silueta 7, detail 6, materiály 6, decaly 7, světlo 7, čitelnost 8, geometrie 8, soulad 7.
Plný výstup: `verify/critic.md`. Snímky `shots:20260930_203904_wayfarer_cabin_furniture`.

- **Opravené:** 1 (vrstvení), 6 (štítky), 7 (skafandr), 9 (oranžová hrana), 12 (bok buňky).
- **Částečně:** 2 (polštář hranatý, opěrky hladké), 3 (dvě svítidla nerozeznatelná, lampička viditelně nesvítí),
  4 (chybí otěr, prázdné střední pole), 5 (pole dveří jen rýhy, světlo obsazenosti není vidět), 8 (sloupky jako
  kolíky, konzoly nevidět), 11 (žebrování nevidět), 13 (sedátko světlejší než matrace).
- Nové doporučené: 8 (skafandr jako hladký panák), 9 (panty skříně jen tušené).

### Po ověřovacím kole (levné body, jen snímky před/po, bez dalšího kola kritika)

Porovnání: `after_verify/03_berth.jpg`, `05_locker.jpg`, `06_hygiene.jpg`, `07_galley.jpg` (vlevo ověřovací kolo,
vpravo `shots:20260930_205637_wayfarer_cabin_furniture`).

- **Bod 2 – opraveno.** Opěrky mají vyboulená pole 2,2 cm, šev napříč s knoflíky, švy 8 mm hluboké. Polštář má
  promáčknutí 4 cm. Sedák výraznější vyboulení.
- **Bod 5 – opraveno.** Pole dveří stojí 12 mm nad tělem dveří s mezerami 2 cm, střední pole je v primárním grafitu.
  Pouzdro světla obsazenosti je 24 cm široké. Snímek buňky má širší záběr (FOV 95), takže je vidět nadpraží se
  světlem. Na listu 06 předtím chybělo, protože horní okraj záběru byl pod nadpražím.
- **Bod 8 – opraveno.** Konzoly mají 17 × 13 cm a 14 mm, sloupky 18 mm.
- **Nový bod 8 (skafandr) – opraveno.** Opasek a dvě hadice podpory života od hrudního modulu ke krčnímu kroužku.
- **Nový bod 9 (panty) – opraveno.** Průběžné panty po celé výšce obou dveří skříně.
- **Bod 13 – částečně.** Světlo sedátka má 0,2 cd. Sedák je pořád světlejší než matrace. Materiál je stejný:
  sedák je vodorovná plocha 30 cm pod svítícím pruhem a kamera se na něj dívá shora, matrace je ve stínu police.
- **Bod 4 – částečně.**
  - Karty otěru kolem tlačítek a pod boxem mají plnou sílu, ale na krémovém panelu ze snímku skoro nejsou vidět.
  - Štítek servisního pole je větší, ale světlý nápis na krémové ploše nečte. Tmavá varianta štítků kitu zatím
    neexistuje.
- **Bod 3 – neopraveno.** Čočka lampičky míří na polštář, z uličky na ni nevidíš. Svítí jen světlo na polštáři,
  jako u skutečné čtecí lampičky. Dvě svítidla pod policí jsou vidět zblízka (list 04). Ze střední vzdálenosti
  splývá jejich světlo na opěrkách, a to je záměr (tlumené světlo, ne dva body).
- **Bod 11 – neopraveno.** Žebra pruhu `rubber_ribbed` mají rozteč ~1 cm. Z výšky očí na 2–4 m jsou menší než
  pixel, zblízka vidět jsou. Pruhy jsou tmavé a matné, což bylo jádro výtky z kola 2.

### Otevřené body (předávám s nimi)

1. Otěr a tmavé štítky na krémovém panelu výdejníku (štítky kitu jsou světlé, na krémové nečtou).
2. Sedák výdejníku vypadá světlejší než matrace (stejný materiál, jiné světlo).
3. Žebrování gumových pruhů podlahy je vidět jen zblízka.
4. Lampička: z uličky není vidět svítící čočka, jen světlo na polštáři.
5. Potrubí ventilátoru buňky je z uličky schované za stropními rozvody (kolo 3, bod 10).
6. Kritik ve všech kolech drží detail a materiály kolem 5–6. Podle zkušenosti z kokpitu jde o systémovou vrstvu:
   odrazy kovu (Lumen reflections v interiéru jsou vypnuté kvůli výkonu), variace drsnosti, drobné popisky.
   Patří do kroku vzhledu materiálů a optimalizace, ne k dalšímu lokálnímu ladění nábytku.
