"""
Fase 2 - OCR local y gratuito para fotos o PDFs escaneados.
Requiere tener Tesseract-OCR instalado en la PC.
La ruta se detecta automáticamente (via config_loader) — no hay rutas hardcodeadas.
"""

import pytesseract
from PIL import Image
from src.utils.config_loader import ruta_tesseract


def _configurar_tesseract():
    ruta = ruta_tesseract()
    if ruta:
        pytesseract.pytesseract.tesseract_cmd = ruta
    # Si no se encontró, pytesseract usará el que esté en PATH del sistema


_configurar_tesseract()


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
            paginas = convert_from_path(ruta_imagen_o_pdf, dpi=200, thread_count=2)
            return "\n".join(
                pytesseract.image_to_string(p, lang="spa").strip()
                for p in paginas
            ).strip()

        imagen = Image.open(ruta_imagen_o_pdf)
        return pytesseract.image_to_string(imagen, lang="spa").strip()

    except pytesseract.TesseractNotFoundError:
        print("  ⚠ Tesseract no encontrado. Instálalo desde https://github.com/UB-Mannheim/tesseract/wiki")
        return ""
    except Exception as e:
        print(f"  ⚠ Error en OCR: {e}")
        return ""