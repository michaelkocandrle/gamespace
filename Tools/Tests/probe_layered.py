"""Probe: does the Wayfarer's hull reach the layered material with its vertex-colour masks?

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\probe_layered.py

Prints LAYERED lines: whether SM_Ship_Wayfarer carries vertex colours, which parent every hull material
instance has, and the layered master's compile state. SUMMARY OK when the mesh has colours and the paint
slots use M_Ship_Layered.
"""
import unreal

FAIL = []


def log(msg):
    unreal.log("LAYERED " + msg)


mesh = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Wayfarer/Meshes/SM_Ship_Wayfarer")
sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
has_vc = None
for fn in ("has_vertex_colors",):
    try:
        has_vc = getattr(sub, fn)(mesh)
    except Exception as error:
        log("%s failed: %s" % (fn, error))
if has_vc is None:
    try:
        has_vc = unreal.EditorStaticMeshLibrary.has_vertex_colors(mesh)
    except Exception as error:
        log("EditorStaticMeshLibrary.has_vertex_colors failed: %s" % error)
log("SM_Ship_Wayfarer has vertex colours: %s" % has_vc)
if not has_vc:
    FAIL.append("no vertex colours on the hull")
data = mesh.get_editor_property("asset_import_data")
try:
    log("import option: %s" % data.get_editor_property("vertex_color_import_option"))
except Exception as error:
    log("import data: %s" % error)
for slot in mesh.get_editor_property("static_materials"):
    mi = slot.get_editor_property("material_interface")
    parent = mi.get_editor_property("parent") if isinstance(mi, unreal.MaterialInstance) else None
    log("slot %s -> %s (parent %s)" % (slot.get_editor_property("material_slot_name"), mi.get_name() if mi else None,
                                       parent.get_name() if parent else None))
    if str(slot.get_editor_property("material_slot_name")).endswith("Paint") and (parent is None or parent.get_name() != "M_Ship_Layered"):
        FAIL.append("paint slot not on M_Ship_Layered")
master = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Shared/Materials/M_Ship_Layered")
log("M_Ship_Layered loaded: %s" % bool(master))
log("SUMMARY %s (%d failed: %s)" % ("OK" if not FAIL else "FAILED", len(FAIL), ", ".join(FAIL)))
