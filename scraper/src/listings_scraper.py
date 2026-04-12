from __future__ import annotations

from collections.abc import Iterable
from math import ceil
import re

from .config import Settings
from .fetchers import BaseFetcher
from .models import ListingRecord
from .utils import build_google_maps_url, clean_text, is_target_city, markdown_link_target, slugify


TOTAL_COUNT_PATTERN = re.compile(r"#####\s+(?P<count>\d+)\s+Butecos")


class ListingsScraper:
    def __init__(self, settings: Settings, fetcher: BaseFetcher) -> None:
        self.settings = settings
        self.fetcher = fetcher

    def parse_listing_page(self, markdown: str, page_url: str, page_number: int | None = None) -> list[ListingRecord]:
        records: list[ListingRecord] = []
        lines = [line.rstrip() for line in markdown.splitlines()]
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if not line.startswith("![Image"):
                index += 1
                continue

            image_url = markdown_link_target(line)
            probe = index + 1
            while probe < len(lines) and not lines[probe].strip():
                probe += 1

            if probe >= len(lines) or not lines[probe].strip().startswith("## "):
                index += 1
                continue

            listing_name = clean_text(lines[probe].strip().removeprefix("## "))
            probe += 1
            while probe < len(lines) and not lines[probe].strip():
                probe += 1

            listing_address = None
            if probe < len(lines):
                candidate = clean_text(lines[probe].strip())
                if candidate and not candidate.startswith("![") and not candidate.startswith("## "):
                    listing_address = candidate

            if listing_name and listing_address:
                records.append(
                    ListingRecord(
                        city=self.settings.target_city,
                        page_number=page_number,
                        listing_name=listing_name,
                        listing_address=listing_address,
                        listing_slug=slugify(listing_name),
                        detalhes_url="",
                        maps_url=build_google_maps_url(listing_address, listing_name),
                        image_url=image_url,
                        source_page_url=page_url,
                    )
                )
            index = probe
        return records

    def discover_total_pages(self) -> int:
        document = self.fetcher.fetch(self.settings.archive_url)
        records = self.parse_listing_page(document.markdown, self.settings.archive_url, page_number=1)
        match = TOTAL_COUNT_PATTERN.search(document.markdown)
        if match and records:
            total_count = int(match.group("count"))
            return min(self.settings.scraper_max_archive_pages, ceil(total_count / len(records)))
        return self.settings.scraper_max_archive_pages

    def scrape_page(self, page_url: str, page_number: int | None = None) -> list[ListingRecord]:
        document = self.fetcher.fetch(page_url)
        return self.parse_listing_page(document.markdown, page_url, page_number=page_number)

    def scrape_all(self) -> Iterable[ListingRecord]:
        seen: set[tuple[str, str | None]] = set()
        total_pages = self.discover_total_pages()

        for page_number in range(1, total_pages + 1):
            page_url = self.settings.archive_url if page_number == 1 else f"{self.settings.archive_url}page/{page_number}/"
            try:
                page_records = self.scrape_page(page_url, page_number=page_number)
            except Exception:
                break
            if not page_records:
                break

            for record in page_records:
                if not is_target_city(record.listing_address, self.settings.target_city, self.settings.target_state):
                    continue
                dedupe_key = (record.listing_name, record.listing_address)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                yield record
