from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

def load_env() -> None:
    base = Path(__file__).resolve().parents[1]
    load_dotenv(base / ".env")

def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)
