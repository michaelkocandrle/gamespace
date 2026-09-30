# Interiérový kit: designový jazyk, mřížka a technická pravidla

Referenční část skillu `ship-interior` (načti při návrhu nebo stavbě dílů kitu). Designový jazyk autor schválil
a dávky 1–4 podle něj vznikly; čísla platí jen v `ArtSource/Kit/kit_rules.json`, tady je čitelná verze.
Historie dávek, kol kritika a měření: `Docs/Archive/skills/ship-interior_2026-09-30.md`.

## Designový jazyk (autor 26. 9. 2026, schválený; dávky 1–4 podle něj)

Vlastní modulární kit pro interiéry Wayfareru, Steadfastu a dalších lodí (zadání autora 26. 9. 2026: kroky
1–7, každý díl jednou vyladit a schválit, pak opakovat). Úroveň a přístup SC, design vlastní, bez kopií dílů.
Quaternius už nosná vrstva není.

Podklady:
- moodboard `ArtSource/Reference/Mood/kit_moodboard.jpg` (lokálně, obsahuje snímek z cizího videa);
- reference `starcitizenreference/Screenshot 2026-09-25 0213*.png` a `ShipDetailing_VideoNotes.md`;
- schválená chodba a kokpit v2, exteriér Wayfareru (recept `Wayfarer_hs.json`).

### 1. Tvarosloví
- **Průřez chodby: lichoběžník s osmiúhelníkovým stropem.**
  - Svislá stěna do výšky 1,3 m.
  - Nad ní zkosení 35° dovnitř, jako dnešní chodba Wayfareru (`kit.chamfer_deg`). Končí u stropu ve vybrání
    se světelnou lištou (`cove_m` 0,12).
  - Plochý strop, uprostřed kabelový žlab.
  - U podlahy sokl 0,10 m se zkosením 45° a modrou lištou.
- **Zalomená stěna:** panel se v horní třetině láme o 10–15° dovnitř. Dlouhá stěna tak není jedna rovina.
- **Rytmus:**
  - portál (rám) po 1,2 m: dva stěnové moduly 0,6 m, nebo jeden modul 1,2 m;
  - rám je o 8–12 cm hlubší než panely, šířka lícové plochy 14 cm (`portal_w`), na vnitřní hraně svítící
    prstenec.
- **Panelové poměry:** 1 : 2 a 2 : 3 (0,6 × 1,2, 0,6 × 0,9, 0,4 × 0,6). Zakázané jsou čtverce přes 0,8 m a
  souvislé plochy přes 1,2 m bez spáry.
- **Tři vrstvy, vždy nad sebou:**
  1. konstrukce (žebra, nosníky, příhrady 60–120 mm hluboké);
  2. panely předsazené 20–40 mm před konstrukcí se stínovou spárou kolem;
  3. výbava na panelech (skříňky, displeje, madla, trubky 5–30 cm).

  Panel vždy přesahuje díl pod sebou. Díly se nepotkávají v jedné rovině (blikání, WORKFLOW 9.3 p).
- **Úhly:** hlavní zkosení 35°, vedlejší 45°. Rohy panelů zaoblené nebo sražené, žádná ostrá pravoúhlá hrana
  delší než 2 cm.

### 2. Velikosti
| Prvek | Hodnota |
|---|---|
| Zkosení velkých dílů (> 1 m: žebra, portály, desky) | 12–20 mm, 2 segmenty |
| Zkosení středních dílů (0,2–1 m: skříňky, konzole, poklopy) | 6–10 mm |
| Zkosení malých dílů (< 0,2 m: ovladače, západky, šrouby) | 2–4 mm |
| Trup exteriéru, pro srovnání | 25 mm |
| Nosná žebra a rámy | 60–120 mm |
| Stěnové panely | 20–30 mm |
| Kryty a poklopy | 10–15 mm |
| Lišty a obruby | 5–8 mm |
| Stínová spára mezi panely (tmavý materiál) | šířka 6–10 mm, hloubka 10–20 mm |
| Dělicí drážka v panelu | šířka 3–4 mm, hloubka 2–3 mm |
| Větrací štěrbiny | 8 mm, rozteč 20 mm |
| Šrouby | Ø 8–12 mm, v řadách po 60–100 mm |
| Výška stropu | chodba 2,3 m, kajuta 2,3–2,4 m, servisní průlez 1,9 m |

### 3. Hierarchie detailu a shlukování
- **Velký:** portály, žebra, stěnové moduly, žlaby, desky. Určuje rytmus prostoru po 1,2 m.
- **Střední (0,2–0,6 m):** skříňky, displeje, konzole, trubky, mřížky, poklopy, madla, svítidla.
- **Malý (1–5 cm):** šrouby, štítky, kontrolky, západky, kabelové vývodky, popisky.
- **Shluky:** 60–70 % středního a malého detailu leží do ~1 m od funkčního místa. Funkční místa: dveře,
  konzole, lůžko, technika, žebřík, hasicí přístroj. Mezi shluky jsou klidné panely jen se spárou, jedním
  štítkem a zrnem materiálu. Rytmus klid – shluk – klid; nikdy rovnoměrný detail po celé stěně.
- Každý panel nad 0,5 m má aspoň spáru nebo jeden decal, jako na exteriéru. Klidná plocha nesmí být holá,
  kritik holé plochy vytýká.

### 4. Paleta a materiály
Barvy jsou lineární, sdílený master kitu s variací po panelech a zrnem v lesku.

| Materiál | Kde | Hodnoty |
|---|---|---|
| **Grafit** (lakovaný kov) | architektura: panely, konzole, desky | 0,05–0,07; drsnost 0,45–0,55; zrno 45 cm; `RoughVariation` 0,35 |
| **Gunmetal** (broušený/satinový kov) | konstrukce, rámy, madla, zábradlí, podlahové lišty | 0,33/0,33/0,34; metallic 1; drsnost 0,30–0,40 |
| **Krémová** (akcent) | lemy dveří, lůžko, výstupky, obložení rámu skla | nejvýš 10–15 % plochy prostoru |
| **Oranžová Halcyon Freightworks** (signální) | madla, záchytné body, výstražné pruhy, linky, poklopy | 0,85/0,34/0,06; nejvýš 3–5 % plochy |
| Guma | stupně, protiskluzové pásy, madla, soklové lišty | tmavá, drsnost 0,8–0,9 |
| Látka, kůže | sedadla, lůžka, polstry | švy z trim sheetu |
| Plast | kryty elektroniky, displejové rámy | drsnost 0,5 |
| Karbon | jen luxusní výbava (jiný výrobce) | – |
| Studené UI | displeje, hologramy, modré lišty u podlahy | modrá 0,45/0,72/1,0 |

- Variace mezi panely jako na exteriéru: tón ±7 %, drsnost ±0,12, 8 % panelů kovových.
- Opotřebení jen v drsnosti, bez otřených hran (rozbor SC).
- **Výrobce jako parametr:** instance palety podle výrobce.
  - Halcyon Freightworks: grafit, krémová, oranžová.
  - Kestrel Dynamics: návrh světlý šedobílý lak, tmavé gunmetal rámy, modrý akcent. Ke schválení s kitem.

### 5. Decaly a trim sheet
- **Hustota jako na podlaze a dveřích C2:**
  - dveře a rámy: číslo sekce, značky, čáry, kroužky, štítek otevírání;
  - podlaha: čáry podél stěn, pruhy u prahů, nápisy sekcí, protiskluzová pole. V nákladovém prostoru decaly
    zabírají až 50 % podlahy.
- **Typy:** strukturní (normála, drsnost, AO: spáry, šrouby, mřížky, poklopy) a informační (barva: nápisy,
  čísla, výstrahy), jak je dnes v knihovně. Dlouhé čáry jsou natažený úsek atlasu.
- **Ovládací panely:**
  - tištěný zaoblený rámeček skupiny s názvem v přerušené horní hraně;
  - oblouky stupnic kolem voličů, popisek pod každým ovladačem, emisní verze štítků;
  - jedno velké podsvícené tlačítko hlavní funkce.
- **Trim sheet kitu** (vlastní, procedurální, 4096 px, 512 px/m):
  - obruby panelů, stínové spáry, řady šroubů, švy čalounění, rámečky, lemy, protiskluzové pruhy;
  - díly kitu mapují hrany a lišty na trim sheet a velké plochy na sdílený master (triplanární zrno).
- **Písmo:** Rajdhani a Share Tech Mono. Servisní nápisy 2 cm, orientační 8–15 cm, čísla sekcí 25–40 cm.

### 6. Světla
Podle rozboru C2 a měření `Docs/Reviews/2026-09-26_interior_lighting_variants.md`.
- **Každé svítidlo, lišta a linka má své světlo:** dosah 1,5–2 m, specular 0,2, bez klasických stínů. Světlo
  je vždy v pouzdře: liniové ve zkosení a v soklu, bodové v kruhovém stropním pouzdře, nikdy holá žárovka.
- **Hustota:**
  - obytné prostory a chodby 1,2–1,8 světla na m²;
  - kokpit 2–3 na m²;
  - velké nákladové prostory 0,5–1 na m².

  Kontrolky, LED a obruby tlačítek jsou jen emisivní.
- **Barevný nádech:**
  - pracovní světla teplá bílá 4000–5200 K;
  - orientační lišty u podlahy studená modrá;
  - akcenty slabě oranžové;
  - nouzová světla červená.

  Kontrast: kužele ze stropních pouzder, tmavé kouty a mezery mezi ostrůvky světla.
- **Stíny:** návrh je MegaLights s ray-traced stíny, zapnuté jen s kamerou uvnitř lodi (+1,8 až +2,2 ms).
  Záložní režim bez stínů (+1,2 až +1,5 ms). Klasické stíny pro desítky světel nejdou (+47 až +113 ms).
- **Jemná objemová mlha:** nízká hustota, jen aby byly vidět kužele. Cena se změří v pilotu chodby.

## Mřížka a technická pravidla (krok 2, 26. 9. 2026)

Strojově čitelně je vše v `ArtSource/Kit/kit_rules.json`. Čtou ho stavební skripty dílů (`Tools/Kit`), kontroly
(`test_ship_geometry.py`, `check_kit_clearance.py`) a manifest kitu, takže čísla se mění jen tam. Výkres průřezů, rytmu a pivotů
`Docs/Kit/kit_sections.png` kreslí z pravidel `python Tools/Kit/draw_kit_sections.py`.

- **Mřížka:**
  - půdorys 0,3 m, moduly 0,3 / 0,6 / 0,9 / 1,2 m;
  - rozteč portálů 1,2 m (portál 0,3 + stěny 0,9) nebo 2,4 m (portál 0,3 + stěny 2,1). Obě smí střídat, aby rytmus
    chodby nebyl jednotvárný (autor 26. 9. 2026);
  - svisle 0,1 m;
  - výplně 0,1 a 0,2 m jen tam, kde trup vnutí šířku mimo mřížku (Wayfarer: nákladový prostor 3,8 m = 3,6 +
    2 × 0,1);
  - díly se skládají bez mezer: každý modul nese na svých okrajích polovinu stínové spáry (4 mm) nad tmavým
    těsněním, takže spoj nikde neprosvítá.
- **Standardní průřezy** (světlá šířka mezi líci panelů u podlahy / strop):

| Průřez | Šířka | Strop | Svislá stěna do | Sklon 3:4 | Strop mezi vybráními | Portál před líc |
|---|---|---|---|---|---|---|
| S servisní průlez | 0,9 | 2,1 | 1,9 | 0,2 (odsazení 0,15) | 0,6 | 0 (lícuje) |
| N úzká chodba | 1,2 | 2,3 | 1,7 | 0,4 (0,3) | 0,6 | 0,08 |
| W široká chodba, místnost | 2,4 | 2,3 | 1,3 | 0,8 (0,6) | 1,2 | 0,10 |
| T vysoká místnost, náklad | podle místnosti | 2,7 | 1,7 | 0,8 (0,6) | podle místnosti | 0,10 |

- **Profil stěny:**
  - sokl do 0,1 m se zkosením 45° a lištou u podlahy;
  - svislá část;
  - sklon 3 : 4 (36,9°, návrhových „~35°“ na mřížce);
  - vybrání 0,12 m se světelnou lištou;
  - strop s kabelovým žlabem.
- **Zóny od líce panelu** (líc = hranice místnosti z layoutu):
  - konstrukce za lícem do 0,2 m, pak obložení trupu;
  - panel 20–30 mm, předsazený 20–40 mm;
  - podlahová deska 50 mm nad konstrukcí 0,15 m;
  - strop s konstrukcí 0,25 m.
- **Průchodnost:** kapsle postavy má poloměr 0,42 m a výšku 1,92 m (`PlayerCharacter.cpp`). Světlá šířka všude
  i v portálu ≥ 0,9 m, světlá výška ≥ 2,0 m. Proto portály v průlezu S nevystupují.
  - Ověření v celé výšce kapsle po 1 cm (hlava a ramena, kde se stěna sklání): `python Tools/Kit/check_kit_clearance.py`.
  - Nejmenší boční rezerva je všude ve výšce boků (0,42 m, kde je kapsle nejširší). Ve výšce ramen a hlavy je
    rezerva větší, protože se kapsle zužuje rychleji než stěna.

| Průřez | Mezi portály: bok / hlava | V portálu: bok / hlava |
|---|---|---|
| S | 0,03 / 0,18 m | 0,03 / 0,18 m |
| N | 0,18 / 0,38 m | 0,10 / 0,30 m |
| W | 0,53 / 0,38 m | 0,43 / 0,28 m |
| T (3,6 m) | 1,38 / 0,78 m | 1,28 / 0,68 m |

  - **Výbava v chodbě N** smí vystoupit nejvýš 0,15 m od líce, pokud je jen na jedné straně (světlá šířka musí
    zůstat 0,9 m); na obou stranách nejvýš 0,15 m dohromady. Skříňky 0,2 m hluboké jen v průřezech W a T.
  - **Kamera třetí osoby** (klávesa V pěšky): rameno 3,8 m, posun (0; 0,55; 0,65) m, sonda 0,12 m, kolize zapnutá.
    V chodbě N skončí 2,75 m za postavou při vodorovném pohledu, 1,3 m při pohledu 30° dolů (narazí na sklon
    stropu). Nikdy nevleze do hlavy a zůstane v profilu. Kolize kitu proto musí blokovat kanál Camera (průchozí
    loď od 29. 9. 2026: meshe místností blokují Pawn i Visibility).
- **Kit v trupu Wayfareru** (`Tools/Kit/hull_fit_sections.py`, řezy po 0,1 m, obálka = líc + konstrukce 0,2 m
  + podlaha 0,2 m + strop 0,25 m, 5 cm od trupu, silueta se nemění; výkres `Docs/Kit/hull_fit_wayfarer.png`):
  - N a W se vejdou do nákladu, techniky i kajuty (rezerva 0,09–0,35 m, nejtěsněji u rampy x = 1,1 m).
  - Místnost na celou šířku layoutu (3,8 m) se se zónou konstrukce 0,2 m nevejde. Nejširší místnost na mřížce:
    náklad 3,0 m, technika 3,3 m, kajuta 3,0 m.
  - Pro náklad je to otázka návrhu: 8 SCU ve 2 řadách a ulička 1,25 m potřebují 3,75 m. Rozhodne se v pilotu
    (tenčí konstrukce 0,1 m jen v nákladu, jiné uspořádání SCU).
  - Kokpit je nízký prostor pod kanopou (podlaha 1,15 m, nad ní ~1,7 m do trupu). Průřezy chodeb v něm neplatí;
    dostane vlastní díly (deska s displejovým pásem, rám skla) v kroku „kokpit z kitu“.
- **Pivoty** (+X dopředu, +Y vlevo, +Z nahoru, měřítko 1, aplikované transformace):
  - průběžné díly (podlaha, strop, portál, trubky, kabely, vzduchotechnika, schody): začátek modulu na ose
    průřezu, z = 0, +X po směru chodby;
  - stěny, dveře, přepážky: dolní roh na lícové rovině, líc míří na +X, šířka po +Y (0 až W);
  - rohy: vnitřní roh průsečíku lícových rovin;
  - výbava, konzole, deska, sklo, světla: střed montážní plochy, čelo na +X.
- **Sockety:**
  - `SOCKET_Snap_Start/End/Left/Right/Top/Bottom`, vždy na mřížce;
  - `SOCKET_Light_n`: X = směr světla, parametry (typ, role teplá/studená/signální/nouzová, cd, dosah, kužel,
    stín MegaLights) v manifestu kitu;
  - `SOCKET_Decal_n`: X = normála, Y = nahoru decalu; tagy číslo sekce, výstraha, štítek, šipka, servis;
  - `SOCKET_Mount_n`: úchyt výbavy.
- **Jména:**
  - `SM_Kit_<Kategorie>_<Díl><velikost v dm><průřez>_<Varianta>`, např. `SM_Kit_Wall_Grille06W_B`. Kategorie:
    Wall, Corner, Portal, Ceiling, Floor, Stair, Door, Bulkhead, Console, Dash, Glass, Fitting, Furniture,
    Pipe, Cable, Duct, Light.
  - `MI_Kit_<Výrobce>_<Role>`, `T_Kit_<Jméno>_<BC|N|ORM|M|H|E>`.
  - Sloty materiálů dílu se jmenují podle role: `Kit_Primary` (grafit), `Kit_Structure` (gunmetal),
    `Kit_Accent`, `Kit_Signal`, `Kit_Rubber`, `Kit_Fabric`, `Kit_Plastic`, `Kit_Trim`, `Kit_Seal`,
    `Kit_GlowWarm`, `Kit_GlowCool`, `Kit_GlowSignal`, `Kit_Screen`, `Kit_Glass`.
- **Paleta podle výrobce:** loď v setupu zvolí `kit_maker` (Halcyon / Kestrel) a import přiřadí sloty rolí
  k `MI_Kit_<Výrobce>_<Role>`. Barvy rolí jsou v `kit_rules.json` (`palettes`). Kit tak slouží více lodím bez
  kopií dílů.
- **Hustota texelů:**
  - trim sheet 1024 px/m (±25 %) pro hrany, lemy, spáry a obruby (autor 26. 9. 2026: 512 byl zblízka měkký). List
    4096 × 2048: pruhy se opakují po 4 m, výšky pruhů celkem 2 m. Paměť 16,8 MB, s mipmapami 22,4 MB (BC1 barva,
    BC5 normála, BC1 ORM), jeden list pro všechny lodě. Hra teď využívá ~3,2 z 5 GB VRAM;
  - velké plochy triplanárně ve světě 1024 px/m, bez UV;
  - decaly 2048 px/m;
  - zrno 45 cm.
- **Rozpočty trojúhelníků** (LOD0, bez Nanite). Dnešní interiér Wayfareru má ~300 tisíc trojúhelníků na
  67 m² (~4,5 tisíce na m²).
  - stěna 5 000 na metr, roh 4 000, portál 8 000, strop 3 500 na metr, podlaha 1 500 na metr;
  - schod 600, dveře 10 000, přepážka 8 000;
  - konzole 15 000, palubní deska 60 000, sklo 500;
  - drobná výbava 3 000, nábytek 15 000;
  - trubky 500 na metr, kabely 1 000 na metr, vzduchotechnika 800 na metr, pouzdro světla 600;
  - místnost nejvýš 10 000 na m², interiér lodi nejvýš 1 milion;
  - LOD1 (50 %, velikost na obrazovce 0,25) jen pro konzole, nábytek a výbavu.
- **Kolize:** jednoduché UCX boxy po modulech, nikdy complex-as-simple. **Přechodná výjimka:** místnosti v lodi
  mají zatím kolizi po polygonech (`CTF_USE_COMPLEX_AS_SIMPLE` z `import_ship.py`); boxy se zavedou s optimalizací
  na konci (autor 29. 9. 2026).
  - stěna, podlaha, strop: jeden box každý;
  - portál: boxy vystupujícího rámu;
  - schody: šikmý box;
  - dveře: rám a pohyblivý box křídla;
  - konzole: jeden box, nábytek 1–3 boxy;
  - drobná výbava bez kolize, pokud se po ní nešplhá.
- **Nanite:** interiér zůstává bez Nanite, znovu ověřeno 26. 9. 2026 (`Docs/Reviews/2026-09-26_kit_nanite_check.md`):
  - s Nanite zmizely tenké díly (rámy, moduly, obruby);
  - stíny MegaLights chtějí přesnou geometrii;
  - interiér letí s kamerou (WORKFLOW 9.2 a).

## Seznam dílů (krok 3, 26. 9. 2026)

Strojově čitelně je seznam v `ArtSource/Kit/kit_parts.json`: rodiny dílů, varianty, délky modulů, průřezy,
dávka a stav (planned / built / approved). Seznam odpovídá zadání autora: 47 rodin, 78 variant před násobením
délkami a průřezy. Stavba po dávkách, další dávka až po schválení předchozí:

1. **Stěnové moduly a materiály kitu:**
   - plný, s mřížkou, se skříňkou, s průchodem trubek, se servisním poklopem, s displejem (každý A–C);
   - master a instance podle výrobce, trim sheet.
2. **Rohy, přechody, portály, strop:**
   - vnitřní a vnější roh, přechod N–W, konec chodby, zúžení do průlezu;
   - portál se svítícím prstencem;
   - stropní žlab, stropní panely se světlem a ventilací.
3. **Podlaha, schody, rampa:** desky s lištami, rošty, poklopy, schody, rampa.
4. **Zárubně, dveře, přepážky:** posuvné dveře s animovatelným křídlem.
5. **Konzole, deska, sklo:**
   - konzole stojící, nástěnná a rohová;
   - palubní deska s displejovým pásem zapuštěným pod linií pohledu a ovládacími moduly z kokpitu v2;
   - skleněné panely 0,2 / 0,32 / 0,5 m.
6. **Výbava a nábytek:**
   - madla, zábradlí, žebříky, hasicí přístroj, lékárnička, cedule;
   - skříňky, boxy, lůžko, sedadla (procedurální sedadlo z kokpitu v2).
7. **Infrastruktura:** trubky, kabely, vzduchotechnika, parametricky podle délky a průměru.
8. **Pouzdra svítidel:** liniové, bodové, nouzové, kontrolky (jen emise) s přednastavenými světly.

Pravidla pro všechny díly:
- materiál, decaly, světla a sockety podle designového jazyka, žádné holé šedé díly;
- průřez N: výbava nejvýš 0,15 m od líce;
- zákaz klávesnic u dveří platí i pro displejové moduly.
