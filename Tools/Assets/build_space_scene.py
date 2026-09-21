"""Builds the space look of TestSpace: star sky (stars, nebulae, sun disc), test planet, a moon and a
ringed gas giant in the distance, sun, exposure, and the ship's space dust material.

Two steps, editor closed:

    python Tools/Assets/generate_milky_way_glow.py Intermediate/GeneratedAssets/milky_way_glow.hdr
    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\build_space_scene.py

Re-runnable. Assets and level actors this script owns are updated in place: materials are
rebuilt from the graph below and actors are found by label. Imported source assets (glow
cubemap, planet mesh) are imported once and then left alone. Nothing else in the level is
touched. The level's one SkyAtmosphere belongs to Veyra (Atmosphere_Veyra, sized to the planet);
any other is removed - the engine's default is an Earth-sized sky and horizon, the opposite of space.
"""

import math
import os

import unreal

import gamespace_assets as ga

# ---------------------------------------------------------------------------------------
# Tuning
# ---------------------------------------------------------------------------------------

# Fixed exposure. Auto exposure would brighten a mostly black star field until the stars
# bloom out, then darken again whenever a lit asteroid fills the view.
EXPOSURE_EV100 = 3.0

# How the ship is lit (found on 20. 9. 2026 with Tools/Shots/look_sun.json and look_fill.json:
# in space the ship was a silhouette, because almost nothing filled its shadow side).
#   SKY_LIGHT_INTENSITY - the fill. 0.35 left the hull black against space; above ~1.1 the
#     planet loses its terminator. 0.7 with lighter paint (Vanguard_setup.json) is the balance.
#   SUN_CONTACT_SHADOW_M - small shadows in the panel gaps, in metres of screen ray.
#   SUN_SOURCE_ANGLE_DEG - how wide the sun is, i.e. how soft the terminator is.
SKY_LIGHT_INTENSITY = 0.7
SUN_CONTACT_SHADOW_M = 0.08
SUN_SOURCE_ANGLE_DEG = 0.5

# The grade, in the unbound volume together with the exposure. Restrained on purpose: a little
# contrast and saturation, a hint of blue in the highlights, film grain and a vignette for the
# filmic feel of the Star Citizen references. Two settings were tried and dropped, both because
# of the cockpit: chromatic aberration (scene_fringe_intensity) drew colour fringes along the
# dashboard's edges, and white balance (white_temp) turned the whole interior blue.
# Tune them in the running game with space.Post / space.Sun / space.Sky, then space.PostDump
# prints these lines (Source/gamespace/SpacePostTuning.cpp, Docs/WORKFLOW.md kapitola 11).
POST_SETTINGS = (
    ("color_contrast", unreal.Vector4(1.08, 1.08, 1.08, 1.0)),
    ("color_gain", unreal.Vector4(1.0, 1.0, 1.04, 1.0)),
    ("color_saturation", unreal.Vector4(1.06, 1.06, 1.06, 1.0)),
    ("bloom_intensity", 0.45),
    ("film_grain_intensity", 0.2),
    ("vignette_intensity", 0.35),
)

# Stars are computed per pixel in the sky material (see STAR_HLSL). Brightness scales every
# star; density scales how many there are (1.0 is roughly 45k over the whole sky).
STAR_BRIGHTNESS = 8.0
STAR_DENSITY = 1.0

# The diffuse Milky Way band. Kept faint: it is a hint of structure, not a light source.
GLOW_BRIGHTNESS = 0.06

# Coloured nebula clouds in three regions of the sky (see NEBULA_HLSL). At the fixed exposure
# ~10 is white, so the brightest wisps reach roughly a third of that. ASkyDome.NebulaScale
# scales it in the level without rebuilding.
NEBULA_BRIGHTNESS = 3.0

# The sun disc drawn by the sky, pointed at the directional light by ASkyDome. The disc is far
# above white so it blooms; the glow is a corona fading over ~20 degrees.
SUN_DISC_BRIGHTNESS = 400.0
SUN_GLOW_BRIGHTNESS = 25.0

# Star twinkle defaults; ASkyDome drives the parameter between its SpaceTwinkle and
# AtmosphereTwinkle.
STAR_TWINKLE = 0.12

# Sky dome radius. The dome (ASkyDome) follows the camera and the stars are looked up by view
# direction, so the size does not change how the sky looks. It must exceed the distance to the
# farthest body that should be visible: anything beyond it is hidden behind the dome.
SKY_DOME_RADIUS_KM = 2000.0

# Planet: radius 25 km, centre 45 km straight ahead of PlayerStart (which faces +X), so the ship
# starts 20 km above sea level - above the 12 km atmosphere, in "orbit". The planet fills ~67
# degrees of view. Descent at the 300 m/s boost cap takes a bit over a minute to the atmosphere
# edge. The sky dome (1000 km) stays far outside everything here.
PLANET_NAME = "Veyra"
PLANET_RADIUS_CM = 25_000_00
PLANET_LOCATION_CM = (45_000_00, 0, 0)

# Sun from behind the player's left shoulder, so the planet is seen about three-quarters lit.
SUN_PITCH, SUN_YAW = -39.0, 45.0

# Distant bodies (ADistantBody): scenery with real parallax, no gravity. Both stay well inside the
# sky dome. Directions are chosen to be in view from PlayerStart (facing +X) beside Veyra and
# at least half lit by the sun.
MOON_NAME = "Keth"
MOON_RADIUS_KM = 6.0
MOON_ORBIT = {"orbit_radius_km": 150.0, "orbit_period_seconds": 1500.0, "orbit_inclination_deg": -15.0,
              "orbit_node_deg": 30.0, "orbit_phase_deg": -100.0}
GIANT_NAME = "Orun"
GIANT_RADIUS_KM = 150.0
GIANT_RING_OUTER_KM = 330.0
GIANT_RING_INNER_FRACTION = 0.55   # of the outer radius; must clear the planet (150 / 330 = 0.45)
GIANT_DISTANCE_KM = 620.0
GIANT_YAW_DEG, GIANT_ELEVATION_DEG = 70.0, 10.0
GIANT_AXIAL_TILT_DEG = 18.0
GIANT_SPIN_SECONDS = 1800.0

# Veyra's atmosphere: the engine's SkyAtmosphere, sized to the planet (21. 9. 2026, after the planet
# reference video: a thin bright limb from space, hazy layered distance and a coloured sky from the
# surface - starcitizenreference/Planets_VideoNotes.md). Earth's coefficients are per km over an
# 8 km scale height and a 6400 km planet; Veyra is 25 km across with a 3 km scale height, so the
# coefficients are raised until the optical depth matches: blue zenith ~1.2 as on Earth, and dust
# (Mie) three times Earth's for a desert. Aerial perspective is stretched for the same reason: the
# horizon here is kilometres away, not a hundred.
ATMO_HEIGHT_KM = 12.0
ATMO_RAYLEIGH_SCALE = 0.09            # Earth 0.0331; 0.16 painted the desert blue-violet
ATMO_RAYLEIGH_COLOR = (0.175, 0.409, 1.0)   # Earth's ratios (0.0058, 0.0135, 0.0331 per km)
ATMO_RAYLEIGH_HEIGHT_KM = 1.5         # Earth 8; 3 km made a halo as thick as a tenth of the planet
ATMO_MIE_SCALE = 0.07                 # Earth 0.003996: a dusty desert, the haze in its dust colour
ATMO_MIE_COLOR = (1.0, 0.75, 0.5)     # warm dust
ATMO_MIE_HEIGHT_KM = 0.6
ATMO_MIE_ANISOTROPY = 0.8
ATMO_GROUND_ALBEDO = (0.45, 0.36, 0.28)
# The atmosphere's own ground sits this far below sea level. At sea level, rays just over the real
# horizon hit that virtual ground wherever the terrain is higher, and the horizon had a black band.
ATMO_GROUND_BELOW_SEA_KM = 2.0
ATMO_AERIAL_DISTANCE_SCALE = 16.0     # layered distance within a few km, as in the reference
# Sky material: how much of the atmosphere's light to add over the stars, and how fast the stars
# go behind it (1 / luminance at which they are gone).
ATMO_SKY_SCALE = 4.0
ATMO_STAR_FADE = 4.0
# The painted sky gradient mixed back in, in the planet's dusty colours. Not for its looks alone: the
# sky light's capture gets no light from the atmosphere node, and without the painted sky the ship
# on the ground had no fill at all and was black even at five times the sky light (ship_dark_probe,
# 21. 9. 2026). It also pales the sky towards the reference's dusty desert skies.
PAINTED_SKY_AMOUNT = 0.4
PAINTED_SKY_ZENITH = (0.30, 0.40, 0.58)
PAINTED_SKY_HORIZON = (0.78, 0.72, 0.64)

# Space dust around the ship camera (USpaceDustComponent).
DUST_COLOR = (0.70, 0.80, 1.00)
DUST_BRIGHTNESS = 1.8  # 3.0 until 19. 9. 2026 (bright white sticks), 1.6, then 5.0 when the material began
                       # tapering every speck to a point; 2.5 since the quantum reference video (21. 9. 2026):
                       # outside quantum Star Citizen's dust is only a hint of motion. 1.8 when the hull
                       # sparks (USpaceHullSparksComponent) took over the speed lines near the ship.

# ---------------------------------------------------------------------------------------

LEVEL = "/Game/Maps/TestSpace"
GLOW_TEXTURE = "/Game/Environments/Space/T_MilkyWay_Glow_Cube"
STARFIELD_MATERIAL = "/Game/Environments/Space/M_Starfield_Sky"
DUST_MATERIAL = "/Game/Environments/Space/M_SpaceDust"
TUNNEL_MATERIAL = "/Game/Environments/Space/M_SpeedTunnel"
FOG_MATERIAL = "/Game/Environments/Space/M_QuantumFog"
GAS_GIANT_MATERIAL = "/Game/Environments/Space/M_GasGiant"
MOON_MATERIAL = "/Game/Environments/Space/M_Moon"
RINGS_MATERIAL = "/Game/Environments/Space/M_PlanetRings"
PLANET_MESH = "/Game/Planets/SM_PlanetSphere"
PLANET_MATERIAL = "/Game/Planets/M_Planet_Terrain"

MEL = unreal.MaterialEditingLibrary
GENERATED = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_intermediate_dir()), "GeneratedAssets")


def log(msg):
    unreal.log("build_space_scene: " + msg)


# ---------------------------------------------------------------------------------------
# Source assets
# ---------------------------------------------------------------------------------------


def write_sphere_obj(path, radius=100.0, segments=256, rings=128):
    """UV sphere, 1 unit = 1 cm. The engine's basic sphere has 960 triangles, which shows as a
    faceted silhouette on a 500 m planet; this one has ~65k."""
    lines = []
    for r in range(rings + 1):
        theta = math.pi * r / rings
        for s in range(segments + 1):
            phi = 2.0 * math.pi * s / segments
            n = (math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta))
            lines.append("v %.5f %.5f %.5f" % (n[0] * radius, n[1] * radius, n[2] * radius))
            lines.append("vn %.5f %.5f %.5f" % n)
            lines.append("vt %.5f %.5f" % (s / segments, 1.0 - r / rings))
    row = segments + 1
    for r in range(rings):
        for s in range(segments):
            a, b = r * row + s + 1, r * row + s + 2
            c, d = a + row, b + row
            if r != 0:
                lines.append("f %d/%d/%d %d/%d/%d %d/%d/%d" % (a, a, a, c, c, c, b, b, b))
            if r != rings - 1:
                lines.append("f %d/%d/%d %d/%d/%d %d/%d/%d" % (b, b, b, c, c, c, d, d, d))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def import_sources():
    hdr = os.path.join(GENERATED, "milky_way_glow.hdr")
    if not ga.existing_or_none(GLOW_TEXTURE) and not os.path.isfile(hdr):
        raise RuntimeError("%s missing - run Tools/Assets/generate_milky_way_glow.py first" % hdr)
    cube = ga.import_file(GLOW_TEXTURE, hdr, on_exists="skip",
                          properties={"lod_group": unreal.TextureGroup.TEXTUREGROUP_SKYBOX})
    if not isinstance(cube, unreal.TextureCube):
        raise RuntimeError("%s imported as %s, expected TextureCube" % (GLOW_TEXTURE, cube.get_class().get_name()))

    mesh = ga.existing_or_none(PLANET_MESH)
    if mesh is None:
        os.makedirs(GENERATED, exist_ok=True)
        obj = os.path.join(GENERATED, "planet_sphere.obj")
        write_sphere_obj(obj)
        mesh = ga.import_file(PLANET_MESH, obj)
    ensure_sphere_collision(mesh)
    ensure_sphere_not_nanite(mesh)
    return cube, mesh


def ensure_sphere_not_nanite(mesh):
    """The distant bodies (Orun, Keth) are this sphere scaled to 6-150 km. With Nanite on, their
    silhouettes came out as visible straight edges - a polygon, not a planet (quantum shots, 21. 9.
    2026). The plain mesh keeps all 256 segments, which is round even with Orun filling half the view."""
    settings = mesh.get_editor_property("nanite_settings")
    if not settings.get_editor_property("enabled"):
        return
    settings.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", settings)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    log("planet mesh: Nanite off (round silhouettes)")


def ensure_sphere_collision(mesh):
    """Replace the importer's convex hull with one exact sphere, so the ship's swept movement
    meets the actual surface rather than a simplified hull.

    Written straight into the BodySetup: the collision helpers on StaticMeshEditorSubsystem /
    EditorStaticMeshLibrary refuse to run in the headless commandlet and just return -1.
    """
    body = mesh.get_editor_property("body_setup")
    agg = body.get_editor_property("agg_geom")
    spheres = agg.get_editor_property("sphere_elems")
    if (len(spheres) == 1 and abs(spheres[0].get_editor_property("radius") - 100.0) < 0.01
            and not agg.get_editor_property("convex_elems") and not agg.get_editor_property("box_elems")):
        return
    sphere = unreal.KSphereElem()
    sphere.set_editor_property("radius", 100.0)  # matches write_sphere_obj
    agg.set_editor_property("sphere_elems", [sphere])
    agg.set_editor_property("convex_elems", [])
    agg.set_editor_property("box_elems", [])
    agg.set_editor_property("sphyl_elems", [])
    body.set_editor_property("agg_geom", agg)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    log("planet mesh collision set to one sphere, radius 100")


# ---------------------------------------------------------------------------------------
# Materials (script-owned: the graph is rebuilt on every run)
# ---------------------------------------------------------------------------------------


def fresh_material(path):
    material = ga.existing_or_none(path)
    if material is None:
        folder, name = path.rsplit("/", 1)
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.Material, unreal.MaterialFactoryNew())
    else:
        # delete_all_material_expressions() leaves nodes behind when run headless, so the graph
        # grew on every run. Delete one by one and check the graph really is empty.
        for expr in list(MEL.get_material_expressions(material)):
            MEL.delete_material_expression(material, expr)
        left = MEL.get_num_material_expressions(material)
        if left:
            raise RuntimeError("%s still has %d expression(s) after clearing" % (path, left))
    return material


def node(material, cls, x, y, **properties):
    expr = MEL.create_material_expression(material, cls, x, y)
    for key, value in properties.items():
        expr.set_editor_property(key, value)
    return expr


def link(src, dst, dst_input, src_output=""):
    if not MEL.connect_material_expressions(src, src_output, dst, dst_input):
        raise RuntimeError("could not connect %s.%r -> %s.%r" % (
            src.get_class().get_name(), src_output, dst.get_class().get_name(), dst_input))


def output(src, prop, src_output=""):
    if not MEL.connect_material_property(src, src_output, prop):
        raise RuntimeError("could not connect %s.%r -> %s" % (src.get_class().get_name(), src_output, prop))


def finish(material):
    MEL.layout_material_expressions(material)
    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    log("built %s (%d nodes)" % (material.get_path_name(), MEL.get_num_material_expressions(material)))


# Procedural stars, evaluated per pixel. Each of three layers splits every cube face into a
# grid; a hash decides whether a cell holds a star, where in the cell, how bright and what
# colour. The star is drawn as a Gaussian whose width is measured in screen pixels (from the
# derivative of the view direction), so it is a crisp ~1-2 px point at any resolution and
# field of view - unlike a texture, whose texels are larger than pixels. The 3x3 neighbour
# loop lets stars near a cell edge spill into the next cell without being clipped.
STAR_HLSL = r"""
float3 d = normalize(Dir);
// Radians per pixel. Derived from the direction itself, which is continuous across cube faces
// (derivatives of per-face coordinates would jump at every face edge).
float pixelAngle = max(0.5 * (length(ddx(d)) + length(ddy(d))), 1e-5);

float3 ad = abs(d);
int face;
float2 uv;
if (ad.x >= ad.y && ad.x >= ad.z) { face = d.x > 0 ? 0 : 1; uv = d.yz / ad.x; }
else if (ad.y >= ad.z)            { face = d.y > 0 ? 2 : 3; uv = d.xz / ad.y; }
else                              { face = d.z > 0 ? 4 : 5; uv = d.xy / ad.z; }

// More stars along the Milky Way plane (same 62 degree tilt as the glow texture, sigma 9 deg).
float3 bandNormal = float3(0.0, -0.8829, 0.4695);
float bandLat = asin(clamp(dot(d, bandNormal), -1.0, 1.0)) / 0.157;
float band = exp(-0.5 * bandLat * bandLat);

float3 result = 0;
for (int layer = 0; layer < 3; layer++)
{
    float cells = floor(36.0 * pow(2.6, layer));
    // Fewer stars per cell in the finer layers: the fine layers fill in faint background stars,
    // the coarse layer carries the few bright ones.
    float chance = (layer == 0 ? 0.45 : layer == 1 ? 0.26 : 0.12) * Density * (0.5 + 1.4 * band);
    float layerFlux = Brightness * 6.0 * pow(0.3, layer);
    float2 baseCell = floor((uv * 0.5 + 0.5) * cells);

    for (int oy = -1; oy <= 1; oy++)
    {
        for (int ox = -1; ox <= 1; ox++)
        {
            float2 cell = baseCell + float2(ox, oy);
            if (cell.x < 0.0 || cell.y < 0.0 || cell.x >= cells || cell.y >= cells) continue;

            uint3 v = uint3(uint(cell.x), uint(cell.y), uint(face + 8 * layer + 1));
            v = v * 1664525u + 1013904223u;
            v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
            v ^= v >> 16u;
            v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
            float3 h = float3(v) * (1.0 / 4294967295.0);
            if (h.z > chance) continue;

            uint3 w = v * 1664525u + 1013904223u;
            w.x += w.y * w.z; w.y += w.z * w.x; w.z += w.x * w.y;
            w ^= w >> 16u;
            w.x += w.y * w.z; w.y += w.z * w.x; w.z += w.x * w.y;
            float3 h2 = float3(w) * (1.0 / 4294967295.0);

            float2 s = ((cell + 0.1 + 0.8 * h.xy) / cells) * 2.0 - 1.0;
            float3 sd = face == 0 ? float3( 1.0, s.x, s.y) : face == 1 ? float3(-1.0, s.x, s.y)
                      : face == 2 ? float3(s.x,  1.0, s.y) : face == 3 ? float3(s.x, -1.0, s.y)
                      : face == 4 ? float3(s.x, s.y,  1.0) : float3(s.x, s.y, -1.0);
            sd = normalize(sd);

            float r = length(d - sd) / pixelAngle;   // distance to the star in pixels
            float core = exp(-2.2 * r * r);          // about 1.1 px across
            if (core < 0.002) continue;

            // Steep distribution: most stars faint, a handful bright - the contrast that makes
            // a real sky read as depth rather than as uniform noise.
            float flux = layerFlux * lerp(0.03, 1.0, pow(h2.x, 8.0));
            // Twinkle: two slow sines per star at its own rates and phases.
            float twinkle = 0.5 * sin(Time * (2.3 + 7.0 * h2.z) + h.x * 6283.0) + 0.5 * sin(Time * (5.1 + 11.0 * h.y) + h2.x * 628.3);
            flux *= max(0.0, 1.0 + Twinkle * twinkle);
            float3 tint = h2.y < 0.5
                ? lerp(float3(1.0, 0.72, 0.48), float3(1.0, 0.97, 0.93), h2.y * 2.0)
                : lerp(float3(1.0, 0.97, 0.93), float3(0.72, 0.83, 1.0), h2.y * 2.0 - 1.0);
            result += core * flux * tint;
        }
    }
}
return result;
"""


def custom(material, code, inputs, x, y, description, output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3):
    expr = node(material, unreal.MaterialExpressionCustom, x, y, code=code, description=description, output_type=output_type)
    pins = []
    for name in inputs:
        custom_pin = unreal.CustomInput()  # struct constructors take no keyword arguments
        custom_pin.set_editor_property("input_name", name)
        pins.append(custom_pin)
    expr.set_editor_property("inputs", pins)
    return expr


def scalar(material, name, value, x, y):
    return node(material, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=value)


def vector(material, name, rgb, x, y):
    return node(material, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))


def sun_direction():
    """Unit vector towards the sun for the directional light's pitch and yaw (the light shines the other way)."""
    pitch, yaw = math.radians(SUN_PITCH), math.radians(SUN_YAW)
    forward = (math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch))
    return tuple(-c for c in forward)


def build_starfield_material(glow_cube):
    m = fresh_material(STARFIELD_MATERIAL)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)   # seen from inside the dome
    m.set_editor_property("is_sky", True)      # sky pass; also picked up by the real-time sky light

    # CameraVector points from the pixel to the camera; the sky lookup needs the opposite.
    view = node(m, unreal.MaterialExpressionCameraVectorWS, -1100, 0)
    flip = node(m, unreal.MaterialExpressionConstant, -1100, 120, r=-1.0)
    direction = node(m, unreal.MaterialExpressionMultiply, -900, 0)
    link(view, direction, "A")
    link(flip, direction, "B")

    stars = custom(m, STAR_HLSL, ("Dir", "Density", "Brightness", "Time", "Twinkle"), -600, 0, "Procedural stars")
    density = scalar(m, "StarDensity", STAR_DENSITY, -900, 200)
    brightness = scalar(m, "StarBrightness", STAR_BRIGHTNESS, -900, 320)
    time = node(m, unreal.MaterialExpressionTime, -900, 440)
    twinkle = scalar(m, "Twinkle", STAR_TWINKLE, -900, 540)
    link(direction, stars, "Dir")
    link(density, stars, "Density")
    link(brightness, stars, "Brightness")
    link(time, stars, "Time")
    link(twinkle, stars, "Twinkle")

    glow = node(m, unreal.MaterialExpressionTextureSampleParameterCube, -600, 400,
                parameter_name="MilkyWayGlow", texture=glow_cube)
    link(direction, glow, "UVs")
    glow_brightness = node(m, unreal.MaterialExpressionScalarParameter, -600, 650,
                           parameter_name="GlowBrightness", default_value=GLOW_BRIGHTNESS)
    glow_scaled = node(m, unreal.MaterialExpressionMultiply, -350, 400)
    link(glow, glow_scaled, "A", "RGB")
    link(glow_brightness, glow_scaled, "B")

    nebula = custom(m, NOISE_STRUCT + NEBULA_HLSL, ("Dir", "Brightness"), -600, 800, "Nebulae")
    link(direction, nebula, "Dir")
    link(scalar(m, "NebulaBrightness", NEBULA_BRIGHTNESS, -900, 850), nebula, "Brightness")

    stars_and_glow = node(m, unreal.MaterialExpressionAdd, -300, 0)
    link(stars, stars_and_glow, "A")
    link(glow_scaled, stars_and_glow, "B")
    space = node(m, unreal.MaterialExpressionAdd, -150, 0)
    link(stars_and_glow, space, "A")
    link(nebula, space, "B")

    sun = custom(m, SUN_HLSL, ("Dir", "SunDir", "SunColor", "Disc", "Glow", "Amount"), -150, 1000, "Sun disc and glow")
    link(direction, sun, "Dir")
    link(vector(m, "SunDirection", sun_direction(), -450, 1000), sun, "SunDir")
    link(vector(m, "SunColor", (1.0, 0.97, 0.92), -450, 1150), sun, "SunColor")
    link(scalar(m, "SunDiscBrightness", SUN_DISC_BRIGHTNESS, -450, 1300), sun, "Disc")
    link(scalar(m, "SunGlowBrightness", SUN_GLOW_BRIGHTNESS, -450, 1400), sun, "Glow")

    # Atmosphere: ASkyDome sets these every frame from the planet nearest the camera.
    blend = node(m, unreal.MaterialExpressionCustom, 100, 0,
                 code=ATMOSPHERE_HLSL, description="Atmosphere blend",
                 output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    names = ("Space", "Dir", "Up", "Zenith", "Horizon", "Brightness", "Amount", "Sun", "Atmo", "AtmoScale", "StarFade", "FakeSky")
    custom_inputs = []
    for name in names:
        custom_pin = unreal.CustomInput()
        custom_pin.set_editor_property("input_name", name)
        custom_inputs.append(custom_pin)
    blend.set_editor_property("inputs", custom_inputs)
    up = node(m, unreal.MaterialExpressionVectorParameter, -150, 250, parameter_name="PlanetUp",
              default_value=unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    zenith = node(m, unreal.MaterialExpressionVectorParameter, -150, 400, parameter_name="SkyZenithColor",
                  default_value=unreal.LinearColor(0.16, 0.32, 0.62, 1.0))
    horizon = node(m, unreal.MaterialExpressionVectorParameter, -150, 550, parameter_name="SkyHorizonColor",
                   default_value=unreal.LinearColor(0.62, 0.70, 0.80, 1.0))
    sky_brightness = node(m, unreal.MaterialExpressionScalarParameter, -150, 700,
                          parameter_name="SkyBrightness", default_value=6.0)
    amount = node(m, unreal.MaterialExpressionScalarParameter, -150, 800,
                  parameter_name="AtmosphereAmount", default_value=0.0)
    link(space, blend, "Space")
    link(direction, blend, "Dir")
    link(up, blend, "Up")
    link(zenith, blend, "Zenith")
    link(horizon, blend, "Horizon")
    link(sky_brightness, blend, "Brightness")
    link(amount, blend, "Amount")
    link(amount, sun, "Amount")
    link(sun, blend, "Sun")
    atmo = node(m, unreal.MaterialExpressionSkyAtmosphereViewLuminance, -150, 1500)
    link(atmo, blend, "Atmo")
    link(scalar(m, "AtmosphereSkyScale", ATMO_SKY_SCALE, -150, 1600), blend, "AtmoScale")
    link(scalar(m, "AtmosphereStarFade", ATMO_STAR_FADE, -150, 1700), blend, "StarFade")
    # The painted sky gradient, partly (PAINTED_SKY_AMOUNT: the sky light's capture needs it).
    link(scalar(m, "FakeSkyAmount", PAINTED_SKY_AMOUNT, -150, 1800), blend, "FakeSky")
    output(blend, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(m)
    return m


# Sky colour by elevation above the local horizon, blended over the stars. Stars fade faster than
# the sky brightens (squared), as they do in a real dusk: the thinnest haze already hides them.
# Below the horizon (seen only in gaps, e.g. over a cliff) the colour darkens.
ATMOSPHERE_HLSL = r"""
float3 d = normalize(Dir);
float3 up = normalize(Up.xyz);
float mu = dot(d, up);
float3 sky = lerp(Horizon.rgb, Zenith.rgb, sqrt(saturate(mu)));
sky *= lerp(1.0, 0.35, saturate(-mu * 3.0));
float a = saturate(Amount);
// The real atmosphere (SkyAtmosphere, Veyra's): its light along this view, and the stars behind
// it fading as it brightens - the limb from space, the day sky from the ground.
float3 atmo = Atmo * AtmoScale;
float hide = saturate(1.0 - dot(atmo, float3(0.3, 0.59, 0.11)) * StarFade);
float keep = (1.0 - a) * (1.0 - a) * hide;
return Space * keep + sky * Brightness * a * FakeSky + atmo + Sun;
"""

# Value noise and fbm for the sky and the distant bodies. HLSL in a Custom node is the body of one
# function; a local struct is the way to get helper functions into it.
NOISE_STRUCT = r"""
struct FSpaceNoise
{
    float Hash(float3 p)
    {
        p = frac(p * float3(0.1031, 0.1030, 0.0973));
        p += dot(p, p.yxz + 33.33);
        return frac((p.x + p.y) * p.z);
    }
    float Noise(float3 x)
    {
        float3 i = floor(x);
        float3 f = frac(x);
        f = f * f * (3.0 - 2.0 * f);
        return lerp(lerp(lerp(Hash(i), Hash(i + float3(1, 0, 0)), f.x),
                         lerp(Hash(i + float3(0, 1, 0)), Hash(i + float3(1, 1, 0)), f.x), f.y),
                    lerp(lerp(Hash(i + float3(0, 0, 1)), Hash(i + float3(1, 0, 1)), f.x),
                         lerp(Hash(i + float3(0, 1, 1)), Hash(i + float3(1, 1, 1)), f.x), f.y), f.z);
    }
    float Fbm(float3 p, int octaves)
    {
        float v = 0.0;
        float a = 0.5;
        for (int o = 0; o < octaves; o++)
        {
            v += a * Noise(p);
            p = p * 2.02 + float3(17.1, 5.3, 11.7);
            a *= 0.5;
        }
        return v;
    }
};
FSpaceNoise N;
"""

# Nebulae: domain-warped fbm clouds, shown only inside three soft regions of the sky so most of it
# stays dark. Each region has its own colour pair; the fine noise mixes between them.
NEBULA_HLSL = r"""
float3 d = normalize(Dir);
float3 w = float3(N.Fbm(d * 2.5 + 1.7, 4), N.Fbm(d * 2.5 + 9.2, 4), N.Fbm(d * 2.5 + 4.4, 4));
float cloud = N.Fbm(d * 3.2 + (w - 0.5) * 2.2, 5);
float fine = N.Fbm(d * 11.0 + (w - 0.5) * 3.0, 4);

float3 c1 = normalize(float3(0.35, -0.55, 0.76));
float3 c2 = normalize(float3(-0.75, 0.55, 0.25));
float3 c3 = normalize(float3(0.15, 0.75, -0.62));
float r1 = saturate(1.0 - acos(saturate(dot(d, c1))) / 0.75);
float r2 = saturate(1.0 - acos(saturate(dot(d, c2))) / 0.9);
float r3 = saturate(1.0 - acos(saturate(dot(d, c3))) / 0.6);
r1 *= r1; r2 *= r2; r3 *= r3;

float density = saturate((cloud - 0.38) * 3.0);
density = density * density * (0.55 + 0.9 * fine);
float3 col1 = lerp(float3(0.55, 0.10, 0.35), float3(1.00, 0.45, 0.30), fine);
float3 col2 = lerp(float3(0.05, 0.25, 0.45), float3(0.25, 0.75, 0.80), fine);
float3 col3 = lerp(float3(0.35, 0.18, 0.05), float3(0.90, 0.60, 0.25), fine);
return density * (r1 * col1 + r2 * col2 + r3 * col3) * Brightness;
"""

# Sun: a limb-darkened disc and a corona of three exponential falloffs. The angle comes from the
# chord length, which stays precise for tiny angles where acos(dot) would not.
SUN_HLSL = r"""
float3 d = normalize(Dir);
float3 s = normalize(SunDir.xyz);
float ang = 2.0 * asin(saturate(length(d - s) * 0.5));
const float radius = 0.0105;
float disc = 1.0 - smoothstep(radius * 0.9, radius, ang);
float limb = lerp(0.6, 1.0, sqrt(saturate(1.0 - (ang / radius) * (ang / radius))));
float corona = 0.55 * exp(-ang / 0.018) + 0.12 * exp(-ang / 0.08) + 0.015 * exp(-ang / 0.35);
float a = saturate(Amount);
float3 tint = SunColor.rgb * lerp(float3(1.0, 1.0, 1.0), float3(1.0, 0.85, 0.65), a);
return tint * (disc * limb * Disc * lerp(1.0, 0.6, a) + corona * Glow * (1.0 + 1.5 * a));
"""

GAS_GIANT_HLSL = r"""
float3 n = normalize(Nrm);
float lat = n.z;
float swirl = N.Fbm(n * 3.0 + float3(0.0, 0.0, Time * 0.003), 5);
float bands = lat * 9.0 + (swirl - 0.5) * 1.6 + (N.Fbm(float3(lat * 30.0, n.x * 4.0, n.y * 4.0), 4) - 0.5) * 0.5;
float b1 = 0.5 + 0.5 * sin(bands * 3.14159);
float b2 = 0.5 + 0.5 * sin(bands * 1.7 + 1.3);
float3 cream = float3(0.86, 0.78, 0.62);
float3 tanColor = float3(0.70, 0.52, 0.36);
float3 rust = float3(0.52, 0.30, 0.20);
float3 pale = float3(0.78, 0.80, 0.78);
float3 col = lerp(lerp(rust, tanColor, b1), lerp(cream, pale, b2), smoothstep(0.3, 0.7, b1));
float lon = atan2(n.y, n.x);
float storm = exp(-(pow((lat + 0.33) / 0.06, 2.0) + pow((lon - 0.9) / 0.16, 2.0)));
col = lerp(col, float3(0.72, 0.36, 0.24), saturate(storm * 1.2));
col *= lerp(1.0, 0.55, smoothstep(0.75, 0.98, abs(lat)));
return col;
"""

MOON_HLSL = r"""
float3 n = normalize(Nrm);
float base = N.Fbm(n * 4.0, 5);
float maria = smoothstep(0.45, 0.6, N.Fbm(n * 1.6 + 3.0, 4));
float detail = N.Fbm(n * 28.0, 4);
// Craters: distance to the nearest random point of a 3D grid; a dark floor and a bright rim.
float3 p = n * 12.0;
float3 ip = floor(p);
float3 fp = frac(p);
float nearest = 10.0;
for (int x = -1; x <= 1; x++)
for (int y = -1; y <= 1; y++)
for (int z = -1; z <= 1; z++)
{
    float3 g = float3(x, y, z);
    float3 o = float3(N.Hash(ip + g), N.Hash(ip + g + 17.3), N.Hash(ip + g + 41.7));
    nearest = min(nearest, length(g + o - fp));
}
float floorDark = 1.0 - 0.25 * (1.0 - smoothstep(0.18, 0.3, nearest));
float rim = exp(-pow((nearest - 0.32) / 0.04, 2.0));
float grey = lerp(0.36, 0.60, base) * lerp(1.0, 0.62, maria) * (0.85 + 0.3 * detail) * floorDark + 0.12 * rim;
return grey * float3(1.0, 0.98, 0.95);
"""

# Rings on the engine plane (UV 0..1 across the outer diameter). Ringlets are sines of the radius,
# faded out where they would be finer than a pixel so the rings do not shimmer at a distance.
RINGS_HLSL = r"""
float r = length(UV - 0.5) * 2.0;
float fw = max(fwidth(r), 1e-5);
float soft = smoothstep(Inner, Inner + 0.02, r) * (1.0 - smoothstep(0.97, 1.0, r));
float ringlets = 0.55 + 0.25 * sin(r * 260.0) * saturate(1.0 - fw * 260.0 * 0.5)
               + 0.15 * sin(r * 611.0 + 1.3) * saturate(1.0 - fw * 611.0 * 0.5)
               + 0.10 * sin(r * 1400.0 + 0.7) * saturate(1.0 - fw * 1400.0 * 0.5);
float gap = 1.0 - 0.9 * exp(-pow((r - 0.8) / 0.012, 2.0));
return float4(lerp(float3(0.55, 0.49, 0.40), float3(0.85, 0.80, 0.70), saturate(ringlets)), saturate(soft * ringlets * gap) * 0.85);
"""


def local_normal(material, x, y):
    """The sphere's own direction at the pixel: the vertex normal in local space (no precision
    trouble hundreds of kilometres from the origin, unlike world positions)."""
    normal = node(material, unreal.MaterialExpressionVertexNormalWS, x, y)
    local = node(material, unreal.MaterialExpressionTransform, x + 150, y,
                 transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
                 transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
    link(normal, local, "")
    return local


def build_body_material(path, hlsl, roughness, with_time):
    m = fresh_material(path)
    inputs = ("Nrm", "Time") if with_time else ("Nrm",)
    colour = custom(m, NOISE_STRUCT + hlsl, inputs, -300, 0, path.rsplit("/", 1)[1])
    link(local_normal(m, -700, 0), colour, "Nrm")
    if with_time:
        link(node(m, unreal.MaterialExpressionTime, -700, 150), colour, "Time")
    output(colour, unreal.MaterialProperty.MP_BASE_COLOR)
    output(node(m, unreal.MaterialExpressionConstant, -300, 200, r=roughness), unreal.MaterialProperty.MP_ROUGHNESS)
    output(node(m, unreal.MaterialExpressionConstant, -300, 300, r=0.2), unreal.MaterialProperty.MP_SPECULAR)
    finish(m)
    return m


def build_rings_material():
    m = fresh_material(RINGS_MATERIAL)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    rings = custom(m, RINGS_HLSL, ("UV", "Inner"), -400, 0, "Rings", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    link(node(m, unreal.MaterialExpressionTextureCoordinate, -700, 0), rings, "UV")
    link(scalar(m, "RingInnerFraction", GIANT_RING_INNER_FRACTION, -700, 150), rings, "Inner")
    rgb = node(m, unreal.MaterialExpressionComponentMask, -150, 0, r=True, g=True, b=True, a=False)
    link(rings, rgb, "")
    alpha = node(m, unreal.MaterialExpressionComponentMask, -150, 150, r=False, g=False, b=False, a=True)
    link(rings, alpha, "")
    output(rgb, unreal.MaterialProperty.MP_BASE_COLOR)
    output(alpha, unreal.MaterialProperty.MP_OPACITY)
    output(node(m, unreal.MaterialExpressionConstant, -150, 300, r=0.9), unreal.MaterialProperty.MP_ROUGHNESS)
    finish(m)
    return m


def build_dust_material():
    """USpaceDustComponent specks: additive and unlit.

    A speck is a stretched cube, and a cube has ends. Drawn flat they are white sticks cut off
    square, which is exactly what the prototype looked like (20. 9. 2026, the author against a
    Star Citizen frame). So the material tapers the brightness along the streak and across it,
    turning the box into a soft spindle: bright in the middle, nothing at the tips and edges.

    The shape is measured from the instance's own centre, not from LocalPosition: on an instanced
    mesh that node returns the primitive's space, not the instance's, so the taper came out negative
    everywhere and the dust vanished (21. 9. 2026). ObjectPositionWS is per instance, and the
    component pushes the direction and the half sizes in as parameters (it sets them every frame on
    a dynamic instance), with the speck's own length multiplier in custom data 2.

    Per instance: custom data 0 is the fade (distance from the camera and speed), 1 is that speck's
    own brightness, 2 its length as a multiple of the common one.
    """
    m = fresh_material(DUST_MATERIAL)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("used_with_instanced_static_meshes", True)

    here = node(m, unreal.MaterialExpressionWorldPosition, -1700, -100)
    centre = node(m, unreal.MaterialExpressionObjectPositionWS, -1700, 20)
    delta = node(m, unreal.MaterialExpressionSubtract, -1500, -60)
    link(here, delta, "A")
    link(centre, delta, "B")

    direction = vector(m, "DustDirection", (1.0, 0.0, 0.0), -1700, 160)
    along = node(m, unreal.MaterialExpressionDotProduct, -1340, -60)
    link(delta, along, "A")
    link(direction, along, "B")

    # Across: what is left of the offset once the along part is taken out.
    along_vec = node(m, unreal.MaterialExpressionMultiply, -1200, 120)
    link(direction, along_vec, "A")
    link(along, along_vec, "B")
    across_vec = node(m, unreal.MaterialExpressionSubtract, -1060, 60)
    link(delta, across_vec, "A")
    link(along_vec, across_vec, "B")
    across_len = node(m, unreal.MaterialExpressionLength, -920, 60)
    link(across_vec, across_len, "")

    # Along, as a fraction of this speck's own half length.
    own_length = node(m, unreal.MaterialExpressionPerInstanceCustomData, -1700, 300, data_index=2)
    half_length = node(m, unreal.MaterialExpressionMultiply, -1400, 300)
    link(scalar(m, "DustHalfLengthCm", 700.0, -1700, 400), half_length, "A")
    link(own_length, half_length, "B")
    along_unit = node(m, unreal.MaterialExpressionDivide, -1100, -60)
    link(along, along_unit, "A")
    link(half_length, along_unit, "B")
    along_abs = node(m, unreal.MaterialExpressionAbs, -960, -60)
    link(along_unit, along_abs, "")
    along_pow = node(m, unreal.MaterialExpressionPower, -820, -60)
    link(along_abs, along_pow, "Base")
    link(scalar(m, "DustTipSharpness", 3.0, -960, -160), along_pow, "Exp")
    along_fade = node(m, unreal.MaterialExpressionOneMinus, -680, -60)
    link(along_pow, along_fade, "")

    across_unit = node(m, unreal.MaterialExpressionDivide, -780, 60)
    link(across_len, across_unit, "A")
    link(scalar(m, "DustHalfWidthCm", 1.4, -920, 160), across_unit, "B")
    across_fade = node(m, unreal.MaterialExpressionOneMinus, -640, 60)
    link(across_unit, across_fade, "")

    shape = node(m, unreal.MaterialExpressionMultiply, -480, 0)
    link(along_fade, shape, "A")
    link(across_fade, shape, "B")
    shape_clamped = node(m, unreal.MaterialExpressionClamp, -340, 0, min_default=0.0, max_default=1.0)
    link(shape, shape_clamped, "")

    fade = node(m, unreal.MaterialExpressionPerInstanceCustomData, -1700, 520, data_index=0)
    own = node(m, unreal.MaterialExpressionPerInstanceCustomData, -1700, 620, data_index=1)
    colour = vector(m, "DustColor", DUST_COLOR, -1700, 720)
    brightness = scalar(m, "DustBrightness", DUST_BRIGHTNESS, -1700, 820)
    tinted = node(m, unreal.MaterialExpressionMultiply, -1400, 720)
    link(colour, tinted, "A")
    link(brightness, tinted, "B")
    per_instance = node(m, unreal.MaterialExpressionMultiply, -1400, 560)
    link(fade, per_instance, "A")
    link(own, per_instance, "B")
    faded = node(m, unreal.MaterialExpressionMultiply, -1000, 640)
    link(tinted, faded, "A")
    link(per_instance, faded, "B")
    final = node(m, unreal.MaterialExpressionMultiply, -200, 300)
    link(faded, final, "A")
    link(shape_clamped, final, "B")
    output(final, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(m)
    return m


# The cruise speed tunnel (USpaceSpeedTunnelComponent), per pixel of a cylinder wall round the flight
# path. P is the pixel relative to the camera (the instance origin); z runs along the flight path.
# The wall is cut into lanes round the axis, each with one streak per period that scrolls backwards
# by Offset, so it flows the way stationary dust does past a moving ship. Beams are a smooth noise
# round the axis, strongest far ahead where they converge. The far end cap is the glow on the
# vanishing point. Everything is multiplied by Alpha (speed) and the layer's brightness.
TUNNEL_HLSL = r"""
float3 dir = Dir.xyz;
float z = dot(P, dir);
float3 rv = P - z * dir;
float r = length(rv);
float zn = z / HalfLength;
bool cap = abs(zn) > 0.985;
float a = atan2(dot(rv, Up.xyz), dot(rv, Right.xyz)) / 6.2831853 + 0.5;
// A little per-pixel noise: the smooth beams band into visible steps without it.
float dither = frac(sin(dot(P, float3(12.9898, 78.233, 37.719))) * 43758.5453) - 0.5;
float3 result = 0;

// Haze: the tunnel is a lit fog, brightest on the walls beside the ship and dark down the middle
// towards the vanishing point (the reference's "hole").
if (!cap)
{
    result += Haze.rgb * Beam * (1.0 - smoothstep(0.0, 0.5, zn)) * smoothstep(-0.05, 0.05, zn);
}

// Beams: smooth noise round the axis, strongest far ahead where they converge. They carry on over
// the far cap, so the vanishing point is not a dark disc where the wall stops.
if (Beam > 0.0)
{
    float count = max(floor(BeamCount), 1.0);
    float bt = a * count;
    float bi = floor(bt);
    float n0 = frac(sin((bi + Seed * 13.1) * 91.345) * 47453.5453);
    float n1 = frac(sin((fmod(bi + 1.0, count) + Seed * 13.1) * 91.345) * 47453.5453);
    float n = lerp(n0, n1, smoothstep(0.0, 1.0, frac(bt)));
    float count2 = floor(count * 2.7);
    float bt2 = a * count2;
    float ci = floor(bt2);
    float c0 = frac(sin((ci + Seed * 5.7) * 17.231) * 23421.631);
    float c1 = frac(sin((fmod(ci + 1.0, count2) + Seed * 5.7) * 17.231) * 23421.631);
    n = n * 0.6 + 0.4 * lerp(c0, c1, smoothstep(0.0, 1.0, frac(bt2)));
    float shafts = pow(saturate(n), BeamSharp);
    float fb = cap ? (zn > 0.0 ? 1.0 : 0.0) : smoothstep(0.02, 0.7, zn);
    result += BeamColor.rgb * BeamBright * Beam * shafts * fb;

    // Flares: a few broad green beams out of the vanishing point that come and go (Flare 0..1, a
    // new FlareSeed each time, so every flare points elsewhere). Strongest at the jump itself.
    if (Flare > 0.001)
    {
        float fcount = 7.0;
        float ft = a * fcount;
        float fi = floor(ft);
        float fh = frac(sin((fi + FlareSeed * 3.31) * 51.713) * 31718.123);
        float fx = frac(ft) - 0.2 - 0.6 * frac(fh * 7.13);
        float beam = fh > 0.45 ? saturate(1.0 - abs(fx) / 0.09) : 0.0;
        beam *= beam;
        float ff = cap ? (zn > 0.0 ? 1.0 : 0.0) : smoothstep(-0.05, 0.4, zn);
        result += FlareColor.rgb * Flare * beam * ff * Beam;
    }
}
if (cap)
{
    // The far end: the glow on the vanishing point.
    float g = saturate(1.0 - r / Radius);
    g = g * g * g;
    result += GlowColor.rgb * GlowBright * g * (zn > 0.0 ? 1.0 : 0.1);
    return max(result * (1.0 + 0.1 * dither) * Alpha * Bright, 0.0);
}

// Streaks
float lanes = max(floor(Lanes), 1.0);
float la = a * lanes;
float lane = floor(la);
float2 hs = float2(lane, Seed);
float h1 = frac(sin(dot(hs, float2(12.9898, 78.233))) * 43758.5453);
float h2 = frac(sin(dot(hs, float2(39.3468, 11.135))) * 24634.6345);
float h3 = frac(sin(dot(hs, float2(73.156, 52.235))) * 15731.7431);
float h4 = frac(sin(dot(hs, float2(94.673, 23.914))) * 31337.4297);
// Width in cm on a wall 25 m out, scaled with the wall's distance, so every wall's streaks are
// equally thin on screen whatever its lane count (a share of the lane made the near wall's bars fat).
float laneCm = 6.2831853 * max(r, 1.0) / lanes;
float u = (frac(la) - 0.5 - (h1 - 0.5) * 0.6) * laneCm;
float across = saturate(1.0 - abs(u) / (StreakWidth * Radius / 2500.0));
across *= across;
float len = StreakLen * (0.45 + 1.1 * h2);
float x = frac((z + Offset) / Period + h3) * Period / len;
float along = x < 1.0 ? 1.0 - pow(abs(2.0 * x - 1.0), 3.0) : 0.0;
// Most streaks faint and a few bright, as dust is; the rest of the lanes empty.
float own = h4 < Fill ? 0.2 + 0.8 * pow(frac(h4 * 7.31), 3.0) : 0.0;
float3 tint = lerp(StreakColor.rgb, BeamColor.rgb * 1.4, ColorSpread * frac(h2 * 3.77));
float nearFar = smoothstep(-0.02, 0.06, zn) * (1.0 - smoothstep(0.45, 0.95, zn));
result += tint * StreakBright * across * along * own * nearFar;
return max(result * (1.0 + 0.1 * dither) * Alpha * Bright, 0.0);
"""


def build_tunnel_material():
    """USpaceSpeedTunnelComponent walls: additive, unlit, two sided (the camera is inside them).

    All the shape is in TUNNEL_HLSL; the component pushes the flight direction, the scroll and
    every look value into a dynamic instance each frame, so space.Tunnel tunes it live. Per
    instance: custom data 0 radius, 1 brightness, 2 seed, 3 beam weight, 4 lanes.
    """
    m = fresh_material(TUNNEL_MATERIAL)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("used_with_instanced_static_meshes", True)
    m.set_editor_property("enable_responsive_aa", True)

    here = node(m, unreal.MaterialExpressionWorldPosition, -1700, -100)
    centre = node(m, unreal.MaterialExpressionObjectPositionWS, -1700, 20)
    delta = node(m, unreal.MaterialExpressionSubtract, -1500, -60)
    link(here, delta, "A")
    link(centre, delta, "B")

    names = ["P", "Dir", "Right", "Up", "Radius", "Bright", "Seed", "Beam", "Lanes", "HalfLength", "Offset", "Period",
             "StreakLen", "StreakWidth", "Fill", "ColorSpread", "StreakColor", "StreakBright", "BeamColor", "BeamBright", "BeamCount",
             "BeamSharp", "GlowColor", "GlowBright", "Alpha", "Haze", "Flare", "FlareSeed", "FlareColor"]
    tunnel = custom(m, TUNNEL_HLSL, names, -400, 0, "SpeedTunnel")
    sources = {
        "P": delta,
        "Dir": vector(m, "TunnelDirection", (1.0, 0.0, 0.0), -1100, -300),
        "Right": vector(m, "TunnelRight", (0.0, 1.0, 0.0), -1100, -200),
        "Up": vector(m, "TunnelUp", (0.0, 0.0, 1.0), -1100, -100),
        "HalfLength": scalar(m, "TunnelHalfLengthCm", 150000.0, -1100, 0),
        "Offset": scalar(m, "TunnelOffsetCm", 0.0, -1100, 100),
        "Period": scalar(m, "TunnelPeriodCm", 40000.0, -1100, 200),
        "StreakLen": scalar(m, "StreakLengthCm", 8000.0, -1100, 300),
        "StreakWidth": scalar(m, "StreakWidthCm", 8.0, -1100, 400),
        "ColorSpread": scalar(m, "StreakColorSpread", 0.5, -1300, 400),
        "Fill": scalar(m, "StreakFill", 0.55, -1100, 500),
        "StreakColor": vector(m, "StreakColor", (0.85, 0.92, 1.0), -1100, 600),
        "StreakBright": scalar(m, "StreakBrightness", 6.0, -1100, 700),
        "BeamColor": vector(m, "BeamColor", (0.35, 0.6, 1.0), -1100, 800),
        "BeamBright": scalar(m, "BeamBrightness", 0.25, -1100, 900),
        "BeamCount": scalar(m, "BeamCount", 14.0, -1100, 1000),
        "BeamSharp": scalar(m, "BeamSharpness", 4.0, -1100, 1100),
        "GlowColor": vector(m, "GlowColor", (0.8, 0.9, 1.0), -1100, 1200),
        "GlowBright": scalar(m, "GlowBrightness", 2.0, -1100, 1300),
        "Alpha": scalar(m, "TunnelAlpha", 0.0, -1100, 1400),
        "Haze": vector(m, "HazeColor", (0.02, 0.03, 0.06), -1300, 1500),
        "Flare": scalar(m, "FlareAlpha", 0.0, -1300, 1600),
        "FlareSeed": scalar(m, "FlareSeed", 1.0, -1300, 1700),
        "FlareColor": vector(m, "FlareColor", (0.1, 0.9, 0.45), -1300, 1800),
    }
    for index, name in enumerate(["Radius", "Bright", "Seed", "Beam", "Lanes"]):
        sources[name] = node(m, unreal.MaterialExpressionPerInstanceCustomData, -1700, 300 + 100 * index, data_index=index)
    for name in names:
        link(sources[name], tunnel, name)
    output(tunnel, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(m)
    return m


# The quantum tunnel's fog (USpaceSpeedTunnelComponent's second mesh, behind the streak walls). In the
# reference the tunnel hides the stars and planets outside: a dim blue-grey fog, lighter on the walls
# beside the ship and dark down the middle towards the vanishing point. Translucent rather than
# additive, because additive light can brighten the sky but never cover it.
FOG_HLSL = r"""
float z = dot(P, Dir.xyz);
float zn = z / HalfLength;
float3 rv = P - z * Dir.xyz;
float a = atan2(dot(rv, Up.xyz), dot(rv, Right.xyz)) / 6.2831853 + 0.5;
// Soft light shafts round the axis, so the fog reads as the walls of a tunnel and not a wash.
float count = 13.0;
float i0 = floor(a * count);
float n0 = frac(sin((i0 + 3.0) * 91.345) * 47453.5453);
float n1 = frac(sin((fmod(i0 + 1.0, count) + 3.0) * 91.345) * 47453.5453);
float n = lerp(n0, n1, smoothstep(0.0, 1.0, frac(a * count)));
float shafts = 0.45 + 1.1 * n * n;
float far = smoothstep(0.0, 0.65, zn);
float3 colour = lerp(Near.rgb * shafts, Far.rgb, far);
// Thick on the walls beside the ship, thin down the middle: a tunnel you look along, not a fog bank.
float opacity = Opacity * lerp(1.0, CentreOpacity, far) * lerp(0.7, 1.0, shafts / 1.55);
return float4(colour, saturate(opacity * Alpha));
"""


def build_fog_material():
    m = fresh_material(FOG_MATERIAL)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("two_sided", True)
    here = node(m, unreal.MaterialExpressionWorldPosition, -1100, -100)
    centre = node(m, unreal.MaterialExpressionObjectPositionWS, -1100, 20)
    delta = node(m, unreal.MaterialExpressionSubtract, -900, -60)
    link(here, delta, "A")
    link(centre, delta, "B")
    # Neither history nor ghosts: the fog does not move with the world, so TSR had nothing to reject a
    # stale pixel with and the ship left a dark copy of itself where it had been (free look in a jump,
    # the author's screenshot, 21. 9. 2026).
    m.set_editor_property("enable_responsive_aa", True)
    m.set_editor_property("output_translucent_velocity", True)
    names = ["P", "Dir", "Right", "Up", "HalfLength", "Near", "Far", "Opacity", "CentreOpacity", "Alpha"]
    fog = custom(m, FOG_HLSL, names, -400, 0, "QuantumFog", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    sources = {
        "P": delta,
        "Dir": vector(m, "TunnelDirection", (1.0, 0.0, 0.0), -900, 100),
        "Right": vector(m, "TunnelRight", (0.0, 1.0, 0.0), -1100, 150),
        "Up": vector(m, "TunnelUp", (0.0, 0.0, 1.0), -1100, 250),
        "CentreOpacity": scalar(m, "FogCentreOpacity", 0.35, -1100, 550),
        "HalfLength": scalar(m, "TunnelHalfLengthCm", 150000.0, -900, 200),
        "Near": vector(m, "FogNearColor", (0.04, 0.055, 0.09), -900, 300),
        "Far": vector(m, "FogFarColor", (0.004, 0.006, 0.012), -900, 400),
        "Opacity": scalar(m, "FogOpacity", 0.8, -900, 500),
        "Alpha": scalar(m, "TunnelAlpha", 0.0, -900, 600),
    }
    for name in names:
        link(sources[name], fog, name)
    rgb = node(m, unreal.MaterialExpressionComponentMask, -200, 0, r=True, g=True, b=True, a=False)
    link(fog, rgb, "")
    alpha = node(m, unreal.MaterialExpressionComponentMask, -200, 150, r=False, g=False, b=False, a=True)
    link(fog, alpha, "")
    output(rgb, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    output(alpha, unreal.MaterialProperty.MP_OPACITY)
    finish(m)
    return m


def pin(expr, wanted):
    """Input pin name, checked against the node - pin names are not always the obvious ones."""
    names = [str(n) for n in MEL.get_material_expression_input_names(expr)]
    if wanted not in names:
        raise RuntimeError("%s has no input %r; inputs are %s" % (expr.get_class().get_name(), wanted, names))
    return wanted


def primitive_data(material, name, index, x, y):
    """Scalar read per component from custom primitive data (set by AQuadSpherePlanet)."""
    return node(material, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name,
                use_custom_primitive_data=True, primitive_data_index=index)


def build_planet_material():
    """Terrain material for AQuadSpherePlanet tiles.

    Each tile is its own component, so object position and radius describe the tile, not the
    planet. The planet-local position is rebuilt instead from the tile centre that the planet
    passes in custom primitive data (slots 0-2). Also reads the geomorph range (3-4), the planet
    radius (5), the tile depth (6) and a debug flag (7).
    """
    m = fresh_material(PLANET_MATERIAL)

    world = node(m, unreal.MaterialExpressionWorldPosition, -2000, 0)
    tile_origin = node(m, unreal.MaterialExpressionObjectPositionWS, -2000, 150)
    in_tile_world = node(m, unreal.MaterialExpressionSubtract, -1900, 0)  # small, single precision is fine
    link(world, in_tile_world, pin(in_tile_world, "A"))
    link(tile_origin, in_tile_world, pin(in_tile_world, "B"))
    # Into the tile's (= the planet's) local frame, so colours stay on the ground when the planet
    # actor is rotated. Tile components carry no rotation of their own.
    in_tile = node(m, unreal.MaterialExpressionTransform, -1800, 0,
                   transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
                   transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
    link(in_tile_world, in_tile, "")
    cx = primitive_data(m, "TileCenterX", 0, -2000, 300)
    cy = primitive_data(m, "TileCenterY", 1, -2000, 400)
    cz = primitive_data(m, "TileCenterZ", 2, -2000, 500)
    cxy = node(m, unreal.MaterialExpressionAppendVector, -1850, 350)
    link(cx, cxy, pin(cxy, "A"))
    link(cy, cxy, pin(cxy, "B"))
    centre = node(m, unreal.MaterialExpressionAppendVector, -1700, 400)
    link(cxy, centre, pin(centre, "A"))
    link(cz, centre, pin(centre, "B"))
    planet_local = node(m, unreal.MaterialExpressionAdd, -1550, 0)
    link(in_tile, planet_local, pin(planet_local, "A"))
    link(centre, planet_local, pin(planet_local, "B"))
    radius = primitive_data(m, "PlanetRadius", 5, -1550, 200)
    unit = node(m, unreal.MaterialExpressionDivide, -1200, 0)
    link(planet_local, unit, pin(unit, "A"))
    link(radius, unit, pin(unit, "B"))

    # Continents: one multi-octave noise over the surface blends two terrain colours.
    noise = node(m, unreal.MaterialExpressionNoise, -1000, 0,
                 scale=1.6, levels=6, output_min=0.0, output_max=1.0)
    link(unit, noise, "World Position")
    lowland = node(m, unreal.MaterialExpressionVectorParameter, -1000, 250,
                   parameter_name="LowlandColor", default_value=unreal.LinearColor(0.30, 0.12, 0.06, 1.0))
    highland = node(m, unreal.MaterialExpressionVectorParameter, -1000, 450,
                    parameter_name="HighlandColor", default_value=unreal.LinearColor(0.62, 0.42, 0.24, 1.0))
    terrain = node(m, unreal.MaterialExpressionLinearInterpolate, -700, 250)
    link(lowland, terrain, "A")
    link(highland, terrain, "B")
    link(noise, terrain, "Alpha")

    # Polar caps: |z| near 1, with the edge broken up by the same noise.
    z = node(m, unreal.MaterialExpressionComponentMask, -1000, -250, r=False, g=False, b=True, a=False)
    link(unit, z, "")
    abs_z = node(m, unreal.MaterialExpressionAbs, -850, -250)
    link(z, abs_z, "")
    wobble_amount = node(m, unreal.MaterialExpressionConstant, -850, -120, r=0.12)
    wobble = node(m, unreal.MaterialExpressionMultiply, -700, -120)
    link(noise, wobble, "A")
    link(wobble_amount, wobble, "B")
    latitude = node(m, unreal.MaterialExpressionAdd, -550, -250)
    link(abs_z, latitude, "A")
    link(wobble, latitude, "B")
    cap = node(m, unreal.MaterialExpressionSmoothStep, -400, -250, const_min=0.86, const_max=0.93)
    link(latitude, cap, "Value")

    ice = node(m, unreal.MaterialExpressionVectorParameter, -700, 600,
               parameter_name="IceColor", default_value=unreal.LinearColor(0.85, 0.88, 0.90, 1.0))
    base = node(m, unreal.MaterialExpressionLinearInterpolate, -300, 250)
    link(terrain, base, "A")
    link(ice, base, "B")
    link(cap, base, "Alpha")

    # Debug: space.TerrainDebugLOD 1 tints each tile by its quadtree depth.
    depth = primitive_data(m, "TileDepth", 6, -700, 850)
    hue_steps = node(m, unreal.MaterialExpressionConstant3Vector, -700, 950,
                     constant=unreal.LinearColor(0.37, 0.61, 0.83, 1.0))
    hue = node(m, unreal.MaterialExpressionMultiply, -550, 850)
    link(depth, hue, pin(hue, "A"))
    link(hue_steps, hue, pin(hue, "B"))
    tint = node(m, unreal.MaterialExpressionFrac, -400, 850)
    link(hue, tint, "")
    debug_flag = primitive_data(m, "DebugTint", 7, -400, 1000)
    shown = node(m, unreal.MaterialExpressionLinearInterpolate, -150, 400)
    link(base, shown, "A")
    link(tint, shown, "B")
    link(debug_flag, shown, "Alpha")
    output(shown, unreal.MaterialProperty.MP_BASE_COLOR)

    rough = node(m, unreal.MaterialExpressionConstant, -300, 500, r=0.85)
    output(rough, unreal.MaterialProperty.MP_ROUGHNESS)

    # Geomorph: move each vertex towards where the parent tile would put it (UV1.xy, UV2.x, in
    # the tile's local frame) as the camera distance goes from MorphStart to MorphEnd.
    uv1 = node(m, unreal.MaterialExpressionTextureCoordinate, -1200, 1300, coordinate_index=1)
    uv2 = node(m, unreal.MaterialExpressionTextureCoordinate, -1200, 1450, coordinate_index=2)
    uv2_x = node(m, unreal.MaterialExpressionComponentMask, -1050, 1450, r=True, g=False, b=False, a=False)
    link(uv2, uv2_x, "")
    delta_local = node(m, unreal.MaterialExpressionAppendVector, -900, 1350)
    link(uv1, delta_local, pin(delta_local, "A"))
    link(uv2_x, delta_local, pin(delta_local, "B"))
    delta_world = node(m, unreal.MaterialExpressionTransform, -750, 1350,
                       transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                       transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    link(delta_local, delta_world, "")

    camera = node(m, unreal.MaterialExpressionCameraPositionWS, -1200, 1650)
    distance = node(m, unreal.MaterialExpressionDistance, -1050, 1600)
    link(world, distance, pin(distance, "A"))
    link(camera, distance, pin(distance, "B"))
    morph_start = primitive_data(m, "MorphStart", 3, -1200, 1800)
    morph_end = primitive_data(m, "MorphEnd", 4, -1200, 1900)
    past_start = node(m, unreal.MaterialExpressionSubtract, -900, 1650)
    link(distance, past_start, pin(past_start, "A"))
    link(morph_start, past_start, pin(past_start, "B"))
    span = node(m, unreal.MaterialExpressionSubtract, -900, 1850)
    link(morph_end, span, pin(span, "A"))
    link(morph_start, span, pin(span, "B"))
    ratio = node(m, unreal.MaterialExpressionDivide, -750, 1700)
    link(past_start, ratio, pin(ratio, "A"))
    link(span, ratio, pin(ratio, "B"))
    morph = node(m, unreal.MaterialExpressionSaturate, -600, 1700)
    link(ratio, morph, "")
    offset = node(m, unreal.MaterialExpressionMultiply, -450, 1450)
    link(delta_world, offset, pin(offset, "A"))
    link(morph, offset, pin(offset, "B"))
    output(offset, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    finish(m)
    return m


# ---------------------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------------------


def upsert_actor(eas, actors, label, cls, location=(0.0, 0.0, 0.0), replace_other_class=False):
    for actor in actors:
        if actor.get_actor_label() == label:
            # cls may be a Python wrapper type or a UClass from load_class(); compare as UClass.
            wanted = cls if isinstance(cls, unreal.Class) else cls.static_class()
            if not unreal.MathLibrary.class_is_child_of(actor.get_class(), wanted):
                if not replace_other_class:
                    raise RuntimeError("actor %r is a %s, expected %s" % (label, actor.get_class().get_name(), cls))
                # Only for actors this script created itself, when their class has changed.
                log("replacing %s (%s) with %s" % (label, actor.get_class().get_name(), wanted.get_name()))
                eas.destroy_actor(actor)
                break
            actor.set_actor_location(unreal.Vector(*location), False, False)
            return actor
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    log("spawned %s" % label)
    return actor


def build_level(sky_material, planet_mesh, planet_material, body_materials):
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not les.load_level(LEVEL):
        raise RuntimeError("could not load " + LEVEL)
    actors = eas.get_all_level_actors()

    for actor in actors:
        if isinstance(actor, unreal.SkyAtmosphere) and actor.get_actor_label() != "Atmosphere_" + PLANET_NAME:
            log("removing %s" % actor.get_actor_label())
            eas.destroy_actor(actor)
    actors = eas.get_all_level_actors()

    # Veyra's atmosphere, centred on the planet (see ATMO_* above).
    atmo_actor = upsert_actor(eas, actors, "Atmosphere_" + PLANET_NAME, unreal.SkyAtmosphere, PLANET_LOCATION_CM)
    atmo = atmo_actor.get_component_by_class(unreal.SkyAtmosphereComponent)
    for key, value in (
            ("transform_mode", unreal.SkyAtmosphereTransformMode.PLANET_CENTER_AT_COMPONENT_TRANSFORM),
            ("bottom_radius", PLANET_RADIUS_CM / 100000.0 - ATMO_GROUND_BELOW_SEA_KM),
            ("atmosphere_height", ATMO_HEIGHT_KM),
            ("ground_albedo", unreal.Color(*[int(round(255 * c)) for c in ATMO_GROUND_ALBEDO], 255)),
            ("rayleigh_scattering_scale", ATMO_RAYLEIGH_SCALE),
            ("rayleigh_scattering", unreal.LinearColor(*ATMO_RAYLEIGH_COLOR, 1.0)),
            ("rayleigh_exponential_distribution", ATMO_RAYLEIGH_HEIGHT_KM),
            ("mie_scattering_scale", ATMO_MIE_SCALE),
            ("mie_scattering", unreal.LinearColor(*ATMO_MIE_COLOR, 1.0)),
            ("mie_exponential_distribution", ATMO_MIE_HEIGHT_KM),
            ("mie_anisotropy", ATMO_MIE_ANISOTROPY),
            ("aerial_pespective_view_distance_scale", ATMO_AERIAL_DISTANCE_SCALE)):
        atmo.set_editor_property(key, value)
    log("atmosphere: %s, %.0f km thick, Rayleigh %.3f / %.1f km, Mie %.3f / %.1f km, aerial x%.0f" % (
        atmo_actor.get_actor_label(), ATMO_HEIGHT_KM, ATMO_RAYLEIGH_SCALE, ATMO_RAYLEIGH_HEIGHT_KM,
        ATMO_MIE_SCALE, ATMO_MIE_HEIGHT_KM, ATMO_AERIAL_DISTANCE_SCALE))

    # Keyword arguments on purpose: unreal.Rotator's positional order is roll, pitch, yaw.
    for actor in actors:
        if isinstance(actor, unreal.DirectionalLight):
            actor.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=SUN_PITCH, yaw=SUN_YAW), False)
            sun = actor.get_component_by_class(unreal.DirectionalLightComponent)
            sun.set_editor_property("contact_shadow_length", SUN_CONTACT_SHADOW_M)
            sun.set_editor_property("light_source_angle", SUN_SOURCE_ANGLE_DEG)
            # Lights Veyra's atmosphere (and is dimmed and reddened through it on the ground).
            sun.set_editor_property("atmosphere_sun_light", True)
            log("sun: contact shadows %.2f m, source angle %.2f deg" % (SUN_CONTACT_SHADOW_M, SUN_SOURCE_ANGLE_DEG))
        if isinstance(actor, unreal.SkyLight):
            sky_light = actor.get_component_by_class(unreal.SkyLightComponent)
            # Stars exist below the horizon too; don't clamp the captured lower half to black.
            sky_light.set_editor_property("lower_hemisphere_is_black", False)
            sky_light.set_editor_property("intensity", SKY_LIGHT_INTENSITY)
            log("sky light intensity %.2f" % SKY_LIGHT_INTENSITY)

    # Star dome: ASkyDome sets its own mesh, collision, shadow and scale (from the radius) and
    # follows the camera at runtime; only the material and radius are set here.
    sky = upsert_actor(eas, actors, "StarfieldSky", unreal.load_class(None, "/Script/gamespace.SkyDome"),
                       replace_other_class=True)
    # set_editor_property goes through PostEditChangeProperty, which reruns OnConstruction.
    sky.set_editor_property("dome_radius_km", SKY_DOME_RADIUS_KM)
    sky.get_component_by_class(unreal.StaticMeshComponent).set_material(0, sky_material)
    log("sky dome radius %.0f km, actor scale %.0f" % (SKY_DOME_RADIUS_KM, sky.get_actor_scale3d().x))

    # Planet: quad-sphere terrain. Shape and LOD tuning are C++ defaults on AQuadSpherePlanet;
    # only identity, size and material are set here. Body is its hidden safety sphere.
    planet_class = unreal.load_class(None, "/Script/gamespace.QuadSpherePlanet")
    planet = upsert_actor(eas, actors, "Planet_" + PLANET_NAME, planet_class, PLANET_LOCATION_CM,
                          replace_other_class=True)
    planet.set_actor_scale3d(unreal.Vector(1, 1, 1))  # tiles are in cm; scale must stay 1
    planet.set_editor_property("display_name", unreal.Text(PLANET_NAME))
    planet.set_editor_property("radius_km", PLANET_RADIUS_CM / 100000.0)
    planet.set_editor_property("terrain_material", planet_material)
    planet.set_editor_property("sky_zenith_color", unreal.LinearColor(*PAINTED_SKY_ZENITH, 1.0))
    planet.set_editor_property("sky_horizon_color", unreal.LinearColor(*PAINTED_SKY_HORIZON, 1.0))
    planet.get_component_by_class(unreal.StaticMeshComponent).set_static_mesh(planet_mesh)

    # Distant bodies. Mesh first, then the radius: OnConstruction scales by the mesh's bounds.
    body_class = unreal.load_class(None, "/Script/gamespace.DistantBody")
    yaw, elevation = math.radians(GIANT_YAW_DEG), math.radians(GIANT_ELEVATION_DEG)
    giant_cm = tuple(GIANT_DISTANCE_KM * 100000.0 * c for c in
                     (math.cos(elevation) * math.cos(yaw), math.cos(elevation) * math.sin(yaw), math.sin(elevation)))
    giant = upsert_actor(eas, actors, "GasGiant_" + GIANT_NAME, body_class, giant_cm, replace_other_class=True)
    moon = upsert_actor(eas, actors, "Moon_" + MOON_NAME, body_class, PLANET_LOCATION_CM, replace_other_class=True)
    for actor, name, radius, material in ((giant, GIANT_NAME, GIANT_RADIUS_KM, body_materials["giant"]),
                                          (moon, MOON_NAME, MOON_RADIUS_KM, body_materials["moon"])):
        body = actor.get_editor_property("body")
        body.set_static_mesh(planet_mesh)
        body.set_material(0, material)
        actor.set_editor_property("display_name", unreal.Text(name))
        actor.set_editor_property("radius_km", radius)
    giant.set_editor_property("ring_outer_radius_km", GIANT_RING_OUTER_KM)
    giant.set_editor_property("axial_tilt_deg", GIANT_AXIAL_TILT_DEG)
    giant.set_editor_property("spin_period_seconds", GIANT_SPIN_SECONDS)
    giant.get_editor_property("rings").set_material(0, body_materials["rings"])
    moon.set_editor_property("spin_period_seconds", 0.0)
    for key, value in MOON_ORBIT.items():
        moon.set_editor_property(key, value)
    moon.set_editor_property("orbit_center", planet)  # last: re-runs OnConstruction onto the orbit
    log("%s at %.0f km, %s orbiting %s at %.0f km" % (giant.get_actor_label(), GIANT_DISTANCE_KM, moon.get_actor_label(),
                                                     planet.get_actor_label(), MOON_ORBIT["orbit_radius_km"]))

    # Exposure: clamp auto exposure to one value, i.e. fixed. Then the grade.
    ppv = upsert_actor(eas, actors, "PP_SpaceExposure", unreal.PostProcessVolume)
    ppv.set_editor_property("unbound", True)
    settings = ppv.get_editor_property("settings")
    for key, value in ((("auto_exposure_min_brightness", EXPOSURE_EV100),
                        ("auto_exposure_max_brightness", EXPOSURE_EV100)) + POST_SETTINGS):
        settings.set_editor_property("override_" + key, True)
        settings.set_editor_property(key, value)
    ppv.set_editor_property("settings", settings)
    log("post process: %s" % ", ".join(key for key, _ in POST_SETTINGS))

    if not les.save_current_level():
        raise RuntimeError("could not save " + LEVEL)
    log("saved %s" % LEVEL)


def main():
    cube, planet_mesh = import_sources()
    sky_material = build_starfield_material(cube)
    planet_material = build_planet_material()
    build_dust_material()
    build_tunnel_material()
    build_fog_material()
    body_materials = {
        "giant": build_body_material(GAS_GIANT_MATERIAL, GAS_GIANT_HLSL, 0.95, with_time=True),
        "moon": build_body_material(MOON_MATERIAL, MOON_HLSL, 0.9, with_time=False),
        "rings": build_rings_material(),
    }
    build_level(sky_material, planet_mesh, planet_material, body_materials)

    start = unreal.Vector(0.0, 0.0, 300.0)
    centre = unreal.Vector(*PLANET_LOCATION_CM)
    surface_m = ((centre - start).length() - PLANET_RADIUS_CM) / 100.0
    log("sea level %.0f m below PlayerStart: %.0f s at 120 m/s, %.0f s at 300 m/s boost" % (
        surface_m, surface_m / 120.0, surface_m / 300.0))


main()
