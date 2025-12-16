from __future__ import annotations
from pathlib import Path
import pandas as pd

def write_output(df: pd.DataFrame, output_dir: Path, fmt: str = "csv") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        out_path = output_dir / "catalog_unificado.csv"
        df.to_csv(out_path, index=False)
        return out_path

    if fmt == "parquet":
        out_path = output_dir / "catalog_unificado.parquet"
        df.to_parquet(out_path, index=False)
        return out_path

    if fmt == "json":
        out_path = output_dir / "catalog_unificado.json"
        df.to_json(out_path, orient="records", force_ascii=False)
        return out_path

    if fmt in ("xlsx", "excel"):
        out_path = output_dir / "catalog_unificado.xlsx"
        df.to_excel(out_path, index=False)
        return out_path

    raise ValueError(f"Formato no soportado: {fmt}")
