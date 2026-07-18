"""
Fase 3 - Respaldo con Groq (modelos Llama/GPT-OSS via inferencia rápida).
Se llama SOLO cuando el procesamiento local (regex + fuzzy) no pudo
completar algun campo obligatorio (consorcio o fecha).

Groq API es compatible con el SDK/protocolo de OpenAI (chat.completions),
y tiene un tier gratuito generoso.

IMPORTANTE: a diferencia de Claude, Groq NO acepta PDF como documento nativo.
Solo acepta imágenes (JPEG/PNG) en sus modelos de visión. Por eso, cuando el
archivo es un PDF sin texto (escaneado), se convierte la primera página a
imagen con pdf2image antes de enviarla.
"""

import os
import base64
import json
from pathlib import Path
from groq import Groq

# Modelos recomendados actuales de Groq (revisar https://console.groq.com/docs/models
# si alguno queda deprecado - Groq rota su catálogo con cierta frecuencia).
MODELO_TEXTO = "openai/gpt-oss-120b"
MODELO_VISION = "qwen/qwen3.6-27b"

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


def _cliente() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def analizar_con_texto(texto_factura: str, consorcios: list) -> dict | None:
    """
    Envía el texto extraído a Groq para completar campos faltantes.
    Usa este camino cuando el PDF tenía capa de texto (factura electrónica).
    """
    try:
        cliente = _cliente()
        prompt = f"{_construir_lista_consorcios(consorcios)}\n\nTexto de la factura:\n{texto_factura[:3000]}"

        respuesta = cliente.chat.completions.create(
            model=MODELO_TEXTO,
            max_tokens=300,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": prompt},
            ],
        )
        return _parsear_respuesta(respuesta.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠ Groq (texto) falló: {e}")
        return None


def _convertir_a_imagen_base64(ruta_archivo: str) -> tuple[str, str] | None:
    """
    Devuelve (base64_datos, media_type) listos para enviar a Groq.
    Si es PDF, renderiza la primera página como PNG (Groq no acepta PDF nativo).
    """
    ruta = Path(ruta_archivo)
    extension = ruta.suffix.lower()

    if extension == ".pdf":
        try:
            from pdf2image import convert_from_path
        except ImportError:
            print("  ⚠ pdf2image no instalado — no se puede convertir PDF para Groq")
            return None
        paginas = convert_from_path(ruta_archivo, dpi=200, thread_count=1, first_page=1, last_page=1)
        if not paginas:
            return None
        import io
        buffer = io.BytesIO()
        paginas[0].save(buffer, format="PNG")
        datos_b64 = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
        return datos_b64, "image/png"

    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    media_type = media_types.get(extension, "image/jpeg")
    with open(ruta_archivo, "rb") as f:
        datos_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
    return datos_b64, media_type


def analizar_con_imagen(ruta_archivo: str, consorcios: list) -> dict | None:
    """
    Envía la imagen (o primera página del PDF convertida a imagen) a un
    modelo de visión de Groq. Usa este camino cuando es foto o PDF escaneado
    sin texto.
    """
    try:
        resultado_conversion = _convertir_a_imagen_base64(ruta_archivo)
        if resultado_conversion is None:
            return None
        datos_b64, media_type = resultado_conversion

        cliente = _cliente()
        prompt_usuario = f"{_construir_lista_consorcios(consorcios)}\n\nAnaliza esta factura y extrae los datos solicitados."

        respuesta = cliente.chat.completions.create(
            model=MODELO_VISION,
            max_tokens=300,
            reasoning_effort="none",  # modo directo, sin razonamiento interno
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_usuario},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{datos_b64}"},
                        },
                    ],
                },
            ],
        )
        return _parsear_respuesta(respuesta.choices[0].message.content)

    except Exception as e:
        print(f"  ⚠ Groq (imagen) falló: {e}")
        return None


def _parsear_respuesta(texto: str) -> dict | None:
    """
    Parsea el JSON que devuelve Groq y lo convierte a los campos
    que usa processor.py: anio, mes, consorcio, proveedor, ruc_proveedor, total.
    Tolerante a texto adicional alrededor del JSON (el modo JSON estricto de
    Groq no siempre es compatible con los modelos de visión).
    """
    try:
        texto_limpio = texto.strip().strip("`").strip()
        if texto_limpio.startswith("json"):
            texto_limpio = texto_limpio[4:].strip()

        try:
            datos = json.loads(texto_limpio)
        except json.JSONDecodeError:
            # Fallback: extraer el primer bloque {...} del texto, por si el
            # modelo agregó explicación antes o después del JSON.
            import re
            match = re.search(r"\{.*\}", texto_limpio, re.DOTALL)
            if not match:
                raise
            datos = json.loads(match.group(0))

        resultado = {
            "consorcio": datos.get("consorcio"),
            "proveedor": datos.get("proveedor"),
            "ruc_proveedor": datos.get("ruc_proveedor"),
            "total": datos.get("total"),
            "anio": None,
            "mes": None,
        }

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
        print(f"  ⚠ No se pudo parsear respuesta de Groq: {e}")
        print(f"  Respuesta recibida: {texto[:200]}")
        return None