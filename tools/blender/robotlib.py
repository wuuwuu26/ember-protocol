"""
余火协议 · Blender 资产管线共享库
================================================
被 build_*.py 引用的通用能力：图元、细节生成器、材质、绑定、UV/LOD、导出、渲染。

设计原则:
  1. 所有几何走同一套图元函数，保证风格统一
  2. 细节靠"细节生成器"批量产生（greeble / grille / panel / piston / cable），
     而不是手写每个零件 —— 这是程序化建模能追上人工效率的关键
  3. 部件保持独立对象直到最后一刻，因为游戏里每个部件要能独立摧毁与替换
"""

import bpy
import bmesh
import math
import os
import random
import mathutils

Vector = mathutils.Vector


# ═══════════════════════════════════════════════════════════
# 场景
# ═══════════════════════════════════════════════════════════

def new_scene():
    """清空场景，返回一个干净的工作环境。"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures,
                  bpy.data.lights, bpy.data.cameras, bpy.data.collections,
                  bpy.data.curves, bpy.data.worlds):
        for item in list(block):
            if item.users == 0:
                try:
                    block.remove(item)
                except Exception:
                    pass


def activate(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def assign_mat(ob, mat):
    """清空并赋予材质。一个对象一个材质槽 —— 对应游戏里每部件独立材质。"""
    if ob is None or not hasattr(ob.data, "materials"):
        return
    ob.data.materials.clear()
    ob.data.materials.append(mat)


# ═══════════════════════════════════════════════════════════
# 图元
# ═══════════════════════════════════════════════════════════

def _finish(ob, mat, bev, segments=2, angle=38.0):
    if bev and bev > 0:
        dims = ob.dimensions
        w = min(bev, min(dims) * 0.26) if min(dims) > 1e-6 else 0.0
        if w > 1e-5:
            activate(ob)
            m = ob.modifiers.new("bev", 'BEVEL')
            m.width = w
            m.segments = segments
            m.limit_method = 'ANGLE'
            m.angle_limit = math.radians(angle)
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception:
                pass

    # ── 平滑着色 + 按角度保留硬边（第八十二轮）──
    # 之前只有 loft / lathe / sweep 设了 use_smooth，球体 / 圆柱 / 圆环
    # 全都是**平面着色**：导出后每个多边形一个法线，球面上就是一瓣一瓣的
    # 刻面。巡逻机是 36 段的球，正面看是一朵"花瓣"，非常显眼。
    # 这里统一：所有面设为光滑，再把夹角 > 35° 的边标成锐边 ——
    # 平面（箱体）保持棱角，曲面变平滑，是机械件该有的读法。
    try:
        me = ob.data
        for poly in me.polygons:
            poly.use_smooth = True
        bm = bmesh.new()
        bm.from_mesh(me)
        limit = math.radians(35.0)
        for e in bm.edges:
            if len(e.link_faces) == 2:
                try:
                    if e.calc_face_angle() > limit:
                        e.smooth = False
                except Exception:
                    pass
        bm.to_mesh(me)
        bm.free()
    except Exception:
        pass

    if mat:
        assign_mat(ob, mat)
    return ob


def box(name, size, loc, rot=(0, 0, 0), mat=None, bev=0.014, segments=2):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(ob, mat, bev, segments)


def prism(name, size, loc, rot=(0, 0, 0), top=(1.0, 1.0), top_off=(0.0, 0.0),
          bottom=(1.0, 1.0), bottom_off=(0.0, 0.0), mat=None,
          bev=0.010, segments=2):
    """梯形棱柱（上/下截面可分别缩放、平移）。

    为什么需要它：方块拼出来的机甲永远是"一摞纸箱"。真实机甲的装甲板
    几乎都是**上窄下宽 / 前倾收口**的梯形 —— 肩甲外张、胸腔下收、
    小腿上粗下细。只把几个关键块换成 prism，剪影立刻从"积木"变成"机甲"。

    top / bottom 是截面在 X/Y 上的缩放比，top_off / bottom_off 是截面偏移
    （做前倾、侧倾的斜面）。
    """
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.x = v.co.x * top[0] + top_off[0]
            v.co.y = v.co.y * top[1] + top_off[1]
        else:
            v.co.x = v.co.x * bottom[0] + bottom_off[0]
            v.co.y = v.co.y * bottom[1] + bottom_off[1]
    bmesh.ops.scale(bm, vec=Vector((size[0], size[1], size[2])),
                    verts=bm.verts)
    # 直接在 bmesh 里倒角：新建的 object 还没进 depsgraph，
    # ob.dimensions 此时是 0，_finish 里的倒角宽度会算成 0（静默不生效）。
    w = min(bev, min(size) * 0.24) if bev else 0.0
    if w > 1e-5:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                        offset=w, segments=segments, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    activate(ob)
    if mat:
        assign_mat(ob, mat)
    return ob


def bolt_ring(name, center, radius, count, mat, axis='Y', r=0.018, depth=0.02,
              phase=0.0):
    """一圈螺栓 —— 装甲分块最省面数的"工艺感"来源。"""
    out = []
    for i in range(count):
        a = phase + i * 2.0 * math.pi / count
        if axis == 'Y':
            p = (center[0] + math.cos(a) * radius, center[1],
                 center[2] + math.sin(a) * radius)
            rot = (math.radians(90), 0, 0)
        elif axis == 'X':
            p = (center[0], center[1] + math.cos(a) * radius,
                 center[2] + math.sin(a) * radius)
            rot = (0, math.radians(90), 0)
        else:
            p = (center[0] + math.cos(a) * radius,
                 center[1] + math.sin(a) * radius, center[2])
            rot = (0, 0, 0)
        out.append(cyl("%s_%02d" % (name, i + 1), r, depth, p, rot=rot,
                       mat=mat, verts=6, bev=0.002, segments=1))
    return out


def nozzle(name, radius, depth, loc, rot=(0, 0, 0), mat=None, inner=None,
           verts=20):
    """喷口：外锥 + 内锥（内壁用自发光/深色），推进器与炮口的通用件。"""
    out = [cone("%s_bell" % name, radius, radius * 0.62, depth, loc,
                rot=rot, mat=mat, verts=verts, bev=0.004)]
    if inner:
        d = Vector((0, 0, depth * 0.92))
        d.rotate(mathutils.Euler(rot, 'XYZ'))
        out.append(cone("%s_inner" % name, radius * 0.80, radius * 0.55,
                        depth * 0.55,
                        (loc[0] + d.x * 0.18, loc[1] + d.y * 0.18,
                         loc[2] + d.z * 0.18),
                        rot=rot, mat=inner, verts=verts, bev=0.002))
    return out


def cyl(name, radius, depth, loc, rot=(0, 0, 0), mat=None, verts=20,
        bev=0.006, segments=2):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        vertices=verts, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, mat, bev, segments)


def cyl_between(name, p1, p2, radius, mat=None, verts=20, bev=0.006,
                segments=2):
    """由**两个端点**直接建圆柱（第七十五轮）。

    为什么不继续用 `cyl(名字, 半径, 长度, 中点, rot=(倾角,0,0))`：
    那种写法要手工保证「长度 = 三维距离」「中点 = 两端中点」「倾角符号对」，
    四条腿 × 五个机体 = 二十处手算，错一处就是"腿在膝盖断成两截"
    （本轮实测运输机/巨象的踝端被甩到膝那一侧，脚掌和小腿脱开 20cm）。
    这里只需要给两个真实关节位置，长度/朝向/中点全部由几何算出，不可能对不上。

    与 `cyl` 的区别：`cyl` 的 `loc` 是物体原点、`depth` 是全长；
    这里的 `loc` 取两点中点，物体原点仍在圆柱几何中心，便于绑定。
    """
    p1 = Vector(p1)
    p2 = Vector(p2)
    d = p2 - p1
    length = d.length
    if length < 1e-5:
        return cyl(name, radius, 0.01, tuple(p1), mat=mat, verts=verts,
                   bev=bev, segments=segments)
    mid = (p1 + p2) * 0.5
    direction = d.normalized()
    up = Vector((0, 0, 1))
    if abs(direction.dot(up)) > 0.999:
        up = Vector((0, 1, 0))
    x_ax = direction.cross(up).normalized()
    y_ax = direction.cross(x_ax).normalized()
    rot = mathutils.Matrix((x_ax, y_ax, direction)).transposed().to_euler()
    return cyl(name, radius, length, tuple(mid), rot=tuple(rot), mat=mat,
               verts=verts, bev=bev, segments=segments)


def cone(name, r1, r2, depth, loc, rot=(0, 0, 0), mat=None, verts=18, bev=0.005):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth,
                                    vertices=verts, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, mat, bev, 2)


def sphere(name, radius, loc, mat=None, segments=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segments,
                                         ring_count=rings, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, mat, 0, 1)


# ═══════════════════════════════════════════════════════════
# 曲面图元 —— "不要方块"的唯一解法
# ═══════════════════════════════════════════════════════════
#
# 只用 box / prism 拼出来的东西，无论加多少倒角，剪影永远是直线段 + 直角。
# 真实机甲（以及任何工业产品）的形体语言是：**壳体是曲面，装甲板是它的切面**。
# 所以这里补三种曲面：椭球（肩甲穹顶 / 关节球）、环面（关节箍 / 管道弯头）、
# 沿路径的圆管（液压软管 / 线束）。

def ellipsoid(name, radii, loc, rot=(0, 0, 0), mat=None,
              segments=28, rings=18, cut_below=None):
    """椭球。radii=(rx, ry, rz)。

    cut_below：给一个相对值（-1..1），把该高度以下的部分切掉 ——
    用来做"半穹顶"肩甲：cut_below=0 就是标准半球。
    """
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=segments,
                                         ring_count=rings, location=loc,
                                         rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (radii[0], radii[1], radii[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    if cut_below is not None and cut_below > -1.0:
        # 用 bmesh 切：保留 z >= cut_below * rz 的部分，并把切面封口
        #
        # ⚠️ 旧实现只删面、再 holes_fill 封口，有三个后果（第七十五轮修复）：
        #   1. 封口面没有 UV —— UE 里那张面会采样到贴图左上角的一点，
        #      渲染出来是一个纯黑/纯色的"洞"，看起来就是"碗底"；
        #   2. holes_fill 的法线方向不确定，背面剔除后从下方看不见，
        #      于是半球变成一个空心壳，能看见内壁；
        #   3. 切边留下的孤立顶点没有被删除，LOD 生成会因此报错。
        # 修法：按顶点删（连带删面）→ 全部法线重算朝外 → 三角化 + 补 UV。
        me = ob.data
        bm = bmesh.new()
        bm.from_mesh(me)
        zc = cut_below * radii[2]
        keep_v = [v for v in bm.verts if v.co.z >= zc - 1e-5]
        drop_v = [v for v in bm.verts if v.co.z < zc - 1e-5]
        bmesh.ops.delete(bm, geom=drop_v, context='VERTS')
        # 封口：用剩余边界环建面（nfgon → 三角化）
        edges = [e for e in bm.edges if e.is_boundary]
        if edges and keep_v:
            try:
                bmesh.ops.holes_fill(bm, edges=edges)
            except Exception:
                pass
        # 封口面（holes_fill 生成的 ngon）法线可能还没算出来，先更新一次
        bm.normal_update()
        # 法线修正（第七十五轮）：
        # 切开的半球不是封闭体，recalc_face_normals 的取向不可靠，切面附近的面
        # 会残留朝内法线。Blender 默认双面渲染，看不出来；UE 是单面渲染，
        # 这些面导入后直接消失（"建模不完整"的来源之一）。
        #
        # 逐面判定（按面中心相对球心）对封口面附近的侧面会误判（面中心在
        # 切面上方但顶点在切面上），所以改为两步：
        #   1. 封口面（全部顶点都在切面上）→ 法线朝下；
        #   2. 其余面 → 用"面中心到球心"的方向做参考，但容差放宽，
        #      并且对判定为"几乎垂直"的面（|dot| < 0.02）不做翻转，避免抖动。
        for f in bm.faces:
            on_rim = all(v.co.z <= zc + 1e-4 for v in f.verts)
            if on_rim:
                want = (0.0, 0.0, -1.0)
            else:
                c = f.calc_center_median()
                ln = math.sqrt(c.x * c.x + c.y * c.y + c.z * c.z)
                want = ((c.x / ln, c.y / ln, c.z / ln) if ln > 1e-9
                        else (0.0, 0.0, 1.0))
            d = f.normal.dot(want)
            if d < -0.02:
                f.normal_flip()
        # 三角化：导入 UE 前必须三角化，否则 ngon 封口面会丢失
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        bm.to_mesh(me)
        bm.free()
        # 切面新增的面没有 UV：补一份柱面 UV，避免 UE 里采到单点颜色
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        uv = me.uv_layers.active.data
        for poly in me.polygons:
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uv[li].uv = (0.5 + co.x * 0.5, 0.5 + co.y * 0.5)
    return _finish(ob, mat, 0, 1)


def torus(name, major_r, minor_r, loc, rot=(0, 0, 0), mat=None,
          major_seg=28, minor_seg=10):
    """环面：关节箍、管道弯头、护圈。"""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_r, minor_radius=minor_r,
        major_segments=major_seg, minor_segments=minor_seg,
        location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    return _finish(ob, mat, 0, 1)


def capsule(name, radius, length, loc, rot=(0, 0, 0), mat=None,
            verts=20, segments=24, rings=14):
    """胶囊（圆柱 + 两端半球）：四肢、液压缸、储气罐。

    用椭球实现：半径 = radius，Z 半轴 = length/2 + radius。
    末端是球面，跟"圆柱 + 平端盖"的观感差别很大 —— 后者一眼就是低模。
    """
    return ellipsoid(name, (radius, radius, length * 0.5 + radius),
                     loc, rot=rot, mat=mat, segments=segments, rings=rings)


def tube(name, points, radius, mat, res=8, bevel_res=3, smooth=True):
    """沿折线生成**平滑圆管**（软管 / 线束 / 弯管）。

    用 Blender 的曲线 + bevel 转网格：折点自动圆滑过渡，
    比"两点之间插一根圆柱"真实得多 —— 后者在拐角处是硬折。
    """
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = res
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.fill_mode = 'FULL'
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        bp = sp.bezier_points[i]
        bp.co = Vector(p)
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    sp.use_smooth = smooth
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    activate(ob)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.active_object
    if mat:
        assign_mat(ob, mat)
    return ob


def rounded_box(name, size, loc, rot=(0, 0, 0), mat=None, radius=0.03,
                segments=4):
    """圆角方块：倒角段数拉到 4，边缘就是连续曲面而不是"削了一刀"。"""
    return prism(name, size, loc, rot=rot, mat=mat, bev=radius,
                 segments=segments)



# ═══════════════════════════════════════════════════════════
# 细节生成器 —— 精细度的主要来源
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# 高级建模 —— 放样 / 旋转 / 扫掠 / 细分 / 布尔
# ═══════════════════════════════════════════════════════════
#
# 前面那些图元（box / cyl / ellipsoid）本质是"预制件"：
# 每个都是封闭的、均匀的、无变化的形体。用它们拼出来的东西，
# 无论怎么摆都带着"零件感"—— 因为真实工业造型里的曲面是**连续的**：
# 一个胸腔从腰部的方形截面，经过收腰、外扩、到胸口的圆角梯形，
# 是**一条放样曲线**，不是"方块 + 球 + 圆锥"三段拼接。
#
# 所以这里补四类真正的高级操作：
#   loft   多截面放样   —— 截面形状沿轴连续渐变（圆↔方、粗↔细、直↔弯）
#   lathe  旋转体       —— 一条轮廓线绕轴旋转（喷口、轮毂、关节罩）
#   sweep  沿路径扫掠   —— 截面沿曲线走（护甲边条、线束、管廊）
#   subd/shell/bool     —— 细分平滑 / 抽壳 / 挖孔

def _superellipse(a, rx, ry, n):
    """超椭圆参数方程。

    n=2 → 椭圆；n=4 → 圆角方；n=8 → 近方；n→∞ → 矩形。
    这是"一个截面从圆连续变成方"的关键 —— 放样时每层给不同的 n，
    形体就会从管状平滑过渡成装甲块，而不会出现硬接缝。
    """
    c, s = math.cos(a), math.sin(a)
    if n <= 2.0 + 1e-6:
        return rx * c, ry * s
    p = 2.0 / n
    x = rx * math.copysign(abs(c) ** p, c) if abs(c) > 1e-12 else 0.0
    y = ry * math.copysign(abs(s) ** p, s) if abs(s) > 1e-12 else 0.0
    return x, y


def loft(name, rings, seg=28, mat=None, close_start=True, close_end=True,
         smooth=True, bev=0.0, segments=2, rot=(0, 0, 0), loc=(0, 0, 0)):
    """多截面放样（loft）—— 本库最重要的曲面工具。

    rings: [(center, rx, ry, exponent, roll_deg), ...]，从一端排到另一端。
        center   截面中心 (x, y, z)。**给不同的 x/y 就能做出弯曲的壳体**
                 （比如顺着大腿弧度弯的护甲），这是拼接做不到的。
        rx, ry   截面半宽 / 半高
        exponent 超椭圆指数：2=椭圆, 3.5=圆角梯形, 6=近方
        roll_deg 截面绕自身轴旋转（做扭转的护甲片）

    典型用法（胸腔：腰方 → 收腰 → 胸圆）：
        loft("part_torso", [
            ((0, 0, -0.30), 0.26, 0.20, 5.0, 0),
            ((0, 0, -0.10), 0.23, 0.18, 4.0, 0),   # 收腰
            ((0, 0,  0.14), 0.32, 0.24, 3.0, 0),   # 外扩
            ((0, 0,  0.34), 0.30, 0.22, 2.4, 0),   # 肩部收口
        ], seg=32, mat=pal.steel)
    """
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    loops = []
    for item in rings:
        center, rx, ry, n = item[0], item[1], item[2], item[3]
        roll = item[4] if len(item) > 4 else 0.0
        c = Vector(center)
        rad = math.radians(roll)
        ca, sa = math.cos(rad), math.sin(rad)
        vs = []
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            x, y = _superellipse(a, rx, ry, n)
            if rad:
                x, y = x * ca - y * sa, x * sa + y * ca
            vs.append(bm.verts.new(c + Vector((x, y, 0.0))))
        loops.append(vs)

    for k in range(len(loops) - 1):
        A, B = loops[k], loops[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            try:
                bm.faces.new((A[i], A[j], B[j], B[i]))
            except ValueError:
                pass
    if close_start and len(loops[0]) >= 3:
        try:
            bm.faces.new(loops[0])
        except ValueError:
            pass
    if close_end and len(loops[-1]) >= 3:
        try:
            bm.faces.new(list(reversed(loops[-1])))
        except ValueError:
            pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    # ⚠️ loc 必须显式赋值 —— 早前漏了这一行，用 loc 的部件（脚）
    #    全部留在了世界原点，看起来像"脚从腿上掉下来了"。
    ob.location = loc
    ob.rotation_euler = rot
    activate(ob)
    if smooth:
        for poly in ob.data.polygons:
            poly.use_smooth = True
    return _finish(ob, mat, bev, segments)


def lathe(name, profile, seg=32, mat=None, loc=(0, 0, 0), rot=(0, 0, 0),
          smooth=True, bev=0.0, segments=2, flip=False):
    """旋转体：轮廓线 [(r, z), ...] 绕 Z 轴转一圈。

    r 给 0 的点会收成一个极点 —— 喷口内壁、球关节罩、轮毂、
    螺栓头的圆顶，这些"回转对称"的件用旋转体做是唯一正确的方式，
    拿圆柱 + 圆锥拼永远会看到接缝。

    profile 必须从一端排到另一端（z 单调），r >= 0。
    """
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    loops = []
    for (r, z) in profile:
        if r <= 1e-5:
            v = bm.verts.new(Vector((0.0, 0.0, z)))
            loops.append([v])
            continue
        vs = []
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            vs.append(bm.verts.new(
                Vector((r * math.cos(a), r * math.sin(a), z))))
        loops.append(vs)

    for k in range(len(loops) - 1):
        A, B = loops[k], loops[k + 1]
        if len(A) == 1 and len(B) > 1:          # 极点 → 环：扇形
            for i in range(len(B)):
                j = (i + 1) % len(B)
                try:
                    bm.faces.new((A[0], B[i], B[j]))
                except ValueError:
                    pass
        elif len(B) == 1 and len(A) > 1:
            for i in range(len(A)):
                j = (i + 1) % len(A)
                try:
                    bm.faces.new((A[i], A[j], B[0]))
                except ValueError:
                    pass
        elif len(A) == len(B):
            for i in range(len(A)):
                j = (i + 1) % len(A)
                try:
                    bm.faces.new((A[i], A[j], B[j], B[i]))
                except ValueError:
                    pass

    # 两端没到极点就封口
    for loop, rev in ((loops[0], True), (loops[-1], False)):
        if len(loop) >= 3:
            try:
                bm.faces.new(list(reversed(loop)) if rev else loop)
            except ValueError:
                pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if flip:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    activate(ob)
    if smooth:
        for poly in ob.data.polygons:
            poly.use_smooth = True
    return _finish(ob, mat, bev, segments)


def sweep(name, path, profile, mat=None, up=(0, 0, 1), smooth=True,
          close_start=True, close_end=True, bev=0.0, segments=2):
    """沿路径扫掠：截面 profile（归一化 [(x, y)]，范围约 ±1）沿 path 走。

    比 tube 强的地方：tube 只能给圆形截面，这里截面可以是任意形状
    （方形边条、扁椭圆护甲条、D 形管）。护甲边缘的"包边"、
    机体的线束、管廊，都该用扫掠而不是"两根圆柱对接"。

    用平行传输算坐标系，所以路径急转弯时截面不会突然翻面。
    """
    pts = [Vector(p) for p in path]
    if len(pts) < 2:
        return None

    # 切线
    tangents = []
    for i in range(len(pts)):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())

    # 平行传输参考向量
    ref = Vector(up)
    if abs(ref.dot(tangents[0])) > 0.95:
        ref = Vector((1, 0, 0))
    frames = []
    prev_ref = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    for i, t in enumerate(tangents):
        r = prev_ref - t * prev_ref.dot(t)
        if r.length < 1e-5:
            r = Vector((1, 0, 0)) - t * t.x
        r.normalize()
        s = t.cross(r).normalized()
        frames.append((r, s))
        prev_ref = r

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    loops = []
    for i, p in enumerate(pts):
        r, s = frames[i]
        vs = []
        for (px, py) in profile:
            vs.append(bm.verts.new(p + r * px + s * py))
        loops.append(vs)

    n = len(profile)
    for k in range(len(loops) - 1):
        A, B = loops[k], loops[k + 1]
        for i in range(n):
            j = (i + 1) % n
            try:
                bm.faces.new((A[i], A[j], B[j], B[i]))
            except ValueError:
                pass
    if close_start:
        try:
            bm.faces.new(loops[0])
        except ValueError:
            pass
    if close_end:
        try:
            bm.faces.new(list(reversed(loops[-1])))
        except ValueError:
            pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    activate(ob)
    if smooth:
        for poly in ob.data.polygons:
            poly.use_smooth = True
    return _finish(ob, mat, bev, segments)


def subdivide(ob, levels=1, apply=True):
    """Catmull-Clark 细分。低模放样 + 一级细分 = 连续曲面，面数还很省。"""
    if ob is None:
        return ob
    activate(ob)
    m = ob.modifiers.new("subd", 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    if apply:
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:
            pass
    return ob


def shell(ob, thickness, offset=-1.0, apply=True):
    """抽壳：把单面片变成有厚度的壳。

    护甲板本质是"曲面 + 厚度"，不是"实体块"。放样出一片曲面再抽壳，
    边缘会自然形成真实的板材厚度（还能在边缘看到内壁）。
    """
    if ob is None:
        return ob
    activate(ob)
    m = ob.modifiers.new("shell", 'SOLIDIFY')
    m.thickness = thickness
    m.offset = offset
    if apply:
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:
            pass
    return ob


def boolean_cut(target, cutters, keep_cutters=False):
    """布尔差集：在实体上挖孔 / 开槽。

    散热窗、检修口、观察缝这些"必须真的凹进去"的结构，
    靠贴几块薄片是做不出来的（近看就是贴纸）。
    """
    if target is None or not cutters:
        return target
    for c in cutters:
        if c is None:
            continue
        activate(target)
        m = target.modifiers.new("bool", 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.object = c
        try:
            m.solver = 'EXACT'
        except Exception:
            pass
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:
            pass
        if not keep_cutters:
            try:
                bpy.data.objects.remove(c, do_unlink=True)
            except Exception:
                pass
    return target


def bend(ob, angle_deg, axis='X', apply=True):
    """弯曲变形（Simple Deform）。给平直件加弧度，比如护甲板的包角。"""
    if ob is None or abs(angle_deg) < 1e-3:
        return ob
    activate(ob)
    m = ob.modifiers.new("bend", 'SIMPLE_DEFORM')
    m.deform_method = 'BEND'
    m.deform_axis = axis
    m.angle = math.radians(angle_deg)
    if apply:
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:
            pass
    return ob


def greeble(prefix, center, size, count, seed, mats,
            scale=(0.025, 0.075), depth=(0.003, 0.012),
            faces=('+Y', '-Y', '+X', '-X', '+Z'), inset=0.28,
            thin_chance=0.05, shrink=0.92):
    """在包围盒表面散布小机械块。

    这是让模型"看起来有东西"最有效的手段。纯粹的方块 + 倒角会显得像占位符，
    但表面散布上百个 2—8 cm 的小块之后，视觉密度会立刻接近成品。

    ⚠️ 悬空修复：身体是椭球/圆柱，比包围盒窄。块贴在盒面、又落在盒角时
       会掉进空气里（侧面看就是一根戳出来的尖刺 / 脚下一块脱离的平板）。
       收紧四处：
       - shrink 0.92：盒子整体往内收，块更贴近真实曲面；
       - inset 0.12→0.28：块更靠近每面中心，那里盒面才贴近曲面；
       - thin_chance 0.30→0.05、长条倍率降到 1.5~2.2：几乎不再生成长条尖刺；
       - depth 上限 0.026→0.012：凸出更浅，不扎出来。
    """
    rng = random.Random(seed)
    out = []
    if os.environ.get("NO_GREEBLE"):
        return out
    cx, cy, cz = center
    sx, sy, sz = size[0] * shrink, size[1] * shrink, size[2] * shrink
    for i in range(count):
        f = rng.choice(faces)
        a = rng.uniform(-0.5 + inset, 0.5 - inset)
        b = rng.uniform(-0.5 + inset, 0.5 - inset)
        d = rng.uniform(depth[0], depth[1])
        w = rng.uniform(scale[0], scale[1])
        h = rng.uniform(scale[0], scale[1])
        if rng.random() < thin_chance:
            w *= rng.uniform(1.5, 2.2)
            h *= rng.uniform(0.40, 0.60)

        if f == '+Y':
            loc = (cx + a * sx, cy + sy * 0.5 + d * 0.5, cz + b * sz)
            sz3 = (w, d, h)
        elif f == '-Y':
            loc = (cx + a * sx, cy - sy * 0.5 - d * 0.5, cz + b * sz)
            sz3 = (w, d, h)
        elif f == '+X':
            loc = (cx + sx * 0.5 + d * 0.5, cy + a * sy, cz + b * sz)
            sz3 = (d, w, h)
        elif f == '-X':
            loc = (cx - sx * 0.5 - d * 0.5, cy + a * sy, cz + b * sz)
            sz3 = (d, w, h)
        else:  # '+Z'
            loc = (cx + a * sx, cy + b * sy, cz + sz * 0.5 + d * 0.5)
            sz3 = (w, h, d)

        m = rng.choice(mats)
        # 小块不加倒角：2—8 cm 尺度下 3 mm 的倒角看不见，但每个都执行一次
        # modifier apply，上百个累积起来会明显拖慢生成速度。
        out.append(box("%s_%03d" % (prefix, i + 1), sz3, loc, mat=m, bev=0))
    return out


def grille(name, size, loc, rot=(0, 0, 0), slats=5, mat=None, axis='Z'):
    """散热格栅：一组平行薄片。机械感最强的单一细节。"""
    out = []
    sx, sy, sz = size
    span = sz if axis == 'Z' else sy
    step = span / (slats * 2.0)
    for i in range(slats):
        off = -span * 0.5 + step * (i * 2 + 1)
        if axis == 'Z':
            p = (loc[0], loc[1], loc[2] + off)
            s = (sx, sy, step * 0.85)
        else:
            p = (loc[0], loc[1] + off, loc[2])
            s = (sx, step * 0.85, sz)
        out.append(box("%s_%02d" % (name, i + 1), s, p, rot=rot, mat=mat,
                       bev=step * 0.10, segments=1))
    return out


def panel_lines(prefix, center, size, count, seed, mat, thickness=0.012):
    """面板接缝：略微凸出的细条，模拟装甲分块。"""
    rng = random.Random(seed)
    out = []
    cx, cy, cz = center
    sx, sy, sz = size
    for i in range(count):
        vertical = rng.random() < 0.5
        if vertical:
            loc = (cx + rng.uniform(-0.42, 0.42) * sx,
                   cy - sy * 0.5 - thickness * 0.4,
                   cz + rng.uniform(-0.35, 0.35) * sz)
            s = (thickness, thickness * 1.6, sz * rng.uniform(0.35, 0.85))
        else:
            loc = (cx + rng.uniform(-0.35, 0.35) * sx,
                   cy - sy * 0.5 - thickness * 0.4,
                   cz + rng.uniform(-0.42, 0.42) * sz)
            s = (sx * rng.uniform(0.35, 0.85), thickness * 1.6, thickness)
        out.append(box("%s_%02d" % (prefix, i + 1), s, loc, mat=mat,
                       bev=thickness * 0.2, segments=1))
    return out


def piston(prefix, p1, p2, radius, mat_body, mat_rod, taper=0.62):
    """液压活塞：套筒 + 活塞杆。放在关节处能立刻读出"这是能动的"。"""
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    length = d.length
    if length < 1e-5:
        return []
    mid = (p1 + p2) * 0.5
    direction = d.normalized()
    up = Vector((0, 0, 1))
    if abs(direction.dot(up)) > 0.999:
        up = Vector((0, 1, 0))
    x_ax = direction.cross(up).normalized()
    y_ax = direction.cross(x_ax).normalized()
    rot = mathutils.Matrix((x_ax, y_ax, direction)).transposed().to_euler()

    sleeve_len = length * 0.58
    sleeve_c = p1 + direction * (sleeve_len * 0.5)
    body = cyl("%s_sleeve" % prefix, radius, sleeve_len, tuple(sleeve_c),
               rot=tuple(rot), mat=mat_body, verts=14, bev=radius * 0.12)

    rod_c = p1 + direction * (length - length * (1 - taper) * 0.5)
    rod = cyl("%s_rod" % prefix, radius * 0.44, length * (1 - taper),
              tuple(rod_c), rot=tuple(rot), mat=mat_rod, verts=10,
              bev=radius * 0.08)
    return [body, rod]


def cable(prefix, points, radius, mat, segments=12):
    """线缆：贝塞尔曲线转网格。给机械体加上"有生命"的杂乱感。"""
    curve_data = bpy.data.curves.new("%s_curve" % prefix, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 3
    curve_data.resolution_u = segments
    sp = curve_data.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for i, p in enumerate(points):
        bp = sp.bezier_points[i]
        bp.co = p
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    ob = bpy.data.objects.new("%s_mesh" % prefix, curve_data)
    bpy.context.collection.objects.link(ob)
    activate(ob)
    try:
        bpy.ops.object.convert(target='MESH')
        ob = bpy.context.active_object
    except Exception:
        pass
    if mat:
        assign_mat(ob, mat)
    return ob


def armor_plate(name, size, loc, rot, mat, offset=0.03, scale=1.12, bev=0.012):
    """叠层装甲：在主装甲外再叠一层略大的板，产生层次。"""
    return box(name, (size[0] * scale, size[1] * 0.55, size[2] * scale),
               (loc[0], loc[1] - offset, loc[2]), rot=rot, mat=mat, bev=bev)


def bolt(name, loc, radius, mat, depth=0.012):
    return cyl(name, radius, depth, loc, rot=(math.radians(90), 0, 0),
               mat=mat, verts=8, bev=radius * 0.2)


# ═══════════════════════════════════════════════════════════
# 材质
# ═══════════════════════════════════════════════════════════

def _mat(name, color, metallic, roughness, emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = None
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if bsdf is None:
        return m

    def setv(names, val):
        for sn in names:
            if sn in bsdf.inputs:
                bsdf.inputs[sn].default_value = val
                return True
        return False

    setv(["Base Color"], (color[0], color[1], color[2], 1.0))
    setv(["Metallic"], metallic)
    setv(["Roughness"], roughness)
    if emission is not None:
        setv(["Emission Color", "Emission"],
             (emission[0], emission[1], emission[2], 1.0))
        setv(["Emission Strength"], strength)
    return m


class Palette(object):
    """一套材质。每个机型/敌人可以有自己的 accent 配色。"""

    def __init__(self, accent, glow, tag="std"):
        # ⚠️ 2026-10-19 配色重做：原来的装甲基色是 (0.082,0.092,0.108) + metallic 0.88，
        #    在夜景里等于"纯黑剪影"——金属度高的表面几乎不漫反射，颜色全靠环境反射，
        #    而竞技场的天空/地面都很暗 → 机体只剩轮廓。涂装装甲应该：
        #      · 金属度 0.25~0.35（保留一点高光，但主要靠漫反射出颜色）
        #      · 基色 0.16~0.25（sRGB 约 0.45~0.53，夜景里才读得出"浅灰蓝装甲"）
        #    真正该高金属度的是裸露的骨架 / 关节 / 铜件。
        self.accent = _mat("M_Accent_%s" % tag, accent, 0.22, 0.44)
        self.accent_dark = _mat("M_AccentDark_%s" % tag,
                                tuple(c * 0.42 for c in accent), 0.24, 0.55)
        self.steel = _mat("M_Steel", (0.165, 0.175, 0.195), 0.30, 0.52)
        self.steel_light = _mat("M_SteelLight", (0.245, 0.250, 0.260), 0.28, 0.44)
        self.frame = _mat("M_Frame", (0.038, 0.040, 0.046), 0.62, 0.62)
        self.joint = _mat("M_Joint", (0.022, 0.024, 0.028), 0.45, 0.78)
        self.rubber = _mat("M_Rubber", (0.020, 0.021, 0.024), 0.08, 0.90)
        self.copper = _mat("M_Copper", (0.33, 0.19, 0.09), 0.92, 0.32)
        self.core = _mat("M_Core_%s" % tag, (0.05, 0.05, 0.08),
                         0.25, 0.20, emission=glow, strength=1.7)
        self.visor = _mat("M_Visor_%s" % tag, (0.04, 0.05, 0.07),
                          0.30, 0.16, emission=glow, strength=1.3)
        self.rust = _mat("M_Rust", (0.115, 0.062, 0.038), 0.55, 0.82)

    def greeble_mats(self):
        return [self.steel, self.steel_light, self.frame, self.copper]


# ═══════════════════════════════════════════════════════════
# 顶点组 / 合并 / 绑定
# ═══════════════════════════════════════════════════════════

def assign_group(ob, group_name):
    """把物体的全部顶点分配给一个顶点组。"""
    vg = ob.vertex_groups.get(group_name)
    if vg is None:
        vg = ob.vertex_groups.new(name=group_name)
    vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')


def assign_vcol(ob, rgb):
    """给一个部件刷上统一的顶点色。

    顶点色在这里当"表面细节层"用，不是用来上色的：
    每个部件给一个接近 1.0 但略有差异的灰度（见 build_chassis 的 tone_for），
    叠加一个"越靠下越暗"的积灰渐变。UE 侧材质把 BaseColor 乘以顶点色，
    于是相邻装甲板之间出现细微的明暗差 —— 这正是"看起来是一台真机器、
    而不是一块均色的灰盒子"的关键。

    用顶点色而不是贴图：贴图要 UV 展开方向一致才有意义，而这批资产是
    Smart UV 自动展开的，方向随机；顶点色只依赖几何，不受 UV 影响。
    FBX 会把顶点色层一起导出，UE 导入后即为 VertexColor 节点。
    """
    me = ob.data
    attr = me.color_attributes.get("Col")
    if attr is None:
        try:
            attr = me.color_attributes.new(name="Col", type='BYTE_COLOR',
                                           domain='CORNER')
        except Exception:
            return
    n = len(me.loops)
    if n == 0:
        return
    flat = [rgb[0], rgb[1], rgb[2], 1.0] * n
    try:
        attr.data.foreach_set("color", flat)
    except Exception:
        for i in range(n):
            attr.data[i].color = (rgb[0], rgb[1], rgb[2], 1.0)


def join_objects(objs, name):
    """合并为一网格。合并前必须已经建好顶点组，否则权重会丢。"""
    objs = flatten(objs)
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    ob.data.name = name + "_mesh"
    return ob


def make_armature(name, bone_defs, loc=(0, 0, 0)):
    """按定义创建骨架。bone_defs: [{name, head, tail, parent}]"""
    arm_data = bpy.data.armatures.new(name)
    arm_ob = bpy.data.objects.new(name, arm_data)
    bpy.context.collection.objects.link(arm_ob)
    arm_ob.location = loc
    activate(arm_ob)
    bpy.ops.object.mode_set(mode='EDIT')
    created = {}
    for bd in bone_defs:
        eb = arm_data.edit_bones.new(bd["name"])
        eb.head = Vector(bd["head"])
        eb.tail = Vector(bd["tail"])
        eb.roll = 0.0
        created[bd["name"]] = eb
    for bd in bone_defs:
        p = bd.get("parent")
        if p and p in created:
            created[bd["name"]].parent = created[p]
            created[bd["name"]].use_connect = bool(bd.get("connect", False))
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_ob


def bind(mesh_ob, arm_ob):
    """把网格绑定到骨架。"""
    mesh_ob.parent = arm_ob
    mesh_ob.matrix_parent_inverse = arm_ob.matrix_world.inverted()
    m = mesh_ob.modifiers.new("Armature", 'ARMATURE')
    m.object = arm_ob
    return m


# ── 按部件名自动绑定 ─────────────────────────────────────

def side_of(name):
    """从部件名里提取左右侧标记。"""
    if "_L" in name:
        return "L"
    if "_R" in name:
        return "R"
    return None


SPLIT_LEGS = False   # 双足：thigh/shin/foot
SPLIT_QUAD = False   # 四足：前后两对，后腿名字以 B（hauler）或 2（colossus）结尾


def _is_back_leg(n):
    return n.endswith("B") or n.endswith("2")


def infer_bone_name(name):
    """从部件对象名推断它该归到哪根骨骼。

    判定顺序很关键：先头、再躯干、再四肢。否则 chassis_head 会被
    chassis_ 前缀规则吃掉，head_cheek_L 会被 _L 规则误判成手臂。

    foot 必须在 leg 关键词之前判定 —— 否则 part_foot_L 会被
    "leg/thruster/foot/knee..." 这条腿骨规则吃进去，脚永远无法独立成骨。
    独立脚骨的意义：UE 侧程序化动画按"髋→踝"量腿长（没有脚骨会退回
    90cm 的估计值），且脚踝可以反向旋转、摆动时脚掌不随小腿甩。
    """
    n = name
    if "core" in n:
        return "core"
    if n.startswith("chassis_head") or n.startswith("head_") or n == "head":
        return "head"
    if n.startswith("chassis_") or n.startswith("torso") or n == "part_torso":
        return "torso"
    if "shoulder" in n or "arm" in n:
        s = side_of(n)
        return "arm_%s" % s if s else "arm_L"
    if "foot" in n:
        s = side_of(n)
        if s and SPLIT_QUAD and _is_back_leg(n):
            return "foot_B%s" % s
        return "foot_%s" % s if s else "foot_L"
    if any(k in n for k in ("leg", "thruster", "foot", "knee", "ankle", "hip")):
        s = side_of(n)
        if s and (SPLIT_LEGS or SPLIT_QUAD):
            # 双足 / 四足：大腿、小腿分骨，UE 步态两骨 IK 才有关节可解。
            # 四足的后腿加 B 前缀（thigh_BL），前腿沿用 thigh_L。
            tag = "B" if (SPLIT_QUAD and _is_back_leg(n)) else ""
            if "knee" in n or "shin" in n:
                return "shin_%s%s" % (tag, s)
            return "thigh_%s%s" % (tag, s)
        return "leg_%s" % s if s else "leg_L"
    return "torso"


def auto_rig(objs, rig_name, limb_parent="torso",
             lods=((0.45, "_LOD1"), (0.18, "_LOD2")), do_uv=True):
    """按部件名自动生成骨架并绑定，一步完成 UV 与 LOD。

    刚性机械体的骨骼不需要解剖学正确 —— 每根骨骼锚在对应部件组的质心上，
    部件是刚体不会形变，所以「一组部件一根骨骼」就够了。

    执行顺序不可调换：合并 → UV → LOD → 绑定。
    LOD 必须在绑定之前生成，否则减面会把骨架修改器一起吃进去。

    返回 (mesh, armature, [(lod_name, tris), ...])
    """
    objs = flatten(objs)
    groups = {}
    for ob in objs:
        groups.setdefault(infer_bone_name(ob.name), []).append(ob)

    # 骨骼位置必须在合并之前算好 —— 合并会销毁原始部件对象
    centers = {}
    bounds = {}
    seg_len = {}      # 大腿/小腿真实段长（取主圆柱部件，而非整组包围盒）
    joint_head = {}   # 关节根位置（髋球 / 膝球中心）
    joint_tail = {}   # 关节末端（小腿圆柱下端点 = 踝关节）
    for bone, g in groups.items():
        mn, mx = world_bounds(g)
        bounds[bone] = (mn, mx)
        centers[bone] = ((mn[0] + mx[0]) * 0.5,
                         (mn[1] + mx[1]) * 0.5,
                         (mn[2] + mx[2]) * 0.5)
        # 大腿 / 小腿：真实段长取对应主圆柱（part_leg_* / leg_shin_*），
        # 关节根取髋球 / 膝球（leg_hip_* / leg_knee_*）中心。
        # 不能用整组包围盒：髋球、膝球、液压缸会把包围盒拉长，
        # 让骨长虚高（运输机大腿骨被拉到 1.15m，实际圆柱仅 0.55m），
        # 进而导致 UE 侧 IK 认为腿"更长"、与真实几何错位 → 四足超伸。
        if bone.startswith("thigh"):
            for ob in g:
                if "part_leg" in ob.name:
                    bmn, bmx = world_bounds([ob])
                    seg_len[bone] = math.sqrt(
                        (bmx[0] - bmn[0]) ** 2 + (bmx[1] - bmn[1]) ** 2
                        + (bmx[2] - bmn[2]) ** 2)
                    break
            for ob in g:
                if "leg_hip" in ob.name or ob.name.endswith("_hip"):
                    hmn, hmx = world_bounds([ob])
                    joint_head[bone] = ((hmn[0] + hmx[0]) * 0.5,
                                        (hmn[1] + hmx[1]) * 0.5,
                                        (hmn[2] + hmx[2]) * 0.5)
                    break
        elif bone.startswith("shin"):
            for ob in g:
                if "leg_shin" in ob.name:
                    bmn, bmx = world_bounds([ob])
                    # ⚠️ 第七十六轮：圆柱改成斜置后，只取 Z 高度会算短骨长
                    #    （斜段在 Z 上的投影小于真实长度）→ IK 以为腿更短。
                    seg_len[bone] = math.sqrt(
                        (bmx[0] - bmn[0]) ** 2 + (bmx[1] - bmn[1]) ** 2
                        + (bmx[2] - bmn[2]) ** 2)
                    # 小腿圆柱的**下端点**就是踝关节位置（脚骨挂在它下面）。
                    # 用它当"下一关节"，小腿骨才能真正斜向踝，
                    # 而不会歪向脚掌包围盒中心（那里比踝低且前偏）。
                    #
                    # ⚠️ 第七十六轮：这段原来写在 break **之后**，是死代码 ——
                    #    joint_tail 从未被赋值，小腿骨尾端就退回到包围盒中心，
                    #    骨骼朝向与几何倾角不符。后果是 UE 侧 IK 目标点（按参考姿势
                    #    累积）和脚骨的真实静止位置差了 13~19cm，而 IK 报 clamp==d
                    #    （"以为到了"），于是脚整体偏到目标下方 20cm，四条腿永不抬脚。
                    #    实测：hipRef==hipRun 完全一致，只有 ankleRef≠ankleRun。
                    joint_tail[bone] = ((bmn[0] + bmx[0]) * 0.5,
                                        (bmn[1] + bmx[1]) * 0.5,
                                        bmn[2])
                    break
            for ob in g:
                if "leg_knee" in ob.name:
                    hmn, hmx = world_bounds([ob])
                    joint_head[bone] = ((hmn[0] + hmx[0]) * 0.5,
                                        (hmn[1] + hmx[1]) * 0.5,
                                        (hmn[2] + hmx[2]) * 0.5)
                    break

    for bone, g in groups.items():
        for ob in g:
            assign_group(ob, bone)

    mesh = join_objects(objs, "SK_%s" % rig_name)
    if do_uv:
        # 和玩家机体一致：世界对齐立方投影（1 UV 单位 = 1.2m）。
        # 敌人也要吃同一套程序化面板缝贴图，UV 不连续的话接缝会撕裂。
        cube_uv(mesh, size_m=3.2)
    lod_info = add_lods(mesh, lods) if lods else []

    defs = [dict(name="root", head=(0, 0, 0), tail=(0, 0, 0.25))]
    has_torso = "torso" in centers
    for bone in sorted(centers):
        c = centers[bone]
        mn, mx = bounds[bone]
        if bone == "torso" or not has_torso:
            parent = "root"
        else:
            parent = limb_parent if limb_parent in centers else "root"

        # 脚骨挂在**同侧**的腿骨下面（拿不到腿骨就退到默认父级）。
        # 挂在腿骨下 = 腿摆动时脚随动、脚踝再做反向旋转补偿 ——
        # 与玩家骨架（thigh→shin→foot）的层级语义一致，
        # UE 侧的程序化动画不需要任何改动就能识别。
        if bone.startswith("foot"):
            side = bone.rsplit("_", 1)[-1]
            for cand in ("shin_%s" % side, "thigh_%s" % side, "leg_%s" % side):
                if cand in centers:
                    parent = cand
                    break
        elif bone.startswith("shin"):
            side = bone.rsplit("_", 1)[-1]
            for cand in ("thigh_%s" % side, "leg_%s" % side):
                if cand in centers:
                    parent = cand
                    break

        # ⚠️ 四肢骨骼的原点必须在**根部关节**，不能在部件质心。
        # 程序化摆骨骼永远绕骨骼原点旋转：原点在质心 → 整条腿像跷跷板
        # 绕着中段甩（玩家机体就踩过这个坑，见 build_chassis.build_rig）。
        # 这里的部件是整段四肢，所以"根部"= 包围盒顶端。
        if bone.startswith(("arm", "foot")):
            # 手臂 / 脚：保持原逻辑（整段部件，根部=包围盒顶端）
            head = ((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, mx[2] - 0.01)
            tail = ((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5, mn[2])
        elif bone.startswith(("thigh", "shin")):
            # 大腿 / 小腿：根取关节球（髋 / 膝）中心，尾指向**下一个关节**。
            #
            # ⚠️ 不能把尾巴直接放在正下方（旧实现 tail = (jh.x, jh.y, jh.z - seg)）。
            #    四足腿的膝盖是前/后偏的（hauler 偏 0.36·D、colossus 偏 0.55m），
            #    视觉圆柱因此是斜的，但旧骨架仍竖直 → 骨架与几何错位：
            #      · UE 侧读到 Rest.Theta1Deg≈0（以为腿竖直）；
            #      · 实际膝/踝在 Y 方向偏了半米；
            #      · IK 按"竖直腿 + 三维骨长"反解 → 落脚点系统性偏离目标 → 四足滑步。
            #    改为尾指向真实关节位置后，骨架与几何一致，IK 才有正确解。
            jh = joint_head.get(bone, c)
            # 段长取主圆柱的**三维**对角线（圆柱是斜的，只取 Z 会算短）
            seg = seg_len.get(bone, mx[2] - mn[2])
            head = jh
            nxt = None
            side = bone.rsplit("_", 1)[-1]
            if bone.startswith("thigh"):
                # 大腿：尾指向真实膝球中心
                nxt = joint_head.get("shin_%s" % side)
            elif bone.startswith("shin"):
                # ⚠️ 第七十六轮：小腿尾端必须指向**真实踝关节**（圆柱下端点），
                #    与大腿同样"尾指向下一关节"。
                #    原来这里什么都不做、尾端竖直向下，理由是"倾斜会让 IK 裁剪上万次"——
                #    那是因为当时腿的几何还是竖直的。现在几何已斜置（cyl_between），
                #    骨架若仍竖直就与几何错位：UE 侧按参考姿势累积出的踝位置
                #    和脚骨真实静止位置差 13~19cm，而 IK 报 clamp==d（"以为到了"），
                #    脚整体偏到目标下方、四条腿永不抬脚（C_9 实测偏差 20~25cm）。
                nxt = joint_tail.get(bone)
            if nxt is not None:
                dv = (nxt[0] - jh[0], nxt[1] - jh[1], nxt[2] - jh[2])
                dl = math.sqrt(dv[0] ** 2 + dv[1] ** 2 + dv[2] ** 2)
                if dl > 1e-4:
                    s = seg / dl
                    tail = (jh[0] + dv[0] * s, jh[1] + dv[1] * s, jh[2] + dv[2] * s)
                else:
                    tail = (jh[0], jh[1], jh[2] - seg)
            else:
                tail = (jh[0], jh[1], jh[2] - seg)
        else:
            head = c
            tail = (c[0], c[1], c[2] + 0.22)
        defs.append(dict(name=bone, head=head, tail=tail, parent=parent))

    arm = make_armature(rig_name, defs)
    bind(mesh, arm)
    return mesh, arm, lod_info


def add_lods(mesh, ratios=((0.45, "_LOD1"), (0.18, "_LOD2"))):
    """批量生成 LOD 并移入独立集合，避免污染主资产。

    必须在绑定之前调用 —— 绑定之后网格会带上骨架修改器，
    减面会把骨架一起吃掉。
    """
    out = []
    col = bpy.data.collections.new("LODs")
    bpy.context.scene.collection.children.link(col)
    for ratio, sfx in ratios:
        lod = make_lod(mesh, ratio, sfx)
        out.append((lod.name, tri_count(lod)))
        for c in list(lod.users_collection):
            c.objects.unlink(lod)
        col.objects.link(lod)
    return out


# ═══════════════════════════════════════════════════════════
# UV / LOD
# ═══════════════════════════════════════════════════════════

def cube_uv(ob, size_m=1.2, margin=0.0):
    """世界对齐的立方体投影 UV（1 个 UV 单位 = size_m 米）。

    为什么不用 Smart UV：
      Smart UV 是**按面片自动分岛**的，相邻两个面的 UV 方向随机、不连续。
      程序化细节贴图（面板缝 / 铆钉）一旦按这种 UV 采样，每条接缝都会错位，
      看起来像贴图"撕裂"。
      立方体投影按世界坐标投影，同一个朝向的所有面共享一套连续 UV，
      面板缝在整块装甲上是**连贯**的 —— 这才是工业表面该有的样子。
    材质侧直接用 UV0 采样，也不再依赖三平面函数（那条链路很难验证）。
    """
    # ⚠️ 不能用 bpy.ops.uv.cube_project：它会把结果**归一化到 0~1**，
    #    不管 cube_size 给多少。2.7m 高的机体最终 UV 也只有 0~1，
    #    等于一张 4K 贴图铺满整台机体 —— 板缝被拉到 90cm 宽，
    #    近看就是一片纯色，这就是"机体表面没有纹理"的真正原因。
    #
    # 这里手写投影：按每个面的主轴（法线最大的那个轴）选投影平面，
    # UV = 世界坐标 / size_m。机体 2.7m → UV 0~2.25，贴图重复 2 次多，
    # 板缝和铆钉才会以 1.2m 的真实尺度出现。
    me = ob.data
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers[0]
    mw = ob.matrix_world

    for poly in me.polygons:
        n = poly.normal
        ax = 0 if abs(n.x) >= abs(n.y) and abs(n.x) >= abs(n.z) else (
            1 if abs(n.y) >= abs(n.z) else 2)
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            if ax == 0:          # 法线朝 X → 投影到 YZ
                u, w = v.y, v.z
            elif ax == 1:        # 朝 Y → 投影到 XZ
                u, w = v.x, v.z
            else:                # 朝 Z → 投影到 XY
                u, w = v.x, v.y
            uvl.data[li].uv = (u / size_m, w / size_m)
    return True


def smart_uv(ob, angle_deg=66.0, margin=0.02):
    activate(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    ok = False
    for kwargs in (
        {"angle_limit": math.radians(angle_deg), "island_margin": margin},
        {"angle_limit": math.radians(angle_deg)},
        {},
    ):
        try:
            bpy.ops.uv.smart_project(**kwargs)
            ok = True
            break
        except Exception:
            continue
    bpy.ops.object.mode_set(mode='OBJECT')
    return ok


def make_lod(ob, ratio, suffix):
    """生成减面 LOD。在绑定之前生成，否则会带上骨架修改器。"""
    dup = ob.copy()
    dup.data = ob.data.copy()
    dup.name = ob.name + suffix
    dup.data.name = ob.data.name + suffix
    bpy.context.collection.objects.link(dup)
    activate(dup)
    m = dup.modifiers.new("dec", 'DECIMATE')
    m.ratio = ratio
    try:
        bpy.ops.object.modifier_apply(modifier=m.name)
    except Exception:
        pass
    return dup


def tri_count(ob):
    me = ob.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


# ═══════════════════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════════════════

def _rotate_scene_z(angle_deg):
    """绕世界 Z 轴旋转整个场景（含骨架，网格跟随父级）。

    只改根对象的 matrix_world，不逐个旋转 mesh 数据 —— 后者会破坏网格与骨架的绑定。
    """
    R = mathutils.Matrix.Rotation(math.radians(angle_deg), 4, 'Z')
    for ob in bpy.data.objects:
        if ob.parent is None:
            ob.matrix_world = R @ ob.matrix_world
    bpy.context.view_layer.update()


def export_fbx(path):
    """导出 FBX。

    ⚠️ 关于单位与朝向 —— 这是踩过坑的地方，改动前务必先读：

    【单位】实测结论（Blender 5.2，往返导入验证，见 verify_fbx.py）：
        global_scale=1.0（默认）        → 往返高度 2.590 m  ✅ 正确
        global_scale=100.0              → 往返高度 259.0 m  ❌ 大 100 倍
        先烘焙 100 再 global_scale=1.0  → 往返高度 259.0 m  ❌ 同样错
      Blender 默认导出本身就会正确处理米 → 厘米换算，手动设 global_scale 只会双重缩放。

    【朝向】实测结论（UE 5.8 内读取包围盒 origin 对照 Blender，见 ue/Scripts/verify_import.py）：
        Blender (x, y, z) → UE (x, -y, z)   —— X/Z 不变，Y 轴翻转。
        机体正面在 Blender 是 -Y，翻转后落在 UE +Y；而 UE 的约定是 +X 朝前。
        所以导出前绕 Z 轴 +90° 旋转：-Y → +X，正面落到 UE +X。
        旋转只作用于导出过程，导出后立即还原，不影响 .blend 文件本身。
    """
    _rotate_scene_z(90.0)
    try:
        kw = dict(
            filepath=path, use_selection=False,
            apply_unit_scale=True, global_scale=1.0,
            apply_scale_options='FBX_SCALE_NONE',
            object_types={'MESH', 'ARMATURE', 'EMPTY'},
            use_mesh_modifiers=False, mesh_smooth_type='EDGE',
            bake_space_transform=False, path_mode='AUTO',
            embed_textures=False, add_leaf_bones=False,
            # 顶点色层必须导出 —— UE 侧材质用 VertexColor 做表面明暗差异
            # （见 build_chassis.Assembler.tone_for）。'NONE' 会把它整个丢掉。
            colors_type='SRGB',
            primary_bone_axis='Y', secondary_bone_axis='X')
        valid = set(bpy.ops.export_scene.fbx.get_rna_type().properties.keys())
        bpy.ops.export_scene.fbx(**{k: v for k, v in kw.items() if k in valid})
    finally:
        _rotate_scene_z(-90.0)


def export_glb(path):
    kw = dict(filepath=path, export_format='GLB', use_selection=False,
              export_apply=False, export_skins=True)
    try:
        valid = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
        bpy.ops.export_scene.gltf(**{k: v for k, v in kw.items() if k in valid})
    except Exception as e:
        print("    [warn] GLB 跳过: %s" % e)


def save_blend(path):
    # 关掉 .blend1 自动备份 —— 否则每次重建都会多出一倍文件，
    # 54 个资产会变成 108 个，白白占空间。
    try:
        bpy.context.preferences.filepaths.save_version = 0
    except Exception:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=path)


# ═══════════════════════════════════════════════════════════
# 布局与渲染
# ═══════════════════════════════════════════════════════════

def flatten(objs):
    """把可能嵌套的物体列表压平。

    细节生成器（greeble / grille / piston / mount）都返回列表，很容易在调用处
    误用 append 而塞进一个嵌套列表。这里统一兜底，避免下游到处报
    'list object has no attribute select_set' 这类难查的错误。
    """
    out = []
    for o in objs:
        if isinstance(o, (list, tuple, set)):
            out.extend(flatten(o))
        elif o is not None:
            out.append(o)
    return out


def world_bounds(objs):
    mn = [1e9] * 3
    mx = [-1e9] * 3
    for ob in flatten(objs):
        if ob.type != 'MESH':
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    if mn[0] > mx[0]:
        return [0, 0, 0], [0, 0, 0]
    return mn, mx


def layout_grid(groups, cols, gap=0.55, normalize=True, target_h=1.6):
    """把多组物体摆成网格，用于出目录图。

    groups: [[obj, ...], ...]  每组是一个独立模型
    normalize: 把每个模型统一缩放到同一高度，便于横向对比

    关键：缩放必须以「整组的包围盒中心」为支点，同时缩放各零件的位置。
    如果只改 ob.scale，每个零件会绕自身中心缩放而位置不动 —— 模型会炸开。
    """
    groups = [flatten(g) for g in groups]
    infos = []
    cell_w = cell_h = 0.0
    for g in groups:
        mn, mx = world_bounds(g)
        h = max(mx[2] - mn[2], 1e-4)
        s = (target_h / h) if normalize else 1.0
        w = (mx[0] - mn[0]) * s
        h2 = h * s
        infos.append((mn, mx, s, w, h2))
        cell_w = max(cell_w, w)
        cell_h = max(cell_h, h2)
    cell_w += gap
    # 纵向间距必须用「高度」而不是 Y 方向深度 —— 网格铺在 XZ 平面上，
    # 用深度会导致高模型的行距不够而被裁出画面。
    cell_h += gap

    rows = int(math.ceil(len(groups) / float(cols)))
    for idx, g in enumerate(groups):
        mn, mx, s, w, h2 = infos[idx]
        r, c = idx // cols, idx % cols
        bcx = (mn[0] + mx[0]) * 0.5
        bcy = (mn[1] + mx[1]) * 0.5
        bcz = (mn[2] + mx[2]) * 0.5
        tx = (c - (cols - 1) * 0.5) * cell_w
        tz = -(r - (rows - 1) * 0.5) * cell_h
        for ob in g:
            # 以组包围盒中心为支点缩放，然后把缩放后的中心移到格子中心。
            # 注意末尾不能再加回 bcx/bcz —— 否则高的模型会浮在画面上方被裁掉。
            ob.location = ((ob.location[0] - bcx) * s + tx,
                           (ob.location[1] - bcy) * s,
                           (ob.location[2] - bcz) * s + tz)
            ob.scale = (ob.scale[0] * s, ob.scale[1] * s, ob.scale[2] * s)
    return rows, cell_w, cell_h


def fit_distance(span_w, span_h, lens, res_x, res_y, margin=1.16, sensor=36.0):
    """算出能把 span_w x span_h 完整框进画面的相机距离。

    不这么算的话，72mm 镜头在 12 米宽的目录图前只能拍到中间一小块。
    """
    fov_h = 2.0 * math.atan(sensor / (2.0 * lens))
    sensor_v = sensor * (float(res_y) / float(res_x))
    fov_v = 2.0 * math.atan(sensor_v / (2.0 * lens))
    d_h = (span_w * 0.5 * margin) / max(math.tan(fov_h * 0.5), 1e-6)
    d_v = (span_h * 0.5 * margin) / max(math.tan(fov_v * 0.5), 1e-6)
    return max(d_h, d_v)


def setup_render(out_png, target, distance=None, res=1280, wide=False,
                 span=None, lens=72.0, flat=False):
    """相机 + 三点布光 + AgX 色彩管理。灯光能量经过校准，避免洗白配色。

    span=(宽, 高) 时自动计算相机距离，用于目录图这类大跨度构图；
    flat=True 用更正面的机位，适合看排列整齐的网格。
    """
    scene = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        try:
            scene.render.engine = eng
            break
        except Exception:
            continue
    if scene.render.engine == 'CYCLES':
        scene.cycles.samples = 64
        scene.cycles.use_denoising = True
    elif hasattr(scene, "eevee"):
        for attr, val in (("taa_render_samples", 64), ("use_raytracing", True)):
            if hasattr(scene.eevee, attr):
                try:
                    setattr(scene.eevee, attr, val)
                except Exception:
                    pass

    res_x = int(res * 1.5) if wide else res
    res_y = res
    if span is not None:
        distance = fit_distance(span[0], span[1], lens, res_x, res_y)
    if distance is None:
        distance = 5.4

    tgt = bpy.data.objects.new("cam_target", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = Vector(target)

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    bpy.context.collection.objects.link(cam)
    if flat:
        cam.location = (distance * 0.14, -distance * 0.98, target[2] + distance * 0.12)
    else:
        cam.location = (distance * 0.52, -distance * 0.86, target[2] + distance * 0.22)
    con = cam.constraints.new('TRACK_TO')
    con.target = tgt
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    scene.camera = cam

    def light(name, loc, energy, color, size):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        bpy.context.collection.objects.link(lo)
        lo.location = loc
        c = lo.constraints.new('TRACK_TO')
        c.target = tgt
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'

    # 灯光随场景尺度等比放大，保证任何距离下曝光一致
    k = max(distance, 0.5) / 5.4
    light("KeyLight", (3.8 * k, -4.0 * k, target[2] + 4.8 * k), 340 * k * k,
          (1.00, 0.96, 0.90), 4.0 * k)
    light("FillLight", (-4.4 * k, -2.6 * k, target[2] + 2.2 * k), 95 * k * k,
          (0.70, 0.82, 1.00), 5.5 * k)
    light("RimLight", (-1.8 * k, 4.6 * k, target[2] + 3.8 * k), 210 * k * k,
          (1.00, 0.80, 0.60), 3.0 * k)

    world = bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.042, 0.048, 0.060, 1.0)
        bg.inputs[1].default_value = 0.9
    scene.world = world

    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = out_png
    try:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Base Contrast'
        scene.view_settings.exposure = -0.35
    except Exception:
        pass


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
