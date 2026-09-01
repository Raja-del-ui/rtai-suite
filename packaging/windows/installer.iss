
; Inno Setup script — Royal-Sec Tactical Console
#define MyAppName "Royal-Sec rtai-suite"
#define MyAppVersion "4.1.0-military"
#define MyAppPublisher "Royal-Sec Ltd"
#define MyAppURL "https://royal-sec.com"
#define MyAppExeName "Royal-Sec-rtai-suite.exe"

[Setup]
AppId={{8E4A9F2C-7B5D-4E2A-9F8C-123456789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={pf}\Royal-Sec\rtai-suite
DefaultGroupName=Royal-Sec
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Royal-Sec-rtai-suite-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\..\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\Royal-Sec-rtai-suite.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\EULA.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  MsgBox('Royal-Sec Tactical Console will be installed.' + #13#10 + 'First launch will prompt to set a GUI password (PBKDF2, audit-logged).', mbInformation, MB_OK);
  Result := True;
end;
