from __future__ import annotations

import json
import textwrap
from typing import Optional, Dict, Any, List

from openai import OpenAI

from utils.env import load_env, get_env
from utils.logging import get_logger

logger = get_logger()

# Carga .env y API key
load_env()
api_key = get_env("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY no encontrada en .env")

client = OpenAI(api_key=api_key)


def _extract_first_json_object(text: str) -> Optional[dict]:
    """
    Extrae el primer objeto JSON válido desde un string.
    Ignora cualquier texto antes o después.
    """
    try:
        start = text.find("{")
        if start == -1:
            return None

        brace_count = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                brace_count += 1
            elif text[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    json_str = text[start : i + 1]
                    return json.loads(json_str)
        return None
    except Exception:
        return None


def _normalize_links(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    normalized_links: List[str] = []
    for raw_link in value:
        if isinstance(raw_link, str):
            trimmed_link = raw_link.strip()
            if trimmed_link:
                normalized_links.append(trimmed_link)
    # dedupe manteniendo orden
    seen_links = set()
    deduped_links: List[str] = []
    for link in normalized_links:
        if link not in seen_links:
            deduped_links.append(link)
            seen_links.add(link)
    return deduped_links


def _clean_str(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    s = value.strip()
    return s or None


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return None


def buscar_oem_en_internet(oem: str) -> Optional[Dict[str, Any]]:
    """
    Busca info del OEM usando OpenAI + web_search_preview.
    Retorna dict con:
      - repuesto_nombre / repuesto_especificaciones_texto
      - compatibilidad_texto + campos desglosados (marca/modelo/años/motor)
      - links_fuente (lista) y link_fuente (primer enlace)
    Retorna None si no hay nada útil o si ocurre un error.
    """
    oem = oem.strip()
    if not oem:
        return None
    prompt = textwrap.dedent(
        """
        Busca en internet qu? repuesto corresponde al c?digo OEM: "{oem}".

        Responde SOLO con un JSON v?lido (sin texto extra) con estas claves:
        {{
          "repuesto_nombre": "string|null",
          "repuesto_especificaciones_texto": "string|null",
          "compatibilidad_texto": "string|null",   // resumen libre de compatibilidades
          "compatibilidades": [
            {{
              "compatibilidad_texto": "string|null",
              "compatibilidad_marca": "string|null",
              "compatibilidad_modelo": "string|null",
              "compatibilidad_anio_desde": "number|null",
              "compatibilidad_anio_hasta": "number|null",
              "compatibilidad_motor_litros": "number|null",
              "compatibilidad_codigo_motor": "string|null"
            }}
          ],
          "dimensiones": "number[]|null",          // usa mm si puedes; si vienen en pulgadas, aclara en especificaciones
          "dimensiones_unidad": "string|null",     // ej. "mm" o "in"
          "links_fuente": "string[]"   // puede ser []
        }}

        Reglas (se breve):
        - Usa solo datos expl?citos de las fuentes. No inventes ni completes con conjeturas.
        - Si hay varias p?ginas ?tiles, agrega varias en links_fuente.
        - Si hay varias compatibilidades (varios modelos/motores/a?os), usa el array "compatibilidades".
        - Si algo no est? expl?cito, usa null.
        - No incluyas explicaciones ni texto fuera del JSON.
        """
    ).format(oem=oem)

    try:
        response = client.responses.create(
            model="gpt-4.1",
            input=prompt,
            tools=[{"type": "web_search_preview"}],
        )
    except Exception as api_error:
        logger.warning(f"OpenAI call falló para OEM {oem}: {api_error}")
        return None

    raw_output_text = (response.output_text or "").strip()
    logger.info(f"LLM raw text for OEM '{oem}': {raw_output_text}")

    parsed_data = _extract_first_json_object(raw_output_text)
    if not parsed_data:
        logger.warning(f"No se pudo extraer JSON válido para OEM {oem}")
        return None

    links = _normalize_links(parsed_data.get("links_fuente"))
    compat_text = _clean_str(parsed_data.get("compatibilidad_texto"))

    raw_dimensions = parsed_data.get("dimensiones") if isinstance(parsed_data.get("dimensiones"), list) else []
    parsed_dimensions: list[float] = []
    if raw_dimensions:
        for raw_value in raw_dimensions:
            dimension_value = _to_float(raw_value)
            if dimension_value is not None and dimension_value < 5000:  # evita números absurdos
                parsed_dimensions.append(dimension_value)

    raw_compatibilities = parsed_data.get("compatibilidades") if isinstance(parsed_data.get("compatibilidades"), list) else []
    compat_list: list[dict[str, Any]] = []
    for compat_item in raw_compatibilities:
        if not isinstance(compat_item, dict):
            continue
        compat_list.append(
            {
                "compatibilidad_texto": _clean_str(compat_item.get("compatibilidad_texto")),
                "compatibilidad_marca": _clean_str(compat_item.get("compatibilidad_marca")),
                "compatibilidad_modelo": _clean_str(compat_item.get("compatibilidad_modelo")),
                "compatibilidad_anio_desde": _to_int(compat_item.get("compatibilidad_anio_desde")),
                "compatibilidad_anio_hasta": _to_int(compat_item.get("compatibilidad_anio_hasta")),
                "compatibilidad_motor_litros": _to_float(compat_item.get("compatibilidad_motor_litros")),
                "compatibilidad_codigo_motor": _clean_str(compat_item.get("compatibilidad_codigo_motor")),
            }
        )

    base_compatibility = compat_list[0] if compat_list else {}

    result: Dict[str, Any] = {
        "repuesto_nombre": _clean_str(parsed_data.get("repuesto_nombre")),
        "repuesto_especificaciones_texto": _clean_str(parsed_data.get("repuesto_especificaciones_texto")),
        "compatibilidad_texto": compat_text,
        "compatibilidad_marca": _clean_str(parsed_data.get("compatibilidad_marca")) or base_compatibility.get("compatibilidad_marca"),
        "compatibilidad_modelo": _clean_str(parsed_data.get("compatibilidad_modelo")) or base_compatibility.get("compatibilidad_modelo"),
        "compatibilidad_anio_desde": _to_int(parsed_data.get("compatibilidad_anio_desde")) or base_compatibility.get("compatibilidad_anio_desde"),
        "compatibilidad_anio_hasta": _to_int(parsed_data.get("compatibilidad_anio_hasta")) or base_compatibility.get("compatibilidad_anio_hasta"),
        "compatibilidad_motor_litros": _to_float(parsed_data.get("compatibilidad_motor_litros")) or base_compatibility.get("compatibilidad_motor_litros"),
        "compatibilidad_codigo_motor": _clean_str(parsed_data.get("compatibilidad_codigo_motor")) or base_compatibility.get("compatibilidad_codigo_motor"),
        "compatibilidades": compat_list if compat_list else None,
        "dimensiones": parsed_dimensions if parsed_dimensions else None,
        "dimensiones_unidad": _clean_str(parsed_data.get("dimensiones_unidad")),
        "links_fuente": links,
        "link_fuente": links[0] if links else None,
        "fuente": "openai",
    }

    # si no encontró nada útil
    if (
        result["repuesto_nombre"] is None
        and result["repuesto_especificaciones_texto"] is None
        and result["compatibilidad_texto"] is None
        and not result["links_fuente"]
    ):
        return None

    return result
