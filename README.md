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
| `HullCollision` | Root. Box (200 x 100 x 35 cm on the placeholder, sized to the mesh by the ship import), `Pawn` profile: what the ship's own movement sweeps. **Ignores pawns**: it encloses the whole ship including the air under the wings, and a pilot getting out inside it got stuck or pushed through the ground. Unscaled, so the cameras do not inherit the hull's scale |
| `Hull`        | The ship mesh (placeholder: `/Engine/BasicShapes/Cube` stretched to 2.0 x 1.0 x 0.35). Query-only collision from its simple collision (the UCX hulls from Blender) blocking pawns, cameras and visibility: characters walk around the real shape. The ship's own movement never sees it |
| `CameraBoom`  | 900 cm spring arm (Vanguard: 14.5 m), mild lag, collision test on: pulls the camera in rather than letting it sink into an asteroid. The mouse wheel scales it 0.45x-3x |
| `ChaseCamera` | Third-person camera                                              |
| `CockpitCamera` | Pilot's eye (Vanguard: 520, 0, 110 - at the windscreen, see below), FOV 90, inactive until toggled; `Alt` + wheel zooms it to `CockpitZoomFov` 40. `bHideHullInCockpit` hides the hull from the pilot, only for the placeholder cube |
| `EngineAudio` | Thruster loop, not spatialised. Hum, boost and cruise layers are created at runtime next to it |
| `SpaceDust`   | `USpaceDustComponent`: 400 specks in a 70 m box around the camera that stretch into streaks with speed |

### Flight model

Motion is integrated by hand in `Tick` rather than simulated by Chaos, which keeps the feel
predictable and cheap to tune.

- Every thruster direction has its own acceleration limit (cm/s^2, 981 = 1 G): main
  `ThrustAcceleration`, `RetroAcceleration`, `StrafeAcceleration`, up `LiftAcceleration`, `DownAcceleration`.
  The commanded acceleration is applied along the hull's local axes and accumulated into
  `LinearVelocity` (world space, cm/s).
- **Environment (L3).** Every tick the ship samples the nearest `ACelestialBody`
  (`SampleEnvironment`). Everything blends smoothly with altitude:
  - **Space** (above the atmosphere): no drag, no gravity - true Newtonian drift
    (`SpaceLinearDamping` 0). Coupled, the flight computer brakes; decoupled, the ship keeps flying.
  - **Atmosphere**: drag `LinearDamping` (0.4/s) plus `QuadraticDrag` (4e-5 per cm, grows with
    speed squared), both multiplied by air density (0 at the top, 1 at sea level), and gravity
    along the local down (`GravityScale`).
  - At sea level, with G-Safe's 7 G against the drag, that gives ~90 m/s top speed and ~13 m/s
    falling with the engines off. `ComputeEnvironmentAcceleration` is the exact formula.
  - **Entry heat** (`Spaceship|Entry`): density x (speed / 200 m/s)^3, from `HeatOnset` to
    `HeatFull`, smoothed; shakes the camera (`HeatShakeCm`) and shows on the HUD.
- The master mode's top speed (`ScmMaxSpeed` / `NavMaxSpeed`, raised by the afterburner) is a hard
  cap; above it (afterburner fading, NAV back to SCM) the excess bleeds off at `OverspeedDecay`.
  Cruise has its own limit.
- Pitch, yaw and roll drive a target rate (`PitchRate`, `YawRate`, `RollRate`, scaled down in NAV,
  in cruise and by G-Safe / ComStab, see below). `AngularVelocity` eases towards it at
  `AngularResponsiveness` but never changes faster than `PitchAcceleration` / `YawAcceleration` /
  `RollAcceleration` (rotational inertia), then applies as a *local* rotation. Local rotation is what
  makes this 6DOF rather than an aircraft glued to a horizon, and it avoids gimbal lock at the poles.
- Movement is swept (`bSweepMovement`), and a blocking hit projects velocity onto the surface
  plane so the ship slides instead of stalling. **A sweep only tests the root component**, which
  is why `HullCollision` has to be the root: with a plain scene component there the ship used to
  fly straight through the planet.
- **Mouse steering is a Star Citizen virtual joystick** (default, `bMouseRecenter` false): mouse
  movement moves a cursor inside a circle, and it stays where it is left. `VJoyCountsToFull` (300)
  mouse counts from the centre reach the rim = full turn rate; inside `VJoyDeadzone` (6 % of the
  radius) nothing turns, outside it the rate grows linearly. The debug HUD draws the circle, the dead
  zone and the cursor in the middle of the screen. With `bMouseRecenter` the older spring-centred
  stick is back (`MouseSensitivity` per pixel, `MouseRecenterRate`). Either way steering works on a
  stick position, not on per-frame deltas, so it is independent of frame rate.

All tuning values are `EditAnywhere` under the `Spaceship|Flight`, `Spaceship|IFCS` and
`Spaceship|Handling` categories.

### IFCS (SC-1a): coupled flight, speed limiter, master modes, G-Safe, ComStab

Modelled on Star Citizen's Intelligent Flight Control System (`starcitizenreference/`). Headless:
`Tools/Tests/test_ifcs_sc1.py`.

- **Coupled** (default, `V` toggles, HUD `CPLD`): `W` `S` `A` `D` `Space` `Ctrl` ask for a velocity
  in that direction while held - up to the speed limit. A released key means zero on that axis: the
  flight computer brakes it with the thrusters it has. It chases the target at `FlightAssistResponse`
  (3 per s), feeds forward drag and gravity (the ship hovers in the atmosphere) and every direction
  keeps its thruster limit, so hard turns still slide. There is no throttle lever any more.
- **Decoupled** (HUD `DECOUPLED`): the keys fire the thrusters directly, nothing brakes, nothing
  holds altitude: the ship keeps its velocity while it turns. The thrusters cannot push the speed
  past the limiter, but a faster ship is not slowed down by it. Rotation stays computer-controlled.
- **Spacebrake** (hold `X`, `IA_AllStop`): coupled flight towards zero on every axis with every
  thruster, also when decoupled. Keys are ignored while held.
- **Near the ground**: the commanded descent speed shrinks to `LandingDescentSpeed` (2.5 m/s) by
  20 m above the terrain, and with nothing held and the hull under ~4 m up, the computer holds only
  75 % of gravity, so the ship settles onto its gear.
- **Speed limiter** (mouse wheel, `IA_SpeedLimiter`): a fraction of the master mode's top speed,
  `SpeedLimiterStep` (5 %) per notch, `SpeedLimiterMin` (5 %) to 100 %. No key goes past it; lowering
  it in coupled flight brakes down to it. In cruise it sets how much of the cruise limit to use.
  `Alt` + wheel is the camera zoom (both actions are on the wheel; the ship checks Alt).
- **Master modes** (`B`, `IA_MasterMode`): switching takes `MasterModeSwitchSeconds` (2 s, the HUD
  shows the progress; `B` again cancels).
  - **SCM**: `ScmMaxSpeed` (Vanguard 210 m/s), full manoeuvrability. Cruise refused (`NeedsNav`).
  - **NAV**: `NavMaxSpeed` (1 km/s), turn rates x `NavTurnScale` (0.5), strafe / up / down thrust x
    `NavManeuverScale` (0.5), cruise drive available. Back to SCM drops out of cruise and bleeds the
    speed down.
- **G-Safe** (`K`, on by default): thruster acceleration on the pilot is limited to `GSafeMaxG`
  (7 G) in total and `GSafeMaxVerticalG` (5 G) along the spine. In coupled flight pitch and yaw rates
  are limited so that bending the flight path at the current speed takes at most `GSafeTurnG` (14 G):
  ~39 deg/s at 200 m/s, never below `GSafeMinTurnFraction` (30 %) of the full rate.
- **ComStab** (`L`, on by default): when G-Safe has to cut the thrust, sideways and vertical keep
  what they need and forward gets the rest (`LimitThrustForPilot`). And once nose and flight path are
  more than `ComStabSlipStartDeg` (8) apart, turning slows, down to `ComStabMinTurnFraction` (35 %) at
  `ComStabSlipFullDeg` (30). At SCM top speed with full yaw, slip stays around 40 degrees instead of
  sliding sideways and backwards.
- **Entry heat** is measured against `HeatReferenceSpeed` 200 m/s (the SCM top speed): SCM flight
  stays cool, boost and NAV speeds in thick air heat up.
- **Boost** (hold `Shift`, SC-1b, `Tools/Tests/test_boost_afterburner_sc1b.py`): the manoeuvring
  thrusters - retro, strafe, up, down - x `BoostManeuverMultiplier` (Vanguard 1.6), turn rates and
  rotational accelerations x `BoostRotationMultiplier` (1.4). Main thrust and the speed limit stay.
  **G-Safe is suspended while boost burns**, whatever `K` says (HUD `g-safe (boost)`): no G cap, no
  turn limit at speed. Burns energy whenever Shift is held (no W needed): `BoostDurationSeconds`
  (4.5 s), recharges in `BoostRechargeSeconds` (7 s) after `BoostRechargeDelaySeconds` (1 s); run
  dry, it stays off until `BoostUnlockFraction` (30 %) is back. HUD bar on the IFCS line.
- **Afterburner** (hold `Tab` with `W`, `IA_Afterburner`, **SCM only**): main thrust x
  `AfterburnerThrustMultiplier` (2.1); the speed limit becomes SCM top speed x
  `AfterburnerSpeedMultiplier` (2.5: 525 m/s on the Vanguard) **x the speed limiter** - at a 50 %
  limiter the afterburner tops out at 50 % of that. Own fuel: `AfterburnerDurationSeconds` (8 s) of
  burn, refills slowly in `AfterburnerRefillSeconds` (40 s) after `AfterburnerRefillDelaySeconds`
  (2 s); empty, it switches itself off and waits for `AfterburnerUnlockFraction` (15 %). The raised
  limit spools in over `AfterburnerSpoolSeconds` (0.4 s) and fades out over `AfterburnerFadeSeconds`
  (4 s), so letting go or running dry slows the ship at about retro strength instead of snapping.
  Works coupled and decoupled.
  - *Not in NAV*: NAV already flies at five times SCM speed with reduced manoeuvring and has cruise
    for more; the afterburner is the short combat or escape burst above SCM speed.
  - *G-Safe stays on*: the afterburner is straight-line forward thrust, exactly the load G-Safe
    exists for, so with G-Safe on it raises top speed but acceleration stays at 7 G. Turning G-Safe
    off (K), or holding boost at the same time (Shift + Tab), lets its full 16 G through. That is the
    tuning: from SCM speed to the top takes **4.4 s inside G-Safe and 1.8 s outside it**, out of an
    8 s tank, so the full speed is really only worth it with the safety off - the pilot chooses.
  - *Feel*: the limit opens in `AfterburnerSpoolSeconds` (0.25 s) and the view punches out at once
    (+9 degrees of FOV, eased in at 9 per second, back at 2.5) with a jolt and
    `AfterburnerShakeCm` 4.5 of shake, then fades over `AfterburnerFadeSeconds`.
  HUD line `AFTERBRN`: fuel bar and %, BURNING / fading / EMPTY - refilling / SCM only.
- **Quantum drive** (SC-4, NAV only, after the reference video in
  `starcitizenreference/QuantumTravel_VideoNotes.md`; it replaced the cruise drive on `J`): the body
  nearest the nose (within `QuantumPickDeg`, 35 degrees) is the destination. The drive spools by itself
  (`QuantumSpoolSeconds` 6 s) and calibrates while the nose is within `QuantumAlignDeg` (6 degrees) of
  it (`QuantumCalibrationSeconds` 2.5 s). READY, then the left mouse button held for
  `QuantumEngageHoldSeconds` (0.6 s) jumps: no steering, the nose stays on the destination, speed
  rises at `QuantumAccelerationKmS2` (8) to `QuantumMaxSpeedKmS` (30) and brakes to arrive at
  `QuantumExitSpeed` (300 m/s) `max(0.6 radii, 15 km)` above the surface. Then the drive cools for
  `QuantumCooldownSeconds` (10 s). Refused: shorter than `QuantumMinJumpKm` (20 km), a body on the
  way, or not enough fuel (`QuantumFuelPer1000Km` 12 %). `B` back to SCM ends a jump where the ship is.
  `space.Quantum <name> [0..1]` jumps at once for testing; shots take `"quantum": "<name>"`.
- **Feel**: the view widens with the afterburner (+7 degrees) and in a quantum jump (+12), the camera shakes
  with afterburner, boost (lightly), charging, entry heat and a short jolt on boost and afterburner
  ignition, engage and drop. Thruster materials (slots named `*Emissive*`) glow with engine load,
  much brighter with the afterburner and in a quantum jump;
  `*NavWhite*` slots double-flash like anti-collision strobes. Space dust streaks show direction
  and speed.
- **Sound** follows what the thrusters really do (`GetEngineDemand`: braking and hovering are
  heard, a steady coast through empty space is quiet): a reactor hum while piloted, the thruster
  roar, an afterburner layer while the afterburner burns, a quantum drone, plus one-shots for afterburner ignition,
  quantum engage held, jump and arrival (the former cruise sounds). All procedural placeholders from
  `python Tools/Assets/generate_ship_sounds.py Intermediate/GeneratedAssets`, imported by
  `.\Tools\run_editor_python.ps1 Tools\Assets\build_ship_audio.py` to `/Game/Ships/Audio/SW_*`;
  reimport real recordings onto the same assets. The generator prints each file's band balance:
  the first engine loop sounded like a vacuum cleaner because of its 1-4 kHz energy, so nothing
  here has more than a few percent above 2 kHz.

Headless: `Tools/Tests/test_flight_modes.py` (boost energy, cruise NAV-only / engage / limit / drop
in deep space and over Veyra, free look all round,
exit candidates and collision setup, character recovery, scene extras).

### Cockpit view

**Meshy Vanguard (18. 9. 2026):** the eye is at (410, 0, 145), 14 cm above the front edge of the cabin
roof. The model has no interior, and seen from inside every face is a back face that Unreal culls, so
from the seat the pilot would see nothing of the ship; the nose falls away at 29 degrees, more than the
25 degrees the view shows below the horizon, so straight ahead shows no ship either - free look does.
The survey now ignores faces seen from behind (add `twosided` for the old behaviour) and takes a sweep
range (`sweep:X0:X1:Z0:Z1`, cm). The text below is about the procedural Vanguard before it.

**Hull detail** (20. 9. 2026): an AI model's paint is one 4K texture over a 14 m hull (~3 mm a pixel), so it
goes soft as soon as the camera comes close (it is not texture streaming: a shot with
`r.Streaming.FullyLoadUsedTextures 1` looks the same). `M_Ship_PBR` adds a micro-detail layer, the way Star
Citizen's hulls are layered: a tiling normal (metal grain, sparse scratches) and large wear blotches for the
roughness, projected triplanar **in the ship's own space**, so the detail keeps its size in centimetres and
does not swim as the ship moves. `Tools/Assets/generate_detail_textures.py` generates the seamless textures
(numpy) into `ArtSource/Ships/Shared/Textures`; the setup file tunes the layer per ship (`detail_tile_cm`,
`detail_normal_strength` - 0 turns it off -, `detail_grunge_tile_cm`, `detail_rough_variation`). Wear only
raises the roughness; lowering it too gave the hull bright specular patches. The space conversions are done
in HLSL inside a Custom node (`GetPrimitiveData(Parameters).WorldToLocal`, `Parameters.TangentToWorld`):
with Transform expressions the normal came out wrong and the ship rendered black. The Vanguard's hull also
keeps **1 million triangles** instead of 200 thousand (`decimate.hull_target_tris`; the Meshy original has
3.36 million) - Nanite draws only what the screen needs, and the shots measured 92 FPS against 94 without
either change.

**Cockpit interior** (18. 9. 2026): the Vanguard has a Meshy cockpit tub (dashboard with screens, consoles,
side-sticks, pedals) as the part `SM_Ship_Vanguard_Interior` - the `interior` section of
`Vanguard_ai_build.json`, placed by `Tools/Blender/fit_ship_interior.py` (inside the hull everywhere, rim
at the canopy rail, eye with a clear view ahead). Since 18. 9. 2026 it is Meshy's dark variant, and the pilot
sits well back from it as in the Star Citizen reference (`Docs/UI/Screenshot 2026-09-17 201854.png`):
**eye (174, 0, 189)**, the dashboard top 8 degrees and the displays 14-25 degrees below the eye.
**Displays:** the two big screens are flat quads (slot `M_Ship_Vanguard_Screens`, recipe `interior.displays`)
that show the flight instruments live: `UCockpitDisplayComponent` draws `USpaceCockpitDisplays` (the
flight HUD's widgets, driven by the same `ApplyState`) into a render target (both displays side by side) 60 times a second,
through one kept `SVirtualWindow` (a new window per draw made Slate rebuild its vertex arrays every time),
while the ship is flown from the cockpit, and the unlit `M_Ship_Screen` (pixel animation) shows it. The screens
fill the glass in the bezels (~29 x 25 cm; layout 560 x 490, drawn at the size they appear on screen, from the
window width - `ScreenShareAt88`) and are styled like the reference's MFDs (deep blue glass, a title over a rule,
a `< PAGE >` bar): left FLIGHT (speed, limiter and G large, the mode pill, SPD / BST / AB / G bars like the
power page), right SYSTEMS (a list like the contacts page: COUPLED, G-SAFE, COMSTAB, BOOST, PRECISION and GEAR
with their switch pills, CRUISE with its state). Since 19. 9. 2026 (see Docs/HANDOFF.md 28) the look follows the
reference's MFDs more closely: lit glass with a faint grid and darker edges, a column of keys on the inner side
(left: CPLD, GSAF, CSTB, BOOST, PREC; right: MODE, GEAR, CRUISE), block bars like the power page, a STATUS list
like the contacts page, and the figures change 5 times a second (`state_rate_hz` in the setup) so temporal AA
does not blend each number with the one before; bars and lamps still move at 60 Hz. The interior is imported without Nanite (`no_nanite_parts` in
the setup): with Nanite its motion vectors were wrong in fast flight and temporal AA broke the displays' type
up. The cockpit camera has no motion blur. **Centre column** (19. 9. 2026): the two small screens between the
MFDs are displays too - RADAR (a plan view with the nose up, 5 km rings, the pilot's 88-degree view, contacts
within range - pawns and static meshes with collision - as diamonds on a stalk for their height, and the
celestial bodies as bearings on the rim with their initial, unless more than 60 degrees above or below the
wings; heading and contact count under it) and SELF STATUS (the ship from above as its collision hulls'
outlines, the `Engine_*` sockets glowing with the engine demand, the `Gear_*` legs lit while out, GEAR and
thrust / LANDED). `USpaceHudRadar`, `USpaceHudShipStatus`, contacts from `USpaceCockpitDisplays::MakeRadarContacts`
(5 Hz, with the figures); `space.CockpitCentre 0` switches the column off. The canvas is 1330 x 490:
left 0-560, right 560-1120, centre 1120-1330 (radar over 0-259) - `USpaceCockpitDisplays::ScreenRect`, and
`texture_size` / `texture_rect` in the recipe map each quad to its rectangle. Every line on those pages has one
thickness and one layer: Slate starts a new batch at each change of either and re-reserves the whole vertex list
per batch, and drawn with glow passes the two pages cost ~15 ms a frame (`stat SpaceCockpit`, `stat SpaceHud`).
**MFD pages** (19. 9. 2026): `F1` pages the left MFD, `F2` the right one, `Alt` with the key goes back
(Shift would boost); `[` and `]` do the same on a US keyboard (on a Czech one they are not keys of their
own). `Config/DefaultInput.ini` removes the engine's debug views from F1 / F2 (wireframe, unlit - they work
in Development builds). Left: FLIGHT, THRUSTERS (each direction's thrust against what it can do now -
main, retro, strafe with its side, up, down, in G - with BOOST and G-SAFE under it), NAVIGATION (master
mode and sub-mode, speed, limit, cruise, and the bodies with the range to their surface, bearing from the
nose and elevation). Right: STATUS, CONTACTS (the radar's contacts as a list: name - SHIP, EVA or the mesh's
name - range, bearing, elevation), SELF STATUS (the ship large, state, gear, engines, boost, afterburner
fuel). Only what the game has data for: no weapons, shields, power or cooling pages. The pages live in a
`UWidgetSwitcher` (only the one shown is painted); `UCockpitDisplayComponent` keeps the page
(`CyclePage`, `SetPage`, `GetPage`), `space.MfdPage <left> <right>` sets it from the console. The thrust
figures come from `ASpaceshipPawn::GetThrusterAcceleration` / `GetThrusterCapacity`.
**Readable from the seat** (19. 9. 2026): an MFD is ~0.4 of its layout size on a 1080p screen from the eye, so
the pages carry less and larger type (speed 96, G 56, nothing under 26; tested). Holding `Z` or the middle
mouse button leans in to the dashboard as the reference does (`SetDashboardFocus`: the head moves 15 cm
towards the `Display_*` sockets, turns to them and the view narrows until they fill it; the flight HUD
steps aside). The Vanguard's eye moved 20 cm nearer the dashboard with a 3 degree tilt down
(`cockpit_view_pitch_deg`) so the displays are larger at rest.
The screen HUD stays,
compacted so it sits above the dashboard. The cockpit is dark like the reference: the displays light it
(a rect light at each `Display_*` socket), a faint key and fill light keep the dashboard's shape, and the inside
of the canopy frame has its own dark slot (`M_Ship_Vanguard_CanopyFrame`).
Three things make it work in the game, all in the recipe or the setup file:
- `SM_Ship_Vanguard_Lining`: the hull around the cockpit copied with inward normals (`lining`). The hull is
  one-sided; without it the pilot saw the ground through the floor and the sides. The canopy glass is left out.
- `canopy_clear`: hull faces inside the canopy that face the cabin (frame undersides behind the opaque
  panes) are deleted; from the seat they crossed the HUD.
- `CockpitLight` (`cockpit_light_intensity_cd` 12, `cockpit_light_offset`, `cockpit_light_radius_cm`) and
  `CockpitFillLight` (`cockpit_fill_*`), both `cockpit_light_source_radius_cm` large: shadowless point lights
  between the eye and the dashboard and above the head; the hull shadows the cabin, which was otherwise
  almost black. Keep them under the canopy roof, or they light the canopy from outside.

**Placeholder cockpit** (`bPlaceholderCockpit`, `placeholder_cockpit` in the setup file, off on the
Vanguard since it has an interior): until a ship has a modelled interior, simple dark boxes around the pilot's eye give the HUD a cabin to sit in - a
sloped instrument panel with three screens whose far edge, with a glare-shield lip, is 16 degrees below
the horizon (~77 % of the screen's height, just under the HUD), canopy pillars ~30 degrees left and right
leaning outwards, and a seat behind the eye. Engine cube and `BasicShapeMaterial` (`Color`), built at
BeginPlay on a root at the eye (not on the camera, so free look turns only the head), pilot's view only,
no collision, no shadows, shown in cockpit view only. The layout is one table in `SpaceshipPawn.cpp`
(`SpaceshipCockpitLayout::Parts`), exposed as `GetPlaceholderCockpitCorners` and checked against the
view and the HUD's window by `Tools/Tests/test_cockpit_frame.py`; pictures: `Tools/Shots.ps1 -Preset cockpit`.

The eye position lives in `<Ship>_setup.json` (`components.cockpit_camera.relative_location`) and is
measured against the real model, not guessed: `Tools/Blender/cockpit_view_survey.py` casts a grid of
rays over the camera's field of view in Blender and prints what each one hits and how much of the view
is open.

    blender.exe -b ArtSource\Ships\Vanguard\Vanguard.blend --python Tools\Blender\cockpit_view_survey.py -- 520 0 110 88

The Vanguard has no modelled cockpit interior: the canopy is a shallow shell over a solid fuselage,
and its frame is part of the hull mesh. From a seat position (345, 0, 103) the survey found the tinted
glass 13 cm above the eye, filling 70 % of the view, the fuselage and frame the rest - **0 % open sky**,
which is what a player sees as a blue tunnel with a dark mass below. At (520, 0, 110), just in front of
the glass and 47 cm above the nose deck, **97.5 % of the view is open**, no glass is in the forward view
and only the nose tip shows at the bottom, like the Star Citizen reference in `Docs/UI/`. Free look
still swings round to the canopy and the hull. Run the survey again after changing a ship's model, and
put the result in its setup file; `Tools/Tests/test_flight_modes.py` then checks the eye against the
canopy mesh bounds (inside its footprint, upper half, well forward of its middle, looking straight ahead).

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

### Landing gear and precision mode (SC-2a)

Star Citizen style: the gear has to be down to land, and lowering it puts the ship into precision
(landing) mode. Headless: `Tools/Tests/test_landing_sc2.py`; pictures: `Tools/Shots.ps1 -Preset landing`.

- **Gear** (`N`, `IA_LandingGear`): `Retracted` / `Extending` / `Deployed` / `Retracting`, moving over
  `GearDeploySeconds` (2 s) and reversible halfway; a small camera jolt when it locks down. Raising it
  while landed is refused (the LANDING line says so for 3 s).
- **Touchdown needs the gear down and locked**: `EvaluateTouchdown` puts `GearUp` before every other
  blocker, so from 30 m down (the probe zone) the LANDING line reads `GEAR UP - lower it (N)` and the
  HUD's GEAR lamp blinks red. With the gear up the ship can still rest on the ground and slide, but it
  never becomes Landed (no alignment, no getting out). The rest is the L5 rule, measured under the pads.
- **The visible gear.** A mesh component whose name contains `Gear` is the ship's modelled gear: the
  Vanguard's skids are their own part, `SM_Ship_Vanguard_Gear`, cut out of the Meshy model by
  `Tools/Blender/build_ai_ship.py` (`parts.Gear` in `Vanguard_ai_build.json`; for the earlier procedural
  model `Tools/Blender/split_ship_gear.py` did the same). Stow travel 115 cm: the nose skid hangs 1.1 m
  under the belly. Stowed, the part
  rises `GearStowTravelCm` (95 cm on the procedural Vanguard, 115 on the Meshy one) into the belly, eased, and is hidden; it has no collision. The legs
  already reach the bottom of the collision box (the pads' soles, where `SOCKET_Gear_*` are), so
  `GearExtensionCm` is 0 for the Vanguard and it stands exactly where it did before SC-2a.
- **Ships without a gear part** get placeholder legs from `/Engine/BasicShapes/Cylinder` on the
  sockets named in `GearSocketNames` (with or without the `SOCKET_` prefix the FBX import drops): a
  sleeve, a piston and a pad in the hull's own HullDark / BareMetal / Rubber materials, swinging down
  (`GearFoldDeg`) and telescoping out (`ComputeGearLegPose`). They hang `GearExtensionCm` (100) below
  the hull box; the landing code then keeps the ground that far from the box (`ApplyGearSupport`: the
  descent stops on the pads, and lowering the gear under a ship on its belly lifts it).
- **Precision mode** (`P`, `IA_Precision`; on with the gear, off with it; `P` overrides either way):
  the SCM top speed becomes `ScmMaxSpeed x PrecisionSpeedFraction` (0.15: 31.5 m/s on the Vanguard) and
  the **speed limiter works inside it**, so one wheel notch is ~1.6 m/s instead of 10.5. Turn rates and
  rotational accelerations x `PrecisionTurnScale` (0.45). Thruster accelerations stay: stopping needs
  them. SCM only: in NAV it stays switched on but does nothing (HUD PREC amber). The afterburner is
  refused. Switched on at speed, the ship brakes down with its retro thrusters (~5 G), not with the
  overspeed bleed: the hard speed cap stays at the full SCM speed.
- **HUD**: GEAR lamp (green down, amber blinking on the way, red blinking low with it up) and PREC lamp
  (green, amber in NAV); the speed gauge's full scale follows the precision speed.


### VTOL (SC-2b)

`G` stands the ship on its lift thrusters instead of its main engines - the reference's VTOL switch,
one of four that are on at the same time (VTOL / CPLD / ESP / GEAR). SCM only; NAV turns it off. The
transition takes `VtolTransitionSeconds` so nothing snaps, and `GetVtolBlend` is how far through it
is. In VTOL the mains keep `VtolThrustFraction` of their thrust, the lift thrusters gain
`VtolLiftMultiplier` and the lateral ones `VtolStrafeMultiplier`, the top speed becomes
`VtolMaxSpeed` (the limiter still works inside it), and `Space` / `Left Ctrl` become a climb rate
(`VtolClimbSpeed`) rather than another way of reaching the top speed. With the stick still the ship
rights itself towards the horizon at `VtolLevelRate`; any stick input takes it straight back. The
afterburner is refused and the cruise drive is dropped.

Hovering also shows on the engines now. `EngineDemand` measured the vertical axis against the full
capacity of the lift thrusters, so holding station over Veyra - 0.46 G out of a possible 5.5 - read
as 0.06 and neither the nozzles nor the sound moved. It is measured against one G of thrust
(`HoverThrustReferenceG`) instead.

Headless: `Tools/Tests/test_vtol_sc2b.py`; pictures: `Tools/Shots.ps1 -Preset vtol`. The key comes
from `Tools/Assets/add_vtol_input.py`, and `space.Vtol 1|0` switches it from the console.

### Controls

| Action       | Keyboard / mouse           | Gamepad              |
| ------------ | -------------------------- | -------------------- |
| Thrust       | `W` / `S`                  | Left stick Y         |
| Strafe       | `D` / `A`                  | Left stick X         |
| Lift         | `Space` / `Left Ctrl`      | -                    |
| Roll         | `E` / `Q`                  | Shoulder buttons     |
| Pitch / yaw  | Mouse                      | Right stick          |
| Boost (hold) | `Left Shift`               | -                    |
| Afterburner (hold, SCM) | `Tab` (with `W`) | -                   |
| Coupled / decoupled | `V`                 | -                    |
| Spacebrake (hold) | `X`                   | -                    |
| Speed limiter | Mouse wheel               | -                    |
| SCM / NAV    | `B`                        | -                    |
| G-Safe / ComStab | `K` / `L`              | -                    |
| Quantum jump | hold left mouse button (NAV, nose on a body, READY) | - |
| Camera       | `C` (chase / cockpit)      | -                    |
| Zoom         | `Alt` + mouse wheel (chase distance, cockpit zoom) | - |
| Landing gear | `N` (down also switches precision on) | -          |
| Precision mode | `P`                      | -                    |
| VTOL (SCM only) | `G`                     | -                    |
| Dashboard focus | hold `Z` or the middle mouse button | -            |
| MFD pages    | `F1` left, `F2` right (`Alt` + key: back; `[` `]` on a US keyboard) | - |
| Get out      | `F` (only when LANDED)     | -                    |
| Free look    | hold right mouse button    | -                    |
| HUD          | `H` (compact / full / off) | -                    |

`V`, `X` and the wheel are `IA_FlightAssist`, `IA_AllStop` and `IA_CameraZoom`, appended to
`IMC_Spaceship` by `Tools/Assets/add_flight_modes_input.py`; the left mouse button is `IA_QuantumEngage`
(`Tools/Assets/add_quantum_input.py`); `B`, the
wheel again, `K` and `L` are `IA_MasterMode`, `IA_SpeedLimiter`, `IA_GSafe` and `IA_ComStab` from
`Tools/Assets/add_ifcs_input.py`; `N` and `P` are `IA_LandingGear` and `IA_Precision` from
`Tools/Assets/add_landing_input.py`; `F1` / `F2` (and `[` / `]`) are `IA_MfdLeft` and `IA_MfdRight` from
`Tools/Assets/add_mfd_input.py` (without them the ship maps the same keys at runtime).

**Free look** (Elite-style head look): while the right mouse button is held, the ship keeps its
heading (pitch/yaw rotation stops at once; roll keys and the flight path carry on) and the mouse
turns only the camera - the chase boom swings around the ship, the cockpit camera turns like a
head. `FreeLookSensitivity` 0.36 deg per mouse count, `FreeLookMaxYawDeg` 180 (all the way
round, to look at the whole ship) and `FreeLookMaxPitchDeg` 85, smoothed at `FreeLookFollowRate`.
On release the camera eases back the shorter way (`FreeLookReturnRate` 6: ~95 % in 0.5 s) while
steering works again immediately, from a centred
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
- **Ship exit / boarding**: on a LANDED ship, F spawns the character at the first free spot of:
  the hull mesh socket `Exit` (`SOCKET_Exit` from Blender), then right, left, behind and in front
  of the hull mesh bounds at 0.8, 3.8 and 8.8 m past them. Every spot is first pushed outward
  (sideways for the socket) until the pilot capsule, standing at the gear's height, is
  `ExitClearanceCm` (80 cm) clear of the hull's collision shapes (`GetHullClearance`: geometry of the
  UCX hulls, no physics query). The Vanguard's socket is only 2 cm clear of its belly hull, so the
  pilot now appears 1.4 m further out. Then each spot is put on the terrain and tested with a
  capsule overlap against everything that blocks pawns. The ship's root box ignores cameras, or the
  character's camera, starting inside it, would be pulled in to the head. F within `BoardingRangeCm` (4 m from the hull box) of a landed ship
  possesses the ship again and removes the character (0.75 s cooldown after getting out).
- **Safety net** (`RecoverFromTerrain`, every tick): a capsule more than `FallThroughToleranceCm`
  (60) under the terrain height field, or falling without moving for `StuckFallingSeconds`
  (0.6 s) close to the ground, is lifted back on top and logged (HUD `RECOVER`). The height field
  is exact where the collision tiles are an approximation, so this catches tunnelling through a
  tile and wedging on a seam.
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
(`python Tools/Assets/tests/test_import_ship_plan.py` tests that part). First real run: the
Vanguard (`ArtSource/Ships/Vanguard`), checked afterwards in a fresh editor by
`Tools/Tests/test_ship_import.py`. From Git Bash, run Blender with `MSYS_NO_PATHCONV=1`, or
`--out "//Export"` is rewritten to `/Export` (C:\Export).

**AI models (Meshy, Higgsfield) -> game ship**: `Tools/Blender/build_ai_ship.py` rebuilds a ship from
the raw AI export, driven by `ArtSource/Ships/<Ship>/<Ship>_ai_build.json` (ShipPipeline.md, 2B):
orient and scale, cut fused parts out by region boxes (the Vanguard's skids -> `SM_Ship_Vanguard_Gear`),
decimate with importance rules, **a fresh UV atlas and the source re-baked onto it** (base colour, ORM,
normal map - AI atlases have thousands of tiny islands that decimation welds together, and Meshy's
normal map is nearly flat), an emissive slot for the nozzle discs, k-DOP `UCX_` hulls per region box and
sockets. The current Vanguard (18. 9. 2026) is Meshy's "Ironclad Starfighter": 3.36 M triangles in,
200 k + 14 k gear out, 14 x 11.4 x 6.2 m, four engine nacelles. Its material is `M_Ship_PBR`
(`BaseColorMap`, `ORMMap` G roughness / B metallic, `NormalMap` with the green channel flipped on import,
`Tools/Assets/ship_materials.py`); thrusters keep `M_Ship_Hull` with emission.

The ORM's **red channel is not occlusion** here, it is the emissive mask for the cockpit screens, so
the re-bake leaves the ship with no occlusion at all and the hull reads as one flat colour whatever
the lighting does. `Tools/Blender/bake_ship_ao.py` bakes `T_Ship_<Ship>_AO.png` afterwards, from the
built meshes, through an occlusion shader limited to half a metre (Cycles' own AO bake has no limit,
and on a closed 14 m hull that reads as dirt rather than panel gaps). The material darkens the paint
by it (`CavityStrength`), sends it to the Ambient Occlusion output (`AOStrength`) and uses it to keep
worn paint (`WearAmount`) on the exposed surfaces. `AOMap` defaults to white, so a ship without the
bake looks exactly as it did.

**Markings** (registration, hazard bands, a service hatch) are deferred decals, not paint in the
atlas: `Tools/Assets/generate_decals.py` draws `ArtSource/Ships/Shared/Decals/D_*.png`, and the
`decals` list in `<Ship>_setup.json` places `Decal_<name>` components under Hull with their own
material instance. Two things to know before placing one. A decal projects along its component's
**-X**, so the rotation has to point X *away* from the surface (roof: pitch +90; left flank: yaw
+90); backwards it paints thin air and smears into streaks across whatever grazing geometry it
catches. And the texture lands the way the box is turned, which on the flanks came out mirrored -
rotations cannot mirror, so the material has `DecalFlipU` / `DecalFlipV` (`flip_u`, `flip_v` in the
setup). Pick the spots by raycasting the model in Blender: a decal on a curved or hidden surface
simply does not read.

**Panel seams** come from a tiling sheet as well (`Tools/Assets/generate_panel_lines.py`,
`T_Ship_Panels.png`: the seam's normal in RG, the groove in B), projected triplanar in the ship's
space like the micro detail, because the ship's atlas is thousands of tiny islands and a line drawn
into it would break at every island edge. The groove also darkens and roughens the paint. Two
numbers matter: a seam narrower than about 2 cm never survives the mip chain and simply is not
there, and above `panel_strength` ~0.8 the seams run over greebles and curves the model has no
plating on, which reads as an overlay rather than a hull. The Vanguard uses a 260 cm sheet at 0.55,
and the layer costs no frames.

The whole hull is one material, so the only **zones** available without a second UV set are the ones
the ship's own shape gives. The one that earns its keep is the tail: from `scorch_start_cm` back to
`scorch_end_cm` (both negative, along the ship's X) the material darkens and roughens the paint, so
the plating around the nozzles is burnt and the viewer can tell which end is the engine.
`scorch_amount` defaults to 0 - the lengths are centimetres and mean nothing on a ship of another
size, so each ship sets its own in `<Ship>_setup.json`.

**Graphics quality.** New settings are Cinematic, not the engine's Medium. Of the eight scalability
groups only global illumination costs anything - at Cinematic it halves the frame rate and in these
scenes, lit by a sun and a sky light, the pictures did not change - so it is capped
(`USpaceUserSettings::MaxGlobalIlluminationQuality`) and the rest go all the way up, which costs
about 10 % of the frame rate and measurably sharpens the image. `Tools/Shots.ps1 -Preset look_groups`
re-measures one group at a time. Before hunting a soft image in a model or a material, check the
settings: twice in one day that is what it turned out to be (a 50 % render scale, then Medium). `import_ship.py` imports
a mesh fresh when its material slots changed (a reimport kept the old model's slots) and removes the
Blueprint components, meshes and material instances an earlier model left behind.

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

## Flight HUD (SC-1c, UMG)

**Since 19. 9. 2026 the layout follows the current Star Citizen HUD** (`Docs/UI/Screenshot 2026-09-17 201854.png`,
every element measured at 1080p from the middle of the screen; Slate's DPI scale fits other resolutions), in
ice-cyan and near-white in Rajdhani Medium with a faint cyan halo:
- **left:** master mode icon, `SCM`/`NAV` over the sub-mode (`FLIGHT`, `PREC`, `SPOOL`, `CRUISE`); switch
  badges shown only while on (`CSTB`, `CPLD`/`BRAKE`, `PREC`, `BOOST`); the strafe cross (red arrow heads
  lit in the strafe direction, a dot for drift across the nose); the tall thin speed tube with the limiter
  handle and a `+` beside it; the speed and `m/s` under it; `BOOST` / `LIMIT` rows under a bracket;
- **middle:** heading tape (0 = north, the world Z axis on the local horizon), the pitch ladder (horizon
  strokes and 5-degree brackets, rolled and projected with the view's field of view), the nose reticle,
  the virtual joystick (now faint);
- **right:** the afterburner tube with its red reserve, the percentage and `AB` (`AB BURN/DRY/SCM`); the
  altitude tape in km above sea level with the value in a box; the gyro (turn rate as an orange line) and
  the G-Safe shield (dim when off, amber when suspended); G with the G-Safe limit under a line; `GEAR` /
  `CRUISE` rows at the top and `R-ALT` / `VSI` / `ATMO` at the bottom.
- Heading, ladder and altitudes only near a body. SC's fuel, countermeasure and weapon readouts are left
  out: this game has no such systems yet, and the HUD shows nothing it cannot back with real data.
- **Your own font:** the first `.ttf` / `.otf` in `Content/UI/Fonts/Custom/` replaces Rajdhani and Share Tech Mono
  everywhere (HUD and cockpit displays); package the game after adding it. The folder is git-ignored, so a font
  that may not be redistributed never reaches the repository. The fonts are staged as raw files
  (`DirectoriesToAlwaysStageAsUFS` = `UI/Fonts`, relative to `Content`; `Tools/Package.ps1` checks they are in).
- Painted widgets: `USpaceHudSymbol` (mode icon, strafe cross, gyro, shield, ring, reticle, plus,
  brackets), `USpaceHudTape` (heading / altitude), `USpaceHudLadder`; `USpaceHudGauge` gained a reserve
  band. The cockpit displays (`USpaceCockpitDisplays`) use the same palette.

The rest of this section describes SC-1c's first layout; its logic (lamps, limiter, reverse zone,
afterburner states, virtual joystick) is unchanged.

`Source/gamespace/SpaceFlightHud.*` - after `Docs/UI/SC_ThrottleHUD_VisualReference.md`: thin,
translucent cyan lines framing the middle of the screen, no panels. Built entirely in C++, no widget
Blueprint: `USpaceFlightHud` (a `UUserWidget`) constructs its widget tree in `Initialize` from UMG
widgets (canvas, boxes, `UTextBlock`s, `UBorder` lamps) plus two widgets that paint themselves:
`USpaceHudGauge` (thin line gauge: rails, ticks, translucent fill with a bright edge, optional red
reverse zone and a marker; vertical or horizontal) and `USpaceHudVirtualJoystick`. `ASpaceDebugHUD`
creates it for the local player (z-order -10, under the menus); it follows the flown ship every tick
and hides with `H` (`space.Hud` 0) or when no ship is flown (the root panel collapses, the widget
keeps ticking). Module dependency: `UMG`.

- **Left of centre**, right-aligned against a frame line:
  - status lamps with small squares - `SCM`/`NAV` (blinks while switching, shows the mode being
    switched to), `CPLD` (reads `BRAKE`, red, under the spacebrake), `GSAF` (amber while boost
    suspends it), `CSTB`, `BOOST` (amber), `GEAR` and `PREC` (SC-2a, see Landing gear); dark = off;
  - the **speed gauge**: full height = the mode's top speed as the afterburner currently raises it
    (`GetSpeedLimit / GetSpeedLimiter`, so it rescales smoothly while the afterburner spools and
    fades); fill = speed along the nose (green, amber with the afterburner or above the limiter);
    the cyan **marker is the speed limiter**; the red zone at the bottom (12 %) fills when flying
    backwards, at the same metres per pixel;
  - speed (`157 M/S`) and `LIM 180 M/S 90%` in small type under it;
  - the **G meter** tied to it: a short horizontal gauge to 12 G with the G-Safe limit as a mark
    (while G-Safe is limiting) and the value; cyan, amber above 70 % of `GSafeMaxG`, red above it.
- **Right of centre**, after a frame line: `BOOST` energy and `AFTERBURNER` fuel as vertical gauges in
  the same style with the % under them (`LOW`, `BURN`, `EMPTY`, `SCM ONLY`; the afterburner gauge
  dims in NAV).
- **Centre**: the virtual joystick - rim, dead zone, cursor (amber with a line from the centre when
  outside the dead zone); hidden while landed or free looking.

**Palette** (from `Docs/UI/SC_throttle_hud_reference.png`): the instruments are yellow-green on
near-black with near-white labels and a thin cool-white rail; **cyan is only for the frame brackets
and the virtual joystick**, and warm colours are warnings, never a state - amber marks G-Safe
suspended by boost and a high G load, red the reserve, flying backwards and the part of the speed bar
above the limiter mark. An earlier pass painted boost and the afterburner amber, which read as an
orange HUD; the reference never floods a bar with a warning colour.

**Look** (matched against the screenshots in `Docs/UI/`, iterated with `Tools/Shots.ps1 -Preset hud`):
bars are thin capsules - a dark tube with a 1 px cool-white outline and ticks up its side, a gradient
fill broken into thin rungs (the reference fills its tubes like a ladder, not with a solid block), a
halo, and the limiter hanging off the side as a short handle with a nub. Status switches are dark
boxes holding their label with a small square lamp inside on the right, groups are framed
by corner brackets over the bare view rather than by filled panels, and type is the engine's thin
Roboto Light for numbers with small wide-spaced Bold caps for labels, both outlined so they read over
a bright sky. Slate has no additive brush and a scene bloom would light the whole game, so the glow is
the same shape drawn twice more, inflated and very faint (`GlowLines`, `GlowRounded`); rounded shapes
come from `FSlateRoundedBoxBrush` and the fills from `FSlateDrawElement::MakeGradient` with a corner
radius. A rounded box takes its colour from the **draw tint**, not from the brush - passing it on the
brush renders solid white.

**Type**: `Content/UI/Fonts` holds the HUD's own faces with their licences - **Rajdhani SemiBold**
for labels, switch pills and gauge titles, **Share Tech Mono** for every number (speed, limit, G,
percentages: fixed-width digits do not dance as the value changes), both SIL OFL 1.1. They are loaded
from the file (`SpaceHudStyle::LabelFont` / `NumberFont`), not imported as Font assets, because the
font importer needs a Slate application and the headless editor this project scripts with has none;
each falls back to an engine face if its file goes missing. Raw files under `Content` are not cooked,
so `DirectoriesToAlwaysStageAsUFS` in `Config/DefaultGame.ini` stages them into the pak.

**Life**: bars ease towards their value (about 1/11 s) so a jump in speed springs rather than snaps,
and lit lamps and fills breathe at 0.55 Hz by 8 %. One clock (`USpaceFlightHud::DebugAdvance`) drives
both, which is also how the tests step the animation without Slate.

`USpaceFlightHud::MakeState(Ship, HudMode)` gathers everything shown into `FSpaceFlightHudState` and
`ApplyState` only displays it, so headless tests check the values without a screen:
`Tools/Tests/test_flight_hud_sc1c.py`. Layout constants (offsets +-300 px from the centre, gauge sizes)
and colours (`SpaceHudStyle`) are at the top of `SpaceFlightHud.cpp`.


**Flight path marker (SC-3).** The HUD shows where the ship is actually going, not where its nose
points - in Star Citizen that is what you fly by, and decoupled the two part company entirely. A
ring with three stubs sits where the velocity lands on the screen, projected from the view's focal
length in `USpaceFlightHud::ApplyView` in the HUD's own 1080p units. Behind the nose - reversing, or
sliding sideways past 90 degrees - there is no projection, so it goes amber, draws dashed and pins
to the opposite side of a circle, which is the way to turn to bring it back; exactly behind it parks
at the bottom rather than flickering round the ring. Below 5 m/s it is not drawn, because under that
the direction is noise. `Tools/Tests/test_flight_hud_sc3.py` checks the projection against the
geometry it claims to do; `Tools/Shots.ps1 -Preset velocity_vector` shows it.

Two things came with it, both for putting the ship in states it cannot fly into by itself: the shot
list's `drift` field (`[forward, right, up]` in m/s, the ship's own axes, instead of `speed_ms`
which only flies straight ahead) and `space.Drift <forward> <right> <up>` in the console.

## SpaceDebugHUD

`AHUD` subclass set as `HUDClass` on `SpaceGameMode`. Creates the UMG flight HUD (above) and draws
the rest as plain canvas text in the top-left corner: the cruise drive state or the key help
(`DRIVE`), flight regime, landing, camera, target. In full mode it also prints the numbers the UMG HUD
shows graphically (`SPEED`, `IFCS`, `AFTERBRN`) for tuning. A master mode switch, cruise charging, a
drop close to the ground and free look also show big in the middle of the screen. A tuning aid, not
UMG - SC-3 replaces it.

`H` (`IA_ToggleHud`, appended to `IMC_Spaceship` and `IMC_Character` by
`Tools/Assets/add_hud_toggle_input.py`) cycles the CVar `space.Hud`: `1` compact (default: mode,
drive, flight, landing, move; the UMG flight HUD shows speed and IFCS), `2` full (every line below), `0` hidden. Position and text size
scale with the viewport height (1.0 at 1080 p), so the panel stays in the corner at any
resolution.

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
once it is `RebaseDistanceKm` (default 40; cruise drive at 6 km/s would rebase every 1.7 s at 10) away, through the engine's own
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
| `Sun`              | Directional light, movable, intensity 8, pitch -39 / yaw 45: from behind the player's left shoulder. Contact shadows 0.08 m, source angle 0.5 deg |
| `SkyLight`         | Movable, real-time capture, intensity 0.7 (`SKY_LIGHT_INTENSITY`). It fills the ship's shadow side; at the old 0.35 the hull was a black silhouette against space |
| `StarfieldSky`     | `ASkyDome`: 2000 km sphere that follows the camera, with `M_Starfield_Sky`: unlit, *Is Sky*, procedural twinkling stars, a Milky Way glow cubemap, nebulae and the sun disc |
| Space dust         | `USpaceDustComponent` on the ship: 700 specks (only a hint of motion, as in Star Citizen; none in a quantum jump) in a 30 m box, wrapped around the camera. A speck is a stretched cube that `M_SpaceDust` tapers to a soft spindle, with its own length and brightness, so the field reads as dust rather than as a row of identical white sticks. `space.Dust <Property> <Value>` tunes it live; the shape is measured from `ObjectPositionWS`, because `LocalPosition` on an instanced mesh is the primitive's space, not the instance's |
| Speed tunnel       | `USpaceSpeedTunnelComponent` on the ship: the look of a quantum jump, shown only in one (the pawn's quantum blend). `M_QuantumFog`, a translucent cylinder behind the streaks, hides the sky as the reference's fog does; green flares come at the jump and every 8-18 s. Three open cylinders round the camera along the flight path (25, 60, 150 m); from inside, their walls converge on the vanishing point by plain perspective. `M_SpeedTunnel` draws streaks (lanes round the axis, one streak per period, scrolled by a distance the component accumulates and capped at 2 km/s apparent so they never strobe), soft beams converging on the vanishing point and a glow there (the far cap). `space.Tunnel <Property> <Value>` tunes it live |
| `Planet_Veyra`     | `AQuadSpherePlanet`, radius 25 km, centre 45 km ahead of the start (start is 20 km above sea level, 8 km above the atmosphere) |
| `Moon_Keth`        | `ADistantBody`, radius 6 km, orbits Veyra at 150 km every 25 min (`M_Moon`: craters, maria) |
| `GasGiant_Orun`    | `ADistantBody`, radius 150 km with rings to 330 km, 620 km away to the right of Veyra (`M_GasGiant` bands and a storm, `M_PlanetRings`) |
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
(verified 20 km out after a rebase). Its radius (`DomeRadiusKm`, 2000) must exceed the distance
to the farthest body that should be visible, because anything beyond it is hidden: the gas
giant's far ring edge is 950 km from the start.

**A sky that is not a backdrop.** Painted stars never move, so on their own they read as a
canvas. Several things break that:
- **Parallax**: the moon and the gas giant are real geometry (`ADistantBody`: a lit sphere, rings,
  optional orbit and spin; no gravity, not a `CelestialBody`), so they shift against the stars as
  the ship travels, especially in cruise. The moon moves visibly along its orbit.
- **Space dust** around the ship streaks past with speed (`M_SpaceDust`, additive).
- **Nebulae**: domain-warped fbm clouds in three regions of the sky (magenta, teal, amber),
  `NebulaBrightness` 3; `ASkyDome.NebulaScale` scales it per level.
- **The sun**: a limb-darkened disc far above white (it blooms) with a corona, pointed at the
  level's directional light by `ASkyDome` every frame (`SunDirection`, `SunColor`); warmer and
  wider seen through air. `ASkyDome.SunScale` scales it.
- **Twinkle**: every star flickers slightly at its own rates; `ASkyDome` drives `Twinkle` from
  `SpaceTwinkle` (0.12) in space to `AtmosphereTwinkle` (0.6) in air, where real stars scintillate.

**Atmosphere in the sky.** `ASkyDome` samples the environment at the camera each frame and sets
`AtmosphereAmount`, `PlanetUp`, `SkyZenithColor`, `SkyHorizonColor` and `SkyBrightness` on a
dynamic instance of `M_Starfield_Sky`. The material blends a horizon-to-zenith gradient over the
stars; stars fade with the square of the remaining space. The sky gradient does not know where
the sun is yet: the night side is blue too.

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
position are constants at the top of `build_space_scene.py`, together with the
lighting and the grade (`SKY_LIGHT_INTENSITY`, `SUN_CONTACT_SHADOW_M`, `SUN_SOURCE_ANGLE_DEG`,
`POST_SETTINGS`). Tune those in the running game first - `space.Post`, `space.PostList`,
`space.PostDump`, `space.Sun`, `space.SunDir`, `space.Sky`, `space.LightList` in
`Source/gamespace/SpacePostTuning.cpp` reach every setting by name through the reflection data -
then write the numbers here and re-run this script. `Tools/Tests/test_scene_look.py` compares the
saved level with the recipe, so a forgotten re-run shows up as a failing test.

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

## Playable build: title screen, pause menu, settings

`.\Tools\Package.ps1` (editor closed, ~3-5 min) cooks a Development build into
`C:\gamespace\Builds\Gamespace`. Double-click `Windows\gamespace.exe` there, or run
`.\Tools\Play.ps1`. After packaging the script checks that key assets C++ loads by path are in
the build.

- **Title screen** `/Game/Maps/MainMenu` (built by `Tools/Assets/build_main_menu.py`, the game's
  `GameDefaultMap`; the editor still starts on TestSpace): the Vanguard with Orun and Keth behind
  it, a slowly drifting camera (`MenuCamera` around the actor tagged `MenuOrbitCenter`), ambient
  music. HRÁT / NASTAVENÍ / KONEC. Game mode `ASpaceMenuGameMode`: no pawn.
- **Pause menu**: Escape (F10 too; in PIE Escape stops the session, so use F10 there) pauses the
  game: POKRAČOVAT / NASTAVENÍ / HLAVNÍ MENU / UKONČIT HRU.
- **Settings** (`USpaceUserSettings`, a `UGameUserSettings` subclass registered in
  DefaultEngine.ini, saved to `GameUserSettings.ini`): window mode, resolution, overall quality,
  resolution scale, VSync, frame limit; master / effects / music volume (heard live while
  dragging); mouse sensitivity (multiplies ship steering, free look and on-foot look); inverted
  ship pitch; HUD mode; FPS counter. POUŽÍT applies and saves, Escape / ZPĚT discards. First
  start: borderless fullscreen at the desktop resolution, quality High. The quality row reads
  `GetGraphicsQualityLevel()` (the lowest scalability group), not the engine's
  `GetOverallScalabilityLevel()`, which is -1 whenever the resolution scale is not the preset's
  default: the row then showed High and the next POUŽÍT saved High over the player's choice.
- **Global keys** live in `ASpacePlayerController`'s own mapping context (priority 100): Escape /
  F10 menu, H HUD (saved to the settings). Pawns no longer bind H.
- The menus are plain Slate (`SSpaceMenu`), no UMG assets. UI sounds `/Game/UI/Audio`.

**Cooking and path-loaded assets.** The cooker only follows references from the cooked maps.
Everything C++ loads by path (input actions and contexts, sounds, dust material) was missing from
the first packaged builds: no sound, no H. `Config/DefaultGame.ini` now lists `MapsToCook` and
`DirectoriesToAlwaysCook` (`/Game/Input`, `Ships`, `UI`, `Environments`, `Planets`,
`Characters`, `Blueprints`); add any new folder loaded by path there.

Headless: `Tools/Tests/test_menu_settings.py`.

## Screenshots for visual checks

`Tools/Shots.ps1` runs the **packaged** game through a shot list and quits: cooked materials, no
editor, and nobody has to play to see what a change looks like.

```powershell
.\Tools\Shots.ps1 -Preset cockpit           # Tools/Shots/cockpit.json
.\Tools\Shots.ps1 -Preset hud -Package      # package first (after any C++ or content change)
.\Tools\Shots.ps1 -Last                     # paths of the newest set
```

Pictures land in `Saved/Shots/<stamp>_<preset>/NN_<name>.png` (not in git; `-Keep` also copies them
to `Docs/Shots/` for the repository's visual history). Presets are `cockpit`, `hud`, `ship`,
`landing`, `ship_views` (a model from every side) and `cockpit_tune` (variants side by side). A shot list is JSON read from disk at runtime, so
editing one needs no repackaging; a shot can set the camera, HUD mode, altitude, facing, speed, master
mode, limiter, coupled / G-Safe / ComStab, boost, afterburner, the virtual joystick cursor, the gear
(`gear` straight down or up, `lower_gear` to catch it moving), `precision`, the chase camera swung round
the ship (`chase_yaw`, `chase_pitch` > 0 from below, `chase_zoom`), and - for tuning a cockpit without
reimporting the ship - `cockpit_eye`, `hide_hull` and `hide_canopy`. A low `altitude_m` with the gear
down and a few seconds of `settle` lands the ship for real (the collision under it is built at once).

`USpaceShotRunner` (`SpaceShotRunner.*`) does the work: `-ShotList=<path> -ShotOut=<dir>` on the
command line, or `space.Shot [name]` / `space.Shots <path>` in the console during a normal session.

## Playing fullscreen outside the editor

| Command | What runs | When |
| --- | --- | --- |
| `.\Tools\Package.ps1` then `.\Tools\Play.ps1` | The cooked build in `C:\gamespace\Builds\Gamespace`, window mode and resolution from its settings | Normal play testing. Re-package after content or C++ changes (editor closed). |
| `.\Tools\Play.ps1 -Editor` | `UnrealEditor.exe -game` on TestSpace, uncooked | Quick look without packaging. Loads slower; materials the editor has not compiled yet can render grey. |

`Play.ps1 -Windowed -Width 1600 -Height 900` (or `-Exclusive`) overrides the settings for one
launch. In game: `~` console (`stat fps`, `stat unit`), `Alt+Enter` window/fullscreen.

Inside the editor: Play dropdown > **New Editor Window (PIE)** opens a separate window
(`Alt+Enter` makes it fullscreen), or press `F11` in the viewport for immersive mode. `Shift+F1`
frees the mouse.

## Handoff

`Docs/HANDOFF.md` is the state of the project for a new session: collaboration rules, the master
reference folder `starcitizenreference/`, code map, tests, known issues and the Star Citizen
flight system roadmap.
