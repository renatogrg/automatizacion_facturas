@echo off
REM Detiene el servicio de Windows

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Este script debe ejecutarse como ADMINISTRADOR
    pause
    exit /b 1
)

echo Deteniendo servicio SistemaFacturas...
net stop SistemaFacturas

if %errorLevel% equ 0 (
    echo ✓ Servicio detenido
) else (
    echo ✗ Error al detener el servicio
)

pause