; ╔══════════════════════════════════════════════════════════╗
; ║  Legal AI Contract System — Inno Setup Installer        ║
; ║  Creates a proper Windows .exe installer                ║
; ╚══════════════════════════════════════════════════════════╝
;
; Prerequisites:
;   1. Run  python build_exe.py  first (creates dist/LegalAI/)
;   2. Install Inno Setup: https://jrsoftware.org/isdl.php
;   3. Open this file in Inno Setup Compiler and click Build
;
; Output: installer/Output/LegalAI-Setup-1.0.0.exe

[Setup]
AppName=Legal AI Contract System
AppVersion=1.0.0
AppPublisher=Legal AI
AppPublisherURL=https://github.com/ayu9x/Generative-AI-for-Automated-Legal-Contract-Drafting-and-Review
DefaultDirName={autopf}\LegalAI
DefaultGroupName=Legal AI Contract System
OutputDir=Output
OutputBaseFilename=LegalAI-Setup-1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=..\frontend\public\vite.svg
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=Legal AI Contract System
LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Bundle the entire PyInstaller output
Source: "..\dist\LegalAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcuts
Name: "{group}\Legal AI Contract System"; Filename: "{app}\LegalAI.exe"; Comment: "Start Legal AI Contract System"
Name: "{group}\Uninstall Legal AI"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{commondesktop}\Legal AI Contract System"; Filename: "{app}\LegalAI.exe"; Comment: "Start Legal AI Contract System"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
; Launch after installation
Filename: "{app}\LegalAI.exe"; Description: "Launch Legal AI Contract System"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
