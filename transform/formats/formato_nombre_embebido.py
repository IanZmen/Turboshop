from __future__ import annotations
import pandas as pd

from constants.formats import FORMAT_NOMBRE_EMBEBIDO
from constants.output import DEFAULT_OUTPUT_FIELDS
from transform.parsing_medidas import build_medida_fields, extraer_medidas
from transform.parsing_nombre_embebido import parse_compatibilidad_desde_nombre

def procesar_formato_nombre_embebido_a_tabla_unica(
    data_frame: pd.DataFrame, nombre_hoja: str
) -> pd.DataFrame:
    columnas = {str(column_name).strip().lower(): column_name for column_name in data_frame.columns}

    sku_series = data_frame[columnas["sku"]].astype("string").str.strip()
    repuesto_series = data_frame[columnas["repuesto"]].astype("string").str.strip()
    codigo_series = data_frame[columnas["codigo"]].astype("string").str.replace("\n", " ", regex=False).str.strip()

    rows = []
    for row_index in range(len(data_frame)):
        sku = (sku_series.iloc[row_index] or "").strip()
        nombre_repuesto = (repuesto_series.iloc[row_index] or "").strip()
        codigo_oem = (codigo_series.iloc[row_index] or "").strip()

        medidas_raw, medidas, separador_medidas = extraer_medidas(nombre_repuesto)
        medida_fields = build_medida_fields(medidas_raw, medidas, separador_medidas)

        compatibilidades = parse_compatibilidad_desde_nombre(nombre_repuesto)
        if not compatibilidades:
            compatibilidades = [{
                "compatibilidad_marca": None,
                "compatibilidad_modelo": None,
                "compatibilidad_anio_desde": None,
                "compatibilidad_anio_hasta": None,
                "compatibilidad_motor_litros": None,
                "compatibilidad_codigo_motor": None,
                "compatibilidad_texto": None
            }]

        for compat in compatibilidades:
            row = {
                "repuesto_oem": codigo_oem or None,
                "proveedor": nombre_hoja,
                "formato_origen": FORMAT_NOMBRE_EMBEBIDO,
                "repuesto_sku": sku or None,
                "repuesto_nombre": nombre_repuesto or None,
                "compatibilidad_marca": compat["compatibilidad_marca"],
                "compatibilidad_modelo": compat["compatibilidad_modelo"],
                "compatibilidad_anio_desde": compat["compatibilidad_anio_desde"],
                "compatibilidad_anio_hasta": compat["compatibilidad_anio_hasta"],
                "compatibilidad_motor_litros": compat["compatibilidad_motor_litros"],
                "compatibilidad_codigo_motor": compat["compatibilidad_codigo_motor"],
                "compatibilidad_texto": compat["compatibilidad_texto"],
            }
            row.update(medida_fields)
            row.update(DEFAULT_OUTPUT_FIELDS)
            rows.append(row)

    return pd.DataFrame(rows)
