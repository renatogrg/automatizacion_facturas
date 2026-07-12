"""
Fase 3 - Respaldo con Claude Haiku 4.5, SOLO cuando la validacion local
(regex + fuzzy matching) no pudo identificar el consorcio con confianza.
Se prefiere enviar texto (barato) antes que imagen (mas caro).
"""

import os
from anthropic import Anthropic

MODELO = "claude-haiku-4-5-20251001"


def analizar_con_texto(texto_factura: str, consorcios: list) -> dict:
    cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # TODO: construir prompt que devuelva JSON con
    # consorcio, ruc, proveedor, ruc_proveedor, fecha, total
    raise NotImplementedError


def analizar_con_imagen(ruta_archivo: str, consorcios: list) -> dict:
    cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # TODO: enviar el PDF/imagen en base64 como ultimo recurso
    raise NotImplementedError
