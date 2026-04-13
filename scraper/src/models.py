from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ListingRecord:
    city: str
    page_number: int | None
    listing_name: str
    listing_address: str | None
    listing_slug: str
    detalhes_url: str
    maps_url: str | None
    image_url: str | None
    source_page_url: str


@dataclass
class DetailRecord:
    name: str | None
    slug: str
    full_address: str | None
    neighborhood: str | None
    city: str | None
    state: str | None
    complemento: str | None
    phone: str | None
    hours: str | None
    dish_name: str | None
    dish_description: str | None
    detail_image_url: str | None
    detalhes_url: str
    maps_url: str | None
    source_page_url: str
    parse_status: str = "ok"
    missing_fields: list[str] = field(default_factory=list)


@dataclass
class FinalRecord:
    id: str
    name: str
    slug: str
    city: str | None
    state: str | None
    address_raw: str | None
    address_normalized: str | None
    neighborhood: str | None
    complemento: str | None
    phone: str | None
    hours: str | None
    dish_name: str | None
    dish_description: str | None
    image_url: str | None
    detalhes_url: str
    maps_url: str | None
    lat: float | None
    lng: float | None
    geocode_status: str
    geocode_confidence: str | None
    geocode_provider: str | None
    source_city: str
    source_page_number: int | None
    scraped_at: str
    parse_status: str
    missing_fields: list[str] = field(default_factory=list)


JsonDict = dict[str, Any]


@dataclass
class RunSummary:
    pages_crawled: int = 0
    listings_found: int = 0
    detail_pages_visited: int = 0
    geocoding_successes: int = 0
    geocoding_failures: int = 0
    final_usable_records: int = 0
