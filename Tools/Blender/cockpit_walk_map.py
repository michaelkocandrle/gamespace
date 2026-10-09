"""A walk map of the cockpit (author 9. 10. 2026: "you still cannot walk round the seat"): the game walker of
check_ship_geometry (capsule WALK_R x WALK_H, standing on the highest floor within a step) tried on a 3 cm grid
over the cockpit floor; every free cell joined to its free neighbours within a step's height, flood-filled from the
left aisle. Writes Saved/GeoCheck/cockpit_walk.png (green: walkable and reached, yellow: free but cut off, red:
the capsule hits something) and prints whether the walker gets round the seat (behind it and in front of it).

    blender -b ArtSource/Ships/Wayfarer/Wayfarer_HS_Game.blend --python Tools/Blender/cockpit_walk_map.py -- Wayfarer
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_ship_geometry as cg  # noqa: E402

ROOT = cg.ROOT
ship = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "Wayfarer"
recipe = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), encoding="utf-8"))
off = Vector(recipe["assemble"]["offset"])
all_bm = bmesh.new()
for suffix in ("_Interior", "_InteriorKit", "_InteriorKitMod"):
    ob = cg.obj(ship, suffix)
    if ob is None:
        continue
    bm = cg.world_bm(ob)
    me = bpy.data.meshes.new("_walk")
    bm.to_mesh(me)
    all_bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bm.free()
tree = BVHTree.FromBMesh(all_bm)

X0, X1, Y0, Y1, STEP = 15.4, 18.5, -1.45, 1.45, 0.03
FLOOR = 1.15
nx, ny = int((X1 - X0) / STEP) + 1, int((Y1 - Y0) / STEP) + 1
feet = {}
free = {}
R = cg.WALK_R
for i in range(nx):
    for j in range(ny):
        c = Vector((X0 + i * STEP, Y0 + j * STEP, 0.0))
        rest = None
        for k in range(-6, 7):
            d = R * k / 6.0
            for e in ((d, 0.0), (0.0, d)):
                o = Vector((c.x + e[0], c.y + e[1], FLOOR + cg.WALK_STEP + 0.01)) + off
                hit = tree.ray_cast(o, Vector((0.0, 0.0, -1.0)), cg.WALK_STEP + 0.4)
                if hit[0] is None:
                    continue
                z = hit[0].z - off.z + math.sqrt(max(R ** 2 - e[0] ** 2 - e[1] ** 2, 0.0)) - R
                rest = z if rest is None else max(rest, z)
        if rest is None:
            continue
        f = rest + cg.WALK_HOVER
        ok = True
        z = f + R + 0.05
        while z <= f + cg.WALK_H - R + 1e-6:
            near = tree.find_nearest(Vector((c.x, c.y, z)) + off, R)
            if near[0] is not None and near[3] < R + 0.01:
                ok = False
                break
            z += 0.05
        feet[(i, j)] = f
        free[(i, j)] = ok


def cell(x, y):
    return (int(round((x - X0) / STEP)), int(round((y - Y0) / STEP)))


start = cell(16.2, 0.85)
if not free.get(start):
    cand = [k for k, v in free.items() if v and abs(k[0] - start[0]) < 10 and abs(k[1] - start[1]) < 10]
    start = cand[0] if cand else start
reach = set()
stack = [start] if free.get(start) else []
while stack:
    k = stack.pop()
    if k in reach:
        continue
    reach.add(k)
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (k[0] + di, k[1] + dj)
        if free.get(n) and n not in reach and abs(feet[n] - feet[k]) <= cg.WALK_STEP:
            stack.append(n)


def reached_line(xs, y0, y1):
    """Is some cell between y0 and y1 at each of the xs reached (a passage across)."""
    return all(any(cell(x, y) in reach for y in [y0 + t * STEP for t in range(int((y1 - y0) / STEP) + 1)]) for x in xs)


behind = any(cell(x, 0.0) in reach for x in [15.6 + t * STEP for t in range(30)])
front = any(cell(x, 0.0) in reach for x in [17.35 + t * STEP for t in range(40)])
right = any(cell(16.9, y) in reach for y in [-1.2 + t * STEP for t in range(25)])
print("WALKMAP " + json.dumps({"start": [round(X0 + start[0] * STEP, 2), round(Y0 + start[1] * STEP, 2)],
                               "reached_cells": len(reach), "behind_seat": behind, "in_front_of_seat": front,
                               "right_aisle": right}))
# the map as text, x down the rows (aft to fore), y across (port +y on the left): o reached, . free but cut off,
# # blocked, blank no floor
print("WALKROW y from %.2f (left) to %.2f (right), 6 cm" % (1.4, -1.4))
for x in [15.5 + t * 0.06 for t in range(int((18.0 - 15.5) / 0.06) + 1)]:
    ys = [1.4 - t * 0.06 for t in range(47)]
    row = "".join("o" if cell(x, y) in reach else ("." if free.get(cell(x, y)) else ("#" if cell(x, y) in free else " ")) for y in ys)
    print("WALKROW x %.2f %s" % (x, row))

try:
    from PIL import Image
    img = Image.new("RGB", (nx, ny), (40, 40, 40))
    px = img.load()
    for (i, j), ok in free.items():
        px[i, ny - 1 - j] = (60, 200, 90) if (i, j) in reach else ((230, 200, 60) if ok else (200, 60, 50))
    img = img.resize((nx * 6, ny * 6), Image.NEAREST)
    out = os.path.join(ROOT, "Saved", "GeoCheck", "cockpit_walk.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print("WALKMAP image", out)
except ImportError:
    print("WALKMAP no PIL in Blender's Python: image skipped")
