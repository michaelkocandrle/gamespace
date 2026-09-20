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
           "screen": SHARED + "/M_Ship_Screen", "decal": SHARED + "/M_Ship_Decal"}
TEXTURE_PARAMS = {"base_color": "BaseColorMap", "orm": "ORMMap", "normal": "NormalMap", "ao": "AOMap"}


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
    # Base colour goes out through the cavity and wear layer (see _add_cavity_and_wear).
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
    # Metallic goes out through the cavity and wear layer too.
    normal = _texture_param(pbr, "NormalMap", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                            "/Engine/EngineMaterials/DefaultNormal", -900, 800)
    panel_offset, panel_groove = _add_panel_layer(pbr)
    scorch = _add_scorch_mask(pbr)
    grunge = _add_detail_layer(pbr, normal, rough, panel_offset, panel_groove, scorch)
    _add_cavity_and_wear(pbr, tint, metal, grunge, panel_groove, scorch)
    MEL.recompile_material(pbr)
    unreal.EditorAssetLibrary.save_loaded_asset(pbr, only_if_is_dirty=False)
    return pbr


DETAIL_TEXTURES = {"T_Ship_Detail_N": "normal", "T_Ship_Detail_Grunge": "orm", "T_Ship_Panels": "orm"}
SHARED_TEXTURES = "/Game/Ships/Shared/Textures"
SHARED_DECALS = "/Game/Ships/Shared/Decals"

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


# Panel seams, the same triplanar projection as the micro detail. One texture, three taps: the seam's
# normal is in RG (z is rebuilt) and the groove itself in B, so the material can darken and roughen it.
_PANEL_CODE = _TRIPLANAR + """
float3 sx = Texture2DSample(TexP, TexPSampler, p.yz).rgb;
float3 sy = Texture2DSample(TexP, TexPSampler, p.zx).rgb;
float3 sz = Texture2DSample(TexP, TexPSampler, p.xy).rgb;
float3 tx = float3(sx.rg * 2.0 - 1.0, 0.0); tx.z = sqrt(saturate(1.0 - dot(tx.xy, tx.xy)));
float3 ty = float3(sy.rg * 2.0 - 1.0, 0.0); ty.z = sqrt(saturate(1.0 - dot(ty.xy, ty.xy)));
float3 tz = float3(sz.rg * 2.0 - 1.0, 0.0); tz.z = sqrt(saturate(1.0 - dot(tz.xy, tz.xy)));
float3 ax = float3(1.0, 0.0, 0.0) * (n.x < 0.0 ? -1.0 : 1.0);
float3 ay = float3(0.0, 1.0, 0.0) * (n.y < 0.0 ? -1.0 : 1.0);
float3 az = float3(0.0, 0.0, 1.0) * (n.z < 0.0 ? -1.0 : 1.0);
float3 nx = normalize(float3(0.0, 1.0, 0.0) * tx.x + float3(0.0, 0.0, 1.0) * tx.y + ax * tx.z);
float3 ny = normalize(float3(0.0, 0.0, 1.0) * ty.x + float3(1.0, 0.0, 0.0) * ty.y + ay * ty.z);
float3 nz = normalize(float3(1.0, 0.0, 0.0) * tz.x + float3(0.0, 1.0, 0.0) * tz.y + az * tz.z);
float3 seam = normalize(w.x * nx + w.y * ny + w.z * nz);
float3 flat = normalize(w.x * ax + w.y * ay + w.z * az + 0.0001);
float3 offset = mul(seam - flat, (float3x3)GetPrimitiveData(Parameters).LocalToWorld);
float3 tangent = float3(dot(offset, Parameters.TangentToWorld[0]), dot(offset, Parameters.TangentToWorld[1]),
                        dot(offset, Parameters.TangentToWorld[2]));
float groove = w.x * sx.b + w.y * sy.b + w.z * sz.b;
return float4(clamp(tangent, -1.0, 1.0), groove);
"""


def _add_panel_layer(pbr):
    """Plating: a tiling sheet of seams projected in the ship's own space (Tools/Assets/generate_panel_lines.py).

    The ship's UV atlas is thousands of tiny islands, so a seam drawn into it would break at every
    island edge; projected this way it keeps its size in centimetres wherever it lands. Parameters:
    PanelTileCm (how many centimetres one sheet covers), PanelStrength, PanelSeamDarken;
    PanelStrength 0 turns the whole thing off. Returns (normal offset, groove) or (None, None).
    """
    texture = import_shared_texture("T_Ship_Panels")
    if texture is None:
        return None, None
    sheet = _node(pbr, unreal.MaterialExpressionTextureObjectParameter, -1700, 2100, parameter_name="PanelMap",
                  sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, texture=texture)
    panel = _custom(pbr, "PanelSeams", _PANEL_CODE, unreal.CustomMaterialOutputType.CMOT_FLOAT4,
                    ["TexP", "LocalPos", "Tile"], -1300, 2100)
    _link(sheet, panel, "TexP")
    _link(_node(pbr, unreal.MaterialExpressionLocalPosition, -1700, 2000), panel, "LocalPos")
    _link(_scalar(pbr, "PanelTileCm", 180.0, -1700, 2300), panel, "Tile")
    strength = _scalar(pbr, "PanelStrength", 0.6, -1700, 2400)
    offset = _node(pbr, unreal.MaterialExpressionComponentMask, -1100, 2100, r=True, g=True, b=True, a=False)
    _link(panel, offset, "")
    scaled = _node(pbr, unreal.MaterialExpressionMultiply, -950, 2100)
    _link(offset, scaled, "A")
    _link(strength, scaled, "B")
    groove = _node(pbr, unreal.MaterialExpressionComponentMask, -1100, 2300, r=False, g=False, b=False, a=True)
    _link(panel, groove, "")
    shown = _node(pbr, unreal.MaterialExpressionMultiply, -950, 2300)
    _link(groove, shown, "A")
    _link(strength, shown, "B")
    return scaled, shown


def import_decal_texture(name):
    """A generated marking (Tools/Assets/generate_decals.py) as /Game/Ships/Shared/Decals/<name>. Colour
    with an alpha: sRGB on, and no compression that would eat the alpha of thin stencil type."""
    filename = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Decals", name + ".png")
    if not os.path.isfile(filename):
        return None
    texture = _import_png(filename, SHARED_DECALS, name)
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_BC7)
    texture.set_editor_property("srgb", True)
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def _import_png(filename, folder, name):
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
    return texture


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


def _apply_scorch(pbr, colour, scorch):
    """Soot over the paint towards the tail. Returns the node to send to Base Color."""
    if scorch is None:
        return colour
    burnt = _node(pbr, unreal.MaterialExpressionLinearInterpolate, 50, 0)
    _link(colour, burnt, "A")
    _link(_vector(pbr, "ScorchColor", (0.10, 0.09, 0.09), -700, 800), burnt, "B")
    _link(scorch, burnt, "Alpha")
    return burnt


def _add_scorch_mask(pbr):
    """How burnt the plating is, from the ship's own X: 0 ahead of ScorchStartCm, 1 behind ScorchEndCm.

    Every ship here is one material over the whole hull, so the only zones available without a second
    UV set are the ones the geometry itself gives. The strongest is the tail: the plating around the
    nozzles takes the exhaust and goes dark and rough, which is what the Star Citizen references show
    and what tells a viewer which end is the engine. Parameters: ScorchAmount (0 turns it off),
    ScorchStartCm, ScorchEndCm (both negative, behind the ship's origin), ScorchColor, ScorchRough.
    The lengths are centimetres in the ship's space, so they belong in <Ship>_setup.json, not here.
    """
    position = _node(pbr, unreal.MaterialExpressionLocalPosition, -1700, 2700)
    forward = _node(pbr, unreal.MaterialExpressionComponentMask, -1500, 2700, r=True, g=False, b=False, a=False)
    _link(position, forward, "")
    start = _scalar(pbr, "ScorchStartCm", -150.0, -1700, 2800)
    end = _scalar(pbr, "ScorchEndCm", -600.0, -1700, 2900)
    behind = _node(pbr, unreal.MaterialExpressionSubtract, -1350, 2700)
    _link(start, behind, "A")
    _link(forward, behind, "B")
    span = _node(pbr, unreal.MaterialExpressionSubtract, -1350, 2850)
    _link(start, span, "A")
    _link(end, span, "B")
    ratio = _node(pbr, unreal.MaterialExpressionDivide, -1200, 2700)
    _link(behind, ratio, "A")
    _link(span, ratio, "B")
    mask = _node(pbr, unreal.MaterialExpressionClamp, -1050, 2700, min_default=0.0, max_default=1.0)
    _link(ratio, mask, "")
    amount = _node(pbr, unreal.MaterialExpressionMultiply, -900, 2700)
    _link(mask, amount, "A")
    _link(_scalar(pbr, "ScorchAmount", 0.0, -1700, 3000), amount, "B")
    return amount


def _add_detail_layer(pbr, normal, rough, panel_offset=None, panel_groove=None, scorch=None):
    """The micro surface the AI paint has no room for: a tiling normal and a roughness breakup, projected
    in the ship's own space, added on top of the baked maps. Parameters: DetailTileCm (how many centimetres
    one tile covers), DetailNormalStrength, DetailGrungeTileCm, DetailRoughVariation; 0 strength turns it off."""
    textures = {name: import_shared_texture(name) for name in ("T_Ship_Detail_N", "T_Ship_Detail_Grunge")}
    if not all(textures.values()):
        # No generated micro detail in the repository: the master keeps its baked maps, plus the panel
        # seams if those are there.
        if panel_offset is None:
            if not MEL.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL):
                raise RuntimeError("normal map -> Normal")
        else:
            only_panels = _node(pbr, unreal.MaterialExpressionAdd, -600, 900)
            if not MEL.connect_material_expressions(normal, "RGB", only_panels, "A"):
                raise RuntimeError("normal map -> panel add")
            _link(panel_offset, only_panels, "B")
            straight = _node(pbr, unreal.MaterialExpressionNormalize, -400, 900)
            _link(only_panels, straight, "")
            _output(straight, unreal.MaterialProperty.MP_NORMAL)
        _output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
        return None
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
    if panel_offset is not None:
        with_panels = _node(pbr, unreal.MaterialExpressionAdd, -500, 900)
        _link(combined, with_panels, "A")
        _link(panel_offset, with_panels, "B")
        combined = with_panels
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
    if panel_groove is not None:
        # A seam is bare, unpainted metal at the bottom of a groove: rougher than the plate around it.
        seam_rough = _node(pbr, unreal.MaterialExpressionMultiply, -250, 1450)
        _link(panel_groove, seam_rough, "A")
        _link(_scalar(pbr, "PanelSeamRough", 0.18, -1700, 2500), seam_rough, "B")
        with_seam = _node(pbr, unreal.MaterialExpressionAdd, -150, 1300)
        _link(clamped, with_seam, "A")
        _link(seam_rough, with_seam, "B")
        clamped = _node(pbr, unreal.MaterialExpressionClamp, -60, 1300, min_default=0.03, max_default=1.0)
        _link(with_seam, clamped, "")
    if scorch is not None:
        burnt = _node(pbr, unreal.MaterialExpressionMultiply, -60, 1500)
        _link(scorch, burnt, "A")
        _link(_scalar(pbr, "ScorchRough", 0.25, -1700, 3100), burnt, "B")
        with_burn = _node(pbr, unreal.MaterialExpressionAdd, 20, 1350)
        _link(clamped, with_burn, "A")
        _link(burnt, with_burn, "B")
        clamped = _node(pbr, unreal.MaterialExpressionClamp, 100, 1350, min_default=0.03, max_default=1.0)
        _link(with_burn, clamped, "")
    _output(clamped, unreal.MaterialProperty.MP_ROUGHNESS)
    return grunge


def _add_cavity_and_wear(pbr, tint, metal, grunge, panel_groove=None, scorch=None):
    """What makes a hull stop reading as one flat colour.

    Cavity: the baked ambient occlusion (the ORM's red channel, unused until 20. 9. 2026) both goes to
    the material's Ambient Occlusion output and darkens the paint a little, so panel gaps, recesses and
    the shade under greebles are there even in light that does not reach them.

    Wear: where the surface is exposed (high occlusion) and the grunge blotches are strongest, the paint
    thins out to bare metal - lighter, fully metallic. That is what breaks up the single-colour look of
    the Star Citizen references. Parameters: CavityStrength, AOStrength, WearAmount, WearThreshold,
    WearColor, WearMetallic; WearAmount 0 turns the wear off, CavityStrength 0 the cavity.
    """
    # Its own map, not a channel of the ORM: the ORM's red is the emissive mask for the screens
    # (Tools/Blender/build_ai_ship.py, surface_nodes), 1 over the whole hull, so reading occlusion out
    # of it darkened nothing (20. 9. 2026, found by painting the wear red and watching it cover the hull
    # evenly). White by default, so a ship without a baked AO map looks exactly as it did.
    ao_map = _texture_param(pbr, "AOMap", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
                            "/Engine/EngineResources/WhiteSquareTexture", -1100, 200)
    ao = _node(pbr, unreal.MaterialExpressionMultiply, -700, 200, const_b=1.0)
    if not MEL.connect_material_expressions(ao_map, "R", ao, "A"):
        raise RuntimeError("AO map R -> ambient occlusion")

    # Ambient Occlusion output: lerp(1, ao, AOStrength).
    ao_out = _node(pbr, unreal.MaterialExpressionLinearInterpolate, -450, 150, const_a=1.0)
    _link(ao, ao_out, "B")
    _link(_scalar(pbr, "AOStrength", 0.6, -900, 100), ao_out, "Alpha")
    _output(ao_out, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)

    # Paint darkened in the cavities: tint * lerp(1, ao, CavityStrength).
    cavity = _node(pbr, unreal.MaterialExpressionLinearInterpolate, -450, 250, const_a=1.0)
    _link(ao, cavity, "B")
    _link(_scalar(pbr, "CavityStrength", 0.35, -900, 150), cavity, "Alpha")
    shaded = _node(pbr, unreal.MaterialExpressionMultiply, -300, 0)
    _link(tint, shaded, "A")
    _link(cavity, shaded, "B")
    if panel_groove is not None:
        # The groove is in shadow of its own walls, so the paint in it reads darker.
        darken = _node(pbr, unreal.MaterialExpressionMultiply, -450, 400)
        _link(panel_groove, darken, "A")
        _link(_scalar(pbr, "PanelSeamDarken", 0.45, -900, 400), darken, "B")
        lit = _node(pbr, unreal.MaterialExpressionOneMinus, -350, 400)
        _link(darken, lit, "")
        seamed = _node(pbr, unreal.MaterialExpressionMultiply, -250, 100)
        _link(shaded, seamed, "A")
        _link(lit, seamed, "B")
        shaded = seamed

    if grunge is None:
        # No generated detail textures: the paint keeps the cavity, there is nothing to wear it with.
        _output(_apply_scorch(pbr, shaded, scorch), unreal.MaterialProperty.MP_BASE_COLOR)
        _output(metal, unreal.MaterialProperty.MP_METALLIC)
        return

    # The wear mask: the top of the grunge blotches, and only where the surface is exposed.
    above = _node(pbr, unreal.MaterialExpressionSubtract, -1000, 1800)
    _link(grunge, above, "A")
    threshold = _scalar(pbr, "WearThreshold", 0.62, -1700, 1800)
    _link(threshold, above, "B")
    headroom = _node(pbr, unreal.MaterialExpressionOneMinus, -1000, 1900)
    _link(threshold, headroom, "")
    spread = _node(pbr, unreal.MaterialExpressionDivide, -850, 1800)
    _link(above, spread, "A")
    _link(headroom, spread, "B")
    mask = _node(pbr, unreal.MaterialExpressionClamp, -700, 1800, min_default=0.0, max_default=1.0)
    _link(spread, mask, "")
    exposed = _node(pbr, unreal.MaterialExpressionMultiply, -550, 1800)
    _link(mask, exposed, "A")
    _link(ao, exposed, "B")
    amount = _node(pbr, unreal.MaterialExpressionMultiply, -400, 1800)
    _link(exposed, amount, "A")
    _link(_scalar(pbr, "WearAmount", 0.3, -1700, 1900), amount, "B")

    worn_colour = _node(pbr, unreal.MaterialExpressionLinearInterpolate, -150, 0)
    _link(shaded, worn_colour, "A")
    _link(_vector(pbr, "WearColor", (0.34, 0.34, 0.36), -700, 0), worn_colour, "B")
    _link(amount, worn_colour, "Alpha")
    _output(_apply_scorch(pbr, worn_colour, scorch), unreal.MaterialProperty.MP_BASE_COLOR)

    worn_metal = _node(pbr, unreal.MaterialExpressionLinearInterpolate, -150, 500)
    _link(metal, worn_metal, "A")
    _link(_scalar(pbr, "WearMetallic", 1.0, -700, 600), worn_metal, "B")
    _link(amount, worn_metal, "Alpha")
    _output(worn_metal, unreal.MaterialProperty.MP_METALLIC)


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
    elif key in ("orm", "ao"):
        # Values, not colour: no sRGB curve on the way in.
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
    return {"hull": hull, "pbr": build_pbr_master(), "glass": glass, "screen": build_screen_master(),
            "decal": build_decal_master()}


def build_decal_master():
    """The markings: a deferred decal projected onto the hull, so a stencil does not need a place in the
    ship's UV atlas and stays sharp from any distance. Parameters: DecalTexture, DecalTint, DecalOpacity
    (the paint's age), DecalRoughness (fresh paint is smoother than the hull around it)."""
    decal = _fresh_material(MASTERS["decal"])
    decal.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    # decal_blend_mode is read-only from Python and already defaults to translucent, which is the one
    # that paints base colour and roughness and leaves the hull's normal alone.
    decal.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    texture = _texture_param(decal, "DecalTexture", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                             "/Engine/EngineResources/WhiteSquareTexture", -800, 0)
    _link(_decal_uvs(decal), texture, "UVs")
    tinted = _node(decal, unreal.MaterialExpressionMultiply, -400, 0)
    if not MEL.connect_material_expressions(texture, "RGB", tinted, "A"):
        raise RuntimeError("decal texture RGB -> base colour")
    _link(_vector(decal, "DecalTint", (1.0, 1.0, 1.0), -800, 250), tinted, "B")
    _output(tinted, unreal.MaterialProperty.MP_BASE_COLOR)
    opacity = _node(decal, unreal.MaterialExpressionMultiply, -400, 400)
    if not MEL.connect_material_expressions(texture, "A", opacity, "A"):
        raise RuntimeError("decal texture A -> opacity")
    _link(_scalar(decal, "DecalOpacity", 1.0, -800, 450), opacity, "B")
    _output(opacity, unreal.MaterialProperty.MP_OPACITY)
    _output(_scalar(decal, "DecalRoughness", 0.55, -800, 600), unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(decal)
    unreal.EditorAssetLibrary.save_loaded_asset(decal, only_if_is_dirty=False)
    return decal


def _decal_uvs(decal):
    """The decal's own UVs, with a switch for each axis: DecalFlipU, DecalFlipV (0 or 1).

    A decal's texture lands on the surface the way the projection box is turned, and which way round
    that is depends on the rotation - stencil type came out mirrored on the ship's flanks (20. 9. 2026).
    A rotation cannot mirror, so the flip belongs here.
    """
    uvs = _node(decal, unreal.MaterialExpressionTextureCoordinate, -1600, 0)
    axes = []
    for index, (channel, name) in enumerate((("R", "DecalFlipU"), ("G", "DecalFlipV"))):
        part = _node(decal, unreal.MaterialExpressionComponentMask, -1400, index * 200,
                     r=(channel == "R"), g=(channel == "G"), b=False, a=False)
        _link(uvs, part, "")
        flipped = _node(decal, unreal.MaterialExpressionOneMinus, -1250, index * 200)
        _link(part, flipped, "")
        pick = _node(decal, unreal.MaterialExpressionLinearInterpolate, -1100, index * 200)
        _link(part, pick, "A")
        _link(flipped, pick, "B")
        _link(_scalar(decal, name, 0.0, -1600, 200 + index * 200), pick, "Alpha")
        axes.append(pick)
    joined = _node(decal, unreal.MaterialExpressionAppendVector, -950, 100)
    _link(axes[0], joined, "A")
    _link(axes[1], joined, "B")
    return joined


def build_decal_instances(ship, setup, masters):
    """One material instance per marking in the setup's "decals" list, as MI_Ship_<Ship>_Decal_<name>.
    Returns {name: instance} for the components import_ship.py puts on the Blueprint."""
    folder = "/Game/Ships/%s/Materials" % ship
    instances = {}
    for spec in setup.get("decals") or []:
        texture = import_decal_texture(spec["texture"])
        if texture is None:
            continue
        name = "MI_Ship_%s_Decal_%s" % (ship, spec["name"])
        path = "%s/%s" % (folder, name)
        mi = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
        if mi is None:
            mi = _asset_tools().create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, masters["decal"])
        MEL.set_material_instance_texture_parameter_value(mi, "DecalTexture", texture)
        for key, param in (("opacity", "DecalOpacity"), ("roughness", "DecalRoughness"),
                           ("flip_u", "DecalFlipU"), ("flip_v", "DecalFlipV")):
            if key in spec:
                MEL.set_material_instance_scalar_parameter_value(mi, param, float(spec[key]))
        if "tint" in spec:
            c = spec["tint"]
            MEL.set_material_instance_vector_parameter_value(mi, "DecalTint", unreal.LinearColor(c[0], c[1], c[2], 1.0))
        MEL.update_material_instance(mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
        instances[spec["name"]] = path
    return instances


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
                       ("detail_grunge_tile_cm", "DetailGrungeTileCm"), ("detail_rough_variation", "DetailRoughVariation"),
                       ("cavity_strength", "CavityStrength"), ("ao_strength", "AOStrength"),
                       ("wear_amount", "WearAmount"), ("wear_threshold", "WearThreshold"), ("wear_metallic", "WearMetallic"),
                       ("panel_tile_cm", "PanelTileCm"), ("panel_strength", "PanelStrength"),
                       ("panel_seam_darken", "PanelSeamDarken"), ("panel_seam_rough", "PanelSeamRough"),
                       ("scorch_amount", "ScorchAmount"), ("scorch_start_cm", "ScorchStartCm"),
                       ("scorch_end_cm", "ScorchEndCm"), ("scorch_rough", "ScorchRough")):
        if key in spec:
            MEL.set_material_instance_scalar_parameter_value(mi, param, float(spec[key]))
    for key, param in (("base_color_tint", "BaseColorTint"), ("wear_color", "WearColor"), ("scorch_color", "ScorchColor")):
        if key in spec:
            c = spec[key]
            MEL.set_material_instance_vector_parameter_value(mi, param, unreal.LinearColor(c[0], c[1], c[2], 1.0))
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
    decals = build_decal_instances(ship, setup, masters)
    if decals:
        notes.append("%d decal materials: %s" % (len(decals), ", ".join(sorted(decals))))
    notes.append("%d material instances, masters %s" % (len(instances), ", ".join(MASTERS.values())))
    return notes
