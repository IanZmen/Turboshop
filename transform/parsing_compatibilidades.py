from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional, Tuple

YEAR4 = re.compile(r"\b(19\d{2}|20\d{2})\b")
# Permite 1-2 decimales y sufijos L/LTS; ignora mediciones con X/* porque se procesan aparte
LITERS = re.compile(r"\b(\d(?:\.\d){1,2})\s*(LTS?|L)?\b", re.IGNORECASE)
ENGINE_CODE = re.compile(r"\b([A-Z]\d[A-Z0-9]{2,5})\b")  # G4FC, D4HB, etc.
RANGE_2DIGIT = re.compile(r"\b(\d{2})\s*[-/]\s*(\d{2})\b")  # 07-11
RANGE_4DIGIT = re.compile(r"\b(19\d{2}|20\d{2})\s*[-/]\s*(19\d{2}|20\d{2})\b")  # 2016/2020
GENERIC_RANGE = re.compile(r"\b(\d{2,4})\s*[-/]\s*(\d{2,4})\b")
ON_PATTERN = re.compile(r"\b(\d{2}|19\d{2}|20\d{2})\s*ON\b", re.IGNORECASE)  # 97 ON / 1997 ON
MEASURE_BLOCK = re.compile(r"\d+(?:[.,]\d+)?(?:\s*[xX\*\u00D7]\s*\d+(?:[.,]\d+)?)+")
DECIMALS = re.compile(r"\b\d+\.\d+\b")

def _to_year_4(y: str) -> Optional[int]:
    # convierte "07" -> 2007 (heurística) y "97" -> 1997
    y = y.strip()
    if len(y) == 4:
        return int(y)
    if len(y) == 2:
        yy = int(y)
        return 2000 + yy if yy <= 30 else 1900 + yy
    return None

def extraer_anios(texto: str) -> Tuple[Optional[int], Optional[int]]:
    t = texto.upper()
    # Limpia motores (decimales) y medidas (X/*) para que no interfieran al detectar años
    t = MEASURE_BLOCK.sub(" ", t)
    t = DECIMALS.sub(" ", t)

    m = RANGE_4DIGIT.search(t)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = RANGE_2DIGIT.search(t)
    if m:
        y1 = _to_year_4(m.group(1))
        y2 = _to_year_4(m.group(2))
        return y1, y2

    m = GENERIC_RANGE.search(t)
    if m:
        y1 = _to_year_4(m.group(1))
        y2 = _to_year_4(m.group(2))
        return y1, y2

    m = ON_PATTERN.search(t)
    if m:
        y = _to_year_4(m.group(1))
        return y, None  # "desde y en adelante"

    m = YEAR4.search(t)
    if m:
        y = int(m.group(1))
        return y, y

    # Año suelto de 2 dígitos
    m = re.search(r"\b(\d{2})\b", t)
    if m:
        y = _to_year_4(m.group(1))
        return y, y

    return None, None

def extraer_motor_litros(texto: str) -> Optional[float]:
    m = LITERS.search(texto)
    return float(m.group(1)) if m else None

def extraer_codigo_motor(texto: str) -> Optional[str]:
    # filtra cosas demasiado cortas, pero deja códigos tipo G4FC / D4HB
    m = ENGINE_CODE.search(texto.upper())
    return m.group(1) if m else None

def extraer_marca_modelo(texto: str) -> tuple[Optional[str], Optional[str]]:
    # Heurística simple:
    # primer token = marca
    # resto (hasta encontrar motor/años) = modelo "crudo"
    tokens = [t for t in texto.strip().split() if t]
    if not tokens:
        return None, None

    marca = tokens[0].upper()

    # modelo: toma tokens siguientes hasta topar con motor litros / año / código motor
    modelo_tokens = []
    for tok in tokens[1:]:
        upper_tok = tok.upper()
        # ignora ceros sueltos que contaminan el modelo
        if upper_tok in {"0", "00"}:
            continue

        if YEAR4.fullmatch(upper_tok) or LITERS.fullmatch(upper_tok) or ENGINE_CODE.fullmatch(upper_tok):
            break
        # también corta si parece rango tipo 07-11
        if RANGE_2DIGIT.fullmatch(upper_tok) or RANGE_4DIGIT.fullmatch(upper_tok) or GENERIC_RANGE.fullmatch(upper_tok):
            break
        # corta si parece motor decimal o medida con X/*
        if DECIMALS.fullmatch(upper_tok) or re.search(r"\d\s*[X\*\u00D7]\s*\d", upper_tok):
            break
        modelo_tokens.append(tok)

    modelo = " ".join(modelo_tokens).strip() if modelo_tokens else None
    return marca, (modelo.upper() if modelo else None)
