// 部位伤害系统 —— 游戏最核心的战斗机制
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameplayTagContainer.h"
#include "RobotTypes.h"
// FPartBoneRule 在 HandlePartDestruction 的签名里按值/引用使用，
// 只前置声明不够（USTRUCT 需要完整定义），必须 include。
#include "PartMapData.h"
#include "PartDamageComponent.generated.h"

class UPartMapData;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnPartDamaged,
	FGameplayTag, PartTag, float, RemainingRatio);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPartDestroyed, FGameplayTag, PartTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnActorDisabled);

/**
 * 部位血量组件。挂在玩家与所有敌人身上。
 *
 * 为什么部位 HP 不放进 GAS AttributeSet：
 * 部位数量是动态的（不同敌人部位数不同），AttributeSet 适合固定属性。
 * 这里用独立组件管理，GAS 只负责通过 GameplayEffect 把伤害投递进来。
 *
 * 拆解表现用"假拆解"：隐藏骨骼 + 生成预制备件模型，
 * 而不是 Chaos 逐块碎裂 —— 碎块不可控，且无法稳定作为可拾取物。
 */
UCLASS(ClassGroup = (Robot), meta = (BlueprintSpawnableComponent))
class ROBOTCOMBAT_API UPartDamageComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPartDamageComponent();

	/** 部位映射表。不同敌人配不同的表，一套代码通吃敌我。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Robot|Parts")
	TObjectPtr<UPartMapData> PartMap;

	/** 可选的具名单位标记：核心存活但四肢尽毁时进入"可修复"状态 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Robot|Parts")
	bool bIsCompanionCandidate = false;

	/**
	 * PartMap 为空时是否用代码里的默认规则兜底。
	 *
	 * 兜底很必要：脚本创建数据资产时如果失败（或忘了配），部位系统会静默失效 ——
	 * 打哪都不掉血，而且不报错。有这个开关至少能跑起来并打出日志。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Robot|Parts")
	bool bBuildDefaultsIfNoMap = true;

	/** 兜底时用哪套骨架命名。true = 玩家骨架（torso 兼任核心），false = 敌人骨架。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Robot|Parts")
	bool bUsePlayerRigDefaults = false;

	// ── 事件 ──
	UPROPERTY(BlueprintAssignable, Category = "Robot|Parts")
	FOnPartDamaged OnPartDamaged;

	UPROPERTY(BlueprintAssignable, Category = "Robot|Parts")
	FOnPartDestroyed OnPartDestroyed;

	/** 核心被毁 / 全部功能部位失效 */
	UPROPERTY(BlueprintAssignable, Category = "Robot|Parts")
	FOnActorDisabled OnActorDisabled;

	// ── 查询 ──

	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	bool GetPartHealth(const FGameplayTag& PartTag, FPartHealth& OutHealth) const;

	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	float GetPartRatio(const FGameplayTag& PartTag) const;

	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	bool IsPartDestroyed(const FGameplayTag& PartTag) const;

	/** 核心是否已被摧毁 */
	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	bool IsCoreDestroyed() const;

	/** 是否处于"可修复/可招募"窗口：核心存活，但功能部位基本失效 */
	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	bool IsRepairable() const;

	/**
	 * 运行时无敌开关（第一百零八轮）。
	 *
	 * 用途：观察者模式下机甲脱离控制仍留在场上，会被敌人打爆 ——
	 * 进入观察者时给玩家的部位组件设 true，退出设回 false。
	 * 与启动期 -GodMode 的区别：这个能运行时动态开关，且只作用于
	 * 被设置的那个组件实例（敌人不受影响）。
	 *
	 * 拦截点在设计上是唯一的：所有伤害最终都汇聚到 ApplyDamageToPart()
	 * （ApplyDamageByBone / ApplyDamageByBoneEx 都调它），在那里 return 即可。
	 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Parts")
	void SetInvulnerable(bool bEnable) { bInvulnerable = bEnable; }

	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	bool IsInvulnerable() const { return bInvulnerable; }

	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	int32 GetAlivePartCount() const;

	// ── 伤害入口 ──

	/**
	 * 按骨骼名施加伤害。命中检测拿到骨骼名后调这个，
	 * 内部负责翻译成部位标签。
	 *
	 * @return 实际造成伤害的部位标签；未命中任何部位时返回无效 Tag
	 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Parts")
	FGameplayTag ApplyDamageByBone(FName BoneName, float Damage);

	/** 直接按部位标签施加伤害 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Parts")
	void ApplyDamageToPart(const FGameplayTag& PartTag, float Damage);

	/**
	 * 施加伤害并报告"实际发生了什么" —— 给 UI 用（伤害数字 / 部位摧毁提示）。
	 *
	 * 为什么要单独一个接口：部位已毁时 ApplyDamageToPart 会静默忽略，
	 * 但如果 UI 只按"发射了就弹数字"，玩家会以为"打腿还有用"——
	 * 实际上早就没收益了，视觉反馈必须和规则一致。
	 *
	 * @param OutTaken        实际扣除的血量（部位已毁时为 0）
	 * @param bOutBrokePart   这一击是否把该部位打到 0（用于放大数字）
	 * @param bOutCoreDestroyed 这一击是否摧毁了核心
	 * @param IncomingDirection 弹丸的飞行方向（世界空间）。用于计算方向加成；
	 *        传零向量表示"不计算方向加成"（向后兼容旧调用）。
	 * @return 实际承受伤害的部位标签；未命中部位时返回无效 Tag
	 */
	FGameplayTag ApplyDamageByBoneEx(FName BoneName, float Damage,
		float& OutTaken, bool& bOutBrokePart, bool& bOutCoreDestroyed,
		const FVector& IncomingDirection = FVector::ZeroVector);

	/**
	 * 某部位被从 Direction 方向击中时的伤害倍率。
	 *
	 * 规则（见 FPartBoneRule 上的注释）：把"从部位指向射手的向量"与机体前向
	 * 做点积，> 0.55 算背面、< -0.55 算正面，其余算侧面。
	 * 阈值给得比较宽，是因为战斗里玩家不会精确站到正后方 ——
	 * 太窄的话"绕后"就变成了一个需要卡角度的技巧，而不是战术选择。
	 */
	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	float GetExposureMultiplier(const FGameplayTag& PartTag,
		const FVector& IncomingDirection) const;

	/** 任务结束后的自动修复（玩家自身部位） */
	UFUNCTION(BlueprintCallable, Category = "Robot|Parts")
	void RepairAllParts();

	/**
	 * 设置部位映射表并立即重建部位血量。
	 *
	 * 为什么需要这个：组件的 BeginPlay 早于 Actor 的 BeginPlay，
	 * 如果等 Actor 在 BeginPlay 里赋值 PartMap，部位已经用空表初始化过了。
	 * 用这个函数可以安全地在任何时候换表并重建。
	 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Parts")
	void SetPartMap(UPartMapData* InPartMap);

	/** 初始化：按映射表建立部位血量表 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Parts")
	void InitializeParts();

protected:
	virtual void BeginPlay() override;

	/** 部位归零后的处理：隐藏骨骼、生成掉落物、广播事件 */
	void HandlePartDestruction(const FGameplayTag& PartTag, const FPartBoneRule& Rule);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Parts")
	TMap<FGameplayTag, FPartHealth> Parts;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Parts")
	bool bDisabled = false;

	/** 运行时无敌标志（见 SetInvulnerable 注释）。默认关，退出观察者务必复位。 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Parts")
	bool bInvulnerable = false;

private:
	/** 该部位的掉落物生成位置（世界空间） */
	FVector ResolveDropLocation(FName BoneName) const;
};
