"""Ship materials: master materials and per-ship instances from <Ship>_setup.json.

Used by Tools/Assets/import_ship.py. Editor-side only (needs `unreal`).

Masters (rebuilt on every run, like the scene materials):
    /Game/Ships/Shared/Materials/M_Ship_Hull   opaque, Nanite: BaseColor, Metallic, Roughness,
                                               EmissiveColor x EmissiveStrength (flat colours per slot:
                                               hand-modelled ships, thruster and light slots)
    /Game/Ships/Shared/Materials/M_Ship_PBR    opaque, Nanite: textures BaseColorMap, ORMMap (G roughness,
                                               B metallic) and NormalMap, with BaseColorTint,
                                               RoughnessScale, MetallicScale (AI models, one texture set)
    /Game/Ships/Shared/Materials/M_Ship_Screen masked, unlit, pixel animation: a cockpit display as a glass
                                               panel - ScreenTexture x EmissiveStrength with faint scan lines,
                                               lit pixels opaque, the empty glass dithered see-through
                                               (GlassOpacity), a cool fresnel sheen; not lit (lit glass
                                               reflected the sky and washed the instruments out). The game sets
                                               ScreenTexture to a render target it draws its displays into
                                               (UCockpitDisplayComponent); in the editor it is black
    /Game/Ships/Shared/Materials/M_Ship_ScreenBack opaque with pixel animation: the plate behind a display's
                                               clear glass (BaseColor, Metallic, Roughness)
    /Game/Ships/Shared/Materials/M_Ship_Blink  opaque: a slowly blinking LED (EmissiveColor x EmissiveStrength
                                               pulsing BlinkMin..1 at BlinkHz)
    /Game/Ships/Shared/Materials/M_Ship_Holo   additive, unlit: the cockpit's ship hologram (turns about
                                               HoloPivot by World Position Offset, scan lines, damage colour)
    /Game/Ships/Shared/Materials/M_Ship_Glass  translucent, two-sided, surface translucency volume:
                                               BaseColor, Opacity / Roughness / Specular seen from outside,
                                               OpacityInside / RoughnessInside / SpecularInside from inside
                                               (blended by MPC_ShipView.InsideView)
    /Game/Ships/Shared/Materials/MPC_ShipView  InsideView: 1 while the player's camera is inside a ship's
                                               interior (ASpaceshipPawn::UpdateViewCollection)

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
           "screen": SHARED + "/M_Ship_Screen", "decal": SHARED + "/M_Ship_Decal",
           "meshdecal": SHARED + "/M_Ship_MeshDecal", "meshdecal_paint": SHARED + "/M_Ship_MeshDecalPaint",
           "meshdecal_ao": SHARED + "/M_Ship_MeshDecalAO", "meshdecal_grime": SHARED + "/M_Ship_MeshDecalGrime",
           "layered": SHARED + "/M_Ship_Layered", "screenback": SHARED + "/M_Ship_ScreenBack",
           "blink": SHARED + "/M_Ship_Blink", "holo": SHARED + "/M_Ship_Holo"}
TEXTURE_PARAMS = {"base_color": "BaseColorMap", "orm": "ORMMap", "normal": "NormalMap", "ao": "AOMap",
                  "decal_normal": "DecalNormalMap", "decal_m": "DecalMMap", "decal_bc": "DecalColorMap",
                  "decal_ao": "DecalAOMap"}


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


def _view_collection():
    """MPC_ShipView with the scalar InsideView (default 0 = outside). An existing parameter is kept: its id is what
    the materials reference."""
    path = SHARED + "/MPC_ShipView"
    mpc = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mpc is None:
        mpc = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MPC_ShipView", SHARED, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    params = list(mpc.get_editor_property("scalar_parameters"))
    if not any(str(p.get_editor_property("parameter_name")) == "InsideView" for p in params):
        p = unreal.CollectionScalarParameter()
        p.set_editor_property("parameter_name", "InsideView")
        p.set_editor_property("default_value", 0.0)
        mpc.set_editor_property("scalar_parameters", params + [p])
        unreal.EditorAssetLibrary.save_loaded_asset(mpc, only_if_is_dirty=False)
    return mpc


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
    # A glass panel (author 25. 9. 2026, step 3): the content opaque and sharp, the empty glass see-through -
    # MASKED with a temporal dither for the glass, not translucent. Translucent screens were tried on
    # 19. 9. 2026 (Tools/Shots/display_sharpness.json) and dropped: no depth and no motion vectors, TSR doubled
    # the rows under camera shake, "after motion blur" blurred them standing still. Masked writes depth and
    # velocity like any opaque surface; TSR resolves the dither into a smoked glass. Pixel animation kept:
    # TSR keeps less history on the changing texture. The figures change 5 times a second
    # (UCockpitDisplayComponent::StateRateHz), so TSR settles between them.
    screen.set_editor_property("has_pixel_animation", True)
    screen.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    screen.set_editor_property("opacity_mask_clip_value", 0.5)
    screen.set_editor_property("translucency_pass", unreal.MaterialTranslucencyPass.MTP_BEFORE_DOF)
    screen.set_editor_property("enable_responsive_aa", False)
    screen.set_editor_property("output_translucent_velocity", False)
    screen.set_editor_property("used_with_nanite", True)
    image = _texture_param(screen, "ScreenTexture", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                           "/Engine/EngineResources/Black", -1600, 300)
    # content = the display's lit pixels (text, lines, symbols); the widget's dark glass stays below the threshold
    lum = _node(screen, unreal.MaterialExpressionDotProduct, -1300, 600)
    MEL.connect_material_expressions(image, "RGB", lum, "A")
    _link(_node(screen, unreal.MaterialExpressionConstant3Vector, -1500, 700, constant=unreal.LinearColor(0.3, 0.59, 0.11, 1.0)), lum, "B")
    over = _node(screen, unreal.MaterialExpressionSubtract, -1100, 600)
    _link(lum, over, "A")
    _link(_scalar(screen, "GlassThreshold", 0.07, -1300, 800), over, "B")
    content = _node(screen, unreal.MaterialExpressionMultiply, -900, 600)
    _link(over, content, "A")
    _link(_scalar(screen, "ContentRamp", 20.0, -1100, 800), content, "B")
    content_c = _node(screen, unreal.MaterialExpressionSaturate, -750, 600)
    _link(content, content_c, "")
    # the glass: dithered by blue noise at GlassOpacity (0 = clear, 1 = solid dark glass; DitherTemporalAA is
    # not exposed to Python) - opaque where GlassOpacity is above the noise, 0.5 is the clip value. Default 0:
    # clear glass over the display's dark back plate reads best (a dark shifted copy of the page seen at first
    # was the sun's shadow of the letters - the Screens component casts no shadow, import_ship.py).
    above = _node(screen, unreal.MaterialExpressionSubtract, -800, 850)
    _link(_scalar(screen, "GlassOpacity", 0.0, -1000, 850), above, "A")
    _link(_node(screen, unreal.MaterialExpressionScalarBlueNoise, -1000, 950), above, "B")
    dither = _node(screen, unreal.MaterialExpressionAdd, -650, 850)
    _link(above, dither, "A")
    _link(_node(screen, unreal.MaterialExpressionConstant, -800, 950, r=0.5), dither, "B")
    mask = _node(screen, unreal.MaterialExpressionMax, -550, 700)
    _link(content_c, mask, "A")
    _link(dither, mask, "B")
    _output(mask, unreal.MaterialProperty.MP_OPACITY_MASK)
    # emissive: the image, faint scan lines across it, a cool fresnel sheen on the glass
    uv = _node(screen, unreal.MaterialExpressionTextureCoordinate, -1600, 0)
    v = _node(screen, unreal.MaterialExpressionComponentMask, -1400, 0, r=False, g=True, b=False, a=False)
    _link(uv, v, "")
    rows = _node(screen, unreal.MaterialExpressionMultiply, -1200, 0)
    _link(v, rows, "A")
    _link(_scalar(screen, "ScanRows", 380.0, -1400, 120), rows, "B")
    wave = _node(screen, unreal.MaterialExpressionSine, -1000, 0, period=1.0)
    _link(rows, wave, "")
    depth = _scalar(screen, "ScanDepth", 0.06, -1000, 120)
    scan = _node(screen, unreal.MaterialExpressionMultiply, -850, 0)
    _link(wave, scan, "A")
    _link(depth, scan, "B")
    scan1 = _node(screen, unreal.MaterialExpressionSubtract, -700, 0)
    _link(_node(screen, unreal.MaterialExpressionConstant, -850, -80, r=1.0), scan1, "A")
    _link(scan, scan1, "B")
    lit = _node(screen, unreal.MaterialExpressionMultiply, -500, 300)
    MEL.connect_material_expressions(image, "RGB", lit, "A")
    _link(_scalar(screen, "EmissiveStrength", 3.0, -700, 400), lit, "B")
    lit_scan = _node(screen, unreal.MaterialExpressionMultiply, -350, 200)
    _link(lit, lit_scan, "A")
    _link(scan1, lit_scan, "B")
    fres = _node(screen, unreal.MaterialExpressionFresnel, -700, 1000, exponent=4.0, base_reflect_fraction=0.04)
    sheen = _node(screen, unreal.MaterialExpressionMultiply, -500, 1000)
    _link(fres, sheen, "A")
    _link(_vector(screen, "SheenColor", (0.03, 0.06, 0.1), -700, 1150), sheen, "B")
    emissive = _node(screen, unreal.MaterialExpressionAdd, -200, 400)
    _link(lit_scan, emissive, "A")
    _link(sheen, emissive, "B")
    _output(emissive, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(screen)
    unreal.EditorAssetLibrary.save_loaded_asset(screen, only_if_is_dirty=False)
    return screen


def build_holo_master():
    """The cockpit's ship hologram (step 6): additive, unlit, one-sided. Emission = HoloColor x HoloStrength x
    (a base plus a fresnel rim) x scan lines rolling up in world z x a faint flicker; damage colour prepared
    (lerp to DamageColor by DamageAmount x vertex colour R - static 0 for now). World Position Offset turns the
    mesh slowly about the vertical through HoloPivot (mesh space, cm - import_ship.py sets it from the imported
    mesh's bounds) and jitters it a little."""
    m = _fresh_material(MASTERS["holo"])
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    # one-sided: the mesh is the hull's closed outer envelope (hs_cockpit._envelope); its far side added through
    # the near one blurred the shape (critic, 25. 9. 2026)
    m.set_editor_property("two_sided", False)
    m.set_editor_property("enable_responsive_aa", True)
    time = _node(m, unreal.MaterialExpressionTime, -2200, 1200)
    # --- turn about the pivot: RotateAboutAxis(axis, angle 0..1, pivot, position)
    pivot_local = _vector(m, "HoloPivot", (0.0, 0.0, 0.0), -2200, 1500)
    pivot = _node(m, unreal.MaterialExpressionTransformPosition, -1900, 1500)
    pivot.set_editor_property("transform_source_type", unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
    pivot.set_editor_property("transform_type", unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD)
    MEL.connect_material_expressions(pivot_local, "", pivot, "")
    axis = _node(m, unreal.MaterialExpressionTransform, -1900, 1650)
    axis.set_editor_property("transform_source_type", unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
    axis.set_editor_property("transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    MEL.connect_material_expressions(_node(m, unreal.MaterialExpressionConstant3Vector, -2200, 1650,
                                           constant=unreal.LinearColor(0.0, 0.0, 1.0, 1.0)), "", axis, "")
    axis_n = _node(m, unreal.MaterialExpressionNormalize, -1700, 1650)
    MEL.connect_material_expressions(axis, "", axis_n, "")
    turns = _node(m, unreal.MaterialExpressionMultiply, -1900, 1350)
    _link(time, turns, "A")
    _link(_scalar(m, "HoloTurnsPerSecond", 1.0 / 30.0, -2200, 1350), turns, "B")
    angle = _node(m, unreal.MaterialExpressionFrac, -1700, 1350)
    MEL.connect_material_expressions(turns, "", angle, "")
    pos = _node(m, unreal.MaterialExpressionWorldPosition, -1900, 1800)
    pos.set_editor_property("world_position_shader_offset", unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    rot = _node(m, unreal.MaterialExpressionRotateAboutAxis, -1400, 1500)
    MEL.connect_material_expressions(axis_n, "", rot, "NormalizedRotationAxis")
    MEL.connect_material_expressions(angle, "", rot, "RotationAngle")
    MEL.connect_material_expressions(pivot, "", rot, "PivotPoint")
    MEL.connect_material_expressions(pos, "", rot, "Position")
    # --- jitter: a tiny shake along the axis, two beating sines
    j1 = _node(m, unreal.MaterialExpressionSine, -1700, 1950, period=0.23)
    MEL.connect_material_expressions(time, "", j1, "")
    j2 = _node(m, unreal.MaterialExpressionSine, -1700, 2050, period=1.7)
    MEL.connect_material_expressions(time, "", j2, "")
    jj = _node(m, unreal.MaterialExpressionMultiply, -1550, 2000)
    _link(j1, jj, "A")
    _link(j2, jj, "B")
    jamp = _node(m, unreal.MaterialExpressionMultiply, -1400, 2000)
    _link(jj, jamp, "A")
    _link(_scalar(m, "JitterCm", 0.05, -1550, 2150), jamp, "B")
    jvec = _node(m, unreal.MaterialExpressionMultiply, -1250, 1900)
    _link(axis_n, jvec, "A")
    _link(jamp, jvec, "B")
    wpo = _node(m, unreal.MaterialExpressionAdd, -1100, 1600)
    _link(rot, wpo, "A")
    _link(jvec, wpo, "B")
    _output(wpo, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    # --- colour: base + fresnel rim, scan lines, flicker, damage
    fres = _node(m, unreal.MaterialExpressionFresnel, -1700, 300, exponent=2.5, base_reflect_fraction=0.0)
    rim = _node(m, unreal.MaterialExpressionMultiply, -1500, 300)
    _link(fres, rim, "A")
    _link(_scalar(m, "RimStrength", 1.4, -1700, 450), rim, "B")
    shade = _node(m, unreal.MaterialExpressionAdd, -1300, 300)
    _link(rim, shade, "A")
    _link(_scalar(m, "BaseGlow", 0.22, -1500, 450), shade, "B")
    wz = _node(m, unreal.MaterialExpressionComponentMask, -1700, 700, r=False, g=False, b=True, a=False)
    MEL.connect_material_expressions(_node(m, unreal.MaterialExpressionWorldPosition, -1900, 700), "", wz, "")
    lines = _node(m, unreal.MaterialExpressionDivide, -1500, 700)
    _link(wz, lines, "A")
    _link(_scalar(m, "ScanCm", 0.35, -1700, 820), lines, "B")
    roll = _node(m, unreal.MaterialExpressionMultiply, -1500, 900)
    _link(time, roll, "A")
    _link(_scalar(m, "ScanSpeed", 1.5, -1700, 950), roll, "B")
    phase = _node(m, unreal.MaterialExpressionAdd, -1300, 750)
    _link(lines, phase, "A")
    _link(roll, phase, "B")
    wave = _node(m, unreal.MaterialExpressionSine, -1150, 750, period=1.0)
    MEL.connect_material_expressions(phase, "", wave, "")
    sw = _node(m, unreal.MaterialExpressionMultiply, -1000, 750)
    _link(wave, sw, "A")
    _link(_scalar(m, "ScanDepth", 0.25, -1150, 870), sw, "B")
    scan = _node(m, unreal.MaterialExpressionSubtract, -850, 750)
    _link(_node(m, unreal.MaterialExpressionConstant, -1000, 650, r=1.0), scan, "A")
    _link(sw, scan, "B")
    f1 = _node(m, unreal.MaterialExpressionSine, -1150, 1050, period=0.061)
    MEL.connect_material_expressions(time, "", f1, "")
    f2 = _node(m, unreal.MaterialExpressionSine, -1150, 1150, period=0.37)
    MEL.connect_material_expressions(time, "", f2, "")
    ff = _node(m, unreal.MaterialExpressionMultiply, -1000, 1100)
    _link(f1, ff, "A")
    _link(f2, ff, "B")
    fa = _node(m, unreal.MaterialExpressionMultiply, -850, 1100)
    _link(ff, fa, "A")
    _link(_scalar(m, "Flicker", 0.06, -1000, 1220), fa, "B")
    flick = _node(m, unreal.MaterialExpressionAdd, -700, 1100)
    _link(_node(m, unreal.MaterialExpressionConstant, -850, 1000, r=1.0), flick, "A")
    _link(fa, flick, "B")
    vc = _node(m, unreal.MaterialExpressionVertexColor, -1500, 0)
    dmg = _node(m, unreal.MaterialExpressionMultiply, -1300, 0)
    MEL.connect_material_expressions(vc, "R", dmg, "A")
    _link(_scalar(m, "DamageAmount", 0.0, -1500, 100), dmg, "B")
    colour = _node(m, unreal.MaterialExpressionLinearInterpolate, -1100, 0)
    _link(_vector(m, "HoloColor", (0.2, 0.55, 1.0), -1300, -150), colour, "A")
    _link(_vector(m, "DamageColor", (1.0, 0.25, 0.05), -1300, 150), colour, "B")
    _link(dmg, colour, "Alpha")
    c1 = _node(m, unreal.MaterialExpressionMultiply, -900, 100)
    _link(colour, c1, "A")
    _link(_scalar(m, "HoloStrength", 3.0, -1100, 200), c1, "B")
    c2 = _node(m, unreal.MaterialExpressionMultiply, -700, 250)
    _link(c1, c2, "A")
    _link(shade, c2, "B")
    c3 = _node(m, unreal.MaterialExpressionMultiply, -550, 450)
    _link(c2, c3, "A")
    _link(scan, c3, "B")
    c4 = _node(m, unreal.MaterialExpressionMultiply, -400, 600)
    _link(c3, c4, "A")
    _link(flick, c4, "B")
    _output(c4, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    return m


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
    if key in ("normal", "decal_normal"):
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("flip_green_channel", True)
    elif key in ("orm", "ao", "decal_m", "decal_ao"):
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

    # the plate behind a display's clear glass: the hull's parameters plus pixel animation - seen through the
    # clipped glass it takes over the page's pixels as they change, so TSR keeps as little history there as on
    # the page itself
    back = _fresh_material(MASTERS["screenback"])
    back.set_editor_property("has_pixel_animation", True)
    _output(_vector(back, "BaseColor", (0.02, 0.022, 0.026), -600, 0), unreal.MaterialProperty.MP_BASE_COLOR)
    _output(_scalar(back, "Metallic", 0.0, -600, 150), unreal.MaterialProperty.MP_METALLIC)
    _output(_scalar(back, "Roughness", 0.9, -600, 250), unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(back)
    unreal.EditorAssetLibrary.save_loaded_asset(back, only_if_is_dirty=False)

    # a slowly blinking indicator LED (cockpit control modules, step 4): the hull's parameters, the emission
    # pulsing between BlinkMin and 1 at BlinkHz (a soft sine, not a hard flash)
    blink = _fresh_material(MASTERS["blink"])
    _output(_vector(blink, "BaseColor", (0.3, 0.3, 0.3), -900, 0), unreal.MaterialProperty.MP_BASE_COLOR)
    _output(_scalar(blink, "Metallic", 0.0, -900, 150), unreal.MaterialProperty.MP_METALLIC)
    _output(_scalar(blink, "Roughness", 0.3, -900, 250), unreal.MaterialProperty.MP_ROUGHNESS)
    phase = _node(blink, unreal.MaterialExpressionMultiply, -1100, 700)
    _link(_node(blink, unreal.MaterialExpressionTime, -1300, 650), phase, "A")
    _link(_scalar(blink, "BlinkHz", 0.6, -1300, 780), phase, "B")
    wave = _node(blink, unreal.MaterialExpressionSine, -950, 700, period=1.0)
    _link(phase, wave, "")
    half = _node(blink, unreal.MaterialExpressionMultiply, -800, 700)
    _link(wave, half, "A")
    _link(_node(blink, unreal.MaterialExpressionConstant, -950, 800, r=0.5), half, "B")
    pulse = _node(blink, unreal.MaterialExpressionAdd, -650, 700)
    _link(half, pulse, "A")
    _link(_node(blink, unreal.MaterialExpressionConstant, -800, 800, r=0.5), pulse, "B")
    level = _node(blink, unreal.MaterialExpressionLinearInterpolate, -500, 650)
    _link(_scalar(blink, "BlinkMin", 0.08, -700, 600), level, "A")
    _link(_node(blink, unreal.MaterialExpressionConstant, -700, 650, r=1.0), level, "B")
    _link(pulse, level, "Alpha")
    colour = _node(blink, unreal.MaterialExpressionMultiply, -500, 400)
    _link(_vector(blink, "EmissiveColor", (1.0, 0.38, 0.06), -900, 400), colour, "A")
    _link(_scalar(blink, "EmissiveStrength", 6.0, -900, 550), colour, "B")
    emissive = _node(blink, unreal.MaterialExpressionMultiply, -300, 500)
    _link(colour, emissive, "A")
    _link(level, emissive, "B")
    _output(emissive, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(blink)
    unreal.EditorAssetLibrary.save_loaded_asset(blink, only_if_is_dirty=False)

    glass = _fresh_material(MASTERS["glass"])
    glass.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    glass.set_editor_property("two_sided", True)
    # Surface TranslucencyVolume: the reflection environment and Lumen reflections, diffuse from the lighting volume.
    # Forward shading (per-pixel, every local light) cost 1.1 ms once the canopy filled the pilot's view (26. 9. 2026)
    glass.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
    _output(_vector(glass, "BaseColor", (0.25, 0.35, 0.4), -600, 0), unreal.MaterialProperty.MP_BASE_COLOR)
    # a weak reflection seen from the cockpit, a strong one from the chase camera and outside (author 26. 9. 2026):
    # each value has an outside and an inside parameter, MPC_ShipView.InsideView picks between them
    inside = _node(glass, unreal.MaterialExpressionCollectionParameter, -900, 600,
                   collection=_view_collection(), parameter_name="InsideView")
    for i, (name, default, name_in, default_in, prop) in enumerate((
            ("Opacity", 0.2, "OpacityInside", 0.2, unreal.MaterialProperty.MP_OPACITY),
            ("Roughness", 0.03, "RoughnessInside", 0.08, unreal.MaterialProperty.MP_ROUGHNESS),
            ("Specular", 1.0, "SpecularInside", 0.5, unreal.MaterialProperty.MP_SPECULAR))):
        blend = _node(glass, unreal.MaterialExpressionLinearInterpolate, -350, 150 + i * 200)
        _link(_scalar(glass, name, default, -600, 150 + i * 200), blend, "A")
        _link(_scalar(glass, name_in, default_in, -600, 230 + i * 200), blend, "B")
        _link(inside, blend, "Alpha")
        _output(blend, prop)
    MEL.recompile_material(glass)
    unreal.EditorAssetLibrary.save_loaded_asset(glass, only_if_is_dirty=False)
    return {"hull": hull, "pbr": build_pbr_master(), "glass": glass, "screen": build_screen_master(),
            "decal": build_decal_master(), "meshdecal": build_mesh_decal_master(False),
            "meshdecal_paint": build_mesh_decal_master(True), "meshdecal_ao": build_mesh_decal_ao_master(),
            "meshdecal_grime": build_mesh_decal_grime_master(),
            "layered": build_layered_master(), "screenback": back, "blink": blink, "holo": build_holo_master()}


def build_mesh_decal_ao_master():
    """The occlusion of a structural mesh decal (seams, rivets, grilles take the hull's paint): a
    colour-only DBuffer decal, black with opacity (1 - AO) x DecalAOStrength x the item's alpha. DBuffer
    colour blends as lerp(paint, black, opacity), i.e. it darkens whatever paint is under it - AO a DBuffer
    decal cannot write otherwise. Only Base Color and Opacity are connected, so it writes colour and
    nothing else; its quad lies on the normal-only one (hs_decals.py)."""
    m = _fresh_material(MASTERS["meshdecal_ao"])
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    white = "/Engine/EngineResources/WhiteSquareTexture"
    aom = _texture_param(m, "DecalAOMap", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, white, -900, 0)
    mm = _texture_param(m, "DecalMMap", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, white, -900, 300)
    inv = _node(m, unreal.MaterialExpressionOneMinus, -600, 0)
    if not MEL.connect_material_expressions(aom, "R", inv, ""):
        raise RuntimeError("decal AO -> one minus")
    k = _node(m, unreal.MaterialExpressionMultiply, -450, 50)
    _link(inv, k, "A")
    _link(_scalar(m, "DecalAOStrength", 0.9, -900, 500), k, "B")
    a = _node(m, unreal.MaterialExpressionMultiply, -300, 100)
    _link(k, a, "A")
    if not MEL.connect_material_expressions(mm, "R", a, "B"):
        raise RuntimeError("decal M.R -> AO opacity")
    _output(_decal_fade(m, a), unreal.MaterialProperty.MP_OPACITY)
    _output(_vector(m, "DecalAOColor", (0.0, 0.0, 0.0), -600, 300), unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    return m


# Masks of the layered master, shared by its two Custom nodes. VC is the mesh's vertex colour from
# Tools/Blender/hs_layers.py: R ambient occlusion, G 1 - convex edge, B 1 - secondary paint; Amount (A)
# scales the layering (the pilot region has 1, the rest 0; a mesh without vertex colours reads white:
# no AO, no edge, primary paint, full grunge). Grunge: the shared blotch texture, triplanar in the ship's
# own space at two scales.
_LAYER_MASKS = _TRIPLANAR + """
float g1 = w.x * Texture2DSample(TexG, TexGSampler, p.yz).r + w.y * Texture2DSample(TexG, TexGSampler, p.zx).r
         + w.z * Texture2DSample(TexG, TexGSampler, p.xy).r;
float3 q = p * 3.7;
float g2 = w.x * Texture2DSample(TexG, TexGSampler, q.yz).r + w.y * Texture2DSample(TexG, TexGSampler, q.zx).r
         + w.z * Texture2DSample(TexG, TexGSampler, q.xy).r;
float g = saturate(g1 * 0.65 + g2 * 0.35);
float ao = lerp(1.0, VC.r, Amount);
float edge = (1.0 - VC.g) * Amount;
float p2 = 1.0 - VC.b;
float dirt = saturate((1.0 - ao) * 1.8) * saturate(0.3 + g) * DirtAmount * Amount;
// only the most exposed edges, where the grunge is strongest too (clean Origin-like look, 24. 9. 2026)
float wear = saturate((edge * (0.5 + 1.0 * g) - WearThreshold) * 3.0) * EdgeWear;
"""

_LAYER_MASK_NODE = _LAYER_MASKS + """
return float4(g, ao, dirt, wear);
"""

# The colour and surface nodes read the masks from the one mask node (M = g, ao, dirt, wear): the grunge
# texture is sampled once per pixel (six taps), not twice (24. 9. 2026).
# Livery: analytic zones in the ship's own space (cm), crisp at any distance, one set of scalars per
# variant - top saddle (z above TopZ + TopSlope*x), lower zone (z below BotZ + BotSlope*x), tail block
# (x below TailX), nose block (x above NoseX) in the secondary colour; an accent stripe along
# StripeZ + StripeSlope*x, StripeW wide, between StripeX0 and StripeX1. LiveryAmount 0 turns it off (every
# slot but the primary paint).
_LIVERY = """
float3 lp = LocalPos;
float zone = 0.0;
zone = max(zone, step(TopZ + TopSlope * lp.x, lp.z));
zone = max(zone, step(lp.z, BotZ + BotSlope * lp.x));
zone = max(zone, step(lp.x, TailX));
zone = max(zone, step(NoseX, lp.x));
float sz = StripeZ + StripeSlope * lp.x;
float stripe = step(abs(lp.z - sz), StripeW * 0.5) * step(StripeX0, lp.x) * step(lp.x, StripeX1);
"""

# Panel variation: UV1 carries a per-panel random pair (hs_layers.panel_ids): r.x shifts the paint's tone
# and roughness a little, r.y picks a panel class - bare metal (below MetalShare) or carbon (below
# MetalShare + CarbonShare), the rest paint. SC hulls: neighbouring plates never match exactly.
_PANEL = """
float2 r = PanelId;
float isMetal = step(r.y, MetalShare) * step(0.001, r.y);
float isCarbon = step(MetalShare, r.y) * step(r.y, MetalShare + CarbonShare);
float3 cw = frac(LocalPos / 1.2);
float twill = step(0.5, frac((cw.x + cw.y + cw.z) * 3.0 + step(0.5, frac(cw.x * 6.0)) * 0.5));
"""

_LAYER_COLOUR = """
float g = M.x; float ao = M.y; float dirt = M.z; float wear = M.w;
float p2 = 1.0 - VC.b;
""" + _LIVERY + _PANEL + """
float3 paint = lerp(Primary, Secondary, p2);
paint = lerp(paint, LiveryColor, zone * LiveryAmount);
paint = lerp(paint, Accent, stripe * LiveryAmount * (1.0 - zone * 0.0));
paint *= 1.0 + (r.x - 0.5) * PanelTone * Amount;
paint = lerp(paint, MetalPanel, isMetal * Amount * LiveryAmount);
paint = lerp(paint, lerp(float3(0.018, 0.019, 0.021), float3(0.04, 0.042, 0.046), twill), isCarbon * Amount * LiveryAmount);
paint *= lerp(1.0, 0.8 + 0.4 * g, GrungeAmount * Amount);
paint *= lerp(1.0, ao, CavityStrength);
paint = lerp(paint, DirtColor, dirt);
paint = lerp(paint, BareMetal, wear);
return paint;
"""

_LAYER_SURFACE = """
float g = M.x; float ao = M.y; float dirt = M.z; float wear = M.w;
float p2 = 1.0 - VC.b;
""" + _LIVERY + _PANEL + """
float rough = lerp(PrimaryRough, SecondaryRough, max(p2, zone * LiveryAmount));
rough += (r.x - 0.5) * PanelRough * Amount;
rough = lerp(rough, 0.3, isMetal * Amount * LiveryAmount);
rough = lerp(rough, 0.22 + twill * 0.1, isCarbon * Amount * LiveryAmount);
rough = saturate(rough + (g - 0.5) * RoughVariation * Amount);
rough = lerp(rough, 0.85, dirt);
rough = lerp(rough, BareRough, wear);
float metal = lerp(PaintMetal, 1.0, max(wear, isMetal * Amount * LiveryAmount));
return float3(saturate(rough), metal, lerp(1.0, ao, AOStrength));
"""


def build_layered_master():
    """Layered hull paint (step 5 of the SC detail plan, skill ship-pipeline 3b3): primary and secondary
    paint by mask, cavity darkening and dirt from the baked AO, edge wear to bare metal on convex edges
    broken up by grunge, grunge over the paint, all from vertex colours (hs_layers.py) and one tiling
    texture, no per-ship UV textures. Parameters (colours linear): PrimaryColor, SecondaryColor,
    BareMetalColor, DirtColor, PrimaryRoughness, SecondaryRoughness, PaintMetallic, BareMetalRoughness,
    EdgeWear, DirtAmount, GrungeAmount, GrungeTileCm, RoughVariation, CavityStrength, AOStrength,
    EmissiveColor, EmissiveStrength."""
    m = _fresh_material(MASTERS["layered"])
    m.set_editor_property("used_with_nanite", True)
    grunge_tex = import_shared_texture("T_Ship_Detail_Grunge")
    vc = _node(m, unreal.MaterialExpressionVertexColor, -1700, 0)
    local_position = _node(m, unreal.MaterialExpressionLocalPosition, -1700, 200)
    tex = _node(m, unreal.MaterialExpressionTextureObjectParameter, -1700, 350, parameter_name="GrungeMap",
                sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, texture=grunge_tex)
    tile = _scalar(m, "GrungeTileCm", 180.0, -1700, 500)
    params = {
        "Primary": _vector(m, "PrimaryColor", (0.6, 0.57, 0.5), -1700, 650),
        "Secondary": _vector(m, "SecondaryColor", (0.45, 0.44, 0.41), -1700, 800),
        "BareMetal": _vector(m, "BareMetalColor", (0.55, 0.55, 0.57), -1700, 950),
        "DirtColor": _vector(m, "DirtColor", (0.09, 0.08, 0.07), -1700, 1100),
        "GrungeAmount": _scalar(m, "GrungeAmount", 0.5, -1700, 1250),
        "DirtAmount": _scalar(m, "DirtAmount", 0.6, -1700, 1350),
        "EdgeWear": _scalar(m, "EdgeWear", 0.8, -1700, 1450),
        "CavityStrength": _scalar(m, "CavityStrength", 0.5, -1700, 1550),
        "PrimaryRough": _scalar(m, "PrimaryRoughness", 0.42, -1700, 1650),
        "SecondaryRough": _scalar(m, "SecondaryRoughness", 0.5, -1700, 1750),
        "PaintMetal": _scalar(m, "PaintMetallic", 0.0, -1700, 1850),
        "BareRough": _scalar(m, "BareMetalRoughness", 0.3, -1700, 1950),
        "RoughVariation": _scalar(m, "RoughVariation", 0.2, -1700, 2050),
        "AOStrength": _scalar(m, "AOStrength", 0.8, -1700, 2150),
        "WearThreshold": _scalar(m, "WearThreshold", 0.45, -1700, 2250),
        "Accent": _vector(m, "AccentColor", (0.72, 0.17, 0.02), -1900, 650),
        "MetalPanel": _vector(m, "MetalPanelColor", (0.6, 0.6, 0.62), -1900, 800),
        "LiveryColor": _vector(m, "LiveryColor", (0.05, 0.053, 0.058), -1900, 950),
    }
    for i, (pname, default) in enumerate((("LiveryAmount", 0.0), ("TopZ", 9999.0), ("TopSlope", 0.0), ("BotZ", -9999.0),
                                          ("BotSlope", 0.0), ("TailX", -9999.0), ("NoseX", 9999.0), ("StripeZ", 0.0),
                                          ("StripeSlope", 0.0), ("StripeW", 0.0), ("StripeX0", -9999.0), ("StripeX1", 9999.0),
                                          ("PanelTone", 0.06), ("PanelRough", 0.1), ("MetalShare", 0.0), ("CarbonShare", 0.0))):
        params[pname] = _scalar(m, pname, default, -2100, 650 + i * 100)
    panel_uv = _node(m, unreal.MaterialExpressionTextureCoordinate, -1900, 2400, coordinate_index=1)
    mask_in = ["VC", "Amount", "LocalPos", "TexG", "Tile", "DirtAmount", "EdgeWear", "WearThreshold"]
    masks = _custom(m, "Layered_masks", _LAYER_MASK_NODE, unreal.CustomMaterialOutputType.CMOT_FLOAT4, mask_in, -1250, 300)
    if not MEL.connect_material_expressions(vc, "", masks, "VC"):
        raise RuntimeError("vertex colour -> masks")
    if not MEL.connect_material_expressions(vc, "A", masks, "Amount"):
        raise RuntimeError("vertex colour A -> masks")
    _link(local_position, masks, "LocalPos")
    _link(tex, masks, "TexG")
    _link(tile, masks, "Tile")
    for name in mask_in[5:]:
        _link(params[name], masks, name)
    livery_in = ["LocalPos", "PanelId", "LiveryAmount", "TopZ", "TopSlope", "BotZ", "BotSlope", "TailX", "NoseX", "StripeZ",
                 "StripeSlope", "StripeW", "StripeX0", "StripeX1", "MetalShare", "CarbonShare"]
    colour_in = ["M", "VC", "Amount", "Primary", "Secondary", "BareMetal", "DirtColor", "GrungeAmount", "CavityStrength",
                 "Accent", "MetalPanel", "PanelTone", "LiveryColor"] + livery_in
    surface_in = ["M", "VC", "Amount", "PrimaryRough", "SecondaryRough", "PaintMetal", "BareRough", "AOStrength", "RoughVariation",
                  "PanelRough"] + livery_in
    nodes = {}
    for key, code, names, y in (("colour", _LAYER_COLOUR, colour_in, 0), ("surface", _LAYER_SURFACE, surface_in, 700)):
        node = _custom(m, "Layered_" + key, code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, names, -900, y)
        _link(masks, node, "M")
        if not MEL.connect_material_expressions(vc, "", node, "VC"):
            raise RuntimeError("vertex colour -> " + key)
        if not MEL.connect_material_expressions(vc, "A", node, "Amount"):
            raise RuntimeError("vertex colour A -> " + key)
        for name in names[3:]:
            if name == "LocalPos":
                _link(local_position, node, name)
            elif name == "PanelId":
                _link(panel_uv, node, name)
            else:
                _link(params[name], node, name)
        nodes[key] = node
    # everything through one Make Material Attributes node: the Python enum has no clear-coat pins
    mk = _node(m, unreal.MaterialExpressionMakeMaterialAttributes, -300, 600)
    m.set_editor_property("use_material_attributes", True)
    _link(nodes["colour"], mk, "BaseColor")
    for i, (channel, prop) in enumerate((("r", unreal.MaterialProperty.MP_ROUGHNESS), ("g", unreal.MaterialProperty.MP_METALLIC),
                                         ("b", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION))):
        mask = _node(m, unreal.MaterialExpressionComponentMask, -600, 700 + i * 120,
                     r=channel == "r", g=channel == "g", b=channel == "b", a=False)
        _link(nodes["surface"], mask, "")
        _link(mask, mk, {"r": "Roughness", "g": "Metallic", "b": "AmbientOcclusion"}[channel])
    emissive = _node(m, unreal.MaterialExpressionMultiply, -600, 1200)
    _link(_vector(m, "EmissiveColor", (0.0, 0.0, 0.0), -900, 1200), emissive, "A")
    _link(_scalar(m, "EmissiveStrength", 0.0, -900, 1350), emissive, "B")
    _link(emissive, mk, "EmissiveColor")
    # Origin-like finish: a clear coat over the paint that mirrors the environment (ClearCoat 0 = off)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_CLEAR_COAT)
    _link(_scalar(m, "ClearCoat", 0.0, -900, 1500), mk, "ClearCoat")
    # the clear coat's gloss varies with the grunge and dies in the dirt (SC breakdown, 26. 9. 2026: the smudges
    # show in the reflections; a constant clear-coat roughness mirrored the sky the same everywhere)
    ccr = _custom(m, "ClearCoatRough", "return saturate(Base + (M.x - 0.5) * Var + M.z * 0.5);",
                  unreal.CustomMaterialOutputType.CMOT_FLOAT1, ["M", "Base", "Var"], -600, 1600)
    _link(masks, ccr, "M")
    _link(_scalar(m, "ClearCoatRoughness", 0.06, -900, 1600), ccr, "Base")
    _link(_scalar(m, "ClearCoatRoughVariation", 0.0, -900, 1700), ccr, "Var")
    _link(ccr, mk, "ClearCoatRoughness")
    _output(mk, unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    return m


def _decal_fade(m, opacity, x=-350, y=1100):
    """Opacity x a smooth fade with camera distance: 1 up to DecalFadeStartCm, 0 at DecalFadeEndCm. The
    Decals component's draw distance lies just past the end, so the part disappears without a pop."""
    dist = _node(m, unreal.MaterialExpressionCameraPositionWS, x - 500, y)
    wp = _node(m, unreal.MaterialExpressionWorldPosition, x - 500, y + 100)
    d = _node(m, unreal.MaterialExpressionDistance, x - 350, y)
    _link(dist, d, "A")
    _link(wp, d, "B")
    end = _scalar(m, "DecalFadeEndCm", 9000.0, x - 500, y + 250)
    start = _scalar(m, "DecalFadeStartCm", 6000.0, x - 500, y + 350)
    num = _node(m, unreal.MaterialExpressionSubtract, x - 200, y)
    _link(end, num, "A")
    _link(d, num, "B")
    den = _node(m, unreal.MaterialExpressionSubtract, x - 200, y + 200)
    _link(end, den, "A")
    _link(start, den, "B")
    ratio = _node(m, unreal.MaterialExpressionDivide, x - 100, y)
    _link(num, ratio, "A")
    _link(den, ratio, "B")
    fade = _node(m, unreal.MaterialExpressionSaturate, x, y)
    _link(ratio, fade, "")
    out = _node(m, unreal.MaterialExpressionMultiply, x + 120, y - 100)
    _link(opacity, out, "A")
    _link(fade, out, "B")
    return out


def build_mesh_decal_master(paint):
    """Mesh decals (Tools/Blender/decal_library.py atlas on quads a hair above the hull, their own non-Nanite
    part): a static mesh with a Deferred Decal material, drawn into the DBuffer (r.DBuffer is on). The engine
    derives what the decal writes from the connected pins, so there are two masters:
      meshdecal        normal + roughness + metallic only - seams, grilles, bolts keep the hull's paint;
      meshdecal_paint  also base colour (labels, stripes, parts with their own colour; baked AO in it),
                       opacity x DecalColorMap alpha, as a second quad over the normal-only one.
    Textures: DecalNormalMap (tangent, OpenGL -> flip green on import), DecalMMap (R alpha = where the decal
    applies, G roughness, B metallic), DecalColorMap (sRGB). DecalNormalStrength flattens the normal."""
    m = _fresh_material(MASTERS["meshdecal_paint" if paint else "meshdecal"])
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    white = "/Engine/EngineResources/WhiteSquareTexture"
    nmap = _texture_param(m, "DecalNormalMap", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                          "/Engine/EngineMaterials/DefaultNormal", -900, 0)
    flat = _node(m, unreal.MaterialExpressionConstant3Vector, -900, 200, constant=unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    strength = _node(m, unreal.MaterialExpressionLinearInterpolate, -500, 100)
    _link(flat, strength, "A")
    _link(nmap, strength, "B")
    _link(_scalar(m, "DecalNormalStrength", 1.0, -900, 300), strength, "Alpha")
    _output(strength, unreal.MaterialProperty.MP_NORMAL)
    mm = _texture_param(m, "DecalMMap", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, white, -900, 450)
    rough = _node(m, unreal.MaterialExpressionMultiply, -500, 450)
    if not MEL.connect_material_expressions(mm, "G", rough, "A"):
        raise RuntimeError("decal M.G -> roughness")
    _link(_scalar(m, "DecalRoughnessScale", 1.0, -900, 650), rough, "B")
    _output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
    if not MEL.connect_material_property(mm, "B", unreal.MaterialProperty.MP_METALLIC):
        raise RuntimeError("decal M.B -> metallic")
    opacity = _node(m, unreal.MaterialExpressionMultiply, -500, 800)
    if not MEL.connect_material_expressions(mm, "R", opacity, "A"):
        raise RuntimeError("decal M.R -> opacity")
    _link(_scalar(m, "DecalOpacity", 1.0, -900, 850), opacity, "B")
    if paint:
        # colour only where the item has its own (DecalColorMap alpha: labels, recess floors, slats,
        # bolts); a DBuffer decal has one opacity for all it writes, so the paint quad sits on top of
        # the normal-only one and covers just those parts
        col = _texture_param(m, "DecalColorMap", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, white, -900, 1000)
        _output(col, unreal.MaterialProperty.MP_BASE_COLOR)
        own = _node(m, unreal.MaterialExpressionMultiply, -350, 850)
        _link(opacity, own, "A")
        if not MEL.connect_material_expressions(col, "A", own, "B"):
            raise RuntimeError("decal BC.A -> opacity")
        opacity = own
    _output(_decal_fade(m, opacity), unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    return m


def build_mesh_decal_grime_master():
    """Large grime cards (hs_decals rule "grime", Tools/Assets/generate_grime_textures.py; from the SC breakdown,
    26. 9. 2026): colour and roughness only - no normal pin, so the hull's panel detail and the structural decals
    under a card stay as they are. DecalColorMap (sRGB grime colour, alpha = coverage), DecalMMap (R = applies,
    G roughness), opacity = alpha x R x DecalOpacity, faded with distance like the other mesh decals."""
    m = _fresh_material(MASTERS["meshdecal_grime"])
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    white = "/Engine/EngineResources/WhiteSquareTexture"
    col = _texture_param(m, "DecalColorMap", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, white, -900, 0)
    _output(col, unreal.MaterialProperty.MP_BASE_COLOR)
    mm = _texture_param(m, "DecalMMap", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, white, -900, 300)
    rough = _node(m, unreal.MaterialExpressionMultiply, -500, 300)
    if not MEL.connect_material_expressions(mm, "G", rough, "A"):
        raise RuntimeError("grime M.G -> roughness")
    _link(_scalar(m, "DecalRoughnessScale", 1.0, -900, 500), rough, "B")
    _output(rough, unreal.MaterialProperty.MP_ROUGHNESS)
    cover = _node(m, unreal.MaterialExpressionMultiply, -500, 650)
    if not MEL.connect_material_expressions(col, "A", cover, "A"):
        raise RuntimeError("grime BC.A -> opacity")
    if not MEL.connect_material_expressions(mm, "R", cover, "B"):
        raise RuntimeError("grime M.R -> opacity")
    # x vertex colour alpha: 0 along the edges where hs_decals dropped cells off the surface
    vc = _node(m, unreal.MaterialExpressionVertexColor, -900, 950)
    soft = _node(m, unreal.MaterialExpressionMultiply, -500, 850)
    _link(cover, soft, "A")
    if not MEL.connect_material_expressions(vc, "A", soft, "B"):
        raise RuntimeError("grime VC.A -> opacity")
    opacity = _node(m, unreal.MaterialExpressionMultiply, -350, 700)
    _link(soft, opacity, "A")
    _link(_scalar(m, "DecalOpacity", 0.5, -900, 800), opacity, "B")
    _output(_decal_fade(m, opacity), unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    return m


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
                       ("decal_normal_strength", "DecalNormalStrength"), ("decal_opacity", "DecalOpacity"),
                       ("decal_ao_strength", "DecalAOStrength"),
                       ("decal_roughness_scale", "DecalRoughnessScale"),
                       ("roughness_scale", "RoughnessScale"), ("metallic_scale", "MetallicScale"),
                       ("detail_tile_cm", "DetailTileCm"), ("detail_normal_strength", "DetailNormalStrength"),
                       ("detail_grunge_tile_cm", "DetailGrungeTileCm"), ("detail_rough_variation", "DetailRoughVariation"),
                       ("cavity_strength", "CavityStrength"), ("ao_strength", "AOStrength"),
                       ("wear_amount", "WearAmount"), ("wear_threshold", "WearThreshold"), ("wear_metallic", "WearMetallic"),
                       ("panel_tile_cm", "PanelTileCm"), ("panel_strength", "PanelStrength"),
                       ("panel_seam_darken", "PanelSeamDarken"), ("panel_seam_rough", "PanelSeamRough"),
                       ("scorch_amount", "ScorchAmount"), ("scorch_start_cm", "ScorchStartCm"),
                       ("scorch_end_cm", "ScorchEndCm"), ("scorch_rough", "ScorchRough"),
                       ("blink_hz", "BlinkHz"), ("blink_min", "BlinkMin")):
        if key in spec:
            MEL.set_material_instance_scalar_parameter_value(mi, param, float(spec[key]))
    for key, param in (("base_color_tint", "BaseColorTint"), ("wear_color", "WearColor"), ("scorch_color", "ScorchColor")):
        if key in spec:
            c = spec[key]
            MEL.set_material_instance_vector_parameter_value(mi, param, unreal.LinearColor(c[0], c[1], c[2], 1.0))
    # any parameter by its name (the layered master has many): "vectors" {name: [r, g, b]}, "scalars" {name: v}
    for name, c in (spec.get("vectors") or {}).items():
        MEL.set_material_instance_vector_parameter_value(mi, name, unreal.LinearColor(c[0], c[1], c[2], 1.0))
    for name, v in (spec.get("scalars") or {}).items():
        MEL.set_material_instance_scalar_parameter_value(mi, name, float(v))
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
