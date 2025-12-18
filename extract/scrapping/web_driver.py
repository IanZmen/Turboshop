from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager


@dataclass(frozen=True)
class ScraperConfig:
    # Delay “humano” para no bombardear: 2–5s por defecto
    human_delay_range: Tuple[float, float] = (2.0, 5.0)

    # Timeouts
    page_load_timeout: int = 30
    wait_timeout: int = 15

    # Navegación
    headless: bool = False
    window_size: Tuple[int, int] = (1280, 800)

    # Buenas prácticas anti “ruido”
    disable_images: bool = True
    user_agent: Optional[str] = None


class WebDriverWrapper:
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None

    # ---------- Setup / Teardown ----------
    def initialize_driver(self) -> None:
        chrome_options = webdriver.ChromeOptions()

        if self.config.headless:
            # "new" headless suele ir mejor en Chrome moderno
            chrome_options.add_argument("--headless=new")

        w, h = self.config.window_size
        chrome_options.add_argument(f"--window-size={w},{h}")

        # Ajustes “suaves”
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        if self.config.user_agent:
            chrome_options.add_argument(f"--user-agent={self.config.user_agent}")

        if self.config.disable_images:
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(self.config.page_load_timeout)
        self.wait = WebDriverWait(self.driver, self.config.wait_timeout)

    def quit_driver(self) -> None:
        if self.driver is not None:
            try:
                self.driver.quit()
            finally:
                self.driver = None
                self.wait = None

    # ---------- Ética / rate limiting ----------
    def human_delay(self) -> None:
        """Delay aleatorio 2–5s (configurable) para bajar carga y parecer humano."""
        lo, hi = self.config.human_delay_range
        time.sleep(random.uniform(lo, hi))

    # ---------- Navegación ----------
    def load_page(self, url: str, delay_after: bool = True) -> None:
        self._require_driver()
        self.driver.get(url)
        # Espera mínima a “document ready”
        self._wait_document_ready()
        if delay_after:
            self.human_delay()

    def get_url(self) -> str:
        self._require_driver()
        return self.driver.current_url

    # ---------- Tabs ----------
    def new_tab(self, url: str, delay_after: bool = True) -> None:
        self._require_driver()
        self.driver.execute_script("window.open(arguments[0], '_blank');", url)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self._wait_document_ready()
        if delay_after:
            self.human_delay()

    def change_tab(self, index: int) -> None:
        self._require_driver()
        handles = self.driver.window_handles
        if not (0 <= index < len(handles)):
            raise IndexError(f"Tab index {index} out of range. Open tabs: {len(handles)}")
        self.driver.switch_to.window(handles[index])

    def close_tab(self, fallback_index: int = 0) -> None:
        self._require_driver()
        self.driver.close()
        handles = self.driver.window_handles
        if handles:
            self.change_tab(min(fallback_index, len(handles) - 1))

    # ---------- Wait helpers ----------
    def find_visible(self, by: By, value: str) -> WebElement:
        self._require_driver()
        return self.wait.until(EC.visibility_of_element_located((by, value)))

    def find_present(self, by: By, value: str) -> WebElement:
        self._require_driver()
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click(self, by: By, value: str, delay_after: bool = True, retries: int = 2) -> None:
        """
        Click robusto: espera clickable + reintentos por intercept/stale.
        """
        self._require_driver()
        last_err = None
        for _ in range(retries + 1):
            try:
                el = self.wait.until(EC.element_to_be_clickable((by, value)))
                el.click()
                if delay_after:
                    self.human_delay()
                return
            except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                last_err = e
                time.sleep(0.4)
        raise last_err  # type: ignore

    def write(self, by: By, value: str, text: str, clear: bool = True, delay_after: bool = True) -> None:
        self._require_driver()
        el = self.find_visible(by, value)
        if clear:
            el.clear()
        el.send_keys(text)
        if delay_after:
            self.human_delay()

    def get_text(self, by: By, value: str) -> str:
        self._require_driver()
        return self.find_visible(by, value).text

    def get_attr(self, by: By, value: str, attr: str) -> str:
        self._require_driver()
        return self.find_present(by, value).get_attribute(attr) or ""

    # ---------- Internals ----------
    def _require_driver(self) -> None:
        if self.driver is None or self.wait is None:
            raise RuntimeError("Driver not initialized. Call initialize_driver() first.")

    def _wait_document_ready(self) -> None:
        """Espera a que el documento esté listo (sin meter sleeps fijos)."""
        self._require_driver()
        try:
            WebDriverWait(self.driver, self.config.wait_timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            # No siempre es fatal (SPA). Se puede seguir, pero sin romper.
            pass
