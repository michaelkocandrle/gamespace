"""Headless checks for the cockpit displays: the flight HUD's instruments on the Vanguard's dashboard.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_cockpit_displays.py

Nothing is drawn in a commandlet, so this checks what can be checked without a screen:
- USpaceCockpitDisplays builds two screens (FLIGHT left, SYSTEMS right) from the HUD's own widgets,
  with the names USpaceFlightHud::ApplyState drives, in type big enough for a screen seen ~1.5 m away;
- ApplyState puts a ship's state into them exactly as into the HUD (same texts, same lamps);
- the Vanguard's interior has the display slot (M_Ship_Vanguard_Screens, flat quads made by
  Tools/Blender/build_ai_ship.py), with the unlit display material, and UCockpitDisplayComponent finds it.
How the displays look: Tools/Shots.ps1 -Preset cockpit, and the step's report. Nothing is saved.
Prints "DISPTEST PASS" / "DISPTEST FAIL" lines and a summary.
"""

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
    scale = ship.get_editor_property("cockpit_displays").pixel_scale()
    check("displays drawn at about their size on screen (1920 px wide: ~0.65 of the 560 px layout)", 0.5 < scale < 0.8, "%.2f" % scale)

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
    check("a Display_ socket in front of each screen (their glow)", sorted(n for n in sockets if n.startswith("Display_")) == ["Display_left", "Display_right"],
          ", ".join(sockets))
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

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
