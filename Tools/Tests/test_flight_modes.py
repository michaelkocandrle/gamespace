"""Headless checks for boost energy, cruise drive (NAV only), free look, exits and the scene extras.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_flight_modes.py

Drives a temporary ship frame by frame (1/60 s) through SpaceshipPawn.debug_step_flight, which
runs the same code as Tick. Deep-space parts run in a new blank map (no planet), planet parts in
TestSpace. Nothing is saved. The commandlet has no collision queries, so the exit test checks the
candidate order and the collision setup, not overlaps.
Prints "FMTEST PASS" / "FMTEST FAIL" lines and a summary.
"""

import math

import unreal

LEVEL = "/Game/Maps/TestSpace"
STEP = 1.0 / 60.0
failures = []


def log(msg):
    unreal.log("FMTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def length(a):
    return math.sqrt(sum(c * c for c in a))


def run(ship, seconds, thrust=0.0, strafe=0.0, lift=0.0, boost=False, each=None):
    velocity = None
    for i in range(int(round(seconds / STEP))):
        velocity = ship.debug_step_flight(STEP, thrust, strafe, lift, boost)
        if each:
            each(i, velocity)
    return v3(velocity) if velocity else v3(ship.get_linear_velocity())


eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cdo = unreal.get_default_object(unreal.SpaceshipPawn)
MAX = cdo.get_editor_property("scm_max_speed")
NAV = cdo.get_editor_property("nav_max_speed")
SWITCH = cdo.get_editor_property("master_mode_switch_seconds")

# Coupled / decoupled, limiter, spacebrake and master modes: Tools/Tests/test_ifcs_sc1.py.

# =========================================================================================
# Deep space
# =========================================================================================
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)


def spawn():
    return eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())


def to_nav(ship):
    ship.request_master_mode(unreal.MasterMode.NAV)
    run(ship, SWITCH + 0.05)


# --- Boost energy (what boost does: Tools/Tests/test_boost_afterburner_sc1b.py) ---------------------------------------------------------------------------
ship = spawn()
try:
    duration = cdo.get_editor_property("boost_duration_seconds")
    peak = [0.0]
    active_frames = [0]

    def watch(i, v):
        peak[0] = max(peak[0], v.x)
        if ship.is_boosting():
            active_frames[0] += 1

    run(ship, duration + 1.0, thrust=1.0, boost=True, each=watch)
    check("boost lasts BoostDurationSeconds", abs(active_frames[0] * STEP - duration) < 0.1, "%.2f s" % (active_frames[0] * STEP))
    check("empty boost locks", ship.is_boost_locked() and not ship.is_boosting() and ship.get_boost_energy() < 0.01)
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    delay = cdo.get_editor_property("boost_recharge_delay_seconds")
    recharge = cdo.get_editor_property("boost_recharge_seconds")
    unlock = cdo.get_editor_property("boost_unlock_fraction")
    frames = 0
    while not ship.is_boost_locked() and frames < 3000:
        ship.debug_step_flight(STEP, 1.0, 0.0, 0.0, True)
        frames += 1
    run(ship, delay - 0.05)
    check("no recharge during BoostRechargeDelaySeconds", ship.get_boost_energy() < 0.005, "%.4f" % ship.get_boost_energy())
    run(ship, 0.05)
    start_energy = ship.get_boost_energy()
    run(ship, 1.0)
    gained = ship.get_boost_energy() - start_energy
    check("recharges at 1 / BoostRechargeSeconds per second", abs(gained - 1.0 / recharge) < 0.005, "%.3f per s" % gained)
    ship.debug_step_flight(STEP, 1.0, 0.0, 0.0, True)
    check("still locked below BoostUnlockFraction", ship.is_boost_locked() and not ship.is_boosting(), "energy %.2f" % ship.get_boost_energy())
    run(ship, (unlock - ship.get_boost_energy()) * recharge + 0.1)
    ship.debug_step_flight(STEP, 1.0, 0.0, 0.0, True)
    check("boost works again once BoostUnlockFraction is back", ship.is_boosting() and not ship.is_boost_locked(),
          "energy %.2f" % ship.get_boost_energy())
finally:
    eas.destroy_actor(ship)

# --- Cruise in deep space ------------------------------------------------------------------
ship = spawn()
try:
    spool = cdo.get_editor_property("cruise_spool_seconds")
    cruise_max = cdo.get_editor_property("cruise_max_speed")
    ship.toggle_cruise()
    check("J refused in SCM", ship.get_cruise_state() == unreal.CruiseState.OFF and ship.get_cruise_blocker() == unreal.CruiseBlocker.NEEDS_NAV)
    to_nav(ship)
    ship.set_speed_limiter(0.75)
    ship.toggle_cruise()
    check("J starts charging in NAV", ship.get_cruise_state() == unreal.CruiseState.SPOOLING)
    run(ship, spool - 0.1)
    check("still charging just before CruiseSpoolSeconds", ship.get_cruise_state() == unreal.CruiseState.SPOOLING,
          "%.0f %%" % (100 * ship.get_cruise_spool_progress()))
    run(ship, 0.2)
    check("engaged after CruiseSpoolSeconds", ship.get_cruise_state() == unreal.CruiseState.ACTIVE)
    check("limit in deep space is CruiseMaxSpeed", abs(ship.get_cruise_speed_limit() - cruise_max) < 1.0)
    velocity = run(ship, 6.0)
    check("cruise flies at limiter x limit", abs(velocity[0] - 0.75 * cruise_max) < 0.02 * cruise_max,
          "%.0f m/s" % (velocity[0] / 100.0))
    ship.toggle_cruise()
    check("J again drops out", ship.get_cruise_state() == unreal.CruiseState.DROPPING
          and ship.get_cruise_blocker() == unreal.CruiseBlocker.PILOT)
    velocity = run(ship, 3.0)
    check("drop bleeds speed down to NAV top speed", length(velocity) <= NAV + 1.0 and ship.get_cruise_state() == unreal.CruiseState.OFF,
          "%.0f m/s, state %s" % (length(velocity) / 100.0, ship.get_cruise_state()))
    check("cruise limit function", abs(ship.compute_cruise_speed_limit(1000000.0, 0.0, True) - 400000.0) < 1.0
          and abs(ship.compute_cruise_speed_limit(1000.0, 0.0, True) - cdo.get_editor_property("cruise_min_speed")) < 1.0
          and ship.compute_cruise_speed_limit(1000000.0, 1.0, True) < ship.compute_cruise_speed_limit(1000000.0, 0.0, True))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    to_nav(ship)
    ship.toggle_cruise()
    run(ship, cdo.get_editor_property("cruise_spool_seconds") + 0.1)
    ship.toggle_master_mode()
    check("B back to SCM drops out of cruise", ship.get_cruise_state() == unreal.CruiseState.DROPPING and ship.is_master_mode_switching())
finally:
    eas.destroy_actor(ship)

# --- Free look all the way round -------------------------------------------------------------
ship = spawn()
try:
    frames = [(0.0, 0.0, 1.0)] + [(30.0, 0.0, 1.0)] * 60 + [(0.0, 0.0, 0.0)] * 90
    out = ship.debug_simulate_free_look([unreal.Vector(*f) for f in frames])
    yaw = [out[2 * i].x for i in range(len(frames))]
    check("free look yaw is not limited", max(yaw[:61]) > 300.0, "reached %.0f deg" % max(yaw[:61]))
    after = yaw[61:]
    check("release swings back the shorter way", abs(after[0]) <= 180.0 + 1e-3 and abs(after[-1]) < 0.01
          and all(abs(after[i + 1]) <= abs(after[i]) + 1e-6 for i in range(len(after) - 1)),
          "from %.1f to %.2f deg" % (after[0], after[-1]))
finally:
    eas.destroy_actor(ship)

# =========================================================================================
# Over Veyra
# =========================================================================================
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
actors = eas.get_all_level_actors()
planet = next(a for a in actors if a.get_actor_label() == "Planet_Veyra")
C = v3(planet.get_actor_location())
R = planet.get_editor_property("radius_km") * 100000.0


def above_surface(direction, altitude_cm):
    d = [c / length(direction) for c in direction]
    probe = unreal.Vector(*[C[k] + d[k] * (R + 1000000.0) for k in range(3)])
    terrain = planet.get_terrain_height_at(probe)
    return unreal.Vector(*[C[k] + d[k] * (R + terrain + altitude_cm) for k in range(3)])


# --- Cruise near the ground ------------------------------------------------------------------
up = (-1.0, 0.0, 0.0)  # the side of Veyra facing PlayerStart
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, above_surface(up, 150000.0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
try:
    to_nav(ship)
    ship.toggle_cruise()
    check("cruise refused 1.5 km above ground", ship.get_cruise_state() == unreal.CruiseState.OFF
          and ship.get_cruise_blocker() == unreal.CruiseBlocker.TOO_LOW)
finally:
    eas.destroy_actor(ship)

# Nose straight down at the planet from 6 km: the limit shrinks with altitude and cruise drops out low.
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, above_surface(up, 600000.0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
try:
    to_nav(ship)
    ship.toggle_cruise()
    run(ship, cdo.get_editor_property("cruise_spool_seconds") + 0.1)
    check("cruise engages 6 km up", ship.get_cruise_state() == unreal.CruiseState.ACTIVE)
    worst = [0.0]
    dropped_at = [None]

    def dive(i, v):
        if ship.get_cruise_state() == unreal.CruiseState.ACTIVE:
            limit = ship.get_cruise_speed_limit()
            worst[0] = max(worst[0], length(v3(v)) / max(limit, 1.0))
        elif dropped_at[0] is None:
            loc = v3(ship.get_actor_location())
            dropped_at[0] = length([loc[k] - C[k] for k in range(3)]) - R

    # debug_step_flight has no mouse, so point the nose at the ground by rotating the actor.
    ship.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(ship.get_actor_location(), unreal.Vector(*C)), False)
    run(ship, 30.0, each=dive)
    check("never faster than the altitude limit", worst[0] < 1.001, "worst %.3f x limit" % worst[0])
    check("drops out close to the ground", dropped_at[0] is not None and ship.get_cruise_blocker() == unreal.CruiseBlocker.TOO_LOW,
          "dropped %.0f m above sea level" % ((dropped_at[0] or 0) / 100.0))
finally:
    eas.destroy_actor(ship)

# --- Exit and hull collision ------------------------------------------------------------------
vanguard = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Ships/Vanguard/Blueprints/BP_Ship_Vanguard")
ship = eas.spawn_actor_from_class(vanguard, above_surface(up, 250.0), unreal.Rotator())
try:
    box = ship.get_editor_property("hull_collision")
    hull = ship.get_editor_property("hull")
    check("root box ignores pawns (no pilot stuck inside it)",
          box.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) == unreal.CollisionResponseType.ECR_IGNORE)
    check("hull mesh blocks pawns and cameras, query only",
          hull.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) == unreal.CollisionResponseType.ECR_BLOCK
          and hull.get_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA) == unreal.CollisionResponseType.ECR_BLOCK
          and hull.get_collision_enabled() == unreal.CollisionEnabled.QUERY_ONLY)
    check("root box ignores cameras (a pilot's camera starting inside it was pulled in to the head)",
          box.get_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA) == unreal.CollisionResponseType.ECR_IGNORE)
    candidates = [v3(c) for c in ship.get_exit_candidates()]
    socket = v3(hull.get_socket_location("Exit"))
    check("exit tries SOCKET_Exit first, then 12 spots around the hull", len(candidates) == 13, "%d candidates" % len(candidates))
    # Ship-local: the ship sits at its spawn rotation (identity), so world offsets are local offsets.
    loc = v3(ship.get_actor_location())
    first = [candidates[0][k] - loc[k] for k in range(3)]
    sock = [socket[k] - loc[k] for k in range(3)]
    clearance_needed = ship.get_editor_property("exit_clearance_cm")
    radius, half = 42.0, 96.0
    raw = ship.get_hull_clearance(unreal.Vector(*socket), radius, half)
    got = ship.get_hull_clearance(unreal.Vector(*candidates[0]), radius, half)
    # Vanguard: socket at (517, 230), belly hull UCX_08 to x 473 / y 244: only 2 cm of room before the fix.
    check("raw SOCKET_Exit spot is too close to the hull (the bug)", raw < clearance_needed, "%.0f cm" % raw)
    check("exit moved sideways out of the hull, same place along it", abs(first[0] - sock[0]) < 1.0 and first[1] > sock[1] + 100.0,
          "socket (%.0f, %.0f) -> (%.0f, %.0f)" % (sock[0], sock[1], first[0], first[1]))
    check("exit spot clear of the hull by ExitClearanceCm", clearance_needed <= got < clearance_needed + 30.0, "%.0f cm" % got)
    worst = min(ship.get_hull_clearance(unreal.Vector(*c), radius, half) for c in candidates)
    check("every exit candidate clear of the hull", worst >= clearance_needed - 0.5, "worst %.0f cm" % worst)
    rings = [length([c[k] - loc[k] for k in range(3)]) for c in candidates[1:]]
    check("fallback spots move outwards", rings[0] < rings[4] < rings[8], "%.0f / %.0f / %.0f m" % (rings[0] / 100, rings[4] / 100, rings[8] / 100))
    # The pilot's eye at the windscreen, checked against the canopy mesh: inside its footprint along
    # the ship, in its top half, well forward of its middle (the seat position had the tinted glass
    # 13 cm from the eye and 0 % open view). The view itself is measured with
    # Tools/Blender/cockpit_view_survey.py: 97.5 % open, only the nose tip at the bottom.
    camera = ship.get_editor_property("cockpit_camera")
    cockpit = v3(camera.get_editor_property("relative_location"))
    rotation = camera.get_editor_property("relative_rotation")
    canopy = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Vanguard/Meshes/SM_Ship_Vanguard_Canopy").get_bounding_box()
    low, high = v3(canopy.min), v3(canopy.max)
    check("cockpit eye at the windscreen, not buried in the canopy bubble",
          low[0] < cockpit[0] < high[0] and cockpit[0] > (low[0] + high[0]) / 2 + 50.0
          and (low[2] + high[2]) / 2 < cockpit[2] < high[2] and abs(cockpit[1]) < 1.0,
          "eye %s, canopy x %.0f..%.0f z %.0f..%.0f" % (cockpit, low[0], high[0], low[2], high[2]))
    check("cockpit camera looks straight ahead", abs(rotation.pitch) < 1e-3 and abs(rotation.yaw) < 1e-3 and abs(rotation.roll) < 1e-3, str(rotation))
    check("free look unlimited on the Vanguard", ship.get_editor_property("free_look_max_yaw_deg") >= 180.0)
finally:
    eas.destroy_actor(ship)

# --- Character safety net ----------------------------------------------------------------------
character = eas.spawn_actor_from_class(unreal.PlayerCharacter, above_surface(up, -300.0), unreal.Rotator())
try:
    moved = character.recover_from_terrain(STEP)
    loc = v3(character.get_actor_location())
    probe_dir = [loc[k] - C[k] for k in range(3)]
    probe = unreal.Vector(*[C[k] + probe_dir[k] / length(probe_dir) * (R + 1000000.0) for k in range(3)])
    clearance = length(probe_dir) - R - planet.get_terrain_height_at(probe) - 96.0
    check("character under the ground is put back on top", moved and character.get_terrain_recovery_count() == 1 and 0.0 < clearance < 80.0,
          "capsule bottom %.0f cm above the terrain" % clearance)
    check("a character on the ground is left alone", not character.recover_from_terrain(STEP))
finally:
    eas.destroy_actor(character)

# --- Scene extras -----------------------------------------------------------------------------
moon = next((a for a in actors if a.get_actor_label() == "Moon_Keth"), None)
giant = next((a for a in actors if a.get_actor_label() == "GasGiant_Orun"), None)
check("moon and gas giant placed", moon is not None and giant is not None)
if moon:
    offset = v3(moon.compute_orbit_offset(0.0))
    check("moon orbit radius", abs(length(offset) - 150.0 * 100000.0) < 1.0, "%.1f km" % (length(offset) / 100000.0))
    quarter = v3(moon.compute_orbit_offset(moon.get_editor_property("orbit_period_seconds") / 4.0))
    dot = sum(offset[k] * quarter[k] for k in range(3)) / (length(offset) * length(quarter))
    check("moon moves a quarter turn in a quarter period", abs(dot) < 1e-3, "cos %.4f" % dot)
if giant:
    distance = length(v3(giant.get_actor_location())) / 100000.0
    dome = next((a for a in actors if a.get_actor_label() == "StarfieldSky"), None)
    dome_km = dome.get_editor_property("dome_radius_km") if dome else 0.0
    check("gas giant and rings inside the sky dome", distance + giant.get_editor_property("ring_outer_radius_km") < dome_km,
          "%.0f km + rings %.0f km, dome %.0f km" % (distance, giant.get_editor_property("ring_outer_radius_km"), dome_km))
for path in ("/Game/Environments/Space/M_SpaceDust", "/Game/Environments/Space/M_GasGiant", "/Game/Environments/Space/M_Moon",
             "/Game/Environments/Space/M_PlanetRings", "/Game/Ships/Audio/SW_EngineHum", "/Game/Ships/Audio/SW_CruiseCharge",
             "/Game/Input/IA_CruiseDrive", "/Game/Input/IA_FlightAssist"):
    check("asset %s" % path.rsplit("/", 1)[1], unreal.EditorAssetLibrary.does_asset_exist(path))
sky = unreal.EditorAssetLibrary.load_asset("/Game/Environments/Space/M_Starfield_Sky")
names = [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(sky)]
check("sky material has nebula, sun and twinkle parameters",
      {"NebulaBrightness", "SunDiscBrightness", "SunGlowBrightness", "Twinkle"} <= set(names), ", ".join(names))
imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Spaceship")
pairs = set()
for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings"):
    a = m.get_editor_property("action")
    pairs.add((str(m.get_editor_property("key").get_editor_property("key_name")), a.get_name() if a else None))
check("V / J / X / wheel / B mapped", {("V", "IA_FlightAssist"), ("J", "IA_CruiseDrive"), ("X", "IA_AllStop"), ("MouseWheelAxis", "IA_CameraZoom"),
                                      ("B", "IA_MasterMode")} <= pairs)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
