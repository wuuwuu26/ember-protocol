#include "RobotGameMode.h"

#include "RobotCharacter.h"
#include "RobotEnemy.h"
#include "RobotPlayerController.h"

#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"

ARobotGameMode::ARobotGameMode()
{
	RobotCharacterClass = ARobotCharacter::StaticClass();
	DefaultPawnClass = RobotCharacterClass;
	// 自定义控制器：主菜单和 HUD 都挂在它上面。
	// 构造函数一定会执行，所以这里设的类不会被蓝图"顺手"改掉。
	PlayerControllerClass = ARobotPlayerController::StaticClass();

	// 单机项目不需要 HUD 的网络同步，保持默认即可
	bStartPlayersAsSpectators = false;

	// 任务判定（胜负结算）需要 Tick —— GameModeBase 默认不 Tick
	PrimaryActorTick.bCanEverTick = true;
}

void ARobotGameMode::StartPlay()
{
	Super::StartPlay();

	UWorld* World = GetWorld();
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;

	if (World)
	{
		MissionStartTime = World->GetTimeSeconds();
	}

	if (ARobotPlayerController* RPC = Cast<ARobotPlayerController>(PC))
	{
		RPC->ShowMainMenu();
	}
	else
	{
		UE_LOG(LogTemp, Warning,
			TEXT("[菜单] 玩家控制器不是 ARobotPlayerController（实际是 %s），主菜单不会显示"),
			PC ? *PC->GetClass()->GetName() : TEXT("空"));
	}
}

// ─────────────────────────────────────────────
// 任务目标与胜负结算
// ─────────────────────────────────────────────

void ARobotGameMode::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bMissionFinished)
	{
		return;
	}
	UWorld* W = GetWorld();
	if (!W)
	{
		return;
	}

	const float Now = W->GetTimeSeconds();

	// 开局 1 秒后再统计初始敌人数（等所有 Actor 注册完成；
	// 统计脚本摆进关卡的敌人与运行时生成的敌人都算）。
	if (InitialEnemyCount < 0)
	{
		if (Now - MissionStartTime < 1.0f)
		{
			return;
		}
		int32 Count = 0;
		for (TActorIterator<ARobotEnemy> It(W); It; ++It)
		{
			++Count;
		}
		InitialEnemyCount = Count;
		UE_LOG(LogTemp, Warning, TEXT("[任务] 目标：肃清区域。初始敌人 %d 个"),
			Count);
		return;
	}

	// 胜利：开局有敌人，且已全部瘫痪（核心被毁或功能部位尽毁）。
	// 存活数直接用玩家控制器里的 0.5 秒缓存，不重复遍历。
	if (InitialEnemyCount > 0)
	{
		if (ARobotPlayerController* PC = Cast<ARobotPlayerController>(
				W->GetFirstPlayerController()))
		{
			if (PC->GetAliveEnemyCount() == 0)
			{
				FinishMission(true);
			}
		}
	}
}

void ARobotGameMode::NotifyPlayerDefeated()
{
	if (bMissionFinished)
	{
		return;
	}
	FinishMission(false);
}

void ARobotGameMode::FinishMission(bool bVictory)
{
	if (bMissionFinished)
	{
		return;
	}
	bMissionFinished = true;

	UWorld* W = GetWorld();
	ARobotPlayerController* PC = W
		? Cast<ARobotPlayerController>(W->GetFirstPlayerController()) : nullptr;

	const float Elapsed = W ? (W->GetTimeSeconds() - MissionStartTime) : 0.f;

	int32 Salvage = 0;
	if (PC)
	{
		if (const ARobotCharacter* R = Cast<ARobotCharacter>(PC->GetPawn()))
		{
			Salvage = R->GetSalvage();
		}
	}
	const int32 Alive = PC ? PC->GetAliveEnemyCount() : 0;
	const int32 Killed = FMath::Max(InitialEnemyCount - Alive, 0);

	const FString Stats = FString::Printf(
		TEXT("用时 %.1f 秒　·　回收废料 %d　·　击毁 %d / %d"),
		Elapsed, Salvage, Killed, FMath::Max(InitialEnemyCount, 0));

	UE_LOG(LogTemp, Warning, TEXT("[任务] %s"),
		bVictory ? TEXT("区域已肃清 —— 任务完成") : TEXT("机体瘫痪 —— 任务失败"));

	if (PC)
	{
		PC->ShowEndScreen(bVictory, Stats);
	}
}

void ARobotGameMode::BeginPlay()
{
	Super::BeginPlay();
	EnsureLevelLighting();
}

void ARobotGameMode::EnsureLevelLighting()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	int32 Fixed = 0;

	// ── 平行光 ──
	for (TActorIterator<ADirectionalLight> It(World); It; ++It)
	{
		UDirectionalLightComponent* C =
			Cast<UDirectionalLightComponent>(It->GetLightComponent());
		if (!C)
		{
			continue;
		}
		C->SetMobility(EComponentMobility::Movable);
		// ★ 2026-10-24：100000 lux + 暖白 (1, 0.96, 0.89) 会把场景烤成一片橙红，
		//    而且它和 RobotCharacter::FixLevelLighting 里的太阳参数互相覆盖，
		//    谁也说不清运行时到底是哪个值。
		//    现在两边用同一组数：9000 lux 冷白月光（太阳当主光，
		//    11 盏暖色装饰点光只做氛围）。
		C->SetIntensity(9000.f);
		C->SetLightColor(FLinearColor(0.78f, 0.86f, 1.00f));
		// ★ 2026-10-24：必须是 false。
		//
		//    SkyAtmosphere 一旦把这盏灯认成"自己的太阳"，就会对它的光做一次
		//    大气透过率计算（低角度 → 强暖橙）。结果是：不管 light_color
		//    设成多冷的颜色，落到场景里都是暖的 —— 实测 R/B 恒在 1.3 左右，
		//    而把这一位关掉后立刻回到 1.00（完全中性）。
		//
		//    这里原来写的是 true，和 RobotCharacter::FixLevelLighting 里的
		//    false 互相打架：谁后执行取决于 Actor 初始化顺序，所以画面
		//    时暖时冷（同一份代码两次运行结果不同）。两处必须一致。
		C->SetAtmosphereSunLight(false);
		C->MarkRenderStateDirty();
		++Fixed;

		UE_LOG(LogTemp, Warning,
			TEXT("[灯光] 平行光已修正：Movable / 9000 lux 冷白 / 大气太阳光"));
	}

	// ── 天光 ──
	for (TActorIterator<ASkyLight> It(World); It; ++It)
	{
		USkyLightComponent* C = It->GetLightComponent();
		if (!C)
		{
			continue;
		}
		C->SetMobility(EComponentMobility::Movable);
		// 天光 2.4 + 冷蓝，和正式路径一致
		C->SetIntensity(2.4f);
		C->SetLightColor(FLinearColor(0.62f, 0.74f, 1.00f));
		// 实时捕获：没有烘焙的天空贴图时，不实时捕获就没有任何环境光
		C->bRealTimeCapture = true;
		C->SetVisibility(true);
		C->MarkRenderStateDirty();
		C->RecaptureSky();
		++Fixed;

		UE_LOG(LogTemp, Warning,
			TEXT("[灯光] 天光已修正：Movable / 实时捕获 / 强度 1.0"));
	}

	UE_LOG(LogTemp, Warning, TEXT("[灯光] 运行时共修正 %d 个灯光"), Fixed);
}
