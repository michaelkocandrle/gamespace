"""Hard-surface part builder: a revolved part (engine nacelle, tank, turret ring...) from a JSON recipe.

The AI model only gives the volume (axis + radius profile measured on it). The part is built as real
hard-surface geometry:
  - separate panels with real gaps (sector shells with thickness) over a dark substructure,
  - solid rings for bands, flanges and grooves, with steps between sections,
  - intake and exhaust as modelled ducts with hub, spokes and ring,
  - bevel (angle limited, harden normals) + weighted normals on everything,
  - greebles and bolts from a reusable kit (collection HS_Kit) instanced by the geometry-nodes group
    HS_KitInstancer on a point cloud whose attributes (kit_index, rot) say what goes where.

    MSYS_NO_PATHCONV=1 blender -b --factory-startup --python Tools/Blender/hs_build_part.py -- ArtSource/Ships/<Ship>/HardSurface/nacelle.json

Writes recipe["out_blend"]; everything lives in the collection HS_<name>. Blender coordinates, metres.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
KIT_NAMES = ["vent", "hatch", "sensor", "strip", "bolt", "hatch_large"]


# --------------------------------------------------------------------------------------------
# Profile helpers
# --------------------------------------------------------------------------------------------

def section_points(profile, x0, x1):
    """Profile points of one section. A step is two points at the same x: the section starting there
    takes the later one, the section ending there the earlier one."""
    pts = []
    for i, (x, r) in enumerate(profile):
        if x0 < x < x1:
            pts.append((x, r))
        elif x == x0 and (i + 1 >= len(profile) or profile[i + 1][0] != x0):
            pts.append((x, r))
        elif x == x1 and (i == 0 or profile[i - 1][0] != x1):
            pts.append((x, r))
    return pts


def radius_at(pts, x):
    for (xa, ra), (xb, rb) in zip(pts, pts[1:]):
        if xa <= x <= xb and xb > xa:
            return ra + (rb - ra) * (x - xa) / (xb - xa)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]


def slope_at(pts, x):
    for (xa, ra), (xb, rb) in zip(pts, pts[1:]):
        if xa <= x <= xb and xb > xa:
            return (rb - ra) / (xb - xa)
    return 0.0


def refine(pts, step=0.1):
    """Extra rings along long spans so tapered panels stay smooth."""
    out = [pts[0]]
    for (xa, ra), (xb, rb) in zip(pts, pts[1:]):
        n = max(1, int(math.ceil((xb - xa) / step)))
        for k in range(1, n + 1):
            t = k / n
            out.append((xa + (xb - xa) * t, ra + (rb - ra) * t))
    return out


# --------------------------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------------------------

def surface_grid(bm, pts, a0, a1, n, axis, offset=0.0, full=False):
    """Rows of verts: one ring per profile point, n+1 (or n when full) per ring."""
    yc, zc = axis
    cols = n if full else n + 1
    rows = []
    for x, r in pts:
        rr = r + offset
        ring = []
        for j in range(cols):
            a = a0 + (a1 - a0) * j / n
            ring.append(bm.verts.new((x, yc + rr * math.cos(a), zc + rr * math.sin(a))))
        rows.append(ring)
    return rows


def bridge(bm, rows, full, flip=False):
    faces = []
    for ra, rb in zip(rows, rows[1:]):
        cols = len(ra)
        for j in range(cols if full else cols - 1):
            k = (j + 1) % cols
            quad = [ra[j], ra[k], rb[k], rb[j]]
            faces.append(bm.faces.new(quad[::-1] if flip else quad))
    return faces


def shell(bm, pts, a0, a1, n, axis, thickness, full=False):
    """Closed shell between the outer surface and one `thickness` below it."""
    outer = surface_grid(bm, pts, a0, a1, n, axis, 0.0, full)
    inner = surface_grid(bm, pts, a0, a1, n, axis, -thickness, full)
    bridge(bm, outer, full)
    bridge(bm, inner, full, flip=True)
    # End caps (annuli at both x ends).
    for ro, ri in ((outer[0], inner[0]), (outer[-1], inner[-1])):
        cols = len(ro)
        for j in range(cols if full else cols - 1):
            k = (j + 1) % cols
            bm.faces.new([ro[j], ri[j], ri[k], ro[k]])
    if not full:
        for side in (0, -1):
            for ra_o, rb_o, ra_i, rb_i in zip([r[side] for r in outer], [r[side] for r in outer[1:]],
                                              [r[side] for r in inner], [r[side] for r in inner[1:]]):
                bm.faces.new([ra_o, rb_o, rb_i, ra_i])


def finish(bm, name, coll, bevel, smooth=True):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    limit = math.radians(bevel["angle_deg"])
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < limit
        else:
            e.smooth = False
    for f in bm.faces:
        f.smooth = smooth
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    add_modifiers(ob, bevel)
    return ob


def add_modifiers(ob, bevel, width=None):
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(bevel["angle_deg"])
    m.width = width if width is not None else bevel["width"]
    m.segments = bevel["segments"]
    m.harden_normals = True
    m.miter_outer = "MITER_ARC"
    w = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    w.keep_sharp = True
    w.mode = "FACE_AREA"


def box(bm, cx, cy, cz, sx, sy, sz):
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=res["verts"])
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=res["verts"])


def cyl(bm, cx, cy, cz, r, h, seg=12, axis="Z"):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    bmesh.ops.translate(bm, vec=(cx, cy, cz), verts=res["verts"])


# --------------------------------------------------------------------------------------------
# Kit: reusable greebles + the geometry-nodes instancer
# --------------------------------------------------------------------------------------------

def build_kit(bevel):
    """Kit parts sit on z=0 facing +Z, long side along +X (the ship's axis)."""
    kit = bpy.data.collections.get("HS_Kit") or bpy.data.collections.new("HS_Kit")
    if kit.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(kit)
    shapes = {}

    def vent(bm):
        box(bm, 0, 0, 0.0075, 0.42, 0.24, 0.015)
        for k in range(7):
            box(bm, 0, -0.09 + k * 0.03, 0.025, 0.36, 0.014, 0.022)

    def hatch(bm):
        box(bm, 0, 0, 0.01, 0.62, 0.42, 0.02)
        box(bm, 0, 0, 0.026, 0.50, 0.30, 0.012)
        for sy in (-0.1, 0.1):
            box(bm, 0.18, sy, 0.042, 0.09, 0.02, 0.02)
        for sx in (-0.27, 0.27):
            for sy in (-0.17, 0.17):
                cyl(bm, sx, sy, 0.024, 0.012, 0.01, 6)

    def sensor(bm):
        box(bm, 0, 0, 0.03, 0.16, 0.10, 0.06)
        cyl(bm, 0.05, 0, 0.065, 0.025, 0.02, 16)

    def strip(bm):
        box(bm, 0, 0, 0.009, 0.55, 0.07, 0.018)
        for sx in (-0.23, 0.23):
            cyl(bm, sx, 0, 0.021, 0.011, 0.008, 6)

    def bolt(bm):
        cyl(bm, 0, 0, 0.005, 0.014, 0.01, 6)

    def hatch_large(bm):
        # Service door: raised frame, recessed door leaf, hinge line and latch.
        box(bm, 0, 0, 0.012, 1.10, 0.70, 0.024)
        box(bm, 0, 0, 0.027, 0.98, 0.58, 0.008)
        box(bm, -0.46, 0, 0.036, 0.04, 0.52, 0.018)
        box(bm, 0.40, 0, 0.038, 0.10, 0.14, 0.02)
        for sx in (-0.5, 0.5):
            for sy in (-0.3, 0, 0.3):
                cyl(bm, sx, sy, 0.028, 0.012, 0.01, 6)

    makers = {"vent": vent, "hatch": hatch, "sensor": sensor, "strip": strip, "bolt": bolt,
              "hatch_large": hatch_large}
    for i, name in enumerate(KIT_NAMES):
        obj_name = "HSKit_%d_%s" % (i, name)
        if obj_name in bpy.data.objects:
            shapes[name] = bpy.data.objects[obj_name]
            continue
        bm = bmesh.new()
        makers[name](bm)
        ob = finish(bm, obj_name, kit, bevel)
        ob.modifiers["Bevel"].width = 0.003
        shapes[name] = ob
    # The kit is a library: excluded from the view layer so only its instances render.
    lc = bpy.context.view_layer.layer_collection.children.get(kit.name)
    if lc:
        lc.exclude = True
    return kit


def build_instancer(kit):
    ng = bpy.data.node_groups.get("HS_KitInstancer")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("HS_KitInstancer", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n = ng.nodes
    gin, gout = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    coll = n.new("GeometryNodeCollectionInfo")
    coll.inputs["Collection"].default_value = kit
    coll.inputs["Separate Children"].default_value = True
    coll.inputs["Reset Children"].default_value = True
    idx = n.new("GeometryNodeInputNamedAttribute")
    idx.data_type = "INT"
    idx.inputs["Name"].default_value = "kit_index"
    rot = n.new("GeometryNodeInputNamedAttribute")
    rot.data_type = "FLOAT_VECTOR"
    rot.inputs["Name"].default_value = "rot"
    e2r = n.new("FunctionNodeEulerToRotation")
    inst = n.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Pick Instance"].default_value = True
    link = ng.links.new
    link(gin.outputs[0], inst.inputs["Points"])
    link(coll.outputs[0], inst.inputs["Instance"])
    link(idx.outputs["Attribute"], inst.inputs["Instance Index"])
    link(rot.outputs["Attribute"], e2r.inputs[0])
    link(e2r.outputs[0], inst.inputs["Rotation"])
    link(inst.outputs["Instances"], gout.inputs[0])
    return ng


def kit_points(name, coll, placements, instancer):
    """Point cloud with kit_index + rot (Euler) per point, instanced by HS_KitInstancer."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([p[0] for p in placements], [], [])
    ia = me.attributes.new("kit_index", "INT", "POINT")
    ra = me.attributes.new("rot", "FLOAT_VECTOR", "POINT")
    ia.data.foreach_set("value", [KIT_NAMES.index(p[1]) for p in placements])
    flat = []
    for p in placements:
        flat.extend(p[2])
    ra.data.foreach_set("vector", flat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    mod = ob.modifiers.new("Kit", "NODES")
    mod.node_group = instancer
    return ob


def surface_frame(pts, axis, x, angle):
    """Position and Euler on the outer surface at (x, angle): +Z out of the surface, +X along it."""
    yc, zc = axis
    r, s = radius_at(pts, x), slope_at(pts, x)
    ca, sa = math.cos(angle), math.sin(angle)
    pos = Vector((x, yc + r * ca, zc + r * sa))
    tx = Vector((1.0, s * ca, s * sa)).normalized()
    nz = Vector((-s, ca, sa)).normalized()
    ny = nz.cross(tx)
    rot = Matrix((tx, ny, nz)).transposed().to_euler()
    return pos, rot


# --------------------------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------------------------

def build(recipe):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    axis = (recipe["axis"]["y"], recipe["axis"]["z"])
    n = recipe["segments"]
    bevel = recipe["bevel"]
    coll = bpy.data.collections.new("HS_" + recipe["name"])
    bpy.context.scene.collection.children.link(coll)
    profile = [tuple(p) for p in recipe["profile"]]
    surfaces = {}

    sub_bm = bmesh.new()
    for sec in recipe["sections"]:
        pts = section_points(profile, *sec["x"])
        surfaces[sec["name"]] = pts
        if sec["kind"] == "ring":
            bm = bmesh.new()
            shell(bm, refine(pts), 0, 2 * math.pi, n, axis, sec["wall"], full=True)
            finish(bm, "%s_%s" % (recipe["name"], sec["name"]), coll, bevel)
            continue
        # Panels: sector shells with a real gap, over a dark substructure ring.
        pts_f = refine(pts)
        rows = sec["rows"]
        xs = [sec["x"][0] + (sec["x"][1] - sec["x"][0]) * k / rows for k in range(rows + 1)]
        phase = math.radians(sec.get("phase_deg", 0))
        for row in range(rows):
            xa, xb = xs[row] + (sec["gap"] / 2 if row else 0), xs[row + 1] - (sec["gap"] / 2 if row < rows - 1 else 0)
            row_pts = [(xa, radius_at(pts_f, xa))] + [p for p in pts_f if xa < p[0] < xb] + [(xb, radius_at(pts_f, xb))]
            for k in range(sec["around"]):
                span = 2 * math.pi / sec["around"]
                r_mean = sum(p[1] for p in row_pts) / len(row_pts)
                half_gap = sec["gap"] / 2 / r_mean
                a0, a1 = phase + k * span + half_gap, phase + (k + 1) * span - half_gap
                bm = bmesh.new()
                seg = max(2, int(round(n / sec["around"])))
                shell(bm, row_pts, a0, a1, seg, axis, sec["thickness"])
                finish(bm, "%s_%s_P%d_%d" % (recipe["name"], sec["name"], row, k), coll, bevel)
        under = [(x, r - sec["thickness"] - 0.004) for x, r in pts_f]
        rows_s = surface_grid(sub_bm, under, 0, 2 * math.pi, n, axis, 0.0, full=True)
        bridge(sub_bm, rows_s, True)
    finish(sub_bm, recipe["name"] + "_Substructure", coll, bevel)

    for ring in recipe.get("rings", []):
        bm = bmesh.new()
        pts = [(ring["x"][0], ring["r_out"]), (ring["x"][1], ring["r_out"])]
        shell(bm, pts, 0, 2 * math.pi, n, axis, ring["r_out"] - ring["r_in"], full=True)
        finish(bm, "%s_%s" % (recipe["name"], ring["name"]), coll, bevel)

    it = recipe["intake"]
    x0, d = it["x_lip"], it["depth"]
    duct = [(x0 - d, it["hub_r"]), (x0 - d, it["r_duct"]), (x0 - 0.06, it["r_duct"] + 0.005),
            (x0, it["r_lip"] - 0.08), (x0 + 0.02, it["r_lip"] - 0.03), (x0, it["r_lip"])]
    bm = bmesh.new()
    bridge(bm, surface_grid(bm, duct, 0, 2 * math.pi, n, axis, 0.0, full=True), True)
    # Hub: short cylinder with a rounded dome, not a spike.
    hx = x0 - d
    hub = [(hx, it["hub_r"]), (hx + 0.10, it["hub_r"]), (hx + 0.16, it["hub_r"] * 0.92),
           (hx + 0.21, it["hub_r"] * 0.7), (hx + 0.24, it["hub_r"] * 0.4), (hx + 0.25, 0.001)]
    bridge(bm, surface_grid(bm, hub, 0, 2 * math.pi, n, axis, 0.0, full=True), True)
    for k in range(it["spokes"]):
        a = math.pi / 4 + k * 2 * math.pi / it["spokes"]
        rm = (it["hub_r"] + it["r_duct"]) / 2
        L = it["r_duct"] - it["hub_r"]
        res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.06, L, it["spoke_w"]), verts=res["verts"])
        bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "X"))
        bmesh.ops.translate(bm, vec=(x0 - d + 0.03, axis[0] + rm * math.cos(a), axis[1] + rm * math.sin(a)), verts=res["verts"])
    finish(bm, recipe["name"] + "_Intake", coll, bevel)
    bm = bmesh.new()
    rr = it["ring_r"]
    shell(bm, [(x0 - d, rr[1]), (x0 - d + 0.08, rr[1])], 0, 2 * math.pi, n, axis, rr[1] - rr[0], full=True)
    finish(bm, recipe["name"] + "_IntakeRing", coll, bevel)

    ex = recipe["exhaust"]
    x0, d = ex["x_lip"], ex["depth"]
    nozzle = [(x0, ex["r_lip"]), (x0 - 0.02, ex["r_lip"] - 0.03), (x0, ex["r_lip"] - 0.08),
              (x0 + 0.06, ex["r_duct"] + 0.005), (x0 + d, ex["r_duct"]), (x0 + d, ex["cone_r"])]
    cone = [(x0 + d, ex["cone_r"]), (ex["cone_tip"] + 0.08, ex["cone_r"] * 0.35), (ex["cone_tip"], 0.001)]
    bm = bmesh.new()
    bridge(bm, surface_grid(bm, nozzle, 0, 2 * math.pi, n, axis, 0.0, full=True), True)
    bridge(bm, surface_grid(bm, cone, 0, 2 * math.pi, n, axis, 0.0, full=True), True)
    finish(bm, recipe["name"] + "_Exhaust", coll, bevel)

    kit = build_kit(bevel)
    instancer = build_instancer(kit)
    places = []
    for g in recipe.get("greebles", []):
        pos, rot = surface_frame(surfaces[g["surface"]], axis, g["x"], math.radians(g["angle_deg"]))
        places.append((tuple(pos), g["part"], tuple(rot)))
    for br in recipe.get("bolt_rings", []):
        for k in range(br["count"]):
            a = 2 * math.pi * (k + 0.5) / br["count"]
            radial = Vector((0.0, math.cos(a), math.sin(a)))
            z = Vector((-1.0, 0, 0)) if br["facing"] == "aft" else Vector((1.0, 0, 0))
            y = z.cross(radial)
            rot = Matrix((radial, y, z)).transposed().to_euler()
            pos = Vector((br["x"], axis[0], axis[1])) + radial * br["r"]
            places.append((tuple(pos), "bolt", tuple(rot)))
    kit_points(recipe["name"] + "_Greebles", coll, places, instancer)

    out = os.path.join(ROOT, recipe["out_blend"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in coll.objects:
        ev = ob.evaluated_get(dg)
        if ev.type == "MESH":
            tris += sum(len(p.vertices) - 2 for p in ev.data.polygons)
    print("HS_BUILD", out, "objects", len(coll.objects), "tris(excl. instances)", tris, "kit points", len(places))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    with open(os.path.join(ROOT, args[0]) if not os.path.isabs(args[0]) else args[0], encoding="utf-8") as fh:
        build(json.load(fh))
