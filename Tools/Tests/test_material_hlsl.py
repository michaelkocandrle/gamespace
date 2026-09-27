"""Static check of the HLSL in the material builders (no Unreal needed):

    python Tools/Tests/test_material_hlsl.py

Fails on a cast of the primitive's LocalToWorld / WorldToLocal (FDFMatrix / FDFInverseMatrix structs) straight to a
matrix type: HLSL flattens the struct and takes its first floats in memory order, which is not the rotation block -
a face with the normal (0, 0, 1) turned into a zero vector, normalize() made it NaN and the ship master rendered
black on every flat face (WORKFLOW dg, 27. 9. 2026). Use DFToFloat3x3(...) or the struct's .M.
Also fails on a normal map sampled raw with its blue channel used: normal maps are BC5, the blue channel reads 0.
Prints "HLSLTEST PASS" / "HLSLTEST FAIL" lines.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES = [os.path.join(REPO, "Tools", "Assets", f) for f in sorted(os.listdir(os.path.join(REPO, "Tools", "Assets")))
           if f.endswith(".py")]
# (float3x3)GetPrimitiveData(Parameters).WorldToLocal - no .M after the member
STRUCT_CAST = re.compile(r"\(\s*float[34]x[34]\s*\)\s*GetPrimitiveData\([^)]*\)\.(?:Previous)?(?:LocalToWorld|WorldToLocal)\b(?!\.M)")
# Texture2DSample(TexN, ...).rgb * 2 - 1 on the normal-map input TexN
RAW_NORMAL = re.compile(r"Texture2DSample\(\s*TexN\s*,[^;]*\)\s*\.rgb\s*\*\s*2")


def main():
    failures = 0
    for path in SOURCES:
        text = open(path, encoding="utf-8").read()
        for rx, what in ((STRUCT_CAST, "cast of a primitive matrix struct (use DFToFloat3x3)"),
                         (RAW_NORMAL, "raw normal-map sample with its blue channel (BC5 has none, rebuild z)")):
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                print("HLSLTEST FAIL %s:%d %s: %s" % (os.path.relpath(path, REPO), line, what, m.group(0)))
                failures += 1
    print("HLSLTEST %s (%d files, %d failures)" % ("PASS" if not failures else "FAIL", len(SOURCES), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
