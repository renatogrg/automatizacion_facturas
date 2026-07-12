"""
Orquestador principal: toma un archivo, extrae, clasifica, organiza y registra.
"""

import os
from pathlib import Path

from src.extractor.pdf_text import extraer_texto_nativo
from src.extractor.ocr import extraer_texto_ocr
from src.classifier.consorcio_matcher import identificar_consorcio, buscar_ruc, buscar_fecha_emision
from src.organizer.file_organizer import mover_a_destino
from src.registry.excel_registry import registrar_factura, registrar_pendiente


def procesar_factura_completo(
    ruta_archivo: str,
    consorcios: list,
    carpeta_facturas: str,
    carpeta_pendientes: str
) -> bool:
    """
    Pipeline completo: extrae, clasifica, organiza y registra una factura.
    
    Returns:
        True si se procesó exitosamente, False si fue a pendientes
    """
    nombre_archivo = os.path.basename(ruta_archivo)
    print(f"\n[Procesando] {nombre_archivo}")
    
    # Paso 1: Extracción de texto
    print("  [1] Extrayendo texto...")
    texto = extraer_texto_nativo(ruta_archivo)
    if not texto or len(texto) < 50:
        texto = extraer_texto_ocr(ruta_archivo)
        if not texto:
            print("  ❌ No se pudo extraer texto")
            motivo = "No se pudo extraer texto"
            registrar_pendiente(
                Path(carpeta_pendientes) / "Registro_Pendientes.xlsx",
                nombre_archivo,
                motivo
            )
            mover_a_destino(ruta_archivo, carpeta_pendientes, ".", 0, 1)
            return False
    
    # Paso 2: Identificar consorcio
    print("  [2] Identificando consorcio...")
    consorcio = identificar_consorcio(texto, consorcios)
    if not consorcio:
        print("  ❌ Consorcio no identificado")
        motivo = "RUC/nombre de consorcio no encontrado"
        registrar_pendiente(
            Path(carpeta_pendientes) / "Registro_Pendientes.xlsx",
            nombre_archivo,
            motivo
        )
        mover_a_destino(ruta_archivo, carpeta_pendientes, ".", 0, 1)
        return False
    
    # Paso 3: Buscar fecha
    print("  [3] Buscando fecha de emisión...")
    fecha = buscar_fecha_emision(texto)
    if not fecha:
        print("  ⚠ Fecha no encontrada, usando mes actual")
        from datetime import datetime
        anio = datetime.now().year
        mes = datetime.now().month
    else:
        anio, mes = fecha
    
    # Paso 4: Organizar (mover a carpeta)
    print(f"  [4] Organizando en {consorcio['nombre']}/{anio}/{mes:02d}...")
    ruta_final = mover_a_destino(
        ruta_archivo,
        carpeta_facturas,
        consorcio['nombre'],
        anio,
        mes
    )
    if not ruta_final:
        print("  ❌ Error al organizar archivo")
        return False
    
    # Paso 5: Registrar en Excel
    print("  [5] Registrando en Excel...")
    ruta_excel = Path(carpeta_facturas) / consorcio['nombre'] / "Registro Facturas.xlsx"
    registrar_factura(
        str(ruta_excel),
        {
            "Fecha": f"{anio}-{mes:02d}-01",
            "Consorcio": consorcio['nombre'],
            "Proveedor": "—",  # Por ahora, podría extraerse del texto después
            "RUC proveedor": buscar_ruc(texto) or "—",
            "Total": "—",  # Podría extraerse del texto después
            "Archivo": os.path.basename(ruta_final),
        }
    )
    
    print(f"  ✓ Factura procesada exitosamente")
    return True