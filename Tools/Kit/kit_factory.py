"""Parts factory, pilot 1 step 3 (FACTORY_WORKFLOW v0.2, 6. 10. 2026): the corridor test section for judging the kit's
shared material base (ArtSource/Kit/kit_materials.json) in context, from the same angles as the SC etalon's anchor
shots (lesson P26: not on isolated samples shot square on). Rough geometry from the KF-PORTAL-01 sheet rev. B
(ArtSource/Kit/Design/KF-PORTAL-01.json) in section W - not the part's blockout (step 4):
  SM_Kit_Test_Portal03W_A  the ring: base / step 2 / crown (cream lacquer, 4 mm worn bevels), polished lips over the
                           crown's edges, the ribbed rubber cuff, the L1 foot housings with their diffusers, the L2
                           corner housings (the L3 strip is hidden in its groove: only its light, Tools/Assets/import_kit.py)
  SM_Kit_Test_Bay09W_A     0.9 m between portals: the walkway plate (polished lip, field 6 mm down, anti-slip lanes),
                           satin graphite side plates and edge strips, graphite wall panels on the W profile, a rubber
                           kick strip (no plinth light, sheet rev. B), the ceiling panel

    blender -b --factory-startup --python-exit-code 1 --python Tools/Kit/kit_build.py -- factory --no-render

Frames (kit_rules pivots, "run"): origin at the module start on the corridor's centre line at floor level, +X along
the run, +Y across, +Z up - so the master's walked line (|LocalPos.y| < 25 cm) and hand band (LocalPos.z) hold.
"""
import json
import math
import os

from mathutils import Matrix

import kit_geo

ROOT = kit_geo.ROOT
SPEC = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "Design", "KF-PORTAL-01.json"), encoding="utf-8"))
MATS = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_materials.json"), encoding="utf-8"))
SEC = kit_geo.RULES["sections"]["W"]
BEV = {r: v["bevel_mm"] / 1000.0 for r, v in MATS["roles"].items() if not r.startswith("_")}
MM = 0.001

FACTORY = [("Test", "Portal", 0.3, "W", "A"), ("Test", "Bay", 0.9, "W", "A")]
VIEWS = {("Test", p): ((1, 0.0, 0.0), (1, -0.6, 0.2)) for _, p, _, _, _ in FACTORY}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


def budget(cat, part, size):
    return 40000


# ------------------------------------------------------------------ the W profile (as draw_part_sheet.py)
def half_profile():
    h, top, cw = SEC["width"] / 2, SEC["vertical_to"] + SEC["slope_rise"], SEC["ceiling_width"] / 2
    return [(h, 0.0), (h, SEC["vertical_to"]), (cw, top), (cw, SEC["cove_to"]), (0.0, SEC["ceiling"])]


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


def path(d):
    """The section's outline offset d into the corridor, left floor -> over the top -> right floor, (y, z)."""
    return full(offset_inward(half_profile(), d))


def run_matrix(x_front):
    # a prism drawn in (y, z) and extruded along -local z becomes one along -x from x_front
    return Matrix(((0.0, 0.0, 1.0, x_front), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def ring(p, role, u0, u1, v0, v1, bevel=0.0, segments=1):
    """One ring band of the portal: between the outline offset v0 and v1 (mm), from u0 to u1 (mm) along the run."""
    poly = path(v0 * MM) + list(reversed(path(v1 * MM)))
    p.poly_prism(role, poly, run_matrix(u1 * MM), (u1 - u0) * MM, bevel=bevel, segments=segments)


def test_portal(name, seed):
    p = kit_geo.Part(name, seed)
    pr = SPEC["profile"]
    bv = BEV["Kit_Lacquer"]
    base, mid, crown = pr["steps"]
    ring(p, "Kit_Lacquer", base["u0"], base["u1"], base["v0"], base["v1"], bevel=bv)
    ring(p, "Kit_Lacquer", mid["u0"], mid["u1"], mid["v0"], mid["v1"], bevel=bv)
    lip, cf = pr["lip"]["width"], pr["cuff"]
    for a, b in ((crown["u0"], crown["u0"] + lip), (crown["u1"] - lip, crown["u1"])):
        ring(p, "Kit_Lip", a, b, crown["v0"], crown["v1"], bevel=crown.get("chamfer", 12) * MM * 0.5, segments=3)
    for a, b in ((crown["u0"] + lip, cf["u0"]), (cf["u1"], crown["u1"] - lip)):
        ring(p, "Kit_Lacquer", a, b, crown["v0"], crown["v1"], bevel=bv)
    ring(p, "Kit_Gasket", cf["u0"], cf["u1"], crown["v0"], crown["v1"] - cf["depth"])
    u = cf["u0"] + 4
    while u + cf["rib_width"] <= cf["u1"]:
        ring(p, "Kit_Gasket", u, u + cf["rib_width"], crown["v1"] - cf["depth"], crown["v1"] - 1, bevel=0.001)
        u += cf["rib_pitch"]
    # L1: the foot housings (graphite, octagon-ish by a big bevel) with the diffuser on their inner face
    half, prot = SEC["width"] / 2, pr["protrusion_by_section"]["W"] * MM
    for s in (-1, 1):
        # 60 mm deep, its face 30 mm proud of the crown
        y0, y1 = sorted((s * (half - prot + 0.03), s * (half - prot - 0.03)))
        p.box("Kit_Graphite", (0.075, y0, 0.02), (0.225, y1, 0.17), bevel=0.035, segments=1)
        yd = s * (half - prot - 0.03)
        ya, yb = sorted((yd, yd - s * 0.004))
        p.box("Kit_GlowFoot", (0.105, ya, 0.07), (0.195, yb, 0.12), panel=False)
        # L2: the corner housing, a short tube under the slope's top with its warm lens
        cy, cz = s * (SEC["ceiling_width"] / 2 - prot - 0.03), SEC["vertical_to"] + SEC["slope_rise"] - 0.03
        p.tube("Kit_Graphite", (0.15, cy, cz + 0.04), (0.15, cy, cz), 0.03, 16)
        p.tube("Kit_GlowWarm", (0.15, cy, cz + 0.002), (0.15, cy, cz - 0.001), 0.022, 16)
    p.collision_box((0.0, -half, 0.0), (0.3, half, SEC["ceiling"]))
    return p


def _octagon(cx, cy, w, h, c):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def test_bay(name, seed):
    p = kit_geo.Part(name, seed)
    fl = SPEC["floor"]
    L, W, c, lip, rec = 0.9, fl["walk_width"], fl["corner_chamfer"], fl["lip"], fl["insert_recess"]
    half = SEC["width"] / 2
    edge = half - fl["edge_strip"]
    ident = Matrix.Identity(4)
    p.box("Kit_Seal", (0.0, -half - 0.1, -0.06), (L, half + 0.1, -0.05), panel=False)      # dark under everything
    # the walkway plate: lip ring, the field 6 mm down with the anti-slip lanes
    outer = _octagon(L / 2, 0, L - 0.01, W - 0.01, c)
    inner = _octagon(L / 2, 0, L - 0.01 - 2 * lip, W - 0.01 - 2 * lip, c - lip * 0.41)
    for i in range(8):
        j = (i + 1) % 8
        p.poly_prism("Kit_Lip", [outer[i], outer[j], inner[j], inner[i]], ident, 0.02, bevel=0.0015, segments=1)
    p.poly_prism("Kit_Graphite", inner, Matrix.Translation((0, 0, -rec)), 0.02, panel=True)
    ln = fl["lanes"]
    y = -W / 2 + lip + 0.04
    while y + ln["width"] <= W / 2 - lip - 0.04:
        p.box("Kit_AntiSlip", (c * 0.6, y, -rec), (L - c * 0.6, y + ln["width"], -rec + 0.0015), panel=False)
        y += ln["pitch"]
    # the side plates and the edge strips (W), satin graphite
    for s in (-1, 1):
        y0, y1 = sorted((s * (W / 2), s * edge))
        p.box("Kit_Graphite", (0.004, y0 + 0.004, -0.02), (L - 0.004, y1 - 0.004, 0.0), bevel=0.003, segments=1)
        y0, y1 = sorted((s * edge, s * (half + 0.1)))
        p.box("Kit_Graphite", (0.0, y0, -0.02), (L, y1, 0.004), bevel=0.002, segments=1, panel=False)
    # the walls on the W profile: the rubber kick strip (0-0.1), the vertical panel, the slope, the cove; graphite
    pts = half_profile()
    segs = [((half, 0.1), (half, SEC["vertical_to"])), (pts[1], pts[2]), (pts[2], pts[3])]
    for s in (-1, 1):
        for (a, b) in segs:
            # the panel 20 mm thick behind the face line (worked on the right side, mirrored), 3 mm short at each
            # end: the seams between wall, slope and cove
            dy, dz = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dy, dz)
            ty, tz = dy / n * 0.003, dz / n * 0.003
            oy, oz = dz / n * 0.02, -dy / n * 0.02          # outward, away from the corridor
            a2, b2 = (a[0] + ty, a[1] + tz), (b[0] - ty, b[1] - tz)
            quad = [a2, b2, (b2[0] + oy, b2[1] + oz), (a2[0] + oy, a2[1] + oz)]
            p.poly_prism("Kit_Graphite", [(s * y, z) for y, z in quad], run_matrix(L - 0.004), L - 0.008, bevel=0.003,
                         segments=1)
        y0, y1 = sorted((s * half, s * (half + 0.02)))
        p.box("Kit_Gasket", (0.0, y0, 0.0), (L, y1, 0.1), bevel=0.002, segments=1)
        for z in (0.025, 0.05, 0.075):
            yy0, yy1 = sorted((s * (half - 0.003), s * half))
            p.box("Kit_Gasket", (0.0, yy0, z - 0.003), (L, yy1, z + 0.003), panel=False)
    p.box("Kit_Graphite", (0.004, -SEC["ceiling_width"] / 2, SEC["ceiling"]), (L - 0.004, SEC["ceiling_width"] / 2, SEC["ceiling"] + 0.02),
          bevel=0.003, segments=1)
    p.box("Kit_Seal", (0.0, -half - 0.1, SEC["ceiling"] + 0.02), (L, half + 0.1, SEC["ceiling"] + 0.03), panel=False)
    for s in (-1, 1):          # behind the walls: no light leaks through the seams
        y0, y1 = sorted((s * (half + 0.03), s * (half + 0.04)))
        p.box("Kit_Seal", (0.0, y0, 0.0), (L, y1, SEC["ceiling"] + 0.03), panel=False)
    p.collision_box((0.0, -half, -0.05), (L, half, 0.0))
    return p


BUILDERS = {"Portal": test_portal, "Bay": test_bay}


def build_part(cat, part, size, sec_key, var, seed):
    return BUILDERS[part](part_name(cat, part, size, sec_key, var), seed)
