# Plán rozdělení `ASpaceshipPawn` (schválen 30. 9., proveden 1. 10. 2026; průběh na konci)

Podnět: technický audit v1, 4.1 a 4.8. Zadání autora: nejdřív jen návrh (pořadí kroků, rizika, které testy chrání
který krok); po schválení postupně po jedné komponentě, každá se zelenými testy, začít tou s nejmenším rizikem.
Podklad: čtecí mapa `SpaceshipPawn.h` (2 262 řádků) a `SpaceshipPawn.cpp` (3 978 řádků), ~235 UPROPERTY,
~141 UFUNCTION, žádná replikace; `BP_Ship_Wayfarer` je datový potomek bez vlastní logiky.

## Proč (konkrétní důvod podle principu v `ARCHITECTURE.md`)

- Jedna třída nese let, vstup, režimy, VTOL, podvozek, přistání, quantum, kameru, zvuk, světla, efekty, průchozí
  loď, výstup a ladicí API. Další systémy (poškození, energie, štíty, zbraně, náklad, AI lodě) by šly do ní.
- Testovací API (`Debug*`) a runtime API jsou promíchané; změna v jednom systému dnes znamená číst 6 000 řádků.
- Měřitelný cíl: každý systém ve vlastním souboru s jasným vstupem a výstupem, pawn jen orchestruje Tick
  a drží data. Chování se nemění (stejné testy, stejné hodnoty).

## Pravidla pro každý krok (z mapy rizik)

1. **Tuning UPROPERTY zůstávají na pawnu** (stejná jména). 23 hodnot je uložených jako override v
   `BP_Ship_Wayfarer`, klíče `pawn` v `<Loď>_setup.json` je nastavují jménem a testy je čtou z CDO
   (`ship_under_test.check_setup_values`, `get_editor_property`). Přesun vlastnosti z herce do komponenty by override
   tiše zahodil (CoreRedirects přesun z herce do podobjektu neumí). Komponenta čte tuning přes vlastníka.
   Přesun tuningu je samostatný pozdější krok se změnou setupu, importu a testů najednou a s reimportem.
2. **Stav (runtime proměnné) se stěhuje do komponenty**, tuning ne.
3. **Každá UFUNCTION volaná z Pythonu nebo z jiné třídy zůstane na pawnu jako tenký přeposílač** se stejným jménem
   (HUD čte ~45 getterů, snímkovač ~20 funkcí, testy ~120 volání). Testy se v krocích nemění.
4. **Pawn dál řídí pořadí v `Tick`/`StepFlight`** a volá komponenty výslovně; komponenty nemají vlastní
   `TickComponent`, nespoléhají na `BeginPlay` ani `InitializeComponent` (testy spawnují pawn v editorovém světě bez
   BeginPlay a Ticku). Pořadí je nosné: free look před řízením, prolínání prezentace po simulaci, `EngineLoad` (zvuk)
   před světly.
5. **13 výchozích podobjektů pawnu zůstává, jak jsou** (`CameraBoom`, `CockpitCamera`, `Hull`, `HullCollision`…):
   nesou override z importu a jména čte kód i Python. Nové logické komponenty vznikají v konstruktoru pawnu
   (`CreateDefaultSubobject`, bez ticku, stav `Transient`) a drží ukazatele na stávající podobjekty.
6. **Jména jako kontrakty zůstávají** (sockety `Display_*`, `Exit`, `WalkSeat`, `WalkRamp`, `Gear_*`, prefixy meshí
   `Interior*`, `InteriorMod_`, světla `Light_fix_`, tag `InteriorOnly`, sloty `Emissive`, `Thruster`…).
7. **Log kategorie** `LogSpaceship` se přesune do sdílené hlavičky (dnes je `static` v jednom .cpp).
8. Každý krok: build editoru, `Tools\Test.ps1 -UE -Filter <dotčené>` a nakonec `-All`, balení, dotčené snímky;
   commit za krok; když cokoliv zčervená, krok se vrací, ne opravuje za chodu.

## Cílový tvar

```
ASpaceshipPawn            data (tuning UPROPERTY), podobjekty, Tick = pořadí kroků, přeposílače API
├── FShipFlightModel      čistá matematika bez stavu (statické funkce, parametry v argumentech)
├── UShipSystemsComponent master mode SCM/NAV, omezovač, G-Safe, ComStab, boost, afterburner, VTOL
├── UShipLandingComponent podvozek, precision, dosednutí, tření, přistání a vzlet
├── UShipQuantumComponent cíl, blokace, spool, kalibrace, skok, příjezd, palivo
├── UShipPresentationComponent  efekty kamery, zvuk motorů, světla lodi, prach, tunel, jiskry, pohled z kabiny (MPC)
├── UShipBoardingComponent      průchozí loď: vstát, sednout, rampa, výstup, kapsle, gravitace v lodi
├── UShipInputComponent   napojení Enhanced Input a handlery
└── UShipDebugComponent   ladicí a testovací API (pawn ho přeposílá)
Let (IFCS, lineární a úhlový pohyb) zůstává v pawnu jako poslední krok a pak případně UShipFlightComponent.
```

Oproti auditu: navíc `UShipBoardingComponent` (průchozí loď a výstup jsou dnes samostatný velký celek, 29. 9. 2026)
a efekty kamery patří do prezentace. Pevný časový krok simulace se nedělá (odložené rozhodnutí v `ARCHITECTURE.md`);
`FShipFlightModel` ho ale později usnadní.

## Pořadí kroků, rizika a testy

| # | Krok | Co se přesouvá | Riziko | Testy, které ho chrání |
| --- | --- | --- | --- | --- |
| 1 | **`FShipFlightModel`** (doporučený start) | Čisté `const` výpočty bez vedlejších účinků: `ComputeQuantumSpeedAt`, `ComputeQuantumArrivalAltitude`, `ComputeQuantumFuelUse`, `SegmentHitsSphere`, `LimitThrustForPilot`, `EvaluateTouchdown`, `EvaluateLanding`, `ApplyGroundFriction`, `ComputeLandedRotationStep`, `ComputeEnvironmentAcceleration`, `ComputeHeatTarget`, `ComputeGearLegPose`, `ComputeGearStowOffsetCm`, `ComputeVtolLevelStep`, `ComputeDashboardFocus`. Tuning jde v argumentu (malé struktury sestavené z UPROPERTY pawnu). Pawn UFUNCTION zůstávají jako přeposílače. | **Nejnižší:** žádný stav, žádný Tick, žádné UPROPERTY, žádné assety. Chyba = špatně předaný argument, test ji chytí číselně. | `test_ifcs_sc1` (51 kontrol, `limit_thrust_for_pilot`), `test_quantum_sc4` (45, rychlost, výška příletu, palivo, úsečka–koule), `test_landing_sc2` (58, `evaluate_touchdown` ×10), `test_landing_l5` (11), `test_planet_l3` (26, prostředí, teplo), `test_vtol_sc2b` (30, srovnání na horizont), `test_free_look` (26, přiblížení na displeje) |
| 2 | **VTOL** jako první část `UShipSystemsComponent` | Stav `bVtolMode`, `VtolBlend`; `SetVtol`, `UpdateVtol`, `ToggleVtol`, `space.Vtol`. 7 `Vtol*` UPROPERTY zůstává. | Nízké: nejmenší stavový celek, jediná závislost ven je `MasterMode`, dovnitř jen čtení a jeden zápis z `BeginQuantumJump`. | `test_vtol_sc2b` (30, vyhrazený), `test_landing_sc2`, `test_flight_modes`; snímky `vtol` |
| 3 | Zbytek `UShipSystemsComponent` | Master mode a přepínání, omezovač, G-Safe, ComStab, boost (energie), afterburner (palivo). | Střední: `MasterMode` čte VTOL, precision, quantum i rychlosti; `CameraKick` a jednorázové zvuky jdou ven (přes rozhraní pawnu). | `test_ifcs_sc1`, `test_boost_afterburner_sc1b` (33), `test_flight_modes` (33), `test_flight_hud_sc1c` (49, přes HUD gettery) |
| 4 | `UShipQuantumComponent` | Stav quantum, `UpdateQuantumTarget`, `EvaluateQuantum`, `UpdateQuantum`, `Begin/EndQuantumJump`, `UpdateQuantumTravel`, `DebugEngageQuantum`. | Střední: skok zapisuje rychlost, úhlovou rychlost, boost/afterburner/VTOL a zvuk; přímý posun lodi (`SetActorLocationAndRotation`) zůstává přes pawn. | `test_quantum_sc4` (45), `test_speed_tunnel` (21), `test_celestial_registry`; snímky `quantum` |
| 5 | `UShipLandingComponent` | Podvozek (stavový automat, póza noh), precision, `UpdateLanding` (sonda terénu), `Enter/ExitLanded`, `UpdateLandedMotion`, tření a opora podvozku. | Střední až vyšší: zapisuje rychlost a mezery k zemi, sonda sweepem (v commandletu sweepy nezasáhnou → sonda je testem pokrytá slaběji). | `test_landing_sc2` (58), `test_landing_l5` (11), `test_vtol_sc2b`; ruční přistání ve hře, snímky `landing` |
| 6 | `UShipPresentationComponent` | `UpdateCameraEffects` (kopnutí, třes, FOV, expozice, lag), `SetupAudioLayers`, `UpdateEngineAudio`, `SetupShipLights`, `UpdateShipLights`, `UpdateSpaceDust`, `UpdateViewCollection` (MPC, přední vrstva Lumenu). | Nízké v logice, ale **bez automatického pokrytí** (zvuk, světla, kamera jen očima a ušima). Globální statické proměnné v `UpdateViewCollection`. | `test_free_look`, `test_cockpit_frame` (část); jinak snímky `cockpit`, `quantum`, `ship`, `wayfarer_rooms` a poslech ve hře |
| 7 | `UShipBoardingComponent` | `SetInteriorWalk`, `LeaveSeat`, `ExitShip`, `OnBoarded`, výstupní body, kapsle, gravitace v lodi, světla jen pro interiér. | Střední: volá ho postava, `SpaceInterior` a ovladač; kolize chůze se v commandletu neověří. | `test_flight_modes` (geometrie výstupu), `test_character_l6`, `test_ship_geometry.py` (`walk_blocked`); preset `wayfarer_walk` a log |
| 8 | `UShipInputComponent` | `SetupPlayerInputComponent`, 31 handlerů, načtení input assetů, `ClearPilotInput`. | Vyšší: kód vazby vstupu headless nikdy neběží; chyba se ukáže až při hraní. Mrtvý `HandleToggleHud` pryč. | `test_ifcs_sc1`, `test_free_look`, `test_flight_modes` (jen mapování v IMC); **ruční test všech kláves** |
| 9 | `UShipDebugComponent` | 21 `Debug*` UFUNCTION a konzolové příkazy (`space.Drift`, `space.Quantum`, `space.ShipMat`…). | Nízké v logice, ale ~120 volání v testech → pawn přeposílá stejná jména. | celá sada `Tools\Test.ps1 -UE` |
| 10 | Let (IFCS) | Co zbude: `UpdateAngularMotion`, `UpdateLinearMotion`, stav rychlostí. Případně `UShipFlightComponent`. | Nejvyšší: rozbočovač, čte všechny ostatní celky. Až nakonec, až budou ostatní rozhraní hotová. | `test_ifcs_sc1`, `test_boost_afterburner_sc1b`, `test_flight_modes`, `test_planet_l3`, `test_flight_hud_sc1c` |

## Co musí autor posoudit

- Schválení pořadí; doporučuji začít krokem 1 (`FShipFlightModel`) a po něm krokem 2 (VTOL) jako vzorem pro další
  komponenty.
- Kroky 6 a 8 potřebují jeho ruční kontrolu ve hře (zvuk, světla, všechny klávesy), automatické testy je nepokryjí.
- Tuning UPROPERTY zůstávají na pawnu; jejich přesun do komponent je samostatné rozhodnutí na později (mění setup
  a import).

## Průběh (30. 9. – 1. 10. 2026, větev `pawn-split`)

Schváleno autorem 30. 9. v tomto pořadí. Každý krok: build editoru i hry, celá sada `Tools\Test.ps1 -UE` (22 testů,
1398 kontrol) zelená, dotčené snímky `-Editor` prohlédnuté, samostatný commit.

| # | Commit | Výsledek |
| --- | --- | --- |
| – | `19085bf` | Oprava mimo plán: migrace nastavení se bez `GameUserSettings.ini` zacyklila (pád UE testů v novém worktree, hra na novém počítači). |
| 1 | `fecd300` | `FShipFlightModel`: čistá matematika; výsledky bit po bitu stejné. `ComputeDashboardFocus` zůstal (čte sockety, není čistý). |
| 2 | `c3798f3` | VTOL v `UShipSystemsComponent`, `LogSpaceship` ve sdílené hlavičce. |
| 3 | `fa6795f` | Master mode, omezovač, boost, afterburner; boost a afterburner sdílejí `FShipReserve`. G-Safe a ComStab zůstaly (editovatelné přepínače). |
| 4 | `b632529` | `UShipQuantumComponent`; snímky `quantum`. |
| 5 | `01ed359` | `UShipLandingComponent` (přistání, země, podvozek, precision); sonda a viditelné nohy na pawnu; snímky `landing`, `vtol`. |
| 6 | `74ad068` | `UShipPresentationComponent`; snímky `cockpit`, `quantum`, `ship`, `wayfarer_rooms`. |
| 7 | `c66a424` | `UShipBoardingComponent`; snímky `wayfarer_walk` (vstát, ven, dovnitř, sednout). |
| 8 | `5a833be` | `UShipInputComponent`; mrtvý `HandleToggleHud` pryč. |
| 9 | `3277999` | `SpaceshipPawnDebug.cpp`: ladicí API a konzolové příkazy. |
| 10 | – | Nedělá se: jádro letu zůstává v pawnu (`ARCHITECTURE.md` kap. 2). |

Odchylky od plánu a proč:

- **Pravidlo 5** (komponenty drží ukazatele na podobjekty): prezentace, nástup a vstup místo toho čtou pawn přímo
  jako jeho `friend`. Čtou desítky jeho hodnot a dílů; struktury argumentů by byly delší než kód. Systémy, quantum
  a přistání berou tuning jako malé struktury.
- **Krok 9:** místo `UShipDebugComponent` samostatný soubor. Komponenta by byla 22 přeposílačů bez vlastního stavu.
- **Krok 10:** let se nepřesouvá; komponenta by jen přenesla kód, který čte všechno a zapisuje polohu a rychlost.
- Balení: jednou po kroku 9 do `C:\gamespace\Builds_audit\Gamespace` (autor 1. 10.: druhá session nebalí do
  `Builds`); kroky 6 a 8 ověří autor ve hře.

Výsledek: `SpaceshipPawn.cpp` 3 978 → 1 762 řádků, `SpaceshipPawn.h` 2 262 → 2 031 (hlavička nese tuning
UPROPERTY a přeposílače, to je záměr). Chování beze změny podle testů a snímků.

## Mimo tento plán

- Pevný časový krok simulace (odloženo). `SpaceUserSettings` s `const_cast` (opravit při nejbližší změně nastavení).
- `SpaceFlightHud.cpp` (~3 000 řádků) je prezentační vrstva s oddělenou logikou stavu (`MakeState`);
  audit ji nevidí jako riziko, nerozdělovat.
