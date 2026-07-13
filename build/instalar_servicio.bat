"""
Script para instalar el sistema como servicio de Windows.

Uso:
    python build/instalar_servicio.py install     # Instalar servicio
    python build/instalar_servicio.py start       # Iniciar
    python build/instalar_servicio.py stop        # Detener
    python build/instalar_servicio.py remove      # Desinstalar
    
Ejecutar como ADMINISTRADOR.
"""

import sys
import os
import time
import threading
from pathlib import Path

import win32serviceutil
import win32service
import servicemanager


class SistemaFacturasService(win32serviceutil.ServiceFramework):
    """Servicio de Windows para el sistema de facturas."""
    
    _svc_name_ = "SistemaFacturas"
    _svc_display_name_ = "Sistema de Gestión Automática de Facturas"
    _svc_description_ = "Monitorea y procesa automáticamente facturas en C:\\FACTURAS\\ENTRADA_FACTURA"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.is_alive = True
        self.watcher_thread = None
    
    def SvcStop(self):
        """Se ejecuta cuando el usuario detiene el servicio."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_alive = False
        
        # Esperar a que el thread termine
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.watcher_thread.join(timeout=5)
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, "")
        )
    
    def SvcDoRun(self):
        """Se ejecuta cuando el servicio inicia."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        
        # Iniciar el watcher en un thread daemon
        self.watcher_thread = threading.Thread(target=self._run_watcher, daemon=True)
        self.watcher_thread.start()
        
        # Mantener el servicio vivo
        while self.is_alive:
            time.sleep(1)
    
    def _run_watcher(self):
        """Corre el watcher en background."""
        try:
            # Asegurar que el directorio del programa esté en el path
            ruta_programa = Path(__file__).parent.parent
            sys.path.insert(0, str(ruta_programa))
            
            # Cambiar al directorio del programa
            os.chdir(str(ruta_programa))
            
            from src.watcher import iniciar_watcher
            from src.utils.config_loader import cargar_settings, cargar_consorcios
            from src.utils.logger import obtener_logger
            
            logger = obtener_logger("servicio")
            logger.info("Servicio iniciado correctamente")
            
            settings = cargar_settings("config/settings.json")
            consorcios = cargar_consorcios("config/consorcios.json")
            
            # Iniciar el watcher (bloqueante)
            iniciar_watcher(settings, consorcios)
            
        except Exception as e:
            try:
                from src.utils.logger import obtener_logger
                logger = obtener_logger("servicio")
                logger.error(f"Error crítico en watcher: {e}")
            except:
                pass
            
            servicemanager.LogErrorMsg(f"Error en servicio: {e}")
            self.is_alive = False


def main():
    if len(sys.argv) == 1:
        # Sin argumentos, ejecutar como servicio
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingleServiceProcess(SistemaFacturasService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Con argumentos: install, start, stop, remove
        win32serviceutil.HandleCommandLine(SistemaFacturasService)


if __name__ == '__main__':
    main()