from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from utils.logging import get_logger
from extract.scrapping.web_driver import WebDriverWrapper, ScraperConfig

import time as time_module

logger = get_logger()


# ------------------ Parsers ------------------

def _parse_dimensions(dim_text: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], int, str]:
    """
    Ej: "15.8 x 11.3 x 3.2 inches"
    Devuelve (dimension_1, dimension_2, dimension_3, dimension_4, cantidad, separador="X")
    """
    if not dim_text:
        return (None, None, None, None, 0, "")

    dimension_numbers = re.findall(r"\d+(?:\.\d+)?", dim_text)
    dimension_values: List[Optional[float]] = [float(number) for number in dimension_numbers[:4]]
    while len(dimension_values) < 4:
        dimension_values.append(None)

    dimension_count = len(dimension_numbers[:4])
    dimension_separator = "X" if dimension_count >= 2 else ""
    return (dimension_values[0], dimension_values[1], dimension_values[2], dimension_values[3], dimension_count, dimension_separator)


def _parse_year_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    year_range_match = re.search(r"(\d{4})\s*-\s*(\d{4})", text)
    if not year_range_match:
        return (None, None)
    try:
        return int(year_range_match.group(1)), int(year_range_match.group(2))
    except Exception:
        return (None, None)


def _parse_make_model(text: str) -> Tuple[Optional[str], Optional[str]]:
    # "2006-2011 Toyota Yaris" -> Toyota, Yaris
    cleaned = re.sub(r"^\s*\d{4}\s*-\s*\d{4}\s*", "", text).strip()
    parts = cleaned.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    if cleaned:
        return (None, cleaned)
    return (None, None)


def _parse_engine_liters(trim_engine: str) -> Optional[float]:
    # "RS, STD|4 Cyl 1.5L" -> 1.5
    liters_match = re.search(r"(\d+(?:\.\d+)?)\s*L\b", trim_engine)
    return float(liters_match.group(1)) if liters_match else None


def _parse_engine_code(option_details: str) -> Optional[str]:
    # "1NZFE; NCP91L-..." -> 1NZFE
    if not option_details:
        return None
    first = option_details.split(";")[0].strip()
    return first or None


def _clean_title_for_description(h1_text: str) -> str:
    # "Toyota 53383-52050 Hood To Cowl Top Seal" -> "Toyota 53383-52050 Hood To Cowl Top Seal"
    return (h1_text or "").strip()


# ------------------ DOM extractors ------------------

def _extract_specs_table(wd: WebDriverWrapper) -> Dict[str, str]:
    specs_table: Dict[str, str] = {}
    table_rows = wd.driver.find_elements(  # type: ignore
        By.CSS_SELECTOR,
        "li[data-id='Product Specifications'] table.pn-spec-list tbody tr"
    )
    for row in table_rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 2:
            key = (cells[0].text or "").strip()
            value = (cells[1].text or "").strip()
            if key:
                specs_table[key] = value
    return specs_table


def _extract_header(wd: WebDriverWrapper) -> Dict[str, str]:
    header_data: Dict[str, str] = {}

    heading_element = wd.driver.find_element(By.CSS_SELECTOR, "div.pn-detail.part-number-detail h1.pn-detail-h1")  # type: ignore
    header_data["heading_text"] = (heading_element.text or "").strip()

    try:
        strong_element = wd.driver.find_element(By.CSS_SELECTOR, "h1.pn-detail-h1 strong")  # type: ignore
        header_data["part_name"] = (strong_element.text or "").strip()
    except Exception:
        header_data["part_name"] = ""

    try:
        sub_description = wd.driver.find_element(By.CSS_SELECTOR, "div.pn-detail.part-number-detail p.pn-detail-sub-desc")  # type: ignore
        header_data["sub_desc"] = (sub_description.text or "").strip()
    except Exception:
        header_data["sub_desc"] = ""

    return header_data


def _extract_fitment_rows(wd: WebDriverWrapper) -> List[Dict[str, str]]:
    fitment_rows: List[Dict[str, str]] = []
    rows = wd.driver.find_elements(  # type: ignore
        By.CSS_SELECTOR,
        "li[data-id='Vehicle Fitment'] table.fit-vehicle-list-table tbody tr"
    )
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 3:
            fitment_rows.append(
                {
                    "year_make_model": (cells[0].text or "").strip(),
                    "trim_engine": (cells[1].text or "").strip(),
                    "option_details": (cells[2].text or "").strip(),
                }
            )
    return fitment_rows



# ------------------ Guards / Detection ------------------

def _vehicle_modal_is_open(wd: WebDriverWrapper) -> bool:
    """
    Detecta el modal de "Select Vehicle by Model/VIN".
    Si aparece, tu regla es: cerrar driver y devolver None.
    """
    if wd.driver is None:
        return False

    # Lo más estable: el contenedor .v-cm-content + texto “Select Vehicle”
    modal_elements = wd.driver.find_elements(By.CSS_SELECTOR, "div.v-cm-content")
    if not modal_elements:
        return False

    modal_text = (modal_elements[0].text or "").lower()
    return ("select vehicle" in modal_text) or ("enter the vin" in modal_text) or ("select vehicle by model" in modal_text)


def _wait_for_detail_or_vehicle_modal(wd: WebDriverWrapper) -> str:
    """
    Espera hasta que ocurra una de dos cosas:
    - aparezca el detalle del repuesto
    - aparezca el modal de vehículo

    Retorna: "detail" | "vehicle_modal" | "timeout"
    """
    wd._require_driver()

    wait_timeout_seconds = wd.config.wait_timeout
    # polling simple: usamos wait del wrapper para visibilidad/presencia,
    # pero como son dos condiciones, hacemos un loop corto.

    loop_start_time = time_module.time()

    while time_module.time() - loop_start_time < wait_timeout_seconds:
        # 1) modal vehículo
        if _vehicle_modal_is_open(wd):
            return "vehicle_modal"

        # 2) detalle repuesto
        try:
            if wd.driver.find_elements(By.CSS_SELECTOR, "div.pn-detail.part-number-detail"):  # type: ignore
                return "detail"
        except Exception:
            pass

        time_module.sleep(0.25)

    return "timeout"


# ------------------ Main scraper ------------------

def scrape_oem_data_in_toyota_parts_deal(oem_code: str) -> Optional[List[Dict[str, Any]]]:
    wd = WebDriverWrapper(
        ScraperConfig(
            headless=False,
            disable_images=False,
            human_delay_range=(1.5, 2.5),
        )
    )

    try:
        wd.initialize_driver()
        wd.load_page("https://www.toyotapartsdeal.com/")

        # 1) Buscar OEM
        search_input = wd.find_visible(By.CSS_SELECTOR, "input.ab-input-control")
        search_input.clear()
        search_input.send_keys(oem_code)
        wd.human_delay()
        search_input.send_keys(Keys.ENTER)
        
        wd.human_delay()
        wd.human_delay()
        wd.human_delay()
        wd.human_delay()

        # Esperar: detalle o modal
        state = _wait_for_detail_or_vehicle_modal(wd)

        if state == "vehicle_modal":
            logger.info(f"[TPD] Apareció modal de vehículo para OEM={oem_code}. Se devuelve None.")
            return None

        if state != "detail":
            logger.info(f"[TPD] No se encontró detalle (state={state}) para OEM={oem_code}. Se devuelve None.")
            return None

        wd.human_delay()
        wd.human_delay()
        wd.human_delay()
        wd.human_delay()

        # 2) Esperar página de detalle (si quedas en results, esto puede fallar -> lo arreglamos después si te pasa)
        wd.find_present(By.CSS_SELECTOR, "div.pn-detail.part-number-detail")
        wd.human_delay()

        # 3) Extraer
        url = wd.get_url()
        header_data = _extract_header(wd)
        specs_table = _extract_specs_table(wd)
        fitment_rows = _extract_fitment_rows(wd)

        # repuesto_nombre: preferimos el strong (limpio) y le agregamos Brand / Part Description si existen
        base_name = header_data.get("part_name") or header_data.get("heading_text") or ""
        brand_name = specs_table.get("Brand", "").strip()
        part_description = specs_table.get("Part Description", "").strip()
        name_parts = [part for part in [brand_name, base_name, part_description] if part]
        repuesto_nombre = " ".join(name_parts) or base_name

        # sku: si no existe, None (como pediste)
        repuesto_sku = specs_table.get("SKU")
        if repuesto_sku:
            repuesto_sku = repuesto_sku.strip() or None
        else:
            repuesto_sku = None

        # OEM: lo que buscaste (más confiable), pero si specs trae MPN lo puedes guardar si quieres
        repuesto_oem = oem_code

        # Dimensiones: parse y además incrustar en specs_text
        dimensions_text = (specs_table.get("Item Dimensions") or "").strip()
        dimension_1, dimension_2, dimension_3, dimension_4, dimension_count, dimension_separator = _parse_dimensions(dimensions_text)

        # Armar texto de especificaciones, incluyendo medidas dentro (como pediste)
        title_text = _clean_title_for_description(header_data.get("heading_text", ""))
        sub_desc = header_data.get("sub_desc", "")

        specs_lines = []
        if title_text:
            specs_lines.append(title_text)
        if sub_desc:
            specs_lines.append(sub_desc)

        # key-values (menos ruido: sin Shipping & Return con links)
        for key, value in specs_table.items():
            if key.lower().strip() == "shipping & return":
                continue
            specs_lines.append(f"{key}: {value}")

        # incrustar medidas explícitas al final (aunque ya estén como Item Dimensions)
        if dimension_count > 0:
            # ej: "DIMENSIONS_PARSED: 15.8X11.3X3.2 (inches)"
            dims_join = dimension_separator.join([str(dim) for dim in [dimension_1, dimension_2, dimension_3, dimension_4] if dim is not None])
            unit_hint = ""
            if "inch" in dimensions_text.lower():
                unit_hint = " inches"
            elif "cm" in dimensions_text.lower():
                unit_hint = " cm"
            specs_lines.append(f"DIMENSIONS_PARSED: {dims_join}{unit_hint}".strip())

        repuesto_especificaciones_texto = " | ".join([s for s in specs_lines if s]).strip(" |")

        # 4) Base row (sin proveedor ni formato_origen)
        base_row: Dict[str, Any] = {
            "repuesto_sku": repuesto_sku,
            "repuesto_oem": repuesto_oem,
            "proveedor": None,          # lo llena tu ETL según hoja (proveedor_3)
            "formato_origen": None,     # lo llena tu ETL (formato_oem_solo)
            "repuesto_nombre": repuesto_nombre,
            "repuesto_especificaciones_texto": repuesto_especificaciones_texto,
            "repuesto_medida_1": dimension_1,
            "repuesto_medida_2": dimension_2,
            "repuesto_medida_3": dimension_3,
            "repuesto_medida_4": dimension_4,
            "repuesto_cantidad_medidas": dimension_count,
            "repuesto_separador_medidas": dimension_separator,
            "uso_de_OPEN_AI": False,
            "paginas_de_informacion": url,
        }

        # 5) Compatibilidades (1 fila por fitment)
        if not fitment_rows:
            base_row.update(
                {
                    "compatibilidad_marca": None,
                    "compatibilidad_modelo": None,
                    "compatibilidad_anio_desde": None,
                    "compatibilidad_anio_hasta": None,
                    "compatibilidad_motor_litros": None,
                    "compatibilidad_codigo_motor": None,
                    "compatibilidad_texto": None,
                }
            )
            return [base_row]

        fitment_output: List[Dict[str, Any]] = []
        for fitment_row in fitment_rows:
            year_make_model_text = fitment_row["year_make_model"]
            trim_engine = fitment_row["trim_engine"]
            option_details = fitment_row["option_details"]

            year_from, year_to = _parse_year_range(year_make_model_text)
            make, model = _parse_make_model(year_make_model_text)
            liters = _parse_engine_liters(trim_engine)
            engine_code = _parse_engine_code(option_details)

            row = dict(base_row)
            row.update(
                {
                    "compatibilidad_marca": make,
                    "compatibilidad_modelo": model,
                    "compatibilidad_anio_desde": year_from,
                    "compatibilidad_anio_hasta": year_to,
                    "compatibilidad_motor_litros": liters,
                    "compatibilidad_codigo_motor": engine_code,
                    "compatibilidad_texto": f"{year_make_model_text} | {trim_engine} | {option_details}".strip(" |"),
                }
            )
            fitment_output.append(row)
        logger.info(fitment_output)
        return fitment_output

    except Exception as e:
        logger.warning(f"[TPD] Error: {type(e).__name__}: {e}")
        return None
    finally:
        try:
            wd.quit_driver()
        except Exception:
            pass


if __name__ == "__main__":
    rows = scrape_oem_data_in_toyota_parts_deal("53410-12480")
    if rows:
        logger.info(f"filas retornadas: {len(rows)}")
        logger.info(rows[0])
