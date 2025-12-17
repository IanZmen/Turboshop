from __future__ import annotations
import pandas as pd

from constants.formats import FORMAT_COMPLETO
from constants.output import DEFAULT_OUTPUT_FIELDS
from transform.delete_0 import limpiar_ceros_modelo_texto
from transform.parsing_compatibilidades import (
    extraer_anios,
    extraer_motor_litros,
    extraer_codigo_motor,
    extraer_marca_modelo_flexible,
)
from transform.parsing_medidas import build_medida_fields, extraer_medidas


def procesar_formato_completo_a_tabla_unica(
    data_frame: pd.DataFrame, nombre_hoja: str
) -> pd.DataFrame:
    columnas = {str(column_name).strip().lower(): column_name for column_name in data_frame.columns}

    sku_series = data_frame[columnas["sku"]].astype("string").str.strip()
    oem_series = data_frame[columnas["oem"]].astype("string").str.strip()
    repuesto_series = data_frame[columnas["repuesto"]].astype("string").str.strip()
    compatibilidad_series = data_frame[columnas["compatibilidades"]].astype("string").fillna("").str.strip()

    rows = []
    for row_index in range(len(data_frame)):
        sku = (sku_series.iloc[row_index] or "").strip()
        oem = (oem_series.iloc[row_index] or "").strip()
        nombre_rep = (repuesto_series.iloc[row_index] or "").strip()
        compatibilidad_raw = (compatibilidad_series.iloc[row_index] or "").strip()

        compatibilidad_parts = [part.strip() for part in compatibilidad_raw.split(",") if part.strip()] or [None]

        especificaciones_raw, medidas, separador_medidas = extraer_medidas(nombre_rep)
        medida_fields = build_medida_fields(especificaciones_raw, medidas, separador_medidas)

        for compatibilidad_texto in compatibilidad_parts:
            compatibilidad_marca = compatibilidad_modelo = None
            compatibilidad_anio_desde = compatibilidad_anio_hasta = None
            compatibilidad_motor_litros = None
            compatibilidad_codigo_motor = None
            texto_compatibilidad = None

            if compatibilidad_texto is not None:
                texto_compatibilidad = compatibilidad_texto
                compatibilidad_marca, compatibilidad_modelo = extraer_marca_modelo_flexible(compatibilidad_texto)
                compatibilidad_anio_desde, compatibilidad_anio_hasta = extraer_anios(compatibilidad_texto)
                compatibilidad_motor_litros = extraer_motor_litros(compatibilidad_texto)
                compatibilidad_codigo_motor = extraer_codigo_motor(compatibilidad_texto)
                if compatibilidad_anio_desde and compatibilidad_anio_hasta is None:
                    compatibilidad_anio_hasta = compatibilidad_anio_desde

                compatibilidad_modelo = limpiar_ceros_modelo_texto(compatibilidad_modelo)

            row = {
                "repuesto_oem": oem or None,
                "proveedor": nombre_hoja,
                "formato_origen": FORMAT_COMPLETO,
                "repuesto_sku": sku or None,
                "repuesto_nombre": nombre_rep or None,
                "compatibilidad_marca": compatibilidad_marca,
                "compatibilidad_modelo": compatibilidad_modelo,
                "compatibilidad_anio_desde": compatibilidad_anio_desde,
                "compatibilidad_anio_hasta": compatibilidad_anio_hasta,
                "compatibilidad_motor_litros": compatibilidad_motor_litros,
                "compatibilidad_codigo_motor": compatibilidad_codigo_motor,
                "compatibilidad_texto": texto_compatibilidad,
            }
            row.update(medida_fields)
            row.update(DEFAULT_OUTPUT_FIELDS)
            rows.append(row)

    output_table = pd.DataFrame(rows)
    return output_table
