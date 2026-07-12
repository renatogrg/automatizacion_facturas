"""
Identificación 100% local (gratis) del consorcio, por RUC y por nombre.
Se usa antes de considerar llamar a la API.
"""

import re
from datetime import datetime
from rapidfuzz import fuzz


def buscar_ruc(texto: str) -> str | None:
    """
    Busca un RUC (11 dígitos) en el texto.
    Los RUC peruanos siempre tienen exactamente 11 dígitos.
    
    Args:
        texto: texto extraído de la factura
        
    Returns:
        RUC encontrado (cadena de 11 dígitos) o None
    """
    coincidencias = re.findall(r"\b\d{11}\b", texto)
    # Retorna el primero encontrado (generalmente el del proveedor)
    # pero una versión mejorada podría buscar el RUC del cliente
    return coincidencias[0] if coincidencias else None


def buscar_fecha_emision(texto: str) -> tuple[int, int] | None:
    """
    Busca la fecha de emisión en formatos comunes peruanos:
    - DD/MM/YYYY
    - DD-MM-YYYY
    - Fecha de emisión: ...
    
    Args:
        texto: texto extraído
        
    Returns:
        Tupla (año, mes) o None si no encuentra
    """
    # Patrón: DD/MM/YYYY o DD-MM-YYYY
    patrones = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
    ]
    
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            grupos = match.groups()
            if len(grupos) == 3:
                # Verificar si es DD/MM/YYYY (grupos[2] es año > 1900)
                if int(grupos[2]) > 1900:
                    anio = int(grupos[2])
                    mes = int(grupos[1])
                else:
                    # Es YYYY/MM/DD
                    anio = int(grupos[0])
                    mes = int(grupos[1])
                
                if 1 <= mes <= 12 and 2000 <= anio <= 2099:
                    return (anio, mes)
    
    return None


def identificar_consorcio(texto: str, consorcios: list) -> dict | None:
    """
    Identifica el consorcio basándose en RUC exacto (prioridad alta)
    o nombre fuzzy (respaldo).
    
    Args:
        texto: texto extraído de la factura
        consorcios: lista de dicts con id, nombre, ruc
        
    Returns:
        Dict con {id, nombre, ruc} del consorcio identificado, o None
    """
    # Paso 1: Buscar RUC exacto (más confiable)
    ruc_encontrado = buscar_ruc(texto)
    if ruc_encontrado:
        for c in consorcios:
            if c["ruc"] == ruc_encontrado:
                return c
    
    # Paso 2: Buscar por nombre fuzzy (si RUC no funcionó)
    texto_upper = texto.upper()
    mejor_match = None
    mejor_score = 0
    
    for c in consorcios:
        score = fuzz.partial_ratio(c["nombre"].upper(), texto_upper)
        if score > mejor_score:
            mejor_score = score
            mejor_match = c
    
    # Considerar un match válido si el score es > 85
    if mejor_score > 85:
        return mejor_match
    
    return None