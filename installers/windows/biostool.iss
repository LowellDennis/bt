; Inno Setup Script for HPE Server BIOS Tool
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "HPE Server BIOS Tool"
#define MyAppVersion "0.9.0"
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
; LicenseFile=..\..\LICENSE
InfoBeforeFile=..\..\README.md
OutputDir=.\output
OutputBaseFilename=BIOSTool-{#MyAppVersion}-Setup
SetupIconFile=..\..\.gui\biostool.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full installation"

[Tasks]
Name: "addtopath"; Description: "Add BT to system PATH"; GroupDescription: "Additional tasks:"
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Core BT Tool files
Source: "..\..\*.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\*.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\*.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\*.sh"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\*.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\attach\*"; DestDir: "{app}\attach"; Flags: ignoreversion recursesubdirs
Source: "..\..\build\*"; DestDir: "{app}\build"; Flags: ignoreversion recursesubdirs
Source: "..\..\clean\*"; DestDir: "{app}\clean"; Flags: ignoreversion recursesubdirs
Source: "..\..\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs
Source: "..\..\create\*"; DestDir: "{app}\create"; Flags: ignoreversion recursesubdirs
Source: "..\..\destroy\*"; DestDir: "{app}\destroy"; Flags: ignoreversion recursesubdirs
Source: "..\..\detach\*"; DestDir: "{app}\detach"; Flags: ignoreversion recursesubdirs
Source: "..\..\init\*"; DestDir: "{app}\init"; Flags: ignoreversion recursesubdirs
Source: "..\..\merge\*"; DestDir: "{app}\merge"; Flags: ignoreversion recursesubdirs
Source: "..\..\move\*"; DestDir: "{app}\move"; Flags: ignoreversion recursesubdirs
Source: "..\..\pull\*"; DestDir: "{app}\pull"; Flags: ignoreversion recursesubdirs
Source: "..\..\push\*"; DestDir: "{app}\push"; Flags: ignoreversion recursesubdirs
Source: "..\..\select\*"; DestDir: "{app}\select"; Flags: ignoreversion recursesubdirs
Source: "..\..\status\*"; DestDir: "{app}\status"; Flags: ignoreversion recursesubdirs
Source: "..\..\switch\*"; DestDir: "{app}\switch"; Flags: ignoreversion recursesubdirs
Source: "..\..\top\*"; DestDir: "{app}\top"; Flags: ignoreversion recursesubdirs

; GUI Application files
Source: "..\..\.gui\btgui.py"; DestDir: "{app}\.gui"; Flags: ignoreversion
Source: "..\..\.gui\biostool.ico"; DestDir: "{app}\.gui"; Flags: ignoreversion skipifsourcedoesntexist

; VS Code Extension (included if .vsix exists, installed if VS Code detected)
Source: "..\..\.vscode-extension\*.vsix"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName} Documentation"; Filename: "{app}\README.md"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{group}\BIOS Tool GUI"; Filename: "{code:GetPythonwPath}"; Parameters: """{app}\.gui\btgui.py"""; WorkingDir: "{app}"; IconFilename: "{app}\.gui\biostool.ico"
Name: "{autodesktop}\BIOS Tool GUI"; Filename: "{code:GetPythonwPath}"; Parameters: """{app}\.gui\btgui.py"""; WorkingDir: "{app}"; IconFilename: "{app}\.gui\biostool.ico"; Tasks: desktopicon

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

function GetPythonwPath(Param: String): String;
var
  PythonPath: String;
begin
  // Try to find pyw.exe in common Python installation locations
  // First check the Windows directory (Python Launcher for Windows)
  PythonPath := ExpandConstant('{win}\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  // Check the Python Launcher location
  PythonPath := ExpandConstant('{localappdata}\Programs\Python\Launcher\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  // Check Windows App alias location
  PythonPath := ExpandConstant('{localappdata}\Microsoft\WindowsApps\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  // Check common Python install paths (various versions)
  PythonPath := 'C:\Python314\pyw.exe';
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := 'C:\Python313\pyw.exe';
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := 'C:\Python312\pyw.exe';
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := ExpandConstant('{pf}\Python314\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := ExpandConstant('{pf}\Python313\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := ExpandConstant('{pf}\Python312\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := ExpandConstant('{localappdata}\Programs\Python\Python314\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := ExpandConstant('{localappdata}\Programs\Python\Python313\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  PythonPath := ExpandConstant('{localappdata}\Programs\Python\Python312\pyw.exe');
  if FileExists(PythonPath) then
  begin
    Result := PythonPath;
    Exit;
  end;
  
  // Fallback to just pyw.exe (relies on PATH)
  Result := 'pyw.exe';
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
  
  if CurPageID = wpWelcome then
  begin
    if not PythonInstalled then
    begin
      if MsgBox('Python is not installed. The BIOS Tool requires Python to run.' + #13#10 + #13#10 + 
                'Do you want to continue anyway? (You will need to install Python manually)', 
                mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  EnvPath: String;
  FindRec: TFindRec;
  PythonExe: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Find a working Python executable for pip
    PythonExe := '';
    if FileExists(ExpandConstant('{win}\py.exe')) then
      PythonExe := ExpandConstant('{win}\py.exe')
    else if FileExists('C:\Python314\python.exe') then
      PythonExe := 'C:\Python314\python.exe'
    else if FileExists('C:\Python313\python.exe') then
      PythonExe := 'C:\Python313\python.exe'
    else if FileExists('C:\Python312\python.exe') then
      PythonExe := 'C:\Python312\python.exe'
    else if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python314\python.exe')) then
      PythonExe := ExpandConstant('{localappdata}\Programs\Python\Python314\python.exe')
    else if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python313\python.exe')) then
      PythonExe := ExpandConstant('{localappdata}\Programs\Python\Python313\python.exe')
    else if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python312\python.exe')) then
      PythonExe := ExpandConstant('{localappdata}\Programs\Python\Python312\python.exe')
    else if FileExists(ExpandConstant('{pf}\Python314\python.exe')) then
      PythonExe := ExpandConstant('{pf}\Python314\python.exe')
    else if FileExists(ExpandConstant('{pf}\Python313\python.exe')) then
      PythonExe := ExpandConstant('{pf}\Python313\python.exe')
    else if FileExists(ExpandConstant('{pf}\Python312\python.exe')) then
      PythonExe := ExpandConstant('{pf}\Python312\python.exe');
    
    // Install Python dependencies if we found Python
    if PythonExe <> '' then
    begin
      Log('Installing Python dependencies using: ' + PythonExe);
      
      // Show progress to user
      WizardForm.StatusLabel.Caption := 'Installing Python dependencies (PyQt6, wakepy)...';
      WizardForm.StatusLabel.Update;
      
      // PyQt6 - required for GUI application (install first as it's required)
      if Exec(PythonExe, '-m pip install PyQt6', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      begin
        if ResultCode = 0 then
          Log('Successfully installed PyQt6')
        else
        begin
          Log('Failed to install PyQt6 (code: ' + IntToStr(ResultCode) + ')');
          MsgBox('Warning: Failed to install PyQt6 (required for GUI).' + #13#10 + #13#10 +
                 'Please run this command manually after installation:' + #13#10 +
                 '"' + PythonExe + '" -m pip install PyQt6', mbInformation, MB_OK);
        end;
      end
      else
      begin
        Log('Could not execute pip for PyQt6');
        MsgBox('Warning: Could not install PyQt6 (required for GUI).' + #13#10 + #13#10 +
               'Please run this command manually after installation:' + #13#10 +
               '"' + PythonExe + '" -m pip install PyQt6', mbInformation, MB_OK);
      end;
      
      // wakepy - keeps system awake during builds (optional)
      if Exec(PythonExe, '-m pip install wakepy', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      begin
        if ResultCode = 0 then
          Log('Successfully installed wakepy')
        else
          Log('Failed to install wakepy (code: ' + IntToStr(ResultCode) + ') - optional dependency');
      end;
      
      WizardForm.StatusLabel.Caption := '';
    end
    else
    begin
      Log('Could not find Python executable for dependency installation');
      MsgBox('Warning: Could not find Python to install dependencies.' + #13#10 + #13#10 +
             'The GUI requires PyQt6. Please install it manually:' + #13#10 +
             'python -m pip install PyQt6', mbInformation, MB_OK);
    end;

    // Install VS Code extension if VS Code is installed
    if VSCodeInstalled then
    begin
      if FindFirst(ExpandConstant('{tmp}\*.vsix'), FindRec) then
      begin
        try
          repeat
            Exec(VSCodePath, '--install-extension "' + ExpandConstant('{tmp}\') + FindRec.Name + '"', 
                 '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
            if ResultCode = 0 then
              Log('Successfully installed VS Code extension: ' + FindRec.Name)
            else
              Log('Failed to install VS Code extension: ' + FindRec.Name + ' (code: ' + IntToStr(ResultCode) + ')');
          until not FindNext(FindRec);
        finally
          FindClose(FindRec);
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
