from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass(frozen=True)
class OemLookupResult:
    oem: str
    found: bool
    source: str                  # ej "boston.cl"
    url: Optional[str] = None

    part_name: Optional[str] = None
    brand: Optional[str] = None
    specs_text: Optional[str] = None

    # texto crudo de compatibilidades (si lo hay)
    compat_raw: Optional[str] = None

    # compatibilidades estructuradas (si logras)
    compat: Optional[List[Dict[str, Any]]] = None

    notes: Optional[str] = None
