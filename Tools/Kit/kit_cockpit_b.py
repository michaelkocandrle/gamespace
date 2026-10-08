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


def legend(p, body, c, r, a, n, h=0.008, role="Kit_Legend", depth=0.0003, font="Content/UI/Fonts/Rajdhani-SemiBold.ttf"):
    """Printed lettering as geometry, centred on c in the face frame (r right, a up, n out), cap height ~h: crisp at any
    distance, white - the library decals' small grey type did not read from the seat (critic r20-23)."""
    import os
    import bpy
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cu = bpy.data.curves.new("legend", "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(os.path.join(root, font), check_existing=True)
    cu.size = h * 1.45                                      # Rajdhani's caps are ~0.69 em
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = depth / 2
    cu.resolution_u = 3
    ob = bpy.data.objects.new("legend", cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    verts = [tuple(c + r * v.co.x + a * v.co.y + n * (v.co.z + depth / 2)) for v in me.vertices]
    faces = [list(f.vertices) for f in me.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)
    for f in p.mesh(role, verts, faces):
        f.smooth = False


def led(p, c, n, glow="Kit_GlowKey", r=0.003):
    """A status LED: a polished ring, a glowing dome proud of it, a faint halo ring round it."""
    p.lathe("Kit_Lip", [(r + 0.0022, 0.0), (r + 0.0022, 0.0011), (r + 0.0008, 0.0013)], tuple(c), axis=tuple(n), seg=20)
    p.lathe(glow, [(r, 0.0), (r, 0.0008), (r * 0.7, 0.0019), (0.0, 0.0025)], tuple(c + n * 0.0011), axis=tuple(n), seg=20)
    p.lathe("Kit_GlowCool" if glow != "Kit_GlowAmber" else "Kit_GlowSignal",
            [(r + 0.0045, 0.0), (r + 0.0045, 0.0002), (r + 0.0026, 0.0002), (r + 0.0026, 0.0)], tuple(c + n * 0.0001), axis=tuple(n), seg=24)


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
    p.box("Kit_Signal", (-0.03, -0.0095, 0.0), (0.03, 0.0095, 0.0012), m=fm(lp), panel=False)
    legend(p, "EMER", lp + n * 0.0012, r, a, n, h=0.011, role="Kit_Seal")


def console_b(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}   # the frame's chamfers: a glossier polished paint that catches the light
    p.sharp_deg = 20.0           # the concept's machined chamfers (25-55 deg) must not shade into soft rolls
    # 1 the pedestal: a light worn frame, the kick chamfered back, a dark recessed kick with a vent row
    ped = [(0.03, 0.07), (L - 0.1, 0.07), (L - 0.02, 0.15), (L - 0.02, DECK), (0.0, DECK), (0.0, 0.1)]   # an 80 mm 45 deg cut at the front foot
    side_prism(p, "Kit_Frame", ped, U0, W, 0.012, 1)
    p.box("Kit_Graphite", (0.05, U0 + 0.02, 0.0), (L - 0.08, W - 0.02, 0.075), bevel=0.004, segments=2)
    for k in range(14):
        xk = 0.12 + k * 0.024
        p.box("Kit_Housing", (xk, U0 + 0.016, 0.018), (xk + 0.012, U0 + 0.022, 0.055), bevel=0.002, segments=1, panel=False)
        p.box("Kit_Housing", (xk + 0.5, W - 0.026, 0.018), (xk + 0.512, W - 0.02, 0.055), bevel=0.002, segments=1, panel=False)
    # dark panels set into both long faces, a belt line over them, screws; the outboard front a hatch band and a plate
    for x0, x1 in ((0.05, 0.29), (0.294, 0.545), (0.549, 0.8)):        # three panels, 4 mm seams between them
        chamfer_panel(p, "Kit_Inset", x0, x1, 0.11, DECK - 0.062, U0, -1)
        chamfer_panel(p, "Kit_Inset", x0, x1, 0.11, DECK - 0.062, W, 1)
    chamfer_panel(p, "Kit_Inset", 0.83, L - 0.08, 0.12, 0.3, U0, -1, c=0.05)
    p.box("Kit_Graphite", (0.0, U0 - 0.004, DECK - 0.052), (L - 0.02, U0, DECK - 0.046), panel=False)
    p.box("Kit_Graphite", (0.0, W, DECK - 0.052), (L - 0.02, W + 0.004, DECK - 0.046), panel=False)
    hatch(p, 0.85, L - 0.1, DECK - 0.04, DECK - 0.012, W, 1)
    p.box("Kit_Housing", (0.86, W, 0.14), (1.06, W + 0.004, 0.24), bevel=0.002, segments=1)
    _label(p, "maker", Vector((0.44, U0 - 0.0065, 0.14)), -Y, X, Z, scale=0.3)
    # the deck: a dark plate between the blocks
    p.box("Kit_Inset", (0.0, U0, DECK - 0.004), (L - 0.02, W, DECK + 0.006), bevel=0.003, segments=2)
    # 2 the forearm beam: a light frame in a stepped side profile, two padded perforated rests on it, on two slanted
    # brackets and a rear leg over the deck (the 9 cm gap under it is the concept's floating arm)
    beam = [(0.02, BEAM0), (0.58, BEAM0), (0.63, BEAM0 + 0.03), (0.63, AT - 0.035), (0.6, AT - 0.018), (0.03, AT - 0.018),
            (0.0, AT - 0.04), (0.0, BEAM0 + 0.02)]
    side_prism(p, "Kit_Frame", beam, -0.075, 0.155, 0.009, 1)
    # the stepped side: a lower band 8 mm proud on both sides, chamfered (the concept's beam is not one slab)
    band = [(0.04, BEAM0 - 0.004), (0.57, BEAM0 - 0.004), (0.6, BEAM0 + 0.022), (0.04, BEAM0 + 0.022), (0.02, BEAM0 + 0.01)]
    side_prism(p, "Kit_Inset", band, -0.083, -0.07, 0.004, 1)           # the lower band a graphite inset
    side_prism(p, "Kit_Inset", band, 0.15, 0.163, 0.004, 1)
    for xa, xb in ((0.05, 0.3), (0.32, 0.57)):                 # the beam side's two graphite sub-panels, screwed
        p.box("Kit_Inset", (xa, -0.079, BEAM0 + 0.026), (xb, -0.0745, AT - 0.025), bevel=0.0015, segments=1)
        for xx in (xa + 0.008, xb - 0.008):
            for zz in (BEAM0 + 0.031, AT - 0.03):
                screw(p, Vector((xx, -0.0795, zz)), -Y, 0.0022)
    for k in range(6):
        screw(p, Vector((0.06 + k * 0.1, -0.0758, BEAM0 + 0.017)), -Y, 0.003)
    for xa, xb in ((0.035, 0.313), (0.317, 0.595)):
        p.box("Kit_Leather", (xa, -0.062, AT - 0.022), (xb, 0.142, AT), bevel=0.013, segments=4)
        p.box("Kit_Leather", (xa + 0.012, -0.05, AT - 0.004), (xb - 0.012, 0.13, AT + 0.005), bevel=0.009, segments=4)   # the dome
        sx0, sx1, su0, su1 = xa + 0.024, xb - 0.024, -0.038, 0.118          # the stitching on the dome's flat: 4 mm stitches, 2 mm apart
        for (p0, p1) in (((sx0, su0), (sx1, su0)), ((sx0, su1), (sx1, su1)), ((sx0, su0), (sx0, su1)), ((sx1, su0), (sx1, su1))):
            ln = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
            p.box("Kit_Seal", (min(p0[0], p1[0]) - 0.0013, min(p0[1], p1[1]) - 0.0013, AT + 0.0040),     # the stitch's dark channel
                  (max(p0[0], p1[0]) + 0.0013, max(p0[1], p1[1]) + 0.0013, AT + 0.0052), panel=False)
            k = 0
            while k * 0.006 + 0.004 <= ln:
                t0, t1 = k * 0.006 / ln, (k * 0.006 + 0.004) / ln
                a0 = (p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0)
                a1 = (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)
                p.box("Kit_Housing", (min(a0[0], a1[0]) - 0.0006, min(a0[1], a1[1]) - 0.0006, AT + 0.0042),     # a grey thread
                      (max(a0[0], a1[0]) + 0.0006, max(a0[1], a1[1]) + 0.0006, AT + 0.0056), panel=False)
                k += 1
        for i in range(int((xb - xa - 0.09) / 0.006) + 1):          # 1.6 mm holes at 6 mm, a middle band 40 mm wide
            for j in range(7):
                hx, hu = xa + 0.045 + i * 0.006, 0.022 + j * 0.006 + (0.003 if i % 2 else 0.0)
                if hu > 0.062 or hx > xb - 0.045:
                    continue
                p.box("Kit_Seal", (hx - 0.001, hu - 0.001, AT + 0.0046), (hx + 0.001, hu + 0.001, AT + 0.0053), panel=False)
    _label(p, "maker", Vector((0.445, -0.0796, BEAM0 + 0.045)), -Y, X, Z, scale=0.3)
    for ua in (-0.066, 0.14):                                  # a hidden 6 mm light strip under each beam edge, washing the gap
        p.box("Kit_Seal", (0.07, ua - 0.002, BEAM0 - 0.004), (0.55, ua + 0.008, BEAM0), panel=False)
        p.box("Kit_Lip", (0.072, ua - 0.004, BEAM0 - 0.006), (0.548, ua + 0.01, BEAM0 - 0.003), bevel=0.001, segments=1, panel=False)   # a polished bezel
        p.box("Kit_GlowCool", (0.075, ua - 0.001, BEAM0 - 0.0085), (0.545, ua + 0.007, BEAM0 - 0.0055), bevel=0.0015, segments=2, panel=False)  # 8 mm diffuser
    for k, gl in enumerate(("Kit_GlowCool", "Kit_GlowCool", "Kit_GlowAmber")):      # status LEDs on the beam's front end
        uu = -0.03 + k * 0.025
        p.lathe("Kit_Lip", [(0.0045, 0.0), (0.0045, 0.0012), (0.0032, 0.0014)], (0.63, uu, AT - 0.05), axis=(1, 0, 0), seg=16)
        p.lathe(gl, [(0.003, 0.0), (0.003, 0.0012), (0.002, 0.0024), (0.0, 0.0028)], (0.6312, uu, AT - 0.05), axis=(1, 0, 0), seg=16)
    _label(p, "st_hfcl", Vector((0.18, -0.0796, BEAM0 + 0.045)), -Y, X, Z, scale=0.5)
    for k in range(2):                                         # Halcyon's mark: two slanted orange bars, 30 mm
        x_ = 0.335 + k * 0.016
        bar = [(x_, BEAM0 + 0.031), (x_ + 0.008, BEAM0 + 0.031), (x_ + 0.018, BEAM0 + 0.059), (x_ + 0.010, BEAM0 + 0.059)]
        side_prism(p, "Kit_Signal", bar, -0.0805, -0.0785, 0.0, 1)
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
    side_prism(p, "Kit_Frame", sb, U0 - 0.012, 0.18, 0.009, 1)
    p.box("Kit_Housing", (0.69, U0 + 0.005, 0.503), (0.84, 0.165, 0.509), bevel=0.003, segments=2)
    p.box("Kit_Perforated", (0.69, U0 - 0.0145, DECK + 0.015), (0.84, U0 - 0.011, 0.485), panel=False)
    for xx in (0.68, 0.85):
        screw(p, Vector((xx, U0 - 0.0125, DECK + 0.012)), -Y)
        screw(p, Vector((xx, U0 - 0.0125, 0.488)), -Y)
    stick(p, Vector((0.765, 0.075, 0.509)), "ck_rcs", head_role="Kit_Gasket", guard="d", plate_role="Kit_Inset",
          ball_role="Kit_Gasket", bars=15)      # a graphite base, a rubber gimbal boot, 9 mm hatch bars
    for xf, nx in ((0.66, -1), (0.87, 1)):                     # graphite insets on the block's ends, 15 mm frame
        p.box("Kit_Inset", (xf - 0.002 if nx > 0 else xf - 0.004, U0 + 0.003, DECK + 0.015),
              (xf + 0.004 if nx > 0 else xf + 0.002, 0.165, 0.475), bevel=0.002, segments=1)
        for uu in (U0 + 0.012, 0.156):
            screw(p, Vector((xf + nx * 0.0045, uu, 0.466)), X * nx, 0.003)
    # 4 the middle block: the intake grille on top, the status strip and the 2 x 2 keys on its seat-facing chamfer
    mb = [(0.2, DECK), (W - 0.005, DECK), (W - 0.005, 0.52), (0.34, 0.52), (0.2, 0.455)]
    end_prism(p, "Kit_Frame", mb, 0.64, 0.98, 0.009, 1)
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
        p.box("Kit_GlowCool" if k < 2 else "Kit_GlowAmber", (0.005, -0.004, 0.0055), (0.055, 0.004, 0.0065), m=fm(q), panel=False)
        legend(p, {"ck_main": "MAIN", "ck_batt": "BATT", "ck_temp": "TEMP"}[lab], q - X * 0.03 + n * 0.0057, X, d, n, h=0.0075)
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
        legend(p, {"ck_lights": "LT", "ck_gear": "GR", "ck_vtol": "VT", "ck_esp": "ESP"}[lab], fm(q) @ Vector((0.0, 0.0, 0.0139)), X, d, n, h=0.0065, role="Kit_Seal")
    for xx in (0.665, 0.955):
        screw(p, c0 + X * xx + d * 0.04 + n * 0.003, n)
        screw(p, c0 + X * xx - d * 0.04 + n * 0.003, n)
    # 5 the front tower: its rear slope faces the pilot with the emergency key and the rockers, LEDs over them
    TU = 0.27                                                  # the tower's seat-side face
    tw = [(0.98, DECK), (L - 0.02, DECK), (L - 0.02, 0.7), (L - 0.05, 0.74), (1.115, 0.74), (0.98, 0.5)]
    side_prism(p, "Kit_Frame", tw, TU, W - 0.005, 0.009, 1)
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
        _rocker(p, q, r, a, nf, lab, label_scale=0, index=False)
        legend(p, {"ck_pwr": "PWR", "ck_extlt": "EXT LT", "ck_eng": "ENG"}[lab], q - a * 0.034 + nf * 0.0002, r, a, nf, h=0.008)
        led(p, ff(q) @ Vector((0.0, 0.0245, 0.0015)), nf)
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
    # the tower's seat-side inset (the biggest face the pilot sees): a polished-frame plate, a row of vent slots, stencils
    uf_ = TU - 0.0045
    p.box("Kit_Lip", (1.019, uf_ - 0.0012, 0.528), (1.085, uf_ + 0.001, 0.568), bevel=0.0006, segments=1, panel=False)
    p.box("Kit_Graphite", (1.022, uf_ - 0.0016, 0.531), (1.082, uf_ - 0.0011, 0.565), panel=False)
    legend(p, "HF-3287", Vector((1.052, uf_ - 0.0016, 0.5545)), X, Z, -Y, h=0.0095)
    legend(p, "L ARM", Vector((1.052, uf_ - 0.0016, 0.5395)), X, Z, -Y, h=0.0068)
    for k in range(8):
        xk = 1.03 + k * 0.014
        p.box("Kit_Seal", (xk, uf_ - 0.0005, DECK + 0.035), (xk + 0.004, uf_ + 0.001, DECK + 0.075), bevel=0.0008, segments=1, panel=False)
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
    gu0, gz0 = W - 0.12, 0.545                                     # a framed grille sub-panel, 70 x 45 mm
    p.box("Kit_Lip", (L - 0.0165, gu0 - 0.003, gz0 - 0.003), (L - 0.0135, gu0 + 0.073, gz0 + 0.048), bevel=0.0008, segments=1, panel=False)
    p.box("Kit_Perforated", (L - 0.0138, gu0, gz0), (L - 0.0132, gu0 + 0.07, gz0 + 0.045), panel=False)
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
    p.box("Kit_Lip", (-0.104, -0.044, -0.002), (0.104, 0.044, 0.0012), bevel=0.0008, segments=1, m=fs_(pc), panel=False)
    p.box("Kit_Inset", (-0.1, -0.04, -0.002), (0.1, 0.04, 0.0018), m=fs_(pc), panel=False)
    for k, lab in enumerate(("ck_lights", "ck_gear", "ck_vtol")):
        q = fs_(pc) @ Vector((0.062 * (k - 1), -0.004, 0.0018))
        _rocker(p, q, X, sd_, ns, lab, label_scale=0, index=False, cap="Kit_Inset")
        for sv in (-1, 1):                                       # polished side guards: guarded switches
            p.box("Kit_Lip", (sv * 0.0125 - 0.0015, -0.017, 0.0), (sv * 0.0125 + 0.0015, 0.017, 0.009), bevel=0.0007, segments=1,
                  m=frame(q, X, sd_, ns))
        led(p, q + sd_ * 0.024, ns, "Kit_GlowAmber" if k == 1 else "Kit_GlowKey", r=0.0026)
        legend(p, {"ck_lights": "LIGHTS", "ck_gear": "GEAR", "ck_vtol": "VTOL"}[lab], q - sd_ * 0.027 + ns * 0.0002, X, sd_, ns, h=0.0075)
    # 7b the rear deck outboard of the beam: a service hatch (a raised lid in a dark seam, a recessed pull, two
    # quarter-turn latches, its stencils) - the concept has no empty board
    hx0, hx1, hu0, hu1 = 0.06, 0.58, 0.2, W - 0.04
    p.box("Kit_Graphite", (hx0 - 0.006, hu0 - 0.006, DECK + 0.004), (hx1 + 0.006, hu1 + 0.006, DECK + 0.008), panel=False)
    lid = [(hu0, DECK), (hu1, DECK), (hu1, DECK + 0.018), (hu1 - 0.012, DECK + 0.026), (hu0 + 0.012, DECK + 0.026), (hu0, DECK + 0.018)]
    end_prism(p, "Kit_Frame", lid, hx0, hx1, 0.003, 1)
    zt = DECK + 0.026
    p.box("Kit_Inset", (hx0 + 0.022, hu0 + 0.022, zt - 0.002), (hx1 - 0.022, hu1 - 0.022, zt + 0.006), bevel=0.004, segments=1)
    zt += 0.006
    for xx in (hx0 + 0.035, (hx0 + hx1) / 2, hx1 - 0.035):
        for uu in (hu0 + 0.035, hu1 - 0.035):
            screw(p, Vector((xx, uu, zt)), Z, 0.0045)
    for uu in ((hu0 + hu1) / 2,):
        for xx in (hx0 + 0.035, hx1 - 0.035):
            screw(p, Vector((xx, uu, zt)), Z, 0.0045)
    for xx in ((hx0 + hx1) / 2 - 0.12, (hx0 + hx1) / 2 + 0.12):  # two recessed latches, 20 x 8 mm
        p.box("Kit_Seal", (xx - 0.012, hu1 - 0.034, zt - 0.003), (xx + 0.012, hu1 - 0.022, zt + 0.0002), bevel=0.001, segments=1)
        p.box("Kit_Lip", (xx - 0.01, hu1 - 0.032, zt - 0.0015), (xx + 0.01, hu1 - 0.024, zt + 0.0006), bevel=0.0012, segments=1)
    p.box("Kit_Lip", (0.266, hu1 - 0.079, zt - 0.001), (0.374, hu1 - 0.041, zt + 0.0008), bevel=0.0008, segments=1, panel=False)
    p.box("Kit_Seal", (0.27, hu1 - 0.075, zt - 0.012), (0.37, hu1 - 0.045, zt + 0.0011), bevel=0.004, segments=2)        # the pull
    p.sweep("Kit_Lip", [Vector((0.285, hu1 - 0.06, zt - 0.006)), Vector((0.29, hu1 - 0.06, zt - 0.001)), Vector((0.35, hu1 - 0.06, zt - 0.001)),
                        Vector((0.355, hu1 - 0.06, zt - 0.006))], 0.003, seg=12)                                    # its lever
    _label(p, "st_inspect", Vector((0.47, hu1 - 0.06, zt + 0.0004)), Z, X, Y, scale=0.45)
    _label(p, "pn_9", Vector((0.12, hu0 + 0.07, zt + 0.0004)), Z, X, Y, scale=0.6)
    p.box("Kit_Lip", (0.28, hu1 - 0.07, zt - 0.006), (0.36, hu1 - 0.065, zt - 0.002), bevel=0.0015, segments=2)
    for xx in (hx0 + 0.05, hx1 - 0.16):
        c = Vector((xx, (hu0 + hu1) / 2, zt))
        p.lathe("Kit_Lip", [(0.011, 0.0), (0.011, 0.0015), (0.009, 0.0025)], tuple(c), seg=20)
        p.box("Kit_Graphite", (xx - 0.0075, (hu0 + hu1) / 2 - 0.0015, zt + 0.0015), (xx + 0.0075, (hu0 + hu1) / 2 + 0.0015, zt + 0.0035), panel=False)
    _label(p, "st_service", Vector((0.22, hu0 + 0.06, zt + 0.0004)), Z, X, Y, scale=0.7)       # read from the seat
    _label(p, "label_coolant", Vector((0.47, hu1 - 0.13, zt + 0.0004)), Z, X, Y, scale=0.9)
    # a groove splits the lid 60/40; the small field a framed grille
    gx = hx0 + 0.022 + 0.63 * (hx1 - hx0 - 0.044)
    p.box("Kit_Seal", (gx - 0.0008, hu0 + 0.03, zt - 0.0005), (gx + 0.0008, hu1 - 0.03, zt + 0.0003), panel=False)
    p.box("Kit_Lip", (gx + 0.03, hu0 + 0.045, zt - 0.0005), (gx + 0.115, hu0 + 0.09, zt + 0.0009), bevel=0.0006, segments=1, panel=False)
    p.box("Kit_Perforated", (gx + 0.033, hu0 + 0.048, zt + 0.0009), (gx + 0.112, hu0 + 0.087, zt + 0.0012), panel=False)
    # the big field: a pressed 3 mm bead frame 15 mm inside the groove and the lid edge, an OPEN arrow at the pull
    fx0, fx1, fu0, fu1 = hx0 + 0.075, gx - 0.015, hu0 + 0.1, hu1 - 0.1
    for a, b in (((fx0, fu0), (fx1, fu0 + 0.003)), ((fx0, fu1 - 0.003), (fx1, fu1)),
                 ((fx0, fu0), (fx0 + 0.003, fu1)), ((fx1 - 0.003, fu0), (fx1, fu1))):
        p.box("Kit_Inset", (a[0], a[1], zt - 0.0005), (b[0], b[1], zt + 0.0018), bevel=0.0012, segments=2, panel=False)
    for k in range(3):                                          # two ribs 3 x 6 mm across the frame
        xr = fx0 + (fx1 - fx0) * (k + 1) / 4
        if k != 1:
            p.box("Kit_Inset", (xr - 0.0015, fu0 + 0.012, zt - 0.0005), (xr + 0.0015, fu1 - 0.012, zt + 0.0025), bevel=0.0012, segments=2, panel=False)
    legend(p, "< OPEN >", Vector((0.32, hu1 - 0.0895, zt + 0.0002)), X, Y, Z, h=0.011)
    # 15 mm hazard strips low on both pedestal sides (5 mm orange bars, 5 mm gaps, a dark band)
    for uf, ns_ in ((U0, -1), (W, 1)):
        fz0, fz1 = 0.081, 0.099
        for x0_, x1_ in ((0.08, 0.38), (0.5, 0.78)):
            p.box("Kit_Seal", (x0_ - 0.002, uf + ns_ * 0.0002 - 0.0008, fz0 - 0.002), (x1_ + 0.002, uf + ns_ * 0.0002 + 0.0008, fz1 + 0.002), panel=False)
            xx = x0_
            while xx + 0.006 + (fz1 - fz0) <= x1_:
                bar = [(xx, fz0), (xx + 0.006, fz0), (xx + 0.006 + (fz1 - fz0), fz1), (xx + (fz1 - fz0), fz1)]
                if ns_ < 0:
                    side_prism(p, "Kit_Signal", bar, uf - 0.0014, uf - 0.0009, 0.0, 1)
                else:
                    side_prism(p, "Kit_Signal", bar, uf + 0.0009, uf + 0.0014, 0.0, 1)
                xx += 0.012
    # 7c the decal layers (author 8. 10.: the parts are new from the factory - no wear; the richness is stacked detail):
    # stencils, labels and ids on the graphite insets, rivet rows on the frame band, a socket and a hazard band on the
    # front, plates on the outboard side - each fully on one flat face
    zb = 0.41                                                   # the frame band between the insets and the belt line
    det = [("st_inspect", (0.24, U0 - 0.0065, 0.19), -Y, X, 0.7), ("st_service", (0.17, U0 - 0.0065, 0.28), -Y, X, 0.7),
           ("pn_1", (0.085, U0 - 0.0065, DECK - 0.09), -Y, X, 0.7), ("pn_2", (0.33, U0 - 0.0065, DECK - 0.09), -Y, X, 0.7),
           ("pn_3", (0.585, U0 - 0.0065, DECK - 0.09), -Y, X, 0.7),
           ("st_hfcl", (0.63, U0 - 0.0065, 0.17), -Y, X, 0.7),
           ("label_coolant", (0.24, W + 0.0065, 0.2), Y, -X, 0.8), ("st_torque", (0.25, W + 0.0065, 0.33), Y, -X, 0.6),
           ("warning_label", (0.62, W + 0.0065, 0.22), Y, -X, 0.8), ("st_gnd", (0.62, W + 0.0065, 0.32), Y, -X, 0.8),
           ("tri_warning", (1.11, TU - 0.0065, 0.5), -Y, X, 0.6), ("panel_B07", (1.1, W + 0.0045, 0.6), Y, -X, 0.6),
           ("socket", (L - 0.0155, (U0 + TU) / 2, 0.33), X, Y, 0.8),
           ("hazard_subtle", (L - 0.0195, (TU + W) / 2, 0.39), X, Y, 0.9), ("panel_A12", (L - 0.0195, (TU + W) / 2, 0.2), X, Y, 0.8),
           ("corner_mark", (0.9, 0.0, DECK + 0.0065), Z, X, 0.6), ("label_power", (0.94, U0 - 0.0005, 0.22), -Y, X, 0.6),
           ("ck_maker_plate", (0.96, W + 0.0045, 0.19), Y, -X, 0.9),
           # the second layer: small stencils and ids on the insets and the frame
           ("st_hfcl", (1.13, TU - 0.0065, 0.62), -Y, X, 0.45),
           ("st_extpwr", (0.81, W + 0.0035, 0.46), Y, -X, 0.6), ("st_torque", (0.81, W + 0.0035, 0.3), Y, -X, 0.5),
           ("pn_6", (0.73, W + 0.0035, 0.42), Y, -X, 0.6), ("st_gnd", (L - 0.0155, (U0 + TU) / 2, 0.39), X, Y, 0.5),
           ("pn_8", (0.5, W + 0.0065, 0.16), Y, -X, 0.6),
           ("st_torque", (1.11, TU - 0.0065, 0.6), -Y, X, 0.35), ("pn_5", (1.13, TU - 0.0065, 0.66), -Y, X, 0.5)]
    for uf, ns_ in ((U0, -1), (W, 1)):                         # a polished 9 mm bead along the frame band (was rivet rows)
        ua, ub = sorted((uf, uf + ns_ * 0.003))
        p.box("Kit_FrameEdge", (0.02, ua, zb - 0.0045), (0.8, ub, zb + 0.0045), bevel=0.0015, segments=2, panel=False)
    for item, at, nn, rr, sc_ in det:
        nn = Vector(nn)
        up = Z if abs(nn.z) < 0.5 else Y                       # right x up = the normal (a right-handed decal frame)
        _label(p, item, Vector(at), nn, Vector(rr), up, scale=sc_, is_label=item.startswith(("st_", "pn_", "label_", "warning", "tri_", "warn_", "panel_", "ck_")))
    p.collision_box((0.0, -0.08, 0.0), (L + 0.09, W + 0.005, 0.68))
    return p
