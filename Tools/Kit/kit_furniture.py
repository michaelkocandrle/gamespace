"""Cabin furniture of the interior kit (kit_parts.json batch "furniture", 30. 9. 2026).

The author approved the Wayfarer's cabin from the kit and asked for its furniture as kit parts, not one-offs for the
ship: a berth with shelves and a reading light, a suit locker, a hygiene cell and a food dispenser - the four boxes
hs_interior built for the approved layout (Wayfarer_layout.json, each with its purpose). The SC references
(starcitizenreference/Screenshot 2026-09-25 021316 / 021331: a berth alcove with padded walls, a lamp in its corner,
orange edges; storage lockers with orange handles; a galley unit with a dispenser bay) set the level: every part a
carcass with frames, doors and fittings in the kit's language - the warm graphite paint, the lighter structure metal,
orange signal parts, housed lights, screens in the cold UI.

For a hull liner room (section L, kit_liner.py): the back edge stands WALL_GAP off the liner's face - clear of its
frames (8 cm) - and nothing rises above the liner's chamfer (vertical to 1.7 m, then 0.75 m in per metre up).
  Bunk     21  berth 2.1 x 0.85: alcove cheeks to 1.72 m, the mattress in three tufted cushions, pillow, blanket, two
               shelves with retaining bars, padded back rolls, a reading lamp with its switch, a dim strip under the
               lower shelf; the base with the life support's air intake and the kit's recessed plinth. The liner stays
               visible between the back rolls and the shelves (its section number and life support label).
  Locker   10  suit and weapon locker 0.95 x 0.55 x 1.8: a tall suit door with a window (a hanger rail and a dim light
               inside), a narrow weapon door with a lock cylinder and an orange lever latch, a boot drawer, a status
               light, vent slots.
  Hygiene  15  hygiene cell 1.45 x 1.0 x 2.05: side walls following the chamfer, a recessed sliding door in a proud
               frame (built closed), an occupancy screen, an extraction grille and its duct to the ceiling, corner posts,
               kick plates.
  Food     16  galley unit 1.6 x 0.45 at 0.8-1.8 m: a chilled cabinet and a ration drawer, the counter, a water
               dispenser bay (nozzle, drip grille, bay light) in a cream fascia beside its screen and buttons, stowage
               doors above; under it a fold-down seat on its struts with a back cushion.
Frame: kit_rules "faced" pivot - on the floor under the middle of the back edge, front +X, width along +Y (the viewer's
right facing the front), z up.

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- furniture
"""
from mathutils import Vector

import kit_geo
from kit_batch2 import BEV_MID, BEV_SMALL, label
from kit_geo import frame

WALL_GAP = 0.1               # back edge to the liner's face (its frames stand 8 cm off it)
LINER_VT, LINER_RUN = 1.7, 0.75
FRAME_OUT = 0.08             # the liner's exposed frames: 8 cm off the panels, up the chamfer too (kit_liner FL_OUT)
FRONT = frame((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))      # u along +Y, v up, w out of the front (+X)


def top_at(x, margin=0.02):
    """The highest a part may reach x in front of its back edge: under the liner's chamfer and the frames standing
    FRAME_OUT off it at every module joint - the chamfer's plane moved FRAME_OUT along its normal (0.8, -0.6) drops by
    FRAME_OUT / 0.6 (kit_clash.py found the berth's back and the galley's top in the frames, 30. 9. 2026)."""
    return LINER_VT + (x + WALL_GAP) / LINER_RUN - FRAME_OUT / 0.6 - margin


def front_plate(p, role, x, y0, y1, z0, z1, t=0.02, bevel=BEV_SMALL, pressed=False, secondary=False, panel=True):
    """A plate facing +X with its face on the plane x; pressed: the face inset 4 cm and set back 6 mm."""
    return p.slab(role, FRONT, y0, y1, z0, z1, t, bevel, 1, proud=x, secondary=secondary, panel=panel,
                  inset=(0.04, 0.006) if pressed and min(y1 - y0, z1 - z0) > 0.14 else None)


def ring(p, role, x, y0, y1, z0, z1, w, depth, bevel=0.003, bottom=True):
    """Four members round an opening y0..y1 x z0..z1 on the plane x, w wide, standing depth proud of it (a doorway's
    without the bottom one)."""
    members = [(y0 - w, y1 + w, z1, z1 + w), (y0 - w, y0, z0, z1), (y1, y1 + w, z0, z1)]
    if bottom:
        members.append((y0 - w, y1 + w, z0 - w, z0))
    for (a0, a1, b0, b1) in members:
        p.box(role, (x, a0, b0), (x + depth, a1, b1), bevel=bevel, segments=1, panel=False)


def bar_handle(p, x, y, z0, z1):
    """An upright U handle off a face at x: two standoffs and the grip, 4 cm out."""
    for zz in (z0, z1):
        p.tube("Kit_Structure", (x - 0.002, y, zz), (x + 0.04, y, zz), 0.007, 8)
    p.tube("Kit_Structure", (x + 0.04, y, z0 - 0.01), (x + 0.04, y, z1 + 0.01), 0.009, 10)


def pull(p, x, y0, y1, z):
    """A horizontal pull off a face at x (drawers, cabinet doors)."""
    for yy in (y0, y1):
        p.tube("Kit_Structure", (x - 0.002, yy, z), (x + 0.035, yy, z), 0.007, 8)
    p.tube("Kit_Structure", (x + 0.035, y0 - 0.01, z), (x + 0.035, y1 + 0.01, z), 0.009, 10)


def hinge(p, x, y, z0, z1):
    p.tube("Kit_Structure", (x + 0.006, y, z0), (x + 0.006, y, z1), 0.008, 10)


def plinth(p, x_front, y0, y1, h=0.08, back=0.05):
    """The kit's recessed plinth under a carcass: a dark recess set back, a housed cool strip in it."""
    p.box("Kit_Seal", (0.0, y0, 0.0), (x_front - back, y1, h), panel=False)
    p.box("Kit_Structure", (x_front - back, y0 + 0.01, 0.028), (x_front - back + 0.012, y1 - 0.01, 0.056), bevel=0.002, segments=1, panel=False)
    p.box("Kit_GlowCool", (x_front - back + 0.012, y0 + 0.02, 0.036), (x_front - back + 0.015, y1 - 0.02, 0.048), panel=False)


def grille(p, x, y0, y1, z0, z1, pitch=0.026):
    """A framed louvre grille over a dark plenum on the plane x (air in or out)."""
    ring(p, "Kit_Structure", x, y0, y1, z0, z1, 0.02, 0.018)
    p.box("Kit_Seal", (x - 0.03, y0, z0), (x + 0.004, y1, z1), panel=False)
    n = max(2, int((z1 - z0) / pitch))
    for k in range(n):
        z = z0 + (k + 0.5) * (z1 - z0) / n
        p.box("Kit_Structure", (x - 0.004, y0, z - 0.005), (x + 0.012, y1, z + 0.005), panel=False)


def screen(p, x, y0, y1, z0, z1, region):
    """A small display on the plane x: a bezel ring and the page (kit_screens.py region) 1 mm proud."""
    ring(p, "Kit_Plastic", x, y0, y1, z0, z1, 0.012, 0.01, bevel=0.002)
    p.box("Kit_Seal", (x - 0.006, y0, z0), (x + 0.004, y1, z1), panel=False)
    p.slab("Kit_Screen", FRONT, y0, y1, z0, z1, 0.001, proud=x + 0.005, atlas=tuple(region), panel=False)


def cushion(p, lo, hi, r=0.03):
    """A padded block: soft rounded edges (three segments)."""
    p.box("Kit_Cushion", lo, hi, bevel=r, segments=3, panel=False)


# =============================================================================== the berth
def bunk(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D = 0.85
    hw = L / 2                       # outer half width
    iw = hw - 0.03                   # between the cheeks
    zp = 0.42                        # the platform's top
    # the cheeks at the head and the foot: the bed's sides, then stepping back to carry the shelves (the alcove)
    zt = top_at(0.0)                 # 1.66 at the back
    prof = [(0.0, 0.0), (D, 0.0), (D, 0.72), (0.32, 0.98), (0.32, 1.72), ((1.72 - zt) * LINER_RUN + 0.01, 1.72), (0.0, zt)]
    assert all(z <= top_at(x) for x, z in prof)
    for s in (1, -1):
        m = frame((0, s * hw, 0), (1, 0, 0), (0, 0, 1), (0, s, 0))
        p.poly_prism("Kit_Primary", prof, m, 0.03, bevel=0.004, segments=1)
        # an orange edge strip down each cheek's front (the reference's berth frame), 1 cm proud
        p.box("Kit_Signal", (D, s * (hw - 0.022) - 0.006, 0.12), (D + 0.008, s * (hw - 0.022) + 0.006, 0.7), panel=False)
    # the base: pressed front with the life support's air intake, the recessed plinth under it
    plinth(p, D - 0.03, -iw, iw)
    front_plate(p, "Kit_Primary", D - 0.03, -iw, -0.31, 0.08, zp - 0.02, pressed=True)
    front_plate(p, "Kit_Primary", D - 0.03, 0.31, iw, 0.08, zp - 0.02, pressed=True)
    front_plate(p, "Kit_Primary", D - 0.03, -0.31, 0.31, 0.08, 0.13, panel=False)
    front_plate(p, "Kit_Primary", D - 0.03, -0.31, 0.31, zp - 0.07, zp - 0.02, panel=False)
    grille(p, D - 0.03, -0.29, 0.29, 0.15, zp - 0.09)
    p.box("Kit_Seal", (0.0, -iw, 0.08), (D - 0.05, iw, zp - 0.02), panel=False)       # the cavity's back behind the front
    # the platform and its front rail (a lip that keeps the mattress on in low gravity)
    p.box("Kit_Structure", (0.0, -iw, zp - 0.02), (D, iw, zp), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (D - 0.035, -iw, zp), (D, iw, zp + 0.05), bevel=0.004, segments=1, panel=False)
    # the mattress in three tufted cushions, a pillow at the head (-Y), the blanket folded at the foot
    n = 3
    span = 2 * iw - 0.01
    for k in range(n):
        y0 = -iw + 0.005 + k * span / n
        cushion(p, (0.03, y0 + 0.004, zp), (D - 0.04, y0 + span / n - 0.004, zp + 0.14), r=0.035)
    cushion(p, (0.1, -iw + 0.04, zp + 0.14), (0.52, -iw + 0.38, zp + 0.235), r=0.04)
    p.box("Kit_Fabric", (0.05, iw - 0.42, zp + 0.14), (D - 0.07, iw - 0.05, zp + 0.18), bevel=0.015, segments=2, panel=False)
    # the back: a panel behind the rolls, one behind the shelves; between them the liner shows (its section number)
    front_plate(p, "Kit_Primary", 0.02, -iw, iw, zp, 1.02, pressed=True)
    front_plate(p, "Kit_Primary", 0.02, -iw, iw, 1.28, zt, pressed=True)
    # (into the pressed panel's 6 mm inset: the rounded rolls hung 6 mm off it - geometry check)
    for (z0, z1) in ((0.6, 0.8), (0.8, 1.0)):
        cushion(p, (0.013, -iw + 0.02, z0 + 0.004), (0.1, iw - 0.02, z1 - 0.004), r=0.03)
    # two shelves between the cheeks: a lip at the front, a retaining bar over it
    for zs in (1.28, 1.56):
        p.box("Kit_Structure", (0.02, -iw, zs - 0.02), (0.31, iw, zs), bevel=0.003, segments=1, panel=False)
        p.box("Kit_Structure", (0.295, -iw, zs), (0.31, iw, zs + 0.03), bevel=0.002, segments=1, panel=False)
        p.tube("Kit_Structure", (0.3, -iw, zs + 0.085), (0.3, iw, zs + 0.085), 0.006, 8)
        for yy in (-iw + 0.015, iw - 0.015):
            p.tube("Kit_Structure", (0.3, yy, zs + 0.03), (0.3, yy, zs + 0.085), 0.006, 8)
    # the berth light: a dim warm strip under the lower shelf, down on the mattress
    p.box("Kit_Structure", (0.19, -iw + 0.09, 1.253), (0.29, iw - 0.09, 1.26), panel=False)
    p.box("Kit_GlowDim", (0.2, -iw + 0.1, 1.248), (0.28, iw - 0.1, 1.253), panel=False, bezel_face=-1)
    p.socket("Light_Berth_0", (0.3, 0.0, 1.2), x=(0, 0, -1), z=(1, 0, 0), type="point", role="warm", cd=2.0, radius_m=1.4,
             source_radius_cm=20.0)
    # the reading lamp on the head cheek's inner face, aimed at the pillow; its switch under it
    yl = -iw
    p.box("Kit_Structure", (0.17, yl, 1.07), (0.27, yl + 0.05, 1.16), bevel=0.006, segments=2, panel=False)
    p.box("Kit_Seal", (0.18, yl + 0.05, 1.08), (0.26, yl + 0.054, 1.15), panel=False)
    p.box("Kit_GlowWarm", (0.195, yl + 0.054, 1.095), (0.245, yl + 0.057, 1.135), panel=False, bezel_face=1)
    d = Vector((0.2, 0.5, -0.6)).normalized()
    p.socket("Light_Reading_0", (0.22, yl + 0.07, 1.1), x=tuple(d), z=(1, 0, 0), type="spot", role="warm", cd=25.0,
             cone_deg=60.0, radius_m=1.8, source_radius_cm=2.0, dir_ue=[d.x, -d.y, d.z])
    p.box("Kit_Plastic", (0.17, yl, 0.88), (0.27, yl + 0.012, 0.96), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (0.19, yl + 0.012, 0.9), (0.21, yl + 0.02, 0.94), panel=False)
    p.box("Kit_GlowSignal", (0.245, yl + 0.012, 0.93), (0.255, yl + 0.015, 0.94), panel=False)
    label(p, "st_service", (D - 0.03 - 0.003, -0.5, 0.26), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.4, True)
    p.grime("soot", (D - 0.03, 0.0, 0.1), (1, 0, 0), (0, 0, -1), (2 * iw - 0.1, 0.1), 0.8)
    p.collision_box((0.0, -hw, 0.0), (D, hw, zp + 0.2))
    return p


# =============================================================================== the suit and weapon locker
def locker(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D, H = 0.55, 1.8
    hw = L / 2
    fx = D                               # the carcass front
    # the carcass: sides, top, back, the recessed plinth
    zc = top_at(0.0)
    xc = (H - zc) * LINER_RUN + 0.005                 # the back top edge chamfered under the liner's frames
    prof = [(0.0, 0.0), (D, 0.0), (D, H), (xc, H), (0.0, zc)]
    for s in (1, -1):
        p.poly_prism("Kit_Primary", prof, frame((0, s * hw, 0), (1, 0, 0), (0, 0, 1), (0, s, 0)), 0.025, bevel=0.004, segments=1)
    yi = hw - 0.025
    p.box("Kit_Primary", (xc, -yi, H - 0.03), (D, yi, H), bevel=0.003, segments=1)
    p.quads("Kit_Primary", [[(0.0, -yi, zc), (xc, -yi, H), (xc, yi, H), (0.0, yi, zc)]], toward=(-1.0, 0.0, 4.0))
    p.box("Kit_Seal", (0.0, -yi, 0.08), (0.02, yi, zc), panel=False)
    plinth(p, fx, -hw + 0.025, hw - 0.025)
    # the front frame: outer members, the mullion between the doors, the rail over the boot drawer
    yi0, yi1, zi0, zi1 = -hw + 0.055, hw - 0.055, 0.11, H - 0.06
    ring(p, "Kit_Structure", fx, yi0, yi1, zi0, zi1, 0.03, 0.016)
    ym = hw - 0.055 - 0.32                # the weapon door's inner edge
    p.box("Kit_Structure", (fx, ym - 0.03, 0.35), (fx + 0.016, ym, zi1), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (fx, yi0, 0.35), (fx + 0.016, yi1, 0.38), bevel=0.003, segments=1, panel=False)
    # the suit door: a window over the hanger rail, vent slots low, the U handle at its meeting edge, hinges outside
    dy0, dy1, dz0, dz1 = yi0 + 0.004, ym - 0.034, 0.384, zi1 - 0.004
    wy0, wy1, wz0, wz1 = dy0 + 0.1, dy1 - 0.1, 0.98, dz1 - 0.12
    for (a0, a1, b0, b1) in ((dy0, dy1, dz0, wz0), (dy0, dy1, wz1, dz1), (dy0, wy0, wz0, wz1), (wy1, dy1, wz0, wz1)):
        front_plate(p, "Kit_Primary", fx + 0.01, a0, a1, b0, b1, secondary=True)
    ring(p, "Kit_Structure", fx + 0.01, wy0, wy1, wz0, wz1, 0.014, 0.008, bevel=0.002)
    p.box("Kit_Glass", (fx - 0.004, wy0, wz0), (fx, wy1, wz1), panel=False)
    p.tube("Kit_Structure", (0.28, -hw + 0.025, wz1 - 0.06), (0.28, ym - 0.03, wz1 - 0.06), 0.01, 10)  # the hanger rail
    p.box("Kit_GlowDim", (0.2, wy0, H - 0.035), (0.36, wy1, H - 0.03), panel=False, bezel_face=-1)
    df = fx + 0.01                       # the doors' faces, 6 mm behind the frame's
    for k in range(5):
        z = 0.5 + k * 0.024
        p.box("Kit_Seal", (df - 0.004, dy0 + 0.08, z), (df + 0.0012, dy1 - 0.08, z + 0.01), panel=False)
    bar_handle(p, df, dy1 - 0.04, 1.0, 1.3)
    for zz in ((dz0 + 0.1, dz0 + 0.22), (dz1 - 0.22, dz1 - 0.1)):
        hinge(p, df + 0.002, dy0 + 0.004, *zz)
    # the weapon door: a pressed door, a lock cylinder and an orange lever latch at its meeting edge
    ey0, ey1 = ym + 0.004, yi1 - 0.004
    front_plate(p, "Kit_Primary", df, ey0, ey1, dz0, dz1, t=0.02, pressed=True, secondary=True)
    c = (df, ey0 + 0.06, 1.12)
    p.tube("Kit_Structure", c, (c[0] + 0.012, c[1], c[2]), 0.016, 14)
    p.box("Kit_Seal", (c[0] + 0.012, c[1] - 0.002, c[2] - 0.008), (c[0] + 0.0135, c[1] + 0.002, c[2] + 0.008), panel=False)
    p.box("Kit_Structure", (df, ey0 + 0.035, 1.2), (df + 0.012, ey0 + 0.085, 1.34), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Signal", (df + 0.012, ey0 + 0.045, 1.215), (df + 0.026, ey0 + 0.075, 1.325), bevel=0.003, segments=1, panel=False)
    for zz in ((dz0 + 0.1, dz0 + 0.22), (dz1 - 0.22, dz1 - 0.1)):
        hinge(p, df + 0.002, ey1 - 0.004, *zz)
    # the boot drawer: its front and a horizontal pull
    front_plate(p, "Kit_Primary", df, yi0 + 0.004, yi1 - 0.004, zi0 + 0.004, 0.346, pressed=True, secondary=True)
    pull(p, df, -0.12, 0.12, 0.25)
    # a status light on the frame's head
    p.box("Kit_GlowCool", (fx + 0.016, yi1 - 0.06, zi1 + 0.01), (fx + 0.019, yi1 - 0.03, zi1 + 0.02), panel=False)
    label(p, "st_inspect", (df, (ey0 + ey1) / 2, 0.62), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.4, True)
    p.grime("soot", (df, 0.0, 0.14), (1, 0, 0), (0, 0, -1), (L - 0.2, 0.08), 0.8)
    p.collision_box((0.0, -hw, 0.0), (D + 0.06, hw, H))
    return p


# =============================================================================== the hygiene cell
def hygiene(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D, H = 1.0, 2.05
    hw = L / 2
    # the roof: sloped under the chamfer, then a notch under the liner's cable tray (on the chamfer 0.27-0.34 m off the
    # face, down to 1.99 m - the first roof at 2.05 ran into it), then flat at the cell's height
    zb, zn = top_at(0.0), 1.95
    xn = (zn - zb) * LINER_RUN
    xs = (H - top_at(0.0, 0.0)) * LINER_RUN + 0.02    # the flat roof clear of the frames' line by 2 cm
    prof = [(0.0, 0.0), (D, 0.0), (D, H), (xs, H), (xs, zn), (xn, zn), (0.0, zb)]
    assert all(z <= top_at(x) + 1e-6 for x, z in prof)
    for s in (1, -1):
        m = frame((0, s * hw, 0), (1, 0, 0), (0, 0, 1), (0, s, 0))
        p.poly_prism("Kit_Primary", prof, m, 0.03, bevel=0.004, segments=1)
    # the roof's plates; the extraction fan on it, its duct up into the ceiling
    yi = hw - 0.03
    p.box("Kit_Primary", (xs, -yi, H - 0.03), (D, yi, H), panel=False)
    p.box("Kit_Primary", (xn, -yi, zn - 0.03), (xs, yi, zn), panel=False)
    p.box("Kit_Primary", (xs - 0.03, -yi, zn), (xs, yi, H - 0.03), panel=False)
    p.quads("Kit_Primary", [[(0.0, -yi, zb), (xn, -yi, zn), (xn, yi, zn), (0.0, yi, zb)]], toward=(1.0, 0.0, 4.0))
    # (0.39-0.67 m out: at 0.75 its box reached the ceiling services' strut channels - kit_clash.py)
    p.box("Kit_Structure", (0.39, -0.16, H), (0.67, 0.16, H + 0.08), bevel=0.006, segments=1)
    p.tube("Kit_Rubber", (0.53, 0.0, H + 0.08), (0.53, 0.0, 2.31), 0.05, 14, caps=False)
    for zc in (H + 0.08, 2.28):
        p.tube("Kit_Structure", (0.53, 0.0, zc - 0.012), (0.53, 0.0, zc + 0.012), 0.058, 14)
    # the front wall either side of the doorway and over it (pressed panels), kick plates at their foot
    dw, dh = 0.4, 1.97
    fx = D
    for (y0, y1) in ((-hw, -dw - 0.04), (dw + 0.04, hw)):
        front_plate(p, "Kit_Primary", fx, y0, y1, 0.0, H, t=0.03, pressed=True)
        p.slab("Kit_Trim", FRONT, y0 + 0.02, y1 - 0.02, 0.01, 0.11, 0.006, BEV_SMALL, 1, proud=fx + 0.003, trim="kickplate", panel=False)
    front_plate(p, "Kit_Primary", fx, -dw - 0.04, dw + 0.04, dh + 0.04, H, t=0.03)
    # corner posts in the structure metal, the door's frame proud of the wall
    for s in (1, -1):
        p.box("Kit_Structure", (fx - 0.035, min(s * (hw - 0.035), s * (hw + 0.005)), 0.0), (fx + 0.012, max(s * (hw - 0.035), s * (hw + 0.005)), H),
              bevel=0.004, segments=1, panel=False)
    ring(p, "Kit_Structure", fx, -dw, dw, 0.0, dh, 0.04, 0.02, bottom=False)
    # the door: a recessed sliding leaf in the opening (built closed - the layout's walk_exempt), a finger pull
    p.box("Kit_Seal", (fx - 0.06, -dw, 0.0), (fx - 0.04, dw, dh), panel=False)
    front_plate(p, "Kit_Primary", fx - 0.005, -dw + 0.006, dw - 0.006, 0.006, dh - 0.006, t=0.025, pressed=True, secondary=True)
    p.box("Kit_Seal", (fx - 0.012, dw - 0.07, 0.9), (fx - 0.003, dw - 0.035, 1.2), panel=False)
    p.box("Kit_Structure", (fx - 0.012, dw - 0.068, 0.93), (fx - 0.004, dw - 0.037, 0.95), panel=False)
    p.box("Kit_Rubber", (fx - 0.006, -dw, 0.0), (fx + 0.004, -dw + 0.006, dh), panel=False)     # the leaf's seal at the jamb
    # the occupancy screen beside the door, the extraction grille over it on the other side, a status bar on the head
    screen(p, fx, dw + 0.09, hw - 0.1, 1.36, 1.5, REGIONS["hygiene"])
    grille(p, fx, -hw + 0.08, -dw - 0.1, 1.55, 1.85)
    p.box("Kit_GlowCool", (fx + 0.02, -0.12, dh + 0.012), (fx + 0.023, 0.12, dh + 0.024), panel=False)
    label(p, "st_vent", (fx, (-hw - dw) / 2, 1.47), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.35, True)
    p.grime("soot", (fx + 0.004, 0.0, 0.01), (1, 0, 0), (0, 0, -1), (0.76, 0.08), 0.7)
    p.collision_box((0.0, -hw, 0.0), (D + 0.03, hw, H))
    return p


# =============================================================================== the galley unit
def food(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D = 0.45
    hw = L / 2
    z0, z1 = 0.8, 1.8
    # the unit's back and a plate behind the seat, on brackets back to the liner (a plate over the whole height left
    # a big plain field under the unit - the liner shows there instead)
    sy0, sy1 = -0.34, 0.08
    # the unit's back 0.1 m off the wall plate's plane: its top then clears the liner's frames on the chamfer
    xb = 0.1
    assert z1 <= top_at(xb)
    front_plate(p, "Kit_Primary", xb + 0.02, -hw, hw, z0, z1, pressed=True)
    front_plate(p, "Kit_Primary", 0.02, sy0 - 0.06, sy1 + 0.06, 0.15, z0, pressed=True)
    for (yy, zz) in ((-hw + 0.2, 1.6), (hw - 0.2, 1.6), (-hw + 0.2, 0.9), (hw - 0.2, 0.9)):
        p.box("Kit_Structure", (-WALL_GAP - 0.012, yy - 0.03, zz - 0.04), (xb, yy + 0.03, zz + 0.04), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (-WALL_GAP - 0.012, (sy0 + sy1) / 2 - 0.03, 0.26), (0.0, (sy0 + sy1) / 2 + 0.03, 0.34), bevel=0.003, segments=1, panel=False)
    # the carcass: sides in the structure metal, bottom and top
    xc = xb + 0.02
    for s in (1, -1):
        p.box("Kit_Structure", (xc, min(s * hw, s * (hw - 0.03)), z0), (D, max(s * hw, s * (hw - 0.03)), z1), bevel=0.004, segments=1, panel=False)
    iw = hw - 0.03
    p.box("Kit_Primary", (xc, -iw, z0), (D, iw, z0 + 0.03), bevel=0.003, segments=1)
    p.box("Kit_Primary", (xc, -iw, z1 - 0.03), (D, iw, z1), bevel=0.003, segments=1)
    # low: the chilled cabinet (left) and the ration drawer (right)
    zl0, zl1 = z0 + 0.03, 1.2
    p.box("Kit_Seal", (xc, -iw, zl0), (D - 0.02, iw, zl1), panel=False)
    front_plate(p, "Kit_Primary", D, -iw + 0.004, -0.006, zl0 + 0.004, zl1 - 0.004, pressed=True, secondary=True)
    front_plate(p, "Kit_Primary", D, 0.006, iw - 0.004, zl0 + 0.004, zl1 - 0.004, pressed=True, secondary=True)
    pull(p, D, -0.22, -0.1, zl1 - 0.06)
    pull(p, D, 0.28, 0.46, zl1 - 0.06)
    p.box("Kit_GlowCool", (D, -iw + 0.05, zl1 - 0.05), (D + 0.003, -iw + 0.09, zl1 - 0.04), panel=False)       # cooling
    # the counter
    p.box("Kit_Structure", (xc, -iw, zl1), (D + 0.02, iw, zl1 + 0.025), bevel=0.004, segments=1, panel=False)
    # the middle: a cream fascia with the water bay, the screen and its buttons beside it
    zm0, zm1 = zl1 + 0.025, 1.55
    bay = (0.12, 0.56, zm0 + 0.03, zm1 - 0.04)
    by0, by1, bz0, bz1 = bay
    for (a0, a1, b0, b1) in ((-iw, by0, zm0, zm1), (by1, iw, zm0, zm1), (by0, by1, zm0, bz0), (by0, by1, bz1, zm1)):
        front_plate(p, "Kit_Accent", D - 0.01, a0, a1, b0, b1, t=0.02, panel=False)
    # the bay: a dark recess 0.3 m deep (back, roof, floor, sides) behind the fascia
    bx0, bx1 = xc + 0.1, D - 0.03
    p.box("Kit_Seal", (bx0 - 0.02, by0 - 0.01, bz0), (bx0, by1 + 0.01, bz1), panel=False)
    p.box("Kit_Seal", (bx0, by0 - 0.01, bz1 - 0.01), (bx1, by1 + 0.01, bz1), panel=False)
    p.box("Kit_Seal", (bx0, by0 - 0.01, bz0), (bx1, by1 + 0.01, bz0 + 0.01), panel=False)
    for (a0, a1) in ((by0 - 0.01, by0), (by1, by1 + 0.01)):
        p.box("Kit_Seal", (bx0, a0, bz0), (bx1, a1, bz1), panel=False)
    ring(p, "Kit_Structure", D - 0.01, by0, by1, bz0, bz1, 0.015, 0.012, bevel=0.002)
    c = ((by0 + by1) / 2)
    p.box("Kit_Structure", (bx0 + 0.02, c - 0.05, bz1 - 0.06), (bx0 + 0.13, c + 0.05, bz1 - 0.01), bevel=0.004, segments=1, panel=False)  # the head
    p.tube("Kit_Structure", (bx0 + 0.075, c, bz1 - 0.06), (bx0 + 0.075, c, bz1 - 0.12), 0.01, 12)                                        # the nozzle
    for k in range(8):
        yy = by0 + 0.02 + k * (by1 - by0 - 0.04) / 7
        p.box("Kit_Structure", (bx0 + 0.01, yy - 0.004, bz0 + 0.01), (bx1 - 0.01, yy + 0.004, bz0 + 0.02), panel=False)       # the drip grille
    p.box("Kit_GlowNeutral", (bx1 - 0.05, by0 + 0.03, bz1 - 0.016), (bx1 - 0.02, by1 - 0.03, bz1 - 0.01), panel=False)
    p.socket("Light_Bay_0", (D - 0.1, c, bz1 - 0.04), x=(0, 0, -1), z=(1, 0, 0), type="point", role="neutral", cd=1.5,
             radius_m=0.8, source_radius_cm=3.0)
    screen(p, D - 0.01, -0.4, -0.23, zm0 + 0.1, zm0 + 0.27, REGIONS["galley"])
    for k, yy in enumerate((-0.385, -0.315, -0.245)):
        p.box("Kit_Plastic", (D - 0.01, yy - 0.025, zm0 + 0.035), (D + 0.004, yy + 0.025, zm0 + 0.07), bevel=0.003, segments=1, panel=False)
    p.box("Kit_GlowCool", (D + 0.004, -0.39, zm0 + 0.074), (D + 0.006, -0.38, zm0 + 0.08), panel=False)
    # high: two stowage doors with finger pulls
    zh0, zh1 = zm1, z1 - 0.03
    p.box("Kit_Seal", (xc, -iw, zh0), (D - 0.02, iw, zh1), panel=False)
    for (a0, a1) in ((-iw + 0.004, -0.006), (0.006, iw - 0.004)):
        front_plate(p, "Kit_Primary", D, a0, a1, zh0 + 0.004, zh1 - 0.004, pressed=True, secondary=True)
        p.box("Kit_Seal", (D - 0.004, (a0 + a1) / 2 - 0.08, zh0 + 0.012), (D + 0.001, (a0 + a1) / 2 + 0.08, zh0 + 0.026), panel=False)
    # the fold-down seat under it: a hinge rail on the wall plate, the pan and its cushion, two struts, a back cushion
    p.box("Kit_Structure", (0.02, sy0 - 0.02, 0.4), (0.06, sy1 + 0.02, 0.45), bevel=0.004, segments=1, panel=False)
    p.box("Kit_Structure", (0.06, sy0, 0.43), (0.42, sy1, 0.455), bevel=0.004, segments=1, panel=False)
    cushion(p, (0.07, sy0 + 0.01, 0.455), (0.41, sy1 - 0.01, 0.51), r=0.02)
    for yy in (sy0 + 0.03, sy1 - 0.03):
        p.tube("Kit_Structure", (0.38, yy, 0.43), (0.02, yy, 0.2), 0.009, 10)
        p.box("Kit_Structure", (0.02, yy - 0.02, 0.18), (0.04, yy + 0.02, 0.23), bevel=0.003, segments=1, panel=False)
    cushion(p, (0.013, sy0 + 0.02, 0.56), (0.075, sy1 - 0.02, 0.76), r=0.02)
    p.collision_box((0.0, -hw, z0), (D + 0.05, hw, z1))
    p.collision_box((0.02, sy0, 0.4), (0.42, sy1, 0.51))
    return p


# =============================================================================== the batch
REGIONS = {"hygiene": (0.125, 0.25, 0.375, 0.5), "galley": (0.75, 0.0, 1.0, 0.25)}     # kit_screens.py pages
FURNITURE = [("Furniture", "Bunk", 2.1, "L", "A"), ("Furniture", "Locker", 0.95, "L", "A"),
             ("Furniture", "Hygiene", 1.45, "L", "A"), ("Furniture", "Food", 1.6, "L", "A")]
VIEWS = {(c, pa): ((1.0, 0.05, 0.15), (1.0, -0.85, 0.45)) for c, pa, _, _, _ in FURNITURE}
BUILDERS = {"Bunk": bunk, "Locker": locker, "Hygiene": hygiene, "Food": food}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(size * 10 + 0.5), sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    return BUILDERS[part](var, size, part_name(cat, part, size, sec_key, var), seed)


def budget(cat, part, size):
    return int(kit_geo.RULES["tri_budget"]["Furniture"])
