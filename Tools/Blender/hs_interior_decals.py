"""Mesh decals inside the ship, from the exterior's decal library (ArtSource/Ships/Shared/Decals, Tools/Blender/
decal_library.py; placed by hs_decals.Placer, which lays each item onto the surface it hits), plus the grab bars
on the canopy pillars. Author 25. 9. 2026: "don't spare decals and details" - walls get recessed panels, hatches,
vents, bolts, rivets, seams, cable runs, panel numbers and service stencils; the cockpit gets labels at every
control group (NAV, COMMS, PWR, SHLD, WPN, FLIGHT, SYSTEMS...), EJECT, CANOPY, MASTER ARM, EMERG O2 and the maker's
plate.

Recipe interior.decals:
  index      the library index (decal_library_index.json)
  items      [{"item", "from": [x, y, z], "to": [x, y, z] | "dir": [..], "rot", "scale"}]  one ray each
  scatter    [{"items": [..], "weights": [..], "x": [x0, x1], "z": [z0, z1], "from_y": y, "sides": [1, -1],
               "dir_z": dz, "step": m, "prob": p, "seed": n}]  a grid of rays towards the walls
  grab_bars  [{"at": [x, y, z], "from": [x, y, z], "length": m}]  a bar on the surface the ray hits
Output: SM_Ship_<Ship>_IntDecals (slots Decal / DecalAO / DecalPaint / Trim / TrimAO, the exterior's materials;
hs_assemble_ship joins it into the part "InteriorDecals" - atlas UVs, no unwrap, no collision, not Nanite) and
SM_Ship_<Ship>_Int_GrabBars.
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

import hs_decals


def _target(objs):
    bm = bmesh.new()
    for ob in objs:
        if ob.type != "MESH" or not ob.data.polygons:
            continue
        me = ob.data.copy()
        me.transform(ob.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new("_int_decal_target")
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(me.name, me)


def cockpit_items(spec, eye, root=None):
    """Labels at the cockpit's control groups, aimed from the pilot's eye (the cockpit recipe's geometry)."""
    ck = spec.get("_cockpit", {})
    out = []
    if not ck:
        return out
    e = Vector(eye)
    for side, label, keys in ((1, "ck_flight", "left"), (-1, "ck_sys", "right")):
        c = Vector((ck["pod_x"], side * ck["pod_y"], ck["pod_z"]))
        n = (e - c).normalized()
        right = Vector((0, 0, 1)).cross(n).normalized()
        up = n.cross(right).normalized()
        sh = ck["screen_w"] * 490.0 / 560.0
        # between the screen's bezel and the key row
        t = c - up * ((sh + 0.05) / 2 + 0.02)
        out.append({"item": label, "from": list(e), "to": list(t)})
        # small panel number on the outer strip
        s = c + right * (-side) * (ck["screen_w"] / 2 + ck["side_margin"] * 0.5) + up * 0.13
        out.append({"item": "panel_C21" if side > 0 else "panel_C22", "from": list(e), "to": list(s), "scale": 0.7})
    # a label under every control of the control modules (hs_cockpit.control_module), shot at its face
    import hs_cockpit
    index = json.load(open(os.path.join(root, spec["index"]), encoding="utf-8")) if root and spec.get("index") else None
    for lab in hs_cockpit.LABELS:
        at, n = Vector(lab["at"]), Vector(lab["n"])
        scale = lab["scale"]
        if index and lab["item"] in index["decals"]:
            # a long word (QUANTUM) shrinks to its control's cell
            scale = min(scale, lab.get("max_w", 1.0) / index["decals"][lab["item"]]["size_m"][0])
        out.append({"item": lab["item"], "from": list(at + n * 0.03), "dir": list(-n), "scale": scale, "label": True,
                    "frame": (lab["x"], lab["y"])})
    x, y, zt = ck["wing"][1]
    out.append({"item": "ck_maker_plate", "from": list(e), "to": [x + 0.05, y - 0.02, ck.get("fascia_bottom_z", 0.97) + 0.03], "scale": 0.8})
    return out


def build(objs, ship, coll, spec, root, mats, eye):
    index = json.load(open(os.path.join(root, spec["index"]), encoding="utf-8"))
    target = _target(objs)
    pl = hs_decals.Placer(target, {"offset_m": spec.get("offset_m", 0.0015), "grid_m": spec.get("grid_m", 0.05)},
                          index, (0.0, 0.0, 0.0), (99.0, 99.0))
    report = {"items": 0, "scatter": 0}

    failed = []

    def shoot(it):
        o = Vector(it["from"])
        d = (Vector(it["to"]) - o) if "to" in it else Vector(it["dir"])
        hit, n = pl.cast(o, d.normalized())
        if hit is None:
            pl.skipped["miss"] += 1
            if it.get("label"):
                failed.append((it["item"], "miss", [round(v, 3) for v in o]))
            return None
        before = dict(pl.skipped)
        # a control's label lies on its module's face between the controls: lay it from just above the face
        # (from 12 cm the rays met the controls and the glare shield - every module label failed, 25. 9. 2026)
        pl.reach = 0.02 if it.get("label") else 0.12
        # a module's label runs along the module (its own frame), not by the surface's world orientation
        frame = (Vector(it["frame"][0]), Vector(it["frame"][1])) if "frame" in it else None
        fr = pl.place_at(it["item"], hit, n, it.get("rot", 0.0), it.get("scale", 1.0), "interior", not it.get("label"), frame)
        pl.reach = 0.12
        if fr is None and it.get("label"):
            failed.append((it["item"], [k for k in pl.skipped if pl.skipped[k] != before.get(k)], [round(v, 3) for v in hit]))
        return fr

    for it in cockpit_items(spec, eye, root) + spec.get("items", []):
        if shoot(it):
            report["items"] += 1
    for sc in spec.get("scatter", []):
        rng = random.Random(sc.get("seed", 3))
        names, weights = sc["items"], sc.get("weights") or [1] * len(sc["items"])
        x0, x1 = sc["x"]
        z0, z1 = sc["z"]
        step = sc.get("step", 0.3)
        nx, nz = max(1, int((x1 - x0) / step)), max(1, int((z1 - z0) / step))
        for side in sc.get("sides", [1, -1]):
            for i in range(nx + 1):
                for j in range(nz + 1):
                    if rng.random() > sc.get("prob", 0.5):
                        continue
                    x = x0 + (x1 - x0) * i / nx + rng.uniform(-0.4, 0.4) * step
                    z = z0 + (z1 - z0) * j / nz + rng.uniform(-0.4, 0.4) * step
                    it = {"item": rng.choices(names, weights)[0], "from": [x, sc.get("from_y", 0.0), z],
                          "dir": [0.0, side, sc.get("dir_z", 0.0)], "rot": rng.choice(sc.get("rots", [0.0]))}
                    if shoot(it):
                        report["scatter"] += 1
    out = []
    name = "SM_Ship_%s_IntDecals" % ship
    me = bpy.data.meshes.new(name)
    pl.bm.to_mesh(me)
    pl.bm.free()
    for slot in hs_decals.SLOTS:
        m = bpy.data.materials.get("M_Ship_%s_%s" % (ship, slot)) or bpy.data.materials.new("M_Ship_%s_%s" % (ship, slot))
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    out.append(ob)
    # grab bars on the canopy pillars: a satin bar on two stand-offs with a yellow grip, along the surface
    bars = bmesh.new()
    grips = bmesh.new()
    for gb in spec.get("grab_bars", []):
        o, a = Vector(gb["from"]), Vector(gb["at"])
        hit, n = pl.cast(o, (a - o).normalized())
        if hit is None:
            continue
        along = Vector(gb.get("along", (0, 0, 1)))
        along = (along - n * along.dot(n)).normalized()
        L = gb.get("length", 0.3)
        hit = hit + n * gb.get("standoff_m", 0.0)
        p0, p1 = hit - along * L / 2, hit + along * L / 2
        side = n.cross(along).normalized()
        for p in (p0, p1):
            _tube(bars, p, p + n * 0.05, 0.012)
            _tube(bars, p - n * 0.002, p + n * 0.006, 0.022)
            # a mounting plate with four screws under each stand-off (the bar hung unanchored)
            _plate(bars, p + n * 0.003, along, side, n, 0.07, 0.05, 0.006)
            for du in (-0.025, 0.025):
                for dv in (-0.017, 0.017):
                    q = p + along * du + side * dv + n * 0.006
                    _tube(bars, q, q + n * 0.004, 0.005, 8)
        _tube(bars, p0 + n * 0.05 - along * 0.012, p1 + n * 0.05 + along * 0.012, 0.013)
        _tube(grips, p0 + n * 0.05 + along * 0.06, p1 + n * 0.05 - along * 0.06, 0.016)
    for bm, key, nm in ((bars, "int_trim", "GrabBars"), (grips, "accent", "GrabGrips")):
        if bm.verts:
            m2 = bpy.data.meshes.new("SM_Ship_%s_Int_%s" % (ship, nm))
            bm.to_mesh(m2)
            o2 = bpy.data.objects.new(m2.name, m2)
            coll.objects.link(o2)
            m2.materials.append(mats[key])
            m2.shade_smooth()
            out.append(o2)
        bm.free()
    bpy.data.meshes.remove(target.data)
    report.update({"skipped": pl.skipped, "faces": len(me.polygons), "labels_failed": failed})
    print("INTDECALS " + json.dumps({"labels_failed": failed}))
    return out, report


def _plate(bm, c, x, y, n, w, h, t):
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, h, t), verts=res["verts"])
    from mathutils import Matrix
    m = Matrix((x, y, n)).transposed().to_4x4()
    m.translation = c
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def _tube(bm, a, b, r, seg=10):
    d = b - a
    if d.length < 1e-5:
        return
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length)
    m = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m.translation = (a + b) / 2
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])
