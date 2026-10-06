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

from mathutils import Matrix, Vector

import kit_geo

ROOT = kit_geo.ROOT
SPEC = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "Design", "KF-PORTAL-01.json"), encoding="utf-8"))
MATS = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_materials.json"), encoding="utf-8"))
SEC = kit_geo.RULES["sections"]["W"]
BEV = {r: v["bevel_mm"] / 1000.0 for r, v in MATS["roles"].items() if not r.startswith("_")}
MM = 0.001

import kit_portal  # noqa: E402  (the part itself: KF-PORTAL-01's blockout)
import kit_batch2  # noqa: E402  (the decal helper)

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
    """The test section's shell for 0.9 m between portals, built as a wall module with the decal stack (author 6. 10.
    2026, Docs/Kit/etalon/decal_stack.md): mid-grey panels (Kit_Panel), nested chamfered fields with recesses and dark
    perforated inserts, slot rows, bolts, text strips on dark bands, tone-on-tone hazard hatching, small LEDs; the rubber
    kick strip, the ceiling panel, dark backing; no floor - the part under test brings it."""
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
            p.poly_prism("Kit_Panel", [(s * y, z) for y, z in quad], run_matrix(L - 0.004), L - 0.008, bevel=0.003,
                         segments=1)
        y0, y1 = sorted((s * half, s * (half + 0.02)))
        p.box("Kit_Gasket", (0.0, y0, 0.0), (L, y1, 0.1), bevel=0.002, segments=1)
        for z in (0.025, 0.05, 0.075):
            yy0, yy1 = sorted((s * (half - 0.003), s * half))
            p.box("Kit_Gasket", (0.0, yy0, z - 0.003), (L, yy1, z + 0.003), panel=False)
        y0, y1 = sorted((s * (half + 0.03), s * (half + 0.04)))
        p.box("Kit_Seal", (0.0, y0, 0.0), (L, y1, SEC["ceiling"] + 0.03), panel=False)
        wall_module(p, s, L)
    p.box("Kit_Panel", (0.004, -SEC["ceiling_width"] / 2, SEC["ceiling"]), (L - 0.004, SEC["ceiling_width"] / 2, SEC["ceiling"] + 0.02),
          bevel=0.003, segments=1)
    p.box("Kit_Seal", (0.0, -half - 0.1, SEC["ceiling"] + 0.02), (L, half + 0.1, SEC["ceiling"] + 0.03), panel=False)
    p.collision_box((0.0, -half, 2.0), (L, half, SEC["ceiling"]))
    ceiling_module(p, L)
    return p


class Face:
    """A planar face of the shell in its own frame: x along the run, v up the face (m from its foot), h out of it into
    the corridor. Prisms are drawn in (x, v) and stand h_front out of the face; decals land on whatever is in front."""

    def __init__(self, origin, vdir, normal):
        self.o, self.v, self.n = Vector(origin), Vector(vdir).normalized(), Vector(normal).normalized()
        self.x = Vector((1.0, 0.0, 0.0))
        # a left-handed frame (x, v, n) would mirror the prisms and turn their faces inside out: draw them mirrored in
        # x with -x as the axis instead (the same place, a right-handed matrix)
        self.flip = self.x.dot(self.v.cross(self.n)) < 0
        # the decal frame: x cross y must be the normal (never mirrored), so on the left wall the text runs along -x
        self.dx = self.x if self.x.cross(self.v).dot(self.n) > 0 else -self.x

    def at(self, x, v, h=0.0):
        return self.o + self.x * x + self.v * v + self.n * h

    def matrix(self, h):
        t = self.o + self.n * h
        X, V, N = (-self.x if self.flip else self.x), self.v, self.n
        return Matrix(((X.x, V.x, N.x, t.x), (X.y, V.y, N.y, t.y), (X.z, V.z, N.z, t.z), (0.0, 0.0, 0.0, 1.0)))

    def local(self, poly):
        return [(-x, v) for x, v in poly] if self.flip else list(poly)

    def prism(self, p, role, poly, h, depth, bevel=0.0015):
        p.poly_prism(role, self.local(poly), self.matrix(h), depth, bevel=bevel, segments=1)

    def ring(self, p, role, outer, inner, h, depth):
        """The band between two polygons with as many corners (a raised frame round a field)."""
        k = len(outer)
        for i in range(k):
            j = (i + 1) % k
            p.poly_prism(role, self.local([outer[i], outer[j], inner[j], inner[i]]), self.matrix(h), depth, bevel=0.001, segments=1)

    def decal(self, p, item, x, v, h=0.0, scale=1.0, label=False, rot=0.0):
        c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        xd, yd = self.dx * c + self.v * sn, -self.dx * sn + self.v * c
        kit_batch2.label(p, item, self.at(x, v, h), self.n, xd, yd, scale=scale, is_label=label)


def octagon(x0, v0, x1, v1, c):
    return [(x0 + c, v0), (x1 - c, v0), (x1, v0 + c), (x1, v1 - c), (x1 - c, v1), (x0 + c, v1), (x0, v1 - c), (x0, v0 + c)]


def inset(poly, d):
    """An octagon (or rectangle) from octagon() shrunk by d on every side (the chamfers keep their 45 deg)."""
    xs, vs = [q[0] for q in poly], [q[1] for q in poly]
    x0, x1, v0, v1 = min(xs), max(xs), min(vs), max(vs)
    c = poly[0][0] - x0
    return octagon(x0 + d, v0 + d, x1 - d, v1 - d, max(c - d * 0.414, 0.0))


def nested_field(p, f, x0, v0, x1, v1, c, frame=0.03, h=0.014, field_role="Kit_Graphite", field_h=0.005):
    """Two levels: a raised chamfered frame (Kit_Panel) round a recessed field. Returns the field's polygon."""
    outer = octagon(x0, v0, x1, v1, c)
    inner = inset(outer, frame)
    f.ring(p, "Kit_Panel", outer, inner, h, h)
    f.prism(p, field_role, inner, field_h, field_h)
    return inner


def bolts(p, f, poly, h, d=0.016):
    xs, vs = [q[0] for q in poly], [q[1] for q in poly]
    for x, v in ((min(xs) + d, min(vs) + d), (max(xs) - d, min(vs) + d), (max(xs) - d, max(vs) - d), (min(xs) + d, max(vs) - d)):
        f.decal(p, "bolt", x, v, h, scale=0.4)


def text_strip(p, f, item, x0, x1, v, h=0.0, scale=0.7):
    """SC's text strip: a dark band 25 mm tall with a small light stencil on it."""
    f.prism(p, "Kit_Graphite", [(x0, v - 0.0125), (x1, v - 0.0125), (x1, v + 0.0125), (x0, v + 0.0125)], h + 0.0015, 0.0015, bevel=0.0)
    f.decal(p, item, (x0 + x1) / 2, v, h + 0.0015, scale=scale, label=True)


def led(p, f, x, v, h, w=0.012, t=0.004):
    f.prism(p, "Kit_GlowFoot", [(x - w / 2, v - t / 2), (x + w / 2, v - t / 2), (x + w / 2, v + t / 2), (x - w / 2, v + t / 2)], h + 0.002, 0.002,
            bevel=0.0)


def wall_module(p, s, L):
    """One side's wall between two portals (s = -1 left, +1 right; the sides differ so the corridor never mirrors)."""
    half = SEC["width"] / 2
    cw = SEC["ceiling_width"] / 2
    z0, top = SEC["vertical_to"], SEC["vertical_to"] + SEC["slope_rise"]
    sl = math.hypot(half - cw, top - z0)
    wall = Face((0.0, s * half, 0.0), (0, 0, 1), (0, -s, 0))
    # 1 the low vent band: a framed perforated intake over the kick strip
    vent = nested_field(p, wall, 0.06, 0.13, 0.84, 0.33, 0.03, frame=0.022, h=0.012, field_role="Kit_Perforated", field_h=0.003)
    bolts(p, wall, octagon(0.06, 0.13, 0.84, 0.33, 0.03), 0.012, d=0.011)
    # 2 the main plate: frame -> recess -> a third-level plate
    field = nested_field(p, wall, 0.06, 0.39, 0.84, 1.12, 0.07, frame=0.035, h=0.016)
    bolts(p, wall, octagon(0.06, 0.39, 0.84, 1.12, 0.07), 0.016, d=0.018)
    if s < 0:
        # the component cover: a chamfered plate in the recess, a smaller field in it with the maker's mark
        cover = octagon(0.2, 0.52, 0.7, 0.98, 0.06)
        wall.prism(p, "Kit_Panel", cover, 0.014, 0.009)
        mark = inset(cover, 0.03)
        wall.ring(p, "Kit_Lip", cover, inset(cover, 0.004), 0.0145, 0.0005)
        wall.prism(p, "Kit_Graphite", mark, 0.0105, 0.002)
        wall.decal(p, "maker", 0.45, 0.8, 0.0105, scale=0.42, label=True)
        wall.decal(p, "st_service", 0.45, 0.66, 0.0105, scale=0.8, label=True)
        wall.decal(p, "slot_l", 0.45, 0.56, 0.014, scale=0.8)
        led(p, wall, 0.76, 1.04, 0.005)
        led(p, wall, 0.79, 1.04, 0.005)
        wall.decal(p, "corner_mark", 0.13, 0.46, 0.005, scale=0.7, label=True)
    else:
        # the service side: a hatch with its handle, a power socket with a label, a status LED pair
        wall.decal(p, "hatch_small", 0.3, 0.86, 0.005)
        wall.decal(p, "access_panel", 0.62, 0.86, 0.005, scale=0.75)
        wall.decal(p, "socket", 0.3, 0.55, 0.005)
        wall.decal(p, "label_power", 0.3, 0.66, 0.005, scale=0.6, label=True)
        for i in range(4):
            wall.decal(p, "slot_s", 0.57 + i * 0.03, 0.55, 0.005, scale=0.3, rot=90.0)
        led(p, wall, 0.45, 0.62, 0.005)
        led(p, wall, 0.45, 0.6, 0.005)
        wall.decal(p, "tri_warning", 0.74, 0.55, 0.005, scale=0.5, label=True)
    # 3 the upper band: a slot row, a text strip, tone-on-tone hatching at the edge by the portal
    # a row of small upright slots (SC: 3-6 little cut-outs in a row)
    for i in range(6):
        wall.decal(p, "slot_s", 0.12 + i * 0.035, 1.2, 0.0, scale=0.3, rot=90.0)
    text_strip(p, wall, "st_inspect" if s < 0 else "st_torque", 0.5, 0.84, 1.2)
    wall.decal(p, "hazard_subtle", 0.03, 0.75, 0.0, scale=0.6, rot=90.0, label=True)
    wall.decal(p, "hazard_subtle", 0.87, 0.75, 0.0, scale=0.6, rot=90.0, label=True)
    # 4 the slope: perforated panels in a frame with a middle bar
    up = Vector((0.0, -s * (half - cw) / sl, (top - z0) / sl))
    slope = Face((0.0, s * half, z0), up, Vector((s, 0, 0)).cross(up))
    frame = octagon(0.06, 0.08, 0.84, 0.92, 0.06)
    inner = inset(frame, 0.03)
    slope.ring(p, "Kit_Panel", frame, inner, 0.014, 0.014)
    slope.prism(p, "Kit_Panel", [(0.09, 0.485), (0.81, 0.485), (0.81, 0.515), (0.09, 0.515)], 0.014, 0.011)
    if s < 0:
        slope.prism(p, "Kit_Perforated", inner, 0.003, 0.003)
    else:
        # the right slope: the lower half perforated, the upper half a plate with a small hatch
        (a0, b0), (a1, _), (_, b1), _, _, _, _, (x0, _) = inner
        x1, v1 = inner[2][0], inner[4][1]
        c = a0 - x0
        slope.prism(p, "Kit_Perforated", [(a0, b0), (a1, b0), (x1, b0 + c), (x1, 0.5), (x0, 0.5), (x0, b0 + c)], 0.003, 0.003)
        slope.prism(p, "Kit_Panel", [(x0, 0.5), (x1, 0.5), (x1, v1 - c), (x1 - c, v1), (x0 + c, v1), (x0, v1 - c)], 0.008, 0.005)
        slope.decal(p, "hatch_small", 0.45, 0.72, 0.008, scale=0.9)
    bolts(p, slope, frame, 0.014, d=0.015)
    slope.decal(p, "hazard_subtle", 0.25, 0.095, 0.014, scale=0.55, label=True)
    slope.decal(p, "hazard_subtle", 0.65, 0.905, 0.014, scale=0.55, label=True)
    text_strip(p, slope, "st_vent" if s < 0 else "st_service", 0.3, 0.6, 0.5, 0.014)
    # the dirt where it forms (Halcyon alpha ~0.8): along the kick strip's top
    p.grime("rim", (0.45, s * half, 0.11), (0, -s, 0), (0, 0, 1), (0.8, 0.06), 0.8)


def ceiling_module(p, L):
    """The ceiling panel between the portals: a slot row each side of a small vent, a text strip."""
    ceil = Face((0.0, 0.0, SEC["ceiling"]), (0, -1, 0), (0, 0, -1))
    ceil.decal(p, "vent_small", L / 2, 0.0, 0.0)
    for i in range(4):
        ceil.decal(p, "slot_s", 0.12 + i * 0.035, -0.4, 0.0, scale=0.3, rot=90.0)
        ceil.decal(p, "slot_s", 0.68 + i * 0.035, 0.4, 0.0, scale=0.3, rot=90.0)
    text_strip(p, ceil, "st_inspect", 0.3, 0.6, 0.25)


def part_name_any(cat, part, size, sec, var):
    return kit_portal.part_name(cat, part, size, sec, var) if cat != "Test" else part_name(cat, part, size, sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    if cat == "Test":
        return test_shell(part_name(cat, part, size, sec_key, var), seed)
    return kit_portal.build_part(cat, part, size, sec_key, var, seed)
