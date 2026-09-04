from __future__ import annotations

from datetime import datetime

import pandas as pd


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    features = df.copy()
    features['computed_at'] = datetime.utcnow().isoformat()
    if 'source' not in features.columns:
        features['source'] = 'gymshark_algolia'
    if 'current_price' not in features.columns:
        features['current_price'] = None
    if 'price_change_pct_7d' not in features.columns:
        features['price_change_pct_7d'] = None
    if 'price_change_pct_30d' not in features.columns:
        features['price_change_pct_30d'] = None
    if 'days_tracked' not in features.columns:
        features['days_tracked'] = 0
    if 'is_available' not in features.columns:
        features['is_available'] = None
    if 'availability_change_count' not in features.columns:
        features['availability_change_count'] = 0
    return features[[
        'listing_id', 'source', 'computed_at', 'current_price', 'price_change_pct_7d',
        'price_change_pct_30d', 'days_tracked', 'is_available', 'availability_change_count'
    ]]
