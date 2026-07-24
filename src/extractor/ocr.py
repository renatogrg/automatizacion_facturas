"""
Fase 2 - OCR local y gratuito para fotos o PDFs escaneados.
Requiere tener Tesseract-OCR instalado en la PC.
La ruta se detecta automáticamente (via config_loader) — no hay rutas hardcodeadas.
"""

import pytesseract
from pathlib import Path
from PIL import Image
from src.utils.config_loader import ruta_tesseract


def _configurar_tesseract():
    ruta = ruta_tesseract()
    if ruta:
        pytesseract.pytesseract.tesseract_cmd = ruta
    # Si no se encontró, pytesseract usará el que esté en PATH del sistema


_configurar_tesseract()


def _poppler_path() -> str | None:
    """Detecta la ruta de Poppler automáticamente sin depender del PATH del sistema."""
    candidatos = [
        r"C:\SistemaFacturas\poppler\Library\bin",
        r"C:\Program Files\poppler\Library\bin",
        r"C:\poppler\Library\bin",
        # Entorno de desarrollo: build/poppler junto al proyecto
        str(Path(__file__).resolve().parents[2] / "build" / "poppler" / "Library" / "bin"),
    ]
    for ruta in candidatos:
        if Path(ruta).exists():
            return ruta
    return None


def extraer_texto_ocr(ruta_imagen_o_pdf: str) -> str:
    """
    Extrae texto de una imagen (JPEG, PNG) o PDF escaneado usando Tesseract.
    Devuelve cadena vacía si Tesseract no está instalado o si falla la extracción.
    """
    try:
        if ruta_imagen_o_pdf.lower().endswith(".pdf"):
            try:
                from pdf2image import convert_from_path
            except ImportError:
                print("  ⚠ pdf2image no instalado — no se puede leer PDF escaneado")
                return ""
            paginas = convert_from_path(
                ruta_imagen_o_pdf, dpi=200, thread_count=2,
                poppler_path=_poppler_path(),
            )
            return "\n".join(
                pytesseract.image_to_string(p, lang="spa+spa_old").strip()
                for p in paginas
            ).strip()

        imagen = Image.open(ruta_imagen_o_pdf)
        return pytesseract.image_to_string(imagen, lang="spa+spa_old").strip()

    except pytesseract.TesseractNotFoundError:
        print("  ⚠ Tesseract no encontrado. Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki")
        return ""
    except Exception as e:
        print(f"  ⚠ Error en OCR: {e}")
        return ""