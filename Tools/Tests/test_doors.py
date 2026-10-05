"""Headless checks for the ship's sliding doors (author 5. 10. 2026: SC's doors open; hs_interior.build_door).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_doors.py

  1. the ship under test has its door leaves (components Door<n><A|B>) and the doorways are found;
  2. the game starts with every door shut: the leaf stands in its doorway;
  3. F opens it: the leaf slides aside over ~0.9 s (eased), by about its own width, and shuts again;
  4. a shut leaf blocks the walker while the interior is walked, an open one does not;
  5. an open door shuts by itself after a while with nobody in it;
  6. standing at a door, the prompt is OTEVŘÍT / ZAVŘÍT (SC's vertical label beside the F key).
Prints "DOORTEST PASS" / "DOORTEST FAIL" lines and a summary.
"""

import os
import sys

import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ship_under_test as sut  # noqa: E402

STEP = 1.0 / 60.0
failures = []


def log(msg):
    unreal.log("DOORTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5


def step(ship, seconds):
    for _ in range(int(round(seconds / STEP))):
        ship.debug_step_doors(STEP)


if not sut.name():
    log("SKIP " + sut.NO_SHIP)
else:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSpace")
    ship = eas.spawn_actor_from_class(sut.bp_class(), unreal.Vector(0.0, 0.0, 9.0e8), unreal.Rotator())
    try:
        leaves = {c.get_name(): c for c in ship.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith("Door")}
        check("the ship has door leaves", len(leaves) >= 2, ", ".join(sorted(leaves)))
        step(ship, STEP)
        count = ship.get_door_count()
        check("the doorways are found", count >= 2, "%d doors" % count)

        for door in range(count):
            at = ship.get_door_location(door)
            leaf = leaves.get("Door%dA" % door)
            if leaf is None:
                check("door %d has leaf A" % door, False)
                continue
            shut = leaf.get_world_location()
            lo, hi = leaf.get_local_bounds()
            centre = leaf.get_world_transform().transform_location((lo + hi) * 0.5)
            check("door %d starts shut, the leaf in the doorway" % door,
                  not ship.is_door_open(door) and abs(centre.y - at.y) < 70.0 and abs(centre.x - at.x) < 30.0,
                  "leaf %.0f %.0f, doorway %.0f %.0f" % (centre.x, centre.y, at.x, at.y))
            prompt = ship.get_door_prompt_location(door)
            off = ((prompt.x - at.x) ** 2 + (prompt.y - at.y) ** 2) ** 0.5
            check("door %d: the prompt by the closing edge (SC)" % door, 25.0 < off < 60.0 and abs(prompt.z - at.z) < 1.0, "%.0f cm from the centre" % off)
            check("door %d found from 1 m in front of it" % door, ship.find_door_near(at + unreal.Vector(100.0, 0.0, 0.0), 160.0) == door)

            ship.set_door_open(door, True)
            step(ship, 0.25)
            early = dist(leaf.get_world_location(), shut)
            step(ship, 0.2)
            half = ship.debug_get_door_open_alpha(door)
            step(ship, 0.6)
            moved = dist(leaf.get_world_location(), shut)
            check("door %d opens over ~0.9 s" % door, 0.35 < half < 0.65 and ship.debug_get_door_open_alpha(door) == 1.0,
                  "alpha %.2f at 0.45 s" % half)
            check("door %d eases (slower start than linear)" % door, 0.0 < early < moved * 0.24, "%.0f of %.0f cm after 0.25 s" % (early, moved))
            lo, hi = leaf.get_local_bounds()
            open_centre = leaf.get_world_transform().transform_location((lo + hi) * 0.5)
            check("door %d slides aside by about its width" % door, abs(moved - (abs(hi.y - lo.y) + 1.0)) < 3.0,
                  "%.0f cm, open centre %.0f %.0f %.0f, bounds y %.0f..%.0f" % (moved, open_centre.x, open_centre.y, open_centre.z, lo.y, hi.y))

            ship.set_interior_walk(True)
            col_open = leaf.get_collision_enabled()
            ship.set_door_open(door, False)
            step(ship, 1.0)
            col_shut = leaf.get_collision_enabled()
            check("door %d: shut blocks the walker, open does not" % door,
                  col_open == unreal.CollisionEnabled.NO_COLLISION and col_shut == unreal.CollisionEnabled.QUERY_ONLY
                  and leaf.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) == unreal.CollisionResponseType.ECR_BLOCK,
                  "%s / %s" % (col_open, col_shut))
            ship.set_interior_walk(False)
            check("door %d shuts back into the doorway" % door, dist(leaf.get_world_location(), shut) < 0.5)

        # the walker between two doors picks the one he looks at, not the nearer one behind him
        a, b = ship.get_door_location(0), ship.get_door_location(1)
        mid = a * 0.6 + b * 0.4
        check("between two doors, the one ahead is picked",
              ship.find_door_ahead(mid, a - b, 160.0) == 0 and ship.find_door_ahead(mid, b - a, 160.0) == 1)

        # 5) closes by itself (the editor has no walker standing in it)
        ship.set_door_open(0, True)
        step(ship, 1.0)
        check("an open door stays open a while", ship.is_door_open(0))
        import time
        time.sleep(6.2)
        step(ship, 1.0)
        check("with nobody in it, an open door shuts by itself after ~6 s", not ship.is_door_open(0) and ship.debug_get_door_open_alpha(0) == 0.0)

        # 6) the prompt
        src = open(os.path.join(sut.REPO, "Source", "gamespace", "SpaceInteraction.cpp"), encoding="utf-8").read()
        check("the walker's prompt at a door is OTEVŘÍT / ZAVŘÍT, vertical",
              '"OTEVŘÍT"' in src and '"ZAVŘÍT"' in src and "bVertical = true" in src)
    finally:
        eas.destroy_actor(ship)

log("SUMMARY %s (%d failed)" % ("PASS" if not failures else "FAIL", len(failures)))
