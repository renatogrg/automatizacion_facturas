@echo off
REM Inicia el servicio de Windows

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Este script debe ejecutarse como ADMINISTRADOR
    pause
    exit /b 1
)

echo Iniciando servicio SistemaFacturas...
net start SistemaFacturas

if %errorLevel% equ 0 (
    echo ✓ Servicio iniciado
) else (
    echo ✗ Error al iniciar el servicio
)

pause