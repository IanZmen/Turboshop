from __future__ import annotations
import re
from typing import Optional, Tuple, List, Dict

DRIVETRAIN = re.compile(r"\b4\s*[xX]\s*[24]\b")
BELT_CODE = re.compile(r"\b\d+PK-\d+\b", re.IGNORECASE)
MILLIMETER_SINGLE_PATTERN = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(MM|mm)\b")

YEAR_TOKEN = re.compile(r"\b\d{2}\s*[-/]\s*\d{2}\b")
ENGINE_RANGE = re.compile(r"\b\d(?:[.,]\d)\s*-\s*\d(?:[.,]\d)\b")

MEASURE_NUMBER_PATTERN = r"\d+(?:[.,]\d+)?(?:[.,]\d*)?"
SEQUENCE_EXPLICIT_PATTERN = re.compile(
    rf"(?<!\d)({MEASURE_NUMBER_PATTERN}(?:\s*(?:[xX\*\u00D7-])\s*{MEASURE_NUMBER_PATTERN}){{1,5}})(?!\d)"
)
SPLIT_SEQUENCE_PATTERN = re.compile(r"\s*(?:[xX\*\u00D7-])\s*")


def _to_float(raw_number: str) -> Optional[float]:
    normalized_number = raw_number.strip().replace(",", ".")
    if normalized_number.endswith("."):
        normalized_number = normalized_number[:-1]
    try:
        return float(normalized_number)
    except Exception:
        return None


def _sequence_is_small_ints(sequence_raw: str) -> bool:
    parts = [
        part.strip()
        for part in SPLIT_SEQUENCE_PATTERN.split(sequence_raw)
        if part.strip()
    ]
    if len(parts) < 2:
        return False
    for part in parts:
        if "." in part or "," in part:
            return False
        if not part.isdigit():
            return False
        if int(part) > 10:
            return False
    return True


def _is_false_sequence(
    sequence_raw: str, texto_limpio: str, millimeter_found: bool
) -> bool:
    sequence_text = sequence_raw.strip()

    if ENGINE_RANGE.fullmatch(sequence_text):
        return True

    if YEAR_TOKEN.fullmatch(sequence_text):
        return True

    if _sequence_is_small_ints(sequence_text):
        normalized_text = texto_limpio.upper()
        if "RIO" in normalized_text:
            return True
        if not millimeter_found:
            return True

    return False


def extraer_medidas(texto: str) -> Tuple[Optional[str], List[Optional[float]], Optional[str]]:
    if not texto:
        return None, [], None

    limpio = DRIVETRAIN.sub("", texto)
    limpio = BELT_CODE.sub("", limpio)
    limpio = YEAR_TOKEN.sub("", limpio)

    raw_parts: list[str] = []
    vals: list[Optional[float]] = []
    sequence_separator: Optional[str] = None

    millimeter_match = MILLIMETER_SINGLE_PATTERN.search(limpio)
    if millimeter_match:
        raw_parts.append(f"{millimeter_match.group(1)}{millimeter_match.group(2)}")
        millimeter_value = _to_float(millimeter_match.group(1))
        if millimeter_value is not None:
            vals.append(millimeter_value)

    sequence_match = SEQUENCE_EXPLICIT_PATTERN.search(limpio)
    if sequence_match:
        sequence_text = sequence_match.group(1).strip().rstrip(".)],;")
        if not DRIVETRAIN.fullmatch(sequence_text.replace(" ", "")) and not _is_false_sequence(
            sequence_text, texto_limpio=limpio, millimeter_found=(millimeter_match is not None)
        ):
            if "*" in sequence_text:
                sequence_separator = "*"
            elif "-" in sequence_text:
                sequence_separator = "-"
            elif "X" in sequence_text.upper() or "×" in sequence_text:
                sequence_separator = "X"

            raw_parts.append(sequence_text)

            nums = [
                raw_number
                for raw_number in SPLIT_SEQUENCE_PATTERN.split(sequence_text)
                if raw_number.strip()
            ]
            for raw_number in nums:
                numeric_value = _to_float(raw_number)
                if numeric_value is not None:
                    vals.append(numeric_value)

    if not raw_parts:
        return None, [], None

    return ";".join(raw_parts), vals, sequence_separator


def build_medida_fields(
    especificaciones_texto: Optional[str],
    medidas: List[Optional[float]],
    separador: Optional[str],
) -> Dict[str, object]:
    medida_1 = medidas[0] if len(medidas) > 0 else None
    medida_2 = medidas[1] if len(medidas) > 1 else None
    medida_3 = medidas[2] if len(medidas) > 2 else None
    medida_4 = medidas[3] if len(medidas) > 3 else None

    return {
        "repuesto_especificaciones_texto": especificaciones_texto,
        "repuesto_medida_1": medida_1,
        "repuesto_medida_2": medida_2,
        "repuesto_medida_3": medida_3,
        "repuesto_medida_4": medida_4,
        "repuesto_cantidad_medidas": len(medidas) if medidas else 0,
        "repuesto_separador_medidas": separador,
    }
