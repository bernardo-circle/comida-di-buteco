from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def ascii_slug_base(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.replace("–", "-").replace("—", "-")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def slugify(value: str) -> str:
    base = ascii_slug_base(value).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return base or "item"


def absolute_url(base_url: str, maybe_relative_url: str | None) -> str | None:
    if not maybe_relative_url:
        return None
    return urljoin(base_url, maybe_relative_url)


def unique_slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    tail = path.split("/")[-1] if path else "item"
    return slugify(tail)


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def serialize_records(records: Iterable[object]) -> list[dict]:
    serialized: list[dict] = []
    for record in records:
        if is_dataclass(record):
            serialized.append(asdict(record))
        else:
            serialized.append(dict(record))
    return serialized


def write_json(path: Path, payload: object) -> None:
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8") as file_obj:
        json.dump(payload, file_obj, ensure_ascii=False, indent=2)


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    row_list = list(rows)
    ensure_parent_dir(path)
    if not row_list:
        with path.open("w", encoding="utf-8", newline="") as file_obj:
            file_obj.write("")
        return

    fieldnames = list(row_list[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row_list)


def markdown_link_target(line: str) -> str | None:
    match = re.search(r"\((https?://[^)]+)\)", line)
    return clean_text(match.group(1)) if match else None


def parse_address_components(address: str | None) -> dict[str, str | None]:
    cleaned = clean_text(address)
    if not cleaned:
        return {
            "address_normalized": None,
            "street": None,
            "neighborhood": None,
            "city": None,
            "state": None,
        }

    street = None
    neighborhood = None
    city = None
    state = None

    if "|" in cleaned:
        street, remainder = [part.strip() for part in cleaned.split("|", 1)]
    else:
        street, remainder = cleaned, ""

    city_state_source = remainder or cleaned
    city_state_match = re.search(r"(?P<body>.+?)\s*-\s*(?P<state>[A-Z]{2})$", city_state_source)
    if city_state_match:
        state = clean_text(city_state_match.group("state"))
        body = clean_text(city_state_match.group("body"))
        if body:
            parts = [clean_text(part) for part in body.split(",") if clean_text(part)]
            if len(parts) >= 2:
                neighborhood = parts[0]
                city = parts[-1]
            elif len(parts) == 1:
                city = parts[0]

    return {
        "address_normalized": cleaned,
        "street": clean_text(street),
        "neighborhood": neighborhood,
        "city": city,
        "state": state,
    }


def canonical_name_key(value: str | None) -> str | None:
    if not value:
        return None
    return slugify(value)


def address_signature(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if not cleaned:
        return None
    return slugify(cleaned)


def is_target_city(address: str | None, target_city: str, target_state: str) -> bool:
    components = parse_address_components(address)
    city = clean_text(components["city"])
    state = clean_text(components["state"])
    if not city or not state:
        return False
    return slugify(city) == slugify(target_city) and state.upper() == target_state.upper()


def build_google_maps_url(address: str | None, name: str | None = None) -> str | None:
    query_parts = [part for part in [name, address] if clean_text(part)]
    if not query_parts:
        return None
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(', '.join(query_parts))}"


def missing_fields_from_mapping(mapping: Mapping[str, object], required_fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field_name in required_fields:
        if mapping.get(field_name) in (None, "", []):
            missing.append(field_name)
    return missing
