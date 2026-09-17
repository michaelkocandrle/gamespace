# Gamespace – handoff pro další session

Stav k **17. 9. 2026**. Tento dokument je vstupní bod pro novou session (Claude Code) i pro autora
projektu. Popisuje, co projekt je, jak se s autorem pracuje, kde je co v kódu, co je hotové, co je
rozbité nebo neověřené a co následuje.

> **Pro novou session – začni takhle:**
> 1. Přečti celý tento dokument.
> 2. Přečti **master referenci** v `C:\gamespace\gamespace\starcitizenreference\` (kapitola 3).
> 3. Přečti `README.md` (technická dokumentace systémů, anglicky) a podle úkolu
>    `Docs/Ships/ShipPipeline.md` nebo `Docs/Characters/CharacterPipeline.md`.
> 4. Než cokoli změníš, přečti si pravidla spolupráce (kapitola 2).

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
  - loď **Vanguard** (lehká stíhačka 17,6 × 13 × 4,4 m, vlastní model z Blenderu);
  - postava na nohou (placeholder UE Manny).
- **Další velký cíl autora:** letový systém lodi má být **kompletní kopie systému ze Star
  Citizen**. Nemá vzniknout najednou, ale po krocích (kapitola 9).

---

## 2. Autor a pravidla spolupráce (DŮLEŽITÉ)

- **Komunikace česky.** Autor **není herní vývojář** a nezná UI Unreal Editoru. Všechno dělej
  kódem a skripty, ne návodem „klikni v editoru“. Když se editoru nejde vyhnout, dej číslované
  kroky s přesnými názvy.
- Na konci každého kroku autor chce:
  - přesný **testovací scénář** (co spustit, co zkusit, co má vidět);
  - informaci, jestli stačí **Live Coding**, nebo je nutný **restart editoru**;
  - **rizika** a co je neověřené.
- **Neměřit ani netestovat v PIE či okně editoru bez vyžádání** („ne laskavě už proteď nic
  neměř“). Testuj **headless** (`Tools/run_editor_python.ps1`) a autorovi napiš scénář.
  Okno editoru mu kradlo myš a klávesnici.
- **Ručně vyrobené input assety** (`IA_*`, `IMC_Spaceship`, `IMC_Character`) **nikdy znovu
  nevytvářej ani nepřepisuj**. Mapování jen přidávej přes `gamespace_assets.add_mappings()`.
- **Nikdy neměň bezpečnostní nastavení Windows.** Smart App Control autor 16. 9. 2026 vypnul,
  moduly v `gamespace.Build.cs` se proto přidávat smí. Když build selže na Code Integrity
  (3077 / 0x800711C7), řekni to autorovi a nic neměň.
- **Git:** commit po každém dokončeném kroku, **nepushovat** (pushuje autor). Commit message
  končí řádkem `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
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

Pozor:
- Úseky „Náš stav“ v referencích byly psané před posledními kroky a místy jsou zastaralé. Náš
  let už má coupled/decoupled (V), throttle páku, boost s energií a cruise (J). Aktuální stav je
  v kapitole 5.
- Složka **není v gitu** (untracked). Jestli ji commitovat, rozhoduje autor.

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
- Pracovní postup po změně: build → headless skript nebo testy → `Package.ps1` → commit →
  odpověď autorovi s testovacím scénářem.

---

## 5. Stav vývoje – co je hotové

Od nejstaršího (celkem 25 commitů, posledních ~7 nepushnutých):

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

---

## 6. Mapa kódu a obsahu

### C++ (`Source/gamespace/`)

| Třída | Soubor | Úloha |
| --- | --- | --- |
| `ASpaceshipPawn` | `SpaceshipPawn.*` | Loď: let (FA, plyn, boost, cruise), přistání, výstup, kamery, zvuk, světla, prach. Hlavní soubor letového systému, cíl přestavby na Star Citizen. |
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
| `ASpaceDebugHUD` | `SpaceDebugHUD.*` | Textový debug HUD (CVar `space.Hud`), FPS. Anglicky, placeholder, nahradit skutečným HUD. |
| `USpaceOriginRebasingSubsystem` | `SpaceOriginRebasingSubsystem.*` | Posun počátku světa. |

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
| `Assets/build_space_scene.py` | TestSpace: obloha, planeta, tělesa, prach, materiály. |
| `Assets/build_main_menu.py` | Level úvodní obrazovky. |
| `Assets/import_ship.py` + `ship_materials.py` | Import lodi z Blenderu. |
| `Assets/generate_ship_sounds.py` → `build_ship_audio.py` | Generátor zvuků (numpy) a jejich import. |
| `Assets/add_*_input.py` | Přidávání mapování kláves (pouze append). |
| `Assets/install_mannequin_pack.py`, `generate_milky_way_glow.py` | Jednorázová instalace a textura. |
| `Blender/gamespace_ship_export.py` | Export lodí z Blenderu (FBX, manifest, validace). |
| `Content/Python/gamespace_assets.py` | Knihovna pro skriptové vytváření IA, IMC a dalších assetů. |

### Dokumentace
- `README.md`: podrobný technický popis systémů (anglicky).
- `Docs/Ships/ShipPipeline.md`: pipeline lodí (česky).
- `Docs/Characters/CharacterPipeline.md`: pipeline postav (česky).
- `Docs/HANDOFF.md`: tento dokument.

---

## 7. Ovládání (aktuální)

**Loď:**

| Akce | Klávesa |
| --- | --- |
| Páka plynu (FA on) nebo přímý tah (FA off) | W / S |
| Strafe | A / D |
| Nahoru / dolů | Space / Ctrl |
| Roll | Q / E |
| Směr | myš |
| Boost | Shift |
| Flight assist | V |
| All stop | X |
| Cruise | J |
| Kamera chase / kokpit | C |
| Zoom | kolečko |
| Free look | pravé tlačítko |
| Vystoupit (jen když LANDED) | F |

**Postava:** WASD, myš, Space skok, Shift sprint, F nastoupit.

**Globální:** Escape (F10) menu a pauza, H HUD (kompaktní / plný / skrytý).

---

## 8. Testy

Všechny jsou headless (`.\Tools\run_editor_python.ps1 Tools\Tests\<soubor>`). Každý tiskne
`… SUMMARY OK/FAILED`. K 17. 9. 2026 **všechny prochází**.

| Test | Pokrývá |
| --- | --- |
| `test_planet_l3.py` | Terén, LOD, atmosféra, gravitace, pád, entry heat. |
| `test_landing_l5.py` | Sklon, pravidla dosednutí, tření, zarovnání, cena warm-upu kolizí. |
| `test_character_l6.py` | Input assety postavy, gravity frame, výstup, animace, foot IK. |
| `test_free_look.py` | Free look (neomezený yaw, návrat). |
| `test_ship_import.py` | Importovaná loď: meshe, kolize, sockety, materiály, všechny hodnoty ze setup JSON (s `GAMESPACE_SHIP_MANIFEST`). |
| `test_flight_modes.py` | Páka, detent, all stop, FA off, boost energie, cruise (vesmír i nad Veyrou), výstup, kolize lodi, záchrana postavy, tělesa, zvuky. |
| `test_menu_settings.py` | Třída nastavení, herní režimy a controller, config cookování, level MainMenu, zvuky UI, orientace při výstupu. |
| `Tools/Assets/tests/*`, `Tools/Blender/tests/*` | Čistý Python bez Unrealu: plán importu, manifest (`python <soubor>`). |

Co headless **nejde** ověřit a musí vyzkoušet autor ve hře:
- vzhled (obloha, jas, rámování úvodní obrazovky);
- zvuk;
- chování Slate menu;
- skutečné kolize (v commandletu nefungují traces ani sweepy).

---

## 9. Roadmapa – letový systém podle Star Citizen (rozdělit do kroků)

Autor chce **kompletní kopii SC pilotování**, ale ne v jednom kroku. Níže je navržené rozdělení.
**Před začátkem každé fáze** ho potvrď s autorem a zkontroluj master referenci. Každá fáze má
končit hratelným buildem, testy a scénářem.

Dnešní systém (FA on/off, páka, boost, cruise J) je mezikrok. Části se převezmou (per-axis limity
trysek, environment, přistání), jiné se nahradí (J cruise → quantum travel, páka → SC throttle
a speed limiter).

- **SC-1 – IFCS jádro a master modes**
  - Režimy SCM a NAV: rychlostní limity a manévrovatelnost. NAV vypíná „bojové“ věci.
  - SC semantika coupled a decoupled.
  - Speed limiter na kolečku myši; W/S jako cílová rychlost do limitu.
  - Kapacity trysek podle směru (main, retro, manévrovací), hmotnost a setrvačnost lodi.
  - Zrychlení a rotace omezené přetížením (G-Safe) a ComStab.
  - Myš jako VJoy s viditelným kruhem a kurzorem.
  - Oddělit boost (manévrovací) a afterburner (hlavní tah, palivo).
- **SC-2 – Přistání SC stylem**
  - Landing gear (N) s vizuálem na socketech `Gear_*`.
  - Precision / landing mode s nízkými limity.
  - Přepínač VTOL.
- **SC-3 – HUD a MFD:** rychlostní pásky, SCM/NAV, stavové přepínače VTOL/CPLD/ESP/GEAR,
  velocity vector, G-metr, kurzor VJoy. Nahradí anglický debug HUD (UMG nebo Slate).
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

## 10. Známé problémy a neověřené věci

- **Neověřeno autorem** (postaveno v posledním kroku, headless testy prochází):
  - úvodní obrazovka a její rámování kamery, menu a nastavení;
  - H v zabaleném buildu;
  - zvuk v buildu (dřív v něm úplně chyběl);
  - oprava krátkého škubnutí kamery po výstupu z lodi (postava je teď otočená k lodi).
- **Zvuky jsou procedurální placeholdery** z numpy a nikdo je zatím neslyšel. Ladění podle
  autorovy zpětné vazby. Hlasitosti jsou v nastavení a v `ASpaceshipPawn` (`EngineHumVolume`,
  `EngineVolume`, `BoostVolume`, `CruiseVolume`, `OneShotVolume`).
- **Jas oblohy** (slunce, mlhoviny) je nastavený odhadem. Ladí se v levelu na `StarfieldSky`
  (`NebulaScale`, `SunScale`) nebo v konstantách `build_space_scene.py`.
- **Uprostřed výhledu z kokpitu** je středový rám kabiny, tak je loď vymodelovaná.
- **V PIE Escape ukončí hru** (je to zkratka editoru). V PIE otevírá menu **F10**, v buildu Escape.
- Debug HUD je anglicky, menu česky.
- Build je **Development** (má konzoli `~`). Shipping zatím nebyl zkoušený.
- `IMC_Spaceship` a `IMC_Character` pořád mapují H na `IA_ToggleHud`. Nic na to není navázané
  (H obsluhuje controller), je to neškodné.
- Asteroidy v TestSpace jsou šedé placeholder krychle.
- Obloha nerozlišuje denní a noční stranu planety: v atmosféře je modrá všude.

---

## 11. Technické pasti (ušetří hodiny)

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

## 12. Poslední commity

Viz `git log --oneline`. Poslední kroky:
- `73b1410`: letové režimy, cruise, vrstvený zvuk, živá obloha, opravy výstupu a kokpitu;
- následující commit: hratelný build (úvodní obrazovka, pauza, nastavení, H, cookování, zvuky UI)
  a tento handoff.
