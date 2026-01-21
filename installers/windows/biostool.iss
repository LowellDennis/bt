; Inno Setup Script for HPE Server BIOS Tool
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "HPE Server BIOS Tool"
#define MyAppVersion "0.7.0"
#define MyAppPublisher "HPE"
#define MyAppURL "https://github.com/LowellDennis/bt"
#define MyAppExeName "bt.cmd"

[Setup]
AppId={{E8C9A7D1-4B2F-4E3A-9C5D-6F8A1B3E4D2C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\HPE\BIOSTool
DefaultGroupName=HPE Server BIOS Tool
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
InfoBeforeFile=..\..\README.md
OutputDir=.\output
OutputBaseFilename=BIOSTool-{#MyAppVersion}-Setup
SetupIconFile=..\..\BiosTool.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full installation"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "core"; Description: "BT Command Line Tool"; Types: full custom; Flags: fixed
Name: "vscode"; Description: "VS Code Extension"; Types: full custom
Name: "gui"; Description: "GUI Application (future)"; Types: full custom; Flags: dontinheritcheck

[Tasks]
Name: "addtopath"; Description: "Add BT to system PATH"; GroupDescription: "Additional tasks:"; Components: core
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional shortcuts:"; Components: gui; Flags: unchecked

[Files]
; Core BT Tool files
Source: "..\..\*.py"; DestDir: "{app}"; Components: core; Flags: ignoreversion
Source: "..\..\*.cmd"; DestDir: "{app}"; Components: core; Flags: ignoreversion
Source: "..\..\*.ps1"; DestDir: "{app}"; Components: core; Flags: ignoreversion
Source: "..\..\*.txt"; DestDir: "{app}"; Components: core; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Components: core; Flags: ignoreversion
Source: "..\..\attach\*"; DestDir: "{app}\attach"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\build\*"; DestDir: "{app}\build"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\clean\*"; DestDir: "{app}\clean"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\config\*"; DestDir: "{app}\config"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\create\*"; DestDir: "{app}\create"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\destroy\*"; DestDir: "{app}\destroy"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\detach\*"; DestDir: "{app}\detach"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\init\*"; DestDir: "{app}\init"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\merge\*"; DestDir: "{app}\merge"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\move\*"; DestDir: "{app}\move"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\pull\*"; DestDir: "{app}\pull"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\push\*"; DestDir: "{app}\push"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\select\*"; DestDir: "{app}\select"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\status\*"; DestDir: "{app}\status"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\switch\*"; DestDir: "{app}\switch"; Components: core; Flags: ignoreversion recursesubdirs
Source: "..\..\top\*"; DestDir: "{app}\top"; Components: core; Flags: ignoreversion recursesubdirs

; VS Code Extension
Source: "..\..\vscode-extension\*.vsix"; DestDir: "{tmp}"; Components: vscode; Flags: ignoreversion deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName} Documentation"; Filename: "{app}\README.md"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Registry]
; Register installation path for detection
Root: HKLM; Subkey: "Software\HPE\BIOSTool"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\HPE\BIOSTool"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Code]
var
  PythonInstalled: Boolean;
  VSCodeInstalled: Boolean;
  VSCodePath: String;

function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if not Result then
    Result := Exec('py', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function GetVSCodePath(): String;
var
  VSCodePaths: array of String;
  I: Integer;
begin
  Result := '';
  SetArrayLength(VSCodePaths, 4);
  VSCodePaths[0] := ExpandConstant('{pf}\Microsoft VS Code\bin\code.cmd');
  VSCodePaths[1] := ExpandConstant('{localappdata}\Programs\Microsoft VS Code\bin\code.cmd');
  VSCodePaths[2] := ExpandConstant('{pf32}\Microsoft VS Code\bin\code.cmd');
  VSCodePaths[3] := 'code'; // In PATH
  
  for I := 0 to GetArrayLength(VSCodePaths) - 1 do
  begin
    if (I < 3) and FileExists(VSCodePaths[I]) then
    begin
      Result := VSCodePaths[I];
      Exit;
    end;
  end;
  // Try code in PATH
  Result := 'code';
end;

function InitializeSetup(): Boolean;
begin
  PythonInstalled := IsPythonInstalled();
  VSCodePath := GetVSCodePath();
  VSCodeInstalled := (VSCodePath <> '');
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if CurPageID = wpSelectComponents then
  begin
    if not PythonInstalled then
    begin
      if MsgBox('Python is not installed. The BIOS Tool requires Python to run.' + #13#10 + #13#10 + 
                'Do you want to continue anyway? (You will need to install Python manually)', 
                mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
    
    if Result and WizardIsComponentSelected('vscode') and not VSCodeInstalled then
    begin
      if MsgBox('VS Code does not appear to be installed.' + #13#10 + #13#10 + 
                'The extension will be included but not installed automatically.' + #13#10 + 
                'Continue anyway?', 
                mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  EnvPath: String;
  VSIXFiles: TArrayOfString;
  I: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Install VS Code extension if selected and VS Code is installed
    if WizardIsComponentSelected('vscode') and VSCodeInstalled then
    begin
      if FindFirst(ExpandConstant('{tmp}\*.vsix'), VSIXFiles) then
      begin
        try
          for I := 0 to GetArrayLength(VSIXFiles) - 1 do
          begin
            Exec(VSCodePath, '--install-extension "' + ExpandConstant('{tmp}\') + VSIXFiles[I] + '"', 
                 '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
            if ResultCode = 0 then
              Log('Successfully installed VS Code extension: ' + VSIXFiles[I])
            else
              Log('Failed to install VS Code extension: ' + VSIXFiles[I] + ' (code: ' + IntToStr(ResultCode) + ')');
          end;
        finally
        end;
      end;
    end;
    
    // Add to PATH if selected
    if WizardIsTaskSelected('addtopath') then
    begin
      EnvPath := GetEnv('PATH');
      if Pos(ExpandConstant('{app}'), EnvPath) = 0 then
      begin
        RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 
                           'Path', EnvPath);
        EnvPath := EnvPath + ';' + ExpandConstant('{app}');
        RegWriteStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 
                          'Path', EnvPath);
      end;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  EnvPath: String;
  AppPath: String;
  StartPos: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Remove from PATH
    AppPath := ExpandConstant('{app}');
    if RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 
                          'Path', EnvPath) then
    begin
      // Remove our path
      StringChangeEx(EnvPath, ';' + AppPath, '', True);
      StringChangeEx(EnvPath, AppPath + ';', '', True);
      StringChangeEx(EnvPath, AppPath, '', True);
      RegWriteStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 
                        'Path', EnvPath);
    end;
  end;
end;
