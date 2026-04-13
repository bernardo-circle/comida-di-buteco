from __future__ import annotations

from .models import DetailRecord, FinalRecord, ListingRecord
from .utils import (
    address_signature,
    build_google_maps_url,
    canonical_name_key,
    missing_fields_from_mapping,
    parse_address_components,
    utc_now_iso,
)


def listing_only_record(listing: ListingRecord) -> FinalRecord:
    parsed_address = parse_address_components(listing.listing_address)
    payload = {
        "id": listing.listing_slug,
        "name": listing.listing_name,
        "slug": listing.listing_slug,
        "city": parsed_address["city"] or listing.city,
        "state": parsed_address["state"],
        "address_raw": listing.listing_address,
        "address_normalized": parsed_address["address_normalized"],
        "neighborhood": parsed_address["neighborhood"],
        "complemento": None,
        "phone": None,
        "hours": None,
        "dish_name": None,
        "dish_description": None,
        "image_url": listing.image_url,
        "detalhes_url": listing.detalhes_url or "",
        "maps_url": listing.maps_url or build_google_maps_url(listing.listing_address, listing.listing_name),
        "lat": None,
        "lng": None,
        "geocode_status": "pending",
        "geocode_confidence": None,
        "geocode_provider": None,
        "source_city": listing.city,
        "source_page_number": listing.page_number,
        "scraped_at": utc_now_iso(),
        "parse_status": "listing_only",
    }
    missing_fields = missing_fields_from_mapping(payload, ["name", "address_raw"])
    return FinalRecord(**payload, missing_fields=missing_fields)


def merge_listing_and_detail(listing: ListingRecord, detail: DetailRecord) -> FinalRecord:
    address_raw = detail.full_address or listing.listing_address
    parsed_address = parse_address_components(address_raw)
    image_url = detail.detail_image_url or listing.image_url
    payload = {
        "id": detail.slug or listing.listing_slug,
        "name": detail.name or listing.listing_name,
        "slug": detail.slug or listing.listing_slug,
        "city": detail.city or parsed_address["city"],
        "state": detail.state or parsed_address["state"],
        "address_raw": address_raw,
        "address_normalized": parsed_address["address_normalized"],
        "neighborhood": detail.neighborhood or parsed_address["neighborhood"],
        "complemento": detail.complemento,
        "phone": detail.phone,
        "hours": detail.hours,
        "dish_name": detail.dish_name,
        "dish_description": detail.dish_description,
        "image_url": image_url,
        "detalhes_url": detail.detalhes_url,
        "maps_url": detail.maps_url or listing.maps_url or build_google_maps_url(address_raw, detail.name or listing.listing_name),
        "lat": None,
        "lng": None,
        "geocode_status": "pending",
        "geocode_confidence": None,
        "geocode_provider": None,
        "source_city": listing.city,
        "source_page_number": listing.page_number,
        "scraped_at": utc_now_iso(),
        "parse_status": detail.parse_status,
    }
    missing_fields = missing_fields_from_mapping(payload, ["name", "address_raw", "detalhes_url"])
    if missing_fields and payload["parse_status"] == "ok":
        payload["parse_status"] = "partial"
    return FinalRecord(**payload, missing_fields=missing_fields)


def match_listings_to_details(listings: list[ListingRecord], details: list[DetailRecord]) -> tuple[list[FinalRecord], list[ListingRecord], list[DetailRecord]]:
    details_by_name: dict[str, list[DetailRecord]] = {}
    details_by_url = {detail.detalhes_url: detail for detail in details}
    for detail in details:
        name_key = canonical_name_key(detail.name)
        if name_key:
            details_by_name.setdefault(name_key, []).append(detail)

    matched_detail_slugs: set[str] = set()
    final_records: list[FinalRecord] = []
    unmatched_listings: list[ListingRecord] = []

    for listing in listings:
        chosen = None
        if listing.detalhes_url:
            chosen = details_by_url.get(listing.detalhes_url)

        candidates = details_by_name.get(canonical_name_key(listing.listing_name), []) if chosen is None else []
        if candidates:
            listing_signature = address_signature(listing.listing_address)
            for candidate in candidates:
                if address_signature(candidate.full_address) == listing_signature:
                    chosen = candidate
                    break
            if chosen is None and len(candidates) == 1:
                chosen = candidates[0]

        if chosen is None:
            unmatched_listings.append(listing)
            final_records.append(listing_only_record(listing))
            continue

        matched_detail_slugs.add(chosen.slug)
        final_records.append(merge_listing_and_detail(listing, chosen))

    unmatched_details = [detail for detail in details if detail.slug not in matched_detail_slugs]
    return final_records, unmatched_listings, unmatched_details
