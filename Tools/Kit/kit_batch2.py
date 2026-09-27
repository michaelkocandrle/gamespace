"""Batch 2 of the interior kit (kit_parts.json batch 2, 27. 9. 2026): portal rings, ceiling panels and open ceiling
bays with trays, corridor end walls, the narrowing into a service crawlway, the N -> W transition and the inner and
outer corners. The same design language as the wall modules (Tools/Kit/kit_walls.py): the structure layer in the
palette's lighter painted metal, pressed panels in the dark primary, housed light strips with one linear light each.

Frames (kit_rules.json pivots):
  run     Portal, Ceiling, the transition: origin at the module start on the section centreline at floor level,
          +X along the run, +Y to the left, +Z up; the section's panel faces at y = +-width / 2.
  wall    End, Narrow: origin at the bottom corner on the face plane, face +X, width along +Y (0..W).
  corner  inner: where the two face planes meet at the floor, the room in +X +Y (walls on x = 0 and y = 0).
          outer: the convex edge at the floor; the walls run along -Y (face +X) and -X (face +Y), the part fills
          the quadrant +X +Y above the walls' break (the hip where the two slopes meet) and guards the edge.

A corner needs no wall halves: two wall modules that start at the same inner corner overlap over the slope inset,
and their slopes intersect in the valley on their own (the lower slope is the visible one). The corner part covers
the seam - a post and a valley beam (A) or a 45 deg chamfer panel (B).
"""
import math
import random
import zlib

from mathutils import Vector

import kit_geo
from kit_geo import frame

G = 0.006
GAP = 0.012
PT = 0.025
BEV_MID, BEV_SMALL = 0.007, 0.003
SQ = math.sqrt(0.5)
PANEL_IDS = ["panel_A12", "panel_A14", "panel_B03", "panel_B07", "panel_C21", "panel_C22", "panel_D05", "panel_E11",
             "panel_F02", "panel_G08", "panel_H19"]


class Section:
    def __init__(self, key):
        s = kit_geo.RULES["sections"][key]
        self.key = key
        self.width, self.ceiling = s["width"], s["ceiling"]
        self.vt, self.rise = s["vertical_to"], s["slope_rise"]
        self.top = self.vt + self.rise
        self.xt = 0.75 * self.rise
        self.half = self.width / 2
        self.protrusion = s["portal_protrusion"]
        # the ceiling spans between the walls' cove fascias (kit_walls: fascia face at inset xt - 0.125), 2 cm behind
        self.ceil_half = self.half - (self.xt - 0.125) + 0.02

    def inner(self, d):
        """The section's inner outline offset d into the room, (y, z) from the left floor corner over the top to the
        right one: the vertical leg, the slope line (3:4) and the ceiling - the cove is inside the offset slope line."""
        h, vt = self.half, self.vt
        sy, sz = h - 0.8 * d, vt - 0.6 * d
        t1 = (sy - (h - d)) / 0.6
        p1 = (h - d, sz + 0.8 * t1)
        t2 = (self.ceiling - d - sz) / 0.8
        p2 = (max(0.05, sy - 0.6 * t2), self.ceiling - d)
        return [(h - d, 0.0), p1, p2, (-p2[0], p2[1]), (-p1[0], p1[1]), (-(h - d), 0.0)]


def strip_light(p, name, c, direction, width, height, role, cd, radius_m):
    """A linear fixture's light: a rect light facing `direction` (part coords), `width` along the socket's Y."""
    d = Vector(direction).normalized()
    p.socket(name, tuple(c), x=tuple(d), z=_perp(d), type="rect", role=role, cd=round(cd, 3),
             width_cm=round(width * 100, 1), height_cm=round(height * 100, 1), radius_m=radius_m,
             dir_ue=[round(d.x, 4), round(-d.y, 4), round(d.z, 4)], megalights_shadow=True)


def strip_light_along(p, name, c, direction, along, width, height, role, cd, radius_m):
    """The same with the strip's long axis given (part coords): the import turns the light to it."""
    d, a = Vector(direction).normalized(), Vector(along).normalized()
    p.socket(name, tuple(c), x=tuple(d), z=tuple(d.cross(a).normalized()), type="rect", role=role, cd=round(cd, 3),
             width_cm=round(width * 100, 1), height_cm=round(height * 100, 1), radius_m=radius_m,
             dir_ue=[round(d.x, 4), round(-d.y, 4), round(d.z, 4)], along_ue=[round(a.x, 4), round(-a.y, 4), round(a.z, 4)],
             megalights_shadow=True)


def _perp(d):
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    return tuple(d.cross(ref).normalized())


def seg_frame(a, b, room, x0=0.0, vertical_plane=True):
    """A frame on a segment a -> b of an outline in the YZ plane (portal arches, crawlway frames): local x along the
    segment, local y along -X, local z the in-plane normal toward `room` (a (y, z) point)."""
    dy, dz = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dy, dz)
    dy, dz = dy / ln, dz / ln
    n = (-dz, dy)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if n[0] * (room[0] - mid[0]) + n[1] * (room[1] - mid[1]) < 0:
        n = (dz, -dy)
    # right-handed: x = (0, dy, dz), z = (0, n), y = z x x
    xv = Vector((0, dy, dz))
    zv = Vector((0, n[0], n[1]))
    yv = zv.cross(xv)
    return frame((x0, a[0], a[1]), xv, yv, zv), ln


def seg_frame_wall(a, b, room):
    """The same on a wall's face plane (YZ at x = 0, face +X): local z = +X, local x along the segment."""
    dy, dz = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dy, dz)
    xv = Vector((0, dy / ln, dz / ln))
    zv = Vector((1, 0, 0))
    yv = zv.cross(xv)
    # yv points to one side of the segment in the face plane: make it point toward `room` (the opening)
    mid = Vector((0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    if yv.dot(Vector((0, room[0], room[1])) - mid) < 0:
        xv = -xv
        yv = zv.cross(xv)
        return frame((0, b[0], b[1]), xv, yv, zv), ln
    return frame((0, a[0], a[1]), xv, yv, zv), ln


def frame_hole(p, role, m, u0, u1, v0, v1, hole, thick=PT, bevel=BEV_MID, secondary=False, proud=0.0):
    hu0, hu1, hv0, hv1 = hole
    if hu0 - u0 > 0.01:
        p.slab(role, m, u0, hu0, v0, v1, thick, bevel, secondary=secondary, proud=proud)
    if u1 - hu1 > 0.01:
        p.slab(role, m, hu1, u1, v0, v1, thick, bevel, secondary=secondary, proud=proud)
    if hv0 - v0 > 0.01:
        p.slab(role, m, max(u0, hu0), min(u1, hu1), v0, hv0, thick, bevel, secondary=secondary, proud=proud)
    if v1 - hv1 > 0.01:
        p.slab(role, m, max(u0, hu0), min(u1, hu1), hv1, v1, thick, bevel, secondary=secondary, proud=proud)


def frame_ring(p, m, hole, t=0.025, proud=0.012, role="Kit_Structure"):
    hu0, hu1, hv0, hv1 = hole
    for (a0, a1, b0, b1) in ((hu0 - t, hu0, hv0 - t, hv1 + t), (hu1, hu1 + t, hv0 - t, hv1 + t), (hu0, hu1, hv0 - t, hv0), (hu0, hu1, hv1, hv1 + t)):
        p.slab(role, m, a0, a1, b0, b1, 0.03, BEV_SMALL, proud=proud, panel=False)


def gasket(p, m, hole, t=0.006):
    hu0, hu1, hv0, hv1 = hole
    for (a0, a1, b0, b1) in ((hu0, hu0 + t, hv0, hv1), (hu1 - t, hu1, hv0, hv1), (hu0 + t, hu1 - t, hv0, hv0 + t), (hu0 + t, hu1 - t, hv1 - t, hv1)):
        p.slab("Kit_Rubber", m, a0, a1, b0, b1, 0.02, proud=0.004, panel=False)


def pressed(p, m, u0, u1, v0, v1, secondary=False, proud=0.0):
    if min(u1 - u0, v1 - v0) > 0.2:
        p.slab("Kit_Primary", m, u0, u1, v0, v1, PT + proud, BEV_MID, secondary=secondary, inset=(0.04, 0.006), proud=proud)
    else:
        p.slab("Kit_Primary", m, u0, u1, v0, v1, PT + proud, BEV_MID, secondary=secondary, proud=proud)


def label(p, item, at, normal, xdir, ydir, scale=1.0, is_label=False):
    """A decal shot at a surface point from 8 cm in front along its normal (kit_walls.Wall.label)."""
    at, n = Vector(at), Vector(normal).normalized()
    p.decal(item, at + n * 0.08, at - n * 0.02, scale=scale, frame_xy=[list(Vector(xdir).normalized()), list(Vector(ydir).normalized())],
            label=is_label)


# =============================================================================== portal rings
def portal(sec, var, name, seed):
    """A structural frame around the whole section, 0.3 m of the run: a dark collar 3.5 cm off the walls over the
    full depth, the frame proper protruding `portal_protrusion` over the middle, bolted. A: a lit inner ring (a
    housed warm strip along the frame's inner face, one linear light under the head). B: a hazard band on both legs
    and a frame number plate. C: a deeper, heavier frame with the wall pipe run passing through its legs."""
    p = kit_geo.Part(name, seed)
    rng = random.Random(seed)
    L = 0.3
    h, C = sec.half, sec.ceiling
    outer = [(-(h + 0.2), 0.0), (-(h + 0.2), C + 0.25), (h + 0.2, C + 0.25), (h + 0.2, 0.0)]
    # N B: the heavy bulkhead frame where a W corridor narrows into N (author 27. 9.: "the section change must be
    # the heaviest frame, not the lightest" - critic): 26 cm deep, stepped collars on both faces, the lit ring
    # of A, a hazard band on the header; the clear width stays passable (1.0 m)
    heavy = sec.key == "N" and var == "B"

    def prism(role, d, x0, x1, bevel=0.0):
        m = frame((x1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))
        p.poly_prism(role, sec.inner(d) + outer, m, x1 - x0, bevel=bevel, segments=1, panel=False)

    prism("Kit_Primary", 0.035, G, L - G)
    d2 = sec.protrusion + (0.03 if var == "C" else 0.02 if heavy else 0.0)
    x0, x1 = (0.03, 0.27) if var == "C" else (0.02, 0.28) if heavy else (0.06, 0.24)
    # the frame proper, its edges chamfered (they carry the edge wear)
    prism("Kit_Structure", d2, x0, x1, bevel=0.014 if heavy else 0.01)
    if heavy:
        # a stepped collar on each face: the frame reads in layers from both corridors
        prism("Kit_Structure", d2 - 0.035, x0 - 0.016, x0, bevel=0.006)
        prism("Kit_Structure", d2 - 0.035, x1, x1 + 0.016, bevel=0.006)
    arch = sec.inner(d2)
    room = (0.0, C * 0.5)
    xc0 = (x0 + x1) / 2
    if var == "C":
        # a ridge round the heavy frame's inner face (A carries its light strip there, B its hazard bands)
        prism("Kit_Structure", d2 + 0.016, xc0 - 0.022, xc0 + 0.022, bevel=0.004)
    # gusset plates on both faces at the knees (leg to slope, slope to head), foot plates at the legs
    p1, p2 = arch[1], arch[2]
    g = 0.22
    knees = [[(h - d2, p1[1] - g), p1, (p1[0] - 0.6 * g, p1[1] + 0.8 * g), (h + 0.02, p1[1] + 0.12), (h + 0.02, p1[1] - g)],
             [(p2[0] + 0.6 * g, p2[1] - 0.8 * g), p2, (p2[0] - g, p2[1]), (p2[0] - g, C + 0.02), (p2[0] + 0.25, C + 0.02)]]
    for pts in knees:
        for sgn in (1, -1):
            poly = [(sgn * y, z) for (y, z) in pts]
            if sgn < 0:
                poly.reverse()
            p.poly_prism("Kit_Structure", poly, frame((x1 + 0.012, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), 0.014, panel=False)
            p.poly_prism("Kit_Structure", [(-y, z) for (y, z) in reversed(poly)], frame((x0 - 0.012, 0, 0), (0, -1, 0), (0, 0, 1), (-1, 0, 0)), 0.014, panel=False)
    for sgn in (1, -1):
        ya, yb = sorted((sgn * (h - d2 - 0.025), sgn * (h + 0.01)))
        p.box("Kit_Structure", (x0 - 0.025, ya, 0.0), (x1 + 0.025, yb, 0.09), bevel=0.006, segments=1)
        for xb in (x0 - 0.025, x1 + 0.025):
            for yy in (sgn * (h - d2 + 0.005), sgn * (h - 0.03)):
                dd = -1 if xb < x0 else 1
                p.tube("Kit_Structure", (xb, yy, 0.05), (xb + dd * 0.005, yy, 0.05), 0.008, 6)
    # bolt heads on both faces of the frame, on the band between the frame's inner edge and the collar
    mid = sec.inner((d2 + 0.035) / 2)
    pts = []
    for (a, b) in zip(mid[:-1], mid[1:]):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(ln / 0.32))
        for k in range(n):
            t = (k + 0.5) / n
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    for (y, z) in pts:
        if z < 0.15:
            continue
        for xf, sgn in ((x1, 1), (x0, -1)):
            p.tube("Kit_Structure", (xf, y, z), (xf + sgn * 0.005, y, z), 0.0075, 6)
    xc = (x0 + x1) / 2
    # the frame number: one plate per frame on the left leg at eye height, light text on a dark plate, the
    # largest the leg's face takes (6-8 cm letters); the number goes by variant until the signage batch gives
    # every frame in a layout its own (SOCKET_Decal_Section) - "four codes on two metres, 1 cm high" (critic)
    fw = x1 - x0
    m = frame((0, h - d2, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0))
    lift = 0.028 if var == "C" else 0.008             # on C the plate stands on the ridge
    # (the leg's vertical face ends at the knee, 1.27 m in W: a plate higher up sat inside the frame)
    zp0, zp1 = 0.98, 1.14
    p.slab("Kit_Plastic", m, x0 + 0.004, x1 - 0.004, zp0, zp1, 0.012, BEV_SMALL, proud=lift, panel=False)
    number = {"A": "panel_F02", "B": "panel_G08", "C": "panel_H19"}[var] if sec.key == "W" else "panel_C21"
    label(p, number, (xc, h - d2 - lift, (zp0 + zp1) / 2), (0, -1, 0), (1, 0, 0), (0, 0, 1), min(1.6, (fw - 0.012) / 0.14))
    p.socket("Decal_Section", (xc, h - d2 - lift - 0.001, (zp0 + zp1) / 2), x=(0, -1, 0), z=(0, 0, 1), tag="section_number")
    if var == "A" or heavy:
        # the lit ring over the slopes and the head only (no strip down the legs - critic): a diffuser set 7 mm
        # down in a channel between two lips, a cap at each end, one linear light under the head
        segs = list(zip(arch[:-1], arch[1:]))[1:-1]
        for i, (a, b) in enumerate(segs):
            m, ln = seg_frame(a, b, room, xc)
            p.slab("Kit_GlowWarm", m, 0.0, ln, -0.013, 0.013, 0.006, proud=0.003, panel=False)
            for (v0, v1) in ((-0.026, -0.013), (0.013, 0.026)):
                p.slab("Kit_Structure", m, -0.01, ln + 0.01, v0, v1, 0.014, BEV_SMALL, segments=1, proud=0.01, panel=False)
            if i in (0, len(segs) - 1):
                u = 0.0 if i == 0 else ln - 0.03
                p.slab("Kit_Structure", m, u, u + 0.03, -0.026, 0.026, 0.014, BEV_SMALL, segments=1, proud=0.011, panel=False)
        p2 = arch[2]
        strip_light(p, "Light_Ring_0", (xc, 0.0, C - d2 - 0.02), (0, 0, -1), 2 * p2[0] - 0.06, 0.024, "warm", 1.0, 2.4)
        if heavy:
            # the hazard band across the header, on the W-side collar (its visible band under the ceiling line)
            label(p, "hazard_stripe", (x0 - 0.016, 0.0, C - (d2 - 0.035) / 2), (-1, 0, 0), (0, -1, 0), (0, 0, 1), 0.85)
    elif var == "B":
        # a hatched hazard band up both legs, 0.3-0.9 m, 7 cm wide, under the number plate
        for sgn in (1, -1):
            y = sgn * (h - d2)
            # (x cross y = the face normal on both legs: the left band's frame was mirrored and it was not drawn)
            label(p, "hazard_stripe", (xc, y, 0.6), (0, -sgn, 0), (0, 0, 1), (-sgn, 0, 0), 1.2)
    else:
        # the open ceiling bay's services pass through the frame's head (Ceiling_Tray B: the duct and the pipe at
        # the same place), flanged on both faces of the frame (the leg pipes of round 1 hid inside the frame)
        yd0, yd1, zd0, zd1 = -0.34, -0.06, C - 0.06, C + 0.07
        yp, zp, rp = 0.16, C - 0.01, 0.045
        p.box("Kit_Structure", (0.0, yd0, zd0), (L, yd1, zd1), bevel=BEV_SMALL, segments=1)
        p.tube("Kit_Structure", (0.0, yp, zp), (L, yp, zp), rp, 18, caps=False)
        for xf, dd in ((x0, -1), (x1, 1)):
            xa, xb = sorted((xf, xf + dd * 0.018))
            p.box("Kit_Structure", (xa, yd0 - 0.022, zd0 - 0.022), (xb, yd1 + 0.022, zd1 + 0.022), bevel=0.003, segments=1)
            p.tube("Kit_Structure", (xf, yp, zp), (xf + dd * 0.018, yp, zp), rp + 0.02, 18)
            for k in range(6):
                t = 2 * math.pi * k / 6
                c = (xf + dd * 0.018, yp + (rp + 0.013) * math.cos(t), zp + (rp + 0.013) * math.sin(t))
                p.tube("Kit_Structure", c, (c[0] + dd * 0.006, c[1], c[2]), 0.005, 6)
    # collision: the legs, the slope corners and the head
    for sgn in (1, -1):
        p.collision_box((0.0, min(sgn * (h - d2), sgn * (h + 0.05)), 0.0), (L, max(sgn * (h - d2), sgn * (h + 0.05)), p1[1]))
        p.collision_hull([(x, sgn * y, z) for x in (0.0, L) for (y, z) in (p1, (h + 0.05, p1[1]), (h + 0.05, C), (p2[0], C - d2))])
    p.collision_box((0.0, -p2[0], C - d2), (L, p2[0], C))
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== ceiling
def _ceiling_frame(sec):
    # local x along the run, local y across (world -Y), local z down: slabs face the corridor below
    return frame((0, 0, sec.ceiling), (1, 0, 0), (0, -1, 0), (0, 0, -1))


def ceiling_panel(sec, var, L, name, seed):
    """Ceiling panels between the walls' cove fascias, 0.3 / 0.6 / 1.2 m of the run: a dark backing, three pressed
    strips across (side strips 0.3 m), half a transverse beam at each end (the frame rhythm carried over the
    ceiling). A: a round down-light (the corridor's work light; a 0.3 m module is a plain filler). B: a square vent
    diffuser. C: a housed linear light along the run."""
    p = kit_geo.Part(name, seed)
    C, w = sec.ceiling, sec.ceil_half
    M = _ceiling_frame(sec)
    p.slab("Kit_Seal", M, 0, L, -w, w, 0.01, proud=-0.07, panel=False)
    side = min(0.3, w * 0.35)
    strips = [(-w, -w + side - GAP / 2), (-w + side + GAP / 2, w - side - GAP / 2), (w - side + GAP / 2, w)]
    hole = None
    if var == "B":
        s = min(0.45, 2 * (w - side) - 0.12)
        hole = (L / 2 - s / 2, L / 2 + s / 2, -s / 2, s / 2)
    elif var == "A" and L >= 0.5:
        hole = (L / 2 - 0.12, L / 2 + 0.12, -0.12, 0.12)
    elif var == "C":
        hole = (0.1, L - 0.1, -0.055, 0.055)
    for k, (v0, v1) in enumerate(strips):
        if k == 1 and hole:
            frame_hole(p, "Kit_Primary", M, G, L - G, v0, v1, hole)
        else:
            pressed(p, M, G, L - G, v0, v1)
    for (u0, u1) in ((0.0, 0.065), (L - 0.065, L)):
        p.slab("Kit_Structure", M, u0, u1, -w, w, 0.045, proud=0.04, panel=False)
    if var == "A" and L >= 0.5:
        # a recessed square down-light: a trim frame, a dark reflector well 6 cm up, the lens at its top behind a
        # two-blade louvre ("flat household lamps" - critic)
        c = (L / 2, 0.0)
        p.box("Kit_Seal", (c[0] - 0.12, -0.12, C + 0.058), (c[0] + 0.12, 0.12, C + 0.064), panel=False)
        for (a0, a1, b0, b1) in ((-0.12, -0.11, -0.12, 0.12), (0.11, 0.12, -0.12, 0.12), (-0.11, 0.11, -0.12, -0.11), (-0.11, 0.11, 0.11, 0.12)):
            p.box("Kit_Seal", (c[0] + a0, b0, C), (c[0] + a1, b1, C + 0.06), panel=False)
        p.box("Kit_GlowWarm", (c[0] - 0.08, -0.08, C + 0.052), (c[0] + 0.08, 0.08, C + 0.058), panel=False)
        for v in (-0.04, 0.04):
            p.box("Kit_Structure", (c[0] - 0.11, v - 0.004, C + 0.012), (c[0] + 0.11, v + 0.004, C + 0.05), panel=False)
        frame_ring(p, M, hole, t=0.03, proud=0.016)
        p.socket("Light_Down_0", (c[0], c[1], C - 0.05), x=(0, 0, -1), z=(1, 0, 0), type="spot", role="work",
                 cd=35.0 if L >= 1.0 else 22.0, cone_deg=100.0, radius_m=3.6, source_radius_cm=6.0, megalights_shadow=True)
    elif var == "B":
        # the diffuser: a framed opening, a linear bar grille over a dark plenum - the bars' sides catch the
        # corridor light from any angle (a perforated face read as a black hole seen from along the run)
        p.slab("Kit_Seal", M, hole[0], hole[1], hole[2], hole[3], 0.01, proud=-0.06, panel=False)
        n_bars = int((hole[1] - hole[0] - 0.03) / 0.034)
        for k in range(n_bars):
            u = hole[0] + 0.015 + (k + 0.5) * (hole[1] - hole[0] - 0.03) / n_bars
            p.slab("Kit_Structure", M, u - 0.004, u + 0.004, hole[2] + 0.008, hole[3] - 0.008, 0.036, proud=-0.006, panel=False)
        for v in (-0.25 * (hole[3] - hole[2]), 0.25 * (hole[3] - hole[2])):
            p.slab("Kit_Structure", M, hole[0] + 0.01, hole[1] - 0.01, v - 0.004, v + 0.004, 0.012, proud=-0.03, panel=False)
        frame_ring(p, M, hole, t=0.028, proud=0.014)
        gasket(p, M, hole)
    elif var == "C":
        # a recessed linear fixture: the channel 4 cm up, a diffuser in it, a trim frame round the slot
        u0, u1 = hole[0], hole[1]
        p.slab("Kit_Seal", M, u0, u1, -0.055, 0.055, 0.006, proud=-0.045, panel=False)
        for (v0, v1) in ((-0.055, -0.045), (0.045, 0.055)):
            p.slab("Kit_Seal", M, u0, u1, v0, v1, 0.045, proud=0.0, panel=False)
        p.slab("Kit_GlowWarm", M, u0 + 0.01, u1 - 0.01, -0.038, 0.038, 0.004, proud=-0.03, panel=False)
        # cross louvres in the channel every 8 cm: the diffuser reads as a fixture, not a white plate (critic r2)
        n_l = int((u1 - u0 - 0.02) / 0.08)
        for k in range(1, n_l):
            u = u0 + 0.01 + k * (u1 - u0 - 0.02) / n_l
            p.slab("Kit_Structure", M, u - 0.003, u + 0.003, -0.045, 0.045, 0.026, proud=-0.002, panel=False)
        frame_ring(p, M, hole, t=0.02, proud=0.014)
        strip_light_along(p, "Light_Linear_0", (L / 2, 0.0, C - 0.02), (0, 0, -1), (1, 0, 0), u1 - u0 - 0.04, 0.05, "work", 32.0 * L, 3.6)
    p.collision_box((0, -w, C), (L, w, C + 0.2))
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


def ceiling_tray(sec, var, L, name, seed):
    """An open ceiling bay (services exposed, the SC industrial look): a dark backing 16 cm above the ceiling line,
    transverse joists continuing the frames, and what the bay carries, hung from the joists just under the line.
    A: an open cable tray with bundles. B: a rectangular duct with flange bands and a colour-coded pipe."""
    p = kit_geo.Part(name, seed)
    rng = random.Random(zlib.crc32(name.encode()))
    C, w = sec.ceiling, sec.ceil_half
    top = C + 0.2
    # the bay's back and sides in the dark primary, not black: the structure has to read in it ("a hole into the
    # void" - critic); a cool service strip along the back
    p.box("Kit_Primary", (0, -w, top), (L, w, top + 0.01), panel=True)
    for sgn in (1, -1):
        p.box("Kit_Primary", (0, min(sgn * w, sgn * (w + 0.01)), C), (L, max(sgn * w, sgn * (w + 0.01)), top), panel=True)
    p.box("Kit_GlowCool", (0.04, -0.012, top - 0.004), (L - 0.04, 0.012, top), panel=False)
    joists = [(0.0, 0.032), (L - 0.032, L)] + [(u - 0.025, u + 0.025) for u in ([0.3, 0.9] if L > 1.0 else [L / 2])]
    for (u0, u1) in joists:
        p.box("Kit_Structure", (u0, -w, C - 0.002), (u1, w, top), bevel=BEV_SMALL, segments=1)
    hangs = [(a + b) / 2 for (a, b) in joists[2:]]
    # a linear fixture hung from the joists beside the services (the bays were unlit)
    yf = 0.45
    f0, f1 = (0.2, L - 0.2) if L > 1.0 else (0.1, L - 0.1)
    zf = C - 0.03
    p.box("Kit_Structure", (f0, yf - 0.04, zf), (f1, yf + 0.04, zf + 0.045), bevel=BEV_SMALL, segments=1)
    p.box("Kit_GlowWarm", (f0 + 0.015, yf - 0.026, zf - 0.003), (f1 - 0.015, yf + 0.026, zf), panel=False)
    # side lips and cross louvres every 8 cm under the diffuser (critic r2: "a glued-on white plate")
    for (ya, yb) in ((yf - 0.04, yf - 0.026), (yf + 0.026, yf + 0.04)):
        p.box("Kit_Structure", (f0, ya, zf - 0.016), (f1, yb, zf), panel=False)
    n_l = int((f1 - f0 - 0.03) / 0.08)
    for k in range(1, n_l):
        u = f0 + 0.015 + k * (f1 - f0 - 0.03) / n_l
        p.box("Kit_Structure", (u - 0.003, yf - 0.026, zf - 0.014), (u + 0.003, yf + 0.026, zf - 0.003), panel=False)
    for u in hangs:
        if f0 < u < f1:
            p.tube("Kit_Structure", (u, yf, zf + 0.045), (u, yf, top), 0.006, 6)
    strip_light_along(p, "Light_Linear_0", ((f0 + f1) / 2, yf, zf - 0.02), (0, 0, -1), (1, 0, 0), f1 - f0 - 0.04, 0.05, "work", 26.0 * (f1 - f0), 3.4)
    if var == "A":
        z0 = C - 0.05                           # the tray plate
        y0, y1 = -0.17, 0.17
        p.box("Kit_Structure", (0, y0, z0 - 0.006), (L, y1, z0), panel=False)
        for y in (y0, y1 - 0.005):
            p.box("Kit_Structure", (0, y, z0 - 0.006), (L, y + 0.005, z0 + 0.045), panel=False)
        for u in hangs:
            for y in (y0 + 0.02, y1 - 0.02):
                p.tube("Kit_Structure", (u, y, z0), (u, y, C), 0.006, 6)
            p.box("Kit_Structure", (u - 0.015, y0 - 0.01, z0 - 0.014), (u + 0.015, y1 + 0.01, z0 - 0.006), panel=False)
        # bundles lying in the tray (black) and one cream data line
        ys = [-0.12, -0.085, -0.045, 0.0, 0.05, 0.1]
        for k, y in enumerate(ys):
            r = rng.choice([0.012, 0.014, 0.016]) if k != 3 else 0.009
            role = "Kit_Accent" if k == 3 else "Kit_Rubber"
            p.tube(role, (0, y, z0 + r), (L, y, z0 + r), r, 10, caps=False)
        for u in hangs:
            p.tube("Kit_Signal", (u + 0.1, -0.14, z0 + 0.018), (u + 0.1, 0.13, z0 + 0.018), 0.004, 6)
    else:
        # the duct: 0.28 x 0.13, flange bands at the joists
        y0, y1, z0, z1 = -0.34, -0.06, C - 0.06, C + 0.07
        p.box("Kit_Structure", (0, y0, z0), (L, y1, z1), bevel=BEV_SMALL, segments=1)
        for u in hangs:
            p.box("Kit_Structure", (u - 0.012, y0 - 0.008, z0 - 0.008), (u + 0.012, y1 + 0.008, z1 + 0.008), bevel=0.002, segments=1)
            p.tube("Kit_Structure", (u, (y0 + y1) / 2, z1), (u, (y0 + y1) / 2, top), 0.008, 6)
        # the pipe: r 45 mm, clamped to the joists, a colour code band
        yp, zp, r = 0.16, C - 0.01, 0.045
        p.tube("Kit_Structure", (0, yp, zp), (L, yp, zp), r, 18, caps=False)
        for u in hangs:
            p.tube("Kit_Structure", (u - 0.014, yp, zp), (u + 0.014, yp, zp), r + 0.007, 18)
            p.tube("Kit_Structure", (u, yp, zp + r), (u, yp, top), 0.007, 6)
        uc = L / 2 + (0.12 if L > 1.0 else 0.0)
        p.tube("Kit_Accent", (uc - 0.02, yp, zp), (uc + 0.02, yp, zp), r + 0.0015, 18, caps=False)
        for uu in (uc - 0.026, uc + 0.026):
            p.tube("Kit_Signal", (uu - 0.004, yp, zp), (uu + 0.004, yp, zp), r + 0.002, 18, caps=False)
        label(p, rng.choice(["label_coolant", "label_hydraulic"]), (L / 2 - 0.25, (y0 + y1) / 2, z0), (0, 0, -1), (1, 0, 0), (0, -1, 0), 0.9)
    p.collision_box((0, -w, C - 0.08), (L, w, top))
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== end walls and the crawlway
FACE = frame((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))            # local x -> +Y, local y -> +Z, normal +X
PLINTH = frame((-0.1, 0, 0), (0, 1, 0), (SQ, 0, SQ), (SQ, 0, -SQ))


def _outline(sec):
    W, vt, top, xt, C = sec.width, sec.vt, sec.top, sec.xt, sec.ceiling
    return [(0, 0), (W, 0), (W, vt), (W - xt, top), (W - xt + 0.14, top), (W - xt + 0.14, C), (xt - 0.14, C), (xt - 0.14, top), (xt, top), (0, vt)]


def _end_base(p, sec, spans, back_x=-0.07, hole=None):
    """What every end wall has: the dark backing, the plinth (recess, housed cool strip, one linear light) and the
    kick panel over `spans` (y ranges), the rail with its signal line at the break. hole (y0, y1, z0, z1): an
    opening in the backing under the break (a window that looks out)."""
    W, vt = sec.width, sec.vt
    back = frame((back_x, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))
    if hole:
        y0, y1, z0, z1 = hole
        outline = _outline(sec)
        for poly in ([(0, 0), (W, 0), (W, z0), (0, z0)], [(0, z0), (y0, z0), (y0, z1), (0, z1)],
                     [(y1, z0), (W, z0), (W, z1), (y1, z1)], [(0, z1), (W, z1)] + outline[2:]):
            p.poly_prism("Kit_Seal", poly, back, 0.01, panel=False)
    else:
        p.poly_prism("Kit_Seal", _outline(sec), back, 0.01, panel=False)
    for k, (a, b) in enumerate(spans):
        p.slab("Kit_Seal", PLINTH, a, b, 0, 0.1414, 0.012, panel=False)
        f0, f1 = a + G + 0.004, b - G - 0.004
        p.slab("Kit_Structure", PLINTH, f0, f1, 0.034, 0.046, 0.012, BEV_SMALL, segments=1, proud=0.012, panel=False)
        p.slab("Kit_Structure", PLINTH, f0, f1, 0.072, 0.084, 0.012, BEV_SMALL, segments=1, proud=0.012, panel=False)
        p.slab("Kit_GlowCool", PLINTH, f0 + 0.012, f1 - 0.012, 0.046, 0.072, 0.004, proud=0.004, panel=False)
        for (c0, c1) in ((f0, f0 + 0.012), (f1 - 0.012, f1)):
            p.slab("Kit_Structure", PLINTH, c0, c1, 0.034, 0.084, 0.012, proud=0.014, panel=False)
        p.box("Kit_Rubber", (-0.1, a, 0), (-0.085, b, 0.012), bevel=0.003, panel=False)
        p.slab("Kit_Primary", FACE, a + G, b - G, 0.1 + GAP / 2, 0.5 - GAP / 2, PT, BEV_MID, secondary=True)
        p.slab("Kit_Trim", FACE, a + G, b - G, 0.1 + GAP / 2, 0.2 + GAP / 2, 0.006, BEV_SMALL, proud=0.003, trim="kickplate", panel=False)
        p.slab("Kit_Signal", FACE, a, b, vt - 0.049, vt - 0.043, 0.01, proud=-0.006, panel=False)
        p.slab("Kit_Trim", FACE, a, b, vt - 0.025, vt + 0.025, 0.045, BEV_SMALL, proud=0.014, trim="rail_bolted", panel=False)


def _upper_side(p, sec, y_in, left):
    """The upper panel beside the side wall's slope, from the break to the ceiling, up to y_in (the bay edge)."""
    W, vt, top, xt, C = sec.width, sec.vt, sec.top, sec.xt, sec.ceiling
    z0 = vt + 0.03
    ys = (z0 - vt) * 0.75 + 0.01
    pts = [(ys, z0), (y_in, z0), (y_in, C), (xt - 0.14, C), (xt - 0.14, top), (xt, top)]
    if not left:
        pts = [(W - y, z) for (y, z) in reversed(pts)]
    p.poly_prism("Kit_Primary", pts, FACE, PT, panel=True)


def end_wall(sec, var, name, seed):
    """A corridor end wall with the section's outline: three bays between two vertical frames that run to the
    ceiling, pressed panels, the walls' rail and plinth carried across, a head beam under the ceiling. B has a window
    slot at eye height in the middle bay (glass in a gasketed frame over a deep dark box)."""
    p = kit_geo.Part(name, seed)
    rng = random.Random(seed)
    W, vt, top, xt, C = sec.width, sec.vt, sec.top, sec.xt, sec.ceiling
    b1, b2 = W / 3, 2 * W / 3
    rib = 0.03
    bays = [(G, b1 - rib), (b1 + rib, b2 - rib), (b2 + rib, W - G)]
    window = None
    if var == "B":
        window = (b1 + 0.1, b2 - 0.1, 0.8, 1.14)          # under the rail at the break
    # with a window the dark backing goes behind the shutter (at 7 cm it hid the reveal's back and the shutter), and
    # it is open behind the window: the shutter is half raised and the lower half looks out
    hole = (window[0] - 0.02, window[1] + 0.02, window[2] - 0.02, window[3] + 0.02) if window else None
    _end_base(p, sec, [(0.0, b1), (b1, b2), (b2, W)], back_x=-0.2 if var == "B" else -0.07, hole=hole)
    for k, (u0, u1) in enumerate(bays):
        if k == 1 and window:
            frame_hole(p, "Kit_Primary", FACE, u0, u1, 0.5 + GAP / 2, vt - 0.055, window)
        else:
            pressed(p, FACE, u0, u1, 0.5 + GAP / 2, vt - 0.055)
    # upper zone: side panels along the slopes, the middle bay to the ceiling
    _upper_side(p, sec, b1 - rib, True)
    _upper_side(p, sec, b2 + rib, False)
    pressed(p, FACE, b1 + rib, b2 - rib, vt + 0.03, C - 0.07)
    for y in (b1, b2):
        p.slab("Kit_Structure", FACE, y - rib, y + rib, 0.1, C, 0.07, proud=0.045, panel=False)
        for z in (0.35, 0.8, 1.6, 2.0):
            if z < C - 0.1:
                p.tube("Kit_Structure", (0.045, y, z), (0.05, y, z), 0.0065, 6)
    p.slab("Kit_Structure", FACE, xt - 0.14, W - xt + 0.14, C - 0.07, C, 0.08, BEV_SMALL, segments=1, proud=0.035, panel=False)
    if window:
        # a 14 cm reveal, the glass near the face, a closed armoured shutter behind it (slats) and its status
        # light: a window with nothing behind it read as a switched-off screen (critic)
        h0, h1, v0, v1 = window
        frame_ring(p, FACE, window, t=0.03, proud=0.02)
        # a second, outer collar a step lower: the frame in layers (critic r2: "no depth of the frame")
        frame_ring(p, FACE, (h0 - 0.03, h1 + 0.03, v0 - 0.03, v1 + 0.03), t=0.022, proud=0.01)
        gasket(p, FACE, window)
        p.slab("Kit_Glass", FACE, h0, h1, v0, v1, 0.004, proud=-0.012, panel=False)
        d = 0.14
        # the reveal runs back to the backing (-0.2): no gap round the opening to look into
        p.box("Kit_Primary", (-0.2, h0 - 0.02, v1), (0.0, h1 + 0.02, v1 + 0.02), panel=False)
        p.box("Kit_Structure", (-0.2, h0 - 0.02, v0 - 0.02), (0.0, h1 + 0.02, v0), bevel=BEV_SMALL, segments=1, panel=False)
        for (a0, a1) in ((h0 - 0.02, h0), (h1, h1 + 0.02)):
            p.box("Kit_Primary", (-0.2, a0, v0), (0.0, a1, v1), panel=False)
        # the armoured shutter half raised (author 27. 9.): four of seven dark slats down from the head and a heavier
        # bottom rail, the lower part open - in a ship it shows the real outside, in the showroom a star field
        n, n_down = 7, 4
        for k in range(n - n_down, n):
            z0 = v0 + (v1 - v0) * k / n
            z1 = v0 + (v1 - v0) * (k + 1) / n - 0.005
            # dark armoured slats: in the light paint under a warm light they read as a glowing box (critic r2)
            p.box("Kit_Primary", (-d - 0.012, h0, z0), (-d, h1, z1), bevel=0.002, segments=1)
        zb = v0 + (v1 - v0) * (n - n_down) / n
        p.box("Kit_Structure", (-d - 0.016, h0, zb - 0.014), (-d + 0.004, h1, zb + 0.004), bevel=0.003, segments=1)
        for yy in (h0 + 0.03, h1 - 0.03):
            # guide channels at the sides the slats run in
            p.box("Kit_Structure", (-d - 0.02, yy - 0.008, v0), (-d + 0.004, yy + 0.008, v1), bevel=0.002, segments=1, panel=False)
        # a strip light in the reveal's head lights the shutter (without it the window stayed black)
        p.box("Kit_GlowWarm", (-d + 0.02, h0 + 0.02, v1 - 0.006), (-0.03, h1 - 0.02, v1), panel=False)
        strip_light_along(p, "Light_Window_0", (-d / 2, (h0 + h1) / 2, v1 - 0.012), (-0.5, 0, -0.866), (0, 1, 0), h1 - h0 - 0.04, 0.02,
                          "work", 1.4, 0.6)
        p.box("Kit_GlowSignal", (0.0, h1 + 0.035, v1 - 0.03), (0.008, h1 + 0.05, v1 - 0.015), panel=False)
    p.collision_box((-0.2, 0, 0), (0, W, C))
    p.socket("Snap_Start", (0, 0, 0), x=(0, -1, 0), z=(0, 0, 1))
    p.socket("Snap_End", (0, W, 0), x=(0, 1, 0), z=(0, 0, 1))
    return p


def narrow(sec, var, name, seed):
    """The end of a W corridor narrowing into a service crawlway (section S, 0.9 m wide, flush portal): an end wall
    with the crawlway's outline cut in the middle, a framed opening with a hazard band over it, and 0.6 m of the
    crawlway behind (walls, ceiling with a dim strip, floor plate) fading into the dark."""
    p = kit_geo.Part(name, seed)
    S = Section("S")
    W, vt, top, xt, C = sec.width, sec.vt, sec.top, sec.xt, sec.ceiling
    o0, o1 = (W - S.width) / 2, (W + S.width) / 2
    f = 0.06
    _end_base(p, sec, [(0.0, o0 - f), (o1 + f, W)])
    for (u0, u1) in ((G, o0 - f - G), (o1 + f + G, W - G)):
        pressed(p, FACE, u0, u1, 0.5 + GAP / 2, vt - 0.055)
    _upper_side(p, sec, o0 - f - G, True)
    _upper_side(p, sec, o1 + f + G, False)
    p.slab("Kit_Primary", FACE, o0 - f, o1 + f, S.ceiling + f + 0.004, C, PT, BEV_MID)
    # the opening's frame, flush with the portal rules for S: members along the crawlway's outline
    ol = [(o0, 0.0), (o0, S.vt), (o0 + S.xt, S.ceiling), (o1 - S.xt, S.ceiling), (o1, S.vt), (o1, 0.0)]
    centre = (W / 2, 1.0)
    for a, b in zip(ol[:-1], ol[1:]):
        m, ln = seg_frame_wall(a, b, centre)
        # local y points into the opening: the member lies on the outer side (-y), 6 cm wide, 3 cm proud
        p.slab("Kit_Structure", m, -0.02, ln + 0.02, -f, 0.0, 0.05, BEV_SMALL, segments=1, proud=0.03, panel=False)
    label(p, "hazard_stripe", (0.0, W / 2, S.ceiling + f + 0.07), (1, 0, 0), (0, 1, 0), (0, 0, 1), 1.0)
    label(p, "st_service", (0.0, o1 + f + 0.2, 1.55), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.9)
    # the crawlway stub behind the opening, 0.6 m
    d = 0.6
    for (y, s) in ((o0, 1), (o1, -1)):
        yl, yi = (y - 0.02, y) if s > 0 else (y, y + 0.02)
        p.box("Kit_Primary", (-d, yl, 0.0), (0.0, yi, S.vt), panel=True)
        # its slope: a lofted face from the break to the crawlway ceiling
        p.quads("Kit_Primary", [[(-d, y, S.vt), (0.0, y, S.vt), (0.0, y + s * S.xt, S.ceiling), (-d, y + s * S.xt, S.ceiling)]],
                toward=(-d / 2, W / 2, 1.0))
        p.box("Kit_Structure", (-d, min(y, y + s * 0.03), S.vt - 0.03), (0.0, max(y, y + s * 0.03), S.vt + 0.01), panel=False)
    p.box("Kit_Primary", (-d, o0 + S.xt, S.ceiling), (0.0, o1 - S.xt, S.ceiling + 0.02), panel=True)
    p.box("Kit_GlowCool", (-0.45, W / 2 - 0.02, S.ceiling - 0.004), (-0.08, W / 2 + 0.02, S.ceiling), panel=False)
    p.box("Kit_Plastic", (-d, o0, -0.02), (0.0, o1, 0.0), panel=True)
    p.slab("Kit_Trim", frame((-d, 0, 0.0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 0.05, d - 0.05, o0 + 0.1, o1 - 0.1, 0.004, proud=0.002,
           trim="antislip_tread", panel=False)
    p.box("Kit_Seal", (-d - 0.01, o0, 0.0), (-d, o1, S.ceiling), panel=False)
    # 1.2 cd: at 0.25 the crawlway read as a black rectangle under MegaLights with shadows (27. 9. 2026)
    strip_light_along(p, "Light_Crawl_0", (-0.26, W / 2, S.ceiling - 0.01), (0, 0, -1), (1, 0, 0), 0.36, 0.04, "cool", 1.2, 1.2)
    # collision: the wall either side of the opening, the head, the crawlway walls
    p.collision_box((-0.2, 0, 0), (0, o0 - f, C))
    p.collision_box((-0.2, o1 + f, 0), (0, W, C))
    p.collision_box((-0.2, o0 - f, S.ceiling), (0, o1 + f, C))
    p.collision_box((-d, o0 - 0.05, 0), (0, o0, S.ceiling))
    p.collision_box((-d, o1, 0), (0, o1 + 0.05, S.ceiling))
    p.socket("Snap_Start", (0, 0, 0), x=(0, -1, 0), z=(0, 0, 1))
    p.socket("Snap_End", (0, W, 0), x=(0, 1, 0), z=(0, 0, 1))
    return p


# =============================================================================== the N -> W transition
def transition(name, seed):
    """0.6 m of run in which the section widens from N (1.2 m, break 1.7) to W (2.4 m, break 1.3): both walls flare
    at 45 deg in plan and their profile is lofted between the two sections - plinth recess and cool strip, vertical
    panel, the rail following the falling break, the slope, the cove lip, strip and fascia at the constant 2.1 m."""
    p = kit_geo.Part(name, seed)
    N, Wd = Section("N"), Section("W")
    L = 0.6
    C, top = Wd.ceiling, Wd.top
    room = (L / 2, 0.0, 1.0)
    for s in (1, -1):
        n = Vector((SQ, -s * SQ, 0.0))                       # inward normal of the flared face

        def at(t, inset, z):
            x = L * t
            y = s * (N.half + (Wd.half - N.half) * t)
            return Vector((x + n.x * inset, y + n.y * inset, z))

        vt = lambda t: N.vt + (Wd.vt - N.vt) * t
        xt = lambda t: N.xt + (Wd.xt - N.xt) * t

        def band(role, prof, secondary=False, toward=room):
            # prof(t) -> (inset0, z0, inset1, z1): a lofted strip between the two ends
            a0, z0, a1, z1 = prof(0.0)
            b0, w0, b1, w1 = prof(1.0)
            p.quads(role, [[at(0, a0, z0), at(1, b0, w0), at(1, b1, w1), at(0, a1, z1)]], toward=toward, secondary=secondary)

        band("Kit_Seal", lambda t: (-0.1, 0.0, 0.0, 0.1))
        band("Kit_Primary", lambda t: (0.0, 0.1, 0.0, 0.5), secondary=True)
        band("Kit_Primary", lambda t: (0.0, 0.5 + GAP / 2, 0.0, vt(t) - 0.055))
        band("Kit_Seal", lambda t: (-0.004, 0.5 - GAP / 2, -0.004, 0.5 + GAP / 2))
        band("Kit_Signal", lambda t: (-0.002, vt(t) - 0.049, -0.002, vt(t) - 0.043))
        band("Kit_Primary", lambda t: (0.0, vt(t) + 0.03, xt(t) - 0.01, top - 0.04 + 0.0))
        band("Kit_Primary", lambda t: (xt(t) - 0.125, top, xt(t) - 0.125, C), secondary=True)
        # the rail along the falling break, the lip along the top, the plinth and cove strips: bars on the loft
        a, b = at(0, 0.0, vt(0)), at(1, 0.0, vt(1))
        _bar(p, "Kit_Structure", a, b, n, 0.05, 0.016, 0.004)
        a, b = at(0, xt(0), top), at(1, xt(1), top)
        _bar(p, "Kit_Structure", a, b, n, 0.075, 0.026, -0.005)
        a, b = at(0, -0.05, 0.075), at(1, -0.05, 0.075)
        _bar(p, "Kit_GlowCool", a, b, Vector((SQ * n.x, SQ * n.y, -SQ)), 0.024, 0.004, 0.0)
        a, b = at(0, xt(0) - 0.07, top + 0.004), at(1, xt(1) - 0.07, top + 0.004)
        _bar(p, "Kit_GlowWarm", a, b, Vector((0, 0, 1)), 0.024, 0.004, 0.0)
        # a bolted frame rib up the middle of each flared face (vertical panel and slope) - the plain lofted
        # panels read as "a flat wall with a hole" (critic r2, r3)
        t = 0.5
        a, b = at(t, 0.0, 0.09), at(t, 0.0, vt(t) + 0.02)
        _bar(p, "Kit_Structure", a, b, n, 0.07, 0.035, 0.0)
        a2, b2 = at(t, 0.0, vt(t)), at(t, xt(t), top)
        d = (b2 - a2).normalized()
        h = Vector((-n.y, n.x, 0.0)).normalized()
        sn = d.cross(h).normalized()
        if sn.dot(n) < 0:
            sn = -sn
        _bar(p, "Kit_Structure", a2, b2, sn, 0.07, 0.035, 0.0)
        for z in (0.35, 0.8, vt(t) - 0.2):
            c = at(t, 0.036, z)
            p.tube("Kit_Structure", tuple(c), tuple(c + n * 0.005), 0.0065, 6)
        for u in (0.3, 0.7):
            c = a2 + d * ((b2 - a2).length * u) + sn * 0.036
            p.tube("Kit_Structure", tuple(c), tuple(c + sn * 0.005), 0.0065, 6)
        mid_cove = at(0.5, 0.5 * (N.xt + Wd.xt) - 0.07, top + 0.02)
        strip_light_along(p, "Light_Cove_%d" % (0 if s > 0 else 1), mid_cove, (0, 0, 1), (at(1, 0.45, top) - at(0, 0.3, top)),
                          0.75, 0.025, "warm", 0.6, 1.1)
        p.collision_hull([at(t, i, z) for t in (0.0, 1.0) for (i, z) in ((-0.2, 0.0), (0.0, 0.0), (0.0, C), (-0.2, C))])
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


def _bar(p, role, a, b, n, height, depth, lift):
    """A bar from a to b on a face with normal n: `height` across the face, `depth` proud of it."""
    ax = (b - a)
    ln = ax.length
    ax.normalize()
    zv = Vector(n).normalized()
    yv = zv.cross(ax).normalized()
    m = frame(a, ax, yv, zv)
    p.box(role, (0.0, -height / 2, lift), (ln, height / 2, lift + depth), m=m, panel=False)


# =============================================================================== corners
def _valley(sec):
    a = Vector((0.0, 0.0, sec.vt))
    b = Vector((sec.xt, sec.xt, sec.top))
    return a, b


def corner_inner(sec, var, name, seed):
    """The seam where two walls meet at an inner corner (their slopes make the valley themselves). A: a square
    structural post in the corner and a beam up the valley to a cove bracket. B: a 45 deg chamfer panel across the
    corner below the break (plinth and rail cut diagonally), the same valley beam."""
    p = kit_geo.Part(name, seed)
    vt, top, xt = sec.vt, sec.top, sec.xt
    if var == "A":
        # the post with its room-facing edge chamfered (a plain square box read as "a bare prism" - critic r2), a
        # foot plate, and a rubber guard on the chamfer where shoulders and carts hit
        post = [(0.0, 0.0), (0.13, 0.0), (0.13, 0.06), (0.06, 0.13), (0.0, 0.13)]
        p.poly_prism("Kit_Structure", post, frame((0.0, 0.0, vt + 0.03), (1, 0, 0), (0, 1, 0), (0, 0, 1)), vt + 0.03,
                     bevel=0.005, segments=1, panel=False)
        foot = [(0.0, 0.0), (0.16, 0.0), (0.16, 0.075), (0.075, 0.16), (0.0, 0.16)]
        p.poly_prism("Kit_Structure", foot, frame((0.0, 0.0, 0.08), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 0.08,
                     bevel=0.005, segments=1, panel=False)
        m_ch = frame((0.13, 0.06, 0.0), (-SQ, SQ, 0.0), (0.0, 0.0, 1.0), (SQ, SQ, 0.0))
        p.slab("Kit_Rubber", m_ch, 0.004, 0.095, 0.15, 1.0, 0.02, bevel=0.006, segments=2, proud=0.012, panel=False)
        for z in (0.3, 0.7, 1.1):
            if z < vt - 0.1:
                for (x, y, d) in ((0.13, 0.03, (1, 0, 0)), (0.03, 0.13, (0, 1, 0))):
                    p.tube("Kit_Structure", (x, y, z), (x + d[0] * 0.005, y + d[1] * 0.005, z), 0.0065, 6)
        p.box("Kit_Structure", (-0.01, -0.01, vt - 0.03), (0.16, 0.16, vt + 0.05), bevel=0.004, segments=1)
        p.collision_box((0.0, 0.0, 0.0), (0.16, 0.16, vt + 0.05))
    else:
        d = 0.34
        m = frame((d, 0.0, 0.0), (-SQ, SQ, 0.0), (0.0, 0.0, 1.0), (SQ, SQ, 0.0))
        w = d * math.sqrt(2)
        p.slab("Kit_Seal", m, -0.02, w + 0.02, 0.0, vt, 0.01, proud=-0.06, panel=False)
        p.slab("Kit_Primary", m, 0.0, w, 0.1 + GAP / 2, 0.5 - GAP / 2, PT, BEV_MID, secondary=True)
        pressed(p, m, 0.0, w, 0.5 + GAP / 2, vt - 0.055)
        p.slab("Kit_Trim", m, -0.01, w + 0.01, vt - 0.025, vt + 0.025, 0.045, BEV_SMALL, proud=0.014, trim="rail_bolted", panel=False)
        p.slab("Kit_Seal", m, 0.0, w, 0.0, 0.1, 0.012, proud=-0.02, panel=False)
        p.slab("Kit_GlowCool", m, 0.03, w - 0.03, 0.03, 0.06, 0.004, proud=-0.012, panel=False)
        p.collision_hull([(x, y, z) for z in (0.0, vt) for (x, y) in ((d, 0.0), (0.0, d), (0.0, 0.0))])
    # the valley beam and the bracket at the top of the valley
    a, b = _valley(sec)
    ax = (b - a).normalized()
    across = Vector((SQ, -SQ, 0.0))
    zv = ax.cross(across).normalized()
    m = frame(a, ax, across, zv)
    p.box("Kit_Structure", (0.0, -0.05, -0.02), ((b - a).length, 0.05, 0.06), m=m, bevel=0.004, segments=1)
    p.box("Kit_Structure", (xt - 0.09, xt - 0.09, top - 0.09), (xt + 0.02, xt + 0.02, top + 0.05), bevel=0.004, segments=1)
    p.socket("Snap_A", (0, 0, 0), x=(0, 1, 0), z=(0, 0, 1))
    p.socket("Snap_B", (0, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


def corner_outer(sec, var, name, seed):
    """An outer (convex) corner: the hip where the two walls' slopes meet over the quadrant beyond their ends (two
    triangular facets in the slope planes), a bumper up the vertical edge (painted guard with a rubber nose) that
    carries on as a ridge bar up the hip, and the cove turned round the corner (lip, ledge, strip, fascia)."""
    p = kit_geo.Part(name, seed)
    vt, top, xt, C = sec.vt, sec.top, sec.xt, sec.ceiling
    o = Vector((0.0, 0.0, vt))
    room = (xt * 2.0, xt * 2.0, vt - 0.5)
    p.quads("Kit_Primary", [[o, (xt, 0.0, top), (xt, xt, top)], [o, (xt, xt, top), (0.0, xt, top)]], toward=room)
    # backing under the facets so nothing shows through their seams
    p.quads("Kit_Seal", [[(0.0, 0.0, vt + 0.03), (xt, 0.0, top + 0.03), (xt, xt, top + 0.03), (0.0, xt, top + 0.03)]], toward=room)
    # the bumper: a guard over the vertical edge with a rubber nose, then a ridge bar up the hip with a rubber strip
    p.box("Kit_Structure", (-0.025, -0.025, 0.0), (0.075, 0.075, vt + 0.02), bevel=0.006, segments=1)
    p.tube("Kit_Rubber", (0.058, 0.058, 1.1), (0.058, 0.058, vt - 0.03), 0.026, 12)
    # the bumper proper: a rounded rubber guard 0.15-1.05 m over the edge, where carts and shoulders hit
    p.box("Kit_Rubber", (0.0, 0.0, 0.15), (0.098, 0.098, 1.05), bevel=0.018, segments=3)
    # hazard hatching on its two room faces (critic r2: "the bumper reads as a grey prism")
    label(p, "hazard_stripe", (0.098, 0.049, 0.6), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.8)
    label(p, "hazard_stripe", (0.049, 0.098, 0.6), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.8)
    a, b = o, Vector((xt, xt, top))
    ax = (b - a).normalized()
    across = Vector((SQ, -SQ, 0.0))
    zv = ax.cross(across).normalized()
    if zv.z > 0:
        zv = -zv
        across = -across
    m = frame(a, ax, across, zv)
    ln = (b - a).length
    p.box("Kit_Structure", (0.0, -0.045, -0.02), (ln, 0.045, 0.045), m=m, bevel=0.004, segments=1)
    p.box("Kit_Rubber", (0.04, -0.02, 0.045), (ln - 0.04, 0.02, 0.058), m=m, bevel=0.003, panel=False)
    # the cove round the corner, both arms
    for (i, j) in ((0, 1), (1, 0)):
        def bx(role, lo, hi, **kw):
            lo2 = [0, 0, lo[2]]
            hi2 = [0, 0, hi[2]]
            lo2[i], lo2[j] = lo[0], lo[1]
            hi2[i], hi2[j] = hi[0], hi[1]
            p.box(role, tuple(lo2), tuple(hi2), **kw)
        bx("Kit_Structure", (xt - 0.022, 0.0, top - 0.045), (xt + 0.004, xt + 0.004, top + 0.03), bevel=BEV_SMALL, panel=False)
        bx("Kit_Structure", (xt - 0.125, 0.0, top - 0.02), (xt - 0.02, xt - 0.02, top), panel=False)
        bx("Kit_Primary", (xt - 0.14, 0.0, top), (xt - 0.125, xt - 0.125, C), secondary=True)
        bx("Kit_GlowWarm", (xt - 0.08, 0.0, top), (xt - 0.055, xt - 0.055, top + 0.006), panel=False)
    p.collision_box((-0.025, -0.025, 0.0), (0.075, 0.075, vt))
    p.socket("Snap_A", (0, 0, 0), x=(0, -1, 0), z=(0, 0, 1))
    p.socket("Snap_B", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== the batch
# (category, part, size m, section, variant, builder, render views)
FRONT = ((1, 0, 0.12), (1, -0.9, 0.35))
FROM_BELOW = ((0.35, -0.15, -1.0), (0.9, -0.7, -0.8))
CORNER_VIEW = ((1, 1, 0.3), (1, 0.35, 0.45))

BATCH2 = [
    ("Portal", "Ring", 0.3, "W", "A"), ("Portal", "Ring", 0.3, "W", "B"), ("Portal", "Ring", 0.3, "W", "C"),
    ("Portal", "Ring", 0.3, "N", "A"), ("Portal", "Ring", 0.3, "N", "B"),
    ("Ceiling", "Panel", 1.2, "W", "A"), ("Ceiling", "Panel", 0.6, "W", "A"), ("Ceiling", "Panel", 0.3, "W", "A"),
    ("Ceiling", "Panel", 1.2, "W", "B"), ("Ceiling", "Panel", 1.2, "W", "C"),
    ("Ceiling", "Tray", 1.2, "W", "A"), ("Ceiling", "Tray", 0.6, "W", "A"), ("Ceiling", "Tray", 1.2, "W", "B"),
    ("Wall", "End", 2.4, "W", "A"), ("Wall", "End", 2.4, "W", "B"), ("Wall", "Narrow", 2.4, "W", "A"),
    ("Wall", "Transition", 0.6, "W", "A"),
    ("Corner", "Inner", 0.0, "W", "A"), ("Corner", "Inner", 0.0, "W", "B"), ("Corner", "Outer", 0.0, "W", "A"),
    # the sample's narrow stub (section N): its end wall and ceiling
    ("Wall", "End", 1.2, "N", "A"), ("Ceiling", "Panel", 1.2, "N", "A"),
]


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


VIEWS = {("Portal", "Ring"): FRONT, ("Ceiling", "Panel"): FROM_BELOW, ("Ceiling", "Tray"): FROM_BELOW,
         ("Corner", "Inner"): CORNER_VIEW, ("Corner", "Outer"): CORNER_VIEW, ("Wall", "End"): FRONT, ("Wall", "Narrow"): FRONT,
         ("Wall", "Transition"): ((1, 0.0, 0.12), (1, -0.9, 0.35))}


def build_part(cat, part, size, sec_key, var, seed):
    name = part_name(cat, part, size, sec_key, var)
    sec = Section(sec_key)
    if cat == "Portal":
        return portal(sec, var, name, seed)
    if cat == "Ceiling":
        return (ceiling_panel if part == "Panel" else ceiling_tray)(sec, var, size, name, seed)
    if cat == "Corner":
        return (corner_inner if part == "Inner" else corner_outer)(sec, var, name, seed)
    if part == "End":
        return end_wall(sec, var, name, seed)
    if part == "Narrow":
        return narrow(sec, var, name, seed)
    if part == "Transition":
        return transition(name, seed)
    raise ValueError(name)


def budget(cat, part, size):
    b = kit_geo.RULES["tri_budget"]
    if cat == "Portal":
        return b["Portal"]
    if cat == "Ceiling":
        return max(1500, int(b["Ceiling_per_m"] * size))
    if cat == "Corner":
        return b["Corner"]
    if part == "Transition":
        return int(b["Wall_base"] + b["Wall_per_m"] * size * 2)       # both walls
    return int(b["Wall_base"] + b["Wall_per_m"] * size)
