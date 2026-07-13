"""
Identificación 100% local (gratis) del consorcio, por RUC y por nombre.
Se usa antes de considerar llamar a la API.
"""

import re
from rapidfuzz import fuzz


# Etiquetas que preceden al RUC/DNI del CLIENTE en facturas peruanas.
# Se ordenan de más específico a más genérico para reducir falsos positivos.
_ETIQUETAS_CLIENTE = re.compile(
    r"""
    (?:
        r\.?u\.?c\.?\s*/\s*d\.?n\.?i\.?   # RUC/DNI  (Plasita, Ferreport)
      | clie(?:nte)?                        # Cliente, CLIE  (Comercial Oscar, Tai Loy)
      | jente                               # OCR imperfecto de "Cliente" (Ferreport)
      | raz(?:on|\.)\s*social               # RAZ.SOCIAL, Razon Social
      | cliente\s*ruc                       # "Cliente RUC" juntos
    )
    [\s:]*
    """,
    re.IGNORECASE | re.VERBOSE,
)

_RUC_11 = re.compile(r"\b(\d{11})\b")


def buscar_ruc_cliente(texto: str, consorcios: list) -> str | None:
    """
    Busca el RUC del cliente/consorcio en el texto.
    Estrategia:
      1. Buscar una etiqueta de cliente seguida de un RUC de 11 dígitos.
      2. Si no, buscar cualquier RUC de 11 dígitos que coincida con un consorcio conocido.
      3. Si no, devolver None (no el primer RUC, que suele ser el del proveedor).
    """
    rucs_conocidos = {c["ruc"] for c in consorcios}

    # Estrategia 1: etiqueta de cliente → RUC
    for m in _ETIQUETAS_CLIENTE.finditer(texto):
        fragmento = texto[m.end():m.end() + 60]  # los ~60 chars tras la etiqueta
        ruc_m = _RUC_11.search(fragmento)
        if ruc_m:
            return ruc_m.group(1)

    # Estrategia 2: cualquier RUC de 11 dígitos que sea de un consorcio conocido
    for ruc_m in _RUC_11.finditer(texto):
        if ruc_m.group(1) in rucs_conocidos:
            return ruc_m.group(1)

    return None


def buscar_ruc(texto: str) -> str | None:
    """
    Devuelve el primer RUC de 11 dígitos que aparece en el texto
    (usado para capturar el RUC del PROVEEDOR, que aparece al inicio).
    """
    m = _RUC_11.search(texto)
    return m.group(1) if m else None


def buscar_fecha_emision(texto: str) -> tuple[int, int] | None:
    """
    Busca la fecha de emisión en formatos comunes peruanos:
      - DD/MM/YYYY hh:mm  (Plasita Mil Ofertas, Ferreport)
      - YYYY-MM-DD        (el click / Wayayo)
      - DD/MM/YYYY        (genérico)
      - /MM/YY al pie del ticket (Tai Loy, posiblemente truncado)

    Returns:
        Tupla (año, mes) o None si no encuentra.
    """
    # Prioridad 1: buscar junto a etiqueta de fecha para evitar fechas de vencimiento
    patron_con_etiqueta = re.compile(
        r"(?:fecha\s*(?:de\s*)?emisi[oó]n|f[/.]h\s*emisi[oó]n|fecha)[^\d]*"
        r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})"
        r"|"
        r"(\d{4})[/\-](\d{2})[/\-](\d{2})",  # YYYY-MM-DD
        re.IGNORECASE,
    )
    for m in patron_con_etiqueta.finditer(texto):
        g = m.groups()
        if g[0]:  # DD/MM/YYYY o DD/MM/YY
            d, mo, y = int(g[0]), int(g[1]), int(g[2])
            if y < 100:
                y += 2000
            if 1 <= mo <= 12 and 2000 <= y <= 2099:
                return (y, mo)
        elif g[3]:  # YYYY-MM-DD
            y, mo = int(g[3]), int(g[4])
            if 1 <= mo <= 12 and 2000 <= y <= 2099:
                return (y, mo)

    # Prioridad 2: cualquier fecha DD/MM/YYYY en el texto (sin etiqueta)
    for m in re.finditer(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", texto):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 2000 <= y <= 2099:
            return (y, mo)

    # Prioridad 3: YYYY-MM-DD sin etiqueta
    for m in re.finditer(r"(\d{4})[/\-](\d{2})[/\-](\d{2})", texto):
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12 and 2000 <= y <= 2099:
            return (y, mo)

    return None


def identificar_consorcio(texto: str, consorcios: list) -> dict | None:
    """
    Identifica el consorcio basándose en:
      1. RUC del cliente exacto (prioridad alta, gratis).
      2. Nombre fuzzy contra el texto (respaldo).

    Args:
        texto: texto extraído de la factura
        consorcios: lista de dicts con id, nombre, ruc

    Returns:
        Dict con {id, nombre, ruc} del consorcio identificado, o None
    """
    # Paso 1: RUC exacto del cliente/consorcio
    ruc_cliente = buscar_ruc_cliente(texto, consorcios)
    if ruc_cliente:
        for c in consorcios:
            if c["ruc"] == ruc_cliente:
                return c

    # Paso 2: fuzzy match del nombre
    texto_upper = texto.upper()
    mejor_match = None
    mejor_score = 0

    for c in consorcios:
        score = fuzz.partial_ratio(c["nombre"].upper(), texto_upper)
        if score > mejor_score:
            mejor_score = score
            mejor_match = c

    if mejor_score > 85:
        return mejor_match

    return None