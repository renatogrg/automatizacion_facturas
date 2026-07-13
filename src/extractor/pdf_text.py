"""
Fase 1 - Extraccion gratuita de texto nativo de un PDF (factura electronica).
Usa PyMuPDF (fitz). Si el PDF no trae texto (es una imagen), devuelve cadena vacia
y el pipeline debe pasar a ocr.py
"""

import fitz  # PyMuPDF

EXTENSIONES_VALIDAS = {".pdf", ".jpg", ".jpeg", ".png"}


def es_extension_valida(ruta: str) -> bool:
    """Retorna True solo si el archivo tiene una extensión soportada."""
    from pathlib import Path
    return Path(ruta).suffix.lower() in EXTENSIONES_VALIDAS


def extraer_texto_nativo(ruta_pdf: str) -> str:
    """
    Intenta extraer texto nativo de un PDF.
    Si el archivo no es PDF, devuelve cadena vacía (pasará a OCR).
    Si es PDF pero no tiene texto (escaneo/foto), también devuelve vacío.
    """
    from pathlib import Path
    if Path(ruta_pdf).suffix.lower() != ".pdf":
        return ""  # No es PDF, no intentar
    texto = ""
    with fitz.open(ruta_pdf) as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto.strip()