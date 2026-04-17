[Setup]
AppName=AI Multi Agent
AppVersion=1.0
AppPublisher=Muhammad Haris Imtiaz
DefaultDirName={userdocs}\AIResearchAgent
DefaultGroupName=AI Research Agent
OutputDir=P:\projects\multi-agent-researcher\dist
OutputBaseFilename=AI-Research-Agent-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
PrivilegesRequired=lowest


[Messages]
WelcomeLabel1=Welcome to AI Research Agent
WelcomeLabel2=This will install AI Research Agent on your computer.%n%nThe setup will:%n%n  - Install the AI Research Agent app%n  - Download the AI model (qwen2.5 ~1GB)%n  - Install all required components%n  - Create a desktop shortcut%n%nClick Next to continue.

[Files]
Source: "P:\projects\multi-agent-researcher\agents\*"; DestDir: "{app}\agents"; Flags: recursesubdirs
Source: "P:\projects\multi-agent-researcher\graph\*"; DestDir: "{app}\graph"; Flags: recursesubdirs
Source: "P:\projects\multi-agent-researcher\tools\*"; DestDir: "{app}\tools"; Flags: recursesubdirs
Source: "P:\projects\multi-agent-researcher\output\*"; DestDir: "{app}\output"; Flags: recursesubdirs
Source: "P:\projects\multi-agent-researcher\app\*"; DestDir: "{app}\app"; Flags: recursesubdirs
Source: "P:\projects\multi-agent-researcher\pyproject.toml"; DestDir: "{app}"
Source: "P:\projects\multi-agent-researcher\uv.lock"; DestDir: "{app}"
Source: "P:\projects\multi-agent-researcher\launch.bat"; DestDir: "{app}"
Source: "P:\projects\multi-agent-researcher\setup.bat"; DestDir: "{app}"
Source: "P:\projects\multi-agent-researcher\hide.vbs"; DestDir: "{app}"
Source: "P:\projects\multi-agent-researcher\.env.example"; DestDir: "{app}"; DestName: ".env"

[Icons]
Name: "{userdesktop}\AI Research Agent"; Filename: "wscript.exe"; Parameters: "hide.vbs"; WorkingDir: "{app}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 13

[Run]
Filename: "{app}\setup.bat"; Description: "Run first-time setup (download AI model + install dependencies)"; Flags: postinstall waituntilterminated shellexec; Parameters: ""; WorkingDir: "{app}"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"