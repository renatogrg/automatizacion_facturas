"""
Orquestador principal: toma un archivo, extrae, clasifica, organiza y registra.

Flujo de costo mínimo:
  1. Validar extensión (gratis) — ignorar si no es PDF/JPG/JPEG/PNG
  2. Extraer texto nativo con PyMuPDF (gratis)
  3. Si no hay texto → OCR local con Tesseract (gratis)
  4. Identificar consorcio por RUC exacto o nombre fuzzy (gratis)
  5. Buscar fecha con regex (gratis)
  6. Si falta consorcio O fecha → Claude Haiku 4.5 (pago, ~$0.001-0.003)
  7. Si Claude tampoco resuelve → PENDIENTES con motivo claro
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
from src.organizer.file_organizer import mover_a_destino
from src.registry.excel_registry import registrar_factura, registrar_pendiente


def _enviar_a_pendientes(ruta_archivo: str, carpeta_facturas: str, motivo: str):
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
    nombre_archivo = os.path.basename(ruta_archivo)
    print(f"\n[Procesando] {nombre_archivo}")

    # ── Paso 0: Validar extensión ────────────────────────────────────────────
    if not es_extension_valida(ruta_archivo):
        print("  [!] Extensión no soportada — ignorando.")
        return False

    # ── Paso 1: Extracción de texto ──────────────────────────────────────────
    print("  [1] Extrayendo texto...")
    texto = extraer_texto_nativo(ruta_archivo)
    es_imagen = not texto or len(texto) < 50

    if es_imagen:
        texto = extraer_texto_ocr(ruta_archivo)
        if not texto:
            print("  ❌ No se pudo extraer texto")
            _enviar_a_pendientes(ruta_archivo, carpeta_facturas, "No se pudo extraer texto")
            return False

    # ── Paso 2: Identificar consorcio (gratis) ───────────────────────────────
    print("  [2] Identificando consorcio...")
    consorcio = identificar_consorcio(texto, consorcios)

    # ── Paso 3: Buscar fecha (gratis) ────────────────────────────────────────
    print("  [3] Buscando fecha de emisión...")
    fecha = buscar_fecha_emision(texto)
    anio, mes = fecha if fecha else (None, None)

    # ── Paso 4: Fallback a Claude si falta consorcio O fecha ─────────────────
    if consorcio is None or fecha is None:
        print("  [4] Consultando Claude Haiku 4.5 (datos incompletos)...")
        nombres_consorcios = [c["nombre"] for c in consorcios]

        try:
            from src.extractor.claude_client import analizar_con_texto, analizar_con_imagen

            if es_imagen:
                resultado = analizar_con_imagen(ruta_archivo, nombres_consorcios)
            else:
                resultado = analizar_con_texto(texto, nombres_consorcios)

            if resultado:
                # Completar consorcio si falta
                if consorcio is None and resultado.get("consorcio"):
                    nombre_c = resultado["consorcio"].upper()
                    for c in consorcios:
                        if c["nombre"].upper() in nombre_c or nombre_c in c["nombre"].upper():
                            consorcio = c
                            break

                # Completar fecha si falta
                if fecha is None and resultado.get("anio") and resultado.get("mes"):
                    anio = resultado["anio"]
                    mes = resultado["mes"]

        except Exception as e:
            print(f"  ⚠ Claude no disponible: {e}")

    # ── Paso 5: Si aún falta algo → PENDIENTES ───────────────────────────────
    if consorcio is None:
        print("  ❌ Consorcio no identificado → PENDIENTES")
        _enviar_a_pendientes(ruta_archivo, carpeta_facturas, "Consorcio no identificado")
        return False

    if anio is None or mes is None:
        print("  ❌ Fecha no encontrada → PENDIENTES")
        _enviar_a_pendientes(ruta_archivo, carpeta_facturas, "Fecha de emisión no encontrada")
        return False

    # ── Paso 6: Organizar ────────────────────────────────────────────────────
    print(f"  [5] Organizando en {consorcio['nombre']}/{anio}/{mes:02d}...")
    ruta_final = mover_a_destino(
        ruta_archivo, carpeta_facturas, consorcio["nombre"], anio, mes
    )
    if not ruta_final:
        print("  ❌ Error al mover archivo")
        return False

    # ── Paso 7: Registrar en Excel ───────────────────────────────────────────
    print("  [6] Registrando en Excel...")
    ruta_excel = (
        Path(carpeta_facturas) / consorcio["nombre"]
        / f"Registro Facturas {consorcio['nombre']}.xlsx"
    )
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
        nombre_consorcio=consorcio["nombre"],
    )

    print("  ✓ Factura procesada exitosamente")
    return True