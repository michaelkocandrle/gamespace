"""Clashes between a ship's kit parts (30. 9. 2026): the geometry check (check_ship_geometry.py) joins the kit rooms into
one mesh and never sees one kit part standing in another - the cabin's hygiene cell's roof ran into the liner's cable
tray on the chamfer. This places every kit part of the recipe as its own object (kit_layout, as kit_rooms.py does in
Unreal) and reports the pairs whose surfaces intersect (BVHTree.overlap), for the parts named on the command line
(or all of a category prefix, e.g. Furniture_) against every other part.

    blender -b --factory-startup --python Tools/Kit/kit_clash.py -- <Ship> [part or prefix ...]

Prints KITCLASH {"pairs": [[a, b, n], ...]} - n intersecting face pairs; exits 1 when there are any.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import kit_layout  # noqa: E402

# parts meant to meet: brackets and ducts reach into the liner or the ceiling, a floor under a wall's plinth
TOUCHING_OK = 0.004          # (BVHTree.overlap reports intersecting triangles; coplanar contact counts too)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    ship, wanted = args[0], args[1:] or ["Furniture_"]
    recipe = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), encoding="utf-8"))
    mods = recipe["interior"]["kit_modules"]
    placed = kit_layout.layout_parts(mods, kit_layout.manifest_parts())
    names = {"SM_Kit_" + m for m, _, _ in placed}
    src = {}
    for path in kit_layout.kit_blends():
        with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
            got = [n for n in data_from.objects if n in names and n not in src]
            data_to.objects = list(got)
        for n, ob in zip(got, data_to.objects):
            if ob is not None:
                src[n] = ob
    dg = bpy.context.evaluated_depsgraph_get()
    trees = []
    for k, (m, (x, y_ue, z), yaw) in enumerate(placed):
        ob = src["SM_Kit_" + m]
        ev = ob.evaluated_get(dg)
        bm = bmesh.new()
        bm.from_mesh(ev.to_mesh())
        # drop the decal and grime cards (thin shells laid on the surfaces) - by material name
        mats = [mt.name if mt else "" for mt in ob.data.materials]
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if "Decal" in mats[f.material_index]], context="FACES")
        bm.transform(Matrix.Translation((x, -y_ue, z)) @ Matrix.Rotation(math.radians(-yaw), 4, "Z"))
        bm.faces.ensure_lookup_table()
        trees.append(("%s#%d" % (m, k), BVHTree.FromBMesh(bm), [f.calc_center_median().copy() for f in bm.faces]))
        ev.to_mesh_clear()
        bm.free()
    pairs = []
    for i, (a, ta, ca) in enumerate(trees):
        if not any(a.startswith(w) for w in wanted):
            continue
        for j, (b, tb, cb) in enumerate(trees):
            if i == j or (any(b.startswith(w) for w in wanted) and j < i):
                continue
            ov = ta.overlap(tb)
            if ov:
                # where: the layout-metre centre of the first few faces of `a` that intersect (for finding the cause)
                at = sorted({tuple(round(c, 2) for c in ca[fa]) for fa, fb in ov})[:4]
                pairs.append([a, b, len(ov), at])
    print("KITCLASH " + json.dumps({"ship": ship, "parts": len(trees), "pairs": pairs}))
    sys.exit(1 if pairs else 0)


main()
