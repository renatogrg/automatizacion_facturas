@echo off
REM Crea un acceso directo en la carpeta de Inicio para autoarrancar el servicio

setlocal enabledelayedexpansion

cd /d "%~dp0.."

REM Ruta a la carpeta de Inicio
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

REM Crear carpeta si no existe
if not exist "C:\SistemaFacturas" mkdir C:\SistemaFacturas

REM Crear un script de Python que corra el watcher en C:\SistemaFacturas\
(
echo @echo off
echo cd /d "C:\SistemaFacturas"
echo call venv\Scripts\activate.bat
echo python -m src.main
) > "C:\SistemaFacturas\iniciar_servicio.bat"

REM Crear acceso directo en Startup que apunte al script en C:\SistemaFacturas\
powershell -Command ^
  "$WshShell = New-Object -ComObject WScript.Shell; " ^
  "$Shortcut = $WshShell.CreateShortcut('%STARTUP%\SistemaFacturas.lnk'); " ^
  "$Shortcut.TargetPath = 'C:\SistemaFacturas\iniciar_servicio.bat'; " ^
  "$Shortcut.WorkingDirectory = 'C:\SistemaFacturas'; " ^
  "$Shortcut.Save()"

echo.
echo ✓ Script creado en: C:\SistemaFacturas\iniciar_servicio.bat
echo ✓ Acceso directo creado en Startup (apunta al script anterior)
echo.
echo El servicio se iniciará automáticamente cuando enciendas la PC.
echo.
pause