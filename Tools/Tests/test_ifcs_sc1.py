"""Headless checks for SC-1a: the Star Citizen style IFCS core.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_ifcs_sc1.py

Drives temporary ships (native SpaceshipPawn defaults) frame by frame (1/60 s) in a new blank map
(deep space: no drag, no gravity) through SpaceshipPawn.debug_step_flight_input, which runs the same
code as Tick. Covers per-direction thruster limits, coupled braking, decoupled drift, the speed
limiter, spacebrake, SCM / NAV, rotational inertia, G-Safe, ComStab and the mouse virtual joystick.
Nothing is saved. Prints "IFCSTEST PASS" / "IFCSTEST FAIL" lines and a summary.
"""

import math

import unreal

STEP = 1.0 / 60.0
G = 980.665
failures = []


def log(msg):
    unreal.log("IFCSTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def length(a):
    return math.sqrt(sum(c * c for c in a))


def angle_deg(a, b):
    la, lb = length(a), length(b)
    if la < 1e-6 or lb < 1e-6:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(a[k] * b[k] for k in range(3)) / (la * lb)))))


def run(ship, seconds, lin=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), boost=False, each=None):
    """lin = (thrust, strafe, lift), rot = (roll, pitch, yaw), held for `seconds`."""
    velocity = None
    for i in range(int(round(seconds / STEP))):
        velocity = ship.debug_step_flight_input(STEP, unreal.Vector(*lin), unreal.Vector(*rot), boost)
        if each:
            each(i, velocity)
    return v3(velocity) if velocity else v3(ship.get_linear_velocity())


eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cdo = unreal.get_default_object(unreal.SpaceshipPawn)
P = {name: cdo.get_editor_property(name) for name in (
    "thrust_acceleration", "retro_acceleration", "strafe_acceleration", "lift_acceleration", "down_acceleration",
    "scm_max_speed", "nav_max_speed", "master_mode_switch_seconds", "nav_turn_scale", "nav_maneuver_scale",
    "speed_limiter_step", "speed_limiter_min", "g_safe_max_g", "g_safe_max_vertical_g", "g_safe_turn_g",
    "g_safe_min_turn_fraction", "pitch_rate", "yaw_rate", "pitch_acceleration", "yaw_acceleration",
    "v_joy_counts_to_full", "v_joy_deadzone")}
SCM = P["scm_max_speed"]
NAV = P["nav_max_speed"]
log("INFO main %.1f G, retro %.1f G, strafe %.1f G, up %.1f G, down %.1f G, SCM %.0f m/s, NAV %.0f m/s, G-Safe %.1f G" % (
    P["thrust_acceleration"] / G, P["retro_acceleration"] / G, P["strafe_acceleration"] / G, P["lift_acceleration"] / G,
    P["down_acceleration"] / G, SCM / 100, NAV / 100, P["g_safe_max_g"]))

unreal.EditorLoadingAndSavingUtils.new_blank_map(False)


def spawn(yaw=0.0):
    return eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))


# --- G-Safe on a thruster command (pure function) -----------------------------------------------
ship = spawn()
try:
    lim = P["g_safe_max_g"] * G
    vert = P["g_safe_max_vertical_g"] * G
    r = v3(ship.limit_thrust_for_pilot(unreal.Vector(10 * G, 0.0, 0.0), True))
    check("G-Safe caps forward thrust at GSafeMaxG", abs(r[0] - lim) < 1.0, "%.2f G" % (r[0] / G))
    r = v3(ship.limit_thrust_for_pilot(unreal.Vector(0.0, 0.0, -9 * G), False))
    check("G-Safe caps vertical thrust at GSafeMaxVerticalG", abs(r[2] + vert) < 1.0, "%.2f G" % (r[2] / G))
    r = v3(ship.limit_thrust_for_pilot(unreal.Vector(7 * G, 5 * G, 0.0), True))
    check("ComStab allocation keeps sideways thrust, forward gets the rest",
          abs(r[1] - 5 * G) < 1.0 and abs(length(r) - lim) < 1.0, "fwd %.2f G, side %.2f G" % (r[0] / G, r[1] / G))
    r = v3(ship.limit_thrust_for_pilot(unreal.Vector(7 * G, 5 * G, 0.0), False))
    check("without ComStab everything scales together", abs(length(r) - lim) < 1.0 and abs(r[0] / r[1] - 1.4) < 1e-3,
          "fwd %.2f G, side %.2f G" % (r[0] / G, r[1] / G))
    r = v3(ship.limit_thrust_for_pilot(unreal.Vector(2 * G, 1 * G, 1 * G), True))
    check("G-Safe leaves small commands alone", abs(r[0] - 2 * G) < 1e-3 and abs(r[1] - G) < 1e-3)
finally:
    eas.destroy_actor(ship)

# --- Coupled: W held accelerates at main thrust up to the limit, release brakes at retro ----------
ship = spawn()
try:
    check("defaults: coupled, SCM, G-Safe, ComStab, limiter 100 %",
          ship.is_flight_assist_on() and ship.get_master_mode() == unreal.MasterMode.SCM and ship.is_g_safe_on()
          and ship.is_com_stab_on() and abs(ship.get_speed_limiter() - 1.0) < 1e-6)
    ship.set_g_safe(False)
    v = run(ship, 0.5, lin=(1, 0, 0))
    check("G-Safe off: W accelerates at the main thrusters' limit", abs(v[0] / 0.5 - P["thrust_acceleration"]) < 0.03 * P["thrust_acceleration"],
          "%.2f G" % (v[0] / 0.5 / G))
    ship.set_g_safe(True)
    before = v[0]
    v = run(ship, 0.5, lin=(1, 0, 0))
    expected = min(P["thrust_acceleration"], P["g_safe_max_g"] * G)
    check("G-Safe on: forward acceleration capped", abs((v[0] - before) / 0.5 - expected) < 0.03 * expected,
          "%.2f G" % ((v[0] - before) / 0.5 / G))
    v = run(ship, 10.0, lin=(1, 0, 0))
    check("W settles at the SCM speed limit along the nose", abs(v[0] - SCM) < 0.01 * SCM and abs(v[1]) < 1.0 and abs(v[2]) < 1.0,
          "%.1f m/s" % (v[0] / 100))
    v1 = run(ship, 0.5)
    retro = min(P["retro_acceleration"], P["g_safe_max_g"] * G)
    check("releasing W brakes with the retro thrusters", abs((v[0] - v1[0]) / 0.5 - retro) < 0.03 * retro,
          "%.2f G" % ((v[0] - v1[0]) / 0.5 / G))
    v = run(ship, 10.0)
    check("coupled comes to a stop by itself", length(v) < 10.0, "%.2f cm/s" % length(v))

    v = run(ship, 0.5, lin=(0, 1, 0))
    strafe = min(P["strafe_acceleration"], P["g_safe_max_g"] * G)
    check("strafe accelerates at the strafe thrusters' limit", abs(v[1] / 0.5 - strafe) < 0.03 * strafe, "%.2f G" % (v[1] / 0.5 / G))
    run(ship, 3.0, lin=(0, 1, 0))
    v = run(ship, 10.0)
    check("released strafe drift is cancelled", length(v) < 10.0, "%.2f cm/s" % length(v))
    v = run(ship, 0.5, lin=(0, 0, -1))
    down = min(P["down_acceleration"], P["g_safe_max_vertical_g"] * G)
    check("down thrusters have their own limit", abs(-v[2] / 0.5 - down) < 0.03 * down, "%.2f G" % (-v[2] / 0.5 / G))
    run(ship, 10.0)
finally:
    eas.destroy_actor(ship)

# --- Speed limiter ---------------------------------------------------------------------------------
ship = spawn()
try:
    ship.set_speed_limiter(0.5)
    v = run(ship, 10.0, lin=(1, 0, 0))
    check("W stops at the limiter", abs(v[0] - 0.5 * SCM) < 0.01 * SCM, "%.1f m/s at 50 %%" % (v[0] / 100))
    ship.adjust_speed_limiter(2.0)
    check("wheel notch = SpeedLimiterStep", abs(ship.get_speed_limiter() - (0.5 + 2 * P["speed_limiter_step"])) < 1e-4,
          "%.3f" % ship.get_speed_limiter())
    ship.set_speed_limiter(0.3)
    v = run(ship, 10.0, lin=(1, 0, 0))
    check("lowering the limiter in flight brakes down to it", abs(v[0] - 0.3 * SCM) < 0.01 * SCM, "%.1f m/s" % (v[0] / 100))
    ship.set_speed_limiter(0.0)
    low = ship.get_speed_limiter()
    ship.adjust_speed_limiter(100.0)
    check("limiter clamped to SpeedLimiterMin..1", abs(low - P["speed_limiter_min"]) < 1e-5 and abs(ship.get_speed_limiter() - 1.0) < 1e-6,
          "%.3f .. %.3f" % (low, ship.get_speed_limiter()))
    ship.set_speed_limiter(0.5)
    v = run(ship, 10.0, lin=(1, 1, 0))
    check("diagonal flight also stays under the limit", length(v) < 0.5 * SCM * 1.005, "%.1f m/s" % (length(v) / 100))
finally:
    eas.destroy_actor(ship)

# --- Decoupled -------------------------------------------------------------------------------------
ship = spawn()
try:
    run(ship, 4.0, lin=(1, 0, 0))
    ship.set_flight_assist(False)
    before = run(ship, STEP)
    after = run(ship, 5.0)
    check("decoupled: no braking after release", abs(after[0] - before[0]) < 1.0 and after[0] > 10000.0,
          "%.1f -> %.1f m/s" % (before[0] / 100, after[0] / 100))
    heading0 = v3(ship.get_actor_forward_vector())
    after_turn = run(ship, 2.0, rot=(0, 0, 1))
    heading1 = v3(ship.get_actor_forward_vector())
    check("decoupled: turning keeps the flight path", angle_deg(heading0, heading1) > 30.0 and angle_deg(after, after_turn) < 0.1,
          "nose turned %.0f deg, velocity turned %.2f deg" % (angle_deg(heading0, heading1), angle_deg(after, after_turn)))
    ship.set_flight_assist(True)
    v = run(ship, 6.0)
    check("coupled again: the flight computer brings velocity back under control", length(v) < 50.0,
          "%.1f cm/s" % length(v))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    ship.set_flight_assist(False)
    ship.set_speed_limiter(0.5)
    v = run(ship, 10.0, lin=(1, 0, 0))
    check("decoupled thrust cannot push past the limiter", abs(length(v) - 0.5 * SCM) < 0.005 * SCM, "%.1f m/s" % (length(v) / 100))
    ship.set_space_brake(True)
    v1 = run(ship, 0.5)
    check("spacebrake brakes decoupled flight at the retro limit", abs((v[0] - v1[0]) / 0.5 - min(P["retro_acceleration"], P["g_safe_max_g"] * G)) < 0.05 * P["retro_acceleration"],
          "%.2f G" % ((v[0] - v1[0]) / 0.5 / G))
    v = run(ship, 8.0, lin=(1, 0, 0))
    check("spacebrake stops the ship even with W held", length(v) < 10.0 and ship.is_space_braking(), "%.2f cm/s" % length(v))
    ship.set_space_brake(False)
    v = run(ship, 2.0)
    check("after the spacebrake decoupled stays at rest", length(v) < 10.0)
finally:
    eas.destroy_actor(ship)

# --- Master modes ----------------------------------------------------------------------------------
ship = spawn()
try:
    switch = P["master_mode_switch_seconds"]
    ship.debug_step_flight(1.0 / 60.0, 0.0, 0.0, 0.0, False)
    check("no quantum drive in SCM", ship.get_quantum_state() == unreal.QuantumState.IDLE
          and ship.get_quantum_blocker() == unreal.QuantumBlocker.NEEDS_NAV)
    ship.toggle_master_mode()
    check("B starts switching to NAV", ship.is_master_mode_switching() and ship.get_pending_master_mode() == unreal.MasterMode.NAV
          and ship.get_master_mode() == unreal.MasterMode.SCM)
    run(ship, switch - 0.1)
    check("still SCM just before MasterModeSwitchSeconds", ship.get_master_mode() == unreal.MasterMode.SCM,
          "%.0f %%" % (100 * ship.get_master_mode_switch_progress()))
    run(ship, 0.2)
    check("NAV after MasterModeSwitchSeconds", ship.get_master_mode() == unreal.MasterMode.NAV and not ship.is_master_mode_switching())
    v = run(ship, 30.0, lin=(1, 0, 0))
    check("NAV flies up to NavMaxSpeed", abs(v[0] - NAV) < 0.01 * NAV, "%.0f m/s" % (v[0] / 100))
    ship.toggle_master_mode()
    ship.toggle_master_mode()
    check("B again cancels a switch", not ship.is_master_mode_switching() and ship.get_master_mode() == unreal.MasterMode.NAV)
    ship.request_master_mode(unreal.MasterMode.SCM)
    v = run(ship, switch - 0.05, lin=(1, 0, 0))
    check("NAV speed held until the switch completes", v[0] > 0.95 * NAV, "%.0f m/s" % (v[0] / 100))
    v = run(ship, 6.1, lin=(1, 0, 0))
    check("back in SCM the ship slows to the SCM limit", ship.get_master_mode() == unreal.MasterMode.SCM and length(v) < SCM * 1.01,
          "%.0f m/s" % (length(v) / 100))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    ship.request_master_mode(unreal.MasterMode.NAV)
    run(ship, P["master_mode_switch_seconds"] + 0.1)
    v = run(ship, 0.5, lin=(0, 1, 0))
    nav_strafe = min(P["strafe_acceleration"] * P["nav_maneuver_scale"], P["g_safe_max_g"] * G)
    check("NAV: manoeuvring thrust reduced", abs(v[1] / 0.5 - nav_strafe) < 0.03 * nav_strafe, "%.2f G" % (v[1] / 0.5 / G))
    run(ship, 10.0)
    run(ship, 3.0, rot=(0, 0, 1))
    rate = ship.get_editor_property("angular_velocity").z
    expected = P["yaw_rate"] * P["nav_turn_scale"]
    check("NAV: turn rates reduced", abs(rate - expected) < 0.02 * expected, "yaw %.1f deg/s, expected %.1f" % (rate, expected))
finally:
    eas.destroy_actor(ship)

# --- Rotation: inertia, G-Safe turn limit, ComStab ------------------------------------------------------
ship = spawn()
try:
    run(ship, 0.1, rot=(0, 1, 0))
    rate = ship.get_editor_property("angular_velocity").y
    check("pitch rate builds up no faster than PitchAcceleration", 0.0 < rate <= P["pitch_acceleration"] * 0.1 + 0.5,
          "%.1f deg/s after 0.1 s (max %.1f)" % (rate, P["pitch_acceleration"] * 0.1))
    run(ship, 2.0, rot=(0, 1, 0))
    rate = ship.get_editor_property("angular_velocity").y
    check("stationary: full pitch rate", abs(rate - P["pitch_rate"]) < 0.02 * P["pitch_rate"], "%.1f deg/s" % rate)
    run(ship, 0.1)
    rate2 = ship.get_editor_property("angular_velocity").y
    check("releasing the stick stops rotation with inertia too", rate - rate2 <= P["pitch_acceleration"] * 0.1 + 0.5 and rate2 > 0,
          "%.1f -> %.1f deg/s" % (rate, rate2))
finally:
    eas.destroy_actor(ship)


def fast_turn(gsafe, comstab, seconds=3.0):
    """At SCM top speed, W and full yaw held. Returns (settled yaw rate, max slip, max G)."""
    s = spawn()
    try:
        s.set_g_safe(gsafe)
        s.set_com_stab(comstab)
        run(s, 8.0, lin=(1, 0, 0))
        stats = {"slip": 0.0, "g": 0.0}

        def watch(i, v):
            stats["slip"] = max(stats["slip"], s.get_slip_angle_deg())
            if i > 30:
                stats["g"] = max(stats["g"], s.get_g_force())

        run(s, seconds, lin=(1, 0, 0), rot=(0, 0, 1), each=watch)
        return s.get_editor_property("angular_velocity").z, stats["slip"], stats["g"]
    finally:
        eas.destroy_actor(s)


rate_on, slip_gs, g_on = fast_turn(True, False)
rate_off, slip_free, g_off = fast_turn(False, False)
limit = max(math.degrees(P["g_safe_turn_g"] * G / SCM), P["yaw_rate"] * P["g_safe_min_turn_fraction"])
# A sliding ship flies a little faster than the limit along the nose, which lowers the limit a bit.
check("G-Safe: nose turns slower at SCM speed", abs(rate_on - min(limit, P["yaw_rate"])) < 0.06 * limit,
      "%.1f deg/s, limit %.1f" % (rate_on, limit))
check("G-Safe off: full yaw rate at speed", abs(rate_off - P["yaw_rate"]) < 0.03 * P["yaw_rate"], "%.1f deg/s" % rate_off)
check("G-Safe keeps the pilot under GSafeMaxG", g_on <= P["g_safe_max_g"] + 0.05, "max %.2f G (off: %.2f G)" % (g_on, g_off))
_, slip_comstab, _ = fast_turn(False, True)
check("ComStab: less slide in a hard turn", slip_comstab < 0.8 * slip_free, "max slip %.1f deg with, %.1f deg without" % (slip_comstab, slip_free))
log("INFO hard turn at SCM: G-Safe %.1f deg/s slip %.1f deg; free %.1f deg/s slip %.1f deg %.1f G; ComStab slip %.1f deg" % (
    rate_on, slip_gs, rate_off, slip_free, g_off, slip_comstab))

# --- Mouse virtual joystick ------------------------------------------------------------------------------
ship = spawn()
try:
    check("virtual joystick is the default", ship.uses_virtual_joystick())
    counts = P["v_joy_counts_to_full"]
    frames = [(counts * 0.1, 0.0, 0.0)] * 5 + [(0.0, 0.0, 0.0)] * 90
    out = ship.debug_simulate_free_look([unreal.Vector(*f) for f in frames])
    stick = ship.get_mouse_stick()
    check("cursor stays where the mouse left it", abs(stick.x - 0.5) < 1e-3 and abs(stick.y) < 1e-6, "(%.3f, %.3f)" % (stick.x, stick.y))
    yaws = [out[2 * i + 1].y for i in range(len(frames))]
    late = yaws[-1] - yaws[-31]
    check("ship keeps turning with the mouse still", late > 5.0, "%.1f deg in the last 0.5 s" % late)
    ship.debug_simulate_free_look([unreal.Vector(counts * 10, counts * 10, 0.0)])
    stick = ship.get_mouse_stick()
    check("cursor clamped to the circle", abs(math.hypot(stick.x, stick.y) - 1.0) < 1e-3, "|stick| %.3f" % math.hypot(stick.x, stick.y))
finally:
    eas.destroy_actor(ship)

ship = spawn()
try:
    counts = P["v_joy_counts_to_full"] * P["v_joy_deadzone"] * 0.8
    out = ship.debug_simulate_free_look([unreal.Vector(counts, 0.0, 0.0)] + [unreal.Vector(0.0, 0.0, 0.0)] * 60)
    rot = out[-1]
    check("inside the dead zone nothing turns", abs(rot.x) < 1e-4 and abs(rot.y) < 1e-4 and abs(rot.z) < 1e-4,
          "pitch %.5f yaw %.5f" % (rot.x, rot.y))
finally:
    eas.destroy_actor(ship)

# --- Assets -------------------------------------------------------------------------------------------------
imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Spaceship")
pairs = set()
for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings"):
    a = m.get_editor_property("action")
    pairs.add((str(m.get_editor_property("key").get_editor_property("key_name")), a.get_name() if a else None))
check("B / wheel / K / L mapped, zoom and spacebrake kept",
      {("B", "IA_MasterMode"), ("MouseWheelAxis", "IA_SpeedLimiter"), ("K", "IA_GSafe"), ("L", "IA_ComStab"),
       ("MouseWheelAxis", "IA_CameraZoom"), ("X", "IA_AllStop"), ("W", "IA_Thrust")} <= pairs, "%d mappings" % len(pairs))
all_stop = unreal.EditorAssetLibrary.load_asset("/Game/Input/IA_AllStop")
check("IA_AllStop has no Pressed trigger, so holding X is seen", len(all_stop.get_editor_property("triggers")) == 0)
vanguard = unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class("/Game/Ships/Vanguard/Blueprints/BP_Ship_Vanguard"))
check("Vanguard has its SC-1a thruster values",
      abs(vanguard.get_editor_property("retro_acceleration") - 4415.0) < 1 and abs(vanguard.get_editor_property("scm_max_speed") - 21000.0) < 1
      and abs(vanguard.get_editor_property("yaw_acceleration") - 180.0) < 1,
      "retro %.0f, SCM %.0f" % (vanguard.get_editor_property("retro_acceleration"), vanguard.get_editor_property("scm_max_speed")))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
