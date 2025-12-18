from __future__ import annotations

from typing import Optional, Dict, Any, List

from utils.logging import get_logger

from extract.scrapping.sites.toyota_parts_deal import scrape_oem_data_in_toyota_parts_deal
from extract.OpenAI.oem_llm import buscar_oem_en_internet


logger = get_logger()


def _clean_str(val: Any) -> Optional[str]:
    if not isinstance(val, str):
        return None
    s = val.strip()
    return s or None


def _scrape_with_toyota_parts_deal(oem_code: str) -> Optional[Dict[str, Any]]:
    """
    Ejecuta scraping en ToyotaPartsDeal y adapta la salida al formato
    que consume el pipeline (mismo shape que el LLM).
    """

    try:
        scraped_rows: Optional[List[Dict[str, Any]]] = scrape_oem_data_in_toyota_parts_deal(oem_code)
    except Exception as scrape_error:
        logger.warning(f"[SCRAPING] Error ejecutando scraper ToyotaPartsDeal para OEM {oem_code}: {scrape_error}")
        return None

    if not scraped_rows:
        return None

    first_row = scraped_rows[0]

    compat_list: List[Dict[str, Any]] = []
    for scraped_row in scraped_rows:
        compat_list.append(
            {
                "compatibilidad_texto": _clean_str(scraped_row.get("compatibilidad_texto")),
                "compatibilidad_marca": _clean_str(scraped_row.get("compatibilidad_marca")),
                "compatibilidad_modelo": _clean_str(scraped_row.get("compatibilidad_modelo")),
                "compatibilidad_anio_desde": scraped_row.get("compatibilidad_anio_desde"),
                "compatibilidad_anio_hasta": scraped_row.get("compatibilidad_anio_hasta"),
                "compatibilidad_motor_litros": scraped_row.get("compatibilidad_motor_litros"),
                "compatibilidad_codigo_motor": _clean_str(scraped_row.get("compatibilidad_codigo_motor")),
            }
        )

    dimensiones: List[float] = []
    for key in ("repuesto_medida_1", "repuesto_medida_2", "repuesto_medida_3", "repuesto_medida_4"):
        raw_value = first_row.get(key)
        if isinstance(raw_value, (int, float)):
            dimensiones.append(float(raw_value))
    dimensiones = [dimension_value for dimension_value in dimensiones if dimension_value is not None]

    specs_text = _clean_str(first_row.get("repuesto_especificaciones_texto")) or ""
    dim_unidad = None
    lower_specs = specs_text.lower()
    if "inch" in lower_specs:
        dim_unidad = "in"
    elif "mm" in lower_specs:
        dim_unidad = "mm"
    elif "cm" in lower_specs:
        dim_unidad = "cm"

    link = _clean_str(first_row.get("paginas_de_informacion"))
    links = [link] if link else []

    return {
        "repuesto_sku": _clean_str(first_row.get("repuesto_sku")),
        "repuesto_nombre": _clean_str(first_row.get("repuesto_nombre")),
        "repuesto_especificaciones_texto": specs_text or None,
        "compatibilidad_texto": _clean_str(first_row.get("compatibilidad_texto")),
        "compatibilidad_marca": _clean_str(first_row.get("compatibilidad_marca")),
        "compatibilidad_modelo": _clean_str(first_row.get("compatibilidad_modelo")),
        "compatibilidad_anio_desde": first_row.get("compatibilidad_anio_desde"),
        "compatibilidad_anio_hasta": first_row.get("compatibilidad_anio_hasta"),
        "compatibilidad_motor_litros": first_row.get("compatibilidad_motor_litros"),
        "compatibilidad_codigo_motor": _clean_str(first_row.get("compatibilidad_codigo_motor")),
        "compatibilidades": compat_list or None,
        "dimensiones": dimensiones or None,
        "dimensiones_unidad": dim_unidad,
        "links_fuente": links,
        "link_fuente": link,
        "fuente": "toyotapartsdeal",
    }


def query_oem_with_llm(oem_code: str) -> Optional[Dict[str, Any]]:
    """
    Consulta a LLM/OpenAI para enriquecer datos de un OEM.
    Retorna None si no hay resultado usable o si ocurre un error.
    """

    try:
        logger.info(f"Consultando LLM para OEM '{oem_code}'...")
        result = buscar_oem_en_internet(oem_code)
        logger.info(f"Resultado LLM para OEM '{oem_code}': {result}")
        if not result or not isinstance(result, dict):
            return None
        return result
    except Exception as llm_error:
        logger.warning(f"LLM falló para OEM {oem_code}: {llm_error}")
        return None


def enrich_oem_data(oem_code: str, use_llm: bool) -> Optional[Dict[str, Any]]:
    """
    Intenta enriquecer:
    1) scraping (ToyotaPartsDeal)
    2) LLM (si use_llm=True)
    """
    scraping_result = _scrape_with_toyota_parts_deal(oem_code)
    if scraping_result:
        return scraping_result

    if use_llm:
        llm_result = query_oem_with_llm(oem_code)
        if llm_result:
            return llm_result

    return None
