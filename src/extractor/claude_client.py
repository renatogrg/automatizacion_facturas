"""
Fase 3 - Respaldo con Claude Haiku 4.5.
Se llama SOLO cuando el procesamiento local (regex + fuzzy) no pudo
completar algún campo obligatorio (consorcio o fecha).

Estrategia de costo mínimo:
  - Si el PDF tiene texto nativo → enviar solo texto (barato, ~$0.001)
  - Si es foto/escaneo          → enviar imagen en base64 (un poco más, ~$0.003)
"""

import os
import base64
import json
from pathlib import Path
from anthropic import Anthropic

MODELO = "claude-haiku-4-5-20251001"

PROMPT_SISTEMA = """Eres un extractor de datos de facturas peruanas (comprobantes de pago electrónico).
Tu única tarea es analizar el documento y devolver un JSON con exactamente estos campos:

{
  "consorcio": "nombre exacto del cliente/consorcio que aparece en la factura, o null",
  "fecha_dd_mm_yyyy": "fecha de emisión en formato DD/MM/YYYY, o null",
  "proveedor": "nombre del proveedor/emisor de la factura, o null",
  "ruc_proveedor": "RUC de 11 dígitos del proveedor, o null",
  "total": "importe total como número decimal (ej: 248.40), o null"
}

Reglas:
- El campo "consorcio" es el CLIENTE (quien recibe la factura), NO el proveedor.
- Busca el cliente en campos como: Cliente, CLIENTE, Clie, Jente, Raz.Social, RAZ.SOCIAL.
- La fecha de emisión puede aparecer como: Fecha de emisión, F/H emisión, FECHA, o al pie del ticket.
- Si un campo no está visible o es ilegible, usa null.
- Responde SOLO con el JSON, sin texto adicional, sin comillas de código."""


def _construir_lista_consorcios(consorcios: list) -> str:
    return "Consorcios válidos (cliente debe ser uno de estos): " + ", ".join(consorcios)


def analizar_con_texto(texto_factura: str, consorcios: list) -> dict | None:
    """
    Envía el texto extraído a Claude para completar campos faltantes.
    Usa este camino cuando el PDF tenía capa de texto (factura electrónica).
    Costo estimado: ~$0.001 por factura.
    """
    try:
        cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        prompt = f"{_construir_lista_consorcios(consorcios)}\n\nTexto de la factura:\n{texto_factura[:3000]}"

        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=300,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": prompt}],
        )
        return _parsear_respuesta(respuesta.content[0].text)
    except Exception as e:
        print(f"  ⚠ Claude (texto) falló: {e}")
        return None


def analizar_con_imagen(ruta_archivo: str, consorcios: list) -> dict | None:
    """
    Envía la imagen/PDF como base64 a Claude con visión.
    Usa este camino cuando es foto o PDF escaneado sin texto.
    Costo estimado: ~$0.003 por imagen.
    """
    try:
        cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        ruta = Path(ruta_archivo)
        extension = ruta.suffix.lower()

        # Determinar media_type
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf",
        }
        media_type = media_types.get(extension, "image/jpeg")

        # Leer y codificar en base64
        with open(ruta_archivo, "rb") as f:
            datos_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

        # Construir el bloque de contenido correcto según el tipo
        if media_type == "application/pdf":
            bloque_doc = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": datos_b64,
                },
            }
        else:
            bloque_doc = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": datos_b64,
                },
            }

        prompt_usuario = f"{_construir_lista_consorcios(consorcios)}\n\nAnaliza esta factura y extrae los datos solicitados."

        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=300,
            system=PROMPT_SISTEMA,
            messages=[
                {
                    "role": "user",
                    "content": [
                        bloque_doc,
                        {"type": "text", "text": prompt_usuario},
                    ],
                }
            ],
        )
        return _parsear_respuesta(respuesta.content[0].text)

    except Exception as e:
        print(f"  ⚠ Claude (imagen) falló: {e}")
        return None


def _parsear_respuesta(texto: str) -> dict | None:
    """
    Parsea el JSON que devuelve Claude y lo convierte a los campos
    que usa processor.py: anio, mes, consorcio, proveedor, ruc_proveedor, total.
    """
    try:
        # Limpiar posibles backticks de markdown
        texto = texto.strip().strip("`").strip()
        if texto.startswith("json"):
            texto = texto[4:].strip()

        datos = json.loads(texto)

        resultado = {
            "consorcio": datos.get("consorcio"),
            "proveedor": datos.get("proveedor"),
            "ruc_proveedor": datos.get("ruc_proveedor"),
            "total": datos.get("total"),
            "anio": None,
            "mes": None,
        }

        # Parsear fecha DD/MM/YYYY
        fecha_str = datos.get("fecha_dd_mm_yyyy")
        if fecha_str:
            partes = fecha_str.replace("-", "/").split("/")
            if len(partes) == 3:
                try:
                    dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
                    if anio < 100:
                        anio += 2000
                    if 1 <= mes <= 12 and 2000 <= anio <= 2099:
                        resultado["anio"] = anio
                        resultado["mes"] = mes
                except ValueError:
                    pass

        return resultado

    except (json.JSONDecodeError, Exception) as e:
        print(f"  ⚠ No se pudo parsear respuesta de Claude: {e}")
        print(f"  Respuesta recibida: {texto[:200]}")
        return None