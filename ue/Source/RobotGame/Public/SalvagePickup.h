// 回收物 —— 部位被拆解后掉落的废料容器
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SalvagePickup.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class URotatingMovementComponent;

/**
 * 回收物容器。
 *
 * 掉落来源：敌人部位被摧毁。价值由部位决定（核心最高，躯干为 0 不掉落）。
 * 玩家靠近自动吸附拾取 —— 不需要按键，避免在战斗中增加操作负担。
 */
UCLASS()
class ROBOTGAME_API ASalvagePickup : public AActor
{
	GENERATED_BODY()

public:
	ASalvagePickup();

	/** 由生成方设置价值 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Salvage")
	void SetValue(int32 InValue);

	UFUNCTION(BlueprintPure, Category = "Robot|Salvage")
	int32 GetValue() const { return Value; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Salvage")
	TObjectPtr<USphereComponent> Collision;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Salvage")
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Salvage")
	TObjectPtr<URotatingMovementComponent> Spin;

	/** 拾取半径（cm） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Salvage")
	float PickupRadius = 220.f;

	/** 吸附半径：进入这个范围后会被拉向玩家 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Salvage")
	float AttractRadius = 500.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Salvage")
	float AttractSpeed = 900.f;

	/** 生成后的存活时间（秒）。0 表示不自动消失。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Salvage")
	float LifeSeconds = 0.f;

private:
	UPROPERTY()
	TObjectPtr<AActor> AttractTarget;

	int32 Value = 5;
	bool bCollected = false;
	float BobTime = 0.f;

	/** 尝试把废料加给玩家，成功返回 true */
	bool TryCollect(AActor* Collector);

protected:
	/** 废料掉落后的金色拾取信标光，夜景中清晰指引掉落物位置 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Salvage")
	TObjectPtr<class UPointLightComponent> BeaconLight;
};
