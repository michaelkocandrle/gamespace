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
- `LinearDamping` bleeds velocity off each second. This is the "flight assist" of Elite-style
  flight models - **set it to 0 for true Newtonian drift**.
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

- **Cruise speed is set by damping, not by `MaxSpeed`.** With flight assist on, speed settles at
  `ThrustAcceleration / LinearDamping` - 4000 / 1.2 = ~33 m/s with the defaults - long before the
  120 m/s cap. Tune those two to change how fast the ship feels; `MaxSpeed` is only a safety cap.
- **Boost** (`BoostMultiplier`, default 2.5) multiplies forward thrust and the speed cap while
  held, so cruise speed goes to ~83 m/s. Reverse, strafe and lift are unaffected. On release,
  speed above the normal cap bleeds off at `OverspeedDecay` instead of snapping down.

All tuning values are `EditAnywhere` under the `Spaceship|Flight` and `Spaceship|Handling`
categories.

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

The `TARGET` line shows the nearest `ACelestialBody`: its name, the distance to its surface, and
the time to reach it at the current closing speed (`--:--` when not approaching).

## CelestialBody

`Source/gamespace/CelestialBody.h` - `ACelestialBody`, a named body in space (planet, moon,
station): a `Body` static mesh component and a `DisplayName`. `GetSurfaceDistance()` measures
to the mesh's bounding sphere - exact for spheres, an underestimate for elongated shapes.

## TestSpace

`Content/Maps/TestSpace` - the test level, and the editor/game startup map. Non-partitioned.
Its space look is built by `Tools/Assets/build_space_scene.py` (see below).

| Actor              | Notes |
| ------------------ | ----- |
| `Sun`              | Directional light, movable, intensity 8, pitch -39 / yaw 45: from behind the player's left shoulder |
| `SkyLight`         | Movable, real-time capture, intensity 0.35. Captures the star dome, so ambient light is near zero |
| `StarfieldSky`     | 8 km engine sphere with `M_Starfield_Sky`: unlit, *Is Sky*, procedural stars plus a Milky Way glow cubemap |
| `Planet_Veyra`     | `ACelestialBody`, radius 500 m, surface 2.5 km ahead of the start |
| `PP_SpaceExposure` | Unbound post-process volume fixing exposure at EV100 3 |
| `PlayerStart`      | At (0, 0, 300), facing +X towards the planet |
| `Asteroid_00-15`   | Scaled cubes scattered 30-260 m out |

The asteroids are placeholder reference geometry, not a design decision. Without something to
fly past, an empty sky gives no sense of motion whatsoever. Delete them once real props exist.

**Distances.** Cruise speed is ~33 m/s, so the planet surface is ~76 s away, ~30 s with boost.
It starts at ~19 degrees across in the 90 degree view.

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

**Why an 8 km dome.** The stars are looked up by view direction, so the dome's size does not
change how they look; it only has to enclose everything you fly to. 8 km is verified in PIE.
Flying more than 8 km from the origin takes you outside it.

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
| `Planets/SM_PlanetSphere`             | 65k-triangle Nanite sphere, radius 100 cm, one sphere collision |
| `Planets/M_Planet_Test`               | Noise-based two-tone terrain with polar caps, colour parameters |

### Smart App Control

This machine runs Windows Smart App Control, which judges every freshly built unsigned DLL by
reputation. Occasionally it blocks `UnrealEditor-gamespace.dll` (Code Integrity event 3077),
and the editor reports that *the game module 'gamespace' could not be loaded*. So far a retry
has loaded the same file fine. `run_editor_python.ps1` reports this as a failure rather than
silently succeeding.

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
