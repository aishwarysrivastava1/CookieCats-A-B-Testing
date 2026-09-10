-- 03_retention_by_version.sql
-- Purpose: the core A/B summary table (retention and engagement per group).

WITH group_totals AS (                                         -- CTE = a named temporary result we can reuse below
    SELECT
        version,                                               -- test group
        COUNT(*)                                     AS players,          -- players in the group
        CAST(SUM(CAST(retention_1 AS INTEGER)) AS INTEGER) AS d1_retained,  -- TRUE becomes 1, FALSE becomes 0, so SUM = count of TRUE
        CAST(SUM(CAST(retention_7 AS INTEGER)) AS INTEGER) AS d7_retained,  -- same idea for day 7
        AVG(sum_gamerounds)                          AS mean_rounds,      -- average rounds (sensitive to outliers)
        MEDIAN(sum_gamerounds)                       AS median_rounds     -- middle value (robust to outliers)
    FROM players                                               -- read from the players view
    GROUP BY version                                           -- one row per group
)
SELECT
    version,                                                   -- test group
    players,                                                   -- players in the group
    d1_retained,                                               -- players who came back 1 day after install
    ROUND(100.0 * d1_retained / players, 2)          AS d1_retention_pct,  -- day-1 retention rate in percent
    d7_retained,                                               -- players who came back 7 days after install
    ROUND(100.0 * d7_retained / players, 2)          AS d7_retention_pct,  -- day-7 retention rate in percent
    ROUND(mean_rounds, 2)                            AS mean_rounds,       -- rounded average rounds
    median_rounds                                              -- median rounds
FROM group_totals                                              -- read from the CTE above
ORDER BY version;                                              -- gate_30 first
