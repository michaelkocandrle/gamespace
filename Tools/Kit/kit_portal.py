"""KF-PORTAL-01, the corridor frame module (parts factory pilot 1, FACTORY_WORKFLOW v0.2 step 4 blockout, 6. 10. 2026):
the part's own builder from its sheet data (ArtSource/Kit/Design/KF-PORTAL-01.json, rev. C + D) in sections W and N.
  SM_Kit_Portal_Frame03<S>_A  the frame ring - one solid lacquer form (base / step 2 / crown), a polished bead on the
                              crown's edges, the rubber cuff on the soffit; the L1 boots (light lacquer, polished bead
                              on the top edge, the octagonal cup with its glow and a weak light inside); the L2 corner
                              housings; the L3 strip's light; the threshold plate in the floor's lip network
  SM_Kit_Floor_Walk09<S>_A    0.9 m between portals (pitch 1.2): the walkway octagon with the anti-slip lanes, the corner
                              triangles and (W) the side plates, all in the continuous polished lip network; edge strips
Lights are sockets (import_kit.place_part, kit_rooms): Light_Cup_<n> point (role "foot", ~0.5 m), Light_Corner_<n>
spot down (wide), Light_Strip_0 rect under the top member. Blockout: the forms and the materials of the shared base,
no decals, no grime cards, no edge-wear bevels yet (step 5).

    blender -b --factory-startup --python-exit-code 1 --python Tools/Kit/kit_build.py -- factory --no-render
"""
import json
import math
import os

from mathutils import Matrix, Vector

import kit_geo
import kit_batch2

ROOT = kit_geo.ROOT
SPEC = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "Design", "KF-PORTAL-01.json"), encoding="utf-8"))
MM = 0.001

PARTS = [("Portal", "Frame", 0.3, "W", "A"), ("Portal", "Frame", 0.3, "N", "A"),
         ("Floor", "Walk", 0.9, "W", "A"), ("Floor", "Walk", 0.9, "N", "A")]


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


def budget(cat, part, size):
    return 60000


# ------------------------------------------------------------------ the section profile (as draw_part_sheet.py)
def section(key):
    return kit_geo.RULES["sections"][key]


def half_profile(sec):
    h, top, cw = sec["width"] / 2, sec["vertical_to"] + sec["slope_rise"], sec["ceiling_width"] / 2
    return [(h, 0.0), (h, sec["vertical_to"]), (cw, top), (cw, sec["cove_to"]), (0.0, sec["ceiling"])]


def _intersect(p0, p1, q0, q1):
    x1, y1 = p0
    x2, y2 = p1
    x3, y3 = q0
    x4, y4 = q1
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return p1
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def offset_inward(pts, d):
    lines = []
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        dy, dz = y1 - y0, z1 - z0
        n = math.hypot(dy, dz)
        ny, nz = -dz / n, dy / n
        lines.append(((y0 + ny * d, z0 + nz * d), (y1 + ny * d, z1 + nz * d)))
    out = [lines[0][0]]
    for (a0, a1), (b0, b1) in zip(lines, lines[1:]):
        out.append(_intersect(a0, a1, b0, b1))
    out.append(lines[-1][1])
    out[0] = (out[0][0], 0.0)
    return out


def full(pts):
    return [(-y, z) for y, z in pts] + list(reversed(pts))[1:]


def run_matrix(x_front):
    # a prism drawn in (y, z), extruded along -local z, becomes one along -x from x_front
    return Matrix(((0.0, 0.0, 1.0, x_front), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def ring(p, sec, role, u0, u1, v0, v1, bevel=0.0, segments=1, scale=1.0):
    """A band of the ring between the outline offset v0 and v1 (mm, x scale for N), from u0 to u1 (mm) along the run."""
    hp = half_profile(sec)
    poly = full(offset_inward(hp, v0 * MM * scale)) + list(reversed(full(offset_inward(hp, v1 * MM * scale))))
    p.poly_prism(role, poly, run_matrix(u1 * MM), (u1 - u0) * MM, bevel=bevel, segments=segments)


def _octagon(cx, cy, w, h, c):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def _lip_frame(p, x0, x1, y0, y1, ends=(1.0, 1.0)):
    lip = SPEC["floor"]["lip"]
    for (a0, a1, b0, b1) in ((x0, x0 + lip * ends[0], y0, y1), (x1 - lip * ends[1], x1, y0, y1),
                             (x0, x1, y0, y0 + lip), (x0, x1, y1 - lip, y1)):
        if a1 - a0 > 1e-4 and b1 - b0 > 1e-4:
            p.box("Kit_Lip", (a0, b0, -0.02), (a1, b1, 0.0), bevel=0.0015, segments=1, panel=False)


def _field(p, role, x0, x1, y0, y1):
    rec = SPEC["floor"]["insert_recess"]
    p.box(role, (x0, y0, -0.03), (x1, y1, -rec), panel=True)


# ------------------------------------------------------------------ the portal module
def frame_profile(sec_key):
    """The member's closed cross-section in (u, v) mm (rev. E): the half from the sheet mirrored at u 150, closed along
    the wall face. Returns [(u, v, role)], role = the material of the edge to the next point ("edge": a worn tread)."""
    half = SPEC["profile"]["profile_half"]["points"]
    sc = SPEC["profile"]["protrusion_by_section"][sec_key] / SPEC["profile"]["protrusion_by_section"]["W"]
    left = [(u, v * sc, r) for u, v, r in half]
    right = []
    for i in range(len(half) - 1, -1, -1):
        u, v, _ = half[i]
        role = half[i - 1][2] if i > 0 else "wall"
        right.append((300 - u, v * sc, role))
    # the middle of the crown (u 110-190) is the cuff's recess: the soffit there is rubber
    pts = left + right
    out = []
    for i, (u, v, r) in enumerate(pts):
        out.append((u, v, r))
    return out


def loft(p, sec, profile, x_scale=MM):
    """The frame ring swept along the section (rev. E): every profile point (u, v) becomes the section's outline offset
    v into the corridor at x = u; consecutive points make quad strips, the two floor ends are capped. Built as one
    closed mesh (normals recalculated), then split by the profile edges' roles; "edge" strips are the worn treads."""
    import bmesh
    hp = half_profile(sec)
    rows = [full(offset_inward(hp, v * MM)) for u, v, r in profile]
    tmp = bmesh.new()
    V = [[tmp.verts.new((u * x_scale, y, z)) for (y, z) in row] for (u, v, r), row in zip(profile, rows)]
    K = len(rows[0])
    n = len(profile)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        role = profile[i][2]
        for k in range(K - 1):
            f = tmp.faces.new((V[i][k], V[i][k + 1], V[j][k + 1], V[j][k]))
            faces.append((f, role))
    for k in (0, K - 1):
        f = tmp.faces.new([V[i][k] for i in range(n)])
        faces.append((f, "cap"))
    bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces)
    by_role = {}
    for f, role in faces:
        by_role.setdefault(role, []).append([v.co.copy() for v in f.verts])
    tmp.free()
    for role, polys in by_role.items():
        mat = {"edge": "Kit_Lacquer", "cap": "Kit_Lacquer", "wall": "Kit_Lacquer", "cuff": "Kit_Lacquer"}.get(role, role)
        bm = bmesh.new()
        local = []
        for poly in polys:
            vs = [bm.verts.new(c) for c in poly]
            bm.faces.new(vs)
        local = [v.co.copy() for v in bm.verts]
        edge = set(bm.faces) if role == "edge" else ()
        out = p._merge(p.bm[mat], bm, local, edge)
        lo = (min(c.x for c in local), min(c.y for c in local), min(c.z for c in local))
        hi = (max(c.x for c in local), max(c.y for c in local), max(c.z for c in local))
        p.meta[mat].append((out, ("member", Vector(lo), Vector(hi)), p._panel_id(True), False))


def threshold(p, sec_key):
    """Step 5: the threshold under the portal as the band - its field in the lip network, 5 grooves across, the cover
    plate with 4 bolts (a functional cover), the maker's badge in relief on it, the edge strips with the gutter's
    grooves, smears in the corners by the walls."""
    sec = section(sec_key)
    half = sec["width"] / 2
    edge = half - SPEC["floor"]["edge_strip"]
    dt = SPEC["details"]
    p.box("Kit_Seal", (0.0, -half - 0.1, -0.06), (0.3, half + 0.1, -0.05), panel=False)
    _field(p, "Kit_Graphite", 0.0, 0.3, -edge, edge)
    _lip_frame(p, 0.0, 0.3, -edge, edge, ends=(0.5, 0.5))
    cl, cw = dt["threshold"]["cover"]
    gw = dt["threshold"]["groove_w"]
    rec = SPEC["floor"]["insert_recess"]
    n = dt["threshold"]["grooves"]
    for s in (-1, 1):
        # grooves across, either side of the cover plate
        for k in range(n):
            x = 0.05 + k * 0.2 / (n - 1)
            ya, yb = sorted((s * (cl / 2 + 0.03), s * (edge - 0.05)))
            p.box("Kit_Seal", (x - gw / 2, ya, -rec - 0.0005), (x + gw / 2, yb, -rec + 0.0003), panel=False)
        # the edge strip with the gutter's grooves along the run
        y0, y1 = sorted((s * edge, s * (half + 0.1)))
        p.box("Kit_Graphite", (0.0, y0, -0.02), (0.3, y1, 0.004), panel=False)
        for g in range(dt["gutter"]["grooves"]):
            yy = s * (edge + 0.012 + g * 0.014)
            ya, yb = sorted((yy - 0.002, yy + 0.002))
            p.box("Kit_Seal", (0.0, ya, 0.0035), (0.3, yb, 0.0045), panel=False)
        p.grime("smear", (0.15, s * (edge - 0.06), -rec), (0, 0, 1), (0, s, 0), (0.24, 0.1), 0.35)
    # the cover plate (graphite, 2 mm proud of the field) with 4 polished bolts and the badge in relief
    p.box("Kit_Graphite", (0.15 - cw / 2, -cl / 2, -rec), (0.15 + cw / 2, cl / 2, -rec + 0.003), bevel=0.0015, segments=1)
    for bx in (0.15 - cw / 2 + 0.018, 0.15 + cw / 2 - 0.018):
        for by in (-cl / 2 + 0.02, cl / 2 - 0.02):
            p.tube("Kit_Lip", (bx, by, -rec + 0.003), (bx, by, -rec + 0.0045), 0.006, 10)
    bw, bl = dt["threshold"]["badge"]
    # the maker's badge in relief: graphite raised 1.5 mm, its two bars polished (round 1: a lacquer badge read as a
    # white sticker)
    p.box("Kit_Graphite", (0.15 - bl / 2, -bw / 2, -rec + 0.003), (0.15 + bl / 2, bw / 2, -rec + 0.0045), bevel=0.001, segments=1)
    for dy in (-0.008, 0.008):
        p.box("Kit_Lip", (0.15 - bl / 2 + 0.008, dy - 0.0015, -rec + 0.0045), (0.15 + bl / 2 - 0.008, dy + 0.0015, -rec + 0.0052),
              bevel=0.0005, segments=1, panel=False)


def pillar_labels(p, sec_key):
    """Step 5: a 3 cm frame number on the base facet of each pillar, both faces of the module (etalon: small labels on
    the pillar's side)."""
    sec = section(sec_key)
    half = sec["width"] / 2
    sc = SPEC["profile"]["protrusion_by_section"][sec_key] / SPEC["profile"]["protrusion_by_section"]["W"]
    lab = SPEC["details"]["pillar_label"]
    z = lab["at_z"]
    for s in (-1, 1):
        for face in (-1, 1):
            # the base facet's middle: u 20.5 (or 279.5), v 27.5; its normal out of the run and into the corridor
            u = 0.0205 if face < 0 else 0.2795
            v = 0.0275 * sc
            at = (u, s * (half - v), z)
            nrm = Vector((face, -s, 0.0)).normalized()
            xdir = Vector((0, 0, 1))
            ydir = nrm.cross(xdir)
            kit_batch2.label(p, lab["item"], at, nrm, xdir, ydir, scale=lab["scale"], is_label=True)


def boot(p, sec_key, s):
    """Rev. E: the L1 boot round one pillar's foot (s = -1 / +1 side) - light lacquer, flat on top (no roof), octagonal
    in plan (the corridor-side vertical edges chamfered), a polished bead on its top edge; the cup sunk into its
    corridor face (an octagonal well whose inner walls the weak light lights, a 14 mm emitter at the bottom)."""
    sec = section(sec_key)
    bt = SPEC["boot"]
    half = sec["width"] / 2
    v1 = bt["v1_by_section"][sec_key]
    h = bt["height_by_section"][sec_key] * MM
    cp = bt["cup"]
    dep = cp["depth_by_section"][sec_key]
    c = min(bt["chamfer"], dep - 5)                          # the plan chamfer inside the cup's depth (N: 40)
    zc = cp["z_by_section"][sec_key] * MM
    Y = lambda v: s * (half - v * MM)                         # noqa: E731
    top = Matrix.Translation((0, 0, h))
    # the core behind the cup and the two chamfered side pieces in front of it
    p.poly_prism("Kit_Lacquer", [(0.0, Y(0)), (0.3, Y(0)), (0.3, Y(v1 - dep)), (0.0, Y(v1 - dep))], top, h)
    for u0, u1, sg in ((0, c, 1), (300 - c, 300, -1)):
        if sg > 0:
            tri = [(0.0, Y(v1 - dep)), (c * MM, Y(v1 - dep)), (c * MM, Y(v1)), (0.0, Y(v1 - c))]
        else:
            tri = [((300 - c) * MM, Y(v1 - dep)), (0.3, Y(v1 - dep)), (0.3, Y(v1 - c)), ((300 - c) * MM, Y(v1))]
        p.poly_prism("Kit_Lacquer", tri, top, h)
    # the front frame round the cup: 8 quads between the octagonal well and the face's rectangle (u c..300-c, z 0..h),
    # drawn in (u, z - zc), extruded dep mm into the boot (local z -> +s y: from the face towards the wall)
    r = cp["size"] / 2 * MM
    oc = [(0.15 + r * math.cos(math.radians(45 * k)), r * math.sin(math.radians(45 * k))) for k in range(8)]
    ux0, ux1, zz0, zz1 = c * MM, (300 - c) * MM, -zc, h - zc

    def to_rect(a):
        dx, dz = math.cos(math.radians(a)), math.sin(math.radians(a))
        t = min([(ux1 - 0.15) / dx if dx > 1e-9 else 1e9, (ux0 - 0.15) / dx if dx < -1e-9 else 1e9,
                 zz1 / dz if dz > 1e-9 else 1e9, zz0 / dz if dz < -1e-9 else 1e9])
        return (0.15 + dx * t, dz * t)

    # the rectangle's corners between the rays go into their sector's piece, or the piece would cut the corner off
    corners = [(ux1, zz1), (ux0, zz1), (ux0, zz0), (ux1, zz0)]
    ang = lambda pt: math.degrees(math.atan2(pt[1], pt[0] - 0.15)) % 360.0     # noqa: E731
    pieces = []
    for k in range(8):
        a0, a1 = 45.0 * k, 45.0 * (k + 1)
        mid = sorted([cn for cn in corners if a0 < ang(cn) < a1], key=ang, reverse=True)
        pieces.append([oc[k], oc[(k + 1) % 8], to_rect(a1 % 360.0)] + mid + [to_rect(a0)])
    # drawn in (u, z - zc); local z -> -s y (front at the face, the depth towards the wall), local y -> s z: the matrix
    # keeps a positive determinant on both sides, so the local polygon's z is mirrored for s = -1
    m = Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -s * 1.0, Y(v1)), (0.0, s * 1.0, 0.0, zc), (0.0, 0.0, 0.0, 1.0)))
    for poly in pieces:
        p.poly_prism("Kit_Lacquer", [(x, s * z) for x, z in poly], m, dep * MM)
    # the cup's bottom (lacquer, lit) and the small emitter in its middle; the light a little in front of it
    yb = Y(v1 - dep)
    ya, yb2 = sorted((yb, yb - s * 0.001))
    # the bottom dark (round 1: a lacquer bottom 15 mm from the light read as a flat white octagon); the light falls
    # on the well's lacquer walls, the source shows as the small emitter only
    p.box("Kit_Gasket", (0.15 - r, ya, zc - r), (0.15 + r, yb2, zc + r), panel=False)
    e = cp["emitter"] * MM / 2
    p.tube("Kit_GlowFoot", (0.15, yb, zc), (0.15, yb - s * 0.003, zc), e, 12)
    p.socket("Light_Cup_%d" % (0 if s < 0 else 1), (0.15, yb - s * dep * MM * 0.15, zc), x=(0, -s, 0), z=(0, 0, 1), type="point",
             role="foot", cd=cp["light_cd"], radius_m=cp["light_radius_m"], source_radius_cm=0.6)
    # the polished bead on the top edge: the corridor face and the two plan chamfers, 1 mm proud
    bd = bt["bead"]
    edge = [(0, v1 - c), (c, v1), (300 - c, v1), (300, v1 - c)]
    for (ua, va), (ub, vb) in zip(edge, edge[1:]):
        dx, dy = ub - ua, vb - va
        nn = math.hypot(dx, dy)
        ix, iy = dy / nn * bd, -dx / nn * bd                   # inward in plan (towards the wall)
        ox, oy = -dy / nn * 1.0, dx / nn * 1.0                 # 1 mm out
        quad = [((ua + ox) * MM, Y(va + oy)), ((ub + ox) * MM, Y(vb + oy)), ((ub + ix) * MM, Y(vb + iy)),
                ((ua + ix) * MM, Y(va + iy))]
        p.poly_prism("Kit_Lip", quad, Matrix.Translation((0, 0, h + 0.001)), bd * MM + 0.001, bevel=0.003, segments=2)
    # dirt where it forms: a rim card round the boot's foot on the floor
    p.grime("rim", (0.15, Y(v1 + 30), 0.0), (0, 0, 1), (0, s, 0), (0.32, 0.07), 0.55)


def portal_frame(name, sec_key, seed):
    """Rev. E + step 5: the frame swept from the sheet's profile (one lacquer form, the steps' 45 deg facets, the
    polished crown facet), the rubber cuff on the soffit, the boots, the L2 / L3 lights, the threshold and labels."""
    p = kit_geo.Part(name, seed)
    sec = section(sec_key)
    pr = SPEC["profile"]
    sc = pr["protrusion_by_section"][sec_key] / pr["protrusion_by_section"]["W"]
    loft(p, sec, frame_profile(sec_key))
    cf = pr["cuff"]
    top = 100 * sc
    ring(p, sec, "Kit_Gasket", cf["u0"], cf["u1"], top / sc - cf["depth"] / sc, top / sc + 0.2, scale=sc)
    u = cf["u0"] + 3
    while u + cf["rib_width"] <= cf["u1"]:
        ring(p, sec, "Kit_Gasket", u, u + cf["rib_width"], top / sc, top / sc + cf["rib_height"] / sc, scale=sc)
        u += cf["rib_pitch"]
    half = sec["width"] / 2
    prot = pr["protrusion_by_section"][sec_key] * MM
    lt = SPEC["light_levels"]
    for s in (-1, 1):
        boot(p, sec_key, s)
        cy, cz = s * (sec["ceiling_width"] / 2 - prot - 0.03), sec["vertical_to"] + sec["slope_rise"] - 0.03
        p.tube("Kit_Graphite", (0.15, cy, cz + 0.04), (0.15, cy, cz), 0.03, 16)
        p.tube("Kit_GlowWarm", (0.15, cy, cz + 0.002), (0.15, cy, cz - 0.001), 0.022, 16)
        p.socket("Light_Corner_%d" % (0 if s < 0 else 1), (0.15, cy, cz - 0.01), x=(0, 0, -1), z=(1, 0, 0), type="spot",
                 role="neutral", cd=lt["L2_cd"], cone_deg=lt["L2_cone_deg"], radius_m=3.5, source_radius_cm=2.0)
    kit_batch2.strip_light_along(p, "Light_Strip_0", (0.15, 0.0, sec["ceiling"] - 0.1), (0, 0, -1), (0, 1, 0),
                                 sec["ceiling_width"] - 0.2, 0.02, "neutral", lt["L3_cd"], 2.5)
    threshold(p, sec_key)
    pillar_labels(p, sec_key)
    p.collision_box((0.0, -half, 0.0), (0.3, half, sec["ceiling"]))
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (0.3, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


# ------------------------------------------------------------------ the floor module
def floor_walk(name, sec_key, seed):
    p = kit_geo.Part(name, seed)
    sec = section(sec_key)
    fl = SPEC["floor"]
    L, c, lip, rec = 0.9, fl["corner_chamfer"], fl["lip"], fl["insert_recess"]
    half = sec["width"] / 2
    edge = half - fl["edge_strip"]
    W = min(fl["walk_width"], 2 * edge)                       # N: the walkway is the whole floor
    ident = Matrix.Identity(4)
    p.box("Kit_Seal", (0.0, -half - 0.1, -0.06), (L, half + 0.1, -0.05), panel=False)
    outer = _octagon(L / 2, 0, L, W, c)
    inner = _octagon(L / 2, 0, L - 2 * lip, W - 2 * lip, c - lip * 0.41)
    for i in range(8):
        j = (i + 1) % 8
        p.poly_prism("Kit_Lip", [outer[i], outer[j], inner[j], inner[i]], ident, 0.02, bevel=0.0015, segments=1)
    p.poly_prism("Kit_Graphite", inner, Matrix.Translation((0, 0, -rec)), 0.02, panel=True)
    ln = fl["lanes"]
    y = -W / 2 + lip + 0.04
    while y + ln["width"] <= W / 2 - lip - 0.04:
        p.box("Kit_AntiSlip", (c * 0.6, y, -rec), (L - c * 0.6, y + ln["width"], -rec + 0.0015), panel=False)
        y += ln["pitch"]
    for s in (-1, 1):
        for (xa, xb) in ((0.0, c), (L, L - c)):
            tri = [(xa, s * W / 2), (xb, s * W / 2), (xa, s * (W / 2 - c))]
            p.poly_prism("Kit_Graphite", tri, Matrix.Translation((0, 0, -rec)), 0.02)
            x0, x1 = sorted((xa, xa + (lip * 0.5 if xa == 0.0 else -lip * 0.5)))
            ya, yb = sorted((s * W / 2, s * (W / 2 - c)))
            p.box("Kit_Lip", (x0, ya, -0.02), (x1, yb, 0.0), bevel=0.0015, segments=1, panel=False)
        if edge - W / 2 > 0.05:
            y0, y1 = sorted((s * (W / 2), s * edge))
            _field(p, "Kit_Graphite", 0.0, L, y0, y1)
            _lip_frame(p, 0.0, L, y0, y1, ends=(0.5, 0.5))
        y0, y1 = sorted((s * edge, s * (half + 0.1)))
        p.box("Kit_Graphite", (0.0, y0, -0.02), (L, y1, 0.004), panel=False)
        # step 5: the gutter's grooves along the run on the edge strip, dirt along the plinth
        for g in range(SPEC["details"]["gutter"]["grooves"]):
            yy = s * (edge + 0.012 + g * 0.014)
            ya, yb = sorted((yy - 0.002, yy + 0.002))
            p.box("Kit_Seal", (0.0, ya, 0.0035), (L, yb, 0.0045), panel=False)
        p.grime("rim", (L / 2, s * (edge + 0.03), 0.004), (0, 0, 1), (0, s, 0), (L - 0.05, 0.06), 0.45)
    p.collision_box((0.0, -half, -0.05), (L, half, 0.0))
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


def build_part(cat, part, size, sec_key, var, seed):
    name = part_name(cat, part, size, sec_key, var)
    return portal_frame(name, sec_key, seed) if cat == "Portal" else floor_walk(name, sec_key, seed)
