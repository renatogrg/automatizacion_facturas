@echo off
REM ============================================================
REM  INSTALADOR DEL SISTEMA DE FACTURAS
REM  Instala el servicio de Windows y crea el archivo de inicio
REM  en C:\SistemaFacturas\
REM
REM  EJECUTAR COMO ADMINISTRADOR
REM ============================================================

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo  ERROR: Este script debe ejecutarse como ADMINISTRADOR.
    echo  Haz clic derecho ^> "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   INSTALANDO SISTEMA DE GESTION AUTOMATICA DE FACTURAS
echo  ============================================================
echo.

REM ── 1. Copiar programa a C:\SistemaFacturas\ ──────────────────
echo  [1/4] Copiando programa a C:\SistemaFacturas\...
if not exist "C:\SistemaFacturas" mkdir "C:\SistemaFacturas"

REM Copiar todo el proyecto (se asume que este .bat está en build\)
xcopy /E /I /Y "%~dp0.." "C:\SistemaFacturas" >nul 2>&1
if %errorLevel% neq 0 (
    echo  ERROR al copiar archivos.
    pause
    exit /b 1
)
echo  OK

REM ── 2. Crear entorno virtual e instalar dependencias ─────────
echo  [2/4] Instalando dependencias Python...
cd /d "C:\SistemaFacturas"

if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo  ERROR al instalar dependencias.
    pause
    exit /b 1
)
echo  OK

REM ── 3. Crear SistemaFacturas.bat en C:\SistemaFacturas\ ──────
echo  [3/4] Creando SistemaFacturas.bat en C:\SistemaFacturas\...

(
echo @echo off
echo REM Inicia el Sistema de Gestion Automatica de Facturas
echo cd /d "C:\SistemaFacturas"
echo call venv\Scripts\activate.bat
echo python -m src.main
echo pause
) > "C:\SistemaFacturas\SistemaFacturas.bat"

echo  OK

REM ── 4. Crear acceso directo en Inicio (autoarranque) ─────────
echo  [4/4] Configurando inicio automatico al encender la PC...

set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$sc = $ws.CreateShortcut('%STARTUP%\SistemaFacturas.lnk');" ^
  "$sc.TargetPath = 'C:\SistemaFacturas\SistemaFacturas.bat';" ^
  "$sc.WorkingDirectory = 'C:\SistemaFacturas';" ^
  "$sc.WindowStyle = 7;" ^
  "$sc.Description = 'Sistema de Gestion Automatica de Facturas';" ^
  "$sc.Save()" >nul 2>&1

echo  OK

echo.
echo  ============================================================
echo   INSTALACION COMPLETADA
echo  ============================================================
echo.
echo   Programa instalado en : C:\SistemaFacturas\
echo   Archivo de inicio     : C:\SistemaFacturas\SistemaFacturas.bat
echo   Autoarranque          : Configurado (inicio de sesion)
echo.
echo   PROXIMO PASO:
echo   Edita C:\SistemaFacturas\config\.env
echo   y coloca tu clave de API de Anthropic:
echo   ANTHROPIC_API_KEY=sk-ant-...
echo.
pause