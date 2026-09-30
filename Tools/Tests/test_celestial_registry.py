"""Headless checks for the body registry (USpaceCelestialRegistrySubsystem, audit v1, 30. 9. 2026).

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_celestial_registry.py

TestSpace's terrain planet and backdrop bodies are all in the world's registry; a body spawned in the editor world
(as the other tests do) joins it and leaves it again when destroyed; the radar and the nearest body still see what a
walk of the world would. Nothing is saved. Prints "REGTEST PASS" / "REGTEST FAIL" lines and a summary.
"""

import unreal

failures = []


def log(msg):
    unreal.log("REGTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def zero_rotator():
    return unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)


unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSpace")
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
registry = unreal.SpaceCelestialRegistrySubsystem


def registered(distant):
    return registry.debug_count_registered_bodies(world, distant)


actors = eas.get_all_level_actors()
celestial = [a for a in actors if isinstance(a, unreal.CelestialBody)]
distant = [a for a in actors if isinstance(a, unreal.DistantBody)]
check("TestSpace has a terrain planet and backdrop bodies", len(celestial) >= 1 and len(distant) >= 1,
      "%d terrain, %d backdrop" % (len(celestial), len(distant)))
check("the editor world has a registry", registered(False) >= 0, str(registered(False)))
check("every terrain body of the level is registered", registered(False) == len(celestial),
      "%d registered, %d in the level" % (registered(False), len(celestial)))
check("every backdrop body of the level is registered", registered(True) == len(distant),
      "%d registered, %d in the level" % (registered(True), len(distant)))

# Spawned and destroyed in the editor world, as the radar and quantum tests do.
moon = eas.spawn_actor_from_class(unreal.DistantBody, unreal.Vector(0.0, -100000000.0, 0.0), zero_rotator())
check("a spawned backdrop body joins the registry", registered(True) == len(distant) + 1, str(registered(True)))
eas.destroy_actor(moon)
check("and leaves it when destroyed", registered(True) == len(distant), str(registered(True)))

rock = eas.spawn_actor_from_class(unreal.CelestialBody, unreal.Vector(0.0, 0.0, 500000000.0), zero_rotator())
check("a spawned terrain body joins the registry", registered(False) == len(celestial) + 1, str(registered(False)))
eas.destroy_actor(rock)
check("and leaves it when destroyed", registered(False) == len(celestial), str(registered(False)))

# The radar reads its bodies from the registry: one body contact per registered body that is not hidden.
ship = eas.spawn_actor_from_class(unreal.SpaceshipPawn, unreal.Vector(0.0, 0.0, 30000000.0), zero_rotator())
try:
    contacts = unreal.SpaceCockpitDisplays.make_radar_contacts(ship, 5000.0)
    bodies = [c for c in contacts if c.get_editor_property("body")]
    visible = [a for a in celestial + distant if not a.get_editor_property("hidden")]
    check("the radar lists every visible body of the level", len(bodies) == len(visible),
          "%d on the radar, %d visible" % (len(bodies), len(visible)))
finally:
    eas.destroy_actor(ship)

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
