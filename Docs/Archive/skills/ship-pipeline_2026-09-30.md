# Archiv skillu `ship-pipeline` (přesunuto 30. 9. 2026)

Doslovně přesunuté oddíly z `.claude/skills/ship-pipeline/SKILL.md` (commit 44c26cc): měření a testy z jednotlivých
dnů, rozbory referencí SC s hodnotami Wayfareru „před/po“ a cena kritika. Závěry a pravidla z nich zůstaly ve
skillu (zkráceně); postup kritika je ve skillu `visual-review`. Archiv není zdroj aktuálního stavu.

## Test konzistentních pohledů přes Higgsfield (24. 9. 2026)

## 2a. Konzistentní pohledy přes Higgsfield MCP (ověřeno 24. 9. 2026)

Test na procedurálním modelu první stíhačky (17,58 × 12,96 × 4,36 m), aby šel každý pohled změřit proti
skutečnému modelu. Testovací soubory, prompty a listy rozdílů byly smazány spolu s lodí (24. 9. 2026);
historie je v gitu, commit `2919d8a`. Naměřené výsledky platí dál:

| Varianta (IoU proti modelu) | bok | zepředu | shora | uzávěr | rozpětí/výška proti spec |
| --- | --- | --- | --- | --- | --- |
| GPT Image 2.5, jen hero obrázek | 0,79 | 0,29 | 0,65 | 24 % | −37 % / +4 % |
| GPT Image 2.5, list 2 × 2 v jednom obrázku | 0,22 | 0,56 | 0,58 | 138 % | nepoužitelné |
| Nano Banana Pro, jen hero (zepředu po `remove_background`) | 0,82 | 0,73 | 0,76 | 15 % | −4 % / +9 % |
| GPT Image 2.5 + vodicí silueta | 0,89 | 0,54 | 0,92 | 17 % | −3 % / +5 % |
| **Nano Banana Pro + vodicí silueta** | **0,97** | **0,90** | **0,98** | **0,3 %** | **0,1 % / 0,4 %** |

Co z toho plyne:
- **Bez vodítka si model domyslí půdorys** (GPT udělal křídla dopředu šípová a o třetinu kratší) a „zepředu“
  kreslí seshora šikmo. Hezký obrázek neznamená správný tvar – vždy měř.
- **List všech pohledů v jednom obrázku nepoužívej**: pohledy mají každý jiné měřítko, přetékají přes
  buňky a půdorys neodpovídá boku.
- **Vodicí silueta jako druhá reference** („The second image is the exact orthographic … silhouette of this
  ship … must match exactly“) je hlavní páka. **Výchozí volba: Nano Banana Pro + vodítko** – siluetu
  drží téměř přesně a přitom kreslí skutečný povrch a barvy z hero obrázku. U nové lodi vodítko vzniká
  z našeho 2D návrhu (obrys paluby z `<Loď>_layout.json`, profil z řezu), ne z AI.
- Pohled **zepředu je nejslabší** (tenká křídla = malý posun rozhodí IoU). Nano Banana v něm nakreslil
  navíc dvě plovoucí špičky ploutví nad lodí – měření je jako odtržené skvrny zahodí, ale obrázek
  do multi-image to 3D takhle nesmí → přegenerovat, nebo poslat jen bok + shora + 3/4.
  **Každý pohled si před použitím prohlédni** (Read na PNG), číslo nestačí.
- Modely někdy kreslí podlahu a stín i přes „no floor“ → před měřením `remove_background` (Higgsfield,
  výstup s alfou, `extract_reference_mask` alfu použije).
- **Světlý trup na světle šedém pozadí** rozbije vyříznutí siluety (díry, falešné IoU 0,56). Generuj na
  pozadí kontrastním k trupu (světlý trup → „plain uniform dark charcoal background“), jinak `remove_background`.
- Model rád „zjednoduší“ půdorys (Wayfarer: gondoly přilepené k trupu, rozpětí −20 %). Pomohla třetí
  reference (pohled zepředu, kde gondoly stojí zvlášť) a slovní popis rozestupu; nebo prompt „Fill the dark
  silhouette in the first image with the starship from the second image“ (vodítko jako první reference).

## Rozbory referencí SC (24.–26. 9. 2026)

**Rozbor lodí SC v Blenderu** (Markom3D: C2 Hercules exteriér a kokpit, Argo MOLE; poznatky s časy
`starcitizenreference/ShipDetailing_VideoNotes.md`, 26. 9. 2026):
- Trup bez decalů je skoro hladký, panelové linky jsou pásy decalů (to děláme). Žaluzie, logo, velká čísla a
  výstrahy na MOLE jsou decaly na rovném laku.
- **Velké karty špíny** 1–4 m se stékajícími šmouhami nad motory, přes křídla a svislé plochy. U nás chybí,
  špína je jen procedurální v materiálu.
- **Lak bez opotřebení hran.** Špinavý dojem dělá drsnost (dlaždicová textura šmouh a škrábanců), ne barva ani
  otřené hrany. Náš `EdgeWear` 0,8 je proti SC příliš.
- Natažené úseky atlasu: dlouhé čáry z jednoho malého kusu textury.
- **Zavedeno (26. 9. 2026):**
  - karty špíny `decals.grime` (`Placer.card`, atlas `generate_grime_textures.py`, master `meshdecal_grime`,
    buňka 8 cm, měkký okraj přes vertex colour, `up` = odkud špína jde);
  - `EdgeWear` 0,15 a `ClearCoatRoughVariation` 0,12;
  - recenze `Docs/Reviews/2026-09-26_sc_breakdown_tasks.md`.

**„Feel“ SC: rozbor referencí** (Docs/UI screenshoty Titan, Guardian, Hornet, Cutlass, Spirit; ship matrix Pisces,
100i, Mustang, Aurora; porovnáno se stejných vzdáleností, 24. 9. 2026):

| Kategorie | SC má | Wayfarer měl (před) | Chybělo / co jsme udělali |
| --- | --- | --- | --- |
| Hodnotová stavba (zdálky) | 30–60 % plochy tmavé: grafitové zóny, tmavý podvozek mezi bílými deskami; loď se čte i jako silueta dvou tónů | ~95 % bílé, tmavý jen nos a záď | **nejdůležitější** – livrej (analytické zóny, 3 varianty) |
| Povrch (zblízka) | lesklý lak s clear coatem, odráží oblohu a okolí; sousední desky se liší tónem a leskem | matný lak, všechny desky stejné | clear coat 1 / 0,05; variace po panelu (UV1), 8 % kovových a 5 % karbonových panelů |
| Spáry | tmavé pryžové/stínové spáry 0,5–1 cm, rámují každý panel | světlé drážky splývaly s lakem | těsnění v drážkách (materiál Seal) |
| Velké značení | jméno / registrace přes část boku, logo výrobce, velké výstražné zóny u trysek a rampy (1 až 4 m) | jen malé nápisy (≤ 0,6 m) | promítané decaly WAYFARER, HF-0417, logo Halcyon, EXHAUST / RAMP |
| Manévrovací trysky | 12–30 bloků na malé lodi, na přídi, bocích, zádi, spodku i hřbetu | žádné | 26 bloků RCS (`hs_functional.py`) |
| Antény, senzory | 2–5 na loď (lopatka, bič, kopule) | 1 senzorový kit | 2 lopatky, bič, 2 kopule |
| Mechanika zvenku | závěsy klapek, písty, objímky zbraní, přípojky | kryty klapek, holé hlavně | závěsy, objímky zbraní, přípojky |
| Malé decaly | 0,5–2 / m² na klidných plochách, 5–10 / m² u servisních míst | ~0,8 / m² | beze změny (hustota už odpovídá) |
| Světla | pozice, obrys, reflektory, pásy; často modrobílé emisní lišty | pozice, obrys, reflektor, šachta | (další krok: emisní lišty podél trupu) |
| Siluetové vrstvy | hluboké převisy, negativní prostor mezi deskami | hladký loft s deskami 2–3 cm | (omezeno výkresem; siluetu nesmíme měnit) |

Závěr: rozdíl ve „feelu“ dělá hlavně **hodnotová stavba a lesk**, až potom počet detailů. Livrej a clear coat
mají největší efekt ze všech vzdáleností.

**„Feel“ SC uvnitř: rozbor referencí interiérů** (21 autorových snímků `starcitizenreference/Screenshot
2026-09-25 02*.png`: Argo, MISC, RSI, Origin, Drake, Crusader, obytné moduly i chodby; 25. 9. 2026). Autor
na jejich kvalitu míří. Wayfarer v1 (hs_interior.py, boxy z půdorysu) autor odmítl: „prázdný byt nebo kancelář“.

| Kategorie | SC má | Wayfarer v1 měl | Chybí / co s tím |
| --- | --- | --- | --- |
| Tvar prostoru | průřez lichoběžník nebo osmiúhelník, zkosené horní rohy, strop 2,1–2,4 m, portály (rámy) každých 1–2 m lámou délku | pravoúhlý box 3,8 × 2,3 m, rovný strop | zkosení nahoře, portál na každém modulu kitu |
| Konstrukce | odhalená žebra a nosníky, příhradový strop (Drake), kabelové svazky ve žlabech (žluté u MISC), potrubí s objímkami, vzduchotechnika | tenká žebra zapuštěná ve stěně | stropní žlab s kabely a trubkami, žebra přes celý profil |
| Vrstvy stěny | 3 roviny: nosná konstrukce, panely s přesahem 2–8 cm, výbava na panelech; panely 0,6–1,2 m, dělené spárou | jedna rovina, velké plochy | díly kitu (trim sheet s normálovou mapou), přesahy, lišty |
| Vybavení | skříňky se západkami, madla, hasicí přístroj, výdejník, obrazovka na rameni, lavice s čalouněním, žebřík; **ve shlucích** u dveří, konzolí, lůžka, techniky, mezi nimi klid | kvádry předmětů z půdorysu | výbava podle funkce místa, shluky, klidné plochy mezi |
| Materiály | lakovaný kov ve 2–3 tónech, holý kov na hranách, prošívané čalounění (Argo, Drake), gumová a děrovaná protiskluzová podlaha, karbon (RSI), barevný akcent výrobce (Argo oranž, RSI modrá, Drake žlutá) | jednolité plochy jednoho materiálu | trim textury kitu přetónované do palety, oranžový akcent Halcyonu, guma, čalounění |
| Decaly | velká čísla sekcí a dveří (01, 02), logo výrobce na stěně, výstražné pruhy u prahů a rampy, šipky, štítky CAUTION, čáry na podlaze | žádné | promítané decaly interiéru: místnosti, sekce, nouzové značky, šipky, pruhy |
| Světlo | kontrast: svítidla v pouzdrech (lišty ve zkosení, kruhová stropní), kužele a tmavé kouty, akcentová a orientační světla u podlahy, displeje a kontrolky; teplé 3000–4000 K proti studeným displejům | rovnoměrně svítící strop, bodovky bez pouzder | světla v pouzdrech kitu, směrová, tmavá místa mezi nimi, akcent u podlahy |
| Hustota detailu | 3 úrovně: velké (portály, panely), střední (skříňky, madla, ventilace 0,2–0,5 m), malé (šrouby, kontrolky, štítky 1–5 cm) | jen velké | všechny tři úrovně, malé hlavně u funkčních míst |

Závěr: interiér SC stojí na **konstrukci a vrstvách** (profil, portály, žlaby, panely s hloubkou) a
**kontrastním světle**. Předměty jsou až třetí vrstva. Postup: modulární kit (Quaternius, CC0) jako nosná
vrstva, procedurální přesný detail a decaly navíc (`Docs/AssetPipeline_Modular.md`).

**Kabina (kokpit) SC: rozbor a cílová čísla** (25. 9. 2026). Hlavní reference `cockpit_reference_holo.png`
v repozitáři není; náhradou autorových 5 snímků kokpitů SC `starcitizenreference/cockpit_reference_1..5.png`
(1, 2, 4 lehká stíhačka ve vesmíru / ve dne / v noci, 3 luxusní kabina, 5 těžký rám). Cíl = medián.

| Kategorie | SC má | Wayfarer má (po konceptu A) | Chybí |
| --- | --- | --- | --- |
| Displeje | tenké skleněné panely, průhledné, svítí jen obsah, tenký technický rám s podsvíceným okrajem, na držácích; často jeden široký panel pod linií pohledu (3, 5) | dva MFD v tlustých chromových rámečcích, neprůhledné tmavé pozadí | sklo, průhlednost, edge light, držáky, široký centrální panel |
| Fyzické ovladače | moduly (pods) s pouzdrem, rámem, šrouby a štítkem; páčky s kryty, voliče s drážkováním, kolébky, řady podsvícených tlačítek (12–18 mm), popisky u všeho | kulaté tečky a holé válce, pár kláves | skutečné tvary se zkosením, moduly, popisky |
| Kontrolky | desítky LED v řadách, oranžové a bílé, některé blikají | pár emisivních teček | řady LED, blikání |
| Palubní deska | nízká (horní hrana 23–47 % výšky obrazu od spodu, medián 35 %), mělká, dva moduly po stranách a střed otevřený dolů | horní hrana 39,8 % | mírně snížit a zúžit |
| Rám skla | skoro bezrámová kabina (1–4): jen tenký rám nahoře (0,4–0,7 % šířky), nic v pásu ±15° kolem pohledu; těžký rám (5) má sloupky 3,5 % | středový kříž nahoře, plné boční stěny, výhled 24,5 % | tenký rám, bez kříže, větší skla (cíl výhledu medián 62 %, rozsah 45–75 %) |
| Hologram lodi | vlastní loď jako modrý aditivní hologram vlevo nahoře (1, 2, 3) mimo pohled | drátěné kroužky radaru | hologram z meshe lodi |
| Světlo | tmavá kabina, světlo hlavně z displejů, hologramů a kontrolek, tlumené akcenty | světlá krémová kabina, výplňová světla | tmavší základ, ostrůvky světla |
| Barvy materiálů | tmavý grafit / gunmetal kolem displejů, světlé jen akcenty (3 bílá luxusní výjimka) | krémový rám kolem displejů | tmavé kolem displejů, krém jako akcent |

Změřeno (1920×1080, `Tools/Blender/eye_view_metrics.py`, reference odečtené z mřížky):

| Veličina | Ref 1 | Ref 2 | Ref 3 | Ref 4 | Ref 5 | **Medián (cíl ±15 %)** | Wayfarer před | Wayfarer po kroku 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Výhled ven (% plochy) | 62 | 51 | 75 | 62 | 45 | **62 (53–71)** | 24,5 | 60,8 |
| Horní hrana desky (% od spodu) | 38 | 47 | 23 | 35 | 28 | **35 (30–40)** | 39,8 | 35,3 |
| Nejširší sloupek v poli (% šířky) | 0,4 | 0,7 | 0,5 | 2 | 3,5 | **0,7** (≤ 2 přijatelné) | 42,1 (plné boční stěny) | 2,3 |
| Sloupek v pásu ±15° | ne | ne | ne | ne | ne | **ne** | ne | ne |

Krok 2 (25. 9. 2026): sklo začínalo 1–1,3 m nad okem, takže víc skla nepomohlo. **Oko musí sedět v pásu skla.**
Kokpit se proto zvedl o 0,8 m: podlaha 1,15, oko 2,45, schody z kabiny. Dál:
- zrušená podélná páteř a přední vzpěra (ležela v horizontu), vzpěry 6 cm;
- horní trysky RCS ze skla na nos;
- deska o 5 cm níž.

Exteriér a silueta zůstaly stejné. Měření `eye_view_metrics.py` čte oko ze `SOCKET_Cockpit` otevřeného blendu.

## Vizuální kritik: původní oddíl 7b (před přesunem do skillu `visual-review`)

## 7b. Vizuální kritik před každým předáním (autor 25. 9. 2026)

Nezávislý podagent `visual-critic` (`.claude/agents/visual-critic.md`, jen čtení, model Fable 5.1, effort
max) porovná výsledek s referencí dřív, než ho uvidí autor. Doplňuje automatické kontroly
(`test_ship_geometry.py`, testy UE), nenahrazuje je: musí proběhnout obojí.
`test_ship_geometry.py` běží sám jako poslední krok `hs_assemble_ship.py` (autor 27. 9. 2026); při FAIL přestavba skončí
kódem 1 (`HSASSEMBLE GEOTEST FAIL`).

Postup:
1. Srovnávací listy: `review.json` (téma, cíl, styl, sekce checklistu, dvojice reference / výsledek)
   → `python Tools/Review/make_compare_sheet.py <review.json>` → `Docs/Reviews/<datum>_<téma>/`
   (listy + `brief.md`). Záběry zblízka, ze střední vzdálenosti (chase nebo z oka) a zdálky; den,
   noc a vesmír, kde to dává smysl.
2. Spusť kritika. Dostane **jen** `brief.md` a listy. Žádný popis postupu, doby práce, záměrů ani
   vlastní názor na výsledek. Prompt: „Přečti <složka>/brief.md a všechny listy v něm a vyhodnoť
   je podle svého zadání.“
3. FAIL → oprav body „musí se opravit“, nové snímky, nové listy, kritik znovu. Nejvýš 3 kola, pak
   předej i s otevřenými body. Opravy po posledním kole ověř jedním kolem jen na opravené body (listy
   jen s nimi, brief „ověř tyto body“); do limitu se nepočítá (autor 26. 9. 2026).
   Když se skóre přes kola hýbe jen o bod, lokální opravy nestačí: hierarchii detailu, materiály
   a světlo drží systémové věci (kit, rozmístění světel, decaly špíny, variace drsnosti).
4. Žádnou výtku tiše nevynechat. U každé: opraveno / neopraveno a proč. Nesouhlas je v pořádku,
   ale zdůvodněný.
5. Recenze do `Docs/Reviews/<datum>_<téma>.md`: odkaz na listy, výstup kritika z každého kola,
   reakce na každý bod.
6. Výtku, kterou označíš jako neplatnou, dolož výřezem ze snímku (PIL: výřez, zvětšení, popisek
   nahoře s číslem kola a bodu). Výřezy do `Docs/Reviews/<datum>_<téma>/evidence/` (autor 25. 9. 2026).
7. Cena: kritik ~3–4 min na kolo (kokpit v2: 190 s, 177 s, 214 s), listy ~1 min. Dražší jsou opravy
   a nové balení mezi koly (~12 min). Kritik občas přehlédne malý detail na vlastním listu (throttle,
   popisky), proto se každá výtka ověřuje na snímku v plném rozlišení.
6. V reportu autorovi: verdikt a skóre posledního kola, počet kol, výtky s reakcí, odkaz na recenzi.
7. Když autor vytkne něco, co kritik přehlédl, doplň to do zadání kritika nebo do checklistu níže
   a zapiš do `Docs/Reviews/calibration.md`.

Kalibrace na historii (pět verzí, které autor zkritizoval): `Docs/Reviews/calibration.md`.
