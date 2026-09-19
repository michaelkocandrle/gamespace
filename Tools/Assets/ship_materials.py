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
    # Roughness goes out through the detail layer (see _add_detail_layer).
    metal = _node(pbr, unreal.MaterialExpressionMultiply, -400, 500)
    if not MEL.connect_material_expressions(orm, "B", metal, "A"):
        raise RuntimeError("ORM B -> metallic")
    _link(_scalar(pbr, "MetallicScale", 1.0, -900, 650), metal, "B")
    _output(metal, unreal.MaterialProperty.MP_METALLIC)
    normal = _texture_param(pbr, "NormalMap", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                            "/Engine/EngineMaterials/DefaultNormal", -900, 800)
    _add_detail_layer(pbr, normal, rough)
    MEL.recompile_material(pbr)
    unreal.EditorAssetLibrary.save_loaded_asset(pbr, only_if_is_dirty=False)
    return pbr


DETAIL_TEXTURES = {"T_Ship_Detail_N": "normal", "T_Ship_Detail_Grunge": "orm"}
SHARED_TEXTURES = "/Game/Ships/Shared/Textures"

# Triplanar in the ship's own space: the detail keeps its size in centimetres, and it does not swim when
# the ship moves (world-space projection would). Each plane's sample is put back into local space through
# that plane's axes, and what the node returns is only the difference from the flat surface, so the graph
# can add it to the baked normal in tangent space.
_TRIPLANAR = """
float3x3 WorldToLocal = (float3x3)GetPrimitiveData(Parameters).WorldToLocal;
float3 p = LocalPos / max(Tile, 1.0);
float3 n = normalize(mul(Parameters.TangentToWorld[2], WorldToLocal));
float3 w = pow(abs(n), 4);
w /= (w.x + w.y + w.z + 0.0001);
"""

_DETAIL_NORMAL_CODE = _TRIPLANAR + """
float3 sx = Texture2DSample(TexN, TexNSampler, p.yz).rgb * 2.0 - 1.0;
float3 sy = Texture2DSample(TexN, TexNSampler, p.zx).rgb * 2.0 - 1.0;
float3 sz = Texture2DSample(TexN, TexNSampler, p.xy).rgb * 2.0 - 1.0;
float3 ax = float3(1.0, 0.0, 0.0) * (n.x < 0.0 ? -1.0 : 1.0);
float3 ay = float3(0.0, 1.0, 0.0) * (n.y < 0.0 ? -1.0 : 1.0);
float3 az = float3(0.0, 0.0, 1.0) * (n.z < 0.0 ? -1.0 : 1.0);
float3 nx = normalize(float3(0.0, 1.0, 0.0) * sx.x + float3(0.0, 0.0, 1.0) * sx.y + ax * sx.z);
float3 ny = normalize(float3(0.0, 0.0, 1.0) * sy.x + float3(1.0, 0.0, 0.0) * sy.y + ay * sy.z);
float3 nz = normalize(float3(1.0, 0.0, 0.0) * sz.x + float3(0.0, 1.0, 0.0) * sz.y + az * sz.z);
float3 detail = normalize(w.x * nx + w.y * ny + w.z * nz);
float3 flat = normalize(w.x * ax + w.y * ay + w.z * az + 0.0001);
// The difference, back in tangent space, so the graph can add it to the baked normal map.
float3 offset = mul(detail - flat, (float3x3)GetPrimitiveData(Parameters).LocalToWorld);
float3 tangent = float3(dot(offset, Parameters.TangentToWorld[0]), dot(offset, Parameters.TangentToWorld[1]),
                        dot(offset, Parameters.TangentToWorld[2]));
return clamp(tangent, -1.0, 1.0);
"""

_DETAIL_GRUNGE_CODE = _TRIPLANAR + """
float g = w.x * Texture2DSample(TexG, TexGSampler, p.yz).r
        + w.y * Texture2DSample(TexG, TexGSampler, p.zx).r
        + w.z * Texture2DSample(TexG, TexGSampler, p.xy).r;
return g;
"""


def import_shared_texture(name):
    """A generated detail texture (Tools/Assets/generate_detail_textures.py) as /Game/Ships/Shared/Textures/<name>."""
    filename = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Textures", name + ".png")
    if not os.path.isfile(filename):
        return None
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", filename)
    task.set_editor_property("destination_path", SHARED_TEXTURES)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset("%s/%s" % (SHARED_TEXTURES, name))
    if texture is None:
        raise RuntimeError("could not import %s" % filename)
    if DETAIL_TEXTURES[name] == "normal":
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("flip_green_channel", True)
    else:
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        texture.set_editor_property("srgb", False)
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def _custom(material, name, code, output_type, input_names, x, y):
    node = _node(material, unreal.MaterialExpressionCustom, x, y, code=code, output_type=output_type, description=name)
    inputs = []
    for input_name in input_names:
        # Struct wrappers take no keyword arguments (Docs/WORKFLOW.md 9.5b).
        custom_input = unreal.CustomInput()
        custom_input.set_editor_property("input_name", input_name)
        inputs.append(custom_input)
    node.set_editor_property("inputs", inputs)
    return node


def _add_detail_layer(pbr, normal, rough):
    """The micro surface the AI paint has no room for: a tiling normal and a roughness breakup, projected
    in the ship's own space, added on top of the baked maps. Parameters: DetailTileCm (how many centimetres
    one tile covers), DetailNormalStrength, DetailGrungeTileCm, DetailRoughVariation; 0 strength turns it off."""
    textures = {name: import_shared_texture(name) for name in DETAIL_TEXTURES}
    if not all(textures.values()):
        # No generated textures in the repository: the master keeps its baked maps alone.
        if not MEL.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL):
            raise RuntimeError("normal map -> Normal")
        _output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
        return
    tex_normal = _node(pbr, unreal.MaterialExpressionTextureObjectParameter, -1700, 1000, parameter_name="DetailNormalMap",
                       sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, texture=textures["T_Ship_Detail_N"])
    tex_grunge = _node(pbr, unreal.MaterialExpressionTextureObjectParameter, -1700, 1200, parameter_name="DetailGrungeMap",
                       sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, texture=textures["T_Ship_Detail_Grunge"])
    local_position = _node(pbr, unreal.MaterialExpressionLocalPosition, -1700, 800)

    # --- Normal: the detail's deviation from the flat surface, added to the baked normal ---------------
    detail = _custom(pbr, "DetailNormal", _DETAIL_NORMAL_CODE, unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                     ["TexN", "LocalPos", "Tile"], -1300, 1000)
    _link(tex_normal, detail, "TexN")
    _link(local_position, detail, "LocalPos")
    _link(_scalar(pbr, "DetailTileCm", 30.0, -1700, 1400), detail, "Tile")
    scaled = _node(pbr, unreal.MaterialExpressionMultiply, -800, 1000)
    _link(detail, scaled, "A")
    _link(_scalar(pbr, "DetailNormalStrength", 0.7, -1700, 1500), scaled, "B")
    combined = _node(pbr, unreal.MaterialExpressionAdd, -600, 900)
    if not MEL.connect_material_expressions(normal, "RGB", combined, "A"):
        raise RuntimeError("normal map -> detail add")
    _link(scaled, combined, "B")
    final_normal = _node(pbr, unreal.MaterialExpressionNormalize, -400, 900)
    _link(combined, final_normal, "")
    _output(final_normal, unreal.MaterialProperty.MP_NORMAL)

    # --- Roughness: the blotches lift and lower it a little, so the paint is not uniformly polished -----
    grunge = _custom(pbr, "DetailGrunge", _DETAIL_GRUNGE_CODE, unreal.CustomMaterialOutputType.CMOT_FLOAT1,
                     ["TexG", "LocalPos", "Tile"], -1300, 1300)
    _link(tex_grunge, grunge, "TexG")
    _link(local_position, grunge, "LocalPos")
    _link(_scalar(pbr, "DetailGrungeTileCm", 140.0, -1700, 1600), grunge, "Tile")
    centred = _node(pbr, unreal.MaterialExpressionSubtract, -1000, 1300, const_b=0.5)
    _link(grunge, centred, "A")
    # Only upwards: dirt and wear make a surface rougher, never more polished. Lowering the roughness
    # under a blotch gave the hull bright specular patches up close (20. 9. 2026).
    positive = _node(pbr, unreal.MaterialExpressionClamp, -930, 1300, min_default=0.0, max_default=1.0)
    _link(centred, positive, "")
    spread = _node(pbr, unreal.MaterialExpressionMultiply, -850, 1300, const_b=2.0)
    _link(positive, spread, "A")
    amount = _node(pbr, unreal.MaterialExpressionMultiply, -700, 1300)
    _link(spread, amount, "A")
    _link(_scalar(pbr, "DetailRoughVariation", 0.12, -1700, 1700), amount, "B")
    factor = _node(pbr, unreal.MaterialExpressionAdd, -550, 1300, const_a=1.0)
    _link(amount, factor, "B")
    varied = _node(pbr, unreal.MaterialExpressionMultiply, -400, 1250)
    _link(rough, varied, "A")
    _link(factor, varied, "B")
    clamped = _node(pbr, unreal.MaterialExpressionClamp, -250, 1250, min_default=0.03, max_default=1.0)
    _link(varied, clamped, "")
    _output(clamped, unreal.MaterialProperty.MP_ROUGHNESS)


def build_screen_master():
    screen = _fresh_material(MASTERS["screen"])
    screen.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    # Opaque, with pixel animation so temporal AA (TSR) keeps less history on the changing texture.
    # Tried and dropped (19. 9. 2026, Tools/Shots/display_sharpness.json): translucent with responsive
    # AA (rows doubled under camera shake: no motion vectors), the same with "Output Depth and Velocity"
    # (numbers still blended), and translucency after motion blur, past TSR (blurred and doubled even
    # standing still). What keeps changing numbers sharp is the display itself: its figures change 12
    # times a second (UCockpitDisplayComponent::StateRateHz), so TSR settles between them.
    screen.set_editor_property("has_pixel_animation", True)
    screen.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    screen.set_editor_property("translucency_pass", unreal.MaterialTranslucencyPass.MTP_BEFORE_DOF)
    screen.set_editor_property("enable_responsive_aa", False)
    screen.set_editor_property("output_translucent_velocity", False)
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
                       ("roughness_scale", "RoughnessScale"), ("metallic_scale", "MetallicScale"),
                       ("detail_tile_cm", "DetailTileCm"), ("detail_normal_strength", "DetailNormalStrength"),
                       ("detail_grunge_tile_cm", "DetailGrungeTileCm"), ("detail_rough_variation", "DetailRoughVariation")):
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
