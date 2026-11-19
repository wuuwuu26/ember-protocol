#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RobotDamageSpark.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;

/**
 * 部位被破坏/受损时附着的电火花短路粒子 Actor。
 * 纯 C++ 驱动小尺寸发光网格迸发与轻量点光源闪烁，呈现短路滋滋电弧感。
 */
UCLASS()
class ROBOTGAME_API ARobotDamageSpark : public AActor
{
	GENERATED_BODY()

public:
	ARobotDamageSpark();

	/** 设置电弧闪烁的生命周期与强度 */
	void InitSpark(float InLifeTime = 12.f);

protected:
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|VFX")
	TObjectPtr<UStaticMeshComponent> SparkMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|VFX")
	TObjectPtr<UPointLightComponent> SparkLight;

private:
	float SparkTimer = 0.f;
	float LifeTime = 12.f;
	float Age = 0.f;
};
