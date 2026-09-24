---
name: unreal-scripting
description: Headless Unreal Engine 5.8 work on the gamespace project - C++ editor build (Build.bat gamespaceEditor), Live Coding vs. editor restart, unity-build differences of the game target, headless Python via Tools/run_editor_python.ps1, the test list (Tools/Tests/*.py plus plain-Python tests), Tools/Package.ps1 and cooking (DirectoriesToAlwaysCook, path-loaded assets), git/commit rules, and the known traps for environment, content/cooking, C++/UHT and Python in UE (unreal.Rotator order, StaticMeshEditorSubsystem None, set_collision_enabled not saved, material pin names, tags vs. labels). Load before building C++, running an editor Python script or test, packaging the game, or committing.
---

# Unreal headless: build, Python, testy, balení, git

Autor není herní vývojář: **všechno skriptem nebo kódem, nikdy klikáním v editoru.**
Komunikace s autorem česky, commit zprávy anglicky. Když se editoru nejde vyhnout, dej číslované
kroky s přesnými názvy. **Neměř a netestuj v PIE ani v okně editoru bez vyžádání** (kradlo mu myš).

## Cesty

| Co | Kde |
| --- | --- |
| Engine | `C:\Program Files\Epic Games\UE_5.8` |
| Projekt | `C:\gamespace\gamespace\gamespace.uproject` |
| C++ | `Source/gamespace/` (moduly v `gamespace.Build.cs`) |
| Python knihovna pro skripty | `Content/Python/gamespace_assets.py` (na `sys.path`, `import gamespace_assets`) |
| Skripty assetů | `Tools/Assets/*.py` (import_ship, import_interior, build_space_scene, add_*_input, ship_materials…) |
| Headless testy | `Tools/Tests/test_*.py` |
| Zabalená hra | `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe` (Development) |
| Config cookování | `Config/DefaultGame.ini` |

## 1. C++ build

PowerShell, **editor musí být zavřený**:

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" gamespaceEditor Win64 Development -Project="C:\gamespace\gamespace\gamespace.uproject" -WaitMutex -FromMsBuild
```

- **Live Coding** stačí jen na změny těl funkcí. Nové soubory, `UPROPERTY`, `UFUNCTION`, změny
  hlaviček = zavřít editor + plný build. **Autorovi to vždy napiš** (Live Coding / restart editoru).
- **Herní target má jiné seskupení unity buildu než editor.** Chyba (kolize jmen) se může ukázat
  až v `Package.ps1`. Viz 9.4a níže.
- Nový modul v `gamespace.Build.cs` je povolený (Smart App Control je vypnutý). Když build spadne
  na Code Integrity (3077 / 0x800711C7), řekni to autorovi a **na bezpečnostních nastaveních
  Windows nic neměň**.

## 2. Headless Python v editoru

**Vždy nástrojem PowerShell** (z bashe se rozbije `$PSScriptRoot`):

```powershell
.\Tools\run_editor_python.ps1 Tools\Tests\test_cockpit_displays.py
.\Tools\run_editor_python.ps1 Tools\Assets\import_interior.py
```

- Spouští `UnrealEditor-Cmd.exe -run=pythonscript -NullRHI`, plugin Python zapíná z příkazové řádky.
- **Odmítne běžet, když je projekt otevřený v editoru** (editor by skriptem změněné assety
  přepsal). Požádej autora, ať editor zavře.
- Výsledek: `RESULT: OK` / `RESULT: FAILED`, plný log v `%TEMP%\editor_python_<čas>.log`.
  Commandlet sám hlásí úspěch i po výjimce, proto skript čte log (`LogPython: Error`, `Traceback`).
  `FAILED - the script never ran` = editor nenastartoval (typicky herní modul nejde načíst, chybí build).
- Delší skripty (patche, generátory) piš nástrojem Write do scratchpadu, ne heredocem v bashi
  (apostrofy). Cesty v Pythonu jako `r"C:\..."` (`\U` = unicode escape).
- Env proměnná pro skript: `$env:GAMESPACE_SHIP_MANIFEST = "...\Vanguard_manifest.json"; .\Tools\run_editor_python.ps1 ...`

## 3. Testy

Spusť ty, kterých se změna týká; po větší změně všechny. Každý tiskne `SUMMARY OK/FAILED`
(`test_planet_rocks.py` tiskne `ROCKTEST PASS/FAIL` + souhrn).

| Test (`Tools/Tests/`) | Pokrývá |
| --- | --- |
| `test_ifcs_sc1.py`, `test_boost_afterburner_sc1b.py`, `test_flight_modes.py`, `test_free_look.py` | let, IFCS, boost, afterburner, výstup, kolize lodi |
| `test_landing_sc2.py`, `test_landing_l5.py`, `test_vtol_sc2b.py` | podvozek, přistání, precision, VTOL |
| `test_flight_hud_sc1c.py`, `test_flight_hud_sc3.py` | HUD, značka dráhy letu |
| `test_cockpit_displays.py`, `test_cockpit_frame.py` | MFD, radar, self status, oko a deska kokpitu |
| `test_quantum_sc4.py`, `test_speed_tunnel.py` | quantum drive, tunel skoku |
| `test_ship_import.py` | import lodi z manifestu (volitelně `GAMESPACE_SHIP_MANIFEST`) |
| `test_interior.py` | interiér Steadfastu: usage flagy, výchozí textury samplerů, `M_KitTrim`, tagy, světla |
| `test_scene_look.py` | uložená úroveň proti receptu (atmosféra, post process, lak) – chytá zapomenutý `build_space_scene.py` / `import_ship.py` |
| `test_planet_l3.py`, `test_planet_rocks.py`, `test_character_l6.py`, `test_menu_settings.py` | planeta, kameny, postava, menu a nastavení |

Mimo UE (obyčejný `python <soubor>`):
- `Tools/Assets/tests/test_import_ship_plan.py`
- `Tools/Blender/tests/test_ship_export_core.py`

Headless **nejde** ověřit: vzhled (→ snímky `Tools\Shots.ps1`, skill unreal-shots-and-look), zvuk,
Slate menu, skutečné kolize (v commandletu traces/sweepy nezasáhnou).
Pravidlo: když se opraví chyba, kterou autor viděl, přidej do testu kontrolu, která by ji chytila
(příklad `no_nanite_parts` v `test_import_ship_plan.py`, usage flagy v `test_interior.py`).
Úplný popis testů: HANDOFF kap. 8.

## 4. Balení a cookování

```powershell
.\Tools\Package.ps1     # ~5 min; BuildCookRun Development -> C:\gamespace\Builds\Gamespace
.\Tools\Play.ps1        # spuštění; -Windowed -Width 1600 -Height 900 pro okno
```

- Editor musí být zavřený. Autor hraje **zabalenou hru**, po změně C++ nebo obsahu vždy znovu balit.
- Když autor hru hraje, balení visí nebo nakopíruje starý exe. **Po zabalení zkontroluj čas
  `gamespace.exe`.** Neptej se předem, jestli hra běží – prostě balíš; ozvi se jen při zaseknutí.
- `Package.ps1` sám ukončí proces `gamespace` (zaseknutý snímkový běh) a při „Failed reading oplog
  from Zen“ restartuje `zenserver` a balí ještě jednou.
- Selhání: `PACKAGE FAILED` → UAT log v `C:\Program Files\Epic Games\UE_5.8\Engine\Programs\AutomationTool\Saved\Logs`
  a cook log `%APPDATA%\Unreal Engine\AutomationTool\Logs\...\Log.txt`.
- Po buildu kontroluje `Manifest_UFSFiles_Win64.txt`: 12 klíčových assetů (mapy, zvuky, input,
  `M_SpaceDust`, `BP_Ship_Vanguard`, písma). Chybí-li, `PACKAGE INCOMPLETE`.

**Assety načítané z C++ podle cesty** (`StaticLoadObject`, `ConstructorHelpers`) cooker nevidí.
Musí být ve složce z `Config/DefaultGame.ini`:

```ini
+DirectoriesToAlwaysCook=(Path="/Game/Input")        ; dál Ships, UI, Environments, Planets, Characters, Blueprints
+DirectoriesToAlwaysStageAsUFS=(Path="UI/Fonts")      ; relativně ke Content, ne /Game/...
```

Nový adresář načítaný podle cesty = přidat řádek **a** doplnit kontrolu do `$required` v `Package.ps1`.

Uncooked `-game` (bez zabalení) kreslí nové materiály šedě – vzhled posuzuj jen v zabaleném buildu.

## 5. Git

- Každý hotový krok (i drobnost nebo dokumentace) **commit + push**: `git push origin main`
  (https://github.com/michaelkocandrle/gamespace). Nic nenechávej jen lokálně.
- **Před commitem `git status`** a kontrola, co jde dovnitř.
- **Nikdy nepřidávej:**
  - `ArtSource/Ships/Vanguard/Export/Meshy_AI_Sci_Fi_Transport_Ship_0918125120_texture_fbx/` (autorova složka)
  - `Docs/UI/Screenshot 2026-09-21 150400.png`
  ```bash
  git add -A -- . ':!ArtSource/Ships/Vanguard/Export/Meshy_AI_Sci_Fi_Transport_Ship_0918125120_texture_fbx' ':!Docs/UI/Screenshot 2026-09-21 150400.png'
  ```
- **Nikdy force push**, žádné přepisování historie, žádné `--no-verify`.
- Zpráva anglicky, krátký nadpis, na konci:
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
- `.uasset`/`.umap` a zdrojová grafika jdou přes Git LFS (`.gitattributes`).
- Po větším kroku aktualizuj `Docs/HANDOFF.md` (kap. 5 hotové, kap. 11 známé problémy,
  kap. 13 commity); po změně systému i `README.md`.

## 6. Nástrahy (příznak → příčina → řešení)

### Prostředí (WORKFLOW 9.1)
- **Balení visí / starý exe** → běží hra z `Builds` nebo visí spadlý proces → autor ať hru zavře,
  zkontroluj čas `gamespace.exe`.
- **`run_editor_python.ps1` z bashe nefunguje** → `$PSScriptRoot` → nástroj PowerShell.
- **Bash heredoc rozbije Python** → apostrofy, `\U` v cestách → Write do scratchpadu, `r"..."`.
- **Blender z Git Bash mění cesty** `/c/...`, `//Export` → vždy `MSYS_NO_PATHCONV=1`.
- **winget nástroj není v PATH** do restartu terminálu → volej plnou cestou.
- **Klávesy:** autor má českou klávesnici (0405) – `[ ] ; '` nejsou samostatné klávesy. Nové
  klávesy z písmen, čísel, F-kláves, čárky, tečky. F1–F5, F9, F11, PgUp/PgDn, `;` mají v Development
  ladicí příkazy enginu → uvolnit řádkem `-DebugExecBindings=(…)` (přesná kopie z `BaseInput.ini`)
  v `Config/DefaultInput.ini`.

### Obsah a cookování (WORKFLOW 9.3, obecné)
- **Písmo v buildu chybí** → `DirectoriesToAlwaysStageAsUFS` je relativní ke `Content` (`UI/Fonts`).
- **Zvuky/input v buildu chybí** → načítané podle cesty → `DirectoriesToAlwaysCook` + kontrola v `Package.ps1`.
- **Blueprint drží starou hodnotu** po odebrání ze `_setup.json` → v BP ji nastav explicitně.
- **Input assety** `IA_*`, `IMC_Spaceship`, `IMC_Character` **nikdy znovu nevytvářej**; mapování
  jen přidávej `gamespace_assets.add_mappings()` ve skriptech `Tools/Assets/add_*_input.py`.
- **Šedá šachovnice v zabalené hře, v editoru OK** → materiál se při cooku nezkompiloval
  (`WorldGridMaterial`): (1) chybí usage flag – skript musí nastavit `used_with_nanite`,
  `used_with_static_mesh`, `used_with_instanced_static_meshes`; (2) sampler bez výchozí textury
  spadne na sRGB `DefaultTexture` → u Normal/Linear = chyba kompilace. Hledej „Failed to compile
  Material“ v cook logu (hlásí uzel); log hry říká jen „missing usage flag“, „Invalid shader map ID“.
- **Průsvitné/aditivní materiály nesmí na Nanite mesh** → vlastní mesh s vypnutým Nanite.
- **Statické světlo nejde za běhu měnit setterem** → zápis do vlastností + `MarkRenderStateDirty()`
  (`SpaceInteriorTuning.cpp`, `SpacePostTuning.cpp`).
- **Konzolové příkazy scénáře snímků** mají být idempotentní (přepínače jako `space.Interior`).
- **Žádná jména ze Star Citizenu** v obsahu (stanice, lodě, firmy) – vzhled ano, značky ne.
- Interiérové a kitbash nástrahy (rub stěn, světla za stěnou, blikání koplanárních ploch, díry
  paprsky, stíny lokálních světel, jména materiálů v `import_interior.py`, Meshy sestavy, bmesh
  normály): WORKFLOW 9.3 e, g–n, p–s, x–aa. Vykreslování: WORKFLOW 9.2 (skill unreal-shots-and-look).

### C++ a UHT (WORKFLOW 9.4)
- **Build editoru projde, balení spadne na redefinici** → unity build herního targetu spojí jiné
  .cpp → statické helpery a konstanty v .cpp pojmenovávej jedinečně (`MasterModeColor`, ne `ModeColor`).
- **`Points.Add(Points[0])` padá** → realokace TArray zneplatní referenci → prvek nejdřív zkopíruj.
- **C4458 `Slot` zastiňuje `UWidget::Slot`** → ve widgetech nepoužívej `Slot` jako jméno proměnné.
- **UHT chyba: parametr `UFUNCTION` = jméno vlastnosti třídy** → přejmenuj parametr.
- **Nativní třídy:** CDO hodnoty se do instancí nekopírují → assety načítej v konstruktoru (`ConstructorHelpers`).
- **Pohyb pawnu sweepuje jen root** (`HullCollision`, ignoruje pawny); postava koliduje s `Hull` (UCX).
- Co má Python „přepočítat“ na C++ herci (construction script), vystav jako
  `UFUNCTION(BlueprintCallable)` (vzor `ASpaceSlidingDoor::LayoutLeaves`).

### Python v UE (WORKFLOW 9.5 + 9.3 o, t, w)
- **`unreal.Rotator(a, b, c)` je poziční roll, pitch, yaw** → vždy `unreal.Rotator(roll=…, pitch=…, yaw=…)`.
- **`unreal.Color(255, 238, 214)` je modrá** (FColor = B, G, R, A) → `unreal.Color(r=255, g=238, b=214, a=255)`.
- Struct wrappery obecně neberou keyword argumenty v konstruktoru → vytvoř prázdný a nastav `set_editor_property`.
- **Commandlet:** traces a sweepy nezasáhnou; animace potřebují `++GFrameCounter`; shadery se
  nekompilují (chyby HLSL až při cooku).
- Vlastnosti jen `Config` bez `BlueprintReadOnly`/`Edit` nejsou z Pythonu vidět → přidej specifikátor.
- **`StaticMeshEditorSubsystem` headless vrací `None`** → Nanite vypni
  `mesh.set_editor_property("nanite_settings", …)` (mesh se přestaví sám).
- `rerun_construction_scripts` v Pythonu neexistuje (viz UFUNCTION výše); `get_relative_location`
  není → `comp.get_editor_property("relative_location")`.
- **`set_collision_enabled()` se s levelem neuloží** → `set_collision_profile_name("NoCollision")`.
- **Piny uzlů materiálu:** `Power` má `Base`/`Exp` (ne `A`/`B`); `TextureSample` bere souřadnice na
  `UVs` (ne `Coordinates`). `connect_material_expressions` při špatném jménu jen vrátí `False` →
  kontroluj návratovou hodnotu a hlas chybu (vzor `link()` v `import_interior.py`).
- **`spawn_actor_from_object` headless padá** (ACCESS_VIOLATION) → `spawn_actor_from_class(unreal.StaticMeshActor, …)`
  a pak `static_mesh_component.set_static_mesh(...)`.
- `asset_import_data` z Interchange nemá `source_data` → starší kód na tom padá.
- **Label herce v zabalené hře neexistuje** (`set_actor_label` je jen editor) → co má hra najít,
  dostane **tag**: `actor.set_editor_property("tags", [unreal.Name("...")])` (vzor `import_interior.py`).

## 7. Odpověď autorovi po kroku

Co se změnilo a proč; které testy prošly; které snímky jsi sám prohlédl; že je build připravený
v `C:\gamespace\Builds\Gamespace\Windows\gamespace.exe`; přesný testovací scénář (klávesy, kam letět);
co posoudí jen autor; Live Coding vs. restart editoru; rizika. Podrobně WORKFLOW kap. 1.
