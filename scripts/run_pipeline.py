from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.connection import execute_sql_file
from src.pipeline import Pipeline

if __name__ == '__main__':
    schema_path = ROOT / 'src' / 'database' / 'schema.sql'
    execute_sql_file(str(schema_path))
    pipeline = Pipeline()
    result = pipeline.run(pages=2, hits_per_page=20)
    print(json.dumps(result, default=str, indent=2))
