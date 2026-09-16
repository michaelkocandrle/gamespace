# gamespace

Sci-fi space game prototype. Unreal Engine 5.8, C++ game module `gamespace`.

## Repository layout

```
Config/                 Project .ini files
Content/
  Ships/                Ship meshes, materials, Blueprints
  Environments/         Stations, asteroids, props
  Planets/              Planet bodies, atmospheres
  UI/                   Widgets, HUD
  Blueprints/           Gameplay Blueprints that are not ship-specific
  Materials/            Shared materials and material functions
  VFX/                  Niagara systems
  Input/                Enhanced Input assets (IMC_Spaceship, IA_*)
  Maps/                 Levels
Source/gamespace/       C++ game module
```

`Input/` and `Maps/` are not in the original folder list but the input assets and test
level need somewhere to live.

### Git LFS

`.gitattributes` routes `*.uasset`, `*.umap` and common source-art formats through Git LFS.
Run once per machine, before cloning or pushing:

```bash
git lfs install
```

## SpaceshipPawn

`Source/gamespace/SpaceshipPawn.h` / `.cpp` - a player-flown ship with 6 degrees of freedom.

### Components

| Component     | Purpose                                                         |
| ------------- | --------------------------------------------------------------- |
| `HullCollision` | Root. Box 200 x 100 x 35 cm, `Pawn` profile - the ship's only collision. Unscaled, so the cameras do not inherit the hull's scale |
| `Hull`        | `/Engine/BasicShapes/Cube` stretched to 2.0 x 1.0 x 0.35, visual only |
| `CameraBoom`  | 900 cm spring arm, mild lag, collision test on: pulls the camera in rather than letting it sink into an asteroid |
| `ChaseCamera` | Third-person camera                                              |
| `CockpitCamera` | Nose view at (90, 0, 15), FOV 90, inactive until toggled; hides the hull from the player's own view |
| `EngineAudio` | Engine loop, not spatialised, started and stopped from `Tick` |

### Flight model

Motion is integrated by hand in `Tick` rather than simulated by Chaos, which keeps the feel
predictable and cheap to tune.

- Thrust, strafe and lift are accelerations applied along the hull's local axes and accumulated
  into `LinearVelocity` (world space, cm/s).
- **Environment (L3).** Every tick the ship samples the nearest `ACelestialBody`
  (`SampleEnvironment`). Everything blends smoothly with altitude:
  - **Space** (above the atmosphere): no drag, no gravity - true Newtonian drift
    (`SpaceLinearDamping` 0). The ship keeps flying until you brake with S.
  - **Atmosphere**: drag `LinearDamping` (0.4/s) plus `QuadraticDrag` (4e-5 per cm, grows with
    speed squared), both multiplied by air density (0 at the top, 1 at sea level), and gravity
    along the local down (`GravityScale`).
  - At sea level that gives ~62 m/s cruise at full thrust, ~116 m/s with boost, ~13 m/s falling
    with the engines off. `ComputeEnvironmentAcceleration` is the exact formula.
  - **Entry heat** (`Spaceship|Entry`): density x (speed / 100 m/s)^3, from `HeatOnset` to
    `HeatFull`, smoothed; shakes the camera (`HeatShakeCm`) and shows on the HUD.
- `MaxSpeed` is a hard cap.
- Pitch, yaw and roll drive a target rate that `AngularVelocity` eases towards over
  `AngularResponsiveness`, then apply as a *local* rotation. Local rotation is what makes this
  6DOF rather than an aircraft glued to a horizon, and it avoids gimbal lock at the poles.
- Movement is swept (`bSweepMovement`), and a blocking hit projects velocity onto the surface
  plane so the ship slides instead of stalling. **A sweep only tests the root component**, which
  is why `HullCollision` has to be the root: with a plain scene component there the ship used to
  fly straight through the planet.
- **Mouse steering is a virtual joystick.** Mouse movement pushes the stick
  (`MouseSensitivity`, deflection per pixel), which springs back to centre at
  `MouseRecenterRate`. Full turn rate at ~130 px/s of mouse movement. This keeps steering
  independent of frame rate; turning pixels-per-frame straight into a turn rate made the ship
  turn half as fast at 120 FPS as at 60. The turn rate itself is capped by `PitchRate` (100),
  `YawRate` (75) and `RollRate` (150) deg/s.
- **Engine sound** follows the controls, not the speed: main thrust counts fully, strafe and lift
  60 %, roll 30 %. Volume, pitch (narrow range, 0.8-1.05, +0.15 boost) and a low-pass filter
  (400 Hz at light load up to 2 kHz at full) spool at `EngineSpoolRate`, and the sound is stopped
  outright below 1 % load, so a ship at rest is silent. The sound is a procedural placeholder:
  low-pass filtered noise with a soft narrow-band hum, no pure tones and nothing above ~1 kHz,
  in a seamless 8 s loop. An earlier version with sine partials and hiss sounded like a vacuum
  cleaner - its perceived loudness centred at 1.3 kHz, where the ear is most sensitive. Rebuilt with
  `python Tools/Assets/generate_engine_sound.py Intermediate/GeneratedAssets/engine_loop.wav`
  and then `.\Tools\run_editor_python.ps1 Tools\Assets\build_ship_audio.py`. A real recording
  can be reimported onto `/Game/Ships/Audio/SW_EngineLoop`.

- **Speed**: in space `MaxSpeed` (120 m/s, 300 m/s with boost) is the only limit; in the
  atmosphere drag sets cruise speed (see above).
- **Boost** (`BoostMultiplier`, default 2.5) multiplies forward thrust and the speed cap while
  held. Reverse, strafe and lift are unaffected. On release,
  speed above the normal cap bleeds off at `OverspeedDecay` instead of snapping down.

All tuning values are `EditAnywhere` under the `Spaceship|Flight` and `Spaceship|Handling`
categories.

### Landing (L5)

Low over a planet (below `LandingProbeAltitudeM`, 30 m) the ship probes the ground every frame:
a sweep of the hull straight down gives the gap, and `ACelestialBody::GetSurfaceFrame` the
terrain normal averaged over `LandingFootprintRadiusCm` (1.5 m).

- **Touchdown** (`Settling`): gap <= 60 cm, slope <= `MaxLandingSlopeDeg` (25), speed <= 3 m/s,
  hull tilted <= 30 degrees against the terrain, no thrust and no upward lift. All of it must
  hold for `LandingConfirmSeconds` (0.75 s) without a break; a bounce restarts the window.
- **Landed**: flight physics and steering are off. The ship eases its up vector onto the terrain
  normal, keeping its heading (`LandingAlignRate` 6: ~95 % in 0.5 s), sweeps the hull down onto
  the collision and eases onto it, and leftover sliding dies out (`LandedBrakeRate`).
- **Takeoff**: W, S or Space at half input or more. Space lifts straight off; W on a slope can
  push the nose into the hill. For `TakeoffCooldownSeconds` (0.75 s) no new touchdown.
- **Friction while touching the ground** (not landed yet, or on ground too steep to land):
  Coulomb friction `GroundFriction` 0.5 against the gravity pressing the ship down, so it stands
  still on slopes up to ~26.5 degrees and slides on steeper ones.
- Steeper than 25 degrees: touchdown is refused (HUD `TOO STEEP`); the ship slides.

Headless: `Tools/Tests/test_landing_l5.py`. Under a 1.5 m footprint Veyra's slope has a median
of 15 degrees; 87 % of the surface is landable, 4.5 % is steeper than 30 degrees.

### Controls

| Action       | Keyboard / mouse           | Gamepad              |
| ------------ | -------------------------- | -------------------- |
| Thrust       | `W` / `S`                  | Left stick Y         |
| Strafe       | `D` / `A`                  | Left stick X         |
| Lift         | `Space` / `Left Ctrl`      | -                    |
| Roll         | `E` / `Q`                  | Shoulder buttons     |
| Pitch / yaw  | Mouse                      | Right stick          |
| Boost (hold) | `Left Shift`               | -                    |
| Camera       | `C` (chase / cockpit)      | -                    |
| Get out      | `F` (only when LANDED)     | -                    |
| Free look    | hold right mouse button    | -                    |

**Free look** (Elite-style head look): while the right mouse button is held, the ship keeps its
heading (pitch/yaw rotation stops at once; roll keys and the flight path carry on) and the mouse
turns only the camera - the chase boom swings around the ship, the cockpit camera turns like a
head. `FreeLookSensitivity` 0.36 deg per mouse count, limits `FreeLookMaxYawDeg` 110 and
`FreeLookMaxPitchDeg` 70, smoothed at `FreeLookFollowRate`. On release the camera eases back
(`FreeLookReturnRate` 6: ~95 % in 0.5 s) while steering works again immediately, from a centred
stick. The HUD shows FREE LOOK in the middle of the screen and the camera angles on the CAMERA
line. Input: `IA_FreeLook` (bool, held), added to `IMC_Spaceship` by
`Tools/Assets/add_free_look_input.py`; headless test `Tools/Tests/test_free_look.py`.

### Enhanced Input

The pawn resolves its mapping context and actions in this order, first hit wins:

1. Whatever is assigned on the Blueprint child (`Spaceship|Input` category).
2. Assets loaded from `/Game/Input`: `IMC_Spaceship`, `IA_Thrust`, `IA_Strafe`, `IA_Lift`,
   `IA_Roll`, `IA_Look`, `IA_ToggleCamera`, `IA_Boost`, plus `IMC_SpaceshipMouse` and
   `IA_LookMouse`.

The mouse has its own action and context because a mouse delta (pixels this frame) and a stick
(a position) need different handling, and an action value does not say which key produced it.
`IMC_SpaceshipMouse` is added one priority above `IMC_Spaceship`; Enhanced Input then skips the
mouse mapping in `IMC_Spaceship`, so `IA_Look` only carries the gamepad stick.
3. An equivalent set built procedurally at possession time, so the pawn flies out of the box.

Step 3 logs a warning under `LogSpaceship`. It exists so the pawn is testable immediately -
`.uasset` is a binary editor format and cannot be authored outside the editor, so the assets in
step 2 have to be created there. Do that when you want designers to rebind keys without
recompiling.

#### Authoring the assets in the editor

In the Content Browser, in `Content/Input`, right-click → **Input** →

| Asset             | Type                  | Value Type       |
| ----------------- | --------------------- | ---------------- |
| `IA_Thrust`       | Input Action          | Axis1D (float)   |
| `IA_Strafe`       | Input Action          | Axis1D (float)   |
| `IA_Lift`         | Input Action          | Axis1D (float)   |
| `IA_Roll`         | Input Action          | Axis1D (float)   |
| `IA_Look`         | Input Action          | Axis2D (Vector2D)|
| `IMC_Spaceship`   | Input Mapping Context | -                |

Then open `IMC_Spaceship` and add the mappings from the controls table. Every negative direction
(`S`, `A`, `Left Ctrl`, `Q`, left shoulder) needs a **Negate** modifier on that key mapping.
`IA_Look` maps to the `Mouse XY 2D-Axis` key and to `Gamepad Right Thumbstick 2D-Axis`.

The names above are exactly what `SpaceshipPawn.cpp` looks for, so once they exist the pawn picks
them up with no further wiring and the warning disappears.

## PlayerCharacter (on foot)

`Source/gamespace/PlayerCharacter.h`, `PlayerCharacterAnimInstance.h` - `APlayerCharacter`, the
player outside the ship. Placeholder art: the UE5 Mannequin pack (`SKM_Manny_Simple` and the
Unarmed animations), installed unchanged at `/Game/Characters/Mannequins` by
`python Tools/Assets/install_mannequin_pack.py` (a copy of the engine's Characters template pack).

| Action          | Keyboard / mouse |
| --------------- | ---------------- |
| Move            | `W` `A` `S` `D`  |
| Look            | Mouse            |
| Jump            | `Space`          |
| Sprint (hold)   | `Left Shift`     |
| Board ship      | `F` within 4 m of a landed ship |

Input: `IMC_Character` with `IA_CharMove`, `IA_CharLook`, `IA_CharJump`, `IA_CharSprint` and the
shared `IA_Interact` (F, Pressed), created by `Tools/Assets/add_character_input.py`, which also
appended F to `IMC_Spaceship`. Each pawn removes its mapping contexts when it is unpossessed, so
the ship's mouse context never swallows the character's mouse look.

- **Gravity** comes from the nearest celestial body every tick: `SetGravityDirection(-Up)` and
  `GravityScale` = body gravity / world gravity (0.61 on Veyra). Character Movement (UE 5.4+)
  walks, jumps, finds floors and stays upright in that frame by itself. Walk 2.5 m/s, sprint
  5.5 m/s, jump 4.5 m/s (~1.7 m high at 6 m/s^2).
- **View**: control rotation is world-space and the camera manager clamps its world pitch and
  roll, which breaks when up is not world Z. So the look yaw/pitch live in a gravity frame carried
  along the planet by parallel transport (no twist after a full lap, tested), and the camera boom
  (absolute rotation) is rotated to it directly. Movement input is relative to that view.
- **Animation**: `UPlayerCharacterAnimInstance` evaluates the pose natively (no Animation
  Blueprint): idle / walk / jog blended by ground speed in the gravity plane, one shared phase so
  the feet stay in step, play rate matched to speed (reference speeds 3 / 6 m/s read from
  `BS_Idle_Walk_Run`), plus jump start, fall loop and a landing blend. The template ABP and foot
  IK rig assume world -Z gravity, hence native.
- **Foot IK**: the capsule stands on the coarse collision tiles (2.4 m cells); the visible terrain
  has 33 cm cells. Measured difference: median 3.9 cm, 99 % under 18 cm, max 25 cm. Each foot's
  ground is read from the planet's height field (what the visible mesh is built from), the pelvis
  drops up to 40 cm for the lower foot, both legs get two-bone IK in their animated bend plane,
  feet tilt with the slope up to 30 degrees. Off when not standing on planet terrain.
- **Ship exit / boarding**: on a LANDED ship, F spawns the character at the hull mesh socket
  `Exit` (`SOCKET_Exit` from Blender) or, without one, 80 cm right of the hull, placed on the
  terrain, and possesses it. F within `BoardingRangeCm` (4 m from the hull box) of a landed ship
  possesses the ship again and removes the character (0.75 s cooldown after getting out).
- **HUD**: `MODE` shows IN SHIP / ON FOOT with the F prompt; on foot also MOVE, GRAVITY, FOOT IK.

Headless: `Tools/Tests/test_character_l6.py` (assets and input, gravity frame transport, exit
placement, native pose evaluation, foot IK with forced ground, terrain vs collision error).

## Ship art pipeline

The real ship replaces the placeholder cube through Higgsfield (AI 3D, GLB) -> Blender -> FBX ->
Unreal. The step-by-step guide, folder layout (`ArtSource/Ships/<Ship>/` for source files,
`Content/Ships/<Ship>/` for assets), naming (`SM_Ship_<Ship>`, `UCX_`, `SOCKET_`, `_LOD<n>`),
model checklist and the pawn changes the switch needs are in
[Docs/Ships/ShipPipeline.md](Docs/Ships/ShipPipeline.md).

`Tools/Blender/gamespace_ship_export.py` is a Blender add-on (sidebar tab "Gamespace") and
command-line script that validates a ship and exports one FBX per mesh plus a JSON manifest
with sizes, socket positions in Unreal centimetres and suggested pawn settings. Its validation
core runs without Blender: `python Tools/Blender/tests/test_ship_export_core.py`.

The manifest can be checked on its own before any import
(`python Tools/Blender/gamespace_ship_export.py --check-manifest <manifest.json>`).
`Tools/Assets/import_ship.py` (editor closed, `GAMESPACE_SHIP_MANIFEST` set) imports the FBX
files, checks them against the manifest and writes the manifest's suggested settings into
`BP_Ship_<Ship>`; run with plain Python it is a dry run that prints the plan
(`python Tools/Assets/tests/test_import_ship_plan.py` tests that part). It has not run inside
Unreal yet.

The player character pipeline (Higgsfield rig vs. UE5 Mannequin skeleton, camera and animation
decisions, folder layout and naming) is in
[Docs/Characters/CharacterPipeline.md](Docs/Characters/CharacterPipeline.md).

## Script-authored assets

New Input Actions, Mapping Contexts, Data Assets, Curve Tables and Data Tables can be created
from Python instead of by hand: [`Content/Python/gamespace_assets.py`](Content/Python/gamespace_assets.py).
Its module docstring holds the full reference.

```python
import gamespace_assets as ga

boost = ga.input_action("/Game/Input/IA_Boost", "bool")
look = ga.existing("/Game/Input/IA_Look")        # reference only, never modified
ga.mapping_context("/Game/Input/IMC_Debug", [
    ga.Map(boost, "LeftShift", triggers=["Pressed"]),
    ga.Map(look, "Down", swizzle="YXZ", negate=True),
])
```

Run it headless with the editor **closed**:

```
.\Tools\run_editor_python.ps1 path\to\script.py
```

The runner refuses to start while an editor has this project open, because that editor would
overwrite the script's changes with its own in-memory copies on the next save. With the editor
open, enable the *Python Editor Script Plugin* and use **Tools → Execute Python Script** instead.

**Existing assets are never touched by default.** Every function takes `on_exists`:
`"error"` (default, raises), `"skip"` (returns the asset unmodified) or `"update"`
(explicit opt-in; for mapping contexts and data tables it *replaces* the contents).

To extend an existing mapping context without replacing it, use `ga.add_mappings()`: it
appends, skips mappings that already exist, and refuses to save if any original mapping changed.
`Tools/Assets/add_camera_and_boost_input.py` is the worked example.

### What still needs the editor

| Asset / feature | Why |
| --- | --- |
| `CurveFloat`, `CurveVector`, `CurveLinearColor` keys | The key data is a bare `UPROPERTY()` that Python cannot see, and the CSV/JSON import on `UCurveBase` is not a `UFUNCTION`. Use a `CurveTable` instead, or add a small editor-only C++ function that wraps `ImportFromJSONString`. |
| Cubic / weighted curve tangents | `CurveTable` keys from script are simple curves, linear interpolation only. |
| Any property declared as plain `UPROPERTY()` | Python only reaches `EditAnywhere` / `Blueprint*` properties. Applies to our own C++ classes too. |
| Player Mappable Key Settings on mappings | Not tested. |


`Source/gamespace/SpaceGameMode.h` / `.cpp` - `AGameModeBase` with `DefaultPawnClass` set to
`ASpaceshipPawn`. It is the project-wide default, wired up in `Config/DefaultEngine.ini`:

```ini
[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Game/Maps/TestSpace.TestSpace
GameDefaultMap=/Game/Maps/TestSpace.TestSpace
GlobalDefaultGameMode=/Script/gamespace.SpaceGameMode
```

Any level without a World Settings override therefore spawns a flyable ship at its
`PlayerStart`. A Blueprint child of `SpaceGameMode` can still override the pawn per level.

## SpaceDebugHUD

`AHUD` subclass set as `HUDClass` on `SpaceGameMode`. Draws speed (m/s and km/h), throttle
(signed %, the raw `IA_Thrust` value), boost state and active camera as plain canvas text in
the top-left corner. A tuning aid, not UMG - replace it when a real HUD exists.

The `LANDING` line shows `LANDED` (green), `TOUCHDOWN nn %` while settling (yellow), or below
30 m the gap, slope and tilt with the reason touchdown is not possible (`too high`, `TOO STEEP`,
`too fast`, `level the ship`, `engines on`, `taking off`). The `TERRAIN` line counts collision
warm-ups.

The `FLIGHT` line shows the regime (`ORBIT` / `ATMOSPHERE` / `SURFACE`, or `DEEP SPACE` with no
body around), altitude above the terrain (AGL) and above sea level (ASL), air density in %,
gravity, and `HEAT` in % during a hot entry (the line turns orange-red).

The `TARGET` line shows the nearest `ACelestialBody`: its name, the distance to its surface, and
the time to reach it at the current closing speed (`--:--` when not approaching).

The `ORIGIN` line shows how far the ship is from the current world origin and where that origin
is in absolute km; `REBASE` shows how many origin shifts have happened, how long ago and how
long the last one took.

## Large world coordinates and origin rebasing

**Large World Coordinates are always on in UE 5.1+.** There is no project setting for it:
`FVector`/`FTransform` are `double`, the old per-world `bEnableLargeWorlds` flag is deprecated
("As of UE 5.1 all worlds are large"), `UE_USE_UE4_WORLD_MAX` is 0 and the world is valid up to
~44 million km from the origin. Chaos physics also uses `double` (`Chaos::FReal`).
`ASpaceshipPawn` keeps `LinearVelocity`/`AngularVelocity` as `FVector`, and all actor locations
(including `ACelestialBody`) are standard double-precision transforms.

**Origin rebasing** (`USpaceOriginRebasingSubsystem`) still moves the world origin to the ship
once it is `RebaseDistanceKm` (default 10) away, through the engine's own
`UWorld::RequestNewWorldOrigin`. It keeps coordinates small for what remains single precision:
mesh vertices in component space, GPU particles, material world-position maths. Settings are
on `ASpaceGameMode` (`Space|Origin Rebasing`); during PIE select *SpaceGameMode* in the
Outliner to change them live.

Measured in PIE: a rebase takes 0.2-1.5 ms; positions, velocities, relative distances and
collision are unchanged afterwards (drift 0.000000 cm).

Limits to know:
- `UWorld::OriginLocation` is `FIntVector` (int32 cm), so the origin can only follow to
  ±21,474 km from absolute zero. Beyond that rebasing stops with one warning; the world keeps
  working in plain double coordinates (verified at 30,000 km).
- Chaos cannot shift its physics scene (`FPhysScene_Chaos::SupportsOriginShifting()` is false),
  so the engine teleports every physics body one by one. Cheap now; it scales with body count.
- Local only, not network-aware; editor worlds never rebase.

Console commands (open the console in PIE with the key under Esc):

| Command | Effect |
| ------- | ------ |
| `space.TeleportForwardKm <km>` | Moves the ship along its nose |
| `space.TeleportAbsoluteKm <x> <y> <z>` | Moves the ship to an absolute position, independent of rebasing |
| `space.RebaseNow` | Moves the origin to the ship on the next tick |
| `space.PrintOrigin` | Logs origin and ship position (`LogSpaceOrigin`) |

Teleports snap the chase camera to the ship (`ASpaceshipPawn::SnapCameraToShip`); camera lag is
also capped at 15 m, since at orbital speeds it would otherwise trail kilometres behind.

## CelestialBody

`Source/gamespace/CelestialBody.h` - `ACelestialBody`, a named body in space (planet, moon,
station): a `Body` static mesh component and a `DisplayName`. `GetSurfaceDistance()` measures
to the mesh's bounding sphere - exact for spheres, an underestimate for elongated shapes.

`SampleEnvironment(Location)` returns an `FCelestialEnvironment`: altitude above terrain and sea
level, local up, air density, gravity, sky colours and amount, and the flight regime
(`ORBIT` / `ATMOSPHERE` / `SURFACE`). The base class has none; `AQuadSpherePlanet` does.
`ACelestialBody::FindNearest` is what the ship, the sky dome and the HUD use.

## QuadSpherePlanet (terrain L2, atmosphere L3)

`Source/gamespace/QuadSpherePlanet.h`, `PlanetTerrain.h` - `AQuadSpherePlanet`, an
`ACelestialBody` whose surface is a quad-sphere: six cube faces projected onto the sphere
(equi-angular mapping), each a quadtree of `UProceduralMeshComponent` tiles.

- **Height**: fBm of `PlanetTerrain::GradientNoise3D` - improved Perlin noise entirely in double
  precision, with a hashed (never repeating) lattice - sampled on the unit sphere. Veyra: radius
  25 km, amplitude 800 m, largest features 8 km, 12 octaves (smallest ~4 m); relief up to about
  +/-1.6 km, typically +/-260 m. Normals come from the height field, so they match across LODs.
- **LOD**: a tile splits when the camera is within `LodDistanceFactor` (1.5) tile sizes of its
  bounds, merges with 15 % hysteresis; 48x48 cells, finest tiles ~10 m (`LeafTileSizeM` 16),
  depth 12. Tile bounds use the height at the tile centre plus how much the terrain can vary
  inside a tile of that size (octaves combined as root of sum of squares), cached per node - not
  the planet-wide maximum height, which on a mountainous planet made every tile look near.
  Tiles below the horizon (behind a sphere under the lowest terrain) are not split.
- **Tile counts** (headless, `CountLodTilesFrom`, descending over the start point): 72 at 20 km,
  183 at 5 km, 309 at 1 km, 510 at 200 m, 714 at 30 m, 750 at 5 m (~3.5 M triangles). The L2
  tuning (32 cells, factor 3, 4 m leaves) would need 1983 tiles at 5 m on this planet.
- **No holes / pops / cracks**: parents stay visible until all four children are built (and
  children until the parent is); vertices carry their parent-grid position in UV1/UV2 and the
  material geomorphs towards it with camera distance; skirts (8 % of the tile size) hang under
  tile edges.
- **Precision**: each tile component sits at the tile centre (double transform); vertices are
  relative to it, so float mesh data only holds tile-sized values.
- **Threads**: tiles build on the thread pool; component creation is capped per frame by count
  and time budget (`UploadBudgetMs`), cache eviction by `MaxEvictionsPerFrame`, and LOD
  selection only reruns when the camera moved or tiles changed.
- **Collision**: separate invisible collision tiles (32 cells) around the ship. Radius
  `CollisionMinRadiusM` (60 m) + speed x `CollisionLookaheadSeconds` (2.5 s), up to 2 km; tile
  size radius / 2, at least 64 m, so there are always ~25-50 bodies. When the size changes, the
  old tiles stay until the new set is built. Below `CollisionWarmupAltitudeM` (150 m), missing
  collision tiles right under the ship (within 15 m) are built on the game thread with synchronous
  physics cooking (~1.6 ms to build, at most 2 per frame), so a touchdown never meets a tile
  whose collision is still cooking. The inherited `Body` is a hidden sphere just under
  the lowest possible terrain as a safety net. `GetSurfaceDistance` uses the exact height field.
- **Atmosphere and gravity** (`Planet|Atmosphere`): `AtmosphereHeightKm` 12, exponential density
  with `AtmosphereScaleHeightKm` 3 (reaching exactly 0 at the top); gravity `SurfaceGravity`
  6 m/s^2, inverse square, faded in from 0 at the top to full at 40 % of the height; sky colour
  amount rises faster than density (18 % at 8 km, 53 % at 5 km, 99 % at 1 km). Regime `SURFACE`
  below `SurfaceRegimeAltitudeM` (500 m) above the terrain.
- **Debug**: HUD `FLIGHT` and `TERRAIN` lines; `space.TerrainDebugLOD 1` tints tiles by depth;
  `space.TerrainFreezeLOD 1` freezes LOD updates.

L2 measurements (500 m planet, PIE): ~89 fps from orbit, ~66 fps at 30 m with ~1000 visible
tiles, ~54 fps flying 20 m above the surface. The 25 km planet is not measured in PIE yet.

Headless checks: `.\Tools\run_editor_python.ps1 Tools\Tests\test_planet_l3.py` - noise
determinism, range and smoothness, tile counts per altitude, atmosphere curves, and simulated
descents with the ship's real drag/gravity/heat code.

When measuring in an editor that is not in the foreground, pass
`-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False`,
otherwise the editor throttles itself to ~3 fps.

## TestSpace

`Content/Maps/TestSpace` - the test level, and the editor/game startup map. Non-partitioned.
Its space look is built by `Tools/Assets/build_space_scene.py` (see below).

| Actor              | Notes |
| ------------------ | ----- |
| `Sun`              | Directional light, movable, intensity 8, pitch -39 / yaw 45: from behind the player's left shoulder |
| `SkyLight`         | Movable, real-time capture, intensity 0.35. Captures the star dome, so ambient light is near zero |
| `StarfieldSky`     | `ASkyDome`: 1000 km sphere that follows the camera, with `M_Starfield_Sky`: unlit, *Is Sky*, procedural stars plus a Milky Way glow cubemap |
| `Planet_Veyra`     | `AQuadSpherePlanet`, radius 25 km, centre 45 km ahead of the start (start is 20 km above sea level, 8 km above the atmosphere) |
| `PP_SpaceExposure` | Unbound post-process volume fixing exposure at EV100 3 |
| `PlayerStart`      | At (0, 0, 300), facing +X towards the planet |
| `Asteroid_00-15`   | Scaled cubes scattered 30-260 m out |

The asteroids are placeholder reference geometry, not a design decision. Without something to
fly past, an empty sky gives no sense of motion whatsoever. Delete them once real props exist.

**Distances.** In space the ship accelerates to 120 m/s (300 m/s with boost). Simulated boost
dive straight down: atmosphere after ~28 s, entry heat between ~8 and ~3 km, ground after ~3.5
min if the throttle is released at 3 km. The planet fills ~67 degrees of the 90 degree view.

**Why no SkyAtmosphere.** It simulates an Earth-like atmosphere with the player at sea level:
a sunset sky over a black ground plane, which is the opposite of space.

**Why fixed exposure.** Auto exposure would brighten the mostly black sky until the stars bloom
out, then darken again whenever a lit asteroid fills the view.

**Why procedural stars.** A star texture cannot stay sharp: a cubemap texel is larger than a
screen pixel, and filtering turns points into smudges. `M_Starfield_Sky` computes the stars per
pixel in a Custom HLSL node (hashed cells on the cube faces, three layers, Gaussian points sized
in screen pixels), so they are ~1 px points at any resolution. Only the soft Milky Way glow
comes from a texture. What is left of the softness is TSR, the temporal anti-aliasing, which
softens anything smaller than a pixel. Material parameters: `StarBrightness`, `StarDensity`,
`GlowBrightness`. The sky light still captures the dome, but only for ambient light, which is
near zero.

**Why the dome follows the camera.** The stars are looked up by view direction, so the dome's
position and size do not change how they look. A fixed dome could be flown out of; `ASkyDome`
re-centres on the camera every frame, so the sky works at any distance and across rebases
(verified 20 km out after a rebase). Its radius (`DomeRadiusKm`, 1000) must exceed the distance
to the farthest body that should be visible, because anything beyond it is hidden. 1000 km
is plenty: Veyra is 45 km away and its horizon, even from the start, is under 40 km.

**Atmosphere in the sky.** `ASkyDome` samples the environment at the camera each frame and sets
`AtmosphereAmount`, `PlanetUp`, `SkyZenithColor`, `SkyHorizonColor` and `SkyBrightness` on a
dynamic instance of `M_Starfield_Sky`. The material blends a horizon-to-zenith gradient over the
stars; stars fade with the square of the remaining space. The sky does not know where the sun is
yet: the night side is blue too.

**Checking visuals headlessly.** A standalone `-game` run of uncooked content renders newly
created materials with the default material, even with their shaders compiled. Judge the look
in PIE, not in `-game`.

### Rebuilding the scene

Editor closed:

```
python Tools/Assets/generate_milky_way_glow.py Intermediate/GeneratedAssets/milky_way_glow.hdr
.\Tools\run_editor_python.ps1 Tools\Assets\build_space_scene.py
```

The generator runs in the system Python with numpy and is deterministic. The build script is
safe to re-run: it rebuilds its own two materials, finds its actors by label, and imports the
glow cubemap and planet mesh only if they are missing. Brightness, exposure, planet size and
position are constants at the top of `build_space_scene.py`.

Assets it creates:

| Asset | What |
| ----- | ---- |
| `Environments/Space/T_MilkyWay_Glow_Cube` | Diffuse Milky Way band, imported from a long-lat HDR as a cubemap |
| `Environments/Space/M_Starfield_Sky`  | Sky material: procedural stars + glow |
| `Planets/SM_PlanetSphere`             | 65k-triangle Nanite sphere, radius 100 cm, one sphere collision; now only the planet's hidden safety sphere |
| `Planets/M_Planet_Terrain`            | Terrain tile material: noise colours and polar caps from the planet-local position, geomorphing via World Position Offset, LOD debug tint |
| `Planets/M_Planet_Test`               | Material of the old single-sphere planet; no longer used by the script |

### Smart App Control

Smart App Control used to block freshly built DLLs and any change to `gamespace.Build.cs`. The
user has since turned it off, so module dependencies can be added again (ProceduralMeshComponent
was the first). If a build or editor start ever fails with Code Integrity event 3077 or
0x800711C7, that is the cause.

## Testing in the editor

1. Close the editor if it is open, then build the **gamespaceEditor** target (Live Coding cannot
   pick up newly added source files):

   ```
   "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" gamespaceEditor Win64 Development -Project="C:\gamespace\gamespace\gamespace.uproject" -WaitMutex
   ```

2. Open the project. It starts on `TestSpace`.
3. Press Play. `W` to accelerate, mouse to steer, `Q` / `E` to roll.

Nothing needs placing by hand: the game mode supplies the pawn and the level has a
`PlayerStart`.
