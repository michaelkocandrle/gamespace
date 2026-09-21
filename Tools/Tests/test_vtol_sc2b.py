"""Headless checks for SC-2b: VTOL and hovering.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_vtol_sc2b.py

Temporary ships (native SpaceshipPawn defaults) in a new blank map, driven frame by frame (1/60 s)
through the same code as Tick. Deep space: no drag, no gravity, so what the thrusters do is all
there is. Covers:
  1. the switch: SCM only, refused in NAV, dropped when the ship leaves SCM, and the transition takes
     VtolTransitionSeconds rather than snapping
  2. what it does to the thrusters: the mains fall to VtolThrustFraction, the lift and lateral ones gain
  3. speed: the top speed becomes VtolMaxSpeed, the limiter still works inside it, and Space / Ctrl are
     a climb rate (VtolClimbSpeed), not another way of reaching the top speed
  4. what it refuses: the afterburner (and VTOL is SCM only, so never in a quantum jump)
  5. levelling: ComputeVtolLevelStep turns the hull back towards the up it is given, at VtolLevelRate,
     and does nothing without VTOL or without an up
  6. hovering shows on the engines: a vertical thrust of about one G reads as most of the engine demand,
     which is what makes the nozzles glow and the sound rise (it read 0.06 before, HANDOFF kapitola 11)
  7. the HUD's VTOL badge, the input asset on G with no clash, and the shot list
Nothing is saved. Prints "VTOLTEST PASS" / "VTOLTEST FAIL" lines and a summary.
"""

import json
import math
import os

import unreal

STEP = 1.0 / 60.0
G = 980.665
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
failures = []


def log(msg):
    unreal.log("VTOLTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def flat(rotator):
    """A rotator that asks for nothing, to a tenth of a degree."""
    return abs(rotator.pitch) < 0.1 and abs(rotator.roll) < 0.1 and abs(rotator.yaw) < 0.1


def run(ship, seconds, lin=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), boost=False):
    for _ in range(int(round(seconds / STEP))):
        ship.debug_step_flight_input(STEP, unreal.Vector(*lin), unreal.Vector(*rot), boost)
    return v3(ship.get_linear_velocity())


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.new_level("/Temp/VtolTest")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def spawn():
    ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    ship.set_flight_assist(True)
    return ship


probe = spawn()
SCM = probe.get_mode_max_speed()
VTOL_SPEED = probe.get_editor_property("vtol_max_speed")
CLIMB = probe.get_editor_property("vtol_climb_speed")
TRANSITION = probe.get_editor_property("vtol_transition_seconds")
THRUST_FRACTION = probe.get_editor_property("vtol_thrust_fraction")
LIFT_MULTIPLIER = probe.get_editor_property("vtol_lift_multiplier")
STRAFE_MULTIPLIER = probe.get_editor_property("vtol_strafe_multiplier")
LEVEL_RATE = probe.get_editor_property("vtol_level_rate")
eas.destroy_actor(probe)

# ---------------------------------------------------------------------------------------
# 1) The switch
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    check("VTOL starts off", not ship.is_vtol_on() and ship.get_vtol_blend() == 0.0)
    ship.set_vtol(True)
    check("G switches it on", ship.is_vtol_on() and ship.is_vtol_active())
    run(ship, TRANSITION * 0.4)
    part = ship.get_vtol_blend()
    check("the transition is gradual, not a snap", 0.05 < part < 0.85, "%.2f after %.1f s" % (part, TRANSITION * 0.4))
    run(ship, TRANSITION)
    check("fully in after VtolTransitionSeconds", ship.get_vtol_blend() > 0.999, "%.3f" % ship.get_vtol_blend())

    ship.request_master_mode(unreal.MasterMode.NAV)
    ship.debug_finish_master_mode_switch()
    run(ship, TRANSITION * 1.2)
    check("NAV drops VTOL", not ship.is_vtol_on() and ship.get_vtol_blend() < 0.001,
          "on %s, blend %.3f" % (ship.is_vtol_on(), ship.get_vtol_blend()))
    ship.set_vtol(True)
    check("VTOL refused in NAV", not ship.is_vtol_on())
    ship.request_master_mode(unreal.MasterMode.SCM)
    ship.debug_finish_master_mode_switch()
    ship.set_vtol(True)
    check("back in SCM it can be switched on again", ship.is_vtol_on() and ship.is_vtol_active())
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 2) The thrusters
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    run(ship, 0.2, lin=(1, 1, 1))
    before = ship.get_thruster_capacity()
    ship.set_vtol(True)
    run(ship, TRANSITION * 1.5, lin=(1, 1, 1))
    after = ship.get_thruster_capacity()
    main = after[0].x / max(before[0].x, 1.0)
    lift = after[0].z / max(before[0].z, 1.0)
    strafe = after[0].y / max(before[0].y, 1.0)
    check("the mains fall to VtolThrustFraction", abs(main - THRUST_FRACTION) < 0.02, "%.2f of %.2f" % (main, THRUST_FRACTION))
    check("the lift thrusters gain VtolLiftMultiplier", abs(lift - LIFT_MULTIPLIER) < 0.02, "%.2f of %.2f" % (lift, LIFT_MULTIPLIER))
    check("the lateral thrusters gain VtolStrafeMultiplier", abs(strafe - STRAFE_MULTIPLIER) < 0.02,
          "%.2f of %.2f" % (strafe, STRAFE_MULTIPLIER))
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 3) Speed and the climb rate
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    ship.set_vtol(True)
    run(ship, TRANSITION * 1.5)
    check("top speed becomes VtolMaxSpeed", abs(ship.get_mode_max_speed() - VTOL_SPEED) < 1.0,
          "%.1f m/s of %.1f" % (ship.get_mode_max_speed() / 100, VTOL_SPEED / 100))
    check("VTOL is slower than SCM", VTOL_SPEED < SCM, "%.0f < %.0f cm/s" % (VTOL_SPEED, SCM))
    ship.set_speed_limiter(0.5)
    check("the limiter still works inside VTOL", abs(ship.get_speed_limit() - 0.5 * VTOL_SPEED) < 1.0)
    ship.set_speed_limiter(1.0)
    forward = run(ship, 25.0, lin=(1, 0, 0))
    check("W settles at the VTOL speed", abs(forward[0] - VTOL_SPEED) < 0.03 * VTOL_SPEED, "%.1f m/s" % (forward[0] / 100))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    ship.set_vtol(True)
    run(ship, TRANSITION * 1.5)
    up = run(ship, 20.0, lin=(0, 0, 1))
    check("Space climbs at VtolClimbSpeed, not at the top speed", abs(up[2] - CLIMB) < 0.05 * CLIMB,
          "%.1f m/s of %.1f" % (up[2] / 100, CLIMB / 100))
    down = run(ship, 20.0, lin=(0, 0, -1))
    check("Ctrl sinks at the same rate", abs(down[2] + CLIMB) < 0.05 * CLIMB, "%.1f m/s" % (down[2] / 100))
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 4) What VTOL refuses
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    ship.set_vtol(True)
    run(ship, TRANSITION * 1.5)
    ship.set_afterburner_held(True)
    run(ship, 2.0, lin=(1, 0, 0))
    check("the afterburner is refused in VTOL", not ship.is_afterburner_active())
    ship.set_afterburner_held(False)
    ship.set_vtol(False)
    run(ship, TRANSITION * 1.5)
    ship.set_afterburner_held(True)
    run(ship, 0.5, lin=(1, 0, 0))
    check("and works again once VTOL is off", ship.is_afterburner_active())
    ship.set_afterburner_held(False)
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 5) Levelling
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    ship.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=20.0, yaw=0.0), False)
    up = unreal.Vector(0, 0, 1)
    check("no levelling without VTOL", flat(ship.compute_vtol_level_step(up, STEP)))
    ship.set_vtol(True)
    run(ship, TRANSITION * 1.5)
    step = ship.compute_vtol_level_step(up, 1.0)
    # 20 degrees of error and 25 deg/s of authority: one second takes all 20 of it, nose down.
    check("nose down towards the horizon", abs(step.pitch + 20.0) < 0.5, "pitch %.1f deg" % step.pitch)
    ship.set_actor_rotation(unreal.Rotator(roll=30.0, pitch=0.0, yaw=0.0), False)
    step = ship.compute_vtol_level_step(up, 1.0)
    # 30 degrees of error is more than a second of authority, so the step is the rate.
    check("and rolls back the other way, no faster than VtolLevelRate", abs(step.roll + LEVEL_RATE) < 0.5,
          "roll %.1f deg of %.1f" % (step.roll, LEVEL_RATE))
    ship.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=45.0), False)
    check("level already: nothing to do (yaw is the pilot's)", flat(ship.compute_vtol_level_step(up, 1.0)),
          str(ship.compute_vtol_level_step(up, 1.0)))
    check("no up, no levelling", flat(ship.compute_vtol_level_step(unreal.Vector(0, 0, 0), 1.0)))
    # A small step never overshoots: the clamp is the rate, the error is what is left.
    ship.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=2.0, yaw=0.0), False)
    small = ship.compute_vtol_level_step(up, 1.0)
    check("a small error is corrected in one go, not overshot", abs(small.pitch + 2.0) < 0.2, "%.2f deg" % small.pitch)
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 6) Hovering shows on the engines
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    ship.set_flight_assist(False)          # decoupled: the keys are the thrusters, nothing else
    caps = ship.get_thruster_capacity()
    share = G / max(caps[0].z, 1.0)        # the lift input that gives about one G
    run(ship, 0.5, lin=(0, 0, share))
    demand = ship.get_engine_demand()
    check("a hover's worth of vertical thrust reads as most of the engine demand",
          demand > 0.7, "%.2f at %.2f of the lift thrusters" % (demand, share))
    run(ship, 0.5, lin=(0, 0, 0))
    check("and nothing held reads as nothing", ship.get_engine_demand() < 0.05, "%.2f" % ship.get_engine_demand())
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 7) HUD, input, shot list
# ---------------------------------------------------------------------------------------
hud = unreal.new_object(unreal.SpaceFlightHud)
hud.debug_initialize()
names = set(hud.debug_get_widget_names())
check("the HUD has a VTOL badge", "Lamp_VTOL" in names)

by_key = {}
for path in unreal.EditorAssetLibrary.list_assets("/Game/Input", recursive=False):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.InputMappingContext):
        continue
    # default_key_mappings, not the deprecated "mappings": add_mappings writes the new struct, and the
    # old property does not always show what was added (20. 9. 2026, the VTOL key was invisible there).
    for mapping in asset.get_editor_property("default_key_mappings").get_editor_property("mappings"):
        action = mapping.get_editor_property("action")
        key = mapping.get_editor_property("key").get_editor_property("key_name")
        if action:
            by_key.setdefault(str(key), set()).add(action.get_name())
check("G mapped to IA_Vtol only", by_key.get("G") == {"IA_Vtol"}, str(by_key.get("G")))

shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "vtol.json"), encoding="utf-8"))["shots"]
known = {"name", "camera", "hud", "altitude_m", "facing", "speed_ms", "mode", "limiter", "coupled", "gsafe", "comstab",
         "boost", "afterburner", "stick", "settle", "cockpit_eye", "hide_hull", "hide_canopy", "gear", "lower_gear",
         "precision", "chase_yaw", "chase_pitch", "chase_zoom", "console", "_comment"}
unknown = sorted({k for s in shots for k in s} - known)
check("the VTOL shot list uses only fields the runner reads", not unknown and len(shots) >= 4, str(unknown))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
