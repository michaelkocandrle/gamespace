"""Headless checks for step 2b after the author's SC captures (4. 10. 2026): the MFD CONFIGURATION page and getting up
in flight.

    .\Tools\run_editor_python.ps1 Tools\Tests\test_mfd_config.py

  1. the left MFD has a fourth page, CONFIGURATION, with the ship's real flight switches; their switch points lie
     inside the display, top to bottom, at the right edge;
  2. interact mode: the MFD hotspots sit on the page tab; with CONFIGURATION up each switch is a hotspot labelled with
     what a click does (ZAPNOUT / VYPNOUT); unpowered none;
  3. getting up in flight: F brakes the ship to a hold (coupled), the key list says so, F again cancels.
Prints "CFGTEST PASS" / "CFGTEST FAIL" lines and a summary.
"""

import json
import math
import os
import sys

import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ship_under_test as sut  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STEP = 1.0 / 60.0
failures = []


def log(msg):
    unreal.log("CFGTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def describe(pawn):
    lines = [line.split("|") for line in unreal.SpaceControlsLibrary.describe_interaction(pawn, False)]
    return [l[1] for l in lines if l[0] == "hotspot"], [(l[1], l[2]) for l in lines if l[0] == "key"]


# 1) the page
uvs = [unreal.SpaceCockpitDisplays.config_switch_uv(i) for i in range(5)]
check("five switch points inside the display", all(0.5 < uv.x < 1.0 and 0.0 < uv.y < 0.9 for uv in uvs), str([(round(u.x, 2), round(u.y, 2)) for u in uvs]))
check("the switches run top to bottom", all(uvs[i].y < uvs[i + 1].y for i in range(4)))

if not sut.name():
    log("SKIP ship under test (none)")
else:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSpace")
    bp = eas.spawn_actor_from_class(sut.bp_class(), unreal.Vector(0.0, 0.0, 9.0e8), unreal.Rotator())
    try:
        # 2) hotspots
        bp.set_power(True, True)
        hotspots, _ = describe(bp)
        check("FLIGHT page: four MFD page arrows and PWR", len(hotspots) == 5, str(hotspots))
        bp.cycle_mfd_page(0, -1)
        check("one page back from FLIGHT is CONFIGURATION", bp.get_mfd_page(0) == 3, str(bp.get_mfd_page(0)))
        hotspots, _ = describe(bp)
        config = hotspots[5:]
        check("CONFIGURATION: one hotspot per switch", len(config) == 5, str(hotspots))
        check("a switch says what a click does", config and config[0] == "COUPLED MODE: VYPNOUT", str(config[:1]))
        bp.set_flight_assist(False)
        hotspots, _ = describe(bp)
        check("...and follows the ship", "COUPLED MODE: ZAPNOUT" in hotspots, str(hotspots))
        bp.set_flight_assist(True)
        bp.set_power(False, False)
        hotspots, _ = describe(bp)
        check("unpowered: no switches", not any(":" in h for h in hotspots), str(hotspots))
        bp.set_power(True, True)
        bp.cycle_mfd_page(0, 1)

        # 3) getting up in flight
        bp.set_flight_assist(False)
        bp.debug_set_linear_velocity(unreal.Vector(3000.0, 0.0, 0.0))
        _, keys = describe(bp)
        check("flying: F gets up with the ship stopping", ("VSTÁT (LOĎ ZASTAVÍ)", "F") in keys, str(keys))
        check("F in flight starts the hold", bp.request_leave_seat_in_flight() and bp.is_leave_seat_pending())
        check("the hold flies coupled", bp.is_flight_assist_on())
        _, keys = describe(bp)
        check("braking: F stays seated", ("ZŮSTAT SEDĚT (LOĎ BRZDÍ)", "F") in keys, str(keys))
        for _ in range(int(8.0 / STEP)):
            v = bp.debug_step_flight_input(STEP, unreal.Vector(1.0, 0.0, 0.0), unreal.Vector(0.0, 0.0, 0.0), False)
        speed = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        check("the ship brakes to a hold despite W", speed < 100.0, "%.0f cm/s" % speed)
        bp.interact()
        check("F again cancels", not bp.is_leave_seat_pending())
    finally:
        eas.destroy_actor(bp)

shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "mfd_config.json"), encoding="utf-8"))["shots"]
check("the mfd_config shots open CONFIGURATION", any("space.MfdPage 3" in c for s in shots for c in s.get("console", [])))
log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
