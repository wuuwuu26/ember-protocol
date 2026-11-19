// 玩家控制器 —— 主菜单与 HUD 的宿主
//
// 为什么单独建一个控制器类：菜单和 HUD 需要有个"生命周期明确"的宿主
// （BeginPlay 建、EndPlay 拆），挂在角色身上会让职责混乱。
// 控制器类在 GameMode 的构造函数里指定 —— 构造函数一定会跑，
// 不像 BeginPlay 会被蓝图的事件节点干扰。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "RobotTypes.h"
#include "RobotPlayerController.generated.h"

	class SRobotMainMenu;
	class SRobotHUD;
	class SRobotModdingPanel;
	class SRobotObserverHUD;

UCLASS()
class ROBOTGAME_API ARobotPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ARobotPlayerController();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupInputComponent() override;

	/** 显示主菜单：切 UI 输入模式、显示光标、暂停游戏 */
	void ShowMainMenu();

	/** 开始游戏：移除菜单、恢复游戏输入、取消暂停 */
	void StartGame();

	/** 主菜单是否还开着 */
	bool IsMenuOpen() const { return bMenuOpen; }

	/**
	 * 应用显示设置。返回一行给玩家看的结果文本（成功或失败原因）。
	 * 参数：目标分辨率、显示模式索引（0=全屏 1=无边框 2=窗口化）、画质档位 0—3。
	 */
	FString ApplyDisplaySettings(const FIntPoint& Resolution,
		int32 WindowModeIndex, int32 QualityIndex);

	/** 退出游戏 */
	void QuitGameNow();

	/** 显示结算画面（胜利/失败）。GameMode 判定后调用。 */
	void ShowEndScreen(bool bVictory, const FString& StatsText);

	/** 从结算画面重新开始（结算面板按回车触发） */
	void RestartMission();

	// ── 改装台（M 键）──

	/** 打开/关闭改装台（打开时暂停世界、切 UI 输入） */
	void ToggleModding();

	/** 改装台是否开着 */
	bool IsModdingOpen() const;

	/**
	 * 在槽位里循环切换模块（面板上的 &lt; &gt; 按钮与调试路径共用）。
	 * 返回一行给玩家看的结果（已装配 / 失败原因）。
	 */
	FString CycleModule(EModuleSlot Slot, int32 Direction);

	/** 收集某槽位全部候选模块（含空选项 nullptr 在最前） */
	void CollectModuleCandidates(EModuleSlot Slot,
		TArray<class URobotModuleData*>& Out) const;

	/** 槽位当前挂载的模块（无则 nullptr） */
	class URobotModuleData* GetMountedModule(EModuleSlot Slot) const;

	// ── 战斗反馈（HUD 每帧拉取，事件只记时间戳）──

	/** 玩家命中敌人（弹丸命中后调用）。bKilled = 这一击摧毁了核心。
	 *  WorldLocation = 命中点（伤害数字从这里往上飘）。 */
	void NotifyHitConfirmed(bool bKilled, const FVector& WorldLocation = FVector::ZeroVector);

	/**
	 * 追加一条伤害数字。由弹丸在"造成实际伤害"之后调用 ——
	 * 部位完全摧毁后的溢出伤害不弹数字（那会误导玩家以为还在掉血）。
	 *
	 * @param ExposureMultiplier 这一发的方向倍率（正面 1.0 / 侧面 / 背面）。
	 *        倍率已经体现在 Amount 里，这里只用来加"侧击/背击"的提示 ——
	 *        光看到数字变大，玩家会以为是随机浮动；标出方向才学得会绕后。
	 */
	void PushDamageNumber(const FVector& WorldLocation, float Amount,
		const FGameplayTag& PartTag, bool bPartBreak,
		float ExposureMultiplier = 1.f);

	/** 伤害数字数量 / 第 i 条的数据。供 SRobotWorldMarkers 每帧拉取。 */
	int32 GetDamageNumberCount() const;
	bool GetDamageNumber(int32 Index, FVector& OutWorld, FText& OutLabel,
		FLinearColor& OutColor, float& OutAlpha, bool& bOutBig, float& OutDriftX) const;

	/**
	 * 部位易伤提示：准心指着敌机时，在它上方显示当前瞄准部位的血量。
	 *
	 * 为什么要做：游戏的核心是"打部位"，但玩家在开打之前**无法判断**
	 * 哪条腿还剩多少血、下一枪该不该换目标。只靠命中时的伤害数字是事后信息，
	 * 而"打哪里"需要事前信息。这个提示把"拆解策略"从猜测变成决策。
	 */
	int32 GetPartHintCount() const;
	bool GetPartHint(int32 Index, FVector& OutWorld, FText& OutLabel,
		FLinearColor& OutColor) const;

	/** 关卡开始到现在命中的总次数（结算用） */
	int32 GetHitCount() const { return TotalHits; }
	/** 部位摧毁次数（结算用） */
	int32 GetPartBreakCount() const { return TotalPartBreaks; }

	/** 玩家部位受伤（角色受击回调里调用） */
	void NotifyPlayerDamaged();

	/** 距上次"命中确认"的秒数；从未命中返回一个很大的值 */
	float GetHitMarkerAge() const;
	/** 上次命中是否打掉了核心（决定命中标记的颜色） */
	bool WasLastHitKill() const { return bLastHitWasKill; }

	/** 距上次"玩家受伤"的秒数；从未受伤返回一个很大的值 */
	float GetDamageFlashAge() const;

	/** 当前存活敌人数（0.5 秒缓存，HUD 每帧调用也不贵） */
	int32 GetAliveEnemyCount() const;

	// ── 观察者模式（第一百零七轮）──
	//
	// 按 V 切换：脱离机甲，进入自由飞行观察相机，绕着场景看。
	// 相机自管（独立 ACameraActor + SetViewTarget），移动/转向在 Tick 里
	// 直接读按键驱动 —— 不挂 Character 的 EnhancedInput（避免 FInputModeUIOnly
	// 与 Possess 抢视角的耦合），也不冻结世界（Menu/Modding 才暂停）。

	/** 进入/退出观察者模式 */
	void ToggleObserver();
	/** 强制设定观察者模式（供 -Observer 启动参数 / 控制台用） */
	void EnterObserver();
	void ExitObserver();
	/** 是否处于观察者模式 */
	bool IsObserverMode() const { return bObserverMode; }

	/** 供观察者 HUD 每帧拉取的遥测 */
	FVector GetObserverLocation() const { return ObserverCamLoc; }
	FRotator GetObserverRotation() const { return ObserverCamRot; }
	float GetObserverSpeed() const { return ObserverSpeed; }

	/** 世界标记（伤害数字）的宿主控件。HUD 创建时一起建出来。 */
	TSharedPtr<class SRobotWorldMarkers> WorldMarkers;

private:
	void RemoveMenuFromViewport();
	void FocusGameViewport();

	/** 建立游戏内 HUD（开局后就一直在，菜单打开时隐藏） */
	void CreateHUD();

	/** 按"菜单是否打开"同步 HUD 的可见性 */
	void UpdateHUDVisibility();

	// ── 观察者模式内部 ──
	/** 每帧推进自由飞行相机（只在观察者模式下跑） */
	void TickObserver(float DeltaSeconds);
	/** 滚轮调速回调（BindAxisKey 每帧给轴值） */
	void OnObserverScroll(float Value);
	/** 建立/移除观察者 HUD 覆盖层 */
	void CreateObserverHUD();
	void RemoveObserverHUD();
	/** 确保观察者相机 Actor 存在，并把 ViewTarget 指过去 */
	void EnsureObserverCamera();
	/** 给玩家机甲的 PartDamage 设运行时无敌（观察者模式免报废） */
	void SetMechInvulnerable(bool bEnable);

	bool bObserverMode = false;
	/** -Observer 启动参数：延到首帧 Tick 再进观察者 */
	bool bObserverPending = false;
	TWeakObjectPtr<class ACameraActor> ObserverCamera;
	FVector ObserverCamLoc = FVector::ZeroVector;
	FRotator ObserverCamRot = FRotator::ZeroRotator;
	/** 当前移动速度（cm/s），滚轮调 */
	float ObserverSpeed = 1200.f;
	/** 滚轮轴当帧累计（OnObserverScroll 写、TickObserver 消费清零） */
	float ObserverScrollAccum = 0.f;
	TSharedPtr<SRobotObserverHUD> ObserverHUDWidget;
	/** 记录进入前的输入模式，退出时恢复 */
	bool bObserverWasShowingCursor = false;

	/** 重新统计存活敌人（Timer 驱动，0.5 秒一次） */
	void RefreshEnemyCount();

	/** 刷新"准心指着哪个敌人、哪个部位"的提示（0.1 秒一次） */
	void RefreshAimHint();

	/** 一条伤害数字 */
	struct FDamageNumber
	{
		FVector World = FVector::ZeroVector;
		FText Text;
		FLinearColor Color = FLinearColor::White;
		float Age = 0.f;
		float Life = 0.9f;
		bool bBig = false;
		/** 同一位置连续命中时的横向错开量（避免数字叠在一起看不清） */
		float DriftX = 0.f;
	};

	/** 一条部位提示 */
	struct FPartHint
	{
		FVector World = FVector::ZeroVector;
		FText Label;
		FLinearColor Color = FLinearColor::White;
	};

	TArray<FDamageNumber> DamageNumbers;
	TArray<FPartHint> PartHints;
	float PartHintNextRefresh = 0.f;

	int32 TotalHits = 0;
	int32 TotalPartBreaks = 0;

	TSharedPtr<SRobotMainMenu> MenuWidget;
	TSharedPtr<SRobotHUD> HUDWidget;
	TSharedPtr<class SRobotEndScreen> EndWidget;
	TSharedPtr<class SRobotModdingPanel> ModdingWidget;
	bool bMenuOpen = false;

	// 战斗反馈时间戳（世界秒）。用 -1e9 表示"从未发生"。
	float HitMarkerTime = -1e9f;
	bool bLastHitWasKill = false;
	float DamageFlashTime = -1e9f;

	int32 AliveEnemyCount = 0;
	float EnemyCountNextRefresh = 0.f;

	// ── 调试：-AutoShot 连拍 ──
	//
	// 原来是用 5 个定时器在 0.12 秒间隔各请求一次截图，结果只落盘 2 张 ——
	// UE 的 FScreenshotRequest 同一时刻只允许一个挂起请求，
	// 而 1.6MB 的 PNG 写盘要花掉几百毫秒，后面几个请求全被丢掉了。
	// 改成"上一张写完后才请求下一张"，保证每一帧都真的落盘。
	int32 ShotBurstRemaining = 0;
	float ShotBurstNextTime = 0.f;

	/**
	 * 调试：-ShotEvery=<秒> 每 N 秒抓一张图（无人值守做视觉验收用）。
	 * 世界时间驱动 —— 和 -AutoShot / -AutoShotAt 用同一套"上一张落盘才发下一张"的节流。
	 */
	float ShotEverySeconds = 0.f;
	float ShotEveryNextTime = 0.f;

	/** 调试：-AutoQuit=<秒> 的到点时间（世界秒）。<=0 表示不启用。 */
	float AutoQuitAt = -1.f;

	/** 调试：-AutoShotAt=<秒> 在指定时刻补一张截图（用来拍结算画面）。 */
	float AutoShotAt = -1.f;
	bool bAutoShotAtDone = false;
};
