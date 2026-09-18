"""Headless checks for SC-2a: landing gear and precision mode.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_landing_sc2.py

Temporary ships (native SpaceshipPawn defaults) in a new blank map, driven frame by frame (1/60 s)
through the same code as Tick. The commandlet cannot sweep against the terrain, so the parts that
need the ground are tested through their pure functions (EvaluateTouchdown, the leg pose). Covers:
  1. the touchdown rule with the gear: GEAR UP first, the gap measured under the pads
  2. the gear state machine: timing, reversing halfway, precision following the gear, no raising while landed
  3. the gear's movement: the modelled part rises GearStowTravelCm into the hull; the placeholder legs
     (ships without a modelled gear) reach exactly GearExtensionCm down, fold flat stowed, smooth in between
  4. precision mode: top speed, the limiter inside it, SCM only, afterburner refused, gentler turning,
     speed bleeding down smoothly when it comes on at speed
  5. the HUD: GEAR and PREC lamps and their colours
  6. input assets (N, P, no clashes), Vanguard values from its setup JSON, its modelled gear part (split off
     in Blender) standing on the collision box's bottom and disappearing into the belly, the landing shot list
Nothing is saved. Prints "SC2TEST PASS" / "SC2TEST FAIL" lines and a summary.
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
    unreal.log("SC2TEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def length(a):
    return math.sqrt(sum(c * c for c in a))


def run(ship, seconds, lin=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), boost=False, each=None):
    """lin = (thrust, strafe, lift), rot = (roll, pitch, yaw), held for `seconds`."""
    for i in range(int(round(seconds / STEP))):
        velocity = ship.debug_step_flight_input(STEP, unreal.Vector(*lin), unreal.Vector(*rot), boost)
        if each:
            each(i, v3(velocity))
    return v3(ship.get_linear_velocity())


def lamp(hud, name):
    color = hud.debug_is_lamp_lit(name)
    return color is not None, color


def green(color):
    return color.r < 0.85 and color.g > 0.9 and color.b < 0.5


def amber(color):
    return color.r > 0.9 and 0.6 < color.g < 0.9 and color.b < 0.4


B = unreal.LandingBlocker
cdo = unreal.get_default_object(unreal.SpaceshipPawn)
P = {name: cdo.get_editor_property(name) for name in (
    "gear_extension_cm", "gear_deploy_seconds", "gear_fold_deg", "gear_pad_thickness_cm", "landing_max_gap_cm",
    "max_landing_slope_deg", "landing_max_speed", "scm_max_speed", "nav_max_speed", "precision_speed_fraction",
    "precision_turn_scale", "speed_limiter_step", "yaw_rate", "retro_acceleration", "g_safe_max_g", "overspeed_decay")}
EXT = P["gear_extension_cm"]
SCM = P["scm_max_speed"]
PREC = SCM * P["precision_speed_fraction"]
log("INFO gear %.0f cm in %.1f s, precision %.1f m/s (%.1f m/s a limiter notch), turning x%.2f" % (
    EXT, P["gear_deploy_seconds"], PREC / 100, PREC * P["speed_limiter_step"] / 100, P["precision_turn_scale"]))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)


def spawn():
    return eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))


# ---------------------------------------------------------------------------------------
# 1) Touchdown rule with the gear
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    gap_ok = EXT + 0.5 * P["landing_max_gap_cm"]
    check("gear up: GEAR UP whatever else holds", ship.evaluate_touchdown(gap_ok, 0.0, 0.0, 0.0, False, False) == B.GEAR_UP)
    check("gear up: GEAR UP even far above the ground (the warning covers the probe zone)",
          ship.evaluate_touchdown(-1.0, 0.0, 0.0, 0.0, False, False) == B.GEAR_UP)
    check("gear up on the belly: still GEAR UP", ship.evaluate_touchdown(0.0, 0.0, 0.0, 0.0, False, False) == B.GEAR_UP)
    check("gear down, pads within the touchdown gap: lands", ship.evaluate_touchdown(gap_ok, 0.0, 0.0, 0.0, False, True) == B.NONE)
    check("gear down, pads too high (gap measured under the pads, not the hull)",
          ship.evaluate_touchdown(EXT + P["landing_max_gap_cm"] + 5.0, 0.0, 0.0, 0.0, False, True) == B.TOO_HIGH)
    check("gear down, hull gap below the gear length (pads pressed in): lands",
          ship.evaluate_touchdown(0.3 * EXT, 0.0, 0.0, 0.0, False, True) == B.NONE)
    check("gear down, nothing below the probe: too high", ship.evaluate_touchdown(-1.0, 0.0, 0.0, 0.0, False, True) == B.TOO_HIGH)
    check("gear down keeps the other L5 rules (steep, fast, engines)",
          ship.evaluate_touchdown(gap_ok, 0.0, 0.0, P["max_landing_slope_deg"] + 3, False, True) == B.TOO_STEEP
          and ship.evaluate_touchdown(gap_ok, P["landing_max_speed"] + 10, 0.0, 0.0, False, True) == B.TOO_FAST
          and ship.evaluate_touchdown(gap_ok, 0.0, 0.0, 0.0, True, True) == B.ENGINE_INPUT)
    check("L5 rule unchanged for the old callers", ship.evaluate_landing(0.5 * P["landing_max_gap_cm"], 0.0, 0.0, 0.0, False) == B.NONE)

    # -----------------------------------------------------------------------------------
    # 2) Gear state machine
    # -----------------------------------------------------------------------------------
    S = unreal.GearState
    check("starts with the gear up, precision off",
          ship.get_gear_state() == S.RETRACTED and ship.get_gear_deploy() == 0.0 and not ship.is_precision_mode_on())
    ship.toggle_gear()
    check("N: extending, precision on at once", ship.get_gear_state() == S.EXTENDING and ship.is_precision_mode_on())
    half = P["gear_deploy_seconds"] * 0.5
    for _ in range(int(round(half / STEP))):
        ship.debug_step_gear(STEP)
    check("halfway after half the deploy time", abs(ship.get_gear_deploy() - 0.5) < 0.02 and ship.get_gear_state() == S.EXTENDING,
          "%.3f" % ship.get_gear_deploy())
    check("ground offset follows the deploy", abs(ship.get_gear_ground_offset_cm() - EXT * ship.get_gear_deploy()) < 1e-3)
    check("not deployed yet: touchdown would still say GEAR UP", not ship.is_gear_deployed())
    ship.toggle_gear()
    check("N halfway reverses from where it is", ship.get_gear_state() == S.RETRACTING and abs(ship.get_gear_deploy() - 0.5) < 0.02
          and not ship.is_precision_mode_on())
    for _ in range(int(round((half + 0.1) / STEP))):
        ship.debug_step_gear(STEP)
    check("back up in the same time it had come down", ship.get_gear_state() == S.RETRACTED and ship.get_gear_deploy() == 0.0)
    ship.set_gear_down(True)
    for _ in range(int(round((P["gear_deploy_seconds"] + 0.1) / STEP))):
        ship.debug_step_gear(STEP)
    check("down and locked after GearDeploySeconds", ship.get_gear_state() == S.DEPLOYED and ship.is_gear_deployed()
          and abs(ship.get_gear_ground_offset_cm() - EXT) < 1e-3)
    ship.debug_force_landed(True)
    refused = not ship.set_gear_down(False)
    check("landed: raising the gear is refused and says so", refused and ship.get_gear_state() == S.DEPLOYED
          and ship.get_gear_message_seconds() > 0.0)
    ship.debug_force_landed(False)
    check("after takeoff the gear goes up", ship.set_gear_down(False) and ship.get_gear_state() == S.RETRACTING)
    ship.debug_set_gear_instant(False)
    ship.toggle_precision_mode()
    check("P: precision by hand without the gear", ship.is_precision_mode_on() and ship.get_gear_state() == S.RETRACTED)
    ship.toggle_precision_mode()
    ship.debug_set_gear_instant(True)
    ship.toggle_precision_mode()
    check("P overrides the gear: gear down, precision off", not ship.is_precision_mode_on() and ship.is_gear_deployed())
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 3) Leg pose
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    def pose(d, nose):
        return [v3(v) for v in ship.compute_gear_leg_pose(d, nose)]

    def sole(p):
        return p[5][2] - 0.5 * p[6][2] * 100.0

    down = pose(1.0, False)
    check("down: leg straight, pad sole exactly GearExtensionCm below the socket",
          abs(down[0][0]) < 1e-3 and abs(sole(down) + EXT) < 0.5, "sole %.1f cm" % sole(down))
    check("down: pad thickness as set", abs(down[6][2] * 100.0 - P["gear_pad_thickness_cm"]) < 1e-3)
    check("down: sleeve reaches up into the hull (no gap at the root)", down[1][2] + 0.5 * down[2][2] * 100.0 > 20.0)
    up_nose, up_main = pose(0.0, True), pose(0.0, False)
    check("stowed: nose leg folds forward, main legs back, nearly flat",
          abs(up_nose[0][0] - P["gear_fold_deg"]) < 1e-3 and abs(up_main[0][0] + P["gear_fold_deg"]) < 1e-3)
    check("stowed: telescoped short", -sole(up_main) < 0.7 * EXT, "reach %.0f cm" % -sole(up_main))
    worst_angle, worst_reach, prev, pistons_ok, reaches = 0.0, 0.0, None, True, []
    for i in range(101):
        p = pose(i / 100.0, False)
        reaches.append(-sole(p))
        pistons_ok = pistons_ok and p[4][2] > 0.0
        if prev:
            worst_angle = max(worst_angle, abs(p[0][0] - prev[0][0]))
            worst_reach = max(worst_reach, abs(sole(p) - sole(prev)))
        prev = p
    check("smooth: no jump between 1 % steps", worst_angle < 4.0 and worst_reach < 3.0,
          "max %.2f deg, %.2f cm" % (worst_angle, worst_reach))
    check("reach never shrinks on the way down", all(b >= a - 1e-3 for a, b in zip(reaches, reaches[1:])))
    check("piston always has a length", pistons_ok)

    travel = ship.get_editor_property("gear_stow_travel_cm")
    offsets = [ship.compute_gear_stow_offset_cm(i / 100.0) for i in range(101)]
    check("modelled gear: stowed GearStowTravelCm up, down at 0, never moving back",
          abs(offsets[0] - travel) < 1e-3 and abs(offsets[-1]) < 1e-3 and all(b <= a + 1e-4 for a, b in zip(offsets, offsets[1:])))
    check("modelled gear: eased, no jump", max(abs(b - a) for a, b in zip(offsets, offsets[1:])) < 0.02 * travel)
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 4) Precision mode in flight (deep space: no drag, no gravity)
# ---------------------------------------------------------------------------------------
ship = spawn()
try:
    ship.set_precision_mode(True)
    check("precision: top speed SCM x fraction", abs(ship.get_mode_max_speed() - PREC) < 1e-2, "%.1f m/s" % (ship.get_mode_max_speed() / 100))
    ship.set_speed_limiter(0.5)
    check("limiter still works inside precision", abs(ship.get_speed_limit() - 0.5 * PREC) < 1e-2)
    ship.adjust_speed_limiter(1.0)
    check("one notch = SpeedLimiterStep of the precision speed", abs(ship.get_speed_limit() - 0.55 * PREC) < 1e-2,
          "%.2f m/s a notch" % (PREC * P["speed_limiter_step"] / 100))
    ship.set_speed_limiter(1.0)
    v = run(ship, 8.0, lin=(1, 0, 0))
    check("W settles at the precision speed", abs(v[0] - PREC) < 0.01 * PREC, "%.1f m/s" % (v[0] / 100))
    ship.set_afterburner_held(True)
    peak = [0.0]
    run(ship, 1.5, lin=(1, 0, 0), each=lambda i, vel: peak.__setitem__(0, max(peak[0], length(vel))))
    ship.set_afterburner_held(False)
    check("afterburner refused in precision", not ship.is_afterburner_active() and peak[0] < PREC * 1.01, "peak %.1f m/s" % (peak[0] / 100))
    ship.request_master_mode(unreal.MasterMode.NAV)
    ship.debug_finish_master_mode_switch()
    check("NAV: precision stays switched on but not in effect", ship.is_precision_mode_on() and not ship.is_precision_active()
          and abs(ship.get_mode_max_speed() - P["nav_max_speed"]) < 1e-2)
    ship.request_master_mode(unreal.MasterMode.SCM)
    ship.debug_finish_master_mode_switch()
    check("back in SCM: precision in effect again", ship.is_precision_active())
finally:
    eas.destroy_actor(ship)

# Coming on at full SCM speed: no snap, bleeds down to the precision speed.
ship = spawn()
try:
    run(ship, 10.0, lin=(1, 0, 0))
    before = length(v3(ship.get_linear_velocity()))
    ship.set_precision_mode(True)
    first = length(run(ship, STEP))
    worst = [(before - first) / STEP]
    last = [first]

    def watch(i, vel):
        s = length(vel)
        worst[0] = max(worst[0], (last[0] - s) / STEP)
        last[0] = s
    run(ship, 6.0, each=watch)
    decel_cap = max(P["retro_acceleration"], P["g_safe_max_g"] * G) * 1.05
    check("precision at SCM speed: slows down without a snap", worst[0] < decel_cap, "max %.1f G" % (worst[0] / G))
    check("...and is down to the precision speed within 6 s", last[0] < PREC * 1.02, "%.1f m/s" % (last[0] / 100))
finally:
    eas.destroy_actor(ship)

# Gentler turning.
def yaw_turned(precision):
    s = spawn()
    try:
        s.set_precision_mode(precision)
        run(s, 1.0, rot=(0, 0, 1))
        start = s.get_actor_rotation().yaw
        run(s, 0.5, rot=(0, 0, 1))
        return abs(unreal.MathLibrary.normalize_axis(s.get_actor_rotation().yaw - start)) / 0.5
    finally:
        eas.destroy_actor(s)


normal_rate, precise_rate = yaw_turned(False), yaw_turned(True)
check("precision turns at PrecisionTurnScale of the normal rate",
      abs(precise_rate / normal_rate - P["precision_turn_scale"]) < 0.05,
      "%.1f vs %.1f deg/s" % (precise_rate, normal_rate))

# ---------------------------------------------------------------------------------------
# 5) HUD lamps
# ---------------------------------------------------------------------------------------
hud = unreal.new_object(unreal.SpaceFlightHud)
hud.debug_initialize()
names = set(hud.debug_get_widget_names())
check("HUD has GEAR and PREC lamps", {"Lamp_GEAR", "Lamp_PREC"} <= names)
ship = spawn()
try:
    state = unreal.SpaceFlightHud.make_state(ship, 1)
    hud.apply_state(state)
    check("gear up, precision off: both lamps dark", not lamp(hud, "GEAR")[0] and not lamp(hud, "PREC")[0]
          and not state.gear_down and not state.precision_on)
    ship.debug_set_gear_instant(True)
    state = unreal.SpaceFlightHud.make_state(ship, 1)
    hud.apply_state(state)
    lit_gear, gear_color = lamp(hud, "GEAR")
    lit_prec, prec_color = lamp(hud, "PREC")
    check("gear down: GEAR green, PREC green", state.gear_down and lit_gear and green(gear_color) and lit_prec and green(prec_color))
    ship.request_master_mode(unreal.MasterMode.NAV)
    ship.debug_finish_master_mode_switch()
    state = unreal.SpaceFlightHud.make_state(ship, 1)
    hud.apply_state(state)
    lit_prec, prec_color = lamp(hud, "PREC")
    check("NAV: PREC amber (on, not in effect)", state.precision_on and not state.precision_active and lit_prec and amber(prec_color))
    ship.debug_set_gear_instant(False)
    ship.request_master_mode(unreal.MasterMode.SCM)
    ship.debug_finish_master_mode_switch()
    ship.set_gear_down(True)
    state = unreal.SpaceFlightHud.make_state(ship, 1)
    check("gear on its way: HUD state says moving", state.gear_moving and not state.gear_down)
    ship.set_precision_mode(True)
    ship.set_speed_limiter(1.0)
    state = unreal.SpaceFlightHud.make_state(ship, 1)
    check("precision: the speed gauge's full scale is the precision speed", abs(state.gauge_scale_cm_s - PREC) < 1.0,
          "%.1f m/s" % (state.gauge_scale_cm_s / 100))
finally:
    eas.destroy_actor(ship)

# ---------------------------------------------------------------------------------------
# 6) Assets, Vanguard, shot list
# ---------------------------------------------------------------------------------------
imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Spaceship")
by_key = {}
for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings"):
    a = m.get_editor_property("action")
    by_key.setdefault(str(m.get_editor_property("key").get_editor_property("key_name")), set()).add(a.get_name() if a else None)
check("N mapped to IA_LandingGear only", by_key.get("N") == {"IA_LandingGear"}, str(by_key.get("N")))
check("P mapped to IA_Precision only", by_key.get("P") == {"IA_Precision"}, str(by_key.get("P")))
for path in ("/Game/Input/IA_LandingGear", "/Game/Input/IA_Precision"):
    action = unreal.EditorAssetLibrary.load_asset(path)
    check(path.split("/")[-1] + " is a bool action", action is not None and action.get_editor_property("value_type") == unreal.InputActionValueType.BOOLEAN)

setup = json.load(open(os.path.join(REPO, "ArtSource", "Ships", "Vanguard", "Vanguard_setup.json"), encoding="utf-8"))["pawn"]
vanguard = unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class("/Game/Ships/Vanguard/Blueprints/BP_Ship_Vanguard"))
keys = [k for k in setup if k.startswith("gear_") or k.startswith("precision_")]
check("Vanguard gear / precision values from its setup JSON (%d)" % len(keys),
      len(keys) >= 5 and all(abs(vanguard.get_editor_property(k) - setup[k]) < 1e-4 for k in keys))
mesh = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Vanguard/Meshes/SM_Ship_Vanguard")
manifest = json.load(open(os.path.join(REPO, "ArtSource", "Ships", "Vanguard", "Export", "Vanguard_manifest.json"), encoding="utf-8"))
box_bottom = -manifest["suggested_pawn_settings"]["HullCollision_BoxExtent_cm"][2]
sockets = []
for name in vanguard.get_editor_property("gear_socket_names"):
    # The FBX import drops the SOCKET_ prefix; the ship accepts either spelling.
    socket = mesh.find_socket(str(name)) or mesh.find_socket(str(name).replace("SOCKET_", ""))
    if socket:
        sockets.append((str(name), socket.get_editor_property("relative_location").z))
check("the Vanguard mesh has all three gear sockets", len(sockets) == 3, str(sockets))
check("gear sockets (the pads' soles) sit on the hull box's bottom",
      all(abs(z - box_bottom) < 2.0 for _, z in sockets), "box bottom %.1f, sockets %s" % (box_bottom, [round(z, 1) for _, z in sockets]))

# The modelled legs are their own part now, inside the collision box: nothing hangs below it.
parts = manifest["meshes"]
gear_part = parts.get("SM_Ship_Vanguard_Gear")
hull_part = parts.get("SM_Ship_Vanguard")
check("Vanguard: the legs are a separate part (SM_Ship_Vanguard_Gear), no longer in the hull mesh",
      gear_part is not None and gear_part["part"] == "Gear" and hull_part["bounds_m"][0][2] > -1.6,
      "hull bottom %.2f m" % hull_part["bounds_m"][0][2])
gear_bottom_cm = gear_part["bounds_m"][0][2] * 100.0 if gear_part else 0.0
check("Vanguard: pads reach the box bottom, so gear_extension_cm is 0",
      abs(gear_bottom_cm - box_bottom) < 2.0 and vanguard.get_editor_property("gear_extension_cm") == 0.0,
      "pads %.1f cm" % gear_bottom_cm)
travel = vanguard.get_editor_property("gear_stow_travel_cm")
check("Vanguard: stowed, the pads rise above the hull's lowest point (hidden in the belly)",
      gear_bottom_cm + travel > hull_part["bounds_m"][0][2] * 100.0,
      "stowed soles %.0f cm, hull bottom %.0f cm" % (gear_bottom_cm + travel, hull_part["bounds_m"][0][2] * 100.0))
bp_ship = eas.spawn_actor_from_class(unreal.EditorAssetLibrary.load_blueprint_class("/Game/Ships/Vanguard/Blueprints/BP_Ship_Vanguard"),
                                     unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
try:
    gear_meshes = [c for c in bp_ship.get_components_by_class(unreal.StaticMeshComponent)
                   if "Gear" in c.get_name() and c.get_editor_property("static_mesh")
                   and c.get_editor_property("static_mesh").get_name() == "SM_Ship_Vanguard_Gear"]
    check("BP_Ship_Vanguard has the Gear component with the gear mesh", len(gear_meshes) == 1,
          ", ".join(c.get_name() for c in bp_ship.get_components_by_class(unreal.StaticMeshComponent)))
finally:
    eas.destroy_actor(bp_ship)

shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "landing.json"), encoding="utf-8"))["shots"]
known = {"name", "camera", "hud", "altitude_m", "facing", "speed_ms", "mode", "limiter", "coupled", "gsafe", "comstab",
         "boost", "afterburner", "stick", "settle", "cockpit_eye", "hide_hull", "hide_canopy", "gear", "lower_gear",
         "precision", "chase_yaw", "chase_pitch", "chase_zoom", "_comment"}
unknown = sorted({k for s in shots for k in s} - known)
check("landing shot list uses only fields the runner reads", not unknown and len(shots) >= 5, str(unknown))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
