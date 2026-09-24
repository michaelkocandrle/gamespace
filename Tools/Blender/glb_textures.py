"""Unpack the PBR textures of an AI GLB (Higgsfield / Meshy) into the four maps build_ai_ship.py reads.

    blender -b --python Tools/Blender/glb_textures.py -- ArtSource/Ships/<Ship>/Higgsfield/<model>.glb <out_dir>

Writes <out_dir>/base_color.png, normal.png, roughness.png and metallic.png. glTF packs roughness and
metallic into one image (G roughness, B metallic); they are split into two greyscale maps. The GLB
itself is never modified. Prints GLBTEX {...} with the paths for the recipe's "textures".
"""
import json
import os
import sys

import bpy
import numpy as np


def save_array(arr, w, h, path, colour):
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


def pixels(img):
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(h, w, 4), w, h


def main(argv):
    glb, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    mats = [m for o in bpy.data.objects if o.type == "MESH" for m in o.data.materials if m and m.use_nodes]
    if not mats:
        raise SystemExit("glb_textures: no node material in %s" % glb)
    nt = mats[0].node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")

    def image_into(socket):
        """The image texture feeding a BSDF input, through Separate Color / Normal Map nodes."""
        stack = [l.from_node for l in socket.links]
        while stack:
            n = stack.pop()
            if n.type == "TEX_IMAGE":
                return n.image
            for inp in n.inputs:
                stack.extend(l.from_node for l in inp.links)
        return None

    written = {}
    base = image_into(bsdf.inputs["Base Color"])
    arr, w, h = pixels(base)
    save_array(arr, w, h, os.path.join(out, "base_color.png"), True)
    written["base_color"] = os.path.join(out, "base_color.png")
    normal = image_into(bsdf.inputs["Normal"])
    if normal:
        arr, w, h = pixels(normal)
        save_array(arr, w, h, os.path.join(out, "normal.png"), False)
    else:
        arr = np.tile(np.array([0.5, 0.5, 1.0, 1.0], np.float32), (h, w, 1))
        save_array(arr, w, h, os.path.join(out, "normal.png"), False)
    written["normal"] = os.path.join(out, "normal.png")
    mr = image_into(bsdf.inputs["Roughness"]) or image_into(bsdf.inputs["Metallic"])
    if mr:
        arr, w, h = pixels(mr)
        rough, metal = arr[..., 1], arr[..., 2]
    else:
        rough = np.full((h, w), bsdf.inputs["Roughness"].default_value, np.float32)
        metal = np.full((h, w), bsdf.inputs["Metallic"].default_value, np.float32)
    for name, ch in (("roughness", rough), ("metallic", metal)):
        grey = np.stack([ch, ch, ch, np.ones_like(ch)], axis=-1)
        save_array(grey, grey.shape[1], grey.shape[0], os.path.join(out, name + ".png"), False)
        written[name] = os.path.join(out, name + ".png")
    tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == "MESH" for p in o.data.polygons)
    print("GLBTEX " + json.dumps({"textures": written, "triangles": tris, "materials": len(mats),
                                  "base_size": list(base.size)}))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
