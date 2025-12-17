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
