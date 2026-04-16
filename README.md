# Comida di Buteco

Rio de Janeiro buteco directory and map built from Comida di Buteco listing pages.

The project has two main parts:

- `scraper/`: collects, enriches, normalizes, and geocodes buteco data into flat files
- `frontend/`: React + Leaflet app that loads the generated dataset and presents it as a searchable map experience

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

## Project status

The current repo supports:

- crawling Rio listings from the Comida di Buteco site
- enriching records with detail-page data
- geocoding addresses during the data pipeline
- exporting CSV and JSON output artifacts
- browsing the resulting dataset in a local map UI with:
  - search by name
  - neighborhood filter
  - individual map markers
  - selected buteco details in the sidebar
  - mobile-friendly browse/details flow

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

This frontend is a plain static Vite app, so Vercel is the easiest hosting option.

1. Push the code to GitHub.
2. In Vercel, choose `Add New Project`.
3. Import the GitHub repository.
4. Set the project root to `frontend`.
5. Keep the default build settings:
   - Build command: `npm run build`
   - Output directory: `dist`
6. Deploy and share the generated URL.

Because the real dataset is committed under `frontend/public/data/rio_butecos_final.json`, no backend or runtime API is needed.

## Stadia Maps authentication

The deployed frontend uses Stadia Maps tiles. Local development works on `localhost`, but production deployments need Stadia authentication.

Recommended setup:

1. Create or sign in to a Stadia Maps account.
2. Open `Manage Properties`.
3. Add your deployed domain under `Authentication Configuration`.
4. If using Vercel, make sure the actual `*.vercel.app` domain is allowed if that is what the browser sends as the origin.
5. Refresh the deployed app after saving.

## Current behavior

- archive pages are crawled sequentially and filtered to Rio capital by address parsing
- detail URLs are discovered from the site sitemap
- detail parsing is resilient to missing fields
- historical duplicate detail pages are deduped by name/address, preferring the most recent-looking image year
- geocoding is cached in `data/cache/geocode_cache.json`
- the frontend supports search, neighborhood filter, marker hover/click interaction, selected-record details, and mobile browsing

## Known limitations

- the first full `details` run can be slow because the public sitemap contains historical buteco pages, not only current entries
- the archive mirror preserves visible card content but not the original `Detalhes` links, so detail URL discovery comes from the sitemap instead of the archive cards
- if the dataset changes in the future, `frontend/public/data/rio_butecos_final.json` should be refreshed before redeploying
- geocode confidence is heuristic because Nominatim does not expose a dedicated confidence score

## Tests and verification

- `python3 -m compileall scraper/src scraper/tests`
- `PYTHONPATH=. ../.venv/bin/python -m unittest discover tests`
- live archive page parser check through mirrored fetch
- live sitemap discovery and detail parser check through mirrored fetch
- live Nominatim geocode check
- `npm run build`
- `npm run dev` boot check

## Next improvements

1. Add a current-year hint to detail selection so historical pages are excluded earlier.
2. Add concurrent detail fetching with a conservative worker limit.
3. Persist crawl logs and per-record failure reasons to a run report file.
4. Add richer neighborhood parsing and address normalization.
5. Add frontend result count by visible map bounds.
6. Add lightweight frontend tests around filters, selection, and mobile interaction behavior.
