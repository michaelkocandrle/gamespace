"""Vertex-colour masks for the layered ship material (M_Ship_Layered, Tools/Assets/ship_materials.py),
called by hs_assemble_ship.py on the joined main mesh (skill ship-pipeline 3b3, step 5).

    R  ambient occlusion: cosine-weighted rays over the hemisphere, "ao_distance_m" long (contact shadow of
       plates, recesses, pipes, greebles), 1 = open
    G  1 - edge: convex edges (a bevel's middle vertices, where the paint chips first) are 0; only vertices
       whose faces are all smaller than "edge_max_face_m2" count (vertex colour spreads over every face a
       vertex touches); white means no edge, so a mesh without vertex colours shows no wear
    B  1 - secondary paint: faces with attribute "paint2" (hs_detail.py) are 0
    A  how much of the layering applies: 1 inside "region" (the pilot), 0 elsewhere, so the rest of the ship
       keeps the clean look until the pilot is approved

Written as a point-domain float colour "Col"; the FBX exporter stores it as sRGB bytes and Unreal's
VertexColor node gives the linear values back.
"""
import math
import random

import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _hemisphere(n, count, rng):
    t = n.orthogonal().normalized()
    b = n.cross(t)
    dirs = []
    for k in range(count):
        # stratified cosine-weighted directions
        u = (k + rng.random()) / count
        a = 2 * math.pi * ((k * 0.618034) % 1.0)
        r = math.sqrt(u)
        dirs.append((t * (r * math.cos(a)) + b * (r * math.sin(a)) + n * math.sqrt(max(0.0, 1 - u))).normalized())
    return dirs


def bake(ob, spec, off):
    """ob: the joined main mesh in ship coordinates. spec: recipe "layers". off: the assemble offset
    (layout -> ship), for the region given in layout x."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    x0, x1 = (v + off[0] for v in spec["region_x"])
    rays = spec.get("ao_rays", 24)
    dist = spec.get("ao_distance_m", 0.5)
    e0, e1 = spec.get("edge", [0.28, 0.45])
    max_area = spec.get("edge_max_face_m2", 0.02)
    rng = random.Random(7)
    p2_layer = bm.faces.layers.int.get("paint2")
    n_verts = len(bm.verts)
    cols = [(1.0, 1.0, 1.0, 0.0)] * n_verts
    inside = 0
    for v in bm.verts:
        if not (x0 <= v.co.x <= x1):
            continue
        inside += 1
        n = v.normal
        if n.length < 0.5:
            cols[v.index] = (1.0, 1.0, 1.0, 1.0)
            continue
        # occlusion
        o = v.co + n * 0.003
        hit = 0
        for d in _hemisphere(n, rays, rng):
            if tree.ray_cast(o, d, dist)[0] is not None:
                hit += 1
        ao = 1.0 - hit / rays
        # convexity: how far the neighbours fall below the tangent plane. Only for vertices surrounded by
        # small faces (a bevel's middle row): a vertex colour spreads over every face it touches, so an
        # edge value on the corner of a big face washed the whole face (fins, thin shell floors)
        low = 0.0
        if max((f.calc_area() for f in v.link_faces), default=1.0) > max_area:
            e_iter = ()
        else:
            e_iter = v.link_edges
        for e in e_iter:
            w = e.other_vert(v).co - v.co
            if w.length > 1e-6:
                low = min(low, w.normalized().dot(n))
        edge = min(1.0, max(0.0, (-low - e0) / (e1 - e0)))
        p2 = 0.0
        if p2_layer is not None and v.link_faces:
            p2 = sum(f[p2_layer] for f in v.link_faces) / len(v.link_faces)
        cols[v.index] = (ao, 1.0 - edge, 1.0 - p2, 1.0)
    bm.free()
    attr = me.color_attributes.get("Col") or me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    flat = [c for col in cols for c in col]
    attr.data.foreach_set("color", flat)
    me.color_attributes.active_color = attr
    return {"vertices": n_verts, "in_region": inside, "rays": rays}
