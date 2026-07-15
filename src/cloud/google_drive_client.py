"""
Cliente de Google Drive API v2 — optimizado para subir archivos directamente.

Flujo sin Drive for Desktop:
1. Procesar archivo localmente en C:\FACTURAS\
2. Subir a Drive por API
3. Obtener ID para hipervínculo
4. Escribir en Excel (local + Drive)
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io


SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_PATH = "config/google_token.json"
CREDENTIALS_PATH = "config/google_credentials.json"


def _obtener_credentials():
    """Obtiene credenciales autenticadas."""
    creds = None

    if Path(TOKEN_PATH).exists():
        creds = UserCredentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_PATH).exists():
                raise FileNotFoundError(
                    f"No encontré: {CREDENTIALS_PATH}\n"
                    "Descárgalo desde Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        Path(TOKEN_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def _construir_servicio():
    """Construye cliente de Google Drive API."""
    creds = _obtener_credentials()
    return build("drive", "v3", credentials=creds)


def obtener_id_carpeta(nombre_carpeta: str, carpeta_padre_id: str = None) -> str:
    """Busca una carpeta en Drive por nombre. Retorna su ID."""
    try:
        service = _construir_servicio()

        query = (
            f"name='{nombre_carpeta}' and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )
        if carpeta_padre_id:
            query += f" and '{carpeta_padre_id}' in parents"

        resultados = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=1,
            )
            .execute()
        )

        carpetas = resultados.get("files", [])
        return carpetas[0]["id"] if carpetas else ""

    except Exception as e:
        print(f"  ⚠ Error buscando carpeta en Drive: {e}")
        return ""


def crear_carpeta(nombre: str, carpeta_padre_id: str = None) -> str:
    """
    Crea una carpeta en Drive.
    
    Args:
        nombre: nombre de la carpeta
        carpeta_padre_id: ID de la carpeta padre (si no, crea en raíz)
    
    Returns:
        ID de la carpeta creada
    """
    try:
        service = _construir_servicio()

        metadata = {
            "name": nombre,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if carpeta_padre_id:
            metadata["parents"] = [carpeta_padre_id]

        carpeta = service.files().create(body=metadata, fields="id").execute()
        return carpeta.get("id", "")

    except Exception as e:
        print(f"  ⚠ Error creando carpeta en Drive: {e}")
        return ""


def obtener_o_crear_carpeta(nombre: str, carpeta_padre_id: str = None) -> str:
    """Obtiene ID de carpeta, o la crea si no existe."""
    id_carpeta = obtener_id_carpeta(nombre, carpeta_padre_id)
    if not id_carpeta:
        id_carpeta = crear_carpeta(nombre, carpeta_padre_id)
    return id_carpeta


def subir_archivo(
    ruta_local: str,
    nombre_drive: str,
    carpeta_padre_id: str = None,
) -> tuple:
    """
    Sube un archivo a Drive.
    
    Args:
        ruta_local: ruta del archivo en PC
        nombre_drive: nombre que tendrá en Drive
        carpeta_padre_id: ID de carpeta destino
    
    Returns:
        (id_archivo, url_drive) o ("", "") si falla
    """
    try:
        service = _construir_servicio()
        ruta = Path(ruta_local)

        if not ruta.exists():
            print(f"  ⚠ Archivo no encontrado: {ruta_local}")
            return "", ""

        # Detectar MIME type
        mime_types = {
            ".pdf": "application/pdf",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        mime_type = mime_types.get(ruta.suffix.lower(), "application/octet-stream")

        metadata = {"name": nombre_drive}
        if carpeta_padre_id:
            metadata["parents"] = [carpeta_padre_id]

        media = MediaFileUpload(str(ruta), mimetype=mime_type, resumable=True)
        archivo = (
            service.files()
            .create(body=metadata, media_body=media, fields="id")
            .execute()
        )

        id_archivo = archivo.get("id", "")
        url = f"https://drive.google.com/open?id={id_archivo}" if id_archivo else ""

        return id_archivo, url

    except Exception as e:
        print(f"  ⚠ Error subiendo archivo a Drive: {e}")
        return "", ""


def subir_o_actualizar_archivo(
    ruta_local: str,
    nombre_drive: str,
    carpeta_padre_id: str = None,
) -> tuple:
    """
    Sube un archivo a Drive. Si ya existe un archivo con ese nombre en la
    misma carpeta, actualiza su contenido en vez de crear uno duplicado.

    Args:
        ruta_local: ruta del archivo en PC
        nombre_drive: nombre que tendrá en Drive
        carpeta_padre_id: ID de carpeta destino

    Returns:
        (id_archivo, url_drive) o ("", "") si falla
    """
    try:
        service = _construir_servicio()
        ruta = Path(ruta_local)

        if not ruta.exists():
            print(f"  ⚠ Archivo no encontrado: {ruta_local}")
            return "", ""

        mime_types = {
            ".pdf": "application/pdf",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        mime_type = mime_types.get(ruta.suffix.lower(), "application/octet-stream")
        media = MediaFileUpload(str(ruta), mimetype=mime_type, resumable=True)

        id_existente = obtener_id_archivo(nombre_drive, carpeta_padre_id)

        if id_existente:
            archivo = (
                service.files()
                .update(fileId=id_existente, media_body=media, fields="id")
                .execute()
            )
            id_archivo = archivo.get("id", id_existente)
        else:
            metadata = {"name": nombre_drive}
            if carpeta_padre_id:
                metadata["parents"] = [carpeta_padre_id]
            archivo = (
                service.files()
                .create(body=metadata, media_body=media, fields="id")
                .execute()
            )
            id_archivo = archivo.get("id", "")

        url = f"https://drive.google.com/open?id={id_archivo}" if id_archivo else ""
        return id_archivo, url

    except Exception as e:
        print(f"  ⚠ Error subiendo/actualizando archivo a Drive: {e}")
        return "", ""


def subir_o_actualizar_google_sheet(
    ruta_local_xlsx: str,
    nombre_drive: str,
    carpeta_padre_id: str = None,
) -> tuple:
    """
    Sube un .xlsx a Drive convirtiéndolo a Google Sheets nativo (no queda
    como archivo .xlsx). Si ya existe una hoja de cálculo con ese nombre en
    la carpeta, actualiza su contenido en vez de crear una duplicada.

    Args:
        ruta_local_xlsx: ruta del .xlsx en disco (usado solo como fuente de datos)
        nombre_drive: nombre que tendrá la hoja de cálculo en Drive
        carpeta_padre_id: ID de carpeta destino

    Returns:
        (id_sheet, url_sheet) o ("", "") si falla
    """
    try:
        service = _construir_servicio()
        ruta = Path(ruta_local_xlsx)

        if not ruta.exists():
            print(f"  ⚠ Archivo no encontrado: {ruta_local_xlsx}")
            return "", ""

        mime_xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        mime_sheet = "application/vnd.google-apps.spreadsheet"
        media = MediaFileUpload(str(ruta), mimetype=mime_xlsx, resumable=True)

        # Buscar si ya existe una Google Sheet (no un .xlsx) con este nombre
        query = (
            f"name='{nombre_drive}' and mimeType='{mime_sheet}' and trashed=false"
        )
        if carpeta_padre_id:
            query += f" and '{carpeta_padre_id}' in parents"
        resultados = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
            .execute()
        )
        existentes = resultados.get("files", [])

        if existentes:
            id_sheet = existentes[0]["id"]
            # Subir el xlsx como nuevo contenido: Drive lo reconvierte a Sheets
            service.files().update(
                fileId=id_sheet, media_body=media, fields="id"
            ).execute()
        else:
            metadata = {"name": nombre_drive, "mimeType": mime_sheet}
            if carpeta_padre_id:
                metadata["parents"] = [carpeta_padre_id]
            archivo = (
                service.files()
                .create(body=metadata, media_body=media, fields="id")
                .execute()
            )
            id_sheet = archivo.get("id", "")

        url = f"https://docs.google.com/spreadsheets/d/{id_sheet}/edit" if id_sheet else ""
        return id_sheet, url

    except Exception as e:
        print(f"  ⚠ Error subiendo/convirtiendo Google Sheet: {e}")
        return "", ""


def crear_hoja_calculo(
    nombre: str,
    carpeta_padre_id: str = None,
) -> tuple:
    """
    Crea un Google Sheets en Drive.
    
    Returns:
        (id_sheet, url_drive)
    """
    try:
        service = _construir_servicio()

        metadata = {
            "name": nombre,
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
        if carpeta_padre_id:
            metadata["parents"] = [carpeta_padre_id]

        sheet = service.files().create(body=metadata, fields="id").execute()
        id_sheet = sheet.get("id", "")
        url = f"https://docs.google.com/spreadsheets/d/{id_sheet}/edit" if id_sheet else ""

        return id_sheet, url

    except Exception as e:
        print(f"  ⚠ Error creando Google Sheet: {e}")
        return "", ""


def obtener_id_archivo(nombre: str, carpeta_padre_id: str = None) -> str:
    """Busca un archivo en Drive por nombre."""
    try:
        service = _construir_servicio()

        query = f"name='{nombre}' and trashed=false"
        if carpeta_padre_id:
            query += f" and '{carpeta_padre_id}' in parents"

        resultados = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=1,
            )
            .execute()
        )

        archivos = resultados.get("files", [])
        return archivos[0]["id"] if archivos else ""

    except Exception as e:
        print(f"  ⚠ Error buscando archivo en Drive: {e}")
        return ""


def construir_url_drive(archivo_id: str) -> str:
    """Construye URL de acceso directo."""
    return f"https://drive.google.com/open?id={archivo_id}"


def prueba_conexion():
    """Test rápido de autenticación."""
    try:
        service = _construir_servicio()
        resultado = service.files().list(pageSize=1, fields="files(id)").execute()
        print("✓ Conexión a Google Drive exitosa")
        return True
    except Exception as e:
        print(f"✗ Error conectando a Google Drive: {e}")
        return False