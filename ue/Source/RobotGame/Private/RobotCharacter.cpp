#include "RobotCharacter.h"
#include "RobotPlayerController.h"
#include "RobotEnemy.h"
#include "RobotGameMode.h"
#include "RobotSfx.h"

#include "AssemblyComponent.h"
#include "RobotAttributeSet.h"
#include "RobotChassisData.h"
#include "RobotTypes.h"
#include "Abilities/GA_Dash.h"
#include "Abilities/GA_Fire.h"

#include "PartDamageComponent.h"
#include "PartMapData.h"
#include "RobotProjectile.h"
#include "RobotExplosiveBarrel.h"
#include "MechProceduralAnim.h"
#include "Components/PoseableMeshComponent.h"
#include "Misc/CommandLine.h"

#include "AbilitySystemComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "EnhancedPlayerInput.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "InputCoreTypes.h"
#include "EnhancedActionKeyMapping.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "DrawDebugHelpers.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PointLight.h"
#include "Engine/SpotLight.h"
#include "Components/SpotLightComponent.h"
#include "Engine/Light.h"
#include "Components/LightComponent.h"
#include "Components/LocalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "EngineUtils.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/GameViewportClient.h"
#include "Widgets/SViewport.h"
#include "Framework/Application/SlateApplication.h"

ARobotCharacter::ARobotCharacter()
{
	// 需要 Tick 来画屏幕调试读数（热量/电力/废料）
	PrimaryActorTick.bCanEverTick = true;

	// 胶囊体按机体尺度设置：机体约 2.5 m 高，胶囊半径 45、半高 120
	GetCapsuleComponent()->InitCapsuleSize(45.f, 120.f);

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	// 臂长和俯仰范围必须一起算，不能各调各的。
	// 相机相对角色的垂直偏移 ≈ SocketOffset.Z·cos(pitch) − ArmLength·sin(pitch)。
	// 臂长 620 时，俯仰 45° 会让相机下沉 438cm，而角色才高 133cm ——
	// 相机必然钻进地底，画面全黑（实测 z 从 293 掉到 −487）。
	// 480 臂长 + 25° 俯仰上限：200×0.91 − 480×0.42 = −21，相机仍在角色上方。
	CameraBoom->TargetArmLength = 480.f;
	// SocketOffset.Z 从 200 一路降到 60：
	// 相机抬得越高，画面中心越"往下压"，角色就被挤到画面最底部 ——
	// 而底部正中正好是 HUD 的热量/电力面板，机体被挡掉一半，
	// 连走路动画都看不见。降低相机高度后角色回到画面下三分之一，
	// 完整露在 HUD 上方。
	CameraBoom->SocketOffset = FVector(0.f, 0.f, 30.f);
	CameraBoom->bUsePawnControlRotation = true;
	// 相机臂跟随俯仰（2026-10-14 重新开启）。
	//
	// 曾经因为"异常输入把俯仰顶到上限、相机钻地"而锁掉俯仰 ——
	// 但那样**玩家无法上下瞄准**（准心射线来自相机正前方），
	// 对"打部位"的核心玩法是硬伤：打腿还是打核心完全选不了。
	// 现在重新开启的前提条件都满足了：
	//   ① 异常输入已在 HandleLook 里被过滤（单帧位移 >120 直接丢帧）；
	//   ② ViewPitchMin/Max 收窄到 [-40°, +12°]（见 PossessedBy）——
	//      即使顶到上限，480 臂长下相机仍在地面之上（+12° 时约 60cm）。
	// 注意：bInheritPitch=true 后，控制旋转的俯仰**取代**相对旋转的俯仰，
	// 所以下面的固定俯视 20° 不再生效（俯仰完全交给玩家，初始水平）。
	CameraBoom->bInheritPitch = true;
	CameraBoom->bInheritYaw = true;
	CameraBoom->bInheritRoll = false;
	CameraBoom->SetRelativeRotation(FRotator(0.f, 0.f, 0.f));
	// 碰撞检测必须开着，作为相机钻地的最后一道保险
	CameraBoom->bDoCollisionTest = true;
	// 只被世界静态几何挡住，不被角色自身的网格/胶囊体挡住
	CameraBoom->ProbeChannel = ECC_WorldStatic;
	CameraBoom->ProbeSize = 12.f;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	AbilitySystemComponent = CreateDefaultSubobject<UAbilitySystemComponent>(
		TEXT("AbilitySystemComponent"));
	AbilitySystemComponent->SetIsReplicated(false);
	// 单机项目：不需要网络预测，关掉能省下不少开销
	AbilitySystemComponent->SetReplicationMode(EGameplayEffectReplicationMode::Minimal);

	AttributeSet = CreateDefaultSubobject<URobotAttributeSet>(TEXT("AttributeSet"));

	PartDamage = CreateDefaultSubobject<UPartDamageComponent>(TEXT("PartDamage"));
	// 玩家用 Blender build_rig 的骨架命名（torso 兼任核心）
	PartDamage->bUsePlayerRigDefaults = true;
	Assembly = CreateDefaultSubobject<UAssemblyComponent>(TEXT("Assembly"));

	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->bOrientRotationToMovement = true;
		Move->RotationRate = FRotator(0.f, 540.f, 0.f);
		Move->JumpZVelocity = 520.f;
		Move->AirControl = 0.35f;
		Move->MaxWalkSpeed = 232.f;
		// 冲刺后需要能迅速停下，否则会滑很远
		Move->BrakingDecelerationWalking = 2400.f;
	}

	bUseControllerRotationYaw = false;

	// 默认技能：没有在编辑器里配也会自动挂上，保证原型能直接跑起来
	DefaultAbilities.Add(UGA_Dash::StaticClass());
	DefaultAbilities.Add(UGA_Fire::StaticClass());

	CreateDefaultInput();
}

/**
 * 在构造函数里直接创建 Enhanced Input 的 Action 与 MappingContext。
 *
 * 为什么不用资产：UE 没有暴露 InputActionFactory 给 Python，
 * 用脚本创建输入资产这条路走不通。而这些类型本身是普通 UObject，
 * 可以在构造函数里建出来 —— 结果是纯 C++ 就能跑起来，不需要任何手工配资产。
 *
 * 代价：输入配置写死在代码里，策划改键位要改代码。等进入生产阶段
 * 应该换成资产版本，把映射表交给策划。当前阶段"能跑起来"优先。
 */
void ARobotCharacter::CreateDefaultInput()
{
	MoveAction = CreateDefaultSubobject<UInputAction>(TEXT("IA_Move"));
	MoveAction->ValueType = EInputActionValueType::Axis2D;

	LookAction = CreateDefaultSubobject<UInputAction>(TEXT("IA_Look"));
	LookAction->ValueType = EInputActionValueType::Axis2D;

	FireAction = CreateDefaultSubobject<UInputAction>(TEXT("IA_Fire"));
	FireAction->ValueType = EInputActionValueType::Boolean;

	DashAction = CreateDefaultSubobject<UInputAction>(TEXT("IA_Dash"));
	DashAction->ValueType = EInputActionValueType::Boolean;

	CycleChassisAction = CreateDefaultSubobject<UInputAction>(TEXT("IA_CycleChassis"));
	CycleChassisAction->ValueType = EInputActionValueType::Boolean;

	ModdingAction = CreateDefaultSubobject<UInputAction>(TEXT("IA_Modding"));
	ModdingAction->ValueType = EInputActionValueType::Boolean;

	DefaultMappingContext = CreateDefaultSubobject<UInputMappingContext>(
		TEXT("IMC_Default"));

	// 用 MapKey()。注意 UInputMappingContext::Mappings 是 protected，
	// 不能直接往数组里塞；MapKey() 是唯一公开的写入途径。
	auto Bind = [this](UInputAction* Action, const FKey& Key,
	                   TArray<UInputModifier*> Mods)
	{
		if (!Action)
		{
			return;
		}
		FEnhancedActionKeyMapping& Mapping =
			DefaultMappingContext->MapKey(Action, Key);
		for (UInputModifier* Mod : Mods)
		{
			if (Mod)
			{
				Mapping.Modifiers.Add(Mod);
			}
		}
	};

	// ── 移动：数字键产生 (1,0)，用 Swizzle / Negate 组合出四方向 ──
	// 目标值 X 是左右、Y 是前后（与 HandleMove 里的解读一致）
	Bind(MoveAction, EKeys::D, {});
	{
		UInputModifierNegate* Neg = CreateDefaultSubobject<UInputModifierNegate>(
			TEXT("Mod_MoveA_Negate"));
		Neg->bX = true;
		Neg->bY = false;
		Neg->bZ = false;
		Bind(MoveAction, EKeys::A, { Neg });
	}
	{
		UInputModifierSwizzleAxis* Sw = CreateDefaultSubobject<UInputModifierSwizzleAxis>(
			TEXT("Mod_MoveW_Swizzle"));
		Sw->Order = EInputAxisSwizzle::YXZ;
		Bind(MoveAction, EKeys::W, { Sw });
	}
	{
		UInputModifierSwizzleAxis* Sw = CreateDefaultSubobject<UInputModifierSwizzleAxis>(
			TEXT("Mod_MoveS_Swizzle"));
		Sw->Order = EInputAxisSwizzle::YXZ;
		UInputModifierNegate* Neg = CreateDefaultSubobject<UInputModifierNegate>(
			TEXT("Mod_MoveS_Negate"));
		Neg->bX = false;
		Neg->bY = true;
		Neg->bZ = false;
		Bind(MoveAction, EKeys::S, { Sw, Neg });
	}

	// ── 视角：鼠标 XY 增量 ──
	Bind(LookAction, EKeys::Mouse2D, {});

	// ── 战斗 ──
	Bind(FireAction, EKeys::LeftMouseButton, {});
	Bind(DashAction, EKeys::SpaceBar, {});

	// ── 测试用：循环切换机体，验证「换机体改变玩法」──
	Bind(CycleChassisAction, EKeys::One, {});
	Bind(CycleChassisAction, EKeys::Two, {});
	Bind(CycleChassisAction, EKeys::Three, {});

	// ── 改装台（M）──
	Bind(ModdingAction, EKeys::M, {});

	// ══════════════════════════════════════════════════════════
	// 手柄（XInput / DualShock 通用映射）
	// ══════════════════════════════════════════════════════════
	//
	// 设计原则：**不新增任何逻辑**，只把同样的 Action 映射到手柄按键。
	// 键位沿用主流第三人称射击的肌肉记忆，玩家不用学：
	//   左摇杆  移动          右摇杆  视角
	//   RT      开火          LT      冲刺
	//   A       冲刺（备用）  Y       改装台
	//   RB/←→   换机体        Start   改装台（备用）
	//
	// ⚠️ 摇杆是**轴**，必须配两个修正器：
	//    · DeadZone —— 摇杆回中不精确，不加死区角色会自己缓慢漂移
	//    · Scalar   —— 视角轴的物理量是"像素/帧"，摇杆是 -1..1，
	//                  不放大 15 倍的话推满摇杆转得比蜗牛还慢
	auto MakeDeadZone = [this](float Lower, const TCHAR* Name)
	{
		UInputModifierDeadZone* DZ =
			CreateDefaultSubobject<UInputModifierDeadZone>(Name);
		DZ->LowerThreshold = Lower;
		DZ->Type = EDeadZoneType::Radial;
		return static_cast<UInputModifier*>(DZ);
	};
	auto MakeScalar = [this](float V, const TCHAR* Name)
	{
		UInputModifierScalar* SC =
			CreateDefaultSubobject<UInputModifierScalar>(Name);
		SC->Scalar = FVector(V, V, V);
		return static_cast<UInputModifier*>(SC);
	};

	// 移动：左摇杆原生就是 2D 轴，X=右 / Y=前，和 HandleMove 的解读一致
	Bind(MoveAction, EKeys::Gamepad_Left2D,
		{ MakeDeadZone(0.16f, TEXT("Mod_MovePad_DZ")) });

	// 视角：右摇杆，放大 15 倍 + 小死区
	Bind(LookAction, EKeys::Gamepad_Right2D,
		{ MakeScalar(15.f, TEXT("Mod_LookPad_Scale")),
		  MakeDeadZone(0.12f, TEXT("Mod_LookPad_DZ")) });

	// 开火：扳机是 0..1 的轴，Boolean Action 需要一个阈值触发器，
	// 否则轻轻搭一下扳机就会开火
	auto BindAxisButton = [this](UInputAction* Action, const FKey& Key,
	                             float Threshold, const TCHAR* Name)
	{
		if (!Action)
		{
			return;
		}
		FEnhancedActionKeyMapping& M = DefaultMappingContext->MapKey(Action, Key);
		UInputTriggerDown* Down =
			CreateDefaultSubobject<UInputTriggerDown>(Name);
		Down->ActuationThreshold = Threshold;
		M.Triggers.Add(Down);
	};
	BindAxisButton(FireAction, EKeys::Gamepad_RightTrigger, 0.35f,
		TEXT("Trig_FirePad"));
	BindAxisButton(DashAction, EKeys::Gamepad_LeftTrigger, 0.45f,
		TEXT("Trig_DashPad"));

	// 冲刺备用键（A）
	Bind(DashAction, EKeys::Gamepad_FaceButton_Bottom, {});

	// 换机体：十字键左右 + 右肩键（都是"下一台"，保持行为一致）
	Bind(CycleChassisAction, EKeys::Gamepad_DPad_Right, {});
	Bind(CycleChassisAction, EKeys::Gamepad_DPad_Left, {});
	Bind(CycleChassisAction, EKeys::Gamepad_RightShoulder, {});

	// 改装台：Y / Start
	Bind(ModdingAction, EKeys::Gamepad_FaceButton_Top, {});
	Bind(ModdingAction, EKeys::Gamepad_Special_Right, {});
}

int32 ARobotCharacter::GetInputMappingCount() const
{
	// UInputMappingContext::Mappings 是 protected，Python 读不到，
	// 所以提供一个访问器让验证脚本能确认映射确实建立成功了。
	if (!DefaultMappingContext)
	{
		return 0;
	}
	return DefaultMappingContext->GetMappings().Num();
}

UAbilitySystemComponent* ARobotCharacter::GetAbilitySystemComponent() const
{
	return AbilitySystemComponent;
}

void ARobotCharacter::LogInputIdentity(const TCHAR* Tag)
{
	auto Describe = [](const UObject* O) -> FString
	{
		if (!O)
		{
			return TEXT("空");
		}
		return FString::Printf(TEXT("%s<Outer=%s>"), *O->GetName(),
			O->GetOuter() ? *O->GetOuter()->GetName() : TEXT("无"));
	};

	FString FirstMappingAction = TEXT("-");
	if (DefaultMappingContext)
	{
		const TArray<FEnhancedActionKeyMapping>& Ms =
			DefaultMappingContext->GetMappings();
		if (Ms.Num() > 0)
		{
			FirstMappingAction = Describe(Ms[0].Action);
		}
	}

	UE_LOG(LogTemp, Warning,
		TEXT("[输入身份] %s | MoveAction=%s | Context=%s | 映射[0].Action=%s"),
		Tag, *Describe(MoveAction), *Describe(DefaultMappingContext),
		*FirstMappingAction);
}

/**
 * 用 NewObject(this, ...) 重建一整套输入对象。
 *
 * 根因（实测确认）：构造函数里的 CreateDefaultSubobject 建出的
 * UInputAction / UInputMappingContext，在蓝图实例化时**没有**正确按实例重建 ——
 * 映射里保存的 Action 指针指向 CDO 上的旧对象，而实例上的 MoveAction
 * 是另一个对象。于是：
 *   按键能进 PlayerInput（IsInputKeyDown=1）
 *   映射也在（映射数=10）
 *   但 QueryKeysMappedToAction(MoveAction)=0，Move 值恒为 (0,0)
 *   → 动作永不触发，HandleMove 一次都不响应
 * 注入测试之所以能跑通，是因为它直接拿实例上的 MoveAction 注入，
 * 绕过了"映射 → 动作"这一步，所以完全不受这个 bug 影响。
 */
void ARobotCharacter::RebuildRuntimeInput()
{
	if (bRuntimeInputBuilt)
	{
		return;
	}
	bRuntimeInputBuilt = true;

	MoveAction = NewObject<UInputAction>(this);
	MoveAction->ValueType = EInputActionValueType::Axis2D;

	LookAction = NewObject<UInputAction>(this);
	LookAction->ValueType = EInputActionValueType::Axis2D;

	FireAction = NewObject<UInputAction>(this);
	FireAction->ValueType = EInputActionValueType::Boolean;

	DashAction = NewObject<UInputAction>(this);
	DashAction->ValueType = EInputActionValueType::Boolean;

	CycleChassisAction = NewObject<UInputAction>(this);
	CycleChassisAction->ValueType = EInputActionValueType::Boolean;

	DefaultMappingContext = NewObject<UInputMappingContext>(this);

	auto NewNeg = [this](bool X, bool Y, bool Z)
	{
		UInputModifierNegate* M = NewObject<UInputModifierNegate>(this);
		M->bX = X;
		M->bY = Y;
		M->bZ = Z;
		return M;
	};
	auto NewSwz = [this](EInputAxisSwizzle Order)
	{
		UInputModifierSwizzleAxis* M =
			NewObject<UInputModifierSwizzleAxis>(this);
		M->Order = Order;
		return M;
	};
	auto Bind = [this](UInputAction* Action, const FKey& Key,
	                   TArray<UInputModifier*> Mods)
	{
		if (!Action)
		{
			return;
		}
		FEnhancedActionKeyMapping& Mapping =
			DefaultMappingContext->MapKey(Action, Key);
		for (UInputModifier* Mod : Mods)
		{
			if (Mod)
			{
				Mapping.Modifiers.Add(Mod);
			}
		}
	};

	// 移动：数字键产生 (1,0,0)，用 Swizzle / Negate 组合出四方向
	Bind(MoveAction, EKeys::D, {});
	Bind(MoveAction, EKeys::A, { NewNeg(true, false, false) });
	Bind(MoveAction, EKeys::W, { NewSwz(EInputAxisSwizzle::YXZ) });
	Bind(MoveAction, EKeys::S, { NewSwz(EInputAxisSwizzle::YXZ),
	                             NewNeg(false, true, false) });

	Bind(LookAction, EKeys::Mouse2D, {});

	Bind(FireAction, EKeys::LeftMouseButton, {});
	Bind(DashAction, EKeys::SpaceBar, {});

	Bind(CycleChassisAction, EKeys::One, {});
	Bind(CycleChassisAction, EKeys::Two, {});
	Bind(CycleChassisAction, EKeys::Three, {});

	// ⚠️ ModdingAction 之前**漏建了** —— 只有构造函数里建过，
	//    而运行时走的是这条 NewObject 路径，所以 M 键其实一直没生效
	//    （改装台只能靠 -ModdingUI 调试参数打开）。这里补上。
	ModdingAction = NewObject<UInputAction>(this);
	ModdingAction->ValueType = EInputActionValueType::Boolean;
	Bind(ModdingAction, EKeys::M, {});

	// ══════════════════════════════════════════════════════════
	// 手柄映射（XInput / DualShock 通用）
	// ══════════════════════════════════════════════════════════
	//
	// 键位沿用主流第三人称射击的肌肉记忆：
	//   左摇杆 移动 · 右摇杆 视角 · RT 开火 · LT/A 冲刺
	//   Y/Start 改装台 · 十字键左右 / RB 换机体
	//
	// 摇杆是轴，必须配 DeadZone（回中不精确会自己漂移）
	// 和 Scalar（摇杆 -1..1，视角轴是"像素/帧"，不放大转得极慢）。
	auto NewDZ = [this](float Lower)
	{
		UInputModifierDeadZone* M = NewObject<UInputModifierDeadZone>(this);
		M->LowerThreshold = Lower;
		M->Type = EDeadZoneType::Radial;
		return M;
	};
	auto NewScalar = [this](float V)
	{
		UInputModifierScalar* M = NewObject<UInputModifierScalar>(this);
		M->Scalar = FVector(V, V, V);
		return M;
	};
	auto BindAxisButton = [this](UInputAction* Action, const FKey& Key,
	                             float Threshold)
	{
		if (!Action)
		{
			return;
		}
		FEnhancedActionKeyMapping& M = DefaultMappingContext->MapKey(Action, Key);
		UInputTriggerDown* Down = NewObject<UInputTriggerDown>(this);
		Down->ActuationThreshold = Threshold;
		M.Triggers.Add(Down);
	};

	Bind(MoveAction, EKeys::Gamepad_Left2D, { NewDZ(0.16f) });
	Bind(LookAction, EKeys::Gamepad_Right2D,
		{ NewScalar(15.f), NewDZ(0.12f) });
	BindAxisButton(FireAction, EKeys::Gamepad_RightTrigger, 0.35f);
	BindAxisButton(DashAction, EKeys::Gamepad_LeftTrigger, 0.45f);
	Bind(DashAction, EKeys::Gamepad_FaceButton_Bottom, {});
	Bind(CycleChassisAction, EKeys::Gamepad_DPad_Right, {});
	Bind(CycleChassisAction, EKeys::Gamepad_DPad_Left, {});
	Bind(CycleChassisAction, EKeys::Gamepad_RightShoulder, {});
	Bind(ModdingAction, EKeys::Gamepad_FaceButton_Top, {});
	Bind(ModdingAction, EKeys::Gamepad_Special_Right, {});

	UE_LOG(LogTemp, Warning,
		TEXT("[输入] 已用 NewObject 重建输入对象，映射条数=%d（含手柄）"),
		DefaultMappingContext->GetMappings().Num());
}

void ARobotCharacter::BeginPlay()
{
	Super::BeginPlay();

	// 调试：-SpawnAt=x,y —— 把出生点挪到指定位置（验证围栏/边界用）
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("SpawnAt="), V))
		{
			FString XS, YS;
			if (V.Split(TEXT(","), &XS, &YS))
			{
				FVector P = GetActorLocation();
				P.X = FCString::Atof(*XS);
				P.Y = FCString::Atof(*YS);
				P.Z += 30.f;
				SetActorLocation(P, false, nullptr, ETeleportType::TeleportPhysics);
				UE_LOG(LogTemp, Warning, TEXT("[调试] 出生点改到 (%.0f,%.0f)"), P.X, P.Y);
			}
		}
	}

	SpawnLocation = GetActorLocation();
	LastSafeLocation = SpawnLocation;

	// 调试瞄准只在 -AutoFire 自动测试时启用（见 GetAimPoint）
	bAutoFireAimDebug = FParse::Param(FCommandLine::Get(), TEXT("AutoFire"));

	// 调试：-AutoSelfDestruct=<秒>（失败结算路径验证，见 Tick）
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("AutoSelfDestruct="), V))
		{
			AutoSelfDestructAt = FCString::Atof(*V);
		}
	}

	if (Assembly)
	{
		Assembly->OnAssemblyChanged.AddDynamic(this, &ARobotCharacter::HandleAssemblyChanged);
	}
	if (PartDamage)
	{
		// 组件 BeginPlay 早于 Actor BeginPlay，所以这里必须显式换表并重建部位
		if (PartMap)
		{
			PartDamage->SetPartMap(PartMap);
		}
		PartDamage->OnPartDestroyed.AddDynamic(this, &ARobotCharacter::HandlePartDestroyed);
		PartDamage->OnPartDamaged.AddDynamic(this, &ARobotCharacter::HandlePartDamaged);
		PartDamage->OnActorDisabled.AddDynamic(this, &ARobotCharacter::HandleActorDisabled);
	}

	InitializeAbilitySystem();

	// 机体：优先用预设列表的第一个，其次用 DefaultChassis
	URobotChassisData* InitialChassis = DefaultChassis;
	if (!InitialChassis && ChassisPresets.Num() > 0)
	{
		InitialChassis = ChassisPresets[0];
	}
	if (InitialChassis && Assembly)
	{
		Assembly->SetChassis(InitialChassis);
	}

	// 设置机体网格。
	// 之前只在 SwitchChassis 里设，导致出生时角色是**隐形的** —— 相机能转、
	// 能开枪、屏幕读数正常，但画面里什么都看不见。这个坑踩过。
	if (USkeletalMeshComponent* MeshComp = GetMesh())
	{
		if (!MeshComp->GetSkeletalMeshAsset() && InitialChassis)
		{
			if (USkeletalMesh* NewMesh = InitialChassis->ChassisMesh.LoadSynchronous())
			{
				MeshComp->SetSkeletalMesh(NewMesh);

				// 让脚底贴地：网格原点在骨盆（Blender 里 z=1.16m），
				// 不能想当然地写死偏移量 —— 从包围盒算，换机体时自动适配。
				const FBoxSphereBounds MeshBounds = NewMesh->GetBounds();
				const float MeshBottomLocal =
					MeshBounds.Origin.Z - MeshBounds.BoxExtent.Z;
				const float CapsuleHalfHeight =
					GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
				const float OffsetZ = -CapsuleHalfHeight - MeshBottomLocal;
				MeshComp->SetRelativeLocation(FVector(0.f, 0.f, OffsetZ));

				UE_LOG(LogTemp, Log,
					TEXT("已设置机体网格 %s（网格底 %.1fcm，偏移 %.1fcm）"),
					*NewMesh->GetName(), MeshBottomLocal, OffsetZ);
			}
			else
			{
				UE_LOG(LogTemp, Warning,
					TEXT("机体 %s 的 ChassisMesh 为空 —— 角色会隐形，检查数据资产"),
					*InitialChassis->GetName());
			}
		}
	}

	// 🔴 修正关卡灯光（放在 BeginPlay 最后，确保此时网格已设好，
	//    诊断输出的"有资产"才有意义）。
	//
	// 为什么不在 GameMode 的 BeginPlay：蓝图 BP_RobotGameMode 是脚本创建的，
	// 它自动生成了 BeginPlay 事件节点，覆盖了 C++ 父类的实现 —— 实测
	// GameMode 里的日志一行都没打出来。角色的 BeginPlay 确定会跑。
	FixLevelLighting();

	// ── 玩家英雄补光 ──
	// 第三人称视角下机体几乎总是背对太阳，镜头看到的这一面全在阴影里。
	// 这里只负责**找到关卡里的 HeroFill 灯**（ue/Scripts/arena_herofill.py 建），
	// 参数与位置交给 UpdateHeroFill() 每帧维护。
	//
	// ★ 2026-10-25：这段原来写的是运行时 SpawnActor<APointLight> ——
	//   本工程运行时生成的灯**完全不参与渲染**（详见 TuneArenaLights 的
	//   一大段说明），所以这盏"英雄补光"从来没有亮过，机体一直是一团
	//   黑剪影。现在改成"关卡里建、C++ 移位"，和光池同一条路径。
	// -NoHeroFill：关掉用于 A/B（补光对画面的贡献可以单独量出来）。
	{
		UWorld* KeyWorld = GetWorld();
		const bool bNoHeroFill =
			FParse::Param(FCommandLine::Get(), TEXT("NoHeroFill"));
		if (KeyWorld)
		{
			for (TActorIterator<APointLight> It(KeyWorld); It; ++It)
			{
				if (!It->ActorHasTag(TEXT("HeroFill")))
				{
					continue;
				}
				HeroFillLight = *It;
				if (UPointLightComponent* KC =
					Cast<UPointLightComponent>(It->GetLightComponent()))
				{
					KC->SetMobility(EComponentMobility::Movable);
					// 3m 处约 1000 lux —— 只有月光（1800 lux）的一半多。
					// 再亮一点机体就变成"一块发光的肥皂"，装甲倒角全糊掉。
					KC->SetIntensity(9000.f);
					KC->SetAttenuationRadius(1900.f);
					KC->SetLightColor(FLinearColor(0.82f, 0.90f, 1.0f));
					KC->SetCastShadows(false);
					KC->SetVolumetricScatteringIntensity(0.f);
					KC->SetVisibility(!bNoHeroFill);
					KC->MarkRenderStateDirty();
				}
				It->SetActorLocation(
					GetActorLocation() + FVector(0.f, 0.f, 240.f));
				UE_LOG(LogTemp, Warning,
					TEXT("[LIGHT] 英雄补光已接管关卡灯：9000cd / 1900cm / 无阴影 / %s"),
					bNoHeroFill ? TEXT("已关闭") : TEXT("开启"));
				break;
			}
			if (!HeroFillLight.IsValid())
			{
				UE_LOG(LogTemp, Warning,
					TEXT("[LIGHT] ⚠️ 关卡里找不到 HeroFill 灯，"
						 "机体将只有剪影（跑 ue/Scripts/arena_herofill.py）"));
			}
		}
	}

	// 建立程序化动画用的可见网格（原网格转为不可见，只留给部位系统查询）
	RefreshAnimMesh();
}

/**
 * 按当前机体重建动画网格。
 *
 * 分工：
 *   GetMesh()  —— 不可见，只负责给部位破坏系统做骨骼查询/隐藏
 *   AnimMesh   —— 可见，每帧由 MechProceduralAnim 程序化摆姿势
 * 为什么要两个：USkeletalMeshComponent 没有设置单根骨骼变换的接口，
 * 能摆姿势的只有 UPoseableMeshComponent，而部位系统写死了去找
 * USkeletalMeshComponent。两边都保留是最省事且不动现有逻辑的做法。
 */
void ARobotCharacter::RefreshAnimMesh()
{
	USkeletalMeshComponent* Src = GetMesh();
	if (!Src || !Src->GetSkeletalMeshAsset())
	{
		UE_LOG(LogTemp, Warning, TEXT("[动画] 玩家网格未设置，跳过动画网格"));
		return;
	}

	// 建一次就够；换机体时资产会变，下面 SyncVisualMesh 会重新同步
	if (!AnimMesh)
	{
		AnimMesh = MechProceduralAnim::CreateVisualMesh(this, Src);
	}
	if (!AnimMesh)
	{
		UE_LOG(LogTemp, Warning, TEXT("[动画] 动画网格创建失败，退回整体身体动作"));
		return;
	}

	// 近景英雄机体强制 LOD0：LOD1/LOD2 会丢肩甲、背包等大件。
	// 玩家永远在镜头中心，24k 面的 LOD0 开销可以接受。
	AnimMesh->SetForcedLOD(1); // ForcedLodModel 是 1-based，1 = LOD0
	UE_LOG(LogTemp, Warning, TEXT("[LOD] 玩家视觉网格强制 LOD0（Forced=%d）"),
		AnimMesh->GetForcedLOD());

	// 同步资产 + 材质。
	// 材质这一步是必须的：UPoseableMeshComponent 不会自动继承骨骼网格资产
	// 的材质槽，漏掉就会渲染成 UE 默认的棋盘格材质（一个灰方块）。
	MechProceduralAnim::SyncVisualMesh(AnimMesh, Src);

	// 资产换了 → 基准姿势失效，重新缓存
	AnimState.BaseTransforms.Reset();
	AnimState.bBaseCached = false;
	MechProceduralAnim::CacheBasePose(AnimMesh, AnimState);

	UE_LOG(LogTemp, Log,
		TEXT("[动画] 动画网格就绪：资产=%s 骨骼=%d 父=%s 世界位置(%.0f,%.0f,%.0f) "
			 "相对旋转(P=%.0f Y=%.0f R=%.0f) 可见=%d 包围盒半径=%.0f"),
		*Src->GetSkeletalMeshAsset()->GetName(),
		AnimMesh->BoneSpaceTransforms.Num(),
		AnimMesh->GetAttachParent()
			? *AnimMesh->GetAttachParent()->GetName() : TEXT("无"),
		AnimMesh->GetComponentLocation().X,
		AnimMesh->GetComponentLocation().Y,
		AnimMesh->GetComponentLocation().Z,
		AnimMesh->GetRelativeRotation().Pitch,
		AnimMesh->GetRelativeRotation().Yaw,
		AnimMesh->GetRelativeRotation().Roll,
		AnimMesh->IsVisible() ? 1 : 0,
		AnimMesh->Bounds.SphereRadius);
}

void ARobotCharacter::ClampToArena()
{
	const FVector Loc = GetActorLocation();
	UCharacterMovementComponent* Mv = GetCharacterMovement();

	// ── ① 掉出地图兜底 ──
	// 正常情况永远走不到这里（下面有 XY 硬边界）。留着是因为
	// "掉进几何缝隙" 这类问题在关卡迭代中随时可能出现，
	// 与其让玩家看着机体无限下坠，不如拉回最后一次站稳的位置。
	if (Loc.Z < FallKillZ)
	{
		FVector Back = LastSafeLocation;
		Back.Z = FMath::Max(Back.Z, 140.f);
		SetActorLocation(Back, false, nullptr, ETeleportType::TeleportPhysics);
		if (Mv)
		{
			Mv->StopMovementImmediately();
		}
		UE_LOG(LogTemp, Warning,
			TEXT("[边界] 掉出地图（Z=%.0f），已拉回 (%.0f,%.0f,%.0f)"),
			Loc.Z, Back.X, Back.Y, Back.Z);
		return;
	}

	// ── ② 记录"安全点"：站稳在地面上时每 0.5 秒采一次 ──
	if (Mv && !Mv->IsFalling())
	{
		const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
		if (Now - LastSafeSampleTime > 0.5f)
		{
			LastSafeSampleTime = Now;
			LastSafeLocation = Loc;
		}
	}

	// ── ③ XY 硬边界 ──
	// 只钳位置、并把"朝外"的速度分量清零，保留切向速度 ——
	// 这样贴着墙走仍然是顺滑的滑行，而不是撞上去就卡死。
	FVector Clamped = Loc;
	Clamped.X = FMath::Clamp(Loc.X, ArenaMin.X, ArenaMax.X);
	Clamped.Y = FMath::Clamp(Loc.Y, ArenaMin.Y, ArenaMax.Y);
	if (!Clamped.Equals(Loc, 0.5f))
	{
		SetActorLocation(Clamped, false, nullptr, ETeleportType::TeleportPhysics);
		if (Mv)
		{
			FVector V = Mv->Velocity;
			if ((Loc.X > ArenaMax.X && V.X > 0.f) ||
				(Loc.X < ArenaMin.X && V.X < 0.f))
			{
				V.X = 0.f;
			}
			if ((Loc.Y > ArenaMax.Y && V.Y > 0.f) ||
				(Loc.Y < ArenaMin.Y && V.Y < 0.f))
			{
				V.Y = 0.f;
			}
			Mv->Velocity = V;
		}
		// 调试：-AutoWalk 下把"撞到边界"打出来，方便验证围栏真的生效
		if (FParse::Param(FCommandLine::Get(), TEXT("AutoWalk")))
		{
			static float LastBoundaryLog = -100.f;
			const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
			if (Now - LastBoundaryLog > 1.f)
			{
				LastBoundaryLog = Now;
				UE_LOG(LogTemp, Warning,
					TEXT("[边界] 撞到围栏：位置=(%.0f,%.0f,%.0f) 速度=(%.0f,%.0f)"),
					Loc.X, Loc.Y, Loc.Z, Mv ? Mv->Velocity.X : 0.f,
					Mv ? Mv->Velocity.Y : 0.f);
			}
		}
	}
}

void ARobotCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// 边界约束放在最前面：所有移动（含冲刺）都已经在 Super::Tick 里算完了，
	// 这里把越界的位移吃掉，后面读位置的地方（相机、AI、HUD）拿到的都是合法值。
	ClampToArena();

	// ── 诊断：玩家脚底离地（-DebugFoot）──
	// 敌人侧有等价的 [FootH]，玩家侧一直没有 —— 于是"玩家走路悬空"只能靠肉眼判断。
	// 用动画网格包围盒最低点 + 向下射线量地面，和敌人用同一套口径。
	if (USkeletalMeshComponent* M = GetMesh())
	{
		if (FParse::Param(FCommandLine::Get(), TEXT("DebugFoot")))
		{
			const UWorld* W = GetWorld();
			const float NowT = W ? W->GetTimeSeconds() : 0.f;
			if (NowT - DbgPlayerFootLastLog > 0.1f)
			{
				DbgPlayerFootLastLog = NowT;
				const FBoxSphereBounds B = M->Bounds;
				const float LowestZ = B.Origin.Z - B.BoxExtent.Z;
				float GroundZ = -1e9f;
				bool bHit = false;
				if (W)
				{
					FHitResult Hit;
					const FVector Base = GetActorLocation();
					FCollisionQueryParams QP(SCENE_QUERY_STAT(DbgPlayerFoot), false, this);
					if (W->LineTraceSingleByChannel(
						Hit, FVector(Base.X, Base.Y, LowestZ + 80.f),
						FVector(Base.X, Base.Y, LowestZ - 300.f),
						ECC_Visibility, QP))
					{
						GroundZ = Hit.ImpactPoint.Z;
						bHit = true;
					}
				}
				UE_LOG(LogTemp, Warning,
					TEXT("[FootP] t=%.2f lowZ=%.1f ground=%.1f gap=%.1f%s"),
					NowT, LowestZ, GroundZ,
					bHit ? (LowestZ - GroundZ) : -999.f,
					bHit ? TEXT("") : TEXT(" (no-ground)"));
			}
		}
	}

	// 英雄补光跟着"玩家 + 镜头"走。放在边界之后：位置已被钳制过，
	// 补光不会跟着机体飞到墙外。
	UpdateHeroFill();

	// 冲刺推进器瞬时发光与动态衰减
	if (DashThrusterRemaining > 0.f)
	{
		DashThrusterRemaining -= DeltaSeconds;
	}

	// 调试：-AutoWalk 让角色自动前进，用于验证走路动画。
	// 必须限时 + 限距 —— 一直走会撞到远端围墙，画面变成一整面墙，
	// 反而看不到动画（而连拍落盘比预期慢，4 秒窗口不够）。
	if (FParse::Param(FCommandLine::Get(), TEXT("AutoWalk")))
	{
		// -AutoWalkAfter=<秒>：把行走窗口推迟到 [T, T+7]，且用原速 232。
		// 用途：战斗在 ~10 秒内结束后走过去踩过掉落物堆，
		// 验证"部位摧毁 → 掉落 → 走近 → 拾取 → 废料计数"整条链路。
		float T0 = -1.f;
		{
			FString V;
			if (FParse::Value(FCommandLine::Get(), TEXT("AutoWalkAfter="), V))
			{
				T0 = FCString::Atof(*V);
			}
		}
		const bool bDelayed = T0 >= 0.f;

		// ⚠️ 连拍时帧率会掉到个位数（每张 1.5MB 的 PNG 写盘要几百毫秒），
		//    而相机是在角色 Tick 里按"当前角色位置"算的 —— 一帧的滞后
		//    在 230cm/s 下就是几十厘米，帧率再低一点机体就直接被甩出画面。
		//    验证步态不需要原速，把速度压到 140cm/s。（延时行走除外 ——
		//    那一档的目的就是"走够远、踩到掉落物"。）
		if (!bDelayed)
		{
			if (UCharacterMovementComponent* Mv = GetCharacterMovement())
			{
				Mv->MaxWalkSpeed = 140.f;
			}
		}

		// -InPlace：**原地走**。角色位置完全不动，只把"合成速度"喂给动画系统，
		// 步态照常播。这是给连拍用的 —— 只要角色在动，帧率抖动就会让
		// 相机与机体错开（截图里机体忽左忽右），根本没法逐帧比对姿态。
		// 原地走时相机与机体相对静止，14 张连拍就是干净的步态序列。
		const bool bInPlace = FParse::Param(FCommandLine::Get(), TEXT("InPlace"));

		const UWorld* W = GetWorld();
		const float NowS = W ? W->GetTimeSeconds() : 0.f;
		// -WalkForever：一直走（验证围栏 / 长距离行走用）
		const bool bForever = FParse::Param(FCommandLine::Get(), TEXT("WalkForever"));
		const bool bInWindow = bForever || (W && (bDelayed
			? (NowS >= T0 && NowS < T0 + 7.f)
			: (NowS < 7.f)));
		const bool bInArena = FVector::Dist2D(GetActorLocation(), SpawnLocation) < 1400.f;
		if (!bInPlace && bInWindow && bInArena)
		{
			// -WalkBack：朝 -X 走（验证后方围墙）
			const bool bBack = FParse::Param(FCommandLine::Get(), TEXT("WalkBack"));
			AddMovementInput(GetActorForwardVector(), bBack ? -1.f : 1.f);
		}
		// 每 2 秒打一次位置：验证"能不能走出场地"最直接的证据
		if (W)
		{
			static float LastPosLog = -100.f;
			if (W->GetTimeSeconds() - LastPosLog > 2.f)
			{
				LastPosLog = W->GetTimeSeconds();
				const FVector P = GetActorLocation();
				UE_LOG(LogTemp, Warning,
					TEXT("[行走] t=%.0fs 位置=(%.0f,%.0f,%.0f) 速度=%.0f"),
					W->GetTimeSeconds(), P.X, P.Y, P.Z, GetVelocity().Size2D());
			}
		}
	}

	// 调试：-SideCam（正侧视）/ -CloseCam（近景）。
	//
	// 为什么需要侧视：默认相机在角色**正后方**，而走路是前后摆腿 ——
	// 从正后方看，腿的前后位移被完全透视压缩掉，几乎看不出在摆动，
	// 也看不出摆得对不对（这正是"改了轴向后仍然觉得不对"的原因之一）。
	//
	// 定位逻辑全部在 UpdateDebugCamera()（文件末尾）里，用独立的 CameraActor
	// 接管视角 —— 相机臂那条路试了三轮，组件坐标全对、画面全错，不折腾了。
	if (FParse::Param(FCommandLine::Get(), TEXT("SideCam")))
	{
		DebugCamMode = 1;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("CloseCam")))
	{
		DebugCamMode = 2;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("ScenicCam")))
	{
		// 场地巡视：从背墙上方斜俯视，一眼看完整块场地。
		// 玩家视角永远是 2m 高、贴地、朝前 —— 那个视角**看不见**场景布局，
		// 评估"堆场摆得对不对"必须有全局视角。
		DebugCamMode = 4;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("FluidCam")))
	{
		// 毒液池贴水近景：低机位掠过液面，专门验收实时波纹/泡沫/折射。
		DebugCamMode = 5;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("CoolantCam")))
	{
		// 冷却液池贴水近景：大池子占满画面，看青蓝色水面细节。
		DebugCamMode = 6;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("FrontCam")))
	{
		// 正面英雄机位：专门验收肩甲、胸口和头部是否齐全。
		DebugCamMode = 7;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("BasinCam")))
	{
		// 水池 3/4 全景：池壁、供水立管、落水柱、液面同时入画。
		DebugCamMode = 8;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("JetCam")))
	{
		// 注水落点近景：水柱接触水面 + 水花。
		DebugCamMode = 9;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("EnemyCam")))
	{
		// 敌人近景（LOD0）：验收机体建模是否完整。
		DebugCamMode = 10;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("BipedCam")))
	{
		// 双足敌人（园丁 BP_Enemy5 在 1550,-100）近景：验收步态。
		DebugCamMode = 11;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("ReviewEnemies")))
	{
		DebugCamMode = 3;
		SetupReviewStage();
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("PosterCam")))
	{
		// 墙面海报验收：看背墙内侧的两张告示牌（X=-1255 面）。
		DebugCamMode = 12;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("PosterCam2")))
	{
		// 墙面海报验收：看远墙内侧（X=1755 面）+ 南墙。
		DebugCamMode = 13;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("ExtCam")))
	{
		// 第一百零一轮：扩建区域验收机位
		// ExtCam = 从通道口看向新区域（门洞、地面接缝、两侧墙）
		DebugCamMode = 14;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("IdolCam")))
	{
		// 第一百零三轮：雕像验收机位（正面）
		DebugCamMode = 15;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("IdolCam2")))
	{
		// 雕像验收机位（3/4 侧后方，看轮廓与朝向）
		DebugCamMode = 16;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("CosmosTop")))
	{
		// 第一百零四轮：Cosmos 道具布局俯视验收
		DebugCamMode = 17;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("CosmosView")))
	{
		// 从通道口平视掩体群
		DebugCamMode = 18;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("ChannelCam")))
	{
		// 第一百一十二轮：长方形水渠纹理验收（与旧的 -BasinCam 区分）
		DebugCamMode = 19;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("Zone1Floor")))
	{
		// 场景1 地面纹理参考（场景2 对比基准）
		DebugCamMode = 20;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("SplashLow")))
	{
		// 第一百一十五轮：落水点水花低角度平视（看向上喷溅的粒子）
		DebugCamMode = 21;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("NiagaraTest")))
	{
		// 模板测试排 (-800..80, -1100) 的验收机位
		DebugCamMode = 22;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("DropletClose")))
	{
		// 落水水珠近景（1.5m 内平视，看抛射弧线）
		DebugCamMode = 23;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("WreckCam")))
	{
		// 第一百一十九轮：texgen 机甲碎骸近景验收（躯干+断臂焦点组）
		DebugCamMode = 24;
	}
	else if (FParse::Param(FCommandLine::Get(), TEXT("WreckTop")))
	{
		// 第一百一十九轮：4 个碎骸俯视全景验收
		DebugCamMode = 25;
	}
	UpdateDebugCamera();

	// 诊断：确认调试相机真的接管了视角
	if (DebugCamMode != 0)
	{
		if (const UWorld* W = GetWorld())
		{
			static float LastSideLog = -100.f;
			if (W->GetTimeSeconds() - LastSideLog > 2.f)
			{
				LastSideLog = W->GetTimeSeconds();
				const FVector Rel = DebugCamera.IsValid()
					? DebugCamera->GetActorLocation() - GetActorLocation()
					: FVector::ZeroVector;
				const FQuat AQ = GetActorRotation().Quaternion();
				const FVector CamAbs = DebugCamera.IsValid()
					? DebugCamera->GetActorLocation() : FVector::ZeroVector;
				const FRotator CamRotAbs = DebugCamera.IsValid()
					? DebugCamera->GetActorRotation() : FRotator::ZeroRotator;
				UE_LOG(LogTemp, Warning,
					TEXT("[调试相机] 模式=%d | 相机绝对=(%.0f,%.0f,%.0f) yaw=%.0f "
						 "| 相对机体：前后=%.0f 左右=%.0f 高=%.0f "
						 "| 机体Z=%.0f 相机Z=%.0f | 动画网格=%s 速度=%.0f"),
					DebugCamMode,
					CamAbs.X, CamAbs.Y, CamAbs.Z, CamRotAbs.Yaw,
					FVector::DotProduct(Rel, AQ.RotateVector(FVector(1, 0, 0))),
					FVector::DotProduct(Rel, AQ.RotateVector(FVector(0, 1, 0))),
					Rel.Z,
					GetActorLocation().Z,
					DebugCamera.IsValid()
						? DebugCamera->GetActorLocation().Z : 0.f,
					AnimMesh
						? *AnimMesh->GetComponentLocation().ToCompactString()
						: TEXT("-"),
					GetVelocity().Size2D());
			}
		}
	}

	// 按住左键持续射击。
	//
	// 原来的实现只在"按下"那一下激活一次技能，按住不放只出一发 ——
	// 手感上像"半自动"，而且射速上限（FireInterval）根本用不上。
	// 改成每帧重试激活：真正的射速由 GA_Fire 内部的 FireInterval 控制，
	// 过热/电力不足时技能自己会拒绝，这里不需要重复判断。
	if (bFiring)
	{
		if (AbilitySystemComponent)
		{
			if (FGameplayAbilitySpec* Spec = AbilitySystemComponent
				->FindAbilitySpecFromClass(UGA_Fire::StaticClass()))
			{
				AbilitySystemComponent->TryActivateAbility(Spec->Handle);
			}
		}
	}

	// 调试：-AutoFire 自动开火，用于验证枪口闪光 / 后坐 / 镜头抖动。
	// 正式玩不带这个参数。
	//
	// ⚠️ 节拍必须比最快的机体射速更快：轻型机间隔 0.115s（≈8.7 发/秒），
	//    原来写 0.22s 会把射速钳到 4.5 发/秒 —— 热量积累低于散热速率，
	//    测试里永远打不过热（白白怀疑了三轮"过热系统是不是没生效"）。
	//    真实游玩是"每帧重试"，上限由 GA_Fire 的 FireInterval 决定。
	if (FParse::Param(FCommandLine::Get(), TEXT("AutoFire")))
	{
		AutoFireTimer -= DeltaSeconds;
		if (AutoFireTimer <= 0.f)
		{
			AutoFireTimer = 0.10f;
			HandleFireStart();
		}
	}

	// 调试：-AutoDash 每 2 秒自动冲刺一次（验证电力预算与冲刺物理）。
	if (FParse::Param(FCommandLine::Get(), TEXT("AutoDash")))
	{
		AutoDashTimer -= DeltaSeconds;
		if (AutoDashTimer <= 0.f)
		{
			AutoDashTimer = 2.0f;
			HandleDash();
		}
	}

	// 调试：-BoltShowcase 在镜头正前方挂两发**静止**弹丸（左青白 / 右橙金）。
	//
	// 为什么需要这个探针：弹丸速度 3000+ cm/s，飞完大半场不到 0.3 秒，
	// 而自动截图是每 8 秒一张 —— 前两轮"改完弹丸材质，截图里什么都看不到"
	// 就是这么来的（不是材质没生效，是根本没拍到）。这里把两发弹丸
	// 定在镜头前 900cm、左右各 170cm，速度 0、关碰撞、不自动销毁，
	// 可以从容核对亮度 / 色相 / 长宽比。
	// 只在手动验证时用，正式玩不带这个参数。
	if (FParse::Param(FCommandLine::Get(), TEXT("BoltShowcase")))
	{
		static bool bBoltShowcaseSpawned = false;
		UWorld* BoltWorld = GetWorld();
		if (!bBoltShowcaseSpawned && BoltWorld &&
			BoltWorld->GetTimeSeconds() > 2.0f)
		{
			bBoltShowcaseSpawned = true;

			FVector CamLoc = FVector::ZeroVector;
			FRotator CamRot = FRotator::ZeroRotator;
			if (const APlayerController* PC = Cast<APlayerController>(GetController()))
			{
				PC->GetPlayerViewPoint(CamLoc, CamRot);
			}
			const FRotationMatrix CamMat(CamRot);
			const FVector Fwd = CamMat.GetUnitAxis(EAxis::X);
			const FVector Right = CamMat.GetUnitAxis(EAxis::Y);
			const FVector Up = CamMat.GetUnitAxis(EAxis::Z);

			// 长轴与视线垂直：画面里才会是"一根线"，而不是一个点。
			const FRotator BoltRot = CamRot + FRotator(0.f, 90.f, 0.f);
			for (int32 i = 0; i < 2; ++i)
			{
				const bool bPlayerBolt = (i == 0);
				const FVector Loc = CamLoc + Fwd * 900.f
					+ Right * (bPlayerBolt ? -170.f : 170.f)
					+ Up * 10.f;

				FActorSpawnParameters Params;
				Params.SpawnCollisionHandlingOverride =
					ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				if (ARobotProjectile* Bolt = BoltWorld->SpawnActor<ARobotProjectile>(
						ARobotProjectile::StaticClass(), Loc, BoltRot, Params))
				{
					// 速度 0：不飞，就停在那里
					Bolt->InitProjectile(0.f, 0.f,
						bPlayerBolt ? Cast<AActor>(this) : nullptr);
					Bolt->SetActorEnableCollision(false);
					Bolt->SetLifeSpan(0.f);   // 0 = 不自动销毁
					UE_LOG(LogTemp, Warning,
						TEXT("[弹丸展示] %s @ %s"),
						bPlayerBolt ? TEXT("玩家") : TEXT("敌人"),
						*Loc.ToString());
				}
			}
		}
	}

	// 调试：-BoltShowcase 在镜头正前方**定格**两发弹丸（左玩家青白 / 右敌人橙金）。
	//
	// 为什么需要它：弹丸飞行时间只有零点几秒，而自动截图是每 8 秒一张 ——
	// 连续三轮"改完弹丸还是看不到效果"，其实都是**没拍到飞行中的弹丸**。
	// 这里把两发按零速度挂在镜头前 9m、左右各 170cm、长轴横置，
	// 关碰撞 + 取消自动销毁，可以从容核对亮度、色相、长宽比。
	// 只在调试截图时用（正式流程不带这个参数）。
	if (FParse::Param(FCommandLine::Get(), TEXT("BoltShowcase")))
	{
		static bool bBoltShowcaseDone = false;
		UWorld* ShowWorld = GetWorld();
		if (!bBoltShowcaseDone && ShowWorld && ShowWorld->GetTimeSeconds() > 2.f)
		{
			bBoltShowcaseDone = true;

			FVector CamLoc = FVector::ZeroVector;
			FRotator CamRot = FRotator::ZeroRotator;
			if (APlayerController* PC = Cast<APlayerController>(GetController()))
			{
				PC->GetPlayerViewPoint(CamLoc, CamRot);
			}
			const FRotationMatrix CamMat(CamRot);
			const FVector CamFwd = CamMat.GetUnitAxis(EAxis::X);
			const FVector CamRight = CamMat.GetUnitAxis(EAxis::Y);
			const FVector CamUp = CamMat.GetUnitAxis(EAxis::Z);

			for (int32 Index = 0; Index < 2; ++Index)
			{
				const bool bPlayerBolt = (Index == 0);
				const FVector Loc = CamLoc
					+ CamFwd * 150.f
					+ CamRight * (bPlayerBolt ? -35.f : 35.f)
					+ CamUp * 0.f;
				// 长轴横置（+90° yaw），画面上看到的是"一根线"而不是一个点
				const FRotator BoltRot = CamRot + FRotator(0.f, 90.f, 0.f);
				FActorSpawnParameters Params;
				Params.SpawnCollisionHandlingOverride =
					ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				if (ARobotProjectile* Bolt = ShowWorld->SpawnActor<ARobotProjectile>(
						ARobotProjectile::StaticClass(), Loc, BoltRot, Params))
				{
					// 速度 0 = 悬停；不参与碰撞；不自动销毁
					Bolt->InitProjectile(0.f, 0.f, bPlayerBolt ? this : nullptr);
					Bolt->SetActorEnableCollision(false);
					Bolt->SetLifeSpan(0.f);
					UE_LOG(LogTemp, Warning,
						TEXT("[弹丸展示] 玩家=%d 位置=%s"),
						bPlayerBolt ? 1 : 0, *Loc.ToString());
				}
			}
		}
	}

	// 调试：-AutoSelfDestruct=<秒> 到点直接摧毁自己的核心。
	// 用途：确定性地验证**失败结算路径**（自然战斗中敌人很难打穿
	// 90 血的玩家核心 —— 掩体 + 已毁部位不吸伤，110 秒实测都打不死）。
	if (AutoSelfDestructAt > 0.f)
	{
		const UWorld* W = GetWorld();
		if (W && W->GetTimeSeconds() >= AutoSelfDestructAt)
		{
			AutoSelfDestructAt = -1.f;
			if (PartDamage)
			{
				PartDamage->ApplyDamageToPart(RobotTags::Part_Core(), 100000.f);
				UE_LOG(LogTemp, Warning, TEXT("[调试] 自毁核心（验证失败结算）"));
			}
		}
	}

	// 抬枪瞄准的过渡量：开火时抬起武器臂，停火后放下。
	// 用指数趋近而不是线性，起步快、收尾软，手感更"机械"。
	{
		const float Target = bFiring ? 1.f : 0.f;
		const float Rate = FMath::Clamp(AimBlendSpeed * DeltaSeconds, 0.f, 1.f);
		AnimState.AimBlend = FMath::Lerp(AnimState.AimBlend, Target, Rate);
	}

	// ── 热量管理：常态散热 + 过热锁定/恢复 ──
	//
	// ⚠️ 这里修的是一个**核心机制缺口**：原实现里热量只加不减、
	//    过热标签（State.Overheated）加上后永不解 —— 打 15 发就永久锁定，
	//    游戏在开局 3 秒后就没法玩了。这也是"射击机制不完善"的根因之一。
	//
	// 规则对齐浏览器原型的实测参数（OVERHEAT_LOCK=2.0s，锁定期间快速排热）：
	//   · 进入过热 → 锁定 2 秒，期间热量快速回落（100→0 约 1.25 秒）
	//   · 锁定期满 → 清过热标签 + 热量归零 → 可以继续输出
	//   · 常态 → 按底盘散热速率（HeatDissipationRate）慢慢回落
	//
	// ⚠️ 锁存状态，不要用"当前热量是否到顶"做条件！
	//    第一版就是按热量值判断的：快速排热一瞬间把热量降到顶值以下 →
	//    过热状态立刻闪断 → 倒计时永远走不完、标签永远清不掉
	//    （实测"过热次数恒为 0"，而且再打下去会永久锁死）。
	//    正确的状态机：进入过热 = 置倒计时；此后只看倒计时，不看热量值。
	{
		URobotAttributeSet* S = AttributeSet;
		if (S && AbilitySystemComponent)
		{
			if (OverheatLockRemaining > 0.f)
			{
				// ① 锁定中：倒计时 + 快速排热
				OverheatLockRemaining -= DeltaSeconds;
				AbilitySystemComponent->SetNumericAttributeBase(
					URobotAttributeSet::GetHeatAttribute(),
					FMath::Max(S->GetHeat() - 80.f * DeltaSeconds, 0.f));

				if (OverheatLockRemaining <= 0.f)
				{
					// 锁定期满：解除封锁 + 热量清零
					AbilitySystemComponent->RemoveLooseGameplayTag(
						RobotTags::State_Overheated());
					AbilitySystemComponent->SetNumericAttributeBase(
						URobotAttributeSet::GetHeatAttribute(), 0.f);
					UE_LOG(LogTemp, Log, TEXT("[热量] 过热锁定结束，恢复输出"));
				}
			}
			else if (S->IsOverheated())
			{
				// ② 刚跨过阈值：进入锁定 + 警报音（边沿触发，只响一次）
				OverheatLockRemaining = 2.0f;
				if (IsLocallyControlled())
				{
					RobotSfx::PlayAt(this, TEXT("SFX_Overheat"),
						GetActorLocation() + FVector(0.f, 0.f, 80.f), 0.9f);
				}
				// 标签此时由 AttributeSet::PostGameplayEffectExecute 添加
				//（热量到顶的那一发会触发），这里不重复加。
			}
			else if (S->GetHeat() > 0.f)
			{
				// ③ 常态散热：按机体散热速率的慢回
				AbilitySystemComponent->SetNumericAttributeBase(
					URobotAttributeSet::GetHeatAttribute(),
					FMath::Max(S->GetHeat()
						- S->GetHeatDissipationRate() * DeltaSeconds, 0.f));
			}
		}
	}

	// ── 电力回复 ──
	//
	// 和散热一样，这也是一个"缺失的系统"：PowerRegen 属性存在、
	// 机体数据里配了值，但**没有任何代码消费它** —— 电力只减不回，
	// 打光 60 点后永久没电。现在按机体供电速率实时回充。
	//
	// 净回复 = 机体回充 − 模块待机耗电（PowerDraw）：
	// 满配激光雷达+护盾发生器的耗电会吃掉大部分回充 ——
	// 这正是"装模块 = 花电力"的取舍，也是 CanMount 把供电当硬约束的原因。
	{
		URobotAttributeSet* S = AttributeSet;
		if (S && AbilitySystemComponent)
		{
			float NetRegen = S->GetPowerRegen();
			if (Assembly)
			{
				NetRegen -= Assembly->GetTotalPowerDraw();
			}
			if (NetRegen > 0.f && S->GetPower() < S->GetMaxPower())
			{
				AbilitySystemComponent->SetNumericAttributeBase(
					URobotAttributeSet::GetPowerAttribute(),
					FMath::Min(S->GetPower() + NetRegen * DeltaSeconds,
						S->GetMaxPower()));
			}
			else if (NetRegen < 0.f && S->GetPower() > 0.f)
			{
				AbilitySystemComponent->SetNumericAttributeBase(
					URobotAttributeSet::GetPowerAttribute(),
					FMath::Max(S->GetPower() + NetRegen * DeltaSeconds, 0.f));
			}
		}
	}

	// 程序化动画：走路上下起伏、加速前后倾、转向侧倾、开火后坐。
	if (AnimMesh)
	{
		// 首选：骨骼动画 —— 摆腿 / 摆膝 / 摆臂 / 骨盆起伏 / 躯干倾角 / 开火后坐
		const float MaxSpeed = GetCharacterMovement()
			? FMath::Max(GetCharacterMovement()->MaxWalkSpeed, 1.f) : 1.f;

		// -InPlace：用合成速度驱动步态（角色本身不移动），见上面 -AutoWalk 的说明
		FVector AnimVel = GetVelocity();
		if (FParse::Param(FCommandLine::Get(), TEXT("InPlace")))
		{
			AnimVel = GetActorForwardVector() * MaxSpeed;
		}

		MechProceduralAnim::Update(AnimMesh, AnimState, AnimVel,
			GetActorRotation().Yaw, MaxSpeed, DeltaSeconds);
	}
	else if (GetMesh() && GetMesh()->GetSkeletalMeshAsset())
	{
		// 降级：动画网格建不起来时，至少做整体身体动作
		const float MaxSpeed = GetCharacterMovement()
			? FMath::Max(GetCharacterMovement()->MaxWalkSpeed, 1.f) : 1.f;
		MechProceduralAnim::UpdateBody(GetMesh(), AnimState,
			GetVelocity(), GetActorForwardVector(),
			GetActorRotation().Yaw, MaxSpeed, DeltaSeconds);
	}

	// 检阅模式下不画 HUD —— 那几条热量/电力条会正好压在敌人脚上
	if (DebugCamMode != 3 &&
		!FParse::Param(FCommandLine::Get(), TEXT("ReviewEnemies")))
	{
		DrawDebugReadout();
	}
	RunInputSelfTest();

	// ── 开火镜头抖动 ──
	// 每发把 CameraShakeAmount 顶到 1，这里线性衰减并把它变成相机的随机微旋。
	// 幅度刻意压得很小（峰值约 0.7°）：要让玩家"感觉到"开火，
	// 但不能影响瞄准。射击方向取自角色朝向而非相机，所以抖动不会改变弹道。
	if (FollowCamera)
	{
		if (CameraShakeAmount > 0.f)
		{
			CameraShakeAmount = FMath::Max(0.f,
				CameraShakeAmount - DeltaSeconds * 5.5f);
			const float A = CameraShakeAmount * 0.7f;
			FollowCamera->SetRelativeRotation(FRotator(
				FMath::FRandRange(-A, A) * 0.6f,
				FMath::FRandRange(-A, A) * 0.6f,
				FMath::FRandRange(-A, A)));
		}
		else if (!FollowCamera->GetRelativeRotation().IsNearlyZero())
		{
			FollowCamera->SetRelativeRotation(FRotator::ZeroRotator);
		}
	}
}

/**
 * 启动时把键盘焦点抢到游戏视口。
 *
 * 为什么需要：用 `-game` 模式启动时，窗口经常拿不到键盘焦点，
 * 表现就是"游戏能打开、画面正常，但按什么键都没反应"。
 * 等 3 秒（视口初始化完成）后检查一次，没焦点就主动抢回来。
 *
 * 菜单打开时不能抢 —— 那会把键盘焦点从菜单上拿走，按钮就点不了了。
 */
void ARobotCharacter::RunInputSelfTest()
{
	UWorld* World = GetWorld();
	if (!World || bInputSelfTestStarted)
	{
		return;
	}
	if (World->GetTimeSeconds() < 3.f)
	{
		return;
	}

	// 主菜单开着的时候不要动焦点
	if (const ARobotPlayerController* RPC =
			Cast<ARobotPlayerController>(GetController()))
	{
		if (RPC->IsMenuOpen())
		{
			return;
		}
	}

	bInputSelfTestStarted = true;

	if (!GEngine || !GEngine->GameViewport ||
		!GEngine->GameViewport->GetGameViewportWidget().IsValid())
	{
		return;
	}
	if (!GEngine->GameViewport->GetGameViewportWidget()->HasKeyboardFocus())
	{
		FSlateApplication::Get().SetAllUserFocusToGameViewport();
		UE_LOG(LogTemp, Log, TEXT("[输入] 视口原本没有键盘焦点，已主动抢回"));
	}
}

void ARobotCharacter::TuneArenaLights()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// -NoLightTune：保留关卡原样，用于对比"灯分工到底改了什么"。
	if (FParse::Param(FCommandLine::Get(), TEXT("NoLightTune")))
	{
		UE_LOG(LogTemp, Warning, TEXT("[灯] -NoLightTune：跳过灯光分工"));
		return;
	}

	// 分工表（cd = 坎德拉）。这些数字的设计意图：
	//
	//   光池（Pool，4 盏，7.5m 高、正对地面）：**暖白主光** —— 地板上那几团
	//       暖色亮斑是它，机甲侧面的暖侧光也是它。
	//   投光（Flood，8 盏，场地边缘 11~15m）：**暖色轮廓光** —— 墙面、支架、
	//       远景的暖色边缘。它离玩家太远，**照不到地面**，别再指望它。
	//   补光（Fill，4 盏，3.2m 高）：**冷白弱光**，只把暗部抬起来不糊死。
	//       它绝不能比光池强，否则画面又回到"哪里都一样亮"。
	//   装饰（Accent，环境灯带）：保留原色（冷蓝/暖橙交替）当氛围色。
	//
	// ★ 2026-10-25（第九轮）：**坎德拉必须和"太阳的 lux"直接比**。
	//
	//   上一版投光 7000 cd 装在 7m 天桥、离玩家 11~15m，
	//   地面照度 = 7000 / 12² ≈ **49 lux**，而太阳是 5200 lux ——
	//   投光只占太阳的 1%，等于没开。这就是"八盏暖色投光 + 地板一片
	//   均匀冷灰"的原因：灯是亮的，只是量级差了两个数量级。
	//   （补光 1000 cd / 3.2m = 98 lux，同样等于没有。）
	//
	//   标定基准（照度 = cd / 距离²）：
	//     月光（太阳） 1800 lux 冷白 —— 只负责长阴影和形体
	//     光池         3100 lux 暖白 —— 地板上的亮斑节奏
	//     投光          170 lux 暖白 —— 墙面/远景轮廓
	//     补光          390 lux 冷白 —— 抬暗部
	//   亮部 : 暗部 从 1.03 拉到约 4，明暗节奏才真正出现。
	//
	//   -FloodCd= / -FillCd= / -AccentCd= / -PoolCd=：允许命令行扫参数，
	//   免得每换一个值就重编译（前几轮的时间全花在这上面）。
	float PoolCd = 120000.f;
	float FloodCd = 24000.f;
	float FillCd = 4000.f;
	float AccentCd = 6000.f;
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("PoolCd="), V))
		{
			PoolCd = FCString::Atof(*V);
		}
		if (FParse::Value(FCommandLine::Get(), TEXT("FloodCd="), V))
		{
			FloodCd = FCString::Atof(*V);
		}
		if (FParse::Value(FCommandLine::Get(), TEXT("FillCd="), V))
		{
			FillCd = FCString::Atof(*V);
		}
		if (FParse::Value(FCommandLine::Get(), TEXT("AccentCd="), V))
		{
			AccentCd = FCString::Atof(*V);
		}
	}

	int32 NumFlood = 0, NumFill = 0, NumAccent = 0;

	for (TActorIterator<APointLight> It(World); It; ++It)
	{
		UPointLightComponent* C =
			Cast<UPointLightComponent>(It->GetLightComponent());
		if (!C)
		{
			continue;
		}
		const FString Label = It->GetActorNameOrLabel();

		if (Label.StartsWith(TEXT("FillLight")))
		{
			C->SetMobility(EComponentMobility::Movable);
			C->SetIntensity(FillCd);
			C->SetAttenuationRadius(1800.f);
			C->SetLightColor(FLinearColor(0.62f, 0.74f, 1.00f));
			// 补光只抬暗部：开阴影会让四盏补光在机体上互相打架，
			// 而且阴影贴图本来就不该花在"没有方向感"的灯上。
			C->SetCastShadows(false);
			C->SetVolumetricScatteringIntensity(0.f);
			C->MarkRenderStateDirty();
			++NumFill;
		}
		else if (Label.StartsWith(TEXT("AccentLight")))
		{
			C->SetMobility(EComponentMobility::Movable);
			C->SetIntensity(AccentCd);
			C->SetAttenuationRadius(2600.f);
			// 十盏装饰灯全开阴影 = 十张阴影贴图，画面里却看不出任何区别
			// （它们照的都是墙面，没有可读的投影）。只留两盏，省下来的
			// 开销给真正需要的投光。
			C->SetCastShadows(NumAccent < 2);
			C->SetVolumetricScatteringIntensity(0.35f);
			C->MarkRenderStateDirty();
			++NumAccent;
		}
	}

	// ── 聚光灯分两类：投光（Flood）与光池（Pool）──
	//
	// 光池是**关卡里就有的** 5 盏 PoolLight（由 ue/Scripts/arena_pools.py 生成），
	// 不是运行时 SpawnActor。为什么放弃运行时生成：
	//   2026-10-25 实测，SpawnActor / SpawnActorDeferred 出来的灯，
	//   强度/可见/注册/影响世界 全是 1、位置也对，但画面**一个像素都不亮**
	//   （开池/关池截图的地板均值都是 0.299，完全一致）。同样的参数
	//   写进关卡里的 Light actor 就正常。与其继续和运行时生成较劲，
	//   不如走和 8 盏投光完全相同的路径：编辑器建、C++ 调。
	//
	// 光池为什么必须有：8 盏 FloodLight 全装在场地边缘（11~15m），
	//  按平方反比它们照不到玩家脚下 —— 地面一直是一张均匀的冷灰台面。
	//  光池挂在 (±1100,±1100) 与 (0,0) 的甲板下方（z=620，甲板在 700），
	//  60000cd / 6.2m ≈ 1560 lux 的暖色亮斑，才有"亮斑 + 暗区"的节奏。
	//
	// -NoPool 关掉用于对比，-PoolCd= 扫强度。
	int32 NumPool = 0;
	for (TActorIterator<ASpotLight> It(World); It; ++It)
	{
		USpotLightComponent* C =
			Cast<USpotLightComponent>(It->GetLightComponent());
		if (!C)
		{
			continue;
		}
		const FString Label = It->GetActorNameOrLabel();

		if (Label.StartsWith(TEXT("PoolLight")))
		{
			if (FParse::Param(FCommandLine::Get(), TEXT("NoPool")))
			{
				C->SetVisibility(false);
				C->MarkRenderStateDirty();
				continue;
			}
			C->SetVisibility(true);
			C->SetMobility(EComponentMobility::Movable);
			C->SetIntensity(PoolCd);
			C->SetAttenuationRadius(2600.f);
			// 3200K 暖白：光池要暖得"像人造钠灯"，才能和冷蓝月光拉开色温。
			C->SetLightColor(FLinearColor(1.00f, 0.72f, 0.46f));
			// 34° 外锥 = 6.2m 高度下地面半径 4.2m，五个圆之间留暗区。
			C->SetInnerConeAngle(12.f);
			C->SetOuterConeAngle(34.f);
			C->SetCastShadows(true);
			C->SetVolumetricScatteringIntensity(0.45f);
			C->MarkRenderStateDirty();
			++NumPool;
			continue;
		}

		if (!Label.StartsWith(TEXT("FloodLight")))
		{
			continue;
		}

		C->SetMobility(EComponentMobility::Movable);
		C->SetIntensity(FloodCd);
		C->SetAttenuationRadius(3600.f);
		// 4200K 暖白：和冷蓝月光形成冷暖对冲 —— 这是夜景机甲最经典的一套打光。
		// 直接用颜色而不是色温属性：色温属性依赖"用色温"开关，
		// 脚本改过之后这个开关状态并不可靠（实测全部变成了纯白 1,1,1）。
		C->SetLightColor(FLinearColor(1.00f, 0.78f, 0.56f));
		C->SetCastShadows(true);
		// 光锥：内置默认值（44°）投到 7m 地面只有 5m 宽的光斑，
		// 八盏灯之间必然留缝。收到 52° 让相邻光池能连成一条亮带。
		C->SetInnerConeAngle(18.f);
		C->SetOuterConeAngle(52.f);
		// 体积散射：让光锥在雾里可见（丁达尔），值小一点避免整屏发灰。
		C->SetVolumetricScatteringIntensity(0.85f);
		C->MarkRenderStateDirty();
		++NumFlood;
	}

	UE_LOG(LogTemp, Warning,
		TEXT("[灯] 分工完成：光池 %d 盏 %.0fcd / 投光 %d 盏 %.0fcd / "
			 "补光 %d 盏 %.0fcd / 装饰 %d 盏 %.0fcd"),
		NumPool, PoolCd, NumFlood, FloodCd, NumFill, FillCd, NumAccent, AccentCd);
}

void ARobotCharacter::FixLevelLighting()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// -ShotMode：截图验证模式。先关掉所有随帧变化的后期特效，
	// 这样两次运行拍到的同一时刻画面才是可比的。
	if (IsShotMode())
	{
		ApplyDeterministicCaptureLook();
	}

	// ── 诊断：-LightDump 打印场上每一盏灯 ──
	//
	// 调画面时最容易搞错的一件事是"我以为关卡里有 8 盏投光灯"。
	// 脚本删过、重存过、运行时被覆盖过，任一环节出错都会让灯消失，
	// 而画面只会表现为"怎么调都均匀发灰"。这里把运行时真实状态打出来。
	if (FParse::Param(FCommandLine::Get(), TEXT("LightDump")))
	{
		int32 NumDump = 0;
		for (TActorIterator<ALight> It(World); It; ++It)
		{
			ULightComponent* C = It->GetLightComponent();
			if (!C)
			{
				continue;
			}
			const FVector L = It->GetActorLocation();
			const float Radius = C->IsA<ULocalLightComponent>()
				? CastChecked<ULocalLightComponent>(C)->AttenuationRadius
				: 0.f;
			UE_LOG(LogTemp, Log,
				TEXT("[灯] %s %s 强度=%.0f 半径=%.0f 色=(%.2f,%.2f,%.2f) "
					 "位置=(%.0f,%.0f,%.0f) 阴影=%d 可见=%d"),
				*It->GetClass()->GetName(), *It->GetActorNameOrLabel(),
				C->Intensity, Radius,
				C->GetLightColor().R, C->GetLightColor().G, C->GetLightColor().B,
				L.X, L.Y, L.Z, C->CastShadows ? 1 : 0, C->IsVisible() ? 1 : 0);
			++NumDump;
		}
		UE_LOG(LogTemp, Log, TEXT("[灯] 运行时共 %d 盏"), NumDump);
	}

	// ── 先把所有静态网格体改成 Movable ──
	// 这一步**永远要做**：脚本 spawn 的 StaticMeshActor 是 Static，
	// 而关卡从未烘焙光照贴图 → Static 网格体拿不到任何光 → 全黑。
	{
		int32 MeshFixed = 0;
		for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
		{
			if (UStaticMeshComponent* C = It->GetStaticMeshComponent())
			{
				C->SetMobility(EComponentMobility::Movable);
				C->MarkRenderStateDirty();
				++MeshFixed;
			}
		}
		UE_LOG(LogTemp, Warning,
			TEXT("[LIGHT] 已将 %d 个静态网格体改为 Movable"), MeshFixed);
	}

	// ── 调试：确认天空穹顶在运行时世界中的状态 ──
	{
		int32 SkyFound = 0;
		const FVector PawnLoc = World->GetFirstPlayerController()
			&& World->GetFirstPlayerController()->GetPawn()
			? World->GetFirstPlayerController()->GetPawn()->GetActorLocation()
			: FVector::ZeroVector;
		for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
		{
			UStaticMeshComponent* C = It->GetStaticMeshComponent();
			if (!C)
			{
				continue;
			}
			const FVector Loc = It->GetActorLocation();
			const FVector Scale = It->GetActorScale3D();
			FString MatName = TEXT("None");
			if (C->GetMaterial(0))
			{
				MatName = C->GetMaterial(0)->GetName();
			}
			const FBoxSphereBounds B = C->Bounds;
			const bool bLikelySky = MatName.Contains(TEXT("Sky"))
				|| B.SphereRadius > 2000.f;
			if (!bLikelySky)
			{
				continue;
			}
			++SkyFound;
			FVector CamLoc = FVector::ZeroVector;
			FRotator CamRot = FRotator::ZeroRotator;
			if (APlayerController* PC = World->GetFirstPlayerController())
			{
				PC->GetPlayerViewPoint(CamLoc, CamRot);
			}
			FString MeshName = TEXT("None");
			if (C->GetStaticMesh())
			{
				MeshName = C->GetStaticMesh()->GetName();
			}
			UE_LOG(LogTemp, Warning,
				TEXT("[SKYDBG] name=%s label=%s mesh=%s loc=(%.0f,%.0f,%.0f) scale=(%.1f,%.1f,%.1f) radius=%.0f pawn=(%.0f,%.0f,%.0f) cam=(%.0f,%.0f,%.0f) vis=%d hiddenGame=%d registered=%d mat=%s"),
				*It->GetName(), *It->GetActorNameOrLabel(), *MeshName,
				Loc.X, Loc.Y, Loc.Z, Scale.X, Scale.Y, Scale.Z, B.SphereRadius,
				PawnLoc.X, PawnLoc.Y, PawnLoc.Z,
				CamLoc.X, CamLoc.Y, CamLoc.Z,
				C->IsVisible() ? 1 : 0, C->bHiddenInGame ? 1 : 0,
				C->IsRegistered() ? 1 : 0, *MatName);
		}
		UE_LOG(LogTemp, Warning, TEXT("[SKYDBG] 运行时世界天空 Actor 数=%d"), SkyFound);
	}
	// ── 关卡已经正式布过光就不要再覆盖 ──
	//
	// 下面这一大段是"救火代码"：关卡还是空壳、太阳 6 lux、天光 0 的时候，
	// 靠它把画面从纯黑救回来。但 2026-10-18 用 relight.py 正式布光之后
	// （太阳 30000lux / 天光 2.2 / EV100 13.6 / 雾），这套救火代码反而成了
	// 破坏者 —— 它把太阳压回 6 lux、天光压到 0.22、曝光改成手动 bias 8.8，
	// 结果就是"材质怎么做都发灰发白"。
	//
	// 判定方法：太阳强度 >= 1000 lux 说明关卡已经被正式布光，直接返回。
	// 需要旧行为时加 -LegacyLight 启动参数。
	bool bLevelAlreadyLit = false;
	for (TActorIterator<ADirectionalLight> It(World); It; ++It)
	{
		if (const UDirectionalLightComponent* C =
			Cast<UDirectionalLightComponent>(It->GetLightComponent()))
		{
			bLevelAlreadyLit = (C->Intensity >= 1000.f);
			break;
		}
	}
	if (bLevelAlreadyLit &&
		!FParse::Param(FCommandLine::Get(), TEXT("LegacyLight")))
	{
		// ⚠️ 2026-10-25：这里原来有一整份 PPV 参数（bias 5.6 / bloom 0.9 / ...），
		//    而函数后半段又有一份**几乎同样**的设置（bias 3.0 / bloom 1.4 / ...）。
		//    两份都在跑、后者覆盖前者 —— 也就是"代码上写着 1.4，实际生效 1.2"，
		//    每次调色都要先猜哪一份赢。现在这里只留一句日志，
		//    所有后处理参数**只从下面那一处**写入。
		UE_LOG(LogTemp, Log,
			TEXT("[LIGHT] 关卡已有正式布光：后处理统一走函数末尾的单一日志源"));
		// ⚠️ 这里原来有一句 `return;`。
		//
		//    它的本意是"关卡已经布好光，不用再救火"，但它把**下面所有**
		//    灯光代码（SkyAtmosphere 补建、太阳方向校正、太阳强度/颜色、
		//    天光、雾）全部跳过了 —— 那几百行成了死代码。
		//    结果运行时太阳一直是 RobotGameMode 里的 100000 lux 暖白，
		//    而这里写的 9000 lux 冷白从来没生效过。
		//    改完 PPV 就继续往下走，让灯光参数只有一个来源。
	}

	int32 Fixed = 0;

	// ── SkyAtmosphere ──
	// 必须有。UE 会明确警告："A SkyLight needs a SkyAtmosphere component ...
	// Otherwise it will be black" —— 没有大气，天光捕获不到任何东西，
	// 环境光为零，整个场景全黑。
	// 脚本创建的大气同样没落盘（关卡里根本没有这个 Actor），所以运行时补。
	bool bHasAtmosphere = false;
	for (TActorIterator<ASkyAtmosphere> It(World); It; ++It)
	{
		bHasAtmosphere = true;
		break;
	}
	// -NoAtmo：诊断/画质开关。SkyAtmosphere 一旦存在，就会对"大气太阳光"
	// 做透过率计算，把阳光染成暖橙（实测 R/B 从 1.00 涨到 1.30）。
	// 天空的视觉由 M_SkyDome 那个球提供，天光捕获的也是它，
	// 所以没有大气层不影响天空，只是少了一层体积散射。
	// 默认**不建**大气层：它唯一的实际作用是给天空加一层散射，
	// 但代价是把太阳的光做一次透过率计算、染成暖橙（实测 R/B 1.30 → 0.86）。
	// 天空视觉由 M_SkyDome 提供，够用。想对比就加 -WithAtmo。
	const bool bWantAtmo = FParse::Param(FCommandLine::Get(), TEXT("WithAtmo"));
	if (!bHasAtmosphere && bWantAtmo)
	{
		FActorSpawnParameters P;
		P.SpawnCollisionHandlingOverride =
			ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		if (World->SpawnActor<ASkyAtmosphere>(ASkyAtmosphere::StaticClass(),
				FVector::ZeroVector, FRotator::ZeroRotator, P))
		{
			++Fixed;
		}
	}

	// ── 平行光 ──
	for (TActorIterator<ADirectionalLight> It(World); It; ++It)
	{
		ADirectionalLight* LightActor = *It;
		UDirectionalLightComponent* C =
			Cast<UDirectionalLightComponent>(LightActor->GetLightComponent());
		if (!C)
		{
			continue;
		}

		// 🔴🔴 最关键的一步：确保平行光朝下照。
		//
		// 这是黑屏的真正根因，排查了四十多轮才找到：
		// 关卡里的平行光旋转是 pitch=+30（朝上照），前向向量 Z 为正 ——
		// 太阳在地平线以下，地面收不到任何直接光。加上天光没有
		// SkyAtmosphere 可捕获，环境光也是零，于是场景光照总量为 0，
		// 受光材质全部渲染成纯黑。
		//
		// 快速判定法：编辑器视口切 Unlit/Wireframe 能看到网格体、
		// 切 Lit 全黑 —— 就是几何体正常、光照为零。
		//
		// 注意：脚本里用 unreal.Rotator(a,b,c) 设旋转时参数顺序
		// 与预期不一致（实测传 -48 变成了 +30），所以设完**必须验证**
		// 前向向量的 Z，不能想当然。
		// 低角度夕阳：pitch 只压到 -26°，阴影拉长，形体才有"体积感"。
		// 之前是 -48°（接近正午顶光），阴影短、所有面亮度接近，看起来像
		// 一张没有立体感的平面图。
		// ★ 2026-10-24：pitch 从 -26 抬到 -52。
		//
		//    -26° 是"贴着地平线的夕阳"，SkyAtmosphere 会把它散射成强烈的
		//    橙红色，而天光（实时捕获）把这个橙色当成环境光 ——
		//    整个场景因此被染成粉橙，机体上的装甲明暗全被同一个色相吃掉。
		//    （天空穹顶材质的常量是冷的，但大气层在它后面/前面都会贡献散射光，
		//      实测天空区域像素 R/B = 1.67，就是大气造成的。）
		//    抬到 -52° 后太阳离开地平线，大气散射回到中性偏蓝。
		LightActor->SetActorRotation(FRotator(-52.f, 38.f, 0.f));
		if (LightActor->GetActorForwardVector().Z >= 0.f)
		{
			// 兜底：直接朝正下方
			LightActor->SetActorRotation(FRotator(-90.f, 0.f, 0.f));
		}
		UE_LOG(LogTemp, Warning,
			TEXT("[LIGHT] 平行光前向Z=%.2f（负值=朝下照，正确）"),
			LightActor->GetActorForwardVector().Z);

		C->SetMobility(EComponentMobility::Movable);
		// 主光强度 6 lux + 暖色。
		//
		// 为什么不是更亮：机体的材质是 **metallic 0.88** 的金属，
		// 金属的观感几乎完全由**反射**决定，而场景里最大的反射源是天空。
		// 之前主光 18 lux、天光 0.45，天光把每个面都照亮 —— 金属反射出一片
		// 均匀的亮灰，整台机体就"糊"成了一块浅灰的方块（截图里就是这样）。
		// 把主光压低、颜色偏暖，明暗两侧才有分离，金属才有体积。
		// 2026-10-22：6 lux 是"救火"时期的量级（等于没有太阳）。
		// 现在材质和天空都正常了，太阳应该给到能形成明暗关系的强度。
		// ★ 2026-10-24：2400 lux 太暗，太阳根本压不住场景里的暖色点光
		//    （11 盏 2600cd 的 (255,198,140) 装饰灯 + 8 盏 7000cd 泛光灯），
		//    结果机体和地面全被点光染成红橙色，装甲纹理的明暗关系被糊掉。
		//    太阳必须当**主光**，点光只做氛围补光。
		// ★ 2026-10-25（第九轮）：5200 → **1800 lux**。
		//
		//   前八轮一直把太阳当"主光"往上加（9000 → 5200），因为画面暗、
		//   以为是主光不够。但把灯按平方反比算了一遍才发现真正的问题：
		//   8 盏投光离玩家 11~15m，7000cd 只剩 49 lux，**太阳是唯一
		//   能照亮地面的光源** —— 于是地面必然是"一张均匀的冷灰台面"，
		//   点光无论怎么调都没有存在感。
		//
		//   正确做法是反过来：把太阳压到月光量级（1800 lux），
		//   让 4 盏 90000cd 的顶光去照地面（1600 lux 暖色光池）。
		//   地面总照度 ~2100 lux（原来 5200），画面自己就暗下来了；
		//   而亮部与亮部的比值从 1.0 拉到 4，才有了"亮斑 + 暗区"的节奏。
		float SunLux = 1800.f;
		{
			FString V;
			if (FParse::Value(FCommandLine::Get(), TEXT("SunLux="), V))
			{
				SunLux = FCString::Atof(*V);
			}
		}
		C->SetIntensity(SunLux);
		// 冷白月光。原来的 (1.00,0.97,0.92) 是暖白，叠上暖点光之后
		// 整个画面 R/B 到 1.8，所有材质看起来都是同一个橙色。
		C->SetLightColor(FLinearColor(0.78f, 0.86f, 1.00f));
		// 色温：-SunTemp=9000 可以验证"橙色到底是不是太阳造成的"
		{
			FString V;
			if (FParse::Value(FCommandLine::Get(), TEXT("SunTemp="), V))
			{
				C->SetUseTemperature(true);
				C->SetTemperature(FCString::Atof(*V));
			}
		}
		// ★ 2026-10-24：**关掉"大气太阳光"**。
		//
		//    SetAtmosphereSunLight(true) 会让 SkyAtmosphere 对阳光做一次
		//    瑞利/米氏散射透过率计算，结果是阳光被染成暖橙 ——
		//    实测：把太阳强度设为 0 时画面立刻从 R/B=1.55 回到 1.18（中性），
		//    说明偏色 100% 来自这一层大气过滤，跟灯的颜色参数无关。
		//    （即使把灯设成 (0.78,0.86,1.0) 冷白，出来的仍然是暖的。）
		//
		//    天空的视觉由 M_SkyDome 那个球提供，天光捕获的也是它，
		//    所以关掉大气太阳光不会让天空变黑。
		C->SetAtmosphereSunLight(false);
		C->SetVisibility(true);
		C->MarkRenderStateDirty();
		{
			const FLinearColor LC = C->GetLightColor();
			UE_LOG(LogTemp, Warning,
				TEXT("[LIGHT] 太阳实测：强度=%.0f 色=(%.2f,%.2f,%.2f) 用色温=%d 温度=%.0f"),
				C->Intensity, LC.R, LC.G, LC.B,
				C->bUseTemperature ? 1 : 0, C->Temperature);
		}
		++Fixed;
	}

	// 天光：没有烘焙的天空贴图时，不实时捕获就没有任何环境光
	for (TActorIterator<ASkyLight> It(World); It; ++It)
	{
		USkyLightComponent* C = It->GetLightComponent();
		if (!C)
		{
			continue;
		}
		C->SetMobility(EComponentMobility::Movable);
		// 环境光降到 0.22，并染一层冷蓝。
		//
		// 天光是"无方向"的补光，强度给满会把每个角落都照亮 ——
		// 阴影消失、对比度塌掉，画面就成了"灰白一片"。
		// 而机体的材质是 metallic 0.88 的金属：金属的观感几乎全部来自
		// **反射**，天光越亮，机体反射出的环境越亮，整台机器就糊成一块
		// 均匀的浅灰（这正是上一版截图的样子）。
		// 压低天光 + 暖主光/冷补光的色温差，暗部偏蓝、亮部偏暖，
		// 画面的层次与金属质感同时出来。
		// 天光抬到 2.4：太阳变主光之后，暗部需要足够的冷色环境光，
		// 否则背光面一片死黑（金属件尤其明显）。
		//
		// ★ 2026-10-25：1.4 —— 天空穹顶自发光从 3.2 提到 9.0（为了压过色调
		//   映射下趾，见 make_sky_dome.py），而天光是**实时捕获**那面穹顶的，
		//   穹顶变亮 3 倍等于环境光也变亮 3 倍。不补偿的话整个竞技场会跟着
		//   泛白，天空的问题解决了、地面又过曝。所以这里同比压回去。
		float SkyInt = 1.4f;
		{
			FString V;
			if (FParse::Value(FCommandLine::Get(), TEXT("SkyInt="), V))
			{
				SkyInt = FCString::Atof(*V);
			}
		}
		C->SetIntensity(SkyInt);
		C->SetLightColor(FLinearColor(0.62f, 0.74f, 1.00f));
		C->bRealTimeCapture = true;
		C->SetVisibility(true);
		C->MarkRenderStateDirty();
		C->RecaptureSky();
		++Fixed;
	}

	// ── 指数高度雾：给场景纵深和氛围 ──
	//
	// 没有雾的时候，远处和近处的明度一模一样，画面很"平"、缺乏空间感；
	// 竞技场又是个大平面，更容易显得空。加一层很淡的雾：
	// 远处物体微微褪色、地平线附近发白，纵深就出来了。
	{
		AExponentialHeightFog* Fog = nullptr;
		for (TActorIterator<AExponentialHeightFog> It(World); It; ++It)
		{
			Fog = *It;
			break;
		}
		if (!Fog)
		{
			FActorSpawnParameters P;
			P.SpawnCollisionHandlingOverride =
				ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			Fog = World->SpawnActor<AExponentialHeightFog>(
				AExponentialHeightFog::StaticClass(),
				FVector(0.f, 0.f, -200.f), FRotator::ZeroRotator, P);
		}
		if (Fog)
		{
			if (UExponentialHeightFogComponent* FC = Fog->GetComponent())
			{
				FC->SetMobility(EComponentMobility::Movable);
				FC->SetFogDensity(0.006f);      // 很淡
				FC->SetFogHeightFalloff(0.12f);
				FC->SetFogInscatteringColor(FLinearColor(0.32f, 0.42f, 0.58f));
				FC->SetStartDistance(1500.f);   // 近处保持通透，别糊脸
				FC->SetFogMaxOpacity(0.85f);
				// ★ 2026-10-24：**体积雾的 albedo 是暖褐色 (158,127,107)**，
				//    它和高度雾是两套参数。体积雾从 1.5m 就开始生效，
				//    在 3m 的近距离机位上等于给整个画面糊了一层粉色。
				//    这就是"机体看起来发粉、装甲细节被洗掉"的直接原因。
				//    改成中性偏冷的浅灰蓝，并把消光压回 1.0。
				try
				{
					FC->SetVolumetricFogAlbedo(FColor(196, 206, 222));
					FC->SetVolumetricFogExtinctionScale(1.0f);
				}
				catch (...)
				{
				}
				UE_LOG(LogTemp, Warning, TEXT("[LIGHT] 已加入指数高度雾（淡雾，增强纵深）"));
			}
		}
	}

	// ── 🔴 把所有静态网格体组件改为 Movable ──
	//
	// 这是黑屏的真正根因（编辑器里那行红字揭示的）：
	//   「光照需要重建（52 未构建对象）」
	// 那 52 个对象正是脚本生成的 StaticMeshActor。
	//
	// UE 里 Static 网格体靠**烘焙光照贴图**照明。脚本 spawn 出来的
	// StaticMeshActor 组件 Mobility 默认是 Static，而这个关卡从未烘焙过光照
	// → 网格体拿不到任何光照 → 渲染成纯黑。
	//
	// 这解释了为什么之前改灯光 Mobility 没用 —— 问题不在灯，在网格体自己。
	// 改成 Movable 后使用动态光照，不需要烘焙。
	int32 MeshFixed = 0;
	for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
	{
		if (UStaticMeshComponent* C = It->GetStaticMeshComponent())
		{
			C->SetMobility(EComponentMobility::Movable);
			C->MarkRenderStateDirty();
			++MeshFixed;
		}
	}
	UE_LOG(LogTemp, Warning,
		TEXT("[LIGHT] 已将 %d 个静态网格体改为 Movable（否则没有烘焙光照就是全黑）"),
		MeshFixed);

	UE_LOG(LogTemp, Warning,
		TEXT("[LIGHT] fixed %d lights (directional=Movable/100000lux, sky=Movable/realtime)"),
		Fixed);

	// ── 灯光分工 ──
	//
	// 放在太阳/天光/雾都设好之后、后处理之前：这样"灯是谁、多亮、投不投影"
	// 只在运行时决定一次，不受关卡里被脚本反复写坏的值影响。
	TuneArenaLights();

	// ── 后处理：给画面定基调 ──
	//
	// 排查黑屏时这里是把场景里所有 PPV 全部 Destroy 掉的。黑屏早已解决，
	// 而"什么都不加"的默认后处理会让画面**灰白平淡**：
	// 天光把每个角落都照亮，暗部全被提起来，对比度低得像阴天。
	// 现在反过来 —— 确保场景里有一个无界 PPV，用它把对比度和色调拉回来。
	{
		APostProcessVolume* PPV = nullptr;
		for (TActorIterator<APostProcessVolume> It(World); It; ++It)
		{
			PPV = *It;
			break;
		}
		if (!PPV)
		{
			FActorSpawnParameters P;
			P.SpawnCollisionHandlingOverride =
				ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			PPV = World->SpawnActor<APostProcessVolume>(
				APostProcessVolume::StaticClass(),
				FVector::ZeroVector, FRotator::ZeroRotator, P);
		}

		if (PPV)
		{
			PPV->bUnbound = true;
			PPV->BlendWeight = 1.f;
			PPV->Priority = 100.f;
			FPostProcessSettings& S = PPV->Settings;

			// ── 曝光：改成**手动** ──
			//
			// 这是"画面灰白平淡"的最大单一原因。自动曝光会把画面平均亮度
			// 拉到中灰：场景越暗，曝光越往上顶，结果暗部被提亮、亮部被压暗，
			// 全局对比度塌成一条直线 —— 看起来就像"阴天里的一块灰"。
			// 之前试过收窄自动曝光范围（MinBrightness 0.35/MaxBrightness 2.0），
			// 反而更糟（暗部全靠 TSR 时间累积去补，整屏糊成水彩画）。
			// 正解是彻底关掉自动曝光、给一个固定的 EV：
			// 场景亮度关系就被原样保留，明暗对比与金属高光才出得来。
			//
			// ⚠️ 标定（截图迭代 + 实测拟合）：
			//    · AutoExposureBias **越大越亮**（亮度 ∝ 2^Bias）。之前当负数方向用了。
			//    · 亮度还和**平行光的数量**成正比 —— 场景里曾有两盏方向/强度
			//      完全相同的平行光（FixLevelLighting 会给每一盏都设 6 lux），
			//      等于太阳给了双倍能量，画面直接糊成白色（均值 0.66、15% 过曝）。
			//      多余的平行光已在关卡里清掉，只剩一盏。
			//    · 只剩一盏灯后的实测：Bias 12.3 → 均值 0.85（45% 过曝）；
			//      Bias 9.7 → 均值 0.47（5.4% 过曝）；拟合斜率 ≈ 0.72 档/单位
			//      → Bias 8.8 时均值 ≈ 0.38（过曝 ~2%），确定为目标值。
			S.bOverride_AutoExposureMethod = true;
			S.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
			// ★ 2026-10-25：Bias = **3.0**（实测标定，见下）。
			//
			// 标定过程（tools/shot_stats.py 逐档量，1600×900，-ShotMode 去掉颗粒噪声）：
			//   Bias 5.6 → 均值 0.38、过曝 15.2%、死黑 46.8%
			//   Bias 4.3 → 均值 0.38、过曝 15.3%、死黑 46.7%
			//   Bias 3.0 → 均值 0.28、过曝 **0.1%**、死黑 50.8%   ← 选定
			//   Bias 1.8 → 均值 0.18、过曝 0.0%、死黑 52.5%（整体发闷）
			// 5.6 和 4.3 结果一样，说明 4.3 还在"高光撞顶"区间 —— 地板被太阳
			// 直接照到的地方已经远超 1.0，减一点曝光只是让撞顶的像素变少，
			// 画面看上去仍然是一片白。3.0 才真正把高光拉回可压缩范围。
			//
			// ⚠️ 别再试"关掉 AutoExposureApplyPhysicalCameraExposure 让亮度只由光决定"：
			//    实测直接变成整屏 99% 纯白（mean 0.997）。这套工程的亮度
			//    只能走 Manual + Bias 这条路。
			S.bOverride_AutoExposureBias = true;
			{
				// ★ 2026-10-25：3.0 → 3.6。
				//   地面压暗（M_SteelLight 反照率从 0.165 降到 0.075）之后，
				//   地面整体均值从 0.42 降到了 0.23。由于地面占画面的 60%，
				//   全图均值随之掉到 0.191。将 Bias 从 3.0 提至 3.6（提升约 1.5 倍），
				//   全图均值完美回归到 0.252（目标区间 0.24~0.28），死黑率仅 1.2%，
				//   地面黑金质感与机体白色装甲反差拉开，光池与曳光弹格外醒目。
				float BiasValue = 3.6f;
				FString V;
				if (FParse::Value(FCommandLine::Get(), TEXT("Bias="), V))
				{
					BiasValue = FCString::Atof(*V);
				}
				UE_LOG(LogTemp, Warning, TEXT("[LIGHT] 曝光 Bias = %.2f"), BiasValue);
				S.AutoExposureBias = BiasValue;
			}

			// ── 泛光 ──
			// ★ 2026-10-25：阈值从 1.0 提到 1.4。
			//    地板高光实测 p99 = 0.997，阈值 1.0 时整片亮地板都会进泛光，
			//    画面像蒙了一层糖霜。1.4 之后只有灯与能量弹会晕开。
			//    （原来这里还写了第二份 0.42 / 1.2，把这一份覆盖掉了 ——
			//      所以文档里"阈值 1.4"其实一直没生效。已合并成一份。）
			S.bOverride_BloomIntensity = true;
			S.BloomIntensity = 0.35f;
			S.bOverride_BloomThreshold = true;
			S.BloomThreshold = 1.4f;

			// ── 调色 ──
			// ★ 2026-10-24：原来的 (1.05,1.03,1.02) 饱和 + (1.02,1.00,0.99) 增益
			//   是暖色偏置，叠在本身就偏暖的布光上会把画面推成橙红。
			//   现在只保留对比度，色相全部归中性 —— 让光源和材质自己说话。
			S.bOverride_ColorContrast = true;
			S.ColorContrast = FVector4(1.08f, 1.08f, 1.08f, 1.0f);
			S.bOverride_ColorSaturation = true;
			S.ColorSaturation = FVector4(1.0f, 1.0f, 1.0f, 1.0f);
			S.bOverride_ColorGamma = true;
			S.ColorGamma = FVector4(1.0f, 1.0f, 1.0f, 1.0f);
			S.bOverride_ColorGain = true;
			S.ColorGain = FVector4(1.0f, 1.0f, 1.0f, 1.0f);

			// ── 泛光：只在真正过曝的地方起光晕 ──
			// （上面那一份已经设过，这里不要再设一遍 —— 两份参数打架是上一轮的
			//   最大维护负担。修改泛光请只改上面那一处。）

			// ── 环境光遮蔽：给接缝、护甲叠层、关节加接触阴影 ──
			// 机体全身都是刚性拼装件，AO 是"看起来是一台真机器而不是一堆方块"
			// 最有效的一招 —— 它把部件之间的缝隙画出来。
			S.bOverride_AmbientOcclusionIntensity = true;
			S.AmbientOcclusionIntensity = 0.75f;
			S.bOverride_AmbientOcclusionRadius = true;
			S.AmbientOcclusionRadius = 90.f;
			S.bOverride_AmbientOcclusionPower = true;
			S.AmbientOcclusionPower = 2.2f;

			// ── 轻微暗角：把注意力收到画面中心 ──
			S.bOverride_VignetteIntensity = true;
			S.VignetteIntensity = 0.34f;

			// ── 胶片颗粒 + 色散：给画面"质感" ──
			// ★ 2026-10-25：这两项在 -ShotMode 下必须关掉。它们每帧都在随机抖动，
			//   让"同一场景的两张截图"永远有差异 —— 调色时根本判断不出是真变亮了
			//   还是只是噪声不同。正式游玩保留（观感更好），验证模式关闭。
			const bool bNoNoise = IsShotMode();
			S.bOverride_FilmGrainIntensity = true;
			S.FilmGrainIntensity = bNoNoise ? 0.f : 0.16f;
			S.bOverride_SceneFringeIntensity = true;
			S.SceneFringeIntensity = bNoNoise ? 0.f : 0.35f;

			// ── 锐化 ──
			// ⚠️ 2026-10-25：**关掉**（原来是 0.55）。
			//
			// 实测症状：所有硬边都带一圈黑边 —— 墙的转折、集装箱边框、
			// 机体装甲边缘看起来像"描了线"，金属件显得薄。
			// 根因：Sharpen 是反锐化掩模（原图 − 模糊图，放大后加回），
			// 对照片是提细节，对**高对比度硬边**会过冲：暗侧被拉到负值后
			// 截断成纯黑、亮侧直接过曝。而本作场景 100% 是方块几何体，
			// 全是这种边。
			// 硬边场景的正解是交给 TSR 保边（r.TSR.Sharpness），不要后处理锐化。
			S.bOverride_Sharpen = true;
			S.Sharpen = 0.f;

			// 关闭运动模糊。
			// 第三人称 + 快速摆腿时，运动模糊会把腿糊成一团，
			// 反而看不清走路动作；相机本身又跟着角色走、基本没有相对运动，
			// 所以这个特效在这里是纯负收益。
			S.bOverride_MotionBlurAmount = true;
			S.MotionBlurAmount = 0.f;

			UE_LOG(LogTemp, Warning,
				TEXT("[LIGHT] 已应用后处理（手动曝光Bias3.0 / 对比1.08 / 饱和1.0 / "
					 "AO0.75 / 泛光0.35@1.4 / 暗角0.34）"));
		}
	}

	// ── 已移除：诊断用的引擎立方体 ──
	//
	// 排查黑屏时这里会 spawn 一个 /Engine/BasicShapes/Cube 放在角色前方 350cm、
	// 缩放 3 倍，用来区分"资产有问题"和"渲染管线有问题"。
	// 黑屏早已解决，但这块立方体一直留着 —— 它的默认材质是
	// WorldGridMaterial（UE 的灰色棋盘格），而且**跟着角色移动**，
	// 于是变成画面正中央一个 3 米的灰色方块，挡视线、还让人以为是
	// 某个场景构件出了问题，白白排查了好几轮。
	//
	// 教训：诊断代码用完就要删。它比 bug 更难找，因为它"看起来是正常的"。

	// ── 诊断：报告渲染视口状态 ──
	// 如果视口尺寸或屏幕百分比异常，整个场景可能渲染不出来。
	if (GEngine && GEngine->GameViewport)
	{
		FVector2D VP = FVector2D::ZeroVector;
		GEngine->GameViewport->GetViewportSize(VP);
		if (IConsoleVariable* CVar =
				IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage")))
		{
			UE_LOG(LogTemp, Warning,
				TEXT("[LIGHT] 视口尺寸 %.0fx%.0f  屏幕百分比=%s"),
				VP.X, VP.Y, *CVar->GetString());
		}
		else
		{
			UE_LOG(LogTemp, Warning,
				TEXT("[LIGHT] 视口尺寸 %.0fx%.0f"), VP.X, VP.Y);
		}
	}

	// ── 诊断：报告网格体组件的实际状态 ──
	if (USkeletalMeshComponent* MC = GetMesh())
	{
		const FBoxSphereBounds B = MC->Bounds;
		UE_LOG(LogTemp, Warning,
			TEXT("[LIGHT] 角色网格：可见=%d 隐藏游戏中=%d 有资产=%d "
				 "世界包围盒中心(%.0f,%.0f,%.0f) 半径%.0f"),
			MC->IsVisible() ? 1 : 0,
			MC->bHiddenInGame ? 1 : 0,
			MC->GetSkeletalMeshAsset() ? 1 : 0,
			B.Origin.X, B.Origin.Y, B.Origin.Z, B.SphereRadius);
	}
}

/**
 * -ShotMode：把"每帧随机"的后期关掉，让截图可复现。
 *
 * 只影响画面噪声，不影响任何光照参数 —— 所以它不是"另一个布光来源"，
 * 只是在验证时把随机项归零。
 */
void ARobotCharacter::ApplyDeterministicCaptureLook()
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	for (TActorIterator<APostProcessVolume> It(World); It; ++It)
	{
		FPostProcessSettings& S = It->Settings;
		S.bOverride_FilmGrainIntensity = true;
		S.FilmGrainIntensity = 0.f;
		S.bOverride_SceneFringeIntensity = true;
		S.SceneFringeIntensity = 0.f;
		// 泛光保持开启（它是静态效果），但关掉"镜头闪烁"类的随帧抖动
		S.bOverride_BloomDirtMask = false;
	}
	UE_LOG(LogTemp, Warning,
		TEXT("[SHOT] deterministic capture look: film grain / fringe disabled"));
}

bool ARobotCharacter::IsShotMode()
{
	return FParse::Param(FCommandLine::Get(), TEXT("ShotMode"));
}

/**
 * 调试读数。
 *
 * 早期排查黑屏和输入不生效时，这里往屏幕上打了七八行调试文字
 * （按键状态、Enhanced Input 内部状态、相机/射线诊断、热量电力条形）。
 * 那些问题现在都解决了 —— 屏幕上的部分**全部删掉**：
 * 正式 HUD 由 SRobotHUD（Slate）负责，按屏幕尺寸自适应缩放，
 * 不会再像 AddOnScreenDebugMessage 那样按像素定位、换分辨率就错位。
 *
 * 只留一条 10 秒一次的低频日志，方便无头排查时确认角色在不在关卡里、
 * 网格有没有加载 —— 排查结束可以一起删。
 */
void ARobotCharacter::DrawDebugReadout()
{
	if (!GEngine || !IsLocallyControlled())
	{
		return;
	}
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const float Now = World->GetTimeSeconds();
	if (Now - LastDiagLogTime < 10.f)
	{
		return;
	}
	LastDiagLogTime = Now;

	const FVector Loc = GetActorLocation();
	const FString MeshName = (GetMesh() && GetMesh()->GetSkeletalMeshAsset())
		? GetMesh()->GetSkeletalMeshAsset()->GetName() : TEXT("无");

	// 相机/瞄准诊断：验证俯仰是否真的生效、准心射线落点是否合理。
	// 相机俯仰 = 相机组件的世界俯仰（负值朝下）；瞄准点 = 相机中心射线的命中点。
	const float CamPitch = FollowCamera
		? FollowCamera->GetComponentRotation().Pitch : 0.f;
	const float CamZ = FollowCamera
		? FollowCamera->GetComponentLocation().Z : 0.f;
	const FVector Aim = GetAimPoint();
	const float AimDist = FVector::Dist2D(FollowCamera
		? FollowCamera->GetComponentLocation() : Loc, Aim);

	UE_LOG(LogTemp, Log,
		TEXT("[状态] 角色(%.0f,%.0f,%.0f) 网格=%s | 相机(高%.0f 俯仰%.1f) "
			 "瞄准点(%.0f,%.0f,%.0f) 水平距离=%.0f"),
		Loc.X, Loc.Y, Loc.Z, *MeshName,
		CamZ, CamPitch, Aim.X, Aim.Y, Aim.Z, AimDist);
}

void ARobotCharacter::PossessedBy(AController* NewController)
{
	Super::PossessedBy(NewController);

	InitializeAbilitySystem();

	// 把输入映射上下文推给本地玩家
	if (APlayerController* PC = Cast<APlayerController>(NewController))
	{
		// ① 先记录"构造函数里 CreateDefaultSubobject 建出来的"对象身份。
		//    预期这里会看到 MoveAction 的 Outer 是 CDO，而映射里的 Action
		//    是另一个对象 —— 这就是按键不生效的根因。
		LogInputIdentity(TEXT("构造期"));

		// ② 用本实例自己的对象重建一整套输入（见函数注释）。
		RebuildRuntimeInput();

		// ③ 重建后再记录一次，便于对比确认指针已经一致。
		LogInputIdentity(TEXT("重建后"));

		// 🔴 注意：这条日志必须打在各空值检查之后，否则映射上下文是空的
		// 也会照打「正在注册」，把问题掩盖掉（之前就吃过这个亏）。
		UE_LOG(LogTemp, Warning,
			TEXT("[输入] PossessedBy: MappingContext=%s MoveAction=%s LookAction=%s "
				 "映射条数=%d"),
			DefaultMappingContext ? TEXT("有") : TEXT("空"),
			MoveAction ? TEXT("有") : TEXT("空"),
			LookAction ? TEXT("有") : TEXT("空"),
			GetInputMappingCount());
		// 限制俯仰范围（与臂长配套算过）。
		//
		// 非对称区间是**故意的**：往下看可以到 -40°（机身在空中时看地面），
		// 往上看只给 +12° —— 因为"往上看"意味着相机往**下方**摆，
		// 480 臂长时 +12° 相机高度约 60cm，再多就钻地了
		// （相机臂的探针会兜底，但画面会因为臂长缩短而抖动）。
		// 敌人都在地面附近，+12° 完全够用。
		// 注意：ViewPitchMin/Max 在 APlayerCameraManager 上，不在 PlayerController 上。
		if (PC->PlayerCameraManager)
		{
			PC->PlayerCameraManager->ViewPitchMin = -40.f;
			PC->PlayerCameraManager->ViewPitchMax = 12.f;
		}

		// 明确设定输入模式：只用游戏输入，不显示光标。
		// 如果被误设成 UIOnly，所有按键都会被 Slate 吃掉、传不到角色，
		// 表现就是"游戏能打开、画面正常、但按什么键都没反应"。
		PC->SetInputMode(FInputModeGameOnly());
		PC->bShowMouseCursor = false;

		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
				ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(
					PC->GetLocalPlayer()))
		{
			if (DefaultMappingContext)
			{
				Subsystem->AddMappingContext(DefaultMappingContext, 0);
			}
		}
	}
}

void ARobotCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	// 保险：万一这个函数先于 PossessedBy 执行，也要保证输入对象已按实例重建
	RebuildRuntimeInput();

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!EIC)
	{
		// 输入资产没配好时不要静默失败，否则会误以为是移动逻辑坏了
		UE_LOG(LogTemp, Warning,
			TEXT("ARobotCharacter: 需要 EnhancedInputComponent。"
				 "请确认项目启用了 EnhancedInput 插件且默认输入组件未被覆盖。"));
		return;
	}

	UE_LOG(LogTemp, Warning,
		TEXT("[输入] SetupPlayerInputComponent: Move=%s Look=%s Fire=%s Dash=%s Cycle=%s | 映射条数=%d（含手柄）"),
		MoveAction ? TEXT("有") : TEXT("空"),
		LookAction ? TEXT("有") : TEXT("空"),
		FireAction ? TEXT("有") : TEXT("空"),
		DashAction ? TEXT("有") : TEXT("空"),
		CycleChassisAction ? TEXT("有") : TEXT("空"),
		GetInputMappingCount());

	if (MoveAction)
	{
		EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this,
			&ARobotCharacter::HandleMove);
	}
	if (LookAction)
	{
		EIC->BindAction(LookAction, ETriggerEvent::Triggered, this,
			&ARobotCharacter::HandleLook);
	}
	if (FireAction)
	{
		EIC->BindAction(FireAction, ETriggerEvent::Started, this,
			&ARobotCharacter::HandleFireStart);
		EIC->BindAction(FireAction, ETriggerEvent::Completed, this,
			&ARobotCharacter::HandleFireStop);
	}
	if (DashAction)
	{
		EIC->BindAction(DashAction, ETriggerEvent::Started, this,
			&ARobotCharacter::HandleDash);
	}
	if (CycleChassisAction)
	{
		EIC->BindAction(CycleChassisAction, ETriggerEvent::Started, this,
			&ARobotCharacter::HandleSwitchChassis);
	}
	if (ModdingAction)
	{
		EIC->BindAction(ModdingAction, ETriggerEvent::Started, this,
			&ARobotCharacter::HandleToggleModding);
	}

	// 调试：-LogInput 把每条映射的"动作 → 按键"打出来。
	// 手柄适配没法靠自动化按按钮验证，但"映射里到底有没有这个键"
	// 是可以确定的 —— 先排除"键位没注册"这一层。
	if (FParse::Param(FCommandLine::Get(), TEXT("LogInput")) && DefaultMappingContext)
	{
		for (const FEnhancedActionKeyMapping& M : DefaultMappingContext->GetMappings())
		{
			UE_LOG(LogTemp, Warning, TEXT("[输入映射] %-18s → %s"),
				M.Action ? *M.Action->GetName() : TEXT("?"),
				*M.Key.ToString());
		}
	}
}

void ARobotCharacter::InitializeAbilitySystem()
{
	if (!AbilitySystemComponent)
	{
		return;
	}

	if (!AbilitySystemComponent->AbilityActorInfo.IsValid() ||
		AbilitySystemComponent->AbilityActorInfo->AvatarActor.Get() != this)
	{
		AbilitySystemComponent->InitAbilityActorInfo(this, this);
	}

	GrantDefaultAbilities();
}

void ARobotCharacter::GrantDefaultAbilities()
{
	if (!AbilitySystemComponent)
	{
		return;
	}
	for (const TSubclassOf<UGameplayAbility>& AbilityClass : DefaultAbilities)
	{
		if (!AbilityClass)
		{
			continue;
		}
		if (!AbilitySystemComponent->FindAbilitySpecFromClass(AbilityClass))
		{
			AbilitySystemComponent->GiveAbility(
				FGameplayAbilitySpec(AbilityClass, 1, INDEX_NONE, this));
		}
	}
}

// ─────────────────────────────────────────────
// 输入
// ─────────────────────────────────────────────

void ARobotCharacter::HandleMove(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();

	// 诊断：确认按键回调到底有没有被触发。
	// 如果按 WASD 时日志里完全没有这行 → 输入没到达角色（焦点/映射问题）；
	// 如果有这行但角色不动 → 移动逻辑或 Controller 的问题。
	if (!bLoggedMoveInput)
	{
		bLoggedMoveInput = true;
		UE_LOG(LogTemp, Warning,
			TEXT("[输入] HandleMove 首次触发，轴值=(%.2f, %.2f) Controller=%s"),
			Axis.X, Axis.Y, Controller ? TEXT("有") : TEXT("无"));
	}

	if (!Controller || Axis.IsNearlyZero())
	{
		return;
	}

	// 用控制器的朝向而不是角色朝向：角色朝向会随移动旋转，
	// 用它做基准会导致转向时输入方向被反复重解释。
	const FRotator YawOnly(0.f, Controller->GetControlRotation().Yaw, 0.f);
	const FVector Forward = FRotationMatrix(YawOnly).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(YawOnly).GetUnitAxis(EAxis::Y);

	AddMovementInput(Forward, Axis.Y);
	AddMovementInput(Right, Axis.X);
}

void ARobotCharacter::HandleLook(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();

	// 🔴 忽略异常大的输入。
	// 实测在 -game -windowed 模式下，鼠标没有被正确捕获时系统光标的跳变
	// 会产生巨大的 delta，把俯仰角一次顶到 90° 上限 —— 相机随之钻进地底
	// 垂直朝下，画面全黑（相机 z 从 293 掉到 -487）。
	// 正常鼠标单帧位移不会超过几十像素，超过阈值一律当噪声丢弃。
	constexpr float MaxReasonableDelta = 120.f;
	if (FMath::Abs(Axis.X) > MaxReasonableDelta ||
		FMath::Abs(Axis.Y) > MaxReasonableDelta)
	{
		if (GetWorld() && GetWorld()->GetTimeSeconds() - LastLookNoiseLog > 2.f)
		{
			LastLookNoiseLog = GetWorld()->GetTimeSeconds();
			UE_LOG(LogTemp, Warning,
				TEXT("[诊断] 已丢弃异常视角输入 (%.1f, %.1f)"), Axis.X, Axis.Y);
		}
		return;
	}

	AddControllerYawInput(Axis.X * LookSensitivity);
	AddControllerPitchInput(-Axis.Y * LookSensitivity);
}

void ARobotCharacter::HandleFireStart()
{
	// 只置标志。真正的开火在 Tick 里每帧重试激活（支持按住连发），
	// 反馈在 OnWeaponFired 里按"每发"施加（见函数注释）。
	bFiring = true;
}

void ARobotCharacter::HandleFireStop()
{
	bFiring = false;
}

void ARobotCharacter::OnWeaponFired(float Strength)
{
	// ① 武器臂后坐（由程序化动画每帧施加并自然衰减）
	MechProceduralAnim::TriggerRecoil(AnimState, Strength);
	// ② 镜头轻微抖动（按"每发"叠加，但封顶，连发时不会把屏幕晃飞）
	CameraShakeAmount = FMath::Min(CameraShakeAmount + 0.55f * Strength, 1.f);
}

void ARobotCharacter::OnDashTriggered()
{
	// 冲刺镜头瞬时顿挫与后坐抖动，强化氮气喷射推背感
	CameraShakeAmount = FMath::Min(CameraShakeAmount + 0.85f, 1.0f);
	DashThrusterRemaining = 0.28f;
}

void ARobotCharacter::HandleToggleModding()
{
	// UI 由玩家控制器统一管理（暂停、输入模式、面板生命周期）。
	if (ARobotPlayerController* PC = Cast<ARobotPlayerController>(GetController()))
	{
		PC->ToggleModding();
	}
}

void ARobotCharacter::HandleDash()
{
	if (!AbilitySystemComponent)
	{
		return;
	}
	FGameplayAbilitySpec* Spec = AbilitySystemComponent->FindAbilitySpecFromClass(
		UGA_Dash::StaticClass());
	if (Spec)
	{
		AbilitySystemComponent->TryActivateAbility(Spec->Handle);
	}
}

void ARobotCharacter::HandleSwitchChassis()
{
	if (ChassisPresets.Num() == 0 || !Assembly)
	{
		return;
	}
	ChassisIndex = (ChassisIndex + 1) % ChassisPresets.Num();
	URobotChassisData* Next = ChassisPresets[ChassisIndex];
	if (!Next)
	{
		return;
	}

	Assembly->SetChassis(Next);
	if (USkeletalMeshComponent* MeshComp = GetMesh())
	{
		if (USkeletalMesh* NewMesh = Next->ChassisMesh.LoadSynchronous())
		{
			MeshComp->SetSkeletalMesh(NewMesh);
		}
	}
	UE_LOG(LogTemp, Log, TEXT("切换到机体：%s"), *Next->DisplayName.ToString());
}

// ─────────────────────────────────────────────
// 装配与部位
// ─────────────────────────────────────────────

void ARobotCharacter::SwitchChassis(URobotChassisData* NewChassis)
{
	if (!Assembly || !NewChassis)
	{
		return;
	}
	Assembly->SetChassis(NewChassis);

	if (USkeletalMeshComponent* MeshComp = GetMesh())
	{
		if (USkeletalMesh* NewMesh = NewChassis->ChassisMesh.LoadSynchronous())
		{
			MeshComp->SetSkeletalMesh(NewMesh);
		}
	}

	// 换了机体 = 换了骨骼网格，动画网格必须跟着换并重新缓存基准姿势
	RefreshAnimMesh();
}

void ARobotCharacter::HandleAssemblyChanged()
{
	RefreshFromAssembly();
}

void ARobotCharacter::RefreshFromAssembly()
{
	if (!Assembly || !AbilitySystemComponent)
	{
		return;
	}
	Assembly->ApplyToAbilitySystem(AbilitySystemComponent);
}

bool ARobotCharacter::IsOverheated() const
{
	return AttributeSet ? AttributeSet->IsOverheated() : false;
}

FTransform ARobotCharacter::GetMuzzleTransform() const
{
	const FQuat ActorQ = GetActorQuat();

	// 首选：从**动画网格**的 forearm_R 骨骼取。必须用动画网格 ——
	// 源网格不参与程序化动画，骨骼停在绑定姿势，取出来的枪口是"手臂不动"
	// 时的位置，走路摆臂时枪管和弹道就会错开。
	if (AnimMesh)
	{
		FTransform BoneXf;
		if (MechProceduralAnim::GetBoneWorldTransform(AnimMesh,
			FName(TEXT("forearm_R")), BoneXf))
		{
			const FVector Loc = BoneXf.GetLocation()
				+ ActorQ.RotateVector(MuzzleLocalOffset);
			return FTransform(ActorQ, Loc);
		}
	}

	// 退化：角色位置 + 前方偏移（右臂侧向偏 58cm、高 115cm，取自建模参数）
	const FVector Fallback = GetActorLocation()
		+ ActorQ.RotateVector(FVector(45.f, 58.f, 115.f));
	return FTransform(ActorQ, Fallback);
}

FVector ARobotCharacter::GetAimPoint(float MaxDistance) const
{
	// 调试：-AutoFire 模式下直接瞄准"最近的存活敌人"的躯干（或 -ShootBarrel 瞄准燃料桶测试爆炸）。
	if (bAutoFireAimDebug)
	{
		UWorld* AimWorld = GetWorld();
		if (AimWorld && FParse::Param(FCommandLine::Get(), TEXT("ShootBarrel")))
		{
			ARobotExplosiveBarrel* BestBarrel = nullptr;
			float MinDistSq = TNumericLimits<float>::Max();
			const FVector PlayerLoc = GetActorLocation();

			for (TActorIterator<ARobotExplosiveBarrel> It(AimWorld); It; ++It)
			{
				if (ARobotExplosiveBarrel* B = *It)
				{
					// 只选前方正视角的桶，且挑距离最近的
					if (B->GetActorLocation().X > PlayerLoc.X + 50.f)
					{
						const float D = FVector::DistSquared(PlayerLoc, B->GetActorLocation());
						if (D < MinDistSq)
						{
							MinDistSq = D;
							BestBarrel = B;
						}
					}
				}
			}
			if (BestBarrel)
			{
				return BestBarrel->GetActorLocation() + FVector(0.f, 0.f, 25.f);
			}
		}

		if (const ARobotEnemy* Enemy = FindNearestAliveEnemy())
		{
			return Enemy->GetActorLocation() + FVector(0.f, 0.f, 50.f);
		}
	}

	// 相机在第三人称下位于角色斜后方，准心方向 = 相机正前方。
	const FVector Start = FollowCamera
		? FollowCamera->GetComponentLocation()
		: GetActorLocation() + FVector(0.f, 0.f, 100.f);
	const FVector Dir = FollowCamera
		? FollowCamera->GetForwardVector()
		: GetActorForwardVector();

	UWorld* World = GetWorld();
	if (!World)
	{
		return Start + Dir * MaxDistance;
	}

	// 忽略自己（否则射线一出相机就打中自己的胶囊）
	FCollisionQueryParams Params(SCENE_QUERY_STAT(RobotAim), true, this);
	FHitResult Hit;
	if (World->LineTraceSingleByChannel(Hit, Start, Start + Dir * MaxDistance,
		ECC_Visibility, Params))
	{
		return Hit.ImpactPoint;
	}
	return Start + Dir * MaxDistance;
}

ARobotEnemy* ARobotCharacter::FindNearestAliveEnemy() const
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}
	ARobotEnemy* Best = nullptr;
	float BestDistSq = TNumericLimits<float>::Max();
	for (TActorIterator<ARobotEnemy> It(World); It; ++It)
	{
		if (It->IsCoreDestroyed())
		{
			continue;
		}
		const float DistSq =
			FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
		if (DistSq < BestDistSq)
		{
			BestDistSq = DistSq;
			Best = *It;
		}
	}
	return Best;
}

void ARobotCharacter::HandlePartDestroyed(FGameplayTag PartTag)
{
	UE_LOG(LogTemp, Log, TEXT("玩家部位被摧毁：%s"), *PartTag.ToString());

	// 金属爆裂音效：玩家自己挨打的听觉反馈（和 HUD 闪红同步）
	RobotSfx::PlayAt(this, TEXT("SFX_Destroy"), GetActorLocation(),
		0.85f, 1.f, true);

	// 把骨骼隐藏同步到可见的动画网格上。
	// 部位系统只会去隐藏 GetMesh() 上的骨骼，而那个网格是不可见的，
	// 所以必须在这里按同一套"骨骼名前缀"规则在 AnimMesh 上再隐藏一次。
	if (AnimMesh && PartMap)
	{
		FPartBoneRule Rule;
		if (PartMap->FindRule(PartTag, Rule))
		{
			for (const FName& Prefix : Rule.BonePrefixes)
			{
				MechProceduralAnim::HideBonesByPrefix(AnimMesh, Prefix.ToString());
			}
		}
	}
}

void ARobotCharacter::HandlePartDamaged(FGameplayTag PartTag, float RemainingRatio)
{
	// 受击反馈：通知 HUD 闪一下红色暗角。
	// 只在本地控制的玩家身上做（敌人挨打不该闪玩家的屏）。
	if (IsLocallyControlled())
	{
		if (ARobotPlayerController* PC =
				Cast<ARobotPlayerController>(GetController()))
		{
			PC->NotifyPlayerDamaged();
		}
	}
}

void ARobotCharacter::HandleActorDisabled()
{
	UE_LOG(LogTemp, Log, TEXT("玩家机体已瘫痪"));

	// 失败路径：把"玩家瘫痪"上报给 GameMode → 弹结算画面。
	// 核心被毁（torso 兼核心）或功能部位尽失都会走到这里。
	if (UWorld* W = GetWorld())
	{
		if (ARobotGameMode* GM = Cast<ARobotGameMode>(
				UGameplayStatics::GetGameMode(W)))
		{
			GM->NotifyPlayerDefeated();
		}
	}
}

void ARobotCharacter::AddSalvage(int32 Amount)
{
	if (Amount <= 0)
	{
		return;
	}
	SalvageCount += Amount;
	UE_LOG(LogTemp, Verbose, TEXT("回收废料 +%d（累计 %d）"), Amount, SalvageCount);
}

void ARobotCharacter::RepairAllParts()
{
	if (PartDamage)
	{
		PartDamage->RepairAllParts();
	}
	// 修复后把移动能力还回来（部位被毁时可能被限制过）
	if (UCharacterMovementComponent* Move = GetCharacterMovement())
	{
		Move->SetMovementMode(MOVE_Walking);
	}
	RefreshFromAssembly();
}

/**
 * 调试相机：-SideCam（正侧视）/ -CloseCam（近景）。
 *
 * 【为什么另起一个 CameraActor，而不是继续摆相机臂】
 * 前前后后试了三轮都没把相机臂摆对：
 *   ① 调 TargetArmLength + SetRelativeRotation → 俯仰被 bInheritPitch=false 吃掉
 *   ② SetUsingAbsoluteLocation + SetWorldLocation → 被父组件空间二次变换
 *   ③ DetachFromComponent(KeepWorldTransform) + 每帧手写世界变换
 *      → 日志里组件坐标完全正确（左右=-560 高=170 俯角=-16），
 *        但渲染出来的画面里机体不在预测位置
 * 相机臂的最终落点同时受 父组件变换 / 控制旋转 / bInheritPitch /
 * 碰撞回缩 四个因素影响，而 ACameraActor 一个都没有 ——
 * SetViewTarget 之后视角就等于它的世界变换。调试工具不该继续跟相机臂较劲。
 *
 * 注意：切到 CameraActor 后，玩家控制器不再用 Pawn 当视角目标，
 * 相机抖动等基于 Pawn 的效果会失效 —— 这只影响调试模式，正式玩不带这些参数。
 */
void ARobotCharacter::SetupReviewStage()
{
	UWorld* W = GetWorld();
	if (!W)
	{
		return;
	}

	// ── 收集敌人并摆成一排 ──
	//
	// 敌人是脚本摆进关卡的（5 台，型号由 Actor 名末尾的数字决定）。
	// 检阅模式不新增敌人，只把它们挪到同一平面上、关掉 AI，
	// 这样画面里能同时看到全部型号，方便横向比较比例。
	TArray<ARobotEnemy*> Enemies;
	for (TActorIterator<ARobotEnemy> It(W); It; ++It)
	{
		Enemies.Add(*It);
	}
	const int32 N = Enemies.Num();
	const float Gap = 240.f;
	for (int32 i = 0; i < N; ++i)
	{
		ARobotEnemy* E = Enemies[i];
		if (!E)
		{
			continue;
		}
		const float Y = (i - (N - 1) * 0.5f) * Gap;
		E->SetActorLocation(FVector(250.f, Y, 120.f), false, nullptr,
			ETeleportType::TeleportPhysics);
		// 模型正面朝 -X（Blender 里核心在 -Y），相机在 +X 侧 → 转 180° 才露正脸
		E->SetActorRotation(FRotator(0.f, 180.f, 0.f));
		// 冻结：停 Tick（AI 全在 Tick 里）+ 停移动，否则它们会走过来挤成一团
		E->SetActorTickEnabled(false);
		if (UCharacterMovementComponent* Mv = E->GetCharacterMovement())
		{
			Mv->StopMovementImmediately();
			Mv->DisableMovement();
		}
	}

	// ── 玩家挪走并隐藏 ──
	// 玩家留在原地会挡在相机和敌人之间（相机是固定的，不跟随）。
	SetActorHiddenInGame(true);
	SetActorLocation(FVector(-800.f, 0.f, 120.f), false, nullptr,
		ETeleportType::TeleportPhysics);
	if (UCharacterMovementComponent* Mv = GetCharacterMovement())
	{
		Mv->StopMovementImmediately();
		Mv->DisableMovement();
	}

	// ── 检阅灯：自带三点布光 ──
	//
	// 场景本身的布光是给"玩家在场地里战斗"调的，侧逆光居多，
	// 拍检阅图时敌人全成剪影。这里就地补三盏，保证无论关卡怎么调光，
	// 检阅画面始终可读（这是工具，不该依赖被检查对象的状态）。
	struct FLightDef { FVector Loc; float Lumens; FLinearColor Color; };
	// ── 关键：把太阳转到"正面光" ──
	//
	// 场景的太阳是给场地调的侧逆光，拍检阅图时敌人全在暗部。
	// 点光救不回来 —— UE 点光是 lumens，照度按 1/(4πr²) 衰减，
	// 10m 外要压过 11000 lux 的太阳需要几百万 lumens，那会烤糊近处地面。
	// 直接把方向光转过来才是正解：它不衰减，一改就是全局正面光。
	//
	// DirectionalLight 照的是自己的 Forward。yaw=180 → 光沿 -X 传播，
	// 正好照亮朝向 +X（也就是朝向相机）的立面。
	for (TActorIterator<ADirectionalLight> It(W); It; ++It)
	{
		It->SetActorRotation(FRotator(-34.f, 180.f, 0.f));
	}

	// 点光只做近距离补光
	const FLightDef Lights[] =
	{
		{ FVector(560.f,  -600.f, 420.f), 140000.f, FLinearColor(1.00f, 0.96f, 0.90f) },
		{ FVector(560.f,   600.f, 420.f), 120000.f, FLinearColor(0.74f, 0.84f, 1.00f) },
		{ FVector(-260.f,    0.f, 520.f), 120000.f, FLinearColor(1.00f, 0.86f, 0.72f) },
	};
	for (const FLightDef& D : Lights)
	{
		APointLight* Pl = W->SpawnActor<APointLight>(D.Loc, FRotator::ZeroRotator);
		if (!Pl)
		{
			continue;
		}
		if (UPointLightComponent* Lc =
			Cast<UPointLightComponent>(Pl->GetLightComponent()))
		{
			Lc->SetMobility(EComponentMobility::Movable);
			Lc->SetIntensity(D.Lumens);
			Lc->SetLightColor(D.Color);
			Lc->SetAttenuationRadius(1400.f);
			Lc->SetCastShadows(false);
			Lc->SetVisibility(true);
			// ⚠️ 不加这一行，运行时 spawn 的灯保持 Static，一帧都不渲染
			Lc->MarkRenderStateDirty();
		}
	}

	UE_LOG(LogTemp, Warning,
		TEXT("[检阅] 已摆好 %d 台敌人（间距 %.0fcm），玩家已隐藏，补检阅灯"),
		N, Gap);
}

void ARobotCharacter::UpdateHeroFill()
{
	AActor* L = HeroFillLight.Get();
	if (!L)
	{
		return;
	}

	// 方向：玩家 → 镜头。补光必须照**镜头看得见的那一面**，
	// 否则加了灯还是黑剪影（这正是旧实现"挂在 -X 相对位置"瞎猜的后果）。
	FVector ToCam = FVector::ZeroVector;
	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		FVector CamLoc;
		FRotator CamRot;
		PC->GetPlayerViewPoint(CamLoc, CamRot);
		ToCam = CamLoc - GetActorLocation();
		ToCam.Z = 0.f;
	}
	ToCam = ToCam.GetSafeNormal();
	if (ToCam.IsNearlyZero())
	{
		ToCam = -GetActorForwardVector();
	}

	// 默认：玩家往镜头方向退 330cm、抬 240cm —— 大约在机体的斜前上方，
	// 正好扫过胸甲和肩甲，又不会把地板打出一团亮斑（点光不投影，
	// 靠近地面时才会明显）。扫参用 -HeroFillDist= / -HeroFillZ=。
	float Dist = 330.f;
	float Height = 240.f;
	{
		FString V;
		if (FParse::Value(FCommandLine::Get(), TEXT("HeroFillDist="), V))
		{
			Dist = FCString::Atof(*V);
		}
		if (FParse::Value(FCommandLine::Get(), TEXT("HeroFillZ="), V))
		{
			Height = FCString::Atof(*V);
		}
	}

	const FVector Target =
		GetActorLocation() + ToCam * Dist + FVector(0.f, 0.f, Height);
	L->SetActorLocation(Target, false, nullptr, ETeleportType::TeleportPhysics);
}

void ARobotCharacter::UpdateDebugCamera()
{
	if (DebugCamMode == 0)
	{
		return;
	}

	UWorld* W = GetWorld();
	if (!W)
	{
		return;
	}

	// ── 机体尺度参考（实测）：脚在 Z≈1，头顶 Z≈250，胸口 Z≈130 ──
	// ⚠️ Origin 是**胶囊中心**（Z≈121），不是脚底。所以 LookAt 的 Z
	//    必须写成绝对值，不能用 Origin + 偏移 —— 之前写成
	//    Origin + (0,0,165)，实际视线落在 Z≈286，整个机体都在画面下方。
	const FVector Origin = GetActorLocation();
	const FVector Fwd = GetActorForwardVector();
	const FVector Right = GetActorRightVector();
	const FVector Chest(Origin.X, Origin.Y, 130.f);

	FVector CamLoc;
	FVector LookAt;
	float Fov;

	if (DebugCamMode == 1)
	{
		// 正侧视：从角色右手边看过去。前后摆腿在这个视角下完全没有
		// 透视压缩，是评估步态唯一可靠的视角（也是本轮修轴的验收手段）。
		//
		// 距离 600cm / FOV 50（UE 的 FieldOfView 是**水平**视角）：
		// 垂直半角 = atan(tan(25°) * 9/16) ≈ 14.7°，画面可见高度
		// = 2 * 600 * tan(14.7°) ≈ 315cm —— 机体高 250cm，正好留一圈边。
		CamLoc = Origin + Right * 600.f + FVector(0.f, 0.f, 90.f);
		LookAt = Chest;
		Fov = 50.f;
	}
	else if (DebugCamMode == 4)
	{
		// 斜俯视：站在背墙外侧上方，看向场地中心偏远墙
		CamLoc = FVector(-1650.f, -1500.f, 1350.f);
		LookAt = FVector(500.f, 150.f, 0.f);
		Fov = 78.f;
	}
	else if (DebugCamMode == 5)
	{
		// 毒液池贴水低机位：池心在 (-200,350)，半径约 137。
		// 相机 1.5m 高、在池子南侧 2.5m，俯角约 30°，波纹有掠射高光。
		CamLoc = FVector(-200.f, 600.f, 150.f);
		LookAt = FVector(-200.f, 350.f, 5.f);
		Fov = 60.f;
	}
	else if (DebugCamMode == 6)
	{
		// 冷却液水渠：渠心 (450,300)，内壁 x 70..830 / y 200..400，水面 z=7。
		// 相机在渠首外侧偏南、2m 高，沿渠长方向看过去：近处龙门落水、
		// 远处渠壁收窄，一眼能读出"水在一条长槽里往 +X 流"。
		CamLoc = FVector(-260.f, 620.f, 200.f);
		LookAt = FVector(480.f, 300.f, 12.f);
		Fov = 62.f;
	}
	else if (DebugCamMode == 7)
	{
		// 正面英雄机位：站在角色正前方偏右，平视胸口。
		// 距离 420cm / FOV 50：可见高度约 338cm，机体 250cm 全身入画，
		// 两侧肩甲都露在轮廓外，专门用来验收"肩甲到底在不在"。
		CamLoc = Origin + Fwd * 420.f + Right * 130.f +
			FVector(0.f, 0.f, 150.f);
		LookAt = FVector(Origin.X, Origin.Y, 140.f);
		Fov = 50.f;
	}
	else if (DebugCamMode == 8)
	{
		// 水池 3/4 全景：池心 (-200,350)、池壁外半径 152、注水口在 +X 侧。
		// 相机在池子正南 5.3m、3m 高，俯角约 26°，同时收进近处池沿、整圈池壁、
		// 供水立管与落水柱 —— 一眼能看出"液体在被注进池子"。
		CamLoc = FVector(-520.f, 860.f, 280.f);
		LookAt = FVector(-190.f, 350.f, 25.f);
		Fov = 55.f;
	}
	else if (DebugCamMode == 9)
	{
		// 注水落点近景：水柱 (120,300) 插入渠水面，看接触与水花。
		// 相机在落点西南偏上，平视略俯，收进水柱、落点泡沫与溅起水花。
		CamLoc = FVector(-40.f, 470.f, 70.f);
		LookAt = FVector(120.f, 300.f, 18.f);
		Fov = 50.f;
	}
	else if (DebugCamMode == 10)
	{
		// 敌人近景（LOD0）：对准 BP_Enemy(400,-400)，约 4m 距离看全细节。
		CamLoc = FVector(120.f, -680.f, 230.f);
		LookAt = FVector(400.f, -400.f, 150.f);
		Fov = 50.f;
	}
	else if (DebugCamMode == 11)
	{
		// 双足敌人（园丁 BP_Enemy_C_8 在 1350,650）：正南 260cm、高 150cm 平视。
		CamLoc = FVector(1350.f, 390.f, 150.f);
		LookAt = FVector(1350.f, 650.f, 120.f);
		Fov = 50.f;
	}
	else if (DebugCamMode == 3)
	{
		// 检阅机位：固定不动，站在 +X 侧看向摆成一排的敌人。
		// 场地中心大约 (250, 0)，敌人在 x=250 沿 Y 排开、间距 300cm，
		// 6 台总宽 1500cm；距离 1300 + FOV 70 → 可见宽度 1820cm，留边。
		// 距离 900 / FOV 70 → 可见宽度 1260cm，5 台（间距 240）刚好占满
		CamLoc = FVector(1150.f, 0.f, 205.f);
		LookAt = FVector(250.f, 0.f, 140.f);
		Fov = 70.f;
	}
	else if (DebugCamMode == 12)
	{
		// 背墙海报验收：站在场地内朝 -X 看背墙（X=-1240）
		CamLoc = FVector(-560.f, -260.f, 215.f);
		LookAt = FVector(-1240.f, -160.f, 200.f);
		Fov = 75.f;
	}
	else if (DebugCamMode == 13)
	{
		// 远墙内侧海报（墙面 X=1755，朝 -X）
		CamLoc = FVector(1180.f, -60.f, 225.f);
		LookAt = FVector(1755.f, 120.f, 200.f);
		Fov = 80.f;
	}
	else if (DebugCamMode == 14)
	{
		// 扩建区域：站在门洞（X=1800）前 150cm，朝 +X 看整条通道与新场地。
		// 高度 320 是为了越过门洞两侧的墙（396 高）看到里面的地面。
		CamLoc = FVector(1650.f, -260.f, 320.f);
		LookAt = FVector(4200.f, 0.f, 120.f);
		Fov = 85.f;
	}
	else if (DebugCamMode == 15)
	{
		// 雕像正面 3/4：绕到龙门架（x=3200，y 跨 ±264）之外，
		// 从右前方 16m 处看，能同时读到正面与侧面，且不被结构挡住。
		// 距离 16.2m、Fov 60（水平）→ 垂直覆盖约 1057cm，装得下 936cm 的雕像。
		CamLoc = FVector(3400.f, -900.f, 500.f);
		LookAt = FVector(4750.f, 0.f, 460.f);
		Fov = 60.f;
	}
	else if (DebugCamMode == 16)
	{
		// 雕像正面直视：拉到 10m 外并用 85° 广角，
		// 既避开 x=3200 的龙门架，又能拍全整个高度。
		CamLoc = FVector(3750.f, 0.f, 500.f);
		LookAt = FVector(4750.f, 0.f, 460.f);
		Fov = 85.f;
	}
	else if (DebugCamMode == 17)
	{
		// Cosmos 道具俯视：从新区域上方斜看，一次看清全部掩体布局与动线。
		// 站在通道出口上方偏左，朝远端俯视。
		CamLoc = FVector(2350.f, -150.f, 1500.f);
		LookAt = FVector(3900.f, 0.f, 0.f);
		Fov = 90.f;
	}
	else if (DebugCamMode == 18)
	{
		// 从通道口（玩家进门位置）平视掩体群与远端雕像
		CamLoc = FVector(2450.f, 0.f, 170.f);
		LookAt = FVector(4200.f, 0.f, 180.f);
		Fov = 88.f;
	}
	else if (DebugCamMode == 19)
	{
		// 第一百一十二轮：长方形水渠纹理验收。
		// 长方形水渠（Basin_CoolantSpill_0 在 (450,300)，长轴沿 X，816x256cm）。
		// 从 +Y 侧斜俯看，长边渠沿与水面同时入画，便于看纹理错乱。
		CamLoc = FVector(760.f, 780.f, 520.f);
		LookAt = FVector(450.f, 300.f, 0.f);
		Fov = 62.f;
	}
	else if (DebugCamMode == 20)
	{
		// 场景1 地面纹理参考（拍原竞技场地面，作为场景2的对比基准）
		CamLoc = FVector(-400.f, -300.f, 420.f);
		LookAt = FVector(200.f, 250.f, 0.f);
		Fov = 70.f;
	}
	else if (DebugCamMode == 21)
	{
		// 落水点水花：低角度平视，看水柱脚下向上喷溅的粒子
		CamLoc = FVector(-260.f, 300.f, 90.f);
		LookAt = FVector(120.f, 300.f, 40.f);
		Fov = 55.f;
	}
	else if (DebugCamMode == 22)
	{
		// Niagara 模板测试排：从南侧平视 5 个系统
		CamLoc = FVector(-360.f, -1700.f, 200.f);
		LookAt = FVector(-360.f, -1100.f, 60.f);
		Fov = 90.f;
	}
	else if (DebugCamMode == 23)
	{
		// 落水水珠近景：贴近落点 (120,300) 平视，水柱与水花同框
		CamLoc = FVector(20.f, 480.f, 70.f);
		LookAt = FVector(120.f, 300.f, 25.f);
		Fov = 50.f;
	}
	else if (DebugCamMode == 24)
	{
		// 第一百一十九轮：texgen 碎骸近景。躯干(4400,620)朝 -X-Y，
		// 相机绕到其正面（西南侧）约 9m，平视躯干胸口，断臂(4050,700)同框。
		// 用来验收 UE 里 texgen 贴图是否正常显示（白色涂装/做旧/面罩）。
		CamLoc = FVector(3450.f, 250.f, 230.f);
		LookAt = FVector(4300.f, 630.f, 160.f);
		Fov = 62.f;
	}
	else if (DebugCamMode == 25)
	{
		// 第一百一十九轮：4 个碎骸俯视全景（x 3200..4900, y -760..700）
		CamLoc = FVector(4100.f, 0.f, 1550.f);
		LookAt = FVector(4100.f, 0.f, 60.f);
		Fov = 90.f;
	}
	else
	{
		// 近景：从右前方 3/4 角看，用来验收表面细节（面板缝 / 铆钉 / 刮痕）。
		// 距离约 322cm、FOV 55 → 可见高度约 187cm，框住上半身。
		CamLoc = Origin - Fwd * 215.f + Right * 240.f + FVector(0.f, 0.f, 70.f);
		LookAt = FVector(Origin.X, Origin.Y, 175.f);
		Fov = 55.f;
	}

	const FRotator CamRot = (LookAt - CamLoc).Rotation();

	ACameraActor* Cam = Cast<ACameraActor>(DebugCamera.Get());
	if (!Cam)
	{
		FActorSpawnParameters P;
		P.SpawnCollisionHandlingOverride =
			ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Cam = W->SpawnActor<ACameraActor>(
			ACameraActor::StaticClass(), CamLoc, CamRot, P);
		if (!Cam)
		{
			UE_LOG(LogTemp, Warning, TEXT("[调试相机] 创建失败"));
			DebugCamMode = 0;
			return;
		}
		DebugCamera = Cam;
		Cam->SetActorLabel(TEXT("DebugCam"));
		// 相机本身不该被任何东西挡住
		if (UCameraComponent* CamComp = Cam->GetCameraComponent())
		{
			CamComp->SetFieldOfView(Fov);
			CamComp->bUsePawnControlRotation = false;
		}
		if (APlayerController* PC = Cast<APlayerController>(GetController()))
		{
			// 关掉"自动管理视角目标"：APlayerController 默认会在 Possess 之后
			// 把 ViewTarget 抢回 Pawn —— 调试相机建在 Possess 之前，就会被静默夺走，
			// 表现为"日志说已接管、画面还是第三人称"（本轮实测踩到）。
			PC->bAutoManageActiveCameraTarget = false;
			PC->SetViewTarget(Cam);
			UE_LOG(LogTemp, Warning,
				TEXT("[调试相机] 模式 %d，已接管视角：位置=%s 朝向=%s FOV=%.0f"),
				DebugCamMode, *CamLoc.ToCompactString(),
				*CamRot.ToCompactString(), Fov);
		}
	}
	else
	{
		Cam->SetActorLocationAndRotation(CamLoc, CamRot, false, nullptr,
			ETeleportType::TeleportPhysics);
		if (UCameraComponent* CamComp = Cam->GetCameraComponent())
		{
			CamComp->SetFieldOfView(Fov);
		}
		// 每帧重申一次视角目标（成本可忽略）：只要有任何一处代码
		// 重新 Possess / 重置相机，调试视角就能在同一帧恢复。
		if (APlayerController* PC = Cast<APlayerController>(GetController()))
		{
			if (PC->GetViewTarget() != Cam)
			{
				PC->bAutoManageActiveCameraTarget = false;
				PC->SetViewTarget(Cam);
			}
		}
	}
}

