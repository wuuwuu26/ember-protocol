// 弹丸 —— 命中时把伤害路由到部位系统
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RobotProjectile.generated.h"

class USphereComponent;
class UProjectileMovementComponent;
class UStaticMeshComponent;
class UPointLightComponent;

/**
 * 机体武器弹丸。
 *
 * 关键在 ProcessHit：从命中结果取出 BoneName，交给目标的 UPartDamageComponent
 * 翻译成部位标签。命中不在映射表里的骨骼（装饰骨、武器）时不计入部位伤害 ——
 * 这样"瞄准腿部"才有意义，而不是随便打哪都算。
 *
 * 碰撞策略：对 Pawn 用 Overlap、对场景用 Block。
 * 为什么不能对 Pawn 用 Block：弹丸出膛点在射手自己的胶囊里，而"物理阻挡"
 * 是双向的 —— 弹丸会挡住射手自己的移动扫掠（实测日志里大量
 * "BP_Enemy_C_8 is stuck ... Component:Collision"，敌人绕着绕着被自己的子弹卡住）。
 * 改成 Overlap 后，弹丸照常触发伤害，但不再参与角色移动的阻挡判定。
 */
UCLASS()
class ROBOTGAME_API ARobotProjectile : public AActor
{
	GENERATED_BODY()

public:
	ARobotProjectile();

	/** 由施放者设置伤害与速度 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Projectile")
	void InitProjectile(float InDamage, float InSpeed, AActor* InInstigatorActor);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void OnHit(UPrimitiveComponent* HitComp, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, FVector NormalImpulse,
		const FHitResult& Hit);

	/** 打中角色走这条（Pawn 是 Overlap，不是 Block） */
	UFUNCTION()
	void OnOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
		bool bFromSweep, const FHitResult& SweepResult);

	/** 命中处理的唯一实现：直接命中与重叠都汇到这里 */
	void ProcessHit(AActor* OtherActor, UPrimitiveComponent* OtherComp,
		const FVector& ImpactPoint, const FVector& ImpactNormal, FName BoneName);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Projectile")
	TObjectPtr<USphereComponent> Collision;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Projectile")
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Projectile")
	TObjectPtr<UProjectileMovementComponent> Movement;

	/**
	 * 枪口闪光 / 弹体光晕。
	 *
	 * 出弹点就是枪口，所以弹丸出生瞬间把这里的强度拉满、随后迅速衰减，
	 * 视觉上就是"开火一闪"。用点光源而不是发光材质球：材质需要资产配合，
	 * 点光源不依赖任何资产，一定有效，也不会被蓝图序列化吃掉。
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Projectile")
	TObjectPtr<UPointLightComponent> MuzzleLight;

	/**
	 * 曳光光晕 —— 与枪口闪光分开。
	 *
	 * 之前只有 MuzzleLight：它在 0.08 秒内衰减到 0，弹丸飞出去之后
	 * 就只剩自发光材质，不再照亮环境。高速弹道在夜景里应该把旁边的
	 * 地面/墙面扫亮一条，所以再加一盏**全程常亮**的低强度点光。
	 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Projectile")
	TObjectPtr<UPointLightComponent> TracerLight;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Projectile")
	float Damage = 15.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Projectile")
	float LifeSeconds = 3.f;

	/** 枪口闪光的峰值强度（流明） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Projectile")
	float FlashIntensity = 12000.f;

	/** 闪光衰减时长（秒）。短一点才有"一闪"的感觉 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Projectile")
	float FlashDuration = 0.08f;

	/** 命中后是否销毁。设 false 可做穿透弹。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot|Projectile")
	bool bDestroyOnHit = true;

private:
	/** 闪光剩余时间，Tick 里线性衰减到 0 */
	float FlashRemaining = 0.f;

	/** 已经结算过命中：防止一次重叠被多帧/多组件重复触发 */
	bool bImpactProcessed = false;
};
