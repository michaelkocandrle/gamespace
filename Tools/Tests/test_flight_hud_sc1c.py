"""Headless checks for the UMG flight HUD (USpaceFlightHud): SC-1c's logic in the layout of the current
Star Citizen HUD (Docs/UI/Screenshot 2026-09-17 201854.png).

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


# The palette after the current SC HUD: instruments ice-cyan, cautions amber, the rest near-white.
def amber(color):
    return color.r > 0.9 and 0.6 < color.g < 0.9 and color.b < 0.4


def instrument(color):
    return color.r < 0.8 and color.g > 0.8 and color.b > 0.95


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
# Every element of the reference that this game has a system for (fuel, countermeasures and weapons it has not).
expected = {"Root", "Ladder", "HeadingTape", "Reticle", "VirtualJoystick",
            "ModeIcon", "ModeText", "SubModeText", "Lamp_CSTB", "Lamp_CPLD", "Lamp_PREC", "Lamp_BOOST", "Strafe", "LimiterPlus",
            "SpeedGauge", "SpeedValue", "SpeedUnit", "RowBoostValue", "RowBoostLabel", "RowLimitValue", "RowLimitLabel",
            "AfterburnerGauge", "AbRing", "AfterburnerValue", "AfterburnerLabel", "AltitudeUnit", "AltitudeTape",
            "Gyro", "Shield", "GValue", "GUnit", "GMax", "RowGearValue", "RowQuantumValue", "RowRAltValue", "RowVsiValue", "RowAtmoValue"}
check("widget tree has every element of the SC reference", expected <= names, "missing %s" % sorted(expected - names))
check("gauges, symbols, tapes and the ladder are the custom widgets",
      isinstance(hud.debug_get_gauge("SpeedGauge"), unreal.SpaceHudGauge) and isinstance(hud.debug_get_virtual_joystick(), unreal.SpaceHudVirtualJoystick)
      and isinstance(hud.debug_get_part("Strafe"), unreal.SpaceHudSymbol) and isinstance(hud.debug_get_part("AltitudeTape"), unreal.SpaceHudTape)
      and isinstance(hud.debug_get_part("Ladder"), unreal.SpaceHudLadder))
heading = hud.debug_get_part("HeadingTape")
check("heading tape horizontal and wrapping (359 -> 0), altitude tape vertical",
      heading.get_editor_property("wrap360") and not heading.get_editor_property("vertical") and heading.format(360.0) == "0" and heading.format(-5.0) == "355"
      and hud.debug_get_part("AltitudeTape").get_editor_property("vertical"), "%s %s" % (heading.format(360.0), heading.format(-5.0)))
check("afterburner tube has the red reserve at its root", abs(hud.debug_get_gauge("AfterburnerGauge").get_editor_property("reserve_zone") - 0.25) < 1e-4)
# The ladder sits on the real 5-degree lines: 1920 px wide, 90 degrees -> focal 960 px.
line = unreal.SpaceHudLadder.line_centre(5.0, 0.0, 0.0, 90.0, 1920.0)
rolled = unreal.SpaceHudLadder.line_centre(5.0, 0.0, 90.0, 90.0, 1920.0)
check("ladder: the 5 degree line 84 px above the middle, rolled right it swings left",
      abs(line.x) < 0.01 and abs(line.y + 83.99) < 0.1 and rolled.x < -83.0 and abs(rolled.y) < 0.1, "%s %s" % (line, rolled))

# --- Look: panels with cut corners, monospace type, animated lamps ---------------------------------
brackets = {"BracketMode", "BracketRows", "BracketStatus", "BracketAir", "GSeparator"}
check("text blocks framed by thin brackets, not panels", brackets <= names and not ({"LampPanel", "SpeedPanel"} & names), "missing %s" % sorted(brackets - names))
lamp_widget = hud.debug_get_lamp("CPLD")
check("lamps are the painted widget with an animated intensity", isinstance(lamp_widget, unreal.SpaceHudLamp))
# Typography after the reference: a thin face for the big numbers, small wide-spaced caps for the
# labels, and an outline so both stay readable over a bright sky.
speed_font = hud.debug_get_text_widget("SpeedValue").get_editor_property("font")
label_font = hud.debug_get_text_widget("LampLabel_CPLD").get_editor_property("font")
check("speed number is outlined so it reads over a bright sky",
      speed_font.get_editor_property("outline_settings").get_editor_property("outline_size") >= 1)
# Labels use the engine's condensed Roboto, which Slate's typefaces do not expose, so the HUD loads
# the .ttf by path: a path font has no typeface name, while the fallback (Bold) would have one.
# A face loaded from a file has neither a font object nor a typeface name; the engine fallbacks
# (Roboto Bold / DroidSansMono) would have both, so this proves the project fonts are the ones in use.
check("numbers use the project's face, not an engine fallback",
      speed_font.get_editor_property("font_object") is None and str(speed_font.get_editor_property("typeface_font_name")) in ("", "None"))
check("labels use the project's Rajdhani", label_font.get_editor_property("font_object") is None)
check("labels in the condensed face, small and spaced (the reference: ~11 px at 1080p)", str(label_font.get_editor_property("typeface_font_name")) in ("", "None")
      and label_font.get_editor_property("letter_spacing") >= 40 and label_font.get_editor_property("size") <= 12,
      "typeface %r, spacing %d, size %d" % (str(label_font.get_editor_property("typeface_font_name")),
                                            label_font.get_editor_property("letter_spacing"), label_font.get_editor_property("size")))
check("the big readouts (speed, AB, G) at the reference's ~22 px", speed_font.get_editor_property("size") == 22,
      "%d" % speed_font.get_editor_property("size"))

# The bar springs after the value instead of snapping to it, and the halo breathes.
gauge = hud.debug_get_gauge("SpeedGauge")
hud.debug_advance(2.0)
settled = gauge.get_editor_property("display")
pulse_a = gauge.get_editor_property("pulse")
hud.debug_advance(0.9)
check("the halo breathes", abs(pulse_a - gauge.get_editor_property("pulse")) > 0.02 and 0.85 < gauge.get_editor_property("pulse") < 1.15,
      "%.3f -> %.3f" % (pulse_a, gauge.get_editor_property("pulse")))

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
        check("default lamp %s %s" % (name, "lit" if want else "dark"), lit == want and (not want or instrument(color)), str(color))
    check("mode SCM over the sub-mode FLIGHT", hud.debug_get_text("ModeText") == "SCM" and hud.debug_get_text("SubModeText") == "FLIGHT")
    check("switch badges shown only while on (CSTB, CPLD on; PREC, BOOST off)",
          hud.debug_is_shown("Badge_CSTB") and hud.debug_is_shown("Badge_CPLD") and not hud.debug_is_shown("Badge_PREC") and not hud.debug_is_shown("Badge_BOOST"))
    check("no body nearby: heading, ladder and altitude tape hidden, air rows blank",
          not state.has_environment and not hud.debug_is_shown("HeadingTape") and not hud.debug_is_shown("Ladder")
          and not hud.debug_is_shown("AltitudeTape") and hud.debug_get_text("RowRAltValue") == "-")
    check("status rows: GEAR UP, QT OFF", hud.debug_get_text("RowGearValue") == "UP" and hud.debug_get_text("RowQuantumValue") == "OFF")

    # --- Speed gauge against the limiter -----------------------------------------------------------
    run(ship, 10.0, lin=(1, 0, 0))
    state = show(hud, ship)
    gauge = hud.debug_get_gauge("SpeedGauge")
    hud.debug_advance(0.05)
    check("the bar lags behind a jump in speed, then catches up", 0.0 < gauge.get_editor_property("display") < 0.9,
          "display %.2f of value %.2f" % (gauge.get_editor_property("display"), gauge.get_editor_property("value")))
    hud.debug_advance(2.0)
    check("full speed: gauge full, limiter mark at the top", abs(gauge.get_editor_property("value") - 1.0) < 0.01
          and abs(gauge.get_editor_property("marker") - 1.0) < 1e-4, "value %.3f marker %.3f" % (gauge.get_editor_property("value"), gauge.get_editor_property("marker")))
    check("speed number under the tube, m/s under it", hud.debug_get_text("SpeedValue") == "200" and hud.debug_get_text("SpeedUnit") == "m/s",
          hud.debug_get_text("SpeedValue"))
    ship.set_speed_limiter(0.5)
    run(ship, 10.0, lin=(1, 0, 0))
    state = show(hud, ship)
    check("limiter 50 %: fill and mark at half", abs(gauge.get_editor_property("value") - 0.5) < 0.01
          and abs(gauge.get_editor_property("marker") - 0.5) < 1e-4, "value %.3f marker %.3f" % (gauge.get_editor_property("value"), gauge.get_editor_property("marker")))
    check("LIMIT row shows the limiter", hud.debug_get_text("RowLimitValue") == "50%", repr(hud.debug_get_text("RowLimitValue")))
    ship.set_speed_limiter(0.25)
    run(ship, 0.2, lin=(1, 0, 0))
    state = show(hud, ship)
    # The fill stays green; the gauge paints the part above the limiter mark red by itself.
    check("faster than a lowered limiter: flagged, fill still green", state.over_limit and instrument(gauge.get_editor_property("fill_color")))
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
    check("decoupled: CPLD dark, its badge gone", not lamp(hud, "CPLD")[0] and not hud.debug_is_shown("Badge_CPLD"))
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
    cstb = hud.debug_get_lamp("CSTB")
    check("a lit lamp reaches full brightness", cstb.get_editor_property("intensity") > 0.99)
    ship.set_com_stab(False)
    show(hud, ship)
    before = cstb.get_editor_property("intensity")
    hud.debug_advance(0.03)
    mid = cstb.get_editor_property("intensity")
    check("switching a lamp fades it, not blinks", cstb.get_editor_property("flash") > 0.5 and before > mid > 0.05,
          "%.2f -> %.2f" % (before, mid))
    hud.debug_advance(1.0)
    check("the fade settles where the state says", cstb.get_editor_property("intensity") < 0.01 and cstb.get_editor_property("flash") < 0.01)
    ship.set_com_stab(True)
    show(hud, ship)
    hud.debug_advance(1.0)
    check("a lamp switched back on is fully lit again", cstb.get_editor_property("intensity") > 0.99)
    ship.set_g_safe(False)
    show(hud, ship)
    check("G-Safe off: GSAF dark, the shield dimmed", not lamp(hud, "GSAF")[0]
          and hud.debug_get_part("Shield").get_editor_property("color").a < 0.5)
    ship.set_g_safe(True)
    show(hud, ship)
    run(ship, 0.5, lin=(0, 1, 0), boost=True)
    state = show(hud, ship)
    lit_gsaf, color_gsaf = lamp(hud, "GSAF")
    lit_boost, color_boost = lamp(hud, "BOOST")
    # Boost is a normal state (bright green); G-Safe suspended by it is the caution (amber).
    check("boost: BOOST lit green, GSAF amber (suspended)", lit_boost and instrument(color_boost) and lit_gsaf and amber(color_gsaf),
          "boost %s gsaf %s" % (color_boost, color_gsaf))
    check("G follows the ship, the G-Safe limit under it", abs(state.g_force - ship.get_g_force()) < 1e-4
          and hud.debug_get_text("GValue") == "%.1f" % ship.get_g_force() and hud.debug_get_text("GMax") == "%.1f" % ship.get_g_safe_max_g(),
          hud.debug_get_text("GValue"))
    check("BOOST row shows the energy", ship.get_boost_energy() < 1.0 and hud.debug_get_text("RowBoostValue") == "%.0f%%" % (ship.get_boost_energy() * 100),
          hud.debug_get_text("RowBoostValue"))
    check("strafing right lights the strafe cross's right arrow", state.strafe_input.x > 0.5
          and hud.debug_get_part("Strafe").get_editor_property("value").x > 0.5, str(state.strafe_input))
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
    check("afterburner: AB BURN, gauge shows fuel", hud.debug_get_text("AfterburnerLabel") == "AB BURN"
          and abs(ab.get_editor_property("value") - ship.get_afterburner_fuel()) < 1e-4 and ship.get_afterburner_fuel() < 1.0,
          hud.debug_get_text("AfterburnerLabel"))
    check("afterburner: speed gauge rescales to the raised top speed, limiter mark stays at 100 %",
          abs(state.gauge_scale_cm_s - SCM * AB) < 1.0 and abs(gauge.get_editor_property("marker") - 1.0) < 1e-4 and instrument(gauge.get_editor_property("fill_color")),
          "scale %.0f m/s" % (state.gauge_scale_cm_s / 100))
    ship.set_afterburner_held(True)
    for _ in range(2000):
        if ship.is_afterburner_locked():
            break
        ship.debug_step_flight_input(STEP, unreal.Vector(1, 0, 0), unreal.Vector(0, 0, 0), False)
    ship.set_afterburner_held(False)
    show(hud, ship)
    check("empty tank: DRY", hud.debug_get_text("AfterburnerLabel").endswith("DRY"), hud.debug_get_text("AfterburnerLabel"))
    ship.toggle_master_mode()
    run(ship, 0.5)
    show(hud, ship)
    check("switching to NAV: mode label already NAV", hud.debug_get_text("ModeText") == "NAV")
    run(ship, 2.0)
    show(hud, ship)
    # Since 21. 9. 2026 (74ba375, the author's playtest) the gauge shows quantum fuel in NAV instead of a
    # dimmed "SCM only" afterburner.
    check("NAV: the afterburner gauge shows QT FUEL", hud.debug_get_text("AfterburnerLabel") == "QT FUEL",
          hud.debug_get_text("AfterburnerLabel"))
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

# --- Line batching (WORKFLOW 9.2g) --------------------------------------------------------------------------
# The drawn parts' lines are made by the root widget grouped by layer and thickness; 0 is only for an A/B.
check("space.HudLineBatch on by default (lines grouped: few Slate batches)",
      unreal.SystemLibrary.get_console_variable_int_value("space.HudLineBatch") == 1)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
