from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from extract.scrapping.models import OemLookupResult
from extract.scrapping.web_driver import WebDriverWrapper
from extract.scrapping.sites.base import SiteAdapter

@dataclass
class FirstMatchReport:
    oem: str
    result: Optional[OemLookupResult]
    tried_sources: List[str]
    errors: List[str]

class OemFirstMatchService:
    def __init__(self, driver_wrapper: WebDriverWrapper, adapters: List[SiteAdapter]):
        self.driver_wrapper = driver_wrapper
        self.adapters = adapters

    def lookup(self, oem: str) -> FirstMatchReport:
        tried_sources: List[str] = []
        errors: List[str] = []

        for adapter in self.adapters:
            if not adapter.cfg.enabled:
                continue

            tried_sources.append(adapter.key)
            try:
                lookup_result = adapter.lookup_oem(self.driver_wrapper, oem)
                if lookup_result is None:
                    errors.append(f"{adapter.key}: adapter returned None (site changed?)")
                    continue

                if lookup_result.found:
                    return FirstMatchReport(oem=oem, result=lookup_result, tried_sources=tried_sources, errors=errors)

            except Exception as error:
                errors.append(f"{adapter.key}: {type(error).__name__}: {error}")

        return FirstMatchReport(oem=oem, result=None, tried_sources=tried_sources, errors=errors)
