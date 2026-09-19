"""Move the live screen quads to corner sets (u, v in the display frame, TL TR BR BL) and screenshot the eye view.
python mcp_corners.py '<json {left:[[u,v]x4], right:[...], centre_top:[...]}>' out.png (screens left out keep theirs)"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_socket import send

corners = sys.argv[1]
CODE = r'''
import bpy, bmesh, json
from mathutils import Vector, Matrix
corners = json.loads(%r)
cfg = json.load(open(r"C:\gamespace\gamespace\ArtSource\Ships\Vanguard\Vanguard_ai_build.json", encoding="utf-8"))
spec = cfg["interior"]; p = spec["placement"]
M = Matrix.Translation(Vector(p["offset"])) @ Matrix.Diagonal((p["scale"], p["scale"], p["scale"] * p["height_ratio"], 1.0))
for o in [o for o in bpy.data.objects if o.name.startswith("MeasureGrid")]:
    o.hide_set(True)
ob = bpy.data.objects["SM_Ship_Vanguard_Interior"]
slot = [i for i, m in enumerate(ob.data.materials) if m and m.name.endswith("_Screens")][0]
bm = bmesh.new(); bm.from_mesh(ob.data)
quads = [f for f in bm.faces if f.material_index == slot]
for s in spec["displays"]["screens"]:
    c, u, v = Vector(s["centre"]), Vector(s["u"]).normalized(), Vector(s["v"]).normalized()
    n = u.cross(v).normalized()
    cw = M @ c
    if s["name"] not in corners:
        continue
    face = min(quads, key=lambda f: (f.calc_center_median() - cw).length)
    uv = bm.loops.layers.uv.active
    # the loops keep their UVs: match each loop to the corner with the same UV corner
    for loop in face.loops:
        x, y = loop[uv].uv
        k = s["name"]
        # Which corner of the screen's texture share this loop is: fx 0 left / 1 right, fy 1 top.
        if "texture_rect" in s:
            (w, h), (x0, y0, x1, y1) = spec["displays"]["texture_size"], s["texture_rect"]
            fx = round((x * w - x0) / (x1 - x0))
            fy = round((y1 - (1.0 - y) * h) / (y1 - y0))
        else:
            half = spec["displays"]["screens"].index(s)
            fx = round(x * len(spec["displays"]["screens"]) - half)
            fy = round(y)
        idx = {(0, 1): 0, (1, 1): 1, (1, 0): 2, (0, 0): 3}[(fx, fy)]
        a, b = corners[k][idx]
        loop.vert.co = M @ (c + u * a + v * b + n * 0.005)
bm.to_mesh(ob.data); bm.free(); ob.data.update()
print("CORNERS set")
''' % corners
print(send("execute_code", {"code": CODE}))
print(send("get_viewport_screenshot", {"max_size": 1600, "filepath": sys.argv[2], "format": "png"}))
