"""Headless checks for SC-4: the quantum drive, which replaced the cruise drive.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_quantum_sc4.py

Follows the sequence in starcitizenreference/QuantumTravel_VideoNotes.md: nothing in SCM; in NAV
the body in front of the nose is the destination, the drive spools on its own and calibrates while
the nose is on it; READY, then the left mouse button held jumps; no steering in the jump; the ship
arrives above the destination at NAV speed and the drive cools down. Blocked: too close, a body in
the way, not enough fuel. The HUD says each of these the way the reference does.

Runs in TestSpace (Veyra 45 km ahead of PlayerStart, Keth, Orun 620 km off to the side), frame by
frame through SpaceshipPawn.debug_step_flight. Nothing is saved.
Prints "QTTEST PASS" / "QTTEST FAIL" lines and a summary.
"""

import json
import math
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEVEL = "/Game/Maps/TestSpace"
STEP = 1.0 / 60.0
failures = []


def log(msg):
    unreal.log("QTTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def sub(a, b):
    return tuple(a[k] - b[k] for k in range(3))


def length(a):
    return math.sqrt(sum(c * c for c in a))


def run(ship, seconds, each=None, rotation=None):
    for i in range(int(round(seconds / STEP))):
        if rotation is not None:
            ship.debug_step_flight_input(STEP, unreal.Vector(0.0, 0.0, 0.0), unreal.Vector(*rotation), False)
        else:
            ship.debug_step_flight(STEP, 0.0, 0.0, 0.0, False)
        if each and each(i):
            return i * STEP
    return seconds


cdo = unreal.get_default_object(unreal.SpaceshipPawn)
SPOOL = cdo.get_editor_property("quantum_spool_seconds")
CALIBRATE = cdo.get_editor_property("quantum_calibration_seconds")
HOLD = cdo.get_editor_property("quantum_engage_hold_seconds")
COOL = cdo.get_editor_property("quantum_cooldown_seconds")
EXIT = cdo.get_editor_property("quantum_exit_speed")
TOP = cdo.get_editor_property("quantum_max_speed_km_s") * 100000.0
SWITCH = cdo.get_editor_property("master_mode_switch_seconds")
State = unreal.QuantumState
Blocker = unreal.QuantumBlocker

# --- The numbers on their own ---------------------------------------------------------------
check("arrival: 0.6 radii up, never under 15 km",
      abs(cdo.compute_quantum_arrival_altitude(2500000.0) - 1500000.0) < 1.0
      and abs(cdo.compute_quantum_arrival_altitude(15000000.0) - 9000000.0) < 1.0)
check("fuel: 12 % per 1000 km", abs(cdo.compute_quantum_fuel_use(1.0e8) - 0.12) < 1e-4)
check("a body on the segment blocks it, one beside it does not",
      unreal.SpaceshipPawn.segment_hits_sphere(unreal.Vector(0, 0, 0), unreal.Vector(1000, 0, 0), unreal.Vector(500, 50, 0), 100.0)
      and not unreal.SpaceshipPawn.segment_hits_sphere(unreal.Vector(0, 0, 0), unreal.Vector(1000, 0, 0), unreal.Vector(500, 200, 0), 100.0)
      and not unreal.SpaceshipPawn.segment_hits_sphere(unreal.Vector(0, 0, 0), unreal.Vector(1000, 0, 0), unreal.Vector(1300, 0, 0), 100.0))

# A 600 km jump with the speed profile alone: rises, holds the top, brakes to the exit speed.
remaining, speed, elapsed, peak = 6.0e7, EXIT, 0.0, 0.0
while remaining > 0.0 and elapsed < 300.0:
    speed = cdo.compute_quantum_speed(remaining, speed, STEP)
    peak = max(peak, speed)
    remaining -= speed * STEP
    elapsed += STEP
check("a 600 km jump takes seconds, not minutes", 10.0 < elapsed < 60.0, "%.1f s" % elapsed)
check("and never goes over the top speed", peak <= TOP + 1.0, "%.1f km/s" % (peak / 100000.0))
check("it arrives at the exit speed", abs(cdo.compute_quantum_speed(0.0, TOP, STEP) - EXIT) < 1.0)

# The start eases in: after half a second of a jump it is still slow, after the ramp at full acceleration.
RAMP = cdo.get_editor_property("quantum_ramp_seconds")
speed, t = EXIT, 0.0
while t < 0.5:
    speed = cdo.compute_quantum_speed_at(6.0e7, speed, STEP, t)
    t += STEP
check("half a second in, still under 1 km/s (the author: it snapped to full speed)", speed < 100000.0, "%.0f m/s" % (speed / 100.0))
early = cdo.compute_quantum_speed_at(6.0e7, 500000.0, STEP, 0.1) - 500000.0
late = cdo.compute_quantum_speed_at(6.0e7, 500000.0, STEP, RAMP + 0.1) - 500000.0
check("and the acceleration builds up over the ramp", 0.0 < early < 0.2 * late, "%.0f vs %.0f cm/s per frame" % (early, late))

# =========================================================================================
# TestSpace
# =========================================================================================
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()
planet = next(a for a in actors if a.get_actor_label() == "Planet_Veyra")
giant = next(a for a in actors if a.get_actor_label() == "GasGiant_Orun")
VEYRA = v3(planet.get_actor_location())
VEYRA_R = planet.get_editor_property("radius_km") * 100000.0
ORUN = v3(giant.get_actor_location())
ORUN_R = giant.get_radius_km() * 100000.0
START = (0.0, 0.0, 300.0)


def spawn(location=START, look_at=None):
    rotation = unreal.Rotator()
    if look_at is not None:
        rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*look_at))
    return eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(*location), rotation)


def to_nav(ship):
    ship.request_master_mode(unreal.MasterMode.NAV)
    run(ship, SWITCH + 0.05)


def hud(ship):
    return unreal.SpaceFlightHud.make_state(ship, 1)


# --- SCM, and a destination too close -------------------------------------------------------
ship = spawn()
try:
    run(ship, 0.5)
    check("SCM: no quantum drive", ship.get_quantum_state() == State.IDLE and ship.get_quantum_blocker() == Blocker.NEEDS_NAV)
    widget = unreal.new_object(unreal.SpaceFlightHud)
    widget.debug_initialize()
    widget.apply_state(hud(ship))
    check("SCM: the afterburner block is the afterburner", widget.debug_get_text("AfterburnerLabel").startswith("AB"),
          widget.debug_get_text("AfterburnerLabel"))
    state = hud(ship)
    check("SCM: no arcs, no status, no destination on the HUD",
          state.quantum_arcs == 0 and state.quantum_status == "" and not state.quantum_target_visible)
    to_nav(ship)
    check("NAV: the planet ahead is the destination", ship.has_quantum_target() and str(ship.get_quantum_target_name()) == "Veyra",
          str(ship.get_quantum_target_name()))
    check("but 20 km up it is too close to jump to", ship.get_quantum_blocker() == Blocker.TOO_CLOSE,
          "%.1f km to the arrival point" % (ship.get_quantum_target_distance() / 100000.0))
    check("the HUD says so", hud(ship).quantum_status == "TOO CLOSE", hud(ship).quantum_status)
finally:
    eas.destroy_actor(ship)

# --- The whole jump to Orun -----------------------------------------------------------------
ship = spawn(look_at=ORUN)
try:
    to_nav(ship)
    check("nose on Orun picks it", str(ship.get_quantum_target_name()) == "Orun", str(ship.get_quantum_target_name()))
    # NAV swaps the afterburner block for the quantum fuel, as SC swaps weapons for fuel (22. 9. 2026).
    widget = unreal.new_object(unreal.SpaceFlightHud)
    widget.debug_initialize()
    widget.apply_state(hud(ship))
    check("NAV: the HUD shows QT FUEL where the afterburner is", widget.debug_get_text("AfterburnerLabel") == "QT FUEL"
          and widget.debug_get_text("AfterburnerValue") == "%.0f%%" % (100.0 * ship.get_quantum_fuel()),
          "%s %s" % (widget.debug_get_text("AfterburnerLabel"), widget.debug_get_text("AfterburnerValue")))
    check("and it is in reach", ship.get_quantum_blocker() == Blocker.NONE, str(ship.get_quantum_blocker()))
    run(ship, SPOOL * 0.5)
    state = hud(ship)
    check("half way through the spool: SPOOLING on the HUD, violet arcs", state.quantum_status.startswith("SPOOLING")
          and state.quantum_arcs == 1 and ship.get_quantum_state() == State.CHARGING, state.quantum_status)
    run(ship, SPOOL * 0.5 + 0.1)
    check("spooled: CALIBRATING", hud(ship).quantum_status.startswith("CALIBRATING") or ship.get_quantum_state() == State.READY,
          hud(ship).quantum_status)
    run(ship, CALIBRATE + 0.1)
    state = hud(ship)
    check("calibrated: READY, green arcs", ship.get_quantum_state() == State.READY and state.quantum_status == "READY"
          and state.quantum_arcs == 2, "%s %s" % (ship.get_quantum_state(), state.quantum_status))
    check("the destination is in the middle of the HUD", state.quantum_target_visible, state.quantum_target_range)

    fuel_before = ship.get_quantum_fuel()
    distance = ship.get_quantum_target_distance()
    ship.set_quantum_engage_held(True)
    run(ship, HOLD * 0.5)
    check("a short press does not jump", ship.get_quantum_state() == State.READY)
    run(ship, HOLD * 0.5 + 0.05)
    check("held QuantumEngageHoldSeconds: jumping", ship.get_quantum_state() == State.TRAVELING)
    ship.set_quantum_engage_held(False)
    check("the fuel for the distance is burnt", abs((fuel_before - ship.get_quantum_fuel()) - cdo.compute_quantum_fuel_use(distance)) < 1e-3,
          "%.1f %% for %.0f km" % (100.0 * (fuel_before - ship.get_quantum_fuel()), distance / 100000.0))

    # Full stick while jumping: the nose stays on Orun.
    run(ship, 3.0, rotation=(1.0, 1.0, 1.0))
    to_orun = sub(ORUN, v3(ship.get_actor_location()))
    forward = v3(ship.get_actor_forward_vector())
    angle = math.degrees(math.acos(max(-1.0, min(1.0, sum(forward[k] * to_orun[k] for k in range(3)) / length(to_orun)))))
    check("no steering in a jump", angle < 1.0, "%.2f deg off" % angle)
    check("fast", length(v3(ship.get_linear_velocity())) > 1.0e6, "%.1f km/s" % (length(v3(ship.get_linear_velocity())) / 100000.0))

    took = run(ship, 90.0, each=lambda i: ship.get_quantum_state() != State.TRAVELING)
    altitude = length(sub(v3(ship.get_actor_location()), ORUN)) - ORUN_R
    check("arrives in under a minute", ship.get_quantum_state() == State.COOLING, "%.1f s more" % took)
    check("above Orun at the arrival altitude", abs(altitude - cdo.compute_quantum_arrival_altitude(ORUN_R)) < 500000.0,
          "%.0f km up" % (altitude / 100000.0))
    check("at NAV speed", length(v3(ship.get_linear_velocity())) <= EXIT + 1.0)
    state = hud(ship)
    check("cooling: COOLING on the HUD, red arcs", state.quantum_status.startswith("COOLING") and state.quantum_arcs == 3,
          state.quantum_status)
    run(ship, COOL * 0.5)
    check("no second jump while cooling", ship.get_quantum_state() == State.COOLING)
    run(ship, COOL * 0.5 + 0.2)
    check("cool again after QuantumCooldownSeconds", ship.get_quantum_state() != State.COOLING, str(ship.get_quantum_state()))
finally:
    eas.destroy_actor(ship)

# --- Leaving NAV mid-jump drops out where the ship is ------------------------------------------
ship = spawn(look_at=ORUN)
try:
    ship.debug_engage_quantum("Orun", 0.3)
    run(ship, 0.5)
    ship.request_master_mode(unreal.MasterMode.SCM)
    run(ship, 0.1)
    # The blocker then reads NEEDS_NAV (SCM), which is what the drive has to say from here on.
    check("B to SCM ends the jump", ship.get_quantum_state() == State.COOLING and length(v3(ship.get_linear_velocity())) <= EXIT + 1.0,
          "%s, %.0f m/s" % (ship.get_quantum_state(), length(v3(ship.get_linear_velocity())) / 100.0))
finally:
    eas.destroy_actor(ship)

# --- Veyra between the ship and Orun ----------------------------------------------------------
# Behind Veyra as seen from Orun, and 0.6 radii off the line through its centre: the nose on Orun
# picks Orun (Veyra's centre is well off the nose), but the path still cuts through Veyra.
away = sub(VEYRA, ORUN)
away = tuple(c / length(away) for c in away)
side = (away[1], -away[0], 0.0)
side = tuple(c / length(side) for c in side)
behind = tuple(VEYRA[k] + away[k] * (VEYRA_R + 4000000.0) + side[k] * 0.6 * VEYRA_R for k in range(3))
ship = spawn(location=behind, look_at=ORUN)
try:
    to_nav(ship)
    check("a planet in the way: OBSTRUCTED", ship.get_quantum_blocker() == Blocker.OBSTRUCTED and hud(ship).quantum_status == "OBSTRUCTED",
          "%s, %s" % (ship.get_quantum_blocker(), str(ship.get_quantum_target_name())))
    run(ship, SPOOL + CALIBRATE + 0.5)
    check("and it never gets ready", ship.get_quantum_state() != State.READY)
finally:
    eas.destroy_actor(ship)

# --- Out of fuel ------------------------------------------------------------------------------
ship = spawn(look_at=ORUN)
try:
    ship.debug_set_quantum_fuel(0.01)
    to_nav(ship)
    check("not enough fuel: NO QT FUEL", ship.get_quantum_blocker() == Blocker.NO_FUEL and hud(ship).quantum_status == "NO QT FUEL")
finally:
    eas.destroy_actor(ship)

# --- Turning off the destination --------------------------------------------------------------
ship = spawn(look_at=ORUN)
try:
    to_nav(ship)
    run(ship, SPOOL + CALIBRATE + 0.2)
    check("ready on Orun", ship.get_quantum_state() == State.READY)
    ship.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(ship.get_actor_location(),
                            unreal.Vector(*[ORUN[k] + 0.35 * length(sub(ORUN, START)) * (1.0 if k == 2 else 0.0) for k in range(3)])), False)
    run(ship, 0.3)
    check("nose off it: not ready, calibration falling", ship.get_quantum_state() != State.READY and ship.get_quantum_calibration() < 1.0,
          "%s, calibration %.2f" % (ship.get_quantum_state(), ship.get_quantum_calibration()))
    check("the destination stays (still within the pick cone)", str(ship.get_quantum_target_name()) == "Orun")
finally:
    eas.destroy_actor(ship)

# --- HUD, input, shots ------------------------------------------------------------------------
widget = unreal.new_object(unreal.SpaceFlightHud)
widget.debug_initialize()
names = set(widget.debug_get_widget_names())
wanted = {"QuantumArcs", "QuantumTarget", "QuantumArrow", "QuantumTargetName", "QuantumTargetRange", "QuantumStatusBox", "QuantumStatus"}
check("the HUD has the quantum parts", wanted <= names, str(sorted(wanted - names)))

imc = unreal.load_asset("/Game/Input/IMC_Spaceship")
pairs = {(str(m.get_editor_property("key").get_editor_property("key_name")),
          m.get_editor_property("action").get_name() if m.get_editor_property("action") else "")
         for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")}
check("left mouse button jumps", ("LeftMouseButton", "IA_QuantumEngage") in pairs)
check("J no longer does anything", not any(key == "J" for key, _ in pairs), str(sorted(p for p in pairs if p[0] == "J")))

shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "quantum.json"), encoding="utf-8"))["shots"]
known = {"name", "camera", "hud", "altitude_m", "facing", "speed_ms", "drift", "mode", "limiter", "coupled", "gsafe",
         "comstab", "boost", "afterburner", "stick", "settle", "cockpit_eye", "hide_hull", "hide_canopy", "gear",
         "lower_gear", "precision", "chase_yaw", "chase_pitch", "chase_zoom", "console", "quantum", "quantum_progress",
         "quantum_ready", "_comment"}
unknown = sorted({k for shot in shots for k in shot} - known)
check("the quantum shot list uses only fields the runner reads", not unknown, str(unknown))
check("and shows the charge, READY, the jump from outside and inside",
      any("quantum" in s for s in shots) and any(s.get("quantum_ready") for s in shots)
      and any("quantum" in s and s["camera"] == "chase" for s in shots) and any("quantum" in s and s["camera"] == "cockpit" for s in shots))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
