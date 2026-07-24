@echo off
title Sistema de Gestion Automatica de Facturas
cd /d "C:\SistemaFacturas"

REM Agregar Poppler al PATH local (solo para esta sesión)
set PATH=%PATH%;C:\SistemaFacturas\poppler\Library\bin

call venv\Scripts\activate.bat
python -m src.main
pause