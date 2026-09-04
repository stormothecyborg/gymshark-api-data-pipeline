from __future__ import annotations

import pytest

from src.database.repository import Repository


class DummyConn:
    def __init__(self):
        self.queries = []

    def cursor(self):
        return self

    def execute(self, query, params=None):
        self.queries.append((query, params))
        return self

    def fetchone(self):
        return (1,)

    def fetchall(self):
        return [(1,)]

    def commit(self):
        return None


def test_repository_can_build_upsert_sql_and_counts():
    repo = Repository(DummyConn())
    sql = repo._build_upsert_sql('listings', ['listing_id', 'source', 'title'], ['listing_id'])
    assert 'INSERT INTO listings' in sql
    assert 'ON CONFLICT (listing_id)' in sql
    assert 'DO UPDATE SET' in sql

    assert repo._safe_bool(True) is True
    assert repo._safe_bool('false') is False
