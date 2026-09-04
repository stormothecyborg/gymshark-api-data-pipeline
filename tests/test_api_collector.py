from __future__ import annotations

from src.collectors.gymshark_api import AlgoliaCollector


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = 'ok'

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('bad status')


def test_collector_builds_payload_and_extracts_hits():
    collector = AlgoliaCollector()
    payload = collector.build_request_payload(query='test', hits_per_page=2)
    assert payload['query'] == 'test'
    assert payload['hitsPerPage'] == 2
    assert payload['filters'] == '("inStock":"true")'

    response = DummyResponse({'hits': [{'title': 'A'}, {'title': 'B'}], 'nbHits': 2})
    hits = collector.extract_hits(response)
    assert len(hits) == 2
    assert hits[0]['title'] == 'A'


def test_collector_handles_missing_hits_list():
    collector = AlgoliaCollector()
    response = DummyResponse({'results': []})
    assert collector.extract_hits(response) == []
