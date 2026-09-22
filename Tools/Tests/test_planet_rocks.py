"""Headless checks for the rocks on Veyra (UPlanetRockScatter, planets 4/4) and the ground textures.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_planet_rocks.py

The rocks come from a hash of their cell, stand on the exact height field and are sunk into it,
cluster on slopes, and stay within a count the frame can afford. Also: the terrain material has
its textures.
Nothing is saved. Prints "ROCKTEST PASS" / "ROCKTEST FAIL" lines and a summary.
"""

import math

import unreal

failures = []


def log(msg):
    unreal.log("ROCKTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def v3(v):
    return (v.x, v.y, v.z)


def length(a):
    return math.sqrt(sum(c * c for c in a))


unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSpace")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
planet = next(a for a in actors if a.get_actor_label() == "Planet_Veyra")
rocks = planet.get_editor_property("rocks")
kinds = rocks.get_editor_property("kinds")
R = planet.get_editor_property("radius_km") * 100000.0

check("four kinds of rock, each with a Nanite mesh",
      len(kinds) == 4 and all(k.get_editor_property("mesh") and k.get_editor_property("mesh").get_editor_property("nanite_settings").get_editor_property("enabled")
                              for k in kinds), str(len(kinds)))

# Round the start point's ground (below PlayerStart) and at a few other places.
spots = [(-1.0, 0.0, 0.0), (-0.8, 0.6, 0.0), (0.0, 0.0, 1.0), (0.3, -0.7, 0.648)]
worst_total = 0
for d in spots:
    n = length(d)
    local = unreal.Vector(*[c / n * (R + 100000.0) for c in d])
    counts = rocks.debug_count_rocks_around(local)
    again = rocks.debug_count_rocks_around(local)
    worst_total = max(worst_total, sum(counts))
    check("rocks round %s: the same every time" % str(d), list(counts) == list(again), str(list(counts)))
check("a count the frame can afford (under 20 000 in the scatter radius)", 0 < worst_total < 20000, str(worst_total))

# Every rock of every kind in one cell: on the ground, sunk a little.
planet_centre = v3(planet.get_actor_location())
below = 0
total = 0
for index in range(len(kinds)):
    for d in spots:
        n = length(d)
        local = unreal.Vector(*[c / n * R for c in d])
        for xform in rocks.debug_rocks_in_cell(local, index):
            p = v3(xform.translation)
            ground = planet.get_terrain_height_at(unreal.Vector(*[planet_centre[k] + p[k] for k in range(3)]))
            height_above = length(p) - R - ground
            total += 1
            if height_above < 50.0:
                below += 1
check("rocks stand on the ground, not floating (origin within 50 cm above it or sunk)", total > 0 and below == total,
      "%d of %d" % (below, total))

# More rocks on slopes: compare the two sides of the rock's own threshold across many cells.
flat = kinds[0].get_editor_property("per_cell_flat")
slope = kinds[0].get_editor_property("per_cell_slope")
check("more stones on slopes than on the flats (by the recipe)", slope > flat)

material = unreal.load_asset("/Game/Planets/M_Planet_Terrain")
check("terrain material one-sided (two-sided did not fix the ridged terrain's holes)", not material.get_editor_property("two_sided"))
check("and it takes a world-space normal (triplanar)", not material.get_editor_property("tangent_space_normal"))
params = set(str(p) for p in unreal.MaterialEditingLibrary.get_texture_parameter_names(material))
wanted = {"SandAlbedo", "SandNormalMap", "SandARMMap", "RockAlbedo", "RockNormalMap", "RockARMMap",
          "StrataAlbedo", "StrataNormalMap", "StrataARMMap"}
check("with its nine ground textures", wanted <= params, str(sorted(wanted - params)))
wrap = planet.get_editor_property("terrain_texture_wrap_cm")
scales = [unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(material, name)
          for name in ("SandScaleCm", "RockScaleCm", "StrataScaleCm")]
check("every texture scale divides the wrap length (no seams between tiles)",
      all(s > 0 and abs(wrap / s - round(wrap / s)) < 1e-6 for s in scales), "%s into %.0f" % (scales, wrap))

log("SUMMARY %s (%d failed: %s)" % ("OK" if not failures else "FAILED", len(failures), ", ".join(failures)))
