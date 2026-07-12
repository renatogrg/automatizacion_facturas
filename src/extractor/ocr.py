"""
Fase 2 - OCR local y gratuito para fotos o PDFs escaneados.
Requiere tener Tesseract-OCR instalado en la PC (no solo la libreria de Python).
"""

import pytesseract
from PIL import Image


def extraer_texto_ocr(ruta_imagen_o_pdf: str) -> str:
    # TODO: si es PDF, convertir primero cada pagina a imagen con pdf2image
    imagen = Image.open(ruta_imagen_o_pdf)
    return pytesseract.image_to_string(imagen, lang="spa").strip()
