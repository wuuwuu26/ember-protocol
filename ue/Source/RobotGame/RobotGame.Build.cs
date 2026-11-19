// RobotGame —— 主游戏模块：角色、装配、输入、存档。
using UnrealBuildTool;

public class RobotGame : ModuleRules
{
	public RobotGame(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"GameplayTags",
			"GameplayAbilities",
			"GameplayTasks",
			"NavigationSystem",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate",
			"SlateCore",
			"ProceduralMeshComponent",
			"RobotCore",
			"RobotCombat"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"RenderCore",
			// FDisplayMetrics（读取桌面分辨率，用于窗口尺寸适配）在 ApplicationCore 里
			"ApplicationCore"
		});

		PublicIncludePaths.Add(ModuleDirectory + "/Public");
	}
}
