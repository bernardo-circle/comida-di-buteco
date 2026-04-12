# MVP Architecture

## Overview

The MVP is intentionally split into two clean modules:

- `scraper/` produces static output artifacts
- `frontend/` renders those artifacts on a map

This keeps the system easy to run locally and avoids introducing a database or backend API for a one-time static directory.

## Data collection strategy

### Listing crawl

- Start from `https://comidadibuteco.com.br/butecos/`
- Walk paginated archive pages sequentially
- Parse visible listing cards from mirrored markdown output
- Extract:
  - page number
  - name
  - address
  - image URL
  - generated maps URL
- Filter to Rio capital by parsed `city/state`

### Detail discovery

- Fetch `wp-sitemap.xml`
- Extract all `buteco-sitemapN.xml` URLs
- Extract all detail URLs from those sitemaps
- Visit each detail page and parse:
  - name
  - full address
  - neighborhood
  - phone
  - hours
  - dish name
  - dish description
  - image URL

### Why sitemap discovery is used

The archive mirror preserves visible card content well, but not the original `Detalhes` links. The sitemap is therefore the most reliable source of canonical detail URLs in this environment.

## Merge strategy

- Use listing pages as the source of current visible archive records
- Use detail pages as the source of richer metadata
- Match records by normalized name plus address signature
- Deduplicate historical detail pages by preferring the most recent-looking detail image year

## Geocoding strategy

- Geocode in the data pipeline, never in the frontend
- Use Nominatim with:
  - local cache
  - Rio de Janeiro bias in fallback query
  - stored status/confidence/provider metadata

## Frontend strategy

- Vite + React
- Leaflet + OpenStreetMap tiles
- Marker clustering from day one
- Left sidebar:
  - search
  - neighborhood filter
  - result list
  - selected buteco details
- Right map panel:
  - clustered markers
  - click marker to select
  - map recenters on selected listing

## Key tradeoffs

- No database: simplest path for static data
- Mirror fallback for scraping: needed because direct HTML fetches hit Cloudflare challenge pages
- Sitemap + archive hybrid: a pragmatic compromise between completeness and local reliability
- Flat output files: easier debugging and inspection than hidden state in a service layer
