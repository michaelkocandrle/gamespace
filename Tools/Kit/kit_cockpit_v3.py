"""Wayfarer cockpit v3 (author 8. 10. 2026, ArtSource/Ships/Wayfarer/Concept/Cockpit/cockpit_layout_v3_proposal.png):
the sticks on the seat's arms, the consoles thin along the walls and run into the dash wings (one shape, the glossy
column paint), aisles round the seat on both sides.

  SM_Kit_Cockpit_SeatArm07W_L / _R          the seat's forearm rest: a leather pad, 2 x 2 backlit keys, the stick; a
                                            bracket down to the seat's side
  SM_Kit_Cockpit_ConsoleWall18W_L / _R      the wall console from 16.0 m to the dash wing: an intake, a service
                                            hatch, a tower with the emergency key, six rockers and the status bars on
                                            its seat-facing slope, light lines along its inner face

Both are built in the ship layout's coordinates (x from the stern, y to port, z from the cockpit floor) and placed at
the layout's origin (interior.kit_modules.run_parts [[0, 0, 1.15], [1, 0], [part]]): the console follows the hull's
wall polygon exactly. _R is the mirror of _L (kit_cockpit_b._mirror_y: the text still reads right).
"""
import math

from mathutils import Vector

import kit_geo
from kit_geo import frame
import kit_cockpit_b as kb
from kit_cockpit_b import side_prism, end_prism, screw, legend, led, keycap, rocker_b, emergency_key, MIRROR, _mirror_y
from kit_cockpit import stick, _label

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
WALL = [(15.2, 1.75), (16.5, 1.6), (18.6, 1.0)]     # the cockpit's port wall (Wayfarer_layout.json, rooms.cockpit.poly)
LINER = 0.1                                         # the lining's face inside the hull line
CX0, CX1 = 16.0, 17.85                              # the console's aft end .. its front, tucked into the dash wing
TOP = 0.70                                          # the console's top over the cockpit floor


def wall_y(x):
    for (a, b), (c, e) in zip(WALL, WALL[1:]):
        if a <= x <= c:
            return b + (e - b) * (x - a) / (c - a)
    return WALL[-1][1]


def depth(x):
    """The console's depth from the lining: 0.36 m aft, 0.06 m at the dash (the aisle stays >= 0.53 m)."""
    return 0.36 + (0.06 - 0.36) * (min(max(x, CX0), 17.75) - CX0) / (17.75 - CX0)


def inner_y(x):
    return wall_y(x) - LINER - depth(x)


def _built(fn, name, seed, mirror):
    MIRROR[0] = mirror
    try:
        p = fn(name, seed)
    finally:
        MIRROR[0] = False
    if mirror:
        _mirror_y(p)
    return p


# ------------------------------------------------------------------ the seat's arm
def _seat_arm(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    x0, x1, y0, y1, at = 16.72, 17.42, 0.42, 0.58, 0.62
    beam = [(x0, 0.53), (x1 - 0.03, 0.53), (x1, 0.56), (x1, 0.598), (x1 - 0.015, 0.605), (x0 + 0.02, 0.605), (x0, 0.585)]
    side_prism(p, "Kit_Frame", beam, y0, y1, 0.006, 1)
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
    p.box("Kit_Housing", (16.85, y0 + 0.005, 0.24), (16.97, y0 + 0.06, 0.532), bevel=0.006, segments=3)
    p.box("Kit_Housing", (16.76, 0.398, 0.22), (17.06, 0.428, 0.42), bevel=0.006, segments=3)
    for xx in (16.79, 17.03):
        for zz in (0.25, 0.39):
            screw(p, Vector((xx, 0.4285, zz)), Y, 0.0045)
    _label(p, "st_hfcl", Vector((17.2, y1 + 0.0005, 0.565)), Y, -X, Z, scale=0.35)
    p.collision_box((x0, y0, 0.22), (x1, y1, 0.68))
    return p


def seat_arm(name, seed, mirror=False):
    return _built(_seat_arm, name, seed, mirror)


# ------------------------------------------------------------------ the wall console
def _inner_frame(xa, xb, z, out=0.0):
    """A frame on the console's inner face between xa and xb: x along it (forward), y up, z out (to the aisle)."""
    a = Vector((xa, inner_y(xa), z))
    b = Vector((xb, inner_y(xb), z))
    t = (b - a).normalized()
    n = Vector((t.y, -t.x, 0.0))                       # out of the face, to the seat
    return a + n * out, t, n, (b - a).length


def _wall_console(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    xs = [CX0, 16.5, CX1]
    inner = [(x, inner_y(x)) for x in xs]
    outer = [(x, wall_y(x) - LINER + 0.02) for x in xs]     # 2 cm into the lining: no gap at the wall
    p.poly_prism("Kit_Frame", inner + outer[::-1], frame(Vector((0, 0, TOP)), X, Y, Z), TOP, bevel=0.009, segments=1)
    # a dark kick 4 cm in along the floor
    kick = [(x, inner_y(x) + 0.035) for x in xs]
    p.poly_prism("Kit_Inset", kick + outer[::-1], frame(Vector((0, 0, 0.05)), X, Y, Z), 0.05, bevel=0.003, segments=1)
    # the inner face: graphite panels with seams and screws, a light line low and one under the top edge
    for (xa, xb) in ((CX0, 16.5), (16.5, 17.75)):
        o, t, n, ln = _inner_frame(xa, xb, 0.0)
        fm = frame(o, t, Z, n)
        segs = 1 if ln < 0.6 else 3
        for k in range(segs):
            s0 = 0.03 + k * (ln - 0.06) / segs + (0.002 if k else 0.0)
            s1 = 0.03 + (k + 1) * (ln - 0.06) / segs - (0.002 if k < segs - 1 else 0.0)
            p.box("Kit_Inset", (s0, 0.12, -0.002), (s1, TOP - 0.08, 0.005), bevel=0.003, segments=2, m=fm)
            for ss in (s0 + 0.014, s1 - 0.014):
                for zz in (0.134, TOP - 0.094):
                    screw(p, fm @ Vector((ss, zz, 0.0055)), n, 0.003)
        for zz, h in ((0.09, 0.005), (TOP - 0.045, 0.004)):
            p.box("Kit_Seal", (0.02, zz - 0.006, -0.001), (ln - 0.02, zz + 0.006, 0.0012), m=fm, panel=False)
            p.box("Kit_GlowStrip", (0.023, zz - h / 2, 0.0005), (ln - 0.023, zz + h / 2, 0.0022), bevel=0.0008, segments=1, m=fm, panel=False)
    o, t, n, ln = _inner_frame(16.5, 17.75, 0.0)
    _label(p, "st_service", frame(o, t, Z, n) @ Vector((0.25, 0.3, 0.0056)), n, t, Z, scale=0.6)
    _label(p, "pn_2", frame(o, t, Z, n) @ Vector((0.06, TOP - 0.11, 0.0056)), n, t, Z, scale=0.6)
    # 1 the aft top: a service hatch (a framed lid, a recessed pull, four screws, its plate)
    hx0, hx1 = CX0 + 0.04, 16.62
    hu0, hu1 = inner_y(hx1) + 0.03, wall_y(hx1) - LINER - 0.03
    zt = TOP
    p.box("Kit_Seal", (hx0 - 0.004, hu0 - 0.004, zt - 0.001), (hx1 + 0.004, hu1 + 0.004, zt + 0.0008), panel=False)
    p.box("Kit_Frame", (hx0, hu0, zt), (hx1, hu1, zt + 0.012), bevel=0.004, segments=2)
    p.box("Kit_Inset", (hx0 + 0.02, hu0 + 0.02, zt + 0.011), (hx1 - 0.02, hu1 - 0.02, zt + 0.015), bevel=0.002, segments=2)
    for xx in (hx0 + 0.035, hx1 - 0.035):
        for uu in (hu0 + 0.035, hu1 - 0.035):
            screw(p, Vector((xx, uu, zt + 0.015)), Z, 0.0045)
    p.box("Kit_Seal", (hx1 - 0.16, (hu0 + hu1) / 2 - 0.015, zt + 0.008), (hx1 - 0.08, (hu0 + hu1) / 2 + 0.015, zt + 0.0152), bevel=0.003, segments=2)
    p.sweep("Kit_Lip", [Vector((hx1 - 0.15, (hu0 + hu1) / 2, zt + 0.011)), Vector((hx1 - 0.09, (hu0 + hu1) / 2, zt + 0.011))], 0.003, seg=12)
    p.box("Kit_Lip", (hx0 + 0.06, hu0 + 0.05, zt + 0.0148), (hx0 + 0.15, hu0 + 0.1, zt + 0.0162), bevel=0.0006, segments=1, panel=False)
    p.box("Kit_Legend", (hx0 + 0.062, hu0 + 0.052, zt + 0.0152), (hx0 + 0.148, hu0 + 0.098, zt + 0.0166), panel=False)
    legend(p, "SERVICE", Vector((hx0 + 0.105, hu0 + 0.081, zt + 0.0166)), X, Y, Z, h=0.009, role="Kit_Seal")
    legend(p, "HF-WC 01", Vector((hx0 + 0.105, hu0 + 0.064, zt + 0.0166)), X, Y, Z, h=0.0065, role="Kit_Seal")
    # 2 the tower beside the pilot (x 16.72 .. 17.18): its slope faces the seat with the emergency key, two rows of
    # rockers and the status bars
    tx0, tx1 = 16.72, 17.18
    yi = inner_y(tx1) + 0.012                          # never over the aisle (the inner edge leans in forward)
    yo = wall_y(tx1) - LINER + 0.01
    th = 0.24
    prof = [(yi, TOP), (yo, TOP), (yo, TOP + th), (yi + 0.11, TOP + th), (yi, TOP + 0.08)]
    end_prism(p, "Kit_Frame", prof, tx0, tx1, 0.008, 1)
    a = Vector((0.0, 0.11, th - 0.08)).normalized()    # up the slope
    r = X
    nf = r.cross(a)                                    # out of the slope, to the seat and up
    if nf.y > 0:
        r, nf = -r, -nf
    fc = Vector(((tx0 + tx1) / 2, yi + 0.055, TOP + 0.08 + (th - 0.08) / 2)) + nf * 0.0005
    ff = lambda o: frame(o, r, a, nf)                  # noqa: E731
    w2, h2 = (tx1 - tx0) / 2 - 0.02, ((0.11 ** 2 + (th - 0.08) ** 2) ** 0.5) / 2 - 0.012
    p.box("Kit_Lip", (-w2 - 0.004, -h2 - 0.004, -0.004), (w2 + 0.004, h2 + 0.004, 0.0015), bevel=0.002, segments=2, m=ff(fc))
    p.box("Kit_Inset", (-w2, -h2, -0.004), (w2, h2, 0.002), m=ff(fc), panel=False)
    for row, labs in enumerate((("PWR", "EXT LT", "ENG"), ("LIGHTS", "GEAR", "VTOL"))):
        for i, lab in enumerate(labs):
            q = fc + r * (-0.155 + 0.068 * i) + a * (0.03 - 0.062 * row) + nf * 0.002
            rocker_b(p, q, r, a, nf, lit="Kit_GlowAmber" if lab == "GEAR" else "Kit_GlowCool")
            legend(p, lab, q - a * 0.027 + nf * 0.0002, r, a, nf, h=0.0068)
    emergency_key(p, fc + r * 0.135 + a * 0.0 + nf * 0.002, r, a, nf)
    # the status bars on the tower's top, read from the seat
    sc = Vector(((tx0 + tx1) / 2, (yi + 0.11 + yo) / 2, TOP + th + 0.0005))
    p.box("Kit_Lip", (sc.x - 0.075, sc.y - 0.04, sc.z - 0.001), (sc.x + 0.075, sc.y + 0.04, sc.z + 0.003), bevel=0.0015, segments=2)
    p.box("Kit_Seal", (sc.x - 0.07, sc.y - 0.035, sc.z + 0.003), (sc.x + 0.07, sc.y + 0.035, sc.z + 0.0035), panel=False)
    fm = lambda o: frame(o, X, Y, Z)                   # noqa: E731
    for k, lab in enumerate(("MAIN", "BATT", "TEMP")):
        q = Vector((sc.x - 0.02, sc.y + 0.022 - 0.022 * k, sc.z + 0.0035))
        for gi in range(8):
            on = gi < (8, 6, 3)[k]
            x0_ = 0.004 + gi * 0.0068
            p.box(("Kit_GlowCool" if k < 2 else "Kit_GlowAmber") if on else "Kit_Inset",
                  (x0_, -0.0035, 0.0), (x0_ + 0.0055, 0.0035, 0.0007 if on else 0.0003), m=fm(q), panel=False)
        legend(p, lab, q - X * 0.026 + Z * 0.0002, X, Y, Z, h=0.007)
    _label(p, "maker", Vector(((tx0 + tx1) / 2, yo - 0.0005 - 0.0, TOP + 0.15)), Y, -X, Z, scale=0.3)
    # 3 the front top towards the dash: an intake grille in a lip
    gx0, gx1 = 17.24, 17.7
    p.box("Kit_Lip", (gx0, inner_y(gx1) + 0.015, TOP - 0.001), (gx1, wall_y(gx1) - LINER - 0.015, TOP + 0.004), bevel=0.0015, segments=2)
    k = 0
    xx = gx0 + 0.012
    while xx + 0.012 < gx1 - 0.008:
        p.box("Kit_Housing", (xx, inner_y(gx1) + 0.022, TOP + 0.004), (xx + 0.01, wall_y(gx1) - LINER - 0.022, TOP + 0.01), bevel=0.0025, segments=2, panel=False)
        xx += 0.02
    p.collision_hull([Vector((x, y, z)) for (x, y) in inner + outer for z in (0.0, TOP + 0.02)])
    p.collision_box((tx0, yi, TOP), (tx1, yo, TOP + th))
    return p


def wall_console(name, seed, mirror=False):
    return _built(_wall_console, name, seed, mirror)
