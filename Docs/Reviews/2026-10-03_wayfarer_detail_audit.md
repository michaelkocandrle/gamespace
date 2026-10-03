# Audit detailu Wayfareru proti SC: „detail, který platí“ (3. 10. 2026)

Jen audit: nic se nestaví, nic se neodstraňuje, kritik se nespouštěl. Výsledkem je návrh pravidla pro skill
`ship-pipeline` (kap. 3b3). Skill `new-ship` v repozitáři zatím není, text pravidla je připravený i pro něj.

**Podklady SC**
- Rozbory videí: `starcitizenreference/ShipDetailing_VideoNotes.md`. Odkazy jsou psané jako C2 / KOK / MOLE a čas
  ve videu. Snímky videí na novém PC chybí (byly mimo git), proto se opírám o zápis s časy.
- Screenshoty v `starcitizenreference/` (25 snímků, `cockpit_reference_*`): všechny jsou interiér nebo kokpit,
  pěšky z 1–3 m. Exteriér je jen nos lodi 890 Jump ze 2–8 m (`Screenshot 2026-09-25 021133`).
- Exteriéry SC v `Docs/UI/`: chase pohledy 15–40 m (`Screenshot 2026-09-20 093457` Gladius, `093924` / `094043`
  Arrow, `235808` / `235846` Guardian, `2026-09-17 201804`) a marketingové rendery (`star-citizen-spaceships-4k-ma.jpg`
  Starlifter, `Concept_citcon2015_5.avif` Gladius).
- Snímek `Docs/UI/Screenshot 2026-09-20 091342` je z naší hry, ne ze SC; vyřazen.
- **Exteriér SC obcházený pěšky z 1–3 m nemáme v žádném podkladu.** Ve sloupci 1–3 m je u exteriéru proto všude
  „nejistě“.

**Podklady u nás**
- `Export/Wayfarer_decals.json`: 4 385 decalů trupu. Po pravidlech: šrouby kitu 3 408, coverage 348, kit_detail 150,
  panel_numbers 138, clusters 128, items 101, panel_marks 54, companions 40, greeble_companions 18.
- `Design/Wayfarer_exterior_kit.json`: 144 desek, 1 270 bodů šroubů, 68 čísel desek, 54 malých poklopů se 108 zámky.
- Recept `HardSurface/Wayfarer_hs.json`, `Export/Wayfarer_budget.json`, knihovna `Shared/Decals/decal_library.json`.

**Viditelnost (výpočet, ne reference).** Chase kamera FOV 80°, 1920 px: ve 28 m je 41 px/m, v 10 m 114 px/m,
v 5 m 229 px/m, ve 2 m 570 px/m. Na tomto výpočtu stojí hranice „uvidí“:
- tvar je vidět od ~4 px;
- písmo je čitelné od ~8 px výšky znaku.

Co to dává pro naše rozměry:
- šroub kitu 5 cm: 2 px ve 28 m, 11 px v 5 m;
- číslo desky (znak ~3 cm): 1 px ve 28 m, 3 px v 10 m, 7 px v 5 m, čitelné až ze ~2 m;
- šablona 3,4 cm: totéž jako číslo desky;
- NO STEP 7 cm: 3 px ve 28 m, 16 px v 5 m;
- poklop 26 × 20 cm: 10 × 8 px ve 28 m (tvar);
- spára 6 mm: pod 1 px ve 28 m (vidět jen stínováním hrany).

## Tabulka

Vzdálenosti: **chase** 28 m, **blízko** 5–10 m, **obcházení** 1–3 m, **int.** = interiér. U nás „vidět“ podle
výpočtu výše.

| Kategorie | SC: chase | SC: blízko | SC: obcházení | SC: int. | U nás (počet) | U nás vidět od | Verdikt |
|---|---|---|---|---|---|---|---|
| Šrouby rámu a desek | ne (Starlifter 4K čisté desky, Gladius, Guardian) | ne (tytéž) | nejistě | ano: decal na hranách stěn (C2 4:30, 5:10), řady nýtů (`021554`) | 3 408 decalů z 1 270 bodů + řady nýtů ve shlucích | ~5 m | exteriér: decal jen u hardwaru (zdvojovací plech, závěs, poklop), plochá deska bez šroubů; interiér: decal |
| Čísla desek | ne | ano, ale jen **jedno velké číslo na panelu** („08“ na panelu MOLE, MOLE 0:32) a registrace (Starlifter „SC-2647BM“ na ploutvi) | nejistě | ano: velká malovaná čísla (`021347`, `021701`) | 68 čísel (R 18, K 14, L 14, S 11, U 10, N 1), znak ~3 cm; + 8 falešných kódů `panel_A12…` z coverage | ~2 m | decal, ale jen velké číslo (≥ 15 cm) na několika hlavních panelech a registrace; drobná čísla každé desky ne |
| Nápisy, stenciling | jen značky a názvy lodi (GUARDIAN `235808`) | ano: NO STEP, servisní text u poklopů (Starlifter 4K); atlas C2 s CAUTION, EXHAUST, AIRLOCK, VENT (C2 5:50) | nejistě | ano: hodně (`021406`, `021456`, `021635`) | ~15 šablon `xst_*` u hardwaru, 40 průvodních štítků, štítky ve 128 decalech shluků | 3,4 cm: ~2 m; 7 cm: ~5 m | decal; jen u hardwaru, který jmenuje |
| Výstražné značení | ne | málo: trojúhelníky a šipky (Starlifter), DANGER a šrafy na panelu (MOLE 0:32) | nejistě | ano (`021422`, `021545`) | pruhy, trojúhelníky a šipky v hero, shlucích a coverage; šipky u víček | 5–10 m | decal; jen u skutečného nebezpečí (výfuk, podvozek, hrana rampy, sání) |
| Poklopy | nejistě | ano: ohraničené poklopy (Starlifter, Gladius) | nejistě | ano: geometrie (C2 5:00) | 54 `hatch_small` + 108 zámků (decal), 6 v hero | ~10 m (tvar) | velký servisní poklop geometrie (spára), malý decal |
| Mřížky, žaluzie | ano: velká sání (Arrow `093924`) | ano: perforace (Starlifter); žaluzie MOLE jsou normálový decal (MOLE 0:32) | nejistě | ano: geometrie (C2 5:00) | větrací skříně (geometrie), `vent_grille` 3, `louvers` 2, `vent_small` | skříň 28 m, decal ~5 m | velké sání geometrie, žaluzie a perforace decal |
| Rozvody a hadice na trupu | ne (Starlifter, Gladius, Guardian, Arrow) | ne (tytéž) | nejistě | ano (`021422`, `021456`) | konduity podél páteře (8 běhů), boční S (2 × 2), trubky gondol | ~10 m | v exteriéru SC nedoloženo: jen v odkryté mechanice, ne na otevřeném laku; interiér geometrie |
| Skříně, výstupky | ano: rozbíjí siluetu (Gladius koncept, `source.webp`, Perseus) | ano | nejistě | ano | větrací skříně (hřbet, záď), střední vrstva 57 k trojúhelníků | 28 m | geometrie, málo a velké, jen na funkčních místech |
| Panelové spáry | ano (všechny exteriéry, `093457`, `093924`) | ano: tenké pásy decalů, geometrie jen pár širokých drážek (C2 0:28–0:42) | nejistě | ano | geometrické mezery desek kitu + pásy `panel_lines` | 28 m (hlavní) | hlavní spáry geometrie, ostatní decal |
| Špína | ve hře jemná (C2 1:04) | ano: velké karty stékání (C2 0:50, 0:54, 8:00), otřené náběžné hrany (Starlifter 4K) | nejistě | ano (`021711`) | 16 karet (22 se zrcadlením) + procedurální v materiálu | 10–28 m | decal karty na místech, kde špína vzniká; materiál |
| Světla a poziční světla | ano: navigační, konce křídel, záře motorů (`093457`, `201804`, `093924`) | ano | nejistě | ano: ~790 světel C2 (C2 8:04) | navigační, ocasní, značkovací, světlomety, pruhy, stroboskopy | 28 m+ | geometrie + světlo |

## Věci, které v SC doložené nejsou a vygenerovalo je u nás pravidlo (jen návrh, nic neodstraněno)

1. **Čísla desek na K/L/U/N (a R/S)**, `D-R-PANEL-NUMBERS` v `exterior_kit_layout.py`: 68 drobných čísel.
   - SC má jedno velké číslo na panelu nebo registraci; drobné číslo na každé desce nemá žádný podklad.
   - Ve hře jsou čitelná až ze ~2 m.
   - Návrh: zrušit, nebo nahradit 4–6 velkými čísly (≥ 15 cm) na hlavních panelech hřbetu a boků.
   - Falešné kódy `panel_A12…` z `coverage` patří sem také.
2. **Štítky u poklopů** (`rule_companions`): štítek nad každý poklop se losuje z celé sady štítků, takže nejmenuje
   hardware pod sebou. To odporuje pravidlu kitu „service_labels jen u hardwaru, který jmenují“.
   - Návrh: štítek jen tam, kde poklop má známý účel z dat (ID funkčního prvku), jinak žádný.
   - Madlo u každého poklopu (`handle`) a červená značka (70 %) jsou rovněž bez podkladu: nejistě.
3. **„Držáky“ u víček**: `bracket_chance` 0,8 dává `chevrons_port` k zásuvkám a víčkům. V SC to nemá podklad.
   Návrh: vynechat, šipky jen u plnicích míst (palivo, `xst_qtfuel`).
4. **Text na dveřích rampy** `xst_ramp` „RAMP – STAND CLEAR“:
   - exteriér SC: nejistě (máme jen nápis BRIDGE na podlaze tunelu C2, C2 6:58, tedy interiér);
   - výstražný pruh na hraně rampy je obhajitelný, text na dveřích ne;
   - návrh: ponechat do rozhodnutí autora, ověřit na referenci rampy SC.
5. **Shluky šablon** (`clusters`, 128 decalů): náhodný rozptyl štítků, šipek a nýtů kolem servisních míst.
   - SC soustředí hustotu do funkčních míst (KOK 3:28), takže princip sedí.
   - Náhodné štítky ve shluku ale nejmenují nic konkrétního.
   - Návrh: ve shlucích jen strukturní položky (nýty, značky), text jen u hardwaru.
6. **3 408 šroubů kitu jako decal**: v exteriéru SC se šrouby nedoložily ani ve 4K renderu.
   - Ve hře jsou vidět od ~5 m, z chase kamery vůbec ne.
   - Návrh: šrouby jen u zdvojovacích plechů, závěsů a poklopů, plochou desku nechat bez nich.
   - Data a výkresy si body šroubů ponechají (pro interiér a zblízka).
7. **Konduity na otevřeném hřbetu a bocích**: v exteriérech SC nejsou. Odkrytá mechanika (pod motorem, C2 1:55) je
   jiný případ. Vynechat je nenavrhuji (jsou ve schválených výkresech E), jen je označuji jako odchylku od
   reference ke schválení autorem.

## Návrh pravidla „detail, který platí“ (pro `ship-pipeline` 3b3 a budoucí `new-ship`)

**Tři otázky.** Každý prvek detailu musí mít tři odpovědi „ano“, jinak se nestaví. Odpovědi se zapíšou do `purpose`
prvku v datech návrhu.
1. **Reference:** je v referenci SC? Uvést snímek nebo video s časem. „Nejistě“ = neprochází, dokud to autor
   nepotvrdí.
2. **Viditelnost:** uvidí to hráč v některé hrací vzdálenosti? Rozhoduje výpočet podle kamery: tvar ≥ 4 px,
   písmo ≥ 8 px výšky znaku. Hrací vzdálenosti: chase 28 m, blízko 5–10 m, obcházení 1–3 m, interiér.
3. **Účel ve čtení:** mění to čitelnost siluety, hierarchie (co je hlavní a co doplněk) nebo materiálů? Nebo to
   pojmenuje skutečný hardware (štítek u věci, kterou jmenuje)?

**Rozpočet detailu na vrstvu.** Stavba počty hlásí a test je hlídá, podobně jako dnes rozpočet trojúhelníků.

| Vrstva | Čte se z | Velikost | Provedení | Rozpočet |
|---|---|---|---|---|
| Velká | chase 28 m | ≥ 25 cm (≥ 10 px) | geometrie: silueta, hlavní spáry, sání, skříně, světla | jen funkční prvky z dat; každý s ID a účelem |
| Střední | 5–10 m | 5–25 cm | geometrie nebo normálový decal: poklopy, žaluzie, NO STEP, registrace, velká čísla, výstrahy | na panel nejvýš 2; velké plochy klidné (spára a zrno materiálu stačí) |
| Malá | 1–3 m a interiér | < 5 cm | decal: šrouby, drobný text, značky | jen u hardwaru, který doplňuje (poklop, závěs, zdvojovací plech, plnicí místo); na ploché desce 0 |

**Doplňky pravidla**
- Hustota se soustředí do shluků u funkčních míst, velké plochy zůstávají klidné (C2 KOK 3:28).
- Žádný text bez věci, kterou jmenuje.
- Žádné náhodné losování typu štítku: typ plyne z dat prvku.
- Interiér smí malou vrstvu mít hustší (SC interiéry, `021406`, `021554`), protože ho hráč vidí z 1–3 m.

**Otevřené body**
- Exteriér SC obcházený pěšky (1–3 m) chybí v referenci. Doplnit snímky ze hry (autor) nebo rozbor videa; do té
  doby malá vrstva exteriéru jen podle bodu 3.
- Návrhy 1–7 výše čekají na rozhodnutí autora. Pokud autor rozhodne, mění se recept a data exteriéru, což dělá
  hlavní session.
