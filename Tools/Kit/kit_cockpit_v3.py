"""Wayfarer cockpit v3 (author 8. 10. 2026, ArtSource/Ships/Wayfarer/Concept/Cockpit/cockpit_layout_v3_proposal.png):
the sticks on the seat's arms, the consoles thin along the walls and run into the dash wings (one shape, the glossy
column paint), aisles round the seat on both sides.

  SM_Kit_Cockpit_SeatArm07W_L / _R          the seat's forearm rest: a leather pad, 2 x 2 backlit keys, the stick; a
                                            bracket down to the seat's side
  SM_Kit_Cockpit_ConsoleWall18W_L / _R      v4 (concept consoles_v4_concept_b.png): one lofted shape out of the
                                            lining up into the dash wing, a sloped top with the SYS rockers and the
                                            EMERG field sunk in it, a recessed lit kick, light lines on its inner edge

Both are built in the ship layout's coordinates (x from the stern, y to port, z from the cockpit floor) and placed at
the layout's origin (interior.kit_modules.run_parts [[0, 0, 1.15], [1, 0], [part]]): the console follows the hull's
wall polygon exactly. _R is the mirror of _L (kit_cockpit_b._mirror_y: the text still reads right).
"""
import math

from mathutils import Vector

import kit_geo
from kit_geo import frame
import kit_cockpit_b as kb
from kit_cockpit_b import side_prism, screw, legend, led, keycap, rocker_b, emergency_key, MIRROR, _mirror_y
from kit_cockpit import stick, _label

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
WALL = [(15.2, 1.75), (16.5, 1.6), (18.6, 1.0)]     # the cockpit's port wall (Wayfarer_layout.json, rooms.cockpit.poly)
LINER = 0.1                                         # the lining's face inside the hull line
CX1 = 17.85                                         # the console's front, tucked into the dash wing
# cockpit v4 (author 8. 10. 2026: the side consoles read as boxes - concept consoles_v4_concept_b.png approved): one
# lofted shape growing out of the lining and sweeping up into the dash wing. Stations (x, depth from the lining's
# face, height of its inner top edge); the top falls 11 deg towards the aisle (SLOPE); the depth never exceeds v3's
# (the aisles stay as walked).
STATIONS = [(15.9, 0.06, 0.64), (16.0, 0.30, 0.66), (16.5, 0.257, 0.689), (16.7, 0.24, 0.70), (17.25, 0.14, 0.72),
            (17.62, 0.08, 0.835), (CX1, 0.06, 0.835)]
SLOPE = 0.2


def wall_y(x):
    for (a, b), (c, e) in zip(WALL, WALL[1:]):
        if a <= x <= c:
            return b + (e - b) * (x - a) / (c - a)
    return WALL[-1][1]


def _built(fn, name, seed, mirror):
    MIRROR[0] = mirror
    try:
        p = fn(name, seed)
    finally:
        MIRROR[0] = False
    if mirror:
        _mirror_y(p)
    return p


def guarded_toggle(p, c, r, a, n):
    """A toggle under a hinged red guard (22 x 30 mm) in a satin bezel, its black-yellow field."""
    fm = frame(c, r, a, n)
    p.box("Kit_Lip", (-0.013, -0.017, 0.0), (0.013, 0.017, 0.003), bevel=0.0012, segments=2, m=fm)
    p.box("Kit_Seal", (-0.010, -0.014, 0.0028), (0.010, 0.014, 0.0034), m=fm, panel=False)
    p.lathe("Kit_Lip", [(0.0035, 0.0), (0.0035, 0.004), (0.0015, 0.012), (0.0, 0.0125)], tuple(fm @ Vector((0.0, -0.002, 0.003))), axis=tuple(n), seg=12)
    p.box("Kit_Red", (-0.011, -0.015, 0.016), (0.011, 0.015, 0.0175), bevel=0.0008, segments=1, m=fm)
    for sv in (-1, 1):
        p.box("Kit_Red", (sv * 0.011 - 0.001, -0.015, 0.0034), (sv * 0.011 + 0.001, 0.015, 0.0175), m=fm, panel=False)
    p.box("Kit_Red", (-0.011, 0.014, 0.0034), (0.011, 0.015, 0.0175), m=fm, panel=False)
    for k in range(5):                                   # the black-yellow field under it
        p.box("Kit_Signal", (-0.016 + k * 0.0065, -0.024, 0.0), (-0.013 + k * 0.0065, -0.019, 0.0012), m=fm, panel=False)


def knob(p, c, n, r=0.011):
    """A knurled rotary selector: a satin skirt, a graphite knob with ribs, a lit index line."""
    n = Vector(n)
    p.lathe("Kit_Lip", [(r + 0.004, 0.0), (r + 0.004, 0.002), (r + 0.002, 0.003)], tuple(c), axis=tuple(n), seg=24)
    p.lathe("Kit_Inset", [(r, 0.002), (r, 0.012), (r * 0.85, 0.016), (0.0, 0.0165)], tuple(c), axis=tuple(n), seg=24)
    t = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
    b = n.cross(t).normalized()
    t = b.cross(n).normalized()
    for k in range(16):
        ang = 2 * math.pi * k / 16
        q = Vector(c) + (t * math.cos(ang) + b * math.sin(ang)) * r
        p.sweep("Kit_Housing", [q + n * 0.003, q + n * 0.011], 0.0009, seg=4)
    p.box("Kit_GlowCool", (-0.0007, 0.002, 0.0164), (0.0007, r * 0.8, 0.0168), m=frame(Vector(c), t, b, n), panel=False)


def boot(p, c, n, r0=0.035, r1=0.012, h=0.03, folds=4):
    """A folded rubber boot round the stick's neck."""
    prof = [(r0, 0.0)]
    for k in range(folds * 2):
        t = (k + 1) / (folds * 2)
        rr = r0 + (r1 - r0) * t + (0.004 if k % 2 == 0 else -0.002)
        prof.append((rr, h * t))
    prof.append((0.0, h))
    p.lathe("Kit_Gasket", prof, tuple(c), axis=tuple(n), seg=32)


# ------------------------------------------------------------------ the seat's arm
def _seat_arm(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge", "Kit_PanelPaint": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    x0, x1, y0, y1, at = 16.72, 17.42, 0.42, 0.58, 0.62
    beam = [(x0, 0.53), (x1 - 0.03, 0.53), (x1, 0.56), (x1, 0.598), (x1 - 0.015, 0.605), (x0 + 0.02, 0.605), (x0, 0.585)]
    side_prism(p, "Kit_PanelPaint", beam, y0, y1, 0.01, 3)          # (shape pass 8. 10.) rounded, not a chamfered box
    # the forearm pad: leather on a graphite base, a domed top, a grey stitch in a dark channel
    p.box("Kit_Inset", (x0 + 0.015, y0 + 0.006, 0.603), (17.02, y1 - 0.006, 0.61), bevel=0.003, segments=2)
    p.box("Kit_Leather", (x0 + 0.02, y0 + 0.01, 0.608), (17.0, y1 - 0.01, at), bevel=0.01, segments=4)
    p.box("Kit_Leather", (x0 + 0.03, y0 + 0.02, 0.612), (16.99, y1 - 0.02, at + 0.006), bevel=0.008, segments=4)
    for uu in (y0 + 0.028, y1 - 0.028):
        p.box("Kit_Seal", (x0 + 0.04, uu - 0.0013, at + 0.0045), (16.98, uu + 0.0013, at + 0.0062), panel=False)
        xx = x0 + 0.045
        while xx + 0.004 < 16.975:
            p.box("Kit_Housing", (xx, uu - 0.0006, at + 0.0048), (xx + 0.004, uu + 0.0006, at + 0.0066), panel=False)
            xx += 0.006
    # 2 x 2 backlit keys and the stick ahead of the pad
    kc = Vector((17.115, (y0 + y1) / 2, 0.605))
    p.box("Kit_Inset", (17.03, y0 + 0.008, 0.6025), (x1 - 0.012, y1 - 0.012, 0.6052), bevel=0.0015, segments=2, panel=False)   # the controls' field
    p.box("Kit_Lip", (17.055, y0 + 0.012, 0.603), (17.175, y1 - 0.012, 0.607), bevel=0.0015, segments=2)
    for i, lab in enumerate(("LT", "GR", "VT", "ESP")):
        q = kc + X * (0.026 * (1 if i % 2 else -1)) + Y * (0.0245 * (1 if i < 2 else -1))
        keycap(p, frame(q - Z * 0.0055, -Y, X, Z), lab)
    stick(p, Vector((17.33, (y0 + y1) / 2, 0.605)), "ck_rcs", head_role="Kit_Frame", guard="d", plate_role="Kit_Inset",
          ball_role="Kit_Gasket", bars=15, grip_role="Kit_Inset")
    # a cool light line along the arm's outer underside (it reads from the aisle), its channel
    p.box("Kit_Seal", (x0 + 0.03, y1 - 0.002, 0.533), (x1 - 0.05, y1 + 0.0008, 0.545), panel=False)
    p.box("Kit_GlowStrip", (x0 + 0.033, y1 - 0.001, 0.5365), (x1 - 0.053, y1 + 0.0016, 0.5415), bevel=0.0008, segments=1, panel=False)
    # the bracket to the seat: a post under the arm and a plate on the seat's side, bolted
    p.box("Kit_PanelPaint", (16.87, y0 + 0.004, 0.3), (16.95, y0 + 0.045, 0.532), bevel=0.014, segments=3)
    p.box("Kit_Lip", (16.81, 0.372, 0.28), (17.01, 0.428, 0.39), bevel=0.005, segments=3)
    for xx in (16.83, 16.99):
        for zz in (0.295, 0.375):
            screw(p, Vector((xx, 0.4285, zz)), Y, 0.004)
    _label(p, "st_hfcl", Vector((17.2, y1 + 0.0005, 0.565)), Y, -X, Z, scale=0.35)
    # (cockpit v3 r1, critic: one detail where SC has five) a satin strip along the top's outer edge, perforation in
    # the pad's middle band, two screwed graphite side panels with a grille between, a light line and an LED on the
    # front, a folded rubber boot round the stick, a guarded toggle by the keys, the serial plate
    p.box("Kit_Lip", (x0 + 0.02, y1 - 0.009, 0.603), (x1 - 0.02, y1 - 0.001, 0.607), bevel=0.0012, segments=2, panel=False)
    for i in range(int((16.97 - x0 - 0.06) / 0.006)):
        for j in range(5):
            hx, hu = x0 + 0.05 + i * 0.006, (y0 + y1) / 2 - 0.012 + j * 0.006 + (0.003 if i % 2 else 0.0)
            p.box("Kit_Seal", (hx - 0.001, hu - 0.001, at + 0.0058), (hx + 0.001, hu + 0.001, at + 0.0066), panel=False)
    for (sa, sb) in ((x0 + 0.03, x0 + 0.21), (x0 + 0.29, x0 + 0.47)):
        p.box("Kit_Inset", (sa, y1 - 0.002, 0.545), (sb, y1 + 0.004, 0.597), bevel=0.002, segments=2)
        for xx in (sa + 0.01, sb - 0.01):
            for zz in (0.553, 0.589):
                screw(p, Vector((xx, y1 + 0.0045, zz)), Y, 0.0035)
    p.box("Kit_Lip", (x0 + 0.215, y1 - 0.001, 0.55), (x0 + 0.285, y1 + 0.0035, 0.592), bevel=0.001, segments=1, panel=False)
    p.box("Kit_Perforated", (x0 + 0.219, y1 + 0.0032, 0.554), (x0 + 0.281, y1 + 0.0042, 0.588), panel=False)
    p.box("Kit_Seal", (x1 + 0.0002, y0 + 0.02, 0.566), (x1 + 0.0016, y1 - 0.02, 0.576), panel=False)
    p.box("Kit_GlowStrip", (x1 + 0.0012, y0 + 0.024, 0.5685), (x1 + 0.0028, y1 - 0.045, 0.5735), bevel=0.0006, segments=1, panel=False)
    led(p, Vector((x1 + 0.0016, y1 - 0.03, 0.571)), X, glow="Kit_GlowAmber", r=0.0024)
    boot(p, Vector((17.33, (y0 + y1) / 2, 0.609)), Z)
    guarded_toggle(p, Vector((17.225, y0 + 0.03, 0.6055)), -Y, X, Z)
    p.box("Kit_Lip", (x0 + 0.5, y1 - 0.0005, 0.5465), (x0 + 0.62, y1 + 0.0018, 0.5655), bevel=0.0005, segments=1, panel=False)
    p.box("Kit_Legend", (x0 + 0.502, y1 + 0.0012, 0.548), (x0 + 0.618, y1 + 0.0022, 0.564), panel=False)
    legend(p, "HF-SA 07  SN 2214", Vector((x0 + 0.56, y1 + 0.0022, 0.556)), -X, Z, Y, h=0.0055, role="Kit_Seal")
    p.collision_box((x0, y0, 0.22), (x1, y1, 0.68))
    return p


def seat_arm(name, seed, mirror=False):
    return _built(_seat_arm, name, seed, mirror)


# ------------------------------------------------------------------ the wall console
def _station(x):
    """(depth, inner top z) at x, linear between the stations."""
    for (xa, da, za), (xb, db, zb) in zip(STATIONS, STATIONS[1:]):
        if xa <= x <= xb:
            t = (x - xa) / (xb - xa)
            return da + (db - da) * t, za + (zb - za) * t
    return STATIONS[-1][1], STATIONS[-1][2]


def _V(x, s, z):
    """A point s in from the lining's face (s < 0: into the lining) at height z."""
    return Vector((x, wall_y(x) - LINER - s, z))


def _section(x):
    """The console's cross-section at x, round from the lining's foot: the kick recessed 5 cm (its top chamfered out
    to the face), the inner face, a 25 mm chamfer to the top, the sloped top back into the lining."""
    d, zi = _station(x)
    zo = zi + SLOPE * (d - 0.005)
    return [_V(x, -0.02, 0.0), _V(x, d - 0.05, 0.0), _V(x, d - 0.05, 0.10), _V(x, d, 0.13), _V(x, d, zi - 0.03),
            _V(x, d - 0.025, zi), _V(x, -0.02, zo)]


def top_pt(x, s):
    """A point on the console's sloped top."""
    d, zi = _station(x)
    return _V(x, s, zi + SLOPE * (d - 0.025 - s))


def top_frame(x, s):
    """(point, right, up, normal) on the top: up towards the wall (reads from the seat), right forward."""
    q = top_pt(x, s)
    a = (top_pt(x, s - 0.01) - q).normalized()
    r0 = (top_pt(x + 0.01, s) - q).normalized()
    n = r0.cross(a).normalized()
    if n.z < 0:
        n = -n
    r = a.cross(n).normalized()
    return q, r, a, n


def _skin(p, role, rings, centres):
    """Closed rings (same count) skinned with quads, each face turned away from its ring pair's centre; caps."""
    verts, faces = [], []
    m = len(rings[0])
    for ring in rings:
        verts += [Vector(v) for v in ring]
    def fix(f, c):
        a_, b_, c_ = verts[f[0]], verts[f[1]], verts[f[2]]
        nrm = (b_ - a_).cross(c_ - a_)
        ctr = sum((verts[i] for i in f), Vector()) / len(f)
        return f if nrm.dot(ctr - c) >= 0 else f[::-1]
    for k in range(len(rings) - 1):
        c = (centres[k] + centres[k + 1]) / 2
        for i in range(m):
            j = (i + 1) % m
            faces.append(fix([k * m + i, k * m + j, (k + 1) * m + j, (k + 1) * m + i], c))
    faces.append(fix(list(range(m)), centres[1]))                         # the caps face away from the next ring
    faces.append(fix([(len(rings) - 1) * m + i for i in range(m)], centres[-2]))
    return p.mesh(role, [tuple(v) for v in verts], faces)


def _top_patch(p, role, x0, x1, s0, s1, z0, z1):
    """A slab following the sloped top between x0..x1 and s0..s1 (s1 a number or a function of x: a field that
    narrows with the console), from z0 to z1 over it (insets, bezels)."""
    xs = [x0] + [st[0] for st in STATIONS if x0 < st[0] < x1] + [x1]
    rings, centres = [], []
    for x in xs:
        s1x = s1(x) if callable(s1) else s1
        ring = [top_pt(x, s0) + Vector((0, 0, z0)), top_pt(x, s1x) + Vector((0, 0, z0)),
                top_pt(x, s1x) + Vector((0, 0, z1)), top_pt(x, s0) + Vector((0, 0, z1))]
        rings.append(ring)
        centres.append(sum(ring, Vector()) / 4)
    _skin(p, role, rings, centres)


def _face_patch(p, role, x0, x1, z0, z1, o0, o1):
    """A slab on the console's inner face between x0..x1 and z0..z1, o0..o1 proud of it (windows, frames)."""
    xs = [x0] + [st[0] for st in STATIONS if x0 < st[0] < x1] + [x1]
    rings, centres = [], []
    for x in xs:
        d = _station(x)[0]
        ring = [_V(x, d + o0, z0), _V(x, d + o0, z1), _V(x, d + o1, z1), _V(x, d + o1, z0)]
        rings.append(ring)
        centres.append(sum(ring, Vector()) / 4)
    _skin(p, role, rings, centres)


def _wall_console(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge", "Kit_PanelPaint": "Kit_FrameEdge", "Kit_PanelSatin": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    # the body: one loft through the stations, the panel paint (author 8. 10.: the column's glossy white)
    xs = [st[0] for st in STATIONS]
    rings = [_section(x) for x in xs]
    centres = []
    for x in xs:
        d, zi = _station(x)
        centres.append(_V(x, min(d * 0.45, d - 0.07), zi * 0.5))
    _skin(p, "Kit_PanelSatin", rings, centres)       # (concept B: white and lit, the mirror coat read grey)
    # the kick's back: dark, a light line along its top lights the recess and the floor (concept B)
    kick = [[_V(x, _station(x)[0] - 0.0505, 0.004), _V(x, _station(x)[0] - 0.0505, 0.098),
             _V(x, _station(x)[0] - 0.047, 0.098), _V(x, _station(x)[0] - 0.047, 0.004)] for x in xs]
    _skin(p, "Kit_Inset", kick, [sum(r, Vector()) / 4 for r in kick])
    # (v4 r1: a thin line under the overhang did not read) a 4 cm band of light along the kick's back: the recess glows
    band = [[_V(x, _station(x)[0] - 0.0468, 0.02), _V(x, _station(x)[0] - 0.0468, 0.06),
             _V(x, _station(x)[0] - 0.0452, 0.06), _V(x, _station(x)[0] - 0.0452, 0.02)] for x in xs]   # (in front of the dark back)
    _skin(p, "Kit_GlowStrip", band, [sum(r, Vector()) / 4 for r in band])
    # the inner top edge: a satin rail in the chamfer and a cool light line under it, both running on into the dash
    p.sweep("Kit_Lip", [_V(x, _station(x)[0] - 0.011, _station(x)[1] - 0.012) for x in xs], 0.0045, seg=10)
    p.sweep("Kit_GlowStrip", [_V(x, _station(x)[0] + 0.0012, _station(x)[1] - 0.042) for x in xs], 0.0022, seg=8)
    # seams down the inner face at its breaks and between them
    # (v4 r1: black seams every 30 cm read as cracks) hairline seams only where the face breaks
    for x in (16.5, 17.25):
        d, zi = _station(x)
        p.sweep("Kit_Seal", [_V(x, d + 0.0002, 0.135), _V(x, d + 0.0002, zi - 0.05)], 0.0007, seg=4)
    da = _station(16.3)[0]
    t = (_V(16.31, da, 0) - _V(16.3, da, 0)).normalized()
    nf = Vector((t.y, -t.x, 0.0))
    if nf.dot(Vector((0, -1, 0))) < 0:
        nf = -nf
    _label(p, "maker", _V(16.3, da + 0.0008, 0.52), nf, t, Vector((0, 0, 1)), scale=0.55)
    # (concept B) one graphite field along the top, narrowing with the console, in a satin bezel: the SYS rockers in a
    # row by the wall, the emergency key, the power bars and the caution lamp ahead of them
    edge = lambda x: _station(x)[0] - 0.045                # noqa: E731
    _top_patch(p, "Kit_Lip", 16.03, 17.16, 0.03, edge, -0.002, 0.0025)
    _top_patch(p, "Kit_Inset", 16.04, 17.15, 0.036, lambda x: edge(x) - 0.006, -0.001, 0.0034)
    labs = ("PWR", "EXT LT", "ENG", "LIGHTS", "GEAR", "VTOL")
    for i, lab in enumerate(labs):
        q, r, a, n = top_frame(16.1 + i * 0.08, 0.098)
        rocker_b(p, q + n * 0.0034, r, a, n, lit="Kit_GlowAmber" if lab == "GEAR" else "Kit_GlowCool")
        legend(p, lab, q - a * 0.032 + n * 0.0036, r, a, n, h=0.0066)
    q, r, a, n = top_frame(16.07, 0.142)
    legend(p, "SYS", q + n * 0.0036, r, a, n, h=0.013)
    q, r, a, n = top_frame(16.72, 0.068)
    emergency_key(p, q + n * 0.0034, r, a, n)
    for k, lab in enumerate(("MAIN", "BATT")):
        for gi in range(8):
            on = gi < (8, 5)[k]
            q, r, a, n = top_frame(16.84 + gi * 0.017, 0.064 + 0.03 * k)
            fm = frame(q + n * 0.0034, r, a, n)
            p.box("Kit_GlowCool" if on else "Kit_Seal", (-0.0065, -0.004, 0.0), (0.0065, 0.004, 0.0009 if on else 0.0004), m=fm, panel=False)
        q, r, a, n = top_frame(16.805, 0.064 + 0.03 * k)
        legend(p, lab, q + n * 0.0036, r, a, n, h=0.0055)
    q, r, a, n = top_frame(17.1, 0.08)
    led(p, q + n * 0.0034, n, glow="Kit_GlowAmber", r=0.004)
    legend(p, "CAUT", q - a * 0.02 + n * 0.0036, r, a, n, h=0.0055)
    # (concept B) lit windows in the inner face: a dark recess in a satin frame, a band of light along its foot
    for (wx0, wx1) in ((16.08, 16.46), (16.56, 17.16), (17.3, 17.58)):
        _face_patch(p, "Kit_Lip", wx0 - 0.008, wx1 + 0.008, 0.162, 0.408, 0.0004, 0.003)
        _face_patch(p, "Kit_Inset", wx0, wx1, 0.17, 0.4, 0.0004, 0.0036)
        _face_patch(p, "Kit_GlowStrip", wx0 + 0.015, wx1 - 0.015, 0.182, 0.19, 0.0036, 0.0048)
    # the collision: one hull per span
    for (x0, x1) in zip(xs, xs[1:]):
        pts = []
        for x in (x0, x1):
            d, zi = _station(x)
            pts += [_V(x, -0.02, 0.0), _V(x, d, 0.0), _V(x, d, zi), _V(x, -0.02, zi + SLOPE * (d - 0.005))]
        p.collision_hull(pts)
    return p


def wall_console(name, seed, mirror=False):
    return _built(_wall_console, name, seed, mirror)


# ------------------------------------------------------------------ the seat back's shell
def seat_back(name, seed):
    """The pilot seat's back from behind (cockpit v3 r1, critic: a black slab): a glossy shell on the back's 8 deg
    slope (measured off PilotSeat.glb as placed: x 16.636 at 0.45 m, 16.55 at 1.05 m), a graphite inset in four
    fields, the mechanism cover with screws, the serial plate and a black-yellow field, a light line under the top."""
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    u = Vector((-0.086, 0.0, 0.6)).normalized()           # up the back
    n = Vector((-u.z, 0.0, u.x))                           # out of it, aft
    r = u.cross(n)                                         # right x up = out: the viewer behind sees -y as right
    r = -r if r.dot(Vector((0, -1, 0))) < 0 else r
    o = Vector((16.636 - 0.143 * (0.74 - 0.45), 0.0, 0.74)) + n * 0.003
    fm = lambda q: frame(q, r, u, n)                       # noqa: E731
    p.box("Kit_Frame", (-0.2, -0.3, -0.006), (0.2, 0.3, 0.012), bevel=0.01, segments=3, m=fm(o))
    for (a0, a1, b0, b1) in ((-0.15, -0.002, 0.02, 0.24), (0.002, 0.15, 0.02, 0.24), (-0.15, -0.002, -0.2, 0.016), (0.002, 0.15, -0.2, 0.016)):
        p.box("Kit_Inset", (a0, b0, 0.011), (a1, b1, 0.015), bevel=0.002, segments=2, m=fm(o))
    for su in (-1, 1):
        for sv in (-1, 1):
            screw(p, fm(o) @ Vector((su * 0.175, sv * 0.27, 0.0125)), n, 0.004)
    # the mechanism cover at the bottom
    p.box("Kit_Housing", (-0.08, -0.29, 0.012), (0.08, -0.21, 0.03), bevel=0.006, segments=3, m=fm(o))
    for su in (-1, 1):
        for sv in (-1, 1):
            screw(p, fm(o) @ Vector((su * 0.068, -0.25 + sv * 0.028, 0.0302)), n, 0.0035)
    for k in range(6):                                     # the black-yellow field over it
        p.box("Kit_Signal", (-0.04 + k * 0.014, -0.205, 0.012), (-0.033 + k * 0.014, -0.188, 0.0135), m=fm(o), panel=False)
    p.box("Kit_Lip", (0.03, 0.25, 0.0118), (0.13, 0.28, 0.0135), bevel=0.0005, segments=1, m=fm(o), panel=False)
    p.box("Kit_Legend", (0.032, 0.252, 0.0128), (0.128, 0.278, 0.0142), m=fm(o), panel=False)
    legend(p, "PS-07  SN 0417", fm(o) @ Vector((0.08, 0.265, 0.0142)), r, u, n, h=0.0075, role="Kit_Seal")
    p.box("Kit_Seal", (-0.16, 0.255, 0.0118), (-0.02, 0.271, 0.0132), m=fm(o), panel=False)
    p.box("Kit_GlowStrip", (-0.157, 0.259, 0.0128), (-0.023, 0.267, 0.0145), bevel=0.0008, segments=1, m=fm(o), panel=False)
    _label(p, "maker", fm(o) @ Vector((0.0, -0.06, 0.0151)), n, r, u, scale=0.45)
    p.collision_box(tuple(fm(o) @ Vector((-0.2, -0.3, -0.006))), tuple(fm(o) @ Vector((0.2, 0.3, 0.03))))
    return p
