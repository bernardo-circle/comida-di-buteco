from __future__ import annotations

import re

from .config import Settings
from .fetchers import BaseFetcher
from .models import DetailRecord, ListingRecord
from .utils import build_google_maps_url, clean_text, markdown_link_target, missing_fields_from_mapping, parse_address_components, unique_slug_from_url


SITEMAP_PATTERN = re.compile(r"https://comidadibuteco\.com\.br/buteco-sitemap\d+\.xml")
DETAIL_URL_PATTERN = re.compile(r"https://comidadibuteco\.com\.br/buteco/[^\]\s)]+/")


class DetailsScraper:
    def __init__(self, settings: Settings, fetcher: BaseFetcher) -> None:
        self.settings = settings
        self.fetcher = fetcher

    def discover_sitemap_urls(self) -> list[str]:
        sitemap_index_url = f"{self.settings.base_url}/wp-sitemap.xml"
        document = self.fetcher.fetch(sitemap_index_url)
        matches = list(dict.fromkeys(SITEMAP_PATTERN.findall(document.markdown)))
        return sorted(matches, key=lambda url: int(re.search(r"buteco-sitemap(\d+)\.xml", url).group(1)))

    def discover_detail_urls(self) -> list[str]:
        detail_urls: list[str] = []
        seen: set[str] = set()
        for sitemap_url in self.discover_sitemap_urls():
            document = self.fetcher.fetch(sitemap_url)
            for url in DETAIL_URL_PATTERN.findall(document.markdown):
                if url in seen:
                    continue
                seen.add(url)
                detail_urls.append(url)
        return detail_urls

    def parse_detail_page(self, markdown: str, detalhes_url: str) -> DetailRecord:
        lines = [line.strip() for line in markdown.splitlines()]
        heading_positions = [index for index, line in enumerate(lines) if line.startswith("# ")]
        name = clean_text(lines[heading_positions[1]].removeprefix("# ")) if len(heading_positions) > 1 else clean_text(lines[0].removeprefix("# "))
        section_start = heading_positions[1] if len(heading_positions) > 1 else 0
        section_lines = lines[section_start + 1 :]

        detail_image_url = None
        for line in section_lines:
            if line.startswith("![Image"):
                image_url = markdown_link_target(line)
                if image_url and "logo-comida-di-buteco" not in image_url and "img-buteco.png" not in image_url:
                    detail_image_url = image_url
                    break

        full_address = None
        phone = None
        hours = None
        dish_name = None
        dish_description = None
        complemento = None

        for index, line in enumerate(section_lines):
            if not line.startswith("**"):
                continue

            label_match = re.match(r"\*\*(?P<label>[^*]+)\*\*(?P<value>.*)", line)
            if not label_match:
                continue

            label = clean_text(label_match.group("label").rstrip(":"))
            value = clean_text(label_match.group("value"))
            if value is None:
                for candidate in section_lines[index + 1 :]:
                    candidate_value = clean_text(candidate)
                    if not candidate_value:
                        continue
                    if candidate_value.startswith("**"):
                        break
                    value = candidate_value
                    break

            if label == "Endereço":
                full_address = value
            elif label == "Telefone":
                phone = value
            elif label in {"Horario", "Horário"}:
                hours = value
            elif dish_name is None:
                dish_name = label
                dish_description = value

        if full_address and " | " in full_address:
            maybe_parts = full_address.split(" | ")
            if len(maybe_parts) > 2:
                complemento = clean_text(" | ".join(maybe_parts[1:-1]))

        address_parts = parse_address_components(full_address)
        payload = {
            "name": name,
            "slug": unique_slug_from_url(detalhes_url),
            "full_address": full_address,
            "neighborhood": address_parts["neighborhood"],
            "city": address_parts["city"],
            "state": address_parts["state"],
            "complemento": complemento,
            "phone": phone,
            "hours": hours,
            "dish_name": dish_name,
            "dish_description": dish_description,
            "detail_image_url": detail_image_url,
            "detalhes_url": detalhes_url,
            "maps_url": build_google_maps_url(full_address, name),
            "source_page_url": detalhes_url,
        }
        missing_fields = missing_fields_from_mapping(payload, ["name", "full_address"])
        parse_status = "ok" if not missing_fields else "partial"
        return DetailRecord(
            **payload,
            parse_status=parse_status,
            missing_fields=missing_fields,
        )

    def scrape_detail(self, listing: ListingRecord) -> DetailRecord:
        document = self.fetcher.fetch(listing.detalhes_url)
        return self.parse_detail_page(document.markdown, listing.detalhes_url)

    def scrape_detail_url(self, detalhes_url: str) -> DetailRecord:
        document = self.fetcher.fetch(detalhes_url)
        return self.parse_detail_page(document.markdown, detalhes_url)
