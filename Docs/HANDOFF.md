# Gamespace – handoff pro další session

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
  - jedna planeta **Veyra** (poloměr 25 km, atmosféra 12 km, gravitace 6 m/s²);
  - kulisy: měsíc **Keth** a plynný obr **Orun** s prstenci;
  - loď **Vanguard**: od 18. 9. 2026 model z Meshy („Ironclad Starfighter“), 14 × 11,4 × 6,2 m se
    4 motorovými gondolami, zpracovaný receptem `Tools/Blender/build_ai_ship.py` (kapitola 5, bod 20).
    Původní procedurální model (17,6 m) je v `ArtSource/Ships/Vanguard/Vanguard.blend` jen pro historii;
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
| Cruise (jen v NAV) | J |
| Kamera chase / kokpit | C |
| Zoom | Alt + kolečko |
| Free look | pravé tlačítko |
| Podvozek (vysunutí zapne i precision) | N |
| Precision mode | P |
| Stránky MFD (levý / pravý, s Alt zpět) | F1 / F2 |
| Přiblížení na displeje (držet) | Z / prostřední tlačítko myši |
| Vystoupit (jen když LANDED) | F |

**Postava:** WASD, myš, Space skok, Shift sprint, F nastoupit.

**Globální:** Escape (F10) menu a pauza, H HUD (kompaktní / plný / skrytý).

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
| `test_flight_modes.py` | Boost energie, cruise jen v NAV (vesmír i nad Veyrou), výstup, kolize lodi, záchrana postavy, tělesa, zvuky. |
| `test_cockpit_displays.py` | Displeje v kokpitu: dvě obrazovky (FLIGHT, SYSTEMS) se všemi přístroji a velkým písmem, stejné hodnoty jako HUD pro stejnou loď, komponenta na lodi, slot `M_Ship_Vanguard_Screens` v interiéru s unlit `MI_Ship_Vanguard_Screens`. Stránky MFD (přepínání, obtékání, titulek a záložka, obsah seznamů a tahu, klávesy F1/F2 a [ ] bez kolizí, ladicí zobrazení enginu z F1/F2 odebrané). Střední sloupek: RADAR a SELF STATUS, `texture_rect` v receptu = `ScreenRect` v kódu, poměr stran jako sklo, radar vidí objekt v dosahu přesně tam, kde je (a ten mimo dosah ne), těleso jako směr, planeta pod lodí bez směru, silueta z 10 hullů Vanguardu, 4 motory, 3 nohy, 4 sockety `Display_*`. Jak vypadají: `-Preset cockpit` a `cockpit_centre`. |
| `test_cockpit_frame.py` | Kokpit: Vanguard má interiér (díl, oko nad vanou za deskou, deska 7–13° pod okem jako v SC referenci, pilot ≥ 1,2 m od desky, provizorium vypnuté); rozložení provizorního rámu pro lodě bez interiéru (nic v okně HUD, deska 14–20° pod horizontem, sloupky 24–34° do stran, sedadlo za okem). |
| `test_landing_sc2.py` | SC-2a: dosednutí jen s podvozkem (GEAR UP před vším ostatním, mezera pod patkami), stavový automat podvozku (časy, otočení v půlce, zákaz zasunutí na zemi), pohyb modelovaného dílu i zástupných nohou, precision (strop, omezovač uvnitř, jen SCM, bez afterburneru, pomalejší otáčení, brzdění bez skoku), kontrolky GEAR/PREC, klávesy N/P bez kolizí, hodnoty a díl `Gear` Vanguardu, scénář `landing`. |
| `test_menu_settings.py` | Třída nastavení, herní režimy a controller, config cookování, level MainMenu, zvuky UI, orientace při výstupu. |
| `test_scene_look.py` | Vzhled uložené úrovně proti receptu: intenzita sky lightu, contact shadows a šířka slunce, všechna nastavení `POST_SETTINGS` v neohraničeném volume (a že chromatická aberace a vyvážení bílé zůstala vypnutá), lak trupu z `Vanguard_setup.json`. Chytá zapomenuté spuštění `build_space_scene.py` / `import_ship.py`. |
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

| Scénář | K čemu |
| --- | --- |
| `cockpit` | Pohled z kokpitu a chase kamery nad planetou i ve vesmíru, s HUD i bez něj. |
| `hud` | Letový HUD ve všech stavech: klid, na limitu, afterburner, boost s vychýleným joystickem, NAV, decoupled s vypnutým G-Safe, let pozpátku, plný textový výpis. |
| `ship` | Loď zvenku: nad planetou, při sestupu, ve vesmíru, se zářícími tryskami. |
| `cockpit_light` | Nasvícení kokpitu proti tmavé SC referenci: nastavení ze setupu ve vesmíru a v atmosféře, staré šedé a bez světel pro srovnání. |
| `cockpit_tune` | Porovnání variant kokpitu vedle sebe (pozice oka, co se pilotovi skrývá). Vzor pro dočasné scénáře při ladění. |
| `ship_views` | Loď ze všech stran (8 pohledů kolem, shora, zespodu s podvozkem, zblízka, ve vesmíru, se zářícími tryskami). Pro každý nový nebo změněný model. |
| `landing` | SC-2a: podvozek ze strany (dole, v půlce cesty), zespodu, loď stojící na patkách, varování GEAR UP, loď na břiše bez podvozku, HUD po přistání, precision HUD, kokpit na zemi. |
| `cockpit_centre` | Střední sloupek desky (RADAR, SELF STATUS): vesmír, horizont, afterburner, vysouvání podvozku, přistání. Obrazovky jsou malé: vyříznout a zvětšit. |
| `cockpit_readability` | Čitelnost displejů: výchozí pohled, přiblížení (Z) na FLIGHT/STATUS a THRUSTERS/CONTACTS, na konci staré oko pro srovnání. |
| `hull_tune` | Ladění materiálu trupu: šest variant v jednom běhu přes `space.ShipMat` (síla detailu, velikost dlaždice, světlejší lak, drsnost). |
| `hull_detail` | Trup zblízka (tryska, bok, vršek, celá loď): posouzení detailní vrstvy materiálu. Srovnání: `detail_normal_strength` 0 v setupu, znovu import a balení. |
| `mfd_pages` | Stránky MFD: FLIGHT/STATUS, THRUSTERS/CONTACTS s afterburnerem, NAVIGATION/SELF STATUS ve vesmíru a po přistání, THRUSTERS při visení. Stránky nastavuje pole `console` (`space.MfdPage`). |
| `look_sun` | Proč je loď v kosmu silueta: stejný záběr se sluncem otočeným po 90° (`space.SunDir`), pak s jasnějším sky lightem a méně drsným trupem. |
| `look_fill` | Odděluje světlo od laku: sweep intenzity sky lightu 0.35–1.5, pak světlejší lak, méně kovu a tvrdší slunce. |
| `look_tune` | Post process po vrstvách (contact shadows, Lumen, sky light, grade, film) v kosmu i v atmosféře; poslední snímek vypíše `space.PostDump`. |
| `look_final` | Vybrané hodnoty proti úrovni tak, jak je: vesmír, atmosféra, kokpit, detail – a Lumen kvalita zvlášť, aby byla vidět cena ve snímcích. |
| `hull_zones` | Rozbití jednolitého trupu: okluze, kavita ve dvou sílách a odřený lak ve třech, první dvojice bez všeho pro srovnání. |
| `hull_decals` | Kam dosedly nápisy: zblízka na každý z nich a pak celá loď. Decal, který není kolmý na svůj povrch, se rozmaže do šmouh místo aby četl – to je to, co se na snímcích hledá. |
| `hull_panels` | Panelové spáry: bez nich, pak list ve třech velikostech a třech sílách (`space.ShipMat`). |

Scénář je JSON a **čte se z disku za běhu**, takže úprava scénáře nevyžaduje nové zabalení hry.
Pole jednoho snímku: `name`, `camera` (`cockpit`/`chase`), `hud` (0/1/2), `altitude_m`, `facing`
(`horizon`/`planet`/`away`), `speed_ms`, `mode` (`SCM`/`NAV`), `limiter`, `coupled`, `gsafe`,
`comstab`, `boost`, `afterburner`, `stick` (kurzor VJoy), `settle` (sekundy na ustálení),
`cockpit_eye`, `hide_hull`, `hide_canopy`, `cockpit_light` [cd, cd], `display_light`, `interior_tint` (pro ladění kokpitu bez reimportu lodi), `console` (seznam konzolových příkazů před snímkem, pro srovnání nastavení), `gear` (podvozek
hned dole / nahoře), `lower_gear` (začne vysouvat, krátký `settle` ho chytí v půlce), `precision`,
`chase_yaw`, `chase_pitch` (> 0 = zespodu), `chase_zoom` (kamera otočená kolem lodi). Nízká
`altitude_m` s podvozkem a pár sekund `settle` loď opravdu posadí na zem.

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

Dnešní systém (FA on/off, páka, boost, cruise J) je mezikrok. Části se převezmou (per-axis limity
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
  - **SC-2b (další krok):** VTOL (G, jen SCM, přechod ~1,5 s): hlavní tah ~35 %, strop ~60 m/s, svislé
    trysky ×1,5 a boční ×1,3, Space/Ctrl na stoupavost ~15 m/s, auto-srovnání na horizont, afterburner
    a cruise odmítnuté. K tomu zpětná vazba při visení z kapitoly 11 (svislý tah v `GetEngineDemand`,
    záře trysek, hover zvuk).
- **SC-3 – zbytek HUD a MFD:** VTOL a GEAR (po SC-2), ESP a LOCK (až budou zbraně), velocity
  vector, MFD panely, celková přestavba na UMG a náhrada anglického debug HUD.
- **SC-4 – Quantum travel** místo cruise J: markery cílů (Veyra, Keth, Orun, později stanice),
  natočení, spool + kalibrace (B), engage, efekt tunelu, cooldown, blokace překážkou, palivo.
  Vyžaduje rozhodnutí o měřítku systému (SpaceEnvironment reference doporučuje realistické
  vzdálenosti + QT).
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
- **Vznášení v atmosféře bez zpětné vazby** (autor 17. 9. 2026): loď umí v atmosféře úplně zastavit
  a viset, ale nic to nedává najevo: trysky nesvítí, zvuk se nemění. Chování je
  správné (coupled brzdí i svisle), působí ale lacině. **Řeší se v SC-2b spolu s VTOL.** Příčina je
  změřená: `GetEngineDemand` bere svislou osu × 0,7 proti plné kapacitě zvedacích trysek, visení na
  Veyře (~0,46 G) tak dává zátěž ~0,06, takže záře i zvuk zůstanou skoro na nule. G-metr naopak
  ukazuje 0,5–0,8 G (snímky `landing` 18. 9. 2026), jen je to na stupnici 12 G malý proužek.
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
- Asteroidy v TestSpace jsou šedé placeholder krychle.
- Obloha nerozlišuje denní a noční stranu planety: v atmosféře je modrá všude.

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
- panelové spáry jako dlaždicová vrstva materiálu (bod 40).
