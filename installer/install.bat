@echo off
REM ============================================================
REM  ZoomDownloader - سكربت ما بعد التثبيت (يعمل تلقائياً من المثبت)
REM  يجلب أي تبعيات ناقصة: Chromium الخاص بـ Playwright + ffmpeg
REM ============================================================
setlocal
set APPDIR=%~dp0

echo [ZoomDownloader] فحص التبعيات...

REM 1) Chromium - يأتي مدمجاً مع PyInstaller عادة عبر ms-playwright.
REM    إن لم يوجد، نزّل متصفح Chromium المحمول.
if not exist "%APPDIR%ms-playwright" (
  echo Chromium غير مدمج. سيستخدم البرنامج متصفح النظام أو سيطلبه عند أول تشغيل.
  REM ملاحظة: نسخة الـ EXE المبنية عبر build_windows.bat تتضمن المتصفح
  REM لأن playwright install تم قبل PyInstaller مع مجلد %USERPROFILE% قابل للنقل.
)

REM 2) ffmpeg - ضروري لدمج m3u8
where ffmpeg >nul 2>&1
if errorlevel 1 (
  if not exist "%APPDIR%ffmpeg.exe" (
    echo جلب ffmpeg...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile \"$env:TEMP\ffmpeg.zip\"; Expand-Archive -Path \"$env:TEMP\ffmpeg.zip\" -DestinationPath \"$env:TEMP\ffmpeg\" -Force; Copy-Item \"$env:TEMP\ffmpeg\*\bin\ffmpeg.exe\" -Destination '%APPDIR%ffmpeg.exe' -Force; echo OK } catch { echo FAIL: $_ }"
  )
)

echo [ZoomDownloader] اكتمل فحص التبعيات.
exit /b 0
