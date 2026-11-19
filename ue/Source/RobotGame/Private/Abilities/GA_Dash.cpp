#include "Abilities/GA_Dash.h"

#include "RobotCharacter.h"
#include "RobotSfx.h"
#include "AssemblyComponent.h"
#include "RobotAttributeSet.h"
#include "RobotChassisData.h"
#include "RobotTypes.h"

#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

UGA_Dash::UGA_Dash()
{
	// 过热时直接拦截施放，不用在每个技能里手写判断
	ActivationBlockedTags.AddTag(RobotTags::State_Overheated());
}

void UGA_Dash::ActivateAbility(const FGameplayAbilitySpecHandle Handle,
	const FGameplayAbilityActorInfo* ActorInfo,
	const FGameplayAbilityActivationInfo ActivationInfo,
	const FGameplayEventData* TriggerEventData)
{
	Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);

	ACharacter* Character = Cast<ACharacter>(GetAvatarActorFromActorInfo());
	if (!Character)
	{
		EndAbility(Handle, ActorInfo, ActivationInfo, true, true);
		return;
	}

	// 消耗量来自装配数据 —— 换机体后冲刺代价会变，这是数据驱动的意义
	float PowerCost = 22.f;
	if (const URobotChassisData* Chassis = GetChassis())
	{
		PowerCost = Chassis->DashPowerCost;
	}

	// 电力不足直接失败。注意这里 EndAbility 的 bWasCancelled=true，
	// 让动画蓝图能区分"没电了"和"主动取消"。
	if (!ConsumePower(PowerCost))
	{
		EndAbility(Handle, ActorInfo, ActivationInfo, true, true);
		return;
	}

	AddHeat(HeatPerDash);

	// 冲刺方向：优先用移动输入方向，没有输入则朝正前方
	FVector Direction = Character->GetLastMovementInputVector().GetSafeNormal();
	if (Direction.IsNearlyZero())
	{
		Direction = Character->GetActorForwardVector();
	}
	Direction.Z = 0.f;
	Direction = Direction.GetSafeNormal();

	// LaunchCharacter 会叠加到 CMC 的当前速度上，bXYOverride=true 保证
	// 冲刺速度是决定性的，不会被原有速度稀释。
	Character->LaunchCharacter(Direction * DashStrength, true, false);

	// 冲刺音效：在角色位置播放（喷口气流声）
	RobotSfx::PlayAt(Character, TEXT("SFX_Dash"), Character->GetActorLocation(),
		0.8f);

	// 冲刺反馈回调：机体推进器喷口微光与镜头顿挫
	if (ARobotCharacter* Robot = Cast<ARobotCharacter>(Character))
	{
		Robot->OnDashTriggered();
	}

	// 开发期日志：冲刺是"电力预算"的核心消费者，实机验证时要看得到
	// 消耗与余额（-AutoDash 自动测试会反复触发它）。
	if (const URobotAttributeSet* Attrs = GetRobotAttributes())
	{
		UE_LOG(LogTemp, Log, TEXT("[冲刺] 消耗电力=%.0f 剩余=%.0f 热量=%.0f/%.0f"),
			PowerCost, Attrs->GetPower(), Attrs->GetHeat(), Attrs->GetMaxHeat());
	}

	EndAbility(Handle, ActorInfo, ActivationInfo, true, false);
}
