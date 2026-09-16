"""Imports a ship exported by Tools/Blender/gamespace_ship_export.py and sets up its Blueprint.

Editor closed:

    $env:GAMESPACE_SHIP_MANIFEST = "C:\\gamespace\\gamespace\\ArtSource\\Ships\\Vanguard\\Export\\Vanguard_manifest.json"
    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\import_ship.py

Without GAMESPACE_SHIP_MANIFEST the script uses the only *_manifest.json under
ArtSource/Ships/*/Export/. Optional switches (environment variables, "0" turns them off):

    GAMESPACE_SHIP_DRY_RUN=1          validate and print the plan, touch nothing
    GAMESPACE_SHIP_APPLY_PLANET=0     leave Planet_Veyra's collision settings alone
    GAMESPACE_SHIP_SET_GAME_MODE=0    do not make TestSpace spawn the new ship

Dry run without Unreal (plain Python, any time):

    python Tools/Assets/import_ship.py ArtSource/Ships/Vanguard/Export/Vanguard_manifest.json

Steps:
  1. Validate the manifest (gamespace_ship_export.validate_manifest). Errors stop everything.
  2. Import every LOD0 FBX into /Game/Ships/<Ship>/Meshes with the legacy FBX importer:
     no generated collision (UCX hulls), absolute vertex transform, no materials/textures,
     Nanite on except for glass parts.
  3. Check each mesh against the manifest: size (retries once with Convert Scene Unit if it
     came in 100x small), orientation, collision hull count, material slots, sockets (location
     and scale fixed to the manifest values if the importer changed them).
  4. Create or update /Game/Ships/<Ship>/Blueprints/BP_Ship_<Ship> (child of ASpaceshipPawn)
     with the manifest's suggested_pawn_settings: root box, hull mesh and offset, camera boom,
     cockpit camera, landing and heat values; glass parts become extra mesh components.
  5. Optionally: planet collision settings in TestSpace, and a BP_SpaceGameMode that spawns
     the new ship as TestSpace's game mode override.
  6. Write <Ship>_import_report.json next to the manifest.

Nothing is saved when a step fails before the Blueprint stage; meshes that did import stay.
Reduced LODs (_LOD1...) are not imported: Nanite meshes do not use them. Import them in the
Static Mesh Editor if a part runs without Nanite.
"""

import glob
import json
import os
import sys

try:
    import unreal
except ImportError:
    unreal = None

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "Tools", "Blender"))
import gamespace_ship_export as gx  # noqa: E402  (bpy-free core)

LEVEL = "/Game/Maps/TestSpace"
PLANET_LABEL = "Planet_Veyra"
GAME_MODE_PATH = "/Game/Blueprints/BP_SpaceGameMode"

# Parts whose materials are see-through: Nanite does not render translucency.
GLASS_HINTS = ("canopy", "glass", "window", "visor")

SIZE_TOLERANCE = 0.03      # 3 % between imported bounds and the manifest
SOCKET_TOLERANCE_CM = 1.0


# =========================================================================================
# Plan: pure Python, testable without Unreal
# =========================================================================================

def is_glass_part(mesh_name, mesh_entry):
    """A see-through part: named like one, or made of nothing but glass materials. A hull with a few
    small glass bits (sensor windows) stays Nanite; those bits need an opaque glass look."""
    if any(h in mesh_name.lower() for h in GLASS_HINTS):
        return True
    materials = mesh_entry.get("materials") or []
    return bool(materials) and all(any(h in m.lower() for h in GLASS_HINTS) for m in materials)


def find_manifest(explicit=None):
    if explicit:
        return os.path.abspath(explicit)
    found = sorted(glob.glob(os.path.join(REPO, "ArtSource", "Ships", "*", "Export", "*_manifest.json")))
    if len(found) != 1:
        raise RuntimeError("Set GAMESPACE_SHIP_MANIFEST: found %d manifests under ArtSource/Ships/*/Export/ (%s)"
                           % (len(found), ", ".join(found) or "none"))
    return found[0]


def build_plan(manifest, manifest_dir):
    """Everything the import will do, as data. Assumes validate_manifest passed."""
    ship = manifest["ship"]
    root = "/Game/Ships/%s" % ship
    s = manifest["suggested_pawn_settings"]
    size = manifest["expected_ue_size_cm"]

    meshes = []
    for entry in manifest["files"]:
        name = entry["objects"][0]
        info = manifest["meshes"][name]
        if info["lod"] != 0:
            continue
        glass = is_glass_part(name, info)
        meshes.append({
            "name": name,
            "fbx": os.path.join(manifest_dir, entry["fbx"]),
            "destination": root + "/Meshes",
            "asset_path": "%s/Meshes/%s" % (root, name),
            "part": info.get("part"),
            "nanite": not glass,
            "materials": info["materials"],
            "collision_hulls": sum(1 for h in manifest["collision"].values() if h["mesh"] == name),
            "sockets": {sock_name: sock["location_ue_cm"] for sock_name, sock in manifest["sockets"].items()
                        if sock["parent"] == name},
            "expected_size_cm": [round((info["bounds_m"][1][i] - info["bounds_m"][0][i]) * 100.0, 1) for i in range(3)],
        })
    main = "SM_Ship_%s" % ship
    meshes.sort(key=lambda m: (m["name"] != main, m["name"]))

    # (component property name on ASpaceshipPawn or None for the pawn itself, property, value)
    pawn = [
        ("hull_collision", "box_extent", s["HullCollision_BoxExtent_cm"]),
        ("hull", "static_mesh", "%s/Meshes/%s" % (root, main)),
        ("hull", "relative_scale3d", [1.0, 1.0, 1.0]),
        ("hull", "relative_location", s["Hull_RelativeLocation_cm"]),
        ("camera_boom", "target_arm_length", s["CameraBoom_TargetArmLength_cm"]),
        ("camera_boom", "socket_offset_z", s["CameraBoom_SocketOffset_Z_cm"]),
        ("camera_boom", "probe_size", s["CameraBoom_ProbeSize_cm"]),
        ("camera_boom", "camera_lag_max_distance", s["CameraBoom_CameraLagMaxDistance_cm"]),
        (None, "landing_footprint_radius_cm", s["LandingFootprintRadiusCm"]),
        (None, "landing_max_gap_cm", s["LandingMaxGapCm"]),
        (None, "ground_contact_tolerance_cm", s["GroundContactToleranceCm"]),
        (None, "heat_shake_cm", s["HeatShakeCm"]),
    ]
    if s["CockpitCamera_location_ue_cm"] is not None:
        pawn.append(("cockpit_camera", "relative_location", s["CockpitCamera_location_ue_cm"]))

    extra_components = [{"component": m["part"] or m["name"], "mesh": m["asset_path"],
                         "relative_location": s["Hull_RelativeLocation_cm"]}
                        for m in meshes if m["name"] != main]

    return {
        "ship": ship,
        "meshes": meshes,
        "blueprint": "%s/Blueprints/BP_Ship_%s" % (root, ship),
        "pawn_settings": pawn,
        "extra_components": extra_components,
        "planet_settings": [("collision_warmup_reach_m", s["Planet_CollisionWarmupReachM"]),
                            ("collision_min_radius_m", s["Planet_CollisionMinRadiusM"])],
        "game_mode": GAME_MODE_PATH,
        "expected_ship_size_cm": size,
        "skipped_lods": [e["fbx"] for e in manifest["files"] if manifest["meshes"][e["objects"][0]]["lod"] > 0],
    }


def format_plan(plan):
    lines = ["Ship %s" % plan["ship"]]
    for m in plan["meshes"]:
        lines.append("  import %s -> %s  (Nanite %s, %d collision hulls, sockets %s, size %s cm)" % (
            os.path.basename(m["fbx"]), m["asset_path"], "on" if m["nanite"] else "off", m["collision_hulls"],
            ", ".join(m["sockets"]) or "-", m["expected_size_cm"]))
    lines.append("  blueprint %s" % plan["blueprint"])
    for component, prop, value in plan["pawn_settings"]:
        lines.append("    %s.%s = %s" % (component or "(pawn)", prop, value))
    for extra in plan["extra_components"]:
        lines.append("    + component %s with %s" % (extra["component"], extra["mesh"]))
    for prop, value in plan["planet_settings"]:
        lines.append("  %s.%s = %s" % (PLANET_LABEL, prop, value))
    if plan["skipped_lods"]:
        lines.append("  not imported (LODs, Nanite): %s" % ", ".join(plan["skipped_lods"]))
    return "\n".join(lines)


def compare_size(actual_cm, expected_cm):
    """'ok', 'unit' (100x too small: file in metres), 'rotated' (X and Y swapped) or 'wrong'."""
    def close(a, b):
        return all(abs(x - y) <= SIZE_TOLERANCE * max(abs(y), 1.0) for x, y in zip(a, b))
    if close(actual_cm, expected_cm):
        return "ok"
    if close([x * 100.0 for x in actual_cm], expected_cm):
        return "unit"
    if close([actual_cm[1], actual_cm[0], actual_cm[2]], expected_cm):
        return "rotated"
    return "wrong"


def socket_key(name):
    """Unreal drops the SOCKET_ prefix on import; compare without it."""
    return name[len("SOCKET_"):] if name.startswith("SOCKET_") else name


# =========================================================================================
# Unreal
# =========================================================================================

class ImportFailed(RuntimeError):
    pass


def log(msg):
    if unreal:
        unreal.log("import_ship: " + msg)
    else:
        print(msg)


def vec(v):
    return unreal.Vector(float(v[0]), float(v[1]), float(v[2]))


def use_legacy_fbx_importer():
    # The Interchange FBX importer ignores FbxImportUI; the checks after import catch it either way.
    for command in ("Interchange.FeatureFlags.Import.FBX 0", "Interchange.FeatureFlags.Import.FBX.ToLevel 0"):
        unreal.SystemLibrary.execute_console_command(None, command)


def import_fbx(mesh, convert_scene_unit=False):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("automated_import_should_detect_type", False)
    data = ui.get_editor_property("static_mesh_import_data")
    # (property, value, required). Required ones change the result in ways the checks after the
    # import cannot repair; the others are verified or fixed afterwards.
    for prop, value, required in (
        ("combine_meshes", True, True),
        ("auto_generate_collision", False, True),
        ("transform_vertex_to_absolute", True, True),
        ("convert_scene", True, True),
        ("force_front_x_axis", False, True),
        ("convert_scene_unit", convert_scene_unit, True),
        ("import_uniform_scale", 1.0, True),
        ("one_convex_hull_per_ucx", True, False),
        ("import_mesh_lods", False, False),
        ("generate_lightmap_u_vs", False, False),
        ("build_nanite", mesh["nanite"], False),
        ("bake_pivot_in_vertex", False, False),
        ("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS, False),
        ("reorder_material_to_fbx_order", True, False),
    ):
        try:
            data.set_editor_property(prop, value)
        except Exception as error:
            if required:
                raise ImportFailed("FbxStaticMeshImportData.%s: %s" % (prop, error))
            log("warning: FbxStaticMeshImportData.%s not set (%s); checked after import" % (prop, error))
    ui.set_editor_property("static_mesh_import_data", data)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", mesh["fbx"])
    task.set_editor_property("destination_path", mesh["destination"])
    task.set_editor_property("destination_name", mesh["name"])
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", ui)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    static_mesh = unreal.EditorAssetLibrary.load_asset(mesh["asset_path"])
    if not isinstance(static_mesh, unreal.StaticMesh):
        raise ImportFailed("%s did not produce a static mesh at %s (imported: %s)" % (
            mesh["fbx"], mesh["asset_path"], list(task.get_editor_property("imported_object_paths"))))
    return static_mesh


def mesh_size_cm(static_mesh):
    box = static_mesh.get_bounding_box()
    return [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z]


def check_and_fix_mesh(static_mesh, mesh, report):
    notes = report.setdefault(mesh["name"], [])

    # Nanite: set explicitly in case the importer ignored build_nanite.
    settings = static_mesh.get_editor_property("nanite_settings")
    if settings.get_editor_property("enabled") != mesh["nanite"]:
        settings.set_editor_property("enabled", mesh["nanite"])
        static_mesh.set_editor_property("nanite_settings", settings)
        notes.append("Nanite set to %s after import" % mesh["nanite"])

    # Collision: exactly the UCX hulls, nothing generated.
    agg = static_mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    shapes = sum(len(agg.get_editor_property(k)) for k in ("convex_elems", "box_elems", "sphere_elems", "sphyl_elems"))
    if shapes != mesh["collision_hulls"]:
        raise ImportFailed("%s has %d collision shapes, manifest lists %d hulls" % (mesh["name"], shapes, mesh["collision_hulls"]))

    # Material slots, in FBX order.
    slots = [str(m.get_editor_property("material_slot_name")) for m in static_mesh.get_editor_property("static_materials")]
    if sorted(slots) != sorted(mesh["materials"]):
        notes.append("material slots %s differ from Blender %s" % (slots, mesh["materials"]))

    # Sockets: the importer may carry the FBX node scale over; the manifest has the truth. The
    # Sockets array itself is protected from Python in UE 5.8, so look each one up by name.
    wanted = {socket_key(k): v for k, v in mesh["sockets"].items()}
    missing = []
    for key, target in sorted(wanted.items()):
        sock = static_mesh.find_socket(key) or static_mesh.find_socket("SOCKET_" + key)
        if sock is None:
            missing.append(key)
            continue
        loc = sock.get_editor_property("relative_location")
        scale = sock.get_editor_property("relative_scale")
        if max(abs(loc.x - target[0]), abs(loc.y - target[1]), abs(loc.z - target[2])) > SOCKET_TOLERANCE_CM:
            notes.append("socket %s moved from (%.1f, %.1f, %.1f) to manifest %s" % (key, loc.x, loc.y, loc.z, target))
            sock.set_editor_property("relative_location", vec(target))
        if max(abs(scale.x - 1.0), abs(scale.y - 1.0), abs(scale.z - 1.0)) > 1e-3:
            notes.append("socket %s scale (%.3g, %.3g, %.3g) reset to 1" % (key, scale.x, scale.y, scale.z))
            sock.set_editor_property("relative_scale", unreal.Vector(1.0, 1.0, 1.0))
        if str(sock.get_editor_property("socket_name")) != key:
            sock.set_editor_property("socket_name", key)
    if missing:
        raise ImportFailed("%s is missing sockets %s" % (mesh["name"], missing))


def import_all_meshes(plan, report):
    imported = {}
    for mesh in plan["meshes"]:
        static_mesh = import_fbx(mesh)
        verdict = compare_size(mesh_size_cm(static_mesh), mesh["expected_size_cm"])
        if verdict == "unit":
            log("%s came in 100x small; reimporting with Convert Scene Unit" % mesh["name"])
            report.setdefault(mesh["name"], []).append("reimported with convert_scene_unit")
            static_mesh = import_fbx(mesh, convert_scene_unit=True)
            verdict = compare_size(mesh_size_cm(static_mesh), mesh["expected_size_cm"])
        if verdict == "rotated":
            raise ImportFailed("%s is rotated 90 degrees (X and Y swapped): the nose must be along +X in Blender" % mesh["name"])
        if verdict != "ok":
            raise ImportFailed("%s imported at %s cm, manifest says %s cm" % (
                mesh["name"], [round(x, 1) for x in mesh_size_cm(static_mesh)], mesh["expected_size_cm"]))
        check_and_fix_mesh(static_mesh, mesh, report)
        unreal.EditorAssetLibrary.save_loaded_asset(static_mesh, only_if_is_dirty=False)
        imported[mesh["name"]] = static_mesh
        log("imported %s" % mesh["asset_path"])
    return imported


def load_or_create_blueprint(path, parent_class):
    existing = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if existing:
        return existing
    folder, name = path.rsplit("/", 1)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Blueprint, factory)
    if not blueprint:
        raise ImportFailed("could not create %s" % path)
    return blueprint


def blueprint_default_object(blueprint):
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    generated = unreal.EditorAssetLibrary.load_blueprint_class(blueprint.get_path_name().split(".")[0])
    return unreal.get_default_object(generated)


def apply_pawn_settings(plan, report):
    blueprint = load_or_create_blueprint(plan["blueprint"], unreal.SpaceshipPawn)
    # Compile first so the default object exists; the native components' overrides set on it are
    # saved with the Blueprint, exactly like edits in its Details panel.
    pawn = blueprint_default_object(blueprint)
    applied = []
    for component_name, prop, value in plan["pawn_settings"]:
        target = pawn if component_name is None else pawn.get_editor_property(component_name)
        if prop == "box_extent":
            target.set_box_extent(vec(value), False)
        elif prop == "static_mesh":
            target.set_static_mesh(unreal.EditorAssetLibrary.load_asset(value))
        elif prop == "socket_offset_z":
            offset = target.get_editor_property("socket_offset")
            target.set_editor_property("socket_offset", unreal.Vector(offset.x, offset.y, float(value)))
        elif prop in ("relative_location", "relative_scale3d"):
            target.set_editor_property(prop, vec(value))
        else:
            target.set_editor_property(prop, float(value))
        applied.append("%s.%s = %s" % (component_name or "pawn", prop, value))

    for extra in plan["extra_components"]:
        applied.append(add_mesh_component(blueprint, extra))

    unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=False)
    report["blueprint"] = {"path": plan["blueprint"], "applied": applied}
    log("updated %s" % plan["blueprint"])
    return blueprint


def add_mesh_component(blueprint, extra):
    """Adds (or reuses) a StaticMeshComponent under Hull for a glass or extra part."""
    try:
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        library = unreal.SubobjectDataBlueprintFunctionLibrary
        handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
        parent = handles[0]
        existing = None
        for handle in handles:
            obj = library.get_object(library.get_data(handle))
            if obj is None:
                continue
            name = obj.get_name().replace("_GEN_VARIABLE", "")
            if name == "Hull":
                parent = handle
            if name == extra["component"]:
                existing = obj
        if existing is None:
            params = unreal.AddNewSubobjectParams()  # struct constructors take no keyword arguments
            params.set_editor_property("parent_handle", parent)
            params.set_editor_property("new_class", unreal.StaticMeshComponent)
            params.set_editor_property("blueprint_context", blueprint)
            handle, fail_reason = subsystem.add_new_subobject(params)
            if not library.is_handle_valid(handle):
                raise RuntimeError(str(fail_reason))
            subsystem.rename_subobject(handle, unreal.Text(extra["component"]))
            existing = library.get_object(library.get_data(handle))
        existing.set_static_mesh(unreal.EditorAssetLibrary.load_asset(extra["mesh"]))
        # Attached under Hull, which already carries the offset.
        existing.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
        existing.set_collision_profile_name("NoCollision")
        unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
        return "component %s = %s" % (extra["component"], extra["mesh"])
    except Exception as error:
        return "MANUAL STEP: add a Static Mesh component %r under Hull with %s (automatic add failed: %s)" % (
            extra["component"], extra["mesh"], error)


def apply_level_settings(plan, blueprint, apply_planet, set_game_mode, report):
    if not (apply_planet or set_game_mode):
        return
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not les.load_level(LEVEL):
        raise ImportFailed("could not load %s" % LEVEL)
    if apply_planet:
        planet = next((a for a in eas.get_all_level_actors() if a.get_actor_label() == PLANET_LABEL), None)
        if planet is None:
            raise ImportFailed("%s not found in %s" % (PLANET_LABEL, LEVEL))
        for prop, value in plan["planet_settings"]:
            planet.set_editor_property(prop, float(value))
        report["planet"] = dict(plan["planet_settings"])
    if set_game_mode:
        game_mode = load_or_create_blueprint(plan["game_mode"], unreal.SpaceGameMode)
        mode_cdo = blueprint_default_object(game_mode)
        pawn_class = unreal.EditorAssetLibrary.load_blueprint_class(plan["blueprint"])
        mode_cdo.set_editor_property("default_pawn_class", pawn_class)
        unreal.EditorAssetLibrary.save_loaded_asset(game_mode, only_if_is_dirty=False)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        settings = world.get_world_settings()
        settings.set_editor_property("default_game_mode", unreal.EditorAssetLibrary.load_blueprint_class(plan["game_mode"]))
        report["game_mode"] = {"path": plan["game_mode"], "default_pawn_class": plan["blueprint"], "level": LEVEL}
    if not les.save_current_level():
        raise ImportFailed("could not save %s" % LEVEL)


def env_flag(name, default):
    value = os.environ.get(name)
    return default if value is None else value.strip() not in ("0", "false", "False", "")


def main(argv):
    manifest_path = find_manifest(argv[0] if argv else os.environ.get("GAMESPACE_SHIP_MANIFEST"))
    manifest, issues = gx.load_and_validate_manifest(manifest_path)
    log("manifest %s\n%s" % (manifest_path, gx.format_issues(issues)))
    if any(i["level"] == gx.ERROR for i in issues):
        raise ImportFailed("manifest has errors; fix them in Blender and export again")

    plan = build_plan(manifest, os.path.dirname(manifest_path))
    log(format_plan(plan))
    if unreal is None or env_flag("GAMESPACE_SHIP_DRY_RUN", False):
        log("dry run: nothing imported")
        return 0

    report = {"manifest": manifest_path, "ship": plan["ship"], "meshes": {}}
    use_legacy_fbx_importer()
    import_all_meshes(plan, report["meshes"])
    blueprint = apply_pawn_settings(plan, report)
    apply_level_settings(plan, blueprint, env_flag("GAMESPACE_SHIP_APPLY_PLANET", True),
                         env_flag("GAMESPACE_SHIP_SET_GAME_MODE", True), report)

    report_path = os.path.join(os.path.dirname(manifest_path), "%s_import_report.json" % plan["ship"])
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    manual = [a for a in report.get("blueprint", {}).get("applied", []) if a.startswith("MANUAL STEP")]
    log("done; report %s%s" % (report_path, ("\n" + "\n".join(manual)) if manual else ""))
    return 0


if unreal is not None:
    # Run by the editor (like the other asset scripts). A raised exception is what
    # run_editor_python.ps1 reports as FAILED.
    main([])
elif __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ImportFailed, RuntimeError) as error:
        print("FAILED: %s" % error)
        sys.exit(1)
