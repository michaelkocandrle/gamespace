"""Shape layers on top of the exact base (step 4 of the SC detail plan, skill ship-pipeline 3b3).

The base (hs_build_ship.py) is the large layer: loft, outlines, revolved pods. This module adds the
medium layer from the recipe's "detail" block, in LAYOUT coordinates (x from the aft end, z from the deck):

  hull_plates    armour plates with real thickness: a copy of the hull faces in a region, solidified
                 outwards, bevelled; an optional smaller "step" plate on top (stepped transition)
  hull_recesses  recessed bays cut into the hull (inset frame + walls + dark floor) with what sits in
                 them: louvers (cooler grilles) or pipes (exposed mechanics)
  pod            per pod: armour plate sectors (with steps), an open service bay (one panel and the
                 substructure under it removed, a closed tub with pipes and an actuator inside) and a
                 pipe run along the outside with clamps

Everything is built for the port side (+y) and mirrored, except regions marked "centre". Detail objects
get face attribute "paint2" (1 = secondary paint) which hs_assemble_ship.py turns into the vertex-colour
paint mask for the layered material. Prints HSDETAIL {...}.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import hs_build_part as hp

MIRROR_Y = Matrix.Scale(-1.0, 4, (0.0, 1.0, 0.0))


# --------------------------------------------------------------------------------------------
# Small geometry helpers
# --------------------------------------------------------------------------------------------

def _fillet(pts, bend):
    """Polyline -> smooth path: every inner corner replaced by a quadratic arc of size `bend`."""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for a, p, b in zip(pts, pts[1:], pts[2:]):
        da, db = (a - p), (b - p)
        ra, rb = min(bend, da.length / 2), min(bend, db.length / 2)
        pa, pb = p + da.normalized() * ra, p + db.normalized() * rb
        for k in range(7):
            t = k / 6
            out.append(pa * (1 - t) ** 2 + p * 2 * t * (1 - t) + pb * t * t)
    out.append(pts[-1])
    return out


def tube(bm, pts, r, seg=12, bend=0.08):
    """Closed pipe along a polyline (rounded bends, capped ends), frames by parallel transport."""
    path = _fillet(pts, bend)
    t0 = (path[1] - path[0]).normalized()
    nrm = t0.orthogonal().normalized()
    rings = []
    for i, p in enumerate(path):
        if i == 0:
            t = (path[1] - path[0]).normalized()
        elif i == len(path) - 1:
            t = (path[-1] - path[-2]).normalized()
        else:
            t = ((path[i + 1] - path[i]).normalized() + (path[i] - path[i - 1]).normalized()).normalized()
        nrm = (nrm - t * nrm.dot(t)).normalized()
        b = t.cross(nrm)
        rings.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for ra, rb in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((ra[k], ra[(k + 1) % seg], rb[(k + 1) % seg], rb[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])


def oriented_box(bm, centre, xdir, zdir, size):
    """Box of `size` (x along xdir, z along zdir) centred at `centre`."""
    x = Vector(xdir).normalized()
    z = (Vector(zdir) - x * x.dot(Vector(zdir))).normalized()
    y = z.cross(x)
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=res["verts"])
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(centre)
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def mirror_into(bm):
    """Adds a copy of everything mirrored to starboard (y -> -y, faces flipped)."""
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    dup = bmesh.ops.duplicate(bm, geom=geom)
    verts = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMVert)]
    faces = [e for e in dup["geom"] if isinstance(e, bmesh.types.BMFace)]
    bmesh.ops.transform(bm, matrix=MIRROR_Y, verts=verts)
    bmesh.ops.reverse_faces(bm, faces=faces)


def tag_paint2(ob, value=1):
    a = ob.data.attributes.get("paint2") or ob.data.attributes.new("paint2", "INT", "FACE")
    a.data.foreach_set("value", [value] * len(ob.data.polygons))


def new_object(name, bm, coll, material, bevel, paint2=0, recalc=True, width=None):
    if recalc:
        ob = hp.finish(bm, name, coll, bevel)
    else:
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        hp.add_modifiers(ob, bevel)
    if width is not None:
        ob.modifiers["Bevel"].width = width
    ob.data.materials.append(material)
    tag_paint2(ob, paint2)
    return ob


# --------------------------------------------------------------------------------------------
# Hull
# --------------------------------------------------------------------------------------------

def _in_region(f, reg, side, margin=0.0):
    """Face centre inside a region: x range, optional z / abs-y ranges, normal filter, port (+1) or
    starboard (-1) or both (0). `margin` widens the ranges (the coarse pick before clipping)."""
    c = f.calc_center_median()
    n = f.normal
    m, mn = margin, (0.15 if margin else 0.0)
    if not (reg["x"][0] - m <= c.x <= reg["x"][1] + m):
        return False
    if "z" in reg and not (reg["z"][0] - m <= c.z <= reg["z"][1] + m):
        return False
    if "abs_y" in reg and not (reg["abs_y"][0] - m <= abs(c.y) <= reg["abs_y"][1] + m):
        return False
    if "normal_z" in reg and not (reg["normal_z"][0] - mn <= n.z <= reg["normal_z"][1] + mn):
        return False
    if side and c.y * side <= 0:
        return False
    return True


def _clip_planes(reg, side):
    """The region's bounds as planes (point, outward normal): x always, z and abs-y when given."""
    planes = [((reg["x"][0], 0, 0), (-1, 0, 0)), ((reg["x"][1], 0, 0), (1, 0, 0))]
    if "z" in reg:
        planes += [((0, 0, reg["z"][0]), (0, 0, -1)), ((0, 0, reg["z"][1]), (0, 0, 1))]
    if "abs_y" in reg:
        a0, a1 = reg["abs_y"]
        for sg in ((side,) if side else (1, -1)):
            planes.append(((0, sg * a1, 0), (0, sg, 0)))
            if a0 > 0:
                planes.append(((0, sg * a0, 0), (0, -sg, 0)))
    return planes


def _cut_region(bm, reg, side):
    """Region faces with straight edges: the faces near the region are bisected on its bounds first
    (picking whole faces by their centre gave staircase outlines, 24. 9. 2026), then the ones inside
    are returned."""
    near = [f for f in bm.faces if _in_region(f, reg, side, margin=0.12)]
    for co, no in _clip_planes(reg, side):
        geom = list({e for f in near if f.is_valid for e in list(f.verts) + list(f.edges)} | {f for f in near if f.is_valid})
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no)
        near = [f for f in bm.faces if f.is_valid and _in_region(f, reg, side, margin=0.12)]
    return [f for f in near if _in_region(f, reg, side)]


def hull_plates(hull, specs, coll, mats, bevel):
    """Armour plates: hull faces of the region (clipped to its bounds) copied, solidified outwards by
    "t", bevelled."""
    made = []
    for i, reg in enumerate(specs):
        for side in ((0,) if reg.get("centre") else (1, -1)):
            src = bmesh.new()
            src.from_mesh(hull.data)
            faces = _cut_region(src, reg, side)
            if not faces:
                print("HSDETAIL plate %d side %d: no faces" % (i, side))
                src.free()
                continue
            keep = set(faces)
            bmesh.ops.delete(src, geom=[f for f in src.faces if f not in keep], context="FACES")
            bm = src
            name = "SM_Ship_Detail_Plate_%d%s" % (i, "" if not side else ("_L" if side > 0 else "_R"))
            me = bpy.data.meshes.new(name)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            coll.objects.link(ob)
            ob.data.materials.clear()
            for poly in ob.data.polygons:
                poly.material_index = 0
            ob.data.shade_smooth()
            sol = ob.modifiers.new("Solidify", "SOLIDIFY")
            sol.thickness, sol.offset, sol.use_even_offset = reg.get("t", 0.03), 1.0, True
            hp.add_modifiers(ob, bevel, width=reg.get("bevel", 0.006))
            ob.data.materials.append(mats[reg.get("material", "paint")])
            tag_paint2(ob, 1 if reg.get("secondary") else 0)
            made.append(ob)
    return made


def _frame_of(faces):
    """Centre, mean normal and the in-surface axes (x along the ship) of a face region."""
    c = sum((f.calc_center_median() for f in faces), Vector()) / len(faces)
    n = sum((f.normal * f.calc_area() for f in faces), Vector()).normalized()
    x = (Vector((1, 0, 0)) - n * n.x).normalized()
    return c, n, x, n.cross(x)


def hull_recesses(hull, specs, coll, mats, bevel):
    """Bays cut into the hull: inset frame, walls "depth" deep, dark floor; then what sits inside."""
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    names = [m.name for m in hull.data.materials]
    extra = bmesh.new()
    report = []
    for reg in specs:
        dark = mats[reg.get("floor", "dark")]
        if dark.name not in names:
            hull.data.materials.append(dark)
            names.append(dark.name)
        for side in ((0,) if reg.get("centre") else (1, -1)):
            faces = _cut_region(bm, reg, side)
            if not faces:
                continue
            c, n, x, y = _frame_of(faces)
            ins = bmesh.ops.inset_region(bm, faces=faces, thickness=reg.get("frame", 0.012), depth=0.0,
                                         use_even_offset=True)
            # extrude_face_region returns only the new top faces and keeps the originals: the originals
            # go (they would close the bay), the walls are flipped (extruded inwards they face away)
            ext = bmesh.ops.extrude_face_region(bm, geom=faces)
            verts = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=-n * reg["depth"], verts=verts)
            floor = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMFace)]
            bmesh.ops.delete(bm, geom=[f for f in faces if f.is_valid], context="FACES_ONLY")
            walls = list({f for v in verts for f in v.link_faces} - set(floor))
            bmesh.ops.reverse_faces(bm, faces=walls)
            for f in floor + walls:
                f.material_index = names.index(dark.name)
            del ins
            # contents, in the bay's frame (x along the ship, y across, z out of the floor)
            xs = [v.co.dot(x) for f in floor for v in f.verts]
            ys = [v.co.dot(y) for f in floor for v in f.verts]
            lx, ly = max(xs) - min(xs), max(ys) - min(ys)
            cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
            base = x * cx + y * cy + n * (c.dot(n) - reg["depth"])
            if reg.get("fill") == "louvers":
                count = reg.get("count", 8)
                for k in range(count):
                    off = (k + 0.5) / count - 0.5
                    centre = base + y * (off * ly * 0.92) + n * reg["depth"] * 0.45
                    tilt = n * math.cos(math.radians(55)) + y * math.sin(math.radians(55))
                    oriented_box(extra, centre, x, tilt, (lx * 0.96, reg["depth"] * 0.9, 0.008))
            elif reg.get("fill") == "pipes":
                rs = reg.get("pipe_r", [0.03, 0.022, 0.03])
                for k, r in enumerate(rs):
                    off = (k + 0.5) / len(rs) - 0.5
                    # tops level just under the hull surface: the lines fill the trough in silhouette
                    # (a trough on the roof crest lowered the side outline, 24. 9. 2026)
                    p0 = base + y * (off * ly * 0.75) + n * (reg["depth"] - r - 0.004)
                    a, b = p0 - x * (lx * 0.5 + 0.02), p0 + x * (lx * 0.5 + 0.02)
                    tube(extra, [a, b], r, seg=14)
                for k in range(reg.get("clamps", 3)):
                    t = (k + 0.5) / reg.get("clamps", 3) - 0.5
                    oriented_box(extra, base + x * (t * lx * 0.8) + n * (reg["depth"] / 2 - 0.004), x, n,
                                 (0.035, ly * 0.85, reg["depth"] - 0.008))
                if reg.get("valve"):
                    tube(extra, [base + x * (lx * 0.1) + n * 0.02, base + x * (lx * 0.1) + n * 0.1], 0.045, seg=16)
            report.append({"at": [round(c.x, 2), round(c.y, 2), round(c.z, 2)], "fill": reg.get("fill")})
    bm.to_mesh(hull.data)
    bm.free()
    ob = None
    if extra.verts:
        ob = new_object("SM_Ship_Detail_RecessParts", extra, coll, mats["dark"], bevel, width=0.003)
    else:
        extra.free()
    return report, ob


# --------------------------------------------------------------------------------------------
# Pods
# --------------------------------------------------------------------------------------------

def _pod_frame(axis, x, a, r):
    yc, zc = axis
    return Vector((x, yc + r * math.cos(a), zc + r * math.sin(a)))


def _mirror_angle(a):
    return math.pi - a


def pod_detail(coll, pod_cfg, spec, mats, bevel, ship):
    """Armour sectors, the open bay and the external pipe run on both pods (port built, starboard mirrored)."""
    rev = pod_cfg["revolve"]
    axis = (rev["axis"]["y"], rev["axis"]["z"])
    profile = [tuple(p) for p in rev["profile"]]
    body = next(s for s in rev["sections"] if s["name"] == spec.get("section", "Body"))
    pts = hp.refine(hp.section_points(profile, *body["x"]))
    th = body["thickness"]
    report = {}

    def r_at(x):
        return hp.radius_at(pts, x)

    # 1) armour plate sectors with thickness, sitting on the panels; optional step plate on top
    plates = bmesh.new()
    steps = bmesh.new()
    for p in spec.get("plates", []):
        x0, x1 = p["x"]
        row = [(x0, r_at(x0) + p["t"])] + [(x, r + p["t"]) for x, r in pts if x0 < x < x1] + [(x1, r_at(x1) + p["t"])]
        a0, a1 = math.radians(p["deg"][0]), math.radians(p["deg"][1])
        hp.shell(plates, row, a0, a1, max(4, int((p["deg"][1] - p["deg"][0]) / 4)), axis, p["t"])
        if p.get("step"):
            s = p["step"]
            sx0, sx1 = x0 + s["inset"], x1 - s["inset"]
            da = s["inset"] / r_at((x0 + x1) / 2)
            srow = [(sx0, r_at(sx0) + p["t"] + s["t"])] + [(x, r + p["t"] + s["t"]) for x, r in pts if sx0 < x < sx1] + \
                   [(sx1, r_at(sx1) + p["t"] + s["t"])]
            hp.shell(steps, srow, a0 + da, a1 - da, max(4, int((p["deg"][1] - p["deg"][0]) / 4)), axis, s["t"])
    for b in (plates, steps):
        mirror_into(b)
    made = [new_object("SM_Ship_Detail_PodPlates", plates, coll, mats["paint"], bevel, paint2=1, width=0.006),
            new_object("SM_Ship_Detail_PodPlateSteps", steps, coll, mats["paint"], bevel, paint2=1, width=0.005)]
    report["plates"] = len(spec.get("plates", []))

    # 2) the open service bay: panel(s) and the substructure under them removed, a closed tub inside
    bay = spec.get("bay")
    if bay:
        x0, x1 = bay["x"]
        a0, a1 = math.radians(bay["deg"][0]), math.radians(bay["deg"][1])
        depth = bay["depth"]
        for tag, sign in (("L", 1), ("R", -1)):
            ax = (axis[0] * sign, axis[1])
            for ob in [o for o in coll.objects if o.name.startswith("SM_Ship_%s_Pod_%s_%s_P" % (ship, tag, body["name"]))]:
                c = sum((v.co for v in ob.data.vertices), Vector()) / max(1, len(ob.data.vertices))
                ang = math.atan2(c.z - ax[1], (c.y - ax[0]) * sign) % (2 * math.pi)
                if x0 - 0.1 < c.x < x1 + 0.1 and a0 <= ang <= a1:
                    bpy.data.objects.remove(ob)
            sub = bpy.data.objects.get("SM_Ship_%s_Pod_%s_Substructure" % (ship, tag))
            if sub:
                bm = bmesh.new()
                bm.from_mesh(sub.data)
                kill = []
                for f in bm.faces:
                    c = f.calc_center_median()
                    ang = math.atan2(c.z - ax[1], (c.y - ax[0]) * sign) % (2 * math.pi)
                    if x0 < c.x < x1 and a0 < ang < a1:
                        kill.append(f)
                bmesh.ops.delete(bm, geom=kill, context="FACES")
                bm.to_mesh(sub.data)
                bm.free()
        tub = bmesh.new()
        r_sub = lambda x: r_at(x) - th - 0.004  # noqa: E731
        rf = [(x0, r_sub(x0) - depth), (x1, r_sub(x1) - depth)]
        seg = max(4, int(bay["deg"][1] - bay["deg"][0]) // 4)
        hp.shell(tub, rf, a0, a1, seg, axis, 0.012)
        for xe in (x0, x1 - 0.012):
            hp.shell(tub, [(xe, r_sub(xe) + 0.002), (xe + 0.012, r_sub(xe) + 0.002)], a0, a1, seg, axis, depth + 0.002)
        for ae in (a0, a1):
            w = 0.012 / r_sub(x0)
            hp.shell(tub, [(x0, r_sub(x0) + 0.002), (x1, r_sub(x1) + 0.002)], ae - w / 2, ae + w / 2, 1, axis, depth + 0.002)
        mech = bmesh.new()
        span = a1 - a0
        for k, (fr, r) in enumerate(bay.get("pipes", [[0.25, 0.022], [0.5, 0.018], [0.72, 0.026]])):
            a = a0 + span * fr
            rr = r_sub((x0 + x1) / 2) - depth + r + 0.012
            tube(mech, [_pod_frame(axis, x0 - 0.01, a, rr), _pod_frame(axis, x1 + 0.01, a, rr)], r, seg=14)
        # actuator: cylinder with a rod, on brackets
        act = bay.get("actuator")
        if act:
            a = a0 + span * act["at"]
            rr = r_sub((x0 + x1) / 2) - depth + act["r"] + 0.03
            xa, xb = act["x"]
            tube(mech, [_pod_frame(axis, xa, a, rr), _pod_frame(axis, xa + (xb - xa) * 0.6, a, rr)], act["r"], seg=16, bend=0.001)
            tube(mech, [_pod_frame(axis, xa + (xb - xa) * 0.55, a, rr), _pod_frame(axis, xb, a, rr)], act["r"] * 0.4, seg=12, bend=0.001)
            for xe in (xa, xb):
                p = _pod_frame(axis, xe, a, rr - act["r"] - 0.012)
                outward = (p - Vector((xe, axis[0], axis[1]))).normalized()
                oriented_box(mech, p, Vector((1, 0, 0)), outward, (0.05, act["r"] * 2.2, 0.05))
        for k in range(bay.get("clamps", 3)):
            xc = x0 + (x1 - x0) * (k + 1) / (bay.get("clamps", 3) + 1)
            p = _pod_frame(axis, xc, (a0 + a1) / 2, r_sub(xc) - depth + 0.03)
            outward = (p - Vector((xc, axis[0], axis[1]))).normalized()
            oriented_box(mech, p, Vector((1, 0, 0)), outward, (0.03, (r_sub(xc) - depth) * span * 0.9, 0.05))
        for b in (tub, mech):
            mirror_into(b)
        made.append(new_object("SM_Ship_Detail_PodBay", tub, coll, mats["dark"], bevel, width=0.004))
        made.append(new_object("SM_Ship_Detail_PodBayMech", mech, coll, mats["metal"], bevel, width=0.003))
        report["bay"] = {"x": bay["x"], "deg": bay["deg"], "depth": depth}

    # 3) external pipe run along the pod with clamps, ends bending into the panels
    run = spec.get("pipe_run")
    if run:
        pipes = bmesh.new()
        clamps = bmesh.new()
        x0, x1 = run["x"]
        for deg, r in run["pipes"]:
            a = math.radians(deg)
            lift = run["standoff"] + r
            path = [_pod_frame(axis, x0, a, r_at(x0) - 0.01),
                    _pod_frame(axis, x0 + 0.15, a, r_at(x0 + 0.15) + lift),
                    _pod_frame(axis, x1 - 0.15, a, r_at(x1 - 0.15) + lift),
                    _pod_frame(axis, x1, a, r_at(x1) - 0.01)]
            tube(pipes, path, r, seg=14, bend=0.1)
        degs = [d for d, _ in run["pipes"]]
        am = math.radians(sum(degs) / len(degs))
        width = (max(degs) - min(degs) + 8) * math.pi / 180 * r_at((x0 + x1) / 2)
        n = run.get("clamps", 5)
        for k in range(n):
            xc = x0 + 0.3 + (x1 - x0 - 0.6) * k / max(1, n - 1)
            p = _pod_frame(axis, xc, am, r_at(xc) + run["standoff"] * 0.5 + 0.01)
            outward = (p - Vector((xc, axis[0], axis[1]))).normalized()
            oriented_box(clamps, p, Vector((1, 0, 0)), outward, (0.04, width, run["standoff"] + 0.03))
        for b in (pipes, clamps):
            mirror_into(b)
        made.append(new_object("SM_Ship_Detail_PodPipes", pipes, coll, mats["metal"], bevel, width=0.002))
        made.append(new_object("SM_Ship_Detail_PodClamps", clamps, coll, mats["dark"], bevel, width=0.003))
        report["pipes"] = len(run["pipes"])
    return made, report


def apply(recipe, made, coll, mats, ship):
    """Entry point from hs_build_ship.py (after the hull zones, before greebles and the canopy cut)."""
    spec = recipe.get("detail")
    if not spec:
        return {}
    bevel = spec.get("bevel", {"angle_deg": 30, "width": 0.006, "segments": 2})
    report = {}
    objs = []
    hull = made.get("hull")
    if hull is not None and spec.get("hull_recesses"):
        report["recesses"], ob = hull_recesses(hull, spec["hull_recesses"], coll, mats, bevel)
        if ob:
            objs.append(ob)
    if hull is not None and spec.get("hull_plates"):
        objs += hull_plates(hull, spec["hull_plates"], coll, mats, bevel)
        report["hull_plates"] = len(spec["hull_plates"])
    if spec.get("pod"):
        more, report["pod"] = pod_detail(coll, recipe["parts"]["pod"], spec["pod"], mats, bevel, ship)
        objs += more
    for key in list(made):
        try:
            made[key].name
        except ReferenceError:
            del made[key]    # pod panels removed for the open bay
    for ob in objs:
        made["detail_" + ob.name] = ob
    report["objects"] = [o.name for o in objs]
    return report
