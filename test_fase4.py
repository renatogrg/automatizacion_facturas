r"""
Script de prueba Fase 4 - Organización y registro.

Procesa las facturas de prueba y las organiza localmente (simulado en salida_prueba\FACTURAS)
y en Drive si está disponible (G:\Mi unidad\FACTURAS).
"""

import sys
from pathlib import Path
import shutil
import os

sys.path.insert(0, str(Path(__file__).parent))

from src.processor import procesar_factura_completo
from src.utils.config_loader import cargar_consorcios, cargar_settings


def _mostrar_estructura(carpeta: Path, etiqueta: str):
    """Muestra los archivos dentro de una carpeta de salida."""
    archivos = sorted(carpeta.rglob("*"))
    archivos = [r for r in archivos if r.is_file()]
    if not archivos:
        print(f"  (vacía)")
        return
    for ruta in archivos:
        rel = ruta.relative_to(carpeta)
        print(f"  {rel}")


def main():
    # ── Cargar configuración ─────────────────────────────────────────────────
    consorcios = cargar_consorcios("config/consorcios.json")
    cfg        = cargar_settings("config/settings.json")

    drive_habilitado = cfg.get("drive_habilitado", False)
    carpeta_drive    = cfg.get("carpeta_facturas_drive", "")

    print(f"✓ Consorcios: {[c['nombre'] for c in consorcios]}")
    print(f"✓ Drive habilitado: {drive_habilitado}")
    if drive_habilitado:
        drive_disponible = Path(carpeta_drive).drive
        drive_ok = bool(drive_disponible) and Path(drive_disponible + "\\").exists()
        print(f"✓ Drive disponible: {drive_ok} ({carpeta_drive})")
    print()

    # ── Preparar carpetas de prueba ──────────────────────────────────────────
    carpeta_facturas  = Path("salida_prueba/FACTURAS")
    carpeta_entrada   = Path("salida_prueba/ENTRADA_FACTURA")
    carpeta_pendientes = Path("salida_prueba/FACTURAS/PENDIENTES")

    # Limpiar salida anterior
    for carpeta in [carpeta_facturas, carpeta_entrada]:
        if carpeta.exists():
            shutil.rmtree(carpeta)

    carpeta_entrada.mkdir(parents=True, exist_ok=True)
    carpeta_pendientes.mkdir(parents=True, exist_ok=True)

    # Copiar facturas de prueba a entrada simulada
    archivos_prueba = [
        a for a in Path("tests/sample_invoices").glob("*.*")
        if a.name != ".gitkeep"
    ]
    print(f"Copiando {len(archivos_prueba)} archivo(s) a entrada simulada...")
    for archivo in archivos_prueba:
        shutil.copy(archivo, carpeta_entrada / archivo.name)

    # ── Procesar ─────────────────────────────────────────────────────────────
    total    = 0
    exitosas = 0

    print()
    print("=" * 70)
    print("PROCESANDO FACTURAS")
    print("=" * 70)

    for archivo in sorted(carpeta_entrada.glob("*.*")):
        total += 1
        # Inyectar rutas del test en settings temporalmente
        cfg_test = cfg.copy()
        cfg_test["carpeta_facturas_local"] = str(carpeta_facturas)
        cfg_test["carpeta_pendientes_local"] = str(carpeta_pendientes)
        # Drive apunta a la ruta real (si está disponible, escribirá ahí)
        # Si no está disponible, file_organizer avisará y seguirá local

        if procesar_factura_completo(
            str(archivo),
            consorcios,
            str(carpeta_facturas),   # carpeta_facturas (compat.)
            str(carpeta_pendientes), # carpeta_pendientes (compat.)
        ):
            exitosas += 1

    # ── Resumen ──────────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print(f"RESUMEN: {exitosas}/{total} facturas procesadas exitosamente")
    print("=" * 70)

    print("\n📁 Estructura LOCAL generada:")
    print(f"   {carpeta_facturas.absolute()}")
    _mostrar_estructura(carpeta_facturas, "local")

    if drive_habilitado and carpeta_drive:
        drive_path = Path(carpeta_drive)
        if drive_path.exists():
            print(f"\n☁  Estructura DRIVE generada:")
            print(f"   {drive_path}")
            _mostrar_estructura(drive_path, "drive")
        else:
            print(f"\n☁  Drive no disponible — solo copia local guardada.")

    print()
    pendientes = list(carpeta_pendientes.glob("*"))
    pendientes = [p for p in pendientes if p.is_file() and p.suffix != ".xlsx"]
    if pendientes:
        print(f"⏳ En PENDIENTES ({len(pendientes)} archivo(s)):")
        for p in pendientes:
            print(f"   {p.name}")
        print("   → Se resolverán cuando la API key de Claude esté configurada.")


if __name__ == "__main__":
    main()