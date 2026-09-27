"""Batch 3 of the interior kit (kit_parts.json batch 3, 27. 9. 2026): floor plates, a grating over a service channel,
a floor hatch, a ship's stair and the inner surface of a boarding ramp. The same design language as batches 1-2: the
floor in the dark secondary of the primary paint, the structure layer (edge strips, nosings, stringers, rails) in the
palette's lighter painted metal, anti-slip lanes from the trim sheet at its native scale, the hazard strip at edges
that people step off.

Frames (kit_rules.json pivots, "run"): origin at the module start on the section centreline at floor level, +X along
the run (for the stair and the ramp: up the slope), +Y to the left, +Z up. The walking surface is z = 0 (the stair's
and the ramp's bottom edge); a floor module is the section's width plus 0.1 m each side, under the walls' plinth
recess, so no gap shows along the walls.
"""
import math
import zlib

from mathutils import Vector

import kit_geo
from kit_geo import frame
import kit_batch2
from kit_batch2 import Section, label, BEV_SMALL

G = 0.004            # half a seam between plates
PLATE = 0.02         # plate thickness (top at z = 0)
LANE_W, LANE_P = 0.08, 0.11     # anti-slip lanes: the trim strip's native 80 mm, 11 cm pitch
TOP = frame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))


def _layout(sec):
    """Across the floor (y): the edge strip along each wall, the side plates and the centre walkway."""
    h = sec.half
    hw = h + 0.1                                   # under the plinth recess
    walk = min(0.6, h * 0.5)                       # centre walkway half width (W 0.6, N 0.3)
    edge = h - 0.06                                # the edge strip's inner edge
    return h, hw, walk, edge


def _underlay(p, L, hw, z=-0.05):
    # a dark sheet under everything: the seams between the plates show it, never the void
    p.box("Kit_Seal", (0.0, -hw, z - 0.01), (L, hw, z), panel=False)


def _edge_strips(p, L, h, hw, edge):
    # a raised angle along each wall: the floor's edge reads, and the plinth recess has something to sit on
    for s in (1, -1):
        y0, y1 = sorted((s * edge, s * hw))
        p.box("Kit_Structure", (0.0, y0, -PLATE), (L, y1, 0.004), bevel=BEV_SMALL, segments=1, panel=False)
        # countersunk bolts along it every 0.3 m
        n = max(1, int(round(L / 0.3)))
        for k in range(n):
            x = (k + 0.5) * L / n
            yb = s * (edge + 0.03)
            p.tube("Kit_Structure", (x, yb, 0.004), (x, yb, 0.0055), 0.006, 6)


def _plate(p, x0, x1, y0, y1, secondary=True, bolts=True):
    p.box("Kit_Primary", (x0 + G, y0 + G, -PLATE), (x1 - G, y1 - G, 0.0), bevel=0.003, segments=1, secondary=secondary)
    if bolts:
        for (x, y) in ((x0 + 0.03, y0 + 0.03), (x1 - 0.03, y0 + 0.03), (x0 + 0.03, y1 - 0.03), (x1 - 0.03, y1 - 0.03)):
            p.tube("Kit_Structure", (x, y, 0.0), (x, y, 0.0012), 0.0055, 6)


def _lanes(p, x0, x1, y0, y1, pitch=LANE_P, z=0.0):
    """Anti-slip lanes along the run, 1.5 mm proud of the surface at height z, across y0..y1."""
    n = max(1, int((y1 - y0 + (pitch - LANE_W)) / pitch))
    span = n * pitch - (pitch - LANE_W)
    start = (y0 + y1) / 2 - span / 2
    for k in range(n):
        ya = start + k * pitch
        p.box("Kit_Trim", (x0 + 0.03, ya, z - 0.001), (x1 - 0.03, ya + LANE_W, z + 0.0015), panel=False, trim="antislip_tread")


def _collision(p, L, hw):
    p.collision_box((0.0, -hw, -0.06), (L, hw, 0.0))


# =============================================================================== floor plates
def floor_plate(sec, var, L, name, seed):
    """A: the centre walkway in plates with anti-slip lanes, plain bolted side plates, the edge strips.
    B: the same plates, a painted centre line and hazard strips where the side plates meet the edge strips."""
    p = kit_geo.Part(name, seed)
    h, hw, walk, edge = _layout(sec)
    _underlay(p, L, hw)
    _edge_strips(p, L, h, hw, edge)
    # the centre walkway: one plate across, or two with a seam on the centreline in the wide section
    if walk > 0.45:
        for (y0, y1) in ((-walk, 0.0), (0.0, walk)):
            _plate(p, 0.0, L, y0, y1)
    else:
        _plate(p, 0.0, L, -walk, walk)
    for (y0, y1) in ((walk, edge), (-edge, -walk)):
        _plate(p, 0.0, L, y0, y1, secondary=False)
    if var == "A":
        _lanes(p, 0.0, L, -walk + 0.03, walk - 0.03)
    else:
        # a centre line (paint, signal colour) and thin painted lines at the walkway's edges; no hazard hatching along
        # the walls - it read as a threshold at every door (critic r1: hatching only where one steps off)
        p.box("Kit_Signal", (0.02, -0.012, -0.001), (L - 0.02, 0.012, 0.0008), panel=False)
        for s in (1, -1):
            # cream paint, 2.5 cm, 5 cm in from the walkway's edge (in the structure grey they merged with the plates'
            # chamfers - critic r3)
            y0, y1 = sorted((s * (walk - 0.05), s * (walk - 0.075)))
            p.box("Kit_Accent", (0.02, y0, -0.001), (L - 0.02, y1, 0.0008), panel=False)
        _lanes(p, 0.0, L, -walk + 0.06, -0.05)
        _lanes(p, 0.0, L, 0.05, walk - 0.06)
    _collision(p, L, hw)
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== grating over a service channel
def floor_grille(sec, var, L, name, seed):
    """A grating over a dark service channel down the middle: two pipes and a cable bundle on supports, a dim cool strip
    low on one side so the services read, the grating's bars along the run on cross bars, plates either side."""
    p = kit_geo.Part(name, seed)
    h, hw, walk, edge = _layout(sec)
    cw = 0.3 if sec.key == "W" else 0.24          # channel half width
    depth = 0.2                                    # (0.28 read as a black void under the bars - critic r2)
    _underlay(p, L, hw)
    _edge_strips(p, L, h, hw, edge)
    for (y0, y1) in ((cw + 0.03, edge), (-edge, -cw - 0.03)):
        _plate(p, 0.0, L, y0, y1, secondary=True)
        _lanes(p, 0.0, L, y0 + 0.02, y1 - 0.02)
    # the channel: walls and bottom in the dark primary, the grating's seat angles at the top
    for s in (1, -1):
        y0, y1 = sorted((s * cw, s * (cw + 0.03)))
        p.box("Kit_Primary", (0.0, y0, -depth), (L, y1, -PLATE), panel=False, secondary=True)
        ya, yb = sorted((s * (cw - 0.02), s * (cw + 0.03)))
        p.box("Kit_Structure", (0.0, ya, -0.035), (L, yb, -0.025), bevel=0.002, segments=1, panel=False)
    # the channel bottom in the lighter structure paint, so the pipes stand out against it
    p.box("Kit_Structure", (0.0, -cw, -depth - 0.01), (L, cw, -depth), panel=False)
    # services: a coolant pipe, a smaller water line, a cable bundle; supports every 0.6 m
    rng_off = (zlib.crc32(name.encode()) % 7) * 0.01
    zc = -depth + 0.07                             # the coolant line's axis
    p.tube("Kit_Accent", (0.0, -0.1 * cw / 0.3, zc), (L, -0.1 * cw / 0.3, zc), 0.035, 16, caps=False)
    p.tube("Kit_Structure", (0.0, 0.1 * cw / 0.3, zc - 0.02), (L, 0.1 * cw / 0.3, zc - 0.02), 0.024, 12, caps=False)
    for k, (dy, r) in enumerate(((0.19, 0.012), (0.215, 0.011), (0.2, 0.01))):
        y = dy * cw / 0.3
        p.tube("Kit_Rubber", (0.0, y, -depth + 0.015 + k * 0.006), (L, y, -depth + 0.015 + k * 0.006), r, 8, caps=False)
    n_sup = max(1, int(round(L / 0.6)))
    for k in range(n_sup):
        x = (k + 0.5) * L / n_sup + rng_off
        p.box("Kit_Structure", (x - 0.02, -cw, -depth), (x + 0.02, cw, -depth + 0.03), bevel=0.002, segments=1, panel=False)
        p.box("Kit_Structure", (x - 0.012, -0.1 * cw / 0.3 - 0.045, -depth), (x + 0.012, -0.1 * cw / 0.3 + 0.045, zc + 0.04),
              panel=False)
        # a signal-coloured band round the coolant line at each support
        p.tube("Kit_Signal", (x - 0.03, -0.1 * cw / 0.3, zc), (x + 0.03, -0.1 * cw / 0.3, zc), 0.037, 16, caps=False)
    p.box("Kit_GlowCool", (0.02, -cw + 0.004, -depth + 0.035), (L - 0.02, -cw + 0.01, -depth + 0.05), panel=False)
    # the grating: flat bars along the run 4.5 cm apart, 6 mm thick, on cross bars every 0.3 m (3 cm at 5 mm read as a
    # dark moire rectangle - critic r1), in a raised frame with a chamfer
    nb = int(round(2 * cw / 0.045))
    for k in range(1, nb):
        y = -cw + k * 2 * cw / nb
        p.box("Kit_Structure", (0.02, y - 0.003, -0.03), (L - 0.02, y + 0.003, 0.0), panel=False)
    nc = max(2, int(round(L / 0.3)))
    for k in range(nc + 1):
        x = 0.02 + k * (L - 0.04) / nc
        p.box("Kit_Structure", (x - 0.005, -cw, -0.03), (x + 0.005, cw, -0.014), panel=False)
    for (a0, a1, b0, b1) in ((0.0, L, -cw - 0.03, -cw), (0.0, L, cw, cw + 0.03), (0.0, 0.02, -cw, cw), (L - 0.02, L, -cw, cw)):
        p.box("Kit_Structure", (a0, b0, -0.03), (a1, b1, 0.004), bevel=0.003, segments=1, panel=False)
    # the services lit from inside: a cool linear light along the channel under the grating (the channel read as a void)
    # 1.8 cd per metre: at 5 the cream coolant line burnt out to a white stripe (critic r3)
    kit_batch2.strip_light_along(p, "Light_Channel_0", (L / 2, 0.0, -0.045), (0, 0, -1), (1, 0, 0), L - 0.1, 0.03, "work",
                                 1.8 * L, 0.6)
    _collision(p, L, hw)
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== floor hatch
def floor_hatch(sec, var, L, name, seed):
    """A 0.6 m module with a service hatch in the walkway: a bolted frame, the lid with anti-slip lanes, a flush ring
    handle in a pocket at the front edge, two hinges at the back, the service stencil beside it."""
    p = kit_geo.Part(name, seed)
    h, hw, walk, edge = _layout(sec)
    _underlay(p, L, hw)
    _edge_strips(p, L, h, hw, edge)
    for (y0, y1) in ((walk, edge), (-edge, -walk)):
        _plate(p, 0.0, L, y0, y1, secondary=False)
    s = min(0.46, 2 * walk - 0.1)
    cx, cy = L / 2, 0.0
    x0, x1, y0, y1 = cx - s / 2, cx + s / 2, cy - s / 2, cy + s / 2
    # the walkway plates round the hatch
    for (a0, a1, b0, b1) in ((0.0, L, -walk, y0 - 0.03), (0.0, L, y1 + 0.03, walk), (0.0, x0 - 0.03, y0 - 0.03, y1 + 0.03),
                             (x1 + 0.03, L, y0 - 0.03, y1 + 0.03)):
        if a1 - a0 > 0.02 and b1 - b0 > 0.02:
            _plate(p, a0, a1, b0, b1, bolts=False)
    # the frame: a raised bolted ring in the dark primary with a chamfer (the light structure paint stood out as a
    # bare aluminium frame - critic r2), a rubber seal groove inside it
    for (a0, a1, b0, b1) in ((x0 - 0.03, x1 + 0.03, y0 - 0.03, y0), (x0 - 0.03, x1 + 0.03, y1, y1 + 0.03),
                             (x0 - 0.03, x0, y0, y1), (x1, x1 + 0.03, y0, y1)):
        p.box("Kit_Primary", (a0, b0, -PLATE), (a1, b1, 0.003), bevel=0.003, segments=1, panel=False)
    for (a0, a1, b0, b1) in ((x0, x1, y0, y0 + 0.004), (x0, x1, y1 - 0.004, y1), (x0, x0 + 0.004, y0, y1), (x1 - 0.004, x1, y0, y1)):
        p.box("Kit_Rubber", (a0, b0, -0.012), (a1, b1, -0.0015), panel=False)
    for (x, y) in ((x0 - 0.015, y0 - 0.015), (x1 + 0.015, y0 - 0.015), (x0 - 0.015, y1 + 0.015), (x1 + 0.015, y1 + 0.015)):
        p.tube("Kit_Structure", (x, y, 0.003), (x, y, 0.0045), 0.006, 6)
    # the lid, 2 mm down in the frame with a dark gap round it
    p.box("Kit_Seal", (x0, y0, -0.03), (x1, y1, -0.025), panel=False)
    p.box("Kit_Primary", (x0 + 0.004, y0 + 0.004, -PLATE), (x1 - 0.004, y1 - 0.004, -0.002), bevel=0.003, segments=1)
    _lanes(p, x0 + 0.02, x1 - 0.02, y0 + 0.04, y1 - 0.04, z=-0.002)
    # the recessed lift handle at the front (-X) edge: a pocket with a lit-from-above lip and a flat bar across it
    px = x0 + 0.055
    p.box("Kit_Seal", (px - 0.03, -0.06, -0.018), (px + 0.03, 0.06, -0.0015), panel=False)
    # the pocket's floor in the structure paint: without it the handle read as a black cut into nothing (critic r3)
    p.box("Kit_Structure", (px - 0.028, -0.058, -0.017), (px + 0.028, 0.058, -0.0145), panel=False)
    p.box("Kit_Structure", (px - 0.03, -0.062, -0.0035), (px + 0.03, -0.056, -0.0015), panel=False)
    p.box("Kit_Structure", (px - 0.03, 0.056, -0.0035), (px + 0.03, 0.062, -0.0015), panel=False)
    p.box("Kit_Structure", (px - 0.006, -0.056, -0.012), (px + 0.006, 0.056, -0.004), bevel=0.002, segments=1, panel=False)
    # two quarter-turn latches either side of the handle and two hinges with knuckles at the back (+X) edge
    for yy in (y0 + 0.06, y1 - 0.06):
        p.tube("Kit_Structure", (px, yy, -0.004), (px, yy, -0.0015), 0.014, 12)
        p.box("Kit_Seal", (px - 0.011, yy - 0.0015, -0.0016), (px + 0.011, yy + 0.0015, -0.001), panel=False)
    for yy in (y0 + 0.09, y1 - 0.09):
        # the hinge leaf in the dark primary (in the light structure paint it read as a blank label - critic r3)
        p.box("Kit_Primary", (x1 - 0.05, yy - 0.03, -0.004), (x1 - 0.004, yy + 0.03, -0.0012), bevel=0.002, segments=1,
              panel=False)
        p.tube("Kit_Structure", (x1 + 0.002, yy - 0.03, -0.001), (x1 + 0.002, yy + 0.03, -0.001), 0.007, 12)
    # the lid's countersunk bolts
    for (bx, by) in ((x0 + 0.02, y0 + 0.02), (x1 - 0.02, y0 + 0.02), (x0 + 0.02, y1 - 0.02), (x1 - 0.02, y1 - 0.02)):
        p.tube("Kit_Structure", (bx, by, -0.002), (bx, by, -0.0008), 0.005, 6)
    _collision(p, L, hw)
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (L, 0, 0), x=(1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== stair
RISE, GOING, NOSING = 0.2, 0.25, 0.025


def stair_flight(sec, var, rise_total, name, seed):
    """A ship's stair up `rise_total` (steps of 0.2 m, going 0.25 m, 38.7 deg): treads in the floor plates' dark metal
    with anti-slip lanes, a structure-painted nosing with a lit strip in its face on every step, dark risers, stringers
    either side and a handrail on posts either side, run on 0.3 m at both ends. The walking collision is a ramp."""
    p = kit_geo.Part(name, seed)
    n = max(1, int(round(rise_total / RISE)))
    w = sec.width - 0.1                             # between the stringers
    hw = w / 2
    run = n * GOING
    for i in range(n):
        xa, xb = i * GOING, (i + 1) * GOING
        z = (i + 1) * RISE
        # the tread and its anti-slip lanes
        p.box("Kit_Primary", (xa - NOSING + 0.03, -hw, z - 0.03), (xb, hw, z), bevel=0.003, segments=1, secondary=True)
        _lanes(p, xa - NOSING + 0.03, xb, -hw + 0.04, hw - 0.04, pitch=0.12, z=z)
        # the nosing: a structure-painted lip, a lit strip set into its face (the step edge reads in the dark)
        p.box("Kit_Structure", (xa - NOSING, -hw, z - 0.04), (xa - NOSING + 0.035, hw, z + 0.002), bevel=0.003, segments=1,
              panel=False)
        p.box("Kit_GlowCool", (xa - NOSING - 0.002, -hw + 0.04, z - 0.028), (xa - NOSING, hw - 0.04, z - 0.016), panel=False)
        # the strip lights the step below it (critic r1: the lit edges did nothing to the treads)
        kit_batch2.strip_light_along(p, "Light_Step_%d" % i, (xa - NOSING - 0.004, 0.0, z - 0.022), (-0.6, 0, -0.8), (0, 1, 0),
                                     2 * hw - 0.1, 0.012, "work", 0.08, 0.45)
        # the riser, set back
        p.box("Kit_Primary", (xa - 0.01, -hw, z - RISE), (xa, hw, z - 0.04), panel=False, secondary=True)
    # stringers: a sloped beam either side from the floor to the top
    for s in (1, -1):
        y0, y1 = sorted((s * hw, s * (hw + 0.045)))
        # a closed stringer down to the floor (critic r1: "steps as boxes on a black block"), bolted along its top
        prof = [(-NOSING - 0.02, 0.0), (run, 0.0), (run, rise_total + 0.06), (run - 0.05, rise_total + 0.06),
                (-NOSING - 0.02, 0.26)]
        # (x, z) in the frame's (u, v), extruded along its -z = +Y from y0 to y1 (a right-handed frame: a mirrored one
        # turned the faces inside out after the normals were recalculated)
        mm = frame((0.0, y0, 0.0), (1, 0, 0), (0, 0, 1), (0, -1, 0))
        p.poly_prism("Kit_Structure", prof, mm, y1 - y0, bevel=0.006, segments=1, panel=False)
        for i in range(n):
            bx, bz = (i + 0.5) * GOING, (i + 0.5) * RISE + 0.12
            p.tube("Kit_Structure", (bx, s * (hw + 0.045), bz), (bx, s * (hw + 0.049), bz), 0.007, 6)
        # the handrail 0.9 m above the nosing line on posts at every other step, level runs of 0.3 m at both ends; the
        # rail in the maker's orange, round bends and bolted base plates (critic r1: "a kinked chrome tube, no mounts")
        yr = s * (hw + 0.02)
        a = Vector((-0.3, yr, 0.9))
        b = Vector((0.0, yr, 0.9))
        c = Vector((run, yr, rise_total + 0.9))
        d = Vector((run + 0.3, yr, rise_total + 0.9))
        for (u, v) in ((a, b), (b, c), (c, d)):
            p.tube("Kit_Signal", tuple(u), tuple(v), 0.021, 16)
        for (q, d1, d2) in ((b, (b - a).normalized(), (c - b).normalized()), (c, (c - b).normalized(), (d - c).normalized())):
            # the knee: a short sleeve along the bend's bisector over the joint, so the bend reads round, not kinked
            bis = (d1 + d2).normalized()
            p.tube("Kit_Signal", tuple(q - bis * 0.035), tuple(q + bis * 0.035), 0.025, 16)
        posts = [(i * GOING, i * RISE) for i in list(range(0, n + 1, 2)) + ([n] if n % 2 else [])]
        posts += [(-0.3, 0.0), (run + 0.3, rise_total)]
        for (x, zb) in posts:
            p.tube("Kit_Structure", (x, yr, zb), (x, yr, zb + 0.9), 0.015, 12)
            # a welded saddle under the rail on each post
            p.box("Kit_Structure", (x - 0.025, yr - 0.012, zb + 0.855), (x + 0.025, yr + 0.012, zb + 0.875), bevel=0.003,
                  segments=1, panel=False)
            # a bolted base plate on the tread / floor / deck
            p.box("Kit_Structure", (x - 0.04, yr - 0.04, zb), (x + 0.04, yr + 0.04, zb + 0.008), bevel=0.002, segments=1,
                  panel=False)
            for (ox, oy) in ((-0.028, -0.028), (0.028, -0.028), (-0.028, 0.028), (0.028, 0.028)):
                p.tube("Kit_Structure", (x + ox, yr + oy, zb + 0.008), (x + ox, yr + oy, zb + 0.011), 0.005, 6)
    # the hazard lip where one steps off the top landing onto the stair (the only hatching on the stair - critic r1)
    p.box("Kit_Structure", (run - 0.005, -hw, rise_total - 0.03), (run + 0.07, hw, rise_total + 0.002), bevel=0.002,
          segments=1, panel=False)
    p.box("Kit_Trim", (run + 0.004, -hw + 0.02, rise_total + 0.002), (run + 0.066, hw - 0.02, rise_total + 0.0035),
          panel=False, trim="hazard")
    # walking: a ramp hull from the first nosing to the top (38.7 deg, under the character's walkable angle)
    p.collision_hull([(x, y, z) for y in (-hw, hw) for (x, z) in ((-NOSING, 0.0), (run, rise_total), (run, 0.0))])
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (run, 0, rise_total), x=(1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== boarding ramp
def stair_ramp(sec, var, run, name, seed, rise=0.8):
    """The inner surface of a boarding ramp: `run` m of horizontal run up `rise` (15 deg for 2.9 / 0.8), plates in the
    floor's dark metal with transverse anti-slip ribs every 0.25 m of slope, hazard strips along both edges, curbs,
    a dark underside. The walking collision is the slope."""
    p = kit_geo.Part(name, seed)
    W = sec.width
    hw = W / 2
    ang = math.atan2(rise, run)
    ln = math.hypot(run, rise)
    d = Vector((math.cos(ang), 0.0, math.sin(ang)))
    nrm = Vector((-math.sin(ang), 0.0, math.cos(ang)))
    m = frame((0.0, 0.0, 0.0), tuple(d), (0, 1, 0), tuple(nrm))
    # three plates across, seams along the slope
    for (y0, y1) in ((-hw + 0.08, -0.4), (-0.4, 0.4), (0.4, hw - 0.08)):
        p.slab("Kit_Primary", m, 0.01, ln - 0.01, y0 + G, y1 - G, PLATE, 0.003, segments=1, secondary=True)
    # anti-slip lanes along the slope on every plate (critic r1: "no anti-slip, glossy like wet plastic")
    for (y0, y1) in ((-hw + 0.08, -0.4), (-0.4, 0.4), (0.4, hw - 0.08)):
        n_l = max(1, int((y1 - y0 - 0.06) / LANE_P))
        span = n_l * LANE_P - (LANE_P - LANE_W)
        ys = (y0 + y1) / 2 - span / 2
        for k in range(n_l):
            ya = ys + k * LANE_P
            p.slab("Kit_Trim", m, 0.05, ln - 0.05, ya, ya + LANE_W, 0.0025, proud=0.0015, panel=False, trim="antislip_tread")
    # transverse ribs every 0.25 m of slope (boots and cargo wheels), rubber-capped
    nr = int(ln / 0.25)
    for k in range(1, nr):
        u = k * ln / nr
        p.slab("Kit_Structure", m, u - 0.015, u + 0.015, -hw + 0.12, hw - 0.12, 0.012, 0.003, segments=1, proud=0.012,
               panel=False)
        p.slab("Kit_Rubber", m, u - 0.009, u + 0.009, -hw + 0.14, hw - 0.14, 0.004, proud=0.016, panel=False)
    # hazard strips and curbs along both edges
    for s in (1, -1):
        y0, y1 = sorted((s * (hw - 0.08), s * (hw - 0.14)))
        p.slab("Kit_Trim", m, 0.0, ln, y0, y1, 0.003, proud=0.0015, panel=False, trim="hazard")
        c0, c1 = sorted((s * (hw - 0.08), s * hw))
        p.slab("Kit_Structure", m, 0.0, ln, c0, c1, PLATE + 0.06, 0.006, segments=1, proud=0.06, panel=False)
    # a drainage grille across the foot
    for k in range(int((W - 0.3) / 0.04)):
        yy = -hw + 0.15 + k * 0.04
        p.slab("Kit_Structure", m, 0.03, 0.2, yy - 0.003, yy + 0.003, 0.02, proud=0.004, panel=False)
    # the lip at the bottom edge (it meets the ground) and the underside
    p.slab("Kit_Structure", m, -0.04, 0.01, -hw, hw, 0.03, 0.004, segments=1, proud=0.005, panel=False)
    # the dark sides under the slope, facing out (they show from beside the ramp)
    p.quads("Kit_Seal", [[(0.0, -hw, -0.03), (run, -hw, rise - 0.03), (run, -hw, -0.03)]], toward=(run * 0.6, -5.0, 0.2))
    p.quads("Kit_Seal", [[(0.0, hw, -0.03), (run, hw, -0.03), (run, hw, rise - 0.03)]], toward=(run * 0.6, 5.0, 0.2))
    p.collision_hull([(x, y, z) for y in (-hw, hw) for (x, z) in ((0.0, 0.0), (run, rise), (run, 0.0))])
    p.socket("Snap_Start", (0, 0, 0), x=(-1, 0, 0), z=(0, 0, 1))
    p.socket("Snap_End", (run, 0, rise), x=(1, 0, 0), z=(0, 0, 1))
    return p


# =============================================================================== the batch
# (category, part, size m, section, variant); for the stair the size is its rise, for the ramp its horizontal run
FROM_ABOVE = ((0.35, -0.2, 1.0), (1.0, -0.8, 0.7))
STAIR_VIEW = ((0.3, -1.0, 0.35), (-0.6, -1.0, 0.8))
BATCH3 = [
    ("Floor", "Plate", 1.2, "W", "A"), ("Floor", "Plate", 0.6, "W", "A"), ("Floor", "Plate", 1.2, "W", "B"),
    ("Floor", "Plate", 0.6, "W", "B"),
    ("Floor", "Grille", 1.2, "W", "A"), ("Floor", "Grille", 0.6, "W", "A"),
    ("Floor", "Hatch", 0.6, "W", "A"),
    ("Floor", "Plate", 1.2, "N", "A"), ("Floor", "Plate", 1.2, "N", "B"), ("Floor", "Plate", 0.3, "N", "A"),
    ("Floor", "Grille", 1.2, "N", "A"), ("Floor", "Hatch", 0.6, "N", "A"),
    ("Stair", "Flight", 0.8, "N", "A"),
    ("Stair", "Ramp", 2.9, "W", "A"),
]
VIEWS = {("Floor", "Plate"): FROM_ABOVE, ("Floor", "Grille"): FROM_ABOVE, ("Floor", "Hatch"): FROM_ABOVE,
         ("Stair", "Flight"): STAIR_VIEW, ("Stair", "Ramp"): STAIR_VIEW}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    name = part_name(cat, part, size, sec_key, var)
    sec = Section(sec_key)
    if part == "Plate":
        return floor_plate(sec, var, size, name, seed)
    if part == "Grille":
        return floor_grille(sec, var, size, name, seed)
    if part == "Hatch":
        return floor_hatch(sec, var, size, name, seed)
    if part == "Flight":
        return stair_flight(sec, var, size, name, seed)
    if part == "Ramp":
        return stair_ramp(sec, var, size, name, seed)
    raise ValueError(name)


def budget(cat, part, size):
    b = kit_geo.RULES["tri_budget"]
    if part == "Flight":
        return int(b["Stair_per_step"] * max(1, round(size / RISE)) + 2000)      # + the stringers and rails
    if part == "Ramp":
        return int(b["Floor_per_m"] * size * 2)
    return max(900, int(b["Floor_per_m"] * size * (1.8 if part in ("Grille", "Hatch") else 1.0)))   # (hardware on the hatch)
