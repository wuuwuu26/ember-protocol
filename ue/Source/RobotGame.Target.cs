// 余火协议 —— 游戏主 Target
using UnrealBuildTool;
using System.Collections.Generic;

public class RobotGameTarget : TargetRules
{
	public RobotGameTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;

		ExtraModuleNames.AddRange(new string[] { "RobotCore", "RobotCombat", "RobotGame" });
	}
}
