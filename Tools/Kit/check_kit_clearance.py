"""Clearance of the character in the kit's standard sections (step 2 of the kit brief, author 26. 9. 2026):

    python Tools/Kit/check_kit_clearance.py

1. The capsule (PlayerCharacter.cpp: radius 0.42 m, half height 0.96 m, hemispherical caps) against the wall
   profile at every height from the floor to the top of the head, between portals and inside a portal (the frame
   is proud of the faces by the section's portal_protrusion on walls, slope and ceiling). Reports the smallest
   side margin and where it is (the wall slopes in at shoulder and head height).
2. The third-person camera: spring arm 3.8 m, socket offset (0, 0.55, 0.65) m, probe sphere 0.12 m, collision on
   (PlayerCharacter.cpp). The arm is swept like USpringArmComponent does (origin -> desired socket, sphere probe),
   in the section's cross profile (corridor straight along +X), for view pitches -30..+30 deg looking down the
   corridor, and reports how far behind the character the camera ends up.
Prints CLEARANCE {...} (JSON) and exits 1 if any margin is below the rules' minimum.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))
CAPSULE_R, CAPSULE_HH = 0.42, 0.96
ARM, SOCKET_Y, SOCKET_Z, PROBE = 3.8, 0.55, 0.65, 0.12
PLINTH = RULES["zones"]["plinth_height"]


def wall_half_width(sec, width, z, portal):
    """Half the clear width at height z (0 at the floor), inside a portal when portal is True."""
    w2 = width / 2
    p = (sec.get("portal_protrusion") or 0.0) if portal else 0.0
    if z < PLINTH:
        # 45 deg plinth: the face steps in by (PLINTH - z) at the floor
        base = w2 - (PLINTH - z)
    elif z <= sec["vertical_to"]:
        base = w2
    else:
        base = w2 - 0.75 * min(z - sec["vertical_to"], sec["slope_rise"])
    return base - p


def ceiling(sec, portal):
    return sec["ceiling"] - ((sec.get("portal_protrusion") or 0.0) if portal else 0.0)


def capsule_half(z):
    lo, hi = CAPSULE_R, 2 * CAPSULE_HH - CAPSULE_R
    if z < 0 or z > 2 * CAPSULE_HH:
        return None
    if z < lo:
        return math.sqrt(max(0.0, CAPSULE_R ** 2 - (lo - z) ** 2))
    if z > hi:
        return math.sqrt(max(0.0, CAPSULE_R ** 2 - (z - hi) ** 2))
    return CAPSULE_R


def capsule_margin(sec, width, portal):
    worst = (1e9, 0.0)
    z = 0.0
    while z <= 2 * CAPSULE_HH - 1e-9:
        c = capsule_half(z)
        m = wall_half_width(sec, width, z, portal) - c
        if m < worst[0]:
            worst = (m, z)
        z += 0.01
    head = ceiling(sec, portal) - 2 * CAPSULE_HH
    return worst, head


def arm_camera(sec, width, pitch_deg):
    """Distance behind the character where the sphere-probed arm stops, and the camera's (y, z)."""
    pivot = (0.0, 0.0, CAPSULE_HH)                    # capsule centre, walking on the centreline
    pr = math.radians(pitch_deg)
    back = (-math.cos(pr) * ARM, 0.0, -math.sin(pr) * ARM)   # arm points back and, looking down (pitch < 0), up
    target = (pivot[0] + back[0], pivot[1] + SOCKET_Y, pivot[2] + back[2] + SOCKET_Z)
    steps = 400
    for k in range(1, steps + 1):
        t = k / steps
        y = pivot[1] + (target[1] - pivot[1]) * t
        z = pivot[2] + (target[2] - pivot[2]) * t
        # the probe sphere must stay inside the profile (checked at its centre height and its top / bottom)
        ok = True
        for dz in (-PROBE, 0.0, PROBE):
            zz = z + dz
            if zz <= 0.0 or zz >= ceiling(sec, True) - (PROBE if dz == 0.0 else 0.0):
                ok = False
                break
            if abs(y) + (PROBE if dz == 0.0 else math.sqrt(max(0.0, PROBE ** 2 - dz ** 2))) > wall_half_width(sec, width, zz, True):
                ok = False
                break
        if not ok:
            t = (k - 1) / steps
            break
    y = pivot[1] + (target[1] - pivot[1]) * t
    z = pivot[2] + (target[2] - pivot[2]) * t
    return round(-back[0] * t, 2), round(y, 2), round(z, 2)


def main():
    out, fail = {}, []
    widths = {"S": None, "N": None, "W": None, "T": 3.6}
    for key, sec in RULES["sections"].items():
        if key.startswith("_"):
            continue
        width = sec["width"] or widths[key]
        res = {}
        for portal in (False, True):
            (m, z), head = capsule_margin(sec, width, portal)
            res["portal" if portal else "between"] = {"side_margin_m": round(m, 3), "at_height_m": round(z, 2), "head_room_m": round(head, 3)}
            if m < 0.02 or head < RULES["collision"]["min_clear_height"] - 2 * CAPSULE_HH:
                fail.append("%s %s" % (key, "portal" if portal else "between"))
        res["camera_3p"] = {str(p): arm_camera(sec, width, p) for p in (-30, -15, 0, 15, 30)}
        out[key] = res
    print("CLEARANCE " + json.dumps(out, ensure_ascii=False))
    for key, res in out.items():
        print("%s  between: side %.3f m at %.2f m, head %.3f m | portal: side %.3f m at %.2f m, head %.3f m" % (
            key, res["between"]["side_margin_m"], res["between"]["at_height_m"], res["between"]["head_room_m"],
            res["portal"]["side_margin_m"], res["portal"]["at_height_m"], res["portal"]["head_room_m"]))
        print("   3P camera (pitch: metres behind, y, z): " + ", ".join("%s: %s" % (p, v) for p, v in res["camera_3p"].items()))
    if fail:
        print("CLEARANCE FAIL", fail)
        sys.exit(1)


if __name__ == "__main__":
    main()
