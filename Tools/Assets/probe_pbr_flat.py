"""Regression plates for the ship masters on faces lying exactly flat (WORKFLOW dd, dg): the real M_Ship_PBR and
M_Ship_Layered on flat plates in the kit showroom's stair bay - axis aligned, turned about the vertical, tilted - next
to the plain kit trim master. Every instance: default textures, MetallicScale 0, RoughnessScale 0.6 - a lit plate is
light grey whatever its UVs, a black one means the master breaks on that orientation. Rebuilds the ship masters
first. Run after import_kit.py (which clears the showroom), then package and shoot Tools/Shots/probe_pbr_flat.json.

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\probe_pbr_flat.py

History: round 1 (27. 9. 2026) isolated the panel seam node, round 2 its groove output and the triplanar weights;
the cause was the (float3x3) cast of the primitive's FDFMatrix structs (ship_materials._TRIPLANAR).
"""
import os
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ship_materials  # noqa: E402

FOLDER = "/Game/Kit/Materials/Probe"
TAG = "KitShowroom"
ORIGIN = unreal.Vector(0.0, -50000.0, 0.0)
PLATES = [                      # (label, master key, roll, yaw)
    ("pbr_flat", "pbr", 0.0, 0.0),
    ("pbr_yaw37", "pbr", 0.0, 37.0),
    ("pbr_tilted", "pbr", 12.0, 0.0),
    ("layered_flat", "layered", 0.0, 0.0),
    ("layered_yaw37", "layered", 0.0, 37.0),
    ("kit_trim", "trim", 0.0, 0.0),
]
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary


def instance(master, name):
    path = "%s/%s" % (FOLDER, name)
    mi = EAL.load_asset(path) if EAL.does_asset_exist(path) else None
    if mi is None:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, unreal.MaterialInstanceConstant,
                                                                     unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, master)
    for p, v in [("MetallicScale", 0.0), ("RoughnessScale", 0.6)]:
        MEL.set_material_instance_scalar_parameter_value(mi, p, v)
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi


def main():
    # the bisecting variants of rounds 1-2 are no longer needed
    wanted = {"MI_Probe_%s" % label for label, _, _, _ in PLATES}
    for path in EAL.list_assets(FOLDER, recursive=False, include_folder=False):
        if path.split(".")[-1] not in wanted:
            EAL.delete_asset(path)
    masters = ship_materials.build_masters()
    masters["trim"] = EAL.load_asset("/Game/Kit/Materials/M_Kit_Trim")
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSpace")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith("KitProbe_"):
            actors.destroy_actor(a)
    cube = EAL.load_asset("/Engine/BasicShapes/Cube")
    for i, (label, key, roll, yaw) in enumerate(PLATES):
        mi = instance(masters[key], "MI_Probe_%s" % label)
        x, y = 14.25 + i * 0.3, -0.6          # between the stair and the ramp, on the provisional floor
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, ORIGIN + unreal.Vector(x * 100.0, y * 100.0, 3.0),
                                          unreal.Rotator(roll=roll, pitch=0.0, yaw=yaw))
        a.static_mesh_component.set_static_mesh(cube)
        a.static_mesh_component.set_material(0, mi)
        a.set_actor_scale3d(unreal.Vector(0.25, 0.5, 0.04))
        a.set_actor_label("KitProbe_%d_%s" % (i, label))
        a.set_editor_property("tags", [unreal.Name(TAG)])
        unreal.log("PROBEFLAT %d %s -> %s" % (i, label, masters[key].get_name()))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()


main()
