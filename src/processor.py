"""
Orquestador principal del pipeline de procesamiento de facturas.

Flujo (costo mínimo):
  0. Validar extensión            → ignorar si no es PDF/JPG/JPEG/PNG
  1. Extraer texto nativo         → PyMuPDF (gratis)
  2. Si no hay texto → OCR        → Tesseract (gratis)
  3. Identificar consorcio        → RUC exacto + fuzzy (gratis)
  4. Buscar fecha                 → regex (gratis)
  5. Si falta algo → Claude       → Haiku 4.5 (pago, ~$0.001–$0.003)
  6. Si Claude tampoco resuelve   → PENDIENTES con motivo
  7. Organizar en carpetas        → local + Drive (si habilitado)
  8. Registrar en Excel           → local + Drive
"""
from src.google_sheets.sheets_manager import obtener_servicio_drive
from datetime import datetime
from src.google_sheets.sheets_manager import obtener_servicio_sheets
import os
from pathlib import Path

from src.extractor.pdf_text import extraer_texto_nativo, es_extension_valida
from src.extractor.ocr import extraer_texto_ocr
from src.classifier.consorcio_matcher import (
    identificar_consorcio,
    buscar_ruc,
    buscar_fecha_emision,
)
from src.organizer.file_organizer import mover_a_destino, copiar_a_pendientes
from src.registry.excel_registry import registrar_factura, registrar_pendiente
from src.utils.config_loader import cargar_settings


def _settings():
    try:
        return cargar_settings()
    except Exception:
        return {}


def _enviar_a_pendientes(
    ruta_archivo: str,
    motivo: str,
    cfg: dict,
):
    nombre = Path(ruta_archivo).name
    local  = cfg.get("carpeta_facturas_local", "C:\\FACTURAS")
    drive  = cfg.get("carpeta_facturas_drive", "")
    drive_on = cfg.get("drive_habilitado", False)

    ruta_l, ruta_d, _, _ = copiar_a_pendientes(
        ruta_archivo, local, carpeta_drive=drive, drive_habilitado=drive_on
    )

    # Excel local de pendientes - RUTA CORREGIDA
    excel_local = Path(local) / "FACTURAS PENDIENTES" / "Registro_Pendientes.xlsx"
    registrar_pendiente(str(excel_local), nombre, motivo)

    # Excel Drive de pendientes
    if drive_on and drive and ruta_d:
        excel_drive = Path(drive) / "FACTURAS PENDIENTES" / "Registro_Pendientes.xlsx"
        registrar_pendiente(str(excel_drive), nombre, motivo)
    
   

def procesar_factura_completo(
    ruta_archivo: str,
    consorcios: list,
    carpeta_facturas: str,       # mantenido por compatibilidad con test_fase4
    carpeta_pendientes: str,     # mantenido por compatibilidad con test_fase4
) -> bool:
    nombre_archivo = Path(ruta_archivo).name
    print(f"\n[Procesando] {nombre_archivo}")

    cfg = _settings()
    local  = cfg.get("carpeta_facturas_local", carpeta_facturas)
    drive  = cfg.get("carpeta_facturas_drive", "")
    drive_on = cfg.get("drive_habilitado", False)

    # ── 0. Validar extensión ─────────────────────────────────────────────────
    if not es_extension_valida(ruta_archivo):
        print("  [!] Extensión no soportada — ignorando.")
        return False

    # ── 1–2. Extraer texto ───────────────────────────────────────────────────
    print("  [1] Extrayendo texto...")
    texto    = extraer_texto_nativo(ruta_archivo)
    es_img   = not texto or len(texto) < 50
    if es_img:
        texto = extraer_texto_ocr(ruta_archivo)
    if not texto:
        print("  ❌ No se pudo extraer texto")
        _enviar_a_pendientes(ruta_archivo, "No se pudo extraer texto", cfg)
        return False

    # ── 3. Identificar consorcio (gratis) ────────────────────────────────────
    print("  [2] Identificando consorcio...")
    consorcio = identificar_consorcio(texto, consorcios)

    # ── 4. Buscar fecha (gratis) ─────────────────────────────────────────────
    print("  [3] Buscando fecha de emisión...")
    fecha = buscar_fecha_emision(texto)
    anio, mes = fecha if fecha else (None, None)

    # ── 5. Fallback a Claude ─────────────────────────────────────────────────
    if consorcio is None or fecha is None:
        print("  [4] Consultando Claude Haiku 4.5 (datos incompletos)...")
        nombres_c = [c["nombre"] for c in consorcios]
        try:
            from src.extractor.claude_client import analizar_con_texto, analizar_con_imagen
            res = analizar_con_imagen(ruta_archivo, nombres_c) if es_img \
                  else analizar_con_texto(texto, nombres_c)

            if res:
                if consorcio is None and res.get("consorcio"):
                    nc = res["consorcio"].upper()
                    for c in consorcios:
                        if c["nombre"].upper() in nc or nc in c["nombre"].upper():
                            consorcio = c
                            break
                if fecha is None and res.get("anio") and res.get("mes"):
                    anio, mes = res["anio"], res["mes"]
        except Exception as e:
            print(f"  ⚠ Claude no disponible: {e}")

    # ── 6. Sin datos → PENDIENTES ────────────────────────────────────────────
    if consorcio is None:
        print("  ❌ Consorcio no identificado → PENDIENTES")
        _enviar_a_pendientes(ruta_archivo, "Consorcio no identificado", cfg)
        return False
    if anio is None or mes is None:
        print("  ❌ Fecha no encontrada → PENDIENTES")
        _enviar_a_pendientes(ruta_archivo, "Fecha de emisión no encontrada", cfg)
        return False

    # ── 7. Organizar en carpetas ─────────────────────────────────────────────
    print(f"  [5] Organizando en {consorcio['nombre']}/{anio}/{mes:02d}...")
    ruta_l, ruta_d, archivo_id, carpeta_id = mover_a_destino(
        ruta_archivo, local, consorcio["nombre"], anio, mes,
        carpeta_drive=drive, drive_habilitado=drive_on,
    )
    if not ruta_l:
        print("  ❌ Error al mover archivo")
        return False

    ruta_carpeta_local = str(Path(ruta_l).parent)
    ruta_carpeta_drive = str(Path(ruta_d).parent) if ruta_d else ""

    # ── 8. Registrar en Excel ────────────────────────────────────────────────
    print("  [6] Registrando en Excel...")
    datos_fila = {
        "Fecha":         f"{anio}-{mes:02d}-01",
        "Consorcio":     consorcio["nombre"],
        "Proveedor":     consorcio.get("proveedor_texto", "—"),
        "RUC proveedor": buscar_ruc(texto) or "—",
        "Total":         "—",
    }

    # Excel local (con hipervínculos)
    excel_local = Path(local) / consorcio["nombre"] / f"Registro Facturas {consorcio['nombre']}.xlsx"
    registrar_factura(
        str(excel_local), datos_fila,
        ruta_pdf_final=ruta_l,
        ruta_carpeta=ruta_carpeta_local,
        es_drive=False,
    )
    # Excel Drive
    if drive_on and drive and ruta_d:
       excel_drive = Path(drive) / consorcio["nombre"] / f"Registro Facturas - {consorcio['nombre']}.xlsx"
       registrar_factura(
           str(excel_drive), datos_fila,
           ruta_pdf_final=ruta_d,
           ruta_carpeta=ruta_carpeta_drive,
           es_drive=True,
       )
    

    # Excel Drive (sin hipervínculos file:///)
    # Google Sheets en Drive (con hipervínculos compartibles)
    if drive_on and drive and ruta_d and archivo_id and carpeta_id:
        try:
            from src.google_sheets.sheets_manager import (
                autenticar_google,
                crear_o_abrir_sheet,
                agregar_fila_con_links,
                obtener_servicio_drive
            )
            
            creds = autenticar_google()
            nombre_sheet = f"Registro Facturas {consorcio['nombre']}"
            
            # Obtener ID de la carpeta del consorcio en Drive
            drive_service = obtener_servicio_drive(creds)
            carpeta_consorcio_nombre = consorcio['nombre']
            query = f"name='{carpeta_consorcio_nombre}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id)',
                pageSize=1
            ).execute()
            
            carpeta_consorcio_id = ""
            folders = results.get('files', [])
            if folders:
                carpeta_consorcio_id = folders[0]['id']
            
            # Crear o abrir el Sheet en la carpeta del consorcio
            spreadsheet_id = crear_o_abrir_sheet(
                creds, 
                nombre_sheet,
                carpeta_drive_id=carpeta_consorcio_id
            )
            
            if spreadsheet_id:
                agregar_fila_con_links(
                    creds,
                    spreadsheet_id,
                    datos_fila["Fecha"],
                    datos_fila["Consorcio"],
                    datos_fila["Proveedor"],
                    datos_fila["RUC proveedor"],
                    datos_fila["Total"],
                    archivo_id,
                    carpeta_id
                )
                print("  ✓ Registrado en Google Sheets")
        except Exception as e:
            print(f"  ⚠ No se pudo registrar en Sheets: {e}")
            import traceback
            traceback.print_exc()

    print("  ✓ Factura procesada exitosamente")
    return True