"""The rear ramp as a moving part (variant A, author 10. 10. 2026; plan Docs/Reviews/2026-10-06_ramp_plan.md).

One leaf hinged at its foot: closed it IS the stern (the hull's side outline ends in the leaf's outer line), open it
lies on the ground at ~31 degrees and is walked on its inner face. Recipe interior.ramp:

  {"hinge": [x, z], "top": [x, z], "half": m, "t": m, "open_deg": deg}   layout metres (x along the ship, z up)

  - interior(g, H): the passage from the stern to the hold (room "ramp" of the layout): floor, side walls whose aft
    edge follows the stern line, a ceiling and a header over the opening, jamb strips where the hull is cut
  - leaf(ship, coll, mats): the leaf's inner structure (deck plate, treads, kerbs, hazard edges, hinge knuckles) as
    objects SM_Ship_<Ship>_RampLeaf_<material>; hs_assemble_ship groups them into the part RampLeaf
  - sockets(): Ramp_hinge (a point on the hinge axis), Ramp_tip (the leaf's free edge, closed), Control_ramp (the
    switch inside the passage), Ramp_out (where a walker steps off the open ramp)
  - split(objs, off, spec): in hs_assemble_ship, after the decals - every face of the finished exterior (hull, kit,
    parts, decals) inside the leaf's slab moves to RampLeaf / RampDecals, cut cleanly at the slab's edges

The game turns the parts RampLeaf and RampDecals about Ramp_hinge (ASpaceshipPawn / UShipBoardingComponent).
"""
import math

import bmesh
import bpy
from mathutils import Vector


class Ramp:
    def __init__(self, spec):
        self.h = Vector((spec["hinge"][0], 0.0, spec["hinge"][1]))
        top = Vector((spec["top"][0], 0.0, spec["top"][1]))
        d = top - self.h
        self.length = d.length
        self.u = d.normalized()                                  # up the leaf (closed)
        self.n = Vector((self.u.z, 0.0, -self.u.x))              # into the ship, normal to the leaf
        self.half = spec.get("half", 1.1)
        self.t = spec.get("t", 0.12)
        self.open_deg = spec.get("open_deg", 130.0)

    def p(self, s, t, y=0.0):
        """Layout point at s along the leaf, t into the ship from its outer face, y across."""
        q = self.h + self.u * s + self.n * t
        return Vector((q.x, y, q.z))

    def skin_x(self, z):
        """x of the leaf's outer line (the stern) at height z."""
        return self.h.x + self.u.x / self.u.z * (z - self.h.z)

    def inner_x(self, z):
        return self.skin_x(z) + self.t / self.u.z


def _quad_box(bm, corners, depth_dir, depth):
    """A slab from four corners (one face) pushed depth along depth_dir."""
    vs = [bm.verts.new(c) for c in corners] + [bm.verts.new(c + depth_dir * depth) for c in corners]
    bm.faces.new(vs[:4])
    bm.faces.new(list(reversed(vs[4:])))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[i], vs[j], vs[4 + j], vs[4 + i]))


def interior(g, box, r, H):
    """The passage (layout room "ramp", x 0 .. the hold's portal at 1.0)."""
    x1 = 1.0
    hw = r.half
    # floor from the hinge to the portal (closed, its first 10 cm sits under the leaf, hidden)
    box(g["int_dark"], (r.h.x + 0.02, -hw, -0.07), (x1, hw, -0.03))
    nt = 3
    for j in range(nt):
        ya, yb = -hw + 2 * hw * j / nt, -hw + 2 * hw * (j + 1) / nt
        box(g["int_floor"], (r.h.x + 0.035, ya + 0.005, -0.03), (x1, yb - 0.005, 0.0))
    # side walls, their aft edge on the stern line (the jamb where the hull is cut), lower band and panel as the hold
    zc = H                                                  # the passage's ceiling
    for sgn in (1, -1):
        for key, za, zb in (("int_wall", 0.0, 1.1), ("int_panel", 1.11, zc)):
            bm = g[key]
            yi, yo = sgn * hw, sgn * (hw + 0.04)
            pts = [(r.skin_x(za) + 0.025, za), (x1, za), (x1, zb), (r.skin_x(zb) + 0.025, zb)]   # 2.5 cm in: the lofted skin strays ~2 cm off the line
            vs = [bm.verts.new((x, yy, z)) for yy in (yi, yo) for (x, z) in pts]
            bm.faces.new(vs[:4] if sgn < 0 else list(reversed(vs[:4])))
            bm.faces.new(list(reversed(vs[4:])) if sgn < 0 else vs[4:])
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new((vs[i], vs[j], vs[4 + j], vs[4 + i]))
        # a hazard strip down the jamb, a trim at the wall's foot
        for i in range(10):
            za, zb = 0.1 + i * 0.2, 0.1 + i * 0.2 + 0.1
            xa = r.skin_x(za) + 0.01
            box(g["accent"], (xa, min(sgn * hw, sgn * (hw - 0.006)), za), (xa + 0.06, max(sgn * hw, sgn * (hw - 0.006)), zb))
        box(g["int_trim"], (r.skin_x(0.0) + 0.02, min(sgn * hw, sgn * (hw - 0.03)), 0.0), (x1, max(sgn * hw, sgn * (hw - 0.03)), 0.08))
    # ceiling from the leaf's inner face (closed) to the portal, a header down to it from the hull's roof
    xc = r.inner_x(zc) + 0.01
    box(g["int_panel"], (xc, -hw, zc), (x1, hw, zc + 0.04))
    box(g["int_dark"], (xc, -hw - 0.04, zc + 0.04), (x1, hw + 0.04, zc + 0.08))
    top = r.p(r.length, 0.0)
    box(g["int_trim"], (xc, -hw - 0.04, zc - 0.08), (xc + 0.06, hw + 0.04, top.z + 0.02))
    box(g["accent"], (xc - 0.004, -hw + 0.1, zc - 0.07), (xc, hw - 0.1, zc - 0.03))
    # a light over the passage
    box(g["int_light"], (0.6, -0.5, zc - 0.012), (0.9, 0.5, zc))


def leaf(r, ship, coll, mats, finish):
    """The leaf's inner side (closed: facing the passage; open: the walked deck)."""
    groups = {}

    def bm(key):
        if key not in groups:
            groups[key] = bmesh.new()
        return groups[key]

    hw = r.half - 0.015
    L = r.length
    across = Vector((0.0, 1.0, 0.0))
    # the deck plate: from just inside the outer skin to the inner face
    _quad_box(bm("int_dark"), [r.p(0.02, 0.006, -hw), r.p(0.02, 0.006, hw), r.p(L - 0.01, 0.006, hw), r.p(L - 0.01, 0.006, -hw)],
              r.n, r.t - 0.025)
    _quad_box(bm("int_floor"), [r.p(0.06, r.t - 0.02, -hw + 0.08), r.p(0.06, r.t - 0.02, hw - 0.08),
                                r.p(L - 0.08, r.t - 0.02, hw - 0.08), r.p(L - 0.08, r.t - 0.02, -hw + 0.08)], r.n, 0.02)
    # treads across the deck every 0.28 m
    k = 0
    s = 0.25
    while s < L - 0.2:
        _quad_box(bm("int_rubber"),
                  [r.p(s, r.t, -hw + 0.12), r.p(s, r.t, hw - 0.12), r.p(s + 0.05, r.t, hw - 0.12), r.p(s + 0.05, r.t, -hw + 0.12)],
                  r.n, 0.012)
        s += 0.28
        k += 1
    # kerbs along both edges, hazard bands on their faces
    for sgn in (1, -1):
        ya, yb = sorted((sgn * hw, sgn * (hw - 0.07)))
        _quad_box(bm("int_trim"), [r.p(0.03, r.t - 0.005, ya), r.p(0.03, r.t - 0.005, yb), r.p(L - 0.02, r.t - 0.005, yb),
                                   r.p(L - 0.02, r.t - 0.005, ya)], r.n, 0.05)
        for i in range(int((L - 0.2) / 0.3)):
            sa = 0.1 + i * 0.3
            ya2, yb2 = sorted((sgn * (hw - 0.071), sgn * (hw - 0.073)))
            _quad_box(bm("accent"), [r.p(sa, r.t + 0.005, ya2), r.p(sa, r.t + 0.005, yb2), r.p(sa + 0.15, r.t + 0.005, yb2),
                                     r.p(sa + 0.15, r.t + 0.005, ya2)], r.n, 0.035)
    # the lip at the free edge (lands on the ground when open)
    _quad_box(bm("int_rubber"),
              [r.p(L - 0.06, 0.0, -hw), r.p(L - 0.06, 0.0, hw), r.p(L - 0.01, 0.0, hw), r.p(L - 0.01, 0.0, -hw)], r.n, r.t + 0.01)
    # hinge knuckles at the foot: on the leaf every other one (the hull keeps the rest, F-RAMP-HINGE)
    import hs_interior as hi
    c = r.h + r.n * 0.04
    for i in range(5):
        y0 = -hw + 0.1 + i * (2 * hw - 0.2) / 4
        hi.cyl(bm("metal"), (c.x, y0 - 0.12, c.z), (c.x, y0 + 0.12, c.z), 0.05, seg=16)
    out = []
    for key, b in groups.items():
        ob = finish(b, "SM_Ship_%s_RampLeaf_%s" % (ship, key), coll, {"angle_deg": 30, "width": 0.003, "segments": 1})
        ob.data.materials.append(mats[key])
        out.append(ob)
    return out


def sockets(r):
    open_tip = r.h + _rot(r.u, r.open_deg) * r.length
    return {
        "Ramp_hinge": r.h.copy(),
        "Ramp_tip": r.p(r.length, r.t),
        "Control_ramp": Vector((0.85, -(r.half - 0.06), 1.3)),
        "Ramp_out": Vector((open_tip.x - 0.8, 0.0, open_tip.z + 0.1)),
    }


def _rot(v, deg):
    """v (x, z in the ship's side plane) turned by deg about +y the way the leaf opens (aft and down)."""
    a = math.radians(deg)
    x, z = v.x, v.z
    return Vector((x * math.cos(a) - z * math.sin(a), 0.0, x * math.sin(a) + z * math.cos(a)))


def split(out, off, spec):
    """Move every exterior face inside the leaf's slab from the hull part ("") and the decals ("Decals") into
    RampLeaf / RampDecals (objects in ship coordinates: layout + off)."""
    r = Ramp(spec)
    o = Vector(off)
    hinge = r.h + o
    s_max = r.length
    t_out, t_in = -spec.get("reach_out", 0.45), r.t + 0.005

    def st(co):
        d = co - hinge
        return d.x * r.u.x + d.z * r.u.z, d.x * r.n.x + d.z * r.n.z

    def inside(co):
        s, t = st(co)
        return -0.06 <= s <= s_max and t_out <= t <= t_in and abs(co.y) <= r.half

    moved = {}
    for src, dst in (("", "RampLeaf"), ("Decals", "RampDecals")):
        ob = out.get(src)
        if ob is None:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        slab = [f for f in bm.faces if any(inside(v.co) for v in f.verts) or inside(f.calc_center_median())]
        if not slab:
            bm.free()
            continue
        if src == "":
            # clean edges: the leaf's sides and its top (decals are only taken whole)
            geom = list({e for f in slab for e in f.edges}) + slab + list({v for f in slab for v in f.verts})
            for y in (-r.half, r.half):
                res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector((0, y, 0)), plane_no=Vector((0, 1, 0)))
                geom = [x for x in bm.verts[:] + bm.edges[:] + bm.faces[:] if x.is_valid]
            top = hinge + r.u * s_max
            bmesh.ops.bisect_plane(bm, geom=[x for x in bm.verts[:] + bm.edges[:] + bm.faces[:] if x.is_valid], dist=1e-5,
                                   plane_co=top, plane_no=Vector((r.u.x, 0, r.u.z)))
        take = [f for f in bm.faces if inside(f.calc_center_median())]
        nb = bmesh.new()
        vmap = {}
        lay_src = bm.loops.layers.uv.active
        lay_dst = nb.loops.layers.uv.new(lay_src.name) if lay_src is not None else None
        for f in take:
            vs = []
            for v in f.verts:
                if v.index not in vmap or not vmap[v.index].is_valid:
                    vmap[v.index] = nb.verts.new(v.co)
                vs.append(vmap[v.index])
            try:
                nf = nb.faces.new(vs)
            except ValueError:
                continue
            nf.material_index = f.material_index
            nf.smooth = f.smooth
            if lay_dst is not None:
                for la, lb in zip(f.loops, nf.loops):
                    lb[lay_dst].uv = la[lay_src].uv
        bm.verts.index_update()
        bmesh.ops.delete(bm, geom=take, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
        me = bpy.data.meshes.new("%s_%s" % (out[""].name, dst))       # SM_Ship_<Ship>_<part>
        nb.to_mesh(me)
        nb.free()
        for m in ob.data.materials:
            me.materials.append(m)
        new = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(new)
        if dst in out:
            # join into the leaf's inner side (hs_ramp.leaf, grouped as RampLeaf already)
            bpy.ops.object.select_all(action="DESELECT")
            out[dst].select_set(True)
            new.select_set(True)
            bpy.context.view_layer.objects.active = out[dst]
            bpy.ops.object.join()
            bpy.ops.object.material_slot_remove_unused()
        else:
            out[dst] = new
        moved[dst] = len(take)
    return moved
