"""The exterior kit on the ship from the approved drawings (author 1. 10. 2026), called by hs_build_ship.py after the
detail layer and before the lights, greebles and decals (they then land on the plates).

Input: the kit layout Tools/Design/exterior_kit_layout.py writes from the drawing model (recipe "exterior_kit"
{"layout": path}): outlines in a view's plane with their cut-outs - SB (x, z) for the side bands (mirrored to port),
TOP (x, y) for the roof, AFT (y, z) for the aft wall.

  plates, frame   the hull faces under the outline (cut exactly along it: bisect planes through every edge in the
                  view direction, then the faces whose centre projects inside), copied, solidified outwards by the
                  kit's thickness, bevelled; one object per ID (the layered paint gives every object its own panel
                  tone, hs_layers.panel_ids); plates in the primary paint or the secondary (face attribute paint2),
                  the frame gunmetal with its T profile's web ("cap", higher) on top; bolts (short cylinders on the
                  face) where the layout has them; the hatches' latches
  skin            the hull skin under the plates of the region turns the channel colour (darker than the frame)
  parts           XK-RCS blocks on the pods, strobe housings with a steady position lens and a strobe lens (slot
                  "Strobe": the game flashes it, UShipPresentationComponent), the ramp work light (a spot in
                  hs_lights), the ramp cylinders with clevis brackets and hoses, the ramp hinge
Prints HSKIT {...}.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import hs_build_part as hp

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MIRROR_Y = Matrix.Scale(-1.0, 4, (0.0, 1.0, 0.0))


def _path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


# ------------------------------------------------------------------------------------------------ view planes
def to2d(view, co):
    """A 3D point to the view's plane."""
    if view == "SB":
        return co.x, co.z
    if view == "TOP":
        return co.x, co.y
    return co.y, co.z                                       # AFT


def plane_of(view, a, b):
    """The plane through the outline edge a-b that contains the view direction: (point, normal)."""
    (u0, v0), (u1, v1) = a, b
    du, dv = u1 - u0, v1 - v0
    n2 = (dv, -du)
    if view == "SB":
        return Vector((u0, 0.0, v0)), Vector((n2[0], 0.0, n2[1])).normalized()
    if view == "TOP":
        return Vector((u0, v0, 0.0)), Vector((n2[0], n2[1], 0.0)).normalized()
    return Vector((0.0, u0, v0)), Vector((0.0, n2[0], n2[1])).normalized()


def inside(pt, ring):
    """Point in polygon (even-odd)."""
    x, y = pt
    c = False
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def in_polys(pt, polys):
    return any(inside(pt, outer) and not any(inside(pt, h) for h in holes) for outer, holes in polys)


def frame_cover(layout_path):
    """Predicate: is a hull point under the kit's frame (ribs, longerons, spine)? The loft then builds no seam groove
    there - the frame covers it (triangle budget rule, author 1. 10. 2026). Side outlines (SB, mirrored) test (x, z),
    plan outlines (TOP) test (x, y) of the upper half."""
    try:
        kit = json.load(open(_path(layout_path), encoding="utf-8"))
    except OSError:
        return None
    side = [e["polys"] for e in kit.get("frame", []) if e["id"].startswith("FR-") and e["view"] == "SB"]
    top = [e["polys"] for e in kit.get("frame", []) if e["id"].startswith("FR-") and e["view"] == "TOP"]
    boxes = [(bbox2(p, 0.01), p) for p in side], [(bbox2(p, 0.01), p) for p in top]

    def hit(pt, entries):
        return any(b[0] <= pt[0] <= b[2] and b[1] <= pt[1] <= b[3] and in_polys(pt, p) for b, p in entries)

    def covered(co, z_mid):
        return hit((co[0], co[2]), boxes[0]) or (co[2] > z_mid and hit((co[0], co[1]), boxes[1]))
    return covered


def dissolve_planar(bm, deg=1.0):
    """Merge coplanar faces (within deg, never across materials) before solidify and bevel: the kit's plates and
    frame are copies of the finely divided hull and the modifiers multiplied every face (rule B1 of the triangle
    budget, author 1. 10. 2026)."""
    hp.planar_merge(bm, deg)


def seg_for(r):
    """Sides of a cylinder by its diameter (rule B3): under 50 mm 8, up to 150 mm 12, above 16."""
    d = 2 * r
    return 8 if d < 0.05 else (12 if d <= 0.15 else 16)


def normal_ok(n, flt, slack=0.0):
    if "ny_max" in flt and n.y > flt["ny_max"] + slack:
        return False
    if "nz_min" in flt and n.z < flt["nz_min"] - slack:
        return False
    if "nx_max" in flt and n.x > flt["nx_max"] + slack:
        return False
    return True


def bbox2(polys, m=0.0):
    us = [p[0] for outer, _ in polys for p in outer]
    vs = [p[1] for outer, _ in polys for p in outer]
    return min(us) - m, min(vs) - m, max(us) + m, max(vs) + m


def _near(f, view, bb, flt):
    if not normal_ok(f.normal, flt, slack=0.25):
        return False
    pts = [to2d(view, v.co) for v in f.verts]
    us = [p[0] for p in pts]
    vs = [p[1] for p in pts]
    return not (max(us) < bb[0] or min(us) > bb[2] or max(vs) < bb[1] or min(vs) > bb[3])


def cut_faces(hull, entry):
    """A bmesh with the hull faces under the entry's outline, cut exactly along it (starboard / port as the view)."""
    view, polys, flt = entry["view"], entry["polys"], entry.get("normal", {})
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    bm.transform(hull.matrix_world)
    bb = bbox2(polys, 0.15)
    side_ok = (lambda f: f.calc_center_median().y < 0.0) if view == "SB" else (lambda f: True)
    near = [f for f in bm.faces if _near(f, view, bb, flt) and side_ok(f)]
    keep = set(near)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context="FACES")
    for outer, holes in polys:
        for ring in [outer] + holes:
            for i in range(len(ring)):
                a, b = ring[i], ring[(i + 1) % len(ring)]
                if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-5:
                    continue
                co, no = plane_of(view, a, b)
                # only the faces near this edge: the plane is infinite, the outline is not
                lo_u, hi_u = min(a[0], b[0]) - 0.06, max(a[0], b[0]) + 0.06
                lo_v, hi_v = min(a[1], b[1]) - 0.06, max(a[1], b[1]) + 0.06
                geom_f = []
                for f in bm.faces:
                    pts = [to2d(view, v.co) for v in f.verts]
                    if max(p[0] for p in pts) < lo_u or min(p[0] for p in pts) > hi_u or \
                            max(p[1] for p in pts) < lo_v or min(p[1] for p in pts) > hi_v:
                        continue
                    geom_f.append(f)
                if not geom_f:
                    continue
                geom = list({e for f in geom_f for e in list(f.verts) + list(f.edges)} | set(geom_f))
                bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no)
    take = [f for f in bm.faces if normal_ok(f.normal, flt) and in_polys(to2d(view, f.calc_center_median()), polys)]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in set(take)], context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    return bm, len(take)


def fill_grooves(bm, view, tree, reach=0.03, deepest=0.02):
    """Lift the vertices that sit in a hull groove to the surface beside it (kit pilot critic round 1: the hull's seam
    grooves - a V 30 mm wide and 10 mm deep at every seam station, under every rib - left a dip along each rib and
    kept the ribs' web from being cut at all). Samples the hull reach either side along both of the view plane's
    axes; only lifts, and only by less than deepest (a groove, not a step)."""
    if view == "SB":
        d, axes = Vector((0, 1, 0)), (Vector((1, 0, 0)), Vector((0, 0, 1)))
    elif view == "TOP":
        d, axes = Vector((0, 0, -1)), (Vector((1, 0, 0)), Vector((0, 1, 0)))
    else:
        d, axes = Vector((1, 0, 0)), (Vector((0, 1, 0)), Vector((0, 0, 1)))
    out = -d
    moved = 0
    for v in bm.verts:
        co = v.co.copy()
        best = None
        for a in axes:
            hs = []
            for sgn in (-1, 1):
                hit, _, _, _ = tree.ray_cast(co + a * (sgn * reach) + out * 0.5, d, 1.0)
                if hit is None:
                    break
                hs.append(hit.dot(out))
            if len(hs) == 2:
                m = (hs[0] + hs[1]) / 2
                best = m if best is None else max(best, m)
        if best is not None:
            lift = best - co.dot(out)
            if 1e-4 < lift < deepest:
                v.co = co + out * lift
                moved += 1
    bm.normal_update()
    return moved


def mirror_into(bm):
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    dup = bmesh.ops.duplicate(bm, geom=geom)
    verts = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMVert)]
    faces = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMFace)]
    bmesh.ops.transform(bm, matrix=MIRROR_Y, verts=verts)
    bmesh.ops.reverse_faces(bm, faces=faces)


def shell(name, bm, coll, material, t, bevel, paint2=0):
    """The cut faces as a plate: coplanar faces merged, solidified outwards by t, bevelled (1 segment, hardened
    normals)."""
    dissolve_planar(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.data.materials.append(material)
    for poly in ob.data.polygons:
        poly.material_index = 0
    ob.data.shade_smooth()
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness, sol.offset, sol.use_even_offset, sol.use_rim = t, 1.0, True, True
    hp.add_modifiers(ob, {"angle_deg": 30, "width": min(bevel, t * 0.35), "segments": 1}, width=min(bevel, t * 0.35))
    a = ob.data.attributes.get("paint2") or ob.data.attributes.new("paint2", "INT", "FACE")
    a.data.foreach_set("value", [paint2] * len(ob.data.polygons))
    return ob


# ------------------------------------------------------------------------------------------------ small parts
def _box(bm, c, x, y, z, size):
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=res["verts"])
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = c
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def _cyl(bm, a, b, r, seg=None, r2=None):
    """A capped cylinder (or cone to r2); its sides by the diameter (seg_for) - seg is ignored, kept for the
    callers' readability."""
    seg = seg_for(max(r, r2 or 0.0))
    a, b = Vector(a), Vector(b)
    d = b - a
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    m = q.to_matrix().to_4x4()
    m.translation = (a + b) / 2
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def _frame(n):
    """In-surface axes: x along the ship, or across it on a face looking aft / ahead (the ramp light stood 45 deg
    turned when n.orthogonal() chose the axis)."""
    ref = Vector((0, 1, 0)) if abs(n.x) > 0.7 else Vector((1, 0, 0))
    x = ref - n * n.dot(ref)
    if x.length < 1e-3:
        x = n.orthogonal()
    x.normalize()
    return x, n.cross(x)


def _ring(bm, a, ax, x, y, p0, p1, want, seg=16):
    """One band of a surface of revolution about the axis ax through a: from profile point p0 = (r, t) to p1, as
    quads (triangles where r is 0). want = (radial, axial) is the side its faces must show (normals flipped to it)."""
    def ring(r, t):
        if r < 1e-6:
            return [bm.verts.new(a + ax * t)] * seg
        return [bm.verts.new(a + ax * t + (x * math.cos(2 * math.pi * i / seg) + y * math.sin(2 * math.pi * i / seg)) * r)
                for i in range(seg)]
    r0, r1 = ring(*p0), ring(*p1)
    for i in range(seg):
        j = (i + 1) % seg
        vs = [r0[i], r0[j], r1[j], r1[i]]
        uniq = []
        for v in vs:
            if v not in uniq:
                uniq.append(v)
        if len(uniq) < 3:
            continue
        f = bm.faces.new(uniq)
        f.normal_update()
        c = f.calc_center_median()
        rad = (c - a) - ax * (c - a).dot(ax)
        rad = rad.normalized() if rad.length > 1e-6 else Vector()
        if f.normal.dot(rad * want[0] + ax * want[1]) < 0:
            f.normal_flip()


def nozzle(bms, a, ax, d):
    """An RCS nozzle on a block face at a, aimed along ax, exit diameter d: a heat-tinted throat collar, an open bell
    of bare metal with a lip, a sooty dark inside with a recessed bottom (critic round 1: the bells read as flat
    caps)."""
    x, y = _frame(ax)
    ro, L = d / 2, d * 0.55
    _cyl(bms["heat"], a - ax * 0.004, a + ax * 0.022, ro * 0.62, 16)
    _ring(bms["metal"], a, ax, x, y, (ro * 0.55, 0.02), (ro, L), (1, 0))
    _ring(bms["metal"], a, ax, x, y, (ro, L), (ro * 0.84, L), (0, 1))
    _ring(bms["dark"], a, ax, x, y, (ro * 0.84, L), (ro * 0.4, L * 0.35), (-1, 1))
    _ring(bms["dark"], a, ax, x, y, (ro * 0.4, L * 0.35), (0.0, L * 0.35), (0, 1))


def rcs_block(bms, p, n, kp):
    """XK-RCS (concept C, critic round 1): a robust thruster block - a gunmetal housing with a stepped top on a
    mounting plate with eight bolts (sunk into the pod so its curve leaves no gap), five open nozzles in four
    directions: two up, one to each side, one aft."""
    lx, ly, h = kp["size"]
    nd, pt = kp["nozzle_d"], 0.03
    x, y = _frame(n)
    sink = 0.12
    _box(bms["gunmetal"], p + n * ((pt - sink) / 2), x, y, n, (lx + 0.1, ly + 0.1, pt + sink))
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if i == 0 and j == 0:
                continue
            b = p + n * pt + x * (i * (lx / 2 + 0.028)) + y * (j * (ly / 2 + 0.028))
            _cyl(bms["metal"], b - n * 0.002, b + n * 0.012, 0.011, 8)
    hb = h * 0.72
    _box(bms["gunmetal"], p + n * (pt + hb / 2), x, y, n, (lx, ly, hb))
    _box(bms["gunmetal"], p + n * (pt + hb + (h - hb) / 2), x, y, n, (lx - 0.08, ly - 0.08, h - hb))
    top = p + n * (pt + h)
    for i in (-1, 1):
        nozzle(bms, top + x * (i * lx * 0.24), n, nd)
    mid = p + n * (pt + hb * 0.5)
    for j in (-1, 1):
        nozzle(bms, mid + y * (j * ly / 2), y * j, nd * 0.85)
    nozzle(bms, mid - x * (lx / 2), -x, nd * 0.85)
    # a dark service panel on the top step between the nozzles
    _box(bms["dark"], top + n * 0.002, x, y, n, (lx * 0.16, ly * 0.5, 0.004))


def strobe(bms, p, n, size, position):
    """XK-STROBE (critic round 1): a dark housing on a gunmetal foot with a steady position lens (white, red or
    green: slots PosWhite, LightRed, LightGreen) and the strobe lens (slot Strobe: the game flashes it)."""
    lx, ly, h = size
    x, y = _frame(n)
    _box(bms["gunmetal"], p + n * 0.006, x, y, n, (lx + 0.04, ly + 0.03, 0.012))
    _box(bms["dark"], p + n * (0.012 + h * 0.35), x, y, n, (lx, ly, h * 0.7))
    lens = {"white": "pos_white", "red": "light_red", "green": "light_green"}.get(position)
    top = p + n * (0.012 + h * 0.7)
    _box(bms["strobe"], top + n * (h * 0.12) - x * (lx * 0.24), x, y, n, (lx * 0.42, ly * 0.72, h * 0.24))
    if lens:
        _box(bms[lens], top + n * (h * 0.12) + x * (lx * 0.24), x, y, n, (lx * 0.42, ly * 0.72, h * 0.24))


def lamp(bms, p, n, kp):
    """XK-WORKLIGHT (critic round 1: a flat white diamond): a bracket plate with four bolts, a round housing tilted
    25 deg down to the ramp, a hood over it, a metal bezel and a warm lens (slot LightWarm: it glows)."""
    D, _, depth = kp["size"]
    bw, bh, bt = kp["bracket"]
    x, y = _frame(n)
    up = Vector((0, 0, 1))
    _box(bms["gunmetal"], p + n * (bt / 2), x, y, n, (bw, bh, bt))
    for i in (-1, 1):
        for j in (-1, 1):
            b = p + n * bt + x * (i * (bw / 2 - 0.03)) + up * (j * (bh / 2 - 0.03))
            _cyl(bms["metal"], b - n * 0.002, b + n * 0.01, 0.01, 8)
    tilt = math.radians(25.0)
    ax = (n * math.cos(tilt) - up * math.sin(tilt)).normalized()
    a = p + n * bt
    f = a + ax * depth
    _cyl(bms["dark"], a, f, D / 2, 24)
    _ring(bms["metal"], f, ax, *_frame(ax), (D / 2, 0.0), (kp["lens_d"] / 2, 0.0), (0, 1), seg=24)
    _cyl(bms["light_warm"], f - ax * 0.01, f + ax * 0.003, kp["lens_d"] / 2, 24)
    hx, hy = _frame(ax)
    side = hx.cross(ax).normalized()
    if side.dot(up) < 0:
        side = -side
    _box(bms["dark"], a + ax * (depth * 0.55) + side * (D / 2 + 0.006), hx, side.cross(hx).normalized(), side,
         (D * 1.05, depth * 1.1, 0.012))


def piston(bms, base, top, kp, wall_x):
    """XK-PISTON (critic round 1: the rods read as wires): a gunmetal cylinder with metal end rings, a chrome rod,
    eyes in clevis brackets (two cheeks and a base plate with two bolts on the wall or the frame), a pressure hose
    from the cylinder's foot into the wall."""
    base, top = Vector(base), Vector(top)
    d, rod_d = kp["d"], kp["rod_d"]
    bw, bh, bt = kp["bracket"]
    up = (top - base).normalized()
    b0, b1 = base + up * 0.07, base + (top - base) * 0.55
    _cyl(bms["dark"], b0, b1, d / 2, 20)          # dark barrel against the chrome rod (critic round 2)
    for c in (b0, b1):
        _cyl(bms["metal"], c - up * 0.014, c + up * 0.014, d / 2 + 0.008, 20)
    _cyl(bms["metal"], b1 - up * 0.02, top - up * 0.06, rod_d / 2, 16)
    _cyl(bms["metal"], top - up * 0.07, top - up * 0.04, rod_d / 2 + 0.012, 16)
    ex = Vector((1, 0, 0))
    eye_l = 0.07
    for c, wx in ((base, wall_x[0]), (top, wall_x[1])):
        _cyl(bms["metal"], c - Vector((0, eye_l / 2, 0)), c + Vector((0, eye_l / 2, 0)), d * 0.32, 14)
        _cyl(bms["metal"], c - Vector((0, eye_l / 2 + 0.03, 0)), c + Vector((0, eye_l / 2 + 0.03, 0)), 0.014, 8)
        reach = wx - c.x                                   # from the eye to the wall (+x)
        for sgn in (-1, 1):
            cc = Vector((c.x + reach / 2, c.y + sgn * (eye_l / 2 + 0.01), c.z))
            _box(bms["gunmetal"], cc, ex, Vector((0, 1, 0)), Vector((0, 0, 1)), (abs(reach) + 0.05, 0.016, bh * 0.7))
        bc = Vector((wx - bt / 2, c.y, c.z))
        _box(bms["gunmetal"], bc, ex, Vector((0, 1, 0)), Vector((0, 0, 1)), (bt, eye_l + 0.08, bh))
        for k in (-1, 1):
            bb = Vector((wx - bt, c.y, c.z + k * (bh / 2 - 0.025)))
            _cyl(bms["metal"], bb + ex * 0.002, bb - ex * 0.01, 0.011, 8)
    # the hose: out of the cylinder's foot on the outboard side, up beside it, into the wall
    s = 1.0 if base.y > 0 else -1.0
    o = d / 2 + kp["hose_d"]
    pts = [b0 + up * 0.12 + Vector((0, s * (d / 2 - 0.01), 0)),
           b0 + up * 0.16 + Vector((0.02, s * o, 0)),
           b1 - up * 0.12 + Vector((0.02, s * o, 0)),
           Vector((wall_x[0], base.y + s * o, (b1 - up * 0.06).z))]
    for a_, b_ in zip(pts, pts[1:]):
        _cyl(bms["dark"], a_, b_, kp["hose_d"] / 2, 10)
        _cyl(bms["dark"], b_ - (b_ - a_).normalized() * 0.01, b_ + (b_ - a_).normalized() * 0.012,
             kp["hose_d"] / 2 + 0.004, 10)


def hinge(bms, p):
    """XK-HINGE: the ramp door's hinge on its bottom edge - knuckles of bare metal along y on a pin."""
    (y0, y1), z, x, n, L, r = p["y"], p["z"], p["x"], p["count"], p["knuckle"], p["d"] / 2
    gap = (y1 - y0 - n * L) / (n - 1)
    for i in range(n):
        a = y0 + i * (L + gap)
        _cyl(bms["metal"], Vector((x, a, z)), Vector((x, a + L, z)), r, 16)
        for e in (a + 0.006, a + L - 0.006):
            _cyl(bms["gunmetal"], Vector((x, e - 0.006, z)), Vector((x, e + 0.006, z)), r + 0.006, 16)
    _cyl(bms["metal"], Vector((x, y0 - 0.02, z)), Vector((x, y1 + 0.02, z)), p["pin_d"] / 2, 10)


def _tube(bm, pts, r, seg=None):
    """One continuous pipe through the points (rings turned to the local tangent, capped ends): far lighter than a
    capped cylinder per segment (the conduits' first build put the hull over the exporter's 1 M triangle limit)."""
    seg = seg_for(r)
    rings = []
    for i, c in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((0, 1, 0))
        u = (ref - t * t.dot(ref)).normalized()
        v = t.cross(u)
        rings.append([bm.verts.new(c + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a_[k], a_[(k + 1) % seg], b_[(k + 1) % seg], b_[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def conduit(bms, p, ray):
    """XK-CONDUIT (critic round 2: services along the spine, concept B): pipes in the channel between the spine and
    the roof plates, lift above the skin (over the ribs), following the roof; bare-metal band clamps with a foot every
    clamp_pitch, kept off the ribs; at each end of a run the pipe turns down into the skin through a flange."""
    seg = 12
    if p.get("view") == "SB":
        conduit_side(bms, p, ray, seg)
        return
    for run in p["runs"]:
        y, r = run["y"], run["d"] / 2
        x0, x1 = run["x"]
        n = max(2, int((x1 - x0) / 0.3) + 1)
        pts, skin = [], []
        for i in range(n):
            x = x0 + (x1 - x0) * i / (n - 1)
            hit, _ = ray("TOP", x, y)
            if hit is None:
                continue
            skin.append(hit)
            pts.append(Vector((x, y, hit.z + p["lift"] + r)))
        if len(pts) < 2:
            continue
        mat = bms[run["material"]]
        # the ends: down into the skin through a flange
        ends = [(skin[0], pts[0], 1.0), (skin[-1], pts[-1], -1.0)]
        path = ([Vector((pts[0].x + 0.02, y, skin[0].z - 0.01)), Vector((pts[0].x + 0.09, y, pts[0].z))] + pts[1:-1] +
                [Vector((pts[-1].x - 0.09, y, pts[-1].z)), Vector((pts[-1].x - 0.02, y, skin[-1].z - 0.01))])
        _tube(mat, [q for i, q in enumerate(path) if i == 0 or (q - path[i - 1]).length > 1e-4], r, seg)
        for sk, pt, sgn in ends:
            c = Vector((pt.x + sgn * 0.02, y, sk.z))
            _cyl(bms["metal"], c - Vector((0, 0, 0.004)), c + Vector((0, 0, 0.012)), r + p["flange"], seg)
        # band clamps with a foot, off the ribs
        k = 1
        while x0 + k * p["clamp_pitch"] < x1 - 0.15:
            x = x0 + k * p["clamp_pitch"]
            k += 1
            if any(abs(x - a) < p["avoid_w"] for a in p["avoid_x"]):
                x += p["avoid_w"] * 1.5
            hit, _ = ray("TOP", x, y)
            if hit is None:
                continue
            zc = hit.z + p["lift"] + r
            w = p["clamp_w"]
            _cyl(bms["metal"], Vector((x - w / 2, y, zc)), Vector((x + w / 2, y, zc)), r + 0.005, seg)
            _box(bms["metal"], Vector((x, y, (hit.z + zc) / 2 - 0.004)), Vector((1, 0, 0)), Vector((0, 1, 0)),
                 Vector((0, 0, 1)), (w, max(run["d"] * 0.7, 0.03), zc - hit.z + 0.008))


def conduit_side(bms, p, ray, seg):
    """XK-CONDUIT along the shoulder (F-CONDUIT-S, kit pilot step c): each run a polyline in the side view (x, z),
    the pipe's bottom lift off the skin along the surface normal (over the S plates and the ribs), both sides; clamps
    with a foot every clamp_pitch off the ribs, the ends down into the plates through a flange."""
    for side in (1, -1):
        for run in p["runs"]:
            r = run["d"] / 2
            surf = []
            for x, z in run["pts"]:
                hit, n = ray("SB", x, z)
                if hit is None:
                    continue
                if side > 0:
                    hit, n = Vector((hit.x, -hit.y, hit.z)), Vector((n.x, -n.y, n.z))
                surf.append((hit, n.normalized()))
            if len(surf) < 2:
                continue
            pts = [h + n * (p["lift"] + r) for h, n in surf]
            (h0, n0), (h1, n1) = surf[0], surf[-1]
            path = ([h0 + n0 * 0.02 + Vector((0.02, 0, 0)), pts[0] + Vector((0.07, 0, 0))] + pts[1:-1] +
                    [pts[-1] - Vector((0.07, 0, 0)), h1 + n1 * 0.02 - Vector((0.02, 0, 0))])
            _tube(bms[run["material"]], [q for i, q in enumerate(path) if i == 0 or (q - path[i - 1]).length > 1e-4], r, seg)
            for h, n, sgn in ((h0, n0, 1.0), (h1, n1, -1.0)):
                c = h + Vector((sgn * 0.02, 0, 0))
                _cyl(bms["metal"], c + n * 0.026, c + n * 0.042, r + p["flange"], seg)
            x0, x1 = run["pts"][0][0], run["pts"][-1][0]
            k = 1
            while x0 + k * p["clamp_pitch"] < x1 - 0.15:
                x = x0 + k * p["clamp_pitch"]
                k += 1
                if any(abs(x - a) < p["avoid_w"] for a in p["avoid_x"]):
                    x += p["avoid_w"] * 1.5
                # the run's z at x (linear between its points)
                zs = run["pts"]
                j = max(i for i in range(len(zs)) if zs[i][0] <= x or i == 0)
                j = min(j, len(zs) - 2)
                t = (x - zs[j][0]) / max(zs[j + 1][0] - zs[j][0], 1e-6)
                hit, n = ray("SB", x, zs[j][1] + t * (zs[j + 1][1] - zs[j][1]))
                if hit is None:
                    continue
                if side > 0:
                    hit, n = Vector((hit.x, -hit.y, hit.z)), Vector((n.x, -n.y, n.z))
                n = n.normalized()
                c = hit + n * (p["lift"] + r)
                w = p["clamp_w"]
                _cyl(bms["metal"], c - Vector((w / 2, 0, 0)), c + Vector((w / 2, 0, 0)), r + 0.005, seg)
                fx = Vector((1, 0, 0))
                fy = n.cross(fx).normalized()
                foot = p["lift"] + r
                _box(bms["metal"], hit + n * (foot / 2), fx, fy, n, (w, max(run["d"] * 0.7, 0.03), foot + 0.008))


# ------------------------------------------------------------------------------------------------ build
def apply(recipe, made, coll, mats, ship):
    spec = recipe.get("exterior_kit")
    if not spec or "hull" not in made:
        return {}
    kit = json.load(open(_path(spec["layout"]), encoding="utf-8"))
    hull = made["hull"]
    report = {"plates": 0, "frame": 0, "faces": 0, "bolts": 0, "parts": 0, "region": kit.get("region")}
    tree_bm = bmesh.new()
    tree_bm.from_mesh(hull.data)
    tree_bm.transform(hull.matrix_world)
    tree = BVHTree.FromBMesh(tree_bm)
    bolts = bmesh.new()
    latches = bmesh.new()
    kit_decals = []

    def ray(view, u, v, side=1):
        if view == "SB":
            o, d = Vector((u, -10.0 * side, v)), Vector((0, side, 0))
        elif view == "TOP":
            o, d = Vector((u, v, 10.0)), Vector((0, 0, -1))
        else:
            o, d = Vector((-10.0, u, v)), Vector((1, 0, 0))
        hit, n, _, _ = tree.ray_cast(o, d, 30.0)
        return hit, n

    for group in ("plates", "frame"):
        for e in kit.get(group, []):
            bm, nf = cut_faces(hull, e)
            if not nf:
                print("HSKIT %s %s: no faces under the outline" % (group, e["id"]))
                bm.free()
                continue
            report["groove_verts"] = report.get("groove_verts", 0) + fill_grooves(bm, e["view"], tree)
            if e.get("mirror"):
                mirror_into(bm)
            name = "SM_Ship_%s_Kit_%s%s%s" % (ship, e["id"], "_%s" % e["view"] if group == "frame" else "",
                                               "_%s" % e["suffix"] if e.get("suffix") else "")
            shell(name, bm, coll, mats[e["material"]], e["t"], e["bevel"], e.get("paint2", 0))
            report[group] += 1
            report["faces"] += nf
            cap = e.get("cap")
            if cap:
                # the T profile's web: the hull faces under the narrower outline, higher than the flange
                cbm, cn = cut_faces(hull, dict(e, polys=cap["polys"]))
                if cn:
                    fill_grooves(cbm, e["view"], tree)
                    if e.get("mirror"):
                        mirror_into(cbm)
                    shell(name + "_Web", cbm, coll, mats[cap.get("material", e["material"])], cap["t"], 0.003)
                    report["webs"] = report.get("webs", 0) + 1
                else:
                    print("HSKIT frame %s %s: no faces under the web" % (e["id"], e["view"]))
                    cbm.free()
            for u, v in e.get("latches", []):
                hit, n = ray(e["view"], u, v)
                if hit is not None:
                    lx, ly, lh = e["latch"]
                    fx, fy = _frame(n)
                    _box(latches, hit + n * (e["t"] + lh / 2 - 0.002), fx, fy, n, (lx, ly, lh))
                    report["latches"] = report.get("latches", 0) + 1
            if e.get("bolts_as") == "decal":
                # the bolts as mesh decals at the same points (triangle budget rule A): hs_decals lays them from the
                # scene's hs_kit_decals (layout coordinates), mirrored like the plate
                for u, v in e.get("bolts", []):
                    hit, n = ray(e["view"], u, v)
                    if hit is None:
                        continue
                    at = hit + n * (e["t"] + 0.03)
                    kit_decals.append({"id": e["id"], "item": e["bolt_item"], "on": "ray", "at": [round(c, 4) for c in at],
                                       "dir": [round(-c, 4) for c in n], "mirror": bool(e.get("mirror")),
                                       "check_overlap": False, "flat": True})
                    report["bolt_decals"] = report.get("bolt_decals", 0) + (2 if e.get("mirror") else 1)
                continue
            for u, v in e.get("bolts", []):
                for side in ((1, -1) if e.get("mirror") else (1,)):
                    hit, n = ray(e["view"], u, v)
                    if hit is None:
                        continue
                    if side < 0:
                        hit, n = Vector((hit.x, -hit.y, hit.z)), Vector((n.x, -n.y, n.z))
                    r = max(e.get("bolt_d", 0.02), 0.012) / 2
                    # 8 sides: with the conduits the hull reached the exporter's 1 M triangle limit (round 3)
                    _cyl(bolts, hit + n * (e["t"] - 0.003), hit + n * (e["t"] + 0.006), r, 8, r * 0.8)
                    report["bolts"] += 1
    if bolts.faces:
        ob = hp.finish(bolts, "SM_Ship_%s_Kit_Bolts" % ship, coll, {"angle_deg": 30, "width": 0.0, "segments": 1})
        ob.data.materials.append(mats["metal"])
    else:
        bolts.free()
    if latches.faces:
        ob = hp.finish(latches, "SM_Ship_%s_Kit_Latches" % ship, coll, {"angle_deg": 30, "width": 0.001, "segments": 1})
        ob.data.materials.append(mats["dark"])
    else:
        latches.free()
    # the skin under the plates and the frame: the channel floor (darker than the frame)
    sk = kit.get("skin")
    if sk:
        report["skin_faces"] = skin(hull, sk, mats[sk["material"]], recipe)
    # parts
    bms = {k: bmesh.new() for k in ("paint", "gunmetal", "dark", "metal", "heat", "strobe", "pos_white", "light_red",
                                    "light_green", "light_warm")}
    lights = json.loads(bpy.context.scene.get("hs_lights", "[]"))
    for p in kit.get("parts", []):
        sides = (1, -1) if p.get("mirror", True) else (1,)
        for side in sides:
            if p["type"] == "rcs":
                ay, az = p["pod_axis"]
                a = math.radians(p["deg"] if side > 0 else 180.0 - p["deg"])
                radial = Vector((0.0, math.cos(a), math.sin(a)))
                o = Vector((p["x"], ay * side, az)) + radial * 3.0
                hit, n, _, _ = pod_tree(made, side).ray_cast(o, -radial, 6.0)
                if hit is None:
                    print("HSKIT rcs %s side %d: no pod surface" % (p["id"], side))
                    continue
                rcs_block(bms, hit, n.normalized(), p)
            elif p["type"] == "strobe":
                at = Vector(p["at"])
                at.y *= side
                nrm = Vector(p["normal"])
                nrm.y *= side
                strobe(bms, at, nrm, p["size"], p.get("position") if side > 0 else p.get("mirror_position"))
            elif p["type"] == "lamp":
                at = Vector((p["x"], p["y"] * side, p["z"]))
                hit, _ = ray("AFT", at.y, at.z)
                lamp(bms, Vector((hit.x if hit else at.x, at.y, at.z)), Vector((-1.0, 0.0, 0.0)), p)
                L = p.get("light")
                if L:
                    tilt = math.radians(L.get("aim_down_deg", 45.0))
                    lights.append({"name": "kit_%s%s" % (p["id"].lower().replace("-", "_"), "" if len(sides) == 1 else
                                                         ("_L" if side > 0 else "_R")),
                                   "type": L.get("type", "spot"), "color": [1.0, 0.95, 0.88],
                                   "intensity_cd": L["intensity_cd"], "radius_m": L["radius_m"],
                                   "location": [at.x - 0.08, at.y, at.z],
                                   "direction": [-math.cos(tilt), 0.0, -math.sin(tilt)],
                                   "cone_deg": L.get("cone_deg", 60.0), "source_radius_cm": 3.0, "specular": 0.4})
            elif p["type"] == "piston":
                # the brackets' base: the hull wall at the foot, the ramp frame's face at the head
                y = p["y"] * side
                walls = []
                for z in p["z"]:
                    hit, _ = ray("AFT", y, z)
                    walls.append(hit.x if hit else 0.0)
                fr = next((f for f in kit.get("frame", []) if f["id"] == "F-RAMP-FRAME" and not f.get("suffix")), None)
                if fr:
                    walls[1] -= fr["t"]
                piston(bms, (p["x"], y, p["z"][0]), (p["x"], y, p["z"][1]), p, walls)
            elif p["type"] == "hinge":
                hinge(bms, p)
            elif p["type"] == "conduit":
                conduit(bms, p, ray)
            report["parts"] += 1
    bpy.context.scene["hs_lights"] = json.dumps(lights)
    bpy.context.scene["hs_kit_decals"] = json.dumps(kit_decals)
    for key, bm in bms.items():
        if not bm.faces:
            bm.free()
            continue
        ob = hp.finish(bm, "SM_Ship_%s_Kit_Parts_%s" % (ship, key.title().replace("_", "")), coll,
                       {"angle_deg": 30, "width": 0.004, "segments": 1})
        ob.data.materials.append(mats[key])
    tree_bm.free()
    print("HSKIT " + json.dumps(report))
    return report


_POD_TREES = {}


def pod_tree(made, side):
    """BVH of the pod on one side (port +1 / starboard -1) for the parts placed on it."""
    if side in _POD_TREES:
        return _POD_TREES[side]
    bm = bmesh.new()
    for key, ob in made.items():
        if key.startswith("pod_") and ob.type == "MESH":
            c = sum((ob.matrix_world @ Vector(b) for b in ob.bound_box), Vector()) / 8
            if c.y * side > 0:
                tmp = bmesh.new()
                tmp.from_mesh(ob.data)
                tmp.transform(ob.matrix_world)
                me = bpy.data.meshes.new("_podtmp")
                tmp.to_mesh(me)
                tmp.free()
                bm.from_mesh(me)
                bpy.data.meshes.remove(me)
    _POD_TREES[side] = BVHTree.FromBMesh(bm)
    return _POD_TREES[side]


def skin(hull, sk, material, recipe):
    """Hull faces in the region (x range, section height v >= v_min) take the gunmetal slot."""
    mats = [m.name for m in hull.data.materials]
    if material.name not in mats:
        hull.data.materials.append(material)
        mats.append(material.name)
    slot = mats.index(material.name)
    layout = json.load(open(_path(recipe["layout"]), encoding="utf-8"))
    side = next(e["poly"] for e in layout["exterior"]["side"] if e.get("part") == "hull" and "poly" in e)

    def zspan(x):
        zs = []
        n = len(side)
        for i in range(n):
            (x0, z0), (x1, z1) = side[i], side[(i + 1) % n]
            if (x0 <= x <= x1 or x1 <= x <= x0) and x0 != x1:
                zs.append(z0 + (x - x0) / (x1 - x0) * (z1 - z0))
        return (min(zs), max(zs)) if zs else (0.0, 1.0)

    count = 0
    aft = sk.get("aft")
    if aft:
        # the aft wall round its plates and frame (kit pilot step c): faces facing aft inside the outline (port half,
        # mirrored), not inside the ramp frame
        half = [tuple(p) for p in aft["outline"]]
        ey0, ez0, ey1, ez1 = aft["exclude"]
        for poly in hull.data.polygons:
            c = poly.center
            if c.x > aft["x_max"] or c.z > aft.get("z_max", 99.0) or not normal_ok(poly.normal, aft["normal"]):
                continue
            if ey0 <= c.y <= ey1 and ez0 <= c.z <= ez1:
                continue
            if inside((abs(c.y), c.z), half):
                poly.material_index = slot
                count += 1
    near = [([tuple(p) for p in ring], (min(p[0] for p in ring), min(p[1] for p in ring),
                                        max(p[0] for p in ring), max(p[1] for p in ring)))
            for ring in sk.get("near_side", [])]
    for poly in hull.data.polygons:
        c = poly.center
        if near and abs(poly.normal.y) > 0.3:
            # a side face (whole-ship kit): channel floor only round the plates and the frame (layout skin.near_side)
            if any(b[0] <= c.x <= b[2] and b[1] <= c.z <= b[3] and inside((c.x, c.z), ring) for ring, b in near):
                poly.material_index = slot
                count += 1
                continue
        if not (sk["x"][0] <= c.x <= sk["x"][1]):
            continue
        zb, zt = zspan(c.x)
        if (c.z - zb) / max(zt - zb, 1e-6) >= sk["v_min"]:
            poly.material_index = slot
            count += 1
    return count
