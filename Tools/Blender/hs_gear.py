"""Real landing gear (whole-ship rebuild part 3, skill ship-pipeline 3b3), called by hs_build_ship.py.

Replaces the gear parts built from the drawing's outlines (a strut block and a pad, as intersected prisms)
by a working-looking leg inside the same envelopes, so the silhouette holds:

  - trunnion yoke at the top, oleo strut: outer cylinder, polished piston, gland ring
  - torque links (scissor) on the aft side, a drag brace to the front, hydraulic lines down the leg
  - a leg door on the outboard side (main gear) / the front (nose gear) that fills the strut envelope in the
    side view, with a hazard band (accent) at its lower edge
  - ankle joint and a foot: rubber sole, gunmetal base plate and a smaller deck, gussets and bolts; a hydraulic
    actuator ahead of the strut

Recipe "gear": {"<part>": {"at": [x, y, z_top], "mirror": bool, "strut": [lx, ly, top, bottom],
"pad": [lx, ly, z_bottom, height], "door": "outboard" | "front"}} in layout metres. The finished leg keeps
the part's object name (the assemble step groups it as the Gear part the pawn raises and lowers).
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import hs_build_part as hp
import hs_detail


def _cyl(bm, a, b, r, seg=20):
    hs_detail.tube(bm, [Vector(a), Vector(b)], r, seg=seg, bend=0.0001)


def _box(bm, c, size, xdir=(1, 0, 0), zdir=(0, 0, 1)):
    hs_detail.oriented_box(bm, Vector(c), Vector(xdir), Vector(zdir), size)


def leg(spec, sign):
    """bmeshes by material key for one leg; y mirrored by sign."""
    x, y, _ = spec["at"]
    y *= sign
    lx, ly, top, bot = spec["strut"]
    plx, ply, pz, ph = spec["pad"]
    parts = {k: bmesh.new() for k in ("dark", "metal", "paint", "accent", "rubber", "gunmetal")}
    out = 1 if y >= 0 else -1                          # outboard direction in y
    # trunnion yoke and mount block
    _box(parts["dark"], (x, y, top - 0.06), (lx * 0.9, ly * 0.9, 0.12))
    _cyl(parts["metal"], (x, y - ly * 0.5, top - 0.1), (x, y + ly * 0.5, top - 0.1), 0.045)
    # oleo strut
    z_outer_bot = top - 0.12 - (top - bot) * 0.5
    _cyl(parts["dark"], (x, y, top - 0.12), (x, y, z_outer_bot), 0.11, seg=24)
    _cyl(parts["metal"], (x, y, z_outer_bot - 0.005), (x, y, z_outer_bot + 0.03), 0.118, seg=24)   # gland
    z_ankle = bot + 0.07
    _cyl(parts["metal"], (x, y, z_outer_bot), (x, y, z_ankle + 0.03), 0.07, seg=24)                # piston
    # torque links on the aft side (-x): two arms meeting at a knee, a collar on the piston
    mid = (z_outer_bot + z_ankle) / 2
    knee = (x - 0.19, y, mid)
    for yy in (y - 0.03, y + 0.03):
        _cyl(parts["metal"], (x - 0.09, yy, z_outer_bot - 0.01), (knee[0], yy, mid), 0.016, seg=10)
        _cyl(parts["metal"], (knee[0], yy, mid), (x - 0.07, yy, z_ankle + 0.06), 0.016, seg=10)
    _cyl(parts["dark"], (knee[0], y - 0.05, mid), (knee[0], y + 0.05, mid), 0.022, seg=12)
    _cyl(parts["dark"], (x, y, z_ankle + 0.04), (x, y, z_ankle + 0.09), 0.09, seg=20)       # collar
    _cyl(parts["dark"], (x - 0.1, y - 0.04, z_outer_bot - 0.01), (x - 0.1, y + 0.04, z_outer_bot - 0.01), 0.02, seg=12)
    # drag brace: from the front of the yoke down to the outer cylinder
    _cyl(parts["dark"], (x + lx * 0.4, y, top - 0.1), (x + 0.1, y, (top - 0.12 + z_outer_bot) / 2), 0.028, seg=12)
    # hydraulic lines down the leg
    for dy in (-0.05, 0.05):
        pts = [Vector((x + 0.12, y + dy, top - 0.12)), Vector((x + 0.125, y + dy, z_outer_bot)), Vector((x + 0.085, y + dy, z_ankle + 0.1))]
        hs_detail.tube(parts["dark"], pts, 0.009, seg=8, bend=0.05)
    # leg door: fills the strut envelope in the side view
    if spec.get("door", "outboard") == "outboard":
        dy = y + out * (ly * 0.5 - 0.012)
        _box(parts["paint"], (x, dy, (top - 0.02 + z_outer_bot) / 2), (lx, 0.022, (top - 0.02) - z_outer_bot), zdir=(0, 0, 1))
        _box(parts["accent"], (x, dy + out * 0.004, z_outer_bot + 0.04), (lx * 0.98, 0.02, 0.06))
    else:
        _box(parts["paint"], (x + lx * 0.5 - 0.012, y, (top - 0.02 + z_outer_bot) / 2), (0.022, ly, (top - 0.02) - z_outer_bot),
             xdir=(0, 1, 0), zdir=(0, 0, 1))
        _box(parts["accent"], (x + lx * 0.5 - 0.008, y, z_outer_bot + 0.04), (0.02, ly * 0.98, 0.06), xdir=(0, 1, 0))
    # ankle and pad
    _cyl(parts["metal"], (x, y - 0.09, z_ankle), (x, y + 0.09, z_ankle), 0.05)
    _box(parts["dark"], (x, y, z_ankle - 0.03), (0.2, 0.16, 0.08))
    # foot (SC exterior technique 12, 10. 10. 2026: the plain black slab read as a brick): a rubber sole proud of
    # a gunmetal base plate, a smaller deck on it (a step, not one block), two gussets from the ankle block to
    # the toe and heel, a bolt in each corner of the deck
    pad_top = pz + ph
    sole = 0.035
    base_h = (ph - sole) * 0.45
    _box(parts["rubber"], (x, y, pz + sole / 2), (plx, ply, sole))
    _box(parts["gunmetal"], (x, y, pz + sole + base_h / 2), (plx * 0.96, ply * 0.96, base_h))
    deck_h = ph - sole - base_h
    _box(parts["gunmetal"], (x, y, pz + sole + base_h + deck_h / 2), (plx * 0.72, ply * 0.66, deck_h))
    for sx in (-1, 1):
        gx = x + sx * plx * 0.22
        _box(parts["gunmetal"], (gx, y, pad_top + 0.045), (plx * 0.36, 0.03, 0.09))
        for sy in (-1, 1):
            q = (x + sx * plx * 0.32, y + sy * ply * 0.27, pad_top)
            _cyl(parts["metal"], q, (q[0], q[1], q[2] + 0.012), 0.016, seg=8)
    # hydraulic retraction actuator ahead of the strut (+x): cylinder from the yoke, rod to the ankle collar,
    # eyes at both ends
    # (a front door - the nose gear - takes it on the side instead)
    front = spec.get("door", "outboard") == "front"
    ax, ay = (x, y + 0.17) if front else (x + 0.19, y)
    za, zb = top - 0.16, z_ankle + 0.12
    zm = za + (zb - za) * 0.55
    _cyl(parts["dark"], (ax, ay, za), (ax, ay, zm), 0.042, seg=16)
    _cyl(parts["metal"], (ax, ay, zm), (ax, ay, zb), 0.022, seg=12)
    for zz in (za + 0.02, zb):
        if front:
            _cyl(parts["gunmetal"], (ax - 0.035, ay, zz), (ax + 0.035, ay, zz), 0.03, seg=12)
        else:
            _cyl(parts["gunmetal"], (ax, ay - 0.035, zz), (ax, ay + 0.035, zz), 0.03, seg=12)
    end = (x, y + 0.06, z_ankle + 0.07) if front else (x + 0.06, y, z_ankle + 0.07)
    _cyl(parts["metal"], (ax, ay - 0.03, zb) if front else (ax - 0.03, ay, zb), end, 0.02, seg=10)
    return parts


def build(recipe, made, coll, mats, bevel, ship):
    spec = recipe.get("gear")
    if not spec:
        return {}
    report = {}
    for part, g in spec.items():
        if part.startswith("_") or part not in made:
            continue
        old = made[part]
        name = old.name
        pieces = []
        for sign in ((1, -1) if g.get("mirror") else (1,)):
            for key, bm in leg(g, sign).items():
                if not bm.verts:
                    bm.free()
                    continue
                ob = hp.finish(bm, "%s_%s_%d" % (name, key, sign), coll, bevel)
                ob.modifiers["Bevel"].width = 0.004
                ob.data.materials.append(mats[{"rubber": "dark"}.get(key, key)])
                pieces.append(ob)
        # one object per gear part, modifiers applied, under the old name
        dg = bpy.context.evaluated_depsgraph_get()
        bm_all = bmesh.new()
        me_all = bpy.data.meshes.new(name + "_joined")
        mat_list = []
        for ob in pieces:
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            m = ob.data.materials[0]
            if m.name not in [x.name for x in mat_list]:
                mat_list.append(m)
            idx = [x.name for x in mat_list].index(m.name)
            for p in me.polygons:
                p.material_index = idx
            bm_all.from_mesh(me)
            bpy.data.meshes.remove(me)
            bpy.data.objects.remove(ob)
        bm_all.to_mesh(me_all)
        bm_all.free()
        for m in mat_list:
            me_all.materials.append(m)
        bpy.data.objects.remove(old)
        ob = bpy.data.objects.new(name, me_all)
        ob.data.name = name
        coll.objects.link(ob)
        for p in ob.data.polygons:
            p.use_smooth = True
        ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL").keep_sharp = True
        made[part] = ob
        report[part] = {"faces": len(me_all.polygons)}
    return report
