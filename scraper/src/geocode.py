from __future__ import annotations

import time
from dataclasses import replace

import requests

from .config import CACHE_DIR, Settings
from .models import FinalRecord
from .utils import clean_text, read_json, slugify, write_json


GEOCODE_CACHE_PATH = CACHE_DIR / "geocode_cache.json"


class Geocoder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.geocoder_user_agent})
        self.cache: dict[str, dict] = read_json(GEOCODE_CACHE_PATH, default={})  # type: ignore[assignment]

    def _cache_key(self, address: str) -> str:
        return slugify(address)

    def _persist_cache(self) -> None:
        write_json(GEOCODE_CACHE_PATH, self.cache)

    def geocode(self, address: str | None) -> dict:
        cleaned = clean_text(address)
        if not cleaned:
            return {
                "lat": None,
                "lng": None,
                "geocode_status": "missing_address",
                "geocode_confidence": None,
                "geocode_provider": self.settings.geocoder_provider,
            }

        cache_key = self._cache_key(cleaned)
        if cache_key in self.cache:
            return self.cache[cache_key]

        queries = [cleaned]
        if "rio de janeiro" not in cleaned.lower():
            queries.append(f"{cleaned}, Rio de Janeiro, RJ, Brazil")

        result = {
            "lat": None,
            "lng": None,
            "geocode_status": "not_found",
            "geocode_confidence": None,
            "geocode_provider": self.settings.geocoder_provider,
        }
        for query in queries:
            response = self.session.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "br",
                    "addressdetails": 1,
                },
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            time.sleep(self.settings.geocoder_delay_seconds)
            if not payload:
                continue

            item = payload[0]
            importance = item.get("importance")
            confidence = "high" if importance and importance >= 0.6 else "medium" if importance and importance >= 0.3 else "low"
            result = {
                "lat": float(item["lat"]),
                "lng": float(item["lon"]),
                "geocode_status": "ok",
                "geocode_confidence": confidence,
                "geocode_provider": self.settings.geocoder_provider,
            }
            break

        self.cache[cache_key] = result
        self._persist_cache()
        return result

    def geocode_record(self, record: FinalRecord) -> FinalRecord:
        result = self.geocode(record.address_normalized or record.address_raw)
        return replace(
            record,
            lat=result["lat"],
            lng=result["lng"],
            geocode_status=result["geocode_status"],
            geocode_confidence=result["geocode_confidence"],
            geocode_provider=result["geocode_provider"],
        )
