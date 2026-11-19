// 余火协议 —— 编辑器 Target
using UnrealBuildTool;
using System.Collections.Generic;

public class RobotGameEditorTarget : TargetRules
{
	public RobotGameEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;

		ExtraModuleNames.AddRange(new string[] { "RobotCore", "RobotCombat", "RobotGame" });
	}
}
