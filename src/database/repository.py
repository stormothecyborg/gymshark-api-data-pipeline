from __future__ import annotations

import json
import logging
from typing import Any, Iterable

logger = logging.getLogger(__name__)


class Repository:
    def __init__(self, connection):
        self.conn = connection

    @staticmethod
    def _safe_bool(value: Any) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {'true', '1', 'yes', 'y'}
        return bool(value)

    @staticmethod
    def _build_upsert_sql(table: str, columns: Iterable[str], unique_keys: Iterable[str]) -> str:
        columns = list(columns)
        unique_keys = list(unique_keys)
        update_columns = [col for col in columns if col not in unique_keys]
        placeholders = ', '.join(['%s'] * len(columns))
        update_sql = ', '.join(f'{col} = EXCLUDED.{col}' for col in update_columns)
        conflict_sql = ', '.join(unique_keys)
        return (
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_sql}) DO UPDATE SET {update_sql}"
        )

    def insert_raw_listing(self, source: str, scraped_at, request_id: str, raw_payload: dict, listing_url: str | None = None):
        sql = """
            INSERT INTO raw_listings (source, scraped_at, request_id, raw_payload, listing_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING raw_id
        """
        serialized = json.dumps(raw_payload, default=str, allow_nan=False)
        with self.conn.cursor() as cur:
            cur.execute(sql, (source, scraped_at, request_id, serialized, listing_url))
            row = cur.fetchone()
        self.conn.commit()
        return row[0] if row else None

    def upsert_listing(self, listing: dict) -> None:
        columns = [
            'listing_id', 'source', 'title', 'category', 'brand', 'product_url', 'sku',
            'currency', 'first_seen_at', 'last_seen_at'
        ]
        sql = self._build_upsert_sql('listings', columns, ['listing_id'])
        values = [
            listing.get('listing_id'), listing.get('source'), listing.get('title'), listing.get('category'),
            listing.get('brand'), listing.get('product_url'), listing.get('sku'), listing.get('currency'),
            listing.get('first_seen_at'), listing.get('last_seen_at')
        ]
        with self.conn.cursor() as cur:
            cur.execute(sql, values)
        self.conn.commit()

    def insert_snapshot(self, snapshot: dict) -> None:
        sql = """
            INSERT INTO listing_snapshots (listing_id, source, observed_at, price, old_price, availability, raw_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                snapshot.get('listing_id'), snapshot.get('source'), snapshot.get('observed_at'),
                snapshot.get('price'), snapshot.get('old_price'), snapshot.get('availability'), snapshot.get('raw_id')
            ))
        self.conn.commit()

    def insert_run(self, run_data: dict):
        sql = """
            INSERT INTO pipeline_runs (started_at, finished_at, source, rows_extracted, rows_cleaned,
            rows_rejected, status, error_message, duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING run_id
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                run_data.get('started_at'), run_data.get('finished_at'), run_data.get('source'),
                run_data.get('rows_extracted'), run_data.get('rows_cleaned'), run_data.get('rows_rejected'),
                run_data.get('status'), run_data.get('error_message'), run_data.get('duration_seconds')
            ))
            row = cur.fetchone()
        self.conn.commit()
        return row[0] if row else None

    def insert_feature(self, feature: dict) -> None:
        sql = """
            INSERT INTO listing_features (
                listing_id, source, computed_at, current_price, price_change_pct_7d,
                price_change_pct_30d, days_tracked, is_available, availability_change_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                feature.get('listing_id'), feature.get('source'), feature.get('computed_at'),
                feature.get('current_price'), feature.get('price_change_pct_7d'), feature.get('price_change_pct_30d'),
                feature.get('days_tracked'), feature.get('is_available'), feature.get('availability_change_count')
            ))
        self.conn.commit()
