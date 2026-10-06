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
    note(ax, (0.0, w["ceiling"] - 0.055), "L3 2× skrytá lišta v drážce u koruny (jen horní člen)", (-1.4, 2.62))
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
    pl = fl["plate_lengths"][0]
    xs = [0, L, L + pl, L + pl + fl["band_length"], L + 2 * pl + fl["band_length"]]
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
    dim(ax, (0, -0.32), (xs[1] + pl, -0.32), "rozteč 1,2 = 0,3 + 0,9")
    note(ax, (xs[4] + 0.15, 2.22), "řez horním členem: 3 stupně", (xs[4] - 0.9, 1.75))
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
    for st in pr["steps"]:
        c = st.get("chamfer", 0)
        u0, u1, v0, v1 = st["u0"], st["u1"], st["v0"], st["v1"]
        pts = [(u0, v0), (u1, v0), (u1, v1 - c), (u1 - c, v1), (u0 + c, v1), (u0, v1 - c)]
        ax.add_patch(Polygon(pts, fc=C_FRAME, ec="k", lw=0.6))
        label = "%s  %d–%d" % (st["name"], v0, v1)
        if u1 + 70 > 300:
            ax.text((u0 + u1) / 2, (v0 + v1) / 2, label, fontsize=6, ha="center", va="center")
        else:
            ax.text(u1 + 6, (v0 + v1) / 2, label, fontsize=6, va="center")
    mid = pr["steps"][1]
    for a, b in hs["grooves"]:
        # the groove up into step 2 from its ledge, against the crown's riser; the strip at its top
        ax.add_patch(Rectangle((a, mid["v1"] - hs["groove_depth"]), b - a, hs["groove_depth"], fc="white", ec="k", lw=0.4))
        ax.add_patch(Rectangle((a + 1, mid["v1"] - hs["groove_depth"]), b - a - 2, 3, fc=C_WARM, ec="k", lw=0.3))
    crown = pr["steps"][-1]
    lip = pr["lip"]["width"]
    for a, b in ((crown["u0"], crown["u0"] + lip), (crown["u1"] - lip, crown["u1"])):
        ax.plot([a, b], [crown["v1"] + 1.5, crown["v1"] + 1.5], color=C_LIP, lw=3.5, solid_capstyle="butt")
    cf = pr["cuff"]
    ax.add_patch(Rectangle((cf["u0"], crown["v1"] - cf["depth"]), cf["u1"] - cf["u0"], cf["depth"], fc=C_RUBBER, ec="k",
                           lw=0.4))
    u = cf["u0"] + 4
    while u + cf["rib_width"] <= cf["u1"]:
        ax.add_patch(Rectangle((u, crown["v1"] - cf["depth"]), cf["rib_width"], cf["depth"] + 2, fc="#3a3b3f", ec="none"))
        u += cf["rib_pitch"]
    g0 = hs["grooves"][0]
    note(ax, (g0[0] + 7, mid["v1"] - 18), "L3 2× lišta 12 v drážce 14 × 20 u boku koruny (symetricky)", (-85, 92))
    note(ax, (crown["u0"] + 9, crown["v1"] + 2), "leštěný lem 18 mm přes zkosení 12 mm", (-85, 128))
    note(ax, ((cf["u0"] + cf["u1"]) / 2, crown["v1"] - 3), "pryžová manžeta 50 mm, žebra 7 / rozteč 15, hl. 6", (150, 140))
    dim(ax, (0, -55), (300, -55), "modul 300 (spára 2 × 4)")
    dim(ax, (390, 0), (390, 100), "100 (W)\n80 (N)", off=(18, 0))
    # where the strip shows from the eye (1.65 m), rev. A against rev. B; the vertical half FOV at 90 deg, 16:9
    half_v = math.degrees(math.atan(math.tan(math.radians(spec["eye"]["fov"] / 2)) * 9 / 16))
    rows = []
    for title, groove in (("rev. A (1 lišta na římse)", False), ("rev. B (2 lišty v drážce)", True)):
        for side, far, elev in hidden_strip_visibility(spec, groove):
            if far is None:
                seen = "neviditelná do 10 m"
            elif far > 9.9:
                seen = "vidět z celé chodby (≥ 10 m, elevace od %.0f°)" % elev
            else:
                seen = ("vidět jen do %.2f m od člena (elevace ≥ %.0f°)" % (far, elev)).replace(".", ",")
            rows.append("%s, %s: %s" % (title, side, seen))
    rows.append("svislé ½ FOV při 90° (16:9) = %.0f°: při pohledu vodorovně je zdroj nad %.0f° mimo obraz" % (half_v, half_v))
    ax.text(-85, -68, "\n".join(rows), fontsize=5.5, va="top", family="monospace")
    ax.text(150, 162, "u podél chodby →   v od líce stěny do chodby ↑   (mm)", fontsize=6, ha="center", color="#555")
    ax.set_xlim(-90, 440)
    ax.set_ylim(-120, 172)


def view_floor(ax, spec, secs):
    """Plan of a 2.4 m pitch in W: threshold, walkway plate (A, lanes), band, grille plate (G), threshold."""
    w = secs["W"]
    fl = spec["floor"]
    L = spec["portal_length"]
    half = w["width"] / 2
    walk = fl["walk_width"] / 2
    edge = half - fl["edge_strip"]
    ln = fl["plate_lengths"][0]
    x = 0.0

    def sides(x, ln):
        for s in (-1, 1):
            y0, y1 = sorted((s * walk, s * edge))
            ax.add_patch(Rectangle((x + 0.005, y0 + 0.005), ln - 0.01, y1 - y0 - 0.01, fc="#a3a7ae", ec="k", lw=0.4))
            for bx in (x + 0.03, x + ln - 0.03):
                for by in (y0 + 0.03, y1 - 0.03):
                    ax.add_patch(Circle((bx, by), 0.006, fc="#555", ec="none"))
            ya, yb = sorted((s * edge, s * half))
            ax.add_patch(Rectangle((x, ya), ln, yb - ya, fc=C_FRAME, ec="k", lw=0.3))

    for kind, size in (("t", L), ("a", ln), ("b", fl["band_length"]), ("g", ln), ("t", L)):
        if kind == "t":
            ax.add_patch(Rectangle((x, -half), size, 2 * half, fc="#cfc6b3", ec="k", lw=0.5))
            for s in (-1, 1):
                ax.add_patch(Polygon(octagon(x + size / 2, s * (half - 0.12), 0.15, 0.15, 0.04), fc="#2b2d31", ec="k",
                                     lw=0.4))
                ax.add_patch(Rectangle((x + size / 2 - 0.045, s * (half - 0.12) - 0.02), 0.09, 0.04, fc=C_COOL))
        elif kind == "a":
            sides(x, size)
            o = octagon(x + size / 2, 0, size - 0.01, 2 * walk - 0.01, fl["corner_chamfer"])
            ax.add_patch(Polygon(o, fc=C_LIP, ec="k", lw=0.5))
            ins = fl["lip"]
            i = octagon(x + size / 2, 0, size - 0.01 - 2 * ins, 2 * walk - 0.01 - 2 * ins, fl["corner_chamfer"] * 0.85)
            ax.add_patch(Polygon(i, fc="#5f636a", ec="k", lw=0.4))
            ln_ = fl["lanes"]
            y = -walk + 0.06
            while y + ln_["width"] <= walk - 0.06:
                ax.add_patch(Rectangle((x + 0.07, y), size - 0.14, ln_["width"], fc="#3d4046", ec="none"))
                y += ln_["pitch"]
        elif kind == "g":
            sides(x, size)
            cw = fl["grille"]["channel_width"] / 2
            for s in (-1, 1):
                y0, y1 = sorted((s * cw, s * walk))
                ax.add_patch(Rectangle((x + 0.005, y0), size - 0.01, y1 - y0, fc="#5f636a", ec="k", lw=0.4))
                yy = y0 + 0.03
                while yy + 0.08 <= y1 - 0.02:
                    ax.add_patch(Rectangle((x + 0.05, yy), size - 0.1, 0.08, fc="#3d4046", ec="none"))
                    yy += 0.11
            ax.add_patch(Rectangle((x, -cw), size, 2 * cw, fc="#202124", ec=C_LIP, lw=1.4))
            yb = -cw
            while yb <= cw:
                ax.plot([x + 0.02, x + size - 0.02], [yb, yb], color="#8a8e95", lw=0.5)
                yb += fl["grille"]["bar_pitch"]
        else:
            ax.add_patch(Rectangle((x + 0.005, -half), size - 0.01, 2 * half, fc="#9a9ea5", ec="k", lw=0.5))
            b = fl["band"]
            for g in range(b["grooves"]):
                xx = x + 0.04 + g * (size - 0.08) / (b["grooves"] - 1)
                ax.plot([xx, xx], [-half + 0.12, -0.25], color="#444", lw=0.5)
                ax.plot([xx, xx], [0.25, half - 0.12], color="#444", lw=0.5)
            cl, cwid = b["cover"]
            ax.add_patch(Rectangle((x + size / 2 - cwid / 2, -cl / 2), cwid, cl, fc="#b9bcc2", ec="k", lw=0.5))
            for bx in (x + size / 2 - cwid / 2 + 0.02, x + size / 2 + cwid / 2 - 0.02):
                for by in (-cl / 2 + 0.025, cl / 2 - 0.025):
                    ax.add_patch(Circle((bx, by), 0.006, fc="#333", ec="none"))
            ax.add_patch(Rectangle((x + size / 2 - 0.025, -0.075), 0.05, 0.15, fc="none", ec="#333", lw=0.4))
            ax.text(x + size / 2, 0, "logo", fontsize=4, rotation=90, ha="center", va="center")
            for s in (-1, 1):
                ax.add_patch(Circle((x + size / 2, s * (half - 0.06)), b["bolt_cups"]["d"] / 2, fc="#666", ec="k", lw=0.3))
        x += size
    a0 = L
    note(ax, (a0 + 0.45, 0.35), "A: chodník 1,2 – protiskluzové pásy 80 / 110 ve vložce −6,\nleštěný lem 18, zkosené rohy 120",
         (a0 - 0.2, 1.58))
    note(ax, (a0 + 0.45, 0.9), "boční deska hladká, 4 šrouby; okrajová lišta 60", (-0.25, 1.9))
    note(ax, (a0 + ln + 0.15, -0.2), "pás 0,3: 5 drážek, destička 400 × 150 se 4 šrouby", (0.4, -1.62))
    note(ax, (a0 + ln + 0.3 + 0.45, 0.0), "G: mřížka nad kanálem 0,6 × hl. 0,2 (rozvody), lem 18", (1.3, -1.92))
    dim(ax, (-0.08, -half), (-0.08, half), "W 2,4", off=(-0.08, 0))
    ax.text(x / 2, -2.1, "N 1,2: jen chodník A nebo G a pás (boční desky odpadají); desky 0,9 a 0,6", fontsize=6,
            ha="center", color="#555")
    ax.set_xlim(-0.3, x + 0.1)
    ax.set_ylim(-2.2, 2.05)


def view_joint(ax, spec):
    """Elevation of the pillar foot where the wall plinth and the floor meet the portal (mm)."""
    ax.add_patch(Rectangle((-250, -200), 800, 150, fc="#d8d8d8", ec="#888", lw=0.4, hatch="////"))
    ax.add_patch(Rectangle((-250, -50), 245, 50, fc="#a7abb2", ec="k", lw=0.5))
    ax.add_patch(Rectangle((5, -50), 290, 50, fc="#cfc6b3", ec="k", lw=0.5))
    ax.add_patch(Rectangle((305, -50), 245, 50, fc="#a7abb2", ec="k", lw=0.5))
    for a in (-250 + 20, 305 + 20):
        ax.plot([a, a + 18], [1, 1], color=C_LIP, lw=3)
    # the wall plinth: a rubber kick strip 100 mm, no light (rev. B), stopping at the portal base with half the gap
    for x0, x1 in ((-250, -4), (304, 550)):
        ax.add_patch(Polygon([(x0, 0), (x1, 0), (x1, 100), (x0, 100)], fc=C_RUBBER, ec="k", lw=0.4))
        for zz in (25, 50, 75):
            ax.plot([x0 + 4, x1 - 4], [zz, zz], color="#45474c", lw=0.5)
    ax.add_patch(Rectangle((8, 0), 284, 420, fc=C_FRAME, ec="k", lw=0.6))
    ax.add_patch(Rectangle((38, 0), 224, 420, fc="#efe7d6", ec="k", lw=0.4))
    ax.add_patch(Rectangle((68, 170), 164, 250, fc="#f6f0e3", ec="k", lw=0.4))
    ax.add_patch(Polygon(octagon(150, 95, 150, 150, 40), fc="#2b2d31", ec="k", lw=0.5))
    ax.add_patch(Rectangle((105, 70), 90, 50, fc=C_COOL))
    note(ax, (150, 95), "L1 pouzdro 150 × 150 × 60,\ndifuzor 90 × 50", (330, 300))
    note(ax, (-120, 60), "sokl: pryžový kopací pás 100, žebra,\nBEZ holé modré lišty (rev. B)", (-245, 250))
    note(ax, (-220, 1), "lem desky 18 nad vložkou −6", (-245, 160))
    note(ax, (150, -25), "práh portálu 290, spára 10", (300, -120))
    ax.text(150, 440, "pata pilíře (pohled z chodby, mm)", fontsize=6, ha="center", color="#555")
    ax.set_xlim(-260, 560)
    ax.set_ylim(-210, 470)


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
    ax.text(0, -1.0, "rozteč %.1f m; oko 1,65 m v ose, FOV %d° (do dodání FOV ze SC)" % (pitch, spec["eye"]["fov"]),
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
    revs = "  ".join("%s %s: %s" % (r["rev"], r["date"], r["what"]) for r in spec.get("revisions", []))
    ax.text(0.0, 0.28, "\n".join(textwrap.wrap("Revize: " + revs, 175)), fontsize=5.5, va="top", color="#444")
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
        ("podlaha", fig.add_axes([0.03, 0.05, 0.30, 0.40]), lambda ax: (setup(ax, "4 Podlaha – půdorys rozteče 2,4 (W)",
                                                                              "1:20"), view_floor(ax, spec, secs))),
        ("napojeni", fig.add_axes([0.36, 0.05, 0.22, 0.40]), lambda ax: (setup(ax, "5 Napojení na stěnu a podlahu",
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
