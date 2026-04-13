# Comida di Buteco MVP

Static-data MVP for Rio de Janeiro buteco listings from Comida di Buteco.

The project has two layers:

- `scraper/`: crawl, enrich, normalize, and geocode the data into flat files
- `frontend/`: React + Leaflet UI that reads a committed static dataset and renders it on a map

## Repository structure

```text
data/
  cache/            Fetch and geocode cache
  intermediate/     JSON snapshots between scraper stages
docs/               Architecture notes
frontend/           Vite + React + Leaflet map UI
output/             CSV/JSON artifacts for inspection and frontend consumption
scraper/            Python pipeline
```

## Stack

- Scraping: Python, `requests`, mirrored markdown fetch fallback, parser layer in Python
- Discovery: archive pagination + WordPress sitemap discovery
- Geocoding: Nominatim with local cache
- Frontend: React, Vite, Leaflet
- Persistence: flat files only

## Why the scraper uses a mirrored fetch path

Direct requests to `https://comidadibuteco.com.br` are blocked from this environment by Cloudflare challenge pages. The pipeline therefore supports:

- `SCRAPER_FETCH_MODE=requests`: direct requests only
- `SCRAPER_FETCH_MODE=mirror`: fetch through `https://r.jina.ai/http://...`
- `SCRAPER_FETCH_MODE=auto`: try direct requests first, then fall back to the mirror

The default is `auto`. In practice, `mirror` is the reliable mode for local execution here.

## Setup

### 1. Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r scraper/requirements.txt
```

Optional environment file:

```bash
cp .env.example .env
```

### 2. Frontend dependencies

```bash
cd frontend
npm install
```

## Scraper commands

Run from the repository root.

### Raw listings

```bash
PYTHONPATH=scraper .venv/bin/python -m src.cli listings
```

Outputs:

- `output/rio_listings_raw.csv`
- `data/intermediate/rio_listings_raw.json`

### Raw details

```bash
PYTHONPATH=scraper .venv/bin/python -m src.cli details
```

Outputs:

- `output/rio_details_raw.csv`
- `data/intermediate/rio_details_raw.json`

### Normalize only

```bash
PYTHONPATH=scraper .venv/bin/python -m src.cli normalize
```

### Geocode and write final dataset

```bash
PYTHONPATH=scraper .venv/bin/python -m src.cli geocode
```

### End-to-end pipeline

```bash
PYTHONPATH=scraper .venv/bin/python -m src.cli pipeline
```

Final outputs:

- `output/rio_butecos_final.csv`
- `output/rio_butecos_final.json`

## Frontend commands

The frontend reads the committed static dataset at `frontend/public/data/rio_butecos_final.json`.

If that file is missing for any reason, it falls back to `frontend/public/data/rio_butecos_sample.json`.

### Start local dev

```bash
cd frontend
npm run dev
```

### Production build

```bash
cd frontend
npm run build
```

## Deploy on Vercel

This frontend is now a plain static Vite app, so Vercel is the easiest hosting option.

1. Push this branch to GitHub.
2. In Vercel, choose `Add New Project`.
3. Import the GitHub repository.
4. Set the project root to `frontend`.
5. Keep the default build settings:
   - Build command: `npm run build`
   - Output directory: `dist`
6. Deploy and share the generated URL.

Because the real dataset is committed under `frontend/public/data/rio_butecos_final.json`, no server or runtime API is needed.

## Current behavior

- Archive pages are crawled sequentially and filtered to Rio capital by address parsing
- Detail URLs are discovered from the site sitemap
- Detail parsing is resilient to missing fields
- Historical duplicate detail pages are deduped by name/address, preferring the most recent-looking image year
- Geocoding is cached in `data/cache/geocode_cache.json`
- Frontend supports search, neighborhood filter, clustered markers, marker click, and detail view

## Known limitations

- The first full `details` run can be slow because the public sitemap contains historical buteco pages, not only current entries
- The archive mirror preserves visible card content but not the original `Detalhes` links, so detail URL discovery comes from the sitemap instead of the archive cards
- If the dataset changes in the future, `frontend/public/data/rio_butecos_final.json` should be refreshed before redeploying
- Geocode confidence is heuristic because Nominatim does not expose a dedicated confidence score

## Tests and verification run so far

- `python3 -m compileall scraper/src scraper/tests`
- `PYTHONPATH=. ../.venv/bin/python -m unittest discover tests`
- Live archive page parser check through mirrored fetch
- Live sitemap discovery and detail parser check through mirrored fetch
- Live Nominatim geocode check
- `npm run build`
- `npm run dev` boot check

## Next improvements after MVP

1. Add a current-year hint to detail selection so historical pages are excluded earlier
2. Add concurrent detail fetching with a conservative worker limit
3. Persist crawl logs and per-record failure reasons to a run report file
4. Add richer neighborhood parsing and address normalization
5. Add frontend result count by visible map bounds
6. Add lightweight tests for frontend filters and static dataset loading
