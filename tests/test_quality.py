from __future__ import annotations

import pandas as pd

from src.quality.checks import (
    validate_record,
    validate_dataframe,
    quality_summary,
)


def test_validate_record_accepts_valid_record():
    record = {
        'listing_id': 'abc-123',
        'title': 'Training Tee',
        'product_url': 'https://www.gymshark.com/products/training-tee',
        'currency': 'GBP',
        'current_price': 39.99,
        'sku': 'ABC-123',
        'category': 'Menswear',
        'brand': 'Gymshark',
    }
    assert validate_record(record) == []


def test_validate_record_flags_missing_fields_and_bad_price():
    record = {
        'title': 'Bad item',
        'current_price': -5,
        'product_url': 'not-a-url',
    }
    issues = validate_record(record)
    assert any('listing_id' in issue for issue in issues)
    assert any('price' in issue.lower() for issue in issues)
    assert any('url' in issue.lower() for issue in issues)


def test_validate_dataframe_collects_issues():
    df = pd.DataFrame([
        {
            'listing_id': 'a',
            'title': 'Valid',
            'product_url': 'https://example.com/product',
            'currency': 'GBP',
            'current_price': 10.0,
        },
        {
            'listing_id': None,
            'title': 'Bad',
            'product_url': 'bad-url',
            'currency': 'GBP',
            'current_price': -1,
        },
    ])
    summary = validate_dataframe(df)
    assert summary['total_rows'] == 2
    assert summary['rejected_rows'] >= 1
    assert summary['validation_issues'] >= 1


def test_quality_summary_counts_rejections_and_failures():
    summary = quality_summary(10, 8, 2, 1)
    assert summary['total_extracted'] == 10
    assert summary['successfully_transformed'] == 8
    assert summary['rejected'] == 2
    assert summary['validation_failures'] == 1
