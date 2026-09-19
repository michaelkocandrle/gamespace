"""Blender MCP helpers for the live-viewport workflow, see Docs/WORKFLOW.md (chapter Blender MCP)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_socket import send

CODE = r'''
import bpy, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
cfg = json.load(open(r"C:\gamespace\gamespace\ArtSource\Ships\Vanguard\Vanguard_ai_build.json", encoding="utf-8"))
spec = cfg["interior"]; p = spec["placement"]
M = Matrix.Translation(Vector(p["offset"])) @ Matrix.Diagonal((p["scale"], p["scale"], p["scale"] * p["height_ratio"], 1.0))
eye = Vector(cfg["sockets"]["Cockpit"]["location"])
ob = bpy.data.objects["SM_Ship_Vanguard_Interior"]
screens_slot = [i for i, m in enumerate(ob.data.materials) if m and m.name.endswith("_Screens")][0]
bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
polys = ob.data.polygons
out = {}
for s in spec["displays"]["screens"]:
    c, u, v = Vector(s["centre"]), Vector(s["u"]).normalized(), Vector(s["v"]).normalized()
    n = u.cross(v).normalized()
    cw = M @ c
    nw = ((M @ (c + n)) - cw).normalized()
    inside = {}
    step = 0.002
    for i in range(-110, 111):
        for j in range(-95, 96):
            a, b = i * step, j * step
            target = M @ (c + u * a + v * b)
            d = (target - eye).normalized()
            loc, nor, idx, dist = bvh.ray_cast(eye, d)
            if loc is None:
                inside[(i, j)] = False
            elif polys[idx].material_index == screens_slot:
                inside[(i, j)] = True
            else:
                hitz = (loc - cw).dot(nw)   # >0: in front of the display plane (raised bezel)
                inside[(i, j)] = -0.02 < hitz < 0.006
    # the opening: the connected region of "inside" cells round the centre
    seen = set(); stack = [(0, 0)]
    while stack:
        k = stack.pop()
        if k in seen or not inside.get(k):
            continue
        seen.add(k)
        i, j = k
        stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
    pts = [(i * step, j * step) for i, j in seen]
    corner = lambda f: max(pts, key=f)
    tl = corner(lambda q: -q[0] + q[1]); tr = corner(lambda q: q[0] + q[1])
    br = corner(lambda q: q[0] - q[1]); bl = corner(lambda q: -q[0] - q[1])
    out[s["name"]] = {"cells": len(pts), "top_left": tl, "top_right": tr, "bottom_right": br, "bottom_left": bl,
                      "u_range": [min(q[0] for q in pts), max(q[0] for q in pts)], "v_range": [min(q[1] for q in pts), max(q[1] for q in pts)]}
print("OPENINGS " + json.dumps(out))
'''
r = send("execute_code", {"code": CODE}, timeout=600)
print(json.dumps(r)[:2500])
