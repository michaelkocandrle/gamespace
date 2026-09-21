# Quantum travel – poznatky z referenčního videa (21. 9. 2026)

Zdroj: YouTube `vF2pkgvwf-M` („Step-by-Step Quantum Travel Tutorial | Star Citizen 101“, 8:28,
staženo 3840×2160 60 fps). Video i snímky jsou jen lokálně v `ArtSource/Reference/Video/sc_quantum_travel_tutorial/`
(necommitují se), stáhne je znovu `python Tools/Reference/fetch_video.py <url> sc_quantum_travel_tutorial`.
Časy níže odkazují na snímky `frames/tHH_MM_SS.jpg`.

## 1. Průběh skoku (co hráč dělá a co vidí)

| Fáze | Čas | Co se děje | HUD |
| --- | --- | --- | --- |
| Cíl | 2:00–3:14 | Mapa hvězdného systému (F2), výběr cíle, „Set route“. Trasa je oranžová čára, panel QUANTUM TRAVEL ukazuje cíl, čas letu (0h 2m 4s) a vzdálenost (19.06Gm). | celoobrazovková mapa |
| Natočení | 3:18–3:44 | Pilot natáčí nos na cíl. Na HUD je značka cíle a šipka ukazující, kam se otočit. | značka cíle (kolečko, jméno, vzdálenost v Gm), šipka k cíli mimo zorné pole |
| Režim QT | 3:48 | **B** přepne do quantum režimu. | svislé a vodorovné modré čáry na krátkou chvíli „orámují“ pohled (přechod režimu) |
| Spool | 3:50–3:56 | Drive se nabíjí. | zelený rámeček nahoře `SPOOLING 37%`; kolem cíle dva velké oblouky, dokud se nezarovná, jsou modrofialové |
| Kalibrace | 7:26–7:30 | Zarovnání na cíl (když je cíl blízko středu). | `CALIBRATING 34%`, pak `READY` |
| Připraveno | 3:58–4:08 | Drive připraven, nos míří na cíl. | `READY`, **oblouky zezelenají** a na jejich středu se objeví zelené šipky `> <` ukazující na cíl |
| Skok | 4:10 | **Podržet levé tlačítko myši.** | záblesk: modrá koule světla před nosem, zelené paprsky rozletí z úběžníku |
| Let | 4:12–5:00 | Tunel; nejde řídit (video to říká výslovně). | `READY` zůstává; na displeji `QT EXIT`; značka cíle ve středu |
| Výstup | 5:02 | Loď vypadne do normálního prostoru u cíle (nebo po přerušení). | `COOLING 18%`, **celá značka cíle a okolní objekty zčervenají**, dokud drive nevychladne; pak zase `READY` |
| Příjezd | 7:44 | U planety: tenká jasná atmosféra na obzoru (dobrá reference pro planety). | |

Chyby, které video jmenuje: málo paliva, poškozený drive, cíl zakrytý (planeta v cestě), bug.
Palivo: samostatný ukazatel „QD Fuel“ (1:00), klesá během skoku.

## 2. Vzhled tunelu (zvenku 0:00–1:40, z kokpitu 4:12–5:00)

- **Tma, ne černo:** pozadí je mlžná tmavě modrošedá, místy do fialova, s měkkými širokými
  světelnými pruhy sbíhajícími se k úběžníku. Jas se pomalu přelévá, jak pruhy rotují.
- **Čar je málo.** Desítky tenkých, ostrých bílých čar, řídce rozesetých, různě dlouhých. Většina
  obrazu je čistá mlha. Naše první verze tunelu má čar zhruba pětkrát víc.
- **Zelené/tyrkysové paprsky:** krátké záblesky (asi jednou za 10–20 s) – několik širokých
  jasných paprsků z úběžníku na pár sekund, pak zase zmizí. Nejsilnější při vstupu do skoku.
- **Záře:** jasný bílý bod před nosem lodi (zvenku) a **modrá záře pod nosem / na přídi** (z kokpitu je
  to modrá kaluž světla na spodní hraně skla).
- **Modré jiskry z trupu:** husté modré „vlasy“ jisker proudí z hran trupu dozadu; zvenku
  výrazný prvek, z kokpitu téměř neviditelný.
- **Loď je silueta:** v tunelu je trup skoro černý, osvětlený jen zezadu modře.

## 3. Normální let

- V kokpitu při běžné rychlosti (3:18–3:44, otáčení lodi) **nejsou vidět žádné rychlostní čáry**.
  Prach, pokud vůbec, je sotva znatelný. Náš prach v SCM a NAV je výrazně nad referencí.
- Cruise jako samostatný režim ve videu není: dálkový přesun je jen quantum travel.

## 4. HUD styl (zvětšené výřezy 4K)

- Stavový rámeček nahoře uprostřed: zelený text velkými písmeny mezi dvěma svislými čárkami,
  tmavě zelené pozadí (`SPOOLING nn%`, `CALIBRATING nn%`, `READY`, `COOLING nn%`, `ONLINE`).
- Dva velké oblouky vlevo a vpravo od středu (asi třetina výšky obrazu), barva podle stavu:
  modrofialová (nepřipraveno), zelená se šipkami (READY), červená (chlazení).
- Značka cíle: tenké kolečko s ikonou, pod ním jméno a vzdálenost (`19.0Gm`) modrofialově.
- Ostatní objekty systému jako malé ikony kolem; v chlazení všechny červeně.
