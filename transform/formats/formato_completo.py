from __future__ import annotations
import hashlib
import pandas as pd

from transform.parsing_medidas import extraer_medidas

from transform.parsing_compatibilidades import (
    extraer_anios, extraer_motor_litros, extraer_codigo_motor, extraer_marca_modelo
)

def _id_repuesto(proveedor: str, sku: str, oem: str, nombre: str) -> str:
    base = f"{proveedor}|{sku}|{oem}|{nombre}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]

def procesar_formato_completo_a_tabla_unica(df: pd.DataFrame, nombre_hoja: str) -> pd.DataFrame:
    cols = {str(c).strip().lower(): c for c in df.columns}

    sku_s = df[cols["sku"]].astype("string").str.strip()
    oem_s = df[cols["oem"]].astype("string").str.strip()
    rep_s = df[cols["repuesto"]].astype("string").str.strip()
    comp_s = df[cols["compatibilidades"]].astype("string").fillna("").str.strip()

    rows = []
    for i in range(len(df)):
        sku = (sku_s.iloc[i] or "").strip()
        oem = (oem_s.iloc[i] or "").strip()
        nombre_rep = (rep_s.iloc[i] or "").strip()
        compat_raw = (comp_s.iloc[i] or "").strip()

        rid = _id_repuesto(nombre_hoja, sku, oem, nombre_rep)

        # si no hay compatibilidades, igual dejamos una fila con campos compat vacíos
        partes = [p.strip() for p in compat_raw.split(",") if p.strip()] or [None]

        for p in partes:
            marca = modelo = None
            anio_desde = anio_hasta = None
            motor_litros = None
            codigo_motor = None
            texto_compat = None

            if p is not None:
                texto_compat = p
                marca, modelo = extraer_marca_modelo(p)
                anio_desde, anio_hasta = extraer_anios(p)
                motor_litros = extraer_motor_litros(p)
                codigo_motor = extraer_codigo_motor(p)
                # si solo se detecta año de inicio, asumimos rango cerrado en el mismo año
                if anio_desde and anio_hasta is None:
                    anio_hasta = anio_desde

            medidas_raw, vals, sep = extraer_medidas(nombre_rep)

            # relleno fijo a 4 columnas
            m1 = vals[0] if len(vals) > 0 else None
            m2 = vals[1] if len(vals) > 1 else None
            m3 = vals[2] if len(vals) > 2 else None
            m4 = vals[3] if len(vals) > 3 else None

            # si no hay especificaciones_texto, al menos guardamos lo raw encontrado
            especificaciones_texto = medidas_raw

            rows.append({
                # trazabilidad
                "id_repuesto": rid,
                "proveedor": nombre_hoja,
                "formato_origen": "formato_completo",

                # repuesto
                "repuesto_sku": sku or None,
                "repuesto_oem": oem or None,
                "repuesto_nombre": nombre_rep or None,
                "repuesto_especificaciones_texto": especificaciones_texto,
                "repuesto_medida_1": m1,
                "repuesto_medida_2": m2,
                "repuesto_medida_3": m3,
                "repuesto_medida_4": m4,
                "repuesto_cantidad_medidas": len(vals) if vals else 0,
                "repuesto_separador_medidas": sep,

                # compatibilidad
                "compat_marca": marca,
                "compat_modelo": modelo,
                "compat_anio_desde": anio_desde,
                "compat_anio_hasta": anio_hasta,
                "compat_motor_litros": motor_litros,
                "compat_codigo_motor": codigo_motor,
                "compat_texto": texto_compat,
            })

    out = pd.DataFrame(rows)
    return out
