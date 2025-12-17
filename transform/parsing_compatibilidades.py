from __future__ import annotations
import re
from typing import Optional, Tuple

from constants.vehicles import KNOWN_MAKES

YEAR4 = re.compile(r"\b(19\d{2}|20\d{2})\b")
LITERS = re.compile(r"\b(\d(?:\.\d){1,2})\s*(LTS?|L)?\b", re.IGNORECASE)

RANGE_2DIGIT = re.compile(r"\b(\d{2})\s*[-/]\s*(\d{2})\b")
RANGE_4DIGIT = re.compile(r"\b(19\d{2}|20\d{2})\s*[-/]\s*(19\d{2}|20\d{2})\b")
GENERIC_RANGE = re.compile(r"\b(\d{2,4})\s*[-/]\s*(\d{2,4})\b")
ON_PATTERN = re.compile(r"\b(\d{2}|19\d{2}|20\d{2})\s*ON\b", re.IGNORECASE)

MEASURE_BLOCK = re.compile(r"\d+(?:[.,]\d+)?(?:\s*[xX\*\u00D7]\s*\d+(?:[.,]\d+)?)+")
DECIMALS = re.compile(r"\b\d+\.\d+\b")

STOP_WORDS = {
    "MOBIS","EXEDY","NPR","RIK","LUK","GENUIN","GENUINE","KOREA","CHINA","STD","OEM","ORIGINAL"
}

TOKEN = re.compile(r"\b[A-Z0-9]{2,12}\b")
HAS_LETTER = re.compile(r"[A-Z]")
HAS_DIGIT = re.compile(r"\d")


def _to_year_4(year_token: str) -> Optional[int]:
    year_token = year_token.strip()
    if len(year_token) == 4:
        return int(year_token)
    if len(year_token) == 2:
        two_digit_year = int(year_token)
        return 2000 + two_digit_year if two_digit_year <= 30 else 1900 + two_digit_year
    return None


def extraer_anios(texto: str) -> Tuple[Optional[int], Optional[int]]:
    normalized_text = texto.upper()
    normalized_text = MEASURE_BLOCK.sub(" ", normalized_text)
    normalized_text = DECIMALS.sub(" ", normalized_text)

    range_match = RANGE_4DIGIT.search(normalized_text)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))

    range_match = RANGE_2DIGIT.search(normalized_text)
    if range_match:
        return _to_year_4(range_match.group(1)), _to_year_4(range_match.group(2))

    range_match = GENERIC_RANGE.search(normalized_text)
    if range_match:
        return _to_year_4(range_match.group(1)), _to_year_4(range_match.group(2))

    on_match = ON_PATTERN.search(normalized_text)
    if on_match:
        return _to_year_4(on_match.group(1)), None

    year_match = YEAR4.search(normalized_text)
    if year_match:
        year_value = int(year_match.group(1))
        return year_value, year_value

    return None, None


def extraer_motor_litros(texto: str) -> Optional[float]:
    liters_match = LITERS.search(texto)
    if not liters_match:
        return None
    liters_value = float(liters_match.group(1))
    if liters_value < 0.8 or liters_value > 8.0:
        return None
    return liters_value


def extraer_codigo_motor(texto: str) -> Optional[str]:
    normalized_text = texto.upper()
    candidates = []
    for token in TOKEN.findall(normalized_text):
        if token in KNOWN_MAKES or token in STOP_WORDS:
            continue
        if not HAS_LETTER.search(token) or not HAS_DIGIT.search(token):
            continue
        if token.isdigit():
            continue
        candidates.append(token)

    if not candidates:
        return None

    candidates.sort(key=lambda token: (-(len(token)), -sum(ch.isdigit() for ch in token)))
    return candidates[0]


def extraer_marca_modelo_flexible(texto: str) -> tuple[Optional[str], Optional[str]]:
    tokens = [token for token in texto.strip().split() if token]
    if not tokens:
        return None, None

    first_token = tokens[0].upper()
    marca = first_token if first_token in KNOWN_MAKES else None
    model_start_index = 1 if marca else 0

    modelo_tokens = []
    for token in tokens[model_start_index:]:
        token_upper = token.upper()
        if YEAR4.fullmatch(token_upper) or LITERS.fullmatch(token) or RANGE_2DIGIT.fullmatch(token) or RANGE_4DIGIT.fullmatch(token):
            break
        if token_upper == "0":
            continue
        modelo_tokens.append(token)

    modelo = " ".join(modelo_tokens).strip() if modelo_tokens else None
    return marca, (modelo.upper() if modelo else None)


def split_aplicaciones_seguro(aplicaciones: str) -> list[str]:
    if not aplicaciones:
        return []
    aplicaciones_texto = aplicaciones.strip()
    partes_aplicaciones = re.split(r"\s-\s", aplicaciones_texto)
    if len(partes_aplicaciones) > 1:
        return [part.strip() for part in partes_aplicaciones if part.strip()]
    partes_aplicaciones = re.split(r",(?![^()]*\))", aplicaciones_texto)
    return [part.strip() for part in partes_aplicaciones if part.strip()]
