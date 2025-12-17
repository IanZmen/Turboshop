from __future__ import annotations
import pandas as pd

from constants.formats import FORMAT_APLICACIONES
from constants.output import DEFAULT_OUTPUT_FIELDS
from transform.parsing_compatibilidades import (
    extraer_anios,
    extraer_motor_litros,
    extraer_codigo_motor,
    extraer_marca_modelo_flexible,
    split_aplicaciones_seguro,
)
from transform.parsing_medidas import build_medida_fields, extraer_medidas

def procesar_formato_aplicaciones(
    data_frame: pd.DataFrame, fuente_hoja: str
) -> pd.DataFrame:
    columnas = {str(column_name).strip().lower(): column_name for column_name in data_frame.columns}
    codigo_series = data_frame[columnas["codigo"]].astype("string").str.strip()
    descripcion_series = data_frame[columnas["descripcion"]].astype("string").str.strip()
    aplicaciones_series = data_frame[columnas["aplicaciones"]].astype("string").fillna("").str.strip()

    rows = []

    for row_index in range(len(data_frame)):
        codigo = (codigo_series.iloc[row_index] or "").strip()
        descripcion = (descripcion_series.iloc[row_index] or "").strip()
        aplicaciones = (aplicaciones_series.iloc[row_index] or "").strip()

        medidas_raw, medidas, separador_medidas = extraer_medidas(descripcion)
        medida_fields = build_medida_fields(medidas_raw, medidas, separador_medidas)

        aplicaciones_partes = split_aplicaciones_seguro(aplicaciones) or [None]

        for aplicacion in aplicaciones_partes:
            compatibilidad_marca = compatibilidad_modelo = None
            compatibilidad_anio_desde = compatibilidad_anio_hasta = None
            compatibilidad_motor_litros = None
            compatibilidad_codigo_motor = None
            compatibilidad_texto = None

            if aplicacion is not None:
                compatibilidad_texto = aplicacion
                compatibilidad_marca, compatibilidad_modelo = extraer_marca_modelo_flexible(aplicacion)
                compatibilidad_anio_desde, compatibilidad_anio_hasta = extraer_anios(aplicacion)
                compatibilidad_motor_litros = extraer_motor_litros(aplicacion)
                compatibilidad_codigo_motor = extraer_codigo_motor(aplicacion)

            row = {
                "proveedor": fuente_hoja,
                "formato_origen": FORMAT_APLICACIONES,
                "repuesto_sku": None,  # este proveedor no trae SKU
                "repuesto_oem": codigo or None,  # Supuesto: aquí CODIGO funciona como identificador
                "repuesto_nombre": descripcion or None,
                "compatibilidad_marca": compatibilidad_marca,
                "compatibilidad_modelo": compatibilidad_modelo,
                "compatibilidad_anio_desde": compatibilidad_anio_desde,
                "compatibilidad_anio_hasta": compatibilidad_anio_hasta,
                "compatibilidad_motor_litros": compatibilidad_motor_litros,
                "compatibilidad_codigo_motor": compatibilidad_codigo_motor,
                "compatibilidad_texto": compatibilidad_texto,
            }
            row.update(medida_fields)
            row.update(DEFAULT_OUTPUT_FIELDS)
            rows.append(row)

    output_table = pd.DataFrame(rows)

    # Tipos sugeridos (evita 2007.0)
    for compatibilidad_column in ["compatibilidad_anio_desde", "compatibilidad_anio_hasta"]:
        output_table[compatibilidad_column] = pd.to_numeric(output_table[compatibilidad_column], errors="coerce").astype("Int64")

    output_table["compatibilidad_motor_litros"] = pd.to_numeric(output_table["compatibilidad_motor_litros"], errors="coerce")

    return output_table
