# Gymshark API Data Engineering Pipeline

This project builds a realistic end-to-end ETL pipeline that consumes Gymshark’s live Algolia product search API, transforms the semi-structured JSON into analytics-ready records, validates the output, stores the results in PostgreSQL, and tracks historical snapshots across runs.

## 1. Project objective

The goal is to demonstrate a production-style data engineering workflow using:

- reverse-engineered API discovery through browser network inspection
- direct API extraction instead of scraping HTML
- Extract → Transform → Validate → Load stages
- Python and pandas for parsing and normalization
- PostgreSQL for raw and curated storage
- historical product snapshots for trend analysis
- automated testing and validation
- technical documentation suitable for an interview discussion

## 2. Why use the API instead of scraping HTML?

The Gymshark storefront is rendered through JavaScript and fetches product data from an Algolia index rather than exposing a single clean HTML product list. This makes the frontend API the better source of truth for a data engineering pipeline because it is structured, efficient, and much more reliable than parsing page markup.

This project intentionally avoids screen scraping and instead consumes the public frontend API that was discovered in the browser’s Network tab.

## 3. API discovery through browser DevTools

The API endpoint was discovered by inspecting browser traffic in Chrome DevTools under Network → Fetch/XHR.

Observed request:

- Method: POST
- URL: https://2deaes0cuo-2.algolianet.com/1/indexes/production_rw_products_v2_popularity/query
- Headers:
  - x-algolia-application-id
  - x-algolia-api-key
  - x-algolia-agent
- Body:

{
"query": "",
"hitsPerPage": 10,
"filters": "(\"inStock\":\"true\")",
"ruleContexts": ["web_minibag"]
}

The response contains a `hits` array with product objects and fields such as `objectID`, `sku`, `handle`, `title`, `brand`, `price`, `compareAtPrice`, `availableColours`, `featuredImage`, and `inStock`.

> Important: the API is filtered by `inStock=true`, so a product disappearing from this response is not proof of absence from stock. Availability is recorded only when the API explicitly provides it.

## 4. Architecture

The project follows this flow:

Gymshark Frontend
↓
Algolia API discovered in browser Network tab
↓
Python collector
↓
Raw JSON persistence
↓
Parser and normalizer
↓
Quality validation and rejection tracking
↓
PostgreSQL
↓
Historical snapshots
↓
Analytics-ready features

## 5. Project structure

- src/collectors/gymshark_api.py
- src/parsers/gymshark_parser.py
- src/transformations/normalize.py
- src/transformations/features.py
- src/quality/checks.py
- src/database/connection.py
- src/database/repository.py
- src/database/schema.sql
- src/config/settings.py
- src/pipeline.py
- tests/
- sql/analysis_queries.sql
- scripts/run_pipeline.py
- .env
- .env.example
- requirements.txt
- pyproject.toml

## 6. Extraction layer

The collector in `src/collectors/gymshark_api.py`:

- reads the endpoint and credentials from environment variables
- sends POST requests with the Algolia headers
- supports pagination via `hitsPerPage` and page count
- handles timeouts and retry logic with exponential backoff
- returns raw product hits while preserving the original payload shape
- generates a request identifier and timestamps for traceability

## 7. Transformation and normalization

The parser in `src/parsers/gymshark_parser.py` extracts and normalizes:

- listing ID
- product title
- SKU
- category
- brand
- handle
- canonical URL
- currency
- current price
- compare-at price
- image URL
- colour metadata
- extraction timestamp
- availability, only when explicitly provided by the API

The normalization layer cleans string values, coerces numeric prices, handles nullable fields, and safely defends against malformed nested JSON structures.

## 8. PostgreSQL schema

The database is expected to use the existing local PostgreSQL instance with these settings:

- host: localhost
- port: 5432
- database: listing_tracker
- user: listing_tracker_user

The SQL schema in `src/database/schema.sql` creates the following tables:

- raw_listings
  - raw_id
  - source
  - scraped_at
  - request_id
  - raw_payload JSONB
  - listing_url

- listings
  - listing_id
  - source
  - title
  - category
  - brand
  - product_url
  - sku
  - currency
  - first_seen_at
  - last_seen_at

- listing_snapshots
  - snapshot_id
  - listing_id
  - source
  - observed_at
  - price
  - old_price
  - availability
  - raw_id

- pipeline_runs
  - run_id
  - started_at
  - finished_at
  - source
  - rows_extracted
  - rows_cleaned
  - rows_rejected
  - status
  - error_message
  - duration_seconds

- listing_features
  - listing_id
  - source
  - computed_at
  - current_price
  - price_change_pct_7d
  - price_change_pct_30d
  - days_tracked
  - is_available
  - availability_change_count

## 9. Data quality and validation

The validation logic in `src/quality/checks.py` checks for:

- missing required IDs and critical values
- malformed URLs
- negative or invalid prices
- empty product titles
- unexpected field types
- malformed API responses
- suspicious extraction counts

Rejected records are not silently ignored. The pipeline tracks validation issues and totals so bad rows are visible and reviewable in the execution summary.

## 10. Reliability and failure handling

The pipeline includes:

- HTTP timeout enforcement
- API retries with exponential backoff
- structured logging
- transaction-level writes
- explicit run status tracking in `pipeline_runs`
- graceful handling of malformed records
- clear failure propagation instead of silent partial success

A critical API or database failure results in a failed pipeline run with a captured error message.

## 11. Historical tracking strategy

The historical snapshot table is designed to support analyses such as:

- price changes over time
- products newly observed in each run
- products that disappear from a query response
- tracking duration for each product
- historical price history

The design is intentionally careful: the dataset does not assume a missing product in an `inStock=true` filter is a real stock-out. It tracks query-level observation changes rather than interpreting absence as a true product availability signal.

## 12. Analytics-ready features

The feature generation layer in `src/transformations/features.py` prepares rows for downstream analysis. Example outputs include:

- current price
- price change percentages
- days tracked
- availability flags where explicitly supported
- availability-change counters where supported

The SQL examples in `sql/analysis_queries.sql` cover:

- total product count
- category breakdowns
- price summaries
- price deltas over time
- longest tracked listings
- extraction counts by run

## 13. Environment configuration

Copy `.env.example` to `.env` and fill in the local values if needed. The project is already configured with the required local database and Algolia variables.

Example:

DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=listing_tracker
DATABASE_USER=listing_tracker_user
DATABASE_PASSWORD=your_password

ALGOLIA_APP_ID=2DEAES0CUO
ALGOLIA_API_KEY=your_algolia_api_key
ALGOLIA_INDEX_NAME=production_rw_products_v2_popularity
ALGOLIA_ENDPOINT=https://2deaes0cuo-2.algolianet.com/1/indexes/production_rw_products_v2_popularity/query

## 14. How to run the pipeline

From the project root:

1. Create and activate the virtual environment if needed.
2. Install dependencies:
   pip install -r requirements.txt
3. Run the schema bootstrap and pipeline:
   python scripts/run_pipeline.py

You can also run the module directly:

python -m src.pipeline

## 15. Testing

This project uses `pytest` for automated validation. The test suite covers:

- API response parsing
- normalization logic
- missing fields
- malformed records
- price transformation
- feature generation
- repository SQL generation
- data quality checks

Run tests with:

pytest -q

## 16. Limitations and assumptions

- The pipeline depends on the live Algolia endpoint and inventory state at execution time.
- Some products may not appear in a filtered response even if still in the catalog.
- Availability tracking is only reliable when the API exposes it directly.
- Historical tracking is incremental and designed for time-series analytics rather than perfect inventory state reconstruction.

## 17. Example output flow

```text
Gymshark Frontend
      ↓
Algolia API
      ↓
Python ETL
      ↓
raw_listings JSONB
      ↓
listings + listing_snapshots
      ↓
pipeline_runs + listing_features
      ↓
SQL analytics and ML feature pipelines
```

This project is intentionally built to be realistic, explainable, and interview-ready while remaining simple enough to run locally in a standard Python + PostgreSQL environment.
