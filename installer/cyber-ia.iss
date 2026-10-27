; ================================================================================
; ⚡ CYBER-IA // Instalador Autónomo de Escritorio (Inno Setup 6)
; Arquitectura: Windows x64 | PyTorch CUDA + FastAPI Subordinado + Tauri/Rust GUI
; Copyright (C) 2026 MightyWolf117 y Colaboradores. Licencia GNU GPLv3
; ================================================================================

#define MyAppName "CYBER-IA"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MightyWolf117"
#define MyAppURL "https://github.com/MightyWolf117/IA-Interface-for-Desktop"
#define MyAppExeName "cyber-ia.exe"

[Setup]
; Identificador de Aplicación (GUID único)
AppId={{D29E7F46-7781-4C5C-9A82-84F4BFB0F6B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Directorios de Instalación
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Licencia y Políticas de Uso Obligatorias
LicenseFile=..\interface\src-tauri\INSTALLER_LICENSE.txt

; Identidad Gráfica Cyberpunk HUD
SetupIconFile=..\interface\src-tauri\icons\icon.ico
WizardImageFile=..\interface\src-tauri\icons\nsis_sidebar.bmp
WizardSmallImageFile=..\interface\src-tauri\icons\inno_header.bmp
WizardStyle=modern

; Compatibilidad 64-bit y Privilegios
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Configuración de Salida y Compresión de Alto Rendimiento (>2 GB soportado nativamente)
OutputDir=output
OutputBaseFilename=CYBER-IA_1.0.0_x64-setup
Compression=lzma2/ultra64
SolidCompression=yes
DiskSpanning=no

; Desinstalador y Control en Sistema
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} // Neural Desktop Interface

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
spanish.BeveledLabel=CYBER-IA // Neural Desktop Interface
english.BeveledLabel=CYBER-IA // Neural Desktop Interface

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; 1. Binario Principal de la Interfaz Gráfica (Rust + Tauri)
Source: "..\interface\src-tauri\target\release\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; 2. Dependencia Interna: Backend de IA Compilado (PyTorch CUDA + FastAPI)
Source: "..\interface\src-tauri\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

; 3. Licencia y Documentación Oficial
Source: "..\interface\src-tauri\INSTALLER_LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Accesos Directos del Menú Inicio y Escritorio
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
; Ejecución post-instalación
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
