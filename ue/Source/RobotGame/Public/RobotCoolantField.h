#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProceduralMeshComponent.h"
#include "RobotCoolantField.generated.h"

class UProceduralMeshComponent;
class USphereComponent;
class UPointLightComponent;
class UInstancedStaticMeshComponent;
class UMaterialInterface;

/**
 * 冷却液泄漏池 —— CellFluids 风格的实时浅水波场。
 *
 * 为什么不用 Blender 预烘焙：流体要“活”。这里在运行时维护一张高度场，
 * 每帧推进二维波动方程，玩家 / 敌机踩进水里会激起真实的尾迹涟漪，
 * 断管入水口持续注入新的波源。网格顶点每帧重建法线，配合法线贴图与
 * 顶点色泡沫，形成持续流动、边缘浸润的液体表面。
 *
 * 玩法：站进冷却液会快速带走机体热量（-9/s），与剧毒废液池的升温形成
 * 明确的风险 / 收益对位。
 */
UCLASS()
class ROBOTGAME_API ARobotCoolantField : public AActor
{
	GENERATED_BODY()

public:
	ARobotCoolantField();

	virtual void Tick(float DeltaSeconds) override;

	/** 液面半径（cm） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float PoolRadius = 300.f;

	/** 高度场横向格数 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	int32 GridCells = 56;

	/** 波速平方（越大涟漪扩散越快） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float WaveSpeedSq = 0.18f;

	/** 每步阻尼（越接近 1 波纹持续越久） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float Damping = 0.988f;

	/** 站在液体里每秒降低多少热量 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float HeatCoolPerSecond = 9.f;

	/** 覆盖液面材质；留空则用冷却液材质。毒液池可指向 M_Toxic_Fluid。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	TObjectPtr<UMaterialInterface> SurfaceMaterial;

	/** 液面点光颜色（冷却液青蓝，毒液绿） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	FLinearColor GlowColor = FLinearColor(0.12f, 0.92f, 1.0f, 1.0f);

	/** 液面点光强度；毒液池调低，避免和废液池自带绿光叠加过曝 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float GlowIntensity = 9000.f;

	/** 水面最大起伏（cm）。越大越像海浪；毒液池只要薄薄一层涟漪。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float MaxHeight = 5.f;

	/** 死水池：关闭持续入水口和边缘涌泉，只留微小环境涟漪与角色/弹丸扰动 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	bool bStagnant = false;

	/** 持续注水口（局部坐标 cm）：液体从这里不断注入，形成连续外扩的涟漪。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	bool bInflow = false;

	/** 注水口位置（相对 Actor 的 XY，cm）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	FVector2D InflowLocal = FVector2D(100.f, 0.f);

	/** 每次注入的强度（负值=往下压出凹陷）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float InflowStrength = 1.6f;

	/** 注入点半径（cm）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float InflowRadius = 70.f;

	/** 注水节律（秒）。0.08 ≈ 每秒 12 次，看起来是连续水流。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	float InflowInterval = 0.08f;

	/** 主流向（cm/s）：整张高度场沿此方向平流，波纹会顺流漂走。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant")
	FVector2D FlowVelocity = FVector2D::ZeroVector;

	// ── 落水水珠（第一百一十五轮，C++ 自写物理粒子）─────────────
	//
	// 为什么不用 Niagara：UE5.8 Python 复制引擎模板能落盘、能加载，
	// 但 emitter 运行时引用没重定位，实测 5 个模板贴到玩家脸前都不出粒子；
	// 且项目在 SM5 下有材质编译失败。这里用 InstancedStaticMesh 自己积分，
	// 完全代码驱动、和本类的高度场物理联动（水珠落回时再注入涟漪）。

	/** 是否开启落水水珠 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant|Splash")
	bool bSplashDroplets = true;

	/** 每次注水脉冲喷出的水珠数 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant|Splash")
	int32 DropletsPerPulse = 3;

	/** 水珠初始上抛速度（cm/s） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant|Splash")
	float DropletLaunchSpeed = 165.f;

	/** 水珠水平散开速度（cm/s） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant|Splash")
	float DropletSpread = 95.f;

	/** 水珠重力（cm/s²） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant|Splash")
	float DropletGravity = 780.f;

	/** 水珠半径（cm） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant|Splash")
	float DropletRadius = 2.4f;

	/** 同屏水珠上限（性能护栏） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Robot|Coolant|Splash")
	int32 MaxDroplets = 90;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Coolant")
	TObjectPtr<UProceduralMeshComponent> Surface;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Coolant")
	TObjectPtr<USphereComponent> Zone;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Coolant")
	TObjectPtr<UPointLightComponent> Glow;

	/** 落水水珠批量渲染组件（一个组件画所有实例）。 */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot|Coolant")
	TObjectPtr<UInstancedStaticMeshComponent> Droplets;

private:
	void BuildMesh();
	void StepSim();
	void RefreshMesh();
	void ApplyImpulse(float LocalX, float LocalY, float Strength, float RadiusCm);
	/** 把高度场沿 FlowVelocity 平流一小步（双线性采样）。 */
	void Advect(float Dt);
	/** 轻度平滑：压掉网格尺度的棋盘伪影（5 点平均）。 */
	void SmoothHeight(float Amount);
	/** 生成一批落水水珠（在入水口脉冲时调用）。 */
	void SpawnDroplets(int32 Count);
	/** 每帧推进水珠物理（位置/速度/重力/寿命/落回检测）。 */
	void StepDroplets(float Dt);
	/** 把存活水珠的变换写回 InstancedStaticMesh。 */
	void RefreshDroplets();

	/** 一颗水珠 */
	struct FSplashDroplet
	{
		FVector Pos = FVector::ZeroVector;   // 局部坐标
		FVector Vel = FVector::ZeroVector;
		float Age = 0.f;
		float Life = 1.f;
		float Scale = 1.f;   // 个体尺寸倍率（真实水花大小不一）
		bool bAlive = false;
	};
	TArray<FSplashDroplet> DropletPool;

	// 高度场 (N+1)^2
	TArray<float> Height;
	TArray<float> Velocity;

	TArray<FVector> Verts;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FLinearColor> Colors;
	TArray<FProcMeshTangent> Tangents;
	TArray<int32> Tris;

	float CellSize = 12.f;
	int32 N = 56;
	float SimAccum = 0.f;
	float TimeAccum = 0.f;
	/** 死水环境脉冲计时（每实例独立，避免多池共用一个 static 计时器互相加速）。 */
	float StagnantTimer = 0.f;
	/** 注水口节拍计时。 */
	float InflowTimer = 0.f;
	/** 平流用的临时缓冲，避免每帧分配。 */
	TArray<float> HeightSrc;
	TArray<float> VelocitySrc;
	float BaseZ = 5.f;
	bool bMeshReady = false;
	bool bMeshDirty = true;
};
