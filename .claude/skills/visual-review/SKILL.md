---
name: visual-review
description: The independent visual critic for every handover of visual work in gamespace (author's rule of 25. 9. 2026) - review.json, compare sheets and brief.md from Tools/Review/make_compare_sheet.py, the visual-critic subagent (.claude/agents/visual-critic.md), rounds and the verification round, reacting to every point, evidence crops, the review file in Docs/Reviews/, the critic checklists (exterior, interior, cockpit) and the calibration log Docs/Reviews/calibration.md. Load before handing any visual result (ship, interior, kit part, cockpit, effect) to the author, or when changing the critic's brief or checklists.
---

# Vizuální kritik před každým předáním

Nezávislý podagent `visual-critic` (`.claude/agents/visual-critic.md`, jen čtení, nejsilnější model) porovná
výsledek s referencí dřív, než ho uvidí autor. **Doplňuje** automatické kontroly (`test_ship_geometry.py`, testy UE),
nenahrazuje je: musí proběhnout obojí. `test_ship_geometry.py` běží sám jako poslední krok `hs_assemble_ship.py`
(autor 27. 9. 2026); při FAIL přestavba skončí kódem 1 (`HSASSEMBLE GEOTEST FAIL`).

## Postup

1. **Snímky** pro kola kritika z rychlé smyčky `.\Tools\Shots.ps1 -Preset <x> -Editor` nebo rendery z Blenderu,
   ne z balení hry (autor 28. 9. 2026). Zabalí se jednou na konci kroku.
2. **Srovnávací listy:** `review.json` (téma, cíl, styl, sekce checklistu, dvojice reference / výsledek) →
   `python Tools/Review/make_compare_sheet.py <review.json>` → `Docs/Reviews/<datum>_<téma>/` (listy + `brief.md`).
   Reference vlevo, výsledek vpravo; zblízka, střední vzdálenost (chase nebo z oka) a zdálky; den, noc a vesmír,
   kde to dává smysl. U interiéru pohled z oka a zezadu, zblízka ovladače.
3. **Stylový záměr kroku** (např. „udržovaná pracovní loď: panely téměř čisté, špína jen tam, kde vzniká“) patří
   do `goal`/`style` briefu, aby kritik nechtěl víc, než je záměr.
4. **Spusť kritika.** Dostane **jen** `brief.md` a listy: žádný popis postupu, doby práce, záměrů ani vlastní názor.
   Prompt: „Přečti <složka>/brief.md a všechny listy v něm a vyhodnoť je podle svého zadání.“
5. **FAIL** → oprav body „musí se opravit“, nové snímky, nové listy, kritik znovu. **Nejvýš 3 kola**, pak předej
   i s otevřenými body.
6. **Ověřovací kolo:** když po posledním kole ještě opravuješ, spusť na opravené body jedno kolo jen na ně (listy jen
   s nimi, brief „ověř tyto body“); do limitu 3 kol se nepočítá (autor 26. 9. 2026).
7. **Žádnou výtku tiše nevynechat.** U každé: opraveno / neopraveno a proč. Nesouhlas je v pořádku, ale zdůvodněný.
   Každou výtku ověř na snímku v plném rozlišení: kritik občas přehlédne malý detail na vlastním listu.
8. **Neplatnou výtku dolož výřezem** ze snímku (PIL: výřez, zvětšení, popisek nahoře s číslem kola a bodu).
   Výřezy do `Docs/Reviews/<datum>_<téma>/evidence/` (autor 25. 9. 2026).
9. **Recenze** do `Docs/Reviews/<datum>_<téma>.md`: odkaz na listy, výstup kritika z každého kola, reakce na každý bod.
10. **V reportu autorovi:** verdikt a skóre posledního kola, počet kol, výtky s reakcí, odkaz na recenzi.
11. **Kalibrace:** když autor vytkne něco, co kritik přehlédl, doplň to do zadání kritika nebo do checklistu níže
    a zapiš do `Docs/Reviews/calibration.md`.

- Když se skóre přes kola hýbe jen o bod, lokální opravy nestačí: hierarchii detailu, materiály a světlo drží
  systémové věci (kit, rozmístění světel, decaly špíny, variace drsnosti).
- Cena: kritik ~3–4 min na kolo, listy ~1 min; dražší jsou opravy mezi koly.

## Checklisty (čte je `make_compare_sheet.py`, klíč `checklist` v `review.json`)

<!-- critic-checklist:exterior -->
- Povrch: rovné panely a čisté, zkosené hrany, které chytají světlo. Žádné měkké, zvlněné nebo
  rozeklané plochy.
- Tvar vrstvený z dílů s tloušťkou (desky nad rámem, zapuštěná místa, odhalená mechanika, trubky,
  stupně). Hierarchie velký / střední / malý detail, zvlášť střední vrstva.
- Detail je skutečný tvar nebo mesh decal s hloubkou, ne jen čáry na hladkém povrchu.
- Materiály: primární a sekundární lak, holý kov, guma, tmavé mechanické díly; variace drsnosti.
  Opotřebení jen na exponovaných hranách.
- Decaly: čísla panelů, šablonové nápisy, výstražné pruhy, šipky, nýty. Shlukované, čitelné, nikdy
  zrcadlené.
- Světla lodi: poziční světla, osvětlené šachty, emisivní prvky dávají měřítko; nic přepáleného.
- Silueta odpovídá výkresu / konceptu; nic netrčí šikmo, nic nevisí.
<!-- /critic-checklist -->

<!-- critic-checklist:interior -->
- Tvar prostoru vychází z trupu: zalomené a zkosené stěny, nízký konstrukční strop, průřez spíš
  lichoběžník / osmiúhelník. Pravoúhlá místnost s rovnými stěnami je chyba.
- Vrstvy: žebra, kabelové žlaby a trubky pod stropem, panely s hloubkou a přesahy, madla, skříňky
  se západkami, mřížky v podlaze, přípojky. Detail shlukovaný kolem funkčních míst.
- Každý předmět má účel; žádné výplňové rekvizity, žádné krabicové pulty.
- Materiály: čalounění, guma, broušený i lakovaný kov, akcenty palety; tmavá teplá architektura,
  studené UI. Béžová / jednolitá / plastová plocha je chyba.
- Decaly: označení místností a sekcí, nouzové značky, popisky ovladačů; čitelné, nezrcadlené.
- Světlo: kontrast, svítidla v pouzdrech, kužely, tmavá místa, akcenty. Ploché rovnoměrné světlo
  ze stropu je chyba, stejně jako přepálená skvrna.
- Geometrie: žádné díry do prázdna, průniky stěnou, plovoucí díly, lišty mimo místo.
<!-- /critic-checklist -->

<!-- critic-checklist:cockpit -->
- Z oka pilota: kolik je vidět ven, jak tlustý je rám skla, jestli výhled neblokuje hmota (rám,
  police, deska). Nic nesmí stát v ose pohledu.
- Palubní deska: tvarovaná, nízko, s hloubkou. Displeje zabudované do desky nebo jako skleněné
  panely na držácích, ne samostatné desky položené na stole.
- Fyzické ovladače: skutečné typy (kryté přepínače, otočné voliče, kolébky, podsvícená tlačítka),
  každý s popiskem. Holé válce, kulaté tečky nebo prázdné desky jsou placeholdery.
- Materiály: tmavý grafit kolem displejů, světlé jen akcenty; polstrování, kov, guma. Tvary nesmí
  zmizet v černé.
- Světlo: displeje a hologram svítí na okolí, ostrůvky světla, žádné přepálené skvrny; tvary čitelné
  ve dne i v noci.
- Čitelnost HUD a displejů má přednost před vším ostatním; žádné zdvojení nebo rozmazání.
- Zadní pohled (dveře, stěna, okna): text nezrcadlený, stěny s detailem, čisté spoje stěny a skla,
  žádné čáry přes okno.
- HOTAS, sedadlo a hologram: detailní, ukotvené, žádné díly ve vzduchu.
<!-- /critic-checklist -->
