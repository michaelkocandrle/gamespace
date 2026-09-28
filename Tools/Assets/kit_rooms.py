"""Rooms of a ship built from the interior kit (kit brief step 7.1, 28. 9. 2026).

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\kit_rooms.py            (every ship whose recipe has kit rooms)

Reads the recipe block interior.kit_modules of ArtSource/Ships/<Ship>/HardSurface/<Ship>_hs.json - layout metres
(x forward, y to port, z from the deck), wall runs and run parts as import_kit.SHOWROOM - and puts the kit parts
(/Game/Kit/Meshes, import_kit.py) into /Game/Ships/<Ship>/Blueprints/BP_Ship_<Ship> as components under Hull:
  InteriorMod_NN_<part>      StaticMeshComponent, no collision (the ship's interior is not walkable yet)
  Light_fix_kit_NN           a light at every light socket of the part, as the showroom's (import_kit.place_part):
                             point, spot or rect, x KIT_LIGHT_SCALE. The prefix Light_fix_ makes the pawn switch
                             them with the fixture lights (on only with the camera inside, ASpaceshipPawn)
hs_interior builds nothing in these rooms but the bulkheads and the stand-ins (kit_modules.stand_in_floor).
Old InteriorMod_* / Light_fix_kit_* components go first, so every run rebuilds the rooms. Hull space is the game
blend's space in centimetres with Unreal's y mirrored: game = layout + assemble.offset (hs_assemble_ship).
Called by import_kit.py and import_ship.py after their own work; prints KITROOMS {...}.
"""
import ast
import json
import os
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "Tools", "Kit"))
import kit_layout  # noqa: E402   (the placement, shared with Blender's geometry check)

MESH_PREFIX, LIGHT_PREFIX = "InteriorMod_", "Light_fix_kit_"


def _import_kit_constants():
    """KIT_LIGHT_SCALE and LIGHT_COLOURS from import_kit.py, read without running it (it imports on load)."""
    tree = ast.parse(open(os.path.join(HERE, "import_kit.py"), encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("KIT_LIGHT_SCALE", "LIGHT_COLOURS"):
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out["KIT_LIGHT_SCALE"], out["LIGHT_COLOURS"]


KIT_LIGHT_SCALE, LIGHT_COLOURS = _import_kit_constants()
# the showroom's x2.0 makes up for the ray-traced shadows it lights with; unshadowed in a ship (see _light) the same
# lights took the Wayfarer's corridor to a mean of 0.32 (SC 0.13-0.23): x1.1 there (28. 9. 2026)
SHIP_LIGHT_SCALE = 1.1


def recipes():
    """(ship, recipe) for every ship whose hard-surface recipe has interior.kit_modules."""
    root = os.path.join(REPO, "ArtSource", "Ships")
    for ship in sorted(os.listdir(root)):
        path = os.path.join(root, ship, "HardSurface", "%s_hs.json" % ship)
        if os.path.exists(path):
            recipe = json.load(open(path, encoding="utf-8"))
            if (recipe.get("interior") or {}).get("kit_modules"):
                yield ship, recipe


class Components:
    """Adds components under Hull to one Blueprint (the SubobjectDataSubsystem, as import_ship does)."""

    def __init__(self, blueprint):
        self.bp = blueprint
        self.sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        self.lib = unreal.SubobjectDataBlueprintFunctionLibrary

    def _handles(self):
        return self.sub.k2_gather_subobject_data_for_blueprint(self.bp)

    def _name(self, handle):
        obj = self.lib.get_object(self.lib.get_data(handle))
        return (obj.get_name().replace("_GEN_VARIABLE", ""), obj) if obj is not None else (None, None)

    def remove_old(self):
        handles = self._handles()
        old = [h for h in handles if (self._name(h)[0] or "").startswith((MESH_PREFIX, LIGHT_PREFIX))]
        if old:
            self.sub.delete_subobjects(handles[0], old, self.bp)
        return len(old)

    def add(self, cls, name):
        handles = self._handles()
        parent = next((h for h in handles if self._name(h)[0] == "Hull"), handles[0])
        params = unreal.AddNewSubobjectParams()   # struct constructors take no keyword arguments
        params.set_editor_property("parent_handle", parent)
        params.set_editor_property("new_class", cls)
        params.set_editor_property("blueprint_context", self.bp)
        handle, fail = self.sub.add_new_subobject(params)
        if not self.lib.is_handle_valid(handle):
            raise RuntimeError("%s: %s" % (name, fail))
        self.sub.rename_subobject(handle, unreal.Text(name))
        return self.lib.get_object(self.lib.get_data(handle))


def _light(c, role, cd, radius_m, source_cm, spot_cone=None):
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", float(cd) * SHIP_LIGHT_SCALE)
    c.set_editor_property("attenuation_radius", float(radius_m) * 100.0)
    # no shadows, as the ship's other fixture lights (hs_fixture_lights): the ship is flown without MegaLights, and
    # 11 shadowed lights took the Wayfarer's interior views from 18 to 27-42 ms GPU (1676 draws instead of 673,
    # 28. 9. 2026); the showroom's lights keep theirs (walked, MegaLights on)
    c.set_editor_property("cast_shadows", False)
    col = LIGHT_COLOURS[role]
    c.set_editor_property("light_color", unreal.Color(r=col[0], g=col[1], b=col[2], a=255))
    if source_cm is not None:
        c.set_editor_property("source_radius", float(source_cm))
    if spot_cone is not None:
        c.set_editor_property("outer_cone_angle", spot_cone / 2)
        c.set_editor_property("inner_cone_angle", spot_cone / 4)


def build_ship(ship, recipe, report):
    mods = recipe["interior"]["kit_modules"]
    off = recipe["assemble"]["offset"]
    parts = kit_layout.manifest_parts()
    bp_path = "/Game/Ships/%s/Blueprints/BP_Ship_%s" % (ship, ship)
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    if bp is None:
        raise RuntimeError("no Blueprint " + bp_path)
    comps = Components(bp)
    removed = comps.remove_old()

    def hull_cm(x, y_ue, z):
        # layout metres, y already in Unreal's sense -> Hull space (the game blend's space in cm)
        return unreal.Vector((x + off[0]) * 100.0, (y_ue - off[1]) * 100.0, (z + off[2]) * 100.0)

    n_parts = n_lights = 0
    for k, (m, (x, y, z), yaw) in enumerate(kit_layout.layout_parts(mods, parts)):
        name = "SM_Kit_" + m
        sm = unreal.EditorAssetLibrary.load_asset("/Game/Kit/Meshes/" + name)
        if sm is None:
            raise RuntimeError("kit part %s not imported (import_kit.py)" % name)
        c = comps.add(unreal.StaticMeshComponent, "%s%02d_%s" % (MESH_PREFIX, k, m))
        c.set_static_mesh(sm)
        c.set_editor_property("relative_location", hull_cm(x, y, z))
        c.set_editor_property("relative_rotation", unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
        c.set_collision_profile_name("NoCollision")
        n_parts += 1
        base = hull_cm(x, y, z)
        for sname, sock in sorted(parts[name]["sockets"].items()):
            if not sname.startswith("SOCKET_Light"):
                continue
            prm = sock.get("params") or {}
            lx, ly, lz = sock["location_ue_cm"]
            wx, wy = kit_layout.rotate(yaw, lx, ly)
            at = base + unreal.Vector(wx, wy, lz)
            lname = "%s%02d" % (LIGHT_PREFIX, n_lights)
            if prm.get("type") == "rect":
                lc = comps.add(unreal.RectLightComponent, lname)
                dx, dy, dz = prm["dir_ue"]
                fx, fy = kit_layout.rotate(yaw, dx, dy)
                ax, ay, az = prm.get("along_ue", (0.0, -1.0, 0.0))
                gx, gy = kit_layout.rotate(yaw, ax, ay)
                rot = unreal.MathLibrary.make_rot_from_xy(unreal.Vector(fx, fy, dz), unreal.Vector(gx, gy, az))
                _light(lc, prm.get("role", "warm"), prm["cd"], prm.get("radius_m", 2.0), None)
                lc.set_editor_property("source_width", float(prm["width_cm"]))
                lc.set_editor_property("source_height", float(prm["height_cm"]))
                lc.set_editor_property("barn_door_angle", 70.0)
                lc.set_editor_property("barn_door_length", 3.0)
                lc.set_editor_property("specular_scale", 0.3)
            elif prm.get("type") == "spot":
                lc = comps.add(unreal.SpotLightComponent, lname)
                rot = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0)
                _light(lc, prm.get("role", "work"), prm["cd"], prm.get("radius_m", 3.8), prm.get("source_radius_cm", 4.0),
                       spot_cone=prm.get("cone_deg", 90.0))
                lc.set_editor_property("specular_scale", 0.6)
            else:
                lc = comps.add(unreal.PointLightComponent, lname)
                rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
                _light(lc, prm.get("role", "warm"), prm.get("cd", 1.0), prm.get("radius_m", 1.6), prm.get("source_radius_cm", 1.0))
                lc.set_editor_property("specular_scale", 0.2)
            lc.set_editor_property("relative_location", at)
            lc.set_editor_property("relative_rotation", rot)
            n_lights += 1
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    report[ship] = {"rooms": mods.get("rooms", []), "parts": n_parts, "lights": n_lights, "removed": removed}


def build_all():
    report = {}
    for ship, recipe in recipes():
        build_ship(ship, recipe, report)
    print("KITROOMS " + json.dumps(report))
    return report


if __name__ == "__main__":
    build_all()
