from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from extract.scrapping.models import OemLookupResult
from extract.scrapping.web_driver import WebDriverWrapper

@dataclass(frozen=True)
class SiteConfig:
    base_url: str
    enabled: bool = True

class SiteAdapter(ABC):
    key: str  # ej "boston"

    def __init__(self, cfg: SiteConfig):
        self.cfg = cfg

    @abstractmethod
    def lookup_oem(self, wd: WebDriverWrapper, oem: str) -> Optional[OemLookupResult]:
        """
        Retorna None si el sitio no pudo procesar (ej cambió HTML).
        Retorna OemLookupResult(found=False) si procesó bien pero no encontró.
        """
        raise NotImplementedError
