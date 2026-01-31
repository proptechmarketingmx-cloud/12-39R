; Inno Setup Script generated as template for CRMInmobiliario
; Ajusta AppVersion, DefaultDirName y archivos incluidos según necesidades

[Setup]
AppName=CRM Inmobiliario
AppVersion=1.0.0
DefaultDirName={pf}\CRM Inmobiliario
DefaultGroupName=CRM Inmobiliario
OutputBaseFilename=CRMInmobiliario_Installer
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Ajusta la ruta al EXE generado por PyInstaller
Source: "{#ProjectDir}\dist\CRMInmobiliario.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CRM Inmobiliario"; Filename: "{app}\CRMInmobiliario.exe"
Name: "{userdesktop}\CRM Inmobiliario"; Filename: "{app}\CRMInmobiliario.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crea un acceso directo en el Escritorio"; GroupDescription: "Otras opciones:"; Flags: unchecked

[Run]
Filename: "{app}\CRMInmobiliario.exe"; Description: "Lanzar CRM Inmobiliario"; Flags: nowait postinstall skipifsilent

; Nota: reemplaza {#ProjectDir} por la ruta de tu proyecto si usas Inno desde otra carpeta.
