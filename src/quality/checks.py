from __future__ import annotations

import math
from typing import Any
from urllib.parse import urlparse

import pandas as pd


def is_valid_url(value: Any) -> bool:
    if value is None:
        return False
    parsed = urlparse(str(value))
    return bool(parsed.scheme and parsed.netloc)


def validate_record(record: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    required_fields = ['listing_id', 'title', 'product_url', 'currency', 'current_price']
    for field in required_fields:
        if field not in record or record.get(field) in (None, ''):
            issues.append(f'Missing required field: {field}')

    if record.get('current_price') is not None:
        price = float(record['current_price'])
        if math.isnan(price) or price < 0:
            issues.append('Invalid price value: current_price must be >= 0')

    if record.get('product_url') is not None and not is_valid_url(record['product_url']):
        issues.append('Invalid product_url format')

    if record.get('title') is not None and len(str(record['title']).strip()) == 0:
        issues.append('Title is empty')

    if record.get('listing_id') is not None and not isinstance(record['listing_id'], (str, int)):
        issues.append('listing_id has unexpected type')

    return issues


def validate_dataframe(df: pd.DataFrame) -> dict[str, int]:
    total_rows = len(df)
    rejected_rows = 0
    issues = 0
    for _, row in df.iterrows():
        row_issues = validate_record(row.to_dict())
        if row_issues:
            rejected_rows += 1
            issues += len(row_issues)
    return {
        'total_rows': total_rows,
        'rejected_rows': rejected_rows,
        'validation_issues': issues,
        'accepted_rows': total_rows - rejected_rows,
    }


def quality_summary(total_extracted: int, successfully_transformed: int, rejected: int, validation_failures: int) -> dict[str, int]:
    return {
        'total_extracted': total_extracted,
        'successfully_transformed': successfully_transformed,
        'rejected': rejected,
        'validation_failures': validation_failures,
    }
