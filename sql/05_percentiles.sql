-- 05_percentiles.sql
-- Purpose: percentiles show the shape of a skewed distribution better than the mean.

SELECT
    version,                                                               -- test group
    QUANTILE_CONT(sum_gamerounds, 0.25) AS p25_rounds,                     -- 25% of players played this many rounds or fewer
    QUANTILE_CONT(sum_gamerounds, 0.50) AS p50_rounds,                     -- the median
    QUANTILE_CONT(sum_gamerounds, 0.75) AS p75_rounds,                     -- 75th percentile
    QUANTILE_CONT(sum_gamerounds, 0.90) AS p90_rounds,                     -- 90th percentile
    QUANTILE_CONT(sum_gamerounds, 0.99) AS p99_rounds,                     -- 99th percentile (heavy players)
    MAX(sum_gamerounds)                 AS max_rounds                      -- the single most extreme player
FROM players                                                               -- read from the players view
GROUP BY version                                                           -- one row per group
ORDER BY version;                                                          -- gate_30 first
