"""Headless checks for the quantum tunnel (USpaceSpeedTunnelComponent).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_speed_tunnel.py

In a quantum jump (SC-4) the tunnel is the look of speed: fog, a few streaks radiating from the
flight path, beams, a glow on the vanishing point and green flares. It shows only in a jump (the
pawn's quantum blend); whether that works is in test_quantum_sc4.py and the quantum shots. This
checks the rules that keep it from looking wrong: streaks that never jump further than their own
length in a frame (strobing), walls the ship fits inside, every material parameter in place.
Nothing is saved. Prints "TUNNELTEST PASS" / "TUNNELTEST FAIL" lines and a summary.
"""

import json
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
failures = []


def log(msg):
    unreal.log("TUNNELTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.new_level("/Temp/TunnelTest")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# The real ship (its hull decides whether it fits inside the nearest wall), the bare pawn if it is missing.
ship_class = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Ships/Vanguard/Blueprints/BP_Ship_Vanguard") or unreal.SpaceshipPawn
ship = eas.spawn_actor_from_class(ship_class, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))

try:
    tunnel = ship.get_editor_property("speed_tunnel")
    dust = ship.get_editor_property("space_dust")
    check("the ship has a speed tunnel", tunnel is not None)

    nav_top = ship.get_editor_property("nav_max_speed")
    cruise_top = ship.get_editor_property("quantum_max_speed_km_s") * 100000.0
    check("the dust is gone before quantum speeds would turn it to flicker",
          dust.get_editor_property("fade_out_end_speed") <= 200000.0)

    # Strobing: at 60 FPS a streak must be longer than what it scrolls in a frame, with room to spare.
    worst = min(tunnel.compute_streak_length(v) / max(tunnel.compute_apparent_speed(v) / 60.0, 1.0)
                for v in range(int(nav_top), int(cruise_top) + 1, 10000))
    check("a streak is at least twice what it scrolls in a 60 FPS frame", worst >= 2.0, "%.2f" % worst)
    check("streaks never run into the next one in their lane",
          tunnel.compute_streak_length(cruise_top * 10.0) <= 0.6 * tunnel.get_editor_property("period_cm") + 0.5)

    # The hull sparks (blue in a jump, a few white in flight) are born on the hull's collision.
    sparks = ship.get_editor_property("hull_sparks")
    check("the ship has hull sparks", sparks is not None)
    if sparks is not None:
        count, from_collision = sparks.debug_get_spawn_point_count()
        check("and finds points to pour them from on the Vanguard's hull (its collision shapes, not a box round it)",
              count >= 32 and from_collision, "%d points, collision %s" % (count, from_collision))
        check("a jump has many sparks, normal flight few", sparks.get_editor_property("quantum_count") >= 5 * sparks.get_editor_property("flight_count") > 0)
        spark_material = unreal.load_asset("/Game/Environments/Space/M_HullSpark")
        check("the sparks have their own material", spark_material is not None)
        if spark_material is not None:
            check("additive, on instances, two sided (the ribbons face the camera from either side)",
                  spark_material.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_ADDITIVE
                  and spark_material.get_editor_property("used_with_instanced_static_meshes")
                  and spark_material.get_editor_property("two_sided"))
            check("and NOT responsive AA (it drew black scribbles over the lit walls)",
                  not spark_material.get_editor_property("enable_responsive_aa"))
    check("the dust is only a hint (a few hundred specks)", dust.get_editor_property("particle_count") <= 400)

    layers = tunnel.get_editor_property("layers")
    radii = [layer.get_editor_property("radius_cm") for layer in layers]
    check("at least two walls, nearest first", len(radii) >= 2 and radii == sorted(radii), str(radii))
    origin, box = ship.get_actor_bounds(True)
    ship_half = max(box.x, box.y, box.z)
    check("the ship fits inside the nearest wall", bool(radii) and radii[0] > ship_half * 1.5,
          "wall %.0f cm, ship half size %.0f cm" % (radii[0] if radii else 0, ship_half))
    check("the tunnel reaches well past the widest wall",
          bool(radii) and tunnel.get_editor_property("half_length_cm") > 5.0 * radii[-1])
finally:
    eas.destroy_actor(ship)

material = unreal.load_asset("/Game/Environments/Space/M_SpeedTunnel")
check("the tunnel material exists", material is not None)
if material:
    check("additive and two sided (the camera is inside it)",
          material.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_ADDITIVE and material.get_editor_property("two_sided"))
    mel = unreal.MaterialEditingLibrary
    params = set(str(p) for p in mel.get_scalar_parameter_names(material))
    params |= set(str(p) for p in mel.get_vector_parameter_names(material))
    wanted = {"TunnelDirection", "TunnelRight", "TunnelUp", "TunnelAlpha", "TunnelHalfLengthCm", "TunnelOffsetCm",
              "TunnelPeriodCm", "StreakLengthCm", "StreakWidthCm", "StreakColorSpread", "StreakFill", "StreakColor", "StreakBrightness",
              "BeamColor", "BeamBrightness", "BeamCount", "BeamSharpness", "GlowColor", "GlowBrightness",
              "HazeColor", "FlareColor", "FlareAlpha", "FlareSeed"}
    check("with every parameter the component sets", wanted <= params, str(sorted(wanted - params)))

shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "tunnel_tune.json"), encoding="utf-8"))["shots"]
known = {"name", "camera", "hud", "altitude_m", "facing", "speed_ms", "drift", "mode", "limiter", "coupled", "gsafe",
         "comstab", "boost", "afterburner", "stick", "settle", "cockpit_eye", "hide_hull", "hide_canopy", "gear",
         "lower_gear", "precision", "chase_yaw", "chase_pitch", "chase_zoom", "console", "quantum", "quantum_progress",
         "quantum_ready", "_comment"}
unknown = sorted({k for shot in shots for k in shot} - known)
check("the tunnel's shot list uses only fields the runner reads", not unknown, str(unknown))
check("and shows a jump from outside and from the cockpit",
      any(s.get("quantum") and s["camera"] == "chase" for s in shots)
      and any(s.get("quantum") and s["camera"] == "cockpit" for s in shots))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
