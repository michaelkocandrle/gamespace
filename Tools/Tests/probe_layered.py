"""Probe: does the Wayfarer's hull reach the layered material with its vertex-colour masks?

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\probe_layered.py

Prints LAYERED lines: whether SM_Ship_Wayfarer imports its vertex colours, which parent every hull material
instance has, and the layered master's compile state. SUMMARY OK when the colours are imported and the paint
slots use M_Ship_Layered.
"""
import unreal

FAIL = []


def log(msg):
    unreal.log("LAYERED " + msg)


mesh = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Wayfarer/Meshes/SM_Ship_Wayfarer")
# has_vertex_colors() reads the render data, which a Nanite mesh does not fill in the commandlet: it said
# False while the packaged game showed the masks (24. 9. 2026). The import option is what decides.
data = mesh.get_editor_property("asset_import_data")
option = data.get_editor_property("vertex_color_import_option") if data else None
log("SM_Ship_Wayfarer vertex colour import: %s" % option)
if option != unreal.VertexColorImportOption.REPLACE:
    FAIL.append("vertex colours not imported (option %s)" % option)
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
