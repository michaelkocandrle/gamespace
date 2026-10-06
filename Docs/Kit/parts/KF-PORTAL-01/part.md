# KF-PORTAL-01 – rámový modul chodby (pilot 1)

**Workflow:** `Docs/Kit/FACTORY_WORKFLOW.md` v0.1.
**Stav:** návrh. Kroky 0–2 jsou hotové a čekají na schválení listu autorem; nic dalšího se nestaví.
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
| Podlahová deska | **0,9** a **0,6** × šířka 1,2 | 0,6 pro Wayfarer (níže); W má navíc boční desky do soklu (2 × 0,5 + žlab 0,1) |
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

**Steadfast v2** (`Steadfast_layout.json`, návrh 24. 9., čeká na schválení)
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

**Otevřené pro autora:**
1. Krémový lak rámu, nebo grafitový rám s krémovým jen lemem.
2. Steadfast v2 chodba na W 2,4.
3. FOV ze SC pro pohled z oka (list počítá 90°, nejistě).
