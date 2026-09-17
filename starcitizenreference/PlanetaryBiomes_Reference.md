# Planetární prostředí a biomy — kompletní referenční rozbor

Rozbor toho, jak No Man's Sky, Starfield a Elite Dangerous řeší biomy,
povrchovou rozmanitost planet a jak se to technicky dělá na terénu —
včetně konkrétního propojení na náš vlastní quad-sphere terén systém
(`PlanetTerrain`, `AQuadSpherePlanet`).

---

## 1. Designová filozofie: jeden biom na planetu, nebo víc?

Zásadní rozdíl mezi hrami, se skutečnými herními důsledky:

- **No Man's Sky**: typicky **jeden biom na planetu** (Lush, Barren,
  Toxic, Radioactive, atd.), definovaný sadou parametrů — atmosférické
  složení, typ/hustota flóry a fauny, počasí, zdroje surovin. Rozmanitost
  vzniká kombinatorikou parametrů napříč miliardami planet, ne
  rozmanitostí uvnitř jedné planety.
  - Existují speciální "Mega-Exotic" biomy s extrémními vizuálními
    filtry (barevné posuny, monochromatické tóny) a obřími rostlinami
    jako permanentními orientačními body.
  - "Infested" subtyp se dá překrýt přes běžný biom a vytvořit
    lokální variaci (zamořená flóra) bez nutnosti nové base kategorie.
- **Starfield**: naopak cíleně staví **víc biomů na jedné planetě**
  (zdokumentovaný případ: 6 rozlišitelných biomů na jedné planetě —
  hustá zeleň, pláně, poušť, skalnatý terén). Dělá to kombinací
  biome-metrik (klima, historie osídlení) s ručně navrženými POI
  šablonami, co se do vygenerovaného terénu vsazují.
- **Praktický kompromis, který zmiňují diskuze o obou hrách**: NMS má
  "planeta = jeden biom" jednodušší přístup, co je rychlejší
  implementovat, ale rychleji se okouká (jakmile vidíš všechny biomy
  jednou, víš jak vypadá celý vesmír). Starfieldí multi-biome přístup
  je bohatší, ale výrazně náročnější technicky i umělecky.

**Doporučení pro nás:** vzhledem k tomu, že budeme mít málo planet
(ne miliardy), dává větší smysl **Starfield přístup — víc biomů na
jedné planetě** podle zeměpisné šířky/výšky/vlhkosti. Je to i přirozeně
kompatibilní s tím, co už řekl Claude Code (potřeba dat o sklonu/výšce
do materiálu) — jedna planeta s bohatou vnitřní rozmanitostí bude
zajímavější k prozkoumání než víc jednodušších planet.

---

## 2. Co definuje biom — parametry k navržení

Napříč hrami se opakuje podobná sada parametrů, které dohromady
definují "biom":

- **Klima/teplota** — určuje typ terénu (sníh na pólech/vysoko, poušť
  v teplých nízkých oblastech, atd.)
- **Vlhkost/přítomnost vody** — lesní/travnatá vegetace vs. holá skála
  vs. poušť
- **Nadmořská výška** — hory mají jiný povrch než údolí (sníh nahoře,
  tráva dole — klasický height-blend vzorec)
- **Sklon terénu** — strmé svahy = holá skála/sutina, mírné svahy =
  vegetace se drží (slope-blend)
- **Barevná paleta** — i geometricky podobný terén vypadá jinak jen
  změnou palety (NMS dělá tohle masivně — stejná "kostra" terénu,
  různé barvy = pocit jiné planety)
- **Hazardy/počasí** — bouře, radiace, extrémní teploty (NMS: "Storm
  Crystals" se otevírají jen během extrémního počasí — počasí jako
  gameplay mechanika, ne jen vizuál)
- **Flóra/fauna hustota a typ** — co roste/žije, jak hustě

---

## 3. Technická implementace — jak se biomy dělají na terénu (Unreal)

Tohle je přímo akční část pro náš `PlanetTerrain`. Standardní technika
(používaná i v Unreal Landscape systému i v custom PMC terénech):

### Slope blending (podle sklonu)
- Spočítá se z normály terénu: dot product mezi normálou a "nahoru"
  vektorem. Dot = 1 znamená plochý terén, dot = 0 znamená svislou
  stěnu.
- Typicky: tráva/půda na plochém terénu, skála/sutina na strmém.

### Height blending (podle nadmořské výšky)
- Založené na world-space výšce vrcholu (případně relativní výšce
  vůči "hladině moře" nebo střední hodnotě planety).
- Typicky: sníh nahoře, skála uprostřed, tráva/písek dole.

### Kombinace obojího
- Nejrealističtější výsledek kombinuje height i slope zároveň (např.
  sníh se objevuje jen nad určitou výškou A zároveň jen na mírnějších
  svazích — na příkré skále sníh nedrží ani vysoko v horách).

### Jak se to dostane do materiálu — klíčový technický bod
Landscape systém v Unreal (vestavěný nástroj) tohle řeší přes **weight
mapy** (až 8 vrstev), ručně malovatelné v editoru. **My ale terén
NEMÁME jako Landscape — máme vlastní `ProceduralMeshComponent` systém**
(kvůli quad-sphere/LOD architektuře), takže tenhle přístup nejde použít
přímo. Místo toho potřebujeme:

- **Zapéct sklon a výšku přímo do vertex dat** každé dlaždice terénu
  (vertex color kanály, nebo extra UV kanál) při generování meshe —
  přesně to, co Claude Code již identifikoval jako chybějící krok
  po L2/L3 ("Materiál zatím pozná jen polohu na planetě a hodnotu
  šumu; nemá sklon ani výšku. Biomy budou potřebovat data do vrcholů").
- Materiál pak čte tahle vertex data a podle nich blendne mezi
  texturami/barvami — runtime výpočet ze samotné geometrie (normály,
  world position) je i technicky možný a možná jednodušší než pečení
  do vertex dat, protože se to spočítá stejně konzistentně pro každou
  dlaždici bez extra kroku při generování.

### Sdílené parametry napříč biomy
Pro věci jako barva mlhy/oparu, barva oblohy podle aktuální biomové
oblasti, doporučuje se **Material Parameter Collection** (MPC) —
globální sada parametrů, kterou může měnit gameplay kód a všechny
materiály (terén, obloha, opar) na ni reagují konzistentně. Tohle
přesně zmínil Claude Code jako plán pro L4.

---

## 4. Počasí a denní/noční cyklus

- Počasí jako čistě vizuální vrstva (mraky, mlha) je nejjednodušší
  přidat, ale nejmíň zajímavé.
- Počasí jako **gameplay mechanika** (NMS: bouře otevírají speciální
  zdroje, extrémní teplota poškozuje skafandr) je zajímavější, ale
  vyžaduje propojení s systémy, co ještě nemáme (HP/poškození postavy,
  inventář/zdroje).
- Denní/noční cyklus u nás bude komplikovaný kvůli rotaci planety —
  Claude Code už upozorňoval, že "nic nepočítá s rotací planety" jako
  známé omezení z L5. Otáčející se planeta s pohybujícím se sluncem by
  vyžadovala přepočítávat i orientaci gravitace/landed stavu postavy
  v čase, ne jen staticky.

---

## 5. Povrchové POI (points of interest)

Podobně jako u vesmírných POI (viz předchozí dokument), i na povrchu
planety obě hry (NMS, Starfield) kombinují:
- **Ručně navržené šablony** (budovy, ruiny, tábory) vsazené
  algoritmicky do terénu podle biome-metrik
- **Procedurálně generované varianty** stejné šablony (různá velikost/
  rotace/poškození), aby to nepůsobilo jako "copy-paste"

**Náš stav:** nemáme na Veyře žádné POI — jen terén. To je logický
další krok po biomech, ne před nimi (nejdřív rozmanitý terén, pak do
něj vsadit zajímavá místa).

---

## Shrnutí — co z tohohle dává smysl pro gamespace a kdy

1. **Nejnutnější technický krok**: dostat sklon + výšku do vertex dat
   nebo runtime výpočtu v materiálu terénu — bez tohohle nejde stavět
   žádný biome systém. Tohle je přímé pokračování L4 kroku, který jsme
   už plánovali.

2. **Doporučený přístup**: multi-biome na jedné planetě (Starfield
   styl), ne jeden biom na planetu (NMS styl) — dává větší smysl pro
   náš rozsah (málo planet, chceme každou zajímavou uvnitř sebe).

3. **Material Parameter Collection** pro sdílené hodnoty (barva mlhy/
   oblohy podle biomu) — středně náročný krok, navazuje na základní
   slope/height blending.

4. **Počasí jako gameplay mechanika** — odložit, dokud nemáme inventář/
   HP systém postavy, na co by to mohlo navazovat.

5. **Denní/noční cyklus s rotující planetou** — technicky náročné kvůli
   propojení s gravitací/landed stavem, odložit na později, není
   kritické pro "biomy vypadají dobře".

6. **Povrchové POI** — až po základním biome systému, ne před ním.

Další logický krok z tohohle dokumentu by byl konkrétní prompt pro
Claude Code na "slope + height data do vertex/materiálu terénu" —
ale to necháme na chvíli, kdy budeme chtít pokračovat v implementaci,
ne v research fázi.
