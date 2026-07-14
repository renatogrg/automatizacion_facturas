"""
Gestor de Google Sheets para registros de facturas.
Crea sheets automáticamente y genera hipervínculos compartibles de Drive.
"""

import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

# Alcances necesarios
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]


def autenticar_google():
    """
    Autentica con Google usando OAuth 2.0.
    La primera vez abre un navegador para el consentimiento.
    Luego guarda el token en token.pickle para reutilizarlo.
    """
    creds = None
    token_file = Path("config/token.pickle")
    credentials_file = Path("config/credentials.json")
    
    # Si existe token guardado, cargarlo
    if token_file.exists():
        with open(token_file, 'rb') as f:
            creds = pickle.load(f)
    
    # Si no hay token o está expirado, autenticar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Guardar el token para próximas veces
        with open(token_file, 'wb') as f:
            pickle.dump(creds, f)
    
    return creds


def obtener_servicio_sheets(creds):
    """Retorna el cliente de Google Sheets API."""
    return build('sheets', 'v4', credentials=creds)


def obtener_servicio_drive(creds):
    """Retorna el cliente de Google Drive API."""
    return build('drive', 'v3', credentials=creds)


def crear_o_abrir_sheet(creds, nombre_sheet: str, carpeta_drive_id: str = None) -> str:
    """
    Crea un Google Sheet nuevo o abre uno existente.
    
    Args:
        creds: credenciales autenticadas
        nombre_sheet: nombre del sheet (ej. "Registro Facturas Consorcio Wayayo")
        carpeta_drive_id: ID de la carpeta en Drive donde guardarlo (opcional)
    
    Returns:
        spreadsheet_id del sheet
    """
    try:
        sheets_service = obtener_servicio_sheets(creds)
        drive_service = obtener_servicio_drive(creds)
        
        # Buscar si ya existe un sheet con ese nombre
        query = f"name='{nombre_sheet}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]['id']
        
        # Si no existe, crear uno nuevo
        spreadsheet = {
            'properties': {
                'title': nombre_sheet
            }
        }
        
        spreadsheet_result = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId'
        ).execute()
        
        spreadsheet_id = spreadsheet_result.get('spreadsheetId')
        
        # Si se especifica carpeta, mover el sheet a esa carpeta
        if carpeta_drive_id:
            drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=carpeta_drive_id,
                removeParents='root',
                fields='id, parents'
            ).execute()
        
        # Crear la hoja con encabezados
        _crear_encabezados(sheets_service, spreadsheet_id)
        
        return spreadsheet_id
        
    except HttpError as error:
        print(f'Error en Google Sheets: {error}')
        return None


def _crear_encabezados(sheets_service, spreadsheet_id: str):
    """Crea los encabezados en el sheet."""
    encabezados = [
        ['Fecha', 'Consorcio', 'Proveedor', 'RUC proveedor', 'Total', 'Abrir PDF', 'Abrir Carpeta']
    ]
    
    body = {
        'values': encabezados
    }
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='Facturas!A1:G1',
        valueInputOption='RAW',
        body=body
    ).execute()


def agregar_fila_con_links(
    creds,
    spreadsheet_id: str,
    fecha: str,
    consorcio: str,
    proveedor: str,
    ruc: str,
    total: str,
    archivo_drive_id: str,
    carpeta_drive_id: str
):
    """
    Agrega una fila al sheet con hipervínculos compartibles de Drive.
    
    Args:
        creds: credenciales autenticadas
        spreadsheet_id: ID del sheet
        fecha, consorcio, proveedor, ruc, total: datos de la factura
        archivo_drive_id: ID del archivo en Drive
        carpeta_drive_id: ID de la carpeta en Drive
    """
    try:
        sheets_service = obtener_servicio_sheets(creds)
        drive_service = obtener_servicio_drive(creds)
        
        # Obtener links compartibles
        link_archivo = _obtener_link_compartible(drive_service, archivo_drive_id)
        link_carpeta = _obtener_link_compartible(drive_service, carpeta_drive_id)
        
        # Preparar fila con fórmulas HYPERLINK
        fila = [
            fecha,
            consorcio,
            proveedor,
            ruc,
            total,
            f'=HYPERLINK("{link_archivo}", "Abrir PDF")' if link_archivo else "—",
            f'=HYPERLINK("{link_carpeta}", "Abrir Carpeta")' if link_carpeta else "—"
        ]
        
        body = {'values': [fila]}
        
        sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Facturas!A:G',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
    except HttpError as error:
        print(f'Error agregando fila a Sheets: {error}')


def _obtener_link_compartible(drive_service, file_id: str) -> str:
    """Genera un link compartible de Drive para un archivo."""
    try:
        # Compartir con acceso público o retornar link
        drive_service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'},
            fields='id'
        ).execute()
        
        return f"https://drive.google.com/open?id={file_id}"
    except HttpError:
        # Si ya está compartido, solo retornar el link
        return f"https://drive.google.com/open?id={file_id}"