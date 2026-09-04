from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / '.env')

DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
DATABASE_PORT = int(os.getenv('DATABASE_PORT', '5432'))
DATABASE_NAME = os.getenv('DATABASE_NAME', 'listing_tracker')
DATABASE_USER = os.getenv('DATABASE_USER', 'listing_tracker_user')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')

ALGOLIA_APP_ID = os.getenv('ALGOLIA_APP_ID', '')
ALGOLIA_API_KEY = os.getenv('ALGOLIA_API_KEY', '')
ALGOLIA_INDEX_NAME = os.getenv('ALGOLIA_INDEX_NAME', 'production_rw_products_v2_popularity')
ALGOLIA_ENDPOINT = os.getenv('ALGOLIA_ENDPOINT', '')

SOURCE_NAME = 'gymshark_algolia'
