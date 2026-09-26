"""A light for every light fixture (26. 9. 2026, from the SC breakdown: the C2 carries ~790 lights, 74 on the
bridge and 160 in the hold - every strip, ring and lamp lights its surroundings; we had 35 room lights with a 5 m
reach for the whole ship). starcitizenreference/ShipDetailing_VideoNotes.md, chapter 6.

fixture_lights(objs, mats, spec, lights_out): finds the islands of the emissive materials named in spec
["materials"] ({material key: {"color": [r, g, b], "cd_per_m": .., "min_len_m": ..}}), measures each along its
long axis (PCA) and puts point lights along it every seg_m: short reach (radius_m), no shadow (the importer's
interior lights never cast one), low specular. Each light sits off the strip on its open side (rays along the
strip's thin axis into the rest of the interior pick the side with more room), push_m out at most: a light
millimetres from its mounting surface burns a white spot into it (inverse square).
Returns a report: counts by material, lights dropped over max_lights.
"""
import math

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


def _islands(bm, faces):
    faces = set(faces)
    seen, out = set(), []
    for f in faces:
        if f in seen:
            continue
        stack, isl = [f], []
        seen.add(f)
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h in faces and h not in seen:
                        seen.add(h)
                        stack.append(h)
        out.append(isl)
    return out


def _axes(points):
    """Centroid and the principal axes (long, middle, thin) of a point set, with the extents along them."""
    n = len(points)
    c = sum(points, Vector()) / n
    cov = Matrix(((0.0,) * 3,) * 3)
    for p in points:
        d = p - c
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    # power iteration for the long axis, then the rest in its orthogonal plane
    def dominant(m, guess):
        v = guess.normalized()
        for _ in range(40):
            w = m @ v
            if w.length < 1e-12:
                break
            v = w.normalized()
        return v
    a = dominant(cov, Vector((1.0, 0.3, 0.1)))
    proj = Matrix.Identity(3) - Matrix(((a.x * a.x, a.x * a.y, a.x * a.z), (a.y * a.x, a.y * a.y, a.y * a.z),
                                        (a.z * a.x, a.z * a.y, a.z * a.z)))
    b = dominant(proj @ cov @ proj, a.orthogonal())
    t = a.cross(b).normalized()
    ext = []
    for ax in (a, b, t):
        s = [(p - c).dot(ax) for p in points]
        ext.append((min(s), max(s)))
    return c, (a, b, t), ext


def fixture_lights(objs, mats, spec, lights_out):
    kinds = {mats[k]: (k, v) for k, v in spec.get("materials", {}).items() if k in mats}
    seg = spec.get("seg_m", 0.9)
    push = spec.get("push_m", 0.12)
    radius = spec.get("radius_m", 1.6)
    max_lights = spec.get("max_lights", 140)
    # the interior as one tree, for the open-side test
    whole = bmesh.new()
    for ob in objs:
        if ob.type != "MESH" or not ob.data.polygons:
            continue
        tmp = bmesh.new()
        tmp.from_mesh(ob.data)
        tmp.transform(ob.matrix_world)
        me = ob.data.copy()
        tmp.to_mesh(me)
        tmp.free()
        whole.from_mesh(me)
        import bpy
        bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(whole)
    whole.free()
    made, report = [], {}
    for ob in objs:
        if ob.type != "MESH":
            continue
        slots = {i: kinds[m] for i, m in enumerate(ob.data.materials) if m in kinds}
        if not slots:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        for idx, (key, kv) in slots.items():
            faces = [f for f in bm.faces if f.material_index == idx]
            for isl in _islands(bm, faces):
                pts = list({v.co.copy().freeze() for f in isl for v in f.verts})
                if len(pts) < 3:
                    continue
                c, (a, b, t), ext = _axes([Vector(p) for p in pts])
                length = ext[0][1] - ext[0][0]
                if length < kv.get("min_len_m", spec.get("min_len_m", 0.25)):
                    continue
                mid = c + a * ((ext[0][0] + ext[0][1]) / 2)
                # open side along the thin axis (for a tube the middle axis is as good)
                best, room = None, -1.0
                for d in (t, -t, b, -b):
                    start = mid + d * ((ext[2][1] - ext[2][0]) / 2 + 0.002)
                    hit = tree.ray_cast(start, d, 2.0)[0]
                    free = 2.0 if hit is None else (hit - start).length
                    if free > room + 0.02:
                        best, room = d, free
                k = max(1, int(round(length / seg)))
                off = best * min(push, room * 0.5)
                for i in range(k):
                    p = mid + a * (((i + 0.5) / k - 0.5) * length) + off
                    made.append({"at": [round(p.x, 4), round(p.y, 4), round(p.z, 4)], "type": "point",
                                 "cd": round(kv["cd_per_m"] * length / k, 3), "color": kv["color"],
                                 "radius_m": kv.get("radius_m", radius), "source_radius_cm": 1.0,
                                 "specular": kv.get("specular", 0.2), "_fixture": key})
                report[key] = report.get(key, 0) + k
        bm.free()
    dropped = max(0, len(made) - max_lights)
    if dropped:
        # keep the strongest (longest runs) when over the budget
        made.sort(key=lambda l: -l["cd"])
        made = made[:max_lights]
    lights_out.extend(made)
    return {"lights": len(made), "by_material": report, "dropped": dropped}
