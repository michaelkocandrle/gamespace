"""Probe: can this project draw mesh decals (a static mesh with a Deferred Decal material)?

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\probe_mesh_decals.py

Prints MESHDECAL lines: the renderer settings that matter (DBuffer decals, Nanite), and builds the two
mesh-decal masters of Tools/Assets/ship_materials.py (M_Ship_MeshDecal, M_Ship_MeshDecalPaint) to show
they compile and what the engine derives from their connected pins (MaterialDecalResponse is about
receivers; the DBuffer channels follow the connected outputs). Also walks what feeds each output of the
paint master (its opacity must be M.R x DecalOpacity x DecalColorMap alpha) and checks the decal textures'
alpha survived the import. Result recorded in the ship-pipeline skill.
"""
import os
import sys

import unreal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Assets"))
import ship_materials  # noqa: E402

FAIL = []
MEL = unreal.MaterialEditingLibrary


def log(msg):
    unreal.log("MESHDECAL " + msg)


def describe(node, depth=0):
    """What feeds a node, a few levels deep (class, parameter name, the input pins)."""
    if node is None or depth > 4:
        return "-"
    name = node.get_class().get_name().replace("MaterialExpression", "")
    try:
        name += "(%s)" % node.get_editor_property("parameter_name")
    except Exception:
        pass
    ins = MEL.get_inputs_for_material_expression(unreal.EditorAssetLibrary.load_asset(ship_materials.MASTERS["meshdecal_paint"]), node) \
        if depth < 4 else []
    parts = [describe(i, depth + 1) for i in ins if i is not None]
    return name + ("[" + ", ".join(parts) + "]" if parts else "")


for cvar in ("r.DBuffer", "r.Nanite", "r.MeshDecals.DepthBias"):
    log("%s = %s" % (cvar, unreal.SystemLibrary.get_console_variable_float_value(cvar)))
if unreal.SystemLibrary.get_console_variable_float_value("r.DBuffer") < 1:
    FAIL.append("r.DBuffer off: decal normals would not reach the lit hull")
for paint in (False, True):
    m = ship_materials.build_mesh_decal_master(paint)
    domain = m.get_editor_property("material_domain")
    log("%s: domain %s, blend %s" % (m.get_name(), domain, m.get_editor_property("blend_mode")))
    if domain != unreal.MaterialDomain.MD_DEFERRED_DECAL:
        FAIL.append(m.get_name() + " not a deferred decal")
    for prop in (unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_OPACITY, unreal.MaterialProperty.MP_NORMAL,
                 unreal.MaterialProperty.MP_ROUGHNESS, unreal.MaterialProperty.MP_METALLIC):
        node = MEL.get_material_property_input_node(m, prop)
        log("  %s <- %s" % (str(prop).split(".")[-1], describe(node) if node else "not connected"))
hull = unreal.EditorAssetLibrary.load_asset(ship_materials.MASTERS["hull"])
if hull:
    log("hull master decal response: %s (receives colour, normal, roughness)" % hull.get_editor_property("material_decal_response"))
for tex in ("T_Decals_BC", "T_Trim_BC"):
    t = unreal.EditorAssetLibrary.load_asset("/Game/Ships/Wayfarer/Textures/" + tex)
    if t:
        log("%s: compression %s, srgb %s, alpha kept: %s" % (tex, t.get_editor_property("compression_settings"),
                                                         t.get_editor_property("srgb"),
                                                         not t.get_editor_property("compression_no_alpha")))
log("SUMMARY %s (%d failed: %s)" % ("OK" if not FAIL else "FAILED", len(FAIL), ", ".join(FAIL)))
