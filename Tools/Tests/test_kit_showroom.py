"""Checks the interior kit as Tools/Kit/kit_build.py and Tools/Assets/import_kit.py leave it, in a fresh editor
process (first kit checks; step 5 of the kit brief adds the geometry checks).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_kit_showroom.py

Prints "KITTEST PASS" / "KITTEST FAIL" lines; a failure is also logged as an error, so the run reports FAILED.
Never saves.

What it guards (27. 9. 2026):
- every kit mesh has vertex colours: the layered master's edge-wear and dirt masks (kit_geo, face-corner Col).
  They were lost once in kit_build.join() and came out all white, which Unreal drops on import;
- the layout rule for decals: never the same service label (st_*, label_*) on neighbouring modules of a wall
  run of the sample (import_kit.SHOWROOM, the labels from kit_manifest.json);
- the kit material step: seam dirt on the floor plates, the layered master's surface detail switched on for every
  kit instance and off for the ships';
- the showroom is walkable: a gravity volume over it, the start U / space.Showroom puts the player at, the
  dark sun box around it without collision.
"""

import ast
import json
import os
import tempfile

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "Tools", "Assets", "import_kit.py")
MANIFEST = os.path.join(REPO, "ArtSource", "Kit", "Export", "kit_manifest.json")
MAP = "/Game/Maps/TestSpace"

failures = []


def log(msg):
    unreal.log("KITTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)
        unreal.log_error("KITTEST FAIL " + name)


# the constants of import_kit.py, read without running it
tree = ast.parse(open(SCRIPT, encoding="utf-8").read())
C = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        try:
            C[node.targets[0].id] = ast.literal_eval(node.value)
        except ValueError:
            pass
parts = json.load(open(MANIFEST, encoding="utf-8"))["parts"]
EXPORT_DIR = os.path.join(tempfile.gettempdir(), "kittest_export")
os.makedirs(EXPORT_DIR, exist_ok=True)


def exported_colours(sm):
    fn = os.path.join(EXPORT_DIR, sm.get_name() + ".fbx")
    task = unreal.AssetExportTask()
    task.set_editor_property("object", sm)
    task.set_editor_property("filename", fn)
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("replace_identical", True)
    task.set_editor_property("exporter", unreal.StaticMeshExporterFBX())
    if not unreal.Exporter.run_asset_export_task(task) or not os.path.exists(fn):
        return False
    with open(fn, "rb") as f:
        return f.read().count(b"LayerElementColor") > 0

# ---------------------------------------------------------------- meshes: vertex colours
for name, part in sorted(parts.items()):
    sm = unreal.EditorAssetLibrary.load_asset("/Game/Kit/Meshes/" + name)
    check("%s imported" % name, sm is not None)
    if sm is None:
        continue
    masks = part.get("colour_masks", {})
    # not all white: a ceiling part has nothing by the floor, a lofted part no chamfer (kit_build applies the same)
    check("%s: colour masks exported (edge %s, floor %s, secondary %s corners)" % (name, masks.get("edge"), masks.get("floor"), masks.get("secondary")),
          masks.get("domain") == "CORNER" and masks.get("edge", 0) + masks.get("floor", 0) + masks.get("secondary", 0) > 0)
    # has_vertex_colors() answers False in this commandlet even for the Wayfarer hull, whose masks work: export
    # the mesh back to FBX instead - Unreal writes a colour layer only when the mesh has colours (27. 9. 2026)
    check("%s: vertex colours in Unreal" % name, exported_colours(sm))
    if name.startswith("SM_Kit_Floor_Plate"):
        # the kit material step: dirt round every plate (kit_geo seam ring)
        check("%s: seam dirt on the plates (%s corners)" % (name, masks.get("seam")), masks.get("seam", 0) > 0)

# ---------------------------------------------------------------- materials: the layered master's surface detail
MEL = unreal.MaterialEditingLibrary
kit_layered = [a for a in unreal.EditorAssetLibrary.list_assets("/Game/Kit/Materials", recursive=False, include_folder=False)
               if a.split(".")[-1].startswith("MI_Kit_")]
for path in sorted(kit_layered):
    mi = unreal.EditorAssetLibrary.load_asset(path)
    parent = mi.get_editor_property("parent") if isinstance(mi, unreal.MaterialInstanceConstant) else None
    if parent is None or parent.get_name() != "M_Ship_Layered":
        continue
    # the roles may override SURFACE (the paint 80 cm, the signal orange 30 cm): a sane grunge tile, the switch on
    tile = MEL.get_material_instance_scalar_parameter_value(mi, "GrungeTileCm")
    check("%s: surface detail on (SurfaceDetail, GrungeTileCm %.0f)" % (mi.get_name(), tile),
          MEL.get_material_instance_static_switch_parameter_value(mi, "SurfaceDetail") and 20.0 <= tile <= 200.0)
# the ships keep the master's default: the switch off (the Wayfarer's look does not change with the kit's)
for path in unreal.EditorAssetLibrary.list_assets("/Game/Ships/Wayfarer/Materials", recursive=False, include_folder=False):
    mi = unreal.EditorAssetLibrary.load_asset(path)
    if isinstance(mi, unreal.MaterialInstanceConstant) and mi.get_editor_property("parent")             and mi.get_editor_property("parent").get_name() == "M_Ship_Layered":
        check("%s: surface detail off" % mi.get_name(), not MEL.get_material_instance_static_switch_parameter_value(mi, "SurfaceDetail"))

# ---------------------------------------------------------------- the layout rule for service labels
runs = C.get("SHOWROOM", {}).get("wall_runs", [])
check("the showroom layout is readable from import_kit.py", bool(runs))
for i, (a0, b0, n, mods) in enumerate(runs):
    for a, b in zip(mods, mods[1:]):
        la = set(parts.get("SM_Kit_" + a, {}).get("service_labels", []))
        lb = set(parts.get("SM_Kit_" + b, {}).get("service_labels", []))
        check("run %d: %s | %s share no service label" % (i, a, b), not (la & lb), ", ".join(sorted(la & lb)))

# ---------------------------------------------------------------- the showroom in the level
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
tag = unreal.Name(C["TAG"])
room = [a for a in actors if tag in list(a.tags)]
modules = [a for a in room if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh
           and a.static_mesh_component.static_mesh.get_name().startswith("SM_Kit_")]
L = C["SHOWROOM"]
expected = sum(len(r[3]) for r in L["wall_runs"]) + sum(len(r[2]) for r in L["run_parts"]) + len(L["placed"])
check("every part of the sample placed (%d)" % expected, len(modules) == expected, "%d" % len(modules))
walls = [a for a in modules if a.static_mesh_component.static_mesh.get_name().startswith("SM_Kit_Wall_")]
rects = [a for a in room if isinstance(a, unreal.RectLight)]
# two per wall module: the cove up and the wash under the lip (the plinth's went, 27. 9. 2026)
check("linear lights along the strips (%d)" % len(rects), len(rects) >= 2 * sum(len(r[3]) for r in L["wall_runs"]))
gravity = [a for a in room if isinstance(a, unreal.SpaceGravityVolume)]
check("one gravity volume, %s cm/s2" % C["GRAVITY_CMS2"], len(gravity) == 1
      and abs(gravity[0].get_editor_property("gravity_cm_s2") - C["GRAVITY_CMS2"]) < 0.5)
spawn = [a for a in actors if unreal.Name(C["SPAWN_TAG"]) in list(a.tags)]
check("one start of the walk (%s)" % C["SPAWN_TAG"], len(spawn) == 1)
annex = [a for a in actors if unreal.Name(C["ANNEX_SPAWN_TAG"]) in list(a.tags)]
check("one start of the annex (%s, U from the showroom)" % C["ANNEX_SPAWN_TAG"], len(annex) == 1)
stairs = [a for a in actors if unreal.Name(C["STAIRS_SPAWN_TAG"]) in list(a.tags)]
check("one start of the stair bay (%s, U from the annex)" % C["STAIRS_SPAWN_TAG"], len(stairs) == 1)
if gravity and stairs:
    check("the stair bay's start lies inside the gravity volume",
          gravity[0].contains_point(stairs[0].get_actor_location() + unreal.Vector(0.0, 0.0, 100.0)))
# batch 3: the corridors stand on kit floors, no provisional floor plane left in them
floors = [m for m in modules if m.static_mesh_component.static_mesh.get_name().startswith("SM_Kit_Floor_")]
prov = [a for a in room if a.get_actor_label().startswith("KitProvisional_Floor_")]
check("kit floors in the corridors (%d modules), one provisional floor (the stair bay)" % len(floors),
      len(floors) >= 20 and len(prov) == 1, "%d provisional" % len(prov))
if gravity and spawn:
    start = spawn[0].get_actor_location() + unreal.Vector(0.0, 0.0, 100.0)
    check("the start and every part lie inside the gravity volume",
          gravity[0].contains_point(start) and all(gravity[0].contains_point(m.get_actor_location() + unreal.Vector(0, 0, 50.0)) for m in modules))
if gravity and annex:
    check("the annex start lies inside the gravity volume",
          gravity[0].contains_point(annex[0].get_actor_location() + unreal.Vector(0.0, 0.0, 100.0)))
# MegaLights variant C (author, 27. 9. 2026): every kit light casts its (ray-traced) shadow
lights = [a for a in room if isinstance(a, (unreal.RectLight, unreal.SpotLight, unreal.PointLight))]
unshadowed = [a.get_actor_label() for a in lights if not a.get_component_by_class(unreal.LocalLightComponent).get_editor_property("cast_shadows")]
check("every showroom light casts shadows (%d lights)" % len(lights), lights and not unshadowed, ", ".join(unshadowed[:5]))
# the half-open window looks out at a star field card behind the end wall, without collision
stars = [a for a in room if a.get_actor_label() == "KitShowroom_WindowStars"]
mat = stars[0].static_mesh_component.get_material(0) if stars else None
check("a star field behind the window (%s), no collision" % C["STARS_MATERIAL"], len(stars) == 1 and mat is not None
      and mat.get_path_name().startswith(C["STARS_MATERIAL"])
      and str(stars[0].static_mesh_component.get_collision_profile_name()) == "NoCollision",
      mat.get_path_name() if mat else "none")
box = [a for a in room if a.get_actor_label() == "KitProvisional_SunBox"]
check("the sun box has no collision (the player walks inside it)", len(box) == 1
      and str(box[0].static_mesh_component.get_collision_profile_name()) == "NoCollision",
      box and str(box[0].static_mesh_component.get_collision_profile_name()))

log("SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
