import json
import os
from pathlib import Path


def obtener_ruta_base():
    """Retorna la ruta base del proyecto."""
    return Path(__file__).parent.parent.parent


def cargar_settings(ruta="config/settings.json") -> dict:
    ruta_base = obtener_ruta_base()
    ruta_completa = ruta_base / ruta
    with open(ruta_completa, encoding="utf-8") as f:
        return json.load(f)


def cargar_consorcios(ruta="config/consorcios.json") -> list:
    ruta_base = obtener_ruta_base()
    ruta_completa = ruta_base / ruta
    with open(ruta_completa, encoding="utf-8") as f:
        return json.load(f)["consorcios"]