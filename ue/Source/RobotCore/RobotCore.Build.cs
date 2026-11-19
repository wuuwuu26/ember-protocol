// RobotCore —— 基础类型、GameplayTag 声明、数据资产定义。
// 依赖方向的最底层：不允许依赖任何其他游戏模块。
using UnrealBuildTool;

public class RobotCore : ModuleRules
{
	public RobotCore(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"GameplayTags",
			// URobotModuleData 里有 TArray<TSoftClassPtr<UGameplayAbility>>，
			// UHT 生成的代码需要该类的完整定义（Z_Construct_UClass_UGameplayAbility），
			// 仅前置声明不够。这里依赖的是引擎插件而非其他游戏模块，
			// 不违反「RobotCore 不依赖任何其他游戏模块」的分层规则。
			"GameplayAbilities",
			"GameplayTasks"
		});

		PublicIncludePaths.Add(ModuleDirectory + "/Public");
	}
}
