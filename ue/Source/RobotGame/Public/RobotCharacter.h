// 玩家机体
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AbilitySystemInterface.h"
#include "MechProceduralAnim.h"
#include "RobotCharacter.generated.h"

class UAbilitySystemComponent;
class URobotAttributeSet;
class UPartDamageComponent;
class UAssemblyComponent;
class URobotChassisData;
class UPartMapData;
class UInputMappingContext;
class UInputAction;

/**
 * 玩家机体。
 *
 * 移动基础用 CMC 而不是 Mover —— Mover 在 UE5.8 仍处于"从实验性向稳定架构
 * 演进"阶段，未标注生产就绪。攀爬、磁吸、冲刺都通过自定义 MovementMode 实现，
 * 并封装在接口之后，将来迁移 Mover 时只换实现层。
 */
UCLASS()
class ROBOTGAME_API ARobotCharacter : public ACharacter, public IAbilitySystemInterface
{
	GENERATED_BODY()

public:
	ARobotCharacter();

	virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override;

	UFUNCTION(BlueprintPure, Category = "Robot")
	URobotAttributeSet* GetAttributeSet() const { return AttributeSet; }

	UFUNCTION(BlueprintPure, Category = "Robot")
	UPartDamageComponent* GetPartDamage() const { return PartDamage; }

	UFUNCTION(BlueprintPure, Category = "Robot")
	UAssemblyComponent* GetAssembly() const { return Assembly; }

	/** 切换机体（在主基地或维修点调用） */
	UFUNCTION(BlueprintCallable, Category = "Robot")
	void SwitchChassis(URobotChassisData* NewChassis);

	/** 当前是否处于过热锁定 */
	UFUNCTION(BlueprintPure, Category = "Robot")
	bool IsOverheated() const;

	/** 拾取废料。由回收物容器调用。 */
	UFUNCTION(BlueprintCallable, Category = "Robot")
	void AddSalvage(int32 Amount);

	UFUNCTION(BlueprintPure, Category = "Robot")
	int32 GetSalvage() const { return SalvageCount; }

	/** 已建立的输入映射条数。UInputMappingContext::Mappings 是 protected，
	 *  Python 读不到，所以在这里暴露一个访问器供验证脚本使用。 */
	UFUNCTION(BlueprintPure, Category = "Input")
	int32 GetInputMappingCount() const;

	// ── 武器（普通 C++ 接口，不加反射宏）──
	//
	// 说明：本项目的手动编译链路（绕过 UBA）没有依赖追踪，
	// 新增 UPROPERTY/UFUNCTION 需要重跑 UHT 才安全。这几个接口只被
	// C++ 调用（GA_Fire），不暴露给蓝图，所以用普通成员/函数最稳妥。

	/**
	 * 武器臂枪口的世界变换。
	 *
	 * 取的是**动画网格**上 forearm_R 骨骼的位置 —— 枪口必须跟着程序化
	 * 动画走（走路时手臂在摆、开火时手臂后坐），否则弹丸会从"手臂静止
	 * 时的位置"飞出来，视觉上枪管和弹道对不上。
	 * 动画网格取不到时退化为"角色位置 + 前方偏移"，永远返回有效值。
	 */
	FTransform GetMuzzleTransform() const;

	/** 是否正在开火（按住连发） */
	bool IsFiring() const { return bFiring; }

	/**
	 * 由武器技能在**成功出弹**后回调 —— 施加后坐、镜头抖动、瞄准过渡。
	 *
	 * 为什么放在这里而不是"按下开火键"时：按住连发时按键只触发一次，
	 * 如果反馈绑在按键上，连发的第 2 发之后就没有任何后坐了。
	 * 反馈必须和"真的打出一发"一一对应。
	 */
	void OnWeaponFired(float Strength = 1.f);

	/** 冲刺喷气推进触发 */
	void OnDashTriggered();

	/** 动画网格（可能为空）。供武器/特效系统查询骨骼挂点。 */
	class UPoseableMeshComponent* GetAnimMesh() const { return AnimMesh; }

	/**
	 * 玩家当前瞄准的世界坐标点 —— 从相机中心沿视线做射线，
	 * 命中什么就瞄什么，没命中就取视线尽头。
	 *
	 * 为什么必须从**相机**而不是从角色朝向算：第三人称下相机在角色斜后方，
	 * 直接沿角色朝向射击，弹道会和准心差出几米，玩家会觉得"打不准"。
	 * 标准做法就是「相机中心定方向、枪口定起点」。
	 */
	FVector GetAimPoint(float MaxDistance = 30000.f) const;

	/** 最近的存活敌人（-AutoFire 调试瞄准用；正常游玩不经过） */
	class ARobotEnemy* FindNearestAliveEnemy() const;

	/**
	 * 任务结束后的自动修复。
	 * 玩家自身部位被毁会临时失去对应能力，但不应永久损失 ——
	 * 检查点或任务结束时恢复。
	 */
	UFUNCTION(BlueprintCallable, Category = "Robot")
	void RepairAllParts();

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void PossessedBy(AController* NewController) override;
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	/** 屏幕调试显示。没有正式 HUD 之前，用它在画面上显示热量/电力/废料 ——
	 *  否则玩家看不到热量条，无法评估「爆发—停顿」节奏是否成立。 */
	void DrawDebugReadout();

	/**
	 * 竞技场边界约束（每帧在 Tick 里调用）。
	 *
	 * 做两件事：
	 *   ① XY 钳在可玩矩形内，朝外的速度分量清零 —— 不会走出围墙；
	 *   ② Z 低于 FallKillZ 时判定掉出地图，拉回最近的安全位置。
	 *
	 * 为什么用代码而不是只靠场景碰撞：围墙是静态网格，碰撞由 FBX 导入时
	 * 自动生成，改导入设置/换资产就可能静默失效；冲刺速度高时薄墙也有
	 * 穿透风险。代码边界不依赖任何资产，是最后一道保险。
	 */
	void ClampToArena();

	/**
	 * 运行时强制修正关卡灯光。
	 *
	 * 脚本设置灯光组件属性后 save_current_level() 不会把变更落盘 ——
	 * 实测关卡里存的仍是 Mobility=Stationary、intensity=10、
	 * real_time_capture=False。而 Static/Stationary 灯光需要烘焙光照贴图，
	 * 没有烘焙就完全不照明，表现就是整个场景全黑。
	 * 在运行时强制改，不依赖关卡的保存状态。
	 */
	void FixLevelLighting();

	/**
	 * 给竞技场的每一类灯"分工"。
	 *
	 * 为什么需要单独一步：2026-10-25 用 -LightDump 打出运行时的 24 盏灯，
	 * 发现**所有灯都是 2600 cd** —— 太阳 9000 lux，10 盏装饰、8 盏投光、
	 * 4 盏补光全部 2600。这是历史上若干个脚本各写各的、互相覆盖的结果。
	 *
	 * 结果就是画面"哪里都一样亮"：没有主光、没有光池、没有明暗层次，
	 * 地板整片均匀发白，跟"夜景工业场地"没有关系。
	 * 灯的分工必须在**一个地方**定义，并且每帧只被写一次。
	 */
	void TuneArenaLights();

	/**
	 * 英雄补光跟随。
	 *
	 * 灯本身是**关卡里**的 HeroFill（ue/Scripts/arena_herofill.py 建），
	 * 不是运行时 SpawnActor —— 本工程运行时生成的灯完全不参与渲染，
	 * 旧代码那盏"跟随玩家的 9000cd 补光"从写下那天起就没亮过，
	 * 这正是第三人称视角下机体永远是一团黑剪影的原因。
	 *
	 * 位置：玩家 → 镜头的方向退 300cm、再往镜头左侧偏 170cm、抬 260cm。
	 * 也就是始终在"镜头与机体之间偏左上"，照的是镜头看得见的那一面，
	 * 同时保留一点侧向的立体感（正对镜头打光会把装甲倒角全抹平）。
	 */
	void UpdateHeroFill();

	/**
	 * -ShotMode 启动时调用：关掉随帧变化的特效（胶片颗粒/色散/泛光），
	 * 让同一时刻的截图可以在两次运行之间逐像素比较。
	 *
	 * 调色时如果画面自带随机颗粒，A/B 两张图的差异里永远混着噪声，
	 * 人眼无法判断"这次是变亮了还是变噪了"，数值脚本也一样。
	 */
	void ApplyDeterministicCaptureLook();

	/** 当前是否带 -ShotMode 启动 */
	static bool IsShotMode();

	/** 初始化 GAS：授予默认技能、绑定输入 */
	virtual void InitializeAbilitySystem();

	/** 把装配结果写进属性与移动参数 */
	void RefreshFromAssembly();

	/** 授予默认技能（幂等，Possess 重复调用不会重复授予） */
	void GrantDefaultAbilities();

	/** 在构造函数里创建 Enhanced Input 的 Action 与 MappingContext（不依赖资产） */
	void CreateDefaultInput();

	// ── 输入回调 ──

	void HandleMove(const struct FInputActionValue& Value);
	void HandleLook(const struct FInputActionValue& Value);
	void HandleFireStart();
	void HandleFireStop();
	void HandleDash();
	void HandleSwitchChassis();

	/** 打开/关闭改装台（M）—— 具体 UI 由玩家控制器管理 */
	void HandleToggleModding();

	UFUNCTION()
	void HandleAssemblyChanged();

	UFUNCTION()
	void HandlePartDestroyed(FGameplayTag PartTag);

	/** 部位受伤（未摧毁）—— 用来驱动 HUD 的受击反馈 */
	UFUNCTION()
	void HandlePartDamaged(FGameplayTag PartTag, float RemainingRatio);

	UFUNCTION()
	void HandleActorDisabled();

	// ── 组件 ──

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot")
	TObjectPtr<UAbilitySystemComponent> AbilitySystemComponent;

	UPROPERTY()
	TObjectPtr<URobotAttributeSet> AttributeSet;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot")
	TObjectPtr<UPartDamageComponent> PartDamage;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Robot")
	TObjectPtr<UAssemblyComponent> Assembly;

	// ── 程序化动画 ──
	//
	// 项目里没有任何动画资产，所以走路/开火/转向全靠代码摆骨骼。
	// 可见的必须是 UPoseableMeshComponent（USkeletalMeshComponent 没有
	// 设置单根骨骼变换的接口）；原网格保留但不可见，专供部位系统查询。
	// 细节见 MechProceduralAnim.h。

	UPROPERTY()
	TObjectPtr<class UPoseableMeshComponent> AnimMesh;

	FMechAnimState AnimState;

	/** 按当前机体重建动画网格并重新缓存基准姿势 */
	void RefreshAnimMesh();

	// ── 相机（第三人称）──

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<class USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	TObjectPtr<class UCameraComponent> FollowCamera;

	// ── 配置 ──

	/** 出生时的默认机体 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
	TObjectPtr<URobotChassisData> DefaultChassis;

	/** 出生时授予的技能（冲刺、基础攻击等） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
	TArray<TSubclassOf<class UGameplayAbility>> DefaultAbilities;

	/** 可切换的机体预设。按 1/2/3 循环切换，用于验证「换机体改变玩法」这一支柱。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
	TArray<TObjectPtr<URobotChassisData>> ChassisPresets;

	/** 玩家部位映射表。玩家也会被拆部位 —— 手臂被毁则无法使用该臂武器。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
	TObjectPtr<UPartMapData> PartMap;

	// ── 输入 ──

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<class UInputMappingContext> DefaultMappingContext;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<class UInputAction> MoveAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<class UInputAction> LookAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<class UInputAction> FireAction;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<class UInputAction> DashAction;

	/** 切换机体（测试用） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<class UInputAction> CycleChassisAction;

	/** 打开/关闭改装台（M） */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	TObjectPtr<class UInputAction> ModdingAction;

	/** 鼠标灵敏度 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Input")
	float LookSensitivity = 1.0f;

private:
	/** 当前机体在 ChassisPresets 中的索引 */
	int32 ChassisIndex = 0;

	/** -DebugFoot 时玩家脚底离地日志的节流（每实例，不能用函数内 static） */
	float DbgPlayerFootLastLog = -100.f;

	/** 是否正在开火（按住连发） */
	bool bFiring = false;

	/** 开火镜头抖动的剩余量（0~1），Tick 里衰减到 0 */
	float CameraShakeAmount = 0.f;

	/** -AutoFire 调试瞄准：直接瞄最近敌人（BeginPlay 按命令行设置） */
	bool bAutoFireAimDebug = false;

	/** 过热锁定的剩余秒数（进入过热时置 2 秒，见 Tick 里的热量管理） */
	float OverheatLockRemaining = 0.f;

	/** 调试用：-AutoFire 时的开火节拍 */
	float AutoFireTimer = 0.f;

	/** 调试用：-AutoDash 时的冲刺节拍 */
	float AutoDashTimer = 0.f;

	/** 调试用：-AutoSelfDestruct=<秒> 的到点时间（<=0 不启用） */
	float AutoSelfDestructAt = -1.f;

	/** 调试用：出生点，-AutoWalk 用它限制"别走太远撞墙" */
	FVector SpawnLocation = FVector::ZeroVector;

	// ── 竞技场边界（防掉出地图）──
	//
	// 关卡里的围墙是静态网格，靠它挡人有两个隐患：
	//   ① 网格碰撞是 FBX 导入时自动生成的，换资产/改导入设置就可能失效；
	//   ② 冲刺时速度高，薄墙有穿透风险。
	// 所以再加一道**代码级硬边界**：每帧把角色钳在可玩区域内，
	// 并把朝外的速度分量清零。它不依赖任何资产，永远不会失效。
	//
	// 数值来自 rebuild_arena.py 的围墙位置（内侧面）再内缩半个胶囊半径：
	//   新围墙（2026-10-19 重建）：中心线 x=-1300 / 1800，y=±1380，
	//   墙面内侧 ≈ 中心线 ±0.45m，再减胶囊半径 45cm。
	//   ⚠️ 代码边界只是**兜底**：正常情况由墙体碰撞拦人，边界值要比墙面
	//   稍微靠外一点，否则玩家会停在离墙 20cm 的"空气墙"上。
	FVector ArenaMin = FVector(-1255.f, -1335.f, -1e9f);
	FVector ArenaMax = FVector(1755.f, 1335.f, 1e9f);

	/** 掉到这个高度以下就判定"掉出地图"，拉回安全点 */
	float FallKillZ = -300.f;

	/** 最近一次站稳的位置（掉出地图后回到这里） */
	FVector LastSafeLocation = FVector::ZeroVector;

	/** 上一次记录安全位置的时间 */
	float LastSafeSampleTime = -100.f;

	/** 已回收的废料总量 */
	int32 SalvageCount = 0;

	/** 上次往日志写诊断的时间 */
	float LastDiagLogTime = -100.f;

	/** 上次记录"丢弃异常视角输入"的时间 */
	float LastLookNoiseLog = -100.f;

	/** 是否已记录过移动输入（诊断用，只记一次避免刷屏） */
	bool bLoggedMoveInput = false;

	// ── 输入自检（无需人工按键，用于区分「按键没传到窗口」和「映射没生效」）──
	bool bInputSelfTestStarted = false;

	void RunInputSelfTest();

	/** 运行时重建输入对象是否已完成 */
	bool bRuntimeInputBuilt = false;

	/**
	 * 用 NewObject(this, ...) 重新构建一整套输入对象。
	 *
	 * 为什么必须这么做：构造函数里的 CreateDefaultSubobject 建出来的
	 * UInputAction / UInputMappingContext 在蓝图实例化时不会正确地"按实例"
	 * 重建 —— 映射里保存的 Action 指针指向的是 CDO 上的旧对象，而实例上的
	 * MoveAction 是另一个对象。表现就是：
	 *   按键能进 PlayerInput（IsInputKeyDown 为真）、映射也在（映射数=10），
	 *   但 QueryKeysMappedToAction(MoveAction) 返回 0，动作永远不触发。
	 * NewObject 以本角色为 Outer 建对象，保证全部指向同一批实例对象。
	 */
	void RebuildRuntimeInput();

	/** 打印输入对象的身份（名字 + Outer），用于确认指针是否指向同一批对象 */
	void LogInputIdentity(const TCHAR* Tag);

	// ── 武器参数（放在类末尾：新增成员不能插在已反射成员之前，
	//    否则 STRUCT_OFFSET 会错位 —— 手动编译链路不重跑 UHT）──

	/**
	 * 枪口相对 forearm_R 骨骼原点的偏移（角色本地空间，厘米）。
	 * 默认值由 Blender 建模参数反推：炮管尖端在肘关节前 40cm、下 6cm。
	 */
	FVector MuzzleLocalOffset = FVector(82.f, 0.f, -4.f);

	/** 抬枪瞄准的过渡速度（每秒），越大越"脆" */
	float AimBlendSpeed = 7.f;

	/**
	 * 调试用：-SideCam 是否已经把相机从相机臂上摘下来过。
	 * 只摘一次 —— 摘下来之后 世界变换 == 相对变换，每帧手写位置才落得准。
	 */
	bool bSideCamDetached = false;

	// ── 调试相机（-SideCam / -CloseCam）──
	//
	// 为什么用独立的 CameraActor 而不是摆相机臂：
	// 相机臂的落点同时受 父组件变换 / 控制旋转 / bInheritPitch / 碰撞回缩
	// 四个因素影响，任何一个不对，画面里就看不到机体，而组件坐标读出来
	// **还是对的**（查了三轮，日志全对、画面全错）。
	// ACameraActor 没有这些耦合：把它 SetViewTarget 上去，视角就是它的
	// 世界变换，一厘米不差。调试工具不值得再跟相机臂较劲。
	//
	// ⚠️ 刻意**不加 UPROPERTY**：本机 UBT 坏掉，加了反射标记就必须重跑 UHT，
	//    否则结构体布局和 .gen.cpp 对不上，加载关卡时在引擎里崩。
	//    改用 TWeakObjectPtr —— 它不进 GC 引用图，但也因此不会悬垂。
	//
	// ⚠️⚠️ 类型用 AActor 而**不是** ACameraActor：UHT 生成的宏是**按行号**索引的
	//    （UCLASS() 展开成 FID_xxx_h_<行号>_PROLOG）。在 UCLASS() **之前**
	//    加任何一行 —— 哪怕只是一句前置声明 —— 都会让整个类找不到 PROLOG 宏，
	//    报出一串 "缺少 ; (在 <class-head> 的前面)"，看起来像语法错，其实是
	//    UHT 产物过期。改动只能加在类**末尾**（GENERATED_BODY 之后）。
	//    AActor 在 GameFramework/Character.h 里已经是完整类型，不需要前置声明。
	TWeakObjectPtr<AActor> DebugCamera;

	/** 调试相机模式：0=关 1=侧视 2=近景 */
	int32 DebugCamMode = 0;

	/** 创建/更新调试相机，并在第一帧把它设为视角目标 */
	void UpdateDebugCamera();

	/** 关卡里的英雄补光（标签 HeroFill），由 UpdateHeroFill 每帧摆位 */
	TWeakObjectPtr<AActor> HeroFillLight;

	/** 冲刺喷气推进的瞬时动态光照衰减 */
	float DashThrusterRemaining = 0.f;

	/** 检阅模式：把场景里所有敌人摆成一排、冻结 AI、隐藏玩家。
	 *  用途 = 每次改完敌人模型都要在**真实渲染管线**下看一遍，
	 *  而编辑器视口既没有后处理也不代表游戏光照。 */
	void SetupReviewStage();
};
