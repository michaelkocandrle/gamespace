"""Checks the Steadfast interior as Tools/Assets/import_interior.py leaves it, in a fresh editor process.

    .\\Tools\\run_editor_python.ps1 Tools\\Tests\\test_interior.py

Prints "INTERIORTEST PASS" / "INTERIORTEST FAIL" lines and a summary. Never saves.

What it guards:
- the traps that turned the cooked bay into a grey checkerboard (Docs/WORKFLOW.md 9.3 f): the Nanite
  usage flag on M_KitTrim and a default texture in every sampler;
- the knobs space.Kit tunes are material parameters, with the defaults the script names;
- the tags the console commands find the interior by (Source/gamespace/SpaceInteriorTuning.cpp).
"""

import ast
import json
import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "Tools", "Assets", "import_interior.py")
LIGHTS = os.path.join(REPO, "ArtSource", "Ships", "Steadfast", "Interior", "Interior_lights.json")
WANTED = ("MATERIAL", "MAP", "GUNMETAL", "LIFT", "METALLIC_SCALE", "ROUGHNESS_SCALE", "ROUGHNESS_FLOOR",
          "INTERIOR_TAG", "WORK_LIGHT_TAG", "ACCENT_LIGHT_TAG", "WORK_LIGHT_LUMENS", "WORK_LIGHT_KELVIN", "WORK_LIGHT_CONE", "ACCENT_LIGHT_LUMENS", "PACKAGE", "ROOMS")

failures = []


def log(msg):
    unreal.log("INTERIORTEST " + msg)


def check(name, ok, detail=""):
    log(("PASS " if ok else "FAIL ") + name + ("  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def constants():
    """The constants out of import_interior.py, without running the import."""
    tree = ast.parse(open(SCRIPT, encoding="utf-8").read(), SCRIPT)
    body = [n for n in tree.body if isinstance(n, ast.Assign)
            and any(getattr(t, "id", None) in WANTED + ("PACKAGE",) for t in n.targets)]
    namespace = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), SCRIPT, "exec"), namespace)
    return namespace


C = constants()
MEL = unreal.MaterialEditingLibrary
material = unreal.EditorAssetLibrary.load_asset(C["MATERIAL"])
check("M_KitTrim exists", material is not None)
if material:
    for usage in ("used_with_nanite", "used_with_static_mesh", "used_with_instanced_static_meshes"):
        check("M_KitTrim %s" % usage, material.get_editor_property(usage))
    scalars = {str(n): MEL.get_material_default_scalar_parameter_value(material, n)
               for n in MEL.get_scalar_parameter_names(material)}
    for name, key in (("Lift", "LIFT"), ("MetallicScale", "METALLIC_SCALE"),
                      ("RoughnessScale", "ROUGHNESS_SCALE"), ("RoughnessFloor", "ROUGHNESS_FLOOR")):
        check("parameter %s = %s" % (name, C[key]), name in scalars and abs(scalars[name] - C[key]) < 1e-4,
              str(scalars.get(name)))
    colour = MEL.get_material_default_vector_parameter_value(material, "Gunmetal")
    check("parameter Gunmetal = %s" % (C["GUNMETAL"],),
          all(abs(a - b) < 1e-4 for a, b in zip((colour.r, colour.g, colour.b), C["GUNMETAL"])))
    for name in MEL.get_texture_parameter_names(material):
        check("sampler %s has a default texture" % name,
              MEL.get_material_default_texture_parameter_value(material, name) is not None)

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(C["MAP"])
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def tagged(tag):
    return [a for a in actors if unreal.Name(tag) in list(a.tags)]


layout = json.load(open(LIGHTS, encoding="utf-8"))
interior = tagged(C["INTERIOR_TAG"])
check("one tagged mesh actor per room %s" % (C["ROOMS"],), len(interior) == len(C["ROOMS"]),
      ", ".join(a.static_mesh_component.static_mesh.get_name() for a in interior))
for actor in interior:
    mesh = actor.static_mesh_component.static_mesh
    slots = [s.material_interface for s in mesh.static_materials] if mesh else []
    check("every slot wears an M_KitTrim instance",
          bool(slots) and all(s and s.get_base_material() == material for s in slots),
          ", ".join(s.get_name() if s else "None" for s in slots))
work = tagged(C["WORK_LIGHT_TAG"])
wanted_work = sum(len(layout[room]["work"]) for room in C["ROOMS"])
wanted_accent = sum(len(layout[room]["accent"]) for room in C["ROOMS"])
check("a work light under every fixture (%d)" % wanted_work, len(work) == wanted_work, "%d" % len(work))
for light in work:
    component = light.get_component_by_class(unreal.SpotLightComponent)
    if not component:
        check("%s is a spot light" % light.get_actor_label(), False)
        continue
    down = light.get_actor_forward_vector()
    check("%s points down, cone %s" % (light.get_actor_label(), C["WORK_LIGHT_CONE"]),
          down.z < -0.99 and abs(component.outer_cone_angle - C["WORK_LIGHT_CONE"][1]) < 0.01,
          "forward %s, outer %.1f" % (down, component.outer_cone_angle))
    check("%s: %s lm, %s K" % (light.get_actor_label(), C["WORK_LIGHT_LUMENS"], C["WORK_LIGHT_KELVIN"]),
          abs(component.intensity - C["WORK_LIGHT_LUMENS"]) < 0.5 and component.use_temperature
          and abs(component.temperature - C["WORK_LIGHT_KELVIN"]) < 0.5,
          "%.0f lm, %s, %.0f K" % (component.intensity, component.use_temperature, component.temperature))
lamp = unreal.EditorAssetLibrary.load_asset(C["PACKAGE"] + "/MI_KitLamp")
check("ceiling fixtures in every room wear MI_KitLamp (cold, not the kit's orange)",
      lamp is not None and bool(interior) and all(
          any(actor.static_mesh_component.static_mesh.get_material(i) == lamp
              for i in range(len(actor.static_mesh_component.static_mesh.static_materials)))
          for actor in interior))
check("every accent light (%d)" % wanted_accent, len(tagged(C["ACCENT_LIGHT_TAG"])) == wanted_accent,
      "%d" % len(tagged(C["ACCENT_LIGHT_TAG"])))
for light in tagged(C["ACCENT_LIGHT_TAG"]):
    component = light.point_light_component
    check("%s: %s lm" % (light.get_actor_label(), C["ACCENT_LIGHT_LUMENS"]),
          abs(component.intensity - C["ACCENT_LIGHT_LUMENS"]) < 0.5, "%.0f" % component.intensity)

log("SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
