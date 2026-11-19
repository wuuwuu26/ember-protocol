#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RobotHazardSludge.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class USphereComponent;

/**
 * 战术环境剧毒废液池（CellFluid 生态）。
 *
 * 位于工业竞技场地板凹陷洼地：
 * 1. 表面呈动态缓慢翻滚的荧光青绿生物废液，散发 18,000cd 的剧毒冷光；
 * 2. 玩家或敌机踏入废液池时（Overlap），机体散热系统受到化学腐蚀堵塞：
 *    - 每秒持续累加 18% 热量（强制升温，诱发过热锁定）；
 *    - 移动速度降低 40%（泥泞滞涩减速）；
 * 3. 伴随间歇性低沉气泡破裂与电解液滋滋声。
 */
UCLASS()
class ROBOTGAME_API ARobotHazardSludge : public AActor
{
	GENERATED_BODY()

public:
	ARobotHazardSludge();

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Hazard")
	TObjectPtr<USphereComponent> HazardArea;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Hazard")
	TObjectPtr<UStaticMeshComponent> SludgeMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Hazard")
	TObjectPtr<UPointLightComponent> SludgeGlow;

	/** 危险区域半径（cm） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Hazard")
	float HazardRadius = 180.f;

	/** 每秒腐蚀升温量（%） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Hazard")
	float HeatPerSecond = 22.f;

private:
	float BubbleTimer = 0.f;
};
