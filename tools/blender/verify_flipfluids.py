"""验证 FLIP Fluids 插件能否在 Blender 5.2 无头模式启用。"""
import bpy
import addon_utils

mod = addon_utils.enable("flip_fluids_addon", default_set=True, persistent=True)
print("FF_ENABLED", mod is not None)
if mod:
    info = getattr(mod, "bl_info", {})
    print("FF_VERSION", info.get("version"), info.get("name"))
print("FF_OPS_FLIP", hasattr(bpy.ops, "flip_fluids"))
print("FF_DOMAIN_OP", hasattr(bpy.ops.object, "flip_fluids_helper_addon_disable"))
names = [m.__name__ for m in bpy.context.preferences.addons]
print("FF_ADDONS", names)
print("FF_VERIFY_DONE")
