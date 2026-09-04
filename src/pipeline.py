from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.collectors.gymshark_api import AlgoliaCollector
from src.config.settings import SOURCE_NAME
from src.database.connection import get_connection
from src.database.repository import Repository
from src.parsers.gymshark_parser import normalize_listing_record, parse_hit
from src.quality.checks import quality_summary, validate_dataframe
from src.transformations.features import build_feature_frame
from src.transformations.normalize import normalize_dataframe

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def sanitize_for_db(value):
    if isinstance(value, dict):
        return {str(k): sanitize_for_db(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_for_db(v) for v in value]
    if isinstance(value, tuple):
        return [sanitize_for_db(v) for v in value]
    if pd.isna(value) if hasattr(value, '__float__') else False:
        return None
    if isinstance(value, float) and (pd.isna(value) or value == float('inf') or value == float('-inf')):
        return None
    return value


class Pipeline:
    def __init__(self, collector: AlgoliaCollector | None = None, repo: Repository | None = None):
        self.collector = collector or AlgoliaCollector()
        self.repo = repo

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def run(self, query: str = '', hits_per_page: int = 20, pages: int = 2, timeout: int = 30) -> dict[str, Any]:
        started_at = self._utc_now()
        run_id = None
        status = 'failed'
        error_message = None
        rows_extracted = 0
        rows_cleaned = 0
        rows_rejected = 0

        try:
            response_hits = self.collector.fetch_all(query=query, hits_per_page=hits_per_page, pages=pages, timeout=timeout)
            rows_extracted = len(response_hits)
            logger.info('Extracted %s hits', rows_extracted)

            if not response_hits:
                status = 'success'
                return {
                    'run_id': run_id,
                    'status': status,
                    'rows_extracted': rows_extracted,
                    'rows_cleaned': rows_cleaned,
                    'rows_rejected': rows_rejected,
                }

            parsed_records = []
            for hit in response_hits:
                parsed = parse_hit(hit, extraction_time=started_at.isoformat())
                normalized = normalize_listing_record(parsed)
                parsed_records.append(normalized)

            df = pd.DataFrame(parsed_records)
            df = normalize_dataframe(df)
            df = df.where(pd.notnull(df), None)
            rows_cleaned = len(df)
            rows_rejected = int(df['listing_id'].isna().sum())
            valid_df = df.dropna(subset=['listing_id'])

            qa = validate_dataframe(valid_df)
            rows_rejected = qa['rejected_rows']
            valid_df = valid_df.reset_index(drop=True)

            with get_connection() as conn:
                repo = self.repo or Repository(conn)
                run_data = {
                    'started_at': started_at,
                    'finished_at': self._utc_now(),
                    'source': SOURCE_NAME,
                    'rows_extracted': rows_extracted,
                    'rows_cleaned': rows_cleaned,
                    'rows_rejected': rows_rejected,
                    'status': 'running',
                    'error_message': None,
                    'duration_seconds': 0,
                }
                run_id = repo.insert_run(run_data)

                for _, row in valid_df.iterrows():
                    row_dict = sanitize_for_db(row.to_dict())
                    listing = {
                        'listing_id': row_dict.get('listing_id'),
                        'source': SOURCE_NAME,
                        'title': row_dict.get('title'),
                        'category': row_dict.get('category'),
                        'brand': row_dict.get('brand'),
                        'product_url': row_dict.get('product_url'),
                        'sku': row_dict.get('sku'),
                        'currency': row_dict.get('currency'),
                        'first_seen_at': started_at,
                        'last_seen_at': started_at,
                    }
                    repo.upsert_listing(listing)
                    raw_id = repo.insert_raw_listing(
                        source=SOURCE_NAME,
                        scraped_at=started_at,
                        request_id=self.collector.build_request_id(),
                        raw_payload=row_dict,
                        listing_url=row_dict.get('product_url'),
                    )
                    snapshot = {
                        'listing_id': row_dict.get('listing_id'),
                        'source': SOURCE_NAME,
                        'observed_at': started_at,
                        'price': row_dict.get('current_price'),
                        'old_price': row_dict.get('old_price'),
                        'availability': row_dict.get('is_available'),
                        'raw_id': raw_id,
                    }
                    repo.insert_snapshot(sanitize_for_db(snapshot))

                feature_df = build_feature_frame(valid_df)
                feature_df['source'] = SOURCE_NAME
                feature_df = feature_df.where(pd.notnull(feature_df), None)
                for _, feature_row in feature_df.iterrows():
                    repo.insert_feature(sanitize_for_db(feature_row.to_dict()))

                finished_at = self._utc_now()
                duration = (finished_at - started_at).total_seconds()
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE pipeline_runs SET finished_at=%s, status=%s, rows_extracted=%s, rows_cleaned=%s, rows_rejected=%s, duration_seconds=%s WHERE run_id=%s",
                        (finished_at, 'success', rows_extracted, rows_cleaned, rows_rejected, duration, run_id),
                    )
                conn.commit()
                status = 'success'

            return {
                'run_id': run_id,
                'status': status,
                'rows_extracted': rows_extracted,
                'rows_cleaned': rows_cleaned,
                'rows_rejected': rows_rejected,
                'quality_summary': quality_summary(rows_extracted, rows_cleaned, rows_rejected, qa['validation_issues']),
            }

        except Exception as exc:  # pragma: no cover - real pipeline failure path
            error_message = str(exc)
            logger.exception('Pipeline failed')
            finished_at = self._utc_now()
            duration = (finished_at - started_at).total_seconds()
            try:
                with get_connection() as conn:
                    repo = self.repo or Repository(conn)
                    repo.insert_run({
                        'started_at': started_at,
                        'finished_at': finished_at,
                        'source': SOURCE_NAME,
                        'rows_extracted': rows_extracted,
                        'rows_cleaned': rows_cleaned,
                        'rows_rejected': rows_rejected,
                        'status': 'failed',
                        'error_message': error_message,
                        'duration_seconds': duration,
                    })
            except Exception:  # pragma: no cover - logging only
                logger.exception('Failed to record pipeline failure row')
            return {
                'run_id': run_id,
                'status': 'failed',
                'rows_extracted': rows_extracted,
                'rows_cleaned': rows_cleaned,
                'rows_rejected': rows_rejected,
                'error_message': error_message,
            }


if __name__ == '__main__':
    pipeline = Pipeline()
    result = pipeline.run(pages=2, hits_per_page=20)
    print(json.dumps(result, default=str, indent=2))
