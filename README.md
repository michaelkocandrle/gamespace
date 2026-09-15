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
| `ShipRoot`    | Unscaled pivot so the camera does not inherit the hull's scale   |
| `Hull`        | `/Engine/BasicShapes/Cube` stretched to 2.0 x 1.0 x 0.35         |
| `CameraBoom`  | 900 cm spring arm, no collision test, mild lag                   |
| `ChaseCamera` | Third-person camera                                              |

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
  plane so the ship slides instead of stalling.

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

### Enhanced Input

The pawn resolves its mapping context and actions in this order, first hit wins:

1. Whatever is assigned on the Blueprint child (`Spaceship|Input` category).
2. Assets loaded from `/Game/Input`: `IMC_Spaceship`, `IA_Thrust`, `IA_Strafe`, `IA_Lift`,
   `IA_Roll`, `IA_Look`.
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

## SpaceGameMode

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

## TestSpace

`Content/Maps/TestSpace` - the test level, and the editor/game startup map. Non-partitioned,
20 actors:

| Actor            | Notes                                                                |
| ---------------- | -------------------------------------------------------------------- |
| `Sun`            | Directional light, movable, intensity 8, 0.2 deg source angle for hard vacuum shadows |
| `SkyAtmosphere`  | Default settings                                                      |
| `SkyLight`       | Movable, real-time capture, intensity 0.35 - ambient fill only        |
| `PlayerStart`    | At (0, 0, 300)                                                        |
| `Asteroid_00-15` | Scaled cubes scattered 30-260 m out                                   |

The asteroids are placeholder reference geometry, not a design decision. Without something to
fly past, an empty sky gives no sense of motion whatsoever. Delete them once real props exist.

There is no starfield yet: `SkyAtmosphere` renders an atmosphere, not stars. That wants an HDRI
cubemap on the sky light or a dedicated skybox material.

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
