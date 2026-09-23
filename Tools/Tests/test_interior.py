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
LAYOUT = os.path.join(REPO, "ArtSource", "Ships", "Steadfast", "Interior", "Interior_layout.json")
WANTED = ("MATERIAL", "MAP", "GUNMETAL", "LIFT", "METALLIC_SCALE", "ROUGHNESS_SCALE", "ROUGHNESS_FLOOR",
          "INTERIOR_TAG", "WORK_LIGHT_TAG", "ACCENT_LIGHT_TAG", "WORK_LIGHT_LUMENS", "WORK_LIGHT_KELVIN", "WORK_LIGHT_CONE", "ACCENT_LIGHT_LUMENS", "PACKAGE", "ROOMS",
          "GLASS", "DOOR_LEAF", "GLASS_TAG", "DOOR_TAG", "SPAWN_TAG", "GRAVITY_CMS2", "GLASS_MATERIAL", "PLACE_AT", "WORK_LIGHT_RADIUS",
          "SCREENS", "SCREENS_TAG", "HOLO_MATERIAL")

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
    namespace = {"unreal": unreal}
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


layout = json.load(open(LAYOUT, encoding="utf-8"))
rooms = layout["rooms"]
interior = tagged(C["INTERIOR_TAG"])
check("one tagged mesh actor per room %s" % (C["ROOMS"],), len(interior) == len(C["ROOMS"]),
      ", ".join(a.static_mesh_component.static_mesh.get_name() for a in interior))
for actor in interior:
    mesh = actor.static_mesh_component.static_mesh
    slots = [s.material_interface for s in mesh.static_materials] if mesh else []
    # Seats wear the leather material (HANDOFF point 67); everything else is the kit trim.
    check("%s: every slot wears an M_KitTrim instance (or the seats' leather)" % mesh.get_name(),
          bool(slots) and all(s and (s.get_base_material() == material or s.get_name() == "M_KitLeather") for s in slots),
          ", ".join(s.get_name() if s else "None" for s in slots))
    # Walkable: the character collides with the polygons, not a box round the room.
    body = mesh.get_editor_property("body_setup")
    check("%s collides per polygon" % mesh.get_name(),
          body is not None and body.get_editor_property("collision_trace_flag") == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
work = tagged(C["WORK_LIGHT_TAG"])
wanted_work = sum(len(rooms[room]["work"]) for room in C["ROOMS"])
wanted_accent = sum(len(rooms[room]["accent"]) + len(rooms[room].get("screen", [])) for room in C["ROOMS"])
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
    # Fills cast no shadows: 22 shadowed local lights were most of the frame (HANDOFF point 63).
    check("%s: %s lm, no shadows" % (light.get_actor_label(), C["ACCENT_LIGHT_LUMENS"]),
          abs(component.intensity - C["ACCENT_LIGHT_LUMENS"]) < 0.5 and not component.cast_shadows,
          "%.0f lm, shadows %s" % (component.intensity, component.cast_shadows))
for light in work:
    component = light.get_component_by_class(unreal.SpotLightComponent)
    if component:
        check("%s: reach %.0f cm" % (light.get_actor_label(), C["WORK_LIGHT_RADIUS"]),
              abs(component.attenuation_radius - C["WORK_LIGHT_RADIUS"]) < 0.5, "%.0f" % component.attenuation_radius)


# The walk: glass that stops the player, a door that opens, gravity round all of it, a start.
glass = tagged(C["GLASS_TAG"])
check("cockpit glass: one actor, translucent two-sided material, not Nanite, collides",
      len(glass) == 1 and glass[0].static_mesh_component.static_mesh.get_material(0).get_path_name().split(".")[0] == C["GLASS_MATERIAL"]
      and not glass[0].static_mesh_component.static_mesh.get_editor_property("nanite_settings").enabled
      and glass[0].static_mesh_component.static_mesh.get_editor_property("body_setup").get_editor_property("collision_trace_flag")
      == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
glass_material = unreal.EditorAssetLibrary.load_asset(C["GLASS_MATERIAL"])
check("M_KitGlass translucent and two-sided", glass_material is not None
      and glass_material.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_TRANSLUCENT
      and glass_material.get_editor_property("two_sided"))
# The cockpit's holograms: their own actor, not Nanite, no collision, additive, a picture on each.
screens = tagged(C["SCREENS_TAG"])
holo = unreal.EditorAssetLibrary.load_asset(C["HOLO_MATERIAL"])
check("hologram master additive, unlit, two-sided", holo is not None
      and holo.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_ADDITIVE
      and holo.get_editor_property("shading_model") == unreal.MaterialShadingModel.MSM_UNLIT
      and holo.get_editor_property("two_sided"))
if screens:
    screen_mesh = screens[0].static_mesh_component.static_mesh
    pictures = [MEL.get_material_instance_texture_parameter_value(screen_mesh.get_material(i), "Page")
                for i in range(len(screen_mesh.static_materials))]
    check("cockpit screens: one actor, not Nanite, no collision, a hologram page on every slot",
          len(screens) == 1 and not screen_mesh.get_editor_property("nanite_settings").enabled
          and screens[0].static_mesh_component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
          and all(p is not None and p.get_name().startswith("Holo_") for p in pictures),
          "nanite %s, collision %s, %s" % (screen_mesh.get_editor_property("nanite_settings").enabled,
                                           screens[0].static_mesh_component.get_collision_enabled(),
                                           ", ".join(p.get_name() if p else "None" for p in pictures)))
else:
    check("cockpit screens actor", False)
doors = tagged(C["DOOR_TAG"])
check("a sliding door per layout door (%d)" % len(layout["doors"]), len(doors) == len(layout["doors"]))
for door in doors:
    a, b = door.get_editor_property("leaf_a"), door.get_editor_property("leaf_b")
    leaf = a.static_mesh
    check("%s: both leaves wear the leaf mesh and block" % door.get_actor_label(),
          leaf is not None and leaf.get_name() == C["DOOR_LEAF"] and b.static_mesh == leaf
          and str(a.get_collision_profile_name()) == "BlockAll", "%s, %s" % (leaf and leaf.get_path_name(), a.get_collision_profile_name()))
    spread = abs(a.get_editor_property("relative_location").y - b.get_editor_property("relative_location").y)
    width = leaf.get_bounding_box().max.y - leaf.get_bounding_box().min.y if leaf else 0.0
    check("%s: closed, the leaves meet in the middle" % door.get_actor_label(), abs(spread - width) < 2.0,
          "spread %.1f, leaf %.1f cm" % (spread, width))
gravity = [a for a in actors if isinstance(a, unreal.SpaceGravityVolume)]
check("one gravity volume, %s cm/s2" % C["GRAVITY_CMS2"], len(gravity) == 1
      and abs(gravity[0].get_editor_property("gravity_cm_s2") - C["GRAVITY_CMS2"]) < 0.5)
spawn = tagged(C["SPAWN_TAG"])
check("one start of the walk", len(spawn) == 1)
if gravity and spawn:
    check("the start and every room's lights lie inside the gravity volume",
          gravity[0].contains_point(spawn[0].get_actor_location())
          and all(gravity[0].contains_point(l.get_actor_location()) for l in work))

log("SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
