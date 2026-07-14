r"""
Organiza facturas en la estructura Consorcio/Año/Mes,
tanto en la carpeta local (C:\FACTURAS) como en Drive (G:\Mi unidad\FACTURAS).
...
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


def _drive_disponible(carpeta_drive: str) -> bool:
    """
    Verifica si la unidad de Drive está montada y accesible.
    No requiere internet — solo verifica que la carpeta exista en el sistema de archivos.
    (Drive for Desktop la mantiene aunque no haya conexión; sincronizará después.)
    """
    try:
        drive = Path(carpeta_drive)
        # Verificar que la unidad raíz exista (ej. G:\)
        return drive.drive and Path(drive.drive + "\\").exists()
    except Exception:
        return False


def _subcarpeta_consorcio(base: str, nombre_consorcio: str, anio: int, mes: int) -> Path:
    return Path(base) / nombre_consorcio / str(anio) / MESES[mes]


def _subcarpeta_pendientes(base: str) -> Path:
    return Path(base) / "FACTURAS PENDIENTES"


def _nombre_sin_conflicto(carpeta: Path, nombre_archivo: str) -> Path:
    """Agrega sufijo _1, _2, … si el archivo ya existe en destino."""
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
    carpeta_drive: str = "",
    drive_habilitado: bool = False,
) -> tuple[str, str, str, str]:
    """
    Mueve el archivo a la carpeta local y lo copia también a Drive (si está habilitado).

    Returns:
        Tupla (ruta_final_local, ruta_final_drive, archivo_drive_id, carpeta_drive_id).
        Los IDs de Drive son "" si Drive no se usó o falló.
    """
    nombre_archivo = Path(ruta_origen).name
    es_pendiente   = (nombre_consorcio == ".")

    # ── Destino local ────────────────────────────────────────────────────────
    if es_pendiente:
        carpeta_dest_local = _subcarpeta_pendientes(carpeta_local)
    else:
        carpeta_dest_local = _subcarpeta_consorcio(carpeta_local, nombre_consorcio, anio, mes)

    carpeta_dest_local.mkdir(parents=True, exist_ok=True)
    ruta_final_local = _nombre_sin_conflicto(carpeta_dest_local, nombre_archivo)

    try:
        shutil.move(ruta_origen, str(ruta_final_local))
    except Exception as e:
        print(f"  ❌ Error moviendo a local: {e}")
        return "", "", "", ""

    # ── Destino Drive ────────────────────────────────────────────────────────
    ruta_final_drive = ""
    archivo_drive_id = ""
    carpeta_drive_id = ""

    if drive_habilitado and carpeta_drive:
        if not _drive_disponible(carpeta_drive):
            print("  ⚠ AVISO: Google Drive no está disponible en este momento.")
            print("    El archivo quedó guardado localmente.")
        else:
            try:
                if es_pendiente:
                    carpeta_dest_drive = _subcarpeta_pendientes(carpeta_drive)
                else:
                    carpeta_dest_drive = _subcarpeta_consorcio(
                        carpeta_drive, nombre_consorcio, anio, mes
                    )
                carpeta_dest_drive.mkdir(parents=True, exist_ok=True)
                ruta_final_drive = _nombre_sin_conflicto(carpeta_dest_drive, nombre_archivo)
                shutil.copy2(str(ruta_final_local), str(ruta_final_drive))
                
                # Obtener IDs de Drive
                from src.google_sheets.sheets_manager import autenticar_google, obtener_servicio_drive
                creds = autenticar_google()
                drive_service = obtener_servicio_drive(creds)
                
                # Buscar el archivo en Drive por nombre
                query = f"name='{nombre_archivo}' and trashed=false"
                results = drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id)',
                    pageSize=1
                ).execute()
                
                files = results.get('files', [])
                if files:
                    archivo_drive_id = files[0]['id']
                
                # Obtener ID de la carpeta
                carpeta_parts = str(carpeta_dest_drive).split('\\')
                query_carpeta = f"name='{carpeta_parts[-1]}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                results_carpeta = drive_service.files().list(
                    q=query_carpeta,
                    spaces='drive',
                    fields='files(id)',
                    pageSize=1
                ).execute()
                
                folders = results_carpeta.get('files', [])
                if folders:
                    carpeta_drive_id = folders[0]['id']
                    
            except Exception as e:
                print(f"  ⚠ AVISO: No se pudo copiar a Drive: {e}")
                ruta_final_drive = ""

    return str(ruta_final_local), str(ruta_final_drive), archivo_drive_id, carpeta_drive_id


def copiar_a_pendientes(
    ruta_origen: str,
    carpeta_local: str,
    carpeta_drive: str = "",
    drive_habilitado: bool = False,
) -> tuple[str, str]:
    """Atajo para mover un archivo a PENDIENTES (sin consorcio ni fecha)."""
    return mover_a_destino(
        ruta_origen, carpeta_local, ".", 0, 1,
        carpeta_drive=carpeta_drive,
        drive_habilitado=drive_habilitado,
    )