@echo off
REM Crea un acceso directo en la carpeta de Inicio para autoarrancar el servicio

setlocal enabledelayedexpansion

cd /d "%~dp0.."

REM Ruta a la carpeta de Inicio
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

REM Crear un script de Python que corra el watcher
(
echo @echo off
echo cd /d "%cd%"
echo call venv\Scripts\activate.bat
echo python -m src.main
) > "%STARTUP%\SistemaFacturas.bat"

echo.
echo ✓ Acceso directo creado en:
echo   %STARTUP%\SistemaFacturas.bat
echo.
echo El servicio se iniciará automáticamente cuando enciendas la PC.
echo.
pause