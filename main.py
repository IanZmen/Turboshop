from __future__ import annotations
import os
from pathlib import Path
import pandas as pd

from config import ETLConfig
from utils.logging import get_logger
from extract.excel_reader import read_all_sheets
from detect.format_detector import detectar_formato
from transform.formats.formato_completo import procesar_formato_completo_a_tabla_unica
from load.writer import write_output

logger = get_logger()

def run(cfg: ETLConfig) -> Path:
    sheets = read_all_sheets(cfg.input_path)
    outputs: list[pd.DataFrame] = []

    for sheet in sheets:
        match = detectar_formato(sheet.df)
        if not match:
            logger.info(f"Hoja '{sheet.sheet_name}' ignorada por ahora. Columnas={list(sheet.df.columns)}")
            continue

        if match.format_key == "formato_completo":
            logger.info(f"Hoja '{sheet.sheet_name}' -> {match.format_key}")
            outputs.append(procesar_formato_completo_a_tabla_unica(sheet.df, sheet.sheet_name))

    if not outputs:
        raise RuntimeError("No se generó salida.")

    final_df = pd.concat(outputs, ignore_index=True)

    # ejemplo: quitar duplicados exactos
    final_df = final_df.drop_duplicates()

    # aquí sí: un solo archivo, el formato lo decide cfg
    out_path = write_output(final_df, cfg.output_dir, fmt=cfg.output_format)
    logger.info(f"Salida final generada: {out_path}")
    return out_path

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = ETLConfig(
        input_path=Path(os.path.join(base_dir, "ArchivosIniciales", "datos_tarea_reclutamiento.xlsx")),
        output_dir=Path(os.path.join(base_dir, "out")),
        output_format="xlsx",
    )
    run(cfg)
