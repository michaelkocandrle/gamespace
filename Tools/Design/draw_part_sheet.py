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


def view_front(ax, spec, secs):
    w = secs["W"]
    outer = section_profile(w)
    p = spec["profile"]["protrusion_by_section"]["W"] / 1000
    rings = [offset_inward(outer, d / 1000) for d in (0, 40, 70, 100)]
    shades = ["#d9cfbb", "#e3d9c6", "#efe7d6"]
    for k in range(3):
        poly = full(rings[k]) + list(reversed(full(rings[k + 1])))
        ax.add_patch(Polygon(poly, closed=True, fc=shades[k], ec=C_FRAME_E, lw=0.5))
    inner = full(rings[3])
    ax.plot(*zip(*inner), color=C_LIP, lw=2.2, solid_capstyle="butt")
    ax.plot(*zip(*full(outer)), color=C_WALL, lw=1.0)
    n = secs["N"]
    ax.plot(*zip(*full(section_profile(n))), color="#777", lw=0.7, ls="--")
    ax.plot(*zip(*full(offset_inward(section_profile(n), spec["profile"]["protrusion_by_section"]["N"] / 1000))),
            color="#777", lw=0.5, ls=":")
    ax.text(0, 1.55, "N (čárkovaně)\n1,2 × 2,3 m", fontsize=6, ha="center", color="#555")
    ax.plot([-1.3, 1.3], [0, 0], color=C_FLOOR, lw=1.2)
    # foot light housings (L1) and top corner lights (L2), the hidden strip (L3)
    half = w["width"] / 2
    for s in (-1, 1):
        cy = s * (half - p + 0.03 - 0.075)
        ax.add_patch(Polygon(octagon(cy, 0.095, 0.15, 0.15, 0.04), fc="#2b2d31", ec="k", lw=0.5))
        ax.add_patch(Rectangle((cy - 0.045, 0.07), 0.09, 0.05, fc=C_COOL, ec="none"))
        ty = s * (w["ceiling_width"] / 2 - p)
        ax.add_patch(Circle((ty * 0.97, w["vertical_to"] + w["slope_rise"] - 0.02), 0.03, fc=C_WARM, ec="k", lw=0.4))
    cw = w["ceiling_width"] / 2 - 0.07
    ax.plot([-cw, cw], [w["ceiling"] - 0.055, w["ceiling"] - 0.055], color=C_WARM, lw=1.5, ls=(0, (3, 1)))
    note(ax, (half - p + 0.03 - 0.075, 0.17), "L1 patka, studená, osmiboké pouzdro 150", (0.5, 0.55))
    note(ax, (0.5, 2.08), "L2 horní roh Ø60, 4000 K", (0.9, 2.5))
    note(ax, (0.0, w["ceiling"] - 0.055), "L3 skrytá lišta ve stínu stupně 2 (jen horní člen)", (-1.4, 2.62))
    note(ax, (-half + 0.05, 0.9), "základna / stupeň 2 / koruna\n40 / 70 / 100 mm od líce stěny", (-1.45, 1.2))
    note(ax, (-(half - p), 0.6), "leštěný lem 18 mm", (-0.9, 0.35))
    dim(ax, (-half + p, -0.12), (half - p, -0.12), "světlost u podlahy %.2f m" % (w["width"] - 2 * p))
    dim(ax, (-half, -0.25), (half, -0.25), "W %.1f m mezi líci stěn" % w["width"])
    dim(ax, (1.45, 0), (1.45, w["ceiling"] - p), "světlá výška %.2f" % (w["ceiling"] - p), off=(0.05, 0))
    ax.set_xlim(-1.6, 1.7)
    ax.set_ylim(-0.35, 2.75)


def view_section(ax, spec, secs):
    w = secs["W"]
    fl = spec["floor"]
    L = spec["portal_length"]
    xs = [0, L, L + fl["plate_length"], L + fl["plate_length"] + fl["band_length"],
          L + 2 * fl["plate_length"] + fl["band_length"]]
    end = xs[-1] + L
    ax.add_patch(Rectangle((-0.1, -0.2), end + 0.2, 0.15, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    ax.add_patch(Rectangle((-0.1, w["ceiling"]), end + 0.2, 0.25, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    # floor: thresholds, plates, band (top at 0, plates' insert 6 mm lower)
    segs = [(0, L, "práh"), (xs[1], xs[2], "deska 0,9"), (xs[2], xs[3], "pás 0,3"), (xs[3], xs[4], "deska 0,9"),
            (xs[4], end, "práh")]
    for a, b, t in segs:
        ax.add_patch(Rectangle((a + 0.005, -0.05), b - a - 0.01, 0.05, fc="#b9bcc2", ec="k", lw=0.4))
        ax.text((a + b) / 2, -0.12, t, fontsize=6, ha="center")
    # wall beyond (elevation): the slope and cove lines
    for z, t in ((0.1, "sokl"), (w["vertical_to"], "zlom 1,3"), (w["vertical_to"] + w["slope_rise"], "vybrání 2,1")):
        ax.plot([-0.1, end + 0.1], [z, z], color="#888", lw=0.5, ls="--")
        ax.text(end + 0.12, z, t, fontsize=6, va="center")
    for x0 in (0, xs[4]):
        # pillar beyond in elevation, the cut top member (steps hanging from the ceiling)
        ax.add_patch(Rectangle((x0 + 0.008, 0), L - 0.016, w["ceiling"], fc=C_FRAME, ec=C_FRAME_E, lw=0.5, alpha=0.55))
        for st in spec["profile"]["steps"]:
            ax.add_patch(Rectangle((x0 + st["u0"] / 1000, w["ceiling"] - st["v1"] / 1000), (st["u1"] - st["u0"]) / 1000,
                                   (st["v1"] - st["v0"]) / 1000, fc=C_FRAME, ec="k", lw=0.5))
        ax.add_patch(Polygon(octagon(x0 + L / 2, 0.095, 0.15, 0.15, 0.04), fc="#2b2d31", ec="k", lw=0.4))
        ax.add_patch(Rectangle((x0 + L / 2 - 0.045, 0.07), 0.09, 0.05, fc=C_COOL))
        ax.add_patch(Circle((x0 + L / 2, 2.08), 0.03, fc=C_WARM, ec="k", lw=0.4))
    dim(ax, (0, 2.62), (xs[1], 2.62), "0,3")
    dim(ax, (0, 2.75), (xs[4], 2.75), "rozteč 2,4 = 0,3 + 0,9 + 0,3 + 0,9")
    dim(ax, (0, -0.32), (xs[1] + fl["plate_length"], -0.32), "rozteč 1,2 = 0,3 + 0,9")
    note(ax, (xs[4] + 0.15, 2.22), "řez horním členem: 3 stupně", (xs[4] - 0.9, 1.75))
    ax.set_xlim(-0.2, end + 0.55)
    ax.set_ylim(-0.42, 2.85)


def view_profile(ax, spec):
    pr = spec["profile"]
    # wall panels either side of the base (half gap each), the structure behind
    ax.add_patch(Rectangle((-80, -40), 460, 40, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    ax.add_patch(Rectangle((-80, 0), 80 - pr["gap"] / 2, 25, fc="#55585e", ec="k", lw=0.5))
    ax.add_patch(Rectangle((300 + pr["gap"] / 2, 0), 80, 25, fc="#55585e", ec="k", lw=0.5))
    ax.text(-40, 30, "stěna", fontsize=6, ha="center")
    ax.text(340, 30, "stěna", fontsize=6, ha="center")
    for st in pr["steps"]:
        c = st.get("chamfer", 0)
        u0, u1, v0, v1 = st["u0"], st["u1"], st["v0"], st["v1"]
        pts = [(u0, v0), (u1, v0), (u1, v1 - c), (u1 - c, v1), (u0 + c, v1), (u0, v1 - c)]
        ax.add_patch(Polygon(pts, fc=C_FRAME, ec="k", lw=0.6))
        label = "%s  %d–%d" % (st["name"], v0, v1)
        if u1 + 70 > 300:  # the base: the label inside, the wall panel sits beside it
            ax.text((u0 + u1) / 2, (v0 + v1) / 2, label, fontsize=6, ha="center", va="center")
        else:
            ax.text(u1 + 6, (v0 + v1) / 2, label, fontsize=6, va="center")
    crown = pr["steps"][-1]
    lip, c = pr["lip"]["width"], crown["chamfer"]
    for a, b in ((crown["u0"], crown["u0"] + lip), (crown["u1"] - lip, crown["u1"])):
        ax.plot([a, b], [crown["v1"] + 1.5, crown["v1"] + 1.5], color=C_LIP, lw=3.5, solid_capstyle="butt")
    cf = pr["cuff"]
    ax.add_patch(Rectangle((cf["u0"], crown["v1"] - cf["depth"]), cf["u1"] - cf["u0"], cf["depth"], fc=C_RUBBER, ec="k",
                           lw=0.4))
    u = cf["u0"] + 4
    while u + cf["rib_width"] <= cf["u1"]:
        ax.add_patch(Rectangle((u, crown["v1"] - cf["depth"]), cf["rib_width"], cf["depth"] + 2, fc="#3a3b3f", ec="none"))
        u += cf["rib_pitch"]
    hs = pr["hidden_strip"]
    ax.add_patch(Rectangle((hs["u"] - 6, hs["v"] - 3), hs["width"], 6, fc=C_WARM, ec="k", lw=0.3))
    note(ax, (hs["u"], hs["v"]), "L3 skrytá lišta 12 mm (jen horní člen)", (-75, 85))
    note(ax, (crown["u0"] + 9, crown["v1"] + 2), "leštěný lem 18 mm přes zkosení 12 mm", (-75, 120))
    note(ax, ((cf["u0"] + cf["u1"]) / 2, crown["v1"] - 3), "pryžová manžeta 50 mm, žebra 7 / rozteč 15, hl. 6", (150, 135))
    dim(ax, (0, -55), (300, -55), "modul 300 (spára 2 × 4)")
    dim(ax, (pr["steps"][1]["u0"], -20), (pr["steps"][1]["u1"], -20), "224", fs=5)
    dim(ax, (390, 0), (390, 100), "100 (W)\n80 (N)", off=(18, 0))
    ax.text(150, 158, "u podél chodby →   v od líce stěny do chodby ↑   (mm)", fontsize=6, ha="center", color="#555")
    ax.set_xlim(-90, 440)
    ax.set_ylim(-75, 170)


def view_floor(ax, spec, secs):
    w = secs["W"]
    fl = spec["floor"]
    L = spec["portal_length"]
    half = w["width"] / 2
    x = 0.0
    parts = [("t", L), ("p", fl["plate_length"]), ("b", fl["band_length"]), ("p", fl["plate_length"]), ("t", L)]
    for kind, ln in parts:
        if kind == "t":
            ax.add_patch(Rectangle((x, -half), ln, 2 * half, fc="#cfc6b3", ec="k", lw=0.5))
            for s in (-1, 1):
                ax.add_patch(Polygon(octagon(x + ln / 2, s * (half - 0.12), 0.15, 0.15, 0.04), fc="#2b2d31", ec="k",
                                     lw=0.4))
                ax.add_patch(Rectangle((x + ln / 2 - 0.045, s * (half - 0.12) - 0.02), 0.09, 0.04, fc=C_COOL))
        elif kind == "p":
            cw = fl["centre_width"]
            o = octagon(x + ln / 2, 0, ln - fl["gap"], cw - fl["gap"], fl["corner_chamfer"])
            ax.add_patch(Polygon(o, fc="#a7abb2", ec="k", lw=0.5))
            i = octagon(x + ln / 2, 0, ln - fl["gap"] - 2 * (fl["lip_inset"] + fl["lip"]),
                        cw - fl["gap"] - 2 * (fl["lip_inset"] + fl["lip"]), fl["corner_chamfer"] * 0.8)
            ax.add_patch(Polygon(i, fc="#7d8188", ec=C_LIP, lw=1.6, hatch="...."))
            for s in (-1, 1):
                y0 = s * cw / 2
                y1 = s * (half - fl["gutter"])
                ax.add_patch(Rectangle((x + 0.005, min(y0, y1)), ln - 0.01, abs(y1 - y0), fc="#9a9ea5", ec="k", lw=0.4))
                for g in range(fl["side_plate_grooves"]):
                    yy = y0 + (y1 - y0) * (g + 1) / (fl["side_plate_grooves"] + 1)
                    ax.plot([x + 0.06, x + ln - 0.06], [yy, yy], color="#555", lw=0.4)
                ax.add_patch(Rectangle((x, min(y1, s * half)), ln, fl["gutter"], fc="#5d6066", ec="k", lw=0.3))
        else:
            ax.add_patch(Rectangle((x + 0.005, -half), ln - 0.01, 2 * half, fc="#9a9ea5", ec="k", lw=0.5))
            b = fl["band"]
            for g in range(b["grooves"]):
                xx = x + 0.04 + g * (ln - 0.08) / (b["grooves"] - 1)
                ax.plot([xx, xx], [-half + 0.12, -0.25], color="#444", lw=0.5)
                ax.plot([xx, xx], [0.25, half - 0.12], color="#444", lw=0.5)
            cl, cwid = b["cover"]
            ax.add_patch(Rectangle((x + ln / 2 - cwid / 2, -cl / 2), cwid, cl, fc="#b9bcc2", ec="k", lw=0.5))
            ax.add_patch(Rectangle((x + ln / 2 - 0.025, -0.075), 0.05, 0.15, fc="none", ec="#333", lw=0.4))
            ax.text(x + ln / 2, 0, "logo", fontsize=4, rotation=90, ha="center", va="center")
            for s in (-1, 1):
                ax.add_patch(Circle((x + ln / 2, s * (half - 0.06)), b["bolt_cups"]["d"] / 2, fc="#666", ec="k", lw=0.3))
        x += ln
    note(ax, (L + 0.45, 0), "osmiboká deska 0,9 × 1,2, zkosení 120,\nleštěný lem 18, perforace Ø15 / 25 hex", (L + 0.1, 1.55))
    note(ax, (L + 1.05, 0.7), "příčný pás 0,3: 5 drážek, destička 400 × 150, 4 šrouby", (1.0, -1.65))
    note(ax, (L + 0.3, 0.85), "boční deska W, 4 drážky; žlab 0,1 u soklu", (-0.1, 1.85))
    dim(ax, (-0.08, -half), (-0.08, half), "W 2,4", off=(-0.08, 0))
    ax.text(x / 2, -1.95, "N 1,2: jen střední deska a pás (boční desky odpadají)", fontsize=6, ha="center", color="#555")
    ax.set_xlim(-0.3, x + 0.1)
    ax.set_ylim(-2.05, 2.05)


def view_joint(ax, spec):
    """Elevation of the pillar foot where the wall plinth and the floor meet the portal (mm)."""
    ax.add_patch(Rectangle((-250, -200), 800, 150, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    # floor: plate (lip at 0, insert 6 lower), threshold under the portal, 10 mm gaps
    ax.add_patch(Rectangle((-250, -50), 245, 50, fc="#a7abb2", ec="k", lw=0.5))
    ax.add_patch(Rectangle((5, -50), 290, 50, fc="#cfc6b3", ec="k", lw=0.5))
    ax.add_patch(Rectangle((305, -50), 245, 50, fc="#a7abb2", ec="k", lw=0.5))
    for a in (-250 + 20, 305 + 20):
        ax.plot([a, a + 18], [1, 1], color=C_LIP, lw=3)
    # wall plinth 100 high with its 45 deg chamfer, stopping at the portal base with half the shadow gap
    for x0, x1 in ((-250, -4), (304, 550)):
        ax.add_patch(Polygon([(x0, 0), (x1, 0), (x1, 70), (x1, 100), (x0, 100), (x0, 70)], fc="#55585e", ec="k", lw=0.4))
        ax.plot([x0, x1], [70, 70], color=C_COOL, lw=1.5)
    ax.add_patch(Rectangle((8, 0), 284, 420, fc=C_FRAME, ec="k", lw=0.6))
    ax.add_patch(Rectangle((38, 0), 224, 420, fc="#efe7d6", ec="k", lw=0.4))
    ax.add_patch(Rectangle((68, 170), 164, 250, fc="#f6f0e3", ec="k", lw=0.4))
    ax.add_patch(Polygon(octagon(150, 95, 150, 150, 40), fc="#2b2d31", ec="k", lw=0.5))
    ax.add_patch(Rectangle((105, 70), 90, 50, fc=C_COOL))
    note(ax, (150, 95), "L1 pouzdro 150 × 150 × 60, difuzor 90 × 50", (330, 300))
    note(ax, (-120, 70), "sokl stěny 100, modrá lišta – končí u základny", (-240, 250))
    note(ax, (-220, 1), "lem desky 18 nad vložkou −6", (-240, 160))
    note(ax, (150, -25), "práh portálu 290, spára 10", (300, -120))
    ax.text(150, 440, "pata pilíře (pohled z chodby, mm)", fontsize=6, ha="center", color="#555")
    ax.set_xlim(-260, 560)
    ax.set_ylim(-210, 470)


def view_eye(ax, spec, secs):
    """Pinhole view from the eye down a W corridor: three portals on the 2.4 pitch, floor plates, lights."""
    w = secs["W"]
    eye = spec["eye"]["height"]
    f = 1.0 / math.tan(math.radians(spec["eye"]["fov"] / 2))
    outer = full(section_profile(w))
    p = spec["profile"]["protrusion_by_section"]["W"] / 1000
    inner = full(offset_inward(section_profile(w), p))

    def proj(x, y, z):
        return (-y * f / x, (z - eye) * f / x)

    starts = [1.2, 3.6, 6.0]
    for x0 in starts:
        for x in (x0, x0 + spec["portal_length"]):
            ax.add_patch(Polygon([proj(x, y, z) for y, z in outer + list(reversed(inner))], closed=True, fc=C_FRAME,
                                 ec=C_FRAME_E, lw=0.4, alpha=0.75))
            ax.plot(*zip(*[proj(x, y, z) for y, z in inner]), color=C_LIP, lw=1.2)
        for s in (-1, 1):
            ax.add_patch(Circle(proj(x0 + 0.15, s * (w["width"] / 2 - p - 0.05), 0.1), 0.012, fc=C_COOL))
            ax.add_patch(Circle(proj(x0 + 0.15, s * (w["ceiling_width"] / 2 - p), 2.08), 0.012, fc=C_WARM))
    for (y0, z0) in outer:
        a, b = proj(0.6, y0, z0), proj(8.4, y0, z0)
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#888", lw=0.4)
    fl = spec["floor"]
    for x0 in starts[:-1]:
        for xs in (x0 + 0.3, x0 + 0.3 + fl["plate_length"] + fl["band_length"]):
            o = octagon(xs + fl["plate_length"] / 2, 0, fl["plate_length"], fl["centre_width"], fl["corner_chamfer"])
            ax.add_patch(Polygon([proj(x, y, 0.0) for x, y in o], fc="#9ea2a9", ec=C_LIP, lw=0.6))
    ax.text(0, -1.0, "oko 1,65 m v ose, FOV %d° (nejistě, FOV ze SC dodá autor); portály po 2,4 m" % spec["eye"]["fov"],
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
        cell.set_height(0.09 if r == 0 else 0.2)
    mats = ("Materiály (styl výrobce v part.md): lak rámu = paletová barva výrobce (Halcyon: krémová); leštěný lem = "
            "leštěný kov; manžeta = guma; podlahová vložka = perforovaný grafit; desky a pás = grafit. Všechna "
            "světla v pouzdře nebo skrytá, bez stínů.")
    ax.text(0.0, 0.18, mats, fontsize=6, wrap=True, va="top")
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
        ("podlaha", fig.add_axes([0.03, 0.05, 0.30, 0.40]), lambda ax: (setup(ax, "4 Podlaha – půdorys rozteče 2,4 (W)",
                                                                              "1:20"), view_floor(ax, spec, secs))),
        ("napojeni", fig.add_axes([0.36, 0.05, 0.22, 0.40]), lambda ax: (setup(ax, "5 Napojení na stěnu a podlahu",
                                                                               "1:5"), view_joint(ax, spec))),
        ("oko", fig.add_axes([0.61, 0.22, 0.38, 0.30]), lambda ax: (setup(ax, "6 Pohled z oka 1,65 m", ""),
                                                                       view_eye(ax, spec, secs))),
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
