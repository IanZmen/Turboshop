import re
from typing import Optional

ZERO_TOKEN = re.compile(r"(?:(?<=\s)|^)\s*0(?=\s|$)")
TRAILING_ZERO = re.compile(r"(?:\s+0)+\s*$")


def limpiar_ceros_modelo_texto(modelo: Optional[str]) -> Optional[str]:
    def _clean(texto: Optional[str]) -> Optional[str]:
        if not texto:
            return None
        cleaned = texto.strip()
        cleaned = TRAILING_ZERO.sub("", cleaned)
        cleaned = ZERO_TOKEN.sub(" ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned or None

    return _clean(modelo.upper() if modelo else None)
