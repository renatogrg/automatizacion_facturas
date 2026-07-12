"""
Fase 2 - OCR local y gratuito para fotos o PDFs escaneados.
Requiere tener Tesseract-OCR instalado en la PC (no solo la libreria de Python).
"""

import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os

# Configurar la ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\rodri\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

def extraer_texto_ocr(ruta_imagen_o_pdf: str) -> str:
    if ruta_imagen_o_pdf.lower().endswith(".pdf"):
        paginas = convert_from_path(ruta_imagen_o_pdf, dpi=200, thread_count=4)
        return "\n".join(
            pytesseract.image_to_string(pagina, lang="spa").strip()
            for pagina in paginas
        ).strip()

    imagen = Image.open(ruta_imagen_o_pdf)
    return pytesseract.image_to_string(imagen, lang="spa").strip()
