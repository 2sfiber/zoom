; ZoomDownloader - معالج تثبيت NSIS
; البناء: makensis /DVERSION=1.0.0 installer\setup.nsi  (يتطلب مجلد dist\ZoomDownloader)

!ifndef VERSION
  !define VERSION "1.1.0"
!endif

!define APPNAME "ZoomDownloader"
!define EXENAME "ZoomDownloader.exe"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

Unicode true
Name "${APPNAME}"
OutFile "..\installer-output\ZoomDownloader-Setup.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "InstallDir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma
BrandingText "${APPNAME} ${VERSION}"

!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXENAME}"
!define MUI_FINISHPAGE_RUN_TEXT "تشغيل ${APPNAME} الآن"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Arabic"
!insertmacro MUI_LANGUAGE "English"

Section "ZoomDownloader" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "..\dist\ZoomDownloader\*.*"

  ; اختصار سطح المكتب
  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXENAME}"
  ; اختصار قائمة ابدأ
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXENAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall ${APPNAME}.lnk" "$INSTDIR\Uninstall.exe"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\${APPNAME}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "${UNINST_KEY}" "Publisher" "${APPNAME}"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\${EXENAME}"
  WriteRegStr HKLM "${UNINST_KEY}" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "${UNINST_KEY}"
  DeleteRegKey HKLM "Software\${APPNAME}"
SectionEnd
