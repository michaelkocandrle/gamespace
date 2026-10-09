"""Functional parts as real geometry (skill ship-pipeline 3b3): what makes an SC ship read as a machine that
works - RCS thruster blocks, antennas, sensor domes, weapon mounts, flap hinges, umbilical connectors.
Called by hs_build_ship.py after the lights. Recipe block "functional", LAYOUT coordinates:

  items  {"kind": rcs | blade | whip | dome | connector | hinge, "on": pod / side / top / bottom / ray
         (as the decals and lights), "mirror" (default true), "rot" degrees about the normal, "size" scale}
  gun_mounts  {"gun": [x0, x1], "y": .., "z": .., "r": .., "at": [x, ...]}: clamp collars and a pylon
         block to the wing under each

Every part is laid on the surface by a ray (the hull, pods, plates and wings as built), its +Z out of the
surface; an RCS block points its nozzles along the surface normal (and "tilt" degrees towards +x / -x).
"""
import math

import bmesh
from mathutils import Matrix, Vector

import hs_build_part as hp
import hs_detail
import hs_lights


def _frame(n, rot):
    x = Vector((1, 0, 0)) - n * n.x
    if x.length < 1e-3:
        x = n.orthogonal()
    x.normalize()
    if rot:
        x = Matrix.Rotation(math.radians(rot), 3, n) @ x
    return x, n.cross(x)


def _box(bm, c, x, y, z, size):
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=res["verts"])
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = c
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def _cyl(bm, a, b, r, seg=16, r2=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    m = q.to_matrix().to_4x4()
    m.translation = (a + b) / 2
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def _cbox(bm, c, x, y, z, size, chamfer):
    """A machined box: the part's Bevel modifier (4 mm, angle limited) chamfers its edges."""
    _box(bm, c, x, y, z, size)


def rcs(g, p, n, x, y, s):
    """Thruster block (author 9. 10. 2026: the box with two cylinders read as Lego): a machined gunmetal housing
    with chamfered edges 3 cm proud, a dark recessed face plate in a raised lip, two nozzle bells (bare-metal
    flared rim, a dark throat, a hot-metal ring inside), a slotted grille between them, four corner screws."""
    tilt = math.radians(g.get("tilt", 0.0))
    dirn = (n * math.cos(tilt) + x * math.sin(tilt)).normalized()
    bm_gm, bm_dk, bm_mt = g["_bm"]["gunmetal"], g["_bm"]["dark"], g["_bm"]["metal"]
    L, W = 0.30 * s, 0.19 * s
    _cbox(bm_gm, p + n * 0.012 * s, x, y, n, (L, W, 0.03 * s), 0.008 * s)                    # housing
    _cbox(bm_gm, p + n * 0.03 * s, x, y, n, (L - 0.03 * s, W - 0.03 * s, 0.006 * s), 0.003 * s)  # lip
    _box(bm_dk, p + n * 0.0335 * s, x, y, n, (L - 0.05 * s, W - 0.05 * s, 0.002 * s))        # face plate
    for k in (-1, 1):
        c = p + n * 0.034 * s + x * (0.075 * k * s)
        _cyl(bm_mt, c, c + dirn * 0.022 * s, 0.034 * s, 20, 0.041 * s)                      # flared bell
        _cyl(bm_dk, c + dirn * 0.004 * s, c + dirn * 0.0225 * s, 0.03 * s, 20, 0.036 * s)    # its throat
        _cyl(bm_mt, c + dirn * 0.003 * s, c + dirn * 0.008 * s, 0.014 * s, 12)               # the injector
    for j in range(4):                                                                       # the grille
        q = p + n * 0.0345 * s + y * ((j - 1.5) * 0.022 * s)
        _box(bm_mt, q, x, y, n, (0.05 * s, 0.006 * s, 0.003 * s))
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = p + n * 0.027 * s + x * sx * (L / 2 - 0.016 * s) + y * sy * (W / 2 - 0.016 * s)
            _cyl(bm_mt, q, q + n * 0.004 * s, 0.006 * s, 8)


def blade(g, p, n, x, y, s):
    """Swept blade antenna on a base plate."""
    _box(g["_bm"]["dark"], p + n * 0.006, x, y, n, (0.2 * s, 0.07 * s, 0.012))
    bm = g["_bm"]["dark"]
    h, c0, c1 = 0.16 * s, 0.14 * s, 0.06 * s
    pts = [p + n * 0.012 - x * c0 * 0.5, p + n * 0.012 + x * c0 * 0.5, p + n * h + x * (c0 * 0.5 - 0.02), p + n * h + x * (c0 * 0.5 - 0.02 - c1)]
    t = y * 0.006
    vs = [bm.verts.new(q + t) for q in pts] + [bm.verts.new(q - t) for q in pts]
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])


def whip(g, p, n, x, y, s):
    _cyl(g["_bm"]["dark"], p, p + n * 0.03, 0.03 * s, 16)
    _cyl(g["_bm"]["metal"], p + n * 0.03, p + n * 0.3 * s, 0.006, 8)
    _cyl(g["_bm"]["dark"], p + n * 0.3 * s, p + n * 0.32 * s, 0.012, 8)


def dome(g, p, n, x, y, s):
    """Sensor dome: base ring and a dark glossy hemisphere."""
    r = 0.08 * s
    p = p - n * 0.03
    _cyl(g["_bm"]["paint"], p - n * 0.01, p + n * 0.04, r * 1.25, 32)
    bm = g["_bm"]["dark"]      # glass is translucent: Nanite cannot draw it on the main mesh
    rows = []
    for i in range(7):
        a = (math.pi / 2) * i / 6
        ring = []
        for j in range(24):
            b = 2 * math.pi * j / 24
            ring.append(bm.verts.new(p + n * (0.025 + r * math.sin(a)) + (x * math.cos(b) + y * math.sin(b)) * r * math.cos(a)))
        rows.append(ring)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(24):
            bm.faces.new((r0[j], r0[(j + 1) % 24], r1[(j + 1) % 24], r1[j]))
    bm.faces.new(rows[0][::-1])


def connector(g, p, n, x, y, s):
    """Umbilical connector: a gunmetal flange with 6 bolts, a bare-metal coupling with a dark socket, the cap hinged
    on a lug beside it."""
    bm_gm, bm_mt, bm_dk = g["_bm"]["gunmetal"], g["_bm"]["metal"], g["_bm"]["dark"]
    _cyl(bm_gm, p - n * 0.01, p + n * 0.018, 0.065 * s, 32)
    for k in range(6):
        a_ = 2 * math.pi * k / 6
        q = p + n * 0.018 + (x * math.cos(a_) + y * math.sin(a_)) * 0.052 * s
        _cyl(bm_mt, q, q + n * 0.004, 0.006 * s, 8)
    _cyl(bm_mt, p + n * 0.018, p + n * 0.04, 0.04 * s, 24)
    _cyl(bm_dk, p + n * 0.038, p + n * 0.041, 0.028 * s, 24)
    _cbox(bm_gm, p + n * 0.02 + x * 0.085 * s, x, y, n, (0.035 * s, 0.03 * s, 0.025), 0.004 * s)


def hinge(g, p, n, x, y, s):
    """Flap hinge: a chamfered gunmetal mounting plate with 4 screws, two lugs with a bare-metal pin and its caps."""
    bm_gm, bm_mt = g["_bm"]["gunmetal"], g["_bm"]["metal"]
    _cbox(bm_gm, p + n * 0.006 * s, x, y, n, (0.14 * s, 0.09 * s, 0.012 * s), 0.004 * s)
    for k in (-1, 1):
        _cbox(bm_gm, p + n * 0.035 * s + y * (0.028 * k * s), x, y, n, (0.07 * s, 0.014 * s, 0.05 * s), 0.004 * s)
        q = p + n * 0.012 * s + x * (0.055 * k * s)
        for j in (-1, 1):
            c = q + y * (0.032 * j * s)
            _cyl(bm_mt, c, c + n * 0.003 * s, 0.005 * s, 8)
    a_, b_ = p + n * 0.05 * s - y * 0.05 * s, p + n * 0.05 * s + y * 0.05 * s
    _cyl(bm_mt, a_, b_, 0.011 * s, 16)
    for c in (a_, b_):
        _cyl(bm_mt, c - (b_ - a_).normalized() * 0.004 * s, c + (b_ - a_).normalized() * 0.004 * s, 0.016 * s, 16)


KINDS = {"rcs": rcs, "blade": blade, "whip": whip, "dome": dome, "connector": connector, "hinge": hinge}


def apply(recipe, made, coll, mats, bevel):
    spec = recipe.get("functional")
    if not spec:
        return {}
    rev = recipe["parts"]["pod"]["revolve"]["axis"]
    axis = (rev["y"], rev["z"])
    tree = hs_lights._tree(coll)
    bms = {k: bmesh.new() for k in ("paint", "dark", "metal", "gunmetal")}
    count = {}
    for g in spec.get("items", []):
        if g.get("kit"):
            continue            # a kit part (XK-*): Tools/Blender/hs_exterior_kit.py builds it
        g = dict(g, _bm=bms)
        for side in ((1, -1) if g.get("mirror", True) else (1,)):
            origin, d = hs_lights._ray(g, side, axis)
            hit, n, _, _ = tree.ray_cast(origin, d, 20.0)
            if hit is None:
                print("HSFUNC miss", g["kind"], g.get("x"), side)
                continue
            n = n.normalized()
            x, y = _frame(n, g.get("rot", 0.0) * side)
            KINDS[g["kind"]](g, hit, n, x, y, g.get("size", 1.0))
            count[g["kind"]] = count.get(g["kind"], 0) + 1
    for gm in spec.get("gun_mounts", []):
        for side in (1, -1):
            yy = gm["y"] * side
            for xc in gm["at"]:
                c = Vector((xc, yy, gm["z"]))
                _cyl(bms["dark"], c - Vector((0.06, 0, 0)), c + Vector((0.06, 0, 0)), gm["r"] * 1.1, 24)
                _cyl(bms["metal"], c - Vector((0.075, 0, 0)), c - Vector((0.06, 0, 0)), gm["r"] * 1.14, 24)
            count["gun_mount"] = count.get("gun_mount", 0) + 1
    objs = []
    for key, bm in bms.items():
        if not bm.verts:
            bm.free()
            continue
        ob = hp.finish(bm, "SM_Ship_Detail_Functional_%s" % key.title(), coll, bevel)
        ob.modifiers["Bevel"].width = 0.004
        ob.data.materials.append(mats[key])
        objs.append(ob)
        made["functional_" + key] = ob
    return {"parts": count, "objects": [o.name for o in objs]}
