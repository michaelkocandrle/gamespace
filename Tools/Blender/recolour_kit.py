"""Restyle a downloaded asset kit into the gamespace palette, in Blender.

    blender <soubor.blend> --python Tools/Blender/recolour_kit.py
    (nebo přes Blender MCP: exec(open(r"...\\recolour_kit.py").read()))

Co to dělá s každým materiálem, který má Principled BSDF a obrázkovou texturu v Base Color:

1. **Gunmetal**: texturu odbarví (Hue/Saturation, saturace 0,12), zesvětlí (Value 2,1 - kity bývají
   hodně tmavé) a vynásobí naší šedomodrou. Kresba panelů, švy a špína z textury zůstanou.
2. **Oranžový akcent**: spočítá, jak moc je texel červený (R minus to větší z G a B) a kde to
   přeleze práh, přebarví na oranžovou. Tím se převezmou akcentní pruhy kitu, pokud je má.
3. **Svítící pásy**: když kit dodává emisivní mapu (`*_Emissive.png`), použije ji jako sílu emise
   a obarví ji na oranžovou. Tohle je to, co nakonec dělá identitu - u Quaternius MegaKitu mají
   díly akcent jen v emisivní mapě, v base colouru žádný červený pruh není.

Materiál se označí `recoloured`, takže druhé spuštění ho nechá být.
"""

import os
import bpy

# Paleta gamespace, lineární RGB. Gunmetal odpovídá trupu Vanguardu (ošoupaná šedomodrá ocel),
# oranžová je akcent Halcyon Freightworks.
GUNMETAL = (0.62, 0.65, 0.70)
ORANGE = (0.85, 0.34, 0.06)
SATURATION = 0.12
VALUE_GAIN = 2.1
EMISSIVE_GAIN = 9.0
ACCENT_FROM = (0.04, 0.18)      # jak červený musí texel být, aby se bral jako akcent


def texture_dir():
    """Kde hledat emisivní mapy: vedle první načtené textury."""
    for image in bpy.data.images:
        if image.filepath:
            path = bpy.path.abspath(image.filepath)
            if os.path.exists(path):
                return os.path.dirname(path)
    return None


def emissive_for(image_name, folder):
    if not folder:
        return None
    stem = image_name.split("_BaseColor")[0].split(".")[0]
    for candidate in ("%s_Emissive.png" % stem, "T_Trim_01_Emissive.png"):
        path = os.path.join(folder, candidate)
        if os.path.exists(path):
            return path
    return None


def recolour(mat, folder):
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return False
    link = next((l for l in nt.links if l.to_node == bsdf and l.to_socket.name == "Base Color"), None)
    if not link or link.from_node.type != 'TEX_IMAGE':
        return False
    src = link.from_node
    x, y = src.location.x + 300, src.location.y

    sep = nt.nodes.new("ShaderNodeSeparateColor"); sep.location = (x, y + 300)
    nt.links.new(src.outputs["Color"], sep.inputs[0])
    gb = nt.nodes.new("ShaderNodeMath"); gb.operation = 'MAXIMUM'; gb.location = (x + 180, y + 380)
    nt.links.new(sep.outputs[1], gb.inputs[0]); nt.links.new(sep.outputs[2], gb.inputs[1])
    diff = nt.nodes.new("ShaderNodeMath"); diff.operation = 'SUBTRACT'; diff.location = (x + 340, y + 340)
    nt.links.new(sep.outputs[0], diff.inputs[0]); nt.links.new(gb.outputs[0], diff.inputs[1])
    mask = nt.nodes.new("ShaderNodeMapRange"); mask.location = (x + 500, y + 340)
    mask.inputs['From Min'].default_value = ACCENT_FROM[0]
    mask.inputs['From Max'].default_value = ACCENT_FROM[1]
    nt.links.new(diff.outputs[0], mask.inputs['Value'])

    hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.location = (x, y)
    hsv.inputs['Saturation'].default_value = SATURATION
    hsv.inputs['Value'].default_value = VALUE_GAIN
    nt.links.new(src.outputs["Color"], hsv.inputs['Color'])
    tint = nt.nodes.new("ShaderNodeMixRGB"); tint.blend_type = 'MULTIPLY'; tint.location = (x + 200, y)
    tint.inputs['Fac'].default_value = 1.0
    tint.inputs['Color2'].default_value = (GUNMETAL[0], GUNMETAL[1], GUNMETAL[2], 1.0)
    nt.links.new(hsv.outputs['Color'], tint.inputs['Color1'])

    accent = nt.nodes.new("ShaderNodeMixRGB"); accent.location = (x + 700, y + 60)
    accent.inputs['Color2'].default_value = (ORANGE[0], ORANGE[1], ORANGE[2], 1.0)
    nt.links.new(mask.outputs['Result'], accent.inputs['Fac'])
    nt.links.new(tint.outputs['Color'], accent.inputs['Color1'])
    nt.links.new(accent.outputs['Color'], bsdf.inputs['Base Color'])

    path = emissive_for(src.image.name, folder) if src.image else None
    if path:
        image = bpy.data.images.get(os.path.basename(path)) or bpy.data.images.load(path, check_existing=True)
        image.colorspace_settings.name = 'Non-Color'
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = image
        tex.location = (src.location.x, src.location.y - 620)
        uv = next((l for l in nt.links if l.to_node == src), None)
        if uv:
            nt.links.new(uv.from_socket, tex.inputs['Vector'])
        channel = nt.nodes.new("ShaderNodeSeparateColor"); channel.location = (tex.location.x + 150, tex.location.y - 150)
        nt.links.new(tex.outputs['Color'], channel.inputs[0])
        gain = nt.nodes.new("ShaderNodeMath"); gain.operation = 'MULTIPLY'
        gain.inputs[1].default_value = EMISSIVE_GAIN
        gain.location = (tex.location.x + 300, tex.location.y)
        nt.links.new(channel.outputs[0], gain.inputs[0])
        bsdf.inputs['Emission Color'].default_value = (ORANGE[0], ORANGE[1], ORANGE[2], 1.0)
        nt.links.new(gain.outputs[0], bsdf.inputs['Emission Strength'])

    mat["recoloured"] = True
    return True


def main():
    folder = texture_dir()
    done = [m.name for m in bpy.data.materials
            if m.use_nodes and not m.get("recoloured") and recolour(m, folder)]
    print("recolour_kit: %d materiálů přebarveno" % len(done))
    return done


if __name__ == "__main__":
    main()
