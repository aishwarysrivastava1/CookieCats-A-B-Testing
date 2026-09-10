-- 06_rounds_buckets_descriptive.sql
-- Purpose: DESCRIPTIVE ONLY. Shows how retention varies with rounds played.
-- WARNING: rounds played happen AFTER assignment, so the gate itself can change them.
-- Comparing groups inside these buckets is NOT a valid causal comparison (see notebook 07).

WITH bucketed AS (                                             -- CTE that assigns each player to a rounds bucket
    SELECT
        version,                                               -- test group
        retention_7,                                           -- day-7 retention flag
        CASE                                                   -- CASE WHEN = if/else logic in SQL
            WHEN sum_gamerounds = 0              THEN '1) 0 rounds'
            WHEN sum_gamerounds BETWEEN 1 AND 29 THEN '2) 1-29 rounds'
            WHEN sum_gamerounds BETWEEN 30 AND 39 THEN '3) 30-39 rounds'
            WHEN sum_gamerounds BETWEEN 40 AND 99 THEN '4) 40-99 rounds'
            WHEN sum_gamerounds BETWEEN 100 AND 499 THEN '5) 100-499 rounds'
            ELSE '6) 500+ rounds'
        END AS rounds_bucket                                   -- the bucket label
    FROM players                                               -- read from the players view
)
SELECT
    rounds_bucket,                                             -- bucket label
    version,                                                   -- test group
    COUNT(*)                                          AS players,            -- players in this bucket and group
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY version), 2) AS share_of_group_pct,  -- % of the group in this bucket
    ROUND(100.0 * AVG(CAST(retention_7 AS INTEGER)), 2) AS d7_retention_pct   -- day-7 retention inside the bucket
FROM bucketed                                                  -- read from the CTE
GROUP BY rounds_bucket, version                                -- one row per bucket and group
ORDER BY rounds_bucket, version;                               -- tidy ordering
