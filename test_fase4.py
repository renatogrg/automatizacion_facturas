"""
Script de prueba Fase 4 - Organización y registro.

Procesa las facturas de prueba y las organiza en C:\FACTURAS (simulado en carpeta local).
"""

import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent))

from src.processor import procesar_factura_completo
from src.utils.config_loader import cargar_consorcios


def main():
    # Cargar config
    consorcios = cargar_consorcios("config/consorcios.json")
    print(f"✓ Consorcios: {[c['nombre'] for c in consorcios]}\n")
    
    # Crear carpetas de salida simuladas
    carpeta_facturas = Path("salida_prueba/FACTURAS")
    carpeta_entrada = Path("salida_prueba/ENTRADA_FACTURA")
    carpeta_pendientes = Path("salida_prueba/FACTURAS/PENDIENTES")
    
    # Limpiar si existe
    if carpeta_facturas.exists():
        shutil.rmtree(carpeta_facturas)
    if carpeta_entrada.exists():
        shutil.rmtree(carpeta_entrada)
    
    # Crear estructura
    carpeta_entrada.mkdir(parents=True, exist_ok=True)
    carpeta_pendientes.mkdir(parents=True, exist_ok=True)
    
    # Copiar archivos de prueba a "entrada"
    archivos_prueba = list(Path("tests/sample_invoices").glob("*.*"))
    archivos_prueba = [a for a in archivos_prueba if a.name != ".gitkeep"]
    
    print(f"Copiando {len(archivos_prueba)} archivo(s) a entrada simulada...\n")
    for archivo in archivos_prueba:
        shutil.copy(archivo, carpeta_entrada / archivo.name)
    
    # Procesar cada archivo
    total = 0
    exitosas = 0
    
    print("="*70)
    print("PROCESANDO FACTURAS")
    print("="*70)
    
    for archivo in sorted(carpeta_entrada.glob("*.*")):
        total += 1
        if procesar_factura_completo(
            str(archivo),
            consorcios,
            str(carpeta_facturas),
            str(carpeta_pendientes)
        ):
            exitosas += 1
    
    print("\n" + "="*70)
    print(f"RESUMEN: {exitosas}/{total} facturas procesadas exitosamente")
    print(f"Carpeta de salida: {carpeta_facturas.absolute()}")
    print("="*70)
    
    # Mostrar estructura creada
    print("\nEstructura de carpetas generada:")
    for ruta in sorted(carpeta_facturas.rglob("*")):
        if ruta.is_file():
            rel = ruta.relative_to(carpeta_facturas)
            print(f"  {rel}")


if __name__ == "__main__":
    main()