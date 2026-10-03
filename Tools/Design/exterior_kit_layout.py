"""The exterior kit's build layout from the approved drawings (author 1. 10. 2026: build the exterior kit and the pilot
from the approved drawings E-01 to E-08). The drawing model (exterior_model + exterior_views) already knows every
plate's outline with its cut-outs, the frame and the proposed parts; this script writes them as the input of the
Blender kit step (Tools/Blender/hs_exterior_kit.py), so the ship is built from exactly what the drawings show.

    python Tools/Design/exterior_kit_layout.py [Wayfarer] [--region pilot]

Writes ArtSource/Ships/<Ship>/Design/<Ship>_exterior_kit.json (generated - do not edit; the digests of the data it
was made from are in it and Tools/Tests/test_exterior_drawing.py checks them):
  plates  outlines in a view's plane: SB (x, z) for the side bands, TOP (x, y) for the roof, AFT (y, z) for the aft
          wall; each with its cut-outs, thickness, bevel, bolt points, material, the faces it may take (normal
          filter) and whether it is mirrored to port
  frame   the same for the ribs, longerons and the spine (lower than the plates: the plates sit on the frame)
  parts   placed kit parts (XK-RCS blocks, strobes, the ramp light, the ramp pistons, the conduits along the spine)
  decals  the plate numbers (rule D-R-PANEL-NUMBERS) as hs_decals texts (one-glyph library items pn_<glyph>)
  skin    where the hull skin under the plates turns gunmetal
Regions: "ship" = the whole hull (every band, the full frame). "pilot" = the roof (band R, spine, ribs over the roof), the shoulders (band S, longerons FR-LONG-HI and
FR-LONG-TOP, the ribs above v 0.75), the stern (ramp frame, pistons, ramp light) and the pods (XK-RCS on the pods,
fin and wing strobes) - the part of the ship the chase camera sees most.
"""
import argparse
import json
import math
import os
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import exterior_model as em  # noqa: E402
import exterior_views as ev  # noqa: E402

MAT = {"MZ-PAINT1": ("paint", 0), "MZ-PAINT2": ("paint", 1), "MZ-GUNMETAL": ("gunmetal", 0), "MZ-DARK": ("dark", 0),
       "MZ-METAL": ("metal", 0), "MZ-CHANNEL": ("channel", 0)}
REGIONS = {
    "pilot": {
        "bands": ["R", "S", "A"],
        "frame": {"FR-SPINE": None, "FR-LONG-TOP": None, "FR-LONG-HI": None, "FR-RIB": 0.75},
        "parts": ["F-RAMP-FRAME", "F-RAMP-PISTON", "F-RAMP-TREAD", "F-RAMP-HINGE", "L-RAMP", "L-STROBE-FIN",
                  "L-STROBE-WING", "F-RCS-12", "F-RCS-13", "F-CONDUIT", "F-CONDUIT-S", "F-VENT-AFT"],
        "skin": {"x": [3.0, 15.4], "v_min": 0.759},
        "aft_skin": True,
        "_comment": "the roof, the shoulders, the stern and the pods: what the chase camera sees most (author 1. 10. 2026); "
                    "the aft wall as plates on a frame (band A, step c 2. 10. 2026)",
    },
    "ship": {
        "bands": ["K", "L", "U", "N", "S", "R", "A"],
        "frame": {"FR-SPINE": None, "FR-LONG-TOP": None, "FR-LONG-HI": None, "FR-LONG-LO": None, "FR-RIB": None},
        "parts": ["F-RAMP-FRAME", "F-RAMP-PISTON", "F-RAMP-TREAD", "F-RAMP-HINGE", "L-RAMP", "L-STROBE-FIN",
                  "L-STROBE-WING", "F-RCS-12", "F-RCS-13", "F-CONDUIT", "F-CONDUIT-S", "F-VENT-AFT"],
        "skin": {"x": [3.0, 15.4], "v_min": 0.759},
        "skin_near_side": 0.1,
        "aft_skin": True,
        "_comment": "the whole hull (author 2. 10. 2026: after the pilot the kit on the whole ship): every side band "
                    "(keel K, lower side L, upper side U, shoulder S), the roof, the aft wall, the full frame (ribs over "
                    "the whole height, the low longeron) and the channel skin over the whole hull",
    },
}


def rings(g, tol=0.004):
    """Polygon(s) as [[outer, [hole, ...]], ...] with rounded coordinates."""
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        p = p.simplify(tol, preserve_topology=True)
        r = lambda ring: [[round(x, 4), round(y, 4)] for x, y in list(ring.coords)[:-1]]
        out.append([r(p.exterior), [r(h) for h in p.interiors]])
    return out


def bolt_points(full, shp, kit):
    """Bolts of a heavy plate as the drawing places them (Drawer.bolts): at every pitch along the first axis, near
    both ends of the plate's cut line across it, inset by the kit's edge distance; only those on the plate."""
    from shapely.geometry import Point
    if "bolt_pitch" not in kit or "bolt_edge" not in kit:          # frame kits place their bolts in profile()
        return []
    x0, z0, x1, z1 = full.bounds
    pitch, edge = kit["bolt_pitch"], kit["bolt_edge"]
    pts = []
    for x in em.bolt_columns(x0, x1, edge, pitch):
        cut = LineString([(x, z0 - 1), (x, z1 + 1)]).intersection(full)
        if not cut.is_empty:
            b = cut.bounds
            if b[3] - b[1] > 2 * edge + 0.05:
                pts += [(x, b[1] + edge), (x, b[3] - edge)]
    return [[round(a, 4), round(b, 4)] for a, b in pts if shp.buffer(-0.01).contains(Point(a, b))]


def plate_entry(e, view, shape, kit, design_kit, mirror, normal):
    mat, p2 = MAT[e.material]
    k = design_kit[kit]
    return {"id": e.id, "kit": kit, "material": mat, "paint2": p2, "view": view, "mirror": mirror, "normal": normal,
            "t": k.get("t", k.get("h", 0.02)), "bevel": k.get("bevel", 0.004), "polys": rings(shape),
            "bolts": bolt_points(shape, shape, k), "bolt_d": k.get("bolt_d", 0.0)}


def vent_entries(e, view, g, k, normal, horizontal, mirror=False):
    """XK-VENTBOX as three plates (critic round 2: the mid layer): the gunmetal housing with its rim (the outline with
    the inner opening as a hole), the dark floor of the opening lower than the rim, gunmetal slats across it
    (horizontal: slats along the first axis, stacked along the second - the aft wall; else across the first axis)."""
    inner = g.buffer(-k["rim"], join_style=2)
    base = dict(id=e.id, kit=e.kit, view=view, mirror=mirror, normal=normal, bolts=[], bolt_d=0.0, paint2=0)
    out = [dict(base, material="gunmetal", t=k["t"], bevel=k["bevel"], polys=rings(g.difference(inner)))]
    out.append(dict(base, material="dark", t=k["floor"], bevel=0.002, polys=rings(inner), suffix="Floor"))
    x0, y0, x1, y1 = inner.bounds
    bars, w, pitch = [], k["slat_w"], k["slat_pitch"]
    span = (y1 - y0) if horizontal else (x1 - x0)
    n = max(1, int((span - w) // pitch) + 1)
    lead = (span - (n - 1) * pitch) / 2
    for i in range(n):
        c = (y0 if horizontal else x0) + lead + i * pitch
        bars.append(box(x0, c - w / 2, x1, c + w / 2) if horizontal else box(c - w / 2, y0, c + w / 2, y1))
    out.append(dict(base, material="gunmetal", t=k["slat_t"], bevel=0.002, polys=rings(unary_union(bars)),
                    suffix="Slats"))
    return out


def side_dir(band):
    """Direction of a decal ray onto a side band (layout y > 0 side, mirrored): down and in on the shoulder S (~45 deg),
    up and in on the keel chamfer K, straight in on the upright sides L, U, N (revision G, 3. 10. 2026: the shoulder's
    ray on an upright side could hit the shoulder above first)."""
    return {"S": [0.0, -0.7071, -0.7071], "K": [0.0, -0.7071, 0.7071]}.get(band, [0.0, -1.0, 0.0])


def panel_numbers(m):
    """D-R-PANEL-NUMBERS on the built bands: the shoulder plates (side view) in their lower aft corner, the edge
    distance in; the roof plates (plan) at their aft edge between the doubler and the hatch bands (the outer corner
    lies on the roof edge's slope). hs_decals texts out of the one-glyph library items pn_<glyph>."""
    rule = m.by_id.get("D-R-PANEL-NUMBERS")
    if rule is None:
        return []
    d = rule.data
    roof = m.design["panels"]["roof"]
    sub = roof["sub"]
    out = []
    for e in m.elements:
        if e.cat != "panel" or e.data.get("sub") or e.data.get("band") not in d.get("bands", []):
            continue
        num = e.id.split("-")[-1]
        # the glyph items are 3.4 cm letters; the rule's size scales them (revision G critic: 7 cm, readable at 3-5 m)
        k = d["size"] / 0.034
        glyphs = dict(glyphs=num, prefix="pn_", advance=round(0.022 * k, 4), scale=round(k, 3))
        if e.data["band"] == "R":
            shp = e.geo["TOP"]["shape"]
            x0, y0, x1, y1 = shp.bounds
            side = 1 if e.data["side"] == "L" else -1
            top = max(sub["doubler_odd"]["y"][1], sub["doubler_even"]["y"][1], sub["vent"]["y"][1])
            yc = side * (roof["spine_gap"] + (top + sub["hatch_y"][0]) / 2)
            # clear of the plate's cut-outs and its doubler / hatch / vent box: slide forward from the aft edge
            busy = unary_union([o.geo["TOP"]["shape"] for o in m.elements
                                if o.data.get("of") == e.id and o.geo.get("TOP")] or [Polygon()])
            ok = shp.buffer(-0.02, join_style=2).difference(busy.buffer(0.02, join_style=2))
            hw, hh = 0.06, d["size"] / 2 + 0.004
            x = x0 + d["edge"] + hw
            while x < x1 - hw and not ok.contains(box(x - hw, yc - hh, x + hw, yc + hh)):
                x += 0.02
            if x >= x1 - hw:
                continue
            out.append(dict({"id": "D-PN-%s" % num, "on": "top", "x": round(x, 4), "y": round(yc, 4), "mirror": False},
                            **glyphs))
        else:
            shp = e.geo["SB"]["shape"]
            x0, z0, x1, z1 = shp.bounds
            xs = x0 + d["edge"] + 0.06
            cut = LineString([(xs, z0 - 1), (xs, z1 + 1)]).intersection(shp)
            zb = (cut.bounds[1] if not cut.is_empty else z0) + d["edge"] + d["size"] / 2
            # a ray onto the band's face (side_dir: the shoulder ~45 deg down and in; hs_decals 'ray', mirrored)
            yh = m.hull_y(xs, zb)
            out.append(dict({"id": "D-PN-%s" % num, "on": "ray", "at": [round(xs, 4), round(yh, 4), round(zb, 4)],
                             "dir": side_dir(e.data["band"]), "mirror": True}, **glyphs))
    return out


def along(lines, pitch):
    """Points along lines (a ring or a line string, or several) every pitch, from half a pitch in."""
    pts = []
    for ln in getattr(lines, "geoms", [lines]):
        n = int(ln.length // pitch)
        for i in range(n):
            p = ln.interpolate(pitch / 2 + i * pitch)
            pts.append((p.x, p.y))
    return pts


def profile(shp, k):
    """A frame piece's T profile (critic round 1: the frame read as a flat dark fill): the web on top - the outline
    inset to the kit's cap width, cap_h higher - and the bolt rows on the flange both sides of the web."""
    if not k.get("cap_w") or shp.is_empty:
        return {}
    w = k["w"]
    web = em.polys_only(shp.buffer(-(w - k["cap_w"]) / 2, join_style=2))
    rows = shp.buffer(-(w - k["cap_w"]) / 4, join_style=2)
    r = k["bolt_d"] / 2
    pts = []
    if not rows.is_empty:
        keep_off = web.buffer(r + 0.002)
        inside = shp.buffer(-(r + 0.002))
        pts = [p for p in along(rows.boundary, k["bolt_pitch"])
               if inside.contains(Point(p)) and not keep_off.contains(Point(p))]
    out = {"bolts": [[round(a, 4), round(b, 4)] for a, b in pts], "bolt_d": k["bolt_d"]}
    if not web.is_empty:
        out["cap"] = {"polys": rings(web), "t": k["h"] + k["cap_h"]}
        if k.get("cap_material"):
            # the spine's crest in bare metal (critic round 2: lighter than the frame)
            out["cap"]["material"] = MAT[k["cap_material"]][0]
    return out


def layout(m, region):
    reg = REGIONS[region]
    kit = m.kit
    plates, frame, parts = [], [], []

    def rise(e, ent):
        # a doubler panel stands kit "rise" above its own plate (revision G critic: on the 40 mm plates K, L, N the
        # 42 mm doubler stood 2 mm proud and read as a drawn outline)
        k = kit[e.kit]
        if e.data.get("sub") == "doubler" and "rise" in k:
            ent["t"] = round(kit[m.by_id[e.data["of"]].kit]["t"] + k["rise"], 4)
        return ent
    # plates: the roof in plan (each side its own outline), the side bands from starboard, mirrored
    for e in m.elements:
        if e.cat != "panel" or e.data.get("band") not in reg["bands"] or e.data["band"] == "A":
            continue
        if e.data["band"] == "R":
            ent = rise(e, plate_entry(e, "TOP", e.geo["TOP"]["shape"], e.kit, kit, False, {"nz_min": 0.3}))
            if e.data.get("sub") == "vent":
                plates += vent_entries(e, "TOP", e.geo["TOP"]["shape"], kit[e.kit], {"nz_min": 0.3}, False)
                continue
            if e.data.get("sub") == "hatch":
                # two dark latches towards the roof edge, a quarter of the hatch's length from each end
                x0, y0, x1, y1 = e.geo["TOP"]["shape"].bounds
                yl = y1 - 0.045 if y1 > 0 else y0 + 0.045
                ent["latches"] = [[round(x0 + (x1 - x0) * f, 4), round(yl, 4)] for f in (0.25, 0.75)]
                ent["latch"] = kit[e.kit]["latch"]
            plates.append(ent)
        elif e.geo.get("SB"):
            if e.data.get("sub") == "vent":
                # a vent box on a side plate (revision G: the side mid layer), slats upright, both sides
                plates += vent_entries(e, "SB", e.geo["SB"]["shape"], kit[e.kit], {"ny_max": -0.2}, False, mirror=True)
                continue
            ent = rise(e, plate_entry(e, "SB", e.geo["SB"]["shape"], e.kit, kit, True, {"ny_max": -0.2}))
            if e.data.get("sub") == "hatch":
                # two dark latches along the hatch's lower edge, a quarter of its length from each end (as on the roof)
                x0, z0, x1, z1 = e.geo["SB"]["shape"].bounds
                ent["latches"] = [[round(x0 + (x1 - x0) * f, 4), round(z0 + 0.045, 4)] for f in (0.25, 0.75)]
                ent["latch"] = kit[e.kit]["latch"]
            plates.append(ent)
    # the aft wall (band A): plates on the frame FR-AFT with vent boxes, in the aft view (y, z; the layout's own
    # coordinates - the drawing turns them to paper axes)
    aft = m.design["panels"].get("aft")
    if aft and aft["band"] in reg["bands"]:
        lay = m.views_model.aft_layout()
        for ident, tag, n, shp in lay["plates"]:
            plates.append(plate_entry(m.by_id[ident], "AFT", shp, aft["kit"], kit, False, aft["normal"]))
        for ident, g in lay["vents"]:
            e = m.by_id[ident]
            for ent in vent_entries(e, "AFT", g, kit[e.kit], aft["normal"], True):
                plates.append(ent)
        e = m.by_id[next(f["id"] for f in m.design["frame"] if f["kind"] == "aft")]
        k = kit[e.kit]
        frame.append(dict(dict(plate_entry(e, "AFT", lay["frame"], e.kit, kit, False, aft["normal"]), t=k["h"],
                               bevel=0.003, bolts=[]), **profile(lay["frame"], k)))
    # the frame: from starboard (mirrored) where it is on the side and the shoulders, in plan over the flat roof
    upper = m.hull_band(0.0, 21.0, 0.0, 1.0)
    for ident, v_min in reg["frame"].items():
        e = m.by_id[ident]
        k = kit[e.kit]
        if e.geo.get("SB"):
            shp = e.geo["SB"]["shape"]
            if v_min is not None:
                shp = em.polys_only(shp.intersection(m.hull_band(0.0, 21.0, v_min, 1.0)))
            if not shp.is_empty:
                frame.append(dict(dict(plate_entry(e, "SB", shp, e.kit, kit, True, {"ny_max": -0.2}), t=k["h"],
                                       bevel=0.003, bolts=[]), **profile(shp, k)))
        top = e.geo.get("TOP")
        if top and (e.data.get("kind") in ("spine",) or (e.data.get("kind") == "ribs" and e.data.get("roof"))):
            shp = top["shape"]
            if e.data.get("kind") == "ribs":
                # only over the flat roof: the shoulders' part is in the side outline above
                shp = em.polys_only(shp.intersection(unary_union([box(x - 1, -m.hw(x) * m.u_out(1.0) * 1.02, x + 1,
                                                                       m.hw(x) * m.u_out(1.0) * 1.02)
                                                                   for x in m.seams])))
            # nz_min 0.5: the seam grooves under the ribs are a V with faces at nz 0.6 (fill_grooves lifts them)
            frame.append(dict(dict(plate_entry(e, "TOP", shp, e.kit, kit, False, {"nz_min": 0.5}), t=k["h"],
                                   bevel=0.003, bolts=[]), **profile(shp, k)))
    _ = upper
    # parts
    rev = m.recipe["parts"]["pod"]["revolve"]
    for ident in reg["parts"]:
        e = m.by_id[ident]
        d = e.data
        if ident == "F-RAMP-FRAME":
            k = kit[d["kit"]]
            (y0, y1), (z0, z1), w = d["y"], d["z"], d["w"]
            g = box(y0, z0, y1, z1).difference(box(y0 + w, z0 - 1.0, y1 - w, z1 - w))
            # bolts along the U's centre line
            mid = LineString([(y0 + w / 2, z0), (y0 + w / 2, z1 - w / 2), (y1 - w / 2, z1 - w / 2), (y1 - w / 2, z0)])
            bolts = [[round(a, 4), round(b, 4)] for a, b in along(mid, k["bolt_pitch"])]
            frame.append(dict(plate_entry(e, "AFT", g, d["kit"], kit, False, {"nx_max": -0.5}), t=k["h"],
                              bevel=k.get("bevel", 0.004), bolts=bolts, bolt_d=k["bolt_d"], material="gunmetal", paint2=0))
            gus = ev.ramp_gussets(d, k)
            if gus:
                frame.append(dict(plate_entry(e, "AFT", unary_union(gus), d["kit"], kit, False, {"nx_max": -0.5}),
                                  t=k["gusset_t"], bevel=0.003, suffix="Gussets", material="gunmetal", paint2=0,
                                  bolts=[[round(a, 4), round(b, 4)] for a, b in ev.ramp_gusset_bolts(d, k)],
                                  bolt_d=k["bolt_d"]))
        elif ident == "F-RAMP-TREAD":
            # on the ramp door, a recipe plate (P-B-07) proud of the hull: the bars and the threshold stand on it
            k = kit[d["kit"]]
            base = m.by_id["P-B-07"].data["t"]
            shapes = ev.tread_bars(d, k)
            frame.append(dict(plate_entry(e, "AFT", unary_union(shapes[:-1]), d["kit"], kit, False, {"nx_max": -0.5}),
                              t=base + k["h"], bevel=0.003, bolts=[], material="gunmetal", paint2=0))
            frame.append(dict(plate_entry(e, "AFT", shapes[-1], d["kit"], kit, False, {"nx_max": -0.5}),
                              t=base + k["threshold_h"], bevel=0.003, bolts=[], material="dark", paint2=0,
                              suffix="Threshold"))
        elif ident == "F-RAMP-HINGE":
            k = kit[d["kit"]]
            parts.append({"id": ident, "type": "hinge", "x": d["x"], "y": d["y"], "z": d["z"], "d": k["d"],
                          "knuckle": k["knuckle"], "count": k["count"], "pin_d": k["pin_d"], "mirror": False})
        elif ident == "F-RAMP-PISTON":
            k = kit[d["kit"]]
            parts.append({"id": ident, "type": "piston", "x": d["x"], "y": d["y"], "z": d["z"], "d": k["d"],
                          "rod_d": k["rod_d"], "bracket": k["bracket"], "hose_d": k["hose_d"],
                          "mirror": d.get("mirror", True)})
        elif ident in ("L-RAMP",):
            k = kit[d["kit"]]
            parts.append({"id": ident, "type": "lamp", "on": "aft", "x": d["x"], "y": d["y"], "z": d["z"], "size": k["size"],
                          "lens_d": k["lens_d"], "bracket": k["bracket"], "light": d.get("light"), "color": d["color"],
                          "mirror": d.get("mirror", True)})
        elif ident in ("L-STROBE-FIN", "L-STROBE-WING"):
            k = kit[d["kit"]]
            if d["on"] == "fin_tip":
                tip = max(p[0] for p in m.front["fin"])
                root = min(p[0] for p in m.front["fin"] if p[1] >= max(q[1] for q in m.front["fin"]) - 1e-6)
                at = [d["x"], (tip + root) / 2, d["z"]]
                nrm = [0.0, 0.0, 1.0]
            else:
                at = [d["x"], d["y"], d["z"]]
                nrm = [0.0, 1.0, 0.0]
            parts.append({"id": ident, "type": "strobe", "at": at, "normal": nrm, "size": k["size"], "mirror": True,
                          "position": d.get("position"), "mirror_position": d.get("mirror_position", d.get("position"))})
        elif ident == "F-CONDUIT":
            k = kit[d["kit"]]
            runs = [{"y": round(sd * p["y"], 4), "d": p["d"], "material": MAT[p["material"]][0], "x": [x0, x1]}
                    for p, sd, x0, x1 in ev.conduit_runs(m, d)]
            parts.append({"id": ident, "type": "conduit", "runs": runs, "lift": k["lift"], "clamp_pitch": k["clamp_pitch"],
                          "clamp_w": k["clamp_w"], "flange": k["flange"], "mirror": False,
                          "avoid_x": [round(x, 4) for x in m.seams], "avoid_w": kit["XK-RIB"]["w"] / 2 + 0.03})
        elif ident == "F-CONDUIT-S":
            # along the shoulder, over the S plates (side view x, z; mirrored): each pipe a polyline at its section
            # height v, lifted off the skin along the surface normal
            k = kit[d["kit"]]
            runs = []
            for p in d["pipes"]:
                n = max(2, int((d["x"][1] - d["x"][0]) / 0.3) + 1)
                xs = [d["x"][0] + (d["x"][1] - d["x"][0]) * i / (n - 1) for i in range(n)]
                runs.append({"pts": [[round(x, 4), round(m.z_of(x, p["v"]), 4)] for x in xs], "d": p["d"],
                             "material": MAT[p["material"]][0]})
            parts.append({"id": ident, "type": "conduit", "view": "SB", "runs": runs, "lift": d["lift"],
                          "clamp_pitch": k["clamp_pitch"], "clamp_w": k["clamp_w"], "flange": k["flange"], "mirror": True,
                          "avoid_x": [round(x, 4) for x in m.seams], "avoid_w": kit["XK-RIB"]["w"] / 2 + 0.03})
        elif ident == "F-VENT-AFT":
            k = kit[d["kit"]]
            for sd in ((1, -1) if d.get("mirror", True) else (1,)):
                g = box(sd * d["y"] - d["w"] / 2, d["z"][0], sd * d["y"] + d["w"] / 2, d["z"][1])
                for ent in vent_entries(e, "AFT", g, k, {"nx_max": -0.5}, True):
                    ent["suffix"] = ("%s_%s" % (ent.get("suffix", "Box"), "L" if sd > 0 else "R"))
                    frame.append(ent)
        elif ident in ("F-RCS-12", "F-RCS-13"):
            k = kit["XK-RCS"]
            parts.append({"id": ident, "type": "rcs", "on": d["on"], "x": d["x"], "deg": d["deg"], "size": k["size"],
                          "nozzle_d": k["nozzle_d"], "plate": k["plate"], "mirror": d.get("mirror", True),
                          "pod_axis": [rev["axis"]["y"], rev["axis"]["z"]]})
    # the channel floor under the plates and the frame, darker than the frame (MZ-CHANNEL; critic round 1)
    skin = dict(reg["skin"], material="channel", id="P-HULL")
    if reg.get("skin_near_side"):
        # on the sides only round the plates and the frame (whole-ship kit critic round 1, 3. 10. 2026: the whole
        # skin as channel floor read as a black hull with white patches): the side outlines of every side plate and
        # frame piece, grown by the margin - elsewhere (the nose, the keel without plates) the paint stays
        near = unary_union([e.geo["SB"]["shape"] for e in m.elements
                            if e.geo.get("SB") and ((e.cat == "panel" and e.data.get("band") in reg["bands"]
                                                     and e.data.get("band") not in ("R", "A"))
                                                    or e.id in reg["frame"])])
        skin["near_side"] = [r[0] for r in rings(near.buffer(reg["skin_near_side"], join_style=2), 0.01)]
    if reg.get("aft_skin") and aft:
        # the aft wall between the plates, the frame and the ramp frame reads as the channel too (the white wall round
        # the plates read as one white box); not inside the ramp frame (the door leaf P-B-07 and its seam)
        fr = m.by_id["F-RAMP-FRAME"].data
        skin["aft"] = {"outline": aft["outline"], "normal": aft["normal"], "x_max": 0.7, "z_max": aft.get("skin_z_max", 99.0),
                       "exclude": [fr["y"][0], fr["z"][0] - 0.2, fr["y"][1], fr["z"][1]]}
    out = {"plates": plates, "frame": frame, "parts": parts, "skin": skin, "decals": panel_numbers(m)}
    decal_detail(m, out)
    return out


def decal_detail(m, out):
    """Small detail as mesh decals (triangle budget rule A, author 1. 10. 2026; recipe exterior_kit.decal_detail.scope,
    a list of IDs or "all"): the bolts of a plate or frame piece in scope are marked "bolts_as": "decal" (the builder
    places bolt_kit / bolt_kit_frame decals at the same points instead of bolt geometry); a small hatch in scope is
    not built - its plate keeps no hole and the hatch becomes decals (hatch_small at scale 1.3 + two latch_kit).
    The data, the IDs and the drawings stay as they are; only the way it is rendered changes."""
    scope = m.recipe.get("exterior_kit", {}).get("decal_detail", {}).get("scope", [])
    if not scope:
        return
    inside = (lambda i: True) if scope == "all" else (lambda i: i in scope)
    for ent in out["plates"] + out["frame"]:
        if inside(ent["id"]) and ent.get("bolts"):
            ent["bolts_as"] = "decal"
            ent["bolt_item"] = "bolt_kit_frame" if ent["kit"] in ("XK-RIB", "XK-LONGERON") else "bolt_kit"
    keep = []
    for ent in out["plates"]:
        e = m.by_id[ent["id"]]
        if e.data.get("sub") != "hatch" or not inside(ent["id"]) or ent.get("suffix"):
            keep.append(ent)
            continue
        view = ent["view"]
        g = e.geo[view]["shape"]
        x0, y0, x1, y1 = g.bounds
        hx, hy = m.kit["XK-HATCH"]["size"]
        if view == "TOP":
            out["decals"].append({"id": ent["id"], "item": "hatch_small", "on": "top", "x": round((x0 + x1) / 2, 4),
                                  "y": round((y0 + y1) / 2, 4), "scale": round(hx / 0.26, 3), "mirror": False,
                                  "check_overlap": False, "flat": True})
            for lx, ly in ent.get("latches", []):
                out["decals"].append({"id": ent["id"] + "-latch", "item": "latch_kit", "on": "top", "x": lx, "y": ly,
                                      "mirror": False, "check_overlap": False, "flat": True})
        else:
            # a side band (side view x, z): a ray onto the band's face like the plate numbers, both sides
            def ray(x, z, **kw):
                return dict({"on": "ray", "at": [round(x, 4), round(m.hull_y(x, z), 4), round(z, 4)],
                             "dir": side_dir(e.data["band"]), "mirror": True, "check_overlap": False, "flat": True}, **kw)
            out["decals"].append(ray((x0 + x1) / 2, (y0 + y1) / 2, id=ent["id"], item="hatch_small",
                                     scale=round(hx / 0.26, 3)))
            for lx, lz in ent.get("latches", []):
                out["decals"].append(ray(lx, lz, id=ent["id"] + "-latch", item="latch_kit"))
        # the parent plate keeps no hole where the hatch was cut out
        parent = next(p for p in keep + out["plates"] if p["id"] == e.data["of"] and not p.get("suffix"))
        pg = m.by_id[parent["id"]].geo[view]["shape"]
        parent["polys"] = rings(em.polys_only(pg.union(g.buffer(m.kit["XK-HATCH"]["gap"] + 0.002, join_style=2)).buffer(0)))
    out["plates"] = keep


def write(ship="Wayfarer", region="pilot"):
    m = em.Model(ship)
    out = {"_comment": "Generated by Tools/Design/exterior_kit_layout.py from the drawing model (the approved drawings "
                       "E-01 to E-08) - do not edit. Input of Tools/Blender/hs_exterior_kit.py: outlines in a view's "
                       "plane (SB: x, z; TOP: x, y; AFT: y, z), metres, layout coordinates.",
           "ship": ship, "region": region, "region_spec": REGIONS[region], "digests": m.digests}
    out.update(layout(m, region))
    path = os.path.join(em.ROOT, "ArtSource", "Ships", ship, "Design", "%s_exterior_kit.json" % ship)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    n = {k: len(out[k]) for k in ("plates", "frame", "parts")}
    print("EXTKIT wrote %s: %d plates, %d frame pieces, %d parts (%s)" % (os.path.relpath(path, em.ROOT), n["plates"],
                                                                          n["frame"], n["parts"], region))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ship", nargs="?", default="Wayfarer")
    ap.add_argument("--region", default="pilot", choices=sorted(REGIONS))
    a = ap.parse_args(argv)
    write(a.ship, a.region)


if __name__ == "__main__":
    main()
