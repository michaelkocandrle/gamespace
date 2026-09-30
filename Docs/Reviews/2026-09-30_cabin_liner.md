# Recenze: kajuta z obložení trupu (Wayfarer, varianta B), 30. 9. 2026

Autor vybral variantu B z `Docs/Kit/cabin_plan_wayfarer.png`. Kajuta je z obložení trupu, líc na ±1,9 m, takže
schválený půdorys se nemění. Posuzuje se z první osoby (oko 1,65 m), snímky z rychlé smyčky
(`Shots.ps1 -Preset wayfarer_rooms -Editor`, 1920×1080). Nábytek je zatím dočasný (lodní kvádry, posunuté před
žebra a pod zkosení) a podlaha lodní. Obojí přijde v dalších krocích a brief to kritikovi říká.

- Zadání a páry: `2026-09-30_cabin_liner/review_round1.json`, `review_round2.json`
- Listy a brief: `2026-09-30_cabin_liner/round1/`, `round2/`
- Výstupy kritika: `round1/critic.md`, `round2/critic.md`
- Důkazy: `2026-09-30_cabin_liner/evidence/`

## Co kajuta dostala

- Stěny: `Wall_HullLiner` 10,39–15,19 m, na levoboku E-B-A-A-D, na pravoboku A-A-A-A-D. Poslední 0,6 m u kokpitu
  je nový `06L_D` s plochým soklem: trup je tam u podlahy jen 4,5 cm za lícem a zapuštěný sokl z něj vylezl
  (geometrická kontrola „penetrating“, WORKFLOW el).
- Čela přepážek:
  - vzadu `Bulkhead_Door00L38_A`;
  - vpředu nová varianta `_F`: průchod až ke stropu nad schody do kokpitu, sloupky ke stropu, trám se u nich
    zastaví (nadpraží ve 2,05 m bralo hlavu na schodech).
- Strop L38 A-C-A-C se svatozářemi, bodovkami na stěny a vrstvou rozvodů.
- Světla kajuty tlumí `kit_modules.light_scale` (0,6, wash 0,36): pod světly skladu měla p50 0,28.
- Nábytek je 5 cm před žebry a pod zkosením. Hygienická buňka má boky podle profilu obložení a střechu ve 2,05 m.

## Kolo 1 – FAIL

Skóre: silueta 5, detail 4, materiály 4, decaly 2, světlo 5, čitelnost 3, geometrie 6, soulad 5.
Plný výstup: `round1/critic.md`.

### Reakce na body

1. **Plochý světlý strop bez struktury (musí se opravit) – opraveno.**
   - Stropní panely širokých místností mají na koncích půlky T žeber (stojina 2 cm, příruba 9 cm, 8 cm hluboké).
     Na spojích modulů tak žebra stěn pokračují přes strop.
   - Ve skladu jsou stropní moduly srovnané se žebry stěn: začínají modulem 0,6 m s mřížkou.
   - Svatozáře 6 → 3,5 cd, strop už není nejsvětlejší plocha (list 04: průměr 0,17).
   - Čočka svítidla A je 2 cm pod lícem místo 5 cm za lamelami. Zblízka svítí (bod 6).
2. **Jednotvárné stěny bez madel (musí se opravit) – opraveno.**
   - Nová varianta obložení `12L_E`: vzduchová zpátečka podpory života v dolní desce (rám, tmavá komora, lamely,
     šrouby). Levobok u zadních dveří, kajuta má teď tři varianty (A, B, E) a E s B se shlukují u vstupu.
   - Madlo (oranžové, na distančních patkách) je na všech čelech přepážek pod stavovým světlem. U schodů madla
     má zábradlí.
   - Kov konstrukce a zkosení hran už obložení má (kolo 3 skladu). Působilo jako „dřevotříska“ hlavně kvůli
     přesvícení, které bod 4 řeší.
3. **Žádné čitelné nápisy (musí se opravit) – opraveno.**
   - Nové nápisy (`generate_interior_decals.py`, `Wayfarer_setup.json`):
     - CREW QUARTERS na zadním čele, na levoboku (na pravoboku ho zakrývala buňka);
     - COCKPIT se šipkou a „FLIGHT DECK · MIND THE STAIRS“ na předním čele;
     - čísla sekcí 05 a 06 na levoboku;
     - štítek LIFE SUPPORT S1 nad lůžkem (zařízení je pod ním);
     - výstražný pruh na podlaze před schody.
   - Geometrická kontrola u tří nápisů hlásila „marks nothing“: horní desky čel jsou zapuštěné a v ose podlahy
     vede spára dlaždic. Po posunu k lícům hlásila „reaches the other side“, a proto mají nápisy na čelech hloubku
     2 cm. Teď prošla.
4. **Přepálená světla bez hierarchie (musí se opravit) – opraveno.**
   - Stavové světlo: čočka 3 × 3 cm v tmavém rámečku, světlo 0,4 → 0,15 cd, emise `Kit_GlowSignal` 4 → 2.
   - Bodovky na stěny sedí 0,4 m od kraje stropu místo 0,2 m a svítí pod úhlem 31°, kužel 60°. Nepřepalují
     horní hranu zkosení.
   - Pásky žlábku jsou v tlumeném materiálu `Kit_GlowDim` jako sekundární světlo.
   - Wash stěn v kajutě je na 0,36 (kajuta 0,6 × 0,6), spodní třetiny stěn jsou tmavší.
   - Změřeno: kajuta průměr 0,15–0,21, p50 0,11–0,18, B/R 0,71–0,80, v rozsahu SC.
5. **Proporce vysoké chodby (musí se opravit) – částečně.**
   - Průřez L je daný trupem a autor ho schválil 28. 9.: svisle do 1,7 m, zkosení do 2,2 m, strop 2,3 m. Kajuta
     je 3,8 m široká a zkosení větší nedovolí, protože nad 2 m se trup zužuje.
   - Příčná žebra přes strop (bod 1) teď čtou průřez jako žebrovaný osmiúhelník. Strop nižší být nemůže:
     pod rozvody zůstává 2,13 m.
6. **Svítidlo zblízka nesvítí (doporučeno) – opraveno** (čočka níž, viz bod 1).
7. **Servisní modul a žlaby bez detailu (doporučeno) – částečně.**
   - Oranžový kabel ve žlabu je tenčí (průměr 26 → 18 mm).
   - Malé krabičky na stěně jsou rozvodné skříňky modulu B a čela přepážky (svod kabelu ze žlabu, štítek SERVICE).
     Detail modulu (kryt, LED) je v otevřených bodech.
8. **Plochý portál ke schodům (doporučeno) – částečně.**
   - Čelo F má stejnou dvouvrstvou zárubeň jako ostatní dveře, jen bez horního dílu (průchod ke stropu).
   - Oranžové pásky na sloupcích jsou značky procedurální přepážky za čelem. Působí jako akcent, proto zůstaly.
   - Práh přijde s podlahou.
9. **Zadní dveře bez křídla, dvě stavová světla (doporučeno) – vysvětleno.**
   - Druhé (červenější) světlo patří čelu přepážky ze strany technické chodby a je vidět průchodem. Obě čela
     mají světlo každé na své straně.
   - Posuvné křídlo zatím loď nemá (kapsa v silné přepážce u chodby ano). Dveře s logikou jsou mimo tento krok.
10. **Kolize nábytku se žlabem (doporučeno, ověřit) – neplatné.**
    - Střecha hygienické buňky je ve 2,05 m, spodek nosníku žlabu ve 2,09 m, matice závěsů ve 2,084 m, objímky
      trubek ve 2,122 m. Mezera je 3,4 cm, pohled zespodu ji zkracuje.
    - Důkaz: `evidence/item10_cell_below_tray.jpg`.
11. **Oranžová ve žlabech přebíjí (doporučeno) – opraveno.** Oranžový je jen jeden kabel ze sedmi, teď je
    tenčí. Pásky na trubkách jsou značení potrubí (jeden na modul).

## Kolo 2 – FAIL

Skóre: silueta 6 (+1), detail 4, materiály 5 (+1), decaly 6 (+4), světlo 5, čitelnost 6 (+3), geometrie 7 (+1),
soulad 6 (+1). Plný výstup: `round2/critic.md`.

### Reakce na body

1. **Strop jako jednolitá plocha (musí se opravit) – opraveno.**
   - Střední pás stropu širokých místností jsou teď tři desky, krajní dvě nadzvednuté o 12 mm (plná tloušťka,
     jinak ztratily podklad – kontrola „floating“). Všechny desky jsou v tmavším grafitu.
   - Moduly A mají servisní poklop do rozvodů: rám, dvířka o 1 cm níž, dvě čtvrtotáčkové západky s oranžovou pákou.
   - Svítidlo A má jasné jádro v tlumeném prstenci (difuzor), žádný bílý čtverec.
2. **Přepálené světelné pásy (musí se opravit) – opraveno / vysvětleno.**
   - „Vlnky“ na zkosení dělal wash obložení těsně u zkosení. Zdroj je teď 11 cm před lemem žlábku.
   - „Bílá čára ve 1,3 m“ je čtecí světlo pod policí dočasného lůžka, tedy nábytek pro příští krok. V briefu kola 3
     je to uvedeno.
3. **Nízká hustota detailu stěn (musí se opravit) – opraveno.**
   - Nová varianta obložení `12L_S`: nástěnná skříňka 0,72 × 0,66 m, 11 cm hluboká, přes lištu, dvoje dvířka
     s oranžovými úchyty, panty a stavová LED. Levobok u vstupu je teď E (mřížka) – S (skříňka), detail se shlukuje
     u dveří.
   - Lem žlabu na zkosení je nižší (6 cm místo 10,5), kabely nad ním jsou vidět.
4. **Materiály bez rozlišení (musí se opravit) – opraveno.**
   - Konstrukce paleta ×1,25, drsnost 0,42, o stupně světlejší než panely i v tlumenější kajutě.
   - Stropní desky tmavší (bod 1).
   - Gumové těsnění (1,2 cm) po okraji otvoru všech dveří před zárubní.
5. **Průchod do kokpitu pravoúhlý (musí se opravit) – opraveno.** Čelo F má zkosené horní rohy (0,12 m) jako
   ostatní dveře, gumové těsnění a dvouvrstvou zárubeň. Rohy jsou ve 2,18 m, nad hlavou i na schodech:
   průchodová kontrola prošla.
6. **Žebřík vedle schodů (doporučeno) – neplatné.** Je to svod dvou kabelů ze stropního žlabu do rozvodné skříňky
   čela, s objímkami po ~0,35 m. Stejný svod mají všechna čela dveří. Důkaz: `evidence/r2_item6_cable_drop.jpg`.
7. **CREW QUARTERS nečitelný (doporučeno) – opraveno.** Světlejší tón a plná neprůhlednost. Popisky ovladačů
   dveří přijdou s logikou dveří.
8. **Svítidla bez pouzdra, nejasná mřížka (doporučeno) – opraveno.** Lineární svítidlo v širokých místnostech
   nemá příčné lamely (čte se jako světlo, ne jako výdech). Svítidlo A má difuzor (bod 1).
9. **Oranžová na každé příčce žlabu (doporučeno) – opraveno.** Oranžový kabel ve stropním žlabu je teď krémový,
   oranžová zůstala signálním prvkům.
10. **Prázdná čela u průchodů (doporučeno) – částečně.** Čela mají žebra ke stropu, madlo pod stavovým světlem,
    rozvodnou skříňku se svodem kabelů a nápisy (CREW QUARTERS, COCKPIT). Ovládací panel dveří přijde s logikou
    dveří.
11. **Skříň těsně u trubek (doporučeno, ověřit) – neplatné.** Vysoký blok je hygienická buňka se střechou ve
    2,05 m. Trubky leží na nosnících ve 2,13 m (spodek nosníku 2,09 m, objímky 2,122 m). Skříň na skafandr je
    vysoká 1,8 m. Důkaz: `evidence/item10_cell_below_tray.jpg`.

## Kolo 3 – FAIL (poslední počítané)

Skóre: silueta 7 (+1), detail 5 (+1), materiály 6 (+1), decaly 7 (+1), světlo 6 (+1), čitelnost 7 (+1),
geometrie 7, soulad 7 (+1). Plný výstup: `round3/critic.md`.

### Reakce na body

1. **Prázdné stěny, servisní modul bez hloubky (musí se opravit) – opraveno, ověřeno.**
   - Vložené desky obložení mají vnitřní panel 12 mm za 4,5 cm lemem (dřív 6 mm).
   - Skříňka `12L_S` má rám 3 cm přes dvířka, gumu mezi dvířky, pákové západky, větší panty, LED a štítek.
   - Modul E má u mřížky krabici s přípojkou a svod do žlabu na zkosení a oranžové madlo pod lištou u dveří.
   - Kvůli hlubšímu vložení se do něj prodloužily všechny přišroubované díly (štítek výrobce, poklop, úchyty
     a zásuvka modulu C, mřížka). Kontrola „floating“ jinak našla 12 visících štítků.
2. **Jeden matný materiál (musí se opravit) – částečně.**
   - Lak panelů má drsnost 0,58, konstrukce 0,36, kov 0,5, broušení 0,9 a opotřebení hran 0,7.
   - Ověřovací kolo vidí tónové rozlišení, broušený kov a opotřebené hrany ze střední vzdálenosti ne.
   - Otevřený bod (níže).
3. **Přepálené zdroje (musí se opravit) – opraveno, ověřeno.**
   - Bodovky na stěny: kužel 40°, sklon 27°, na zkosení už nesvítí.
   - Lineární svítidla širokých místností jsou o 0,25 m kratší od konců a mají 24 cd/m místo 32. Pás nad průchodem
     ke schodům (koncové žebro stropu vedle svítidla) už nepřepaluje.
4. **Prázdný kabelový žlab (doporučeno) – částečně.** Lem žlabu na zkosení je nižší (kolo 2). Ve stropním žlabu
   leží svazky na příčkách (kolo 2 skladu).
5. **Svítidlo jako stupňovitý rám (doporučeno) – neměněno.** Jádro a prstenec difuzoru z kola 2 zůstávají,
   zploštění rámu je v otevřených bodech.
6. **Závěsy jako tenké tyčky (doporučeno) – neměněno.** Závěsy jsou závitové tyče 16 mm, třmeny přijdou
   s dalším dílem kitu.
7. **Studené modré schody (doporučeno) – neměněno.** Schody do kokpitu jsou lodní (procedurální) a přijdou
   s kokpitem.
8. **Nouzové značení a popisky ovladačů (doporučeno) – neměněno.** Přijde s logikou dveří.
9. **Nábytek nad linií zkosení (doporučeno, ověřit) – neplatné.** Buňka a výdejník jsou pod zkosením, boky buňky
   ho kopírují. Geometrická kontrola i ověřovací kolo („nábytek nekoliduje se stěnami“) to potvrzují.
10. **Plochý strop a poklop (doporučeno) – částečně.** Desky ve třech výškách a poklop se západkami z kola 2.
    Šrouby v rozích stropních desek jsou v otevřených bodech.

## Ověřovací kolo (body 1–3 z kola 3) – FAIL (bod 2)

Skóre: silueta 7, detail 7, materiály 6, decaly 7, světlo 7, čitelnost 7, geometrie 7, soulad 7.
Plný výstup: `verify/critic.md`.

- Bod 1 (stěny) je opravený. Těsnění, panty, svod a madlo kritik ze střední vzdálenosti nerozliší a žádá list
  zblízka.
- Bod 2 (materiály) je opravený jen částečně: tónové rozlišení ano, broušený kov, guma a opotřebení hran
  ze střední vzdálenosti ne.
- Bod 3 (přepaly) je opravený.

### Otevřené body (předávám s nimi)

1. Povrchová odezva materiálů. Broušený kov konstrukce by potřeboval odrazy (Lumen reflections v interiéru jsou
   vypnuté kvůli výkonu), gumu a výraznější opotřebení hran. Rozhodnutí patří do kroku optimalizace a vzhledu
   materiálů, autor ho posoudí ve hře.
2. Svítidlo A zploštit na jeden rám s difuzorem, šrouby v rozích stropních desek.
3. Třmeny na závěsech trubek, patky zábradlí schodů.
4. Teplé světlo schodů do kokpitu (s kokpitem).
5. Nouzové značení (EXIT nad dveřmi do chodby) a popisky stavových světel a ovladačů (s logikou dveří).
6. Kolem zadních dveří rám s přesahem, výstražný pruh na prahu (s podlahou).
7. „Příčky u průchodu“ jsou svod kabelů do rozvodné skříňky (kolo 2, bod 6).
