"""Walk a line through the ship with the game's walker and print, every 3 cm, where its feet are and what its body
touches (no step exemption): finds what stops the character in a doorway or on stairs.

    blender -b ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend --python Tools/Blender/walk_probe.py -- <Ship> x0 y0 x1 y1 [feet_z]
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

args = sys.argv[sys.argv.index("--") + 1:]
ship, x0, y0, x1, y1 = args[0], *map(float, args[1:5])
feet = float(args[5]) if len(args) > 5 else 0.0
recipe = json.load(open(os.path.join(cg.ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), encoding="utf-8"))
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
R = cg.WALK_R
n = int(math.hypot(x1 - x0, y1 - y0) / 0.03) + 1
for i in range(n):
    t = i / max(n - 1, 1)
    c = Vector((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.0))
    rest = None
    for k in range(-6, 7):
        d = R * k / 6.0
        for e in ((d, 0.0), (0.0, d)):
            o = Vector((c.x + e[0], c.y + e[1], feet + cg.WALK_STEP + 0.01)) + off
            hit = tree.ray_cast(o, Vector((0.0, 0.0, -1.0)), cg.WALK_STEP + 1.0)
            if hit[0] is None:
                continue
            z = hit[0].z - off.z + math.sqrt(max(R ** 2 - e[0] ** 2 - e[1] ** 2, 0.0)) - R
            rest = z if rest is None else max(rest, z)
    if rest is None:
        print("WALKPROBE x %.2f y %.2f no floor" % (c.x, c.y))
        continue
    feet = rest + cg.WALK_HOVER
    worst = None
    z = feet + R + 0.05
    while z <= feet + cg.WALK_H - R + 1e-6:
        near = tree.find_nearest(Vector((c.x, c.y, z)) + off, R)
        if near[0] is not None and near[3] < R + 0.01:
            gap = R + 0.01 - near[3]
            if worst is None or gap > worst[0]:
                worst = (gap, near[0] - off, z)
        z += 0.05
    msg = "WALKPROBE x %.2f y %.2f feet %.3f" % (c.x, c.y, feet)
    if worst:
        q = worst[1]
        msg += "  HIT %.3f at (%.3f, %.3f, %.3f) body z %.2f%s" % (worst[0], q.x, q.y, q.z, worst[2],
                                                                    "  (step)" if q.z <= feet + cg.WALK_STEP else "")
    print(msg)
