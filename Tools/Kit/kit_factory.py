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
FACTORY = [("Test", "Shell", 0.9, "W", "A"), ("Terminal", "Eng", 0.7, "W", "A")] + kit_portal.PARTS
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
    # the walls (they had none: the player could walk into them) - the vertical wall and the slope as hulls
    cw = SEC["ceiling_width"] / 2
    top = SEC["vertical_to"] + SEC["slope_rise"]
    for s in (-1, 1):
        y0, y1 = sorted((s * (half - 0.03), s * (half + 0.03)))
        p.collision_box((0.0, y0, 0.0), (L, y1, SEC["vertical_to"]))
        p.collision_hull([(x, s * (yy + d), zz) for x in (0.0, L) for d in (-0.03, 0.03)
                          for yy, zz in ((half, SEC["vertical_to"]), (cw, top))])
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
        wall.decal(p, "latch_kit", 0.66, 0.75, 0.014, scale=0.7, label=True)
        wall.decal(p, "red_marker", 0.13, 1.02, 0.005, label=True)
        text_strip(p, wall, "st_gnd", 0.55, 0.82, 0.36, scale=0.75)
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
        wall.decal(p, "latch_kit", 0.3, 0.97, 0.005, scale=0.6, label=True)
        wall.decal(p, "red_dot", 0.36, 0.47, 0.005, label=True)
        text_strip(p, wall, "st_extpwr", 0.1, 0.4, 0.36, scale=0.75)
    # 3 the upper band: a slot row, a text strip, tone-on-tone hatching at the edge by the portal
    # a row of small upright slots (SC: 3-6 little cut-outs in a row)
    for i in range(6):
        wall.decal(p, "slot_s", 0.12 + i * 0.035, 1.2, 0.0, scale=0.3, rot=90.0)
    text_strip(p, wall, "st_inspect" if s < 0 else "st_torque", 0.5, 0.84, 1.2)
    wall.decal(p, "corner_mark", 0.08, 1.26, 0.0, scale=0.5, label=True)
    wall.decal(p, "st_hfcl", 0.7, 1.26, 0.0, scale=0.7, label=True)
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


CEIL_LIGHT_CD = 2.0      # 6 cd: mean 0.35, 3 cd: 0.30 against SC 0.21-0.24


def ceiling_module(p, L):
    """The ceiling panel between the portals: a slot row each side of a small vent, a text strip."""
    ceil = Face((0.0, 0.0, SEC["ceiling"]), (0, -1, 0), (0, 0, -1))
    # step 2 of the decal stack (author 6. 10.): a housed ceiling light per module - SC's ceiling modules carry their own
    # lights, the slopes and the walls sat in the dark with the portal's lights only. A framed recess, an opal diffuser,
    # a rect light aimed down (the source is the diffuser, never a bare strip)
    box = [(0.2, -0.06), (0.7, -0.06), (0.7, 0.06), (0.2, 0.06)]
    rim = [(0.18, -0.08), (0.72, -0.08), (0.72, 0.08), (0.18, 0.08)]
    ceil.ring(p, "Kit_Panel", rim, box, 0.012, 0.012)
    ceil.prism(p, "Kit_GlowNeutral", box, 0.004, 0.002, bevel=0.0)
    for x in (0.25, 0.35, 0.45, 0.55, 0.65):
        ceil.prism(p, "Kit_Graphite", [(x - 0.002, -0.06), (x + 0.002, -0.06), (x + 0.002, 0.06), (x - 0.002, 0.06)], 0.006, 0.002, bevel=0.0)
    p.socket("Light_Ceil_0", (L / 2, 0.0, SEC["ceiling"] - 0.01), x=(0, 0, -1), z=(1, 0, 0), type="rect", role="neutral",
             cd=CEIL_LIGHT_CD, width_cm=50.0, height_cm=12.0, radius_m=3.0, dir_ue=[0.0, 0.0, -1.0], along_ue=[1.0, 0.0, 0.0])
    ceil.decal(p, "vent_small", L / 2, -0.28, 0.0, scale=0.8)
    for i in range(4):
        ceil.decal(p, "slot_s", 0.12 + i * 0.035, -0.4, 0.0, scale=0.3, rot=90.0)
        ceil.decal(p, "slot_s", 0.68 + i * 0.035, 0.4, 0.0, scale=0.3, rot=90.0)
    text_strip(p, ceil, "st_inspect", 0.3, 0.6, 0.25)


def rounded_rect(w, h, r, seg=5):
    """A rounded rectangle centred on 0 in (y, z), as many points per corner as seg + 1 (rings pair two of them)."""
    pts = []
    for cy, cz, a0 in ((w / 2 - r, h / 2 - r, 0.0), (-w / 2 + r, h / 2 - r, 90.0), (-w / 2 + r, -h / 2 + r, 180.0), (w / 2 - r, -h / 2 + r, 270.0)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def face_matrix(x_front):
    # a prism drawn in (y, z) and extruded along -x from x_front (right-handed: y x z = x)
    return Matrix(((0.0, 0.0, 1.0, x_front), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def band(p, role, outer, inner, x_front, depth):
    """The band between two rounded outlines with as many points, as quads (no bevel: bevelled quads drew a groove at
    every corner segment - the radial lines the author read as plastic, 7. 10. 2026)."""
    k = len(outer)
    for i in range(k):
        j = (i + 1) % k
        p.poly_prism(role, [outer[i], outer[j], inner[j], inner[i]], face_matrix(x_front), depth, bevel=0.0, panel=False,
                     segments=1)


def face_label(p, item, y, z, x, scale=1.0, label=True, rot=0.0):
    """A decal on the terminal's face (normal +x): its frame y along +y, up +z (x cross y = the normal)."""
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    xd, yd = Vector((0.0, c, s_)), Vector((0.0, -s_, c))
    kit_batch2.label(p, item, (x, y, z), (1, 0, 0), xd, yd, scale=scale, is_label=label)


def terminal_housing(name, seed):
    """SC's wall engineering terminal (author 7. 10. 2026, his captures; round 2: "a big plastic thing - tune it into
    detail"), built in layers like the reference: a dark mounting plate behind with a shadow gap and bolts; the light
    bezel with a sunk panel line round its face, a step down into a dark inner wall and a polished lip round the deep
    glass; a two-tone top tab with a seam, slots and a status LED; the left wing (grey) with a round key in a dark
    bezel and a knurled ring, a slider grip running in a recessed channel; screws, vent slots, a stencilled ID, a
    hatching band. The screen faces +x, the pivot is the back's centre on the wall."""
    p = kit_geo.Part(name, seed)
    W, H = 0.70, 0.43
    B0, D = 0.012, 0.046               # the bezel's back (on the mounting plate) and its face
    seg = 10
    # 1 the mounting plate: dark, larger, chamfered, four bolts - the shadow line round the bezel
    mount = rounded_rect(W + 0.05, H + 0.045, 0.03, seg)
    p.poly_prism("Kit_Graphite", mount, face_matrix(B0), B0, bevel=0.002, panel=False, segments=1)
    for y, z in ((-0.36, 0.23), (0.36, 0.23), (-0.36, -0.23), (0.36, -0.23)):
        p.tube("Kit_Lip", (B0, y, z), (B0 + 0.004, y, z), 0.006, 12)
        p.tube("Kit_Graphite", (B0 + 0.004, y, z), (B0 + 0.0048, y, z), 0.0025, 6)
    # 2 the bezel: the outer rim, a sunk panel line, the face, the step down, the dark inner wall, the polished lip
    outer = rounded_rect(W, H, 0.045, seg)
    rim_in = rounded_rect(W - 0.024, H - 0.024, 0.033, seg)
    groove = rounded_rect(W - 0.030, H - 0.030, 0.030, seg)
    face_in = rounded_rect(0.626, 0.346, 0.03, seg)
    step = rounded_rect(0.610, 0.330, 0.026, seg)
    lip_out = rounded_rect(0.600, 0.320, 0.023, seg)
    lip_in = rounded_rect(0.592, 0.312, 0.020, seg)
    glass = rounded_rect(0.586, 0.306, 0.018, seg)
    band(p, "Kit_Lacquer", outer, rim_in, D, D - B0)
    band(p, "Kit_Graphite", rim_in, groove, D - 0.002, D - B0 - 0.002)
    band(p, "Kit_Lacquer", groove, face_in, D, D - B0)
    band(p, "Kit_Lacquer", face_in, step, D - 0.005, D - B0 - 0.005)          # the step down to the glass
    band(p, "Kit_Graphite", step, lip_out, D - 0.008, D - B0 - 0.008)         # the dark inner wall
    band(p, "Kit_Lip", lip_out, lip_in, D - 0.011, 0.004)                     # the polished lip
    band(p, "Kit_Graphite", lip_in, glass, D - 0.012, D - B0 - 0.012)
    p.poly_prism("Kit_Graphite", glass, face_matrix(0.013), 0.001, bevel=0.0, panel=False, segments=1)   # behind the live screen (1.5 cm)
    # 3 the top tab: a grey trapezoid with a seam, two slots and a small status LED
    tab = [(-0.15, 0.2), (0.15, 0.2), (0.13, 0.238), (-0.13, 0.238)]
    p.poly_prism("Kit_Panel", tab, face_matrix(D + 0.004), D + 0.004 - B0, bevel=0.002, segments=1)
    p.poly_prism("Kit_Graphite", [(-0.125, 0.226), (0.125, 0.226), (0.125, 0.228), (-0.125, 0.228)], face_matrix(D + 0.0045), 0.001,
                 panel=False, segments=1)
    p.poly_prism("Kit_GlowFoot", [(0.085, 0.212), (0.105, 0.212), (0.105, 0.216), (0.085, 0.216)], face_matrix(D + 0.005), 0.001,
                 panel=False, segments=1)
    for y in (-0.06, -0.045, -0.03):
        p.poly_prism("Kit_Graphite", [(y - 0.004, 0.208), (y + 0.004, 0.208), (y + 0.004, 0.22), (y - 0.004, 0.22)], face_matrix(D + 0.0045),
                     0.002, panel=False, segments=1)
    # 4 the left wing (the viewer's left: -y): a grey plate, the key in a dark bezel with a knurled ring, the slider
    wing = [(-0.335, 0.16), (-0.405, 0.13), (-0.405, -0.19), (-0.335, -0.21)]
    p.poly_prism("Kit_Panel", wing, face_matrix(D - 0.004), D - 0.004 - B0, bevel=0.003, segments=1)
    ky, kz = -0.368, 0.05
    p.tube("Kit_Graphite", (D - 0.006, ky, kz), (D - 0.001, ky, kz), 0.028, 32)
    for k in range(28):
        a = 2.0 * math.pi * k / 28
        cy, cz = ky + math.cos(a) * 0.0215, kz + math.sin(a) * 0.0215
        p.box("Kit_Lip", (D - 0.001, cy - 0.0012, cz - 0.0012), (D + 0.009, cy + 0.0012, cz + 0.0012), panel=False)
    p.tube("Kit_Panel", (D - 0.001, ky, kz), (D + 0.010, ky, kz), 0.0195, 32)
    p.tube("Kit_Lip", (D + 0.010, ky, kz), (D + 0.0115, ky, kz), 0.014, 32)
    # the slider: a dark channel sunk in the wing, the grip riding in it with its ribs
    p.box("Kit_Graphite", (D - 0.012, -0.388, -0.18), (D - 0.0035, -0.348, -0.04), bevel=0.0015, segments=1)
    p.box("Kit_Panel", (D - 0.008, -0.385, -0.165), (D + 0.004, -0.351, -0.085), bevel=0.002, segments=1)
    for k in range(7):
        z = -0.159 + k * 0.0105
        p.box("Kit_Gasket", (D + 0.004, -0.382, z), (D + 0.0075, -0.354, z + 0.005), panel=False)
    # 5 screws in the bezel's corners and the big one at the top right
    for y, z in ((-0.318, 0.178), (0.318, 0.178), (-0.318, -0.178), (0.318, -0.178)):
        p.tube("Kit_Graphite", (D - 0.0015, y, z), (D + 0.0005, y, z), 0.0055, 16)
        p.tube("Kit_Lip", (D + 0.0005, y, z), (D + 0.0015, y, z), 0.004, 6)
    p.tube("Kit_Graphite", (D - 0.002, 0.322, 0.19), (D + 0.001, 0.322, 0.19), 0.011, 24)
    p.tube("Kit_Lip", (D + 0.001, 0.322, 0.19), (D + 0.0035, 0.322, 0.19), 0.008, 24)
    # 6 the bottom: a row of vent slots on the bezel's lower band, a status LED pair at the right
    for k in range(12):
        y = -0.11 + k * 0.02
        p.poly_prism("Kit_Graphite", [(y - 0.0035, -0.2), (y + 0.0035, -0.2), (y + 0.0035, -0.188), (y - 0.0035, -0.188)], face_matrix(D + 0.0003),
                     0.003, panel=False, segments=1)
    for y in (0.24, 0.258):
        p.poly_prism("Kit_GlowFoot", [(y - 0.005, -0.195), (y + 0.005, -0.195), (y + 0.005, -0.191), (y - 0.005, -0.191)], face_matrix(D + 0.001),
                     0.001, panel=False, segments=1)
    # 7 the information layer: an ID stencil at the top left, a small service marker (a hatching band on the wing
    # had no room between the key and the slider)
    face_label(p, "st_hfcl", -0.22, 0.194, D, scale=0.55)
    face_label(p, "red_marker", 0.205, -0.193, D)
    # the screen's glow on what is in front of it
    p.socket("Light_Screen_0", (D + 0.03, 0.0, 0.0), x=(1, 0, 0), z=(0, 0, 1), type="rect", role="cool", cd=1.2,
             width_cm=56.0, height_cm=28.0, radius_m=2.0, dir_ue=[1.0, 0.0, 0.0], along_ue=[0.0, 1.0, 0.0], shadows=False)
    p.collision_box((0.0, -W / 2 - 0.03, -H / 2 - 0.02), (D, W / 2 + 0.03, H / 2 + 0.02))
    return p


def part_name_any(cat, part, size, sec, var):
    return kit_portal.part_name(cat, part, size, sec, var) if cat not in ("Test", "Terminal") else part_name(cat, part, size, sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    if cat == "Test":
        return test_shell(part_name(cat, part, size, sec_key, var), seed)
    if cat == "Terminal":
        return terminal_housing(part_name(cat, part, size, sec_key, var), seed)
    return kit_portal.build_part(cat, part, size, sec_key, var, seed)
