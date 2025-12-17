from __future__ import annotations
import os
from pathlib import Path
import pandas as pd

from config import ETLConfig
from constants.formats import (
    FORMAT_APLICACIONES,
    FORMAT_COMPLETO,
    FORMAT_NOMBRE_EMBEBIDO,
)
from detect.format_detector import detectar_formato
from extract.excel_reader import read_all_sheets
from load.writer import write_output
from transform.formats.formato_aplicaciones import procesar_formato_aplicaciones
from transform.formats.formato_completo import procesar_formato_completo_a_tabla_unica
from transform.formats.formato_nombre_embebido import (
    procesar_formato_nombre_embebido_a_tabla_unica,
)
from utils.dataframe import order_columns_by_prefix
from utils.logging import get_logger

logger = get_logger()

PROCESSORS = {
    FORMAT_COMPLETO: procesar_formato_completo_a_tabla_unica,
    FORMAT_APLICACIONES: procesar_formato_aplicaciones,
    FORMAT_NOMBRE_EMBEBIDO: procesar_formato_nombre_embebido_a_tabla_unica,
}

def run(config: ETLConfig) -> Path:
    sheet_data_list = read_all_sheets(config.input_path)
    processed_outputs: list[pd.DataFrame] = []

    for sheet_data in sheet_data_list:
        detected_format = detectar_formato(sheet_data.data_frame)

        if not detected_format:
            logger.info(
                f"Hoja '{sheet_data.sheet_name}' ignorada. "
                f"Columnas detectadas={list(sheet_data.data_frame.columns)}"
            )
            continue

        processor = PROCESSORS.get(detected_format.format_key)
        if not processor:
            logger.warning(
                f"Formato detectado pero sin processor: {detected_format.format_key} "
                f"(Hoja={sheet_data.sheet_name})"
            )
            continue

        logger.info(
            f"Procesando hoja '{sheet_data.sheet_name}' "
            f"con formato='{detected_format.format_key}' ({detected_format.reason})"
        )

        processed_data_frame = processor(sheet_data.data_frame, sheet_data.sheet_name)
        processed_outputs.append(processed_data_frame)

    if not processed_outputs:
        raise RuntimeError("No se generó ninguna salida procesable.")

    unified_data_frame = pd.concat(processed_outputs, ignore_index=True)

    # quitar duplicados exactos (misma compatibilidad + mismo repuesto)
    unified_data_frame = unified_data_frame.drop_duplicates()

    unified_data_frame = order_columns_by_prefix(unified_data_frame, prefixes=("repuesto_", "compatibilidad_"))

    output_path = write_output(
        unified_data_frame,
        config.output_dir,
        output_format=config.output_format
    )

    logger.info(f"Salida final generada: {output_path}")
    logger.info(f"Filas totales: {len(unified_data_frame)}")

    return output_path


if __name__ == "__main__":
    base_directory = os.path.dirname(os.path.abspath(__file__))
    config = ETLConfig(
        input_path=Path(os.path.join(base_directory, "ArchivosIniciales", "datos_tarea_reclutamiento.xlsx")),
        output_dir=Path(os.path.join(base_directory, "out")),
        output_format="xlsx",
    )
    run(config)
