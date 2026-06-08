; Agent Meeting Room — Inno Setup Script
; Requires Inno Setup 6+ from https://jrsoftware.org/isinfo.php
; Run: iscc AgentMeetingRoom_Setup.iss

#define AppName      "Agent Meeting Room"
#define AppVersion   "1.10.0"
#define AppPublisher "Ghraven"
#define AppURL       "https://github.com/GhravenLabs/Agent-Meeting-Room"
#define AppExeName   "AgentMeetingRoom.exe"

[Setup]
AppId={{8F3A2E1D-7C4B-4F9A-B2D6-1E5A8C3F7B9D}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\AgentMeetingRoom
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=AgentMeetingRoom-{#AppVersion}-Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=100
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline

; Uninstall info
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";    GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startmenuicon";  Description: "Create a &Start Menu shortcut"; GroupDescription: "Additional icons:"; Flags: checked

[Files]
; Main executable (built by PyInstaller)
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Config template — copied to app dir, user fills in API key
Source: ".env.example";  DestDir: "{app}"; DestName: ".env.example"; Flags: ignoreversion

; Icon asset
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

; README for reference
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
; Start Menu
Name: "{group}\{#AppName}";                    Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Uninstall {#AppName}";          Filename: "{uninstallexe}"

; Desktop (optional task)
Name: "{autodesktop}\{#AppName}";              Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[Code]
// Check if Ollama is installed and warn if not
function InitializeSetup(): Boolean;
var
  OllamaPath: string;
begin
  Result := True;
  if not RegQueryStringValue(HKLM, 'SOFTWARE\Ollama', 'InstallDir', OllamaPath) then
  begin
    if MsgBox(
      'Ollama does not appear to be installed.' + #13#10 + #13#10 +
      'Agent Meeting Room uses Ollama to run local AI models.' + #13#10 +
      'You can install it from https://ollama.com after setup.' + #13#10 + #13#10 +
      'Continue installing Agent Meeting Room anyway?',
      mbConfirmation, MB_YESNO
    ) = IDNO then
      Result := False;
  end;
end;

// After install, offer to open .env for API key setup
procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvSrc, EnvDest: string;
begin
  if CurStep = ssPostInstall then
  begin
    EnvSrc  := ExpandConstant('{app}\.env.example');
    EnvDest := ExpandConstant('{app}\.env');
    // Copy .env.example to .env if .env doesn't exist yet
    if not FileExists(EnvDest) then
      FileCopy(EnvSrc, EnvDest, False);
  end;
end;
