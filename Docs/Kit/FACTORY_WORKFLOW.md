# Workflow továrny dílů – v0.2 (autor 6. 10. 2026)

| Verze | Datum | Změny |
|---|---|---|
| v0 | 6. 10. 2026 | návrh |
| v0.1 | 6. 10. 2026 | autor schválil v0 s úpravami: (1) karta dílu odděluje **kvalitu ze SC** od **stylu výrobce**, kit přebírá principy kvality RSI, ne barvy a styl Aurory, špína se hodnotí podle stylu výrobce; (2) nástroje v pilotu jen v nejjednodušší funkční verzi, jejich čas se vede zvlášť; (3) materiálová trojice a světlo v pouzdře vznikají v pilotu 1 jako sdílený základ `M_Kit_*`; (4) piloty po jednom: 1 = rámový modul chodby, 2 = pouzdro panelu dveří (po retrospektivě pilotu 1), terminál není pilot; skill `visual-review` upraven (gate a checklist `part`, pole `etalon`) |
| v0.2 | 6. 10. 2026 | autor neschválil tabuli materiálů a změnil test (poučení **P26**): materiály se posuzují **v kontextu a ze stejných úhlů jako kotevní záběry SC**, ne na izolovaných vzorcích snímaných kolmo. Krok 3 (a každý další krok se snímky) používá **zkušební úsek chodby** (3 portály, podlaha, kus stěny a stropu z hrubé geometrie listu) se světly z listu a bez pomocného světla místnosti; kap. 3 přepsána |

**Cíl:** každý díl jednou na úroveň etalonu SC (`Docs/Kit/etalon/etalon.md`), pak v každé lodi. Lodě se liší
paletou, doplňky a světly.
**Kvalita a styl zvlášť** (v0.1): z etalonu SC se přebírají **principy kvality RSI**:
- materiálová trojice (světlý lak / leštěný lem 1,5–2 cm / tmavá perforace nebo guma);
- světlo vždy v pouzdře nebo skryté v hraně;
- stupňovité profily, zapuštěná pole, zkosené rámy.

**Ne barvy a styl Aurory.** Barvy, tvarové akcenty a míru opotřebení dodává **výrobce lodi paletou** (Halcyon
Freightworks, Kestrel Dynamics…); rozměr „špína“ se hodnotí podle stylu výrobce.

**Princip:** piloty po jednom, každý celý (tvar, materiál, světlo, decaly, špína, funkce). Na nich se workflow odladí.
Zrychluje se jen podle naměřených dat (kap. 5).
**Vstupy:**
- etalon;
- 25 poučení `Docs/Kit/catalog_draft.md` (dál **P1–P25**);
- `.claude/skills/ship-interior/kit-design.md`;
- recenze chodby, kajuty a rampy.

Každý díl má složku `Docs/Kit/parts/<ID>/` s kartou `part.md` (zadání, cíle, metriky) a recenzí. Nové nástroje
v textu jsou označené **(nový)**. Postaví se v pilotu, ne předem, a **jen v nejjednodušší funkční verzi** (v0.1).
Čas na nástroje se v `factory_metrics.csv` vede zvlášť od času na díl.

## 1. Výroba jednoho dílu

| # | Krok – co se dělá | Čím | Výstup | Hotovo, když | Kontroly (poučení) |
|---|---|---|---|---|---|
| 0 | **Zadání:** kategorie, úroveň, cílové lodě a jejich rozměry z výkresů, rozměrová řada a varianty | výkresy lodí, `kit_rules.json`, `kit_parts.json` | karta `part.md` | každá cílová loď má rozměr, do kterého díl padne | P9 řada z výkresů; P13 uzel = samostatný díl |
| 1 | **Etalonová karta, dvě části:** (a) **cíle kvality ze SC** – 3–4 kotevní záběry a měřené cíle v šesti rozměrech (tvar a hierarchie, materiály, světlo, decaly, špína, funkce), platí pro všechny díly; (b) **styl výrobce** – paleta, tvarosloví, míra opotřebení (navrhne Claude, potvrdí autor) | `etalon/sc/*.jpg`; když chybí záběr, požadavek na dotočení autorovi | tabulka cílů a styl v `part.md` | každý rozměr má číslo nebo „nejistě“; styl výrobce potvrzený autorem | P2 cíle měřené, ne pocitové |
| 2 | **2D list dílu:** pohled, řez, detail profilu 1:5; obě polohy pohyblivých částí; pohled z oka (co je vidět); volné místo kolem | `Tools/Design` (nový `draw_part_sheet.py` podle `draw_interior_sheet.py`) | `ArtSource/Kit/Design/<ID>.png` + JSON | **autor list schválil** | P2 2D před 3D; P7 obě polohy, průchod 1,8 m, dosednutí; P8 0,5 m za dveřmi, řez trupem; P15 funkční prvek na líc; P16 obsah za mřížkou z oka |
| 3 | **Materiálový základ:** díl používá sdílený master + trim + zrno, žádný vlastní materiál. **V pilotu 1 je krok 3 stavbou tohoto základu** (`M_Kit_Base`, `kit_materials.json`: lak / světlý leštěný lem / guma + grafit, protiskluzové pásy), ne materiálem jednoho dílu. Posuzuje se **jen ve zkušebním úseku** (kap. 3) | `M_Kit_Base`, `kit_materials.json`, `test_kit_materials.py`, `kit_factory.py` + preset `kit_test_section` | listy SC / úsek ze 4 úhlů etalonu | test zelený (limity, lem pevný u všech výrobců, kontrast pásů); `measure_look` v rozsahu etalonu; autor schválil listy | P1 základ před koly; P10 kov; P14 čalounění; **P26 kontext a úhly etalonu**; P25 snímky lodí před a po |
| 4 | **Blockout:** hrubá geometrie v rozměrech, jeden snímek z oka vedle etalonu | `Tools/Kit/kit_<dávka>.py`, `render_kit_closeup.py` | `closeup_<ID>_eye.png` | silueta a proporce odpovídají etalonu na listu vedle sebe | P3 tvar dřív než obsah; P18 `--python-exit-code 1`, čas blendu |
| 5 | **Detail:** vrstvy 2 a 3, decaly, špína, světlo v pouzdře podle světelného plánu kategorie | kit skript, knihovna decalů, `kit_layout.py` | díl v blendu + manifest | hustota vrstev podle karty; A/B snímek decalů a špíny (vyp / černá / bílá) | P5 A/B před laděním; P20 seřazené pořadí; P23 orientace nápisů; P24 atlas jen `append`, celá dávka |
| 6 | **UE a zkušební úsek:** import, snímky z pevné sady pohledů v kontextu (kap. 3), změření vzhledu | `import_kit.py`, `Shots.ps1 -Preset part_<kat> -Editor`, `measure_look.py` | `shots:part_<ID>/…` | kvalita vynucená (v logu), čas FBX novější než blend, `measure_look` v rozsahu SC | P19 export a čas FBX; P22 `-Editor` a kvalita; P25 změna masteru = snímky všech lodí; P26 v kontextu, úhly etalonu |
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
- **Skill `visual-review`** (upraveno v0.1): checklist `part`, `gate: part` (`"pilot": true/false`), pole `etalon`
  v `review.json` → `sheet_00_etalon.jpg` a oddíl „Etalon“ v briefu; bod „u dveří žádný panel“ nahrazen panelem
  ve fyzickém pouzdře.

## 3. Zkušební úsek a pevné pohledy (v0.2, poučení P26)

**Místo:** zkušební úsek chodby v `TestSpace` za schodišťovou halou (`import_kit.SHOWROOM["test_section"]`,
geometrie `Tools/Kit/kit_factory.py`).
- Chodba W se **3 portály po 1,2 m**, podlahou, kusem stěny a stropu, z hrubé geometrie listu dílu. Není to
  blockout dílu.
- Díl, který se hodnotí, se do úseku vloží místo své hrubé verze; zbytek zůstává jako kontext.
- **Světlo jen z listu** (u pilotu 1: L1 patky ~7500 K, L2 rohy, L3 skrytá lišta). Žádné pomocné světlo místnosti,
  žádné slunce, žádné okno.
- Tóny se měří `measure_look.py` proti kotevním záběrům (etalon Aurory: průměr 0,23–0,28, p10 0,13, B/R ~1,0).

**Pohledy:** stejné úhly jako kotevní záběry SC (preset `Tools/Shots/kit_test_section.json`), FOV 90 jako ve SC (potvrdil autor 6. 10. 2026), 2560 × 1440.

| Pohled | Úhel | Kotevní záběr |
|---|---|---|
| 1 | z oka 1,65 m po ose do hloubky | `ram_portal_1` |
| 2 | pata pilíře se světlem L1 šikmo shora z ~1,2 m | `ram_portal_2` |
| 3 | podlaha 35° dolů s lemem | `podlaha_1` |
| 4 | detail laku a tmavé třetiny z ~0,5 m šikmo | `ram_portal_3` |

Další kategorie (dveře, panel dveří, nábytek…) dostanou svůj úsek a úhly podle svých kotevních záběrů, až na ně
přijde řada. Izolované vzorky snímané kolmo se nehodnotí.

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

**Po každém dílu** se do `Docs/Kit/factory_metrics.csv` zapíše (řádek na krok; sloupec `kind` = `part` nebo
`tool`, čas na nástroje zvlášť):
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

## Piloty (autor 6. 10. 2026)

Jdou **po jednom**; pilot 2 začne až po retrospektivě pilotu 1.
1. **Pilot 1:** rámový modul chodby (portál + patky se světlem + podlahová deska), `Docs/Kit/parts/KF-PORTAL-01/`.
   Zároveň staví sdílený materiálový základ a pouzdro světla (krok 3).
2. **Pilot 2:** pouzdro panelu dveří; logika `USpaceDoorPanel` zůstává.

Inženýrský terminál není pilot: patří k systémům lodi později.
