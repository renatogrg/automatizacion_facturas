"""
Registra cada factura procesada en el Excel del consorcio correspondiente,
y las no resueltas en Registro_Pendientes.xlsx
"""

import os
from openpyxl import Workbook, load_workbook
from pathlib import Path
from datetime import datetime

COLUMNAS = ["Fecha", "Consorcio", "Proveedor", "RUC proveedor", "Total", "Archivo"]


def registrar_factura(ruta_excel: str, fila: dict):
    """
    Agrega una fila al Excel. Si no existe, lo crea.
    
    Args:
        ruta_excel: ruta al archivo .xlsx
        fila: dict con keys del COLUMNAS
              ej. {"Fecha": "2026-07-01", "Consorcio": "Wayayo", ...}
    """
    ruta_excel = Path(ruta_excel)
    ruta_excel.parent.mkdir(parents=True, exist_ok=True)
    
    if ruta_excel.exists():
        wb = load_workbook(ruta_excel)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(COLUMNAS)
    
    # Construir fila en el orden de COLUMNAS
    nueva_fila = [fila.get(col, "") for col in COLUMNAS]
    ws.append(nueva_fila)
    wb.save(ruta_excel)


def registrar_pendiente(ruta_excel_pendientes: str, nombre_archivo: str, motivo: str = ""):
    """
    Registra una factura que no pudo ser identificada.
    
    Args:
        ruta_excel_pendientes: ruta a Registro_Pendientes.xlsx
        nombre_archivo: nombre del archivo que no se resolvió
        motivo: razón por la cual no se identificó (ej. "RUC no encontrado")
    """
    ruta_excel_pendientes = Path(ruta_excel_pendientes)
    ruta_excel_pendientes.parent.mkdir(parents=True, exist_ok=True)
    
    if ruta_excel_pendientes.exists():
        wb = load_workbook(ruta_excel_pendientes)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(["Fecha procesamiento", "Nombre archivo", "Motivo"])
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append([fecha_hoy, nombre_archivo, motivo])
    wb.save(ruta_excel_pendientes)