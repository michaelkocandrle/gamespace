"""Step 2 drawing of a parts-factory part (Docs/Kit/FACTORY_WORKFLOW.md, pilot 1 KF-PORTAL-01, 6. 10. 2026).

    python Tools/Design/draw_part_sheet.py ArtSource/Kit/Design/KF-PORTAL-01.json

The simplest working version (workflow v0.1: tools in a pilot only as simple as works): one A3 sheet from the part's
JSON and the kit sections (ArtSource/Kit/kit_rules.json) - front view, section along the run, the profile detail 1:5,
the floor plan, the joint to the wall and floor, the view from the eye and the lights table. Writes
<json dir>/<id>.png and each view as <json dir>/<id>_<nn>_<view>.png for review crops. Only the corridor frame
module's geometry is drawn for now; the next part adds its own view functions.
"""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle, Circle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json")

C_WALL = "#3b3d42"     # wall panel face line
C_FRAME = "#e6dcc8"    # frame lacquer (fill)
C_FRAME_E = "#6b5f4a"
C_LIP = "#9aa3ad"      # polished lip
C_RUBBER = "#26272a"
C_COOL = "#3c8dde"
C_WARM = "#e0a040"
C_FLOOR = "#8d9096"
C_DIM = "#c0392b"
C_BOOT = "#e6dcc8"       # rev. D: the boot in the frame's lacquer
C_GLOW = "#dfe9ff"       # the cup's glow (~7500 K)


def section_profile(sec):
    """Right half of the wall panel face (y, z) from the floor to the ceiling centre (kit_rules sections)."""
    h = sec["width"] / 2
    top = sec["vertical_to"] + sec["slope_rise"]
    cw = sec["ceiling_width"] / 2
    return [(h, 0.0), (h, sec["vertical_to"]), (cw, top), (cw, sec["cove_to"]), (0.0, sec["ceiling"])]


def offset_inward(pts, d):
    """Offset an open polyline (right half, floor -> ceiling centre) by d into the room (toward -y / -z)."""
    lines = []
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        dy, dz = y1 - y0, z1 - z0
        n = math.hypot(dy, dz)
        # inward normal of a segment walked floor -> ceiling on the right side: rotate (dy, dz) by +90 deg
        ny, nz = -dz / n, dy / n
        lines.append(((y0 + ny * d, z0 + nz * d), (y1 + ny * d, z1 + nz * d)))
    out = [lines[0][0]]
    for (a0, a1), (b0, b1) in zip(lines, lines[1:]):
        out.append(intersect(a0, a1, b0, b1))
    out.append(lines[-1][1])
    out[0] = (out[0][0], 0.0)
    return out


def intersect(p0, p1, q0, q1):
    x1, y1 = p0
    x2, y2 = p1
    x3, y3 = q0
    x4, y4 = q1
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return p1
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def full(pts):
    """Both halves as one path: the left floor up to the ceiling centre and down to the right floor."""
    return [(-y, z) for y, z in pts] + list(reversed(pts))[1:]


def octagon(cx, cy, w, h, c):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c),
            (x0, y0 + c)]


def setup(ax, title, scale):
    ax.set_aspect("equal")
    ax.set_title("%s   %s" % (title, scale), fontsize=10, loc="left", fontweight="bold")
    ax.tick_params(labelsize=6)
    ax.grid(True, lw=0.2, alpha=0.4)


def dim(ax, a, b, text, off=(0, 0), fs=6):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<->", color=C_DIM, lw=0.6))
    ax.text((a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1], text, color=C_DIM, fontsize=fs, ha="center",
            va="center", bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.8))


def note(ax, xy, text, xytext, fs=6):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, arrowprops=dict(arrowstyle="-", lw=0.4, color="#444"),
                bbox=dict(fc="#fffbe8", ec="#bbb", lw=0.3, pad=1.2))


def boot_section(spec, sec_key="W"):
    """The boot's section (v from the wall face, z), mm."""
    v1, prot, zv, zt = boot_dims(spec, sec_key)
    return [(0, 0), (v1, 0), (v1, zv), (prot, zt), (0, zt)]


def boot_plan(spec, sec_key="W"):
    """The boot's plan (u along the run, v from the wall face), mm: octagonal on the corridor side."""
    b = spec["boot"]
    v1 = b["v1_by_section"][sec_key]
    c = b["chamfer"]
    return [(b["u0"], 0), (b["u1"], 0), (b["u1"], v1 - c), (b["u1"] - c, v1), (b["u0"] + c, v1), (b["u0"], v1 - c)]


def boot_dims(spec, sec_key="W"):
    b = spec["boot"]
    v1 = b["v1_by_section"][sec_key]
    prot = spec["profile"]["protrusion_by_section"][sec_key]
    return v1, prot, b["z_vert"], b["z_vert"] + (v1 - prot)


def _boot_elevation(ax, spec, x0, L):
    """The boot seen from the corridor (u, z): light lacquer, the bead along the top edge, the cup's glow."""
    b = spec["boot"]
    v1, prot, zv, zt = boot_dims(spec)
    c = b["chamfer"] / 1000
    ax.add_patch(Polygon([(x0, 0), (x0 + L, 0), (x0 + L, zv / 1000), (x0 + L - c, zt / 1000), (x0 + c, zt / 1000),
                          (x0, zv / 1000)], fc=C_BOOT, ec=C_FRAME_E, lw=0.5))
    for xx in (x0 + c, x0 + L - c):
        ax.plot([xx, xx], [0, zv / 1000], color="#b8ad97", lw=0.4)
    ax.plot([x0, x0 + L], [zv / 1000, zv / 1000], color=C_LIP, lw=1.6)
    cp = b["cup"]
    ax.add_patch(Polygon(octagon(x0 + cp["u"] / 1000, cp["z"] / 1000, cp["outer"] / 1000, cp["outer"] / 1000,
                                 cp["outer"] / 1000 * 0.29), fc=C_BOOT, ec=C_FRAME_E, lw=0.5))
    ax.add_patch(Polygon(octagon(x0 + cp["u"] / 1000, cp["z"] / 1000, cp["inner"] / 1000, cp["inner"] / 1000,
                                 cp["inner"] / 1000 * 0.29), fc=C_GLOW, ec="#9fb6e0", lw=0.5))


def view_front(ax, spec, secs):
    w = secs["W"]
    outer = section_profile(w)
    p = spec["profile"]["protrusion_by_section"]["W"] / 1000
    rings = [offset_inward(outer, d / 1000) for d in (0, 40, 70, 100)]
    poly = full(rings[0]) + list(reversed(full(rings[3])))
    ax.add_patch(Polygon(poly, closed=True, fc=C_FRAME, ec=C_FRAME_E, lw=0.6))
    for k in (1, 2):
        ax.plot(*zip(*full(rings[k])), color="#c9bea8", lw=0.5)
    inner = full(rings[3])
    ax.plot(*zip(*inner), color=C_LIP, lw=1.6, solid_capstyle="butt")
    ax.plot(*zip(*full(outer)), color=C_WALL, lw=1.0)
    n = secs["N"]
    ax.plot(*zip(*full(section_profile(n))), color="#777", lw=0.7, ls="--")
    ax.plot(*zip(*full(offset_inward(section_profile(n), spec["profile"]["protrusion_by_section"]["N"] / 1000))),
            color="#777", lw=0.5, ls=":")
    ax.text(0, 1.55, "N (čárkovaně)\n1,2 × 2,3 m", fontsize=6, ha="center", color="#555")
    ax.plot([-1.3, 1.3], [0, 0], color=C_FLOOR, lw=1.2)
    half = w["width"] / 2
    v1, prot, zv, zt = boot_dims(spec)
    cp = spec["boot"]["cup"]
    for s in (-1, 1):
        pts = [(s * (half - v / 1000), z / 1000) for v, z in boot_section(spec)]
        ax.add_patch(Polygon(pts, fc=C_BOOT, ec=C_FRAME_E, lw=0.6))
        ax.plot([s * (half - v1 / 1000), s * (half - v1 / 1000)], [(zv - 12) / 1000, zv / 1000], color=C_LIP, lw=2.0)
        # the cup's collar out of the face, its glowing back
        yb = s * (half - v1 / 1000)
        yc = yb - s * cp["depth"] / 1000
        ax.add_patch(Rectangle((min(yb, yc), (cp["z"] - cp["outer"] / 2) / 1000), abs(yc - yb), cp["outer"] / 1000,
                               fc=C_BOOT, ec=C_FRAME_E, lw=0.5))
        ax.plot([yb, yb], [(cp["z"] - cp["inner"] / 2) / 1000, (cp["z"] + cp["inner"] / 2) / 1000], color=C_GLOW, lw=3)
        ty = s * (w["ceiling_width"] / 2 - p)
        ax.add_patch(Circle((ty * 0.97, w["vertical_to"] + w["slope_rise"] - 0.02), 0.03, fc=C_WARM, ec="k", lw=0.4))
    cw = w["ceiling_width"] / 2 - 0.07
    ax.plot([-cw, cw], [w["ceiling"] - 0.055, w["ceiling"] - 0.055], color=C_WARM, lw=1.5, ls=(0, (3, 1)))
    note(ax, (half - v1 / 1000, 0.1), "L1 světlá bota s leštěnou hranou,\nzáře v osmibokém kalichu", (0.25, 0.62))
    note(ax, (0.5, 2.08), "L2 horní roh Ø60, 18 cd, kužel 100°", (0.75, 2.5))
    note(ax, (0.0, w["ceiling"] - 0.055), "L3 2× skrytá lišta v drážce u koruny (jen horní člen)", (-1.4, 2.62))
    note(ax, (-half + 0.05, 0.9), "rám = jeden plný tvar v laku,\nstupně 40 / 70 / 100 jen stínem", (-1.45, 1.2))
    note(ax, (-(half - p), 0.7), "leštěná linka jen na hraně koruny", (-0.95, 0.42))
    dim(ax, (-half + p, -0.12), (half - p, -0.12), "světlost u podlahy %.2f m (nad botami %.2f)" % (
        w["width"] - 2 * p, w["width"] - 2 * v1 / 1000))
    dim(ax, (-half, -0.25), (half, -0.25), "W %.1f m mezi líci stěn" % w["width"])
    dim(ax, (1.45, 0), (1.45, w["ceiling"] - p), "světlá výška %.2f" % (w["ceiling"] - p), off=(0.05, 0))
    ax.set_xlim(-1.6, 1.7)
    ax.set_ylim(-0.35, 2.75)


def view_section(ax, spec, secs):
    w = secs["W"]
    fl = spec["floor"]
    L = spec["portal_length"]
    pl = fl["plate_lengths"][0]
    xs = [0, L, L + pl, L + pl + fl["band_length"], L + 2 * pl + fl["band_length"]]
    end = xs[-1] + L
    ax.add_patch(Rectangle((-0.1, -0.2), end + 0.2, 0.15, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    ax.add_patch(Rectangle((-0.1, w["ceiling"]), end + 0.2, 0.25, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    segs = [(0, L, "práh"), (xs[1], xs[2], "deska 0,9"), (xs[2], xs[3], "pás 0,3"), (xs[3], xs[4], "deska 0,9"),
            (xs[4], end, "práh")]
    for a, b, t in segs:
        ax.add_patch(Rectangle((a + 0.009, -0.05), b - a - 0.018, 0.044, fc="#b9bcc2", ec="k", lw=0.4))
        ax.text((a + b) / 2, -0.12, t, fontsize=6, ha="center")
    for x in sorted({v for a, b, _ in segs for v in (a, b)}):
        ax.add_patch(Rectangle((x - 0.009, -0.006), 0.018, 0.006, fc=C_LIP, ec="none"))
    for z, t in ((0.1, "sokl"), (w["vertical_to"], "zlom 1,3"), (w["vertical_to"] + w["slope_rise"], "vybrání 2,1")):
        ax.plot([-0.1, end + 0.1], [z, z], color="#888", lw=0.5, ls="--")
        ax.text(end + 0.12, z, t, fontsize=6, va="center")
    st = spec["profile"]["steps"]
    for x0 in (0, xs[4]):
        ax.add_patch(Rectangle((x0 + 0.008, 0), L - 0.016, w["ceiling"], fc=C_FRAME, ec=C_FRAME_E, lw=0.5, alpha=0.55))
        ax.add_patch(Polygon([(x0 + st[0]["u0"] / 1000, w["ceiling"]), (x0 + st[0]["u1"] / 1000, w["ceiling"]),
                              (x0 + st[0]["u1"] / 1000, w["ceiling"] - st[0]["v1"] / 1000),
                              (x0 + st[1]["u1"] / 1000, w["ceiling"] - st[0]["v1"] / 1000),
                              (x0 + st[1]["u1"] / 1000, w["ceiling"] - st[1]["v1"] / 1000),
                              (x0 + st[2]["u1"] / 1000, w["ceiling"] - st[1]["v1"] / 1000),
                              (x0 + st[2]["u1"] / 1000, w["ceiling"] - st[2]["v1"] / 1000),
                              (x0 + st[2]["u0"] / 1000, w["ceiling"] - st[2]["v1"] / 1000),
                              (x0 + st[2]["u0"] / 1000, w["ceiling"] - st[1]["v1"] / 1000),
                              (x0 + st[1]["u0"] / 1000, w["ceiling"] - st[1]["v1"] / 1000),
                              (x0 + st[1]["u0"] / 1000, w["ceiling"] - st[0]["v1"] / 1000),
                              (x0 + st[0]["u0"] / 1000, w["ceiling"] - st[0]["v1"] / 1000)], fc=C_FRAME, ec="k", lw=0.6))
        _boot_elevation(ax, spec, x0, L)
        ax.add_patch(Circle((x0 + L / 2, 2.08), 0.03, fc=C_WARM, ec="k", lw=0.4))
    dim(ax, (0, 2.62), (xs[1], 2.62), "0,3")
    dim(ax, (0, 2.75), (xs[4], 2.75), "rozteč 2,4 = 0,3 + 0,9 + 0,3 + 0,9")
    dim(ax, (0, -0.32), (xs[1] + pl, -0.32), "rozteč 1,2 = 0,3 + 0,9 (výchozí, autor 6. 10.)")
    note(ax, (xs[4] + 0.15, 2.22), "řez horním členem: jeden plný tvar", (xs[4] - 1.0, 1.75))
    note(ax, (xs[4] + 0.15, 0.095), "světlá bota, záře v kalichu", (xs[4] - 1.0, 0.55))
    note(ax, (xs[3] + 0.0, -0.003), "síť leštěného lemu", (xs[2] - 0.2, 0.3))
    ax.set_xlim(-0.2, end + 0.55)
    ax.set_ylim(-0.42, 2.85)


def hidden_strip_visibility(spec, grooves=True):
    """Where the top member's hidden strip is seen from the eye, both directions down the corridor (2D in the run's
    vertical plane: u along the run in metres, z up). Returns [(side, farthest distance seen or None, elevation deg)]."""
    pr = spec["profile"]
    top = 2.3                                    # the ceiling (W and N): the top member hangs from it
    z = lambda v: top - v / 1000                 # noqa: E731
    base, mid, crown = pr["steps"]
    boxes = [(base["u0"] / 1000, base["u1"] / 1000, z(base["v1"]), z(base["v0"])),
             (crown["u0"] / 1000, crown["u1"] / 1000, z(crown["v1"]), z(crown["v0"]))]
    hs = pr["hidden_strip"]
    if grooves:
        cuts = sorted(tuple(g) for g in hs["grooves"])
        ledge = z(mid["v1"])
        u = mid["u0"]
        for a, b in cuts:
            boxes.append((u / 1000, a / 1000, ledge, z(mid["v0"])))
            boxes.append((a / 1000, b / 1000, ledge + hs["groove_depth"] / 1000, z(mid["v0"])))
            u = b
        boxes.append((u / 1000, mid["u1"] / 1000, ledge, z(mid["v0"])))
        strips = [((a + 1) / 1000, (b - 1) / 1000, ledge + hs["groove_depth"] / 1000 - 1e-4) for a, b in cuts]
    else:
        boxes.append((mid["u0"] / 1000, mid["u1"] / 1000, z(mid["v1"]), z(mid["v0"])))
        strips = [(0.046, 0.058, z(mid["v1"]) - 1e-4)]
    eye = spec["eye"]["height"]

    def blocked(p, q):
        for (u0, u1, z0, z1) in boxes:
            t0, t1 = 0.0, 1.0
            ok = True
            for a, d, lo, hi in ((p[0], q[0] - p[0], u0, u1), (p[1], q[1] - p[1], z0, z1)):
                if abs(d) < 1e-12:
                    if a <= lo or a >= hi:
                        ok = False
                        break
                    continue
                ta, tb = sorted(((lo - a) / d, (hi - a) / d))
                t0, t1 = max(t0, ta), min(t1, tb)
                if t0 >= t1:
                    ok = False
                    break
            if ok and t1 - t0 > 1e-6:
                return True
        return False

    out = []
    for side, sign in (("blízká strana (u < 0)", -1), ("vzdálená strana (u > 0,3)", 1)):
        far = None
        for k in range(1, 400):
            dist = k * 0.025
            e = (-dist if sign < 0 else 0.3 + dist, eye)
            seen = any(not blocked(e, (s0 + (s1 - s0) * f, sz)) for s0, s1, sz in strips for f in (0.0, 0.5, 1.0))
            if seen:
                far = dist
        elev = math.degrees(math.atan2(strips[0][2] - eye, far)) if far else None
        out.append((side, far, elev))
    return out


def view_profile(ax, spec):
    pr = spec["profile"]
    ax.add_patch(Rectangle((-80, -40), 460, 40, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    ax.add_patch(Rectangle((-80, 0), 80 - pr["gap"] / 2, 25, fc="#55585e", ec="k", lw=0.5))
    ax.add_patch(Rectangle((300 + pr["gap"] / 2, 0), 80, 25, fc="#55585e", ec="k", lw=0.5))
    ax.text(-40, 30, "stěna", fontsize=6, ha="center")
    ax.text(340, 30, "stěna", fontsize=6, ha="center")
    hs = pr["hidden_strip"]
    base, mid, crown = pr["steps"]
    e = pr["lip"]["edge"]
    # rev. C: one solid outline in one lacquer (no seams between the steps)
    outline = [(base["u0"], 0), (base["u1"], 0), (base["u1"], base["v1"]), (mid["u1"], base["v1"]), (mid["u1"], mid["v1"]),
               (crown["u1"], mid["v1"]), (crown["u1"], crown["v1"] - e), (crown["u1"] - e, crown["v1"]),
               (crown["u0"] + e, crown["v1"]), (crown["u0"], crown["v1"] - e), (crown["u0"], mid["v1"]),
               (mid["u0"], mid["v1"]), (mid["u0"], base["v1"]), (base["u0"], base["v1"])]
    ax.add_patch(Polygon(outline, fc=C_FRAME, ec="k", lw=0.7))
    for k, st in enumerate(pr["steps"]):
        if k == 0:          # the base: the wall panel sits beside it
            ax.text((st["u0"] + st["u1"]) / 2, 8, "%s %d–%d" % (st["name"], st["v0"], st["v1"]), fontsize=6, ha="center")
        else:
            ax.text(st["u1"] + 6, (st["v0"] + st["v1"]) / 2, "%s %d–%d" % (st["name"], st["v0"], st["v1"]), fontsize=6,
                    va="center")
    for a, b in hs["grooves"]:
        ax.add_patch(Rectangle((a, mid["v1"] - hs["groove_depth"]), b - a, hs["groove_depth"], fc="white", ec="k", lw=0.4))
        ax.add_patch(Rectangle((a + 1, mid["v1"] - hs["groove_depth"]), b - a - 2, 3, fc=C_WARM, ec="k", lw=0.3))
    for (x, sgn) in ((crown["u0"], 1), (crown["u1"], -1)):
        # the polished bead on the crown's edge: 12 x 12 mm, rounded
        ax.add_patch(Polygon([(x, crown["v1"] - e), (x + sgn * e * 0.3, crown["v1"] - e * 0.3), (x + sgn * e, crown["v1"]),
                              (x + sgn * e, crown["v1"] - e)], fc=C_LIP, ec="k", lw=0.4))
    cf = pr["cuff"]
    ax.add_patch(Rectangle((cf["u0"], crown["v1"] - cf["depth"]), cf["u1"] - cf["u0"], cf["depth"], fc=C_RUBBER, ec="k",
                           lw=0.4))
    u = cf["u0"] + 4
    while u + cf["rib_width"] <= cf["u1"]:
        ax.add_patch(Rectangle((u, crown["v1"] - cf["depth"]), cf["rib_width"], cf["depth"] + 2, fc="#3a3b3f", ec="none"))
        u += cf["rib_pitch"]
    note(ax, (hs["grooves"][0][0] + 7, mid["v1"] - 18), "L3 2× lišta 12 v drážce 14 × 20 u boku koruny", (-85, 74))
    note(ax, (crown["u0"] + 4, crown["v1"] - 4), "leštěná hrana koruny 12 × 12 (jedna linka)", (-85, 128))
    note(ax, ((cf["u0"] + cf["u1"]) / 2, crown["v1"] - 3), "pryžová manžeta %d na vnitřní straně, žebra %d / %d" % (cf["u1"] - cf["u0"], cf["rib_width"], cf["rib_pitch"]), (150, 140))
    ax.text(150, 30, "jeden plný tvar, jeden lak –\nstupně čitelné jen stínem a odleskem", fontsize=6, ha="center")
    dim(ax, (0, -55), (300, -55), "modul 300 (spára 2 × 4)")
    dim(ax, (390, 0), (390, 100), "100 (W)\n80 (N)", off=(18, 0))
    half_v = math.degrees(math.atan(math.tan(math.radians(spec["eye"]["fov"] / 2)) * 9 / 16))
    rows = []
    for side, far, elev in hidden_strip_visibility(spec, True):
        rows.append("L3, %s: %s" % (side, "neviditelná do 10 m" if far is None else
                                    ("vidět jen do %.2f m od člena (elevace ≥ %.0f°)" % (far, elev)).replace(".", ",")))
    rows.append("svislé ½ FOV při 90° (16:9) = %.0f°: při pohledu vodorovně je zdroj mimo obraz" % half_v)
    ax.text(-85, -68, "\n".join(rows), fontsize=5.5, va="top", family="monospace")
    ax.text(150, 162, "u podél chodby →   v od líce stěny do chodby ↑   (mm)", fontsize=6, ha="center", color="#555")
    ax.set_xlim(-90, 440)
    ax.set_ylim(-110, 172)


def view_floor(ax, spec, secs):
    """Plan of two 1.2 m pitches in W: threshold + walkway plate A, threshold + grille plate G, the boots at the
    pillars (rev. D: light, the cup on the corridor face) and the continuous network of the polished lip."""
    w = secs["W"]
    fl = spec["floor"]
    L = spec["portal_length"]
    half = w["width"] / 2
    walk = fl["walk_width"] / 2
    edge = half - fl["edge_strip"]
    ln = fl["plate_lengths"][0]
    c = fl["corner_chamfer"]

    def lipped(poly, fc):
        ax.add_patch(Polygon(poly, fc=fc, ec=C_LIP, lw=2.2, joinstyle="miter"))

    v1 = spec["boot"]["v1_by_section"]["W"]
    cp = spec["boot"]["cup"]
    x = 0.0
    for kind in ("t", "a", "t", "g", "t"):
        size = L if kind == "t" else ln
        if kind == "t":
            lipped([(x, -edge), (x + size, -edge), (x + size, edge), (x, edge)], "#5d6066")
            for s in (-1, 1):
                pts = [(x + u / 1000, s * (half - v / 1000)) for u, v in boot_plan(spec)]
                ax.add_patch(Polygon(pts, fc=C_BOOT, ec=C_LIP, lw=1.2))
                yb = s * (half - v1 / 1000)
                yc = yb - s * cp["depth"] / 1000
                ax.add_patch(Rectangle((x + (cp["u"] - cp["outer"] / 2) / 1000, min(yb, yc)), cp["outer"] / 1000,
                                       abs(yc - yb), fc=C_BOOT, ec=C_FRAME_E, lw=0.5))
                ax.add_patch(Circle((x + cp["u"] / 1000, yc - s * 0.03), 0.035, fc=C_GLOW, ec="none", alpha=0.6))
        else:
            o = octagon(x + size / 2, 0, size, 2 * walk, c)
            if kind == "a":
                lipped(o, "#5f636a")
                y = -walk + 0.06
                while y + fl["lanes"]["width"] <= walk - 0.06:
                    ax.add_patch(Rectangle((x + 0.07, y), size - 0.14, fl["lanes"]["width"], fc="#696d74", ec="none"))
                    y += fl["lanes"]["pitch"]
            else:
                lipped(o, "#4a4d52")
                cw = fl["grille"]["channel_width"] / 2
                ax.add_patch(Rectangle((x + 0.04, -cw), size - 0.08, 2 * cw, fc="#202124", ec="none"))
                yb = -cw
                while yb <= cw:
                    ax.plot([x + 0.06, x + size - 0.06], [yb, yb], color="#8a8e95", lw=0.5)
                    yb += fl["grille"]["bar_pitch"]
            for s in (-1, 1):
                lipped([(x, s * walk), (x + c, s * walk), (x, s * (walk - c))], "#5d6066")
                lipped([(x + size, s * walk), (x + size - c, s * walk), (x + size, s * (walk - c))], "#5d6066")
                lipped([(x, s * walk), (x + size, s * walk), (x + size, s * edge), (x, s * edge)], "#666a71")
        x += size
    for s in (-1, 1):
        ya, yb = sorted((s * edge, s * half))
        ax.add_patch(Rectangle((0, ya), x, yb - ya, fc=C_FRAME, ec="k", lw=0.3))
    note(ax, (L + 0.45, 0.35), "A: chodník – protiskluzové pásy ve vložce −6 mm", (L - 0.2, 1.62))
    note(ax, (L + 0.45, walk + 0.005), "souvislá síť leštěného lemu 18 mm přes všechny desky", (-0.25, 1.92))
    note(ax, (L + 0.15, -0.5), "boční deska a rohové trojúhelníky – také v síti", (-0.2, -1.6))
    note(ax, (2 * L + ln + 0.45, 0.0), "G: mřížka nad kanálem 0,6 × hl. 0,2", (1.3, -1.92))
    note(ax, (0.15, half - 0.17), "světlá bota L1, kalich ke chodbě, jemná záře", (0.45, 1.4))
    dim(ax, (-0.08, -half), (-0.08, half), "W 2,4", off=(-0.08, 0))
    ax.text(x / 2, -2.1, "rozteč 1,2 m (výchozí): práh 0,3 + deska 0,9; N: bota 120 mm, chodník přes celou šířku", fontsize=6,
            ha="center", color="#555")
    ax.set_xlim(-0.3, x + 0.1)
    ax.set_ylim(-2.2, 2.05)


def view_joint(ax, spec):
    """The boot (L1) rev. D 1:5: its section across the corridor through the cup, mm."""
    b = spec["boot"]
    cp = b["cup"]
    v1, prot, zv, zt = boot_dims(spec)
    ax.add_patch(Rectangle((-60, -60), 340, 60, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    ax.add_patch(Rectangle((-60, 0), 60, 330, fc="#55585e", ec="k", lw=0.4))
    ax.add_patch(Polygon(boot_section(spec), fc=C_BOOT, ec=C_FRAME_E, lw=0.7))
    ax.add_patch(Rectangle((0, zt), prot, 100, fc=C_FRAME, ec="k", lw=0.5))
    ax.text(prot / 2, zt + 50, "pilíř\n(jeden tvar)", fontsize=5.5, ha="center", va="center")
    ax.add_patch(Rectangle((v1 - 12, zv - 12), 14, 14, fc=C_LIP, ec="k", lw=0.4))
    # the cup: a collar 30 mm out of the face, its glowing back, the weak light inside
    z0, z1 = cp["z"] - cp["outer"] / 2, cp["z"] + cp["outer"] / 2
    zi0, zi1 = cp["z"] - cp["inner"] / 2, cp["z"] + cp["inner"] / 2
    ax.add_patch(Rectangle((v1, z0), cp["depth"], (cp["outer"] - cp["inner"]) / 2, fc=C_BOOT, ec=C_FRAME_E, lw=0.5))
    ax.add_patch(Rectangle((v1, zi1), cp["depth"], (cp["outer"] - cp["inner"]) / 2, fc=C_BOOT, ec=C_FRAME_E, lw=0.5))
    ax.add_patch(Rectangle((v1 - 2, zi0), 3, cp["inner"], fc=C_GLOW, ec="#9fb6e0", lw=0.5))
    ax.add_patch(Circle((v1 + cp["depth"] * 0.4, cp["z"]), 4, fc="white", ec="#9fb6e0", lw=0.6))
    for r, a in ((60, 0.35), (120, 0.18), (190, 0.08)):
        ax.add_patch(Circle((v1 + cp["depth"] * 0.4, cp["z"]), r, fc="none", ec="#9fb6e0", lw=0.5, alpha=a * 2, ls="--"))
    ax.add_patch(Rectangle((v1, -6), 18, 6, fc=C_LIP, ec="none"))
    ax.add_patch(Rectangle((v1 + 18, -6), 140, 6, fc="#5f636a", ec="k", lw=0.3))
    note(ax, (v1 - 5, zv - 5), "leštěná hrana boty 12 mm", (v1 + 40, zv + 70))
    note(ax, (v1 + 15, cp["z"]), "osmiboký kalich 110 / 90, hl. 30;\nsvítící dno + slabé světlo ~0,5 m", (v1 + 45, cp["z"] + 120))
    note(ax, (v1 + 60, 2), "jen jemný rozptyl na podlahu,\nžádný reflektor", (v1 + 45, -45))
    dim(ax, (0, -30), (v1, -30), "%d (N %d)" % (v1, b["v1_by_section"]["N"]))
    dim(ax, (-35, 0), (-35, zt), "%d" % zt, off=(-14, 0))
    ax.text(130, 345, "bota L1 rev. D – řez kalichem (mm)", fontsize=6, ha="center", color="#555")
    ax.set_xlim(-100, 420)
    ax.set_ylim(-70, 360)


def view_eye(ax, spec, secs, pitch):
    """Pinhole view from the eye down a W corridor: portals on the given pitch, floor plates, lights."""
    w = secs["W"]
    eye = spec["eye"]["height"]
    f = 1.0 / math.tan(math.radians(spec["eye"]["fov"] / 2))
    outer = full(section_profile(w))
    p = spec["profile"]["protrusion_by_section"]["W"] / 1000
    inner = full(offset_inward(section_profile(w), p))
    L = spec["portal_length"]
    fl = spec["floor"]

    def proj(x, y, z):
        return (-y * f / x, (z - eye) * f / x)

    starts = []
    x0 = 1.2
    while x0 < 9.0:
        starts.append(x0)
        x0 += pitch
    for x0 in reversed(starts):
        # floor: walkway plates (and the band on the long pitch) between this portal and the next
        xs = [x0 + L]
        if pitch > 2.0:
            xs.append(x0 + L + fl["plate_lengths"][0] + fl["band_length"])
        for xa in xs:
            if xa + fl["plate_lengths"][0] > 9.0:
                continue
            o = octagon(xa + fl["plate_lengths"][0] / 2, 0, fl["plate_lengths"][0], fl["walk_width"], fl["corner_chamfer"])
            ax.add_patch(Polygon([proj(x, y, 0.0) for x, y in o], fc="#6f737a", ec=C_LIP, lw=0.6))
        for x in (x0 + L, x0):
            ax.add_patch(Polygon([proj(x, y, z) for y, z in outer + list(reversed(inner))], closed=True, fc=C_FRAME,
                                 ec=C_FRAME_E, lw=0.4))
            ax.plot(*zip(*[proj(x, y, z) for y, z in inner]), color=C_LIP, lw=1.0)
        for s in (-1, 1):
            ax.add_patch(Circle(proj(x0 + 0.15, s * (w["width"] / 2 - p - 0.05), 0.1), 0.012, fc=C_COOL))
            ax.add_patch(Circle(proj(x0 + 0.15, s * (w["ceiling_width"] / 2 - p), 2.08), 0.012, fc=C_WARM))
    for (y0, z0) in outer:
        a, b = proj(0.6, y0, z0), proj(9.0, y0, z0)
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#888", lw=0.4)
    ax.text(0, -1.0, "rozteč %.1f m; oko 1,65 m v ose, FOV %d° (jako SC)" % (pitch, spec["eye"]["fov"]),
            fontsize=6, ha="center", color="#555")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.08, 0.75)
    ax.set_xticks([])
    ax.set_yticks([])


def view_table(ax, spec):
    ax.axis("off")
    import textwrap
    widths = [0.04, 0.13, 0.26, 0.23, 0.16, 0.16]
    rows = [["ID", "Svítidlo", "Pouzdro", "Kde", "Barva", "Dosah"]]
    for l in spec["lights"]:
        rows.append([l["id"], l["name"] + " (" + l["count"] + ")", l["housing"], l["where"], l["colour"], l["reach"]])
    rows = [["\n".join(textwrap.wrap(c, max(4, int(w * 130)))) for c, w in zip(r, widths)] for r in rows]
    t = ax.table(cellText=rows, loc="upper left", cellLoc="left", colWidths=widths)
    t.auto_set_font_size(False)
    t.set_fontsize(5.5)
    for (r, _), cell in t.get_celld().items():
        cell.set_height(0.08 if r == 0 else 0.15)
    mats = ("Materiály (styl výrobce v part.md): celý rám krémový lak (Halcyon, autor 6. 10.); leštěný lem = leštěný "
            "kov; manžeta a sokl = guma; chodník = protiskluzový grafit; desky a pás = grafit. Všechna světla "
            "v pouzdře nebo skrytá, bez stínů.")
    # the last two revisions (the rest stays in the JSON): the full list ran into the title line at rev. D
    revs = "  ".join("%s %s: %s" % (r["rev"], r["date"], r["what"]) for r in spec.get("revisions", [])[-2:])
    ax.text(0.0, 0.28, "\n".join(textwrap.wrap("Revize: " + revs, 150)), fontsize=5.5, va="top", color="#444")
    ax.text(0.0, 0.43, "\n".join(textwrap.wrap(mats, 150)), fontsize=6, va="top")
    ax.text(0.0, 0.02, "%s  rev. %s  |  %s  |  %s  |  sekce %s; S a T jen poznámka" % (
        spec["id"], spec["revision"], spec["status"], spec["date"], ", ".join(spec["sections"])), fontsize=7,
        fontweight="bold")


def main():
    src = sys.argv[1]
    spec = json.load(open(src, encoding="utf-8"))
    secs = json.load(open(RULES, encoding="utf-8"))["sections"]
    fig = plt.figure(figsize=(16.54, 11.69), dpi=200)
    fig.suptitle("%s – %s" % (spec["id"], spec["title"]), fontsize=13, fontweight="bold", x=0.01, ha="left")
    views = [
        ("pohled", fig.add_axes([0.03, 0.50, 0.30, 0.44]), lambda ax: (setup(ax, "1 Pohled (W, N čárkovaně)", "1:20"),
                                                                          view_front(ax, spec, secs))),
        ("rez", fig.add_axes([0.36, 0.50, 0.30, 0.44]), lambda ax: (setup(ax, "2 Řez podél chodby (W)", "1:20"),
                                                                       view_section(ax, spec, secs))),
        ("profil", fig.add_axes([0.69, 0.55, 0.30, 0.39]), lambda ax: (setup(ax, "3 Detail profilu člena", "1:5"),
                                                                          view_profile(ax, spec))),
        ("podlaha", fig.add_axes([0.03, 0.05, 0.30, 0.40]), lambda ax: (setup(ax, "4 Podlaha – půdorys 2 × 1,2 (W)",
                                                                              "1:20"), view_floor(ax, spec, secs))),
        ("napojeni", fig.add_axes([0.36, 0.05, 0.22, 0.40]), lambda ax: (setup(ax, "5 Patka L1 – bota rev. D, řez",
                                                                               "1:5"), view_joint(ax, spec))),
        ("oko_12", fig.add_axes([0.61, 0.23, 0.19, 0.29]), lambda ax: (setup(ax, "6a Pohled z oka – rozteč 1,2", ""),
                                                                           view_eye(ax, spec, secs, 1.2))),
        ("oko_24", fig.add_axes([0.80, 0.23, 0.19, 0.29]), lambda ax: (setup(ax, "6b Pohled z oka – rozteč 2,4", ""),
                                                                           view_eye(ax, spec, secs, 2.4))),
        ("svetla", fig.add_axes([0.61, 0.02, 0.38, 0.18]), lambda ax: view_table(ax, spec)),
    ]
    for _, ax, fn in views:
        fn(ax)
    out_dir = os.path.dirname(os.path.abspath(src))
    out = os.path.join(out_dir, spec["id"] + ".png")
    fig.savefig(out)
    fig.canvas.draw()
    for k, (name, ax, _) in enumerate(views, 1):
        bb = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02, 1.02)
        fig.savefig(os.path.join(out_dir, "%s_%02d_%s.png" % (spec["id"], k, name)), bbox_inches=bb)
    print("SHEET " + out)


if __name__ == "__main__":
    main()
