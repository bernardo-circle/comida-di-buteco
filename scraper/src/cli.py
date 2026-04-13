from __future__ import annotations

import argparse

from .config import get_settings
from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Comida di Buteco MVP pipeline")
    parser.add_argument(
        "command",
        choices=["listings", "details", "normalize", "geocode", "pipeline"],
        help="Pipeline stage to run",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    pipeline = Pipeline(settings)

    if args.command == "listings":
        listings, summary = pipeline.run_listings()
        print(f"Listings written: {len(listings)}")
        print(f"Pages crawled: {summary.pages_crawled}")
        return

    if args.command == "details":
        details, summary = pipeline.run_details()
        print(f"Details written: {len(details)}")
        print(f"Detail pages visited: {summary.detail_pages_visited}")
        return

    if args.command == "normalize":
        listings, _ = pipeline.run_listings()
        details, _ = pipeline.run_details()
        final_records, unmatched_listings, unmatched_details = pipeline.run_normalize(listings, details)
        print(f"Matched records: {len(final_records)}")
        print(f"Unmatched listings: {len(unmatched_listings)}")
        print(f"Unmatched details: {len(unmatched_details)}")
        return

    if args.command == "geocode":
        listings, _ = pipeline.run_listings()
        details, _ = pipeline.run_details()
        final_records, _, _ = pipeline.run_normalize(listings, details)
        geocoded = pipeline.run_geocode(final_records)
        print(f"Geocoded records written: {len(geocoded)}")
        return

    summary = pipeline.run()
    print(f"Pages crawled: {summary.pages_crawled}")
    print(f"Listings found: {summary.listings_found}")
    print(f"Detail pages visited: {summary.detail_pages_visited}")
    print(f"Geocoding successes: {summary.geocoding_successes}")
    print(f"Geocoding failures: {summary.geocoding_failures}")
    print(f"Final usable records: {summary.final_usable_records}")


if __name__ == "__main__":
    main()
