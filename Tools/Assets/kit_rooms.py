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
INTERIOR_ONLY_TAG = "InteriorOnly"        # SpaceshipPawn: on only under the interior lighting
# under the flight lighting (no MegaLights, every light paid in full) the kit corridor kept 1 ms over the old one:
# the walls' wash and the floor channel light only when walked (author 29. 9. 2026, then 20 ms on the RTX 2060; the
# target since 3. 10. 2026 is 1440p / 60 fps with TSR or DLSS on an RTX 5070 Ti - re-measured at the final optimisation)
INTERIOR_ONLY_SOCKETS = ("SOCKET_Light_Wash", "SOCKET_Light_Channel", "SOCKET_Light_Down", "SOCKET_Light_Halo",
                         "SOCKET_Light_Scallop")
# the author's light plan for a ship's kit room (28. 9. 2026): only the main lights cast shadows (the ceiling trays'
# linear lights: the dominant sources), the rest none but contact shadows. The walls' wash lights at half strength:
# without them the walls under the slope went black (0.08), at full strength the corridor was flat and over the SC
# brightness; their count does not change MegaLights' cost (8 or 12 lights: 3.5 ms)
# (29. 9. 2026, critic of the hold: "no pools on the floor, the frames cast no shadows") the ceiling panels' down-lights
# too - interior only, under MegaLights
SHADOWED_SOCKETS = ("SOCKET_Light_Linear", "SOCKET_Light_Down")
SKIPPED_SOCKETS = ()
SOCKET_SCALE = {"SOCKET_Light_Wash": 0.5}
CONTACT_SHADOW = 0.05       # screen fraction
# kit parts on lighting channel 1 only, their lights on 0 and 1: the sun (channel 0) never reaches a room inside the
# hull, and a receiver it cannot light needs no virtual shadow map pages - the sun's shadow depths were 3.3-3.8 ms of a
# corridor view (28. 9. 2026)
MESH_CHANNELS = (False, True, False)
LIGHT_CHANNELS = (True, True, False)


def _channels(values):
    ch = unreal.LightingChannels()
    for i, v in enumerate(values):
        ch.set_editor_property("channel%d" % i, v)
    return ch


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


def _light(c, role, cd, radius_m, source_cm, spot_cone=None, shadow=False):
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", float(cd) * SHIP_LIGHT_SCALE)
    c.set_editor_property("attenuation_radius", float(radius_m) * 100.0)
    # shadows only for the main lights: the ship is flown without MegaLights, and 11 shadowed lights took the
    # Wayfarer's interior views from 18 to 27-42 ms GPU (1676 draws instead of 673, 28. 9. 2026); the others get
    # contact shadows. The showroom's lights keep theirs (walked, MegaLights on)
    c.set_editor_property("cast_shadows", bool(shadow))
    if not shadow:
        c.set_editor_property("contact_shadow_length", CONTACT_SHADOW)
    c.set_editor_property("lighting_channels", _channels(LIGHT_CHANNELS))
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
    if not kit_layout.active_rooms(recipe):
        # switched off (kit_modules.enabled false): the rooms keep the ship's own interior (hs_interior)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        report[ship] = {"rooms": [], "enabled": False, "parts": 0, "lights": 0, "removed": removed}
        return

    def hull_cm(x, y_ue, z):
        # layout metres, y already in Unreal's sense -> Hull space (the game blend's space in cm)
        return unreal.Vector((x + off[0]) * 100.0, (y_ue - off[1]) * 100.0, (z + off[2]) * 100.0)

    # light zones along the ship (kit_modules.light_scale [[x0, x1, factor, room]], layout metres): a room's own level
    # (30. 9. 2026: the cabin, 4.8 m under the hold's lights, came out at p50 0.28 - SC 0.08-0.18)
    zones = [z for z in mods.get("light_scale", []) if not isinstance(z, str)]

    def zone_k(x_m, sname):
        # [x0, x1, factor, room, {socket prefix: extra factor}]
        z = next((z for z in zones if z[0] <= x_m <= z[1]), None)
        if z is None:
            return 1.0
        extra = z[4] if len(z) > 4 else {}
        return z[2] * next((v for k, v in extra.items() if sname.startswith(k)), 1.0)

    n_parts = n_lights = 0
    for k, (m, (x, y, z), yaw) in enumerate(kit_layout.layout_parts(mods, parts)):
        name = "SM_Kit_" + m
        sm = None
        if unreal.EditorAssetLibrary.does_asset_exist("/Game/Kit/Meshes/" + name):
            sm = unreal.EditorAssetLibrary.load_asset("/Game/Kit/Meshes/" + name)
        if sm is None:
            # a part built but not imported yet: import_kit.py imports import_ship (which builds the ship's kit rooms on
            # import) before it imports the parts, then builds the rooms again - skip it here, loudly
            unreal.log_warning("KITROOMS %s: kit part %s not imported yet (import_kit.py), skipped" % (ship, name))
            report.setdefault("missing_parts", []).append(name)
            continue
        c = comps.add(unreal.StaticMeshComponent, "%s%02d_%s" % (MESH_PREFIX, k, m))
        c.set_static_mesh(sm)
        c.set_editor_property("relative_location", hull_cm(x, y, z))
        c.set_editor_property("relative_rotation", unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
        c.set_collision_profile_name("NoCollision")
        c.set_editor_property("lighting_channels", _channels(MESH_CHANNELS))
        n_parts += 1
        base = hull_cm(x, y, z)
        for sname, sock in sorted(parts[name]["sockets"].items()):
            if not sname.startswith("SOCKET_Light") or sname.startswith(SKIPPED_SOCKETS):
                continue
            shadow = sname.startswith(SHADOWED_SOCKETS)
            prm = sock.get("params") or {}
            k_cd = next((v for kk, v in SOCKET_SCALE.items() if sname.startswith(kk)), 1.0)
            k_cd *= zone_k(x + kit_layout.rotate(yaw, *sock["location_ue_cm"][:2])[0] / 100.0, sname)
            prm = dict(prm, cd=prm.get("cd", 1.0) * k_cd)
            lx, ly, lz = sock["location_ue_cm"]
            wx, wy = kit_layout.rotate(yaw, lx, ly)
            at = base + unreal.Vector(wx, wy, lz)
            # (the socket's kind in the name: Light_fix_kit_03_Linear)
            lname = "%s%02d_%s" % (LIGHT_PREFIX, n_lights, sname.split("__")[0][len("SOCKET_Light_"):].split("_")[0])
            if prm.get("type") == "rect":
                lc = comps.add(unreal.RectLightComponent, lname)
                dx, dy, dz = prm["dir_ue"]
                fx, fy = kit_layout.rotate(yaw, dx, dy)
                ax, ay, az = prm.get("along_ue", (0.0, -1.0, 0.0))
                gx, gy = kit_layout.rotate(yaw, ax, ay)
                rot = unreal.MathLibrary.make_rot_from_xy(unreal.Vector(fx, fy, dz), unreal.Vector(gx, gy, az))
                _light(lc, prm.get("role", "warm"), prm["cd"], prm.get("radius_m", 2.0), None, shadow=shadow)
                lc.set_editor_property("source_width", float(prm["width_cm"]))
                lc.set_editor_property("source_height", float(prm["height_cm"]))
                lc.set_editor_property("barn_door_angle", 70.0)
                lc.set_editor_property("barn_door_length", 3.0)
                lc.set_editor_property("specular_scale", 0.3)
            elif prm.get("type") == "spot":
                lc = comps.add(unreal.SpotLightComponent, lname)
                rot = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0)
                if "dir_ue" in prm:
                    # a tilted spot (the wide ceilings' wall washers): its own direction, turned with the part
                    dx, dy, dz = prm["dir_ue"]
                    fx, fy = kit_layout.rotate(yaw, dx, dy)
                    rot = unreal.MathLibrary.make_rot_from_x(unreal.Vector(fx, fy, dz))
                _light(lc, prm.get("role", "work"), prm["cd"], prm.get("radius_m", 3.8), prm.get("source_radius_cm", 4.0),
                       spot_cone=prm.get("cone_deg", 90.0), shadow=shadow)
                lc.set_editor_property("specular_scale", 0.6)
            else:
                lc = comps.add(unreal.PointLightComponent, lname)
                rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
                _light(lc, prm.get("role", "warm"), prm.get("cd", 1.0), prm.get("radius_m", 1.6), prm.get("source_radius_cm", 1.0),
                       shadow=shadow)
                # the ceiling's halo lights none (critic of the hold, round 2: "a wide waxy highlight across the ceiling")
                lc.set_editor_property("specular_scale", float(prm.get("specular", 0.2)))
            lc.set_editor_property("relative_location", at)
            lc.set_editor_property("relative_rotation", rot)
            # a light only for the walked interior (MegaLights): the pawn keeps it off under the flight lighting, where
            # every unshadowed light is paid in full (the component bays' lights, 29. 9. 2026)
            if prm.get("interior_only") or sname.startswith(INTERIOR_ONLY_SOCKETS):
                lc.set_editor_property("component_tags", [unreal.Name(INTERIOR_ONLY_TAG)])
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
