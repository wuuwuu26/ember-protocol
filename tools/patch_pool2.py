# -*- coding: utf-8 -*-
"""Replace the runtime-spawned pool lights with tuning of level PoolLight actors."""
import io

P = r"ue/Source/RobotGame/Private/RobotCharacter.cpp"
s = io.open(P, encoding="utf-8").read()

start = s.index("\tfor (TActorIterator<ASpotLight> It(World); It; ++It)")
end = s.index("\tUE_LOG(LogTemp, Warning,\n\t\tTEXT(\"[灯] 分工完成")

new_block = '''\t// ── 聚光灯分两类：投光（Flood）与光池（Pool）──
\t//
\t// 光池是**关卡里就有的** 5 盏 PoolLight（由 ue/Scripts/arena_pools.py 生成），
\t// 不是运行时 SpawnActor。为什么放弃运行时生成：
\t//   2026-10-25 实测，SpawnActor / SpawnActorDeferred 出来的灯，
\t//   强度/可见/注册/影响世界 全是 1、位置也对，但画面**一个像素都不亮**
\t//   （开池/关池截图的地板均值都是 0.299，完全一致）。同样的参数
\t//   写进关卡里的 Light actor 就正常。与其继续和运行时生成较劲，
\t//   不如走和 8 盏投光完全相同的路径：编辑器建、C++ 调。
\t//
\t// 光池为什么必须有：8 盏 FloodLight 全装在场地边缘（11~15m），
\t//  按平方反比它们照不到玩家脚下 —— 地面一直是一张均匀的冷灰台面。
\t//  光池挂在 (±1100,±1100) 与 (0,0) 的甲板下方（z=620，甲板在 700），
\t//  60000cd / 6.2m ≈ 1560 lux 的暖色亮斑，才有"亮斑 + 暗区"的节奏。
\t//
\t// -NoPool 关掉用于对比，-PoolCd= 扫强度。
\tint32 NumPool = 0;
\tfor (TActorIterator<ASpotLight> It(World); It; ++It)
\t{
\t\tUSpotLightComponent* C =
\t\t\tCast<USpotLightComponent>(It->GetLightComponent());
\t\tif (!C)
\t\t{
\t\t\tcontinue;
\t\t}
\t\tconst FString Label = It->GetActorNameOrLabel();

\t\tif (Label.StartsWith(TEXT("PoolLight")))
\t\t{
\t\t\tif (FParse::Param(FCommandLine::Get(), TEXT("NoPool")))
\t\t\t{
\t\t\t\tC->SetVisibility(false);
\t\t\t\tC->MarkRenderStateDirty();
\t\t\t\tcontinue;
\t\t\t}
\t\t\tC->SetVisibility(true);
\t\t\tC->SetMobility(EComponentMobility::Movable);
\t\t\tC->SetIntensity(PoolCd);
\t\t\tC->SetAttenuationRadius(2600.f);
\t\t\t// 3200K 暖白：光池要暖得"像人造钠灯"，才能和冷蓝月光拉开色温。
\t\t\tC->SetLightColor(FLinearColor(1.00f, 0.72f, 0.46f));
\t\t\t// 34° 外锥 = 6.2m 高度下地面半径 4.2m，五个圆之间留暗区。
\t\t\tC->SetInnerConeAngle(12.f);
\t\t\tC->SetOuterConeAngle(34.f);
\t\t\tC->SetCastShadows(true);
\t\t\tC->SetVolumetricScatteringIntensity(0.45f);
\t\t\tC->MarkRenderStateDirty();
\t\t\t++NumPool;
\t\t\tcontinue;
\t\t}

\t\tif (!Label.StartsWith(TEXT("FloodLight")))
\t\t{
\t\t\tcontinue;
\t\t}

\t\tC->SetMobility(EComponentMobility::Movable);
\t\tC->SetIntensity(FloodCd);
\t\tC->SetAttenuationRadius(3600.f);
\t\t// 4200K 暖白：和冷蓝月光形成冷暖对冲 —— 这是夜景机甲最经典的一套打光。
\t\t// 直接用颜色而不是色温属性：色温属性依赖"用色温"开关，
\t\t// 脚本改过之后这个开关状态并不可靠（实测全部变成了纯白 1,1,1）。
\t\tC->SetLightColor(FLinearColor(1.00f, 0.78f, 0.56f));
\t\tC->SetCastShadows(true);
\t\t// 光锥：内置默认值（44°）投到 7m 地面只有 5m 宽的光斑，
\t\t// 八盏灯之间必然留缝。收到 52° 让相邻光池能连成一条亮带。
\t\tC->SetInnerConeAngle(18.f);
\t\tC->SetOuterConeAngle(52.f);
\t\t// 体积散射：让光锥在雾里可见（丁达尔），值小一点避免整屏发灰。
\t\tC->SetVolumetricScatteringIntensity(0.85f);
\t\tC->MarkRenderStateDirty();
\t\t++NumFlood;
\t}

'''

s = s[:start] + new_block + s[end:]
io.open(P, "w", encoding="utf-8").write(s)
print("patched")
