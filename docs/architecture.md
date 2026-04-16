# Project Architecture

## Overview

The project is intentionally split into two clean modules:

- `scraper/` produces flat output artifacts
- `frontend/` renders those artifacts as a browsable map UI

This keeps the system easy to run locally and avoids introducing a database or backend service for a mostly static directory experience.

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
  - Rio de Janeiro bias in fallback queries
  - stored status, provider, and heuristic confidence metadata

## Frontend strategy

- Vite + React
- Leaflet map with OpenStreetMap tiles
- Marker clustering to keep dense areas readable
- Sidebar includes:
  - project framing
  - selected buteco details
  - search by name
  - neighborhood filter
  - results list
- Map panel includes:
  - clustered markers
  - marker click selection
  - bounds fitting for filtered results
  - fly-to behavior for selected records

## Data loading strategy

- During local development, Vite exposes `/api/butecos`
- That route reads `output/rio_butecos_final.json` from the repository root
- If the final dataset is missing, the UI falls back to `frontend/public/data/rio_butecos_sample.json`

This keeps local development simple without introducing a separate API service.

## Key tradeoffs

- No database: simplest path for static or infrequently changing data
- Mirror fallback for scraping: needed because direct HTML fetches hit Cloudflare challenge pages
- Sitemap + archive hybrid: pragmatic compromise between completeness and local reliability
- Flat output files: easier debugging and inspection than hidden state in a service layer
