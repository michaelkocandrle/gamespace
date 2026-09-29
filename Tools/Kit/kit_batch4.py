"""Batch 4 of the interior kit, first part: component bays (kit_parts.json Wall_ComponentBay, 28. 9. 2026).

A component bay is a wall module (kit_walls.Wall: pivot on the panel face at the floor, face +X into the room,
length along +Y) with a niche through the wall structure towards the hull, and the ship component in it:
  A  power plant: a heavy grille door on hinges, the plant on a sled on pull-out rails, its status screen, power
     cables and coolant lines into the niche, REACTOR S1 and HIGH VOLTAGE plates, a bay light
  B  cooler: the finned core in the lower niche, its exhaust duct rising behind an exhaust grille towards the
     wing root, COOLER S1 plate, a bay light
  C  shield generator: a hatch with quarter-turn latches and an inspection window over the boxed generator,
     its emitter ring glowing through the window, SHIELD GEN S1 plate
The Wayfarer's technical corridor has its S1 components in the walls (layout objects): the kit pilot stood them
in generic grille and hatch walls and they lost their identity (Docs/Reviews/2026-09-28_wayfarer_kit_corridor.md).
Depth: the niche goes BAY_DEPTH behind the panel face - the wall structure (0.2 m) and part of the hull margin
(~1 m behind a W wall at waist height in the Wayfarer, hull_fit_wayfarer_kit_rooms.png).
Every component carries SOCKET_Component (its slot and size) for when components become items of their own.

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- batch4
"""
import json
import math
import os

from mathutils import Vector

import kit_geo
import kit_walls
from kit_geo import frame
from kit_walls import BEV_BIG, BEV_MID, BEV_SMALL, G, PT, Wall, _frame_ring, _gasket, _u_handle

BAY_DEPTH = {"A": 0.55, "B": 0.55, "C": 0.45}
LINER = 0.03                       # the niche's lining plates
SILL = 0.16                        # the niche floor: above the plinth, the component slides out over it
HEAD = 1.02                        # the niche's top: leaves the main panel above it for the component plate


# =============================================================================== the niche
def _bay_shell(w, hole, depth):
    """The wall around an opening hole = (u0, u1, v0, v1) through the kick and main panels, a heavy frame ring
    round it and a lined niche `depth` deep behind it (closed on every side: the geometry check finds holes)."""
    u0, u1, v0, v1 = hole
    p, L = w.p, w.L
    t = LINER
    w.shell(skip_main=True, skip_kick=True, backing_hole=(u0 - t, u1 + t, v0 - t, v1 + t))
    k0, k1 = w.kick
    w.frame_hole("Kit_Primary", w.VERT, G, L - G, k0, k1, (u0, u1, v0, k1 + 0.01), secondary=True)
    w.frame_hole("Kit_Primary", w.VERT, G, L - G, w.main[0], w.main[1], (u0, u1, w.main[0] - 0.01, v1))
    # the brushed kick plate either side of the opening (the plain shell's plate runs the whole module)
    for (a0, a1) in ((G, u0), (u1, L - G)):
        if a1 - a0 > 0.02:
            p.slab("Kit_Trim", w.VERT, a0, a1, k0, k0 + 0.1, 0.006, BEV_SMALL, proud=0.003, trim="kickplate", panel=False)
    # the lining: sill, head, cheeks, back wall in the lighter structure metal - in the wall's dark paint the niche read
    # as a black void round the component (critic r3); SC's bays are light inside
    p.box("Kit_Structure", (-depth, u0, v0 - t), (0.0, u1, v0), bevel=BEV_SMALL, segments=1)
    p.box("Kit_Structure", (-depth, u0, v1), (0.0, u1, v1 + t))
    for (a0, a1) in ((u0 - t, u0), (u1, u1 + t)):
        p.box("Kit_Structure", (-depth, a0, v0 - t), (0.0, a1, v1 + t))
    p.box("Kit_Structure", (-depth - t, u0 - t, v0 - t), (-depth, u1 + t, v1 + t))
    # two ribs up the back wall and one across the head in the dark paint: the niche is structure, not a box
    for yy in (u0 + 0.12, u1 - 0.12):
        p.box("Kit_Primary", (-depth, yy - 0.02, v0), (-depth + 0.03, yy + 0.02, v1), bevel=BEV_SMALL, segments=1, panel=False)
    p.box("Kit_Primary", (-depth, u0, v1 - 0.04), (-depth + 0.035, u1, v1), bevel=BEV_SMALL, segments=1, panel=False)
    # a housed dim strip across the back wall under the head: the niche's back reads above the component (it read as
    # a black void and the cooler's exhaust ran into the dark - verification round, author 29. 9. 2026)
    zb0, zb1 = v1 - 0.075, v1 - 0.047
    p.box("Kit_Primary", (-depth, u0 + 0.03, zb0), (-depth + 0.02, u1 - 0.03, zb1), bevel=0.002, segments=1, panel=False)
    p.box("Kit_GlowDim", (-depth + 0.02, u0 + 0.042, zb0 + 0.007), (-depth + 0.023, u1 - 0.042, zb1 - 0.007), panel=False)
    # the heavy frame ring and its gasket
    _frame_ring(w, w.VERT, hole, t=0.035, proud=0.015)
    _gasket(w, w.VERT, hole)
    # dirt along the sill's front edge, where the component comes out (a maintained ship: dirt where it builds up)
    w.grime("rim", w.VERT, (u0 + u1) / 2, k0 + 0.03, (0, 1), (u1 - u0, 0.06), 0.8)


def _bay_light(w, hole, depth):
    """A linear fixture under the niche's head at its front, lighting the component (neutral white)."""
    u0, u1, v0, v1 = hole
    p = w.p
    a0, a1 = u0 + 0.05, u1 - 0.05
    # behind the door's track under the head (x -0.04 .. -0.012)
    p.box("Kit_Structure", (-0.125, a0, v1 - 0.022), (-0.05, a1, v1), bevel=BEV_SMALL, segments=1, panel=False)
    p.box("Kit_GlowNeutral", (-0.11, a0 + 0.012, v1 - 0.026), (-0.065, a1 - 0.012, v1 - 0.022), panel=False)
    d = Vector((-0.45, 0.0, -0.89)).normalized()
    w.p.socket("Light_Bay_0", (-0.0875, (u0 + u1) / 2, v1 - 0.03), x=tuple(d), z=(0, 1, 0), type="rect", role="neutral",
               cd=round(1.6 * (a1 - a0), 3), width_cm=round((a1 - a0 - 0.024) * 100, 1), height_cm=4.0, radius_m=0.55,
               dir_ue=[round(d.x, 4), round(-d.y, 4), round(d.z, 4)], megalights_shadow=False, interior_only=True)


def _screen(p, x, u0, u1, v0, v1, region):
    """A status screen on the plane x (facing +X) under a cover glass, in a dark bezel."""
    kit = json.load(open(os.path.join(kit_geo.ROOT, "ArtSource", "Kit", "Textures", "screens_index.json")))
    p.box("Kit_Plastic", (x, u0 - 0.012, v0 - 0.012), (x + 0.012, u1 + 0.012, v1 + 0.012), bevel=0.003, panel=False)
    p.slab("Kit_Screen", frame((x + 0.0125, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0, u1, v0, v1, 0.001,
           atlas=tuple(kit[region]), panel=False)
    p.slab("Kit_Glass", frame((x + 0.0155, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), u0 - 0.002, u1 + 0.002, v0 - 0.002, v1 + 0.002, 0.002, panel=False)


def _casing_label(p, item, x, u, v, scale):
    """A label on a component's front (the plane x, facing +X), shot from 3 cm: a ray from further out hit the bars
    of the bay's grille door first."""
    p.decal(item, (x + 0.03, u, v), (x - 0.02, u, v), scale=scale, frame_xy=[[0, 1, 0], [0, 0, 1]], label=True)


def _plate_above(w, item, u, hole):
    """The component's plate on the main panel between the frame ring and the rail."""
    w.label(item, w.VERT, u, (hole[3] + 0.035 + w.main[1]) / 2, 1.0)


def _jamb_lights(w, hole):
    """Glowing strips down both jambs of an open bay, in housings, seen from the corridor: the head fixture's light
    showed no source (critic r1: "the niche glows with no fixture")."""
    u0, u1, v0, v1 = hole
    p = w.p
    # (a 4 cm housing and a 2.6 cm diffuser read as "thin burnt lines, an artefact" - critic r3)
    for (a0, a1, g0, g1) in ((u0, u0 + 0.016, u0 + 0.016, u0 + 0.019), (u1 - 0.016, u1, u1 - 0.019, u1 - 0.016)):
        p.box("Kit_Primary", (-0.115, a0, v0 + 0.11), (-0.05, a1, v1 - 0.07), bevel=0.003, segments=1, panel=False)
        # the dim warm glow with the fixtures' dark bezel (kit_geo BEZEL_ROLES): neutral white and then the walls'
        # warm strip emission burnt out to flat white bars (critic r2, author 29. 9. 2026)
        p.box("Kit_GlowDim", (-0.102, g0, v0 + 0.13), (-0.063, g1, v1 - 0.09), panel=False)


def _sill_hazard(p, hole):
    """A hazard band across the sill behind the door track, 4.5 cm (critic r1: the 6.5 cm band read as catalogue)."""
    u0, u1, v0, v1 = hole
    p.box("Kit_Trim", (-0.09, u0 + 0.03, v0), (-0.045, u1 - 0.01, v0 + 0.003), trim="hazard", panel=False)


# =============================================================================== A: power plant
def _open_door(w, hole):
    """The bay's sliding door, open: its track under the head and in the sill, the leaf's edge 4 cm out of the pocket
    slot at the left cheek with an orange edge band and a recessed pull (SC shows the component whole with the bay
    door open - ComponentBays_VideoNotes 3:36; a closed grille of bars every 5 cm read as a prison cell, render
    28. 9. 2026; a 1.6 cm edge did not read as a door - critic r1)."""
    u0, u1, v0, v1 = hole
    p = w.p
    p.box("Kit_Structure", (-0.04, u0, v1 - 0.026), (-0.012, u1, v1), bevel=BEV_SMALL, segments=1, panel=False)
    p.box("Kit_Seal", (-0.034, u0, v1 - 0.03), (-0.018, u1, v1 - 0.026), panel=False)
    p.box("Kit_Seal", (-0.036, u0, v0 - 0.004), (-0.016, u1, v0 + 0.0008), panel=False)
    p.box("Kit_Seal", (-0.036, u0 - 0.004, v0), (-0.016, u0 + 0.001, v1 - 0.026), panel=False)
    p.box("Kit_Primary", (-0.033, u0, v0 + 0.004), (-0.019, u0 + 0.04, v1 - 0.03), bevel=0.002, segments=1)
    p.box("Kit_Signal", (-0.032, u0 + 0.04, v0 + 0.006), (-0.02, u0 + 0.046, v1 - 0.032), bevel=0.0015, segments=1, panel=False)
    zc = (v0 + v1) / 2
    p.box("Kit_Seal", (-0.0205, u0 + 0.012, zc - 0.07), (-0.0185, u0 + 0.03, zc + 0.07), bevel=0.001, segments=1, panel=False)


def _clamp(p, x_front, y, z_top, strut_to):
    """An orange cradle clamp hooking a casing's top front edge at z_top: a plate down the front, a plate over the
    edge, a bolt, and a strut in the structure metal up to the niche's head (SC: bright U-clamps hold the component
    top and bottom - ComponentBays_VideoNotes 3:36)."""
    p.box("Kit_Signal", (x_front - 0.002, y - 0.024, z_top - 0.075), (x_front + 0.016, y + 0.024, z_top + 0.016), bevel=0.004, segments=1, panel=False)
    p.box("Kit_Signal", (x_front - 0.1, y - 0.024, z_top), (x_front + 0.016, y + 0.024, z_top + 0.016), bevel=0.004, segments=1, panel=False)
    p.tube("Kit_Structure", (x_front + 0.016, y, z_top - 0.045), (x_front + 0.022, y, z_top - 0.045), 0.009, 6)
    p.box("Kit_Structure", (x_front - 0.085, y - 0.016, z_top + 0.016), (x_front - 0.045, y + 0.016, strut_to), bevel=BEV_SMALL, segments=1, panel=False)


def _clamp_foot(p, x_front, y, z_sled, z_up):
    """The bottom clamp: a plate up the casing's front from the sled to z_up, bolted, on a foot bolted to the sled."""
    p.box("Kit_Signal", (x_front - 0.002, y - 0.024, z_sled), (x_front + 0.016, y + 0.024, z_up), bevel=0.004, segments=1, panel=False)
    p.box("Kit_Signal", (x_front - 0.002, y - 0.032, z_sled), (x_front + 0.04, y + 0.032, z_sled + 0.012), bevel=0.003, segments=1, panel=False)
    p.tube("Kit_Structure", (x_front + 0.016, y, z_up - 0.03), (x_front + 0.022, y, z_up - 0.03), 0.009, 6)
    for yb in (y - 0.022, y + 0.022):
        p.tube("Kit_Structure", (x_front + 0.028, yb, z_sled + 0.012), (x_front + 0.028, yb, z_sled + 0.018), 0.006, 6)


def _screws(p, x, pts, r=0.006):
    """Screw heads on the plane x (facing +X)."""
    for (y, z) in pts:
        p.tube("Kit_Structure", (x - 0.001, y, z), (x + 0.004, y, z), r, 8)
        p.box("Kit_Seal", (x + 0.0035, y - r * 0.8, z - 0.0012), (x + 0.0045, y + r * 0.8, z + 0.0012), panel=False)


def _valve(p, x, y, z, side):
    """A quarter-turn valve where a line enters a niche cheek: its body on the cheek (side +1: the cheek at +y facing
    -y) and an orange lever along the line."""
    s = side
    y0, y1 = sorted((y, y - s * 0.035))
    p.box("Kit_Structure", (x - 0.035, y0, z - 0.028), (x + 0.035, y1, z + 0.028), bevel=0.004, segments=1, panel=False)
    p.tube("Kit_Structure", (x, y - s * 0.035, z), (x, y - s * 0.05, z), 0.012, 10)
    p.box("Kit_Signal", (x - 0.004, y - s * 0.05 - 0.005, z - 0.007), (x + 0.075, y - s * 0.05 + 0.005, z + 0.007), bevel=0.002, segments=1, panel=False)


def power_plant(w, rng):
    L, p = w.L, w.p
    D = BAY_DEPTH["A"]
    hole = (0.1, L - 0.1, SILL, HEAD)
    u0, u1, v0, v1 = hole
    _bay_shell(w, hole, D)
    _bay_light(w, hole, D)
    _jamb_lights(w, hole)
    _open_door(w, hole)
    _sill_hazard(p, hole)
    cx0, cx1 = -D + 0.06, -0.09
    cy0, cy1 = u0 + 0.14, u1 - 0.14
    z0 = v0 + 0.022
    # pull-out rails on the sill either side of the plant, where they show, their orange end stops, and the sled on
    # four roller carriages (rails under the sled did not show - critic r1)
    for yy in (u0 + 0.07, u1 - 0.07):
        p.box("Kit_Structure", (-D + 0.12, yy - 0.016, v0), (-0.05, yy + 0.016, v0 + 0.024), bevel=BEV_SMALL, segments=1, panel=False)
        p.box("Kit_Seal", (-D + 0.12, yy - 0.005, v0 + 0.02), (-0.052, yy + 0.005, v0 + 0.0245), panel=False)
        p.box("Kit_Signal", (-0.075, yy - 0.02, v0 + 0.022), (-0.05, yy + 0.02, v0 + 0.05), bevel=0.003, segments=1, panel=False)
        sy0, sy1 = sorted((yy, u0 + 0.12 if yy < L / 2 else u1 - 0.12))
        for xx in (cx0 + 0.1, cx1 - 0.06):
            p.box("Kit_Structure", (xx - 0.03, yy - 0.02, v0 + 0.024), (xx + 0.03, yy + 0.02, v0 + 0.05), bevel=0.003, segments=1, panel=False)
            p.tube("Kit_Rubber", (xx, yy - 0.021, v0 + 0.037), (xx, yy + 0.021, v0 + 0.037), 0.009, 10)
            p.box("Kit_Structure", (xx - 0.015, sy0, v0 + 0.03), (xx + 0.015, sy1, v0 + 0.045), panel=False)
    p.box("Kit_Structure", (-D + 0.05, u0 + 0.12, z0), (-0.075, u1 - 0.12, z0 + 0.02), bevel=BEV_SMALL, segments=1, panel=False)
    # the plant: a heavy cream casing with big radii, a lifting plate on top - no fins (fins and a big vent read as a
    # second cooler, critic r1: the plant needs a sign of power)
    cz0, cz1 = z0 + 0.02, 0.84
    p.box("Kit_Accent", (cx0, cy0, cz0), (cx1, cy1, cz1), bevel=0.03, segments=3)
    p.box("Kit_Primary", (cx0 + 0.02, cy0 + 0.02, cz0 - 0.004), (cx1 + 0.004, cy1 - 0.02, cz0 + 0.05), bevel=0.006, segments=1, panel=False)
    p.box("Kit_Seal", (cx1 - 0.002, cy0 + 0.03, 0.5), (cx1 + 0.0015, cy1 - 0.03, 0.504), panel=False)
    p.box("Kit_Structure", (cx0 + 0.05, cy0 + 0.05, cz1 - 0.004), (cx1 - 0.05, cy1 - 0.05, cz1 + 0.012), bevel=0.004, segments=1, panel=False)
    for yy in (cy0 + 0.2, cy1 - 0.2):
        xm = (cx0 + cx1) / 2
        p.box("Kit_Structure", (xm - 0.03, yy - 0.012, cz1 + 0.012), (xm + 0.03, yy + 0.012, cz1 + 0.03), panel=False)
        p.tube("Kit_Structure", (xm, yy - 0.008, cz1 + 0.05), (xm, yy + 0.008, cz1 + 0.05), 0.024, 14)
        p.tube("Kit_Seal", (xm, yy - 0.0085, cz1 + 0.05), (xm, yy + 0.0085, cz1 + 0.05), 0.012, 12)
    _screws(p, cx1, [(cy0 + 0.035, cz0 + 0.075), (cy1 - 0.035, cz0 + 0.075), (cy0 + 0.035, cz1 - 0.045), (cy1 - 0.035, cz1 - 0.045)])
    # the control module on the right of the front: a thick dark bezel, the status screen, three LEDs
    mu0, mu1 = cy1 - 0.3, cy1 - 0.04
    p.box("Kit_Plastic", (cx1 - 0.01, mu0, 0.53), (cx1 + 0.018, mu1, 0.79), bevel=0.012, segments=2)
    _screen(p, cx1 + 0.018, mu0 + 0.05, mu0 + 0.18, 0.62, 0.75, "reactor")
    for k, role in enumerate(("Kit_GlowCool", "Kit_GlowCool", "Kit_GlowSignal")):
        yy = mu0 + 0.212 + k * 0.02
        p.box(role, (cx1 + 0.018, yy - 0.006, 0.7), (cx1 + 0.022, yy + 0.006, 0.712), panel=False)
    # the core viewport on the left of the front: a box proud of the casing with a heavy dark bezel, the core's glow at
    # its back, the finned core cylinder across it and a cover glass (two flat glowing slits read as a toaster - critic r2)
    ky0, ky1 = cy0 + 0.06, mu0 - 0.05
    kz0, kz1 = 0.6, 0.745
    kf = cx1 + 0.07
    for (a0, a1, b0, b1) in ((ky0, ky0 + 0.022, kz0, kz1), (ky1 - 0.022, ky1, kz0, kz1), (ky0 + 0.022, ky1 - 0.022, kz0, kz0 + 0.022),
                             (ky0 + 0.022, ky1 - 0.022, kz1 - 0.022, kz1)):
        p.box("Kit_Plastic", (cx1 - 0.006, a0, b0), (kf, a1, b1), bevel=0.006, segments=1)
    p.box("Kit_GlowSignal", (cx1 - 0.001, ky0 + 0.022, kz0 + 0.022), (cx1 + 0.004, ky1 - 0.022, kz1 - 0.022), panel=False)
    kc = ((kz0 + kz1) / 2)
    xk = cx1 + 0.035
    p.tube("Kit_Structure", (xk, ky0 + 0.022, kc), (xk, ky1 - 0.022, kc), 0.015, 16)
    nfin = 9
    for k in range(nfin):
        yf = ky0 + 0.04 + k * (ky1 - ky0 - 0.08) / (nfin - 1)
        p.tube("Kit_Structure", (xk, yf - 0.003, kc), (xk, yf + 0.003, kc), 0.026, 16)
    p.slab("Kit_Glass", frame((kf - 0.004, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), ky0 + 0.02, ky1 - 0.02, kz0 + 0.02, kz1 - 0.02, 0.003, panel=False)
    # two carry handles low on the front
    _u_handle(p, cx1, (cy0 + 0.08, 0.4), (cy0 + 0.26, 0.4))
    _u_handle(p, cx1, (cy1 - 0.26, 0.4), (cy1 - 0.08, 0.4))
    # the cradle: orange clamps on the top and bottom front edges, struts to the head and down to the sled
    for yy in (cy0 + 0.1, cy1 - 0.1):
        _clamp(p, cx1, yy, cz1, v1 - 0.04)
        _clamp_foot(p, cx1, yy, z0 + 0.02, cz0 + 0.09)
    # power: the HV connector on the front of the top with its locking lever, the orange HV cable up to the niche's
    # head (in sight from the corridor, critic r1), two black cables from the back
    hx0, hx1, hy0, hy1 = cx1 - 0.11, cx1 - 0.02, cy0 + 0.3, cy0 + 0.39
    p.box("Kit_Structure", (hx0, hy0, cz1 + 0.01), (hx1, hy1, cz1 + 0.06), bevel=0.006, segments=1, panel=False)
    # the lever lies against the connector's face (1 mm off it, the geometry check found it floating)
    p.tube("Kit_Signal", (hx1 + 0.005, hy0 - 0.01, cz1 + 0.045), (hx1 + 0.005, hy1 + 0.01, cz1 + 0.045), 0.007, 10)
    xc, yc = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    p.tube("Kit_Structure", (xc, yc, cz1 + 0.06), (xc, yc, cz1 + 0.085), 0.034, 14)
    p.tube("Kit_Signal", (xc, yc, cz1 + 0.085), (xc, yc, v1), 0.024, 14, caps=False)
    p.tube("Kit_Structure", (xc, yc, v1 - 0.035), (xc, yc, v1), 0.036, 14)
    for k in range(2):
        yy = cy0 + 0.14 + k * 0.06
        xb = cx0 + 0.04
        p.tube("Kit_Structure", (xb, yy, cz1 - 0.01), (xb, yy, cz1 + 0.035), 0.026, 12)
        p.tube("Kit_Rubber", (xb, yy, cz1 + 0.035), (xb, yy, v1), 0.016, 12, caps=False)
        p.tube("Kit_Structure", (xb, yy, v1 - 0.03), (xb, yy, v1), 0.028, 12)
    # coolant: supply and return from the plant's right side into the niche cheek through quarter-turn valves
    for k, zz in enumerate((0.3, 0.41)):
        xx = cx0 + 0.2
        p.tube("Kit_Accent", (xx, cy1 - 0.01, zz), (xx, u1 - 0.03, zz), 0.02, 12, caps=False)
        p.tube("Kit_Signal" if k == 0 else "Kit_Structure", (xx, cy1 - 0.005, zz), (xx, cy1 + 0.022, zz), 0.029, 12)
        _valve(p, xx, u1, zz, 1)
    # (no bus bars in the left gap: dark tubes deep in the shadow beside the door read as loose pipes - critic r2)
    # plates: the component and the voltage warning above the opening; the maker's mark and the HV warning on the casing
    _plate_above(w, "plate_reactor", u0 + 0.2, hole)
    _plate_above(w, "warn_hv", u1 - 0.18, hole)
    _casing_label(p, "maker_veyra", cx1, L / 2, 0.45, 0.85)
    # how it comes out, on the casing by the handles (critic r3: "not visible how it is swapped")
    _casing_label(p, "st_rails", cx1, L / 2, 0.33, 0.9)
    # screws along the seam and a capped service port low on the right (critic r3: "a smooth box")
    _screws(p, cx1, [(cy0 + 0.06 + k * (cy1 - cy0 - 0.12) / 7, zz) for k in range(8) for zz in (0.488, 0.516)], r=0.0045)
    p.tube("Kit_Plastic", (cx1 - 0.002, cy1 - 0.058, 0.34), (cx1 + 0.014, cy1 - 0.058, 0.34), 0.02, 14)
    p.tube("Kit_Signal", (cx1 + 0.012, cy1 - 0.058, 0.34), (cx1 + 0.02, cy1 - 0.058, 0.34), 0.014, 14)
    _casing_label(p, "warn_hv", cx1, (ky0 + ky1) / 2, 0.572, 0.6)
    # dirt: soot at the casing's foot, a rim under the core viewport
    p.grime("soot", (cx1, (cy0 + cy1) / 2, cz0 + 0.07), (1, 0, 0), (0, 0, -1), (cy1 - cy0 - 0.1, 0.08), 0.6)
    p.socket("Component", (cx0 + (cx1 - cx0) / 2, (cy0 + cy1) / 2, z0), x=(1, 0, 0), z=(0, 0, 1), slot="power_plant", size=1)
    w.shell_decals(rng, main=False)


# =============================================================================== B: cooler
def cooler(w, rng):
    L, p = w.L, w.p
    D = BAY_DEPTH["B"]
    hole = (0.09, L - 0.09, SILL, HEAD)
    u0, u1, v0, v1 = hole
    _bay_shell(w, hole, D)
    _bay_light(w, hole, D)
    _jamb_lights(w, hole)
    _open_door(w, hole)
    _sill_hazard(p, hole)
    # the cooler: a cream casing on two feet, the finned core a block proud of its front (shown whole, like the plant:
    # a louvre grille over the upper opening hid it and the core read as a black screen - render 28. 9. 2026)
    cx0, cx1 = -D + 0.05, -0.16
    cy0, cy1 = u0 + 0.03, u1 - 0.03
    cz0, cz1 = v0 + 0.04, 0.7
    for yy in (cy0 + 0.05, cy1 - 0.05):
        p.box("Kit_Structure", (cx0 + 0.02, yy - 0.03, v0), (cx1 - 0.01, yy + 0.03, cz0), bevel=0.003, segments=1, panel=False)
        _clamp_foot(p, cx1, yy, v0, cz0 + 0.045)
    p.box("Kit_Accent", (cx0, cy0, cz0), (cx1, cy1, cz1), bevel=0.025, segments=3)
    # the core: a dark back plate, bright fins 3 mm thick every 14 mm standing 5 cm off it, a frame and a cross bar
    fy0, fy1, fz0, fz1 = cy0 + 0.035, cy1 - 0.035, cz0 + 0.07, 0.56
    cf = cx1 + 0.06
    p.box("Kit_Primary", (cx1 - 0.005, fy0, fz0), (cx1 + 0.004, fy1, fz1), panel=False)
    for (a0, a1, c0, c1) in ((fy0 - 0.018, fy0, fz0 - 0.018, fz1 + 0.018), (fy1, fy1 + 0.018, fz0 - 0.018, fz1 + 0.018),
                             (fy0, fy1, fz0 - 0.018, fz0), (fy0, fy1, fz1, fz1 + 0.018)):
        p.box("Kit_Structure", (cx1 - 0.005, a0, c0), (cf, a1, c1), bevel=0.003, segments=1, panel=False)
    nf = int((fy1 - fy0) / 0.014)
    for k in range(nf):
        yy = fy0 + (k + 0.5) * (fy1 - fy0) / nf
        p.box("Kit_Structure", (cx1 + 0.004, yy - 0.0015, fz0), (cf - 0.004, yy + 0.0015, fz1), panel=False)
    zm = (fz0 + fz1) / 2
    p.box("Kit_Structure", (cf - 0.012, fy0, zm - 0.008), (cf, fy1, zm + 0.008), bevel=0.002, segments=1, panel=False)
    # grab handles up both sides of the core frame (critic r1: "no handles, no clamps - how does it come out")
    _u_handle(p, cf, (fy0 - 0.009, fz0 + 0.06), (fy0 - 0.009, fz1 - 0.06))
    _u_handle(p, cf, (fy1 + 0.009, fz0 + 0.06), (fy1 + 0.009, fz1 - 0.06))
    # the status screen in the band over the core, between the clamps (no maker's mark: no room on a 0.6 m cooler)
    ym = (cy0 + cy1) / 2
    _screen(p, cx1, ym - 0.04, ym + 0.04, 0.595, 0.672, "cooler")
    # coolant loop A: two couplings low on the front, their hoses bending down into ports in the sill with valve levers
    # (two bare coupling ends read as "forgotten spheres", critic r1)
    for k, yy in enumerate((ym - 0.035, ym + 0.035)):
        zz = fz0 - 0.042
        xe = cx1 + 0.07
        p.tube("Kit_Structure", (cx1, yy, zz), (cx1 + 0.03, yy, zz), 0.014, 8)
        p.tube("Kit_Signal" if k == 0 else "Kit_Accent", (cx1 + 0.018, yy, zz), (cx1 + 0.03, yy, zz), 0.017, 8)
        p.tube("Kit_Rubber", (cx1 + 0.03, yy, zz), (xe, yy, zz), 0.013, 8, caps=False)
        p.tube("Kit_Rubber", (xe, yy, zz + 0.013), (xe, yy, v0 + 0.012), 0.013, 8, caps=False)
        p.tube("Kit_Structure", (xe, yy, v0), (xe, yy, v0 + 0.018), 0.02, 8)
        p.box("Kit_Signal", (xe - 0.004, yy - 0.004, v0 + 0.006), (xe + 0.05, yy + 0.004, v0 + 0.014), bevel=0.002, segments=1, panel=False)
    # the cradle clamps on the top front edge
    for yy in (cy0 + 0.06, cy1 - 0.06):
        _clamp(p, cx1, yy, cz1, v1 - 0.04)
    # the exhaust: a round duct from the casing's top, flanged, bending back into the niche's back wall (towards the
    # wing root) through a bolted flange plate, ribbed where it is flexible
    xd, yd, r = -0.31, (cy0 + cy1) / 2, 0.065
    zt = cz1 + 0.02
    p.tube("Kit_Structure", (xd, yd, cz1 - 0.01), (xd, yd, zt), r + 0.014, 12)
    zb = zt + 0.04
    p.tube("Kit_Structure", (xd, yd, zt), (xd, yd, zb), r, 12, caps=False)
    R = 0.13
    c = Vector((xd - R, yd, zb))
    segs = 4
    ext = r * math.tan(math.radians(90 / segs / 2))
    for k in range(segs):
        t0, t1 = math.radians(90 * k / segs), math.radians(90 * (k + 1) / segs)
        a = c + Vector((R * math.cos(t0), 0, R * math.sin(t0)))
        bb = c + Vector((R * math.cos(t1), 0, R * math.sin(t1)))
        dd = (bb - a).normalized()
        p.tube("Kit_Rubber", a - dd * ext, bb + dd * ext, r, 12, caps=False)
        p.tube("Kit_Structure", bb - dd * 0.004, bb + dd * 0.004, r + 0.006, 12)
    zc = zb + R
    p.tube("Kit_Rubber", (xd - R, yd, zc), (-D + 0.045, yd, zc), r, 12, caps=False)
    p.tube("Kit_Structure", (xd - R - 0.048, yd, zc), (xd - R - 0.032, yd, zc), r + 0.01, 12)
    fz_hi = min(zc + 0.1, v1 - 0.045)
    p.box("Kit_Structure", (-D + 0.03, yd - 0.1, zc - 0.1), (-D + 0.045, yd + 0.1, fz_hi), bevel=0.003, segments=1, panel=False)
    for (yb, zbolt) in ((yd - 0.08, zc - 0.08), (yd + 0.08, zc - 0.08), (yd - 0.08, fz_hi - 0.02), (yd + 0.08, fz_hi - 0.02)):
        p.tube("Kit_Structure", (-D + 0.045, yb, zbolt), (-D + 0.051, yb, zbolt), 0.007, 6)
    _plate_above(w, "plate_cooler", L / 2, hole)
    # dirt: streaks under the core, where the air leaves (author 28. 9.: streaks under the grilles)
    p.grime("streaks", (cx1 + 0.001, ym, fz0 - 0.03), (1, 0, 0), (0, 0, 1), (fy1 - fy0, 0.05), 0.6)
    p.socket("Component", ((cx0 + cx1) / 2, (cy0 + cy1) / 2, v0), x=(1, 0, 0), z=(0, 0, 1), slot="cooler", size=1)
    w.shell_decals(rng, main=False)


# =============================================================================== C: shield generator
def shield_generator(w, rng):
    L, p = w.L, w.p
    D = BAY_DEPTH["C"]
    hole = (0.1, L - 0.1, SILL, HEAD)
    u0, u1, v0, v1 = hole
    _bay_shell(w, hole, D)
    # the generator behind the hatch: a cream box, its emitter ring glowing in a dark recess in its front
    gx0, gx1 = -D + 0.04, -0.09
    gy0, gy1 = u0 + 0.16, u1 - 0.16
    p.box("Kit_Structure", (gx0, gy0 + 0.04, v0), (gx1 - 0.02, gy1 - 0.04, v0 + 0.05), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Accent", (gx0, gy0, v0 + 0.05), (gx1, gy1, v1 - 0.08), bevel=BEV_BIG, segments=2)
    wu0, wu1, wv0, wv1 = (L / 2 - 0.19, L / 2 + 0.19, 0.64, 0.86)
    # the emitter a little under the window's middle: seen from a standing eye 1.3 m away the view through the window
    # falls ~5 cm on the generator's face 9 cm behind it (at the middle it showed only the ring's top - shots 28. 9.)
    ec = Vector((gx1, L / 2, (wv0 + wv1) / 2 - 0.055))
    p.tube("Kit_Seal", ec + Vector((-0.03, 0, 0)), ec + Vector((0.002, 0, 0)), 0.1, 24)
    n, rr = 18, 0.075
    pts = [ec + Vector((0.004, rr * math.cos(2 * math.pi * k / n), rr * math.sin(2 * math.pi * k / n))) for k in range(n)]
    ex = 0.011 * math.tan(math.pi / n)
    for k in range(n):
        a, bb = pts[k], pts[(k + 1) % n]
        dd = (bb - a).normalized()
        p.tube("Kit_GlowCool", a - dd * ex, bb + dd * ex, 0.011, 8, caps=False)
    p.tube("Kit_Structure", ec + Vector((-0.02, 0, 0)), ec + Vector((0.03, 0, 0)), 0.035, 16)
    for k in range(4):
        t = math.radians(45 + 90 * k)
        a = ec + Vector((0.01, 0.042 * math.cos(t), 0.042 * math.sin(t)))
        bb = ec + Vector((0.01, 0.068 * math.cos(t), 0.068 * math.sin(t)))
        p.tube("Kit_Structure", a, bb, 0.006, 6)
    # the hatch over the whole opening, flush with the wall face inside the proud frame ring, the window cut out of it
    hu0, hu1, hv0, hv1 = u0 + 0.006, u1 - 0.006, v0 + 0.006, v1 - 0.006
    win = (wu0, wu1, wv0, wv1)
    # the pieces round the window without bevels (bevelled, they read as three panels with seams down the hatch) and a
    # bevelled rim round the hatch's edge
    # the hatch face in the lighter structure metal inside a dark painted rim: in the wall's paint it read as one more
    # wall panel (critic r2)
    # 8 mm under its rim (critic r3: "one flat board")
    HF = -0.008
    for (a0, a1, b0, b1) in ((hu0, wu0, hv0, hv1), (wu1, hu1, hv0, hv1), (wu0, wu1, hv0, wv0), (wu0, wu1, wv1, hv1)):
        p.slab("Kit_Structure", w.VERT, a0, a1, b0, b1, 0.02, proud=HF)
    for (a0, a1, b0, b1) in ((hu0, hu0 + 0.03, hv0, hv1), (hu1 - 0.03, hu1, hv0, hv1), (hu0 + 0.03, hu1 - 0.03, hv0, hv0 + 0.03),
                             (hu0 + 0.03, hu1 - 0.03, hv1 - 0.03, hv1)):
        p.slab("Kit_Primary", w.VERT, a0, a1, b0, b1, 0.01, BEV_SMALL, secondary=True, proud=0.003)
    _frame_ring(w, w.VERT, win, t=0.016, proud=0.01)
    _gasket(w, w.VERT, win)
    p.slab("Kit_Glass", frame((-0.012, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), wu0, wu1, wv0, wv1, 0.003, panel=False)
    # four quarter-turn latches, two hinges on the left, a recessed pull on the right
    # quarter-turn latches 48 mm across with a tool slot and an orange index mark (critic r1: "four small dots")
    for uu in (hu0 + 0.055, hu1 - 0.055):
        for vv in (hv0 + 0.055, hv1 - 0.055):
            a = w.world(w.VERT, uu, vv, HF)
            # (disc latches with a slot read as screws - verification round; a wing to turn by hand does not)
            p.tube("Kit_Seal", a + Vector((-0.002, 0, 0)), a + Vector((0.003, 0, 0)), 0.036, 16)
            p.tube("Kit_Structure", a, a + Vector((0.009, 0, 0)), 0.026, 16)
            p.box("Kit_Signal", (a.x + 0.009, a.y - 0.03, a.z - 0.007), (a.x + 0.024, a.y + 0.03, a.z + 0.007), bevel=0.003, segments=1, panel=False)
            p.box("Kit_Signal", (a.x + 0.003, a.y - 0.004, a.z + 0.03), (a.x + 0.007, a.y + 0.004, a.z + 0.042), panel=False)
    for vv in (hv0 + 0.16, hv1 - 0.16):
        a = w.world(w.VERT, hu0 + 0.012, vv, 0.012)
        p.tube("Kit_Structure", a - Vector((0, 0, 0.05)), a + Vector((0, 0, 0.05)), 0.011, 12)
    # an orange grab handle opposite the hinges (the recessed pull did not read as a way to open it - critic r1)
    _u_handle(p, HF, (hu1 - 0.075, 0.4), (hu1 - 0.075, 0.6))
    # the air intake low on the hatch, the status screen beside the window
    p.slab("Kit_Trim", frame((HF + 0.001, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), hu0 + 0.12, hu1 - 0.16, hv0 + 0.08, hv0 + 0.18,
           0.003, trim="vent_slots", panel=False)
    _screen(p, HF, wu1 + 0.07, wu1 + 0.17, 0.7, 0.8, "shield")
    _plate_above(w, "plate_shield", u0 + 0.2, hole)
    # on a dark plate of its own (verification round: grey text on the bare metal did not read)
    ic = (hu0 + hu1) / 2
    p.slab("Kit_Plastic", w.VERT, ic - 0.12, ic + 0.12, hv0 + 0.215, hv0 + 0.265, 0.004, 0.0015, proud=HF + 0.003, panel=False)
    p.decal("st_inspect", w.world(w.VERT, ic, hv0 + 0.24, HF + 0.04), w.world(w.VERT, ic, hv0 + 0.24, HF - 0.01), scale=1.1,
            frame_xy=[[0, 1, 0], [0, 0, 1]], label=True)
    # the emitter's light behind the window: it lights the generator's face and the window's frame (critic r1: "a
    # painted ring that lights nothing")
    p.socket("Light_Emitter_0", (gx1 + 0.05, L / 2, ec.z), x=(1, 0, 0), z=(0, 0, 1), type="point", role="cool", cd=0.25,
             radius_m=0.35, megalights_shadow=False, interior_only=True)
    # dirt along the hatch's bottom edge
    w.grime("soot", w.VERT, L / 2, hv0 + 0.05, (0, -1), (hu1 - hu0 - 0.1, 0.1), 0.6)
    p.socket("Component", ((gx0 + gx1) / 2, L / 2, v0), x=(1, 0, 0), z=(0, 0, 1), slot="shield_generator", size=1)
    w.shell_decals(rng, main=False)


VARIANTS = {"A": power_plant, "B": cooler, "C": shield_generator}

# =============================================================================== the batch
# (category, part, size m, section, variant)
BATCH4 = [("Wall", "ComponentBay", 1.2, "W", "A"), ("Wall", "ComponentBay", 0.6, "W", "B"), ("Wall", "ComponentBay", 1.2, "W", "C")]
BAY_VIEW = ((1, 0, 0.12), (1, -0.9, 0.35))
VIEWS = {("Wall", "ComponentBay"): BAY_VIEW}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    import random
    name = part_name(cat, part, size, sec_key, var)
    w = Wall(sec_key, size, name, seed)
    VARIANTS[var](w, random.Random(seed))
    return w.p


def budget(cat, part, size):
    b = kit_geo.RULES["tri_budget"]
    # a bay is a wall module plus the component in it, which costs the same in a 0.6 m bay as in a 1.2 m one: the
    # wall's budget plus a fitting's
    return int(b["Wall_base"] + b["Wall_per_m"] * size + b["Fitting"])
