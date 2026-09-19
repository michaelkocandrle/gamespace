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
setup = import_ship.load_setup(import_ship.setup_path(os.path.dirname(manifest_path), manifest["ship"]))
plan = import_ship.build_plan(manifest, os.path.dirname(manifest_path), setup)
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
    if plan["materials"]:
        unassigned = []
        for slot in mesh.get_editor_property("static_materials"):
            mat = slot.get_editor_property("material_interface")
            if not isinstance(mat, unreal.MaterialInstanceConstant) or not mat.get_path_name().startswith("/Game/Ships/"):
                unassigned.append("%s=%s" % (slot.get_editor_property("material_slot_name"), mat.get_name() if mat else None))
        check("%s every slot has a ship material instance" % m["name"], not unassigned, "; ".join(unassigned))

# --- materials -----------------------------------------------------------------------------
if plan["materials"]:
    MEL = unreal.MaterialEditingLibrary
    folder = "/Game/Ships/%s/Materials" % plan["ship"]
    for name, spec in sorted(plan["materials"].items()):
        mi = unreal.EditorAssetLibrary.load_asset("%s/%s" % (folder, name))
        parent = mi.get_editor_property("parent") if mi else None
        want_parent = {"hull": "M_Ship_Hull", "pbr": "M_Ship_PBR", "glass": "M_Ship_Glass", "screen": "M_Ship_Screen"}[spec["master"]]
        check("%s parent %s" % (name, want_parent), parent is not None and parent.get_name() == want_parent,
              parent.get_name() if parent else "missing")
        for key, param in (("base_color", "BaseColorMap"), ("orm", "ORMMap"), ("normal", "NormalMap")):
            if mi and key in (spec.get("textures") or {}):
                texture = MEL.get_material_instance_texture_parameter_value(mi, param)
                want = "T_" + os.path.splitext(os.path.basename(spec["textures"][key]))[0].replace("T_", "", 1)
                ok = texture is not None and texture.get_name() == want
                if ok and key == "normal":
                    ok = (texture.get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_NORMALMAP
                          and not texture.get_editor_property("srgb") and texture.get_editor_property("flip_green_channel"))
                elif ok and key == "orm":
                    ok = (texture.get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_MASKS
                          and not texture.get_editor_property("srgb"))
                elif ok:
                    ok = texture.get_editor_property("srgb")
                check("%s %s = %s, set up for its role" % (name, param, want), ok, texture.get_name() if texture else "none")
        if mi and "emissive_strength" in spec:
            got = MEL.get_material_instance_scalar_parameter_value(mi, "EmissiveStrength")
            check("%s glows" % name, abs(got - spec["emissive_strength"]) < 1e-3 and got > 1.0, "%.1f" % got)
    glass = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Shared/Materials/M_Ship_Glass")
    check("M_Ship_Glass is translucent", glass is not None and glass.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_TRANSLUCENT)
    for master in ("M_Ship_Hull", "M_Ship_PBR"):
        asset = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Shared/Materials/" + master)
        check("%s used with Nanite" % master, asset is not None and asset.get_editor_property("used_with_nanite"))

# --- nothing left over from an earlier model -------------------------------------------------
root = "/Game/Ships/%s" % plan["ship"]
leftovers = [p.split(".")[0] for f in ("/Meshes", "/Materials") for p in unreal.EditorAssetLibrary.list_assets(root + f, recursive=False)
             if p.split(".")[0] not in {m["asset_path"] for m in plan["meshes"]} | {"%s/Materials/%s" % (root, n) for n in plan["materials"]}]
check("no meshes or material instances of an earlier model left", not leftovers, ", ".join(leftovers))

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
        # Effective values: manifest first, setup file after it (later entries win).
        effective = {}
        for component, prop, value in plan["pawn_settings"]:
            if prop not in ("box_extent", "static_mesh", "socket_offset_z", "relative_scale3d") and component != "hull":
                effective[(component, prop)] = value
        for (component, prop), want in sorted(effective.items(), key=lambda kv: (kv[0][0] or "", kv[0][1])):
            target = ship if component is None else ship.get_editor_property(component)
            got = target.get_editor_property(prop)
            if isinstance(want, bool):
                ok, shown = got == want, str(got)
            elif isinstance(want, (list, tuple)):
                ok = max(abs(got.x - want[0]), abs(got.y - want[1]), abs(got.z - want[2])) < 0.5
                shown = "(%.0f, %.0f, %.0f)" % (got.x, got.y, got.z)
            else:
                ok, shown = abs(got - want) < max(0.05, abs(want) * 1e-4), "%.4g" % got
            check("%s.%s = %s" % (component or "pawn", prop, want), ok, shown)
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
