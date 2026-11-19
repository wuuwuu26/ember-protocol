#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProceduralMeshComponent.h"
#include "RobotBasin.generated.h"

class UProceduralMeshComponent;
class UMaterialInterface;

/**
 * 圆形水池池壁（程序化环状网格）。
 *
 * 为什么需要：液体直接摊在地板上，无论材质怎么做都像"倒了一地的果冻"。
 * 一圈有厚度的池壁给出三件事：
 *   1. 硬水线 —— 水面与池壁相交处有明确的接触线；
 *   2. 容器感 —— 液体被"装"在里面，而不是浮在地板上；
 *   3. 湿润带 —— 顶点色 R 标记水位附近的湿区，材质在那里压暗、降粗糙，
 *      池壁下半截是湿的、上半截是干的，这是真实水池最直观的一条线索。
 *
 * 网格分三段：内壁 / 顶面环 / 外壁。材质请用双面，避免绕序问题。
 */
UCLASS()
class ROBOTGAME_API ARobotBasin : public AActor
{
	GENERATED_BODY()

public:
	ARobotBasin();

	/** 池壁内半径（cm）——液面半径略小于它，水面正好顶在壁上。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float InnerRadius = 138.f;

	/** 池壁外半径（cm）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float OuterRadius = 162.f;

	/** 池壁顶面高度（相对 Actor）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float TopZ = 10.f;

	/** 池壁底面高度（相对 Actor，埋进地板）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float BottomZ = -10.f;

	/** 水位高度（相对 Actor），用于计算湿润带。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float WaterZ = 5.5f;

	/** 湿润带高度（cm）：水位以上多少厘米内算"湿"。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float WetBand = 10.f;

	/** 圆周分段数。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	int32 Segments = 96;

	/** 矩形水渠模式：忽略半径参数，改用 HalfLength / HalfWidth / WallThickness。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	bool bChannel = false;

	/** 水渠内壁半长（X，cm）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float HalfLength = 380.f;

	/** 水渠内壁半宽（Y，cm）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float HalfWidth = 100.f;

	/** 渠壁厚度（cm）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	float WallThickness = 28.f;

	/** 池壁材质（建议双面）。 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Basin")
	TObjectPtr<UMaterialInterface> RimMaterial;

protected:
	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Basin")
	TObjectPtr<UProceduralMeshComponent> Mesh;

private:
	void BuildRing();
	void BuildChannel();
	float WetAt(float Z) const;
};
