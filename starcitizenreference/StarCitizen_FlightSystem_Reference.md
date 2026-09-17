# Star Citizen — pilotovací systém: kompletní referenční rozbor

Tento dokument popisuje, jak funguje letový/pilotovací systém ve Star Citizen,
včetně všech vrstev (IFCS, flight modes, power management, quantum travel,
VTOL/landing). Cíl: mít referenci, ze které budeme postupně vybírat prvky
k implementaci do gamespace — **ne** implementovat všechno najednou.

---

## 1. IFCS — Intelligent Flight Control System

Základní vrstva celého letu. IFCS je "asistenční systém", který stojí mezi
vstupem hráče (klávesnice/myš/joystick) a fyzickými thrustery lodi:

- Bez IFCS by loď reagovala čistě newtonovsky — každý impuls thrusteru
  trvale mění rychlost/rotaci, dokud ho nevyrušíš protilehlým impulsem.
- IFCS tohle zjednodušuje: interpretuje vstup hráče jako "chci letět/točit
  se tímhle směrem/rychlostí" a sám dopočítává potřebné impulsy thrusterů,
  včetně automatického brzdění při puštění vstupu.
- Filozoficky: IFCS dělá Newtonovskou fyziku ovladatelnou pro běžného
  hráče, aniž by se úplně ztratil pocit hmoty a setrvačnosti lodi.

**Náš stav:** Náš `SpaceshipPawn` dělá něco podobného už teď — `LinearDamping`
jako flight assist, manuální integrace v Tick. Je to zjednodušená verze
stejného principu.

---

## 2. Coupled / Decoupled mód

Přepínatelný mód (výchozí klávesa `V`), zásadně mění chování lodi:

- **Coupled** (výchozí): IFCS aktivně řídí — loď se snaží dosáhnout a
  udržet rychlost/směr, který nastavíš throttle/vstupem. Když pustíš
  vstup, loď se sama zpomalí/zastaví (aktivní brzdění, ne jen setrvačnost).
- **Decoupled**: IFCS přestává aktivně brzdit lineární pohyb. Loď si
  ponechá aktuální vektor rychlosti (setrvačnost jako v reálném vesmíru)
  a hráč může nezávisle přidávat rotaci/strafe navrch, aniž by to měnilo
  původní trajektorii. Používá se na rychlou změnu orientace (např. otočit
  se čelem k pronásledovateli, zatímco pořád letíš směrem, kterým jsi
  letěl předtím — "Kessel burn"/power slide manévr).
- Designový záměr CIG: decoupled má být krátkodobý nástroj na rychlou
  změnu orientace, ne trvalý stav pro boj ("turreting") — v decoupled jsi
  totiž snadný cíl, protože letíš předvídatelně po přímce.

**Náš stav:** Nemáme tenhle přepínač vůbec — naše loď je defaultně něco
mezi (Newtonian s dampingem jako flight assist, bez aktivního coupled
"snap to zero" brzdění). Freelook, co jsme udělali, řeší podobný problém
(rozhlížení bez měnění trajektorie) jinou cestou — jen pro kameru, ne pro
skutečnou rotaci lodi.

---

## 3. Flight Modes: Precision / SCM / Cruise (dřívější systém) → Master Modes SCM/NAV (aktuální)

Star Citizen měnil tenhle systém v průběhu vývoje. Dva modely, oba užitečné
k pochopení:

### Starší model (3 profily)
- **Precision Mode**: aktivní při vzletu/přistání. Nižší max. rychlost,
  přeškálovaný throttle pro jemné doladění v blízkosti objektů (docking,
  landing, boarding).
- **SCM (Space Combat Maneuvering)**: standardní bojový mód, plný rozsah
  6DOF manévrování při omezené (bojové) rychlosti.
- **Cruise Mode**: vysoká rychlost (5×+ SCM), ale IFCS uzamkne nos lodi
  na vektor pohybu — "manévrování" v cruise znamená hlavně korekci kurzu,
  ne bojové obraty. Výslovně NENÍ myšlený pro boj/asteroidová pole.

### Aktuální model (Master Modes)
- **SCM**: standardní zbraně/štíty aktivní, bojová rychlost a plná
  manévrovatelnost.
- **NAV**: aktivace deaktivuje zbraně, štíty se stáhnou do bufferu, a
  automaticky se spustí spool quantum drive — mód určený čistě pro
  cestování na velké vzdálenosti, ne pro boj.

**Design insight:** oba modely řeší stejný problém — vysoká cestovní
rychlost by v plně volném 6DOF manévrování byla nekontrolovatelná/nebezpečná,
takže hra násilně zjednoduší ovládání (uzamkne nos na vektor, vypne zbraně)
výměnou za tu rychlost.

**Náš stav:** Máme jen ORBIT/ATMOSPHERE/SURFACE přechody podle výšky —
to je jiná osa (výšková, ne rychlostní/účelová). Nemáme ekvivalent
Precision/SCM/Cruise ani SCM/NAV.

---

## 4. G-Safe a ComStab

Dva asistenční systémy chránící/usnadňující let, oba se dají vypnout:

- **G-Safe**: omezuje akceleraci/rotaci lodi tak, aby pilot nikdy
  neutrpěl G-LOC (ztráta vědomí z přetížení). Automaticky se **vypíná**
  při použití boost/afterburner (Left Shift) — tedy boost = rychlejší,
  ale riskantnější/míň chráněný let.
- **ComStab (Command-Level Stability)**: potlačuje pocit "sklouzávání"
  při zatáčení (bez něj loď při rotaci trochu "ujíždí" do strany, jako
  smyk). Vypnutí ComStab + G-Safe dohromady dává největší rozsah pohybu
  a nejrychlejší odezvu thrusterů, ale je nejnáročnější na ovládání.

**Náš stav:** Nemáme, ale koncept "vyšší riziko/kontrola výměnou za
výkon" už částečně máme u HEAT systému při atmosférickém vstupu.

---

## 5. ESP — Enhanced Stick Precision

Asistenční systém pro míření, ne pro let samotný:

- Kolem zaměřovacího kříže je neviditelný kruh. Jakmile se "pip" (predikce
  polohy cíle) dostane do tohoto kruhu, vstup z joysticku/myši se plynule
  ztlumí (dampuje) podle křivky.
- Cíl: zabránit přestřelení cíle při rychlém manévrování — bez ESP hráči
  typicky "oscilují" kolem cíle (přetočí, opraví, přetočí zpět).
- Velikost kruhu i křivka dampingu jsou nastavitelné v settings.

**Náš stav:** Nemáme (nemáme ještě ani zbraně/míření), ale je to dobrý
koncept si zapamatovat pro budoucí bojový systém.

---

## 6. Boost / Afterburner

Dva různé systémy zrychlení, ne jeden:

- **Boost**: přidává výkon do manévrovacích (ne hlavních) thrusterů —
  zvyšuje manévrovatelnost/rotaci, ne primárně rychlost vpřed. Zároveň
  IFCS srovná "prograde vector" před loď (pokud není). Vypíná G-Safe.
- **Afterburner**: používá samostatnou palivovou nádrž, přetěžuje hlavní
  thrustery pro vyšší přímou rychlost. Max. afterburner rychlost je
  relativní k aktuálnímu throttle — při 50% throttle dostaneš jen 50%
  max afterburner rychlosti. Typicky ~2× normální SCM max rychlost.

**Náš stav:** Máme "Boost" (`BoostMultiplier = 2.5`, Shift), ale je to
jednodušší — jeden systém, ne rozdělený na manévrovací vs. přímé zrychlení.
To je v pořádku pro náš rozsah, jen dobré vědět, že SC to řeší jemněji.

---

## 7. Power Triangle — správa energie

Herní mechanika, ne čistě letová, ale úzce propojená s výkonem lodi:

- Trojúhelníkový UI prvek rozděluje celkový výkon reaktoru mezi tři
  větve: **Weapons / Shields / Engines** (zbraně/štíty/pohon).
- Přesun výkonu k Engines = vyšší max rychlost, rychlejší boost regen,
  rychlejší rotace.
- Přesun k Weapons = víc výstřelů energetických zbraní, rychlejší dobíjení.
- Přesun k Shields = víc HP štítů, rychlejší regenerace.
- Typický vzorec: v boji přepínat mezi "vše do zbraní" (útok) a "vše do
  štítů" (obrana), cestovní přesun "vše do enginů" (rychlost/útěk).
- Odpojení výkonu od nepoužívaných systémů (např. vypnuté zbraně při
  cestování) = víc výkonu jinam a nižší detekovatelnost (EM signature).

**Náš stav:** Nemáme (nemáme ještě zbraně ani štíty) — relevantní až
ve chvíli, kdy budeme řešit boj/systémy lodi jako celek.

---

## 8. Quantum Travel — cestování na velké vzdálenosti

Vícefázový systém, ne jeden "teleport" příkaz:

1. **Výběr cíle** — přes starmapu (mobiGlas) nebo přímé zamíření na
   marker v HUD bez plánované trasy.
2. **Natočení lodi** na waypoint marker (může být i za tebou na startu).
3. **Spool** (výchozí klávesa `B`) — postupné "roztáčení" quantum drive,
   čas se škáluje podle vzdálenosti a třídy pohonu (stíhačky sekundy,
   velké nákladní lodě desítky sekund). HUD ukazuje % spoolu.
4. **Kalibrace** — souběžně se spoolem, systém počítá parametry skoku
   (směr, vzdálenost, palivo). Může ji zablokovat překážka mezi lodí
   a cílem (jiná loď, asteroid) — výjimka jsou "splined" skoky, co
   obepnou překážku obloukem.
5. **Engage** (držet `B`) — jakmile je spool i kalibrace 100%, skok se
   spustí. Vizuální "tunelový" efekt během cesty.
6. **Cooldown** po příletu — po dobu cooldownu nejde znovu skočit
   (ale lze mezitím spoolovat/kalibrovat další skok).

**Rizikové mechaniky:**
- **Interdiction**: nepřítel může "vytáhnout" loď z aktivního quantum
  letu (ambush mechanika).
- **EMP** může přerušit spool fázi a zabránit útěku.
- **Group jump**: víc lodí se dá synchronizovat na jeden leader jump.

**Design insight:** spool/kalibrace vytváří úmyslné okno zranitelnosti —
hráč je "vystavený" před skokem, což vytváří napětí/riziko i v čistě
cestovní mechanice, ne jen v boji.

**Náš stav:** Nemáme (nemáme multi-systémovou navigaci — jen jednu
planetu). Relevantní až ve chvíli, kdy přidáme víc objektů/systémů
ve vesmíru, mezi kterými má smysl "rychle cestovat".

---

## 9. VTOL a Landing Gear

- **VTOL** mód mění orientaci/chování hlavních thrusterů pro svislé
  přistání/vzlet (podobně jako tiltrotor) — přepínatelný stav vedle
  GEAR (podvozek nahoru/dolů).
- **GEAR**: vysunutí/zasunutí podvozku, obvykle nutná podmínka pro
  landed stav (bez vysunutého podvozku loď nemůže bezpečně stát).
- UI ukazuje stav čtyř přepínačů najednou: VTOL / CPLD (coupled) / ESP
  / GEAR — všechny čtyři jsou nezávislé, souběžně aktivní stavové
  přepínače viditelné na HUD.

**Náš stav:** Náš landing systém (L5) řeší koncepčně to samé (landed
stav, auto-vyrovnání), ale bez explicitního VTOL přepínače nebo
vizuálního landing gear — zatím na placeholder krychli to ani nedává
smysl. Až budeme mít skutečný model lodi, bude landing gear vizuálně
i mechanicky navazovat na tohle schéma.

---

## Shrnutí — co z tohohle systému dává smysl pro gamespace a kdy

Tohle je **hodně** na jednou implementovat a ani to nedává smysl — Star
Citizen na tenhle systém měl roky vývoje a celý tým. Doporučené pořadí,
KDYŽ/POKUD se rozhodneme jednotlivé prvky přidávat (ne teď, jen jako
mapa na budoucnost):

1. **Coupled/Decoupled přepínač** — nejsnazší přidat na náš současný
   flight model, dává okamžitý gameplay benefit (rychlá změna orientace
   bez ztráty trajektorie), navazuje přirozeně na freelook, co už máme.
2. **Precision mód u přistání** — už ho vlastně máme implicitně (LANDED
   stav zpomaluje/omezuje), jen bychom to mohli pojmenovat/rozšířit.
3. **Power triangle** — až budeme řešit zbraně/štíty (zatím nemáme ani
   jedno), tehdy dává smysl.
4. **Quantum travel** — až budeme mít víc než jednu planetu/systém.
5. **G-Safe/ComStab/ESP** — jemné doladění, spíš pozdější fáze polish,
   ne core mechanika.
6. **VTOL/Landing gear vizuál** — přirozeně naváže na skutečný model
   lodi z Meshy/Blender pipeline.

Nedoporučuju poslat tohle celé Claude Code jako jeden úkol — je to
referenční mapa. Až budeme chtít přidat konkrétní prvek (např. coupled/
decoupled), vytáhneme z tohodle dokumentu tu jednu sekci a uděláme
z ní přesně specifikovaný krok, stejně jako doteď.
