// 敌人机体 —— 与玩家共用同一套部位伤害系统
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AbilitySystemInterface.h"
// TMap<FGameplayTag, int32> 需要 FGameplayTag 的完整定义 ——
// 缺这个 include 会在 TMap 的 GetTypeHash 处报「不完整类型」。
#include "GameplayTagContainer.h"
#include "MechProceduralAnim.h"
#include "RobotEnemy.generated.h"

class UAbilitySystemComponent;
class URobotAttributeSet;
class UPartDamageComponent;
class UPartMapData;
class ARobotProjectile;

/**
 * 敌人机体。
 *
 * 架构要点：它挂的是与玩家**完全相同**的 UPartDamageComponent，
 * 只是换了一张 UPartMapData。这就是"一套代码通吃敌我"的落点 ——
 * 打腿会瘸、打臂会失去攻击能力，对敌我都成立。
 *
 * AI 用简单的 C++ 状态机而不是 StateTree：StateTree 需要额外的资产，
 * 而垂直切片阶段先用能跑起来的实现。生产阶段再迁移，行为逻辑不变。
 */
UCLASS()
class ROBOTGAME_API ARobotEnemy : public ACharacter, public IAbilitySystemInterface
{
	GENERATED_BODY()

public:
	ARobotEnemy();

	virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override;

	UFUNCTION(BlueprintPure, Category = "Robot|Enemy")
	UPartDamageComponent* GetPartDamage() const { return PartDamage; }

	/** 核心是否被摧毁（HUD 残敌计数 / 关卡结算判定用） */
	UFUNCTION(BlueprintPure, Category = "Robot|Enemy")
	bool IsCoreDestroyed() const;

	/** 是否已瘫痪（核心被毁，或功能部位尽失） */
	UFUNCTION(BlueprintPure, Category = "Robot|Enemy")
	bool IsDisabled() const { return bDisabled; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	// ── 行为查询（部位状态直接改变行为，这是"拆解有策略"的落点）──

	/** 还有武器臂吗？没有则无法攻击。 */
	UFUNCTION(BlueprintPure, Category = "Robot|Enemy")
	bool HasAliveWeaponArm() const;

	/** 存活推进器数量 0—2。0 则无法移动，1 则半速。 */
	UFUNCTION(BlueprintPure, Category = "Robot|Enemy")
	int32 GetAliveThrusterCount() const;

	/** 进入瘫痪状态：停止移动与攻击 */
	void EnterDisabledState();

	UFUNCTION()
	void HandlePartDestroyed(FGameplayTag PartTag);

	UFUNCTION()
	void HandleActorDisabled();

	/** 尝试朝目标开火 */
	void TryAttack(AActor* Target);

	/**
	 * 目标胸口是否在视线内。
	 *
	 * 为什么需要：敌人原本隔着掩体也会开火 —— 子弹打在墙上，但枪口闪光、
	 * 音效、后坐动画全在演，玩家读到的是"这游戏在乱打"。有视线判断之后，
	 * "躲到掩体后面"才真的能让敌人停火，掩体才有意义。
	 *
	 * @param OutBlocker 可选：返回挡住视线的 Actor/组件名，用于诊断"为什么不开火"。
	 */
	bool HasLineOfSightTo(const AActor* Target, FString* OutBlocker = nullptr) const;

	/**
	 * 给这个敌人套上骨骼网格并让脚底贴地。
	 *
	 * 为什么在 C++ 里按路径加载、而不是用 UPROPERTY 配数组：
	 * BP_Enemy 是脚本创建的，它把 MeshVariants 这类 EditDefaultsOnly 数组
	 * 以"空数组"的形式序列化过 —— 蓝图 CDO 的值会覆盖 C++ 构造函数里填好的值
	 * （输入对象那次就是栽在同一个坑上）。走 LoadObject + 字面路径最稳。
	 */
	void ApplyMeshVariant();

	/** 解析要用的外观变体索引：显式指定优先，否则按 Actor 名字里的数字取 */
	int32 ResolveVariantIndex() const;

	/** 按当前外观重建程序化动画网格（可见网格 + 基准姿势缓存） */
	void RefreshAnimMesh();

	// ── 程序化动画（项目里没有动画资产，见 MechProceduralAnim.h）──

	UPROPERTY()
	TObjectPtr<class UPoseableMeshComponent> AnimMesh;

	FMechAnimState AnimState;

	// ── 组件 ──

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Enemy")
	TObjectPtr<UAbilitySystemComponent> AbilitySystemComponent;

	UPROPERTY()
	TObjectPtr<URobotAttributeSet> AttributeSet;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Enemy")
	TObjectPtr<UPartDamageComponent> PartDamage;

	// ── 配置 ──

	/** 部位映射表。不同敌人配不同的表。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy")
	TObjectPtr<UPartMapData> PartMap;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy")
	TSubclassOf<ARobotProjectile> ProjectileClass;

	/** 部位被拆解时掉落的回收物类。留空则不掉落。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy")
	TSubclassOf<class ASalvagePickup> SalvageClass;

	/** 部位标签 → 掉落价值。核心最高，躯干不掉落。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy")
	TMap<FGameplayTag, int32> SalvageValues;

	/** 基础移动速度（推进器全存活时） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy", meta = (ClampMin = "0"))
	// 敌机比玩家快会拉开错觉：260cm/s 对腿长约 104cm 的机体来说太快，
	// 步幅被 StrideMax 截断 → 提高步频但腿来不及摆，表现为"脚乱蹬、身体平移"。
	// 按腿长把速度限制在"步幅不超过腿长 0.6×"的范围内（见 ApplyMeshVariant 末尾）。
	float BaseMoveSpeed = 260.f;

	/** 进入攻击距离的阈值（cm） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy", meta = (ClampMin = "0"))
	float AttackRange = 900.f;

	/** 超出这个距离就放弃追击 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy", meta = (ClampMin = "0"))
	float LoseTargetRange = 3000.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy", meta = (ClampMin = "0"))
	float AttackInterval = 1.35f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy", meta = (ClampMin = "0"))
	float AttackDamage = 7.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy")
	float ProjectileSpeed = 1600.f;

	/**
	 * 敌方射击散布（半角，度）。
	 *
	 * 为什么必须有：之前敌人是"激光炮"—— 从胸口精确瞄准玩家的胸口，
	 * 远距离也弹无虚发。多个敌人同时开火时玩家几乎没有操作空间，
	 * 而且没有对射的紧张感。给一个固定散布后：
	 *   · 远距离命中率自然下降（距离越远，同样角度偏差的横向偏移越大）；
	 *   · 玩家移动/冲刺可以"甩弹"，操作有正反馈；
	 *   · 弹道可见（有枪口闪光和飞行弹体），可以看着弹道躲。
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy", meta = (ClampMin = "0"))
	float AttackSpreadDegrees = 2.4f;

	// ── 战术走位 ──

	/**
	 * 环绕半径带（相对 AttackRange）。
	 *
	 * 敌人不该只是"走到射程内站定开火"—— 那会让玩家永远只看到正面装甲，
	 * 新加的"背/侧方向伤害加成"就永远用不上。这里让敌人在射程内绕着玩家转，
	 * 并优先朝玩家的背后绕。太远（> Outer）就边绕边压上，太近（< Inner）边打边退。
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics", meta = (ClampMin = "0.1", ClampMax = "1.5"))
	float StrafeInnerRatio = 0.55f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics", meta = (ClampMin = "0.2", ClampMax = "2.0"))
	float StrafeOuterRatio = 0.95f;

	/** 切向速度权重。越大越像"绕圈"，越小越像"正面顶上来"。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics", meta = (ClampMin = "0"))
	float StrafeWeight = 1.0f;

	/** 换向间隔（秒）。太短会左右抽搐，太长会绕成一段直线。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics", meta = (ClampMin = "0.5"))
	float StrafeFlipMin = 2.2f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics", meta = (ClampMin = "0.5"))
	float StrafeFlipMax = 4.0f;

	/** 是否要求有视线才开火（关掉仅用于调试/录制）。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics")
	bool bRequireLineOfSight = true;

	/**
	 * 绕后手（flanker）在变体里占的比例：变体序号 % 3 == 0 的敌人绕后，
	 * 其余当"压制手"——不刻意绕背，随机换向。
	 *
	 * 为什么需要分工：如果五个敌人全都往玩家背后绕，玩家会面对一个空屏幕
	 * 被五个看不见的敌人集火。让一部分敌人留在正面/侧面当"可见威胁"，
	 * 玩家才知道该先打谁；背后的枪声也才有意义（有人在绕，有人在压）。
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics", meta = (ClampMin = "1"))
	int32 FlankerRoleModulo = 3;

	/** 只剩一条腿时的散布惩罚倍率：站不稳，打不准。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Enemy|Tactics", meta = (ClampMin = "1"))
	float LameSpreadScale = 1.6f;

	/** 显式指定外观变体索引。小于 0 表示按 Actor 名字里的数字自动挑。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Enemy")
	int32 MeshVariantIndex = -1;

	/**
	 * 统一缩放。<= 0 表示"用外观表里预设的缩放"。
	 *
	 * 默认必须是 0 而不是 1：如果默认 1，就分不清"没设置"和"显式设成 1"，
	 * Colossus 的预设 0.5 会被这个默认值吃掉（实测踩过）。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Enemy")
	float MeshScale = 0.f;

	/** 悬浮机（巡逻机）：没有腿，程序化步态与可见腿骨都要关掉。由 ApplyMeshVariant 按外观定义写入。 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Enemy")
	bool bHoverMech = false;

	/** 调试 -EnemyInPlace：位置锁定，但用合成速度驱动步态（拍步态用）。 */
	UPROPERTY()
	bool bDebugInPlace = false;

	/** -EnemyInPlace 下合成的速度，每帧喂给动画。 */
	FVector DebugSynthVel = FVector::ZeroVector;

	/** -EnemyInPlace 下锁定的位置。 */
	FVector LockedLocation = FVector::ZeroVector;

	/** -EnemyWalkConst：每实例的固定推进速度与初始化标志（绝不能跨实例共享）。 */
	FVector WalkConstVel = FVector::ZeroVector;
	bool bWalkConstInit = false;

	/** 调试 -BreakLeg=<L|R>：出生时打断指定腿（验证独腿支撑补偿）。 */
	FString DebugBreakLeg;

	/** BeginPlay 中延后到 SetPartMap 之后应用断腿参数。 */
	FString PendingBreakLeg;

	/** -EnemyInPlaceIndex：只有该外观序号的敌人原地不动。 */
	int32 DebugInPlaceIndex = INDEX_NONE;

	/** 双腿全断后已收缩碰撞胶囊（避免每帧重复设置）。 */
	bool bCapsuleShrunk = false;

	/** 第一帧之后已按腿长修正过行走速度。 */
	bool bLegSpeedAdjusted = false;

	/** -DebugAim 上次打印时间。 */
	float DebugAimLastLog = -100.f;
	/** -DebugFoot 的日志节流（每实例，不能写函数内 static） */
	float DebugFootLastLog = -100.f;

	/** 上次开火时记录的目标速度，用于估算机动剧烈程度（急停/变向 → 缩短前置量）。 */
	FVector LastAimTargetVel = FVector::ZeroVector;
	float LastAimTime = -100.f;

	/** 四足机（运输机/巨像）：骨骼里有 thigh_BL 骨。 */
	bool IsQuadruped() const;

private:
	UPROPERTY()
	TObjectPtr<AActor> CurrentTarget;

	/** 出生点（掉出地图时拉回用，见 Tick） */
	FVector HomeLocation = FVector::ZeroVector;

	bool bDisabled = false;
	float AttackTimer = 0.f;
	float RepathTimer = 0.f;

	// ── 战术状态 ──

	/** 当前环绕方向：+1 逆时针（从上看），-1 顺时针 */
	int32 StrafeSign = 1;

	/** true = 绕后手（追玩家背后）；false = 压制手（随机换向，留在视野里） */
	bool bFlanker = false;

	/** 距离下次换向还有多久 */
	float StrafeFlipTimer = 0.f;

	/** 缓存视线结果，避免每帧做射线 */
	bool bHasLineOfSight = true;
	float LOSCheckTimer = 0.f;

	/** 视线去抖：连续多久保持"另一种结果"，够久才切换（掩体边缘会抖动） */
	float LOSPendingTime = 0.f;

	/** 瘫痪后的火花抽搐计时器 */
	float DisabledSparkTimer = 0.f;

	/** 上一次记录的走位状态，只在切换时打日志（避免刷屏） */
	int32 LastLoggedStrafeSign = 0;
	bool bLastLoggedLOS = true;
};
