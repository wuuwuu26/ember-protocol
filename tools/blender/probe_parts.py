import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import robotlib as R
import build_chassis as BC

P = BC.variant_params("medium")
pal = R.Palette(P["accent"], P["glow"], P["code"])
R.new_scene()
pal = R.Palette(P["accent"], P["glow"], P["code"])
A = BC.build(P, pal)

rows = []
for ob in A.all:
    mn, mx = R.world_bounds([ob])
    dx, dy, dz = mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]
    # 只看"在胸口高度、且前后跨度大"的件
    if mn[2] < 2.2 and mx[2] > 1.7:
        rows.append((dy, ob.name, mn, mx, dx, dy, dz))
rows.sort(reverse=True)
print("%-26s %7s %7s %7s   %s" % ("name", "dX", "dY", "dZ", "Z范围"))
for _, nm, mn, mx, dx, dy, dz in rows[:14]:
    print("%-26s %7.3f %7.3f %7.3f   %.2f ~ %.2f" % (nm, dx, dy, dz, mn[2], mx[2]))
