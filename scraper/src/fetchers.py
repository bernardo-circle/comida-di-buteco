from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from .config import FETCH_CACHE_DIR, Settings
from .utils import read_json, utc_now_iso, write_json


class FetchError(RuntimeError):
    pass


@dataclass
class FetchedDocument:
    request_url: str
    source_url: str
    title: str | None
    raw_text: str
    markdown: str
    fetched_at: str


def parse_reader_response(request_url: str, response_text: str) -> FetchedDocument:
    title = None
    source_url = request_url
    markdown = response_text

    if response_text.startswith("Title: "):
        title = response_text.splitlines()[0].removeprefix("Title: ").strip()

    for line in response_text.splitlines():
        if line.startswith("URL Source:"):
            source_url = line.removeprefix("URL Source:").strip()
            break

    marker = "Markdown Content:\n"
    if marker in response_text:
        markdown = response_text.split(marker, 1)[1].strip()

    return FetchedDocument(
        request_url=request_url,
        source_url=source_url,
        title=title,
        raw_text=response_text,
        markdown=markdown,
        fetched_at=utc_now_iso(),
    )


class BaseFetcher:
    def fetch(self, url: str) -> FetchedDocument:
        raise NotImplementedError


class RequestsFetcher(BaseFetcher):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    @retry(
        retry=retry_if_exception_type((requests.RequestException, FetchError)),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True,
    )
    def fetch(self, url: str) -> FetchedDocument:
        response = self.session.get(url, timeout=self.settings.request_timeout_seconds)
        if response.status_code == 403 or "cf-mitigated" in response.headers or "Just a moment" in response.text:
            raise FetchError(f"Direct fetch blocked for {url}")
        response.raise_for_status()
        return FetchedDocument(
            request_url=url,
            source_url=url,
            title=None,
            raw_text=response.text,
            markdown=response.text,
            fetched_at=utc_now_iso(),
        )


class MirrorFetcher(BaseFetcher):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True,
    )
    def fetch(self, url: str) -> FetchedDocument:
        mirror_url = f"{self.settings.scraper_mirror_base_url}{url}"
        response = self.session.get(mirror_url, timeout=self.settings.request_timeout_seconds)
        response.raise_for_status()
        return parse_reader_response(url, response.text)


class CachingFetcher(BaseFetcher):
    def __init__(self, fetcher: BaseFetcher, cache_namespace: str) -> None:
        self.fetcher = fetcher
        self.cache_dir = FETCH_CACHE_DIR / cache_namespace
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def fetch(self, url: str) -> FetchedDocument:
        cache_path = self._cache_path(url)
        cached = read_json(cache_path, default=None)
        if cached:
            return FetchedDocument(**cached)

        document = self.fetcher.fetch(url)
        write_json(cache_path, document.__dict__)
        return document


class AutoFetcher(BaseFetcher):
    def __init__(self, settings: Settings) -> None:
        self.direct = CachingFetcher(RequestsFetcher(settings), "direct")
        self.mirror = CachingFetcher(MirrorFetcher(settings), "mirror")

    def fetch(self, url: str) -> FetchedDocument:
        try:
            return self.direct.fetch(url)
        except Exception:
            return self.mirror.fetch(url)


def build_fetcher(settings: Settings) -> BaseFetcher:
    mode = settings.scraper_fetch_mode.lower()
    if mode == "requests":
        return CachingFetcher(RequestsFetcher(settings), "direct")
    if mode == "mirror":
        return CachingFetcher(MirrorFetcher(settings), "mirror")
    return AutoFetcher(settings)
