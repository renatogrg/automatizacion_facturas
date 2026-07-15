"""
Monitorea la carpeta ENTRADA_FACTURA en tiempo real.
Cuando entra un archivo nuevo, lo procesa automáticamente.
"""

import os
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
        tamaño_anterior = 0
        while tiempo_espera < 30:
            try:
                tamaño_actual = os.path.getsize(ruta)
                if tamaño_actual == tamaño_anterior and tamaño_actual > 0:
                    break
                tamaño_anterior = tamaño_actual
                time.sleep(1)
                tiempo_espera += 1
            except OSError:
                time.sleep(1)
                tiempo_espera += 1
        
        nombre_archivo = os.path.basename(ruta)
        
        # Verificar si el archivo ya existe en FACTURAS (fue procesado antes)
        if self._archivo_ya_existe(nombre_archivo):
            print(f"\n[WATCHER] Archivo duplicado detectado: {nombre_archivo}")
            self._enviar_a_duplicadas(ruta, nombre_archivo)
            return
        
        # Procesar archivo nuevo
        if ruta not in self.archivos_procesados:
            self.archivos_procesados.add(ruta)
            print(f"\n[WATCHER] Archivo detectado: {nombre_archivo}")
            
            try:
                procesar_factura_completo(
                    ruta,
                    self.consorcios,
                    self.carpeta_facturas,
                    self.carpeta_pendientes
                )
            except Exception as e:
                logger.error(f"Error procesando {ruta}: {e}")
                print(f"❌ Error al procesar {nombre_archivo}: {e}")
    
    def _archivo_ya_existe(self, nombre_archivo: str) -> bool:
        """
        Verifica si un archivo con el mismo nombre ya existe en FACTURAS
        (es decir, ya fue procesado antes).
        """
        carpeta_facturas = Path(self.carpeta_facturas)
        print(f"  [DEBUG] Buscando duplicado: {nombre_archivo}")
        print(f"  [DEBUG] Carpeta: {carpeta_facturas}")
        print(f"  [DEBUG] Existe: {carpeta_facturas.exists()}")

        # Si la carpeta no existe, no hay duplicados
        if not carpeta_facturas.exists():
            print(f"  [DEBUG] Carpeta no existe, no es duplicado")
            return False
        
        # Buscar en todas las subcarpetas de consorcios
        try:
            encontrado = False
            for consorcio_dir in carpeta_facturas.iterdir():
                if not consorcio_dir.is_dir():
                    continue
            
                # Saltar carpetas especiales
                if consorcio_dir.name in ["Facturas Pendientes", "ENTRADA_FACTURA"]:
                    continue

                print(f"  [DEBUG] Buscando en: {consorcio_dir.name}")
            
                # Buscar en todos los años/meses de este consorcio
                for archivo in consorcio_dir.rglob(nombre_archivo):
                    if archivo.is_file():
                        print(f"  [DEBUG] Duplicado encontrado: {archivo}")
                        return True
            if not encontrado:
                print(f"  [DEBUG] No encontrado, es archivo nuevo")
            return encontrado
        
        except Exception as e:
            print(f"  [DEBUG] Error: {e}")
            logger.error(f"Error verificando duplicados: {e}")
        
        return False
    
    def _enviar_a_duplicadas(self, ruta_archivo: str, nombre_archivo: str):
        """
        Mueve un archivo duplicado a FACTURAS PENDIENTES/Facturas duplicadas
        tanto en local como en Drive.
        """
        from src.organizer.file_organizer import mover_a_destino
        
        try:
            cfg = self._cargar_config()
            local = cfg.get("carpeta_facturas_local", self.carpeta_facturas)
            drive_on = cfg.get("drive_habilitado", False)
            
            # Crear carpeta local
            carpeta_duplicadas_local = Path(local) / "FACTURAS PENDIENTES" / "Facturas duplicadas"
            carpeta_duplicadas_local.mkdir(parents=True, exist_ok=True)
            
            ruta_destino_local = carpeta_duplicadas_local / nombre_archivo
            if ruta_destino_local.exists():
                base, ext = os.path.splitext(nombre_archivo)
                contador = 1
                while (carpeta_duplicadas_local / f"{base}_{contador}{ext}").exists():
                    contador += 1
                ruta_destino_local = carpeta_duplicadas_local / f"{base}_{contador}{ext}"
            
            shutil.move(ruta_archivo, str(ruta_destino_local))
            
            # Subir a Drive por API (el proyecto ya no usa unidad G:\ mapeada
            # de Drive for Desktop; todo se sube vía Google Drive API)
            if drive_on:
                try:
                    from src.cloud.google_drive_client import (
                        obtener_o_crear_carpeta,
                        subir_archivo,
                    )
                    id_facturas = obtener_o_crear_carpeta("FACTURAS")
                    id_pendientes = obtener_o_crear_carpeta("FACTURAS PENDIENTES", id_facturas)
                    id_duplicadas = obtener_o_crear_carpeta("Facturas duplicadas", id_pendientes)
                    if id_duplicadas:
                        subir_archivo(str(ruta_destino_local), ruta_destino_local.name, id_duplicadas)
                except Exception as e:
                    print(f"  ⚠ Drive duplicado: {e} (local está guardado)")
            
            print(f"  ✓ Movido a Facturas duplicadas")
            
        except Exception as e:
            print(f"  ❌ Error al mover a duplicadas: {e}")
            logger.error(f"Error moviendo a duplicadas {ruta_archivo}: {e}")
    
    def _cargar_config(self):
        """Carga settings.json para acceder a rutas de Drive."""
        from src.utils.config_loader import cargar_settings
        try:
            return cargar_settings()
        except:
            return {}




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
    print("  (Servicio en segundo plano)\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⊘ Deteniendo watcher...")
        observador.stop()
    except Exception as e:
        logger.error(f"Error en watcher: {e}")
    
    observador.join()