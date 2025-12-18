from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pandas as pd

from constants.formats import (
    FORMAT_APLICACIONES,
    FORMAT_COMPLETO,
    FORMAT_NOMBRE_EMBEBIDO,
    FORMAT_OEM_SOLO,
)

FORMAT_COLUMN_RULES = {
    FORMAT_COMPLETO: {"sku", "oem", "compatibilidades", "repuesto"},
    FORMAT_APLICACIONES: {"codigo", "descripcion", "aplicaciones"},
    FORMAT_NOMBRE_EMBEBIDO: {"sku", "repuesto", "codigo"},
    FORMAT_OEM_SOLO: {"oem"},
}


def _normalize_column_name(column_name: str) -> str:
    return str(column_name).strip().lower()

@dataclass(frozen=True)
class FormatMatch:
    format_key: str
    reason: str

def detectar_formato(data_frame: pd.DataFrame) -> Optional[FormatMatch]:
    normalized_columns = {_normalize_column_name(column) for column in data_frame.columns}

    if FORMAT_COLUMN_RULES[FORMAT_COMPLETO].issubset(normalized_columns):
        return FormatMatch(
            format_key=FORMAT_COMPLETO,
            reason="Columnas SKU+OEM+COMPATIBILIDADES+REPUESTO"
        )

    if FORMAT_COLUMN_RULES[FORMAT_APLICACIONES].issubset(normalized_columns):
        return FormatMatch(
            format_key=FORMAT_APLICACIONES,
            reason="Columnas CODIGO+DESCRIPCION+APLICACIONES"
        )

    if FORMAT_COLUMN_RULES[FORMAT_NOMBRE_EMBEBIDO].issubset(normalized_columns):
        return FormatMatch(
            format_key=FORMAT_NOMBRE_EMBEBIDO,
            reason="Columnas SKU+REPUESTO+CODIGO (compatibilidad en nombre)"
        )

    if normalized_columns == FORMAT_COLUMN_RULES[FORMAT_OEM_SOLO]:
        return FormatMatch(
            format_key=FORMAT_OEM_SOLO,
            reason="Solo columna OEM"
        )

    return None
