from __future__ import annotations
import re
from typing import Optional, List, Tuple

from constants.vehicles import KNOWN_MAKES

# corta cuando empiezan especificaciones del repuesto (medidas, posiciones, etc.)
STOP_WORDS = {
    "DELANTERO","TRASERO","PLANO","PROFUNDIDAD","KIT","EMBRAGUE","DISCO","FRENO","OPTICO",
    "RADIADOR","BUJE","BANDEJA","SELLO","ANILLOS","CORREA","MOTOR"
}

YEAR4 = re.compile(r"\b(19\d{2}|20\d{2})\b")
RANGE_2D = re.compile(r"\b(\d{2})\s*-\s*(\d{2})\b")        # 08-11
RANGE_2D_OPEN = re.compile(r"\b(\d{2})\s*-\s*\b")          # 12-
RANGE_SLASH = re.compile(r"\b(\d{2,4})/(\d{2,4})\b")       # 1042/ ... (ojo: no siempre año)
LITERS = re.compile(r"\b(\d\.\d)\b")
ENGINE = re.compile(r"\b([A-Z]\d[A-Z0-9]{2,8})\b")

def _to_year4(year_token: str) -> Optional[int]:
    year_token = year_token.strip()
    if len(year_token) == 4:
        return int(year_token)
    if len(year_token) == 2:
        two_digit_year = int(year_token)
        return 2000 + two_digit_year if two_digit_year <= 30 else 1900 + two_digit_year
    return None

def extraer_anios_embebidos(texto: str) -> tuple[Optional[int], Optional[int]]:
    normalized_text = texto.upper()

    range_match = RANGE_2D.search(normalized_text)
    if range_match:
        year_start = _to_year4(range_match.group(1))
        year_end = _to_year4(range_match.group(2))
        return year_start, year_end

    range_open_match = RANGE_2D_OPEN.search(normalized_text)
    if range_open_match:
        year_start = _to_year4(range_open_match.group(1))
        return year_start, None

    year_match = YEAR4.search(normalized_text)
    if year_match:
        year_value = int(year_match.group(1))
        return year_value, year_value

    return None, None

def extraer_motor_y_codigo(texto: str) -> tuple[Optional[float], Optional[str]]:
    motor = None
    liters_match = LITERS.search(texto)
    if liters_match:
        try:
            motor = float(liters_match.group(1))
        except:
            motor = None

    codigo_motor = None
    engine_match = ENGINE.search(texto.upper())
    if engine_match:
        codigo_motor = engine_match.group(1)
    return motor, codigo_motor

def _clean_vehicle_text(raw_text: str) -> str:
    # normaliza separadores
    raw_text = raw_text.replace("﻿", "").replace("\n", " ").strip()
    raw_text = re.sub(r"\s+", " ", raw_text)
    return raw_text

def split_vehiculos_en_nombre(nombre: str) -> List[str]:
    """
    Separa por '/' cuando el string tiene pinta de múltiples vehículos.
    Ej: 'JAC URBAN HFC 1042/ISUZU NKR 3.1 ...' -> ['JAC URBAN HFC 1042', 'ISUZU NKR 3.1 ...']
    """
    if not nombre:
        return []

    normalized_vehicle_text = _clean_vehicle_text(nombre)

    # solo usar '/' como separador si aparece seguido de una marca conocida
    if "/" in normalized_vehicle_text:
        chunks = [
            chunk.strip()
            for chunk in normalized_vehicle_text.split("/")
            if chunk.strip()
        ]
        if len(chunks) >= 2:
            # si alguno empieza con marca conocida, lo aceptamos como split
            ok = any((chunk.split()[0].upper() in KNOWN_MAKES) for chunk in chunks if chunk.split())
            if ok:
                return chunks

    return [normalized_vehicle_text]

def parse_compatibilidad_desde_nombre(nombre: str) -> List[dict]:
    """
    Extrae 1+ compatibilidades desde el nombre del repuesto.
    Devuelve lista de dicts con compatibilidad_marca, compatibilidad_modelo, anios, motor, codigo_motor, compatibilidad_texto.
    """
    compatibility_records = []
    for vehicle_text in split_vehiculos_en_nombre(nombre):
        vehicle_text = _clean_vehicle_text(vehicle_text)
        vehicle_tokens = vehicle_text.split()
        if not vehicle_tokens:
            continue

        # Encontrar primera marca conocida en tokens
        marca_index = None
        for token_index, token_value in enumerate(vehicle_tokens):
            if token_value.upper() in KNOWN_MAKES:
                marca_index = token_index
                break

        if marca_index is None:
            # no hay marca: guardamos todo como texto y modelo None
            anio_desde, anio_hasta = extraer_anios_embebidos(vehicle_text)
            motor_litros, codigo_motor = extraer_motor_y_codigo(vehicle_text)
            compatibility_records.append({
                "compatibilidad_marca": None,
                "compatibilidad_modelo": None,
                "compatibilidad_anio_desde": anio_desde,
                "compatibilidad_anio_hasta": anio_hasta,
                "compatibilidad_motor_litros": motor_litros,
                "compatibilidad_codigo_motor": codigo_motor,
                "compatibilidad_texto": vehicle_text
            })
            continue

        marca = vehicle_tokens[marca_index].upper()

        # modelo: desde token siguiente hasta que aparezca año / motor / código motor / palabra stop
        modelo_tokens = []
        for token_value in vehicle_tokens[marca_index + 1:]:
            token_upper = token_value.upper()
            if token_upper in STOP_WORDS:
                break
            if (
                YEAR4.fullmatch(token_upper)
                or RANGE_2D.fullmatch(token_value)
                or RANGE_2D_OPEN.fullmatch(token_value)
                or LITERS.fullmatch(token_value)
                or ENGINE.fullmatch(token_upper)
            ):
                break
            # stop si llega otra marca (por seguridad)
            if token_upper in KNOWN_MAKES:
                break
            modelo_tokens.append(token_value)

        modelo = " ".join(modelo_tokens).strip().upper() if modelo_tokens else None

        anio_desde, anio_hasta = extraer_anios_embebidos(vehicle_text)
        motor_litros, codigo_motor = extraer_motor_y_codigo(vehicle_text)

        # rango abierto: si solo hay desde y no hay hasta, lo dejamos None
        compatibility_records.append({
            "compatibilidad_marca": marca,
            "compatibilidad_modelo": modelo,
            "compatibilidad_anio_desde": anio_desde,
            "compatibilidad_anio_hasta": anio_hasta,
            "compatibilidad_motor_litros": motor_litros,
            "compatibilidad_codigo_motor": codigo_motor,
            "compatibilidad_texto": vehicle_text
        })

    return compatibility_records
