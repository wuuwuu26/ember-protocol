# -*- coding: utf-8 -*-
p = r'ue/Source/RobotGame/Private/RobotPlayerController.cpp'
s = open(p, encoding='utf-8').read()
s = s.replace('''			if (!FScreenshotRequest::IsScreenshotRequested())
			{
				FScreenshotRequest::RequestScreenshot(true);
				UE_LOG(LogTemp, Warning, TEXT("[连拍] 定时抓图 t=%.1fs"),''', '''			if (!FScreenshotRequest::IsScreenshotRequested())
			{
				CaptureShot(this);
				UE_LOG(LogTemp, Warning, TEXT("[连拍] 定时抓图 t=%.1fs"),''')
s = s.replace('''			if (!FScreenshotRequest::IsScreenshotRequested())
			{
				FScreenshotRequest::RequestScreenshot(true);
				UE_LOG(LogTemp, Log, TEXT("[连拍] 补拍一张（t=%.1f）"),''', '''			if (!FScreenshotRequest::IsScreenshotRequested())
			{
				CaptureShot(this);
				UE_LOG(LogTemp, Log, TEXT("[连拍] 补拍一张（t=%.1f）"),''')
s = s.replace('''	FScreenshotRequest::RequestScreenshot(true);
	--ShotBurstRemaining;''', '''	CaptureShot(this);
	--ShotBurstRemaining;''')
s = s.replace('''					if (!FScreenshotRequest::IsScreenshotRequested())
					{
						FScreenshotRequest::RequestScreenshot(true);
						UE_LOG(LogTemp, Warning,
							TEXT("[改装调试] 面板内补拍一张（真实时间 %.1fs）"), E);''', '''					if (!FScreenshotRequest::IsScreenshotRequested())
					{
						CaptureShot(this);
						UE_LOG(LogTemp, Warning,
							TEXT("[改装调试] 面板内补拍一张（真实时间 %.1fs）"), E);''')
open(p, 'w', encoding='utf-8', newline='').write(s)
print('remaining raw calls:', s.count('FScreenshotRequest::RequestScreenshot(true);'))
