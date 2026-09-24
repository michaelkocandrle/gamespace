"""Headless checks for ship free look (hold right mouse button).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_free_look.py

Spawns a temporary ship in the editor world and drives its real steering and free look code frame
by frame (1/60 s) through SpaceshipPawn.debug_simulate_free_look. Never saves.
Prints "FLTEST PASS" / "FLTEST FAIL" lines and a summary.
"""

import unreal

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import ship_under_test as sut  # noqa: E402

failures = []


def log(msg):
    unreal.log("FLTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


# ---------------------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------------------
action = unreal.EditorAssetLibrary.load_asset("/Game/Input/IA_FreeLook")
check("IA_FreeLook is a held bool", isinstance(action, unreal.InputAction)
      and action.get_editor_property("value_type") == unreal.InputActionValueType.BOOLEAN
      and len(action.get_editor_property("triggers")) == 0)
imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Spaceship")
pairs = set()
for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings"):
    a = m.get_editor_property("action")
    pairs.add((str(m.get_editor_property("key").get_editor_property("key_name")), a.get_name() if a else None))
check("right mouse button mapped, flight mappings kept",
      ("RightMouseButton", "IA_FreeLook") in pairs and {("W", "IA_Thrust"), ("F", "IA_Interact"), ("C", "IA_ToggleCamera")} <= pairs,
      "%d mappings" % len(pairs))

cdo = unreal.get_default_object(unreal.SpaceshipPawn)
sens = cdo.get_editor_property("free_look_sensitivity")
max_yaw = cdo.get_editor_property("free_look_max_yaw_deg")
max_pitch = cdo.get_editor_property("free_look_max_pitch_deg")
log("INFO free look sensitivity %.2f deg/count (steering %.2f stick/count), limits yaw +-%.0f, pitch +-%.0f" % (
    sens, cdo.get_editor_property("mouse_sensitivity"), max_yaw, max_pitch))
check("sensitivity is 4x the steering number", abs(sens - 4 * cdo.get_editor_property("mouse_sensitivity")) < 1e-3)

# ---------------------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------------------
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 80000.0))
try:
    frames = []
    frames += [(10.0, 5.0, 0.0)] * 30          # 0-29   steering: the ship turns
    frames += [(0.0, 0.0, 1.0)] * 1            # 30     press
    frames += [(20.0, 8.0, 1.0)] * 60          # 31-90  look right and up, far past the limits
    frames += [(-30.0, -30.0, 1.0)] * 40       # 91-130 look left and down, past the limits
    frames += [(0.0, 0.0, 0.0)] * 90           # 131-220 release: swing back
    frames += [(30.0, 0.0, 0.0)] * 20          # 221-240 steering again

    out = ship.debug_simulate_free_look([unreal.Vector(*f) for f in frames])
    cam = [(out[2 * i].x, out[2 * i].y, out[2 * i].z) for i in range(len(frames))]
    rot = [(out[2 * i + 1].x, out[2 * i + 1].y, out[2 * i + 1].z) for i in range(len(frames))]

    def turned(a, b):
        return max(abs(a[0] - b[0]), abs(((a[1] - b[1]) + 180.0) % 360.0 - 180.0))

    check("steering turns the ship before free look", turned(rot[0], rot[29]) > 1.0, "%.2f deg" % turned(rot[0], rot[29]))
    held = range(30, 131)
    drift = max(turned(rot[30], rot[i]) for i in held)
    check("ship pitch/yaw frozen while held", drift < 0.01, "max change %.4f deg over %d frames" % (drift, len(held)))
    check("camera stays straight when steering", all(abs(c[0]) < 1e-6 and abs(c[1]) < 1e-6 for c in cam[:30]))

    peak_yaw = max(c[0] for c in cam[31:91])
    peak_pitch = max(c[1] for c in cam[31:91])
    low_yaw = min(c[0] for c in cam[91:131])
    low_pitch = min(c[1] for c in cam[91:131])
    if max_yaw >= 180.0:
        # All the way round (the default): the chase camera orbits the ship.
        check("yaw unlimited", peak_yaw > 180.0, "range %.1f .. %.1f" % (low_yaw, peak_yaw))
    else:
        check("yaw limited to +-%.0f" % max_yaw, peak_yaw <= max_yaw + 1e-3 and low_yaw >= -max_yaw - 1e-3 and peak_yaw > max_yaw - 1.0,
              "range %.1f .. %.1f" % (low_yaw, peak_yaw))
    check("pitch limited to +-%.0f" % max_pitch, peak_pitch <= max_pitch + 1e-3 and low_pitch >= -max_pitch - 1e-3 and peak_pitch > max_pitch - 1.0,
          "range %.1f .. %.1f" % (low_pitch, peak_pitch))
    first_step = max(abs(cam[31][0] - cam[30][0]), abs(cam[31][1] - cam[30][1]))
    check("camera follows the mouse smoothly (no jump to target)", 0.5 < first_step < 20 * sens,
          "first frame %.2f deg of %.2f requested" % (first_step, 20 * sens))
    check("mouse right/up turns the camera right/up", cam[40][0] > 0 and cam[40][1] > 0)

    back = cam[131:221]
    steps = [max(abs(back[i + 1][0] - back[i][0]), abs(back[i + 1][1] - back[i][1])) for i in range(len(back) - 1)]
    monotonic = all(abs(back[i + 1][0]) <= abs(back[i][0]) + 1e-6 and abs(back[i + 1][1]) <= abs(back[i][1]) + 1e-6 for i in range(len(back) - 1))
    start = max(abs(back[0][0]), abs(back[0][1]))
    t95 = next((i / 60.0 for i, c in enumerate(back) if max(abs(c[0]), abs(c[1])) <= 0.05 * start), None)
    check("released camera swings back monotonically", monotonic)
    check("swing back is smooth", max(steps) < 12.0, "max %.2f deg per frame from %.0f deg" % (max(steps), start))
    check("swing back takes about half a second", t95 is not None and 0.3 < t95 < 0.8, "95 %% after %s s" % (t95,))
    check("camera fully back", max(abs(back[-1][0]), abs(back[-1][1])) < 0.01, "%s" % (back[-1],))
    check("mouse does not turn the ship during the swing back", turned(rot[131], rot[220]) < 0.01)
    # The virtual joystick has to leave its dead zone and the rotation has inertia, so give it 10 frames.
    check("steering works right after release", turned(rot[221], rot[231]) > 0.3, "%.3f deg in 10 frames" % turned(rot[221], rot[231]))
    check("steering after release does not move the camera", all(abs(c[0]) < 1e-6 for c in cam[221:]))
    log("INFO camera: held peak yaw %.1f pitch %.1f, 95 %% back in %.2f s" % (peak_yaw, peak_pitch, t95 or -1))
finally:
    eas.destroy_actor(ship)

# --- Dashboard focus (Z / middle mouse button): lean in to the displays, as the reference does -----------
# Needs the model's Display_ sockets, so only with a modelled ship (Tools/Tests/ship_under_test.py).
if not sut.SHIP:
    sut.skip(log, "dashboard focus towards the Display_ sockets")
elif not any(n.startswith("Display_") for n in sut.socket_names()):
    sut.skip(log, "dashboard focus towards the Display_ sockets", "%s has no Display_ sockets yet (no modelled cockpit)" % sut.SHIP)
else:
    ship = eas.spawn_actor_from_class(sut.bp_class(), unreal.Vector(0.0, 0.0, 80000.0))
    try:
        camera = ship.get_editor_property("cockpit_camera")
        eye0 = camera.get_editor_property("relative_location")
        # Python gives the out parameters, or None when the function returns false.
        found = ship.compute_dashboard_focus()
        ok = found is not None
        eye, rotation, fov = found if ok else (eye0, unreal.Rotator(), 0.0)
        lean = (eye - eye0).length()
        check("focus found from the Display_ sockets: the head leans ~15 cm towards them", ok and 14.0 < lean < 16.0 and eye.x > eye0.x and eye.z < eye0.z,
              "%s, %.1f cm" % (ok, lean))
        check("focus looks down at the dashboard (the displays are 14-25 degrees under the eye)", -30.0 < rotation.pitch < -10.0 and abs(rotation.yaw) < 2.0,
              "pitch %.1f yaw %.1f" % (rotation.pitch, rotation.yaw))
        check("focus narrows the view so the displays fill it (30-60 degrees, the normal view is ~88)", 30.0 < fov < 60.0, "%.1f" % fov)
        ship.set_dashboard_focus(True)
        ship.debug_advance_dashboard_focus(1.0)
        turned_to = camera.get_editor_property("relative_rotation")
        check("held: the head turns to the dashboard within a second", ship.get_dashboard_focus() > 0.95 and abs(turned_to.pitch - rotation.pitch) < 1.5,
              "%.2f, pitch %.1f" % (ship.get_dashboard_focus(), turned_to.pitch))
        ship.set_dashboard_focus(False)
        ship.debug_advance_dashboard_focus(1.5)
        back = camera.get_editor_property("relative_rotation")
        rest = ship.get_editor_property("cockpit_view_pitch_deg")
        check("released: back to the normal view (its rest tilt, setup cockpit_view_pitch_deg)", ship.get_dashboard_focus() == 0.0 and abs(back.pitch - rest) < 0.01,
              "%.3f, pitch %.2f, rest %.2f" % (ship.get_dashboard_focus(), back.pitch, rest))
        check("the ship's view rests a little tilted down, towards its displays (-2..-5 deg)", -5.0 <= rest <= -2.0, "%.1f" % rest)
    finally:
        eas.destroy_actor(ship)
imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Spaceship")
keys = [str(m.get_editor_property("key").get_editor_property("key_name")) for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
        if m.get_editor_property("action") and m.get_editor_property("action").get_name() == "IA_DashboardFocus"]
others = [m.get_editor_property("action").get_name() for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
          if str(m.get_editor_property("key").get_editor_property("key_name")) in ("Z", "MiddleMouseButton") and m.get_editor_property("action").get_name() != "IA_DashboardFocus"]
check("focus on Z and the middle mouse button, nothing else there", sorted(keys) == ["MiddleMouseButton", "Z"] and not others, "%s %s" % (keys, others))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
