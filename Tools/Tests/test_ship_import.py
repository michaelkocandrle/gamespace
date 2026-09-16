"""Checks a ship imported by Tools/Assets/import_ship.py, in a fresh editor process (so only what
was saved counts).

    $env:GAMESPACE_SHIP_MANIFEST = "...\\Vanguard_manifest.json"   (optional, default: the only manifest)
    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_ship_import.py

Prints "SHIPTEST PASS" / "SHIPTEST FAIL" lines and a summary. Never saves.
"""

import os
import sys

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "Tools", "Assets"))
os.environ["GAMESPACE_SHIP_DRY_RUN"] = "1"
import import_ship  # noqa: E402  (dry run on import: prints the plan, changes nothing)

failures = []


def log(msg):
    unreal.log("SHIPTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


manifest_path = import_ship.find_manifest(os.environ.get("GAMESPACE_SHIP_MANIFEST"))
manifest, _ = import_ship.gx.load_and_validate_manifest(manifest_path)
plan = import_ship.build_plan(manifest, os.path.dirname(manifest_path))
s = manifest["suggested_pawn_settings"]

# --- meshes ------------------------------------------------------------------------------
for m in plan["meshes"]:
    mesh = unreal.EditorAssetLibrary.load_asset(m["asset_path"])
    check("%s exists" % m["name"], isinstance(mesh, unreal.StaticMesh))
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    size = import_ship.mesh_size_cm(mesh)
    check("%s size" % m["name"], import_ship.compare_size(size, m["expected_size_cm"]) == "ok",
          "%s cm, manifest %s" % ([round(x, 1) for x in size], m["expected_size_cm"]))
    nanite = mesh.get_editor_property("nanite_settings").get_editor_property("enabled")
    check("%s Nanite %s" % (m["name"], "on" if m["nanite"] else "off"), nanite == m["nanite"])
    agg = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    hulls = len(agg.get_editor_property("convex_elems"))
    check("%s collision hulls" % m["name"], hulls == m["collision_hulls"], "%d" % hulls)
    bad = []
    for name, target in m["sockets"].items():
        key = import_ship.socket_key(name)
        sock = mesh.find_socket(key)
        if sock is None:
            bad.append("%s missing" % key)
            continue
        loc = sock.get_editor_property("relative_location")
        scale = sock.get_editor_property("relative_scale")
        if max(abs(loc.x - target[0]), abs(loc.y - target[1]), abs(loc.z - target[2])) > 1.0:
            bad.append("%s at (%.0f, %.0f, %.0f)" % (key, loc.x, loc.y, loc.z))
        if max(abs(scale.x - 1), abs(scale.y - 1), abs(scale.z - 1)) > 1e-3:
            bad.append("%s scale %.3g" % (key, scale.x))
    check("%s sockets saved at manifest positions, scale 1" % m["name"], not bad, "; ".join(bad) or "%d sockets" % len(m["sockets"]))

# --- blueprint: spawn it, so inherited component overrides are what the game would see ------
bp_class = unreal.EditorAssetLibrary.load_blueprint_class(plan["blueprint"])
check("Blueprint class loads", bp_class is not None)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ship = eas.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 900000)) if bp_class else None
if ship:
    try:
        box = ship.get_editor_property("hull_collision")
        extent = box.get_unscaled_box_extent()
        want = s["HullCollision_BoxExtent_cm"]
        check("root box extent", max(abs(extent.x - want[0]), abs(extent.y - want[1]), abs(extent.z - want[2])) < 0.5,
              "(%.1f, %.1f, %.1f)" % (extent.x, extent.y, extent.z))
        hull = ship.get_editor_property("hull")
        mesh = hull.get_editor_property("static_mesh")
        check("hull mesh", mesh is not None and mesh.get_name() == "SM_Ship_%s" % plan["ship"], str(mesh.get_name() if mesh else None))
        sc = hull.get_editor_property("relative_scale3d")
        check("hull scale 1", abs(sc.x - 1) + abs(sc.y - 1) + abs(sc.z - 1) < 1e-4, "(%.2f, %.2f, %.2f)" % (sc.x, sc.y, sc.z))
        boom = ship.get_editor_property("camera_boom")
        check("camera arm", abs(boom.get_editor_property("target_arm_length") - s["CameraBoom_TargetArmLength_cm"]) < 0.5,
              "%.0f cm" % boom.get_editor_property("target_arm_length"))
        cockpit = ship.get_editor_property("cockpit_camera").get_editor_property("relative_location")
        want = s["CockpitCamera_location_ue_cm"]
        check("cockpit camera at SOCKET_Cockpit", max(abs(cockpit.x - want[0]), abs(cockpit.y - want[1]), abs(cockpit.z - want[2])) < 0.5,
              "(%.0f, %.0f, %.0f)" % (cockpit.x, cockpit.y, cockpit.z))
        for prop, key in (("landing_footprint_radius_cm", "LandingFootprintRadiusCm"), ("landing_max_gap_cm", "LandingMaxGapCm"),
                          ("ground_contact_tolerance_cm", "GroundContactToleranceCm"), ("heat_shake_cm", "HeatShakeCm")):
            check(prop, abs(ship.get_editor_property(prop) - s[key]) < 0.05, "%.1f" % ship.get_editor_property(prop))
        meshes = [c for c in ship.get_components_by_class(unreal.StaticMeshComponent)]
        names = {c.get_name(): c for c in meshes}
        extras = [e["component"] for e in plan["extra_components"]]
        for extra in extras:
            comp = next((c for n, c in names.items() if n.startswith(extra)), None)
            ok = comp is not None and comp.get_editor_property("static_mesh") is not None
            check("component %s with its mesh" % extra, ok, ", ".join(sorted(names)))
    finally:
        eas.destroy_actor(ship)

# --- level ---------------------------------------------------------------------------------
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(import_ship.LEVEL)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
mode = world.get_world_settings().get_editor_property("default_game_mode")
check("TestSpace game mode override", mode is not None and mode.get_name().startswith("BP_SpaceGameMode"), str(mode.get_name() if mode else None))
if mode:
    pawn = unreal.get_default_object(mode).get_editor_property("default_pawn_class")
    check("game mode spawns the ship", pawn is not None and pawn.get_name().startswith("BP_Ship_%s" % plan["ship"]), str(pawn.get_name() if pawn else None))
planet = next((a for a in eas.get_all_level_actors() if a.get_actor_label() == import_ship.PLANET_LABEL), None)
for prop, value in plan["planet_settings"]:
    check("planet %s" % prop, planet is not None and abs(planet.get_editor_property(prop) - value) < 0.01,
          "%.1f" % planet.get_editor_property(prop) if planet else "no planet")

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
