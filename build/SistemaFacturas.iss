; ============================================================
;  INNO SETUP - Sistema de Gestión Automática de Facturas
;  Compilar: abrir con Inno Setup Compiler y presionar F9
;  Descarga: https://jrsoftware.org/isdl.php
; ============================================================

#define AppName    "Sistema de Facturas"
#define AppVersion "1.0"
#define AppPublisher "Tu Empresa"
#define InstallDir "C:\SistemaFacturas"
#define FacturasDir "C:\FACTURAS"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={#InstallDir}
DisableDirPage=yes
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=SistemaFacturas_Instalador
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
; SetupIconFile=..\assets\icono.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Código fuente
Source: "..\src\*"; DestDir: "{app}\src"; Flags: recursesubdirs createallsubdirs ignoreversion

; Tesseract OCR (instalador externo incluido en el paquete)
Source: "tesseract-setup.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

; Poppler binaries (requerido por pdf2image para convertir PDF a imagen)
; Extraer el ZIP de poppler en build\poppler\ antes de compilar
Source: "poppler\*"; DestDir: "{app}\poppler"; Flags: recursesubdirs createallsubdirs ignoreversion

; Paquetes de idioma español para Tesseract
Source: "spa.traineddata"; DestDir: "{commonpf64}\Tesseract-OCR\tessdata"; Flags: ignoreversion uninsneveruninstall
Source: "spa_old.traineddata"; DestDir: "{commonpf64}\Tesseract-OCR\tessdata"; Flags: ignoreversion uninsneveruninstall

; Requirements
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; Script de arranque - está en la misma carpeta que el .iss
Source: "SistemaFacturas.bat"; DestDir: "{app}"; Flags: ignoreversion

; GROQ API Key
Source: "..\config\.env"; DestDir: "{app}\config"; DestName: ".env"; Flags: ignoreversion

; Consorcios (editable: agregar/quitar consorcios)
Source: "..\config\consorcios.json"; DestDir: "{app}\config"; Flags: ignoreversion

; Configuración general
Source: "..\config\settings.json"; DestDir: "{app}\config"; Flags: ignoreversion

; Credenciales Google Drive
Source: "..\config\google_credentials.json"; DestDir: "{app}\config"; Flags: ignoreversion
; google_token.json NO se incluye — se genera automáticamente al primer inicio
; cuando el usuario autoriza con su cuenta de Google Drive

; Instrucciones para cambiar credenciales
; Source: "..\config\README_CREDENCIALES.txt"; DestDir: "{app}\config"; Flags: ignoreversion

[Dirs]
; Carpeta raíz de facturas en C:\
Name: "{#FacturasDir}"
Name: "{#FacturasDir}\ENTRADA_FACTURA"
Name: "{#FacturasDir}\FACTURAS PENDIENTES"
Name: "{#FacturasDir}\FACTURAS PENDIENTES\Facturas duplicadas"

; Logs internos
Name: "{app}\logs"

[Icons]
; Acceso directo en Escritorio (inicio MANUAL, sin autoarranque)
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\SistemaFacturas.bat"; WorkingDir: "{app}"; Comment: "Iniciar el Sistema de Gestión Automática de Facturas"

[Run]
; 1. Instalar Tesseract OCR silenciosamente
Filename: "{tmp}\tesseract-setup.exe"; Parameters: "/S"; StatusMsg: "Instalando Tesseract OCR..."; Flags: waituntilterminated

; 2. Crear venv e instalar dependencias Python
Filename: "{cmd}"; Parameters: "/c cd /d ""{app}"" && python -m venv venv && venv\Scripts\python.exe -m pip install -r requirements.txt --quiet"; StatusMsg: "Instalando dependencias Python (puede tardar unos minutos)..."; Flags: runhidden waituntilterminated

[UninstallDelete]
Type: filesandordirs; Name: "{app}\venv"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\src\__pycache__"

[Messages]
FinishedLabel=Instalación completada correctamente.%n%n▶  Doble clic en "Sistema de Facturas" en el Escritorio para iniciar.%n%nCarpeta de facturas : C:\FACTURAS\%n  Coloca las facturas en: C:\FACTURAS\ENTRADA_FACTURA
