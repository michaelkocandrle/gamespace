"""Hard-surface ship exterior built straight from the approved 2D drawing (no AI geometry).

    MSYS_NO_PATHCONV=1 blender -b --factory-startup --python Tools/Blender/hs_build_ship.py -- ArtSource/Ships/<Ship>/HardSurface/<Ship>_hs.json

The drawing (Design/<Ship>_layout.json, block "exterior") has every piece of the ship in three views
(side x-z, top x-y, front y-z), tied together by "part". This script turns them into solids that match
the drawing by construction:
  - the hull (kind "hull") is a loft: at every station along x its section is the front-view outline,
    scaled to the half width of the top view and the height of the side view there;
  - every other part is the intersection of its outlines extruded through the other axes (a visual hull):
    boxy, exact, the right base for hard-surface detail;
  - a part missing from a view borrows it from another part ("borrow" in the recipe, e.g. the nozzle
    takes the pod's round front outline);
  - the canopy is cut out of the hull where the canopy outline is (side and top) - its own mesh, glass;
  - bevel (angle-limited, harden normals) and weighted normals on every part.
Coordinates are the layout's: metres, x forward from the aft end of the hull, y port, z up from the deck.
Writes recipe["out_blend"] (collection HS_<Ship>, one object per part) and prints HSSHIP {...}.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BIG = 60.0


def path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def polys_of(entry, view):
    """The entry's polygon(s) in view coordinates, with the mirrored copy for top / front."""
    if "circle" in entry:
        cx, cy, r = entry["circle"]
        base = [(cx + r * math.cos(t * math.pi / 32), cy + r * math.sin(t * math.pi / 32)) for t in range(64)]
    else:
        base = [tuple(v) for v in entry["poly"]]
    out = [base]
    if entry.get("mirror") and view in ("top", "front"):
        out.append([(a, -b) for a, b in base] if view == "top" else [(-a, b) for a, b in base])
    return out


def ccw(poly):
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if area > 0 else poly[::-1]


def prism(name, polys, view):
    """Polygons of one view extruded through the missing axis, one closed mesh."""
    bm = bmesh.new()
    for poly in polys:
        poly = ccw(poly)
        lo, hi = [], []
        for a, b in poly:
            if view == "side":      # (x, z), extruded along y
                lo.append(bm.verts.new((a, -BIG, b))); hi.append(bm.verts.new((a, BIG, b)))
            elif view == "top":     # (x, y), along z
                lo.append(bm.verts.new((a, b, -BIG))); hi.append(bm.verts.new((a, b, BIG)))
            else:                   # front (y, z), along x
                lo.append(bm.verts.new((-BIG, a, b))); hi.append(bm.verts.new((BIG, a, b)))
        n = len(poly)
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        for i in range(n):
            bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def intersect(base, others):
    bpy.context.view_layer.objects.active = base
    for o in others:
        mod = base.modifiers.new("x_" + o.name, "BOOLEAN")
        mod.operation, mod.solver, mod.object = "INTERSECT", "EXACT", o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for o in others:
        bpy.data.objects.remove(o)
    return base


def span_at(poly, x, axis_other=1):
    """Min and max of the other coordinate where the vertical line at x crosses the polygon."""
    vals = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (x0 - x) * (x1 - x) <= 0 and x0 != x1:
            t = (x - x0) / (x1 - x0)
            vals.append(y0 + t * (y1 - y0))
        elif x0 == x == x1:
            vals += [y0, y1]
    return (min(vals), max(vals)) if vals else None


def resample(poly, n):
    """n points evenly spaced along a closed polygon's perimeter, starting at its lowest-left vertex."""
    pts = [Vector(p) for p in poly]
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    total = sum((b - a).length for a, b in segs)
    out, acc, k = [], 0.0, 0
    for i in range(n):
        target = total * i / n
        while acc + (segs[k][1] - segs[k][0]).length < target and k < len(segs) - 1:
            acc += (segs[k][1] - segs[k][0]).length
            k += 1
        a, b = segs[k]
        t = (target - acc) / max((b - a).length, 1e-9)
        out.append(a + (b - a) * t)
    return out


def loft(name, side_poly, top_poly, front_poly, step, ring, seams=None):
    """Hull loft: the front outline, normalised to its bounding box, scaled at each station to the top
    view's half width and the side view's bottom / top. seams: real panel lines, grooves cut into the
    surface - rings at stations "x" and lines along the hull at section heights "around" ([side, v] with
    side +1 port / -1 starboard and v 0 bottom .. 1 top), "width" and "depth" in metres."""
    seams = seams or {}
    depth, half = seams.get("depth", 0.0), seams.get("width", 0.02) / 2
    fp = ccw(front_poly)
    fy0, fy1 = min(p[0] for p in fp), max(p[0] for p in fp)
    fz0, fz1 = min(p[1] for p in fp), max(p[1] for p in fp)
    sub = 8
    dense = [((p.x - fy0) / (fy1 - fy0) * 2 - 1, (p.y - fz0) / (fz1 - fz0)) for p in resample(fp, ring * sub)]
    # longitudinal seams: the dense point on the requested side nearest the requested height, plus the
    # groove's two walls one dense step either side
    marks = []
    for side, v in seams.get("around", []):
        cand = [i for i, (u, _) in enumerate(dense) if u * side > 0.85]
        if cand:
            marks.append(min(cand, key=lambda i: abs(dense[i][1] - v)))
    keep = set(range(0, len(dense), sub))
    for m in marks:
        keep -= {m - 1, m + 1}
        keep |= {(m - 1) % len(dense), m, (m + 1) % len(dense)}
    order = sorted(keep)
    template = [dense[i] for i in order]
    groove_idx = {order.index(m) for m in marks}
    ring = len(template)
    x0, x1 = min(p[0] for p in side_poly), max(p[0] for p in side_poly)
    stations = [(x0 + i * step, False) for i in range(int((x1 - x0) / step) + 1)]
    if stations[-1][0] < x1:
        stations.append((x1, False))
    for sx in seams.get("x", []):
        stations = [st for st in stations if abs(st[0] - sx) > half * 1.5]
        stations += [(sx - half, False), (sx, True), (sx + half, False)]
    stations.sort()
    bm = bmesh.new()
    rows = []
    for x, is_seam in stations:
        xs = min(max(x, x0 + 1e-4), x1 - 1e-4)
        zb, zt = span_at(side_poly, xs)
        w = span_at(top_poly, xs)
        hw = max(abs(w[0]), abs(w[1])) if w else 0.01
        hw = max(hw, 0.01)
        zt = max(zt, zb + 0.01)
        row = []
        for k, (u, v) in enumerate(template):
            y, z = u * hw, zb + v * (zt - zb)
            if depth and (is_seam or k in groove_idx) and hw > 0.3:
                d = Vector((u * hw, (v - 0.5) * (zt - zb)))
                if d.length > 1e-6:
                    d.normalize()
                    y, z = y - d.x * depth, z - d.y * depth
            row.append(bm.verts.new((x, y, z)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(ring):
            bm.faces.new((r0[i], r0[(i + 1) % ring], r1[(i + 1) % ring], r1[i]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def inside(poly, a, b):
    c = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > b) != (y1 > b) and a < (x1 - x0) * (b - y0) / (y1 - y0) + x0:
            c = not c
    return c


def cut_polyline(bm, pts, view, x_range=None, z_min=None):
    """Bisects the mesh along a polyline of one view (side: (x, z) segments -> planes containing y; top:
    (x, y) segments -> planes containing z), each segment only on faces within its own x span, so the
    cut follows the drawn line exactly instead of the triangles' zig-zag."""
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        if abs(a1 - a0) < 1e-6:
            continue
        if view == "side":
            co, no = Vector((a0, 0, b0)), Vector((-(b1 - b0), 0, a1 - a0)).normalized()
        else:
            co, no = Vector((a0, b0, 0)), Vector((-(b1 - b0), a1 - a0, 0)).normalized()
        lo, hi = min(a0, a1) - 0.02, max(a0, a1) + 0.02
        faces = [f for f in bm.faces if lo <= f.calc_center_median().x <= hi and (z_min is None or f.calc_center_median().z > z_min)]
        geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
        if geom:
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no)


def split_canopy(hull, side_polys, top_polys, name, frame=None):
    """Hull faces inside the canopy outline (side and top) move to their own object, recessed a little;
    the frame (strut rings at struts_x, a spine along the top) stays hull."""
    frame = frame or {}
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    # cut the hull exactly along the canopy's lower edge (side) and outline (top), and at the struts
    for sp in side_polys:
        xs = [p[0] for p in sp]
        lower = sorted({(round(x, 4), span_at(sp, x)[0]) for x in xs if span_at(sp, x)})
        cut_polyline(bm, lower, "side", z_min=0.8)
    for tp in top_polys:
        cut_polyline(bm, list(tp) + [tp[0]], "top", z_min=0.8)
    for sx in frame.get("struts_x", []):
        for d in (-1, 1):
            x = sx + d * frame.get("strut_width", 0.0) / 2
            faces = [f for f in bm.faces if abs(f.calc_center_median().x - x) < 0.3 and f.calc_center_median().z > 0.8]
            geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
            if geom:
                bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector((x, 0, 0)), plane_no=Vector((1, 0, 0)))
    for d in (-1, 1):
        y = d * frame.get("spine_width", 0.0) / 2
        faces = [f for f in bm.faces if f.calc_center_median().z > 1.5 and f.calc_center_median().x > 14.5]
        geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
        if geom and y:
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector((0, y, 0)), plane_no=Vector((0, 1, 0)))
    # The hull's top follows the canopy's upper edge exactly, so a point-in-polygon test on the side outline
    # flickers along it (striped glass). Test against the canopy's LOWER edge only: above it, inside the top
    # outline, facing up or sideways.
    def lower_edge(x):
        spans = [span_at(p, x) for p in side_polys]
        spans = [s for s in spans if s]
        return min(s[0] for s in spans) if spans else None

    def is_glass(f):
        c = f.calc_center_median()
        z0 = lower_edge(c.x)
        return (z0 is not None and c.z >= z0 - 0.01 and any(inside(p, c.x, c.y) for p in top_polys)
                and f.normal.z > -0.2)
    struts, spine = frame.get("struts_x", []), frame.get("spine_width", 0.0) / 2
    strut_half = frame.get("strut_width", 0.0) / 2

    def is_frame(f):
        c = f.calc_center_median()
        return any(abs(c.x - sx) < strut_half for sx in struts) or abs(c.y) < spine
    glass = [f for f in bm.faces if is_glass(f) and not is_frame(f)]
    gbm = bmesh.new()
    vmap = {}
    for f in glass:
        vs = []
        for v in f.verts:
            if v.index not in vmap:
                vmap[v.index] = gbm.verts.new(v.co)
            vs.append(vmap[v.index])
        gbm.faces.new(vs)
    bmesh.ops.delete(bm, geom=glass, context="FACES")
    bm.to_mesh(hull.data)
    bm.free()
    gbm.normal_update()
    recess = frame.get("recess", 0.0)
    for v in gbm.verts:
        v.co -= v.normal * recess
    me = bpy.data.meshes.new(name)
    gbm.to_mesh(me)
    gbm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, len(glass)


def place_greebles(hull, specs, coll, bevel):
    """Kit parts (Tools/Blender/hs_build_part.py kit: vent, hatch, sensor, strip, bolt, hatch_large) on the
    hull: a ray from outside ("side" +1 port / -1 starboard, or "top" / "bottom") at x and height z (or y)
    finds the surface; the part lies on it, long side along the hull."""
    from mathutils.bvhtree import BVHTree
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hs_build_part
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    tree = BVHTree.FromBMesh(bm)
    places = []
    for g in specs:
        for sign in ((1, -1) if g.get("mirror", True) and g["from"] in ("side",) else (1,)):
            if g["from"] == "side":
                origin, d = Vector((g["x"], sign * 10.0, g["z"])), Vector((0, -sign, 0))
            elif g["from"] == "top":
                origin, d = Vector((g["x"], g.get("y", 0.0), 10.0)), Vector((0, 0, -1))
            else:
                origin, d = Vector((g["x"], g.get("y", 0.0), -10.0)), Vector((0, 0, 1))
            hit, normal, _, _ = tree.ray_cast(origin, d)
            if hit is None:
                continue
            # the part's footprint can straddle a seam groove or a curvature change: one ray's normal
            # then tilts the whole part (the roof hatch stood up at an angle, 24. 9. 2026). Average the
            # normals of rays over the footprint (along the ship and across it).
            across = Vector((0, 0, 1)) if g["from"] == "side" else Vector((0, 1, 0))
            normals = [normal]
            for dx, da in ((0.4, 0), (-0.4, 0), (0, 0.25), (0, -0.25), (0.25, 0.15), (-0.25, -0.15)):
                h2, n2, _, _ = tree.ray_cast(origin + Vector((dx, 0, 0)) + across * da, d)
                if h2 is not None and (h2 - hit).length < 0.6 and n2.dot(normal) > 0.5:
                    normals.append(n2)
            normal = sum(normals, Vector()).normalized()
            z = normal.normalized()
            xdir = (Vector((1, 0, 0)) - z * z.x).normalized()
            y = z.cross(xdir)
            rot = Matrix((xdir, y, z)).transposed().to_euler()
            places.append((tuple(hit + z * 0.002), g["part"], tuple(rot)))
    bm.free()
    kit = hs_build_part.build_kit(bevel)
    inst = hs_build_part.build_instancer(kit)
    hs_build_part.kit_points("SM_Ship_Hull_Greebles", coll, places, inst)
    return len(places)


def material(name, colour, rough, metal, emit=None, alpha=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*colour, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1)
        bsdf.inputs["Emission Strength"].default_value = 6.0
    if alpha is not None:
        bsdf.inputs["Alpha"].default_value = alpha
    return m


def finish(ob, bevel):
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(bevel.get("sharp_deg", 35)))
    if bevel.get("width", 0) > 0:
        mod = ob.modifiers.new("Bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel["width"], bevel.get("segments", 2), "ANGLE"
        mod.angle_limit = math.radians(bevel.get("angle_deg", 30))
        mod.harden_normals = True
        mod.miter_outer = "MITER_ARC"
    ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL").keep_sharp = True


def main(argv):
    recipe = json.load(open(path(argv[0]), encoding="utf-8"))
    layout = json.load(open(path(recipe["layout"]), encoding="utf-8"))
    ship = layout["ship"]
    ext = layout["exterior"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.data.collections.new("HS_%s" % ship)
    bpy.context.scene.collection.children.link(coll)
    views = {}
    for view in ("side", "top", "front"):
        for e in ext[view]:
            views.setdefault(e["part"], {}).setdefault(view, e)    # first entry of a part in a view wins
    for part, spec in recipe.get("borrow", {}).items():
        for view, other in spec.items():
            if other in views and view in views[other]:
                views.setdefault(part, {})[view] = views[other][view]
    mats = {k: material("M_Ship_%s_%s" % (ship, v["slot"]), tuple(v["colour"]), v["roughness"], v["metallic"],
                        tuple(v["emit"]) if "emit" in v else None) for k, v in recipe["materials"].items()}
    made, report = {}, {}
    for part, vs in views.items():
        cfg = recipe["parts"].get(part, {})
        if cfg.get("skip"):
            continue
        name = "SM_Ship_%s_%s" % (ship, cfg.get("name", part.title().replace("_", "")))
        if cfg.get("revolve"):
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import hs_build_part
            for sign, tag in ((1, "L"), (-1, "R")):
                rec = json.loads(json.dumps(cfg["revolve"]))
                rec["name"] = "%s_%s" % (name, tag)
                rec["axis"] = {"y": cfg["revolve"]["axis"]["y"] * sign, "z": cfg["revolve"]["axis"]["z"]}
                if sign < 0:
                    # the starboard pod is the port one mirrored: panel breaks at 180 - phase (the same
                    # phase put the starboard gaps elsewhere, so decals fitting port crossed a gap)
                    for sec in rec["sections"]:
                        if sec.get("kind") == "panels":
                            span = 360.0 / sec["around"]
                            sec["phase_deg"] = (180.0 - sec.get("phase_deg", 0.0)) % span
                before = set(bpy.data.objects)
                hs_build_part.build_into(rec, coll)
                for ob in set(bpy.data.objects) - before:
                    if ob.type != "MESH" or coll not in ob.users_collection:
                        continue
                    key = next((k for k in cfg.get("materials", {}) if k in ob.name), None)
                    ob.data.materials.append(mats[cfg["materials"][key] if key else cfg.get("material", "paint")])
                    made["%s_%s" % (part, ob.name)] = ob
            report[part] = {"revolved": True}
            continue
        if cfg.get("cylinders"):
            bm = bmesh.new()
            for c in cfg["cylinders"]:
                for sign in ((1, -1) if c.get("mirror") else (1,)):
                    x0c, x1c = c["x"]
                    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=c.get("segments", 24), radius1=c["r"],
                                                radius2=c.get("r2", c["r"]), depth=x1c - x0c)
                    bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
                    bmesh.ops.translate(bm, verts=res["verts"], vec=((x0c + x1c) / 2, c["y"] * sign, c["z"]))
            me = bpy.data.meshes.new(name)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            coll.objects.link(ob)
            ob.data.materials.append(mats[cfg.get("material", "dark")])
            made[part] = ob
            report[part] = {"object": name, "cylinders": len(cfg["cylinders"])}
            continue
        if cfg.get("loft"):
            ob = loft(name, ccw(polys_of(vs["side"], "side")[0]), polys_of(vs["top"], "top")[0],
                      polys_of(vs["front"], "front")[0], cfg.get("step", 0.05), cfg.get("ring", 96), cfg.get("seams"))
        else:
            if len(vs) < 2:
                print("HSSHIP skip %s: only in %s" % (part, list(vs)))
                continue
            prisms = [prism("%s_%s" % (name, v), polys_of(e, v), v) for v, e in vs.items()]
            ob = intersect(prisms[0], prisms[1:])
            ob.name = ob.data.name = name
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
        ob.data.materials.append(mats[cfg.get("material", "paint")])
        made[part] = ob
        report[part] = {"object": name, "faces": len(ob.data.polygons), "views": sorted(vs)}
    if recipe.get("wings"):
        # shaped wings and fins with leading edge, flaps and fairings inside the drawing's slab
        # (Tools/Blender/hs_wings.py)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import hs_wings
        for part, wspec in recipe["wings"].items():
            if part.startswith("_") or part not in made:
                continue
            slab = made.pop(part)
            new = hs_wings.build(slab, wspec, coll, mats, recipe.get("detail", {}).get("bevel", {"angle_deg": 30, "width": 0.006, "segments": 2}),
                                 slab.name)
            bpy.data.objects.remove(slab)
            for ob in new:
                made["wing_" + ob.name] = ob
            report[part] = {"shaped": [ob.name for ob in new]}
    hz = recipe["parts"].get("hull", {}).get("zones", [])
    if hz and "hull" in made:
        hull = made["hull"]
        bm = bmesh.new()
        bm.from_mesh(hull.data)
        for z in hz:
            for cut in z.get("cuts", []):
                if cut["view"] in ("x", "z"):
                    # a straight cut at x = value or z = value, across the whole hull
                    no = Vector((1, 0, 0)) if cut["view"] == "x" else Vector((0, 0, 1))
                    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
                    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=no * cut["value"], plane_no=no)
                else:
                    cut_polyline(bm, cut["points"], cut["view"], z_min=cut.get("z_min"))
        slots = {}
        for z in hz:
            m = mats[z["material"]]
            if m.name not in [x.name for x in hull.data.materials]:
                hull.data.materials.append(m)
            slots[z["name"]] = [x.name for x in hull.data.materials].index(m.name)
        bm.to_mesh(hull.data)
        bm.free()
        bm = bmesh.new()
        bm.from_mesh(hull.data)
        for z in hz:
            t = z["where"]
            for f in bm.faces:
                c = f.calc_center_median()
                if all(t[k][0] <= getattr(c, k) <= t[k][1] for k in ("x", "z") if k in t) and \
                        ("abs_y" not in t or t["abs_y"][0] <= abs(c.y) <= t["abs_y"][1]) and \
                        ("normal_abs_y_min" not in t or abs(f.normal.y) >= t["normal_abs_y_min"]):
                    f.material_index = slots[z["name"]]
        bm.to_mesh(hull.data)
        bm.free()
        report["hull_zones"] = [z["name"] for z in hz]
    if recipe.get("detail"):
        # medium shape layer on the exact base (Tools/Blender/hs_detail.py): before greebles and the canopy
        # cut, so rays see the plates and recesses
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import hs_detail
        report["detail"] = hs_detail.apply(recipe, made, coll, mats, ship)
    if recipe.get("lights"):
        # light fittings and emissive strips (Tools/Blender/hs_lights.py); the real lights go to the scene
        # property hs_lights for hs_assemble_ship.py
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import hs_lights
        report["lights"] = hs_lights.apply(recipe, made, coll, lambda key: mats[key],
                                           recipe.get("detail", {}).get("bevel", {"angle_deg": 30, "width": 0.006, "segments": 2}))
    if recipe["parts"].get("hull", {}).get("greebles") and "hull" in made:
        report["hull_greebles"] = place_greebles(made["hull"], recipe["parts"]["hull"]["greebles"], coll, recipe.get("kit_bevel", {"angle_deg": 30, "width": 0.004, "segments": 2}))
    if "canopy" in views and "hull" in made:
        cv = views["canopy"]
        glass, n = split_canopy(made["hull"], polys_of(cv["side"], "side"), polys_of(cv["top"], "top"),
                                "SM_Ship_%s_Canopy" % ship, recipe.get("canopy_frame"))
        for c in list(glass.users_collection):
            c.objects.unlink(glass)
        coll.objects.link(glass)
        glass.data.materials.append(mats["glass"])
        made["canopy"] = glass
        report["canopy"] = {"object": glass.name, "faces": n, "cut_from": "hull"}
    for part, ob in made.items():
        if ob.modifiers:
            continue   # revolved parts come finished from hs_build_part
        finish(ob, recipe.get("bevel", {}) if part != "canopy" else {"sharp_deg": 60})
    out = path(recipe["out_blend"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("HSSHIP " + json.dumps({"out": recipe["out_blend"], "parts": report}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
