"""
Sistema de logging simple.
"""

import logging
from pathlib import Path

# Crear carpeta de logs si no existe
Path("logs").mkdir(exist_ok=True)


def obtener_logger(nombre: str) -> logging.Logger:
    """
    Retorna un logger configurado.
    
    Args:
        nombre: nombre del módulo (ej. "watcher", "main")
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(nombre)
    
    if not logger.handlers:
        handler = logging.FileHandler("logs/sistema.log", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger