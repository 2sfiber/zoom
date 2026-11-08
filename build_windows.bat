@echo off
REM ============================================================
REM  ZoomDownloader - سكربت البناء الكامل على ويندوز (نقرة واحدة)
REM  يقوم بـ: تثبيت بايثون deps + متصفح Playwright + بناء EXE + بناء المثبت
REM  المتطلبات: Windows 10/11 + Python 3.10+ مثبت + Inno Setup مثبت
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo [1/5] تثبيت مكتبات بايثون...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [2/5] تثبيت متصفح Playwright (Chromium)...
py -m playwright install chromium
if errorlevel 1 goto :error
REM نسخ المتصفح داخل مجلد التوزيع ليكون Standalone
py -m playwright install --help >nul

echo [3/5] بناء ملف EXE عبر PyInstaller...
py -m pip install pyinstaller
py -m PyInstaller ZoomDownloader.spec --noconfirm
if errorlevel 1 goto :error

echo [4/5] تجهيز مجلد التوزيع مع ffmpeg...
REM جلب ffmpeg تلقائياً (لدمج الصوت/الصورة من m3u8)
if not exist "dist\ZoomDownloader\ffmpeg.exe" (
  echo جلب ffmpeg...
  powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile '%TEMP%\ffmpeg.zip'"
  powershell -Command "Expand-Archive -Path '%TEMP%\ffmpeg.zip' -DestinationPath '%TEMP%\ffmpeg' -Force; Copy-Item '%TEMP%\ffmpeg\*\bin\ffmpeg.exe' -Destination 'dist\ZoomDownloader\ffmpeg.exe' -Force"
)
REM نسخ سكربت التثبيت مع التوزيع
copy /Y "installer\install.bat" "dist\ZoomDownloader\install.bat" >nul 2>&1

echo [5/5] بناء معالج التثبيت (Inno Setup)...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
  echo.
  echo ============================================================
  echo  تم بنجاح! تجد المثبت في: installer\Output\ZoomDownloader-Setup.exe
  echo ============================================================
) else (
  echo تحذير: Inno Setup غير مثبت. الملف التنفيذي جاهز في dist\ZoomDownloader\ZoomDownloader.exe
  echo حمله من: https://jrsoftware.org/isdl.php ثم أعد تشغيل هذا السكربت.
)
pause
exit /b 0

:error
echo.
echo !!! حدث خطأ. راجع الرسائل أعلاه.
pause
exit /b 1
