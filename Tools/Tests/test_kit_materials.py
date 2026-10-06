"""The kit's shared material base against the workflow's limits (parts factory, FACTORY_WORKFLOW v0.1 step 3, 6. 10. 2026).

    python Tools/Tests/test_kit_materials.py

The simplest version (workflow v0.1: tools in a pilot only as simple as works), offline, on
ArtSource/Kit/kit_materials.json:
1. every role's roughness and metallic inside its limits (lacquer metallic <= 0.1, the lip polished metal 0.2-0.3, the
   dark rubber / graphite 0.6-0.7, the anti-slip floor);
2. every maker's palette has every colour a role names, linear 0..1;
3. the maker's wear stays a style, not an overall wear: amounts 0..1, the walked line narrower than a walkway;
4. the edge wear width (the bevel of a worn role) inside edge_wear_mm, the hand band inside the corridor's height.
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


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    limits, roles, makers = data["limits"], data["roles"], data["makers"]
    for role, r in roles.items():
        if role.startswith("_"):
            continue
        lim = limits.get(role)
        check(lim is not None, "%s has limits" % role)
        if lim:
            check(inside(r["roughness"], lim["roughness"]), "%s roughness %.2f in %s" % (role, r["roughness"], lim["roughness"]))
            check(inside(r["metallic"], lim["metallic"]), "%s metallic %.2f in %s" % (role, r["metallic"], lim["metallic"]))
        if r.get("edge_wear"):
            check(inside(r["bevel_mm"], limits["edge_wear_mm"]), "%s worn edge %d mm in %s" % (role, r["bevel_mm"], limits["edge_wear_mm"]))
    lo, hi = limits["hand_band_m"]
    check(0.0 < lo < hi <= 2.3, "hand band %.1f-%.1f m inside the corridor's 2.3 m" % (lo, hi))
    for maker, m in makers.items():
        if maker.startswith("_"):
            continue
        pal = m["palette"]
        for role, r in roles.items():
            if role.startswith("_"):
                continue
            c = pal.get(r["colour"])
            check(c is not None and len(c) == 3 and all(0.0 <= x <= 1.0 for x in c),
                  "%s palette has %s for %s" % (maker, r["colour"], role))
        for key in ("signal", "bare_metal", "dirt"):
            check(key in pal, "%s palette has %s" % (maker, key))
        w = m["wear"]
        for key in ("cavity_dirt", "edge_wear", "walked", "grunge"):
            check(0.0 <= w[key] <= 1.0, "%s wear %s %.2f in 0..1" % (maker, key, w[key]))
        check(0.0 < w["walk_half_width_m"] <= 0.4, "%s walked line half width %.2f m <= 0.4 (a line, not the floor)" % (
            maker, w["walk_half_width_m"]))
    print("KITMAT SUMMARY %s (%d failures)" % ("PASS" if not fails else "FAIL", fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
