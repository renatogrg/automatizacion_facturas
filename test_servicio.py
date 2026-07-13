"""
Prueba para simular lo que hace el servicio.
"""

import sys
import os
from pathlib import Path

# Simular lo que hace el servicio
ruta_programa = Path(__file__).parent
sys.path.insert(0, str(ruta_programa))
os.chdir(str(ruta_programa))

try:
    print("1. Importando módulos...")
    from src.watcher import iniciar_watcher
    from src.utils.config_loader import cargar_settings, cargar_consorcios
    from src.utils.logger import obtener_logger
    
    print("2. Obteniendo logger...")
    logger = obtener_logger("test")
    
    print("3. Cargando configuración...")
    settings = cargar_settings("config/settings.json")
    print(f"   Settings: {settings}")
    
    print("4. Cargando consorcios...")
    consorcios = cargar_consorcios("config/consorcios.json")
    print(f"   Consorcios: {len(consorcios)}")
    
    print("5. Iniciando watcher...")
    iniciar_watcher(settings, consorcios)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()