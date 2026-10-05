"""Headless checks for the ship's power (SC's cold start, step 2a after the author's captures, 4. 10. 2026).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_ship_power.py

  1. power off: the keys move nothing (no thrust, the thrusters' acceleration is zero);
  2. power on: the start-up takes PowerBootSeconds, still without thrust, then the ship flies; instant power on;
  3. the key list: NAPÁJENÍ (ZAP/VYP) U first, no flight keys without power;
  4. the ship under test: the PWR selector next to the left MFD as a hotspot (ZAPNOUT / VYPNOUT NAPÁJENÍ), the MFDs
     only clickable with power;
  5. the controls table (KLÁVESY) has U, the shot list exists.
The displays' dark glass and start-up screens, the HUD and the lights are checked in the ship_power shots.
Prints "PWRTEST PASS" / "PWRTEST FAIL" lines and a summary.
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
    unreal.log("PWRTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def speed(v):
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def fly(ship, seconds, thrust=1.0):
    ship.debug_set_linear_velocity(unreal.Vector(0.0, 0.0, 0.0))
    v = unreal.Vector(0.0, 0.0, 0.0)
    for _ in range(int(round(seconds / STEP))):
        v = ship.debug_step_flight_input(STEP, unreal.Vector(thrust, 0.0, 0.0), unreal.Vector(0.0, 0.0, 0.0), False)
    return v


def describe(pawn):
    lines = [line.split("|") for line in unreal.SpaceControlsLibrary.describe_interaction(pawn, False)]
    return [l[1] for l in lines if l[0] == "hotspot"], [(l[1], l[2]) for l in lines if l[0] == "key"]


eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSpace")
FAR = unreal.Vector(0.0, 0.0, 9.0e8)   # deep space, away from the planets' gravity

ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, FAR, unreal.Rotator())
try:
    check("a ship starts powered (bStartPowered)", ship.is_powered() and ship.get_editor_property("start_powered"))
    flying = speed(fly(ship, 1.0))
    check("powered: W accelerates", flying > 100.0, "%.0f cm/s after 1 s" % flying)

    # 1) off
    check("power off is accepted", ship.set_power(False, False))
    check("off: state Off, start-up 0", ship.get_power_state() == unreal.SpacePowerState.OFF and ship.get_power_boot_alpha() == 0.0)
    drift = speed(fly(ship, 1.0))
    acc = ship.debug_get_thruster_acceleration()
    check("off: W moves nothing", drift < 1.0 and speed(acc) == 0.0, "%.2f cm/s, thrust %.1f" % (drift, speed(acc)))
    _, keys = describe(ship)
    actions = [a for a, k in keys]
    check("off: the key list starts with NAPÁJENÍ (ZAP/VYP) U", keys and keys[0] == ("NAPÁJENÍ (ZAP/VYP)", "U"), str(keys))
    check("off: no flight keys", "SCM / NAV" not in actions and "VZLET" not in actions, str(actions))

    # 2) the start-up
    boot = ship.get_editor_property("power_boot_seconds")
    check("power on is accepted", ship.set_power(True, False))
    check("on: the start-up runs", ship.get_power_state() == unreal.SpacePowerState.BOOTING and not ship.is_powered())
    ship.debug_step_power(boot * 0.4)
    alpha = ship.get_power_boot_alpha()
    check("the start-up's progress follows its clock", abs(alpha - 0.4) < 0.02, "%.3f" % alpha)
    check("starting up: still no thrust", speed(fly(ship, 0.25)) < 1.0)
    ship.debug_step_power(boot)
    check("after PowerBootSeconds the ship is on", ship.is_powered() and ship.get_power_boot_alpha() == 1.0)
    check("on again: W accelerates", speed(fly(ship, 1.0)) > 100.0)
    _, keys = describe(ship)
    check("on: flight keys on the list", ("SCM / NAV", "B") in keys and keys[0][1] == "U", str(keys))
    ship.set_power(False, False)
    ship.set_power(True, True)
    check("instant power on skips the start-up", ship.is_powered())
    check("a ship without the left MFD has no PWR selector", ship.get_power_control_location() is None)
finally:
    eas.destroy_actor(ship)

# 4) the ship under test: the PWR selector
if sut.name():
    bp = eas.spawn_actor_from_class(sut.bp_class(), FAR, unreal.Rotator())
    try:
        at = bp.get_power_control_location()
        check("%s: the PWR selector is found" % sut.name(), at is not None)
        if at is not None:
            local = bp.get_actor_transform().inverse_transform_location(at)
            check("the PWR selector is in the cockpit, left of the centreline", local.y < -30.0 and local.x > 0.0, str(local))
        bp.set_power(False, False)
        hotspots, _ = describe(bp)
        check("off: only the PWR selector is clickable (dark MFDs)", hotspots == ["ZAPNOUT NAPÁJENÍ"], str(hotspots))
        bp.set_power(True, True)
        hotspots, _ = describe(bp)
        check("on: the MFDs' page arrows and the PWR selector", len(hotspots) == 5 and hotspots[-1] == "VYPNOUT NAPÁJENÍ", str(hotspots))
    finally:
        eas.destroy_actor(bp)
else:
    log("SKIP ship under test (none)")

# 5) controls and shots
controls = unreal.SpaceControlsLibrary.describe_controls()
check("KLÁVESY lists U for the power", any(c.startswith("flight|U|0|") for c in controls))
shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "ship_power.json"), encoding="utf-8"))["shots"]
check("the ship_power shots switch the power", any("space.Power 1" in c for s in shots for c in s.get("console", [])))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
