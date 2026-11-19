#include "RobotPlayerController.h"

#include "RobotEnemy.h"
#include "RobotCharacter.h"
#include "AssemblyComponent.h"
#include "RobotModuleData.h"
#include "RobotTypes.h"
#include "PartDamageComponent.h"
#include "PartMapData.h"
#include "UI/RobotMainMenu.h"
#include "UI/RobotHUD.h"
#include "UI/RobotWorldMarker.h"
#include "UI/RobotObserverHUD.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameUserSettings.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SViewport.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Containers/Ticker.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Camera/PlayerCameraManager.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/MeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "InputCoreTypes.h"

namespace
{
	// 调试开关：只在排查界面时用，正常玩保持 0。
	//   0 = 正常（启动弹主菜单）
	//   1 = 跳过主菜单，直接开始（用来单独看 HUD）
	//   2 = 启动就停在设置页（用来单独看设置界面）
	static TAutoConsoleVariable<int32> CVarMenuDebug(
		TEXT("Robot.MenuDebug"), 0,
		TEXT("0=正常 1=跳过菜单 2=直接进设置页"),
		ECVF_Default);


	/**
	 * 从相机中心往前打一条射线，把沿途命中的 Actor / 组件 / 材质打出来。
	 *
	 * 用途：定位"画面正中一个灰色方块"到底是场景里的哪个东西。
	 * 靠肉眼看截图猜了太多轮都猜错（动画网格、敌人、后墙、道具都排除了），
	 * 射线检测是确定性的 —— 它打到谁就是谁。
	 */
	void ProbeCenterView(APlayerController* PC)
	{
		if (!PC) { return; }
		APlayerCameraManager* Cam = PC->PlayerCameraManager;
		UWorld* World = PC->GetWorld();
		if (!Cam || !World) { return; }

		const FVector Start = Cam->GetCameraLocation();
		const FVector Dir = Cam->GetCameraRotation().Vector();
		const FVector End = Start + Dir * 20000.f;

		FCollisionQueryParams Params(SCENE_QUERY_STAT(CenterProbe), true);
		if (const APawn* P = PC->GetPawn())
		{
			Params.AddIgnoredActor(P);
		}

		TArray<FHitResult> Hits;
		World->LineTraceMultiByChannel(Hits, Start, End, ECC_Visibility, Params);

		UE_LOG(LogTemp, Warning,
			TEXT("[探针] 相机(%.0f,%.0f,%.0f) 朝(%.2f,%.2f,%.2f) 命中 %d 个"),
			Start.X, Start.Y, Start.Z, Dir.X, Dir.Y, Dir.Z, Hits.Num());

		for (int32 i = 0; i < FMath::Min(Hits.Num(), 10); ++i)
		{
			const FHitResult& H = Hits[i];
			FString MatName = TEXT("-");
			if (const UMeshComponent* MeshComp = Cast<UMeshComponent>(H.GetComponent()))
			{
				if (const UMaterialInterface* Mat = MeshComp->GetMaterial(0))
				{
					MatName = Mat->GetName();
				}
				else
				{
					MatName = TEXT("空");
				}
			}
			UE_LOG(LogTemp, Warning,
				TEXT("[探针] %d) Actor=%s 组件=%s 材质0=%s 距%.0fcm @(%.0f,%.0f,%.0f)"),
				i, *GetNameSafe(H.GetActor()),
				H.GetComponent() ? *H.GetComponent()->GetName() : TEXT("?"),
				*MatName, H.Distance, H.Location.X, H.Location.Y, H.Location.Z);
		}
	}

	FString WindowModeName(EWindowMode::Type Mode)	{
		switch (Mode)
		{
		case EWindowMode::Fullscreen:         return TEXT("全屏");
		case EWindowMode::WindowedFullscreen: return TEXT("无边框窗口");
		default:                              return TEXT("窗口化");
		}
	}

	FString QualityName(int32 Level)
	{
		switch (Level)
		{
		case 0:  return TEXT("低");
		case 1:  return TEXT("中");
		case 2:  return TEXT("高");
		default: return TEXT("极高");
		}
	}
}

ARobotPlayerController::ARobotPlayerController()
{
	// 菜单要能点，默认的输入模式由 ShowMainMenu 显式设置
	bShowMouseCursor = false;
	// 调试连拍要在 Tick 里推进
	PrimaryActorTick.bCanEverTick = true;
	// ⚠️ 暂停时也要 Tick：改装台/主菜单都会 SetPause(true)，
	// 而无人值守验证的驱动（AutoQuit / 连拍 / 改装UI时间线）全在 Tick 里。
	// 只设 bTickEvenWhenPaused 不够 —— PlayerController 还需要
	// bShouldPerformFullTickWhenPaused 才会在暂停时完整 Tick
	//（实测漏掉这一条：打开改装台后整个世界冻住、自动退出永远不触发）。
	PrimaryActorTick.bTickEvenWhenPaused = true;
	bShouldPerformFullTickWhenPaused = true;
}

void ARobotPlayerController::BeginPlay()
{
	Super::BeginPlay();

	// 高分屏（Windows 200% 缩放）下 Slate 会以 2x 应用缩放绘制 HUD，
	// 而设计画布固定 1280x720，结果整块 UI 被重复平铺成 2x2（截图里能看到
	// 多份「残敌 / 热量 / 电力」面板叠在画面各处）。强制 1:1 应用缩放后，
	// HUD 只随视口等比缩放一次，任何分辨率下都不再重影。
	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().SetApplicationScale(1.0f);
	}

	// HUD 先建出来（菜单打开时隐藏），这样点"开始游戏"后立刻就有反馈
	CreateHUD();
	// 菜单由 GameMode::StartPlay 触发显示（那里能确保玩家控制器已经就绪）。
	// 这里只把窗口焦点抢过来 —— -game 模式启动的窗口经常拿不到键盘焦点。
	FocusGameViewport();

	// -Observer：启动即进入观察者模式（自动截图验收用，等价于按一次 V）。
	// 延到首帧 Tick 再进：BeginPlay 时 Pawn/PlayerCameraManager 可能还没就绪，
	// 那样 EnterObserver 取不到相机起点。用 bObserverPending 在 Tick 里触发。
	if (FParse::Param(FCommandLine::Get(), TEXT("Observer")))
	{
		bObserverPending = true;
	}
}

void ARobotPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	if (!InputComponent) { return; }

	// V 键：切换观察者模式。用 PlayerController 自己的 InputComponent 绑
	// （老式 BindKey），不碰 Character 的 EnhancedInput 资产体系，也避免
	// 依赖 EnhancedInput 的 MappingContext 是否已注入。
	InputComponent->BindKey(EKeys::V, IE_Pressed,
		this, &ARobotPlayerController::ToggleObserver);
	// 滚轮：观察者模式下调速。轴值累加到成员，TickObserver 里消费。
	InputComponent->BindAxisKey(EKeys::MouseWheelAxis,
		this, &ARobotPlayerController::OnObserverScroll);

	// 控制台命令双保险：无法按键 / 远程执行时可用 `Robot.ToggleObserver`
	static FAutoConsoleCommandWithWorld CVarToggleObserver(
		TEXT("Robot.ToggleObserver"),
		TEXT("切换观察者模式（自由飞行相机）"),
		FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* W)
		{
			if (W)
			{
				if (APlayerController* PC = W->GetFirstPlayerController())
				{
					if (ARobotPlayerController* RPC = Cast<ARobotPlayerController>(PC))
					{
						RPC->ToggleObserver();
					}
				}
			}
		}));
}

void ARobotPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	RemoveMenuFromViewport();
	RemoveObserverHUD();
	if (GEngine && GEngine->GameViewport)
	{
		if (HUDWidget.IsValid())
		{
			GEngine->GameViewport->RemoveViewportWidgetContent(HUDWidget.ToSharedRef());
		}
		if (WorldMarkers.IsValid())
		{
			GEngine->GameViewport->RemoveViewportWidgetContent(WorldMarkers.ToSharedRef());
		}
	}
	HUDWidget.Reset();
	WorldMarkers.Reset();
	Super::EndPlay(EndPlayReason);
}

/**
 * 调试：推进 -AutoShot 连拍。
 *
 * 关键点是"上一张还没落盘就不要再请求" —— FScreenshotRequest 同一时刻
 * 只保留一个挂起请求，1.6MB 的 PNG 写盘要几百毫秒，密集请求会被静默丢弃。
 * 所以这里每帧检查 IsScreenshotRequested()，空闲了才发下一张。
 */
static void CaptureShot(APlayerController* PC)
{
	// -HighShot：走 HighResShot 的独立截帧路径。
	// 某些机器上 RequestScreenshot 的 GPU 回读会把不同帧拼成瓦片（HUD 重影），
	// HighResShot 走的是另一条 FFrameGrabber 管线，出来的图更干净。
	if (FParse::Param(FCommandLine::Get(), TEXT("HighShot")))
	{
		if (PC)
		{
			PC->ConsoleCommand(TEXT("HighResShot 1"));
		}
		return;
	}
	FScreenshotRequest::RequestScreenshot(true);
}

void ARobotPlayerController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// 观察者模式：自由飞行相机每帧推进（不暂停世界，敌人照常动，方便观察）
	// -Observer 启动参数：首帧补进观察者（BeginPlay 时相机系统未必就绪）
	if (bObserverPending)
	{
		bObserverPending = false;
		if (PlayerCameraManager && GetPawn())
		{
			EnterObserver();
		}
	}
	TickObserver(DeltaSeconds);

	// 调试：-AutoQuit=<秒> 到点自动退出。
	// 无人值守跑验证时必须有它 —— 否则游戏进程会一直挂着，
	// 而它在后台占着 DLL，下一次链接会报 LNK1104。
	if (AutoQuitAt > 0.f)
	{
		if (const UWorld* W = GetWorld())
		{
			if (W->GetTimeSeconds() >= AutoQuitAt)
			{
				UE_LOG(LogTemp, Warning, TEXT("[调试] 到点自动退出（%.1fs）"), AutoQuitAt);
				AutoQuitAt = -1.f;
				ConsoleCommand(TEXT("quit"));
				return;
			}
		}
	}

	// 存活敌人计数：0.5 秒刷一次，HUD 每帧读缓存值。
	if (UWorld* W2 = GetWorld())
	{
		if (W2->GetTimeSeconds() >= EnemyCountNextRefresh)
		{
			EnemyCountNextRefresh = W2->GetTimeSeconds() + 0.5f;
			RefreshEnemyCount();
		}

		// 伤害数字：每帧推进年龄并清掉过期的（数量少，开销可忽略）
		if (DamageNumbers.Num() > 0)
		{
			for (int32 i = DamageNumbers.Num() - 1; i >= 0; --i)
			{
				DamageNumbers[i].Age += DeltaSeconds;
				if (DamageNumbers[i].Age >= DamageNumbers[i].Life)
				{
					DamageNumbers.RemoveAt(i);
				}
			}
		}

		// 部位提示：0.1 秒刷新一次（每帧做一次射线 + 骨骼距离计算没必要）
		if (W2->GetTimeSeconds() >= PartHintNextRefresh)
		{
			PartHintNextRefresh = W2->GetTimeSeconds() + 0.1f;
			RefreshAimHint();
		}

		// 调试：-ShotEvery=<秒> 每隔 N 秒抓一张（视觉验收用）
		if (ShotEverySeconds > 0.f && W2->GetTimeSeconds() >= ShotEveryNextTime)
		{
			ShotEveryNextTime = W2->GetTimeSeconds() + ShotEverySeconds;
			if (!FScreenshotRequest::IsScreenshotRequested())
			{
				CaptureShot(this);
				UE_LOG(LogTemp, Warning, TEXT("[连拍] 定时抓图 t=%.1fs"),
					W2->GetTimeSeconds());
			}
		}

		// 调试：到点补拍一张（结算画面）
		if (!bAutoShotAtDone && AutoShotAt > 0.f
			&& W2->GetTimeSeconds() >= AutoShotAt)
		{
			bAutoShotAtDone = true;
			if (!FScreenshotRequest::IsScreenshotRequested())
			{
				CaptureShot(this);
				UE_LOG(LogTemp, Log, TEXT("[连拍] 补拍一张（t=%.1f）"),
					W2->GetTimeSeconds());
			}
		}
	}

	if (ShotBurstRemaining <= 0)
	{
		return;
	}
	const UWorld* World = GetWorld();
	if (!World || World->GetTimeSeconds() < ShotBurstNextTime)
	{
		return;
	}
	if (FScreenshotRequest::IsScreenshotRequested())
	{
		// 上一张还在写盘，下一帧再看
		return;
	}

	CaptureShot(this);
	--ShotBurstRemaining;
	ShotBurstNextTime = World->GetTimeSeconds() + 0.1f;
	UE_LOG(LogTemp, Log, TEXT("[连拍] 已请求第 %d 张（t=%.2f）"),
		14 - ShotBurstRemaining, World->GetTimeSeconds());
}

// ─────────────────────────────────────────────
// 战斗反馈
// ─────────────────────────────────────────────

void ARobotPlayerController::NotifyHitConfirmed(bool bKilled, const FVector& WorldLocation)
{
	if (const UWorld* W = GetWorld())
	{
		HitMarkerTime = W->GetTimeSeconds();
		bLastHitWasKill = bKilled;
	}
	++TotalHits;
}

void ARobotPlayerController::NotifyPlayerDamaged()
{
	if (const UWorld* W = GetWorld())
	{
		DamageFlashTime = W->GetTimeSeconds();
	}
}

float ARobotPlayerController::GetHitMarkerAge() const
{
	if (const UWorld* W = GetWorld())
	{
		return W->GetTimeSeconds() - HitMarkerTime;
	}
	return 1e9f;
}

float ARobotPlayerController::GetDamageFlashAge() const
{
	if (const UWorld* W = GetWorld())
	{
		return W->GetTimeSeconds() - DamageFlashTime;
	}
	return 1e9f;
}

int32 ARobotPlayerController::GetAliveEnemyCount() const
{
	return AliveEnemyCount;
}

// ─────────────────────────────────────────────
// 伤害数字与部位提示
// ─────────────────────────────────────────────

namespace
{
	/** 部位标签 → 中文短名（打出来要一眼看懂"打的是腿"） */
	FString PartShortName(const FGameplayTag& Tag)
	{
		if (!Tag.IsValid())
		{
			return FString();
		}
		static const TMap<FString, FString> Names =
		{
			{ TEXT("Part.Core"),     TEXT("核心") },
			{ TEXT("Part.Torso"),    TEXT("躯干") },
			{ TEXT("Part.Head"),     TEXT("头部") },
			{ TEXT("Part.Arm.L"),    TEXT("左臂") },
			{ TEXT("Part.Arm.R"),    TEXT("右臂") },
			{ TEXT("Part.Leg.L"),    TEXT("左腿") },
			{ TEXT("Part.Leg.R"),    TEXT("右腿") },
		};
		const FString Key = Tag.ToString();
		if (const FString* Found = Names.Find(Key))
		{
			return *Found;
		}
		// 兜底：去掉 "Part." 前缀，便于新加部位时也不至于显示空
		FString S = Key;
		S.RemoveFromStart(TEXT("Part."));
		return S;
	}

	/** 部位血量比例 → 颜色：满血白、半血橙、濒危红 */
	FLinearColor PartHealthColor(float Ratio)
	{
		if (Ratio <= 0.f)
		{
			return FLinearColor(0.45f, 0.45f, 0.48f, 1.f);   // 已毁：灰
		}
		if (Ratio <= 0.34f)
		{
			return FLinearColor(1.00f, 0.32f, 0.24f, 1.f);   // 残血：红
		}
		if (Ratio <= 0.7f)
		{
			return FLinearColor(1.00f, 0.72f, 0.28f, 1.f);   // 半血：橙
		}
		return FLinearColor(0.92f, 0.96f, 1.00f, 1.f);       // 完好：白
	}
}

void ARobotPlayerController::PushDamageNumber(const FVector& WorldLocation,
	float Amount, const FGameplayTag& PartTag, bool bPartBreak,
	float ExposureMultiplier)
{
	// 上限保护：连发时一秒能打出 10+ 条，全部保留没有意义
	constexpr int32 MaxNumbers = 12;
	while (DamageNumbers.Num() >= MaxNumbers)
	{
		DamageNumbers.RemoveAt(0);
	}

	FDamageNumber N;
	N.World = WorldLocation;
	N.Age = 0.f;
	// 部位摧毁的那一发停留更久 —— 这是玩家最想看清的一条信息
	N.Life = bPartBreak ? 1.35f : 0.85f;
	N.bBig = bPartBreak;

	const int32 Rounded = FMath::Max(1, FMath::RoundToInt(Amount));
	const FString Part = PartShortName(PartTag);

	if (bPartBreak)
	{
		// 部位摧毁：字号最大 + 红橙，并且带上部位名
		N.Text = FText::FromString(Part.IsEmpty()
			? FString::Printf(TEXT("拆解  %d"), Rounded)
			: FString::Printf(TEXT("拆解 %s  %d"), *Part, Rounded));
		N.Color = FLinearColor(1.f, 0.42f, 0.18f, 1.f);
		++TotalPartBreaks;
	}
	else
	{
		// 普通命中：只显示数字（信息密度高，连发时不刷屏）
		//
		// 方向提示的阈值跟着 PartMapData 的默认倍率走：
		// 背面 2.0、侧面 1.6、正面 1.0。取中间值做分界，避免出现
		// "倍率刚好 1.55 就换了个词"的抖动。
		const TCHAR* Prefix = TEXT("");
		if (ExposureMultiplier >= 1.75f)
		{
			Prefix = TEXT("背击 ");
		}
		else if (ExposureMultiplier >= 1.3f)
		{
			Prefix = TEXT("侧击 ");
		}
		N.Text = FText::FromString(FString::Printf(TEXT("%s%d"), Prefix, Rounded));

		// 打核心用青色：让"打在核心上"和"打在挡板上"在余光里就能分开。
		// 背击/侧击用暖色：和"正面硬啃"在余光里也能分开。
		const bool bCore = PartTag == RobotTags::Part_Core();
		if (bCore)
		{
			N.Color = FLinearColor(1.f, 0.92f, 0.55f, 1.f);
		}
		else if (ExposureMultiplier >= 1.75f)
		{
			N.Color = FLinearColor(1.00f, 0.55f, 0.22f, 1.f);
		}
		else if (ExposureMultiplier >= 1.3f)
		{
			N.Color = FLinearColor(1.00f, 0.80f, 0.45f, 1.f);
		}
		else
		{
			N.Color = FLinearColor(0.95f, 0.97f, 1.f, 1.f);
		}
	}

	// 同一位置 0.35 秒内已有数字 → 横向错开，避免叠成一坨。
	// 部位摧毁居中置顶，普通命中数字左右交替散开。
	if (bPartBreak)
	{
		N.DriftX = 0.f;
		N.World.Z += 25.f;
	}
	else
	{
		N.DriftX = FMath::FRandRange(-16.f, 16.f);
		for (const FDamageNumber& Old : DamageNumbers)
		{
			if (Old.Age < 0.35f && FVector::DistSquared(Old.World, WorldLocation) < 50.f * 50.f)
			{
				N.DriftX = Old.DriftX >= 0.f ? -28.f : 28.f;
				break;
			}
		}
	}

	DamageNumbers.Add(N);
}

int32 ARobotPlayerController::GetDamageNumberCount() const
{
	return DamageNumbers.Num();
}

bool ARobotPlayerController::GetDamageNumber(int32 Index, FVector& OutWorld,
	FText& OutLabel, FLinearColor& OutColor, float& OutAlpha, bool& bOutBig, float& OutDriftX) const
{
	if (!DamageNumbers.IsValidIndex(Index))
	{
		return false;
	}
	const FDamageNumber& N = DamageNumbers[Index];
	const float T = FMath::Clamp(N.Age / FMath::Max(N.Life, 0.01f), 0.f, 1.f);

	OutWorld = N.World;
	OutLabel = N.Text;
	OutColor = N.Color;
	// 前 60% 保持不透明，后 40% 快速淡出 —— 数字要"看得清"，不要"一直挂着"
	OutAlpha = T < 0.6f ? 1.f : FMath::Square(1.f - (T - 0.6f) / 0.4f);
	bOutBig = N.bBig;
	OutDriftX = N.DriftX;
	return true;
}

int32 ARobotPlayerController::GetPartHintCount() const
{
	return PartHints.Num();
}

bool ARobotPlayerController::GetPartHint(int32 Index, FVector& OutWorld,
	FText& OutLabel, FLinearColor& OutColor) const
{
	if (!PartHints.IsValidIndex(Index))
	{
		return false;
	}
	const FPartHint& H = PartHints[Index];
	OutWorld = H.World;
	OutLabel = H.Label;
	OutColor = H.Color;
	return true;
}

void ARobotPlayerController::RefreshAimHint()
{
	PartHints.Reset();

	UWorld* W = GetWorld();
	ARobotCharacter* R = Cast<ARobotCharacter>(GetPawn());
	if (!W || !R || bMenuOpen || ModdingWidget.IsValid())
	{
		return;
	}

	FVector CamLoc;
	FRotator CamRot;
	GetPlayerViewPoint(CamLoc, CamRot);
	const FVector Dir = CamRot.Vector();

	// 从**相机**往外打一条射线：相机中心就是准心，
	// 命中哪个敌人就在它头顶标出"当前瞄的是哪个部位、还剩多少血"。
	FCollisionQueryParams Params(SCENE_QUERY_STAT(RobotAimHint), true, R);
	FHitResult Hit;
	if (!W->LineTraceSingleByChannel(Hit, CamLoc, CamLoc + Dir * 30000.f,
		ECC_Visibility, Params))
	{
		return;
	}

	ARobotEnemy* Enemy = Cast<ARobotEnemy>(Hit.GetActor());
	if (!Enemy)
	{
		return;
	}

	UPartDamageComponent* Parts = Enemy->GetPartDamage();
	if (!Parts || !Parts->PartMap)
	{
		return;
	}

	const FVector HeadTop = Enemy->GetActorLocation()
		+ FVector(0.f, 0.f, Enemy->GetSimpleCollisionHalfHeight() + 70.f);

	// 瘫痪目标：提示"不用再打了"
	if (Enemy->IsCoreDestroyed() || Enemy->IsDisabled())
	{
		FPartHint H;
		H.World = HeadTop;
		H.Label = FText::FromString(TEXT("已瘫痪  ·  可回收"));
		H.Color = FLinearColor(0.55f, 0.85f, 1.0f, 1.f);
		PartHints.Add(H);
		return;
	}

	// ── 命中点属于哪个部位 ──
	//
	// 弹丸撞的是胶囊（没有骨骼名），所以这里同样用"最近部位骨骼"反推。
	// 每个部位只用它的**主骨骼**（规则里的第一个前缀）参与距离竞争 ——
	// 用全部前缀会让"前臂/小腿"这些远端骨骼把近处关节挤掉，
	// 明明是躯干边缘却显示成"右臂"，读起来像 bug。
	const USkeletalMeshComponent* Skel =
		Enemy->FindComponentByClass<USkeletalMeshComponent>();
	if (!Skel)
	{
		return;
	}

	FName BestBone = NAME_None;
	float BestDistSq = TNumericLimits<float>::Max();
	for (const FPartBoneRule& Rule : Parts->PartMap->Rules)
	{
		if (Rule.BonePrefixes.Num() == 0)
		{
			continue;
		}
		for (int32 BoneIndex = 0; BoneIndex < Skel->GetNumBones(); ++BoneIndex)
		{
			const FName BoneName = Skel->GetBoneName(BoneIndex);
			if (!BoneName.ToString().StartsWith(Rule.BonePrefixes[0].ToString(),
					ESearchCase::IgnoreCase))
			{
				continue;
			}
			// 只考虑该部位的主骨骼层级：前缀完全相同的那一根 + 同前缀的子骨骼
			const float D = FVector::DistSquared(
				Skel->GetBoneLocation(BoneName, EBoneSpaces::WorldSpace),
				Hit.ImpactPoint);
			if (D < BestDistSq)
			{
				BestDistSq = D;
				BestBone = BoneName;
			}
			// 找到主骨骼就跳出内层循环（同一部位只取一次）
			break;
		}
	}

	const FGameplayTag Tag = BestBone.IsNone()
		? FGameplayTag() : Parts->PartMap->ResolvePartTag(BestBone);
	if (!Tag.IsValid())
	{
		return;
	}

	FPartHealth Health;
	if (!Parts->GetPartHealth(Tag, Health))
	{
		return;
	}

	const float Ratio = Health.GetRatio();
	FPartHint H;
	H.World = HeadTop;
	H.Label = FText::FromString(FString::Printf(TEXT("%s  %d%%"),
		*PartShortName(Tag), FMath::RoundToInt(Ratio * 100.f)));
	H.Color = PartHealthColor(Ratio);
	PartHints.Add(H);
}

void ARobotPlayerController::RefreshEnemyCount()
{
	UWorld* W = GetWorld();
	if (!W)
	{
		return;
	}

	int32 Count = 0;
	for (TActorIterator<ARobotEnemy> It(W); It; ++It)
	{
		// "还在场上"的判定：核心没被摧毁。核心一毁就是瘫痪/可回收状态，
		// 不再算威胁（与结算条件的口径保持一致）。
		if (!It->IsCoreDestroyed())
		{
			++Count;
		}
	}
	AliveEnemyCount = Count;
}

// ─────────────────────────────────────────────
// 结算画面
// ─────────────────────────────────────────────

void ARobotPlayerController::ShowEndScreen(bool bVictory, const FString& StatsText)
{
	if (EndWidget.IsValid())
	{
		return;
	}
	SAssignNew(EndWidget, SRobotEndScreen)
		.Owner(this)
		.bVictory(bVictory)
		.StatsText(StatsText);

	if (GEngine && GEngine->GameViewport)
	{
		// ZOrder 200：压在 HUD（10）之上
		GEngine->GameViewport->AddViewportWidgetContent(
			EndWidget.ToSharedRef(), 200);
	}

	// 输入切到 UI 并把键盘焦点给结算面板（回车重开靠它）。
	// 世界不暂停 —— 结算画面背后还能看到战场（敌人已全灭或玩家已瘫痪，
	// 不会有新的战斗行为）。
	FInputModeUIOnly Mode;
	Mode.SetWidgetToFocus(EndWidget);
	SetInputMode(Mode);
	bShowMouseCursor = true;

	UE_LOG(LogTemp, Warning, TEXT("[结算] %s | %s"),
		bVictory ? TEXT("任务完成") : TEXT("机体瘫痪"), *StatsText);
}

void ARobotPlayerController::RestartMission()
{
	if (EndWidget.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(
			EndWidget.ToSharedRef());
	}
	EndWidget.Reset();

	// 重开整关：重新加载关卡 = 敌人/玩家/掉落全部重置。
	// 垂直切片阶段这是最省事且不会漏状态的重开方式。
	ConsoleCommand(TEXT("RestartLevel"));
}

// ─────────────────────────────────────────────
// 改装台（M 键）
// ─────────────────────────────────────────────

namespace
{
	/** 槽位是否可以互相替代（左右臂/左右推进器/两个辅助槽视为同类） */
	bool SameSlotKind(EModuleSlot A, EModuleSlot B)
	{
		if (A == B)
		{
			return true;
		}
		auto In = [](EModuleSlot S, EModuleSlot X, EModuleSlot Y)
		{
			return S == X || S == Y;
		};
		if (In(A, EModuleSlot::ArmLeft, EModuleSlot::ArmRight)
			&& In(B, EModuleSlot::ArmLeft, EModuleSlot::ArmRight))
		{
			return true;
		}
		if (In(A, EModuleSlot::ThrusterLeft, EModuleSlot::ThrusterRight)
			&& In(B, EModuleSlot::ThrusterLeft, EModuleSlot::ThrusterRight))
		{
			return true;
		}
		if (In(A, EModuleSlot::Aux01, EModuleSlot::Aux02)
			&& In(B, EModuleSlot::Aux01, EModuleSlot::Aux02))
		{
			return true;
		}
		return false;
	}
}

bool ARobotPlayerController::IsModdingOpen() const
{
	return ModdingWidget.IsValid();
}

void ARobotPlayerController::ToggleModding()
{
	if (ModdingWidget.IsValid())
	{
		// 关闭：移除面板、恢复游戏输入
		if (GEngine && GEngine->GameViewport)
		{
			GEngine->GameViewport->RemoveViewportWidgetContent(
				ModdingWidget.ToSharedRef());
		}
		ModdingWidget.Reset();
		SetPause(false);
		SetInputMode(FInputModeGameOnly());
		bShowMouseCursor = false;
		return;
	}

	SAssignNew(ModdingWidget, SRobotModdingPanel).Owner(this);
	if (GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->AddViewportWidgetContent(
			ModdingWidget.ToSharedRef(), 150);
	}
	// 暂停世界 + UI 输入 + 光标：调装配时不挨打
	SetPause(true);
	FInputModeUIOnly Mode;
	Mode.SetWidgetToFocus(ModdingWidget);
	SetInputMode(Mode);
	bShowMouseCursor = true;
}

URobotModuleData* ARobotPlayerController::GetMountedModule(EModuleSlot Slot) const
{
	if (const ARobotCharacter* R = Cast<ARobotCharacter>(GetPawn()))
	{
		if (const UAssemblyComponent* A = R->GetAssembly())
		{
			return A->GetModule(Slot);
		}
	}
	return nullptr;
}

void ARobotPlayerController::CollectModuleCandidates(EModuleSlot Slot,
	TArray<URobotModuleData*>& Out) const
{
	Out.Reset();
	Out.Add(nullptr);   // 第一项永远是"空"（卸下）
	const FAssetRegistryModule& ARM =
		FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	FARFilter Filter;
	Filter.ClassPaths.Add(URobotModuleData::StaticClass()->GetClassPathName());
	Filter.bRecursiveClasses = true;
	TArray<FAssetData> Assets;
	ARM.Get().GetAssets(Filter, Assets);
	for (const FAssetData& AD : Assets)
	{
		if (URobotModuleData* M = Cast<URobotModuleData>(AD.GetAsset()))
		{
			if (SameSlotKind(M->TargetSlot, Slot))
			{
				Out.Add(M);
			}
		}
	}
	// 稳定排序：按资产名，避免每次打开面板顺序乱跳。
	//
	// ⚠️ 不能把 nullptr 放进待排序数组！TArray<指针>::Sort 的断言是通过
	//    TDereferenceWrapper 把元素**解引用后**传进来的（断言参数是对象引用），
	//    遇到空指针直接 EXCEPTION_ACCESS_VIOLATION（实测崩在 0x18）。
	//    所以：先剔除空项排序，再把"空"插回列表最前。
	TArray<URobotModuleData*> Sorted = Out;
	Sorted.Remove(nullptr);
	Sorted.Sort([](const URobotModuleData& A, const URobotModuleData& B)
	{
		return A.GetName() < B.GetName();
	});
	Out.Reset();
	Out.Add(nullptr);
	Out.Append(Sorted);
}

FString ARobotPlayerController::CycleModule(EModuleSlot Slot, int32 Direction)
{
	ARobotCharacter* R = Cast<ARobotCharacter>(GetPawn());
	UAssemblyComponent* A = R ? R->GetAssembly() : nullptr;
	if (!A)
	{
		return TEXT("没有可用的装配组件");
	}

	TArray<URobotModuleData*> Candidates;
	CollectModuleCandidates(Slot, Candidates);
	if (Candidates.Num() <= 1)
	{
		return TEXT("没有兼容这个槽位的模块");
	}

	URobotModuleData* Current = A->GetModule(Slot);
	int32 Cur = Candidates.IndexOfByKey(Current);
	if (Cur == INDEX_NONE)
	{
		Cur = 0;
	}
	const int32 N = Candidates.Num();
	const int32 Next = ((Cur + Direction) % N + N) % N;
	URobotModuleData* Target = Candidates[Next];

	// 空选项 = 卸下
	if (!Target)
	{
		A->UnmountModule(Slot);
		if (R->GetAbilitySystemComponent())
		{
			A->ApplyToAbilitySystem(R->GetAbilitySystemComponent());
		}
		return FString::Printf(TEXT("已卸下：%s"), *UEnum::GetDisplayValueAsText(Slot).ToString());
	}

	// 装配前检查（供电超载等会给出面向玩家的原因）
	FText Reason;
	if (!A->CanMount(Slot, Target, Reason))
	{
		return Reason.ToString();
	}

	A->MountModule(Slot, Target);
	if (R->GetAbilitySystemComponent())
	{
		A->ApplyToAbilitySystem(R->GetAbilitySystemComponent());
	}
	return FString::Printf(TEXT("已装配：%s"), *Target->DisplayName.ToString());
}

void ARobotPlayerController::CreateHUD()
{
	if (HUDWidget.IsValid() || !GEngine || !GEngine->GameViewport)
	{
		return;
	}

	// -NoHUD：纯美术/截图模式，完全不挂 HUD 与世界标记层。
	// 截图管线里 Slate 偶发整层重影，这条开关能保证出图绝对干净。
	if (FParse::Param(FCommandLine::Get(), TEXT("NoHUD")))
	{
		return;
	}

	SAssignNew(HUDWidget, SRobotHUD).Owner(this);
	GEngine->GameViewport->AddViewportWidgetContent(HUDWidget.ToSharedRef(), 10);

	// 世界标记（伤害数字/部位提示）单独一层，压在 HUD 之上、菜单之下。
	// ZOrder 15：HUD 是 10，改装台 150，菜单 100。
	SAssignNew(WorldMarkers, SRobotWorldMarkers).Owner(this);
	GEngine->GameViewport->AddViewportWidgetContent(WorldMarkers.ToSharedRef(), 15);

	UpdateHUDVisibility();
}

void ARobotPlayerController::UpdateHUDVisibility()
{
	// 观察者模式：常规 HUD（热量/电力/准星/伤害数字）全部隐藏 ——
	// 视角已脱离机甲，这些战斗读数没有意义；改由观察者 HUD 接管。
	const EVisibility Vis = (bMenuOpen || bObserverMode)
		? EVisibility::Collapsed : EVisibility::SelfHitTestInvisible;
	if (HUDWidget.IsValid())
	{
		// SelfHitTestInvisible：HUD 只是显示，不拦截鼠标点击
		HUDWidget->SetVisibility(Vis);
	}
	if (WorldMarkers.IsValid())
	{
		WorldMarkers->SetVisibility(Vis);
	}
}

// ═══════════════════════════════════════════════════════════════
// 观察者模式（第一百零七轮）
// ═══════════════════════════════════════════════════════════════

void ARobotPlayerController::ToggleObserver()
{
	if (bObserverMode) { ExitObserver(); }
	else { EnterObserver(); }
}

void ARobotPlayerController::EnterObserver()
{
	if (bObserverMode) { return; }
	// 菜单/改装台/结算开着时不允许进（它们在 UIOnly 输入模式 + 暂停世界）
	if (bMenuOpen || IsModdingOpen()) { return; }

	bObserverMode = true;

	// 起点：不要贴着玩家相机（出生点常怼在近景结构前，视野被挡）。
	// 从机甲位置往"背后 + 上方"拉开一段，微微俯视，进入时就能看到场景全貌。
	if (APawn* P = GetPawn())
	{
		const FVector PawnLoc = P->GetActorLocation();
		const FRotator PawnRot = P->GetActorRotation();
		const FVector Back = -FRotationMatrix(FRotator(0.f, PawnRot.Yaw, 0.f))
			.GetUnitAxis(EAxis::X);
		ObserverCamLoc = PawnLoc + Back * 900.f + FVector(0.f, 0.f, 520.f);
		// 朝向：回头看向机甲/场景中心
		ObserverCamRot = (PawnLoc + FVector(0.f, 0.f, 120.f) - ObserverCamLoc).Rotation();
	}
	else if (PlayerCameraManager)
	{
		ObserverCamLoc = PlayerCameraManager->GetCameraLocation();
		ObserverCamRot = PlayerCameraManager->GetCameraRotation();
	}
	if (ObserverCamLoc.IsNearlyZero())
	{
		ObserverCamLoc = FVector(-200.f, 0.f, 520.f);
		ObserverCamRot = FRotator(-12.f, 0.f, 0.f);
	}

	// 接管视角前关掉自动管理，否则任何 Possess 会把 ViewTarget 抢回 Pawn
	bAutoManageActiveCameraTarget = false;
	EnsureObserverCamera();

	// 输入：游戏模式 + 显示光标无所谓（我们直接读按键），隐藏光标更沉浸
	bObserverWasShowingCursor = bShowMouseCursor;
	bShowMouseCursor = false;
	SetInputMode(FInputModeGameOnly());

	CreateObserverHUD();
	UpdateHUDVisibility();

	// 机甲脱离控制仍留在场上，会被敌人打爆 —— 观察者期间免报废。
	// 伤害闸门在 PartDamageComponent::ApplyDamageToPart（所有伤害都汇聚到它）。
	SetMechInvulnerable(true);

	UE_LOG(LogTemp, Log, TEXT("[观察者] 进入自由飞行（V 返回）· 机甲免报废"));
}

void ARobotPlayerController::ExitObserver()
{
	if (!bObserverMode) { return; }
	bObserverMode = false;

	RemoveObserverHUD();

	// 归还视角：重新 Possess 当前 Pawn 即可让相机回到机甲第三人称。
	// bAutoManageActiveCameraTarget 设回 true，让引擎正常管理相机目标。
	bAutoManageActiveCameraTarget = true;
	if (APawn* P = GetPawn())
	{
		SetViewTarget(P);
	}
	if (bObserverWasShowingCursor)
	{
		bShowMouseCursor = true;
	}
	SetInputMode(FInputModeGameOnly());

	// 相机 Actor 留着不销毁（弱引用，下次进复用）；清掉引用让它自生自灭
	ObserverCamera.Reset();
	UpdateHUDVisibility();

	// 复位无敌：回到机甲后恢复正常受伤规则（这行不能漏，否则玩家永远无敌）
	SetMechInvulnerable(false);

	UE_LOG(LogTemp, Log, TEXT("[观察者] 返回机甲 · 恢复受伤"));
}

void ARobotPlayerController::SetMechInvulnerable(bool bEnable)
{
	// 只作用于玩家自己的机甲。观察者不改变敌人行为 —— 敌人照常互相无伤、
	// 照常被玩家打（玩家此时不开火，但逻辑保持干净）。
	if (ARobotCharacter* R = Cast<ARobotCharacter>(GetPawn()))
	{
		if (UPartDamageComponent* PD = R->GetPartDamage())
		{
			PD->SetInvulnerable(bEnable);
		}
	}
}

void ARobotPlayerController::EnsureObserverCamera()
{
	UWorld* W = GetWorld();
	if (!W) { return; }

	ACameraActor* Cam = ObserverCamera.Get();
	if (!Cam)
	{
		FActorSpawnParameters P;
		P.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Cam = W->SpawnActor<ACameraActor>(
			ACameraActor::StaticClass(), ObserverCamLoc, ObserverCamRot, P);
		if (!Cam)
		{
			UE_LOG(LogTemp, Warning, TEXT("[观察者] 相机创建失败"));
			return;
		}
		ObserverCamera = Cam;
		Cam->SetActorLabel(TEXT("ObserverCam"));
		if (UCameraComponent* C = Cam->GetCameraComponent())
		{
			C->bUsePawnControlRotation = false;
			C->SetFieldOfView(80.f);
		}
	}
	SetViewTarget(Cam);
}

void ARobotPlayerController::CreateObserverHUD()
{
	if (ObserverHUDWidget.IsValid() || !GEngine || !GEngine->GameViewport) { return; }
	// -NoHUD 纯截图模式下也不挂（与常规 HUD 一致）
	if (FParse::Param(FCommandLine::Get(), TEXT("NoHUD"))) { return; }

	SAssignNew(ObserverHUDWidget, SRobotObserverHUD).Owner(this);
	// Z=20：压在 HUD(10)/WorldMarkers(15) 之上，菜单(100)/改装台(150) 之下。
	GEngine->GameViewport->AddViewportWidgetContent(ObserverHUDWidget.ToSharedRef(), 20);
}

void ARobotPlayerController::RemoveObserverHUD()
{
	if (ObserverHUDWidget.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(ObserverHUDWidget.ToSharedRef());
	}
	ObserverHUDWidget.Reset();
}

void ARobotPlayerController::OnObserverScroll(float Value)
{
	if (bObserverMode)
	{
		ObserverScrollAccum += Value;
	}
}

void ARobotPlayerController::TickObserver(float DeltaSeconds)
{
	if (!bObserverMode) { return; }

	// ── 视角：鼠标增量 → 偏航/俯仰 ──
	float MX = 0.f, MY = 0.f;
	GetInputMouseDelta(MX, MY);
	if (!FMath::IsNearlyZero(MX) || !FMath::IsNearlyZero(MY))
	{
		const float Sens = 0.12f;
		ObserverCamRot.Yaw += MX * Sens;
		ObserverCamRot.Pitch = FMath::Clamp(
			ObserverCamRot.Pitch - MY * Sens, -89.f, 89.f);
		ObserverCamRot.Roll = 0.f;
	}

	// ── 滚轮：消费 OnObserverScroll 累计的轴值来调速 ──
	if (!FMath::IsNearlyZero(ObserverScrollAccum))
	{
		ObserverSpeed = FMath::Clamp(
			ObserverSpeed * (1.f + ObserverScrollAccum * 0.35f),
			150.f, 12000.f);
		ObserverScrollAccum = 0.f;
	}

	// ── 移动：WASD + QE 升降 + Shift 加速 ──
	const FRotator YawOnly(0.f, ObserverCamRot.Yaw, 0.f);
	const FVector Fwd = FRotationMatrix(YawOnly).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(YawOnly).GetUnitAxis(EAxis::Y);
	const FVector Up(0.f, 0.f, 1.f);

	FVector Move(0.f);
	if (IsInputKeyDown(EKeys::W)) { Move += Fwd; }
	if (IsInputKeyDown(EKeys::S)) { Move -= Fwd; }
	if (IsInputKeyDown(EKeys::D)) { Move += Right; }
	if (IsInputKeyDown(EKeys::A)) { Move -= Right; }
	if (IsInputKeyDown(EKeys::E)) { Move += Up; }
	if (IsInputKeyDown(EKeys::Q)) { Move -= Up; }

	float Speed = ObserverSpeed;
	if (IsInputKeyDown(EKeys::LeftShift) || IsInputKeyDown(EKeys::RightShift))
	{
		Speed *= 3.f;
	}
	if (!Move.IsNearlyZero())
	{
		ObserverCamLoc += Move.GetSafeNormal() * Speed * DeltaSeconds;
	}

	// ── 应用到相机 Actor + 每帧重申 ViewTarget ──
	if (ACameraActor* Cam = ObserverCamera.Get())
	{
		Cam->SetActorLocationAndRotation(ObserverCamLoc, ObserverCamRot,
			false, nullptr, ETeleportType::TeleportPhysics);
		if (GetViewTarget() != Cam)
		{
			bAutoManageActiveCameraTarget = false;
			SetViewTarget(Cam);
		}
	}
}

void ARobotPlayerController::FocusGameViewport()
{
	if (GEngine && GEngine->GameViewport &&
		GEngine->GameViewport->GetGameViewportWidget().IsValid())
	{
		FSlateApplication::Get().SetAllUserFocusToGameViewport();
	}
}

void ARobotPlayerController::ShowMainMenu()
{
	if (bMenuOpen)
	{
		return;
	}

	// 调试：跳过菜单直接开始，方便单独验证 HUD / 动画
	// 两种触发方式：命令行 -SkipMenu，或控制台变量 Robot.MenuDebug 1
	if (FParse::Param(FCommandLine::Get(), TEXT("SkipMenu")) ||
		CVarMenuDebug.GetValueOnGameThread() == 1)
	{
		UE_LOG(LogTemp, Warning, TEXT("[菜单] 跳过主菜单（调试开关）"));
		StartGame();
		return;
	}

	bMenuOpen = true;

	if (GEngine && GEngine->GameViewport)
	{
		SAssignNew(MenuWidget, SRobotMainMenu).Owner(this);
		GEngine->GameViewport->AddViewportWidgetContent(
			MenuWidget.ToSharedRef(), 100);
	}

	// 菜单期间：UI 输入模式 + 光标 + 暂停，避免玩家还在读菜单就被敌人打
	//
	// ⚠️ 必须把焦点交给菜单控件：只调 SetInputMode(UIOnly) 而不指定焦点时，
	//    键盘/手柄事件会落到 viewport 上，菜单控件的 OnKeyDown 收不到 ——
	//    手柄玩家会卡在菜单里进不去游戏。
	{
		FInputModeUIOnly Mode;
		if (MenuWidget.IsValid())
		{
			Mode.SetWidgetToFocus(MenuWidget);
		}
		SetInputMode(Mode);
	}
	bShowMouseCursor = true;
	SetPause(true);
	UpdateHUDVisibility();
	FocusGameViewport();

	UE_LOG(LogTemp, Warning, TEXT("[菜单] 主菜单已显示"));

}

void ARobotPlayerController::RemoveMenuFromViewport()
{
	if (MenuWidget.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(
			MenuWidget.ToSharedRef());
	}
	MenuWidget.Reset();
}

void ARobotPlayerController::StartGame()
{
	RemoveMenuFromViewport();
	bMenuOpen = false;

	SetPause(false);
	SetInputMode(FInputModeGameOnly());
	bShowMouseCursor = false;
	UpdateHUDVisibility();
	FocusGameViewport();

	UE_LOG(LogTemp, Warning, TEXT("[菜单] 开始游戏"));

	// 调试：带 -AutoShot 启动时自动连拍。
	// 用于无人值守地检查 HUD、程序化动画、敌人是否走过来。正式玩不带这个参数。
	if (FParse::Param(FCommandLine::Get(), TEXT("AutoShot")))
	{
		// 连拍 14 张、名义间隔 0.1 秒（实际由"上一张落盘"驱动，见 Tick）。
		// 一个步态周期约 0.6 秒，这样能把"抬腿 / 落地 / 换腿"几个关键姿态都拍下来，
		// 用来判断程序化走路动画到底哪里不对（单张图看不出来）。
		ShotBurstRemaining = 14;
		ShotBurstNextTime = GetWorld() ? GetWorld()->GetTimeSeconds() + 1.2f : 1.2f;
	}

	// 调试：-AutoQuit=<秒>
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("AutoQuit="), V))
		{
			AutoQuitAt = FCString::Atof(*V);
			UE_LOG(LogTemp, Warning, TEXT("[调试] 将在 %.1f 秒后自动退出"), AutoQuitAt);
		}
	}

	// 调试：-AutoShotAt=<秒> 在指定时刻补拍一张（结算画面等后期事件用它）。
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("AutoShotAt="), V))
		{
			AutoShotAt = FCString::Atof(*V);
			UE_LOG(LogTemp, Warning, TEXT("[调试] 将在 %.1f 秒补拍一张"), AutoShotAt);
		}
	}

	// 调试：-ShotEvery=<秒> 每 N 秒抓一张（世界时间从 0 开始算）
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("ShotEvery="), V))
		{
			ShotEverySeconds = FMath::Max(FCString::Atof(*V), 0.f);
			ShotEveryNextTime = ShotEverySeconds;
			UE_LOG(LogTemp, Warning, TEXT("[调试] 每 %.1f 秒抓一张图"),
				ShotEverySeconds);
		}
	}

	// 调试：-ModdingUI 无人值守驱动改装台
	//（3s 打开 → 5s/6s 各切一次头部槽 → 9s 关闭；截图 + 日志验证整条链路）
	//
	// ⚠️ 用 FTSTicker 而不是 Tick 驱动：改装台会 SetPause(true)（设计如此 ——
	//    调装配时不该挨打），而暂停后 Actor Tick 的恢复语义极其绕
	//    （bTickEvenWhenPaused + bShouldPerformFullTickWhenPaused 都设了
	//    仍然不跑）。核心 Ticker 跑在 GameThread 上、**不受世界暂停影响**，
	//    是验证"暂停状态 UI"唯一可靠的驱动方式。
	if (FParse::Param(FCommandLine::Get(), TEXT("ModdingUI")))
	{
		UE_LOG(LogTemp, Warning, TEXT("[调试] 3 秒后自动打开改装台"));
		TSharedRef<float> Elapsed = MakeShared<float>(0.f);
		TSharedRef<int32> Step = MakeShared<int32>(0);
		FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateLambda([this, Elapsed, Step](float Dt) -> bool
			{
				*Elapsed += Dt;
				const float E = *Elapsed;
				auto Adv = [&](int32 From) { return *Step == From; };

				if (Adv(0) && E >= 3.f)
				{
					ToggleModding();
					UE_LOG(LogTemp, Warning, TEXT("[改装调试] 打开改装台 → %s"),
						IsModdingOpen() ? TEXT("成功") : TEXT("失败"));
					++*Step;
				}
				else if (Adv(1) && E >= 5.f)
				{
					const FString Msg = CycleModule(EModuleSlot::Head, +1);
					UE_LOG(LogTemp, Warning, TEXT("[改装调试] 头部切换 → %s"), *Msg);
					++*Step;
				}
				else if (Adv(2) && E >= 6.f)
				{
					// 切一条武器臂 —— 验证"机体档位 × 武器臂乘数"真的生效
					// （面板的武器行会从基础值变到乘算后的值）
					const FString Msg = CycleModule(EModuleSlot::ArmLeft, +1);
					UE_LOG(LogTemp, Warning, TEXT("[改装调试] 左臂切换 → %s"), *Msg);
					++*Step;
				}
				else if (Adv(3) && E >= 8.f)
				{
					// 全部装配完成后抓图（面板显示的武器行应带乘数效果）。
					// ⚠️ 必须在这里（Ticker，按**真实时间**）抓，不能用
					// -AutoShotAt（世界时间在暂停时冻结，等世界时间到点
					// 面板早关了，拍到的只有游戏画面）。
					if (!FScreenshotRequest::IsScreenshotRequested())
					{
						CaptureShot(this);
						UE_LOG(LogTemp, Warning,
							TEXT("[改装调试] 面板内补拍一张（真实时间 %.1fs）"), E);
					}
					++*Step;
				}
				else if (Adv(4) && E >= 9.5f)
				{
					ToggleModding();
					UE_LOG(LogTemp, Warning, TEXT("[改装调试] 关闭改装台 → %s"),
						IsModdingOpen() ? TEXT("仍开着(异常)") : TEXT("成功"));
					++*Step;
					return false;   // 完成，注销 Ticker
				}
				return true;        // 继续
			}));
	}

	// 调试：带 -Probe 启动时，3 秒后从相机中心打一条射线，
	// 把命中的 Actor/组件/材质打进日志 —— 用来定位画面里的可疑物体。
	if (FParse::Param(FCommandLine::Get(), TEXT("Probe")))
	{
		FTSTicker::GetCoreTicker().AddTicker(
			FTickerDelegate::CreateLambda([this](float) -> bool
			{
				ProbeCenterView(this);
				return false;
			}), 3.0f);
	}
}

void ARobotPlayerController::QuitGameNow()
{
	UE_LOG(LogTemp, Warning, TEXT("[菜单] 退出游戏"));
	ConsoleCommand(TEXT("quit"));
}

FString ARobotPlayerController::ApplyDisplaySettings(const FIntPoint& Resolution,
	int32 WindowModeIndex, int32 QualityIndex)
{
	UGameUserSettings* Settings = GEngine ? GEngine->GetGameUserSettings() : nullptr;
	if (!Settings)
	{
		return TEXT("无法访问显示设置（GameUserSettings 为空）");
	}

	const EWindowMode::Type Mode =
		(EWindowMode::Type)FMath::Clamp(WindowModeIndex, 0, 2);
	const int32 Quality = FMath::Clamp(QualityIndex, 0, 3);

	// 顺序有讲究：先切显示模式，再设分辨率。
	// 反过来在独占全屏下会因为"分辨率不在该模式的合法列表里"被静默忽略。
	Settings->SetFullscreenMode(Mode);
	if (Resolution.X > 0 && Resolution.Y > 0)
	{
		Settings->SetScreenResolution(Resolution);
	}
	Settings->SetOverallScalabilityLevel(Quality);
	Settings->ApplySettings(false);
	Settings->SaveSettings();

	// 应用后确认一次真实生效的值，别只报"我以为设成了什么"
	const FIntPoint Now = Settings->GetScreenResolution();
	const FString Result = FString::Printf(
		TEXT("已应用：%d × %d  ·  %s  ·  画质 %s"),
		Now.X, Now.Y, *WindowModeName(Settings->GetFullscreenMode()),
		*QualityName(Settings->GetOverallScalabilityLevel()));

	UE_LOG(LogTemp, Warning, TEXT("[菜单] %s"), *Result);
	return Result;
}
