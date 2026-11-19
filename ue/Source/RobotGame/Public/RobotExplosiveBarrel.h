#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RobotExplosiveBarrel.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class ASalvagePickup;

/**
 * 战术爆炸燃料桶。
 *
 * 散布在竞技场掩体与脚手架旁。
 * 受到 1~2 枪射击（生命值 <= 0）时触发剧烈爆炸：
 * 1. 爆发 120,000cd 的橘红强光冲击波（随时间快速衰减）；
 * 2. 对 450cm 范围内的敌人造成范围部位伤害，可直接炸断敌机机械臂/腿部；
 * 3. 伴随剧烈金属爆炸低沉重音，并向四周震落 2~3 块高价值金琥珀废料核心；
 * 4. 桶身碎裂转变为焦黑废墟模型残骸。
 */
UCLASS()
class ROBOTGAME_API ARobotExplosiveBarrel : public AActor
{
	GENERATED_BODY()

public:
	ARobotExplosiveBarrel();

	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
		class AController* EventInstigator, class AActor* DamageCauser) override;

protected:
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Barrel")
	TObjectPtr<UStaticMeshComponent> BarrelMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Barrel")
	TObjectPtr<UPointLightComponent> BlastLight;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Barrel")
	TSubclassOf<ASalvagePickup> SalvageClass;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Barrel")
	float MaxHealth = 20.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Barrel")
	float BlastRadius = 460.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Barrel")
	float BlastDamage = 45.f;

private:
	float CurrentHealth = 20.f;
	bool bExploded = false;
	float BlastDecayTime = 0.f;
	const float MaxBlastDecay = 0.28f;

	void Explode(AActor* DamageCauser);
};
