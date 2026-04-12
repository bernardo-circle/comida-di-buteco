from __future__ import annotations

import unittest

from src.config import get_settings
from src.details_scraper import DetailsScraper
from src.fetchers import BaseFetcher, FetchedDocument
from src.listings_scraper import ListingsScraper
from src.normalize import match_listings_to_details


ARCHIVE_MARKDOWN = """
## Butecos Participantes

##### 1097 Butecos para você visitar

![Image 1: Baixo Gago](https://cdn.example.com/baixo-gago.jpg)

## Baixo Gago

R. Gago Coutinho, 51 | Laranjeiras, Rio de Janeiro - RJ

![Image 2: Adegadega](https://cdn.example.com/adegadega.jpg)

## Adegadega

R. Juiz Aderbal de Oliveira, 209 | Centro, São João de Meriti - RJ
"""


DETAIL_MARKDOWN = """
# Baixo Gago - Comida di Buteco

# Baixo Gago

![Image 5](https://cdn.example.com/baixo-gago-detail.jpg)

**Porogodó** Cestinhas de massa de pastel assadas.

**Endereço:**R. Gago Coutinho, 51 | Laranjeiras, Rio de Janeiro - RJ

**Telefone:**(21) 98849-3672 | (21) 2556-0638

**Horario:**Segunda-feira: 12h - 22h
"""


SITEMAP_INDEX_MARKDOWN = """
# Sitemap Index

[https://comidadibuteco.com.br/buteco-sitemap1.xml](https://comidadibuteco.com.br/buteco-sitemap1.xml)
"""


SITEMAP_MARKDOWN = """
# Sitemap

[https://comidadibuteco.com.br/buteco/3508-revision-v1/](https://comidadibuteco.com.br/buteco/3508-revision-v1/)
"""


class StubFetcher(BaseFetcher):
    def __init__(self, documents: dict[str, str]) -> None:
        self.documents = documents

    def fetch(self, url: str) -> FetchedDocument:
        markdown = self.documents[url]
        return FetchedDocument(
            request_url=url,
            source_url=url,
            title=None,
            raw_text=markdown,
            markdown=markdown,
            fetched_at="2026-04-12T00:00:00+00:00",
        )


class PipelineParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = get_settings()

    def test_listing_parser_filters_to_target_city(self) -> None:
        fetcher = StubFetcher({self.settings.archive_url: ARCHIVE_MARKDOWN})
        scraper = ListingsScraper(self.settings, fetcher)

        records = list(scraper.scrape_all())

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].listing_name, "Baixo Gago")

    def test_detail_parser_extracts_core_fields(self) -> None:
        fetcher = StubFetcher({"https://comidadibuteco.com.br/buteco/3508-revision-v1/": DETAIL_MARKDOWN})
        scraper = DetailsScraper(self.settings, fetcher)

        record = scraper.scrape_detail_url("https://comidadibuteco.com.br/buteco/3508-revision-v1/")

        self.assertEqual(record.name, "Baixo Gago")
        self.assertEqual(record.city, "Rio de Janeiro")
        self.assertEqual(record.state, "RJ")
        self.assertEqual(record.dish_name, "Porogodó")

    def test_sitemap_parser_discovers_detail_urls(self) -> None:
        fetcher = StubFetcher(
            {
                "https://comidadibuteco.com.br/wp-sitemap.xml": SITEMAP_INDEX_MARKDOWN,
                "https://comidadibuteco.com.br/buteco-sitemap1.xml": SITEMAP_MARKDOWN,
            }
        )
        scraper = DetailsScraper(self.settings, fetcher)

        detail_urls = scraper.discover_detail_urls()

        self.assertEqual(detail_urls, ["https://comidadibuteco.com.br/buteco/3508-revision-v1/"])

    def test_listing_detail_matching(self) -> None:
        listing_fetcher = StubFetcher({self.settings.archive_url: ARCHIVE_MARKDOWN})
        detail_fetcher = StubFetcher({"https://comidadibuteco.com.br/buteco/3508-revision-v1/": DETAIL_MARKDOWN})

        listing = list(ListingsScraper(self.settings, listing_fetcher).scrape_all())[0]
        detail = DetailsScraper(self.settings, detail_fetcher).scrape_detail_url("https://comidadibuteco.com.br/buteco/3508-revision-v1/")

        final_records, unmatched_listings, unmatched_details = match_listings_to_details([listing], [detail])

        self.assertEqual(len(final_records), 1)
        self.assertEqual(len(unmatched_listings), 0)
        self.assertEqual(len(unmatched_details), 0)

    def test_listing_without_detail_still_produces_final_record(self) -> None:
        listing_fetcher = StubFetcher({self.settings.archive_url: ARCHIVE_MARKDOWN})
        listing = list(ListingsScraper(self.settings, listing_fetcher).scrape_all())[0]

        final_records, unmatched_listings, unmatched_details = match_listings_to_details([listing], [])

        self.assertEqual(len(final_records), 1)
        self.assertEqual(final_records[0].parse_status, "listing_only")
        self.assertEqual(len(unmatched_listings), 1)
        self.assertEqual(len(unmatched_details), 0)


if __name__ == "__main__":
    unittest.main()
