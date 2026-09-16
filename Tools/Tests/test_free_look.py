"""Headless checks for ship free look (hold right mouse button).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_free_look.py

Spawns a temporary ship in the editor world and drives its real steering and free look code frame
by frame (1/60 s) through SpaceshipPawn.debug_simulate_free_look. Never saves.
Prints "FLTEST PASS" / "FLTEST FAIL" lines and a summary.
"""

import unreal

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
    frames += [(10.0, 0.0, 0.0)] * 20          # 221-240 steering again

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
    check("steering works right after release", turned(rot[221], rot[224]) > 0.05, "%.3f deg in 3 frames" % turned(rot[221], rot[224]))
    check("steering after release does not move the camera", all(abs(c[0]) < 1e-6 for c in cam[221:]))
    log("INFO camera: held peak yaw %.1f pitch %.1f, 95 %% back in %.2f s" % (peak_yaw, peak_pitch, t95 or -1))
finally:
    eas.destroy_actor(ship)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
