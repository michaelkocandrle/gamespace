"""Ship materials: master materials and per-ship instances from <Ship>_setup.json.

Used by Tools/Assets/import_ship.py. Editor-side only (needs `unreal`).

Masters (rebuilt on every run, like the scene materials):
    /Game/Ships/Shared/Materials/M_Ship_Hull   opaque, Nanite: BaseColor, Metallic, Roughness,
                                               EmissiveColor x EmissiveStrength (flat colours per slot:
                                               hand-modelled ships, thruster and light slots)
    /Game/Ships/Shared/Materials/M_Ship_PBR    opaque, Nanite: textures BaseColorMap, ORMMap (G roughness,
                                               B metallic) and NormalMap, with BaseColorTint,
                                               RoughnessScale, MetallicScale (AI models, one texture set)
    /Game/Ships/Shared/Materials/M_Ship_Screen opaque, unlit, pixel animation: a cockpit display - ScreenTexture x
                                               EmissiveStrength, nothing else (lit glass reflected the sky
                                               and the cockpit light and washed the instruments out). The game sets
                                               ScreenTexture to a render target it draws its displays into
                                               (UCockpitDisplayComponent); in the editor it is black
    /Game/Ships/Shared/Materials/M_Ship_Glass  translucent, two-sided, surface forward shading:
                                               BaseColor, Opacity, Roughness

Instances go to /Game/Ships/<Ship>/Materials/MI_... and are assigned to mesh slots by slot name
(the Blender material name), optionally only on the meshes an entry lists. A "pbr" entry names its
textures (base_color, orm, normal: PNG paths relative to the repository); they are imported to
/Game/Ships/<Ship>/Textures as T_<file name> with the right settings (normal maps: no sRGB, green
channel flipped, because Blender bakes OpenGL normal maps and Unreal expects DirectX; ORM: masks).
"""

import os

import unreal

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MEL = unreal.MaterialEditingLibrary
SHARED = "/Game/Ships/Shared/Materials"
MASTERS = {"hull": SHARED + "/M_Ship_Hull", "pbr": SHARED + "/M_Ship_PBR", "glass": SHARED + "/M_Ship_Glass",
           "screen": SHARED + "/M_Ship_Screen"}
TEXTURE_PARAMS = {"base_color": "BaseColorMap", "orm": "ORMMap", "normal": "NormalMap"}


def _asset_tools():
    return unreal.AssetToolsHelpers.get_asset_tools()


def _fresh_material(path):
    material = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        folder, name = path.rsplit("/", 1)
        material = _asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    else:
        for expr in list(MEL.get_material_expressions(material)):
            MEL.delete_material_expression(material, expr)
    return material


def _node(material, cls, x, y, **properties):
    expr = MEL.create_material_expression(material, cls, x, y)
    for key, value in properties.items():
        expr.set_editor_property(key, value)
    return expr


def _link(src, dst, dst_input):
    if not MEL.connect_material_expressions(src, "", dst, dst_input):
        raise RuntimeError("could not connect %s -> %s.%s" % (src.get_class().get_name(), dst.get_class().get_name(), dst_input))


def _output(src, prop):
    if not MEL.connect_material_property(src, "", prop):
        raise RuntimeError("could not connect %s -> %s" % (src.get_class().get_name(), prop))


def _vector(material, name, default, x, y):
    return _node(material, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                 default_value=unreal.LinearColor(default[0], default[1], default[2], 1.0))


def _scalar(material, name, default, x, y):
    return _node(material, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=default)


def _texture_param(material, name, sampler, default_path, x, y):
    return _node(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=name,
                 sampler_type=sampler, texture=unreal.load_asset(default_path))


def build_pbr_master():
    pbr = _fresh_material(MASTERS["pbr"])
    pbr.set_editor_property("used_with_nanite", True)
    color = _texture_param(pbr, "BaseColorMap", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                           "/Engine/EngineResources/WhiteSquareTexture", -900, 0)
    tint = _node(pbr, unreal.MaterialExpressionMultiply, -400, 0)
    _link(color, tint, "A")
    tint_param = _vector(pbr, "BaseColorTint", (1.0, 1.0, 1.0), -900, 200)
    MEL.connect_material_expressions(tint_param, "", tint, "B")
    _output(tint, unreal.MaterialProperty.MP_BASE_COLOR)
    orm = _texture_param(pbr, "ORMMap", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
                         "/Engine/EngineResources/WhiteSquareTexture", -900, 350)
    rough = _node(pbr, unreal.MaterialExpressionMultiply, -400, 350)
    if not MEL.connect_material_expressions(orm, "G", rough, "A"):
        raise RuntimeError("ORM G -> roughness")
    _link(_scalar(pbr, "RoughnessScale", 1.0, -900, 550), rough, "B")
    _output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
    metal = _node(pbr, unreal.MaterialExpressionMultiply, -400, 500)
    if not MEL.connect_material_expressions(orm, "B", metal, "A"):
        raise RuntimeError("ORM B -> metallic")
    _link(_scalar(pbr, "MetallicScale", 1.0, -900, 650), metal, "B")
    _output(metal, unreal.MaterialProperty.MP_METALLIC)
    normal = _texture_param(pbr, "NormalMap", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                            "/Engine/EngineMaterials/DefaultNormal", -900, 800)
    if not MEL.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL):
        raise RuntimeError("normal map -> Normal")
    MEL.recompile_material(pbr)
    unreal.EditorAssetLibrary.save_loaded_asset(pbr, only_if_is_dirty=False)
    return pbr


def build_screen_master():
    screen = _fresh_material(MASTERS["screen"])
    screen.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    # The texture changes every frame on a surface that does not move: pixel animation tells temporal AA
    # (TSR) so, and it keeps less history there. Opaque on purpose: a translucent screen with responsive
    # AA writes no motion vectors, and with the camera shake whole rows of type doubled.
    screen.set_editor_property("has_pixel_animation", True)
    screen.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    screen.set_editor_property("used_with_nanite", True)
    image = _texture_param(screen, "ScreenTexture", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                           "/Engine/EngineResources/Black", -900, 300)
    emissive = _node(screen, unreal.MaterialExpressionMultiply, -400, 300)
    MEL.connect_material_expressions(image, "RGB", emissive, "A")
    _link(_scalar(screen, "EmissiveStrength", 3.0, -900, 500), emissive, "B")
    _output(emissive, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(screen)
    unreal.EditorAssetLibrary.save_loaded_asset(screen, only_if_is_dirty=False)
    return screen


def import_texture(ship, key, source, never_stream=False):
    """A PNG from the repository as /Game/Ships/<Ship>/Textures/T_..., set up for its role. never_stream:
    always at full resolution (a cockpit, which is always right in front of the camera)."""
    filename = os.path.join(REPO, source) if not os.path.isabs(source) else source
    name = os.path.splitext(os.path.basename(filename))[0]
    if not name.startswith("T_"):
        name = "T_" + name
    folder = "/Game/Ships/%s/Textures" % ship
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", filename)
    task.set_editor_property("destination_path", folder)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset("%s/%s" % (folder, name))
    if texture is None:
        raise RuntimeError("could not import %s" % filename)
    if key == "normal":
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("flip_green_channel", True)
    elif key == "orm":
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        texture.set_editor_property("srgb", False)
    else:
        texture.set_editor_property("srgb", True)
    texture.set_editor_property("never_stream", bool(never_stream))
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def build_masters():
    hull = _fresh_material(MASTERS["hull"])
    hull.set_editor_property("used_with_nanite", True)
    _output(_vector(hull, "BaseColor", (0.35, 0.35, 0.35), -600, 0), unreal.MaterialProperty.MP_BASE_COLOR)
    _output(_scalar(hull, "Metallic", 0.3, -600, 150), unreal.MaterialProperty.MP_METALLIC)
    _output(_scalar(hull, "Roughness", 0.5, -600, 250), unreal.MaterialProperty.MP_ROUGHNESS)
    emissive = _node(hull, unreal.MaterialExpressionMultiply, -300, 400)
    _link(_vector(hull, "EmissiveColor", (0.0, 0.0, 0.0), -600, 400), emissive, "A")
    _link(_scalar(hull, "EmissiveStrength", 0.0, -600, 550), emissive, "B")
    _output(emissive, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(hull)
    unreal.EditorAssetLibrary.save_loaded_asset(hull, only_if_is_dirty=False)

    glass = _fresh_material(MASTERS["glass"])
    glass.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    glass.set_editor_property("two_sided", True)
    glass.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    _output(_vector(glass, "BaseColor", (0.25, 0.35, 0.4), -600, 0), unreal.MaterialProperty.MP_BASE_COLOR)
    _output(_scalar(glass, "Opacity", 0.2, -600, 150), unreal.MaterialProperty.MP_OPACITY)
    _output(_scalar(glass, "Roughness", 0.03, -600, 250), unreal.MaterialProperty.MP_ROUGHNESS)
    _output(_node(glass, unreal.MaterialExpressionConstant, -600, 350, r=1.0), unreal.MaterialProperty.MP_SPECULAR)
    MEL.recompile_material(glass)
    unreal.EditorAssetLibrary.save_loaded_asset(glass, only_if_is_dirty=False)
    return {"hull": hull, "pbr": build_pbr_master(), "glass": glass, "screen": build_screen_master()}


def build_instance(name, folder, spec, masters, ship=None):
    path = "%s/%s" % (folder, name)
    mi = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mi is None:
        mi = _asset_tools().create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, masters[spec["master"]])
    for key, param in (("base_color", "BaseColor"), ("emissive_color", "EmissiveColor")):
        if key in spec:
            c = spec[key]
            MEL.set_material_instance_vector_parameter_value(mi, param, unreal.LinearColor(c[0], c[1], c[2], 1.0))
    for key, param in (("metallic", "Metallic"), ("roughness", "Roughness"), ("emissive_strength", "EmissiveStrength"), ("opacity", "Opacity"),
                       ("roughness_scale", "RoughnessScale"), ("metallic_scale", "MetallicScale")):
        if key in spec:
            MEL.set_material_instance_scalar_parameter_value(mi, param, float(spec[key]))
    if "base_color_tint" in spec:
        c = spec["base_color_tint"]
        MEL.set_material_instance_vector_parameter_value(mi, "BaseColorTint", unreal.LinearColor(c[0], c[1], c[2], 1.0))
    for key, source in (spec.get("textures") or {}).items():
        MEL.set_material_instance_texture_parameter_value(mi, TEXTURE_PARAMS[key], import_texture(ship, key, source, spec.get("never_stream", False)))
    MEL.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi


def apply(ship, setup, mesh_assets):
    """setup: the parsed <Ship>_setup.json. mesh_assets: {mesh name: StaticMesh}. Returns notes."""
    specs = setup.get("materials") or {}
    if not specs:
        return []
    masters = build_masters()
    folder = "/Game/Ships/%s/Materials" % ship
    notes = []
    # Mesh-specific entries win over general ones for the same slot.
    ordered = sorted(specs.items(), key=lambda kv: 1 if kv[1].get("meshes") else 0)
    instances = {name: build_instance(name, folder, spec, masters, ship) for name, spec in ordered}
    for mesh_name, mesh in mesh_assets.items():
        slots = mesh.get_editor_property("static_materials")
        for index, slot in enumerate(slots):
            slot_name = str(slot.get_editor_property("material_slot_name"))
            chosen = None
            for name, spec in ordered:
                if slot_name in spec.get("slots", []) and (not spec.get("meshes") or mesh_name in spec["meshes"]):
                    chosen = name
            if chosen is None:
                notes.append("%s slot %s has no material in the setup" % (mesh_name, slot_name))
                continue
            mesh.set_material(index, instances[chosen])
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    notes.append("%d material instances, masters %s" % (len(instances), ", ".join(MASTERS.values())))
    return notes
