from __future__ import annotations

import unittest

from src.config import get_settings
from src.details_scraper import DetailsScraper
from src.fetchers import BaseFetcher, FetchedDocument
from src.geocode import Geocoder
from src.listings_scraper import ListingsScraper
from src.normalize import match_listings_to_details
from src.models import DetailRecord, ListingRecord
from src.utils import is_target_city, parse_address_components


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


DETAIL_MARKDOWN_MULTILINE = """
# Bar do David - Comida di Buteco

# Bar do David

![Image 5](https://cdn.example.com/bar-do-david.jpg)

**Conchas Dell Mare**

Conchas de macarrao frito.

**Endereço:**

Ladeira Ari Barroso, 66 | Leme, Rio de Janeiro - RJ

**Telefone:**

(21) 96483-1046

**Horário:**

Terça-feira: 11h - 21h
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

    def test_address_parser_handles_city_without_pipe_separator(self) -> None:
        address = "R. Tenente Cleto Campelo, 582 Rio de Janeiro - RJ"

        parsed = parse_address_components(address)

        self.assertEqual(parsed["street"], "R. Tenente Cleto Campelo, 582")
        self.assertEqual(parsed["city"], "Rio de Janeiro")
        self.assertTrue(is_target_city(address, "Rio de Janeiro", "RJ"))

    def test_explicit_detail_url_override_matches_even_when_name_differs(self) -> None:
        listing = ListingRecord(
            city="Rio de Janeiro",
            page_number=1,
            listing_name="Bar Gato de Botas",
            listing_address="R. Torres Homem, 118 | Vila Isabel, Rio de Janeiro - RJ",
            listing_slug="bar-gato-de-botas",
            detalhes_url="https://comidadibuteco.com.br/buteco/gato-de-botas/",
            maps_url=None,
            image_url=None,
            source_page_url="https://example.com",
        )
        detail = DetailRecord(
            name="Gato de Botas",
            slug="gato-de-botas",
            full_address="R. Torres Homem, 118 | Vila Isabel, Rio de Janeiro - RJ",
            neighborhood="Vila Isabel",
            city="Rio de Janeiro",
            state="RJ",
            complemento=None,
            phone=None,
            hours=None,
            dish_name=None,
            dish_description=None,
            detail_image_url=None,
            detalhes_url="https://comidadibuteco.com.br/buteco/gato-de-botas/",
            maps_url=None,
            source_page_url="https://comidadibuteco.com.br/buteco/gato-de-botas/",
        )

        final_records, unmatched_listings, unmatched_details = match_listings_to_details([listing], [detail])

        self.assertEqual(len(final_records), 1)
        self.assertEqual(final_records[0].name, "Gato de Botas")
        self.assertEqual(len(unmatched_listings), 0)
        self.assertEqual(len(unmatched_details), 0)

    def test_detail_parser_handles_multiline_labeled_fields(self) -> None:
        fetcher = StubFetcher({"https://comidadibuteco.com.br/buteco/bar-do-david-rio/": DETAIL_MARKDOWN_MULTILINE})
        scraper = DetailsScraper(self.settings, fetcher)

        record = scraper.scrape_detail_url("https://comidadibuteco.com.br/buteco/bar-do-david-rio/")

        self.assertEqual(record.name, "Bar do David")
        self.assertEqual(record.full_address, "Ladeira Ari Barroso, 66 | Leme, Rio de Janeiro - RJ")
        self.assertEqual(record.phone, "(21) 96483-1046")
        self.assertEqual(record.hours, "Terça-feira: 11h - 21h")

    def test_geocoder_query_candidates_expand_common_address_patterns(self) -> None:
        geocoder = Geocoder(self.settings)

        queries = geocoder._query_candidates(  # noqa: SLF001
            "Pça. Serzedelo Correia, 15 | Copacabana, Rio de Janeiro - RJ",
            name="Bar da Tati",
            neighborhood="Copacabana",
        )

        self.assertTrue(any("Praça Serzedelo Correia" in query for query in queries))
        self.assertTrue(any("Bar da Tati, Copacabana, Rio de Janeiro, RJ, Brazil" == query for query in queries))


if __name__ == "__main__":
    unittest.main()
