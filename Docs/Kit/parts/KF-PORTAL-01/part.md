# KF-PORTAL-01 – rámový modul chodby (pilot 1)

**Workflow:** `Docs/Kit/FACTORY_WORKFLOW.md` v0.1.
**Stav:** pilot.
- List rev. A autor schválil s úpravami 6. 10.; rev. B je zapracovaná.
- Krok 3 (materiálový základ) běží a končí STOPem s tabulí materiálů.
- Blockout (krok 4) až po schválení autorem.
**Úroveň:** 1. **Kategorie:** rám / portál + svítidla + podlaha.
**List:** `ArtSource/Kit/Design/KF-PORTAL-01.png` (data `KF-PORTAL-01.json`, nástroj `Tools/Design/draw_part_sheet.py`).

## Krok 0 – zadání

**Díl:** modul chodby, který se opakuje po rozteči. Skládá se z:
- portálu (rám kolem průřezu, délka 0,3 m podél chodby, tři stupně, leštěný lem, pryžová manžeta);
- dvou patek se světlem L1 u podlahy;
- dvou horních světel L2 a skryté lišty L3 v horním členu;
- podlahy mezi portály: osmiboká deska 0,9, příčný pás 0,3 a práh pod portálem.

**V pilotu 1 se staví i sdílený základ kitu** (workflow v0.1, bod 3): `M_Kit_*` s trojicí lak / leštěný lem / guma
či perforace a pouzdro světla jako sdílený díl.

**Rozměrová řada** – kit (`kit_rules.json`): mřížka 0,3 m, rozteč portálů 1,2 m (portál 0,3 + 0,9) nebo 2,4 m
(0,3 + 2,1), lze je střídat.

| Prvek | Řada | Poznámka |
|---|---|---|
| Portál | délka 0,3; průřez W, N | výstupek z líce stěny W 100 mm, N 80 mm (stupně 40 / 70 / 100) |
| Podlahová deska | **0,9** a **0,6** × chodník 1,2 | 0,6 pro Wayfarer (níže). Rev. B: charakter podlahy kitu – A = chodník s protiskluzovými pásy 80 / 110, G = mřížka nad kanálem 0,6 × hl. 0,2; W má navíc hladké boční desky a okrajové lišty 60 mm |
| Příčný pás | 0,3 | mezi dvěma deskami v rozteči 2,4 |
| Práh | 0,3 | pod portálem, s patkami L1 |
| Skladba rozteče | 1,2 = 0,3 + 0,9; 2,4 = 0,3 + 0,9 + 0,3 + 0,9 | |

**Wayfarer** (výkresy I-01–I-04, `Wayfarer_hs.json` `interior.kit_modules`)
- **Technická chodba W:** x 8,24–10,34, mezi přepážkami 2,1 m.
  - Zadní přepážka `Bulkhead_Door03W_B` (0,3 m, dveře mimo osu y 0,5) zabírá místo portálu. Na volný portál
    zbývá 1,8 m: stěny 1,2 + 0,6 (výklenky komponent), takže **samostatný portál se tam nevejde**.
  - Podlaha 1,8 = deska 0,9 + pás 0,3 + deska 0,6. Spáry pak lícují se stěnovými moduly. Odtud deska 0,6 v řadě.
  - Profil portálu pak dostanou čela přepážek (pozdější varianta `Bulkhead_Door`, mimo tento díl).
- **Sklad (L41) a kajuta (L38):** obložení trupu, ne průřez W/N; portál zatím ne.
- **Kokpit:** vlastní díly.

**Steadfast v2** (`Steadfast_layout.json`, návrh 24. 9., čeká na schválení). **Autor 6. 10.: hlavní chodba
W 2,4 × 2,3 m.**
- **Ověřeno ve 2D:**
  - Do trupu 6,4 m se vejde: stěny se strukturou do |y| 1,4 m, boční místnosti 1,8 m.
  - Kolidují 2 předměty: skříň s léky (|y| 1,0–1,4) a stůl jídelny (|y| 1,3–2,7). Oba se dají posunout.
  - Konstrukce stropu zasahuje 0,15 m nad světlou výšku 2,4, do střechy trupu, jejíž tloušťka zatím není navržená
    (nejistě).
  - Délka 11,4 m.
  - Dveře 1,0–1,3 m se vejdou jen do pole 2,1 m (rozteč 2,4).
  - Zapsáno v `Steadfast_Design.md` kap. 6.

Původní stav:
- **Hlavní chodba horní paluby:** 1,6 × 2,4 m, délka 11,5 m, 6 bočních dveří.
  - **Nesedí na žádný průřez kitu** (N 1,2, W 2,4; strop 2,4 je mezi 2,3 a T 2,7) a délka není na mřížce 0,3.
  - **Návrh:** při schválení Steadfastu v2 přejít na W 2,4 × 2,3 a délku 11,4 m (rozteče 2,4 a 1,2). Dveře
    do bočních místností pak padnou do stěnových modulů mezi portály.
  - **Rozhodne autor.**
- Schodiště k můstku 1,2 m odpovídá N.

**Varianty:**
- **W a N** se staví.
- **S** (0,9, portál zarovnaný s lícem: kapsle postavy 0,84 m) a **T** (2,7) jsou jen poznámka, nestaví se.
- Písmena A/B/C podle pravidel kitu přijdou až s detailem (krok 5): A bez štítků, B se štítkem úseku,
  C s nouzovou značkou.

## Krok 1 – etalonová karta

### a) Cíle kvality ze SC (platí pro všechny díly)

Kotevní záběry: `Docs/Kit/etalon/sc/`
- `ram_portal_1` – chodba přes 2–3 rámy;
- `ram_portal_2` – pata rámu se světlem;
- `ram_portal_3` – vnitřní rám a šikmý portál;
- `podlaha_1` – desky, mřížka, rohová světla;
- `podlaha_2` – ražba, šrouby v jamkách;
- `podlaha_3` – práh a schod;
- `svitidla_1` – obdélníkové svítidlo s difuzorem;
- `svitidla_2` – rohová světla v osmibokém krytu.

| Rozměr | Cíl (z `etalon.md`) | Jak se ověří |
|---|---|---|
| **Tvar a hierarchie** | Profil 2–3 stupně po 2–3 cm, výstupek 5–10 cm, zkosení 45°, osmiboké tvary. Tři vrstvy: rám → stupně a manžeta → šrouby, ražba, štítky. Deska osmiboká se zkosením rohů 12–15 cm, zapuštěná o 0,5–1 cm, spára 1 cm. | list (krok 2), pohled C 0,5 m |
| **Materiály** | Trojice: lak (drsnost 0,4–0,5) / **leštěný lem 15–20 mm** (0,2–0,3), který kreslí obrys v odlescích / tmavá guma či perforace (0,6–0,7). Perforace desky Ø 15 mm, rozteč 25 mm. Žádná plocha nad 0,5 m s jednou drsností. | showroom D (do hloubky), měření drsnosti v materiálu |
| **Světlo** | Vše v pouzdře nebo skryté. Patka: osmiboký kryt ~15 × 15 cm, 2 na portál, studená, skvrna ~0,5 m, s bloomem. Horní roh: malé bodové světlo. Nepřímé teplé světlo z horní hrany, přechod jasu dolů. Do hloubky dvojice světel po ~1,2–1,5 m; mezi nimi tma. | `measure_look.py` v rozsahu SC, pohled D |
| **Decaly a značení** | Malé: štítky 3 cm na pilíři, šipky a trojúhelníky 1–3 cm. Logo jako **ražba** (~15 × 5 cm v podlaze). Hierarchie logo → název úseku → servisní značky. | pohled C, test orientace |
| **Špína a opotřebení** | Podle stylu výrobce (níže), ne podle čisté Aurory. | pohled B a C |
| **Funkce a stavy** | Světla mají dva stavy (napájení lodi zapnuto / vypnuto, nouzově jen patky). Modul navazuje na stěnu a podlahu bez mezer. Průchod je volný: světlost W 2,2 × 2,2 m, N 1,04 × 2,22 m, minimum kitu 0,9 × 2,0. | list (krok 2), `check_kit_clearance.py` |

### b) Styl výrobce – Halcyon Freightworks (návrh, potvrdí autor)

Zdroj: dnešní chodba a exteriér Wayfareru (paleta `kit-design.md` kap. 4).
- **Paleta dílu:**
  - **lak rámu = krémová** (akcent Halcyonu, 10–15 % plochy prostoru; portály a lemy jsou přesně to místo);
  - okolí (stěny, desky, pás) **grafit** 0,05–0,07, drsnost 0,45–0,55;
  - **leštěný lem = gunmetal** leštěný, drsnost 0,2–0,25;
  - **manžeta = tmavá guma** 0,8–0,9;
  - **perforovaná vložka = grafit** matný 0,65;
  - **signální oranžová** (0,85 / 0,34 / 0,06) jen na štítku úseku a šipkách, do 3 % plochy.
- **Světlo:**
  - patky studené jako modrá lišta u soklu (orientační, UI 0,45 / 0,72 / 1,0);
  - horní roh 4000 K a skrytá lišta 3500 K (teplá architektura).
- **Tvarosloví Halcyonu:**
  - průmyslovější než RSI: rovné stupně místo zaoblení, pohledové šrouby Ø 10 mm v řadách po 80 mm na
    základně a na krycí destičce;
  - ražené logo Halcyon jako geometrie na destičce pásu.
- **Opotřebení** (udržovaná pracovní loď, víc než Aurora):
  - špína ve spárách, v drážkách pásu a v žebrech manžety;
  - otěr hran 2–6 mm na stupních v pásmu ruky a ramene (0,9–1,6 m) a na lemu prahu;
  - vyšlapaná dráha na středu desek a prahů (směrová buňka atlasu z backlogu kitu);
  - karty špíny nejvýš ~10 % plochy podlahy; stěny a strop čistší.

**Rozhodnutí autora 6. 10.:**
- rám je celý krémový lak;
- Steadfast v2 má chodbu W 2,4 × 2,3;
- FOV 90° jako ve SC (potvrdil autor 6. 10.).

**Otevřené pro autora:** výchozí rozteč portálů 1,2, nebo 2,4 m. List rev. B ukazuje obě (pohled 6a/6b);
doporučeno 1,2 m podle etalonu.

## Krok 2 – list (rev. B, 6. 10.)

`ArtSource/Kit/Design/KF-PORTAL-01.png`, výřezy `KF-PORTAL-01_0n_*.png`. Úpravy autora proti rev. A:
1. Pohled z oka ve dvou roztečích, 1,2 a 2,4 m.
2. Podlaha má charakter dnešního kitu a z principů SC jen leštěný lem 18 mm, vložku −6 mm a zkosené rohy 120 mm.
   Perforovaná deska Aurory nepřevzata.
3. **Sokl:** holá modrá lišta je z modulu **odstraněná**; sokl je pryžový kopací pás 100 mm se žebry.
   - Proč: etalon nemá souvislou světelnou linku u podlahy. Orientační světlo dávají patky L1 jako ostrůvky po
     rozteči a holý pruh porušuje pravidlo „světlo v pouzdře“.
   - Pryž doplní materiálovou trojici a chrání sokl.
   - Alternativa, kdyby autor chtěl souvislou linku: opálový difuzor 20 mm v drážce 30 mm pod přesahem 10 mm.
   - Změna se týká stěnových modulů kitu (dávka 1). Projeví se, až jimi projde továrna.
4. **L3:** rev. A (jedna lišta na římse stupně 2) byla z blízké strany vidět z celé chodby, od elevace 3°.
   Rev. B má dvě symetrické lišty v drážce 14 × 20 mm u boků koruny. Zdroj je vidět jen pod členem, do 0,30 m,
   při elevaci ≥ 63°, z obou směrů. Při pohledu vodorovně (svislé ½ FOV 29°) je mimo obraz. Výpočet je přímo
   v listu (`hidden_strip_visibility`).
5. Destička příčného pásu má 4 šrouby.

## Krok 3 – materiálový základ kitu (6. 10., STOP)

Sdílený základ kitu vznikl v pilotu 1:
- `ArtSource/Kit/kit_materials.json`: role trojice, palety Halcyon a Kestrel, styl opotřebení výrobce;
- master `M_Kit_Base` a instance `MI_Kit_<Výrobce>_<Role>`;
- tabule vzorků v showroomu a test `test_kit_materials.py`.

Podrobnosti, slabá místa a měření odrazů jsou v `Docs/Reviews/2026-10-06_kit_material_board.md`. Varianta c stojí
na RX 9070 v 1440p +0,6 až +1,4 ms GPU. Blockout (krok 4) až po schválení tabule autorem.

## Krok 3b – zkušební úsek (workflow v0.2, 6. 10., STOP)

- Autor tabuli neschválil. Rozhodl: odrazy kovu varianta c v celé hře, výchozí rozteč portálů **1,2 m**, FOV 90°.
- Poučení P26: materiály se posuzují v kontextu, ze stejných úhlů jako etalon.
- **Zkušební úsek chodby:** 3 portály po 1,2 m, hrubá geometrie z listu rev. B, světla L1/L2/L3.
- **Materiály v0.2:**
  - lak je satén;
  - světlý leštěný lem pevný u všech výrobců;
  - guma 0,88 a grafit 0,45 zvlášť;
  - škrábance jen na grafitu ve výšce ruky;
  - protiskluzový vzor v pásech, dráha přes drsnost;
  - L1 ~7500 K.
- Listy a zdůvodnění: `Docs/Reviews/2026-10-06_kit_test_section.md`.
- P25: Wayfarer před a po beze změny (rozdíly jen šum na hranách).
- Blockout (krok 4) až po schválení autorem.

## Návrat do kroku 2 – list rev. C a kalibrace světla (6. 10., STOP)

- Krok 3 je schválený. Kvůli **návrhovým chybám** se díl vrátil do kroku 2:
  - profil se četl jako proužky;
  - patka byla krabička místo boty;
  - podlaha byla „rohožky“ bez sítě lemu.
- **Rev. C:**
  - rám je jeden lakovaný tvar s jedinou leštěnou linkou na hraně koruny a manžetou uvnitř;
  - osmiboká bota L1 se zapuštěným světlem;
  - souvislá síť lemu přes celou podlahu.
- **Kalibrace světla:** L1 reflektor 4 cd ze štěrbiny, L2 18 cd / 100°, L3 8 cd, grafit Halcyonu 0,06.
- Tabulka jasu a listy jsou v `Docs/Reviews/2026-10-06_kit_test_section_revc.md`.
- Blockout (krok 4) až po schválení autorem.

## Rev. D a krok 4 – blockout (6. 10., STOP)

- Rev. C je schválený kromě boty.
- **Rev. D:**
  - bota L1 je světlá s leštěnou hranou a září v osmibokém kalichu, jemný rozptyl, žádný reflektor;
  - v N je bota 120 mm;
  - manžeta je jemnější a světlejší.
- **Blockout** `Tools/Kit/kit_portal.py`: `Portal_Frame03W/N_A`, `Floor_Walk09W/N_A`; světla jako sockety dílu.
  Zkušební úsek je z blockoutu.
- **Post-process interiéru** (závoj, zvednutá černá) je jen uvnitř lodí; vesmír a planety se nezměnily (P25).
- Listy, tabulka jasu SC / rev. C / rev. D: `Docs/Reviews/2026-10-06_kf_portal_01_blockout.md`.
- Krok 5 (detail) až po schválení autorem.

## Rev. E, krok 5 (detail) a krok 6 (UE) – 6. 10., STOP

- Blockout je schválený s úpravami tvaru. **Rev. E:**
  - čela stupňů zkosená pod 45°, leštěná zkosená hrana koruny;
  - bota nízká (W 150, N 120), plochá, osmiboká, s hlubokým kalichem a tmavým dnem.
- **Detail:**
  - štítky 3 cm na plošce pilíře;
  - práh s drážkami, krycí destičkou se 4 šrouby a reliéfem;
  - žlab u soklu, karty špíny, otěr v pásmu ruky.
- **Otevřené:**
  - rozptyl kalichu na podlahu;
  - nové místo drážky L3;
  - síla karet špíny.
- Závoj interiéru je bez kokpitu.
- Recenze a tabulka jasu SC / blockout / detail: `Docs/Reviews/2026-10-06_kf_portal_01_detail.md`.
- Krok 7 (výkon) a 8 (kritik) až po schválení.
