// RobotCombat —— GAS 技能、伤害路由、部位 HP。
using UnrealBuildTool;

public class RobotCombat : ModuleRules
{
	public RobotCombat(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"GameplayTags",
			"GameplayAbilities",
			"GameplayTasks",
			"RobotCore"
		});

		PublicIncludePaths.Add(ModuleDirectory + "/Public");
	}
}
