from __future__ import annotations

from .config import INTERMEDIATE_DIR, OUTPUT_DIR, Settings
from .details_scraper import DetailsScraper
from .fetchers import build_fetcher
from .geocode import Geocoder
from .listings_scraper import ListingsScraper
from .models import DetailRecord, ListingRecord, RunSummary
from .normalize import match_listings_to_details
from .utils import address_signature, canonical_name_key, clean_text, serialize_records, write_csv, write_json


LISTINGS_JSON_PATH = INTERMEDIATE_DIR / "rio_listings_raw.json"
DETAILS_JSON_PATH = INTERMEDIATE_DIR / "rio_details_raw.json"
LISTINGS_CSV_PATH = OUTPUT_DIR / "rio_listings_raw.csv"
DETAILS_CSV_PATH = OUTPUT_DIR / "rio_details_raw.csv"
FINAL_CSV_PATH = OUTPUT_DIR / "rio_butecos_final.csv"
FINAL_JSON_PATH = OUTPUT_DIR / "rio_butecos_final.json"


class Pipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.fetcher = build_fetcher(settings)
        self.listings_scraper = ListingsScraper(settings, self.fetcher)
        self.details_scraper = DetailsScraper(settings, self.fetcher)
        self.geocoder = Geocoder(settings)

    def run_listings(self) -> tuple[list[ListingRecord], RunSummary]:
        listings = list(self.listings_scraper.scrape_all())
        write_json(LISTINGS_JSON_PATH, serialize_records(listings))
        write_csv(LISTINGS_CSV_PATH, serialize_records(listings))
        summary = RunSummary(
            pages_crawled=max((record.page_number or 0 for record in listings), default=0),
            listings_found=len(listings),
        )
        return listings, summary

    def _detail_priority(self, detail: DetailRecord) -> tuple[int, int]:
        year = 0
        if detail.detail_image_url:
            for token in detail.detail_image_url.split("/"):
                if token.isdigit() and len(token) == 4:
                    year = max(year, int(token))
        revision_bonus = 1 if "revision" in detail.slug else 0
        return (year, revision_bonus)

    def _dedupe_details(self, details: list[DetailRecord]) -> list[DetailRecord]:
        best_by_key: dict[tuple[str | None, str | None], DetailRecord] = {}
        for detail in details:
            key = (canonical_name_key(detail.name), address_signature(detail.full_address))
            current = best_by_key.get(key)
            if current is None or self._detail_priority(detail) >= self._detail_priority(current):
                best_by_key[key] = detail
        return list(best_by_key.values())

    def run_details(self) -> tuple[list[DetailRecord], RunSummary]:
        detail_urls = self.details_scraper.discover_detail_urls()
        details: list[DetailRecord] = []
        for detalhes_url in detail_urls:
            detail = self.details_scraper.scrape_detail_url(detalhes_url)
            if clean_text(detail.city) != self.settings.target_city or clean_text(detail.state) != self.settings.target_state:
                continue
            details.append(detail)
        details = self._dedupe_details(details)
        write_json(DETAILS_JSON_PATH, serialize_records(details))
        write_csv(DETAILS_CSV_PATH, serialize_records(details))
        summary = RunSummary(
            detail_pages_visited=len(detail_urls),
            listings_found=len(details),
        )
        return details, summary

    def run_normalize(self, listings: list[ListingRecord], details: list[DetailRecord]):
        return match_listings_to_details(listings, details)

    def run_geocode(self, final_records):
        geocoded_records = [self.geocoder.geocode_record(record) for record in final_records]
        write_csv(FINAL_CSV_PATH, serialize_records(geocoded_records))
        write_json(FINAL_JSON_PATH, serialize_records(geocoded_records))
        return geocoded_records

    def run(self) -> RunSummary:
        listings, listing_summary = self.run_listings()
        details, details_summary = self.run_details()
        final_records, _, _ = self.run_normalize(listings, details)
        geocoded_records = self.run_geocode(final_records)
        return RunSummary(
            pages_crawled=listing_summary.pages_crawled,
            listings_found=listing_summary.listings_found,
            detail_pages_visited=details_summary.detail_pages_visited,
            geocoding_successes=sum(1 for record in geocoded_records if record.geocode_status == "ok"),
            geocoding_failures=sum(1 for record in geocoded_records if record.geocode_status != "ok"),
            final_usable_records=len(geocoded_records),
        )
