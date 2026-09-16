"""Copies the UE5 Mannequin pack (Manny/Quinn, Unarmed animations, rigs) into the project.

Plain Python, editor closed:

    python Tools/Assets/install_mannequin_pack.py [--engine "C:/Program Files/Epic Games/UE_5.8"]

This is what the editor's "Add Feature or Content Pack > Characters" does for a template's
shared resources: the files under Templates/TemplateResources/High/Characters/Content go to
Content/Characters, which mounts them at /Game/Characters/Mannequins - the path the assets
reference each other by. Files that already exist are left alone; nothing is renamed.
"""

import argparse
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACK = os.path.join("Templates", "TemplateResources", "High", "Characters", "Content")

# Checked after copying: what APlayerCharacter and its anim instance load.
REQUIRED = [
    "Mannequins/Meshes/SKM_Manny_Simple.uasset",
    "Mannequins/Meshes/SK_Mannequin.uasset",
    "Mannequins/Anims/Unarmed/MM_Idle.uasset",
    "Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd.uasset",
    "Mannequins/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd.uasset",
    "Mannequins/Anims/Unarmed/Jump/MM_Jump.uasset",
    "Mannequins/Anims/Unarmed/Jump/MM_Fall_Loop.uasset",
    "Mannequins/Anims/Unarmed/Jump/MM_Land.uasset",
    "Mannequins/Anims/Unarmed/BS_Idle_Walk_Run.uasset",
]


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default=r"C:\Program Files\Epic Games\UE_5.8")
    args = parser.parse_args(argv)

    source = os.path.join(args.engine, PACK)
    target = os.path.join(REPO, "Content", "Characters")
    if not os.path.isdir(source):
        print("FAILED: %s not found" % source)
        return 1

    copied = skipped = 0
    for folder, _, files in os.walk(source):
        for name in files:
            src = os.path.join(folder, name)
            dst = os.path.join(target, os.path.relpath(src, source))
            if os.path.exists(dst):
                skipped += 1
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    missing = [r for r in REQUIRED if not os.path.isfile(os.path.join(target, r))]
    print("copied %d, already present %d, into %s" % (copied, skipped, target))
    if missing:
        print("FAILED: missing %s" % ", ".join(missing))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
