# -*- coding: utf-8 -*-
"""插入 UpdateHeroFill 实现，并在 Tick 里调用。"""
import io

P = r"ue/Source/RobotGame/Private/RobotCharacter.cpp"
d = io.open(P, "r", encoding="utf-8", newline="").read()

# ── ① 实现：插在 UpdateDebugCamera 定义之前 ──
anchor = "void ARobotCharacter::UpdateDebugCamera()"
assert d.count(anchor) == 1

impl = '''/**
 * \u82f1\u96c4\u8865\u5149\u8ddf\u968f\u3002
 *
 * \u706f\u4f4d = \u73a9\u5bb6\u4f4d\u7f6e + \u300c\u671d\u955c\u5934\u65b9\u5411\u300d\u504f\u540e 300cm
 *          + \u955c\u5934\u53f3\u65b9\u5411\u504f -170cm + \u62ac 260cm\u3002
 *
 * \u4e3a\u4ec0\u4e48\u4e0d\u76f4\u63a5\u653e\u5728\u955c\u5934\u4f4d\u7f6e\uff1a\u90a3\u7b49\u4e8e\u300c\u6241\u5e73\u6253\u5149\u300d\uff0c
 * \u88c5\u7532\u7684\u5012\u89d2\u3001\u51f9\u69fd\u3001\u87ba\u6813\u5168\u90e8\u5931\u53bb\u9634\u5f71\uff0c\u673a\u4f53\u53d8\u6210\u4e00\u5757\u80a5\u7682\u3002
 * \u504f\u5230\u5de6\u4e0a\u65b9\u65e2\u80fd\u5310\u4eae\u955c\u5934\u770b\u5f97\u89c1\u7684\u90a3\u9762\uff0c\u53c8\u7559\u4e0b\u4e00\u70b9\u4f53\u79ef\u611f\uff0c
 * \u548c\u53f3\u4fa7\u7684\u6696\u8272\u5149\u6c60\u5f62\u6210\u201c\u5de6\u51b7\u53f3\u6696\u201d\u3002
 *
 * \u6bcf\u5e27\u4e00\u6b21 SetActorLocation \u5bf9\u4e00\u76cf Movable \u70b9\u5149\u662f\u5fae\u4e0d\u8db3\u9053\u7684\u5f00\u9500\uff08\u4e0d\u91cd\u5efa\u6e32\u67d3\u72b6\u6001\uff09\u3002
 */
void ARobotCharacter::UpdateHeroFill()
{
\tAActor* Lamp = HeroFillLight.Get();
\tif (!Lamp)
\t{
\t\treturn;
\t}

\tFVector Toward = -GetActorForwardVector();
\tFVector Side = GetActorRightVector();
\tif (APlayerController* PC = Cast<APlayerController>(GetController()))
\t{
\t\tFVector CamLoc;
\t\tFRotator CamRot;
\t\tPC->GetPlayerViewPoint(CamLoc, CamRot);
\t\tFVector ToCam = CamLoc - GetActorLocation();
\t\tToCam.Z = 0.f;
\t\tif (!ToCam.IsNearlyZero())
\t\t{
\t\t\tToward = ToCam.GetSafeNormal();
\t\t\tSide = FRotationMatrix(CamRot).GetScaledAxis(EAxis::Y).GetSafeNormal();
\t\t}
\t}

\tFVector Target = GetActorLocation() + Toward * 300.f - Side * 170.f;
\tTarget.Z = FMath::Max(Target.Z, 0.f) + 260.f;
\tLamp->SetActorLocation(Target);
}

'''

d = d.replace(anchor, impl + anchor, 1)

# ── ② Tick 调用：紧跟 ClampToArena(); ──
tick_anchor = "\tClampToArena();\r\n"
assert d.count(tick_anchor) == 1, d.count(tick_anchor)

call = (
    "\tClampToArena();\r\n"
    "\r\n"
    "\t// \u8865\u5149\u8ddf\u7740\u955c\u5934\u8d70\uff08\u4f4d\u7f6e\u6bcf\u5e27\u7b97\uff0c"
    "\u70b9\u5149\u672c\u8eab\u53c2\u6570\u5728 BeginPlay \u91cc\u5df2\u7ecf\u5b9a\u597d\uff09\u3002\r\n"
    "\tUpdateHeroFill();\r\n"
)
d = d.replace(tick_anchor, call, 1)

io.open(P, "w", encoding="utf-8", newline="").write(d)
print("ok", d.count("UpdateHeroFill"))
