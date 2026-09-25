# Gamespace – handoff pro další session

> **Vstupním bodem je od 24. 9. 2026 `CLAUDE.md` v kořeni repozitáře** (krátký přehled, pravidla, příkazy) a skills v `.claude/skills/` (načítají se podle úkolu). Tento dokument nečti celý, hledej v něm grepem; zůstává jako historie a úplný seznam.


Stav k **19. 9. 2026**. Tento dokument je vstupní bod pro novou session (Claude Code) i pro autora
projektu. Popisuje, co projekt je, jak se s autorem pracuje, kde je co v kódu, co je hotové, co je
rozbité nebo neověřené a co následuje.

> **Pro novou session – začni takhle:**
> 1. Přečti celý tento dokument.
> 2. Přečti **master referenci** v `C:\gamespace\gamespace\starcitizenreference\` (kapitola 3).
> 3. Přečti `README.md` (technická dokumentace systémů, anglicky) a podle úkolu
>    `Docs/Ships/ShipPipeline.md` nebo `Docs/Characters/CharacterPipeline.md`.
> 4. Než cokoli změníš, přečti si pravidla spolupráce (kapitola 2).
> 5. Přečti **`Docs/WORKFLOW.md`**: postup jednoho kroku (Blender → Unreal → testy → balení →
>    snímky → commit), Blender MCP a úplný seznam nástrah, na kterých jsme se už spálili.

---

## 1. Projekt a vize

- **Gamespace** je sci-fi vesmírná hra v **Unreal Engine 5.8, C++**. Projekt je v
  `C:\gamespace\gamespace`, modul `gamespace`, repozitář
  `https://github.com/michaelkocandrle/gamespace` (větev `main`).
- Inspirace: **Star Citizen (hlavní vzor)**, Elite Dangerous a No Man's Sky. Cílem je seamless
  let z vesmíru až na povrch planety, vystoupení z lodi a chůze po planetě.
- Dnešní obsah:
  - hratelný prototyp s úvodní obrazovkou;
  - **flotila (přehled a plán v `Docs/Ships/Fleet.md`)**: čtyři plánované lodě, dvě odlišné
    fiktivní frakce/výrobci (Kestrel Dynamics = bojová/průzkumná technika, Halcyon
    Freightworks = nákladní/těžební technika). Vanguard je z Kestrel Dynamics (doplnit
    do jeho specu, vznikl před zavedením šablony);
  - jedna planeta **Veyra** (poloměr 120 km od 21. 9. 2026, předtím 25 km, atmosféra 12 km, gravitace 6 m/s²);
  - kulisy: měsíc **Keth** a plynný obr **Orun** s prstenci;
  - loď **Vanguard**: od 18. 9. 2026 model z Meshy („Ironclad Starfighter“), 14 × 11,4 × 6,2 m se
    4 motorovými gondolami, zpracovaný receptem `Tools/Blender/build_ai_ship.py` (kapitola 5, bod 20).
    Původní procedurální model (17,6 m) je v `ArtSource/Ships/Vanguard/Vanguard.blend` jen pro historii;
  - druhá loď **Steadfast** (výrobce Halcyon Freightworks, nákladní/průzkumná, posádka 3,
    pomalejší a větší než Vanguard) — rozjeto 23. 9. 2026, autor pracoval z jiného PC bez
    Claude Code. Hotovo: jméno a specifikace `ArtSource/Ships/Steadfast/Steadfast_spec.json` (design/identity list, NENÍ totéž co funkční `*_setup.json` build config jako u Vanguardu)
    (rozměry/let jsou odhady, přeměřit po importu jako u Vanguardu), hrubý exteriér z Meshy
    (Smart Topology, vysoký polygon count, ještě nestažený/needitovaný v Blenderu), koncept
    interiéru `ArtSource/Ships/Steadfast/Concept/interior_hero.png` a rozpis dílů
    `ArtSource/Ships/Steadfast/Kitbash/interior_kitbash_parts.json` (revidováno podle nového
    pravidla v `Docs/AssetPipeline_Modular.md` — všechny funkční díly procedurálně, ne z AI).
    Další krok: stáhnout exteriér z Meshy, naimportovat podle `Docs/Ships/ShipPipeline.md`,
    pak procedurální detail interiéru přes Blender MCP;
  - postava na nohou (placeholder UE Manny).
- **Další velký cíl autora:** letový systém lodi má být **kompletní kopie systému ze Star
  Citizen**. Nemá vzniknout najednou, ale po krocích (kapitola 10).

---

## 2. Autor a pravidla spolupráce (DŮLEŽITÉ)

- **Komunikace česky.** Autor **není herní vývojář** a nezná UI Unreal Editoru. Všechno dělej
  kódem a skripty, ne návodem „klikni v editoru“. Když se editoru nejde vyhnout, dej číslované
  kroky s přesnými názvy.
- Na konci každého kroku autor chce:
  - přesný **testovací scénář** (co spustit, co zkusit, co má vidět);
  - informaci, jestli stačí **Live Coding**, nebo je nutný **restart editoru**;
  - **rizika** a co je neověřené.
- **Vizuální změny si ověř sám snímky** (kapitola 9, `Tools\Shots.ps1`), než řekneš, že je hotovo.
  Autorovi pak napiš, co jsi na snímcích viděl, a odděl, co musí posoudit on sám (pocit z ovládání,
  plynulost, zvuk).
- **Neměřit ani netestovat v PIE či okně editoru bez vyžádání** („ne laskavě už proteď nic
  neměř“). Testuj **headless** (`Tools/run_editor_python.ps1`) a autorovi napiš scénář.
  Okno editoru mu kradlo myš a klávesnici.
- **Ručně vyrobené input assety** (`IA_*`, `IMC_Spaceship`, `IMC_Character`) **nikdy znovu
  nevytvářej ani nepřepisuj**. Mapování jen přidávej přes `gamespace_assets.add_mappings()`.
- **Nikdy neměň bezpečnostní nastavení Windows.** Smart App Control autor 16. 9. 2026 vypnul,
  moduly v `gamespace.Build.cs` se proto přidávat smí. Když build selže na Code Integrity
  (3077 / 0x800711C7), řekni to autorovi a nic neměň.
- **Git (pokyn autora 17. 9. 2026): všechno, co uděláš, vždy commitni a pushni do repozitáře**
  https://github.com/michaelkocandrle/gamespace/tree/main (remote `origin`, větev `main`).
  - Commit a push po každém dokončeném kroku, i po drobných opravách a úpravách dokumentace.
  - Nic nenechávej jen lokálně. Před commitem zkontroluj `git status`, jestli se tam nedostalo
    něco, co tam nepatří.
  - Commit message končí řádkem `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
  - Nahrazuje dřívější pravidlo „nepushovat, pushuje autor“.
- Autor hraje hlavně **zabalenou hru** (`C:\gamespace\Builds\Gamespace`), ne PIE. Po změnách
  obsahu nebo C++ je proto potřeba znovu spustit `Tools\Package.ps1`.
- Velké úkoly autor chce **dělit do kroků**. Nedělej obří změny najednou, domluv rozdělení.

---

## 3. MASTER REFERENCE: `C:\gamespace\gamespace\starcitizenreference\`

**Tahle složka je hlavní reference toho, jak si autor hru představuje.** Autor do ní bude
průběžně přidávat další podklady (texty, případně obrázky nebo videa). Před každým návrhem
herního systému, hlavně letového, se do ní podívej a drž se jí. Když je v rozporu s tímto
dokumentem nebo s README, **platí reference**. Doptej se, pokud není jasné, co se má převzít.

Obsah k 17. 9. 2026:

| Soubor | O čem je |
| --- | --- |
| `StarCitizen_FlightSystem_Reference.md` | Rozbor pilotování ve Star Citizen: IFCS, coupled/decoupled, flight modes (Precision/SCM/Cruise → master modes SCM/NAV), G-Safe a ComStab, ESP, boost vs. afterburner, power triangle, quantum travel (výběr cíle, spool, kalibrace, engage, cooldown, interdikce), VTOL a landing gear. Obsahuje doporučené pořadí zavádění. |
| `SpaceEnvironment_Reference.md` | Vesmírné prostředí: měřítko vesmíru (1:1 + quantum travel vs. zmenšené vzdálenosti), obsah mezi planetami (asteroidová pole, vraky, mlhoviny, stanice, signály), procedurální vs. ručně dělaný obsah, hazardy, skybox. Doporučení: realistické vzdálenosti + quantum travel, malý ručně navržený systém. |
| `PlanetaryBiomes_Reference.md` | Planetární biomy: více biomů na planetu (Starfield styl), sklon a výška do materiálu terénu, Material Parameter Collection, počasí, den a noc, povrchové POI. |
| `Gamespace_ReferenceLibrary_Plan.md` | Plán dalších referenčních témat (ekonomika a těžba, zbraně a štíty, EVA, mise a AI, UI a navigace). |

**UI reference: `Docs/UI/`** (pro krok **SC-1c**, viz kapitola 10):

| Soubor | O čem je |
| --- | --- |
| `SC_ThrottleHUD_VisualReference.md` | Rozbor letového HUD ze Star Citizen: svislý pruh rychlosti vůči limitu s barevným kódováním, G-metr pod ním, malé stavové indikátory (CPLD, ESP, LOCK / VTOL, GEAR, GSAF), symetrické rozložení kolem středu, tenké cyan linky místo plných panelů, pruh paliva. Doporučuje UMG místo Canvas. |
| `SC_throttle_hud_reference.png` | Screenshot kokpitu SC, ke kterému se dokument vztahuje. |

Pozor:
- Úseky „Náš stav“ v referencích byly psané před posledními kroky a místy jsou zastaralé. Náš
  let už má SC-1a a SC-1b: coupled/decoupled podle SC, SCM/NAV, omezovač, G-Safe, ComStab, VJoy, boost a afterburner s
  vlastní energií a palivem a cruise (J, jen NAV). Aktuální stav je
  v kapitole 5.
- Složka je v gitu (autor ji commitnul 17. 9. 2026).

---

## 4. Prostředí a příkazy

| Co | Kde / jak |
| --- | --- |
| Engine | `C:\Program Files\Epic Games\UE_5.8` |
| Projekt | `C:\gamespace\gamespace\gamespace.uproject` |
| Hratelný build | `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe` (Development, složka je samostatná) |
| Blender 5.2 | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; z Git Bash volat s `MSYS_NO_PATHCONV=1` |
| Python | systémový Python 3.13 s numpy a scipy (generátory zvuku a textur) |

Příkazy (PowerShell, pracovní složka `C:\gamespace\gamespace`, **editor musí být zavřený**):

```
# Build editoru (C++)
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" gamespaceEditor Win64 Development -Project="C:\gamespace\gamespace\gamespace.uproject" -WaitMutex -FromMsBuild

# Python skript headless v editoru (assety, testy). Spouštět nástrojem PowerShell, ne přes bash
# (jinak se rozbije $PSScriptRoot).
.\Tools\run_editor_python.ps1 Tools\Tests\test_flight_modes.py

# Zabalená hra (~5 min) + kontrola, že v buildu jsou zvuky, input a materiály
.\Tools\Package.ps1

# Spuštění zabalené hry (bez parametrů s nastavením ze hry)
.\Tools\Play.ps1
```

- **Live Coding vs. restart:** nové soubory, nové `UPROPERTY` nebo `UFUNCTION` a změny hlaviček
  vyžadují zavřít editor a udělat plný build. Změny jen v tělech funkcí jdou Live Codingem.
- Pracovní postup po změně: build → headless skript nebo testy → `Package.ps1` → commit a push →
  odpověď autorovi s testovacím scénářem.

---

## 5. Stav vývoje – co je hotové

Od nejstaršího (vše je commitnuté a pushnuté na GitHub):

1. **Základ lodi:** `ASpaceshipPawn` s ručně integrovaným 6DOF letem, Enhanced Input, chase a
   cockpit kamerou, myší jako virtuálním joystickem a debug HUD.
2. **L1 – přesnost:** Large World Coordinates a vlastní world origin rebasing
   (`USpaceOriginRebasingSubsystem`, rebase po 40 km).
3. **L2 – planeta:** `AQuadSpherePlanet`, tedy quad-sphere terén s LOD, analytickou výškovou
   funkcí (`PlanetTerrain`), horizon cullingem a asynchronním stavěním dlaždic. Kolize jsou
   samostatné dlaždice kolem hráče, včetně synchronního warm-upu pod lodí.
4. **L3 – atmosféra:** Veyra zvětšená na 25 km. Hustota vzduchu, odpor a gravitace se mění s
   výškou, přibyl entry heat s třesením kamery a obloha se v atmosféře prolíná do modré.
5. **L5 – přistání:** stavy Flying / Settling / Landed, zarovnání na terén, tření na svahu,
   kontrola sklonu, odpočet dosednutí v HUD.
6. **L6 – postava:** `APlayerCharacter` se sférickou gravitací, paralelně přenášeným gravity
   frame pro kameru, nativní animací (bez Animation BP) a foot IK z výškové funkce. Umí vystoupit
   z lodi a nastoupit do ní (F).
7. **Pipeline lodí:**
   - Blender export add-on (`Tools/Blender/gamespace_ship_export.py`) s validací a manifestem.
   - Import do UE (`Tools/Assets/import_ship.py`) s kontrolami, materiály
     (`ship_materials.py`) a ručním laděním z `ArtSource/Ships/<Loď>/<Loď>_setup.json`.
   - Loď Vanguard: 9 kolizních UCX hullů, 11 socketů, 13 materiálových instancí.
8. **Free look** (pravé tlačítko myši): kamera se otočí o celých 360° a vrací se kratší cestou.
9. **Letové režimy** (krok před tímto):
   - flight assist (V) s pákou plynu, detentem na nule a držením výšky;
   - FA off = čistá newtonovská setrvačnost;
   - all stop (X);
   - boost s energií;
   - cruise drive (J) s rychlostním limitem podle výšky, až 6 km/s;
   - zoom kamery kolečkem, FOV kick, třes kamery;
   - světla trysek podle výkonu, blikající poziční světla, prach v prostoru.
10. **Vrstvený zvuk** (procedurální placeholdery): hum, trysky, boost, cruise, one-shoty, dosednutí.
11. **Živá obloha:**
    - slunce s korónou, mlhoviny a blikání hvězd (vše v materiálu `M_Starfield_Sky`);
    - `ADistantBody` pro měsíc Keth (obíhá Veyru) a obra Orun s prstenci.
12. **Opravy výstupu z lodi:**
    - Kořenový kolizní box lodi ignoruje pawny, postava naráží do UCX hullů.
    - Místo výstupu se hledá, dokud není volné, a postava je otočená k lodi.
    - Záchranná síť proti propadnutí terénem.
13. **Hratelný build (tento krok):**
    - úvodní obrazovka (`/Game/Maps/MainMenu`: Hrát / Nastavení / Konec, loď a plynný obr v
      pozadí, ambient hudba);
    - pauza na Escape (F10 v PIE);
    - nastavení (grafika, zvuk, ovládání, HUD, FPS), ukládají se do `GameUserSettings.ini`;
    - H funguje globálně přes `ASpacePlayerController`;
    - oprava cookování: assety načítané podle cesty chyběly v buildu, proto nebyl zvuk a
      nefungovalo H.
    - Autor build ověřil 17. 9. 2026: menu, nastavení, zvuk, H, Escape i výkon jsou v pořádku
      (výjimky jsou v kapitole 10).
14. **SC-1a – jádro IFCS podle Star Citizen** (17. 9. 2026):
    - trysky mají zrychlení zvlášť pro každý směr (main, retro, strafe, nahoru, dolů) a rotace má
      setrvačnost (úhlové zrychlení);
    - coupled: držená klávesa chce rychlost až do limitu, puštěná osa se zabrzdí. Páka plynu
      zmizela. Decoupled drží vektor rychlosti;
    - spacebrake (držet X), omezovač rychlosti na kolečku (zoom je teď Alt + kolečko);
    - master modes SCM a NAV (B, přepnutí trvá 2 s), cruise (J) funguje jen v NAV;
    - G-Safe (K) a ComStab (L);
    - myš jako virtuální joystick SC s kruhem a kurzorem v HUD;
    - entry heat se nově měří proti 200 m/s (rychlost SCM).
15. **Opravy po SC-1a** (17. 9. 2026): výstup z lodi (postava vedle lodi, kamera normálně daleko)
    a zobrazení kvality grafiky v menu (kapitola 11).
16. **SC-1b – boost a afterburner** (17. 9. 2026):
    - boost (Shift) zesiluje jen manévrovací trysky (retro, strafe, nahoru, dolů) a rotaci a po
      dobu hoření vypíná G-Safe. Hlavní tah ani rychlost nemění;
    - afterburner (Tab + W, jen SCM) zesiluje hlavní tah a zvedá rychlostní limit na SCM × 2 ×
      omezovač. Má vlastní palivo na 8 s hoření a doplňuje se 40 s. Po vyhoření nebo puštění se
      limit 4 s plynule vrací. G-Safe nevypíná;
    - hodnoty jsou ve `Vanguard_setup.json`, HUD má řádek AFTERBRN a stav boostu na řádku IFCS;
    - **ladění 17. 9. 2026:** tah ×2,1, rychlost ×2,5 (Vanguard 525 m/s), náběh limitu 0,25 s,
      silnější FOV a třes. Palivo a G-Safe zůstaly: se zapnutým G-Safe je zrychlení pořád stropované
      na 7 G, takže z SCM na maximálku je to 4,4 s, bez G-Safe (Shift+Tab nebo K) 1,8 s z 8s nádrže.
17. **SC-1c – letový HUD v UMG** (17. 9. 2026), podle `Docs/UI/`, včetně vizuálního polishe podle
    referenčních screenshotů (kapsle se zaoblenými konci a přechodem, pilulkové indikátory, rohové
    konzoly, tenká technická typografie, vrstvená záře):
    - vlevo od středu kontrolky SCM/NAV, CPLD, GSAF, CSTB, BOOST, svislý ukazatel rychlosti
      (výplň = rychlost, značka = omezovač, červená zóna = let pozpátku), rychlost a limit malým
      písmem, G-metr;
    - vpravo ukazatele energie boostu a paliva afterburneru, uprostřed virtuální joystick;
    - celé v C++ (`USpaceFlightHud`, bez widget Blueprintu), tenké průhledné cyan linky;
    - kompaktní textový debug HUD už neukazuje SPEED, IFCS ani AFTERBRN, plný (H) ano.
18. **Oprava kamery v kokpitu a workflow vizuální kontroly** (17. 9. 2026): sklo canopy se pilotovi
    skrývá, oko je na (500, 0, 110) a vybralo se podle snímků; snímky ze zabalené hry umí
    `Tools/Shots.ps1` (kapitola 9).
19. **SC-2a – podvozek a precision mode** (18. 9. 2026, rozsah potvrzený autorem):
    - podvozek na **N** se vysouvá a zasouvá 2 s a jde otočit v půlce. Bez vysunutého podvozku loď
      **nedosedne** (blokátor `GearUp`, HUD `GEAR UP - lower it (N)` a červeně blikající kontrolka GEAR
      už od 30 m). Když loď stojí, zasunout podvozek nejde;
    - **vizuál podvozku:** Vanguard měl nohy už vymodelované, jenže napevno spojené s trupem (byly vidět
      i za letu). `Tools/Blender/split_ship_gear.py` je oddělil do dílu `SM_Ship_Vanguard_Gear`, ten
      prošel pipeline a kód ho při zasunutí posune o 95 cm do břicha a skryje. Loď stojí přesně tam,
      kde dřív (patky = spodek kolizního boxu, `gear_extension_cm` 0). Lodě bez dílu `_Gear` dostanou
      zástupné nohy z válců na socketech `Gear_*`;
    - **precision mode:** zapne se s podvozkem a vypne s ním, ručně ho přepíná **P**. Strop je SCM × 0,15
      (Vanguard 31,5 m/s) a omezovač funguje uvnitř (zub kolečka = ~1,6 m/s). Otáčení × 0,45, jen
      v SCM, afterburner je odmítnutý. Když se zapne ve 200 m/s, loď zabrzdí retro tryskami (~5 G);
    - HUD má kontrolky GEAR a PREC a ukazatel rychlosti se přeškáluje na precision strop;
    - snímky: nová pole scénáře (`gear`, `lower_gear`, `precision`, `chase_yaw` / `chase_pitch` /
      `chase_zoom`), scénář `landing`, loď umí ve snímku opravdu přistát.
20. **Vanguard z Meshy – první průchod „AI model → hratelná loď“** (18. 9. 2026, varianta C autora):
    - recept `ArtSource/Ships/Vanguard/Vanguard_ai_build.json` + obecný skript `Tools/Blender/build_ai_ship.py`
      postaví z originálu (3,36 mil. trojúhelníků, `ArtSource/Ships/Vanguard/Meshy/`) `Vanguard_Meshy.blend`
      za 3 minuty: otočení (Meshy mělo příď na −X), 14 m, vyříznutí srostlých ližin do dílu `Gear`,
      decimace na 200 tis. + 14 tis. (podvozek) s důrazem na vršky, příď a kabinu, **nové UV a přepečení**
      barvy, ORM a normal mapy z originálu, 10 kolizních hullů, 11 socketů (4 motory, 3 nohy);
    - proč přepečení: UV atlas Meshy má tisíce malých ostrůvků, decimace je slepila a na kovu vznikaly
      fleky; normal mapa z Meshy je skoro prázdná, detail je v geometrii;
    - Unreal: nový master `M_Ship_PBR` (textury místo barev po slotech), trysky dál přes `M_Ship_Hull`
      s emisí; `import_ship.py` umí naimportovat mesh načisto, když se změnily sloty, a uklidit, co už nic
      nepoužívá (komponenta Canopy, 12 starých MI, canopy mesh); úvodní obrazovka skládá loď z manifestu;
    - kamera: rameno 27 m, výška 5,7 m (vybráno porovnávacími snímky), oko kokpitu (410, 0, 145);
    - barva: Meshy maluje trup velmi tmavě (albedo ~0,04 lineárně, starý Vanguard 0,34) a z 85 % kovově,
      ve hře byla loď černá silueta. `base_color_tint` 2,2 a `metallic_scale` 0,5 v `Vanguard_setup.json`
      ji dělají tmavě modrošedou; ladí se bez nového buildu v Blenderu (jen import + balení);
    - postup pro další lodě je v `Docs/Ships/ShipPipeline.md`, kapitola 2B; nový scénář snímků `ship_views`.
21. **Provizorní kokpit** (18. 9. 2026): model z Meshy nemá interiér, z kokpitu nebylo vidět nic z lodi.
    `bPlaceholderCockpit` (v `Vanguard_setup.json` `placeholder_cockpit`) postaví kolem oka pilota
    jednoduché tmavé kvádry: šikmý přístrojový panel se třemi obrazovkami a hranou 16° pod horizontem
    (pod HUD, ~77 % výšky obrazovky), sloupky rámu kabiny ~30° vlevo a vpravo a sedadlo za zády. Jen
    v pohledu z kokpitu, bez kolize a stínů. Rozložení podle SC reference v `Docs/UI/` a snímků;
    oko zůstalo (410, 0, 145), uvnitř kabiny (340, 0, 140) prosvítal zevnitř model. Test
    `test_cockpit_frame.py`. Ve Vanguardu ho 18. 9. 2026 nahradil skutečný interiér (bod 22); v kódu
    zůstal pro lodě bez interiéru.
22. **Interiér kokpitu z Meshy** (18. 9. 2026): vana kokpitu (deska s obrazovkami, konzole, side-sticky,
    pedály; 1,27 mil. → 120 tis. trojúhelníků, nové UV a přepečené textury 2K) jako díl
    `SM_Ship_Vanguard_Interior`, sekce `interior` v `Vanguard_ai_build.json`:
    - usazení našel nový `Tools/Blender/fit_ship_interior.py`: vana celá uvnitř trupu (2 cm), okraj
      ~15 cm od stěn kabiny, měřítko 0,95 (výška × 0,95), okraj na úrovni zábradlí canopy jako u stíhačky;
      „co největší, co se vejde“ nešlo – deska by došla ke stropu canopy a oko by nemělo kam;
    - **oko se posunulo na (305, 0, 156)** nad sedadlo za sticky, 22 cm pod strop; deska 15° pod okem
      (pod HUD). Výš to nejde: střecha canopy se k čelnímu sklu svažuje a z oka na 163 cm byla vidět
      z boku jako světlý pruh přes HUD – nástroj proto hledá oko s čistým výhledem 0–6° nad horizont;
    - **výstelka** `SM_Ship_Vanguard_Lining`: trup je jednostranný, z kokpitu byl neviditelný a pilot
      viděl podlahou a boky na zem. Build kopíruje stěny trupu kolem kokpitu otočené dovnitř (textura
      trupu), mimo zasklení canopy;
    - **úklid canopy:** plochy uvnitř canopy mířící do kabiny (spodky rámu, zvenku za neprůhledným
      zasklením nejsou vidět) build maže;
    - **kokpitové světlo** (`cockpit_light_*` v setupu): trup kabinu stíní, interiér byl skoro černý;
      bodové světlo mezi okem a deskou, 12 cd, bez stínů, musí zůstat pod střechou canopy (nad ní svítilo
      na canopy zvenku);
    - `placeholder_cockpit` vypnutý.
23. **Tmavý interiér, displeje s HUD a oko dál od desky** (18. 9. 2026): interiér z bodu 22 nahradila
    tmavá varianta z Meshy (`Interior/Meshy/Spaceship_Cockpit_0918171055/`, matná, metallic 0), stejným
    postupem (decimace na 150 tis., fit, nové UV, přepečení 4K s víc texelů tam, kam pilot kouká):
    - **oko (174, 0, 189)**, 65 cm za bočními páčkami, ~1,5 m od desky. Rámování podle SC reference
      `Docs/UI/Screenshot 2026-09-17 201854.png`: horní hrana desky 8° pod okem (reference ~8°), displeje
      14–25° (reference 15–24°). Předtím (305, 0, 156), 0,75 m od desky, displeje u spodního okraje.
      Usazení vany: měřítko 1,15, offset (2,45, 0, 1,25); ověřeno `fit_ship_interior.py`,
      `cockpit_view_survey.py` (70 % výhledu volné) a porovnávacími snímky `cockpit_tune`;
    - **displeje:** AI malované ciferníky nejdou přečíst (limit generativních textur), takže build
      (`interior.displays` v receptu) vyřízne plochy obou velkých obrazovek a dá místo nich ploché
      quady se slotem `M_Ship_Vanguard_Screens`, UV vedle sebe přes jednu texturu (levý = levá půlka).
      Hra do ní kreslí `USpaceCockpitDisplays` (widgety HUDu, stejné názvy, stejný `ApplyState`) přes
      `UCockpitDisplayComponent` (render target 1024 × 448, 30× za s, jen v pohledu z kokpitu).
      Materiál `M_Ship_Screen` je **unlit** (osvětlené sklo odráželo denní oblohu a slévalo obsah).
      Rozvržení: **vlevo FLIGHT** (SCM/NAV, rychloměr, rychlost, omezovač, G-metr), **vpravo SYSTEMS**
      (CPLD, GSAF, CSTB, BOOST, GEAR, PREC, sloupce BST a AB) – jako u SC: let vlevo, systémy vpravo;
    - **hlavní HUD zůstává**, jen kompaktnější (kontrolky vedle rychloměru jako v SC, kratší sloupce,
      o 50 px výš), aby byl celý nad deskou. Důvod: v chase kameře displeje vidět nejsou, a i v kokpitu
      je rychlý údaj v úrovni horizontu (SC to má stejně: letový HUD ve výhledu, MFD pro systémy).
      Displeje svítí i s HUD vypnutým (H) – jsou součást lodi;
    - kokpitová světla: klíčové 80 cm před okem (dosah 250 cm), výplňové nad hlavou, obě měkká (12 cm);
      při změně oka v shotech (`cockpit_eye`) se posouvají s ním.
24. **Tmavý kokpit jako v SC** (18. 9. 2026, krok A podle autorova srovnání se SC): deska byla plošně šedá
    od klíčového světla 12 cd (bez kokpitových světel je úplně černá – slunce ji nesvítí). Teď:
    - **displeje svítí do kokpitu**: u každého socketu `Display_*` (build je dává 3 cm před obrazovky)
      plošné světlo 8 cd, modrozelené (0,4 / 0,75 / 1), bez stínů, dosah 160 cm, natočené k oku
      (`components.cockpit_displays` v setupu);
    - klíčové světlo 1,5 cd, výplňové 0,8 cd, interiér ztmavený (`base_color_tint` 0,6);
    - **vnitřek rámu canopy** má vlastní tmavý slot `M_Ship_Vanguard_CanopyFrame` (recept `canopy_frame`:
      plochy trupu v boxu, které oko vidí zepředu; zvenku jsou odvrácené) – předtím svítil barvou trupu
      jako světlé dráty přes výhled;
    - ladění podle snímků: pole shotu `cockpit_light` [klíčové, výplňové], `display_light`, `interior_tint`,
      scénář `cockpit_light` (nastavení ze setupu, staré šedé, bez světel, ve vesmíru, v atmosféře).
25. **HUD podle současného SC** (19. 9. 2026, krok B podle autorova „1:1“): rozložení prvek po prvku podle
    `Docs/UI/Screenshot 2026-09-17 201854.png` (změřeno v 1080p od středu), barvy ledově azurové a téměř
    bílé místo zelené ze SC-1c, písmo Rajdhani Medium se slabou září. Nové: kurzová páska, žebřík sklonu,
    výšková páska v km, R-ALT / VSI / ATMO, gyro s rychlostí otáčení, štít G-Safe, kříž strafe, ikona
    režimu s pod-režimem, odznaky přepínačů (jen zapnuté), řádky BOOST / LIMIT a GEAR / CRUISE. Vynechané:
    palivo H/Q, DECOY/NOISE, GUN – hra ty systémy nemá a HUD nic nepředstírá. Oprava: obrysy (trubice,
    odznaky, pilulky na displejích) se kreslily jako plné světlé plochy. Podrobnosti v README („Flight HUD“).
26. **Displeje jako SC MFD a vlastní písmo** (19. 9. 2026):
    - obrazovky rozšířené přes boční lišty s tlačítky na ~38 × 25 cm (1,5 : 1), render target 2 × 640 × 420;
    - styl SC MFD: tmavě modré sklo, titulek nad linkou, dole lišta stránky „< FLIGHT >“. Vlevo FLIGHT:
      rychlost, omezovač, G velkým písmem, pilulka režimu, sloupce SPD/BST/AB/G (jako SC power management).
      Vpravo SYSTEMS: seznam jako SC kontakty – COUPLED, G-SAFE, COMSTAB, BOOST, PRECISION, GEAR s pilulkou
      přepínače, CRUISE se stavem;
    - **vlastní písmo:** první .ttf/.otf v `Content/UI/Fonts/Custom/` použije HUD i displeje (pak zabalit hru).
      Složka je v `.gitignore` – písmo, které se nesmí šířit, se tak nedostane na GitHub. Ověřeno s dočasně
      vloženým Roboto Light;
    - **oprava:** písma HUDu se do zabalené hry nikdy nedostala (`DirectoriesToAlwaysStageAsUFS` měl cestu
      `Content/UI/Fonts` místo `UI/Fonts`), HUD v balíčku tak vždy ukazoval záložní Roboto. `Package.ps1`
      teď kontroluje, že písma v buildu jsou.
27. **Ostré displeje za letu, zpět v rámu** (19. 9. 2026, podle autorova snímku: MFD rozmazané a mimo rám):
    - obrazovky zase přesně ve skle rámečku (29 × 25 cm), layout 560 × 490 (stejný poměr);
    - **hlavní příčina rozmazání: Nanite.** Interiér letí s kamerou a Nanite mu za rychlého letu dávalo
      špatné pohybové vektory; časové vyhlazování (TSR) pak míchalo obraz z nesprávného místa – rozpadal
      se text i rám (ověřeno: s `r.Nanite 0` ostré, s FXAA bez rozpadu). Interiér je teď bez Nanite
      (`no_nanite_parts` v setupu, import to čte);
    - render target se kreslí v rozlišení, v jakém je displej vidět (podle šířky okna, `ScreenShareAt88`),
      písmo se tak rasterizuje v cílové velikosti; mění se jen při změně okna (dřív reagoval na FOV
      afterburneru a přealokovával se každý snímek);
    - materiál displeje s příznakem pixelové animace; kokpitová kamera bez motion bluru; jas 1,8; 60 Hz;
    - zkoušené a zamítnuté: průhledný materiál s responsive AA (bez pohybových vektorů se při třesení
      zdvojovaly řádky), mipmapy render targetu (engine je pro tenhle případ nevystavuje);
    - nástroje: pole shotu `console` (konzolové příkazy), `space.CameraShake` (násobitel třesení kamery),
      scénář `display_sharpness` (displeje za rychlého letu).
28. **MFD jako v SC, plocha uvnitř rámu, pomalejší číslice** (19. 9. 2026, autor: pořád záškuby, nesedí do
    rámu, nepůsobí jako skutečné MFD):
    - plocha obrazovky zmenšená o ~8 mm dovnitř otvoru rámečku (otvor není obdélník: šikmý spodek,
      zaoblené rohy); kolem zůstává tmavý okraj původního skla;
    - vzhled podle SC MFD: sklo (modrý přechod, jemná mřížka, ztmavení ke krajům, odlesk nahoře, tenký
      rámeček), sloupec „fyzických“ tlačítek u vnitřní strany (vlevo CPLD/GSAF/CSTB/BOOST/PREC, vpravo
      MODE/GEAR/CRUISE; zapnuté svítí výplní), záložka stránky jako pilulka, blokové sloupce SPD/BST/AB/G
      (jako SC power management), vpravo seznam STATUS s hodnotami v pilulkách (jako SC komunikace);
    - **čísla na displejích se mění 5× za sekundu** (`state_rate_hz` v setupu), sloupce a kontrolky dál
      plynule 60×. Časové vyhlazování (TSR) míchá číslo, které se mění každých pár snímků, s předchozím;
      podrženo ~200 ms se ustálí. Vyzkoušené a zamítnuté: pixelová animace sama, průhledný materiál
      s responsive AA (i s výstupem rychlosti), průhlednost až po TSR (rozmazané i v klidu), vypnutí
      anti-flickeru TSR a kratší historie TSR.
29. **Blender MCP a displeje přesně do rámu** (19. 9. 2026):
    - nainstalovaný Blender MCP (ahujasid/blender-mcp, PyPI `blender-mcp` 2.0.0): `uv` přes winget, server v Claude
      Code (`claude mcp add blender`, scope local pro C:\gamespace, s plnou cestou k `uvx.exe` a
      `DISABLE_TELEMETRY=true` – balíček jinak posílá anonymní statistiky a se souhlasem i prompty, snímky
      a stav scény na Supabase autora), doplněk `blender_mcp_addon` v Blenderu 5.2 (z balíčku, souhlas
      s telemetrií vypnutý). Doplněk po startu Blenderu s GUI otevře server na `localhost:9876`, který
      spouští libovolný Python v Blenderu (jen lokálně). V dávkových `-b` bězích pipeline se jen zaregistruje;
    - MCP nástroje (31: scéna, snímek viewportu, `execute_blender_code`, …) se v Claude Code načtou
      v nové relaci; `get_scene_info` a spol. chtějí argument `user_prompt` (stačí prázdný);
    - první použití: v živém viewportu z oka pilota (kamera 174/0/189 cm, FOV 88°, backface culling jako
      v Unrealu) s měřicí mřížkou na rovině displejů se ukázalo, že otvory rámečků nejsou obdélníky
      (pravý se naklání). Displeje mají teď v receptu `corners` (4 rohy otvoru) místo `rect`; build
      vyřízne AI sklo uvnitř obrysu a dá tam čtyřúhelník. Levý displej sedí na rám, pravý má dole vlevo
      zubatou hranu samotného rámu (decimovaná AI geometrie);
    - opraveno: `ModeColor` v HUDu kolidoval v unity buildu hry se stejnojmennou konstantou v `SpaceDebugHUD.cpp`.
30. **Doladění vzhledu** (19. 9. 2026): `space.Hud` má čtyři režimy – 0 skrytý, **1 jen letový HUD (výchozí, jako
    SC, bez textového panelu)**, 2 s kompaktním textem, 3 s plným textem; H je projde dokola, menu je nabízí.
    Čísla na MFD se při rychlé změně ukazují po krocích (rychlost po 10 m/s, G po 0,5), přesně až když se
    ustálí (`USpaceCockpitDisplays::Steady`). Prach tenčí a kratší (3 cm, 22 ms, max. 25 m, jas 1,6). Vzpěry
    canopy tmavý kov (0,06, metallic 0,6, roughness 0,35) místo matné černé.
31. **Střední sloupek desky: RADAR a SELF STATUS** (19. 9. 2026, WORKFLOW kap. 10 bod 1):
    - oba malé čtverce mezi MFD jsou živé displeje. Otvory změřené přes Blender MCP z oka pilota (paprsky
      → rovina skla se stejným sklonem jako velké MFD, flood fill, obrys v přiblíženém pohledu z oka opravený
      podle skla; spodní hrany jsou vodorovné, v pravém dolním rohu je na rámečku knoflík) a zapsané do
      receptu jako `centre_top` a `centre_bottom` (11 × 13,5 a 11 × 12 cm). Řez jen 6 mm hluboko
      (`cut_depth_m`), aby knoflíky zůstaly;
    - plátno displejů má 1330 × 490 px (dva MFD a sloupek 210 px), každý displej dostal v receptu
      `texture_rect` (`texture_size`), stejná hustota pixelů jako MFD a poměr stran jako sklo;
    - **RADAR** podle středu desky v SC referenci: pohled shora s nosem nahoru, dosah 5 km (kruhy po
      třetinách), výseč výhledu pilota (88°), kontakty v dosahu (pawny a static meshe s kolizí) jako kosočtverce
      na „stopce“ podle výšky, tělesa (Veyra, Keth, Orun) jako značka se začátečním písmenem na okraji – jen
      když leží do 60° nad/pod křídly (planeta pod lodí se neukazuje). Dole kurz a počet kontaktů;
    - **SELF STATUS** podle stránky SC: loď shora z obrysů jejích kolizních hullů (obecné pro každou loď),
      motory ze socketů `Engine_*` svítí podle tahu, podvozek ze `Gear_*` svítí, když je venku (jantarově
      při pohybu). Dole GEAR a tah v %, na zemi LANDED. Štíty ani poškození hra nemá, takže se nepředstírají;
    - malé displeje svítí do kokpitu úměrně ploše; `space.CockpitCentre 0` sloupek vypne;
    - **výkon:** první verze stála herní vlákno 6–17 ms na snímek (kokpit ~31 místo ~64 FPS). Příčina
      nalezená přes Unreal Insights: Slate dávkuje vyhlazené čáry kvadraticky, když se střídá tloušťka nebo
      vrstva (WORKFLOW 9.2g). Radar a silueta teď kreslí jednou tloušťkou v jedné vrstvě: +0,5–1 ms;
    - měření: `stat SpaceCockpit`, `stat SpaceHud`; scénář snímků `cockpit_centre`.
31b. **Displeje až pod rámeček** (19. 9. 2026, podle autorových detailů): plochy všech čtyř displejů sahají
    o ~5 mm pod vyvýšenou hranu rámečku (`grow_m` v receptu), řez AI skla zůstal na obrysu. Světlé proužky
    v rozích zmizely; zubatá levá hrana rámu pravého MFD je v AI modelu (WORKFLOW 9.6d).
32b. **Čitelnost displejů z křesla** (19. 9. 2026, autor: čísla z výchozího pohledu moc malá; zvolil všechny tři
    cesty):
    - **větší písmo, méně obsahu:** z oka ~1,3 m od desky je MFD na 1080p obrazovce ~0,4 své velikosti v návrhu.
      Rychlost 96, G 56, režim 62, všechno ostatní ≥ 26 (malé displeje ≥ 21); test to hlídá. Pryč: sloupec G (G je
      velké číslo), tlačítka na STATUS (opakovala seznam) a jeho řádek FLIGHT, sloupec elevace v seznamech,
      palivo AB na SELF STATUS; seznamy mají 3 tělesa / 4 kontakty;
    - **přiblížení na desku jako v SC:** držet **Z** nebo **prostřední tlačítko myši** – hlava se nakloní k displejům
      (15 cm, ~19° dolů), zorné pole se zúží na ~44°, aby displeje vyplnily obraz; letový HUD se mezitím schová;
      puštěním zpět. Poloha se počítá ze socketů `Display_*` (každá loď). Konzole `space.DashboardFocus 1/0`;
    - **kompozice:** oko o 20 cm blíž k desce a o 3 cm níž (194, 0, 186) a pohled o 3° dolů
      (`cockpit_view_pitch_deg`): displeje ~20 % větší, celá deska v záběru, výhled dopředu zůstal. Srovnání se
      starým okem ve scénáři `cockpit_readability` (poslední snímek); vrátit jde v `Vanguard_setup.json`.
32. **Stránky MFD** (19. 9. 2026, WORKFLOW kap. 10 bod 2, klávesy a rozsah vybral autor):
    - **F1** přepíná levý MFD, **F2** pravý, **Alt + F1 / F2** zpět (Shift by zapnul boost). Autor nejdřív
      vybral [ a ], jenže na jeho české klávesnici to nejsou samostatné klávesy (vpravo od P je „ú“), proto
      F1/F2; [ a ] zůstaly navíc pro US klávesnici. Engine měl na F1/F2 v Development buildu ladicí
      zobrazení (drátový model, unlit) – `Config/DefaultInput.ini` je odebírá. Akce `IA_MfdLeft`,
      `IA_MfdRight` přidává `Tools/Assets/add_mfd_input.py` (jen připojuje mapování do `IMC_Spaceship`);
    - jen stránky se skutečnými daty (zbraně, štíty, energii ani chlazení hra nemá, nic se nepředstírá):
      vlevo **FLIGHT → THRUSTERS → NAVIGATION**, vpravo **STATUS → CONTACTS → SELF STATUS**;
    - THRUSTERS: tah každého směru (main, retro, strafe se stranou, up, down) proti tomu, co směr právě
      zvládne (s boostem, afterburnerem a NAV), v G, a pod tím BOOST a G-SAFE. Data z nového
      `GetThrusterAcceleration` / `GetThrusterCapacity` lodi; NAVIGATION: režim, pod-režim, rychlost, limit,
      cruise a tělesa (vzdálenost k povrchu, směr od nosu, elevace); CONTACTS: kontakty radaru jako seznam
      (SHIP, EVA nebo jméno meshe); SELF STATUS: velká silueta a stav, podvozek, motory, boost, palivo AB;
    - stránka se drží v komponentě displejů, konzole `space.MfdPage <levý> <pravý>` (0–2); kreslí se jen
      zobrazená stránka (nové stránky 1,4–2,5 ms kreslení, výchozí FLIGHT/STATUS 4 ms);
    - scénář snímků `mfd_pages`.
33. **Zrychlení kreslení displejů a HUD** (19. 9. 2026, WORKFLOW 9.2g):
    - displeje se kreslí do jednoho trvalého virtuálního okna (dřív nové okno při každém kreslení → Slate
      stavěl pole vrcholů od nuly a každá dávka je kopírovala): „Display draw“ na FLIGHT/STATUS 3,3 → 1,0 ms
      za snímek (5,6 → 1,9 ms na jedno vykreslení), THRUSTERS/CONTACTS 2,3 → 1,0 ms, NAVIGATION/SELF
      1,2 → 0,6 ms, herní vlákno v kokpitu ~8,3 → ~6,2 ms;
    - čáry HUD a displejů se kreslí seskupené podle vrstvy a tloušťky (dávek čar HUD 132 → 63); vzhled
      beze změny (snímky `hud`, `cockpit`, `mfd_pages` staré proti novým);
    - přepínače pro A/B měření: `space.CockpitKeepWindow 0/1`, `space.HudLineBatch 0/1`; `stat SpaceHud`
      ukazuje „Line batches“.

33. **Loď zblízka: detailní vrstva materiálu a víc geometrie** (20. 9. 2026, autor: z chase kamery je loď
    zblízka rozmazaná; vybral obě cesty):
    - **proč to bylo měkké:** model z Meshy má jednu 4K texturu na celou 14m loď, tedy ~3 mm na pixel.
      Přepečení to nezlepší, chybějící detail v ní prostě není. Ověřeno, že to není streamováním textur
      (snímek s `r.Streaming.FullyLoadUsedTextures 1` vypadá stejně);
    - **detailní vrstva v `M_Ship_PBR`** jako vrstvené materiály v SC: dlaždicová mikro-normála (kovová
      zrnitost a řídké škrábance) a velké skvrny opotřebení pro drsnost, promítnuté **triplanárně v
      souřadnicích lodi** (neplavou, když loď letí). Textury generuje
      `Tools/Assets/generate_detail_textures.py` (numpy, bezešvé, 1024²) do
      `ArtSource/Ships/Shared/Textures`; materiál je importuje do `/Game/Ships/Shared/Textures`;
    - parametry v setupu lodi: `detail_tile_cm` (18), `detail_normal_strength` (0,8; 0 vrstvu vypne),
      `detail_grunge_tile_cm` (60), `detail_rough_variation` (0,12). Opotřebení drsnost **jen zvyšuje** –
      když ji i snižovalo, dělaly se na trupu lesklé fleky;
    - převod mezi prostory dělá HLSL uvnitř Custom uzlu (`GetPrimitiveData(Parameters).WorldToLocal`,
      `Parameters.TangentToWorld`). S uzly Transform (world→local, local→tangent) vyšla normála špatně a
      **loď byla celá černá**;
    - **geometrie:** trup má místo 200 tis. **1 milion trojúhelníků** (`decimate.hull_target_tris`),
      originál z Meshy má 3,36 mil. Nanite kreslí jen to, co je na obrazovce potřeba: ve snímcích 92 FPS
      proti 94 FPS bez vrstvy i bez geometrie. FBX trupu má 93 MB (Git LFS);
    - scénář snímků `hull_detail` (tryska, bok, vršek, celá loď) a srovnání se `detail_normal_strength` 0.

34. **Ladění vzhledu za běhu** (20. 9. 2026): `space.ShipMat <parametr> <hodnota>` a
    `space.ShipMatColor <parametr> <r> <g> <b>` mění materiály lodi v běžící zabalené hře (dynamické
    instance, nic se neukládá). Scénář `hull_tune` udělá v jednom balíčku šest variant. Důvod: každá
    varianta přes recept a balení stála ~4 minuty, teď ~20 s. Co sedí, přepíše se do setupu lodi.

35. **Hra běžela na polovičním rozlišení** (20. 9. 2026, nález při hledání „proč je to rozmazané“):
    v `GameUserSettings.ini` bylo `sg.ResolutionQuality=50`, takže engine kreslil scénu v 800 × 450 a
    škáloval ji na 1600 × 900. Týkalo se to **všeho**: hran lodi, displejů v kokpitu i HUD; žádné
    vylepšení textur se proti tomu neprosadí. Nové nastavení má **100 %** a uložený soubor se jednou
    převede (`USpaceUserSettings::MigrateSettings`, `SettingsVersion` 2). Slider „Škálování rozlišení“
    v menu zůstává, kdyby bylo potřeba ubrat. **Výkon se nezměnil** (66 → 65 FPS), protože scéna je
    omezená procesorem a GPU mělo rezervu.
    - pozor: `ScalabilityQuality.ResolutionQuality` samo nestačí, hodnotu do renderu i do ukládání dostane
      až `Scalability::SetQualityLevels`.

36. **Světlo a post scény; loď v kosmu přestala být silueta** (20. 9. 2026, po „SC úrovni grafiky
    s co nejrychlejším workflow“):
    - **Nález**: loď v kosmu vycházela jako černá silueta (průměrný jas plochy lodi 10/255, nad 60
      jen 3,9 % pixelů). Sweep směru slunce ve čtyřech krocích (`Tools/Shots/look_sun.json`,
      `space.SunDir`) ukázal, že **na směru slunce nezáleží** – chyběl **výplňový svit**: sky light
      měl intenzitu 0.35 a lak trupu byl skoro černý.
    - **Řešení** (`Tools/Shots/look_fill.json` oddělil světlo od laku): sky light **0.7**,
      `base_color_tint` trupu **3.2** (z 2.2), contact shadows slunce **0.08 m**, šířka slunce
      **0.5°**, a zdrženlivý grade v neohraničeném post process volume – kontrast 1.08, sytost 1.06,
      modro do světel (gain B 1.04), bloom 0.45, film grain 0.2, vinětace 0.35.
    - **Zahozeno po kontrole snímků**: chromatická aberace (barevné lemy po hranách desky v kokpitu),
      vyvážení bílé 6200 K (zmodralý interiér) a Lumen kvalita 2 (nic vidět, ~1 FPS).
      Interiér kokpitu zůstal na `base_color_tint` 0.6, takže kokpit je pořád tmavý jako v SC.
    - **Rychlá smyčka** (WORKFLOW kapitola 11): `space.Post`, `space.PostList`, `space.PostDump`,
      `space.Sun`, `space.SunDir`, `space.Sky`, `space.LightList` v
      `Source/gamespace/SpacePostTuning.cpp` sahají na nastavení přes reflexi, takže se nic
      neudržuje ručně a `space.PostDump` vypíše rovnou řádky pro recept. Jeden průchod ladění stojí
      ~30 s místo ~4 minut, protože se nemusí balit.
    - Hodnoty jsou v `Tools/Assets/build_space_scene.py` (`SKY_LIGHT_INTENSITY`,
      `SUN_CONTACT_SHADOW_M`, `SUN_SOURCE_ANGLE_DEG`, `POST_SETTINGS`) a v `Vanguard_setup.json`;
      `Tools/Tests/test_scene_look.py` porovnává uloženou úroveň s receptem.
    - Výkon: 80 → 88 FPS (změna vzhledu nic nestojí).

37. **Hrany trupu: změřeno a zahozeno** (20. 9. 2026): plán byl zkosit hrany a zostřit normály, aby
    hrany chytaly světlo jako na referencích. Histogram trupu v Blenderu (1,5 mil. hran) ale ukázal
    **92 % hran pod 36°** a jen 2,3 % nad 72° – model z Meshy je organický sken, ne panelová loď.
    A/B ve viewportu (ostrý úhel 60° vs. 35°, bevel 2 mm) změnilo **1 % pixelů**. Hrany mají smysl až
    u modelů s rovnými panely; teď je větší rozdíl proti SC v decalech a zónách materiálu.

38. **Trup přestal být jednolitá barva: okluze, kavity a odřený lak** (20. 9. 2026, navazuje na bod 36):
    - **Nález**: v pečených texturách lodi **není žádná okluze**. Červený kanál ORM, kde by podle
      `Docs/Ships/ShipPipeline.md` měla být, je v receptu z AI modelu **emisní maska obrazovek**
      (`build_ai_ship.py`, `surface_nodes`), na trupu rovná 1. Proto byl trup všude stejně světlý,
      bez ohledu na to, jestli je to rovný panel nebo zápich pod greeblem.
    - Jak se to našlo: první pokus (kavita z ORM.R) nezměnil **nic** – 0,7 % pixelů, tedy šum.
      Nátěr odřeného laku na červenou ukázal, proč: červená pokryla celou loď rovnoměrně, takže
      maska okluze byla všude 1. Druhý pokus (kavita z normálové mapy, `generate_cavity_map.py`)
      skončil šumem taky, protože atlas z `smart_project` má tisíce drobných ostrůvků a gradient
      přes jejich hranice nic neznamená – ten skript proto v repozitáři není.
    - **Řešení**: `Tools/Blender/bake_ship_ao.py` dopeče `T_Ship_<Loď>_AO.png` (4096², 16 vzorků,
      ~30 s) z hotových meshů přes occlusion shader s **dosahem paprsku 0,5 m** – Cycles vlastní
      AO bake je bez limitu a na uzavřeném 14m trupu dal průměr 0,27, tedy špinavou loď místo spár.
      `M_Ship_PBR` má novou vrstvu: `CavityStrength` (ztmavení laku), `AOStrength` (výstup Ambient
      Occlusion), `WearAmount` / `WearThreshold` / `WearColor` / `WearMetallic` (lak prodřený na kov
      tam, kde jsou skvrny grunge a povrch je exponovaný).
    - **Hodnoty** (`Tools/Shots/hull_zones.json`, sedm variant v jednom běhu): cavity 0.5, AO 0.6,
      wear 0.2. Nad ~0,3 vypadá odřený lak spíš jako špína než jako opotřebení. Kavita mění 7–10 %
      pixelů v detailu, na celou loď z dálky je to jemné; zblízka je v ní hloubka, která tam nebyla.
    - Bez mapy (`AOMap` je bílá) vypadá materiál přesně jako předtím, takže lodě bez dopečené okluze
      nic nerozbije. `test_ship_import.py` hlídá, že je mapa importovaná jako Masks bez sRGB, že ji
      materiál lodi opravdu má a že wear zůstal do 0,3.

39. **Nápisy na trupu: decaly** (20. 9. 2026, navazuje na bod 38): registrační číslo, výstražné pruhy,
    servisní poklop a NO STEP se promítají na trup jako deferred decaly, takže nemusí mít místo
    v UV atlasu lodi a zblízka zůstanou ostré.
    - `Tools/Assets/generate_decals.py` kreslí `ArtSource/Ships/Shared/Decals/D_*.png` (RGBA, písmo
      projektu z `Content/UI/Fonts`, jemný šum do alfy, aby hrana nebyla břitva). Registrace je
      `VNG-014 / CROSSFIELD DYNAMICS` – smyšlená loděnice, ne cizí značka; změní se jedním řetězcem.
    - Master `M_Ship_Decal`, instance `MI_Ship_<Loď>_Decal_<jméno>`, komponenty `Decal_<jméno>` pod
      Hull podle seznamu `decals` v `<Loď>_setup.json` (`import_ship.py`, `add_decal_component`).
    - **Dvě pasti, které stály většinu času** (obě jsou teď v komentáři v setupu i v testu):
      - **Decal promítá podél `-X` své komponenty**, takže rotace musí otočit X *pryč* od povrchu:
        na střeše pitch **+90**, na levém boku yaw **+90**. Obráceně se promítá do prázdna a jen se
        rozmaže přes to, co náhodou chytne pod ostrým úhlem – vypadá to jako vodorovné šmouhy, ne
        jako chybějící decal, takže je snadné hledat chybu jinde.
      - Textura se na plochu položí podle toho, jak je krabice otočená; na boku vyšlo písmo
        **zrcadlově**. Rotace zrcadlit neumí, proto má materiál `DecalFlipU` / `DecalFlipV`
        (v setupu `flip_u`, `flip_v`).
    - Místa vybral raycast do modelu v Blenderu: vnější stěna horní gondoly (`y = +-5.64 m`) je
      jediná velká rovná plocha lodi a nese registraci, vnitřní stěny gondol výstražné pruhy.
      Decal na zakřiveném nebo zvenku neviditelném místě prostě nečte – první pokus dal registraci
      mezi gondoly, kde ji nebylo vidět.
    - `test_ship_import.py` hlídá, že každý decal ze setupu má svou instanci se svou texturou a že
      loď má nápis na obou bocích.

40. **Panelové spáry na trupu** (20. 9. 2026, poslední díl „zón materiálu“):
    `Tools/Assets/generate_panel_lines.py` kreslí dlaždicový list `T_Ship_Panels.png` (RG normála
    spáry, B drážka) a `M_Ship_PBR` ho promítá **triplanárně v prostoru lodi** stejně jako mikrodetail,
    takže spáry drží velikost v centimetrech a neplavou. Do atlasu lodi je nakreslit nejde – je to
    tisíce drobných ostrůvků ze `smart_project`, čára by se lámala na každé hranici.
    - Drážka zároveň **ztmaví lak** (`panel_seam_darken`) a **zdrsní** ho (`panel_seam_rough`), protože
      na dně spáry je holý kov ve vlastním stínu.
    - Hodnoty Vanguardu (`Tools/Shots/hull_panels.json`, šest variant v jednom běhu): list **260 cm**
      (plechy zhruba půl metru), `panel_strength` **0.55**. Nad ~0,8 začnou spáry běžet i přes greebly
      a zaoblení, kde loď žádné plechování nemá, a vypadá to jako přelepka místo trupu.
    - **Spára užší než ~2 cm nepřežije mip řetězec** – první verze měla 5 px na 1024 listu (asi 9 mm)
      a v hře nebylo vidět nic, změna byla 1 % pixelů. Teď je 12 px, tedy ~2 cm při listu 180 cm.
      Druhá verze zase vyšla jako tapeta: samé průběžné řezy přes celý list. Layout proto dělí každý
      plech ještě jednou (a někdy podruhé) řezy, které zůstávají uvnitř plechu, takže dlaždice pořád
      navazuje.
    - Výkon: 86–88 FPS se spárami i bez nich (tři odběry textury navíc). `panel_strength` 0 vrstvu
      vypne; loď bez listu v repozitáři vypadá jako předtím.

41. **Spálený plech u trysek: první zóna materiálu** (20. 9. 2026): celý trup je jeden materiál, takže jediné zóny, které jdou udělat bez druhé sady UV, jsou ty, které dává tvar lodi sám.
    Nejsilnější je ocas: `M_Ship_PBR` bere polohu v prostoru lodi a od `scorch_start_cm` dozadu
    ztmavuje a zdrsňuje lak, dokud za `scorch_end_cm` není černý. Je to to, co na referencích SC
    říká, kde je motor.
    - Hodnoty Vanguardu (`Tools/Shots/hull_scorch.json`): `scorch_amount` **0.55**, od **-200 cm**
      do **-620 cm**. Začátek na -150 se plazil dopředu na prostředek trupu, nad ~0,8 vypadá celá záď
      jako stín, ne jako saze. Z předu se mění 1,5 % pixelů, tedy nic – zůstává to vzadu.
    - `scorch_amount` je ve výchozím stavu **0**: délky jsou v centimetrech a na lodi jiné velikosti
      nic neříkají, takže každá loď si je musí nastavit.

42. **Proč to bylo rozmazané: hra běžela na Medium** (20. 9. 2026, autor: „pořád si všímám
    nedokonalostí a artefaktů, které to rozostřují“):
    - **Nález**: `SetFromSingleQualityLevel(2)` nastavilo **všech osm** škálovacích skupin na Medium.
      Tam sedí engineův antialiasing (TSR), kvalita textur i post processu. Trup zblízka z toho
      vycházel rozmazaný a se schodovitými artefakty po obrysech, písmo na displejích bylo měkké.
      Je to stejná třída chyby jako těch 50 % rozlišení z bodu 35 – ne vada modelu ani materiálu.
    - **Měření** (`Tools/Shots/look_groups.json`, každá skupina zvlášť na Cinematic): jediná drahá
      skupina je **global illumination** (Lumen) – půlí snímkování (85 → 46 FPS) a v těchto scénách,
      osvětlených sluncem a sky lightem, na obrázcích nezměnila nic. Antialiasing, textury, post
      process, stíny, efekty, dohled a odrazy jsou **zadarmo**.
    - **Řešení**: výchozí předvolba je **Cinematic** s **global illumination zastropovaným na 2**
      (`USpaceUserSettings::ApplyQualityRules`, `MaxGlobalIlluminationQuality`) a uložený soubor se
      jednou převede (`SettingsVersion` 3). K tomu `r.Tonemapper.Sharpen=0.6` v `DefaultEngine.ini`:
      TSR ze své podstaty rozostřuje a tohle vrátí hranu písmu i nýtům, bez lemů.
    - **Výsledek** (Laplace na výřezu): trup zblízka **5,2 → 7,2** (+39 %), deska v kokpitu
      **19,1 → 25,1** (+31 %). Cena zhruba **10 %** snímků (kokpit 61 → 54, chase 91 → 82).
    - Menu ukazuje předvolbu, kterou hráč vybral (`GraphicsQualityLevel`), ne nejnižší skupinu –
      skupiny se s předvolbou nikdy neshodují, protože GI je zastropované a rozlišení drží na 100 %.

43. **SC-2b – VTOL a visící let** (20. 9. 2026, rozsah z roadmapy potvrzený autorem):
    **G** postaví loď na zvedací trysky místo hlavních motorů. Jen v SCM, jako přepínač VTOL
    v referenci; přechod trvá `VtolTransitionSeconds` (1,5 s), takže nic neskočí, a `GetVtolBlend`
    říká, jak daleko je.
    - Hlavní tah klesne na **35 %**, zvedací trysky ×**1,5**, boční ×**1,3**; strop rychlosti je
      **60 m/s** (omezovač uvnitř něj pořád platí) a **Space/Ctrl jsou stoupavost 15 m/s**, ne další
      cesta k maximální rychlosti.
    - **Auto-srovnání na horizont**: s klidnou pákou se trup vrací k rovině rychlostí
      `VtolLevelRate` (25°/s). Jakýkoli vstup do páky to okamžitě přebije. Je to čistá funkce
      `ComputeVtolLevelStep`, takže se dá otestovat bez planety – a taky se hned ukázalo, že první
      verze točila loď na opačnou stranu.
    - **Odmítne afterburner** a **shodí cruise**; přechod do NAV VTOL vypne.
    - HUD i MFD mají odznak **VTOL** vedle CPLD, GSAF, CSTB, BOOST a PREC (v referenci je VTOL
      jeden ze čtyř souběžných přepínačů), a druhý řádek pod režimem ukazuje `VTOL`.
    - **Visení už je vidět na motorech** (známý problém z kapitoly 11, 17. 9. 2026): `EngineDemand`
      měřil svislou osu proti **plné kapacitě** zvedacích trysek, takže visení na Veyře (0,46 G
      z možných 5,5) dávalo zátěž 0,06 a trysky i zvuk zůstaly na nule. Teď se svislá osa měří proti
      **jednomu G tahu** (`HoverThrustReferenceG`), takže visení čte jako práce, kterou to je.
    - Klávesa: `Tools/Assets/add_vtol_input.py` (IA_Vtol na G); bez něj si ji loď namapuje za běhu.
      Konzole: `space.Vtol 1|0`. Testy: `Tools/Tests/test_vtol_sc2b.py`, snímky: `Tools/Shots/vtol.json`.

44. **SC-3 – značka dráhy letu** (20. 9. 2026): na HUD přibyla značka toho, **kam loď doopravdy letí**,
    ne kam míří nos. V SC se podle ní lítá – v decoupled se nos a dráha letu rozejdou úplně.
    - Kroužek se třemi vousy (letecký flight path marker) na místě, kam rychlost dopadá na obrazovku.
      Počítá se z ohniskové délky pohledu v `USpaceFlightHud::ApplyView`, v jednotkách 1080p plátna HUD.
    - **Za nosem** (couvání, let bokem přes 90°) průmět neexistuje: značka zezlátne, vykreslí se
      čárkovaně a přilepí se na kruh **na opačnou stranu**, což je směr, kam se otočit. Přesně vzadu
      zaparkuje dole, aby neposkakovala dokola.
    - Pod 5 m/s se nekreslí: pod tím je směr šum a značka by poskakovala kolem středu.
    - Nikdy neopustí kruh o poloměru 330 jednotek kolem středu.
    - `Tools/Tests/test_flight_hud_sc3.py` měří průmět proti geometrii, kterou tvrdí, že dělá – značka
      s přehozeným znaménkem je horší než žádná.
    - K tomu dvě věci do nástrojů: pole `drift` ve scénáři snímků (rychlost v osách lodi, m/s – `speed_ms`
      umí jen rovně vpřed) a konzolový `space.Drift <vpřed> <vpravo> <nahoru>` pro hraní.

45. **Rychlostní čáry** (21. 9. 2026, autor: protýpová laciná verze proti snímku ze Star Citizen):
    prach byl pole **stejně dlouhých, stejně jasných bílých klacíků** s ostře uříznutými konci.
    - `M_SpaceDust` teď každou čáru **zužuje do ztracena** podél i napříč, takže z kvádru je měkké
      vřeteno. Každá částice má navíc **vlastní délku a jas** (`LengthSpread`, `BrightnessSpread`,
      jas třetí mocninou, takže je většina slabých a pár výrazných).
    - **Past**: `LocalPosition` u instancovaného meshe nevrací prostor instance, ale primitiva, takže
      taper vyšel všude záporně a prach **úplně zmizel**. Tvar se počítá z `ObjectPositionWS` (ta u
      instancí funguje) a komponenta posílá směr letu a poloviční rozměry do dynamické instance
      materiálu; délka konkrétní částice je v custom data 2.
    - Zužování sebere zhruba tři čtvrtiny světla, proto `DUST_BRIGHTNESS` 1.6 → 5.0.
    - Hustota 400 → **2600** částic v krabici 30 m: pole bylo příliš řídké, než aby v pohybu četlo
      jako prach. **Nestojí to nic měřitelného** (80 FPS s 900 i s 3500, `Tools/Shots/dust_tune.json`).
    - Ladí se za běhu: `space.Dust <Vlastnost> <hodnota>`, `space.DustList`. Změna počtu se projeví
      hned (pole se přestaví).
46. **Rychlostní tunel v cruise** (21. 9. 2026, autor: bílé čáry samy nestačí, dva snímky quantum
    travel ze Star Citizen): nová komponenta `USpaceSpeedTunnelComponent` na lodi.
    - **Proč nestačí prach:** jeho smítka stojí ve světě. V cruise loď přeletí celou 30m krabici za
      snímek, každé smítko skočí jinam a čáry se rozpadnou na blikání. Nad ~600 m/s proto vzhled
      přebírá tunel a prach mezi 600 a 1500 m/s mizí (`FadeOutStartSpeed`, `FadeOutEndSpeed`).
    - **Jak funguje:** tři otevřené válce kolem kamery (25, 60 a 150 m), osa ve směru letu. Uvnitř
      válce se stěna perspektivou sbíhá do úběžníku, takže čáry vycházejí z bodu, kam loď letí,
      bez triků v obrazovém prostoru, a loď zůstává před nimi. `M_SpeedTunnel` (HLSL v Custom node)
      kreslí na stěnu **čáry** (dráhy kolem osy, v každé jedna čára na periodu, většina slabých,
      pár jasných, některé do modra), **měkké světelné pruhy** sbíhající se do úběžníku a **záři**
      na úběžníku (vzdálené víko válce).
    - Čáry se posouvají o dráhu, kterou počítá komponenta, ne o čas materiálu: zdánlivá rychlost
      sleduje skutečnou, ale nepřekročí `MaxApparentSpeed` (2 km/s). Čára, která za snímek skočí
      dál, než je sama dlouhá, bliká místo toho, aby tekla; test hlídá aspoň dvojnásobek.
    - **Šířka čar v cm, škálovaná vzdáleností stěny.** Podíl dráhy dělal z blízké stěny tlusté
      pruhy, jedna šířka pro všechny stěny zase nechala vzdálené zmizet.
    - **Pruhy pokračují přes víko.** V první verzi končily kousek před úběžníkem a kolem záře zůstal
      tmavý kotouč; bez ditheru navíc měkké přechody dělaly schody.
    - **Dvě chyby prachu, které tunel odhalil:** (a) pawn prach v cruise zesiloval 2,5× (z doby, kdy byl
      jediným efektem) – pryč; (b) prach se stavěl kolem polohy kamery z **minulého snímku** (camera
      manager se aktualizuje až po pawnu). Při 1,2 km/s je to 20 m, ochrana „nic u objektivu“ měřila
      od špatného místa a smítko projelo kamerou jako bílý klín přes půl obrazu. Poloha se teď
      posune o pohyb lodi za snímek a blízkost se měří k nejbližšímu bodu čáry, ne k jejímu středu.
    - Hodnoty (`Tools/Shots/tunnel_tune.json`, tři kola): `StreakBrightness` 10, `StreakWidthCm` 7,
      `BeamBrightness` 2, `BeamCount` 24, `BeamSharpness` 6, `GlowBrightness` 2, modré pruhy
      (tyrkysová varianta ze druhého SC snímku je v tune sadě). Plně od 2,5 km/s.
    - Ladí se za běhu: `space.Tunnel <Vlastnost> <hodnota>`, `space.TunnelList`; stěny přes
      `space.Tunnel Layers ((RadiusCm=2500,Brightness=1,Lanes=50,BeamWeight=0),...)`.
    - Snímky umí cruise: pole `"cruise": true` (`ASpaceshipPawn::DebugEngageCruise`, rychlost =
      limit × `limiter`). Výsledek: `-Preset speed_tunnel` (SCM → NAV → cruise 1,2 a 6 km/s).
    - Výkon: 82–87 FPS s tunelem, stejně jako bez něj.
    - *Tentýž den nahrazeno bodem 47:* tunel teď patří quantum skoku, cruise zmizel.
47. **SC-4 – quantum drive místo cruise** (21. 9. 2026, podle referenčního videa, poznámky
    v `starcitizenreference/QuantumTravel_VideoNotes.md`; autor: cruise ve SC není, rychlostních čar
    je mimo quantum šíleně moc). Cruise (J) je pryč celý: stav, klávesa, `IA_CruiseDrive`, výškový limit.
    - **Průběh jako ve videu:** v NAV je cílem těleso nejblíž nosu (do `QuantumPickDeg` 35°). Drive
      se sám **spooluje** (`QuantumSpoolSeconds` 6 s) a **kalibruje**, dokud je nos do 6° od cíle
      (`QuantumCalibrationSeconds` 2,5 s, mimo cíl rychle padá). Pak **READY** a **podržené levé
      tlačítko myši** (0,6 s) skočí. Ve skoku **nejde řídit**, nos se drží na cíli. Loď dorazí
      `max(0,6 poloměru, 15 km)` nad povrch v rychlosti NAV (300 m/s) a drive **chladne 10 s**.
      B zpět do SCM skok přeruší tam, kde loď je.
    - **Blokace:** `TOO CLOSE` (skok kratší než 20 km – z výchozího bodu je Veyra moc blízko),
      `OBSTRUCTED` (těleso v cestě, počítá se úsečka na místo příletu proti koulím těles), `NO QT FUEL`
      (12 % nádrže na 1000 km, doplňování zatím není).
    - **Rychlost ve skoku:** zrychlení 8 km/s², strop 30 km/s, brzdění tak, aby dorazil přesně
      rychlostí výstupu. Na Orun (380 km od startu) to je asi 17 s, 600 km zhruba 24 s. Měřítko
      systému je naše (desítky až stovky km), ne gigametry SC; doba skoku je ale podobná.
    - **HUD podle 4K výřezů z videa:** zelený rámeček nahoře (`SPOOLING 37%`, `CALIBRATING`, `READY`,
      `COOLING 44%`, oranžově důvod blokace), dva oblouky kolem středu (fialové → zelené se šipkami
      `> <` → červené při chlazení), značka cíle (kroužek, jméno, vzdálenost `394.5km`), a když je
      cíl mimo obraz, šipka kam zatočit. Displeje mají řádek QUANTUM (OFF/SPOOL/CALIB/READY/JUMP/COOL).
    - **Tunel jen ve skoku** (řídí ho `GetQuantumBlend`, ne rychlost). Podle videa: **mlha** zakrývá
      vesmír (nový `M_QuantumFog`, průsvitný válec za stěnami s čarami – aditivní světlo oblohu
      jen zesvětlí, nikdy ji nezakryje), světlejší u stěn a tmavá ke středu; **řídké** tenké čáry
      (`Fill` 0,2); záře na úběžníku; **zelené záblesky** z úběžníku na začátku skoku a pak náhodně
      každých 8–18 s. **Past:** záporná `TranslucentSortPriority` na mlze ji řadí před *všechny*
      průsvitné věci a prstence Orunu jí prosvítaly celé; mlha má 0, stěny s čarami 10.
    - **Prach** v normálním letu jen jako náznak: 700 smítek místo 2600, jas 2,5 místo 5; ve skoku
      žádný. Jeho poloha se počítá z kamery posunuté o pohyb za snímek (bod 46).
    - Ladění za běhu: `space.Quantum <jméno> [0..1]` (skok hned, bez spoolu), `space.Quantum ready`,
      `space.Tunnel FogOpacity 0.97` a ostatní vlastnosti tunelu. Snímky: pole `"quantum": "Orun"`,
      `"quantum_progress"`, `"quantum_ready"` a `"facing": "body:Orun"`.
    - Vstup: `Tools/Assets/add_quantum_input.py` (IA_QuantumEngage na levé tlačítko, IA_CruiseDrive
      odmapovaná a smazaná). Test `Tools/Tests/test_quantum_sc4.py`, snímky `-Preset quantum`.
    - Chybí proti SC: mapa systému (F2) a výběr cíle z ní, modrá záře pod přídí z kokpitu,
      doplňování paliva, interdikce (jiskry z trupu: bod 48).

---
48. **Quantum podruhé: jiskry u lodi, tunel místo mlhy, kamera** (21. 9. 2026, autor po prvním testu:
    mechanismus solidní, mlha všude a moc hustá, chyba při free looku, chce modré jiskry kolem lodi
    jako ve videu a méně bílých čar, a ty u lodi).
    - **Chyba při free looku:** loď ve skoku ujela ze záběru (a na jejím místě zůstal tmavý „duch“).
      Příčina: zpoždění kamery (spring arm lag). Omezené na 15 m, ale ty metry jdou podél dráhy letu
      a při pohledu z boku vystrčí loď z obrazu. Ve skoku je zpoždění **vypnuté**. **Past:**
      `CameraLagMaxDistance = 0` neznamená žádné zpoždění, ale **žádný strop** – kamera zůstala
      kilometry vzadu. Duch lodi: průsvitná mlha se nehýbe se světem, TSR neměl čím odmítnout starý
      pixel; mlha i tunel mají teď `enable_responsive_aa` a mlha `output_translucent_velocity`.
    - **Tunel místo mlhy:** mlha je hustá (0,9), ale **tmavá uprostřed** a u stěn světlá ve 13 měkkých
      pruzích kolem osy (`FogCentreOpacity`, `FogNearColor`, `FogFarColor`). Řídká mlha všude četla jako
      zamlžení a cíl pak prosvítal celý; tmavá díra se světlými stěnami je to, co je ve videu.
    - **Modré jiskry kolem lodi** (`USpaceHullSparksComponent`, materiál prachu s vlastní barvou):
      420 krátkých jisker se rodí na povrchu lodi (60 % na přední polovině – příď „rozráží“), žijí
      0,2–0,55 s a proudí dozadu podél trupu a trochu od něj. Body: z kolize trupu, když ji trasování
      najde, jinak obal 85 % hranic lodi (tak to je teď – kolize trupu se trasovat nedá, ale obal kolem
      Vanguardu stačí, jiskry obtékají motory i příď). Z kokpitu jsou jiskry blíž než 5–12 m skryté,
      jinak šly přes sklo jako tlusté pruhy.
    - **Bílé čáry v normálním letu:** tatáž komponenta, 60 bílých slabých jisker u lodi od 30 m/s
      (plně od 200 m/s); prach kolem kamery jen 250 smítek s jasem 1,8. Tloušťka 5 cm: 2 cm byly
      z chase kamery (25–35 m) pod pixelem.
    - Snímky `-Preset quantum_look` (skok zezadu, z boku, zepředu, free look, kokpit; SCM a NAV).

---
49. **Planety 1/4: atmosféra Veyry** (21. 9. 2026, podle referenčního videa průletu planetami,
    poznámky `starcitizenreference/Planets_VideoNotes.md`, snímky `ArtSource/Reference/Video/sc_pyro_planets/`).
    Dřív byla obloha jen malovaný přechod v materiálu hvězd a Unreal atmosféru skript mazal.
    - **SkyAtmosphere velikosti Veyry** (`Atmosphere_Veyra`, střed v planetě). Koeficienty Země
      přepočtené na planetu 25 km: Rayleigh 0,09 s výškou hustoty 1,5 km (3 km dělalo halo tlusté
      jako desetina planety, 0,16 barvilo poušť do fialova), prach (Mie) 0,07 teplé barvy s výškou
      0,6 km, letecká perspektiva ×16 (obzor je tu kilometry daleko, ne sto). Hodnoty `ATMO_*`
      v `build_space_scene.py`.
    - **Obloha hvězd má uzel atmosféry** (`SkyAtmosphereViewLuminance`): světlo atmosféry přes
      hvězdy a hvězdy za světlou atmosférou mizí – lem z vesmíru, denní obloha ze země.
    - **Past 1 – černý pruh na obzoru:** atmosféra má vlastní „zem“ ve výšce hladiny, náš terén je
      místy o 1,6 km výš a paprsky těsně nad skutečným obzorem narážely na tmavou virtuální zem.
      Zem atmosféry je 2 km pod hladinou (`ATMO_GROUND_BELOW_SEA_KM`).
    - **Past 2 – černá loď na zemi:** sky light zachytává oblohu do cubemapy a uzel atmosféry v tom
      záchytu nedává nic. Loď pak neměla výplň ani při 5× sky lightu. Malovaný přechod je proto
      zpátky na 40 % (`PAINTED_SKY_AMOUNT`) v prachových barvách planety – dává výplň a zároveň
      zesvětlí oblohu k zaprášeným pouštním oblohám z videa.
    - Slunce svítí do atmosféry (`atmosphere_sun_light`).
    - Rychlé ladění bez balení: `space.Atmo <vlastnost> <hodnota>` (SkyAtmosphere) a
      `space.SkyParam <parametr> <hodnota>` (materiál oblohy). Etapy: `Tools/Shots/atmo_tune*.json`.
    - Zbývá z videa: kulatá silueta (dnes „brambora“ z dálky), materiál povrchu ve třech měřítkách,
      kameny, mraky. Orun a Keth zatím atmosféru nemají (jedna SkyAtmosphere na level).

---
50. **Planety 2/4: kulaté siluety, Veyra 120 km** (21. 9. 2026, autor zvolil zvětšení planety).
    - **Veyra** měla na poloměr 25 km reliéf ±1,6 km (6 % poloměru) a z vesmíru byla „brambora“.
      Teď má **poloměr 120 km** (reliéf 1,3 %), střed 140 km před startem, takže start je pořád
      20 km nad hladinou. Terén, gravitace a atmosféra zůstaly; dlaždic terénu je skoro stejně (780
      místo 750 u země), protože LOD se řídí vzdáleností, ne velikostí planety.
    - **Keth** obíhá na 420 km (60 min) místo 150 km – jinak by byl skoro na povrchu a uvnitř
      skořepiny příletu quantum skoku (72 km).
    - **Orun a Keth hranatí kvůli Nanite:** koule s 256 segmenty zvětšená na 6–150 km měla s Nanite
      viditelné rovné hrany. Na `SM_PlanetSphere` je Nanite vypnuté (`ensure_sphere_not_nanite`).
    - **Pryč zástupné asteroidy** (16 šedých krychlí kolem startu z prvního prototypu): s velkou
      Veyrou visely uprostřed výhledu z orbity jako černé kostky.
    - Snímek `planet_300km` v `-Preset space_look` (celá planeta s lemem, Orun, Keth).

---
51. **Planety 3/4: povrch ve třech měřítkách** (21. 9. 2026, podle videa). `M_Planet_Terrain` měl
    jeden šum mezi dvěma barvami a polární čepičky. Teď je celá barva v `Tools/Assets/terrain.hlsl`
    (Custom uzel, konstanty `TERRAIN_*` v `build_space_scene.py`):
    - **Oblasti z orbity:** zdeformovaný nízkofrekvenční šum na jednotkové kouli dělí planetu na
      planiny, okrové vysočiny, červenohnědé pánve a tmavou skálu, s členitými, ale čitelnými okraji.
    - **Střední měřítko:** holá skála na svazích (sklon 18–32°, `TERRAIN_SLOPE_ROCK`), prach v údolích,
      bledší nejvyšší vrcholy; drsnost skály 0,78, prachu 0,95.
    - **Zblízka:** rozbití barvy na ~40 m, ~3 m a ~0,6 m a tmavší kamínky na rovinách.
    - **Atmosféra do teplé:** terén vycházel fialovošedý – modrý Rayleigh přes leteckou perspektivu
      a modrý malovaný zenit přes sky light. Rayleigh 0,035, prach 0,12, perspektiva ×10, zenit šedý.
      Varianty v `Tools/Shots/terrain_atmo.json`.
    - Snímky `-Preset terrain_look` (300 km → přistání). `Tools/Shots/sheet.py` skládá složku snímků
      do jednoho přehledu.
    - **Známé:** zblízka je zem pořád hladká (kameny jsou krok 4); u země se objevuje hláška VSM
      „Non-Nanite Marking Job Queue overflow“ (dlaždice terénu nejsou Nanite) – zatím bez vlivu na FPS
      ve snímcích (60–80), sledovat; na snímku z 15 km šikmo je jedna podezřele rovná hrana stínu.

---
52. **Planety 4/4: fotoskenovaná zem a kameny** (22. 9. 2026, autor: zblízka „low grafika, rozmazané“).
    - **Příčina rozmazání:** povrch byl jen barva ze šumu, bez textur a bez normal mapy – světlo nemělo
      na čem ukázat zrno, kamínky a praskliny. Teď tři fotoskenované materiály z Poly Haven (CC0,
      `Tools/Assets/fetch_polyhaven.py` → `ArtSource/Textures/PolyHaven/`): štěrkový písek na rovinách
      (repeat 2,5 m), rozpraskaná skála na svazích (4 m), vrstvená skála na útesech (6 m). Promítnuté
      triplanárně v prostoru planety, normála ve world space (`tangent_space_normal` off), barvu dál
      určují oblasti a sklon – textura se dělí svým průměrem (`means.json`), takže přidává detail,
      ne barvu. Drsnost aspoň 0,8 (skeny se na hřebenech leskly jako mokré).
    - **Přesnost textur 120 km od středu:** střed dlaždice ve floatu je o centimetr vedle, to je u 2,5 m
      textury několik texelů a švy mezi dlaždicemi. Planeta posílá střed dlaždice modulo
      `TerrainTextureWrapCm` (60 m) v double (custom data 8–10); každé měřítko textury ho musí dělit.
    - **Past:** `.Sample()` v Custom uzlu shodí celý materiál na výchozí šedý – ray tracing hit shadery
      nemají derivace. `Texture2DSample()` projde. Chyba je vidět jen v cook logu („Failed to compile Material“).
    - **Kameny** (`UPlanetRockScatter` na planetě, 4 fotoskenované modely z Poly Haven, Nanite): buňky
      ~46 m na mřížce stěn krychle, obsah buňky z hashe (pořád stejné kameny na stejném místě), stojí na
      přesném výškovém poli, zapuštěné o čtvrtinu výšky, víc na svazích, některé buňky skoro prázdné.
      Okruh 700 m, nad 2,5 km nic; kolem 10 000 instancí. **Zatím bez kolize** – loď kameny proletí.
      Pozor: `rock_09` je sken velký 14 cm (Poly Haven udává rozměry v mm).
    - **Stíny:** dlaždice terénu větší než 2 km stíny nevrhají (VSM hlásil přetečení fronty non-Nanite
      meshů). Změřeno u země: 62 FPS s VSM, 51 bez – hláška nic nestojí, jen se skrývá
      (`r.Shadow.Virtual.AllowScreenOverflowMessages=0`).
    - **Hřebenový terén vypnutý:** `RidgedOctaves` (ostré hřebeny, klidná údolí) vypadal z 300 m–2 km
      mnohem líp, ale kamera po přistání končila pod vykreslenou zemí a u okraje planety byly díry.
      Kód zůstal, `RidgedOctaves = 0`, příčina se musí najít, než se zapne (kap. 11).
    - `Package.ps1` teď sám ukončí zaseknutou hru a při „Failed reading oplog from Zen“ restartuje Zen
      a balí znovu.
    - Test `Tools/Tests/test_planet_rocks.py`, snímky `-Preset rocks_look`, přehled `Tools/Shots/sheet.py`.

---
53. **Quantum tunel podle autorova testu** (22. 9. 2026, autor po SC-4: planeta prosvítá tunelem
    jako duch, tunel je plochý paprskovitý vzor, v referenci je to uzavřený tmavý prostor s modrými
    jiskrami těsně u lodi).
    - **Prosvítání:** mlha (`M_QuantumFog`) krývala jen 60–90 %, takže jasný Orun, hvězdy i mlhovina
      prosvítaly. Teď krývá 100 % (`FogOpacity` 1, `FogCentreOpacity` 1) a vzhled dělají jen barvy:
      tmavě modrá u stěn v širokých radiálních paprscích (`FogShaftCount`, `FogShaftContrast`), černá
      díra v úběžníku, žádná záře uprostřed (`GlowBrightness` 0).
    - **Past – černé čáry:** jakmile byla mlha plně krycí, občas se vykreslila až po jiskrách (stejná
      priorita řazení průhledných věcí, řadí se podle vzdálenosti a střed mlhy je v kameře) a jiskry
      přemazala na černé kostičkované čáry. Jiskry a prach mají `TranslucentSortPriority` 20, stěny
      tunelu 10, mlha 0. (Po změně počtu jisker přes konzoli se čáry mohou ještě krátce objevit.)
    - **Čáry:** jen 8 % drah (`Fill` 0,08), bílé (`StreakColorSpread` 0), jasnější.
    - **Jiskry u lodi:** 300 tenkých modrých, život do 0,35 s, tok 35 m/s, rozptyl 0,08 – drží se
      trupu na délku lodi. Hustší a delší varianty dělaly mrak daleko za lodí.
    - **Loď je silueta:** slunce se ve skoku stáhne na pětinu (`QuantumSunScale`), u přídě svítí modré
      světlo (`QuantumGlow`, 60 cd) – to je modrá záře na spodku přídě.
    - Nové konzolové ladění `space.Sparks`; varianty `Tools/Shots/tunnel_variants.json`, výsledek bez
      ladění `-Preset quantum_final`.
    - Z kokpitu je modrá záře pod přídí pořád slabší než v referenci (jiskry blízko oka jsou skryté,
      bližší dávaly přes sklo tlusté pruhy) – k posouzení autorem.

---
54. **Další opravy z autorova testu SC-1c/SC-4** (22. 9. 2026, `Docs/TestScenario_SC1c_SC4.md`).
    - **Náběh skoku:** zrychlení skoku roste během `QuantumRampSeconds` (2,5 s) místo plných 8 km/s²
      od začátku; brzdění u cíle je beze změny, takže dojezd je pořád přesný. Tunel, zorné pole
      a zvuk skoku se řídí rychlostí (plné od čtvrtiny maxima), ne časem – přijdou spolu s rychlostí.
      Po 0,3 s 356 m/s, po 1 s 1,4 km/s, po 3 s 14 km/s (`-Preset playtest_fixes`). Skok na 600 km
      trvá 23,6 s místo 22. Menší škubnutí kamery na startu.
    - **HUD v NAV:** v SC se v NAV bojový blok HUD (zbraně, munice) vymění za H2/QT FUEL (referenční
      video). Zbraně nemáme, ale ukazatel afterburneru (v NAV nepoužitelný) se v NAV mění na **QT FUEL**
      – tím je quantum palivo konečně na HUD. Displeje v kokpitu mají dál svůj AB sloupec.
    - **HUD v kokpitu a zvenku stejný – záměr:** SC promítá HUD na hledí a ve třetí osobě ukazuje
      totéž; podrobnosti nesou displeje v kokpitu (stránky MFD, radar, stav lodi).
    - **Kokpit:** výchozí pohled rovně (`cockpit_view_pitch_deg` 0 místo -3), oko beze změny – asi
      o třetinu víc výhledu ven, displeje celé. Vyšší oko nebo náklon nahoru displeje ořezávaly
      (`Tools/Shots/cockpit_view_tune.json`).
    - Nesoulady scénáře se hrou (pro další testy): spool běží sám po B a namíření, levé tlačítko se
      drží až při READY; TOO CLOSE = cíl blíž než 20 km, překážka v cestě je OBSTRUCTED; asteroidy
      ve scéně nejsou (radar v 5 km nemá co ukázat).

---
55. **Tunel bez prosvítání a jiskry místo čar** (22. 9. 2026, autor ke snímkům ze skoku: „dějou se tam
    tyhle artefakty, plus ty modré čáry působí blbě, jsou to jen čáry – má to podle reference
    vypadat jinak, spíš jako jiskry“).
    - **Artefakty = Orun a jeho prstence skrz tunel.** Mlha tunelu byla průhledná (`BLEND_TRANSLUCENT`),
      a průhledný materiál svět pod sebou vždycky jen dobarvuje – zakrýt ho neumí, ať má krytí
      jakékoliv. Mlha je teď **maskovaná** (neprůhledná, s děrami): kde má být řidší, tam se pixely
      vyřezávají podle modrého šumu (`ScalarBlueNoise`, práh 0,5) – z dálky to vypadá jako závoj,
      ale skutečně zakrývá. `DitherTemporalAA` v Pythonu není.
    - **Jiskry podle reference** (`sc_quantum_travel_tutorial` 0:20–0:45): v SC nejsou rovné čáry, ale
      tenké modré „vlásky“ v trsech z několika míst na trupu, rozevřou se do vějíře a strhne je to
      dozadu. `USpaceHullSparksComponent` je přepsaný: 7 emitorů na trupu, každý se po 0,4–1,3 s
      přesune jinam; jiskra vyletí v kuželu kolem normály (1800 cm/s) a stálé zrychlení dozadu
      (14 000 cm/s²) jí dráhu zakřiví; kreslí se jako řetěz 5 krátkých úseků po poslední 0,09 s dráhy,
      slábnoucí do ohonu. 260 jisker = 1300 instancí, snímek to nestojí nic (85–90 FPS).
    - **Tři pasti, kvůli kterým jiskry nešly vidět vůbec** (materiál se přitom kompiloval bez chyby):
      1. Tvar se měřil jako 3D vzdálenost od osy kvádru – jenže pixel na povrchu kvádru je od osy
         vždycky aspoň půl šířky daleko, takže jas vycházel všude nula. Teď se měří v souřadnicích
         instance (`LocalPosition`, origin `INSTANCE`) a napříč se bere **menší** ze dvou os.
      2. Vstupy Custom uzlu jsou `float`. Odečítat v něm dvě světové pozice u planety vzdálené
         100 000 km znamená chybu v řádu decimetrů – u 2cm jiskry konec. Rozdíly se počítají uzly
         mimo Custom (LWC), nebo se world space nepoužije vůbec (tady to druhé).
      3. Jiskra užší než pixel se v TSR rozpadne na tečkovanou čáru. Materiál je proto
         `enable_responsive_aa` a šířka jiskry roste se vzdáleností (`MinScreenThickness` 0,005 ≈ 4 px).
    - **Body na trupu:** raycast do kolize lodi nic netrefil (konvexní tvary UCX, a testy běží bez
      fyziky), jiskry tak létaly z krabice kolem lodi, ve vzduchu. Teď se čtou přímo z tvarů kolize
      (`UBodySetup::GetClosestPointAndNormal`, `bUseConvexShapes`) – 674 bodů na trupu.
    - Snímky `-Preset sparks_look` (bok, zespoda zepředu, zezadu, kokpit) a `-Preset quantum_final`.
      Z kokpitu jiskry skoro vidět nejsou – stejně jako v referenci.

---
56. **Skok podle reference, kolo 2** (22. 9. 2026, autor vypsal pět konkrétních rozdílů proti SC snímkům).
    - **Prosvítající cíl byl chyba vykreslování, ne barvy.** Mlha tunelu se při náběhu prolínala
      tečkovanou maskou, a těmi dírami byla vidět celá planeta. Teď mlha zakryje svět hned, jak skok
      začne (`cover` = 0/1), a *rozsvěcí se barvou*. Cíl je místo toho **maják**: malá zářící koule
      (`M_QuantumBeacon`, `BeaconSizeDeg` 1,4°) v úběžníku, která taky **svítí na loď** zepředu
      (bodové světlo 220 000 cd) – z toho je ta silueta jako v referenci.
    - **Pozadí bylo modré kvůli expozici, ne kvůli materiálu.** V tmavém tunelu se automatická
      expozice vytáhla a z téměř černé udělala sytě modrou. Při skoku je teď expozice připíchnutá
      (`QuantumExposure` 1,6, bias -0,8) a všechno svítící se tomu přizpůsobilo: čáry 160, maják 260,
      jiskry 70, záře motorů se v skoku škrtí na 35 % (`QuantumThrusterScale`), jinak z nich byly
      čtyři reflektory.
    - **Jiskry místo výbuchu proudí.** `USpaceHullSparksComponent` už nemá emitory-body: jiskra se
      rodí kdekoliv na trupu, unáší ji tok dozadu podél lodi (`FlowSpeed` 2600 cm/s), pomalu se
      zvedá od povrchu (`LiftSpeed`) a vlní se na dvou turbulentních vlnách, které se s věkem
      rozšiřují (`TurbulenceCm`, `TurbulenceRate`). Stopa se kreslí po úsecích a nikdy není delší
      než `MaxTrailCm`, jinak z ní při zrychlování byly kolejnice přes celou obrazovku.
    - **Barevná variace:** stěny mají široké barevné pásy (`FogBandColor`, tři pomalu plující),
      oblaka mění jas, a mezi bílými čarami jsou řídce zelené a zlaté (v `TUNNEL_HLSL`).
    - **Kamera už neteleportuje loď do středu:** zpoždění kamery se při skoku nevypíná, ale
      navíjí (`BaseCameraLagSpeed` → `QuantumCameraLagSpeed`), takže loď do středu plynule dojede.
    - **Past:** Custom uzel s `LocalPosition` se v zabalené hře nezkompiloval a maják se kreslil
      výchozím šedým materiálem – v editoru i v cook logu bez chyby. Materiál majáku je proto bez
      Custom uzlu (jen emisivní barva × jas). Platí to samé pravidlo jako u `Texture2DSample`:
      **co jde postavit uzly, nedávej do Custom uzlu.**
    - **Kolo 3 po dalším autorově snímku:** černé „škrábance“ kolem lodi byl `enable_responsive_aa`
      na jiskrách – jakmile se stěny rozsvítily, TSR tam neměl co vzít a kreslil tmu; vypnuto.
      Jiskry se teď kreslí jako **plošky natočené ke kameře** (`Plane` místo `Cube`), takže rychlé
      stopy nesekají; tok jde podél povrchu trupu (tangenciálně, nikdy dopředu), takže obtéká loď.
      Mlha je **koule kolem kamery** a její barva závisí jen na směru pohledu – válec dělal přes
      obraz ostrou rovnou hranu (vlastní silueta). Jedna strana tunelu je světlejší podle toho, kde
      stojí slunce (`FogSunAmount`).
    - **Kolo 4 (doladění):** mraky na stěnách jsou dvě vrstvy šumu běžící různě rychle (`FogCloudSpeed`),
      takže se převalují místo rovnoměrného klouzání; jejich součet se váží, ne sčítá – sečtený se
      ořezával na 1 a dělal ploché obdélníky. Jiskry mají teplotu: u trupu bílé, v úplavu tmavě modré
      (custom data 2, `HotColor` a `HeatFalloff`; hlava mladé jiskry je nejteplejší).
    - **Loď je v tunelu silueta, ne bílý plast** (autor, 22. 9. 2026). Vinu nesly dvě věci, ne expozice:
      bodové světlo u majáku svítilo 220 000 cd ze 60 m (teď 35 000, dělá jen obrys) a bílá část
      jisker obalovala trup (`HotColor` ztlumená, `HeatFalloff` 4 – jiskra chladne dřív). Ambientní
      světlo scény se teď v skoku škrtí jako slunce (`QuantumSkyScale` 0,15, slunce 0,45); v tunelu
      stejně není od čeho se odrazit. Ověřeno vypínáním zdrojů po jednom (`Tools/Shots/ship_dark.json`).
    - Nové ladění: `space.Ship <Property> <Value>` (vlastnosti lodi za běhu).
      Snímky `-Preset quantum_look`, `-Preset quantum_ramp`, `-Preset sparks_flow`, `-Preset tunnel_haze`.

---
57. **Plastový vzhled trupu: změřeno a opraveno** (22. 9. 2026, krok 2 a 3 domluveného postupu).
    - **Co to nebylo** (měřeno na zabalené hře, `Tools/Shots/plastic_diag.json`; jas trupu, rozptyl a
      99. percentil ze snímků): traced odrazy (`r.Lumen.Reflections.MaxRoughnessToTrace` 0,4 → 1,0)
      **žádná měřitelná změna**; lokální expozice vypnutá (kontrast 0,8 → 1,0) kontrast **snížila**
      (std 0,170 → 0,141), takže 0,8 pomáhá; sky light 0,7 → 0,3 posunul jas o 0,006 – výplň to neplácá.
    - **Past v měření:** konzolové příkazy platí do konce běhu, takže druhý snímek „zdědí“ nastavení
      prvního. Každá varianta teď začíná návratem na výchozí hodnoty a první snímek je zahřívací
      (loď se do něj ještě nestihne natočit).
    - **Co to bylo:** materiál. `metallic_scale` 0,5 → **2,0**, `roughness_scale` → **0,75**,
      `detail_normal_strength` 0,8 → **1,2** (`Vanguard_setup.json`, varianty v `Tools/Shots/plastic_mat.json`).
      Šedá barva se změní na lakovaný kov: světla (p99) 0,749 → 0,871, rozptyl 0,174 → 0,196.
      ×2,5 / 0,6 vypadalo nad planetou mokře. **Interiér kokpitu hodnoty nedědí** – v setupu je nemá
      a musí zůstat na hodnotách masteru.
    - Kontrolní snímky bez ladění: `-Preset hull_now` (vesmír, nad planetou, kokpit).
58. **Nákladový prostor Steadfastu ve hře** (23. 9. 2026, autor: „dej to do hry ať to vidíme“).
    - Prostor postavený z CC0 kitu Quaternius (Blender, `Tools/Blender/recolour_kit.py`) je slitý do
      jednoho meshe (16 806 trojúhelníků, 10,2 × 8,0 × 3,1 m) a leží v `ArtSource/Ships/Steadfast/
      Interior/CargoBay.glb`.
    - `Tools/Assets/import_interior.py` ho naimportuje do `/Game/Environments/Steadfast`, postaví
      materiál `M_KitTrim` (odbarvit → zesvětlit → gunmetal, ORM na roughness/metallic/AO, oranžová
      emise), přiřadí instance na sloty, postaví herce v `TestSpace` 500 m stranou a rozsvítí
      osm světel. Celé se to dá kdykoliv přehrát znovu.
    - **Tři pasti, které to držely šedé** (podrobně kap. 12): chybějící usage flag Nanite,
      nepřipojený texturní parametr se sRGB `DefaultTexture` (materiál se v zabalené hře vůbec
      nezkompiloval a engine kreslil šachovnici `WorldGridMaterial`) a `unreal.Color` v pořadí BGRA.
    - Volná kamera snímků umí `exposure` – bez zafixované expozice automatika vyrovnala každou
      změnu materiálu a měření nedávalo smysl. Pro interiér sedí 2,0.
    - Snímky: `-Preset steadfast_interior`. **Zbývá doladit:** gunmetal je pořád spíš stříbrný než
      šedomodrý a kit nemá strop.
59. **Nákladový prostor: modrá ocel místo stříbra, změřeno** (23. 9. 2026). Autor upřesnil cíl: **ne
    kopie jedné reference, ale styl** – futuristické sci-fi, každá loď vlastní design, stejný „vibe“
    (tři jeho obrázky jsou lokálně v `ArtSource/Reference/Mood/`, mimo git). Změřené rozsahy těch
    obrázků (sRGB): B/R 1,1–1,6 (studené), sytost 0,25–0,45, stíny p10 0,05–0,13, světla p90 ~0,7.
    - **Ladění za běhu:** `space.Kit`, `space.KitColor`, `space.KitLight`, `space.KitReset`
      (`Source/gamespace/SpaceInteriorTuning.cpp`). Zesvětlení, metallic a drsnost jsou teď parametry
      `M_KitTrim`; interiér a světla se hledají podle tagů (`SpaceInterior`, `SpaceInteriorLight_Work`,
      `_Accent`), protože jména herců z editoru v zabalené hře nejsou.
    - **Měření** (`-Preset interior_tune`, 15 variant, pevná expozice 2,0, stěna/podlaha/detail stěny):
      výchozí stav stěna B/R **0,95**, sytost 0,05 – tedy teplé stříbro, ne šedomodrá.
      - Otevřený strop to **nebyl**: slunce i sky light na nulu změnily barvu stěny o ~1 %.
      - Samotná modřejší barva gunmetalu posune B/R jen na 1,00–1,05: **teplá světla modrou vyruší**.
      - Světla 7000 K místo teplých (255, 238, 214) jsou největší páka (B/R 1,06 samo o sobě).
      - Nižší metallic povrch **zesvětlí** (víc difuzní složky), nezmodří.
      - Zesvětlení ×1,25 je hlavní příčina „křídového“ vzhledu; jas jde s ním lineárně.
    - **Nové hodnoty** (`import_interior.py`): gunmetal (0,35, 0,42, 0,55), zesvětlení 0,8, metallic
      ×0,4, pracovní světla 575 lm a 7000 K; oranžové akcenty beze změny. Výsledek v zabalené hře:
      stěna B/R **1,26**, sytost 0,21, jas 0,58; podlaha 1,28 / 0,24 / 0,52 – v rozsahu referencí.
    - **Zbývá:** stíny jsou pořád světlé (p10 0,19 proti 0,05–0,13). To už je rozložení světla,
      ne materiál: kontrast přinese strop se světelnými pásy a tmavšími kouty (další krok).
    - Test `test_interior.py` hlídá parametry, usage flagy, výchozí textury samplerů, tagy a světla.
60. **Nákladový prostor zastropený a uzavřený** (23. 9. 2026).
    - **Strop tam byl, jen obráceně:** shell z kitu má ve 2 m desku 8 × 6 m, jenže je to podlahový díl
      lícem nahoru. Materiál je jednostranný, takže zevnitř deska neexistovala. Navíc stěny prostor
      neuzavíraly (otevřené rohy u zadního konce, některé panely lícem ven) – obojí našel průzkum
      paprsky s ohledem na orientaci plochy v Blenderu.
    - **`Tools/Blender/build_cargo_bay.py`** (headless Blender) staví `CargoBay.glb` z
      `CargoBay_Shell.glb` (původní prostor) a dílů vybalených přímo ze zipu kitu: strop z 12 desek
      `Platform_DarkPlates` lícem dolů, 6 svítidel `Prop_Light_Wide` ve dvou řadách a obložení 14
      deskami těsně za stěnami lícem dovnitř (kde stěna je, schová se; kde není, zavře díru).
      Materiály dílů se mapují na materiály shellu, svítidla dostanou `M_Lamp` → `MI_KitLamp`
      (studená bílá emise). 18 182 trojúhelníků.
    - **Světla:** pracovní světla jsou bodovky (spot) pod svítidly mířící dolů, 1150 lm, 7000 K,
      kužel 80°; oranžové akcenty u podlahy 200 lm. Změřeno `-Preset ceiling_tune` s kamerami uvnitř:
      575 lm / 65° nechalo stěny skoro černé (průměr 0,21), 1800 lm přepálilo podlahu (p90 0,83),
      a oranžová světla na 550 lm barvila celý strop do hněda (B/R 0,93 při pohledu nahoru).
    - Výsledek (zabalená hra, `steadfast_interior`): B/R 1,19–1,22, průměrný jas 0,21–0,31, stíny p10
      0,01–0,02, světla p90 ~0,77. Oproti bodu 59 přibyl kontrast, který bez stropu chyběl.
    - Kamery `steadfast_interior` stojí uvnitř (dřív byly za přední stěnou, která je zezadu
      průhledná); přibyl záběr `e_ceiling`. Pro snímky zvenku zůstává `a_above`.
    - Zadní stěna má za dveřním rámem mezeru, kterou teď zavírá obložení – vchod do chodby ke
      kokpitu se do obložení vyřízne v dalším kroku.
61. **Chodba ke kokpitu a strojovna** (23. 9. 2026). Steadfast zatím nemá rozvržení lodi, zvoleno:
    +X je směr letu; strojovna (x −7..−1 m, 6 × 6 m) | přepážka 1 m | nákladový prostor (0..8) |
    přepážka | chodba (9..17, 2 m široká) | zavřené dveře ke kokpitu. Přepážky jsou tam, kde podlaha
    shellu přečnívá o metr za jeho stěny.
    - **`Tools/Blender/build_steadfast_interior.py`** (přejmenovaný `build_cargo_bay.py`) staví
      místnosti z obecných kusů – podlaha, stěny s otvory, strop, svítidla, dveřní rám (kit
      `Door_Frame_Square` ×0,4), vybavení – a každou exportuje jako vlastní GLB (`CargoBay`,
      `Corridor` 2 106 trojúhelníků, `EngineRoom` 39 083). Pozice světel zapíše do
      `Interior_lights.json`; `import_interior.py` podle něj staví bodovky a akcenty (18 světel).
    - Chodba: panely `ShortWall_Metal2`, svítidla uprostřed, průduch ve stropě, terminál a oranžové
      světlo nad zavřenými dveřmi. Strojovna: tmavé panely a podlaha, jádro (`Column_Hollow`) se
      čtyřmi trubkovými sloupy, regály s potrubím podél stěn, konzole, oranžový svit u paty jádra.
    - **Průchody do shellu:** skript vyřízne svislé plochy v otvoru 2 m přes celou přepážku (shell
      má za stěnou ještě vnější stěnu na konci přečnívající podlahy) a odstraní starý dveřní rám,
      který stál kolmo přes zadní stěnu a nikam nevedl. Přečnívající podlaha míří lícem dolů, proto
      mají průchody vlastní podlahu.
    - **Akcenty 100 lm** (`-Preset accent_tune`): uvnitř místností (dřív stály za stěnou prostoru)
      už 200 lm oteplilo prostor a strojovnu na B/R 0,97–1,11; se 100 lm jsou všechny záběry
      1,10–1,28 a oranžová místa pořád čitelná.
    - Výsledek (`-Preset steadfast_interior`, 10 záběrů): B/R 1,10–1,28, průměrný jas 0,22–0,32, stíny
      p10 0,01–0,04, světla p90 0,66–0,79 – v rozsahu autorových referencí.
    - **Omezení:** interiér nemá kolize (postava jím zatím nechodí, jde jen o vzhled), stojí v
      `TestSpace` samostatně mimo loď, dveře ke kokpitu se neotvírají a kokpit Steadfastu (procedurální
      dashboard) ještě není. Zvenku jsou místnosti otevřené – zakryje je trup lodi. *(Vše kromě trupu
      vyřešil bod 62.)*
62. **Interiér Steadfastu k projití** (23. 9. 2026, autor: „chci si to ozkoušet i v té hře samotné a mít
    možnost tam projít“).
    - **Jak se tam dostat:** klávesa **I** (kdekoliv v TestSpace, z lodi i pěšky), tlačítko
      **INTERIÉR STEADFASTU (I)** v menu pauzy, nebo `space.Interior`. Hráč se objeví v nákladovém
      prostoru čelem dopředu; další I (nebo tlačítko ZPĚT) ho vrátí do lodi, kterou řídil, nebo na
      místo, kde stál. Loď zatím stojí tam, kde ji opustil (`ASpacePlayerController::ToggleInterior`).
    - **Umělá gravitace:** `ASpaceGravityVolume` (box kolem celého interiéru, 981 cm/s², „dolů“ je -Z
      boxu). `APlayerCharacter::UpdateGravity` se na něj ptá dřív než na planetu a uvnitř vypne
      záchranu z terénu.
    - **Kolize:** všechny místnosti a sklo kolidují podle polygonů (`CTF_USE_COMPLEX_AS_SIMPLE`).
      Ověřeno v zabalené hře scénářem `-Preset interior_walk`: `space.Walk` postavu posílá a do logu
      píše `WALK end` – prošla prostor → chodba → dveře → kokpit, zastavila se o boční stěnu na 2,16 m
      (stěna 2,5 m minus poloměr kapsle), o sedačku a o potrubí ve strojovně.
    - **Dveře:** `ASpaceSlidingDoor` mezi chodbou a kokpitem, dvě křídla (`DoorLeaf.glb`) se odsunou,
      když je hráč blíž než 2,6 m (0,55 s), a zablokují, když jsou zavřená. `space.Door 1|0|-1`.
    - **Strop 2,4 m** místo 2 m (postava s kamerou za zády byla ve 2 m stísněná). Nad stěnami shellu je
      pás obložení, deska ve 2 m je pryč (svítidla visí nad ní).
    - **Vlastní dveřní rámy:** rám z kitu měl průchod jen 1,4 m vysoký (masivní nadpraží); nové rámy
      mají průchod 1,3 × 2,1 m, oranžový pruh a nadpraží ke stropu.
    - **Kokpit** (x 17–22 m, 5 × 5 m): procedurální dashboard (šikmý pult, tři modré displeje, řada
      oranžových tlačítek), dvě sedačky, okno přes celou šířku se sloupky a sklem (`CockpitGlass.glb`,
      průsvitný oboustranný `M_KitGlass`, bez Nanite), modré světlo od displejů. B/R snímků 1,39–1,50.
    - **Opravy:** černé klíny u zadního průchodu byl stín terminálu, který kitbash zapustil napůl do
      stěny (smazán, nahrazen celým terminálem); tenká deska podél osy prostoru před předními dveřmi
      („sloup“ ve snímcích) zastavovala hráče – smazána; nápis FREE LOOK se už nekreslí, když pohled drží
      volná kamera snímků; runner snímků spouštěl konzolové příkazy každého snímku dvakrát.
    - Rozvržení je v `ArtSource/Ships/Steadfast/Interior/Interior_layout.json` (světla, dveře, start,
      gravitace; píše Blender skript, čte import).
    - **Zbývá:** vnější trup Steadfastu (interiér zatím stojí sám v prostoru, zvenku otevřený) – samostatný
      projekt jako u Vanguardu, čeká na autorovo rozhodnutí.
63. **Interiér po autorově projití: díry, blikání, kokpit, výkon** (23. 9. 2026, autor: „glitchující
    krabice… díry ve stěnách… cockpit úplně mimo reference… výkon slabší“).
    - **Díry:** `Tools/Blender/find_interior_holes.py` střílí paprsky z mřížky bodů v každé místnosti
      a hlásí ty, které utečou ven (rub plochy se prochází, protože ho Unreal nekreslí). Našel škvíry
      v rozích, kde se panely jen dotýkají hranou, a 5 cm mezery v rozích obložení. Oprava: tmavý
      uzavřený plášť lícem dovnitř kolem strojovny, prostoru a chodby (s otvorem pro dveře kokpitu)
      – škvíra ukáže tmu, ne planetu. Kokpit má vlastní uzavřenou kabinu. Výsledek: žádný skutečný
      únik (zbývá 28 falešných paprsků z bodu uvnitř pultu).
    - **Blikání beden:** kitbash měl bedny dvakrát – jednu na podlaze (0,04–1,08 m) a stejnou napůl
      zapuštěnou (−0,52–0,52 m); v pásu 4–52 cm se jejich stěny přetahovaly (z-fighting). Stavitel
      teď zapuštěné a přesně zdvojené díly maže (26 dílů) a také vnější stěny shellu, které ležely ve
      stejné rovině jako stěny strojovny a chodby. Měřeno `-Preset flicker_check` (8 snímků stejné
      kamery, podíl pixelů, které se mění o víc než 8 %): prostor 0,84 % → 0,01 %.
    - **Výkon:** `-Preset perf_interior` (stat unit): stíny 22 lokálních světel byly většina snímku.
      Akcenty a světla displejů stíny nevrhají, pracovní světla dosvítí 4,5 m místo 9 (už nestínují
      sousední místnosti). Prostor 15,3–18,8 → 12,0 ms, strojovna → 10,7, chodba → 10,7, kokpit ~10,5.
    - **Kokpit podle reference** (`Docs/UI`, kokpit Constellation): prosklená kabina ze tří žeber
      s tmavými vzpěrami a sklem i nad hlavou, nízký pult u přídě, dvě MFD na ramenech pro každého
      pilota po stranách výhledu, vysoká černá sedadla s bílými pruhy, joystickem a plynem v područkách,
      boční konzole a panel nad hlavou s tlačítky. Obrazovky jsou modré plochy (jas emise 1,5).
64. **Srovnání se SC a výchozí kvalita pro autorův počítač** (23. 9. 2026). Autor: RTX 2060 6 GB, 1920 × 1080;
    směr grafiky **podle SC** (teplá architektura se světelnými lištami, tmavý základ, studené hologramové UI –
    nahrazuje modrou ocel z bodu 59), assety zdarma nebo po dílech z Meshy/Scenario, žádné placené balíky
    (průzkum zdrojů: `Docs/AssetSources_Free.md`).
    - **Srovnání** (reference `ArtSource/Reference/Mood/sc_cockpit_*.webp`, lokálně): náš interiér je 2–3×
      světlejší (střední jas 0,42–0,44 proti 0,08–0,18), bez jasných světelných lišt (p99 0,71–0,78 proti
      0,71–0,88), celý studený (B/R 1,2–1,27 proti teplým 0,72–1,05), o ~40 % méně jemného detailu, s jedním
      materiálem kitu a prázdnými obrazovkami. Plán v tomto pořadí: výkon → světlo podle SC → hologramové
      obrazovky s obsahem → materiály (ambientCG) → detail geometrie → letový kokpit Vanguardu.
    - **Výkon ve 1080p** (`-Preset perf_quality -Width 1920 -Height 1080`): filmová 100 % = 49 FPS v interiéru,
      70 v letu; epická + TSR 75 % = 70–78 a 90–98. Interiér brzdí počet pixelů (skupiny kvality o stupeň níž
      0–1 ms, rozlišení vykreslování 6 ms). **Nové výchozí nastavení: epická, vykreslení 75 %, TSR** –
      `USpaceUserSettings` verze 4 převede uložená nastavení jednou; v menu „Kvalita grafiky“ a „Rozlišení
      vykreslování (TSR)“ jde zpět na filmovou a 100 %. Pod 50 % nikdy.
65. **Světlo interiéru podle SC** (23. 9. 2026, krok 2 plánu z bodu 64). Měřeno s **automatickou expozicí**,
    jak hru vidí hráč (`-Preset sc_look -Width 1920 -Height 1080`, čísla `python Tools/Shots/measure_look.py`):
    průměrný jas byl už v rozsahu SC (0,16–0,26), chyběla jasná světla (p99 0,56–0,69 proti 0,56–0,88) a barva
    byla studená (B/R 1,10–1,33 proti 0,72–1,05).
    - **Světelné lišty** (`M_Strip` → `MI_KitStrip`, teplá bílá, emise 14): po hraně stropu všech místností,
      u podlahy v chodbě, svisle v rozích strojovny a na vnitřních stranách rámů dveří.
    - **Paleta:** neutrální tmavý kov (gunmetal 0,33/0,33/0,34), pracovní světla 5200 K, svítidla teplá bílá.
      Teplý kov pod teplým světlem byl moc hnědý (B/R 0,57–0,63, sytost 0,42–0,49) – `-Preset sc_tune`.
    - **Výsledek:** prostor, chodba a strojovna B/R 0,70–0,77, sytost 0,27–0,35, p99 0,72–0,96 – v rozsahu SC.
      Kokpit zatím B/R 1,08–1,23 a p99 0,56 (bez lišt, obrazovky bez obsahu) – krok 3.
    - Jemného detailu je pořád méně (0,024–0,027 proti SC 0,024–0,035) – materiály a geometrie, kroky 4–5.
66. **Hologramové obrazovky v kokpitu** (23. 9. 2026, krok 3). `Tools/Assets/draw_holo_screens.py` kreslí obsah ve
    stylu SC UI (naše písma Rajdhani / Share Tech Mono): POWER MANAGEMENT (PWR/WPN/THR/SHLD/COOL), SELF STATUS se
    siluetou lodi, COMMUNICATIONS, SCANNING, dvě obrazovky pultu a disk radaru. Jména jsou naše (Veyra, Halcyon),
    ne ze SC. Obrázky leží v `ArtSource/Ships/Steadfast/Interior/Screens/`.
    - Obrazovky jsou vlastní mesh `CockpitScreens.glb` (bez Nanite, bez kolize, bez stínu) s přesným mapováním
      obrázku; materiál `M_KitHolo` aditivní, unlit, oboustranný: obrázek × modrý tint × jas 5 × jemné řádky.
      Černá je průhledná, všechno nakreslené svítí. Každá obrazovka má instanci `MI_Holo_<stránka>`.
    - Levý pilot Self Status | Power, pravý Comms | Scan, na pultu Flight a Systems, nad pultem radar.
    - Statické – živá data (jako displeje Vanguardu, `UCockpitDisplayComponent`) přijdou, až Steadfast poletí.
    - Zbývá v kokpitu: hranatá sedadla, žádné světelné lišty (p99 0,53–0,56).
67. **Materiály: opotřebení, špína, podlahové desky, kůže** (23. 9. 2026, krok 4). Materiály z ambientCG
    (CC0, `ArtSource/Textures/ambientCG/`, 2K: PaintedMetal004 a 013, MetalPlates006, Leather033A, Rubber004)
    importuje `import_interior.py` (`/Game/Environments/Steadfast/Surfaces`) a `M_KitTrim` je vrství
    na kit:
    - **opotřebení** – škrábance na holý kov (metalness mapa PaintedMetal004 = kde je lak prodřený), hlavně
      na hranách kitu (kde jeho normála uhýbá od roviny); parametry `WearAmount` 0,5, `WearEverywhere` 0,05;
    - **špína** – velké skvrny (AO PaintedMetal013) a dutiny kitu (jeho AO), `GrimeAmount` 0,5;
    - **podlahové desky** MetalPlates006 na všem, co míří nahoru (`FloorPlates` 0,65).
    Vše promítané ze tří stran ve světových souřadnicích, UV kitu nevadí. Sedadla mají `M_KitLeather`
    (černá kůže z Leather033A).
    - **Měřeno** (`-Preset wear_tune`): opotřebení 0,8 s pětinou mimo hrany dělalo z celých stěn maskáč (detail
      0,040, nad SC); 0,5 skoro jen na hranách = 0,027–0,030, v rozsahu SC (0,024–0,035). Barva a jas beze změny.
    - Ladění za běhu: `space.Kit WearAmount / WearEverywhere / GrimeAmount / FloorPlates`.
68. **Opotřebení prověřené zblízka a první díly z Meshy** (23. 9. 2026, autor: „prověř to opotřebení“, krok 5).
    - **Opotřebení** (`-Preset wear_check`, stěna / bedna / rám dveří / podlaha zblízka proti výřezům SC):
      v SC referencích jsou lakované panely skoro čisté. Naše 0,5 vypadalo jako bílé oděrky a na
      procedurálních dílech (rámy dveří, víka) sedělo náhodně uprostřed ploch. Teď `WearAmount` 0,2,
      jen na hranách (`WearEverywhere` 0), holý kov jen o stupeň světlejší než lak (0,30) a matný (0,45).
    - **Meshy** (`Tools/Assets/meshy_generate.py --spec ArtSource/Ships/Steadfast/Kitbash/meshy_parts.json
      --out ArtSource/Ships/Steadfast/Kitbash/Meshy --refine`, 10 kreditů za díl):
      - `PilotSeat` – vysoké černé kožené sedadlo s bílými bočnicemi, joystickem a lyžinami; výborné, ve hře.
      - `SideConsole` – boční panel s oranžovými přepínači a pákou; ve hře u obou stěn kokpitu.
      - Přední pult nevyšel dvakrát: poprvé celá kabina s oblouky (zahozeno), podruhé skříň s obrazovkami –
        ta stojí jako `EquipmentRack` ve strojovně. Přední pult zůstává procedurální s hologramy.
    - Díly jsou samostatné herce s vlastními texturami z Meshy (`/Game/Environments/Steadfast/Props`),
      rozmístění v `MESHY_PROPS` stavitele → `Interior_layout.json` → `import_interior.py` (`place_props`:
      jednotné měřítko podle šířky, postavené na podlahu, Meshy dívá do −Y → otočení −90°). Kolize podle
      polygonů. Procedurální sedadla a boční konzole jsou pryč.
69. **Šablonové nápisy a značky (decaly) ze Scenario** (23. 9. 2026, krok 5). Jeden atlas 4 × 4 (2048 px)
    vygenerovaný ve Scenario (GPT Image 2.5 Sunburst, 12 CU): žluté a oranžové výstražné pruhy, CARGO BAY,
    ENGINE ROOM, COCKPIT, DECK A-01…03, šipka, výstražný trojúhelník, CAUTION HIGH VOLTAGE, NO STEP,
    HALCYON FREIGHTWORKS s logem, FIRE SUPPRESSION, AIRLOCK, „07“ – ošoupaná šablonová barva na černé.
    Texty vyšly přesně podle zadání, jména jsou naše. Leží v `ArtSource/Ships/Steadfast/Interior/Decals/`.
    - `M_Decal` (deferred decal, translucent): políčko atlasu podle `CellU`/`CellV`, černá = bez barvy
      (neprůhlednost z jasu), barva ztlumená na 0,7. Instance `MI_Decal_NN` pro každé políčko.
    - Rozmístění v `DECALS` stavitele (políčko, bod na povrchu, normála povrchu, velikost) →
      `Interior_layout.json` → `place_decals`: 17 decalů – nápisy u dveří, šipka ke kokpitu, pruhy na
      podlaze před průchody, výstrahy ve strojovně.
    - Natočení na stěně: decal promítá podél své +X a atlas na stěně leží na boku – potřebuje roll +90°
      (−90° ho obrátí vzhůru nohama). Podlaha pitch −90°.
70. **Rozvody: potrubí, kabely, rošt** (24. 9. 2026, krok 5). Stavitel má pomůcky `cylinder`, `pipe_run`
    (trubka s objímkami a závěsy ke stropu každý metr), `cable` / `cable_bundle` (tři kabely prověšené po
    parabole mezi sponami) a `grating` (rošt nad tmavou šachtou):
    - chodba: dvě trubky pod stropem, svazek kabelů podél stěny, rošt uprostřed podlahy;
    - nákladový prostor: dvojice trubek podél obou stěn pod stropem;
    - strojovna: silné přívody od jádra ke stěnám, trubky podél stěn a svisle v rozích, svazky kabelů.
    Chodba má +8 000 trojúhelníků, strojovna +8 800; FPS ve 1080p beze změny (70–73). Jemný detail chodby
    0,027 → 0,035, na horní hraně SC (0,024–0,035). Díry: žádná nová.
    - Kabely jsou černé a šedé. Materiál s „light“ ve jméně import bere jako svítící pás – první verze měla
      oranžově svítící kabel.
71. **Přední pult kokpitu Steadfastu** (24. 9. 2026, konec kroku 5). `front_console`: tři panely se spárami,
    výřez pro kolena, zkosený lem se světelnou linkou, větrací štěrbiny, stříšky nad obrazovkami, podstavec
    radaru se svítícím lemem a horní deska plná páček, knoflíků, podsvícených kláves a kontrolek (7 700
    trojúhelníků celý kokpit). Horní linie pultu beze změny, obrazovky a radar sedí na stejném místě.
    - **Autor k interiéru (24. 9. 2026), vstup do příštího hodnocení:** proti SC „pořád znatelně něco chybí“,
      předměty v místnostech působí osaměle a některé jsou špatně umístěné.
72. **Letový kokpit Vanguardu podle SC** (24. 9. 2026, krok 6). Srovnání s referencemi (`Docs/UI`, kokpit
    ve vesmíru a nad planetou): displeje už obsahem odpovídají, rozdíl byl v jasu – náš kokpit nad
    planetou měl střední jas 0,26–0,43, SC 0,13–0,19 (tmavý kokpit, jasné displeje).
    - `ASpaceshipPawn::CockpitExposureBias` = −0,7 EV jen pro kokpitovou kameru (ve skoku dál platí
      `QuantumExposureBias`). Změřeno `-Preset cockpit_look` (0 / −0,5 / −1 / −1,5 EV přes `space.Post`).
    - Displeje jsou emisivní a ztmavly by s expozicí: `emissive_strength` 1,8 → 2,9 (= ×2^0,7) ve
      `Vanguard_setup.json`, po expozici tedy stejně jasné jako dřív (a nekvetou víc).
    - Sklo displejů (`ESpaceHudSymbol::MfdGlass`) poloviční jas a slabší mřížka – tmavé sklo, jasný obsah.
    - Výsledek (`-Preset cockpit`, 1080p): nad planetou 0,10–0,19, ve vesmíru 0,05.
    - Nedělal jsem tlačítka PWR/WPN/THR/SHLD/COOL a QTM/RADR/PROX/HIT/MISL: v SC ovládají systémy (energie,
      zbraně, štíty), které hra zatím nemá – přijdou se SC-6.
73. **Autorovo hodnocení interiéru a nový směr** (24. 9. 2026). Předměty v lodi nepůsobí, že na loď patří
    a mají využití; klávesnice u dveří (`Prop_AccessPoint`) je no-go (velká, svítivá, levná), přední pult
    Steadfastu „jako z levné low poly hry“, stěny kitu pořád low poly. Co sedí: nápisy (decaly), osvětlení
    lištami, hologramy (ladit), sedadla z Meshy. **Nový postup pro každou loď:** nejdřív detailní návrh ve 2D
    – technický list podle RSI Ship Matrix a popsaný řez a půdorysy, kde má každá místnost a každý předmět
    účel (vzory `Docs/UI/reference_tvorba_lodi/`) – a do 3D až po autorově schválení, bez kompromisů a bez
    stylizace podle jednoho dvou obrázků. **Pořadí (autor):** 1 první osoba, 2 usedání do pilotního křesla
    (animace z Mixamo), 3 2D návrh Steadfastu, 4 stavba Steadfastu podle něj.
74. **První osoba** (24. 9. 2026, krok 1 z bodu 73). Výchozí a v lodích jediný pohled hráče; třetí osoba
    zůstává na testy – **V** přepíná (`APlayerCharacter::SetFirstPerson`).
    - `FirstPersonCamera` na kapsli v očích (165 cm nad chodidly, 14 cm před obličejem), FOV 90°, pohled
      nahoru a dolů ±80°. Tělo se otáčí s pohledem (v první osobě `bOrientRotationToMovement` vypnuté),
      hlava je skrytá (`HideBoneByName("head")`), zbytek těla i stíny zůstávají – při pohledu dolů je vidět.
    - Výchozí stav už v konstruktoru (postava, která nezačne hru – editor, testy – je taky v první osobě).
    - Klávesnice u dveří jsou z interiéru pryč. Snímky `interior_walk` jsou teď z první osoby.
    - Test `test_character_l6.py`: první osoba výchozí, oči 1,6–1,7 m, přepnutí tam a zpět.
75. **Steadfast – 2D návrh v2 ke schválení** (24. 9. 2026, krok 3 z bodu 73). Nic ve 3D, dokud ho autor neschválí.
    - `ArtSource/Ships/Steadfast/Design/Steadfast_Design.md`: vize, parametry, uspořádání, pohyb posádky, designový jazyk a otevřené otázky.
    - `Steadfast_layout.json`: jediný zdroj pravdy – místnosti, objekty s účelem, dveře; metry, x dopředu, y na levobok.
    - Výkresy `Steadfast_deck_upper.png`, `Steadfast_deck_lower.png`, `Steadfast_cutaway.png` kreslí `Tools/Design/draw_ship_design.py <layout.json>` (Pillow, písmo Bahnschrift).
    - `ArtSource/Ships/Steadfast/Steadfast_spec.json` je ve tvaru RSI Ship Matrix. Kód ho nečte; letové hodnoty se ladí jinde.
76. **CLAUDE.md a skills** (24. 9. 2026). Vstupní bod je krátký `CLAUDE.md` v kořeni repozitáře.
    Know-how je rozdělené do sedmi skills v `.claude/skills/`, které se načítají podle úkolu: ship-pipeline, ship-interior, blender-mcp, unreal-scripting, unreal-shots-and-look, cockpit-displays a asset-sources.
    HANDOFF, WORKFLOW a README zůstávají jako historie a úplný seznam; hledej v nich grepem.
77. **Oficiální Blender MCP (Blender Lab) vedle komunitního** (24. 9. 2026).
    - Server `blender-lab` (uvx z git tagu v1.0.3, `BLENDER_MCP_PORT=9877`); addon `bl_ext.user_default.mcp` na portu 9877.
    - Komunitní `blender` zůstává na 9876, oba běží naráz.
    - Oficiální addon potřebuje online přístup: Blender spusť s `--online-mode`, nebo zapni Allow Online Access.
    - Přímý klient socketu je `Tools/Blender/mcp/lab_socket.py`. Podrobnosti a srovnání jsou ve skillu `blender-mcp`.
78. **Operátory přes MCP** (24. 9. 2026). Helper `Tools/Blender/mcp/ops_context.py` (`run_op`, `edit_mode`) dává operátorům kontext 3D viewportu.
    - Test `test_ops_context.py`: join, modifier_apply, bevel s profilem, boolean a inset projdou headless i živě; knife_project jen živě.
    - Headless ho helper odmítne, protože by tiše nic neudělal.
    - Pravidlo „přes MCP žádné operátory“ ve WORKFLOW 9.2 a AssetPipeline_Modular je nahrazené.
79. **Měřitelná shoda siluety** (24. 9. 2026). `Tools/Blender/silhouette_compare.py` má tři kroky:
    - render: ortografické masky ve Workbench, headless, zepředu, z boku a shora; výřez boxem nebo válcem;
    - compare: vyřízne siluetu konceptu z neutrálního pozadí, spočítá IoU po pohledech, poměr stran a obrázky rozdílu;
    - run: obojí najednou.
    Dva rendery se porovnávají ve světových souřadnicích. Test `Tools/Blender/tests/test_silhouette_compare.py` má 14 kontrol. Postup je ve skillu `ship-pipeline` 3b.
80. **Pilot hard-surface exteriéru: gondola Vanguardu** (24. 9. 2026). AI trup slouží jen jako objemová reference, díl se staví receptem
    `ArtSource/Ships/Vanguard/HardSurface/nacelle.json` přes `Tools/Blender/hs_build_part.py`.
    - Geometrie: panely se skutečnými spárami, prstence, sání a tryska, bevel a weighted normals, greebly z kitu `HS_Kit` přes GN `HS_KitInstancer`.
    - IoU proti Meshy gondole vzrostlo z 0,854 na 0,894 po změření osy a poloměrů z masek. Listy jsou v `Docs/Shots/HardSurface/`.
    - Postup je v AssetPipeline_Modular, v části „Exteriér: hard-surface“.
    - Otevřené: ohnout velké díly kitu podle povrchu, pylon, UV a materiály, import do UE.
    - **Celou loď zatím nepřestavovat, čeká se na rozhodnutí autora.**
81. **Higgsfield: konzistentní pohledy lodi ověřené měřením** (24. 9. 2026, krok 4 plánu vylepšení). Test na starém
    Vanguardu (`Vanguard.blend`), aby šel každý vygenerovaný pohled porovnat se skutečným modelem.
    - Z jednoho hero obrázku GPT Image 2.5 i Nano Banana Pro dobře trefí bok (IoU 0,79–0,82), ale půdorys si domyslí
      (GPT: rozpětí −37 %) a „zepředu“ kreslí šikmo. List 2 × 2 v jednom obrázku je nepoužitelný.
    - **Vodicí silueta jako druhá reference** je hlavní páka. Nejlépe Nano Banana Pro + vodítko: bok 0,97, zepředu 0,90,
      shora 0,98, rozměry do 0,5 %; GPT Image 2.5 + vodítko 0,89 / 0,54 / 0,92. U nové lodi vodítko vzniká z 2D návrhu.
      Zepředu Nano Banana přikreslil dvě plovoucí špičky ploutví → pohledy vždy i prohlédnout.
    - `silhouette_compare.py` má nové příkazy `views` (konzistence konceptů mezi sebou a proti rozměrům ze spec, bez
      modelu) a `guide` (vodicí siluety); test 20 kontrol. Postup, tabulka a přijímací prahy: skill `ship-pipeline` 2a.
    - Surové obrázky a prompty: `ArtSource/Ships/Vanguard/Concept/higgsfield_test/`. Spotřeba ~40 kreditů z ~1000.
82. **Vanguard odstraněn** (24. 9. 2026, autor: „vanguard smaž kompletně“). Obsah `/Game/Ships/Vanguard`, zdroje
    `ArtSource/Ships/Vanguard`, presety snímků i dokumentace; commit `558afe7`, historie v gitu.
    - `BP_SpaceGameMode` spawnuje nativní `ASpaceshipPawn` (šedá krychle, létá). Úvodní obrazovka je bez lodi,
      loď do ní dá `MENU_SHIP` v `build_main_menu.py`.
    - Loď pod testem se nastavuje na jednom místě: `Tools/Tests/ship_under_test.py` (dnes `None`). Hodnoty konkrétní
      lodi testy berou z jejího `<Loď>_setup.json`.
    - Výsledek testů: 20/20 OK, 12 kontrol přeskočeno kvůli chybějícímu modelu.
    - V první osobě zatím chybí rám kokpitu, protože placeholder kokpit je vypnutý.
83. **Wayfarer: nová loď od reference po schválený návrh + Ship Matrix flotily** (24. 9. 2026). Malá multirole pro
    jednoho pilota (Halcyon Freightworks), nahrazuje Vanguard. **Návrh v1 schválen autorem** („schvaluju všechno“),
    další krok 3D.
    - `Tools/Design/fetch_ship_matrix.py`: celá RSI Ship Matrix (255 lodí) a referenční sada `small_multirole`
      (8 lodí, medián, komponenty, obrázky jen ke studiu) v `starcitizenreference/ship_matrix/`.
    - `ArtSource/Ships/Wayfarer/`: spec ve tvaru Ship Matrix proti mediánu, layout (4 místnosti, 19 objektů
      s účelem), `Design.md`, výkresy.
    - Rozměry lodi: 21,5 × 14,7 × 5,6 m, 52 t, 8 SCU, SCM 225 m/s.
    - `draw_ship_design.py` čte obecný layout s blokem `exterior` (nový `ship_sheets.py`): exteriér ve třech pohledech
      s kótami, paluby, řez podle dat a masky siluet. Výkresy Steadfastu zůstaly bajtově stejné.
    - Koncepty (Nano Banana Pro s vodítky z masek, stylový vzor = bok A) proti výkresu: bok 0,95, zepředu 0,88,
      shora 0,89 (první pokus shora 0,64 zamítnut), uzávěr 7 %. Rozpětí v konceptu je o 8 % větší → ve 3D platí výkres.
    - **Ship Matrix a dossier** (`Tools/Design/build_ship_matrix.py`): karty a tabulka všech lodí a u každé lodi
      dossier se stavem pipeline a měřením siluet při každém sestavení. Autor ho chce **u každé další lodi** (skill
      `ship-pipeline` 1b).
    - Publikováno: Ship Matrix https://claude.ai/artifact/VvqHBqFf3xesWcBznpcmHU, dossier Wayfarer
      https://claude.ai/artifact/Busq7MdkvGSXMp7RsgP7Ga.
84. **Wayfarer model v1 létá ve hře** (24. 9. 2026, autor: „ano pusť se do toho“). Postup kroku 3D v1:
    - Higgsfield `multi_image_to_3d` ze čtyř schválených pohledů (30 kreditů, ~25 min fronty): 310 tis. trojúhelníků
      s PBR v `ArtSource/Ships/Wayfarer/Higgsfield/` (surové, needitovat).
    - Textury z GLB vybalí `Tools/Blender/glb_textures.py`. `build_ai_ship.py` čte GLB (`source_model`) a délku měří
      až po otočení.
    - Recept `Wayfarer_ai_build.json`: otočení o 180°, délka 21,5 m, díly Gear a Ramp (bez zacelování děr), 10 kolizí
      včetně dvou až k patkám (`gear_extension_cm` 0), sockety, emise trysek gondol. Po buildu `bake_ship_ao.py`.
    - Export bez chyb, `Wayfarer_setup.json` s letovými hodnotami ze specu a dočasným kokpitem, import jako
      `BP_Ship_Wayfarer` (výchozí pawn), úvodní obrazovka s Wayfarerem.
    - Loď pod testem je `ship_under_test.SHIP = "Wayfarer"`. Testy: 20/20 OK. Zobecněné testy: výstup, když socket
      už stojí mimo trup; kokpit a free look se přeskočí bez interiéru a Display socketů; test podvozku počítá s posunem
      trupu k pivotu.
    - Silueta modelu proti výkresu: bok 0,91, shora 0,78, zepředu 0,59. AI dala gondoly k trupu (y ±2,46 místo 3,4 m)
      a sklopila křídla dolů.
    - Známé: zevnitř kokpitu tmavé střepy AI trupu, neprůhledné sklo, rampa visí pootevřená, v ship_views „space“ je
      loď mimo záběr.
    - Nové nástroje: `Tools/Blender/render_ship_views.py` (rendery s texturami ze 6 úhlů) a sekce „3D model“
      v dossieru (`dossier.json` → `model`).
    - Další krok: průchozí interiér podle layoutu, uvnitř létající lodi.
85. **Wayfarer 1.1: proč vypadal rozbitě a špinavě, a oprava** (24. 9. 2026, autor: „vypadá nekvalitně, jak kdyby
    byla rozbitá špinavá“). Změřené příčiny:
    - **UV atlas využíval 0,4 % textury.** AI mesh byl polévka rozpojených trojúhelníků (309 tis. vrcholů → 149 tis.
      po svaření) a `smart_project` s marginem na každý z 52 tis. ostrůvků je zmenšil na nic. 4K textura se chovala
      jako ~260 px.
    - Zdrojová AI textura (2K mozaika) měla šmouhy na hranách ostrůvků a zapečené fialové odlesky.
    - `M_Ship_PBR` přidával procedurální panely (`PanelStrength` 0,6) přes vymodelované, grunge a opotřebení.
    - Trysky svítily jen na ploškách mířících přímo dozadu, takže vznikl vzorovaný „medailon“.
    Opravy:
    - `build_ai_ship.py`: `weld_m` (svaření vrcholů) a unwrap s nulovým marginem a jedním `pack_islands` (ADD
      0,0005). Atlas teď využívá 55 % textury a log to vypisuje.
    - Nový `Tools/Blender/repaint_ship.py` (po každém buildu, před AO), řízený blokem `repaint` v receptu:
      - AI barva jen rozhodne zónu (bílá, gunmetal, oranžová, sklo, kov trysek); zóny se vyhladí přes sousedy
        a odstraní ostrůvky pod 0,2 m²;
      - každá zóna dostane jednu čistou barvu a jen 30 % AI jasu normalizovaného na zónu;
      - pruhy se berou po texelech z AI kresby (medián, práh), mimo oblast trysek.
    - AI mapy mají příponu `_AI`, hra používá přebarvené.
    - Materiál: `panel_strength` 0, `wear_amount` 0,03, grunge 0,04; emise trysek přes celý disk.
    - Test `test_ship_import` se u lodi s `panel_strength` 0 v setupu řídí tím nastavením.
    Snímky ze zabalené hry jsou prohlédnuté (`Docs/Shots/Wayfarer/`) a dossier je aktualizovaný.
    Zbývá: tvar z AI (zvlněné plochy, gondoly u trupu), neprůhledné sklo, střepy v kokpitu.
86. **Wayfarer exteriér v2: přesně podle výkresu, bez AI geometrie** (24. 9. 2026, autor: „geometrie je mimo, lak
    s tím nesedí, tohle není dost dobré, myslel jsem že tu geometrii zvládneš přesně“). Image-to-3D neumí přesný
    hard-surface; AI model zůstává jen jako reference stylu.
    - `Tools/Blender/hs_build_ship.py` + `HardSurface/Wayfarer_hs.json` staví díly z obrysů layoutu, které spojuje klíč
      `part` v bloku `exterior`:
      - trup je loft (tvar čela natažený na šířku shora a výšku z boku);
      - ostatní díly jsou průnik vytažených obrysů;
      - gondoly jsou rotační přes `hs_build_part.build_into` (panely, pásy, sání, tryska);
      - zbraně jsou válce.
    - Navrch přibylo:
      - panelové drážky: prstence na přepážkách layoutu a podélné linie;
      - rám kabiny se zapuštěným sklem;
      - přesné řezy podél čar (`bisect`) pro okraj skla, oranžový pruh, tmavý nos a záď;
      - účelové detaily přes kit (`place_greebles`, paprsek na trup).
    - `Tools/Blender/hs_assemble_ship.py` (blok `assemble`) dělá herní meshe: aplikuje modifikátory, realizuje instance,
      spojí díly do trupu, skla a podvozku, posune loď do středu, rozbalí UV a postaví k-DOP kolize a sockety
      v souřadnicích layoutu. Pak export a import jako dřív.
    - Každá zóna laku má vlastní slot (M_Ship_Hull: lak, tmavá, oranžová, kov; sklo; emise trysek). Žádná textura.
    - Silueta herního modelu proti výkresu: bok 0,978, shora 0,988, zepředu 0,911 (AI model měl 0,91 / 0,78 / 0,59).
    - Stavba odhalila chybu ve výkresu: ploutev byla shora užší (y 3,55), než je zepředu vykloněná (3,95). Opraveno.
    - Zbývá detail: křídla a ploutve jsou rovné desky, podvozek jsou hranoly, lak je bez jemné struktury, velký poklop
      na střeše trčí šikmo, sklo je do prázdna, rampa není samostatný díl.
87. **Wayfarer: pilot vrstev detailu podle SC na gondolách a zádi** (24. 9. 2026). Autor chtěl stavět na přesném
    základu a jít po rozboru SC (Argo MOLE): decaly, trim, vrstvy tvaru, materiál, světla. Siluetu nesměl pilot
    zhoršit. Každý krok je samostatný commit, skill `ship-pipeline` 3b3. Pilot pokrývá gondoly a záď (x 0 až 6,9 m),
    zbytek lodi je záměrně čistý kvůli srovnání.
    - Krok 1, knihovna decalů: `Tools/Blender/decal_library.py` + `ArtSource/Ships/Shared/Decals/decal_library.json`,
      16 položek a atlasy N/H/AO/BC/M.
    - Krok 2, trim sheet: 8 pásů.
    - Krok 3, mesh decaly v UE 5.8: DBuffer, mastery `M_Ship_MeshDecal` a `M_Ship_MeshDecalPaint`, vlastní díl bez
      Nanite. Ve hře ověřeno, že se kreslí i na Nanite trupu.
    - Krok 4, vrstvy tvaru: `Tools/Blender/hs_detail.py`.
      - Trup: desky s tloušťkou (ořez rovinami), stupňovitý kryt zádi, skluznice na břiše, zapuštěné mřížky a žlab
        s potrubím.
      - Gondoly: pancéřové sektory se stupni, otevřená šachta s potrubím a aktuátorem, vnější potrubí s objímkami.
      - Střešní poklop leží rovně: normála je průměr 7 paprsků a poklop se posunul ze spáry.
      - Pravá gondola má zrcadlenou fázi panelů.
    - Rozmístění decalů a trimu: `Tools/Blender/hs_decals.py` (87 decalů a 38 pásů). Decal přes hranu se vynechá,
      pás se na nespojitosti rozdělí.
    - Krok 5, materiál: `M_Ship_Layered`.
      - Dva laky podle masky, AO se špínou, opotřebení hran a grunge.
      - Vše z vertex colour, které peče `Tools/Blender/hs_layers.py` (AO paprsky, konvexní hrany jen na malých
        ploškách, sekundární lak, míra vrstev).
    - Krok 6, světla: `Tools/Blender/hs_lights.py`.
      - Polohová světla (červená a zelená), bílé zadní, jantarová obrysová.
      - Reflektory na ramenou, světlo v šachtě, světelné pásy.
      - Skutečná světla jdou přes `Export/<Loď>_lights.json` do komponent blueprintu.
    - Snímky: volná kamera v prostoru lodi (`camera_local` / `look_local`) a preset `pilot_views` včetně soumraku.
      Srovnání Meshy / čistá v2 / pilot ze stejných úhlů: https://claude.ai/artifact/PjCuewmYjX94QG41id7TNC
    - Silueta: bok 0,9786 (dřív 0,9781), shora 0,9898 (0,9881), zepředu 0,915 (0,911). Všech 22 testů prošlo.
    - Otevřené:
      - střední hustota je pořád pod SC (prázdné plochy gondol, chybí textové decaly);
      - opotřebení hran je jen na zkoseních;
      - záď v základu fasetovaná;
      - křídla a ploutve ploché;
      - noc netestovaná (jen soumrak).
    - Celou loď přestavím až po schválení pilotu autorem.
88. **Pilot kolo 2: knihovna decalů v2, pravidla, detail zádi, šachta, styl Origin** (24. 9. 2026 večer).
    - Knihovna v2: 4096 px při 2048 px/m, 55 položek s typy strukturní / informační / opotřebení.
      - Strukturní decaly nemají barvu a AO dává nový master `M_Ship_MeshDecalAO`.
      - Texty jsou z Rajdhani a Share Tech Mono; přibyly řady nýtů, čísla panelů, štítky, šipky a stékání.
    - Rozmístění pravidly: 258 decalů (gondoly po 73, trup 112) a 240 běhů nýtů, asi 250 m, zatím jen pilot.
    - Tvar:
      - pancéřové desky a dveře rampy na zadní stěně a zkosení;
      - šachta gondoly se skříňkami, svazkem kabelů, chladicí trubkou a ventilem, vnitřek `BayInterior`;
      - mřížky zádi jsou decaly (výřez do n-úhelníku zadní stěny se protrhl).
    - Materiál ve stylu Origin: světlý lak 0,32, šedý sekundární, leštěný kov, opotřebení jen nad prahem, málo
      špíny.
    - Opravy:
      - černé tahy na přídi gondoly (mřížka na silném zakřivení) a tečkovaný pás na šikmé stěně krytu;
      - alfa výstražného štítku;
      - zadní světlo je jen čočka;
      - obrysy decalů přes drsnost;
      - čísla vzhůru nohama.
    - Výkon 1080p (stejné záběry, `perf_pilot`):

      | Záběr | Čistá v2 | Pilot | Bez decalů a světel |
      | --- | --- | --- | --- |
      | Zezadu zleva | 88 FPS | 82 FPS | 84 FPS |
      | Tři čtvrtiny | 85 FPS | 80 FPS | 81 FPS |
      | Detail zádi | 82 FPS | 75 FPS | 76 FPS |

    - Iterace se od teď kontroluje v Blenderu; balí se a testuje jednou před předáním (CLAUDE.md).
89. **Wayfarer: celá loď podle schváleného pilotu** (24. 9. 2026 v noci, autor pilot schválil).
    - Rozbor referencí SC: hustotu dělají panelové linky, značení je tón v tónu, drobné červené značky, šipky u
      portů. Knihovna má 69 položek a 11 pásů.
    - Úspory: grunge se vzorkuje jen jednou. Decaly se plynule stmívají mezi 60 a 90 m (ověřeno: menu, chase,
      přistání).
    - Noční test (`night_views`, slunce pod horizontem): světla čtou. Obloha levelu v noci zůstává světlá.
    - Část 1 (trup a příď): 686 decalů, desky a pravidlo `greeble_companions`.
    - Část 2: tvarovaná křídla a ploutve (`hs_wings.py`) s decaly.
    - Část 3: podvozek (`hs_gear.py`).
    - Celkem 800 decalů (trup 345, gondoly 109 / 117, křídla 94 / 96, ploutve 19 / 20) a kolem 650 m pásů.
    - Silueta: bok 0,9787, shora 0,9892, zepředu 0,915.
    - FPS 1080p perf_pilot: čistá v2 88 / 85 / 82, celá loď 82 / 79 / 74.
90. **Wayfarer: „feel“ SC – hodnotová stavba, lesk, velké značení, funkční díly** (24. 9. 2026 v noci).
    - Rozbor referencí (tabulka ve skillu ship-pipeline): největší rozdíl je poměr tmavé/světlé plochy a lesklý
      lak, ne počet decalů.
    - Livrej ve vrstveném materiálu: analytické zóny, 3 varianty (A grafitové sedlo, B dělená, C klín a tmavá
      záď) k výběru autorem. Výchozí je A.
    - Clear coat (lesk s odrazy), variace po panelu (tón, drsnost, kovové a karbonové panely, UV1), těsnění ve
      spárách.
    - Velké promítané decaly: WAYFARER, HF-0417, logo Halcyon Freightworks, výstražné zóny EXHAUST a RAMP
      (`generate_big_decals.py`).
    - `hs_functional.py`: 26 bloků RCS, 2 lopatkové antény, bičová anténa, 2 senzorové kopule, 4 přípojky,
      6 závěsů klapek, objímky zbraní.
    - Silueta: bok 0,9781, shora 0,9898, zepředu 0,917.
    - Autor zvolil livrej A. Doplněno: emisní světelné lišty podél spodní části boků, pod kabinou a na břiše
      (`hs_lights` strips s `"on": side / bottom`); stínový kanál s kabely podél boků mezi horním a spodním
      oplechováním (hloubka 5 cm, uvnitř obrysu). Silueta: bok 0,9812, shora 0,9886, zepředu 0,916.
91. **Wayfarer: interiér ze schváleného půdorysu v1, uvnitř létajícího trupu** (25. 9. 2026).
    - `Tools/Blender/hs_interior.py` (recept `interior` v `Wayfarer_hs.json`) staví nákladový prostor, techniku,
      kajutu a kokpit: podlahy z dlaždic, panelové stěny (tmavý spodní pás, žebra, soklová lišta), stropy
      se světelnými lištami, přepážky s průchody podle dveří v layoutu a všech 19 předmětů z půdorysu
      (hydraulika rampy, tažný paprsek, úchytná mřížka, reaktor, chladič, generátor štítů, skříně, hygienický
      kout, výdejník, lůžko, konzole, přístrojová deska, pilotní křeslo z Meshy). Díly pod podlahou mají poklop.
    - Kokpit: vana do parapetu 1,05 m, nad ním obložení vnitřku trupu (trup zevnitř UE nekreslí).
      Přístrojová deska má 4 obrazovky hry (part `Screens`, sockety `Display_*`), takže MFD fungují
      z pilotního místa. Placeholder kokpit je vypnutý.
    - Světla: 3 bodovky na místnost (20 cd, 5 m, bez stínů), neutrálně teplé (1, 0,93, 0,86); tmavá teplá
      paleta SC (panely 0,13, stěny 0,085, podlaha 0,055). Měření 1080p: průměr 0,32–0,39, B/R 0,78–0,80,
      FPS 62 (nákladový prostor) / 72 (pilotní pohled).
    - Obrazovky na desce jsou o 7 cm výš: při vodorovném pohledu (autor 22. 9.) jsou celé v obraze (15,6–27,8°
      pod okem). Pilot sedí 1,01 m od desky, schválený půdorys (Vanguard měl 1,5 m).
    - Testy psané pro kokpit Vanguardu jsou zobecněné (`test_cockpit_frame` 6, `test_cockpit_displays`,
      `test_free_look` klid −5..0°, menu bez `Screens`). Setup má znovu `cockpit_displays` (5 Hz, 8 cd).
    - Ještě chybí: chůze po přistání (rampa, posuvné dveře, gravitace, vstup postavy) a usednutí do křesla.

92. **Wayfarer interiér v2 – pilot chodby a kokpitu podle SC** (25. 9. 2026). Autor v1 odmítl („prázdný byt
    nebo kancelář“); zastavena práce na celém interiéru, pilot jen na chodbě od rampy ke kajutě (nákladový
    prostor + technická chodba) a na kokpitu.
    - Rozbor 21 referenčních snímků interiérů SC (`starcitizenreference/Screenshot 2026-09-25 02*.png`), tabulka
      „SC má / my máme / chybí“ ve skillu ship-pipeline.
    - `Tools/Blender/hs_interior_kit.py`: díly kitu Quaternius (CC0) s vlastními UV v partu `InteriorKit` (bez
      rozbalení UV, bez Nanite a kolize). Zkosený profil (stěna 3 kit m, horní díl skloněný o 35°), portály na
      každém modulu 1,8 m, stropní trámy, kabelové žlaby, trubky s objímkami, světelné rýhy, zapuštěná svítidla
      s reflektory, modré orientační lišty, tmavý plášť za kitem. Přepážky obložené kitem (`clad_bulkhead`).
      Výbava s účelem: hasicí přístroj, madlo, skříňky se západkami, chráničky kabelů, mřížky (`fittings`).
    - Textury kitu přetónované `Tools/Assets/tone_kit_textures.py` (červená → oranžová Halcyonu, čalounění
      i v antracitu) do `ArtSource/Ships/Shared/Kit/`, v UE na `M_Ship_PBR` (vzorkuje podle UV v prostoru lodi).
    - Decaly interiéru `Tools/Assets/generate_interior_decals.py` (čísla sekcí, místnosti, EXIT, CAUTION, štítky
      komponent, pruh uličky), promítané jako `Int_*` v setupu.
    - Kokpit: čalouněná vana, spodek desky a boky konzolí z trim textur, tmavé čelo kolem displejů, tlačítka
      a přepínače u MFD, řídicí páka a plyn, lišty a podstavec sedadla, spínací panely na parapetu, kovové lemy
      podél skel, akcentová a nožní světla.
    - Náhled v Blenderu ze stejných pozic jako snímky: `Tools/Blender/hs_interior_preview.py`. Nové záběry
      `hold_aisle`, `tech_inside`, `tech_door`, `labels`, `cockpit_right`, `cockpit_left`.
    - Měření 1080p: průměr 0,09–0,21 (SC 0,13–0,23), FPS 61–63 v chodbě, 68 v pilotním pohledu.
    - Čeká na schválení autorem; kajuta a předměty z v1 (mřížka, reaktor, chladiče, štíty) až potom.

93. **Wayfarer: kokpit podle schváleného konceptu A** (25. 9. 2026). Postup jako u exteriéru: render z oka →
    koncepty → výběr autorem → stavba → srovnání z oka.
    - `Tools/Blender/mcp/mcp_eye_view.py`: oko a FOV z manifestu a setupu (= kamera kokpitu), `--headless` clay render.
    - Koncepty Higgsfield (image-to-image z renderu z oka, styl podle autorových snímků SC); vybrán A, přebarvený
      na barvy lodi (`Concept/Cockpit/cockpit_target_space.png`, `_day.png`).
    - `Tools/Blender/hs_cockpit.py` (styl `wrap`): tvarovaná deska kolem pilota napojená na boční konzole,
      zapuštěné MFD s rámečkem a světelnou linkou, řady tlačítek, spínací panely na křídlech, snížený střed
      s holografickým radarem a centrálními displeji, štít nad deskou mimo zorné pole HUD; pod deskou žebra,
      kabely, obložená zadní stěna, pedály, modrá světla.
    - Rám skla: krémový lak lodi (`IntFrame`), oranžové linky souběžné s hranami skla, spáry panelů, kovové lemy,
      madla na sloupcích; normály obložení srovnané, ostré hrany podle úhlu.
    - `Tools/Blender/hs_interior_decals.py`: mesh decaly z knihovny exteriéru v interiéru (štítky u skupin ovladačů,
      EJECT, CANOPY, MASTER ARM, EMERG O2, výrobní štítek; rozptyl panelů, nýtů, mřížek a nápisů po stěnách kokpitu
      i chodby). Knihovna rozšířena o 17 kokpitových položek (`ck_*`).
    - Expozice kokpitu −0,7 → −0,2 EV, emise displejů 2,9 → 2,05 (stejný jas displejů), světla na rám.
    - Měření 1080p: pilotní pohled průměr 0,22 den / 0,19 noc; FPS 65 den / 78 noc.
    - Testy: horní hrana displejů nově ≥ 8° pod okem (HUD končí ~5°), rám kabiny „natřený, ne černý“ (0,15–0,7),
      přiblížení na displeje do 66°.
94. **Wayfarer kokpit k úrovni SC – krok 0 a 1** (25. 9. 2026). Autorovo zadání v 8 krocích, každý krok má vlastní commit.
    - Krok 0: tabulka SC/naše/chybí a měření pohledu (`Tools/Blender/eye_view_metrics.py`): ven 24,5 % (SC 62 %),
      horní hrana desky 39,8 % (SC 35 %), nejširší sloupek 42,1 % (SC 0,7 %).
    - Krok 1: `Tools/Blender/check_ship_geometry.py` + `Tools/Tests/test_ship_geometry.py` prochází. Hlídá zrcadlené decaly, plovoucí díly, průniky, placeholdery a díry. Opravy:
      - nad zadní stěnou kokpitu štít až k trupu;
      - tmavý vnitřní plášť trupu v celém interiéru;
      - oboustranné ostění skla, orientace obložení podle trupu;
      - parapet a boční konzole uvnitř obložení;
      - strop kabiny pod trupem přes celou šířku;
      - křídlo desky zasunuté dovnitř.
    - Krok 2, výhled (SC medián → před → po):
      - ven 62 → 24,5 → 60,8 %;
      - deska 35 → 39,8 → 35,3 %;
      - sloupek 0,7 → 42,1 → 2,3 %;
      - pásmo ±15° čisté.

      Úpravy:
      - kokpit o 0,8 m výš (podlaha 1,15, oko 2,45), 6 schodů z kabiny s podsvícenými nášlapy a zábradlím;
      - štít nad zadní stěnou se žebry;
      - bez páteře a přední vzpěry skla;
      - horní RCS na nosu.

      Silueta beze změny, layout a výkresy přegenerované.
    - Krok 3: displeje jsou skleněné panely:
      - `M_Ship_Screen` masked: obsah neprůhledný, sklo čiré, řádky, fresnel;
      - panel na stojkách 2 cm před deskou, rámeček 7 mm, světelná hrana;
      - matná zadní deska `M_Ship_ScreenBack`;
      - `Screens` bez stínu.

      Čitelné ve dne i v noci (zabalená hra). Rozložení plátna, `ScreenRect` i test beze změny.

---

## 6. Mapa kódu a obsahu

### C++ (`Source/gamespace/`)

| Třída | Soubor | Úloha |
| --- | --- | --- |
| `ASpaceshipPawn` | `SpaceshipPawn.*` | Loď: let (FA, plyn, boost, cruise), přistání, podvozek a precision (SC-2a), výstup, kamery, zvuk, světla, prach. Hlavní soubor letového systému, cíl přestavby na Star Citizen. |
| `APlayerCharacter`, `UPlayerCharacterAnimInstance` | `PlayerCharacter.*`, `PlayerCharacterAnimInstance.*` | Postava na nohou, gravitace, pohled, animace, foot IK, nastupování, záchrana pod terénem. |
| `ACelestialBody` | `CelestialBody.*` | Základ těles: `SampleEnvironment` (výška, hustota, gravitace, režim letu), `GetSurfaceFrame`, `FindNearest`. |
| `AQuadSpherePlanet`, `PlanetTerrain` | `QuadSpherePlanet.*`, `PlanetTerrain.*` | Planeta Veyra: terén, LOD, kolize, atmosféra. |
| `ADistantBody` | `DistantBody.*` | Kulisy (měsíc, obr s prstenci): orbita, rotace, bez gravitace. |
| `ASkyDome` | `SkyDome.*` | Obloha kolem kamery, parametry atmosféry a slunce. |
| `USpaceDustComponent` | `SpaceDustComponent.*` | Prach, který se s rychlostí mění v čáry. |
| `ASpaceGameMode` | `SpaceGameMode.*` | Herní režim (loď, HUD, controller, nastavení rebasingu). |
| `ASpaceMenuGameMode` | `SpaceMenuGameMode.*` | Režim úvodní obrazovky (bez pawnu). |
| `ASpacePlayerController` | `SpacePlayerController.*` | Globální klávesy (Escape/F10, H), menu, pauza, kamera a hudba úvodní obrazovky. |
| `SSpaceMenu` | `SpaceMenuWidget.*` | Menu ve Slate (bez UMG assetů): titul, pauza, nastavení. |
| `USpaceUserSettings` | `SpaceUserSettings.*` | Nastavení hráče (grafika a hlasitosti, citlivost, invert, HUD, FPS). |
| `USpaceFlightHud`, `USpaceHudGauge`, `USpaceHudVirtualJoystick` | `SpaceFlightHud.*` | SC-1c letový HUD v UMG: kontrolky, ukazatel rychlosti a omezovače, G-metr, boost a afterburner, virtuální joystick. Strom widgetů stavěný v C++. |
| `USpaceCockpitDisplays`, `USpaceHudRadar`, `USpaceHudShipStatus` | `SpaceFlightHud.*` | Displeje v kokpitu: dva MFD a střední sloupek (radar, self status), rozvržení plátna (`ScreenRect`), kontakty radaru (`MakeRadarContacts`). |
| `UCockpitDisplayComponent` | `CockpitDisplayComponent.*` | Kreslí `USpaceCockpitDisplays` do render targetu na slot `*_Screens`, světla displejů, `space.CockpitCentre`, `stat SpaceCockpit`. |
| `USpaceShotRunner` | `SpaceShotRunner.*` | Snímky podle scénáře pro vizuální kontrolu (kapitola 9): `-ShotList=` z příkazové řádky, `space.Shot` a `space.Shots` v konzoli. |
| `ASpaceDebugHUD` | `SpaceDebugHUD.*` | Textový debug HUD (CVar `space.Hud`), FPS; vytváří `USpaceFlightHud`. Anglicky, placeholder, zbytek nahradí SC-3. |
| `USpaceOriginRebasingSubsystem` | `SpaceOriginRebasingSubsystem.*` | Posun počátku světa. |
| `ASpaceGravityVolume`, `ASpaceSlidingDoor` | `SpaceInterior.*` | Interiér lodi: umělá gravitace (box), posuvné dveře, `space.Interior`, `space.Walk`, `space.Door` (bod 62). Vstup do interiéru dělá `ASpacePlayerController::ToggleInterior` (klávesa I). |
| – (jen konzolové příkazy) | `SpaceInteriorTuning.cpp` | Ladění interiéru za běhu: `space.Kit`, `space.KitColor`, `space.KitLight`, `space.KitReset` (bod 59). |
| – (jen konzolové příkazy) | `SpacePostTuning.cpp` | Ladění vzhledu za běhu přes reflexi: `space.Post`, `space.PostList`, `space.PostDump`, `space.Sun`, `space.SunDir`, `space.Sky`, `space.LightList` (WORKFLOW kapitola 11). |

### Obsah (`Content/`)
- `Maps/MainMenu` (úvodní obrazovka) a `Maps/TestSpace` (hra, start editoru).
- `Ships/Vanguard/…` (mesh, BP_Ship_Vanguard, materiály), `Ships/Shared/Materials` (mastery),
  `Ships/Audio` (zvuky lodi).
- `Environments/Space` (materiály oblohy, těles a prachu), `Planets` (terén).
- `Input` (IA a IMC), `UI/Audio` (zvuky menu), `Characters/Mannequins` (Manny),
  `Blueprints/BP_SpaceGameMode`.
- Každý asset je vytvořený skriptem. Zdroj pravdy jsou skripty v `Tools/Assets`, ne ruční úpravy.

### Nástroje (`Tools/`)

| Skript | K čemu |
| --- | --- |
| `run_editor_python.ps1` | Spouští Python headless v editoru. |
| `Package.ps1`, `Play.ps1` | Build hry a spuštění. |
| `Assets/build_space_scene.py` | TestSpace: obloha, planeta, tělesa, prach, materiály, světla a grade (`SKY_LIGHT_INTENSITY`, `POST_SETTINGS`). |
| `Blender/bake_ship_ao.py` | Dopeče `T_Ship_<Loď>_AO.png` pro už postavenou loď (okluze v pečených texturách není, viz bod 38). |
| `Assets/generate_decals.py` | Kreslí nápisy a výstražné pruhy do `ArtSource/Ships/Shared/Decals` (bod 39). |
| `Assets/generate_panel_lines.py` | Kreslí dlaždicový list panelových spár `T_Ship_Panels.png` (bod 40). |
| `Assets/build_main_menu.py` | Level úvodní obrazovky. |
| `Assets/import_ship.py` + `ship_materials.py` | Import lodi z Blenderu. |
| `Assets/generate_ship_sounds.py` → `build_ship_audio.py` | Generátor zvuků (numpy) a jejich import. |
| `Assets/generate_detail_textures.py` | Dlaždicová mikro-normála a skvrny opotřebení pro detailní vrstvu trupu (numpy, bezešvé). |
| `Assets/add_*_input.py` | Přidávání mapování kláves (pouze append). |
| `Content/UI/Fonts/` | Fonty HUD (Rajdhani, Share Tech Mono) i s licencemi SIL OFL. Načítají se ze souboru, ne jako Font asset: importér fontu potřebuje Slate aplikaci, kterou headless editor nemá. Do balíčku je dostává `DirectoriesToAlwaysStageAsUFS` v `Config/DefaultGame.ini`. |
| `Assets/install_mannequin_pack.py`, `generate_milky_way_glow.py` | Jednorázová instalace a textura. |
| `Blender/gamespace_ship_export.py` | Export lodí z Blenderu (FBX, manifest, validace). |
| `Blender/fit_ship_interior.py` | Najde měřítko a polohu AI interiéru v kabině a oko pilota (uvnitř trupu, okraj u stěn, čistý výhled, deska pod HUD). Výsledek do receptu (`interior.placement`, `sockets.Cockpit`) a setupu. |
| `Blender/build_ai_ship.py` | AI model (Meshy, Higgsfield) → herní `.blend` podle receptu `<Loď>_ai_build.json`: orientace, velikost, díly, decimace, nové UV a přepečené textury, emisivní trysky, UCX hully, sockety. Kapitola 2B v `ShipPipeline.md`. |
| `Blender/split_ship_gear.py` | Oddělí vymodelovaný podvozek z trupu do dílu `SM_Ship_<Loď>_Gear` (volné díly pod břichem u socketů `SOCKET_Gear_*`, kromě dvířek a světla) a uloží `.blend`. Jednorázové, druhé spuštění nic nedělá. Pak export a import jako obvykle. |
| `Assets/add_landing_input.py` | Klávesy N (`IA_LandingGear`) a P (`IA_Precision`) do `IMC_Spaceship` (jen přidává). |
| Blender MCP (`blender` v Claude Code) | Živý Blender: snímky viewportu, spouštění Pythonu ve scéně. Blender spustit s GUI a otevřít .blend; doplněk `blender_mcp_addon` sám poslouchá na `localhost:9876`. Pro modely a materiály: iterovat ve viewportu, teprve pak export do Unrealu. |
| `Blender/cockpit_view_survey.py` | Změří, co pilot vidí: paprsky přes zorné pole proti skutečnému modelu, kolik % výhledu je volných a co ho blokuje. Po změně modelu nebo pozice kamery. |
| `Shots.ps1` + `Shots/*.json` | Snímky ze zabalené hry podle scénáře (kapitola 9). |
| `Content/Python/gamespace_assets.py` | Knihovna pro skriptové vytváření IA, IMC a dalších assetů. |

### Dokumentace
- `README.md`: podrobný technický popis systémů (anglicky).
- `Docs/Ships/ShipPipeline.md`: pipeline lodí (česky).
- `Docs/Characters/CharacterPipeline.md`: pipeline postav (česky).
- `Docs/HANDOFF.md`: tento dokument.
- `Docs/WORKFLOW.md`: postup práce krok za krokem, Blender MCP, úplný seznam nástrah (česky).

---

## 7. Ovládání (aktuální)

**Loď:**

| Akce | Klávesa |
| --- | --- |
| Dopředu / dozadu (coupled: držet = letět, pustit = brzdit) | W / S |
| Strafe | A / D |
| Nahoru / dolů | Space / Ctrl |
| Roll | Q / E |
| Směr (virtuální joystick, kurzor zůstává) | myš |
| Boost (manévrovací trysky a rotace, vypíná G-Safe) | Shift |
| Afterburner (jen SCM) | Tab (s W) |
| Coupled / decoupled | V |
| Spacebrake (držet) | X |
| Omezovač rychlosti | kolečko |
| SCM / NAV | B |
| G-Safe / ComStab | K / L |
| Quantum skok (jen v NAV, nos na tělese, READY) | držet levé tlačítko myši |
| Kamera chase / kokpit | C |
| Zoom | Alt + kolečko |
| Free look | pravé tlačítko |
| Podvozek (vysunutí zapne i precision) | N |
| Precision mode | P |
| VTOL (jen SCM) | G |
| Stránky MFD (levý / pravý, s Alt zpět) | F1 / F2 |
| Přiblížení na displeje (držet) | Z / prostřední tlačítko myši |
| Vystoupit (jen když LANDED) | F |

**Postava:** WASD, myš, Space skok, Shift sprint, F nastoupit, **V první / třetí osoba** (výchozí první).

**Globální:** Escape (F10) menu a pauza, H HUD (kompaktní / plný / skrytý), **I** interiér Steadfastu
(tam a zpátky; totéž tlačítko v menu pauzy).

---

## 8. Testy

Všechny jsou headless (`.\Tools\run_editor_python.ps1 Tools\Tests\<soubor>`). Každý tiskne
`… SUMMARY OK/FAILED`. K 18. 9. 2026 **všechny prochází**.

| Test | Pokrývá |
| --- | --- |
| `test_planet_l3.py` | Terén, LOD, atmosféra, gravitace, pád, entry heat. |
| `test_landing_l5.py` | Sklon, pravidla dosednutí, tření, zarovnání, cena warm-upu kolizí. |
| `test_character_l6.py` | Input assety postavy, gravity frame, výstup, animace, foot IK. |
| `test_free_look.py` | Free look (neomezený yaw, návrat). |
| `test_ship_import.py` | Importovaná loď: meshe, kolize, sockety, materiály, všechny hodnoty ze setup JSON (s `GAMESPACE_SHIP_MANIFEST`). |
| `test_ifcs_sc1.py` | SC-1a: limity trysek podle směru, coupled brzdění, decoupled, omezovač, spacebrake, SCM/NAV, setrvačnost rotace, G-Safe, ComStab, virtuální joystick, input assety, hodnoty Vanguardu. |
| `test_flight_hud_sc1c.py` | HUD (logika SC-1c v rozložení podle současného SC): všechny prvky reference, pásky (kurz přes 360, výška), žebřík (poloha čar podle FOV a náklonu), odznaky jen zapnuté, bez tělesa bez kurzu a výšek, rychlost vůči omezovači, afterburner, pozpátku, kontrolky, G a limit G-Safe, strafe, joystick. Vzhled headless ověřit nejde. |
| `test_boost_afterburner_sc1b.py` | SC-1b: boost jen manévrovací trysky a rotace, vypnutí G-Safe, afterburner (tah, limit × omezovač, palivo, zamčení, doplňování, plynulý návrat, coupled i decoupled, jen SCM, G-Safe zůstává), Shift + Tab, input a hodnoty Vanguardu. |
| `test_flight_modes.py` | Boost energie, výstup, kolize lodi, záchrana postavy, tělesa, zvuky. |
| `test_cockpit_displays.py` | Displeje v kokpitu: dvě obrazovky (FLIGHT, SYSTEMS) se všemi přístroji a velkým písmem, stejné hodnoty jako HUD pro stejnou loď, komponenta na lodi, slot `M_Ship_Vanguard_Screens` v interiéru s unlit `MI_Ship_Vanguard_Screens`. Stránky MFD (přepínání, obtékání, titulek a záložka, obsah seznamů a tahu, klávesy F1/F2 a [ ] bez kolizí, ladicí zobrazení enginu z F1/F2 odebrané). Střední sloupek: RADAR a SELF STATUS, `texture_rect` v receptu = `ScreenRect` v kódu, poměr stran jako sklo, radar vidí objekt v dosahu přesně tam, kde je (a ten mimo dosah ne), těleso jako směr, planeta pod lodí bez směru, silueta z 10 hullů Vanguardu, 4 motory, 3 nohy, 4 sockety `Display_*`. Jak vypadají: `-Preset cockpit` a `cockpit_centre`. |
| `test_cockpit_frame.py` | Kokpit: Vanguard má interiér (díl, oko nad vanou za deskou, deska 7–13° pod okem jako v SC referenci, pilot ≥ 1,2 m od desky, provizorium vypnuté); rozložení provizorního rámu pro lodě bez interiéru (nic v okně HUD, deska 14–20° pod horizontem, sloupky 24–34° do stran, sedadlo za okem). |
| `test_landing_sc2.py` | SC-2a: dosednutí jen s podvozkem (GEAR UP před vším ostatním, mezera pod patkami), stavový automat podvozku (časy, otočení v půlce, zákaz zasunutí na zemi), pohyb modelovaného dílu i zástupných nohou, precision (strop, omezovač uvnitř, jen SCM, bez afterburneru, pomalejší otáčení, brzdění bez skoku), kontrolky GEAR/PREC, klávesy N/P bez kolizí, hodnoty a díl `Gear` Vanguardu, scénář `landing`. |
| `test_vtol_sc2b.py` | SC-2b: VTOL jen v SCM (v NAV odmítnutý a shozený), přechod trvá svůj čas, hlavní tah / zvedací a boční trysky podle násobků, strop rychlosti a stoupavost Space/Ctrl, odmítnutý afterburner, auto-srovnání (`ComputeVtolLevelStep` proti zadanému „nahoru“), visení čte jako práce motorů, odznak VTOL na HUD, klávesa G bez kolize, scénář snímků. |
| `test_flight_hud_sc3.py` | SC-3: značka dráhy letu – nic pod 5 m/s, střed při letu po ose pohledu, správná strana a velikost odchylky podle ohniskové délky, přilepení na kruh, čárkovaná značka za nosem, scénář snímků. |
| `test_menu_settings.py` | Třída nastavení, herní režimy a controller, config cookování, level MainMenu, zvuky UI, orientace při výstupu. |
| `test_quantum_sc4.py` | SC-4: nic v SCM; v NAV cíl podle nosu, Veyra ze startu TOO CLOSE; spool, kalibrace, READY, krátký stisk neskočí, podržení ano; spálené palivo podle vzdálenosti; ve skoku nejde řídit; příjezd na výšku příletu v rychlosti NAV do minuty; chlazení; B přeruší skok; OBSTRUCTED s planetou v cestě; NO QT FUEL; kalibrace padá, když nos uhne; HUD (rámeček, oblouky 0/1/2/3, cíl); LMB namapované, J ne; scénář snímků. Plus profil rychlosti, výška příletu, palivo a test úsečka–koule samostatně. |
| `test_speed_tunnel.py` | Tunel quantum skoku: prach je pryč, než by ho rychlost rozblikala; čára delší než dvojnásobek posunu za snímek při 60 FPS (neblikne); čáry v dráze do sebe nenarazí; stěny od nejbližší, loď Vanguard se vejde do nejbližší; materiál aditivní, oboustranný, se všemi parametry, které komponenta nastavuje; jiskry u lodi (bodů na trupu ≥ 32, ve skoku mnohem víc než v letu), prachu jen pár set; scénář snímků se skokem (`quantum`). |
| `test_scene_look.py` | Vzhled uložené úrovně proti receptu: atmosféra Veyry (jediná, ve středu planety, zem 2 km pod hladinou, koeficienty z receptu, tenký lem, slunce ji osvětluje), intenzita sky lightu, contact shadows a šířka slunce, všechna nastavení `POST_SETTINGS` v neohraničeném volume (a že chromatická aberace a vyvážení bílé zůstala vypnutá), lak trupu z `Vanguard_setup.json`. Chytá zapomenuté spuštění `build_space_scene.py` / `import_ship.py`. |
| `test_interior.py` | Interiér Steadfastu po `import_interior.py` (od bodu 62 i kokpit, sklo bez Nanite s průsvitným oboustranným materiálem, posuvné dveře s křídly zavřenými uprostřed, gravitační box, start chůze a kolize podle polygonů u každé místnosti): `M_KitTrim` má usage flagy Nanite/static/instanced a každý sampler výchozí texturu (jinak šachovnice v buildu), parametry `Lift`, `MetallicScale`, `Roughness*`, `Gunmetal` s hodnotami ze skriptu, jeden otagovaný herec na místnost, všechny sloty na instancích `M_KitTrim`, svítidla v každé místnosti na `MI_KitLamp`, bodovka pod každým svítidlem z `Interior_lights.json` (míří dolů; lm, K, kužel) a všechny akcenty (lm). |
| `Tools/Assets/tests/*`, `Tools/Blender/tests/*` | Čistý Python bez Unrealu: plán importu, manifest (`python <soubor>`). |

Co headless **nejde** ověřit a musí vyzkoušet autor ve hře:
- vzhled (obloha, jas, rámování úvodní obrazovky) – čísla hlídá `test_scene_look.py`, jak to vypadá jen snímky (kapitola 9);
- zvuk;
- chování Slate menu;
- skutečné kolize (v commandletu nefungují traces ani sweepy).

---

## 9. Vizuální kontrola snímky (workflow, 17. 9. 2026)

**Claude Code se umí dívat na obrázky ze souboru, ale neumí si sám udělat screenshot běžící hry.**
Tahle kapitola popisuje, jak si ho udělá skriptem a sám si ho pak prohlédne. Cíl: po každé vizuální
změně (kamera, HUD, model, terén) ověří výsledek dřív, než autorovi řekne, že je hotovo.

### Jak to spustit

```
.\Tools\Shots.ps1 -Preset cockpit            # sada snímků podle scénáře
.\Tools\Shots.ps1 -Preset hud -Package       # nejdřív zabalí hru, pak fotí
.\Tools\Shots.ps1 -Last                      # vypíše nejnovější sadu
```

Skript spustí **zabalenou hru** (ne editor) v okně 1600 × 900, ta si sama načte TestSpace, projde
scénář, u každého snímku nastaví loď a kameru, počká, vyfotí a nakonec se ukončí. Trvá to pár
desítek sekund a hra má po tu dobu okno v popředí, takže se mezitím nemá psát.

- Proč zabalená hra: cooked materiály se vykreslují správně (uncooked `-game` je šedý) a editor
  autorovi nekrade myš a klávesnici.
- Snímky obsahují i HUD (Slate a UMG).

### Kam se ukládají

`Saved\Shots\<RRRRMMDD_HHMMSS>_<scénář>\NN_<název>.png` – číslo je pořadí ve scénáři, takže je
poznat, co je co, a nejnovější složka je ta s nejvyšším časem. `Saved/` **není v gitu**: snímky jsou
pracovní materiál. Když má nějaký zachytit stav pro historii (před/po u vzhledu), přidá se
`-Keep` a kopie jde do `Docs\Shots\<scénář>\<čas>\`, což v gitu je.

### Scénáře (`Tools\Shots\*.json`)

> **Aktuální a úplný seznam scénářů je v `Docs/WORKFLOW.md`, kapitola 6.** Nedrž ho na dvou
> místech – tenhle seznam se přestal ručně udržovat 21. 9. 2026, aby nešel z synchronizace.

Scénář je JSON a **čte se z disku za běhu**, takže úprava scénáře nevyžaduje nové zabalení hry.
Pole jednoho snímku: `name`, `camera` (`cockpit`/`chase`), `hud` (0/1/2), `altitude_m`, `facing`
(`horizon`/`planet`/`away`), `speed_ms`, `mode` (`SCM`/`NAV`), `limiter`, `coupled`, `gsafe`,
`comstab`, `boost`, `afterburner`, `stick` (kurzor VJoy), `settle` (sekundy na ustálení),
`cockpit_eye`, `hide_hull`, `hide_canopy`, `cockpit_light` [cd, cd], `display_light`, `interior_tint` (pro ladění kokpitu bez reimportu lodi), `console` (seznam konzolových příkazů před snímkem, pro srovnání nastavení), `gear` (podvozek
hned dole / nahoře), `lower_gear` (začne vysouvat, krátký `settle` ho chytí v půlce), `precision`,
`chase_yaw`, `chase_pitch` (> 0 = zespodu), `chase_zoom` (kamera otočená kolem lodi), `drift` [vpřed, vpravo, nahoru] v m/s (rychlost v osách lodi místo `speed_ms`, pro značku dráhy letu). Nízká
`altitude_m` s podvozkem a pár sekund `settle` loď opravdu posadí na zem.

**Volná kamera** (23. 9. 2026, pro interiéry a statické scény): `camera: "free"` s `camera_location`
a `camera_look_at` v **metrech** (svět je v cm, skript čísla násobí stem), `fov` a `exposure`.
`exposure` zafixuje automatiku (min = max jas); bez něj kamera dál adaptuje, takže ztmavení
materiálu se na snímku neprojeví – oko se prostě víc otevře. Pro nákladový prostor sedí 2,0.

### Jednotlivý snímek při hraní

V konzoli hry (`~`):

```
space.Shot nazev            # jeden snímek aktuálního pohledu do Saved\Shots\manual
space.Shots <cesta.json>    # projede celý scénář odsud
```

### Jak to používá Claude Code

1. Udělá vizuální změnu, zabalí hru (`Tools\Shots.ps1 -Preset <scénář> -Package`).
2. Prohlédne si snímky (čte je jako obrázky ze souboru) a podle nich rozhodne, jestli výsledek sedí.
3. Když ne, upraví hodnoty a fotí znovu. U kokpitu a podobných voleb si napřed udělá **porovnávací
   scénář** (jako `cockpit_tune`) a vybere variantu podle obrázků, ne odhadem.
4. Autorovi pak napíše, co na snímcích viděl, a **výslovně oddělí, co musí posoudit sám**: pocit
   z ovládání, plynulost, zvuk, čitelnost za pohybu, cokoli, co statický snímek neukáže.

Omezení, se kterými je potřeba počítat:
- Snímek je statický: nepozná se z něj plynulost, pocit z myši ani zvuk.
- Scénář umí jen to, co má v polích. Přistání už jde (scénář `landing`), výstup z lodi a menu zatím ne.
- Ve snímcích s otočenou kamerou (`chase_yaw`) je nahoře nápis FREE LOOK – kamera jede přes free look.
- Hra fotí to, co je zabalené. Po změně C++ nebo obsahu je potřeba `-Package`, jinak snímky ukazují
  starý build; skript na to upozorní.

---

## 10. Roadmapa – letový systém podle Star Citizen (rozdělit do kroků)

Autor chce **kompletní kopii SC pilotování**, ale ne v jednom kroku. Níže je navržené rozdělení.
**Před začátkem každé fáze** ho potvrď s autorem a zkontroluj master referenci. Každá fáze má
končit hratelným buildem, testy a scénářem.

Dnešní systém (FA on/off, páka, boost) je mezikrok; cruise J už nahradil quantum drive (SC-4). Části se převezmou (per-axis limity
trysek, environment, přistání), jiné se nahradí (J cruise → quantum travel, páka → SC throttle
a speed limiter).

- **SC-1 – IFCS jádro a master modes**, rozdělené na dva kroky:
  - **SC-1a (hotovo, 17. 9. 2026, čeká na autorův test):** SCM/NAV, coupled/decoupled podle SC,
    omezovač na kolečku, W/S jako cílová rychlost, trysky podle směru a setrvačnost rotace,
    G-Safe, ComStab, spacebrake, myš jako VJoy s kruhem. Hmotnost lodi zatím není samostatný
    parametr: tah je rovnou zadaný jako zrychlení (stejně ho uvádí SC).
  - **SC-1b (hotovo, 17. 9. 2026, čeká na autorův test):** boost (manévrovací trysky a rotace,
    vypíná G-Safe) a afterburner (hlavní tah, vlastní palivo, rychlost relativní k omezovači, jen
    SCM, G-Safe nechává zapnutý).
  - **SC-1c (hotovo, 17. 9. 2026, čeká na autorův test, rozsah potvrzený autorem):** HUD jen pro mechaniky SC-1a/1b podle
    `Docs/UI/` (kapitola 3): svislý pruh rychlosti vůči omezovači, G-metr, indikátory CPLD, GSAF,
    COMSTAB, BOOST a SCM/NAV, pruhy energie boostu a paliva afterburneru, kurzor virtuálního
    joysticku.
  - Ladění hodnot (G, rychlosti, citlivost VJoy) podle autorova hraní.
- **SC-2 – Přistání SC stylem**, rozdělené na dva kroky (potvrzeno autorem 18. 9. 2026):
  - **SC-2a (hotovo, 18. 9. 2026, čeká na autorův test):** podvozek (N) jako podmínka dosednutí,
    vizuál z modelovaných noh Vanguardu, precision mode (s podvozkem nebo P), kontrolky GEAR a PREC.
  - **SC-2b (hotovo, 20. 9. 2026, čeká na autorův test):** VTOL (G, jen SCM, přechod 1,5 s): hlavní tah
    35 %, strop 60 m/s, svislé trysky ×1,5 a boční ×1,3, Space/Ctrl na stoupavost 15 m/s, auto-srovnání
    na horizont, afterburner a cruise odmítnuté, odznak VTOL na HUD i MFD. Visení už je vidět na
    tryskách (`HoverThrustReferenceG`). Bod 43.
- **SC-3 – zbytek HUD a MFD** (začato 20. 9. 2026: značka dráhy letu, bod 44; VTOL a GEAR už jsou): VTOL a GEAR (po SC-2), ESP a LOCK (až budou zbraně), velocity
  vector, MFD panely, celková přestavba na UMG a náhrada anglického debug HUD.
- **SC-4 – Quantum travel** (hotovo 21. 9. 2026, bod 47): cíl nosem, spool + kalibrace v NAV, READY,
  skok na podržení LMB, tunel s mlhou, příjezd, chlazení, blokace, palivo. Zbývá: mapa systému (F2),
  jiskry z trupu, doplňování paliva, interdikce; měřítko systému je zatím naše (stovky km).
- **SC-5 – Pocit z přetížení:** blackout a redout, dýchání pilota, reakce kamery a zvuku na G.
- **SC-6 – Systémy lodi:** power triangle, ESP (až budou zbraně a štíty).

Další otevřené směry mimo let:
- druhá planeta, stanice nebo POI;
- skutečné zvuky místo procedurálních;
- interiér kokpitu, animace nastupování;
- skutečný HUD a UI;
- těžba a ekonomika (podle SpaceEnvironment reference).

---

## 11. Známé problémy a neověřené věci

- **Hřebenový terén (`RidgedOctaves`) vypnutý** (22. 9. 2026, bod 52): s ním byla kamera po přistání pod
  vykreslenou zemí a u okraje Veyry díry v terénu. Podezření: odhad výšky uvnitř dlaždice
  (`HeightVariationWithinTileCm`) pro hřebenové oktávy nesedí, dlaždice se dělí pozdě a geomorph
  jde k rodiči, který je daleko od skutečné země. Neověřeno.
- **Kameny nemají kolizi** (bod 52): loď i postava jimi projdou.
- **Stěny tunelu nejsou tak „mléčné“ jako v referenci** (bod 56): reference má širší měkké světelné
  klíny přes celý obraz, naše jsou užší a tmavší. Neověřeno autorem.
- **Černé čáry kolem jisker za letu** (bod 56, autor 22. 9. 2026, po opravách zbývá): u rychlých
  tenkých jisker se objevují tmavé „stíny“ podél nich. Není to materiál (je aditivní, zápornou barvu
  vrátit neumí) ani mlha – je to TSR: historie se u rychlé tenké jasné čáry přestřelí a vedle ní
  vznikne záporný ghost. `enable_responsive_aa` to přesouvá jinam (černé škrábance na světlém pozadí).
  Zkusit: menší kontrast jisker, `r.TSR.ShadingRejection.*`, nebo jiskry kreslit do vlastního průchodu.
  Autor to zatím nechal být.
- **Ohony jisker jsou dál místy tečkované** (bod 55): nejrychlejší a nejvzdálenější kusy dráhy
  TSR pořád neudrží celé. Čte se to jako jiskření, ale v referenci jsou vlásky celé.

- **Neověřeno autorem (21. 9. 2026):** quantum drive (bod 47) – jen z testů a snímků. Hlavně jak
  sedí časy (spool 6 s, kalibrace 2,5 s, podržení 0,6 s, chlazení 10 s), jak čáry tečou v pohybu
  a jestli je mlha v tunelu dost/moc hustá (po bodu 48: tmavý střed, světlé stěny). Cruise (J) už není.
  Jiskry kolem lodi a bílé čáry v letu (bod 48) jsou zatím jen ze snímků.

- **Neověřeno autorem:** celý SC-1c, hlavně vzhled (rozmístění, čitelnost na světlém pozadí,
  velikost na jiném rozlišení než 1080p), a nová pozice kamery v kokpitu (C). SC-1a a SC-1b autor otestoval a fungují; hodnoty se
  budou dál ladit. Dříve:
  celý SC-1a (pocit letu, hodnoty G a rychlostí, VJoy kruh, Alt +
  kolečko, přistávání s novým coupled režimem). Headless testy prochází.
- **Zjištěno autorem v buildu (17. 9. 2026):**
  - *Opraveno, čeká na autorův test:* po výstupu z lodi stála postava skoro v trupu a kamera byla
    přiblížená. Příčiny: `SOCKET_Exit` Vanguardu je jen 2 cm od kolizního hullu břicha (`UCX_08`)
    a kořenový box lodi blokoval kanál kamery, takže se boom postavy stáhl k hlavě. Místo výstupu se
    teď posune do strany na `ExitClearanceCm` od kolizních tvarů (`GetHullClearance`, čistá
    geometrie) a box kameru ignoruje.
  - *Opraveno, čeká na autorův test:* grafika „se neměnila“. Engine hlásí úroveň kvality −1
    („vlastní“), jakmile škálování rozlišení není výchozí pro danou úroveň. Menu pak vždy ukázalo
    „Vysoká“ a další POUŽÍT uložilo zpět Vysokou. Menu teď čte `GetGraphicsQualityLevel()`.
  - obloha pořád působí jako tapeta (řeší se v dalších krocích).
- **Zvuky jsou procedurální placeholdery** z numpy a nikdo je zatím neslyšel. Ladění podle
  autorovy zpětné vazby. Hlasitosti jsou v nastavení a v `ASpaceshipPawn` (`EngineHumVolume`,
  `EngineVolume`, `BoostVolume`, `CruiseVolume`, `OneShotVolume`).
- **Jas oblohy** (slunce, mlhoviny) je nastavený odhadem. Ladí se v levelu na `StarfieldSky`
  (`NebulaScale`, `SunScale`) nebo v konstantách `build_space_scene.py`.
- ~~**Vznášení v atmosféře bez zpětné vazby**~~ (autor 17. 9. 2026) – vyřešeno 20. 9. 2026 v SC-2b
  (bod 43): `EngineDemand` měřil svislou osu proti plné kapacitě zvedacích trysek, takže visení na
  Veyře (0,46 G z možných 5,5) dávalo 0,06 a trysky ani zvuk se nehnuly. Teď se měří proti jednomu G
  tahu (`HoverThrustReferenceG`).
- **Meshy Vanguard, kokpit** (tmavý interiér a displeje od 18. 9. 2026, bod 23): z oka (174, 0, 189)
  jdou z horních rohů k desce sloupky rámu canopy. Při rozhlížení do stran (free look ~70°) je 0,9–2 m
  od oka kořen křídla trupu v hrubém rozlišení – boční stěny kabiny jsou zevnitř průhledné (jednostranný
  trup) a oko teď sedí vzadu vedle křídla. Není sedadlo. Dva malé čtverce uprostřed desky jsou od
  19. 9. 2026 displeje (radar, self status; bod 31). Render target nemá mipmapy: na menším rozlišení než
  1600 px může písmo na displejích zrnit; rychle se měnící čísla při zrychlení lehce „duchují“ (TSR).
  Oko je navržené pro 16:9 a FOV 88°.
- **Meshy Vanguard na dunách:** na snímku `landing/06_landed_side` (18. 9. 2026) leží loď na hřbetu
  duny a spodní gondola je zapuštěná ~0,5 m v písku, i když by kolizní box (spodek = podrážky ližin)
  neměl dovolit nic níž než ližiny. Neověřená podezření: hrubší kolizní síť planety než vykreslený
  terén, nebo naklonění při srovnání na průměrný svah (loď je 11,4 m široká). U staré úzké lodi to
  nebylo vidět. K řešení v dalším kroku (dotyk se zemí z UCX hullů / výšky terénu pod rohy).
- **Střední sloupek (bod 31), neověřeno autorem:** čitelnost na jiném rozlišení než 1600 px, pocit z radaru
  za letu. Radar zatím nikdy neviděl kontakt ve hře (v TestSpace ve snímcích žádný nebyl v 5 km); jeho
  poloha je ověřená jen headless testem. Kontakty se obnovují 5× za sekundu, rychlý objekt proto na radaru
  skáče. Silueta SELF STATUS je z kolizních hullů – hranatá, ne přesný obrys modelu.
- **Stránky MFD (bod 32), neověřeno autorem:** přepínání F1/F2 ve hře (headless test ověřuje mapování, ne
  stisk). Popisky na SELF STATUS
  (STATE, GEAR…) jsou malé. Stránky mají jen to, co hra umí; SC stránky zbraní, štítů a energie přijdou se
  systémy. Stránky se zatím nedají přepnout myší jako v SC (režim interakce, klik na displej).
- **Detail lodi (bod 33), neověřeno autorem:** jak to vypadá za letu a na jeho monitoru. Detailní vrstva
  nezostří samotnou kresbu (panely, nápisy) – ta je v AI textuře a ostřejší bude až s lepším modelem nebo
  decaly. Trup s 1 mil. trojúhelníků dělá z FBX 93 MB v Git LFS; u dalších lodí zvaž, jestli to stojí za to.
- **Úvodní obrazovka s novou lodí není vyfocená** (snímky menu neumí); kamera zůstala z 17,6m lodi.
- **SC-2a, loď na břiše bez podvozku „visí“ nad zemí** (snímek `landing/05_belly_gear_up`; u Meshy
  Vanguardu 0,55 m vzadu a 1,1 m vpředu).
  Kolizní box lodi (root, podle něj se loď pohybuje) končí u patek podvozku. Se zasunutým podvozkem
  tedy loď u země stojí na neviditelném boxu. Nastane to jen, když pilot ignoruje GEAR UP. Oprava
  by znamenala zmenšit box k břichu (−1,5 m), jenže box je symetrický kolem středu lodi, takže by
  se zmenšil i nahoře a kýlovky by mohly zajet do terénu nebo asteroidu. Dáme ji, až bude jasné,
  jestli to autorovi vadí.
- **SC-2a, G-metr po přistání** ukazuje poslední hodnotu z letu (~0,5 G), protože v `Landed` se
  `GForce` nepřepočítává. Kosmetické, doladí se se SC-2b.
- **V BP_Ship_Vanguard zůstaly hodnoty zástupných noh** (`gear_strut_radius_cm` 11,
  `gear_pad_radius_cm` 32, `gear_pad_thickness_cm` 12) z prvního pokusu s válci. Nevadí to: Vanguard má
  modelovaný díl `Gear` a zástupné nohy nestaví (kapitola 12, BP override zůstává).
- **Kokpit starého Vanguardu** (do 18. 9. 2026): sklo canopy se pilotovi skrývalo a oko bylo na
  (500, 0, 110) nad přídí. Nový model je popsaný výš („kokpit bez lodi“).
- **V PIE Escape ukončí hru** (je to zkratka editoru). V PIE otevírá menu **F10**, v buildu Escape.
- Debug HUD je anglicky, menu česky.
- Build je **Development** (má konzoli `~`). Shipping zatím nebyl zkoušený.
- `IMC_Spaceship` a `IMC_Character` pořád mapují H na `IA_ToggleHud`. Nic na to není navázané
  (H obsluhuje controller), je to neškodné.
- Obloha nerozlišuje denní a noční stranu planety: v atmosféře je modrá všude.
- **Interiér Steadfastu (body 58–63), neověřeno autorem:** jak se v něm chodí a jak působí za pohybu,
  výška stropu a kamera za postavou v úzké chodbě (kamera se o stěny zkracuje). Kokpit (bod 63) je
  první verze podle reference: sedadla a konzole jsou hranaté, obrazovky jsou jednobarevné plochy bez
  obsahu (napojení na displeje lodi přijde s laděním). Na tenkých hranách příhradových sloupů ve
  strojovně zůstává drobné mihotání odlesků (0,06 % pixelů). Interiér stojí v prostoru sám, bez
  trupu lodi; z lodi k němu nevede nástup (jen klávesa I).

---

## 12. Technické pasti (ušetří hodiny)

> Úplný a novější seznam (vykreslování, displeje, Blender MCP, unity build…) je v
> `Docs/WORKFLOW.md`, kapitola 9. Tady zůstávají ty nejstarší.

- **Cookování:** C++ načítá assety podle cesty (`StaticLoadObject`). Cooker je nevidí, a proto
  jsou složky v `Config/DefaultGame.ini` pod `DirectoriesToAlwaysCook`. Nový assetový adresář
  načítaný podle cesty tam přidej. `Package.ps1` klíčové assety po buildu kontroluje.
- **Python v UE:**
  - `unreal.Rotator(a, b, c)` má poziční pořadí **roll, pitch, yaw**, vždy používej keyword
    argumenty.
  - Struct wrappery neberou keyword argumenty v konstruktoru.
  - Vlastnosti, které jsou jen `Config` a nemají `BlueprintReadOnly` nebo `Edit`, nejsou z
    Pythonu vidět.
- **Commandlet:**
  - traces a sweepy nikdy nezasáhnou;
  - animace potřebuje `++GFrameCounter`;
  - shadery se nekompilují, chyby HLSL se ukážou až při cookování nebo v editoru.
- **Nativní třídy:** hodnoty z CDO se do instancí nekopírují, assety načítej v konstruktoru
  (`ConstructorHelpers`).
- **Pohyb pawnu sweepuje jen root komponentu.** `HullCollision` (box) je proto root a ignoruje
  pawny. Postava koliduje s `Hull` (UCX hully).
- **Blueprint override zůstává uložený:** když se hodnota ze `_setup.json` odebere, v BP zůstane
  stará. Je potřeba ji nastavit explicitně.
- **Neočekávané uncooked chování:** `-game` bez zabalení vykresluje nové materiály šedě. Vzhled
  posuzuj v PIE nebo v zabaleném buildu.
- **Nástroje:** v Bash heredocu dělají potíže apostrofy. Python skripty pro úpravy kódu piš přes
  nástroj Write do scratchpadu a spouštěj je PowerShellem.

---

## 13. Poslední commity

Viz `git log --oneline`. Poslední kroky:
- `73b1410`: letové režimy, cruise, vrstvený zvuk, živá obloha, opravy výstupu a kokpitu;
- `77b26d6`: hratelný build (úvodní obrazovka, pauza, nastavení, H, cookování, zvuky UI) a handoff;
- následující commity: SC-1a, SC-1b, SC-1c (jádro IFCS, boost a afterburner, HUD);
- SC-2a: podvozek (N) a precision mode (P), podvozek Vanguardu jako samostatný díl.
- `8367595`–`a998767`: Meshy Vanguard z receptu, kokpitový interiér z Meshy;
- `1253827`: tmavý kokpit, živé displeje s HUD na desce, oko posunuté dozadu jako v SC;
- `b4ae34a`: displeje svítí do kokpitu, tmavý rám canopy;
- `6a4e43b`: letový HUD rozložený jako v současném SC;
- `d3cadc3`–`ca16a32`: široké MFD, vlastní písmo, ostré displeje v letu (interiér bez Nanite);
- `440c31b`–`d287603`: MFD ve stylu SC, čísla 5 Hz, displeje napasované do rámečků přes Blender MCP;
- `42a1ff5`, `2380850`: výchozí jen letový HUD, ustálená čísla MFD, jemnější prach, kovový rám;
- dokumentace workflow a nástrah (`Docs/WORKFLOW.md`), pomocné skripty Blender MCP v `Tools/Blender/mcp/`;
- střední sloupek desky: RADAR a SELF STATUS (bod 31), kreslení čar bez kvadratického dávkování ve Slate;
- stránky MFD na F1 a F2 (bod 32);
- rychlejší kreslení displejů (trvalé okno) a seskupené čáry HUD (bod 33);
- detailní vrstva materiálu a trup 1 mil. trojúhelníků, ladicí příkazy `space.ShipMat` (body 33 a 34);
- hra kreslila v polovičním rozlišení, zpět na 100 % (bod 35);
- světlo a post scény, loď v kosmu přestala být silueta; rychlá smyčka `space.Post` / `space.Sun` / `space.Sky` (bod 36);
- dopečená okluze, kavita a odřený lak na trupu (bod 38);
- nápisy a výstražné pruhy na trupu jako decaly (bod 39);
- panelové spáry jako dlaždicová vrstva materiálu (bod 40);
- spálený plech u trysek, první zóna materiálu (bod 41);
- hra běžela na Medium: výchozí předvolba Cinematic a doostření (bod 42);
- SC-2b: VTOL, visící let a záře trysek při visení (bod 43);
- SC-3: značka dráhy letu na HUD (bod 44);
- rychlostní čáry: měkká vřetena místo bílých klacíků (bod 45);
- rychlostní tunel, prach bez zpoždění kamery (bod 46);
- workflow s referenčním videem (`Tools/Reference/fetch_video.py`) a poznámky ke quantum travel;
- SC-4: quantum drive místo cruise, HUD podle videa, tunel s mlhou (bod 47);
- jiskry kolem lodi, tunel s tmavým středem, kamera bez zpoždění ve skoku, méně bílých čar (bod 48);
- planety 1/4: atmosféra Veyry podle videa (bod 49);
- planety 2/4: Veyra 120 km, kulaté siluety, pryč zástupné asteroidy (bod 50);
- planety 3/4: povrch ve třech měřítkách, teplá atmosféra (bod 51);
- planety 4/4: fotoskenovaná zem, kameny, Zen restart v Package.ps1 (bod 52);
- quantum tunel po autorově testu: bez prosvítání, uzavřený tmavý prostor, jiskry u lodi (bod 53);
- náběh skoku, QT FUEL na HUD v NAV, rovný pohled z kokpitu (bod 54);
- tunel nic neprosvítá (maskovaná mlha) a jiskry vypadají jako jiskry (bod 55);
- skok podle reference: maják v úběžníku, připíchnutá expozice, proudící jiskry (bod 56);
- plastový trup: změřeno, že to byl materiál, ne světlo (bod 57).
