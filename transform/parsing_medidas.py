from __future__ import annotations
import re
from typing import Optional, Tuple, List

# Captura secuencias tipo:
# 275X24X25.6
# 295X335X101X296
# 235*55
# 294*69*46
# Acepta separadores X x * ×
MEAS_SEQ = re.compile(
    r"\b(\d+(?:[.,]\d+)?(?:\s*[xX\*\u00D7]\s*\d+(?:[.,]\d+)?){1,5})\b"
)

SEP = re.compile(r"\s*([xX\*\u00D7])\s*")

def _to_float(s: str) -> Optional[float]:
    s = s.strip().replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

def extraer_medidas(texto: str) -> Tuple[Optional[str], list[Optional[float]], Optional[str]]:
    """
    Devuelve:
      - medidas_raw: string encontrado (ej "275X24X25.6")
      - valores: lista floats (ej [275.0,24.0,25.6])
      - separador: 'X' o '*' (el primero que aparezca)
    Si no encuentra, devuelve (None, [], None)
    """
    if not texto:
        return None, [], None

    m = MEAS_SEQ.search(texto)
    if not m:
        return None, [], None

    raw = m.group(1).strip()
    # determinar separador principal (primero que aparezca)
    sep_m = SEP.search(raw)
    sep = sep_m.group(1).upper() if sep_m else None

    # split por separadores
    parts = SEP.split(raw)  # incluye separadores, así que mejor usar split manual:
    nums = re.split(r"\s*[xX\*\u00D7]\s*", raw)
    vals = [_to_float(n) for n in nums if n.strip()]

    return raw, vals, sep
