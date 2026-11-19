// 游戏模式
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "RobotGameMode.generated.h"

class ARobotCharacter;

/**
 * 游戏模式。
 *
 * 单机项目，不涉及网络复制与多人大厅，所以直接从 GameModeBase 派生，
 * 只需要指定默认 Pawn 与开局流程。
 */
UCLASS()
class ROBOTGAME_API ARobotGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ARobotGameMode();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/**
	 * 开局流程。
	 *
	 * 用 StartPlay 而不是 BeginPlay 来弹主菜单：StartPlay 是普通虚函数，
	 * 蓝图**无法**覆盖它（BeginPlay 可以被蓝图的 ReceiveBeginPlay 干扰，
	 * 之前排查灯光问题时就在这里吃过亏）。而且到 StartPlay 时玩家控制器
	 * 一定已经就绪，可以直接弹菜单。
	 */
	virtual void StartPlay() override;

	/** 玩家机体瘫痪时由角色调用（失败路径） */
	void NotifyPlayerDefeated();

	/** 玩家机体类。默认指向 C++ 类，可在编辑器里换成蓝图子类。 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Robot")
	TSubclassOf<ARobotCharacter> RobotCharacterClass;

protected:
	/**
	 * 运行时强制修正关卡灯光。
	 *
	 * 为什么放在运行时而不是关卡里：脚本设置灯光组件属性后，
	 * `save_current_level()` 并没有把变更真正落盘 —— 实测关卡里存的
	 * 仍是 Mobility=Stationary、intensity=10、real_time_capture=False。
	 * 而 Static/Stationary 灯光需要烘焙光照贴图，没有烘焙就完全不照明，
	 * 表现就是整个场景全黑。
	 *
	 * 放在 GameMode 的 BeginPlay 里，每次进关都保证灯光是对的，
	 * 不依赖关卡的保存状态。
	 */
	void EnsureLevelLighting();

	/** 汇总一局统计并弹出结算画面（只触发一次） */
	void FinishMission(bool bVictory);

private:
	/** 关卡里初始敌人数。开局 1 秒后统计（等待 Actor 注册完成）。 */
	int32 InitialEnemyCount = -1;

	/** 结算是否已经触发过（防止胜利/失败重复弹窗） */
	bool bMissionFinished = false;

	/** 本局开始时间（世界秒） */
	float MissionStartTime = 0.f;
};
