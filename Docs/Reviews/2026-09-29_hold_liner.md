# Recenze: nákladový prostor z obložení trupu a přepážky s dveřmi (Wayfarer), 29. 9. 2026

Krok A přestavby interiéru Wayfareru. Nákladový prostor je z obložení trupu (`Wall_HullLiner`, průřez L) se stropem
z panelů L41. Přepážky s dveřmi jsou z kitu (`Bulkhead_Door`). Posuzuje se z první osoby, oko 1,65 m, snímky
z rychlé smyčky (`Shots.ps1 -Preset wayfarer_rooms -Editor`, 1920×1080).

- Zadání a páry: `2026-09-29_hold_liner/review_round1.json`, `review_round2.json`
- Listy a brief: `2026-09-29_hold_liner/round1/`, `round2/`
- Výstupy kritika: `round1/critic.md`, `round2/critic.md`
- Důkazy: `2026-09-29_hold_liner/evidence/`

## Kolo 1 – FAIL

Skóre: silueta 6, detail 4, materiály 4, decaly 5, světlo 3, čitelnost 6, geometrie 5, soulad 6.
Plný výstup: `round1/critic.md`.

### Reakce na body

1. **Černý strop (musí se opravit) – opraveno.**
   - Žlábek u stěny leží 8 cm pod stropem a strop 3,6 m široký zasáhne jen pod ostrým úhlem, takže jeho střed
     nedosvítí žádnou silou (WORKFLOW ek).
   - U každého svítidla stropu je teď slabé bodové světlo 35 cm pod stropem (`halo` v `kit_batch2.py`, 6 cd,
     neutrální). Panely, spáry i pouzdra svítidel jsou teď kolem svítidel čitelné, mezi nimi zůstává tmavší strop.
   - Albedo stropu zůstává tmavý grafit podle stylového záměru.
2. **Světlo bez zdrojů a kontrastu (musí se opravit) – opraveno.**
   - Bodovky stropních panelů: 60° a 160 cd místo 100° a 35 cd, se stínem jen v režimu interiéru. Pod každým
     svítidlem je kaluž, mezi nimi tmavší podlaha.
   - Žlábek u stropu je sekundární: 1,1 cd/m. Mezikrok ×2,5 jen přepálil okraj stropu do bíla.
   - Skvrnu nad rampou dělalo lineární světlo prvního panelu, které svítilo na nosník rámu rampy. Teď je u rampy
     bodovka a pod ní kaluž, u přepážky větrací panel (`Ceiling_Panel06L41_B`).
   - Technická chodba: lineární světlo žlabu má 34 cd/m, u krátkého modulu nejméně 14 cd. Krátký modul dával 10 cd
     a podlahu u dveří svítilo hlavně modré světlo ze schodů.
   - Změřeno (`measure_look.py`), sklad pohled dozadu: průměr 0,10 → 0,15, p50 0,06 → 0,11, B/R 0,65 → 0,72.
     Rozsah SC je 0,13–0,23, 0,08–0,18 a 0,72–1,05.
   - Segmentace žlábku: žlábek je po modulech fyzicky přerušený žebry, neměněno.
3. **Nákladová stěna, kolejnice (musí se opravit) – opraveno.**
   - Kolejnice je L-track na distančních patkách: dvě příruby a otvory po 2,5 cm. Na ní jsou dvě kotvy s D-oky,
     z jedné visí popruh s přezkou.
   - Výstražné značky jsou jen nad kotvami; štítek z každého modulu i s deskou pod ním zmizel.
   - Pravobok střídá moduly A-C-B-C-A-C místo A-C-C-C-C-B.
   - Skříňky, přípojky a madla v modulech jsou vybavení, přijdou s nábytkem (autor: po površích nábytek).
4. **Materiály (musí se opravit) – opraveno.**
   - `Kit_Primary` má drsnost 0,42 → 0,5, takže zkosení už neodráží žlábek jako lesklý pruh.
   - `Kit_Structure` je světlejší: paleta ×0,75 → ×0,9, drsnost 0,55. Konstrukce je teď o stupeň světlejší než
     panely (dvoutón).
   - Ve žlabu jsou vidět kabely: krémový (`Kit_Accent`) a oranžový (`Kit_Signal`) mezi černými.
   - Zrno a rozdíly drsnosti mezi panely už materiál má (vrstvený master, posun po panelech), neměněno.
5. **Nápis COCKPIT oříznutý (musí se opravit) – opraveno jinak, než kritik navrhl.**
   - Posun o 15 cm doprava by přetáhl šipku přes zárubeň, protože v kole 1 se jí už dotýkala.
   - Nápis je proto zmenšený na 85 % a vystředěný mezi rám stěny chodby a zárubeň. V kole 2 je z chodby celý.
6. **Černá plocha vpravo od dveří kajuty (musí se opravit) – neplatné jako chyba geometrie.**
   - Je to panel čela přepážky s lištou, oranžovým pruhem a spárami, jen byl v kole 1 neosvětlený. Důkaz:
     `evidence/item6_panel_right_of_door.jpg` (kolo 1, kolo 1 s jasem ×3, kolo 2).
7. **Dveře (doporučeno) – částečně.**
   - Stavové světlo je teď čočka 5×7 cm s vlastním oranžovým světlem na zárubni.
   - Světlo v nadpraží a v průchodu už díl má (`Light_Door_0`, `Light_Reveal_0`).
   - Zelená a červená přijdou s logikou zamykání dveří; do té doby svítí signální barva výrobce.
   - Kapsa a hrana křídla zatím neměněno.
8. **Rampa je rovná stěna (doporučeno) – odloženo.** Rampa přijde s podlahou nákladového prostoru (čeká na autorovo
   rozhodnutí o mřížce). V briefu kola 2 to je uvedeno.
9. **Sokl (doporučeno) – odloženo do kroku podlahy.** Obložení má sokl a kopací plech do 0,5 m. Spodní zkosení
   by zúžilo nákladový prostor u podlahy, patří k návrhu podlahy.
10. **Rozvodná skříňka (doporučeno) – odloženo.** Levné, ale mimo povinné body kola.
11. **Nečitelné popisky regálů (doporučeno) – odloženo.** Hlavní řádky jsou čitelné, podřádky jsou záměrně drobné.

## Kolo 2 – FAIL

Skóre: silueta 6, detail 4, materiály 5 (+1), decaly 6 (+1), světlo 5 (+2), čitelnost 7 (+1), geometrie 7 (+2),
soulad 6. Plný výstup: `round2/critic.md`.

### Reakce na body

1. **Prázdný strop bez vrstev (musí se opravit) – opraveno.**
   - Stropní panely širokých místností nesou vrstvu služeb (`services` v `kit_batch2.py`). Na jedné straně svítidel
     je žebříkový kabelový žlab se svazky (černé, krémové, oranžový), na druhé dvojice trubek s objímkami
     a barevným páskem v každém modulu.
   - Obojí visí na profilových nosnících na závitových tyčích po 0,6 m. Stanice navazují přes moduly, takže vedení
     je souvislé. Pod stropem 2,3 m zůstává průchozí výška 2,13 m.
   - Plný žlab ukazoval zespodu jen tmavou desku, proto je žlab žebříkový a kabely jsou vidět mezi příčkami.
2. **Kolejnice je jen proužek (musí se opravit) – neplatné.**
   - Kritik popisuje signální pruh pod lištou ve 1,3 m (lišta prochází celou lodí). L-track z kola 1 je ve 0,35 m:
     příruby, otvory po 2,5 cm, dvě kotvy s D-oky a popruh s přezkou.
   - Důkaz: `evidence/item2_ltrack_vs_rail_stripe.jpg` (červeně pruh, který kritik četl jako kolejnici, zeleně
     L-track a jeho výřez).
3. **Ploché panely mezi žebry (musí se opravit) – opraveno.**
   - Horní deska hlavního panelu je v modulu 1,2 m rozdělená na dvě. Každá deska obložení (hlavní, horní, pás nad
     lištou) má šrouby ve všech rozích.
   - Nákladové moduly C mají funkční prvky u kontejnerů: madlo u žebra (oranžové) a přípojku napájení pro
     napájené kontejnery s krytkou a štítkem.
   - Strana uličky zůstává hladká a servisní (A, B), detail se shlukuje na nákladové straně, jak kritik chtěl.
   - Nápis „03“ se posunul z nové spáry na levou desku; geometrická kontrola ho hlásila, protože paprsek propadl
     spárou.
4. **Jeden plastový lak (musí se opravit) – opraveno.**
   - Konstrukce (žebra, zárubně, lišty) je broušený kov, ne světlejší lak: `Kit_Structure` metalicita 0,5 → 0,75,
     drsnost 0,42.
   - „Voskový odlesk přes celý strop“ dělaly svatozáře stropu. Ty mají teď nulový odlesk (`specular` v socketu,
     `kit_rooms.py`).
   - Guma (lem soklu, kabely), oranžový hladký lak a otěr hran už materiály mají, neměněno.
5. **Světlo bez kontrastu (musí se opravit) – opraveno.**
   - Bodovky 260 cd a 50° místo 160 cd a 60°.
   - Žlábek u stropu na 45 % (1,1 → 0,5 cd/m), wash stěn 1,1 → 0,7 cd/m. Mezi kalužemi je tma.
   - Změřeno, sklad pohled dozadu: průměr 0,13, p50 0,09, B/R 0,71 (SC 0,13–0,23, 0,08–0,18, 0,72–1,05).
6. **Průřez jako krabice (doporučeno) – odloženo do kroku podlahy** (stejně jako bod 9 z kola 1).
7. **Stropní svítidlo jako mřížka (doporučeno) – neměněno.** Lamely lineárního svítidla přidalo dřívější kolo
   kritika u stropů kitu („nalepená bílá deska“, komentář v `kit_batch2.py`). Obě výtky si protiřečí, rozhodne
   autor ve hře. Svítidlo
   „tříbodové“ je bodovka s dvěma lamelami a teď svítí kaluží na podlahu.
8. **Dveře bez prahu, kapsa (doporučeno) – odloženo.** Práh přijde s podlahou z kitu (dnes je podlaha lodní).
9. **Nízkokontrastní a duplicitní štítky (doporučeno) – odloženo.** COOLER S1 je dvakrát, protože obě stěny chodby
   mají stejný díl `Wall_ComponentBay06W_B`. Číslování jednotek patří k dílům kitu (další dávka).
10. **Přepálené stavové světlo (doporučeno) – odloženo.** „Bílý indikátor vpravo“ je prvek kajuty za dveřmi,
    ne přepážky.

## Kolo 3 – FAIL (poslední počítané)

Skóre: silueta 7 (+1), detail 5 (+1), materiály 5, decaly 6, světlo 4 (−1), čitelnost 7, geometrie 7, soulad 7 (+1).
Plný výstup: `round3/critic.md`.

Hlavní výtka je opak kola 2: po ztlumení žlábku a washe stěn (kolo 2: „žlábek na 30–40 %, mezi svítidly tma“)
zčernaly spodní části stěn. Druhá příčina byla moje: metalicita konstrukce 0,75 z kola 2. Kov bez odrazů ztrácí
difuzní světlo a konstrukce splynula s panely. Tutéž lekci už jednou daly kola materiálového kroku kitu, v komentáři
`import_kit.py` to stálo.

### Reakce na body

1. **Stěny bez světla (musí se opravit) – opraveno, ověřeno v ověřovacím kole.**
   - U každého stropního svítidla A jsou dvě bodovky pro stěny (`scallop` v `kit_batch2.py`, pouzdro v postranním
     pásu stropu, 22° ke stěně, 60 cd, 70°). Na obložení dělají světelné kaluže ve výšce lišty.
   - `kit_rooms.py` a showroom kitu nově berou směr bodovky ze socketu (`dir_ue`).
   - Wash obložení svítí dolů po vlastní stěně místo do místnosti: zkosí přes panely, na jejich hranách, šroubech
     a přírubách žeber. Má 5 cd/m a končí 15 cm před žebry, v plné délce přepaloval horní konce přírub.
   - Změřeno, sklad pohled dozadu: průměr 0,23, p50 0,18, p99 0,84, B/R 0,72 (horní hranice rozsahu SC).
2. **Panely bez hloubky a materiálu (musí se opravit) – opraveno, ověřeno v ověřovacím kole.**
   - Konstrukce: paleta ×1,1, metalicita 0,45, drsnost 0,48, broušení. Je o dva stupně světlejší než panely.
   - Panely mají odstín a drsnost po deskách (`PanelTone` 0,22, `PanelRough` 0,2).
   - Šrouby v rozích jsou větší (průměr 16 mm), aby byly vidět ze střední vzdálenosti.
   - Hloubka spár se neměnila: 12 mm spára a tmavý podklad 7 cm za lícem jsou tam od začátku. V zešikmeném washi
     jsou teď hrany desek vidět.
3. **Kolejnice nečte jako kolejnice (musí se opravit) – neplatné, podruhé.**
   - Kritik opět popisuje signální pruh pod lištou ve 1,3 m. „Zásuvky pod ním“ jsou přípojky napájení kontejnerů
     (kolo 3). Důkaz: `evidence/round3_item3_ltrack_vs_rail_stripe.jpg`.
   - Protože byl L-track ve 0,35 m ve tmě, rozsvítil ho až wash stěn z bodu 1. V ověřovacím kole je v briefu uvedeno,
     kde L-track je.
4. **Strop zblízka (doporučeno) – neměněno.** Svatozáře u svítidel strop čtou, vrstva služeb dala nosníkům objem.
5. **Závěsy žlabu plovou (doporučeno) – opraveno.** Závitové tyče byly (průměr 10 mm) a teď mají 16 mm.
6. **Přepážka ze strany skladu plochá (doporučeno) – odloženo.** Čelo `Bulkhead_Door00L41_C` má stejnou zárubeň
   i stavové světlo jako čelo v chodbě, bylo jen ve tmě. Svod kabelů na čele skladu přijde s podlahou.
7. **Střední měřítko (doporučeno) – částečně.** Přípojky a madla na nákladové straně z kola 3; skříňky patří
   k nábytku a vybavení (další krok).
8. **Žlábek bez pouzdra (doporučeno) – neměněno.** Pouzdro (lem, lišta, difuzor) má, ze vzdálenosti je vidět jen
   svítící pruh.
9. **Teplota světla mezi místnostmi (doporučeno) – odloženo.** Bílé pruhy v technické chodbě jsou žlábky stěn W
   (teplá bílá `Kit_GlowWarm`), při jiné expozici vycházejí bíleji. Sjednotí se s krokem kajuty.
10. **Malé decaly, nouzové značení u průchodů (doporučeno) – odloženo.** Nápis CARGO HOLD je z dřívějšího kroku;
    velké stencily místností jsou práce pro sadu decalů interiéru.
11. **Dva štítky COOLER S1 (doporučeno) – odloženo** (viz kolo 2, bod 9).

### Vedlejší změny

- `Wall_HullLiner06L_C` má 4772 trojúhelníků při rozpočtu 4200. Na krátkém modulu jsou to otvory kolejnice,
  madlo a šrouby; díl se ve Wayfareru nepoužívá.
- Stropy `Ceiling_Panel06L41_A/_B` mají s vrstvou služeb a bodovkami na stěny 2668 a 2376 trojúhelníků při
  rozpočtu 2100.
- Test `test_kit_showroom.py` čte seznam stíněných světel z `kit_rooms.py` a hlídá, že stíněné bodovky svítí jen
  v režimu interiéru.

## Ověřovací kolo (jen body 1, 2, 3, 5 z kola 3) – PASS

Skóre: silueta 7, detail 7, materiály 7, decaly 7, světlo 7, čitelnost 8, geometrie 7, soulad 8.
Plný výstup: `verify/critic.md`. Snímky: `shots:20260929_234719_wayfarer_rooms` (rychlá smyčka), zabalená hra
`20260929_235610_wayfarer_rooms` a procházka `20260929_235330_wayfarer_walk`.

- Body 1 (stěny), 2 (panely a materiály) a 5 (závěsy žlabu) jsou opravené.
- Bod 3 (kolejnice) je opravený co do polohy. Z listu 03 ze střední vzdálenosti ale L-track pořád čte jako tenká
  linka s tečkami. Zblízka je vidět celý (`evidence/round3_item3_ltrack_vs_rail_stripe.jpg`). Otevřené doporučení:
  výraznější profil a oka.

### Otevřená doporučení (předávám s nimi)

1. L-track čitelnější zdálky (výraznější profil, větší oka).
2. Čelo přepážky ze strany skladu: svod kabelů a skříňka jako ze strany chodby. Přijde s podlahou.
3. Stavové světlo přepálené, emise na třetinu. Emise `Kit_GlowSignal` je společná pro celý kit.
4. Wash nákladové stěny je rovnoměrný. Kritik chce střídat intenzitu svítidel.
5. Závěsy žlabu bez kotevní desky u stropu.
6. Stropní desky zblízka bez spár a šroubů.
7. Tmavý spodek stěny u tenkého čela v technické chodbě.
8. Variace tónu mezi panely. `PanelTone` 0,22 už běží, kritik ji ze vzdálenosti nevidí.
9. „COCKPIT u dveří do kajuty“ – nápis ukazuje cestu. Kajutou se jde ke schodům do kokpitu, podřádek zní
   CREW QUARTERS · FLIGHT DECK. Neplatné.

Z kol 1–3 zůstává odloženo: rampa, sokl a spodní zkosení, práh dveří (s podlahou), velké stencily místností,
COOLER S1 dvakrát, teplota žlábků v technické chodbě.
