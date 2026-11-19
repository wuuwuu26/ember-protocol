#include "RobotBasin.h"

#include "Materials/MaterialInterface.h"

ARobotBasin::ARobotBasin()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("BasinMesh"));
	SetRootComponent(Mesh);
	Mesh->bUseAsyncCooking = false;
	Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	Mesh->SetCollisionObjectType(ECC_WorldStatic);
	Mesh->SetCollisionResponseToAllChannels(ECR_Block);
}

float ARobotBasin::WetAt(float Z) const
{
	return FMath::Clamp(1.f - (Z - WaterZ) / FMath::Max(1.f, WetBand), 0.f, 1.f);
}

void ARobotBasin::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	if (bChannel) { BuildChannel(); } else { BuildRing(); }
}

void ARobotBasin::BeginPlay()
{
	Super::BeginPlay();
	// 运行时无条件重建：编辑器里改过参数（半径/水位/湿润带）后，构造时生成的
	// 网格可能是旧参数，这里以 BeginPlay 的最终值为准。
	if (bChannel) { BuildChannel(); } else { BuildRing(); }
}

void ARobotBasin::BuildChannel()
{
	TArray<FVector> Verts;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FLinearColor> Colors;
	TArray<FProcMeshTangent> Tangents;
	TArray<int32> Tris;

	auto PushVert = [&](const FVector& P, const FVector& N, const FVector2D& UV,
		const float Wet, const FVector& Tan)
	{
		Verts.Add(P);
		Normals.Add(N);
		UVs.Add(UV);
		Colors.Add(FLinearColor(Wet, 0.f, 0.f, 1.f));
		Tangents.Add(FProcMeshTangent(Tan.X, Tan.Y, Tan.Z));
	};

	const float T = FMath::Max(2.f, WallThickness);
	const float VWall = (TopZ - BottomZ) / 100.f;

	// 竖向墙面：A→B 沿渠走向，normal 指向该面朝向的一侧。
	auto AddWall = [&](const FVector2D& A, const FVector2D& B, const FVector& N,
		const float Wet, const float U0, const float U1)
	{
		const int32 Base = Verts.Num();
		const FVector Tan(-N.Y, N.X, 0.f);
		PushVert(FVector(A.X, A.Y, BottomZ), N, FVector2D(U0, 0.f), Wet, Tan);
		PushVert(FVector(A.X, A.Y, TopZ), N, FVector2D(U0, VWall), Wet, Tan);
		PushVert(FVector(B.X, B.Y, BottomZ), N, FVector2D(U1, 0.f), Wet, Tan);
		PushVert(FVector(B.X, B.Y, TopZ), N, FVector2D(U1, VWall), Wet, Tan);
		Tris.Add(Base); Tris.Add(Base + 2); Tris.Add(Base + 1);
		Tris.Add(Base + 1); Tris.Add(Base + 2); Tris.Add(Base + 3);
	};

	// 顶面：内边 P 到外边 Q
	// ⚠️ V 原本用整条顶面宽度 T/100（水渠 28cm → 0.28）。乘上材质 tiling 后
	//    还不到半个纹理周期，窄带上采样到的几乎是同一个纹素 → 渠沿渲染成
	//    一条没有细节的平色带（实机表现为"白边，纹理有问题"）。
	//    改成按 12cm 一个周期归一化，窄面上也能看到混凝土粒度的明暗变化。
	auto AddTop = [&](const FVector2D& P0, const FVector2D& P1,
		const FVector2D& Q0, const FVector2D& Q1, const float U0, const float U1)
	{
		const int32 Base = Verts.Num();
		const FVector Tan = FVector((P1 - P0).GetSafeNormal(), 0.f);
		const float V = T / 12.f;      // 每 12cm 一个纹理周期（而不是整条宽度一次）
		PushVert(FVector(P0.X, P0.Y, TopZ), FVector::UpVector, FVector2D(U0, 0.f), 0.f, Tan);
		PushVert(FVector(Q0.X, Q0.Y, TopZ), FVector::UpVector, FVector2D(U0, V), 0.f, Tan);
		PushVert(FVector(P1.X, P1.Y, TopZ), FVector::UpVector, FVector2D(U1, 0.f), 0.f, Tan);
		PushVert(FVector(Q1.X, Q1.Y, TopZ), FVector::UpVector, FVector2D(U1, V), 0.f, Tan);
		Tris.Add(Base); Tris.Add(Base + 2); Tris.Add(Base + 1);
		Tris.Add(Base + 1); Tris.Add(Base + 2); Tris.Add(Base + 3);
	};

	const FVector2D In[4] = {
		FVector2D(-HalfLength, -HalfWidth),
		FVector2D(HalfLength, -HalfWidth),
		FVector2D(HalfLength, HalfWidth),
		FVector2D(-HalfLength, HalfWidth) };
	const FVector2D Out[4] = {
		FVector2D(-HalfLength - T, -HalfWidth - T),
		FVector2D(HalfLength + T, -HalfWidth - T),
		FVector2D(HalfLength + T, HalfWidth + T),
		FVector2D(-HalfLength - T, HalfWidth + T) };

	float UAcc = 0.f;
	for (int32 i = 0; i < 4; ++i)
	{
		const int32 j = (i + 1) % 4;
		const FVector2D A = In[i];
		const FVector2D B = In[j];
		const FVector2D OA = Out[i];
		const FVector2D OB = Out[j];
		const FVector2D D = (B - A).GetSafeNormal();
		const FVector2D Nin(-D.Y, D.X);          // 指向渠内
		const float Len = (B - A).Size() / 100.f;
		const float U0 = UAcc;
		const float U1 = UAcc + Len;

		// 内壁：顶点色 R = 1（湿）
		AddWall(A, B, FVector(Nin.X, Nin.Y, 0.f), 1.f, U0, U1);
		// 顶面：干
		AddTop(A, B, OA, OB, U0, U1);
		// 外壁：干，法线朝外
		AddWall(OA, OB, FVector(-Nin.X, -Nin.Y, 0.f), 0.f, U0, U1);

		UAcc = U1;
	}

	Mesh->ClearAllMeshSections();
	Mesh->CreateMeshSection_LinearColor(0, Verts, Tris, Normals, UVs, Colors,
		Tangents, true);
	if (RimMaterial)
	{
		Mesh->SetMaterial(0, RimMaterial);
	}
}

void ARobotBasin::BuildRing()
{
	const int32 S = FMath::Max(12, Segments);

	TArray<FVector> Verts;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FLinearColor> Colors;
	TArray<FProcMeshTangent> Tangents;
	TArray<int32> Tris;

	auto PushVert = [&](const FVector& P, const FVector& N, const FVector2D& UV,
		const float Wet, const FVector& Tan)
	{
		Verts.Add(P);
		Normals.Add(N);
		UVs.Add(UV);
		Colors.Add(FLinearColor(Wet, 0.f, 0.f, 1.f));
		Tangents.Add(FProcMeshTangent(Tan.X, Tan.Y, Tan.Z));
	};

	// 竖向墙面（内壁 / 外壁）：两排顶点构成一条带
	auto AddWall = [&](float R, bool bInner)
	{
		const int32 Base = Verts.Num();
		for (int32 k = 0; k <= S; ++k)
		{
			const float A = 2.f * PI * k / static_cast<float>(S);
			const FVector Dir(FMath::Cos(A), FMath::Sin(A), 0.f);
			const FVector N = bInner ? -Dir : Dir;
			// 顶点色 R = 1 标记"内壁"：只有内壁会被水浸湿，外墙保持干水泥
			const float VcR = bInner ? 1.f : 0.f;
			const float U = (A * R) / 100.f;              // 弧长（米）
			const float V0 = 0.f;
			const float V1 = (TopZ - BottomZ) / 100.f;
			PushVert(FVector(Dir.X * R, Dir.Y * R, BottomZ), N,
				FVector2D(U, V0), VcR, FVector(-Dir.Y, Dir.X, 0.f));
			PushVert(FVector(Dir.X * R, Dir.Y * R, TopZ), N,
				FVector2D(U, V1), VcR, FVector(-Dir.Y, Dir.X, 0.f));
		}
		for (int32 k = 0; k < S; ++k)
		{
			const int32 a = Base + k * 2;
			const int32 b = a + 1;
			const int32 c = a + 2;
			const int32 d = a + 3;
			Tris.Add(a); Tris.Add(c); Tris.Add(b);
			Tris.Add(b); Tris.Add(c); Tris.Add(d);
		}
	};

	// 顶面环：从内半径到外半径的水平环带
	// ⚠️ V 按 12cm 一个周期归一化（原来用整条环宽/100，窄环带上不到半个周期，
	//    采样到近似同一个纹素 → 池沿渲染成没有细节的平色带）。与水渠顶面同理。
	auto AddTop = [&]()
	{
		const int32 Base = Verts.Num();
		const float V = FMath::Max(OuterRadius - InnerRadius, 1.f) / 12.f;
		for (int32 k = 0; k <= S; ++k)
		{
			const float A = 2.f * PI * k / static_cast<float>(S);
			const FVector Dir(FMath::Cos(A), FMath::Sin(A), 0.f);
			const float U = (A * (InnerRadius + OuterRadius) * 0.5f) / 100.f;
			PushVert(FVector(Dir.X * InnerRadius, Dir.Y * InnerRadius, TopZ),
				FVector::UpVector, FVector2D(U, 0.f), 0.f,
				FVector(-Dir.Y, Dir.X, 0.f));
			PushVert(FVector(Dir.X * OuterRadius, Dir.Y * OuterRadius, TopZ),
				FVector::UpVector, FVector2D(U, V), 0.f,
				FVector(-Dir.Y, Dir.X, 0.f));
		}
		for (int32 k = 0; k < S; ++k)
		{
			const int32 a = Base + k * 2;
			const int32 b = a + 1;
			const int32 c = a + 2;
			const int32 d = a + 3;
			Tris.Add(a); Tris.Add(c); Tris.Add(b);
			Tris.Add(b); Tris.Add(c); Tris.Add(d);
		}
	};

	AddWall(InnerRadius, true);
	AddTop();
	AddWall(OuterRadius, false);

	Mesh->ClearAllMeshSections();
	Mesh->CreateMeshSection_LinearColor(0, Verts, Tris, Normals, UVs, Colors,
		Tangents, true);
	if (RimMaterial)
	{
		Mesh->SetMaterial(0, RimMaterial);
	}
}
