"""The kit's shared material base against the workflow's limits (parts factory, FACTORY_WORKFLOW step 3, 6. 10. 2026).

    python Tools/Tests/test_kit_materials.py

The simplest version (tools in a pilot only as simple as works), offline, on ArtSource/Kit/kit_materials.json:
1. every role's roughness, metallic, micro roughness and scratches inside its limits (lacquer satin metallic <= 0.1 with
   a fine grain and no scratches, the lip light polished silver 0.15-0.25, rubber matt 0.85-0.9, graphite satin);
2. the lip's colour is fixed (an albedo of 0.7-0.8, no palette key): a maker changes the lacquer, never the lip;
3. every maker's palette has every colour a role names, linear 0..1; the anti-slip lanes at most lane_contrast_max
   lighter than the graphite field (the author: no "zebra crossing");
4. the maker's wear stays a style: amounts 0..1, the walked line narrower than a walkway and polished (lower
   roughness than the lanes), the edge wear as wide as a worn role's bevel (edge_wear_mm), the hand band inside 2.3 m;
5. the emissive roles in 0..1 colour, a positive strength.
Prints KITMAT PASS|FAIL lines and KITMAT SUMMARY; exit 1 on a failure.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "ArtSource", "Kit", "kit_materials.json")

fails = 0


def check(ok, what):
    global fails
    print("KITMAT %s %s" % ("PASS" if ok else "FAIL", what))
    if not ok:
        fails += 1


def inside(v, lo_hi):
    return lo_hi[0] - 1e-9 <= v <= lo_hi[1] + 1e-9


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def roles(data):
    return {k: v for k, v in data["roles"].items() if not k.startswith("_")}


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    limits, makers = data["limits"], {k: v for k, v in data["makers"].items() if not k.startswith("_")}
    for role, r in roles(data).items():
        lim = limits.get(role)
        check(lim is not None, "%s has limits" % role)
        if not lim:
            continue
        for key, val in (("roughness", r["roughness"]), ("metallic", r["metallic"]), ("micro_rough", r.get("micro_rough", 0.0)),
                         ("scratches", r.get("scratches", 0.0))):
            if key in lim:
                check(inside(val, lim[key]), "%s %s %.3f in %s" % (role, key, val, lim[key]))
        if "albedo" in lim:
            a = r.get("albedo")
            check(a is not None and "colour" not in r, "%s has a fixed albedo, not a palette colour" % role)
            if a:
                check(inside(lum(a), lim["albedo"]), "%s albedo %.2f in %s" % (role, lum(a), lim["albedo"]))
        if r.get("edge_wear"):
            check(inside(r["bevel_mm"], limits["edge_wear_mm"]), "%s worn edge %d mm in %s" % (role, r["bevel_mm"], limits["edge_wear_mm"]))
    lo, hi = limits["hand_band_m"]
    check(0.0 < lo < hi <= 2.3, "hand band %.1f-%.1f m inside the corridor's 2.3 m" % (lo, hi))
    for maker, m in makers.items():
        pal = m["palette"]
        for role, r in roles(data).items():
            if "colour" in r:
                c = pal.get(r["colour"])
                check(c is not None and len(c) == 3 and all(0.0 <= x <= 1.0 for x in c),
                      "%s palette has %s for %s" % (maker, r["colour"], role))
        for key in ("signal", "bare_metal", "dirt"):
            check(key in pal, "%s palette has %s" % (maker, key))
        if "tread" in pal and "graphite" in pal:
            ratio = lum(pal["tread"]) / max(lum(pal["graphite"]), 1e-6)
            check(ratio <= limits["lane_contrast_max"], "%s lanes %.2fx the graphite field <= %.2f" % (maker, ratio, limits["lane_contrast_max"]))
        w = m["wear"]
        for key in ("cavity_dirt", "edge_wear", "edge_threshold", "walked"):
            check(0.0 <= w[key] <= 1.0, "%s wear %s %.2f in 0..1" % (maker, key, w[key]))
        check(0.0 < w["walk_half_width_m"] <= 0.4, "%s walked line half width %.2f m <= 0.4 (a line, not the floor)" % (
            maker, w["walk_half_width_m"]))
        check(w["walk_roughness"] < data["roles"]["Kit_AntiSlip"]["roughness"],
              "%s walked line polished (%.2f under the lanes' %.2f)" % (maker, w["walk_roughness"], data["roles"]["Kit_AntiSlip"]["roughness"]))
    for role, e in data.get("emissive", {}).items():
        if role.startswith("_"):
            continue
        check(all(0.0 <= x <= 1.0 for x in e["colour"]) and e["strength"] > 0, "%s emissive colour and strength" % role)
    print("KITMAT SUMMARY %s (%d failures)" % ("PASS" if not fails else "FAIL", fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
