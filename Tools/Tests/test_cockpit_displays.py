"""Headless checks for the cockpit displays: the flight HUD's instruments on the Vanguard's dashboard.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_cockpit_displays.py

Nothing is drawn in a commandlet, so this checks what can be checked without a screen:
- USpaceCockpitDisplays builds two MFDs (FLIGHT left, SYSTEMS right) from the HUD's own widgets and the
  centre column's two small screens (RADAR over SELF STATUS),
  with the names USpaceFlightHud::ApplyState drives, in type big enough for a screen seen ~1.5 m away;
- ApplyState puts a ship's state into them exactly as into the HUD (same texts, same lamps);
- each screen's rectangle on the canvas is where the recipe maps its quad (texture_rect), and the centre
  screens have the shape of their glass;
- MFD pages: left FLIGHT / THRUSTERS / NAVIGATION, right STATUS / CONTACTS / SELF STATUS, switched with
  F1 and F2 (and [ ], Alt back) through the display component, the title and page tab following; what they list;
- the radar sees objects in range where they are (and not beyond it) and bodies as bearings; the self
  status page reads the Vanguard's hulls, engines and gear;
- the Vanguard's interior has the display slot (M_Ship_Vanguard_Screens, flat quads made by
  Tools/Blender/build_ai_ship.py), with the unlit display material, and UCockpitDisplayComponent finds it.
How the displays look: Tools/Shots.ps1 -Preset cockpit, and the step's report. Nothing is saved.
Prints "DISPTEST PASS" / "DISPTEST FAIL" lines and a summary.
"""

import json
import os

import unreal

STEP = 1.0 / 60.0
failures = []


def log(msg):
    unreal.log("DISPTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


# --- Widget tree ------------------------------------------------------------------------------------
displays = unreal.new_object(unreal.SpaceCockpitDisplays)
displays.debug_initialize()
names = set(displays.debug_get_widget_names())
expected = {"FlightScreen", "StatusScreen", "FlightTitle", "StatusTitle", "FlightGlass", "StatusGlass", "FlightKeys", "StatusKeys",
            "SpeedGauge", "GGauge", "BoostGauge", "AfterburnerGauge", "SpeedValue", "SpeedUnit", "GText", "GValue", "BoostText",
            "AfterburnerValue", "RowLimitValue", "GMax", "ModeText", "SubModeText", "RowGearValue", "RowCruiseValue", "RowRAltValue",
            "RowVsiValue", "RowAtmoValue", "FlightPages", "StatusPages",
            "Lamp_MODE", "Lamp_CPLD", "Lamp_GSAF", "Lamp_CSTB", "Lamp_BOOST", "Lamp_GEAR", "Lamp_PREC", "Lamp_CRUISE"}
check("two screens in the reference's MFD style (glass, title, keys, page tab) with every instrument", expected <= names, "missing %s" % sorted(expected - names))
check("no virtual joystick on the dashboard", "VirtualJoystick" not in names)
check("titles FLIGHT and STATUS", displays.debug_get_text("FlightTitle") == "FLIGHT" and displays.debug_get_text("StatusTitle") == "STATUS")
size = lambda name: displays.debug_get_text_widget(name).get_editor_property("font").get_editor_property("size")
check("big type: speed >= 48, keys and small figures >= 18 (a display is ~250 px wide on a 1600 px view)",
      size("SpeedValue") >= 48 and size("LampLabel_CPLD") >= 18 and size("RowLimitValue") >= 18 and size("BoostText") >= 18,
      "speed %d, key %d, limit %d, boost %d" % (size("SpeedValue"), size("LampLabel_CPLD"), size("RowLimitValue"), size("BoostText")))
check("switches drawn as the keys beside the reference's MFDs", displays.debug_get_lamp("CPLD").get_editor_property("button"))
check("power-page bars are blocks, not tubes", displays.debug_get_gauge("BoostGauge").get_editor_property("segments") > 0)
centre = {"RadarScreen", "ShipScreen", "RadarGlass", "ShipGlass", "Radar", "ShipStatus", "RadarRange", "RadarHeading", "RadarCount",
          "ShipGear", "ShipThrust"}
check("centre column: RADAR over SELF STATUS, each on its own glass", centre <= names, "missing %s" % sorted(centre - names))
check("centre screens titled like the reference (RADAR, SELF STATUS)",
      displays.debug_get_text("RadarHeaderCaption") == "RADAR" and displays.debug_get_text("ShipHeaderCaption") == "SELF STATUS")
check("centre screens' type readable (>= 16, the glass is ~11 cm wide)", size("RadarRange") >= 16 and size("ShipGear") >= 16 and size("RadarFooterCaption") >= 16)

# --- MFD pages ------------------------------------------------------------------------------------------
pages = {"FlightSwitcher", "StatusSwitcher", "ThrustPage", "NavPage", "ContactsPage", "SelfPage", "ShipStatusLarge"}
pages |= {"ThrustRow_%s" % a for a in ("MAIN", "RETRO", "STRAFE", "UP", "DOWN")} | {"ThrustGauge_%s" % a for a in ("MAIN", "RETRO", "STRAFE", "UP", "DOWN")}
pages |= {"NavRow_%d" % i for i in range(4)} | {"ContactRow_%d" % i for i in range(6)} | {"SelfGear", "SelfEngines", "SelfBoost", "SelfAfterburner", "SelfState"}
check("MFD pages: THRUSTERS and NAVIGATION on the left, CONTACTS and SELF STATUS on the right", pages <= names, "missing %s" % sorted(pages - names))
check("each MFD starts on its first page", displays.debug_get_page(0) == 0 and displays.debug_get_page(1) == 0)
displays.set_pages(1, 2)
check("pages switch, title and page tab follow", displays.debug_get_page(0) == 1 and displays.debug_get_page(1) == 2
      and displays.debug_get_text("FlightTitle") == "THRUSTERS" and displays.debug_get_text("FlightPage") == "THRUSTERS"
      and displays.debug_get_text("StatusTitle") == "SELF STATUS", "%d %d %r %r" % (displays.debug_get_page(0), displays.debug_get_page(1),
                                                                             displays.debug_get_text("FlightTitle"), displays.debug_get_text("StatusTitle")))
displays.set_pages(3, -1)
check("pages wrap round both ways", displays.debug_get_page(0) == 0 and displays.debug_get_page(1) == 2)
displays.set_pages(0, 0)
check("thrust bars are block bars along the row", displays.debug_get_gauge("ThrustGauge_MAIN").get_editor_property("horizontal")
      and displays.debug_get_gauge("ThrustGauge_MAIN").get_editor_property("segments") > 0)

# --- The canvas and the recipe agree ---------------------------------------------------------------
recipe_path = os.path.join(unreal.Paths.project_dir(), "ArtSource", "Ships", "Vanguard", "Vanguard_ai_build.json")
recipe = json.load(open(recipe_path, encoding="utf-8"))["interior"]["displays"]
rect = lambda name: displays.debug_get_screen_rect(name)
screen_names = ("left", "right", "centre_top", "centre_bottom")
canvas = [max(rect(n).z for n in screen_names), max(rect(n).w for n in screen_names)]
check("recipe texture_size is the game's canvas", [round(v) for v in canvas] == recipe["texture_size"], "%s vs %s" % (canvas, recipe["texture_size"]))
for screen in recipe["screens"]:
    r = rect(screen["name"])
    check("screen %s maps where the game draws it" % screen["name"], [round(r.x), round(r.y), round(r.z), round(r.w)] == screen.get("texture_rect"),
          "%s vs %s" % ([r.x, r.y, r.z, r.w], screen.get("texture_rect")))
    tl, tr, br, bl = screen["corners"]
    glass = ((tr[0] - tl[0] + br[0] - bl[0]) / 2.0) / ((tl[1] - bl[1] + tr[1] - br[1]) / 2.0)
    shown = (r.z - r.x) / (r.w - r.y)
    check("screen %s drawn in the shape of its glass (%.2f vs %.2f)" % (screen["name"], shown, glass), abs(shown / glass - 1.0) < 0.08)
check("the four screens: two MFDs and the centre column", sorted(s["name"] for s in recipe["screens"]) == ["centre_bottom", "centre_top", "left", "right"])

# --- Driven like the HUD ------------------------------------------------------------------------------
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
try:
    for _ in range(90):
        ship.debug_step_flight_input(STEP, unreal.Vector(1.0, 0.0, 0.0), unreal.Vector(0.0, 0.0, 0.0), False)
    hud = unreal.new_object(unreal.SpaceFlightHud)
    hud.debug_initialize()
    state = unreal.SpaceFlightHud.make_state(ship, 1)
    hud.apply_state(state)
    displays.apply_state(state)
    same = [displays.debug_get_text("SpeedValue") == hud.debug_get_text("SpeedValue"),
            displays.debug_get_text("GValue") == hud.debug_get_text("GValue"),
            displays.debug_get_text("BoostText") == hud.debug_get_text("RowBoostValue"),
            displays.debug_get_text("AfterburnerValue") == hud.debug_get_text("AfterburnerValue")]
    check("the displays read the same as the HUD", all(same), "%s; speed %r vs %r" % (same, displays.debug_get_text("SpeedText"), hud.debug_get_text("SpeedValue")))
    check("speed shown, not zero", displays.debug_get_text("SpeedValue") not in ("", "0"), displays.debug_get_text("SpeedValue"))
    lit = lambda w, n: w.debug_is_lamp_lit(n) is not None
    check("lamps match the HUD's", all(lit(displays, n) == lit(hud, n) for n in ("MODE", "CPLD", "GSAF", "CSTB", "BOOST", "GEAR", "PREC", "CRUISE")))
    check("the pawn has the display component", isinstance(ship.get_editor_property("cockpit_displays"), unreal.CockpitDisplayComponent))
    cockpit_camera = ship.get_editor_property("cockpit_camera")
    pp = cockpit_camera.get_editor_property("post_process_settings")
    check("no motion blur from the seat (camera shake smeared the displays)",
          pp.get_editor_property("override_motion_blur_amount") and pp.get_editor_property("motion_blur_amount") == 0.0)
    component = ship.get_editor_property("cockpit_displays")
    component.cycle_page(0, 1)
    first = component.get_page(0)
    component.cycle_page(0, -1)
    component.cycle_page(0, -1)
    component.set_page(1, 5)
    check("the display component pages: [ forward, Alt+[ back, wrapping", first == 1 and component.get_page(0) == 2 and component.get_page(1) == 2,
          "%d %d %d" % (first, component.get_page(0), component.get_page(1)))
    component.set_page(0, 0)
    component.set_page(1, 0)
    scale = ship.get_editor_property("cockpit_displays").pixel_scale()
    check("displays drawn at about their size on screen (1920 px wide: ~0.65 of the 560 px layout)", 0.5 < scale < 0.8, "%.2f" % scale)

    # --- Radar ----------------------------------------------------------------------------------------
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    # Relative to where the ship is now (it flew ahead above); it still points along +X.
    at = ship.get_actor_location()
    near = eas.spawn_actor_from_class(unreal.StaticMeshActor, at + unreal.Vector(100000, 20000, 10000), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    near.static_mesh_component.set_static_mesh(cube)
    far = eas.spawn_actor_from_class(unreal.StaticMeshActor, at + unreal.Vector(-800000, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    far.static_mesh_component.set_static_mesh(cube)
    moon = eas.spawn_actor_from_class(unreal.DistantBody, unreal.Vector(0, -100000000, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    try:
        contacts = unreal.SpaceCockpitDisplays.make_radar_contacts(ship, 5000.0)
        objects = [c for c in contacts if not c.get_editor_property("body")]
        bodies = [c for c in contacts if c.get_editor_property("body")]
        pos = objects[0].get_editor_property("position") if objects else None
        check("radar: the object 1 km ahead, 200 m right, 100 m up is there, where it is (and the one 8 km behind is not)",
              len(objects) == 1 and abs(pos.x - 200.0) < 1.0 and abs(pos.y - 1000.0) < 1.0 and abs(objects[0].get_editor_property("height_m") - 100.0) < 1.0,
              "%d objects, %s" % (len(objects), pos))
        check("radar: a distant body as a bearing (left of the nose)", len(bodies) == 1 and bodies[0].get_editor_property("position").x < 0.0,
              "%d bodies" % len(bodies))
        plot = unreal.SpaceHudRadar.plot_position(objects[0], 5000.0) if objects else None
        check("radar plots the contact 0.04 of the radius right and 0.2 ahead", plot is not None and abs(plot.x - 0.04) < 0.001 and abs(plot.y - 0.2) < 0.001, str(plot))
        rim = unreal.SpaceHudRadar.plot_position(bodies[0], 5000.0) if bodies else None
        check("a body sits on the rim", rim is not None and abs(rim.length() - 1.0) < 0.001, str(rim))
        dstate = unreal.SpaceCockpitDisplays.make_display_state(ship, 5000.0)
        displays.apply_state(dstate)
        radar = displays.debug_get_part("Radar")
        shown_contacts = len(radar.get_editor_property("contacts"))
        check("the radar page gets the contacts, count and range", shown_contacts == 2 and displays.debug_get_text("RadarCount") == "1"
              and displays.debug_get_text("RadarRange") == "5.0 KM",
              "%d, %r, %r" % (shown_contacts, displays.debug_get_text("RadarCount"), displays.debug_get_text("RadarRange")))
        check("no body near: heading shown as ---", displays.debug_get_text("RadarHeading") == "---", displays.debug_get_text("RadarHeading"))
        row = [displays.debug_get_text(n) for n in ("ContactName_0", "ContactDist_0", "ContactBrg_0", "ContactElev_0")]
        check("contacts page lists the cube: name, range, bearing from the nose, elevation", row == ["CUBE", "1.02 KM", "011\u00b0", "+6\u00b0"]
              and displays.debug_is_shown("ContactRow_0") and not displays.debug_is_shown("ContactRow_1") and not displays.debug_is_shown("ContactsEmpty"), repr(row))
        nav = [displays.debug_get_text(n) for n in ("NavDist_0", "NavBrg_0")]
        check("navigation page lists the body: range to its surface and bearing (left: 270)", nav == ["900 KM", "270\u00b0"]
              and displays.debug_is_shown("NavRow_0") and not displays.debug_is_shown("NavRow_1"), repr(nav))
        thrust = displays.debug_get_text("ThrustValue_MAIN")
        check("thrusters page: main thrust against its capacity (8.0 G)", thrust.endswith("/ 8.0 G"), thrust)
        check("self status page: state, gear, engines, boost, afterburner", displays.debug_get_text("SelfState") == "FLYING"
              and displays.debug_get_text("SelfGear") == "UP" and displays.debug_get_text("SelfBoost").endswith("%"), displays.debug_get_text("SelfState"))
        check("self status: gear and thrust in the footer (LANDED in its place on the ground)", displays.debug_get_text("ShipGear") == "UP"
              and displays.debug_get_text("ShipThrust").endswith("%"), "%r %r" % (displays.debug_get_text("ShipGear"), displays.debug_get_text("ShipThrust")))
        below = unreal.SpaceRadarContact()
        below.set_editor_property("body", True)
        below.set_editor_property("position", unreal.Vector2D(100.0, 100.0))
        below.set_editor_property("height_m", -300.0)
        check("no bearing for a body more than 60 degrees under the wings (the planet below, landed on a slope)",
              unreal.SpaceHudRadar.plot_position(below, 5000.0).length() == 0.0)
    finally:
        for actor in (near, far, moon):
            eas.destroy_actor(actor)

finally:
    eas.destroy_actor(ship)

# --- The Vanguard's display slot and material ----------------------------------------------------
mesh = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Vanguard/Meshes/SM_Ship_Vanguard_Interior")
slots = [str(m.get_editor_property("material_slot_name")) for m in mesh.get_editor_property("static_materials")]
check("interior mesh has the display slot", "M_Ship_Vanguard_Screens" in slots, ", ".join(slots))
master = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Shared/Materials/M_Ship_Screen")
check("display master is unlit (no sky reflections over the instruments)",
      master is not None and master.get_editor_property("shading_model") == unreal.MaterialShadingModel.MSM_UNLIT)
check("display master opaque with pixel animation (the variants past or around temporal AA were worse)",
      master.get_editor_property("has_pixel_animation") and master.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_OPAQUE)
vanguard = eas.spawn_actor_from_class(unreal.EditorAssetLibrary.load_blueprint_class("/Game/Ships/Vanguard/Blueprints/BP_Ship_Vanguard"),
                                      unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
try:
    found, slot = unreal.CockpitDisplayComponent.find_display_slot(vanguard, "_Screens")
    check("display component finds the slot on the Interior component", found is not None and found.get_name() == "Interior" and slot >= 0,
          "%s slot %s" % (found and found.get_name(), slot))
    material = found.get_material(slot) if found else None
    parent = material.get_editor_property("parent") if isinstance(material, unreal.MaterialInstance) else None
    check("display slot has MI_Ship_Vanguard_Screens on M_Ship_Screen", material is not None and material.get_name() == "MI_Ship_Vanguard_Screens"
          and parent is not None and parent.get_name() == "M_Ship_Screen", "%s / %s" % (material and material.get_name(), parent and parent.get_name()))
    sockets = [str(n) for n in found.get_all_socket_names()] if found else []
    check("a Display_ socket in front of each screen (their glow)", sorted(n for n in sockets if n.startswith("Display_"))
          == ["Display_centre_bottom", "Display_centre_top", "Display_left", "Display_right"], ", ".join(sockets))
    status = displays.debug_get_part("ShipStatus")
    status.set_ship(vanguard)
    check("self status reads the Vanguard: its collision hulls, 4 engines, 3 gear legs", status.get_outline_count() >= 8
          and len(status.get_editor_property("engines")) == 4 and len(status.get_editor_property("gear")) == 3,
          "%d outlines, %d engines, %d gear" % (status.get_outline_count(), len(status.get_editor_property("engines")), len(status.get_editor_property("gear"))))
    displays_component = vanguard.get_editor_property("cockpit_displays")
    check("figures change at most ~6 times a second, so temporal AA settles on each number (setup state_rate_hz)",
          displays_component.get_editor_property("state_rate_hz") <= 6.0, "%.1f" % displays_component.get_editor_property("state_rate_hz"))
    check("displays light the cockpit (setup display_light_intensity_cd > 0)", displays_component.get_editor_property("display_light_intensity_cd") > 0.0)
    hull_mesh = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Vanguard/Meshes/SM_Ship_Vanguard")
    hull_slots = [str(m.get_editor_property("material_slot_name")) for m in hull_mesh.get_editor_property("static_materials")]
    check("inside of the canopy frame has its own dark slot", "M_Ship_Vanguard_CanopyFrame" in hull_slots, ", ".join(hull_slots))
    frame = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Vanguard/Materials/MI_Ship_Vanguard_CanopyFrame")
    base = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(frame, "BaseColor") if frame else None
    check("canopy frame material is dark (below 0.1)", base is not None and max(base.r, base.g, base.b) < 0.1, str(base))
finally:
    eas.destroy_actor(vanguard)

# --- The keys: F1 and F2 (and [ ]) ---------------------------------------------------------------------
imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Spaceship")
mappings = [(str(m.get_editor_property("key").get_editor_property("key_name")), m.get_editor_property("action").get_name() if m.get_editor_property("action") else "")
            for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")]
check("F1 pages the left MFD, F2 the right one; [ and ] too, for a US keyboard (IMC_Spaceship)",
      all(m in mappings for m in (("F1", "IA_MfdLeft"), ("F2", "IA_MfdRight"), ("LeftBracket", "IA_MfdLeft"), ("RightBracket", "IA_MfdRight"))), repr(mappings))
check("nothing else on F1, F2, [ and ]", sorted(a for k, a in mappings if k in ("F1", "F2", "LeftBracket", "RightBracket"))
      == ["IA_MfdLeft", "IA_MfdLeft", "IA_MfdRight", "IA_MfdRight"])
ini = open(os.path.join(unreal.Paths.project_dir(), "Config", "DefaultInput.ini"), encoding="utf-8").read()
check("the engine's debug views are off F1 and F2 (they work in the Development build that is played)",
      '-DebugExecBindings=(Key=F1,Command="viewmode wireframe", bIgnoreShift=True)' in ini and '-DebugExecBindings=(Key=F2,Command="viewmode unlit")' in ini)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
