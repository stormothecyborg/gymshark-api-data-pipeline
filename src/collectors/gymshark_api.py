from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.config.settings import ALGOLIA_API_KEY, ALGOLIA_APP_ID, ALGOLIA_ENDPOINT, SOURCE_NAME

logger = logging.getLogger(__name__)


class AlgoliaCollector:
    def __init__(self, endpoint: str | None = None, app_id: str | None = None, api_key: str | None = None):
        self.endpoint = endpoint or ALGOLIA_ENDPOINT
        self.app_id = app_id or ALGOLIA_APP_ID
        self.api_key = api_key or ALGOLIA_API_KEY

    def build_request_payload(self, query: str = '', hits_per_page: int = 20, page: int = 0) -> dict:
        return {
            'query': query,
            'hitsPerPage': hits_per_page,
            'page': page,
            'filters': '("inStock":"true")',
            'ruleContexts': ['web_minibag'],
        }

    @staticmethod
    def extract_hits(response: Any) -> list[dict[str, Any]]:
        payload = response.json() if hasattr(response, 'json') else response
        if not isinstance(payload, dict):
            return []
        hits = payload.get('hits', [])
        return hits if isinstance(hits, list) else []

    def fetch_page(self, page: int = 0, hits_per_page: int = 20, query: str = '', timeout: int = 30, retries: int = 3) -> dict:
        payload = self.build_request_payload(query=query, hits_per_page=hits_per_page, page=page)
        headers = {
            'x-algolia-application-id': self.app_id,
            'x-algolia-api-key': self.api_key,
            'x-algolia-agent': 'Algolia for JavaScript (4.17.1); Browser',
            'Content-Type': 'application/json',
        }

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(self.endpoint, json=payload, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                logger.warning('Algolia request failed attempt %s/%s: %s', attempt, retries, exc)
                if attempt == retries:
                    raise
                time.sleep(2 ** attempt)

        raise RuntimeError('Failed to fetch Algolia data')

    def fetch_all(self, query: str = '', hits_per_page: int = 20, pages: int = 2, timeout: int = 30) -> list[dict]:
        all_hits: list[dict] = []
        for page in range(pages):
            payload = self.fetch_page(page=page, hits_per_page=hits_per_page, query=query, timeout=timeout)
            hits = self.extract_hits(payload)
            if not hits:
                break
            all_hits.extend(hits)
        return all_hits

    @staticmethod
    def build_request_id() -> str:
        import uuid
        return uuid.uuid4().hex
