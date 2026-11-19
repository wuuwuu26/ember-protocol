// 音效播放小工具 —— 把"加载 + 播放"压缩成一行调用。
//
// 为什么不做成完整的音效管理器：垂直切片阶段只需要"能响"，
// 真正的项目里应该由 AudioComponent 池 + 衰减资产来做。
// 这里用 LoadObject（引擎自带缓存）+ PlaySoundAtLocation 就够，
// 且**加这个头文件不需要改构建图**（无新 .cpp、无反射声明）。
#pragma once

#include "CoreMinimal.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundBase.h"
#include "UObject/UObjectGlobals.h"

namespace RobotSfx
{
	// 音效资产路径统一前缀
	constexpr const TCHAR* SfxDir = TEXT("/Game/RobotGame/Audio/");

	/**
	 * 默认衰减：3.8m 距离内基本满响、之后平滑衰减。
	 * 运行时创建一个瞬态 USoundAttenuation 并 AddToRoot —— 不开编辑器资产
	 * 就能拿到"有距离感"的 3D 音效（不开衰减的话，远处的敌人开火和贴脸一样响）。
	 */
	inline USoundAttenuation* DefaultAttenuation()
	{
		static USoundAttenuation* Cached = nullptr;
		if (!Cached)
		{
			Cached = NewObject<USoundAttenuation>(GetTransientPackage());
			if (Cached)
			{
				Cached->AddToRoot();   // 防止 GC 收走正在使用的衰减配置
				Cached->Attenuation.bAttenuate = true;
				Cached->Attenuation.bSpatialize = true;
				Cached->Attenuation.FalloffDistance = 3800.f;
			}
		}
		return Cached;
	}

	/** 在位置播放一个音效。Pitch 加随机抖动能避免连发时"机械复读"。 */
	inline void PlayAt(const UObject* Ctx, const TCHAR* Name,
		const FVector& Loc, float Volume = 1.f, float Pitch = 1.f,
		bool bRandomPitch = false)
	{
		if (!Ctx)
		{
			return;
		}
		const FString Path = FString::Printf(TEXT("%s%s.%s"), SfxDir, Name, Name);
		if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, *Path))
		{
			const float P = bRandomPitch
				? Pitch * FMath::FRandRange(0.94f, 1.06f) : Pitch;
			UGameplayStatics::PlaySoundAtLocation(
				Ctx, Sound, Loc, Volume, P, 0.f, DefaultAttenuation());
		}
	}
}
