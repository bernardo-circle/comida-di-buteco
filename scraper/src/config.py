from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
CACHE_DIR = DATA_DIR / "cache"
FETCH_CACHE_DIR = CACHE_DIR / "fetch"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("COMIDA_BASE_URL", "https://comidadibuteco.com.br")
    archive_url: str = os.getenv("COMIDA_ARCHIVE_URL", "https://comidadibuteco.com.br/butecos/")
    target_city: str = os.getenv("TARGET_CITY", "Rio de Janeiro")
    target_state: str = os.getenv("TARGET_STATE", "RJ")
    target_region_label: str = os.getenv("TARGET_REGION_LABEL", "Rio de Janeiro - Capital")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    request_delay_seconds: float = float(os.getenv("REQUEST_DELAY_SECONDS", "1.0"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    user_agent: str = os.getenv("USER_AGENT", "comida-di-buteco-mvp/0.1")
    scraper_fetch_mode: str = os.getenv("SCRAPER_FETCH_MODE", "auto")
    scraper_mirror_base_url: str = os.getenv("SCRAPER_MIRROR_BASE_URL", "https://r.jina.ai/http://")
    scraper_max_archive_pages: int = int(os.getenv("SCRAPER_MAX_ARCHIVE_PAGES", "200"))
    scraper_detail_workers: int = int(os.getenv("SCRAPER_DETAIL_WORKERS", "8"))
    geocoder_provider: str = os.getenv("GEOCODER_PROVIDER", "nominatim")
    geocoder_email: str = os.getenv("GEOCODER_EMAIL", "")
    geocoder_user_agent: str = os.getenv("GEOCODER_USER_AGENT", "comida-di-buteco-mvp/0.1")
    geocoder_delay_seconds: float = float(os.getenv("GEOCODER_DELAY_SECONDS", "1.2"))


def get_settings() -> Settings:
    return Settings()
