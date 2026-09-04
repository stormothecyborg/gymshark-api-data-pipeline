from __future__ import annotations

from typing import Any

import pandas as pd


def normalize_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    if 'title' in df.columns:
        df['title'] = df['title'].apply(lambda x: str(x).strip() if isinstance(x, str) else x)
    if 'currency' in df.columns:
        df['currency'] = df['currency'].map(lambda x: str(x).upper() if isinstance(x, str) else x)
    if 'current_price' in df.columns:
        df['current_price'] = pd.to_numeric(df['current_price'], errors='coerce')
    if 'old_price' in df.columns:
        df['old_price'] = pd.to_numeric(df['old_price'], errors='coerce')
    if 'product_url' in df.columns:
        df['product_url'] = df['product_url'].map(lambda x: x if isinstance(x, str) and x.startswith('http') else x)
    return df


def coalesce_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, '', []):
            return value
    return None
