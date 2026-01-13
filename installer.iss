; Inno Setup Installer Script for ProtectSecure
; Compile this script with Inno Setup Compiler

[Setup]
AppName=ProtectSecure
AppVersion=1.0.1
AppPublisher=ProtectSecure
AppPublisherURL=https://github.com/yourusername/protectsecure
DefaultDirName={autopf}\ProtectSecure
DefaultGroupName=ProtectSecure
AllowNoIcons=yes
LicenseFile=
OutputDir=Output
OutputBaseFilename=ProtectSecure_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\ProtectSecure.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ProtectSecure"; Filename: "{app}\ProtectSecure.exe"
Name: "{group}\{cm:UninstallProgram,ProtectSecure}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\ProtectSecure"; Filename: "{app}\ProtectSecure.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\ProtectSecure"; Filename: "{app}\ProtectSecure.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\ProtectSecure.exe"; Description: "{cm:LaunchProgram,ProtectSecure}"; Flags: nowait postinstall skipifsilent

[Code]
// Support for silent installation and automatic restart
var
  RestartApp: Boolean;

procedure InitializeWizard();
begin
  RestartApp := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // If running silently, mark to restart the application
    if WizardSilent then
    begin
      RestartApp := True;
    end;
  end
  else if (CurStep = ssDone) and RestartApp then
  begin
    // Restart the application after silent installation
    Exec(ExpandConstant('{app}\ProtectSecure.exe'), '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
