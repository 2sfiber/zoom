; ============================================================
; ZoomDownloader - معالج تثبيت احترافي (Inno Setup 6)
; يثبت البرنامج + ينشئ اختصار سطح المكتب
; البناء: ISCC.exe installer\setup.iss
; ============================================================

#define MyAppName "ZoomDownloader"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ZoomDownloader"
#define MyAppExeName "ZoomDownloader.exe"

[Setup]
AppId={{3F2A1B4C-7D8E-4A5B-9C0D-1E2F3A4B5C6D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=ZoomDownloader-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName={#MyAppName}
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; نجعل اختصار سطح المكتب افتراضياً عبر الكود (انظر [Icons] بدون Tasks)

[Files]
Source: "..\dist\ZoomDownloader\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\ZoomDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; ملف install.bat يجلب Chromium و ffmpeg عند أول تثبيت إذا نقصا
Source: "install.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; اختصار سطح المكتب المباشر (مطلوب في المواصفات)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; تشغيل سكربت جلب التبعيات الناقصة (متصفح Chromium) بعد التثبيت
Filename: "{app}\install.bat"; Description: "تثبيت المكونات الإضافية (متصفح Chromium)"; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
