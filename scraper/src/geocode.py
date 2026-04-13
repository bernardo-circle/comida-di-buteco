from __future__ import annotations

import re
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

    def _expand_address_abbreviations(self, value: str) -> str:
        expanded = value
        replacements = {
            "Pça.": "Praça",
            "R.": "Rua",
            "Av.": "Avenida",
            "Ld.": "Ladeira",
        }
        for source, target in replacements.items():
            expanded = expanded.replace(source, target)
        return expanded

    def _simplify_address(self, value: str) -> str:
        simplified = self._expand_address_abbreviations(value).replace("|", ",")
        simplified = re.sub(r"\([^)]*\)", "", simplified)
        simplified = re.sub(r"\s*-\s*Loja\s*\d+", "", simplified, flags=re.I)
        simplified = re.sub(r"\s*-\s*Casa\b", "", simplified, flags=re.I)
        simplified = re.sub(r"\s*-\s*B\b", "", simplified, flags=re.I)
        simplified = simplified.replace("Cacuia/Colônia Z-10", "Cacuia")
        simplified = simplified.replace("Bc Anil", "Anil")
        return clean_text(simplified) or value

    def _split_address(self, value: str) -> tuple[str, str | None]:
        parts = [clean_text(part) for part in value.split("|")]
        street = parts[0] if parts else value
        neighborhood = None
        if len(parts) > 1 and parts[1]:
            neighborhood = clean_text(parts[1].split(",")[0])
        return street or value, neighborhood

    def _query_candidates(self, address: str, name: str | None = None, neighborhood: str | None = None) -> list[str]:
        expanded = self._expand_address_abbreviations(address)
        simplified = self._simplify_address(address)
        street, parsed_neighborhood = self._split_address(simplified)
        neighborhood = clean_text(neighborhood) or parsed_neighborhood
        city = "Rio de Janeiro"

        candidates = [
            f"{name}, {expanded.replace('|', ',')}, Brazil" if name else None,
            f"{expanded.replace('|', ',')}, Brazil",
            f"{name}, {simplified}, Brazil" if name else None,
            f"{simplified}, Brazil",
            f"{name}, {street}, {neighborhood}, {city}, RJ, Brazil" if name and neighborhood else None,
            f"{street}, {neighborhood}, {city}, RJ, Brazil" if neighborhood else None,
            f"{name}, {neighborhood}, {city}, RJ, Brazil" if name and neighborhood else None,
            f"{name}, {city}, RJ, Brazil" if name else None,
        ]

        if neighborhood == "Ilha da Gigóia":
            candidates.extend(
                [
                    f"{name}, {street}, Jardim Oceânico, {city}, RJ, Brazil" if name else None,
                    f"{street}, Jardim Oceânico, {city}, RJ, Brazil",
                ]
            )

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            cleaned_candidate = clean_text(candidate)
            if not cleaned_candidate or cleaned_candidate in seen:
                continue
            seen.add(cleaned_candidate)
            deduped.append(cleaned_candidate)
        return deduped

    def _nominatim_search(self, query: str) -> dict | None:
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
            return None

        item = payload[0]
        importance = item.get("importance")
        confidence = "high" if importance and importance >= 0.6 else "medium" if importance and importance >= 0.3 else "low"
        return {
            "lat": float(item["lat"]),
            "lng": float(item["lon"]),
            "geocode_status": "ok",
            "geocode_confidence": confidence,
            "geocode_provider": "nominatim",
        }

    def _arcgis_search(self, query: str) -> dict | None:
        response = self.session.get(
            "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates",
            params={
                "SingleLine": query,
                "f": "pjson",
                "maxLocations": 1,
                "countryCode": "BRA",
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        time.sleep(max(0.4, self.settings.geocoder_delay_seconds / 2))
        candidates = payload.get("candidates") or []
        if not candidates:
            return None

        item = candidates[0]
        score = item.get("score", 0)
        confidence = "high" if score >= 95 else "medium" if score >= 85 else "low"
        return {
            "lat": float(item["location"]["y"]),
            "lng": float(item["location"]["x"]),
            "geocode_status": "ok",
            "geocode_confidence": confidence,
            "geocode_provider": "arcgis",
        }

    def geocode(self, address: str | None, name: str | None = None, neighborhood: str | None = None) -> dict:
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
        cached = self.cache.get(cache_key)
        if cached and cached.get("geocode_status") == "ok":
            return cached

        queries = self._query_candidates(cleaned, name=name, neighborhood=neighborhood)

        result = {
            "lat": None,
            "lng": None,
            "geocode_status": "not_found",
            "geocode_confidence": None,
            "geocode_provider": self.settings.geocoder_provider,
        }

        for query in queries:
            result = self._nominatim_search(query) or result
            if result["geocode_status"] == "ok":
                break

        if result["geocode_status"] != "ok":
            for query in queries:
                result = self._arcgis_search(query) or result
                if result["geocode_status"] == "ok":
                    break

        self.cache[cache_key] = result
        self._persist_cache()
        return result

    def geocode_record(self, record: FinalRecord) -> FinalRecord:
        result = self.geocode(record.address_normalized or record.address_raw, name=record.name, neighborhood=record.neighborhood)
        return replace(
            record,
            lat=result["lat"],
            lng=result["lng"],
            geocode_status=result["geocode_status"],
            geocode_confidence=result["geocode_confidence"],
            geocode_provider=result["geocode_provider"],
        )
