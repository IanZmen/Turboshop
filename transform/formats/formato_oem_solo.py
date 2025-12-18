from __future__ import annotations
import re
import pandas as pd

from constants.formats import FORMAT_OEM_SOLO
from constants.output import DEFAULT_OUTPUT_FIELDS
from extract.oem_enrichment import enrich_oem_data
from transform.parsing_compatibilidades import (
    extraer_anios,
    extraer_motor_litros,
    extraer_codigo_motor,
    extraer_marca_modelo_flexible,
)
from transform.parsing_medidas import build_medida_fields, extraer_medidas


def procesar_formato_oem_solo(
    data_frame: pd.DataFrame, nombre_hoja: str, use_llm: bool
) -> pd.DataFrame:
    columnas = {str(column_name).strip().lower(): column_name for column_name in data_frame.columns}
    oem_series = data_frame[columnas["oem"]].astype("string").str.strip()

    rows = []
    for row_index in range(len(data_frame)):
        oem_code = (oem_series.iloc[row_index] or "").strip()
        if not oem_code:
            continue

        enrichment = enrich_oem_data(oem_code, use_llm)

        especificaciones_texto_enriquecidas = enrichment.get("repuesto_especificaciones_texto") if enrichment else None

        # Tomar dimensiones directas del LLM si vienen estructuradas; si no, extraer del texto
        dimensiones_llm = enrichment.get("dimensiones") if enrichment else None
        medidas: list[float | None] = []
        separador: str | None = None
        especificaciones_texto: str | None = None

        if dimensiones_llm:
            medidas = list(dimensiones_llm)[:4]
            separador = "X" if len(medidas) > 1 else None
        elif especificaciones_texto_enriquecidas:
            especificaciones_texto, medidas, separador = extraer_medidas(especificaciones_texto_enriquecidas)

        medida_fields = build_medida_fields(
            especificaciones_texto=especificaciones_texto,
            medidas=medidas,
            separador=separador,
        )

        compat_list = enrichment.get("compatibilidades") if enrichment else None
        compat_list = compat_list if isinstance(compat_list, list) else []

        if not compat_list:
            compat_list = [
                {
                    "compatibilidad_marca": enrichment.get("compatibilidad_marca") if enrichment else None,
                    "compatibilidad_modelo": enrichment.get("compatibilidad_modelo") if enrichment else None,
                    "compatibilidad_anio_desde": enrichment.get("compatibilidad_anio_desde") if enrichment else None,
                    "compatibilidad_anio_hasta": enrichment.get("compatibilidad_anio_hasta") if enrichment else None,
                    "compatibilidad_motor_litros": enrichment.get("compatibilidad_motor_litros") if enrichment else None,
                    "compatibilidad_codigo_motor": enrichment.get("compatibilidad_codigo_motor") if enrichment else None,
                    "compatibilidad_texto": enrichment.get("compatibilidad_texto") if enrichment else None,
                }
            ]

        if not compat_list:
            compat_list = [
                {
                    "compatibilidad_marca": None,
                    "compatibilidad_modelo": None,
                    "compatibilidad_anio_desde": None,
                    "compatibilidad_anio_hasta": None,
                    "compatibilidad_motor_litros": None,
                    "compatibilidad_codigo_motor": None,
                    "compatibilidad_texto": None,
                }
            ]

        def _int_or_none(val):
            try:
                return int(val) if val is not None else None
            except Exception:
                return None

        def _split_engine_codes(raw: Any) -> list[str | None]:
            if raw is None:
                return [None]
            if isinstance(raw, (int, float)):
                return [str(raw)]
            if not isinstance(raw, str):
                return [None]
            parts = [p.strip() for p in re.split(r"[;,|]", raw) if p.strip()]
            return parts or [None]

        def _split_variant_codes(raw_text: Any) -> list[str | None]:
            """
            Option details suelen venir como: '1NZFE; NCP91L-AGMRKA, NCP91L-AGMRKK'.
            Queremos una fila por cada cС©digo posterior al ';'.
            """
            if not isinstance(raw_text, str):
                return [None]
            if ";" not in raw_text:
                return [None]
            variant_part = raw_text.split(";", 1)[1]
            variants = [v.strip() for v in re.split(r"[;,|]", variant_part) if v.strip()]
            return variants or [None]

        for compat in compat_list:
            compat_texto = compat.get("compatibilidad_texto")
            compat_marca = compat.get("compatibilidad_marca")
            compat_modelo = compat.get("compatibilidad_modelo")
            compat_anio_desde = compat.get("compatibilidad_anio_desde")
            compat_anio_hasta = compat.get("compatibilidad_anio_hasta")
            compat_motor_litros = compat.get("compatibilidad_motor_litros")
            compat_codigo_motor = compat.get("compatibilidad_codigo_motor")

            if not compat_texto:
                parts = [compat_marca, compat_modelo]
                if compat_anio_desde or compat_anio_hasta:
                    if compat_anio_desde and compat_anio_hasta:
                        parts.append(f"{compat_anio_desde}-{compat_anio_hasta}")
                    elif compat_anio_desde:
                        parts.append(str(compat_anio_desde))
                    else:
                        parts.append(str(compat_anio_hasta))
                compat_texto = " ".join([p for p in parts if p]) or None

            # Completar campos faltantes desde compat_texto
            if compat_texto:
                if not compat_marca or not compat_modelo:
                    compat_marca, compat_modelo = extraer_marca_modelo_flexible(compat_texto)
                if compat_anio_desde is None and compat_anio_hasta is None:
                    compat_anio_desde, compat_anio_hasta = extraer_anios(compat_texto)
                if compat_motor_litros is None:
                    compat_motor_litros = extraer_motor_litros(compat_texto)
                if compat_codigo_motor is None:
                    compat_codigo_motor = extraer_codigo_motor(compat_texto)

            engine_codes = _split_engine_codes(compat_codigo_motor)
            variant_codes = _split_variant_codes(compat_texto)

            for engine_code in engine_codes:
                for variant_code in variant_codes:
                    compat_texto_final = compat_texto
                    if variant_code:
                        compat_texto_final = f"{compat_texto} | {variant_code}" if compat_texto else variant_code

                row = {
                    "repuesto_oem": oem_code,
                    "proveedor": nombre_hoja,
                    "formato_origen": FORMAT_OEM_SOLO,
                    "repuesto_sku": enrichment.get("repuesto_sku") if enrichment else None,
                    "repuesto_nombre": enrichment.get("repuesto_nombre") if enrichment else None,
                    "repuesto_especificaciones_texto": medida_fields.get("repuesto_especificaciones_texto"),
                    "compatibilidad_marca": compat_marca,
                    "compatibilidad_modelo": compat_modelo,
                    "compatibilidad_anio_desde": _int_or_none(compat_anio_desde),
                    "compatibilidad_anio_hasta": _int_or_none(compat_anio_hasta),
                    "compatibilidad_motor_litros": compat_motor_litros,
                    "compatibilidad_codigo_motor": engine_code,
                    "compatibilidad_texto": compat_texto_final,
                }

                row.update(medida_fields)

                final_row = {**DEFAULT_OUTPUT_FIELDS, **row}

                if enrichment:
                    links = enrichment.get("links_fuente") or []
                    if links:
                        final_row["paginas_de_informacion"] = " ; ".join(links)
                    elif enrichment.get("link_fuente"):
                        final_row["paginas_de_informacion"] = enrichment.get("link_fuente")

                final_row["uso_de_OPEN_AI"] = bool(use_llm and enrichment)

                rows.append(final_row)

    return pd.DataFrame(rows)
