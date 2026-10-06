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

from mathutils import Matrix

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
def boot(p, sec_key, s):
    """Rev. D: the L1 boot round one pillar's foot (s = -1 / +1 side) - light lacquer, a polished bead on its top
    edge, the octagonal cup in its corridor face with the glowing back and a weak light inside."""
    sec = section(sec_key)
    bt = SPEC["boot"]
    half = sec["width"] / 2
    v1 = bt["v1_by_section"][sec_key]
    prot = SPEC["profile"]["protrusion_by_section"][sec_key]
    zv = bt["z_vert"]
    zt = zv + (v1 - prot)                                     # the 45 deg chamfer up into the pillar's crown
    c = bt["chamfer"]
    Y = lambda v: s * (half - v * MM)                         # noqa: E731
    plan = [(u * MM, Y(v)) for u, v in [(bt["u0"], 0), (bt["u1"], 0), (bt["u1"], v1 - c), (bt["u1"] - c, v1),
                                        (bt["u0"] + c, v1), (bt["u0"], v1 - c)]]
    p.poly_prism("Kit_Lacquer", plan, Matrix.Translation((0, 0, zv * MM)), zv * MM)
    wedge = [(Y(v), z * MM) for v, z in [(0, zv), (v1, zv), (prot, zt), (0, zt)]]
    p.poly_prism("Kit_Lacquer", wedge, run_matrix((bt["u1"] - c * 0.5) * MM), (bt["u1"] - bt["u0"] - c) * MM)
    # the polished bead on the top edge: along the corridor face and the two plan chamfers, 12 mm wide, 14 mm high
    e = bt["bead"]
    edge = [(bt["u0"], v1 - c), (bt["u0"] + c, v1), (bt["u1"] - c, v1), (bt["u1"], v1 - c)]
    for (ua, va), (ub, vb) in zip(edge, edge[1:]):
        dx, dy = ub - ua, vb - va
        n = math.hypot(dx, dy)
        ix, iy = dy / n * e, -dx / n * e                       # inward in plan (u, v): toward the wall
        quad = [(ua * MM, Y(va)), (ub * MM, Y(vb)), ((ub + ix) * MM, Y(vb + iy)), ((ua + ix) * MM, Y(va + iy))]
        p.poly_prism("Kit_Lip", quad, Matrix.Translation((0, 0, (zv + 2) * MM)), (e + 2) * MM, bevel=0.003, segments=2)
    # the cup: an octagonal collar out of the corridor face, its glowing back, the light inside. The collar is drawn
    # in (u, z - zc) and extruded along the face's outward normal (-s in y); local y maps to s * z so the matrix
    # keeps a positive determinant on both sides (a mirrored prism would turn its faces inside out)
    cp = bt["cup"]
    uc, zc = cp["u"] * MM, cp["z"] * MM
    yf = Y(v1)
    d = cp["depth"] * MM
    m = Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -s * 1.0, yf - s * d), (0.0, s * 1.0, 0.0, zc), (0.0, 0.0, 0.0, 1.0)))
    col_o = _octagon(uc, 0.0, cp["outer"] * MM, cp["outer"] * MM, cp["outer"] * MM * 0.29)
    col_i = _octagon(uc, 0.0, cp["inner"] * MM, cp["inner"] * MM, cp["inner"] * MM * 0.29)
    for i in range(8):
        j = (i + 1) % 8
        p.poly_prism("Kit_Lacquer", [col_o[i], col_o[j], col_i[j], col_i[i]], m, d)
    yb = yf - s * 0.001
    ya, yb2 = sorted((yf, yb))
    p.box("Kit_GlowFoot", (uc - cp["inner"] * MM / 2, ya, zc - cp["inner"] * MM / 2), (uc + cp["inner"] * MM / 2, yb2, zc + cp["inner"] * MM / 2),
          panel=False)
    ly = yf - s * cp["depth"] * MM * 0.4
    p.socket("Light_Cup_%d" % (0 if s < 0 else 1), (uc, ly, zc), x=(0, -s, 0), z=(0, 0, 1), type="point", role="foot",
             cd=cp["light_cd"], radius_m=cp["light_radius_m"], source_radius_cm=0.8)


def portal_frame(name, sec_key, seed):
    p = kit_geo.Part(name, seed)
    sec = section(sec_key)
    pr = SPEC["profile"]
    base, mid, crown = pr["steps"]
    # N: the steps shallower (protrusion 80 instead of 100), the same rhythm scaled
    sc = pr["protrusion_by_section"][sec_key] / pr["protrusion_by_section"]["W"]
    e, cf = pr["lip"]["edge"], pr["cuff"]
    ring(p, sec, "Kit_Lacquer", base["u0"], base["u1"], base["v0"], base["v1"], scale=sc)
    ring(p, sec, "Kit_Lacquer", mid["u0"], mid["u1"], mid["v0"], mid["v1"], scale=sc)
    ring(p, sec, "Kit_Lacquer", crown["u0"], crown["u1"], crown["v0"], crown["v1"] - e / sc, scale=sc)
    for a, b in ((crown["u0"], crown["u0"] + e), (crown["u1"] - e, crown["u1"])):
        ring(p, sec, "Kit_Lip", a, b, crown["v1"] - e / sc, crown["v1"], bevel=e * MM * 0.45, segments=3, scale=sc)
    for a, b in ((crown["u0"] + e, cf["u0"]), (cf["u1"], crown["u1"] - e)):
        ring(p, sec, "Kit_Lacquer", a, b, crown["v1"] - e / sc, crown["v1"], scale=sc)
    ring(p, sec, "Kit_Gasket", cf["u0"], cf["u1"], crown["v1"] - e / sc, crown["v1"] - cf["depth"] / sc, scale=sc)
    u = cf["u0"] + 3
    while u + cf["rib_width"] <= cf["u1"]:
        ring(p, sec, "Kit_Gasket", u, u + cf["rib_width"], crown["v1"] - cf["depth"] / sc, crown["v1"] - (cf["depth"] - cf["rib_height"]) / sc,
             scale=sc)
        u += cf["rib_pitch"]
    half = sec["width"] / 2
    edge = half - SPEC["floor"]["edge_strip"]
    prot = pr["protrusion_by_section"][sec_key] * MM
    for s in (-1, 1):
        boot(p, sec_key, s)
        cy, cz = s * (sec["ceiling_width"] / 2 - prot - 0.03), sec["vertical_to"] + sec["slope_rise"] - 0.03
        p.tube("Kit_Graphite", (0.15, cy, cz + 0.04), (0.15, cy, cz), 0.03, 16)
        p.tube("Kit_GlowWarm", (0.15, cy, cz + 0.002), (0.15, cy, cz - 0.001), 0.022, 16)
        lt = SPEC["light_levels"]
        p.socket("Light_Corner_%d" % (0 if s < 0 else 1), (0.15, cy, cz - 0.01), x=(0, 0, -1), z=(1, 0, 0), type="spot",
                 role="neutral", cd=lt["L2_cd"], cone_deg=lt["L2_cone_deg"], radius_m=3.5, source_radius_cm=2.0)
    lt = SPEC["light_levels"]
    kit_batch2.strip_light_along(p, "Light_Strip_0", (0.15, 0.0, sec["ceiling"] - 0.1), (0, 0, -1), (0, 1, 0),
                                 sec["ceiling_width"] - 0.2, 0.02, "neutral", lt["L3_cd"], 2.5)
    # the threshold in the lip network (half the lip at the module's ends)
    p.box("Kit_Seal", (0.0, -half - 0.1, -0.06), (0.3, half + 0.1, -0.05), panel=False)
    _field(p, "Kit_Graphite", 0.0, 0.3, -edge, edge)
    _lip_frame(p, 0.0, 0.3, -edge, edge, ends=(0.5, 0.5))
    for s in (-1, 1):
        y0, y1 = sorted((s * edge, s * (half + 0.1)))
        p.box("Kit_Graphite", (0.0, y0, -0.02), (0.3, y1, 0.004), panel=False)
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
    p.collision_box((0.0, -half, -0.05), (L, half, 0.0))
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


def build_part(cat, part, size, sec_key, var, seed):
    name = part_name(cat, part, size, sec_key, var)
    return portal_frame(name, sec_key, seed) if cat == "Portal" else floor_walk(name, sec_key, seed)
