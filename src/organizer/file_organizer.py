"""
Crea (si no existen) las carpetas Consorcio/Anio/Mes dentro de C:\\FACTURAS
y mueve el archivo procesado a su ubicacion final.
"""

import os
import shutil

MESES = {
    1: "01-Enero", 2: "02-Febrero", 3: "03-Marzo", 4: "04-Abril",
    5: "05-Mayo", 6: "06-Junio", 7: "07-Julio", 8: "08-Agosto",
    9: "09-Setiembre", 10: "10-Octubre", 11: "11-Noviembre", 12: "12-Diciembre",
}


def mover_a_destino(ruta_origen: str, carpeta_facturas: str, nombre_consorcio: str, anio: int, mes: int) -> str:
    carpeta_destino = os.path.join(carpeta_facturas, nombre_consorcio, str(anio), MESES[mes])
    os.makedirs(carpeta_destino, exist_ok=True)
    destino = os.path.join(carpeta_destino, os.path.basename(ruta_origen))
    shutil.move(ruta_origen, destino)
    return destino
