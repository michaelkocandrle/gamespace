"""Batch 4 of the interior kit, third part: the hull liner (kit_parts.json Wall_HullLiner, 29. 9. 2026).

A thin wall along a hull's inside for rooms wider than the W profile allows - the Wayfarer's hold (author 28. 9.
2026: "a thin liner along the hull, exposed frames are fine") and its cabin: its hull leaves 3.8-4.2 m with a 0.15 m
liner where the W walls take 3.0 m. Section L (kit_rules.json): vertical to 1.7 m, a 3:4 chamfer 0.375 m in to 2.2 m
(the hull's own upper chamfer - near the Wayfarer's ramp it leaves no more), the cove to the 2.3 m ceiling, 0.1 m of
structure behind the panel face.

The same design language as the W walls (kit_walls.Wall, which this builds on): the recessed plinth with its housed
cool strip, the kick panel and its brushed plate, the main panel in two plates to the rail at 1.3 m - one line
through the ship - then an upper plate to the chamfer, the chamfer in two panels with a bolted flange, the cable tray
on the chamfer, the cove with its housed warm strips. What makes it a hull liner: exposed hull frames at every module
joint, a flanged T section standing 8 cm off the panels floor to cove, a lightening hole in the web above the rail,
bolted.
  A  plain: the maker's plate
  B  service: a cable drop from the tray into a junction box, a small access hatch with quarter-turn latches
  C  cargo: an L-track tie-down rail at 0.35 m, two anchors with D rings and hazard marks, a strap, a grab handle and a
     power outlet for powered containers (the hold's cargo side)

Frame: kit_rules wall pivot (origin at the bottom start on the face plane, face +X, length along +Y).

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- liner
"""
import random

from mathutils import Vector

import kit_geo
from kit_geo import frame
from kit_walls import BEV_MID, BEV_SMALL, G, GAP, PT, RECESS_BACK, Wall

RAIL = 1.3                     # the rail line of the W walls, carried through


class Liner(Wall):
    def __init__(self, L, name, seed):
        super().__init__("L", L, name, seed)
        self.main = (0.5 + GAP / 2, RAIL - 0.055)
        self.upper = (RAIL + 0.055, self.vt - 0.03)

    def shell(self, main_split=None, upper_split=None, skip_kick=False):
        p, L = self.p, self.L
        sd = self.sec.get("structure_depth", 0.1)
        # dark backing behind everything
        p.slab("Kit_Seal", self.VERT, 0, L, 0.1, self.vt, 0.01, proud=-RECESS_BACK, panel=False)
        p.slab("Kit_Seal", self.SLOPE, 0, L, 0, self.slope_len, 0.01, proud=-RECESS_BACK, panel=False)
        # the recessed plinth with the housed cool strip and the rubber kick edge (as the W walls)
        p.slab("Kit_Seal", self.PLINTH, 0, L, 0, 0.1414, 0.012, panel=False)
        f0, f1 = G + 0.004, L - G - 0.004
        p.slab("Kit_Structure", self.PLINTH, f0, f1, 0.034, 0.046, 0.012, BEV_SMALL, segments=1, proud=0.012, panel=False)
        p.slab("Kit_Structure", self.PLINTH, f0, f1, 0.072, 0.084, 0.012, BEV_SMALL, segments=1, proud=0.012, panel=False)
        p.slab("Kit_GlowCool", self.PLINTH, f0 + 0.012, f1 - 0.012, 0.046, 0.072, 0.004, proud=0.004, panel=False)
        for (c0, c1) in ((f0, f0 + 0.012), (f1 - 0.012, f1)):
            p.slab("Kit_Structure", self.PLINTH, c0, c1, 0.034, 0.084, 0.012, proud=0.014, panel=False)
        p.box("Kit_Rubber", (-0.1, 0, 0), (-0.085, L, 0.012), bevel=0.003, panel=False)
        p.box("Kit_Structure", (-0.11, 0.0, -0.04), (0.0, L, 0.0), panel=False)
        if not skip_kick:
            self.grime("soot", self.VERT, L / 2, self.kick[0] + 0.09, (0, -1), (L - 0.04, 0.18), 1.0)
            p.slab("Kit_Primary", self.VERT, G, L - G, self.kick[0], self.kick[1], PT, BEV_MID, secondary=True)
            p.slab("Kit_Trim", self.VERT, G, L - G, self.kick[0], self.kick[0] + 0.1, 0.006, BEV_SMALL, proud=0.003,
                   trim="kickplate", panel=False)
        # the main panel in two plates to the rail, the upper one 12 mm proud (as the W walls) and in two across a long
        # module; every plate bolted at its corners (critic of the hold, round 2: "smooth plates, no rims or bolts")
        upper_main = ([(G, L / 2 - GAP / 2, self.split + GAP / 2, self.main[1], 0.012), (L / 2 + GAP / 2, L - G, self.split + GAP / 2, self.main[1], 0.012)]
                      if L >= 1.0 else [(G, L - G, self.split + GAP / 2, self.main[1], 0.012)])
        for pan in (main_split or [(G, L - G, self.main[0], self.split - GAP / 2, 0.0)] + upper_main):
            self.pressed(self.VERT, *pan)
            self.bolts(self.VERT, *pan)
        # the rail and its signal line at 1.3 m
        p.slab("Kit_Signal", self.VERT, 0, L, RAIL - 0.049, RAIL - 0.043, 0.01, proud=-0.006, panel=False)
        p.slab("Kit_Trim", self.VERT, 0, L, RAIL - 0.025, RAIL + 0.025, 0.045, BEV_SMALL, proud=0.014, trim="rail_bolted", panel=False)
        # the upper plate between the rail and the chamfer, set back a little
        for pan in (upper_split or [(G, L - G, self.upper[0], self.upper[1], -0.008)]):
            self.pressed(self.VERT, *pan)
            self.bolts(self.VERT, *pan)
        # the chamfer: two pressed panels with a bolted flange between (as the W walls' slope)
        a = 0.45 * self.slope_len
        self.pressed(self.SLOPE, G, L - G, 0.045, a - 0.019)
        p.slab("Kit_Trim", self.SLOPE, 0, L, a - 0.015, a + 0.015, 0.03, BEV_SMALL, proud=0.006, trim="flange_bolted", panel=False)
        self.pressed(self.SLOPE, G, L - G, a + 0.019, self.slope_len - 0.04)
        self.frames()
        self.tray()
        # cove: lip, ledge, fascia, warm strips up and down (the W walls' cove at this section's height)
        xt, zt = self.x_top, self.top
        p.box("Kit_Structure", (xt - 0.022, 0, zt - 0.045), (xt + 0.004, L, zt + 0.03), bevel=BEV_SMALL, panel=False)
        p.box("Kit_Structure", (xt - 0.125, 0, zt - 0.02), (xt - 0.02, L, zt), panel=False)
        p.box("Kit_Primary", (xt - 0.14, 0, zt), (xt - 0.125, L, self.ceiling), secondary=True)
        p.box("Kit_GlowWarm", (xt - 0.08, G + 0.01, zt), (xt - 0.055, L - G - 0.01, zt + 0.006), panel=False)
        for (a0, a1) in ((xt - 0.092, xt - 0.08), (xt - 0.055, xt - 0.043)):
            p.box("Kit_Structure", (a0, G, zt), (a1, L - G, zt + 0.018), panel=False)
        p.box("Kit_Structure", (xt - 0.034, G, zt - 0.066), (xt + 0.008, L - G, zt - 0.045), bevel=BEV_SMALL, segments=1, panel=False)
        p.box("Kit_GlowWarm", (xt - 0.022, G + 0.012, zt - 0.0675), (xt - 0.004, L - G - 0.012, zt - 0.064), panel=False)
        for (c0, c1) in ((0.0, 0.03), (L - 0.03, L)):
            p.box("Kit_Structure", (xt - 0.042, c0, zt - 0.078), (xt + 0.014, c1, zt + 0.036), bevel=0.004, segments=1, panel=False)
        # the up-light: secondary to the ceiling's fixtures (critic of the hold: "1-2 EV under them"); 8 cm under the
        # ceiling it grazes it and cannot light its middle at any strength (x2.5 only burnt the edge white) - the
        # ceiling panels' halo lights do that
        # (round 2: "the cove at 30-40 %, a line, darkness between the fixtures": 0.5 per metre)
        self.strip_light("Light_Cove_0", (xt - 0.0675, L / 2, zt + 0.02), (0, 0, 1), L - 2 * G - 0.03, 0.025, "warm", 0.5 * L, radius_m=1.8)
        # the wash down its own wall, not out into the room (round 3: "the lower walls black, no shape"): aimed at the
        # wall's middle it grazes the panels - their bevels, bolts and the frames' flanges catch it
        # (15 cm short of each frame: at full length its ends burnt the flanges' tops white)
        self.strip_light("Light_Wash_0", (xt - 0.013, L / 2, zt - 0.075), (-0.27, 0, -0.963), max(0.2, L - 0.3), 0.018, "warm", 5.0 * L, radius_m=2.6)
        # collision: the thin wall, the chamfer and cove as one hull
        p.collision_box((-sd, 0, 0), (0, L, self.vt))
        p.collision_hull([(x, y, z) for y in (0, L) for x, z in ((-sd, self.vt), (0, self.vt), (xt, zt), (xt, self.ceiling), (-sd, self.ceiling))])
        p.socket("Snap_Start", (0, 0, 0), x=(0, -1, 0), z=(0, 0, 1))
        p.socket("Snap_End", (0, L, 0), x=(0, 1, 0), z=(0, 0, 1))

    def bolts(self, m, u0, u1, v0, v1, proud=0.0):
        """Four bolt heads in a plate's border, 2.2 cm in from its corners."""
        for u in (u0 + 0.022, u1 - 0.022):
            for v in (v0 + 0.022, v1 - 0.022):
                self.p.tube("Kit_Structure", self.world(m, u, v, proud - 0.001), self.world(m, u, v, proud + 0.005), 0.008, 8)

    # half a flange per module end, standing 8 cm off; half a web 2 cm wide from the backing out: it overlaps the panels'
    # ends as the W walls' frames do (a 6 mm web left the upper plate hanging in the air - geometry check)
    FL_W, FL_OUT, WEB = 0.045, 0.08, 0.02

    def frames(self):
        """An exposed hull frame over each joint: a T section - a web along the joint, a flange across its front -
        from the plinth up the wall and the chamfer to the cove, half of it on each module; lightening holes in the web
        above the rail (dark discs through it), bolts along the flange."""
        p, L = self.p, self.L
        fw, fo, wb = self.FL_W, self.FL_OUT, self.WEB
        z_knee = self.vt
        for y0, s in ((0.0, 1), (L, -1)):
            ya, yb = sorted((y0, y0 + s * wb))
            fa, fb = sorted((y0, y0 + s * fw))
            # web and flange up the wall
            p.box("Kit_Structure", (-RECESS_BACK, ya, 0.1), (fo - 0.012, yb, z_knee), panel=False)
            p.box("Kit_Structure", (fo - 0.012, fa, 0.1), (fo, fb, z_knee), bevel=0.002, segments=1, panel=False)
            # up the chamfer (in its frame: local x along the joint... the slope frame's u runs along the wall)
            p.slab("Kit_Structure", self.SLOPE, min(y0, y0 + s * wb), max(y0, y0 + s * wb), 0.0, self.slope_len, fo - 0.012 + RECESS_BACK,
                   proud=fo - 0.012, panel=False)
            p.slab("Kit_Structure", self.SLOPE, fa, fb, 0.0, self.slope_len, 0.012, BEV_SMALL, segments=1, proud=fo, panel=False)
            # lightening holes: dark discs on both faces of the web, above the rail
            for zc in (1.5,):
                c = Vector((0.04, y0 + s * wb / 2, zc))
                p.tube("Kit_Seal", c - Vector((0, 0.0045, 0)), c + Vector((0, 0.0045, 0)), 0.022, 16)
                p.tube("Kit_Structure", c - Vector((0, 0.005, 0)), c - Vector((0, 0.0045, 0)), 0.028, 16)
                p.tube("Kit_Structure", c + Vector((0, 0.0045, 0)), c + Vector((0, 0.005, 0)), 0.028, 16)
            # bolts along the flange every 0.3 m
            yb_ = y0 + s * 0.022
            for zb in [0.25 + 0.3 * k for k in range(int((z_knee - 0.3) / 0.3) + 1)]:
                p.tube("Kit_Structure", (fo, yb_, zb), (fo + 0.005, yb_, zb), 0.0065, 6)
            # a foot plate where the frame meets the floor
            p.box("Kit_Structure", (0.0, min(fa, fb), 0.0), (fo + 0.01, max(fa, fb), 0.1), bevel=0.003, segments=1, panel=False)

    def tray(self):
        """The open cable tray on the chamfer's upper panel (as the W walls' slope tray): a tray plate on fins off the
        chamfer, a rim at its lower edge, three black cables and a cream one in it."""
        p, L = self.p, self.L
        v0 = self.slope_len - 0.2
        for u in self._stations(0.6):
            p.slab("Kit_Structure", self.SLOPE, u - 0.02, u + 0.02, v0 - 0.02, v0 + 0.07, 0.034, BEV_SMALL, proud=0.034, panel=False)
        p.slab("Kit_Structure", self.SLOPE, 0, L, v0 - 0.02, v0 + 0.07, 0.006, BEV_SMALL, proud=0.04, panel=False)
        p.slab("Kit_Structure", self.SLOPE, 0, L, v0 - 0.02, v0, 0.065, BEV_SMALL, proud=0.105, panel=False)
        # cables that read in the tray (critic: "an empty black groove"): a cream and an orange one among the black
        for (vv, zz, rr, role) in ((v0 + 0.012, 0.051, 0.011, "Kit_Rubber"), (v0 + 0.036, 0.052, 0.012, "Kit_Accent"),
                                   (v0 + 0.059, 0.051, 0.011, "Kit_Rubber"), (v0 + 0.024, 0.067, 0.009, "Kit_Signal")):
            p.tube(role, self.world(self.SLOPE, 0.0, vv, zz), self.world(self.SLOPE, L, vv, zz), rr, 10, caps=False)


def cargo_fittings(w):
    """A cargo module's fittings on its main panel (critic of the hold, round 2: "a handle, a connection"): a grab handle
    beside the frame (a hand hold climbing onto the load, in low gravity) and a power outlet for powered containers,
    its cap on a chain."""
    L = w.L
    hu = L - 0.13
    for v in (w.split + 0.06, w.main[1] - 0.09):
        w.p.tube("Kit_Structure", (0.012, hu, v), (0.06, hu, v), 0.009, 8)
    w.p.tube("Kit_Signal", (0.06, hu, w.split + 0.05), (0.06, hu, w.main[1] - 0.08), 0.014, 10)
    pu, pv = 0.34, 0.68
    w.p.box("Kit_Structure", (0.0, pu - 0.07, pv - 0.09), (0.05, pu + 0.07, pv + 0.09), bevel=0.006, segments=2, panel=False)
    w.p.tube("Kit_Seal", (0.049, pu, pv + 0.015), (0.056, pu, pv + 0.015), 0.036, 16)
    w.p.tube("Kit_Structure", (0.049, pu, pv + 0.015), (0.06, pu, pv + 0.015), 0.042, 16, caps=False)
    for dy in (-0.012, 0.012):
        w.p.tube("Kit_Primary", (0.054, pu + dy, pv + 0.015), (0.058, pu + dy, pv + 0.015), 0.005, 6)
    w.p.box("Kit_Signal", (0.05, pu - 0.05, pv - 0.075), (0.056, pu + 0.05, pv - 0.05), panel=False)
    w.label("st_service", w.VERT, pu, pv + 0.12, 0.35, label=True)


def liner_plain(w, var, rng):
    L = w.L
    w.shell()
    if var == "A":
        w.p.slab("Kit_Structure", w.VERT, 0.12, 0.26, w.main[1] - 0.12, w.main[1] - 0.07, 0.01, BEV_SMALL, proud=0.02, panel=False)
        w.label("maker", w.VERT, 0.19, w.main[1] - 0.095, 0.22)
    elif var == "B":
        # a cable drop from the tray into a junction box on the upper zone, an access hatch on the main panel
        jy = 0.32 if L >= 1.0 else L / 2
        zt = w.vt + 0.02
        w.p.box("Kit_Structure", (0.0, jy - 0.1, RAIL + 0.07), (0.08, jy + 0.1, RAIL + 0.33), bevel=0.006, segments=2)
        w.p.box("Kit_Primary", (0.08, jy - 0.085, RAIL + 0.085), (0.085, jy + 0.085, RAIL + 0.315), bevel=0.002, segments=1)
        for zz in (RAIL + 0.1, RAIL + 0.3):
            for yy in (jy - 0.07, jy + 0.07):
                w.p.tube("Kit_Structure", (0.085, yy, zz), (0.09, yy, zz), 0.005, 6)
        for k, dy in enumerate((-0.035, 0.03)):
            w.p.tube("Kit_Rubber", (0.04, jy + dy, RAIL + 0.33), (0.04 + 0.02 * k, jy + dy, zt), 0.011 if k == 0 else 0.009, 10, caps=False)
        w.label("st_service", w.VERT, jy, RAIL + 0.2, 0.5, label=True)
        if L >= 1.0:
            # a hatch in the main panel's upper plate: frame, recessed door, two quarter-turn latches
            h0, h1, v0, v1 = L * 0.55, L * 0.55 + 0.34, w.split + 0.06, w.split + 0.3
            w.p.slab("Kit_Structure", w.VERT, h0 - 0.02, h1 + 0.02, v0 - 0.02, v1 + 0.02, 0.016, BEV_SMALL, proud=0.028, panel=False)
            w.p.slab("Kit_Primary", w.VERT, h0, h1, v0, v1, 0.012, BEV_SMALL, proud=0.024, secondary=True)
            for uu in (h0 + 0.04, h1 - 0.04):
                c = w.world(w.VERT, uu, (v0 + v1) / 2, 0.024)
                w.p.tube("Kit_Structure", c, c + Vector((0.008, 0, 0)), 0.014, 12)
                w.p.box("Kit_Accent", (c.x + 0.006, c.y - 0.012, c.z - 0.003), (c.x + 0.012, c.y + 0.012, c.z + 0.003), panel=False)
            w.label("st_inspect", w.VERT, (h0 + h1) / 2, v1 - 0.035, 0.6, label=True)
    else:
        # C, cargo side: the fittings on the main panel (a handle, a power outlet), then
        if L >= 1.0:
            cargo_fittings(w)
        # an L-track: a flanged rail on stand-offs with round holes every 2.5 cm along its lip (critic: "a flat strip,
        # not a rail"), two anchors with D rings, a cargo strap hanging from one; hazard marks only at the anchors
        zr = 0.35
        w.p.slab("Kit_Structure", w.VERT, 0.03, L - 0.03, zr - 0.04, zr + 0.04, 0.012, BEV_SMALL, proud=0.05, panel=False)
        w.p.slab("Kit_Structure", w.VERT, 0.03, L - 0.03, zr + 0.012, zr + 0.04, 0.03, BEV_SMALL, proud=0.08, panel=False)
        w.p.slab("Kit_Structure", w.VERT, 0.03, L - 0.03, zr - 0.04, zr - 0.012, 0.03, BEV_SMALL, proud=0.08, panel=False)
        n = int((L - 0.08) / 0.025)
        anchors = (L * 0.25, L * 0.7)
        for k in range(n):
            u = 0.04 + (k + 0.5) * (L - 0.08) / n
            if all(abs(u - a) > 0.04 for a in anchors):   # none under an anchor's block (the 0.6 m module's budget)
                w.p.tube("Kit_Seal", (0.079, u, zr + 0.026), (0.0815, u, zr + 0.026), 0.0055, 6)
        for u in w._stations(0.3):
            w.p.box("Kit_Structure", (0.0, u - 0.02, zr - 0.035), (0.05, u + 0.02, zr + 0.035), bevel=0.002, segments=1, panel=False)
        for k, u in enumerate(anchors):
            w.p.box("Kit_Accent", (0.075, u - 0.035, zr - 0.035), (0.1, u + 0.035, zr + 0.035), bevel=0.004, segments=1, panel=False)
            w.p.tube("Kit_Structure", (0.105, u - 0.025, zr - 0.03), (0.105, u + 0.025, zr - 0.03), 0.007, 10)
            w.p.tube("Kit_Structure", (0.1, u - 0.025, zr - 0.03), (0.105, u - 0.025, zr - 0.03), 0.007, 8)
            w.p.tube("Kit_Structure", (0.1, u + 0.025, zr - 0.03), (0.105, u + 0.025, zr - 0.03), 0.007, 8)
            w.label("hazard_subtle", w.VERT, u, zr + 0.075, 0.3)
            if k == 0:
                # a strap hanging from the ring, its buckle, the loose end on the floor
                w.p.box("Kit_Signal", (0.1, u - 0.022, 0.02), (0.106, u + 0.022, zr - 0.024), panel=False)
                w.p.box("Kit_Structure", (0.098, u - 0.028, 0.17), (0.112, u + 0.028, 0.21), bevel=0.003, segments=1, panel=False)
                w.p.box("Kit_Signal", (0.106, u - 0.022, 0.0), (0.2, u + 0.022, 0.006), panel=False)


LINER = [("HullLiner", 1.2, "A"), ("HullLiner", 1.2, "B"), ("HullLiner", 1.2, "C"), ("HullLiner", 0.6, "A"), ("HullLiner", 0.6, "C")]
VIEWS = ((1, 0, 0.12), (1, -0.9, 0.35))


def part_name(kind, L, var):
    return "SM_Kit_Wall_%s%02dL_%s" % (kind, int(round(L * 10)), var)


def build_part(kind, L, var, seed):
    name = part_name(kind, L, var)
    w = Liner(L, name, seed)
    liner_plain(w, var, random.Random(seed))
    return w.p


def budget(L):
    b = kit_geo.RULES["tri_budget"]
    return int(b["Wall_base"] + b["Wall_per_m"] * L)
