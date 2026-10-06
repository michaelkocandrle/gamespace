# Workflow továrny dílů – v0 (návrh, 6. 10. 2026, čeká na schválení autorem)

**Cíl:** každý díl jednou na úroveň etalonu SC (`Docs/Kit/etalon/etalon.md`), pak v každé lodi. Lodě se liší
paletou, doplňky a světly.
**Princip:** nejdřív 1–2 piloty celé (tvar, materiál, světlo, decaly, špína, funkce). Na nich se workflow odladí.
Zrychluje se jen podle naměřených dat (kap. 5).
**Vstupy:**
- etalon;
- 25 poučení `Docs/Kit/catalog_draft.md` (dál **P1–P25**);
- `.claude/skills/ship-interior/kit-design.md`;
- recenze chodby, kajuty a rampy.

Každý díl má složku `Docs/Kit/parts/<ID>/` s kartou `part.md` (zadání, cíle, metriky) a recenzí. Nové nástroje
v textu jsou označené **(nový)**; postaví se v pilotu, ne předem.

## 1. Výroba jednoho dílu

| # | Krok – co se dělá | Čím | Výstup | Hotovo, když | Kontroly (poučení) |
|---|---|---|---|---|---|
| 0 | **Zadání:** kategorie, úroveň, cílové lodě a jejich rozměry z výkresů, rozměrová řada a varianty | výkresy lodí, `kit_rules.json`, `kit_parts.json` | karta `part.md` | každá cílová loď má rozměr, do kterého díl padne | P9 řada z výkresů; P13 uzel = samostatný díl |
| 1 | **Etalonová karta:** 3–4 kotevní záběry SC a měřené cíle v šesti rozměrech: vrstvy a hustota, materiály, světlo, decaly, špína, tvar | `etalon/sc/*.jpg`; když chybí záběr, požadavek na dotočení autorovi | tabulka cílů v `part.md` | každý rozměr má číslo nebo „nejistě“ | P2 cíle měřené, ne pocitové |
| 2 | **2D list dílu:** pohled, řez, detail profilu 1:5; obě polohy pohyblivých částí; pohled z oka (co je vidět); volné místo kolem | `Tools/Design` (nový `draw_part_sheet.py` podle `draw_interior_sheet.py`) | `ArtSource/Kit/Design/<ID>.png` + JSON | **autor list schválil** | P2 2D před 3D; P7 obě polohy, průchod 1,8 m, dosednutí; P8 0,5 m za dveřmi, řez trupem; P15 funkční prvek na líc; P16 obsah za mřížkou z oka |
| 3 | **Materiálový základ:** díl používá sdílený master + trim + zrno, žádný vlastní materiál | `M_Kit_*`, `kit_trim_sheet.py`; test limitů (nový `test_kit_materials.py`) | seznam slotů v `part.md` | test zelený: lak metallic ≤ 0,1, konstrukce ≤ 0,5, měkké plochy `pad()` | P1 základ před koly; P10 kov; P14 čalounění |
| 4 | **Blockout:** hrubá geometrie v rozměrech, jeden snímek z oka vedle etalonu | `Tools/Kit/kit_<dávka>.py`, `render_kit_closeup.py` | `closeup_<ID>_eye.png` | silueta a proporce odpovídají etalonu na listu vedle sebe | P3 tvar dřív než obsah; P18 `--python-exit-code 1`, čas blendu |
| 5 | **Detail:** vrstvy 2 a 3, decaly, špína, světlo v pouzdře podle světelného plánu kategorie | kit skript, knihovna decalů, `kit_layout.py` | díl v blendu + manifest | hustota vrstev podle karty; A/B snímek decalů a špíny (vyp / černá / bílá) | P5 A/B před laděním; P20 seřazené pořadí; P23 orientace nápisů; P24 atlas jen `append`, celá dávka |
| 6 | **UE a showroom:** import, snímky z pevné sady pohledů (kap. 3), změření vzhledu | `import_kit.py`, `Shots.ps1 -Preset part_<kat> -Editor`, `measure_look.py` | `shots:part_<ID>/…` | kvalita vynucená (v logu), čas FBX novější než blend, `measure_look` v rozsahu SC | P19 export a čas FBX; P22 `-Editor` a kvalita; P25 změna masteru = snímky všech lodí |
| 7 | **Výkon světel** v lodi (interiér i let, 3 běhy) | `Shots.ps1 -Preset kit_perf_profile` | čísla v `part.md` | bez stínů, cena zapsaná (neoptimalizuje se, jen se hlídá skok) | P12 |
| 8 | **Kritik proti etalonu:** list SC vlevo, díl vpravo, stejné vzdálenosti; brief s provizorními prvky a výřezy klíčových prvků | `make_compare_sheet.py`, `visual-critic` | recenze `Docs/Reviews/<datum>_part_<ID>.md` | PASS podle kap. 2, nebo 3 kola a otevřené body autorovi | P6 provizorní se nehodnotí; P11 výřez a poloha ke každému prvku; P4 protichůdnou výtku nejdřív změř; P1 2× ≤ 5 → systémový krok; P21 čitelnost = ray cast; P17 černé plochy = test jiného masteru |
| 9 | **Autorovo oko** ve hře: díl ve showroomu a v jedné lodi | `Package.ps1`, `Play.ps1`; scénář v odpovědi | verdikt autora | autor napsal „schváleno“ nebo výtky | – |
| 10 | **Zápis do katalogu** a metriky | `Docs/Kit/catalog.json` (kap. 4), `factory_metrics.csv` | záznam + metriky | stav `schválený`, metriky vyplněné | – |

**Pravidla mezi kroky**
- Krok se vrací nejvýš o jeden zpět.
- Když výtka kritika míří do kroku 2 nebo 3 (tvar, materiál), oprava jde tam, ne do detailu (P1, P3).
- Balí se jen v kroku 9 (P22).

## 2. Měřítko kvality

- **Hodnocení proti etalonu:** kritik dostane kotevní záběry z karty dílu a hodnotí šest rozměrů dílu:
  1. tvar a hierarchie,
  2. materiály,
  3. světlo,
  4. decaly a značení,
  5. špína a opotřebení,
  6. funkce a stavy.

  10 = nerozeznatelné od SC, 7 = stejná úroveň z oka hráče, 5 = správný směr s chybějící vrstvou.
- **Práh** (návrh, gate `part`):
  - pilot = všech šest ≥ 7 a žádný bod „musí se opravit“;
  - díl podle odladěného workflow = průměr ≥ 7 a žádný rozměr pod 6.
  - Dnešní `step` (6,5) zůstává pro místnosti.
- **Autorovo oko má poslední slovo.** Rozdíl mezi kritikem a autorem jde do `calibration.md` a do checklistu.
- **Návrh změny skillu `visual-review`** (zatím neměnit):
  - nový checklist `part` se šesti rozměry a kotvou „SC vlevo“;
  - `gate: part`;
  - pole `etalon` v `review.json`, které vloží kotevní záběry do listu.
  - V checklistu `interior` opravit zastaralý bod „u dveří žádný panel“ – panel dveří dnes existuje (5. 10.).

## 3. Showroom – pevné pohledy

**Místo:** etalonová zátoka v `TestSpace`, rozšíření `space.Showroom` o `part <ID>` (nový).
- Neutrální okolí ze schválených dílů W.
- **Stejné světlo pro všechny díly:** pracovní 4000 K, patková světla, žádné slunce.

**Sady pohledů:** preset `Tools/Shots/part_<kategorie>.json` z jedné šablony (nový generátor).
- Výška oka 1,65 m.
- FOV podle nastavení SC (autor zjistí, viz `etalon.md` kap. 4).

| Kategorie | Pohledy |
|---|---|
| Stěna, rám / portál, dveře | A celek z 2 m po ose; B 3/4 z 1,2 m; C detail z 0,5 m; D chodba do hloubky se 3 moduly (jako `ram_portal_1`) |
| Podlaha, strop | A z oka 2 m dopředu, skloněno 35° (jako `podlaha_1`); B kolmo z 1 m; C detail lemu 0,4 m |
| Rozvody, svítidla | A z 1,5 m; B detail objímky nebo difuzoru 0,4 m; C světlo vypnuté / zapnuté |
| MFD, konzole, křeslo | A z pilotního oka; B kolmo z 0,4 m; C stavy vypnuto / náběh / zapnuto |
| Panel dveří, centrální displej | A z 1 m; B 0,4 m kolmo; C stavy (úvod, provoz, porucha) |
| Nábytek, kuchyň, drobné | A z 2 m; B 3/4 z 1 m; C detail 0,4 m; D světlo výklenku vyp / zap |

Pohledy A–D jsou stejné pro všechny díly kategorie, takže se díly dají řadit vedle sebe a vedle etalonu.

## 4. Katalog

`Docs/Kit/catalog.json` (nový; `kit_parts.json` zůstane rodinami dávek) a tabulka vygenerovaná do
`Docs/Kit/catalog.md`. Pole záznamu:
- `id`, `level` (1/2), `category`, `family`;
- `status` (návrh / pilot / schválený / vyřazený), `workflow_version`;
- `etalon` (kotevní záběry), `score` (šest rozměrů + průměr, kolo, datum), `review` (cesta), `author_verdict`;
- `source` (skript + funkce, blend, FBX, UE asset), `variants` (písmena + popis), `sizes`, `sections`;
- `params_for_ship` (paleta, rozměr, výrobce, světla – co jiná loď nastaví daty);
- `reuse` (ano / částečně + co chybí), `used_in` (lodě + místnosti), `tris`, `lights`;
- `metrics` (odkaz na řádek `factory_metrics.csv`).

## 5. Pravidla zrychlování

**Po každém dílu** se do `Docs/Kit/factory_metrics.csv` zapíše:
- čas po krocích (práce / čekání na snímky a balení);
- počet kol kritika a skóre po kolech;
- přestavby (kroky vrácené zpět);
- výtky podle rozměru a podle toho, který krok je měl zachytit;
- poučení, která zabrala;
- tokeny orientačně.

**Kdy se smí krok zkrátit nebo vynechat:**
- Krok se zkrátí, jen když **3 po sobě jdoucí díly téže kategorie** v něm nenašly nic, tj. žádná výtka a žádná
  přestavba nevedla zpět do něj.
  - Příklad: 2D list jen řez a pohled z oka.
  - Příklad: kritik jedno kolo, když tři díly prošly v kole 1.
- Kontroly P1–P25 se nevynechávají, jen se automatizují (test místo ruční kontroly).
- Regrese (výtka, kterou měl zkrácený krok zachytit) krok vrací v plné podobě.
- Zrychlení navrhuje retrospektiva s daty a schvaluje autor.

## 6. Retrospektiva a verze

- Po každém pilotu (a pak po každých 3 dílech) vznikne `Docs/Kit/retro/<datum>_<ID>.md`:
  - metriky proti minulému dílu;
  - které kroky a kontroly našly problém a které ne;
  - nové nástrahy;
  - návrh změn workflow.
- Změny se zapíšou jako nová verze tohoto souboru (v1, v2…) s tabulkou změn nahoře. **Platí až po schválení autorem.**
- Díl se staví podle verze, která platila na jeho začátku (`workflow_version` v katalogu).
- Nové nástrahy jdou do `WORKFLOW.md` kap. 9 a trvalé know-how do skillu `ship-interior`.

## Návrh prvních pilotů

Podrobnosti jsou v `etalon.md` kap. 5. Rozhoduje autor.
- **Úroveň 1:** rámový modul chodby (portál + patky se světlem + podlahová deska).
- **Úroveň 2:** inženýrský terminál (centrální displej lodi).
