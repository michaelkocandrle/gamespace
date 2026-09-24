"""Checks a ship imported by Tools/Assets/import_ship.py, in a fresh editor process (so only what
was saved counts).

    $env:GAMESPACE_SHIP_MANIFEST = "...\\<Ship>_manifest.json"   (optional, default: the only manifest)
    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_ship_import.py

Prints "SHIPTEST PASS" / "SHIPTEST FAIL" lines and a summary. Never saves. With no manifest under
ArtSource/Ships/*/Export/ (no modelled ship yet) it prints a SKIP line and passes.
"""

import os
import sys

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "Tools", "Assets"))
import glob  # noqa: E402

os.environ["GAMESPACE_SHIP_DRY_RUN"] = "1"
HAVE_SHIP = bool(os.environ.get("GAMESPACE_SHIP_MANIFEST")
                 or glob.glob(os.path.join(REPO, "ArtSource", "Ships", "*", "Export", "*_manifest.json")))
if HAVE_SHIP:
    import import_ship  # noqa: E402  (dry run on import: prints the plan, changes nothing)

failures = []


def log(msg):
    unreal.log("SHIPTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def main():
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
            want_parent = {"hull": "M_Ship_Hull", "pbr": "M_Ship_PBR", "glass": "M_Ship_Glass", "screen": "M_Ship_Screen",
                           "layered": "M_Ship_Layered", "meshdecal": "M_Ship_MeshDecal",
                           "meshdecal_paint": "M_Ship_MeshDecalPaint", "decal": "M_Ship_Decal"}[spec["master"]]
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
        # The micro-detail layer (20. 9. 2026): the generated tiling textures are in the game and the hull uses them.
        detail = [unreal.EditorAssetLibrary.load_asset("/Game/Ships/Shared/Textures/" + name)
                  for name in ("T_Ship_Detail_N", "T_Ship_Detail_Grunge")]
        check("the detail textures are imported (Tools/Assets/generate_detail_textures.py)", all(detail),
              "%s" % [d.get_name() if d else None for d in detail])
        check("the detail normal is a normal map with its green channel flipped", detail[0] is not None
              and detail[0].get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_NORMALMAP
              and detail[0].get_editor_property("flip_green_channel"))
        # Occlusion (20. 9. 2026): its own baked map, because the ORM's red channel is the emissive mask.
        ao_map = unreal.EditorAssetLibrary.load_asset("/Game/Ships/%s/Textures/T_Ship_%s_AO" % (plan["ship"], plan["ship"]))
        check("the baked AO map is imported (Tools/Blender/bake_ship_ao.py)", ao_map is not None)
        if ao_map:
            check("the AO map is masks, not sRGB",
                  ao_map.get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_MASKS
                  and not ao_map.get_editor_property("srgb"))
        hull_mi = unreal.EditorAssetLibrary.load_asset("/Game/Ships/%s/Materials/MI_Ship_%s_Hull" % (plan["ship"], plan["ship"]))
        if hull_mi:
            strength = MEL.get_material_instance_scalar_parameter_value(hull_mi, "DetailNormalStrength")
            tile = MEL.get_material_instance_scalar_parameter_value(hull_mi, "DetailTileCm")
            wear = MEL.get_material_instance_scalar_parameter_value(hull_mi, "DetailRoughVariation")
            check("the hull wears the detail layer (strength > 0, tile 5..60 cm, wear <= 0.3)",
                  strength > 0.0 and 5.0 <= tile <= 60.0 and 0.0 <= wear <= 0.3, "strength %.2f, tile %.0f cm, wear %.2f" % (strength, tile, wear))
            check("the hull's AO map is the baked one, not the white default",
                  MEL.get_material_instance_texture_parameter_value(hull_mi, "AOMap") == ao_map, "%s" % ao_map)
            cavity = MEL.get_material_instance_scalar_parameter_value(hull_mi, "CavityStrength")
            wear_amount = MEL.get_material_instance_scalar_parameter_value(hull_mi, "WearAmount")
            # Above ~0.3 the wear reads as dirt rather than worn paint (Tools/Shots/hull_zones.json).
            check("the hull has cavity and a restrained amount of wear",
                  cavity > 0.0 and 0.0 <= wear_amount <= 0.3, "cavity %.2f, wear %.2f" % (cavity, wear_amount))
            panels = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Shared/Textures/T_Ship_Panels")
            check("the panel seam sheet is imported (Tools/Assets/generate_panel_lines.py)", panels is not None)
            panel_strength = MEL.get_material_instance_scalar_parameter_value(hull_mi, "PanelStrength")
            panel_tile = MEL.get_material_instance_scalar_parameter_value(hull_mi, "PanelTileCm")
            # Above ~0.8 the seams run over greebles and curves and read as an overlay; a sheet under a
            # metre makes plates too small to be plating (Tools/Shots/hull_panels.json).
            wanted = next((m.get("panel_strength") for m in (setup or {}).get("materials", {}).values()
                           if isinstance(m, dict) and "panel_strength" in m), None)
            if wanted == 0.0:
                # A ship with modelled panel lines (the Wayfarer's repainted AI hull) turns the procedural sheets off:
                # drawn over the modelled seams they doubled up and read as dirt (author 24. 9. 2026).
                check("the hull's own panels: procedural plating off, as its setup says", panel_strength == 0.0,
                      "strength %.2f" % panel_strength)
            else:
                check("the hull's plating is there and restrained",
                      0.0 < panel_strength <= 0.8 and 100.0 <= panel_tile <= 500.0,
                      "strength %.2f, sheet %.0f cm" % (panel_strength, panel_tile))
            scorch = MEL.get_material_instance_scalar_parameter_value(hull_mi, "ScorchAmount")
            start = MEL.get_material_instance_scalar_parameter_value(hull_mi, "ScorchStartCm")
            end = MEL.get_material_instance_scalar_parameter_value(hull_mi, "ScorchEndCm")
            # Both behind the origin and end behind start, or the mask runs the wrong way and burns the
            # nose instead of the tail. Above ~0.8 the back of the ship reads as a shadow, not as soot.
            check("the scorch is behind the ship and restrained",
                  0.0 <= scorch <= 0.8 and end < start <= 0.0,
                  "amount %.2f, %.0f cm -> %.0f cm" % (scorch, start, end))

    # --- nothing left over from an earlier model -------------------------------------------------
    root = "/Game/Ships/%s" % plan["ship"]
    expected_assets = ({m["asset_path"] for m in plan["meshes"]}
                       | {"%s/Materials/%s" % (root, n) for n in plan["materials"]}
                       | {"%s/Materials/MI_Ship_%s_Decal_%s" % (root, plan["ship"], d["name"]) for d in plan["decals"]})
    leftovers = [p.split(".")[0] for f in ("/Meshes", "/Materials") for p in unreal.EditorAssetLibrary.list_assets(root + f, recursive=False)
                 if p.split(".")[0] not in expected_assets]
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

    # --- markings ------------------------------------------------------------------------------
    # A decal only reads when its component's X points AWAY from the surface: the projection runs along
    # -X (Tools/Shots/hull_decals.json, 20. 9. 2026). Backwards it paints thin air and smears.
    for decal in plan["decals"]:
        mi = unreal.EditorAssetLibrary.load_asset(
            "/Game/Ships/%s/Materials/MI_Ship_%s_Decal_%s" % (plan["ship"], plan["ship"], decal["name"]))
        check("decal %s has its material" % decal["name"], mi is not None)
        if mi:
            texture = MEL.get_material_instance_texture_parameter_value(mi, "DecalTexture")
            check("decal %s wears %s" % (decal["name"], decal["texture"]),
                  texture is not None and texture.get_name() == decal["texture"],
                  str(texture.get_name() if texture else None))
        size = decal["size"]
        check("decal %s has a depth and a plane" % decal["name"],
              len(size) == 3 and size[0] > 0.0 and size[1] > 0.0 and size[2] > 0.0, str(size))
    if plan["decals"]:
        names = {d["name"] for d in plan["decals"]}
        check("the ship carries markings on both flanks",
              {"Registration_L", "Registration_R"} <= names, ", ".join(sorted(names)))

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


if HAVE_SHIP:
    main()
else:
    log("SKIP the imported ship's meshes, materials, Blueprint and level (no ship model yet - new ship in design)")

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
