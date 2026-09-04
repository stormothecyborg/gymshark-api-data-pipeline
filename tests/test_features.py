from __future__ import annotations

import pandas as pd

from src.transformations.features import build_feature_frame


def test_build_feature_frame_creates_expected_derived_columns():
    df = pd.DataFrame([
        {
            'listing_id': 'a',
            'source': 'gymshark_algolia',
            'title': 'Product A',
            'currency': 'GBP',
            'current_price': 100.0,
            'old_price': 120.0,
            'first_seen_at': '2025-01-01',
            'last_seen_at': '2025-01-10',
            'is_available': True,
            'price_change_pct_7d': 5.0,
            'price_change_pct_30d': 10.0,
            'days_tracked': 9,
        },
        {
            'listing_id': 'b',
            'source': 'gymshark_algolia',
            'title': 'Product B',
            'currency': 'GBP',
            'current_price': 80.0,
            'old_price': 80.0,
            'first_seen_at': '2025-01-01',
            'last_seen_at': '2025-01-10',
            'is_available': False,
            'price_change_pct_7d': 0.0,
            'price_change_pct_30d': 0.0,
            'days_tracked': 9,
        },
    ])
    features = build_feature_frame(df)
    assert {'listing_id', 'computed_at', 'current_price', 'price_change_pct_7d', 'days_tracked', 'is_available'}.issubset(features.columns)
    assert features['is_available'].tolist() == [True, False]
    assert features['days_tracked'].tolist() == [9, 9]
