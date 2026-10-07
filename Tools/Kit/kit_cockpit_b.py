"""KF-COCKPIT-CONSOLE variant B: the left cockpit console after the 2D concept set (Docs/Kit/parts/KF-COCKPIT-CONSOLE,
author 7. 10. 2026: build it as another part in the showroom, keep variant A).

What the concept says (part.md): a light, worn metal frame with dark panels set in it, not a lacquered box; the
forearm rest a separate beam on two slanted brackets over the pedestal with a clear gap; the stick ahead of it on its
own block with the hatched boot ring; a middle block with the intake grille on top and the status strip and the keys
on its seat-facing chamfer; a raised front tower with the emergency key and the rockers; a tube grab handle with an
orange sleeve across the front. Sizes and layout are ours (1.2 x 0.67 m, the rest at elbow height 0.62 m).
One deviation from the concept: the tower's controls face the pilot (its rear slope), not the front - the concept's
front face would be out of the seated pilot's view and reach.

Local frame as variant A: x along the console, rear (the seat back) 0 -> front L; u (local y) 0 at the seat side ->
W outboard, the forearm rest overhangs u < 0; z up from the floor. (The FBX mirrors y: in Unreal the seat side is +y.)
"""
import math

from mathutils import Vector

import kit_geo
from kit_geo import frame
from kit_cockpit import stick, _label, _rocker

L, W = 1.2, 0.67
U0 = -0.03               # the pedestal's seat-side face (the beam overhangs it by 4.5 cm)
DECK = 0.44              # the pedestal's top
BEAM0, AT = 0.53, 0.62   # the forearm beam's underside and the rest's top (elbow height)
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def side_prism(p, role, pts, u0, u1, bevel, seg=3):
    """A profile in the x-z plane extruded across u from u0 to u1."""
    p.poly_prism(role, pts, frame(Vector((0, u0, 0)), (1, 0, 0), (0, 0, 1), (0, -1, 0)), u1 - u0, bevel=bevel, segments=seg)


def end_prism(p, role, pts, x0, x1, bevel, seg=3):
    """A profile in the u-z plane extruded along x from x0 to x1."""
    p.poly_prism(role, pts, frame(Vector((x1, 0, 0)), (0, 1, 0), (0, 0, 1), (1, 0, 0)), x1 - x0, bevel=bevel, segments=seg)


def screw(p, c, n, r=0.0034):
    p.lathe("Kit_Lip", [(r, 0.0), (r, 0.0007), (0.0, 0.001)], tuple(c), axis=tuple(n), seg=12)


def chamfer_panel(p, role, x0, x1, z0, z1, u, n_sign, c=0.03, depth=0.006):
    """A dark panel with one chamfered corner set into a long face (u: the face; n_sign -1 = the seat side)."""
    pts = [(x0, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1), (x0, z1)]
    if n_sign < 0:
        side_prism(p, role, pts, u - depth, u + 0.002, 0.003, 2)
    else:
        side_prism(p, role, pts, u - 0.002, u + depth, 0.003, 2)
    for xx, zz in ((x0 + 0.015, z0 + 0.015), (x0 + 0.015, z1 - 0.015), (x1 - 0.015, z1 - 0.015), (x1 - c - 0.01, z0 + 0.015)):
        screw(p, Vector((xx, u + n_sign * (depth + 0.0005), zz)), Y * n_sign)


def hatch(p, x0, x1, z0, z1, u, n_sign, step=0.022):
    """Oblique orange bars on a long face (Halcyon's hazard hatch)."""
    k = 0
    x = x0
    while x + (z1 - z0) < x1 + 1e-6:
        uu = u + n_sign * 0.0012
        p.sweep("Kit_Signal", [Vector((x, uu, z0)), Vector((x + (z1 - z0), uu, z1))], 0.004, seg=6, scale_y=0.2)
        x += step
        k += 1


def emergency_key(p, c, r, a, n):
    """The red emergency key under a flip-up red cover, framed in orange, its label plate."""
    fm = lambda o: frame(o, r, a, n)                         # noqa: E731
    p.box("Kit_Signal", (-0.04, -0.031, -0.002), (0.04, 0.031, 0.002), bevel=0.0015, segments=2, m=fm(c))
    p.box("Kit_Graphite", (-0.03, -0.021, 0.0), (0.03, 0.021, 0.007), bevel=0.003, segments=2, m=fm(c))
    p.box("Kit_Red", (-0.022, -0.014, 0.005), (0.022, 0.014, 0.011), bevel=0.0025, segments=3, m=fm(c))
    p.box("Kit_GlowRed", (-0.013, -0.002, 0.0108), (0.013, 0.002, 0.0114), m=fm(c), panel=False)
    hinge = c + a * 0.024 + n * 0.01
    p.sweep("Kit_Lip", [hinge - r * 0.033, hinge + r * 0.033], 0.0045, seg=12)
    t = math.radians(0)                                      # the cover just lifted (it stuck out over the tower)
    a2, n2 = a * math.cos(t) + n * math.sin(t), -a * math.sin(t) + n * math.cos(t)
    mc = frame(hinge, r, a2, n2)
    p.box("Kit_Red", (-0.03, 0.0, -0.0015), (0.03, 0.043, 0.0015), bevel=0.0012, segments=2, m=mc)
    for sv in (-1, 1):
        p.box("Kit_Red", (sv * 0.03 - 0.0015, 0.0, -0.0095), (sv * 0.03 + 0.0015, 0.043, 0.0), bevel=0.0007, segments=1, m=mc)
    p.box("Kit_Red", (-0.03, 0.0405, -0.0095), (0.03, 0.043, 0.0), bevel=0.0007, segments=1, m=mc)
    lp = c - a * 0.045
    p.box("Kit_Graphite", (-0.052, -0.017, 0.0), (0.052, 0.017, 0.0015), m=fm(lp), panel=False)
    _label(p, "ck_emerg_o2", lp + n * 0.0017, n, r, a, scale=0.8)


def console_b(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}   # the frame's chamfers: a glossier polished paint that catches the light
    p.sharp_deg = 20.0           # the concept's machined chamfers (25-55 deg) must not shade into soft rolls
    # 1 the pedestal: a light worn frame, the kick chamfered back, a dark recessed kick with a vent row
    ped = [(0.03, 0.07), (L - 0.06, 0.07), (L - 0.02, 0.11), (L - 0.02, DECK), (0.0, DECK), (0.0, 0.1)]
    side_prism(p, "Kit_Frame", ped, U0, W, 0.012, 1)
    p.box("Kit_Graphite", (0.05, U0 + 0.02, 0.0), (L - 0.08, W - 0.02, 0.075), bevel=0.004, segments=2)
    for k in range(14):
        xk = 0.12 + k * 0.024
        p.box("Kit_Housing", (xk, U0 + 0.016, 0.018), (xk + 0.012, U0 + 0.022, 0.055), bevel=0.002, segments=1, panel=False)
        p.box("Kit_Housing", (xk + 0.5, W - 0.026, 0.018), (xk + 0.512, W - 0.02, 0.055), bevel=0.002, segments=1, panel=False)
    # dark panels set into both long faces, a belt line over them, screws; the outboard front a hatch band and a plate
    for x0, x1 in ((0.05, 0.42), (0.45, 0.8)):
        chamfer_panel(p, "Kit_Inset", x0, x1, 0.11, DECK - 0.062, U0, -1)
        chamfer_panel(p, "Kit_Inset", x0, x1, 0.11, DECK - 0.062, W, 1)
    chamfer_panel(p, "Kit_Inset", 0.83, L - 0.08, 0.12, 0.3, U0, -1, c=0.05)
    p.box("Kit_Graphite", (0.0, U0 - 0.004, DECK - 0.052), (L - 0.02, U0, DECK - 0.046), panel=False)
    p.box("Kit_Graphite", (0.0, W, DECK - 0.052), (L - 0.02, W + 0.004, DECK - 0.046), panel=False)
    hatch(p, 0.85, L - 0.1, DECK - 0.04, DECK - 0.012, W, 1)
    p.box("Kit_Housing", (0.86, W, 0.14), (1.06, W + 0.004, 0.24), bevel=0.002, segments=1)
    _label(p, "maker", Vector((0.62, U0 - 0.0075, 0.28)), -Y, X, Z, scale=0.75)
    # the deck: a dark plate between the blocks
    p.box("Kit_Inset", (0.0, U0, DECK - 0.004), (L - 0.02, W, DECK + 0.006), bevel=0.003, segments=2)
    # 2 the forearm beam: a light frame in a stepped side profile, two padded perforated rests on it, on two slanted
    # brackets and a rear leg over the deck (the 9 cm gap under it is the concept's floating arm)
    beam = [(0.02, BEAM0), (0.58, BEAM0), (0.63, BEAM0 + 0.03), (0.63, AT - 0.035), (0.6, AT - 0.018), (0.03, AT - 0.018),
            (0.0, AT - 0.04), (0.0, BEAM0 + 0.02)]
    side_prism(p, "Kit_Frame", beam, -0.075, 0.155, 0.006, 1)
    # the stepped side: a lower band 8 mm proud on both sides, chamfered (the concept's beam is not one slab)
    band = [(0.04, BEAM0 - 0.004), (0.57, BEAM0 - 0.004), (0.6, BEAM0 + 0.022), (0.04, BEAM0 + 0.022), (0.02, BEAM0 + 0.01)]
    side_prism(p, "Kit_Inset", band, -0.083, -0.07, 0.004, 1)           # the lower band a graphite inset
    side_prism(p, "Kit_Inset", band, 0.15, 0.163, 0.004, 1)
    p.box("Kit_Graphite", (0.04, -0.0775, BEAM0 + 0.03), (0.56, -0.074, BEAM0 + 0.038), panel=False)          # the groove
    for k in range(6):
        screw(p, Vector((0.06 + k * 0.1, -0.0758, BEAM0 + 0.017)), -Y, 0.003)
    for xa, xb in ((0.035, 0.595),):
        p.box("Kit_Gasket", (xa, -0.062, AT - 0.022), (xb, 0.142, AT), bevel=0.013, segments=4)
        for a_, b_ in (((xa + 0.018, -0.045), (xb - 0.018, -0.0435)), ((xa + 0.018, 0.1235), (xb - 0.018, 0.125)),
                       ((xa + 0.018, -0.045), (xa + 0.0195, 0.125)), ((xb - 0.0195, -0.045), (xb - 0.018, 0.125))):
            p.box("Kit_Seal", (a_[0], a_[1], AT - 0.0004), (b_[0], b_[1], AT + 0.0003), panel=False)          # the stitching
        for i in range(int((xb - xa - 0.03) / 0.011)):
            for j in range(15):
                hx, hu = xa + 0.03 + i * 0.011, -0.034 + j * 0.0105 + (0.0052 if i % 2 else 0.0)
                if hu > 0.115 or hx > xb - 0.03:
                    continue
                p.box("Kit_Seal", (hx - 0.0015, hu - 0.0015, AT - 0.0004), (hx + 0.0015, hu + 0.0015, AT + 0.0002), panel=False)
    _label(p, "maker", Vector((0.4, -0.0778, AT - 0.05)), -Y, X, Z, scale=0.3)
    for k in range(2):                                         # Halcyon's mark: two slanted orange bars, 30 mm
        x_ = 0.235 + k * 0.022
        bar = [(x_, AT - 0.068), (x_ + 0.011, AT - 0.068), (x_ + 0.027, AT - 0.034), (x_ + 0.016, AT - 0.034)]
        side_prism(p, "Kit_Signal", bar, -0.078, -0.074, 0.0, 1)
    for xb in (0.2, 0.46):                                                                   # the slanted brackets
        br = [(xb - 0.03, DECK + 0.006), (xb + 0.035, DECK + 0.006), (xb + 0.065, BEAM0 + 0.002), (xb + 0.005, BEAM0 + 0.002)]
        for ua, ub in ((-0.025, 0.0), (0.105, 0.13)):
            side_prism(p, "Kit_Housing", br, ua, ub, 0.004, 2)
            hc = Vector((xb + 0.018, 0.0, (DECK + BEAM0) / 2))                         # the lightening hole
            for uu, nn in ((ua - 0.0004, -1), (ub + 0.0004, 1)):
                p.lathe("Kit_Seal", [(0.012, 0.0), (0.012, 0.0006), (0.0, 0.0006)], (hc.x, uu, hc.z), axis=(0, nn, 0), seg=20)
                p.lathe("Kit_Lip", [(0.0135, 0.0), (0.0135, 0.0004), (0.012, 0.0006)], (hc.x, uu, hc.z), axis=(0, nn, 0), seg=20)
            screw(p, Vector((xb + 0.02, ua - 0.0005, DECK + 0.03)), -Y, 0.004)
            screw(p, Vector((xb + 0.045, ua - 0.0005, BEAM0 - 0.02)), -Y, 0.004)
    rear = [(0.0, DECK), (0.075, DECK), (0.075, BEAM0 + 0.002), (0.0, BEAM0 + 0.002)]
    side_prism(p, "Kit_Frame", rear, -0.025, 0.14, 0.008, 1)
    p.box("Kit_Perforated", (0.015, -0.0275, DECK + 0.02), (0.06, -0.023, BEAM0 - 0.02), panel=False)
    # 3 the stick block: a light block, a dark top plate, the stick with its hatched boot ring; a mesh grille on its side
    sb = [(0.66, DECK), (0.87, DECK), (0.87, 0.49), (0.85, 0.505), (0.68, 0.505), (0.66, 0.49)]
    side_prism(p, "Kit_Frame", sb, U0 - 0.012, 0.18, 0.006, 1)
    p.box("Kit_Housing", (0.69, U0 + 0.005, 0.503), (0.84, 0.165, 0.509), bevel=0.003, segments=2)
    p.box("Kit_Perforated", (0.69, U0 - 0.0145, DECK + 0.015), (0.84, U0 - 0.011, 0.485), panel=False)
    for xx in (0.68, 0.85):
        screw(p, Vector((xx, U0 - 0.0125, DECK + 0.012)), -Y)
        screw(p, Vector((xx, U0 - 0.0125, 0.488)), -Y)
    stick(p, Vector((0.765, 0.075, 0.509)), "ck_rcs", head_role="Kit_Frame", guard="d")      # a worn metal head (concept)
    for xf, nx in ((0.66, -1), (0.87, 1)):                     # graphite insets on the block's ends, 15 mm frame
        p.box("Kit_Inset", (xf - 0.002 if nx > 0 else xf - 0.004, U0 + 0.003, DECK + 0.015),
              (xf + 0.004 if nx > 0 else xf + 0.002, 0.165, 0.475), bevel=0.002, segments=1)
        for uu in (U0 + 0.012, 0.156):
            screw(p, Vector((xf + nx * 0.0045, uu, 0.466)), X * nx, 0.003)
    # 4 the middle block: the intake grille on top, the status strip and the 2 x 2 keys on its seat-facing chamfer
    mb = [(0.2, DECK), (W - 0.005, DECK), (W - 0.005, 0.52), (0.34, 0.52), (0.2, 0.455)]
    end_prism(p, "Kit_Frame", mb, 0.64, 0.98, 0.006, 1)
    p.box("Kit_Lip", (0.68, 0.38, 0.52), (0.94, 0.62, 0.524), bevel=0.0015, segments=2)
    p.box("Kit_Graphite", (0.687, 0.387, 0.524), (0.933, 0.613, 0.5245), panel=False)
    for k in range(10):
        xk = 0.693 + k * 0.0236
        p.box("Kit_Housing", (xk, 0.393, 0.5245), (xk + 0.012, 0.607, 0.531), bevel=0.0025, segments=2, panel=False)
    chamfer_panel(p, "Kit_Inset", 0.67, 0.95, DECK + 0.02, 0.5, W - 0.005, 1, c=0.03)
    d = Vector((0, 0.14, 0.065)).normalized()                 # up the chamfer
    n = X.cross(d)                                            # out of it, to the seat and up
    c0 = Vector((0.0, 0.27, 0.4875)) + n * 0.0005
    fm = lambda o: frame(o, X, d, n)                          # noqa: E731
    p.box("Kit_Housing", (-0.0, -0.06, -0.004), (0.32, 0.06, 0.003), bevel=0.003, segments=2, m=fm(c0 + X * 0.65))
    sc = c0 + X * 0.73                                        # the status strip: three lamps, legends beside them
    p.box("Kit_Lip", (-0.07, -0.042, 0.002), (0.07, 0.042, 0.005), bevel=0.0015, segments=2, m=fm(sc))
    p.box("Kit_Seal", (-0.065, -0.037, 0.005), (0.065, 0.037, 0.0055), m=fm(sc), panel=False)
    for k, lab in enumerate(("ck_main", "ck_batt", "ck_temp")):
        q = sc + d * (0.022 - 0.022 * k)
        p.box("Kit_GlowFoot" if k < 2 else "Kit_GlowAmber", (0.005, -0.004, 0.0055), (0.055, 0.004, 0.0065), m=fm(q), panel=False)
        _label(p, lab, q - X * 0.03 + n * 0.0058, n, X, d, scale=0.62)
    kc = c0 + X * 0.89                                         # the keys
    p.box("Kit_Lip", (-0.055, -0.05, 0.002), (0.055, 0.05, 0.005), bevel=0.0015, segments=2, m=fm(kc))
    p.box("Kit_Graphite", (-0.05, -0.045, 0.005), (0.05, 0.045, 0.006), m=fm(kc), panel=False)
    for i, lab in enumerate(("ck_lights", "ck_gear", "ck_vtol", "ck_esp")):
        q = kc + X * (0.024 * (1 if i % 2 else -1)) + d * (0.021 * (1 if i < 2 else -1))
        p.box("Kit_Seal", (-0.0235, -0.021, 0.006), (0.0235, 0.021, 0.0098), bevel=0.001, segments=1, m=fm(q))
        p.box("Kit_Housing", (-0.019, -0.017, 0.006), (0.019, 0.017, 0.01), bevel=0.002, segments=2, m=fm(q))
        # a gradient: the cap's rim on the dimmer cool glow, a brighter warm centre a hair proud
        p.box("Kit_GlowCool", (-0.016, -0.014, 0.01), (0.016, 0.014, 0.0135), bevel=0.0015, segments=2, m=fm(q))
        p.box("Kit_GlowKey", (-0.0105, -0.0085, 0.0135), (0.0105, 0.0085, 0.0139), m=fm(q), panel=False)
    for xx in (0.665, 0.955):
        screw(p, c0 + X * xx + d * 0.04 + n * 0.003, n)
        screw(p, c0 + X * xx - d * 0.04 + n * 0.003, n)
    # 5 the front tower: its rear slope faces the pilot with the emergency key and the rockers, LEDs over them
    TU = 0.27                                                  # the tower's seat-side face
    tw = [(0.98, DECK), (L - 0.02, DECK), (L - 0.02, 0.7), (L - 0.05, 0.74), (1.115, 0.74), (0.98, 0.5)]
    side_prism(p, "Kit_Frame", tw, TU, W - 0.005, 0.006, 1)
    a = Vector((0.135, 0, 0.24)).normalized()                 # up the slope (forward and up, ~30 deg off vertical)
    r = Vector((0, -1, 0))                                     # the pilot's right on it (toward the seat side... mirrored)
    nf = r.cross(a)                                            # out of it: back to the pilot and up
    if nf.x > 0:
        r, nf = -r, -nf
    fc = Vector((1.0475, (TU + W - 0.005) / 2, 0.62)) + nf * 0.0005
    ff = lambda o: frame(o, r, a, nf)                          # noqa: E731
    w2, h2 = (W - 0.005 - TU - 0.04) / 2, 0.125
    p.box("Kit_Lip", (-w2 - 0.004, -h2 - 0.004, -0.004), (w2 + 0.004, h2 + 0.004, 0.0015), bevel=0.002, segments=2, m=ff(fc))
    p.box("Kit_Inset", (-w2, -h2, -0.004), (w2, h2, 0.002), m=ff(fc), panel=False)
    emergency_key(p, fc + a * 0.025 + nf * 0.002, r, a, nf)
    for i, lab in enumerate(("ck_pwr", "ck_extlt", "ck_eng")):
        q = fc - a * 0.078 + r * (0.105 * (i - 1)) + nf * 0.002
        p.box("Kit_Lip", (-0.016, -0.024, 0.0), (0.016, 0.03, 0.0015), bevel=0.001, segments=1, m=ff(q), panel=False)   # its frame
        _rocker(p, q, r, a, nf, lab, label_scale=1.1)
        p.box("Kit_GlowKey", (-0.008, 0.021, 0.0015), (0.008, 0.0265, 0.0027), m=ff(q), panel=False)
    for su in (-1, 1):
        for sv in (-1, 1):
            screw(p, fc + r * (su * (w2 - 0.012)) + a * (sv * (h2 - 0.012)) + nf * 0.002, nf)
    p.box("Kit_Graphite", (1.131, TU + 0.02, 0.7395), (1.134, W - 0.025, 0.7408), panel=False)            # the top's seam
    for uf, ns_ in ((TU, -1), (W - 0.005, 1)):
        # the inset follows the side's outline 20 mm in: the slope edge leans with the face
        ins = [(1.0, DECK + 0.02), (L - 0.04, DECK + 0.02), (L - 0.04, 0.68), (1.115, 0.72), (1.0, 0.53)]
        if ns_ < 0:
            side_prism(p, "Kit_Inset", ins, uf - 0.004, uf + 0.002, 0.002, 1)
        else:
            side_prism(p, "Kit_Inset", ins, uf - 0.002, uf + 0.004, 0.002, 1)
        for xx, zz in ((1.015, DECK + 0.035), (L - 0.055, DECK + 0.035), (L - 0.055, 0.665), (1.015, 0.52)):
            screw(p, Vector((xx, uf + ns_ * 0.0045, zz)), Y * ns_)
    # the Halcyon mark and name on the tower's outboard inset (the side the hull lights)
    for k in range(2):
        x_ = 1.008 + k * 0.016
        p.sweep("Kit_Signal", [Vector((x_, W + 0.0041, 0.47)), Vector((x_ + 0.012, W + 0.0041, 0.5))], 0.005, seg=6, scale_y=0.25)
    _label(p, "maker", Vector((1.105, W + 0.0045, 0.485)), Y, -X, Z, scale=0.18)
    p.box("Kit_Inset", (L - 0.026, TU + 0.025, DECK + 0.025), (L - 0.016, W - 0.03, 0.672), bevel=0.003, segments=1)
    for uu, zz in ((TU + 0.038, DECK + 0.038), (W - 0.043, DECK + 0.038), (TU + 0.038, 0.66), (W - 0.043, 0.66)):
        screw(p, Vector((L - 0.0155, uu, zz)), X, 0.004)
    for k in range(2):
        u_ = TU + 0.06 + k * 0.02
        mark = [(u_, 0.6), (u_ + 0.009, 0.6), (u_ + 0.023, 0.632), (u_ + 0.014, 0.632)]
        p.poly_prism("Kit_Signal", mark, frame(Vector((L - 0.0125, 0, 0)), (0, 1, 0), (0, 0, 1), (1, 0, 0)), 0.004, bevel=0.0)
    _label(p, "maker", Vector((L - 0.0145, TU + 0.23, 0.615)), X, Y, Z, scale=0.38)
    # the front's hazard band: one 38 mm band in a 2 mm black frame, 9 mm orange bars at 45 deg with 9 mm gaps, clipped
    fz0, fz1, fu0, fu1 = 0.496, 0.534, TU + 0.05, W - 0.06
    fmh = frame(Vector((L - 0.0145, 0, 0)), (0, 1, 0), (0, 0, 1), (1, 0, 0))
    p.box("Kit_Seal", (L - 0.0162, fu0 - 0.002, fz0 - 0.002), (L - 0.0148, fu1 + 0.002, fz1 + 0.002), panel=False)
    hgt = fz1 - fz0
    uu = fu0 - hgt
    while uu < fu1:
        poly = [(uu, fz0), (uu + 0.009, fz0), (uu + 0.009 + hgt, fz1), (uu + hgt, fz1)]
        if poly[0][0] >= fu0 and poly[2][0] <= fu1:              # whole bars only (clipped ends read as slivers)
            p.poly_prism("Kit_Signal", poly, fmh, 0.0004, bevel=0.0)
        uu += 0.018
    # the pedestal's front under the switch module: a graphite inset, its vent and a hazard band
    p.box("Kit_Inset", (L - 0.026, U0 + 0.02, 0.13), (L - 0.016, TU - 0.02, DECK - 0.03), bevel=0.003, segments=1)
    p.box("Kit_Perforated", (L - 0.0165, U0 + 0.04, 0.16), (L - 0.0155, TU - 0.04, 0.24), panel=False)
    for uu in (U0 + 0.033, TU - 0.033):
        for zz in (0.143, DECK - 0.043):
            screw(p, Vector((L - 0.0155, uu, zz)), X, 0.0035)
    # 6 the grab handle: a dark tube across the front on two blocks, an orange knurled sleeve
    hz = 0.47
    hp = [Vector((L - 0.02, 0.13, hz)), Vector((L + 0.045, 0.13, hz)), Vector((L + 0.07, 0.16, hz)), Vector((L + 0.07, W - 0.16, hz)),
          Vector((L + 0.045, W - 0.13, hz)), Vector((L - 0.02, W - 0.13, hz))]
    p.sweep("Kit_Housing", hp, 0.015, seg=16)
    p.sweep("Kit_Grip", [Vector((L + 0.07, 0.2, hz)), Vector((L + 0.07, W - 0.2, hz))], 0.0185, seg=24)
    for uu in (0.2, W - 0.2):
        p.lathe("Kit_Housing", [(0.021, -0.008), (0.021, 0.008), (0.0, 0.008)], (L + 0.07, uu, hz), axis=(0, 1, 0), seg=16)
    for uu in (0.212, W - 0.212):                               # polished end rings
        p.lathe("Kit_Lip", [(0.0195, -0.003), (0.0195, 0.003), (0.0, 0.003)], (L + 0.07, uu, hz), axis=(0, 1, 0), seg=24)
    for uu in (0.13, W - 0.13):
        p.box("Kit_Housing", (L - 0.03, uu - 0.025, hz - 0.03), (L + 0.0, uu + 0.025, hz + 0.03), bevel=0.005, segments=2)
    # 7a the front deck by the seat, ahead of the stick: a small switch module - a sloped dark plate in a light frame,
    # three guarded toggles (the guards two bent bars), their legends, a status LED each
    m0 = Vector((1.03, 0.095, DECK))
    mod = [(-0.05, 0.0), (0.12, 0.0), (0.12, 0.06), (-0.05, 0.03)]   # (u, z): its top slopes down to the seat
    end_prism(p, "Kit_Frame", [(m0.y + a_, m0.z + b_) for a_, b_ in mod], 0.92, 1.15, 0.005, 1)
    sd_ = Vector((0, 0.17, 0.03)).normalized()
    ns = X.cross(sd_)
    if ns.z < 0:
        ns = -ns
    pc = Vector((1.035, m0.y + 0.035, m0.z + 0.045)) + ns * 0.0005
    fs_ = lambda o: frame(o, X, sd_, ns)                       # noqa: E731
    p.box("Kit_Graphite", (-0.1, -0.026, -0.002), (0.1, 0.026, 0.002), m=fs_(pc), panel=False)
    for k, lab in enumerate(("ck_lights", "ck_gear", "ck_vtol")):
        q = Vector((0.06 * (k - 1), 0.0, 0.0))
        p.box("Kit_Lip", q + Vector((-0.009, -0.012, 0.002)), q + Vector((0.009, 0.004, 0.005)), bevel=0.0015, segments=2, m=fs_(pc))
        p.sweep("Kit_Lip", [fs_(pc) @ (q + Vector((0.0, -0.004, 0.005))), fs_(pc) @ (q + Vector((0.0, 0.006, 0.019)))], 0.0022, seg=8)
        for sv in (-1, 1):
            p.sweep("Kit_Housing", [fs_(pc) @ (q + Vector((sv * 0.013, -0.012, 0.002))), fs_(pc) @ (q + Vector((sv * 0.013, -0.008, 0.022))),
                                    fs_(pc) @ (q + Vector((sv * 0.013, 0.004, 0.022)))], 0.0018, seg=6)
        p.box("Kit_GlowKey" if k != 1 else "Kit_GlowAmber", q + Vector((-0.004, 0.012, 0.002)), q + Vector((0.004, 0.016, 0.003)),
              m=fs_(pc), panel=False)
        _label(p, lab, fs_(pc) @ (q + Vector((0.0, -0.019, 0.0021))), ns, X, sd_, scale=0.5)
    # 7b the rear deck outboard of the beam: a service hatch (a raised lid in a dark seam, a recessed pull, two
    # quarter-turn latches, its stencils) - the concept has no empty board
    hx0, hx1, hu0, hu1 = 0.06, 0.58, 0.2, W - 0.04
    p.box("Kit_Graphite", (hx0 - 0.006, hu0 - 0.006, DECK + 0.004), (hx1 + 0.006, hu1 + 0.006, DECK + 0.008), panel=False)
    lid = [(hu0, DECK), (hu1, DECK), (hu1, DECK + 0.018), (hu1 - 0.012, DECK + 0.026), (hu0 + 0.012, DECK + 0.026), (hu0, DECK + 0.018)]
    end_prism(p, "Kit_Frame", lid, hx0, hx1, 0.003, 1)
    zt = DECK + 0.026
    p.box("Kit_Inset", (hx0 + 0.022, hu0 + 0.022, zt - 0.002), (hx1 - 0.022, hu1 - 0.022, zt + 0.006), bevel=0.004, segments=1)
    zt += 0.006
    for xx in (hx0 + 0.035, hx1 - 0.035):
        for uu in (hu0 + 0.035, hu1 - 0.035):
            screw(p, Vector((xx, uu, zt)), Z, 0.0045)
    p.box("Kit_Lip", (hx1 - 0.13, hu0 + 0.05, zt - 0.001), (hx1 - 0.046, hu0 + 0.094, zt + 0.0012), bevel=0.001, segments=1)
    p.box("Kit_Perforated", (hx1 - 0.126, hu0 + 0.054, zt + 0.0012), (hx1 - 0.05, hu0 + 0.09, zt + 0.0016), panel=False)
    p.box("Kit_Seal", (0.27, hu1 - 0.075, zt - 0.012), (0.37, hu1 - 0.045, zt + 0.0003), bevel=0.004, segments=2)        # the pull
    p.box("Kit_Lip", (0.28, hu1 - 0.07, zt - 0.006), (0.36, hu1 - 0.065, zt - 0.002), bevel=0.0015, segments=2)
    for xx in (hx0 + 0.05, hx1 - 0.16):
        c = Vector((xx, (hu0 + hu1) / 2, zt))
        p.lathe("Kit_Lip", [(0.011, 0.0), (0.011, 0.0015), (0.009, 0.0025)], tuple(c), seg=20)
        p.box("Kit_Graphite", (xx - 0.0075, (hu0 + hu1) / 2 - 0.0015, zt + 0.0015), (xx + 0.0075, (hu0 + hu1) / 2 + 0.0015, zt + 0.0035), panel=False)
    _label(p, "st_service", Vector((0.22, hu0 + 0.06, zt + 0.0004)), Z, X, Y, scale=0.7)       # read from the seat
    _label(p, "arrow_access", Vector((0.32, hu1 - 0.1, zt + 0.0004)), Z, X, Y, scale=0.5)
    _label(p, "pn_4", Vector((0.48, hu0 + 0.06, zt + 0.0004)), Z, X, Y, scale=0.6)
    # 7c the decal layers (author 8. 10.: the parts are new from the factory - no wear; the richness is stacked detail):
    # stencils, labels and ids on the graphite insets, rivet rows on the frame band, a socket and a hazard band on the
    # front, plates on the outboard side - each fully on one flat face
    zb = 0.41                                                   # the frame band between the insets and the belt line
    det = [("st_inspect", (0.24, U0 - 0.0065, 0.19), -Y, X, 0.7), ("st_service", (0.27, U0 - 0.0065, 0.29), -Y, X, 0.7),
           ("pn_1", (0.1, U0 - 0.0065, DECK - 0.1), -Y, X, 0.7), ("pn_2", (0.5, U0 - 0.0065, DECK - 0.1), -Y, X, 0.7),
           ("warn_hv", (0.63, U0 - 0.0065, 0.25), -Y, X, 0.7), ("st_hfcl", (0.63, U0 - 0.0065, 0.17), -Y, X, 0.7),
           ("rivet_row_8", (0.24, U0 - 0.0005, zb), -Y, X, 0.8), ("rivet_row_8", (0.63, U0 - 0.0005, zb), -Y, X, 0.8),
           ("rivet_row_8", (0.24, W + 0.0005, zb), Y, -X, 0.8), ("rivet_row_8", (0.63, W + 0.0005, zb), Y, -X, 0.8),
           ("label_coolant", (0.24, W + 0.0065, 0.2), Y, -X, 0.8), ("st_torque", (0.25, W + 0.0065, 0.33), Y, -X, 0.6),
           ("warning_label", (0.62, W + 0.0065, 0.22), Y, -X, 0.8), ("st_gnd", (0.62, W + 0.0065, 0.32), Y, -X, 0.8),
           ("tri_warning", (1.11, TU - 0.0065, 0.5), -Y, X, 0.6), ("panel_B07", (1.1, W + 0.0045, 0.6), Y, -X, 0.6),
           ("socket", (L - 0.0155, (U0 + TU) / 2, 0.33), X, Y, 0.8),
           ("hazard_subtle", (L - 0.0195, (TU + W) / 2, 0.39), X, Y, 0.9), ("panel_A12", (L - 0.0195, (TU + W) / 2, 0.2), X, Y, 0.8),
           ("corner_mark", (0.9, 0.0, DECK + 0.0065), Z, X, 0.6), ("label_power", (0.94, U0 - 0.0005, 0.22), -Y, X, 0.6),
           ("ck_maker_plate", (0.96, W + 0.0045, 0.19), Y, -X, 0.9)]
    for item, at, nn, rr, sc_ in det:
        nn = Vector(nn)
        up = Z if abs(nn.z) < 0.5 else Y                       # right x up = the normal (a right-handed decal frame)
        _label(p, item, Vector(at), nn, Vector(rr), up, scale=sc_, is_label=item.startswith(("st_", "pn_", "label_", "warning", "tri_", "warn_", "panel_", "ck_")))
    p.collision_box((0.0, -0.08, 0.0), (L + 0.09, W + 0.005, 0.68))
    return p
