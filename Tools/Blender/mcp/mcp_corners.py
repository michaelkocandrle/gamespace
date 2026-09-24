"""Move the live screen quads to corner sets (u, v in the display frame, TL TR BR BL) and screenshot the eye view.
python mcp_corners.py <Ship> '<json {left:[[u,v]x4], right:[...], centre_top:[...]}>' out.png (screens left out keep theirs)
Reads ArtSource/Ships/<Ship>/<Ship>_ai_build.json and moves quads on SM_Ship_<Ship>_Interior."""
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


USAGE = "python mcp_corners.py <Ship> '<corners json>' out.png"
SHIP, CFG_PATH, INTERIOR = ship_paths(sys.argv, USAGE)
if len(sys.argv) < 4:
    raise SystemExit("usage: " + USAGE)
corners = sys.argv[2]
CODE = r'''
import bpy, bmesh, json
from mathutils import Vector, Matrix
corners = json.loads(%r)
cfg = json.load(open(__CFG_PATH__, encoding="utf-8"))
spec = cfg["interior"]; p = spec["placement"]
M = Matrix.Translation(Vector(p["offset"])) @ Matrix.Diagonal((p["scale"], p["scale"], p["scale"] * p["height_ratio"], 1.0))
for o in [o for o in bpy.data.objects if o.name.startswith("MeasureGrid")]:
    o.hide_set(True)
ob = bpy.data.objects[__INTERIOR__]
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
CODE = CODE.replace("__CFG_PATH__", repr(CFG_PATH)).replace("__INTERIOR__", repr(INTERIOR))
print(send("execute_code", {"code": CODE}))
print(send("get_viewport_screenshot", {"max_size": 1600, "filepath": sys.argv[3], "format": "png"}))
