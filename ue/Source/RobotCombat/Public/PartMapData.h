// 骨骼名 → 部位标签 的映射表
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "RobotTypes.h"
#include "PartMapData.generated.h"

/** 一条映射规则：命中这些骨骼名的部位归到同一个部位标签 */
USTRUCT(BlueprintType)
struct FPartBoneRule
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part")
	FGameplayTag PartTag;

	/**
	 * 骨骼名前缀匹配。Blender 侧命名规范为 part_upperarm_R / part_knee_L 等，
	 * 所以用前缀匹配即可覆盖左右与编号变体。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part")
	TArray<FName> BonePrefixes;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part")
	float MaxHealth = 20.f;

	/** 摧毁后掉落的废料。躯干为 0 —— 它只是伤害承受面。 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part")
	int32 SalvageValue = 5;

	/** 摧毁该部位是否直接判定死亡（核心 = true） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part")
	bool bDestructionKills = false;

	/**
	 * 暴露度倍率：同一个部位从不同方向打，伤害不同。
	 *
	 * 这是让"打部位"变成**战术**而不是"随便打哪里血条一样掉"的关键：
	 *   · 正面装甲（1.0）：核心与躯干在迎弹面上，正面硬顶
	 *   · 侧面（1.6）：装甲板薄，绕到侧翼打腿/打臂效率最高
	 *   · 背面（2.0）：散热口、电源线、维修盖板全在背面
	 *
	 * 1.0 = 无加成。数值刻意做得比较克制：背面 2 倍是"绕后值得"，不是"必须"。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part|Tactics")
	float FrontMultiplier = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part|Tactics")
	float SideMultiplier = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Part|Tactics")
	float BackMultiplier = 1.0f;
};

/**
 * 部位映射表。
 *
 * 为什么单独做成资产：同一套 PartDamageComponent 要同时服务玩家与所有敌人，
 * 而不同敌人的骨架与部位数量都不同。把"骨骼名 → 部位"这段知识外置，
 * 就能做到一套代码通吃敌我 —— 这是架构上的关键收益。
 */
UCLASS(BlueprintType)
class ROBOTCOMBAT_API UPartMapData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Parts")
	TArray<FPartBoneRule> Rules;

	/**
	 * 把命中的骨骼名翻译成部位标签。
	 * 匹配顺序按 Rules 数组顺序，先匹配到的胜出 —— 所以规则表要把
	 * 更具体的规则（part_core）放在更宽泛的规则（part_）之前。
	 */
	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	FGameplayTag ResolvePartTag(FName BoneName) const;

	/**
	 * 查找某个部位标签对应的规则。
	 * 用出参而不是返回指针 —— UHT 不允许 UFUNCTION 暴露 USTRUCT 的裸指针
	 * （报错：Inappropriate '*' on variable of type 'FPartBoneRule'）。
	 */
	UFUNCTION(BlueprintPure, Category = "Robot|Parts")
	bool FindRule(const FGameplayTag& PartTag, FPartBoneRule& OutRule) const;

	/**
	 * 用代码里的默认规则填充。
	 *
	 * 为什么规则写在 C++ 而不是让脚本填：UE 的 Python 接口无法可靠地构造
	 * FGameplayTag（tag_name 是只读的），脚本填出来的规则全是空标签，
	 * 部位系统会静默失效。规则是项目的核心知识，写在代码里更安全。
	 * 需要按敌人定制时，仍然可以在编辑器里改这个资产。
	 *
	 * @param bForPlayer true 用玩家骨架（Blender build_rig 命名），
	 *                   false 用敌人骨架（infer_bone_name 命名）
	 */
	UFUNCTION(BlueprintCallable, Category = "Robot|Parts")
	void BuildDefaultRules(bool bForPlayer);
};
