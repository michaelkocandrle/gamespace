"""Headless checks for SC-3: the flight path marker on the HUD.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_flight_hud_sc3.py

Star Citizen flies by where the ship is going, not where its nose points - decoupled the two part
company completely. USpaceFlightHud.ApplyView projects the velocity onto the HUD's own 1080p canvas;
this checks that projection against the geometry it claims to do, because a marker that is off by a
sign is worse than no marker at all.

Covers: nothing below walking pace, dead centre when the flight path is down the view's axis, the
right side of the screen for a view turned off it, the offset matching the focal length, the marker
pinned inside a circle, and the hollow mirrored marker when the flight path is behind the nose.
Nothing is saved. Prints "SC3TEST PASS" / "SC3TEST FAIL" lines and a summary.
"""

import json
import math
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESIGN_WIDTH = 1920.0
MARKER_RADIUS = 330.0
MIN_SPEED = 500.0
failures = []


def log(msg):
    unreal.log("SC3TEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def focal(fov_deg):
    return (DESIGN_WIDTH * 0.5) / math.tan(math.radians(fov_deg) * 0.5)


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.new_level("/Temp/Sc3Test")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))


def marker(velocity, view=(0.0, 0.0, 0.0), fov=90.0):
    """(visible, behind, x, y) for a velocity in cm/s and a view rotation (roll, pitch, yaw)."""
    ship.debug_set_linear_velocity(unreal.Vector(*velocity))
    state = unreal.SpaceFlightHud.make_state(ship, 1)
    state = unreal.SpaceFlightHud.apply_view(state, ship, unreal.Rotator(roll=view[0], pitch=view[1], yaw=view[2]), fov)
    return state.velocity_visible, state.velocity_behind, state.velocity_marker.x, state.velocity_marker.y


try:
    visible, _, _, _ = marker((MIN_SPEED * 0.5, 0.0, 0.0))
    check("below walking pace there is no marker", not visible)
    visible, _, _, _ = marker((MIN_SPEED * 2.0, 0.0, 0.0))
    check("moving, there is one", visible)

    visible, behind, x, y = marker((10000.0, 0.0, 0.0))
    check("straight down the view's axis: dead centre", visible and not behind and abs(x) < 0.5 and abs(y) < 0.5,
          "(%.1f, %.1f)" % (x, y))

    # The view turned right by 10 degrees: the flight path is now 10 degrees to its left.
    visible, behind, x, y = marker((10000.0, 0.0, 0.0), view=(0.0, 0.0, 10.0))
    want = math.tan(math.radians(10.0)) * focal(90.0)
    check("view turned right puts the marker left of centre", x < -1.0, "x %.1f" % x)
    check("and as far off as the focal length says", abs(abs(x) - want) < 2.0, "%.1f of %.1f" % (abs(x), want))
    check("with no height to it", abs(y) < 0.5, "y %.1f" % y)

    # Nose up 10 degrees with the flight path level: the marker sits below the middle (screen Y grows down).
    visible, behind, x, y = marker((10000.0, 0.0, 0.0), view=(0.0, 10.0, 0.0))
    check("nose up puts the marker below centre", y > 1.0, "y %.1f" % y)
    check("and as far off as the focal length says", abs(y - want) < 2.0, "%.1f of %.1f" % (y, want))

    # A wide angle would throw it off screen; it is pinned to the circle instead.
    visible, behind, x, y = marker((10000.0, 0.0, 0.0), view=(0.0, 0.0, 60.0))
    radius = math.sqrt(x * x + y * y)
    check("a wide angle is pinned to the circle", abs(radius - MARKER_RADIUS) < 1.0, "%.1f of %.1f" % (radius, MARKER_RADIUS))

    # Flying backwards: no projection exists, so it is drawn hollow and pinned.
    visible, behind, x, y = marker((-10000.0, 0.0, 0.0))
    radius = math.sqrt(x * x + y * y)
    check("flying backwards is marked as behind", visible and behind)
    check("and pinned to the circle", abs(radius - MARKER_RADIUS) < 1.0, "%.1f" % radius)
    check("straight behind parks it at the bottom rather than flickering", y > MARKER_RADIUS - 1.0,
          "(%.1f, %.1f)" % (x, y))

    # Drifting right while pointing forward: the marker goes right, the nose reticle stays put.
    visible, behind, x, y = marker((10000.0, 10000.0, 0.0))
    check("drifting right puts the marker right of the nose", visible and not behind and x > 1.0, "x %.1f" % x)
    check("45 degrees of drift is one focal length across", abs(x - focal(90.0)) < 3.0 or abs(x - MARKER_RADIUS) < 1.0,
          "x %.1f (focal %.1f, pinned %.1f)" % (x, focal(90.0), MARKER_RADIUS))
finally:
    eas.destroy_actor(ship)

hud = unreal.new_object(unreal.SpaceFlightHud)
hud.debug_initialize()
check("the HUD has the marker", "Velocity" in set(hud.debug_get_widget_names()))

shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "velocity_vector.json"), encoding="utf-8"))["shots"]
known = {"name", "camera", "hud", "altitude_m", "facing", "speed_ms", "drift", "mode", "limiter", "coupled", "gsafe",
         "comstab", "boost", "afterburner", "stick", "settle", "cockpit_eye", "hide_hull", "hide_canopy", "gear",
         "lower_gear", "precision", "chase_yaw", "chase_pitch", "chase_zoom", "console", "_comment"}
unknown = sorted({k for shot in shots for k in shot} - known)
check("the marker's shot list uses only fields the runner reads", not unknown and len(shots) >= 4, str(unknown))
check("and it shows the marker ahead, off to the side and behind",
      any(shot.get("drift", [0, 0, 0])[0] > 0 for shot in shots)
      and any(shot.get("drift", [0, 0, 0])[1] != 0 for shot in shots)
      and any(shot.get("drift", [0, 0, 0])[0] < 0 for shot in shots))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
