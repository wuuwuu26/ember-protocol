// GA_Fire —— 基础射击
#pragma once

#include "CoreMinimal.h"
#include "Abilities/RobotGameplayAbility.h"
#include "GA_Fire.generated.h"

class ARobotProjectile;

/**
 * 基础射击技能。
 *
 * 每次射击同时消耗电力与产生热量 —— 连续输出会在几秒内把热量顶到上限，
 * 触发 State.Overheated 并被 ActivationBlockedTags 拦住。这就是
 * "爆发窗口 — 强制停顿"节奏的完整实现。
 *
 * ── 弹道怎么算（这一段是射击手感的核心）──
 *   起点 = 枪口骨骼（跟着程序化动画走，走路摆臂 / 开火后坐都会带着它动）
 *   方向 = 枪口 → 相机准心命中点
 * 而不是"沿角色朝向打"。第三人称相机在角色斜后方，沿角色朝向打会和准心
 * 差出好几米；「相机定方向、枪口定起点」是标准做法。
 *
 * 关于射速控制：这里用技能实例上的时间戳做间隔判断，而不是 GAS 的
 * CooldownGameplayEffect。原因是冷却 GE 需要额外的资产与 Cooldown 标签，
 * 而在单机项目里它带来的收益（冷却 UI 联动）目前用不上。等做 HUD 冷却环时
 * 再换成标准做法。
 */
UCLASS()
class ROBOTGAME_API UGA_Fire : public URobotGameplayAbility
{
	GENERATED_BODY()

public:
	UGA_Fire();

	virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle,
		const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo,
		const FGameplayEventData* TriggerEventData) override;

protected:
	/** 弹丸类。留空则技能静默失败，不会崩溃。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire")
	TSubclassOf<ARobotProjectile> ProjectileClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire", meta = (ClampMin = "0"))
	float Damage = 15.f;

	/**
	 * 每发耗电。与冲刺（22 电）共享同一个电力池 —— 这是"机动 vs 输出"的取舍。
	 *
	 * 标定依据（2026-10-14）：原值 5 让 60 点电力池只够打 12 发、
	 * 之后被回充速率（9/s）掐死，连射变成"打两发歇三秒"。
	 * 改为 2.5 后：爆发可打 24 发，持续输出时消耗（13.1/s）略高于回充（9/s）
	 * —— 资源耗尽变慢、但仍真实存在，冲刺抢电的取舍也保住了。
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire", meta = (ClampMin = "0"))
	float PowerPerShot = 2.5f;

	/**
	 * 每发积热。标定必须考虑**电力限速**（两道成本互相制约）：
	 *   · 电力：2.5/发、回充 9/s（轻型机）→ 可持续射速 ≈ 3.6 发/秒；
	 *   · 热量要在这个射速下积累，必须 > 34/3.6 ≈ 9.5/发（34 是轻型机散热）。
	 *   · 取 19/发：约 2.6 秒、13 发过热 → 锁定 2 秒。
	 * 第一版 11.5 时 3.6×11.5 = 41.4 ≈ 散热 34 —— 净积累几乎为零，
	 * 实机验证"全程零过热"，机制形同虚设（实测 3 轮截图确认）。
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire", meta = (ClampMin = "0"))
	float HeatPerShot = 19.f;

	/** 两次射击的最小间隔（秒）。约 320 发/分。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire", meta = (ClampMin = "0.01"))
	float FireInterval = 0.19f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire")
	float ProjectileSpeed = 4200.f;

	/**
	 * 弹道散布（度）。0 = 绝对精准。
	 *
	 * 给一个很小的散布（0.35°）是有意义的：完全零散布的弹道在远距离会
	 * 出现"所有弹孔叠成一个点"的假感，且没有"火力压制"的视觉表现。
	 * 这个值小到不影响瞄准，只是让弹着点有一点点自然抖动。
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire", meta = (ClampMin = "0"))
	float SpreadDegrees = 0.35f;

	/** 是否连续开火时逐渐加大散布（连射惩罚）。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire")
	bool bBloomOnSustainedFire = true;

	/** 每连射一发额外增加的散布（度），上限 3 倍基础值。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire", meta = (ClampMin = "0"))
	float SpreadBloomPerShot = 0.22f;

	/** 冷却散布的速率（度/秒） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire", meta = (ClampMin = "0"))
	float SpreadCoolRate = 3.5f;

	/** 出弹点的骨骼挂点名（找不到时用角色位置兜底） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Fire")
	FName MuzzleSocketName = TEXT("socket_arm_R");

private:
	/** 上次开火的世界时间。InstancedPerActor 保证每个角色有独立实例。 */
	float LastFireTime = -1000.f;

	/** 当前累积的额外散布（度） */
	float SpreadBloom = 0.f;
};
