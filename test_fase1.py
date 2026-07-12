"""
Script de prueba (Fase 1 + 2) - Extrae texto de facturas de prueba
e identifica el consorcio sin usar la API.

Uso:
    python test_fase1.py
"""

import os
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from src.extractor.pdf_text import extraer_texto_nativo
from src.extractor.ocr import extraer_texto_ocr
from src.classifier.consorcio_matcher import identificar_consorcio, buscar_ruc, buscar_fecha_emision
from src.utils.config_loader import cargar_consorcios


def procesar_factura(ruta_archivo: str, consorcios: list):
    """
    Procesa una factura: extrae texto, identifica consorcio y fecha.
    
    Args:
        ruta_archivo: ruta al archivo (PDF o imagen)
        consorcios: lista de dicts con consorcios
    """
    print(f"\n{'='*70}")
    print(f"Procesando: {os.path.basename(ruta_archivo)}")
    print(f"{'='*70}")
    
    # Paso 1: Intentar extracción nativa
    print("\n[1] Intentando extracción nativa (PDF con texto embebido)...")
    texto = extraer_texto_nativo(ruta_archivo)
    
    if not texto or len(texto) < 50:
        print("    ❌ No hay texto nativo (probablemente es una imagen/escaneo)")
        print("\n[2] Intentando OCR local...")
        texto = extraer_texto_ocr(ruta_archivo)
        if texto:
            print(f"    ✓ OCR exitoso. Extrajo {len(texto)} caracteres")
        else:
            print("    ❌ OCR falló o sin texto legible")
            return
    else:
        print(f"    ✓ Texto nativo exitoso. Extrajo {len(texto)} caracteres")
    
    # Mostrar primeros 200 caracteres del texto
    print(f"\n[Primer párrafo]:\n{texto[:200]}...\n")
    
    # Paso 2: Búsqueda de RUC
    print("[3] Buscando RUC...")
    ruc = buscar_ruc(texto)
    if ruc:
        print(f"    ✓ RUC encontrado: {ruc}")
    else:
        print("    ⚠ RUC no encontrado (buscará por nombre)")
    
    # Paso 3: Búsqueda de fecha
    print("[4] Buscando fecha de emisión...")
    fecha = buscar_fecha_emision(texto)
    if fecha:
        anio, mes = fecha
        print(f"    ✓ Fecha encontrada: {mes:02d}/{anio}")
    else:
        print("    ⚠ Fecha no encontrada")
    
    # Paso 4: Identificar consorcio
    print("[5] Identificando consorcio...")
    consorcio = identificar_consorcio(texto, consorcios)
    if consorcio:
        print(f"    ✓ Consorcio identificado: {consorcio['nombre']}")
        print(f"      ID: {consorcio['id']}")
        print(f"      RUC configurado: {consorcio['ruc']}")
    else:
        print("    ❌ Consorcio NO identificado (necesitaría API)")
    
    print(f"\n{'='*70}\n")


def main():
    # Cargar consorcios
    try:
        ruta_base = Path(__file__).parent
        consorcios = cargar_consorcios(str(ruta_base / "config/consorcios.json"))
        print(f"✓ Consorcios cargados: {[c['nombre'] for c in consorcios]}\n")
    except Exception as e:
        print(f"❌ Error cargando consorcios: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Buscar archivos de prueba
    ruta_base = Path(__file__).parent
    carpeta_pruebas = ruta_base / "tests/sample_invoices"
    
    if not carpeta_pruebas.exists():
        print(f"❌ Carpeta {carpeta_pruebas} no existe")
        print(f"   Ruta calculada: {carpeta_pruebas.absolute()}")
        sys.exit(1)
    
    archivos = list(carpeta_pruebas.glob("*.*"))
    # Excluir .gitkeep
    archivos = [a for a in archivos if a.name != ".gitkeep"]
    
    if not archivos:
        print(f"⚠ No hay facturas de prueba en {carpeta_pruebas}")
        print("  Copia tus PDFs/JPGs ahí y vuelve a ejecutar este script.")
        sys.exit(1)
    
    print(f"Encontrados {len(archivos)} archivo(s) de prueba:\n")
    for a in archivos:
        print(f"  - {a.name}")
    
    # Procesar cada factura
    for archivo in sorted(archivos):
        procesar_factura(str(archivo), consorcios)
    
    print("\n✓ Pruebas completadas")


if __name__ == "__main__":
    main()