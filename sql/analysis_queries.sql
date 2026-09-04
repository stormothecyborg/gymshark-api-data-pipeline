-- Product count
SELECT COUNT(*) AS total_products FROM listings;

-- Products by category
SELECT category, COUNT(*) AS product_count
FROM listings
GROUP BY category
ORDER BY product_count DESC;

-- Average, min, and max price by category
SELECT category,
       AVG(price) AS avg_price,
       MIN(price) AS min_price,
       MAX(price) AS max_price
FROM (
    SELECT listing_id, category, price
    FROM listing_snapshots
    WHERE observed_at = (
        SELECT MAX(observed_at) FROM listing_snapshots ls2 WHERE ls2.listing_id = listing_snapshots.listing_id
    )
) t
GROUP BY category
ORDER BY avg_price DESC;

-- Price changes over time
SELECT listing_id,
       observed_at,
       price,
       LAG(price) OVER (PARTITION BY listing_id ORDER BY observed_at) AS previous_price,
       price - LAG(price) OVER (PARTITION BY listing_id ORDER BY observed_at) AS delta_price
FROM listing_snapshots
ORDER BY listing_id, observed_at;

-- Longest tracked products
SELECT listing_id,
       MIN(observed_at) AS first_seen,
       MAX(observed_at) AS last_seen,
       EXTRACT(DAY FROM (MAX(observed_at) - MIN(observed_at))) AS days_tracked
FROM listing_snapshots
GROUP BY listing_id
ORDER BY days_tracked DESC;

-- Extraction counts by pipeline run
SELECT source, status, COUNT(*) AS run_count,
       SUM(rows_extracted) AS total_rows_extracted
FROM pipeline_runs
GROUP BY source, status
ORDER BY total_rows_extracted DESC;
