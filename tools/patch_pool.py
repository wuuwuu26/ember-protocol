# -*- coding: utf-8 -*-
"""One-off patch: make pool light height / shadow / state configurable."""
import io

P = r"ue/Source/RobotGame/Private/RobotCharacter.cpp"
s = io.open(P, encoding="utf-8").read()

old = """		for (const FVector& Spot : PoolSpots)
		{
			const FVector Loc = Spot + FVector(0.f, 0.f, 620.f);"""
new = """		float PoolZ = 620.f;
		{
			FString V;
			if (FParse::Value(FCommandLine::Get(), TEXT("PoolZ="), V))
			{
				PoolZ = FCString::Atof(*V);
			}
		}
		const bool bPoolShadow =
			!FParse::Param(FCommandLine::Get(), TEXT("PoolNoShadow"));

		for (const FVector& Spot : PoolSpots)
		{
			const FVector Loc = Spot + FVector(0.f, 0.f, PoolZ);"""
assert old in s, "anchor 1"
s = s.replace(old, new)

old2 = """				C->SetCastShadows(true);
				C->SetVolumetricScatteringIntensity(0.45f);"""
new2 = """				C->SetCastShadows(bPoolShadow);
				C->SetVolumetricScatteringIntensity(0.45f);"""
assert old2 in s, "anchor 2"
s = s.replace(old2, new2)

old3 = """					TEXT("[光池] %d 位置=(%.0f,%.0f,%.0f) 强度=%.0f 锥=%.0f/%.0f 半径=%.0f 可见=%d"),
					NumPool, WL.X, WL.Y, WL.Z, C->Intensity,
					C->InnerConeAngle, C->OuterConeAngle, C->AttenuationRadius,
					C->IsVisible() ? 1 : 0);"""
new3 = """					TEXT("[光池] %d 位置=(%.0f,%.0f,%.0f) 强度=%.0f 锥=%.0f/%.0f 半径=%.0f "
						 "可见=%d 注册=%d 影响世界=%d 移动=%d 影=%d"),
					NumPool, WL.X, WL.Y, WL.Z, C->Intensity,
					C->InnerConeAngle, C->OuterConeAngle, C->AttenuationRadius,
					C->IsVisible() ? 1 : 0, C->IsRegistered() ? 1 : 0,
					C->bAffectsWorld ? 1 : 0,
					C->Mobility == EComponentMobility::Movable ? 1 : 0,
					C->CastShadows ? 1 : 0);"""
assert old3 in s, "anchor 3"
s = s.replace(old3, new3)

io.open(P, "w", encoding="utf-8").write(s)
print("patched")
