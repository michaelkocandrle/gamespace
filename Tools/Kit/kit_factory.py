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
FACTORY = [("Test", "Shell", 0.9, "W", "A"), ("Terminal", "Eng", 0.7, "W", "A"), ("Bay", "Service", 1.0, "W", "A"),
           ("Cockpit", "Console", 1.2, "W", "A"), ("Cockpit", "Console", 1.2, "W", "B"),
           ("Cockpit", "Console", 1.2, "W", "BR"),
           # cockpit v3 (8. 10. 2026): the seat's arms and the wall consoles, left and mirrored right
           ("Cockpit", "SeatArm", 0.7, "W", "L"), ("Cockpit", "SeatArm", 0.7, "W", "R"),
           ("Cockpit", "ConsoleWall", 1.8, "W", "L"), ("Cockpit", "ConsoleWall", 1.8, "W", "R"),
           ("Cockpit", "SeatBack", 0.7, "W", "A")] + kit_portal.PARTS
VIEWS = {(c, p): ((1, 0.0, 0.0), (1, -0.6, 0.2)) for c, p, _, _, _ in FACTORY}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


def budget(cat, part, size):
    return 90000 if cat == "Cockpit" else 40000


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
    """SC's wall engineering terminal, round 3 (author 7. 10. 2026: "too robust, not high-tech; one flat white without
    sheen reads as plastic; the bits at the bottom look out of place"): a slim shell - 33 mm border, 30 mm deep - in a
    light grey paint under a clear coat, its outer edge rounded in five steps so the light runs round it, the tab grown
    out of the outline; a hairline polished lip and a satin dark step down to the glass; a shadow gap behind (a smaller
    dark body); on the left border a slim recessed slider and a small key; nothing stuck on. The screen faces +x, the
    pivot is the back's centre on the wall."""
    p = kit_geo.Part(name, seed)
    seg = 12
    GW, GH = 0.586, 0.306                      # the glass (the live screen fills it)
    OW, OH = 0.606, 0.326                      # the shell's opening
    W, H, R = 0.672, 0.392, 0.042              # the shell
    X0, XF = 0.012, 0.030                      # the shell's back and face (the body behind it 12 mm deep, set in)
    fm = lambda x: face_matrix(x)              # noqa: E731
    outer = rounded_rect(W, H, R, seg)
    # the tab grows out of the top edge (between the two top corners)
    top = H / 2
    k = seg + 1
    outer = outer[:k] + [(0.135, top), (0.118, top + 0.017), (-0.118, top + 0.017), (-0.135, top)] + outer[k:]
    opening = rounded_rect(OW, OH, 0.026, seg)
    # 1 the body behind: dark, 8 mm smaller all round - the shell floats on a shadow gap
    p.poly_prism("Kit_Graphite", rounded_rect(W - 0.016, H - 0.016, R - 0.008, seg), fm(X0), X0, bevel=0.002, panel=False, segments=2)
    # 2 the shell: rounded outer edge (5 steps), a softer inner edge
    p.frame_ring("Kit_Shell", outer, opening, fm(XF), XF - X0, bevel_out=0.0075, bevel_in=0.003, segments=5)
    # 3 the hairline lip and the satin step down to the glass
    lip_o = rounded_rect(OW, OH, 0.026, seg)
    lip_i = rounded_rect(OW - 0.004, OH - 0.004, 0.024, seg)
    p.frame_ring("Kit_Lip", lip_o, lip_i, fm(XF - 0.004), 0.003, bevel_in=0.0008, segments=2, panel=False)
    p.frame_ring("Kit_Graphite", lip_i, rounded_rect(GW, GH, 0.018, seg), fm(XF - 0.007), XF - 0.007 - X0, bevel_in=0.0015, segments=3,
                 panel=False)
    p.poly_prism("Kit_Graphite", rounded_rect(GW, GH, 0.018, seg), fm(0.013), 0.001, bevel=0.0, panel=False, segments=1)
    # 4 the tab: a dark glass sensor window set in it, a 3 mm status light
    win = rounded_rect(0.09, 0.008, 0.0035, 6)
    win = [(y, z + top + 0.0085) for y, z in win]
    win_rim = [(y, z + top + 0.0085) for y, z in rounded_rect(0.094, 0.012, 0.005, 6)]
    p.frame_ring("Kit_Lip", win_rim, win, fm(XF + 0.0003), 0.0015, panel=False, segments=1)
    p.poly_prism("Kit_Glass", win, fm(XF - 0.0005), 0.002, bevel=0.0, panel=False, segments=1)
    p.lathe("Kit_GlowFoot", [(0.0, 0.0), (0.0016, 0.0), (0.0016, 0.0012), (0.0, 0.0014)], (XF - 0.0005, 0.075, top + 0.0085), axis=(1, 0, 0),
            seg=16)
    # 5 the left border: a slim recessed slot with the slider, a small key above it (no wing bolted on)
    sy = -(OW / 2 + (W - OW) / 4)
    slot_o = [(y + sy, z - 0.05) for y, z in rounded_rect(0.013, 0.1, 0.0065, 6)]
    slot_i = [(y + sy, z - 0.05) for y, z in rounded_rect(0.009, 0.096, 0.0045, 6)]
    p.frame_ring("Kit_Lip", slot_o, slot_i, fm(XF + 0.0002), 0.001, panel=False, segments=1)
    p.poly_prism("Kit_Graphite", slot_i, fm(XF - 0.004), 0.004, bevel=0.0, panel=False, segments=1)
    p.poly_prism("Kit_Shell", [(y + sy, z - 0.028) for y, z in rounded_rect(0.008, 0.022, 0.0035, 6)], fm(XF - 0.0005), 0.004,
                 bevel=0.0012, panel=False, segments=3)
    for k2 in range(5):
        z = -0.035 + k2 * 0.0035
        p.poly_prism("Kit_Graphite", [(sy - 0.003, z), (sy + 0.003, z), (sy + 0.003, z + 0.0012), (sy - 0.003, z + 0.0012)], fm(XF + 0.0001), 0.0006,
                     panel=False, segments=1)
    p.lathe("Kit_Lip", [(0.0074, 0.0), (0.0074, 0.0012), (0.0062, 0.0016), (0.0, 0.0016)], (XF - 0.0004, sy, 0.055), axis=(1, 0, 0), seg=32)
    p.lathe("Kit_Shell", [(0.0058, 0.0), (0.0058, 0.0024), (0.0052, 0.0034), (0.0035, 0.004), (0.0, 0.0042)], (XF + 0.0008, sy, 0.055),
            axis=(1, 0, 0), seg=32)
    # 6 four small countersunk screws in the corners, flush
    for y, z in ((-0.306, 0.166), (0.306, 0.166), (-0.306, -0.166), (0.306, -0.166)):
        p.lathe("Kit_Lip", [(0.0032, 0.0), (0.0032, 0.0004), (0.0, 0.0006)], (XF - 0.0002, y, z), axis=(1, 0, 0), seg=16)
        p.box("Kit_Graphite", (XF + 0.0003, y - 0.0021, z - 0.00035), (XF + 0.0006, y + 0.0021, z + 0.00035), panel=False)
    # 7 a small ID stencil in the top left of the border
    face_label(p, "st_hfcl", -0.22, 0.176, XF, scale=0.42)
    # the screen's glow on what is in front of it
    p.socket("Light_Screen_0", (XF + 0.03, 0.0, 0.0), x=(1, 0, 0), z=(0, 0, 1), type="rect", role="cool", cd=0.5,
             width_cm=56.0, height_cm=28.0, radius_m=2.0, dir_ue=[1.0, 0.0, 0.0], along_ue=[0.0, 1.0, 0.0], shadows=False)
    p.collision_box((0.0, -W / 2, -H / 2), (XF, W / 2, H / 2 + 0.017))
    return p


FONTS = {"rajdhani": "Content/UI/Fonts/Rajdhani-SemiBold.ttf", "saira": "Content/UI/Fonts/Saira-SemiBold.ttf"}


def emboss_text(p, role, body, y, z, x, size, depth, font="rajdhani", bevel=0.0, wrap=None):
    """Raised lettering as real geometry on a face looking +x (SC's embossed maker's mark on the component bay cover;
    a decal stencil read as print). size = the font's em in metres; the letters stand `depth` proud of x, flat-shaded."""
    import bpy
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(os.path.join(ROOT, FONTS[font]), check_existing=True)
    cu.size = size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = depth / 2
    cu.bevel_depth, cu.bevel_resolution = bevel, 0
    cu.resolution_u = 3                         # the glyphs' curves: 12 (default) tripled the part's triangles
    ob = bpy.data.objects.new("txt", cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    # the text's x right, y up, z out -> the part's +y, +z, +x; its back sits on the face
    if wrap is None:
        verts = [(x + v.co.z + depth / 2, y + v.co.x, z + v.co.y) for v in me.vertices]
    else:
        # printed on a body of revolution round a vertical axis through (cx, cy) of radius r: the text's x runs round it
        # (its middle facing +x), its z out of the surface
        cx, cy, r = wrap
        verts = []
        for v in me.vertices:
            a, rr = (y + v.co.x) / r, r + v.co.z + depth / 2
            verts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z + v.co.y))
    faces = [list(f.vertices) for f in me.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)
    for f in p.mesh(role, verts, faces):
        f.smooth = False


def box_yz(p, role, y0, z0, y1, z1, x_front, depth, bevel=0.0015):
    p.poly_prism(role, [(y0, z0), (y1, z0), (y1, z1), (y0, z1)], face_matrix(x_front), depth, bevel=bevel, panel=False, segments=1)


def chamfer_band(p, role, outer, x_out, inner, x_in):
    """A sloped facet between two outlines with as many points (y, z) on a face looking +x: the outer one at x_out, the
    inner one at x_in - SC's wide 45 deg chamfers round covers and niche frames, flat-shaded so the facet catches light."""
    k = len(outer)
    verts = [(x_out, y, z) for y, z in outer] + [(x_in, y, z) for y, z in inner]
    faces = [[i, (i + 1) % k, k + (i + 1) % k, k + i] for i in range(k)]
    for f in p.mesh(role, verts, faces):
        f.smooth = False


def raised_frame(p, opening, front, w=0.022, h=0.012, c=0.012):
    """A frame standing proud round an opening (critic 7. 10. 2026: the niches were cut straight into a flat plate): a
    chamfered outer facet up from the face plate, a flat top band to the opening's lip."""
    outer = inset(opening, -w)
    top = inset(opening, -(w - c))
    chamfer_band(p, "Kit_Housing", outer, front, top, front + h)
    band(p, "Kit_Housing", top, opening, front + h, h)


def niche(p, y0, z0, y1, z1, c, front, deep, wall_role, back_role, lip=True):
    """An octagonal recess in the bay's face: a frame band (lip), the inner walls as bands stepping back, a back panel
    (emissive for a lit niche). Returns the opening's octagon."""
    o = octagon(y0, z0, y1, z1, c)
    if lip:
        band(p, "Kit_Lip", octagon(y0 - 0.006, z0 - 0.006, y1 + 0.006, z1 + 0.006, c + 0.0025), o, front + 0.002, 0.004)
    # the walls: a thin ring round the opening, deep
    band(p, wall_role, o, inset(o, 0.004), front, deep)
    p.poly_prism(back_role, inset(o, 0.004), face_matrix(front - deep + 0.002), 0.002, bevel=0.0, panel=False, segments=1)
    return o


class Scaled:
    """A Part seen through a uniform scale about a point: lathe, sweep and box take the same arguments as on the Part
    (the extinguisher was modelled at a 2 kg size; the author 7. 10. 2026 wants it bigger - SC's fills its niche)."""

    def __init__(self, p, origin, s):
        self.p, self.o, self.s = p, Vector(origin), s

    def _pt(self, q):
        return tuple(self.o + (Vector(q) - self.o) * self.s)

    def lathe(self, role, profile, base, axis=(0, 0, 1), seg=48, close=False):
        self.p.lathe(role, [(r * self.s, h * self.s) for r, h in profile], self._pt(base), axis, seg=seg, close=close)

    def sweep(self, role, path, r, seg=16, caps=True, scale_y=1.0):
        self.p.sweep(role, [self._pt(q) for q in path], r * self.s, seg=seg, caps=caps, scale_y=scale_y)

    def box(self, role, lo, hi, bevel=0.0, segments=2, panel=True):
        self.p.box(role, self._pt(lo), self._pt(hi), bevel=bevel * self.s, segments=segments, panel=panel)


def extinguisher(p, ex, ey, z0):
    """A fire extinguisher modelled as one (author 7. 10. 2026: the first one was "a cylinder with something on top",
    low quality): a 2 kg canister - the body turned from a profile (a domed foot, a soft shoulder, a neck), glossy red
    under a clear coat; a rubber foot ring and a label sleeve; the head - a valve body with its collar, a pressure gauge
    with a white dial and a polished bezel, the carry handle and the squeeze lever (flat swept straps), the safety pin
    with its pull ring; a rubber hose with polished ferrules down to the nozzle in a clip; the wall bracket with two
    straps and their buckles. ex, ey: the axis; z0 its foot. Faces +x (the niche's opening)."""
    up = (0, 0, 1)
    body = [(0.0, 0.0), (0.016, 0.0012), (0.028, 0.005), (0.036, 0.0115), (0.0405, 0.0215), (0.042, 0.034), (0.042, 0.258),
            (0.0412, 0.27), (0.0385, 0.2805), (0.0335, 0.2895), (0.0265, 0.2955), (0.019, 0.299), (0.0155, 0.3005), (0.0155, 0.31)]
    p.lathe("Kit_Red", body, (ex, ey, z0), up, seg=56, close=True)
    # the rubber foot and the label sleeve (a cream band with a hairline edge)
    p.lathe("Kit_Gasket", [(0.0418, 0.009), (0.0432, 0.0115), (0.0436, 0.016), (0.0436, 0.029), (0.0428, 0.032), (0.0418, 0.0335)],
            (ex, ey, z0), up, seg=56)
    p.lathe("Kit_Lacquer", [(0.0419, 0.104), (0.0425, 0.1055), (0.0425, 0.2045), (0.0419, 0.206)], (ex, ey, z0), up, seg=56)
    p.lathe("Kit_Graphite", [(0.04255, 0.122), (0.04265, 0.1225), (0.04265, 0.1265), (0.04255, 0.127)], (ex, ey, z0), up, seg=56)
    # the head: the collar, the valve body, its cap
    zh = z0 + 0.31
    p.lathe("Kit_Lip", [(0.0158, 0.0), (0.0175, 0.0015), (0.0175, 0.007), (0.0158, 0.0085)], (ex, ey, zh - 0.004), up, seg=32)
    p.lathe("Kit_Graphite", [(0.0145, 0.0), (0.0145, 0.012), (0.0158, 0.014), (0.0158, 0.026), (0.0132, 0.031), (0.009, 0.0335),
                              (0.0, 0.0345)], (ex, ey, zh + 0.004), up, seg=32, close=True)
    # the gauge on the valve's front: polished bezel, white dial, a dark needle
    gx, gz = ex + 0.0155, zh + 0.021
    p.lathe("Kit_Lip", [(0.0062, 0.0), (0.0098, 0.0005), (0.0102, 0.004), (0.0094, 0.0062), (0.0082, 0.0064)], (gx, ey, gz), (1, 0, 0), seg=32)
    p.lathe("Kit_Lacquer", [(0.0082, 0.0055), (0.0, 0.0058)], (gx, ey, gz), (1, 0, 0), seg=32)
    p.box("Kit_Graphite", (gx + 0.0059, ey - 0.0004, gz - 0.0005), (gx + 0.0062, ey + 0.0055, gz + 0.0005), panel=False)
    p.lathe("Kit_GlowRed", [(0.0016, 0.0059), (0.0, 0.006)], (gx, ey - 0.004, gz - 0.003), (1, 0, 0), seg=10)
    # the carry handle (fixed, below) and the squeeze lever (above): flat swept straps running out to +y
    p.sweep("Kit_Graphite", [(ex, ey + 0.008, zh + 0.012), (ex, ey + 0.03, zh + 0.008), (ex, ey + 0.056, zh + 0.0005),
                             (ex, ey + 0.078, zh - 0.008), (ex, ey + 0.088, zh - 0.015)], 0.0062, seg=14, scale_y=0.42)
    p.sweep("Kit_Graphite", [(ex, ey + 0.006, zh + 0.03), (ex, ey + 0.03, zh + 0.034), (ex, ey + 0.058, zh + 0.03),
                             (ex, ey + 0.082, zh + 0.02), (ex, ey + 0.094, zh + 0.011)], 0.0055, seg=14, scale_y=0.45)
    p.sweep("Kit_Gasket", [(ex, ey + 0.05, zh + 0.002), (ex, ey + 0.068, zh - 0.004), (ex, ey + 0.084, zh - 0.0125)], 0.0068, seg=14,
            scale_y=0.6)                                                                        # the handle's grip
    # the safety pin through the valve and its pull ring, a thin tamper seal
    p.sweep("Kit_Lip", [(ex - 0.012, ey + 0.012, zh + 0.022), (ex + 0.018, ey + 0.012, zh + 0.022)], 0.0012, seg=8)
    ring = [(ex + 0.018 + 0.0085 * (1 - math.cos(a)), ey + 0.012, zh + 0.022 + 0.0085 * math.sin(a))
            for a in [2 * math.pi * k / 24 for k in range(25)]]
    p.sweep("Kit_Lip", ring, 0.0014, seg=8, caps=False)
    p.sweep("Kit_GlowRed", [(ex + 0.02, ey + 0.012, zh + 0.0215), (ex + 0.022, ey + 0.006, zh + 0.012)], 0.0005, seg=6)
    # the hose: out of the valve's side (-y), down along the body to the nozzle held in a clip
    hose = [(ex, ey - 0.016, zh + 0.016), (ex + 0.004, ey - 0.032, zh + 0.012), (ex + 0.014, ey - 0.047, zh - 0.006),
            (ex + 0.024, ey - 0.055, zh - 0.04), (ex + 0.026, ey - 0.057, zh - 0.085), (ex + 0.018, ey - 0.055, zh - 0.125),
            (ex + 0.012, ey - 0.052, zh - 0.15)]
    p.sweep("Kit_Gasket", hose, 0.0058, seg=16)
    for c, a in ((hose[0], (0, -1, 0)), (hose[-1], (0, 0, -1))):
        p.lathe("Kit_Lip", [(0.0068, 0.0), (0.0072, 0.002), (0.0072, 0.009), (0.0066, 0.011)], c, a, seg=24)
    nz = (ex + 0.012, ey - 0.052, zh - 0.161)
    p.lathe("Kit_Graphite", [(0.0066, 0.0), (0.0078, 0.006), (0.0094, 0.03), (0.0102, 0.042), (0.0096, 0.045), (0.0072, 0.046)], nz,
            (0, 0, -1), seg=28)
    p.box("Kit_Lip", (ex + 0.002, ey - 0.0625, zh - 0.135), (ex + 0.008, ey - 0.0415, zh - 0.127), bevel=0.001, segments=2)   # the clip
    # the wall bracket: a back plate, two straps round the body with their buckles
    p.box("Kit_Panel", (ex - 0.052, ey - 0.03, z0 + 0.04), (ex - 0.044, ey + 0.03, z0 + 0.27), bevel=0.003, segments=3)
    for zb in (z0 + 0.07, z0 + 0.225):
        p.lathe("Kit_Graphite", [(0.0436, 0.0), (0.0452, 0.0008), (0.0452, 0.0132), (0.0436, 0.014)], (ex, ey, zb), up, seg=56)
        p.box("Kit_Lip", (ex + 0.041, ey - 0.008, zb - 0.002), (ex + 0.0485, ey + 0.008, zb + 0.016), bevel=0.0015, segments=3)
        p.box("Kit_Graphite", (ex + 0.0485, ey - 0.005, zb + 0.004), (ex + 0.05, ey + 0.005, zb + 0.01), panel=False)


def bay_service(name, seed):
    """SC's engineering bay wall after the author's capture (7. 10. 2026; Docs/Kit/etalon/sc/decal_aurora_bay.jpg): in a
    grey frame 1.0 x 1.72 m, 0.18 m deep - a fire extinguisher unit (an octagonal niche lit red, the extinguisher in its
    bracket, a hatch under it with a red marker), two lockers with warm-lit cream insides and polished lips, the
    component bay cover (four nested octagonal levels, the maker's mark and a stencil), louvers and a slot row over
    them, bolts and hatching. The face is +x, the pivot is the back's bottom centre on the wall; -y is the viewer's left."""
    p = kit_geo.Part(name, seed)
    W, H, D = 1.0, 1.72, 0.21                  # 21 cm deep (was 18): room for the bigger extinguisher in its niche
    # the carcass: back, sides, top; the face plate as bands round the three columns
    box_yz(p, "Kit_Graphite", -W / 2, 0.0, W / 2, H, 0.02, 0.02)
    face = D - 0.03
    # the carcass: hollow (the niches sink into it) - sides, top, bottom; the face plate in cells round the openings
    p.box("Kit_Housing", (0.02, -W / 2, 0.0), (face, -W / 2 + 0.015, H), bevel=0.003, segments=1)
    p.box("Kit_Housing", (0.02, W / 2 - 0.015, 0.0), (face, W / 2, H), bevel=0.003, segments=1)
    p.box("Kit_Housing", (0.02, -W / 2, H - 0.015), (face, W / 2, H), bevel=0.003, segments=1)
    p.box("Kit_Housing", (0.02, -W / 2, 0.0), (face, W / 2, 0.015), bevel=0.003, segments=1)

    def cell(y0, z0, y1, z1, opening=None):
        if opening is None:
            box_yz(p, "Kit_Housing", y0, z0, y1, z1, face, 0.02, bevel=0.002)
        else:
            band(p, "Kit_Housing", octagon(y0, z0, y1, z1, 0.0008), opening, face, 0.02)
    # columns (y): A the fire unit -0.485..-0.235, B the lockers -0.225..0.085, C the component bay 0.09..0.49
    cell(-0.5, 0.0, -0.485, H)
    cell(0.49, 0.0, 0.5, H)
    cell(-0.235, 0.0, -0.225, H)
    cell(0.085, 0.0, 0.09, H)
    cell(0.09, 0.0, 0.49, H)
    cell(-0.485, 0.0, -0.235, 0.80)
    cell(-0.485, 1.50, -0.235, H)
    cell(-0.225, 0.0, 0.085, 0.16)
    cell(-0.225, 0.80, 0.085, 0.84)
    cell(-0.225, 1.48, 0.085, H)
    cell(-0.485, 0.80, -0.235, 1.50, octagon(-0.47, 0.82, -0.25, 1.48, 0.03))
    cell(-0.225, 0.16, 0.085, 0.80, octagon(-0.205, 0.18, 0.065, 0.78, 0.05))
    cell(-0.225, 0.84, 0.085, 1.48, octagon(-0.205, 0.86, 0.065, 1.46, 0.05))
    # A: the fire extinguisher niche lit red, 0.8 m up; the extinguisher 1.3x the 2 kg model (author 7. 10. 2026:
    # "still bigger" - SC's fills its niche: ~11 cm across, ~47 cm tall) standing in a dark cradle, a clamp housing over it
    deep = 0.155
    niche(p, -0.47, 0.82, -0.25, 1.48, 0.03, face, deep, "Kit_Graphite", "Kit_Red")
    raised_frame(p, octagon(-0.47, 0.82, -0.25, 1.48, 0.03), face, w=0.012, h=0.01, c=0.008)
    ey, ex, zf = -0.378, face - 0.082, 0.905
    extinguisher(Scaled(p, (ex, ey, zf), 1.3), ex, ey, zf)
    # the cradle: a dark block across the niche's foot, a polished lip on its front edge, a rubber cup the foot sits in
    p.box("Kit_Graphite", (face - deep + 0.004, -0.444, 0.852), (face - 0.022, -0.276, zf), bevel=0.01, segments=3)
    p.lathe("Kit_Lip", [(0.064, 0.0), (0.067, 0.001), (0.067, 0.003), (0.064, 0.004)], (ex, ey, zf - 0.002), (0, 0, 1), seg=48)
    for y in (-0.43, -0.29):
        p.lathe("Kit_Lip", [(0.005, 0.0), (0.005, 0.0015), (0.0035, 0.003), (0.0, 0.0032)], (face - 0.022, y, 0.878), (1, 0, 0), seg=16)
    p.box("Kit_Lip", (face - 0.024, -0.444, zf - 0.008), (face - 0.021, -0.276, zf - 0.004), bevel=0.0008, segments=1, panel=False)
    p.lathe("Kit_Gasket", [(0.058, 0.0), (0.063, 0.002), (0.063, 0.018), (0.06, 0.02)], (ex, ey, zf - 0.004), (0, 0, 1), seg=48)
    face_label(p, "red_dot", -0.31, 0.878, face - 0.0215, scale=0.8)
    # the clamp housing at the top: a dark block with a grille of slots and a red status pip
    p.box("Kit_Graphite", (face - deep + 0.004, -0.444, 1.405), (face - 0.03, -0.276, 1.452), bevel=0.004, segments=2)
    for k in range(5):
        yk = -0.4 + k * 0.018
        p.box("Kit_Housing", (face - 0.0305, yk - 0.004, 1.414), (face - 0.0295, yk + 0.004, 1.443), panel=False)
    p.lathe("Kit_GlowRed", [(0.0025, 0.0), (0.0025, 0.0012), (0.0, 0.0016)], (face - 0.03, -0.3, 1.428), (1, 0, 0), seg=12)
    p.box("Kit_GlowRed", (face - 0.07, -0.43, 1.399), (face - 0.036, -0.29, 1.406), panel=False)     # the source under it
    p.socket("Light_Fire_0", (face - 0.05, ey, 1.39), x=(1, 0, 0), z=(0, 0, 1), type="point", role="signal", cd=0.7,
             radius_m=0.32, source_radius_cm=1.0, shadows=False)
    # under it: a hatch with a recessed grip and the red marker; a text strip at the foot
    hatch = octagon(-0.47, 0.18, -0.25, 0.74, 0.02)
    p.poly_prism("Kit_Housing", hatch, face_matrix(face + 0.008), 0.008, bevel=0.002, segments=1)
    box_yz(p, "Kit_Graphite", -0.40, 0.62, -0.32, 0.645, face + 0.0085, 0.006)
    for z in (0.22, 0.70):
        for y in (-0.455, -0.265):
            p.tube("Kit_Lip", (face + 0.008, y, z), (face + 0.010, y, z), 0.004, 8)
    # B: two lockers (author 7. 10.: flat glowing white boxes): a cream lacquer inside lit by a housed warm strip under
    # its roof, not an emissive back - the back a raised panel with a chamfered top (SC's shield outline) and a hairline
    # lip, two coat hooks, a rubber mat on the floor behind a polished sill, the latch slot in the roof
    ldeep = 0.15
    for z0, z1 in ((0.18, 0.78), (0.86, 1.46)):
        niche(p, -0.205, z0, 0.065, z1, 0.05, face, ldeep, "Kit_Lacquer", "Kit_Lacquer")
        raised_frame(p, octagon(-0.205, z0, 0.065, z1, 0.05), face, w=0.016, h=0.012, c=0.01)
        back = face - ldeep + 0.004
        shield = [(-0.18, z0 + 0.04), (0.04, z0 + 0.04), (0.04, z1 - 0.11), (0.0, z1 - 0.07), (-0.14, z1 - 0.07), (-0.18, z1 - 0.11)]
        p.poly_prism("Kit_Lacquer", shield, face_matrix(back + 0.01), 0.01, bevel=0.003, segments=2)
        band(p, "Kit_Lip", [(-0.183, z0 + 0.037), (0.043, z0 + 0.037), (0.043, z1 - 0.109), (0.001, z1 - 0.067), (-0.141, z1 - 0.067),
                            (-0.183, z1 - 0.109)], shield, back + 0.0085, 0.002)
        for y in (-0.12, -0.02):
            p.lathe("Kit_Lip", [(0.009, 0.0), (0.009, 0.003), (0.0045, 0.006), (0.0045, 0.028), (0.007, 0.031), (0.0, 0.034)],
                    (back + 0.01, y, z1 - 0.15), (1, 0, 0), seg=20, close=True)
        # the roof's light: a housed strip with an opal diffuser across the front of the roof
        p.box("Kit_Graphite", (face - 0.08, -0.152, z1 - 0.016), (face - 0.028, 0.012, z1 - 0.003), bevel=0.002, segments=1)
        p.box("Kit_GlowWarm", (face - 0.074, -0.146, z1 - 0.019), (face - 0.034, 0.006, z1 - 0.015), panel=False)
        p.socket("Light_Locker_%d" % int(z0 * 10), (face - 0.055, -0.07, z1 - 0.03), x=(1, 0, 0), z=(0, 0, 1), type="point",
                 role="warm", cd=0.12, radius_m=0.45, source_radius_cm=2.0, shadows=False)
        # the latch slot in the roof, behind the light
        p.box("Kit_Graphite", (face - 0.12, -0.11, z1 - 0.012), (face - 0.09, -0.03, z1 - 0.003), bevel=0.001, segments=1, panel=False)
        # the floor: a rubber mat, a polished sill at the front edge
        p.box("Kit_AntiSlip", (back + 0.012, -0.17, z0), (face - 0.02, 0.03, z0 + 0.006), bevel=0.002, segments=1)
        for k in range(7):
            yk = -0.155 + k * 0.029
            p.box("Kit_Gasket", (back + 0.016, yk, z0 + 0.006), (face - 0.024, yk + 0.012, z0 + 0.008), panel=False)
        p.box("Kit_Lip", (face - 0.018, -0.172, z0 - 0.002), (face - 0.004, 0.032, z0 + 0.008), bevel=0.002, segments=2)
    # C: the component bay cover after SC's (the author's capture): a heavy plate standing proud of a dark recess, its
    # edge a wide 45 deg chamfer that catches the light, a hairline groove inset on its face, the maker's mark large;
    # latches each side, a recessed pull at the foot
    c0 = octagon(0.10, 0.16, 0.48, 1.05, 0.06)
    band(p, "Kit_Housing", c0, inset(c0, 0.025), face + 0.018, 0.012)
    p.poly_prism("Kit_Graphite", inset(c0, 0.025), face_matrix(face + 0.008), 0.002, bevel=0.0, panel=False, segments=1)
    plate = octagon(0.135, 0.20, 0.445, 1.01, 0.075)
    cf = face + 0.036                                                  # the cover's face
    p.poly_prism("Kit_Housing", plate, face_matrix(cf - 0.028), 0.006, bevel=0.0, panel=False, segments=1)
    pface = inset(plate, 0.045)
    chamfer_band(p, "Kit_Panel", plate, cf - 0.028, pface, cf)
    p.poly_prism("Kit_Housing", pface, face_matrix(cf), 0.002, bevel=0.0, panel=False, segments=1)
    band(p, "Kit_Graphite", inset(plate, 0.03), inset(plate, 0.033), cf + 0.0003, 0.0006)
    band(p, "Kit_Lip", inset(plate, 0.0155), inset(plate, 0.0175), cf + 0.0002, 0.0004)
    for y, sgn in ((0.135, -1), (0.445, 1)):
        yc = y + sgn * 0.004
        p.box("Kit_Lip", (face + 0.012, yc - 0.009, 0.56), (face + 0.03, yc + 0.009, 0.66), bevel=0.003, segments=2)
        p.box("Kit_Graphite", (face + 0.029, yc - 0.003, 0.575), (face + 0.031, yc + 0.003, 0.645), panel=False)
    box_yz(p, "Kit_Graphite", 0.23, 0.245, 0.35, 0.272, cf + 0.0004, 0.012)                 # the pull, sunk in the face
    box_yz(p, "Kit_Lip", 0.235, 0.249, 0.345, 0.252, cf - 0.004, 0.002, bevel=0.0)
    # over the cover: the coolant loop's service hatch (the plain field read empty) - a raised plate with quarter-turn
    # fasteners, a recessed intake grille, a status LED pair and its stencil strip
    hp = octagon(0.13, 1.1, 0.45, 1.46, 0.035)
    p.poly_prism("Kit_Housing", hp, face_matrix(face + 0.012), 0.012, bevel=0.004, segments=2)
    band(p, "Kit_Lip", inset(hp, 0.008), inset(hp, 0.0095), face + 0.0122, 0.0004)
    for y, z in ((0.155, 1.125), (0.425, 1.125), (0.155, 1.435), (0.425, 1.435)):
        p.lathe("Kit_Lip", [(0.0075, 0.0), (0.0075, 0.0015), (0.006, 0.0028), (0.0, 0.003)], (face + 0.012, y, z), (1, 0, 0), seg=20)
        p.box("Kit_Graphite", (face + 0.0148, y - 0.005, z - 0.0008), (face + 0.0152, y + 0.005, z + 0.0008), panel=False)
    grille = octagon(0.17, 1.2, 0.41, 1.37, 0.02)
    p.poly_prism("Kit_Graphite", grille, face_matrix(face + 0.0125), 0.006, bevel=0.0, panel=False, segments=1)
    for k in range(8):
        z = 1.212 + k * 0.0195
        p.box("Kit_Housing", (face + 0.0118, 0.18, z), (face + 0.0168, 0.40, z + 0.009), bevel=0.0015, segments=2)
    for y in (0.37, 0.39):
        p.box("Kit_GlowFoot", (face + 0.012, y - 0.006, 1.398), (face + 0.0135, y + 0.006, 1.402), panel=False)
    box_yz(p, "Kit_Graphite", 0.17, 1.39, 0.34, 1.41, face + 0.0135, 0.0015, bevel=0.0)
    face_label(p, "st_torque", 0.255, 1.4, face + 0.0135, scale=0.8)

    # --- round 2 (critic r1): the unit's marking, the extinguisher's label, screws, small plates, grime
    # the extinguisher's printed label wrapped round the sleeve: CO2, the type line, a red rule
    lr = 0.0425 * 1.3
    emboss_text(p, "Kit_Red", "CO2", 0.0, zf + 0.228, 0.0, 0.034, 0.0004, wrap=(ex, ey, lr))
    emboss_text(p, "Kit_Graphite", "FIRE EXTINGUISHER", 0.0, zf + 0.196, 0.0, 0.0105, 0.0003, wrap=(ex, ey, lr))
    emboss_text(p, "Kit_Graphite", "CLASS B  C  E  -  5 KG", 0.0, zf + 0.181, 0.0, 0.0075, 0.0003, wrap=(ex, ey, lr))
    p.lathe("Kit_Red", [(lr + 0.0002, zf + 0.168), (lr + 0.0005, zf + 0.1685), (lr + 0.0005, zf + 0.172), (lr + 0.0002, zf + 0.1725)],
            (ex, ey, 0.0), (0, 0, 1), seg=56)
    # the unit's name on the frame between the hatch and the niche, a pictogram plate on the hatch, the hatch's purpose
    box_yz(p, "Kit_Graphite", -0.475, 0.766, -0.245, 0.792, face + 0.0012, 0.0012, bevel=0.0)
    emboss_text(p, "Kit_Lacquer", "FIRE EXTINGUISHER UNIT", -0.36, 0.779, face + 0.0012, 0.0175, 0.0006)
    # the bracket's release: a red push button in a guard ring on the hatch, its stencil
    p.lathe("Kit_Graphite", [(0.017, 0.0), (0.017, 0.006), (0.0125, 0.008), (0.0115, 0.002), (0.0, 0.002)], (face + 0.008, -0.295, 0.69),
            (1, 0, 0), seg=28)
    p.lathe("Kit_Red", [(0.0105, 0.0), (0.0105, 0.006), (0.009, 0.0085), (0.0, 0.0092)], (face + 0.01, -0.295, 0.69), (1, 0, 0), seg=28)
    emboss_text(p, "Kit_Lacquer", "RELEASE", -0.295, 0.662, face + 0.008, 0.0105, 0.0004)
    box_yz(p, "Kit_Red", -0.395, 0.48, -0.325, 0.55, face + 0.0095, 0.0015, bevel=0.0008)
    for y0, z0, y1, z1 in ((-0.373, 0.492, -0.355, 0.527), (-0.37, 0.527, -0.358, 0.532), (-0.366, 0.532, -0.362, 0.537),
                           (-0.366, 0.537, -0.346, 0.540), (-0.351, 0.497, -0.347, 0.537), (-0.353, 0.49, -0.345, 0.497)):
        box_yz(p, "Kit_Lacquer", y0, z0, y1, z1, face + 0.0102, 0.0007, bevel=0.0)                 # the extinguisher glyph
    emboss_text(p, "Kit_Lacquer", "SPARE  CHARGE", -0.36, 0.44, face + 0.008, 0.017, 0.0005)
    # the lockers' numbers on the frame under each
    box_yz(p, "Kit_Graphite", -0.135, 0.82 - 0.0135, -0.005, 0.82 + 0.0135, face + 0.0012, 0.0012, bevel=0.0)
    emboss_text(p, "Kit_Lacquer", "LOCKER 01", -0.07, 0.82, face + 0.0012, 0.019, 0.0006)
    box_yz(p, "Kit_Graphite", -0.135, 0.085 - 0.0135, -0.005, 0.085 + 0.0135, face + 0.0012, 0.0012, bevel=0.0)
    emboss_text(p, "Kit_Lacquer", "LOCKER 02", -0.07, 0.085, face + 0.0012, 0.019, 0.0006)
    # screws round the openings and on the cells' corners
    screws = [(-0.478, 0.81), (-0.242, 0.81), (-0.478, 1.49), (-0.242, 1.49), (-0.215, 0.17), (0.075, 0.17), (-0.215, 1.47), (0.075, 1.47),
              (-0.215, 0.79), (0.075, 0.79), (-0.215, 0.85), (0.075, 0.85), (0.1, 0.03), (0.48, 0.03), (0.1, 1.08), (0.48, 1.08),
              (-0.478, 0.03), (-0.242, 0.03), (-0.215, 0.03), (0.075, 0.03)]
    for y, z in screws:
        p.lathe("Kit_Lip", [(0.0042, 0.0), (0.0042, 0.0006), (0.0, 0.0009)], (face, y, z), (1, 0, 0), seg=16)
        p.box("Kit_Graphite", (face + 0.0007, y - 0.0028, z - 0.0005), (face + 0.001, y + 0.0028, z + 0.0005), panel=False)
    # seams: a vertical service line in the cover column, a horizontal one under the hatch
    box_yz(p, "Kit_Graphite", 0.093, 0.02, 0.0955, 1.69, face + 0.0003, 0.0006, bevel=0.0)
    box_yz(p, "Kit_Graphite", -0.483, 0.155, -0.237, 0.1575, face + 0.0003, 0.0006, bevel=0.0)
    # small plates: an inspection tag by the hatch, a pressure tag by the niche
    box_yz(p, "Kit_Lip", -0.47, 0.03, -0.39, 0.06, face + 0.0012, 0.0012, bevel=0.0004)
    emboss_text(p, "Kit_Graphite", "INSP 03-2949", -0.43, 0.045, face + 0.0012, 0.0085, 0.0003)
    # the dirt where it forms: the bay's foot, under the lockers' sills and the cover's pull, round the cradle
    for y, w in ((-0.36, 0.24), (-0.07, 0.3), (0.29, 0.38)):
        p.grime("rim", (face + 0.001, y, 0.07), (1, 0, 0), (0, 0, 1), (w, 0.12), 0.7)
    for z in (0.17, 0.85):
        p.grime("smear", (face + 0.001, -0.07, z - 0.02), (1, 0, 0), (0, 0, 1), (0.22, 0.06), 0.5)
    p.grime("streaks", (cf + 0.001, 0.29, 0.22), (1, 0, 0), (0, 0, 1), (0.14, 0.1), 0.45)
    p.grime("rim", (face + 0.001, -0.36, 0.8), (1, 0, 0), (0, 0, 1), (0.22, 0.05), 0.5)
    p.grime("smear", (cf + 0.001, 0.29, 0.72), (1, 0, 0), (0, 0, 1), (0.22, 0.09), 0.3)
    p.grime("smear", (cf + 0.001, 0.29, 0.3), (1, 0, 0), (0, 0, 1), (0.2, 0.12), 0.45)
    for y in (0.16, 0.42):
        p.grime("smear", (cf + 0.001, y, 0.61), (1, 0, 0), (0, 0, 1), (0.05, 0.14), 0.45)
    p.grime("rim", (face + 0.001, 0.29, 0.17), (1, 0, 0), (0, 0, 1), (0.36, 0.05), 0.6)
    # over B and C: louvers and a slot row
    for k in range(6):
        z = 1.52 + k * 0.026
        p.box("Kit_Graphite", (face - 0.005, -0.21, z), (face + 0.012, 0.47, z + 0.012), bevel=0.002, segments=1)
    box_yz(p, "Kit_Graphite", -0.215, 1.505, 0.475, 1.68, face - 0.004, 0.02)
    # bolts on the frame
    for y in (-0.47, 0.47):
        for z in (0.06, 1.62):
            p.tube("Kit_Lip", (D - 0.03, y, z), (D - 0.026, y, z), 0.007, 12)
    # the information layer
    lab = lambda item, y, z, x, sc=1.0, rot=0.0, lb=True: face_label(p, item, y, z, x, scale=sc, label=lb, rot=rot)  # noqa: E731
    # SC's cover carries the maker's mark large and embossed, the bay's name small under it (author's capture)
    emboss_text(p, "Kit_Shell", "HALCYON", 0.29, 0.72, face + 0.036, 0.05, 0.0025, bevel=0.0005)
    emboss_text(p, "Kit_Shell", "COMPONENT  BAY", 0.29, 0.585, face + 0.036, 0.022, 0.0008)
    lab("plate_cooler", 0.29, 0.38, face + 0.0365, 0.7)
    lab("red_marker", -0.36, 0.3, face + 0.0085, 2.2)
    lab("st_inspect", -0.36, 0.1, face, 0.8)
    lab("hazard_subtle", -0.36, 1.58, face + 0.01, 0.55)
    lab("st_gnd", 0.29, 0.1, face, 0.8)
    p.collision_box((0.0, -W / 2, 0.0), (D, W / 2, H))
    return p


def part_name_any(cat, part, size, sec, var):
    return kit_portal.part_name(cat, part, size, sec, var) if cat not in ("Test", "Terminal", "Bay", "Cockpit") else part_name(cat, part, size, sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    if cat == "Test":
        return test_shell(part_name(cat, part, size, sec_key, var), seed)
    if cat == "Terminal":
        return terminal_housing(part_name(cat, part, size, sec_key, var), seed)
    if cat == "Bay":
        return bay_service(part_name(cat, part, size, sec_key, var), seed)
    if cat == "Cockpit":
        if part == "SeatBack":
            import kit_cockpit_v3
            return kit_cockpit_v3.seat_back(part_name(cat, part, size, sec_key, var), seed)
        if part in ("SeatArm", "ConsoleWall"):          # cockpit v3 (kit_cockpit_v3.py)
            import kit_cockpit_v3
            fn = kit_cockpit_v3.seat_arm if part == "SeatArm" else kit_cockpit_v3.wall_console
            return fn(part_name(cat, part, size, sec_key, var), seed, mirror=var == "R")
        if var in ("B", "BR"):                  # variant B after the 2D concept (Docs/Kit/parts/KF-COCKPIT-CONSOLE); BR its mirror
            import kit_cockpit_b
            return kit_cockpit_b.console_b(part_name(cat, part, size, sec_key, var), seed, mirror=var == "BR")
        import kit_cockpit
        return kit_cockpit.console(part_name(cat, part, size, sec_key, var), seed)
    return kit_portal.build_part(cat, part, size, sec_key, var, seed)
