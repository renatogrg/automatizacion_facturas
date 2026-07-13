"""
Monitorea la carpeta ENTRADA_FACTURA en tiempo real.
Cuando entra un archivo nuevo, lo procesa automáticamente.
"""

import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from src.processor import procesar_factura_completo
from src.utils.logger import obtener_logger

logger = obtener_logger("watcher")


class ManejadorFacturas(FileSystemEventHandler):
    """
    Escucha eventos de archivo en ENTRADA_FACTURA.
    Cuando entra un PDF o imagen, lo procesa.
    """
    
    def __init__(self, consorcios, carpeta_facturas, carpeta_pendientes, carpeta_entrada):
        self.consorcios = consorcios
        self.carpeta_facturas = carpeta_facturas
        self.carpeta_pendientes = carpeta_pendientes
        self.carpeta_entrada = carpeta_entrada
        self.archivos_procesados = set()
    
    def on_created(self, event):
        """Se dispara cuando se crea un archivo nuevo."""
        if event.is_directory:
            return
        
        ruta = event.src_path
        tiempo_espera = 0
        
        # Esperar a que el archivo se escriba completamente
        # (evita procesar archivos que aún se están copiando)
        tamaño_anterior = 0
        while tiempo_espera < 30:  # Aumentar de 10 a 30 segundos
            try:
                tamaño_actual = os.path.getsize(ruta)
                if tamaño_actual == tamaño_anterior and tamaño_actual > 0:
                    break  # El archivo dejó de crecer y tiene contenido, está listo
                tamaño_anterior = tamaño_actual
                time.sleep(1)  # Aumentar de 0.5 a 1 segundo
                tiempo_espera += 1
            except OSError:
                # El archivo aún no existe, intentar más tarde
                time.sleep(1)
                tiempo_espera += 1
        
        # Procesar solo si no ha sido procesado antes
        if ruta not in self.archivos_procesados:
            self.archivos_procesados.add(ruta)
            print(f"\n[WATCHER] Archivo detectado: {os.path.basename(ruta)}")
            
            try:
                procesar_factura_completo(
                    ruta,
                    self.consorcios,
                    self.carpeta_facturas,
                    self.carpeta_pendientes
                )
            except Exception as e:
                logger.error(f"Error procesando {ruta}: {e}")
                print(f"❌ Error al procesar {os.path.basename(ruta)}: {e}")


def iniciar_watcher(settings: dict, consorcios: list):
    """
    Inicia el monitoreo de ENTRADA_FACTURA.
    
    Args:
        settings: dict con paths (de config/settings.json)
        consorcios: lista de consorcios
    """
    carpeta_entrada = settings.get("carpeta_entrada", "C:\\FACTURAS\\ENTRADA_FACTURA")
    carpeta_facturas = settings.get("carpeta_facturas", "C:\\FACTURAS")
    carpeta_pendientes = settings.get("carpeta_pendientes", "C:\\FACTURAS\\PENDIENTES")
    
    # Crear carpetas si no existen
    Path(carpeta_entrada).mkdir(parents=True, exist_ok=True)
    
    
    # Configurar watcher
    manejador = ManejadorFacturas(
        consorcios,
        carpeta_facturas,
        carpeta_pendientes,
        carpeta_entrada
    )
    
    observador = Observer()
    observador.schedule(manejador, carpeta_entrada, recursive=False)
    observador.start()
    
    print(f"✓ Watcher iniciado. Monitoreando: {carpeta_entrada}")
    print("  Presiona Ctrl+C para detener.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⊘ Deteniendo watcher...")
        observador.stop()
    
    observador.join()