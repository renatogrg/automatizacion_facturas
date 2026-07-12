"""
Crea (si no existen) las carpetas Consorcio/Año/Mes dentro de C:\FACTURAS
y mueve el archivo procesado a su ubicación final.
"""

import os
import shutil
from pathlib import Path

MESES = {
    1: "01-Enero", 2: "02-Febrero", 3: "03-Marzo", 4: "04-Abril",
    5: "05-Mayo", 6: "06-Junio", 7: "07-Julio", 8: "08-Agosto",
    9: "09-Setiembre", 10: "10-Octubre", 11: "11-Noviembre", 12: "12-Diciembre",
}


def mover_a_destino(ruta_origen: str, carpeta_facturas: str, nombre_consorcio_id: str, anio: int, mes: int) -> str:
    """
    Mueve el archivo a: carpeta_facturas/nombre_consorcio/año/mes/archivo
    
    Crea las carpetas si no existen.
    
    Args:
        ruta_origen: ruta actual del archivo
        carpeta_facturas: C:\FACTURAS (base)
        nombre_consorcio_id: ej. "Consorcio Wayayo" o "wayayo" 
        anio: ej. 2026
        mes: ej. 7
        
    Returns:
        Ruta final del archivo movido
    """
    try:
        # Construir la ruta destino
        carpeta_destino = Path(carpeta_facturas) / nombre_consorcio_id / str(anio) / MESES[mes]
        carpeta_destino.mkdir(parents=True, exist_ok=True)
        
        # Ruta final del archivo
        nombre_archivo = os.path.basename(ruta_origen)
        ruta_final = carpeta_destino / nombre_archivo
        
        # Si el archivo ya existe, agregar sufijo
        if ruta_final.exists():
            base, ext = os.path.splitext(nombre_archivo)
            contador = 1
            while (carpeta_destino / f"{base}_{contador}{ext}").exists():
                contador += 1
            ruta_final = carpeta_destino / f"{base}_{contador}{ext}"
        
        # Mover el archivo
        shutil.move(ruta_origen, str(ruta_final))
        return str(ruta_final)
        
    except Exception as e:
        print(f"Error moviendo archivo {ruta_origen}: {e}")
        return None