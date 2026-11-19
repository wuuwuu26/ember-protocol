#include "Abilities/RobotGameplayAbility.h"

#include "RobotCharacter.h"
#include "AssemblyComponent.h"
#include "RobotChassisData.h"
#include "RobotAttributeSet.h"

#include "AbilitySystemComponent.h"

URobotGameplayAbility::URobotGameplayAbility()
{
	InstancingPolicy = EGameplayAbilityInstancingPolicy::InstancedPerActor;
	NetExecutionPolicy = EGameplayAbilityNetExecutionPolicy::LocalPredicted;
}

ARobotCharacter* URobotGameplayAbility::GetRobotCharacter() const
{
	if (const FGameplayAbilityActorInfo* Info = GetCurrentActorInfo())
	{
		return Cast<ARobotCharacter>(Info->AvatarActor.Get());
	}
	return nullptr;
}

URobotAttributeSet* URobotGameplayAbility::GetRobotAttributes() const
{
	if (const ARobotCharacter* Character = GetRobotCharacter())
	{
		return Character->GetAttributeSet();
	}
	return nullptr;
}

UAssemblyComponent* URobotGameplayAbility::GetAssembly() const
{
	if (const ARobotCharacter* Character = GetRobotCharacter())
	{
		return Character->GetAssembly();
	}
	return nullptr;
}

const URobotChassisData* URobotGameplayAbility::GetChassis() const
{
	if (const UAssemblyComponent* Assembly = GetAssembly())
	{
		return Assembly->Chassis;
	}
	return nullptr;
}

bool URobotGameplayAbility::IsOverheated() const
{
	const URobotAttributeSet* Attrs = GetRobotAttributes();
	return Attrs ? Attrs->IsOverheated() : false;
}

bool URobotGameplayAbility::ConsumePower(float Amount)
{
	UAbilitySystemComponent* ASC = GetAbilitySystemComponentFromActorInfo();
	URobotAttributeSet* Attrs = GetRobotAttributes();
	if (!ASC || !Attrs || Amount <= 0.f)
	{
		return true;
	}

	if (Attrs->GetPower() < Amount)
	{
		return false;
	}

	ASC->ApplyModToAttribute(URobotAttributeSet::GetPowerAttribute(),
		EGameplayModOp::Additive, -Amount);
	return true;
}

void URobotGameplayAbility::AddHeat(float Amount)
{
	UAbilitySystemComponent* ASC = GetAbilitySystemComponentFromActorInfo();
	if (!ASC || Amount <= 0.f)
	{
		return;
	}
	ASC->ApplyModToAttribute(URobotAttributeSet::GetHeatAttribute(),
		EGameplayModOp::Additive, Amount);
}
