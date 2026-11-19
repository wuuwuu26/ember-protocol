# -*- coding: utf-8 -*-
"""确认手工三平面需要的节点类名与引脚名。"""
import unreal
L = "[引脚]"
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
P, N = "/Game/_Probe", "M_ProbePins"
if unreal.EditorAssetLibrary.does_asset_exist("%s/%s" % (P, N)):
    unreal.EditorAssetLibrary.delete_asset("%s/%s" % (P, N))
mat = AT.create_asset(N, P, unreal.Material, unreal.MaterialFactoryNew())

def make(cls_name):
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        unreal.log("%s ❌ 类不存在: %s" % (L, cls_name))
        return None
    return MEL.create_material_expression(mat, cls, 0, 0)

wp = make("MaterialExpressionWorldPosition")
vn = make("MaterialExpressionVertexNormalWS")
ts = make("MaterialExpressionTextureSampleParameter2D")
ap = make("MaterialExpressionAppendVector")
px = make("MaterialExpressionPower")
dv = make("MaterialExpressionDivide")
ab = make("MaterialExpressionAbs")
cm = make("MaterialExpressionComponentMask")
unreal.log("%s 节点创建: wp=%s vn=%s ts=%s ap=%s" % (L, bool(wp), bool(vn), bool(ts), bool(ap)))

# TextureSample 的 UV 输入引脚名
for pin in ("UVs", "Coordinates", "UV"):
    try:
        MEL.connect_material_expressions(ap, "", ts, pin)
        unreal.log("%s ✓ TextureSample 输入引脚 = %s" % (L, pin))
        break
    except Exception as e:
        unreal.log("%s ✗ %s (%s)" % (L, pin, str(e)[:50]))

# AppendVector 输入
for pin in ("A", "B"):
    try:
        MEL.connect_material_expressions(cm, "", ap, pin)
    except Exception as e:
        unreal.log("%s ✗ Append.%s: %s" % (L, pin, str(e)[:50]))
unreal.log("%s Append A/B 连接完成" % L)

# ComponentMask 输入
try:
    MEL.connect_material_expressions(wp, "", cm, "")
    unreal.log("%s ✓ ComponentMask 默认输入可用" % L)
except Exception as e:
    unreal.log("%s ✗ ComponentMask: %s" % (L, str(e)[:60]))

# WorldPosition 输出引脚
for out in ("", "XYZ", "XY"):
    try:
        c2 = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, 0, 300)
        MEL.connect_material_expressions(wp, out, c2, "")
        unreal.log("%s ✓ WorldPosition 输出 '%s' 可用" % (L, out))
    except Exception as e:
        unreal.log("%s ✗ WorldPosition 输出 '%s': %s" % (L, out, str(e)[:40]))
unreal.log("%s 探测结束" % L)
