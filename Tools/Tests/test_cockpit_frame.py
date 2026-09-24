"""Headless checks for the cockpit: the placeholder frame for ships without a modelled interior, and the ship's own interior.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_cockpit_frame.py

The frame's parts are boxes placed relative to the pilot's eye (SpaceshipPawn.GetPlaceholderCockpitCorners).
Checked against the cockpit camera's view (field of view of the ship under test, Tools/Tests/ship_under_test.py,
or of the native pawn while there is none; 16:9) and the flight HUD, which spans roughly +-26 degrees across and
down to ~15 degrees below the horizon:
  1. nothing of it inside the HUD's window; nothing behind the eye in front
  2. the dashboard's top edge 14..20 degrees below the horizon (under the HUD, not higher)
  3. the dashboard covers the bottom of the view in the middle; the screens are on it and in view
  4. the pillars stand in view left and right, outside the HUD, 24..34 degrees off centre at the bottom
  5. the seat: back and headrest behind the eye, the cushion under the pilot (free look only)
  6. the ship under test (skipped without one): placeholder off, the interior part in the Blueprint, the eye over
     the interior's tub, behind its dashboard, whose top is 7..13 degrees below the eye (the manifest's interior bounds)
The placeholder's layout (1-5) is checked whatever ship uses it.
Prints "COCKPITTEST PASS" / "COCKPITTEST FAIL" lines and a summary.
"""

import math

import unreal

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import ship_under_test as sut  # noqa: E402

failures = []


def log(msg):
    unreal.log("COCKPITTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def angles(p):
    """(yaw, pitch) in degrees of a point in eye space (X forward, Y right, Z up)."""
    return math.degrees(math.atan2(p[1], p[0])), math.degrees(math.atan2(p[2], math.hypot(p[0], p[1])))


def edge_samples(corners, steps=8):
    """Points along the twelve edges of a box given by its eight corners (index bits: X, Y, Z)."""
    out = []
    for a in range(8):
        for bit in (1, 2, 4):
            b = a | bit
            if b == a:
                continue
            for i in range(steps + 1):
                t = i / steps
                out.append(tuple(corners[a][k] + (corners[b][k] - corners[a][k]) * t for k in range(3)))
    return out


pawn = sut.flight_cdo()
log("INFO ship: %s" % sut.label())
fov = pawn.get_editor_property("cockpit_camera").get_editor_property("field_of_view")
half_h = fov / 2.0
half_v = math.degrees(math.atan(math.tan(math.radians(half_h)) * 9.0 / 16.0))
log("INFO view %.0f x %.1f degrees" % (2 * half_h, 2 * half_v))

names = [str(n) for n in pawn.get_placeholder_cockpit_part_names()]
raw = [(c.x, c.y, c.z) for c in pawn.get_placeholder_cockpit_corners()]
check("eight corners per part", len(raw) == 8 * len(names), "%d parts" % len(names))
parts = {name: raw[i * 8:(i + 1) * 8] for i, name in enumerate(names)}
front = {n: c for n, c in parts.items() if not n.startswith(("Seat", "Headrest"))}


def in_view(p):
    yaw, pitch = angles(p)
    return p[0] > 0 and abs(yaw) < half_h and abs(pitch) < half_v


# 1) HUD window stays clear
HUD_YAW, HUD_BOTTOM = 26.0, -15.0
intruders = []
for name, corners in front.items():
    for p in edge_samples(corners):
        yaw, pitch = angles(p)
        if p[0] > 0 and abs(yaw) < HUD_YAW and pitch > HUD_BOTTOM:
            intruders.append("%s at %.0f / %.0f deg" % (name, yaw, pitch))
            break
check("nothing in the HUD's window (+-%d deg across, above %d deg)" % (HUD_YAW, HUD_BOTTOM), not intruders, "; ".join(intruders))
check("the front parts are all ahead of the eye", all(p[0] > 20.0 for c in front.values() for p in c))

# 2) dashboard top edge
dash = [n for n in names if n in ("InstrumentPanel", "GlareShield", "DashboardBody")]
top = max(angles(p)[1] for n in dash for p in edge_samples(parts[n]) if abs(angles(p)[0]) < 20.0)
check("dashboard top 14..20 deg below the horizon (under the HUD)", -20.0 <= top <= -14.0, "%.1f deg, %.0f %% of the height" % (
    top, 100 * (0.5 - 0.5 * math.tan(math.radians(top)) / math.tan(math.radians(half_v)))))

# 3) covers the bottom middle; screens in view on it
lowest = min(angles(p)[1] for n in dash for p in edge_samples(parts[n]) if abs(angles(p)[0]) < 10.0 and p[0] > 0)
check("dashboard reaches below the bottom of the view in the middle", lowest < -half_v, "%.1f deg" % lowest)
screens = [n for n in names if n.startswith("Screen")]
visible = [n for n in screens if any(in_view(p) for p in edge_samples(parts[n]))]
check("the screens are in view", screens and visible == screens, ", ".join(visible))
panel_normal_up = all(min(p[2] for p in parts[s]) > min(p[2] for p in parts["InstrumentPanel"]) for s in screens)
check("the screens lie on the instrument panel", panel_normal_up)

# 4) pillars
for side in ("PillarLeft", "PillarRight"):
    samples = [p for p in edge_samples(parts[side]) if in_view(p)]
    bottom = min(samples, key=lambda p: p[2]) if samples else None
    yaw = abs(angles(bottom)[0]) if bottom else 0.0
    check("%s in view, 24..34 deg off centre at the bottom" % side, samples and 24.0 <= yaw <= 34.0, "%.1f deg" % yaw)

# 5) seat
back = [n for n in names if n in ("SeatBack", "Headrest")]
check("seat back and headrest behind the eye", len(back) == 2 and all(p[0] < 0 for n in back for p in parts[n]))
check("seat cushion under the pilot, out of the forward view",
      "SeatCushion" in parts and not any(in_view(p) for p in edge_samples(parts["SeatCushion"])))

# 6) the ship's modelled interior (Tools/Tests/ship_under_test.py)
if not sut.SHIP:
    sut.skip(log, "the modelled cockpit interior, the eye over its tub and behind its dashboard")
else:
    manifest = sut.manifest()
    interior = manifest["meshes"].get("SM_Ship_%s_Interior" % sut.SHIP)
    check("placeholder cockpit off (the ship has a modelled interior)", not pawn.get_editor_property("placeholder_cockpit"))
    check("interior part in the manifest", interior is not None and interior["part"] == "Interior", str(interior and interior["tris"]))
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    ship = eas.spawn_actor_from_class(sut.bp_class(),
                                      unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    try:
        meshes = {c.get_name(): c for c in ship.get_components_by_class(unreal.StaticMeshComponent)}
        part = meshes.get("Interior")
        check("Interior component with the interior mesh", part is not None and part.get_editor_property("static_mesh") is not None
              and part.get_editor_property("static_mesh").get_name() == "SM_Ship_%s_Interior" % sut.SHIP, ", ".join(sorted(meshes)))
        eye = ship.get_editor_property("cockpit_camera").get_editor_property("relative_location")
        offset = ship.get_editor_property("hull").get_editor_property("relative_location")
        (lx, ly, lz), (hx, hy, hz) = [[c * 100.0 for c in corner] for corner in interior["bounds_m"]]
        ex, ez = eye.x - offset.x, eye.z - offset.z
        check("eye over the interior's tub, behind its dashboard", lx < ex < hx - 40.0 and abs(eye.y) < 1.0 and ez > hz,
              "eye (%.0f, %.0f, %.0f), interior x %.0f..%.0f top %.0f" % (eye.x, eye.y, eye.z, lx, hx, hz))
        angle = math.degrees(math.atan2(ez - hz, hx - ex))
        # The Star Citizen reference (Docs/UI/Screenshot 2026-09-17 201854.png): the dashboard top ~8 degrees below the eye,
        # the pilot sitting well back from it; the HUD is compact and stays above it.
        check("dashboard top 7..13 deg below the eye (as in the reference)", 7.0 <= angle <= 13.0, "%.1f deg" % angle)
        check("pilot well back from the dashboard (>= 1.2 m)", hx - ex >= 120.0, "%.0f cm" % (hx - ex))
    finally:
        eas.destroy_actor(ship)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
