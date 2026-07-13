import json
import os
from pathlib import Path
from dotenv import load_dotenv


def obtener_ruta_base() -> Path:
    """Retorna la ruta base del proyecto (carpeta que contiene 'src' y 'config')."""
    return Path(__file__).parent.parent.parent


def _cargar_env():
    """Carga el .env desde config/.env una sola vez."""
    ruta_env = obtener_ruta_base() / "config" / ".env"
    if ruta_env.exists():
        load_dotenv(ruta_env, override=False)


# Se carga automáticamente al importar este módulo
_cargar_env()


def cargar_settings(ruta="config/settings.json") -> dict:
    ruta_completa = obtener_ruta_base() / ruta
    with open(ruta_completa, encoding="utf-8") as f:
        return json.load(f)


def cargar_consorcios(ruta="config/consorcios.json") -> list:
    ruta_completa = obtener_ruta_base() / ruta
    with open(ruta_completa, encoding="utf-8") as f:
        return json.load(f)["consorcios"]


def ruta_tesseract() -> str:
    """
    Devuelve la ruta de Tesseract.
    Primero busca en el .env (TESSERACT_PATH), luego prueba ubicaciones estándar.
    Esto permite que funcione en cualquier PC sin editar el código.
    """
    # 1. Variable de entorno explícita (en config/.env)
    ruta = os.environ.get("TESSERACT_PATH", "")
    if ruta and Path(ruta).exists():
        return ruta

    # 2. Ubicaciones estándar de Windows
    candidatos = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\rodri\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]
    for c in candidatos:
        if Path(c).exists():
            return c

    # 3. En PATH del sistema (Linux/macOS o Windows con Tesseract en PATH)
    import shutil
    en_path = shutil.which("tesseract")
    if en_path:
        return en_path

    return ""  # No encontrado; ocr.py lo manejará con un mensaje claro