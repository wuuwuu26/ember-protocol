"""C_9 是缩放到 0.5 的。骨骼长度是用米算的（BoneUnitPerCm），
但如果组件有非均匀缩放，TransformPosition 会用缩放后的坐标。
验证：C_9 的腿在"组件空间"里的长度是否是 166cm 的 0.5 倍。"""
import re
from collections import defaultdict

p = r"C:\Users\25227\Documents\robot_game\ue\shot_r590_OK.log"
rows = defaultdict(list)
for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
    if "FootCSV" not in ln:
        continue
    s = ln[ln.find("[FootCSV]"):]
    m = dict(re.findall(r"(\w+)=(-?[\d.]+)", s))
    m["leg"] = re.search(r"leg=(\S+)", s).group(1)
    o = re.search(r"owner=(\S+)", s).group(1)
    rows[(o, m["leg"])].append(m)

for key in [("BP_RobotCharacter_C_0", "L"), ("BP_Enemy_C_8", "L"), ("BP_Enemy_C_9", "L")]:
    seq = [r for r in rows[key] if 2 < float(r["t"]) < 2.1]
    r = seq[0]
    # 用引擎骨骼矩阵（bmx/bmz）和 hipz 反推组件缩放
    # hipz 是组件空间值（206.8 for C_9），fz 是世界（22.7）
    fz, bmz = float(r["fz"]), float(r["bmz"])
    hipz = float(r["hipz"])
    # 若 fz 是世界，则脚的世界高度应≈0（地面），但 C_9 fz=22.7
    print("%-22s fz=%7.2f bmz=%7.2f hipz=%7.2f  ankz=%6.2f  fz-ankz=%7.2f"
          % (key[0], fz, bmz, hipz, float(r["ankz"]), fz - float(r["ankz"])))
