"""Headless checks for SC-1b: boost and afterburner as two separate systems.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_boost_afterburner_sc1b.py

Drives temporary ships (native SpaceshipPawn defaults) frame by frame (1/60 s) in a new blank map
(deep space) through SpaceshipPawn.debug_step_flight_input, the same code as Tick.

- Boost (Shift): manoeuvring thrusters (retro, strafe, up, down) and rotation stronger, main thrust
  and speed limit unchanged, G-Safe suspended while it burns, energy drains without W.
- Afterburner (Tab): main thrust stronger, speed limit SCM x AfterburnerSpeedMultiplier x limiter,
  own fuel (drain, lock when empty, delayed slow refill), smooth fade back, SCM only, coupled and
  decoupled, G-Safe still on.
Nothing is saved. Prints "SC1BTEST PASS" / "SC1BTEST FAIL" lines and a summary.
"""

import math

import unreal

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import ship_under_test as sut  # noqa: E402

STEP = 1.0 / 60.0
G = 980.665
failures = []


def log(msg):
    unreal.log("SC1BTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def length(a):
    return math.sqrt(sum(c * c for c in a))


def run(ship, seconds, lin=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), boost=False, afterburner=False, each=None):
    """lin = (thrust, strafe, lift), rot = (roll, pitch, yaw), held for `seconds`."""
    ship.set_afterburner_held(afterburner)
    velocity = None
    for i in range(int(round(seconds / STEP))):
        velocity = ship.debug_step_flight_input(STEP, unreal.Vector(*lin), unreal.Vector(*rot), boost)
        if each:
            each(i, velocity)
    ship.set_afterburner_held(False)
    return v3(velocity) if velocity else v3(ship.get_linear_velocity())


def decel_watch():
    """each-callback recording the largest speed drop per second between frames, and the last speed."""
    state = {"prev": None, "max": 0.0}

    def each(i, v):
        speed = length(v3(v))
        if state["prev"] is not None:
            state["max"] = max(state["max"], (state["prev"] - speed) / STEP)
        state["prev"] = speed

    return state, each


eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cdo = unreal.get_default_object(unreal.SpaceshipPawn)
P = {name: cdo.get_editor_property(name) for name in (
    "thrust_acceleration", "retro_acceleration", "strafe_acceleration", "lift_acceleration", "scm_max_speed", "yaw_rate",
    "yaw_acceleration", "g_safe_max_g", "g_safe_turn_g", "g_safe_min_turn_fraction", "boost_maneuver_multiplier",
    "boost_rotation_multiplier", "boost_duration_seconds", "afterburner_thrust_multiplier", "afterburner_speed_multiplier",
    "afterburner_duration_seconds", "afterburner_refill_seconds", "afterburner_refill_delay_seconds",
    "afterburner_unlock_fraction", "afterburner_fade_seconds", "master_mode_switch_seconds")}
SCM = P["scm_max_speed"]
AB_SPEED = SCM * P["afterburner_speed_multiplier"]
log("INFO boost: manoeuvring x%.2f, rotation x%.2f; afterburner: thrust x%.2f, speed x%.2f (%.0f m/s), %.0f s fuel, refill %.0f s" % (
    P["boost_maneuver_multiplier"], P["boost_rotation_multiplier"], P["afterburner_thrust_multiplier"],
    P["afterburner_speed_multiplier"], AB_SPEED / 100, P["afterburner_duration_seconds"], P["afterburner_refill_seconds"]))

unreal.EditorLoadingAndSavingUtils.new_blank_map(False)


def spawn():
    return eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())


# =====================================================================================================
# Boost
# =====================================================================================================
ship = spawn()
try:
    ship.set_g_safe(False)
    v = run(ship, 0.5, lin=(1, 0, 0), boost=True)
    check("boost does not strengthen the main thrusters", abs(v[0] / 0.5 - P["thrust_acceleration"]) < 0.03 * P["thrust_acceleration"],
          "%.2f G" % (v[0] / 0.5 / G))
    run(ship, 10.0, lin=(1, 0, 0), boost=False)
    limits = []
    v = run(ship, 3.0, lin=(1, 0, 0), boost=True, each=lambda i, vel: limits.append(ship.get_speed_limit()))
    check("boost does not raise the speed limit or top speed", max(limits) <= SCM + 0.5 and length(v) <= SCM * 1.005,
          "limit %.0f m/s, speed %.1f m/s" % (max(limits) / 100, length(v) / 100))
    v0 = v
    v1 = run(ship, 0.5, boost=True)
    retro = P["retro_acceleration"] * P["boost_maneuver_multiplier"]
    check("boost strengthens the retro thrusters", abs((v0[0] - v1[0]) / 0.5 - retro) < 0.03 * retro, "%.2f G" % ((v0[0] - v1[0]) / 0.5 / G))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    v = run(ship, 0.5, lin=(0, 1, 0), boost=True)
    strafe = P["strafe_acceleration"] * P["boost_maneuver_multiplier"]
    check("boost strengthens strafe - past GSafeMaxG, so G-Safe is suspended", abs(v[1] / 0.5 - strafe) < 0.03 * strafe and strafe > P["g_safe_max_g"] * G,
          "%.2f G (G-Safe cap %.1f G)" % (v[1] / 0.5 / G, P["g_safe_max_g"]))
    check("G-Safe switched on but not active while boosting", ship.is_g_safe_on() and not ship.is_g_safe_active())
    run(ship, 6.0)
    check("G-Safe active again after boost", ship.is_g_safe_active())
    v1 = run(ship, 0.5, lin=(0, 0, 1), boost=True)
    up = P["lift_acceleration"] * P["boost_maneuver_multiplier"]
    check("boost strengthens the up thrusters", abs(v1[2] / 0.5 - up) < 0.03 * up, "%.2f G" % (v1[2] / 0.5 / G))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    run(ship, 0.1, rot=(0, 0, 1), boost=True)
    rate = ship.get_editor_property("angular_velocity").z
    check("boost: yaw rate builds up faster (rotational acceleration x BoostRotationMultiplier)",
          P["yaw_acceleration"] * 0.1 + 0.5 < rate <= P["yaw_acceleration"] * P["boost_rotation_multiplier"] * 0.1 + 0.5, "%.1f deg/s after 0.1 s" % rate)
    run(ship, 2.0, rot=(0, 0, 1), boost=True)
    rate = ship.get_editor_property("angular_velocity").z
    expected = P["yaw_rate"] * P["boost_rotation_multiplier"]
    check("boost: full yaw rate x BoostRotationMultiplier", abs(rate - expected) < 0.02 * expected, "%.1f deg/s, expected %.1f" % (rate, expected))
finally:
    eas.destroy_actor(ship)


def turn_rate_at_speed(boost):
    s = spawn()
    try:
        s.set_com_stab(False)
        run(s, 8.0, lin=(1, 0, 0))
        run(s, 2.0, lin=(1, 0, 0), rot=(0, 0, 1), boost=boost)
        return s.get_editor_property("angular_velocity").z
    finally:
        eas.destroy_actor(s)


limited = max(math.degrees(P["g_safe_turn_g"] * G / SCM), P["yaw_rate"] * P["g_safe_min_turn_fraction"])
plain, boosted = turn_rate_at_speed(False), turn_rate_at_speed(True)
check("boost lifts G-Safe's turn limit at speed", plain < limited * 1.06 and abs(boosted - P["yaw_rate"] * P["boost_rotation_multiplier"]) < 0.03 * P["yaw_rate"] * P["boost_rotation_multiplier"],
      "%.1f deg/s without, %.1f deg/s with boost (G-Safe limit %.1f)" % (plain, boosted, limited))

ship = spawn()
try:
    frames = [0]
    run(ship, P["boost_duration_seconds"] + 0.5, boost=True, each=lambda i, v: frames.__setitem__(0, frames[0] + (1 if ship.is_boosting() else 0)))
    check("boost burns energy without W (it feeds the manoeuvring thrusters)", abs(frames[0] * STEP - P["boost_duration_seconds"]) < 0.1 and ship.is_boost_locked(),
          "%.2f s" % (frames[0] * STEP))
finally:
    eas.destroy_actor(ship)

# =====================================================================================================
# Afterburner
# =====================================================================================================
ship = spawn()
try:
    run(ship, 2.0, afterburner=True)
    check("Tab without W burns nothing", not ship.is_afterburner_active() and ship.get_afterburner_fuel() == 1.0)
    ship.set_g_safe(False)
    v = run(ship, 0.5, lin=(1, 0, 0), afterburner=True)
    main = P["thrust_acceleration"] * P["afterburner_thrust_multiplier"]
    check("afterburner strengthens the main thrusters (G-Safe off)", abs(v[0] / 0.5 - main) < 0.03 * main, "%.2f G" % (v[0] / 0.5 / G))
    ship.set_g_safe(True)
    before = v[0]
    v = run(ship, 0.5, lin=(1, 0, 0), afterburner=True)
    capped = min(main, P["g_safe_max_g"] * G)
    check("afterburner keeps G-Safe on: acceleration capped at GSafeMaxG", ship.is_g_safe_active() and abs((v[0] - before) / 0.5 - capped) < 0.03 * capped,
          "%.2f G" % ((v[0] - before) / 0.5 / G))
    v = run(ship, 6.5, lin=(1, 0, 0), afterburner=True)
    check("afterburner flies at SCM x AfterburnerSpeedMultiplier at a full limiter", abs(v[0] - AB_SPEED) < 0.01 * AB_SPEED,
          "%.1f m/s (%.1f m/s)" % (v[0] / 100, AB_SPEED / 100))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    v = run(ship, 0.5, lin=(0, 1, 0), afterburner=True)
    check("afterburner does not strengthen the manoeuvring thrusters", abs(v[1] / 0.5 - P["strafe_acceleration"]) < 0.03 * P["strafe_acceleration"],
          "%.2f G" % (v[1] / 0.5 / G))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    ship.set_speed_limiter(0.5)
    peak = [0.0]
    v = run(ship, 6.0, lin=(1, 0, 0), afterburner=True, each=lambda i, vel: peak.__setitem__(0, max(peak[0], length(v3(vel)))))
    check("afterburner respects the limiter: 50 % gives 50 % of its top speed", abs(peak[0] - 0.5 * AB_SPEED) < 0.01 * AB_SPEED,
          "peak %.1f m/s, expected %.1f (not %.1f)" % (peak[0] / 100, 0.5 * AB_SPEED / 100, AB_SPEED / 100))
finally:
    eas.destroy_actor(ship)

# Decoupled: thrust and limit work the same; the fade brings speed back smoothly with nothing held.
ship = spawn()
try:
    ship.set_flight_assist(False)
    ship.set_g_safe(False)
    v = run(ship, 5.0, lin=(1, 0, 0), afterburner=True)
    check("decoupled: afterburner reaches its top speed", abs(length(v) - AB_SPEED) < 0.01 * AB_SPEED, "%.1f m/s" % (length(v) / 100))
    ship.set_g_safe(True)
    state, each = decel_watch()
    v = run(ship, P["afterburner_fade_seconds"] + 4.0, each=each)
    check("decoupled: released, speed falls back to SCM top speed", abs(length(v) - SCM) < 0.01 * SCM, "%.1f m/s" % (length(v) / 100))
    check("decoupled: smoothly (no snap)", state["max"] < 8.0 * G, "worst %.1f G" % (state["max"] / G))
finally:
    eas.destroy_actor(ship)

# Coupled: fuel runs out while burning.
ship = spawn()
try:
    frames = [0]
    state, each = decel_watch()

    def burn(i, v):
        if ship.is_afterburner_active():
            frames[0] += 1
        each(i, v)

    run(ship, P["afterburner_duration_seconds"] + P["afterburner_fade_seconds"] + 4.0, lin=(1, 0, 0), afterburner=True, each=burn)
    check("a full tank burns for AfterburnerDurationSeconds", abs(frames[0] * STEP - P["afterburner_duration_seconds"]) < 0.1,
          "%.2f s" % (frames[0] * STEP))
    check("empty tank switches the afterburner off and locks it", not ship.is_afterburner_active() and ship.is_afterburner_locked()
          and ship.get_afterburner_fuel() < 0.2)
    speed = length(v3(ship.get_linear_velocity()))
    check("coupled: back to the SCM limit after running dry", abs(speed - SCM) < 0.01 * SCM, "%.1f m/s" % (speed / 100))
    check("coupled: slowing down is smooth (retro limit, no snap)", state["max"] < 8.0 * G, "worst %.1f G" % (state["max"] / G))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    frames = 0
    ship.set_afterburner_held(True)
    while not ship.is_afterburner_locked() and frames < 2000:
        ship.debug_step_flight_input(STEP, unreal.Vector(1, 0, 0), unreal.Vector(0, 0, 0), False)
        frames += 1
    ship.set_afterburner_held(False)
    delay = P["afterburner_refill_delay_seconds"]
    run(ship, delay - 0.05)
    check("no refill during AfterburnerRefillDelaySeconds", ship.get_afterburner_fuel() < 0.005, "%.4f" % ship.get_afterburner_fuel())
    run(ship, 0.05)
    start = ship.get_afterburner_fuel()
    run(ship, 2.0)
    rate = (ship.get_afterburner_fuel() - start) / 2.0
    check("refills slowly at 1 / AfterburnerRefillSeconds", abs(rate - 1.0 / P["afterburner_refill_seconds"]) < 0.002, "%.4f per s" % rate)
    run(ship, 0.5, lin=(1, 0, 0), afterburner=True)
    check("still locked below AfterburnerUnlockFraction", ship.is_afterburner_locked() and not ship.is_afterburner_active(),
          "fuel %.2f" % ship.get_afterburner_fuel())
    run(ship, (P["afterburner_unlock_fraction"] - ship.get_afterburner_fuel()) * P["afterburner_refill_seconds"] + 0.2)
    run(ship, STEP, lin=(1, 0, 0), afterburner=True)
    check("lights again once AfterburnerUnlockFraction is back", ship.is_afterburner_active(), "fuel %.2f" % ship.get_afterburner_fuel())
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    ship.request_master_mode(unreal.MasterMode.NAV)
    run(ship, P["master_mode_switch_seconds"] + 0.1)
    run(ship, 1.0, lin=(1, 0, 0), afterburner=True)
    check("NAV: no afterburner (fuel untouched, limit unchanged)", not ship.is_afterburner_active() and ship.get_afterburner_fuel() == 1.0
          and abs(ship.get_speed_limit() - ship.get_mode_max_speed()) < 0.5)
finally:
    eas.destroy_actor(ship)

# Boost and afterburner together: boost suspends G-Safe, so the afterburner's full main thrust gets through.
ship = spawn()
try:
    v = run(ship, 0.5, lin=(1, 0, 0), boost=True, afterburner=True)
    main = P["thrust_acceleration"] * P["afterburner_thrust_multiplier"]
    check("Shift + Tab: full afterburner thrust (boost suspends G-Safe)", abs(v[0] / 0.5 - main) < 0.03 * main, "%.2f G" % (v[0] / 0.5 / G))
finally:
    eas.destroy_actor(ship)

# --- Assets --------------------------------------------------------------------------------------------
imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Spaceship")
pairs = set()
for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings"):
    a = m.get_editor_property("action")
    pairs.add((str(m.get_editor_property("key").get_editor_property("key_name")), a.get_name() if a else None))
check("Tab mapped to IA_Afterburner, Shift still boost", {("Tab", "IA_Afterburner"), ("LeftShift", "IA_Boost")} <= pairs)
action = unreal.EditorAssetLibrary.load_asset("/Game/Input/IA_Afterburner")
check("IA_Afterburner is a held bool", action is not None and len(action.get_editor_property("triggers")) == 0)
# Per-ship expectation: the ship's own boost / afterburner values (skipped while there is no modelled ship).
sut.check_setup_values(check, log, ("boost_", "afterburner_"), "boost / afterburner values")

# What the tuning actually buys, printed so the numbers are in the log next to the feel.
g = cdo.get_editor_property("g_safe_max_g") * G
log("INFO from SCM to the afterburner top speed: %.1f s with G-Safe (%.0f m/s2), %.1f s without (%.0f m/s2); tank lasts %.0f s" % (
    (AB_SPEED - SCM) / g, g, (AB_SPEED - SCM) / (P["thrust_acceleration"] * P["afterburner_thrust_multiplier"]),
    P["thrust_acceleration"] * P["afterburner_thrust_multiplier"], P["afterburner_duration_seconds"]))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
