"""Batch 1 of the interior kit: wall modules (kit_parts.json families Wall_*; design language and rules in the
ship-interior skill and ArtSource/Kit/kit_rules.json, 26. 9. 2026).

A wall module is one side of a corridor, L long: pivot on the panel face plane at the floor, face normal +X
(into the room), length along +Y, up +Z. Every module has the same shell - the three layers of the design
language:
  structure  dark backing behind the panels (seen through the shadow gaps), the stringer rail at the break
  panels     kick panel (secondary tone), main panel, slope panel, each 25 mm, bevelled, 8 mm gaps
  fittings   per module type (grille, locker, pipes, hatch, display) and variant A..C
plus the recessed plinth with its cool floor strip, a thin orange signal line under the rail, and the cove at the
top of the slope with its warm strip - each strip carries SOCKET_Light_* every 0.6 m (a light per fixture).
"""
import math
import random
import zlib

from mathutils import Vector

import kit_geo
from kit_geo import frame

G = 0.006                     # half shadow gap (each module carries half at its ends)
GAP = 0.012                   # gap between panels (8 mm read as a hairline - critic, 27. 9. 2026)
PT = 0.025                    # panel thickness
BEV_BIG, BEV_MID, BEV_SMALL = 0.012, 0.007, 0.003
SQ = math.sqrt(0.5)


class Wall:
    def __init__(self, sec_key, L, name, seed):
        self.sec = kit_geo.RULES["sections"][sec_key]
        self.key = sec_key
        self.L = L
        self.vt = self.sec["vertical_to"]
        self.rise = self.sec["slope_rise"]
        self.top = self.vt + self.rise
        self.x_top = 0.75 * self.rise
        self.slope_len = self.rise / 0.8
        self.ceiling = self.sec["ceiling"]
        self.p = kit_geo.Part(name, seed)
        self.VERT = frame((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))
        self.SLOPE = frame((0, 0, self.vt), (0, 1, 0), (0.6, 0, 0.8), (0.8, 0, -0.6))
        self.PLINTH = frame((-0.1, 0, 0), (0, 1, 0), (SQ, 0, SQ), (SQ, 0, -SQ))
        # main panel extents (v, in the vertical frame), may be cut by fittings
        self.kick = (0.1 + GAP / 2, 0.5 - GAP / 2)
        self.main = (0.5 + GAP / 2, self.vt - 0.055)
        # the main panel in two plates, the upper one 12 mm proud over the lower: a shadow line at 0.86 m and a
        # middle scale of detail between the frame and the 3 cm labels (critic round 3, 27. 9. 2026)
        self.split = 0.86
        self.split_default = True

    # ------------------------------------------------------------------ shell
    def shell(self, skip_main=False, skip_kick=False, skip_slope=False, main_split=None, slope_cut=None):
        p, L = self.p, self.L
        # structure: dark backing behind everything, seen through the gaps
        p.slab("Kit_Seal", self.VERT, 0, L, 0.1, self.vt, 0.01, proud=-0.07, panel=False)
        p.slab("Kit_Seal", self.SLOPE, 0, L, 0, self.slope_len, 0.01, proud=-0.07, panel=False)
        # recessed plinth: a dark chamfer with the cool floor strip, a rubber kick edge at the floor
        p.slab("Kit_Seal", self.PLINTH, 0, L, 0, 0.1414, 0.012, panel=False)
        # the floor strip as a fixture: a metal channel with two lips, end caps and a diffuser set in it ("bare neon
        # lines without housings" - critic round 2, 27. 9. 2026)
        f0, f1 = G + 0.004, L - G - 0.004
        p.slab("Kit_Structure", self.PLINTH, f0, f1, 0.034, 0.046, 0.012, BEV_SMALL, segments=1, proud=0.012, panel=False)
        p.slab("Kit_Structure", self.PLINTH, f0, f1, 0.072, 0.084, 0.012, BEV_SMALL, segments=1, proud=0.012, panel=False)
        p.slab("Kit_GlowCool", self.PLINTH, f0 + 0.012, f1 - 0.012, 0.046, 0.072, 0.004, proud=0.004, panel=False)
        for (c0, c1) in ((f0, f0 + 0.012), (f1 - 0.012, f1)):
            p.slab("Kit_Structure", self.PLINTH, c0, c1, 0.034, 0.084, 0.012, proud=0.014, panel=False)
        p.box("Kit_Rubber", (-0.1, 0, 0), (-0.085, L, 0.012), bevel=0.003, panel=False)
        # no light of its own: a linear light per module here cost ~1 ms over a composed sample (41 modules) for a
        # floor band the eye hardly reads - the diffuser glows (batch 2 sample, 27. 9. 2026; with MegaLights the
        # socket can come back)
        # panels (pressed: a border and a recessed centre, the depth layer of the design language)
        if not skip_kick:
            p.slab("Kit_Primary", self.VERT, G, L - G, self.kick[0], self.kick[1], PT, BEV_MID, secondary=True)
            # brushed kick plate over the lower part of the kick panel
            p.slab("Kit_Trim", self.VERT, G, L - G, self.kick[0], self.kick[0] + 0.1, 0.006, BEV_SMALL, proud=0.003,
                   trim="kickplate", panel=False)
        if main_split:
            self.split_default = False
        if not skip_main:
            default = [(G, L - G, self.main[0], self.split - GAP / 2, 0.0), (G, L - G, self.split + GAP / 2, self.main[1], 0.012)]
            for pan in (main_split or default):
                self.pressed(self.VERT, *pan)
        self.ribs()
        # an open cable tray along the top of the slope under the cove: a tray plate standing off the slope on fins,
        # a rim at its lower edge, three black cables and a cream one lying in it, seen from the corridor (a covered
        # channel hid the cables and its brackets stuck out above it as blocks - shots, 27. 9. 2026)
        sl = self.slope_len
        v0 = sl - 0.2
        for u in self._stations(0.6):
            p.slab("Kit_Structure", self.SLOPE, u - 0.02, u + 0.02, v0 - 0.02, v0 + 0.07, 0.034, BEV_SMALL, proud=0.034, panel=False)
        p.slab("Kit_Structure", self.SLOPE, 0, L, v0 - 0.02, v0 + 0.07, 0.006, BEV_SMALL, proud=0.04, panel=False)
        p.slab("Kit_Structure", self.SLOPE, 0, L, v0 - 0.02, v0, 0.065, BEV_SMALL, proud=0.105, panel=False)
        # three cables side by side on the tray plate (its face at 4 cm), the cream one in the groove on top
        for k, (vv, zz, rr, role) in enumerate(((v0 + 0.012, 0.051, 0.011, "Kit_Rubber"), (v0 + 0.036, 0.052, 0.012, "Kit_Rubber"),
                                                (v0 + 0.059, 0.051, 0.011, "Kit_Rubber"), (v0 + 0.024, 0.067, 0.008, "Kit_Accent"))):
            a = self.world(self.SLOPE, 0.0, vv, zz)
            b = self.world(self.SLOPE, L, vv, zz)
            p.tube(role, a, b, rr, 10, caps=False)
        self.conduits()
        # the signal line in the groove under the rail, then the stringer rail at the break (trim: bolted rail)
        p.slab("Kit_Signal", self.VERT, 0, L, self.vt - 0.049, self.vt - 0.043, 0.01, proud=-0.006, panel=False)
        p.slab("Kit_Trim", self.VERT, 0, L, self.vt - 0.025, self.vt + 0.025, 0.045, BEV_SMALL, proud=0.014, trim="rail_bolted", panel=False)
        if not skip_slope:
            if slope_cut:
                for (u0, u1, v0, v1) in slope_cut:
                    self.pressed(self.SLOPE, u0, u1, v0, v1)
            else:
                # two slope panels with a bolted flange between (a single 1 m slope read as a blank board)
                a = 0.45 * self.slope_len
                self.pressed(self.SLOPE, G, L - G, 0.045, a - 0.019)
                p.slab("Kit_Trim", self.SLOPE, 0, L, a - 0.015, a + 0.015, 0.03, BEV_SMALL, proud=0.006, trim="flange_bolted", panel=False)
                self.pressed(self.SLOPE, G, L - G, a + 0.019, self.slope_len - 0.04)
        # cove: lip, ledge, fascia, warm strip washing the ceiling
        xt, zt = self.x_top, self.top
        p.box("Kit_Structure", (xt - 0.022, 0, zt - 0.045), (xt + 0.004, L, zt + 0.03), bevel=BEV_SMALL, panel=False)
        p.box("Kit_Structure", (xt - 0.125, 0, zt - 0.02), (xt - 0.02, L, zt), panel=False)
        p.box("Kit_Primary", (xt - 0.14, 0, zt), (xt - 0.125, L, self.ceiling), secondary=True)
        # the up strip in the cove between two housing lips
        p.box("Kit_GlowWarm", (xt - 0.08, G + 0.01, zt), (xt - 0.055, L - G - 0.01, zt + 0.006), panel=False)
        for (a0, a1) in ((xt - 0.092, xt - 0.08), (xt - 0.055, xt - 0.043)):
            p.box("Kit_Structure", (a0, G, zt), (a1, L - G, zt + 0.018), panel=False)
        # the down strip under the lip: a housing profile with the diffuser in its underside, end caps
        p.box("Kit_Structure", (xt - 0.034, G, zt - 0.066), (xt + 0.008, L - G, zt - 0.045), bevel=BEV_SMALL, segments=1, panel=False)
        p.box("Kit_GlowWarm", (xt - 0.022, G + 0.012, zt - 0.0675), (xt - 0.004, L - G - 0.012, zt - 0.064), panel=False)
        # a bracket over each joint carries the lip and hides the strip ends: separate end caps on every module
        # read as "steps, badly assembled parts" (critic round 3)
        for (c0, c1) in ((0.0, 0.03), (L - 0.03, L)):
            p.box("Kit_Structure", (xt - 0.042, c0, zt - 0.078), (xt + 0.014, c1, zt + 0.036), bevel=0.004, segments=1, panel=False)
        # linear lights: up into the ceiling, and down-out from under the lip washing the slope and the far side
        # (the walls below 1.3 m got no light at all - critic round 2)
        self.strip_light("Light_Cove_0", (xt - 0.0675, L / 2, zt + 0.02), (0, 0, 1), L - 2 * G - 0.03, 0.025, "warm", 0.8 * L, radius_m=1.1)
        self.strip_light("Light_Wash_0", (xt - 0.013, L / 2, zt - 0.075), (0.5, 0, -0.866), L - 2 * G - 0.03, 0.018, "warm", 1.1 * L, radius_m=2.0)
        # collision: the wall to the structure depth, the slope and cove as one hull
        sd = kit_geo.RULES["zones"]["structure_depth"]
        p.collision_box((-sd, 0, 0), (0, L, self.vt))
        p.collision_hull([(x, y, z) for y in (0, L) for x, z in ((-sd, self.vt), (0, self.vt), (xt, zt), (xt, self.ceiling), (-sd, self.ceiling))])
        # snap sockets at the module ends
        p.socket("Snap_Start", (0, 0, 0), x=(0, -1, 0), z=(0, 0, 1))
        p.socket("Snap_End", (0, L, 0), x=(0, 1, 0), z=(0, 0, 1))

    RIB_W, RIB_OUT = 0.065, 0.085       # half a frame per module end (13 cm over the joint), 8.5 cm proud

    def ribs(self):
        """The structure layer: a frame over each joint, from the plinth up the wall and the slope to the cable tray -
        half of it at each module end with a flat 9 cm face across the joint and a chamfer to the panels, bolted.
        Two 3 cm halves with bevels read as a pair of pipes, not as a frame (critic round 2, 27. 9. 2026)."""
        p, L = self.p, self.L
        w, o = self.RIB_W, self.RIB_OUT
        # no bevel: a 5 mm chamfer split the 51 deg and 39 deg profile edges under the 40 deg sharp angle and the
        # smooth shading turned the frames into round posts (shots, 27. 9. 2026)
        start = [(-0.03, 0.0), (o, 0.0), (o, w - 0.02), (o - 0.025, w), (-0.03, w)]
        end = [(x, -y) for (x, y) in start]
        z_knee = self.vt - 0.028               # the vertical face meets the slope face here (a clean mitre)
        normal = Vector((0.8, 0.0, -0.6))
        up = Vector((0.6, 0.0, 0.8))
        for y0, prof in ((0.0, start), (L, end)):
            p.poly_prism("Kit_Structure", prof, frame((0, y0, z_knee), (1, 0, 0), (0, 1, 0), (0, 0, 1)), z_knee - 0.1, panel=False)
            top = self.world(self.SLOPE, y0, self.slope_len - 0.25)
            p.poly_prism("Kit_Structure", prof, frame(top, normal, (0, 1, 0), up), self.slope_len - 0.25 + 0.04, panel=False)
            # bolt heads on the face every 0.3 m
            yb = y0 + (0.022 if y0 == 0.0 else -0.022)
            for zb in [0.25 + 0.3 * k for k in range(int((z_knee - 0.3) / 0.3) + 1)]:
                p.tube("Kit_Structure", (o, yb, zb), (o + 0.005, yb, zb), 0.0065, 6)
            for vb in [0.15 + 0.3 * k for k in range(int((self.slope_len - 0.45) / 0.3) + 1)]:
                a = self.world(self.SLOPE, yb, vb, o)
                p.tube("Kit_Structure", a, a + normal * 0.005, 0.0065, 6)

    def conduits(self):
        """Cable conduits across the upper slope panel (the upper slope was "an empty board with a 3 cm label" -
        critic round 3). One pattern per part, seeded by its name, so a run of modules has no grid of identical
        conduits and clips (author, 27. 9. 2026): none, one, a pair, or a pair where one conduit dives into the
        panel through a grommet; one to three clips at free positions, a saddle or a strap."""
        p, L, sl = self.p, self.L, self.slope_len
        rng = random.Random(zlib.crc32(p.name.encode()))
        pattern = rng.choices(["none", "single", "pair", "drop"], [0.2, 0.25, 0.35, 0.2])[0]
        if L < 0.5 and pattern == "drop":
            pattern = "single"
        if pattern == "none":
            return
        vc = 0.45 * sl + 0.12 + rng.uniform(-0.025, 0.025)
        rows = [vc] if pattern == "single" else [vc, vc + rng.uniform(0.034, 0.05)]
        z, lo, hi = 0.016, self.RIB_W, L - self.RIB_W
        dive = None
        if pattern == "drop":
            # the second conduit comes in at one end and goes into the panel somewhere along the module
            side = rng.choice([0, 1])
            dive = (side, rng.uniform(0.3, 0.7) * L)
        for k, vv in enumerate(rows):
            a, b = 0.0, L
            if dive and k == 1:
                side, ud = dive
                a, b = (0.0, ud) if side == 0 else (ud, L)
                d = 1 if side == 0 else -1
                # a short bend into the panel and a grommet round the hole
                p.tube("Kit_Rubber", self.world(self.SLOPE, ud, vv, z), self.world(self.SLOPE, ud + d * 0.025, vv, -0.01), 0.011, 10, caps=False)
                g = self.world(self.SLOPE, ud + d * 0.025, vv, 0.0)
                n = Vector((0.8, 0.0, -0.6))
                p.tube("Kit_Structure", g - n * 0.002, g + n * 0.005, 0.019, 12)
            p.tube("Kit_Rubber", self.world(self.SLOPE, a, vv, z), self.world(self.SLOPE, b, vv, z), 0.011, 10, caps=False)
            for uu, dd in ((lo, 1), (hi, -1)):
                if a <= uu <= b:
                    p.tube("Kit_Structure", self.world(self.SLOPE, uu, vv, z), self.world(self.SLOPE, uu + dd * 0.012, vv, z), 0.016, 10)
        # clips at free positions, at least 0.18 m apart, clear of the frames and the dive
        n_clips = rng.randint(1, 3) if L >= 1.0 else rng.randint(0, 2) if L >= 0.5 else rng.randint(0, 1)
        spots = []
        for _ in range(40):
            if len(spots) >= n_clips:
                break
            u = rng.uniform(lo + 0.06, hi - 0.06)
            if all(abs(u - q) > 0.18 for q in spots) and not (dive and abs(u - dive[1]) < 0.08):
                spots.append(u)
        v0, v1 = rows[0] - 0.022, rows[-1] + 0.022
        for u in spots:
            if rng.random() < 0.5:
                # a saddle over all the conduits
                p.slab("Kit_Structure", self.SLOPE, u - 0.012, u + 0.012, v0, v1, 0.03, BEV_SMALL, segments=1, proud=0.03, panel=False)
            else:
                # a strap and its two screws
                p.slab("Kit_Structure", self.SLOPE, u - 0.005, u + 0.005, v0 + 0.004, v1 - 0.004, 0.029, proud=0.029, panel=False)
                for vv in (v0 - 0.006, v1 + 0.006):
                    c = self.world(self.SLOPE, u, vv, 0.0)
                    p.tube("Kit_Structure", c, c + Vector((0.8, 0.0, -0.6)) * 0.004, 0.005, 6)

    def strip_light(self, name, c, direction, width, height, role, cd, radius_m=2.6):
        """A linear fixture's light: a rect light facing `direction` (part coords), `width` along the module."""
        d = Vector(direction).normalized()
        self.p.socket(name, tuple(c), x=tuple(d), z=(0, 1, 0), type="rect", role=role, cd=round(cd, 3),
                      width_cm=round(width * 100, 1), height_cm=round(height * 100, 1), radius_m=radius_m,
                      dir_ue=[round(d.x, 4), round(-d.y, 4), round(d.z, 4)], megalights_shadow=True)

    def pressed(self, m, u0, u1, v0, v1, proud=0.0, secondary=False):
        """A panel with a border and a recessed centre when it is big enough, else a plain bevelled panel."""
        if min(u1 - u0, v1 - v0) > 0.2:
            self.p.slab("Kit_Primary", m, u0, u1, v0, v1, PT + proud, BEV_MID, secondary=secondary, inset=(0.04, 0.006), proud=proud)
        else:
            self.p.slab("Kit_Primary", m, u0, u1, v0, v1, PT + proud, BEV_MID, secondary=secondary, proud=proud)

    def _stations(self, step):
        n = max(1, int(round(self.L / step)))
        return [self.L * (i + 0.5) / n for i in range(n)]

    # ------------------------------------------------------------------ helpers
    def frame_hole(self, role, m, u0, u1, v0, v1, hole, thick=PT, bevel=BEV_MID, secondary=False):
        """A panel u0..u1 x v0..v1 in frame m with a rectangular opening hole=(hu0, hu1, hv0, hv1)."""
        hu0, hu1, hv0, hv1 = hole
        p = self.p
        if hu0 - u0 > 0.01:
            p.slab(role, m, u0, hu0, v0, v1, thick, bevel, secondary=secondary)
        if u1 - hu1 > 0.01:
            p.slab(role, m, hu1, u1, v0, v1, thick, bevel, secondary=secondary)
        if hv0 - v0 > 0.01:
            p.slab(role, m, max(u0, hu0), min(u1, hu1), v0, hv0, thick, bevel, secondary=secondary)
        if v1 - hv1 > 0.01:
            p.slab(role, m, max(u0, hu0), min(u1, hu1), hv1, v1, thick, bevel, secondary=secondary)

    def world(self, m, u, v, z=0.0):
        return m @ Vector((u, v, z))

    def label(self, item, m, u, v, scale=1.0, rot=0.0, label=False):
        """A decal shot at the point (u, v) of frame m, from 5 cm in front along the frame's normal."""
        n = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
        at = self.world(m, u, v)
        x = (m.to_3x3() @ Vector((1, 0, 0))).normalized()
        y = (m.to_3x3() @ Vector((0, 1, 0))).normalized()
        self.p.decal(item, at + n * 0.08, at - n * 0.02, rot=rot, scale=scale, frame_xy=[list(x), list(y)], label=label)

    # Service labels sit only at the hardware they name (a hatch, a grille, a bolted doubler, a pipe run); a plain
    # wall carries none. GND POINT / EXT PWR / DO NOT PAINT on bare panels were filler (critic round 3, author
    # 27. 9. 2026). The layout rule - never the same service label on neighbouring modules - is checked where
    # the modules are placed (import_kit.check_layout_labels). Panel numbers are part numbers: the same part
    # carries the same number.
    PANEL_IDS = ["panel_A12", "panel_A14", "panel_B03", "panel_B07", "panel_C21", "panel_C22", "panel_D05", "panel_E11",
                 "panel_F02", "panel_G08", "panel_H19"]

    def _unused(self, rng, pool):
        # "INSPECT 500 H" three times in one view read as a pattern (critic, 27. 9. 2026): no repeats in a module
        used = self.__dict__.setdefault("_used", set())
        pick = rng.choice([x for x in pool if x not in used] or pool)
        used.add(pick)
        return pick

    def panel_id(self, rng):
        return self._unused(rng, self.PANEL_IDS)

    def shell_decals(self, rng, main=True):
        """Decals of the shell. A decal has to lie wholly on a pressed panel's border or wholly in its recess: one
        across the recess chamfer, over the rib or under the cove lip is skipped by the placer."""
        L = self.L
        if main:
            # rivet rows on the borders; no panel number: the numbers belong to the frames, one system, readable
            # ("four codes on two metres, the same code on neighbours" - critic, batch 2 round 1)
            if L >= 0.6:
                self.label("rivet_row_8", self.VERT, L * 0.4, self.main[1] - 0.02, 0.8)
                self.label("rivet_row_8", self.VERT, L * 0.5, (self.split + GAP / 2 + 0.02) if self.split_default else self.main[0] + 0.02, 0.8)
        if L >= 1.2:
            self.label("rivet_row_8", self.SLOPE, L * 0.5, self.slope_len - 0.1, 0.8)



# =============================================================================== module types
def plain(w, var, rng):
    L = w.L
    if var == "A":
        w.shell()
        # a raised ID plate on the main panel
        w.p.slab("Kit_Structure", w.VERT, 0.09, 0.23, w.main[1] - 0.12, w.main[1] - 0.07, 0.01, BEV_SMALL, proud=0.016, panel=False)
        w.label("maker", w.VERT, 0.16, w.main[1] - 0.095, 0.22)          # the maker's plate
        w.shell_decals(rng)
    elif var == "B":
        mid = L / 2
        w.shell(main_split=[(G, mid - GAP / 2, w.main[0], w.main[1]), (mid + GAP / 2, L - G, w.main[0], w.main[1])])
        # a doubler plate with four bolts on the left half
        u0, u1 = G + 0.085, mid - 0.06
        v0, v1 = w.main[0] + 0.12, w.main[1] - 0.14
        w.p.slab("Kit_Primary", w.VERT, u0, u1, v0, v1, 0.012, BEV_SMALL, proud=0.012, secondary=True)
        for uu in (u0 + 0.025, u1 - 0.025):
            for vv in (v0 + 0.025, v1 - 0.025):
                a = w.world(w.VERT, uu, vv, 0.012)
                w.p.tube("Kit_Structure", a, a + Vector((0.006, 0, 0)), 0.007, 12)
        # a bolted doubler carries its torque stencil, not a saturated warning sticker (critic, 27. 9. 2026)
        w.label("st_torque", w.VERT, (u0 + u1) / 2, v1 - 0.06, 0.8)
        w.shell_decals(rng)
    else:  # C: a bolted flange band across the main panel, a vent slot row in the slope panel
        band0, band1 = 0.86, 0.89
        w.shell(main_split=[(G, L - G, w.main[0], band0 - GAP / 2), (G, L - G, band1 + GAP / 2, w.main[1])],
                slope_cut=[(G, L - G, 0.045, 0.28), (G, L - G, 0.36, w.slope_len - 0.04)])
        w.p.slab("Kit_Trim", w.VERT, 0, L, band0, band1, 0.03, BEV_SMALL, proud=0.006, trim="flange_bolted", panel=False)
        w.p.slab("Kit_Trim", w.SLOPE, G, L - G, 0.28 + GAP / 2, 0.36 - GAP / 2, 0.02, BEV_SMALL, proud=-0.004, trim="vent_slots", panel=False)
        w.shell_decals(rng)             # the vent slot row needs no label (a grille module carries VENT)


def grille(w, var, rng):
    L = w.L
    p = w.p
    if var == "A":
        hole = (0.1, L - 0.1, w.main[0] + 0.1, w.main[0] + 0.4)
        w.shell(skip_main=True)
        w.frame_hole("Kit_Primary", w.VERT, G, L - G, w.main[0], w.main[1], hole)
        _louvres(w, w.VERT, hole)
        w.label("st_vent", w.VERT, L / 2, hole[3] + 0.045, 0.8)
        w.shell_decals(rng, main=False)
    elif var == "B":
        hole = (0.1, 0.28, 0.16, w.main[1] - 0.06)
        w.shell(skip_main=True, skip_kick=True)
        w.frame_hole("Kit_Primary", w.VERT, G, L - G, w.kick[0], w.kick[1], (hole[0], hole[1], w.kick[0] - 0.01, w.kick[1] + 0.01), secondary=True)
        w.frame_hole("Kit_Primary", w.VERT, G, L - G, w.main[0], w.main[1], (hole[0], hole[1], w.main[0] - 0.01, hole[3]))
        _louvres(w, w.VERT, hole)
        # right beside the louvre, at mid height ("VENT - KEEP CLEAR far from the grille" - verification round)
        w.label("st_vent", w.VERT, hole[1] + 0.12, (hole[2] + hole[3]) / 2, 0.8)
        w.shell_decals(rng, main=False)
    else:  # C: return-air grille (perforated) in the slope panel
        sl = w.slope_len
        hole = (0.1, L - 0.1, 0.16, min(sl - 0.12, 0.5))
        w.shell(skip_slope=True)
        w.frame_hole("Kit_Primary", w.SLOPE, G, L - G, 0.045, sl - 0.04, hole)
        p.slab("Kit_Seal", w.SLOPE, hole[0], hole[1], hole[2], hole[3], 0.01, proud=-0.045, panel=False)
        p.slab("Kit_Trim", w.SLOPE, hole[0] + 0.01, hole[1] - 0.01, hole[2] + 0.01, hole[3] - 0.01, 0.006, proud=-0.012, trim="perforated", panel=False)
        _frame_ring(w, w.SLOPE, hole)
        w.label("st_vent", w.SLOPE, hole[0] + 0.15, 0.1, 0.8)           # under the grille: the conduits run above it
        w.shell_decals(rng)


def _frame_ring(w, m, hole, t=0.018, proud=0.006):
    hu0, hu1, hv0, hv1 = hole
    p = w.p
    for (a0, a1, b0, b1) in ((hu0 - t, hu0, hv0 - t, hv1 + t), (hu1, hu1 + t, hv0 - t, hv1 + t), (hu0, hu1, hv0 - t, hv0), (hu0, hu1, hv1, hv1 + t)):
        p.slab("Kit_Structure", m, a0, a1, b0, b1, 0.03, BEV_SMALL, proud=proud, panel=False)


def _gasket(w, m, hole, t=0.006):
    """A rubber seal lining the inside of an opening's frame ring."""
    hu0, hu1, hv0, hv1 = hole
    for (a0, a1, b0, b1) in ((hu0, hu0 + t, hv0, hv1), (hu1 - t, hu1, hv0, hv1), (hu0 + t, hu1 - t, hv0, hv0 + t), (hu0 + t, hu1 - t, hv1 - t, hv1)):
        w.p.slab("Kit_Rubber", m, a0, a1, b0, b1, 0.02, proud=0.004, panel=False)


def _louvres(w, m, hole, pitch=0.028):
    hu0, hu1, hv0, hv1 = hole
    p = w.p
    p.slab("Kit_Seal", m, hu0, hu1, hv0, hv1, 0.01, proud=-0.05, panel=False)
    _frame_ring(w, m, hole)
    _gasket(w, m, hole)
    n = int((hv1 - hv0) / pitch)
    for k in range(n):
        vc = hv0 + (k + 0.5) * (hv1 - hv0) / n
        # a slat tilted 35 deg down towards the room
        c = w.world(m, 0, vc, -0.012)
        ay = (m.to_3x3() @ Vector((0, math.cos(math.radians(35)), -math.sin(math.radians(35))))).normalized()
        az = (m.to_3x3() @ Vector((0, math.sin(math.radians(35)), math.cos(math.radians(35))))).normalized()
        ax = (m.to_3x3() @ Vector((1, 0, 0))).normalized()
        sm = frame(c, ax, ay, az)
        p.box("Kit_Structure", (hu0, -0.013, -0.0015), (hu1, 0.013, 0.0015), m=sm, panel=False)


def _u_handle(p, x0, a, b, stand=0.03, r=0.008):
    """A round-bar U handle on the plane x = x0 (the door face) from (u, v) a to b: the grip in orange paint, two
    standoffs in metal with foot plates (orange blocks read as placeholders - critic round 2, 27. 9. 2026)."""
    (ua, va), (ub, vb) = a, b
    p.tube("Kit_Signal", (x0 + stand, ua, va), (x0 + stand, ub, vb), r, 10)
    for (u, v) in (a, b):
        p.tube("Kit_Structure", (x0, u, v), (x0 + stand + r * 0.6, u, v), r * 0.8, 8, caps=False)
        p.tube("Kit_Structure", (x0, u, v), (x0 + 0.004, u, v), r * 1.9, 8)


def locker(w, var, rng):
    L = w.L
    p = w.p
    depth = 0.2 if w.key != "N" else 0.15
    # (a smooth box with two orange blocks, the two stacked lockers identical - critic, 27. 9. 2026)
    lw = 0.46                                         # clears the half frames at the module ends
    w.shell(main_split=[(G, L - G, w.main[0], w.main[1])])    # one main panel: the lockers cover it
    boxes = {"A": [((L - lw) / 2, (L + lw) / 2, 0.15, 1.25 if w.vt >= 1.3 else w.vt - 0.05, "tall")],
             "B": [((L - lw) / 2, (L + lw) / 2, 0.15, 0.62, "pull"), ((L - lw) / 2, (L + lw) / 2, 0.7, 1.22, "lever")],
             "C": [((L - 1.0) / 2, (L + 1.0) / 2, 0.14, 0.54, "box")]}[var]
    f = 0.025                                        # frame ring width
    for i, (u0, u1, v0, v1, kind) in enumerate(boxes):
        # carcass with big bent corners, a raised frame ring round the front, the door 12 mm into the ring over a
        # dark seal gap
        p.box("Kit_Primary", (0.0, u0, v0), (depth - 0.026, u1, v1), bevel=BEV_BIG, segments=1, secondary=True)
        for (a0, a1, b0, b1) in ((u0, u0 + f, v0, v1), (u1 - f, u1, v0, v1), (u0 + f, u1 - f, v0, v0 + f), (u0 + f, u1 - f, v1 - f, v1)):
            p.box("Kit_Primary", (depth - 0.026, a0, b0), (depth, a1, b1), bevel=0.004, segments=1, secondary=True)
        p.box("Kit_Seal", (depth - 0.029, u0 + f, v0 + f), (depth - 0.025, u1 - f, v1 - f), panel=False)
        du0, du1, dv0, dv1 = u0 + f + 0.005, u1 - f - 0.005, v0 + f + 0.005, v1 - f - 0.005
        dz = depth - 0.012                           # the door face
        p.box("Kit_Primary", (depth - 0.024, du0, dv0), (dz, du1, dv1), bevel=BEV_SMALL)
        door = frame((dz, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))
        if kind != "box":
            # hinge barrels on the ring's left edge
            hv = (dv0 + 0.1, dv1 - 0.1) if dv1 - dv0 > 0.4 else (dv0 + 0.06, dv1 - 0.06)
            for vv in hv:
                p.tube("Kit_Structure", (depth + 0.006, u0 + f - 0.003, vv - 0.035), (depth + 0.006, u0 + f - 0.003, vv + 0.035), 0.008, 8)
                p.box("Kit_Structure", (depth - 0.002, u0 + 0.006, vv - 0.03), (depth + 0.004, u0 + f - 0.003, vv + 0.03), panel=False)
        if kind in ("tall", "lever"):
            # vent slots low on the door
            p.slab("Kit_Trim", frame((dz + 0.001, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), du0 + 0.04, du1 - 0.04, dv0 + 0.04,
                   dv0 + 0.12, 0.002, trim="vent_slots", panel=False)
        if kind == "tall":
            # a vertical U handle on two standoffs 3 cm off the door, a latch plate above it
            pu = du1 - 0.05
            pv0, pv1 = (dv0 + dv1) / 2 - 0.15, (dv0 + dv1) / 2 + 0.15
            _u_handle(p, dz, (pu, pv0), (pu, pv1))
            p.box("Kit_Structure", (dz, pu - 0.018, pv1 + 0.04), (dz + 0.006, pu + 0.018, pv1 + 0.085), bevel=0.002, panel=False)
            p.tube("Kit_Plastic", (dz + 0.006, pu, pv1 + 0.0625), (dz + 0.012, pu, pv1 + 0.0625), 0.009, 12)
        elif kind == "lever":
            # upper locker: a latch lever (a round bar) on a pivot boss
            px, pv = du1 - 0.05, dv1 - 0.07
            p.box("Kit_Structure", (dz, px - 0.025, pv - 0.03), (dz + 0.006, px + 0.025, pv + 0.03), bevel=0.002, panel=False)
            p.tube("Kit_Structure", (dz + 0.006, px, pv), (dz + 0.02, px, pv), 0.012, 12)
            p.tube("Kit_Signal", (dz + 0.016, px, pv), (dz + 0.016, px - 0.1, pv), 0.007, 10)
        elif kind == "pull":
            # lower locker: a horizontal U handle across the top and a key lock
            _u_handle(p, dz, (du0 + 0.12, dv1 - 0.06), (du1 - 0.12, dv1 - 0.06))
            p.tube("Kit_Structure", (dz, du1 - 0.05, dv0 + 0.06), (dz + 0.006, du1 - 0.05, dv0 + 0.06), 0.011, 8)
            p.box("Kit_Seal", (dz + 0.006, du1 - 0.051, dv0 + 0.053), (dz + 0.0068, du1 - 0.049, dv0 + 0.067), panel=False)
        else:
            # stowage box: a lid seam, two over-centre latches (a catch on the lid, a base with its hinged bail
            # and an orange lever bar), carry handles on the sides
            p.box("Kit_Seal", (dz - 0.004, du0, dv1 - 0.09), (dz + 0.0005, du1, dv1 - 0.086), panel=False)
            for uu in (u0 + 0.2, u1 - 0.2):
                p.box("Kit_Structure", (dz, uu - 0.022, dv1 - 0.07), (dz + 0.008, uu + 0.022, dv1 - 0.045), bevel=0.002, panel=False)
                p.box("Kit_Structure", (dz, uu - 0.03, dv1 - 0.16), (dz + 0.01, uu + 0.03, dv1 - 0.11), bevel=0.003, panel=False)
                p.tube("Kit_Structure", (dz + 0.014, uu - 0.028, dv1 - 0.115), (dz + 0.014, uu + 0.028, dv1 - 0.115), 0.006, 10)
                for su in (-0.018, 0.018):
                    p.tube("Kit_Structure", (dz + 0.014, uu + su, dv1 - 0.115), (dz + 0.009, uu + su, dv1 - 0.058), 0.003, 6)
                p.tube("Kit_Signal", (dz + 0.02, uu - 0.024, dv1 - 0.13), (dz + 0.02, uu + 0.024, dv1 - 0.13), 0.007, 10)
            vc = (v0 + v1) / 2
            for side in (-1, 1):
                ue = u0 if side < 0 else u1
                for vb in (vc - 0.06, vc + 0.06):
                    p.box("Kit_Structure", (depth * 0.35, min(ue, ue + side * 0.022), vb - 0.01), (depth * 0.65, max(ue, ue + side * 0.022), vb + 0.01), panel=False)
                p.tube("Kit_Structure", (depth * 0.5, ue + side * 0.018, vc - 0.07), (depth * 0.5, ue + side * 0.018, vc + 0.07), 0.008, 10)
        p.collision_box((0, u0, v0), (depth, u1, v1))
    w.shell_decals(rng, main=False)


def _hand_wheel(p, c, rad, n=12):
    """A valve hand wheel lying flat (axis +Z) at c: a rim of short bars, three spokes, a hub."""
    c = Vector(c)
    pts = [c + Vector((rad * math.cos(2 * math.pi * k / n), rad * math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
    ext = 0.006 * math.tan(math.pi / n)
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        d = (b - a).normalized()
        p.tube("Kit_Signal", a - d * ext, b + d * ext, 0.006, 8, caps=False)
    for k in range(3):
        t = 2 * math.pi * k / 3
        p.tube("Kit_Signal", c, c + Vector((rad * math.cos(t), rad * math.sin(t), 0)), 0.004, 6)
    p.tube("Kit_Structure", c - Vector((0, 0, 0.006)), c + Vector((0, 0, 0.008)), 0.011, 12)


def _pipe_channel(w, rng):
    """Pipes C: a main sunk into a framed channel in the wall at waist height, running through the channel's end
    walls (behind the panels on to the next module), clamped inside, a perforated cover over half of it."""
    L, p = w.L, w.p
    c0, c1 = 0.6, 0.86                                # channel v range, in the main panel
    w.shell(main_split=[(G, L - G, w.main[0], c0 - GAP / 2), (G, L - G, c1 + GAP / 2, w.main[1])])
    u0, u1 = 0.085, L - 0.085
    # the channel: dark back 7 cm deep, metal cheeks top and bottom, end walls, a frame ring on the face
    p.slab("Kit_Seal", w.VERT, 0, L, c0, c1, 0.01, proud=-0.07, panel=False)
    for (a0, a1) in ((c0 - GAP / 2, c0 + 0.012), (c1 - 0.012, c1 + GAP / 2)):
        p.slab("Kit_Structure", w.VERT, G, L - G, a0, a1, 0.07, BEV_SMALL, proud=0.0, panel=False)
    for (e0, e1) in ((G, u0), (u1, L - G)):
        p.slab("Kit_Primary", w.VERT, e0, e1, c0, c1, PT, BEV_MID)
    _frame_ring(w, w.VERT, (u0, u1, c0 + 0.012, c1 - 0.012), t=0.02, proud=0.008)
    z, r = (c0 + c1) / 2, 0.045
    x = -0.03                                         # the pipe's axis 3 cm behind the panel face
    p.tube("Kit_Structure", (x, u0 - 0.01, z), (x, u1 + 0.01, z), r, 20, caps=False)
    for yy in (u0 + 0.004, u1 - 0.004):                 # sleeves where it passes the end walls
        p.tube("Kit_Structure", (x, yy - 0.012, z), (x, yy + 0.012, z), r + 0.014, 20)
    for yc in (0.3, L - 0.3):                        # clamps with their back plates
        p.tube("Kit_Structure", (x, yc - 0.014, z), (x, yc + 0.014, z), r + 0.007, 20)
        p.box("Kit_Structure", (-0.068, yc - 0.03, z - r - 0.012), (-0.05, yc + 0.03, z + r + 0.012), bevel=BEV_SMALL, panel=False)
    for yb in (L * 0.5 - 0.02,):                     # colour code
        p.tube("Kit_Accent", (x, yb - 0.02, z), (x, yb + 0.02, z), r + 0.0015, 20)
        for yy in (yb - 0.026, yb + 0.026):
            p.tube("Kit_Signal", (x, yy - 0.004, z), (x, yy + 0.004, z), r + 0.002, 20)
    # a perforated cover over the right part of the channel, screwed to the frame
    cu0 = L * 0.62
    p.slab("Kit_Trim", w.VERT, cu0, u1 - 0.004, c0 + 0.016, c1 - 0.016, 0.004, BEV_SMALL, proud=0.024, trim="perforated", panel=False)
    for uu in (cu0 + 0.02, u1 - 0.024):
        for vv in (c0 + 0.03, c1 - 0.03):
            p.tube("Kit_Plastic", (0.008, uu, vv), (0.028, uu, vv), 0.005, 8)
    p.collision_box((-0.07, 0, c0), (0.01, L, c1))
    w.label(rng.choice(["label_coolant", "label_o2", "label_hydraulic"]), w.VERT, L * 0.3, c1 + 0.09, 1.0)
    w.shell_decals(rng, main=False)


def pipes(w, var, rng):
    L = w.L
    p = w.p
    if var == "C":
        return _pipe_channel(w, rng)
    w.shell()
    # runs high under the rail or sunk into a wall channel, metal with narrow colour bands: low cream pipes read as
    # "plumbing in the walking zone, white PVC" (critic round 2, 27. 9. 2026)
    if var == "A":
        runs = [(w.vt - 0.2, 0.026, "Kit_Structure"), (w.vt - 0.115, 0.026, "Kit_Structure")]
        x_off = 0.06
    elif var == "B":
        runs = [(w.vt - 0.22, 0.022, "Kit_Structure"), (w.vt - 0.155, 0.022, "Kit_Structure"), (w.vt - 0.09, 0.018, "Kit_Structure")]
        x_off = 0.052
    # each run comes out of the wall and goes back into it inside the module: the old runs stopped at the module
    # end with a flange into nothing or into the next module's locker (critic, 27. 9. 2026); runs across modules
    # come with the pipe bridges of batch 7
    ye = 0.2                                          # clear of the frame: at 0.13 m the pipes "ended blind in the rib"
    for z, r, role in runs:
        R = max(1.2 * r, x_off - 0.03)               # bend radius, leaves a short leg for the wall sleeve
        sides = 20 if r > 0.03 else 14
        p.tube(role, (x_off, ye + R, z), (x_off, L - ye - R, z), r, sides, caps=False)
        for end in (0, 1):
            sy = 1 if end == 0 else -1               # +y from the start end, -y from the far end
            yw = ye if end == 0 else L - ye
            c = Vector((x_off - R, yw + sy * R, z))
            n = 4
            ext = r * math.tan(math.radians(90 / n / 2))
            for k in range(n):
                t0, t1 = math.radians(90 * k / n), math.radians(90 * (k + 1) / n)
                a = c + Vector((R * math.cos(t0), -sy * R * math.sin(t0), 0))
                b = c + Vector((R * math.cos(t1), -sy * R * math.sin(t1), 0))
                d = (b - a).normalized()
                p.tube(role, a - d * ext, b + d * ext, r, sides, caps=False)
            p.tube(role, (x_off - R, yw, z), (0.0, yw, z), r, sides, caps=False)                  # leg into the wall
            p.tube("Kit_Structure", (0.0, yw, z), (0.024, yw, z), r + 0.02, sides, caps=True)       # wall sleeve
            p.tube("Kit_Structure", (0.024, yw, z), (0.032, yw, z), r + 0.009, sides, caps=True)
        for yb in (ye + R + 0.06, L - ye - R - 0.06):  # colour code: a cream band between two orange rings
            p.tube("Kit_Accent", (x_off, yb - 0.02, z), (x_off, yb + 0.02, z), r + 0.0015, sides, caps=False)
            for yy in (yb - 0.026, yb + 0.026):
                p.tube("Kit_Signal", (x_off, yy - 0.004, z), (x_off, yy + 0.004, z), r + 0.002, sides, caps=False)
    for yc in (0.38, L - 0.38):
        # stand-off bracket: a wall plate, an arm, a clamp ring per pipe
        zs = [z for z, _, _ in runs]
        p.box("Kit_Structure", (0.0, yc - 0.04, min(zs) - 0.06), (0.024, yc + 0.04, max(zs) + 0.06), bevel=BEV_SMALL, panel=False)
        for z, r, _ in runs:
            p.box("Kit_Structure", (0.024, yc - 0.012, z - 0.01), (x_off - r, yc + 0.012, z + 0.01), bevel=0.002, panel=False)
            p.tube("Kit_Structure", (x_off, yc - 0.012, z), (x_off, yc + 0.012, z), r + 0.007, 20)
    if var == "A":
        # the service point of the run: a gate valve on the upper pipe, its orange hand wheel
        z, r = runs[1][0], runs[1][1]
        yv = L / 2
        p.tube("Kit_Structure", (x_off, yv - 0.05, z), (x_off, yv + 0.05, z), r + 0.012, 16)
        p.tube("Kit_Structure", (x_off, yv, z + r), (x_off, yv, z + r + 0.035), 0.008, 10)
        _hand_wheel(p, (x_off, yv, z + r + 0.04), 0.045)
    zs = [z for z, _, _ in runs]
    p.collision_box((0, 0, min(zs) - 0.06), (x_off + 0.06, L, max(zs) + 0.06))
    lv = max(zs) + 0.12 if max(zs) + 0.2 < w.main[1] else min(zs) - 0.11
    w.label(rng.choice(["label_coolant", "label_o2", "label_hydraulic"]), w.VERT, L / 2, lv, 1.0)
    w.shell_decals(rng)


def hatch(w, var, rng):
    L = w.L
    p = w.p
    if var == "A":
        holes = [((L - 0.38) / 2, (L + 0.38) / 2, w.main[0] + 0.08, w.main[0] + 0.5)]
    elif var == "B":
        holes = [(0.11, 0.44, 0.16, min(1.06, w.main[1] - 0.05))]
    else:
        holes = [(0.1, 0.55, w.main[0] + 0.1, w.main[0] + 0.55), (L - 0.55, L - 0.1, w.main[0] + 0.1, w.main[0] + 0.55)]
    if var == "B":
        w.shell(skip_main=True, skip_kick=True)
        h = holes[0]
        w.frame_hole("Kit_Primary", w.VERT, G, L - G, w.kick[0], w.kick[1], (h[0], h[1], w.kick[0] - 0.01, w.kick[1] + 0.01), secondary=True)
        w.frame_hole("Kit_Primary", w.VERT, G, L - G, w.main[0], w.main[1], (h[0], h[1], w.main[0] - 0.01, h[3]))
    else:
        w.shell(skip_main=True)
        # the main panel around one or two openings
        cuts = sorted(holes)
        u = G
        for (hu0, hu1, hv0, hv1) in cuts:
            if hu0 - u > 0.01:
                p.slab("Kit_Primary", w.VERT, u, hu0, w.main[0], w.main[1], PT, BEV_MID)
            p.slab("Kit_Primary", w.VERT, hu0, hu1, w.main[0], hv0, PT, BEV_MID)
            p.slab("Kit_Primary", w.VERT, hu0, hu1, hv1, w.main[1], PT, BEV_MID)
            u = hu1
        if L - G - u > 0.01:
            p.slab("Kit_Primary", w.VERT, u, L - G, w.main[0], w.main[1], PT, BEV_MID)
    for i, (hu0, hu1, hv0, hv1) in enumerate(holes):
        # (a flat panel with a sticker, no frame, hinges or latches - critic, 27. 9. 2026)
        # a raised frame ring, the cover 6 mm into the opening over a dark recess, four big quarter-turn fasteners,
        # two hinge barrels on the left
        p.slab("Kit_Seal", w.VERT, hu0, hu1, hv0, hv1, 0.01, proud=-0.035, panel=False)
        _frame_ring(w, w.VERT, (hu0, hu1, hv0, hv1), t=0.028, proud=0.012)
        _gasket(w, w.VERT, (hu0, hu1, hv0, hv1))
        # the cover 16 mm under the frame face ("flush with the wall, cannot tell it opens" - critic round 2)
        p.slab("Kit_Primary", w.VERT, hu0 + 0.006, hu1 - 0.006, hv0 + 0.006, hv1 - 0.006, 0.02, BEV_SMALL, proud=-0.004, secondary=True)
        for uu in (hu0 + 0.04, hu1 - 0.04):
            for vv in (hv0 + 0.04, hv1 - 0.04):
                a = w.world(w.VERT, uu, vv, -0.004)
                p.tube("Kit_Structure", a, a + Vector((0.009, 0, 0)), 0.014, 16)
                p.box("Kit_Seal", (a.x + 0.008, a.y - 0.01, a.z - 0.002), (a.x + 0.0095, a.y + 0.01, a.z + 0.002), panel=False)
        for vv in (hv0 + 0.1, hv1 - 0.1):
            a = w.world(w.VERT, hu0 - 0.012, vv, 0.02)
            p.tube("Kit_Structure", a - Vector((0, 0, 0.04)), a + Vector((0, 0, 0.04)), 0.009, 12)
        if var == "B":
            # orange T-handle
            c = w.world(w.VERT, (hu0 + hu1) / 2, (hv0 + hv1) / 2, -0.004)
            p.tube("Kit_Structure", c, c + Vector((0.004, 0, 0)), 0.02, 16)
            p.tube("Kit_Structure", c, c + Vector((0.032, 0, 0)), 0.008, 12)
            p.tube("Kit_Signal", c + Vector((0.032, -0.05, 0)), c + Vector((0.032, 0.05, 0)), 0.009, 12)
        else:
            # a recessed pull
            c = w.world(w.VERT, (hu0 + hu1) / 2, hv1 - 0.07, -0.004)
            p.box("Kit_Seal", (c.x - 0.004, c.y - 0.05, c.z - 0.015), (c.x + 0.001, c.y + 0.05, c.z + 0.015), bevel=0.003, panel=False)
            p.box("Kit_Signal", (c.x - 0.002, c.y - 0.045, c.z - 0.013), (c.x + 0.0015, c.y + 0.045, c.z - 0.009), panel=False)
        # what is behind it as a small label on the cover, the hazard band along the frame's top edge (not a
        # warning sticker in the middle of a blank panel)
        # what the hatch gives access to: a service panel (A), an inspection hatch (B), the systems behind (C)
        w.label(["label_power", "label_hydraulic"][i % 2] if var == "C" else {"A": "st_service", "B": "st_inspect"}[var],
                w.VERT, (hu0 + hu1) / 2, hv1 - 0.1, 0.75)
        w.label("hazard_subtle", w.VERT, (hu0 + hu1) / 2, hv1 + 0.07, min(1.0, (hu1 - hu0 + 0.056) / 0.36))
    w.shell_decals(rng, main=False)


def display(w, var, rng):
    L = w.L
    p = w.p
    w.shell()
    zc = min(1.02, w.vt - 0.25) if w.vt < 1.5 else 1.4
    if var == "A":
        sw, sh = 0.4, 0.26
        u0, u1 = (L - sw) / 2, (L + sw) / 2
        v0, v1 = zc - sh / 2, zc + sh / 2
        # housing proud 35 mm, bezel, recessed screen over a dark back plate, three labelled keys, two LEDs
        p.box("Kit_Plastic", (0.0, u0 - 0.03, v0 - 0.1), (0.035, u1 + 0.03, v1 + 0.03), bevel=BEV_MID)
        p.box("Kit_Seal", (0.03, u0, v0), (0.036, u1, v1), panel=False)
        p.slab("Kit_Screen", frame((0.037, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0 + 0.008, u1 - 0.008, v0 + 0.008, v1 - 0.008,
               0.001, atlas=(0.0, 0.5, 1.0, 1.0), panel=False)
        p.box("Kit_GlowCool", (0.035, u0, v0 - 0.006), (0.037, u1, v0 - 0.003), panel=False)
        # a cover glass 3 mm in front of the screen, inside the bezel (no glass, no depth - critic, 27. 9. 2026)
        p.slab("Kit_Glass", frame((0.041, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0 + 0.002, u1 - 0.002, v0 + 0.002, v1 - 0.002, 0.002, panel=False)
        for (a0, a1, b0, b1) in ((u0 - 0.03, u0, v0, v1), (u1, u1 + 0.03, v0, v1), (u0 - 0.03, u1 + 0.03, v1, v1 + 0.03)):
            p.box("Kit_Plastic", (0.035, a0, b0), (0.044, a1, b1), bevel=0.002, panel=False)
        keys = ["ck_sys", "ck_comms", "ck_lights"]
        for k in range(3):
            kc = u0 + 0.06 + k * (sw - 0.12) / 2
            # a key in a dark well: the well rim, the key cap 4 mm proud of it, its lit bar
            p.box("Kit_Seal", (0.03, kc - 0.036, v0 - 0.076), (0.0355, kc + 0.036, v0 - 0.034), panel=False)
            p.box("Kit_Plastic", (0.03, kc - 0.029, v0 - 0.069), (0.04, kc + 0.029, v0 - 0.041), bevel=0.004, panel=False)
            p.box("Kit_GlowCool", (0.04, kc - 0.02, v0 - 0.049), (0.0412, kc + 0.02, v0 - 0.045), panel=False)
            w.label(keys[k], frame((0.035, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), kc, v0 - 0.088, 0.6, label=True)
        for k, role in enumerate(("Kit_GlowSignal", "Kit_GlowCool")):
            lc = u1 + 0.012
            p.box(role, (0.035, lc - 0.005, v1 - 0.03 - k * 0.03), (0.04, lc + 0.005, v1 - 0.02 - k * 0.03), panel=False)
        p.collision_box((0, u0 - 0.03, v0 - 0.1), (0.05, u1 + 0.03, v1 + 0.03))
        p.socket("Light_Screen_0", (0.25, L / 2, zc), x=(1, 0, 0), z=(0, 0, 1), type="point", role="cool", cd=0.5, radius_m=1.2, megalights_shadow=False)
    elif var == "B":
        pw, ph = 0.22, 0.16
        u0, u1 = (L - pw) / 2, (L + pw) / 2
        v0, v1 = zc - ph / 2, zc + ph / 2
        p.box("Kit_Plastic", (0.0, u0, v0), (0.03, u1, v1), bevel=BEV_MID)
        p.slab("Kit_Screen", frame((0.031, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0 + 0.015, u1 - 0.015, v1 - 0.075, v1 - 0.015,
               0.001, atlas=(0.125, 0.0, 0.5, 0.25), panel=False)
        p.slab("Kit_Glass", frame((0.034, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0 + 0.012, u1 - 0.012, v1 - 0.078, v1 - 0.012, 0.002, panel=False)
        for k, (role, item) in enumerate((("Kit_GlowCool", "ck_ready"), ("Kit_GlowSignal", "ck_fault"))):
            lu = u0 + 0.04 + k * 0.07
            p.box(role, (0.03, lu - 0.006, v0 + 0.045), (0.035, lu + 0.006, v0 + 0.057), panel=False)
            w.label(item, frame((0.03, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), lu, v0 + 0.028, 0.4, label=True)
        # a rocker
        ru = u1 - 0.04
        p.box("Kit_Seal", (0.028, ru - 0.018, v0 + 0.02), (0.031, ru + 0.018, v0 + 0.07), panel=False)
        p.box("Kit_Plastic", (0.03, ru - 0.014, v0 + 0.03), (0.042, ru + 0.014, v0 + 0.06), bevel=0.003, panel=False)
        w.label("ck_lights", frame((0.03, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), ru, v0 + 0.012, 0.4, label=True)
        p.collision_box((0, u0, v0), (0.045, u1, v1))
    else:  # C: narrow vertical gauge
        gw, gh = 0.07, 0.36
        u0, u1 = (L - gw) / 2, (L + gw) / 2
        v0, v1 = zc - gh / 2, zc + gh / 2
        p.box("Kit_Plastic", (0.0, u0 - 0.015, v0 - 0.03), (0.03, u1 + 0.015, v1 + 0.02), bevel=BEV_MID)
        p.slab("Kit_Screen", frame((0.031, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0, u1, v0, v1, 0.001, atlas=(0.0, 0.0, 0.125, 0.5), panel=False)
        p.slab("Kit_Glass", frame((0.034, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0 - 0.004, u1 + 0.004, v0 - 0.004, v1 + 0.004, 0.002, panel=False)
        w.label("ck_pwr", frame((0.03, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), (u0 + u1) / 2, v0 - 0.016, 0.4, label=True)
        p.collision_box((0, u0 - 0.015, v0 - 0.03), (0.04, u1 + 0.015, v1 + 0.02))
    w.shell_decals(rng)


TYPES = {"Plain": plain, "Grille": grille, "Locker": locker, "Pipes": pipes, "Hatch": hatch, "Display": display}

# batch 1 catalog (section W; the same code builds N and T): (part, length, variant)
BATCH1 = [("Plain", 1.2, "A"), ("Plain", 1.2, "B"), ("Plain", 1.2, "C"), ("Plain", 0.6, "A"), ("Plain", 0.3, "A"),
          ("Grille", 0.6, "A"), ("Grille", 1.2, "B"), ("Grille", 1.2, "C"),
          ("Locker", 0.6, "A"), ("Locker", 0.6, "B"), ("Locker", 1.2, "C"),
          ("Pipes", 1.2, "A"), ("Pipes", 1.2, "B"), ("Pipes", 1.2, "C"),
          ("Hatch", 0.6, "A"), ("Hatch", 0.6, "B"), ("Hatch", 1.2, "C"),
          ("Display", 0.6, "A"), ("Display", 0.6, "B"), ("Display", 0.3, "C")]


def part_name(kind, L, sec, var):
    return "SM_Kit_Wall_%s%02d%s_%s" % (kind, int(round(L * 10)), sec, var)


def build_part(kind, L, sec, var, seed):
    import random
    name = part_name(kind, L, sec, var)
    w = Wall(sec, L, name, seed)
    TYPES[kind](w, var, random.Random(seed))
    return w.p
