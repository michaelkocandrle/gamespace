# Recenze: interiérový kit, dávka 1 – stěnové moduly (27. 9. 2026)

Zadání kitu: krok 4 (stavba dílů po dávkách, první dávka stěny). Showroom: chodba průřezu W
(šířka 2,4 m, svislá stěna do 1,3 m, zkosení do 2,1 m, strop 2,3 m) z 20 stěnových modulů
v `TestSpace` na (0, −500, 0) m, snímky `Tools/Shots/kit_showroom.json` ze zabalené hry, 1920×1080.
Podlaha, strop, konce chodby a stropní světla jsou provizorní (dávky 2–3).

Kritik: podagent `visual-critic` (Fable 5.1), listy `Tools/Review/make_compare_sheet.py`.

## Shrnutí

| Kolo | Verdikt | Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Soulad | Součet |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | FAIL | 6 | 3 | 4 | 5 | 4 | 6 | 5 | 6 | 39 |
| 2 | FAIL | 6 | 3 | 4 | 5 | 5 | 6 | 5 | 6 | 40 |
| 3 | FAIL | 7 | 5 | 5 | 6 | 6 | 7 | 7 | 8 | 51 |
| ověření | částečně | body kola 3: lišta a trubky vyřešeno; střední vrstva, materiál a štítky částečně | | | | | | | | |

Otevřené body pro autora a další dávky:
- **Svislé panely:** plné panely mezi výbavou jsou pořád jednolité, i s dělením v 0,86 m.
- **Opakování vedení:** vedení na sklonu je na každém modulu stejné, v dlouhé chodbě dělá rastr.
- **Materiál:** chybí mikroškrábance a kartáčování v normálové mapě. Oděr hran a gumové těsnění jsou zblízka
  málo čitelné.
- **Štítky:** obecné servisní šablony se opakují na sousedních modulech a leží i na prázdném panelu. Mají
  patřit jen k hardwaru, případně jedna na několik modulů.
- **Světlo:** stropní svítidla s kužely a konce chodby jsou provizorní (dávka 2).
- **Značení:** velké označení sekcí, směrovky a nouzové značky přijdou s dávkou 6.

## Kolo 1 – FAIL

Listy a výstup: [round1/](2026-09-27_kit_batch1_walls/round1/) (`critic.md`, 327 s).

| Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Soulad |
|---|---|---|---|---|---|---|---|
| 6 | 3 | 4 | 5 | 4 | 6 | 5 | 6 |

### Reakce na výtky

1. **Chybí konstrukční vrstva, horní polovina stěny prázdná (musí se opravit) – opraveno.**
   Na styku modulů je teď žebro (dvě poloviny po 3 cm, 6 cm před panely) přes svislou část i zkosení.
   Pod horním vybráním vede kabelový žlab na držácích po 0,6 m (tři černé kabely a jeden krémový).
   Spáry mezi panely jsou 12 mm místo 8 mm a zadní tmavá vrstva je 7 cm za panely, takže spára má hloubku.
   Zkosení je od kola 1 rozdělené přírubou na dva panely. Prohlubeň s krytem nebo mřížkou mají moduly
   Grille (A/B ve svislé části, C ve zkosení).
2. **Světlo: přepálené skvrny a řetěz bodů, plochý zbytek (musí se opravit) – opraveno.**
   Soklová světla jsou zasunutá ve vybrání 7,5 cm nad podlahou (dřív 3,5 cm), mají zdroj o poloměru
   6 cm místo 1 cm a intenzitu 0,15 cd. Import nově čte `source_radius_cm` ze socketu.
   Provizorní stropní světla mají polovinu intenzity (bodovky 30 cd s kuželem 60° místo 80°, výplňová
   12 cd místo 20 cd), takže mezi nimi zůstávají tmavá místa.
   Provizorní podlaha má vlastní drsný materiál (drsnost 0,7), takže už neodráží sokl jako zrcadlo.
   Obdélníková světla (rect light) jsem nepoužil: MegaLights/stíny se řeší samostatně
   (návrh MegaLights čeká na autora).
3. **Trubky končí v ničem a vedou do skříňky (musí se opravit) – opraveno.**
   Každá trubka vychází ze stěny a do stěny se vrací uvnitř modulu: oblouk 90°, průchodka s manžetou
   u stěny, 13 cm od konce modulu. Přírubu na hranici modulu jsem zrušil a držáky jsou na 0,38 m od konců.
   Trasy přes víc modulů (mosty trubek) přijdou v dávce 7.
4. **Skříňky a poklop jsou krabice bez výbavy (musí se opravit) – opraveno.**
   - Skříňky mají korpus s velkým ohybem hran, zvýšený rám a dveře zapuštěné 12 mm do rámu přes
     tmavou spáru. K tomu panty na rámu a větrací štěrbiny.
   - Horní a spodní skříňka se liší: horní má páku západky, spodní zapuštěné madlo a zámek na klíč.
   - Vysoká skříňka má zapuštěné svislé madlo s oranžovým úchopem a západkový štítek.
   - Úložná bedna má víko se spárou, dvě rychlouzávěry s oranžovými pákami a boční madla.
   - Poklop má zvýšený rám, čtyři velké rychlouzávěry (průměr 28 mm), dva panty a zapuštěné madlo nebo
     T-kliku. Výstražný pás vede podél horní hrany rámu a uprostřed je jen malý popisek.
5. **Materiál je jedna matná plastová hmota (musí se opravit) – opraveno částečně.**
   - Konstrukce (žebra, rámy, držáky, žlab) je světlejší broušený kov (0,42, drsnost 0,28, metal 1).
   - Lakované panely mají víc kovu pod lakem (metallic 0,45), silnější variaci drsnosti (0,45) a grunge
     (0,4). U podlahy je nově špína z vertex barvy: okluze klesá k podlaze ve spodních 0,5 m.
   - Guma je ve spárách soklu a v kabelech.
   - Krémový akcent (trubky, kabel) je matnější (drsnost 0,56) a špinavější, kritik ho četl jako
     „bílé lesklé trubky“.
   - **Neopraveno: oděr hran.** SC lak podle rozboru nemá ošoupané hrany
     (`Docs/Reviews/2026-09-26_sc_breakdown_tasks.md`), opotřebení je jen na kovu, madlech a u podlahy.
6. **Horní světelná lišta ve vybrání neexistuje jako tvar (doporučeno) – opraveno.**
   Pod hranou vybrání je teď úzká svítící linka, takže je svítidlo vidět i zespodu, nejen jako záře na stropě.
   Vybrání je hluboké 10,5 cm s lemem, římsou a čelem.
7. **Decaly bez hierarchie a opakované (doporučeno) – opraveno částečně.**
   - Servisní šablony a čísla panelů se v modulu neopakují (výběr bez opakování).
   - Číslo panelu je větší a leží v prohlubni panelu. Značka rohu, která ležela přes žebro, je pryč.
   - Výstražné pruhy jsou jen po obvodu poklopu.
   - Popisky pod tlačítky displeje jsou v kole 2 stejně malé. Tlačítka mají teď vlastní svítící
     proužek, takže čitelnost drží tvar, ne text.
   - Označení sekcí (~20 cm), směrovky a nouzové piktogramy patří k portálům a značení
     (dávky 2 a 6), ne ke stěnovému modulu.
8. **Displej bez skla, bez záře, tlačítka jako placeholder (doporučeno) – opraveno.**
   Před obrazovkou je krycí sklo 3 mm uvnitř rámečku; sklo mají i malý panel a svislý ukazatel.
   Tlačítka jsou 3D klávesy v tmavé jamce s rámečkem, 4 mm nad ní, se svítícím proužkem.
   Záře (bloom) je věc nastavení obrazovkového materiálu `M_Ship_Screen`, ten je sdílený s kokpitem.
9. **Proporce: chodba příliš vysoká, strop ~3,3 m (doporučeno) – neplatné.**
   Strop je 2,3 m (průřez W z `ArtSource/Kit/kit_rules.json`), zlom do zkosení je ve 1,3 m a horní hrana
   zkosení ve 2,1 m. Kamera je ve výšce oka 1,65 m.
   Důkaz: [evidence/9_strop_2_3_m.jpg](2026-09-27_kit_batch1_walls/evidence/9_strop_2_3_m.jpg), kde čáry
   2,3 / 1,65 / 0 m v perspektivě sedí na hrany koncové stěny.
   Dojem výšky dělá zorné pole 90°. V kole 2 jsou rozměry uvedené v briefu.

Ověření mimo kritika: rozpočty trojúhelníků všech 20 dílů jsou v limitu (`kit_build.py` KITBUILD
`over_budget: []`). Decaly vynechané placerem zůstávají jen tam, kde panel zakrývají trubky
(Pipes A/B).

Mezi koly 1 a 2 jsem po vlastní kontrole snímků opravil ještě tři věci. Provizorní strop byl kovový a zrcadlil
provizorní světla jako přepálený kříž, teď má drsný nekovový materiál. Kabelový žlab měl krycí plech, takže
kabely nebyly vidět, teď je otevřený. Dublovací plech na Plain B nesl sytou výstražnou nálepku, teď má šablonu
momentu utažení.

## Kolo 2 – FAIL

Listy a výstup: [round2/](2026-09-27_kit_batch1_walls/round2/) (`critic.md`, 317 s, `measure_look.txt`).

| Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Soulad |
|---|---|---|---|---|---|---|---|
| 6 | 3 | 4 | 5 | 5 | 6 | 5 | 6 |

Skóre se proti kolu 1 skoro nepohnulo. Měření vzhledu ukázalo systémovou chybu, kterou kritik popsal jako
desítku lokálních výtek. Stěny měly jas 0,06–0,10 (SC 0,13–0,23), chodba 0,14 a B/R 0,58 (SC 0,72–1,05).

Příčiny, které byly moje:
- Lak dostal v kole 1 `PaintMetallic` 0,45 a ztratil skoro půl difuzního světla.
- Konstrukce jako čistý kov (1,0) zrcadlila tmavou místnost, takže žebra splynula se spárami. Kritik
  napsal „žádná žebra“ a poloviny žeber přečetl jako „svislé trubky bez držáků“ (bod 10).
- Stěny pod 1,3 m nic nesvítilo: lišta ve vybrání svítí jen do stropu, soklové světlo leží za rovinou panelu
  a bodovky mají úzký kužel.

Pitfall zapsán do WORKFLOW co.

### Reakce na výtky kola 2 (opravy před kolem 3)

1. **Chybí konstrukční vrstva (musí se opravit) – opraveno.**
   Na každém spoji je rám 13 cm s plochým lícem 9 cm, 8,5 cm před panely (polovina 6,5 cm na každém modulu).
   Má čisté koleno mezi svislou částí a sklonem a šrouby po 0,3 m. Materiál je světlejší lakovaný kov, ne zrcadlo.
2. **Spodní stěna černá, bez světla (musí se opravit) – opraveno.**
   - Lak je dielektrikum (metallic 0,1).
   - Pod hranou vybrání je lineární světlo mířící dolů a ven: osvětluje sklon a protější stěnu.
   - Provizorní bodovky mají 45 cd a kužel 90° a stojí dál od konců chodby.
   - Jas stěn je teď 0,13–0,18, chodby 0,21.
3. **Trubky v pochozí zóně, bílé PVC (musí se opravit) – opraveno.**
   - Pipes A a B vedou pod madlovou lištou (1,1–1,2 m). A má ventil s oranžovým ručním kolem.
   - Pipes C je potrubí v zapuštěném kanálu v pase s objímkami, průchodkami a perforovaným krytem.
   - Trubky jsou z kovu konstrukce s úzkým barevným kódem (krémový pás mezi dvěma oranžovými kroužky).
4. **Světelné lišty bez pouzdra (musí se opravit) – opraveno.**
   Všechny tři lišty (sokl, vybrání nahoru, pod hranou vybrání) mají kovový profil s lemy, koncovky a difuzor.
   Soklová lišta je ztlumená (emise 8 → 4). Místo řetězu bodů svítí na lištu jedno lineární (rect) světlo.
5. **Madla jako oranžové kvádry (musí se opravit) – opraveno.**
   - Skříňky mají U-madla z kulatiny na dvou kovových podpěrách 3 cm ode dveří a horní skříňka kulatou páku
     na čepu.
   - Bedna má přezkové uzávěry (háček na víku, třmen, oranžová páka).
   - Poklop B má T-kliku z kulatiny.
   - Oranžová je lak (80 % palety, drsnost 0,5), ne emise.
6. **Decaly malé, bez hierarchie (doporučeno) – opraveno částečně.**
   Popisky kláves displeje jsou o 40 % větší. Označení sekcí, směrovky a nouzové značky patří do dávky 6
   (značení) a k portálům z dávky 2, stěnový modul je nenese.
7. **Zrcadlová skladba stěn (doporučeno) – neopraveno.**
   Ukázka je katalogový vzorek všech 20 dílů. Skladba podle funkčních uzlů přijde s krokem 6 (sestava
   z layoutu). Přeskládání by rozbilo záběry detailů.
8. **Šum a plastový lesk (doporučeno) – opraveno.**
   Zrno konstrukce je 0,25 (dřív 0,15 u čistého kovu, který se třpytil), variace drsnosti laku 0,35.
   Špína u soklu je z kola 1.
9. **Poklop bez západky a hloubky (doporučeno) – opraveno.**
   Kryt je 16 mm pod lícem rámu. Čtvrtotáčkové uzávěry (Ø 28 mm), panty a zapuštěné madlo nebo T-klika
   tam byly už v kole 2.
10. **Svislé trubky bez držáků (doporučeno) – neplatné jako trubky, platné jako čitelnost.**
    Šlo o dvě poloviny žebra (2 × 3 cm se zaoblením), ne o trubky. Opraveno bodem 1.
11. **Displej bez skla (doporučeno) – opraveno částečně.**
    Krycí sklo tam od kola 2 je, v tmavé místnosti ale nemá co odrážet. Tlačítka jsou klávesy v jamkách
    se svítícím proužkem. Bloom je věc sdíleného `M_Ship_Screen`.

Výkon po kole 3: GPU 16,3 ms (~61 FPS), `Lights` 3,9 ms (dřív 14,6 / 2,7). Lineární světla stojí
+1,2 ms, zato nepálí skvrny a osvětlí stěny.

## Kolo 3 – FAIL (poslední započítané)

Listy a výstup: [round3/](2026-09-27_kit_batch1_walls/round3/) (`critic.md`, 291 s, `measure_look.txt`).

| Silueta | Hierarchie | Materiály | Decaly | Světlo | Čitelnost | Geometrie | Soulad |
|---|---|---|---|---|---|---|---|
| 7 | 5 | 5 | 6 | 6 | 7 | 7 | 8 |

Součet skóre 51 (kolo 2: 40, kolo 1: 39). Měření chodby: průměr 0,21, p90 0,35, B/R 0,71, detail 0,025,
vše v rozsahu SC.

### Reakce na výtky kola 3 (opravy po posledním kole, ověřené jedním ověřovacím kolem)

1. **Prázdné panely, chybí střední vrstva (musí se opravit) – opraveno.**
   - Hlavní panel je vodorovně rozdělený v 0,86 m a horní deska je o 12 mm vpředu, takže vzniká stínová spára
     a přesah. Na horní hraně spáry je řada nýtů.
   - Horním sklonem vedou dva kabelové kanály na příchytkách, do rámů vcházejí přes objímky.
   - Každý modul má dál svůj funkční prvek: skříňku, poklop, mřížku, displej, ventil nebo ID štítek.
2. **Jednolitý plastový materiál (musí se opravit) – opraveno částečně.**
   - Oděr hran je jen na plochách zkosení. `kit_geo` dává G = 0 plochám, které vznikly bevelem.
     Na nízkopolygonových dílech by maska po vrcholech ošoupala celé plochy.
   - Síla oděru: lak 0,3, konstrukce 0,5, krémová 0,3 (jako interiér Wayfareru 0,3–0,8, trup 0,15).
   - Poklopy a mřížky mají gumové těsnění uvnitř rámu. Variace drsnosti laku je 0,35.
   - Moje dřívější odmítnutí oděru („SC lak nemá otřené hrany“) bylo příliš silné: rozbor SC oděr jen snížil.
   - **Neopraveno:** mikroškrábance a kartáčování v normálové mapě. Chtějí detailní texturu na všech
     površích (trim sheet má kartáčované pruhy jen na liště a kopacím plechu). Otevřený bod pro další dávky.
3. **Popisky bez hardwaru, opakované decaly (musí se opravit) – opraveno.**
   - Šablony „GND POINT“, „EXT PWR“ a „HF-CL“ jsou ze stěn pryč. Zůstaly jen obecné servisní šablony
     (SERVICE ACCESS, INSPECT 500 H, DO NOT PAINT), jedna na modul, šablona ve sklonu zmizela.
   - Výstražné pruhy nad poklopy jsou tlumené tón v tónu (`hazard_subtle`). Pruhy „nad skříňkami“ na listu 04
     byly pruhy nad poklopem Hatch12W_C vedle skříněk, ne nad skříňkami.
4. **Ploché světlo na stěnách, černý konec chodby (doporučeno) – neopraveno.**
   Stropní světla i konce chodby jsou provizorní. Svítidla ve stropě s kužely přijdou s dávkou 2 (strop),
   konec chodby s portály.
5. **Schody na liště ve vybrání (doporučeno) – opraveno.**
   Nad každým spojem je konzole vybrání (Structure, přes lem i lištu), která schová konce lišt.
   Samostatné koncovky jsou pryč.
6. **Trubky končí naslepo v žebru (doporučeno) – opraveno.**
   Vstup do stěny je 0,2 m od konce modulu (dřív 0,13 m), s průchodkou a manžetou mimo rám.
7. **Chybí velké označení sekce (doporučeno) – neopraveno.**
   Patří do dávky 6 (značení: sekce, směrovky, nouzové značky, logo výrobce).
8. **Displej bez skla, tmavý text (doporučeno) – neopraveno.**
   Sklo tam je (viz kolo 2, bod 11). Sekundární text je ID obrazovky v atlasu `kit_screens.py`, oprava přijde
   s obsahem displejů.
9. **Poklop jen deska se čtyřmi šrouby (doporučeno) – opraveno.**
   Čtvrtotáčkové uzávěry a panty tam byly. Přibylo gumové těsnění a zapuštěné madlo nahoře.

Během oprav kola 3 se objevila jedna vlastní vada. Rám se zkosením 5 mm pro oděr hran se kvůli hladkému
stínování četl jako kulaté sloupy, proto jsou rámy bez zkosení a oděr nesou jen zkosené panely, rámečky a lišty.

Výkon po opravách: GPU 16,97 ms (~59 FPS), `Lights` 3,89 ms. Měření chodby: průměr 0,21, p90 0,35,
B/R 0,72, detail 0,026.

## Ověřovací kolo po kole 3 – ČÁSTEČNĚ

Listy a výstup: [verify/](2026-09-27_kit_batch1_walls/verify/) (`critic.md`, 187 s, `measure_look.txt`). Kritik
posuzoval jen body 1, 2, 3, 5 a 6 kola 3. Kolo se do limitu tří kol nepočítá.

| Bod kola 3 | Stav | Reakce |
|---|---|---|
| 1 střední vrstva | částečně | Horní sklon je vyřešený. Svislé plné panely jsou i s dělením jednolité a vedení se opakuje v rastru: otevřeno. |
| 2 materiál | částečně | Kontrast rám/panel a holý kov trubek čte, oděr hran a těsnění zblízka ne: otevřeno (detailní normálová mapa). |
| 3 štítky | částečně | GND/EXT PWR jsou pryč. Obecné šablony se opakují a leží i na prázdném panelu: otevřeno (štítky jen k hardwaru). |
| 5 lišta ve vybrání | vyřešeno | – |
| 6 trubky u rámu | vyřešeno | – |

Poznámka k těsnění: gumový lem 6 mm uvnitř rámu poklopu i mřížky v geometrii je (Kit_Rubber). Ve střední
vzdálenosti ale splývá se stínovou spárou, výtka tedy platí jako výtka k čitelnosti.
