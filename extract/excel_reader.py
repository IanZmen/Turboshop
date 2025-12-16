from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

@dataclass(frozen=True)
class SheetData:
    sheet_name: str
    df: pd.DataFrame

def read_all_sheets(path: Path) -> list[SheetData]:
    # Lee todas las hojas como dict: {sheet_name: df}
    sheets = pd.read_excel(path, sheet_name=None, dtype=str)  # todo como str para no perder info
    out: list[SheetData] = []
    for sheet_name, df in sheets.items():
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        out.append(SheetData(sheet_name=sheet_name, df=df))
    return out
