"""
Orquestador principal: toma un archivo, extrae, clasifica, organiza y registra.

Flujo de costo mínimo:
  1. Validar extensión (gratis) — ignorar silenciosamente si no es soportada.
  2. Extraer texto nativo con PyMuPDF (gratis).
  3. Si no hay texto suficiente → OCR local con Tesseract (gratis).
  4. Identificar consorcio por RUC exacto o nombre fuzzy (gratis).
  5. Buscar fecha con regex (gratis).
  6. Si faltan datos obligatorios (consorcio o fecha) → Claude Haiku 4.5 (pago).
  7. Si Claude tampoco resuelve → PENDIENTES con motivo.
"""

import os
from pathlib import Path
from datetime import datetime

from src.extractor.pdf_text import extraer_texto_nativo, es_extension_valida
from src.extractor.ocr import extraer_texto_ocr
from src.classifier.consorcio_matcher import (
    identificar_consorcio,
    buscar_ruc,
    buscar_fecha_emision,
)
from src.organizer.file_organizer import mover_a_destino
from src.registry.excel_registry import registrar_factura, registrar_pendiente


def _enviar_a_pendientes(ruta_archivo: str, carpeta_facturas: str, carpeta_pendientes: str, motivo: str):
    nombre = os.path.basename(ruta_archivo)
    registrar_pendiente(
        Path(carpeta_facturas) / "Facturas Pendientes" / "Registro_Pendientes.xlsx",
        nombre,
        motivo,
    )
    mover_a_destino(ruta_archivo, carpeta_facturas, ".", 0, 1)


def procesar_factura_completo(
    ruta_archivo: str,
    consorcios: list,
    carpeta_facturas: str,
    carpeta_pendientes: str,
) -> bool:
    """
    Pipeline completo: valida, extrae, clasifica, organiza y registra una factura.

    Returns:
        True si se procesó exitosamente, False si fue a pendientes o se ignoró.
    """
    nombre_archivo = os.path.basename(ruta_archivo)
    print(f"\n[Procesando] {nombre_archivo}")

    # ── Paso 0: Validar extensión ────────────────────────────────────────────
    if not es_extension_valida(ruta_archivo):
        print(f"  [!] Extensión no soportada — ignorando.")
        return False  # No va a PENDIENTES, se descarta silenciosamente

    # ── Paso 1: Extracción de texto ──────────────────────────────────────────
    print("  [1] Extrayendo texto...")
    texto = extraer_texto_nativo(ruta_archivo)
    es_imagen = not texto or len(texto) < 50

    if es_imagen:
        texto = extraer_texto_ocr(ruta_archivo)
        if not texto:
            print("  ❌ No se pudo extraer texto")
            _enviar_a_pendientes(ruta_archivo, carpeta_facturas, carpeta_pendientes, "No se pudo extraer texto")
            return False

    # ── Paso 2: Identificar consorcio (gratis) ───────────────────────────────
    print("  [2] Identificando consorcio...")
    consorcio = identificar_consorcio(texto, consorcios)

    # ── Paso 3: Buscar fecha (gratis) ────────────────────────────────────────
    print("  [3] Buscando fecha de emisión...")
    fecha = buscar_fecha_emision(texto)
    if fecha:
        anio, mes = fecha

    # ── Paso 4: Fallback a Claude si falta consorcio O fecha ─────────────────
    necesita_claude = (consorcio is None) or (fecha is None)
    if necesita_claude:
        print("  [4] Consultando Claude Haiku 4.5 (datos incompletos)...")
        resultado_claude = _llamar_claude(
            ruta_archivo, texto, consorcios, es_imagen,
            necesita_consorcio=(consorcio is None),
            necesita_fecha=(fecha is None),
        )
        if resultado_claude:
            if consorcio is None and resultado_claude.get("consorcio"):
                # Buscar el dict completo del consorcio por nombre devuelto por Claude
                nombre_claude = resultado_claude["consorcio"].upper()
                for c in consorcios:
                    if c["nombre"].upper() in nombre_claude or nombre_claude in c["nombre"].upper():
                        consorcio = c
                        break
            if fecha is None and resultado_claude.get("anio") and resultado_claude.get("mes"):
                anio = resultado_claude["anio"]
                mes = resultado_claude["mes"]

    # ── Paso 5: Si aún falta algo → PENDIENTES ───────────────────────────────
    if consorcio is None:
        print("  ❌ Consorcio no identificado (ni regex ni Claude)")
        _enviar_a_pendientes(ruta_archivo, carpeta_facturas, carpeta_pendientes, "No se pudo extraer texto")
        return False

    if fecha is None:
        print("  ❌ Fecha no encontrada (ni regex ni Claude) → PENDIENTES")
        _enviar_a_pendientes(ruta_archivo, carpeta_facturas, carpeta_pendientes, "No se pudo extraer texto")
        return False

    # ── Paso 6: Organizar (mover a carpeta) ──────────────────────────────────
    print(f"  [5] Organizando en {consorcio['nombre']}/{anio}/{mes:02d}...")
    ruta_final = mover_a_destino(
        ruta_archivo, carpeta_facturas, consorcio["nombre"], anio, mes
    )
    if not ruta_final:
        print("  ❌ Error al mover archivo")
        return False

    # ── Paso 7: Registrar en Excel ───────────────────────────────────────────
    print("  [6] Registrando en Excel...")
    nombre_excel = f"Registro Facturas {consorcio['nombre']}.xlsx"
    ruta_excel = Path(carpeta_facturas) / consorcio['nombre'] / nombre_excel
    fecha_str = f"{mes:02d}/{anio}"  # MM/YYYY → se mostrará en el Excel
    registrar_factura(
        str(ruta_excel),
        {
            "Fecha": f"{anio}-{mes:02d}-01",
            "Consorcio": consorcio["nombre"],
            "Proveedor": "—",
            "RUC proveedor": buscar_ruc(texto) or "—",
            "Total": "—",
            "Archivo": os.path.basename(ruta_final),
        },
        nombre_consorcio=consorcio['nombre']
    )

    print("  ✓ Factura procesada exitosamente")
    return True


def _llamar_claude(
    ruta_archivo: str,
    texto: str,
    consorcios: list,
    es_imagen: bool,
    necesita_consorcio: bool,
    necesita_fecha: bool,
) -> dict | None:
    """
    Llama a Claude Haiku 4.5 solo para los campos que faltan.
    Devuelve un dict con los campos encontrados, o None si falla.
    """
    try:
        from src.extractor.claude_client import analizar_con_texto, analizar_con_imagen
        nombres_consorcios = [c["nombre"] for c in consorcios]

        if es_imagen:
            resultado = analizar_con_imagen(ruta_archivo, nombres_consorcios)
        else:
            resultado = analizar_con_texto(texto, nombres_consorcios)

        return resultado
    except NotImplementedError:
        print("  ⚠ claude_client aún no implementado — yendo a PENDIENTES")
        return None
    except Exception as e:
        print(f"  ⚠ Error llamando a Claude: {e}")
        return None