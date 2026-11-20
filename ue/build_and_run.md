> Language: **English** | [简体中文](./编译与运行.md)
# Compiling and Running

**Status: compile passes, editor launches** (2026-10-08) ｜ UE 5.8.3 ｜ VS Build Tools 2022

---

## I. Build Command

```bash
cd ue
"/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" \
  RobotGameEditor Win64 Development \
  -Project="C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject" \
  -NoUBA -WaitMutex
```

### ⚠️ `-NoUBA` Cannot Be Omitted

`-NoUBA` disables Unreal Build Accelerator. **In this environment, without it the build always fails**:

```
fatal error C1083: cannot open precompiled header file ...SharedPCH.*.h.pch: Access denied
```

UBA performs special file operations (`SetFileInformationByHandle`) that are persistently denied in the current environment,
so the PCH never gets generated, and then the build steps that depend on the PCH report "Access denied".
`-NoUBA` takes the classic build path, which works perfectly.

Cost: no build acceleration; the first full build takes about 40 seconds (the project has only 3 modules, so the impact is small).

> This is the parameter defined in `BuildConfiguration.cs:54`: `[CommandLine("-NoUBA", Value = "false")]`.

## II. Environment Dependencies (All in Place)

| Component | Version | Path |
|---|---|---|
| Unreal Engine | 5.8.3 | `C:\Program Files\Epic Games\UE_5.8` |
| VS Build Tools | 2022 | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools` |
| MSVC compiler | 14.44.35207 | — |
| Windows SDK | 10.0.26100.0 | `C:\Program Files (x86)\Windows Kits\10` |
| .NET Framework SDK | 4.6.2 | `C:\Program Files (x86)\Windows Kits\NETFXSDK\4.6.2` |

### About the .NET Framework SDK

UBT's `SwarmInterface` module requires it, otherwise it reports:

```
Could not find NetFxSDK install dir; this will prevent SwarmInterface from installing.
```

The UBT source `MicrosoftPlatformSDK.cs:356` hard-codes this search order:

```csharp
string[] PreferredVersions = new string[] { "4.6.2", "4.6.1", "4.6" };
```

Install it with:

```powershell
winget install --id Microsoft.DotNet.Framework.DeveloperPack.4.6 --source winget
```

**Careful not to install the wrong thing**: `Microsoft Visual Studio Tools for Applications 2022` (VSTA, 23 MB)
is **not** the C++ build tools and is useless here. What you need is `Microsoft.VisualStudio.2022.BuildTools` (about 7–12 GB).

## III. Five Errors Fixed in the First Build

| Error code | Location | Cause | Fix |
|---|---|---|---|
| C4430 | `PartDamageComponent.h:103` | `FPartBoneRule` undeclared | include `PartMapData.h` (a USTRUCT can't be forward-declared only) |
| C2065 | `RobotModuleData.h` | `Z_Construct_UClass_UGameplayAbility` undeclared | include `Abilities/GameplayAbility.h` + add GAS dependency to RobotCore |
| C2039 | `PartDamageComponent.cpp:212` | `GetReferenceSkeleton` is not a member of `USkeletalMesh` | use `GetRefSkeleton()` instead |
| C2679/C2819 | `RobotAttributeSet.cpp:77` | `Data.Target` is a reference not a pointer | `Data.Target.` instead of `Data.Target->` |
| C2027 | `AssemblyComponent.cpp:249` | `ACharacter` undefined | include `Character.h` + `CharacterMovementComponent.h` |

Another 6 C2352/C2511/C2597 errors were chains caused by the first error and disappeared once the root cause was fixed.

**Lesson**: fix UHT (Unreal Header Tool) errors first; errors in its generated `.gen.cpp` mask the real C++ errors.

## IV. Build Output

```
ue/Binaries/Win64/
├─ UnrealEditor-RobotCore.dll     113 KB
├─ UnrealEditor-RobotCombat.dll   163 KB
├─ UnrealEditor-RobotGame.dll     187 KB
├─ UnrealEditor.modules           module manifest
└─ *.pdb                          debug symbols (~60 MB each)
```

## V. Opening the Project

### Method A: Double-click `.uproject` (recommended)

Just double-click `ue/RobotGame.uproject`; the editor launches with the compiled DLLs.

### Method B: Visual Studio

Open `ue/RobotGame.sln`. `.slnx` is the new solution format, supported by VS 2022 17.10+.

For debugging, select the `Development Editor` configuration and set the startup item to `RobotGame`.

### Method C: Command line

```bash
"/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" \
  "C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject"
```

## VI. Regenerating Project Files

After changing the file structure under `Source/` (adding/removing modules, changing Build.cs):

```bash
"/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" \
  -projectfiles -project="C:/Users/25227/Documents/robot_game/ue/RobotGame.uproject" \
  -game -rocket -progress -NoUBA
```

## VII. FAQ

**Q: On first open, "Project settings missing! Using Virtual Shadow Maps requires Shader Model 6 (SM6)"**
A: Already fixed in `Config/DefaultEngine.ini`, just restart the editor.

The cause was `r.Shadow.Virtual.Enable=1` conflicting with the engine's default `PCD3D_SM5`. The fix removes SM5 and switches to SM6:

```ini
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12
-D3D12TargetedShaderFormats=PCD3D_SM5
+D3D12TargetedShaderFormats=PCD3D_SM6
```

**Trade-off**: SM6 requires DX12-class hardware, and the production plan's minimum spec GTX 1660 (Turing architecture)
supports DX12 and SM6, so the minimum spec isn't broken. The shadow quality gain in the mega-structure scene is worth it.
For compatibility with older cards, fall back to SM5 and turn off `r.Shadow.Virtual.Enable`.

**Q: Build reports PCH "Access denied"**
A: You forgot `-NoUBA`.

**Q: `Could not find NetFxSDK install dir`**
A: Missing .NET Framework SDK, see section II.

**Q: `Sdk: not found. Required version 10.0.19041.0`**
A: Missing Windows SDK. Install the VS Build Tools workload `Microsoft.VisualStudio.Workload.VCTools`.

**Q: Editor reports a missing module on open**
A: Compile first. The editor doesn't compile C++ automatically; you need to run Build.bat once.

**Q: The Chinese in the log is garbled**
A: MSVC outputs in the system code page (GBK) while the terminal reads UTF-8. Just transcode:
```bash
grep -aE "error C" build_log.txt | iconv -f GBK -t UTF-8
```

**Q: A bunch of `UbaStorageServer ... Access is denied` in the log**
A: UBA's file operations were denied. It won't appear with `-NoUBA`, and even if it does it doesn't affect the build result.
