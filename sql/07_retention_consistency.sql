-- 07_retention_consistency.sql
-- Purpose: check how day-1 and day-7 retention relate. A player can skip day 1 but return on day 7.

SELECT
    retention_1,                                               -- came back on day 1?
    retention_7,                                               -- came back on day 7?
    COUNT(*)                                        AS players,   -- players with this combination
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct  -- share of all players
FROM players                                                   -- read from the players view
GROUP BY retention_1, retention_7                              -- one row per combination
ORDER BY retention_1, retention_7;                             -- tidy ordering
