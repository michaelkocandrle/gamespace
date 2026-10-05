# Holo MFD v3: specifikace z referencí SC (5. 10. 2026)

Zadání autora (5. 10. 2026):
- MFD širší;
- jiné rozložení textu;
- jiný font a styl, „víc si s tím vyhrát“;
- výraznější náběh a zajíždění, zvuky.

Hotovo:
- náběh a zajíždění (čára světla z emitoru) a zvuky, commit `b83c01ef`;
- interakce (klik na šipky, kurzor), `72ede954` a `84a7cb8e`.

Zbývá rozložení, rozměr a písmo podle této specifikace.

## Zdroje

Ve výčtu je jen to, co jsem opravdu prohlédl.

- **Autorův záznam SC** (Aurora), `ArtSource/Reference/Video/sc_own_04/frames/`:
  - `t00_08_06`: stránka CONFIGURATION, nejlepší předloha 1:1;
  - `t00_02_39`: SELF STATUS;
  - `t00_02_42`: TARGET STATUS.
- **`Docs/UI/Screenshot 2026-09-20 092817.png` a `093154.png`** (Constellation): záložky, řádky seznamů, průhledné holo MFD s barevným lemem.
- **`Docs/UI/Screenshot 2026-09-17 201854.png`**: starší vzhled 3.x, zúžené tučné písmo.

## 1. Rozměry

- **SC:** obsah MFD má poměr asi 1,6 : 1, s pruhem tlačítek u kraje k ose kokpitu asi 1,9 : 1. Naše plátno 560 × 490 má poměr 1,14 : 1, je tedy asi o 40 % užší.
- **Návrh:** plátno **880 × 490** a sklo široké **0,503 m**. Hustota zůstane 1750 px/m.
  - Obsah zabere 784 px.
  - Pruh tlačítek má 96 px a je u kraje blíž ose kokpitu.
- **Ověřit:** jestli se širší sklo vejde vedle středového sloupku a nezakryje výhled. Upravit `hs_cockpit` (`screen_w`, emitor), `CANVAS`, `RECTS` a `MfdGlassSizeCm`.

## 2. Gramatika rozvržení (SC 4.x)

- **Záložky stránek nahoře:**
  - pás y 10–50, stejně široké záložky, horní rohy zkosené 8 px;
  - aktivní záložka je vyplněná levandulově a má tmavý text, neaktivní je tmavá se světlým textem.
- **Titulek dole** (y 440–482): název stránky na střed, verzálky.
  - V rozích jsou listovací tlačítka ve tvaru rovnoběžníku 110 × 34: vlevo «, vpravo ».
  - Výplň #5A6378, 60 %.
  - Klikací místa interakce jsou na těchto tlačítkách.
- **Řádky:**
  - rozteč 58–70 px;
  - jantarový praporek 4 × 22 na x 16 a popisek od x 32;
  - hodnota nebo ovladač zarovnaný doprava, 24 px od kraje obsahu;
  - pod řádkem linka 1,5 px (#8C93B0, 30 %) s koncovými čárkami;
  - dlouhé seznamy mají posuvník 4 px.
- **Hodnoty:**
  - hodnota je v obrysovém rámečku se zkosenými rohy;
  - přepínač je zaoblený obrys 64 × 30 s jezdcem 22 px;
  - položky seznamu začínají šipkou ▸;
  - kolem drátěného modelu lodi jsou tenké rohové závorky;
  - plných ploch je málo.
- **Tloušťky čar:** linky 1,5 px, obrysy tlačítek a přepínačů 2,5–3 px, závorky 2 px.
- **Okraje a hustota:** okraje 16–24 px, asi 6 řádků na stránku.

## 3. Písmo

- **SC 4.x:** samé verzálky, široký geometrický bezpatkový řez se zaoblenými hranatými bříšky, střední až polotučná váha, prostrkání asi +4 %.
- **Velikosti:**
  - popisky řádků 24–28 px (minimum 26 drží test displejů);
  - velké číslo (rychlost) 110–120 px;
  - popisky 22–24 px, ztlumené.
- **Kandidáti (OFL):**
  1. **Saira SemiBold / Medium**: nejbližší tvarem; rodina má i Condensed pro hustá čísla.
  2. **Exo 2 SemiBold**.
  3. **Electrolize**: má jen jednu váhu.
- Oxanium (dnes) je moc hranaté a zkosené, Michroma moc široká.

## 4. Holografický styl (barvy odebrané ze snímků)

- **Barvy:**
  - text #D8DBF0;
  - aktivní výplň a drátěný model #AAB0D6, akcent #7F8CF0;
  - neaktivní záložka #434C55 (60 %); neaktivní tlačítka bez obrysu, šedý text #8A8E9A;
  - upozornění jantarová #F5A623, varování a přepínače červená #D15D5F.
- **Pozadí:** kouřově námořnická #0E1220, průhlednost 35–50 %, ne černá deska.
- **Dvě vrstvy prvku:**
  - ostré jádro;
  - měkká záře: rozmazaná kopie, poloměr 6 px, 35–40 %, stejný odstín.
- **Velké plochy:** svislý přechod 85 % → 60 %.
- **Barevný lem:** posun 1–1,5 px červená/azurová, jen na plochy a drátěný model, nikdy na malý text.
- **Řádky obrazu:** perioda 2 px, ztmavení 6 %, skoro neznatelné.

## 5. Stránky (levé MFD: obsah x 0–784, pruh 784–880; pravé zrcadlově)

- **FLIGHT:**
  - rychlost 120 px vlevo nahoře s jednotkou M/S 26 px;
  - pod ní G 56 px;
  - řádky LIMIT, G MAX a MODE od y 290;
  - segmentové sloupce SPD, BST a AB: 70 × 260 px, 10 dílků;
  - tlačítka CPLD, GSAF, CSTB, BOOST, PREC a VTOL v pruhu: 80 × 52 px, rozteč 66.
- **THRUSTERS:** řádky MAIN, RETRO, STRAFE, UP a DOWN, rozteč 62, s vodorovným segmentovým pruhem (20 dílků) a hodnotou vpravo.
- **NAVIGATION:**
  - SCM 72 px a FLIGHT;
  - vpravo SPEED, LIMIT a QUANTUM;
  - tabulka NAME, RANGE a BRG s pěti řádky po 46 px a šipkou ▸.
- **CONFIGURATION:** kopie SC; řádky po 70 px, jantarový praporek, přepínač vpravo.
- **STATUS:** řádky GEAR, QUANTUM, R-ALT, VSI a ATMO, hodnoty v rámečcích se zkosenými rohy 220 × 44, jantarově při upozornění.
- **CONTACTS:** souhrn nahoře, řádky jako SC COMMUNICATIONS: ▸ jméno, vzdálenost, směr v rámečku.
- **SELF STATUS:**
  - štítek stavu vlevo nahoře;
  - drátěný model lodi uprostřed v závorkách;
  - vpravo sloupec STATE, GEAR, ENGINES a BOOST.
- **Pruh pravého MFD:** kontrolky s jantarovými bočními pruhy (GEAR, GSAF, QT).

## 6. Animace

Reference **neukazují** vysouvání ani zasouvání MFD. V SC 4.x jsou MFD malých lodí fyzické obrazovky, které se s napájením rozsvítí asi za 3 s.

Náš náběh z čáry světla je tedy vlastní prvek na přání autora (holografický dojem). Jediné holo chování v referencích je průhledná plocha s barevným lemem (Constellation).
