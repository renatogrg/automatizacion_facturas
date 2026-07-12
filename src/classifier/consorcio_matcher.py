"""
Identificacion 100% local (gratis) del consorcio, por RUC y por nombre.
Se usa antes de considerar llamar a la API.
"""

import re
from rapidfuzz import fuzz


def buscar_ruc(texto: str) -> str | None:
    coincidencias = re.findall(r"\b\d{11}\b", texto)
    return coincidencias[0] if coincidencias else None


def identificar_consorcio(texto: str, consorcios: list) -> dict | None:
    ruc_encontrado = buscar_ruc(texto)
    for c in consorcios:
        if ruc_encontrado and c["ruc"] == ruc_encontrado:
            return c
        if fuzz.partial_ratio(c["nombre"].upper(), texto.upper()) > 90:
            return c
    return None
