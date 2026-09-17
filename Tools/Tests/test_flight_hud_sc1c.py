"""Headless checks for SC-1c: the UMG flight HUD (USpaceFlightHud).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_flight_hud_sc1c.py

Nothing is drawn in a commandlet, so this checks what can be checked without a screen:
- the widget tree builds (lamps, speed gauge, G meter, boost and afterburner gauges, virtual joystick);
- USpaceFlightHud.make_state reads the right ship values (speed vs limiter, lamps, G, fuel, stick);
- apply_state puts them into the widgets (gauge values and markers, lamp on/off and colour, texts).
Ships are temporary SpaceshipPawns in a new blank map, driven by debug_step_flight_input. Nothing
is saved. Prints "HUDTEST PASS" / "HUDTEST FAIL" lines and a summary. How it looks: the scenario
in Docs/HANDOFF.md / the step's report.
"""

import unreal

STEP = 1.0 / 60.0
failures = []


def log(msg):
    unreal.log("HUDTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def run(ship, seconds, lin=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0), boost=False, afterburner=False):
    ship.set_afterburner_held(afterburner)
    for _ in range(int(round(seconds / STEP))):
        ship.debug_step_flight_input(STEP, unreal.Vector(*lin), unreal.Vector(*rot), boost)
    ship.set_afterburner_held(False)


def lamp(hud, name):
    # Unreal Python returns only the out colour for a bool function, and None when it returns false.
    color = hud.debug_is_lamp_lit(name)
    return color is not None, color


def amber(color):
    return color.r > 0.9 and 0.5 < color.g < 0.85 and color.b < 0.4


def cyan(color):
    return color.r < 0.6 and color.g > 0.8 and color.b > 0.9


def show(hud, ship, mode=1):
    state = unreal.SpaceFlightHud.make_state(ship, mode)
    hud.apply_state(state)
    return state


cdo = unreal.get_default_object(unreal.SpaceshipPawn)
SCM = cdo.get_editor_property("scm_max_speed")
AB = cdo.get_editor_property("afterburner_speed_multiplier")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)

# --- Widget tree ------------------------------------------------------------------------------------
hud = unreal.new_object(unreal.SpaceFlightHud)
hud.debug_initialize()
names = set(hud.debug_get_widget_names())
expected = {"Root", "LeftCluster", "RightCluster", "SpeedGauge", "GGauge", "BoostGauge", "AfterburnerGauge", "VirtualJoystick",
            "Lamp_MODE", "Lamp_CPLD", "Lamp_GSAF", "Lamp_CSTB", "Lamp_BOOST", "SpeedText", "LimitText", "GText", "BoostText",
            "AfterburnerText", "FrameLeft", "FrameRight"}
check("widget tree has every SC-1c element", expected <= names, "missing %s" % sorted(expected - names))
check("gauges and virtual joystick are the custom widgets",
      isinstance(hud.debug_get_gauge("SpeedGauge"), unreal.SpaceHudGauge) and isinstance(hud.debug_get_virtual_joystick(), unreal.SpaceHudVirtualJoystick))
check("G meter is horizontal, the others vertical", hud.debug_get_gauge("GGauge").get_editor_property("horizontal")
      and not hud.debug_get_gauge("SpeedGauge").get_editor_property("horizontal"))

# --- Look: panels with cut corners, monospace type, animated lamps ---------------------------------
panels = {"LampPanel", "SpeedPanel", "PowerPanel", "FrameLeft", "FrameRight"}
check("clusters sit on cut-corner panels", panels <= names, "missing %s" % sorted(panels - names))
lamp_widget = hud.debug_get_lamp("CPLD")
check("lamps are the painted widget with an animated intensity", isinstance(lamp_widget, unreal.SpaceHudLamp))
# Typography after the reference: a thin face for the big numbers, small wide-spaced caps for the
# labels, and an outline so both stay readable over a bright sky.
speed_font = hud.debug_get_text_widget("SpeedText").get_editor_property("font")
label_font = hud.debug_get_text_widget("LampLabel_CPLD").get_editor_property("font")
check("speed number in the thin face, outlined",
      "Light" in str(speed_font.get_editor_property("typeface_font_name"))
      and speed_font.get_editor_property("outline_settings").get_editor_property("outline_size") >= 1,
      "%s" % speed_font.get_editor_property("typeface_font_name"))
check("labels in small wide-spaced caps", "Bold" in str(label_font.get_editor_property("typeface_font_name"))
      and label_font.get_editor_property("letter_spacing") >= 150 and label_font.get_editor_property("size") <= 10,
      "%s, spacing %d, size %d" % (label_font.get_editor_property("typeface_font_name"),
                                   label_font.get_editor_property("letter_spacing"), label_font.get_editor_property("size")))

state = unreal.SpaceFlightHud.make_state(None, 1)
check("no ship: HUD hidden", not state.visible)

ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
try:
    run(ship, STEP)
    state = show(hud, ship, 0)
    check("H hidden (space.Hud 0): HUD hidden", not state.visible)

    # --- Defaults: SCM, coupled, G-Safe, ComStab on; boost off ---------------------------------
    state = show(hud, ship)
    check("ship flown: HUD visible", state.visible)
    for name, want in (("MODE", True), ("CPLD", True), ("GSAF", True), ("CSTB", True), ("BOOST", False)):
        lit, color = lamp(hud, name)
        check("default lamp %s %s" % (name, "lit" if want else "dark"), lit == want and (not want or cyan(color)), str(color))
    check("mode label SCM", hud.debug_get_text("LampLabel_MODE") == "SCM")

    # --- Speed gauge against the limiter -----------------------------------------------------------
    run(ship, 10.0, lin=(1, 0, 0))
    state = show(hud, ship)
    gauge = hud.debug_get_gauge("SpeedGauge")
    check("full speed: gauge full, limiter mark at the top", abs(gauge.get_editor_property("value") - 1.0) < 0.01
          and abs(gauge.get_editor_property("marker") - 1.0) < 1e-4, "value %.3f marker %.3f" % (gauge.get_editor_property("value"), gauge.get_editor_property("marker")))
    check("speed number under the gauge", hud.debug_get_text("SpeedText") == "200 M/S", hud.debug_get_text("SpeedText"))
    ship.set_speed_limiter(0.5)
    run(ship, 10.0, lin=(1, 0, 0))
    state = show(hud, ship)
    check("limiter 50 %: fill and mark at half", abs(gauge.get_editor_property("value") - 0.5) < 0.01
          and abs(gauge.get_editor_property("marker") - 0.5) < 1e-4, "value %.3f marker %.3f" % (gauge.get_editor_property("value"), gauge.get_editor_property("marker")))
    check("limit text shows the limit and the limiter", hud.debug_get_text("LimitText") == "LIM 100 M/S   50%", repr(hud.debug_get_text("LimitText")))
    ship.set_speed_limiter(0.25)
    run(ship, 0.2, lin=(1, 0, 0))
    state = show(hud, ship)
    check("faster than a lowered limiter: over limit, amber fill", state.over_limit and amber(gauge.get_editor_property("fill_color")))
    ship.set_speed_limiter(1.0)
    run(ship, 12.0)
    run(ship, 3.0, lin=(-1, 0, 0))
    state = show(hud, ship)
    check("flying backwards fills the red reverse zone", state.forward_speed_cm_s < 0 and gauge.get_editor_property("reverse_value") > 0.5
          and gauge.get_editor_property("value") == 0.0, "reverse %.2f" % gauge.get_editor_property("reverse_value"))
    run(ship, 10.0)

    # --- Lamps follow the switches ------------------------------------------------------------------
    ship.set_flight_assist(False)
    show(hud, ship)
    check("decoupled: CPLD dark", not lamp(hud, "CPLD")[0])
    ship.set_space_brake(True)
    show(hud, ship)
    check("spacebrake: CPLD lamp reads BRAKE and is lit", lamp(hud, "CPLD")[0] and hud.debug_get_text("LampLabel_CPLD") == "BRAKE")
    ship.set_space_brake(False)
    ship.set_flight_assist(True)
    ship.set_com_stab(False)
    show(hud, ship)
    check("ComStab off: CSTB dark", not lamp(hud, "CSTB")[0])
    ship.set_com_stab(True)
    # The lamp fades and flashes instead of snapping (SC-1c polish). It has to be lit first: the
    # widgets only animate while the HUD ticks (debug_advance stands in for that headless).
    show(hud, ship)
    hud.debug_advance(1.0)
    gsaf = hud.debug_get_lamp("GSAF")
    check("a lit lamp reaches full brightness", gsaf.get_editor_property("intensity") > 0.99)
    ship.set_g_safe(False)
    show(hud, ship)
    before = gsaf.get_editor_property("intensity")
    hud.debug_advance(0.03)
    mid = gsaf.get_editor_property("intensity")
    check("switching a lamp fades it, not blinks", gsaf.get_editor_property("flash") > 0.5 and before > mid > 0.05,
          "%.2f -> %.2f" % (before, mid))
    hud.debug_advance(1.0)
    check("the fade settles where the state says", gsaf.get_editor_property("intensity") < 0.01 and gsaf.get_editor_property("flash") < 0.01)
    check("G-Safe off: GSAF dark, no G-Safe mark on the G meter", not lamp(hud, "GSAF")[0]
          and hud.debug_get_gauge("GGauge").get_editor_property("marker") < 0)
    ship.set_g_safe(True)
    show(hud, ship)
    hud.debug_advance(1.0)
    check("a lamp switched back on is fully lit again", hud.debug_get_lamp("GSAF").get_editor_property("intensity") > 0.99)
    run(ship, 0.5, lin=(0, 1, 0), boost=True)
    state = show(hud, ship)
    lit_gsaf, color_gsaf = lamp(hud, "GSAF")
    lit_boost, color_boost = lamp(hud, "BOOST")
    check("boost: BOOST lit amber, GSAF amber (suspended)", lit_boost and amber(color_boost) and lit_gsaf and amber(color_gsaf),
          "boost %s gsaf %s" % (color_boost, color_gsaf))
    check("G meter follows the ship", abs(state.g_force - ship.get_g_force()) < 1e-4 and hud.debug_get_text("GText") == "%.1f G" % ship.get_g_force(),
          hud.debug_get_text("GText"))
    boost_gauge = hud.debug_get_gauge("BoostGauge")
    check("boost gauge shows the energy", abs(boost_gauge.get_editor_property("value") - ship.get_boost_energy()) < 1e-4
          and ship.get_boost_energy() < 1.0 and amber(boost_gauge.get_editor_property("fill_color")))
    run(ship, 8.0)
finally:
    eas.destroy_actor(ship)

# --- Afterburner ---------------------------------------------------------------------------------------
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
try:
    run(ship, 3.0, lin=(1, 0, 0), afterburner=True)
    state = show(hud, ship)
    gauge = hud.debug_get_gauge("SpeedGauge")
    ab = hud.debug_get_gauge("AfterburnerGauge")
    check("afterburner: text BURN, gauge shows fuel", hud.debug_get_text("AfterburnerText").endswith("BURN")
          and abs(ab.get_editor_property("value") - ship.get_afterburner_fuel()) < 1e-4 and ship.get_afterburner_fuel() < 1.0,
          hud.debug_get_text("AfterburnerText"))
    check("afterburner: speed gauge rescales to the raised top speed, limiter mark stays at 100 %",
          abs(state.gauge_scale_cm_s - SCM * AB) < 1.0 and abs(gauge.get_editor_property("marker") - 1.0) < 1e-4 and amber(gauge.get_editor_property("fill_color")),
          "scale %.0f m/s" % (state.gauge_scale_cm_s / 100))
    ship.set_afterburner_held(True)
    for _ in range(2000):
        if ship.is_afterburner_locked():
            break
        ship.debug_step_flight_input(STEP, unreal.Vector(1, 0, 0), unreal.Vector(0, 0, 0), False)
    ship.set_afterburner_held(False)
    show(hud, ship)
    check("empty tank: EMPTY", hud.debug_get_text("AfterburnerText").endswith("EMPTY"), hud.debug_get_text("AfterburnerText"))
    ship.toggle_master_mode()
    run(ship, 0.5)
    show(hud, ship)
    check("switching to NAV: mode label already NAV", hud.debug_get_text("LampLabel_MODE") == "NAV")
    run(ship, 2.0)
    show(hud, ship)
    check("NAV: afterburner gauge dimmed, SCM ONLY", ab.get_editor_property("dim") and hud.debug_get_text("AfterburnerText").endswith("SCM ONLY"),
          hud.debug_get_text("AfterburnerText"))
finally:
    eas.destroy_actor(ship)

# --- Virtual joystick ---------------------------------------------------------------------------------------
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
try:
    counts = cdo.get_editor_property("v_joy_counts_to_full")
    ship.debug_simulate_free_look([unreal.Vector(counts * 0.3, counts * 0.2, 0.0)])
    state = show(hud, ship)
    joystick = hud.debug_get_virtual_joystick()
    stick = joystick.get_editor_property("stick")
    check("virtual joystick shown in flight with the ship's cursor", state.show_virtual_joystick and abs(stick.x - 0.3) < 1e-3 and abs(stick.y - 0.2) < 1e-3
          and abs(joystick.get_editor_property("deadzone") - cdo.get_editor_property("v_joy_deadzone")) < 1e-5, "(%.3f, %.3f)" % (stick.x, stick.y))
    ship.debug_simulate_free_look([unreal.Vector(0.0, 0.0, 1.0)])
    state = show(hud, ship)
    check("virtual joystick hidden while free looking", not state.show_virtual_joystick)
finally:
    eas.destroy_actor(ship)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
