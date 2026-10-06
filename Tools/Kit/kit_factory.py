"""Parts factory, pilot 1 (FACTORY_WORKFLOW v0.2): the corridor test section for judging KF-PORTAL-01 in context, from
the same angles as the SC etalon's anchor shots (lesson P26). Since step 4 (6. 10. 2026) the portal and the floor are
the part's own blockout (Tools/Kit/kit_portal.py); this module keeps only the shell around it:
  SM_Kit_Test_Shell09W_A   0.9 m between portals: graphite wall panels on the W profile, the rubber kick strip (no
                           plinth light, sheet rev. B), the ceiling panel, dark backing - no floor

    blender -b --factory-startup --python-exit-code 1 --python Tools/Kit/kit_build.py -- factory --no-render

Frames (kit_rules pivots, "run"): origin at the module start on the corridor's centre line at floor level, +X along
the run, +Y across, +Z up.
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

import kit_portal  # noqa: E402  (the part itself: KF-PORTAL-01's blockout)

# the test section's shell (walls, ceiling, kick strip) and the part under test (kit_portal.PARTS, step 4 blockout)
FACTORY = [("Test", "Shell", 0.9, "W", "A")] + kit_portal.PARTS
VIEWS = {(c, p): ((1, 0.0, 0.0), (1, -0.6, 0.2)) for c, p, _, _, _ in FACTORY}


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


def test_shell(name, seed):
    """The test section's shell for 0.9 m between portals: graphite wall panels on the W profile, the rubber kick strip
    (no plinth light, sheet rev. B), the ceiling panel, dark backing; no floor - the part under test brings it."""
    p = kit_geo.Part(name, seed)
    L = 0.9
    half = SEC["width"] / 2
    pts = half_profile()
    segs = [((half, 0.1), (half, SEC["vertical_to"])), (pts[1], pts[2]), (pts[2], pts[3])]
    for s in (-1, 1):
        for (a, b) in segs:
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
        y0, y1 = sorted((s * (half + 0.03), s * (half + 0.04)))
        p.box("Kit_Seal", (0.0, y0, 0.0), (L, y1, SEC["ceiling"] + 0.03), panel=False)
    p.box("Kit_Graphite", (0.004, -SEC["ceiling_width"] / 2, SEC["ceiling"]), (L - 0.004, SEC["ceiling_width"] / 2, SEC["ceiling"] + 0.02),
          bevel=0.003, segments=1)
    p.box("Kit_Seal", (0.0, -half - 0.1, SEC["ceiling"] + 0.02), (L, half + 0.1, SEC["ceiling"] + 0.03), panel=False)
    p.collision_box((0.0, -half, 2.0), (L, half, SEC["ceiling"]))
    return p


def part_name_any(cat, part, size, sec, var):
    return kit_portal.part_name(cat, part, size, sec, var) if cat != "Test" else part_name(cat, part, size, sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    if cat == "Test":
        return test_shell(part_name(cat, part, size, sec_key, var), seed)
    return kit_portal.build_part(cat, part, size, sec_key, var, seed)
