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
  parts   placed kit parts (XK-RCS blocks, strobes, the ramp light, the ramp pistons)
  skin    where the hull skin under the plates turns gunmetal
Regions: "pilot" = the roof (band R, spine, ribs over the roof), the shoulders (band S, longerons FR-LONG-HI and
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
        "bands": ["R", "S"],
        "frame": {"FR-SPINE": None, "FR-LONG-TOP": None, "FR-LONG-HI": None, "FR-RIB": 0.75},
        "parts": ["F-RAMP-FRAME", "F-RAMP-PISTON", "F-RAMP-TREAD", "F-RAMP-HINGE", "L-RAMP", "L-STROBE-FIN",
                  "L-STROBE-WING", "F-RCS-12", "F-RCS-13"],
        "skin": {"x": [3.0, 15.4], "v_min": 0.759},
        "_comment": "the roof, the shoulders, the stern and the pods: what the chase camera sees most (author 1. 10. 2026)",
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
    return out


def layout(m, region):
    reg = REGIONS[region]
    kit = m.kit
    plates, frame, parts = [], [], []
    # plates: the roof in plan (each side its own outline), the side bands from starboard, mirrored
    for e in m.elements:
        if e.cat != "panel" or e.data.get("band") not in reg["bands"]:
            continue
        if e.data["band"] == "R":
            ent = plate_entry(e, "TOP", e.geo["TOP"]["shape"], e.kit, kit, False, {"nz_min": 0.3})
            if e.data.get("sub") == "hatch":
                # two dark latches towards the roof edge, a quarter of the hatch's length from each end
                x0, y0, x1, y1 = e.geo["TOP"]["shape"].bounds
                yl = y1 - 0.045 if y1 > 0 else y0 + 0.045
                ent["latches"] = [[round(x0 + (x1 - x0) * f, 4), round(yl, 4)] for f in (0.25, 0.75)]
                ent["latch"] = kit[e.kit]["latch"]
            plates.append(ent)
        elif e.geo.get("SB"):
            plates.append(plate_entry(e, "SB", e.geo["SB"]["shape"], e.kit, kit, True, {"ny_max": -0.2}))
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
        elif ident in ("F-RCS-12", "F-RCS-13"):
            k = kit["XK-RCS"]
            parts.append({"id": ident, "type": "rcs", "on": d["on"], "x": d["x"], "deg": d["deg"], "size": k["size"],
                          "nozzle_d": k["nozzle_d"], "plate": k["plate"], "mirror": d.get("mirror", True),
                          "pod_axis": [rev["axis"]["y"], rev["axis"]["z"]]})
    # the channel floor under the plates and the frame, darker than the frame (MZ-CHANNEL; critic round 1)
    skin = dict(reg["skin"], material="channel", id="P-HULL")
    return {"plates": plates, "frame": frame, "parts": parts, "skin": skin}


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
