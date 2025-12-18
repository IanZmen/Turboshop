from __future__ import annotations
from typing import Iterable
import pandas as pd


def order_columns_by_prefix(data_frame: pd.DataFrame, prefixes: Iterable[str]) -> pd.DataFrame:
    ordered_columns: list[str] = []
    seen = set()

    for prefix in prefixes:
        for column in data_frame.columns:
            if column.startswith(prefix) and column not in seen:
                ordered_columns.append(column)
                seen.add(column)

    for column in data_frame.columns:
        if column not in seen:
            ordered_columns.append(column)

    return data_frame.loc[:, ordered_columns]


def reorder_columns(data_frame: pd.DataFrame, priority_columns: Iterable[str]) -> pd.DataFrame:
    """
    Reordena columnas siguiendo una lista de prioridad; cualquier columna no incluida
    se agrega al final en su orden original.
    """
    priority = list(priority_columns)
    seen = set()
    ordered_columns: list[str] = []

    for column in priority:
        if column in data_frame.columns and column not in seen:
            ordered_columns.append(column)
            seen.add(column)

    for column in data_frame.columns:
        if column not in seen:
            ordered_columns.append(column)
            seen.add(column)

    return data_frame.loc[:, ordered_columns]
