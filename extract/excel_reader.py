from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

@dataclass(frozen=True)
class SheetData:
    sheet_name: str
    data_frame: pd.DataFrame

def read_all_sheets(path: Path) -> list[SheetData]:
    sheets = pd.read_excel(path, sheet_name=None, dtype=str)  # todo como str para no perder info
    sheet_data_list: list[SheetData] = []
    for sheet_name, data_frame in sheets.items():
        data_frame = data_frame.copy()
        data_frame.columns = [str(column_name).strip() for column_name in data_frame.columns]
        sheet_data_list.append(SheetData(sheet_name=sheet_name, data_frame=data_frame))
    return sheet_data_list
