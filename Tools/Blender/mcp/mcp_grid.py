"""Blender MCP helpers for the live-viewport workflow, see Docs/WORKFLOW.md (chapter Blender MCP).

    python mcp_grid.py <Ship> out.png

Reads ArtSource/Ships/<Ship>/<Ship>_ai_build.json and works on SM_Ship_<Ship>_Interior."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_socket import send


def ship_paths(argv, usage):
    """The ship is the first command-line argument: its AI build config and interior object name."""
    if len(argv) < 2 or argv[1].startswith("-"):
        raise SystemExit("usage: " + usage)
    ship = argv[1]
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cfg = os.path.join(repo, "ArtSource", "Ships", ship, "%s_ai_build.json" % ship)
    if not os.path.isfile(cfg):
        raise SystemExit("No AI build config for ship %r: %s" % (ship, cfg))
    return ship, cfg, "SM_Ship_%s_Interior" % ship


USAGE = "python mcp_grid.py <Ship> out.png"
SHIP, CFG_PATH, INTERIOR = ship_paths(sys.argv, USAGE)
if len(sys.argv) < 3:
    raise SystemExit("usage: " + USAGE)

CODE = r'''
import bpy, bmesh, json
from mathutils import Vector, Matrix
cfg = json.load(open(__CFG_PATH__, encoding="utf-8"))
spec = cfg["interior"]; p = spec["placement"]
M = Matrix.Translation(Vector(p["offset"])) @ Matrix.Diagonal((p["scale"], p["scale"], p["scale"] * p["height_ratio"], 1.0))
def mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = 3.0
    return m
fine, major, axis = mat("GridFine", (0.9, 0.9, 0.2)), mat("GridMajor", (1.0, 0.1, 0.1)), mat("GridAxis", (0.1, 1.0, 0.2))
for o in [o for o in bpy.data.objects if o.name.startswith("MeasureGrid")]:
    bpy.data.objects.remove(o)
ob = bpy.data.objects[__INTERIOR__]
screens_slot = [i for i, m in enumerate(ob.data.materials) if m and m.name.endswith("_Screens")][0]
ob.data.materials[screens_slot].diffuse_color = (0.05, 0.1, 0.12, 1)
for s in spec["displays"]["screens"]:
    c, u, v = Vector(s["centre"]), Vector(s["u"]).normalized(), Vector(s["v"]).normalized()
    n = u.cross(v).normalized()
    bm = bmesh.new()
    def strip(a0, b0, a1, b1, w, slot):
        d = Vector((a1 - a0, b1 - b0)); d.normalize(); side = Vector((-d.y, d.x)) * w
        pts = [(a0 + side.x, b0 + side.y), (a1 + side.x, b1 + side.y), (a1 - side.x, b1 - side.y), (a0 - side.x, b0 - side.y)]
        f = bm.faces.new([bm.verts.new(M @ (c + u * a + v * b + n * 0.007)) for a, b in pts])
        f.material_index = slot
    for k in range(-25, 26):
        x = k / 100.0
        slot = 2 if k == 0 else (1 if k % 5 == 0 else 0)
        w = 0.0012 if slot else 0.0005
        strip(x, -0.2, x, 0.2, w, slot)
        strip(-0.25, x * 0.8 / 1.0 if False else x, 0.25, x, w, slot) if abs(x) <= 0.2 else None
    me = bpy.data.meshes.new("MeasureGrid_" + s["name"]); bm.to_mesh(me); bm.free()
    g = bpy.data.objects.new("MeasureGrid_" + s["name"], me); bpy.context.scene.collection.objects.link(g)
    for m in (fine, major, axis):
        me.materials.append(m)
print("GRID ok")
'''
CODE = CODE.replace("__CFG_PATH__", repr(CFG_PATH)).replace("__INTERIOR__", repr(INTERIOR))
print(send("execute_code", {"code": CODE}))
print(send("get_viewport_screenshot", {"max_size": 2400, "filepath": sys.argv[2], "format": "png"}))
