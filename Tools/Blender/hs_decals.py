"""Mesh decals and trim strips on a hard-surface ship (skill ship-pipeline 3b3), called by hs_assemble_ship.py.

The library (Tools/Blender/decal_library.py) holds the atlases and an index of every item's UV rect and
size. This module puts them on the ship from the recipe's "decals" block, in LAYOUT coordinates:

  items   one decal per entry: "item" (library name), where ("on": pod / side / top / bottom / ray), "rot"
          degrees about the surface normal (0 = the item's x along the ship), "scale"; "mirror" (default
          true) repeats it on the starboard side. "along" repeats it: {"step": m, "count": n} along x.
  trim    ribbons of a trim strip ("strip"): "pod_ring" (a band around a pod at x over a range of
          angles), "top_cross" (across the roof or belly at x from y0 to y1, rays from above / below),
          "pod_line" (along a pod at an angle from x0 to x1), "ray_line" (layout "points" cast along "dir").

Every decal and ribbon is a grid of quads laid onto the ship: each vertex is ray-cast back onto the hull
along the surface normal and lifted "offset_m" (2 mm) off it, so the quad follows curvature without
z-fighting. Items with their own colour ("has_color" in the index) get a second quad a hair higher with the
paint material. All of it is one mesh (the "Decals" part, not Nanite: Nanite cannot draw decal-domain
materials) with slots Decal / DecalPaint / Trim / TrimPaint and the atlas UVs; it gets no UV unwrap and no
collision.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SLOTS = ("Decal", "DecalPaint", "Trim", "TrimPaint")


def _frame(n, rot_deg=0.0):
    """In-surface axes of a decal that reads right from outside: x runs along the ship and appears to the
    right of a viewer looking at the surface (aft on port-facing surfaces, forward elsewhere), y = n x x
    (so x, y, n are right-handed and the atlas is not mirrored), then turned by rot_deg about n."""
    if abs(n.x) > 0.7:
        # the ship's front or back face: x across the ship, to the viewer's right
        ref = Vector((0, 1 if n.x > 0 else -1, 0))
    else:
        ref = Vector((-1, 0, 0)) if n.y > 0.3 else Vector((1, 0, 0))
    x = ref - n * n.dot(ref)
    if x.length < 1e-4:
        x = n.orthogonal()
    x.normalize()
    if rot_deg:
        x = Matrix.Rotation(math.radians(rot_deg), 3, n) @ x
    return x, n.cross(x)


class Placer:
    def __init__(self, target, offset, index, ship, off, pod_axis):
        bm = bmesh.new()
        bm.from_mesh(target.data)
        bm.transform(target.matrix_world)
        self.tree = BVHTree.FromBMesh(bm)
        bm.free()
        self.offset = offset
        self.index = index
        self.off = Vector(off)
        self.pod = pod_axis                     # (y, z) of the port pod axis, layout
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.count = {"decals": 0, "paint": 0, "ribbons": 0, "misses": 0, "skipped": 0}

    # ------------------------------------------------------------------ rays
    def ray(self, spec, side):
        """Layout ray (origin, direction) for a placement, side +1 port / -1 starboard."""
        on = spec["on"]
        if on == "pod":
            a = math.radians(spec["deg"] if side > 0 else 180.0 - spec["deg"])
            yc, zc = self.pod[0] * side, self.pod[1]
            radial = Vector((0.0, math.cos(a), math.sin(a)))
            return Vector((spec["x"], yc, zc)) + radial * 3.0, -radial
        if on == "side":
            return Vector((spec["x"], 10.0 * side, spec["z"])), Vector((0, -side, 0))
        if on in ("top", "bottom"):
            s = 1 if on == "top" else -1
            return Vector((spec["x"], spec.get("y", 0.0) * side, 10.0 * s)), Vector((0, 0, -s))
        if on == "ray":
            at, d = Vector(spec["at"]), Vector(spec["dir"]).normalized()
            at.y *= side
            d.y *= side
            return at - d * 3.0, d
        raise ValueError(on)

    def cast(self, origin, d):
        hit, n, _, dist = self.tree.ray_cast(origin + self.off, d, 20.0)
        return (hit, n.normalized()) if hit is not None else (None, None)

    def lay(self, p, n, reach=0.12):
        """A point of a quad grid laid back onto the hull along n; None when the hull is not there (the
        decal would hang off an edge)."""
        hit, hn = self.cast(p - self.off + n * reach, -n)
        if hit is None or (hit - p).length > reach * 1.5:
            return None, None
        return hit + hn * self.offset, hn

    # ------------------------------------------------------------------ geometry
    def laid_grid(self, centre, n, x, y, w, h, grid_m):
        """Grid points laid onto the hull, or None if the footprint leaves the surface or crosses an edge
        (a normal more than 30 deg off the centre's): such a decal would fold or hang in the air."""
        nx, ny = max(1, int(math.ceil(w / grid_m))), max(1, int(math.ceil(h / grid_m)))
        pts = []
        for j in range(ny + 1):
            row = []
            for i in range(nx + 1):
                s, t = i / nx, j / ny
                q, qn = self.lay(centre + x * ((s - 0.5) * w) + y * ((t - 0.5) * h), n)
                if q is None or qn.dot(n) < math.cos(math.radians(30)):
                    return None
                row.append((q, qn, s, t))
            pts.append(row)
        return pts

    def grid(self, pts, n, uv_rect, slot, lift):
        verts = [[(self.bm.verts.new(q + qn * lift), s, t) for q, qn, s, t in row] for row in pts]
        ny, nx = len(verts) - 1, len(verts[0]) - 1
        u0, v0, u1, v1 = uv_rect
        for j in range(ny):
            for i in range(nx):
                quad = [verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]]
                f = self.bm.faces.new([q[0] for q in quad])
                f.material_index = slot
                f.smooth = True
                for loop, (_, s, t) in zip(f.loops, quad):
                    u = u0 + (u1 - u0) * s
                    loop[self.uv].uv = (u, v0 + (v1 - v0) * t)
                if f.normal.dot(n) < 0:
                    f.normal_flip()

    def decal(self, spec, side, grid_m):
        item = self.index["decals"][spec["item"]]
        origin, d = self.ray(spec, side)
        hit, n = self.cast(origin, d)
        if hit is None:
            self.count["misses"] += 1
            print("HSDECALS miss %s at %s" % (spec["item"], spec))
            return
        x, y = _frame(n, spec.get("rot", 0.0))
        w, h = (v * spec.get("scale", 1.0) for v in item["size_m"])
        pts = self.laid_grid(hit, n, x, y, w, h, grid_m)
        if pts is None:
            self.count["skipped"] += 1
            print("HSDECALS skipped %s (crosses an edge) at %s side %d" % (spec["item"], {k: v for k, v in spec.items() if k[0] != "_"}, side))
            return
        self.grid(pts, n, item["uv"], 0, 0.0)
        self.count["decals"] += 1
        if item.get("has_color"):
            self.grid(pts, n, item["uv"], 1, 0.0008)
            self.count["paint"] += 1

    def ribbon(self, spec, side, grid_m):
        strip = self.index["trim"][spec["strip"]]
        h = strip["height_m"] * spec.get("scale", 1.0)
        tile = strip["tile_m"]
        pts = []
        if spec["on"] == "pod_ring":
            a0, a1 = spec["deg"]
            n_seg = max(8, int(abs(a1 - a0) / 3))
            for k in range(n_seg + 1):
                a = a0 + (a1 - a0) * k / n_seg
                pts.append(self.ray({"on": "pod", "x": spec["x"], "deg": a}, side))
        elif spec["on"] == "pod_line":
            x0, x1 = spec["x"]
            n_seg = max(4, int((x1 - x0) / grid_m))
            for k in range(n_seg + 1):
                pts.append(self.ray({"on": "pod", "x": x0 + (x1 - x0) * k / n_seg, "deg": spec["deg"]}, side))
        elif spec["on"] in ("top_cross", "bottom_cross"):
            y0, y1 = spec["y"]
            n_seg = max(4, int(abs(y1 - y0) / grid_m))
            for k in range(n_seg + 1):
                pts.append(self.ray({"on": "top" if spec["on"] == "top_cross" else "bottom", "x": spec["x"],
                                     "y": y0 + (y1 - y0) * k / n_seg}, 1))
        elif spec["on"] == "ray_line":
            # a polyline of layout points, each sample cast along "dir" (e.g. the outline of the rear ramp)
            poly = [Vector(p) for p in spec["points"]]
            d = Vector(spec["dir"]).normalized()
            for a, b in zip(poly, poly[1:]):
                n_seg = max(1, int((b - a).length / grid_m))
                for k in range(n_seg):
                    pts.append((a + (b - a) * (k / n_seg) - d * 2.0, d))
            pts.append((poly[-1] - d * 2.0, d))
        else:
            raise ValueError(spec["on"])
        # the path breaks where the hull is not continuous under it (a jump or a bend over 35 deg, e.g.
        # off the edge of the roof): each continuous run is its own ribbon
        runs, run = [], []
        spacing = None
        for o, d in pts:
            p, n = self.cast(o, d)
            if p is not None and run:
                step = (p - run[-1][0]).length
                spacing = spacing or step
                if step > max(spacing, 0.02) * 3 or n.dot(run[-1][1]) < math.cos(math.radians(35)):
                    runs.append(run)
                    run = []
            if p is None:
                if run:
                    runs.append(run)
                run = []
                continue
            run.append((p, n))
        runs.append(run)
        runs = [r for r in runs if len(r) >= 2]
        if not runs:
            self.count["misses"] += 1
            return
        for hits in runs:
            self._ribbon_run(hits, strip, h, tile)

    def _ribbon_run(self, hits, strip, h, tile):
        # a strip of quads: across = in-surface perpendicular to the path, U = distance / tile
        dist = [0.0]
        for (a, _), (b, _) in zip(hits, hits[1:]):
            dist.append(dist[-1] + (b - a).length)
        v0, v1 = strip["v"]
        for slot, lift in ((2, 0.0), (3, 0.0008)) if strip.get("has_color") else ((2, 0.0),):
            rows = []
            for k, (p, n) in enumerate(hits):
                t = (hits[min(k + 1, len(hits) - 1)][0] - hits[max(k - 1, 0)][0]).normalized()
                across = n.cross(t).normalized()
                row = []
                for s in (-0.5, 0.5):
                    q = p + across * (s * h) + n * (self.offset + lift)
                    q2, qn = self.lay(q - n * self.offset, n)
                    if q2 is None:
                        q2, qn = q - n * lift, n
                    row.append(self.bm.verts.new(q2 + qn * lift))
                rows.append((row, dist[k] / tile, n))
            for (ra, ua, na), (rb, ub, _) in zip(rows, rows[1:]):
                f = self.bm.faces.new([ra[0], rb[0], rb[1], ra[1]])
                f.material_index = slot
                f.smooth = True
                for loop, uv in zip(f.loops, ((ua, v0), (ub, v0), (ub, v1), (ua, v1))):
                    loop[self.uv].uv = uv
                if f.normal.dot(na) < 0:
                    f.normal_flip()
        self.count["ribbons"] += 1


def build(recipe, target, ship, off, root):
    """Returns the Decals object (ship coordinates) or None."""
    spec = recipe.get("decals")
    if not spec:
        return None, {}
    index = json.load(open(os.path.join(root, spec["index"]), encoding="utf-8"))
    rev = recipe["parts"]["pod"]["revolve"]["axis"]
    pl = Placer(target, spec.get("offset_m", 0.002), index, ship, off, (rev["y"], rev["z"]))
    grid_m = spec.get("grid_m", 0.06)
    for it in spec.get("items", []):
        along = it.get("along")
        for k in range(along["count"] if along else 1):
            one = dict(it)
            if along and "at" in it:
                one["at"] = [it["at"][0] + along["step"] * k] + list(it["at"][1:])
            elif along:
                one["x"] = it["x"] + along["step"] * k
            for side in ((1, -1) if it.get("mirror", True) else (1,)):
                pl.decal(one, side, grid_m)
    for tr in spec.get("trim", []):
        for side in ((1, -1) if tr.get("mirror", True) and tr["on"].startswith("pod") else (1,)):
            pl.ribbon(tr, side, grid_m)
    name = "SM_Ship_%s_Decals" % ship
    me = bpy.data.meshes.new(name)
    pl.bm.to_mesh(me)
    pl.bm.free()
    for slot in SLOTS:
        m = bpy.data.materials.get("M_Ship_%s_%s" % (ship, slot)) or bpy.data.materials.new("M_Ship_%s_%s" % (ship, slot))
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, pl.count
