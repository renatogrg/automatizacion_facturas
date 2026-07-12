"""
Registra cada factura procesada en el Excel del consorcio correspondiente,
y las no resueltas en Registro_Pendientes.xlsx
"""

import os
from openpyxl import Workbook, load_workbook

COLUMNAS = ["Fecha", "Consorcio", "Proveedor", "RUC proveedor", "Total", "Archivo"]


def registrar_factura(ruta_excel: str, fila: dict):
    if os.path.exists(ruta_excel):
        wb = load_workbook(ruta_excel)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(COLUMNAS)
    ws.append([fila.get(col, "") for col in COLUMNAS])
    wb.save(ruta_excel)
