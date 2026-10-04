"""Headless checks for SC-style interaction (step 1 after the author's captures, 4. 10. 2026).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_interaction.py

Covers what can be checked without a running game (the F tap / hold and the cursor live in the player controller and
are checked in the interaction shots, Tools/Shots/interaction.json):
  1. the key list in the pilot seat: interact mode, flight keys while flying, take-off when landed, the interact-mode
     list (use / back / close);
  2. hotspots: the ship under test's two MFDs (Display_left / Display_right sockets), none on a ship without them;
  3. notifications: toasts and hint cards are kept, counted and can be pushed; a hint shows once per run;
  4. the settings: Rozhraní - tipy defaults to on; the overlay's font and the shot list exist.
Prints "INTTEST PASS" / "INTTEST FAIL" lines and a summary.
"""

import json
import os
import sys

import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ship_under_test as sut  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
failures = []


def log(msg):
    unreal.log("INTTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def describe(pawn, interact=False):
    lines = [line.split("|") for line in unreal.SpaceControlsLibrary.describe_interaction(pawn, interact)]
    return ([l[1] for l in lines if l[0] == "hotspot"], [(l[1], l[2]) for l in lines if l[0] == "key"],
            [l[1:] for l in lines if l[0] == "target"])


eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/Maps/TestSpace")  # new_level logs an error (exit 1) when /Temp already holds the level

# 1) key list in the seat (a native ship: no sockets, not landed)
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 500000.0), unreal.Rotator())
try:
    hotspots, keys, targets = describe(ship)
    actions = [a for a, k in keys]
    check("seated: the key list offers interact mode on a held F", ("INTERAKCE (DRŽET)", "F") in keys, str(keys))
    check("flying: gear, SCM / NAV, coupled and the brake are listed",
          any("PODVOZEK" in a for a in actions) and "SCM / NAV" in actions and "COUPLED / DECOUPLED" in actions and "VESMÍRNÁ BRZDA" in actions,
          str(actions))
    check("no tap target in the seat (SC puts the seated actions on the list)", not targets, str(targets))
    check("a ship without display sockets has no hotspots", not hotspots, str(hotspots))
    ship.debug_set_gear_instant(True)
    ship.debug_force_landed(True)
    _, keys, _ = describe(ship)
    check("landed: take-off on Space, no flight keys", ("VZLET", "Space") in keys and not any(a == "SCM / NAV" for a, k in keys), str(keys))
    ship.debug_force_landed(False)
    _, keys, _ = describe(ship, True)
    check("interact mode: use, back and close", [a for a, k in keys] == ["POUŽÍT", "ZPĚT (MFD)", "ZAVŘÍT INTERAKCI (PUSTIT)"], str(keys))
finally:
    eas.destroy_actor(ship)

# 2) the ship under test's MFDs as hotspots
if sut.name():
    bp = eas.spawn_actor_from_class(sut.bp_class(), unreal.Vector(0.0, 0.0, 500000.0), unreal.Rotator())
    try:
        hotspots, _, _ = describe(bp)
        check("%s: both MFDs are hotspots" % sut.name(), sum(1 for h in hotspots if "MFD" in h) == 2, str(hotspots))
    finally:
        eas.destroy_actor(bp)
else:
    log("SKIP ship under test (none)")

# 3) notifications
# a game instance subsystem needs a game instance as its outer (none runs in the editor)
notes = unreal.new_object(unreal.SpaceNotifications, outer=unreal.new_object(unreal.GameInstance))
notes.debug_toast("Jsi na palubě lodi TEST")
notes.debug_toast("Druhé hlášení")
check("toasts are kept and counted", notes.debug_count_toasts() == 2, str(notes.debug_count_toasts()))
notes.debug_hint("Interakce", "Krátké F použije věc s popiskem.")
check("a hint card is kept", notes.debug_count_hints() == 1)
for _ in range(5):
    notes.debug_toast("x")
check("at most three toasts at once", notes.debug_count_toasts() <= 3, str(notes.debug_count_toasts()))

# 4) settings, assets, shots
check("Rozhraní - tipy defaults to on", unreal.get_default_object(unreal.SpaceUserSettings).get_editor_property("show_hints"))
check("the overlay's font is in the project", os.path.isfile(os.path.join(REPO, "Content", "UI", "Fonts", "Oxanium-Medium.ttf")))
shots = json.load(open(os.path.join(REPO, "Tools", "Shots", "interaction.json"), encoding="utf-8"))["shots"]
check("interaction shots use space.InteractMode and space.Notify",
      any("space.InteractMode" in c for s in shots for c in s.get("console", []))
      and any("space.Notify" in c for s in shots for c in s.get("console", [])))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
