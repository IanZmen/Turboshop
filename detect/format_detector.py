from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pandas as pd

def _norm(c: str) -> str:
    return str(c).strip().lower()

@dataclass(frozen=True)
class FormatMatch:
    format_key: str
    reason: str

def detectar_formato(df: pd.DataFrame) -> Optional[FormatMatch]:
    cols = {_norm(c) for c in df.columns}

    if {"sku", "oem", "compatibilidades", "repuesto"}.issubset(cols):
        return FormatMatch("formato_completo", "SKU+OEM+COMPATIBILIDADES+REPUESTO")

    return None

