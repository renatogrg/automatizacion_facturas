"""
Processor v3 — Local SIEMPRE funciona. Drive es opcional e independiente.

Flujo:
  1. Organizar LOCALMENTE en C:\FACTURAS\ (siempre)
  2. INTENTAR subir a Drive por API (si falla, no importa)
  3. Registrar en Excel (local siempre, Drive solo si subida exitosa)
"""

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
from src.registry.excel_registry_drive import registrar_factura, registrar_pendiente
from src.utils.config_loader import cargar_settings


def _settings():
    try:
        return cargar_settings()
    except Exception:
        return {}


def _subir_a_drive_background(
    ruta_local: str,
    nombre_consorcio: str,
    anio: int,
    mes: int,
) -> tuple:
    """
    Intenta subir a Drive de forma INDEPENDIENTE.
    Si falla, no afecta nada — local ya está guardado.
    
    Returns:
        (id_pdf_drive, url_pdf_drive, id_carpeta_drive, url_carpeta_drive)
        Retorna ("", "", "", "") si falla (pero sin crashear)
    """
    try:
        from src.cloud.google_drive_client import (
            obtener_o_crear_carpeta,
            subir_archivo,
        )

        # Crear estructura en Drive: FACTURAS / Consorcio / Año / Mes
        id_facturas = obtener_o_crear_carpeta("FACTURAS")
        if not id_facturas:
            return "", "", "", ""

        id_consorcio = obtener_o_crear_carpeta(nombre_consorcio, id_facturas)
        if not id_consorcio:
            return "", "", "", ""

        meses = {
            1:  "01-Enero",    2:  "02-Febrero",  3:  "03-Marzo",
            4:  "04-Abril",    5:  "05-Mayo",     6:  "06-Junio",
            7:  "07-Julio",    8:  "08-Agosto",   9:  "09-Setiembre",
            10: "10-Octubre",  11: "11-Noviembre", 12: "12-Diciembre",
        }
        mes_nombre = meses[mes]

        id_año = obtener_o_crear_carpeta(str(anio), id_consorcio)
        if not id_año:
            return "", "", "", ""

        id_mes = obtener_o_crear_carpeta(mes_nombre, id_año)
        if not id_mes:
            return "", "", "", ""

        # Subir archivo
        nombre_archivo = Path(ruta_local).name
        id_archivo, url_archivo = subir_archivo(ruta_local, nombre_archivo, id_mes)

        url_carpeta = f"https://drive.google.com/open?id={id_mes}" if id_mes else ""

        return id_archivo, url_archivo, id_mes, url_carpeta

    except Exception as e:
        # Fallo de Drive, pero local ya está seguro
        print(f"  ⚠ Drive: {e} (local está guardado)")
        return "", "", "", ""


def _enviar_a_pendientes(
    ruta_archivo: str,
    motivo: str,
    cfg: dict,
    es_duplicado: bool = False,
):
    """Mueve archivo a FACTURAS PENDIENTES localmente."""
    local = cfg.get("carpeta_facturas_local", "C:\\FACTURAS")

    ruta_l = copiar_a_pendientes(
        ruta_archivo, local, es_duplicado=es_duplicado
    )

    if not ruta_l:
        return

    nombre = Path(ruta_archivo).name

    # Excel local (SIEMPRE se registra)
    excel_local = Path(local) / "FACTURAS PENDIENTES" / "Registro_Pendientes.xlsx"
    registrar_pendiente(str(excel_local), nombre, motivo)

    # Intentar subir a Drive (independiente)
    try:
        from src.cloud.google_drive_client import (
            obtener_o_crear_carpeta,
            subir_archivo,
            subir_o_actualizar_google_sheet,
        )
        
        id_facturas = obtener_o_crear_carpeta("FACTURAS")
        id_pendientes = obtener_o_crear_carpeta("FACTURAS PENDIENTES", id_facturas)
        
        if id_pendientes:
            subir_archivo(ruta_l, nombre, id_pendientes)

            # Excel de pendientes en Drive, como Google Sheets nativo (actualizar, no duplicar)
            if excel_local.exists():
                subir_o_actualizar_google_sheet(
                    str(excel_local), excel_local.stem, id_pendientes
                )
    except Exception as e:
        print(f"  ⚠ Drive pendiente: {e}")


def procesar_factura_completo(
    ruta_archivo: str,
    consorcios: list,
    carpeta_facturas: str,
    carpeta_pendientes: str,
) -> bool:
    """Pipeline: local SIEMPRE, Drive SI PUEDE."""
    nombre_archivo = Path(ruta_archivo).name
    print(f"\n[Procesando] {nombre_archivo}")

    cfg = _settings()
    local = cfg.get("carpeta_facturas_local", carpeta_facturas)
    drive_habilitado = cfg.get("drive_habilitado", False)

    # ── 0. Validar extensión ─────────────────────────────────────────────────
    if not es_extension_valida(ruta_archivo):
        print("  [!] Extensión no soportada — ignorando.")
        return False

    # ── 1–2. Extraer texto ───────────────────────────────────────────────────
    print("  [1] Extrayendo texto...")
    texto = extraer_texto_nativo(ruta_archivo)
    es_img = not texto or len(texto) < 50
    if es_img:
        texto = extraer_texto_ocr(ruta_archivo)
    if not texto:
        print("  ❌ No se pudo extraer texto")
        _enviar_a_pendientes(ruta_archivo, "No se pudo extraer texto", cfg)
        return False

    # ── 3. Identificar consorcio ─────────────────────────────────────────────
    print("  [2] Identificando consorcio...")
    consorcio = identificar_consorcio(texto, consorcios)

    # ── 4. Buscar fecha ──────────────────────────────────────────────────────
    print("  [3] Buscando fecha de emisión...")
    fecha = buscar_fecha_emision(texto)
    anio, mes = fecha if fecha else (None, None)

    # ── 5. Fallback a Groq ────────────────────────────────────────────────────
    uso_groq = False
    if consorcio is None or fecha is None:
        print("  🤖 [4] Consultando Groq (datos incompletos)...")
        uso_groq = True
        nombres_c = [c["nombre"] for c in consorcios]
        try:
            from src.extractor.groq_client import analizar_con_texto, analizar_con_imagen
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
            print(f"  ⚠ Groq no disponible: {e}")

    # ── 6. Sin datos → FACTURAS PENDIENTES ────────────────────────────────────
    if consorcio is None:
        if uso_groq:
            print("  ❌🤖 Consorcio no identificado (ni con Groq) → FACTURAS PENDIENTES")
        else:
            print("  ❌ Consorcio no identificado → FACTURAS PENDIENTES")
        _enviar_a_pendientes(ruta_archivo, "Consorcio no identificado", cfg)
        return False
    if anio is None or mes is None:
        if uso_groq:
            print("  ❌🤖 Fecha no encontrada (ni con Groq) → FACTURAS PENDIENTES")
        else:
            print("  ❌ Fecha no encontrada → FACTURAS PENDIENTES")
        _enviar_a_pendientes(ruta_archivo, "Fecha de emisión no encontrada", cfg)
        return False

    # ── 7. ORGANIZAR LOCALMENTE (SIEMPRE) ────────────────────────────────────
    print(f"  [5] Organizando localmente en {consorcio['nombre']}/{anio}/{mes:02d}...")
    ruta_l = mover_a_destino(
        ruta_archivo, local, consorcio["nombre"], anio, mes
    )
    if not ruta_l:
        print("  ❌ Error al mover archivo")
        return False

    ruta_carpeta_local = str(Path(ruta_l).parent)

    # ── 8. SUBIR A DRIVE (INDEPENDIENTE, SI FALLA NO IMPORTA) ─────────────────
    id_pdf_drive = ""
    url_pdf_drive = ""
    id_carpeta_drive = ""
    url_carpeta_drive = ""

    if drive_habilitado:
        print("  [6] Subiendo a Google Drive...")
        id_pdf_drive, url_pdf_drive, id_carpeta_drive, url_carpeta_drive = (
            _subir_a_drive_background(ruta_l, consorcio["nombre"], anio, mes)
        )

    # ── 9. REGISTRAR EN EXCEL ────────────────────────────────────────────────
    print("  [7] Registrando en Excel...")
    datos_fila = {
        "Fecha":         f"{anio}-{mes:02d}-01",
        "Consorcio":     consorcio["nombre"],
        "Proveedor":     "—",
        "RUC proveedor": buscar_ruc(texto) or "—",
        "Total":         "—",
    }

    # Excel local (SIEMPRE se crea)
    excel_local = (
        Path(local) / consorcio["nombre"]
        / f"Registro Facturas - {consorcio['nombre']}.xlsx"
    )
    registrar_factura(
        str(excel_local), datos_fila,
        ruta_pdf_final=ruta_l,
        ruta_carpeta=ruta_carpeta_local,
        es_drive=False,
    )

    # Sheets en Drive (SOLO si subida a Drive fue exitosa) — se genera una
    # copia temporal con hipervínculos reales de Drive (no file:///) y esa
    # es la que se sube, convertida a Google Sheets nativo.
    if drive_habilitado and url_pdf_drive:
        try:
            from src.cloud.google_drive_client import (
                obtener_o_crear_carpeta,
                subir_o_actualizar_google_sheet,
            )

            id_facturas = obtener_o_crear_carpeta("FACTURAS")
            id_consorcio_drive = obtener_o_crear_carpeta(
                consorcio["nombre"], id_facturas
            )

            if id_consorcio_drive:
                # Excel temporal con enlaces de Drive (se reconstruye completo
                # a partir de las mismas filas del registro local, pero
                # apuntando a URLs de Drive en vez de rutas locales).
                excel_drive_tmp = (
                    Path(local) / consorcio["nombre"] / ".drive_sync"
                    / f"Registro Facturas - {consorcio['nombre']}.xlsx"
                )
                registrar_factura(
                    str(excel_drive_tmp), datos_fila,
                    url_pdf_drive=url_pdf_drive,
                    url_carpeta_drive=url_carpeta_drive,
                    es_drive=True,
                )

                nombre_sheet = f"Registro Facturas - {consorcio['nombre']}"
                subir_o_actualizar_google_sheet(
                    str(excel_drive_tmp), nombre_sheet, id_consorcio_drive
                )

        except Exception as e:
            print(f"  ⚠ Excel en Drive: {e}")

    if uso_groq:
        print("  ✓🤖 Factura procesada exitosamente (local OK, con ayuda de Groq)")
    else:
        print("  ✓ Factura procesada exitosamente (local OK)")
    return True