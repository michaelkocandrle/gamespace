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
| `USpaceFlightHud`, `USpaceHudGauge`, `USpaceHudVirtualJoystick` | `SpaceFlightHud.*` | SC-1c letový HUD v UMG: kontrolky, ukazatel rychlosti a omezovače, G-metr, boost a afterburner, virtuální joystick. Strom widgetů stavěný v C++. |
| `USpaceShotRunner` | `SpaceShotRunner.*` | Snímky podle scénáře pro vizuální kontrolu (kapitola 9): `-ShotList=` z příkazové řádky, `space.Shot` a `space.Shots` v konzoli. |
| `ASpaceDebugHUD` | `SpaceDebugHUD.*` | Textový debug HUD (CVar `space.Hud`), FPS; vytváří `USpaceFlightHud`. Anglicky, placeholder, zbytek nahradí SC-3. |
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
| `Content/UI/Fonts/` | Fonty HUD (Rajdhani, Share Tech Mono) i s licencemi SIL OFL. Načítají se ze souboru, ne jako Font asset: importér fontu potřebuje Slate aplikaci, kterou headless editor nemá. Do balíčku je dostává `DirectoriesToAlwaysStageAsUFS` v `Config/DefaultGame.ini`. |
| `Assets/install_mannequin_pack.py`, `generate_milky_way_glow.py` | Jednorázová instalace a textura. |
| `Blender/gamespace_ship_export.py` | Export lodí z Blenderu (FBX, manifest, validace). |
| `Blender/cockpit_view_survey.py` | Změří, co pilot vidí: paprsky přes zorné pole proti skutečnému modelu, kolik % výhledu je volných a co ho blokuje. Po změně modelu nebo pozice kamery. |
| `Shots.ps1` + `Shots/*.json` | Snímky ze zabalené hry podle scénáře (kapitola 9). |
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
| `test_ifcs_sc1.py` | SC-1a: limity trysek podle směru, coupled brzdění, decoupled, omezovač, spacebrake, SCM/NAV, setrvačnost rotace, G-Safe, ComStab, virtuální joystick, input assety, hodnoty Vanguardu. |
| `test_flight_hud_sc1c.py` | SC-1c: strom widgetů, data HUD z lodi (rychlost vůči omezovači, afterburner, pozpátku, kontrolky, G, palivo, joystick) a jejich zobrazení ve widgetech. Vzhled headless ověřit nejde. |
| `test_boost_afterburner_sc1b.py` | SC-1b: boost jen manévrovací trysky a rotace, vypnutí G-Safe, afterburner (tah, limit × omezovač, palivo, zamčení, doplňování, plynulý návrat, coupled i decoupled, jen SCM, G-Safe zůstává), Shift + Tab, input a hodnoty Vanguardu. |
| `test_flight_modes.py` | Boost energie, cruise jen v NAV (vesmír i nad Veyrou), výstup, kolize lodi, záchrana postavy, tělesa, zvuky. |
| `test_menu_settings.py` | Třída nastavení, herní režimy a controller, config cookování, level MainMenu, zvuky UI, orientace při výstupu. |
| `Tools/Assets/tests/*`, `Tools/Blender/tests/*` | Čistý Python bez Unrealu: plán importu, manifest (`python <soubor>`). |

Co headless **nejde** ověřit a musí vyzkoušet autor ve hře:
- vzhled (obloha, jas, rámování úvodní obrazovky);
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
| `cockpit_tune` | Porovnání variant kokpitu vedle sebe (pozice oka, co se pilotovi skrývá). Vzor pro dočasné scénáře při ladění. |

Scénář je JSON a **čte se z disku za běhu**, takže úprava scénáře nevyžaduje nové zabalení hry.
Pole jednoho snímku: `name`, `camera` (`cockpit`/`chase`), `hud` (0/1/2), `altitude_m`, `facing`
(`horizon`/`planet`/`away`), `speed_ms`, `mode` (`SCM`/`NAV`), `limiter`, `coupled`, `gsafe`,
`comstab`, `boost`, `afterburner`, `stick` (kurzor VJoy), `settle` (sekundy na ustálení),
`cockpit_eye`, `hide_hull`, `hide_canopy` (pro ladění kokpitu bez reimportu lodi).

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
- Scénář umí jen to, co má v polích. Přistání, výstup z lodi nebo menu se zatím fotit nedají.
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
- **SC-2 – Přistání SC stylem**
  - Landing gear (N) s vizuálem na socketech `Gear_*`.
  - Precision / landing mode s nízkými limity.
  - Přepínač VTOL.
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
  a viset, ale nic to nedává najevo: trysky nesvítí, zvuk se nemění, G-metr je na nule. Chování je
  správné (coupled brzdí i svisle), působí ale lacině. **Úkol na budoucí VTOL/hover polish**, ne teď:
  zapojit svislý tah do `GetEngineDemand` a do záře trysek, přidat hover zvuk a případně ukázat tah
  na HUD.
- **Kokpit:** Vanguard nemá modelovaný vnitřek kabiny (canopy je nízká skořepina nad plným trupem a
  rám kabiny je součástí trupu). Sklo canopy se proto pilotovi skrývá (`hide_canopy_in_cockpit`) a
  oko je na (500, 0, 110): obloha je volná a dole je vidět příď jako palubní deska. Z pozice sedadla
  (340, 0, 100) trup a rám kabiny zakrývaly většinu obrazu, i se skrytým sklem – viz porovnávací
  snímky (`Tools\Shots.ps1 -Preset cockpit_tune`). Skutečný interiér je úkol pro budoucí iteraci
  pipeline lodí.
- **V PIE Escape ukončí hru** (je to zkratka editoru). V PIE otevírá menu **F10**, v buildu Escape.
- Debug HUD je anglicky, menu česky.
- Build je **Development** (má konzoli `~`). Shipping zatím nebyl zkoušený.
- `IMC_Spaceship` a `IMC_Character` pořád mapují H na `IA_ToggleHud`. Nic na to není navázané
  (H obsluhuje controller), je to neškodné.
- Asteroidy v TestSpace jsou šedé placeholder krychle.
- Obloha nerozlišuje denní a noční stranu planety: v atmosféře je modrá všude.

---

## 12. Technické pasti (ušetří hodiny)

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
- následující commit: SC-1a, jádro IFCS podle Star Citizen.
