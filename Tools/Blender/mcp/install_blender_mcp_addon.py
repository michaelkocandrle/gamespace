"""Installs the Blender MCP addon (bundled in the blender-mcp package uvx downloaded) with telemetry off.
Run once after `uvx blender-mcp` has fetched the package:
  blender -b --python Tools/Blender/mcp/install_blender_mcp_addon.py
"""
import glob, os, shutil, sys
import addon_utils
import bpy

found = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\uv\cache\archive-v0\*\Lib\site-packages\blender_mcp\bundled\addon.py"))
if not found:
    sys.exit("MCPINSTALL blender_mcp package not in the uv cache: run uvx blender-mcp once first")
SRC = max(found, key=os.path.getmtime)
addons = bpy.utils.user_resource('SCRIPTS', path="addons", create=True)
dst = os.path.join(addons, "blender_mcp_addon.py")
shutil.copyfile(SRC, dst)
print("MCPINSTALL copied to", dst)
bpy.ops.preferences.addon_refresh()
addon_utils.enable("blender_mcp_addon", default_set=True, persistent=True)
prefs = bpy.context.preferences.addons.get("blender_mcp_addon")
print("MCPINSTALL enabled:", prefs is not None)
if prefs:
    prefs.preferences.telemetry_consent = False
    print("MCPINSTALL telemetry_consent:", prefs.preferences.telemetry_consent)
bpy.ops.wm.save_userpref()
print("MCPINSTALL prefs saved")
