r"""
Organiza facturas en estructura Consorcio/Año/Mes.

Solo local en C:\FACTURAS\. Drive se maneja por API en processor.py.
"""

import os
import shutil
from pathlib import Path

MESES = {
    1:  "01-Enero",    2:  "02-Febrero",  3:  "03-Marzo",
    4:  "04-Abril",    5:  "05-Mayo",     6:  "06-Junio",
    7:  "07-Julio",    8:  "08-Agosto",   9:  "09-Setiembre",
    10: "10-Octubre",  11: "11-Noviembre", 12: "12-Diciembre",
}

CARPETA_PENDIENTES  = "FACTURAS PENDIENTES"
CARPETA_DUPLICADAS  = "Facturas duplicadas"


def _nombre_sin_conflicto(carpeta: Path, nombre_archivo: str) -> Path:
    """Agrega sufijo _1, _2, … si el archivo ya existe."""
    ruta = carpeta / nombre_archivo
    if not ruta.exists():
        return ruta
    base, ext = os.path.splitext(nombre_archivo)
    n = 1
    while (carpeta / f"{base}_{n}{ext}").exists():
        n += 1
    return carpeta / f"{base}_{n}{ext}"


def mover_a_destino(
    ruta_origen: str,
    carpeta_local: str,
    nombre_consorcio: str,
    anio: int,
    mes: int,
) -> str:
    """
    Mueve archivo a Consorcio/Año/Mes en local.
    
    Returns:
        Ruta final local del archivo
    """
    carpeta_dest = (
        Path(carpeta_local) / nombre_consorcio / str(anio) / MESES[mes]
    )

    try:
        carpeta_dest.mkdir(parents=True, exist_ok=True)
        nombre = Path(ruta_origen).name
        ruta_final = _nombre_sin_conflicto(carpeta_dest, nombre)
        shutil.move(ruta_origen, str(ruta_final))
        return str(ruta_final)
    except Exception as e:
        print(f"  ❌ Error moviendo a local: {e}")
        return ""


def mover_a_pendientes(
    ruta_origen: str,
    carpeta_local: str,
    es_duplicado: bool = False,
) -> str:
    """
    Mueve archivo a FACTURAS PENDIENTES\ (o Facturas duplicadas\ si es duplicado).
    
    Returns:
        Ruta final local
    """
    subcarpeta = CARPETA_DUPLICADAS if es_duplicado else ""
    carpeta_dest = Path(carpeta_local) / CARPETA_PENDIENTES
    if subcarpeta:
        carpeta_dest = carpeta_dest / subcarpeta

    try:
        carpeta_dest.mkdir(parents=True, exist_ok=True)
        nombre = Path(ruta_origen).name
        ruta_final = _nombre_sin_conflicto(carpeta_dest, nombre)
        shutil.move(ruta_origen, str(ruta_final))
        return str(ruta_final)
    except Exception as e:
        print(f"  ❌ Error moviendo a PENDIENTES: {e}")
        return ""


def copiar_a_pendientes(
    ruta_origen: str,
    carpeta_local: str,
    carpeta_drive: str = "",
    drive_habilitado: bool = False,
    es_duplicado: bool = False,
) -> str:
    """Alias para compatibilidad."""
    return mover_a_pendientes(ruta_origen, carpeta_local, es_duplicado=es_duplicado)