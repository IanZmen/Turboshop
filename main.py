from __future__ import annotations
from pathlib import Path

from config import ETLConfig
from utils.logging import get_logger
from extract.excel_reader import read_all_sheets

logger = get_logger()


def run_etl(cfg: ETLConfig) -> None:
    sheets = read_all_sheets(cfg.input_path)

    logger.info(f"Se encontraron {len(sheets)} hojas en el archivo\n")

    for sheet in sheets:
        logger.info("=" * 60)
        logger.info(f"Hoja: {sheet.sheet_name}")
        logger.info(f"Columnas: {list(sheet.df.columns)}")
        logger.info("Primeras filas:")
        logger.info(f"\n{sheet.df.head()}\n")

if __name__ == "__main__":
    cfg = ETLConfig(
        input_path=Path("ArchivosIniciales/datos_tarea_reclutamiento.xlsx"),
        output_dir=Path("out"),
        output_format="csv",
    )
    run_etl(cfg)
