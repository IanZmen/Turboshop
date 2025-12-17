from __future__ import annotations
from pathlib import Path
import pandas as pd

def write_output(
    data_frame: pd.DataFrame, output_dir: Path, output_format: str = "csv"
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format == "csv":
        output_path = output_dir / "catalog_unificado.csv"
        data_frame.to_csv(output_path, index=False)
        return output_path

    if output_format == "parquet":
        output_path = output_dir / "catalog_unificado.parquet"
        data_frame.to_parquet(output_path, index=False)
        return output_path

    if output_format == "json":
        output_path = output_dir / "catalog_unificado.json"
        data_frame.to_json(output_path, orient="records", force_ascii=False)
        return output_path

    if output_format in ("xlsx", "excel"):
        output_path = output_dir / "catalog_unificado.xlsx"
        data_frame.to_excel(output_path, index=False)
        return output_path

    raise ValueError(f"Formato no soportado: {output_format}")
