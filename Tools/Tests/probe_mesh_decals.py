"""Probe: can this project draw mesh decals (a static mesh with a Deferred Decal material)?

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\probe_mesh_decals.py

Prints MESHDECAL lines: the renderer settings that matter (DBuffer decals, Nanite), and builds the two
mesh-decal masters of Tools/Assets/ship_materials.py (M_Ship_MeshDecal, M_Ship_MeshDecalPaint) to show
they compile and what the engine derives from their connected pins (MaterialDecalResponse is about
receivers; the DBuffer channels follow the connected outputs). Result recorded in the ship-pipeline skill.
"""
import os
import sys

import unreal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Assets"))
import ship_materials  # noqa: E402

FAIL = []


def log(msg):
    unreal.log("MESHDECAL " + msg)


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
hull = unreal.EditorAssetLibrary.load_asset(ship_materials.MASTERS["hull"])
if hull:
    log("hull master decal response: %s (receives colour, normal, roughness)" % hull.get_editor_property("material_decal_response"))
log("SUMMARY %s (%d failed: %s)" % ("OK" if not FAIL else "FAILED", len(FAIL), ", ".join(FAIL)))
