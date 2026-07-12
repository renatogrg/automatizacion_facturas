"""
Fase 1 - Extraccion gratuita de texto nativo de un PDF (factura electronica).
Usa PyMuPDF (fitz). Si el PDF no trae texto (es una imagen), devuelve cadena vacia
y el pipeline debe pasar a ocr.py
"""

import fitz  # PyMuPDF


def extraer_texto_nativo(ruta_pdf: str) -> str:
    texto = ""
    with fitz.open(ruta_pdf) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto.strip()
